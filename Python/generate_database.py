# -*- coding: utf-8 -*-
"""
generate_database.py
====================
NPN Bank — Master Database Generation Script v2.0

ONE script to:
  1. Generate all product catalogues (credit cards, loans, investments, insurance, debit cards)
  2. Generate merchant master
  3. Generate 1000 diverse customers
  4. Assign products using eligibility + income + occupation logic
  5. Generate correlated transactions (~15,000 rows)
  6. Build Customer 360 JSON
  7. Validate all data (FK, uniqueness, business rules)
  8. Push everything to Supabase in correct insertion order
  9. Print a full summary

Usage:
    python generate_database.py            # Generate + Push
    python generate_database.py --csv-only # Generate CSVs only, no Supabase push
    python generate_database.py --reset    # Truncate Supabase tables before insert
"""

import sys
import os
import csv
import json
import math
import random
import uuid
import argparse
from pathlib import Path
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

# -- Argument parsing ----------------------------------------------------------
parser = argparse.ArgumentParser(description="NPN Bank Master DB Generator")
parser.add_argument("--csv-only", action="store_true", help="Generate CSVs only, skip Supabase")
parser.add_argument("--reset", action="store_true", help="Truncate Supabase tables before insert")
parser.add_argument("--no-hash", action="store_true", help="Skip bcrypt hashing (faster testing)")
args = parser.parse_args()

# -- Environment ---------------------------------------------------------------
from dotenv import load_dotenv
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

SUPABASE_DB_URL = os.environ.get("SUPABASE_DB_URL", "")

# -- Output directory ----------------------------------------------------------
OUTPUT_DIR = BASE_DIR / "Database_csvs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Sub-directory for customer holdings CSVs
HOLDINGS_DIR = OUTPUT_DIR / "generated_customer_360"
HOLDINGS_DIR.mkdir(parents=True, exist_ok=True)

# -- Config --------------------------------------------------------------------
random.seed(42)
NUM_CUSTOMERS    = 1000
BATCH_SIZE       = 500
TODAY            = date.today()
NOW_TS           = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
END_DATE         = datetime(TODAY.year, TODAY.month, TODAY.day)
START_DATE       = END_DATE - timedelta(days=365)

print(f"\n{'='*60}")
print("NPN Bank — Master Database Generation v2.0")
print(f"Customers: {NUM_CUSTOMERS} | Date: {TODAY}")
print(f"Output:    {OUTPUT_DIR}")
print(f"Supabase:  {'PUSH' if not args.csv_only else 'SKIP'}")
print(f"{'='*60}\n")


# ═══════════════════════════════════════════════════════════════
# SECTION 0 — HELPERS
# ═══════════════════════════════════════════════════════════════

def wbool(p: float) -> bool:
    return random.random() < p

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def wchoice(items: List[Tuple]):
    vals   = [x[0] for x in items]
    weights = [x[1] for x in items]
    return random.choices(vals, weights=weights, k=1)[0]

def rdate(start: date, end: date) -> date:
    if end <= start:
        return start
    return start + timedelta(days=random.randint(0, (end - start).days))

def to_float(v, default=0.0) -> float:
    try:
        return float(str(v).replace(",", "").replace("₹", "").strip())
    except Exception:
        return default

def write_csv(filepath: Path, rows: List[Dict], description: str):
    if not rows:
        print(f"  [WARN] {description}: 0 rows — skipping")
        return
    fieldnames = list(rows[0].keys())
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  [CSV]  {description}: {len(rows):,} rows -> {filepath.name}")

def clean_val(val):
    if val is None:
        return None
    try:
        if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
            return None
    except Exception:
        pass
    try:
        import pandas as _pd
        if _pd.isna(val):
            return None
    except Exception:
        pass
    return val


# ═══════════════════════════════════════════════════════════════
# SECTION 1 — PRODUCT CATALOGUES
# ═══════════════════════════════════════════════════════════════

print("PHASE 1 — Generating product catalogues...")

# -- 1A: Credit Card Products ----------------------------------

def _cc(pid, code, name, variant, category, **kw) -> Dict:
    d = {
        "credit_card_product_id": pid,
        "product_code":           code,
        "card_name":              name,
        "card_variant":           variant,
        "card_category":          category,
        "card_type":              kw.get("card_type", "Personal"),
        "card_network":           kw.get("card_network", "Visa"),
        "card_form_factor":       kw.get("card_form_factor", "Physical"),
        "co_brand":               kw.get("co_brand", "No"),
        "co_brand_partner":       kw.get("co_brand_partner", "Not Applicable"),
        "product_status":         kw.get("product_status", "Active"),
        "product_description":    kw.get("product_description", "HDFC Bank credit card."),
        "joining_fee":            kw.get("joining_fee", 0),
        "annual_fee":             kw.get("annual_fee", 0),
        "renewal_fee":            kw.get("renewal_fee", 0),
        "first_year_fee_waiver":  kw.get("first_year_fee_waiver", 0),
        "renewal_fee_waiver":     kw.get("renewal_fee_waiver", 0),
        "interest_rate_monthly":  kw.get("interest_rate_monthly", 3.75),
        "interest_rate_annual":   kw.get("interest_rate_annual", 45.0),
        "minimum_age":            kw.get("minimum_age", 21),
        "maximum_age":            kw.get("maximum_age", 65),
        "minimum_income_monthly": kw.get("minimum_income_monthly", 0),
        "minimum_income_annual":  kw.get("minimum_income_annual", 0),
        "employment_type":        kw.get("employment_type", "Salaried / Self-employed"),
        "minimum_credit_score":   kw.get("minimum_credit_score", 650),
        "residential_requirement":kw.get("residential_requirement", "Resident Indian"),
        "existing_customer_required": kw.get("existing_customer_required", "No"),
        "minimum_credit_limit":   kw.get("minimum_credit_limit", 10000),
        "maximum_credit_limit":   kw.get("maximum_credit_limit", 1000000),
        "airport_lounge_access":  kw.get("airport_lounge_access", "No"),
        "domestic_lounge_visits": kw.get("domestic_lounge_visits", 0),
        "tag_travel":             kw.get("tag_travel", 0),
        "tag_cashback":           kw.get("tag_cashback", 0),
        "tag_shopping":           kw.get("tag_shopping", 0),
        "tag_fuel":               kw.get("tag_fuel", 0),
        "tag_premium":            kw.get("tag_premium", 0),
        "tag_dining":             kw.get("tag_dining", 0),
        "tag_airport_lounge":     kw.get("tag_airport_lounge", 0),
        "reward_program_name":    kw.get("reward_program_name", "Reward Points"),
        "reward_type":            kw.get("reward_type", "Reward Points"),
        "reward_points_per_amount":kw.get("reward_points_per_amount", 150),
        "reward_point_value":     kw.get("reward_point_value", 0.50),
        "cashback_rate":          kw.get("cashback_rate", 0),
        "cashback_available":     kw.get("cashback_available", "No"),
        "foreign_currency_markup":kw.get("foreign_currency_markup", 3.5),
        "created_at":             NOW_TS,
        "updated_at":             NOW_TS,
    }
    return d

CREDIT_CARD_PRODUCTS = [
    # -- Classic / Entry --------------------------------------
    _cc("CC001","HDFCFREEDOM","Freedom Credit Card","Classic","Classic",
        annual_fee=0, joining_fee=0, minimum_income_annual=120000,
        minimum_income_monthly=10000, minimum_credit_score=650,
        minimum_credit_limit=10000, maximum_credit_limit=100000,
        tag_cashback=1, cashback_available="Yes", cashback_rate=5.0),
    _cc("CC002","HDFCMB+","MoneyBack+ Credit Card","Classic","Classic",
        annual_fee=500, joining_fee=500, minimum_income_annual=180000,
        minimum_income_monthly=15000, minimum_credit_score=660,
        minimum_credit_limit=15000, maximum_credit_limit=150000,
        tag_cashback=1, tag_shopping=1, cashback_available="Yes", cashback_rate=2.0),
    # -- Premium -----------------------------------------------
    _cc("CC003","HDFCMILL","Millennia Credit Card","Premium","Premium",
        annual_fee=1000, joining_fee=1000, minimum_income_annual=300000,
        minimum_income_monthly=25000, minimum_credit_score=700,
        minimum_credit_limit=25000, maximum_credit_limit=500000,
        airport_lounge_access="Yes", domestic_lounge_visits=2,
        tag_cashback=1, tag_shopping=1, tag_travel=1,
        tag_airport_lounge=1, cashback_available="Yes", cashback_rate=5.0),
    _cc("CC004","HDFCRGOLD","Regalia Gold","Premium","Premium",
        annual_fee=2500, joining_fee=2500, minimum_income_annual=600000,
        minimum_income_monthly=50000, minimum_credit_score=720,
        minimum_credit_limit=75000, maximum_credit_limit=1500000,
        airport_lounge_access="Yes", domestic_lounge_visits=4,
        tag_travel=1, tag_premium=1, tag_dining=1, tag_airport_lounge=1,
        reward_program_name="Reward Points", reward_points_per_amount=40,
        foreign_currency_markup=2.0),
    # -- Super Premium -----------------------------------------
    _cc("CC005","HDFCINFINIA","Infinia Metal","Super Premium","Super Premium",
        annual_fee=12500, joining_fee=12500, minimum_income_annual=2400000,
        minimum_income_monthly=200000, minimum_credit_score=780,
        card_network="Mastercard",
        minimum_credit_limit=500000, maximum_credit_limit=10000000,
        airport_lounge_access="Yes", domestic_lounge_visits=999,
        tag_travel=1, tag_premium=1, tag_dining=1, tag_airport_lounge=1,
        reward_points_per_amount=5, reward_point_value=1.0,
        foreign_currency_markup=0),
    _cc("CC006","HDFCDINERSBLK","Diners Black","Super Premium","Super Premium",
        annual_fee=10000, joining_fee=10000, minimum_income_annual=1800000,
        minimum_income_monthly=150000, minimum_credit_score=770,
        card_network="Diners Club",
        minimum_credit_limit=300000, maximum_credit_limit=8000000,
        airport_lounge_access="Yes", domestic_lounge_visits=999,
        tag_travel=1, tag_premium=1, tag_dining=1, tag_airport_lounge=1,
        reward_points_per_amount=5, reward_point_value=1.0),
    # -- Business ----------------------------------------------
    _cc("CC007","HDFCBIZBK","Business Credit Card","Business","Classic",
        annual_fee=1000, joining_fee=1000, minimum_income_annual=600000,
        minimum_income_monthly=50000, minimum_credit_score=700,
        card_type="Business",
        minimum_credit_limit=50000, maximum_credit_limit=2000000,
        tag_cashback=1),
    _cc("CC008","HDFCBIZBLK","BizBlack Credit Card","Business","Super Premium",
        annual_fee=10000, joining_fee=10000, minimum_income_annual=3000000,
        minimum_income_monthly=250000, minimum_credit_score=760,
        card_type="Business", card_network="Mastercard",
        minimum_credit_limit=500000, maximum_credit_limit=15000000,
        airport_lounge_access="Yes", tag_premium=1, tag_travel=1),
    # -- Co-brand ----------------------------------------------
    _cc("CC009","HDFCSWIGGY","Swiggy HDFC Bank Credit Card","Co-brand","Premium",
        co_brand="Yes", co_brand_partner="Swiggy",
        annual_fee=500, joining_fee=500, minimum_income_annual=240000,
        minimum_income_monthly=20000, minimum_credit_score=680,
        card_network="Mastercard",
        minimum_credit_limit=20000, maximum_credit_limit=500000,
        tag_dining=1, tag_cashback=1, cashback_available="Yes", cashback_rate=10.0),
    _cc("CC010","HDFCTATANEU","Tata Neu Infinity","Co-brand","Premium",
        co_brand="Yes", co_brand_partner="Tata Neu",
        annual_fee=1499, joining_fee=1499, minimum_income_annual=360000,
        minimum_income_monthly=30000, minimum_credit_score=700,
        card_network="RuPay",
        minimum_credit_limit=30000, maximum_credit_limit=600000,
        tag_shopping=1, tag_cashback=1),
    _cc("CC011","HDFCINDOIL","IndianOil HDFC Bank Credit Card","Co-brand","Classic",
        co_brand="Yes", co_brand_partner="IndianOil",
        annual_fee=500, joining_fee=500, minimum_income_annual=240000,
        minimum_income_monthly=20000, minimum_credit_score=670,
        minimum_credit_limit=20000, maximum_credit_limit=300000,
        tag_fuel=1, cashback_available="Yes"),
    _cc("CC012","HDFCIRCTC","IRCTC HDFC Bank Credit Card","Co-brand","Classic",
        co_brand="Yes", co_brand_partner="IRCTC",
        annual_fee=500, joining_fee=500, minimum_income_annual=240000,
        minimum_income_monthly=20000, minimum_credit_score=670,
        card_network="RuPay",
        minimum_credit_limit=20000, maximum_credit_limit=300000,
        tag_travel=1),
    # -- Pixel / Digital ---------------------------------------
    _cc("CC013","HDFCPIXELGO","Pixel Go Credit Card","Classic","Classic",
        annual_fee=0, joining_fee=0, minimum_income_annual=180000,
        minimum_income_monthly=15000, minimum_credit_score=650,
        card_form_factor="Virtual",
        minimum_credit_limit=10000, maximum_credit_limit=150000,
        tag_cashback=1, cashback_available="Yes", cashback_rate=1.0),
    _cc("CC014","HDFCWOMEN","Women's Advantage Credit Card","Classic","Classic",
        annual_fee=500, joining_fee=500, minimum_income_annual=240000,
        minimum_income_monthly=20000, minimum_credit_score=680,
        minimum_credit_limit=20000, maximum_credit_limit=300000,
        tag_shopping=1, tag_cashback=1),
    # -- Defence ----------------------------------------------
    _cc("CC015","HDFCDEFENCE","Defence Credit Card","Classic","Classic",
        annual_fee=0, joining_fee=0, minimum_income_annual=200000,
        minimum_income_monthly=17000, minimum_credit_score=680,
        employment_type="Defence Personnel / Salaried",
        minimum_credit_limit=15000, maximum_credit_limit=250000),
]

write_csv(OUTPUT_DIR / "credit_card_products.csv", CREDIT_CARD_PRODUCTS, "Credit Card Products")


# -- 1B: Loan Products -----------------------------------------

def _ln(pid, code, name, category, subcategory, ltype, **kw) -> Dict:
    return {
        "loan_product_id":        pid,
        "product_code":           code,
        "product_name":           name,
        "loan_category":          category,
        "loan_subcategory":       subcategory,
        "loan_type":              ltype,
        "customer_type":          kw.get("customer_type", "Individual"),
        "secured_or_unsecured":   kw.get("secured_or_unsecured", "Unsecured"),
        "product_status":         kw.get("product_status", "Active"),
        "loan_purpose":           kw.get("loan_purpose", "General"),
        "minimum_loan_amount":    kw.get("minimum_loan_amount", 50000),
        "maximum_loan_amount":    kw.get("maximum_loan_amount", 2500000),
        "minimum_tenure_months":  kw.get("minimum_tenure_months", 12),
        "maximum_tenure_months":  kw.get("maximum_tenure_months", 60),
        "typical_tenure_months":  kw.get("typical_tenure_months", 36),
        "interest_rate_min":      kw.get("interest_rate_min", 10.5),
        "interest_rate_max":      kw.get("interest_rate_max", 18.0),
        "interest_rate_current":  kw.get("interest_rate_current", 12.5),
        "processing_fee_value":   kw.get("processing_fee_value", 1.0),
        "minimum_age":            kw.get("minimum_age", 21),
        "maximum_age":            kw.get("maximum_age", 60),
        "minimum_income_annual":  kw.get("minimum_income_annual", 200000),
        "minimum_income_monthly": kw.get("minimum_income_monthly", 17000),
        "minimum_credit_score":   kw.get("minimum_credit_score", 700),
        "employment_type":        kw.get("employment_type", "Salaried / Self-employed"),
        "collateral_required":    kw.get("collateral_required", "No"),
        "created_at":             NOW_TS,
        "updated_at":             NOW_TS,
    }

