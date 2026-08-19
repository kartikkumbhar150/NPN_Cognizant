"""Unit tests: Qdrant cloud/local mode selection and credential hygiene.

All offline — the real QdrantClient is monkeypatched with a fake for
client-construction assertions, and collection-compatibility checks use
``QdrantClient(":memory:")``.  No cloud credentials are read, needed,
or printed here.
"""

from __future__ import annotations

import pytest
from qdrant_client import QdrantClient

import chatbot.app.rag.qdrant_store as qdrant_store_module
from chatbot.app.config import ChatbotSettings
from chatbot.app.rag.errors import (
    CollectionConfigurationError,
    VectorStoreError,
)
from chatbot.app.rag.qdrant_store import QdrantVectorStore, create_qdrant_client

# ── Settings/mode unit tests ─────────────────────────────────────────────────


class TestQdrantModeSelection:
    def _settings(self, url: str = "", key: str = "") -> ChatbotSettings:
        return ChatbotSettings(qdrant_url=url, qdrant_api_key=key)

    def test_url_set_selects_cloud_mode(self):
        assert self._settings(url="https://cluster.cloud.qdrant.io").qdrant_mode == "cloud"

    def test_url_unset_selects_local_mode(self):
        assert self._settings().qdrant_mode == "local"

    def test_whitespace_url_still_local(self):
        assert self._settings(url="   ").qdrant_mode == "local"

    def test_repr_never_contains_api_key(self):
        settings = self._settings(url="https://c.qdrant.io", key="SECRET-KEY-123")
        assert "SECRET-KEY-123" not in repr(settings)
        assert "qdrant_api_key='***'" in repr(settings)

    def test_from_env_reflects_environment(self, monkeypatch):
        monkeypatch.setenv("QDRANT_URL", "https://example.qdrant.io")
        monkeypatch.setenv("QDRANT_API_KEY", "k")
        assert ChatbotSettings.from_env().qdrant_mode == "cloud"
        monkeypatch.setenv("QDRANT_URL", "")
        assert ChatbotSettings.from_env().qdrant_mode == "local"


# ── Client construction (fake client — no network) ─────────────────────────


class FakeQdrantClient:
    """Captures constructor kwargs; raises when asked to."""

    instances: list = []

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        FakeQdrantClient.instances.append(self)

    @classmethod
    def last(cls):
        return cls.instances[-1]

    @classmethod
    def reset(cls):
        cls.instances = []


@pytest.fixture(autouse=True)
def _fake_client(monkeypatch):
    FakeQdrantClient.reset()
    monkeypatch.setattr(qdrant_store_module, "QdrantClient", FakeQdrantClient)
    yield
    FakeQdrantClient.reset()


class FailingQdrantClient(FakeQdrantClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        raise ValueError("boom")  # pragma: no cover - construction failure


class TestCreateQdrantClient:
    def test_cloud_mode_passes_url_and_key(self):
        settings = ChatbotSettings(
            qdrant_url="https://cluster.cloud.qdrant.io:6333",
            qdrant_api_key="SECRET-KEY-123",
        )
        client = create_qdrant_client(settings)
        assert isinstance(client, FakeQdrantClient)
        assert client.kwargs.get("url") == "https://cluster.cloud.qdrant.io:6333"
        assert client.kwargs.get("api_key") == "SECRET-KEY-123"

    def test_local_mode_uses_anchored_path(self):
        settings = ChatbotSettings(qdrant_url="", qdrant_local_path=".qdrant")
        client = create_qdrant_client(settings)
        assert "path" in client.kwargs
        assert str(client.kwargs["path"]).endswith("chatbot/.qdrant")

    def test_memory_mode_passthrough(self):
        settings = ChatbotSettings(qdrant_local_path=":memory:")
        client = create_qdrant_client(settings)
        assert client.args == (":memory:",)

    def test_construction_failure_error_carries_no_secrets(self, monkeypatch):
        monkeypatch.setattr(
            qdrant_store_module, "QdrantClient", FailingQdrantClient
        )
        settings = ChatbotSettings(
            qdrant_url="https://cluster.cloud.qdrant.io",
            qdrant_api_key="SECRET-KEY-123",
        )
        with pytest.raises(VectorStoreError) as excinfo:
            create_qdrant_client(settings)
        message = str(excinfo.value)
        assert "SECRET-KEY-123" not in message
        assert "cluster.cloud.qdrant.io" not in message
        assert "ValueError" in message  # exception type only


# ── Collection compatibility (real client, in-memory — still offline) ───────


class TestCollectionCompatibility:
    def test_creates_then_verifies(self):
        client = QdrantClient(":memory:")
        store = QdrantVectorStore(client, "modes_test", dimension=8)
        assert store.ensure_collection() == "created"
        assert store.ensure_collection() == "exists"  # idempotent reuse

    def test_filter_operations_work_after_ensure(self):
        """Cloud rejects payload filters without indexes; ensure_collection
        must create them so delete-by-payload/search filters function."""
        client = QdrantClient(":memory:")
        store = QdrantVectorStore(client, "filter_test", dimension=8)
        store.ensure_collection()
        from chatbot.app.rag.models import VectorRecord

        store.upsert([
            VectorRecord(
                id="01234567-89ab-cdef-0123-456789abcdef",
                vector=[0.1] * 8,
                payload={"source_id": "neft-doc"},
            )
        ])
        store.delete_by_payload("source_id", "neft-doc")  # 400 on cloud pre-fix
        assert store.count() == 0

    def test_dimension_mismatch_fails_without_destroying(self):
        client = QdrantClient(":memory:")
        good = QdrantVectorStore(client, "mismatch_test", dimension=8)
        good.ensure_collection()
        from chatbot.app.rag.models import VectorRecord

        good.upsert([
            VectorRecord(
                id="01234567-89ab-cdef-0123-456789abcdef",
                vector=[0.1] * 8,
                payload={"source_id": "s", "content": "x"},
            )
        ])
        assert good.count() == 1

        wrong = QdrantVectorStore(client, "mismatch_test", dimension=16)
        with pytest.raises(CollectionConfigurationError):
            wrong.ensure_collection()
        # Original collection and its data are intact.
        assert good.count() == 1
        assert good.ensure_collection() == "exists"

    def test_upsert_rejects_wrong_dimension_vectors(self):
        client = QdrantClient(":memory:")
        store = QdrantVectorStore(client, "dim_guard", dimension=8)
        store.ensure_collection()
        from chatbot.app.rag.errors import VectorDimensionError
        from chatbot.app.rag.models import VectorRecord

        with pytest.raises(VectorDimensionError):
            store.upsert([
                VectorRecord(
                    id="01234567-89ab-cdef-0123-456789abcdef",
                    vector=[0.1] * 16,
                    payload={},
                )
            ])
