# NPN Chatbot Service

Standalone FastAPI chatbot for HDFC Bank product knowledge and personalized
recommendations, running on **port 8001** — fully independent of the existing
`Python/api_server.py` (port 8000).

**Owner:** Harshvardhan Lokhande

## What it does

- **POST /chat** — conversational endpoint with intent routing, RAG-grounded
  answers, multi-turn context, and (with a trusted customer ID) personalized
  Next-Best-Offer recommendations.
- **GET /health** — component-level readiness (AI engine, RAG pipeline,
  Qdrant point count, product mappings).

## Quick start

```bash
# 1. Dependencies (reuse the existing venv which already has everything)
source Python/.venv/bin/activate

# 2. Ingest the knowledge corpus into local Qdrant (chatbot/.qdrant)
python chatbot/scripts/ingest_hdfc_knowledge.py

# 3. Run the service
python -m uvicorn chatbot.app.main:app --host 0.0.0.0 --port 8001

# 4. Try it
curl -s localhost:8001/health
curl -s -X POST localhost:8001/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "What is NEFT?"}'
```

## Example calls

```bash
# Product information (grounded in Qdrant)
curl -s -X POST localhost:8001/chat -H 'Content-Type: application/json' \
  -d '{"message": "Tell me about Regalia Gold credit card"}'

# Multi-turn follow-up (pronoun resolution + product-scoped retrieval)
curl -s -X POST localhost:8001/chat -H 'Content-Type: application/json' \
  -d '{"message": "What about its fees?", "conversation_id": "<id-from-previous-response>"}'

# Personalized recommendation — customer_id is the trusted-context channel
curl -s -X POST localhost:8001/chat -H 'Content-Type: application/json' \
  -d '{"message": "Which credit card should I get?", "customer_id": "CUST00001"}'
```

## API contract

### `POST /chat`

Request (unknown fields are rejected — `extra="forbid"`):

| Field             | Type   | Notes                                        |
|-------------------|--------|----------------------------------------------|
| `message`         | str    | 1–2000 chars, non-blank                      |
| `conversation_id` | UUID?  | omit on first turn; echo the returned ID     |
| `customer_id`     | str?   | trusted-context channel (see below)          |

Response:

| Field                | Type   | Meaning                                           |
|----------------------|--------|---------------------------------------------------|
| `answer`             | str    | deterministic template — no LLM anywhere           |
| `intent`             | enum   | e.g. `PRODUCT_INFORMATION`, `UNSAFE_OR_SENSITIVE` |
| `confidence`         | float  | routing confidence 0–1                            |
| `recommendations`    | list   | NBO items with `product_id`, `reason`, facts, `source_ids` |
| `sources`            | list   | provenance for every retrieved chunk              |
| `grounded`           | bool   | true only when backed by Qdrant evidence          |
| `clarifying_question`| str?   | present when input is ambiguous                   |
| `conversation_id`    | str    | UUID to continue the conversation                 |
| `safety_flags`       | list   | machine-readable markers (e.g. `unsafe_query`)    |

Errors: `422` contract violation, `404` unknown `customer_id`, `503`
orchestrator unavailable.

### `GET /health`

```json
{
  "status": "healthy",
  "components": {
    "ai_engine": "loaded",
    "rag_pipeline": "loaded",
    "orchestrator": "ready",
    "qdrant_points": "34",
    "product_mappings": "29"
  }
}
```

## Tests

```bash
source Python/.venv/bin/activate
python -m pytest chatbot/tests/ -q
# 110 passed
```

Data-driven: catalogue counts, mappings, and corpus sizes are read from the
real CSVs and manifest — never hardcoded — so the suite cannot silently drift
from the data. Corpus-dependent integration tests skip with instructions if
Qdrant has not been ingested yet.

## Configuration (`chatbot/.env.example`)

| Variable            | Default                        |
|---------------------|--------------------------------|
| `QDRANT_URL`        | *(empty = local embedded mode under `chatbot/.qdrant`)* |
| `QDRANT_API_KEY`    | *(empty)*                      |
| `QDRANT_COLLECTION` | `hdfc_banking_knowledge_v1`    |
| `EMBEDDING_MODEL`   | `BAAI/bge-small-en-v1.5` (384-d) |
| `RAG_TOP_K`         | `5`                            |
| `CHAT_SERVICE_PORT` | `8001`                         |
| `AI_ENGINE_DIR`     | `../Python` (the existing AI engine) |

## Layout

```
chatbot/
├── app/
│   ├── api/router.py          # POST /chat, GET /health
│   ├── config.py              # env-driven settings
│   ├── integrations/          # thin read-only adapter to Python/ai_engine
│   ├── main.py                # FastAPI app factory
│   ├── models/chat_models.py  # strict Pydantic contracts
│   ├── rag/                   # embeddings, chunking, Qdrant, retrieval, ingestion
│   └── services/              # intent router, orchestrator, recommendation, ...
├── knowledge/hdfc/            # manifest + curated general documents
├── scripts/ingest_hdfc_knowledge.py
└── tests/                     # 110 tests (unit + integration + API)
```

## Design constraints honoured

- **No modifications** to `Python/ai_engine`, `Python/api_server.py`,
  `frontend/`, or `Customer_Application/` — the AI engine is consumed
  read-only through `app/integrations/ai_engine_adapter.py`.
- **No LLM** — answers are deterministic templates over retrieved evidence.
- **customer_id trust model** — identity is supplied by the calling
  application after its own authentication (same employee-dashboard trust
  model as the existing api_server); never derived from message text.
- All generated data (Qdrant storage) stays inside `chatbot/.qdrant`.

See `ARCHITECTURE.md` for the component graph and `FLOWCHART.md` for
request-flow diagrams.
