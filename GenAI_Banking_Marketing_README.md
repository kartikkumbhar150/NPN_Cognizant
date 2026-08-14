# GenAI Marketing for Banking Services

## 1. Project Overview

**GenAI Marketing for Banking Services** is an AI-powered banking marketing platform designed to identify the most relevant banking product or service for a customer based on financial behaviour, transaction history, existing banking relationships, and product eligibility.

Core flow:

```text
Customer Data
      ↓
Transaction History
      ↓
Transaction Categorization
      ↓
Customer Spending Profile
      ↓
Behaviour Pattern Detection
      ↓
Important Event Detection
      ↓
Customer Segmentation
      ↓
Existing Products Check
      ↓
Product Eligibility
      ↓
Product Propensity Prediction
      ↓
Next Best Offer (NBO)
      ↓
GenAI Personalized Marketing
      ↓
Marketing Campaign
      ↓
Customer Response
      ↓
Campaign Analytics
      ↓
Feedback Loop
```

The central idea is:

> **Right customer + right product + right context + right message + right channel = personalized banking marketing**

---

## 2. Problem Statement

Traditional banking marketing often relies on broad customer segments and generic campaigns.

The proposed system uses customer-specific financial behaviour to identify relevant opportunities.

Example:

```text
Customer makes a flight payment
        ↓
Travel-related activity detected
        ↓
Check existing banking products
        ↓
Customer does not have a suitable travel card
        ↓
Check eligibility
        ↓
Predict product interest
        ↓
Travel Credit Card becomes the Next Best Offer
        ↓
GenAI creates personalized marketing content
```

The system should answer:

> **"Given what this customer is doing financially, what banking product is most relevant to them right now, and how should the bank communicate it?"**

---

## 3. Objectives

1. Build a realistic synthetic banking dataset.
2. Create a structured banking database.
3. Analyze transaction behaviour.
4. Categorize transactions.
5. Detect important financial events.
6. Segment customers based on behaviour.
7. Maintain customer-product ownership.
8. Build product eligibility rules.
9. Build Product Propensity Models.
10. Build a Next Best Offer engine.
11. Generate personalized marketing content using GenAI.
12. Create and manage campaigns.
13. Track customer engagement and conversions.
14. Provide explainable recommendations.
15. Implement consent and security controls.
16. Build a feedback loop for continuous improvement.

---

# 4. Core Features

## 4.1 Customer 360° Profile

Combine:

- Customer profile
- Demographics
- Income
- Occupation
- Transactions
- Spending behaviour
- Existing products
- Customer segments
- Recent events
- Product recommendations
- Propensity scores
- Marketing interactions

Example:

```text
Customer: CUST00125
Age: 29
Occupation: Software Engineer
Annual Income: ₹12,00,000

Existing:
Savings Account
Debit Card

Behaviour:
High travel spending
High online spending
Frequent digital payments

Recent Event:
Flight purchase

Potential Products:
Travel Credit Card
SIP
Travel Insurance
```

## 4.2 AI Transaction Categorization

Automatically classify transactions:

```text
IndiGo → Travel → Airline
Swiggy → Food → Food Delivery
Amazon → Shopping → E-Commerce
IRCTC → Travel → Railway
Apollo → Healthcare → Hospital
```

Possible categories:

- Travel
- Food
- Food Delivery
- Shopping
- E-Commerce
- Grocery
- Entertainment
- Movies
- Transport
- Fuel
- Utilities
- Healthcare
- Education
- Rent
- Investment
- SIP
- Insurance
- Bills
- Loan/EMI
- P2P
- Salary
- Other

Recommended hierarchy:

```text
Merchant / MCC
      ↓
Exact Mapping
      ↓
Rules
      ↓
Embeddings / ML
      ↓
LLM fallback
```

## 4.3 Real-Time / Important Event Detection

Detect events such as:

- Flight Purchase
- Hotel Booking
- International Transaction
- Large Purchase
- Salary Credit
- Recurring Rent
- Vehicle Purchase
- Education Payment
- Healthcare Spending
- Recurring Bill
- Investment Transaction
- New High-Value Merchant
- Increased Spending

Example:

```text
₹25,000 → Airline
       ↓
Flight Purchase Event
```

## 4.4 Customer Segmentation

Initial approach: **K-Means clustering**.

Features:

