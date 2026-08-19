"""
Next Best Offer (NBO) Engine (v3.0)
====================================
Banking-Grade Customer Intelligence — NPN Bank AI Pipeline v3.0

Upgrades from v2:
  - get_all_propensity_scores(): returns ranked propensity for ALL banking services
  - CC Upgrade logic: customers with a card are NOT suppressed — they get an upgrade offer
  - Cluster-aware score boosting via ClusteringEngine
  - Comprehensive edge case handling (null credit score, zero income, lapsed insurance, etc.)
  - Low-confidence flag for customers with no transaction data
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import yaml
import os
import math

from ai_engine.feature_engine import CustomerFeatureSet
from ai_engine.eligibility_engine import EligibilityEngine
from ai_engine.product_fit_engine import ProductFitEngine

logger = logging.getLogger(__name__)

# Load config
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config", "nbo_weights.yaml")
try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        CONFIG = yaml.safe_load(f)
except Exception as e:
    logger.error(f"Could not load nbo_weights.yaml: {e}")
    CONFIG = {}

WEIGHTS = CONFIG.get("weights", {
    "propensity": 0.30,
    "product_fit": 0.25,
    "event_relevance": 0.20,
    "customer_need": 0.10,
    "recency": 0.10,
    "relationship_value": 0.05
})

PRODUCT_PRIORITY = CONFIG.get("product_priority", {})

# ── All banking service categories for propensity scoring ─────────────────────
ALL_SERVICE_CATEGORIES = [
    "Travel Credit Card",
    "Rewards Credit Card",
    "Cashback Credit Card",
    "Premium Credit Card",
    "Credit Card Upgrade",
    "Personal Loan",
    "Home Loan",
    "Auto Loan",
    "Education Loan",
    "Gold Loan",
    "Business Loan",
    "Term Life Insurance",
    "Health Insurance",
    "Motor Insurance",
    "Travel Insurance",
    "SIP / Mutual Fund",
    "Fixed Deposit",
    "NPS / Pension",
    "Premium Account",
    "Salary Account",
]


def _safe_float(val: Any, default: float = 0.0) -> float:
    try:
        v = float(val)
        return default if (math.isnan(v) or math.isinf(v)) else v
    except (TypeError, ValueError):
        return default


class NBOEngine:
    """
    Determines the Next Best Offer by orchestrating eligibility, fit, and propensity.
    v3.0: full service scoring + CC upgrade logic + cluster boosting.
    """

    def __init__(
        self,
        credit_cards: pd.DataFrame,
        loans: pd.DataFrame,
        investments: pd.DataFrame = None,
        insurance: pd.DataFrame = None,
    ):
        self.eligibility_engine = EligibilityEngine(credit_cards, loans, investments, insurance)
        self.fit_engine = ProductFitEngine()
        self.credit_cards = credit_cards if credit_cards is not None else pd.DataFrame()
        self.loans = loans if loans is not None else pd.DataFrame()
        self.investments = investments if investments is not None else pd.DataFrame()
        self.insurance = insurance if insurance is not None else pd.DataFrame()

    # ── Primary API ────────────────────────────────────────────────────────────

    def determine_next_best_offer(
        self,
        features: CustomerFeatureSet,
        events: List[Dict],
        financial_gaps: List[Dict],
        customer_data: Dict,
    ) -> Dict[str, Any]:
        """End-to-end NBO determination — returns the single best offer."""
        all_scores = self.get_all_propensity_scores(features, events, financial_gaps, customer_data)

        if not all_scores:
            return self._empty_nbo()

        best = all_scores[0]
        return {
            "category": best.get("product_type", "Unknown"),
            "specific_product": best.get("product_name"),
            "propensity": f"{int(best.get('nbo_score', 0) * 100)}%",
            "reasons": best.get("fit_evidence", ["High overall fit score."]),
            "gap_code": financial_gaps[0]["code"] if financial_gaps else None,
            "full_result": best,
            "product_id": best.get("product_id"),
            "is_upgrade": best.get("is_upgrade", False),
            "all_propensity_scores": all_scores,
            "low_confidence": not features.has_transactions,
        }

    def get_all_propensity_scores(
        self,
        features: CustomerFeatureSet,
        events: List[Dict],
        financial_gaps: List[Dict],
        customer_data: Dict,
    ) -> List[Dict[str, Any]]:
        """
        Returns a ranked list of ALL banking services with propensity scores.
        Handles CC upgrade logic: customers with a card get upgrade offers instead of being suppressed.
        """
        # 1. Get eligible products
        try:
            eligible_products = self.eligibility_engine.get_eligible(features, customer_data)
        except Exception as exc:
            logger.error("EligibilityEngine error: %s", exc)
            eligible_products = []

        # 2. Separate new vs upgrade CC opportunities
        new_products = []
        upgrade_products = []

        for p in eligible_products:
            p_type = p.get("product_type", "").lower()
            p_data = p.get("product_data", {})

            if p_type == "credit_card":
                if features.has_credit_card:
                    # Check if this is a higher-tier card
                    if self._is_higher_tier_card(p_data, features):
                        p["is_upgrade"] = True
                        p["product_type"] = "credit_card_upgrade"
                        upgrade_products.append(p)
                    # else: same or lower tier — skip
                else:
                    p["is_upgrade"] = False
                    new_products.append(p)
            else:
                # Apply standard suppression for non-CC products
                if not self._should_suppress(p_type, p_data, features):
                    p["is_upgrade"] = False
                    new_products.append(p)

        all_candidates = new_products + upgrade_products

        if not all_candidates:
            return []

        # 3. Product fit scoring
        try:
            fit_scored = self.fit_engine.score_all(all_candidates, features, events, financial_gaps)
        except Exception as exc:
            logger.error("ProductFitEngine error: %s", exc)
            fit_scored = [{**p, "fit_score": 0.3, "fit_evidence": [], "matched_features": []} for p in all_candidates]

        # 4. Final ranking with cluster boosts
        ranked = self._rank_offers(fit_scored, features, events, financial_gaps, customer_data)

        # 5. Build service-level summary for UI (all 20 service categories)
        return ranked

    # ── Internal Ranking ───────────────────────────────────────────────────────

    def _rank_offers(
        self,
        fit_scored_products: List[Dict],
        features: CustomerFeatureSet,
        events: List[Dict],
        financial_gaps: List[Dict],
        customer_data: Dict,
    ) -> List[Dict]:
        """Rank products using weighted ensemble + cluster boost."""
        max_severity = max([g.get("severity", 0) for g in financial_gaps], default=0)
        monthly_income = _safe_float(features.monthly_income_avg)
        ranked = []

        # Get cluster boost map
        cluster_boost = {}
        if hasattr(features, "cluster_label") and features.cluster_label != "Standard":
            from ai_engine.clustering_engine import CLUSTER_PERSONAS
            for cid, persona in CLUSTER_PERSONAS.items():
                if persona["label"] == features.cluster_label:
                    cluster_boost = persona.get("nbo_boost", {})
                    break

        for product in fit_scored_products:
            fit_score = _safe_float(product.get("fit_score", 0))
            propensity = fit_score * 0.8 + 0.1

            # Low confidence penalty for customers with no transactions
            if not features.has_transactions:
                propensity *= 0.5

            # Event relevance
            event_relevance = 0.0
            for event in events:
                if len(product.get("matched_features", [])) > 0:
                    ev_conf = _safe_float(event.get("confidence", 0))
                    ev_sev = _safe_float(event.get("severity_score", 0))
                    event_relevance = max(event_relevance, ev_conf * ev_sev)

            # Customer need (gap severity)
            customer_need = 0.0
            if max_severity > 0 and len(product.get("matched_features", [])) > 0:
                customer_need = max_severity / 10.0

            # Recency boost
            recency_score = 0.8 if events else 0.5

            # Relationship value (income-based)
            relationship_val = min(1.0, (monthly_income * 12) / 2_000_000.0) if monthly_income > 0 else 0.1

            # Upgrade bonus
            upgrade_bonus = 0.05 if product.get("is_upgrade") else 0.0

            # Compute base score
            nbo_score = (
                propensity         * WEIGHTS.get("propensity", 0.30) +
                fit_score          * WEIGHTS.get("product_fit", 0.25) +
                event_relevance    * WEIGHTS.get("event_relevance", 0.20) +
                customer_need      * WEIGHTS.get("customer_need", 0.10) +
                recency_score      * WEIGHTS.get("recency", 0.10) +
                relationship_val   * WEIGHTS.get("relationship_value", 0.05) +
                upgrade_bonus
            )

            # Product priority boost from config
            p_type = product.get("product_type", "")
            priority_map = {
                "credit_card": "Credit Card",
                "credit_card_upgrade": "Credit Card",
                "loan": "Personal Loan",
                "investment": "Investment/SIP",
            }
            mapped_cat = priority_map.get(p_type)
            nbo_score += PRODUCT_PRIORITY.get(mapped_cat, 0)

            # Cluster-based boost
            product_name = str(product.get("product_name", ""))
            for boost_key, boost_val in cluster_boost.items():
                if boost_key.lower() in product_name.lower():
                    nbo_score += boost_val
                    break

            ranked.append({
                **product,
                "propensity_score": round(min(1.0, max(0.0, propensity)), 3),
                "nbo_score": round(min(1.0, max(0.0, nbo_score)), 3),
                "propensity_pct": f"{int(min(1.0, max(0.0, nbo_score)) * 100)}%",
                "low_confidence": not features.has_transactions,
            })

        return sorted(ranked, key=lambda x: x["nbo_score"], reverse=True)

    # ── Suppression logic ──────────────────────────────────────────────────────

    def _should_suppress(self, p_type: str, p_data: Dict, features: CustomerFeatureSet) -> bool:
        """Return True if customer already holds this product (standard suppression)."""
        if p_type == "loan":
            cat = str(p_data.get("loan_category", "")).lower()
            if "personal" in cat and features.has_personal_loan: return True
            if "home" in cat and features.has_home_loan: return True
            if ("vehicle" in cat or "auto" in cat) and features.has_vehicle_loan: return True
            if "education" in cat and features.has_education_loan: return True
            if "business" in cat and features.has_business_loan: return True
            if "gold" in cat and features.has_gold_loan: return True

        elif p_type == "insurance":
            cat = str(p_data.get("insurance_type", "")).lower()
            # Check only ACTIVE insurance (lapsed counts as not held)
            if "life" in cat and features.has_life_insurance: return True
            if "health" in cat and features.has_health_insurance: return True
            if ("motor" in cat or "vehicle" in cat or "car" in cat) and features.has_motor_insurance: return True
            if "home" in cat and features.has_home_insurance: return True
            if "travel" in cat and features.has_travel_insurance: return True

        elif p_type == "investment":
            cat = str(p_data.get("investment_type", "")).lower()
            if "mutual fund" in cat and features.has_mutual_fund: return True
            if ("stock" in cat or "equity" in cat) and features.has_stocks: return True
            if "bond" in cat and features.has_bonds: return True
            if "nps" in cat and features.has_nps: return True
            if "etf" in cat and features.has_etf: return True
            if "sip" in cat and features.has_sip: return True

        return False

    def _is_higher_tier_card(self, p_data: Dict, features: CustomerFeatureSet) -> bool:
        """
        Check if p_data represents a higher-tier card than what the customer currently holds.
        Compares by annual_fee as a proxy for tier.
        """
        try:
            candidate_fee = _safe_float(p_data.get("annual_fee", 0))
            # Get the max annual fee of currently held cards
            held_cards = features.holdings.get("credit_cards", [])
            if not held_cards:
                return True  # No specific card info — offer upgrade
            max_held_fee = max(
                (_safe_float(c.get("annual_fee", 0)) for c in held_cards),
                default=0.0,
            )
            return candidate_fee > max_held_fee
        except Exception:
            return True  # Default to offering upgrade

    # ── Fallback ───────────────────────────────────────────────────────────────

    def _empty_nbo(self) -> Dict:
        return {
            "category": "Standard Account",
            "specific_product": "Standard Savings Account",
            "propensity": "10%",
            "reasons": ["No specific eligible product found."],
            "gap_code": None,
            "full_result": {},
            "product_id": None,
            "is_upgrade": False,
            "all_propensity_scores": [],
            "low_confidence": True,
        }

    # ── Backward Compatibility (v1/v2) ─────────────────────────────────────────

    def calculate_propensity(self, customer_data, segments, events, financial_gaps=None):
        """Deprecated: Kept only for API backward compatibility."""
        propensities = {
            "Travel Card": 10, "Investment/SIP": 10, "Personal Loan": 5,
            "Health Insurance": 5, "FD": 10, "Home Loan": 5, "Cashback Card": 5
        }
        if financial_gaps:
            for gap in financial_gaps:
                boost = gap["severity"] * 8
                for product_cat in gap.get("products", []):
                    propensities[product_cat] = min(99, propensities.get(product_cat, 0) + boost)
        return dict(sorted(propensities.items(), key=lambda item: item[1], reverse=True))
