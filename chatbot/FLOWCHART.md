# Flowcharts

## 1. Chat request lifecycle

```mermaid
flowchart TD
    A[Client POST /chat] --> B{Pydantic contract<br/>extra=forbid}
    B -- violation --> E422[422 error]
    B -- valid --> C[router: handle_turn]
    C --> D{customer_id<br/>provided?}
    D -- yes --> E[CustomerContextBuilder<br/>features + events + gaps]
    E -- unknown ID --> E404[404 error]
    E -- ok --> F[AuthorizedCustomerContext]
    D -- no --> F2[context = None]
    F --> G
    F2 --> G[resolve_message<br/>pronoun → last product]
    G --> H[IntentRouter.route<br/>3-layer classification]
    H --> I{intent?}

    I -- UNSAFE_OR_SENSITIVE --> J[BLOCKED<br/>no downstream I/O]
    I -- OUT_OF_SCOPE --> K[OUT_OF_SCOPE]
    I -- CUSTOMER_ACCOUNT_QUERY --> L[ACCOUNT_ACCESS_NOT_WIRED]
    I -- TRANSACTION_QUERY --> M[TRANSACTION_ACCESS_NOT_WIRED]

    I -- PERSONALIZED_RECOMMENDATION --> N{Authorized<br/>context?}
    N -- none --> O[AUTHENTICATED_CONTEXT_REQUIRED<br/>clarifying question]
    N -- present --> P[NBOEngine → NBOAdapter]
    P --> Q[ProductIdResolver<br/>CC001 → HDFCFREEDOM]
    Q --> R[Qdrant exact filter<br/>product_id = canonical]
    R --> S{grounding<br/>chunks?}
    S -- none --> T[NO_EVIDENCE]
    S -- found --> U[SUCCESS +<br/>GroundedRecommendation]

    I -- retrieval intents<br/>GENERAL / PRODUCT_INFO /<br/>COMPARISON / SERVICE_HELP --> V{follow-up<br/>pronoun?}
    V -- yes --> W[filter by<br/>last_product_id]
    V -- no --> X[unfiltered query]
    W --> Y[embed query<br/>FastEmbed 384-d]
    X --> Y
    Y --> Z[Qdrant COSINE search<br/>+ payload filters]
    Z --> AA{chunks?}
    AA -- none --> AB[NO_EVIDENCE /<br/>NEEDS_CLARIFICATION]
    AA -- found --> AC[SUCCESS + sources]

    J --> AD[map_turn_result<br/>deterministic templates]
    K --> AD
    L --> AD
    M --> AD
    O --> AD
    T --> AD
    U --> AD
    AB --> AD
    AC --> AD
    AD --> AE[update conversation state<br/>safe fields only]
    AE --> AF[ChatResponse JSON]
```

## 2. Knowledge ingestion pipeline

```mermaid
flowchart LR
    A[manifest.json<br/>5 curated docs] --> C[load_knowledge_corpus]
    B1[credit_card_products.csv<br/>15 cards] --> D[catalogue_adapter<br/>structured docs]
    B2[loan_products.csv<br/>14 loans] --> D
    C --> E[34 KnowledgeDocuments]
    D --> E
    E --> F[validate + normalize<br/>deterministic]
    F --> G[chunking<br/>SHA-256 content hash<br/>UUIDv5 point IDs<br/>2000-char cap]
    G --> H[FastEmbed<br/>BAAI/bge-small-en-v1.5]
    H --> I[QdrantVectorStore.upsert<br/>source-replace semantics]
    I --> J[(chatbot/.qdrant<br/>34 points)]
```

## 3. Initialization — ChatbotStack composition

```mermaid
flowchart TD
    A[get_stack - lazy singleton] --> B[AI engine adapter<br/>sys.path + read-only engines]
    B -- failure --> B1[degrade: recommendations off]
    B -- ok --> C[CSVs: 15 cards / 14 loans / 1000 customers]
    C --> D[ProductIdResolver<br/>29 deterministic mappings]
    A --> E[FastEmbedProvider<br/>lazy ONNX]
    E --> F[QdrantVectorStore<br/>local chatbot/.qdrant]
    F --> G[KnowledgeRetriever]
    B --> H[CustomerContextBuilder]
    C --> H
    B --> I[NBOAdapter]
    D --> J[RecommendationOrchestrator]
    I --> J
    G --> J
    A --> K[InMemoryConversationStore<br/>TTL 30 min / 10 turns]
    A --> L[IntentRouter]
    L --> M[ChatbotOrchestrator]
    G --> M
    K --> M
    J --> M
    H --> M
```

## 4. Multi-turn follow-up (Hermes P2)

```mermaid
sequenceDiagram
    participant C as Client
    participant S as Server
    participant CS as ConversationStore
    participant Q as Qdrant

    C->>S: "Tell me about Regalia Gold credit card"
    S->>Q: search("Regalia Gold credit card")
    Q-->>S: catalogue-cc-hdfcrgold (0.84)
    S->>CS: last_product_id=HDFCRGOLD, last_product_name=Regalia Gold
    S-->>C: sources[product_id=HDFCRGOLD], conversation_id

    C->>S: "What about its fees?" (same conversation_id)
    S->>CS: get(conversation_id)
    CS-->>S: state (last_product_id=HDFCRGOLD)
    S->>S: resolve_message → "Regalia Gold What about its fees?"
    S->>S: route → PRODUCT_INFORMATION (bare "fees" rule)
    S->>Q: search(resolved, product_id=HDFCRGOLD)
    Q-->>S: Regalia-only chunks
    S-->>C: grounded answer scoped to Regalia
```

## 5. Personalized recommendation with grounding

```mermaid
sequenceDiagram
    participant C as Client
    participant R as Router
    participant CB as CustomerContextBuilder
    participant N as NBOEngine (existing)
    participant PR as ProductIdResolver
    participant Q as Qdrant

    C->>R: POST /chat {message, customer_id: CUST00001}
    R->>CB: build_context(CUST00001)
    CB->>CB: FeatureEngine + EventEngine + FinancialAnalyst
    CB-->>R: AuthorizedCustomerContext
    R->>N: determine_next_best_offer(features, events, gaps, data)
    N-->>R: full_result.product_data.credit_card_product_id = CC001
    R->>PR: resolve(CC001, credit_card)
    PR-->>R: HDFCFREEDOM / Freedom Credit Card
    R->>Q: search("Freedom Credit Card", product_id=HDFCFREEDOM)
    Q-->>R: catalogue-cc-hdfcfreedom (0.82) → confidence HIGH
    R-->>C: recommendation + supporting facts + source_ids
```
