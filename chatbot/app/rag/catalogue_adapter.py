"""Project-catalogue adapter.

Reads the repository's CSV product tables (``credit_card_products.csv``,
``loan_products.csv``) and converts each active row into a
:class:`~chatbot.app.rag.models.KnowledgeDocument` for the ingestion
pipeline.

Only **HDFC Bank**-branded products are included — mixed-provider
catalogues (insurance, debit cards, investments) are excluded because
the chatbot must attribute correctly.

Entity attribution: every document gets ``entity="HDFC Bank"``.
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import List

from chatbot.app.rag.models import KnowledgeDocument


def _slugify_product_id(product_code: str) -> str:
    """Slugify a canonical product_code for use in source_id strings.

    ``HDFCMB+`` becomes ``hdfcmb-plus`` — the ``+`` character is not
    valid in the slug pattern ``[a-z0-9-]``.  The canonical
    ``product_code`` (e.g. ``HDFCMB+``) is preserved as-is on the
    ``KnowledgeDocument.product_id`` field; only the ``source_id``
    (a Qdrant payload key) uses the slugified form.
    """
    return (
        product_code.lower()
        .replace("+", "-plus")
        .replace("_", "-")
        .replace(" ", "-")
        .strip("-")
    )


def load_credit_card_catalogue(csv_path: str | Path) -> List[KnowledgeDocument]:
    """Convert credit_card_products.csv rows to KnowledgeDocument objects."""
    csv_path = Path(csv_path)
    if not csv_path.is_file():
        raise FileNotFoundError(f"credit card catalogue not found: {csv_path}")

    today = datetime.now().strftime("%Y-%m-%d")
    documents: List[KnowledgeDocument] = []

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("product_status", "").strip().lower() != "active":
                continue

            product_id = row.get("product_code", "").strip()
            product_name = row.get("card_name", "").strip()
            if not product_id or not product_name:
                continue

            source_id = f"catalogue-cc-{_slugify_product_id(product_id)}"
            content = _credit_card_content(row)
            documents.append(
                KnowledgeDocument(
                    source_id=source_id,
                    title=f"{product_name} ({product_id})",
                    content=content,
                    entity="HDFC Bank",
                    category="credit_card",
                    source_url=str(csv_path),
                    source_type="project_catalogue",
                    retrieved_at=today,
                    subcategory=row.get("card_category", "").strip() or None,
                    product_id=product_id,
                    product_name=product_name,
                    metadata={
                        "card_network": row.get("card_network", "").strip(),
                        "card_variant": row.get("card_variant", "").strip(),
                        "form_factor": row.get("card_form_factor", "").strip(),
                        "joining_fee": _num(row.get("joining_fee")),
                        "annual_fee": _num(row.get("annual_fee")),
                        "interest_rate_annual": _num(row.get("interest_rate_annual")),
                        "min_credit_limit": _num(row.get("minimum_credit_limit")),
                        "max_credit_limit": _num(row.get("maximum_credit_limit")),
                        "reward_program": row.get("reward_program_name", "").strip(),
                        "cashback_available": _bool(row.get("cashback_available")),
                        "lounge_access": _bool(row.get("airport_lounge_access")),
                    },
                )
            )

    return documents


def load_loan_catalogue(csv_path: str | Path) -> List[KnowledgeDocument]:
    """Convert loan_products.csv rows to KnowledgeDocument objects."""
    csv_path = Path(csv_path)
    if not csv_path.is_file():
        raise FileNotFoundError(f"loan catalogue not found: {csv_path}")

    today = datetime.now().strftime("%Y-%m-%d")
    documents: List[KnowledgeDocument] = []

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("product_status", "").strip().lower() != "active":
                continue

            product_id = row.get("product_code", "").strip()
            product_name = row.get("product_name", "").strip()
            if not product_id or not product_name:
                continue

            source_id = f"catalogue-ln-{_slugify_product_id(product_id)}"
            content = _loan_content(row)
            documents.append(
                KnowledgeDocument(
                    source_id=source_id,
                    title=f"{product_name} ({product_id})",
                    content=content,
                    entity="HDFC Bank",
                    category="loans",
                    source_url=str(csv_path),
                    source_type="project_catalogue",
                    retrieved_at=today,
                    subcategory=row.get("loan_subcategory", "").strip() or None,
                    product_id=product_id,
                    product_name=product_name,
                    metadata={
                        "loan_type": row.get("loan_type", "").strip(),
                        "secured": row.get("secured_or_unsecured", "").strip(),
                        "min_amount": _num(row.get("minimum_loan_amount")),
                        "max_amount": _num(row.get("maximum_loan_amount")),
                        "tenure_months_min": _num(row.get("minimum_tenure_months")),
                        "tenure_months_max": _num(row.get("maximum_tenure_months")),
                        "interest_rate_min": _num(row.get("interest_rate_min")),
                        "interest_rate_max": _num(row.get("interest_rate_max")),
                        "processing_fee": row.get("processing_fee_value", "").strip(),
                    },
                )
            )

    return documents


# ── Helpers ──────────────────────────────────────────────────────────────────


def _credit_card_content(row: dict) -> str:
    parts = [
        f"## {row.get('card_name', '').strip()}",
        row.get("product_description", "").strip(),
        "",
        "## Key Details",
    ]
    if row.get("card_variant", "").strip():
        parts.append(f"- Variant: {row['card_variant'].strip()}")
    if row.get("card_network", "").strip():
        parts.append(f"- Network: {row['card_network'].strip()}")
    if row.get("card_category", "").strip():
        parts.append(f"- Category: {row['card_category'].strip()}")
    if row.get("interest_rate_annual", "").strip():
        parts.append(f"- Annual Interest Rate: {row['interest_rate_annual'].strip()}%")
    if row.get("joining_fee", "").strip():
        parts.append(f"- Joining Fee: {row['joining_fee'].strip()}")
    if row.get("annual_fee", "").strip():
        parts.append(f"- Annual Fee: {row['annual_fee'].strip()}")
    if row.get("minimum_credit_limit", "").strip():
        parts.append(f"- Min Credit Limit: {row['minimum_credit_limit'].strip()}")
    if row.get("maximum_credit_limit", "").strip():
        parts.append(f"- Max Credit Limit: {row['maximum_credit_limit'].strip()}")

    reward = row.get("reward_program_name", "").strip()
    if reward:
        parts.append(f"- Reward Program: {reward}")
    rp = row.get("reward_points_per_amount", "").strip()
    if rp:
        parts.append(f"- Reward Points: {rp} per amount spent")

    parts.append("")
    parts.append("## Fees & Charges")
    if row.get("cash_withdrawal_fee", "").strip():
        parts.append(f"- Cash Withdrawal Fee: {row['cash_withdrawal_fee'].strip()}")
    if row.get("foreign_currency_markup", "").strip():
        parts.append(f"- Foreign Currency Markup: {row['foreign_currency_markup'].strip()}%")
    if row.get("late_payment_fee", "").strip():
        parts.append(f"- Late Payment Fee: {row['late_payment_fee'].strip()}")

    parts.append("")
    parts.append("## Benefits")
    if _bool(row.get("airport_lounge_access")):
        dv = row.get("domestic_lounge_visits", "").strip()
        iv = row.get("international_lounge_visits", "").strip()
        parts.append(f"- Airport Lounge Access (Domestic: {dv}, International: {iv})")
    if _bool(row.get("travel_benefit")):
        parts.append("- Travel Benefits Available")
    if _bool(row.get("fuel_surcharge_waiver")):
        parts.append("- Fuel Surcharge Waiver")
    if _bool(row.get("cashback_available")):
        cb = row.get("cashback_rate", "").strip()
        parts.append(f"- Cashback Available ({cb}%)" if cb else "- Cashback Available")
    if _bool(row.get("golf_benefit")):
        parts.append("- Golf Benefits")

    parts.append("")
    parts.append("## Eligibility")
    if row.get("minimum_age", "").strip():
        parts.append(f"- Minimum Age: {row['minimum_age'].strip()} years")
    if row.get("maximum_age", "").strip():
        parts.append(f"- Maximum Age: {row['maximum_age'].strip()} years")
    if row.get("eligibility_description", "").strip():
        parts.append(f"- {row['eligibility_description'].strip()}")

    return "\n".join(parts)


def _loan_content(row: dict) -> str:
    parts = [
        f"## {row.get('product_name', '').strip()}",
        row.get("product_description", "").strip(),
        "",
        "## Key Details",
    ]
    lt = row.get("loan_type", "").strip()
    sec = row.get("secured_or_unsecured", "").strip()
    if lt:
        parts.append(f"- Loan Type: {lt}")
    if sec:
        parts.append(f"- Security: {sec}")
    if row.get("loan_category", "").strip():
        parts.append(f"- Category: {row['loan_category'].strip()}")

    parts.append("")
    parts.append("## Amount & Tenure")
    if row.get("minimum_loan_amount", "").strip():
        parts.append(f"- Min Amount: {row['minimum_loan_amount'].strip()}")
    if row.get("maximum_loan_amount", "").strip():
        parts.append(f"- Max Amount: {row['maximum_loan_amount'].strip()}")
    if row.get("minimum_tenure_months", "").strip():
        parts.append(f"- Min Tenure: {row['minimum_tenure_months'].strip()} months")
    if row.get("maximum_tenure_months", "").strip():
        parts.append(f"- Max Tenure: {row['maximum_tenure_months'].strip()} months")

    parts.append("")
    parts.append("## Interest & Fees")
    ir_min = row.get("interest_rate_min", "").strip()
    ir_max = row.get("interest_rate_max", "").strip()
    if ir_min and ir_max:
        parts.append(f"- Interest Rate: {ir_min}% - {ir_max}%")
    elif ir_min:
        parts.append(f"- Interest Rate: {ir_min}%")
    if row.get("processing_fee_value", "").strip():
        pft = row.get("processing_fee_type", "").strip()
        parts.append(
            f"- Processing Fee: {row['processing_fee_value'].strip()}"
            f"{f' ({pft})' if pft else ''}"
        )

    parts.append("")
    parts.append("## Eligibility")
    if row.get("minimum_age", "").strip():
        parts.append(f"- Minimum Age: {row['minimum_age'].strip()} years")
    if row.get("maximum_age", "").strip():
        parts.append(f"- Maximum Age: {row['maximum_age'].strip()} years")
    if row.get("minimum_income_monthly", "").strip():
        parts.append(f"- Min Monthly Income: {row['minimum_income_monthly'].strip()}")
    if row.get("minimum_credit_score", "").strip():
        parts.append(f"- Min Credit Score: {row['minimum_credit_score'].strip()}")

    parts.append("")
    parts.append("## Features")
    if _bool(row.get("prepayment_allowed")):
        parts.append("- Prepayment Allowed")
    if _bool(row.get("foreclosure_allowed")):
        parts.append("- Foreclosure Allowed")
    if _bool(row.get("balance_transfer_available")):
        parts.append("- Balance Transfer Available")
    if _bool(row.get("digital_application")):
        parts.append("- Online Application Available")
    if _bool(row.get("instant_approval")):
        parts.append("- Instant Approval Available")

    return "\n".join(parts)


def _num(value: str | None) -> str | None:
    if not value or not value.strip():
        return None
    v = value.strip()
    try:
        float(v)
    except ValueError:
        return v if v.lower() not in ("", "not applicable", "n/a", "0") else None
    return v


def _bool(value: str | None) -> bool:
    if not value:
        return False
    v = value.strip().lower()
    return v in ("1", "yes", "true")
