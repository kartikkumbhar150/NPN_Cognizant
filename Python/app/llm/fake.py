"""Deterministic fake LLM provider for offline, reproducible development.

Purpose: unit/integration tests, CI, offline development, and repeatable
demonstrations before a real provider is integrated. It performs no network
I/O, requires no API key, and never uses randomness — the same
``PromptPackage`` always yields the same ``GeneratedContent``.

The fake is intentionally NOT business logic: it never selects products,
interprets transactions, calculates propensity/eligibility, determines
ownership, or infers missing product benefits. It only simulates
``safe prompt -> structured generated content`` using fact values already
approved by grounding (``PromptPackage.fact_values``).
"""

from __future__ import annotations

from enum import Enum
from typing import Mapping

from pydantic import ValidationError

from app.llm.errors import LLMInvalidResponseError, LLMProviderError, LLMProviderTimeoutError
from app.models.generation import GeneratedContent
from app.models.personalization import Channel
from app.models.prompt import PromptPackage


class FakeProviderMode(str, Enum):
    """Deterministic failure modes the fake provider can simulate."""

    SUCCESS = "SUCCESS"
    INVALID_RESPONSE = "INVALID_RESPONSE"
    TIMEOUT = "TIMEOUT"
    PROVIDER_ERROR = "PROVIDER_ERROR"


def _product_label(fact_values: Mapping[str, str]) -> str:
    return fact_values.get("product_name", "your card")


def _fact_refs(fact_values: Mapping[str, str], *fact_ids: str) -> list[str]:
    return [fact_id for fact_id in fact_ids if fact_id in fact_values]


class DeterministicFakeProvider:
    """Deterministic, offline, provider-neutral fake for Phase 6."""

    provider = "fake"
    model = "deterministic-v1"

    def __init__(
        self,
        *,
        response: GeneratedContent | Mapping | None = None,
        mode: FakeProviderMode = FakeProviderMode.SUCCESS,
    ) -> None:
        """``response`` injects a canned structured result; ``mode`` simulates failure."""
        self._response = response
        self._mode = mode

    async def generate(self, prompt: PromptPackage) -> GeneratedContent:
        if self._mode is FakeProviderMode.TIMEOUT:
            raise LLMProviderTimeoutError("fake provider simulated timeout")
        if self._mode is FakeProviderMode.PROVIDER_ERROR:
            raise LLMProviderError("fake provider simulated upstream error")
        if self._mode is FakeProviderMode.INVALID_RESPONSE:
            raise LLMInvalidResponseError("fake provider simulated malformed output")

        content = (
            self._normalize(self._response)
            if self._response is not None
            else self._generate_from_facts(prompt)
        )
        self._validate_against_prompt(content, prompt)
        return content

    # ------------------------------------------------------------------
    # Canned responses
    # ------------------------------------------------------------------

    def _normalize(self, response: GeneratedContent | Mapping) -> GeneratedContent:
        if isinstance(response, GeneratedContent):
            return response
        try:
            return GeneratedContent.model_validate(dict(response))
        except ValidationError as exc:
            raise LLMInvalidResponseError(f"provider returned structurally invalid content: {exc}") from exc

    # ------------------------------------------------------------------
    # Deterministic generation
    # ------------------------------------------------------------------

    def _generate_from_facts(self, prompt: PromptPackage) -> GeneratedContent:
        facts = prompt.fact_values
        label = _product_label(facts)
        product_name_refs = _fact_refs(facts, "product_name")

        content: dict[str, object] = {}

        if Channel.PUSH in prompt.requested_channels:
            content["push"] = {
                "title": f"Explore {label}",
                "body": f"Discover benefits available with {label}.",
                "fact_refs": product_name_refs,
            }
        if Channel.SMS in prompt.requested_channels:
            content["sms"] = {
                "body": f"Explore benefits available with {label}.",
                "fact_refs": product_name_refs,
            }
        if Channel.EMAIL in prompt.requested_channels:
            content["email"] = {
                "subject": f"Introducing {label}",
                "preheader": f"Benefits worth exploring with {label}.",
                "body": "Learn about the benefits available with this card.",
                "cta_label": "Explore now",
                "fact_refs": product_name_refs,
            }
        if Channel.IN_APP in prompt.requested_channels:
            content["in_app"] = {
                "headline": f"Discover {label}",
                "body": "Explore the benefits available with this card.",
                "cta_label": "Explore now",
                "fact_refs": product_name_refs,
            }
        if Channel.RELATIONSHIP_MANAGER in prompt.requested_channels:
            # A few approved facts as talking points; only facts that exist.
            talking_points = [f"{fact_id}: {value}" for fact_id, value in facts.items()]
            content["relationship_manager"] = {
                "opening": f"I wanted to share some details about {label}.",
                "talking_points": talking_points,
                "closing": "Let me know if you would like more details.",
                "fact_refs": sorted(facts),
            }

        return GeneratedContent.model_validate(content)

    # ------------------------------------------------------------------
    # Boundary validation (structural only — semantic checks are DS-05)
    # ------------------------------------------------------------------

    def _validate_against_prompt(self, content: GeneratedContent, prompt: PromptPackage) -> None:
        requested = set(prompt.requested_channels)
        populated = set(content.populated_channels())
        unexpected = populated - requested
        if unexpected:
            raise LLMInvalidResponseError(
                f"provider returned content for unrequested channels: "
                f"{sorted(channel.value for channel in unexpected)}"
            )

        allowed = set(prompt.allowed_fact_ids)
        for channel in content.populated_channels():
            channel_content = getattr(content, channel.value.lower())
            if channel_content is None:
                continue
            unknown = [ref for ref in channel_content.fact_refs if ref not in allowed]
            if unknown:
                raise LLMInvalidResponseError(
                    f"provider referenced unknown fact ids for {channel.value}: {sorted(unknown)}"
                )
