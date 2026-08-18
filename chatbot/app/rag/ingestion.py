"""Knowledge ingestion orchestration.

Pipeline: load documents → validate → normalize → chunk → batch embed →
VectorRecord → Qdrant upsert, with a structured result.

Determinism: no generative LLM — embedding models are the only model
involved.  Re-ingesting the same corpus is idempotent (same chunk IDs
→ upserts in place).
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Sequence, Set

from chatbot.app.rag.chunking import DEFAULT_MAX_CHUNK_CHARS, chunk_document
from chatbot.app.rag.embeddings import EmbeddingProvider
from chatbot.app.rag.models import KNOWLEDGE_SOURCE_TYPES, KnowledgeDocument, VectorRecord
from chatbot.app.rag.normalization import normalize_text
from chatbot.app.rag.qdrant_store import QdrantVectorStore

FORBIDDEN_METADATA_KEYS = frozenset(
    {
        "customer_id", "account_number", "card_number",
        "jwt", "access_token", "refresh_token", "api_key", "password", "secret",
    }
)

_SOURCE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")


@dataclass(frozen=True)
class SourceFailure:
    """Why one source was rejected before embedding."""

    source_id: str
    reason: str

    def __str__(self) -> str:
        return f"{self.source_id}: {self.reason}"


@dataclass
class IngestionResult:
    """Structured outcome of one ingestion run (mutable accumulator)."""

    documents_processed: int = 0
    documents_failed: int = 0
    chunks_generated: int = 0
    chunks_embedded: int = 0
    points_upserted: int = 0
    sources_replaced: int = 0
    failures: List[SourceFailure] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class KnowledgeIngestionService:
    """Reusable ingestion orchestrator over an embedding provider + store."""

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: QdrantVectorStore,
        allowed_categories: Optional[Set[str]] = None,
        max_chunk_chars: int = DEFAULT_MAX_CHUNK_CHARS,
        batch_size: int = 32,
        replace_sources: bool = True,
    ) -> None:
        if batch_size < 1:
            raise ValueError(f"batch_size must be >= 1, got {batch_size!r}")
        self._provider = embedding_provider
        self._store = vector_store
        self._allowed_categories = allowed_categories
        self._max_chunk_chars = max_chunk_chars
        self._batch_size = batch_size
        self._replace_sources = replace_sources

    # ── Validation ────────────────────────────────────────────────────────────

    def validate_document(self, document: KnowledgeDocument) -> Optional[str]:
        """Return a rejection reason, or ``None`` when the document is valid."""
        if not isinstance(document, KnowledgeDocument):
            return f"expected KnowledgeDocument, got {type(document).__name__}"
        if not document.source_id or not _SOURCE_ID_PATTERN.match(document.source_id):
            return "source_id must be a non-empty lowercase slug ([a-z0-9-])"
        if not _is_date_like(document.retrieved_at):
            return "retrieved_at must be an ISO date (YYYY-MM-DD)"
        if not document.title or not document.title.strip():
            return "title must be non-empty"
        if not document.entity or not document.entity.strip():
            return "entity must be non-empty"
        if not document.category or not document.category.strip():
            return "category must be non-empty"
        if self._allowed_categories is not None and document.category not in self._allowed_categories:
            return (
                f"category {document.category!r} is not in the allowed set "
                f"{sorted(self._allowed_categories)}"
            )
        if document.source_type not in KNOWLEDGE_SOURCE_TYPES:
            return f"source_type must be one of {sorted(KNOWLEDGE_SOURCE_TYPES)}"
        if not document.source_url or not document.source_url.strip():
            return "source_url must be non-empty"
        if document.source_type in ("official_web", "regulator"):
            if not document.source_url.lower().startswith(("http://", "https://")):
                return f"source_type {document.source_type!r} requires an http(s) source_url"
        if (document.product_id is None) != (document.product_name is None):
            return "product_id and product_name must be provided together"
        if document.product_id is not None and not document.product_id.strip():
            return "product_id must be non-empty when provided"
        forbidden = sorted(set(document.metadata) & FORBIDDEN_METADATA_KEYS)
        if forbidden:
            return f"metadata contains forbidden private-data keys: {forbidden}"
        if not normalize_text(document.content):
            return "content is empty after normalization"
        return None

    # ── Ingestion ─────────────────────────────────────────────────────────────

    def ingest(self, documents: Sequence[KnowledgeDocument], dry_run: bool = False) -> IngestionResult:
        """Validate/normalize/chunk (and unless ``dry_run``, embed/upsert)."""
        result = IngestionResult()
        prepared: List[tuple] = []
        for document in documents:
            reason = self.validate_document(document)
            if reason is not None:
                result.failures.append(
                    SourceFailure(
                        document.source_id
                        if isinstance(document, KnowledgeDocument)
                        else "<not-a-document>",
                        reason,
                    )
                )
                result.documents_failed += 1
                continue
            normalized = KnowledgeDocument(
                source_id=document.source_id,
                title=document.title.strip(),
                content=normalize_text(document.content),
                entity=document.entity.strip(),
                category=document.category.strip(),
                source_url=document.source_url.strip(),
                source_type=document.source_type,
                retrieved_at=document.retrieved_at,
                subcategory=document.subcategory,
                product_id=document.product_id,
                product_name=document.product_name,
                effective_date=document.effective_date,
                metadata=dict(document.metadata),
            )
            try:
                chunks = chunk_document(normalized, self._max_chunk_chars)
            except ValueError as exc:
                result.failures.append(SourceFailure(document.source_id, str(exc)))
                result.documents_failed += 1
                continue
            prepared.append((normalized, chunks))
            result.documents_processed += 1
            result.chunks_generated += len(chunks)

        if dry_run:
            return result

        if not prepared:
            return result

        self._store.ensure_collection()

        for document, chunks in prepared:
            if self._replace_sources:
                self._store.delete_by_payload("source_id", document.source_id)
                result.sources_replaced += 1
            self._embed_and_upsert(document, chunks, result)

        return result

    def _embed_and_upsert(self, document, chunks, result) -> int:
        total = 0
        for start in range(0, len(chunks), self._batch_size):
            batch = chunks[start : start + self._batch_size]
            texts = [_embedding_text(document.title, c.section, c.content) for c in batch]
            vectors = self._provider.embed_documents(texts)
            records = [
                VectorRecord(id=chunk.point_id, vector=vector, payload=chunk.payload())
                for chunk, vector in zip(batch, vectors)
            ]
            total += self._store.upsert(records)
            result.chunks_embedded += len(batch)
        result.points_upserted += total
        return total


def _embedding_text(title: str, section: Optional[str], content: str) -> str:
    """Deterministic embedding input: title (and section) prefix the chunk body."""
    header = f"{title} — {section}" if section else title
    return f"{header}\n{content}"


def _is_date_like(value: str) -> bool:
    if not isinstance(value, str):
        return False
    try:
        datetime.fromisoformat(value)
    except ValueError:
        return False
    return True
