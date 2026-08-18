"""Semantic knowledge retriever.

Read-side pipeline::

    validated query
        ↓
    EmbeddingProvider.embed_query()
        ↓
    QdrantVectorStore.search()          (COSINE, server-side payload filters)
        ↓
    threshold → dedup → optional per-source cap → trim to limit
        ↓
    RetrievalResult(items=[RetrievedChunk...], warnings=[...])

This module retrieves *evidence* — it never generates answers, never calls
a generative LLM, never classifies intent, and never touches the NBO
engines.  An empty result is a legitimate, explicit outcome ("no
verifiable evidence"), never a fallback.

Privacy: query text may contain personal information, so it is never
logged, echoed, or stored — ``RetrievalResult`` deliberately omits it,
and diagnostics carry only metadata (counts, source IDs, reasons).
"""

import numbers
from typing import List, Mapping, Optional

from chatbot.app.rag.embeddings import EmbeddingProvider
from chatbot.app.rag.errors import (
    RetrievalUnavailableError,
    RetrievalValidationError,
    VectorDimensionError,
)
from chatbot.app.rag.models import RetrievedChunk, RetrievalResult, ScoredRecord
from chatbot.app.rag.qdrant_store import QdrantVectorStore

MAX_QUERY_CHARS = 500
DEFAULT_TOP_K = 5
MAX_TOP_K = 20

# Over-fetch factor: dedup/per-source capping can drop hits.
_OVERFETCH_FACTOR = 2
_MAX_FETCH_LIMIT = 2 * MAX_TOP_K

# Payload fields that must be present (non-empty) for a hit to count as evidence.
_CRITICAL_FIELDS = (
    "chunk_id", "source_id", "content", "title", "source_url", "entity", "category"
)

# Retriever-side allowlist mirroring QdrantVectorStore.SEARCH_FILTER_FIELDS.
_FILTER_FIELDS = frozenset({"category", "entity", "product_id", "source_id", "subcategory"})


