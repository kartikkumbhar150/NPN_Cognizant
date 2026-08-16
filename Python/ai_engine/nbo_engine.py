"""
Next Best Offer (NBO) Engine (v2.0)
===================================
Banking-Grade Customer Intelligence — NPN Bank AI Pipeline v2.0

Upgrades from v1:
  - Uses EligibilityEngine to enforce hard constraints.
  - Uses ProductFitEngine to score behavioral relevance.
  - Replaces fake `propensity = severity * 8` with a weighted ensemble scorer.
  - Supports Credit Cards, Loans, and Investments from Supabase.
"""

import logging
from typing import Any, Dict, List
import pandas as pd
import yaml
import os

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

class NBOEngine:
    """
    Determines the Next Best Offer by orchestrating eligibility, fit, and propensity.
    """

    def __init__(self, credit_cards: pd.DataFrame, loans: pd.DataFrame, investments: pd.DataFrame = None, insurance: pd.DataFrame = None):
        self.eligibility_engine = EligibilityEngine(credit_cards, loans, investments, insurance)
        self.fit_engine = ProductFitEngine()
        
        # Keep v1 attributes for backward compatibility
        self.credit_cards = credit_cards
        self.loans = loans

    # ── Public API ─────────────────────────────────────────────────────────────

    def determine_next_best_offer(self, features: CustomerFeatureSet, events: List[Dict], financial_gaps: List[Dict], customer_data: Dict) -> Dict[str, Any]:
        """
        End-to-end NBO determination.
        """
        # 1. Hard Eligibility Gate
        eligible_products = self.eligibility_engine.get_eligible(features, customer_data)
        
        if not eligible_products:
            return self._empty_nbo()

        # 2. Product Fit Scoring (Behavioral Match)
        fit_scored_products = self.fit_engine.score_all(eligible_products, features, events, financial_gaps)

        # 3. Final Weighted Ranking
        ranked_offers = self._rank_offers(fit_scored_products, features, events, financial_gaps)

        if not ranked_offers:
            return self._empty_nbo()
            
        best_offer = ranked_offers[0]
        
        # Compatibility with v1 return format
        return {
            "category": best_offer.get("product_type", "Unknown"),
            "specific_product": best_offer.get("product_name"),
            "propensity": f"{int(best_offer.get('nbo_score', 0) * 100)}%",
            "reasons": best_offer.get("fit_evidence", ["High overall fit score."]),
            "gap_code": financial_gaps[0]["code"] if financial_gaps else None,
            # Pass all enriched data for ExplainabilityEngine
            "full_result": best_offer,
            "product_id": best_offer.get("product_id")
        }

    # ── Internal Ranking ───────────────────────────────────────────────────────

    def _rank_offers(self, fit_scored_products: List[Dict], features: CustomerFeatureSet, events: List[Dict], financial_gaps: List[Dict]) -> List[Dict]:
        """Rank products using the config-driven weighted ensemble."""
        ranked = []
        
        # Calculate max gap severity for normalization
        max_severity = max([g.get("severity", 0) for g in financial_gaps]) if financial_gaps else 0
        
        for product in fit_scored_products:
            fit_score = product.get("fit_score", 0)
            
            # Baseline Propensity (placeholder for a real ML model, currently uses fit as proxy)
            propensity = fit_score * 0.8 + 0.1
            
            # Event Relevance
            event_relevance = 0
            for event in events:
                # If product tag matches event tag (simplified check since fit_engine already did tag matching)
                if len(product.get("matched_features", [])) > 0:
                    event_relevance = max(event_relevance, event.get("confidence", 0) * event.get("severity_score", 0))
                    
            # Customer Need (Gap Severity)
            customer_need = 0
            if max_severity > 0 and len(product.get("matched_features", [])) > 0:
                customer_need = max_severity / 10.0
                
            # Recency
            recency_score = 0.5
            if events:
                # Recent event boost
                recency_score = 0.8
                
            # Relationship Value
            relationship_val = min(1.0, (features.monthly_income_avg * 12) / 2000000.0)
            
            # Compute Final Score
            nbo_score = (
                (propensity * WEIGHTS.get("propensity", 0.30)) +
                (fit_score * WEIGHTS.get("product_fit", 0.25)) +
                (event_relevance * WEIGHTS.get("event_relevance", 0.20)) +
                (customer_need * WEIGHTS.get("customer_need", 0.10)) +
                (recency_score * WEIGHTS.get("recency", 0.10)) +
                (relationship_val * WEIGHTS.get("relationship_value", 0.05))
            )
            
            # Add Product Priority Boost
            category_mapping = {
                "credit_card": "Credit Card",
                "loan": "Personal Loan",
                "investment": "Investment/SIP"
            }
            mapped_cat = category_mapping.get(product.get("product_type"))
            nbo_score += PRODUCT_PRIORITY.get(mapped_cat, 0)
            
            ranked.append({
                **product,
                "propensity_score": round(propensity, 3),
                "nbo_score": round(min(1.0, max(0.0, nbo_score)), 3)
            })
            
        return sorted(ranked, key=lambda x: x["nbo_score"], reverse=True)

    # ── Fallback ───────────────────────────────────────────────────────────────

    def _empty_nbo(self):
        return {
            "category": "Standard Account",
            "specific_product": "Standard Savings Account",
            "propensity": "10%",
            "reasons": ["No specific eligible product found."],
            "gap_code": None,
            "full_result": {},
            "product_id": None
        }

    # ── Backward Compatibility (v1) ────────────────────────────────────────────

    def calculate_propensity(self, customer_data, segments, events, financial_gaps=None):
        """Deprecated: Kept only for API backward compatibility if needed."""
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
