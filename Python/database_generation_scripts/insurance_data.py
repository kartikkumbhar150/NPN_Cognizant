import csv

# ============================================================
# CONFIG
# ============================================================

OUTPUT_FILE = "insurance_products.csv"

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

def create_insurance(
    insurance_product_id,
    product_code,
    product_name,
    insurance_company,
    insurance_type,
    plan_type,

    product_status="Active",
    product_description="Bank insurance product.",
    customer_type="Individual",

    minimum_age=18,
    maximum_age=65,
    minimum_income_monthly=0,
    minimum_income_annual=0,
    employment_type="Salaried / Self-employed",
    residential_requirement="Resident Indian",
    existing_customer_required="No",
    eligibility_description="Subject to bank internal eligibility criteria.",

    minimum_sum_insured=100000,
    maximum_sum_insured=10000000,
    premium_frequency="Yearly",
    minimum_premium=1000,
    maximum_premium=100000,
    waiting_period_days=0,

    pre_existing_condition_covered="No",
    pre_existing_condition_waiting_period_days=0,
    hospitalization_coverage="No",
    hospitalization_daily_limit=0,
    cashless_claim_available="No",
    network_hospitals=0,

    room_rent_limit="Not Applicable",
    ambulance_coverage="No",
    ambulance_limit=0,
    diagnostic_coverage="No",
    daycare_procedures="No",
    domiciliary_treatment="No",

    maternity_benefit="No",
    maternity_waiting_period_months=0,
    critical_illness_benefit="No",
    critical_illness_cover_amount=0,
    accidental_death_benefit="No",
    accidental_death_cover_amount=0,
    personal_accident_benefit="No",
    personal_accident_cover_amount=0,

    no_claim_bonus_available="No",
    no_claim_bonus_percent=0,
    tax_benefit="Yes",
    online_purchase_available="Yes",
    digital_policy_available="Yes",
    claim_tracking="Yes",
    customer_support="24x7",

    travel_benefit="No",
    international_coverage="No",
    trip_cancellation="No",
    baggage_loss_cover="No",

    vehicle_damage_cover="No",
    third_party_liability="No",
    roadside_assistance="No",

    life_cover_amount=0,
    policy_term_years=1,
    premium_payment_term_years=1,
    death_benefit="No",
    maturity_benefit="No",
    surrender_benefit="No",

    tag_health=0,
    tag_life=0,
    tag_motor=0,
    tag_travel=0,
    tag_accident=0,
    tag_critical_illness=0,
    tag_family=0,
    tag_tax_saving=0,
    tag_digital=0,
    tag_premium=0,

    launch_date="2020-01-01",
    end_date="2099-12-31"
):

    return {
        "insurance_product_id": insurance_product_id,
        "product_code": product_code,
        "product_name": product_name,
        "insurance_company": insurance_company,
        "insurance_type": insurance_type,
        "plan_type": plan_type,

        "product_status": product_status,
        "product_description": product_description,
        "customer_type": customer_type,

        "minimum_age": minimum_age,
        "maximum_age": maximum_age,
        "minimum_income_monthly": minimum_income_monthly,
        "minimum_income_annual": minimum_income_annual,
        "employment_type": employment_type,
        "residential_requirement": residential_requirement,
        "existing_customer_required": existing_customer_required,
        "eligibility_description": eligibility_description,

        "minimum_sum_insured": minimum_sum_insured,
        "maximum_sum_insured": maximum_sum_insured,
        "premium_frequency": premium_frequency,
        "minimum_premium": minimum_premium,
        "maximum_premium": maximum_premium,
        "waiting_period_days": waiting_period_days,

        "pre_existing_condition_covered": pre_existing_condition_covered,
        "pre_existing_condition_waiting_period_days": pre_existing_condition_waiting_period_days,
        "hospitalization_coverage": hospitalization_coverage,
        "hospitalization_daily_limit": hospitalization_daily_limit,
        "cashless_claim_available": cashless_claim_available,
        "network_hospitals": network_hospitals,

        "room_rent_limit": room_rent_limit,
        "ambulance_coverage": ambulance_coverage,
        "ambulance_limit": ambulance_limit,
        "diagnostic_coverage": diagnostic_coverage,
        "daycare_procedures": daycare_procedures,
        "domiciliary_treatment": domiciliary_treatment,

        "maternity_benefit": maternity_benefit,
        "maternity_waiting_period_months": maternity_waiting_period_months,
        "critical_illness_benefit": critical_illness_benefit,
        "critical_illness_cover_amount": critical_illness_cover_amount,
        "accidental_death_benefit": accidental_death_benefit,
        "accidental_death_cover_amount": accidental_death_cover_amount,
        "personal_accident_benefit": personal_accident_benefit,
        "personal_accident_cover_amount": personal_accident_cover_amount,

        "no_claim_bonus_available": no_claim_bonus_available,
        "no_claim_bonus_percent": no_claim_bonus_percent,
        "tax_benefit": tax_benefit,
        "online_purchase_available": online_purchase_available,
        "digital_policy_available": digital_policy_available,
        "claim_tracking": claim_tracking,
        "customer_support": customer_support,

        "travel_benefit": travel_benefit,
        "international_coverage": international_coverage,
        "trip_cancellation": trip_cancellation,
        "baggage_loss_cover": baggage_loss_cover,

        "vehicle_damage_cover": vehicle_damage_cover,
        "third_party_liability": third_party_liability,
        "roadside_assistance": roadside_assistance,

        "life_cover_amount": life_cover_amount,
        "policy_term_years": policy_term_years,
        "premium_payment_term_years": premium_payment_term_years,
        "death_benefit": death_benefit,
        "maturity_benefit": maturity_benefit,
        "surrender_benefit": surrender_benefit,

        "tag_health": tag_health,
        "tag_life": tag_life,
        "tag_motor": tag_motor,
        "tag_travel": tag_travel,
        "tag_accident": tag_accident,
        "tag_critical_illness": tag_critical_illness,
        "tag_family": tag_family,
        "tag_tax_saving": tag_tax_saving,
        "tag_digital": tag_digital,
        "tag_premium": tag_premium,

        "launch_date": launch_date,
        "end_date": end_date,

        "created_at": CREATED_AT,
        "updated_at": UPDATED_AT
    }


