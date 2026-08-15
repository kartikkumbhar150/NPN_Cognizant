"""Tests for the DS-03 safe prompt builder."""

import json
import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.models.personalization import Channel, PersonalizationRequest, ProductFamily
from app.models.product import (
    GroundedFact,
    GroundedFactCategory,
    GroundedProductFacts,
    ProductStatus,
)
from app.repositories.product_catalogue import CsvCreditCardCatalogueRepository
from app.services.product_grounding import ProductGroundingService
from app.services.prompt_builder import (
    PROMPT_VERSION,
    PromptBuilder,
    PromptContextError,
    PromptTemplateNotFoundError,
)
from app.models.prompt import PromptPackage

# Fixture values that must NEVER appear in a rendered prompt.
FIXTURE_CUSTOMER_ID = "CUST00274"
FIXTURE_RECOMMENDATION_ID = "fixture-nbo-travel-001"
FIXTURE_EVENT_SOURCE_ID = "fixture-event-001"
FIXTURE_PROPENSITY = "0.91"

_ALL_CHANNELS = ["PUSH", "SMS", "EMAIL", "IN_APP", "RELATIONSHIP_MANAGER"]


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------


def request_payload() -> dict:
    """The canonical travel-card fixture request from DS-01."""
    return {
        "recommendation_id": FIXTURE_RECOMMENDATION_ID,
        "customer_id": FIXTURE_CUSTOMER_ID,
        "recommended_product": {
            "product_family": "CREDIT_CARD",
            "product_id": "CC014",
        },
        "decision_context": {
            "segment_code": "FREQUENT_TRAVELLER",
            "recent_events": [
                {
                    "event_type": "FLIGHT_PURCHASE",
                    "occurred_at": "2026-08-12T06:34:14+05:30",
                    "source_event_id": FIXTURE_EVENT_SOURCE_ID,
                }
            ],
            "propensity_score": 0.91,
            "reason_codes": [
                "HIGH_TRAVEL_SPEND",
                "RECENT_FLIGHT_PURCHASE",
                "NO_CONFLICTING_TRAVEL_CARD",
                "PRODUCT_ELIGIBLE",
            ],
            "eligibility_status": "ELIGIBLE",
            "ownership_status": "NO_CONFLICT",
        },
        "preferences": {
            "language": "en",
            "requested_channels": list(_ALL_CHANNELS),
        },
        "consent_verified": True,
    }


def make_request(mutate: dict | None = None) -> PersonalizationRequest:
    payload = request_payload()
    if mutate:
        node = payload
        for key in mutate["path"][:-1]:
            node = node[key]
        node[mutate["path"][-1]] = mutate["value"]
    return PersonalizationRequest.model_validate(payload)


def grounded_cc014() -> GroundedProductFacts:
    """Ground the real CC014 row through the real repository + service."""
    service = ProductGroundingService(CsvCreditCardCatalogueRepository())
    from app.models.personalization import ProductFamily

    return service.ground(ProductFamily.CREDIT_CARD, "CC014")


def grounded_with_tags_only() -> GroundedProductFacts:
    """A grounded product with a tag but no numeric lounge fact."""
    return GroundedProductFacts(
        product_id="CC014",
        product_family=ProductFamily.CREDIT_CARD,
        product_name="Regalia Gold",
        product_type="Super Premium",
        status=ProductStatus.ACTIVE,
        approved_description=None,
        facts=[
            GroundedFact(fact_id="product_name", value="Regalia Gold", category=GroundedFactCategory.IDENTITY),
        ],
        product_tags=["AIRPORT_LOUNGE", "TRAVEL"],
        catalogue_version="sha256:test",
    )


def build(request: PersonalizationRequest | None = None, grounded: GroundedProductFacts | None = None) -> PromptPackage:
    builder = PromptBuilder()
    return builder.build(
        request or make_request(),
        grounded or grounded_cc014(),
    )


def rendered_text(package: PromptPackage) -> str:
    return package.system_prompt + "\n" + package.user_prompt


# --------------------------------------------------------------------------
# Safe request -> prompt
# --------------------------------------------------------------------------


