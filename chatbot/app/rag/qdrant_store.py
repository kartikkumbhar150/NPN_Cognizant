"""Qdrant vector store.

Low-level vector persistence: collection lifecycle, upsert, retrieve-by-ID,
delete, count, and nearest-neighbour ``search``.  Policy/orchestration
(query validation, deduplication, per-source capping, provenance mapping)
lives in ``retriever``, not here.

The store receives vectors — never text — and its collection dimension
comes from the caller (derived from the embedding provider), never a
hardcoded constant.  Qdrant SDK models are confined to this module; the
rest of the codebase uses ``VectorRecord``.

This collection is for PUBLIC/curated bank knowledge only; customer or
private banking data must never be stored here.
"""

from pathlib import Path
from typing import List, Mapping, Optional, Sequence

from qdrant_client import QdrantClient
from qdrant_client import models as qmodels

from chatbot.app.rag.errors import (
    CollectionConfigurationError,
    VectorDimensionError,
    VectorStoreError,
)
from chatbot.app.rag.models import ScoredRecord, VectorRecord, validate_point_id

# chatbot/app/rag/qdrant_store.py → chatbot/app/rag → chatbot/app → chatbot
_CHATBOT_DIR = Path(__file__).resolve().parents[2]

# Payload fields usable as exact-match search filters. Callers may only
# filter on these names — the mapping from caller-facing filter keys to
# payload keys is fixed here, so filter input can never inject arbitrary
# payload field names, operators, or raw filter JSON.
SEARCH_FILTER_FIELDS = frozenset(
    {"category", "entity", "product_id", "source_id", "subcategory"}
)


