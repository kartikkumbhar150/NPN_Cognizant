import csv

# ============================================================
# CONFIG
# ============================================================

OUTPUT_FILE = "credit_card_products.csv"

CREATED_AT = "2026-08-13 22:00:00"
UPDATED_AT = "2026-08-13 22:00:00"


# ============================================================
# DEFAULT VALUES
# ============================================================

TEXT_DEFAULT = "Not Applicable"
NUM_DEFAULT = 0
BOOL_DEFAULT = "No"


# ============================================================
# HELPER
# ============================================================

def create_card(
    credit_card_product_id,
    product_code,
    card_name,
    card_variant,
    card_category,

    card_type="Personal",
    card_network="Visa",
    card_form_factor="Physical",
    co_brand="No",
    co_brand_partner="Not Applicable",
    product_status="Active",
    product_description="HDFC Bank credit card product.",

    joining_fee=0,
    annual_fee=0,
    renewal_fee=0,
    first_year_fee_waiver=0,
    renewal_fee_waiver=0,
    add_on_card_fee=0,
    cash_withdrawal_fee=0,
    foreign_currency_markup=0,
    late_payment_fee=0,
    overlimit_fee=0,
    reward_redemption_fee=0,

    minimum_age=21,
    maximum_age=65,
    minimum_income_monthly=0,
    minimum_income_annual=0,
    employment_type="Salaried / Self-employed",
    minimum_credit_score=0,
    residential_requirement="Resident Indian",
    existing_customer_required="No",
    eligibility_description="Subject to bank credit and internal eligibility criteria.",

    minimum_credit_limit=10000,
    maximum_credit_limit=1000000,
    interest_rate_monthly=3.75,
    interest_rate_annual=45.00,
    cash_advance_limit_percent=40,
    minimum_due_percent=5,
    interest_free_period_days=50,

    reward_program_name="Reward Points",
    reward_type="Reward Points",
    base_reward_points=0,
    reward_points_per_amount=150,
    reward_point_value=0.50,
    accelerated_reward_available="No",
    accelerated_reward_details="Not Applicable",
    reward_expiry_months=24,
    cashback_available="No",
    cashback_rate=0,
    cashback_monthly_cap=0,
    reward_redemption_options="Rewards Catalogue / Statement Credit",

    travel_benefit="No",
    airport_lounge_access="No",
    domestic_lounge_visits=0,
    international_lounge_access="No",
    international_lounge_visits=0,
    lounge_spend_requirement=0,
    priority_pass_available="No",
    priority_pass_visits=0,
    airline_benefits="No",
    hotel_benefits="No",
    travel_redemption_available="No",
    travel_portal="Not Applicable",

    shopping_benefit="No",
    shopping_cashback_rate=0,
    dining_benefit="No",
    dining_discount=0,
    fuel_benefit="No",
    fuel_surcharge_waiver="No",
    fuel_monthly_cap=0,
    golf_benefit="No",
    golf_visits_per_quarter=0,
    movie_benefit="No",
    movie_offer_details="Not Applicable",
    subscription_benefit="No",
    partner_offers="Not Applicable",

    is_cobranded="No",
    partner_category="Not Applicable",
    partner_name="Not Applicable",
    partner_reward_program="Not Applicable",
    partner_discount="Not Applicable",
    partner_exclusive_benefits="Not Applicable",

    tag_travel=0,
    tag_shopping=0,
    tag_dining=0,
    tag_fuel=0,
    tag_online_shopping=0,
    tag_international=0,
    tag_airport_lounge=0,
    tag_rewards=0,
    tag_cashback=0,
    tag_premium=0,
    tag_lifestyle=0,
    tag_golf=0,
    tag_movie=0,
    tag_upi=0,
    tag_business=0,

    launch_date="2020-01-01",
    end_date="2099-12-31"
):

    return {
        "credit_card_product_id": credit_card_product_id,
        "product_code": product_code,
        "card_name": card_name,
        "card_variant": card_variant,
        "card_category": card_category,
        "card_type": card_type,
        "card_network": card_network,
        "card_form_factor": card_form_factor,
        "co_brand": co_brand,
        "co_brand_partner": co_brand_partner,
        "product_status": product_status,
        "product_description": product_description,

        "joining_fee": joining_fee,
        "annual_fee": annual_fee,
        "renewal_fee": renewal_fee,
        "first_year_fee_waiver": first_year_fee_waiver,
        "renewal_fee_waiver": renewal_fee_waiver,
        "add_on_card_fee": add_on_card_fee,
        "cash_withdrawal_fee": cash_withdrawal_fee,
        "foreign_currency_markup": foreign_currency_markup,
        "late_payment_fee": late_payment_fee,
        "overlimit_fee": overlimit_fee,
        "reward_redemption_fee": reward_redemption_fee,

        "minimum_age": minimum_age,
        "maximum_age": maximum_age,
        "minimum_income_monthly": minimum_income_monthly,
        "minimum_income_annual": minimum_income_annual,
        "employment_type": employment_type,
        "minimum_credit_score": minimum_credit_score,
        "residential_requirement": residential_requirement,
        "existing_customer_required": existing_customer_required,
        "eligibility_description": eligibility_description,

        "minimum_credit_limit": minimum_credit_limit,
        "maximum_credit_limit": maximum_credit_limit,
        "interest_rate_monthly": interest_rate_monthly,
        "interest_rate_annual": interest_rate_annual,
        "cash_advance_limit_percent": cash_advance_limit_percent,
        "minimum_due_percent": minimum_due_percent,
        "interest_free_period_days": interest_free_period_days,

        "reward_program_name": reward_program_name,
        "reward_type": reward_type,
        "base_reward_points": base_reward_points,
        "reward_points_per_amount": reward_points_per_amount,
        "reward_point_value": reward_point_value,
        "accelerated_reward_available": accelerated_reward_available,
        "accelerated_reward_details": accelerated_reward_details,
        "reward_expiry_months": reward_expiry_months,
        "cashback_available": cashback_available,
        "cashback_rate": cashback_rate,
        "cashback_monthly_cap": cashback_monthly_cap,
        "reward_redemption_options": reward_redemption_options,

        "travel_benefit": travel_benefit,
        "airport_lounge_access": airport_lounge_access,
        "domestic_lounge_visits": domestic_lounge_visits,
        "international_lounge_access": international_lounge_access,
        "international_lounge_visits": international_lounge_visits,
        "lounge_spend_requirement": lounge_spend_requirement,
        "priority_pass_available": priority_pass_available,
        "priority_pass_visits": priority_pass_visits,
        "airline_benefits": airline_benefits,
        "hotel_benefits": hotel_benefits,
        "travel_redemption_available": travel_redemption_available,
        "travel_portal": travel_portal,

        "shopping_benefit": shopping_benefit,
        "shopping_cashback_rate": shopping_cashback_rate,
        "dining_benefit": dining_benefit,
        "dining_discount": dining_discount,
        "fuel_benefit": fuel_benefit,
        "fuel_surcharge_waiver": fuel_surcharge_waiver,
        "fuel_monthly_cap": fuel_monthly_cap,
        "golf_benefit": golf_benefit,
        "golf_visits_per_quarter": golf_visits_per_quarter,
        "movie_benefit": movie_benefit,
        "movie_offer_details": movie_offer_details,
        "subscription_benefit": subscription_benefit,
        "partner_offers": partner_offers,

        "is_cobranded": is_cobranded,
        "partner_category": partner_category,
        "partner_name": partner_name,
        "partner_reward_program": partner_reward_program,
        "partner_discount": partner_discount,
        "partner_exclusive_benefits": partner_exclusive_benefits,

        "tag_travel": tag_travel,
        "tag_shopping": tag_shopping,
        "tag_dining": tag_dining,
        "tag_fuel": tag_fuel,
        "tag_online_shopping": tag_online_shopping,
        "tag_international": tag_international,
        "tag_airport_lounge": tag_airport_lounge,
        "tag_rewards": tag_rewards,
        "tag_cashback": tag_cashback,
        "tag_premium": tag_premium,
        "tag_lifestyle": tag_lifestyle,
        "tag_golf": tag_golf,
        "tag_movie": tag_movie,
        "tag_upi": tag_upi,
        "tag_business": tag_business,

        "launch_date": launch_date,
        "end_date": end_date,

        "created_at": CREATED_AT,
        "updated_at": UPDATED_AT
    }


