# Deep Financial Intelligence & Personalized Recommendation Engine

## Background

The current system uses a simple heuristic — it checks for a few events (travel, large purchase) and adjusts a hardcoded propensity table. It cannot detect financial gaps like "this person earns ₹12L/year but has never invested" or "this person is spending 40% of income on dining."

The goal is to build a **robust financial analysis engine** that:
1. **Deeply analyzes** a person's full transaction history across multiple dimensions
2. **Detects financial gaps** — things the customer is NOT doing that they should be (no investments, no insurance, no emergency fund, etc.)
3. **Scores financial health** — how well or poorly the customer is managing money
4. **Generates personalized, gap-driven offers** with highly specific reasons based on actual spending data
5. **Writes the marketing message with real context** fed to the LLM (exact rupee amounts, percentages, specific gaps)

---

## Architecture: New `financial_analyst.py` Engine

This replaces the current simplistic propensity logic in `nbo_engine.py` and adds a new layer.

```
BehaviorEngine (existing - reads raw transactions)
       ↓
FinancialAnalyst (NEW - deep analysis layer)
  ├── Income & Savings Profiler
  ├── Spending Pattern Analyser
  ├── Gap Detector (the key innovation)
  └── Financial Health Scorer
       ↓
NBOEngine (refactored - gap-aware recommendations)
       ↓
GenAIService (upgraded - passes real financial context to LLM)
```

---

## Proposed Changes

### 1. Core Python Layer

---

#### [NEW] [`financial_analyst.py`](file:///e:/NPN_Cognizant/Python/ai_engine/financial_analyst.py)

This is the heart of the upgrade. It performs all the deep analysis.

**Income & Savings Profiler:**
- Calculates monthly average income from salary credits
- Calculates monthly average spending (debits)
- Calculates savings rate: `(income - spend) / income * 100`
- Flags: `savings_rate < 10%` = critical, `10-20%` = low, `>30%` = healthy

**Spending Pattern Analyser:**
- Calculates % of income spent in each category (Dining, Travel, Shopping, etc.)
- Compares against healthy benchmarks:
  - Dining > 15% of income = overspending flag
  - Shopping > 20% of income = overspending flag
  - Rent > 35% of income = high burden flag
- Detects impulse spending: many small transactions in Shopping/Dining

**Gap Detector — the key innovation:**
Detects what the customer should have but doesn't:

| Gap | Detection Logic | Bank Product to Offer |
|---|---|---|
| `NO_INVESTMENT` | Salaried + income > 6L + zero Investment category txns | Mutual Fund SIP, FD |
| `NO_INSURANCE` | Zero Insurance category txns + age > 30 | Life/Health Insurance |
| `NO_EMERGENCY_FUND` | Savings rate < 10% + no FD transactions | Savings/FD Account |
| `OVERSPENDING_DINING` | Dining > 15% of income | Dining cashback card |
| `OVERSPENDING_SHOPPING` | Shopping > 20% of income | Shopping rewards card |
| `FREQUENT_TRAVELLER_NO_CARD` | Travel > 15% of total spend + no travel txns to airline card | Travel Credit Card |
| `RENT_BURDEN` | Rent > 35% of income | Home Loan |
| `HIGH_MEDICAL_NO_INSURANCE` | Medical spend > ₹20K + no insurance txns | Health Insurance |
| `SALARY_GROWING_NO_INVESTMENT` | Salary growing month-over-month but no investments | Wealth Management |

**Financial Health Scorer:**
Produces a single score 0-100 with grades:
- `Savings Rate` (30 pts)
- `Investment Activity` (25 pts)
- `Insurance Coverage` (20 pts)
- `Spending Discipline` (25 pts)

---

#### [MODIFY] [`nbo_engine.py`](file:///e:/NPN_Cognizant/Python/ai_engine/nbo_engine.py)

Refactored to consume the `FinancialAnalyst` output instead of hardcoded propensity tables:
- Takes `financial_gaps` and `financial_health` as input
- Ranks gaps by severity + product eligibility
- Picks the single most impactful product to offer
- Generates **rich, specific reasons** using real numbers:
  - ❌ *"High propensity for FD"* (current)
  - ✅ *"You earn ₹2.7L/month but have invested ₹0 in the past 12 months. A ₹5,000/month SIP could grow to ₹1.2L in 2 years."* (new)

---

#### [MODIFY] [`behavior_engine.py`](file:///e:/NPN_Cognizant/Python/ai_engine/behavior_engine.py)

Upgrade to extract richer data needed by the analyst:
- Monthly income breakdown (per month salary credits)
- Monthly expense breakdown (per month debits)
- Transaction count per category (frequency, not just amount)
- Detects month-on-month salary growth

---

#### [MODIFY] [`genai_service.py`](file:///e:/NPN_Cognizant/Python/ai_engine/genai_service.py)

Upgrade the prompt to include the actual financial context:
- Specific gap details (e.g., "earns ₹12L but invests ₹0")
- Financial health score and grade
- Key spending facts as bullet points
- The mock fallback will also become gap-aware and use real numbers

---

#### [MODIFY] [`run_pipeline.py`](file:///e:/NPN_Cognizant/Python/ai_engine/run_pipeline.py)

Wire in the new `FinancialAnalyst` layer and display the financial health report in the Customer 360 output.

---

## Verification Plan

### Automated
```powershell
$env:PYTHONIOENCODING="utf-8"; python ai_engine/run_pipeline.py CUST00125
$env:PYTHONIOENCODING="utf-8"; python ai_engine/run_pipeline.py CUST00001
```

### Manual Verification
- Customer with no investment transactions should get `NO_INVESTMENT` gap and an SIP/FD recommendation
- Customer with high dining spend should get a cashback card recommendation
- GenAI message should contain specific numbers from the analysis (actual income, actual spending amounts)
- Financial health score should appear in the Customer 360 output

