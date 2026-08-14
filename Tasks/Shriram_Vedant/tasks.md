## Phase 2 — Data Processing Pipeline

### Goal
Convert raw banking data into reliable analytical data.

```text
raw_transactions
       ↓
validation
       ↓
cleaning
       ↓
standardization
       ↓
processed_transactions
```

### Tasks
- Remove duplicates
- Validate transaction IDs
- Validate customer IDs
- Handle missing values
- Normalize merchant names
- Normalize transaction descriptions
- Validate MCC
- Standardize dates and amounts
- Detect invalid transactions

**Create:**
- `processed_transactions`

---

## Phase 3 — Transaction Intelligence

### Goal
Understand what customers are doing.

*This is where the project starts becoming intelligent.*

### 3.1 Transaction categorization

**Convert:**
`INDIGO`
**into:**
`Travel → Airline`

**Convert:**
`Swiggy`
**into:**
`Food → Food Delivery`

**Convert:**
`IRCTC`
**into:**
`Travel → Railway`

**Use a hierarchy:**
```text
Merchant/MCC
      ↓
Merchant master
      ↓
Rules
      ↓
Embeddings/ML
      ↓
LLM fallback
```

### 3.2 Customer behavioural features

**Create:**
- `monthly_spending`
- `average_transaction`
- `transaction_frequency`
- `travel_spending`
- `shopping_spending`
- `food_spending`
- `fuel_spending`
- `international_spending`
- `investment_spending`
- `bill_spending`

**Also calculate:**
- Monthly income
- Monthly expenditure
- Savings/surplus
- Spending frequency
- Category frequency
- Merchant frequency
- Digital payment ratio

**Create:**
- `customer_transaction_features`

---

## Phase 4 — Event & Customer Intelligence ⭐

*This is one of the most important phases.*

### 4.1 Event Detection

Identify meaningful financial events.

**Examples:**
- Flight purchase
- Hotel booking
- Vehicle purchase
- International transaction
- Salary credit
- Large purchase
- Recurring rent
- Education payment
- Healthcare spending
- Large savings
- Investment activity

**Example:**
```text
₹22,000 → IndiGo
       ↓
Flight Purchase Event
```

**Create:**
- `customer_events`

### 4.2 Customer Segmentation

Use ML to group similar customers.

**Possible techniques:**
- K-Means
- DBSCAN
- Hierarchical clustering

**Features:**
- Income
- Spending
- Travel frequency
- Online spending
- Investment behaviour
- Transaction frequency

**Possible output:**
- Frequent Traveller
- Digital Shopper
- High-Value Customer
- Investment Prospect
- Loan Prospect
- Premium Customer
- Business Customer

**Create:**
- `customer_segments`

---

## Phase 5 — Product Recommendation Engine ⭐⭐⭐

*This is the core AI engine.*

### 5.1 Product Eligibility Engine

Before recommending anything, check:

```text
Customer Profile
      ↓
Income
Age
Employment
Credit Score
Existing Products
      ↓
Product Eligibility Rules
      ↓
Eligible Products
```

**For example:**
Customer income = ₹12L

**Eligible:**
- Credit Card ✓
- Personal Loan ✓
- SIP ✓
- Premium Card ✓

### 5.2 Product Propensity Model

Now predict:
*"How likely is the customer to be interested in this product?"*

**Example:**
Customer C101

| Product | Propensity |
|---|---|
| Travel Card | 91% |
| Credit Card | 87% |
| SIP | 72% |
| FD | 65% |
| Personal Loan | 21% |

**Possible models:**
- Logistic Regression
- Random Forest
- XGBoost
- Gradient Boosting

**Create:**
- `product_propensity_scores`

### 5.3 Next Best Offer Engine ⭐⭐⭐

**Combine:**
```text
Customer Behaviour
        +
Recent Events
        +
Customer Segment
        +
Existing Products
        +
Product Eligibility
        +
Propensity Score
```

**Example:**
```text
Flight Purchase
      +
Frequent Traveller
      +
No Travel Card
      +
Eligible
      +
91% propensity
      ↓
NEXT BEST OFFER
Travel Credit Card
```

**Create:**
- `next_best_offers`
- `recommendation_reasons`