```text
age
monthly_income
monthly_spending
avg_transaction
travel_spending
food_spending
shopping_spending
investment_spending
transaction_frequency
international_transactions
```

Initial business segments:

- Frequent Travellers
- High-Value Customers
- Young Digital Spenders
- Investment Prospects
- Loan Prospects

K-Means produces cluster IDs; the team should profile each cluster and assign meaningful names.

## 4.5 Product Propensity Scoring

Predict the likelihood that a customer may be interested in a product.

Example:

```text
Travel Credit Card     0.91
Premium Credit Card    0.84
SIP / Investment       0.76
Fixed Deposit          0.68
Personal Loan          0.22
Health Insurance       0.64
```

Possible models:

- Logistic Regression
- Random Forest
- XGBoost
- Gradient Boosting

## 4.6 Next Best Offer

Combine:

```text
Behaviour
+
Recent Event
+
Customer Segment
+
Existing Products
+
Product Eligibility
+
Product Features
+
Propensity Score
+
Marketing Consent
```

Output:

```text
Recommended Product:
Travel Credit Card

Score:
91%

Reasons:
Frequent travel
Recent flight purchase
No suitable travel card
Eligible customer
```

## 4.7 Personalized Marketing using GenAI

The ML/rules layer decides **what to offer**.

GenAI decides **how to communicate it**.

Example:

```text
Planning your next trip?

Explore our travel-focused credit card
and its eligible travel benefits.
```

Generate:

- Push notification
- SMS
- Email
- In-app message
- Campaign headline
- Campaign description
- CTA
- Relationship-manager script

GenAI must not invent:

- Fees
- Rewards
- Eligibility
- Lounge benefits
- Interest rates
- Insurance coverage
- Product terms

Use the approved product catalogue as grounding/context.

## 4.8 AI Campaign Creation

Example:

```text
Campaign:
Travel Card August Campaign

Product:
Travel Credit Card

Target:
Frequent Travellers

Trigger:
Recent flight transaction

Minimum Propensity:
70%

Channels:
Mobile App + Email

Duration:
30 days
```

## 4.9 Multi-Channel Marketing

Possible channels:

- Mobile App
- Push Notification
- Email
- SMS
- Internet Banking
- Relationship Manager

## 4.10 Campaign Analytics & A/B Testing

Track:

- Sent
- Delivered
- Opened
- Clicked
- Application Started
- Application Completed
- Product Approved
- Product Activated
- Conversion Rate
- Revenue / Value
- ROI

A/B example:

```text
Variant A:
Make your next journey more rewarding.

Variant B:
Get more value from your travel spending.
```

## 4.11 Explainable AI

Every recommendation should include reasons.

Example:

```text
Recommended:
Travel Credit Card

Propensity:
91%

Why:
✓ 4 airline transactions
✓ High travel spending
✓ Recent flight purchase
✓ No suitable travel card
✓ Eligible for product
```

## 4.12 Privacy & Consent Management

The system should support:

- Marketing consent
- Opt-out
- Role-based access
- Data minimization
- Audit logging
- Secure handling of customer information
- AI decision logging
- Product eligibility checks

---

# 5. Dataset and Raw Data Layer

## 5.1 Customers

Target:

**300 synthetic customers**

Important fields:

```text
customer_id
customer_number
first_name
middle_name
last_name
date_of_birth
age
gender
marital_status
nationality
residential_status
occupation_type
occupation
employer_name
employment_type
annual_income
income_range
education_level
address_line_1
address_line_2
city
state
country
pincode
mobile_number
email
customer_since
customer_segment_type
customer_status
kyc_status
kyc_last_updated
risk_profile
credit_score
relationship_manager_id
preferred_language
preferred_channel
marketing_consent
created_at
updated_at
```

The synthetic dataset should be overwhelmingly Resident customers, with NRI customers kept very rare.

## 5.2 Raw Transactions

Target:

**~10,000 transactions across 300 customers over approximately one year.**

Raw schema:

```text
transaction_id
customer_id
account_id
card_id
transaction_date
transaction_time
transaction_type
transaction_mode
amount
currency
transaction_status
merchant_id
merchant_name
receiver_name
receiver_identifier
mcc_code
transaction_description
reference_number
channel
location_city
location_state
location_country
created_at
updated_at
```

Do not put AI-derived fields into this raw table.

## 5.3 Merchants

