# Synthetic Banking Dataset

This directory contains the synthetic CSV data generated for the AI-Powered Personalized Banking Marketing System.

## Files Generated So Far

1. **`customers.csv`**
   - The customer master dataset. Contains demographic, employment, and income information for ~300 synthetic customers.

2. **`raw_transactions.csv`**
   - The transaction history. Contains ~10,000 realistic synthetic transactions across various merchants, categories, and channels.

3. **`credit_card_products.csv`**
   - The master product catalogue for credit cards offered by the bank, detailing fees, eligibility, and reward structures.

4. **`loan_products.csv`**
   - The master product catalogue for loan products offered by the bank, detailing interest rates, eligibility, and loan terms.

5. **`customer_accounts.csv`** (To be generated)
   - Maps customers to their bank accounts (e.g. Savings, Current). Links with `customers.csv`.

6. **`customer_credit_cards.csv`** (To be generated)
   - Maps customers to the credit cards they own. Links `customers.csv` and `credit_card_products.csv`.

7. **`customer_loans.csv`** (To be generated)
   - Maps customers to the loans they have taken. Links `customers.csv` and `loan_products.csv`.

8. **`merchants.csv`** (To be generated)
   - The master list of merchants used in the transactions. Links with `raw_transactions.csv`.

**Note:** This data is entirely synthetic and generated for research/prototype purposes. Do not use real customer financial information in this dataset.
