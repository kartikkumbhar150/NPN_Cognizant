"""Domain errors for the RAG vector infrastructure.

Messages must stay diagnosable without ever embedding secrets (API keys,
credentials) or lower-level connection details.
"""


class RagError(Exception):
    """Base class for all RAG infrastructure errors."""


class RagConfigurationError(RagError):
    """Invalid configuration (e.g. unknown embedding provider name)."""


# ── Embedding errors ──────────────────────────────────────────────────────────


class EmbeddingError(RagError):
    """Base class for embedding generation failures."""


class EmbeddingInitializationError(EmbeddingError):
    """The embedding backend/model could not be initialized."""


class EmbeddingInputError(EmbeddingError):
    """Caller input is invalid (empty/blank text, empty document batch)."""


class EmbeddingGenerationError(EmbeddingError):
    """The provider failed while generating embeddings, or returned an
    unusable response (wrong row count, non-numeric values)."""


class EmbeddingDimensionError(EmbeddingError):
    """A produced vector does not match the provider's reported dimension."""

    def __init__(self, model_name: str, expected: int, actual: int) -> None:
        super().__init__(
            f"embedding model {model_name!r} produced a {actual}-dimension "
            f"vector but reports dimension {expected}"
        )
        self.model_name = model_name
        self.expected = expected
        self.actual = actual


# ── Vector store errors ───────────────────────────────────────────────────────


class VectorStoreError(RagError):
    """Base class for vector store failures."""


class VectorDimensionError(VectorStoreError):
    """A record's vector length differs from the collection dimension."""

    def __init__(self, point_id: object, expected: int, actual: int) -> None:
        super().__init__(
            f"vector for point {point_id!r} has {actual} dimensions; "
            f"collection expects {expected}"
        )
        self.point_id = point_id
        self.expected = expected
        self.actual = actual


class PointIdError(VectorStoreError):
    """A point ID is not in a Qdrant-supported form (unsigned int or UUID)."""


class CollectionConfigurationError(VectorStoreError):
    """An existing collection is incompatible with the requested configuration.

    Raised instead of any destructive action: the collection is left
    exactly as found and must be migrated explicitly by a human.
    """

    def __init__(self, collection_name: str, expected: str, actual: str) -> None:
        super().__init__(
            f"collection {collection_name!r} exists with incompatible "
            f"configuration: expected {expected}, found {actual}. "
            f"Refusing to alter or drop the existing collection — "
            f"migration must be performed explicitly."
        )
        self.collection_name = collection_name
        self.expected = expected
        self.actual = actual


# ── Retrieval errors ──────────────────────────────────────────────────────────


class RetrievalError(RagError):
    """Base class for semantic retrieval failures."""


class RetrievalValidationError(RetrievalError):
    """Caller input is invalid (blank/oversized query, bad limit/threshold)."""


class RetrievalUnavailableError(RetrievalError):
    """The knowledge collection is missing — retrieval cannot proceed.

    Deliberately NOT auto-created: a user query must never silently
    create infrastructure, and an absent collection almost certainly
    means ingestion has not run (or pointed at a different collection)."""

    def __init__(self, collection_name: str) -> None:
        super().__init__(
            f"knowledge collection {collection_name!r} does not exist — "
            f"run ingestion first; retrieval never creates collections"
        )
        self.collection_name = collection_name
