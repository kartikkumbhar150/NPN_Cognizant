"""Adversarial tests for the deterministic hallucination guard.

Each scenario injects an unsupported or prohibited claim and asserts the
corresponding controlled violation code.
"""

import pytest

from app.models.generation import GeneratedContent
from app.models.personalization import ProductFamily, ValidationStatus
from app.models.product import (
    GroundedFact,
    GroundedFactCategory,
    GroundedProductFacts,
    ProductStatus,
)
from app.models.validation import ViolationCode
from app.repositories.product_catalogue import CsvCreditCardCatalogueRepository
from app.services.hallucination_guard import HallucinationGuard
from app.services.product_grounding import ProductGroundingService


def grounded_cc014():
    return ProductGroundingService(CsvCreditCardCatalogueRepository()).ground(
        ProductFamily.CREDIT_CARD, "CC014"
    )


def grounded_with_sentinel_lounge() -> GroundedProductFacts:
    """A hand-built grounded product whose lounge fact is the 999 sentinel."""
    return GroundedProductFacts(
        product_id="CC014",
        product_family=ProductFamily.CREDIT_CARD,
        product_name="Regalia Gold",
        product_type="Super Premium",
        status=ProductStatus.ACTIVE,
        facts=[
            GroundedFact(
                fact_id="domestic_lounge_visits",
                value="999",
                category=GroundedFactCategory.TRAVEL,
            )
        ],
        product_tags=["AIRPORT_LOUNGE"],
        catalogue_version="sha256:test",
    )


def body_content(text: str, fact_refs: list[str] | None = None) -> GeneratedContent:
    return GeneratedContent(
        email={
            "subject": "Subject",
            "preheader": "preheader",
            "body": text,
            "cta_label": "Explore now",
            "fact_refs": fact_refs or [],
        }
    )


def assert_code(result, code: ViolationCode) -> None:
    assert result.status is ValidationStatus.FAILED
    assert code in {v.code for v in result.violations}, f"expected {code.value}, got {result.violations}"


def test_invented_annual_fee_fails():
    result = HallucinationGuard().validate(body_content("Annual fee of ₹999"), grounded_cc014())
    assert_code(result, ViolationCode.UNSUPPORTED_MONETARY_CLAIM)


def test_invented_percentage_cashback_fails():
    result = HallucinationGuard().validate(body_content("Get 5% cashback today"), grounded_cc014())
    assert_code(result, ViolationCode.UNSUPPORTED_REWARD_CLAIM)  # cashback unsupported
    assert_code(result, ViolationCode.UNSUPPORTED_PERCENTAGE_CLAIM)  # 5% not grounded


def test_invented_rate_fails():
    result = HallucinationGuard().validate(body_content("Enjoy an 8.5% interest rate"), grounded_cc014())
    assert_code(result, ViolationCode.UNSUPPORTED_RATE_CLAIM)


def test_invented_reward_multiplier_fails():
    result = HallucinationGuard().validate(body_content("Earn 10x reward points"), grounded_cc014())
    assert_code(result, ViolationCode.UNSUPPORTED_REWARD_CLAIM)


def test_unsupported_lounge_visits_fails():
    result = HallucinationGuard().validate(
        body_content("Enjoy 12 international lounge visits"), grounded_cc014()
    )
    assert_code(result, ViolationCode.UNSUPPORTED_LOUNGE_CLAIM)


def test_wrong_lounge_count_fails():
    result = HallucinationGuard().validate(body_content("Enjoy 8 lounge visits"), grounded_cc014())
    assert_code(result, ViolationCode.UNSUPPORTED_LOUNGE_CLAIM)


def test_unlimited_lounge_fails():
    result = HallucinationGuard().validate(body_content("Unlimited lounge access"), grounded_cc014())
    assert_code(result, ViolationCode.UNSUPPORTED_LOUNGE_CLAIM)


