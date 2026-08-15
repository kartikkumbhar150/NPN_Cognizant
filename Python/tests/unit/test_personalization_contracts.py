"""Tests for the Phase 6 request/response contracts and the health endpoint.

Covers the DS-01 acceptance criteria: valid fixture request, rejection of
invalid propensity / empty lists / missing consent / invalid eligibility and
ownership / unsupported channels / unknown enums / extra fields, the output
contract shape, and ``GET /health``.
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.models.personalization import (
    ChannelContent,
    EmailContent,
    GenerationMetadata,
    GenerationResponse,
    InAppContent,
    PersonalizationRequest,
    PushContent,
    RelationshipManagerContent,
    SmsContent,
    ValidationInfo,
    ValidationStatus,
)

client = TestClient(app)


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------


def valid_request_payload() -> dict:
    """The canonical travel-card fixture request from the DS-01 spec."""
    return {
        "recommendation_id": "fixture-nbo-travel-001",
        "customer_id": "CUST00274",
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
                    "source_event_id": "fixture-event-001",
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
            "requested_channels": [
                "PUSH",
                "SMS",
                "EMAIL",
                "IN_APP",
                "RELATIONSHIP_MANAGER",
            ],
        },
        "consent_verified": True,
    }


def assert_rejected(payload: dict) -> None:
    """Assert that pydantic rejects the given payload."""
    with pytest.raises(ValidationError):
        PersonalizationRequest.model_validate(payload)


# --------------------------------------------------------------------------
# Request contract — valid input
# --------------------------------------------------------------------------


def test_valid_request_validates():
    request = PersonalizationRequest.model_validate(valid_request_payload())

    assert request.recommendation_id == "fixture-nbo-travel-001"
    assert request.customer_id == "CUST00274"
    assert request.recommended_product.product_family is request.recommended_product.product_family.CREDIT_CARD
    assert request.recommended_product.product_id == "CC014"
    assert request.decision_context.segment_code == "FREQUENT_TRAVELLER"
    assert len(request.decision_context.recent_events) == 1
    assert request.decision_context.recent_events[0].event_type == "FLIGHT_PURCHASE"
    assert request.decision_context.recent_events[0].source_event_id == "fixture-event-001"
    assert request.decision_context.propensity_score == 0.91
    assert request.decision_context.reason_codes == [
        "HIGH_TRAVEL_SPEND",
        "RECENT_FLIGHT_PURCHASE",
        "NO_CONFLICTING_TRAVEL_CARD",
        "PRODUCT_ELIGIBLE",
    ]
    assert request.decision_context.eligibility_status is request.decision_context.eligibility_status.ELIGIBLE
    assert request.decision_context.ownership_status is request.decision_context.ownership_status.NO_CONFLICT
    assert request.preferences.language == "en"
    assert len(request.preferences.requested_channels) == 5
    assert request.consent_verified is True


# --------------------------------------------------------------------------
# Request contract — propensity
# --------------------------------------------------------------------------


@pytest.mark.parametrize("propensity", [-0.01, 1.01])
def test_propensity_out_of_range_rejected(propensity):
    payload = valid_request_payload()
    payload["decision_context"]["propensity_score"] = propensity
    assert_rejected(payload)


def test_propensity_lower_bound_accepted():
    payload = valid_request_payload()
    payload["decision_context"]["propensity_score"] = 0.0
    assert PersonalizationRequest.model_validate(payload).decision_context.propensity_score == 0.0


def test_propensity_upper_bound_accepted():
    payload = valid_request_payload()
    payload["decision_context"]["propensity_score"] = 1.0
    assert PersonalizationRequest.model_validate(payload).decision_context.propensity_score == 1.0


# --------------------------------------------------------------------------
# Request contract — empty lists
# --------------------------------------------------------------------------


def test_empty_recent_events_rejected():
    payload = valid_request_payload()
    payload["decision_context"]["recent_events"] = []
    assert_rejected(payload)


def test_empty_reason_codes_rejected():
    payload = valid_request_payload()
    payload["decision_context"]["reason_codes"] = []
    assert_rejected(payload)


# --------------------------------------------------------------------------
# Request contract — consent, eligibility, ownership
# --------------------------------------------------------------------------


def test_consent_false_rejected():
    payload = valid_request_payload()
    payload["consent_verified"] = False
    assert_rejected(payload)


@pytest.mark.parametrize("status", ["NOT_ELIGIBLE", "PENDING", "REJECTED"])
def test_invalid_eligibility_rejected(status):
    payload = valid_request_payload()
    payload["decision_context"]["eligibility_status"] = status
    assert_rejected(payload)


@pytest.mark.parametrize("status", ["CONFLICT", "OWNED", "UNKNOWN"])
def test_invalid_ownership_rejected(status):
    payload = valid_request_payload()
    payload["decision_context"]["ownership_status"] = status
    assert_rejected(payload)


# --------------------------------------------------------------------------
# Request contract — channels and enums
# --------------------------------------------------------------------------


def test_unsupported_channel_rejected():
    payload = valid_request_payload()
    payload["preferences"]["requested_channels"] = ["PUSH", "WHATSAPP"]
    assert_rejected(payload)


def test_unknown_product_family_rejected():
    payload = valid_request_payload()
    payload["recommended_product"]["product_family"] = "LOAN"
    assert_rejected(payload)


def test_unknown_enum_style_value_rejected():
    """Any value outside the closed enum sets must fail."""
    payload = valid_request_payload()
    payload["preferences"]["requested_channels"] = ["push"]
    assert_rejected(payload)


# --------------------------------------------------------------------------
# Request contract — extra fields
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "path",
    [
        [],  # top level
        ["recommended_product"],
        ["decision_context"],
        ["decision_context", "recent_events", 0],
        ["preferences"],
    ],
)
def test_extra_fields_rejected(path):
    payload = valid_request_payload()
    node = payload
    for key in path:
        node = node[key]
    node["unexpected_field"] = "surprise"
    assert_rejected(payload)


# --------------------------------------------------------------------------
# Output contract (response)
# --------------------------------------------------------------------------


def test_generation_response_contract_round_trips():
    now = datetime.now(timezone.utc)
    response = GenerationResponse(
        generation_id=uuid4(),
        recommendation_id="fixture-nbo-travel-001",
        product_id="CC014",
        content=ChannelContent(
            push=PushContent(title="Title", body="Body"),
            sms=SmsContent(body="Body"),
            email=EmailContent(
                subject="Subject",
                preheader="Preheader",
                body="Body",
                cta_label="Apply now",
            ),
            in_app=InAppContent(headline="Headline", body="Body", cta_label="Apply now"),
            relationship_manager=RelationshipManagerContent(
                opening="Opening",
                talking_points=["Point one"],
                closing="Closing",
            ),
        ),
        metadata=GenerationMetadata(
            provider="none",  # no provider wired in DS-01
            model="none",
            prompt_version="v1",
            catalogue_version="1.0.0",
            generated_at=now,
            language="en",
        ),
        validation=ValidationInfo(
            status=ValidationStatus.PASSED,
            validated_at=now,
        ),
    )

    data = response.model_dump(mode="json")
    assert data["generation_id"]
    assert data["recommendation_id"] == "fixture-nbo-travel-001"
    assert data["product_id"] == "CC014"
    assert data["content"]["push"] == {"title": "Title", "body": "Body", "fact_refs": []}
    assert data["content"]["sms"] == {"body": "Body", "fact_refs": []}
    assert data["content"]["email"]["subject"] == "Subject"
    assert data["content"]["in_app"]["headline"] == "Headline"
    assert data["content"]["relationship_manager"]["talking_points"] == ["Point one"]
    assert data["metadata"]["prompt_version"] == "v1"
    assert data["metadata"]["catalogue_version"] == "1.0.0"
    assert data["validation"] == {
        "status": "PASSED",
        "validated_at": data["validation"]["validated_at"],
        "violations": [],
    }


# --------------------------------------------------------------------------
# Health endpoint
# --------------------------------------------------------------------------


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "genai-personalization"}
