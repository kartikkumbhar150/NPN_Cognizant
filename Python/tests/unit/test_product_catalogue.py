"""Tests for the credit-card catalogue repository."""

import csv
from pathlib import Path

import pytest

from app.models.product import ProductStatus
from app.repositories.product_catalogue import (
    CatalogueInvalidError,
    CsvCreditCardCatalogueRepository,
    DuplicateProductIdError,
    ProductNotFoundError,
    REQUIRED_COLUMNS,
)


def cc_row(overrides: dict[str, str] | None = None, product_id: str = "CC014") -> dict[str, str]:
    """A full catalogue row mirroring the real CC014 (Regalia Gold) values."""
    row = {
        "credit_card_product_id": product_id,
        "product_code": "HDFC_REGALIA_GOLD",
        "card_name": "Regalia Gold",
        "card_variant": "Super Premium",
        "card_category": "Super Premium",
        "card_type": "Personal",
        "card_network": "Visa",
        "product_status": "Active",
        "product_description": "HDFC Bank credit card product.",
        "joining_fee": "2500",
        "annual_fee": "2500",
        "renewal_fee": "2500",
        "renewal_fee_waiver": "300000",
        "reward_program_name": "Reward Points",
        "base_reward_points": "4",
        "reward_points_per_amount": "150",
        "accelerated_reward_available": "Yes",
        "accelerated_reward_details": "Accelerated rewards on selected SmartBuy and partner spends.",
        "travel_benefit": "Yes",
        "airport_lounge_access": "Yes",
        "domestic_lounge_visits": "12",
        "international_lounge_access": "Yes",
        "international_lounge_visits": "0",
        "priority_pass_available": "No",
        "priority_pass_visits": "0",
        "travel_redemption_available": "Yes",
        "travel_portal": "SmartBuy",
        "dining_benefit": "Yes",
        "dining_discount": "10",
        "tag_travel": "1",
        "tag_shopping": "1",
        "tag_dining": "1",
        "tag_fuel": "0",
        "tag_online_shopping": "0",
        "tag_international": "0",
        "tag_airport_lounge": "1",
        "tag_rewards": "1",
        "tag_cashback": "0",
        "tag_premium": "1",
        "tag_lifestyle": "1",
        "tag_golf": "1",
        "tag_movie": "0",
        "tag_upi": "0",
        "tag_business": "0",
        "end_date": "2099-12-31",
    }
    if overrides:
        row.update(overrides)
    return row


def write_csv(tmp_path: Path, rows: list[dict[str, str]], filename: str = "catalogue.csv") -> Path:
    path = tmp_path / filename
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)
    return path


# --------------------------------------------------------------------------
# Lookup behaviour
# --------------------------------------------------------------------------


def test_get_existing_product_by_exact_id():
    repository = CsvCreditCardCatalogueRepository()
    product = repository.get_credit_card_by_id("CC014")

    assert product.product_id == "CC014"
    assert product.card_name == "Regalia Gold"
    assert product.product_status is ProductStatus.ACTIVE
    assert product.annual_fee == 2500
    assert product.domestic_lounge_visits == 12


def test_missing_product_raises_domain_error():
    repository = CsvCreditCardCatalogueRepository()
    with pytest.raises(ProductNotFoundError) as excinfo:
        repository.get_credit_card_by_id("DOES_NOT_EXIST")
    assert excinfo.value.code == "PRODUCT_NOT_FOUND"
    assert excinfo.value.product_id == "DOES_NOT_EXIST"


def test_exact_id_selection_no_fallback(tmp_path):
    """Lookup must return exactly the requested product, never a 'first match'."""
    path = write_csv(tmp_path, [cc_row(product_id="CC001"), cc_row(product_id="CC014")])
    repository = CsvCreditCardCatalogueRepository(path)

    assert repository.get_credit_card_by_id("CC014").product_id == "CC014"
    assert repository.get_credit_card_by_id("CC001").product_id == "CC001"
    # No fuzzy/partial matching either.
    with pytest.raises(ProductNotFoundError):
        repository.get_credit_card_by_id("CC01")


# --------------------------------------------------------------------------
# Duplicate protection
# --------------------------------------------------------------------------


def test_duplicate_product_id_rejected(tmp_path):
    path = write_csv(
        tmp_path,
        [
            cc_row(product_id="CC014"),
            cc_row(product_id="CC014", overrides={"card_name": "Duplicate Card"}),
        ],
    )
    repository = CsvCreditCardCatalogueRepository(path)
    with pytest.raises(DuplicateProductIdError) as excinfo:
        repository.get_credit_card_by_id("CC014")
    assert excinfo.value.code == "DUPLICATE_PRODUCT_ID"
    assert excinfo.value.product_id == "CC014"


# --------------------------------------------------------------------------
# Path robustness
# --------------------------------------------------------------------------


def test_repository_independent_of_shell_cwd(tmp_path, monkeypatch):
    """Default path resolution must not depend on where the process runs."""
    monkeypatch.chdir(tmp_path)
    repository = CsvCreditCardCatalogueRepository()
    assert repository.get_credit_card_by_id("CC014").product_id == "CC014"


def test_injected_catalogue_path_used(tmp_path):
    path = write_csv(tmp_path, [cc_row(product_id="CC900")])
    repository = CsvCreditCardCatalogueRepository(path)
    assert repository.get_credit_card_by_id("CC900").product_id == "CC900"
    with pytest.raises(ProductNotFoundError):
        repository.get_credit_card_by_id("CC014")


# --------------------------------------------------------------------------
# Malformed catalogues
# --------------------------------------------------------------------------


def test_missing_catalogue_file_raises(tmp_path):
    repository = CsvCreditCardCatalogueRepository(tmp_path / "does-not-exist.csv")
    with pytest.raises(CatalogueInvalidError) as excinfo:
        repository.get_credit_card_by_id("CC014")
    assert excinfo.value.code == "CATALOGUE_INVALID"


def test_missing_required_column_raises(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("credit_card_product_id,card_name\nCC014,Regalia Gold\n", encoding="utf-8")
    repository = CsvCreditCardCatalogueRepository(path)
    with pytest.raises(CatalogueInvalidError):
        repository.get_credit_card_by_id("CC014")


def test_empty_catalogue_raises(tmp_path):
    path = write_csv(tmp_path, [])
    repository = CsvCreditCardCatalogueRepository(path)
    with pytest.raises(CatalogueInvalidError):
        repository.get_credit_card_by_id("CC014")
