"""
NPN Bank — Employee Dashboard API Server
=========================================
FastAPI server that wraps the Python AI engine and exposes REST APIs
for the bank employee dashboard frontend.

Run:
    cd Python/ai_engine && uvicorn ../api_server:app --reload --port 8000
    OR from Python/:
    uvicorn api_server:app --reload --port 8000
"""

import sys
import os
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, List
import math

# ── Path setup so ai_engine modules resolve ──────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AI_ENGINE_DIR = os.path.join(BASE_DIR, "ai_engine")
sys.path.insert(0, AI_ENGINE_DIR)

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.hash import sha256_crypt
from dotenv import load_dotenv

load_dotenv(os.path.join(BASE_DIR, ".env"))

# ── AI Engine imports ─────────────────────────────────────────────────────────
from ai_engine.data_loader import (
    load_customers, 
    load_transactions, 
    load_credit_cards, 
    load_loan_products, 
    load_investment_products,
    load_insurance_products,
    load_customer_holdings
)
from ai_engine.feature_engine import FeatureEngine
from ai_engine.behavior_engine import BehaviorEngine
from ai_engine.event_engine import EventEngine
from ai_engine.segmentation import SegmentationEngine
from ai_engine.nbo_engine import NBOEngine
from ai_engine.genai_service import GenAIService
from ai_engine.financial_analyst import FinancialAnalyst
from ai_engine.explainability_engine import ExplainabilityEngine
from ai_engine.marketing_guard import MarketingGuard

# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="NPN Bank Employee Dashboard API",
    description="Internal API for bank employees to analyse customers and launch campaigns",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://127.0.0.1:5173", 
        "http://localhost:5174", 
        "http://localhost:5175", 
        "http://localhost:5176", 
        "http://localhost:3000"
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:[0-9]+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Auth config ───────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "npnbank-super-secret-key-2024")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Hardcoded employee accounts (prototype)
EMPLOYEES = {
    "employee@npnbank.com": {
        "name": "Priya Sharma",
        "role": "Relationship Manager",
        "hashed_password": pwd_context.hash("npnbank@2024"),
    },
    "manager@npnbank.com": {
        "name": "Rahul Verma",
        "role": "Senior Manager",
        "hashed_password": pwd_context.hash("manager@2024"),
    },
}

# ── In-memory campaign store ──────────────────────────────────────────────────
CAMPAIGNS: List[dict] = []

# ── Lazy-loaded data / engines ────────────────────────────────────────────────
_data_cache = {}

def get_engines():
    """Lazily load data and initialise engines (cached after first call)."""
    if not _data_cache:
        print("Loading data and initialising AI engines v3.0...")
        customers_df    = load_customers()
        transactions_df = load_transactions()
        credit_cards_df = load_credit_cards()
        loans_df        = load_loan_products()
        investments_df  = load_investment_products()
        insurance_df    = load_insurance_products()
        holdings_data   = load_customer_holdings()

        _data_cache["customers_df"]    = customers_df
        _data_cache["transactions_df"] = transactions_df
        _data_cache["holdings_data"]   = holdings_data
        
        # v3 Engines
        _data_cache["feature_engine"]    = FeatureEngine(transactions_df, holdings_data)
        _data_cache["behavior_engine"]   = BehaviorEngine(transactions_df)
        _data_cache["event_engine"]      = EventEngine(transactions_df)
        _data_cache["seg_engine"]        = SegmentationEngine()
        _data_cache["financial_analyst"] = FinancialAnalyst()
        _data_cache["nbo_engine"]        = NBOEngine(credit_cards_df, loans_df, investments_df, insurance_df)
        _data_cache["explain_engine"]    = ExplainabilityEngine()
        _data_cache["marketing_guard"]   = MarketingGuard()
        _data_cache["genai_service"]     = GenAIService()
        
        print("Engines ready.")
    return _data_cache


# ═══════════════════════════════════════════════════════════════════════════════
# Pydantic models
# ═══════════════════════════════════════════════════════════════════════════════

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    employee_name: str
    employee_role: str
    employee_email: str


