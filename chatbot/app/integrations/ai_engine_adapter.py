"""Thin read-only adapter to the existing AI engine.

Vedant/Shriram own ``Python/ai_engine/`` — this module NEVER copies or
rewrites any engine code.  It lazily imports from the existing package and
exposes only what the chatbot needs: data loading, engine construction,
and customer-context building.

The adapter ensures the existing ``Python/`` directory is on ``sys.path``
at import time (the chatbot runs from the repo root, so ``Python/`` is a
sibling directory).
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Ensure the existing Python/ directory is importable (ai_engine lives there).
_REPO_ROOT = Path(__file__).resolve().parents[3]
_PYTHON_DIR = _REPO_ROOT / "Python"
if str(_PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(_PYTHON_DIR))

# ── Data loaders (thin wrappers that cache per-process) ──────────────────


def load_credit_cards():
    """Load credit card catalogue from the existing ai_engine data_loader."""
    from ai_engine.data_loader import load_credit_cards
    return load_credit_cards()


def load_loan_products():
    """Load loan product catalogue from the existing ai_engine data_loader."""
    from ai_engine.data_loader import load_loan_products
    return load_loan_products()


def load_customers():
    """Load customers DataFrame from the existing ai_engine data_loader."""
    from ai_engine.data_loader import load_customers
    return load_customers()


def load_transactions():
    """Load transactions DataFrame from the existing ai_engine data_loader."""
    from ai_engine.data_loader import load_transactions
    return load_transactions()


# ── Engine constructors (lazy, cached per-process) ─────────────────────

_engines_cache: Dict[str, Any] = {}


def get_engines() -> Dict[str, Any]:
    """Lazily build and cache the existing AI engines.

    Returns a dict with keys matching what ``api_server.get_engines()``
    provides: ``feature_engine``, ``event_engine``, ``financial_analyst``,
    ``nbo_engine``, ``explain_engine``, ``customers_df``, ``transactions_df``.
    """
    if _engines_cache:
        return _engines_cache

    # Suppress SQLAlchemy/Supabase warnings when .env is missing
    import warnings
    warnings.filterwarnings("ignore", message=".*SUPABASE.*")

    from ai_engine.data_loader import (
        load_credit_cards, load_customers, load_investment_products,
        load_insurance_products, load_loan_products, load_transactions,
    )
    from ai_engine.event_engine import EventEngine
    from ai_engine.explainability_engine import ExplainabilityEngine
    from ai_engine.feature_engine import FeatureEngine
    from ai_engine.financial_analyst import FinancialAnalyst
    from ai_engine.nbo_engine import NBOEngine

    print("Chatbot integration: loading existing AI engine data and engines...")

    customers_df = load_customers()
    transactions_df = load_transactions()
    credit_cards_df = load_credit_cards()
    loans_df = load_loan_products()
    investments_df = load_investment_products()
    insurance_df = load_insurance_products()

    _engines_cache["customers_df"] = customers_df
    _engines_cache["transactions_df"] = transactions_df

    _engines_cache["feature_engine"] = FeatureEngine(transactions_df)
    _engines_cache["event_engine"] = EventEngine(transactions_df)
    _engines_cache["financial_analyst"] = FinancialAnalyst()
    _engines_cache["nbo_engine"] = NBOEngine(credit_cards_df, loans_df, investments_df, insurance_df)
    _engines_cache["explain_engine"] = ExplainabilityEngine()

    print("Chatbot integration: AI engines ready.")
    return _engines_cache


def reset_engines_cache() -> None:
    """Drop cached engines (tests only)."""
    _engines_cache.clear()