# ============================================================
# HDFC CREDIT CARD PRODUCTS
# ============================================================

cards = [

    # --------------------------------------------------------
    # CLASSIC
    # --------------------------------------------------------

    create_card(
        "CC001",
        "HDFC_FREEDOM",
        "Freedom Credit Card",
        "Classic",
        "Classic",
        card_network="Visa",
        product_description="Entry-level credit card for everyday spending.",
        tag_rewards=1,
        tag_lifestyle=1
    ),

    create_card(
        "CC002",
        "HDFC_MONEYBACK_PLUS",
        "MoneyBack+ Credit Card",
        "Classic",
        "Classic",
        card_network="Visa",
        reward_program_name="CashPoints",
        reward_type="CashPoints",
        cashback_available="Yes",
        cashback_rate=1,
        tag_cashback=1,
        tag_online_shopping=1,
        tag_rewards=1
    ),

    create_card(
        "CC003",
        "HDFC_BUSINESS_MONEYBACK",
        "Business MoneyBack Credit Card",
        "Classic",
        "Classic",
        card_type="Business",
        card_network="Visa",
        tag_business=1,
        tag_rewards=1
    ),

    create_card(
        "CC004",
        "HDFC_SMALL_BUSINESS_MONEYBACK",
        "Small Business MoneyBack Credit Card",
        "Classic",
        "Classic",
        card_type="Business",
        card_network="Visa",
        tag_business=1,
        tag_rewards=1
    ),

    create_card(
        "CC005",
        "HDFC_UPI_RUPAY",
        "HDFC Bank UPI Credit Card",
        "Classic",
        "Classic",
        card_network="RuPay",
        reward_type="Reward Points",
        tag_upi=1,
        tag_rewards=1
    ),

    create_card(
        "CC006",
        "HDFC_PIXEL_GO",
        "PIXEL Go",
        "Classic",
        "Classic",
        card_network="Visa",
        cashback_available="Yes",
        cashback_rate=1,
        tag_cashback=1,
        tag_online_shopping=1,
        tag_lifestyle=1
    ),

    # --------------------------------------------------------
    # PREMIUM
    # --------------------------------------------------------

    create_card(
        "CC007",
        "HDFC_MILLENNIA",
        "Millennia Credit Card",
        "Premium",
        "Premium",
        card_network="Visa",
        cashback_available="Yes",
        cashback_rate=1,
        reward_type="Cashback",
        travel_benefit="Yes",
        airport_lounge_access="Yes",
        domestic_lounge_visits=8,
        lounge_spend_requirement=100000,
        tag_shopping=1,
        tag_online_shopping=1,
        tag_cashback=1,
        tag_lifestyle=1,
        tag_travel=1,
        tag_airport_lounge=1
    ),

    create_card(
        "CC008",
        "HDFC_PIXEL_PLAY",
        "PIXEL Play",
        "Premium",
        "Premium",
        card_network="Visa",
        cashback_available="Yes",
        cashback_rate=1,
        tag_cashback=1,
        tag_online_shopping=1,
        tag_lifestyle=1
    ),

    # --------------------------------------------------------
    # SUPER PREMIUM
    # --------------------------------------------------------

    create_card(
        "CC009",
        "HDFC_INFINIA",
        "Infinia Credit Card",
        "Super Premium",
        "Super Premium",
        card_network="Mastercard",
        card_form_factor="Metal",
        joining_fee=12500,
        annual_fee=12500,
        renewal_fee=12500,
        renewal_fee_waiver=1000000,
        interest_rate_monthly=1.99,
        interest_rate_annual=23.88,
        reward_program_name="Reward Points",
        reward_type="Reward Points",
        base_reward_points=5,
        reward_points_per_amount=150,
        accelerated_reward_available="Yes",
        accelerated_reward_details="Accelerated rewards through selected SmartBuy categories.",
        travel_benefit="Yes",
        airport_lounge_access="Yes",
        international_lounge_access="Yes",
        priority_pass_available="Yes",
        priority_pass_visits=999,
        airline_benefits="Yes",
        hotel_benefits="Yes",
        travel_redemption_available="Yes",
        travel_portal="SmartBuy",
        golf_benefit="Yes",
        golf_visits_per_quarter=2,
        tag_travel=1,
        tag_international=1,
        tag_airport_lounge=1,
        tag_rewards=1,
        tag_premium=1,
        tag_lifestyle=1,
        tag_golf=1
    ),

    create_card(
        "CC010",
        "HDFC_INFINIA_METAL",
        "Infinia Metal Edition",
        "Super Premium",
        "Super Premium",
        card_network="Mastercard",
        card_form_factor="Metal",
        joining_fee=12500,
        annual_fee=12500,
        renewal_fee=12500,
        renewal_fee_waiver=1000000,
        interest_rate_monthly=1.99,
        interest_rate_annual=23.88,
        reward_program_name="Reward Points",
        reward_type="Reward Points",
        base_reward_points=5,
        reward_points_per_amount=150,
        accelerated_reward_available="Yes",
        accelerated_reward_details="Accelerated rewards through selected SmartBuy categories.",
        travel_benefit="Yes",
        airport_lounge_access="Yes",
        international_lounge_access="Yes",
        priority_pass_available="Yes",
        priority_pass_visits=999,
        airline_benefits="Yes",
        hotel_benefits="Yes",
        travel_redemption_available="Yes",
        travel_portal="SmartBuy",
        golf_benefit="Yes",
        golf_visits_per_quarter=2,
        tag_travel=1,
        tag_international=1,
        tag_airport_lounge=1,
        tag_rewards=1,
        tag_premium=1,
        tag_lifestyle=1,
        tag_golf=1
    ),

    create_card(
        "CC011",
        "HDFC_DINERS_BLACK",
        "Diners Black",
        "Super Premium",
        "Super Premium",
        card_network="Diners Club",
        annual_fee=10000,
        renewal_fee=10000,
        renewal_fee_waiver=500000,
        interest_rate_monthly=1.99,
        interest_rate_annual=23.88,
        reward_program_name="Reward Points",
        reward_type="Reward Points",
        travel_benefit="Yes",
        airport_lounge_access="Yes",
        international_lounge_access="Yes",
        priority_pass_available="Yes",
        priority_pass_visits=999,
        airline_benefits="Yes",
        hotel_benefits="Yes",
        travel_redemption_available="Yes",
        travel_portal="SmartBuy",
        golf_benefit="Yes",
        golf_visits_per_quarter=2,
        dining_benefit="Yes",
        tag_travel=1,
        tag_international=1,
        tag_airport_lounge=1,
        tag_rewards=1,
        tag_premium=1,
        tag_golf=1,
        tag_dining=1,
        tag_lifestyle=1
    ),

    create_card(
        "CC012",
        "HDFC_DINERS_BLACK_METAL",
        "Diners Black Metal Edition",
        "Super Premium",
        "Super Premium",
        card_network="Diners Club",
        card_form_factor="Metal",
        annual_fee=10000,
        renewal_fee=10000,
        renewal_fee_waiver=800000,
        interest_rate_monthly=1.99,
        interest_rate_annual=23.88,
        reward_program_name="Reward Points",
        reward_type="Reward Points",
        travel_benefit="Yes",
        airport_lounge_access="Yes",
        international_lounge_access="Yes",
        priority_pass_available="Yes",
        priority_pass_visits=999,
        travel_redemption_available="Yes",
        travel_portal="SmartBuy",
        tag_travel=1,
        tag_international=1,
        tag_airport_lounge=1,
        tag_rewards=1,
        tag_premium=1
    ),

    create_card(
        "CC013",
        "HDFC_DINERS_PRIVILEGE",
        "Diners Privilege",
        "Premium",
        "Premium",
        card_network="Diners Club",
        reward_program_name="Reward Points",
        reward_type="Reward Points",
        dining_benefit="Yes",
        dining_discount=15,
        movie_benefit="Yes",
        movie_offer_details="Eligible movie offers through partner programs.",
        tag_dining=1,
        tag_movie=1,
        tag_rewards=1,
        tag_lifestyle=1
    ),

    create_card(
        "CC014",
        "HDFC_REGALIA_GOLD",
        "Regalia Gold",
        "Super Premium",
        "Super Premium",
        card_network="Visa",
        joining_fee=2500,
        annual_fee=2500,
        renewal_fee=2500,
        renewal_fee_waiver=300000,
        reward_program_name="Reward Points",
        reward_type="Reward Points",
        base_reward_points=4,
        reward_points_per_amount=150,
        accelerated_reward_available="Yes",
        accelerated_reward_details="Accelerated rewards on selected SmartBuy and partner spends.",
        travel_benefit="Yes",
        airport_lounge_access="Yes",
        domestic_lounge_visits=12,
        international_lounge_access="Yes",
        lounge_spend_requirement=100000,
        travel_redemption_available="Yes",
        travel_portal="SmartBuy",
        dining_benefit="Yes",
        dining_discount=10,
        shopping_benefit="Yes",
        golf_benefit="Yes",
        golf_visits_per_quarter=2,
        tag_travel=1,
        tag_shopping=1,
        tag_dining=1,
        tag_airport_lounge=1,
        tag_rewards=1,
        tag_premium=1,
        tag_lifestyle=1,
        tag_golf=1
    ),

    create_card(
        "CC015",
        "HDFC_DOCTORS_REGALIA",
        "Doctor's Regalia",
        "Super Premium",
        "Super Premium",
        card_network="Visa",
        reward_program_name="Reward Points",
        reward_type="Reward Points",
        travel_benefit="Yes",
        airport_lounge_access="Yes",
        domestic_lounge_visits=12,
        travel_redemption_available="Yes",
        travel_portal="SmartBuy",
        tag_travel=1,
        tag_rewards=1,
        tag_premium=1,
        tag_lifestyle=1
    ),

    create_card(
        "CC016",
        "HDFC_BUSINESS_REGALIA",
        "Business Regalia",
        "Super Premium",
        "Super Premium",
        card_type="Business",
        card_network="Visa",
        reward_program_name="Reward Points",
        reward_type="Reward Points",
        travel_benefit="Yes",
        airport_lounge_access="Yes",
        domestic_lounge_visits=12,
        travel_redemption_available="Yes",
        travel_portal="SmartBuy",
        tag_travel=1,
        tag_rewards=1,
        tag_premium=1,
        tag_business=1
    ),

    create_card(
        "CC017",
        "HDFC_BIZBLACK_METAL",
        "BizBlack Metal Card",
        "Super Premium",
        "Super Premium",
        card_type="Business",
        card_network="Mastercard",
        card_form_factor="Metal",
        interest_rate_monthly=1.99,
        interest_rate_annual=23.88,
        travel_benefit="Yes",
        airport_lounge_access="Yes",
        domestic_lounge_visits=999,
        lounge_spend_requirement=0,
        tag_travel=1,
        tag_airport_lounge=1,
        tag_premium=1,
        tag_business=1
    ),

    create_card(
        "CC018",
        "HDFC_BIZPOWER",
        "BizPower",
        "Premium",
        "Premium",
        card_type="Business",
        card_network="Visa",
        travel_benefit="Yes",
        airport_lounge_access="Yes",
        domestic_lounge_visits=4,
        lounge_spend_requirement=75000,
        tag_travel=1,
        tag_airport_lounge=1,
        tag_business=1
    ),

    # --------------------------------------------------------
    # CO-BRAND
    # --------------------------------------------------------

    create_card(
        "CC019",
        "HDFC_SWIGGY",
        "Swiggy HDFC Bank Credit Card",
        "Co-brand",
        "Premium",
        card_network="Mastercard",
        co_brand="Yes",
        co_brand_partner="Swiggy",
        reward_program_name="Cashback",
        reward_type="Cashback",
        cashback_available="Yes",
        cashback_rate=5,
        partner_category="Food Delivery",
        partner_name="Swiggy",
        partner_reward_program="Swiggy Cashback",
        partner_discount="Up to 5% on eligible spends",
        partner_exclusive_benefits="Food delivery and online shopping benefits",
        tag_dining=1,
        tag_online_shopping=1,
        tag_cashback=1,
        tag_lifestyle=1
    ),

    create_card(
        "CC020",
        "HDFC_TATA_NEU_PLUS",
        "Tata Neu Plus HDFC Bank Credit Card",
        "Co-brand",
        "Premium",
        card_network="RuPay",
        co_brand="Yes",
        co_brand_partner="Tata Neu",
        reward_program_name="NeuCoins",
        reward_type="NeuCoins",
        travel_benefit="Yes",
        airport_lounge_access="Yes",
        domestic_lounge_visits=1,
        lounge_spend_requirement=50000,
        shopping_benefit="Yes",
        partner_category="Shopping / Lifestyle",
        partner_name="Tata Neu",
        partner_reward_program="NeuCoins",
        partner_discount="Eligible Tata ecosystem offers",
        partner_exclusive_benefits="Tata Neu ecosystem rewards",
        tag_travel=1,
        tag_shopping=1,
        tag_rewards=1,
        tag_upi=1,
        tag_lifestyle=1
    ),

    create_card(
        "CC021",
        "HDFC_TATA_NEU_INFINITY",
        "Tata Neu Infinity HDFC Bank Credit Card",
        "Co-brand",
        "Premium",
        card_network="RuPay",
        co_brand="Yes",
        co_brand_partner="Tata Neu",
        reward_program_name="NeuCoins",
        reward_type="NeuCoins",
        travel_benefit="Yes",
        airport_lounge_access="Yes",
        domestic_lounge_visits=2,
        lounge_spend_requirement=50000,
        shopping_benefit="Yes",
        partner_category="Shopping / Lifestyle",
        partner_name="Tata Neu",
        partner_reward_program="NeuCoins",
        partner_discount="Eligible Tata ecosystem offers",
        partner_exclusive_benefits="Tata Neu ecosystem rewards",
        tag_travel=1,
        tag_shopping=1,
        tag_rewards=1,
        tag_upi=1,
        tag_premium=1,
        tag_lifestyle=1
    ),

    create_card(
        "CC022",
        "HDFC_IRCTC",
        "IRCTC HDFC Bank Credit Card",
        "Co-brand",
        "Premium",
        card_network="RuPay",
        co_brand="Yes",
        co_brand_partner="IRCTC",
        reward_program_name="IRCTC Reward Points",
        reward_type="Reward Points",
        travel_benefit="Yes",
        partner_category="Rail Travel",
        partner_name="IRCTC",
        partner_reward_program="IRCTC Reward Points",
        partner_discount="Railway transaction benefits",
        partner_exclusive_benefits="Rail-ticket related reward proposition",
        tag_travel=1,
        tag_rewards=1
    ),

    create_card(
        "CC023",
        "HDFC_INDIANOIL",
        "IndianOil HDFC Bank Credit Card",
        "Co-brand",
        "Premium",
        card_network="Visa",
        co_brand="Yes",
        co_brand_partner="IndianOil",
        reward_program_name="Reward Points",
        reward_type="Reward Points",
        fuel_benefit="Yes",
        fuel_surcharge_waiver="Yes",
        fuel_monthly_cap=250,
        partner_category="Fuel",
        partner_name="IndianOil",
        partner_reward_program="Reward Points",
        partner_discount="Fuel-related benefits",
        partner_exclusive_benefits="IndianOil ecosystem benefits",
        tag_fuel=1,
        tag_rewards=1
    ),

    create_card(
        "CC024",
        "HDFC_MARRIOTT_BONVOY",
        "Marriott Bonvoy HDFC Bank Credit Card",
        "Co-brand",
        "Premium",
        card_network="Visa",
        co_brand="Yes",
        co_brand_partner="Marriott Bonvoy",
        reward_program_name="Marriott Bonvoy Points",
        reward_type="Hotel Points",
        travel_benefit="Yes",
        hotel_benefits="Yes",
        partner_category="Hotels",
        partner_name="Marriott Bonvoy",
        partner_reward_program="Marriott Bonvoy Points",
        partner_discount="Hotel-related offers",
        partner_exclusive_benefits="Marriott Bonvoy ecosystem benefits",
        tag_travel=1,
        tag_rewards=1,
        tag_premium=1,
        tag_lifestyle=1
    ),

    create_card(
        "CC025",
        "HDFC_PHONEPE_ULTIMO",
        "PhonePe HDFC Bank Ultimo Credit Card",
        "Co-brand",
        "Premium",
        card_network="RuPay",
        co_brand="Yes",
        co_brand_partner="PhonePe",
        reward_program_name="CashPoints",
        reward_type="CashPoints",
        cashback_available="Yes",
        cashback_rate=1,
        travel_benefit="Yes",
        airport_lounge_access="Yes",
        domestic_lounge_visits=4,
        lounge_spend_requirement=75000,
        partner_category="Payments",
        partner_name="PhonePe",
        partner_reward_program="CashPoints",
        partner_discount="PhonePe ecosystem offers",
        partner_exclusive_benefits="PhonePe ecosystem rewards",
        tag_upi=1,
        tag_rewards=1,
        tag_cashback=1,
        tag_lifestyle=1
    ),

    create_card(
        "CC026",
        "HDFC_PAYTM_SELECT",
        "Paytm HDFC Bank Select Credit Card",
        "Co-brand",
        "Premium",
        card_network="Visa",
        co_brand="Yes",
        co_brand_partner="Paytm",
        reward_program_name="CashPoints",
        reward_type="CashPoints",
        cashback_available="Yes",
        cashback_rate=5,
        travel_benefit="Yes",
        airport_lounge_access="Yes",
        domestic_lounge_visits=8,
        partner_category="Payments / Travel / Shopping",
        partner_name="Paytm",
        partner_reward_program="CashPoints",
        partner_discount="Accelerated CashPoints on eligible Paytm categories",
        partner_exclusive_benefits="Paytm ecosystem rewards",
        tag_travel=1,
        tag_online_shopping=1,
        tag_cashback=1,
        tag_upi=1
    ),

    create_card(
        "CC027",
        "HDFC_SHOPPERS_STOP",
        "Shoppers Stop HDFC Bank Credit Card",
        "Co-brand",
        "Premium",
        card_network="Visa",
        co_brand="Yes",
        co_brand_partner="Shoppers Stop",
        reward_program_name="Reward Points",
        reward_type="Reward Points",
        shopping_benefit="Yes",
        partner_category="Shopping",
        partner_name="Shoppers Stop",
        partner_reward_program="Reward Points",
        partner_discount="Shopping offers",
        partner_exclusive_benefits="Shoppers Stop ecosystem benefits",
        tag_shopping=1,
        tag_rewards=1,
        tag_lifestyle=1
    ),

    create_card(
        "CC028",
        "HDFC_BEST_PRICE",
        "Best Price HDFC Bank Credit Card",
        "Co-brand",
        "Premium",
        card_type="Business",
        card_network="Visa",
        co_brand="Yes",
        co_brand_partner="Best Price",
        reward_program_name="Reward Points",
        reward_type="Reward Points",
        shopping_benefit="Yes",
        partner_category="Wholesale / Retail",
        partner_name="Best Price",
        partner_reward_program="Reward Points",
        partner_discount="Wholesale shopping benefits",
        partner_exclusive_benefits="Best Price ecosystem benefits",
        tag_shopping=1,
        tag_rewards=1,
        tag_business=1
    ),

    create_card(
        "CC029",
        "HDFC_FLIPKART",
        "Flipkart Wholesale HDFC Bank Credit Card",
        "Co-brand",
        "Premium",
        card_type="Business",
        card_network="Visa",
        co_brand="Yes",
        co_brand_partner="Flipkart Wholesale",
        reward_program_name="Reward Points",
        reward_type="Reward Points",
        shopping_benefit="Yes",
        partner_category="Wholesale",
        partner_name="Flipkart Wholesale",
        partner_reward_program="Reward Points",
        partner_discount="Wholesale purchase benefits",
        partner_exclusive_benefits="Flipkart Wholesale ecosystem benefits",
        tag_shopping=1,
        tag_online_shopping=1,
        tag_rewards=1,
        tag_business=1
    ),

    create_card(
        "CC030",
        "HDFC_PHARMEASY",
        "PharmEasy HDFC Bank Credit Card",
        "Co-brand",
        "Premium",
        card_network="Visa",
        co_brand="Yes",
        co_brand_partner="PharmEasy",
        reward_program_name="Cashback",
        reward_type="Cashback",
        cashback_available="Yes",
        cashback_rate=1,
        partner_category="Healthcare / Pharmacy",
        partner_name="PharmEasy",
        partner_reward_program="Cashback",
        partner_discount="Healthcare and pharmacy offers",
        partner_exclusive_benefits="PharmEasy ecosystem benefits",
        tag_cashback=1,
        tag_lifestyle=1
    ),

    create_card(
        "CC031",
        "HDFC_GOOGLE_PAY",
        "Google Pay HDFC Bank Credit Card",
        "Co-brand",
        "Premium",
        card_network="Visa",
        co_brand="Yes",
        co_brand_partner="Google Pay",
        reward_program_name="Cashback",
        reward_type="Cashback",
        cashback_available="Yes",
        cashback_rate=1,
        partner_category="Payments",
        partner_name="Google Pay",
        partner_reward_program="Cashback",
        partner_discount="Google Pay ecosystem offers",
        partner_exclusive_benefits="Google Pay payment-linked benefits",
        tag_upi=1,
        tag_cashback=1,
        tag_online_shopping=1
    ),

    create_card(
        "CC032",
        "HDFC_EQUTIAS",
        "Equitas Small Finance Bank HDFC Co-brand Credit Card",
        "Co-brand",
        "Premium",
        card_network="Visa",
        co_brand="Yes",
        co_brand_partner="Equitas Small Finance Bank",
        reward_program_name="Reward Points",
        reward_type="Reward Points",
        partner_category="Banking",
        partner_name="Equitas Small Finance Bank",
        partner_reward_program="Reward Points",
        partner_discount="Partner banking offers",
        partner_exclusive_benefits="Equitas ecosystem benefits",
        tag_rewards=1
    )
]