class CampaignCreate(BaseModel):
    customer_id: str
    customer_name: str
    product: str
    campaign_name: str
    description: str
    channel: str           # Email | SMS | App Notification
    message_preview: str


class Campaign(BaseModel):
    id: str
    customer_id: str
    customer_name: str
    product: str
    campaign_name: str
    description: str
    channel: str
    message_preview: str
    status: str            # Active | Draft | Completed
    created_at: str
    created_by: str


class CampaignGenerateContent(BaseModel):
    product: str
    segment: str
    tone: Optional[str] = "Professional"


# ═══════════════════════════════════════════════════════════════════════════════
# Auth helpers
# ═══════════════════════════════════════════════════════════════════════════════

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_employee(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None or email not in EMPLOYEES:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return {"email": email, **EMPLOYEES[email]}


# ═══════════════════════════════════════════════════════════════════════════════
# Auth endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/auth/login", response_model=TokenResponse, tags=["Auth"])
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate a bank employee and return a JWT token."""
    emp = EMPLOYEES.get(form_data.username)
    if not emp or not pwd_context.verify(form_data.password, emp["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(
        data={"sub": form_data.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        employee_name=emp["name"],
        employee_role=emp["role"],
        employee_email=form_data.username,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Dashboard endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/dashboard/stats", tags=["Dashboard"])
def get_dashboard_stats(current_employee=Depends(get_current_employee)):
    """
    Returns aggregate statistics for the dashboard.
    """
    eng = get_engines()
    customers_df = eng["customers_df"]
    seg_engine   = eng["seg_engine"]
    feature_engine = eng["feature_engine"]

    total_customers = len(customers_df)

    def income_bucket(income):
        if income < 500000: return "< ₹5L"
        elif income < 1000000: return "₹5L–₹10L"
        elif income < 2000000: return "₹10L–₹20L"
        else: return "> ₹20L"

    income_dist = {}
    for _, row in customers_df.iterrows():
        bucket = income_bucket(row.get("annual_income", 0))
        income_dist[bucket] = income_dist.get(bucket, 0) + 1

    sample = customers_df.head(200)
    segment_dist = {}
    for _, row in sample.iterrows():
        cust_data = row.to_dict()
        features = feature_engine.compute(row["customer_id"], cust_data)
        segs = seg_engine.segment_customer(cust_data, features)
        for s in segs:
            segment_dist[s] = segment_dist.get(s, 0) + 1

    credit_avg = round(float(customers_df["credit_score"].mean()), 0) if "credit_score" in customers_df.columns else 0

    return {
        "total_customers": total_customers,
        "total_campaigns": len(CAMPAIGNS),
        "active_campaigns": sum(1 for c in CAMPAIGNS if c["status"] == "Active"),
        "avg_credit_score": credit_avg,
        "income_distribution": income_dist,
        "segment_distribution": segment_dist,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Customer endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/customers", tags=["Customers"])
def list_customers(
    search: Optional[str] = None,
    segment: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_employee=Depends(get_current_employee),
):
    """List all customers with basic info. Supports search by name/ID."""
    eng = get_engines()
    customers_df = eng["customers_df"]

    cols = ["customer_id", "first_name", "last_name", "annual_income",
            "credit_score", "age", "employment_type", "customer_segment_type",
            "email", "city"]
    available_cols = [c for c in cols if c in customers_df.columns]
    df = customers_df[available_cols].copy()

    if search:
        q = search.lower()
        mask = (
            df["customer_id"].str.lower().str.contains(q, na=False) |
            df["first_name"].str.lower().str.contains(q, na=False) |
            df["last_name"].str.lower().str.contains(q, na=False)
        )
        df = df[mask]

    total = len(df)
    df = df.iloc[offset: offset + limit]

    return {
        "total": total,
        "customers": df.to_dict(orient="records"),
    }


@app.get("/api/customers/{customer_id}/analyze", tags=["Customers"])
def analyze_customer(
    customer_id: str,
    current_employee=Depends(get_current_employee),
):
    """
    Run the full AI pipeline v2 for a single customer.
    """
    eng = get_engines()
    customers_df      = eng["customers_df"]
    feature_engine    = eng["feature_engine"]
    behavior_engine   = eng["behavior_engine"]
    event_engine      = eng["event_engine"]
    financial_analyst = eng["financial_analyst"]
    seg_engine        = eng["seg_engine"]
    nbo_engine        = eng["nbo_engine"]
    explain_engine    = eng["explain_engine"]
    marketing_guard   = eng["marketing_guard"]
    genai_service     = eng["genai_service"]

    customer_row = customers_df[customers_df["customer_id"] == customer_id]
    if customer_row.empty:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    customer_data = customer_row.iloc[0].to_dict()

    # 1. Features
    features = feature_engine.compute(customer_id, customer_data)

    # 2. Behavior & Events
    behavior = behavior_engine.analyze_behavior_v2(customer_id, features)
    events   = event_engine.detect_events(customer_id, features)

    # 3. Financial Analysis
    financial_analysis = financial_analyst.analyse(customer_id, customer_data, features)
    financial_gaps     = financial_analysis.get("gaps", [])

    # 4. Segments
    segments = seg_engine.segment_customer(customer_data, features)

    # 5. NBO
    nbo = nbo_engine.determine_next_best_offer(
        features=features,
        events=events,
        financial_gaps=financial_gaps,
        customer_data=customer_data
    )

    # 6. Explainability
    explanation = explain_engine.explain(
        nbo_candidate=nbo.get("full_result", {}),
        features=features,
        events=events,
        financial_gaps=financial_gaps,
        customer_data=customer_data
    )

    # 7. Marketing Guard
    marketing_check = marketing_guard.check(
        customer_data=customer_data,
        product_result=nbo.get("full_result", {}),
        campaign_history=[]
    )

    # 8. GenAI
    genai_msg = ""
    if marketing_check.get("allowed"):
        channel = marketing_check.get("recommended_channel", "email")
        genai_msg = genai_service.generate_marketing_message(
            customer_data=customer_data,
            nbo_result=nbo,
            explanation=explanation,
            channel=channel,
            features=features  # Pass full feature set for portfolio context
        )

    def serialise(obj):
        if isinstance(obj, float):
            if math.isnan(obj) or math.isinf(obj): return None
            return obj
        if hasattr(obj, "item"):
            val = obj.item()
            if isinstance(val, float) and (math.isnan(val) or math.isinf(val)): return None
            return val
        if hasattr(obj, "__dict__"): # handle CustomerFeatureSet
            return serialise(obj.__dict__)
        if isinstance(obj, dict):
            return {k: serialise(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [serialise(i) for i in obj]
        return obj

    return serialise({
        "customer": customer_data,
        "behavior": behavior,
        "events": events,
        "segments": segments,
        "financial_analysis": financial_analysis,
        "nbo": nbo,
        "explanation": explanation,
        "marketing_check": marketing_check,
        "genai_message": genai_msg,
        "holdings_summary": {
            "has_insurance": features.has_insurance,
            "has_health_insurance": features.has_health_insurance,
            "has_life_insurance": features.has_life_insurance,
            "has_investments": features.has_investments,
            "has_home_loan": features.has_home_loan,
            "has_personal_loan": features.has_personal_loan,
            "held_card_names": features.held_card_names,
            "held_loan_categories": features.held_loan_categories,
            "held_investment_categories": features.held_investment_categories,
            "held_insurance_categories": features.held_insurance_categories,
            "total_emi_monthly": features.total_emi_monthly,
            "total_sip_monthly": features.total_sip_monthly,
            "total_assets_value": features.total_assets_value,
            "total_outstanding_debt": features.total_outstanding_debt,
            "net_worth_indicator": features.net_worth_indicator,
        },
    })


@app.get("/api/customers/{customer_id}/holdings", tags=["Customers"])
def get_customer_holdings(
    customer_id: str,
    current_employee=Depends(get_current_employee),
):
    """
    Get the full Customer 360 raw holdings for a customer.
    """
    eng = get_engines()
    customers_df = eng["customers_df"]
    feature_engine = eng["feature_engine"]
    
    customer_row = customers_df[customers_df["customer_id"] == customer_id]
    if customer_row.empty:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    customer_data = customer_row.iloc[0].to_dict()
    features = feature_engine.compute(customer_id, customer_data)

    def serialise(obj):
        import math
        if isinstance(obj, float):
            if math.isnan(obj) or math.isinf(obj): return None
            return obj
        if hasattr(obj, "item"):
            val = obj.item()
            if isinstance(val, float) and (math.isnan(val) or math.isinf(val)): return None
            return val
        if isinstance(obj, dict):
            return {k: serialise(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [serialise(i) for i in obj]
        return obj

    return serialise(features.holdings)


# ═══════════════════════════════════════════════════════════════════════════════
# Campaign endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/campaigns", tags=["Campaigns"])
def create_campaign(
    campaign: CampaignCreate,
    current_employee=Depends(get_current_employee),
):
    """Create and launch a new marketing campaign."""
    new_campaign = {
        "id": str(uuid.uuid4())[:8].upper(),
        "customer_id": campaign.customer_id,
        "customer_name": campaign.customer_name,
        "product": campaign.product,
        "campaign_name": campaign.campaign_name,
        "description": campaign.description,
        "channel": campaign.channel,
        "message_preview": campaign.message_preview,
        "status": "Active",
        "created_at": datetime.now().isoformat(),
        "created_by": current_employee["name"],
    }
    CAMPAIGNS.insert(0, new_campaign)
    return new_campaign


@app.get("/api/campaigns", tags=["Campaigns"])
def list_campaigns(current_employee=Depends(get_current_employee)):
    """List all campaigns."""
    return {"campaigns": CAMPAIGNS}


@app.patch("/api/campaigns/{campaign_id}/status", tags=["Campaigns"])
def update_campaign_status(
    campaign_id: str,
    status_update: dict,
    current_employee=Depends(get_current_employee),
):
    """Update a campaign's status (Active | Draft | Completed)."""
    for c in CAMPAIGNS:
        if c["id"] == campaign_id:
            c["status"] = status_update.get("status", c["status"])
            return c
    raise HTTPException(status_code=404, detail="Campaign not found")


# ═══════════════════════════════════════════════════════════════════════════════
# Segments endpoint
# ═══════════════════════════════════════════════════════════════════════════════

SEGMENT_DEFINITIONS = [
    {
        "id": "seg-1",
        "name": "High Value",
        "engine_names": ["High-Value Customer", "Mass Affluent Customer"],
        "recommendedProduct": "Premium Account",
        "aiOpportunity": "Eligible for Wealth Tier upgrades",
        "color": "#2563EB",
        "description": "Affluent clients with high liquid assets and recurring high-ticket discretionary transactions.",
    },
    {
        "id": "seg-2",
        "name": "Frequent Travellers",
        "engine_names": ["Frequent Traveller"],
        "recommendedProduct": "Travel Credit Card",
        "aiOpportunity": "Customers with pending airline/hotel bookings",
        "color": "#7C3AED",
        "description": "Corporate and leisure globetrotters logging frequent international or cross-country trips.",
    },
    {
        "id": "seg-3",
        "name": "Investment Oriented",
        "engine_names": ["Investment Prospect"],
        "recommendedProduct": "SIP / Mutual Fund",
        "aiOpportunity": "Surplus liquidity holders ready for portfolio allocation",
        "color": "#059669",
        "description": "Financially disciplined customers maintaining high savings balances without active equity allocations.",
    },
    {
        "id": "seg-4",
        "name": "Loan Ready",
        "engine_names": ["Loan Prospect"],
        "recommendedProduct": "Personal Loan",
        "aiOpportunity": "High-credit-score clients seeking capital flexibility",
        "color": "#D97706",
        "description": "Strong credit history with recent home renovation or lifestyle milestone inquiries.",
    },
    {
        "id": "seg-5",
        "name": "Churn Risk",
        "engine_names": ["Standard Customer"],
        "recommendedProduct": "Credit Card",
        "aiOpportunity": "Customers salvageable via personalized fee waivers & loyalty multipliers",
        "color": "#DC2626",
        "description": "Accounts with declining monthly transactional velocity and lower login frequency.",
    },
]

@app.get("/api/segments", tags=["Segments"])
def get_segments(current_employee=Depends(get_current_employee)):
    eng = get_engines()
    customers_df    = eng["customers_df"]
    feature_engine  = eng["feature_engine"]
    seg_engine      = eng["seg_engine"]

    sample = customers_df.head(500)
    total_sampled = len(sample)
    total_customers = len(customers_df)

    seg_counts: dict = {s["name"]: 0 for s in SEGMENT_DEFINITIONS}
    seg_income_sum:  dict = {s["name"]: 0.0 for s in SEGMENT_DEFINITIONS}
    seg_spend_sum:   dict = {s["name"]: 0.0 for s in SEGMENT_DEFINITIONS}

    for _, row in sample.iterrows():
        cust_data = row.to_dict()
        features = feature_engine.compute(row["customer_id"], cust_data)
        engine_segs = seg_engine.segment_customer(cust_data, features)

        matched = False
        for seg_def in SEGMENT_DEFINITIONS:
            if any(es in engine_segs for es in seg_def["engine_names"]):
                seg_counts[seg_def["name"]] += 1
                income = features.monthly_income_avg * 12
                spend  = features.monthly_spend_avg_90d * 12
                seg_income_sum[seg_def["name"]] += float(income)
                seg_spend_sum[seg_def["name"]]  += float(spend)
                matched = True
                break
        if not matched:
            seg_counts["Churn Risk"] += 1

    scale = total_customers / total_sampled if total_sampled > 0 else 1

    result = []
    for seg_def in SEGMENT_DEFINITIONS:
        count = int(seg_counts[seg_def["name"]] * scale)
        raw_avg_spend = (seg_spend_sum[seg_def["name"]] / max(seg_counts[seg_def["name"]], 1)) / 12
        avg_spend_monthly = round(raw_avg_spend, 0)
        percentage = round(count / total_customers * 100, 1) if total_customers > 0 else 0

        result.append({
            "id":                 seg_def["id"],
            "name":               seg_def["name"],
            "count":              count,
            "percentage":         percentage,
            "avgSpending":        f"₹{avg_spend_monthly:,.0f}",
            "avgSpendingRaw":     avg_spend_monthly,
            "recommendedProduct": seg_def["recommendedProduct"],
            "aiOpportunity":      seg_def["aiOpportunity"],
            "color":              seg_def["color"],
            "description":        seg_def["description"],
        })

    return {"segments": result, "total": total_customers}


# ═══════════════════════════════════════════════════════════════════════════════
# Analytics endpoint
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/analytics", tags=["Analytics"])
def get_analytics(current_employee=Depends(get_current_employee)):
    total_campaigns = len(CAMPAIGNS)
    total_customers_reached = total_campaigns * 420 if total_campaigns > 0 else 8120

    funnel = [
        {"stage": "Audience",     "count": total_customers_reached,                "percentage": "100%",  "fill": "#3b82f6"},
        {"stage": "Delivered",    "count": int(total_customers_reached * 0.983),    "percentage": "98.3%", "fill": "#6366f1"},
        {"stage": "Opened",       "count": int(total_customers_reached * 0.679),    "percentage": "67.9%", "fill": "#8b5cf6"},
        {"stage": "Clicked CTA",  "count": int(total_customers_reached * 0.393),    "percentage": "39.3%", "fill": "#a855f7"},
        {"stage": "Applied",      "count": int(total_customers_reached * 0.226),    "percentage": "22.6%", "fill": "#f59e0b"},
        {"stage": "Converted",    "count": int(total_customers_reached * 0.0268),   "percentage": "2.68%", "fill": "#10b981"},
    ]

    from datetime import datetime, timedelta
    now = datetime.now()
    monthly_perf = []
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    for i in range(8):
        month_dt = now - timedelta(days=30 * (7 - i))
        month_label = months[month_dt.month - 1]
        base_sent = 400 + i * 120 + (total_campaigns * 15)
        monthly_perf.append({
            "month":     month_label,
            "sent":      base_sent,
            "converted": int(base_sent * (0.024 + i * 0.003)),
        })

    segment_conversion = [
        {"segment": "High Value",           "rate": 4.2,  "target": 3.5},
        {"segment": "Freq. Travellers",     "rate": 5.8,  "target": 4.0},
        {"segment": "Investment Orient.",   "rate": 4.9,  "target": 4.0},
        {"segment": "Loan Ready",           "rate": 3.8,  "target": 3.5},
        {"segment": "Churn Risk",           "rate": 2.1,  "target": 2.5},
    ]

    product_performance = [
        {"product": "Travel Credit Card", "offersSent": 2431, "conversions": 141, "conversionRate": 5.8,  "revenueLift": "₹2.84Cr"},
        {"product": "SIP / Mutual Fund",  "offersSent": 1240, "conversions":  61, "conversionRate": 4.9,  "revenueLift": "₹36.4Cr AUM"},
        {"product": "Personal Loan",      "offersSent":  890, "conversions":  34, "conversionRate": 3.8,  "revenueLift": "₹17.6Cr"},
        {"product": "Premium Account",    "offersSent": 1820, "conversions":  76, "conversionRate": 4.2,  "revenueLift": "₹8.56Cr"},
        {"product": "Credit Card",        "offersSent": 3210, "conversions":  67, "conversionRate": 2.1,  "revenueLift": "₹3.22Cr"},
    ]

    return {
        "funnel":              funnel,
        "monthly_performance": monthly_perf,
        "segment_conversion":  segment_conversion,
        "product_performance": product_performance,
        "summary": {
            "total_campaigns":    total_campaigns,
            "total_offers_sent":  sum(p["offersSent"] for p in product_performance),
            "total_conversions":  sum(p["conversions"] for p in product_performance),
            "avg_conversion_rate": 4.16,
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Campaign AI content generation endpoint
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/campaigns/generate-content", tags=["Campaigns"])
def generate_campaign_content(
    req: CampaignGenerateContent,
    current_employee=Depends(get_current_employee),
):
    eng = get_engines()
    genai_service = eng["genai_service"]

    segment_context = {
        "High Value":           {"income": 2500000, "first_name": f"{req.segment} Customer"},
        "Frequent Travellers":  {"income": 1200000, "first_name": f"{req.segment} Customer"},
        "Investment Oriented":  {"income": 1800000, "first_name": f"{req.segment} Customer"},
        "Loan Ready":           {"income": 800000,  "first_name": f"{req.segment} Customer"},
        "Churn Risk":           {"income": 600000,  "first_name": f"{req.segment} Customer"},
    }

    ctx = segment_context.get(req.segment, {"income": 1000000, "first_name": "Valued Customer"})

    customer_data = {
        "first_name":    ctx["first_name"],
        "annual_income": ctx["income"],
    }

    nbo_result = {
        "specific_product": req.product,
    }
    
    explanation = {
        "customer_reasons": [
            f"Customers in the {req.segment} segment show high propensity for {req.product}.",
            f"Tone: {req.tone or 'Professional'}."
        ]
    }

    raw_message = genai_service.generate_marketing_message(customer_data, nbo_result, explanation)

    # Parse subject, body, CTA from the returned text
    lines = raw_message.strip().split("\n")
    subject = ""
    body_lines = []
    cta = "Claim Offer"

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.lower().startswith("subject:"):
            subject = stripped[8:].strip()
        elif stripped.lower().startswith("cta:") or stripped.lower().startswith("call to action:"):
            cta = stripped.split(":", 1)[-1].strip()
        else:
            body_lines.append(line)

    body = "\n".join(body_lines).strip()
    if not subject and lines:
        subject = f"Exclusive {req.product} offer for {req.segment}"
    if not body:
        body = raw_message

    return {
        "subject": subject,
        "body":    body,
        "cta":     cta,
        "tone":    req.tone,
        "raw":     raw_message,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Health check
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "service": "NPN Bank Employee API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
