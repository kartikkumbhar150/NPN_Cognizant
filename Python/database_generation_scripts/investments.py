import csv

# ============================================================
# CONFIGURATION
# ============================================================

OUTPUT_FILE = "investment_products.csv"

CREATED_AT = "2026-08-16 22:30:00"
UPDATED_AT = "2026-08-16 22:30:00"

TEXT_DEFAULT = "Not Applicable"
NUM_DEFAULT = 0
BOOL_DEFAULT = "No"


# ============================================================
# PRODUCT CREATOR
# ============================================================

def create_investment_product(
    investment_product_id,
    product_code,
    product_name,
    product_category,
    product_subcategory,
    product_type,

    provider="HDFC Bank / HDFC Securities",
    issuer="Not Applicable",
    brand_name="HDFC",
    product_status="Active",
    product_description="Investment product/service for prototype use.",

    # --------------------------------------------------------
    # CUSTOMER / ELIGIBILITY
    # --------------------------------------------------------

    customer_type="Individual",
    residency_requirement="Resident Indian",
    minimum_age=18,
    maximum_age=75,
    minimum_income_annual=0,
    minimum_investment_income_requirement=0,
    employment_type="All",
    kyc_required="Yes",
    pan_required="Yes",
    aadhaar_required="Yes",
    bank_account_required="Yes",
    demat_required="No",
    trading_account_required="No",
    risk_profile="Moderate",
    suitability_required="Yes",
    existing_customer_required="No",

    # --------------------------------------------------------
    # INVESTMENT AMOUNTS
    # --------------------------------------------------------

    minimum_investment=100,
    maximum_investment=100000000,
    minimum_lumpsum=100,
    maximum_lumpsum=100000000,
    minimum_monthly_investment=500,
    maximum_monthly_investment=10000000,
    minimum_additional_investment=100,
    minimum_withdrawal_amount=100,
    maximum_withdrawal_amount=100000000,

    # --------------------------------------------------------
    # RETURNS / RISK
    # --------------------------------------------------------

    return_type="Market Linked",
    indicative_return_min=0,
    indicative_return_max=0,
    guaranteed_return="No",
    capital_protection="No",
    principal_guaranteed="No",
    market_linked="Yes",
    risk_level="Moderate",
    volatility_level="Moderate",
    benchmark="Not Applicable",

    # --------------------------------------------------------
    # INVESTMENT HORIZON
    # --------------------------------------------------------

    minimum_investment_horizon_years=1,
    recommended_investment_horizon_years=5,
    maximum_investment_horizon_years=20,
    liquidity="Medium",
    lock_in_period_years=0,
    exit_available="Yes",
    premature_exit_available="Yes",
    exit_load_applicable="No",
    exit_load_percent=0,

    # --------------------------------------------------------
    # FEES
    # --------------------------------------------------------

    entry_load="No",
    entry_load_percent=0,
    management_fee_percent=0,
    expense_ratio_percent=0,
    brokerage_percent=0,
    brokerage_minimum=0,
    transaction_fee=0,
    account_opening_fee=0,
    annual_maintenance_fee=0,
    advisory_fee_percent=0,
    performance_fee_percent=0,
    exit_fee=0,
    other_charges="Applicable taxes and statutory charges",

    # --------------------------------------------------------
    # TAXATION
    # --------------------------------------------------------

    tax_benefit_available="No",
    tax_deduction_section="Not Applicable",
    capital_gains_tax_applicable="Yes",
    dividend_tax_applicable="Not Applicable",
    tds_applicable="Conditional",
    tax_treatment="Depends on product type and prevailing tax rules",

    # --------------------------------------------------------
    # TRANSACTION MODES
    # --------------------------------------------------------

    lumpsum_available="Yes",
    sip_available="No",
    swp_available="No",
    stp_available="No",
    systematic_transfer_available="No",
    auto_debit_available="Yes",
    one_time_investment_available="Yes",
    recurring_investment_available="No",
    online_investment_available="Yes",
    mobile_investment_available="Yes",
    branch_investment_available="Yes",

    # --------------------------------------------------------
    # REDEMPTION
    # --------------------------------------------------------

    redemption_available="Yes",
    redemption_frequency="As permitted",
    redemption_processing_days=3,
    partial_redemption_allowed="Yes",
    full_redemption_allowed="Yes",
    settlement_method="Bank Account Credit",

    # --------------------------------------------------------
    # PRODUCT-SPECIFIC
    # --------------------------------------------------------

    asset_class="Not Applicable",
    investment_style="Not Applicable",
    fund_type="Not Applicable",
    fund_size_category="Not Applicable",
    portfolio_type="Not Applicable",
    maturity_period_years=0,
    coupon_rate=0,
    coupon_frequency="Not Applicable",
    credit_rating="Not Applicable",
    bond_type="Not Applicable",
    government_or_corporate="Not Applicable",
    nps_tier="Not Applicable",
    nps_asset_allocation="Not Applicable",
    demat_account_type="Not Applicable",
    trading_segment="Not Applicable",
    exchange="Not Applicable",
    equity_market_cap="Not Applicable",
    equity_style="Not Applicable",
    portfolio_advisory_type="Not Applicable",
    relationship_manager_available="No",
    dedicated_advisor="No",
    family_office_support="No",
    succession_planning="No",
    estate_planning="No",
    global_investment_access="No",

    # --------------------------------------------------------
    # DOCUMENTS
    # --------------------------------------------------------

    identity_proof_required="Yes",
    address_proof_required="Yes",
    pan_document_required="Yes",
    bank_statement_required="Conditional",
    income_proof_required="Conditional",
    risk_profile_document_required="Yes",
    kyc_document_required="Yes",
    other_documents="Standard product-specific documents",

    # --------------------------------------------------------
    # DIGITAL / SERVICES
    # --------------------------------------------------------

    digital_onboarding="Yes",
    paperless_processing="Yes",
    e_sign_available="Yes",
    online_portfolio_tracking="Yes",
    mobile_portfolio_tracking="Yes",
    research_available="Yes",
    advisory_available="No",
    portfolio_analysis_available="Yes",
    portfolio_optimizer_available="No",
    market_insights_available="Yes",
    alerts_available="Yes",
    statements_available_online="Yes",

    # --------------------------------------------------------
    # MARKETING TAGS
    # --------------------------------------------------------

    tag_mutual_fund=0,
    tag_sip=0,
    tag_bond=0,
    tag_ncd=0,
    tag_nps=0,
    tag_demat=0,
    tag_equity=0,
    tag_stock=0,
    tag_ipo=0,
    tag_etf=0,
    tag_gold_etf=0,
    tag_wealth_management=0,
    tag_private_banking=0,
    tag_retirement=0,
    tag_tax_saving=0,
    tag_income=0,
    tag_growth=0,
    tag_low_risk=0,
    tag_medium_risk=0,
    tag_high_risk=0,
    tag_liquid=0,
    tag_long_term=0,
    tag_short_term=0,
    tag_premium=0,
    tag_hni=0,
    tag_nri=0,
    tag_digital=0,
    tag_beginner=0,
    tag_experienced_investor=0,

    # --------------------------------------------------------
    # VERSIONING
    # --------------------------------------------------------

    launch_date="2020-01-01",
    end_date="2099-12-31",
    effective_from="2026-01-01",
    effective_to="2099-12-31"
):

    return {
        "investment_product_id": investment_product_id,
        "product_code": product_code,
        "product_name": product_name,
        "product_category": product_category,
        "product_subcategory": product_subcategory,
        "product_type": product_type,

        "provider": provider,
        "issuer": issuer,
        "brand_name": brand_name,
        "product_status": product_status,
        "product_description": product_description,

        # Eligibility
        "customer_type": customer_type,
        "residency_requirement": residency_requirement,
        "minimum_age": minimum_age,
        "maximum_age": maximum_age,
        "minimum_income_annual": minimum_income_annual,
        "minimum_investment_income_requirement":
            minimum_investment_income_requirement,
        "employment_type": employment_type,
        "kyc_required": kyc_required,
        "pan_required": pan_required,
        "aadhaar_required": aadhaar_required,
        "bank_account_required": bank_account_required,
        "demat_required": demat_required,
        "trading_account_required": trading_account_required,
        "risk_profile": risk_profile,
        "suitability_required": suitability_required,
        "existing_customer_required": existing_customer_required,

        # Amounts
        "minimum_investment": minimum_investment,
        "maximum_investment": maximum_investment,
        "minimum_lumpsum": minimum_lumpsum,
        "maximum_lumpsum": maximum_lumpsum,
        "minimum_monthly_investment": minimum_monthly_investment,
        "maximum_monthly_investment": maximum_monthly_investment,
        "minimum_additional_investment": minimum_additional_investment,
        "minimum_withdrawal_amount": minimum_withdrawal_amount,
        "maximum_withdrawal_amount": maximum_withdrawal_amount,

        # Risk/returns
        "return_type": return_type,
        "indicative_return_min": indicative_return_min,
        "indicative_return_max": indicative_return_max,
        "guaranteed_return": guaranteed_return,
        "capital_protection": capital_protection,
        "principal_guaranteed": principal_guaranteed,
        "market_linked": market_linked,
        "risk_level": risk_level,
        "volatility_level": volatility_level,
        "benchmark": benchmark,

        # Horizon
        "minimum_investment_horizon_years":
            minimum_investment_horizon_years,
        "recommended_investment_horizon_years":
            recommended_investment_horizon_years,
        "maximum_investment_horizon_years":
            maximum_investment_horizon_years,
        "liquidity": liquidity,
        "lock_in_period_years": lock_in_period_years,
        "exit_available": exit_available,
        "premature_exit_available": premature_exit_available,
        "exit_load_applicable": exit_load_applicable,
        "exit_load_percent": exit_load_percent,

        # Fees
        "entry_load": entry_load,
        "entry_load_percent": entry_load_percent,
        "management_fee_percent": management_fee_percent,
        "expense_ratio_percent": expense_ratio_percent,
        "brokerage_percent": brokerage_percent,
        "brokerage_minimum": brokerage_minimum,
        "transaction_fee": transaction_fee,
        "account_opening_fee": account_opening_fee,
        "annual_maintenance_fee": annual_maintenance_fee,
        "advisory_fee_percent": advisory_fee_percent,
        "performance_fee_percent": performance_fee_percent,
        "exit_fee": exit_fee,
        "other_charges": other_charges,

        # Tax
        "tax_benefit_available": tax_benefit_available,
        "tax_deduction_section": tax_deduction_section,
        "capital_gains_tax_applicable":
            capital_gains_tax_applicable,
        "dividend_tax_applicable":
            dividend_tax_applicable,
        "tds_applicable": tds_applicable,
        "tax_treatment": tax_treatment,

        # Transactions
        "lumpsum_available": lumpsum_available,
        "sip_available": sip_available,
        "swp_available": swp_available,
        "stp_available": stp_available,
        "systematic_transfer_available":
            systematic_transfer_available,
        "auto_debit_available": auto_debit_available,
        "one_time_investment_available":
            one_time_investment_available,
        "recurring_investment_available":
            recurring_investment_available,
        "online_investment_available":
            online_investment_available,
        "mobile_investment_available":
            mobile_investment_available,
        "branch_investment_available":
            branch_investment_available,

        # Redemption
        "redemption_available": redemption_available,
        "redemption_frequency": redemption_frequency,
        "redemption_processing_days":
            redemption_processing_days,
        "partial_redemption_allowed":
            partial_redemption_allowed,
        "full_redemption_allowed":
            full_redemption_allowed,
        "settlement_method": settlement_method,

        # Product specific
        "asset_class": asset_class,
        "investment_style": investment_style,
        "fund_type": fund_type,
        "fund_size_category": fund_size_category,
        "portfolio_type": portfolio_type,
        "maturity_period_years": maturity_period_years,
        "coupon_rate": coupon_rate,
        "coupon_frequency": coupon_frequency,
        "credit_rating": credit_rating,
        "bond_type": bond_type,
        "government_or_corporate": government_or_corporate,
        "nps_tier": nps_tier,
        "nps_asset_allocation": nps_asset_allocation,
        "demat_account_type": demat_account_type,
        "trading_segment": trading_segment,
        "exchange": exchange,
        "equity_market_cap": equity_market_cap,
        "equity_style": equity_style,
        "portfolio_advisory_type": portfolio_advisory_type,
        "relationship_manager_available":
            relationship_manager_available,
        "dedicated_advisor": dedicated_advisor,
        "family_office_support":
            family_office_support,
        "succession_planning":
            succession_planning,
        "estate_planning":
            estate_planning,
        "global_investment_access":
            global_investment_access,

        # Documents
        "identity_proof_required":
            identity_proof_required,
        "address_proof_required":
            address_proof_required,
        "pan_document_required":
            pan_document_required,
        "bank_statement_required":
            bank_statement_required,
        "income_proof_required":
            income_proof_required,
        "risk_profile_document_required":
            risk_profile_document_required,
        "kyc_document_required":
            kyc_document_required,
        "other_documents":
            other_documents,

        # Digital
        "digital_onboarding":
            digital_onboarding,
        "paperless_processing":
            paperless_processing,
        "e_sign_available":
            e_sign_available,
        "online_portfolio_tracking":
            online_portfolio_tracking,
        "mobile_portfolio_tracking":
            mobile_portfolio_tracking,
        "research_available":
            research_available,
        "advisory_available":
            advisory_available,
        "portfolio_analysis_available":
            portfolio_analysis_available,
        "portfolio_optimizer_available":
            portfolio_optimizer_available,
        "market_insights_available":
            market_insights_available,
        "alerts_available":
            alerts_available,
        "statements_available_online":
            statements_available_online,

        # Tags
        "tag_mutual_fund": tag_mutual_fund,
        "tag_sip": tag_sip,
        "tag_bond": tag_bond,
        "tag_ncd": tag_ncd,
        "tag_nps": tag_nps,
        "tag_demat": tag_demat,
        "tag_equity": tag_equity,
        "tag_stock": tag_stock,
        "tag_ipo": tag_ipo,
        "tag_etf": tag_etf,
        "tag_gold_etf": tag_gold_etf,
        "tag_wealth_management":
            tag_wealth_management,
        "tag_private_banking":
            tag_private_banking,
        "tag_retirement": tag_retirement,
        "tag_tax_saving": tag_tax_saving,
        "tag_income": tag_income,
        "tag_growth": tag_growth,
        "tag_low_risk": tag_low_risk,
        "tag_medium_risk": tag_medium_risk,
        "tag_high_risk": tag_high_risk,
        "tag_liquid": tag_liquid,
        "tag_long_term": tag_long_term,
        "tag_short_term": tag_short_term,
        "tag_premium": tag_premium,
        "tag_hni": tag_hni,
        "tag_nri": tag_nri,
        "tag_digital": tag_digital,
        "tag_beginner": tag_beginner,
        "tag_experienced_investor":
            tag_experienced_investor,

        # Versioning
        "launch_date": launch_date,
        "end_date": end_date,
        "effective_from": effective_from,
        "effective_to": effective_to,
        "created_at": CREATED_AT,
        "updated_at": UPDATED_AT
    }


