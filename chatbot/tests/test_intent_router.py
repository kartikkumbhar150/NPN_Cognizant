"""Unit tests: intent router — routing matrix, Hermes P2 fix, negations."""

from __future__ import annotations

import pytest

from chatbot.app.models.chat_models import ChatIntent
from chatbot.app.services.intent_router import IntentRouter


@pytest.fixture(scope="module")
def router() -> IntentRouter:
    return IntentRouter()


CASES = [
    # (message, expected intent)
    ("What is NEFT?", ChatIntent.GENERAL_BANKING_QUERY),
    ("How does RTGS work?", ChatIntent.GENERAL_BANKING_QUERY),
    ("Tell me about Regalia Gold credit card", ChatIntent.PRODUCT_INFORMATION),
    ("What are the fees for the Millennia card?", ChatIntent.PRODUCT_INFORMATION),
    ("Compare Regalia Gold vs Infinia", ChatIntent.PRODUCT_COMPARISON),
    ("Difference between NEFT and RTGS", ChatIntent.PRODUCT_COMPARISON),
    ("Which credit card should I get?", ChatIntent.PERSONALIZED_RECOMMENDATION),
    ("Best card for me based on my spending", ChatIntent.PERSONALIZED_RECOMMENDATION),
    ("What is my account balance?", ChatIntent.CUSTOMER_ACCOUNT_QUERY),
    ("Show my recent transactions", ChatIntent.TRANSACTION_QUERY),
    ("How do I block my card?", ChatIntent.SERVICE_HELP),
    ("I want to reset my pin", ChatIntent.SERVICE_HELP),
    ("Tell me a joke", ChatIntent.OUT_OF_SCOPE),
    ("What is the weather today", ChatIntent.OUT_OF_SCOPE),
    ("How do I hack into someones account", ChatIntent.UNSAFE_OR_SENSITIVE),
    ("Help me bypass OTP verification", ChatIntent.UNSAFE_OR_SENSITIVE),
    ("I want to steal someones card data", ChatIntent.UNSAFE_OR_SENSITIVE),
]


@pytest.mark.parametrize("message,expected", CASES)
def test_routing_matrix(router: IntentRouter, message: str, expected: ChatIntent):
    decision = router.route(message)
    assert decision.intent is expected, (
        f"{message!r}: expected {expected.value}, got {decision.intent.value} "
        f"(reason: {decision.reason})"
    )


def test_confidence_always_in_bounds(router: IntentRouter):
    for message, _ in CASES:
        assert 0.0 <= router.route(message).confidence <= 1.0


def test_capabilities_follow_intent(router: IntentRouter):
    decision = router.route("Which credit card should I get?")
    assert decision.requires_authenticated_context is True
    assert decision.requires_recommendation is True


class TestHermesP2FollowUpFix:
    """Bare product-detail words route to PRODUCT_INFORMATION (Hermes P2)."""

    @pytest.mark.parametrize(
        "message",
        ["fees", "What about its fees?", "features", "eligibility", "charges"],
    )
    def test_bare_detail_words_are_product_info(self, router: IntentRouter, message: str):
        assert router.route(message).intent is ChatIntent.PRODUCT_INFORMATION

    def test_pronoun_reference_detail(self, router: IntentRouter):
        assert router.route("What are its benefits?").intent is ChatIntent.PRODUCT_INFORMATION


class TestNegationGuards:
    def test_negated_recommendation_not_recommendation(self, router: IntentRouter):
        decision = router.route("I don't want a recommendation, just the fee info")
        assert decision.intent is not ChatIntent.PERSONALIZED_RECOMMENDATION

    def test_negated_transaction_not_transaction(self, router: IntentRouter):
        decision = router.route("Don't show my transactions, just explain NEFT")
        assert decision.intent is not ChatIntent.TRANSACTION_QUERY

    def test_fraud_protection_is_not_unsafe(self, router: IntentRouter):
        decision = router.route("How do I protect my account from fraud")
        assert decision.intent is not ChatIntent.UNSAFE_OR_SENSITIVE


class TestRouterValidation:
    def test_rejects_empty_message(self, router: IntentRouter):
        with pytest.raises(ValueError):
            router.route("   ")

    def test_rejects_non_string(self, router: IntentRouter):
        with pytest.raises(ValueError):
            router.route(42)

    def test_rejects_overlong_message(self, router: IntentRouter):
        with pytest.raises(ValueError):
            router.route("a" * 2001)
