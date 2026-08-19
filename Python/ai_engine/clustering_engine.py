"""
Clustering Engine
=================
NPN Bank AI Pipeline v3.0

K-Means clustering of customers on:
  - Age (normalized)
  - Occupation type (one-hot encoded)
  - Annual Income (log-scaled)
  - Monthly Spend avg — 90-day window (log-scaled)

Produces 8 human-readable persona clusters.
Runs a batch fit on the full customer population, then
assigns labels to individual customers at inference time.
"""

from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ── Cluster persona definitions ───────────────────────────────────────────────
CLUSTER_PERSONAS: Dict[int, Dict[str, Any]] = {
    0: {
        "label": "Young Salaried Spender",
        "description": "Age <30, salaried, moderate income, high lifestyle spend",
        "nbo_boost": {"Credit Card": 0.08, "Travel Credit Card": 0.06, "Personal Loan": 0.04},
        "message_tone": "energetic, FOMO-driven, emoji-friendly, short",
        "color": "#EC4899",
    },
    1: {
        "label": "Ambitious Professional",
        "description": "Age 28–40, high income, high digital engagement",
        "nbo_boost": {"Travel Credit Card": 0.10, "SIP / Mutual Fund": 0.08, "Premium Account": 0.06},
        "message_tone": "achievement-oriented, congratulatory, ROI-focused",
        "color": "#7C3AED",
    },
    2: {
        "label": "Established Family",
        "description": "Age 35–50, married, stable income, EMI-heavy",
        "nbo_boost": {"Home Loan": 0.10, "Life Insurance": 0.08, "Health Insurance": 0.06},
        "message_tone": "warm, family-centric, security-focused, aspirational",
        "color": "#2563EB",
    },
    3: {
        "label": "Business Owner",
        "description": "Self-employed/business, high income variance, irregular cash flow",
        "nbo_boost": {"Business Loan": 0.10, "Premium Account": 0.08, "Fixed Deposit": 0.06},
        "message_tone": "growth-oriented, professional, efficiency-driven",
        "color": "#D97706",
    },
    4: {
        "label": "Conservative Saver",
        "description": "Any age, low spend ratio, high surplus, risk-averse",
        "nbo_boost": {"Fixed Deposit": 0.12, "NPS": 0.08, "SIP / Mutual Fund": 0.06},
        "message_tone": "trustworthy, safe, guaranteed-returns framing, formal",
        "color": "#059669",
    },
    5: {
        "label": "Retired / Senior",
        "description": "Age 55+, pension/fixed income, low spend, wealth preservation",
        "nbo_boost": {"Fixed Deposit": 0.12, "Health Insurance": 0.10, "NPS": 0.08},
        "message_tone": "formal, respectful, branch-visit CTA, relationship-based",
        "color": "#0891B2",
    },
    6: {
        "label": "Student / Entry-Level",
        "description": "Age <25, low income, education and dining dominated spend",
        "nbo_boost": {"Education Loan": 0.12, "Credit Card": 0.08, "SIP / Mutual Fund": 0.04},
        "message_tone": "casual, supportive, future-focused, low financial jargon",
        "color": "#F59E0B",
    },
    7: {
        "label": "High Net Worth",
        "description": "Top income decile, high assets, diverse portfolio, low churn risk",
        "nbo_boost": {"Premium Account": 0.10, "SIP / Mutual Fund": 0.08, "Travel Credit Card": 0.08},
        "message_tone": "exclusive, premium, concierge-style, status-driven",
        "color": "#1E293B",
    },
}

OCCUPATION_TYPES = [
    "Salaried", "Business", "Self-employed", "Student",
    "Retired", "Homemaker", "Unemployed", "Other"
]


def _safe_log(val: float) -> float:
    """Log-scale a positive value, returning 0 for <=0."""
    try:
        v = float(val)
        return math.log1p(max(0.0, v))
    except (TypeError, ValueError):
        return 0.0


def _encode_occupation(emp_type: str) -> int:
    """Map employment type string to an integer index."""
    emp_lower = str(emp_type or "").strip().lower()
    mapping = {
        "salaried": 0, "employed": 0,
        "business": 1, "self-employed": 2, "freelancer": 2,
        "student": 3,
        "retired": 4, "pension": 4,
        "homemaker": 5, "housewife": 5,
        "unemployed": 6,
    }
    for key, val in mapping.items():
        if key in emp_lower:
            return val
    return 7  # Other