Merchant master:

```text
merchant_id
merchant_name
legal_name
merchant_type
merchant_category_code
merchant_identifier
upi_id
account_identifier
payment_network
merchant_city
merchant_state
merchant_country
pincode
address
website
contact_number
merchant_status
onboarded_date
created_at
updated_at
```

The bank/payment system may already know receiver/merchant information. LLMs should only be a fallback for ambiguity, not the primary source of merchant identity.

---

# 6. Transaction Universe

The synthetic transaction dataset should contain varied financial behaviour.

### Airlines

- IndiGo
- Air India
- Air India Express
- Vistara
- Akasa Air
- SpiceJet
- Emirates
- Qatar Airways
- Singapore Airlines
- Etihad Airways
- Lufthansa

### Food / Delivery

- Swiggy
- Zomato
- EatSure
- Domino's
- McDonald's
- KFC
- Pizza Hut
- Burger King
- Starbucks
- Subway

### E-Commerce

- Amazon India
- Flipkart
- Myntra
- Ajio
- Meesho
- Nykaa
- Croma
- Reliance Digital
- Tata Cliq
- Decathlon

### Shopping

- Reliance Trends
- Westside
- Lifestyle
- Pantaloons
- Shoppers Stop
- Zudio
- H&M
- Zara
- IKEA
- Home Centre

### Grocery

- DMart
- Reliance Smart
- Nature's Basket
- BigBasket
- Blinkit
- Zepto
- Swiggy Instamart

### Transport

- Uber
- Ola
- Rapido
- BluSmart

### Bus

- RedBus
- AbhiBus
- MSRTC
- KSRTC
- APSRTC
- TNSTC

### Train

- IRCTC
- Indian Railways

### Hotels / Travel

- Taj Hotels
- Marriott
- ITC Hotels
- Hyatt
- OYO
- MakeMyTrip
- Booking.com
- Agoda

### Movies / Entertainment

- PVR INOX
- Cinepolis
- BookMyShow
- Carnival Cinemas
- Netflix
- Spotify
- Amazon Prime
- Disney+ Hotstar
- Sony LIV
- YouTube Premium

### Fuel

- Indian Oil
- Bharat Petroleum
- Hindustan Petroleum
- Shell
- Nayara Energy

### Utilities / Bills

- Electricity
- Water
- Gas
- Mobile Recharge
- DTH
- Broadband
- Airtel
- Jio
- Vi
- BSNL

### Healthcare

- Apollo Hospitals
- Fortis
- Max Healthcare
- Manipal Hospitals
- Apollo Pharmacy
- Tata 1mg
- PharmEasy

### Education

- Coursera
- Udemy
- Unacademy
- BYJU'S
- upGrad

### Investments / Demat

- Zerodha
- Groww
- Upstox
- Angel One
- HDFC Securities
- ICICI Direct
- NSE
- BSE

### Mutual Funds / SIP

- HDFC Mutual Fund
- SBI Mutual Fund
- ICICI Prudential
- Nippon India
- Axis Mutual Fund
- Mirae Asset
- Aditya Birla Sun Life

### Insurance

- HDFC Life
- HDFC ERGO
- ICICI Lombard
- Tata AIA
- Niva Bupa
- Star Health

### Other

- Rent
- College fees
- School fees
- P2P transfers
- Salary credits

---

# 7. Banking Product Catalogue

The platform maintains detailed product catalogues.

Current product families:

```text
Credit Cards
Loans
Deposits
Investments
Insurance
Bank Accounts
```

Product catalogue = what the bank offers.

Customer-product tables = what the customer actually owns.

This distinction is important for recommendations.

---

# 8. Credit Card Products

`credit_card_products` contains detailed card information.

Major groups:

```text
Product Identity
Fees
Eligibility
Credit Terms
Rewards
Travel Benefits
Shopping/Lifestyle Benefits
Co-brand Information
Product Tags
Versioning
```

Product tags include:

```text
Travel
Shopping
Dining
Fuel
Online Shopping
International
Airport Lounge
Rewards
Cashback
Premium
Lifestyle
Golf
Movie
UPI
Business
```

These tags allow the recommendation engine to compare customer behaviour with card characteristics.

---

# 9. Loan Products

`loan_products` contains detailed loan information.

Major product families:

