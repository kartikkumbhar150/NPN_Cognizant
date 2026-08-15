"""Typed models for the rendered prompt package (Phase 6 prompt builder).

The ``PromptPackage`` is the only object produced by the prompt builder. It
deliberately contains no customer identifiers, no propensity, and no raw
request data — only the rendered prompts plus safe metadata needed by later
validation (prompt version, requested channels, allowed fact IDs, language).
"""

from app.models.personalization import Channel, StrictModel


class PromptPackage(StrictModel):
    """The rendered, validated prompt bundle ready for a future LLM call."""

    prompt_version: str  # e.g. "v1" — immutable per version directory
    system_prompt: str
    user_prompt: str
    requested_channels: list[Channel]
    allowed_fact_ids: list[str]
    language: str
