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
from data_loader import load_customers, load_transactions, load_credit_cards, load_loan_products
from behavior_engine import BehaviorEngine
from segmentation import SegmentationEngine
from nbo_engine import NBOEngine
from genai_service import GenAIService
from financial_analyst import FinancialAnalyst

# ── App setup ─────────────────────────────────────────────────────────────────
app = FastAPI(
    title="NPN Bank Employee Dashboard API",
    description="Internal API for bank employees to analyse customers and launch campaigns",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174"],
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
        print("Loading data and initialising AI engines...")
        customers_df    = load_customers()
        transactions_df = load_transactions()
        credit_cards_df = load_credit_cards()
        loans_df        = load_loan_products()

        _data_cache["customers_df"]    = customers_df
        _data_cache["transactions_df"] = transactions_df
        _data_cache["behavior_engine"]   = BehaviorEngine(transactions_df)
        _data_cache["seg_engine"]        = SegmentationEngine()
        _data_cache["financial_analyst"] = FinancialAnalyst(transactions_df)
        _data_cache["nbo_engine"]        = NBOEngine(credit_cards_df, loans_df)
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
    Returns aggregate statistics for the dashboard:
    - total customers
    - segment distribution
    - income tier distribution
    - campaigns count
    """
    eng = get_engines()
    customers_df = eng["customers_df"]
    seg_engine   = eng["seg_engine"]
    behavior_engine = eng["behavior_engine"]

    total_customers = len(customers_df)

    # Income distribution buckets
    def income_bucket(income):
        if income < 500000:
            return "< ₹5L"
        elif income < 1000000:
            return "₹5L–₹10L"
        elif income < 2000000:
            return "₹10L–₹20L"
        else:
            return "> ₹20L"

    income_dist = {}
    for _, row in customers_df.iterrows():
        bucket = income_bucket(row.get("annual_income", 0))
        income_dist[bucket] = income_dist.get(bucket, 0) + 1

    # Segment distribution (sample first 200 customers for speed)
    sample = customers_df.head(200)
    segment_dist = {}
    for _, row in sample.iterrows():
        cust_data = row.to_dict()
        behavior  = behavior_engine.analyze_behavior(row["customer_id"])
        segs      = seg_engine.segment_customer(cust_data, behavior)
        for s in segs:
            segment_dist[s] = segment_dist.get(s, 0) + 1

    # Credit score distribution
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

    # Search filter
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
    Run the full AI pipeline for a single customer.
    Returns: behavior, segments, financial analysis, propensities, NBO, GenAI message.
    """
    eng = get_engines()
    customers_df    = eng["customers_df"]
    behavior_engine = eng["behavior_engine"]
    seg_engine      = eng["seg_engine"]
    financial_analyst = eng["financial_analyst"]
    nbo_engine      = eng["nbo_engine"]
    genai_service   = eng["genai_service"]

    customer_row = customers_df[customers_df["customer_id"] == customer_id]
    if customer_row.empty:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    customer_data = customer_row.iloc[0].to_dict()

    # Run full pipeline
    behavior           = behavior_engine.analyze_behavior(customer_id)
    events             = behavior_engine.detect_events(customer_id)
    segments           = seg_engine.segment_customer(customer_data, behavior)
    financial_analysis = financial_analyst.analyse(customer_id, customer_data, behavior)
    financial_gaps     = financial_analysis.get("gaps", [])

    propensities = nbo_engine.calculate_propensity(
        customer_data, segments, events, financial_gaps=financial_gaps
    )
    nbo = nbo_engine.determine_next_best_offer(
        propensities, customer_data, events,
        financial_gaps=financial_gaps,
        financial_analysis=financial_analysis,
    )
    genai_msg = genai_service.generate_marketing_message(
        customer_data, nbo, financial_analysis=financial_analysis
    )

    # Serialise (convert numpy types and handle NaNs)
    import math
    def serialise(obj):
        if isinstance(obj, float):
            if math.isnan(obj) or math.isinf(obj):
                return None
            return obj
        if hasattr(obj, "item"):   # numpy scalar
            val = obj.item()
            if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
                return None
            return val
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
        "propensities": propensities,
        "nbo": nbo,
        "genai_message": genai_msg,
    })


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
# Health check
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/health", tags=["System"])
def health():
    return {"status": "ok", "service": "NPN Bank Employee API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
