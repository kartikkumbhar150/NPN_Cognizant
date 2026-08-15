"""
analyser.py — deep financial analysis engine
Adapted from Python/ai_engine/financial_analyst.py for the customer portal.
"""
from decimal import Decimal
from datetime import date, timedelta
from collections import defaultdict


MERCHANT_CATEGORY_MAP = {
    "MER00": "Travel", "MER08": "Travel",
    "MER01": "Dining",
    "MER02": "Shopping", "MER03": "Shopping",
    "MER04": "Groceries",
    "MER05": "Transport", "MER06": "Transport", "MER07": "Transport",
    "MER10": "Fuel",
    "MER13": "Medical",
    "MER15": "Investment", "MER16": "Investment",
    "MER17": "Insurance",
}

BENCHMARKS = {
    "dining_pct_warn":       0.12,
    "dining_pct_bad":        0.18,
    "shopping_pct_warn":     0.15,
    "shopping_pct_bad":      0.22,
    "rent_pct_bad":          0.40,
    "savings_rate_critical": 0.08,
    "savings_rate_low":      0.20,
    "savings_rate_healthy":  0.30,
    "travel_pct_traveller":  0.12,
    "medical_high_abs":      20000,
    "income_invest_thresh":  600000,
    "min_invest_ratio":      0.05,
}


def _map_category(merchant_id: str) -> str:
    if not merchant_id:
        return "Other"
    for prefix, cat in MERCHANT_CATEGORY_MAP.items():
        if merchant_id.startswith(prefix):
            return cat
    return "Other"


def _to_float(val) -> float:
    if val is None:
        return 0.0
    if isinstance(val, Decimal):
        return float(val)
    return float(val)


