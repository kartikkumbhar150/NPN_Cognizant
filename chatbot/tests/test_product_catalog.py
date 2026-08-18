"""Data-driven tests: product catalog resolution (NBO ↔ canonical IDs).

Counts come from the real CSVs — never hardcoded — so catalogue growth
can never silently invalidate the suite.
"""

from __future__ import annotations

import pandas as pd
import pytest

from chatbot.app.services.product_catalog import (
    AmbiguousMappingError,
    ProductCatalogError,
    ProductIdResolver,
    UnsupportedProductTypeError,
)


def test_mapping_count_matches_catalogue(credit_cards_df, loans_df):
    resolver = ProductIdResolver(credit_cards_df, loans_df)
    expected = len(credit_cards_df) + len(loans_df)
    assert resolver.mapping_count == expected


def test_every_credit_card_resolves(credit_cards_df, loans_df):
    resolver = ProductIdResolver(credit_cards_df, loans_df)
    for _, row in credit_cards_df.iterrows():
        nbo_id = str(row["credit_card_product_id"]).strip()
        identity = resolver.resolve_nbo_id(nbo_id, "credit_card")
        assert identity is not None, f"unresolved: {nbo_id}"
        assert identity.canonical_product_id == str(row["product_code"]).strip()
        assert identity.product_name == str(row["card_name"]).strip()


def test_every_loan_resolves(credit_cards_df, loans_df):
    resolver = ProductIdResolver(credit_cards_df, loans_df)
    for _, row in loans_df.iterrows():
        nbo_id = str(row["loan_product_id"]).strip()
        identity = resolver.resolve_nbo_id(nbo_id, "loan")
        assert identity is not None, f"unresolved: {nbo_id}"
        assert identity.canonical_product_id == str(row["product_code"]).strip()


def test_reverse_resolution_is_consistent(credit_cards_df, loans_df):
    resolver = ProductIdResolver(credit_cards_df, loans_df)
    for identity in resolver.list_mappings():
        back = resolver.resolve_canonical_id(identity.canonical_product_id)
        assert back is not None
        assert back.nbo_product_id == identity.nbo_product_id


def test_unknown_ids_return_none(credit_cards_df, loans_df):
    resolver = ProductIdResolver(credit_cards_df, loans_df)
    assert resolver.resolve_nbo_id("CC99999", "credit_card") is None
    assert resolver.resolve_nbo_id("LN99999", "loan") is None
    assert resolver.resolve_canonical_id("NO_SUCH_CODE") is None


def test_ids_are_trimmed(credit_cards_df, loans_df):
    resolver = ProductIdResolver(credit_cards_df, loans_df)
    first_card = str(credit_cards_df.iloc[0]["credit_card_product_id"]).strip()
    assert resolver.resolve_nbo_id(f"  {first_card}  ", "credit_card") is not None


class TestHdfcmbSlug:
    """HDFCMB+ canonical code resolves to its NBO row (the '+' product)."""

    def test_hdfcmb_plus_resolves(self, credit_cards_df, loans_df):
        codes = set(credit_cards_df["product_code"].astype(str).str.strip())
        if "HDFCMB+" not in codes:
            pytest.skip("HDFCMB+ not present in this catalogue snapshot")
        resolver = ProductIdResolver(credit_cards_df, loans_df)
        identity = resolver.resolve_canonical_id("HDFCMB+")
        assert identity is not None
        assert identity.product_type == "credit_card"
        assert identity.nbo_product_id  # e.g. CC002


class TestStrictness:
    def _mini_cards(self, code="A1", nbo="CC001"):
        return pd.DataFrame([{
            "credit_card_product_id": nbo, "product_code": code,
            "card_name": "Card A",
        }])

    def _mini_loans(self):
        return pd.DataFrame([{
            "loan_product_id": "LN001", "product_code": "L1",
            "product_name": "Loan A",
        }])

    def test_missing_column_raises(self):
        bad = pd.DataFrame([{"credit_card_product_id": "CC001"}])
        with pytest.raises(ProductCatalogError):
            ProductIdResolver(bad, self._mini_loans())

    def test_conflicting_canonical_raises(self):
        # Two card rows claiming the same product_code with different NBO IDs.
        conflicting = pd.DataFrame([
            {"credit_card_product_id": "CC001", "product_code": "A1", "card_name": "A"},
            {"credit_card_product_id": "CC002", "product_code": "A1", "card_name": "A"},
        ])
        with pytest.raises(AmbiguousMappingError):
            ProductIdResolver(conflicting, self._mini_loans())

    def test_duplicate_identical_rows_are_idempotent(self):
        dup = pd.DataFrame([
            {"credit_card_product_id": "CC001", "product_code": "A1", "card_name": "A"},
            {"credit_card_product_id": "CC001", "product_code": "A1", "card_name": "A"},
        ])
        resolver = ProductIdResolver(dup, self._mini_loans())
        assert resolver.mapping_count == 2

    def test_unsupported_type_raises(self):
        resolver = ProductIdResolver(self._mini_cards(), self._mini_loans())
        with pytest.raises(UnsupportedProductTypeError):
            resolver.resolve_nbo_id("CC001", "insurance")
