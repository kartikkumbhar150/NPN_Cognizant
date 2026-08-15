"""Provider-neutral LLM provider contract for Phase 6.

Future code must depend on ``LLMProvider``, never on a specific vendor
(DeepSeek, OpenAI, Anthropic, NVIDIA, OpenRouter, Gemini...). This keeps
product-grounding, prompting, validation, and campaign logic independent of
the runtime model choice.

The provider receives only the already-safe :class:`PromptPackage` from
DS-03 — never customer objects, raw catalogue rows, transactions, or
upstream request data.

Async is used because real providers will ultimately perform network I/O.
"""

from typing import Protocol, runtime_checkable

from app.models.generation import GeneratedContent
from app.models.prompt import PromptPackage


@runtime_checkable
class LLMProvider(Protocol):
    """Contract every Phase 6 LLM provider implementation must satisfy."""

    provider: str
    model: str

    async def generate(self, prompt: PromptPackage) -> GeneratedContent:
        """Generate structured marketing content for the given safe prompt."""
        ...
