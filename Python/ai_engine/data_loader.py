import pandas as pd
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'Database_csvs')

def load_customers():
    """Loads the customer dataset."""
    filepath = os.path.join(DATA_DIR, 'customers.csv')
    return pd.read_csv(filepath)

def load_transactions():
    """Loads the raw transactions dataset."""
    filepath = os.path.join(DATA_DIR, 'raw_transactions.csv')
    df = pd.read_csv(filepath)
    # Convert dates
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    return df

def load_credit_cards():
    """Loads the credit card products catalogue."""
    filepath = os.path.join(DATA_DIR, 'credit_card_products.csv')
    return pd.read_csv(filepath)

def load_loan_products():
    """Loads the loan products catalogue."""
    filepath = os.path.join(DATA_DIR, 'loan_products.csv')
    return pd.read_csv(filepath)
