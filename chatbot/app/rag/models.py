"""Provider-neutral models for vectors and knowledge documents.

``VectorRecord`` is the application-facing unit of storage; the rest of
the codebase never imports Qdrant SDK classes.  ``KnowledgeDocument``
and ``KnowledgeChunk`` model the ingestion pipeline: a curated source
becomes a document, deterministic chunking splits it into chunks, and
every chunk carries full provenance into its Qdrant payload.
"""

import math
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

PointId = Union[int, str, uuid.UUID]

# Source types understood by the ingestion pipeline.  ``official_web`` and
# ``regulator`` records must cite an http(s) URL; ``project_catalogue``
# records cite a repository file path (the project's own product tables
# and curated knowledge files).
KNOWLEDGE_SOURCE_TYPES = frozenset({"official_web", "regulator", "project_catalogue"})


def validate_point_id(point_id: PointId) -> PointId:
    """Validate a Qdrant-compatible point ID (unsigned int or UUID string).

    UUID strings are canonicalized so the same logical ID always lands in
    the same canonical form.  Returns the validated (canonical) ID.
    """
    if isinstance(point_id, bool):
        raise _bad_id(point_id, "booleans are not valid point IDs")
    if isinstance(point_id, int):
        if point_id < 0:
            raise _bad_id(point_id, "negative integers are not valid point IDs")
        return point_id
    if isinstance(point_id, uuid.UUID):
        return point_id
    if isinstance(point_id, str):
        try:
            return str(uuid.UUID(point_id))
        except ValueError:
            raise _bad_id(
                point_id,
                "string point IDs must be UUIDs (Qdrant restriction)",
            ) from None
    raise _bad_id(point_id, "point IDs must be unsigned integers, UUIDs, or UUID strings")


def _bad_id(point_id: object, reason: str):
    from chatbot.app.rag.errors import PointIdError

    return PointIdError(f"invalid point ID {point_id!r}: {reason}")


@dataclass(frozen=True)
class VectorRecord:
    """One vector point with arbitrary JSON-compatible payload metadata."""

    id: PointId
    vector: List[float]
    payload: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Validate the ID shape (raises PointIdError / canonicalizes strings).
        object.__setattr__(self, "id", validate_point_id(self.id))
        if not isinstance(self.vector, (list, tuple)) or not self.vector:
            raise ValueError("vector must be a non-empty sequence of numbers")
        for component in self.vector:
            if isinstance(component, bool) or not isinstance(component, (int, float)):
                raise ValueError("vector components must be numeric")
            if not math.isfinite(float(component)):
                raise ValueError("vector components must be finite")
        if not isinstance(self.payload, dict):
            raise ValueError("payload must be a JSON-compatible dict")


@dataclass(frozen=True)
class KnowledgeDocument:
    """One normalized, provenance-carrying knowledge source.

    ``content`` is normalized markdown-ish text; ``##``-prefixed heading
    lines delimit sections that chunking respects when a document is too
    large to embed whole.
    """

    source_id: str
    title: str
    content: str
    entity: str
    category: str
    source_url: str
    source_type: str
    retrieved_at: str
    subcategory: Optional[str] = None
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    effective_date: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class KnowledgeChunk:
    """One deterministic chunk of a ``KnowledgeDocument``.

    ``chunk_id`` is a stable content hash (same normalized chunk → same
    ID); ``point_id`` is the Qdrant-compatible UUIDv5 derived from it so
    re-ingestion upserts in place instead of duplicating points.
    """

    chunk_id: str
    point_id: str
    source_id: str
    chunk_index: int
    title: str
    section: Optional[str]
    content: str
    entity: str
    category: str
    subcategory: Optional[str]
    source_url: str
    source_type: str
    retrieved_at: str
    product_id: Optional[str]
    product_name: Optional[str]
    content_hash: str
    effective_date: Optional[str] = None

    def payload(self) -> Dict[str, Any]:
        """The Qdrant payload schema for this chunk (full provenance)."""
        return {
            "chunk_id": self.chunk_id,
            "source_id": self.source_id,
            "chunk_index": self.chunk_index,
            "title": self.title,
            "section": self.section,
            "content": self.content,
            "entity": self.entity,
            "category": self.category,
            "subcategory": self.subcategory,
            "source_url": self.source_url,
            "source_type": self.source_type,
            "retrieved_at": self.retrieved_at,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "effective_date": self.effective_date,
            "content_hash": self.content_hash,
        }


# ── Retrieval results ─────────────────────────────────────────────────────────
#
# Read-side mirror of the chunk payload: every field a downstream consumer
# needs to answer "what does this say, where did it come from, who owns
# it, and how relevant is it?" — with no Qdrant SDK type escaping the
# vector-store layer.


@dataclass(frozen=True)
class ScoredRecord:
    """One raw vector hit before payload interpretation."""

    id: Union[int, str, uuid.UUID]
    score: float
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RetrievedChunk:
    """One validated evidence chunk with full provenance.

    ``score`` is the raw cosine similarity in [-1, 1] as returned by
    Qdrant for COSINE collections — higher is better; callers surfacing
    it on 0–1 API contracts must clamp, not rescale.
    """

    point_id: Union[int, str, uuid.UUID]
    chunk_id: str
    source_id: str
    content: str
    title: str
    section: Optional[str] = None
    entity: str = ""
    category: str = ""
    subcategory: Optional[str] = None
    source_url: str = ""
    source_type: str = ""
    retrieved_at: str = ""
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    effective_date: Optional[str] = None
    score: float = 0.0
    content_hash: str = ""


@dataclass(frozen=True)
class RetrievalResult:
    """Outcome of one retrieval call: evidence plus diagnostics.

    Deliberately does NOT carry the raw query text — queries may contain
    personal information and are never echoed, logged, or persisted by
    the retrieval layer.  ``warnings`` carries skip/dedup diagnostics
    (never query content) so operators can spot corpus hygiene issues.
    """

    items: List[RetrievedChunk] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return bool(self.items)
