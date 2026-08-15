"""Basic and positive tests for the deterministic hallucination guard."""

from app.models.generation import GeneratedContent
from app.models.personalization import Channel, ProductFamily, ValidationStatus
from app.models.validation import ViolationCode
from app.repositories.product_catalogue import CsvCreditCardCatalogueRepository
from app.services.hallucination_guard import (
    EMAIL_SUBJECT_MAX,
    PUSH_BODY_MAX,
    PUSH_TITLE_MAX,
    SMS_BODY_MAX,
    HallucinationGuard,
)
from app.services.product_grounding import ProductGroundingService


def grounded_cc014():
    return ProductGroundingService(CsvCreditCardCatalogueRepository()).ground(
        ProductFamily.CREDIT_CARD, "CC014"
    )


def guard(**kwargs) -> HallucinationGuard:
    return HallucinationGuard(**kwargs)


def push_content(title: str, body: str, fact_refs: list[str] | None = None) -> GeneratedContent:
    return GeneratedContent(
        push={"title": title, "body": body, "fact_refs": fact_refs or []}
    )


def email_content(subject: str, body: str, fact_refs: list[str] | None = None) -> GeneratedContent:
    return GeneratedContent(
        email={
            "subject": subject,
            "preheader": "preheader",
            "body": body,
            "cta_label": "Explore now",
            "fact_refs": fact_refs or [],
        }
    )


# --------------------------------------------------------------------------
# Safe content
# --------------------------------------------------------------------------


def test_safe_grounded_content_passes():
    result = guard().validate(push_content("Explore Regalia Gold", "Discover benefits available with Regalia Gold."), grounded_cc014())
    assert result.status is ValidationStatus.PASSED
    assert result.violations == []


def test_valid_currency_formatting_variation_passes():
    grounded = grounded_cc014()
    for body in ("Annual fee of ₹2,500", "Annual fee of ₹2500"):
        result = guard().validate(email_content("Fee", body, fact_refs=["annual_fee"]), grounded)
        assert result.status is ValidationStatus.PASSED, body


def test_valid_percentage_passes():
    # dining_discount=10 is grounded; "10% dining discount" is supported.
    result = guard().validate(email_content("Dining", "Enjoy 10% dining discount", fact_refs=["dining_discount"]), grounded_cc014())
    assert result.status is ValidationStatus.PASSED


def test_generic_reward_mention_passes():
    result = guard().validate(push_content("Rewards", "Explore the card's approved rewards benefits."), grounded_cc014())
    assert result.status is ValidationStatus.PASSED


def test_valid_subset_of_channels_passes():
    result = guard().validate(
        GeneratedContent(sms={"body": "Explore benefits available with Regalia Gold.", "fact_refs": ["product_name"]}),
        grounded_cc014(),
    )
    assert result.status is ValidationStatus.PASSED


# --------------------------------------------------------------------------
# Fact references
# --------------------------------------------------------------------------


def test_unknown_fact_ref_fails():
    result = guard().validate(push_content("Title", "Body", fact_refs=["made_up_fact"]), grounded_cc014())
    assert result.status is ValidationStatus.FAILED
    codes = {v.code for v in result.violations}
    assert ViolationCode.UNKNOWN_FACT_REFERENCE in codes


# --------------------------------------------------------------------------
# Product identity
# --------------------------------------------------------------------------


def test_wrong_product_name_fails():
    g = guard(known_product_names=["Millennia Card", "Diners Black", "Infinia"])
    result = g.validate(push_content("Wrong", "Explore Millennia Card today"), grounded_cc014())
    assert result.status is ValidationStatus.FAILED
    codes = {v.code for v in result.violations}
    assert ViolationCode.UNSUPPORTED_PRODUCT_NAME in codes


def test_correct_product_name_with_known_set_passes():
    g = guard(known_product_names=["Millennia Card", "Diners Black", "Regalia Gold"])
    result = g.validate(push_content("Explore Regalia Gold", "Discover benefits available with Regalia Gold."), grounded_cc014())
    assert result.status is ValidationStatus.PASSED


# --------------------------------------------------------------------------
# Channel lengths
# --------------------------------------------------------------------------


def test_push_title_length_limit_enforced():
    grounded = grounded_cc014()
    result = guard().validate(push_content("X" * (PUSH_TITLE_MAX + 1), "body"), grounded)
    assert result.status is ValidationStatus.FAILED
    assert any(v.code is ViolationCode.CHANNEL_LENGTH_EXCEEDED and v.field == "title" for v in result.violations)
    # Exactly at the limit passes.
    assert guard().validate(push_content("X" * PUSH_TITLE_MAX, "body"), grounded).status is ValidationStatus.PASSED


def test_push_body_length_limit_enforced():
    result = guard().validate(push_content("title", "X" * (PUSH_BODY_MAX + 1)), grounded_cc014())
    assert result.status is ValidationStatus.FAILED
    assert any(v.field == "body" for v in result.violations)


def test_sms_body_length_limit_enforced():
    content = GeneratedContent(sms={"body": "X" * (SMS_BODY_MAX + 1), "fact_refs": []})
    result = guard().validate(content, grounded_cc014())
    assert result.status is ValidationStatus.FAILED
    assert any(v.channel is Channel.SMS and v.field == "body" for v in result.violations)


def test_email_subject_length_limit_enforced():
    content = email_content("X" * (EMAIL_SUBJECT_MAX + 1), "body")
    result = guard().validate(content, grounded_cc014())
    assert result.status is ValidationStatus.FAILED
    assert any(v.field == "subject" for v in result.violations)


def test_length_limits_are_central_constants():
    assert PUSH_TITLE_MAX == 60
    assert PUSH_BODY_MAX == 160
    assert SMS_BODY_MAX == 160


# --------------------------------------------------------------------------
# Multiple violations
# --------------------------------------------------------------------------


def test_multiple_violations_are_reported():
    content = email_content("Fee", "Annual fee of ₹999 and guaranteed approval", fact_refs=["annual_fee"])
    result = guard().validate(content, grounded_cc014())
    assert result.status is ValidationStatus.FAILED
    codes = {v.code for v in result.violations}
    assert ViolationCode.UNSUPPORTED_MONETARY_CLAIM in codes
    assert ViolationCode.UNSUPPORTED_ELIGIBILITY_CLAIM in codes
    assert len(result.violations) >= 2


# --------------------------------------------------------------------------
# Determinism
# --------------------------------------------------------------------------


def test_validation_is_deterministic():
    content = email_content("Fee", "Annual fee of ₹999", fact_refs=["annual_fee"])
    grounded = grounded_cc014()
    first = guard().validate(content, grounded)
    second = guard().validate(content, grounded)
    assert first.model_dump(mode="json") == second.model_dump(mode="json")