class KnowledgeRetriever:
    """Retrieves grounded HDFC knowledge evidence from the vector store.

    Dependencies are injected (provider + store); the collection to
    search is the one the store was configured with — callers cannot
    direct a query at an arbitrary collection.
    """

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: QdrantVectorStore,
        score_threshold: Optional[float] = None,
        max_chunks_per_source: Optional[int] = None,
    ) -> None:
        if max_chunks_per_source is not None and max_chunks_per_source < 1:
            raise RetrievalValidationError(
                f"max_chunks_per_source must be >= 1, got {max_chunks_per_source!r}"
            )
        if score_threshold is not None and not _valid_threshold(score_threshold):
            raise RetrievalValidationError(
                f"score_threshold must be a number in [-1, 1] (cosine similarity), "
                f"got {score_threshold!r}"
            )
        self._provider = embedding_provider
        self._store = vector_store
        self._score_threshold = score_threshold
        self._max_chunks_per_source = max_chunks_per_source

    # ── Public API ────────────────────────────────────────────────────────────

    def search(
        self,
        query: str,
        *,
        limit: int = DEFAULT_TOP_K,
        score_threshold: Optional[float] = None,
        category: Optional[str] = None,
        entity: Optional[str] = None,
        product_id: Optional[str] = None,
        source_id: Optional[str] = None,
        subcategory: Optional[str] = None,
    ) -> RetrievalResult:
        """Semantic search over the knowledge collection."""
        cleaned_query = self._validate_query(query)
        self._validate_limit(limit)
        threshold = (
            score_threshold
            if score_threshold is not None
            else self._score_threshold
        )
        if threshold is not None and not _valid_threshold(threshold):
            raise RetrievalValidationError(
                f"score_threshold must be a number in [-1, 1], got {threshold!r}"
            )

        filters = self._build_filters(
            category=category, entity=entity, product_id=product_id,
            source_id=source_id, subcategory=subcategory,
        )

        if not self._store.collection_exists():
            raise RetrievalUnavailableError(self._store.collection_name)

        query_vector = self._provider.embed_query(cleaned_query)
        if len(query_vector) != self._store.dimension:
            raise VectorDimensionError("<query>", self._store.dimension, len(query_vector))

        warnings: List[str] = []
        records = self._store.search(
            query_vector,
            limit=min(max(limit * _OVERFETCH_FACTOR, limit), _MAX_FETCH_LIMIT),
            score_threshold=threshold,
            filters=filters,
        )

        chunks: List[RetrievedChunk] = []
        for record in records:
            chunk = self._to_chunk(record, warnings)
            if chunk is not None:
                chunks.append(chunk)

        chunks = self._deduplicate(chunks, warnings)
        chunks = self._cap_per_source(chunks, warnings)
        return RetrievalResult(items=chunks[:limit], warnings=warnings)

    # ── Validation ────────────────────────────────────────────────────────────

    @staticmethod
    def _validate_query(query: str) -> str:
        if not isinstance(query, str):
            raise RetrievalValidationError(f"query must be a string, got {type(query).__name__}")
        cleaned = query.strip()
        if not cleaned:
            raise RetrievalValidationError("query must not be empty or whitespace-only")
        if len(cleaned) > MAX_QUERY_CHARS:
            raise RetrievalValidationError(
                f"query must be at most {MAX_QUERY_CHARS} characters, got {len(cleaned)}"
            )
        return cleaned

    @staticmethod
    def _validate_limit(limit: int) -> None:
        if not isinstance(limit, int) or isinstance(limit, bool):
            raise RetrievalValidationError(f"limit must be an integer, got {limit!r}")
        if limit < 1:
            raise RetrievalValidationError(f"limit must be >= 1, got {limit!r}")
        if limit > MAX_TOP_K:
            raise RetrievalValidationError(f"limit must be <= {MAX_TOP_K}, got {limit!r}")

    # ── Filter construction ──────────────────────────────────────────────────

    @staticmethod
    def _build_filters(
        *,
        category: Optional[str],
        entity: Optional[str],
        product_id: Optional[str],
        source_id: Optional[str],
        subcategory: Optional[str],
    ) -> Optional[Mapping[str, str]]:
        filters: dict = {}
        for name, value in (
            ("category", category), ("entity", entity),
            ("product_id", product_id), ("source_id", source_id),
            ("subcategory", subcategory),
        ):
            if value is None:
                continue
            if not isinstance(value, str) or not value.strip():
                raise RetrievalValidationError(f"filter {name!r} must be a non-empty string")
            filters[name] = value.strip()
        return filters or None

    # ── Result shaping ────────────────────────────────────────────────────────

    @staticmethod
    def _to_chunk(record: ScoredRecord, warnings: List[str]) -> Optional[RetrievedChunk]:
        """Map one raw hit to a ``RetrievedChunk``; skip malformed points."""
        payload = record.payload or {}
        missing = [f for f in _CRITICAL_FIELDS if not _payload_str(payload, f)]
        if missing:
            warnings.append(
                f"skipped point {record.id!r}: missing critical fields {missing}"
            )
            return None
        if isinstance(record.score, bool) or not isinstance(record.score, numbers.Real):
            warnings.append(f"skipped point {record.id!r}: non-numeric score {record.score!r}")
            return None
        return RetrievedChunk(
            point_id=record.id,
            chunk_id=payload["chunk_id"],
            source_id=payload["source_id"],
            content=payload["content"],
            title=payload["title"],
            section=_payload_str(payload, "section"),
            entity=payload["entity"],
            category=payload["category"],
            subcategory=_payload_str(payload, "subcategory"),
            source_url=payload["source_url"],
            source_type=_payload_str(payload, "source_type"),
            retrieved_at=_payload_str(payload, "retrieved_at"),
            product_id=_payload_str(payload, "product_id"),
            product_name=_payload_str(payload, "product_name"),
            effective_date=_payload_str(payload, "effective_date"),
            score=float(record.score),
            content_hash=_payload_str(payload, "content_hash") or "",
        )

    @staticmethod
    def _deduplicate(chunks: List[RetrievedChunk], warnings: List[str]) -> List[RetrievedChunk]:
        """Drop exact-content duplicates (same ``content_hash``), keeping
        the highest-scoring copy."""
        seen: set = set()
        deduped: List[RetrievedChunk] = []
        for chunk in chunks:
            if not chunk.content_hash:
                deduped.append(chunk)
                continue
            if chunk.content_hash in seen:
                warnings.append(
                    f"deduplicated repeated content_hash {chunk.content_hash[:16]}… "
                    f"(kept highest-scoring copy, source {chunk.source_id!r})"
                )
                continue
            seen.add(chunk.content_hash)
            deduped.append(chunk)
        return deduped

    def _cap_per_source(self, chunks: List[RetrievedChunk], warnings: List[str]) -> List[RetrievedChunk]:
        """Optionally cap chunks per source_id (source-diversity knob)."""
        if self._max_chunks_per_source is None:
            return chunks
        per_source: dict = {}
        kept: List[RetrievedChunk] = []
        for chunk in chunks:
            used = per_source.get(chunk.source_id, 0)
            if used >= self._max_chunks_per_source:
                continue
            per_source[chunk.source_id] = used + 1
            kept.append(chunk)
        dropped = len(chunks) - len(kept)
        if dropped:
            warnings.append(f"dropped {dropped} chunk(s) over the per-source cap")
        return kept


def _payload_str(payload: Mapping, field: str) -> Optional[str]:
    value = payload.get(field)
    if isinstance(value, str) and value.strip():
        return value
    return None


def _valid_threshold(value) -> bool:
    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        return False
    return -1.0 <= float(value) <= 1.0
