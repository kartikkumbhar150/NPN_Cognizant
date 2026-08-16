import pandas as pd
import os
import sys
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Load env
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

DB_URL = os.getenv("SUPABASE_DB_URL")
if not DB_URL:
    print("WARNING: SUPABASE_DB_URL is not set. Falling back to local CSVs.")
    DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'Database_csvs')
    engine = None
else:
    # Fix URL for SQLAlchemy if it uses 'postgres://' instead of 'postgresql://'
    if DB_URL.startswith("postgres://"):
        DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(DB_URL)

def _load_table(table_name, csv_fallback):
    """Helper to load from Supabase with a fallback to local CSV."""
    if engine:
        try:
            return pd.read_sql_table(table_name, engine)
        except Exception as e:
            print(f"Failed to load {table_name} from Supabase: {e}. Falling back to CSV.")
    
    # Fallback to CSV
    filepath = os.path.join(DATA_DIR, csv_fallback)
    return pd.read_csv(filepath)

def load_customers():
    """Loads the customer dataset from Supabase."""
    return _load_table('customers', 'customers.csv')

def load_transactions():
    """Loads the raw transactions dataset from Supabase."""
    df = _load_table('raw_transactions', 'raw_transactions.csv')
    # Convert dates regardless of source
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    return df

def load_credit_cards():
    """Loads the credit card products catalogue from Supabase."""
    return _load_table('credit_card_products', 'credit_card_products.csv')

def load_loan_products():
    """Loads the loan products catalogue from Supabase."""
    return _load_table('loan_products', 'loan_products.csv')

def load_investment_products():
    """Loads the investment products catalogue from Supabase."""
    return _load_table('investment_products', 'investment_products.csv')

def load_insurance_products():
    """Loads the insurance product catalogue from Supabase."""
    return _load_table('insurance', 'insurance.csv')

def load_customer_holdings():
    """Loads all Customer 360 holdings datasets."""
    return {
        "accounts": _load_table('customer_accounts', 'generated_customer_360/customer_accounts.csv'),
        "deposits": _load_table('customer_deposits', 'generated_customer_360/customer_deposits.csv'),
        "credit_cards": _load_table('customer_credit_cards', 'generated_customer_360/customer_credit_cards.csv'),
        "debit_cards": _load_table('customer_debit_cards', 'generated_customer_360/customer_debit_cards.csv'),
        "investments": _load_table('customer_investments', 'generated_customer_360/customer_investments.csv'),
        "loans": _load_table('customer_loans', 'generated_customer_360/customer_loans.csv'),
        "insurance": _load_table('customer_insurance', 'generated_customer_360/customer_insurance.csv'),
    }
