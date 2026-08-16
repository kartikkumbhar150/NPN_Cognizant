import sys
sys.stdout.reconfigure(encoding='utf-8', newline='\n')

from data_loader import load_customers, load_transactions, load_credit_cards, load_loan_products, load_investment_products
from ai_engine.feature_engine import FeatureEngine
from behavior_engine import BehaviorEngine
from event_engine import EventEngine
from financial_analyst import FinancialAnalyst
from segmentation import SegmentationEngine
from nbo_engine import NBOEngine
from explainability_engine import ExplainabilityEngine
from marketing_guard import MarketingGuard
from genai_service import GenAIService


def print_customer_360(customer_id, customer_data, features, behavior, events,
                       segments, financial_analysis, nbo_result, explanation, genai_msg, marketing_check):
    sep  = "=" * 65
    dash = "-" * 65

    print(sep)
    print("  CUSTOMER 360 — FINANCIAL INTELLIGENCE REPORT (v2.0)")
    print(sep)
    print(f"  Customer ID : {customer_id}")
    print(f"  Name        : {customer_data.get('first_name')} {customer_data.get('last_name')}")
    print(f"  Income      : Rs. {customer_data.get('annual_income', 0):,}  |  Credit Score: {customer_data.get('credit_score', 'N/A')}")
    
    print(dash)
    print("  SEGMENTS")
    for s in segments:
        print(f"    - {s}")

    # ── Financial Health ─────────────────────────────────────────────────────
    if financial_analysis:
        hs = financial_analysis.get("health_score", {})
        ip = financial_analysis.get("income_profile", {})
        sp = financial_analysis.get("spending_profile", {})

        print(dash)
        print(f"  FINANCIAL HEALTH SCORE : {hs.get('score', 'N/A')}/100  —  {hs.get('grade', '')}")

        bd = hs.get("breakdown", {})
        print(f"    Savings ............ {bd.get('savings', 0)}/30")
        print(f"    Investment ......... {bd.get('investment', 0)}/25")
        print(f"    Insurance .......... {bd.get('insurance', 0)}/20")
        print(f"    Spending Discipline  {bd.get('spending_discipline', 0)}/25")
        print(dash)

        monthly_income = ip.get("monthly_avg_income", 0)
        monthly_spend  = sp.get("monthly_total_spend", 0)
        savings_rate   = sp.get("savings_rate", 0)
        monthly_savings = sp.get("monthly_savings", 0)

        print("  INCOME & SAVINGS (90d Baseline)")
        print(f"    Monthly Income     : Rs. {monthly_income:,.0f}")
        print(f"    Monthly Spending   : Rs. {monthly_spend:,.0f}")
        print(f"    Monthly Savings    : Rs. {monthly_savings:,.0f}  ({savings_rate*100:.1f}%)")
        print(dash)

        cat = sp.get("category_breakdown", {})
        if cat:
            print("  SPENDING BREAKDOWN (90d avg)")
            for c, d in sorted(cat.items(), key=lambda x: x[1]["monthly_avg"], reverse=True):
                bar_width = int(d["pct_of_income"] * 100)
                bar = "█" * min(bar_width, 30)
                print(f"    {c:<18} Rs.{d['monthly_avg']:>8,.0f}   {d['pct_of_income']*100:>5.1f}%  {bar}")
        print(dash)

        gaps = financial_analysis.get("gaps", [])
        if gaps:
            print("  FINANCIAL GAPS DETECTED")
            for g in gaps:
                sev = g["severity"]
                marker = "🔴" if sev >= 8 else ("🟡" if sev >= 5 else "🟢")
                print(f"    {marker} [{sev}/10] {g['title']}")
        print(dash)

    # ── Events ───────────────────────────────────────────────────────────────
    if events:
        print("  RECENT EVENTS")
        for e in events[:5]:
            conf = e.get("confidence", 0)
            marker = "🔥" if conf >= 0.8 else "⚡"
            print(f"    {marker} [{conf:.2f}] {e.get('event_type')}")
        print(dash)

    # ── NBO & Explanation ────────────────────────────────────────────────────
    print("  NEXT BEST OFFER")
    print(f"    Product    : {nbo_result.get('specific_product')}")
    print(f"    Propensity : {nbo_result.get('propensity')}")
    print(f"    Fit Score  : {nbo_result.get('full_result', {}).get('fit_score', 0):.2f}")
    
    print("\n  EXPLANATION (Internal Audit):")
    for r in explanation.get("reasons", []):
        print(f"    • {r}")
    print(dash)

    # ── Marketing Guard ──────────────────────────────────────────────────────
    print("  MARKETING GUARD CHECK")
    if marketing_check.get("allowed"):
        print(f"    ✅ Allowed (Channel: {marketing_check.get('recommended_channel')})")
        for w in marketing_check.get("warnings", []):
            print(f"    ⚠️ Warning: {w}")
    else:
        print(f"    ❌ BLOCKED: {marketing_check.get('reason')}")
    print(dash)

    # ── GenAI Message ────────────────────────────────────────────────────────
    if marketing_check.get("allowed"):
        print("  GENAI PERSONALISED MARKETING MESSAGE")
        for line in genai_msg.splitlines():
            print(f"    {line}")
    print(sep)