```text
Personal Loan
Home Loan
Home Loan Balance Transfer
Loan Against Property
New Car Loan
Used Car Loan
Two-Wheeler Loan
Education Loan
Gold Loan
Consumer Durable Loan
Business Loan
Working Capital Finance
Agriculture & Tractor Loan
Healthcare Finance
Commercial Vehicle Finance
Construction Equipment Finance
Loan Against Securities
Digital Loan Against Mutual Funds
Infrastructure Finance
NRI Home Loan
```

The table includes:

- Purpose
- Amount
- Tenure
- Interest
- Fees
- Eligibility
- Employment rules
- Income rules
- Credit criteria
- Co-applicant rules
- Collateral
- Documentation
- Disbursement
- EMI/repayment
- Product-specific attributes
- Digital features
- Marketing tags

---

# 10. Deposit Products

Examples:

```text
Fixed Deposit
Recurring Deposit
Tax Saving Deposit
```

Store:

- Minimum/maximum amount
- Tenure
- Interest rate
- Senior citizen rate
- Withdrawal rules
- Auto-renewal
- Tax benefit
- Status

---

# 11. Investment Products

Examples:

```text
Mutual Funds
SIP
Bonds
NPS
Investment Accounts
```

Store:

- Product type
- Provider
- Risk level
- Minimum investment
- Maximum investment
- Lock-in
- Investment horizon
- Description
- Status

---

# 12. Insurance Products

Major categories:

```text
Life Insurance
Term Insurance
Savings / Endowment
ULIP
Child Insurance
Retirement / Pension
Health Insurance
Family Health
Senior Citizen Health
Personal Accident
Motor Insurance
Travel Insurance
Home Insurance
Property Insurance
Business Insurance
Rural Insurance
```

Important information:

- Insurer
- Product category
- Coverage
- Sum assured
- Premium
- Policy term
- Eligibility
- Waiting periods
- Exclusions
- Riders
- Claim information
- Distribution channels
- Product tags

---

# 13. Customer Product Ownership

Tables:

```text
customer_accounts
customer_credit_cards
customer_loans
customer_deposits
customer_investments
customer_insurance
```

Purpose:

> Know exactly what products the customer already owns.

This prevents irrelevant recommendations.

---

# 14. AI/Processed Data Layer

Future tables:

```text
processed_transactions
customer_transaction_features
customer_behaviour_profiles
customer_segments
customer_segment_assignments
customer_events
product_propensity_scores
next_best_offers
recommendation_reasons
```

These are generated after the raw data layer is complete.

---

# 15. Marketing Layer

Future tables:

```text
marketing_campaigns
campaign_target_segments
campaign_customers
campaign_messages
campaign_variants
campaign_deliveries
campaign_conversions
```

Purpose:

- Campaign creation
- Audience selection
- GenAI content
- Channel delivery
- A/B testing
- Conversion tracking

---

# 16. Governance Layer

Future tables:

```text
customer_marketing_preferences
data_access_logs
ai_decision_logs
product_eligibility_rules
```

Purpose:

- Consent
- Access control
- Auditability
- AI traceability
- Eligibility enforcement

---

# 17. Complete AI Pipeline

## Phase 1 — Raw Data

```text
Customers
Transactions
Merchants
Products
Existing Customer Products
```

## Phase 2 — Processing

```text
Cleaning
Validation
Merchant Standardization
Transaction Categorization
Feature Engineering
```

## Phase 3 — Behaviour

```text
Customer Spending Profile
Behaviour Patterns
Recurring Patterns
```

## Phase 4 — Events

```text
Flight Purchase
Hotel Booking
International Travel
Large Purchase
Vehicle Purchase
Salary Credit
Investment Activity
etc.
```

## Phase 5 — Segmentation

```text
Customer Features
      ↓
K-Means
      ↓
Business Segments
```

## Phase 6 — Eligibility

```text
Customer Profile
      +
Product Rules
      ↓
Eligible Products
```

## Phase 7 — Propensity

```text
Customer Features
      +
Product Data
      ↓
Product Propensity
```

## Phase 8 — NBO

```text
Behaviour
+
Event
+
Segment
+
Existing Products
+
Eligibility
+
Propensity
        ↓
Next Best Offer
```

## Phase 9 — GenAI

```text
NBO
+
Customer Context
+
Approved Product Information
        ↓
Personalized Marketing
```

## Phase 10 — Campaign

