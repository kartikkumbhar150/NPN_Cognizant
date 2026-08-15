"""Phase 6 request/response contracts for GenAI Personalization.

Responsibility boundary
-----------------------
Upstream systems decide **what** product to offer; Phase 6 decides **how** to
communicate that already-approved product. This service never determines the
product, eligibility, ownership, propensity, segment, events, or reasons —
those arrive here as trusted inputs and are validated strictly.

Privacy
-------
``recommendation_id``, ``customer_id``, and ``source_event_id`` are stored for
internal orchestration and audit only. They must never be forwarded to an LLM
in a future prompt payload.

DS-01 scope: contracts only. No generation, no provider calls, no persistence.
"""

from enum import Enum
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.types import AwareDatetime


class ProductFamily(str, Enum):
    """Product families supported by the Phase 6 contract (first slice)."""

    CREDIT_CARD = "CREDIT_CARD"


class Channel(str, Enum):
    """Marketing channels supported in the first slice."""

    PUSH = "PUSH"
    SMS = "SMS"
    EMAIL = "EMAIL"
    IN_APP = "IN_APP"
    RELATIONSHIP_MANAGER = "RELATIONSHIP_MANAGER"


class EligibilityStatus(str, Enum):
    """Recommendation approval status from the upstream eligibility service."""

    ELIGIBLE = "ELIGIBLE"


class OwnershipStatus(str, Enum):
    """Whether the customer owns a conflicting product."""

    NO_CONFLICT = "NO_CONFLICT"


class ValidationStatus(str, Enum):
    """Outcome of Phase 6 content validation."""

    PASSED = "PASSED"
    FAILED = "FAILED"


class StrictModel(BaseModel):
    """Base for all contract models: reject extra fields, no implicit coercion.

    ``strict=True`` blocks hidden coercion (e.g. strings to numbers/bools).
    Enum and datetime fields opt out per-field below because requests arrive
    as JSON, where enum values and RFC 3339 timestamps are strings — lax mode
    for those fields still requires an exact enum value / valid timestamp, so
    unknown values and malformed datetimes remain rejected.
    """

    model_config = ConfigDict(extra="forbid", strict=True)


# --------------------------------------------------------------------------
# Input contract (request)
# --------------------------------------------------------------------------


class RecentEvent(StrictModel):
    """An important customer event detected by an upstream service."""

    event_type: str
    # RFC 3339 timestamp with offset (as in the upstream fixture). Strict mode
    # disables string parsing, so datetime fields are relaxed to accept the
    # wire format while still requiring a timezone (no naive timestamps).
    occurred_at: AwareDatetime = Field(strict=False)
    source_event_id: str


class RecommendedProduct(StrictModel):
    """The product chosen by the upstream recommendation engine."""

    product_family: ProductFamily = Field(strict=False)
    product_id: str


class DecisionContext(StrictModel):
    """Trusted decision inputs from upstream — read-only for Phase 6."""

    segment_code: str
    recent_events: list[RecentEvent] = Field(min_length=1)
    propensity_score: float = Field(ge=0.0, le=1.0)
    reason_codes: list[str] = Field(min_length=1)
    eligibility_status: EligibilityStatus = Field(strict=False)
    ownership_status: OwnershipStatus = Field(strict=False)


class Preferences(StrictModel):
    """Customer communication preferences."""

    language: str
    requested_channels: list[Annotated[Channel, Field(strict=False)]]


class PersonalizationRequest(StrictModel):
    """Input contract for Phase 6 content generation.

    ``consent_verified`` must be exactly ``true``; a request without verified
    consent is rejected at the boundary.
    """

    recommendation_id: str
    customer_id: str
    recommended_product: RecommendedProduct
    decision_context: DecisionContext
    preferences: Preferences
    consent_verified: Literal[True]


# --------------------------------------------------------------------------
# Output contract (response)
# --------------------------------------------------------------------------


class PushContent(StrictModel):
    """Push notification copy."""

    title: str
    body: str
    fact_refs: list[str] = Field(default_factory=list)


class SmsContent(StrictModel):
    """SMS copy."""

    body: str
    fact_refs: list[str] = Field(default_factory=list)


class EmailContent(StrictModel):
    """Email copy."""

    subject: str
    preheader: str
    body: str
    cta_label: str
    fact_refs: list[str] = Field(default_factory=list)


class InAppContent(StrictModel):
    """In-app message copy."""

    headline: str
    body: str
    cta_label: str
    fact_refs: list[str] = Field(default_factory=list)


class RelationshipManagerContent(StrictModel):
    """Relationship-manager talking script."""

    opening: str
    talking_points: list[str] = Field(default_factory=list)
    closing: str
    fact_refs: list[str] = Field(default_factory=list)


class ChannelContent(StrictModel):
    """Generated copy for every supported channel."""

    push: PushContent
    sms: SmsContent
    email: EmailContent
    in_app: InAppContent
    relationship_manager: RelationshipManagerContent


class GenerationMetadata(StrictModel):
    """Provenance metadata for a generated response."""

    provider: str
    model: str
    prompt_version: str = "v1"
    catalogue_version: str
    generated_at: AwareDatetime = Field(strict=False)
    language: str


class ValidationInfo(StrictModel):
    """Result of Phase 6 content validation (grounding/fact checks in DS-02+)."""

    status: ValidationStatus
    validated_at: AwareDatetime = Field(strict=False)
    violations: list[str] = Field(default_factory=list)


class GenerationResponse(StrictModel):
    """Output contract for Phase 6 content generation."""

    generation_id: UUID
    recommendation_id: str
    product_id: str
    content: ChannelContent
    metadata: GenerationMetadata
    validation: ValidationInfo
