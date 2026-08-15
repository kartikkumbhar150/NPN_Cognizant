"""
Next Best Offer (NBO) Engine
============================
Gap-aware recommendation engine.
Consumes FinancialAnalyst output to recommend the single most
impactful banking product for each customer with specific, data-driven reasons.
"""


class NBOEngine:
    def __init__(self, credit_cards, loans):
        self.credit_cards = credit_cards
        self.loans        = loans

        # Gap code → product category priority mapping
        self.gap_product_map = {
            "NO_INVESTMENT":              ["Investment/SIP", "FD"],
            "HIGH_MEDICAL_NO_INSURANCE":  ["Health Insurance"],
            "NO_INSURANCE":               ["Health Insurance"],
            "TRAVELLER_NO_CARD":          ["Travel Card"],
            "GROWING_INCOME_NO_INVESTMENT": ["Investment/SIP"],
            "CRITICAL_SAVINGS":           ["FD"],
            "HIGH_RENT_BURDEN":           ["Home Loan"],
            "LOW_SAVINGS":                ["Investment/SIP", "FD"],
            "OVERSPENDING_DINING":        ["Cashback Card"],
            "OVERSPENDING_SHOPPING":      ["Shopping Rewards Card"],
            "HIGH_DINING":                ["Cashback Card"],
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Propensity (legacy — kept for segmentation compat, now gap-driven)
    # ─────────────────────────────────────────────────────────────────────────

    def calculate_propensity(self, customer_data, segments, events, financial_gaps=None):
        """
        Calculate product propensity scores.
        When financial_gaps are provided, they drive the scores directly.
        Falls back to heuristic when no gaps are available.
        """
        propensities = {
            "Travel Card":      10,
            "Investment/SIP":   10,
            "Personal Loan":    5,
            "Health Insurance": 5,
            "FD":               10,
            "Home Loan":        5,
            "Cashback Card":    5,
        }

        if financial_gaps:
            # Severity directly boosts propensity
            for gap in financial_gaps:
                boost = gap["severity"] * 8
                for product_cat in gap.get("products", []):
                    if product_cat in propensities:
                        propensities[product_cat] = min(99, propensities[product_cat] + boost)
                    else:
                        # Add new product category if not in default list
                        propensities[product_cat] = min(99, boost)
        else:
            # Legacy heuristic fallback
            if "Frequent Traveller" in segments:
                propensities["Travel Card"] += 35
            if "Investment Prospect" in segments:
                propensities["Investment/SIP"] += 60
            if "Loan Prospect" in segments:
                propensities["Personal Loan"] += 40
            if "High-Value Customer" in segments:
                propensities["FD"] += 50
            if "Flight/Travel Purchase" in events:
                propensities["Travel Card"] += 50

        # Cap at 99
        for k in propensities:
            propensities[k] = min(propensities[k], 99)

        return dict(sorted(propensities.items(), key=lambda item: item[1], reverse=True))

    # ─────────────────────────────────────────────────────────────────────────
    # Next Best Offer — gap-driven
    # ─────────────────────────────────────────────────────────────────────────

    def determine_next_best_offer(self, propensities, customer_data, events,
                                  existing_products=None, financial_gaps=None,
                                  financial_analysis=None):
        """
        Pick the single best offer for this customer.
        If financial_gaps are available, uses the highest-severity gap.
        Falls back to top propensity otherwise.
        """
        income = customer_data.get("annual_income", 0)

        # ── Gap-driven path ─────────────────────────────────────────────────
        if financial_gaps:
            top_gap    = financial_gaps[0]  # already sorted by severity desc
            product_cat = top_gap["products"][0]
            reasons    = [top_gap["insight"]]

            # Add any secondary gap insights (max 2 extras)
            for extra_gap in financial_gaps[1:3]:
                reasons.append(extra_gap["insight"])

            specific_product = self._resolve_product(product_cat, income)

            return {
                "category":        product_cat,
                "specific_product": specific_product,
                "propensity":      f"{propensities.get(product_cat, propensities.get(financial_gaps[0]['products'][0], 50))}%",
                "reasons":         reasons,
                "gap_code":        top_gap["code"],
            }

        # ── Legacy fallback path ─────────────────────────────────────────────
        best_category = list(propensities.keys())[0]
        score         = propensities[best_category]
        specific_product = self._resolve_product(best_category, income)
        reasons = [f"High propensity score for {best_category}."]

        if "Flight/Travel Purchase" in events:
            reasons.append("Recent flight/travel purchase detected.")
        if "Large Purchase" in events:
            reasons.append("Recent large purchase detected.")

        return {
            "category":        best_category,
            "specific_product": specific_product,
            "propensity":      f"{score}%",
            "reasons":         reasons,
            "gap_code":        None,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # Product Resolver — maps category → specific product from catalogue
    # ─────────────────────────────────────────────────────────────────────────

    def _resolve_product(self, product_category, income):
        """Find the best specific product from the catalogue for a category and income."""

        if product_category == "Travel Card":
            travel_cards = self.credit_cards[self.credit_cards["tag_travel"] == 1]
            if not travel_cards.empty:
                eligible = travel_cards[travel_cards["minimum_income_annual"] <= income]
                if not eligible.empty:
                    return eligible.sort_values("minimum_income_annual", ascending=False).iloc[0]["card_name"]
                return travel_cards.iloc[0]["card_name"]

        elif product_category in ("Cashback Card", "Shopping Rewards Card"):
            if "tag_cashback" in self.credit_cards.columns:
                cards = self.credit_cards[self.credit_cards["tag_cashback"] == 1]
            else:
                cards = self.credit_cards
            if not cards.empty:
                eligible = cards[cards["minimum_income_annual"] <= income]
                if not eligible.empty:
                    return eligible.iloc[0]["card_name"]
                return cards.iloc[0]["card_name"]

        elif product_category == "Home Loan":
            home_loans = self.loans[self.loans["product_name"].str.contains("Home", case=False, na=False)]
            if not home_loans.empty:
                return home_loans.iloc[0]["product_name"]
            return "Home Loan"

        elif product_category == "Health Insurance":
            return "Health & Life Insurance Plan"

        elif product_category == "Investment/SIP":
            return "Mutual Fund SIP"

        elif product_category == "FD":
            return "Fixed Deposit (FD)"

        return f"{product_category} Product"