# ============================================================
# PRODUCT CATALOGUE
# ============================================================

products = [

    # ========================================================
    # MUTUAL FUNDS
    # ========================================================

    create_investment_product(
        "INV001",
        "HDFC_MF_EQUITY_DIVERSIFIED",
        "HDFC Equity Diversified Mutual Fund",
        "Mutual Funds",
        "Equity",
        "Equity Mutual Fund",

        provider="HDFC Securities",
        issuer="HDFC Mutual Fund",
        brand_name="HDFC Mutual Fund",

        customer_type="Individual",
        risk_profile="High",
        risk_level="High",
        volatility_level="High",

        minimum_investment=500,
        minimum_lumpsum=500,
        maximum_investment=100000000,
        minimum_monthly_investment=500,
        maximum_monthly_investment=10000000,

        return_type="Market Linked",
        indicative_return_min=-20,
        indicative_return_max=20,
        guaranteed_return="No",
        capital_protection="No",
        principal_guaranteed="No",
        market_linked="Yes",

        minimum_investment_horizon_years=3,
        recommended_investment_horizon_years=7,
        maximum_investment_horizon_years=20,
        liquidity="High",

        management_fee_percent=1.50,
        expense_ratio_percent=1.50,
        entry_load="No",

        exit_load_applicable="Yes",
        exit_load_percent=1.00,

        lumpsum_available="Yes",
        sip_available="Yes",
        swp_available="Yes",
        stp_available="Yes",
        recurring_investment_available="Yes",

        fund_type="Open Ended",
        asset_class="Equity",
        investment_style="Diversified Equity",
        portfolio_type="Growth",

        benchmark="NIFTY 500 TRI",

        online_investment_available="Yes",
        mobile_investment_available="Yes",
        branch_investment_available="Yes",

        research_available="Yes",
        portfolio_analysis_available="Yes",
        market_insights_available="Yes",

        tag_mutual_fund=1,
        tag_growth=1,
        tag_high_risk=1,
        tag_long_term=1,
        tag_beginner=1,
        tag_digital=1
    ),

    create_investment_product(
        "INV002",
        "HDFC_MF_BALANCED_ADVANTAGE",
        "HDFC Balanced Advantage Fund",
        "Mutual Funds",
        "Hybrid",
        "Hybrid Mutual Fund",

        provider="HDFC Securities",
        issuer="HDFC Mutual Fund",
        brand_name="HDFC Mutual Fund",

        risk_profile="Moderate",
        risk_level="Moderate",
        volatility_level="Moderate",

        minimum_investment=100,
        minimum_lumpsum=100,
        minimum_monthly_investment=100,

        return_type="Market Linked",
        indicative_return_min=-10,
        indicative_return_max=14,

        minimum_investment_horizon_years=3,
        recommended_investment_horizon_years=5,
        maximum_investment_horizon_years=15,

        liquidity="High",
        management_fee_percent=1.30,
        expense_ratio_percent=1.30,

        exit_load_applicable="Yes",
        exit_load_percent=1,

        lumpsum_available="Yes",
        sip_available="Yes",
        swp_available="Yes",
        stp_available="Yes",

        fund_type="Open Ended",
        asset_class="Equity + Debt",
        investment_style="Dynamic Asset Allocation",
        portfolio_type="Balanced",

        benchmark="Hybrid Composite Index",

        online_investment_available="Yes",
        mobile_investment_available="Yes",
        branch_investment_available="Yes",

        research_available="Yes",
        portfolio_analysis_available="Yes",

        tag_mutual_fund=1,
        tag_medium_risk=1,
        tag_growth=1,
        tag_long_term=1,
        tag_digital=1
    ),

    create_investment_product(
        "INV003",
        "HDFC_MF_LIQUID",
        "HDFC Liquid Fund",
        "Mutual Funds",
        "Debt",
        "Liquid Mutual Fund",

        provider="HDFC Securities",
        issuer="HDFC Mutual Fund",
        brand_name="HDFC Mutual Fund",

        risk_profile="Low",
        risk_level="Low",
        volatility_level="Low",

        minimum_investment=500,
        minimum_lumpsum=500,

        return_type="Market Linked",
        indicative_return_min=4,
        indicative_return_max=7,

        minimum_investment_horizon_years=0,
        recommended_investment_horizon_years=1,
        maximum_investment_horizon_years=3,

        liquidity="Very High",

        management_fee_percent=0.30,
        expense_ratio_percent=0.30,

        exit_load_applicable="No",

        lumpsum_available="Yes",
        sip_available="Yes",
        swp_available="Yes",

        fund_type="Open Ended",
        asset_class="Debt",
        investment_style="Short Duration Debt",
        portfolio_type="Liquid",

        benchmark="CRISIL Liquid Debt Index",

        online_investment_available="Yes",
        mobile_investment_available="Yes",

        redemption_processing_days=1,

        tag_mutual_fund=1,
        tag_low_risk=1,
        tag_liquid=1,
        tag_short_term=1,
        tag_digital=1
    ),

    # ========================================================
    # SIP
    # ========================================================

    create_investment_product(
        "INV004",
        "HDFC_SIP_EQUITY",
        "HDFC Mutual Fund SIP",
        "SIP",
        "Equity SIP",
        "Systematic Investment Plan",

        provider="HDFC Securities",
        issuer="HDFC Mutual Fund",
        brand_name="HDFC Mutual Fund",

        minimum_investment=500,
        minimum_monthly_investment=500,
        maximum_monthly_investment=10000000,

        risk_profile="High",
        risk_level="High",
        volatility_level="High",

        return_type="Market Linked",
        indicative_return_min=-20,
        indicative_return_max=20,

        minimum_investment_horizon_years=5,
        recommended_investment_horizon_years=10,
        maximum_investment_horizon_years=30,

        liquidity="High",

        auto_debit_available="Yes",
        recurring_investment_available="Yes",
        sip_available="Yes",
        online_investment_available="Yes",
        mobile_investment_available="Yes",


        asset_class="Equity",
        investment_style="Systematic Long-Term Investing",

        research_available="Yes",
        portfolio_analysis_available="Yes",

        tag_sip=1,
        tag_mutual_fund=1,
        tag_growth=1,
        tag_high_risk=1,
        tag_long_term=1,
        tag_digital=1,
        tag_beginner=1
    ),

    # ========================================================
    # BONDS
    # ========================================================

    create_investment_product(
        "INV005",
        "HDFC_BONDS_CORPORATE",
        "Corporate Bonds",
        "Bonds",
        "Corporate Bonds",
        "Debt Securities",

        provider="HDFC Securities",
        issuer="Multiple Corporate Issuers",

        risk_profile="Moderate",
        risk_level="Moderate",
        volatility_level="Low",

        minimum_investment=1000,
        maximum_investment=100000000,

        return_type="Coupon + Capital Appreciation",
        indicative_return_min=6,
        indicative_return_max=11,
        guaranteed_return="No",
        principal_guaranteed="Conditional",

        minimum_investment_horizon_years=2,
        recommended_investment_horizon_years=5,
        maximum_investment_horizon_years=15,

        liquidity="Medium",
        maturity_period_years=5,

        coupon_rate=8.0,
        coupon_frequency="Annual",

        credit_rating="AAA / AA / Investment Grade",
        bond_type="Corporate Bond",
        government_or_corporate="Corporate",

        demat_required="Yes",
        trading_account_required="No",

        online_investment_available="Yes",
        mobile_investment_available="Yes",

        tag_bond=1,
        tag_income=1,
        tag_medium_risk=1,
        tag_long_term=1,
        tag_digital=1
    ),

    create_investment_product(
        "INV006",
        "HDFC_NCD",
        "Non-Convertible Debentures (NCDs)",
        "Bonds",
        "NCD",
        "Non-Convertible Debenture",

        provider="HDFC Securities",
        issuer="Corporate Issuer",

        minimum_investment=1000,
        maximum_investment=100000000,

        risk_profile="Moderate",
        risk_level="Moderate",
        volatility_level="Low",

        return_type="Fixed Coupon",
        indicative_return_min=7,
        indicative_return_max=12,

        guaranteed_return="No",
        capital_protection="Conditional",

        minimum_investment_horizon_years=1,
        recommended_investment_horizon_years=3,
        maximum_investment_horizon_years=10,

        liquidity="Medium",

        maturity_period_years=3,
        coupon_rate=9,
        coupon_frequency="Annual",

        credit_rating="Investment Grade",
        bond_type="NCD",
        government_or_corporate="Corporate",

        demat_required="Yes",

        online_investment_available="Yes",
        mobile_investment_available="Yes",

        tag_bond=1,
        tag_ncd=1,
        tag_income=1,
        tag_medium_risk=1
    ),

    # ========================================================
    # NPS
    # ========================================================

    create_investment_product(
        "INV007",
        "HDFC_NPS_TIER_I",
        "NPS Tier I",
        "NPS",
        "Retirement",
        "National Pension System",

        provider="HDFC Bank / HDFC Pension",
        issuer="PFRDA-regulated NPS ecosystem",

        minimum_age=18,
        maximum_age=70,

        minimum_investment=500,
        minimum_lumpsum=500,
        minimum_monthly_investment=500,

        risk_profile="Moderate",
        risk_level="Moderate",
        volatility_level="Moderate",

        return_type="Market Linked",

        minimum_investment_horizon_years=10,
        recommended_investment_horizon_years=20,
        maximum_investment_horizon_years=40,

        liquidity="Low",
        lock_in_period_years=60,

        exit_available="Conditional",
        premature_exit_available="Conditional",

        tax_benefit_available="Yes",
        tax_deduction_section="80CCD",
        capital_gains_tax_applicable="Conditional",

        lumpsum_available="Yes",
        recurring_investment_available="Yes",
        auto_debit_available="Yes",

        asset_class="Equity + Corporate Bonds + Government Securities",
        portfolio_type="Retirement Portfolio",

        nps_tier="Tier I",
        nps_asset_allocation="Equity / Corporate Bonds / Government Securities",

        online_investment_available="Yes",
        mobile_investment_available="Yes",

        research_available="Yes",
        portfolio_analysis_available="Yes",

        tag_nps=1,
        tag_retirement=1,
        tag_tax_saving=1,
        tag_medium_risk=1,
        tag_long_term=1,
        tag_digital=1
    ),

    create_investment_product(
        "INV008",
        "HDFC_NPS_TIER_II",
        "NPS Tier II",
        "NPS",
        "Flexible Retirement Investment",
        "National Pension System",

        provider="HDFC Bank / HDFC Pension",
        issuer="PFRDA-regulated NPS ecosystem",

        minimum_age=18,
        maximum_age=70,

        minimum_investment=1000,
        minimum_lumpsum=1000,
        minimum_monthly_investment=500,

        risk_profile="Moderate",
        risk_level="Moderate",
        volatility_level="Moderate",

        return_type="Market Linked",

        minimum_investment_horizon_years=3,
        recommended_investment_horizon_years=10,
        maximum_investment_horizon_years=30,

        liquidity="High",
        lock_in_period_years=0,

        exit_available="Yes",
        premature_exit_available="Yes",

        tax_benefit_available="Conditional",

        lumpsum_available="Yes",
        recurring_investment_available="Yes",
        auto_debit_available="Yes",

        asset_class="Equity + Corporate Bonds + Government Securities",
        portfolio_type="Flexible Retirement Portfolio",

        nps_tier="Tier II",
        nps_asset_allocation="Equity / Corporate Bonds / Government Securities",

        online_investment_available="Yes",
        mobile_investment_available="Yes",

        tag_nps=1,
        tag_retirement=1,
        tag_medium_risk=1,
        tag_digital=1
    ),

    # ========================================================
    # DEMAT
    # ========================================================

    create_investment_product(
        "INV009",
        "HDFC_DEMAT_STANDARD",
        "HDFC Demat Account",
        "Demat Account",
        "Dematerialized Securities Account",
        "Demat Account",

        provider="HDFC Securities / HDFC Bank DP",
        issuer="NSDL / CDSL",

        minimum_age=18,
        maximum_age=99,

        minimum_investment=0,
        maximum_investment=1000000000,

        risk_profile="Depends on holdings",
        risk_level="Not Applicable",
        volatility_level="Not Applicable",

        return_type="Not Applicable",

        liquidity="High",

        demat_required="No",
        trading_account_required="Conditional",

        account_opening_fee=0,
        annual_maintenance_fee=0,

        lumpsum_available="Yes",

        asset_class="Equity, Bonds, ETFs, Mutual Funds and Other Eligible Securities",
        demat_account_type="Individual Demat Account",

        online_investment_available="Yes",
        mobile_investment_available="Yes",
        branch_investment_available="Yes",

        online_portfolio_tracking="Yes",
        mobile_portfolio_tracking="Yes",
        portfolio_analysis_available="Yes",

        research_available="Yes",
        market_insights_available="Yes",
        alerts_available="Yes",

        tag_demat=1,
        tag_equity=1,
        tag_bond=1,
        tag_etf=1,
        tag_digital=1
    ),

    create_investment_product(
        "INV010",
        "HDFC_DEMAT_3IN1",
        "HDFC 3-in-1 Investment Account",
        "Demat Account",
        "Integrated Banking + Demat + Trading",
        "3-in-1 Investment Account",

        provider="HDFC Bank + HDFC Securities",
        issuer="NSDL / CDSL",

        minimum_age=18,
        maximum_age=70,

        minimum_investment=0,

        risk_profile="Depends on investments",
        risk_level="Not Applicable",

        liquidity="High",

        demat_required="Yes",
        trading_account_required="Yes",

        account_opening_fee=0,
        annual_maintenance_fee=0,

        lumpsum_available="Yes",

        asset_class="Equity, ETFs, Mutual Funds, IPOs, Bonds and Derivatives",
        demat_account_type="Integrated 3-in-1 Account",
        trading_segment="Equity, F&O, ETFs, Mutual Funds, IPO",

        online_investment_available="Yes",
        mobile_investment_available="Yes",

        relationship_manager_available="Yes",
        research_available="Yes",
        portfolio_analysis_available="Yes",
        market_insights_available="Yes",

        portfolio_optimizer_available="Yes",

        tag_demat=1,
        tag_equity=1,
        tag_ipo=1,
        tag_etf=1,
        tag_bond=1,
        tag_mutual_fund=1,
        tag_digital=1,
        tag_experienced_investor=1
    ),

    # ========================================================
    # EQUITY / STOCK
    # ========================================================

    create_investment_product(
        "INV011",
        "HDFC_EQUITY_TRADING",
        "Equity Trading",
        "Equity",
        "Stocks",
        "Equity Investment",

        provider="HDFC Securities",
        issuer="Listed Companies",

        minimum_investment=100,
        maximum_investment=1000000000,

        risk_profile="High",
        risk_level="High",
        volatility_level="High",

        return_type="Market Linked",
        indicative_return_min=-50,
        indicative_return_max=50,

        liquidity="High",

        demat_required="Yes",
        trading_account_required="Yes",

        brokerage_percent=0.30,
        brokerage_minimum=20,

        lumpsum_available="Yes",

        asset_class="Equity",
        investment_style="Direct Equity",
        equity_market_cap="Large / Mid / Small Cap",
        equity_style="Value / Growth / Blend",
        exchange="NSE / BSE",

        online_investment_available="Yes",
        mobile_investment_available="Yes",

        research_available="Yes",
        portfolio_analysis_available="Yes",
        portfolio_optimizer_available="Yes",
        market_insights_available="Yes",

        tag_equity=1,
        tag_stock=1,
        tag_growth=1,
        tag_high_risk=1,
        tag_digital=1,
        tag_experienced_investor=1
    ),

    # ========================================================
    # IPO
    # ========================================================

    create_investment_product(
        "INV012",
        "HDFC_IPO_INVESTMENT",
        "IPO Investment",
        "Equity",
        "Initial Public Offering",
        "IPO",

        provider="HDFC Securities",
        issuer="Issuing Company",

        minimum_investment=1000,
        maximum_investment=1000000,

        risk_profile="High",
        risk_level="High",
        volatility_level="High",

        return_type="Market Linked",

        minimum_investment_horizon_years=1,
        recommended_investment_horizon_years=3,

        liquidity="High",

        demat_required="Yes",
        trading_account_required="Yes",

        asset_class="Equity",
        exchange="NSE / BSE",

        online_investment_available="Yes",
        mobile_investment_available="Yes",

        research_available="Yes",
        market_insights_available="Yes",

        tag_equity=1,
        tag_stock=1,
        tag_ipo=1,
        tag_high_risk=1,
        tag_digital=1,
        tag_experienced_investor=1
    ),

    # ========================================================
    # ETF
    # ========================================================

    create_investment_product(
        "INV013",
        "HDFC_ETF",
        "Exchange Traded Funds",
        "ETF",
        "ETF Investment",
        "Exchange Traded Fund",

        provider="HDFC Securities",
        issuer="Various Fund Houses",

        minimum_investment=100,
        maximum_investment=100000000,

        risk_profile="Moderate to High",
        risk_level="Moderate",
        volatility_level="Moderate",

        return_type="Market Linked",

        minimum_investment_horizon_years=3,
        recommended_investment_horizon_years=7,

        liquidity="High",

        demat_required="Yes",
        trading_account_required="Yes",

        brokerage_percent=0.20,

        asset_class="Equity / Debt / Commodity",
        investment_style="Passive / Index Tracking",

        exchange="NSE / BSE",

        lumpsum_available="Yes",
        recurring_investment_available="Yes",

        online_investment_available="Yes",
        mobile_investment_available="Yes",

        research_available="Yes",
        portfolio_analysis_available="Yes",

        tag_etf=1,
        tag_equity=1,
        tag_growth=1,
        tag_medium_risk=1,
        tag_long_term=1,
        tag_digital=1
    ),

    # ========================================================
    # GOLD ETF
    # ========================================================

    create_investment_product(
        "INV014",
        "HDFC_GOLD_ETF",
        "Gold ETF",
        "ETF",
        "Gold ETF",
        "Exchange Traded Fund",

        provider="HDFC Securities",
        issuer="Various Asset Managers",

        minimum_investment=100,
        maximum_investment=100000000,

        risk_profile="Moderate",
        risk_level="Moderate",
        volatility_level="Moderate",

        return_type="Market Linked",

        minimum_investment_horizon_years=3,
        recommended_investment_horizon_years=7,

        liquidity="High",

        demat_required="Yes",
        trading_account_required="Yes",

        brokerage_percent=0.20,

        asset_class="Gold",
        investment_style="Gold-linked",

        exchange="NSE / BSE",

        recurring_investment_available="Yes",
        lumpsum_available="Yes",

        online_investment_available="Yes",
        mobile_investment_available="Yes",

        tag_etf=1,
        tag_gold_etf=1,
        tag_medium_risk=1,
        tag_long_term=1,
        tag_digital=1
    ),

    # ========================================================
    # WEALTH MANAGEMENT
    # ========================================================

    create_investment_product(
        "INV015",
        "HDFC_WEALTH_MANAGEMENT",
        "HDFC Wealth Management",
        "Wealth Management",
        "Managed Wealth Advisory",
        "Wealth Management Service",

        provider="HDFC Bank",
        issuer="HDFC Bank",

        customer_type="High Net Worth Individual",
        residency_requirement="Resident / NRI",
        minimum_age=18,
        maximum_age=85,

        minimum_income_annual=5000000,
        minimum_investment=2500000,

        risk_profile="Personalized",
        risk_level="Personalized",
        volatility_level="Personalized",

        return_type="Portfolio Dependent",

        minimum_investment_horizon_years=3,
        recommended_investment_horizon_years=7,
        maximum_investment_horizon_years=30,

        liquidity="Customized",

        advisory_fee_percent=1.00,
        performance_fee_percent=10.00,

        lumpsum_available="Yes",
        recurring_investment_available="Yes",

        online_investment_available="Yes",
        mobile_investment_available="Yes",

        relationship_manager_available="Yes",
        dedicated_advisor="Yes",
        advisory_available="Yes",
        portfolio_analysis_available="Yes",
        portfolio_optimizer_available="Yes",
        research_available="Yes",
        market_insights_available="Yes",

        succession_planning="Yes",
        estate_planning="Yes",
        global_investment_access="Yes",

        asset_class="Multi-Asset",
        portfolio_type="Customized Wealth Portfolio",
        portfolio_advisory_type="Goal-based / Risk-based Advisory",

        tag_wealth_management=1,
        tag_premium=1,
        tag_hni=1,
        tag_long_term=1,
        tag_high_risk=1,
        tag_medium_risk=1
    ),

    # ========================================================
    # PRIVATE BANKING
    # ========================================================

    create_investment_product(
        "INV016",
        "HDFC_PRIVATE_BANKING",
        "HDFC Private Banking",
        "Private Banking",
        "Private Wealth Services",
        "Private Banking Service",

        provider="HDFC Bank",
        issuer="HDFC Bank",

        customer_type="Ultra High Net Worth Individual",
        residency_requirement="Resident / NRI",
        minimum_age=18,
        maximum_age=90,

        minimum_income_annual=10000000,
        minimum_investment=10000000,

        risk_profile="Personalized",
        risk_level="Personalized",
        volatility_level="Personalized",

        return_type="Portfolio Dependent",

        minimum_investment_horizon_years=5,
        recommended_investment_horizon_years=10,
        maximum_investment_horizon_years=50,

        liquidity="Customized",

        advisory_fee_percent=0.75,
        performance_fee_percent=10.00,

        lumpsum_available="Yes",
        recurring_investment_available="Yes",

        online_investment_available="Yes",
        mobile_investment_available="Yes",

        relationship_manager_available="Yes",
        dedicated_advisor="Yes",
        family_office_support="Yes",
        succession_planning="Yes",
        estate_planning="Yes",
        global_investment_access="Yes",

        advisory_available="Yes",
        portfolio_analysis_available="Yes",
        portfolio_optimizer_available="Yes",
        research_available="Yes",
        market_insights_available="Yes",

        asset_class="Multi-Asset / Alternative Investments",
        portfolio_type="Customized Private Wealth Portfolio",
        portfolio_advisory_type="Discretionary / Non-discretionary Wealth Advisory",

        tag_private_banking=1,
        tag_wealth_management=1,
        tag_premium=1,
        tag_hni=1,
        tag_nri=1,
        tag_long_term=1
    ),

    # ========================================================
    # STOCK SIP
    # ========================================================

    create_investment_product(
        "INV017",
        "HDFC_STOCK_SIP",
        "StockSIP",
        "Equity",
        "Systematic Stock Investment",
        "Stock SIP",

        provider="HDFC Securities",
        issuer="Listed Companies",

        minimum_investment=500,
        maximum_investment=1000000,
        minimum_monthly_investment=500,

        risk_profile="High",
        risk_level="High",
        volatility_level="High",

        return_type="Market Linked",
        indicative_return_min=-30,
        indicative_return_max=30,

        minimum_investment_horizon_years=5,
        recommended_investment_horizon_years=10,

        liquidity="High",

        demat_required="Yes",
        trading_account_required="Yes",

        brokerage_percent=0.20,

        recurring_investment_available="Yes",
        auto_debit_available="Yes",

        asset_class="Equity",
        investment_style="Systematic Direct Equity",

        exchange="NSE / BSE",

        online_investment_available="Yes",
        mobile_investment_available="Yes",

        research_available="Yes",
        portfolio_analysis_available="Yes",

        tag_equity=1,
        tag_stock=1,
        tag_sip=1,
        tag_growth=1,
        tag_high_risk=1,
        tag_long_term=1,
        tag_digital=1
    ),

    # ========================================================
    # GOLD SAVINGS / INVESTMENT
    # ========================================================

    create_investment_product(
        "INV018",
        "HDFC_GOLD_INVESTMENT",
        "Gold Investment",
        "Gold",
        "Digital Gold / Gold Investment",
        "Gold Investment",

        provider="HDFC Securities / Partner Platform",
        issuer="Approved Gold Provider",

        minimum_investment=100,
        maximum_investment=10000000,

        risk_profile="Moderate",
        risk_level="Moderate",
        volatility_level="Moderate",

        return_type="Market Linked",

        minimum_investment_horizon_years=3,
        recommended_investment_horizon_years=7,

        liquidity="High",

        lumpsum_available="Yes",
        recurring_investment_available="Yes",

        online_investment_available="Yes",
        mobile_investment_available="Yes",

        asset_class="Gold",

        tag_gold_etf=1,
        tag_medium_risk=1,
        tag_long_term=1,
        tag_digital=1
    ),

    # ========================================================
    # PORTFOLIO MANAGEMENT
    # ========================================================

    create_investment_product(
        "INV019",
        "HDFC_PORTFOLIO_ADVISORY",
        "HDFC Portfolio Advisory",
        "Wealth Management",
        "Portfolio Advisory",
        "Investment Advisory Service",

        provider="HDFC Bank / HDFC Securities",
        issuer="HDFC Bank / HDFC Securities",

        customer_type="HNI / Premium",
        residency_requirement="Resident / NRI",

        minimum_age=18,
        maximum_age=85,

        minimum_income_annual=5000000,
        minimum_investment=5000000,

        risk_profile="Personalized",
        risk_level="Personalized",

        return_type="Portfolio Dependent",

        minimum_investment_horizon_years=3,
        recommended_investment_horizon_years=10,

        liquidity="Customized",

        advisory_fee_percent=1,
        performance_fee_percent=10,

        lumpsum_available="Yes",
        recurring_investment_available="Yes",

        online_investment_available="Yes",
        mobile_investment_available="Yes",

        advisory_available="Yes",
        dedicated_advisor="Yes",
        relationship_manager_available="Yes",
        portfolio_analysis_available="Yes",
        portfolio_optimizer_available="Yes",

        portfolio_advisory_type="Goal-based Portfolio Advisory",
        portfolio_type="Customized Multi-Asset Portfolio",

        tag_wealth_management=1,
        tag_premium=1,
        tag_hni=1,
        tag_long_term=1
    ),

    # ========================================================
    # NRI INVESTMENT ACCOUNT
    # ========================================================

    create_investment_product(
        "INV020",
        "HDFC_NRI_3IN1_INVESTMENT",
        "HDFC NRI 3-in-1 Investment Account",
        "Demat Account",
        "NRI Investment Account",
        "3-in-1 NRI Investment Account",

        provider="HDFC Bank + HDFC Securities",
        issuer="NSDL / CDSL",

        customer_type="NRI",
        residency_requirement="NRI",
        minimum_age=18,
        maximum_age=75,

        minimum_investment=1000,

        risk_profile="Depends on investment",
        risk_level="Personalized",

        liquidity="High",

        demat_required="Yes",
        trading_account_required="Yes",

        asset_class="Equity, IPOs, ETFs, Mutual Funds and Derivatives",

        demat_account_type="NRI Demat + Trading + PIS",
        trading_segment="Equity, IPO, Derivatives, MF, ETF",

        online_investment_available="Yes",
        mobile_investment_available="Yes",

        relationship_manager_available="Yes",
        dedicated_advisor="Yes",

        research_available="Yes",
        market_insights_available="Yes",

        global_investment_access="Yes",

        tag_demat=1,
        tag_nri=1,
        tag_equity=1,
        tag_ipo=1,
        tag_etf=1,
        tag_mutual_fund=1,
        tag_digital=1
    )
]


