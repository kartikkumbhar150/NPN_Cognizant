"""Tests for the product grounding service allowlist and catalogue versioning."""

import csv
import json
from pathlib import Path

import pytest

from app.models.personalization import ProductFamily
from app.models.product import GroundedFactCategory, ProductStatus
from app.repositories.product_catalogue import CsvCreditCardCatalogueRepository, REQUIRED_COLUMNS
from app.services.product_grounding import ProductGroundingService, ProductInactiveError

# Stable fact IDs the first-slice allowlist may emit.
ALLOWED_FACT_IDS = frozenset(
    {
        "product_id",
        "product_name",
        "product_type",
        "status",
        "joining_fee",
        "annual_fee",
        "reward_program_name",
        "reward_rate",
        "accelerated_rewards",
        "domestic_lounge_visits",
        "international_lounge_visits",
        "travel_portal",
        "dining_discount",
    }
)

# Raw / internal / eligibility / credit fields that must never leave grounding.
FORBIDDEN_STRINGS = (
    "minimum_credit_limit",
    "maximum_credit_limit",
    "interest_rate_annual",
    "interest_rate_monthly",
    "eligibility_description",
    "minimum_income_annual",
    "employment_type",
    "renewal_fee_waiver",
    "product_code",
    "created_at",
    "updated_at",
    "lounge_spend_requirement",
    "priority_pass_visits",
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


def make_service(tmp_path: Path, rows: list[dict[str, str]], filename: str = "catalogue.csv"):
    path = write_csv(tmp_path, rows, filename)
    return ProductGroundingService(CsvCreditCardCatalogueRepository(path))


def ground(service: ProductGroundingService, product_id: str = "CC014"):
    return service.ground(ProductFamily.CREDIT_CARD, product_id)


# --------------------------------------------------------------------------
# CC014 grounding identity
# --------------------------------------------------------------------------


def test_cc014_grounding_identity(tmp_path):
    service = make_service(tmp_path, [cc_row()])
    grounded = ground(service, "CC014")

    assert grounded.product_id == "CC014"
    assert grounded.product_family is ProductFamily.CREDIT_CARD
    assert grounded.product_name == "Regalia Gold"
    assert grounded.product_type == "Super Premium"
    assert grounded.status is ProductStatus.ACTIVE
    assert grounded.catalogue_version.startswith("sha256:")
    assert len(grounded.catalogue_version) == len("sha256:") + 64


# --------------------------------------------------------------------------
# Allowlist
# --------------------------------------------------------------------------


def test_facts_are_allowlisted_only(tmp_path):
    service = make_service(tmp_path, [cc_row()])
    grounded = ground(service, "CC014")

    fact_ids = {fact.fact_id for fact in grounded.facts}
    assert fact_ids <= ALLOWED_FACT_IDS
    # Sanity: the positive CC014 facts we expect are present.
    assert "product_name" in fact_ids
    assert "annual_fee" in fact_ids
    assert "domestic_lounge_visits" in fact_ids


def test_raw_and_internal_columns_never_leave_grounding(tmp_path):
    service = make_service(tmp_path, [cc_row()])
    grounded = ground(service, "CC014")

    blob = json.dumps(grounded.model_dump(mode="json"))
    for forbidden in FORBIDDEN_STRINGS:
        assert forbidden not in blob, f"non-allowlisted field leaked: {forbidden}"


def test_every_fact_is_definite_and_positive(tmp_path):
    service = make_service(tmp_path, [cc_row()])
    grounded = ground(service, "CC014")

    for fact in grounded.facts:
        assert fact.value not in {"0", "No", "Not Applicable", "999"}
        assert fact.category in GroundedFactCategory


# --------------------------------------------------------------------------
# Travel facts
# --------------------------------------------------------------------------


def test_only_genuinely_positive_travel_facts_surface(tmp_path):
    service = make_service(tmp_path, [cc_row()])
    grounded = ground(service, "CC014")
    facts = {fact.fact_id: fact.value for fact in grounded.facts}

    # Clearly enabled: 12 domestic lounge visits.
    assert facts["domestic_lounge_visits"] == "12"
    # Travel redemption via SmartBuy portal.
    assert facts["travel_portal"] == "SmartBuy"
    # International lounge access=Yes but visits=0 and no Priority Pass:
    # contradictory data must not surface as a positive claim.
    assert "international_lounge_visits" not in facts


# --------------------------------------------------------------------------
# Zero / negative / sentinel values
# --------------------------------------------------------------------------


def test_zero_values_never_become_positive_claims(tmp_path):
    # Default row already carries zero/disabled benefit fields.
    service = make_service(tmp_path, [cc_row()])
    grounded = ground(service, "CC014")
    fact_ids = {fact.fact_id for fact in grounded.facts}

    assert "priority_pass_visits" not in fact_ids
    assert "international_lounge_visits" not in fact_ids
    assert all("cashback" not in fact_id for fact_id in fact_ids)


def test_999_sentinel_not_interpreted_as_unlimited(tmp_path):
    service = make_service(
        tmp_path,
        [cc_row(overrides={"airport_lounge_access": "Yes", "domestic_lounge_visits": "999"})],
    )
    grounded = ground(service, "CC014")

    fact_ids = {fact.fact_id for fact in grounded.facts}
    # The count is an undocumented sentinel: omitted, never surfaced as unlimited.
    assert "domestic_lounge_visits" not in fact_ids
    for fact in grounded.facts:
        assert "unlimited" not in fact.value.lower()


def test_zero_reward_rate_omitted(tmp_path):
    service = make_service(tmp_path, [cc_row(overrides={"base_reward_points": "0"})])
    grounded = ground(service, "CC014")
    fact_ids = {fact.fact_id for fact in grounded.facts}
    assert "reward_rate" not in fact_ids


# --------------------------------------------------------------------------
# Descriptions
# --------------------------------------------------------------------------


def test_generic_description_omitted(tmp_path):
    service = make_service(tmp_path, [cc_row()])
    grounded = ground(service, "CC014")
    assert grounded.approved_description is None


def test_product_specific_description_included(tmp_path):
    specific = "Premium travel rewards card with airport lounge access and dining discounts."
    service = make_service(tmp_path, [cc_row(overrides={"product_description": specific})])
    grounded = ground(service, "CC014")
    assert grounded.approved_description == specific


# --------------------------------------------------------------------------
# Tags
# --------------------------------------------------------------------------


def test_positive_tags_only(tmp_path):
    service = make_service(tmp_path, [cc_row()])
    grounded = ground(service, "CC014")

    assert grounded.product_tags == [
        "AIRPORT_LOUNGE",
        "DINING",
        "GOLF",
        "LIFESTYLE",
        "PREMIUM",
        "REWARDS",
        "SHOPPING",
        "TRAVEL",
    ]
    # tag_international=0 in the real row: no INTERNATIONAL tag is invented.
    assert "INTERNATIONAL" not in grounded.product_tags


# --------------------------------------------------------------------------
# Catalogue versioning
# --------------------------------------------------------------------------


def test_catalogue_version_is_deterministic(tmp_path):
    path = write_csv(tmp_path, [cc_row()])
    service_a = ProductGroundingService(CsvCreditCardCatalogueRepository(path))
    service_b = ProductGroundingService(CsvCreditCardCatalogueRepository(path))

    version_a1 = ground(service_a, "CC014").catalogue_version
    version_a2 = ground(service_a, "CC014").catalogue_version
    version_b = ground(service_b, "CC014").catalogue_version

    assert version_a1 == version_a2 == version_b
    assert version_a1.startswith("sha256:")


def test_catalogue_version_changes_with_grounded_fact(tmp_path):
    service_a = make_service(tmp_path, [cc_row()], filename="a.csv")
    service_b = make_service(tmp_path, [cc_row(overrides={"annual_fee": "3000"})], filename="b.csv")

    version_a = ground(service_a, "CC014").catalogue_version
    version_b = ground(service_b, "CC014").catalogue_version
    assert version_a != version_b


def test_catalogue_version_insensitive_to_non_grounded_fields(tmp_path):
    service_a = make_service(tmp_path, [cc_row()], filename="a.csv")
    service_b = make_service(
        tmp_path, [cc_row(overrides={"renewal_fee_waiver": "999999"})], filename="b.csv"
    )

    version_a = ground(service_a, "CC014").catalogue_version
    version_b = ground(service_b, "CC014").catalogue_version
    # renewal_fee_waiver is parsed but never grounded -> must not change the hash.
    assert version_a == version_b


# --------------------------------------------------------------------------
# Inactive / expired products
# --------------------------------------------------------------------------


def test_inactive_product_rejected(tmp_path):
    service = make_service(tmp_path, [cc_row(overrides={"product_status": "Inactive"})])
    with pytest.raises(ProductInactiveError) as excinfo:
        ground(service, "CC014")
    assert excinfo.value.code == "PRODUCT_INACTIVE"


def test_expired_product_rejected(tmp_path):
    service = make_service(tmp_path, [cc_row(overrides={"end_date": "2020-01-01"})])
    with pytest.raises(ProductInactiveError) as excinfo:
        ground(service, "CC014")
    assert excinfo.value.code == "PRODUCT_INACTIVE"