# ============================================================
# FIELD LIST
# ============================================================

FIELDNAMES = [
    "credit_card_product_id",
    "product_code",
    "card_name",
    "card_variant",
    "card_category",
    "card_type",
    "card_network",
    "card_form_factor",
    "co_brand",
    "co_brand_partner",
    "product_status",
    "product_description",

    "joining_fee",
    "annual_fee",
    "renewal_fee",
    "first_year_fee_waiver",
    "renewal_fee_waiver",
    "add_on_card_fee",
    "cash_withdrawal_fee",
    "foreign_currency_markup",
    "late_payment_fee",
    "overlimit_fee",
    "reward_redemption_fee",

    "minimum_age",
    "maximum_age",
    "minimum_income_monthly",
    "minimum_income_annual",
    "employment_type",
    "minimum_credit_score",
    "residential_requirement",
    "existing_customer_required",
    "eligibility_description",

    "minimum_credit_limit",
    "maximum_credit_limit",
    "interest_rate_monthly",
    "interest_rate_annual",
    "cash_advance_limit_percent",
    "minimum_due_percent",
    "interest_free_period_days",

    "reward_program_name",
    "reward_type",
    "base_reward_points",
    "reward_points_per_amount",
    "reward_point_value",
    "accelerated_reward_available",
    "accelerated_reward_details",
    "reward_expiry_months",
    "cashback_available",
    "cashback_rate",
    "cashback_monthly_cap",
    "reward_redemption_options",

    "travel_benefit",
    "airport_lounge_access",
    "domestic_lounge_visits",
    "international_lounge_access",
    "international_lounge_visits",
    "lounge_spend_requirement",
    "priority_pass_available",
    "priority_pass_visits",
    "airline_benefits",
    "hotel_benefits",
    "travel_redemption_available",
    "travel_portal",

    "shopping_benefit",
    "shopping_cashback_rate",
    "dining_benefit",
    "dining_discount",
    "fuel_benefit",
    "fuel_surcharge_waiver",
    "fuel_monthly_cap",
    "golf_benefit",
    "golf_visits_per_quarter",
    "movie_benefit",
    "movie_offer_details",
    "subscription_benefit",
    "partner_offers",

    "is_cobranded",
    "partner_category",
    "partner_name",
    "partner_reward_program",
    "partner_discount",
    "partner_exclusive_benefits",

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

    "launch_date",
    "end_date",
    "created_at",
    "updated_at"
]


# ============================================================
# VALIDATION
# ============================================================

def validate_no_blank_values(cards, fields):
    for row_num, row in enumerate(cards, start=1):

        for field in fields:

            value = row.get(field)

            if value is None:
                raise ValueError(
                    f"Blank/None value found: "
                    f"row={row_num}, field={field}"
                )

            if isinstance(value, str) and value.strip() == "":
                raise ValueError(
                    f"Blank string found: "
                    f"row={row_num}, field={field}"
                )


# ============================================================
# WRITE CSV
# ============================================================

validate_no_blank_values(cards, FIELDNAMES)

with open(
    OUTPUT_FILE,
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=FIELDNAMES
    )

    writer.writeheader()
    writer.writerows(cards)


# ============================================================
# SUMMARY
# ============================================================

print("=" * 70)
print("CREDIT CARD PRODUCT DATA GENERATED")
print("=" * 70)
print(f"Products generated : {len(cards)}")
print(f"Columns            : {len(FIELDNAMES)}")
print(f"Output file        : {OUTPUT_FILE}")
print("Blank values       : 0")
print("=" * 70)

for row in cards:
    print(
        f"{row['credit_card_product_id']} | "
        f"{row['card_name']} | "
        f"{row['card_category']}"
    )