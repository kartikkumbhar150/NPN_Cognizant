# Database CSV Assets

## Purpose

This directory contains local CSV datasets used for product catalogues, customers, merchants, transactions, and generated customer 360 records.

## Contents

| Item | Description |
| --- | --- |
| `customers.csv` | Base customer records. |
| `raw_transactions.csv` | Transaction-level activity used for feature generation. |
| `merchants.csv` | Merchant reference data. |
| `*_products.csv` | Product catalogues for credit cards, debit cards, loans, insurance, and investments. |
| `generated_customer_360/` | Precomputed customer 360 extracts by product area. |
| `insurance.csv and debitcard.csv` | Legacy or supplemental product and holding data. |

## Operational Notes

Treat these files as development data. If schema changes are made here, update loaders, generation scripts, and tests together.
