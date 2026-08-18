# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8', newline='\n')
"""
push_to_supabase.py
===================
One-time script to push all CSV data to Supabase PostgreSQL.
Creates tables, inserts data in batches, and adds password_hash
to customers (default password = customer_id, bcrypt-hashed).
"""

import os
import sys
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import bcrypt
from dotenv import load_dotenv

load_dotenv()

# ─── Config ───────────────────────────────────────────────────────────────────
DB_URL = os.environ.get("SUPABASE_DB_URL")
if not DB_URL:
    sys.exit("ERROR: SUPABASE_DB_URL not set in .env")

DATA_DIR = os.path.join(os.path.dirname(__file__), "Database_csvs")
BATCH_SIZE = 500

# ─── Connect ──────────────────────────────────────────────────────────────────
print("Connecting to Supabase...")
conn = psycopg2.connect(DB_URL)
conn.autocommit = False
cur = conn.cursor()
print("Connected.\n")


# ─── Helpers ──────────────────────────────────────────────────────────────────
def clean(val):
    """Convert NaN/NaT to None for psycopg2."""
    if val is None:
        return None
    try:
        import math
        if isinstance(val, float) and math.isnan(val):
            return None
    except Exception:
        pass
    import pandas as _pd
    if _pd.isna(val):
        return None
    return val


def insert_batch(table, cols, rows):
    sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES %s ON CONFLICT DO NOTHING"
    execute_values(cur, sql, rows, page_size=BATCH_SIZE)


# ─────────────────────────────────────────────────────────────────────────────
# 1. CUSTOMERS
# ─────────────────────────────────────────────────────────────────────────────
print("Creating customers table...")
cur.execute("""
CREATE TABLE IF NOT EXISTS customers (
    customer_id          VARCHAR(20)  PRIMARY KEY,
    customer_number      VARCHAR(20),
    first_name           VARCHAR(100),
    middle_name          VARCHAR(100),
    last_name            VARCHAR(100),
    date_of_birth        DATE,
    age                  INTEGER,
    gender               VARCHAR(20),
    marital_status       VARCHAR(30),
    nationality          VARCHAR(50),
    residential_status   VARCHAR(50),
    occupation_type      VARCHAR(50),
    occupation           VARCHAR(100),
    employer_name        VARCHAR(200),
    employment_type      VARCHAR(50),
    annual_income        BIGINT,
    income_range         VARCHAR(30),
    education_level      VARCHAR(50),
    address_line_1       TEXT,
    address_line_2       TEXT,
    city                 VARCHAR(100),
    state                VARCHAR(100),
    country              VARCHAR(50),
    pincode              VARCHAR(20),
    mobile_number        VARCHAR(20),
    phone_number         VARCHAR(20),
    email                VARCHAR(200),
    customer_since       DATE,
    customer_segment_type VARCHAR(50),
    customer_status      VARCHAR(30),
    kyc_status           VARCHAR(30),
    kyc_last_updated     DATE,
    risk_profile         VARCHAR(30),
    credit_score         INTEGER,
    branch_id            VARCHAR(20),
    relationship_manager_id VARCHAR(20),
    preferred_language   VARCHAR(50),
    preferred_channel    VARCHAR(50),
    marketing_consent    VARCHAR(10),
    password_hash        VARCHAR(255)
)
""")
conn.commit()

print("Loading customers.csv...")
df = pd.read_csv(os.path.join(DATA_DIR, "customers.csv"))

# Hash passwords (default: customer_id as password)
print(f"  Hashing passwords for {len(df)} customers (this takes a moment)...")
cols = [
    "customer_id","customer_number","first_name","middle_name","last_name",
    "date_of_birth","age","gender","marital_status","nationality",
    "residential_status","occupation_type","occupation","employer_name",
    "employment_type","annual_income","income_range","education_level",
    "address_line_1","address_line_2","city","state","country","pincode",
    "mobile_number","phone_number","email","customer_since","customer_segment_type",
    "customer_status","kyc_status","kyc_last_updated","risk_profile",
    "credit_score","branch_id","relationship_manager_id","preferred_language",
    "preferred_channel","marketing_consent","password_hash"
]
rows = []
for _, row in df.iterrows():
    pw_hash = bcrypt.hashpw(row["customer_id"].encode(), bcrypt.gensalt()).decode()
    rows.append((
        clean(row.get("customer_id")),
        clean(row.get("customer_number")),
        clean(row.get("first_name")),
        clean(row.get("middle_name")),
        clean(row.get("last_name")),
        clean(row.get("date_of_birth")),
        clean(row.get("age")),
        clean(row.get("gender")),
        clean(row.get("marital_status")),
        clean(row.get("nationality")),
        clean(row.get("residential_status")),
        clean(row.get("occupation_type")),
        clean(row.get("occupation")),
        clean(row.get("employer_name")),
        clean(row.get("employment_type")),
        clean(row.get("annual_income")),
        clean(row.get("income_range")),
        clean(row.get("education_level")),
        clean(row.get("address_line_1")),
        clean(row.get("address_line_2")),
        clean(row.get("city")),
        clean(row.get("state")),
        clean(row.get("country")),
        clean(row.get("pincode")),
        clean(row.get("mobile_number")),
        clean(row.get("phone_number")),
        clean(row.get("email")),
        clean(row.get("customer_since")),
        clean(row.get("customer_segment_type")),
        clean(row.get("customer_status")),
        clean(row.get("kyc_status")),
        clean(row.get("kyc_last_updated")),
        clean(row.get("risk_profile")),
        clean(row.get("credit_score")),
        clean(row.get("branch_id")),
        clean(row.get("relationship_manager_id")),
        clean(row.get("preferred_language")),
        clean(row.get("preferred_channel")),
        clean(row.get("marketing_consent")),
        pw_hash,
    ))

