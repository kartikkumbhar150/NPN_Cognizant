import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()
db = os.getenv('SUPABASE_DB_URL').replace('postgres://', 'postgresql://')
e = create_engine(db)
with e.connect() as conn:
    result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name"))
    tables = [row[0] for row in result]
    print("Tables in Supabase:")
    for t in tables:
        print(f"  - {t}")