def test_free_lounge_fails():
    result = HallucinationGuard().validate(body_content("Free lounge access"), grounded_cc014())
    assert_code(result, ViolationCode.UNSUPPORTED_LOUNGE_CLAIM)


@pytest.mark.parametrize(
    "text",
    ["Unlimited lounge access", "999 lounge visits", "Enjoy 999 domestic lounge visits"],
)
def test_999_never_authorizes_lounge_entitlement(text):
    result = HallucinationGuard().validate(body_content(text), grounded_with_sentinel_lounge())
    assert_code(result, ViolationCode.UNSUPPORTED_LOUNGE_CLAIM)


def test_unsupported_insurance_fails():
    result = HallucinationGuard().validate(
        body_content("Complimentary travel insurance included"), grounded_cc014()
    )
    assert_code(result, ViolationCode.UNSUPPORTED_INSURANCE_CLAIM)


def test_guaranteed_approval_fails():
    result = HallucinationGuard().validate(body_content("Guaranteed approval on application"), grounded_cc014())
    assert_code(result, ViolationCode.UNSUPPORTED_ELIGIBILITY_CLAIM)


def test_preapproved_wording_fails():
    result = HallucinationGuard().validate(body_content("You are pre-approved for this card"), grounded_cc014())
    assert_code(result, ViolationCode.UNSUPPORTED_ELIGIBILITY_CLAIM)


def test_prohibited_absolute_claim_fails():
    result = HallucinationGuard().validate(body_content("This is the best card, risk-free"), grounded_cc014())
    assert_code(result, ViolationCode.PROHIBITED_ABSOLUTE_CLAIM)


def test_invented_url_fails():
    result = HallucinationGuard().validate(body_content("Apply now at https://example.com/apply"), grounded_cc014())
    assert_code(result, ViolationCode.UNAPPROVED_URL)


def test_invented_www_url_fails():
    result = HallucinationGuard().validate(body_content("Visit www.example.com for details"), grounded_cc014())
    assert_code(result, ViolationCode.UNAPPROVED_URL)


@pytest.mark.parametrize(
    "text", ["Call 9876543210 today", "Call +91 98765 43210", "Call 1800-180-1234"]
)
def test_invented_phone_number_fails(text):
    result = HallucinationGuard().validate(body_content(text), grounded_cc014())
    assert_code(result, ViolationCode.UNAPPROVED_PHONE_NUMBER)


def test_invented_deadline_fails():
    result = HallucinationGuard().validate(body_content("Offer ends 31 August, apply soon"), grounded_cc014())
    assert_code(result, ViolationCode.UNAPPROVED_DEADLINE)


def test_invented_validity_period_fails():
    result = HallucinationGuard().validate(body_content("Valid for 7 days only"), grounded_cc014())
    assert_code(result, ViolationCode.UNAPPROVED_DEADLINE)


def test_invented_offer_code_fails():
    result = HallucinationGuard().validate(body_content("Use code TRAVEL50 at checkout"), grounded_cc014())
    assert_code(result, ViolationCode.UNAPPROVED_OFFER_CODE)


def test_pii_identifier_leak_fails():
    g = HallucinationGuard(
        prohibited_identifiers=["CUST00274", "fixture-nbo-travel-001", "fixture-event-001"]
    )
    result = g.validate(body_content("Contact CUST00274 for support"), grounded_cc014())
    assert_code(result, ViolationCode.PII_LEAK)


def test_internal_identifier_field_leak_fails():
    result = HallucinationGuard().validate(body_content("Your customer_id is confidential"), grounded_cc014())
    assert_code(result, ViolationCode.INTERNAL_IDENTIFIER_LEAK)


def test_cust_id_structural_pattern_fails():
    result = HallucinationGuard().validate(body_content("Reference CUST12345 for your records"), grounded_cc014())
    assert_code(result, ViolationCode.INTERNAL_IDENTIFIER_LEAK)