LOAN_PRODUCTS = [
    _ln("LN001","HDFCPL","Personal Loan","Personal","Unsecured Personal","Fixed Rate",
        minimum_loan_amount=50000, maximum_loan_amount=4000000,
        minimum_income_annual=300000, minimum_income_monthly=25000,
        interest_rate_min=10.5, interest_rate_max=21.0, interest_rate_current=13.0,
        minimum_credit_score=700, minimum_tenure_months=12, maximum_tenure_months=60),
    _ln("LN002","HDFCHL","Home Loan","Home","Regular Home Loan","Floating Rate",
        secured_or_unsecured="Secured", collateral_required="Yes",
        minimum_loan_amount=500000, maximum_loan_amount=100000000,
        minimum_income_annual=400000, minimum_income_monthly=33000,
        interest_rate_min=8.35, interest_rate_max=10.0, interest_rate_current=8.7,
        minimum_credit_score=720, minimum_tenure_months=60, maximum_tenure_months=360,
        typical_tenure_months=240, loan_purpose="Home Purchase / Construction",
        minimum_age=21, maximum_age=60),
    _ln("LN003","HDFCNEWCAR","New Car Loan","Auto","New Vehicle","Floating Rate",
        secured_or_unsecured="Secured", collateral_required="Yes",
        minimum_loan_amount=100000, maximum_loan_amount=15000000,
        minimum_income_annual=250000, minimum_income_monthly=21000,
        interest_rate_min=7.9, interest_rate_max=11.5, interest_rate_current=8.75,
        minimum_credit_score=700, minimum_tenure_months=12, maximum_tenure_months=84,
        typical_tenure_months=60, loan_purpose="New Vehicle Purchase"),
    _ln("LN004","HDFCUSEDCAR","Used Car Loan","Auto","Used Vehicle","Fixed Rate",
        secured_or_unsecured="Secured", collateral_required="Yes",
        minimum_loan_amount=100000, maximum_loan_amount=5000000,
        minimum_income_annual=200000, minimum_income_monthly=17000,
        interest_rate_min=11.0, interest_rate_max=15.0, interest_rate_current=12.5,
        minimum_credit_score=680, minimum_tenure_months=12, maximum_tenure_months=60),
    _ln("LN005","HDFCTWOWHL","Two-Wheeler Loan","Two-Wheeler","Bike / Scooter","Fixed Rate",
        secured_or_unsecured="Secured", collateral_required="Yes",
        minimum_loan_amount=25000, maximum_loan_amount=500000,
        minimum_income_annual=100000, minimum_income_monthly=9000,
        interest_rate_min=14.0, interest_rate_max=18.0, interest_rate_current=15.5,
        minimum_credit_score=650, minimum_tenure_months=12, maximum_tenure_months=48,
        minimum_age=18, maximum_age=60),
    _ln("LN006","HDFCEDL","Education Loan","Education","Graduate / PG","Floating Rate",
        secured_or_unsecured="Secured / Unsecured",
        minimum_loan_amount=100000, maximum_loan_amount=2000000,
        minimum_income_annual=0, minimum_income_monthly=0,
        interest_rate_min=9.0, interest_rate_max=13.5, interest_rate_current=10.5,
        minimum_credit_score=0, minimum_tenure_months=12, maximum_tenure_months=180,
        minimum_age=16, maximum_age=35, loan_purpose="Education",
        customer_type="Individual / Student"),
    _ln("LN007","HDFCGOLD","Gold Loan","Gold","Gold Ornaments","Fixed Rate",
        secured_or_unsecured="Secured", collateral_required="Yes",
        minimum_loan_amount=10000, maximum_loan_amount=5000000,
        minimum_income_annual=0, minimum_income_monthly=0,
        interest_rate_min=7.5, interest_rate_max=11.0, interest_rate_current=8.5,
        minimum_credit_score=0, minimum_tenure_months=3, maximum_tenure_months=24,
        minimum_age=18, maximum_age=70, loan_purpose="Personal / Emergency"),
    _ln("LN008","HDFCBIZL","Business Loan","Business","Unsecured Business","Fixed Rate",
        customer_type="Business",
        minimum_loan_amount=50000, maximum_loan_amount=40000000,
        minimum_income_annual=1200000, minimum_income_monthly=100000,
        interest_rate_min=11.0, interest_rate_max=18.0, interest_rate_current=13.5,
        minimum_credit_score=700, minimum_tenure_months=12, maximum_tenure_months=60,
        employment_type="Self-employed / Business", loan_purpose="Business Expansion / Working Capital"),
    _ln("LN009","HDFCWC","Working Capital Finance","Business","Cash Credit / OD","Floating Rate",
        customer_type="Business", secured_or_unsecured="Secured", collateral_required="Yes",
        minimum_loan_amount=500000, maximum_loan_amount=200000000,
        minimum_income_annual=2400000, minimum_income_monthly=200000,
        interest_rate_min=10.0, interest_rate_max=14.0, interest_rate_current=11.5,
        minimum_credit_score=700, minimum_tenure_months=12, maximum_tenure_months=12,
        employment_type="Self-employed / Business", loan_purpose="Working Capital"),
    _ln("LN010","HDFCLAP","Loan Against Property","Property","Residential / Commercial","Floating Rate",
        secured_or_unsecured="Secured", collateral_required="Yes",
        minimum_loan_amount=1000000, maximum_loan_amount=500000000,
        minimum_income_annual=600000, minimum_income_monthly=50000,
        interest_rate_min=9.0, interest_rate_max=12.0, interest_rate_current=10.0,
        minimum_credit_score=720, minimum_tenure_months=24, maximum_tenure_months=180,
        loan_purpose="Business / Personal"),
    _ln("LN011","HDFCLAS","Loan Against Securities","Investment","Equity / MF","Fixed Rate",
        secured_or_unsecured="Secured", collateral_required="Yes",
        minimum_loan_amount=500000, maximum_loan_amount=200000000,
        minimum_income_annual=600000, minimum_income_monthly=50000,
        interest_rate_min=9.5, interest_rate_max=12.0, interest_rate_current=10.5,
        minimum_credit_score=700, minimum_tenure_months=3, maximum_tenure_months=36,
        loan_purpose="Investment / Personal"),
    _ln("LN012","HDFCAGRI","Agriculture / Kisan Credit Card","Agriculture","Crop Loan","Floating Rate",
        secured_or_unsecured="Secured",
        minimum_loan_amount=10000, maximum_loan_amount=3000000,
        minimum_income_annual=0, minimum_income_monthly=0,
        interest_rate_min=7.0, interest_rate_max=10.0, interest_rate_current=7.5,
        minimum_credit_score=0, minimum_tenure_months=6, maximum_tenure_months=60,
        minimum_age=18, maximum_age=65, employment_type="Farmer / Agricultural",
        loan_purpose="Agriculture / Crop Production"),
    _ln("LN013","HDFCTRACTOR","Tractor Loan","Agriculture","Equipment Finance","Fixed Rate",
        secured_or_unsecured="Secured", collateral_required="Yes",
        minimum_loan_amount=200000, maximum_loan_amount=2000000,
        minimum_income_annual=0, minimum_income_monthly=0,
        interest_rate_min=8.5, interest_rate_max=12.0, interest_rate_current=9.5,
        minimum_credit_score=0, minimum_tenure_months=12, maximum_tenure_months=84,
        employment_type="Farmer / Agricultural", loan_purpose="Tractor / Farm Equipment"),
    _ln("LN014","HDFCOVERDRAFT","Overdraft Facility","Personal","Salary OD","Floating Rate",
        minimum_loan_amount=10000, maximum_loan_amount=500000,
        minimum_income_annual=240000, minimum_income_monthly=20000,
        interest_rate_min=12.0, interest_rate_max=16.0, interest_rate_current=13.5,
        minimum_credit_score=680, minimum_tenure_months=12, maximum_tenure_months=12,
        employment_type="Salaried", loan_purpose="Emergency / Short Term"),
]

write_csv(OUTPUT_DIR / "loan_products.csv", LOAN_PRODUCTS, "Loan Products")


# -- 1C: Investment Products -----------------------------------

def _inv(pid, code, name, cat, subcat, ptype, **kw) -> Dict:
    return {
        "investment_product_id":    pid,
        "product_code":             code,
        "product_name":             name,
        "product_category":         cat,
        "product_subcategory":      subcat,
        "product_type":             ptype,
        "provider":                 kw.get("provider", "HDFC Bank / HDFC Securities"),
        "issuer":                   kw.get("issuer", "Not Applicable"),
        "brand_name":               kw.get("brand_name", "HDFC"),
        "product_status":           kw.get("product_status", "Active"),
        "customer_type":            kw.get("customer_type", "Individual"),
        "residency_requirement":    kw.get("residency_requirement", "Resident Indian"),
        "minimum_age":              kw.get("minimum_age", 18),
        "maximum_age":              kw.get("maximum_age", 75),
        "minimum_income_annual":    kw.get("minimum_income_annual", 0),
        "employment_type":          kw.get("employment_type", "All"),
        "kyc_required":             kw.get("kyc_required", "Yes"),
        "demat_required":           kw.get("demat_required", "No"),
        "risk_profile":             kw.get("risk_profile", "Moderate"),
        "return_type":              kw.get("return_type", "Market Linked"),
        "minimum_investment":       kw.get("minimum_investment", 100),
        "maximum_investment":       kw.get("maximum_investment", 100000000),
        "minimum_monthly_investment": kw.get("minimum_monthly_investment", 500),
        "maximum_monthly_investment": kw.get("maximum_monthly_investment", 10000000),
        "indicative_return_min":    kw.get("indicative_return_min", 0),
        "indicative_return_max":    kw.get("indicative_return_max", 0),
        "guaranteed_return":        kw.get("guaranteed_return", "No"),
        "lock_in_period_months":    kw.get("lock_in_period_months", 0),
        "tax_benefit":              kw.get("tax_benefit", "No"),
        "created_at":               NOW_TS,
        "updated_at":               NOW_TS,
    }

INVESTMENT_PRODUCTS = [
    _inv("INV001","HDFCEQMF","HDFC Equity Mutual Fund","Mutual Fund","Large Cap","Mutual Fund - Lumpsum",
         provider="HDFC Mutual Fund", risk_profile="High",
         minimum_investment=5000, minimum_monthly_investment=500,
         indicative_return_min=10, indicative_return_max=15),
    _inv("INV002","HDFCBALF","HDFC Balanced Advantage Fund","Mutual Fund","Balanced Hybrid","Mutual Fund - Lumpsum",
         provider="HDFC Mutual Fund", risk_profile="Moderate",
         minimum_investment=5000, minimum_monthly_investment=500,
         indicative_return_min=8, indicative_return_max=12),
    _inv("INV003","HDFCLIQF","HDFC Liquid Fund","Mutual Fund","Liquid","Mutual Fund - Lumpsum",
         provider="HDFC Mutual Fund", risk_profile="Low",
         return_type="Market Linked",
         minimum_investment=5000, indicative_return_min=5, indicative_return_max=7),
    _inv("INV004","HDFCEQSIP","HDFC Equity SIP","SIP","Equity SIP","SIP",
         provider="HDFC Mutual Fund", risk_profile="High",
         minimum_monthly_investment=500, maximum_monthly_investment=500000,
         indicative_return_min=10, indicative_return_max=15),
    _inv("INV005","HDFCBALSIP","HDFC Balanced SIP","SIP","Balanced SIP","SIP",
         provider="HDFC Mutual Fund", risk_profile="Moderate",
         minimum_monthly_investment=500, indicative_return_min=8, indicative_return_max=12),
    _inv("INV006","HDFCCORPBOND","HDFC Corporate Bond","Bond","Corporate Bond","Bond",
         provider="HDFC Securities", risk_profile="Low-Moderate",
         minimum_investment=10000, guaranteed_return="No",
         indicative_return_min=6.5, indicative_return_max=8.5,
         demat_required="Yes"),
    _inv("INV007","NPSTIER1","NPS Tier I","NPS","National Pension System","NPS",
         provider="HDFC Pension", risk_profile="Moderate",
         minimum_investment=500, minimum_monthly_investment=500,
         lock_in_period_months=0, tax_benefit="Yes",
         indicative_return_min=8, indicative_return_max=10),
    _inv("INV008","HDFC3IN1","HDFC 3-in-1 Investment Account","Demat","Demat + Trading + Bank","Demat",
         provider="HDFC Securities", demat_required="Yes",
         minimum_investment=0, minimum_age=18),
    _inv("INV009","HDFCEQTRD","Equity Trading Account","Stock / Equity","Direct Equity","Stock / Equity",
         provider="HDFC Securities", demat_required="Yes", risk_profile="High",
         minimum_investment=1000,
         indicative_return_min=0, indicative_return_max=0),
    _inv("INV010","HDFCIPO","IPO Investment","IPO","Primary Market","IPO",
         provider="HDFC Securities", demat_required="Yes", risk_profile="High",
         minimum_investment=14000),
    _inv("INV011","HDFCETF","ETF - Nifty 50","ETF","Index ETF","ETF",
         provider="HDFC Securities", demat_required="Yes", risk_profile="Moderate",
         minimum_investment=1000, indicative_return_min=10, indicative_return_max=14),
    _inv("INV012","HDFCGOLDETF","Gold ETF","Gold ETF","Gold","Gold ETF",
         provider="HDFC Securities", demat_required="Yes", risk_profile="Low-Moderate",
         minimum_investment=1000, indicative_return_min=5, indicative_return_max=10),
    _inv("INV013","HDFCWM","Wealth Management Service","Wealth Management","Portfolio Management","Wealth Management",
         provider="HDFC Bank", minimum_income_annual=5000000,
         minimum_investment=5000000, risk_profile="Moderate"),
    _inv("INV014","HDFCPB","Private Banking","Private Banking","Ultra HNI","Private Banking",
         provider="HDFC Bank", minimum_income_annual=10000000,
         minimum_investment=50000000, risk_profile="Moderate"),
    _inv("INV015","HDFCSTKSIP","StockSIP","StockSIP","Equity SIP","StockSIP",
         provider="HDFC Securities", demat_required="Yes", risk_profile="High",
         minimum_monthly_investment=1000, indicative_return_min=10, indicative_return_max=18),
]

write_csv(OUTPUT_DIR / "investment_products.csv", INVESTMENT_PRODUCTS, "Investment Products")


# -- 1D: Insurance Products ------------------------------------

def _ins(pid, code, name, company, itype, plan_type, **kw) -> Dict:
    return {
        "insurance_product_id":     pid,
        "product_code":             code,
        "product_name":             name,
        "insurance_company":        company,
        "insurance_type":           itype,
        "plan_type":                plan_type,
        "product_status":           kw.get("product_status", "Active"),
        "customer_type":            kw.get("customer_type", "Individual"),
        "minimum_age":              kw.get("minimum_age", 18),
        "maximum_age":              kw.get("maximum_age", 65),
        "minimum_income_monthly":   kw.get("minimum_income_monthly", 0),
        "minimum_income_annual":    kw.get("minimum_income_annual", 0),
        "employment_type":          kw.get("employment_type", "Salaried / Self-employed"),
        "minimum_sum_insured":      kw.get("minimum_sum_insured", 100000),
        "maximum_sum_insured":      kw.get("maximum_sum_insured", 10000000),
        "premium_frequency":        kw.get("premium_frequency", "Yearly"),
        "minimum_premium":          kw.get("minimum_premium", 5000),
        "maximum_premium":          kw.get("maximum_premium", 100000),
        "waiting_period_days":      kw.get("waiting_period_days", 0),
        "maternity_benefit":        kw.get("maternity_benefit", "No"),
        "critical_illness_benefit": kw.get("critical_illness_benefit", "No"),
        "accidental_death_benefit": kw.get("accidental_death_benefit", "No"),
        "tax_benefit":              kw.get("tax_benefit", "Yes"),
        "cashless_claim_available": kw.get("cashless_claim_available", "No"),
        "network_hospitals":        kw.get("network_hospitals", 0),
        "created_at":               NOW_TS,
        "updated_at":               NOW_TS,
    }

INSURANCE_PRODUCTS = [
    _ins("INS001","HDFCLTERM","HDFC Life Click 2 Protect","HDFC Life","Life","Term",
         minimum_age=18, maximum_age=65, minimum_sum_insured=2500000, maximum_sum_insured=100000000,
         minimum_premium=5000, maximum_premium=50000, tax_benefit="Yes",
         accidental_death_benefit="Yes"),
    _ins("INS002","HDFCLSAVE","HDFC Life Sanchay Plus","HDFC Life","Life","Endowment",
         minimum_age=30, maximum_age=60, minimum_sum_insured=500000, maximum_sum_insured=10000000,
         minimum_premium=30000, maximum_premium=500000, tax_benefit="Yes"),
    _ins("INS003","HDFCERGOIND","HDFC ERGO Optima Secure","HDFC ERGO","Health","Individual",
         minimum_age=18, maximum_age=65, minimum_sum_insured=500000, maximum_sum_insured=20000000,
         minimum_premium=6000, maximum_premium=40000, cashless_claim_available="Yes",
         network_hospitals=10000, waiting_period_days=30, critical_illness_benefit="Yes"),
    _ins("INS004","HDFCERGOFAM","HDFC ERGO Optima Family Floater","HDFC ERGO","Health","Family Floater",
         minimum_age=18, maximum_age=65, minimum_sum_insured=500000, maximum_sum_insured=20000000,
         minimum_premium=10000, maximum_premium=60000, cashless_claim_available="Yes",
         network_hospitals=10000, maternity_benefit="Yes"),
    _ins("INS005","HDFCERGOSENIOR","HDFC ERGO Optima Senior","HDFC ERGO","Health","Senior Citizen",
         minimum_age=60, maximum_age=80, minimum_sum_insured=200000, maximum_sum_insured=5000000,
         minimum_premium=12000, maximum_premium=80000, cashless_claim_available="Yes"),
    _ins("INS006","HDFCERGOTRAVEL","HDFC ERGO Travel Insurance","HDFC ERGO","Travel","Single Trip",
         minimum_age=18, maximum_age=70, minimum_sum_insured=500000, maximum_sum_insured=50000000,
         minimum_premium=500, maximum_premium=10000, tax_benefit="No"),
    _ins("INS007","HDFCERGOMOTOR","HDFC ERGO Motor Insurance","HDFC ERGO","Motor","Comprehensive",
         minimum_age=18, maximum_age=75, minimum_sum_insured=100000, maximum_sum_insured=5000000,
         minimum_premium=3000, maximum_premium=30000, cashless_claim_available="Yes"),
    _ins("INS008","HDFCERGOPA","HDFC ERGO Personal Accident","HDFC ERGO","Personal Accident","Individual PA",
         minimum_age=18, maximum_age=65, minimum_sum_insured=500000, maximum_sum_insured=10000000,
         minimum_premium=1500, maximum_premium=15000, accidental_death_benefit="Yes"),
    _ins("INS009","HDFCERGOHOME","HDFC ERGO Home Insurance","HDFC ERGO","Home","Structure + Content",
         minimum_age=18, maximum_age=75, minimum_sum_insured=500000, maximum_sum_insured=100000000,
         minimum_premium=2000, maximum_premium=20000),
    _ins("INS010","HDFCLULIP","HDFC Life Click 2 Wealth ULIP","HDFC Life","ULIP","Market Linked",
         minimum_age=18, maximum_age=60, minimum_sum_insured=500000, maximum_sum_insured=50000000,
         minimum_premium=24000, maximum_premium=500000, tax_benefit="Yes"),
    _ins("INS011","HDFCLCHILD","HDFC Life Young Star Child Plan","HDFC Life","Child Insurance","Endowment",
         minimum_age=18, maximum_age=50, minimum_sum_insured=500000, maximum_sum_insured=50000000,
         minimum_premium=20000, maximum_premium=200000, tax_benefit="Yes"),
    _ins("INS012","HDFCLRETIRE","HDFC Life Pension Super Plus","HDFC Life","Retirement","Annuity",
         minimum_age=40, maximum_age=70, minimum_sum_insured=500000, maximum_sum_insured=50000000,
         minimum_premium=25000, maximum_premium=500000, tax_benefit="Yes"),
]

