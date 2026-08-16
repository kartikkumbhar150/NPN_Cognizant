"""
Behavior Engine (v2.0)
======================
Banking-Grade Customer Intelligence — NPN Bank AI Pipeline v2.0

Upgrades from v1:
  - Uses CustomerFeatureSet from FeatureEngine (single categorization source)
  - Rolling-window spend analysis (30/60/90/180 day windows)
  - Payment channel behavior (UPI vs cash vs card)
  - Time-of-day and weekday/weekend patterns
  - Top merchant analysis
  - Backward-compatible public API: analyze_behavior(), detect_events()
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any, Dict, List, Optional

import pandas as pd

from feature_engine import CustomerFeatureSet, categorize_merchant, WINDOW_DAYS

logger = logging.getLogger(__name__)


class BehaviorEngine:
    """
    Generates a comprehensive behavioral profile from CustomerFeatureSet + raw transactions.

    Maintains backward-compatible signatures with v1.
    New callers should use analyze_behavior_v2() for the richer output.
    """

    def __init__(self, transactions_df: pd.DataFrame) -> None:
        self.transactions = transactions_df.copy() if transactions_df is not None else pd.DataFrame()

        # Ensure category column for backward compat
        if not self.transactions.empty and "category" not in self.transactions.columns:
            self.transactions["category"] = self.transactions.apply(
                lambda r: categorize_merchant(
                    r.get("merchant_id"), r.get("transaction_description")
                ),
                axis=1,
            )

    # ── Backward-compatible API (v1) ──────────────────────────────────────────

    def analyze_behavior(self, customer_id: str) -> Dict[str, Any]:
        """
        Phase 2: Behaviour understanding (backward-compatible v1 interface).
        Returns same keys as v1 plus additional rolling window data.
        """
        cust_tx = self._get_customer_tx(customer_id)

        if cust_tx.empty:
            return {
                "total_spend": 0,
                "category_spend": {},
                "category_tx_counts": {},
                "monthly_income": {},
                "monthly_spend": {},
            }

        debits = cust_tx[cust_tx["transaction_type"] == "Debit"]
        credits = cust_tx[cust_tx["transaction_type"] == "Credit"]

        # Category spend and counts
        category_spend = debits.groupby("category")["amount"].sum().to_dict()
        category_tx_counts = debits.groupby("category").size().to_dict()
        total_spend = float(debits["amount"].sum())

        # Monthly income from salary credits
        salary_credits = credits[credits["category"] == "Salary"].copy()
        salary_credits["ym"] = salary_credits["transaction_date"].dt.to_period("M")
        monthly_income = {
            str(k): float(v)
            for k, v in salary_credits.groupby("ym")["amount"].sum().items()
        }

        # Monthly spend breakdown
        debits_copy = debits.copy()
        debits_copy["ym"] = debits_copy["transaction_date"].dt.to_period("M")
        monthly_spend = {
            str(k): float(v)
            for k, v in debits_copy.groupby("ym")["amount"].sum().items()
        }

        # Rolling window summaries (30 and 90 day)
        ref_date = cust_tx["transaction_date"].max()
        window_data = {}
        for days in [30, 60, 90]:
            cutoff = ref_date - timedelta(days=days)
            w_tx = debits[debits["transaction_date"] >= cutoff]
            window_data[f"spend_{days}d"] = float(w_tx["amount"].sum())
            window_data[f"count_{days}d"] = len(w_tx)
            cat_breakdown = w_tx.groupby("category")["amount"].sum().to_dict()
            window_data[f"categories_{days}d"] = cat_breakdown

        return {
            "total_spend": total_spend,
            "category_spend": {k: float(v) for k, v in category_spend.items()},
            "category_tx_counts": category_tx_counts,
            "monthly_income": monthly_income,
            "monthly_spend": monthly_spend,
            "windows": window_data,
        }

    def detect_events(self, customer_id: str) -> List[str]:
        """
        Phase 3: Event detection (backward-compatible v1 interface).
        Returns list of event strings (simplified from v2 event objects).
        """
        cust_tx = self._get_customer_tx(customer_id)
        if cust_tx.empty:
            return []

        from event_engine import EventEngine
        from feature_engine import FeatureEngine

        try:
            # Create a minimal feature set for the event engine
            fe = FeatureEngine(self.transactions)
            # We can't call compute() without customer_data, so use a stub
            features = CustomerFeatureSet(customer_id=customer_id)
            features.has_transactions = True

            event_engine = EventEngine(self.transactions)
            events_v2 = event_engine.detect_events(customer_id, features)

            # Convert v2 event objects to v1 strings for backward compat
            event_strings = []
            for e in events_v2:
                etype = e.get("event_type", "")
                if e.get("confidence", 0) >= 0.55:
                    event_strings.append(etype.replace("_", " ").title())

            return list(set(event_strings))

        except Exception as exc:
            logger.warning("BehaviorEngine.detect_events fallback: %s", exc)
            return self._detect_events_simple(cust_tx)

    # ── Extended v2 API ────────────────────────────────────────────────────────

    def analyze_behavior_v2(
        self, customer_id: str, features: CustomerFeatureSet
    ) -> Dict[str, Any]:
        """
        Full v2 behavioral profile using CustomerFeatureSet.
        Returns richer data than v1.
        """
        cust_tx = self._get_customer_tx(customer_id)

        if cust_tx.empty:
            return self._empty_profile()

        debits = cust_tx[cust_tx["transaction_type"] == "Debit"]
        ref_date = cust_tx["transaction_date"].max()

        # Basic spend metrics
        total_spend = float(debits["amount"].sum())
        category_spend = {k: float(v) for k, v in debits.groupby("category")["amount"].sum().items()}

        # Payment behavior
        payment_profile = self._analyze_payment_behavior(cust_tx)

        # Time behavior
        time_profile = self._analyze_time_behavior(debits)

        # Top merchants
        top_merchants = self._get_top_merchants(debits)

        # Spending velocity (transactions per week in last 30d)
        last_30_debits = debits[debits["transaction_date"] >= ref_date - timedelta(days=30)]
        tx_velocity = len(last_30_debits) / 4.0  # per week

        return {
            "total_spend": total_spend,
            "category_spend": category_spend,
            "category_tx_counts": {k: int(v) for k, v in debits.groupby("category").size().items()},
            "payment_profile": payment_profile,
            "time_profile": time_profile,
            "top_merchants": top_merchants,
            "transaction_velocity_per_week": round(tx_velocity, 1),
            "windows": {  # Include window data from features
                days: {
                    "total_spend": features.windows.get(days, None).__dict__
                    if features.windows.get(days) else {}
                }
                for days in WINDOW_DAYS
            },
        }

    # ── Behavioral sub-analyzers ───────────────────────────────────────────────

    def _analyze_payment_behavior(self, cust_tx: pd.DataFrame) -> Dict[str, Any]:
        """Categorize transactions by payment channel."""
        if "transaction_description" not in cust_tx.columns:
            return {"digital_ratio": 0.75}

        desc_upper = cust_tx["transaction_description"].str.upper().fillna("")

        upi_count = int(desc_upper.str.contains("UPI").sum())
        atm_count = int(desc_upper.str.contains("ATM|CASH").sum())
        neft_count = int(desc_upper.str.contains("NEFT").sum())
        imps_count = int(desc_upper.str.contains("IMPS").sum())
        total = max(len(cust_tx), 1)

        return {
            "upi_ratio": round(upi_count / total, 3),
            "atm_ratio": round(atm_count / total, 3),
            "neft_ratio": round(neft_count / total, 3),
            "imps_ratio": round(imps_count / total, 3),
            "digital_ratio": round(1 - atm_count / total, 3),
        }

    def _analyze_time_behavior(self, debits: pd.DataFrame) -> Dict[str, Any]:
        """Analyze transaction timing patterns."""
        if debits.empty:
            return {}

        # Weekday vs weekend
        weekday_count = int((debits["transaction_date"].dt.dayofweek < 5).sum())
        weekend_count = int((debits["transaction_date"].dt.dayofweek >= 5).sum())
        total = max(len(debits), 1)

        # Month-end spending (last 5 days of month)
        month_end = debits[debits["transaction_date"].dt.day >= 26]
        month_end_pct = len(month_end) / total

        return {
            "weekday_pct": round(weekday_count / total, 3),
            "weekend_pct": round(weekend_count / total, 3),
            "month_end_spending_pct": round(month_end_pct, 3),
        }

    def _get_top_merchants(self, debits: pd.DataFrame, n: int = 5) -> List[Dict]:
        """Return top N merchants by spend."""
        if debits.empty or "merchant_id" not in debits.columns:
            return []

        top = (
            debits.dropna(subset=["merchant_id"])
            .groupby("merchant_id")["amount"]
            .agg(["sum", "count"])
            .sort_values("sum", ascending=False)
            .head(n)
        )

        return [
            {
                "merchant_id": mid,
                "total_spend": round(float(row["sum"]), 2),
                "transaction_count": int(row["count"]),
            }
            for mid, row in top.iterrows()
            if mid and not pd.isna(mid)
        ]

    # ── Simple fallback event detection (v1 logic, used as fallback) ──────────

    def _detect_events_simple(self, cust_tx: pd.DataFrame) -> List[str]:
        """Simple v1-style event detection as fallback."""
        events = set()
        if cust_tx.empty:
            return []

        max_date = cust_tx["transaction_date"].max()
        recent_threshold = max_date - timedelta(days=30)
        recent_tx = cust_tx[cust_tx["transaction_date"] >= recent_threshold]

        for _, tx in recent_tx.iterrows():
            cat = categorize_merchant(tx.get("merchant_id"), tx.get("transaction_description"))
            if cat == "Travel":
                events.add("Travel Purchase")
            if cat == "Medical" and tx.get("amount", 0) > 5000:
                events.add("Healthcare Spending")
            if tx.get("transaction_type") == "Debit" and tx.get("amount", 0) > 20000:
                events.add("Large Purchase")

        return list(events)

    # ── Utilities ─────────────────────────────────────────────────────────────

    def _get_customer_tx(self, customer_id: str) -> pd.DataFrame:
        if self.transactions.empty:
            return pd.DataFrame()
        cust_tx = self.transactions[
            self.transactions["customer_id"] == customer_id
        ].copy()
        if not cust_tx.empty and "transaction_date" in cust_tx.columns:
            cust_tx["transaction_date"] = pd.to_datetime(
                cust_tx["transaction_date"], errors="coerce"
            )
            cust_tx = cust_tx.dropna(subset=["transaction_date"])
        return cust_tx

    def _empty_profile(self) -> Dict:
        return {
            "total_spend": 0,
            "category_spend": {},
            "category_tx_counts": {},
            "payment_profile": {},
            "time_profile": {},
            "top_merchants": [],
            "transaction_velocity_per_week": 0,
            "windows": {},
        }
