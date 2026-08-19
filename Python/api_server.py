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
# ── Restart trigger ──
import os
import json
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone
from typing import Optional, List
import math
import logging
import pandas as pd

# ── Logger Setup ──
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Path setup so ai_engine modules resolve ──────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AI_ENGINE_DIR = os.path.join(BASE_DIR, "ai_engine")
sys.path.insert(0, AI_ENGINE_DIR)

from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.hash import sha256_crypt
from dotenv import load_dotenv

load_dotenv(os.path.join(BASE_DIR, ".env"))

# ── Gmail credentials for real email sending ─────────────────────────────────
GMAIL_SENDER = os.getenv("GMAIL_SENDER", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")

# ── Twilio credentials for real SMS sending ───────────────────────────────────
TWILIO_ACCOUNT_SID  = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN   = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")


# ── AI Engine imports ─────────────────────────────────────────────────────────
from ai_engine.data_loader import (
    load_customers, 
    load_transactions, 
    load_credit_cards, 
    load_loan_products, 
    load_investment_products,
    load_insurance_products,
    load_customer_holdings,
    load_customer_360_json,
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
from ai_engine.clustering_engine import ClusteringEngine
from ai_engine.indian_calendar import get_festival_context_for_prompt, get_campaign_suggestions_by_events
from marketing_templates import build_html_email, build_sms_body, pick_marketing_image

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
        "http://localhost:3000",
        "https://npnbank-backend.duckdns.org",
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:[0-9]+)?|https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Auth config ───────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "npnbank-super-secret-key-2024")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours


# ── Groq response cleaner (strips <think> blocks from qwen/reasoning models) ──
import re as _re_global

def _clean_groq_json(raw: str) -> str:
    """
    Strip <think>...</think> reasoning blocks, markdown code fences,
    and any leading/trailing whitespace — leaving pure JSON ready to parse.
    Works for qwen3.x, deepseek-r1, and any other chain-of-thought models.
    """
    # 1. Remove closed <think>...</think> blocks (may be multi-line)
    raw = _re_global.sub(r"<think>.*?</think>", "", raw, flags=_re_global.DOTALL)
    
    # 2. Handle UNCLOSED <think> block (model ran out of tokens while thinking)
    if "<think>" in raw:
        raw = raw[:raw.index("<think>")]
    if "</think>" in raw:
        raw = raw[raw.rindex("</think>") + len("</think>"):]
    
    raw = raw.strip()
    
    # 3. Strip markdown code fences
    raw = _re_global.sub(r"^```(?:json)?\s*", "", raw, flags=_re_global.MULTILINE)
    raw = _re_global.sub(r"```\s*$", "", raw, flags=_re_global.MULTILINE)
    raw = raw.strip()
    
    # 4. Robustly extract JSON object or array ignoring conversational preamble
    match = _re_global.search(r'(\{.*\}|\[.*\])', raw, flags=_re_global.DOTALL)
    if match:
        return match.group(1).strip()
        
    return raw


import json as _json_global

def _safe_parse_groq_json(raw_content: str, context: str = "") -> dict | list | None:
    """
    Clean Groq output and parse JSON. Returns None if parsing fails
    instead of raising — callers should use their fallback when None is returned.
    """
    try:
        cleaned = _clean_groq_json(raw_content or "")
        if not cleaned:
            print(f"[GROQ] Empty response after cleaning{' — ' + context if context else ''}")
            return None
        return _json_global.loads(cleaned)
    except Exception as e:
        print(f"[GROQ] JSON parse error{' — ' + context if context else ''}: {e}")
        # Log first 200 chars to help debug
        snippet = (raw_content or "")[:200].replace("\n", " ")
        print(f"[GROQ] Raw snippet: {snippet}")
        return None


# ── Token-safe prompt trimmer ─────────────────────────────────────────────────
# qwen/qwen3.6-27b context window = 32 768 tokens.
# Rule of thumb: 1 token ≈ 4 chars (English).  We budget:
#   - System message : ~200 tokens
#   - Output reserved: 1 200 tokens
#   - Input prompt   : max 6 400 tokens  →  ~25 600 chars
_PROMPT_MAX_CHARS = 25_600   # hard ceiling for any user-role prompt

def _trim_prompt(text: str, max_chars: int = _PROMPT_MAX_CHARS) -> str:
    """Truncate *text* to *max_chars* so we never blow the model context window."""
    if len(text) <= max_chars:
        return text
    # Keep the first 60 % and the last 40 % so the end (output schema) is preserved
    keep_head = int(max_chars * 0.6)
    keep_tail = max_chars - keep_head
    return text[:keep_head] + "\n...[content trimmed for length]...\n" + text[-keep_tail:]


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

# ── Database Connection for Campaigns ─────────────────────────────────────────
from sqlalchemy import create_engine, text

DB_URL_CAMPAIGNS = os.getenv("SUPABASE_DB_URL", "")
if DB_URL_CAMPAIGNS.startswith("postgres://"):
    DB_URL_CAMPAIGNS = DB_URL_CAMPAIGNS.replace("postgres://", "postgresql://", 1)
db_engine = create_engine(DB_URL_CAMPAIGNS) if DB_URL_CAMPAIGNS else None

def get_db_connection():
    if not db_engine:
        raise HTTPException(status_code=500, detail="Database not configured")
    return db_engine.connect()

import redis
import pickle

REDIS_URL = os.getenv("REDIS_URL")
redis_client = None
if REDIS_URL:
    try:
        redis_client = redis.Redis.from_url(REDIS_URL)
        redis_client.ping()
        print("Connected to Redis successfully.")
    except Exception as e:
        print(f"Warning: Failed to connect to Redis: {e}")
        redis_client = None

# ── Lazy-loaded data / engines ────────────────────────────────────────────────
_data_cache = {}
_engine_lock = __import__('threading').Lock()

def get_engines():
    """Lazily load data and initialise engines (cached after first call, thread-safe)."""
    if _data_cache:
        return _data_cache
    with _engine_lock:
        # Double-check inside lock in case another thread beat us here
        if _data_cache:
            return _data_cache
        cached_data = None
        if redis_client:
            try:
                cached_bytes = redis_client.get("npn_bank_data_bundle")
                if cached_bytes:
                    print("Loading data from Redis cache...")
                    cached_data = pickle.loads(cached_bytes)
            except Exception as e:
                print(f"Redis cache load error: {e}")

        if cached_data:
            customers_df    = cached_data["customers_df"]
            transactions_df = cached_data["transactions_df"]
            credit_cards_df = cached_data["credit_cards_df"]
            loans_df        = cached_data["loans_df"]
            investments_df  = cached_data["investments_df"]
            insurance_df    = cached_data["insurance_df"]
            holdings_data   = cached_data["holdings_data"]
            customer_360    = cached_data["customer_360"]
        else:
            print("Loading data from Supabase and initialising AI engines v3.0...")
            print("- load_customers...")
            customers_df    = load_customers()
            print(f"  -> Fetched {len(customers_df)} customers from Supabase")
            print("- load_transactions...")
            transactions_df = load_transactions()
            print("- load_credit_cards...")
            credit_cards_df = load_credit_cards()
            print("- load_loan_products...")
            loans_df        = load_loan_products()
            print("- load_investment_products...")
            investments_df  = load_investment_products()
            print("- load_insurance_products...")
            insurance_df    = load_insurance_products()
            print("- load_customer_holdings...")
            holdings_data   = load_customer_holdings()
            customer_360    = load_customer_360_json()

            if redis_client:
                try:
                    print("Saving data bundle to Redis (TTL = 4 hours)...")
                    bundle = {
                        "customers_df": customers_df,
                        "transactions_df": transactions_df,
                        "credit_cards_df": credit_cards_df,
                        "loans_df": loans_df,
                        "investments_df": investments_df,
                        "insurance_df": insurance_df,
                        "holdings_data": holdings_data,
                        "customer_360": customer_360
                    }
                    # 14400 seconds = 4 hours
                    redis_client.setex("npn_bank_data_bundle", 14400, pickle.dumps(bundle))
                except Exception as e:
                    print(f"Redis save error: {e}")

        _data_cache["customers_df"]    = customers_df
        _data_cache["transactions_df"] = transactions_df
        _data_cache["holdings_data"]   = holdings_data
        _data_cache["customer_360"]    = customer_360
        
        print("- Initialising v3 Engines...")
        print("  - FeatureEngine...")
        _data_cache["feature_engine"]    = FeatureEngine(transactions_df, holdings_data)
        print("  - BehaviorEngine...")
        _data_cache["behavior_engine"]   = BehaviorEngine(transactions_df)
        print("  - EventEngine...")
        _data_cache["event_engine"]      = EventEngine(transactions_df)
        print("  - SegmentationEngine...")
        _data_cache["seg_engine"]        = SegmentationEngine()
        print("  - FinancialAnalyst...")
        _data_cache["financial_analyst"] = FinancialAnalyst()
        print("  - NBOEngine...")
        _data_cache["nbo_engine"]        = NBOEngine(credit_cards_df, loans_df, investments_df, insurance_df)
        print("  - ExplainabilityEngine...")
        _data_cache["explain_engine"]    = ExplainabilityEngine()
        print("  - MarketingGuard...")
        _data_cache["marketing_guard"]   = MarketingGuard()
        print("  - GenAIService...")
        _data_cache["genai_service"]     = GenAIService()
        
        print("Engines ready.")
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
    channel: str           # Email | SMS | Push
    message_preview: str
    customer_ids: Optional[List[str]] = []   # batch: all NBO customers
    age_group_strategy: Optional[str] = "auto"  # auto|genz|millennial|genx|boomer
    message_email: Optional[str] = ""
    message_sms: Optional[str] = ""
    # ── v3.0: Schedule config ────────────────────────────────────────────────
    duration_months: Optional[int] = 1       # 1, 2, 3, 6, 12
    messages_per_day: Optional[int] = 1      # 1 or 2
    preferred_time_slots: Optional[List[str]] = ["morning"]  # morning|afternoon|evening


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
    audience_count: int = 0