write_csv(OUTPUT_DIR / "insurance.csv", INSURANCE_PRODUCTS, "Insurance Products")
# Also write as insurance_products.csv for AI engine compatibility
write_csv(OUTPUT_DIR / "insurance_products.csv", INSURANCE_PRODUCTS, "Insurance Products (alias)")


# -- 1E: Debit Card Products -----------------------------------

DEBIT_CARD_PRODUCTS = [
    {"debit_card_product_id":"DB001","product_code":"HDFCMILL_DB","card_name":"Millennia Debit Card","card_variant":"Millennia","card_category":"Premium","card_type":"Personal","card_network":"Visa","product_status":"Active","minimum_age":18,"maximum_age":70,"minimum_balance_required":10000,"atm_daily_limit":25000,"pos_daily_limit":100000,"online_daily_limit":100000,"international_transaction":"Yes","annual_fee":750,"created_at":NOW_TS,"updated_at":NOW_TS},
    {"debit_card_product_id":"DB002","product_code":"HDFCPLAT_DB","card_name":"Platinum Debit Card","card_variant":"Platinum","card_category":"Premium","card_type":"Personal","card_network":"Visa","product_status":"Active","minimum_age":18,"maximum_age":70,"minimum_balance_required":5000,"atm_daily_limit":25000,"pos_daily_limit":75000,"online_daily_limit":75000,"international_transaction":"Yes","annual_fee":500,"created_at":NOW_TS,"updated_at":NOW_TS},
    {"debit_card_product_id":"DB003","product_code":"HDFCCLASS_DB","card_name":"Classic Debit Card","card_variant":"Classic","card_category":"Classic","card_type":"Personal","card_network":"Visa","product_status":"Active","minimum_age":18,"maximum_age":70,"minimum_balance_required":0,"atm_daily_limit":10000,"pos_daily_limit":25000,"online_daily_limit":25000,"international_transaction":"No","annual_fee":150,"created_at":NOW_TS,"updated_at":NOW_TS},
    {"debit_card_product_id":"DB004","product_code":"HDFCRUPAY_DB","card_name":"RuPay Debit Card","card_variant":"Classic","card_category":"Classic","card_type":"Personal","card_network":"RuPay","product_status":"Active","minimum_age":18,"maximum_age":70,"minimum_balance_required":0,"atm_daily_limit":10000,"pos_daily_limit":20000,"online_daily_limit":20000,"international_transaction":"No","annual_fee":0,"created_at":NOW_TS,"updated_at":NOW_TS},
    {"debit_card_product_id":"DB005","product_code":"HDFCMB_DB","card_name":"MoneyBack Debit Card","card_variant":"MoneyBack","card_category":"Classic","card_type":"Personal","card_network":"Visa","product_status":"Active","minimum_age":18,"maximum_age":70,"minimum_balance_required":1000,"atm_daily_limit":10000,"pos_daily_limit":25000,"online_daily_limit":25000,"international_transaction":"No","annual_fee":250,"created_at":NOW_TS,"updated_at":NOW_TS},
    {"debit_card_product_id":"DB006","product_code":"HDFCWOMEN_DB","card_name":"Women's Advantage Debit Card","card_variant":"Women","card_category":"Premium","card_type":"Personal","card_network":"Visa","product_status":"Active","minimum_age":18,"maximum_age":70,"minimum_balance_required":5000,"atm_daily_limit":25000,"pos_daily_limit":75000,"online_daily_limit":75000,"international_transaction":"Yes","annual_fee":500,"created_at":NOW_TS,"updated_at":NOW_TS},
    {"debit_card_product_id":"DB007","product_code":"HDFCBIZ_DB","card_name":"Business Debit Card","card_variant":"Business","card_category":"Business","card_type":"Business","card_network":"Visa","product_status":"Active","minimum_age":18,"maximum_age":70,"minimum_balance_required":25000,"atm_daily_limit":50000,"pos_daily_limit":200000,"online_daily_limit":200000,"international_transaction":"Yes","annual_fee":1000,"created_at":NOW_TS,"updated_at":NOW_TS},
    {"debit_card_product_id":"DB008","product_code":"HDFCTITAN_DB","card_name":"Titanium Debit Card","card_variant":"Titanium","card_category":"Classic","card_type":"Personal","card_network":"Mastercard","product_status":"Active","minimum_age":18,"maximum_age":70,"minimum_balance_required":2500,"atm_daily_limit":15000,"pos_daily_limit":40000,"online_daily_limit":40000,"international_transaction":"No","annual_fee":200,"created_at":NOW_TS,"updated_at":NOW_TS},
]

write_csv(OUTPUT_DIR / "debit_card_products.csv", DEBIT_CARD_PRODUCTS, "Debit Card Products")

print("  [OK] Phase 1 complete\n")


# ═══════════════════════════════════════════════════════════════
# SECTION 2 — MERCHANT MASTER
# ═══════════════════════════════════════════════════════════════

print("PHASE 2 — Building merchant master...")

MERCHANT_MASTER_RAW = [
    ("MER0001","IndiGo","Airlines","4511"),("MER0002","Air India","Airlines","4511"),
    ("MER0003","Air India Express","Airlines","4511"),("MER0004","Vistara","Airlines","4511"),
    ("MER0005","Akasa Air","Airlines","4511"),("MER0006","SpiceJet","Airlines","4511"),
    ("MER0007","Emirates","Airlines","4511"),("MER0008","Qatar Airways","Airlines","4511"),
    ("MER0101","Swiggy","Food Delivery","5812"),("MER0102","Zomato","Food Delivery","5812"),
    ("MER0103","EatSure","Food Delivery","5812"),("MER0104","Dominos","Food Delivery","5812"),
    ("MER0105","McDonalds","Food Delivery","5812"),("MER0106","KFC","Food Delivery","5812"),
    ("MER0201","Amazon India","E-Commerce","5311"),("MER0202","Flipkart","E-Commerce","5311"),
    ("MER0203","Myntra","E-Commerce","5311"),("MER0204","Ajio","E-Commerce","5311"),
    ("MER0205","Meesho","E-Commerce","5311"),("MER0206","Nykaa","E-Commerce","5311"),
    ("MER0207","Croma","Electronics","5732"),("MER0208","Reliance Digital","Electronics","5732"),
    ("MER0301","Reliance Trends","Shopping","5311"),("MER0302","Westside","Shopping","5311"),
    ("MER0303","Lifestyle","Shopping","5311"),("MER0304","Pantaloons","Shopping","5311"),
    ("MER0401","DMart","Grocery","5411"),("MER0402","Reliance Smart","Grocery","5411"),
    ("MER0403","BigBasket","Grocery","5411"),("MER0404","Blinkit","Grocery","5411"),
    ("MER0405","Zepto","Grocery","5411"),
    ("MER0501","Uber","Cab","4121"),("MER0502","Ola","Cab","4121"),
    ("MER0503","Rapido","Cab","4121"),("MER0504","BluSmart","Cab","4121"),
    ("MER0601","RedBus","Bus","4789"),("MER0602","AbhiBus","Bus","4789"),
    ("MER0603","MSRTC","Bus","4131"),("MER0604","KSRTC","Bus","4131"),
    ("MER0701","IRCTC","Train","4112"),("MER0702","Indian Railways","Train","4112"),
    ("MER0801","Taj Hotels","Hotels","7011"),("MER0802","Marriott","Hotels","7011"),
    ("MER0803","ITC Hotels","Hotels","7011"),("MER0804","OYO","Hotels","7011"),
    ("MER0805","MakeMyTrip","Hotels","4722"),("MER0806","Booking.com","Hotels","4722"),
    ("MER0901","PVR INOX","Movies","7832"),("MER0902","Cinepolis","Movies","7832"),
    ("MER0903","BookMyShow","Entertainment","7832"),
    ("MER1001","Indian Oil","Fuel","5541"),("MER1002","Bharat Petroleum","Fuel","5541"),
    ("MER1003","Hindustan Petroleum","Fuel","5541"),("MER1004","Shell","Fuel","5541"),
    ("MER1101","MSEDCL","Utilities","4900"),("MER1102","Adani Electricity","Utilities","4900"),
    ("MER1103","Tata Power","Utilities","4900"),("MER1104","Airtel","Telecom","4814"),
    ("MER1105","Jio","Telecom","4814"),("MER1106","Vi","Telecom","4814"),
    ("MER1201","Netflix","Entertainment","4899"),("MER1202","Spotify","Entertainment","4899"),
    ("MER1203","Amazon Prime","Entertainment","4899"),("MER1204","Disney+ Hotstar","Entertainment","4899"),
    ("MER1205","YouTube Premium","Entertainment","4899"),
    ("MER1301","Apollo Hospitals","Healthcare","8011"),("MER1302","Fortis Healthcare","Healthcare","8011"),
    ("MER1303","Max Healthcare","Healthcare","8011"),("MER1304","Apollo Pharmacy","Pharmacy","5912"),
    ("MER1305","Tata 1mg","Pharmacy","5912"),("MER1306","PharmEasy","Pharmacy","5912"),
    ("MER1401","Coursera","Education","8299"),("MER1402","Udemy","Education","8299"),
    ("MER1403","Unacademy","Education","8299"),("MER1404","BYJU'S","Education","8299"),
    ("MER1501","Zerodha","Investment","6211"),("MER1502","Groww","Investment","6211"),
    ("MER1503","Upstox","Investment","6211"),("MER1504","Angel One","Investment","6211"),
    ("MER1505","HDFC Securities","Investment","6211"),
    ("MER1601","HDFC Mutual Fund","SIP / Mutual Fund","6211"),
    ("MER1602","SBI Mutual Fund","SIP / Mutual Fund","6211"),
    ("MER1603","ICICI Prudential MF","SIP / Mutual Fund","6211"),
    ("MER1701","HDFC Life","Insurance","6300"),("MER1702","HDFC ERGO","Insurance","6300"),
    ("MER1703","ICICI Lombard","Insurance","6300"),
    ("MER1801","Electricity Bill","Bills","4900"),("MER1802","Water Bill","Bills","4900"),
    ("MER1803","Gas Bill","Bills","4900"),("MER1804","Mobile Recharge","Bills","4814"),
    ("MER1805","Credit Card Bill","Bills","6012"),
    ("MER1901","Social","Restaurant","5812"),("MER1902","Barbeque Nation","Restaurant","5812"),
    ("MER1903","Theobroma","Restaurant","5812"),("MER1904","Cafe Coffee Day","Restaurant","5814"),
    ("MER2001","University Fee Portal","Education Fees","8220"),
    ("MER2002","College Fee Payment","Education Fees","8220"),
    ("MER2003","School Fee Payment","Education Fees","8211"),
    ("MER2101","Rent Payment","Rent","6513"),("MER2102","Housing Rent","Rent","6513"),
    ("MER2201","UPI Transfer - Family","P2P Transfer",""),
    ("MER2202","UPI Transfer - Friends","P2P Transfer",""),
    ("MER2203","UPI Transfer - Business","P2P Transfer",""),
    # Agriculture-specific merchants
    ("MERAGR01","Krishi Seva Kendra","Agriculture","5261"),
    ("MERAGR02","Mahindra Farm Equipment","Agriculture Equipment","5999"),
    ("MERAGR03","IFFCO Fertilizers","Agriculture","5261"),
    ("MERAGR04","State Agricultural Market","Agriculture","5261"),
    ("MERAGR05","Tractor Junction","Agriculture Equipment","5511"),
    ("MERAGR06","Bijak Agri","Agriculture","5261"),
]

MERCHANT_ROWS = [
    {"merchant_id":m[0],"merchant_name":m[1],"merchant_category":m[2],"mcc_code":m[3],"created_at":NOW_TS}
    for m in MERCHANT_MASTER_RAW
]
MERCHANTS_BY_ID = {m["merchant_id"]: m for m in MERCHANT_ROWS}
write_csv(OUTPUT_DIR / "merchants.csv", MERCHANT_ROWS, "Merchants")
print("  [OK] Phase 2 complete\n")


# ═══════════════════════════════════════════════════════════════
# SECTION 3 — CUSTOMER PROFILE GENERATION (1000 customers)
# ═══════════════════════════════════════════════════════════════

print("PHASE 3 — Generating 1000 diverse customers...")

FIRST_NAMES_MALE = [
    "Aarav","Aaryan","Abhay","Abhinav","Abhishek","Adarsh","Aditya","Advaith","Agastya",
    "Ajay","Akash","Akshay","Alok","Aman","Amar","Amit","Anand","Aniket","Anil","Anirudh",
    "Ankit","Anmol","Ansh","Anshul","Arjun","Armaan","Arnav","Arun","Aryan","Ashish","Ashok",
    "Atharv","Avinash","Ayush","Bharat","Bhavesh","Chaitanya","Chetan","Chirag","Daksh",
    "Darshan","Deepak","Dev","Dhruv","Dinesh","Divyansh","Eshan","Gaurav","Girish","Harish",
    "Harsh","Harshad","Himanshu","Hrithik","Ishaan","Jai","Jay","Jayesh","Karan","Kartik",
    "Keshav","Krishna","Kunal","Lakshya","Manav","Manish","Mayank","Mihir","Mohit","Nakul",
    "Naman","Naveen","Neel","Nikhil","Nirav","Nitin","Om","Parth","Pranav","Pratik","Rahul",
    "Raj","Rajat","Rajesh","Rajiv","Rakesh","Rohan","Rohit","Sachin","Sagar","Sahil","Sameer",
    "Sanjay","Sanket","Sarthak","Shashank","Shivam","Shrey","Siddharth","Soham","Sourabh",
    "Srinivas","Sumit","Suraj","Tanay","Tanish","Tarun","Tejas","Uday","Utkarsh","Vaibhav",
    "Varun","Ved","Veer","Vijay","Vikas","Vikram","Vinay","Vishal","Vivek","Yash","Yuvraj",
    "Balram","Gopal","Harendra","Kamlesh","Ramesh","Suresh","Santosh","Vijayendra","Yogesh",
]

FIRST_NAMES_FEMALE = [
    "Aadhya","Aakanksha","Aaliya","Aaradhya","Aastha","Aditi","Akanksha","Alisha","Amrita",
    "Ananya","Anika","Anjali","Ankita","Anushka","Anvi","Aparna","Aradhana","Avani","Avantika",
    "Bhavana","Bhumika","Charita","Charvi","Deepa","Deepika","Deepti","Diya","Esha","Garima",
    "Gauri","Gayatri","Geetanjali","Harini","Ira","Isha","Ishita","Jahnavi","Janhvi","Jiya",
    "Kajal","Kalpana","Kanchan","Kavita","Kavya","Khushi","Kirti","Komal","Krisha","Lakshmi",
    "Lavanya","Madhuri","Mahima","Mahi","Manisha","Meera","Megha","Mihika","Mitali","Manya",
    "Muskan","Naina","Namrata","Neha","Nidhi","Nikita","Nisha","Palak","Pallavi","Pooja",
    "Prachi","Pragya","Pranita","Priya","Radhika","Ragini","Rashi","Rashmi","Reema","Rekha",
    "Rhea","Riddhi","Riya","Roshni","Sakshi","Saloni","Sana","Sandhya","Sanjana","Sapna",
    "Sarika","Shalini","Shanaya","Sharanya","Shreya","Shruti","Simran","Sneha","Sonali","Sonia",
    "Suhani","Swati","Tanisha","Tanya","Trisha","Vaishnavi","Vandana","Varsha","Vidhi","Vineeta",
    "Yamini","Zoya","Kamla","Savita","Sunita","Lalita","Geeta","Shanti","Rekha",
]

LAST_NAMES = [
    "Agarwal","Ahire","Bansal","Bhat","Bhatia","Bhosale","Bhatt","Chakraborty","Chaudhary",
    "Chavan","Chopra","Das","Desai","Deshmukh","Dhawan","Dixit","Dubey","Gandhi","Garg","Ghosh",
    "Goel","Gokhale","Goswami","Gupta","Iyer","Jadhav","Jain","Joshi","Kale","Kapoor","Karnik",
    "Kaur","Kulkarni","Kumar","Mahajan","Malhotra","Mane","Mehta","Menon","Mishra","Modi",
    "More","Naik","Nair","Narayan","Nayak","Patel","Patil","Pawar","Pillai","Pradhan","Rao",
    "Rane","Rathod","Roy","Saha","Saini","Salunke","Sarkar","Shah","Sharma","Shetty","Shinde",
    "Singh","Sinha","Solanki","Soman","Sonawane","Srivastava","Subramanian","Suresh","Tiwari",
    "Trivedi","Tripathi","Upadhyay","Vaidya","Varma","Verma","Wagh","Yadav","Yadav","Reddy",
]

