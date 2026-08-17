"""
Targeted schema fix: Only add missing columns to tables.
Does NOT re-push data — that's handled by generate_database.py.
After running this, re-run: python generate_database.py --no-hash
"""
import os
import csv
import psycopg2
from psycopg2.extras import execute_values
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

RAW_URL = os.getenv("SUPABASE_DB_URL", "")
parsed  = urlparse(RAW_URL)
CONN    = {
    "host": parsed.hostname, "port": parsed.port or 5432,
    "dbname": parsed.path.lstrip("/"),
    "user": parsed.username, "password": parsed.password,
    "sslmode": "require", "connect_timeout": 30,
}

CSV_DIR = os.path.join(os.path.dirname(__file__), "Database_csvs")

# All tables + their CSVs (used only to read expected headers)
TABLES = [
    ("insurance",               "insurance.csv"),
    ("investment_products",     "investment_products.csv"),
    ("customers",               "customers.csv"),
    ("customer_accounts",       "generated_customer_360/customer_accounts.csv"),
    ("customer_debit_cards",    "generated_customer_360/customer_debit_cards.csv"),
    ("customer_credit_cards",   "generated_customer_360/customer_credit_cards.csv"),
    ("customer_loans",          "generated_customer_360/customer_loans.csv"),
    ("customer_deposits",       "generated_customer_360/customer_deposits.csv"),
    ("customer_investments",    "generated_customer_360/customer_investments.csv"),
    ("customer_insurance",      "generated_customer_360/customer_insurance.csv"),
    ("raw_transactions",        "raw_transactions.csv"),
]

NUMERIC_COLS = {
    "age","credit_score","annual_income","monthly_income",
    "minimum_age","maximum_age","minimum_income_monthly","minimum_income_annual",
    "minimum_sum_insured","maximum_sum_insured","minimum_premium","maximum_premium",
    "waiting_period_days","network_hospitals","lock_in_period_months",
    "minimum_investment","maximum_investment","minimum_monthly_investment",
    "maximum_monthly_investment","indicative_return_min","indicative_return_max",
    "credit_limit","available_limit","current_outstanding","reward_points_balance",
    "annual_spend","disbursed_amount","outstanding_principal","interest_rate",
    "original_tenure_months","remaining_tenure_months","emi_amount","emi_due_date",
    "principal_amount","interest_rate_pa","tenure_months","maturity_amount",
    "monthly_amount","current_value","total_invested","returns_pct",
    "sum_insured","premium_amount","amount","balance_after",
    "average_monthly_balance","daily_atm_limit","daily_pos_limit",
}

def get_sql_type(col):
    if col in NUMERIC_COLS:
        return "NUMERIC"
    return "TEXT"

def coerce(val, col):
    s = str(val).strip() if val is not None else ""
    if not s or s.lower() in ("nan","none","null"):
        return None
    if col in NUMERIC_COLS:
        try:
            f = float(s.replace(",",""))
            return int(f) if f == int(f) else f
        except:
            return None
    return s

conn = psycopg2.connect(**CONN)
conn.autocommit = False
cur  = conn.cursor()

print("=" * 65)
print("Schema Fix — Adding missing columns to all tables")
print("(Data push skipped — run generate_database.py after this)")
print("=" * 65)

total_added = 0
errors = []

for table, csv_rel in TABLES:
    csv_path = os.path.join(CSV_DIR, csv_rel)
    if not os.path.exists(csv_path):
        print(f"\n  [SKIP]  {table}: CSV not found")
        continue

    # Just read headers — don't load all rows
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader  = csv.DictReader(f)
        headers = list(reader.fieldnames)
        # Read just a few rows to verify headers
        rows = [next(reader, None)]
    rows = [r for r in rows if r]

    # Check table exists
    cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_name=%s", (table,))
    if cur.fetchone()[0] == 0:
        print(f"\n  [SKIP]  {table}: does not exist in Supabase")
        continue

    # Get current columns
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name=%s", (table,))
    db_cols = {r[0] for r in cur.fetchall()}

    missing = [c for c in headers if c not in db_cols]
    print(f"\n  {table}: {len(db_cols)} existing | {len(missing)} missing")

    if missing:
        for col in missing:
            sql_type = get_sql_type(col)
            try:
                cur.execute(f'ALTER TABLE "{table}" ADD COLUMN "{col}" {sql_type}')
                conn.commit()
                print(f"    [OK]  ADD COLUMN {col} ({sql_type})")
                total_added += 1
            except Exception as e:
                conn.rollback()
                msg = str(e).split("\n")[0]
                print(f"    [ERR] {col}: {msg}")
                errors.append((table, col, msg))
    else:
        print(f"    [OK]  All columns present")

cur.close()
conn.close()

print()
print("=" * 65)
print(f"DONE — {total_added} columns added")
if errors:
    print(f"Errors: {len(errors)}")
    for t, c, m in errors:
        print(f"  {t}.{c}: {m}")
print()
print("Next step: python generate_database.py --no-hash")
print("=" * 65)
