"""
Add email column to customers table in Supabase and populate with realistic emails.
Run: python scripts/add_email_column.py
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

DB_URL = os.getenv("SUPABASE_DB_URL")
if not DB_URL:
    print("ERROR: SUPABASE_DB_URL not set in .env")
    sys.exit(1)

SQL_ADD_COLUMN = """
ALTER TABLE customers ADD COLUMN IF NOT EXISTS email TEXT;
"""

SQL_POPULATE_EMAIL = """
UPDATE customers
SET email = LOWER(
    REGEXP_REPLACE(first_name, '[^a-zA-Z]', '', 'g') || '.' ||
    REGEXP_REPLACE(last_name,  '[^a-zA-Z]', '', 'g') || 
    customer_id || '@gmail.com'
)
WHERE email IS NULL OR email = '';
"""

def main():
    print(f"Connecting to Supabase DB...")
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    cur = conn.cursor()

    print("Adding email column (if not exists)...")
    cur.execute(SQL_ADD_COLUMN)
    print("  OK Column added / already exists")

    print("Populating email addresses...")
    cur.execute(SQL_POPULATE_EMAIL)
    print("  OK Emails populated")

    # Verify
    cur.execute("SELECT COUNT(*) FROM customers WHERE email IS NOT NULL")
    count = cur.fetchone()[0]
    print(f"  OK {count} customers now have email addresses")

    cur.execute("SELECT customer_id, first_name, last_name, email FROM customers LIMIT 5")
    rows = cur.fetchall()
    print("\nSample rows:")
    for row in rows:
        print(f"  {row[0]} | {row[1]} {row[2]} | {row[3]}")

    cur.close()
    conn.close()
    print("\nDone!")

if __name__ == "__main__":
    main()
