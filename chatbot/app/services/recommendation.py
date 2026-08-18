"""NBO integration and grounded recommendation pipeline.

Thin read-only adapter around the existing ``NBOEngine`` from
``Python/ai_engine``.  The NBO result (candidate product ID) is resolved
to a canonical product via ``ProductIdResolver`` and then grounded
against the Qdrant catalogue with an exact ``product_id`` filter — no
semantic similarity for recommendations, only deterministic lookup.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from chatbot.app.rag.models import RetrievedChunk, RetrievalResult
from chatbot.app.services.customer_context import AuthorizedCustomerContext
from chatbot.app.services.product_catalog import (
    ProductIdResolver,
    ProductIdentity,
    ProductResolutionError,
)


class RecommendationError(Exception):
    """Base class for recommendation failures."""


class NBOUnavailableError(RecommendationError):
    """The NBO engine could not produce a recommendation."""


class NoGroundingError(RecommendationError):
    """The NBO candidate has no grounding in the knowledge base."""


class ProductMismatchError(RecommendationError):
    """The NBO candidate resolved to an unexpected canonical product."""


class RecommendationConfidence(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class GroundedRecommendation:
    """A recommendation grounded in both NBO pipeline and Qdrant catalogue."""

    product_identity: ProductIdentity
    confidence: RecommendationConfidence
    nbo_raw: Dict[str, Any] = field(default_factory=dict)
    grounding_chunks: List[RetrievedChunk] = field(default_factory=list)
    recommendation_text: str = ""
    reasoning: str = ""

    @property
    def nbo_product_id(self) -> str:
        return self.product_identity.nbo_product_id

    @property
    def canonical_product_id(self) -> str:
        return self.product_identity.canonical_product_id

    @property
    def product_name(self) -> str:
        return self.product_identity.product_name


class NBOAdapter:
    """Thin wrapper calling the existing NBOEngine.

    Reads the NBO result and extracts the candidate product identifiers
    using the known quirk: top-level ``product_id`` is empty; the real ID
    lives in ``full_result["product_data"]["credit_card_product_id"]``.
    """

    def __init__(self, nbo_engine) -> None:
        self._nbo_engine = nbo_engine

    def get_recommendation(
        self, features, events, financial_gaps, customer_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call the existing NBO engine and return the raw result dict."""
        try:
            result = self._nbo_engine.determine_next_best_offer(
                features=features,
                events=events,
                financial_gaps=financial_gaps,
                customer_data=customer_data,
            )
        except Exception as exc:
            raise NBOUnavailableError(
                f"NBO engine call failed: {type(exc).__name__}: {exc}"
            ) from exc

        if not result or not isinstance(result, dict):
            raise NBOUnavailableError("NBO engine returned empty or non-dict result")

        return result

    @staticmethod
    def extract_nbo_product_ids(result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract product identifiers from an NBO result dict.

        Returns a list of dicts, each with ``product_type`` and ``nbo_id``.
        The known quirk: top-level ``product_id`` may be empty; the real
        ID is in ``full_result["product_data"]``.
        """
        products: List[Dict[str, Any]] = []

        top_level_id = result.get("product_id", "")
        top_level_type = result.get("product_type", "")

        full_result = result.get("full_result", {})
        product_data = full_result.get("product_data", {})

        # Try to resolve the real ID from product_data
        real_id = ""
        real_type = ""

        if isinstance(product_data, dict):
            for id_field, ptype in [
                ("credit_card_product_id", "credit_card"),
                ("loan_product_id", "loan"),
            ]:
                pid = product_data.get(id_field, "")
                if pid and str(pid).strip():
                    real_id = str(pid).strip()
                    real_type = ptype
                    break

        # Fallback: if product_data didn't have it, try top-level
        if not real_id and top_level_id:
            real_id = str(top_level_id).strip()
            real_type = top_level_type or "credit_card"

        if real_id:
            products.append({"product_type": real_type, "nbo_id": real_id})

        return products


class RecommendationOrchestrator:
    """Produces grounded recommendations for a customer context.

    Pipeline: NBO engine → resolve canonical ID → Qdrant grounding.
    """

    def __init__(
        self,
        nbo_adapter: NBOAdapter,
        product_resolver: ProductIdResolver,
        knowledge_retriever,
        max_grounding_chunks: int = 3,
    ) -> None:
        self._nbo = nbo_adapter
        self._resolver = product_resolver
        self._retriever = knowledge_retriever
        self._max_grounding_chunks = max_grounding_chunks

    def recommend(self, context: AuthorizedCustomerContext) -> List[GroundedRecommendation]:
        """Generate grounded recommendations for the given customer context."""
        if context is None:
            raise RecommendationError("context is required")

        # Call NBO
        nbo_result = self._nbo.get_recommendation(
            features=context.features,
            events=context.events,
            financial_gaps=context.financial_gaps,
            customer_data=context.customer_data,
        )

        # Extract product IDs
        product_ids = NBOAdapter.extract_nbo_product_ids(nbo_result)
        if not product_ids:
            raise NBOUnavailableError(
                "NBO engine returned no product IDs in the result"
            )

        recommendations: List[GroundedRecommendation] = []
        for pid_info in product_ids:
            nbo_id = pid_info["nbo_id"]
            ptype = pid_info["product_type"]

            # Resolve to canonical identity
            identity = self._resolve_identity(nbo_id, ptype)
            if identity is None:
                continue

            # Ground in Qdrant with exact filter
            grounding = self._ground(identity)

            confidence = self._assess_confidence(grounding, nbo_result)

            rec = GroundedRecommendation(
                product_identity=identity,
                confidence=confidence,
                nbo_raw=nbo_result,
                grounding_chunks=grounding.items if grounding else [],
                recommendation_text=self._compose_text(identity, grounding),
                reasoning=self._compose_reasoning(identity, confidence, grounding),
            )
            recommendations.append(rec)

        return recommendations

    def _resolve_identity(
        self, nbo_id: str, product_type: str
    ) -> Optional[ProductIdentity]:
        try:
            return self._resolver.resolve_nbo_id(nbo_id, product_type)
        except (ProductResolutionError, ValueError):
            return None

    def _ground(self, identity: ProductIdentity) -> Optional[RetrievalResult]:
        try:
            result = self._retriever.search(
                query=identity.product_name,
                limit=self._max_grounding_chunks,
                product_id=identity.canonical_product_id,
            )
            return result if result and result.items else None
        except Exception:
            return None

    @staticmethod
    def _assess_confidence(
        grounding: Optional[RetrievalResult],
        nbo_result: Dict[str, Any],
    ) -> RecommendationConfidence:
        if grounding and grounding.items:
            top_score = grounding.items[0].score
            if top_score >= 0.7:
                return RecommendationConfidence.HIGH
            if top_score >= 0.4:
                return RecommendationConfidence.MEDIUM
        return RecommendationConfidence.LOW

    @staticmethod
    def _compose_text(
        identity: ProductIdentity,
        grounding: Optional[RetrievalResult],
    ) -> str:
        text = f"Based on your profile, I recommend the {identity.product_name}."
        if grounding and grounding.items:
            first = grounding.items[0]
            if first.content:
                snippet = first.content[:200].strip()
                if snippet:
                    text += f" {snippet}"
        return text

    @staticmethod
    def _compose_reasoning(
        identity: ProductIdentity,
        confidence: RecommendationConfidence,
        grounding: Optional[RetrievalResult],
    ) -> str:
        parts = [
            f"NBO candidate: {identity.product_name} ({identity.nbo_product_id})",
            f"Canonical: {identity.canonical_product_id}",
            f"Confidence: {confidence.value}",
        ]
        if grounding:
            parts.append(f"Grounding chunks: {len(grounding.items)}")
        return "; ".join(parts)
