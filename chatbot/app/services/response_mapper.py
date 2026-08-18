"""ChatTurnResult → ChatResponse mapping with deterministic answer composition.

Bridges the provider-neutral orchestration result onto the public API
contract.  Three responsibilities:

1. Source mapping — every ``RetrievedChunk`` becomes a ``ChatSource``.
2. Recommendation mapping — ``GroundedRecommendation`` becomes ``RecommendationItem``.
3. Answer composition — fixed templates, no LLM.
"""

from __future__ import annotations

from typing import List, Optional

from chatbot.app.models.chat_models import (
    ChatIntent, ChatResponse, ChatSource, KnowledgeCategory,
    RecommendationItem, SupportingFact,
)
from chatbot.app.rag.models import RetrievedChunk
from chatbot.app.services.orchestrator import ChatTurnResult, OrchestrationStatus

_CATEGORY_ENUM_MAP = {category.value: category for category in KnowledgeCategory}


def _to_category(value: Optional[str]) -> Optional[KnowledgeCategory]:
    if not isinstance(value, str) or not value.strip():
        return None
    return _CATEGORY_ENUM_MAP.get(value.strip())


def _clamp_score(score: float) -> float:
    return max(0.0, min(1.0, float(score)))


def map_chunk_to_source(chunk: RetrievedChunk) -> ChatSource:
    return ChatSource(
        doc_id=chunk.source_id, title=chunk.title,
        source_url=chunk.source_url or None,
        entity=chunk.entity or None, product_id=chunk.product_id,
        category=_to_category(chunk.category),
        retrieval_score=_clamp_score(chunk.score),
    )


def collect_sources(result: ChatTurnResult) -> List[ChatSource]:
    seen: set = set()
    sources: List[ChatSource] = []
    for chunk in result.retrieved_chunks:
        if chunk.source_id in seen:
            continue
        seen.add(chunk.source_id)
        sources.append(map_chunk_to_source(chunk))
    return sources


_DEFAULT_REC_REASON = (
    "Recommended by the bank's existing recommendation engine based on "
    "this customer's profile."
)


def map_recommendation(recommendation) -> RecommendationItem:
    supporting_facts: List[SupportingFact] = []
    source_ids: List[str] = []

    grounding_chunks = getattr(recommendation, "grounding_chunks", None) or []
    for chunk in grounding_chunks:
        if chunk.source_id not in source_ids:
            source_ids.append(chunk.source_id)
        supporting_facts.append(
            SupportingFact(
                fact=(chunk.content or "")[:300],
                source_id=chunk.source_id,
                category=_to_category(chunk.category),
            )
        )

    reason = getattr(recommendation, "recommendation_text", None) or _DEFAULT_REC_REASON

    return RecommendationItem(
        product_id=getattr(recommendation, "canonical_product_id", None),
        product_name=getattr(recommendation, "product_name", "") or "HDFC Bank product",
        reason=reason, supporting_facts=supporting_facts, source_ids=source_ids,
    )


# ── Deterministic answer composition (no LLM) ──────────────────────────

_ANSWER_GROUNDED_INFO = (
    "I found verified HDFC Bank information relevant to your question. "
    "The supporting sources are included below."
)
_ANSWER_NO_EVIDENCE = (
    "I could not confidently verify the requested information from the "
    "current HDFC knowledge base."
)
_ANSWER_AUTH_REQUIRED = (
    "Authenticated customer context is required for a personalized recommendation."
)
_ANSWER_ACCOUNT_NOT_WIRED = (
    "Account-specific information is not currently available through this chatbot."
)
_ANSWER_TRANSACTION_NOT_WIRED = (
    "Transaction information is not currently available through this chatbot."
)
_ANSWER_BLOCKED = "I cannot help with that request."
_ANSWER_OUT_OF_SCOPE = (
    "This assistant can only help with HDFC banking and service-related questions."
)
_ANSWER_SERVICE_UNAVAILABLE = (
    "The banking knowledge service is temporarily unavailable. Please try again later."
)


def _recommendation_answer(result: ChatTurnResult) -> Optional[str]:
    for recommendation in result.recommendations:
        name = getattr(recommendation, "product_name", None)
        if name:
            return (
                f"Based on the bank's existing recommendation engine, "
                f"{name} is a relevant recommendation for this customer. "
                f"Verified product information is included in the supporting sources."
            )
    return None


def compose_answer(result: ChatTurnResult) -> str:
    if result.answer:
        return result.answer
    if result.status is OrchestrationStatus.SUCCESS:
        if result.recommendations:
            composed = _recommendation_answer(result)
            if composed is not None:
                return composed
        if result.retrieved_chunks:
            return _ANSWER_GROUNDED_INFO
        return _ANSWER_NO_EVIDENCE
    if result.status is OrchestrationStatus.NO_EVIDENCE:
        return _ANSWER_NO_EVIDENCE
    if result.status is OrchestrationStatus.NEEDS_CLARIFICATION:
        return result.clarifying_question or _ANSWER_NO_EVIDENCE
    if result.status is OrchestrationStatus.AUTHENTICATED_CONTEXT_REQUIRED:
        return _ANSWER_AUTH_REQUIRED
    if result.status is OrchestrationStatus.ACCOUNT_ACCESS_NOT_WIRED:
        return _ANSWER_ACCOUNT_NOT_WIRED
    if result.status is OrchestrationStatus.TRANSACTION_ACCESS_NOT_WIRED:
        return _ANSWER_TRANSACTION_NOT_WIRED
    if result.status is OrchestrationStatus.BLOCKED:
        return _ANSWER_BLOCKED
    if result.status is OrchestrationStatus.OUT_OF_SCOPE:
        return _ANSWER_OUT_OF_SCOPE
    if result.status is OrchestrationStatus.SERVICE_UNAVAILABLE:
        return _ANSWER_SERVICE_UNAVAILABLE
    return _ANSWER_NO_EVIDENCE


def map_turn_result(result: ChatTurnResult) -> ChatResponse:
    """Map a ChatTurnResult onto the public ChatResponse contract."""
    safety_flags = list(result.safety_flags)
    if result.status is OrchestrationStatus.SERVICE_UNAVAILABLE:
        safety_flags.append("knowledge_service_unavailable")

    return ChatResponse(
        answer=compose_answer(result),
        intent=result.intent if isinstance(result.intent, ChatIntent) else ChatIntent.GENERAL_BANKING_QUERY,
        confidence=float(result.routing_confidence),
        recommendations=[map_recommendation(r) for r in result.recommendations],
        sources=collect_sources(result),
        grounded=bool(result.grounded),
        clarifying_question=result.clarifying_question,
        conversation_id=result.conversation_id,
        safety_flags=safety_flags,
    )