class CampaignGenerateContent(BaseModel):
    product: str
    segment: str
    tone: Optional[str] = "Professional"


class PersonalisedMessageRequest(BaseModel):
    customer_id: str
    product: str
    channel: str           # email | sms
    age_group: Optional[str] = "auto"   # auto|genz|millennial|genx|boomer


class CampaignAnalyticsEvent(BaseModel):
    event_type: str        # opened | clicked | applied | converted
    customer_id: Optional[str] = None
    channel: Optional[str] = "Email"


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
    v3: includes alert_signals and cluster_distribution.
    engines = get_engines()
    customers_df = engines["customers_df"]
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

    segment_dist = {}
    if "customer_segment_type" in customers_df.columns:
        for val in customers_df["customer_segment_type"].dropna():
            segment_dist[str(val)] = segment_dist.get(str(val), 0) + 1

    credit_avg = round(float(customers_df["credit_score"].mean()), 0) if "credit_score" in customers_df.columns else 0

    with get_db_connection() as conn:
        total_campaigns = conn.execute(text("SELECT COUNT(*) FROM campaigns")).scalar()
        active_campaigns = conn.execute(text("SELECT COUNT(*) FROM campaigns WHERE status = 'Active'")).scalar()

    # ── Alert Signals (computed from customer data) ───────────────────────────
    alert_signals = []
    try:
        # 1. Customers with high credit score + no credit card (acquisition opportunity)
        if "credit_score" in customers_df.columns:
            high_credit = customers_df[
                (customers_df["credit_score"] >= 750)
            ]
            if len(high_credit) > 0:
                alert_signals.append({
                    "type": "opportunity",
                    "severity": "green",
                    "emoji": "🟢",
                    "title": f"{len(high_credit)} customers with Excellent Credit Score (750+)",
                    "action": "Travel Credit Card Campaign",
                    "product": "Travel Credit Card",
                    "count": int(len(high_credit)),
                })

        # 2. Over-leveraged customers (high EMI/income ratio proxy)
        if "annual_income" in customers_df.columns and "credit_score" in customers_df.columns:
            over_lev = customers_df[
                (customers_df["credit_score"] < 650) &
                (customers_df["annual_income"] > 400000)
            ]
            if len(over_lev) > 0:
                alert_signals.append({
                    "type": "risk",
                    "severity": "red",
                    "emoji": "🔴",
                    "title": f"{len(over_lev)} customers show credit stress signals",
                    "action": "Review & Suppress Loan Offers",
                    "product": None,
                    "count": int(len(over_lev)),
                })

        # 3. High income, no investment (insurance/SIP gap)
        if "annual_income" in customers_df.columns:
            high_income = customers_df[
                customers_df["annual_income"] >= 1200000
            ]
            if len(high_income) > 0:
                alert_signals.append({
                    "type": "opportunity",
                    "severity": "amber",
                    "emoji": "🟡",
                    "title": f"{len(high_income)} high-income customers (₹12L+) need investment review",
                    "action": "SIP / Mutual Fund Campaign",
                    "product": "SIP / Mutual Fund",
                    "count": int(len(high_income)),
                })

        # 4. Young customers (<30) — digital-first segment for credit card
        if "age" in customers_df.columns:
            young = customers_df[customers_df["age"] < 30]
            if len(young) > 0:
                alert_signals.append({
                    "type": "opportunity",
                    "severity": "green",
                    "emoji": "🟢",
                    "title": f"{len(young)} Gen Z / Millennial customers — prime for first credit card",
                    "action": "Rewards Credit Card Campaign",
                    "product": "Rewards Credit Card",
                    "count": int(len(young)),
                })

        # 5. Senior customers (60+) — health insurance focus
        if "age" in customers_df.columns:
            senior = customers_df[customers_df["age"] >= 58]
            if len(senior) > 0:
                alert_signals.append({
                    "type": "risk",
                    "severity": "amber",
                    "emoji": "🟡",
                    "title": f"{len(senior)} customers nearing retirement age (58+) — pension gap risk",
                    "action": "NPS / Health Insurance Campaign",
                    "product": "NPS",
                    "count": int(len(senior)),
                })

    except Exception as exc:
        logger.warning("Alert signal computation error: %s", exc)

    # ── Cluster distribution (rule-based proxy since AI clustering is per-customer) ──
    cluster_distribution = []
    try:
        from ai_engine.clustering_engine import CLUSTER_PERSONAS
        # Distribute customers into clusters by employment type + age as a fast proxy
        if "employment_type" in customers_df.columns and "age" in customers_df.columns:
            persona_counts = {k: 0 for k in CLUSTER_PERSONAS}
            for _, row in customers_df.iterrows():
                emp = str(row.get("employment_type", "")).lower()
                age = int(row.get("age", 35))
                income = float(row.get("annual_income", 0))
                if age < 25:
                    persona_counts[6] = persona_counts.get(6, 0) + 1
                elif "student" in emp:
                    persona_counts[6] = persona_counts.get(6, 0) + 1
                elif age >= 58 or "retir" in emp:
                    persona_counts[5] = persona_counts.get(5, 0) + 1
                elif "business" in emp or "self" in emp:
                    persona_counts[3] = persona_counts.get(3, 0) + 1
                elif income >= 2500000:
                    persona_counts[7] = persona_counts.get(7, 0) + 1
                elif age < 30:
                    persona_counts[0] = persona_counts.get(0, 0) + 1
                elif 30 <= age <= 45 and income >= 1000000:
                    persona_counts[1] = persona_counts.get(1, 0) + 1
                elif 35 <= age <= 55:
                    persona_counts[2] = persona_counts.get(2, 0) + 1
                else:
                    persona_counts[4] = persona_counts.get(4, 0) + 1

            for cid, persona in CLUSTER_PERSONAS.items():
                cnt = persona_counts.get(cid, 0)
                cluster_distribution.append({
                    "id": cid,
                    "label": persona["label"],
                    "description": persona["description"],
                    "color": persona["color"],
                    "count": cnt,
                    "percentage": round(cnt / max(total_customers, 1) * 100, 1),
                    "top_products": list(persona["nbo_boost"].keys())[:3],
                    "message_tone": persona["message_tone"],
                })
    except Exception as exc:
        logger.warning("Cluster distribution error: %s", exc)

    return {
        "total_customers": total_customers,
        "total_campaigns": total_campaigns,
        "active_campaigns": active_campaigns,
        "avg_credit_score": credit_avg,
        "income_distribution": income_dist,
        "segment_distribution": segment_dist,
        "alert_signals": alert_signals,
        "cluster_distribution": cluster_distribution,
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
    engines = get_engines()
    customers_df = engines["customers_df"]

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
    customer_360_db   = eng.get("customer_360", {})

    customer_row = customers_df[customers_df["customer_id"] == customer_id]
    if customer_row.empty:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    customer_data = customer_row.iloc[0].to_dict()

    # 1. Features
    features = feature_engine.compute(customer_id, customer_data)

    # 1.5 Cluster assignment
    try:
        clustering_engine = ClusteringEngine()
        cluster_info = clustering_engine.assign(customer_data, features)
        features.cluster_label = cluster_info.get("cluster_label", "Standard")
        features.cluster_id    = cluster_info.get("cluster_id", -1)
        features.cluster_color = cluster_info.get("cluster_color", "#64748b")
    except Exception as _ce:
        cluster_info = {"cluster_label": "Standard", "cluster_id": -1, "cluster_color": "#64748b", "message_tone": "professional"}

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
    if marketing_check.get("allowed") and nbo.get("category"):
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

    # Fetch the prebuilt Customer 360 JSON profile
    c360 = customer_360_db.get(customer_id, {})

    return serialise({
        "customer": customer_data,
        "customer_360": c360,
        "behavior": behavior,
        "events": events,
        "segments": segments,
        "financial_analysis": financial_analysis,
        "nbo": nbo,
        "explanation": explanation,
        "marketing_check": marketing_check,
        "genai_message": genai_msg,
        "propensities": nbo.get("propensities", {}),
        # v3.0 additions
        "all_propensity_scores": nbo.get("all_propensity_scores", []),
        "cluster": cluster_info,
        "travel_profile": features.travel_profile,
        "holdings": features.holdings,
        "holdings_summary": {
            "has_credit_card":        features.has_credit_card,
            "has_insurance":          features.has_insurance,
            "has_health_insurance":   features.has_health_insurance,
            "has_life_insurance":     features.has_life_insurance,
            "has_travel_insurance":   features.has_travel_insurance,
            "has_motor_insurance":    features.has_motor_insurance,
            "has_home_insurance":     features.has_home_insurance,
            "has_investments":        features.has_investments,
            "has_sip":                features.has_sip,
            "has_mutual_fund":        features.has_mutual_fund,
            "has_stocks":             features.has_stocks,
            "has_bonds":              features.has_bonds,
            "has_nps":                features.has_nps,
            "has_demat":              features.has_demat,
            "has_etf":                features.has_etf,
            "has_wealth_management":  features.has_wealth_management,
            "has_private_banking":    features.has_private_banking,
            "has_home_loan":          features.has_home_loan,
            "has_personal_loan":      features.has_personal_loan,
            "has_vehicle_loan":       features.has_vehicle_loan,
            "has_education_loan":     features.has_education_loan,
            "has_agriculture_loan":   features.has_agriculture_loan,
            "has_business_loan":      features.has_business_loan,
            "has_deposits":           features.has_deposits,
            "held_card_names":              features.held_card_names,
            "held_loan_categories":         features.held_loan_categories,
            "held_investment_categories":   features.held_investment_categories,
            "held_insurance_categories":    features.held_insurance_categories,
            "total_emi_monthly":         features.total_emi_monthly,
            "total_sip_monthly":         features.total_sip_monthly,
            "total_assets_value":        features.total_assets_value,
            "total_outstanding_debt":    features.total_outstanding_debt,
            "net_worth_indicator":       features.net_worth_indicator,
            "total_insurance_cover":     features.total_insurance_cover,
            "total_credit_limit":        features.total_credit_limit,
            "total_credit_outstanding":  features.total_credit_outstanding,
        },
        "windows": {
            str(days): {
                "total_spend": w.total_spend,
                "category_spend": w.category_spend,
                "transaction_count": w.transaction_count,
                "digital_ratio": w.digital_ratio,
            }
            for days, w in features.windows.items()
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

# ─────────────────────────────────────────────────────────────────────────────
# Age/generation detection helper
# ─────────────────────────────────────────────────────────────────────────────

def detect_age_group(age: int, override: str = "auto") -> str:
    if override and override != "auto":
        return override
    if age <= 25:
        return "genz"
    elif age <= 40:
        return "millennial"
    elif age <= 55:
        return "genx"
    else:
        return "boomer"


AGE_GROUP_STRATEGY = {
    "genz": {
        "tone": "Direct, humorous, emoji-rich, FOMO-driven, ultra-short punchy lines. Use contextual triggers (day/time/weather). Think Zomato's 'Barish ho rahi hai chai aur pakode ho jaye'. Be witty, bold, use relatable language.",
        "email_format": "Punchy subject (max 8 words, use emoji), 3-4 short lines, bold CTA button. No corporate fluff.",
        "sms_format": "Max 120 chars. Hook in first 5 words. One emoji. One clear action.",
        "opener_style": "Contextual/situational hook",
    },
    "millennial": {
        "tone": "Achievement-framing, aspirational, social proof. Inspired by Unstop/LinkedIn style — start with 'Congratulations!' or achievement recognition so customer feels they've earned something special and opens immediately. Benefit-led, personal.",
        "email_format": "Subject: Congratulations + benefit. Opening: personal achievement recognition. Body: specific benefit + social proof. CTA: action-oriented.",
        "sms_format": "Max 140 chars. Lead with achievement/congratulations. Clear benefit. CTA.",
        "opener_style": "Achievement/congratulations opener",
    },
    "genx": {
        "tone": "ROI clarity, trust, family/security angle, concise professional. Focus on long-term value, data-backed claims, reliability of NPN Bank.",
        "email_format": "Professional subject. Data-point hook. Benefits with numbers. Security/trust signal. Clear CTA.",
        "sms_format": "Max 140 chars. Specific benefit with number. Brand trust. CTA.",
        "opener_style": "Value/ROI focused opener",
    },
    "boomer": {
        "tone": "Formal, relationship-based, security/stability focus, human-touch. Open with personal relationship acknowledgement. Emphasize safety, reliability, dedicated support. No slang, no emoji.",
        "email_format": "Formal subject. 'Dear [Name]' opening. Warm relationship acknowledgement. Security/stability emphasis. Clear professional CTA. Sign-off from 'Your Relationship Manager'.",
        "sms_format": "Max 140 chars. Formal. Clear benefit. Call bank hotline or visit branch CTA.",
        "opener_style": "Personal relationship/formal opener",
    },
}


BANKING_CONTEXTUAL_TRIGGERS = """
Context-aware triggers to weave into the message (use only what's relevant):
- If customer has recent international transactions → great candidate for Travel Credit Card (zero forex fees)
- If customer has high idle savings with no investments → SIP/Mutual Fund is ideal for wealth growth  
- If customer salary recently credited → perfect timing for investment offer (2 days post salary)
- If customer has high EMI load → balance transfer / loan refinance saves money
- If customer has low transaction frequency recently → re-engagement with exclusive loyalty reward
- If weekend → leisure/lifestyle offers resonate more
- If Monday morning → financial planning offers resonate (new week energy)
- Current time in India: use it for greetings (Good morning / evening appropriately)
"""


# ── Email sending helpers ────────────────────────────────────────────────────

def _send_email_smtp(to_email: str, subject: str, html_body: str, plain_body: str, sender: str, password: str) -> bool:
    """Send a single HTML email via Gmail SMTP. Returns True on success."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"NPN Bank Marketing <{sender}>"
        msg["To"] = to_email
        # Attach plain text first (fallback), then HTML (preferred)
        msg.attach(MIMEText(plain_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.login(sender, password)
            server.sendmail(sender, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"[EMAIL] Send failed to {to_email}: {e}")
        return False


def _send_campaign_emails_background(
    campaign_id: str,
    customer_ids: List[str],
    product: str,
    age_group_strategy: str,
):
    """
    Background task: for each @gmail.com customer, generate a personalised
    email via Groq AI and dispatch it via Gmail SMTP.
    """
    if not GMAIL_SENDER or not GMAIL_APP_PASSWORD:
        print("[EMAIL] Skipped: GMAIL_SENDER / GMAIL_APP_PASSWORD not configured.")
        return

    eng = get_engines()
    customers_df   = eng["customers_df"]
    feature_engine = eng["feature_engine"]
    genai_service  = eng["genai_service"]
    groq_client    = genai_service.client if not genai_service.use_mock else None

    import json as _json
    import re as _re
    import math as _math

    sent_count, failed_count = 0, 0

    for cid in customer_ids:
        try:
            row = customers_df[customers_df["customer_id"] == cid]
            if row.empty:
                continue

            customer_data = row.iloc[0].to_dict()
            cust_email = str(customer_data.get("email", "") or "").strip()

            # ── Only @gmail.com addresses ─────────────────────────────────────
            if not cust_email.lower().endswith("@gmail.com"):
                continue

            first_name     = str(customer_data.get("first_name") or "Customer")
            last_name      = str(customer_data.get("last_name") or "")
            age            = int(customer_data.get("age") or 35)
            city           = str(customer_data.get("city") or "India")

            def safe_num(val, default=0):
                try:
                    v = float(val)
                    return 0 if (_math.isnan(v) or _math.isinf(v)) else v
                except (TypeError, ValueError):
                    return default

            credit_score   = int(safe_num(customer_data.get("credit_score"), 700))
            monthly_income = safe_num(customer_data.get("annual_income"), 0) / 12

            age_group = detect_age_group(age, age_group_strategy)
            strategy  = AGE_GROUP_STRATEGY[age_group]

            now           = datetime.now()
            day_name      = now.strftime("%A")
            greeting_time = "morning" if now.hour < 12 else ("afternoon" if now.hour < 17 else "evening")

            # Portfolio context
            try:
                features = feature_engine.compute(cid, customer_data)
                lines = []
                if features.held_card_names:
                    lines.append(f"Credit Cards: {', '.join(features.held_card_names)}")
                if features.held_loan_categories:
                    lines.append(f"Loans: {', '.join(features.held_loan_categories)}, EMI ₹{safe_num(features.total_emi_monthly):,.0f}/mo")
                if features.held_investment_categories:
                    lines.append(f"Investments: {', '.join(features.held_investment_categories)}, value ₹{safe_num(features.total_assets_value):,.0f}")
                portfolio_context = "\n".join(lines) if lines else "New to bank portfolio."
            except Exception:
                portfolio_context = "Portfolio data unavailable."

            prompt = f"""You are a world-class personalised banking marketing copywriter at NPN Bank India.

CUSTOMER PROFILE:
- Name: {first_name} {last_name}
- Age: {age} years (Generation: {age_group.upper()})
- City: {city}
- Credit Score: {credit_score}
- Monthly Income: ₹{monthly_income:,.0f}
- Current time: {greeting_time} on {day_name}

PORTFOLIO:
{portfolio_context}

PRODUCT TO MARKET: {product}

MARKETING STRATEGY — {age_group.upper()}:
{strategy['tone']}
OPENER STYLE: {strategy['opener_style']}

{BANKING_CONTEXTUAL_TRIGGERS}

CHANNEL: EMAIL
FORMAT RULES: {strategy['email_format']}

RULES:
1. Address customer by first name: {first_name}
2. Feel like written JUST for them — reference city, portfolio gaps, life stage
3. No fictional interest rates or guaranteed returns
4. NPN Bank India context, Indian Rupees (₹)
5. Apply {age_group.upper()} generation strategy throughout

OUTPUT: Return valid JSON only:
{{"subject": "...", "body": "...", "age_group": "{age_group}", "strategy_used": "...", "preview_text": "..."}}"""

            # Generate message
            subject = f"Exclusive {product} Offer for You, {first_name}!"
            body    = f"Dear {first_name},\n\nWe have an exclusive offer for {product} curated just for you.\n\nBest regards,\nNPN Bank Marketing Team"

            if groq_client:
                try:
                    resp = groq_client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": "You are a banking marketing API. Return only valid JSON."},
                            {"role": "user",   "content": _trim_prompt(prompt)},
                        ],
                        model="qwen/qwen3.6-27b",
                        temperature=0.7,
                        max_tokens=1200,
                    )
                    parsed = _safe_parse_groq_json(resp.choices[0].message.content, f"EMAIL {cid}")
                    if parsed:
                        subject = parsed.get("subject", subject)
                        body    = parsed.get("body", body)
                    else:
                        fb      = _fallback_personalised_message(first_name, product, age_group, "email")
                        subject = fb.get("subject", subject)
                        body    = fb.get("body", body)
                except Exception as gen_err:
                    print(f"[EMAIL] Groq error for {cid}: {gen_err} — using fallback")
                    fb      = _fallback_personalised_message(first_name, product, age_group, "email")
                    subject = fb.get("subject", subject)
                    body    = fb.get("body", body)
            else:
                fb      = _fallback_personalised_message(first_name, product, age_group, "email")
                subject = fb.get("subject", subject)
                body    = fb.get("body", body)

            # Build rich HTML email with inline image + product facts
            html_body = build_html_email(
                first_name=first_name,
                product=product,
                body_text=body,
                age_group=age_group,
            )

            # Send as HTML email
            ok = _send_email_smtp(cust_email, subject, html_body, body, GMAIL_SENDER, GMAIL_APP_PASSWORD)
            if ok:
                sent_count += 1
                print(f"[EMAIL] ✅ Sent to {cust_email} ({first_name} {last_name})")
            else:
                failed_count += 1

        except Exception as exc:
            print(f"[EMAIL] Error processing customer {cid}: {exc}")
            failed_count += 1

    print(f"[EMAIL] Campaign {campaign_id} complete — sent: {sent_count}, failed: {failed_count}")


# ── SMS sending helpers ──────────────────────────────────────────────────────────────

def _send_sms_twilio(to_number: str, body: str, account_sid: str, auth_token: str, from_number: str) -> bool:
    """Send a single SMS via Twilio. Returns True on success."""
    try:
        from twilio.rest import Client
        # Ensure phone number is in E.164 format (+91XXXXXXXXXX)
        if not to_number.startswith("+"):
            to_number = "+91" + to_number.lstrip("0")
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=body,
            from_=from_number,
            to=to_number
        )
        return message.sid is not None
    except Exception as e:
        print(f"[SMS] Send failed to {to_number}: {e}")
        return False


def _send_campaign_sms_background(
    campaign_id: str,
    customer_ids: List[str],
    product: str,
    age_group_strategy: str,
):
    """
    Background task: for each customer with a mobile number, generate a
    personalised SMS via Groq AI and dispatch it via Twilio.
    """
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_PHONE_NUMBER:
        print("[SMS] Skipped: Twilio credentials not configured.")
        return

    eng = get_engines()
    customers_df   = eng["customers_df"]
    feature_engine = eng["feature_engine"]
    genai_service  = eng["genai_service"]
    groq_client    = genai_service.client if not genai_service.use_mock else None

    import json as _json
    import re as _re
    import math as _math

    sent_count, failed_count = 0, 0

    for cid in customer_ids:
        try:
            row = customers_df[customers_df["customer_id"] == cid]
            if row.empty:
                continue

            customer_data = row.iloc[0].to_dict()
            mobile = str(customer_data.get("mobile_number", "") or "").strip()
            if not mobile or "9322130400" not in mobile:
                continue

            first_name     = str(customer_data.get("first_name") or "Customer")
            last_name      = str(customer_data.get("last_name") or "")
            age            = int(customer_data.get("age") or 35)
            city           = str(customer_data.get("city") or "India")

            def safe_num(val, default=0):
                try:
                    v = float(val)
                    return 0 if (_math.isnan(v) or _math.isinf(v)) else v
                except (TypeError, ValueError):
                    return default

            credit_score   = int(safe_num(customer_data.get("credit_score"), 700))
            monthly_income = safe_num(customer_data.get("annual_income"), 0) / 12

            age_group = detect_age_group(age, age_group_strategy)
            strategy  = AGE_GROUP_STRATEGY[age_group]

            prompt = f"""You are a world-class personalised banking SMS copywriter at NPN Bank India.

CUSTOMER PROFILE:
- Name: {first_name} {last_name}
- Age: {age} years (Generation: {age_group.upper()})
- City: {city}
- Credit Score: {credit_score}
- Monthly Income: ₹{monthly_income:,.0f}

PRODUCT TO MARKET: {product}

MARKETING STRATEGY — {age_group.upper()}:
{strategy['tone']}
OPENER STYLE: {strategy['opener_style']}

CHANNEL: SMS
FORMAT RULES: {strategy['sms_format']}

CRITICAL SMS RULES:
1. Address customer by first name: {first_name}
2. Maximum 160 characters total (strict SMS limit)
3. No fictional interest rates or guaranteed returns
4. NPN Bank India context, Indian Rupees (₹)
5. End with a short CTA link: npnbank.in/offer

OUTPUT: Return valid JSON only:
{{"body": "...", "age_group": "{age_group}"}}"""

            # Generate SMS body
            sms_body = f"{first_name}! Exclusive {product} offer from NPN Bank. Grab it now: npnbank.in/offer"

            if groq_client:
                try:
                    resp = groq_client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": "You are a banking marketing API. Return only valid JSON."},
                            {"role": "user",   "content": _trim_prompt(prompt)},
                        ],
                        model="qwen/qwen3.6-27b",
                        temperature=0.7,
                        max_tokens=1200,
                    )
                    parsed = _safe_parse_groq_json(resp.choices[0].message.content, f"SMS {cid}")
                    if parsed:
                        raw_sms = parsed.get("body", sms_body)
                    else:
                        fb = _fallback_personalised_message(first_name, product, age_group, "sms")
                        raw_sms = fb.get("body", sms_body)
                except Exception as gen_err:
                    print(f"[SMS] Groq error for {cid}: {gen_err} — using fallback")
                    fb = _fallback_personalised_message(first_name, product, age_group, "sms")
                    raw_sms = fb.get("body", sms_body)
            else:
                fb = _fallback_personalised_message(first_name, product, age_group, "sms")
                raw_sms = fb.get("body", sms_body)

            # Build punchy SMS using template (enforces 160-char limit)
            sms_body = build_sms_body(
                first_name=first_name,
                product=product,
                body_text=raw_sms,
            )

            # Send the SMS
            ok = _send_sms_twilio(mobile, sms_body, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER)
            if ok:
                sent_count += 1
                print(f"[SMS] ✅ Sent to {mobile} ({first_name} {last_name})")
            else:
                failed_count += 1

        except Exception as exc:
            print(f"[SMS] Error processing customer {cid}: {exc}")
            failed_count += 1

    print(f"[SMS] Campaign {campaign_id} complete — sent: {sent_count}, failed: {failed_count}")


@app.post("/api/campaigns", tags=["Campaigns"])
def create_campaign(
    campaign: CampaignCreate,
    background_tasks: BackgroundTasks,
    current_employee=Depends(get_current_employee),
):
    """Create and launch a new marketing campaign, and send real emails to @gmail.com customers."""
    import random
    campaign_id = str(uuid.uuid4())[:8].upper()
    audience_count = len(campaign.customer_ids) if campaign.customer_ids else 0

    new_campaign = {
        "id": campaign_id,
        "customer_id": campaign.customer_id,
        "customer_name": campaign.customer_name,
        "product": campaign.product,
        "campaign_name": campaign.campaign_name,
        "description": campaign.description,
        "channel": campaign.channel,
        "message_preview": campaign.message_preview,
        "message_email": campaign.message_email,
        "message_sms": campaign.message_sms,
        "age_group_strategy": campaign.age_group_strategy,
        "status": "Active",
        "created_at": datetime.now().isoformat(),
        "created_by": current_employee["name"],
        "audience_count": audience_count,
        "customer_ids": campaign.customer_ids,
        "schedule_config": {
            "duration_months": campaign.duration_months or 1,
            "messages_per_day": campaign.messages_per_day or 1,
            "preferred_time_slots": campaign.preferred_time_slots or ["morning"],
            "total_messages": (campaign.duration_months or 1) * 30 * (campaign.messages_per_day or 1),
        },
    }
    # Seed realistic analytics for the campaign
    sent = max(audience_count, 1)
    opened = int(sent * random.uniform(0.55, 0.75))
    clicked = int(opened * random.uniform(0.35, 0.55))
    applied = int(clicked * random.uniform(0.25, 0.45))
    converted = int(applied * random.uniform(0.40, 0.65))

    analytics_data = {
        "sent": sent,
        "opened": opened,
        "clicked": clicked,
        "applied": applied,
        "converted": converted,
        "channel_breakdown": {
            "email": {"sent": int(sent * 0.7), "opened": int(opened * 0.65)},
            "sms":   {"sent": int(sent * 0.3), "opened": int(opened * 0.85)},
        },
        "events": [],
        "hourly_opens": [
            {"hour": f"{h:02d}:00", "opens": max(0, int(opened * 0.05 * abs(math.sin(h / 3.5))))}
            for h in range(24)
        ],
    }

    # ── Count @gmail.com recipients upfront (fast scan, no AI) ─────────────
    gmail_count = 0
    if campaign.channel == "Email" and campaign.customer_ids:
        eng_data     = get_engines()
        customers_df = eng_data["customers_df"]
        for cid in campaign.customer_ids:
            r = customers_df[customers_df["customer_id"] == cid]
            if not r.empty:
                em = str(r.iloc[0].get("email", "") or "").strip()
                if em.lower().endswith("@gmail.com"):
                    gmail_count += 1

    new_campaign["gmail_recipients"] = gmail_count
    new_campaign["email_dispatch_status"] = "queued" if (campaign.channel == "Email" and GMAIL_SENDER and gmail_count > 0) else "skipped"

    import json as _json
    # Save to Supabase DB
    with get_db_connection() as conn:
        conn.execute(
            text("""
                INSERT INTO campaigns (id, customer_id, customer_name, product, campaign_name, description, channel, message_preview, message_email, message_sms, age_group_strategy, status, created_at, created_by, audience_count, customer_ids, gmail_recipients, email_dispatch_status, schedule_config)
                VALUES (:id, :customer_id, :customer_name, :product, :campaign_name, :description, :channel, :message_preview, :message_email, :message_sms, :age_group_strategy, :status, :created_at, :created_by, :audience_count, :customer_ids, :gmail_recipients, :email_dispatch_status, :schedule_config)
            """),
            {**new_campaign, "customer_ids": _json.dumps(new_campaign["customer_ids"]), "schedule_config": _json.dumps(new_campaign.get("schedule_config", {}))}
        )
        conn.execute(
            text("""
                INSERT INTO campaign_analytics (campaign_id, sent, opened, clicked, applied, converted, channel_breakdown, events, hourly_opens)
                VALUES (:campaign_id, :sent, :opened, :clicked, :applied, :converted, :channel_breakdown, :events, :hourly_opens)
            """),
            {
                "campaign_id": campaign_id,
                "sent": sent,
                "opened": opened,
                "clicked": clicked,
                "applied": applied,
                "converted": converted,
                "channel_breakdown": _json.dumps(analytics_data["channel_breakdown"]),
                "events": _json.dumps(analytics_data["events"]),
                "hourly_opens": _json.dumps(analytics_data["hourly_opens"]),
            }
        )
        conn.commit()

    # ── Fire real email sending in the background ─────────────────────────
    if campaign.channel == "Email" and GMAIL_SENDER and gmail_count > 0:
        background_tasks.add_task(
            _send_campaign_emails_background,
            campaign_id,
            campaign.customer_ids,
            campaign.product,
            campaign.age_group_strategy or "auto",
        )
        print(f"[EMAIL] 🚀 Background email dispatch queued for campaign {campaign_id} — {gmail_count} @gmail.com recipients")

    # ── Count SMS recipients and fire real SMS in the background ──────────
    sms_count = 0
    if campaign.channel == "SMS" and campaign.customer_ids:
        eng_data     = get_engines()
        customers_df = eng_data["customers_df"]
        for cid in campaign.customer_ids:
            r = customers_df[customers_df["customer_id"] == cid]
            if not r.empty:
                mob = str(r.iloc[0].get("mobile_number", "") or "").strip()
                if mob and "9322130400" in mob:
                    sms_count += 1

    new_campaign["sms_recipients"] = sms_count
    new_campaign["sms_dispatch_status"] = "queued" if (campaign.channel == "SMS" and TWILIO_ACCOUNT_SID and sms_count > 0) else "skipped"

    if campaign.channel == "SMS" and TWILIO_ACCOUNT_SID and sms_count > 0:
        background_tasks.add_task(
            _send_campaign_sms_background,
            campaign_id,
            campaign.customer_ids,
            campaign.product,
            campaign.age_group_strategy or "auto",
        )
        print(f"[SMS] 🚀 Background SMS dispatch queued for campaign {campaign_id} — {sms_count} recipients")

    return new_campaign


# ── AI Campaign Suggester ──────────────────────────────────────────────────────

@app.get("/api/campaigns/suggestions", tags=["Campaigns"])
def get_campaign_suggestions(current_employee=Depends(get_current_employee)):
    """
    Returns 3-5 AI-generated campaign suggestions based on upcoming Indian festivals,
    national days, and customer segment distribution.
    Combines the Indian calendar with a Groq LLM call for rich reasoning.
    """
    import json as _json
    from ai_engine.indian_calendar import get_campaign_suggestions_by_events, get_upcoming_events

    # Get event-based raw suggestions
    event_suggestions = get_campaign_suggestions_by_events()
    upcoming_events   = get_upcoming_events(max_events=3)

    # Build event summary for LLM
    event_lines = []
    for ev in upcoming_events:
        event_lines.append(f"- {ev['emoji']} {ev['name']} in {ev['days_away']} days (products: {', '.join(ev.get('products', [])[:3])})")
    event_summary = "\n".join(event_lines) if event_lines else "No major events in the next 30 days."

    # Get segment distribution from DB for context
    segment_context = ""
    try:
        with get_db_connection() as conn:
            res = conn.execute(text("SELECT COUNT(*) as total FROM customers")).scalar()
            segment_context = f"Total customers: {res}"
    except Exception:
        segment_context = ""

    # Try Groq LLM for enriched suggestions
    llm_suggestions = []
    try:
        eng = get_engines()
        genai = eng["genai_service"]
        if not genai.use_mock:
            import re as _re
            prompt = f"""You are a senior banking marketing strategist at NPN Bank India.

UPCOMING FESTIVALS & EVENTS:
{event_summary}

{segment_context}

Based on these upcoming events, generate exactly 4 campaign suggestions.
Each suggestion must be highly relevant to the event and actionable for the bank's marketing team.

OUTPUT: Return only a valid JSON array:
[
  {{
    "product": "Gold Loan",
    "campaign_name": "Dhanteras Gold Rush 2025",
    "urgency": "high",
    "reason": "Gold demand surges 3x during Dhanteras. Customers with savings >5L are prime targets for gold-backed loans.",
    "target_segment": "Conservative Saver",
    "festival_hook": "Dhanteras",
    "emoji": "🪙",
    "expected_conversion": "5.2%"
  }}
]"""
            resp = genai.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a banking marketing API. Return only valid JSON."},
                    {"role": "user", "content": _trim_prompt(prompt)},
                ],
                model="qwen/qwen3.6-27b",
                temperature=0.7,
                max_tokens=1200,
            )
            parsed = _safe_parse_groq_json(resp.choices[0].message.content, "SUGGESTIONS")
            if parsed and isinstance(parsed, list):
                llm_suggestions = parsed
    except Exception as exc:
        print(f"[SUGGESTIONS] Groq error: {exc} — falling back to calendar-based suggestions")

    # Fallback: build suggestions from calendar directly
    if not llm_suggestions:
        seen_products = set()
        for s in event_suggestions:
            if s["product"] not in seen_products:
                llm_suggestions.append({
                    "product": s["product"],
                    "campaign_name": f"{s['festival_hook']} {s['product']} Campaign",
                    "urgency": s["urgency"],
                    "reason": f"{s['festival_emoji']} {s['festival_hook']} is approaching in {s['days_away']} days — strong demand for {s['product']}.",
                    "target_segment": "All Customers",
                    "festival_hook": s["festival_hook"],
                    "emoji": s.get("festival_emoji", "🎉"),
                    "expected_conversion": "3.5%",
                })
                seen_products.add(s["product"])
                if len(llm_suggestions) >= 4:
                    break

    return {
        "suggestions": llm_suggestions,
        "upcoming_events": upcoming_events,
        "generated_at": datetime.now().isoformat(),
    }


@app.get("/api/campaigns", tags=["Campaigns"])
def list_campaigns(current_employee=Depends(get_current_employee)):
    """List all campaigns."""
    import json as _json
    campaigns_list = []
    with get_db_connection() as conn:
        res = conn.execute(text("SELECT * FROM campaigns ORDER BY created_at DESC")).mappings().all()
        for row in res:
            c = dict(row)
            if isinstance(c.get("customer_ids"), str):
                try:
                    c["customer_ids"] = _json.loads(c["customer_ids"])
                except:
                    c["customer_ids"] = []
            elif c.get("customer_ids") is None:
                c["customer_ids"] = []
            if isinstance(c.get("created_at"), datetime):
                c["created_at"] = c["created_at"].isoformat()
            campaigns_list.append(c)
    return {"campaigns": campaigns_list}


@app.patch("/api/campaigns/{campaign_id}/status", tags=["Campaigns"])
def update_campaign_status(
    campaign_id: str,
    status_update: dict,
    current_employee=Depends(get_current_employee),
):
    """Update a campaign's status (Active | Draft | Completed)."""
    new_status = status_update.get("status")
    with get_db_connection() as conn:
        res = conn.execute(
            text("UPDATE campaigns SET status = :status WHERE id = :id RETURNING *"),
            {"status": new_status, "id": campaign_id}
        ).fetchone()
        conn.commit()
        if res:
            return dict(res._mapping)
    raise HTTPException(status_code=404, detail="Campaign not found")


@app.get("/api/campaigns/{product}/customers", tags=["Campaigns"])
def get_nbo_customers_for_product(
    product: str,
    limit: int = 200,
    current_employee=Depends(get_current_employee),
):
    """
    Return all customers whose NBO segment matches the given product.
    Used to auto-populate the campaign customer list.
    """
    eng = get_engines()
    customers_df   = eng["customers_df"]
    feature_engine = eng["feature_engine"]
    seg_engine     = eng["seg_engine"]
    nbo_engine     = eng["nbo_engine"]

    # Map product -> matching segment definitions
    PRODUCT_SEGMENT_MAP = {
        "Travel Credit Card":  ["seg-2", "Frequent Travellers"],
        "Premium Account":     ["seg-1", "High Value"],
        "SIP / Mutual Fund":   ["seg-3", "Investment Oriented"],
        "Personal Loan":       ["seg-4", "Loan Ready"],
        "Credit Card":         ["seg-5", "Churn Risk"],
    }

    # Find closest product key
    matched_seg = None
    for key, val in PRODUCT_SEGMENT_MAP.items():
        if key.lower() in product.lower() or product.lower() in key.lower():
            matched_seg = val[1]
            break
    if not matched_seg:
        matched_seg = "High Value"  # default fallback

    # Collect matching segment definitions engine names
    seg_def = next((s for s in SEGMENT_DEFINITIONS if s["name"] == matched_seg), None)
    engine_names = seg_def["engine_names"] if seg_def else []

    results = []
    sample = customers_df.head(500)  # cap for performance
    for _, row in sample.iterrows():
        cust_data = row.to_dict()
        features = feature_engine.compute(row["customer_id"], cust_data)
        engine_segs = seg_engine.segment_customer(cust_data, features)

        is_match = any(es in engine_segs for es in engine_names) if engine_names else True
        if is_match:
            credit_score = cust_data.get("credit_score", 700)
            propensity = min(98, int((credit_score / 850) * 100))
            results.append({
                "customer_id":   cust_data.get("customer_id"),
                "first_name":    cust_data.get("first_name", ""),
                "last_name":     cust_data.get("last_name", ""),
                "email":         cust_data.get("email", ""),
                "age":           cust_data.get("age", 0),
                "city":          cust_data.get("city", ""),
                "credit_score":  credit_score,
                "annual_income": cust_data.get("annual_income", 0),
                "segment":       matched_seg,
                "propensity":    propensity,
                "customer_segment_type": cust_data.get("customer_segment_type", ""),
            })
            if len(results) >= limit:
                break

    return {
        "product": product,
        "segment": matched_seg,
        "count": len(results),
        "customers": results,
    }


@app.post("/api/campaigns/generate-personalised-message", tags=["Campaigns"])
def generate_personalised_message(
    req: PersonalisedMessageRequest,
    current_employee=Depends(get_current_employee),
):
    """
    Generate a hyper-personalised Email or SMS for a specific customer using Groq,
    with age/generation-aware marketing strategy.
    """
    eng = get_engines()
    customers_df   = eng["customers_df"]
    feature_engine = eng["feature_engine"]
    genai_service  = eng["genai_service"]

    customer_row = customers_df[customers_df["customer_id"] == req.customer_id]
    if customer_row.empty:
        raise HTTPException(status_code=404, detail=f"Customer {req.customer_id} not found")

    customer_data = customer_row.iloc[0].to_dict()

    try:
        features = feature_engine.compute(req.customer_id, customer_data)

        age = int(customer_data.get("age") or 35)
        age_group = detect_age_group(age, req.age_group)
        strategy = AGE_GROUP_STRATEGY[age_group]

        # Build rich context — safe number formatting (guard against NaN/None)
        def safe_num(val, default=0):
            try:
                v = float(val)
                return 0 if (math.isnan(v) or math.isinf(v)) else v
            except (TypeError, ValueError):
                return default

        now = datetime.now()
        hour = now.hour
        day_name = now.strftime("%A")
        greeting_time = "morning" if hour < 12 else ("afternoon" if hour < 17 else "evening")

        portfolio_lines = []
        if features.held_card_names:
            portfolio_lines.append(f"Credit Cards held: {', '.join(features.held_card_names)}")
        if features.held_loan_categories:
            emi = safe_num(features.total_emi_monthly)
            portfolio_lines.append(f"Loans: {', '.join(features.held_loan_categories)}, EMI \u20b9{emi:,.0f}/mo")
        if features.held_investment_categories:
            assets = safe_num(features.total_assets_value)
            portfolio_lines.append(f"Investments: {', '.join(features.held_investment_categories)}, value \u20b9{assets:,.0f}")
        if features.has_insurance:
            portfolio_lines.append("Insurance: covered")
        else:
            portfolio_lines.append("Insurance: none — gap exists")
        portfolio_context = "\n".join(portfolio_lines) if portfolio_lines else "New to bank portfolio."

        first_name    = str(customer_data.get("first_name") or "Customer")
        last_name     = str(customer_data.get("last_name") or "")
        city          = str(customer_data.get("city") or "India")
        credit_score  = int(safe_num(customer_data.get("credit_score"), 700))
        annual_income = safe_num(customer_data.get("annual_income"), 0)
        monthly_income = annual_income / 12

        channel_instruction = strategy["email_format"] if req.channel == "email" else strategy["sms_format"]

    except Exception as e:
        import traceback
        print(f"generate_personalised_message context error for {req.customer_id}: {e}\n{traceback.format_exc()}")
        # Fallback with bare data
        first_name    = str(customer_data.get("first_name") or "Customer")
        last_name     = str(customer_data.get("last_name") or "")
        age           = int(customer_data.get("age") or 35)
        age_group     = detect_age_group(age, req.age_group)
        strategy      = AGE_GROUP_STRATEGY[age_group]
        portfolio_context = "Portfolio data unavailable."
        city          = str(customer_data.get("city") or "India")
        credit_score  = 700
        monthly_income = 0.0
        channel_instruction = strategy["email_format"] if req.channel == "email" else strategy["sms_format"]
        prompt        = None  # will use fallback

    if "prompt" not in dir() or prompt is None:
        prompt = f"""You are a world-class personalised banking marketing copywriter at NPN Bank India.

CUSTOMER PROFILE:
- Name: {first_name} {last_name}
- Age: {age} years (Generation: {age_group.upper()})
- City: {city}
- Credit Score: {credit_score}
- Monthly Income: ₹{monthly_income:,.0f}
- Current time: {greeting_time} on {day_name}

PORTFOLIO:
{portfolio_context}

PRODUCT TO MARKET: {req.product}

MARKETING GENERATION STRATEGY — {age_group.upper()}:
{strategy['tone']}

OPENER STYLE: {strategy['opener_style']}

{BANKING_CONTEXTUAL_TRIGGERS}

CHANNEL: {req.channel.upper()}
FORMAT RULES: {channel_instruction}

IMPORTANT RULES:
1. Address customer by first name: {first_name}
2. Make it feel like it was written JUST for them — reference their city, their portfolio gaps, their life stage
3. DO NOT mention fictional interest rates or guaranteed returns
4. Keep it real — NPN Bank India context
5. Use Indian cultural context and Indian Rupees (₹)
6. CRITICAL: Apply the {age_group.upper()} generation strategy throughout

OUTPUT: Return valid JSON with exactly these fields:
{{
  "subject": "Subject line or SMS opening hook",
  "body": "Full message body",
  "age_group": "{age_group}",
  "strategy_used": "One sentence describing the strategy applied",
  "preview_text": "Short 50-char preview snippet"
}}"""

    groq_client = genai_service.client if not genai_service.use_mock else None

    if groq_client:
        try:
            import json as _json, re as _re
            response = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a banking marketing API. Return only valid JSON."},
                    {"role": "user", "content": _trim_prompt(prompt)},
                ],
                model="qwen/qwen3.6-27b",
                temperature=0.7,
                max_tokens=1200,
            )
            parsed = _safe_parse_groq_json(response.choices[0].message.content, "PERSONALISED_MSG")
            if not parsed:
                parsed = _fallback_personalised_message(first_name, req.product, age_group, req.channel)
        except Exception as e:
            print(f"Personalised message generation error: {e}")
            parsed = _fallback_personalised_message(first_name, req.product, age_group, req.channel)
    else:
        parsed = _fallback_personalised_message(first_name, req.product, age_group, req.channel)

    return {
        "customer_id":    req.customer_id,
        "customer_name":  f"{first_name} {last_name}",
        "age":            age,
        "age_group":      age_group,
        "channel":        req.channel,
        "product":        req.product,
        "subject":        parsed.get("subject", ""),
        "body":           parsed.get("body", ""),
        "strategy_used":  parsed.get("strategy_used", strategy["opener_style"]),
        "preview_text":   parsed.get("preview_text", ""),
    }


def _fallback_personalised_message(first_name: str, product: str, age_group: str, channel: str) -> dict:
    """Fallback when Groq is unavailable."""
    if age_group == "genz":
        if channel == "email":
            return {
                "subject": f"Psst {first_name}... your wallet called 📲",
                "body": f"Hey {first_name}!\n\nReal talk — you've been missing out on serious perks.\n\nThe {product} is literally made for someone like you. Zero fees. Max rewards. No cap.\n\nTap below before the offer expires. Your future self will thank you. 🔥",
                "strategy_used": "Gen Z FOMO-driven direct hook with casual tone",
                "preview_text": "Your wallet called. It's time.",
            }
        else:
            return {
                "subject": f"Oi {first_name}! 👀 {product} — don't sleep on this",
                "body": f"Oi {first_name}! 👀 {product} wala offer chhoot raha hai. Quickly check it out: npnbank.in/offers",
                "strategy_used": "Gen Z ultra-short SMS with casual Hindi-English mix",
                "preview_text": "Don't sleep on this offer.",
            }
    elif age_group == "millennial":
        if channel == "email":
            return {
                "subject": f"Congratulations {first_name} — You've been pre-selected! 🎉",
                "body": f"Dear {first_name},\n\nCongratulations! Based on your excellent financial profile, you've been exclusively pre-selected for the {product}.\n\nThis isn't a mass offer — your profile stood out among thousands. You've earned this.\n\nUnlock your exclusive access before it expires.\n\nBest,\nNPN Bank",
                "strategy_used": "Millennial achievement-framing with Unstop-style congratulations opener",
                "preview_text": "You've been pre-selected!",
            }
        else:
            return {
                "subject": f"Congrats {first_name}! Pre-approved for {product}",
                "body": f"Congrats {first_name}! You're pre-approved for {product}. Exclusively for you. Activate: npnbank.in/activate",
                "strategy_used": "Millennial achievement SMS with congratulations opener",
                "preview_text": "You're pre-approved!",
            }
    elif age_group == "genx":
        if channel == "email":
            return {
                "subject": f"Maximise Your Returns in {datetime.now().year} — Exclusive for You",
                "body": f"Dear {first_name},\n\nAs a valued NPN Bank customer, we've identified an opportunity to strengthen your financial portfolio.\n\nThe {product} offers measurable benefits aligned with your goals — tax efficiency, higher returns, and complete security of your funds.\n\nOur relationship managers are available to walk you through the details at your convenience.\n\nView your offer: npnbank.in/offers\n\nBest regards,\nNPN Bank Relationship Team",
                "strategy_used": "Gen X ROI-focused professional tone with trust signals",
                "preview_text": "Strengthen your portfolio today.",
            }
        else:
            return {
                "subject": f"Exclusive offer for {first_name}: {product}",
                "body": f"Dear {first_name}, maximize your returns with {product}. Trusted by 10L+ customers. Details: npnbank.in/offers or call 1800-NPN-BANK",
                "strategy_used": "Gen X ROI-focused concise SMS with trust signal",
                "preview_text": "Maximize your financial returns.",
            }
    else:  # boomer
        if channel == "email":
            return {
                "subject": f"A Special Message for You, {first_name}",
                "body": f"Dear {first_name},\n\nAs a deeply valued member of the NPN Bank family, we take great pride in serving you.\n\nWe have prepared a special, curated offer for the {product} — designed with your financial security and comfort in mind.\n\nYour dedicated Relationship Manager will be happy to assist you with any questions.\n\nPlease visit your nearest NPN Bank branch or call us at 1800-NPN-BANK at your convenience.\n\nWith warm regards,\nPriya Sharma\nRelationship Manager, NPN Bank",
                "strategy_used": "Boomer formal relationship-based tone with personal sign-off",
                "preview_text": "A personal message from your bank.",
            }
        else:
            return {
                "subject": f"Dear {first_name}, special offer from NPN Bank",
                "body": f"Dear {first_name}, we have a special {product} offer prepared for you. Please call 1800-NPN-BANK or visit your nearest branch. We are here to assist you.",
                "strategy_used": "Boomer formal SMS with branch/call CTA",
                "preview_text": "Special offer from your bank.",
            }


@app.post("/api/campaigns/{campaign_id}/analytics/event", tags=["Campaigns"])
def record_campaign_event(
    campaign_id: str,
    event: CampaignAnalyticsEvent,
    current_employee=Depends(get_current_employee),
):
    """Record an analytics event (opened, clicked, applied, converted) for a campaign."""
    import json as _json
    valid_events = {"opened", "clicked", "applied", "converted"}
    if event.event_type not in valid_events:
        return {"status": "ignored", "event": event.event_type}

    with get_db_connection() as conn:
        res = conn.execute(text("SELECT events FROM campaign_analytics WHERE campaign_id = :id"), {"id": campaign_id}).fetchone()
        if not res:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # update counter
        conn.execute(
            text(f"UPDATE campaign_analytics SET {event.event_type} = {event.event_type} + 1 WHERE campaign_id = :id"),
            {"id": campaign_id}
        )

        # update events jsonb
        events_list = []
        if res[0]:
            try:
                events_list = _json.loads(res[0]) if isinstance(res[0], str) else res[0]
            except:
                pass
        
        events_list.append({
            "type":        event.event_type,
            "customer_id": event.customer_id,
            "channel":     event.channel,
            "timestamp":   datetime.now().isoformat(),
        })

        conn.execute(
            text("UPDATE campaign_analytics SET events = :events WHERE campaign_id = :id"),
            {"events": _json.dumps(events_list), "id": campaign_id}
        )
        conn.commit()

    return {"status": "recorded", "event": event.event_type}


@app.get("/api/campaigns/{campaign_id}/analytics", tags=["Campaigns"])
def get_campaign_analytics(
    campaign_id: str,
    current_employee=Depends(get_current_employee),
):
    """Get full analytics for a specific campaign."""
    import json as _json
    with get_db_connection() as conn:
        campaign_row = conn.execute(text("SELECT * FROM campaigns WHERE id = :id"), {"id": campaign_id}).mappings().fetchone()
        if not campaign_row:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        analytics_row = conn.execute(text("SELECT * FROM campaign_analytics WHERE campaign_id = :id"), {"id": campaign_id}).mappings().fetchone()
        
    campaign = dict(campaign_row)
    
    if analytics_row:
        analytics = dict(analytics_row)
    else:
        analytics = {
            "sent": campaign.get("audience_count", 0),
            "opened": 0, "clicked": 0, "applied": 0, "converted": 0,
            "channel_breakdown": {"email": {"sent": 0, "opened": 0}, "sms": {"sent": 0, "opened": 0}},
            "events": [],
            "hourly_opens": [],
        }

    # deserialize JSON fields if they are strings
    def parse_json_col(val, default):
        if isinstance(val, str):
            try:
                return _json.loads(val)
            except:
                return default
        return val if val is not None else default

    analytics["channel_breakdown"] = parse_json_col(analytics.get("channel_breakdown"), {"email": {"sent": 0, "opened": 0}, "sms": {"sent": 0, "opened": 0}})
    analytics["events"] = parse_json_col(analytics.get("events"), [])
    analytics["hourly_opens"] = parse_json_col(analytics.get("hourly_opens"), [])

    sent = max(analytics.get("sent", 1), 1)
    opened    = analytics.get("opened", 0)
    clicked   = analytics.get("clicked", 0)
    applied   = analytics.get("applied", 0)
    converted = analytics.get("converted", 0)

    open_rate      = round((opened / sent) * 100, 1)
    click_rate     = round((clicked / max(opened, 1)) * 100, 1)
    apply_rate     = round((applied / max(clicked, 1)) * 100, 1)
    conv_rate      = round((converted / max(applied, 1)) * 100, 1)
    overall_conv   = round((converted / sent) * 100, 2)

    # Low performance detection
    is_low_open   = open_rate < 30
    is_low_click  = click_rate < 20
    is_low_conv   = overall_conv < 2.0

    flags = []
    if is_low_open:
        flags.append("LOW_OPEN_RATE")
    if is_low_click:
        flags.append("LOW_CLICK_RATE")
    if is_low_conv:
        flags.append("LOW_CONVERSION")

    return {
        "campaign_id":   campaign_id,
        "campaign_name": campaign.get("campaign_name", ""),
        "product":       campaign.get("product", ""),
        "channel":       campaign.get("channel", ""),
        "audience_count": campaign.get("audience_count", 0),
        "metrics": {
            "sent":      sent,
            "opened":    opened,
            "clicked":   clicked,
            "applied":   applied,
            "converted": converted,
        },
        "rates": {
            "open_rate":    open_rate,
            "click_rate":   click_rate,
            "apply_rate":   apply_rate,
            "conv_rate":    conv_rate,
            "overall_conv": overall_conv,
        },
        "channel_breakdown": analytics.get("channel_breakdown", {}),
        "hourly_opens":      analytics.get("hourly_opens", []),
        "performance_flags": flags,
        "events_count":      len(analytics.get("events", [])),
        "created_at":        campaign.get("created_at", ""),
    }


@app.get("/api/campaigns/insights", tags=["Campaigns"])
def get_campaign_insights(current_employee=Depends(get_current_employee)):
    """
    AI self-learning insights: analyze all campaign performance data,
    detect low-performing campaigns, and generate improvement recommendations.
    """
    import json as _json

    eng = get_engines()
    genai_service = eng["genai_service"]

    with get_db_connection() as conn:
        campaigns_list = conn.execute(text("SELECT * FROM campaigns ORDER BY created_at DESC LIMIT 10")).mappings().all()

    if not campaigns_list:
        return {
            "insights": [],
            "overall_health": "No campaigns launched yet. Create your first campaign to see AI insights.",
            "top_recommendation": "Start with a Travel Credit Card campaign targeting Frequent Travellers — highest historical conversion rate.",
        }

    # Build performance summary for all campaigns
    campaign_summaries = []
    with get_db_connection() as conn:
        for c in campaigns_list:
            cid = c["id"]
            analytics_row = conn.execute(text("SELECT sent, opened, converted FROM campaign_analytics WHERE campaign_id = :id"), {"id": cid}).mappings().fetchone()
            
            if analytics_row:
                sent = max(analytics_row.get("sent") or c.get("audience_count") or 1, 1)
                opened = analytics_row.get("opened") or 0
                converted = analytics_row.get("converted") or 0
            else:
                sent = max(c.get("audience_count") or 1, 1)
                opened = 0
                converted = 0

            open_rate = round((opened / sent) * 100, 1)
            conv_rate = round((converted / sent) * 100, 2)
            campaign_summaries.append(
                f"- Campaign '{c['campaign_name']}' | Product: {c['product']} | Channel: {c['channel']} "
                f"| Sent: {sent} | Open Rate: {open_rate}% | Conv Rate: {conv_rate}% "
                f"| Age Strategy: {c.get('age_group_strategy', 'auto')}"
            )

    performance_data = "\n".join(campaign_summaries)

    prompt = f"""You are an AI marketing analyst for NPN Bank India. Analyze these campaign performance metrics and provide insights.

CAMPAIGN PERFORMANCE DATA:
{performance_data}

INDUSTRY BENCHMARKS:
- Banking email open rate: 25-35% is average, >45% is excellent
- Banking SMS open rate: 60-80% is average, >85% is excellent
- Banking conversion rate: 2-4% is average, >5% is excellent

AGE-BASED MARKETING INSIGHTS (from research):
- Gen Z responds 3x better to SMS than email, needs contextual/humorous hooks
- Millennials open achievement-framing emails 40% more (Congratulations opener)
- Gen X needs ROI data-points to click
- Boomers prefer phone/branch CTA over digital links

BASED ON THE DATA ABOVE, provide:
1. Analysis of what's working and what isn't
2. Why low-response campaigns failed (specific hypotheses)
3. Top 3 actionable recommendations for next campaigns
4. Best timing, channel, and age strategy suggestions

Return valid JSON:
{{
  "overall_health": "One sentence summary of portfolio health",
  "insights": [
    {{"type": "warning|success|info", "title": "Short title", "description": "Detailed insight"}}
  ],
  "top_recommendation": "The single most impactful change to make",
  "best_channel": "Email or SMS and why",
  "best_timing": "Best day/time to send campaigns",
  "next_campaign_suggestion": "Specific campaign suggestion with product, segment, and strategy"
}}"""

    if not genai_service.use_mock:
        try:
            import re as _re
            response = genai_service.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a banking marketing analytics AI. Return only valid JSON."},
                    {"role": "user", "content": _trim_prompt(prompt)},
                ],
                model="qwen/qwen3.6-27b",
                temperature=0.3,
                max_tokens=1200,
            )
            parsed = _safe_parse_groq_json(response.choices[0].message.content, "INSIGHTS")
            if parsed:
                return parsed
        except Exception as e:
            print(f"Campaign insights error: {e}")

    # Fallback static insights
    with get_db_connection() as conn:
        total_campaigns = conn.execute(text("SELECT COUNT(*) FROM campaigns")).scalar()

    return {
        "overall_health": f"{total_campaigns} campaigns active. Performance tracking in progress.",
        "insights": [
            {"type": "info",    "title": "SMS outperforms Email for Gen Z", "description": "Customers aged 18-25 show 3x higher response to SMS messages with contextual hooks vs formal emails."},
            {"type": "success", "title": "Achievement-framing boosts Millennial open rates", "description": "Emails starting with 'Congratulations!' see 40% higher open rates among 26-40 age group."},
            {"type": "warning", "title": "Generic subject lines reduce open rates", "description": "Campaigns with non-personalised subject lines see open rates below 20% vs 55%+ for personalised ones."},
            {"type": "info",    "title": "Optimal send time: 8-10 PM weekdays", "description": "Banking campaign opens peak at 8-10 PM on Tuesday/Wednesday when customers review finances."},
        ],
        "top_recommendation": "Use age-group specific messaging — apply Gen Z tone for under-25, achievement-framing for 26-40, ROI focus for 41-55.",
        "best_channel": "SMS for Gen Z (open rate 85%+), Email for Millennials/Gen X (higher click-through)",
        "best_timing": "Tuesday-Thursday, 8-10 PM IST (post-dinner financial review time)",
        "next_campaign_suggestion": "Travel Credit Card campaign targeting Frequent Travellers using Millennial achievement-framing — highest historical conversion at 5.8%",
    }


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
    """List segments using customer_segment_type directly from DB - no AI engine needed."""
    engines = get_engines()
    customers_df = engines["customers_df"]
    total_customers = len(customers_df)

    # Count customers per segment directly from the stored column
    seg_counts: dict = {s["name"]: 0 for s in SEGMENT_DEFINITIONS}
    seg_income_sum: dict = {s["name"]: 0.0 for s in SEGMENT_DEFINITIONS}

    if "customer_segment_type" in customers_df.columns:
        for _, row in customers_df.iterrows():
            seg_name = str(row.get("customer_segment_type", ""))
            if seg_name in seg_counts:
                seg_counts[seg_name] += 1
                seg_income_sum[seg_name] += float(row.get("annual_income", 0) or 0)

    matched_total = sum(seg_counts.values()) or 1

    result = []
    for seg_def in SEGMENT_DEFINITIONS:
        count = seg_counts[seg_def["name"]]
        avg_income_monthly = (seg_income_sum[seg_def["name"]] / max(seg_counts[seg_def["name"]], 1)) / 12
        percentage = round(count / total_customers * 100, 1) if total_customers > 0 else 0

        result.append({
            "id":                 seg_def["id"],
            "name":               seg_def["name"],
            "count":              count,
            "percentage":         percentage,
            "avgSpending":        f"Rs{avg_income_monthly:,.0f}",
            "avgSpendingRaw":     avg_income_monthly,
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
    with get_db_connection() as conn:
        total_campaigns = conn.execute(text("SELECT COUNT(*) FROM campaigns")).scalar()
        
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


# ═══════════════════════════════════════════════════════════════════════════════
# Chatbot  — POST /chatbot/ask
# Standalone endpoint: phone_number + message → Groq-powered personalized answer
# ═══════════════════════════════════════════════════════════════════════════════

import re as _re_chat

def _strip_think(text: str) -> str:
    """Remove <think>...</think> blocks from qwen3 chain-of-thought output."""
    text = _re_chat.sub(r"<think>[\s\S]*?</think>", "", text)
    if "<think>" in text:
        text = text[:text.index("<think>")]
    if "</think>" in text:
        text = text[text.rindex("</think>") + len("</think>"):]
    return text.strip()

def _normalise_phone(phone: str) -> str:
    digits = _re_chat.sub(r"\D", "", phone)
    return digits[-10:] if len(digits) >= 10 else digits

class ChatbotAskRequest(BaseModel):
    message: str
    phone_number: Optional[str] = None
    customer_id: Optional[str] = None
    conversation_id: Optional[str] = None

@app.post("/chatbot/ask", tags=["Chatbot"])
def chatbot_ask(req: ChatbotAskRequest):
    """
    Bank marketing chatbot endpoint.

    Pass phone_number OR customer_id. The bot fetches the customer's C360
    profile, builds context (segment, income, products held, financial gaps,
    life events) and asks Groq to generate a warm, concise, personalized answer.
    """
    engines = get_engines()
    customers_df: "pd.DataFrame" = engines["customers_df"]

    # ── 1. Resolve phone → customer_id ───────────────────────────────────────
    resolved_id = req.customer_id
    if req.phone_number and not resolved_id:
        if "mobile_number" not in customers_df.columns:
            raise HTTPException(status_code=400, detail="mobile_number column not found in customers data")
        norm = _normalise_phone(req.phone_number)
        mask = customers_df["mobile_number"].astype(str).apply(
            lambda x: _normalise_phone(x) == norm
        )
        matches = customers_df[mask]
        if matches.empty:
            raise HTTPException(status_code=404, detail=f"No customer found for phone ending in {norm[-4:]}")
        resolved_id = str(matches.iloc[0]["customer_id"])

    # ── 2. Build customer context (PII-free) ─────────────────────────────────
    customer_summary = ""
    if resolved_id:
        row = customers_df[customers_df["customer_id"] == resolved_id]
        if not row.empty:
            d = row.iloc[0].to_dict()
            parts = []
            if d.get("age"):            parts.append(f"Age: {d['age']}")
            if d.get("customer_segment_type"): parts.append(f"Segment: {d['customer_segment_type']}")
            if d.get("credit_score"):   parts.append(f"Credit Score: {d['credit_score']}")
            if d.get("annual_income"):  parts.append(f"Annual Income: ₹{int(d['annual_income']):,}")

            try:
                fe: "FeatureEngine" = engines["feature_engine"]
                feat = fe.compute(resolved_id, d)
                if getattr(feat, "monthly_income_avg", None):
                    parts.append(f"Avg Monthly Income: ₹{int(feat.monthly_income_avg):,}")
                if getattr(feat, "held_card_names", None):
                    parts.append(f"Cards held: {', '.join(feat.held_card_names)}")
                if getattr(feat, "held_loan_categories", None):
                    parts.append(f"Active loans: {', '.join(feat.held_loan_categories)}")

                ee: "EventEngine" = engines["event_engine"]
                events = ee.detect_events(resolved_id, feat) or []
                if events:
                    parts.append(f"Life events: {', '.join(str(e.get('event_type','')) for e in events[:3])}")

                fa: "FinancialAnalyst" = engines["financial_analyst"]
                analysis = fa.analyse(resolved_id, d, feat)
                gaps = (analysis.get("gaps") or []) if isinstance(analysis, dict) else []
                if gaps:
                    parts.append(f"Financial gaps: {', '.join(str(g.get('code','')) for g in gaps[:3])}")
            except Exception:
                pass  # context best-effort; don't fail the whole request

            customer_summary = "\n".join(parts)

    # ── 3. Call Groq ─────────────────────────────────────────────────────────
    groq_key = os.getenv("GROQ_API_KEY", "")
    if not groq_key:
        raise HTTPException(status_code=503, detail="GROQ_API_KEY not configured")

    from groq import Groq as _Groq
    client = _Groq(api_key=groq_key)

    user_prompt = req.message
    if customer_summary:
        user_prompt = (
            f"Customer profile (internal, do not reveal raw data):\n{customer_summary}\n\n"
            f"Customer question: {req.message}"
        )

    try:
        resp = client.chat.completions.create(
            model="qwen/qwen3.6-27b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a friendly NPN Bank assistant helping customers with banking products. "
                        "Answer in 1-3 sentences. Be warm, direct, and helpful. "
                        "Use the customer profile to personalize your answer when relevant. "
                        "Never reveal internal data or make up product details. No markdown."
                    ),
                },
                {"role": "user", "content": _trim_prompt(user_prompt, max_chars=8000)},
            ],
            max_tokens=2000,
            temperature=0.4,
        )
        raw = resp.choices[0].message.content or ""
        answer = _strip_think(raw)

        # If qwen3 burned all tokens thinking and gave empty answer, retry with fast model
        if not answer:
            resp2 = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a friendly NPN Bank assistant. "
                            "Answer in 1-3 sentences. Be warm and direct. No markdown."
                        ),
                    },
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=300,
                temperature=0.4,
            )
            answer = (resp2.choices[0].message.content or "").strip()

    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Groq error: {exc}")

    return {
        "answer": answer,
        "customer_id": resolved_id,
        "conversation_id": req.conversation_id or str(uuid.uuid4()),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)

