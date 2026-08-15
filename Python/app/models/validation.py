"""Structured validation result for the Phase 6 hallucination guard.

The guard's authoritative output is a ``ValidationResult``: PASSED with no
violations, or FAILED with a structured list of controlled ``Violation``
objects. Arbitrary exception strings are never used as the contract.
"""

from enum import Enum

from pydantic import Field

from app.models.personalization import Channel, StrictModel, ValidationStatus


class ViolationCode(str, Enum):
    """Controlled, machine-readable violation categories."""

    UNKNOWN_FACT_REFERENCE = "UNKNOWN_FACT_REFERENCE"
    UNSUPPORTED_PRODUCT_NAME = "UNSUPPORTED_PRODUCT_NAME"
    UNSUPPORTED_MONETARY_CLAIM = "UNSUPPORTED_MONETARY_CLAIM"
    UNSUPPORTED_PERCENTAGE_CLAIM = "UNSUPPORTED_PERCENTAGE_CLAIM"
    UNSUPPORTED_RATE_CLAIM = "UNSUPPORTED_RATE_CLAIM"
    UNSUPPORTED_REWARD_CLAIM = "UNSUPPORTED_REWARD_CLAIM"
    UNSUPPORTED_LOUNGE_CLAIM = "UNSUPPORTED_LOUNGE_CLAIM"
    UNSUPPORTED_INSURANCE_CLAIM = "UNSUPPORTED_INSURANCE_CLAIM"
    UNSUPPORTED_ELIGIBILITY_CLAIM = "UNSUPPORTED_ELIGIBILITY_CLAIM"
    PROHIBITED_ABSOLUTE_CLAIM = "PROHIBITED_ABSOLUTE_CLAIM"
    UNAPPROVED_URL = "UNAPPROVED_URL"
    UNAPPROVED_PHONE_NUMBER = "UNAPPROVED_PHONE_NUMBER"
    UNAPPROVED_DEADLINE = "UNAPPROVED_DEADLINE"
    UNAPPROVED_OFFER_CODE = "UNAPPROVED_OFFER_CODE"
    PII_LEAK = "PII_LEAK"
    INTERNAL_IDENTIFIER_LEAK = "INTERNAL_IDENTIFIER_LEAK"
    CHANNEL_LENGTH_EXCEEDED = "CHANNEL_LENGTH_EXCEEDED"


class Violation(StrictModel):
    """One structured safety violation found in generated content."""

    code: ViolationCode
    channel: Channel
    field: str
    claim: str
    detail: str


class ValidationResult(StrictModel):
    """Deterministic outcome of hallucination-guard validation."""

    status: ValidationStatus
    violations: list[Violation] = Field(default_factory=list)

    @classmethod
    def passed(cls) -> "ValidationResult":
        return cls(status=ValidationStatus.PASSED, violations=[])

    @classmethod
    def failed(cls, violations: list[Violation]) -> "ValidationResult":
        return cls(status=ValidationStatus.FAILED, violations=violations)
