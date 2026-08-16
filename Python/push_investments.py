# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8', newline='\n')

import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.environ.get("SUPABASE_DB_URL")
DATA_DIR = os.path.join(os.path.dirname(__file__), "Database_csvs")

print("Connecting to Supabase...")
engine = create_engine(DB_URL)

print("Loading investment_products.csv...")
df = pd.read_csv(os.path.join(DATA_DIR, "investment_products.csv"))

print("Pushing investment_products to Supabase...")
df.to_sql("investment_products", engine, if_exists="replace", index=False)

print("\n[DONE] Investment Products pushed to Supabase!")
