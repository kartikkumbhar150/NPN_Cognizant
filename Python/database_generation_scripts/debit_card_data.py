import csv

# ============================================================
# CONFIG
# ============================================================

OUTPUT_FILE = "debit_card_products.csv"

CREATED_AT = "2026-08-15 10:00:00"
UPDATED_AT = "2026-08-15 10:00:00"


# ============================================================
# DEFAULT VALUES
# ============================================================

TEXT_DEFAULT = "Not Applicable"
NUM_DEFAULT = 0
BOOL_DEFAULT = "No"


# ============================================================
# HELPER
# ============================================================

def create_debit_card(
    debit_card_product_id,
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
    product_description="Bank debit card product.",

    joining_fee=0,
    annual_fee=0,
    renewal_fee=0,
    first_year_fee_waiver=0,
    renewal_fee_waiver=0,
    add_on_card_fee=0,
    card_replacement_fee=0,
    cash_withdrawal_fee=0,
    foreign_currency_markup=0,

    minimum_age=18,
    maximum_age=70,
    minimum_income_monthly=0,
    minimum_income_annual=0,
    employment_type="Salaried / Self-employed",
    minimum_balance_required=0,
    residential_requirement="Resident Indian",
    existing_customer_required="No",
    eligibility_description="Subject to bank internal eligibility criteria.",

    atm_daily_limit=25000,
    pos_daily_limit=50000,
    online_daily_limit=50000,
    international_transaction="No",
    contactless_enabled="Yes",
    contactless_limit=5000,
    pin_change_available="Yes",
    atm_transaction_limit=5,

    upi_enabled="Yes",
    internet_banking="Yes",
    mobile_banking="Yes",
    tap_to_pay="Yes",
    qr_payment="Yes",

    reward_program_name="Reward Points",
    reward_type="Reward Points",
    reward_points_per_amount=1,
    reward_point_value=0,
    accelerated_reward_available="No",
    accelerated_reward_details="Not Applicable",
    cashback_available="No",
    cashback_rate=0,
    cashback_monthly_cap=0,

    travel_benefit="No",
    airport_lounge_access="No",
    domestic_lounge_visits=0,
    international_lounge_access="No",
    international_lounge_visits=0,
    priority_pass_available="No",

    shopping_benefit="No",
    shopping_cashback_rate=0,
    dining_benefit="No",
    dining_discount=0,
    fuel_benefit="No",
    fuel_surcharge_waiver="No",
    fuel_monthly_cap=0,
    movie_benefit="No",
    movie_offer_details="Not Applicable",

    insurance_cover="No",
    insurance_cover_amount=0,
    purchase_protection="No",
    lost_card_liability="Zero liability subject to bank terms",

    card_control_app="Yes",
    transaction_alerts="Yes",
    instant_card_block="Yes",
    virtual_card_available="No",
    digital_application="Yes",
    instant_issuance="No",
    customer_support="24x7",

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
    tag_movie=0,
    tag_upi=0,
    tag_business=0,

    launch_date="2020-01-01",
    end_date="2099-12-31"
):

    return {
        "debit_card_product_id": debit_card_product_id,
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
        "card_replacement_fee": card_replacement_fee,
        "cash_withdrawal_fee": cash_withdrawal_fee,
        "foreign_currency_markup": foreign_currency_markup,

        "minimum_age": minimum_age,
        "maximum_age": maximum_age,
        "minimum_income_monthly": minimum_income_monthly,
        "minimum_income_annual": minimum_income_annual,
        "employment_type": employment_type,
        "minimum_balance_required": minimum_balance_required,
        "residential_requirement": residential_requirement,
        "existing_customer_required": existing_customer_required,
        "eligibility_description": eligibility_description,

        "atm_daily_limit": atm_daily_limit,
        "pos_daily_limit": pos_daily_limit,
        "online_daily_limit": online_daily_limit,
        "international_transaction": international_transaction,
        "contactless_enabled": contactless_enabled,
        "contactless_limit": contactless_limit,
        "pin_change_available": pin_change_available,
        "atm_transaction_limit": atm_transaction_limit,

        "upi_enabled": upi_enabled,
        "internet_banking": internet_banking,
        "mobile_banking": mobile_banking,
        "tap_to_pay": tap_to_pay,
        "qr_payment": qr_payment,

        "reward_program_name": reward_program_name,
        "reward_type": reward_type,
        "reward_points_per_amount": reward_points_per_amount,
        "reward_point_value": reward_point_value,
        "accelerated_reward_available": accelerated_reward_available,
        "accelerated_reward_details": accelerated_reward_details,
        "cashback_available": cashback_available,
        "cashback_rate": cashback_rate,
        "cashback_monthly_cap": cashback_monthly_cap,

        "travel_benefit": travel_benefit,
        "airport_lounge_access": airport_lounge_access,
        "domestic_lounge_visits": domestic_lounge_visits,
        "international_lounge_access": international_lounge_access,
        "international_lounge_visits": international_lounge_visits,
        "priority_pass_available": priority_pass_available,

        "shopping_benefit": shopping_benefit,
        "shopping_cashback_rate": shopping_cashback_rate,
        "dining_benefit": dining_benefit,
        "dining_discount": dining_discount,
        "fuel_benefit": fuel_benefit,
        "fuel_surcharge_waiver": fuel_surcharge_waiver,
        "fuel_monthly_cap": fuel_monthly_cap,
        "movie_benefit": movie_benefit,
        "movie_offer_details": movie_offer_details,

        "insurance_cover": insurance_cover,
        "insurance_cover_amount": insurance_cover_amount,
        "purchase_protection": purchase_protection,
        "lost_card_liability": lost_card_liability,

        "card_control_app": card_control_app,
        "transaction_alerts": transaction_alerts,
        "instant_card_block": instant_card_block,
        "virtual_card_available": virtual_card_available,
        "digital_application": digital_application,
        "instant_issuance": instant_issuance,
        "customer_support": customer_support,

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
        "tag_movie": tag_movie,
        "tag_upi": tag_upi,
        "tag_business": tag_business,

        "launch_date": launch_date,
        "end_date": end_date,

        "created_at": CREATED_AT,
        "updated_at": UPDATED_AT
    }


