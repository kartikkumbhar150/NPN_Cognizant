"""DS-04 composition test: request -> grounding -> prompt -> fake provider.

Verifies that the interfaces built through DS-04 compose correctly. This is
NOT the full Phase 6 vertical slice (no hallucination guard, no API endpoint,
no persistence).
"""

import asyncio

from app.llm import DeterministicFakeProvider
from app.models.personalization import Channel, PersonalizationRequest, ProductFamily
from app.repositories.product_catalogue import CsvCreditCardCatalogueRepository
from app.services.product_grounding import ProductGroundingService
from app.services.prompt_builder import PromptBuilder


def request_payload() -> dict:
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
            "requested_channels": ["PUSH", "SMS", "EMAIL", "IN_APP", "RELATIONSHIP_MANAGER"],
        },
        "consent_verified": True,
    }


def test_request_grounding_prompt_fake_compose():
    request = PersonalizationRequest.model_validate(request_payload())
    grounded = ProductGroundingService(CsvCreditCardCatalogueRepository()).ground(
        ProductFamily.CREDIT_CARD, "CC014"
    )
    prompt = PromptBuilder().build(request, grounded)
    content = asyncio.run(DeterministicFakeProvider().generate(prompt))

    # All five requested channels are produced, in canonical order.
    assert content.populated_channels() == list(Channel)

    # Content reflects the grounded product, and fact refs stay within bounds.
    assert content.push is not None
    assert "Regalia Gold" in content.push.title
    allowed = set(prompt.allowed_fact_ids)
    for channel in content.populated_channels():
        channel_content = getattr(content, channel.value.lower())
        assert set(channel_content.fact_refs) <= allowed

    # Privacy holds end to end: no customer identifiers anywhere in the chain.
    dump = (
        str(prompt.model_dump(mode="json"))
        + str(content.model_dump(mode="json"))
        + str(grounded.model_dump(mode="json"))
    )
    for secret in ("CUST00274", "fixture-nbo-travel-001", "fixture-event-001", "0.91"):
        assert secret not in dump
