"""Unit tests: RAG primitives — chunking, normalization, models."""

from __future__ import annotations

import pytest

from chatbot.app.rag.chunking import (
    chunk_document,
    chunk_point_id,
    content_hash,
    deterministic_chunk_id,
)
from chatbot.app.rag.errors import PointIdError
from chatbot.app.rag.models import (
    KnowledgeDocument,
    RetrievedChunk,
    validate_point_id,
)
from chatbot.app.rag.normalization import canonical_url, normalize_text


def _doc(content: str, source_id: str = "test-doc") -> KnowledgeDocument:
    return KnowledgeDocument(
        source_id=source_id, title="Test", content=content,
        entity="HDFC Bank", category="payments",
        source_url="https://hdfc.bank.in/test", source_type="curated",
        retrieved_at="2026-01-01",
    )


# ── normalization ─────────────────────────────────────────────────────────


class TestNormalization:
    def test_collapses_whitespace_runs(self):
        assert normalize_text("a  b\t\tc") == "a b c"

    def test_crlf_becomes_lf(self):
        assert normalize_text("a\r\nb\rc") == "a\nb\nc"

    def test_excess_newlines_collapse_to_one_blank_line(self):
        assert normalize_text("a\n\n\n\n\nb") == "a\n\nb"

    def test_strips_document(self):
        assert normalize_text("  \n hello \n ") == "hello"

    def test_empty_returns_empty(self):
        assert normalize_text("   ") == ""

    def test_rejects_non_string(self):
        with pytest.raises(TypeError):
            normalize_text(123)

    def test_canonical_url_lowercases_host_and_drops_tracking(self):
        url = canonical_url("https://Example.COM/page/?utm_source=x&id=7")
        assert url == "https://example.com/page?id=7"

    def test_canonical_url_drops_fragment_and_trailing_slash(self):
        assert canonical_url("https://hdfc.bank.in/cards/#fees") == "https://hdfc.bank.in/cards"

    def test_canonical_url_rejects_non_http(self):
        with pytest.raises(ValueError):
            canonical_url("ftp://hdfc.bank.in/file")


# ── chunking ──────────────────────────────────────────────────────────────


class TestChunking:
    def test_short_document_is_single_chunk(self):
        chunks = chunk_document(_doc("NEFT settles in batches."))
        assert len(chunks) == 1
        assert chunks[0].source_id == "test-doc"

    def test_chunk_ids_are_deterministic(self):
        doc = _doc("Stable content.", source_id="stable")
        first = chunk_document(doc)
        second = chunk_document(doc)
        assert [c.chunk_id for c in first] == [c.chunk_id for c in second]

    def test_different_content_yields_different_hashes(self):
        assert content_hash("fees") != content_hash("features")

    def test_chunk_point_id_is_valid_uuid(self):
        pid = chunk_point_id("sha256:abc123")
        validate_point_id(pid)  # raises on invalid

    def test_deterministic_chunk_id_is_content_hash(self):
        cid = deterministic_chunk_id("src-1", None, "content")
        assert cid.startswith("sha256:")
        # same inputs → same ID; different content → different ID
        assert cid == deterministic_chunk_id("src-1", None, "content")
        assert cid != deterministic_chunk_id("src-1", None, "other content")

    def test_long_document_splits_within_max_chars(self):
        long_content = ("Annual fee waiver on spending. " * 120).strip()
        chunks = chunk_document(_doc(long_content), max_chunk_chars=500)
        assert len(chunks) > 1
        assert all(len(c.content) <= 500 for c in chunks)


# ── models ────────────────────────────────────────────────────────────────


class TestRagModels:
    def test_retrieved_chunk_is_immutable_value_object(self):
        chunk = RetrievedChunk(
            point_id=chunk_point_id("sha256:x"), chunk_id="c",
            source_id="s", content="x", title="t",
            entity="e", category="payments", score=0.8,
        )
        with pytest.raises(Exception):
            chunk.score = 1.0  # frozen dataclass

    def test_validate_point_id_rejects_bad_uuid(self):
        with pytest.raises(PointIdError):
            validate_point_id("not-a-uuid")

    def test_validate_point_id_canonicalizes_uuid_strings(self):
        import uuid as _uuid
        raw = str(_uuid.uuid4())
        canonical = validate_point_id(raw.upper())  # non-canonical casing
        assert canonical == raw  # canonicalized to lowercase string form