def analyse_customer(data: dict) -> dict:
    """Run full financial analysis. Returns structured insights dict."""
    customer     = data.get("customer", {})
    transactions = data.get("transactions", [])
    credit_cards = data.get("credit_cards", [])
    loans        = data.get("loans", [])

    annual_income  = _to_float(customer.get("annual_income", 0))
    monthly_income_declared = annual_income / 12 if annual_income else 0

    # ── Categorise transactions ───────────────────────────────────────────────
    category_spend  = defaultdict(float)
    monthly_spend   = defaultdict(float)
    monthly_income  = defaultdict(float)
    total_debit     = 0.0
    salary_months   = set()
    all_ym_dates    = set()

    for tx in transactions:
        amount      = _to_float(tx.get("amount", 0))
        tx_type     = (tx.get("transaction_type") or "").lower()
        merchant_id = tx.get("merchant_id") or ""
        desc        = (tx.get("transaction_description") or "").upper()
        tx_date     = tx.get("transaction_date")

        ym = str(tx_date)[:7] if tx_date else "unknown"
        if ym != "unknown":
            all_ym_dates.add(ym)

        if tx_type == "credit" and "SALARY" in desc:
            monthly_income[ym] += amount
            salary_months.add(ym)
        elif tx_type == "debit":
            cat = _map_category(merchant_id)
            category_spend[cat] += amount
            monthly_spend[ym]   += amount
            total_debit         += amount

    # Use the actual date span of ALL transactions as the denominator for monthly averages.
    # Using only salary_months would cause wildly inflated monthly spend if salary credits
    # are sparse (e.g. 1 salary credit across 12 months of debits → spending ÷ 1).
    months_observed = max(len(all_ym_dates), len(salary_months), 1)
    avg_monthly_income = (
        sum(monthly_income.values()) / len(monthly_income)
        if monthly_income else monthly_income_declared
    )
    avg_monthly_spend  = total_debit / months_observed
    avg_monthly_savings = avg_monthly_income - avg_monthly_spend
    savings_rate = avg_monthly_savings / avg_monthly_income if avg_monthly_income else 0

    # Spending breakdown with % of income
    category_breakdown = {}
    for cat, total in category_spend.items():
        monthly_avg = total / months_observed
        pct = monthly_avg / avg_monthly_income if avg_monthly_income else 0
        category_breakdown[cat] = {
            "total":         round(total, 2),
            "monthly_avg":   round(monthly_avg, 2),
            "pct_of_income": round(pct, 4),
        }

    # Monthly spend timeline
    monthly_timeline = [
        {"month": k, "amount": round(v, 2)}
        for k, v in sorted(monthly_spend.items())
    ]

    # ── Gap Detection ─────────────────────────────────────────────────────────
    invest_spend   = category_spend.get("Investment", 0)
    insurance_spend= category_spend.get("Insurance", 0)
    medical_spend  = category_spend.get("Medical", 0)
    dining_pct     = category_breakdown.get("Dining",    {}).get("pct_of_income", 0)
    shopping_pct   = category_breakdown.get("Shopping",  {}).get("pct_of_income", 0)
    rent_pct       = category_breakdown.get("Rent",      {}).get("pct_of_income", 0)
    travel_total   = category_spend.get("Travel", 0)
    travel_pct     = travel_total / total_debit if total_debit else 0

    gaps = []

    # No Investment
    if annual_income >= BENCHMARKS["income_invest_thresh"] and invest_spend < annual_income * BENCHMARKS["min_invest_ratio"]:
        shortfall = annual_income * BENCHMARKS["min_invest_ratio"] - invest_spend
        gaps.append({
            "code":     "NO_INVESTMENT",
            "severity": 9,
            "title":    "Zero / Low Investment Activity",
            "insight":  (
                f"You earn Rs.{avg_monthly_income:,.0f}/month but have invested only "
                f"Rs.{invest_spend:,.0f} in the past {months_observed} months. "
                f"You are Rs.{shortfall:,.0f} short of the recommended 5% investment benchmark."
            ),
            "products": ["Mutual Fund SIP", "Fixed Deposit"],
        })

    # No Insurance
    if insurance_spend == 0:
        gaps.append({
            "code":     "NO_INSURANCE",
            "severity": 8,
            "title":    "No Insurance Coverage Detected",
            "insight":  (
                f"No insurance premium payments found in your history. "
                f"With Rs.{medical_spend:,.0f} already spent on healthcare, "
                f"you are financially exposed."
            ),
            "products": ["Health Insurance", "Life Insurance"],
        })

    # Critical savings
    if savings_rate < BENCHMARKS["savings_rate_critical"]:
        gaps.append({
            "code":     "CRITICAL_SAVINGS",
            "severity": 8,
            "title":    "Critically Low Savings Rate",
            "insight":  (
                f"You are saving only {savings_rate*100:.1f}% of your monthly income "
                f"(Rs.{avg_monthly_savings:,.0f}/month). Healthy savings should be 20-30%."
            ),
            "products": ["Fixed Deposit", "Savings Account"],
        })
    elif savings_rate < BENCHMARKS["savings_rate_low"]:
        gaps.append({
            "code":     "LOW_SAVINGS",
            "severity": 6,
            "title":    "Below-Average Savings Rate",
            "insight":  (
                f"Savings rate: {savings_rate*100:.1f}% (Rs.{avg_monthly_savings:,.0f}/month). "
                f"Consider a Recurring Deposit or SIP to build a financial cushion."
            ),
            "products": ["Mutual Fund SIP", "Fixed Deposit"],
        })

    # Overspending dining
    if dining_pct >= BENCHMARKS["dining_pct_bad"]:
        monthly_dining = category_breakdown.get("Dining", {}).get("monthly_avg", 0)
        gaps.append({
            "code":     "OVERSPENDING_DINING",
            "severity": 5,
            "title":    "High Dining & Food Spending",
            "insight":  (
                f"You spend Rs.{monthly_dining:,.0f}/month on dining ({dining_pct*100:.1f}% of income). "
                f"A dining cashback card can reduce this cost."
            ),
            "products": ["Cashback Credit Card"],
        })

    # Overspending shopping
    if shopping_pct >= BENCHMARKS["shopping_pct_bad"]:
        monthly_shop = category_breakdown.get("Shopping", {}).get("monthly_avg", 0)
        gaps.append({
            "code":     "OVERSPENDING_SHOPPING",
            "severity": 5,
            "title":    "High Shopping Spending",
            "insight":  (
                f"Shopping accounts for {shopping_pct*100:.1f}% of income "
                f"(Rs.{monthly_shop:,.0f}/month). A shopping rewards card earns back on what you spend."
            ),
            "products": ["Shopping Rewards Card"],
        })

    # Frequent traveller
    if travel_pct >= BENCHMARKS["travel_pct_traveller"]:
        monthly_travel = category_breakdown.get("Travel", {}).get("monthly_avg", 0)
        gaps.append({
            "code":     "TRAVELLER_NO_CARD",
            "severity": 7,
            "title":    "Frequent Traveller Without a Travel Card",
            "insight":  (
                f"You spend Rs.{monthly_travel:,.0f}/month on travel ({travel_pct*100:.1f}% of total spending) "
                f"but have no travel card benefits. Air miles and lounge access await."
            ),
            "products": ["Travel Credit Card"],
        })

    # High medical, no insurance
    if medical_spend > BENCHMARKS["medical_high_abs"] and insurance_spend == 0:
        gaps.append({
            "code":     "HIGH_MEDICAL_NO_INSURANCE",
            "severity": 9,
            "title":    "High Medical Expenses — No Insurance",
            "insight":  (
                f"You have spent Rs.{medical_spend:,.0f} on healthcare with no insurance detected. "
                f"A health plan can cover these costs going forward."
            ),
            "products": ["Health Insurance"],
        })

    gaps.sort(key=lambda g: g["severity"], reverse=True)

    # ── Health Score ──────────────────────────────────────────────────────────
    breakdown = {}
    if savings_rate >= BENCHMARKS["savings_rate_healthy"]:
        breakdown["savings"] = 30
    elif savings_rate >= BENCHMARKS["savings_rate_low"]:
        breakdown["savings"] = 20
    elif savings_rate >= BENCHMARKS["savings_rate_critical"]:
        breakdown["savings"] = 10
    else:
        breakdown["savings"] = 0

    invest_ratio = invest_spend / (annual_income or 1)
    breakdown["investment"] = min(25, int(invest_ratio / BENCHMARKS["min_invest_ratio"] * 25))

    breakdown["insurance"] = 0 if insurance_spend == 0 else 20

    penalty = sum(5 for g in gaps if g["code"] in (
        "OVERSPENDING_DINING", "OVERSPENDING_SHOPPING", "CRITICAL_SAVINGS", "HIGH_RENT_BURDEN"))
    breakdown["spending_discipline"] = max(0, 25 - penalty)

    total_score = sum(breakdown.values())
    if total_score >= 80:
        grade = "A — Excellent"
    elif total_score >= 65:
        grade = "B — Good"
    elif total_score >= 45:
        grade = "C — Needs Attention"
    elif total_score >= 25:
        grade = "D — Poor"
    else:
        grade = "F — Critical"

    # ── Next Best Offer ───────────────────────────────────────────────────────
    nbo = _compute_nbo(gaps, customer, credit_cards, loans)

    return {
        "customer_id":    customer.get("customer_id"),
        "first_name":     customer.get("first_name"),
        "health_score": {
            "score":     total_score,
            "grade":     grade,
            "breakdown": breakdown,
        },
        "income_profile": {
            "monthly_avg_income":   round(avg_monthly_income, 2),
            "annual_income":        round(avg_monthly_income * 12, 2),
            "months_observed":      months_observed,
            "monthly_avg_savings":  round(avg_monthly_savings, 2),
            "savings_rate_pct":     round(savings_rate * 100, 1),
        },
        "spending_breakdown":  category_breakdown,
        "monthly_timeline":    monthly_timeline,
        "gaps":                gaps,
        "next_best_offer":     nbo,
    }


