"""Phase 6 LLM provider boundary.

Provider-neutral: application code depends on ``LLMProvider``, never on a
specific vendor. DS-04 ships the contract plus a deterministic fake provider;
no real provider is implemented yet.
"""

from app.llm.base import LLMProvider
from app.llm.errors import (
    LLMInvalidResponseError,
    LLMProviderError,
    LLMProviderTimeoutError,
)
from app.llm.fake import DeterministicFakeProvider, FakeProviderMode

__all__ = [
    "DeterministicFakeProvider",
    "FakeProviderMode",
    "LLMInvalidResponseError",
    "LLMProvider",
    "LLMProviderError",
    "LLMProviderTimeoutError",
]