class QdrantVectorStore:
    """Thin, provider-neutral wrapper over a Qdrant client.

    ``client`` is injected so tests can pass ``QdrantClient(":memory:")``
    and the application can pass a local-path or remote client built by
    ``create_qdrant_client``.
    """

    def __init__(
        self,
        client: QdrantClient,
        collection_name: str,
        dimension: int,
        distance: qmodels.Distance = qmodels.Distance.COSINE,
    ) -> None:
        if not collection_name or not collection_name.strip():
            raise VectorStoreError("collection_name must be a non-empty string")
        if not isinstance(dimension, int) or isinstance(dimension, bool) or dimension < 1:
            raise VectorStoreError(f"dimension must be a positive integer, got {dimension!r}")
        self._client = client
        self._collection_name = collection_name
        self._dimension = dimension
        self._distance = distance

    # ── Collection lifecycle ──────────────────────────────────────────────────

    def collection_exists(self) -> bool:
        return self._client.collection_exists(self._collection_name)

    def ensure_collection(self) -> str:
        """Create the collection if absent; verify compatibility if present.

        Returns ``"created"`` or ``"exists"``.  An existing collection
        with a different vector dimension or distance metric raises
        ``CollectionConfigurationError`` WITHOUT altering the collection.

        Also ensures keyword payload indexes for every allowlisted
        filter field: Qdrant Cloud rejects payload-filter operations
        (delete-by-source, filtered search) with HTTP 400 when no index
        exists, while local embedded mode tolerates index-less scans —
        creating them unconditionally keeps both modes working.  Index
        creation is idempotent on both.
        """
        if not self.collection_exists():
            self._client.create_collection(
                collection_name=self._collection_name,
                vectors_config=qmodels.VectorParams(
                    size=self._dimension,
                    distance=self._distance,
                ),
            )
            outcome = "created"
        else:
            info = self._client.get_collection(self._collection_name)
            vectors = info.config.params.vectors
            if not isinstance(vectors, qmodels.VectorParams):
                raise CollectionConfigurationError(
                    self._collection_name,
                    expected=f"single unnamed vector (dim={self._dimension}, "
                    f"distance={self._distance.value})",
                    actual="named/multi vector configuration",
                )
            if vectors.size != self._dimension or vectors.distance != self._distance:
                raise CollectionConfigurationError(
                    self._collection_name,
                    expected=f"dim={self._dimension}, distance={self._distance.value}",
                    actual=f"dim={vectors.size}, distance={vectors.distance.value}",
                )
            outcome = "exists"

        self._ensure_filter_indexes()
        return outcome

    def _ensure_filter_indexes(self) -> None:
        """Create keyword payload indexes for the allowlisted filter fields.

        The local-mode SDK emits a harmless ``UserWarning`` ("no effect
        in the local Qdrant") which is suppressed here: the indexes exist
        for managed-cloud compatibility, and local mode simply ignores
        them.
        """
        import warnings

        for field in sorted(SEARCH_FILTER_FIELDS):
            try:
                with warnings.catch_warnings():
                    warnings.filterwarnings(
                        "ignore", message=".*[Pp]ayload indexes have no effect.*"
                    )
                    self._client.create_payload_index(
                        collection_name=self._collection_name,
                        field_name=field,
                        field_schema=qmodels.PayloadSchemaType.KEYWORD,
                    )
            except Exception as exc:
                raise VectorStoreError(
                    f"payload index creation failed for {field!r}: "
                    f"{type(exc).__name__}"
                ) from exc

    # ── Point operations ────────────────────────────────────────────────────

    def upsert(self, records: Sequence[VectorRecord]) -> int:
        """Upsert records; returns the number written.  Empty input is a
        documented no-op returning 0 (never a client call)."""
        if not records:
            return 0
        points = []
        for record in records:
            if not isinstance(record, VectorRecord):
                raise VectorStoreError(f"expected VectorRecord, got {type(record).__name__}")
            if len(record.vector) != self._dimension:
                raise VectorDimensionError(record.id, self._dimension, len(record.vector))
            points.append(
                qmodels.PointStruct(
                    id=record.id,
                    vector=[float(v) for v in record.vector],
                    payload=dict(record.payload),
                )
            )
        try:
            self._client.upsert(
                collection_name=self._collection_name,
                points=points,
                wait=True,
            )
        except Exception as exc:
            raise VectorStoreError(
                f"Qdrant upsert failed for {len(points)} points: {type(exc).__name__}"
            ) from exc
        return len(points)

    def get(self, point_id) -> Optional[VectorRecord]:
        """Fetch one record by ID; ``None`` when the ID is unknown."""
        canonical = validate_point_id(point_id)
        try:
            results = self._client.retrieve(
                collection_name=self._collection_name,
                ids=[canonical],
                with_payload=True,
                with_vectors=True,
            )
        except Exception as exc:
            raise VectorStoreError(
                f"Qdrant retrieve failed: {type(exc).__name__}"
            ) from exc
        if not results:
            return None
        point = results[0]
        return VectorRecord(
            id=point.id,
            vector=[float(v) for v in point.vector],
            payload=dict(point.payload or {}),
        )

    def delete(self, point_ids: Sequence) -> int:
        """Delete explicit IDs; returns the number requested to delete."""
        if not point_ids:
            return 0
        canonical_ids = [validate_point_id(pid) for pid in point_ids]
        try:
            self._client.delete(
                collection_name=self._collection_name,
                points_selector=qmodels.PointIdsList(points=canonical_ids),
                wait=True,
            )
        except Exception as exc:
            raise VectorStoreError(
                f"Qdrant delete failed: {type(exc).__name__}"
            ) from exc
        return len(canonical_ids)

    def delete_by_payload(self, field: str, value) -> None:
        """Delete every point whose payload ``field`` equals ``value``."""
        if not field or not field.strip():
            raise VectorStoreError("delete_by_payload requires a non-empty field name")
        if value is None or (isinstance(value, str) and not value.strip()):
            raise VectorStoreError("delete_by_payload requires a non-empty value")
        try:
            self._client.delete(
                collection_name=self._collection_name,
                points_selector=qmodels.FilterSelector(
                    filter=qmodels.Filter(
                        must=[
                            qmodels.FieldCondition(
                                key=field,
                                match=qmodels.MatchValue(value=value),
                            )
                        ]
                    )
                ),
                wait=True,
            )
        except Exception as exc:
            raise VectorStoreError(
                f"Qdrant delete-by-payload ({field}) failed: {type(exc).__name__}"
            ) from exc

    def count(self) -> int:
        try:
            return int(self._client.count(self._collection_name, exact=True).count)
        except Exception as exc:
            raise VectorStoreError(
                f"Qdrant count failed: {type(exc).__name__}"
            ) from exc

    # ── Semantic search ─────────────────────────────────────────────────────

    def search(
        self,
        vector: Sequence[float],
        *,
        limit: int,
        score_threshold: Optional[float] = None,
        filters: Optional[Mapping[str, str]] = None,
    ) -> List[ScoredRecord]:
        """Nearest-neighbour search, returning neutral ``ScoredRecord``s.

        With COSINE collections the score Qdrant returns is the cosine
        *similarity* in [-1, 1] — higher is better; ``score_threshold``
        compares against that same scale and is applied Qdrant-side,
        as are ``filters`` (exact payload matches — never post-filtering
        in Python).  Filter keys are validated against
        ``SEARCH_FILTER_FIELDS`` so callers cannot reach arbitrary
        payload fields.
        """
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
            raise VectorStoreError(f"limit must be a positive integer, got {limit!r}")
        if not isinstance(vector, (list, tuple)) or not vector:
            raise VectorStoreError("search vector must be a non-empty sequence of numbers")
        if len(vector) != self._dimension:
            raise VectorDimensionError("<query>", self._dimension, len(vector))
        query_vector = [float(v) for v in vector]
        if score_threshold is not None:
            if (
                isinstance(score_threshold, bool)
                or not isinstance(score_threshold, (int, float))
                or not -1.0 <= float(score_threshold) <= 1.0
            ):
                raise VectorStoreError(
                    f"score_threshold must be a float in [-1, 1] for COSINE "
                    f"similarity, got {score_threshold!r}"
                )
            score_threshold = float(score_threshold)

        query_filter = self._build_filter(filters)

        try:
            response = self._client.query_points(
                collection_name=self._collection_name,
                query=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=query_filter,
                with_payload=True,
            )
        except Exception as exc:
            raise VectorStoreError(
                f"Qdrant search failed: {type(exc).__name__}"
            ) from exc
        return [
            ScoredRecord(
                id=point.id,
                score=float(point.score),
                payload=dict(point.payload or {}),
            )
            for point in response.points
        ]

    @staticmethod
    def _build_filter(filters: Optional[Mapping[str, str]]) -> Optional[qmodels.Filter]:
        """Translate an allowlisted field→value mapping into a Qdrant Filter."""
        if not filters:
            return None
        conditions = []
        for key, value in filters.items():
            if key not in SEARCH_FILTER_FIELDS:
                raise VectorStoreError(
                    f"filter field {key!r} is not searchable; allowed: "
                    f"{sorted(SEARCH_FILTER_FIELDS)}"
                )
            if value is None or (isinstance(value, str) and not value.strip()):
                raise VectorStoreError(f"filter value for {key!r} must be a non-empty string")
            conditions.append(
                qmodels.FieldCondition(key=key, match=qmodels.MatchValue(value=value))
            )
        return qmodels.Filter(must=conditions)

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def collection_name(self) -> str:
        return self._collection_name