def test_safe_request_builds_prompt_package():
    package = build()

    assert package.prompt_version == "v1"
    assert package.language == "en"
    assert package.system_prompt.strip()
    assert package.user_prompt.strip()
    assert package.requested_channels == [
        Channel.PUSH,
        Channel.SMS,
        Channel.EMAIL,
        Channel.IN_APP,
        Channel.RELATIONSHIP_MANAGER,
    ]
    for fact_id in ("product_name", "annual_fee", "domestic_lounge_visits"):
        assert fact_id in package.allowed_fact_ids


# --------------------------------------------------------------------------
# Privacy: identifiers and propensity never enter the prompt
# --------------------------------------------------------------------------


def test_identifier_exclusion():
    package = build()
    text = rendered_text(package)
    dump = json.dumps(package.model_dump(mode="json"))

    for secret in (
        FIXTURE_CUSTOMER_ID,
        FIXTURE_RECOMMENDATION_ID,
        FIXTURE_EVENT_SOURCE_ID,
    ):
        assert secret not in text, f"identifier leaked into prompt: {secret}"
        assert secret not in dump, f"identifier leaked into package: {secret}"

    # Raw field names must not appear either (request is never serialized).
    for raw_name in ("customer_id", "recommendation_id", "source_event_id"):
        assert raw_name not in text


def test_propensity_exclusion():
    package = build()
    text = rendered_text(package)

    assert FIXTURE_PROPENSITY not in text
    assert "91%" not in text
    # The propensity *value* must be excluded; the word may appear only in the
    # system safety instruction ("Never calculate ... propensity scores").


# --------------------------------------------------------------------------
# Grounded facts only
# --------------------------------------------------------------------------


def test_every_prompt_fact_is_grounded():
    package = build()
    allowed = set(package.allowed_fact_ids)
    fact_tokens = set(re.findall(r"\[([a-z_]+)\]", package.user_prompt))

    assert fact_tokens
    assert fact_tokens <= allowed, f"non-grounded fact ids in prompt: {fact_tokens - allowed}"


def test_omitted_fact_remains_omitted():
    # Real CC014 does not ground international lounge visits (contradictory data).
    package = build()
    text = rendered_text(package)

    assert "international_lounge_visits" not in text
    assert "international_lounge_visits" not in package.allowed_fact_ids


def test_tags_are_not_converted_to_numeric_claims():
    package = build(grounded=grounded_with_tags_only())
    text = package.user_prompt

    assert "AIRPORT_LOUNGE" in text
    assert "Never convert a tag into a specific numeric claim" in text
    # No numeric lounge entitlement may be derived from the tag alone.
    assert "domestic_lounge_visits" not in text
    assert "12 lounge" not in text.lower()


# --------------------------------------------------------------------------
# Channels
# --------------------------------------------------------------------------


def test_channel_filtering():
    request = make_request({"path": ["preferences", "requested_channels"], "value": ["PUSH", "EMAIL"]})
    package = build(request=request)

    assert package.requested_channels == [Channel.PUSH, Channel.EMAIL]
    assert "[PUSH]" in package.user_prompt
    assert "[EMAIL]" in package.user_prompt
    for excluded in ("[SMS]", "[IN_APP]", "[RELATIONSHIP_MANAGER]"):
        assert excluded not in package.user_prompt


def test_channel_order_is_deterministic():
    request = make_request(
        {"path": ["preferences", "requested_channels"], "value": ["EMAIL", "PUSH", "SMS"]}
    )
    package_a = build(request=request)
    package_b = build(request=make_request({"path": ["preferences", "requested_channels"], "value": ["SMS", "PUSH", "EMAIL"]}))

    # Same requested set -> same canonical order regardless of input order.
    assert package_a.requested_channels == package_b.requested_channels == [Channel.PUSH, Channel.SMS, Channel.EMAIL]


def test_full_build_is_deterministic():
    package_a = build()
    package_b = build()

    assert package_a.system_prompt == package_b.system_prompt
    assert package_a.user_prompt == package_b.user_prompt
    assert package_a.allowed_fact_ids == package_b.allowed_fact_ids


# --------------------------------------------------------------------------
# Controlled mappings
# --------------------------------------------------------------------------


