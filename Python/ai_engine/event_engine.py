"""
Event Engine
============
Banking-Grade Customer Intelligence — NPN Bank AI Pipeline v2.0

Dedicated event detection module. Uses RELATIVE thresholds based on
each customer's own behavioral baseline, not fixed absolute rupee amounts.

Design principles:
  - A ₹2,000 flight is NOT the same signal for a ₹20,000/month earner
    and a ₹2,00,000/month earner.
  - Every event carries: type, confidence, severity, evidence, and window.
  - Never makes medical diagnoses. Only describes transaction patterns.
  - Never crashes on missing data.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pandas as pd

from ai_engine.feature_engine import CustomerFeatureSet, categorize_merchant

logger = logging.getLogger(__name__)

TRAVEL_MERCHANTS = {"MER00", "MER08"}  # Airlines, Hotels
MEDICAL_MERCHANTS = {"MER13"}
INVESTMENT_MERCHANTS = {"MER15", "MER16"}
INSURANCE_MERCHANTS = {"MER17"}
FUEL_MERCHANTS = {"MER10"}
EDUCATION_MERCHANTS = {"MER14"}
ENTERTAINMENT_MERCHANTS = {"MER09"}
ECOMMERCE_MERCHANTS = {"MER02", "MER03"}


def _merchant_prefix(merchant_id: Optional[str]) -> Optional[str]:
    if not merchant_id or pd.isna(merchant_id):
        return None
    s = str(merchant_id).strip()
    return s[:5] if len(s) >= 5 else s


class EventEngine:
    """
    Detects behavioral events from a CustomerFeatureSet and raw transactions.

    Events are relative to the customer's own baseline — not universal thresholds.
    Each event dict contains:
      event_type, detected_at, window_days, confidence, severity,
      evidence (list of descriptive strings), supporting_transaction_ids (list)
    """

    def __init__(self, transactions_df: pd.DataFrame) -> None:
        self.transactions = transactions_df

    # ── Public API ─────────────────────────────────────────────────────────────

    def detect_events(
        self, customer_id: str, features: CustomerFeatureSet
    ) -> List[Dict[str, Any]]:
        """
        Run all event detectors and return a merged, deduplicated list.
        Never raises — returns empty list on error.
        """
        events: List[Dict] = []
        try:
            cust_tx = self.transactions[
                self.transactions["customer_id"] == customer_id
            ].copy()

            if cust_tx.empty:
                return []

            # Ensure category column exists
            if "category" not in cust_tx.columns:
                cust_tx["category"] = cust_tx.apply(
                    lambda r: categorize_merchant(
                        r.get("merchant_id"), r.get("transaction_description")
                    ),
                    axis=1,
                )

            ref_date = cust_tx["transaction_date"].max()

            # Compute customer-specific baselines
            baseline = self._compute_baselines(cust_tx)

            # Run all detectors
            events += self._detect_travel_events(cust_tx, features, baseline, ref_date)
            events += self._detect_investment_events(cust_tx, features, baseline, ref_date)
            events += self._detect_insurance_events(cust_tx, features, baseline, ref_date)
            events += self._detect_large_purchase_events(cust_tx, baseline, ref_date)
            events += self._detect_income_change_events(cust_tx, features, ref_date)
            events += self._detect_medical_pattern_events(cust_tx, features, baseline, ref_date)
            events += self._detect_education_events(cust_tx, ref_date)
            events += self._detect_lifestyle_events(cust_tx, features, baseline, ref_date)
            events += self._detect_emi_signals(cust_tx, features, ref_date)
            events += self._detect_salary_events(cust_tx, ref_date)

            # Sort by confidence * severity descending
            events.sort(
                key=lambda e: e.get("confidence", 0) * e.get("severity_score", 1),
                reverse=True,
            )

        except Exception as exc:
            logger.error(
                "EventEngine.detect_events error for %s: %s", customer_id, exc, exc_info=True
            )

        return events

    # ── Baseline computation ───────────────────────────────────────────────────

    def _compute_baselines(self, cust_tx: pd.DataFrame) -> Dict[str, float]:
        """Compute customer-specific spending baselines for anomaly detection."""
        debits = cust_tx[cust_tx["transaction_type"] == "Debit"]
        if debits.empty:
            return {}

        amounts = debits["amount"].dropna()
        return {
            "mean_transaction": float(amounts.mean()),
            "median_transaction": float(amounts.median()),
            "p75_transaction": float(amounts.quantile(0.75)),
            "p90_transaction": float(amounts.quantile(0.90)),
            "p95_transaction": float(amounts.quantile(0.95)),
            "total_spend": float(amounts.sum()),
            "monthly_avg_spend": float(amounts.sum() / max(cust_tx["transaction_date"].dt.to_period("M").nunique(), 1)),
        }

    # ── Travel events ──────────────────────────────────────────────────────────

    def _detect_travel_events(
        self, cust_tx: pd.DataFrame, features: CustomerFeatureSet,
        baseline: Dict, ref_date: pd.Timestamp
    ) -> List[Dict]:
        events = []
        debits = cust_tx[cust_tx["transaction_type"] == "Debit"]
        travel_tx = debits[debits["category"] == "Travel"]

        if travel_tx.empty:
            return events

        # Window analysis: recent 60 days
        recent_cutoff = ref_date - timedelta(days=60)
        recent_travel = travel_tx[travel_tx["transaction_date"] >= recent_cutoff]
        recent_count = len(recent_travel)
        recent_spend = float(recent_travel["amount"].sum())

        # Compare to customer baseline
        p75 = baseline.get("p75_transaction", 5000)
        high_value_travel = recent_travel[recent_travel["amount"] >= max(p75, 1000)]

        if recent_count >= 2:
            confidence = min(0.95, 0.40 + (recent_count * 0.10))
            severity = "high" if recent_count >= 4 else "medium"
            severity_score = 0.8 if recent_count >= 4 else 0.5
            events.append({
                "event_type": "FREQUENT_TRAVEL",
                "detected_at": str(ref_date.date()),
                "window_days": 60,
                "confidence": round(confidence, 2),
                "severity": severity,
                "severity_score": severity_score,
                "evidence": [
                    f"{recent_count} travel transactions in the last 60 days",
                    f"Total travel spend: ₹{recent_spend:,.0f} in 60 days",
                ],
                "supporting_transactions": list(
                    recent_travel.index[:5] if hasattr(recent_travel.index, '__iter__') else []
                ),
            })

        # Single high-value travel event (relative to customer baseline)
        if not high_value_travel.empty:
            max_travel = float(high_value_travel["amount"].max())
            if max_travel >= p75:
                confidence = min(0.90, 0.50 + (max_travel / (baseline.get("p90_transaction", 10000) + 1)) * 0.2)
                events.append({
                    "event_type": "HIGH_VALUE_TRAVEL_PURCHASE",
                    "detected_at": str(ref_date.date()),
                    "window_days": 60,
                    "confidence": round(min(0.90, confidence), 2),
                    "severity": "medium",
                    "severity_score": 0.6,
                    "evidence": [
                        f"Travel transaction of ₹{max_travel:,.0f} (above customer's 75th percentile)",
                    ],
                    "supporting_transactions": [],
                })

        # Trend-based: travel spending growing
        travel_trend = features.trends.get("Travel", {})
        if travel_trend.get("direction") == "up" and travel_trend.get("change_percent", 0) > 20:
            events.append({
                "event_type": "TRAVEL_SPEND_INCREASING",
                "detected_at": str(ref_date.date()),
                "window_days": 30,
                "confidence": round(travel_trend.get("confidence", 0.4), 2),
                "severity": "medium",
                "severity_score": 0.5,
                "evidence": [
                    f"Travel spending increased {travel_trend['change_percent']:.0f}% vs previous 30 days",
                ],
                "supporting_transactions": [],
            })

        return events

    # ── Investment events ──────────────────────────────────────────────────────

    def _detect_investment_events(
        self, cust_tx: pd.DataFrame, features: CustomerFeatureSet,
        baseline: Dict, ref_date: pd.Timestamp
    ) -> List[Dict]:
        events = []
        debits = cust_tx[cust_tx["transaction_type"] == "Debit"]
        invest_tx = debits[debits["category"] == "Investment"]

        recent_90 = invest_tx[
            invest_tx["transaction_date"] >= ref_date - timedelta(days=90)
        ]

        if invest_tx.empty:
            # No investment activity at all → strong gap signal
            # Only flag if income is above threshold
            monthly_income = features.monthly_income_avg
            if monthly_income > 30000:  # ₹30K+/month
                events.append({
                    "event_type": "NO_INVESTMENT_ACTIVITY",
                    "detected_at": str(ref_date.date()),
                    "window_days": 365,
                    "confidence": 0.85,
                    "severity": "high",
                    "severity_score": 0.9,
                    "evidence": [
                        "Zero investment transactions detected across entire history",
                        f"Monthly income estimated at ₹{monthly_income:,.0f}",
                    ],
                    "supporting_transactions": [],
                })
        elif not recent_90.empty:
            # Active investor — detect growing investment
            invest_trend = features.trends.get("Investment", {})
            if invest_trend.get("direction") == "up":
                events.append({
                    "event_type": "INVESTMENT_ACTIVITY_GROWING",
                    "detected_at": str(ref_date.date()),
                    "window_days": 90,
                    "confidence": round(invest_trend.get("confidence", 0.5), 2),
                    "severity": "low",
                    "severity_score": 0.3,
                    "evidence": [
                        f"Investment spending increased {invest_trend.get('change_percent', 0):.0f}% recently",
                    ],
                    "supporting_transactions": [],
                })
        elif invest_tx.empty or (not recent_90.empty) is False:
            # Had investments but stopped recently
            events.append({
                "event_type": "INVESTMENT_ACTIVITY_LAPSED",
                "detected_at": str(ref_date.date()),
                "window_days": 90,
                "confidence": 0.70,
                "severity": "medium",
                "severity_score": 0.55,
                "evidence": [
                    "Prior investment activity detected, but none in the last 90 days",
                ],
                "supporting_transactions": [],
            })

        return events

    # ── Insurance events ───────────────────────────────────────────────────────

    def _detect_insurance_events(
        self, cust_tx: pd.DataFrame, features: CustomerFeatureSet,
        baseline: Dict, ref_date: pd.Timestamp
    ) -> List[Dict]:
        events = []
        debits = cust_tx[cust_tx["transaction_type"] == "Debit"]
        insurance_tx = debits[debits["category"] == "Insurance"]

        if insurance_tx.empty:
            confidence = 0.80 if features.monthly_income_avg > 25000 else 0.60
            events.append({
                "event_type": "NO_INSURANCE_SIGNAL",
                "detected_at": str(ref_date.date()),
                "window_days": 365,
                "confidence": confidence,
                "severity": "high",
                "severity_score": 0.85,
                "evidence": [
                    "No insurance premium transactions detected in transaction history",
                ],
                "supporting_transactions": [],
            })

        return events

    # ── Large purchase events ──────────────────────────────────────────────────

    def _detect_large_purchase_events(
        self, cust_tx: pd.DataFrame, baseline: Dict, ref_date: pd.Timestamp
    ) -> List[Dict]:
        events = []
        if not baseline:
            return events

        p90 = baseline.get("p90_transaction", 20000)
        abs_min = 15000

        debits = cust_tx[cust_tx["transaction_type"] == "Debit"]
        recent_cutoff = ref_date - timedelta(days=60)
        recent_debits = debits[debits["transaction_date"] >= recent_cutoff]

        large = recent_debits[
            (recent_debits["amount"] >= p90) & (recent_debits["amount"] >= abs_min)
        ]

        for _, tx in large.iterrows():
            amount = float(tx["amount"])
            category = tx.get("category", "Other")
            confidence = min(0.85, 0.50 + amount / (p90 * 5))
            events.append({
                "event_type": "LARGE_PURCHASE",
                "detected_at": str(tx["transaction_date"].date()),
                "window_days": 60,
                "confidence": round(confidence, 2),
                "severity": "medium",
                "severity_score": 0.6,
                "evidence": [
                    f"Transaction of ₹{amount:,.0f} — above customer's 90th percentile (₹{p90:,.0f})",
                    f"Category: {category}",
                ],
                "supporting_transactions": [],
            })
            # Avoid too many large purchase events
            if len(events) >= 3:
                break

        return events

    # ── Income change events ───────────────────────────────────────────────────

    def _detect_income_change_events(
        self, cust_tx: pd.DataFrame, features: CustomerFeatureSet,
        ref_date: pd.Timestamp
    ) -> List[Dict]:
        events = []

        if features.income_trend == "up" and features.income_growth_rate > 0.10:
            events.append({
                "event_type": "SALARY_INCREASE_DETECTED",
                "detected_at": str(ref_date.date()),
                "window_days": 90,
                "confidence": round(features.income_stability, 2),
                "severity": "medium",
                "severity_score": 0.55,
                "evidence": [
                    f"Monthly income grew {features.income_growth_rate*100:.1f}% over recent months",
                ],
                "supporting_transactions": [],
            })
        elif features.income_trend == "down" and abs(features.income_growth_rate) > 0.10:
            events.append({
                "event_type": "SALARY_DECREASE_DETECTED",
                "detected_at": str(ref_date.date()),
                "window_days": 90,
                "confidence": round(features.income_stability, 2),
                "severity": "medium",
                "severity_score": 0.5,
                "evidence": [
                    f"Monthly income declined {abs(features.income_growth_rate)*100:.1f}% over recent months",
                ],
                "supporting_transactions": [],
            })

        # Regular salary detection
        salary_tx = cust_tx[
            (cust_tx["transaction_type"] == "Credit")
            & (cust_tx["category"] == "Salary")
        ]
        recent_salary = salary_tx[
            salary_tx["transaction_date"] >= ref_date - timedelta(days=180)
        ]
        if len(recent_salary) >= 3:
            events.append({
                "event_type": "REGULAR_SALARY_CREDIT",
                "detected_at": str(ref_date.date()),
                "window_days": 180,
                "confidence": round(min(0.95, len(recent_salary) / 6), 2),
                "severity": "low",
                "severity_score": 0.2,
                "evidence": [
                    f"{len(recent_salary)} salary credits in the last 6 months",
                ],
                "supporting_transactions": [],
            })

        return events

    # ── Medical pattern events ─────────────────────────────────────────────────

    def _detect_medical_pattern_events(
        self, cust_tx: pd.DataFrame, features: CustomerFeatureSet,
        baseline: Dict, ref_date: pd.Timestamp
    ) -> List[Dict]:
        """
        Detect elevated healthcare spending patterns.
        IMPORTANT: Does NOT make medical diagnoses.
        Only describes transaction patterns.
        """
        events = []
        debits = cust_tx[cust_tx["transaction_type"] == "Debit"]
        medical_tx = debits[debits["category"] == "Medical"]

        if medical_tx.empty:
            return events

        recent_180 = medical_tx[
            medical_tx["transaction_date"] >= ref_date - timedelta(days=180)
        ]
        medical_spend_180 = float(recent_180["amount"].sum())
        p75 = baseline.get("p75_transaction", 5000)

        if medical_spend_180 > p75 * 4:  # Relatively high medical spend
            events.append({
                "event_type": "ELEVATED_HEALTHCARE_SPEND_PATTERN",
                "detected_at": str(ref_date.date()),
                "window_days": 180,
                "confidence": 0.75,
                "severity": "medium",
                "severity_score": 0.65,
                "evidence": [
                    f"Healthcare-related spending of ₹{medical_spend_180:,.0f} in the last 180 days",
                    "Note: This describes transaction patterns only — not a medical assessment.",
                ],
                "supporting_transactions": [],
            })

        return events

    # ── Education events ───────────────────────────────────────────────────────

    def _detect_education_events(
        self, cust_tx: pd.DataFrame, ref_date: pd.Timestamp
    ) -> List[Dict]:
        events = []
        debits = cust_tx[cust_tx["transaction_type"] == "Debit"]
        edu_tx = debits[debits["category"] == "Education"]

        if edu_tx.empty:
            return events

        recent_edu = edu_tx[
            edu_tx["transaction_date"] >= ref_date - timedelta(days=180)
        ]
        if len(recent_edu) >= 2:
            edu_spend = float(recent_edu["amount"].sum())
            events.append({
                "event_type": "RECURRING_EDUCATION_SPEND",
                "detected_at": str(ref_date.date()),
                "window_days": 180,
                "confidence": 0.70,
                "severity": "low",
                "severity_score": 0.3,
                "evidence": [
                    f"{len(recent_edu)} education-related transactions totalling ₹{edu_spend:,.0f} in 180 days",
                ],
                "supporting_transactions": [],
            })

        return events

    # ── Lifestyle events ───────────────────────────────────────────────────────

    def _detect_lifestyle_events(
        self, cust_tx: pd.DataFrame, features: CustomerFeatureSet,
        baseline: Dict, ref_date: pd.Timestamp
    ) -> List[Dict]:
        events = []

        # Increasing dining
        dining_trend = features.trends.get("Dining", {})
        if dining_trend.get("direction") == "up" and dining_trend.get("change_percent", 0) > 30:
            events.append({
                "event_type": "DINING_SPEND_INCREASING",
                "detected_at": str(ref_date.date()),
                "window_days": 30,
                "confidence": round(dining_trend.get("confidence", 0.4), 2),
                "severity": "low",
                "severity_score": 0.3,
                "evidence": [
                    f"Dining & food delivery spending up {dining_trend['change_percent']:.0f}% vs previous 30 days",
                ],
                "supporting_transactions": [],
            })

        # Increasing e-commerce
        shopping_trend = features.trends.get("Shopping", {})
        if shopping_trend.get("direction") == "up" and shopping_trend.get("change_percent", 0) > 30:
            events.append({
                "event_type": "ECOMMERCE_SPEND_INCREASING",
                "detected_at": str(ref_date.date()),
                "window_days": 30,
                "confidence": round(shopping_trend.get("confidence", 0.4), 2),
                "severity": "low",
                "severity_score": 0.3,
                "evidence": [
                    f"Shopping & e-commerce spending up {shopping_trend['change_percent']:.0f}% vs previous 30 days",
                ],
                "supporting_transactions": [],
            })

        return events

    # ── EMI signals ────────────────────────────────────────────────────────────

    def _detect_emi_signals(
        self, cust_tx: pd.DataFrame, features: CustomerFeatureSet,
        ref_date: pd.Timestamp
    ) -> List[Dict]:
        events = []

        # Look for recurring equal-amount debits — EMI pattern
        for payment in features.recurring_payments:
            if payment.get("frequency") == "monthly" and payment.get("consistency_score", 0) > 0.80:
                category = payment.get("category", "Other")
                if category in ("EMI", "Other", "Transfer"):
                    amount = payment.get("average_amount", 0)
                    if amount > 2000:  # Minimum EMI floor
                        events.append({
                            "event_type": "EMI_PAYMENT_DETECTED",
                            "detected_at": str(ref_date.date()),
                            "window_days": 180,
                            "confidence": round(payment["consistency_score"], 2),
                            "severity": "low",
                            "severity_score": 0.25,
                            "evidence": [
                                f"Recurring monthly payment of ₹{amount:,.0f} detected",
                                f"Consistency score: {payment['consistency_score']:.2f}",
                            ],
                            "supporting_transactions": [],
                        })

        return events

    # ── Salary events ──────────────────────────────────────────────────────────

    def _detect_salary_events(
        self, cust_tx: pd.DataFrame, ref_date: pd.Timestamp
    ) -> List[Dict]:
        return []  # Handled by income change events
