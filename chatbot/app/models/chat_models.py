"""Strict Pydantic contracts for the HDFC banking chatbot.

All models forbid extra fields (``extra="forbid"``) so unknown client
input fails loudly at the API boundary instead of silently flowing into
later phases.

Security note on ``ChatRequest.customer_id``: it is the *trusted-context
channel only*.  In the standalone deployment this field is supplied by
the calling application after its own authentication (same
employee-dashboard trust model the existing api_server uses for its
customer-analysis endpoints).  Customer identity is never derived from
chat message text.
"""

from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Hard upper bound for a single chat message to prevent pathological requests.
MAX_MESSAGE_LENGTH = 2000
MAX_SEARCH_QUERY_LENGTH = 500


class ChatIntent(str, Enum):
    """Intents the chatbot router classifies into."""

    GENERAL_BANKING_QUERY = "GENERAL_BANKING_QUERY"
    PRODUCT_INFORMATION = "PRODUCT_INFORMATION"
    PRODUCT_COMPARISON = "PRODUCT_COMPARISON"
    PERSONALIZED_RECOMMENDATION = "PERSONALIZED_RECOMMENDATION"
    CUSTOMER_ACCOUNT_QUERY = "CUSTOMER_ACCOUNT_QUERY"
    TRANSACTION_QUERY = "TRANSACTION_QUERY"
    SERVICE_HELP = "SERVICE_HELP"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    UNSAFE_OR_SENSITIVE = "UNSAFE_OR_SENSITIVE"


class KnowledgeCategory(str, Enum):
    """Knowledge-base categories used for Qdrant payload filtering."""

    ACCOUNTS = "accounts"
    DEPOSITS = "deposits"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    LOANS = "loans"
    PAYMENTS = "payments"
    INVESTMENTS = "investments"
    INSURANCE = "insurance"
    FOREX = "forex"
    NRI = "nri"
    BUSINESS_BANKING = "business_banking"
    DIGITAL_BANKING = "digital_banking"
    CUSTOMER_SERVICE = "customer_service"


class ChatRequest(BaseModel):
    """Inbound chat message."""

    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=MAX_MESSAGE_LENGTH)
    conversation_id: Optional[UUID] = None
    customer_id: Optional[str] = None
    phone_number: Optional[str] = Field(
        default=None,
        description="Customer mobile number (e.g. 9876543210 or +919876543210). "
                    "If provided, the service resolves it to a customer_id automatically.",
    )

    @field_validator("message")
    @classmethod
    def _reject_blank_message(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("message must not be empty or whitespace-only")
        return stripped


class ChatEmailRequest(BaseModel):
    """Inbound chat message identifying user by email instead of phone number."""

    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=MAX_MESSAGE_LENGTH)
    conversation_id: Optional[UUID] = None
    email: str = Field(
        description="Customer email address. Resolves to a customer_id automatically."
    )

    @field_validator("message")
    @classmethod
    def _reject_blank_message(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("message must not be empty or whitespace-only")
        return stripped



class ChatSource(BaseModel):
    """Provenance reference for retrieved knowledge."""

    model_config = ConfigDict(extra="forbid")

    doc_id: str
    title: str
    source_url: Optional[str] = None
    entity: Optional[str] = None
    product_id: Optional[str] = None
    category: Optional[KnowledgeCategory] = None
    retrieval_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class SupportingFact(BaseModel):
    """A single grounded fact backing an answer or recommendation."""

    model_config = ConfigDict(extra="forbid")

    fact: str
    source_id: Optional[str] = None
    category: Optional[KnowledgeCategory] = None


class RecommendationItem(BaseModel):
    """A recommendation produced by the existing NBO engine.

    The LLM never originates recommendations; this item explains an
    engine output that already carries evidence.  ``source_ids``
    reference ``ChatSource.doc_id`` values, keeping every recommendation
    traceable to knowledge.
    """

    model_config = ConfigDict(extra="forbid")

    product_id: Optional[str] = None  # canonical product_code (e.g. "HDFCMB+")
    product_name: str
    reason: str
    supporting_facts: List[SupportingFact] = Field(default_factory=list)
    source_ids: List[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    """Validated chatbot response.

    ``grounded`` is ``true`` only when evidence came from Qdrant
    knowledge or a grounded NBO recommendation.  ``safety_flags`` are
    short machine-readable markers (e.g. ``unsafe_query``).
    """

    model_config = ConfigDict(extra="forbid")

    answer: str
    intent: ChatIntent
    confidence: float = Field(ge=0.0, le=1.0)
    recommendations: List[RecommendationItem] = Field(default_factory=list)
    sources: List[ChatSource] = Field(default_factory=list)
    grounded: bool = False
    clarifying_question: Optional[str] = None
    conversation_id: str
    safety_flags: List[str] = Field(default_factory=list)


class KnowledgeSearchRequest(BaseModel):
    """Filtered semantic knowledge search."""

    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=MAX_SEARCH_QUERY_LENGTH)
    category: Optional[KnowledgeCategory] = None
    entity: Optional[str] = None
    limit: int = Field(default=5, ge=1, le=20)

    @field_validator("query")
    @classmethod
    def _reject_blank_query(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("query must not be empty or whitespace-only")
        return stripped


class KnowledgeSearchResult(BaseModel):
    """One retrieved knowledge chunk with its provenance."""

    model_config = ConfigDict(extra="forbid")

    doc_id: str
    title: str
    snippet: str
    source_url: Optional[str] = None
    entity: Optional[str] = None
    product_id: Optional[str] = None
    category: Optional[KnowledgeCategory] = None
    retrieval_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class KnowledgeSearchResponse(BaseModel):
    """Result envelope for knowledge search."""

    model_config = ConfigDict(extra="forbid")

    query: str
    results: List[KnowledgeSearchResult] = Field(default_factory=list)
