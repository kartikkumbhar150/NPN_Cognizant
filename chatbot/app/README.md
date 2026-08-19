# Chatbot Application Package

## Purpose

This package contains the runtime implementation of the chatbot FastAPI service.

## Contents

| Item | Description |
| --- | --- |
| `main.py` | Creates the FastAPI app, configures CORS, includes routers, and manages startup and shutdown. |
| `config.py` | Loads environment-driven chatbot settings. |
| `api/` | HTTP endpoint definitions. |
| `models/` | Pydantic request and response contracts. |
| `rag/` | Retrieval, chunking, embedding, ingestion, normalization, and Qdrant storage code. |
| `services/` | Conversation orchestration, intent routing, recommendations, customer context, and dependency assembly. |
| `integrations/` | Adapters to external or sibling application components. |

## Operational Notes

Use this directory as part of the documented application workflow. Keep generated files, secrets, and environment-specific artifacts out of source control unless they are intentional sample data.
