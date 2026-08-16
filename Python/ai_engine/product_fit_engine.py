"""
Product Fit Engine
==================
Banking-Grade Customer Intelligence — NPN Bank AI Pipeline v2.0

Scores how well each eligible product fits the specific customer's
behavioral profile, financial gaps, and detected events.

Design principles:
  - Fit is computed from actual customer behavior and product tags
  - LLM never participates in fit scoring
  - Works across credit cards, loans, and investment products
  - Returns matched/unmatched features for explainability
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import pandas as pd

from ai_engine.feature_engine import CustomerFeatureSet

logger = logging.getLogger(__name__)

# ── Behavior → product tag mapping ───────────────────────────────────────────
# Maps customer behavioral signals to product tags that would benefit them

BEHAVIOR_TAG_MAP: Dict[str, List[str]] = {
    # If customer has high travel spend → look for travel-tagged products
    "Travel": ["tag_travel", "tag_travel_card", "tag_international", "tag_lounge", "tag_airport_lounge"],
    "Investment": ["tag_investment", "tag_sip", "tag_mutual_fund", "tag_wealth"],
    "Insurance": ["tag_insurance", "tag_health", "tag_health_insurance", "tag_life_insurance"],
    "Dining": ["tag_cashback", "tag_dining", "tag_rewards"],
    "Shopping": ["tag_cashback", "tag_shopping", "tag_rewards", "tag_ecommerce", "tag_online_shopping"],
    "Fuel": ["tag_fuel", "tag_cashback"],
    "Medical": ["tag_health_insurance", "tag_medical", "tag_insurance"],
    "Groceries": ["tag_cashback", "tag_grocery"],
    "Rent": ["tag_home_loan", "tag_home"],
    "Education": ["tag_education_loan", "tag_education"],
    "EMI": ["tag_personal"],
}

# ── Event type → product tag mapping ─────────────────────────────────────────
EVENT_TAG_MAP: Dict[str, List[str]] = {
    "FREQUENT_TRAVEL": ["tag_travel", "tag_international", "tag_lounge", "tag_airport_lounge"],
    "HIGH_VALUE_TRAVEL_PURCHASE": ["tag_travel", "tag_premium"],
    "TRAVEL_SPEND_INCREASING": ["tag_travel"],
    "NO_INVESTMENT_ACTIVITY": ["tag_investment", "tag_sip", "tag_mutual_fund", "tag_nps"],
    "INVESTMENT_ACTIVITY_GROWING": ["tag_investment", "tag_sip", "tag_growth"],
    "INVESTMENT_ACTIVITY_LAPSED": ["tag_investment", "tag_sip"],
    "NO_INSURANCE_SIGNAL": ["tag_insurance", "tag_health_insurance", "tag_life_insurance"],
    "ELEVATED_HEALTHCARE_SPEND_PATTERN": ["tag_health_insurance", "tag_medical"],
    "SALARY_INCREASE_DETECTED": ["tag_investment", "tag_wealth", "tag_sip", "tag_life_insurance"],
    "HIGH_SURPLUS": ["tag_investment", "tag_fd", "tag_sip"],
    "ECOMMERCE_SPEND_INCREASING": ["tag_cashback", "tag_shopping", "tag_online_shopping"],
    "DINING_SPEND_INCREASING": ["tag_cashback", "tag_dining"],
}

# ── Financial gap → product tag mapping ──────────────────────────────────────
GAP_TAG_MAP: Dict[str, List[str]] = {
    "NO_INVESTMENT": ["tag_investment", "tag_sip", "tag_mutual_fund"],
    "LOW_INVESTMENT": ["tag_investment", "tag_sip"],
    "GROWING_INCOME_NO_INVESTMENT": ["tag_investment", "tag_sip"],
    "LOW_SAVINGS": ["tag_fd", "tag_investment"],
    "CRITICAL_SAVINGS": ["tag_fd"],
    "NO_INSURANCE": ["tag_insurance", "tag_health_insurance", "tag_life_insurance"],
    "NO_HEALTH_INSURANCE": ["tag_health_insurance", "tag_insurance"],
    "NO_LIFE_INSURANCE": ["tag_life_insurance", "tag_insurance"],
    "HIGH_MEDICAL_NO_INSURANCE": ["tag_health_insurance", "tag_insurance", "tag_medical"],
    "TRAVELLER_NO_CARD": ["tag_travel", "tag_international", "tag_airport_lounge"],
    "OVERSPENDING_DINING": ["tag_cashback", "tag_dining"],
    "OVERSPENDING_SHOPPING": ["tag_cashback", "tag_shopping", "tag_online_shopping"],
    "HIGH_RENT_BURDEN": ["tag_home_loan", "tag_home"],
    "OVER_LEVERAGED": [],
    "HIGH_OUTSTANDING_DEBT": [],
}


class ProductFitEngine:
    """
    Scores each eligible product against the customer's behavioral profile.

    Usage:
        engine = ProductFitEngine()
        scores = engine.score_all(eligible_products, features, events, gaps)
    """

    # ── Public API ─────────────────────────────────────────────────────────────

    def score_all(
        self,
        eligible_products: List[Dict[str, Any]],
        features: CustomerFeatureSet,
        events: List[Dict],
        financial_gaps: List[Dict],
    ) -> List[Dict[str, Any]]:
        """
        Score all eligible products and return them sorted by fit score descending.
        """
        scored: List[Dict] = []

        # Precompute customer's behavioral tag set
        customer_tags = self._build_customer_tags(features, events, financial_gaps)

        for product_result in eligible_products:
            try:
                fit_result = self._score_product(
                    product_result, customer_tags, features, events, financial_gaps
                )
                scored.append(fit_result)
            except Exception as exc:
                logger.warning(
                    "ProductFitEngine: could not score %s: %s",
                    product_result.get("product_name", "unknown"), exc
                )
                # Still include with 0 score
                scored.append({
                    **product_result,
                    "fit_score": 0.0,
                    "matched_features": [],
                    "unmatched_features": [],
                    "fit_evidence": [],
                })

        return sorted(scored, key=lambda x: x.get("fit_score", 0), reverse=True)

    # ── Customer behavioral tag building ──────────────────────────────────────

    def _build_customer_tags(
        self,
        features: CustomerFeatureSet,
        events: List[Dict],
        financial_gaps: List[Dict],
    ) -> Dict[str, float]:
        """
        Build a weighted tag relevance map for the customer.
        Returns {tag: relevance_score} where relevance is 0–1.
        """
        tag_scores: Dict[str, float] = {}

        w90 = features.windows.get(90)
        total_spend_90 = w90.total_spend if w90 else 0

        # From behavioral category spend (90-day window)
        if w90 and total_spend_90 > 0:
            for category, amount in w90.category_spend.items():
                pct = amount / total_spend_90
                if pct < 0.02:
                    continue  # Ignore trivial categories
                for tag in BEHAVIOR_TAG_MAP.get(category, []):
                    tag_scores[tag] = max(tag_scores.get(tag, 0), min(1.0, pct * 4))

        # From events (weighted by confidence * severity_score)
        for event in events:
            weight = event.get("confidence", 0.5) * event.get("severity_score", 0.5)
            for tag in EVENT_TAG_MAP.get(event.get("event_type", ""), []):
                tag_scores[tag] = min(1.0, tag_scores.get(tag, 0) + weight * 0.5)

        # From financial gaps (severity-weighted)
        for gap in financial_gaps:
            severity = gap.get("severity", 5) / 10.0
            for tag in GAP_TAG_MAP.get(gap.get("code", ""), []):
                tag_scores[tag] = min(1.0, tag_scores.get(tag, 0) + severity * 0.4)

        return tag_scores

    # ── Individual product scoring ────────────────────────────────────────────

    def _score_product(
        self,
        product_result: Dict[str, Any],
        customer_tags: Dict[str, float],
        features: CustomerFeatureSet,
        events: List[Dict],
        financial_gaps: List[Dict],
    ) -> Dict[str, Any]:
        """Score one eligible product against the customer's tag profile."""
        product_data = product_result.get("product_data", {})
        product_type = product_result.get("product_type", "unknown")

        # Get all tags that are set to 1 in this product
        product_tags = [
            k for k, v in product_data.items()
            if k.startswith("tag_") and v == 1
        ]

        matched: List[str] = []
        unmatched: List[str] = []
        fit_score = 0.0

        if customer_tags and product_tags:
            # For each product tag, check if customer has a relevance signal
            for tag in product_tags:
                relevance = customer_tags.get(tag, 0)
                if relevance > 0.10:
                    matched.append(tag)
                    fit_score += relevance
                else:
                    unmatched.append(tag)

            # Normalize by number of product tags
            if product_tags:
                fit_score = min(1.0, fit_score / len(product_tags))

        # Build human-readable evidence
        evidence = self._build_fit_evidence(
            matched, product_result, features, events, financial_gaps
        )

        return {
            **product_result,
            "fit_score": round(fit_score, 3),
            "matched_features": matched,
            "unmatched_features": unmatched,
            "fit_evidence": evidence,
        }

    def _build_fit_evidence(
        self,
        matched_tags: List[str],
        product_result: Dict,
        features: CustomerFeatureSet,
        events: List[Dict],
        financial_gaps: List[Dict],
    ) -> List[str]:
        """Generate human-readable evidence for why this product fits."""
        evidence: List[str] = []
        product_name = product_result.get("product_name", "this product")

        w90 = features.windows.get(90)

        # Travel evidence
        if "tag_travel" in matched_tags and w90:
            travel_spend = w90.category_spend.get("Travel", 0)
            if travel_spend > 0:
                evidence.append(
                    f"Customer spent ₹{travel_spend:,.0f} on travel in the last 90 days"
                )

        # Investment evidence
        if "tag_investment" in matched_tags or "tag_sip" in matched_tags:
            surplus = features.estimated_monthly_surplus
            if surplus > 1000:
                evidence.append(
                    f"Customer has estimated monthly surplus of ₹{surplus:,.0f} available for investment"
                )

        # Insurance evidence
        if "tag_insurance" in matched_tags or "tag_health_insurance" in matched_tags or "tag_life_insurance" in matched_tags:
            if not features.has_insurance:
                evidence.append("Customer has no active insurance policies — coverage gap detected")
            elif not features.has_health_insurance:
                evidence.append("Customer has other insurance but no health coverage")
            elif not features.has_life_insurance:
                evidence.append("Customer has other insurance but no life/term coverage")
            if w90:
                med_spend = w90.category_spend.get("Medical", 0)
                if med_spend > 5000:
                    evidence.append(f"Customer spent ₹{med_spend:,.0f} on medical in last 90 days")

        # Cashback evidence
        if "tag_cashback" in matched_tags and w90:
            dining = w90.category_spend.get("Dining", 0)
            shopping = w90.category_spend.get("Shopping", 0)
            if dining + shopping > 0:
                evidence.append(
                    f"Customer spent ₹{dining+shopping:,.0f} on dining+shopping in 90 days "
                    f"(cashback opportunity)"
                )

        # Event-driven evidence
        for event in events[:2]:
            if event.get("confidence", 0) > 0.60:
                for ev_evidence in event.get("evidence", [])[:1]:
                    evidence.append(ev_evidence)

        # Gap-driven evidence
        for gap in financial_gaps[:2]:
            if gap.get("severity", 0) >= 6:
                evidence.append(f"Financial gap: {gap.get('title', '')}")

        return evidence[:5]  # Limit to 5 evidence points
