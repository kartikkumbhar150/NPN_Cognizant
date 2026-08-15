"""Deterministic hallucination guard for Phase 6 (DS-05).

The approved product catalogue (via ``GroundedProductFacts``) is the factual
authority. Generated content is compared against it:

    GeneratedContent + GroundedProductFacts  ->  ValidationResult (PASSED/FAILED)

This is a deterministic safety gate, NOT another LLM. A valid ``fact_ref``
never makes content safe by itself — every customer-facing text field is
checked for unsupported monetary/percentage/rate/reward/lounge/insurance/
eligibility claims, prohibited absolute wording, invented URLs/phones/
deadlines/offer codes, and identifier leakage.

The guard never chooses products, computes eligibility/propensity/ownership,
creates campaigns, calls a provider, or rewrites generated text into safe
text. Regeneration/fallback belong to DS-06 orchestration.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Collection, Iterable

from app.models.generation import GeneratedContent
from app.models.personalization import Channel, ValidationStatus
from app.models.product import GroundedFactCategory, GroundedProductFacts
from app.models.validation import ValidationResult, Violation, ViolationCode
from app.services.prompt_builder import LIMITS as PROMPT_LIMITS

# --------------------------------------------------------------------------
# Central prototype length limits (validation side).
# Push/SMS mirror the DS-03 prompt limits; the rest are defined here only.
# --------------------------------------------------------------------------

PUSH_TITLE_MAX = PROMPT_LIMITS["push_title_max"]  # 60
PUSH_BODY_MAX = PROMPT_LIMITS["push_body_max"]  # 160
SMS_BODY_MAX = PROMPT_LIMITS["sms_body_max"]  # 160
EMAIL_SUBJECT_MAX = 120
EMAIL_PREHEADER_MAX = 160
EMAIL_BODY_MAX = 1000
IN_APP_HEADLINE_MAX = 60
IN_APP_BODY_MAX = 240
CTA_LABEL_MAX = 40
RM_OPENING_MAX = 200
RM_TALKING_POINT_MAX = 200
RM_CLOSING_MAX = 200

# --------------------------------------------------------------------------
# Deterministic claim patterns (conservative; prototype-appropriate).
# --------------------------------------------------------------------------

_CURRENCY_PATTERN = re.compile(r"(?:₹|rs\.?|inr|usd|eur|\$)\s*(\d[\d,]*(?:\.\d+)?)", re.IGNORECASE)
_PERCENT_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*%")
_RATE_KEYWORDS = re.compile(r"\b(interest|rate|forex|apr|apy)\b", re.IGNORECASE)
_MULTIPLIER_PATTERN = re.compile(r"(\d+)\s*[x×]\s*(rewards?|points|multiplier)", re.IGNORECASE)
_LOUNGE_COUNT_PATTERN = re.compile(
    r"(\d+)\s*(?:(domestic|international)\s+)?lounge\s+(?:visits|access)", re.IGNORECASE
)
_REWARD_KEYWORDS = re.compile(r"\b(rewards?|reward points|points|cashback|cash back)\b", re.IGNORECASE)
_INSURANCE_KEYWORDS = re.compile(
    r"\b(insurance|insured)\b|accident cover|comprehensive cover|health cover", re.IGNORECASE
)
_ELIGIBILITY_KEYWORDS = re.compile(
    r"guaranteed approval|pre[- ]?approved|preapproval|instant approval|"
    r"approval guaranteed|everyone is eligible|eligible for everyone|no credit check",
    re.IGNORECASE,
)
_PROHIBITED_ABSOLUTE = re.compile(
    r"guaranteed|risk[- ]?free|unlimited|always|best card|number one card|"
    r"zero risk|free forever",
    re.IGNORECASE,
)
_URL_PATTERN = re.compile(r"https?://|www\.")
_PHONE_MOBILE_PATTERN = re.compile(r"(?:\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}(?!\d)")
_PHONE_TOLLFREE_PATTERN = re.compile(r"1[89]00[\s-]?\d{3,}")
_DEADLINE_KEYWORDS = re.compile(
    r"offer ends|offer expires|expires on|apply by|valid for|valid until|"
    r"last date|hurry|limited period|limited time|for a limited",
    re.IGNORECASE,
)
_OFFER_CODE_PATTERN = re.compile(
    r"use code|offer code|promo code|coupon code|voucher code|code [a-z0-9]{3,}",
    re.IGNORECASE,
)
_IDENTIFIER_PATTERN = re.compile(
    r"\bcust\d+\b|customer_id|recommendation_id|source_event_id|"
    r"account_id|card_id|transaction_id|kyc",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class _GroundedContext:
    """Safe, derived validation context (never customer data)."""

    allowed_fact_ids: frozenset[str]
    product_name: str
    supported_numbers: frozenset[str]
    domestic_lounge_visits: int | None
    international_lounge_visits: int | None
    reward_facts_exist: bool
    cashback_supported: bool
    insurance_supported: bool
    free_supported: bool
    multiplier_supported: bool


def _normalize(text: str) -> str:
    """Conservative normalization for matching: collapse whitespace, keep case."""
    return re.sub(r"\s+", " ", text).strip()


def _numbers_in(text: str) -> set[str]:
    """All integer tokens in ``text``, normalized (commas and leading zeros removed)."""
    numbers: set[str] = set()
    for token in re.findall(r"\d[\d,]*(?:\.\d+)?", text):
        numbers.add(str(int(float(token.replace(",", "")))))
    return numbers


class HallucinationGuard:
    """Deterministic, offline safety validator for generated Phase 6 content.

    ``known_product_names``: safe set of other catalogue product names used to
    detect wrong-product injections (tests inject a small set; production can
    pass the full catalogue name set). ``prohibited_identifiers``: known
    internal identifier values (e.g. fixture customer/recommendation/event
    IDs) that must never appear in customer-facing text.
    """

    def __init__(
        self,
        *,
        known_product_names: Collection[str] = (),
        prohibited_identifiers: Collection[str] = (),
    ) -> None:
        self._known_product_names = tuple(name.strip() for name in known_product_names if name.strip())
        self._prohibited_identifiers = tuple(
            identifier for identifier in prohibited_identifiers if identifier.strip()
        )

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def validate(self, content: GeneratedContent, grounded: GroundedProductFacts) -> ValidationResult:
        context = self._build_context(grounded)
        violations: list[Violation] = []

        for channel in content.populated_channels():
            channel_content = getattr(content, channel.value.lower())
            if channel_content is None:
                continue
            self._validate_fact_refs(channel, channel_content.fact_refs, context, violations)
            for field, text in self._iter_text_fields(channel_content):
                self._validate_length(channel, field, text, violations)
                self._validate_text(channel, field, text, context, violations)

        if not violations:
            return ValidationResult.passed()
        return ValidationResult.failed(self._dedupe(violations))

    # ------------------------------------------------------------------
    # Context derivation (from approved grounded facts only)
    # ------------------------------------------------------------------

    def _build_context(self, grounded: GroundedProductFacts) -> _GroundedContext:
        facts = grounded.facts
        allowed = frozenset(fact.fact_id for fact in facts)

        supported_numbers: set[str] = set()
        domestic: int | None = None
        international: int | None = None
        reward_facts = False
        cashback = False
        insurance = False
        free_anywhere = False
        multiplier = False

        for fact in facts:
            value = fact.value
            if fact.fact_id != "product_id":
                supported_numbers |= _numbers_in(value)
            if fact.fact_id == "domestic_lounge_visits":
                domestic = _as_count(value)
            elif fact.fact_id == "international_lounge_visits":
                international = _as_count(value)
            if fact.category is GroundedFactCategory.REWARDS:
                reward_facts = True
            lowered = value.casefold()
            if "cashback" in lowered or "cash back" in lowered:
                cashback = True
            if "insurance" in lowered or "insured" in lowered or "accident cover" in lowered:
                insurance = True
            if "free" in lowered:
                free_anywhere = True
            if _MULTIPLIER_PATTERN.search(value):
                multiplier = True

        if grounded.approved_description:
            supported_numbers |= _numbers_in(grounded.approved_description)

        return _GroundedContext(
            allowed_fact_ids=frozenset(allowed),
            product_name=grounded.product_name.casefold(),
            supported_numbers=frozenset(supported_numbers),
            domestic_lounge_visits=domestic,
            international_lounge_visits=international,
            reward_facts_exist=reward_facts,
            cashback_supported=cashback,
            insurance_supported=insurance,
            free_supported=free_anywhere,
            multiplier_supported=multiplier,
        )

    # ------------------------------------------------------------------
    # Per-field checks
    # ------------------------------------------------------------------

    def _validate_fact_refs(
        self,
        channel: Channel,
        fact_refs: list[str],
        context: _GroundedContext,
        violations: list[Violation],
    ) -> None:
        for ref in fact_refs:
            if ref not in context.allowed_fact_ids:
                self._add(
                    violations,
                    ViolationCode.UNKNOWN_FACT_REFERENCE,
                    channel,
                    "fact_refs",
                    ref,
                    f"fact id {ref!r} is not present in the approved grounded facts",
                )

    def _validate_text(
        self,
        channel: Channel,
        field: str,
        text: str,
        context: _GroundedContext,
        violations: list[Violation],
    ) -> None:
        self._check_product_identity(channel, field, text, context, violations)
        self._check_money(channel, field, text, context, violations)
        self._check_percentage(channel, field, text, context, violations)
        self._check_rewards(channel, field, text, context, violations)
        self._check_lounge(channel, field, text, context, violations)
        self._check_insurance(channel, field, text, context, violations)
        self._check_eligibility(channel, field, text, violations)
        self._check_prohibited_absolute(channel, field, text, violations)
        self._check_url(channel, field, text, violations)
        self._check_phone(channel, field, text, violations)
        self._check_deadline(channel, field, text, violations)
        self._check_offer_code(channel, field, text, violations)
        self._check_identifiers(channel, field, text, violations)

    def _check_product_identity(
        self,
        channel: Channel,
        field: str,
        text: str,
        context: _GroundedContext,
        violations: list[Violation],
    ) -> None:
        lowered = text.casefold()
        for name in self._known_product_names:
            if name.casefold() in lowered and name.casefold() != context.product_name:
                self._add(
                    violations,
                    ViolationCode.UNSUPPORTED_PRODUCT_NAME,
                    channel,
                    field,
                    name,
                    "generated content introduces a banking product different from the approved product",
                )
                return

    def _check_money(
        self,
        channel: Channel,
        field: str,
        text: str,
        context: _GroundedContext,
        violations: list[Violation],
    ) -> None:
        for match in _CURRENCY_PATTERN.finditer(text):
            amount = _normalize_number(match.group(1))
            if amount not in context.supported_numbers:
                self._add(
                    violations,
                    ViolationCode.UNSUPPORTED_MONETARY_CLAIM,
                    channel,
                    field,
                    match.group(0),
                    f"monetary amount {amount!r} is not present in the approved grounded facts",
                )

    def _check_percentage(
        self,
        channel: Channel,
        field: str,
        text: str,
        context: _GroundedContext,
        violations: list[Violation],
    ) -> None:
        for match in _PERCENT_PATTERN.finditer(text):
            value = _normalize_number(match.group(1))
            if value not in context.supported_numbers:
                code = (
                    ViolationCode.UNSUPPORTED_RATE_CLAIM
                    if _RATE_KEYWORDS.search(text)
                    else ViolationCode.UNSUPPORTED_PERCENTAGE_CLAIM
                )
                self._add(
                    violations,
                    code,
                    channel,
                    field,
                    match.group(0),
                    f"percentage value {value!r} is not present in the approved grounded facts",
                )

    def _check_rewards(
        self,
        channel: Channel,
        field: str,
        text: str,
        context: _GroundedContext,
        violations: list[Violation],
    ) -> None:
        lowered = text.casefold()
        if "cashback" in lowered or "cash back" in lowered:
            if not context.cashback_supported:
                self._add(
                    violations,
                    ViolationCode.UNSUPPORTED_REWARD_CLAIM,
                    channel,
                    field,
                    "cashback claim",
                    "cashback is not supported by any approved grounded fact",
                )
        for match in _MULTIPLIER_PATTERN.finditer(text):
            if not context.multiplier_supported:
                self._add(
                    violations,
                    ViolationCode.UNSUPPORTED_REWARD_CLAIM,
                    channel,
                    field,
                    match.group(0),
                    "quantitative reward multiplier is not supported by any approved grounded fact",
                )
        if _REWARD_KEYWORDS.search(text) and not context.reward_facts_exist:
            self._add(
                violations,
                ViolationCode.UNSUPPORTED_REWARD_CLAIM,
                channel,
                field,
                "reward claim",
                "no approved grounded reward fact exists to support this claim",
            )

    def _check_lounge(
        self,
        channel: Channel,
        field: str,
        text: str,
        context: _GroundedContext,
        violations: list[Violation],
    ) -> None:
        lowered = text.casefold()
        if "lounge" not in lowered:
            return

        if "unlimited" in lowered:
            self._add(
                violations,
                ViolationCode.UNSUPPORTED_LOUNGE_CLAIM,
                channel,
                field,
                "unlimited lounge",
                "unlimited lounge access is not supported (999 is an undocumented sentinel, never a real entitlement)",
            )
        if "free" in lowered and not context.free_supported:
            self._add(
                violations,
                ViolationCode.UNSUPPORTED_LOUNGE_CLAIM,
                channel,
                field,
                "free lounge",
                "free lounge access is not supported by any approved grounded fact",
            )

        for match in _LOUNGE_COUNT_PATTERN.finditer(text):
            count = _normalize_number(match.group(1))
            qualifier = (match.group(2) or "plain").casefold()
            if count == "999":
                self._add(
                    violations,
                    ViolationCode.UNSUPPORTED_LOUNGE_CLAIM,
                    channel,
                    field,
                    match.group(0),
                    "999 is an undocumented sentinel and never authorizes a lounge entitlement",
                )
                continue
            expected = (
                context.domestic_lounge_visits
                if qualifier == "domestic"
                else context.international_lounge_visits
                if qualifier == "international"
                else context.domestic_lounge_visits or context.international_lounge_visits
            )
            if expected is None or count != str(expected):
                self._add(
                    violations,
                    ViolationCode.UNSUPPORTED_LOUNGE_CLAIM,
                    channel,
                    field,
                    match.group(0),
                    f"lounge entitlement {match.group(0)!r} is not present in the approved grounded facts",
                )

    def _check_insurance(
        self,
        channel: Channel,
        field: str,
        text: str,
        context: _GroundedContext,
        violations: list[Violation],
    ) -> None:
        if _INSURANCE_KEYWORDS.search(text) and not context.insurance_supported:
            self._add(
                violations,
                ViolationCode.UNSUPPORTED_INSURANCE_CLAIM,
                channel,
                field,
                text,
                "insurance/cover claim is not supported by any approved grounded fact",
            )

    def _check_eligibility(
        self,
        channel: Channel,
        field: str,
        text: str,
        violations: list[Violation],
    ) -> None:
        match = _ELIGIBILITY_KEYWORDS.search(text)
        if match:
            self._add(
                violations,
                ViolationCode.UNSUPPORTED_ELIGIBILITY_CLAIM,
                channel,
                field,
                match.group(0),
                "eligibility/approval claims are not approved for marketing content",
            )

    def _check_prohibited_absolute(
        self,
        channel: Channel,
        field: str,
        text: str,
        violations: list[Violation],
    ) -> None:
        match = _PROHIBITED_ABSOLUTE.search(text)
        if match:
            self._add(
                violations,
                ViolationCode.PROHIBITED_ABSOLUTE_CLAIM,
                channel,
                field,
                match.group(0),
                "absolute/guarantee wording is prohibited unless explicitly approved",
            )

    def _check_url(
        self,
        channel: Channel,
        field: str,
        text: str,
        violations: list[Violation],
    ) -> None:
        if _URL_PATTERN.search(text):
            self._add(
                violations,
                ViolationCode.UNAPPROVED_URL,
                channel,
                field,
                text,
                "no URL is approved by the grounding layer",
            )

    def _check_phone(
        self,
        channel: Channel,
        field: str,
        text: str,
        violations: list[Violation],
    ) -> None:
        match = _PHONE_MOBILE_PATTERN.search(text) or _PHONE_TOLLFREE_PATTERN.search(text)
        if match:
            self._add(
                violations,
                ViolationCode.UNAPPROVED_PHONE_NUMBER,
                channel,
                field,
                match.group(0),
                "no phone number is approved by the grounding layer",
            )

    def _check_deadline(
        self,
        channel: Channel,
        field: str,
        text: str,
        violations: list[Violation],
    ) -> None:
        match = _DEADLINE_KEYWORDS.search(text)
        if match:
            self._add(
                violations,
                ViolationCode.UNAPPROVED_DEADLINE,
                channel,
                field,
                match.group(0),
                "deadlines/urgency claims are not approved campaign context",
            )

    def _check_offer_code(
        self,
        channel: Channel,
        field: str,
        text: str,
        violations: list[Violation],
    ) -> None:
        match = _OFFER_CODE_PATTERN.search(text)
        if match:
            self._add(
                violations,
                ViolationCode.UNAPPROVED_OFFER_CODE,
                channel,
                field,
                match.group(0),
                "offer/promo codes are not approved campaign context",
            )

    def _check_identifiers(
        self,
        channel: Channel,
        field: str,
        text: str,
        violations: list[Violation],
    ) -> None:
        for identifier in self._prohibited_identifiers:
            if identifier in text:
                self._add(
                    violations,
                    ViolationCode.PII_LEAK,
                    channel,
                    field,
                    identifier,
                    "known internal identifier value leaked into customer-facing content",
                )
        match = _IDENTIFIER_PATTERN.search(text)
        if match:
            self._add(
                violations,
                ViolationCode.INTERNAL_IDENTIFIER_LEAK,
                channel,
                field,
                match.group(0),
                "internal identifier field leaked into customer-facing content",
            )

    # ------------------------------------------------------------------
    # Length validation
    # ------------------------------------------------------------------

    def _validate_length(
        self,
        channel: Channel,
        field: str,
        text: str,
        violations: list[Violation],
    ) -> None:
        maximum = _FIELD_LIMITS.get((channel, field))
        if maximum is not None and len(text) > maximum:
            self._add(
                violations,
                ViolationCode.CHANNEL_LENGTH_EXCEEDED,
                channel,
                field,
                text,
                f"exceeds the {maximum}-character limit for {channel.value}.{field}",
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _iter_text_fields(channel_content) -> Iterable[tuple[str, str]]:
        for field in (
            "title",
            "headline",
            "subject",
            "preheader",
            "body",
            "cta_label",
            "opening",
            "closing",
        ):
            value = getattr(channel_content, field, None)
            if isinstance(value, str):
                yield field, value
        talking_points = getattr(channel_content, "talking_points", None)
        if talking_points:
            for point in talking_points:
                yield "talking_points", point

    @staticmethod
    def _add(
        violations: list[Violation],
        code: ViolationCode,
        channel: Channel,
        field: str,
        claim: str,
        detail: str,
    ) -> None:
        violations.append(
            Violation(code=code, channel=channel, field=field, claim=claim, detail=detail)
        )

    @staticmethod
    def _dedupe(violations: list[Violation]) -> list[Violation]:
        seen: set[tuple] = set()
        unique: list[Violation] = []
        for violation in violations:
            key = (violation.code, violation.channel, violation.field, violation.claim)
            if key not in seen:
                seen.add(key)
                unique.append(violation)
        return unique


def _as_count(value: str) -> int | None:
    try:
        return int(value)
    except ValueError:
        return None


def _normalize_number(raw: str) -> str:
    """Normalize a numeric token for comparison ("2,500" -> "2500", keep decimals)."""
    cleaned = raw.replace(",", "")
    try:
        return str(int(cleaned))
    except ValueError:
        return cleaned


# Field limits keyed by (channel, field).
_FIELD_LIMITS: dict[tuple[Channel, str], int] = {
    (Channel.PUSH, "title"): PUSH_TITLE_MAX,
    (Channel.PUSH, "body"): PUSH_BODY_MAX,
    (Channel.SMS, "body"): SMS_BODY_MAX,
    (Channel.EMAIL, "subject"): EMAIL_SUBJECT_MAX,
    (Channel.EMAIL, "preheader"): EMAIL_PREHEADER_MAX,
    (Channel.EMAIL, "body"): EMAIL_BODY_MAX,
    (Channel.IN_APP, "headline"): IN_APP_HEADLINE_MAX,
    (Channel.IN_APP, "body"): IN_APP_BODY_MAX,
    (Channel.RELATIONSHIP_MANAGER, "opening"): RM_OPENING_MAX,
    (Channel.RELATIONSHIP_MANAGER, "talking_points"): RM_TALKING_POINT_MAX,
    (Channel.RELATIONSHIP_MANAGER, "closing"): RM_CLOSING_MAX,
    (Channel.PUSH, "cta_label"): CTA_LABEL_MAX,
    (Channel.EMAIL, "cta_label"): CTA_LABEL_MAX,
    (Channel.IN_APP, "cta_label"): CTA_LABEL_MAX,
}
