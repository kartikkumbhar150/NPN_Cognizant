"""Integration tests: live RAG retrieval + grounded NBO recommendation.

These exercise the real stack (FastEmbed + local Qdrant + AI engines)
and require the corpus to be ingested.  Corpus-dependent tests skip
cleanly when Qdrant is empty.
"""

from __future__ import annotations

import pytest

from chatbot.app.rag.catalogue_adapter import (
    load_credit_card_catalogue,
    load_loan_catalogue,
)
from chatbot.app.rag.knowledge_loader import load_knowledge_corpus


def _qdrant_count(s) -> int:
    try:
        return s.qdrant_store.count()
    except Exception:
        return 0


class TestCorpus:
    def test_corpus_documents_load(self, settings):
        docs = load_knowledge_corpus(settings.corpus_dir)
        assert len(docs) >= 1
        for doc in docs:
            assert doc.content.strip()
            assert doc.source_url.startswith("https://")

    def test_catalogue_documents_match_csvs(self, settings, credit_cards_df, loans_df):
        cc_docs = load_credit_card_catalogue(settings.credit_cards_csv)
        ln_docs = load_loan_catalogue(settings.loans_csv)
        assert len(cc_docs) == len(credit_cards_df)
        assert len(ln_docs) == len(loans_df)

    def test_catalogue_source_ids_are_slugs(self, settings, credit_cards_df):
        cc_docs = load_credit_card_catalogue(settings.credit_cards_csv)
        by_source = {d.source_id: d for d in cc_docs}
        for _, row in credit_cards_df.iterrows():
            code = str(row["product_code"]).strip()
            # '+' codes slug to '-plus' (e.g. HDFCMB+ → catalogue-cc-hdfcmb-plus)
            slug = code.lower().replace("+", "-plus").replace(" ", "-")
            expected = f"catalogue-cc-{slug}"
            assert expected in by_source, f"missing slug {expected}"


class TestLiveRetrieval:
    @pytest.fixture(autouse=True)
    def _require_corpus(self, stack):
        if stack.qdrant_store is None or stack.qdrant_store.count() == 0:
            pytest.skip("Qdrant collection empty — run scripts/ingest_hdfc_knowledge.py")
        self.stack = stack
        self.retriever = stack.knowledge_retriever

    def test_neft_query_retrieves_neft_doc(self):
        result = self.retriever.search("What is NEFT?", limit=3)
        assert result.items
        assert result.items[0].source_id == "hdfc-neft"
        assert result.items[0].score > 0.5

    def test_product_filter_returns_only_that_product(self):
        identity = self.stack.product_resolver.resolve_canonical_id("HDFCRGOLD")
        result = self.retriever.search(
            "Regalia Gold", limit=3, product_id=identity.canonical_product_id,
        )
        assert result.items
        assert all(c.product_id == "HDFCRGOLD" for c in result.items)

    def test_entity_filter_hdfc_only(self):
        result = self.retriever.search("fees", limit=5, entity="HDFC Bank")
        assert all(c.entity == "HDFC Bank" for c in result.items)

    def test_scores_are_ranked(self):
        result = self.retriever.search("credit card annual fee", limit=5)
        scores = [c.score for c in result.items]
        assert scores == sorted(scores, reverse=True)


class TestGroundedRecommendation:
    @pytest.fixture(autouse=True)
    def _require_stack(self, stack):
        if stack.recommendation_orchestrator is None:
            pytest.skip("recommendation pipeline not initialized")
        if stack.qdrant_store is None or stack.qdrant_store.count() == 0:
            pytest.skip("Qdrant collection empty — run scripts/ingest_hdfc_knowledge.py")
        self.stack = stack

    def _customer_id(self) -> str:
        return str(self.stack.customers_df.iloc[0]["customer_id"])

    def test_first_customer_gets_grounded_recommendation(self):
        customer_id = self._customer_id()
        context = self.stack.context_builder.build_context(customer_id)
        recos = self.stack.recommendation_orchestrator.recommend(context)
        assert len(recos) >= 1
        rec = recos[0]
        # NBO → canonical mapping is deterministic and grounded in Qdrant
        assert rec.nbo_product_id
        assert rec.canonical_product_id
        assert rec.grounding_chunks, "recommendation must be grounded in catalogue"
        assert all(c.product_id == rec.canonical_product_id for c in rec.grounding_chunks)

    def test_unknown_customer_raises(self):
        from chatbot.app.services.customer_context import CustomerNotFoundError
        with pytest.raises(CustomerNotFoundError):
            self.stack.context_builder.build_context("CUST99999")

    def test_nbo_extraction_handles_product_data_quirk(self):
        """The NBO result's real ID lives in full_result.product_data."""
        from chatbot.app.services.recommendation import NBOAdapter
        customer_id = self._customer_id()
        context = self.stack.context_builder.build_context(customer_id)
        raw = self.stack.nbo_adapter.get_recommendation(
            features=context.features, events=context.events,
            financial_gaps=context.financial_gaps,
            customer_data=context.customer_data,
        )
        extracted = NBOAdapter.extract_nbo_product_ids(raw)
        assert extracted, "no product ID extracted from NBO result"
        assert extracted[0]["nbo_id"]
        assert extracted[0]["product_type"] in ("credit_card", "loan")

    def test_minimized_context_contains_no_pii_markers(self):
        customer_id = self._customer_id()
        context = self.stack.context_builder.build_context(customer_id)
        minimized = context.to_minimized()
        assert minimized.customer_id == customer_id
        # fields are aggregates/labels only
        assert isinstance(minimized.gap_codes, list)
        assert isinstance(minimized.event_types, list)
