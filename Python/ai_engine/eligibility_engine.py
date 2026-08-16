"""
Eligibility Engine
==================
Banking-Grade Customer Intelligence — NPN Bank AI Pipeline v2.0

Hard eligibility gate. A product MUST pass all eligibility rules
before it can enter the NBO candidate set.

Design principles:
  - Eligibility is a HARD CONSTRAINT — propensity never overrides it
  - Works with credit cards, loans, AND investment products
  - Returns detailed pass/fail evidence for auditability
  - Never crashes — returns ineligible on error with explanation
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import pandas as pd

from ai_engine.feature_engine import CustomerFeatureSet

logger = logging.getLogger(__name__)


class EligibilityEngine:
    """
    Checks every product in the combined catalogue against customer criteria.

    Usage:
        engine = EligibilityEngine(credit_cards_df, loans_df, investment_df)
        results = engine.evaluate_all(features, customer_data)
        eligible = [r for r in results if r["eligible"]]
    """

    def __init__(
        self,
        credit_cards_df: pd.DataFrame,
        loans_df: pd.DataFrame,
        investments_df: Optional[pd.DataFrame] = None,
        insurance_df: Optional[pd.DataFrame] = None,
    ) -> None:
        self.credit_cards = credit_cards_df if credit_cards_df is not None else pd.DataFrame()
        self.loans = loans_df if loans_df is not None else pd.DataFrame()
        self.investments = investments_df if investments_df is not None else pd.DataFrame()
        self.insurance = insurance_df if insurance_df is not None else pd.DataFrame()

    # ── Public API ─────────────────────────────────────────────────────────────

    def evaluate_all(
        self, features: CustomerFeatureSet, customer_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Evaluate eligibility for all products in the catalogue.
        Returns list of eligibility results including ineligible ones.
        """
        results: List[Dict] = []

        try:
            # Credit cards
            for _, product in self.credit_cards.iterrows():
                result = self._evaluate_credit_card(product, features, customer_data)
                results.append(result)

            # Loans
            for _, product in self.loans.iterrows():
                result = self._evaluate_loan(product, features, customer_data)
                results.append(result)

            # Investment products
            for _, product in self.investments.iterrows():
                result = self._evaluate_investment(product, features, customer_data)
                results.append(result)

            # Insurance products
            for _, product in self.insurance.iterrows():
                result = self._evaluate_insurance(product, features, customer_data)
                results.append(result)

        except Exception as exc:
            logger.error("EligibilityEngine.evaluate_all error: %s", exc, exc_info=True)

        return results

    def get_eligible(
        self, features: CustomerFeatureSet, customer_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Return only eligible products."""
        return [r for r in self.evaluate_all(features, customer_data) if r["eligible"]]

    # ── Credit card eligibility ───────────────────────────────────────────────

    def _evaluate_credit_card(
        self,
        product: pd.Series,
        features: CustomerFeatureSet,
        customer_data: Dict,
    ) -> Dict[str, Any]:
        """Evaluate credit card eligibility rules."""
        passed: List[str] = []
        failed: List[str] = []
        score = 1.0

        age = features.profile.get("age", 0)
        annual_income = features.profile.get("annual_income", 0) or (
            features.monthly_income_avg * 12
        )
        credit_score = features.profile.get("credit_score", 0)
        product_status = str(product.get("product_status", "Active")).strip()
        product_name = str(product.get("card_name", product.get("product_name", "Unknown")))

        # Rule 1: Product must be active
        if product_status != "Active":
            failed.append(f"Product is not active (status: {product_status})")

        # Anti-Duplication Gate: Check if user already holds this card
        held_cards = features.holdings.get("credit_cards", [])
        for card in held_cards:
            if card.get("card_name") == product_name or card.get("credit_card_product_id") == product.get("card_id"):
                failed.append(f"Customer already holds this credit card ({product_name})")
                score = 0.0

        # Rule 2: Age
        min_age = self._safe_int(product.get("minimum_age"), 18)
        max_age = self._safe_int(product.get("maximum_age"), 70)
        if age < min_age:
            failed.append(f"Customer age {age} < minimum age {min_age}")
            score -= 0.5
        elif age > max_age:
            failed.append(f"Customer age {age} > maximum age {max_age}")
            score -= 0.5
        else:
            passed.append(f"Age {age} within range [{min_age}–{max_age}]")

        # Rule 3: Income
        min_income = self._safe_float(product.get("minimum_income_annual"), 0)
        if annual_income < min_income:
            failed.append(
                f"Annual income ₹{annual_income:,.0f} < required ₹{min_income:,.0f}"
            )
            score -= 0.4
        else:
            passed.append(f"Income ₹{annual_income:,.0f} meets requirement ₹{min_income:,.0f}")

        # Rule 4: Credit score (if specified in product)
        min_credit_score = self._safe_int(product.get("minimum_credit_score"), 0)
        if min_credit_score > 0 and credit_score < min_credit_score:
            failed.append(
                f"Credit score {credit_score} < required {min_credit_score}"
            )
            score -= 0.4
        else:
            passed.append(f"Credit score {credit_score} acceptable")

        eligible = len(failed) == 0
        return {
            "product_id": str(product.get("card_id", product.get("product_id", ""))),
            "product_name": product_name,
            "product_type": "credit_card",
            "eligible": eligible,
            "eligibility_score": round(max(0.0, score), 2),
            "passed_rules": passed,
            "failed_rules": failed,
            "product_data": product.to_dict(),
        }

    # ── Loan eligibility ──────────────────────────────────────────────────────

    def _evaluate_loan(
        self,
        product: pd.Series,
        features: CustomerFeatureSet,
        customer_data: Dict,
    ) -> Dict[str, Any]:
        """Evaluate loan product eligibility."""
        passed: List[str] = []
        failed: List[str] = []
        score = 1.0

        age = features.profile.get("age", 0)
        annual_income = features.profile.get("annual_income", 0) or (
            features.monthly_income_avg * 12
        )
        credit_score = features.profile.get("credit_score", 0)
        product_name = str(product.get("product_name", "Loan Product"))

        # Anti-Duplication Gate: Check if user already holds this loan type
        # For loans, we check category (e.g. Home, Personal) instead of exact product name
        # since holding one home loan generally means we shouldn't recommend another immediately.
        loan_category = str(product.get("loan_category", "")).lower()
        held_loans = features.holdings.get("loans", [])
        for loan in held_loans:
            if loan_category in str(loan.get("loan_category", "")).lower():
                failed.append(f"Customer already has an active {product.get('loan_category')} loan")
                score = 0.0

        # Rule 1: Age
        min_age = self._safe_int(product.get("minimum_age"), 21)
        max_age = self._safe_int(product.get("maximum_age"), 65)
        if age < min_age:
            failed.append(f"Age {age} < minimum {min_age}")
            score -= 0.5
        elif age > max_age:
            failed.append(f"Age {age} > maximum {max_age}")
            score -= 0.5
        else:
            passed.append(f"Age {age} within [{min_age}–{max_age}]")

        # Rule 2: Income
        min_income = self._safe_float(product.get("minimum_income_annual"), 0)
        if annual_income < min_income:
            failed.append(f"Income ₹{annual_income:,.0f} < required ₹{min_income:,.0f}")
            score -= 0.4
        else:
            passed.append(f"Income ₹{annual_income:,.0f} meets requirement")

        # Rule 3: Credit score for loans
        min_credit = self._safe_int(product.get("minimum_credit_score"), 650)
        if credit_score < min_credit:
            failed.append(f"Credit score {credit_score} < required {min_credit}")
            score -= 0.5
        else:
            passed.append(f"Credit score {credit_score} ≥ {min_credit}")

        eligible = len(failed) == 0
        return {
            "product_id": str(product.get("loan_id", product.get("product_id", ""))),
            "product_name": product_name,
            "product_type": "loan",
            "eligible": eligible,
            "eligibility_score": round(max(0.0, score), 2),
            "passed_rules": passed,
            "failed_rules": failed,
            "product_data": product.to_dict(),
        }

    # ── Investment eligibility ─────────────────────────────────────────────────

    def _evaluate_investment(
        self,
        product: pd.Series,
        features: CustomerFeatureSet,
        customer_data: Dict,
    ) -> Dict[str, Any]:
        """Evaluate investment product eligibility."""
        passed: List[str] = []
        failed: List[str] = []
        score = 1.0

        age = features.profile.get("age", 0)
        annual_income = features.profile.get("annual_income", 0) or (
            features.monthly_income_avg * 12
        )
        product_status = str(product.get("product_status", "Active")).strip()
        product_name = str(product.get("product_name", "Investment Product"))

        # Rule 1: Active status
        if product_status != "Active":
            failed.append(f"Product not active (status: {product_status})")

        # Anti-Duplication Gate: Check if user already holds this investment product
        held_investments = features.holdings.get("investments", [])
        for inv in held_investments:
            if inv.get("investment_product_name") == product_name or inv.get("investment_product_id") == product.get("investment_product_id"):
                failed.append(f"Customer already holds this investment product ({product_name})")
                score = 0.0

        # Rule 2: Age
        min_age = self._safe_int(product.get("minimum_age"), 18)
        max_age = self._safe_int(product.get("maximum_age"), 75)
        if age < min_age:
            failed.append(f"Age {age} < minimum {min_age}")
            score -= 0.4
        elif age > max_age:
            failed.append(f"Age {age} > maximum {max_age}")
            score -= 0.3
        else:
            passed.append(f"Age {age} within [{min_age}–{max_age}]")

        # Rule 3: Income
        min_income = self._safe_float(product.get("minimum_income_annual"), 0)
        if min_income > 0 and annual_income < min_income:
            failed.append(f"Income ₹{annual_income:,.0f} < required ₹{min_income:,.0f}")
            score -= 0.4
        else:
            passed.append(f"Income requirement met (₹{annual_income:,.0f})")

        # Rule 4: Minimum investment check (if customer can meet it)
        min_invest = self._safe_float(product.get("minimum_investment"), 0)
        monthly_surplus = features.estimated_monthly_surplus
        if min_invest > 0 and monthly_surplus < min_invest * 0.5:
            # If surplus is less than half the minimum investment, flag it
            failed.append(
                f"Estimated surplus ₹{monthly_surplus:,.0f}/month may not sustain "
                f"min investment ₹{min_invest:,.0f}"
            )
            score -= 0.2

        eligible = len(failed) == 0
        return {
            "product_id": str(product.get("investment_product_id", product.get("product_id", ""))),
            "product_name": product_name,
            "product_type": "investment",
            "eligible": eligible,
            "eligibility_score": round(max(0.0, score), 2),
            "passed_rules": passed,
            "failed_rules": failed,
            "product_data": product.to_dict(),
        }

    # ── Insurance eligibility ──────────────────────────────────────────────────

    def _evaluate_insurance(
        self,
        product: pd.Series,
        features: CustomerFeatureSet,
        customer_data: Dict,
    ) -> Dict[str, Any]:
        """Evaluate insurance product eligibility."""
        passed: List[str] = []
        failed: List[str] = []
        score = 1.0

        age = features.profile.get("age", 0)
        annual_income = features.profile.get("annual_income", 0) or (features.monthly_income_avg * 12)
        product_status = str(product.get("product_status", "Active")).strip()
        product_name = str(product.get("product_name", "Insurance Product"))
        insurance_category = str(product.get("insurance_category", ""))
        minimum_premium = self._safe_float(product.get("minimum_premium"), 0)

        # Rule 1: Active status
        if product_status != "Active":
            failed.append(f"Product not active (status: {product_status})")

        # Anti-Duplication Gate: Check if user already holds this insurance category
        # Don't recommend Life insurance if they already have Life. But Health insurance
        # can still be recommended even if they have Life.
        held_ins_cats = features.held_insurance_categories
        if insurance_category and insurance_category in held_ins_cats:
            failed.append(f"Customer already holds {insurance_category} insurance")
            score = 0.0

        # Rule 2: Entry age gate
        min_entry_age = self._safe_int(product.get("minimum_entry_age"), 18)
        max_entry_age = self._safe_int(product.get("maximum_entry_age"), 70)
        if age < min_entry_age:
            failed.append(f"Age {age} < minimum entry age {min_entry_age}")
            score -= 0.5
        elif age > max_entry_age:
            failed.append(f"Age {age} > maximum entry age {max_entry_age}")
            score -= 0.5
        else:
            passed.append(f"Age {age} within entry range [{min_entry_age}–{max_entry_age}]")

        # Rule 3: Premium affordability (minimum premium must be < 10% of monthly income)
        monthly_income = features.monthly_income_avg or (annual_income / 12)
        monthly_premium_equiv = minimum_premium / 12.0
        if monthly_income > 0 and monthly_premium_equiv > monthly_income * 0.10:
            failed.append(
                f"Minimum premium ₹{minimum_premium:,.0f}/year may not be affordable "
                f"on income ₹{monthly_income:,.0f}/month"
            )
            score -= 0.3
        else:
            passed.append(f"Premium ₹{minimum_premium:,.0f}/year is affordable")

        eligible = len(failed) == 0
        return {
            "product_id": str(product.get("insurance_product_id", product.get("product_id", ""))),
            "product_name": product_name,
            "product_type": "insurance",
            "insurance_category": insurance_category,
            "eligible": eligible,
            "eligibility_score": round(max(0.0, score), 2),
            "passed_rules": passed,
            "failed_rules": failed,
            "product_data": product.to_dict(),
        }

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _safe_int(self, val: Any, default: int) -> int:
        try:
            v = int(val)
            return v if not pd.isna(v) else default
        except (TypeError, ValueError):
            return default

    def _safe_float(self, val: Any, default: float) -> float:
        try:
            v = float(val)
            return v if not pd.isna(v) else default
        except (TypeError, ValueError):
            return default
