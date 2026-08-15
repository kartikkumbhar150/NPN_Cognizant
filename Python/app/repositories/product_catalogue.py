"""Credit-card catalogue repository backed by the prototype CSV.

The CSV remains the single source of truth for the first prototype
repository. This module:

* resolves the catalogue path relative to the module (never the shell cwd)
* parses rows into the typed ``CreditCardProduct`` model
* looks up by exact product ID only — no fuzzy or fallback selection
* raises domain exceptions instead of leaking raw ``KeyError``/``IndexError``
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
from typing import Protocol

from app.models.product import CreditCardProduct, ProductStatus

# Python/app/repositories/product_catalogue.py -> Python/
_DEFAULT_CSV_PATH = Path(__file__).resolve().parents[2] / "Database_csvs" / "credit_card_products.csv"


class CatalogueError(Exception):
    """Base class for catalogue domain errors."""

    code = "CATALOGUE_ERROR"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ProductNotFoundError(CatalogueError):
    """The requested product ID is not present in the catalogue."""

    code = "PRODUCT_NOT_FOUND"

    def __init__(self, product_id: str) -> None:
        super().__init__(f"product not found in catalogue: {product_id!r}")
        self.product_id = product_id


class CatalogueInvalidError(CatalogueError):
    """The catalogue file is missing, malformed, or unreadable."""

    code = "CATALOGUE_INVALID"


class DuplicateProductIdError(CatalogueError):
    """The catalogue contains more than one row with the same product ID."""

    code = "DUPLICATE_PRODUCT_ID"

    def __init__(self, product_id: str) -> None:
        super().__init__(f"duplicate product id in catalogue: {product_id!r}")
        self.product_id = product_id


class ProductCatalogueRepository(Protocol):
    """Contract for a credit-card catalogue source."""

    def get_credit_card_by_id(self, product_id: str) -> CreditCardProduct: ...


# Columns this repository parses. Missing required columns -> CATALOGUE_INVALID.
REQUIRED_COLUMNS: tuple[str, ...] = (
    "credit_card_product_id",
    "product_code",
    "card_name",
    "card_variant",
    "card_category",
    "card_type",
    "card_network",
    "product_status",
    "product_description",
    "joining_fee",
    "annual_fee",
    "renewal_fee",
    "renewal_fee_waiver",
    "reward_program_name",
    "base_reward_points",
    "reward_points_per_amount",
    "accelerated_reward_available",
    "accelerated_reward_details",
    "travel_benefit",
    "airport_lounge_access",
    "domestic_lounge_visits",
    "international_lounge_access",
    "international_lounge_visits",
    "priority_pass_available",
    "priority_pass_visits",
    "travel_redemption_available",
    "travel_portal",
    "dining_benefit",
    "dining_discount",
    "tag_travel",
    "tag_shopping",
    "tag_dining",
    "tag_fuel",
    "tag_online_shopping",
    "tag_international",
    "tag_airport_lounge",
    "tag_rewards",
    "tag_cashback",
    "tag_premium",
    "tag_lifestyle",
    "tag_golf",
    "tag_movie",
    "tag_upi",
    "tag_business",
    "end_date",
)


def _text(row: dict[str, str], column: str) -> str:
    value = row.get(column)
    if value is None:
        raise CatalogueInvalidError(f"missing value for column {column!r}")
    return value.strip()


def _required_text(row: dict[str, str], column: str) -> str:
    value = _text(row, column)
    if not value:
        raise CatalogueInvalidError(f"empty value in required column {column!r}")
    return value


def _int(row: dict[str, str], column: str) -> int:
    value = _text(row, column)
    if value in ("", "Not Applicable"):
        return 0
    try:
        return int(value)
    except ValueError as exc:
        raise CatalogueInvalidError(f"invalid integer in column {column!r}: {value!r}") from exc


def _flag(row: dict[str, str], column: str) -> bool:
    """Boolean-ish benefit flag. Only positive values count; anything else is False."""
    return _text(row, column).casefold() in {"yes", "true", "1"}


def _tag(row: dict[str, str], column: str) -> bool:
    value = _text(row, column)
    if value == "1":
        return True
    if value in ("0", "", "Not Applicable"):
        return False
    raise CatalogueInvalidError(f"invalid tag value in column {column!r}: {value!r}")


def _date(row: dict[str, str], column: str) -> date | None:
    value = _text(row, column)
    if value in ("", "Not Applicable"):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise CatalogueInvalidError(f"invalid date in column {column!r}: {value!r}") from exc


def _status(row: dict[str, str], column: str) -> ProductStatus:
    value = _text(row, column)
    return ProductStatus.ACTIVE if value.casefold() == "active" else ProductStatus.INACTIVE


def _parse_row(row: dict[str, str]) -> CreditCardProduct:
    return CreditCardProduct(
        product_id=_required_text(row, "credit_card_product_id"),
        product_code=_text(row, "product_code"),
        card_name=_required_text(row, "card_name"),
        card_variant=_text(row, "card_variant"),
        card_category=_text(row, "card_category"),
        card_type=_text(row, "card_type"),
        card_network=_text(row, "card_network"),
        product_status=_status(row, "product_status"),
        product_description=_text(row, "product_description"),
        joining_fee=_int(row, "joining_fee"),
        annual_fee=_int(row, "annual_fee"),
        renewal_fee=_int(row, "renewal_fee"),
        renewal_fee_waiver=_int(row, "renewal_fee_waiver"),
        reward_program_name=_text(row, "reward_program_name"),
        base_reward_points=_int(row, "base_reward_points"),
        reward_points_per_amount=_int(row, "reward_points_per_amount"),
        accelerated_reward_available=_flag(row, "accelerated_reward_available"),
        accelerated_reward_details=_text(row, "accelerated_reward_details"),
        travel_benefit=_flag(row, "travel_benefit"),
        airport_lounge_access=_flag(row, "airport_lounge_access"),
        domestic_lounge_visits=_int(row, "domestic_lounge_visits"),
        international_lounge_access=_flag(row, "international_lounge_access"),
        international_lounge_visits=_int(row, "international_lounge_visits"),
        priority_pass_available=_flag(row, "priority_pass_available"),
        priority_pass_visits=_int(row, "priority_pass_visits"),
        travel_redemption_available=_flag(row, "travel_redemption_available"),
        travel_portal=_text(row, "travel_portal"),
        dining_benefit=_flag(row, "dining_benefit"),
        dining_discount=_int(row, "dining_discount"),
        tag_travel=_tag(row, "tag_travel"),
        tag_shopping=_tag(row, "tag_shopping"),
        tag_dining=_tag(row, "tag_dining"),
        tag_fuel=_tag(row, "tag_fuel"),
        tag_online_shopping=_tag(row, "tag_online_shopping"),
        tag_international=_tag(row, "tag_international"),
        tag_airport_lounge=_tag(row, "tag_airport_lounge"),
        tag_rewards=_tag(row, "tag_rewards"),
        tag_cashback=_tag(row, "tag_cashback"),
        tag_premium=_tag(row, "tag_premium"),
        tag_lifestyle=_tag(row, "tag_lifestyle"),
        tag_golf=_tag(row, "tag_golf"),
        tag_movie=_tag(row, "tag_movie"),
        tag_upi=_tag(row, "tag_upi"),
        tag_business=_tag(row, "tag_business"),
        end_date=_date(row, "end_date"),
    )


class CsvCreditCardCatalogueRepository:
    """Loads and indexes the prototype credit-card CSV.

    ``csv_path`` defaults to the prototype catalogue resolved relative to this
    module, so behaviour never depends on the shell's current directory.
    An explicit path may be injected (used by tests with temporary fixtures).
    """

    def __init__(self, csv_path: Path | None = None) -> None:
        self._csv_path = Path(csv_path) if csv_path is not None else _DEFAULT_CSV_PATH
        self._products: dict[str, CreditCardProduct] | None = None

    def get_credit_card_by_id(self, product_id: str) -> CreditCardProduct:
        products = self._load()
        try:
            return products[product_id]
        except KeyError:
            raise ProductNotFoundError(product_id) from None

    def _load(self) -> dict[str, CreditCardProduct]:
        if self._products is None:
            self._products = self._read_catalogue()
        return self._products

    def _read_catalogue(self) -> dict[str, CreditCardProduct]:
        if not self._csv_path.is_file():
            raise CatalogueInvalidError(f"catalogue file not found: {self._csv_path}")

        try:
            with self._csv_path.open(newline="", encoding="utf-8") as fh:
                reader = csv.DictReader(fh)
                if reader.fieldnames is None:
                    raise CatalogueInvalidError(f"catalogue has no header: {self._csv_path}")
                missing = [column for column in REQUIRED_COLUMNS if column not in reader.fieldnames]
                if missing:
                    raise CatalogueInvalidError(
                        f"catalogue missing required columns: {', '.join(missing)}"
                    )

                products: dict[str, CreditCardProduct] = {}
                for row in reader:
                    product = _parse_row(row)
                    if product.product_id in products:
                        raise DuplicateProductIdError(product.product_id)
                    products[product.product_id] = product
        except (OSError, csv.Error, UnicodeDecodeError) as exc:
            raise CatalogueInvalidError(f"failed to read catalogue {self._csv_path}: {exc}") from exc

        if not products:
            raise CatalogueInvalidError(f"catalogue is empty: {self._csv_path}")
        return products
