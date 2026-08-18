# HDFC Bank Knowledge Corpus

## Overview

This directory contains the curated knowledge corpus for the HDFC banking
chatbot's RAG (Retrieval-Augmented Generation) pipeline.

## Structure

- `manifest.json` — canonical source list (committed, never auto-generated)
- `general/` — curated markdown knowledge files for general banking concepts
  that are not tied to a specific catalogue product (NEFT, RTGS, UPI, KYC, etc.)

## Catalogue Products

Credit-card and loan product documents are **generated at ingestion time**
from the repository's CSV tables (`Python/Database_csvs/`), not stored here.
The catalogue adapter (`chatbot.app.rag.catalogue_adapter`) converts each
active product row into a `KnowledgeDocument` with structured content
(fees, eligibility, benefits, interest rates).

## Manifest Format

Each entry in `manifest.json` specifies:
- `source_id` — unique lowercase slug (must match `[a-z0-9-]`)
- `title` — human-readable display name
- `category` — one of the allowed knowledge categories
- `entity` — "HDFC Bank" (attribution)
- `source_url` — provenance URL (may be a `project_catalogue` file path)
- `source_type` — "official_web", "regulator", or "project_catalogue"
- `file` — path relative to `general/` (for curated local documents)

## Ingestion

Run the ingestion script to embed and store all documents in Qdrant:

```bash
cd <repo-root>
python chatbot/scripts/ingest_hdfc_knowledge.py
```

The script:
1. Loads general-knowledge markdown files from `knowledge/hdfc/general/`
2. Loads catalogue products from CSV (15 credit cards + 14 loans)
3. Validates, normalizes, and chunks all documents
4. Embeds with FastEmbed (BAAI/bge-small-en-v1.5, 384-dim)
5. Upserts into a local Qdrant collection
