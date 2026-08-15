"""DS-05 integration safety tests.

Full chain: PersonalizationRequest -> grounding -> PromptBuilder -> fake
provider -> HallucinationGuard. No API endpoint, no regeneration, no
persistence.
"""

import asyncio

from app.llm import DeterministicFakeProvider
from app.models.personalization import Channel, PersonalizationRequest, ProductFamily, ValidationStatus
from app.models.validation import ViolationCode
from app.repositories.product_catalogue import CsvCreditCardCatalogueRepository
from app.services.hallucination_guard import HallucinationGuard
from app.services.product_grounding import ProductGroundingService
from app.services.prompt_builder import PromptBuilder


def request_payload(channels: list[str] | None = None) -> dict:
    return {
        "recommendation_id": "fixture-nbo-travel-001",
        "customer_id": "CUST00274",
        "recommended_product": {"product_family": "CREDIT_CARD", "product_id": "CC014"},
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
            "requested_channels": channels or ["PUSH", "SMS", "EMAIL", "IN_APP", "RELATIONSHIP_MANAGER"],
        },
        "consent_verified": True,
    }


def pipeline(channels: list[str] | None = None, provider: DeterministicFakeProvider | None = None):
    request = PersonalizationRequest.model_validate(request_payload(channels))
    grounded = ProductGroundingService(CsvCreditCardCatalogueRepository()).ground(
        ProductFamily.CREDIT_CARD, "CC014"
    )
    prompt = PromptBuilder().build(request, grounded)
    content = asyncio.run((provider or DeterministicFakeProvider()).generate(prompt))
    return grounded, prompt, content


def test_safe_pipeline_passes_guard():
    grounded, _, content = pipeline()
    guard = HallucinationGuard(
        known_product_names=["Millennia Card", "Diners Black", "Infinia", "Travel Elite Card"],
        prohibited_identifiers=["CUST00274", "fixture-nbo-travel-001", "fixture-event-001"],
    )
    result = guard.validate(content, grounded)
    assert result.status is ValidationStatus.PASSED, result.violations


def test_canned_unsupported_claim_fails_guard():
    canned = {
        "push": {"title": "Regalia Gold", "body": "Annual fee of ₹999 only", "fact_refs": ["product_name"]},
        "email": {
            "subject": "Regalia Gold",
            "preheader": "preheader",
            "body": "Annual fee of ₹999 only",
            "cta_label": "Explore now",
            "fact_refs": ["product_name"],
        },
    }
    provider = DeterministicFakeProvider(response=canned)
    grounded, _, content = pipeline(channels=["PUSH", "EMAIL"], provider=provider)

    result = HallucinationGuard().validate(content, grounded)
    assert result.status is ValidationStatus.FAILED
    codes = {v.code for v in result.violations}
    assert ViolationCode.UNSUPPORTED_MONETARY_CLAIM in codes
