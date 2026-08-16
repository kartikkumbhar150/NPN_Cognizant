"""
Financial Analyst Engine (v2.0)
===============================
Banking-Grade Customer Intelligence — NPN Bank AI Pipeline v2.0

Upgrades from v1:
  - Uses FeatureEngine as the source of truth (no redundant calculations)
  - Loads dynamic benchmarks from thresholds.yaml
  - Replaces hardcoded strings with structured Gap objects
  - Tracks stability and confidence for gaps
"""

import logging
from typing import Any, Dict, List
import pandas as pd
import yaml
import os

from ai_engine.feature_engine import CustomerFeatureSet

logger = logging.getLogger(__name__)

# Load configuration
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config", "thresholds.yaml")
try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        CONFIG = yaml.safe_load(f)
except Exception as e:
    logger.error(f"Could not load thresholds.yaml: {e}")
    CONFIG = {}

# Fallback values if config is missing
BENCHMARKS = {
    "dining_pct_warn": CONFIG.get("spending", {}).get("dining_pct_warn", 0.12),
    "dining_pct_bad": CONFIG.get("spending", {}).get("dining_pct_bad", 0.18),
    "shopping_pct_warn": CONFIG.get("spending", {}).get("shopping_pct_warn", 0.15),
    "shopping_pct_bad": CONFIG.get("spending", {}).get("shopping_pct_bad", 0.22),
    "rent_pct_warn": CONFIG.get("spending", {}).get("rent_pct_warn", 0.30),
    "rent_pct_bad": CONFIG.get("spending", {}).get("rent_pct_bad", 0.40),
    "savings_rate_critical": CONFIG.get("savings", {}).get("critical", 0.08),
    "savings_rate_low": CONFIG.get("savings", {}).get("low", 0.20),
    "savings_rate_healthy": CONFIG.get("savings", {}).get("healthy", 0.30),
    "travel_pct_traveller": CONFIG.get("spending", {}).get("travel_pct_traveller", 0.12),
    "medical_high_abs": CONFIG.get("medical", {}).get("high_spend_absolute", 20000),
    "income_invest_thresh": CONFIG.get("investment", {}).get("income_threshold_annual", 600000),
    "min_invest_ratio": CONFIG.get("investment", {}).get("min_invest_ratio", 0.05),
}

