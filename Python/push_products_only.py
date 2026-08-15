# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8', newline='\n')
"""
push_products_only.py — push credit_card_products and loan_products only.
Run this after push_to_supabase.py has already pushed customers and transactions.
"""
import os
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
import math

load_dotenv()

DB_URL = os.environ.get("SUPABASE_DB_URL")
DATA_DIR = os.path.join(os.path.dirname(__file__), "Database_csvs")

conn = psycopg2.connect(DB_URL)
conn.autocommit = False
cur = conn.cursor()
print("Connected.")

def clean(val):
    if val is None:
        return None
    try:
        if isinstance(val, float) and math.isnan(val):
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

def insert_batch(table, cols, rows):
    sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES %s ON CONFLICT DO NOTHING"
    execute_values(cur, sql, rows, page_size=500)

# ── Credit Card Products ──────────────────────────────────────────────────────
print("Dropping and recreating credit_card_products table...")
cur.execute("DROP TABLE IF EXISTS credit_card_products CASCADE")
cur.execute("""
CREATE TABLE credit_card_products (
    credit_card_product_id  VARCHAR(20) PRIMARY KEY,
    product_code            VARCHAR(50),
    card_name               VARCHAR(200),
    card_type               VARCHAR(50),
    card_network            VARCHAR(30),
    annual_fee              DECIMAL(10,2),
    joining_fee             DECIMAL(10,2),
    minimum_income_annual   BIGINT,
    minimum_credit_score    INTEGER,
    minimum_credit_limit    BIGINT,
    maximum_credit_limit    BIGINT,
    interest_rate_annual    DECIMAL(5,2),
    cashback_rate           DECIMAL(5,2),
    reward_points_per_amount DECIMAL(10,4),
    tag_travel              INTEGER,
    tag_cashback            INTEGER,
    tag_shopping            INTEGER,
    tag_fuel                INTEGER,
    tag_premium             INTEGER,
    tag_dining              INTEGER,
    tag_airport_lounge      INTEGER,
    airport_lounge_access   BOOLEAN,
    domestic_lounge_visits  INTEGER,
    product_status          VARCHAR(20)
)
""")
conn.commit()

df_cc = pd.read_csv(os.path.join(DATA_DIR, "credit_card_products.csv"))
cc_cols = [c for c in [
    "credit_card_product_id","product_code","card_name","card_type",
    "card_network","annual_fee","joining_fee","minimum_income_annual",
    "minimum_credit_score","minimum_credit_limit","maximum_credit_limit",
    "interest_rate_annual","cashback_rate","reward_points_per_amount",
    "tag_travel","tag_cashback","tag_shopping","tag_fuel","tag_premium",
    "tag_dining","tag_airport_lounge","airport_lounge_access",
    "domestic_lounge_visits","product_status"
] if c in df_cc.columns]

rows = [tuple(clean(row.get(c)) for c in cc_cols) for _, row in df_cc.iterrows()]
insert_batch("credit_card_products", cc_cols, rows)
conn.commit()
print(f"  [OK] Inserted {len(rows)} credit card products")

# ── Loan Products ─────────────────────────────────────────────────────────────
print("Dropping and recreating loan_products table...")
cur.execute("DROP TABLE IF EXISTS loan_products CASCADE")
cur.execute("""
CREATE TABLE loan_products (
    loan_product_id         VARCHAR(20) PRIMARY KEY,
    product_code            VARCHAR(50),
    product_name            VARCHAR(200),
    loan_category           VARCHAR(50),
    loan_subcategory        VARCHAR(100),
    minimum_income_annual   BIGINT,
    minimum_credit_score    INTEGER,
    interest_rate_min       DECIMAL(5,2),
    interest_rate_max       DECIMAL(5,2),
    processing_fee_percent  DECIMAL(5,2),
    product_status          VARCHAR(20)
)
""")
conn.commit()

df_loan = pd.read_csv(os.path.join(DATA_DIR, "loan_products.csv"))
loan_cols = [c for c in [
    "loan_product_id","product_code","product_name","loan_category",
    "loan_subcategory","minimum_income_annual","minimum_credit_score",
    "interest_rate_min","interest_rate_max","processing_fee_percent","product_status"
] if c in df_loan.columns]

rows = [tuple(clean(row.get(c)) for c in loan_cols) for _, row in df_loan.iterrows()]
insert_batch("loan_products", loan_cols, rows)
conn.commit()
print(f"  [OK] Inserted {len(rows)} loan products")

cur.close()
conn.close()
print("\n[DONE] Products pushed to Supabase!")
