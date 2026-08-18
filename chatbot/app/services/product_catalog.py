"""Deterministic NBO ↔ Qdrant product-ID resolver.

Two identifier systems coexist:
- NBO pipeline: ``credit_card_product_id`` (CC001…) / ``loan_product_id`` (LN001…)
- RAG catalogue: ``product_code`` (HDFC_FREEDOM, HDFCMB+…) stored as ``product_id`` in Qdrant

This resolver bridges them deterministically — 1:1, no fuzzy matching,
no embeddings, no LLM.  A missing mapping is an explicit failure state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

import pandas as pd

_CANONICAL_ID_COLUMN = "product_code"
_TYPE_COLUMNS: Dict[str, tuple] = {
    "credit_card": ("credit_card_product_id", "card_name"),
    "loan": ("loan_product_id", "product_name"),
}
SUPPORTED_PRODUCT_TYPES = frozenset(_TYPE_COLUMNS.keys())


class ProductResolutionError(Exception):
    """Base class for product-ID resolution failures."""


class ProductCatalogError(ProductResolutionError):
    """A catalogue DataFrame is structurally unusable."""


class AmbiguousMappingError(ProductResolutionError):
    """An ID maps to conflicting targets; mapping must be 1:1."""


class UnsupportedProductTypeError(ProductResolutionError):
    """The product type has no verified mapping."""


@dataclass(frozen=True)
class ProductIdentity:
    """Immutable link between the two identifier systems."""

    nbo_product_id: str
    canonical_product_id: str
    product_name: str
    product_type: str


class ProductIdResolver:
    """Strict, deterministic NBO-ID → canonical-ID resolver.

    Built from injected catalogue DataFrames.
    """

    def __init__(self, credit_cards_df: pd.DataFrame, loans_df: pd.DataFrame) -> None:
        self._nbo_to_identity: Dict[tuple, ProductIdentity] = {}
        self._canonical_to_identity: Dict[str, ProductIdentity] = {}
        self._build(credit_cards_df, "credit_card")
        self._build(loans_df, "loan")

    def resolve_nbo_id(self, nbo_product_id: str, product_type: str) -> Optional[ProductIdentity]:
        """Resolve an NBO product ID to its full identity, or ``None``."""
        self._require_supported_type(product_type)
        if not isinstance(nbo_product_id, str):
            return None
        return self._nbo_to_identity.get((product_type, nbo_product_id.strip()))

    def resolve_canonical_id(self, canonical_product_id: str) -> Optional[ProductIdentity]:
        if not isinstance(canonical_product_id, str):
            return None
        return self._canonical_to_identity.get(canonical_product_id.strip())

    @property
    def mapping_count(self) -> int:
        return len(self._nbo_to_identity)

    def list_mappings(self) -> Sequence[ProductIdentity]:
        return list(self._nbo_to_identity.values())

    @staticmethod
    def supported_product_types() -> frozenset:
        return SUPPORTED_PRODUCT_TYPES

    def _build(self, df: pd.DataFrame, product_type: str) -> None:
        nbo_id_col, name_col = _TYPE_COLUMNS[product_type]
        if df is None:
            raise ProductCatalogError(f"{product_type} catalogue DataFrame is None")
        missing_cols = [col for col in (nbo_id_col, _CANONICAL_ID_COLUMN, name_col) if col not in df.columns]
        if missing_cols:
            raise ProductCatalogError(
                f"{product_type} catalogue missing columns {missing_cols}"
            )
        for _, row in df.iterrows():
            nbo_id = _clean(row.get(nbo_id_col))
            canonical_id = _clean(row.get(_CANONICAL_ID_COLUMN))
            product_name = _clean(row.get(name_col))
            if not nbo_id or not canonical_id:
                continue
            existing_nbo = self._nbo_to_identity.get((product_type, nbo_id))
            if existing_nbo is not None:
                if existing_nbo.canonical_product_id != canonical_id:
                    raise AmbiguousMappingError(
                        f"NBO ID {nbo_id!r} maps to conflicting canonical IDs "
                        f"{existing_nbo.canonical_product_id!r} and {canonical_id!r}"
                    )
                continue
            existing_canonical = self._canonical_to_identity.get(canonical_id)
            if existing_canonical is not None:
                raise AmbiguousMappingError(
                    f"canonical ID {canonical_id!r} claimed by {existing_canonical.nbo_product_id!r} "
                    f"and {nbo_id!r}"
                )
            identity = ProductIdentity(
                nbo_product_id=nbo_id, canonical_product_id=canonical_id,
                product_name=product_name, product_type=product_type,
            )
            self._nbo_to_identity[(product_type, nbo_id)] = identity
            self._canonical_to_identity[canonical_id] = identity

    @staticmethod
    def _require_supported_type(product_type: str) -> None:
        if product_type not in SUPPORTED_PRODUCT_TYPES:
            raise UnsupportedProductTypeError(
                f"product type {product_type!r} has no verified mapping; "
                f"supported: {sorted(SUPPORTED_PRODUCT_TYPES)}"
            )


def _clean(value) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).strip()
