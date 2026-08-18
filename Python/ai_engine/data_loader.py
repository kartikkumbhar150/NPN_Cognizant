import pandas as pd
import os
import sys
import json
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Load env
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

DB_URL = os.getenv("SUPABASE_DB_URL")
if not DB_URL:
    print("WARNING: SUPABASE_DB_URL is not set. Falling back to local CSVs.")
    engine = None
else:
    # Fix URL for SQLAlchemy if it uses 'postgres://' instead of 'postgresql://'
    if DB_URL.startswith("postgres://"):
        DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(DB_URL)

DATA_DIR    = os.path.join(os.path.dirname(__file__), '..', 'Database_csvs')
HOLDINGS_DIR = os.path.join(DATA_DIR, 'generated_customer_360')


def _load_table(table_name):
    """Helper to load exclusively from Supabase."""
    if not engine:
        raise ValueError("SUPABASE_DB_URL is not set. Cannot fetch from Supabase.")
    try:
        return pd.read_sql_table(table_name, engine)
    except Exception as e:
        print(f"Warning: Failed to load {table_name} from Supabase: {e}")
        return pd.DataFrame()


def load_customers():
    """Loads the customer dataset from Supabase."""
    return _load_table('customers')


def load_transactions():
    """Loads the raw transactions dataset from Supabase."""
    df = _load_table('raw_transactions')
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    return df


def load_credit_cards():
    """Loads the credit card products catalogue from Supabase."""
    return _load_table('credit_card_products')


def load_loan_products():
    """Loads the loan products catalogue from Supabase."""
    return _load_table('loan_products')


def load_investment_products():
    """Loads the investment products catalogue from Supabase."""
    return _load_table('investment_products')


def load_insurance_products():
    """Loads the insurance product catalogue from Supabase."""
    for table in ['insurance_products', 'insurance']:
        df = _load_table(table)
        if not df.empty:
            return df
    return pd.DataFrame()


def load_customer_holdings():
    """Loads all Customer 360 holdings datasets."""
    return {
        "accounts":     _load_table('customer_accounts'),
        "deposits":     _load_table('customer_deposits'),
        "credit_cards": _load_table('customer_credit_cards'),
        "debit_cards":  _load_table('customer_debit_cards'),
        "investments":  _load_table('customer_investments'),
        "loans":        _load_table('customer_loans'),
        "insurance":    _load_table('customer_insurance'),
    }


def load_customer_360_json() -> dict:
    """
    Load the prebuilt Customer 360 JSON file.
    Returns a dict keyed by customer_id with the full profile + holdings breakdown.
    Falls back to empty dict if file not found.
    """
    json_path = os.path.join(HOLDINGS_DIR, 'customer_360.json')
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return {item.get("customer_id"): item for item in data if "customer_id" in item}
                return data
        except Exception as e:
            print(f"WARNING: Could not load customer_360.json: {e}")
    return {}


def load_merchants():
    """Load the merchant master table."""
    try:
        return _load_table('merchants')
    except Exception:
        return pd.DataFrame()
