"""
Feature Engine
==============
Banking-Grade Customer Intelligence — NPN Bank AI Pipeline v2.0

Responsibilities:
  1. Data quality checks + normalization
  2. Rolling-window feature computation (7/30/60/90/180/365 day windows)
  3. Produce a standardized CustomerFeatureSet used by all downstream modules

Design principles:
  - Never crash on missing/null data
  - Every feature carries value + source + confidence
  - Rolling windows replace lifetime-only totals
  - No financial decisioning here — pure feature engineering
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)

# ── Merchant category mapping (single source of truth) ───────────────────────
MERCHANT_CATEGORY_MAP: Dict[str, str] = {
    # Prefix-based mapping for synthetic merchant IDs
    "MER00": "Travel",        # Airlines
    "MER01": "Dining",        # Food delivery / restaurants
    "MER02": "Shopping",      # E-commerce
    "MER03": "Shopping",      # Retail
    "MER04": "Groceries",
    "MER05": "Transport",     # Cab
    "MER06": "Transport",     # Bus
    "MER07": "Transport",     # Train
    "MER08": "Travel",        # Hotels
    "MER09": "Entertainment",
    "MER10": "Fuel",
    "MER11": "Utilities",
    "MER12": "Subscriptions",
    "MER13": "Medical",
    "MER14": "Education",
    "MER15": "Investment",    # SIP / Mutual funds
    "MER16": "Investment",    # FD / Bonds
    "MER17": "Insurance",
    "MER18": "Rent",
    "MER19": "P2P",           # Peer-to-peer transfers
    "MER20": "International", # International
}

# Keyword fallback (for description-based matching)
DESCRIPTION_CATEGORY_MAP: Dict[str, str] = {
    "SALARY": "Salary",
    "NEFT": "Transfer",
    "IMPS": "Transfer",
    "UPI": "Transfer",
    "ATM": "Cash",
    "AIRLINE": "Travel",
    "HOTEL": "Travel",
    "FLIGHT": "Travel",
    "SIP": "Investment",
    "MUTUAL": "Investment",
    "INSURANCE": "Insurance",
    "EMI": "EMI",
    "RENT": "Rent",
    "GROCERY": "Groceries",
    "FUEL": "Fuel",
    "SCHOOL": "Education",
    "COLLEGE": "Education",
    "HOSPITAL": "Medical",
    "PHARMACY": "Medical",
    "CLINIC": "Medical",
}

WINDOW_DAYS = [7, 30, 60, 90, 180, 365]


def categorize_merchant(merchant_id: Optional[str], description: Optional[str]) -> str:
    """
    Map a transaction to an analytical category.
    Uses merchant ID prefix first, falls back to description keywords.
    Returns 'Other' if no match found — never raises.
    """
    if merchant_id and not pd.isna(merchant_id) and str(merchant_id).strip():
        mid = str(merchant_id).strip()
        for prefix, cat in MERCHANT_CATEGORY_MAP.items():
            if mid.startswith(prefix):
                return cat

    if description and not pd.isna(description) and str(description).strip():
        desc_upper = str(description).upper()
        for keyword, cat in DESCRIPTION_CATEGORY_MAP.items():
            if keyword in desc_upper:
                return cat

    return "Other"


@dataclass
class WindowFeatures:
    """Spending and behavioral features for a specific rolling window."""
    window_days: int
    transaction_count: int = 0
    debit_count: int = 0
    credit_count: int = 0
    total_spend: float = 0.0
    total_income: float = 0.0
    avg_transaction: float = 0.0
    median_transaction: float = 0.0
    max_transaction: float = 0.0
    category_spend: Dict[str, float] = field(default_factory=dict)
    category_counts: Dict[str, int] = field(default_factory=dict)
    top_merchants: List[Dict] = field(default_factory=list)
    digital_ratio: float = 0.0      # proportion of UPI/netbanking/card vs cash/ATM


@dataclass
class CustomerFeatureSet:
    """
    Complete feature object for one customer.
    This is the standardized contract passed between all pipeline modules.
    """
    customer_id: str
    computed_at: str = ""

    # ── Raw profile ──────────────────────────────────────────────────────────
    profile: Dict[str, Any] = field(default_factory=dict)

    # ── Rolling window features ───────────────────────────────────────────────
    windows: Dict[int, WindowFeatures] = field(default_factory=dict)

    # ── Derived income features ───────────────────────────────────────────────
    monthly_income_avg: float = 0.0
    monthly_income_std: float = 0.0
    income_stability: float = 0.0      # 0–1 (1 = very stable)
    income_trend: str = "stable"       # up / down / stable
    income_growth_rate: float = 0.0    # % change

    # ── Derived spend features ────────────────────────────────────────────────
    monthly_spend_avg_90d: float = 0.0
    monthly_spend_std_90d: float = 0.0
    spend_volatility: float = 0.0
    spend_trend: str = "stable"

    # ── Surplus ──────────────────────────────────────────────────────────────
    estimated_monthly_surplus: float = 0.0
    surplus_ratio: float = 0.0

    # ── Transaction meta ──────────────────────────────────────────────────────
    total_transactions: int = 0
    active_months: int = 0
    first_transaction_date: Optional[str] = None
    last_transaction_date: Optional[str] = None
    tenure_days: int = 0
    has_transactions: bool = False

    # ── Trend signals ─────────────────────────────────────────────────────────
    trends: Dict[str, Dict] = field(default_factory=dict)

    # ── Recurring payments ────────────────────────────────────────────────────
    recurring_payments: List[Dict] = field(default_factory=list)

    # ── Data quality ──────────────────────────────────────────────────────────
    data_quality_score: float = 1.0   # 0–1
    data_warnings: List[str] = field(default_factory=list)

    # ── Raw Product Holdings (all records from DB per customer) ──────────────
    holdings: Dict[str, List[Dict[str, Any]]] = field(default_factory=lambda: {
        "accounts": [],
        "deposits": [],
        "credit_cards": [],
        "debit_cards": [],
        "investments": [],
        "loans": [],
        "insurance": [],
    })

    # ── Derived Holdings Signals (computed from holdings) ──────────────────────
    has_insurance: bool = False
    has_life_insurance: bool = False
    has_health_insurance: bool = False
    has_investments: bool = False
    has_home_loan: bool = False
    has_personal_loan: bool = False
    has_vehicle_loan: bool = False
    has_education_loan: bool = False
    has_deposits: bool = False
    total_emi_monthly: float = 0.0          # Sum of all active loan EMIs
    total_sip_monthly: float = 0.0          # Sum of all active SIP/investment monthly amounts
    total_assets_value: float = 0.0         # investments current_value + deposits principal
    total_outstanding_debt: float = 0.0     # Sum of all outstanding loan principals
    net_worth_indicator: float = 0.0        # total_assets_value - total_outstanding_debt
    held_insurance_categories: List[str] = field(default_factory=list)   # e.g. ["Health", "Life"]
    held_investment_categories: List[str] = field(default_factory=list)  # e.g. ["Mutual Fund", "FD"]
    held_loan_categories: List[str] = field(default_factory=list)        # e.g. ["Personal", "Home"]
    held_card_names: List[str] = field(default_factory=list)             # e.g. ["Diners Black"]

    # ── Feature snapshot for audit ────────────────────────────────────────────
    feature_version: str = "2.0"


class FeatureEngine:
    """
    Transforms raw customer profile + transactions into CustomerFeatureSet.

    Usage:
        engine = FeatureEngine(transactions_df, holdings_data)
        features = engine.compute(customer_id, customer_data)
    """

    def __init__(self, transactions_df: pd.DataFrame, holdings_data: Dict[str, pd.DataFrame] = None) -> None:
        self.transactions = self._clean_transactions(transactions_df)
        self.holdings_data = holdings_data or {}

    # ── Public API ────────────────────────────────────────────────────────────

    def compute(self, customer_id: str, customer_data: Dict[str, Any]) -> CustomerFeatureSet:
        """
        Compute full feature set for one customer.
        Never raises — returns feature set with data_warnings on issues.
        """
        fs = CustomerFeatureSet(
            customer_id=customer_id,
            computed_at=datetime.utcnow().isoformat() + "Z",
            profile=self._normalize_profile(customer_data),
            feature_version="2.0",
        )

        try:
            cust_tx = self.transactions[
                self.transactions["customer_id"] == customer_id
            ].copy()

            if cust_tx.empty:
                fs.has_transactions = False
                fs.data_warnings.append(f"Customer {customer_id} has no transactions.")
                fs.data_quality_score = 0.3
                return fs

            fs.has_transactions = True
            fs = self._compute_transaction_meta(fs, cust_tx)
            fs = self._compute_window_features(fs, cust_tx)
            fs = self._compute_income_features(fs, cust_tx)
            fs = self._compute_spend_features(fs)
            fs = self._compute_surplus(fs, customer_data)
            fs = self._compute_trends(fs, cust_tx)
            fs = self._detect_recurring(fs, cust_tx)
            fs = self._compute_holdings(fs, customer_id)
            fs = self._compute_data_quality(fs, customer_data, cust_tx)

        except Exception as exc:
            logger.error("FeatureEngine.compute error for %s: %s", customer_id, exc, exc_info=True)
            fs.data_warnings.append(f"Feature computation error: {exc}")
            fs.data_quality_score = max(0.1, fs.data_quality_score - 0.4)

        return fs

    # ── Transaction cleaning ─────────────────────────────────────────────────

    def _clean_transactions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and normalize the transactions DataFrame."""
        if df is None or df.empty:
            return pd.DataFrame()

        df = df.copy()

        # Ensure date column
        if "transaction_date" in df.columns:
            df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
            df = df.dropna(subset=["transaction_date"])

        # Ensure amount is numeric and positive
        if "amount" in df.columns:
            df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
            df = df[df["amount"] > 0]

        # Normalize transaction type
        if "transaction_type" in df.columns:
            df["transaction_type"] = df["transaction_type"].str.strip().str.title()

        # Categorize
        df["category"] = df.apply(
            lambda r: categorize_merchant(
                r.get("merchant_id"), r.get("transaction_description")
            ),
            axis=1,
        )

        return df

    # ── Transaction metadata ──────────────────────────────────────────────────

    def _compute_transaction_meta(
        self, fs: CustomerFeatureSet, cust_tx: pd.DataFrame
    ) -> CustomerFeatureSet:
        fs.total_transactions = len(cust_tx)
        fs.first_transaction_date = str(cust_tx["transaction_date"].min().date())
        fs.last_transaction_date = str(cust_tx["transaction_date"].max().date())
        fs.tenure_days = (
            cust_tx["transaction_date"].max() - cust_tx["transaction_date"].min()
        ).days
        fs.active_months = cust_tx["transaction_date"].dt.to_period("M").nunique()
        return fs

    # ── Window features ───────────────────────────────────────────────────────

    def _compute_window_features(
        self, fs: CustomerFeatureSet, cust_tx: pd.DataFrame
    ) -> CustomerFeatureSet:
        """Compute features for each rolling window."""
        reference_date = cust_tx["transaction_date"].max()

        for days in WINDOW_DAYS:
            cutoff = reference_date - timedelta(days=days)
            window_tx = cust_tx[cust_tx["transaction_date"] >= cutoff]

            wf = WindowFeatures(window_days=days)
            wf.transaction_count = len(window_tx)

            if window_tx.empty:
                fs.windows[days] = wf
                continue

            debits = window_tx[window_tx["transaction_type"] == "Debit"]
            credits = window_tx[window_tx["transaction_type"] == "Credit"]

            wf.debit_count = len(debits)
            wf.credit_count = len(credits)
            wf.total_spend = float(debits["amount"].sum())
            wf.total_income = float(credits["amount"].sum())

            if not debits.empty:
                wf.avg_transaction = float(debits["amount"].mean())
                wf.median_transaction = float(debits["amount"].median())
                wf.max_transaction = float(debits["amount"].max())
                wf.category_spend = (
                    debits.groupby("category")["amount"].sum().to_dict()
                )
                wf.category_counts = (
                    debits.groupby("category").size().to_dict()
                )

                # Top merchants by spend
                if "merchant_id" in debits.columns:
                    merch_spend = (
                        debits.groupby("merchant_id")["amount"]
                        .sum()
                        .sort_values(ascending=False)
                        .head(5)
                    )
                    wf.top_merchants = [
                        {"merchant_id": m, "amount": float(a)}
                        for m, a in merch_spend.items()
                        if m and not pd.isna(m)
                    ]

                # Digital payment ratio (non-cash, non-ATM)
                if "transaction_description" in debits.columns:
                    cash_mask = debits["transaction_description"].str.upper().str.contains(
                        "ATM|CASH", na=False
                    )
                    wf.digital_ratio = float(1 - cash_mask.mean()) if len(debits) > 0 else 1.0

            fs.windows[days] = wf

        return fs

    # ── Income features ───────────────────────────────────────────────────────

    def _compute_income_features(
        self, fs: CustomerFeatureSet, cust_tx: pd.DataFrame
    ) -> CustomerFeatureSet:
        """Derive income stability, trend, and monthly averages from salary credits."""
        salary_tx = cust_tx[
            (cust_tx["transaction_type"] == "Credit")
            & (cust_tx["category"] == "Salary")
        ].copy()

        if salary_tx.empty:
            # Fall back to declared income from profile
            declared = fs.profile.get("annual_income", 0) or 0
            fs.monthly_income_avg = declared / 12
            fs.income_stability = 0.5  # Unknown
            fs.data_warnings.append("No salary credits found; using declared income.")
            return fs

        salary_tx["ym"] = salary_tx["transaction_date"].dt.to_period("M")
        monthly = salary_tx.groupby("ym")["amount"].sum().sort_index()
        vals = monthly.values.astype(float)

        fs.monthly_income_avg = float(vals.mean())
        fs.monthly_income_std = float(vals.std()) if len(vals) > 1 else 0.0

        # Stability: coefficient of variation (lower = more stable)
        if fs.monthly_income_avg > 0:
            cv = fs.monthly_income_std / fs.monthly_income_avg
            fs.income_stability = round(max(0.0, 1.0 - min(cv, 1.0)), 3)
        else:
            fs.income_stability = 0.0

        # Trend: compare last 3 months vs previous 3 months
        if len(vals) >= 6:
            recent_avg = vals[-3:].mean()
            prev_avg = vals[-6:-3].mean()
            if prev_avg > 0:
                growth = (recent_avg - prev_avg) / prev_avg
                fs.income_growth_rate = round(growth, 4)
                if growth > 0.05:
                    fs.income_trend = "up"
                elif growth < -0.05:
                    fs.income_trend = "down"
                else:
                    fs.income_trend = "stable"
        elif len(vals) >= 2:
            growth = (vals[-1] - vals[0]) / (vals[0] if vals[0] > 0 else 1)
            fs.income_growth_rate = round(growth, 4)
            fs.income_trend = "up" if growth > 0.05 else ("down" if growth < -0.05 else "stable")

        return fs

    # ── Spend features ────────────────────────────────────────────────────────

    def _compute_spend_features(self, fs: CustomerFeatureSet) -> CustomerFeatureSet:
        """Derive spend volatility and trend from 90-day window."""
        w90 = fs.windows.get(90)
        w180 = fs.windows.get(180)

        if w90 and w90.total_spend > 0:
            # Monthly average over the 90-day window
            fs.monthly_spend_avg_90d = w90.total_spend / 3.0

        if w180 and w90:
            # Compare 90-day spend rate vs prior 90 days
            prior_90 = w180.total_spend - w90.total_spend
            if prior_90 > 0:
                change = (w90.total_spend - prior_90) / prior_90
                if change > 0.15:
                    fs.spend_trend = "up"
                elif change < -0.15:
                    fs.spend_trend = "down"
                else:
                    fs.spend_trend = "stable"

        return fs

    # ── Surplus ───────────────────────────────────────────────────────────────

    def _compute_surplus(
        self, fs: CustomerFeatureSet, customer_data: Dict
    ) -> CustomerFeatureSet:
        """Estimate monthly surplus from income vs spend."""
        income = fs.monthly_income_avg or (
            (customer_data.get("annual_income", 0) or 0) / 12
        )
        spend = fs.monthly_spend_avg_90d

        if income > 0:
            fs.estimated_monthly_surplus = income - spend
            fs.surplus_ratio = round(
                max(-1.0, fs.estimated_monthly_surplus / income), 4
            )
        return fs

    # ── Trend computation ─────────────────────────────────────────────────────

    def _compute_trends(
        self, fs: CustomerFeatureSet, cust_tx: pd.DataFrame
    ) -> CustomerFeatureSet:
        """Compute category-level trends: current 30d vs previous 30d."""
        ref = cust_tx["transaction_date"].max()
        debits = cust_tx[cust_tx["transaction_type"] == "Debit"].copy()

        if debits.empty:
            return fs

        current_cutoff = ref - timedelta(days=30)
        prev_cutoff = ref - timedelta(days=60)

        current_30 = debits[debits["transaction_date"] >= current_cutoff]
        prev_30 = debits[
            (debits["transaction_date"] >= prev_cutoff)
            & (debits["transaction_date"] < current_cutoff)
        ]

        categories = set(debits["category"].unique())
        for cat in categories:
            curr_val = float(current_30[current_30["category"] == cat]["amount"].sum())
            prev_val = float(prev_30[prev_30["category"] == cat]["amount"].sum())

            if prev_val > 0:
                change_pct = round((curr_val - prev_val) / prev_val * 100, 1)
            elif curr_val > 0:
                change_pct = 100.0
            else:
                change_pct = 0.0

            direction = (
                "up" if change_pct > 10 else "down" if change_pct < -10 else "stable"
            )
            confidence = min(
                1.0, (len(current_30[current_30["category"] == cat]) + 1) / 10
            )

            fs.trends[cat] = {
                "metric": f"{cat}_spend_30d",
                "current_value": curr_val,
                "previous_value": prev_val,
                "change_percent": change_pct,
                "direction": direction,
                "confidence": round(confidence, 2),
            }

        return fs

    # ── Recurring payment detection ───────────────────────────────────────────

    def _detect_recurring(
        self, fs: CustomerFeatureSet, cust_tx: pd.DataFrame
    ) -> CustomerFeatureSet:
        """
        Detect recurring transactions using merchant + amount stability.
        A transaction is recurring if same merchant appears 3+ times
        with a consistent interval and amount.
        """
        debits = cust_tx[cust_tx["transaction_type"] == "Debit"].copy()

        if debits.empty or "merchant_id" not in debits.columns:
            return fs

        debits = debits.dropna(subset=["merchant_id"])
        debits = debits[debits["merchant_id"].str.strip() != ""]

        recurring = []
        for merchant_id, group in debits.groupby("merchant_id"):
            if len(group) < 3:
                continue

            group = group.sort_values("transaction_date")
            amounts = group["amount"].values
            avg_amount = float(amounts.mean())
            amount_std = float(amounts.std()) if len(amounts) > 1 else 0
            amount_cv = amount_std / avg_amount if avg_amount > 0 else 1.0

            # Compute intervals
            dates = group["transaction_date"].values
            if len(dates) >= 2:
                intervals = [
                    (dates[i+1] - dates[i]).astype("timedelta64[D]").astype(int)
                    for i in range(len(dates) - 1)
                ]
                avg_interval = sum(intervals) / len(intervals) if intervals else 0
                interval_std = (
                    (sum((x - avg_interval)**2 for x in intervals) / len(intervals)) ** 0.5
                    if len(intervals) > 1 else 0
                )
                interval_cv = interval_std / avg_interval if avg_interval > 0 else 1.0
            else:
                avg_interval = 0
                interval_cv = 1.0

            # Only flag as recurring if both amount and interval are consistent
            if amount_cv < 0.25 and interval_cv < 0.30:
                # Determine frequency label
                if avg_interval < 10:
                    freq = "weekly"
                elif avg_interval < 35:
                    freq = "monthly"
                elif avg_interval < 100:
                    freq = "quarterly"
                else:
                    freq = "irregular"

                consistency = round(1 - (amount_cv + interval_cv) / 2, 2)
                category = group["category"].mode().iloc[0] if not group["category"].empty else "Other"
                last_date = str(group["transaction_date"].max().date())

                recurring.append({
                    "merchant_id": merchant_id,
                    "category": category,
                    "average_amount": round(avg_amount, 2),
                    "frequency": freq,
                    "occurrences": len(group),
                    "last_occurrence": last_date,
                    "consistency_score": consistency,
                })

        fs.recurring_payments = sorted(
            recurring, key=lambda x: x["consistency_score"], reverse=True
        )
        return fs

    # ── Holdings ──────────────────────────────────────────────────────────────

    def _compute_holdings(self, fs: CustomerFeatureSet, customer_id: str) -> CustomerFeatureSet:
        """
        Extract customer holdings from the pre-loaded DataFrames and compute
        all derived signals (booleans, aggregates, category lists).
        """
        if not self.holdings_data:
            return fs

        # ── Load raw records per category ─────────────────────────────────────
        for category, df in self.holdings_data.items():
            if df is not None and not df.empty and "customer_id" in df.columns:
                cust_df = df[df["customer_id"] == customer_id].copy()
                if not cust_df.empty:
                    records = cust_df.where(pd.notnull(cust_df), None).to_dict("records")
                    fs.holdings[category] = records

        # ── Derive signals from loans ──────────────────────────────────────────
        loans = fs.holdings.get("loans", [])
        active_loans = [l for l in loans if str(l.get("loan_status", "")).lower() == "active"]
        if active_loans:
            loan_cats = [str(l.get("loan_category", "")) for l in active_loans]
            fs.held_loan_categories = list(set(loan_cats))
            fs.has_home_loan = any("home" in c.lower() for c in loan_cats)
            fs.has_personal_loan = any("personal" in c.lower() for c in loan_cats)
            fs.has_vehicle_loan = any(c.lower() in ("vehicle", "car", "auto", "two wheeler") for c in loan_cats)
            fs.has_education_loan = any("education" in c.lower() for c in loan_cats)
            fs.total_emi_monthly = sum(float(l.get("emi_amount") or 0) for l in active_loans)
            fs.total_outstanding_debt = sum(float(l.get("outstanding_principal") or 0) for l in active_loans)

        # ── Derive signals from investments ────────────────────────────────────
        investments = fs.holdings.get("investments", [])
        active_investments = [i for i in investments if str(i.get("status", "")).lower() == "active"]
        if active_investments:
            inv_cats = [str(i.get("investment_category", "")) for i in active_investments]
            fs.held_investment_categories = list(set(inv_cats))
            fs.has_investments = True
            fs.total_sip_monthly = sum(float(i.get("monthly_amount") or 0) for i in active_investments)
            fs.total_assets_value += sum(float(i.get("current_value") or 0) for i in active_investments)

        # ── Derive signals from deposits ───────────────────────────────────────
        deposits = fs.holdings.get("deposits", [])
        active_deposits = [d for d in deposits if str(d.get("deposit_status", "")).lower() == "active"]
        if active_deposits:
            fs.has_deposits = True
            fs.total_assets_value += sum(float(d.get("principal_amount") or 0) for d in active_deposits)

        # ── Derive signals from insurance ──────────────────────────────────────
        insurance = fs.holdings.get("insurance", [])
        active_insurance = [i for i in insurance if str(i.get("policy_status", "")).lower() == "active"]
        if active_insurance:
            ins_cats = [str(i.get("insurance_category", "")) for i in active_insurance]
            fs.held_insurance_categories = list(set(ins_cats))
            fs.has_insurance = True
            fs.has_life_insurance = any(c.lower() in ("life", "term", "ulip") for c in ins_cats)
            fs.has_health_insurance = any(c.lower() in ("health", "medical") for c in ins_cats)

        # ── Derive signals from credit cards ───────────────────────────────────
        credit_cards = fs.holdings.get("credit_cards", [])
        active_cards = [c for c in credit_cards if str(c.get("card_status", "")).lower() == "active"]
        if active_cards:
            fs.held_card_names = [str(c.get("card_name", "")) for c in active_cards]

        # ── Net worth indicator ────────────────────────────────────────────────
        fs.net_worth_indicator = fs.total_assets_value - fs.total_outstanding_debt

        # ── Correct surplus: deduct actual EMIs and SIPs ───────────────────────
        # We already computed estimated_monthly_surplus = income - spend
        # Now subtract actual committed outflows not fully captured in spend
        committed_outflows = fs.total_emi_monthly + fs.total_sip_monthly
        if committed_outflows > 0 and fs.monthly_income_avg > 0:
            # Only adjust if surplus hasn't already captured these (EMIs are in spend as "EMI" category)
            w90 = fs.windows.get(90)
            emi_in_spend = (w90.category_spend.get("EMI", 0) / 3.0) if w90 else 0
            invest_in_spend = (w90.category_spend.get("Investment", 0) / 3.0) if w90 else 0
            # If transaction-based EMI/invest spend is much less than actual, use actual
            if committed_outflows > (emi_in_spend + invest_in_spend) * 1.5:
                adjusted_surplus = fs.monthly_income_avg - fs.monthly_spend_avg_90d - max(0, committed_outflows - emi_in_spend - invest_in_spend)
                fs.estimated_monthly_surplus = adjusted_surplus
                if fs.monthly_income_avg > 0:
                    fs.surplus_ratio = round(max(-1.0, fs.estimated_monthly_surplus / fs.monthly_income_avg), 4)

        return fs

    # ── Data quality ──────────────────────────────────────────────────────────

    def _compute_data_quality(
        self,
        fs: CustomerFeatureSet,
        customer_data: Dict,
        cust_tx: pd.DataFrame,
    ) -> CustomerFeatureSet:
        """Score data quality 0–1 and collect warnings."""
        score = 1.0
        warnings = list(fs.data_warnings)

        if fs.total_transactions < 5:
            score -= 0.2
            warnings.append("Very few transactions (<5). Signals may be unreliable.")

        if fs.active_months < 2:
            score -= 0.1
            warnings.append("Data covers less than 2 months.")

        if not customer_data.get("annual_income"):
            score -= 0.1
            warnings.append("Missing declared annual income.")

        if not customer_data.get("age"):
            score -= 0.05
            warnings.append("Missing customer age.")

        w90 = fs.windows.get(90)
        if w90 and w90.transaction_count < 3:
            score -= 0.15
            warnings.append("Sparse recent transactions (< 3 in last 90 days).")

        other_pct = (
            w90.category_spend.get("Other", 0) / max(w90.total_spend, 1)
            if w90 else 0
        )
        if other_pct > 0.50:
            score -= 0.1
            warnings.append(
                f"{other_pct*100:.0f}% of transactions are uncategorized."
            )

        fs.data_quality_score = round(max(0.0, min(1.0, score)), 2)
        fs.data_warnings = warnings
        return fs

    # ── Profile normalizer ────────────────────────────────────────────────────

    def _normalize_profile(self, customer_data: Dict) -> Dict:
        """Normalize and validate the raw customer profile dict."""
        def _safe_int(val: Any, default: int = 0) -> int:
            try:
                return int(val) if val is not None and not (isinstance(val, float) and math.isnan(val)) else default
            except (ValueError, TypeError):
                return default

        def _safe_float(val: Any, default: float = 0.0) -> float:
            try:
                return float(val) if val is not None and not (isinstance(val, float) and math.isnan(val)) else default
            except (ValueError, TypeError):
                return default

        def _safe_str(val: Any, default: str = "") -> str:
            return str(val).strip() if val is not None and not (isinstance(val, float) and math.isnan(val)) else default

        return {
            "customer_id": _safe_str(customer_data.get("customer_id")),
            "first_name": _safe_str(customer_data.get("first_name")),
            "last_name": _safe_str(customer_data.get("last_name")),
            "age": _safe_int(customer_data.get("age"), 30),
            "gender": _safe_str(customer_data.get("gender")),
            "marital_status": _safe_str(customer_data.get("marital_status")),
            "city": _safe_str(customer_data.get("city")),
            "state": _safe_str(customer_data.get("state")),
            "employment_type": _safe_str(customer_data.get("employment_type")),
            "annual_income": _safe_float(customer_data.get("annual_income")),
            "credit_score": _safe_int(customer_data.get("credit_score"), 650),
            "customer_segment_type": _safe_str(customer_data.get("customer_segment_type")),
            "email": _safe_str(customer_data.get("email")),
        }