# ============================================================
# FIELD NAMES
# ============================================================

FIELDNAMES = [
    "investment_product_id",
    "product_code",
    "product_name",
    "product_category",
    "product_subcategory",
    "product_type",

    "provider",
    "issuer",
    "brand_name",
    "product_status",
    "product_description",

    "customer_type",
    "residency_requirement",
    "minimum_age",
    "maximum_age",
    "minimum_income_annual",
    "minimum_investment_income_requirement",
    "employment_type",
    "kyc_required",
    "pan_required",
    "aadhaar_required",
    "bank_account_required",
    "demat_required",
    "trading_account_required",
    "risk_profile",
    "suitability_required",
    "existing_customer_required",

    "minimum_investment",
    "maximum_investment",
    "minimum_lumpsum",
    "maximum_lumpsum",
    "minimum_monthly_investment",
    "maximum_monthly_investment",
    "minimum_additional_investment",
    "minimum_withdrawal_amount",
    "maximum_withdrawal_amount",

    "return_type",
    "indicative_return_min",
    "indicative_return_max",
    "guaranteed_return",
    "capital_protection",
    "principal_guaranteed",
    "market_linked",
    "risk_level",
    "volatility_level",
    "benchmark",

    "minimum_investment_horizon_years",
    "recommended_investment_horizon_years",
    "maximum_investment_horizon_years",
    "liquidity",
    "lock_in_period_years",
    "exit_available",
    "premature_exit_available",
    "exit_load_applicable",
    "exit_load_percent",

    "entry_load",
    "entry_load_percent",
    "management_fee_percent",
    "expense_ratio_percent",
    "brokerage_percent",
    "brokerage_minimum",
    "transaction_fee",
    "account_opening_fee",
    "annual_maintenance_fee",
    "advisory_fee_percent",
    "performance_fee_percent",
    "exit_fee",
    "other_charges",

    "tax_benefit_available",
    "tax_deduction_section",
    "capital_gains_tax_applicable",
    "dividend_tax_applicable",
    "tds_applicable",
    "tax_treatment",

    "lumpsum_available",
    "sip_available",
    "swp_available",
    "stp_available",
    "systematic_transfer_available",
    "auto_debit_available",
    "one_time_investment_available",
    "recurring_investment_available",
    "online_investment_available",
    "mobile_investment_available",
    "branch_investment_available",

    "redemption_available",
    "redemption_frequency",
    "redemption_processing_days",
    "partial_redemption_allowed",
    "full_redemption_allowed",
    "settlement_method",

    "asset_class",
    "investment_style",
    "fund_type",
    "fund_size_category",
    "portfolio_type",
    "maturity_period_years",
    "coupon_rate",
    "coupon_frequency",
    "credit_rating",
    "bond_type",
    "government_or_corporate",
    "nps_tier",
    "nps_asset_allocation",
    "demat_account_type",
    "trading_segment",
    "exchange",
    "equity_market_cap",
    "equity_style",
    "portfolio_advisory_type",
    "relationship_manager_available",
    "dedicated_advisor",
    "family_office_support",
    "succession_planning",
    "estate_planning",
    "global_investment_access",

    "identity_proof_required",
    "address_proof_required",
    "pan_document_required",
    "bank_statement_required",
    "income_proof_required",
    "risk_profile_document_required",
    "kyc_document_required",
    "other_documents",

    "digital_onboarding",
    "paperless_processing",
    "e_sign_available",
    "online_portfolio_tracking",
    "mobile_portfolio_tracking",
    "research_available",
    "advisory_available",
    "portfolio_analysis_available",
    "portfolio_optimizer_available",
    "market_insights_available",
    "alerts_available",
    "statements_available_online",

    "tag_mutual_fund",
    "tag_sip",
    "tag_bond",
    "tag_ncd",
    "tag_nps",
    "tag_demat",
    "tag_equity",
    "tag_stock",
    "tag_ipo",
    "tag_etf",
    "tag_gold_etf",
    "tag_wealth_management",
    "tag_private_banking",
    "tag_retirement",
    "tag_tax_saving",
    "tag_income",
    "tag_growth",
    "tag_low_risk",
    "tag_medium_risk",
    "tag_high_risk",
    "tag_liquid",
    "tag_long_term",
    "tag_short_term",
    "tag_premium",
    "tag_hni",
    "tag_nri",
    "tag_digital",
    "tag_beginner",
    "tag_experienced_investor",

    "launch_date",
    "end_date",
    "effective_from",
    "effective_to",
    "created_at",
    "updated_at"
]


