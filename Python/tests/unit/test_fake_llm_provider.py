"""Tests for the deterministic fake provider's canned responses and failure modes."""

import asyncio

import pytest

from app.llm import DeterministicFakeProvider, FakeProviderMode
from app.llm.errors import LLMInvalidResponseError, LLMProviderError, LLMProviderTimeoutError
from app.models.generation import GeneratedContent
from app.models.personalization import Channel
from app.models.prompt import PromptPackage

ALL_FIVE = list(Channel)


def make_package(
    channels: list[Channel] | None = None,
    fact_values: dict[str, str] | None = None,
    allowed_fact_ids: list[str] | None = None,
) -> PromptPackage:
    facts = fact_values or {
        "product_name": "Regalia Gold",
        "annual_fee": "2500",
        "domestic_lounge_visits": "12",
    }
    return PromptPackage(
        prompt_version="v1",
        system_prompt="system",
        user_prompt="user",
        requested_channels=channels if channels is not None else ALL_FIVE,
        allowed_fact_ids=allowed_fact_ids if allowed_fact_ids is not None else sorted(facts),
        language="en",
        fact_values=facts,
    )


def run(coro):
    return asyncio.run(coro)


def canned_push_email() -> dict:
    return {
        "push": {"title": "Canned title", "body": "Canned body", "fact_refs": ["product_name"]},
        "email": {
            "subject": "Canned subject",
            "preheader": "Canned preheader",
            "body": "Canned body",
            "cta_label": "Apply",
            "fact_refs": ["product_name"],
        },
    }


# --------------------------------------------------------------------------
# Canned responses
# --------------------------------------------------------------------------


def test_canned_valid_response_returned_predictably():
    package = make_package(channels=[Channel.PUSH, Channel.EMAIL])
    provider = DeterministicFakeProvider(response=canned_push_email())

    content = run(provider.generate(package))
    assert content.push is not None and content.push.title == "Canned title"
    assert content.email is not None and content.email.subject == "Canned subject"
    assert content.populated_channels() == [Channel.PUSH, Channel.EMAIL]

    again = run(provider.generate(package))
    assert content.model_dump(mode="json") == again.model_dump(mode="json")


def test_canned_typed_response_accepted():
    package = make_package(channels=[Channel.PUSH, Channel.EMAIL])
    provider = DeterministicFakeProvider(response=GeneratedContent.model_validate(canned_push_email()))
    content = run(provider.generate(package))
    assert content.push is not None


def test_canned_response_unknown_fact_ref_rejected():
    bad = canned_push_email()
    bad["push"]["fact_refs"] = ["invented_fact"]
    provider = DeterministicFakeProvider(response=bad)
    with pytest.raises(LLMInvalidResponseError) as excinfo:
        run(provider.generate(make_package(channels=[Channel.PUSH, Channel.EMAIL])))
    assert excinfo.value.code == "LLM_INVALID_RESPONSE"


def test_canned_response_unrequested_channel_rejected():
    provider = DeterministicFakeProvider(response=canned_push_email())
    # Only PUSH requested, but the canned response includes EMAIL.
    with pytest.raises(LLMInvalidResponseError) as excinfo:
        run(provider.generate(make_package(channels=[Channel.PUSH])))
    assert excinfo.value.code == "LLM_INVALID_RESPONSE"


def test_canned_response_missing_required_field_rejected():
    bad = canned_push_email()
    del bad["push"]["title"]  # structurally invalid push content
    provider = DeterministicFakeProvider(response=bad)
    with pytest.raises(LLMInvalidResponseError) as excinfo:
        run(provider.generate(make_package(channels=[Channel.PUSH, Channel.EMAIL])))
    assert excinfo.value.code == "LLM_INVALID_RESPONSE"


def test_canned_response_empty_channels_rejected():
    provider = DeterministicFakeProvider(response={})
    with pytest.raises(LLMInvalidResponseError):
        run(provider.generate(make_package()))


# --------------------------------------------------------------------------
# Failure simulation
# --------------------------------------------------------------------------


def test_provider_error_mode():
    provider = DeterministicFakeProvider(mode=FakeProviderMode.PROVIDER_ERROR)
    with pytest.raises(LLMProviderError) as excinfo:
        run(provider.generate(make_package()))
    assert excinfo.value.code == "LLM_PROVIDER_ERROR"


def test_timeout_mode():
    provider = DeterministicFakeProvider(mode=FakeProviderMode.TIMEOUT)
    with pytest.raises(LLMProviderTimeoutError) as excinfo:
        run(provider.generate(make_package()))
    assert excinfo.value.code == "LLM_PROVIDER_TIMEOUT"


def test_invalid_response_mode():
    provider = DeterministicFakeProvider(mode=FakeProviderMode.INVALID_RESPONSE)
    with pytest.raises(LLMInvalidResponseError) as excinfo:
        run(provider.generate(make_package()))
    assert excinfo.value.code == "LLM_INVALID_RESPONSE"


# --------------------------------------------------------------------------
# Deterministic content derivation (no hardcoded product)
# --------------------------------------------------------------------------


def test_generated_content_derives_facts_not_hardcoded():
    package = make_package(
        channels=[Channel.PUSH, Channel.EMAIL],
        fact_values={
            "product_name": "Travel Elite Card",
            "annual_fee": "1500",
            "domestic_lounge_visits": "8",
        },
    )
    content = run(DeterministicFakeProvider().generate(package))

    assert content.push.title == "Explore Travel Elite Card"
    assert content.email.subject == "Introducing Travel Elite Card"
    assert "Regalia Gold" not in content.model_dump(mode="json")


def test_relationship_manager_uses_approved_facts():
    facts = {
        "product_name": "Travel Elite Card",
        "annual_fee": "1500",
        "domestic_lounge_visits": "8",
    }
    package = make_package(channels=[Channel.RELATIONSHIP_MANAGER], fact_values=facts)
    content = run(DeterministicFakeProvider().generate(package))

    assert content.relationship_manager is not None
    assert "annual_fee: 1500" in content.relationship_manager.talking_points
    assert set(content.relationship_manager.fact_refs) == set(facts)


def test_no_network_or_api_key_required():
    """The fake provider is fully offline — no network config exists on it."""
    provider = DeterministicFakeProvider()
    assert not hasattr(provider, "api_key")
    assert not hasattr(provider, "base_url")
