import psycopg2
import os
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()
url = os.getenv('SUPABASE_DB_URL')
p = urlparse(url)
conn = psycopg2.connect(host=p.hostname, port=p.port, dbname=p.path.lstrip('/'), user=p.username, password=p.password, sslmode='require')
conn.autocommit = True
cur = conn.cursor()

# 1. Check if password_hash exists in customers
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='customers' AND column_name='password_hash'")
exists = cur.fetchone()
if not exists:
    cur.execute("ALTER TABLE customers ADD COLUMN password_hash TEXT")
    print('[OK] Added password_hash column to customers')
else:
    print('[SKIP] password_hash already exists')

# 2. Check which tables actually exist
for t in ['insurance_products', 'debit_card_products', 'merchants']:
    cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_name=%s", (t,))
    print(f'{t}: exists={cur.fetchone()[0] > 0}')

cur.close()
conn.close()
