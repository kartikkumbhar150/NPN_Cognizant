"""Lightweight in-memory conversation state for multi-turn chatbot.

Bounded, short-term memory — safe derived context only.  No raw customer
data, no account/card numbers, no credentials, no JWTs, no raw
transaction lists are ever stored.

Protocol-based so unit tests can inject fakes.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

_SENSITIVE_KEYS = frozenset({
    "account_number", "card_number", "cvv", "pin", "password",
    "otp", "jwt", "token", "aadhaar", "pan", "dob",
})

DEFAULT_MAX_TURNS = 10
DEFAULT_TTL_SECONDS = 1800  # 30 minutes
DEFAULT_MAX_CONTEXT_ITEMS = 20


class ConversationError(Exception):
    """Base class for conversation-store failures."""


class ConversationNotFoundError(ConversationError):
    """The conversation_id does not exist or has expired."""


class ConversationExpiredError(ConversationNotFoundError):
    """The conversation existed but its TTL has elapsed."""


@dataclass(frozen=True)
class ConversationTurn:
    """One processed turn in a conversation.

    ``safe_summary`` is a derived label, never the raw user message.
    """
    role: str
    intent: str = ""
    safe_summary: str = ""
    timestamp: float = 0.0


@dataclass
class ConversationState:
    """Mutable conversation state snapshot.

    Retains only safe, public, or self-declared context.  Customer
    banking data must NOT be placed here.
    """
    conversation_id: str
    created_at: float = 0.0
    updated_at: float = 0.0
    last_intent: str = ""
    last_product_id: Optional[str] = None
    last_product_name: Optional[str] = None
    last_product_type: Optional[str] = None
    last_category: Optional[str] = None
    declared_preferences: Dict[str, str] = field(default_factory=dict)
    turns: List[ConversationTurn] = field(default_factory=list)
    turn_count: int = 0
    customer_id: Optional[str] = None


@runtime_checkable
class ConversationStore(Protocol):
    def create(self) -> ConversationState: ...
    def get(self, conversation_id: str) -> ConversationState: ...
    def append_turn(self, conversation_id: str, turn: ConversationTurn) -> ConversationState: ...
    def update_context(self, conversation_id: str, **updates: Any) -> ConversationState: ...
    def delete(self, conversation_id: str) -> None: ...


class InMemoryConversationStore:
    """Thread-unsafe, in-memory conversation store for dev/tests."""

    def __init__(
        self,
        max_turns: int = DEFAULT_MAX_TURNS,
        ttl_seconds: float = DEFAULT_TTL_SECONDS,
        max_context_items: int = DEFAULT_MAX_CONTEXT_ITEMS,
    ) -> None:
        if not isinstance(max_turns, int) or isinstance(max_turns, bool) or max_turns < 1:
            raise ValueError(f"max_turns must be a positive integer, got {max_turns!r}")
        if not isinstance(ttl_seconds, (int, float)) or isinstance(ttl_seconds, bool) or ttl_seconds <= 0:
            raise ValueError(f"ttl_seconds must be a positive number, got {ttl_seconds!r}")
        self._max_turns = max_turns
        self._ttl_seconds = ttl_seconds
        self._max_context_items = max_context_items
        self._store: Dict[str, ConversationState] = {}

    def create(self, conversation_id: Optional[str] = None) -> ConversationState:
        if conversation_id is not None:
            self._validate_id(conversation_id)
            # Reuse the caller-supplied ID when free; a collision with a live
            # conversation is treated as an error rather than silently
            # returning someone else's state.
            if conversation_id in self._store:
                raise ConversationError(
                    f"conversation {conversation_id!r} already exists"
                )
        else:
            conversation_id = str(uuid.uuid4())
        now = time.time()
        state = ConversationState(conversation_id=conversation_id, created_at=now, updated_at=now)
        self._store[conversation_id] = state
        return state

    def get(self, conversation_id: str) -> ConversationState:
        self._validate_id(conversation_id)
        state = self._store.get(conversation_id)
        if state is None:
            raise ConversationNotFoundError(f"conversation {conversation_id!r} not found")
        self._check_ttl(state)
        return state

    def append_turn(self, conversation_id: str, turn: ConversationTurn) -> ConversationState:
        self._validate_id(conversation_id)
        state = self._store.get(conversation_id)
        if state is None:
            raise ConversationNotFoundError(f"conversation {conversation_id!r} not found")
        self._check_ttl(state)
        state.turns.append(turn)
        while len(state.turns) > self._max_turns:
            state.turns.pop(0)
        state.turn_count += 1
        state.updated_at = time.time()
        return state

    def update_context(self, conversation_id: str, **updates: Any) -> ConversationState:
        self._validate_id(conversation_id)
        state = self._store.get(conversation_id)
        if state is None:
            raise ConversationNotFoundError(f"conversation {conversation_id!r} not found")
        self._check_ttl(state)
        _SAFE_FIELDS = {
            "last_intent", "last_product_id", "last_product_name",
            "last_product_type", "last_category", "customer_id",
            "declared_preferences",
        }
        for key, value in updates.items():
            if key.lower() in _SENSITIVE_KEYS:
                continue
            if key in _SAFE_FIELDS:
                if key == "declared_preferences":
                    if isinstance(value, dict):
                        for k, v in value.items():
                            if k.lower() in _SENSITIVE_KEYS:
                                continue
                            if len(state.declared_preferences) >= self._max_context_items:
                                break
                            state.declared_preferences[k] = v
                else:
                    setattr(state, key, value)
        state.updated_at = time.time()
        return state

    def delete(self, conversation_id: str) -> None:
        self._validate_id(conversation_id)
        self._store.pop(conversation_id, None)

    def _validate_id(self, conversation_id: str) -> None:
        if not isinstance(conversation_id, str) or not conversation_id.strip():
            raise ConversationError("conversation_id must be a non-empty string")

    def _check_ttl(self, state: ConversationState) -> None:
        if time.time() - state.updated_at > self._ttl_seconds:
            self._store.pop(state.conversation_id, None)
            raise ConversationExpiredError(
                f"conversation {state.conversation_id!r} has expired (TTL {self._ttl_seconds}s)"
            )

    @property
    def size(self) -> int:
        self._purge_expired()
        return len(self._store)

    def _purge_expired(self) -> None:
        now = time.time()
        expired = [
            cid for cid, state in self._store.items()
            if now - state.updated_at > self._ttl_seconds
        ]
        for cid in expired:
            del self._store[cid]

    @staticmethod
    def sensitive_keys() -> frozenset:
        return _SENSITIVE_KEYS
