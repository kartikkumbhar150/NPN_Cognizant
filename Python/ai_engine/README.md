# NPN Bank AI Engine

This AI engine helps bank employees find the most relevant product for a customer. It studies customer transactions, income, spending, existing bank products, and financial needs. It then suggests a **Next Best Offer (NBO)** and, if marketing is permitted, writes a personalised message.

> Important: the current engine is rule-based. Its `propensity` value is a recommendation score, not a guaranteed or trained probability of conversion.

## Simple pipeline flow

All presentation-ready flowcharts are available in `AI_ENGINE_FLOWCHARTS.txt`.

## Data used by the engine

| Input | What it tells the engine |
| --- | --- |
| Customer profile | Age, income, credit score, employment type, account status, and marketing consent. |
| Transactions | Where and how the customer spends, receives salary, pays EMIs, or invests. |
| Product catalogue | Products offered by the bank and their rules, such as minimum income or age. |
| Existing holdings | Products the customer already owns, including cards, loans, investments, deposits, and insurance. |
| Campaign history | Previous offers and customer engagement; used to avoid over-contacting customers. |

## How it works

1. **Load data** — Reads customer profiles, transactions, product catalogues, and current product holdings from Supabase or local CSV files.
2. **Build features** — Calculates income, spending by category, savings, recent transactions, recurring payments, loans, investments, and insurance.
3. **Understand the customer** — Detects patterns such as frequent travel, high shopping, salary increase, high medical spending, or low savings.
4. **Find financial gaps** — Identifies possible needs, for example no investment, no health insurance, or high rent burden.
5. **Check eligibility** — Removes products the customer cannot receive because of age, income, credit score, affordability, inactive status, or existing ownership.
6. **Rank offers** — Matches the customer's needs and behaviour with product tags, then selects the top product.
7. **Explain and protect** — Provides reasons for the recommendation and checks consent, campaign frequency, cooldown, and fatigue before generating any marketing content.

## What the engine returns

For one customer, the API returns a Customer 360 result containing:

- Customer behaviour and detected events.
- Segments, such as `Frequent Traveller` or `Investment Prospect`.
- Financial-health score and detected financial gaps.
- One Next Best Offer with its recommendation score.
- Reasons explaining why that product was selected.
- Marketing decision: allowed/blocked, recommended channel, and warnings.
- A GenAI message only when marketing is allowed.

## How the recommendation score is created

The engine does **not** choose a product only because it is profitable for the bank. It first removes unsuitable products, then scores the remaining products using:

```text
Customer need + spending/behaviour match + recent events + income/value + product priority
```

For example, a customer with frequent airline spending, no travel card, sufficient income, and a good credit score may receive a high score for a Travel Credit Card. A customer who already owns that card, or fails its eligibility rules, will not receive it.

## Rule-based AI and GenAI

- **Rule-based AI** decides *what* product to recommend. It uses customer data, business rules, eligibility checks, and scoring.
- **GenAI (Groq/Llama)** decides *how* to write the message. It uses only the selected product and approved reasons; it does not decide the offer.

## Main files

| File | Simple purpose |
| --- | --- |
| `data_loader.py` | Loads all data from Supabase or CSV files. |
| `feature_engine.py` | Creates the main customer summary used by other modules. |
| `behavior_engine.py` | Finds spending and payment behaviour. |
| `event_engine.py` | Detects signals such as travel, salary changes, or large purchases. |
| `financial_analyst.py` | Finds savings, investment, insurance, and debt gaps. |
| `segmentation.py` | Adds labels such as Frequent Traveller or Investment Prospect. |
| `eligibility_engine.py` | Ensures a product is allowed for the customer. |
| `product_fit_engine.py` | Matches customer needs with product benefits/tags. |
| `nbo_engine.py` | Selects the Next Best Offer. |
| `explainability_engine.py` | Creates understandable recommendation reasons. |
| `marketing_guard.py` | Checks consent and avoids over-contacting customers. |
| `genai_service.py` | Generates marketing copy using Groq or a demo fallback. |

## Example

```text
Customer spends frequently on flights and hotels
        ↓
Engine detects travel behaviour
        ↓
Checks whether the customer already has a travel card and is eligible
        ↓
Travel Credit Card receives a high recommendation score
        ↓
System explains: “High travel spending and no suitable travel card found”
        ↓
If consent is available, generate an email or push notification
```

## Main issues and improvements

| Issue | Why it matters | Suggested improvement |
| --- | --- | --- |
| The score is not a trained ML probability. | It can be misunderstood as a conversion prediction. | Call it a **recommendation score** now; later train and evaluate a real propensity model. |
| Campaign history is empty in the current API flow. | Cooldown and fatigue checks do not work properly. | Store campaign deliveries and engagement in the database, then pass the real history to `MarketingGuard`. |
| Consent defaults to allowed when data is missing. | This is risky for real banking communication. | Use opt-in consent by channel and default to blocked when consent is unknown. |
| Segments are created but do not affect NBO ranking. | Extra processing does not improve the final offer. | Include segment signals in scoring or remove them until needed. |
| The LLM output is not checked after generation. | It could contain unsuitable claims or miss disclaimers. | Validate text against approved product facts, prohibited phrases, word limits, and required disclaimers. |
| All analysis runs during one API request. | It can become slow with many customers/transactions. | Precompute customer features, cache them, and generate GenAI content asynchronously. |
| Tests and dependencies are incomplete. | A clean machine cannot fully verify the API. | Add FastAPI/Uvicorn/test dependencies and automated tests for eligibility, consent, and ranking rules. |

## How to run

From `NPN_Cognizant/Python`:

```powershell
python -m pip install -r requirements.txt
python -m pip install fastapi "uvicorn[standard]" "python-jose[cryptography]" passlib python-multipart
uvicorn api_server:app --reload --port 8000
```

- Set `SUPABASE_DB_URL` to use Supabase. Otherwise the system uses local CSV data.
- Set `GROQ_API_KEY` to use Groq. Without it, the system uses a demo message generator.

## Hackathon pitch line

**NPN Bank AI Engine turns customer financial behaviour into an eligibility-safe, explainable product recommendation and uses GenAI only to communicate that recommendation responsibly.**