```text
Target Audience
        ↓
Channel
        ↓
Message
        ↓
Campaign
```

## Phase 11 — Analytics

```text
Sent
↓
Delivered
↓
Opened
↓
Clicked
↓
Applied
↓
Converted
```

## Phase 12 — Feedback

```text
Response
↓
Training / Evaluation Data
↓
Improved Model
```

---

# 18. End-to-End Example

```text
CUSTOMER
CUST00125
        ↓
TRANSACTION
₹18,500 → IndiGo
        ↓
CATEGORY
Travel → Airline
        ↓
EVENT
Flight Purchase
        ↓
BEHAVIOUR
Frequent Traveller
        ↓
EXISTING PRODUCTS
Savings + Debit Card
No suitable travel card
        ↓
ELIGIBILITY
Eligible
        ↓
PROPENSITY
Travel Card = 91%
        ↓
NEXT BEST OFFER
Travel Credit Card
        ↓
EXPLAINABILITY
4 airline transactions
High travel spending
No suitable travel card
Eligible
        ↓
GENAI
Personalized travel-card message
        ↓
CAMPAIGN
Mobile App + Email
        ↓
CUSTOMER
Opens → Clicks → Applies
        ↓
ANALYTICS
Conversion recorded
        ↓
FEEDBACK LOOP
Model learns
```

---

# 19. Technology Stack

## Frontend

```text
Next.js
TypeScript
Tailwind CSS
Recharts
```

## Core Backend

```text
Spring Boot
Java
REST APIs
Spring Security
JWT
```

## AI Service

```text
Python
FastAPI
Pandas
NumPy
scikit-learn
XGBoost
Transformers
Sentence Transformers
```

## GenAI

LLM API for:

- Personalized content
- Campaign generation
- AI summaries
- Explanations
- Ambiguous classification fallback

## Database

```text
PostgreSQL
```

Optional:

```text
Qdrant
Redis
```

## DevOps

```text
Docker
GitHub
CI/CD
Cloud deployment
Secrets management
Monitoring
```

---

# 20. Recommended Architecture

```text
                    Next.js
                       ↓
                 Spring Boot
                       ↓
                  PostgreSQL
                       ↓
                  FastAPI
                       ↓
          ┌────────────┼────────────┐
          ↓            ↓            ↓
         ML          NLP          GenAI
          ↓            ↓            ↓
          └────────────┼────────────┘
                       ↓
             Recommendation Engine
                       ↓
                Campaign Engine
                       ↓
                  Analytics
```

Spring Boot:

- Customer APIs
- Product APIs
- Transaction APIs
- Authentication
- Authorization
- Campaign APIs
- Business rules

FastAPI:

- Transaction categorization
- Feature engineering
- Event detection
- Segmentation
- Propensity
- Recommendation
- GenAI orchestration

---

# 21. Team Division — 8 Members

## Member 1 — Data Engineering

Responsible for:

- Customer dataset
- Raw transactions
- Merchant data
- Cleaning
- Processing
- Feature pipeline
- PostgreSQL loading

## Member 2 — Customer Intelligence

Responsible for:

- Behaviour analysis
- Spending profiles
- K-Means
- Customer segmentation
- Segment profiling
- Event detection

## Member 3 — Recommendation AI

Responsible for:

- Product eligibility
- Propensity models
- Product ranking
- Next Best Offer
- Recommendation reasons

## Member 4 — GenAI

Responsible for:

- LLM integration
- Prompt engineering
- Product-grounded generation
- Personalized marketing
- Campaign copy
- AI summaries

## Member 5 — Spring Boot Backend

Responsible for:

- REST APIs
- Authentication
- Authorization
- Customer APIs
- Product APIs
- Campaign APIs
- Recommendation APIs

## Member 6 — Frontend

Responsible for:

- Customer 360
- Recommendations
- Customer insights
- Campaign manager
- Analytics dashboard
- Charts

## Member 7 — Marketing Analytics

Responsible for:

- Campaign metrics
- A/B testing
- Conversion tracking
- ROI
- Customer journey
- Campaign optimization
- Feedback data

## Member 8 — Security / Integration / DevOps

Responsible for:

- JWT
- RBAC
- Secure APIs
- Audit logging
- Service integration
- Docker
- Deployment
- Environment/secrets
- Monitoring

---

# 22. Development Roadmap

