"""
db.py — load customer transactions from Supabase
"""
import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()


def get_customer_data(customer_id: str) -> dict:
    """Fetch customer profile and transactions from Supabase."""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Customer profile
    cur.execute(
        "SELECT * FROM customers WHERE customer_id = %s",
        (customer_id,)
    )
    customer = cur.fetchone()
    if not customer:
        cur.close()
        conn.close()
        return {}

    # All transactions
    cur.execute(
        """SELECT transaction_id, transaction_date, transaction_type, transaction_mode,
                  amount, currency, merchant_id, merchant_name, transaction_description,
                  transaction_status, channel, location_city
           FROM transactions
           WHERE customer_id = %s
           ORDER BY transaction_date DESC""",
        (customer_id,)
    )
    transactions = cur.fetchall()

    # Credit card products
    cur.execute("SELECT * FROM credit_card_products WHERE product_status = 'Active'")
    credit_cards = cur.fetchall()

    # Loan products
    cur.execute("SELECT * FROM loan_products WHERE product_status = 'Active'")
    loans = cur.fetchall()

    cur.close()
    conn.close()

    return {
        "customer":     dict(customer),
        "transactions": [dict(t) for t in transactions],
        "credit_cards": [dict(c) for c in credit_cards],
        "loans":        [dict(l) for l in loans],
    }
