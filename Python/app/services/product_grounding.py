"""Product grounding service.

Responsibility boundary (Phase 6, DS-02):

    explicit product ID
        -> repository lookup
        -> active/effective validation
        -> explicit allowlist projection
        -> deterministic catalogue hash
        -> GroundedProductFacts

The service only retrieves an *already selected* product and projects
allowlisted facts. It never chooses a product, and knows nothing about
customers, propensity, eligibility, events, campaigns, or LLMs.

Ambiguous and negative values (``0``, ``No``, ``Not Applicable``, the
undocumented ``999`` sentinel, blanks) never become positive marketing claims;
they are omitted from the grounded projection.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date

from app.models.personalization import ProductFamily
from app.models.product import (
    CreditCardProduct,
    GroundedFact,
    GroundedFactCategory,
    GroundedProductFacts,
    ProductStatus,
)
from app.repositories.product_catalogue import ProductCatalogueRepository

# Undocumented sentinel in the prototype CSV (e.g. lounge-visit counts). The
# catalogue does not document its meaning, so it must never be interpreted as
# "unlimited" or surfaced as a positive claim.
_SENTINEL_COUNT = 999

# Generic placeholder descriptions shared by most rows; not product-specific,
# so they must not be approved for grounding.
_GENERIC_DESCRIPTIONS = frozenset({"hdfc bank credit card product."})

_TAG_ATTRIBUTES: tuple[tuple[str, str], ...] = (
    ("tag_travel", "TRAVEL"),
    ("tag_shopping", "SHOPPING"),
    ("tag_dining", "DINING"),
    ("tag_fuel", "FUEL"),
    ("tag_online_shopping", "ONLINE_SHOPPING"),
    ("tag_international", "INTERNATIONAL"),
    ("tag_airport_lounge", "AIRPORT_LOUNGE"),
    ("tag_rewards", "REWARDS"),
    ("tag_cashback", "CASHBACK"),
    ("tag_premium", "PREMIUM"),
    ("tag_lifestyle", "LIFESTYLE"),
    ("tag_golf", "GOLF"),
    ("tag_movie", "MOVIE"),
    ("tag_upi", "UPI"),
    ("tag_business", "BUSINESS"),
)


class GroundingError(Exception):
    """Base class for product grounding errors."""

    code = "GROUNDING_ERROR"


class ProductInactiveError(GroundingError):
    """The product is inactive or expired and must not be marketed."""

    code = "PRODUCT_INACTIVE"

    def __init__(self, product_id: str, reason: str) -> None:
        super().__init__(f"product {product_id!r} is not marketable: {reason}")
        self.product_id = product_id


class UnsupportedProductFamilyError(GroundingError):
    """The requested product family has no grounding implementation."""

    code = "UNSUPPORTED_PRODUCT_FAMILY"

    def __init__(self, product_family: ProductFamily) -> None:
        super().__init__(f"unsupported product family: {product_family.value}")
        self.product_family = product_family


def _positive_visit_count(value: int) -> int | None:
    """Return the count only when it is a definite positive number.

    ``0`` means no benefit and ``999`` is an undocumented sentinel; both are
    excluded so they can never be read as positive marketing claims.
    """
    if value > 0 and value != _SENTINEL_COUNT:
        return value
    return None


class ProductGroundingService:
    """Grounds an explicitly selected product into allowlisted facts."""

    def __init__(self, repository: ProductCatalogueRepository) -> None:
        self._repository = repository

    def ground(self, product_family: ProductFamily, product_id: str) -> GroundedProductFacts:
        """Ground ``product_id`` within ``product_family``.

        DS-02 supports ``CREDIT_CARD`` only; any other family is rejected
        rather than silently grounded with the wrong projection.
        """
        if product_family is ProductFamily.CREDIT_CARD:
            return self._ground_credit_card(product_id)
        raise UnsupportedProductFamilyError(product_family)

    # ------------------------------------------------------------------
    # Credit-card pipeline
    # ------------------------------------------------------------------

    def _ground_credit_card(self, product_id: str) -> GroundedProductFacts:
        product = self._repository.get_credit_card_by_id(product_id)
        self._validate_marketable(product)

        facts = sorted(self._project_facts(product), key=lambda fact: fact.fact_id)
        product_tags = sorted(self._project_tags(product))
        approved_description = self._approved_description(product)

        catalogue_version = self._catalogue_version(
            product=product,
            facts=facts,
            product_tags=product_tags,
            approved_description=approved_description,
        )

        return GroundedProductFacts(
            product_id=product.product_id,
            product_family=ProductFamily.CREDIT_CARD,
            product_name=product.card_name,
            product_type=product.card_category,
            status=product.product_status,
            approved_description=approved_description,
            facts=facts,
            product_tags=product_tags,
            catalogue_version=catalogue_version,
        )

    def _validate_marketable(self, product: CreditCardProduct) -> None:
        """Reject inactive and clearly expired products."""
        if product.product_status is not ProductStatus.ACTIVE:
            raise ProductInactiveError(
                product.product_id, f"product status is {product.product_status.value}"
            )
        if product.end_date is not None and product.end_date < date.today():
            raise ProductInactiveError(
                product.product_id, f"product expired on {product.end_date.isoformat()}"
            )

    # ------------------------------------------------------------------
    # Allowlist projection
    # ------------------------------------------------------------------

    def _project_facts(self, product: CreditCardProduct) -> list[GroundedFact]:
        """Explicit allowlist. Only clearly defined, positive facts are emitted."""
        facts: list[GroundedFact] = []

        # --- Identity -------------------------------------------------
        facts.append(
            GroundedFact(fact_id="product_id", value=product.product_id, category=GroundedFactCategory.IDENTITY)
        )
        facts.append(
            GroundedFact(fact_id="product_name", value=product.card_name, category=GroundedFactCategory.IDENTITY)
        )
        facts.append(
            GroundedFact(fact_id="product_type", value=product.card_category, category=GroundedFactCategory.IDENTITY)
        )
        facts.append(
            GroundedFact(fact_id="status", value=product.product_status.value, category=GroundedFactCategory.IDENTITY)
        )

        # --- Fees -----------------------------------------------------
        # Fee amounts are unambiguous (0 means no fee, e.g. joining fee free).
        facts.append(
            GroundedFact(fact_id="joining_fee", value=str(product.joining_fee), category=GroundedFactCategory.FEES)
        )
        facts.append(
            GroundedFact(fact_id="annual_fee", value=str(product.annual_fee), category=GroundedFactCategory.FEES)
        )

        # --- Rewards --------------------------------------------------
        if product.reward_program_name and product.reward_program_name != "Not Applicable":
            facts.append(
                GroundedFact(
                    fact_id="reward_program_name",
                    value=product.reward_program_name,
                    category=GroundedFactCategory.REWARDS,
                )
            )
        if product.base_reward_points > 0 and product.reward_points_per_amount > 0:
            facts.append(
                GroundedFact(
                    fact_id="reward_rate",
                    value=(
                        f"{product.base_reward_points} reward points per "
                        f"₹{product.reward_points_per_amount} spent"
                    ),
                    category=GroundedFactCategory.REWARDS,
                )
            )
        if product.accelerated_reward_available:
            details = product.accelerated_reward_details.strip()
            value = details if details and details != "Not Applicable" else "Yes"
            facts.append(
                GroundedFact(fact_id="accelerated_rewards", value=value, category=GroundedFactCategory.REWARDS)
            )

        # --- Travel ---------------------------------------------------
        domestic = _positive_visit_count(product.domestic_lounge_visits)
        if product.airport_lounge_access and domestic is not None:
            facts.append(
                GroundedFact(
                    fact_id="domestic_lounge_visits",
                    value=str(domestic),
                    category=GroundedFactCategory.TRAVEL,
                )
            )
        international = _positive_visit_count(product.international_lounge_visits)
        if product.international_lounge_access and international is not None:
            facts.append(
                GroundedFact(
                    fact_id="international_lounge_visits",
                    value=str(international),
                    category=GroundedFactCategory.TRAVEL,
                )
            )
        if product.travel_redemption_available and product.travel_portal.strip() not in ("", "Not Applicable"):
            facts.append(
                GroundedFact(
                    fact_id="travel_portal",
                    value=product.travel_portal.strip(),
                    category=GroundedFactCategory.TRAVEL,
                )
            )

        # --- Dining ---------------------------------------------------
        if product.dining_benefit and product.dining_discount > 0:
            facts.append(
                GroundedFact(
                    fact_id="dining_discount",
                    value=str(product.dining_discount),
                    category=GroundedFactCategory.DINING,
                )
            )

        return facts

    def _project_tags(self, product: CreditCardProduct) -> list[str]:
        """Normalize the CSV tag flags to positive uppercase tag names."""
        return [name for attribute, name in _TAG_ATTRIBUTES if getattr(product, attribute)]

    def _approved_description(self, product: CreditCardProduct) -> str | None:
        """Only a product-specific description may be approved for grounding."""
        description = product.product_description.strip()
        if not description or description.casefold() in _GENERIC_DESCRIPTIONS:
            return None
        return description

    # ------------------------------------------------------------------
    # Catalogue versioning
    # ------------------------------------------------------------------

    def _catalogue_version(
        self,
        *,
        product: CreditCardProduct,
        facts: list[GroundedFact],
        product_tags: list[str],
        approved_description: str | None,
    ) -> str:
        """Deterministic SHA-256 over the canonical grounded projection.

        Only allowlisted facts feed the hash: the same grounded facts always
        produce the same version, and any change to a grounded fact changes it.
        Non-grounded raw fields (e.g. ``renewal_fee_waiver``) do not affect it.
        """
        payload = {
            "product_id": product.product_id,
            "product_family": ProductFamily.CREDIT_CARD.value,
            "product_name": product.card_name,
            "product_type": product.card_category,
            "status": product.product_status.value,
            "approved_description": approved_description,
            "facts": [
                {"fact_id": fact.fact_id, "value": fact.value, "category": fact.category.value}
                for fact in facts
            ],
            "product_tags": product_tags,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return f"sha256:{digest}"
