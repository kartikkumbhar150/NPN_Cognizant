#!/usr/bin/env python3
"""Ingest the HDFC knowledge corpus into Qdrant.

Usage::

    # Validate only (no embedding, no Qdrant writes):
    python chatbot/scripts/ingest_hdfc_knowledge.py --validate-only

    # Dry run (validate + chunk counts, no Qdrant writes):
    python chatbot/scripts/ingest_hdfc_knowledge.py --dry-run

    # Full ingestion with local Qdrant:
    python chatbot/scripts/ingest_hdfc_knowledge.py
"""

import argparse
import sys
from pathlib import Path

# Ensure the repo root is on sys.path when run from any directory.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from chatbot.app.config import ChatbotSettings  # noqa: E402
from chatbot.app.rag.catalogue_adapter import (  # noqa: E402
    load_credit_card_catalogue,
    load_loan_catalogue,
)
from chatbot.app.rag.embeddings import FastEmbedProvider  # noqa: E402
from chatbot.app.rag.ingestion import KnowledgeIngestionService  # noqa: E402
from chatbot.app.rag.knowledge_loader import load_knowledge_corpus  # noqa: E402
from chatbot.app.rag.models import KnowledgeDocument  # noqa: E402
from chatbot.app.rag.qdrant_store import (  # noqa: E402
    QdrantVectorStore,
    create_qdrant_client,
)

CORPUS_DIR = PROJECT_ROOT / "chatbot" / "knowledge" / "hdfc"

ALLOWED_CATEGORIES = {
    "accounts", "deposits", "credit_card", "debit_card", "loans",
    "payments", "investments", "insurance", "forex", "nri",
    "business_banking", "digital_banking", "customer_service",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest HDFC knowledge corpus into Qdrant")
    parser.add_argument("--dry-run", action="store_true", help="Validate and chunk, but skip embedding/upsert")
    parser.add_argument("--validate-only", action="store_true", help="Only validate documents")
    parser.add_argument("--source", type=str, default=None, help="Ingest a single source_id")
    parser.add_argument("--category", type=str, default=None, choices=sorted(ALLOWED_CATEGORIES))
    parser.add_argument("--collection", type=str, default=None, help="Override collection name")
    parser.add_argument("--max-chunk-chars", type=int, default=2000, help="Max chars per chunk")
    args = parser.parse_args()

    settings = ChatbotSettings.from_env()

    # Load manifest documents
    print(f"Loading corpus from {CORPUS_DIR}...")
    manifest_docs = load_knowledge_corpus(CORPUS_DIR)
    print(f"  Manifest sources: {len(manifest_docs)}")

    # Load catalogue documents from existing project CSVs
    cc_docs = load_credit_card_catalogue(settings.credit_cards_csv)
    ln_docs = load_loan_catalogue(settings.loans_csv)
    catalogue_docs = cc_docs + ln_docs
    print(f"  Catalogue products: {len(cc_docs)} credit cards + {len(ln_docs)} loans = {len(catalogue_docs)}")

    all_docs: list = manifest_docs + catalogue_docs
    print(f"  Total documents: {len(all_docs)}")

    # Filter by source/category if requested
    if args.source:
        all_docs = [d for d in all_docs if d.source_id == args.source]
        print(f"  Filtered to source_id={args.source!r}: {len(all_docs)} documents")
    if args.category:
        all_docs = [d for d in all_docs if d.category == args.category]
        print(f"  Filtered to category={args.category!r}: {len(all_docs)} documents")

    if not all_docs:
        print("No documents to process.")
        sys.exit(0)

    # Validate only mode
    if args.validate_only:
        service = KnowledgeIngestionService(
            embedding_provider=None,  # type: ignore[arg-type]
            vector_store=None,  # type: ignore[arg-type]
            allowed_categories=ALLOWED_CATEGORIES,
        )
        failures = []
        for doc in all_docs:
            reason = service.validate_document(doc)
            if reason:
                failures.append(f"  FAIL {doc.source_id}: {reason}")
        if failures:
            print(f"\n{len(failures)} validation failures:")
            for f in failures:
                print(f)
            sys.exit(1)
        else:
            print(f"\nAll {len(all_docs)} documents passed validation.")
            sys.exit(0)

    # Full pipeline
    print("\nInitializing embedding provider (FastEmbed)...")
    provider = FastEmbedProvider(model_name=settings.embedding_model)

    collection = args.collection or settings.qdrant_collection
    print(f"Initializing Qdrant vector store (collection={collection})...")
    client = create_qdrant_client(settings)
    store = QdrantVectorStore(
        client=client,
        collection_name=collection,
        dimension=provider.dimension,
    )

    service = KnowledgeIngestionService(
        embedding_provider=provider,
        vector_store=store,
        allowed_categories=ALLOWED_CATEGORIES,
        max_chunk_chars=args.max_chunk_chars,
    )

    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Ingesting {len(all_docs)} documents...")
    result = service.ingest(all_docs, dry_run=args.dry_run)

    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Results:")
    print(f"  Documents processed: {result.documents_processed}")
    print(f"  Documents failed:   {result.documents_failed}")
    print(f"  Chunks generated:   {result.chunks_generated}")
    print(f"  Chunks embedded:    {result.chunks_embedded}")
    print(f"  Points upserted:    {result.points_upserted}")
    print(f"  Sources replaced:   {result.sources_replaced}")
    if result.warnings:
        print(f"  Warnings: {len(result.warnings)}")
        for w in result.warnings:
            print(f"    - {w}")
    if result.failures:
        print(f"  Failures: {len(result.failures)}")
        for f in result.failures:
            print(f"    - {f}")

    if result.documents_failed:
        sys.exit(1)
    print("\nDone.")


if __name__ == "__main__":
    main()
