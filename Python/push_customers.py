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

CSV_PATH = os.path.join(os.path.dirname(__file__), "Database_csvs", "customers.csv")
TABLE = "customers"

NUMERIC_COLS = {
    "age", "credit_score", "annual_income", "monthly_income",
    "minimum_age", "maximum_age", "minimum_income_monthly", "minimum_income_annual",
}

def coerce(val, col):
    s = str(val).strip() if val is not None else ""
    if not s or s.lower() in ("nan", "none", "null"):
        return None
    if col in NUMERIC_COLS:
        try:
            f = float(s.replace(",", ""))
            return int(f) if f == int(f) else f
        except:
            return None
    return s

print(f"Pushing {TABLE} to Supabase with proper coercion...")

conn = psycopg2.connect(**CONN)
conn.autocommit = False
cur = conn.cursor()

try:
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = list(reader.fieldnames)
        rows = list(reader)

    # Make sure we only insert columns that exist in Supabase
    cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='{TABLE}'")
    db_cols = {r[0] for r in cur.fetchall()}
    available = [c for c in headers if c in db_cols]

    print(f"Read {len(rows)} rows from CSV.")
    print(f"Using {len(available)} available columns.")

    cur.execute(f'DELETE FROM "{TABLE}"')
    conn.commit()

    total = 0
    batch = 500
    for i in range(0, len(rows), batch):
        chunk = rows[i:i+batch]
        data = [tuple(coerce(r.get(c), c) for c in available) for r in chunk]
        sql = f'INSERT INTO "{TABLE}" ({", ".join(available)}) VALUES %s'
        execute_values(cur, sql, data, page_size=batch)
        conn.commit()
        total += len(chunk)
    
    print(f"[OK] Successfully pushed {total} rows to {TABLE}")
except Exception as e:
    conn.rollback()
    print(f"[ERROR] Push failed: {str(e)}")
finally:
    cur.close()
    conn.close()
