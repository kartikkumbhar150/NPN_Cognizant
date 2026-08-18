"""Lazy singleton ChatbotStack — the composition root.

Wire-time happens once on first access (not import time) so that:
1. Heavy resources (FastEmbed, Qdrant) are loaded only when the server starts.
2. Tests can swap components via ``reset_engines_cache()`` + re-injection.
3. Circular imports between services are impossible — everything is resolved
   through the stack object that owns the instances.
"""

from __future__ import annotations

import logging
import threading
from typing import Optional

from chatbot.app.config import ChatbotSettings

logger = logging.getLogger(__name__)

_stack: Optional[ChatbotStack] = None
_stack_lock = threading.Lock()


class ChatbotStack:
    """Composition root for all chatbot components.

    Created once on first call to ``get_stack()``; holds references to
    every service so they don't need to import each other.
    """

    def __init__(self, settings: Optional[ChatbotSettings] = None) -> None:
        self.settings = settings or ChatbotSettings.from_env()

        # Integrations (loaded lazily from existing Python/ai_engine)
        self.engines = None          # from get_engines()
        self.credit_cards_df = None  # pd.DataFrame
        self.loans_df = None         # pd.DataFrame
        self.customers_df = None     # pd.DataFrame

        # RAG components
        self.embedding_provider = None  # FastEmbedProvider
        self.qdrant_store = None        # QdrantVectorStore
        self.knowledge_retriever = None  # KnowledgeRetriever

        # Product resolution
        self.product_resolver = None  # ProductIdResolver

        # Services
        self.context_builder = None    # CustomerContextBuilder
        self.nbo_adapter = None        # NBOAdapter
        self.recommendation_orchestrator = None  # RecommendationOrchestrator
        self.conversation_store = None  # InMemoryConversationStore
        self.intent_router = None      # IntentRouter
        self.orchestrator = None       # ChatbotOrchestrator

        self._initialized = False

    def initialize(self) -> None:
        """Build all components from the loaded data and settings."""
        if self._initialized:
            return

        from chatbot.app.integrations.ai_engine_adapter import (
            get_engines,
            load_credit_cards,
            load_loan_products,
            load_customers,
        )
        from chatbot.app.rag.embeddings import FastEmbedProvider
        from chatbot.app.rag.qdrant_store import QdrantVectorStore, create_qdrant_client
        from chatbot.app.rag.retriever import KnowledgeRetriever
        from chatbot.app.services.product_catalog import ProductIdResolver
        from chatbot.app.services.customer_context import CustomerContextBuilder
        from chatbot.app.services.recommendation import NBOAdapter, RecommendationOrchestrator
        from chatbot.app.services.conversation import InMemoryConversationStore
        from chatbot.app.services.intent_router import IntentRouter
        from chatbot.app.services.orchestrator import ChatbotOrchestrator

        logger.info("Initializing ChatbotStack...")

        # Load engines and data
        try:
            self.engines = get_engines()
            self.credit_cards_df = load_credit_cards()
            self.loans_df = load_loan_products()
            self.customers_df = load_customers()
            logger.info(
                "Engines loaded: %d cards, %d loans, %d customers",
                len(self.credit_cards_df) if self.credit_cards_df is not None else 0,
                len(self.loans_df) if self.loans_df is not None else 0,
                len(self.customers_df) if self.customers_df is not None else 0,
            )
        except Exception as exc:
            logger.warning("AI engine init failed (recommendations disabled): %s", exc)

        # RAG
        try:
            self.embedding_provider = FastEmbedProvider(
                model_name=self.settings.embedding_model
            )
            client = create_qdrant_client(self.settings)
            self.qdrant_store = QdrantVectorStore(
                client=client,
                collection_name=self.settings.qdrant_collection,
                dimension=self.embedding_provider.dimension,
            )
            self.knowledge_retriever = KnowledgeRetriever(
                embedding_provider=self.embedding_provider,
                vector_store=self.qdrant_store,
            )
            logger.info("RAG pipeline initialized (collection=%s)", self.settings.qdrant_collection)
        except Exception as exc:
            logger.warning("RAG pipeline init failed (knowledge queries disabled): %s", exc)

        # Product resolver
        if self.credit_cards_df is not None and self.loans_df is not None:
            try:
                self.product_resolver = ProductIdResolver(
                    credit_cards_df=self.credit_cards_df,
                    loans_df=self.loans_df,
                )
                logger.info("Product resolver: %d mappings", self.product_resolver.mapping_count)
            except Exception as exc:
                logger.warning("Product resolver init failed: %s", exc)

        # Customer context builder
        if self.engines and self.customers_df is not None:
            try:
                self.context_builder = CustomerContextBuilder(
                    feature_engine=self.engines.get("feature_engine"),
                    event_engine=self.engines.get("event_engine"),
                    financial_analyst=self.engines.get("financial_analyst"),
                    customers_df=self.customers_df,
                )
            except Exception as exc:
                logger.warning("Customer context builder init failed: %s", exc)

        # NBO adapter
        if self.engines and self.engines.get("nbo_engine"):
            try:
                self.nbo_adapter = NBOAdapter(
                    nbo_engine=self.engines["nbo_engine"]
                )
            except Exception as exc:
                logger.warning("NBO adapter init failed: %s", exc)

        # Recommendation orchestrator
        if self.nbo_adapter and self.product_resolver and self.knowledge_retriever:
            try:
                self.recommendation_orchestrator = RecommendationOrchestrator(
                    nbo_adapter=self.nbo_adapter,
                    product_resolver=self.product_resolver,
                    knowledge_retriever=self.knowledge_retriever,
                )
            except Exception as exc:
                logger.warning("Recommendation orchestrator init failed: %s", exc)

        # Conversation and routing (always available — no external deps)
        self.conversation_store = InMemoryConversationStore(
            max_turns=self.settings.max_conversation_turns,
            ttl_seconds=self.settings.conversation_ttl_seconds,
        )
        self.intent_router = IntentRouter()

        # Orchestrator (needs router + retriever + conversation store)
        self.orchestrator = ChatbotOrchestrator(
            intent_router=self.intent_router,
            knowledge_retriever=self.knowledge_retriever,
            conversation_store=self.conversation_store,
            recommendation_orchestrator=self.recommendation_orchestrator,
            product_resolver=self.product_resolver,
            settings=self.settings,
            context_builder=self.context_builder,
        )

        self._initialized = True
        logger.info("ChatbotStack initialization complete")


def get_stack() -> ChatbotStack:
    """Return the global ChatbotStack singleton, initializing on first call."""
    global _stack
    if _stack is None:
        with _stack_lock:
            if _stack is None:
                _stack = ChatbotStack()
                _stack.initialize()
    return _stack


def reset_stack() -> None:
    """Tear down the global stack for testing or hot-reload."""
    global _stack
    with _stack_lock:
        _stack = None
        from chatbot.app.integrations.ai_engine_adapter import reset_engines_cache
        reset_engines_cache()
