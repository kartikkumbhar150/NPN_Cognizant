# Chatbot Tests

## Purpose

This directory contains tests for API behavior, intent routing, product catalog handling, conversation flow, orchestrator logic, and RAG components.

## Contents

| Item | Description |
| --- | --- |
| `conftest.py` | Shared pytest configuration and fixtures. |
| `test_api.py` | API route tests. |
| `test_conversation.py` | Conversation-state tests. |
| `test_intent_router.py` | Intent routing tests. |
| `test_product_catalog.py` | Product catalogue tests. |
| `test_orchestrator_units.py` | Orchestrator unit tests. |
| `test_qdrant_modes.py` | Qdrant mode tests. |
| `test_rag_units.py` | RAG unit tests. |
| `test_rag_integration.py` | RAG integration tests. |

## Operational Notes

Run with `python -m pytest chatbot/tests -q` from the repository root when dependencies are installed.
