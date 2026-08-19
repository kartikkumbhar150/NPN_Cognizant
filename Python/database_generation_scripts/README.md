# Database Generation Scripts

## Purpose

This directory contains Python scripts that create synthetic banking customers, transactions, products, and holding datasets for local development and demonstrations.

## Contents

| Item | Description |
| --- | --- |
| `customer.py` | Customer data generation. |
| `raw_transactions.py` | Transaction data generation. |
| `credit_card_data.py` | Credit card catalogue or holding generation. |
| `debit_card_data.py` | Debit card data generation. |
| `insurance_data.py` | Insurance data generation. |
| `loan_products.py` | Loan product catalogue generation. |
| `investments.py` | Investment product or holding generation. |
| `generated_customer_360/` | Generated outputs from the customer 360 generation flow. |

## Operational Notes

Keep generation logic aligned with the schemas expected by `Python/ai_engine/data_loader.py` and backend endpoints.
