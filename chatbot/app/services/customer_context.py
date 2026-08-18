"""Authorized customer context for personalized recommendations.

Builds the input the existing NBO pipeline consumes — verified from
``NBOEngine.determine_next_best_offer(features, events, financial_gaps,
customer_data)``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List

import pandas as pd

_MINIMIZED_FORBIDDEN_MARKERS = (
    "email", "phone", "mobile", "address",
    "account_number", "card_number", "password",
    "token", "pan", "aadhaar",
)


class CustomerContextError(Exception):
    """Base class for customer-context failures."""


class CustomerNotFoundError(CustomerContextError):
    """The customer ID does not exist in the customers catalogue."""


class ContextBuildError(CustomerContextError):
    """An engine failed while building the context."""


@dataclass(frozen=True)
class CustomerContextData:
    """Data-minimized customer signals safe for downstream layers."""

    customer_id: str
    has_transactions: bool = False
    data_quality_score: float = 0.0
    monthly_income_avg: float = 0.0
    gap_codes: List[str] = field(default_factory=list)
    event_types: List[str] = field(default_factory=list)
    held_card_names: List[str] = field(default_factory=list)
    held_loan_categories: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class AuthorizedCustomerContext:
    """Internal execution context for the NBO pipeline.

    NOT authentication — see module docstring.  Consumed by
    ``NBOAdapter`` / ``RecommendationOrchestrator`` and never
    embedded in the chatbot-facing ``RecommendationResult``.
    """

    customer_id: str
    customer_data: Dict[str, Any]
    features: Any
    events: List[Dict[str, Any]] = field(default_factory=list)
    financial_gaps: List[Dict[str, Any]] = field(default_factory=list)
    computed_at: str = ""

    def to_minimized(self) -> CustomerContextData:
        features = self.features
        gaps = self.financial_gaps or []
        events = self.events or []
        return CustomerContextData(
            customer_id=self.customer_id,
            has_transactions=bool(getattr(features, "has_transactions", False)),
            data_quality_score=float(getattr(features, "data_quality_score", 0.0) or 0.0),
            monthly_income_avg=float(getattr(features, "monthly_income_avg", 0.0) or 0.0),
            gap_codes=[str(g.get("code")) for g in gaps if g.get("code")],
            event_types=[str(e.get("event_type")) for e in events if e.get("event_type")],
            held_card_names=list(getattr(features, "held_card_names", None) or []),
            held_loan_categories=list(getattr(features, "held_loan_categories", None) or []),
        )


class CustomerContextBuilder:
    """Builds ``AuthorizedCustomerContext`` for a verified customer ID.

    All dependencies are injected.
    """

    def __init__(self, feature_engine, event_engine, financial_analyst,
                 customers_df: pd.DataFrame) -> None:
        if customers_df is None or "customer_id" not in customers_df.columns:
            raise CustomerContextError("customers_df must have 'customer_id' column")
        self._feature_engine = feature_engine
        self._event_engine = event_engine
        self._financial_analyst = financial_analyst
        self._customers_df = customers_df

    def build_context(self, customer_id: str) -> AuthorizedCustomerContext:
        if not isinstance(customer_id, str) or not customer_id.strip():
            raise CustomerNotFoundError("customer_id must be a non-empty string")
        customer_row = self._customers_df[self._customers_df["customer_id"] == customer_id]
        if customer_row.empty:
            raise CustomerNotFoundError(
                f"customer {customer_id!r} not found in the customers catalogue"
            )
        customer_data = customer_row.iloc[0].to_dict()
        try:
            features = self._feature_engine.compute(customer_id, customer_data)
            events = self._event_engine.detect_events(customer_id, features)
            analysis = self._financial_analyst.analyse(customer_id, customer_data, features)
        except CustomerContextError:
            raise
        except Exception as exc:
            raise ContextBuildError(
                f"context build failed for {customer_id!r}: {type(exc).__name__}"
            ) from exc

        gaps = analysis.get("gaps", []) if isinstance(analysis, dict) else []
        return AuthorizedCustomerContext(
            customer_id=customer_id, customer_data=customer_data,
            features=features, events=list(events or []),
            financial_gaps=list(gaps or []),
            computed_at=datetime.now(timezone.utc).isoformat(),
        )

    @staticmethod
    def minimized_forbidden_markers() -> tuple:
        return _MINIMIZED_FORBIDDEN_MARKERS