# ============================================================
# VALIDATION
# ============================================================

def validate_no_blanks(rows, fields):

    for row_number, row in enumerate(rows, start=1):

        for field in fields:

            if field not in row:
                raise ValueError(
                    f"Missing field '{field}' in row {row_number}"
                )

            value = row[field]

            if value is None:
                raise ValueError(
                    f"None value in row {row_number}, "
                    f"field '{field}'"
                )

            if isinstance(value, str) and value.strip() == "":
                raise ValueError(
                    f"Blank value in row {row_number}, "
                    f"field '{field}'"
                )


# ============================================================
# VALIDATE
# ============================================================

validate_no_blanks(products, FIELDNAMES)


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
    writer.writerows(products)


# ============================================================
# SUMMARY
# ============================================================

print("=" * 80)
print("INVESTMENT & WEALTH PRODUCT DATA GENERATED")
print("=" * 80)

print(f"Products generated : {len(products)}")
print(f"Columns            : {len(FIELDNAMES)}")
print("Blank values       : 0")
print(f"Output file        : {OUTPUT_FILE}")

print("\nPRODUCT CATALOGUE")
print("-" * 80)

for product in products:

    print(
        f"{product['investment_product_id']:7s} | "
        f"{product['product_category']:20s} | "
        f"{product['product_name']}"
    )

print("=" * 80)