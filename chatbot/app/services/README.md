# Chatbot Services

## Purpose

This directory contains the business logic that turns a user message into a complete chatbot response.

## Contents

| Item | Description |
| --- | --- |
| `orchestrator.py` | Coordinates intent routing, retrieval, recommendation, conversation state, and response generation. |
| `intent_router.py` | Classifies customer messages into supported intents. |
| `conversation.py` | Tracks multi-turn session context. |
| `recommendation.py` | Builds customer-aware recommendation payloads. |
| `product_catalog.py` | Resolves product names, aliases, and catalogue metadata. |
| `customer_context.py` | Loads and validates trusted customer context. |
| `groq_answer.py` | Optional answer generation support where configured. |
| `response_mapper.py` | Maps internal turn results to public API response models. |
| `dependencies.py` | Lazily initializes shared service dependencies. |

## Operational Notes

Use this directory as part of the documented application workflow. Keep generated files, secrets, and environment-specific artifacts out of source control unless they are intentional sample data.