## Sprint 1 — Data Foundation

```text
300 Customers
10,000 Transactions
Merchant Master
Product Catalogues
Customer Product Ownership
PostgreSQL
```

## Sprint 2 — Data Processing

```text
Cleaning
Validation
Merchant Standardization
Transaction Categorization
Feature Engineering
```

## Sprint 3 — Customer Intelligence

```text
Spending Profiles
Behaviour Patterns
Event Detection
K-Means Segmentation
```

## Sprint 4 — Recommendation Engine

```text
Product Eligibility
Product Propensity
NBO
Explainability
```

## Sprint 5 — GenAI

```text
LLM Integration
Personalized Messages
Campaign Generation
A/B Variants
```

## Sprint 6 — Marketing

```text
Target Audience
Campaign Management
Channel Selection
Scheduling
```

## Sprint 7 — Analytics

```text
Journey Tracking
Campaign Metrics
Conversion
A/B Testing
ROI
```

## Sprint 8 — Feedback + Security + Deployment

```text
Feedback Loop
Model Evaluation
Consent
RBAC
Audit
Docker
Deployment
Final Integration
```

---

# 23. MVP

Do not build every possible feature first.

The first complete demo should be:

```text
Flight transaction
        ↓
Travel detection
        ↓
Customer behaviour
        ↓
Existing card check
        ↓
Eligibility
        ↓
Propensity
        ↓
Next Best Offer
        ↓
Explainable reasons
        ↓
GenAI message
        ↓
Dashboard
```

After this works, expand:

```text
Shopping → Shopping/Cashback Card
Vehicle Purchase → Auto Loan
High Savings → FD
Regular Surplus → SIP
International Travel → Travel Card/Insurance
Family Profile → Life/Health Insurance
Business Behaviour → Business Loan
```

---

# 24. Important Engineering Rules

### Rule 1 — Raw data stays raw

Do not mix AI-derived fields into raw tables.

### Rule 2 — ML decides, GenAI communicates

```text
ML / Rules:
What should be recommended?

GenAI:
How should it be communicated?
```

### Rule 3 — Existing products must be checked

Don't recommend products that are irrelevant or already owned without evaluating upgrade/cross-sell opportunities.

### Rule 4 — Eligibility before marketing

An offer should pass eligibility and business rules before being marketed.

### Rule 5 — Product grounding

GenAI must use approved product data.

### Rule 6 — Explainability

Every recommendation must have reasons.

### Rule 7 — Consent

Marketing communication must respect customer preferences.

### Rule 8 — Synthetic data

Use synthetic/anonymized data for the prototype.

---

# 25. Final Project Definition

> **GenAI Marketing for Banking Services is an AI-powered, context-aware banking marketing platform that analyzes customer transaction history and financial behaviour, detects meaningful customer events, segments customers, predicts product interest, determines the Next Best Offer, generates grounded personalized marketing content using GenAI, manages targeted campaigns, tracks outcomes, and continuously improves through customer response feedback.**

---

# 26. Final Success Criteria

The team should consider the system successful when it can:

- Load synthetic customer data.
- Load transaction history.
- Identify merchants/receivers.
- Categorize transactions.
- Generate customer spending profiles.
- Detect behaviour patterns.
- Detect important events.
- Segment customers.
- Load bank product catalogues.
- Track customer-owned products.
- Evaluate eligibility.
- Predict product propensity.
- Generate Next Best Offer.
- Explain recommendations.
- Generate personalized GenAI marketing content.
- Create campaigns.
- Select target customers.
- Deliver through supported channels in the prototype.
- Track engagement.
- Track conversions.
- Run A/B tests.
- Display results in a dashboard.
- Store feedback.
- Evaluate/improve future models.
- Maintain privacy, consent and security controls.

---

# 27. One-Line System Architecture

```text
Raw Banking Data
→ Customer Intelligence
→ Event Detection
→ Segmentation
→ Eligibility
→ Propensity
→ Next Best Offer
→ GenAI Personalization
→ Campaign
→ Analytics
→ Feedback
```

# 28. Core Differentiator

The project is not simply:

> **"AI generates banking advertisements."**

The real innovation is:

> **The system understands the customer's financial context, identifies a relevant product opportunity, decides the Next Best Offer, explains why it is relevant, and then uses GenAI to communicate that offer in a personalized way.**
