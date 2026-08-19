# NPN Bank — GenAI Hyper-Personalized Banking Marketing Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.0-61DAFB.svg?style=flat&logo=react&logoColor=black)](https://react.dev)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![Redis](https://img.shields.io/badge/Redis-Cache%20%26%20Events-DC382D.svg?style=flat&logo=redis&logoColor=white)](https://redis.io)
[![Supabase](https://img.shields.io/badge/Database-Supabase%20%2F%20PostgreSQL-3ECF8E.svg?style=flat&logo=supabase&logoColor=white)](https://supabase.com)
[![Groq](https://img.shields.io/badge/GenAI-Groq%20LLM%20(Llama%203)-F55036.svg?style=flat)](https://groq.com)
[![Vite](https://img.shields.io/badge/Vite-6.2-646CFF.svg?style=flat&logo=vite&logoColor=white)](https://vitejs.dev)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

An enterprise-grade, AI-driven banking intelligence and hyper-personalized marketing platform. Built for **NPN Bank (Cognizant Project)**, this solution shifts banking outreach from generic broadcast marketing to **context-aware, real-time, financial gap-driven recommendations** backed by deterministic explainability, marketing guardrails, and Groq-powered generative marketing copy.

---

## Table of Contents

- [1. Executive Summary & Problem Statement](#1-executive-summary--problem-statement)
- [2. System Architecture](#2-system-architecture)
- [3. Key Platform Capabilities](#3-key-platform-capabilities)
  - [3.1 Customer 360° Intelligence](#31-customer-360-intelligence)
  - [3.2 Financial Gap Detection & Health Scoring](#32-financial-gap-detection--health-scoring)
  - [3.3 Real-Time Event Engine](#33-real-time-event-engine)
  - [3.4 Next Best Offer (NBO) & Eligibility Decisioning](#34-next-best-offer-nbo--eligibility-decisioning)
  - [3.5 Marketing Guard & Consent Safety Gate](#35-marketing-guard--consent-safety-gate)
  - [3.6 Context-Aware GenAI Copywriting](#36-context-aware-genai-copywriting)
  - [3.7 Closed-Loop Campaign Studio & Analytics](#37-closed-loop-campaign-studio--analytics)
  - [3.8 Banking Chatbot & Semantic Search (RAG)](#38-banking-chatbot--semantic-search-rag)
- [4. Backend & Redis Architecture](#4-backend--redis-architecture)
  - [4.1 Backend Service Design](#41-backend-service-design)
  - [4.2 Redis Caching & Event Layer](#42-redis-caching--event-layer)
- [5. Project Directory Structure](#5-project-directory-structure)
- [6. End-to-End AI Engine Pipeline](#6-end-to-end-ai-engine-pipeline)
- [7. API Reference](#7-api-reference)
- [8. Technology Stack](#8-technology-stack)
- [9. Setup & Installation Guide](#9-setup--installation-guide)
  - [9.1 Prerequisites](#91-prerequisites)
  - [9.2 Environment Configuration](#92-environment-configuration)
  - [9.3 Backend Setup](#93-backend-setup)
  - [9.4 Frontend Setup](#94-frontend-setup)
  - [9.5 Chatbot Setup](#95-chatbot-setup)
- [10. Running the Platform](#10-running-the-platform)
- [11. Testing & Verification](#11-testing--verification)
- [12. Contributing & Pull Request Guidelines](#12-contributing--pull-request-guidelines)

---

## 1. Executive Summary & Problem Statement

Traditional retail banking marketing relies on broad demographic segments, static propensity tables, and unsolicited outbound messages. This leads to **customer fatigue, high opt-out rates, and low conversion**.

**The NPN Bank Solution:**
A real-time financial intelligence platform answering one fundamental question:
> *"Given what this customer is doing financially right now, what banking product is genuinely most relevant to them, why are they eligible, and how should the bank communicate it safely and persuasively?"*

```
Traditional Mass Marketing               NPN Hyper-Personalized AI Marketing
-------------------------               ------------------------------------
- Blanket blast campaigns               - Multi-window behavioral profiling (7-365 days)
- Static product pushes                 - Gap detection (e.g., earns ₹12L, ₹0 invested)
- Black-box / opaque logic              - Deterministic eligibility & audit trail
- Generic email templates               - Time-of-day & cohort-tailored GenAI copy
- Disconnected conversion data          - Closed-loop funnel analytics & fatigue guards
```

---

## 2. System Architecture

```mermaid
graph TD
    subgraph Client Layer ["Frontend & Client Layer"]
        UI["React 19 Dashboard (Vite + Tailwind)"]
        CB["Banking Chatbot Interface"]
    end

    subgraph API Gateway ["API Gateway & Auth"]
        FastAPI["FastAPI REST Server (:8000)"]
        JWT["OAuth2 / JWT Authentication"]
        CORS["CORS & Request Middleware"]
    end

    subgraph Caching Layer ["Redis High-Speed Layer"]
        R_C360["Customer 360 Aggregate Cache"]
        R_SESS["Session & Token Blocklist"]
        R_THROT["Campaign Throttling & Cooldowns"]
        R_PUBSUB["Pub/Sub Event Bus"]
    end

    subgraph AI Pipeline ["Banking AI Intelligence Pipeline (v2.0 / v3.0)"]
        FE["Feature Engine (Rolling Windows)"]
        BE["Behavior Engine (Spending Trajectory)"]
        EE["Event Engine (Triggers & Thresholds)"]
        FA["Financial Analyst (Gap Detection & Health Score)"]
        EL["Eligibility Engine (Hard Constraints)"]
        PF["Product Fit Engine (Relevance Scoring)"]
        NBO["Next Best Offer Engine (Ensemble Ranker)"]
        EXP["Explainability Engine (Audit Reasons)"]
        MG["Marketing Guard (Consent & Fatigue Gate)"]
        GENAI["GenAI Service (Groq LLM / Time & Cohort Aware)"]
    end

    subgraph Data Layer ["Persistent Storage & Vector Store"]
        PG["Supabase / PostgreSQL Database"]
        CSV["Synthetic Banking Datasets (CSV)"]
        QD["Qdrant Vector DB (Chatbot Knowledge)"]
    end

    UI <-->|REST API + Bearer Token| FastAPI
    CB <-->|FastAPI / RAG| FastAPI
    FastAPI <--> JWT
    FastAPI <--> CORS

    FastAPI <-->|Low-Latency Read/Write| Caching Layer
    FastAPI --> AI Pipeline

    FE --> BE & EE & FA
    FA & EE & BE --> EL
    EL --> PF --> NBO --> EXP --> MG --> GENAI

    AI Pipeline <--> PG
    AI Pipeline <--> CSV
    CB <--> QD
```

---

## 3. Key Platform Capabilities

### 3.1 Customer 360° Intelligence
- **Comprehensive Demographic & Financial Aggregation:** Synthesizes income, salary stability, transaction velocity, liquidity ratio, savings rate, and credit score.
- **Dynamic Category Breakdowns:** Real-time breakdown across Dining, Travel, Shopping, Utilities, Investments, Healthcare, Rent, and Fuel.
- **Existing Holdings Inspection:** Cross-references active credit cards, loans, fixed deposits, and insurance policies to eliminate redundant marketing.

### 3.2 Financial Gap Detection & Health Scoring
The core algorithmic differentiator in `financial_analyst.py`:
- **Financial Health Score (0–100):** Weighted across Savings Rate (30 pts), Investment Activity (25 pts), Insurance Coverage (20 pts), and Spending Discipline (25 pts).
- **Automated Gap Identification:**
  - `NO_INVESTMENT`: High income (>₹6L) + zero investment activity $\rightarrow$ SIP / Mutual Fund offer.
  - `NO_INSURANCE`: Age > 30 + dependent signals + no insurance txns $\rightarrow$ Term / Health Insurance.
  - `NO_EMERGENCY_FUND`: Low savings rate (<10%) + zero fixed deposits $\rightarrow$ Auto-Sweep FD / Savings.
  - `OVERSPENDING_DINING`: Dining spend > 15% of net income $\rightarrow$ Dining Cashback Credit Card.
  - `FREQUENT_TRAVELLER_NO_CARD`: Travel spend > 15% without a dedicated co-branded travel card $\rightarrow$ Premium Travel Card.
  - `RENT_BURDEN`: High recurring rent debits (>35% income) $\rightarrow$ Home Loan assistance.

### 3.3 Real-Time Event Engine
- Scans rolling transactions to detect life events: **Flight bookings, hotel reservations, international currency exchange, medical emergencies, annual salary increments, and major milestone purchases**.
- Emits high-priority event triggers consumed immediately by the recommendation pipeline.

### 3.4 Next Best Offer (NBO) & Eligibility Decisioning
- **Strict Two-Stage Filtering:**
  1. *Hard Eligibility Gate:* Filters by minimum income, age brackets, minimum credit score, KYC compliance, and existing product holdings.
  2. *Product Fit Scoring:* Computes a multi-factor behavioral fit score using cosine/tag alignment between transaction patterns and bank product specs.
- **Ensemble Ranking:** Ranks opportunities using weighted parameters (`nbo_weights.yaml`) balancing customer benefit, profitability, and gap urgency.

### 3.5 Marketing Guard & Consent Safety Gate
- **Hard Gate Enforcement (`marketing_guard.py`):**
  - Verifies explicit customer DND (Do-Not-Disturb) and marketing consent.
  - **Campaign Fatigue Limits:** Enforces cooldown windows (e.g., max 2 campaigns/month, 7-day spacing between touches).
  - **Channel Optimization:** Selects preferred channel (Email / SMS / Mobile Push) based on historical open and click rates.

### 3.6 Context-Aware GenAI Copywriting
- **Powered by Groq LLM (Llama 3 / Mixtral):**
  - Ingests exact financial facts (actual monthly earnings, exact category spend, detected gaps).
  - **Time & Day-Aware Personalization:** Dynamically alters greeting and tone based on day-of-week and time-of-day (e.g., weekend dining context vs. weekday investment context).
  - **Generational Cohort Adaptation:**
    - *Gen Z:* Snappy, value-first, mobile-centric tone.
    - *Millennial:* Goal-oriented, wealth-building, balanced copy.
    - *Gen X / Boomers:* Security-focused, comprehensive, professional language.
  - Deterministic fallback generator when LLM API keys are unavailable.

### 3.7 Closed-Loop Campaign Studio & Analytics
- Bank managers can review AI recommendations, inspect the full mathematical evidence trail, customize messaging, and launch single or batch campaigns.
- Real-time funnel tracking: **Sent $\rightarrow$ Delivered $\rightarrow$ Opened $\rightarrow$ Clicked $\rightarrow$ Applied $\rightarrow$ Converted**.

### 3.8 Banking Chatbot & Semantic Search (RAG)
- Standalone `/chatbot` module integrating **FastEmbed embeddings** and **Qdrant vector database** for multi-turn customer queries and HDFC/NPN product knowledge retrieval.

---

## 4. Backend & Redis Architecture

### 4.1 Backend Service Design
The backend is built with **FastAPI** (`Python/api_server.py`) and organized into isolated, single-responsibility engines inside `Python/ai_engine/`:

| Module | Primary Responsibility |
|---|---|
| `data_loader.py` | Dual-source ingestion (Supabase PostgreSQL + local CSV fallback). |
| `feature_engine.py` | Normalization, merchant MCC tagging, and 7/30/60/90/180/365-day rolling windows. |
| `behavior_engine.py` | Monthly cash flow trajectory, income volatility, and expense velocity. |
| `event_engine.py` | Real-time threshold matching for milestone financial transactions. |
| `financial_analyst.py` | Gap detection rules, financial health index calculation, and benchmark analysis. |
| `eligibility_engine.py` | Non-negotiable regulatory and credit qualification rules. |
| `product_fit_engine.py` | Mathematical relevance matching against bank product catalogs. |
| `nbo_engine.py` | Multi-objective NBO optimization and top-1 product selection. |
| `explainability_engine.py` | Deterministic evidence generator for regulatory auditability. |
| `marketing_guard.py` | Compliance, DND verification, cooldowns, and anti-fatigue limits. |
| `genai_service.py` | Prompt engineering, time context injection, and Groq LLM execution. |

### 4.2 Redis Caching & Event Layer
Redis is integrated into the system architecture to deliver **sub-millisecond latency** and support distributed banking workloads:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           REDIS CACHE TOPOLOGY                          │
├────────────────────────────────┬────────────────────────────────────────┤
│ Key Namespace Pattern          │ Purpose & Eviction Strategy            │
├────────────────────────────────┼────────────────────────────────────────┤
│ c360:profile:{customer_id}     │ Serialized Customer 360 Feature Set    │
│                                │ (TTL: 15 min / Evict on new txn)       │
│ nbo:recommendation:{cust_id}   │ Precomputed NBO result & audit trail   │
│                                │ (TTL: 1 hour)                          │
│ auth:token_blocklist:{jti}     │ Revoked JWT tokens for secure logout   │
│                                │ (TTL: Matches JWT expiry)              │
│ guard:fatigue:{customer_id}    │ Campaign touch counter & rate limiter  │
│                                │ (Sliding window rate limit)            │
│ analytics:campaign:{camp_id}   │ Real-time in-memory counters           │
│                                │ (INCR opens/clicks/conversions)        │
│ pubsub:banking_events          │ Event bus for real-time transaction    │
│                                │ streaming into Event Engine            │
└────────────────────────────────┴────────────────────────────────────────┘
```

#### Why Redis is Essential for this Architecture:
1. **Low-Latency Dashboard Loading:** Pre-aggregating transaction features for thousands of customers and caching Customer 360 summaries reduces database I/O by >85%.
2. **Atomic Rate-Limiting & Fatigue Protection:** Using Redis atomic increment operations (`INCR`, `EXPIRE`) guarantees that no customer receives duplicate marketing blasts even across concurrent microservices.
3. **Decoupled Analytics Ingestion:** High-volume email open and click webhooks hit Redis counters before asynchronous batch persistence to PostgreSQL/Supabase.

---

## 5. Project Directory Structure

```text
NPN_Cognizant/
├── AI_service.md                     # Deep Financial Intelligence RFC & specifications
├── GenAI_Banking_Marketing_README.md # Full banking marketing technical documentation
├── stats.json                        # Dataset and campaign aggregate baseline statistics
│
├── Python/                           # ── Python AI Engine & API Backend ──
│   ├── api_server.py                 # FastAPI REST API Server (JWT, Endpoints, Router)
│   ├── requirements.txt              # Backend dependencies (FastAPI, Groq, Supabase, Pandas)
│   ├── run_pipeline.py               # Standalone CLI runner for Customer 360 & NBO
│   ├── generate_database.py          # Synthetic banking dataset generator
│   ├── push_to_supabase.py           # Database migration to Supabase PostgreSQL
│   ├── ai_engine/                    # Modular AI & analytics engines
│   │   ├── feature_engine.py         # Rolling-window feature extraction & normalization
│   │   ├── behavior_engine.py        # Spending behavior & income trajectory
│   │   ├── event_engine.py           # Real-time event detection triggers
│   │   ├── financial_analyst.py      # Gap detection & Financial Health Scorer (0-100)
│   │   ├── eligibility_engine.py     # Hard eligibility & product constraints
│   │   ├── product_fit_engine.py     # Product behavioral fit scoring
│   │   ├── nbo_engine.py             # Next Best Offer ranking algorithm
│   │   ├── explainability_engine.py  # Regulatory audit trails & structured reasons
│   │   ├── marketing_guard.py        # Consent, frequency capping, & safety gate
│   │   ├── genai_service.py          # Groq LLM integration & prompt packaging
│   │   ├── segmentation.py           # Customer lifecycle & behavioral segmentation
│   │   ├── data_loader.py            # Supabase / CSV data access layer
│   │   └── config/                   # YAML decision rules & thresholds
│   │       ├── marketing.yaml        # Cooldown intervals & contact frequency limits
│   │       ├── nbo_weights.yaml      # Multi-objective NBO ranking weights
│   │       └── thresholds.yaml       # Financial benchmarks & gap thresholds
│   └── Database_csvs/                # Synthetic banking dataset CSV files
│       ├── customers.csv             # Customer demographic profiles
│       ├── raw_transactions.csv      # Multi-category transaction histories
│       ├── credit_card_products.csv  # Bank credit card catalog
│       ├── debit_card_products.csv   # Bank debit card catalog
│       ├── loan_products.csv         # Retail loan offerings (Home, Personal, Auto)
│       ├── investment_products.csv   # Mutual funds, SIPs, and Fixed Deposits
│       └── insurance_products.csv    # Life, Health, and Motor insurance policies
│
├── frontend/                         # ── React 19 Employee Dashboard ──
│   ├── package.json                  # Frontend dependencies (React 19, Vite, Tailwind v4)
│   ├── vite.config.ts                # Vite configuration
│   └── src/
│       ├── main.jsx                  # React application entry point
│       ├── App.jsx                   # Layout, router, and navigation shell
│       ├── pages/
│       │   ├── Login.jsx             # Employee authentication screen
│       │   ├── Dashboard.jsx         # Executive metrics & real-time alerts
│       │   ├── Customers.jsx         # Searchable customer directory & filters
│       │   ├── Customer360.jsx       # Deep-dive analytics, gap reports, & NBO preview
│       │   ├── Campaigns.jsx         # Campaign creation & AI copy generation studio
│       │   ├── CampaignAnalytics.jsx # Funnel metrics (opens, clicks, conversions)
│       │   ├── Segments.jsx          # Customer segment distribution & demographics
│       │   └── Analytics.jsx         # Portfolio-wide financial health analytics
│       ├── services/                 # API client & fetch wrappers
│       └── contexts/                 # React state & Auth context providers
│
└── chatbot/                          # ── Standalone Banking Assistant & RAG ──
    └── README.md                     # FastEmbed + Qdrant + FastAPI Chatbot module guide
```

---

## 6. End-to-End AI Engine Pipeline

The AI Engine executes an 11-step pipeline for every customer analysis request:

```
[Raw Customer Data + Transactions + Holdings]
                      │
                      ▼
 1. DATA INGESTION (`data_loader.py`)
    ├── Reads Supabase PostgreSQL or local CSV fallback
    └── Normalizes merchant codes, timestamps, and debit/credit amounts
                      │
                      ▼
 2. ROLLING-WINDOW FEATURE COMPUTATION (`feature_engine.py`)
    ├── 7, 30, 60, 90, 180, 365-day rolling totals & velocity
    └── Produces structured `CustomerFeatureSet`
                      │
                      ▼
 3. BEHAVIORAL & CASH FLOW PROFILING (`behavior_engine.py`)
    ├── Monthly net savings rate & expense-to-income ratios
    └── Category spend distributions (Dining, Shopping, Travel, etc.)
                      │
                      ▼
 4. REAL-TIME EVENT DETECTION (`event_engine.py`)
    └── Detects flight payments, salary hikes, large debits, medical bills
                      │
                      ▼
 5. FINANCIAL ANALYST & GAP DETECTION (`financial_analyst.py`)
    ├── Calculates Financial Health Score (0-100)
    └── Identifies gaps (e.g. `NO_INVESTMENT`, `OVERSPENDING_DINING`)
                      │
                      ▼
 6. HARD ELIGIBILITY FILTERING (`eligibility_engine.py`)
    └── Discards products where customer fails age, income, or existing ownership rules
                      │
                      ▼
 7. BEHAVIORAL PRODUCT FIT SCORING (`product_fit_engine.py`)
    └── Computes fit score between customer behavior tags and product features
                      │
                      ▼
 8. NEXT BEST OFFER RANKING (`nbo_engine.py`)
    └── Weighted ensemble ranking $\rightarrow$ Selects winning recommendation
                      │
                      ▼
 9. AUDIT & EXPLAINABILITY PACKAGING (`explainability_engine.py`)
    └── Formulates deterministic, auditable bullet points (no LLM hallucinations)
                      │
                      ▼
10. MARKETING SAFETY CHECK (`marketing_guard.py`)
    ├── Verifies DND status, consent flags, and campaign fatigue cooldowns
    └── If blocked: Aborts outreach / logs safety reason
                      │
                      ▼
11. CONTEXT-AWARE GENAI GENERATION (`genai_service.py`)
    └── Passes exact numbers, time context, and age cohort to Groq LLM
                      │
                      ▼
[Personalized Campaign Offer Displayed on Dashboard]
```

---

## 7. API Reference

All protected endpoints require an `Authorization: Bearer <token>` header obtained via `/auth/login`.

### Authentication
- `POST /auth/login` — Authenticate employee credentials; returns JWT token, employee role, and profile.

### Dashboard & Metrics
- `GET /api/dashboard/stats` — High-level KPI metrics (total customers, total campaigns, active offers, conversion rates).
- `GET /api/analytics` — Portfolio-level distribution of financial health scores, income brackets, and category spending.

### Customer Intelligence
- `GET /api/customers` — Paginated list of bank customers with quick filters (search, segment, risk rating).
- `GET /api/customers/{customer_id}/analyze` — Executes full AI Engine pipeline for a specific customer; returns Customer 360 profile, detected gaps, health score, NBO recommendation, and explainability trail.
- `GET /api/customers/{customer_id}/holdings` — Returns current credit cards, debit cards, loans, and investment accounts.

### Campaign Management & AI Generation
- `POST /api/campaigns` — Create and schedule a new marketing campaign (single or batch).
- `GET /api/campaigns` — List all historical and active campaigns with performance summaries.
- `PATCH /api/campaigns/{campaign_id}/status` — Update campaign lifecycle state (`Active`, `Draft`, `Completed`).
- `GET /api/campaigns/{product}/customers` — Fetch all eligible NBO customers for a selected bank product.
- `POST /api/campaigns/generate-personalised-message` — Generate Groq LLM dynamic copy for a specific customer, product, and channel.
- `POST /api/campaigns/generate-content` — Generate cohort-based general marketing copy.

### Campaign Analytics & Closed-Loop Tracking
- `POST /api/campaigns/{campaign_id}/analytics/event` — Ingest interaction events (`opened`, `clicked`, `applied`, `converted`).
- `GET /api/campaigns/{campaign_id}/analytics` — Detailed funnel breakdown and conversion rates for a specific campaign.
- `GET /api/campaigns/insights` — AI-powered insights on campaign ROI and optimal engagement channels.

### Customer Segments & Health
- `GET /api/segments` — Summary of customer distribution across lifecycle and behavioral segments.
- `GET /health` — API service health check.

---

## 8. Technology Stack

| Domain | Technologies & Libraries |
|---|---|
| **Backend Framework** | Python 3.10+, FastAPI, Uvicorn, Pydantic v2 |
| **Authentication & Security** | OAuth2 Password Bearer, Jose (JWT), Passlib (SHA256 Crypt) |
| **AI / Machine Learning** | Scikit-learn, Pandas, NumPy, Groq API (Llama 3 / Mixtral) |
| **Caching & Event Management**| Redis (In-Memory Caching, Rate Limiting, Pub/Sub) |
| **Database & ORM** | PostgreSQL, Supabase Python Client, SQLAlchemy, Psycopg2 |
| **Frontend Framework** | React 19, Vite, React Router DOM |
| **Styling & Animation** | Tailwind CSS v4, Lucide React, Framer Motion |
| **Data Visualization** | Recharts |
| **Vector Store & Chatbot** | Qdrant, FastEmbed (Embeddings & Semantic Search) |
| **Configuration** | PyYAML, Python-Dotenv |

---

## 9. Setup & Installation Guide

### 9.1 Prerequisites
Ensure you have the following installed on your machine:
- **Python 3.10+**
- **Node.js 18+ & npm** (or Bun)
- **Redis Server** (optional for local mock mode, required for full caching layer)
- **Git**

### 9.2 Environment Configuration

Create a `.env` file inside the `Python/` directory:

```env
# Python/.env
SECRET_KEY=npnbank-super-secret-key-2024
ACCESS_TOKEN_EXPIRE_MINUTES=480

# Groq GenAI API (Optional - uses robust fallback if omitted)
GROQ_API_KEY=your_groq_api_key_here

# Supabase Configuration (Optional - falls back to local CSVs)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# Redis Configuration (Optional - defaults to localhost:6379)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
```

Create a `.env` file inside the `frontend/` directory:

```env
# frontend/.env
VITE_API_BASE_URL=http://localhost:8000
```

---

### 9.3 Backend Setup

1. Navigate to the `Python/` directory:
   ```bash
   cd Python
   ```
2. Create and activate a Python virtual environment:
   ```bash
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # macOS / Linux
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

### 9.4 Frontend Setup

1. Navigate to the `frontend/` directory:
   ```bash
   cd ../frontend
   ```
2. Install npm packages:
   ```bash
   npm install
   ```

---

### 9.5 Chatbot Setup (Optional)

1. Navigate to the `chatbot/` directory:
   ```bash
   cd ../chatbot
   ```
2. Follow instructions in `chatbot/README.md` for FastEmbed and Qdrant setup.

---

## 10. Running the Platform

### Step 1: Start the Backend API Server
From the `Python/` directory:
```bash
# Windows / Linux
uvicorn api_server:app --reload --port 8000
```
*The FastAPI interactive Swagger documentation will be accessible at [http://localhost:8000/docs](http://localhost:8000/docs).*

### Step 2: Start the Frontend Dashboard
From the `frontend/` directory:
```bash
npm run dev
```
*The React Dashboard will be available at [http://localhost:3000](http://localhost:3000) or [http://localhost:5173](http://localhost:5173).*

### Step 3: Log In to the Dashboard
Use the default prototype employee credentials:
- **Email:** `employee@npnbank.com`
- **Password:** `npnbank@2024`
- *(Or Senior Manager: `manager@npnbank.com` / `manager@2024`)*

---

## 11. Testing & Verification

### Running the CLI AI Pipeline Runner
To verify the complete 11-step AI intelligence pipeline on a sample customer from the terminal:
```bash
cd Python
python ai_engine/run_pipeline.py CUST00125
```

### Running Backend Unit & Endpoint Tests
```bash
cd Python
python test_api.py
python test_json_parse.py
```

### Validating Gap Detection Scenarios
- **Scenario A (No Investments):** Analyze customer `CUST00125` (Salaried software engineer earning ₹12L/yr with zero investment debits) $\rightarrow$ Expected output: Flag `NO_INVESTMENT` gap with SIP / Mutual Fund recommendation.
- **Scenario B (High Dining Spend):** Analyze customer with >15% food spend $\rightarrow$ Expected output: Flag `OVERSPENDING_DINING` gap with Dining Cashback Card recommendation.

---

## 12. Contributing & Pull Request Guidelines

We welcome contributions from all team members! Please adhere to the following workflow:

1. **Branch Naming Conventions:**
   - `feature/<name>-<feature-description>` (e.g., `feature/kartik-redis-caching`)
   - `fix/<name>-<bug-description>` (e.g., `fix/sarthak-schema-alignment`)
   - `docs/<name>-<docs-update>`
2. **Coding Standards:**
   - Backend: Follow PEP 8 guidelines and include explicit type hints (`typing`).
   - Engines: Ensure all analytical modules handle null/missing data gracefully without throwing unhandled exceptions.
   - Frontend: Maintain component modularity in `frontend/src/pages/` and utilize Tailwind CSS design tokens.
3. **Pull Request Checklist:**
   - [ ] Local pipeline test (`run_pipeline.py`) passes without errors.
   - [ ] FastAPI endpoints verified via Swagger UI (`/docs`).
   - [ ] Environment variables updated in `.env.example` if new keys are added.
   - [ ] Clean git commit history with descriptive commit messages.

---

##  Project Team & Acknowledgments

- **Backend, System Architecture & Redis Implementation:** Backend Engineering Team
- **AI Engine & Financial Decisioning:** Analytics & Intelligence Team
- **Frontend Dashboard & UI/UX:** Frontend Engineering Team
- **Database & Data Pipeline:** Data Engineering Team
- **Chatbot & Semantic Embeddings:** Conversational AI Team

*Built for NPN Bank — Cognizant Technology Solutions.*
