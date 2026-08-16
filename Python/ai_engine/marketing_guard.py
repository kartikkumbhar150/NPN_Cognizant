"""
Marketing Guard
===============
Banking-Grade Customer Intelligence — NPN Bank AI Pipeline v2.0

Consent and marketing safety gate. This is the LAST checkpoint before
any marketing content is generated or delivered.

Design principles:
  - Consent check happens BEFORE GenAI generation
  - This is a HARD GATE — if blocked, no marketing content is produced
  - Campaign fatigue logic prevents over-contacting customers
  - Reads configuration from marketing.yaml
  - Logs all gate decisions for audit purposes
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)

# Default marketing config (used if YAML not available)
DEFAULT_CONFIG = {
    "consent_defaults": {
        "email": True,
        "sms": True,
        "push": True,
        "app_notification": True,
        "relationship_manager": True,
    },
    "compliance": {
        "min_campaign_interval_hours": 24,
        "max_campaigns_per_month": 8,
        "high_risk_products": ["Home Loan", "Personal Loan"],
    },
    "fatigue": {
        "window_days": 30,
        "max_campaigns_per_window": 5,
        "same_category_days": 7,
        "ignored_threshold": 3,
    },
}


class MarketingGuard:
    """
    Pre-marketing consent and safety gate.

    Usage:
        guard = MarketingGuard(config_path="config/marketing.yaml")
        result = guard.check(customer_data, product_result, campaign_history)
        if result["allowed"]:
            # generate marketing content
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        self.config = self._load_config(config_path)

    # ── Public API ─────────────────────────────────────────────────────────────

    def check(
        self,
        customer_data: Dict[str, Any],
        product_result: Dict[str, Any],
        campaign_history: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """
        Run all marketing safety checks.

        Args:
            customer_data: Customer profile dict
            product_result: The NBO candidate product result
            campaign_history: List of past campaigns for this customer

        Returns:
            {
                "allowed": bool,
                "reason": str (if blocked),
                "recommended_channel": str,
                "channel_score": float,
                "warnings": list,
                "fatigue_score": float,
            }
        """
        warnings: List[str] = []
        history = campaign_history or []

        # ── Check 1: Customer marketing consent ───────────────────────────────
        marketing_consent = customer_data.get("marketing_consent", True)
        if marketing_consent is False:
            return self._blocked(
                "Customer has opted out of marketing communications",
                "marketing_consent_false",
            )

        # ── Check 2: Customer status ───────────────────────────────────────────
        customer_status = str(customer_data.get("status", "Active")).strip()
        if customer_status.lower() in ("closed", "blocked", "suspended", "dormant"):
            return self._blocked(
                f"Customer account status: {customer_status}",
                "inactive_customer",
            )

        # ── Check 3: Product status ────────────────────────────────────────────
        product_status = str(
            product_result.get("product_data", {}).get("product_status", "Active")
        ).strip()
        if product_status != "Active":
            return self._blocked(
                f"Product is not active: {product_status}",
                "inactive_product",
            )

        # ── Check 4: Campaign frequency gate ──────────────────────────────────
        frequency_result = self._check_campaign_frequency(history)
        if not frequency_result["allowed"]:
            return self._blocked(
                frequency_result["reason"],
                "campaign_frequency_exceeded",
            )
        elif frequency_result.get("warning"):
            warnings.append(frequency_result["warning"])

        # ── Check 5: Same product repeat cooldown ─────────────────────────────
        product_name = product_result.get("product_name", "")
        cooldown_result = self._check_product_cooldown(product_name, history)
        if not cooldown_result["allowed"]:
            return self._blocked(
                cooldown_result["reason"],
                "product_cooldown_active",
            )

        # ── Check 6: Fatigue score ─────────────────────────────────────────────
        fatigue_score = self._compute_fatigue_score(history)
        if fatigue_score > 0.85:
            return self._blocked(
                f"Campaign fatigue score too high ({fatigue_score:.2f})",
                "campaign_fatigue",
            )
        elif fatigue_score > 0.60:
            warnings.append(f"Moderate campaign fatigue detected ({fatigue_score:.2f})")

        # ── Determine recommended channel ──────────────────────────────────────
        channel_result = self._recommend_channel(customer_data, history)

        return {
            "allowed": True,
            "reason": None,
            "recommended_channel": channel_result["channel"],
            "channel_score": channel_result["score"],
            "channel_reason": channel_result["reason"],
            "fatigue_score": round(fatigue_score, 2),
            "warnings": warnings,
        }

    # ── Check helpers ──────────────────────────────────────────────────────────

    def _check_campaign_frequency(self, history: List[Dict]) -> Dict:
        """Check if customer has received too many campaigns recently."""
        compliance = self.config.get("compliance", {})
        max_per_month = compliance.get("max_campaigns_per_month", 8)
        min_interval_hours = compliance.get("min_campaign_interval_hours", 24)

        now = datetime.utcnow()
        month_ago = now - timedelta(days=30)

        recent = [
            h for h in history
            if self._parse_date(h.get("created_at", "")) > month_ago
        ]

        if len(recent) >= max_per_month:
            return {
                "allowed": False,
                "reason": f"Maximum {max_per_month} campaigns/month reached ({len(recent)} sent)",
            }

        # Check minimum interval
        if recent:
            latest = max(
                (self._parse_date(h.get("created_at", "")) for h in recent),
                default=datetime.min,
            )
            hours_since = (now - latest).total_seconds() / 3600
            if hours_since < min_interval_hours:
                return {
                    "allowed": False,
                    "reason": f"Minimum campaign interval not met ({hours_since:.0f}h < {min_interval_hours}h required)",
                }

        warning = None
        if len(recent) >= max_per_month * 0.75:
            warning = f"Approaching campaign frequency limit ({len(recent)}/{max_per_month} this month)"

        return {"allowed": True, "warning": warning}

    def _check_product_cooldown(self, product_name: str, history: List[Dict]) -> Dict:
        """Check if same product was recently offered."""
        fatigue_cfg = self.config.get("fatigue", {})
        cooldown_days = fatigue_cfg.get("same_category_days", 7)
        cutoff = datetime.utcnow() - timedelta(days=cooldown_days)

        recent_same = [
            h for h in history
            if h.get("product", "") == product_name
            and self._parse_date(h.get("created_at", "")) > cutoff
        ]

        if recent_same:
            return {
                "allowed": False,
                "reason": f"Same product '{product_name}' was offered within the last {cooldown_days} days",
            }
        return {"allowed": True}

    def _compute_fatigue_score(self, history: List[Dict]) -> float:
        """
        Compute campaign fatigue score 0–1 based on recent ignored campaigns.
        Higher = more fatigued.
        """
        fatigue_cfg = self.config.get("fatigue", {})
        window_days = fatigue_cfg.get("window_days", 30)
        ignored_threshold = fatigue_cfg.get("ignored_threshold", 3)

        now = datetime.utcnow()
        cutoff = now - timedelta(days=window_days)
        recent = [
            h for h in history
            if self._parse_date(h.get("created_at", "")) > cutoff
        ]

        if not recent:
            return 0.0

        # Count ignored (sent but not opened/clicked)
        ignored = [
            h for h in recent
            if h.get("status", "") in ("sent", "delivered")
            and not h.get("opened") and not h.get("clicked")
        ]

        base_fatigue = len(recent) / max(
            self.config.get("compliance", {}).get("max_campaigns_per_month", 8), 1
        )
        ignored_factor = min(1.0, len(ignored) / max(ignored_threshold, 1)) * 0.5

        return min(1.0, base_fatigue * 0.5 + ignored_factor)

    def _recommend_channel(
        self, customer_data: Dict, history: List[Dict]
    ) -> Dict[str, Any]:
        """Recommend the best communication channel."""
        # Prototype: use simple heuristics
        # In production, this would use engagement history per channel

        # Check if customer prefers digital (based on transaction digital ratio)
        digital_ratio = customer_data.get("digital_transaction_ratio", 0.7)

        if digital_ratio > 0.70:
            return {
                "channel": "push",
                "score": 0.80,
                "reason": "Customer shows high digital engagement",
            }
        elif digital_ratio > 0.40:
            return {
                "channel": "email",
                "score": 0.65,
                "reason": "Moderate digital engagement — email preferred",
            }
        else:
            return {
                "channel": "relationship_manager",
                "score": 0.55,
                "reason": "Low digital engagement — RM outreach recommended",
            }

    # ── Utility helpers ────────────────────────────────────────────────────────

    def _blocked(self, reason: str, code: str) -> Dict[str, Any]:
        logger.info("MarketingGuard BLOCKED: [%s] %s", code, reason)
        return {
            "allowed": False,
            "reason": reason,
            "block_code": code,
            "recommended_channel": None,
            "channel_score": 0.0,
            "channel_reason": None,
            "fatigue_score": None,
            "warnings": [],
        }

    def _parse_date(self, date_str: str) -> datetime:
        """Safely parse an ISO date string."""
        if not date_str:
            return datetime.min
        try:
            return datetime.fromisoformat(str(date_str).replace("Z", "+00:00")).replace(tzinfo=None)
        except (ValueError, TypeError):
            return datetime.min

    def _load_config(self, config_path: Optional[str]) -> Dict:
        if not config_path:
            return DEFAULT_CONFIG
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or DEFAULT_CONFIG
        except Exception as exc:
            logger.warning("MarketingGuard: could not load config from %s: %s", config_path, exc)
            return DEFAULT_CONFIG