class ClusteringEngine:
    """
    Clusters customers into 8 personas based on age, occupation, income, and spend.

    Usage:
        engine = ClusteringEngine()
        engine.fit(customers_df, features_map)     # features_map: {customer_id: CustomerFeatureSet}
        label, persona = engine.assign(customer_data, features)
    """

    def __init__(self, n_clusters: int = 8) -> None:
        self.n_clusters = n_clusters
        self._kmeans = None
        self._is_fitted = False
        self._scaler_min: Optional[np.ndarray] = None
        self._scaler_range: Optional[np.ndarray] = None

    # ── Public API ─────────────────────────────────────────────────────────────

    def fit(self, customers_df: pd.DataFrame, features_map: Dict[str, Any]) -> None:
        """
        Fit K-Means on the full population.
        features_map: dict of customer_id -> CustomerFeatureSet
        """
        try:
            from sklearn.cluster import KMeans
            from sklearn.preprocessing import MinMaxScaler

            X, _ = self._build_matrix(customers_df, features_map)
            if len(X) < self.n_clusters:
                logger.warning("ClusteringEngine: Not enough customers to fit %d clusters", self.n_clusters)
                return

            scaler = MinMaxScaler()
            X_scaled = scaler.fit_transform(X)
            self._scaler_min = scaler.data_min_
            self._scaler_range = scaler.data_range_

            km = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10, max_iter=300)
            km.fit(X_scaled)
            self._kmeans = km
            self._is_fitted = True
            logger.info("ClusteringEngine: Fitted on %d customers", len(X))

        except ImportError:
            logger.error("ClusteringEngine: sklearn not installed. pip install scikit-learn")
        except Exception as exc:
            logger.error("ClusteringEngine.fit error: %s", exc, exc_info=True)

    def assign(
        self,
        customer_data: Dict[str, Any],
        features: Any,  # CustomerFeatureSet
    ) -> Dict[str, Any]:
        """
        Assign a cluster to a single customer.
        Returns {cluster_id, label, persona, nbo_boost, message_tone, color}.
        Falls back to heuristic assignment if K-Means not fitted.
        """
        if self._is_fitted and self._kmeans is not None:
            try:
                vec = self._build_vector(customer_data, features)
                vec_scaled = (vec - self._scaler_min) / (self._scaler_range + 1e-9)
                cluster_id = int(self._kmeans.predict([vec_scaled])[0])
            except Exception as exc:
                logger.warning("ClusteringEngine.assign prediction failed: %s — using heuristic", exc)
                cluster_id = self._heuristic_cluster(customer_data, features)
        else:
            cluster_id = self._heuristic_cluster(customer_data, features)

        persona = CLUSTER_PERSONAS.get(cluster_id, CLUSTER_PERSONAS[0])
        return {
            "cluster_id": cluster_id,
            "cluster_label": persona["label"],
            "cluster_description": persona["description"],
            "cluster_color": persona["color"],
            "nbo_boost": persona["nbo_boost"],
            "message_tone": persona["message_tone"],
        }

    def get_persona(self, cluster_id: int) -> Dict[str, Any]:
        return CLUSTER_PERSONAS.get(cluster_id, CLUSTER_PERSONAS[0])

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _build_vector(self, customer_data: Dict, features: Any) -> np.ndarray:
        """Build a 4-feature vector for a single customer."""
        age = float(customer_data.get("age") or 30)
        occ = float(_encode_occupation(customer_data.get("employment_type", "")))
        income = _safe_log(customer_data.get("annual_income") or 0)

        spend_90d = 0.0
        if hasattr(features, "windows") and features.windows:
            w = features.windows.get(90)
            if w:
                spend_90d = w.total_spend
        spend_log = _safe_log(spend_90d)

        return np.array([age, occ, income, spend_log], dtype=float)

    def _build_matrix(
        self,
        customers_df: pd.DataFrame,
        features_map: Dict[str, Any],
    ):
        """Build the N×4 matrix for all customers."""
        rows = []
        ids = []
        for _, row in customers_df.iterrows():
            cid = str(row.get("customer_id", ""))
            features = features_map.get(cid)
            if features is None:
                continue
            try:
                vec = self._build_vector(row.to_dict(), features)
                rows.append(vec)
                ids.append(cid)
            except Exception:
                continue
        return np.array(rows, dtype=float), ids

    def _heuristic_cluster(self, customer_data: Dict, features: Any) -> int:
        """
        Rule-based fallback cluster assignment when K-Means is not fitted.
        Deterministic and never crashes.
        """
        try:
            age = float(customer_data.get("age") or 30)
            income = float(customer_data.get("annual_income") or 0)
            emp = str(customer_data.get("employment_type") or "").lower()
            spend_90 = 0.0
            if hasattr(features, "windows") and features.windows:
                w = features.windows.get(90)
                if w:
                    spend_90 = w.total_spend

            if age < 25:
                return 6  # Student / Entry-Level
            if age >= 55:
                return 5  # Retired / Senior
            if income > 2_500_000:
                return 7  # High Net Worth
            if "business" in emp or "self" in emp:
                return 3  # Business Owner
            if spend_90 / max(income / 12, 1) < 0.25 and income > 400_000:
                return 4  # Conservative Saver
            if income > 1_200_000 and age < 45:
                return 1  # Ambitious Professional
            if age > 35 and customer_data.get("marital_status", "") == "Married":
                return 2  # Established Family
            return 0  # Young Salaried Spender (default)

        except Exception:
            return 0
