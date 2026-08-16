# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8', newline='\n')

import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.environ.get("SUPABASE_DB_URL")
# Convert postgres:// to postgresql:// for SQLAlchemy
if DB_URL and DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

DATA_DIR = os.path.join(os.path.dirname(__file__), "database_generation_scripts", "generated_customer_360")

print("Connecting to Supabase...")
engine = create_engine(DB_URL)

files_to_push = [
    ("customers.csv", "customers"),
    ("customer_accounts.csv", "customer_accounts"),
    ("customer_deposits.csv", "customer_deposits"),
    ("customer_credit_cards.csv", "customer_credit_cards"),
    ("customer_debit_cards.csv", "customer_debit_cards"),
    ("customer_investments.csv", "customer_investments"),
    ("customer_loans.csv", "customer_loans"),
    ("customer_insurance.csv", "customer_insurance"),
]

for filename, table_name in files_to_push:
    filepath = os.path.join(DATA_DIR, filename)
    if os.path.exists(filepath):
        print(f"Loading {filename}...")
        df = pd.read_csv(filepath)
        print(f"Pushing {table_name} to Supabase ({len(df)} rows)...")
        df.to_sql(table_name, engine, if_exists="replace", index=False)
    else:
        print(f"File not found: {filepath}")

print("\n[DONE] Customer 360 datasets pushed to Supabase!")
