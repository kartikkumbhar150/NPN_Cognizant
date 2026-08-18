# Architecture

## Component graph

```
                          ┌──────────────────────────────────────────────┐
                          │  FastAPI app (port 8001)                     │
                          │  chatbot/app/main.py                         │
                          └──────────────┬───────────────────────────────┘
                                         │ POST /chat   GET /health
                         ┌───────────────▼───────────────┐
                         │  api/router.py                │
                         │  - contract enforcement is    │
                         │    done by Pydantic models    │
                         │  - customer_id → 404 on miss  │
                         └───────────────┬───────────────┘
                                         │ handle_turn(message, customer_id, session_id)
        ┌────────────────────────────────▼─────────────────────────────────┐
        │  ChatbotOrchestrator (services/orchestrator.py)                 │
        │  1. resolve_message()      pronoun → last product name          │
        │  2. IntentRouter.route()   3-layer classification               │
        │  3. _dispatch()            per-intent execution                 │
        │  4. conversation store     append turn + safe context updates   │
        └──┬───────────────┬──────────────────┬───────────────────────────┘
           │               │                  │
  requires_retrieval   PERSONALIZED_RECOMMENDATION        UNSAFE / OOS /
           │               │                              ACCOUNT / TRANSACTION
┌──────────▼─────────┐ ┌───▼────────────────────────┐     │
│ KnowledgeRetriever │ │ CustomerContextBuilder     │     │  deterministic
│ (rag/retriever.py) │ │ → AuthorizedCustomerContext│     │  refusal /
│ embed query →      │ │   (features, events, gaps) │     │  clarification
│ Qdrant COSINE +    │ └───┬────────────────────────┘     │  paths, no I/O
│ payload filters →  │     │ recommend(ctx)               │
│ dedup → cap        │ ┌───▼────────────────────────┐     │
└──────────┬─────────┘ │ RecommendationOrchestrator │     │
           │           │ 1. NBOAdapter.get_recommendation()
           │           │    (existing NBOEngine, read-only)│
           │           │ 2. ProductIdResolver: NBO CC001  │
           │           │    → canonical HDFCFREEDOM        │
           │           │ 3. Qdrant exact product_id filter │
           │           │    → grounding chunks             │
           │           └───┬────────────────────────┘     │
           │               │ GroundedRecommendation        │
┌──────────▼───────────────▼──────────────────────────────▼──────────────┐
│  response_mapper.map_turn_result()                                     │
│  ChatTurnResult → ChatResponse (sources, items, deterministic answer)  │
└────────────────────────────────────────────────────────────────────────┘
```

## Data flow at initialization (`services/dependencies.py`)

`ChatbotStack` is a lazy thread-safe singleton — the composition root.
Every component is constructed once, with explicit dependencies, on first
request (or first `get_stack()` call):

1. **AI engine adapter** (`integrations/ai_engine_adapter.py`) — adds
   `Python/` to `sys.path`, calls the existing engine constructors, and
   loads the CSVs (15 credit cards, 14 loans, 1000 customers). Falls back
   gracefully: if this fails, knowledge chat still works; only personalized
   recommendations are disabled.
2. **RAG pipeline** — `FastEmbedProvider` (BAAI/bge-small-en-v1.5, 384-dim,
   lazy ONNX load) + `QdrantVectorStore` (local embedded mode under
   `chatbot/.qdrant` by default).
3. **ProductIdResolver** — deterministic 1:1 NBO↔canonical mapping built
   from the two catalogue DataFrames (29 mappings). Ambiguity is a hard
   error, never a fuzzy match.
4. **Services** — context builder, NBO adapter, recommendation
   orchestrator, conversation store (in-memory, TTL 30 min, 10-turn bound),
   intent router, orchestrator.

## Intent routing (3 layers)

| Layer | Mechanism | Notes |
|-------|-----------|-------|
| 1 | Deterministic regex rules | precedence: UNSAFE → ACCOUNT → TRANSACTION → RECOMMENDATION → COMPARISON → SERVICE_HELP → GENERAL → PRODUCT_INFO; includes negation guards |
| 2 | Optional classifier (Protocol) | pluggable, never required; default build ships without one |
| 3 | Banking-affinity fallback | domain vocabulary hit → GENERAL_BANKING_QUERY (0.40); otherwise OUT_OF_SCOPE |

**Hermes P2 fix** — bare product-detail words ("fees", "features",
"eligibility") route to PRODUCT_INFORMATION even without banking keywords,
so multi-turn follow-ups like "What about its fees?" never fall to
OUT_OF_SCOPE.

## Grounded recommendation pipeline

```
customer_id (trusted-context channel)
   → CustomerContextBuilder
       FeatureEngine.compute + EventEngine.detect_events
       + FinancialAnalyst.analyse            (existing ai_engine, read-only)
   → NBOAdapter.get_recommendation
       NBOEngine.determine_next_best_offer(...)
       quirk: top-level product_id is EMPTY;
       real ID lives in full_result.product_data.credit_card_product_id
   → ProductIdResolver
       CC001 → HDFCFREEDOM (deterministic, 1:1, no fuzzy match)
   → Qdrant grounding
       exact payload filter product_id=HDFCFREEDOM (no similarity for IDs)
   → GroundedRecommendation (confidence from grounding score)
```

The HDFCMB+ rule: the canonical `product_code` `HDFCMB+` is preserved
as-is in Qdrant payloads, while the ingestion `source_id` uses the
URL-safe slug `catalogue-cc-hdfcmb-plus` (`+` → `-plus`).

## Conversation memory

- In-memory store keyed by UUID; caller-supplied IDs are honoured on
  creation (so API clients can pin their own session IDs).
- TTL 30 min, hard bound of 10 turns, safe-field allowlist on context
  updates, sensitive keys (card numbers, OTPs, ...) are dropped.
- Only derived state is kept: `last_intent`, `last_product_id/name/type`,
  `last_category` — never raw customer data.

## Failure semantics

| Failure | Behaviour |
|---------|-----------|
| Qdrant unreachable/empty | SERVICE_UNAVAILABLE status, `knowledge_service_unavailable` safety flag; server stays up |
| AI engine init failure | recommendations disabled; knowledge chat unaffected |
| Unknown customer_id | 404 — trusted-context failures surface, never silently degrade to anonymous |
| NBO returns no usable ID | NO_EVIDENCE (never fabricate a recommendation) |
| Contract violation | 422 at the Pydantic boundary (`extra="forbid"` everywhere) |

## Boundaries honoured

- `Python/ai_engine` is **read-only** — consumed only through the thin
  adapter; no modifications to engine code, `api_server.py`, `frontend/`,
  or `Customer_Application/`.
- No LLM anywhere: answer text is template-composed from status + evidence.
- All generated artifacts (Qdrant storage, model cache) stay under
  `chatbot/`.