def test_controlled_mappings_applied():
    package = build()
    text = package.user_prompt

    assert "frequent traveller" in text
    assert "recent flight purchase" in text
    # Persuasion subset only: business/safety reason codes are excluded.
    assert "no conflicting travel card identified" not in text
    assert "product eligibility was confirmed upstream" not in text
    # Raw codes never reach the prompt.
    for raw in ("FREQUENT_TRAVELLER", "FLIGHT_PURCHASE", "HIGH_TRAVEL_SPEND", "RECENT_FLIGHT_PURCHASE"):
        assert raw not in text


def test_unknown_reason_code_fails_safely():
    request = make_request(
        {"path": ["decision_context", "reason_codes"], "value": ["HIGH_TRAVEL_SPEND", "MYSTERY_CODE"]}
    )
    with pytest.raises(PromptContextError) as excinfo:
        build(request=request)
    assert excinfo.value.code == "PROMPT_CONTEXT_INVALID"


def test_unknown_event_type_fails_safely():
    request = make_request(
        {"path": ["decision_context", "recent_events", 0, "event_type"], "value": "MYSTERY_EVENT"}
    )
    with pytest.raises(PromptContextError) as excinfo:
        build(request=request)
    assert excinfo.value.code == "PROMPT_CONTEXT_INVALID"


def test_unknown_segment_fails_safely():
    request = make_request({"path": ["decision_context", "segment_code"], "value": "MYSTERY_SEGMENT"})
    with pytest.raises(PromptContextError) as excinfo:
        build(request=request)
    assert excinfo.value.code == "PROMPT_CONTEXT_INVALID"


def test_unsupported_language_fails_safely():
    request = make_request({"path": ["preferences", "language"], "value": "hi"})
    with pytest.raises(PromptContextError) as excinfo:
        build(request=request)
    assert excinfo.value.code == "PROMPT_CONTEXT_INVALID"


def test_empty_channels_fails_safely():
    request = make_request({"path": ["preferences", "requested_channels"], "value": []})
    with pytest.raises(PromptContextError) as excinfo:
        build(request=request)
    assert excinfo.value.code == "PROMPT_CONTEXT_INVALID"


# --------------------------------------------------------------------------
# Template loading robustness
# --------------------------------------------------------------------------


def test_missing_template_clean_domain_error(tmp_path):
    builder = PromptBuilder(prompts_root=tmp_path)  # no templates present
    with pytest.raises(PromptTemplateNotFoundError) as excinfo:
        builder.build(make_request(), grounded_cc014())
    assert excinfo.value.code == "PROMPT_TEMPLATE_NOT_FOUND"


def test_cwd_independence(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    package = build()
    assert package.prompt_version == PROMPT_VERSION
    assert package.user_prompt.strip()


# --------------------------------------------------------------------------
# Golden test — lock down stable v1 sections and safety boundaries
# --------------------------------------------------------------------------


def test_v1_golden_sections():
    package = build()
    system = package.system_prompt
    user = package.user_prompt

    # System prompt: role + safety rules.
    for expected in (
        "banking marketing copy generator",
        "already been selected and approved",
        "Never invent",
        "fact_refs",
        "copy generator only",
    ):
        assert expected in system, f"missing system section: {expected!r}"

    # User prompt: stable sections.
    for expected in (
        "TASK",
        "CUSTOMER CONTEXT (controlled, non-identifying)",
        "- behavioral segment: frequent traveller",
        "APPROVED PRODUCT FACTS",
        "- [product_name] Regalia Gold",
        "- [annual_fee] 2500",
        "OUTPUT REQUIREMENTS BY CHANNEL",
        "[PUSH]",
        "[SMS]",
        "[EMAIL]",
        "[IN_APP]",
        "[RELATIONSHIP_MANAGER]",
        "FACT REFERENCES",
        "Allowed fact IDs:",
        "Do not invent new fact IDs",
    ):
        assert expected in user, f"missing user section: {expected!r}"

    # Immutable version marker.
    assert package.prompt_version == "v1"


# --------------------------------------------------------------------------
# Request contract still strict
# --------------------------------------------------------------------------


def test_request_contract_unchanged():
    """DS-01 strictness must still reject invalid requests."""
    payload = request_payload()
    payload["consent_verified"] = False
    with pytest.raises(ValidationError):
        PersonalizationRequest.model_validate(payload)