def _compute_nbo(gaps, customer, credit_cards, loans):
    """Pick the best product recommendation based on detected gaps."""
    if not gaps:
        return {"product": "No urgent recommendation", "propensity": "N/A", "reasons": []}

    top_gap  = gaps[0]
    product_cat = top_gap["products"][0] if top_gap.get("products") else "Product"
    income   = _to_float(customer.get("annual_income", 0))
    reasons  = [g["insight"] for g in gaps[:3]]
    specific = _resolve_product(product_cat, income, credit_cards, loans)

    return {
        "product":    specific,
        "category":   product_cat,
        "propensity": f"{min(99, top_gap['severity'] * 10)}%",
        "reasons":    reasons,
        "gap_code":   top_gap["code"],
    }


def _resolve_product(category, income, credit_cards, loans):
    if "Travel" in category:
        cards = [c for c in credit_cards if c.get("tag_travel")]
        eligible = [c for c in cards if _to_float(c.get("minimum_income_annual", 0)) <= income]
        if eligible:
            return eligible[0].get("card_name", "Travel Credit Card")
        return cards[0].get("card_name", "Travel Credit Card") if cards else "Travel Credit Card"

    if "Cashback" in category or "Shopping" in category:
        cards = [c for c in credit_cards if c.get("tag_cashback")]
        eligible = [c for c in cards if _to_float(c.get("minimum_income_annual", 0)) <= income]
        if eligible:
            return eligible[0].get("card_name", "Cashback Credit Card")

    if "SIP" in category or "Mutual" in category:
        return "Mutual Fund SIP"

    if "Fixed Deposit" in category or "FD" in category:
        return "Fixed Deposit (FD)"

    if "Health Insurance" in category:
        return "Health & Life Insurance Plan"

    if "Home Loan" in category:
        loan = next((l for l in loans if "Home" in (l.get("loan_category") or "")), None)
        return loan.get("product_name", "Home Loan") if loan else "Home Loan"

    if "Personal Loan" in category:
        loan = next((l for l in loans if "Personal" in (l.get("loan_category") or "")), None)
        return loan.get("product_name", "Personal Loan") if loan else "Personal Loan"

    return category