def main(target_customer_id=None):
    print("Loading data from Supabase...")
    customers_df    = load_customers()
    transactions_df = load_transactions()
    credit_cards_df = load_credit_cards()
    loans_df        = load_loan_products()
    investments_df  = load_investment_products()

    print("Initializing Engine v2.0...")
    feature_engine    = FeatureEngine(transactions_df)
    behavior_engine   = BehaviorEngine(transactions_df)
    event_engine      = EventEngine(transactions_df)
    financial_analyst = FinancialAnalyst()
    seg_engine        = SegmentationEngine()
    nbo_engine        = NBOEngine(credit_cards_df, loans_df, investments_df)
    explain_engine    = ExplainabilityEngine()
    marketing_guard   = MarketingGuard()
    genai_service     = GenAIService()

    if not target_customer_id:
        target_customer_id = "CUST00125"

    customer_row = customers_df[customers_df["customer_id"] == target_customer_id]
    if customer_row.empty:
        print(f"Error: Customer {target_customer_id} not found.")
        sys.exit(1)

    customer_data = customer_row.iloc[0].to_dict()

    print(f"Analysing customer: {target_customer_id} ...")

    # 1. Feature Extraction (Single source of truth)
    features = feature_engine.compute(target_customer_id, customer_data)

    # 2. Behavior & Events
    behavior = behavior_engine.analyze_behavior_v2(target_customer_id, features)
    events   = event_engine.detect_events(target_customer_id, features)

    # 3. Deep Financial Analysis
    financial_analysis = financial_analyst.analyse(target_customer_id, customer_data, features)
    financial_gaps     = financial_analysis.get("gaps", [])

    # 4. Segmentation
    segments = seg_engine.segment_customer(customer_data, features)

    # 5. Next Best Offer (Eligibility + Fit + Propensity)
    nbo = nbo_engine.determine_next_best_offer(
        features=features,
        events=events,
        financial_gaps=financial_gaps,
        customer_data=customer_data
    )

    # 6. Explainability (Audit Trail)
    explanation = explain_engine.explain(
        nbo_candidate=nbo.get("full_result", {}),
        features=features,
        events=events,
        financial_gaps=financial_gaps,
        customer_data=customer_data
    )

    # 7. Marketing Guard Check
    marketing_check = marketing_guard.check(
        customer_data=customer_data,
        product_result=nbo.get("full_result", {}),
        campaign_history=[]  # Empty for demo, would fetch from DB in prod
    )

    # 8. GenAI Marketing Message (Only if allowed)
    genai_msg = ""
    if marketing_check.get("allowed"):
        channel = marketing_check.get("recommended_channel", "email")
        genai_msg = genai_service.generate_marketing_message(
            customer_data=customer_data,
            nbo_result=nbo,
            explanation=explanation,
            channel=channel
        )

    print_customer_360(
        target_customer_id,
        customer_data,
        features,
        behavior,
        events,
        segments,
        financial_analysis,
        nbo,
        explanation,
        genai_msg,
        marketing_check
    )


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
