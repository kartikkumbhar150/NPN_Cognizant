"""
Financial Analyst Engine
========================
Deep analysis of a customer's financial behavior.
Detects financial gaps, overspending patterns, and generates
a financial health score to power the recommendation engine.
"""

from datetime import timedelta
import pandas as pd


# ─────────────────────────────────────────────────────────────────────────────
# Benchmarks — thresholds used for gap detection
# ─────────────────────────────────────────────────────────────────────────────
BENCHMARKS = {
    "dining_pct_warn":      0.12,   # >12% of income on dining = warning
    "dining_pct_bad":       0.18,   # >18% = overspending
    "shopping_pct_warn":    0.15,   # >15% of income on shopping = warning
    "shopping_pct_bad":     0.22,   # >22% = overspending
    "rent_pct_warn":        0.30,   # >30% of income on rent = high burden
    "rent_pct_bad":         0.40,   # >40% = very high burden
    "savings_rate_critical": 0.08,  # saving <8% of income = critical
    "savings_rate_low":     0.20,   # saving <20% = low
    "savings_rate_healthy": 0.30,   # saving ≥30% = healthy
    "travel_pct_traveller": 0.12,   # >12% of spend on travel = frequent traveller
    "medical_high_abs":     20000,  # >₹20K medical spend = high
    "income_invest_thresh": 600000, # annual income above which we expect investment activity
    "min_invest_ratio":     0.05,   # expect ≥5% of income going to investments
}


