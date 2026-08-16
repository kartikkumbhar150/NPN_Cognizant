"""
Segmentation Engine (v2.0)
==========================
Banking-Grade Customer Intelligence — NPN Bank AI Pipeline v2.0

Upgrades from v1:
  - Consumes standardized CustomerFeatureSet.
  - Separates Lifecycle segments (new, growing, established) from Behavioral segments.
  - Adds digital engagement and wealth segments.
"""

import logging
from typing import Any, Dict, List
import pandas as pd
import yaml
import os

from ai_engine.feature_engine import CustomerFeatureSet

logger = logging.getLogger(__name__)

# Load configuration
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config", "thresholds.yaml")
try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        CONFIG = yaml.safe_load(f)
except Exception as e:
    logger.error(f"Could not load thresholds.yaml: {e}")
    CONFIG = {}

class SegmentationEngine:
    """
    Categorizes customers based on Lifecycle and Behavior using CustomerFeatureSet.
    """

    def __init__(self):
        self.lifecycle_config = CONFIG.get("lifecycle", {
            "new_customer_days": 90,
            "growing_customer_days": 365,
            "established_customer_days": 1095,
            "high_value_income_threshold": 1500000,
        })
        
    def segment_customer(self, customer_data: Dict[str, Any], features: CustomerFeatureSet) -> List[str]:
        """
        Phase 4: Customer segmentation.
        Returns a list of assigned segments.
        Note: The signature accepts behavior_data in v1, but we'll accept features in v2.
        For backward compatibility, if features is not CustomerFeatureSet, we fall back.
        """
        if not isinstance(features, CustomerFeatureSet):
            return self._segment_customer_v1(customer_data, features)

        assigned_segments = []
        
        # Demographics
        age = features.profile.get('age', 30)
        income = features.profile.get('annual_income', 0) or (features.monthly_income_avg * 12)
        emp_type = features.profile.get('employment_type', '')
        marital_status = features.profile.get('marital_status', 'Single')
        
        # Windows
        w90 = features.windows.get(90)
        w365 = features.windows.get(365)
        total_spend_90 = w90.total_spend if w90 else 0
        total_spend_365 = w365.total_spend if w365 else 0
        
        # Lifecycle Segments
        if features.tenure_days <= self.lifecycle_config.get("new_customer_days", 90):
            assigned_segments.append('New Customer')
        elif features.tenure_days <= self.lifecycle_config.get("growing_customer_days", 365):
            assigned_segments.append('Growing Customer')
        else:
            assigned_segments.append('Established Customer')
            
        # Value Segments
        if income >= self.lifecycle_config.get("high_value_income_threshold", 1500000) or total_spend_365 > 1000000:
            assigned_segments.append('High-Value Customer')
        elif income > 500000:
            assigned_segments.append('Mass Affluent Customer')

        # Behavioral Segments
        if w90:
            travel_spend = w90.category_spend.get('Travel', 0)
            if travel_spend > 25000 or (total_spend_90 > 0 and travel_spend / total_spend_90 > 0.15):
                assigned_segments.append('Frequent Traveller')
                
            dining_shopping_spend = w90.category_spend.get('Dining', 0) + w90.category_spend.get('Shopping', 0)
            if age < 35 and dining_shopping_spend > 15000:
                assigned_segments.append('Young Digital Spender')
                
            if w90.digital_ratio > 0.8:
                assigned_segments.append('High Digital Engagement')
                
        # Prospect Segments
        invest_spend_365 = w365.category_spend.get('Investment', 0) if w365 else 0
        if income > 800000 and not features.has_investments:
            assigned_segments.append('Investment Prospect')
            
        # Demographic Segments
        if emp_type in ['Business', 'Self-employed']:
            assigned_segments.append('Business Customer')
            
        if marital_status == 'Married' and age > 30:
            assigned_segments.append('Family-oriented Customer')

        # Holdings-aware Segments (v3.0)
        if features.has_investments:
            assigned_segments.append('Existing Investor')

        active_loans = [l for l in features.holdings.get("loans", []) if str(l.get("loan_status", "")).lower() == "active"]
        if active_loans:
            assigned_segments.append('Loan Customer')

        foir = features.total_emi_monthly / (features.monthly_income_avg or 1)
        if foir >= 0.50 and features.monthly_income_avg > 0:
            assigned_segments.append('Over-Leveraged Customer')
        elif features.total_outstanding_debt == 0 and len(active_loans) == 0:
            assigned_segments.append('Debt-Free Customer')

        if income >= 600000 and not features.has_insurance:
            assigned_segments.append('Insurance Gap Prospect')

        if not assigned_segments:
            assigned_segments.append('Standard Customer')
            
        return list(set(assigned_segments))

    def _segment_customer_v1(self, customer_data: Dict[str, Any], behavior_data: Dict[str, Any]) -> List[str]:
        """Fallback to v1 segmentation logic if features object is not provided."""
        assigned_segments = []
        
        age = customer_data.get('age', 30)
        income = customer_data.get('annual_income', 0)
        emp_type = customer_data.get('employment_type', '')
        marital_status = customer_data.get('marital_status', 'Single')
        
        total_spend = behavior_data.get('total_spend', 0)
        categories = behavior_data.get('category_spend', {})
        
        travel_spend = categories.get('Travel', 0)
        investment_spend = categories.get('Investment', 0)
        dining_shopping_spend = categories.get('Dining', 0) + categories.get('Shopping', 0)
        medical_spend = categories.get('Medical', 0)
        
        if travel_spend > 50000 or (total_spend > 0 and travel_spend / total_spend > 0.15):
            assigned_segments.append('Frequent Traveller')
        if income >= 2000000 or total_spend > 1000000:
            assigned_segments.append('High-Value Customer')
        if age < 35 and dining_shopping_spend > 30000:
            assigned_segments.append('Young Digital Spender')
        if income > 800000 and investment_spend < 10000:
            assigned_segments.append('Investment Prospect')
        if income >= 500000 and age >= 25 and medical_spend > 20000:
            assigned_segments.append('Loan Prospect')
        if emp_type in ['Business', 'Self-employed']:
            assigned_segments.append('Business Customer')
        if marital_status == 'Married' and age > 30:
            assigned_segments.append('Family-oriented Customer')
            
        if not assigned_segments:
            assigned_segments.append('Standard Customer')
            
        return assigned_segments
