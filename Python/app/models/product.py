"""Catalogue and grounding models for Phase 6 product grounding.

Two layers live here:

1. ``CreditCardProduct`` — a typed internal representation of one credit-card
   catalogue row. This is the *raw* catalogue layer: it holds the fields the
   repository needs, including fields that must never reach GenAI.

2. ``GroundedProductFacts`` / ``GroundedFact`` — the strict allowlisted
   projection that is the only thing allowed to leave the grounding boundary.

Boundary rule (never violated):

    Raw Catalogue Row -> explicit allowlist -> GroundedProductFacts

A raw CSV row is never passed to a future LLM prompt.
"""

from datetime import date
from enum import Enum

from pydantic import Field

from app.models.personalization import ProductFamily, StrictModel


class ProductStatus(str, Enum):
    """Lifecycle status of a catalogue product."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class GroundedFactCategory(str, Enum):
    """Categories a grounded fact may belong to."""

    IDENTITY = "IDENTITY"
    DESCRIPTION = "DESCRIPTION"
    TRAVEL = "TRAVEL"
    FEES = "FEES"
    REWARDS = "REWARDS"
    DINING = "DINING"


# --------------------------------------------------------------------------
# Raw catalogue layer (internal only)
# --------------------------------------------------------------------------


class CreditCardProduct(StrictModel):
    """Typed representation of one credit-card catalogue row.

    Parsed explicitly by the repository. Fields here are a curated subset of
    the CSV: identity/status/date fields plus the allowlist-candidate fields.
    Anything not parsed here (eligibility, credit limits, interest rates,
    timestamps, co-brand data, cashback, fuel/golf/movie benefits, etc.)
    simply cannot be grounded.

    ``renewal_fee_waiver`` is parsed but intentionally **not** grounded: in the
    prototype CSV its values (e.g. 300000) are spend thresholds for fee
    waiver, a semantic the catalogue does not document in a citable way.
    """

    product_id: str
    product_code: str
    card_name: str
    card_variant: str
    card_category: str
    card_type: str
    card_network: str
    product_status: ProductStatus
    product_description: str

    joining_fee: int
    annual_fee: int
    renewal_fee: int
    renewal_fee_waiver: int

    reward_program_name: str
    base_reward_points: int
    reward_points_per_amount: int
    accelerated_reward_available: bool
    accelerated_reward_details: str

    travel_benefit: bool
    airport_lounge_access: bool
    domestic_lounge_visits: int
    international_lounge_access: bool
    international_lounge_visits: int
    priority_pass_available: bool
    priority_pass_visits: int
    travel_redemption_available: bool
    travel_portal: str

    dining_benefit: bool
    dining_discount: int

    tag_travel: bool
    tag_shopping: bool
    tag_dining: bool
    tag_fuel: bool
    tag_online_shopping: bool
    tag_international: bool
    tag_airport_lounge: bool
    tag_rewards: bool
    tag_cashback: bool
    tag_premium: bool
    tag_lifestyle: bool
    tag_golf: bool
    tag_movie: bool
    tag_upi: bool
    tag_business: bool

    end_date: date | None = Field(default=None)


# --------------------------------------------------------------------------
# Grounding boundary layer (the only projection allowed to leave)
# --------------------------------------------------------------------------


class GroundedFact(StrictModel):
    """A single stable, citable product fact for future GenAI grounding.

    ``fact_id`` values are stable identifiers (e.g. ``annual_fee``,
    ``domestic_lounge_visits``) that a prompt builder can reference directly.
    """

    fact_id: str
    value: str
    category: GroundedFactCategory


class GroundedProductFacts(StrictModel):
    """Allowlisted product facts permitted to leave the grounding boundary.

    Never contains raw catalogue columns, eligibility data, credit limits,
    internal timestamps, or other non-allowlisted attributes.
    """

    product_id: str
    product_family: ProductFamily
    product_name: str
    product_type: str
    status: ProductStatus
    approved_description: str | None = None
    facts: list[GroundedFact]
    product_tags: list[str]
    catalogue_version: str  # "sha256:<hex>" over the grounded projection
