# Chatbot RAG Pipeline

## Purpose

This directory contains the retrieval-augmented generation support layer for knowledge ingestion and source-grounded answers.

## Contents

| Item | Description |
| --- | --- |
| `chunking.py` | Splits knowledge documents into retrievable chunks. |
| `embeddings.py` | Creates vector embeddings for chunks and queries. |
| `qdrant_store.py` | Stores and searches embeddings in Qdrant. |
| `retriever.py` | Coordinates semantic retrieval. |
| `ingestion.py` | Builds the vector collection from source documents. |
| `knowledge_loader.py` | Loads manifest and markdown knowledge documents. |
| `catalogue_adapter.py` | Connects product catalogue data to chatbot retrieval and recommendations. |
| `normalization.py` | Normalizes product and query text. |
| `models.py` | Data models used by the RAG subsystem. |
| `errors.py` | RAG-specific exception types. |

## Operational Notes

Use this directory as part of the documented application workflow. Keep generated files, secrets, and environment-specific artifacts out of source control unless they are intentional sample data.
