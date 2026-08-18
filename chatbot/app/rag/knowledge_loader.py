"""Knowledge corpus loader.

Reads the manifest (``knowledge/hdfc/manifest.json``) and produces
:class:`~chatbot.app.rag.models.KnowledgeDocument` objects from the
curated markdown files in ``knowledge/hdfc/general/``.

Catalogue products (credit cards, loans) are loaded separately by
:mod:`~chatbot.app.rag.catalogue_adapter` from the repository's CSV
tables — they are NOT in this manifest.

Usage::

    from chatbot.app.rag.knowledge_loader import load_knowledge_corpus
    documents = load_knowledge_corpus("chatbot/knowledge/hdfc")
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List

from chatbot.app.rag.models import KnowledgeDocument


def load_knowledge_corpus(corpus_dir: str | Path) -> List[KnowledgeDocument]:
    """Load all manifest entries from a corpus directory.

    ``corpus_dir`` must contain ``manifest.json`` and a ``general/``
    subdirectory with the markdown files referenced by the manifest.
    """
    corpus_dir = Path(corpus_dir)
    manifest_path = corpus_dir / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"manifest not found: {manifest_path}")

    with manifest_path.open(encoding="utf-8") as f:
        manifest = json.load(f)

    entries = manifest.get("sources", [])
    if not isinstance(entries, list):
        raise ValueError("manifest 'sources' must be a list")

    documents: List[KnowledgeDocument] = []
    for entry in entries:
        doc = _load_entry(corpus_dir, entry)
        if doc is not None:
            documents.append(doc)

    return documents


def load_manifest_entry(corpus_dir: str | Path, source_id: str) -> KnowledgeDocument:
    """Load a single manifest entry by its source_id."""
    corpus_dir = Path(corpus_dir)
    manifest_path = corpus_dir / "manifest.json"

    with manifest_path.open(encoding="utf-8") as f:
        manifest = json.load(f)

    for entry in manifest["sources"]:
        if entry.get("source_id") == source_id:
            doc = _load_entry(corpus_dir, entry)
            if doc is not None:
                return doc

    raise KeyError(f"source_id {source_id!r} not found in manifest")


def _load_entry(corpus_dir: Path, entry: dict) -> KnowledgeDocument | None:
    """Convert one manifest entry + markdown file into a KnowledgeDocument."""
    md_file = corpus_dir / "general" / entry["file"]
    if not md_file.is_file():
        return None

    content = md_file.read_text(encoding="utf-8")

    retrieved_at = entry.get("retrieved_at")
    if not retrieved_at:
        retrieved_at = datetime.fromtimestamp(md_file.stat().st_mtime).strftime("%Y-%m-%d")

    return KnowledgeDocument(
        source_id=entry["source_id"],
        title=entry["title"],
        content=content,
        entity=entry["entity"],
        category=entry["category"],
        source_url=entry["source_url"],
        source_type=entry["source_type"],
        retrieved_at=retrieved_at,
        subcategory=entry.get("subcategory"),
        effective_date=entry.get("effective_date"),
    )
