"""Unit tests: orchestrator with fake retriever — routing-to-status matrix."""

from __future__ import annotations

from typing import List, Optional

import pytest

from chatbot.app.models.chat_models import ChatIntent
from chatbot.app.rag.models import RetrievedChunk, RetrievalResult
from chatbot.app.services.conversation import InMemoryConversationStore
from chatbot.app.services.intent_router import IntentRouter
from chatbot.app.services.orchestrator import (
    ChatbotOrchestrator,
    OrchestrationStatus,
    resolve_message,
)


class FakeRetriever:
    """Deterministic stand-in for KnowledgeRetriever."""

    def __init__(self, chunks: Optional[List[RetrievedChunk]] = None,
                 fail: bool = False) -> None:
        self._chunks = chunks or []
        self._fail = fail
        self.calls: List[dict] = []

    def search(self, query, **kwargs):
        self.calls.append({"query": query, **kwargs})
        if self._fail:
            from chatbot.app.rag.errors import RetrievalUnavailableError
            raise RetrievalUnavailableError("fake-store")
        return RetrievalResult(items=list(self._chunks))


def _chunk(source_id: str = "src-1", content: str = "Fee information.",
           product_id: str = None, category: str = "payments") -> RetrievedChunk:
    return RetrievedChunk(
        point_id="0123456789abcdef0123456789abcdef",
        chunk_id=f"{source_id}:0", source_id=source_id, content=content,
        title="Source", entity="HDFC Bank", category=category,
        source_url="https://hdfc.bank.in/x", score=0.8,
        product_id=product_id,
    )


def _orch(retriever=None) -> ChatbotOrchestrator:
    return ChatbotOrchestrator(
        intent_router=IntentRouter(),
        knowledge_retriever=retriever or FakeRetriever([_chunk()]),
        conversation_store=InMemoryConversationStore(),
    )


class TestStatusMatrix:
    def test_grounded_banking_query_succeeds(self):
        result = _orch().process_turn("What is NEFT?")
        assert result.status is OrchestrationStatus.SUCCESS
        assert result.grounded is True
        assert len(result.retrieved_chunks) == 1

    def test_unsafe_is_blocked_without_retrieval(self):
        fake = FakeRetriever()
        result = _orch(fake).process_turn("How do I hack into someones account")
        assert result.status is OrchestrationStatus.BLOCKED
        assert fake.calls == []  # no downstream I/O for blocked turns

    def test_out_of_scope(self):
        result = _orch().process_turn("Tell me a joke")
        assert result.status is OrchestrationStatus.OUT_OF_SCOPE

    def test_account_query_not_wired(self):
        result = _orch().process_turn("What is my account balance?")
        assert result.status is OrchestrationStatus.ACCOUNT_ACCESS_NOT_WIRED
        assert result.clarifying_question

    def test_transaction_query_not_wired(self):
        result = _orch().process_turn("Show my recent transactions")
        assert result.status is OrchestrationStatus.TRANSACTION_ACCESS_NOT_WIRED

    def test_recommendation_without_context_requires_auth(self):
        result = _orch().process_turn("Which credit card should I get?")
        assert result.status is OrchestrationStatus.AUTHENTICATED_CONTEXT_REQUIRED
        assert "authenticated" in result.clarifying_question.lower()

    def test_retrieval_failure_is_service_unavailable(self):
        result = _orch(FakeRetriever(fail=True)).process_turn("What is NEFT?")
        assert result.status is OrchestrationStatus.SERVICE_UNAVAILABLE

    def test_no_chunks_is_no_evidence(self):
        result = _orch(FakeRetriever([])).process_turn("What is NEFT?")
        assert result.status is OrchestrationStatus.NO_EVIDENCE
        assert result.grounded is False


class TestMultiTurn:
    def test_conversation_id_is_preserved(self):
        orch = _orch()
        a = orch.process_turn("What is NEFT?", conversation_id="conv-1")
        b = orch.process_turn("How does RTGS work?", conversation_id="conv-1")
        assert a.conversation_id == b.conversation_id == "conv-1"

    def test_follow_up_uses_product_filter(self):
        fake = FakeRetriever([_chunk(product_id="HDFCRGOLD")])
        orch = _orch(fake)
        orch.process_turn("Tell me about Regalia Gold credit card", conversation_id="c")
        orch.process_turn("What about its fees?", conversation_id="c")
        follow_up_call = fake.calls[-1]
        assert follow_up_call.get("product_id") == "HDFCRGOLD"

    def test_followup_without_product_context_asks_for_clarification(self):
        result = _orch(FakeRetriever([])).process_turn("What about its fees?")
        assert result.status is OrchestrationStatus.NEEDS_CLARIFICATION

    def test_blank_message_rejected(self):
        with pytest.raises(ValueError):
            _orch().process_turn("   ")


class TestResolveMessage:
    def test_pronoun_reference_gets_product_prefix(self):
        from chatbot.app.services.conversation import ConversationState
        state = ConversationState(conversation_id="c", last_product_name="Regalia Gold")
        resolved = resolve_message("What about its fees?", state)
        assert resolved.startswith("Regalia Gold")

    def test_plain_message_unchanged(self):
        from chatbot.app.services.conversation import ConversationState
        state = ConversationState(conversation_id="c", last_product_name="Regalia Gold")
        assert resolve_message("What is NEFT?", state) == "What is NEFT?"