insert_batch("customers", cols, rows)
conn.commit()
print(f"  [OK] Inserted {len(rows)} customers\n")


# ─────────────────────────────────────────────────────────────────────────────
# 2. TRANSACTIONS
# ─────────────────────────────────────────────────────────────────────────────
print("Creating transactions table...")
cur.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id          VARCHAR(20) PRIMARY KEY,
    customer_id             VARCHAR(20) REFERENCES customers(customer_id),
    account_id              VARCHAR(20),
    card_id                 VARCHAR(20),
    transaction_date        DATE,
    transaction_time        TIME,
    transaction_type        VARCHAR(10),
    transaction_mode        VARCHAR(30),
    amount                  DECIMAL(15,2),
    currency                VARCHAR(5),
    transaction_status      VARCHAR(20),
    merchant_id             VARCHAR(20),
    merchant_name           VARCHAR(200),
    receiver_name           VARCHAR(200),
    receiver_identifier     VARCHAR(200),
    mcc_code                DECIMAL(10,2),
    transaction_description VARCHAR(200),
    reference_number        VARCHAR(50),
    channel                 VARCHAR(50),
    location_city           VARCHAR(100),
    location_state          VARCHAR(100),
    location_country        VARCHAR(50),
    created_at              TIMESTAMP,
    updated_at              TIMESTAMP
)
""")
conn.commit()

print("Loading raw_transactions.csv...")
df_tx = pd.read_csv(os.path.join(DATA_DIR, "raw_transactions.csv"))

# Deduplicate transaction_id
df_tx = df_tx.drop_duplicates(subset=["transaction_id"])

tx_cols = [
    "transaction_id","customer_id","account_id","card_id",
    "transaction_date","transaction_time","transaction_type","transaction_mode",
    "amount","currency","transaction_status","merchant_id","merchant_name",
    "receiver_name","receiver_identifier","mcc_code","transaction_description",
    "reference_number","channel","location_city","location_state",
    "location_country","created_at","updated_at"
]

print(f"  Inserting {len(df_tx)} transactions in batches of {BATCH_SIZE}...")
for i in range(0, len(df_tx), BATCH_SIZE):
    batch = df_tx.iloc[i:i+BATCH_SIZE]
    rows = [
        tuple(clean(row.get(c)) for c in tx_cols)
        for _, row in batch.iterrows()
    ]
    insert_batch("transactions", tx_cols, rows)
    conn.commit()
    print(f"  ... {min(i+BATCH_SIZE, len(df_tx))}/{len(df_tx)}", end="\r")

print(f"\n  [OK] Inserted {len(df_tx)} transactions\n")


# ─────────────────────────────────────────────────────────────────────────────
# 3. CREDIT CARD PRODUCTS
# ─────────────────────────────────────────────────────────────────────────────
print("Creating credit_card_products table...")
cur.execute("""
CREATE TABLE IF NOT EXISTS credit_card_products (
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

print("Loading credit_card_products.csv...")
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
print(f"  [OK] Inserted {len(rows)} credit card products\n")


# ─────────────────────────────────────────────────────────────────────────────
# 4. LOAN PRODUCTS
# ─────────────────────────────────────────────────────────────────────────────
print("Creating loan_products table...")
cur.execute("""
CREATE TABLE IF NOT EXISTS loan_products (
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

print("Loading loan_products.csv...")
df_loan = pd.read_csv(os.path.join(DATA_DIR, "loan_products.csv"))
loan_cols = [c for c in [
    "loan_product_id","product_code","product_name","loan_category",
    "loan_subcategory","minimum_income_annual","minimum_credit_score",
    "interest_rate_min","interest_rate_max","processing_fee_percent","product_status"
] if c in df_loan.columns]

rows = [tuple(clean(row.get(c)) for c in loan_cols) for _, row in df_loan.iterrows()]
insert_batch("loan_products", loan_cols, rows)
conn.commit()
print(f"  [OK] Inserted {len(rows)} loan products\n")


# ─── Done ─────────────────────────────────────────────────────────────────────
cur.close()
conn.close()
print("=" * 50)
print("All data pushed to Supabase successfully!")
print("Default login: username=CUST00XXX, password=CUST00XXX")
print("=" * 50)