class FinancialAnalyst:
    """
    Deep financial analysis engine (v2).
    Evaluates financial health, flags risks, and identifies gaps based on CustomerFeatureSet.
    """

    def __init__(self, transactions_df=None):
        pass # Transactions are now handled by FeatureEngine

    # ── Public API ─────────────────────────────────────────────────────────────

    def analyse(self, customer_id: str, customer_data: Dict[str, Any], features: CustomerFeatureSet) -> Dict[str, Any]:
        """
        Run full financial analysis. Returns dict with findings.
        Requires v2 CustomerFeatureSet.
        """
        gaps = self._detect_gaps(features)
        health_score = self._score_financial_health(features, gaps)

        return {
            "income_profile": self._extract_income_profile(features),
            "spending_profile": self._extract_spending_profile(features),
            "gaps": gaps,
            "health_score": health_score,
        }

    # ── Extractor Helpers ──────────────────────────────────────────────────────

    def _extract_income_profile(self, features: CustomerFeatureSet) -> Dict[str, Any]:
        return {
            "monthly_avg_income": features.monthly_income_avg,
            "annual_income_observed": features.monthly_income_avg * 12,
            "income_stability": features.income_stability,
            "income_trend": features.income_trend,
            "salary_growing": features.income_trend == "up",
        }

    def _extract_spending_profile(self, features: CustomerFeatureSet) -> Dict[str, Any]:
        w90 = features.windows.get(90)
        category_breakdown = {}
        if w90 and features.monthly_income_avg > 0:
            for cat, amount in w90.category_spend.items():
                category_breakdown[cat] = {
                    "monthly_avg": amount / 3.0,
                    "pct_of_income": (amount / 3.0) / features.monthly_income_avg
                }

        return {
            "monthly_total_spend": features.monthly_spend_avg_90d,
            "monthly_savings": features.estimated_monthly_surplus,
            "savings_rate": features.surplus_ratio,
            "spend_volatility": features.spend_volatility,
            "category_breakdown": category_breakdown,
        }

    # ── Gap Detector ───────────────────────────────────────────────────────────

    def _detect_gaps(self, features: CustomerFeatureSet) -> List[Dict[str, Any]]:
        gaps = []
        w180 = features.windows.get(180)
        
        annual_income = features.monthly_income_avg * 12
        monthly_income = features.monthly_income_avg
        savings_rate = features.surplus_ratio

        invest_spend_180 = w180.category_spend.get("Investment", 0) if w180 else 0
        insurance_spend_180 = w180.category_spend.get("Insurance", 0) if w180 else 0
        medical_spend_180 = w180.category_spend.get("Medical", 0) if w180 else 0

        # ── Clean boolean signals from holdings (v3.0) ───────────────────────────
        has_insurance      = features.has_insurance
        has_health_ins     = features.has_health_insurance
        has_life_ins       = features.has_life_insurance
        has_investments    = features.has_investments
        has_home_loan      = features.has_home_loan
        total_emi_monthly  = features.total_emi_monthly
        total_outstanding  = features.total_outstanding_debt
        foir               = (total_emi_monthly / monthly_income) if monthly_income > 0 else 0
        marital_status     = features.profile.get("marital_status", "Single")
        age                = features.profile.get("age", 30)
        
        # Calculate percentages of income based on 90d window
        w90 = features.windows.get(90)
        total_spend_90 = w90.total_spend if w90 else 0
        
        dining_pct = ((w90.category_spend.get("Dining", 0) / 3.0) / monthly_income) if (w90 and monthly_income > 0) else 0
        shopping_pct = ((w90.category_spend.get("Shopping", 0) / 3.0) / monthly_income) if (w90 and monthly_income > 0) else 0
        rent_pct = ((w90.category_spend.get("Rent", 0) / 3.0) / monthly_income) if (w90 and monthly_income > 0) else 0
        travel_pct = (w90.category_spend.get("Travel", 0) / total_spend_90) if (w90 and total_spend_90 > 0) else 0

        # GAP 1: No investments despite good income
        # If they have no investments, OR if they have investments but very low transaction activity
        if annual_income >= BENCHMARKS["income_invest_thresh"] and not has_investments:
            gaps.append({
                "code": "NO_INVESTMENT",
                "severity": 9,
                "title": "Zero Investment Portfolio",
                "insight": f"You earn ₹{monthly_income:,.0f}/month but have no active investments. Start investing now to beat inflation.",
                "products": ["Investment/SIP", "FD"]
            })
        elif annual_income >= BENCHMARKS["income_invest_thresh"] and has_investments and (invest_spend_180 / 6.0) < (monthly_income * BENCHMARKS["min_invest_ratio"]):
            gap_amount = (monthly_income * BENCHMARKS["min_invest_ratio"]) - (invest_spend_180 / 6.0)
            gaps.append({
                "code": "LOW_INVESTMENT",
                "severity": 7,
                "title": "Sub-Optimal Investment Activity",
                "insight": f"You are investing below the recommended {BENCHMARKS['min_invest_ratio']*100:.0f}% threshold. Consider topping up by ~₹{gap_amount:,.0f}/month.",
                "products": ["Investment/SIP", "FD"]
            })

        # GAP 2a: No insurance at all
        if not has_insurance and insurance_spend_180 == 0:
            gaps.append({
                "code": "NO_INSURANCE",
                "severity": 8,
                "title": "No Insurance Coverage Detected",
                "insight": "You have no active insurance policies, leaving you financially exposed to unexpected events.",
                "products": ["Health Insurance", "Term Insurance"]
            })

        # GAP 2b: Has insurance but no health insurance specifically
        elif has_insurance and not has_health_ins:
            gaps.append({
                "code": "NO_HEALTH_INSURANCE",
                "severity": 7,
                "title": "No Health Insurance Policy",
                "insight": "You have other insurance, but no health insurance. Medical emergencies can be financially devastating without it.",
                "products": ["Health Insurance"]
            })

        # GAP 2c: No life insurance for married customers
        if not has_life_ins and marital_status in ("Married",) and annual_income >= 600000:
            gaps.append({
                "code": "NO_LIFE_INSURANCE",
                "severity": 8,
                "title": "No Life Insurance — Dependents at Risk",
                "insight": "You are married with a good income but have no life or term insurance plan. Your dependents are financially exposed.",
                "products": ["Term Insurance", "Life Insurance"]
            })

        # GAP 3: Critical savings rate
        if savings_rate < BENCHMARKS["savings_rate_critical"]:
            gaps.append({
                "code": "CRITICAL_SAVINGS",
                "severity": 8,
                "title": "Critically Low Savings Rate",
                "insight": f"You are saving only {savings_rate*100:.1f}% of your monthly income. A healthy savings rate is 20-30%.",
                "products": ["FD", "Savings Account"]
            })
        elif savings_rate < BENCHMARKS["savings_rate_low"]:
            gaps.append({
                "code": "LOW_SAVINGS",
                "severity": 6,
                "title": "Below-Average Savings Rate",
                "insight": f"You are saving {savings_rate*100:.1f}% of your monthly income. You could be saving more.",
                "products": ["Investment/SIP", "FD"]
            })

        # GAP 4: Overspending on Dining
        if dining_pct >= BENCHMARKS["dining_pct_bad"]:
            gaps.append({
                "code": "OVERSPENDING_DINING",
                "severity": 5,
                "title": "High Dining & Food Spending",
                "insight": f"You spend {dining_pct*100:.1f}% of your income on dining. A rewards card could help.",
                "products": ["Cashback Card", "Dining Rewards Card"]
            })
        elif dining_pct >= BENCHMARKS["dining_pct_warn"]:
            gaps.append({
                "code": "HIGH_DINING",
                "severity": 4,
                "title": "Elevated Dining Spend",
                "insight": f"Dining & food delivery accounts for {dining_pct*100:.1f}% of your income.",
                "products": ["Cashback Card"]
            })

        # GAP 5: Overspending on Shopping
        if shopping_pct >= BENCHMARKS["shopping_pct_bad"]:
            gaps.append({
                "code": "OVERSPENDING_SHOPPING",
                "severity": 5,
                "title": "High Shopping Spending",
                "insight": f"You spend {shopping_pct*100:.1f}% of your income on shopping. A rewards card is recommended.",
                "products": ["Shopping Rewards Card"]
            })

        # GAP 6: Frequent traveller without a travel card
        if travel_pct >= BENCHMARKS["travel_pct_traveller"]:
            gaps.append({
                "code": "TRAVELLER_NO_CARD",
                "severity": 7,
                "title": "Frequent Traveller Without a Travel Card",
                "insight": f"You spend {travel_pct*100:.1f}% of your total spending on travel. A travel card could provide lounge access and air miles.",
                "products": ["Travel Card"]
            })

        # GAP 7: High rent burden
        if rent_pct >= BENCHMARKS["rent_pct_bad"] and not has_home_loan:
            gaps.append({
                "code": "HIGH_RENT_BURDEN",
                "severity": 6,
                "title": "Very High Rent Burden",
                "insight": f"Rent accounts for {rent_pct*100:.1f}% of your income. A Home Loan could convert rent into asset-building.",
                "products": ["Home Loan"]
            })

        # GAP 8: High medical spend without health insurance
        if medical_spend_180 > BENCHMARKS["medical_high_abs"] and not has_health_ins:
            gaps.append({
                "code": "HIGH_MEDICAL_NO_INSURANCE",
                "severity": 9,
                "title": "High Medical Expenses — No Health Insurance",
                "insight": f"You spent ₹{medical_spend_180:,.0f} on healthcare with no health insurance. This is a critical financial risk.",
                "products": ["Health Insurance"]
            })

        # GAP 9: Growing salary but no investment growth
        if features.income_trend == "up" and not has_investments:
            gaps.append({
                "code": "GROWING_INCOME_NO_INVESTMENT",
                "severity": 7,
                "title": "Rising Income, Zero Investment",
                "insight": "Your salary is growing, but you have not started investing. This is the ideal time to begin building wealth.",
                "products": ["Investment/SIP"]
            })

        # GAP 10: Over-leveraged (FOIR > 50%)
        if foir >= 0.50 and monthly_income > 0:
            gaps.append({
                "code": "OVER_LEVERAGED",
                "severity": 8,
                "title": "Over-Leveraged — EMI Burden Too High",
                "insight": f"Your loan EMIs consume {foir*100:.1f}% of your income (FOIR). The safe limit is 40-50%. Avoid taking additional loans.",
                "products": []
            })

        # GAP 11: High outstanding debt relative to income
        if total_outstanding > annual_income * 4 and annual_income > 0:
            gaps.append({
                "code": "HIGH_OUTSTANDING_DEBT",
                "severity": 7,
                "title": "Very High Debt-to-Income Ratio",
                "insight": f"Your outstanding debt of ₹{total_outstanding:,.0f} is over 4x your annual income. Focus on debt reduction.",
                "products": []
            })

        # Sort by severity descending
        gaps.sort(key=lambda g: g["severity"], reverse=True)
        return gaps

    # ── Financial Health Scorer ────────────────────────────────────────────────

    def _score_financial_health(self, features: CustomerFeatureSet, gaps: List[Dict]) -> Dict[str, Any]:
        breakdown = {}

        # 1. Savings Rate (30 pts)
        sr = features.surplus_ratio
        if sr >= BENCHMARKS["savings_rate_healthy"]:
            breakdown["savings"] = 30
        elif sr >= BENCHMARKS["savings_rate_low"]:
            breakdown["savings"] = 20
        elif sr >= BENCHMARKS["savings_rate_critical"]:
            breakdown["savings"] = 10
        else:
            breakdown["savings"] = 0

        # 2. Investment Activity (25 pts)
        invest_gap = next((g for g in gaps if g["code"] in ("NO_INVESTMENT", "GROWING_INCOME_NO_INVESTMENT")), None)
        if invest_gap is None:
            breakdown["investment"] = 25
        else:
            w180 = features.windows.get(180)
            invest_total_180 = w180.category_spend.get("Investment", 0) if w180 else 0
            annual_income = (features.monthly_income_avg * 12) or 1
            ratio = (invest_total_180 / 0.5) / annual_income # annualized
            breakdown["investment"] = min(25, int((ratio / BENCHMARKS["min_invest_ratio"]) * 25))

        # 3. Insurance Coverage (20 pts)
        ins_gap = next((g for g in gaps if g["code"] in ("NO_INSURANCE", "HIGH_MEDICAL_NO_INSURANCE", "NO_HEALTH_INSURANCE")), None)
        breakdown["insurance"] = 0 if ins_gap else 20

        # 4. Spending Discipline (20 pts)
        penalty = sum(
            5 for g in gaps
            if g["code"] in ("OVERSPENDING_DINING", "OVERSPENDING_SHOPPING", "CRITICAL_SAVINGS", "HIGH_RENT_BURDEN")
        )
        breakdown["spending_discipline"] = max(0, 20 - penalty)

        # 5. Debt Health (10 pts)
        foir_val = features.total_emi_monthly / features.monthly_income_avg if features.monthly_income_avg > 0 else 0
        if foir_val <= 0.30:
            breakdown["debt_health"] = 10
        elif foir_val <= 0.45:
            breakdown["debt_health"] = 6
        elif foir_val <= 0.55:
            breakdown["debt_health"] = 2
        else:
            breakdown["debt_health"] = 0

        total = sum(breakdown.values())

        if total >= 80:
            grade = "A — Excellent"
        elif total >= 65:
            grade = "B — Good"
        elif total >= 45:
            grade = "C — Needs Attention"
        elif total >= 25:
            grade = "D — Poor"
        else:
            grade = "F — Critical"

        return {
            "score": total,
            "grade": grade,
            "breakdown": breakdown,
        }
