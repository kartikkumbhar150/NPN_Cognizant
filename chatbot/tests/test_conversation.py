"""Unit tests: conversation store — lifecycle, TTL, sensitive keys, IDs."""

from __future__ import annotations

import time

import pytest

from chatbot.app.services.conversation import (
    ConversationError,
    ConversationNotFoundError,
    ConversationTurn,
    InMemoryConversationStore,
)


def _turn(role: str = "user") -> ConversationTurn:
    return ConversationTurn(role=role, intent="GENERAL_BANKING_QUERY",
                            safe_summary="test", timestamp=time.time())


class TestLifecycle:
    def test_create_generates_unique_ids(self):
        store = InMemoryConversationStore()
        a = store.create()
        b = store.create()
        assert a.conversation_id != b.conversation_id

    def test_create_with_caller_id_uses_it(self):
        store = InMemoryConversationStore()
        state = store.create("fixed-id")
        assert state.conversation_id == "fixed-id"

    def test_create_with_taken_id_raises(self):
        store = InMemoryConversationStore()
        store.create("fixed-id")
        with pytest.raises(ConversationError):
            store.create("fixed-id")

    def test_get_unknown_raises(self):
        store = InMemoryConversationStore()
        with pytest.raises(ConversationNotFoundError):
            store.get("missing")

    def test_delete_removes(self):
        store = InMemoryConversationStore()
        state = store.create()
        store.delete(state.conversation_id)
        with pytest.raises(ConversationNotFoundError):
            store.get(state.conversation_id)


class TestTurnBounding:
    def test_turns_are_bounded_to_max(self):
        store = InMemoryConversationStore(max_turns=3)
        state = store.create()
        for _ in range(6):
            store.append_turn(state.conversation_id, _turn())
        refreshed = store.get(state.conversation_id)
        assert len(refreshed.turns) == 3
        assert refreshed.turn_count == 6

    def test_update_context_sets_safe_fields(self):
        store = InMemoryConversationStore()
        state = store.create()
        store.update_context(state.conversation_id,
                             last_product_id="HDFCRGOLD",
                             last_product_name="Regalia Gold")
        refreshed = store.get(state.conversation_id)
        assert refreshed.last_product_id == "HDFCRGOLD"
        assert refreshed.last_product_name == "Regalia Gold"

    def test_update_context_rejects_sensitive_keys(self):
        store = InMemoryConversationStore()
        state = store.create()
        store.update_context(state.conversation_id,
                             card_number="4111111111111111",
                             last_intent="PRODUCT_INFORMATION")
        refreshed = store.get(state.conversation_id)
        assert not hasattr(refreshed, "card_number") or getattr(refreshed, "card_number", None) is None


class TestTTL:
    def test_expired_conversation_raises(self):
        store = InMemoryConversationStore(ttl_seconds=0.05)
        state = store.create()
        time.sleep(0.1)
        with pytest.raises(ConversationNotFoundError):
            store.get(state.conversation_id)


class TestValidation:
    def test_invalid_max_turns(self):
        with pytest.raises(ValueError):
            InMemoryConversationStore(max_turns=0)

    def test_invalid_ttl(self):
        with pytest.raises(ValueError):
            InMemoryConversationStore(ttl_seconds=-1)

    def test_blank_id_rejected(self):
        store = InMemoryConversationStore()
        with pytest.raises(ConversationError):
            store.get("  ")