# ============================================================
# INSURANCE PRODUCTS
# ============================================================

insurance_products = [

    # --------------------------------------------------------
    # HEALTH INSURANCE
    # --------------------------------------------------------

    create_insurance(
        "INS001",
        "HDFC_HEALTH_OPTIMA",
        "Health Optima Insurance",
        "HDFC ERGO",
        "Health",
        "Individual Health",
        product_description="Individual health insurance plan covering hospitalization and medical expenses.",
        minimum_age=18,
        maximum_age=65,
        minimum_sum_insured=300000,
        maximum_sum_insured=10000000,
        premium_frequency="Yearly",
        minimum_premium=5000,
        maximum_premium=50000,
        waiting_period_days=30,
        pre_existing_condition_covered="After Waiting Period",
        pre_existing_condition_waiting_period_days=48,
        hospitalization_coverage="Yes",
        hospitalization_daily_limit=5000,
        cashless_claim_available="Yes",
        network_hospitals=13000,
        room_rent_limit="As per policy terms",
        ambulance_coverage="Yes",
        ambulance_limit=5000,
        diagnostic_coverage="Yes",
        daycare_procedures="Yes",
        tax_benefit="Yes",
        tag_health=1,
        tag_tax_saving=1
    ),

    create_insurance(
        "INS002",
        "HDFC_FAMILY_HEALTH",
        "Family Health Insurance",
        "HDFC ERGO",
        "Health",
        "Family Floater",
        product_description="Family floater health insurance for spouse, children and dependents.",
        customer_type="Family",
        minimum_age=18,
        maximum_age=65,
        minimum_sum_insured=500000,
        maximum_sum_insured=15000000,
        premium_frequency="Yearly",
        minimum_premium=8000,
        maximum_premium=75000,
        waiting_period_days=30,
        hospitalization_coverage="Yes",
        cashless_claim_available="Yes",
        network_hospitals=13000,
        maternity_benefit="Yes",
        maternity_waiting_period_months=24,
        ambulance_coverage="Yes",
        diagnostic_coverage="Yes",
        daycare_procedures="Yes",
        no_claim_bonus_available="Yes",
        no_claim_bonus_percent=10,
        tag_health=1,
        tag_family=1,
        tag_tax_saving=1
    ),

    create_insurance(
        "INS003",
        "HDFC_SENIOR_HEALTH",
        "Senior Citizen Health Insurance",
        "HDFC ERGO",
        "Health",
        "Senior Citizen",
        product_description="Health insurance designed for senior citizens.",
        minimum_age=60,
        maximum_age=75,
        minimum_sum_insured=300000,
        maximum_sum_insured=10000000,
        premium_frequency="Yearly",
        minimum_premium=12000,
        maximum_premium=100000,
        waiting_period_days=30,
        pre_existing_condition_covered="After Waiting Period",
        pre_existing_condition_waiting_period_days=48,
        hospitalization_coverage="Yes",
        cashless_claim_available="Yes",
        network_hospitals=13000,
        ambulance_coverage="Yes",
        diagnostic_coverage="Yes",
        daycare_procedures="Yes",
        tag_health=1,
        tag_family=1
    ),

    create_insurance(
        "INS004",
        "HDFC_CRITICAL_ILLNESS",
        "Critical Illness Insurance",
        "HDFC ERGO",
        "Health",
        "Critical Illness",
        product_description="Lump-sum protection against specified critical illnesses.",
        minimum_age=18,
        maximum_age=65,
        minimum_sum_insured=500000,
        maximum_sum_insured=2500000,
        premium_frequency="Yearly",
        minimum_premium=3000,
        maximum_premium=30000,
        critical_illness_benefit="Yes",
        critical_illness_cover_amount=2500000,
        tag_health=1,
        tag_critical_illness=1
    ),

    # --------------------------------------------------------
    # LIFE INSURANCE
    # --------------------------------------------------------

    create_insurance(
        "INS005",
        "HDFC_TERM_LIFE",
        "Term Life Insurance",
        "HDFC Life",
        "Life",
        "Term Life",
        product_description="Pure term insurance providing financial protection to nominees.",
        minimum_age=18,
        maximum_age=65,
        minimum_income_annual=300000,
        minimum_sum_insured=1000000,
        maximum_sum_insured=50000000,
        premium_frequency="Yearly",
        minimum_premium=5000,
        maximum_premium=100000,
        policy_term_years=30,
        premium_payment_term_years=30,
        death_benefit="Yes",
        maturity_benefit="No",
        surrender_benefit="No",
        tax_benefit="Yes",
        tag_life=1,
        tag_tax_saving=1
    ),

    create_insurance(
        "INS006",
        "HDFC_TERM_PLUS",
        "Term Insurance Plus",
        "HDFC Life",
        "Life",
        "Term Life",
        product_description="Term insurance with additional accidental and critical illness protection.",
        minimum_age=18,
        maximum_age=60,
        minimum_income_annual=500000,
        minimum_sum_insured=2500000,
        maximum_sum_insured=50000000,
        premium_frequency="Yearly",
        minimum_premium=8000,
        maximum_premium=125000,
        policy_term_years=30,
        death_benefit="Yes",
        accidental_death_benefit="Yes",
        accidental_death_cover_amount=10000000,
        critical_illness_benefit="Yes",
        critical_illness_cover_amount=2500000,
        tax_benefit="Yes",
        tag_life=1,
        tag_accident=1,
        tag_critical_illness=1,
        tag_tax_saving=1
    ),

    create_insurance(
        "INS007",
        "HDFC_SAVINGS_LIFE",
        "Life Savings Plan",
        "HDFC Life",
        "Life",
        "Savings",
        product_description="Life insurance savings plan with protection and maturity benefits.",
        minimum_age=18,
        maximum_age=55,
        minimum_sum_insured=500000,
        maximum_sum_insured=10000000,
        premium_frequency="Yearly",
        minimum_premium=15000,
        maximum_premium=200000,
        policy_term_years=20,
        premium_payment_term_years=10,
        death_benefit="Yes",
        maturity_benefit="Yes",
        surrender_benefit="Yes",
        tax_benefit="Yes",
        tag_life=1,
        tag_tax_saving=1,
        tag_premium=1
    ),

    create_insurance(
        "INS008",
        "HDFC_CHILD_LIFE",
        "Child Future Life Plan",
        "HDFC Life",
        "Life",
        "Child Plan",
        product_description="Long-term financial protection and savings for a child's future.",
        minimum_age=18,
        maximum_age=50,
        minimum_income_annual=300000,
        minimum_sum_insured=500000,
        maximum_sum_insured=10000000,
        premium_frequency="Yearly",
        minimum_premium=10000,
        maximum_premium=150000,
        policy_term_years=20,
        premium_payment_term_years=10,
        death_benefit="Yes",
        maturity_benefit="Yes",
        tax_benefit="Yes",
        tag_life=1,
        tag_family=1,
        tag_tax_saving=1
    ),

    # --------------------------------------------------------
    # PERSONAL ACCIDENT
    # --------------------------------------------------------

    create_insurance(
        "INS009",
        "HDFC_PERSONAL_ACCIDENT",
        "Personal Accident Insurance",
        "HDFC ERGO",
        "Personal Accident",
        "Accident Cover",
        product_description="Protection against accidental death and disability.",
        minimum_age=18,
        maximum_age=70,
        minimum_sum_insured=500000,
        maximum_sum_insured=10000000,
        premium_frequency="Yearly",
        minimum_premium=1000,
        maximum_premium=15000,
        accidental_death_benefit="Yes",
        accidental_death_cover_amount=10000000,
        personal_accident_benefit="Yes",
        personal_accident_cover_amount=10000000,
        ambulance_coverage="Yes",
        ambulance_limit=10000,
        tag_accident=1
    ),

    create_insurance(
        "INS010",
        "HDFC_ACCIDENT_PLUS",
        "Personal Accident Plus",
        "HDFC ERGO",
        "Personal Accident",
        "Enhanced Accident Cover",
        product_description="Enhanced accident protection with additional medical support.",
        minimum_age=18,
        maximum_age=65,
        minimum_sum_insured=1000000,
        maximum_sum_insured=20000000,
        premium_frequency="Yearly",
        minimum_premium=2000,
        maximum_premium=25000,
        accidental_death_benefit="Yes",
        accidental_death_cover_amount=20000000,
        personal_accident_benefit="Yes",
        personal_accident_cover_amount=20000000,
        ambulance_coverage="Yes",
        ambulance_limit=15000,
        tag_accident=1,
        tag_premium=1
    ),

    # --------------------------------------------------------
    # TRAVEL
    # --------------------------------------------------------

    create_insurance(
        "INS011",
        "HDFC_TRAVEL_INDIA",
        "Domestic Travel Insurance",
        "HDFC ERGO",
        "Travel",
        "Domestic Travel",
        product_description="Insurance for domestic travel emergencies and trip-related risks.",
        minimum_age=18,
        maximum_age=70,
        minimum_sum_insured=100000,
        maximum_sum_insured=5000000,
        premium_frequency="Single",
        minimum_premium=300,
        maximum_premium=10000,
        waiting_period_days=0,
        travel_benefit="Yes",
        international_coverage="No",
        trip_cancellation="Yes",
        baggage_loss_cover="Yes",
        tag_travel=1
    ),

    create_insurance(
        "INS012",
        "HDFC_TRAVEL_GLOBAL",
        "International Travel Insurance",
        "HDFC ERGO",
        "Travel",
        "International Travel",
        product_description="International travel protection covering medical and travel emergencies.",
        minimum_age=18,
        maximum_age=70,
        minimum_sum_insured=500000,
        maximum_sum_insured=10000000,
        premium_frequency="Single",
        minimum_premium=500,
        maximum_premium=25000,
        travel_benefit="Yes",
        international_coverage="Yes",
        trip_cancellation="Yes",
        baggage_loss_cover="Yes",
        tag_travel=1,
        tag_premium=1
    ),

    # --------------------------------------------------------
    # MOTOR
    # --------------------------------------------------------

    create_insurance(
        "INS013",
        "HDFC_CAR_INSURANCE",
        "Comprehensive Car Insurance",
        "HDFC ERGO",
        "Motor",
        "Car Insurance",
        product_description="Comprehensive motor insurance for private cars.",
        minimum_age=18,
        maximum_age=80,
        minimum_sum_insured=100000,
        maximum_sum_insured=50000000,
        premium_frequency="Yearly",
        minimum_premium=2500,
        maximum_premium=75000,
        vehicle_damage_cover="Yes",
        third_party_liability="Yes",
        roadside_assistance="Yes",
        online_purchase_available="Yes",
        digital_policy_available="Yes",
        tag_motor=1,
        tag_digital=1
    ),

    create_insurance(
        "INS014",
        "HDFC_TWO_WHEELER",
        "Two Wheeler Insurance",
        "HDFC ERGO",
        "Motor",
        "Two Wheeler",
        product_description="Motor insurance for motorcycles and scooters.",
        minimum_age=18,
        maximum_age=80,
        minimum_sum_insured=50000,
        maximum_sum_insured=1000000,
        premium_frequency="Yearly",
        minimum_premium=1000,
        maximum_premium=15000,
        vehicle_damage_cover="Yes",
        third_party_liability="Yes",
        roadside_assistance="Yes",
        online_purchase_available="Yes",
        digital_policy_available="Yes",
        tag_motor=1,
        tag_digital=1
    ),

    # --------------------------------------------------------
    # FAMILY / SPECIAL
    # --------------------------------------------------------

    create_insurance(
        "INS015",
        "HDFC_FAMILY_ACCIDENT",
        "Family Personal Accident Cover",
        "HDFC ERGO",
        "Personal Accident",
        "Family Accident",
        product_description="Accident protection for multiple family members.",
        customer_type="Family",
        minimum_age=18,
        maximum_age=65,
        minimum_sum_insured=500000,
        maximum_sum_insured=10000000,
        premium_frequency="Yearly",
        minimum_premium=3000,
        maximum_premium=30000,
        accidental_death_benefit="Yes",
        accidental_death_cover_amount=10000000,
        personal_accident_benefit="Yes",
        personal_accident_cover_amount=10000000,
        tag_accident=1,
        tag_family=1
    ),

    create_insurance(
        "INS016",
        "HDFC_DIGITAL_HEALTH",
        "Digital Health Insurance",
        "HDFC ERGO",
        "Health",
        "Digital Health",
        product_description="Digitally managed health insurance with online purchase and claim tracking.",
        minimum_age=18,
        maximum_age=60,
        minimum_sum_insured=300000,
        maximum_sum_insured=10000000,
        premium_frequency="Yearly",
        minimum_premium=4000,
        maximum_premium=50000,
        waiting_period_days=30,
        hospitalization_coverage="Yes",
        cashless_claim_available="Yes",
        network_hospitals=13000,
        digital_policy_available="Yes",
        online_purchase_available="Yes",
        claim_tracking="Yes",
        tag_health=1,
        tag_digital=1
    ),

    create_insurance(
        "INS017",
        "HDFC_TAX_SAVER_LIFE",
        "Tax Saver Life Insurance",
        "HDFC Life",
        "Life",
        "Tax Saving",
        product_description="Life insurance savings product with eligible tax benefits.",
        minimum_age=18,
        maximum_age=55,
        minimum_income_annual=300000,
        minimum_sum_insured=500000,
        maximum_sum_insured=10000000,
        premium_frequency="Yearly",
        minimum_premium=10000,
        maximum_premium=200000,
        policy_term_years=20,
        premium_payment_term_years=10,
        death_benefit="Yes",
        maturity_benefit="Yes",
        surrender_benefit="Yes",
        tax_benefit="Yes",
        tag_life=1,
        tag_tax_saving=1
    ),

    create_insurance(
        "INS018",
        "HDFC_PREMIUM_HEALTH",
        "Premium Health Insurance",
        "HDFC ERGO",
        "Health",
        "Premium Health",
        product_description="Premium health plan with higher coverage and additional benefits.",
        minimum_age=18,
        maximum_age=65,
        minimum_income_annual=1000000,
        minimum_sum_insured=1000000,
        maximum_sum_insured=25000000,
        premium_frequency="Yearly",
        minimum_premium=15000,
        maximum_premium=150000,
        waiting_period_days=30,
        pre_existing_condition_covered="After Waiting Period",
        pre_existing_condition_waiting_period_days=36,
        hospitalization_coverage="Yes",
        cashless_claim_available="Yes",
        network_hospitals=13000,
        maternity_benefit="Yes",
        maternity_waiting_period_months=24,
        critical_illness_benefit="Yes",
        critical_illness_cover_amount=5000000,
        ambulance_coverage="Yes",
        ambulance_limit=15000,
        diagnostic_coverage="Yes",
        daycare_procedures="Yes",
        no_claim_bonus_available="Yes",
        no_claim_bonus_percent=20,
        tag_health=1,
        tag_premium=1,
        tag_family=1
    )
]