CITIES = [
    ("Mumbai","Maharashtra","400001"),("Pune","Maharashtra","411001"),
    ("Nagpur","Maharashtra","440001"),("Nashik","Maharashtra","422001"),
    ("Thane","Maharashtra","400601"),("Navi Mumbai","Maharashtra","400703"),
    ("Delhi","Delhi","110001"),("New Delhi","Delhi","110011"),
    ("Noida","Uttar Pradesh","201301"),("Gurgaon","Haryana","122001"),
    ("Bengaluru","Karnataka","560001"),("Mysuru","Karnataka","570001"),
    ("Mangaluru","Karnataka","575001"),("Hyderabad","Telangana","500001"),
    ("Chennai","Tamil Nadu","600001"),("Coimbatore","Tamil Nadu","641001"),
    ("Madurai","Tamil Nadu","625001"),("Ahmedabad","Gujarat","380001"),
    ("Surat","Gujarat","395001"),("Vadodara","Gujarat","390001"),
    ("Rajkot","Gujarat","360001"),("Kolkata","West Bengal","700001"),
    ("Jaipur","Rajasthan","302001"),("Lucknow","Uttar Pradesh","226001"),
    ("Kanpur","Uttar Pradesh","208001"),("Bhopal","Madhya Pradesh","462001"),
    ("Indore","Madhya Pradesh","452001"),("Bhubaneswar","Odisha","751001"),
    ("Chandigarh","Chandigarh","160001"),("Kochi","Kerala","682001"),
    ("Thiruvananthapuram","Kerala","695001"),("Patna","Bihar","800001"),
    ("Ranchi","Jharkhand","834001"),("Guwahati","Assam","781001"),
    ("Dehradun","Uttarakhand","248001"),("Amritsar","Punjab","143001"),
    ("Visakhapatnam","Andhra Pradesh","530001"),("Vijayawada","Andhra Pradesh","520001"),
    # Smaller/rural cities for farmers, traders, rural customers
    ("Kolhapur","Maharashtra","416001"),("Solapur","Maharashtra","413001"),
    ("Sangli","Maharashtra","416416"),("Akola","Maharashtra","444001"),
    ("Nanded","Maharashtra","431601"),("Latur","Maharashtra","413512"),
    ("Osmanabad","Maharashtra","413501"),("Wardha","Maharashtra","442001"),
    ("Yavatmal","Maharashtra","445001"),("Amravati","Maharashtra","444601"),
]

# Occupation tuples: (occupation_label, employment_type, income_tier_key)
# income_tier_key maps to an income range selection function
OCCUPATION_TEMPLATES = [
    # Software / IT
    ("Software Engineer","Salaried","it_junior"),
    ("Senior Software Engineer","Salaried","it_mid"),
    ("Data Scientist","Salaried","it_mid"),
    ("Data Analyst","Salaried","it_junior"),
    ("Cloud Engineer","Salaried","it_mid"),
    ("DevOps Engineer","Salaried","it_mid"),
    ("Product Manager","Salaried","it_senior"),
    ("IT Manager","Salaried","it_senior"),
    # Professional
    ("Chartered Accountant","Self-employed","professional"),
    ("Doctor","Salaried","doctor"),
    ("Doctor","Self-employed","doctor"),
    ("Dentist","Self-employed","dentist"),
    ("Pharmacist","Salaried","pharmacist"),
    ("Lawyer","Self-employed","lawyer"),
    ("Architect","Self-employed","architect"),
    ("Consultant","Self-employed","consultant"),
    ("Researcher","Salaried","researcher"),
    # Finance / Bank
    ("Chartered Accountant","Self-employed","professional"),
    ("Finance Manager","Salaried","finance_mgr"),
    ("Bank Employee","Salaried","bank_emp"),
    ("Insurance Officer","Salaried","insurance_emp"),
    ("Investment Advisor","Self-employed","professional"),
    # Education
    ("Teacher","Salaried","teacher"),
    ("Professor","Salaried","professor"),
    ("School Teacher","Salaried","teacher"),
    # Engineering
    ("Civil Engineer","Salaried","engineer"),
    ("Mechanical Engineer","Salaried","engineer"),
    ("Electrical Engineer","Salaried","engineer"),
    # Government / Defence
    ("Government Employee","Salaried","govt_employee"),
    ("Defence Personnel","Salaried","defence"),
    ("Police Officer","Salaried","govt_employee"),
    # Business
    ("Business Owner","Business","business_small"),
    ("Retail Business Owner","Business","business_small"),
    ("Restaurant Owner","Business","business_small"),
    ("Shop Owner","Business","business_small"),
    ("Trader","Self-employed","trader"),
    ("Entrepreneur","Business","business_mid"),
    ("Manufacturer","Business","business_mid"),
    ("Exporter","Business","business_large"),
    ("Importer","Business","business_mid"),
    ("Transport Business Owner","Business","business_mid"),
    ("Construction Business Owner","Business","business_large"),
    ("Medium Business Owner","Business","business_large"),
    # Freelance / Digital
    ("Freelancer","Self-employed","freelancer"),
    ("Content Creator","Self-employed","freelancer"),
    ("Graphic Designer","Self-employed","freelancer"),
    # Agriculture
    ("Farmer","Farmer","farmer"),
    ("Agricultural Worker","Farmer","agri_worker"),
    ("Dairy Farmer","Farmer","farmer"),
    ("Horticulture Farmer","Farmer","farmer"),
    # Others
    ("Retired Professional","Retired","retired"),
    ("Pensioner","Retired","pensioner"),
    ("Homemaker","Homemaker","homemaker"),
    ("Student","Student","student"),
    ("Accountant","Salaried","accountant"),
    ("HR Manager","Salaried","hr_mgr"),
    ("Marketing Manager","Salaried","marketing_mgr"),
]

# Occupation weight — more common occupations get higher weight
OCCUPATION_WEIGHTS = [
    20,15,10,8,8,8,8,6,
    12,10,8,6,5,6,6,8,6,
    8,7,8,6,6,
    15,8,10,
    10,10,8,
    15,10,5,
    12,10,8,8,10,8,6,5,5,6,5,
    8,6,5,
    20,8,8,5,
    10,8,6,8,8,6,6,5,
]

def generate_income(tier: str, age: int) -> int:
    tiers = {
        "student":       (0,       50_000),
        "homemaker":     (0,       120_000),
        "agri_worker":   (60_000,  200_000),
        "farmer":        (80_000,  600_000),
        "pensioner":     (100_000, 500_000),
        "retired":       (200_000, 1_500_000),
        "teacher":       (200_000, 800_000),
        "accountant":    (300_000, 1_000_000),
        "pharmacist":    (300_000, 1_000_000),
        "bank_emp":      (300_000, 1_200_000),
        "insurance_emp": (300_000, 900_000),
        "hr_mgr":        (400_000, 1_500_000),
        "marketing_mgr": (400_000, 1_500_000),
        "engineer":      (400_000, 1_800_000),
        "govt_employee": (250_000, 1_200_000),
        "defence":       (250_000, 1_000_000),
        "researcher":    (400_000, 1_500_000),
        "it_junior":     (400_000, 1_500_000),
        "freelancer":    (200_000, 2_000_000),
        "trader":        (300_000, 3_000_000),
        "it_mid":        (800_000, 3_000_000),
        "professor":     (600_000, 2_000_000),
        "finance_mgr":   (700_000, 2_500_000),
        "it_senior":     (1_500_000, 5_000_000),
        "professional":  (800_000, 5_000_000),
        "dentist":       (600_000, 3_000_000),
        "doctor":        (800_000, 6_000_000),
        "architect":     (600_000, 3_000_000),
        "lawyer":        (600_000, 5_000_000),
        "consultant":    (600_000, 4_000_000),
        "business_small":(400_000, 3_000_000),
        "business_mid":  (1_000_000, 8_000_000),
        "business_large":(3_000_000, 20_000_000),
    }
    lo, hi = tiers.get(tier, (300_000, 1_200_000))
    # Age adjustment for non-student/non-farmer
    if tier not in ("student","homemaker","farmer","agri_worker","pensioner","retired"):
        if age < 25:
            hi = min(hi, 700_000)
        elif age < 30:
            hi = min(hi, hi * 0.6)
        elif age >= 50:
            lo = max(lo, lo * 1.2)
    return random.randint(int(lo), int(max(lo, hi)))

def income_range_label(income: int) -> str:
    if income < 250_000: return "0-2.5L"
    if income < 500_000: return "2.5-5L"
    if income < 1_000_000: return "5-10L"
    if income < 2_000_000: return "10-20L"
    if income < 5_000_000: return "20-50L"
    if income < 10_000_000: return "50L-1Cr"
    return "1Cr+"

EMPLOYERS = [
    "TCS","Infosys","Wipro","HCLTech","Accenture","IBM India","Cognizant","Capgemini",
    "Tech Mahindra","Deloitte","EY India","KPMG India","PwC India","Amazon India",
    "Microsoft India","Google India","Flipkart","Reliance Industries","Tata Motors",
    "Mahindra & Mahindra","Bajaj Finserv","ICICI Bank","Axis Bank","HDFC Bank",
    "Larsen & Toubro","Aditya Birla Group","State Government","Central Government",
    "Municipal Corporation","DRDO","ISRO","Indian Railways","State Bank of India",
    "Self Employed","Independent Consultant","Family Business","Startup","Private Company",
]

EDUCATION_LEVELS = ["Higher Secondary","Diploma","Graduate","Postgraduate","Doctorate"]
EDUCATION_BY_OCC = {
    "Doctor":"Postgraduate","Dentist":"Postgraduate","Lawyer":"Postgraduate",
    "Chartered Accountant":"Postgraduate","Professor":"Postgraduate","Researcher":"Doctorate",
    "Software Engineer":"Graduate","Senior Software Engineer":"Graduate",
    "Data Scientist":"Postgraduate","Student":"Higher Secondary",
    "Farmer":"Higher Secondary","Agricultural Worker":"Higher Secondary",
    "Dairy Farmer":"Higher Secondary","Homemaker":"Higher Secondary",
}

LANGUAGES = ["English","Hindi","Marathi","Gujarati","Tamil","Telugu","Kannada","Bengali",
             "Malayalam","Punjabi","Odia"]

def choose_segment(age, income, emp_type):
    if emp_type == "Business":
        return wchoice([("Business",70),("Premium",25 if income>=2000000 else 5),("Retail",5)])
    if income >= 5_000_000:
        return wchoice([("Premium",85),("Retail",15)])
    if income >= 2_500_000:
        return wchoice([("Premium",75),("Retail",20),("Business",5)])
    if income >= 1_200_000:
        return wchoice([("Premium",35),("Retail",65)])
    return wchoice([("Retail",93),("Premium",7)])

def generate_customer(i: int) -> Dict:
    gender = random.choice(["Male","Female"])
    first_name = random.choice(FIRST_NAMES_MALE if gender=="Male" else FIRST_NAMES_FEMALE)
    last_name  = random.choice(LAST_NAMES)

    occ, emp_type, income_tier = random.choices(
        OCCUPATION_TEMPLATES, weights=OCCUPATION_WEIGHTS, k=1)[0]

    # Age range by occupation
    if occ == "Student": age = random.randint(18, 25)
    elif occ in ("Farmer","Agricultural Worker","Dairy Farmer","Horticulture Farmer"):
        age = random.randint(22, 65)
    elif occ in ("Retired Professional","Pensioner"): age = random.randint(55, 75)
    elif occ in ("Homemaker",): age = random.randint(25, 60)
    elif occ in ("Doctor","Dentist","Lawyer","Chartered Accountant"): age = random.randint(28, 65)
    elif occ in ("Professor",): age = random.randint(35, 65)
    elif "Senior" in occ or "Manager" in occ: age = random.randint(28, 55)
    else: age = random.randint(22, 58)

    annual_income = generate_income(income_tier, age)

    residential_status = wchoice([("Resident",99),("NRI",1)])
    if residential_status == "NRI":
        annual_income = max(annual_income, 2_000_000)

    city, state, pincode = random.choice(CITIES)

    if age < 25:
        marital = wchoice([("Single",88),("Married",12)])
    elif age < 35:
        marital = wchoice([("Single",38),("Married",62)])
    else:
        marital = wchoice([("Married",80),("Divorced",9),("Widowed",11)])

    # Employer
    if emp_type == "Student":     employer = "College / University"
    elif emp_type == "Retired":   employer = "Retired"
    elif emp_type == "Homemaker": employer = "Not Applicable"
    elif emp_type == "Farmer":    employer = "Self / Family Farm"
    elif emp_type == "Business":  employer = wchoice([("Family Business",30),("Independent Business",30),("Startup",20),("Private Company",20)])
    elif emp_type == "Self-employed": employer = "Self Employed"
    else: employer = random.choice(EMPLOYERS)

    customer_since = rdate(date(2015,1,1), date(2025,12,1))

    # Credit score: income & stability driven
    if emp_type == "Student":        cs = random.randint(600, 730)
    elif emp_type in ("Farmer","Homemaker","Agricultural Worker"): cs = random.randint(620, 760)
    elif annual_income >= 3_000_000: cs = random.randint(740, 850)
    elif annual_income >= 1_000_000: cs = random.randint(700, 820)
    elif annual_income >= 500_000:   cs = random.randint(680, 800)
    else:                             cs = random.randint(640, 760)

    if residential_status == "NRI": cs = max(cs, 720)

    seg = choose_segment(age, annual_income, emp_type)

    risk_profile = wchoice([("Low",25),("Moderate",55),("High",20)])
    if annual_income < 500_000:
        risk_profile = wchoice([("Low",50),("Moderate",40),("High",10)])
    if annual_income > 3_000_000:
        risk_profile = wchoice([("Low",20),("Moderate",45),("High",35)])

    if emp_type == "Student":
        pref_channel = wchoice([("Mobile App",70),("NetBanking",15),("Email",10),("SMS",5)])
    elif age >= 55:
        pref_channel = wchoice([("Branch",30),("Mobile App",30),("NetBanking",20),("SMS",10),("Email",10)])
    else:
        pref_channel = wchoice([("Mobile App",45),("NetBanking",20),("Email",15),("SMS",10),("Branch",10)])

    education = EDUCATION_BY_OCC.get(occ, random.choices(
        EDUCATION_LEVELS, weights=[5,10,35,35,15])[0])

    return {
        "customer_id":             f"CUST{i:05d}",
        "customer_number":         f"CIF{i:08d}",
        "first_name":              first_name,
        "middle_name":             "",
        "last_name":               last_name,
        "date_of_birth":           date(TODAY.year-age, random.randint(1,12), random.randint(1,28)).isoformat(),
        "age":                     age,
        "gender":                  gender,
        "marital_status":          marital,
        "nationality":             "Indian",
        "residential_status":      residential_status,
        "occupation_type":         emp_type,
        "occupation":              occ,
        "employer_name":           employer,
        "employment_type":         emp_type,
        "annual_income":           annual_income,
        "income_range":            income_range_label(annual_income),
        "education_level":         education,
        "address_line_1":          f"{random.randint(1,999)} {random.choice(['MG Road','Station Road','Main Street','Park Road','Market Road','Gandhi Nagar','Nehru Colony'])}",
        "address_line_2":          f"{'Flat' if random.random()<0.6 else 'Plot'} {random.randint(1,500)}",
        "city":                    city,
        "state":                   state,
        "country":                 "India",
        "pincode":                 pincode,
        "mobile_number":           f"9{i:09d}"[-10:],
        "email":                   f"{first_name.lower()}.{last_name.lower()}{i}@example.com",
        "customer_since":          customer_since.isoformat(),
        "customer_segment_type":   seg,
        "customer_status":         wchoice([("Active",96),("Dormant",4)]),
        "kyc_status":              wchoice([("Verified",97),("Pending",3)]),
        "kyc_last_updated":        rdate(date(2024,1,1), TODAY).isoformat(),
        "risk_profile":            risk_profile,
        "credit_score":            cs,
        "branch_id":               f"BR{random.randint(1,80):03d}",
        "relationship_manager_id": f"RM{random.randint(1,60):03d}",
        "preferred_language":      random.choice(LANGUAGES),
        "preferred_channel":       pref_channel,
        "marketing_consent":       wchoice([("Yes",92),("No",8)]),
    }

CUSTOMERS = [generate_customer(i) for i in range(1, NUM_CUSTOMERS+1)]
write_csv(OUTPUT_DIR / "customers.csv", CUSTOMERS, "Customers")

# Fast lookup
CUST_BY_ID = {c["customer_id"]: c for c in CUSTOMERS}
print("  [OK] Phase 3 complete\n")


# ═══════════════════════════════════════════════════════════════
# SECTION 4 — PRODUCT OWNERSHIP (ELIGIBILITY-DRIVEN)
# ═══════════════════════════════════════════════════════════════

print("PHASE 4 — Assigning products with eligibility logic...")

ALL_ACCOUNTS    = []
ALL_DEBIT_CARDS = []
ALL_CREDIT_CARDS = []
ALL_LOANS       = []
ALL_DEPOSITS    = []
ALL_INVESTMENTS = []
ALL_INSURANCE   = []

# Indices for ID generation
acc_idx  = [1]
dbc_idx  = [1]
cca_idx  = [1]
loan_idx = [1]
dep_idx  = [1]
inv_idx  = [1]
ins_idx  = [1]

# Per-customer primary account map (for transactions)
CUST_PRIMARY_ACCOUNT = {}  # customer_id -> account_id
CUST_CARDS = {}            # customer_id -> list of credit card IDs
CUST_LOAN_EMIS = {}        # customer_id -> monthly EMI sum
CUST_SIP_AMT = {}          # customer_id -> monthly SIP sum
CUST_HAS_INS = {}          # customer_id -> bool
CUST_HAS_INVEST = {}       # customer_id -> bool
CUST_DEBIT_CARDS = {}      # customer_id -> list of debit card IDs
CUST_LOAN_CATS = {}        # customer_id -> list of loan categories
CUST_HAS_DEMAT = {}        # customer_id -> bool
CUST_INV_CATS = {}         # customer_id -> list of investment categories
CUST_INS_CATS = {}         # customer_id -> list of insurance types