# ============================================================
# DEBIT CARD PRODUCTS
# ============================================================

cards = [

    # --------------------------------------------------------
    # CLASSIC
    # --------------------------------------------------------

    create_debit_card(
        "DC001",
        "HDFC_MILLENNIA_DEBIT",
        "Millennia Debit Card",
        "Classic",
        "Classic",
        card_network="Visa",
        product_description="Everyday debit card for regular banking and digital payments.",
        atm_daily_limit=25000,
        pos_daily_limit=50000,
        online_daily_limit=50000,
        upi_enabled="Yes",
        contactless_enabled="Yes",
        tag_upi=1,
        tag_lifestyle=1
    ),

    create_debit_card(
        "DC002",
        "HDFC_EASYSHOP",
        "EasyShop Debit Card",
        "Classic",
        "Classic",
        card_network="Visa",
        product_description="Standard debit card for ATM, POS, online and UPI transactions.",
        atm_daily_limit=25000,
        pos_daily_limit=50000,
        online_daily_limit=50000,
        tag_upi=1
    ),

    create_debit_card(
        "DC003",
        "HDFC_EASYSHOP_PLATINUM",
        "EasyShop Platinum Debit Card",
        "Platinum",
        "Premium",
        card_network="Visa",
        annual_fee=150,
        renewal_fee=150,
        atm_daily_limit=50000,
        pos_daily_limit=100000,
        online_daily_limit=100000,
        international_transaction="Yes",
        contactless_enabled="Yes",
        travel_benefit="Yes",
        shopping_benefit="Yes",
        tag_travel=1,
        tag_shopping=1,
        tag_premium=1
    ),

    create_debit_card(
        "DC004",
        "HDFC_WOMEN_DEBIT",
        "HDFC Women's Debit Card",
        "Classic",
        "Lifestyle",
        card_network="Visa",
        shopping_benefit="Yes",
        dining_benefit="Yes",
        cashback_available="Yes",
        cashback_rate=1,
        tag_cashback=1,
        tag_shopping=1,
        tag_lifestyle=1
    ),

    create_debit_card(
        "DC005",
        "HDFC_RUPAY_DEBIT",
        "HDFC Bank RuPay Debit Card",
        "Classic",
        "Classic",
        card_network="RuPay",
        upi_enabled="Yes",
        qr_payment="Yes",
        contactless_enabled="Yes",
        tag_upi=1
    ),

    create_debit_card(
        "DC006",
        "HDFC_DIGITAL_DEBIT",
        "Digital Debit Card",
        "Digital",
        "Digital",
        card_network="Visa",
        virtual_card_available="Yes",
        digital_application="Yes",
        instant_issuance="Yes",
        card_control_app="Yes",
        transaction_alerts="Yes",
        tag_online_shopping=1,
        tag_upi=1,
        tag_lifestyle=1
    ),

    # --------------------------------------------------------
    # PREMIUM
    # --------------------------------------------------------

    create_debit_card(
        "DC007",
        "HDFC_PLATINUM_DEBIT",
        "Platinum Debit Card",
        "Platinum",
        "Premium",
        card_network="Visa",
        annual_fee=200,
        renewal_fee=200,
        atm_daily_limit=50000,
        pos_daily_limit=150000,
        online_daily_limit=150000,
        international_transaction="Yes",
        travel_benefit="Yes",
        airport_lounge_access="Yes",
        domestic_lounge_visits=2,
        shopping_benefit="Yes",
        dining_benefit="Yes",
        fuel_benefit="Yes",
        tag_travel=1,
        tag_shopping=1,
        tag_dining=1,
        tag_airport_lounge=1,
        tag_premium=1
    ),

    create_debit_card(
        "DC008",
        "HDFC_REGALIA_DEBIT",
        "Regalia Debit Card",
        "Premium",
        "Premium",
        card_network="Visa",
        annual_fee=300,
        renewal_fee=300,
        atm_daily_limit=100000,
        pos_daily_limit=200000,
        online_daily_limit=200000,
        international_transaction="Yes",
        travel_benefit="Yes",
        airport_lounge_access="Yes",
        domestic_lounge_visits=4,
        dining_benefit="Yes",
        dining_discount=10,
        golf_benefit="Yes",
        tag_travel=1,
        tag_dining=1,
        tag_airport_lounge=1,
        tag_premium=1
    ),

    create_debit_card(
        "DC009",
        "HDFC_IMPERIA_DEBIT",
        "Imperia Platinum Debit Card",
        "Premium",
        "Premium",
        card_network="Mastercard",
        annual_fee=500,
        renewal_fee=500,
        atm_daily_limit=100000,
        pos_daily_limit=250000,
        online_daily_limit=250000,
        international_transaction="Yes",
        travel_benefit="Yes",
        airport_lounge_access="Yes",
        domestic_lounge_visits=8,
        international_lounge_access="Yes",
        international_lounge_visits=2,
        shopping_benefit="Yes",
        dining_benefit="Yes",
        tag_travel=1,
        tag_international=1,
        tag_airport_lounge=1,
        tag_premium=1
    ),

    create_debit_card(
        "DC010",
        "HDFC_PREFERRED_DEBIT",
        "Preferred Banking Debit Card",
        "Premium",
        "Premium",
        card_network="Visa",
        minimum_balance_required=250000,
        atm_daily_limit=100000,
        pos_daily_limit=200000,
        online_daily_limit=200000,
        travel_benefit="Yes",
        airport_lounge_access="Yes",
        domestic_lounge_visits=4,
        tag_travel=1,
        tag_airport_lounge=1,
        tag_premium=1
    ),

    # --------------------------------------------------------
    # BUSINESS
    # --------------------------------------------------------

    create_debit_card(
        "DC011",
        "HDFC_BUSINESS_DEBIT",
        "Business Debit Card",
        "Business",
        "Business",
        card_type="Business",
        card_network="Visa",
        minimum_income_annual=500000,
        employment_type="Business",
        atm_daily_limit=100000,
        pos_daily_limit=250000,
        online_daily_limit=250000,
        international_transaction="Yes",
        tag_business=1
    ),

    create_debit_card(
        "DC012",
        "HDFC_BUSINESS_PLATINUM",
        "Business Platinum Debit Card",
        "Platinum",
        "Business",
        card_type="Business",
        card_network="Mastercard",
        annual_fee=500,
        renewal_fee=500,
        minimum_income_annual=1000000,
        employment_type="Business",
        atm_daily_limit=150000,
        pos_daily_limit=500000,
        online_daily_limit=500000,
        international_transaction="Yes",
        travel_benefit="Yes",
        airport_lounge_access="Yes",
        domestic_lounge_visits=4,
        tag_travel=1,
        tag_airport_lounge=1,
        tag_premium=1,
        tag_business=1
    ),

    create_debit_card(
        "DC013",
        "HDFC_CORPORATE_DEBIT",
        "Corporate Debit Card",
        "Corporate",
        "Business",
        card_type="Business",
        card_network="Visa",
        minimum_income_annual=2000000,
        employment_type="Business",
        atm_daily_limit=200000,
        pos_daily_limit=500000,
        online_daily_limit=500000,
        international_transaction="Yes",
        card_control_app="Yes",
        transaction_alerts="Yes",
        tag_business=1,
        tag_international=1
    ),

    # --------------------------------------------------------
    # CO-BRAND / SPECIAL
    # --------------------------------------------------------

    create_debit_card(
        "DC014",
        "HDFC_INDIANOIL_DEBIT",
        "IndianOil HDFC Bank Debit Card",
        "Co-brand",
        "Co-brand",
        card_network="Visa",
        co_brand="Yes",
        co_brand_partner="IndianOil",
        fuel_benefit="Yes",
        fuel_surcharge_waiver="Yes",
        fuel_monthly_cap=250,
        partner_offers="IndianOil fuel benefits",
        tag_fuel=1,
        tag_lifestyle=1
    ),

    create_debit_card(
        "DC015",
        "HDFC_KIDS_DEBIT",
        "Kids Advantage Debit Card",
        "Youth",
        "Youth",
        card_network="Visa",
        minimum_age=10,
        maximum_age=18,
        minimum_income_monthly=0,
        minimum_income_annual=0,
        employment_type="Student",
        atm_daily_limit=5000,
        pos_daily_limit=10000,
        online_daily_limit=10000,
        contactless_enabled="Yes",
        tag_lifestyle=1
    ),

    create_debit_card(
        "DC016",
        "HDFC_SALARY_DEBIT",
        "Salary Account Debit Card",
        "Classic",
        "Salary",
        card_network="Visa",
        existing_customer_required="Yes",
        atm_daily_limit=50000,
        pos_daily_limit=100000,
        online_daily_limit=100000,
        upi_enabled="Yes",
        mobile_banking="Yes",
        tag_upi=1
    ),

    create_debit_card(
        "DC017",
        "HDFC_NRI_DEBIT",
        "NRI Debit Card",
        "Premium",
        "NRI",
        card_network="Visa",
        residential_requirement="NRI",
        existing_customer_required="Yes",
        atm_daily_limit=100000,
        pos_daily_limit=200000,
        online_daily_limit=200000,
        international_transaction="Yes",
        travel_benefit="Yes",
        tag_travel=1,
        tag_international=1,
        tag_premium=1
    ),

    create_debit_card(
        "DC018",
        "HDFC_WORLD_DEBIT",
        "World Debit Card",
        "World",
        "Premium",
        card_network="Mastercard",
        annual_fee=750,
        renewal_fee=750,
        atm_daily_limit=200000,
        pos_daily_limit=500000,
        online_daily_limit=500000,
        international_transaction="Yes",
        travel_benefit="Yes",
        airport_lounge_access="Yes",
        domestic_lounge_visits=8,
        international_lounge_access="Yes",
        international_lounge_visits=4,
        shopping_benefit="Yes",
        dining_benefit="Yes",
        tag_travel=1,
        tag_international=1,
        tag_shopping=1,
        tag_dining=1,
        tag_airport_lounge=1,
        tag_premium=1
    )
]


