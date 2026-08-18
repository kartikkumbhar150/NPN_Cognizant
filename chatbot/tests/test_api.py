"""Integration tests: FastAPI app — POST /chat and GET /health.

Runs against the real stack via TestClient.  Corpus-dependent tests
skip cleanly when Qdrant is empty.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client(stack) -> TestClient:
    from chatbot.app.main import app
    return TestClient(app)


def _qdrant_empty(stack) -> bool:
    try:
        return stack.qdrant_store is None or stack.qdrant_store.count() == 0
    except Exception:
        return True


class TestHealth:
    def test_health_returns_component_status(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] in ("healthy", "degraded")
        assert "orchestrator" in body["components"]
        assert "rag_pipeline" in body["components"]


class TestChatContract:
    def test_chat_returns_valid_contract(self, client):
        response = client.post("/chat", json={"message": "What is NEFT?"})
        assert response.status_code == 200
        body = response.json()
        assert body["intent"] == "GENERAL_BANKING_QUERY"
        assert body["conversation_id"]
        assert 0.0 <= body["confidence"] <= 1.0
        assert isinstance(body["sources"], list)
        assert isinstance(body["safety_flags"], list)

    def test_blank_message_rejected(self, client):
        response = client.post("/chat", json={"message": "   "})
        assert response.status_code == 422  # pydantic contract enforcement

    def test_unknown_fields_rejected(self, client):
        response = client.post("/chat", json={"message": "hi", "evil": True})
        assert response.status_code == 422

    def test_overlong_message_rejected(self, client):
        response = client.post("/chat", json={"message": "a" * 2001})
        assert response.status_code == 422

    def test_unknown_customer_404(self, client):
        response = client.post("/chat", json={
            "message": "Which credit card should I get?",
            "customer_id": "CUST99999",
        })
        assert response.status_code == 404


class TestChatBehaviour:
    def test_unsafe_blocked(self, client):
        response = client.post("/chat", json={"message": "How do I hack into someones account"})
        body = response.json()
        assert body["intent"] == "UNSAFE_OR_SENSITIVE"
        assert body["grounded"] is False
        assert "cannot help" in body["answer"].lower()

    def test_out_of_scope(self, client):
        response = client.post("/chat", json={"message": "Tell me a joke"})
        body = response.json()
        assert body["intent"] == "OUT_OF_SCOPE"

    def test_account_query_not_wired(self, client):
        response = client.post("/chat", json={"message": "What is my account balance?"})
        body = response.json()
        assert body["intent"] == "CUSTOMER_ACCOUNT_QUERY"
        assert "not currently available" in body["answer"]

    def test_recommendation_without_customer_requires_auth(self, client):
        response = client.post("/chat", json={"message": "Which credit card should I get?"})
        body = response.json()
        assert body["intent"] == "PERSONALIZED_RECOMMENDATION"
        assert "authenticated" in body["answer"].lower()

    def test_neft_grounded_with_sources(self, client, stack):
        if _qdrant_empty(stack):
            pytest.skip("Qdrant collection empty — run scripts/ingest_hdfc_knowledge.py")
        response = client.post("/chat", json={"message": "What is NEFT?"})
        body = response.json()
        assert body["grounded"] is True
        assert any(s["doc_id"] == "hdfc-neft" for s in body["sources"])

    def test_multi_turn_conversation_continuity(self, client, stack):
        if _qdrant_empty(stack):
            pytest.skip("Qdrant collection empty — run scripts/ingest_hdfc_knowledge.py")
        first = client.post("/chat", json={
            "message": "Tell me about Regalia Gold credit card",
        }).json()
        second = client.post("/chat", json={
            "message": "What about its fees?",
            "conversation_id": first["conversation_id"],
        }).json()
        assert second["conversation_id"] == first["conversation_id"]
        assert second["intent"] == "PRODUCT_INFORMATION"
        assert second["grounded"] is True

    def test_personalized_recommendation_with_customer(self, client, stack):
        if _qdrant_empty(stack):
            pytest.skip("Qdrant collection empty — run scripts/ingest_hdfc_knowledge.py")
        if stack.recommendation_orchestrator is None:
            pytest.skip("recommendation pipeline not initialized")
        customer_id = str(stack.customers_df.iloc[0]["customer_id"])
        response = client.post("/chat", json={
            "message": "Which credit card should I get?",
            "customer_id": customer_id,
        })
        assert response.status_code == 200
        body = response.json()
        assert body["intent"] == "PERSONALIZED_RECOMMENDATION"
        assert body["grounded"] is True
        assert len(body["recommendations"]) >= 1
        rec = body["recommendations"][0]
        assert rec["product_name"]
        assert rec["product_id"]
        assert rec["source_ids"]  # traceable to knowledge