class FinancialAnalyst:
    """
    Deep financial analysis engine.
    Analyses income, spending, gaps and financial health for one customer.
    """

    def __init__(self, transactions_df):
        self.tx = transactions_df

    # ─────────────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────────────

    def analyse(self, customer_id, customer_data, behavior_data):
        """
        Run full financial analysis for a customer.
        Returns a rich dict with all findings.
        """
        cust_tx = self.tx[self.tx["customer_id"] == customer_id].copy()

        # Core financial metrics
        income_profile   = self._build_income_profile(cust_tx, customer_data)
        spending_profile = self._build_spending_profile(cust_tx, behavior_data, income_profile)
        gaps             = self._detect_gaps(income_profile, spending_profile, behavior_data)
        health_score     = self._score_financial_health(income_profile, spending_profile, gaps)

        return {
            "income_profile":   income_profile,
            "spending_profile": spending_profile,
            "gaps":             gaps,
            "health_score":     health_score,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Income Profiler
    # ─────────────────────────────────────────────────────────────────────────

    def _build_income_profile(self, cust_tx, customer_data):
        """Extract monthly income pattern from salary credits."""
        salary_tx = cust_tx[
            (cust_tx["transaction_type"] == "Credit") &
            (cust_tx["transaction_description"] == "SALARY CREDIT")
        ].copy()

        declared_annual = customer_data.get("annual_income", 0)
        declared_monthly = declared_annual / 12 if declared_annual else 0

        if salary_tx.empty:
            return {
                "monthly_avg_income": declared_monthly,
                "annual_income_observed": declared_annual,
                "salary_months_observed": 0,
                "salary_growing": False,
                "salary_credits": [],
            }

        salary_tx["ym"] = salary_tx["transaction_date"].dt.to_period("M")
        monthly_salary = salary_tx.groupby("ym")["amount"].sum()

        monthly_avg = monthly_salary.mean()
        salary_credits = monthly_salary.tolist()

        # Is salary growing month-over-month?
        growing = False
        if len(salary_credits) >= 3:
            recent = salary_credits[-3:]
            growing = recent[-1] > recent[0]

        return {
            "monthly_avg_income":      round(monthly_avg, 2),
            "annual_income_observed":  round(monthly_avg * 12, 2),
            "salary_months_observed":  len(monthly_salary),
            "salary_growing":          growing,
            "salary_credits":          salary_credits,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Spending Profiler
    # ─────────────────────────────────────────────────────────────────────────

    def _build_spending_profile(self, cust_tx, behavior_data, income_profile):
        """Build detailed spending breakdown with income-relative percentages."""
        monthly_income = income_profile["monthly_avg_income"] or 1  # avoid div/0

        category_spend = behavior_data.get("category_spend", {})
        total_spend    = behavior_data.get("total_spend", 0)

        # Monthly averages (annualise then divide)
        months_observed = max(income_profile["salary_months_observed"], 1)
        monthly_total   = total_spend / months_observed

        # Per-category monthly average and % of income
        category_breakdown = {}
        for cat, amount in category_spend.items():
            monthly_cat = amount / months_observed
            pct_income  = monthly_cat / monthly_income
            category_breakdown[cat] = {
                "total":          round(amount, 2),
                "monthly_avg":    round(monthly_cat, 2),
                "pct_of_income":  round(pct_income, 4),
            }

        savings_monthly  = monthly_income - monthly_total
        savings_rate     = savings_monthly / monthly_income if monthly_income else 0

        # Transaction counts per category (frequency)
        debits = cust_tx[cust_tx["transaction_type"] == "Debit"]
        cat_counts = {}
        for cat in category_breakdown:
            cat_counts[cat] = len(debits[debits["merchant_id"].apply(
                lambda x: self._is_category(x, cat)
            )])

        return {
            "monthly_total_spend": round(monthly_total, 2),
            "monthly_savings":     round(savings_monthly, 2),
            "savings_rate":        round(savings_rate, 4),
            "category_breakdown":  category_breakdown,
            "category_tx_counts":  cat_counts,
            "months_analysed":     months_observed,
        }

    def _is_category(self, merchant_id, category):
        """Simple category-match helper (mirrors BehaviorEngine mapping)."""
        if pd.isna(merchant_id) or merchant_id == "":
            return False
        mapping = {
            "Travel":      ["MER00", "MER08"],
            "Dining":      ["MER01"],
            "Shopping":    ["MER02", "MER03"],
            "Groceries":   ["MER04"],
            "Transport":   ["MER05", "MER06", "MER07"],
            "Fuel":        ["MER10"],
            "Medical":     ["MER13"],
            "Investment":  ["MER15", "MER16"],
            "Insurance":   ["MER17"],
        }
        prefixes = mapping.get(category, [])
        return any(merchant_id.startswith(p) for p in prefixes)

    # ─────────────────────────────────────────────────────────────────────────
    # Gap Detector — the core innovation
    # ─────────────────────────────────────────────────────────────────────────

    def _detect_gaps(self, income_profile, spending_profile, behavior_data):
        """
        Detect what the customer SHOULD be doing but isn't.
        Returns a list of gap dicts, sorted by severity (highest first).
        """
        gaps = []
        cat  = spending_profile["category_breakdown"]
        monthly_income = income_profile["monthly_avg_income"]
        annual_income  = income_profile["annual_income_observed"]
        savings_rate   = spending_profile["savings_rate"]

        invest_spend   = cat.get("Investment", {}).get("total", 0)
        insurance_spend= cat.get("Insurance",  {}).get("total", 0)
        medical_spend  = cat.get("Medical",    {}).get("total", 0)
        dining_pct     = cat.get("Dining",     {}).get("pct_of_income", 0)
        shopping_pct   = cat.get("Shopping",   {}).get("pct_of_income", 0)
        rent_pct       = cat.get("Rent",       {}).get("pct_of_income", 0)
        travel_total   = cat.get("Travel",     {}).get("total", 0)
        total_spend    = spending_profile["monthly_total_spend"] * spending_profile["months_analysed"]
        travel_pct_spend = travel_total / total_spend if total_spend else 0

        # ── GAP 1: No investments despite good income ──────────────────────
        if (annual_income >= BENCHMARKS["income_invest_thresh"]
                and invest_spend < annual_income * BENCHMARKS["min_invest_ratio"]):
            gap_amount = round(annual_income * BENCHMARKS["min_invest_ratio"] - invest_spend, 2)
            gaps.append({
                "code":     "NO_INVESTMENT",
                "severity": 9,
                "title":    "Zero / Low Investment Activity",
                "insight":  (
                    f"You earn ₹{monthly_income:,.0f}/month but have invested only "
                    f"₹{invest_spend:,.0f} in the past {spending_profile['months_analysed']} months. "
                    f"Financial experts recommend investing at least 5% of income. "
                    f"You are ₹{gap_amount:,.0f} short of that benchmark."
                ),
                "products": ["Investment/SIP", "FD"],
            })

        # ── GAP 2: No insurance coverage ──────────────────────────────────
        if insurance_spend == 0:
            gaps.append({
                "code":     "NO_INSURANCE",
                "severity": 8,
                "title":    "No Insurance Coverage Detected",
                "insight":  (
                    f"There is no insurance premium payment in your transaction history. "
                    f"With an income of ₹{annual_income:,.0f}/year and "
                    f"₹{medical_spend:,.0f} already spent on healthcare, "
                    f"you are financially exposed to medical and life risks."
                ),
                "products": ["Health Insurance"],
            })

        # ── GAP 3: Critical savings rate ───────────────────────────────────
        if savings_rate < BENCHMARKS["savings_rate_critical"]:
            gaps.append({
                "code":     "CRITICAL_SAVINGS",
                "severity": 8,
                "title":    "Critically Low Savings Rate",
                "insight":  (
                    f"You are saving only {savings_rate*100:.1f}% of your monthly income "
                    f"(₹{spending_profile['monthly_savings']:,.0f}/month). "
                    f"A healthy savings rate is 20-30%. "
                    f"A Fixed Deposit can enforce disciplined saving."
                ),
                "products": ["FD", "Savings Account"],
            })
        elif savings_rate < BENCHMARKS["savings_rate_low"]:
            gaps.append({
                "code":     "LOW_SAVINGS",
                "severity": 6,
                "title":    "Below-Average Savings Rate",
                "insight":  (
                    f"You are saving {savings_rate*100:.1f}% of your monthly income "
                    f"(₹{spending_profile['monthly_savings']:,.0f}/month). "
                    f"You could be saving more — a Recurring Deposit or SIP "
                    f"can help build a financial cushion."
                ),
                "products": ["Investment/SIP", "FD"],
            })

        # ── GAP 4: Overspending on Dining ─────────────────────────────────
        if dining_pct >= BENCHMARKS["dining_pct_bad"]:
            monthly_dining = cat.get("Dining", {}).get("monthly_avg", 0)
            gaps.append({
                "code":     "OVERSPENDING_DINING",
                "severity": 5,
                "title":    "High Dining & Food Spending",
                "insight":  (
                    f"You spend ₹{monthly_dining:,.0f}/month on dining & food delivery "
                    f"({dining_pct*100:.1f}% of your income). "
                    f"A dining rewards card can earn you cashback on every order "
                    f"and effectively reduce this cost."
                ),
                "products": ["Cashback Card", "Dining Rewards Card"],
            })
        elif dining_pct >= BENCHMARKS["dining_pct_warn"]:
            monthly_dining = cat.get("Dining", {}).get("monthly_avg", 0)
            gaps.append({
                "code":     "HIGH_DINING",
                "severity": 4,
                "title":    "Elevated Dining Spend",
                "insight":  (
                    f"Dining & food delivery accounts for {dining_pct*100:.1f}% "
                    f"(₹{monthly_dining:,.0f}/month) of your income. "
                    f"A dining cashback card can save you money every month."
                ),
                "products": ["Cashback Card"],
            })

        # ── GAP 5: Overspending on Shopping ───────────────────────────────
        if shopping_pct >= BENCHMARKS["shopping_pct_bad"]:
            monthly_shopping = cat.get("Shopping", {}).get("monthly_avg", 0)
            gaps.append({
                "code":     "OVERSPENDING_SHOPPING",
                "severity": 5,
                "title":    "High Shopping Spending",
                "insight":  (
                    f"You spend ₹{monthly_shopping:,.0f}/month on shopping "
                    f"({shopping_pct*100:.1f}% of your income). "
                    f"A shopping rewards credit card can earn you points on "
                    f"every purchase you're already making."
                ),
                "products": ["Shopping Rewards Card"],
            })

        # ── GAP 6: Frequent traveller without a travel card ───────────────
        if travel_pct_spend >= BENCHMARKS["travel_pct_traveller"]:
            monthly_travel = cat.get("Travel", {}).get("monthly_avg", 0)
            gaps.append({
                "code":     "TRAVELLER_NO_CARD",
                "severity": 7,
                "title":    "Frequent Traveller Without a Travel Card",
                "insight":  (
                    f"You spend ₹{monthly_travel:,.0f}/month on travel "
                    f"({travel_pct_spend*100:.1f}% of total spending) "
                    f"but there are no travel card reward transactions detected. "
                    f"A travel credit card with lounge access and air miles could "
                    f"save you significantly."
                ),
                "products": ["Travel Card"],
            })

        # ── GAP 7: High rent burden ────────────────────────────────────────
        if rent_pct >= BENCHMARKS["rent_pct_bad"]:
            monthly_rent = cat.get("Rent", {}).get("monthly_avg", 0)
            gaps.append({
                "code":     "HIGH_RENT_BURDEN",
                "severity": 6,
                "title":    "Very High Rent Burden",
                "insight":  (
                    f"Rent accounts for {rent_pct*100:.1f}% of your income "
                    f"(₹{monthly_rent:,.0f}/month). "
                    f"A Home Loan could give you ownership at a similar or lower EMI, "
                    f"while also building an asset."
                ),
                "products": ["Home Loan"],
            })

        # ── GAP 8: High medical spend without insurance ────────────────────
        if medical_spend > BENCHMARKS["medical_high_abs"] and insurance_spend == 0:
            gaps.append({
                "code":     "HIGH_MEDICAL_NO_INSURANCE",
                "severity": 9,
                "title":    "High Medical Expenses — No Insurance",
                "insight":  (
                    f"You have spent ₹{medical_spend:,.0f} on healthcare with "
                    f"no insurance detected. This is a serious financial risk. "
                    f"A health insurance plan can cover these costs going forward."
                ),
                "products": ["Health Insurance"],
            })

        # ── GAP 9: Growing salary but no investment growth ─────────────────
        if income_profile["salary_growing"] and invest_spend == 0:
            gaps.append({
                "code":     "GROWING_INCOME_NO_INVESTMENT",
                "severity": 7,
                "title":    "Rising Income, Zero Investment",
                "insight":  (
                    f"Your salary has been growing consistently over the past "
                    f"{income_profile['salary_months_observed']} months, but "
                    f"you have not started investing. This is the best time to "
                    f"begin compounding your wealth — even ₹2,000/month makes a difference."
                ),
                "products": ["Investment/SIP"],
            })

        # Sort by severity descending
        gaps.sort(key=lambda g: g["severity"], reverse=True)
        return gaps

    # ─────────────────────────────────────────────────────────────────────────
    # Financial Health Scorer
    # ─────────────────────────────────────────────────────────────────────────

    def _score_financial_health(self, income_profile, spending_profile, gaps):
        """
        Score the customer's financial health from 0-100.
        Returns score, grade, and a breakdown by dimension.
        """
        breakdown = {}

        # 1. Savings Rate (30 pts)
        sr = spending_profile["savings_rate"]
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
            cat = spending_profile["category_breakdown"]
            invest_total = cat.get("Investment", {}).get("total", 0)
            annual_income = income_profile["annual_income_observed"] or 1
            ratio = invest_total / annual_income
            breakdown["investment"] = min(25, int(ratio / BENCHMARKS["min_invest_ratio"] * 25))

        # 3. Insurance Coverage (20 pts)
        ins_gap = next((g for g in gaps if g["code"] in ("NO_INSURANCE", "HIGH_MEDICAL_NO_INSURANCE")), None)
        breakdown["insurance"] = 0 if ins_gap else 20

        # 4. Spending Discipline (25 pts)
        penalty = sum(
            5 for g in gaps
            if g["code"] in ("OVERSPENDING_DINING", "OVERSPENDING_SHOPPING", "CRITICAL_SAVINGS", "HIGH_RENT_BURDEN")
        )
        breakdown["spending_discipline"] = max(0, 25 - penalty)

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
            "score":     total,
            "grade":     grade,
            "breakdown": breakdown,
        }
