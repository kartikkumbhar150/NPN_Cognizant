import sys
sys.stdout.reconfigure(encoding='utf-8', newline='\n')


from data_loader import load_customers, load_transactions, load_credit_cards, load_loan_products
from behavior_engine import BehaviorEngine
from segmentation import SegmentationEngine
from nbo_engine import NBOEngine
from genai_service import GenAIService
from financial_analyst import FinancialAnalyst


def print_customer_360(customer_id, customer_data, behavior, events,
                       segments, propensities, nbo_result, genai_msg,
                       financial_analysis):
    sep  = "=" * 65
    dash = "-" * 65

    print(sep)
    print("  CUSTOMER 360 — FINANCIAL INTELLIGENCE REPORT")
    print(sep)
    print(f"  Customer ID : {customer_id}")
    print(f"  Name        : {customer_data.get('first_name')} {customer_data.get('last_name')}")
    print(f"  Income      : Rs. {customer_data.get('annual_income', 0):,}  |  Credit Score: {customer_data.get('credit_score', 'N/A')}")
    print(f"  Segment     : {customer_data.get('customer_segment_type', 'N/A')}")
    print(dash)

    # ── Financial Health ─────────────────────────────────────────────────────
    if financial_analysis:
        hs = financial_analysis.get("health_score", {})
        ip = financial_analysis.get("income_profile", {})
        sp = financial_analysis.get("spending_profile", {})

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

        print("  INCOME & SAVINGS")
        print(f"    Monthly Income     : Rs. {monthly_income:,.0f}")
        print(f"    Monthly Spending   : Rs. {monthly_spend:,.0f}")
        print(f"    Monthly Savings    : Rs. {monthly_savings:,.0f}  ({savings_rate*100:.1f}%)")
        print(dash)

        cat = sp.get("category_breakdown", {})
        if cat:
            print("  SPENDING BREAKDOWN (monthly avg)")
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

    # ── Segments & Events ────────────────────────────────────────────────────
    print("  CUSTOMER SEGMENTS")
    for s in segments:
        print(f"    - {s}")

    if events:
        print("  RECENT EVENTS")
        for e in events:
            print(f"    - {e}")
    print(dash)

    # ── Propensity ───────────────────────────────────────────────────────────
    print("  PRODUCT PROPENSITY (Top 5)")
    for prod, score in list(propensities.items())[:5]:
        bar = "█" * (score // 5)
        print(f"    {prod:<25} {score:>3}%  {bar}")
    print(dash)

    # ── NBO ──────────────────────────────────────────────────────────────────
    print("  NEXT BEST OFFER")
    print(f"    Product    : {nbo_result['specific_product']}")
    print(f"    Propensity : {nbo_result['propensity']}")
    print("    Reasons    :")
    for r in nbo_result["reasons"]:
        # Word-wrap long reason strings at 60 chars
        words = r.split()
        line  = "      "
        for word in words:
            if len(line) + len(word) + 1 > 65:
                print(line)
                line = "      " + word + " "
            else:
                line += word + " "
        if line.strip():
            print(line)
    print(dash)

    # ── GenAI Message ────────────────────────────────────────────────────────
    print("  GENAI PERSONALISED MARKETING MESSAGE")
    for line in genai_msg.splitlines():
        print(f"    {line}")
    print(sep)


def main(target_customer_id=None):
    print("Loading data...")
    customers_df    = load_customers()
    transactions_df = load_transactions()
    credit_cards_df = load_credit_cards()
    loans_df        = load_loan_products()

    behavior_engine   = BehaviorEngine(transactions_df)
    seg_engine        = SegmentationEngine()
    financial_analyst = FinancialAnalyst(transactions_df)
    nbo_engine        = NBOEngine(credit_cards_df, loans_df)
    genai_service     = GenAIService()

    if not target_customer_id:
        target_customer_id = "CUST00125"

    customer_row = customers_df[customers_df["customer_id"] == target_customer_id]
    if customer_row.empty:
        print(f"Error: Customer {target_customer_id} not found.")
        sys.exit(1)

    customer_data = customer_row.iloc[0].to_dict()

    print(f"Analysing customer: {target_customer_id} ...")

    # Phase 2 & 3 — Behaviour & Events
    behavior = behavior_engine.analyze_behavior(target_customer_id)
    events   = behavior_engine.detect_events(target_customer_id)

    # Phase 4 — Segmentation
    segments = seg_engine.segment_customer(customer_data, behavior)

    # NEW — Deep Financial Analysis
    financial_analysis = financial_analyst.analyse(target_customer_id, customer_data, behavior)
    financial_gaps     = financial_analysis.get("gaps", [])

    # Phase 5 — Gap-driven Propensity
    propensities = nbo_engine.calculate_propensity(
        customer_data, segments, events,
        financial_gaps=financial_gaps,
    )

    # Phase 6 — Next Best Offer
    nbo = nbo_engine.determine_next_best_offer(
        propensities, customer_data, events,
        financial_gaps=financial_gaps,
        financial_analysis=financial_analysis,
    )

    # Phase 7 — GenAI Marketing Message
    genai_msg = genai_service.generate_marketing_message(
        customer_data, nbo,
        financial_analysis=financial_analysis,
    )

    print_customer_360(
        target_customer_id,
        customer_data,
        behavior,
        events,
        segments,
        propensities,
        nbo,
        genai_msg,
        financial_analysis,
    )


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
