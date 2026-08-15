class SegmentationEngine:
    def __init__(self):
        self.segments = [
            'Frequent Traveller',
            'High-Value Customer',
            'Young Digital Spender',
            'Investment Prospect',
            'Loan Prospect',
            'Premium Customer',
            'Business Customer',
            'Family-oriented Customer'
        ]
        
    def segment_customer(self, customer_data, behavior_data):
        """Phase 4: Customer segmentation (Heuristics for Prototype)"""
        assigned_segments = []
        
        # Demographics
        age = customer_data.get('age', 30)
        income = customer_data.get('annual_income', 0)
        emp_type = customer_data.get('employment_type', '')
        marital_status = customer_data.get('marital_status', 'Single')
        
        # Behavior
        total_spend = behavior_data.get('total_spend', 0)
        categories = behavior_data.get('category_spend', {})
        
        travel_spend = categories.get('Travel', 0)
        investment_spend = categories.get('Investment', 0)
        dining_shopping_spend = categories.get('Dining', 0) + categories.get('Shopping', 0)
        medical_spend = categories.get('Medical', 0)
        
        # Frequent Traveller
        if travel_spend > 50000 or (total_spend > 0 and travel_spend / total_spend > 0.15):
            assigned_segments.append('Frequent Traveller')
            
        # High-Value Customer
        if income >= 2000000 or total_spend > 1000000:
            assigned_segments.append('High-Value Customer')
            
        # Young Digital Spender
        if age < 35 and dining_shopping_spend > 30000:
            assigned_segments.append('Young Digital Spender')
            
        # Investment Prospect
        if income > 800000 and investment_spend < 10000:
            assigned_segments.append('Investment Prospect')
            
        # Loan Prospect
        if income >= 500000 and age >= 25 and medical_spend > 20000:
            assigned_segments.append('Loan Prospect')
            
        # Business Customer
        if emp_type in ['Business', 'Self-employed']:
            assigned_segments.append('Business Customer')
            
        # Family-oriented Customer
        if marital_status == 'Married' and age > 30:
            assigned_segments.append('Family-oriented Customer')
            
        if not assigned_segments:
            assigned_segments.append('Standard Customer')
            
        return assigned_segments
