"""Provider-layer exceptions for Phase 6 LLM providers.

These are the only provider errors that may cross application boundaries.
Future real providers must map their SDK/transport exceptions onto this small
hierarchy instead of leaking SDK-specific exceptions.
"""


class LLMProviderError(Exception):
    """Generic provider failure (connection, transport, upstream error)."""

    code = "LLM_PROVIDER_ERROR"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class LLMProviderTimeoutError(LLMProviderError):
    """The provider call exceeded its allowed time."""

    code = "LLM_PROVIDER_TIMEOUT"


class LLMInvalidResponseError(LLMProviderError):
    """The provider returned output that is structurally invalid.

    Gross structural problems only (missing fields, bad channel shape, unknown
    fact references). Semantic claim validation belongs to DS-05.
    """

    code = "LLM_INVALID_RESPONSE"