def eligible_credit_cards(cust: Dict) -> List[Dict]:
    income  = cust["annual_income"]
    monthly = income / 12
    age     = cust["age"]
    cs      = cust["credit_score"]
    emp     = cust["employment_type"]
    res     = cust["residential_status"]

    result = []
    for card in CREDIT_CARD_PRODUCTS:
        if card["product_status"] != "Active":
            continue
        if age < card["minimum_age"] or age > card["maximum_age"]:
            continue
        if income < card["minimum_income_annual"]:
            continue
        if monthly < card["minimum_income_monthly"]:
            continue
        if cs < card["minimum_credit_score"]:
            continue
        if res == "NRI" and card["residential_requirement"] == "Resident Indian":
            continue
        # Business cards -> only business/self-employed
        if card["card_type"] == "Business" and emp not in ("Business","Self-employed"):
            continue
        # Defence card -> only defence
        if card["card_name"] == "Defence Credit Card" and emp != "Defence Personnel":
            continue
        result.append(card)
    return result


def pick_credit_card(cust: Dict, eligible: List[Dict]) -> Optional[Dict]:
    """Pick the most appropriate card from eligible set based on customer behaviour."""
    income  = cust["annual_income"]
    occ     = cust["occupation"]
    emp     = cust["employment_type"]

    if not eligible:
        return None

    # Filter by income tier
    super_premium = [c for c in eligible if c["card_category"] == "Super Premium"]
    premium       = [c for c in eligible if c["card_category"] == "Premium"]
    classic       = [c for c in eligible if c["card_category"] == "Classic"]
    business_cards = [c for c in eligible if c["card_type"] == "Business"]
    cobrand       = [c for c in eligible if c["co_brand"] == "Yes"]

    if emp == "Business" and business_cards:
        pool = wchoice([(business_cards,60),(cobrand if cobrand else premium,20),(premium,20)])
    elif income >= 2_000_000 and super_premium:
        pool = wchoice([(super_premium,60),(premium,30),(cobrand if cobrand else classic,10)])
    elif income >= 800_000 and premium:
        pool = wchoice([(premium,55),(cobrand if cobrand else classic,25),(classic,20)])
    elif income >= 400_000 and (classic or cobrand):
        pool = wchoice([(classic,50),(cobrand if cobrand else classic,30),(premium if premium else classic,20)])
    else:
        pool = classic if classic else eligible

    if not pool:
        pool = eligible
    return random.choice(pool)


def eligible_loans(cust: Dict) -> List[Dict]:
    income  = cust["annual_income"]
    monthly = income / 12
    age     = cust["age"]
    cs      = cust["credit_score"]
    emp     = cust["employment_type"]
    occ     = cust["occupation"]

    result = []
    for loan in LOAN_PRODUCTS:
        if loan["product_status"] != "Active":
            continue
        min_age = loan.get("minimum_age", 18)
        max_age = loan.get("maximum_age", 70)
        if age < min_age or age > max_age:
            continue
        if income < loan["minimum_income_annual"] and loan["minimum_income_annual"] > 0:
            # Special case: gold loan and education loan have 0 min income
            continue
        if cs < loan["minimum_credit_score"] and loan["minimum_credit_score"] > 0:
            continue
        # Agriculture loans -> only farmers
        if loan["loan_category"] == "Agriculture" and emp not in ("Farmer","Self-employed"):
            continue
        # Business loans -> only business/self-employed
        if loan["customer_type"] == "Business" and emp not in ("Business","Self-employed"):
            continue
        # Education loan -> students or young adults
        if loan["loan_category"] == "Education" and age > 35:
            continue
        result.append(loan)
    return result


