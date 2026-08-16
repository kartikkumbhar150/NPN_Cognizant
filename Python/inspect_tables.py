import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()
db = os.getenv('SUPABASE_DB_URL').replace('postgres://', 'postgresql://')
e = create_engine(db)

tables = [
    'insurance', 'credit_card_products', 'loan_products', 'investment_products',
    'customer_accounts', 'customer_credit_cards', 'customer_debit_cards',
    'customer_deposits', 'customer_insurance', 'customer_investments', 'customer_loans'
]

for t in tables:
    df = pd.read_sql_table(t, e)
    print(f"\n=== {t} ===")
    print(f"  Rows: {len(df)}")
    print(f"  Columns: {list(df.columns)}")
    print(f"  Sample: {df.head(1).to_dict('records')}")
