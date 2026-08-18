"""Public API contracts (Pydantic models) for the chatbot service."""

from chatbot.app.models.chat_models import (
    MAX_MESSAGE_LENGTH,
    MAX_SEARCH_QUERY_LENGTH,
    ChatIntent,
    ChatRequest,
    ChatResponse,
    ChatSource,
    KnowledgeCategory,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeSearchResult,
    RecommendationItem,
    SupportingFact,
)

__all__ = [
    "MAX_MESSAGE_LENGTH",
    "MAX_SEARCH_QUERY_LENGTH",
    "ChatIntent",
    "ChatRequest",
    "ChatResponse",
    "ChatSource",
    "KnowledgeCategory",
    "KnowledgeSearchRequest",
    "KnowledgeSearchResponse",
    "KnowledgeSearchResult",
    "RecommendationItem",
    "SupportingFact",
]
