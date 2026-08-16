import os
import sys
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Load env variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

DB_URL = os.getenv("SUPABASE_DB_URL")
if not DB_URL:
    print("Error: SUPABASE_DB_URL is not set in .env")
    print("Example format: postgresql://postgres.[project-ref]:[password]@aws-0-eu-central-1.pooler.supabase.com:6543/postgres")
    sys.exit(1)

# Fix URL for SQLAlchemy if it uses 'postgres://' instead of 'postgresql://'
if DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DB_URL)

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'Database_csvs')

tables = {
    'customers': 'customers.csv',
    'raw_transactions': 'raw_transactions.csv',
    'credit_card_products': 'credit_card_products.csv',
    'loan_products': 'loan_products.csv'
}

print("Starting migration to Supabase...")

for table_name, file_name in tables.items():
    filepath = os.path.join(DATA_DIR, file_name)
    if not os.path.exists(filepath):
        print(f"Warning: {file_name} not found. Skipping.")
        continue
        
    print(f"\nLoading {file_name} into pandas...")
    df = pd.read_csv(filepath)
    
    # Pre-process dates specifically for transactions
    if table_name == 'raw_transactions':
        df['transaction_date'] = pd.to_datetime(df['transaction_date'])
        
    print(f"Uploading {len(df)} rows to Supabase table '{table_name}'...")
    try:
        # if_exists='replace' will drop the table and recreate it with the correct schema
        df.to_sql(table_name, engine, if_exists='replace', index=False, chunksize=1000)
        print(f"Successfully migrated {table_name}!")
    except Exception as e:
        print(f"Failed to migrate {table_name}: {e}")

print("\nMigration complete! Your Supabase database is now populated.")