# ============================================================
# FIELD LIST
# ============================================================

FIELDNAMES = [
    "insurance_product_id",
    "product_code",
    "product_name",
    "insurance_company",
    "insurance_type",
    "plan_type",

    "product_status",
    "product_description",
    "customer_type",

    "minimum_age",
    "maximum_age",
    "minimum_income_monthly",
    "minimum_income_annual",
    "employment_type",
    "residential_requirement",
    "existing_customer_required",
    "eligibility_description",

    "minimum_sum_insured",
    "maximum_sum_insured",
    "premium_frequency",
    "minimum_premium",
    "maximum_premium",
    "waiting_period_days",

    "pre_existing_condition_covered",
    "pre_existing_condition_waiting_period_days",
    "hospitalization_coverage",
    "hospitalization_daily_limit",
    "cashless_claim_available",
    "network_hospitals",

    "room_rent_limit",
    "ambulance_coverage",
    "ambulance_limit",
    "diagnostic_coverage",
    "daycare_procedures",
    "domiciliary_treatment",

    "maternity_benefit",
    "maternity_waiting_period_months",
    "critical_illness_benefit",
    "critical_illness_cover_amount",
    "accidental_death_benefit",
    "accidental_death_cover_amount",
    "personal_accident_benefit",
    "personal_accident_cover_amount",

    "no_claim_bonus_available",
    "no_claim_bonus_percent",
    "tax_benefit",
    "online_purchase_available",
    "digital_policy_available",
    "claim_tracking",
    "customer_support",

    "travel_benefit",
    "international_coverage",
    "trip_cancellation",
    "baggage_loss_cover",

    "vehicle_damage_cover",
    "third_party_liability",
    "roadside_assistance",

    "life_cover_amount",
    "policy_term_years",
    "premium_payment_term_years",
    "death_benefit",
    "maturity_benefit",
    "surrender_benefit",

    "tag_health",
    "tag_life",
    "tag_motor",
    "tag_travel",
    "tag_accident",
    "tag_critical_illness",
    "tag_family",
    "tag_tax_saving",
    "tag_digital",
    "tag_premium",

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
    writer.writerows(insurance_products)


# ============================================================
# SUMMARY
# ============================================================

print("=" * 60)
print("INSURANCE PRODUCT DATA GENERATED")
print("=" * 60)
print(f"Total insurance products : {len(insurance_products)}")
print(f"Output file              : {OUTPUT_FILE}")
print("=" * 60)