# ============================================================
# FIELD LIST
# ============================================================

FIELDNAMES = [
    "debit_card_product_id",
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
    "card_replacement_fee",
    "cash_withdrawal_fee",
    "foreign_currency_markup",

    "minimum_age",
    "maximum_age",
    "minimum_income_monthly",
    "minimum_income_annual",
    "employment_type",
    "minimum_balance_required",
    "residential_requirement",
    "existing_customer_required",
    "eligibility_description",

    "atm_daily_limit",
    "pos_daily_limit",
    "online_daily_limit",
    "international_transaction",
    "contactless_enabled",
    "contactless_limit",
    "pin_change_available",
    "atm_transaction_limit",

    "upi_enabled",
    "internet_banking",
    "mobile_banking",
    "tap_to_pay",
    "qr_payment",

    "reward_program_name",
    "reward_type",
    "reward_points_per_amount",
    "reward_point_value",
    "accelerated_reward_available",
    "accelerated_reward_details",
    "cashback_available",
    "cashback_rate",
    "cashback_monthly_cap",

    "travel_benefit",
    "airport_lounge_access",
    "domestic_lounge_visits",
    "international_lounge_access",
    "international_lounge_visits",
    "priority_pass_available",

    "shopping_benefit",
    "shopping_cashback_rate",
    "dining_benefit",
    "dining_discount",
    "fuel_benefit",
    "fuel_surcharge_waiver",
    "fuel_monthly_cap",
    "movie_benefit",
    "movie_offer_details",

    "insurance_cover",
    "insurance_cover_amount",
    "purchase_protection",
    "lost_card_liability",

    "card_control_app",
    "transaction_alerts",
    "instant_card_block",
    "virtual_card_available",
    "digital_application",
    "instant_issuance",
    "customer_support",

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
    "tag_movie",
    "tag_upi",
    "tag_business",

    "launch_date",
    "end_date",
    "created_at",
    "updated_at"
]


# ============================================================
# WRITE CSV
# ============================================================

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

print("=" * 60)
print("DEBIT CARD PRODUCT DATA GENERATED")
print("=" * 60)
print(f"Total debit cards : {len(cards)}")
print(f"Output file       : {OUTPUT_FILE}")
print("=" * 60)
