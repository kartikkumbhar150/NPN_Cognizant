"""
Explainability Engine
=====================
Banking-Grade Customer Intelligence — NPN Bank AI Pipeline v2.0

Builds fully auditable, structured explanations from pipeline evidence.

Design principles:
  - LLM NEVER generates explanations — only language packaging
  - Every reason must trace back to actual feature values
  - Explanations are structured (not free-form text) so they can be audited
  - Customer-facing messages avoid "creepy" specificity (no raw account numbers)
  - Internal audit trail retains full evidence chain
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from feature_engine import CustomerFeatureSet

logger = logging.getLogger(__name__)


class ExplainabilityEngine:
    """
    Builds structured explanations for NBO decisions.

    Usage:
        engine = ExplainabilityEngine()
        explanation = engine.explain(nbo_candidate, features, events, gaps)
    """

    # ── Public API ─────────────────────────────────────────────────────────────

    def explain(
        self,
        nbo_candidate: Dict[str, Any],
        features: CustomerFeatureSet,
        events: List[Dict[str, Any]],
        financial_gaps: List[Dict[str, Any]],
        customer_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate a structured explanation for the selected NBO.

        Returns:
          - headline: one-line summary
          - reasons: list of human-readable reasons (internal)
          - customer_reasons: customer-facing reasons (less specific)
          - evidence: list of data points with sources
          - audit_trail: full evidence chain for model governance
        """
        product_name = nbo_candidate.get("product_name", "this product")
        product_type = nbo_candidate.get("product_type", "")

        reasons: List[str] = []
        customer_reasons: List[str] = []
        evidence: List[Dict] = []

        # ── Build reasons from financial gaps ─────────────────────────────────
        for gap in financial_gaps[:3]:
            if gap.get("severity", 0) >= 5:
                reasons.append(f"[Gap: {gap.get('code')}] {gap.get('title', '')}")
                # Customer-facing: softer language
                customer_reasons.append(
                    self._gap_to_customer_reason(gap, product_name)
                )
                evidence.append({
                    "type": "financial_gap",
                    "code": gap.get("code"),
                    "severity": gap.get("severity"),
                    "source": "financial_analyst",
                })

        # ── Build reasons from behavioral events ──────────────────────────────
        for event in events[:3]:
            if event.get("confidence", 0) >= 0.55:
                for ev_text in event.get("evidence", [])[:1]:
                    reasons.append(f"[Event: {event.get('event_type')}] {ev_text}")
                customer_reasons.append(
                    self._event_to_customer_reason(event, product_name)
                )
                evidence.append({
                    "type": "behavioral_event",
                    "event_type": event.get("event_type"),
                    "confidence": event.get("confidence"),
                    "window_days": event.get("window_days"),
                    "source": "event_engine",
                })

        # ── Build reasons from spending patterns ───────────────────────────────
        w90 = features.windows.get(90)
        if w90 and w90.total_spend > 0:
            top_categories = sorted(
                w90.category_spend.items(), key=lambda x: x[1], reverse=True
            )[:3]
            for cat, amount in top_categories:
                if amount / w90.total_spend > 0.15:  # > 15% of spend
                    reasons.append(
                        f"[Spend] {cat} accounts for "
                        f"{amount/w90.total_spend*100:.0f}% of 90-day spend "
                        f"(₹{amount:,.0f})"
                    )
                    evidence.append({
                        "type": "spending_pattern",
                        "category": cat,
                        "amount_90d": round(amount, 2),
                        "pct_of_spend": round(amount / w90.total_spend, 3),
                        "source": "feature_engine",
                    })

        # ── Eligibility confirmation ───────────────────────────────────────────
        passed_rules = nbo_candidate.get("passed_rules", [])
        if passed_rules:
            reasons.append(
                f"[Eligibility] Customer satisfies all product eligibility criteria"
            )
            evidence.append({
                "type": "eligibility",
                "passed_rules": passed_rules[:3],
                "source": "eligibility_engine",
            })

        # ── Fit score evidence ─────────────────────────────────────────────────
        fit_score = nbo_candidate.get("fit_score", 0)
        matched_features = nbo_candidate.get("matched_features", [])
        if matched_features:
            reasons.append(
                f"[Fit] Product features match customer profile "
                f"(fit score: {fit_score:.2f}, matched tags: {', '.join(matched_features[:4])})"
            )
            evidence.append({
                "type": "product_fit",
                "fit_score": fit_score,
                "matched_tags": matched_features,
                "source": "product_fit_engine",
            })

        # ── Generate headline ─────────────────────────────────────────────────
        headline = self._generate_headline(
            product_name, events, financial_gaps, features
        )

        # ── Ensure minimum reasons ────────────────────────────────────────────
        if not customer_reasons:
            customer_reasons = [
                f"Based on your account activity, {product_name} may align well with your current financial needs."
            ]

        return {
            "headline": headline,
            "reasons": reasons[:6],
            "customer_reasons": customer_reasons[:4],
            "evidence": evidence,
            "audit_trail": {
                "customer_id": features.customer_id,
                "product_id": nbo_candidate.get("product_id"),
                "product_name": product_name,
                "feature_version": features.feature_version,
                "computed_at": features.computed_at,
                "gap_codes": [g.get("code") for g in financial_gaps],
                "event_types": [e.get("event_type") for e in events],
                "nbo_score": nbo_candidate.get("nbo_score", 0),
                "propensity_score": nbo_candidate.get("propensity_score", 0),
                "fit_score": fit_score,
            },
        }

    # ── Helper: gap → customer reason ────────────────────────────────────────

    def _gap_to_customer_reason(self, gap: Dict, product_name: str) -> str:
        """Convert a financial gap into a customer-appropriate reason."""
        code = gap.get("code", "")
        mapping = {
            "NO_INVESTMENT": f"You may benefit from a systematic way to grow your savings.",
            "GROWING_INCOME_NO_INVESTMENT": f"With your growing income, this could be a good time to start building wealth.",
            "LOW_SAVINGS": f"This product could help you build a stronger savings habit.",
            "CRITICAL_SAVINGS": f"A structured savings plan could give you greater financial security.",
            "NO_INSURANCE": f"Protecting yourself against unexpected expenses is an important financial step.",
            "HIGH_MEDICAL_NO_INSURANCE": f"A health cover could help manage future healthcare-related costs.",
            "TRAVELLER_NO_CARD": f"If you travel frequently, you may get more value from a travel-focused product.",
            "OVERSPENDING_DINING": f"You could earn rewards on your regular dining & food spending.",
            "OVERSPENDING_SHOPPING": f"Your shopping activity may qualify you for cashback benefits.",
            "HIGH_RENT_BURDEN": f"Owning a home could potentially reduce your monthly housing cost.",
        }
        return mapping.get(code, f"Based on your spending patterns, {product_name} may be a relevant option.")

    # ── Helper: event → customer reason ──────────────────────────────────────

    def _event_to_customer_reason(self, event: Dict, product_name: str) -> str:
        """Convert an event into a customer-appropriate, non-creepy reason."""
        etype = event.get("event_type", "")
        mapping = {
            "FREQUENT_TRAVEL": "If travel is a regular part of your life, a travel-focused product may offer useful benefits.",
            "HIGH_VALUE_TRAVEL_PURCHASE": "For customers who plan significant travel, relevant products can add meaningful value.",
            "TRAVEL_SPEND_INCREASING": "Your recent travel activity suggests you may benefit from travel-oriented features.",
            "NO_INVESTMENT_ACTIVITY": "Setting aside a portion of savings into a growth-oriented product is a common financial milestone.",
            "NO_INSURANCE_SIGNAL": "Financial protection products help manage unexpected costs.",
            "ELEVATED_HEALTHCARE_SPEND_PATTERN": "A health cover product may help manage future healthcare-related expenses.",
            "SALARY_INCREASE_DETECTED": "With improving income, this could be a good time to consider additional financial planning.",
            "ECOMMERCE_SPEND_INCREASING": "Your recent online purchases may qualify for cashback or reward benefits.",
            "DINING_SPEND_INCREASING": "Regular dining and food orders could earn you cashback through the right card.",
            "EMI_PAYMENT_DETECTED": "Managing your regular financial commitments effectively is a smart financial strategy.",
        }
        return mapping.get(
            etype,
            f"Based on your recent account activity, {product_name} may be worth exploring."
        )

    # ── Headline generator ────────────────────────────────────────────────────

    def _generate_headline(
        self,
        product_name: str,
        events: List[Dict],
        gaps: List[Dict],
        features: CustomerFeatureSet,
    ) -> str:
        """Generate a concise, non-creepy headline for the recommendation."""
        # Priority: strongest event or gap
        if events:
            best_event = max(events, key=lambda e: e.get("confidence", 0) * e.get("severity_score", 0))
            etype = best_event.get("event_type", "")
            headlines = {
                "FREQUENT_TRAVEL": f"Explore travel benefits with {product_name}",
                "NO_INVESTMENT_ACTIVITY": f"A potential opportunity to grow your savings",
                "NO_INSURANCE_SIGNAL": f"Protect your finances with a suitable coverage plan",
                "ELEVATED_HEALTHCARE_SPEND_PATTERN": f"A health cover that may suit your needs",
                "SALARY_INCREASE_DETECTED": f"Make your growing income work harder",
            }
            if etype in headlines:
                return headlines[etype]

        if gaps:
            top_gap = gaps[0]
            gap_headlines = {
                "TRAVELLER_NO_CARD": f"Travel smarter with {product_name}",
                "NO_INVESTMENT": f"Start growing your wealth today",
                "NO_INSURANCE": f"Protect what matters most",
                "OVERSPENDING_DINING": f"Earn rewards on your everyday spending",
            }
            headline = gap_headlines.get(top_gap.get("code", ""))
            if headline:
                return headline

        return f"A personalised recommendation for you: {product_name}"
