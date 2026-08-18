"""Deterministic, section-aware chunking for knowledge documents.

Philosophy: keep compact documents whole first, split semantic
boundaries second, enforce size limits third.  A document whose full
content fits within ``max_chunk_chars`` becomes a SINGLE chunk — this
keeps every fact about one catalogue product (fees, benefits,
eligibility) together in one embedded point, which is exactly what
follow-up questions ("what are its fees?") need.  Larger documents are
split on ``##`` section headings, then blank-line paragraphs, and only
when a single unit still exceeds ``max_chunk_chars`` does it fall back
to sentence packing.

Determinism contract: the same normalized document always produces the
same chunks in the same order with the same IDs.  ``chunk_id`` is the
SHA-256 of (source_id, section, content); ``point_id`` is UUIDv5 over
that chunk_id, satisfying Qdrant's UUID/int point-ID restriction without
unstable Python ``hash()`` calls.
"""

import hashlib
import re
import uuid
from typing import List, Optional, Tuple

from chatbot.app.rag.models import KnowledgeChunk, KnowledgeDocument

# bge-small-en-v1.5 encodes at most 512 tokens; ~2000 characters of
# banking prose stays comfortably inside that budget while allowing the
# compact catalogue documents (typically 700–1800 chars) to remain whole.
DEFAULT_MAX_CHUNK_CHARS = 2000

# Fixed namespace so UUIDv5 point IDs are stable across processes/runs.
_CHUNK_ID_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "npn-hdfc-chatbot:knowledge-chunk:v1")

_HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*$")
_SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")


def deterministic_chunk_id(source_id: str, section: Optional[str], content: str) -> str:
    """SHA-256 over the canonical (source_id, section, content) triple."""
    digest = hashlib.sha256(
        "\x1f".join((source_id, section or "", content)).encode("utf-8")
    ).hexdigest()
    return f"sha256:{digest}"


def chunk_point_id(chunk_id: str) -> str:
    """Stable Qdrant point ID (UUIDv5) derived from ``chunk_id``."""
    return str(uuid.uuid5(_CHUNK_ID_NAMESPACE, chunk_id))


def content_hash(content: str) -> str:
    """SHA-256 of chunk content, for changed/unchanged source detection."""
    return f"sha256:{hashlib.sha256(content.encode('utf-8')).hexdigest()}"


def chunk_document(
    document: KnowledgeDocument,
    max_chunk_chars: int = DEFAULT_MAX_CHUNK_CHARS,
) -> List[KnowledgeChunk]:
    """Split ``document`` into deterministic provenance-carrying chunks.

    Compact documents (whole content ≤ ``max_chunk_chars``) produce one
    whole-document chunk with ``section=None``; larger documents are
    split section-aware as described in the module docstring.
    """
    if not isinstance(max_chunk_chars, int) or max_chunk_chars < 40:
        raise ValueError(f"max_chunk_chars must be an int >= 40, got {max_chunk_chars!r}")
    if not document.content or not document.content.strip():
        raise ValueError(f"document {document.source_id!r} has no content to chunk")

    chunks: List[KnowledgeChunk] = []

    def _append(section: Optional[str], text: str) -> None:
        cid = deterministic_chunk_id(document.source_id, section, text)
        chunks.append(
            KnowledgeChunk(
                chunk_id=cid,
                point_id=chunk_point_id(cid),
                source_id=document.source_id,
                chunk_index=len(chunks),
                title=document.title,
                section=section,
                content=text,
                entity=document.entity,
                category=document.category,
                subcategory=document.subcategory,
                source_url=document.source_url,
                source_type=document.source_type,
                retrieved_at=document.retrieved_at,
                product_id=document.product_id,
                product_name=document.product_name,
                content_hash=content_hash(text),
                effective_date=document.effective_date,
            )
        )

    whole = document.content.strip()
    if len(whole) <= max_chunk_chars:
        _append(None, whole)
        return chunks

    for section, body in _sections(document.content):
        for piece in _pack(body, max_chunk_chars):
            text = piece.strip()
            if not text:
                continue
            _append(section, text)

    if not chunks:
        raise ValueError(f"document {document.source_id!r} produced no chunks")
    return chunks


def _sections(content: str) -> List[Tuple[Optional[str], str]]:
    """Split markdown content into (heading, body) pairs in order."""
    current_section: Optional[str] = None
    current_lines: List[str] = []
    sections: List[Tuple[Optional[str], str]] = []
    for line in content.split("\n"):
        match = _HEADING.match(line)
        if match:
            if any(l.strip() for l in current_lines):
                sections.append((current_section, "\n".join(current_lines).strip()))
            current_section = match.group(1).strip()
            current_lines = []
        else:
            current_lines.append(line)
    if any(l.strip() for l in current_lines):
        sections.append((current_section, "\n".join(current_lines).strip()))
    return sections


def _pack(body: str, max_chars: int) -> List[str]:
    """Pack paragraphs (then sentences) of one section into bounded pieces."""
    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
    pieces: List[str] = []
    buffer = ""
    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            # Flush what we have, then sentence-pack the oversized paragraph.
            if buffer:
                pieces.append(buffer)
                buffer = ""
            pieces.extend(_pack_sentences(paragraph, max_chars))
            continue
        candidate = f"{buffer}\n\n{paragraph}" if buffer else paragraph
        if len(candidate) > max_chars and buffer:
            pieces.append(buffer)
            buffer = paragraph
        else:
            buffer = candidate
    if buffer:
        pieces.append(buffer)
    return pieces


def _pack_sentences(paragraph: str, max_chars: int) -> List[str]:
    """Greedy sentence packing for a single oversized paragraph."""
    sentences = _SENTENCE_BOUNDARY.split(paragraph)
    pieces: List[str] = []
    buffer = ""
    for sentence in sentences:
        if not sentence.strip():
            continue
        candidate = f"{buffer} {sentence}".strip() if buffer else sentence.strip()
        if len(candidate) > max_chars and buffer:
            pieces.append(buffer)
            buffer = sentence.strip()
        else:
            buffer = candidate
    if buffer:
        pieces.append(buffer)
    # A single sentence longer than the limit is kept whole rather than
    # split mid-fact; callers should size limits above sentence length.
    return pieces