for cust in CUSTOMERS:
    cid    = cust["customer_id"]
    income = cust["annual_income"]
    monthly_income = income / 12
    age    = cust["age"]
    emp    = cust["employment_type"]
    occ    = cust["occupation"]
    cs     = cust["credit_score"]
    seg    = cust["customer_segment_type"]
    since  = date.fromisoformat(cust["customer_since"])
    marital = cust["marital_status"]
    gender  = cust["gender"]

    # -- 4A: Accounts ------------------------------------------
    if emp == "Business":
        acc_type = wchoice([("Current",75),("Savings",25)])
    elif emp == "Salaried":
        acc_type = wchoice([("Salary",65),("Savings",35)])
    elif emp in ("Student","Homemaker"):
        acc_type = "Savings"
    elif emp == "Farmer":
        acc_type = wchoice([("Savings",80),("Current",20)])
    else:
        acc_type = wchoice([("Savings",70),("Current",30)])

    acc_product_map = {
        "Savings": ["Regular Savings Account","Savings Max","Digital Savings Account","Millennia Savings Account"],
        "Salary":  ["Salary Account","Premium Salary Account","Savings Account"],
        "Current": ["Regular Current Account","Business Current Account","Premium Current Account"],
    }
    acc_product = random.choice(acc_product_map[acc_type])
    acc_open    = rdate(since, TODAY - timedelta(days=30))
    primary_acc_id = f"ACC{acc_idx[0]:05d}"
    CUST_PRIMARY_ACCOUNT[cid] = primary_acc_id

    min_bal = max(5000, monthly_income * random.uniform(0.2, 2.5))
    ALL_ACCOUNTS.append({
        "account_id":             primary_acc_id,
        "customer_id":            cid,
        "account_type":           acc_type,
        "account_product_name":   acc_product,
        "account_number_masked":  f"XXXXXX{random.randint(1000,9999)}",
        "account_status":         "Active",
        "opening_date":           acc_open.isoformat(),
        "currency":               "INR",
        "average_monthly_balance": round(min_bal, 2),
        "branch_id":              cust.get("branch_id","BR001"),
    })
    acc_idx[0] += 1

    # Second account for premium/business customers
    if seg in ("Premium","Business") and wbool(0.25):
        sec_type = "Savings" if acc_type != "Savings" else "Current"
        sec_acc_id = f"ACC{acc_idx[0]:05d}"
        ALL_ACCOUNTS.append({
            "account_id":             sec_acc_id,
            "customer_id":            cid,
            "account_type":           sec_type,
            "account_product_name":   random.choice(acc_product_map[sec_type]),
            "account_number_masked":  f"XXXXXX{random.randint(1000,9999)}",
            "account_status":         "Active",
            "opening_date":           rdate(acc_open, TODAY).isoformat(),
            "currency":               "INR",
            "average_monthly_balance": round(max(10000, monthly_income*random.uniform(0.5,4.0)),2),
            "branch_id":              cust.get("branch_id","BR001"),
        })
        acc_idx[0] += 1

    # -- 4B: Debit Cards ---------------------------------------
    if emp == "Business" or acc_type == "Current":
        db_card = next((c for c in DEBIT_CARD_PRODUCTS if c["card_category"] == "Business"), DEBIT_CARD_PRODUCTS[6])
    elif seg == "Premium" and income >= 500000:
        db_card = random.choice([c for c in DEBIT_CARD_PRODUCTS if c["card_category"] == "Premium"])
    elif gender == "Female" and wbool(0.2):
        db_card = next((c for c in DEBIT_CARD_PRODUCTS if "Women" in c["card_name"]), DEBIT_CARD_PRODUCTS[2])
    else:
        db_card = random.choice([c for c in DEBIT_CARD_PRODUCTS if c["card_category"] in ("Classic","Classic")])

    db_id = f"DBC{dbc_idx[0]:05d}"
    CUST_DEBIT_CARDS[cid] = [db_id]
    ALL_DEBIT_CARDS.append({
        "customer_debit_card_id":  db_id,
        "customer_id":             cid,
        "account_id":              primary_acc_id,
        "debit_card_product_id":   db_card["debit_card_product_id"],
        "card_name":               db_card["card_name"],
        "card_number_masked":      f"XXXX-XXXX-XXXX-{random.randint(1000,9999)}",
        "card_network":            db_card["card_network"],
        "card_status":             "Active",
        "issue_date":              acc_open.isoformat(),
        "expiry_date":             (acc_open.replace(year=acc_open.year+5)).isoformat(),
        "international_enabled":   db_card["international_transaction"],
        "daily_atm_limit":         db_card["atm_daily_limit"],
        "daily_pos_limit":         db_card["pos_daily_limit"],
    })
    dbc_idx[0] += 1

    # -- 4C: Credit Cards --------------------------------------
    CUST_CARDS[cid] = []

    # Credit card ownership probability
    if emp in ("Student","Homemaker","Farmer","Agricultural Worker"): cc_prob = 0.15
    elif income < 200_000: cc_prob = 0.05
    elif income < 400_000: cc_prob = 0.25
    elif income < 700_000: cc_prob = 0.50
    elif income < 1_200_000: cc_prob = 0.70
    elif income < 2_500_000: cc_prob = 0.82
    else: cc_prob = 0.92

    if age < 21: cc_prob = 0.0

    if wbool(clamp(cc_prob, 0, 0.95)):
        eligible_cc = eligible_credit_cards(cust)
        if eligible_cc:
            selected = pick_credit_card(cust, eligible_cc)
            if selected:
                cat = selected.get("card_category","Classic")
                lim_map = {"Classic":(15000,150000),"Premium":(50000,800000),"Super Premium":(200000,5000000),"Business":(50000,3000000),"Co-brand":(20000,500000)}
                lo, hi = lim_map.get(cat, (15000,200000))
                if income >= 2_500_000:
                    lo = int(lo*2); hi = int(hi*2)
                credit_limit = random.randint(lo, max(lo, hi))
                util = random.uniform(0.08, 0.65)
                if wbool(0.07): util = random.uniform(0.70, 0.92)
                outstanding = round(credit_limit * util, 2)
                iss_date = rdate(since, TODAY - timedelta(days=60))
                card_id = f"CCA{cca_idx[0]:05d}"
                CUST_CARDS[cid].append(card_id)
                ALL_CREDIT_CARDS.append({
                    "customer_card_id":     card_id,
                    "customer_id":          cid,
                    "credit_card_product_id": selected["credit_card_product_id"],
                    "card_name":            selected["card_name"],
                    "card_number_masked":   f"XXXX-XXXX-XXXX-{random.randint(1000,9999)}",
                    "card_network":         selected["card_network"],
                    "card_category":        cat,
                    "issue_date":           iss_date.isoformat(),
                    "activation_date":      (iss_date + timedelta(days=random.randint(0,7))).isoformat(),
                    "expiry_date":          (iss_date + timedelta(days=365*5)).isoformat(),
                    "card_status":          "Active",
                    "credit_limit":         credit_limit,
                    "available_limit":      round(max(0, credit_limit-outstanding),2),
                    "current_outstanding":  outstanding,
                    "reward_points_balance":random.randint(0,50000),
                    "annual_spend":         round(credit_limit*random.uniform(0.5,7),2),
                    "international_enabled":selected.get("foreign_currency_markup","3.5") == "0" and "Yes" or wchoice([("Yes",30),("No",70)]),
                    "last_payment_date":    (TODAY - timedelta(days=random.randint(1,45))).isoformat(),
                })
                cca_idx[0] += 1

                # Second card for high-income customers
                if income >= 2_000_000 and wbool(0.25) and len(eligible_cc) >= 2:
                    remaining = [c for c in eligible_cc if c["credit_card_product_id"] != selected["credit_card_product_id"]]
                    if remaining:
                        sel2 = random.choice(remaining)
                        cat2 = sel2.get("card_category","Premium")
                        lo2, hi2 = lim_map.get(cat2,(50000,500000))
                        cl2 = random.randint(lo2, max(lo2,hi2))
                        ut2 = random.uniform(0.05,0.55)
                        card_id2 = f"CCA{cca_idx[0]:05d}"
                        CUST_CARDS[cid].append(card_id2)
                        ALL_CREDIT_CARDS.append({
                            "customer_card_id":     card_id2,
                            "customer_id":          cid,
                            "credit_card_product_id": sel2["credit_card_product_id"],
                            "card_name":            sel2["card_name"],
                            "card_number_masked":   f"XXXX-XXXX-XXXX-{random.randint(1000,9999)}",
                            "card_network":         sel2["card_network"],
                            "card_category":        cat2,
                            "issue_date":           (TODAY-timedelta(days=random.randint(60,1200))).isoformat(),
                            "activation_date":      (TODAY-timedelta(days=random.randint(50,1190))).isoformat(),
                            "expiry_date":          (TODAY+timedelta(days=random.randint(500,1800))).isoformat(),
                            "card_status":          "Active",
                            "credit_limit":         cl2,
                            "available_limit":      round(max(0,cl2-cl2*ut2),2),
                            "current_outstanding":  round(cl2*ut2,2),
                            "reward_points_balance":random.randint(0,75000),
                            "annual_spend":         round(cl2*random.uniform(0.5,6),2),
                            "international_enabled":wchoice([("Yes",50),("No",50)]),
                            "last_payment_date":    (TODAY-timedelta(days=random.randint(1,45))).isoformat(),
                        })
                        cca_idx[0] += 1

    # -- 4D: Loans ---------------------------------------------
    CUST_LOAN_EMIS[cid] = 0.0
    CUST_LOAN_CATS[cid] = []

    # Loan probability by segment
    if emp in ("Student","Homemaker"): loan_prob_base = 0.15
    elif emp == "Farmer": loan_prob_base = 0.30
    elif income < 200_000: loan_prob_base = 0.10
    elif income < 500_000: loan_prob_base = 0.25
    elif income < 1_000_000: loan_prob_base = 0.45
    elif income < 2_500_000: loan_prob_base = 0.55
    else: loan_prob_base = 0.50

    if wbool(loan_prob_base):
        el = eligible_loans(cust)

        # Prioritize occupation-relevant loans
        priority = []
        if occ == "Student" or emp == "Student":
            edu = [l for l in el if l["loan_category"] == "Education"]
            if edu: priority = edu
        if emp == "Farmer":
            agri = [l for l in el if l["loan_category"] == "Agriculture"]
            if agri: priority = agri
        if emp == "Business":
            biz = [l for l in el if l["customer_type"] == "Business"]
            if biz: priority = biz
        if not priority:
            # General salaried -> home/auto/personal
            salaried_cats = [l for l in el if l["loan_category"] in ("Personal","Home","Auto","Two-Wheeler")]
            if salaried_cats: priority = salaried_cats
            else: priority = el

        if priority:
            loan_prod = random.choice(priority)
            lo_amt = loan_prod.get("minimum_loan_amount", 50000)
            hi_amt = loan_prod.get("maximum_loan_amount", 2500000)
            # Cap at income-reasonable level
            max_reasonable = income * 7
            hi_amt = min(hi_amt, max_reasonable)
            if hi_amt < lo_amt:
                hi_amt = lo_amt * 2
            disburse = random.randint(int(lo_amt), int(max(lo_amt, hi_amt)))

            min_ten = loan_prod.get("minimum_tenure_months", 12)
            max_ten = loan_prod.get("maximum_tenure_months", 60)
            tenure  = random.randint(int(min_ten), int(max_ten))

            rate = to_float(loan_prod.get("interest_rate_current", 12.5)) / 12 / 100
            if rate > 0:
                emi = round(disburse * rate * (1+rate)**tenure / ((1+rate)**tenure - 1), 2)
            else:
                emi = round(disburse / tenure, 2)

            disbursed_ago_months = random.randint(3, min(tenure-1, 60))
            remaining_ten = tenure - disbursed_ago_months
            outstanding   = round(disburse * (remaining_ten / tenure), 2)
            outstanding   = min(outstanding, disburse)

            start_dt = rdate(since, TODAY - timedelta(days=disbursed_ago_months*30))

            l_id = f"LOAN{loan_idx[0]:05d}"
            CUST_LOAN_EMIS[cid] += emi
            CUST_LOAN_CATS[cid].append(loan_prod["loan_category"])
            ALL_LOANS.append({
                "customer_loan_id":       l_id,
                "customer_id":            cid,
                "loan_product_id":        loan_prod["loan_product_id"],
                "loan_product_name":      loan_prod["product_name"],
                "loan_category":          loan_prod["loan_category"],
                "loan_purpose":           loan_prod.get("loan_purpose","General"),
                "loan_status":            "Active",
                "disbursement_date":      start_dt.isoformat(),
                "disbursed_amount":       disburse,
                "outstanding_principal":  outstanding,
                "interest_rate":          to_float(loan_prod.get("interest_rate_current",12.5)),
                "original_tenure_months": tenure,
                "remaining_tenure_months":max(1, remaining_ten),
                "emi_amount":             emi,
                "emi_due_date":           random.randint(1,28),
                "last_payment_date":      (TODAY - timedelta(days=random.randint(1,35))).isoformat(),
                "collateral_provided":    loan_prod.get("collateral_required","No"),
                "account_id":             primary_acc_id,
            })
            loan_idx[0] += 1

    # -- 4E: Fixed Deposits / Deposits -------------------------
    monthly_emi  = CUST_LOAN_EMIS.get(cid, 0)
    surplus_est  = max(0, monthly_income - monthly_emi - monthly_income * 0.5)

    # FD probability based on surplus
    if surplus_est > 50000:   fd_prob = 0.75
    elif surplus_est > 20000: fd_prob = 0.55
    elif surplus_est > 8000:  fd_prob = 0.30
    elif income > 300000:     fd_prob = 0.15
    else:                     fd_prob = 0.05

    if emp in ("Retired","Pensioner"): fd_prob = 0.80
    if occ == "Student": fd_prob = 0.05

    FD_PRODUCTS = [
        ("DEP001","Regular Fixed Deposit","Fixed Deposit",6.5),
        ("DEP002","Senior Citizen Fixed Deposit","Fixed Deposit",7.0),
        ("DEP003","Recurring Deposit","Recurring Deposit",6.5),
        ("DEP004","Tax Saving Fixed Deposit","Tax Saving FD",6.5),
    ]

    if wbool(fd_prob):
        if age >= 60:
            dep_choice = FD_PRODUCTS[1]  # Senior FD
        elif emp in ("Salaried","Self-employed") and income >= 500000 and wbool(0.3):
            dep_choice = FD_PRODUCTS[3]  # Tax Saving FD
        elif wbool(0.25):
            dep_choice = FD_PRODUCTS[2]  # RD
        else:
            dep_choice = FD_PRODUCTS[0]  # Regular FD

        max_fd = min(surplus_est * 12, income * 3)
        if max_fd < 10000:
            max_fd = max(10000, income * 0.2)
        fd_amount = random.randint(10000, max(10000, int(max_fd)))

        rate = dep_choice[3] / 100
        ten_months = random.randint(6, 84)
        maturity = round(fd_amount * (1 + rate * ten_months/12), 2)
        start_fd  = rdate(since, TODAY - timedelta(days=30))
        maturity_date = start_fd + timedelta(days=int(ten_months * 30.4))

        dep_id = f"DEP{dep_idx[0]:05d}"
        ALL_DEPOSITS.append({
            "customer_deposit_id": dep_id,
            "customer_id":         cid,
            "deposit_product_id":  dep_choice[0],
            "deposit_product_name":dep_choice[1],
            "deposit_category":    dep_choice[2],
            "deposit_status":      "Active",
            "principal_amount":    fd_amount,
            "interest_rate":       dep_choice[3],
            "deposit_tenure_months": ten_months,
            "maturity_date":       maturity_date.isoformat(),
            "maturity_amount":     maturity,
            "start_date":          start_fd.isoformat(),
            "is_auto_renewal":     wchoice([("Yes",60),("No",40)]),
            "account_id":          primary_acc_id,
        })
        dep_idx[0] += 1

    # -- 4F: Investments ---------------------------------------
    CUST_SIP_AMT[cid]     = 0.0
    CUST_HAS_INVEST[cid]  = False
    CUST_HAS_DEMAT[cid]   = False
    CUST_INV_CATS[cid]    = []

    # Investment probability tiers
    if income < 200_000 or emp in ("Student","Homemaker","Farmer","Agricultural Worker"):
        sip_prob = 0.05; mf_prob = 0.02; eq_prob = 0.01; wm_prob = 0.0; pb_prob = 0.0; nps_prob = 0.05
    elif income < 400_000:
        sip_prob = 0.20; mf_prob = 0.10; eq_prob = 0.02; wm_prob = 0.0; pb_prob = 0.0; nps_prob = 0.10
    elif income < 700_000:
        sip_prob = 0.45; mf_prob = 0.30; eq_prob = 0.08; wm_prob = 0.0; pb_prob = 0.0; nps_prob = 0.20
    elif income < 1_200_000:
        sip_prob = 0.65; mf_prob = 0.50; eq_prob = 0.15; wm_prob = 0.0; pb_prob = 0.0; nps_prob = 0.30
    elif income < 3_000_000:
        sip_prob = 0.75; mf_prob = 0.65; eq_prob = 0.30; wm_prob = 0.05; pb_prob = 0.0; nps_prob = 0.40
    elif income < 10_000_000:
        sip_prob = 0.80; mf_prob = 0.75; eq_prob = 0.55; wm_prob = 0.40; pb_prob = 0.0; nps_prob = 0.45
    else:
        sip_prob = 0.75; mf_prob = 0.80; eq_prob = 0.70; wm_prob = 0.80; pb_prob = 0.55; nps_prob = 0.50

    if emp in ("Retired","Pensioner"): sip_prob *= 0.3; eq_prob *= 0.2

    inv_start = rdate(since, TODAY - timedelta(days=30))

    # SIP
    if wbool(sip_prob):
        sip_prod = random.choice([p for p in INVESTMENT_PRODUCTS if p["product_category"] == "SIP"])
        max_sip  = min(monthly_income * 0.30, surplus_est * 0.8)
        if max_sip < 500: max_sip = 500
        sip_monthly = random.randint(500, max(500, int(max_sip) // 500 * 500))
        sip_monthly = min(sip_monthly, 50000)
        sip_months  = random.randint(3, 36)
        total_invested = sip_monthly * sip_months
        curr_val = round(total_invested * random.uniform(0.98, 1.35), 2)

        CUST_SIP_AMT[cid] += sip_monthly
        CUST_HAS_INVEST[cid] = True
        CUST_INV_CATS[cid].append("SIP")
        ALL_INVESTMENTS.append({
            "customer_investment_id":  f"INV{inv_idx[0]:05d}",
            "customer_id":             cid,
            "investment_product_id":   sip_prod["investment_product_id"],
            "investment_product_name": sip_prod["product_name"],
            "investment_category":     "SIP",
            "provider":                sip_prod["provider"],
            "investment_type":         "SIP",
            "investment_mode":         "Monthly",
            "monthly_amount":          sip_monthly,
            "initial_investment_amount": sip_monthly,
            "total_invested_amount":   total_invested,
            "current_value":           curr_val,
            "start_date":              inv_start.isoformat(),
            "status":                  "Active",
        })
        inv_idx[0] += 1

    # Mutual Fund (lumpsum)
    if wbool(mf_prob):
        mf_prod = random.choice([p for p in INVESTMENT_PRODUCTS if p["product_category"] == "Mutual Fund"])
        mf_inv  = random.randint(5000, max(5000, int(income*0.15)))
        mf_val  = round(mf_inv * random.uniform(0.92, 1.45), 2)
        CUST_HAS_INVEST[cid] = True
        CUST_INV_CATS[cid].append("Mutual Fund")
        ALL_INVESTMENTS.append({
            "customer_investment_id":  f"INV{inv_idx[0]:05d}",
            "customer_id":             cid,
            "investment_product_id":   mf_prod["investment_product_id"],
            "investment_product_name": mf_prod["product_name"],
            "investment_category":     "Mutual Fund",
            "provider":                mf_prod["provider"],
            "investment_type":         "Lumpsum",
            "investment_mode":         "Lumpsum",
            "monthly_amount":          0,
            "initial_investment_amount": mf_inv,
            "total_invested_amount":   mf_inv,
            "current_value":           mf_val,
            "start_date":              inv_start.isoformat(),
            "status":                  "Active",
        })
        inv_idx[0] += 1

    # NPS
    if wbool(nps_prob) and age >= 18 and age <= 65:
        nps_prod = next(p for p in INVESTMENT_PRODUCTS if p["product_category"] == "NPS")
        nps_monthly = random.randint(500, max(500, int(monthly_income*0.05)))
        nps_months  = random.randint(6, 36)
        nps_total   = nps_monthly * nps_months
        nps_val     = round(nps_total * random.uniform(1.0, 1.12), 2)
        CUST_HAS_INVEST[cid] = True
        CUST_INV_CATS[cid].append("NPS")
        ALL_INVESTMENTS.append({
            "customer_investment_id":  f"INV{inv_idx[0]:05d}",
            "customer_id":             cid,
            "investment_product_id":   nps_prod["investment_product_id"],
            "investment_product_name": nps_prod["product_name"],
            "investment_category":     "NPS",
            "provider":                nps_prod["provider"],
            "investment_type":         "NPS",
            "investment_mode":         "Monthly",
            "monthly_amount":          nps_monthly,
            "initial_investment_amount": nps_monthly,
            "total_invested_amount":   nps_total,
            "current_value":           nps_val,
            "start_date":              inv_start.isoformat(),
            "status":                  "Active",
        })
        inv_idx[0] += 1

    # Demat + Equity
    if wbool(eq_prob) and age >= 18:
        demat_prod = next(p for p in INVESTMENT_PRODUCTS if p["product_category"] == "Demat")
        CUST_HAS_DEMAT[cid] = True
        CUST_HAS_INVEST[cid] = True
        CUST_INV_CATS[cid].append("Demat")
        ALL_INVESTMENTS.append({
            "customer_investment_id":  f"INV{inv_idx[0]:05d}",
            "customer_id":             cid,
            "investment_product_id":   demat_prod["investment_product_id"],
            "investment_product_name": demat_prod["product_name"],
            "investment_category":     "Demat",
            "provider":                demat_prod["provider"],
            "investment_type":         "Demat Account",
            "investment_mode":         "One-Time",
            "monthly_amount":          0,
            "initial_investment_amount": 0,
            "total_invested_amount":   0,
            "current_value":           0,
            "start_date":              inv_start.isoformat(),
            "status":                  "Active",
        })
        inv_idx[0] += 1

        # Equity trading
        eq_prod  = next(p for p in INVESTMENT_PRODUCTS if p["product_category"] == "Stock / Equity")
        eq_inv   = random.randint(10000, max(10000, int(income*0.10)))
        eq_val   = round(eq_inv * random.uniform(0.70, 1.80), 2)
        CUST_INV_CATS[cid].append("Stock / Equity")
        ALL_INVESTMENTS.append({
            "customer_investment_id":  f"INV{inv_idx[0]:05d}",
            "customer_id":             cid,
            "investment_product_id":   eq_prod["investment_product_id"],
            "investment_product_name": eq_prod["product_name"],
            "investment_category":     "Stock / Equity",
            "provider":                eq_prod["provider"],
            "investment_type":         "Direct Equity",
            "investment_mode":         "Lumpsum",
            "monthly_amount":          0,
            "initial_investment_amount": eq_inv,
            "total_invested_amount":   eq_inv,
            "current_value":           eq_val,
            "start_date":              inv_start.isoformat(),
            "status":                  "Active",
        })
        inv_idx[0] += 1

    # ETF
    if wbool(eq_prob*0.5) and CUST_HAS_DEMAT[cid]:
        etf_prod = next(p for p in INVESTMENT_PRODUCTS if p["product_category"] == "ETF")
        etf_inv  = random.randint(5000, max(5000, int(income*0.05)))
        etf_val  = round(etf_inv * random.uniform(0.90, 1.50), 2)
        CUST_INV_CATS[cid].append("ETF")
        ALL_INVESTMENTS.append({
            "customer_investment_id":  f"INV{inv_idx[0]:05d}",
            "customer_id":             cid,
            "investment_product_id":   etf_prod["investment_product_id"],
            "investment_product_name": etf_prod["product_name"],
            "investment_category":     "ETF",
            "provider":                etf_prod["provider"],
            "investment_type":         "ETF",
            "investment_mode":         "Lumpsum",
            "monthly_amount":          0,
            "initial_investment_amount": etf_inv,
            "total_invested_amount":   etf_inv,
            "current_value":           etf_val,
            "start_date":              inv_start.isoformat(),
            "status":                  "Active",
        })
        inv_idx[0] += 1

    # Wealth Management
    if wbool(wm_prob) and income >= 5_000_000:
        wm_prod = next(p for p in INVESTMENT_PRODUCTS if p["product_category"] == "Wealth Management")
        wm_inv  = random.randint(5_000_000, max(5_000_000, int(income*2)))
        wm_val  = round(wm_inv * random.uniform(1.02, 1.25), 2)
        CUST_HAS_INVEST[cid] = True
        CUST_INV_CATS[cid].append("Wealth Management")
        ALL_INVESTMENTS.append({
            "customer_investment_id":  f"INV{inv_idx[0]:05d}",
            "customer_id":             cid,
            "investment_product_id":   wm_prod["investment_product_id"],
            "investment_product_name": wm_prod["product_name"],
            "investment_category":     "Wealth Management",
            "provider":                wm_prod["provider"],
            "investment_type":         "Portfolio Management",
            "investment_mode":         "Managed",
            "monthly_amount":          0,
            "initial_investment_amount": wm_inv,
            "total_invested_amount":   wm_inv,
            "current_value":           wm_val,
            "start_date":              inv_start.isoformat(),
            "status":                  "Active",
        })
        inv_idx[0] += 1

    # Private Banking
    if wbool(pb_prob) and income >= 10_000_000:
        pb_prod = next(p for p in INVESTMENT_PRODUCTS if p["product_category"] == "Private Banking")
        pb_inv  = random.randint(50_000_000, max(50_000_000, int(income*5)))
        pb_val  = round(pb_inv * random.uniform(1.02, 1.20), 2)
        CUST_INV_CATS[cid].append("Private Banking")
        ALL_INVESTMENTS.append({
            "customer_investment_id":  f"INV{inv_idx[0]:05d}",
            "customer_id":             cid,
            "investment_product_id":   pb_prod["investment_product_id"],
            "investment_product_name": pb_prod["product_name"],
            "investment_category":     "Private Banking",
            "provider":                pb_prod["provider"],
            "investment_type":         "Private Banking",
            "investment_mode":         "Managed",
            "monthly_amount":          0,
            "initial_investment_amount": pb_inv,
            "total_invested_amount":   pb_inv,
            "current_value":           pb_val,
            "start_date":              inv_start.isoformat(),
            "status":                  "Active",
        })
        inv_idx[0] += 1

    # -- 4G: Insurance -----------------------------------------
    CUST_HAS_INS[cid]  = False
    CUST_INS_CATS[cid] = []

    has_auto_loan = "Auto" in CUST_LOAN_CATS.get(cid,[])
    has_home_loan = "Home" in CUST_LOAN_CATS.get(cid,[])

    def try_insurance(prod_id, ins_type, probability, age_min=18, age_max=75):
        if age < age_min or age > age_max:
            return
        if not wbool(probability):
            return
        prod = next((p for p in INSURANCE_PRODUCTS if p["insurance_product_id"] == prod_id), None)
        if not prod:
            return
        if income < prod.get("minimum_income_annual", 0):
            return
        prem = random.randint(int(prod["minimum_premium"]), int(min(prod["maximum_premium"], max(prod["minimum_premium"], income*0.05))))
        sum_ins_lo = prod.get("minimum_sum_insured", 500000)
        sum_ins_hi = prod.get("maximum_sum_insured", 10000000)
        sum_ins = random.randint(int(sum_ins_lo), int(min(sum_ins_hi, max(sum_ins_lo, income*8))))
        CUST_HAS_INS[cid] = True
        CUST_INS_CATS[cid].append(ins_type)
        ALL_INSURANCE.append({
            "customer_insurance_id":  f"INS{ins_idx[0]:05d}",
            "customer_id":            cid,
            "insurance_product_id":   prod_id,
            "insurance_product_name": prod["product_name"],
            "insurance_type":         ins_type,
            "insurance_company":      prod["insurance_company"],
            "sum_insured":            sum_ins,
            "annual_premium":         prem,
            "premium_frequency":      prod["premium_frequency"],
            "policy_start_date":      rdate(since, TODAY-timedelta(days=30)).isoformat(),
            "policy_end_date":        (rdate(since, TODAY-timedelta(days=30)) + timedelta(days=365)).isoformat(),
            "policy_status":          "Active",
            "nominee_name":           f"Family of {cust['first_name']}",
        })
        ins_idx[0] += 1

    # Term / Life
    if income >= 200000 and age <= 65:
        life_p = 0.0
        if marital == "Married": life_p = 0.55
        elif income >= 500000: life_p = 0.35
        else: life_p = 0.20
        try_insurance("INS001","Life",life_p, 18, 65)

    # Health
    health_p = 0.0
    if age >= 50: health_p = 0.65
    elif age >= 35 and marital == "Married": health_p = 0.55
    elif income >= 500000: health_p = 0.45
    elif income >= 300000: health_p = 0.25
    if age >= 60:
        try_insurance("INS005","Health",health_p*1.2, 60, 80)
    else:
        fam_p = health_p if marital != "Married" else health_p * 1.2
        try_insurance("INS004" if marital=="Married" else "INS003","Health",fam_p, 18, 65)

    # Motor
    try_insurance("INS007","Motor", 0.5 if has_auto_loan else (0.25 if income>=400000 else 0.10), 18, 75)

    # Home
    if has_home_loan:
        try_insurance("INS009","Home", 0.60, 18, 75)
    elif income >= 1000000 and wbool(0.15):
        try_insurance("INS009","Home", 0.15, 18, 75)

    # Travel (frequent travellers)
    travel_p = 0.05
    if income >= 1000000: travel_p = 0.25
    if income >= 3000000: travel_p = 0.45
    if occ in ("Software Engineer","Senior Software Engineer","Data Scientist","Entrepreneur","Business Owner","Exporter","Importer"): travel_p += 0.15
    try_insurance("INS006","Travel",min(travel_p,0.60), 18, 70)

    # PA
    if income >= 300000:
        try_insurance("INS008","Personal Accident", 0.20 if emp=="Salaried" else 0.15, 18, 65)

    # Child plan
    if marital == "Married" and 28 <= age <= 50 and income >= 600000:
        try_insurance("INS011","Child Insurance", 0.15, 18, 50)

    # ULIP
    if income >= 1200000 and age <= 55:
        try_insurance("INS010","ULIP", 0.12, 18, 60)

write_csv(HOLDINGS_DIR / "customer_accounts.csv", ALL_ACCOUNTS, "Customer Accounts")
write_csv(HOLDINGS_DIR / "customer_debit_cards.csv", ALL_DEBIT_CARDS, "Customer Debit Cards")
write_csv(HOLDINGS_DIR / "customer_credit_cards.csv", ALL_CREDIT_CARDS, "Customer Credit Cards")
write_csv(HOLDINGS_DIR / "customer_loans.csv", ALL_LOANS, "Customer Loans")
write_csv(HOLDINGS_DIR / "customer_deposits.csv", ALL_DEPOSITS, "Customer Deposits")
write_csv(HOLDINGS_DIR / "customer_investments.csv", ALL_INVESTMENTS, "Customer Investments")
write_csv(HOLDINGS_DIR / "customer_insurance.csv", ALL_INSURANCE, "Customer Insurance")
print("  [OK] Phase 4 complete\n")


# ═══════════════════════════════════════════════════════════════
# SECTION 5 — TRANSACTION GENERATION (CORRELATED)
# ═══════════════════════════════════════════════════════════════

print("PHASE 5 — Generating correlated transactions...")

# Merchant lookup by category
MERCHANTS_BY_CAT = {}
for m in MERCHANT_MASTER_RAW:
    cat = m[2]
    MERCHANTS_BY_CAT.setdefault(cat, []).append(m)

def pick_merchant(cat: str):
    pool = MERCHANTS_BY_CAT.get(cat, [])
    if not pool:
        # fallback
        return ("MER2201","UPI Transfer","","")
    return random.choice(pool)

TRANSACTION_MODES_W = [
    ("UPI",45),("Debit Card",20),("Credit Card",15),("NEFT",5),
    ("IMPS",5),("RTGS",2),("ATM",4),("Cash",4),
]

def occupation_profile(cust: Dict) -> List[Tuple[str, int]]:
    """Return weighted list of merchant categories for this customer."""
    occ = cust["occupation"]
    emp = cust["employment_type"]
    income = cust["annual_income"]

    base = [
        ("Grocery",11),("Food Delivery",9),("P2P Transfer",14),("Telecom",5),
        ("Utilities",6),("Bills",4),("Restaurant",5),
    ]
    if income >= 500000:
        base += [("E-Commerce",8),("Shopping",5),("Entertainment",4)]
    if income >= 1000000:
        base += [("Airlines",3),("Hotels",3)]

    if emp in ("Student",):
        base += [("Education",8),("Education Fees",6),("Food Delivery",5),("Cab",5)]
    if emp == "Farmer":
        base += [("Agriculture",15),("Agriculture Equipment",5)]
    if occ in ("Business Owner","Entrepreneur","Manufacturer","Exporter","Importer"):
        base += [("P2P Transfer",10),("Airlines",3),("Hotels",2)]
    if emp in ("Retired","Pensioner"):
        base += [("Healthcare",6),("Pharmacy",5)]
        base = [(c,max(1,w-3)) if c in ("E-Commerce","Entertainment") else (c,w) for c,w in base]

    if CUST_LOAN_EMIS.get(cust["customer_id"],0) > 0:
        base.append(("Bills",3))  # EMI payment via bills

    if CUST_SIP_AMT.get(cust["customer_id"],0) > 0:
        base.append(("SIP / Mutual Fund",3))

    if CUST_HAS_INVEST.get(cust["customer_id"],False) and CUST_HAS_DEMAT.get(cust["customer_id"],False):
        base.append(("Investment",3))

    if CUST_HAS_INS.get(cust["customer_id"],False):
        base.append(("Insurance",1))

    if income >= 400000:
        base.append(("Fuel",4))

    return base

def amount_for_category(cat: str, income: int) -> float:
    monthly = income / 12
    ranges = {
        "Airlines":           (3000, min(80000, monthly*2)),
        "Food Delivery":      (100,  min(2000, monthly*0.05)),
        "E-Commerce":         (200,  min(50000, monthly*0.5)),
        "Shopping":           (300,  min(30000, monthly*0.4)),
        "Grocery":            (200,  min(8000,  monthly*0.15)),
        "Cab":                (50,   min(2000,  monthly*0.05)),
        "Bus":                (20,   300),
        "Train":              (100,  5000),
        "Hotels":             (1000, min(50000, monthly*1.5)),
        "Movies":             (150,  1500),
        "Fuel":               (500,  min(10000, monthly*0.08)),
        "Utilities":          (200,  min(5000,  monthly*0.05)),
        "Telecom":            (200,  min(2000,  monthly*0.03)),
        "Entertainment":      (99,   min(1500,  monthly*0.02)),
        "Healthcare":         (200,  min(30000, monthly*0.3)),
        "Pharmacy":           (100,  min(5000,  monthly*0.05)),
        "Education":          (200,  min(5000,  monthly*0.05)),
        "Education Fees":     (10000,min(100000,monthly*3)),
        "Investment":         (500,  min(50000, monthly*0.8)),
        "SIP / Mutual Fund":  (500,  min(50000, monthly*0.3)),
        "Insurance":          (3000, min(50000, monthly*0.5)),
        "Bills":              (100,  min(20000, monthly*0.2)),
        "Restaurant":         (200,  min(10000, monthly*0.15)),
        "P2P Transfer":       (100,  min(50000, monthly*0.5)),
        "Agriculture":        (500,  min(50000, monthly*0.5)),
        "Agriculture Equipment":(5000,min(500000,monthly*5)),
        "Rent":               (5000, min(50000, monthly*0.5)),
    }
    lo, hi = ranges.get(cat, (100, min(5000, monthly*0.1)))
    lo = max(1, int(lo)); hi = max(lo, int(hi))
    return round(random.uniform(lo, hi), 2)

CITIES_LIST = [c[0] for c in CITIES]
STATES_LIST  = [c[1] for c in CITIES]

ALL_TRANSACTIONS = []
tx_id_set = set()
tx_idx = 1

# Salary credits for salaried customers
for cust in CUSTOMERS:
    cid = cust["customer_id"]
    emp = cust["employment_type"]
    income = cust["annual_income"]
    if emp not in ("Salaried","Govt","Defence Personnel"):
        continue
    acc_id = CUST_PRIMARY_ACCOUNT.get(cid, f"ACC{tx_idx:05d}")
    monthly = round(income / 12, 2)
    for months_ago in range(0, 12):
        tx_date = END_DATE - timedelta(days=months_ago*30 + random.randint(0,3))
        if tx_date < START_DATE:
            break
        t_id = f"TXN{tx_idx:07d}"
        tx_idx += 1
        ALL_TRANSACTIONS.append({
            "transaction_id":      t_id,
            "customer_id":         cid,
            "account_id":          acc_id,
            "card_id":             "",
            "transaction_date":    tx_date.strftime("%Y-%m-%d"),
            "transaction_time":    f"{random.randint(8,11):02d}:{random.randint(0,59):02d}:00",
            "transaction_type":    "Credit",
            "transaction_mode":    "NEFT",
            "amount":              monthly,
            "currency":            "INR",
            "transaction_status":  "Success",
            "merchant_id":         "",
            "merchant_name":       cust.get("employer_name","Employer"),
            "receiver_name":       cust["first_name"]+" "+cust["last_name"],
            "receiver_identifier": acc_id,
            "mcc_code":            "",
            "transaction_description": "SALARY CREDIT",
            "reference_number":    f"REF{tx_idx:09d}",
            "channel":             "Bank Transfer",
            "location_city":       cust["city"],
            "location_state":      cust["state"],
            "location_country":    "India",
            "created_at":          tx_date.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at":          tx_date.strftime("%Y-%m-%d %H:%M:%S"),
        })

# Debit transactions per customer (behavioural)
TARGET_TX = 15000
# Remaining budget after salary credits
remaining = max(TARGET_TX - len(ALL_TRANSACTIONS), 5000)
per_customer = max(5, remaining // NUM_CUSTOMERS)

for cust in CUSTOMERS:
    cid    = cust["customer_id"]
    income = cust["annual_income"]
    acc_id = CUST_PRIMARY_ACCOUNT.get(cid, "ACC00001")
    cards  = CUST_CARDS.get(cid, [])
    num_tx = random.randint(max(3, per_customer-5), per_customer+10)

    cat_profile = occupation_profile(cust)
    cats  = [x[0] for x in cat_profile]
    wts   = [x[1] for x in cat_profile]

    for _ in range(num_tx):
        cat = random.choices(cats, weights=wts, k=1)[0]
        merchant = pick_merchant(cat)
        m_id   = merchant[0]
        m_name = merchant[1]
        mcc    = merchant[3] if len(merchant)>3 else ""

        amt = amount_for_category(cat, income)
        mode = wchoice(TRANSACTION_MODES_W)

        # Use credit card if customer has one and mode matches
        card_id = ""
        if mode == "Credit Card" and cards:
            card_id = random.choice(cards)
        elif mode == "Debit Card":
            dcs = CUST_DEBIT_CARDS.get(cid,[])
            card_id = dcs[0] if dcs else ""

        tx_date = START_DATE + timedelta(days=random.randint(0, 364))
        t_id = f"TXN{tx_idx:07d}"
        tx_idx += 1

        city_i = random.randint(0, len(CITIES_LIST)-1)
        ALL_TRANSACTIONS.append({
            "transaction_id":      t_id,
            "customer_id":         cid,
            "account_id":          acc_id,
            "card_id":             card_id,
            "transaction_date":    tx_date.strftime("%Y-%m-%d"),
            "transaction_time":    f"{random.randint(6,23):02d}:{random.randint(0,59):02d}:{random.randint(0,59):02d}",
            "transaction_type":    "Debit",
            "transaction_mode":    mode,
            "amount":              amt,
            "currency":            "INR",
            "transaction_status":  wchoice([("Success",97),("Failed",2),("Pending",1)]),
            "merchant_id":         m_id,
            "merchant_name":       m_name,
            "receiver_name":       m_name,
            "receiver_identifier": m_id,
            "mcc_code":            mcc,
            "transaction_description": f"{cat.upper()} - {m_name}",
            "reference_number":    f"REF{tx_idx:09d}",
            "channel":             wchoice([("Mobile App",50),("Web",20),("POS",20),("ATM",10)]),
            "location_city":       CITIES_LIST[city_i],
            "location_state":      STATES_LIST[city_i],
            "location_country":    "India",
            "created_at":          tx_date.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at":          tx_date.strftime("%Y-%m-%d %H:%M:%S"),
        })

# Deduplicate
seen_tx = set()
UNIQUE_TRANSACTIONS = []
for tx in ALL_TRANSACTIONS:
    if tx["transaction_id"] not in seen_tx:
        seen_tx.add(tx["transaction_id"])
        UNIQUE_TRANSACTIONS.append(tx)

write_csv(OUTPUT_DIR / "raw_transactions.csv", UNIQUE_TRANSACTIONS, "Raw Transactions")
print(f"  [OK] Phase 5 complete — {len(UNIQUE_TRANSACTIONS):,} transactions\n")


# ═══════════════════════════════════════════════════════════════
# SECTION 6 — CUSTOMER 360 JSON
# ═══════════════════════════════════════════════════════════════

print("PHASE 6 — Building Customer 360 JSON...")

def build_customer_360(cust: Dict) -> Dict:
    cid = cust["customer_id"]
    income = cust["annual_income"]
    monthly_income = income / 12

    # Gather holdings
    accounts  = [a for a in ALL_ACCOUNTS    if a["customer_id"] == cid]
    deb_cards = [d for d in ALL_DEBIT_CARDS if d["customer_id"] == cid]
    cre_cards = [c for c in ALL_CREDIT_CARDS if c["customer_id"] == cid]
    loans_own = [l for l in ALL_LOANS       if l["customer_id"] == cid]
    deposits  = [d for d in ALL_DEPOSITS    if d["customer_id"] == cid]
    invest    = [i for i in ALL_INVESTMENTS if i["customer_id"] == cid]
    insure    = [i for i in ALL_INSURANCE   if i["customer_id"] == cid]

    # Investment breakdown
    sip_list = [i for i in invest if i["investment_category"] == "SIP"]
    mf_list  = [i for i in invest if i["investment_category"] == "Mutual Fund"]
    stock_list = [i for i in invest if i["investment_category"] == "Stock / Equity"]
    bond_list  = [i for i in invest if i["investment_category"] == "Bond"]
    nps_list   = [i for i in invest if i["investment_category"] == "NPS"]
    demat_list = [i for i in invest if i["investment_category"] == "Demat"]
    etf_list   = [i for i in invest if i["investment_category"] == "ETF"]
    wm_list    = [i for i in invest if i["investment_category"] == "Wealth Management"]
    pb_list    = [i for i in invest if i["investment_category"] == "Private Banking"]

    # Insurance breakdown
    life_ins   = [i for i in insure if i["insurance_type"] in ("Life","ULIP")]
    health_ins = [i for i in insure if i["insurance_type"] == "Health"]
    travel_ins = [i for i in insure if i["insurance_type"] == "Travel"]
    motor_ins  = [i for i in insure if i["insurance_type"] == "Motor"]
    home_ins   = [i for i in insure if i["insurance_type"] == "Home"]
    other_ins  = [i for i in insure if i["insurance_type"] not in ("Life","ULIP","Health","Travel","Motor","Home")]

    # Financial summary
    total_credit_limit    = sum(c.get("credit_limit",0) for c in cre_cards)
    total_credit_outstanding = sum(c.get("current_outstanding",0) for c in cre_cards)
    credit_util_ratio     = round(total_credit_outstanding/total_credit_limit,4) if total_credit_limit > 0 else 0.0
    total_loan_outstanding = sum(l.get("outstanding_principal",0) for l in loans_own)
    total_monthly_emi      = sum(l.get("emi_amount",0) for l in loans_own)
    total_deposit_value    = sum(d.get("principal_amount",0) for d in deposits)
    total_invest_value     = sum(i.get("current_value",0) for i in invest)
    total_monthly_sip      = sum(i.get("monthly_amount",0) for i in invest if i.get("monthly_amount",0) > 0)
    total_insurance_cover  = sum(i.get("sum_insured",0) for i in insure)

    return {
        "customer_id": cid,
        "personal_profile": {
            "customer_id":    cid,
            "customer_number":cust["customer_number"],
            "full_name":      f"{cust['first_name']} {cust['last_name']}",
            "first_name":     cust["first_name"],
            "last_name":      cust["last_name"],
            "date_of_birth":  cust["date_of_birth"],
            "age":            cust["age"],
            "gender":         cust["gender"],
            "marital_status": cust["marital_status"],
            "nationality":    cust["nationality"],
            "city":           cust["city"],
            "state":          cust["state"],
            "email":          cust["email"],
            "mobile":         cust["mobile_number"],
            "preferred_channel": cust["preferred_channel"],
            "preferred_language": cust["preferred_language"],
            "marketing_consent": cust["marketing_consent"],
        },
        "employment_and_income": {
            "occupation":       cust["occupation"],
            "occupation_type":  cust["occupation_type"],
            "employment_type":  cust["employment_type"],
            "employer_name":    cust["employer_name"],
            "annual_income":    income,
            "monthly_income":   round(monthly_income, 2),
            "income_range":     cust["income_range"],
            "education_level":  cust["education_level"],
        },
        "banking_relationship": {
            "customer_since":          cust["customer_since"],
            "customer_segment_type":   cust["customer_segment_type"],
            "customer_status":         cust["customer_status"],
            "risk_profile":            cust["risk_profile"],
            "credit_score":            cust["credit_score"],
            "kyc_status":              cust["kyc_status"],
            "relationship_manager_id": cust["relationship_manager_id"],
            "residential_status":      cust["residential_status"],
        },
        "accounts":    accounts,
        "debit_cards": deb_cards,
        "credit_cards":cre_cards,
        "loans":       loans_own,
        "deposits":    deposits,
        "investments": {
            "sip":             sip_list,
            "mutual_funds":    mf_list,
            "stocks":          stock_list,
            "bonds":           bond_list,
            "nps":             nps_list,
            "demat":           demat_list,
            "etf":             etf_list,
            "gold_etf":        [i for i in invest if i["investment_category"]=="Gold ETF"],
            "wealth_management": wm_list,
            "private_banking": pb_list,
            "all":             invest,
        },
        "insurance": {
            "life":             life_ins,
            "health":           health_ins,
            "travel":           travel_ins,
            "motor":            motor_ins,
            "home":             home_ins,
            "personal_accident":[i for i in insure if i["insurance_type"]=="Personal Accident"],
            "child":            [i for i in insure if i["insurance_type"]=="Child Insurance"],
            "other":            other_ins,
            "all":              insure,
        },
        "financial_summary": {
            "total_credit_limit":         total_credit_limit,
            "total_credit_outstanding":   total_credit_outstanding,
            "credit_utilization_ratio":   credit_util_ratio,
            "total_loan_outstanding":     total_loan_outstanding,
            "total_monthly_emi":          round(total_monthly_emi, 2),
            "total_deposit_value":        total_deposit_value,
            "total_investment_value":     round(total_invest_value, 2),
            "total_monthly_sip":          round(total_monthly_sip, 2),
            "total_insurance_cover":      total_insurance_cover,
            "estimated_monthly_surplus":  round(max(0, monthly_income - total_monthly_emi - monthly_income*0.5), 2),
        },
        "product_summary": {
            "total_accounts":          len(accounts),
            "total_debit_cards":       len(deb_cards),
            "total_credit_cards":      len(cre_cards),
            "total_active_loans":      len(loans_own),
            "total_active_deposits":   len(deposits),
            "total_investment_products": len(invest),
            "total_insurance_policies":  len(insure),
            "has_credit_card":   len(cre_cards) > 0,
            "has_debit_card":    len(deb_cards) > 0,
            "has_loan":          len(loans_own) > 0,
            "has_fd_or_deposit": len(deposits) > 0,
            "has_investment":    len(invest) > 0,
            "has_sip":           len(sip_list) > 0,
            "has_mutual_fund":   len(mf_list) > 0,
            "has_stocks":        len(stock_list) > 0,
            "has_bonds":         len(bond_list) > 0,
            "has_nps":           len(nps_list) > 0,
            "has_demat":         len(demat_list) > 0,
            "has_etf":           len(etf_list) > 0,
            "has_gold_etf":      any(i["investment_category"]=="Gold ETF" for i in invest),
            "has_life_insurance":   len(life_ins) > 0,
            "has_health_insurance": len(health_ins) > 0,
            "has_travel_insurance": len(travel_ins) > 0,
            "has_motor_insurance":  len(motor_ins) > 0,
            "has_home_insurance":   len(home_ins) > 0,
            "loan_categories":      list({l["loan_category"] for l in loans_own}),
            "insurance_types":      list({i["insurance_type"] for i in insure}),
            "investment_categories":list({i["investment_category"] for i in invest}),
            "card_names":           [c["card_name"] for c in cre_cards],
        },
    }

CUSTOMER_360 = {}
for cust in CUSTOMERS:
    CUSTOMER_360[cust["customer_id"]] = build_customer_360(cust)

c360_path = HOLDINGS_DIR / "customer_360.json"
with open(c360_path, "w", encoding="utf-8") as f:
    json.dump(CUSTOMER_360, f, ensure_ascii=False, default=str)
print(f"  [JSON] Customer 360: {len(CUSTOMER_360):,} profiles -> {c360_path.name}")
print("  [OK] Phase 6 complete\n")


# ═══════════════════════════════════════════════════════════════
# SECTION 7 — VALIDATION
# ═══════════════════════════════════════════════════════════════

print("PHASE 7 — Validating data...")

errors  = []
warns   = []

cust_ids  = {c["customer_id"] for c in CUSTOMERS}
acc_ids   = {a["account_id"]  for a in ALL_ACCOUNTS}
cc_pids   = {c["credit_card_product_id"] for c in CREDIT_CARD_PRODUCTS}
loan_pids = {l["loan_product_id"] for l in LOAN_PRODUCTS}
inv_pids  = {i["investment_product_id"] for i in INVESTMENT_PRODUCTS}
ins_pids  = {i["insurance_product_id"] for i in INSURANCE_PRODUCTS}

# Uniqueness
if len(cust_ids) != NUM_CUSTOMERS:
    errors.append(f"Customer ID duplicates detected: {NUM_CUSTOMERS - len(cust_ids)}")
if len({a["account_id"] for a in ALL_ACCOUNTS}) != len(ALL_ACCOUNTS):
    errors.append("Account ID duplicates detected")

# FK: customer_id in holdings
for rec in ALL_ACCOUNTS + ALL_DEBIT_CARDS + ALL_CREDIT_CARDS + ALL_LOANS + ALL_DEPOSITS + ALL_INVESTMENTS + ALL_INSURANCE:
    if rec["customer_id"] not in cust_ids:
        errors.append(f"Orphan customer_id {rec['customer_id']}")
        break

# Loan: outstanding <= disbursed
for l in ALL_LOANS:
    if l["outstanding_principal"] > l["disbursed_amount"]:
        errors.append(f"Loan {l['customer_loan_id']}: outstanding > disbursed")
        break

# Credit card: outstanding <= limit
for c in ALL_CREDIT_CARDS:
    if c["current_outstanding"] > c["credit_limit"]:
        errors.append(f"CC {c['customer_card_id']}: outstanding > limit")
        break

# Investment: current_value >= 0
for i in ALL_INVESTMENTS:
    if i["current_value"] < 0:
        errors.append(f"Investment {i['customer_investment_id']}: negative current_value")
        break

# SIP amount sanity
for i in ALL_INVESTMENTS:
    if i["investment_category"] == "SIP" and i.get("monthly_amount",0) > 0:
        cust = CUST_BY_ID.get(i["customer_id"])
        if cust:
            mi = cust["annual_income"] / 12
            if i["monthly_amount"] > mi * 0.5:
                warns.append(f"SIP {i['customer_investment_id']}: monthly_amount > 50% income")

for e in errors:
    print(f"  [ERROR] {e}")
for w in warns[:5]:
    print(f"  [WARN]  {w}")

if errors:
    print(f"\n  [FAIL] Validation failed with {len(errors)} errors. Fix before pushing to Supabase.")
    if not args.csv_only:
        sys.exit(1)
else:
    print(f"  [OK] Validation passed ({len(warns)} warnings)\n")


# ═══════════════════════════════════════════════════════════════
# SECTION 8 — SUPABASE PUSH
# ═══════════════════════════════════════════════════════════════

if args.csv_only:
    print("SKIPPING Supabase push (--csv-only mode)\n")
else:
    print("PHASE 8 — Pushing to Supabase...")
    if not SUPABASE_DB_URL:
        print("  [ERROR] SUPABASE_DB_URL not set in .env — skipping push")
    else:
        try:
            import psycopg2
            from psycopg2.extras import execute_values

            print("  Connecting to Supabase...")
            conn = psycopg2.connect(SUPABASE_DB_URL)
            conn.autocommit = False
            cur = conn.cursor()
            print("  Connected.\n")

            def db_clean(val):
                if val is None: return None
                try:
                    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
                        return None
                except Exception: pass
                return val

            def push_table(table: str, rows: List[Dict], cols: List[str], description: str, batch=500):
                if not rows:
                    print(f"  [SKIP]  {description}: 0 rows")
                    return
                # Filter to cols that exist in data dict
                available = [c for c in cols if c in rows[0]]
                try:
                    cur.execute(f'DELETE FROM "{table}"')
                    conn.commit()
                    total = 0
                    for i in range(0, len(rows), batch):
                        chunk = rows[i:i+batch]
                        data  = [tuple(db_clean(r.get(c)) for c in available) for r in chunk]
                        sql   = f'INSERT INTO "{table}" ({", ".join(available)}) VALUES %s'
                        execute_values(cur, sql, data, page_size=batch)
                        conn.commit()
                        total += len(chunk)
                    print(f"  [DB]    {description}: {total:,} rows -> {table}")
                except Exception as _e:
                    conn.rollback()
                    print(f"  [ERROR] Supabase push failed: {str(_e).split(chr(10))[0]}")

            if args.reset:
                print("  [RESET] Truncating all tables...")
                tables_to_reset = [
                    "raw_transactions","customer_insurance","customer_investments",
                    "customer_deposits","customer_loans","customer_credit_cards",
                    "customer_debit_cards","customer_accounts","customers",
                    "merchants","debit_card_products","insurance_products",
                    "investment_products","loan_products","credit_card_products",
                ]
                for t in tables_to_reset:
                    try:
                        cur.execute(f"TRUNCATE TABLE {t} RESTART IDENTITY CASCADE")
                    except Exception:
                        conn.rollback()
                conn.commit()
                print("  [RESET] Done.\n")

            # Hash passwords if needed
            if not args.no_hash:
                try:
                    import bcrypt
                    HAS_BCRYPT = True
                except ImportError:
                    HAS_BCRYPT = False
                    print("  [WARN]  bcrypt not installed — storing plain text passwords")
            else:
                HAS_BCRYPT = False

            # 1. Credit Card Products
            push_table("credit_card_products", CREDIT_CARD_PRODUCTS, [
                "credit_card_product_id","product_code","card_name","card_variant","card_category",
                "card_type","card_network","card_form_factor","co_brand","co_brand_partner",
                "product_status","joining_fee","annual_fee","renewal_fee","interest_rate_annual",
                "minimum_age","maximum_age","minimum_income_monthly","minimum_income_annual",
                "employment_type","minimum_credit_score","residential_requirement",
                "minimum_credit_limit","maximum_credit_limit","airport_lounge_access",
                "domestic_lounge_visits","tag_travel","tag_cashback","tag_shopping","tag_fuel",
                "tag_premium","tag_dining","tag_airport_lounge","reward_type",
                "reward_points_per_amount","reward_point_value","cashback_available",
                "cashback_rate","foreign_currency_markup","created_at","updated_at",
            ], "Credit Card Products")

            # 2. Loan Products
            push_table("loan_products", LOAN_PRODUCTS, [
                "loan_product_id","product_code","product_name","loan_category","loan_subcategory",
                "loan_type","customer_type","secured_or_unsecured","product_status","loan_purpose",
                "minimum_loan_amount","maximum_loan_amount","minimum_tenure_months",
                "maximum_tenure_months","typical_tenure_months","interest_rate_min",
                "interest_rate_max","interest_rate_current","processing_fee_value",
                "minimum_age","maximum_age","minimum_income_annual","minimum_income_monthly",
                "minimum_credit_score","employment_type","collateral_required",
                "created_at","updated_at",
            ], "Loan Products")

            # 3. Investment Products
            push_table("investment_products", INVESTMENT_PRODUCTS, [
                "investment_product_id","product_code","product_name","product_category",
                "product_subcategory","product_type","provider","issuer","brand_name",
                "product_status","customer_type","residency_requirement","minimum_age",
                "maximum_age","minimum_income_annual","employment_type","kyc_required",
                "demat_required","risk_profile","return_type","minimum_investment",
                "maximum_investment","minimum_monthly_investment","maximum_monthly_investment",
                "indicative_return_min","indicative_return_max","guaranteed_return",
                "lock_in_period_months","tax_benefit","created_at","updated_at",
            ], "Investment Products")

            # 4. Insurance Products — push to 'insurance' (primary Supabase table)
            push_table("insurance", INSURANCE_PRODUCTS, [
                "insurance_product_id","product_code","product_name","insurance_company",
                "insurance_type","plan_type","product_status","customer_type","minimum_age",
                "maximum_age","minimum_income_monthly","minimum_income_annual","employment_type",
                "minimum_sum_insured","maximum_sum_insured","premium_frequency",
                "minimum_premium","maximum_premium","waiting_period_days","maternity_benefit",
                "critical_illness_benefit","accidental_death_benefit","tax_benefit",
                "cashless_claim_available","network_hospitals","created_at","updated_at",
            ], "Insurance Products")

            # Also push to 'insurance_products' alias if it exists
            try:
                push_table("insurance_products", INSURANCE_PRODUCTS, [
                    "insurance_product_id","product_code","product_name","insurance_company",
                    "insurance_type","plan_type","product_status","created_at","updated_at",
                ], "Insurance Products (alias)")
            except Exception:
                conn.rollback()

            # 5. Debit Card Products
            try:
                push_table("debit_card_products", DEBIT_CARD_PRODUCTS, [
                    "debit_card_product_id","product_code","card_name","card_variant",
                    "card_category","card_type","card_network","product_status",
                    "minimum_age","maximum_age","minimum_balance_required","atm_daily_limit",
                    "pos_daily_limit","online_daily_limit","international_transaction",
                    "annual_fee","created_at","updated_at",
                ], "Debit Card Products")
            except Exception:
                conn.rollback()
                print("  [WARN]  debit_card_products table may not exist — skipping")

            # 6. Merchants
            try:
                push_table("merchants", MERCHANT_ROWS, [
                    "merchant_id","merchant_name","merchant_category","mcc_code","created_at",
                ], "Merchants")
            except Exception:
                conn.rollback()
                print("  [WARN]  merchants table may not exist — skipping")

            # 7. Customers
            print(f"  Hashing passwords for {len(CUSTOMERS)} customers...")
            cust_rows_db = []
            for cust in CUSTOMERS:
                pw = cust["customer_id"]
                if HAS_BCRYPT:
                    import bcrypt
                    pw_hash = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
                else:
                    pw_hash = pw
                row = dict(cust)
                row["password_hash"] = pw_hash
                cust_rows_db.append(row)

            cust_cols = [
                "customer_id","customer_number","first_name","middle_name","last_name",
                "date_of_birth","age","gender","marital_status","nationality",
                "residential_status","occupation_type","occupation","employer_name",
                "employment_type","annual_income","income_range","education_level",
                "address_line_1","address_line_2","city","state","country","pincode",
                "mobile_number","email","customer_since","customer_segment_type",
                "customer_status","kyc_status","kyc_last_updated","risk_profile",
                "credit_score","branch_id","relationship_manager_id","preferred_language",
                "preferred_channel","marketing_consent","password_hash",
            ]
            push_table("customers", cust_rows_db, cust_cols, "Customers")

            # 8. Customer Accounts
            push_table("customer_accounts", ALL_ACCOUNTS, [
                "account_id","customer_id","account_type","account_product_name",
                "account_number_masked","account_status","opening_date","currency",
                "average_monthly_balance","branch_id",
            ], "Customer Accounts")

            # 9. Customer Debit Cards
            push_table("customer_debit_cards", ALL_DEBIT_CARDS, [
                "customer_debit_card_id","customer_id","account_id","debit_card_product_id",
                "card_name","card_number_masked","card_network","card_status","issue_date",
                "expiry_date","international_enabled","daily_atm_limit","daily_pos_limit",
            ], "Customer Debit Cards")

            # 10. Customer Credit Cards
            push_table("customer_credit_cards", ALL_CREDIT_CARDS, [
                "customer_card_id","customer_id","credit_card_product_id","card_name",
                "card_number_masked","card_network","card_category","issue_date",
                "activation_date","expiry_date","card_status","credit_limit",
                "available_limit","current_outstanding","reward_points_balance",
                "annual_spend","international_enabled","last_payment_date",
            ], "Customer Credit Cards")

            # 11. Customer Loans
            push_table("customer_loans", ALL_LOANS, [
                "customer_loan_id","customer_id","loan_product_id","loan_product_name",
                "loan_category","loan_purpose","loan_status","disbursement_date",
                "disbursed_amount","outstanding_principal","interest_rate",
                "original_tenure_months","remaining_tenure_months","emi_amount",
                "emi_due_date","last_payment_date","collateral_provided","account_id",
            ], "Customer Loans")

            # 12. Customer Deposits
            push_table("customer_deposits", ALL_DEPOSITS, [
                "customer_deposit_id","customer_id","deposit_product_id","deposit_product_name",
                "deposit_category","deposit_status","principal_amount","interest_rate",
                "deposit_tenure_months","maturity_date","maturity_amount","start_date",
                "is_auto_renewal","account_id",
            ], "Customer Deposits")

            # 13. Customer Investments
            push_table("customer_investments", ALL_INVESTMENTS, [
                "customer_investment_id","customer_id","investment_product_id",
                "investment_product_name","investment_category","provider","investment_type",
                "investment_mode","monthly_amount","initial_investment_amount",
                "total_invested_amount","current_value","start_date","status",
            ], "Customer Investments")

            # 14. Customer Insurance
            push_table("customer_insurance", ALL_INSURANCE, [
                "customer_insurance_id","customer_id","insurance_product_id",
                "insurance_product_name","insurance_type","insurance_company",
                "sum_insured","annual_premium","premium_frequency","policy_start_date",
                "policy_end_date","policy_status","nominee_name",
            ], "Customer Insurance")

            # 15. Transactions (in chunks due to size)
            print(f"  Inserting {len(UNIQUE_TRANSACTIONS):,} transactions...")
            tx_cols = [
                "transaction_id","customer_id","account_id","card_id","transaction_date",
                "transaction_time","transaction_type","transaction_mode","amount","currency",
                "transaction_status","merchant_id","merchant_name","receiver_name",
                "receiver_identifier","mcc_code","transaction_description","reference_number",
                "channel","location_city","location_state","location_country",
                "created_at","updated_at",
            ]
            # Check if table is raw_transactions or transactions
            for tx_table in ["raw_transactions","transactions"]:
                try:
                    push_table(tx_table, UNIQUE_TRANSACTIONS, tx_cols, f"Transactions ({tx_table})")
                    break
                except Exception:
                    conn.rollback()
                    continue

            cur.close()
            conn.close()
            print("\n  [OK] Phase 8 complete — All tables pushed to Supabase\n")

        except ImportError:
            print("  [ERROR] psycopg2 not installed. Run: pip install psycopg2-binary")
        except Exception as exc:
            print(f"  [ERROR] Supabase push failed: {exc}")
            try:
                conn.rollback()
                conn.close()
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════
# SECTION 9 — FINAL SUMMARY
# ═══════════════════════════════════════════════════════════════

print(f"\n{'='*60}")
print("GENERATION SUMMARY")
print(f"{'='*60}")
print(f"  Customers:            {len(CUSTOMERS):,}")
print(f"  Accounts:             {len(ALL_ACCOUNTS):,}")
print(f"  Debit Cards:          {len(ALL_DEBIT_CARDS):,}")
print(f"  Credit Cards:         {len(ALL_CREDIT_CARDS):,}  ({len([c for c in CUSTOMERS if CUST_CARDS.get(c['customer_id'])])} customers)")
print(f"  Active Loans:         {len(ALL_LOANS):,}")
print(f"  Fixed/Rec Deposits:   {len(ALL_DEPOSITS):,}")
print(f"  Investment Records:   {len(ALL_INVESTMENTS):,}  (SIP:{sum(1 for i in ALL_INVESTMENTS if i['investment_category']=='SIP')}, MF:{sum(1 for i in ALL_INVESTMENTS if i['investment_category']=='Mutual Fund')}, Eq:{sum(1 for i in ALL_INVESTMENTS if i['investment_category']=='Stock / Equity')}, WM:{sum(1 for i in ALL_INVESTMENTS if i['investment_category']=='Wealth Management')})")
print(f"  Insurance Policies:   {len(ALL_INSURANCE):,}  (Life:{sum(1 for i in ALL_INSURANCE if i['insurance_type']=='Life')}, Health:{sum(1 for i in ALL_INSURANCE if i['insurance_type']=='Health')}, Motor:{sum(1 for i in ALL_INSURANCE if i['insurance_type']=='Motor')})")
print(f"  Transactions:         {len(UNIQUE_TRANSACTIONS):,}")
print(f"  Customer 360 JSON:    {len(CUSTOMER_360):,} profiles")
print(f"\n  Occupation diversity:  {len({c['occupation'] for c in CUSTOMERS})} unique occupations")
print(f"  Income distribution:")

income_buckets = {}
for c in CUSTOMERS:
    lbl = c["income_range"]
    income_buckets[lbl] = income_buckets.get(lbl,0) + 1
for k,v in sorted(income_buckets.items(), key=lambda x: x[0]):
    print(f"    {k:<15} {v:>5}  ({v/NUM_CUSTOMERS*100:.1f}%)")

print(f"\n  Output directory: {OUTPUT_DIR}")
print(f"  Customer 360 JSON: {c360_path}")
print(f"\n{'='*60}")
print("DONE. All files generated successfully!")
if not args.csv_only:
    print("Supabase push complete.")
print(f"{'='*60}\n")
