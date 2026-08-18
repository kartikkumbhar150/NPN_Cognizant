"""Multi-turn chatbot orchestration.

Coordinates intent routing, knowledge retrieval, personalized
recommendation, and conversation state for each user turn.

Architecture::

    User message
          ↓
    resolve_message(message, conversation_state)     (pronoun → product name)
          ↓
    IntentRouter.route(normalized_message)
          ↓
    _dispatch(routing_decision, context)
          ├───────────────────┬──────────────────────┐
          ▼                   ▼                      ▼
    KnowledgeRetriever  RecommendationOrchestrator   safe metadata
    general/product     personalized NBO+grounding   (no I/O)
          │                   │
          └─────────┬─────────┘
                    ↓
    ChatTurnResult (structured, provider-neutral)

Design invariants:
- No LLM.  Output is structured data only.
- conversation_id ≠ customer_id.
- PERSONALIZED_RECOMMENDATION: NBO runs only when a trusted
  AuthorizedCustomerContext is supplied.
- UNSAFE_OR_SENSITIVE: no downstream banking services invoked.
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from chatbot.app.config import ChatbotSettings
from chatbot.app.models.chat_models import ChatIntent
from chatbot.app.rag.errors import RetrievalUnavailableError
from chatbot.app.rag.models import RetrievedChunk
from chatbot.app.services.conversation import (
    ConversationNotFoundError,
    ConversationState,
    ConversationStore,
    ConversationTurn,
)
from chatbot.app.services.product_catalog import ProductIdResolver

logger = logging.getLogger(__name__)


class OrchestrationStatus(str):
    SUCCESS = "SUCCESS"
    NO_EVIDENCE = "NO_EVIDENCE"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    AUTHENTICATED_CONTEXT_REQUIRED = "AUTHENTICATED_CONTEXT_REQUIRED"
    ACCOUNT_ACCESS_NOT_WIRED = "ACCOUNT_ACCESS_NOT_WIRED"
    TRANSACTION_ACCESS_NOT_WIRED = "TRANSACTION_ACCESS_NOT_WIRED"
    BLOCKED = "BLOCKED"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"


@dataclass(frozen=True)
class ChatTurnResult:
    """Structured output of one orchestrated turn."""

    conversation_id: str
    intent: ChatIntent
    routing_confidence: float
    status: OrchestrationStatus
    answer: str = ""
    retrieved_chunks: List[RetrievedChunk] = field(default_factory=list)
    recommendations: list = field(default_factory=list)
    clarifying_question: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    safety_flags: tuple = ()
    grounded: bool = False
    retrieval_query: str = ""

    @property
    def has_evidence(self) -> bool:
        return bool(self.retrieved_chunks) or bool(self.recommendations)


class OrchestrationError(Exception):
    """Base class for orchestration failures."""


class RetrievalFailedError(OrchestrationError):
    """Knowledge retrieval failed during orchestration."""


# ── Reference resolution (structured, no NLP) ─────────────────────────────

_PRONOUN_PRODUCT_RE = None

_PRONOUN_PATTERNS = [
    r"\b(?:its|their|that|this|the)\s+(?:fees?|charges?|features?|benefits?|"
    r"eligibility|details?|requirements?|interest\s+rates?|rewards?|"
    r"annual\s+fee|joining\s+fee|credit\s+limit|cashback)\b",
    r"\bwhat\s+(?:about|are)\s+(?:its|their|that|this|the)\b",
    r"\btell\s+me\s+(?:more|about)\s+(?:its|that|this)\b",
    r"\b(?:compare|vs\.?)\s+(?:it|that|this)\s+(?:with\b|and\b)",
    r"\b(?:what|how)\s+(?:is|are|about)\s+(?:it|that|this|the\s+(?:card|loan|product|plan))\b",
]


def _compile_pronoun_re():
    global _PRONOUN_PRODUCT_RE
    if _PRONOUN_PRODUCT_RE is None:
        _PRONOUN_PRODUCT_RE = re.compile(
            "|".join(_PRONOUN_PATTERNS), re.IGNORECASE,
        )
    return _PRONOUN_PRODUCT_RE


def _is_pronoun_reference(message: str) -> bool:
    return bool(_compile_pronoun_re().search(message))


def resolve_message(message: str, state: Optional[ConversationState]) -> str:
    """Resolve safe conversational references in *message*.

    If the message uses pronoun-like product references ("its fees")
    and the conversation state knows a product, prepend the product name.
    """
    if state is None:
        return message
    if not _is_pronoun_reference(message):
        return message
    product_name = state.last_product_name
    if product_name:
        return f"{product_name} {message}"
    return message


# ── Clarifying templates ─────────────────────────────────────────────────────

_CLARIFICATIONS = {
    "no_product_context": "Which HDFC product would you like information about?",
    "no_comparison_targets": "Which two HDFC products would you like to compare?",
    "auth_required": (
        "Please sign in or provide authenticated customer context to "
        "receive a personalized recommendation."
    ),
    "account_not_wired": "Account access is not available through this chatbot interface.",
    "transaction_not_wired": "Transaction access is not available through this chatbot interface.",
}


# ── ChatbotOrchestrator ─────────────────────────────────────────────────────

class ChatbotOrchestrator:
    """Coordinates intent routing, retrieval, and recommendation per turn.

    All dependencies are injected.  No global state.  No LLM.
    """

    def __init__(
        self,
        intent_router,
        knowledge_retriever,
        conversation_store: ConversationStore,
        recommendation_orchestrator=None,
        product_resolver: Optional[ProductIdResolver] = None,
        settings: Optional[ChatbotSettings] = None,
        context_builder=None,
    ) -> None:
        self._intent_router = intent_router
        self._knowledge_retriever = knowledge_retriever
        self._recommendation_orchestrator = recommendation_orchestrator
        self._conversation_store = conversation_store
        self._product_resolver = product_resolver
        self._settings = settings or ChatbotSettings.from_env()
        self._context_builder = context_builder

    async def handle_turn(
        self,
        message: str,
        customer_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> ChatTurnResult:
        """Orchestrate one user message into a structured result.

        This is the public async API consumed by the FastAPI router.
        ``customer_id`` is the trusted-context channel: when the stack has
        a context builder, the ID is resolved to an
        ``AuthorizedCustomerContext``; unknown IDs raise
        ``CustomerNotFoundError`` (mapped to 404 by the API layer).
        """
        from chatbot.app.services.customer_context import CustomerNotFoundError

        authorized_context = None
        if customer_id and self._context_builder is not None:
            # May raise CustomerNotFoundError — trusted-context failures
            # must surface, never silently degrade to anonymous.
            authorized_context = self._context_builder.build_context(customer_id)
        return self.process_turn(
            message=message,
            conversation_id=session_id,
            authorized_context=authorized_context,
        )

    def process_turn(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        authorized_context=None,
    ) -> ChatTurnResult:
        """Orchestrate one user message into a structured result."""
        if not isinstance(message, str) or not message.strip():
            raise ValueError("message must be a non-empty string")

        conv_state = self._get_or_create_conversation(conversation_id)
        cid = conv_state.conversation_id

        resolved_message = resolve_message(message, conv_state)

        routing = self._intent_router.route(resolved_message)

        result = self._dispatch(
            routing=routing, message=resolved_message,
            conv_state=conv_state, authorized_context=authorized_context,
        )

        self._update_conversation(conv_state, routing, result, resolved_message)
        return result

    # ── Conversation management ──────────────────────────────────────────

    def _get_or_create_conversation(self, conversation_id: Optional[str]) -> ConversationState:
        if conversation_id is not None:
            try:
                return self._conversation_store.get(conversation_id)
            except ConversationNotFoundError:
                pass
        return self._conversation_store.create(conversation_id)

    def _update_conversation(self, conv_state, routing, result, resolved_message) -> None:
        turn = ConversationTurn(
            role="user", intent=routing.intent.value,
            safe_summary=self._safe_summary(routing, result),
            timestamp=time.time(),
        )
        self._conversation_store.append_turn(conv_state.conversation_id, turn)

        updates: Dict[str, Any] = {"last_intent": routing.intent.value}

        product_id, product_name, product_type, category = self._extract_product_references(result)
        if product_id:
            updates["last_product_id"] = product_id
        if product_name:
            updates["last_product_name"] = product_name
        if product_type:
            updates["last_product_type"] = product_type
        if category:
            updates["last_category"] = category

        if updates:
            self._conversation_store.update_context(conv_state.conversation_id, **updates)

    @staticmethod
    def _safe_summary(routing, result) -> str:
        parts = [routing.intent.value]
        if result.retrieved_chunks:
            parts.append(f"{len(result.retrieved_chunks)} chunks")
        if result.recommendations:
            parts.append(f"{len(result.recommendations)} recommendations")
        return " | ".join(parts)

    @staticmethod
    def _extract_product_references(result):
        product_id = None
        product_name = None
        product_type = None
        category = None
        if result.retrieved_chunks:
            first = result.retrieved_chunks[0]
            if first.product_id:
                product_id = first.product_id
            if first.product_name:
                product_name = first.product_name
            if first.category:
                category = first.category
        if result.recommendations and not product_id:
            rec = result.recommendations[0]
            if hasattr(rec, "canonical_product_id") and rec.canonical_product_id:
                product_id = rec.canonical_product_id
            if hasattr(rec, "product_name") and rec.product_name:
                product_name = rec.product_name
            if hasattr(rec, "product_type") and rec.product_type:
                product_type = rec.product_type
        return product_id, product_name, product_type, category

    # ── Intent dispatch ──────────────────────────────────────────────────

    def _dispatch(self, routing, message, conv_state, authorized_context) -> ChatTurnResult:
        intent = routing.intent

        if intent is ChatIntent.UNSAFE_OR_SENSITIVE:
            return self._blocked(routing, conv_state)
        if intent is ChatIntent.OUT_OF_SCOPE:
            return self._out_of_scope(routing, conv_state)
        if intent is ChatIntent.CUSTOMER_ACCOUNT_QUERY:
            return self._account_not_wired(routing, conv_state)
        if intent is ChatIntent.TRANSACTION_QUERY:
            return self._transaction_not_wired(routing, conv_state)
        if intent is ChatIntent.PERSONALIZED_RECOMMENDATION:
            return self._personalized_recommendation(routing, conv_state, authorized_context)

        if routing.requires_retrieval:
            return self._retrieval_turn(routing, message, conv_state)

        return ChatTurnResult(
            conversation_id=conv_state.conversation_id, intent=intent,
            routing_confidence=routing.confidence,
            status=OrchestrationStatus.NO_EVIDENCE,
            warnings=["no downstream handler for intent"],
        )

    # ── Retrieval turn ──────────────────────────────────────────────────

    def _retrieval_turn(self, routing, message, conv_state) -> ChatTurnResult:
        cid = conv_state.conversation_id
        warnings: List[str] = []
        chunks: List[RetrievedChunk] = []
        grounded = False
        status = OrchestrationStatus.NO_EVIDENCE
        retrieval_query = message.strip()

        follow_up = _is_pronoun_reference(message)
        product_id_filter = conv_state.last_product_id if follow_up else None
        category_filter = conv_state.last_category if follow_up else None

        if self._knowledge_retriever is None:
            return ChatTurnResult(
                conversation_id=cid, intent=routing.intent,
                routing_confidence=routing.confidence,
                status=OrchestrationStatus.SERVICE_UNAVAILABLE,
                warnings=["knowledge retriever not initialized"],
                safety_flags=routing.safety_flags,
                retrieval_query=retrieval_query,
            )

        try:
            filters: Dict[str, Any] = {"entity": "HDFC Bank"}
            if product_id_filter:
                filters["product_id"] = product_id_filter
            if category_filter:
                filters["category"] = category_filter

            retrieval = self._knowledge_retriever.search(
                retrieval_query,
                limit=self._settings.rag_top_k,
                entity=filters.get("entity") if len(filters) > 1 else None,
                product_id=product_id_filter,
                category=category_filter,
            )
            chunks = list(retrieval.items)
            warnings.extend(retrieval.warnings)
        except RetrievalUnavailableError as exc:
            warnings.append(f"retrieval unavailable: {exc}")
            return ChatTurnResult(
                conversation_id=cid, intent=routing.intent,
                routing_confidence=routing.confidence,
                status=OrchestrationStatus.SERVICE_UNAVAILABLE,
                warnings=warnings, safety_flags=routing.safety_flags,
                retrieval_query=retrieval_query,
            )

        if chunks:
            grounded = True
            status = OrchestrationStatus.SUCCESS
        else:
            status = OrchestrationStatus.NO_EVIDENCE

        clarifying = None
        if routing.intent is ChatIntent.PRODUCT_COMPARISON and not chunks:
            clarifying = _CLARIFICATIONS["no_comparison_targets"]
            status = OrchestrationStatus.NEEDS_CLARIFICATION
        if (not chunks and not conv_state.last_product_name
                and _is_pronoun_reference(message)):
            clarifying = _CLARIFICATIONS["no_product_context"]
            status = OrchestrationStatus.NEEDS_CLARIFICATION

        return ChatTurnResult(
            conversation_id=cid, intent=routing.intent,
            routing_confidence=routing.confidence, status=status,
            retrieved_chunks=chunks, clarifying_question=clarifying,
            warnings=warnings, safety_flags=routing.safety_flags,
            grounded=grounded, retrieval_query=retrieval_query,
        )

    # ── Personalized recommendation ──────────────────────────────

    def _personalized_recommendation(self, routing, conv_state, authorized_context) -> ChatTurnResult:
        cid = conv_state.conversation_id
        if authorized_context is None:
            return ChatTurnResult(
                conversation_id=cid, intent=routing.intent,
                routing_confidence=routing.confidence,
                status=OrchestrationStatus.AUTHENTICATED_CONTEXT_REQUIRED,
                clarifying_question=_CLARIFICATIONS["auth_required"],
                warnings=["personalized recommendation requires authenticated customer context"],
                safety_flags=routing.safety_flags,
            )
        if self._recommendation_orchestrator is None:
            return ChatTurnResult(
                conversation_id=cid, intent=routing.intent,
                routing_confidence=routing.confidence,
                status=OrchestrationStatus.SERVICE_UNAVAILABLE,
                warnings=["recommendation orchestrator not initialized"],
                safety_flags=routing.safety_flags,
            )
        try:
            reco_list = self._recommendation_orchestrator.recommend(authorized_context)
        except Exception as exc:
            logger.warning("recommendation orchestration failed: %s", exc)
            return ChatTurnResult(
                conversation_id=cid, intent=routing.intent,
                routing_confidence=routing.confidence,
                status=OrchestrationStatus.SERVICE_UNAVAILABLE,
                warnings=[f"recommendation failed: {type(exc).__name__}"],
                safety_flags=routing.safety_flags,
            )

        grounded = bool(reco_list)
        status = OrchestrationStatus.SUCCESS if grounded else OrchestrationStatus.NO_EVIDENCE

        return ChatTurnResult(
            conversation_id=cid, intent=routing.intent,
            routing_confidence=routing.confidence, status=status,
            recommendations=reco_list, warnings=[],
            safety_flags=routing.safety_flags, grounded=grounded,
        )

    # ── Blocked / out-of-scope / not-wired paths ───────────────────────

    @staticmethod
    def _blocked(routing, conv_state) -> ChatTurnResult:
        return ChatTurnResult(
            conversation_id=conv_state.conversation_id, intent=routing.intent,
            routing_confidence=routing.confidence,
            status=OrchestrationStatus.BLOCKED, safety_flags=routing.safety_flags,
        )

    @staticmethod
    def _out_of_scope(routing, conv_state) -> ChatTurnResult:
        return ChatTurnResult(
            conversation_id=conv_state.conversation_id, intent=routing.intent,
            routing_confidence=routing.confidence,
            status=OrchestrationStatus.OUT_OF_SCOPE,
        )

    @staticmethod
    def _account_not_wired(routing, conv_state) -> ChatTurnResult:
        return ChatTurnResult(
            conversation_id=conv_state.conversation_id, intent=routing.intent,
            routing_confidence=routing.confidence,
            status=OrchestrationStatus.ACCOUNT_ACCESS_NOT_WIRED,
            clarifying_question=_CLARIFICATIONS["account_not_wired"],
            warnings=["account access is not available through this chatbot"],
        )

    @staticmethod
    def _transaction_not_wired(routing, conv_state) -> ChatTurnResult:
        return ChatTurnResult(
            conversation_id=conv_state.conversation_id, intent=routing.intent,
            routing_confidence=routing.confidence,
            status=OrchestrationStatus.TRANSACTION_ACCESS_NOT_WIRED,
            clarifying_question=_CLARIFICATIONS["transaction_not_wired"],
            warnings=["transaction access is not available through this chatbot"],
        )
