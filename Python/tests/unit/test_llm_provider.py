"""Tests for the provider-neutral LLM provider contract and the fake provider."""

import asyncio
import inspect

from app.llm import DeterministicFakeProvider, LLMProvider
from app.models.personalization import Channel
from app.models.prompt import PromptPackage

ALL_FIVE = list(Channel)  # PUSH, SMS, EMAIL, IN_APP, RELATIONSHIP_MANAGER


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


# --------------------------------------------------------------------------
# Protocol conformance
# --------------------------------------------------------------------------


def test_fake_provider_conforms_to_provider_contract():
    provider = DeterministicFakeProvider()
    assert isinstance(provider, LLMProvider)
    assert provider.provider == "fake"
    assert provider.model == "deterministic-v1"
    assert inspect.iscoroutinefunction(provider.generate)


def test_provider_interface_receives_only_prompt_package():
    """The provider API takes exactly the safe PromptPackage — no customer input."""
    params = list(inspect.signature(DeterministicFakeProvider.generate).parameters)
    assert params == ["self", "prompt"]
    annotation = inspect.signature(DeterministicFakeProvider.generate).parameters["prompt"].annotation
    # ``from __future__ import annotations`` makes this a string at runtime.
    assert annotation in (PromptPackage, "PromptPackage")


# --------------------------------------------------------------------------
# Determinism
# --------------------------------------------------------------------------


def test_same_prompt_same_output_repeated_calls():
    provider = DeterministicFakeProvider()
    package = make_package()

    first = run(provider.generate(package))
    second = run(provider.generate(package))

    assert first.model_dump(mode="json") == second.model_dump(mode="json")


def test_same_prompt_same_output_across_instances():
    package = make_package()
    first = run(DeterministicFakeProvider().generate(package))
    second = run(DeterministicFakeProvider().generate(package))
    assert first.model_dump(mode="json") == second.model_dump(mode="json")


# --------------------------------------------------------------------------
# Requested channels
# --------------------------------------------------------------------------


def test_only_requested_channels_are_generated():
    package = make_package(channels=[Channel.PUSH, Channel.EMAIL])
    content = run(DeterministicFakeProvider().generate(package))

    assert content.populated_channels() == [Channel.PUSH, Channel.EMAIL]
    assert content.push is not None
    assert content.email is not None
    assert content.sms is None
    assert content.in_app is None
    assert content.relationship_manager is None


def test_all_five_channels_are_generated():
    content = run(DeterministicFakeProvider().generate(make_package()))
    assert content.populated_channels() == ALL_FIVE


# --------------------------------------------------------------------------
# Fact references
# --------------------------------------------------------------------------


def test_fact_refs_stay_within_allowed_fact_ids():
    allowed = ["product_name", "annual_fee", "domestic_lounge_visits"]
    package = make_package(allowed_fact_ids=allowed)
    content = run(DeterministicFakeProvider().generate(package))

    for channel in content.populated_channels():
        channel_content = getattr(content, channel.value.lower())
        assert set(channel_content.fact_refs) <= set(allowed)


# --------------------------------------------------------------------------
# Privacy boundary
# --------------------------------------------------------------------------


def test_no_customer_identifiers_cross_the_boundary():
    package = make_package()
    content = run(DeterministicFakeProvider().generate(package))

    dump = str(package.model_dump(mode="json")) + str(content.model_dump(mode="json"))
    for secret in ("CUST00274", "fixture-nbo-travel-001", "fixture-event-001", "0.91"):
        assert secret not in dump


# --------------------------------------------------------------------------
# Metadata
# --------------------------------------------------------------------------


def test_provider_metadata_identifiers():
    provider = DeterministicFakeProvider()
    assert provider.provider == "fake"
    assert provider.model == "deterministic-v1"