# ── Factories ─────────────────────────────────────────────────────────────────


def create_qdrant_client(settings) -> QdrantClient:
    """Build a Qdrant client from chatbot settings.

    Remote mode when ``QDRANT_URL`` is set (API key passed only — never
    logged).  Otherwise local embedded mode under ``QDRANT_LOCAL_PATH``
    (relative paths anchored to the ``chatbot/`` directory).
    """
    url = (getattr(settings, "qdrant_url", "") or "").strip()
    if url:
        try:
            return QdrantClient(url=url, api_key=settings.qdrant_api_key or None)
        except Exception as exc:
            raise VectorStoreError(
                f"Unable to initialize Qdrant client for the configured "
                f"QDRANT_URL: {type(exc).__name__}"
            ) from exc
    raw_path = (getattr(settings, "qdrant_local_path", ".qdrant") or "").strip()
    if raw_path == ":memory:":
        return QdrantClient(":memory:")
    path = Path(raw_path)
    if not path.is_absolute():
        path = _CHATBOT_DIR / path
    try:
        return QdrantClient(path=str(path))
    except Exception as exc:
        raise VectorStoreError(
            f"Unable to initialize local Qdrant storage at {path}: "
            f"{type(exc).__name__}"
        ) from exc


def create_vector_store(settings, embedding_provider) -> QdrantVectorStore:
    """Compose client + collection name + provider-derived dimension."""
    return QdrantVectorStore(
        client=create_qdrant_client(settings),
        collection_name=settings.qdrant_collection,
        dimension=embedding_provider.dimension,
    )
