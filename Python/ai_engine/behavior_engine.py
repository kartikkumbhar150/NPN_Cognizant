import pandas as pd
from datetime import timedelta

class BehaviorEngine:
    def __init__(self, transactions_df):
        self.transactions = transactions_df
        
        # Mapping generic merchant categories to analytical categories
        self.category_mapping = {
            'AIRLINES': 'Travel',
            'HOTELS': 'Travel',
            'BUS': 'Travel',
            'TRAIN': 'Travel',
            'CAB': 'Transport',
            'INVESTMENT': 'Investment',
            'SIP': 'Investment',
            'INSURANCE': 'Insurance',
            'FOOD_DELIVERY': 'Dining',
            'RESTAURANTS': 'Dining',
            'E_COMMERCE': 'Shopping',
            'SHOPPING': 'Shopping',
            'GROCERY': 'Groceries',
            'HEALTHCARE': 'Medical',
            'COLLEGE_FEES': 'Education',
            'EDUCATION': 'Education',
            'RENT': 'Rent',
            'FUEL': 'Fuel',
            'BILLS': 'Utilities',
            'UTILITIES': 'Utilities'
        }
        
    def analyze_behavior(self, customer_id):
        """Phase 2: Behaviour understanding"""
        cust_tx = self.transactions[self.transactions['customer_id'] == customer_id].copy()
        
        if cust_tx.empty:
            return {'total_spend': 0, 'categories': {}, 'category_spend': {}}
            
        # Map to high-level categories
        cust_tx['analysis_category'] = cust_tx['merchant_id'].apply(
            lambda x: 'Salary' if pd.isna(x) or x == '' else self._map_merchant_to_category(x)
        )
        
        # Debits only for spending behavior
        debits = cust_tx[cust_tx['transaction_type'] == 'Debit']
        credits = cust_tx[cust_tx['transaction_type'] == 'Credit']
        
        total_spend = debits['amount'].sum()
        
        # Spending by category
        category_spend = debits.groupby('analysis_category')['amount'].sum().to_dict()

        # Monthly income from salary credits
        salary_credits = credits[credits['transaction_description'] == 'SALARY CREDIT'].copy()
        salary_credits['ym'] = salary_credits['transaction_date'].dt.to_period('M')
        monthly_income = salary_credits.groupby('ym')['amount'].sum().to_dict()
        monthly_income = {str(k): v for k, v in monthly_income.items()}

        # Monthly spend breakdown
        debits_copy = debits.copy()
        debits_copy['ym'] = debits_copy['transaction_date'].dt.to_period('M')
        monthly_spend = debits_copy.groupby('ym')['amount'].sum().to_dict()
        monthly_spend = {str(k): v for k, v in monthly_spend.items()}

        # Transaction count per category (frequency signal)
        category_tx_counts = debits.groupby('analysis_category').size().to_dict()
        
        return {
            'total_spend':         total_spend,
            'category_spend':      category_spend,
            'monthly_income':      monthly_income,
            'monthly_spend':       monthly_spend,
            'category_tx_counts':  category_tx_counts,
        }


    def detect_events(self, customer_id):
        """Phase 3: Event detection"""
        cust_tx = self.transactions[self.transactions['customer_id'] == customer_id].copy()
        if cust_tx.empty:
            return []
            
        events = set()
        
        # Get the most recent date in the dataset to simulate "today"
        max_date = cust_tx['transaction_date'].max()
        recent_threshold = max_date - timedelta(days=30)
        
        recent_tx = cust_tx[cust_tx['transaction_date'] >= recent_threshold]
        
        for _, tx in recent_tx.iterrows():
            # Check for Flight Purchase
            if self._map_merchant_to_category(tx['merchant_id']) == 'Travel' and tx['amount'] > 2000:
                events.add('Flight/Travel Purchase')
            
            # Check for High Medical
            if self._map_merchant_to_category(tx['merchant_id']) == 'Medical' and tx['amount'] > 5000:
                events.add('Healthcare Spending')
                
            # Check for large purchase
            if tx['transaction_type'] == 'Debit' and tx['amount'] > 20000:
                events.add('Large Purchase')
                
        # Check for regular salary (at least 3 salary credits in last 6 months)
        six_months_ago = max_date - timedelta(days=180)
        salary_tx = cust_tx[(cust_tx['transaction_date'] >= six_months_ago) & (cust_tx['transaction_description'] == 'SALARY CREDIT')]
        if len(salary_tx) >= 3:
            events.add('Regular Salary Credit')
            
        return list(events)
        
    def _map_merchant_to_category(self, merchant_id):
        """Simulate merchant categorization (in reality, we'd use the MCC or merchant table)"""
        if pd.isna(merchant_id) or merchant_id == "":
            return "Other"
            
        # Using the merchant IDs generated in raw_transactions.py
        if merchant_id.startswith('MER00'): return 'Travel' # Airlines
        if merchant_id.startswith('MER01'): return 'Dining' # Food delivery/Restaurants
        if merchant_id.startswith('MER02') or merchant_id.startswith('MER03'): return 'Shopping'
        if merchant_id.startswith('MER04'): return 'Groceries'
        if merchant_id.startswith('MER05') or merchant_id.startswith('MER06') or merchant_id.startswith('MER07'): return 'Transport'
        if merchant_id.startswith('MER08'): return 'Travel' # Hotels
        if merchant_id.startswith('MER10'): return 'Fuel'
        if merchant_id.startswith('MER13'): return 'Medical'
        if merchant_id.startswith('MER15') or merchant_id.startswith('MER16'): return 'Investment'
        if merchant_id.startswith('MER17'): return 'Insurance'
        
        return 'Other'
