import csv
import json
import random
from pathlib import Path
from datetime import date, datetime, timedelta

# ============================================================
# CUSTOMER PROFILE + CUSTOMER 360 SYNTHETIC DATA GENERATOR
# ============================================================
#
# Purpose:
#   Generate a realistic synthetic "Customer 360" dataset for the
#   banking AI/NBO project.
#
# Important design:
#   1. customers.csv contains the core customer master profile.
#   2. Separate product ownership records are generated.
#   3. customer_360.json contains a fully assembled nested profile
#      that can be passed to behavior_engine.py / financial_analyst.py.
#   4. Product ownership is logically consistent with age, income,
#      occupation and customer type.
#   5. Not every customer owns every product.
#   6. Product details are copied from the catalogue where possible.
#
# The product catalogue CSVs expected by this script are optional.
# If present, the script will use them:
#
#   credit_card_products.csv
#   loan_products.csv
#   investment_products.csv
#   insurance_products.csv
#
# If a catalogue file is unavailable, built-in synthetic fallback
# products are used so the script still runs.
#
# ============================================================

random.seed(42)

# ============================================================
# CONFIGURATION
# ============================================================

NUM_CUSTOMERS = 300

BASE_DIR = Path(__file__).resolve().parent

OUTPUT_DIR = BASE_DIR / "generated_customer_360"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CUSTOMERS_FILE = OUTPUT_DIR / "customers.csv"

CUSTOMER_ACCOUNTS_FILE = OUTPUT_DIR / "customer_accounts.csv"
CUSTOMER_DEBIT_CARDS_FILE = OUTPUT_DIR / "customer_debit_cards.csv"
CUSTOMER_CREDIT_CARDS_FILE = OUTPUT_DIR / "customer_credit_cards.csv"
CUSTOMER_LOANS_FILE = OUTPUT_DIR / "customer_loans.csv"
CUSTOMER_DEPOSITS_FILE = OUTPUT_DIR / "customer_deposits.csv"
CUSTOMER_INVESTMENTS_FILE = OUTPUT_DIR / "customer_investments.csv"
CUSTOMER_INSURANCE_FILE = OUTPUT_DIR / "customer_insurance.csv"

CUSTOMER_360_FILE = OUTPUT_DIR / "customer_360.json"

# Search these locations for product catalogues.
CATALOGUE_SEARCH_DIRS = [
    BASE_DIR,
    BASE_DIR.parent,
    BASE_DIR.parent.parent,
    Path.cwd(),
]

TODAY = date.today()

# ============================================================
# COMMON MASTER DATA
# ============================================================

FIRST_NAMES_MALE = [
    "Aarav", "Aaryan", "Abhay", "Abhinav", "Abhishek", "Adarsh",
    "Aditya", "Advaith", "Agastya", "Ajay", "Akash", "Akshay",
    "Alok", "Aman", "Amar", "Amit", "Anand", "Aniket", "Anil",
    "Anirudh", "Ankit", "Anmol", "Ansh", "Anshul", "Arjun",
    "Armaan", "Arnav", "Arun", "Aryan", "Ashish", "Ashok",
    "Atharv", "Avinash", "Ayush", "Bharat", "Bhavesh", "Chaitanya",
    "Chetan", "Chirag", "Daksh", "Darshan", "Deepak", "Dev",
    "Devaansh", "Dhruv", "Dinesh", "Divyansh", "Eshan", "Gaurav",
    "Girish", "Harish", "Harsh", "Harshad", "Himanshu", "Hrithik",
    "Ishaan", "Jai", "Jay", "Jayesh", "Karan", "Kartik", "Kartikeya",
    "Keshav", "Krishna", "Kunal", "Lakshya", "Manav", "Manish",
    "Mayank", "Mihir", "Mohit", "Nakul", "Naman", "Naveen", "Neel",
    "Nikhil", "Nirav", "Nitin", "Om", "Parth", "Pranav", "Pratik",
    "Rahul", "Raj", "Rajat", "Rajesh", "Rajiv", "Rakesh", "Rohan",
    "Rohit", "Sachin", "Sagar", "Sahil", "Sameer", "Sanjay", "Sanket",
    "Sarthak", "Shashank", "Shivam", "Shrey", "Siddharth", "Soham",
    "Sourabh", "Srinivas", "Sumit", "Suraj", "Tanay", "Tanish", "Tarun",
    "Tejas", "Uday", "Utkarsh", "Vaibhav", "Varun", "Ved", "Veer",
    "Vicky", "Vijay", "Vikas", "Vikram", "Vinay", "Vishal", "Vivek",
    "Yash", "Yashwant", "Yuvraj",
]

FIRST_NAMES_FEMALE = [
    "Aadhya", "Aakanksha", "Aaliya", "Aaradhya", "Aastha", "Aditi",
    "Akanksha", "Alisha", "Amrita", "Ananya", "Anika", "Anjali",
    "Ankita", "Anushka", "Anvi", "Aparna", "Aradhana", "Avani",
    "Avantika", "Bhavana", "Bhumika", "Charita", "Charvi", "Deepa",
    "Deepika", "Deepti", "Diya", "Esha", "Garima", "Gauri", "Gayatri",
    "Geetanjali", "Harini", "Ira", "Isha", "Ishita", "Jahnavi", "Janhvi",
    "Jiya", "Kajal", "Kalpana", "Kanchan", "Kareena", "Kavita", "Kavya",
    "Khushi", "Kirti", "Komal", "Krisha", "Lakshmi", "Lavanya",
    "Madhuri", "Mahima", "Mahi", "Manisha", "Meera", "Megha", "Mihika",
    "Mitali", "Manya", "Muskan", "Naina", "Namrata", "Neha", "Nidhi",
    "Nikita", "Nisha", "Nishita", "Palak", "Pallavi", "Pooja", "Prachi",
    "Pragya", "Pranita", "Priya", "Radhika", "Ragini", "Rashi", "Rashmi",
    "Reema", "Rekha", "Rhea", "Riddhi", "Riya", "Roshni", "Sakshi",
    "Saloni", "Sana", "Sandhya", "Sanjana", "Sapna", "Sarika", "Shalini",
    "Shanaya", "Sharanya", "Shreya", "Shruti", "Simran", "Sneha",
    "Sonali", "Sonia", "Sonal", "Suhani", "Swati", "Tanisha", "Tanya",
    "Trisha", "Vaishnavi", "Vandana", "Varsha", "Vidhi", "Vineeta",
    "Yamini", "Zoya",
]

LAST_NAMES = [
    "Agarwal", "Ahire", "Bansal", "Bhat", "Bhatia", "Bhosale", "Bhatt",
    "Chakraborty", "Chaudhary", "Chavan", "Chopra", "Das", "Desai",
    "Deshmukh", "Dhawan", "Dixit", "Dubey", "Gandhi", "Garg", "Ghosh",
    "Goel", "Gokhale", "Goswami", "Gupta", "Iyer", "Jadhav", "Jain",
    "Joshi", "Kale", "Kapoor", "Karnik", "Kaur", "Kulkarni", "Kumar",
    "Mahajan", "Malhotra", "Mane", "Mehta", "Menon", "Mishra", "Modi",
    "More", "Naik", "Nair", "Narayan", "Nayak", "Patel", "Patil",
    "Pawar", "Pillai", "Pradhan", "Rao", "Rane", "Rathod", "Roy", "Saha",
    "Saini", "Salunke", "Sarkar", "Shah", "Sharma", "Shetty", "Shinde",
    "Singh", "Sinha", "Solanki", "Soman", "Sonawane", "Srivastava",
    "Subramanian", "Suresh", "Tiwari", "Trivedi", "Tripathi", "Upadhyay",
    "Vaidya", "Varma", "Verma", "Wagh", "Yadav",
]

CITIES = [
    ("Mumbai", "Maharashtra", "400001"),
    ("Pune", "Maharashtra", "411001"),
    ("Nagpur", "Maharashtra", "440001"),
    ("Nashik", "Maharashtra", "422001"),
    ("Aurangabad", "Maharashtra", "431001"),
    ("Thane", "Maharashtra", "400601"),
    ("Navi Mumbai", "Maharashtra", "400703"),
    ("Delhi", "Delhi", "110001"),
    ("New Delhi", "Delhi", "110011"),
    ("Bengaluru", "Karnataka", "560001"),
    ("Mysuru", "Karnataka", "570001"),
    ("Mangaluru", "Karnataka", "575001"),
    ("Hyderabad", "Telangana", "500001"),
    ("Warangal", "Telangana", "506002"),
    ("Chennai", "Tamil Nadu", "600001"),
    ("Coimbatore", "Tamil Nadu", "641001"),
    ("Madurai", "Tamil Nadu", "625001"),
    ("Ahmedabad", "Gujarat", "380001"),
    ("Surat", "Gujarat", "395001"),
    ("Vadodara", "Gujarat", "390001"),
    ("Rajkot", "Gujarat", "360001"),
    ("Kolkata", "West Bengal", "700001"),
    ("Jaipur", "Rajasthan", "302001"),
    ("Lucknow", "Uttar Pradesh", "226001"),
    ("Kanpur", "Uttar Pradesh", "208001"),
    ("Noida", "Uttar Pradesh", "201301"),
    ("Ghaziabad", "Uttar Pradesh", "201001"),
    ("Bhopal", "Madhya Pradesh", "462001"),
    ("Indore", "Madhya Pradesh", "452001"),
    ("Bhubaneswar", "Odisha", "751001"),
    ("Chandigarh", "Chandigarh", "160001"),
    ("Kochi", "Kerala", "682001"),
    ("Thiruvananthapuram", "Kerala", "695001"),
    ("Patna", "Bihar", "800001"),
    ("Ranchi", "Jharkhand", "834001"),
    ("Guwahati", "Assam", "781001"),
    ("Dehradun", "Uttarakhand", "248001"),
]

OCCUPATIONS = [
    ("Software Engineer", "Salaried"),
    ("Senior Software Engineer", "Salaried"),
    ("Data Analyst", "Salaried"),
    ("Data Scientist", "Salaried"),
    ("Product Manager", "Salaried"),
    ("Project Manager", "Salaried"),
    ("Business Analyst", "Salaried"),
    ("DevOps Engineer", "Salaried"),
    ("Cloud Engineer", "Salaried"),
    ("UI/UX Designer", "Salaried"),
    ("Marketing Manager", "Salaried"),
    ("HR Manager", "Salaried"),
    ("Finance Manager", "Salaried"),
    ("Accountant", "Salaried"),
    ("Chartered Accountant", "Self-employed"),
    ("Doctor", "Salaried"),
    ("Dentist", "Self-employed"),
    ("Pharmacist", "Salaried"),
    ("Teacher", "Salaried"),
    ("Professor", "Salaried"),
    ("Lawyer", "Self-employed"),
    ("Architect", "Self-employed"),
    ("Civil Engineer", "Salaried"),
    ("Mechanical Engineer", "Salaried"),
    ("Electrical Engineer", "Salaried"),
    ("Consultant", "Self-employed"),
    ("Business Owner", "Business"),
    ("Retail Business Owner", "Business"),
    ("Restaurant Owner", "Business"),
    ("Trader", "Self-employed"),
    ("Freelancer", "Self-employed"),
    ("Content Creator", "Self-employed"),
    ("Entrepreneur", "Business"),
    ("Government Employee", "Salaried"),
    ("Defence Personnel", "Salaried"),
    ("Bank Employee", "Salaried"),
    ("Insurance Officer", "Salaried"),
    ("Student", "Student"),
    ("Researcher", "Salaried"),
    ("Retired Professional", "Retired"),
]

EMPLOYERS = [
    "TCS", "Infosys", "Wipro", "HCLTech", "Accenture", "IBM India",
    "Cognizant", "Capgemini", "Tech Mahindra", "Deloitte", "EY India",
    "KPMG India", "PwC India", "Amazon India", "Microsoft India",
    "Google India", "Flipkart", "Reliance Industries", "Tata Motors",
    "Mahindra & Mahindra", "Bajaj Finserv", "ICICI Bank", "Axis Bank",
    "HDFC Bank", "Larsen & Toubro", "Aditya Birla Group", "State Government",
    "Central Government", "Self Employed", "Independent Consultant",
    "Family Business", "Startup", "Private Company",
]

EDUCATION_LEVELS = [
    "Higher Secondary",
    "Diploma",
    "Graduate",
    "Postgraduate",
    "Doctorate",
]

LANGUAGES = [
    "English", "Hindi", "Marathi", "Gujarati", "Tamil",
    "Telugu", "Kannada", "Bengali", "Malayalam", "Punjabi", "Odia"
]

BANK_ACCOUNT_TYPES = [
    "Savings",
    "Salary",
    "Current",
]

DEBIT_CARD_PRODUCTS = [
    ("DB001", "Millennia Debit Card", "Visa", "Premium"),
    ("DB002", "Platinum Debit Card", "Visa", "Premium"),
    ("DB003", "Classic Debit Card", "Visa", "Classic"),
    ("DB004", "RuPay Debit Card", "RuPay", "Classic"),
    ("DB005", "MoneyBack Debit Card", "Visa", "Classic"),
    ("DB006", "Women's Advantage Debit Card", "Visa", "Premium"),
    ("DB007", "Business Debit Card", "Visa", "Business"),
]

DEPOSIT_PRODUCTS_FALLBACK = [
    ("DEP001", "Regular Fixed Deposit", "Fixed Deposit", 6.5),
    ("DEP002", "Senior Citizen Fixed Deposit", "Fixed Deposit", 7.0),
    ("DEP003", "Recurring Deposit", "Recurring Deposit", 6.5),
    ("DEP004", "Tax Saving Fixed Deposit", "Tax Saving FD", 6.5),
]

INVESTMENT_PRODUCTS_FALLBACK = [
    ("INV001", "HDFC Equity Mutual Fund", "Mutual Fund", "HDFC Mutual Fund"),
    ("INV002", "HDFC Balanced Advantage Fund", "Mutual Fund", "HDFC Mutual Fund"),
    ("INV003", "HDFC Liquid Fund", "Mutual Fund", "HDFC Mutual Fund"),
    ("INV004", "HDFC Equity SIP", "SIP", "HDFC Mutual Fund"),
    ("INV005", "HDFC Corporate Bond", "Bond", "HDFC Securities"),
    ("INV006", "NPS Tier I", "NPS", "HDFC Pension"),
    ("INV007", "HDFC 3-in-1 Investment Account", "Demat", "HDFC Securities"),
    ("INV008", "Equity Trading", "Stock / Equity", "HDFC Securities"),
    ("INV009", "IPO Investment", "IPO", "HDFC Securities"),
    ("INV010", "ETF", "ETF", "HDFC Securities"),
    ("INV011", "Gold ETF", "Gold ETF", "HDFC Securities"),
    ("INV012", "Wealth Management", "Wealth Management", "HDFC Bank"),
    ("INV013", "Private Banking", "Private Banking", "HDFC Bank"),
]

INSURANCE_PRODUCTS_FALLBACK = [
    ("INS001", "HDFC Life Term Insurance", "Life", "HDFC Life"),
    ("INS002", "HDFC Life Savings Plan", "Life", "HDFC Life"),
    ("INS003", "HDFC ERGO Health Insurance", "Health", "HDFC ERGO"),
    ("INS004", "HDFC ERGO Family Health", "Health", "HDFC ERGO"),
    ("INS005", "HDFC ERGO Travel Insurance", "Travel", "HDFC ERGO"),
    ("INS006", "HDFC ERGO Motor Insurance", "Motor", "HDFC ERGO"),
    ("INS007", "HDFC ERGO Personal Accident", "Personal Accident", "HDFC ERGO"),
    ("INS008", "HDFC ERGO Home Insurance", "Home", "HDFC ERGO"),
]

LOAN_PRODUCTS_FALLBACK = [
    ("LN001", "Personal Loan", "Personal", "Unsecured"),
    ("LN002", "Home Loan", "Home", "Secured"),
    ("LN003", "New Car Loan", "Auto", "Secured"),
    ("LN004", "Used Car Loan", "Auto", "Secured"),
    ("LN005", "Two-Wheeler Loan", "Two-Wheeler", "Secured"),
    ("LN006", "Education Loan", "Education", "Secured / Unsecured"),
    ("LN007", "Gold Loan", "Gold", "Secured"),
    ("LN008", "Business Loan", "Business", "Unsecured"),
    ("LN009", "Working Capital Finance", "Business", "Secured"),
    ("LN010", "Loan Against Property", "Property", "Secured"),
    ("LN011", "Loan Against Securities", "Investment", "Secured"),
    ("LN012", "Loan Against Mutual Funds", "Investment", "Secured"),
    ("LN013", "Commercial Vehicle Finance", "Commercial", "Secured"),
    ("LN014", "Construction Equipment Finance", "Commercial", "Secured"),
]

CREDIT_CARD_PRODUCTS_FALLBACK = [
    ("CC001", "Freedom Credit Card", "Classic", "Visa"),
    ("CC002", "MoneyBack+ Credit Card", "Classic", "Visa"),
    ("CC003", "Millennia Credit Card", "Premium", "Visa"),
    ("CC004", "Regalia Gold", "Super Premium", "Visa"),
    ("CC005", "Infinia", "Super Premium", "Mastercard"),
    ("CC006", "Diners Black", "Super Premium", "Diners Club"),
    ("CC007", "Tata Neu Infinity", "Premium", "RuPay"),
    ("CC008", "Swiggy HDFC Bank Credit Card", "Premium", "Mastercard"),
    ("CC009", "IndianOil HDFC Bank Credit Card", "Premium", "Visa"),
]

# ============================================================
# FILE HELPERS
# ============================================================

def find_file(filename: str) -> Path | None:
    for directory in CATALOGUE_SEARCH_DIRS:
        candidate = directory / filename
        if candidate.exists():
            return candidate
    return None


def load_csv_records(filename: str) -> list[dict]:
    path = find_file(filename)

    if not path:
        return []

    try:
        with path.open("r", newline="", encoding="utf-8") as file:
            return list(csv.DictReader(file))
    except (OSError, csv.Error) as exc:
        print(f"[WARNING] Could not load {filename}: {exc}")
        return []


def first_value(row: dict, names: list[str], default="Not Applicable"):
    for name in names:
        if name in row and str(row[name]).strip() not in {"", "None", "NULL"}:
            return row[name]
    return default


def to_float(value, default=0.0):
    try:
        if value is None:
            return default
        cleaned = str(value).replace(",", "").replace("₹", "").strip()
        return float(cleaned)
    except (ValueError, TypeError):
        return default


def random_date(start_date: date, end_date: date) -> date:
    if end_date <= start_date:
        return start_date
    return start_date + timedelta(
        days=random.randint(0, (end_date - start_date).days)
    )


def weighted_bool(probability: float) -> bool:
    return random.random() < probability


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def choose_weighted(items: list[tuple[object, float]]):
    values = [item[0] for item in items]
    weights = [item[1] for item in items]
    return random.choices(values, weights=weights, k=1)[0]


def safe_date_string(value):
    if isinstance(value, date):
        return value.isoformat()
    return value


def generate_phone(index: int):
    # Synthetic and deliberately non-real.
    return f"9{index:09d}"[-10:]


def generate_email(first_name: str, last_name: str, index: int):
    return f"{first_name.lower()}.{last_name.lower()}{index}@example.com"


# ============================================================
# PRODUCT CATALOGUE LOADING
# ============================================================

def load_catalogues():
    credit_cards = load_csv_records("credit_card_products.csv")
    loans = load_csv_records("loan_products.csv")
    investments = load_csv_records("investment_products.csv")
    insurance = load_csv_records("insurance_products.csv")

    return {
        "credit_cards": credit_cards,
        "loans": loans,
        "investments": investments,
        "insurance": insurance,
    }


# ============================================================
# FALLBACK NORMALIZATION
# ============================================================

def get_credit_cards(catalogues):
    if catalogues["credit_cards"]:
        return catalogues["credit_cards"]

    rows = []
    for product_id, name, category, network in CREDIT_CARD_PRODUCTS_FALLBACK:
        rows.append({
            "credit_card_product_id": product_id,
            "product_code": product_id,
            "card_name": name,
            "card_category": category,
            "card_network": network,
            "reward_program_name": "Reward Points",
            "reward_type": "Reward Points",
            "foreign_currency_markup": "3.5",
            "annual_fee": "2500",
            "renewal_fee": "2500",
            "airport_lounge_access": "Yes" if category != "Classic" else "No",
            "tag_travel": "1" if "Travel" in name or "Regalia" in name or "Infinia" in name or "Diners" in name else "0",
            "tag_shopping": "1" if "Millennia" in name or "MoneyBack" in name or "Swiggy" in name or "Tata Neu" in name else "0",
            "tag_fuel": "1" if "IndianOil" in name else "0",
            "tag_dining": "1" if "Swiggy" in name or "Diners" in name else "0",
            "tag_premium": "1" if "Premium" in category or "Regalia" in name or "Infinia" in name or "Diners" in name else "0",
        })
    return rows


def get_loans(catalogues):
    if catalogues["loans"]:
        return catalogues["loans"]

    rows = []
    for product_id, name, category, security in LOAN_PRODUCTS_FALLBACK:
        rows.append({
            "loan_product_id": product_id,
            "product_code": product_id,
            "product_name": name,
            "loan_category": category,
            "loan_subcategory": category,
            "loan_type": name,
            "secured_or_unsecured": security,
            "interest_rate_current": "10.5",
            "minimum_loan_amount": "50000",
            "maximum_loan_amount": "5000000",
            "minimum_tenure_months": "12",
            "maximum_tenure_months": "84",
        })
    return rows


def get_investments(catalogues):
    if catalogues["investments"]:
        return catalogues["investments"]

    rows = []
    for product_id, name, category, provider in INVESTMENT_PRODUCTS_FALLBACK:
        rows.append({
            "investment_product_id": product_id,
            "product_code": product_id,
            "product_name": name,
            "product_category": category,
            "product_subcategory": category,
            "product_type": category,
            "provider": provider,
            "issuer": provider,
            "risk_level": (
                "High" if category in {"Stock / Equity", "IPO"}
                else "Low" if category == "Mutual Fund" and "Liquid" in name
                else "Moderate"
            ),
            "minimum_investment": "500",
            "minimum_monthly_investment": "500",
        })
    return rows


def get_insurance(catalogues):
    if catalogues["insurance"]:
        return catalogues["insurance"]

    rows = []
    for product_id, name, category, insurer in INSURANCE_PRODUCTS_FALLBACK:
        rows.append({
            "insurance_product_id": product_id,
            "product_code": product_id,
            "product_name": name,
            "product_category": category,
            "product_subcategory": category,
            "insurance_type": category,
            "insurer_name": insurer,
            "sum_assured_min": "500000",
            "sum_assured_max": "10000000",
            "premium_amount": "15000",
            "premium_frequency": "Annual",
            "minimum_entry_age": "18",
            "maximum_entry_age": "65",
        })
    return rows


# ============================================================
# CUSTOMER PROFILE GENERATION
# ============================================================

def choose_customer_type(age: int, income: int, employment_type: str):
    if employment_type == "Business":
        return choose_weighted([
            ("Business", 70),
            ("Premium", 25 if income >= 2000000 else 5),
            ("Retail", 5),
        ])

    if income >= 2500000:
        return choose_weighted([
            ("Premium", 75),
            ("Retail", 20),
            ("Business", 5),
        ])

    if income >= 1200000:
        return choose_weighted([
            ("Premium", 35),
            ("Retail", 65),
        ])

    return choose_weighted([
        ("Retail", 92),
        ("Premium", 8),
    ])


def generate_income(occupation_type: str, age: int) -> int:
    if occupation_type == "Student":
        return random.randint(0, 250_000)

    if occupation_type == "Retired":
        return random.randint(300_000, 1_500_000)

    if occupation_type == "Business":
        return random.randint(800_000, 12_000_000)

    if occupation_type == "Self-employed":
        return random.randint(500_000, 6_000_000)

    if age < 25:
        return random.randint(300_000, 750_000)

    if age < 35:
        return random.randint(500_000, 2_000_000)

    if age < 50:
        return random.randint(800_000, 4_000_000)

    return random.randint(900_000, 6_000_000)


def income_range(income: int):
    if income < 300_000:
        return "0-3L"
    if income < 500_000:
        return "3-5L"
    if income < 1_000_000:
        return "5-10L"
    if income < 2_000_000:
        return "10-20L"
    if income < 5_000_000:
        return "20-50L"
    return "50L+"


def generate_base_customer(i: int):
    gender = random.choice(["Male", "Female"])

    first_name = (
        random.choice(FIRST_NAMES_MALE)
        if gender == "Male"
        else random.choice(FIRST_NAMES_FEMALE)
    )

    last_name = random.choice(LAST_NAMES)

    age = random.randint(18, 70)
    occupation, employment_type = random.choice(OCCUPATIONS)

    annual_income = generate_income(employment_type, age)

    # NRI is intentionally very rare.
    residential_status = choose_weighted([
        ("Resident", 99),
        ("NRI", 1),
    ])

    if residential_status == "NRI":
        annual_income = random.randint(1_500_000, 8_000_000)

    city, state, pincode = random.choice(CITIES)

    if age < 25:
        marital_status = choose_weighted([
            ("Single", 90),
            ("Married", 10),
        ])
    elif age < 35:
        marital_status = choose_weighted([
            ("Single", 40),
            ("Married", 60),
        ])
    else:
        marital_status = choose_weighted([
            ("Married", 82),
            ("Divorced", 8),
            ("Widowed", 10),
        ])

    if employment_type == "Student":
        employer = "College / University"
    elif employment_type == "Retired":
        employer = "Retired"
    elif employment_type == "Business":
        employer = random.choice([
            "Family Business",
            "Independent Business",
            "Retail Business",
            "Restaurant Business",
            "Startup",
            "Self Employed",
        ])
    else:
        employer = random.choice(EMPLOYERS)

    customer_type = choose_customer_type(
        age=age,
        income=annual_income,
        employment_type=employment_type,
    )

    customer_since = random_date(
        date(2017, 1, 1),
        date(2025, 12, 31),
    )

    credit_score = (
        random.randint(680, 820)
        if annual_income >= 500_000
        else random.randint(650, 760)
    )

    # High-income, stable customers are more likely to have better credit scores.
    if annual_income >= 2_000_000:
        credit_score = random.randint(730, 850)

    # Student with limited credit history is lower.
    if employment_type == "Student":
        credit_score = random.randint(650, 730)

    if customer_type == "Premium":
        risk_profile = choose_weighted([
            ("Low", 30),
            ("Moderate", 55),
            ("High", 15),
        ])
    else:
        risk_profile = choose_weighted([
            ("Low", 25),
            ("Moderate", 60),
            ("High", 15),
        ])

    if employment_type == "Student":
        preferred_channel = choose_weighted([
            ("Mobile App", 65),
            ("NetBanking", 15),
            ("Email", 10),
            ("SMS", 5),
            ("Branch", 5),
        ])
    else:
        preferred_channel = choose_weighted([
            ("Mobile App", 45),
            ("NetBanking", 20),
            ("Email", 15),
            ("SMS", 10),
            ("Branch", 10),
        ])

    customer = {
        "customer_id": f"CUST{i:05d}",
        "customer_number": f"CIF{i:08d}",
        "first_name": first_name,
        "middle_name": "",
        "last_name": last_name,
        "date_of_birth": date(
            TODAY.year - age,
            random.randint(1, 12),
            random.randint(1, 28),
        ).isoformat(),
        "age": age,
        "gender": gender,
        "marital_status": marital_status,
        "nationality": "Indian",
        "residential_status": residential_status,
        "occupation_type": employment_type,
        "occupation": occupation,
        "employer_name": employer,
        "employment_type": employment_type,
        "annual_income": annual_income,
        "income_range": income_range(annual_income),
        "education_level": random.choice(EDUCATION_LEVELS),
        "address_line_1": (
            f"{random.randint(1, 999)} "
            f"{random.choice(['MG Road', 'Station Road', 'Main Street', 'Park Road', 'Market Road'])}"
        ),
        "address_line_2": f"Apartment {random.randint(1, 500)}",
        "city": city,
        "state": state,
        "country": "India",
        "pincode": pincode,
        "mobile_number": generate_phone(i),
        "email": generate_email(first_name, last_name, i),
        "customer_since": customer_since.isoformat(),
        "customer_segment_type": customer_type,
        "customer_status": choose_weighted([
            ("Active", 95),
            ("Dormant", 5),
        ]),
        "kyc_status": choose_weighted([
            ("Verified", 97),
            ("Pending", 3),
        ]),
        "kyc_last_updated": random_date(
            date(2024, 1, 1),
            TODAY,
        ).isoformat(),
        "risk_profile": risk_profile,
        "credit_score": credit_score,
        "relationship_manager_id": (
            f"RM{random.randint(1, 50):03d}"
        ),
        "preferred_language": random.choice(LANGUAGES),
        "preferred_channel": preferred_channel,
        "marketing_consent": choose_weighted([
            ("Yes", 92),
            ("No", 8),
        ]),
    }

    return customer


# ============================================================
# PRODUCT OWNERSHIP LOGIC
# ============================================================

def should_have_account(customer):
    # Almost all bank customers have at least one account.
    return True


def generate_accounts(customer, index):
    rows = []

    customer_id = customer["customer_id"]
    customer_type = customer["customer_segment_type"]
    employment_type = customer["employment_type"]

    # Primary account
    if employment_type == "Business" or customer_type == "Business":
        account_type = choose_weighted([
            ("Current", 75),
            ("Savings", 25),
        ])
    elif employment_type == "Salaried":
        account_type = choose_weighted([
            ("Salary", 65),
            ("Savings", 35),
        ])
    else:
        account_type = "Savings"

    account_product_map = {
        "Savings": [
            "Regular Savings Account",
            "Savings Max",
            "Millennia Savings Account",
            "Digital Savings Account",
        ],
        "Salary": [
            "Salary Account",
            "Premium Salary Account",
        ],
        "Current": [
            "Regular Current Account",
            "Business Current Account",
        ],
    }

    account_product = random.choice(account_product_map[account_type])

    opening_date = random_date(
        date.fromisoformat(customer["customer_since"]),
        TODAY,
    )

    account_id = f"ACC{index:05d}"

    rows.append({
        "account_id": account_id,
        "customer_id": customer_id,
        "account_type": account_type,
        "account_product_name": account_product,
        "account_number_masked": f"XXXXXX{random.randint(1000,9999)}",
        "account_status": "Active",
        "opening_date": opening_date.isoformat(),
        "currency": "INR",
        "average_monthly_balance": round(
            max(
                5_000,
                customer["annual_income"] / 12
                * random.uniform(0.3, 2.5)
            ),
            2,
        ),
    })

    # A small percentage of customers get an additional account.
    if (
        customer["customer_segment_type"] == "Premium"
        and weighted_bool(0.25)
    ):
        second_id = f"ACC{index:05d}B"

        rows.append({
            "account_id": second_id,
            "customer_id": customer_id,
            "account_type": "Savings",
            "account_product_name": random.choice(
                account_product_map["Savings"]
            ),
            "account_number_masked": (
                f"XXXXXX{random.randint(1000,9999)}"
            ),
            "account_status": "Active",
            "opening_date": random_date(
                opening_date,
                TODAY,
            ).isoformat(),
            "currency": "INR",
            "average_monthly_balance": round(
                max(
                    10_000,
                    customer["annual_income"] / 12
                    * random.uniform(0.5, 4.0)
                ),
                2,
            ),
        })

    return rows


def choose_credit_card(customer):
    income = customer["annual_income"]
    age = customer["age"]
    customer_type = customer["customer_segment_type"]
    occupation = customer["occupation"]

    if income < 450_000:
        return "basic"

    if income >= 2_500_000 or customer_type == "Premium":
        return choose_weighted([
            ("premium", 65),
            ("classic", 20),
            ("co_brand", 15),
        ])

    if income >= 1_000_000:
        return choose_weighted([
            ("premium", 40),
            ("classic", 25),
            ("co_brand", 35),
        ])

    if age < 35:
        return choose_weighted([
            ("classic", 40),
            ("co_brand", 35),
            ("premium", 25),
        ])

    return choose_weighted([
        ("classic", 55),
        ("co_brand", 20),
        ("premium", 25),
    ])


def product_matches_card_segment(row, segment):
    category = str(
        first_value(
            row,
            ["card_category", "card_variant"],
            "Classic",
        )
    ).lower()

    name = str(
        first_value(
            row,
            ["card_name", "product_name"],
            "",
        )
    ).lower()

    if segment == "premium":
        return (
            "premium" in category
            or "regalia" in name
            or "infinia" in name
            or "diners black" in name
            or "bizblack" in name
        )

    if segment == "co_brand":
        return (
            "co-brand" in category
            or "swiggy" in name
            or "tata neu" in name
            or "irctc" in name
            or "indianoil" in name
            or "marriott" in name
            or "phonepe" in name
            or "paytm" in name
        )

    if segment == "basic":
        return (
            "classic" in category
            or "freedom" in name
            or "moneyback" in name
            or "pixel go" in name
        )

    return True


def generate_credit_cards(customer, cards, index):
    rows = []

    income = customer["annual_income"]
    customer_type = customer["customer_segment_type"]
    age = customer["age"]

    # Probability of owning a credit card.
    if income < 300_000:
        ownership_probability = 0.20
    elif income < 600_000:
        ownership_probability = 0.40
    elif income < 1_200_000:
        ownership_probability = 0.65
    elif income < 2_500_000:
        ownership_probability = 0.80
    else:
        ownership_probability = 0.90

    if customer_type == "Premium":
        ownership_probability += 0.05

    if age < 21:
        ownership_probability = 0

    if not weighted_bool(clamp(ownership_probability, 0, 0.95)):
        return rows

    desired_segment = choose_credit_card(customer)

    candidates = [
        card for card in cards
        if product_matches_card_segment(card, desired_segment)
    ]

    if not candidates:
        candidates = cards

    # Avoid duplicate card products for one customer.
    selected = random.choice(candidates)

    product_id = first_value(
        selected,
        ["credit_card_product_id", "product_code"],
        "CC001",
    )

    card_name = first_value(
        selected,
        ["card_name", "product_name"],
        "Credit Card",
    )

    card_network = first_value(
        selected,
        ["card_network"],
        "Visa",
    )

    card_category = first_value(
        selected,
        ["card_category", "card_variant"],
        "Classic",
    )

    base_limit = {
        "Classic": (25_000, 100_000),
        "Premium": (75_000, 500_000),
        "Super Premium": (300_000, 2_000_000),
    }

    limit_min, limit_max = base_limit.get(
        card_category,
        (25_000, 250_000),
    )

    if income >= 2_500_000:
        limit_min *= 2
        limit_max *= 2

    credit_limit = random.randint(
        int(limit_min),
        int(max(limit_min, limit_max)),
    )

    utilization = random.uniform(0.10, 0.65)

    if random.random() < 0.08:
        utilization = random.uniform(0.70, 0.90)

    outstanding = round(
        credit_limit * utilization,
        2,
    )

    available_limit = round(
        max(0, credit_limit - outstanding),
        2,
    )

    issue_date = random_date(
        date.fromisoformat(customer["customer_since"]),
        TODAY - timedelta(days=30),
    )

    rows.append({
        "customer_card_id": f"CCA{index:05d}",
        "customer_id": customer["customer_id"],
        "credit_card_product_id": product_id,
        "card_name": card_name,
        "card_number_masked": (
            f"XXXX-XXXX-XXXX-{random.randint(1000,9999)}"
        ),
        "card_network": card_network,
        "card_category": card_category,
        "issue_date": issue_date.isoformat(),
        "activation_date": (
            issue_date + timedelta(days=random.randint(0, 7))
        ).isoformat(),
        "expiry_date": (
            issue_date.replace(
                year=min(issue_date.year + 5, 2099)
            )
        ).isoformat(),
        "card_status": "Active",
        "credit_limit": credit_limit,
        "available_limit": available_limit,
        "current_outstanding": outstanding,
        "reward_points_balance": random.randint(0, 50_000),
        "annual_spend": round(
            credit_limit * random.uniform(1.0, 8.0),
            2,
        ),
        "international_enabled": (
            "Yes"
            if (
                card_category in {"Premium", "Super Premium"}
                or weighted_bool(0.35)
            )
            else "No"
        ),
        "last_payment_date": (
            TODAY - timedelta(days=random.randint(1, 40))
        ).isoformat(),
    })

    # A small number of high-income customers have two cards.
    if (
        income >= 2_000_000
        and weighted_bool(0.20)
        and len(cards) >= 2
    ):
        second_candidates = [
            card for card in candidates
            if first_value(
                card,
                ["credit_card_product_id", "product_code"],
                "",
            ) != product_id
        ]

        if second_candidates:
            selected2 = random.choice(second_candidates)

            product_id2 = first_value(
                selected2,
                ["credit_card_product_id", "product_code"],
                "CC002",
            )

            card_name2 = first_value(
                selected2,
                ["card_name", "product_name"],
                "Second Credit Card",
            )

            rows.append({
                "customer_card_id": f"CCA{index:05d}B",
                "customer_id": customer["customer_id"],
                "credit_card_product_id": product_id2,
                "card_name": card_name2,
                "card_number_masked": (
                    f"XXXX-XXXX-XXXX-{random.randint(1000,9999)}"
                ),
                "card_network": first_value(
                    selected2,
                    ["card_network"],
                    "Visa",
                ),
                "card_category": first_value(
                    selected2,
                    ["card_category", "card_variant"],
                    "Premium",
                ),
                "issue_date": (
                    TODAY
                    - timedelta(days=random.randint(60, 1000))
                ).isoformat(),
                "activation_date": (
                    TODAY
                    - timedelta(days=random.randint(50, 990))
                ).isoformat(),
                "expiry_date": (
                    TODAY + timedelta(days=random.randint(500, 1800))
                ).isoformat(),
                "card_status": "Active",
                "credit_limit": random.randint(100_000, 1_500_000),
                "available_limit": random.randint(50_000, 800_000),
                "current_outstanding": random.randint(0, 300_000),
                "reward_points_balance": random.randint(0, 75_000),
                "annual_spend": random.randint(
                    200_000,
                    3_000_000,
                ),
                "international_enabled": "Yes",
                "last_payment_date": (
                    TODAY - timedelta(days=random.randint(1, 40))
                ).isoformat(),
            })

    return rows


def loan_probability(customer):
    income = customer["annual_income"]
    age = customer["age"]
    employment = customer["employment_type"]

    probability = 0.08

    if income >= 600_000:
        probability += 0.20

    if income >= 1_200_000:
        probability += 0.15

    if employment in {"Salaried", "Business", "Self-employed"}:
        probability += 0.15

    if 25 <= age <= 50:
        probability += 0.15

    if employment == "Student":
        probability *= 0.25

    if employment == "Retired":
        probability *= 0.65

    return clamp(probability, 0, 0.80)


def select_loan_product(customer, loans):
    age = customer["age"]
    occupation = customer["occupation"]
    employment = customer["employment_type"]
    income = customer["annual_income"]

    candidates = []

    for row in loans:
        category = str(
            first_value(
                row,
                ["loan_category", "loan_subcategory"],
                "",
            )
        ).lower()

        name = str(
            first_value(
                row,
                ["loan_product_name", "product_name"],
                "",
            )
        ).lower()

        weight = 1

        if "student" in occupation.lower():
            weight += 6 if "education" in category or "education" in name else 0

        if "business" in employment.lower() or employment == "Business":
            weight += 5 if "business" in category or "working" in name else 0
            weight += 4 if "commercial" in category else 0

        if 25 <= age <= 50:
            weight += 2 if "home" in category or "property" in category else 0
            weight += 2 if "personal" in category else 0
            weight += 2 if "auto" in category or "two-wheeler" in category else 0

        if income >= 2_000_000:
            weight += 2 if "property" in category else 0
            weight += 2 if "investment" in category else 0

        candidates.append((row, weight))

    return choose_weighted(candidates)


def generate_loans(customer, loans, index):
    rows = []

    if not weighted_bool(loan_probability(customer)):
        return rows

    selected = select_loan_product(customer, loans)

    loan_id = first_value(
        selected,
        ["loan_product_id", "product_code"],
        "LN001",
    )

    product_name = first_value(
        selected,
        ["product_name"],
        "Personal Loan",
    )

    category = first_value(
        selected,
        ["loan_category", "loan_subcategory"],
        "Personal",
    )

    category_lower = category.lower()

    # Sanctioned amount should depend on product and income.
    income = customer["annual_income"]

    if "home" in category_lower:
        sanctioned = random.randint(
            2_000_000,
            max(3_000_000, min(15_000_000, income * 8)),
        )

    elif "auto" in category_lower:
        sanctioned = random.randint(
            300_000,
            max(500_000, min(3_000_000, income * 2)),
        )

    elif "two-wheeler" in category_lower:
        sanctioned = random.randint(
            50_000,
            max(100_000, min(500_000, income)),
        )

    elif "education" in category_lower:
        sanctioned = random.randint(
            200_000,
            max(500_000, min(5_000_000, income * 3)),
        )

    elif "gold" in category_lower:
        sanctioned = random.randint(50_000, 1_500_000)

    elif "business" in category_lower or "working" in category_lower:
        sanctioned = random.randint(
            500_000,
            max(1_000_000, min(10_000_000, income * 5)),
        )

    elif "property" in category_lower:
        sanctioned = random.randint(
            1_000_000,
            max(2_000_000, min(10_000_000, income * 5)),
        )

    else:
        sanctioned = random.randint(
            100_000,
            max(250_000, min(2_500_000, income * 2)),
        )

    sanctioned = int(round(sanctioned / 10_000) * 10_000)

    disbursed = round(
        sanctioned * random.uniform(0.85, 1.0),
        2,
    )

    outstanding = round(
        disbursed * random.uniform(0.30, 0.85),
        2,
    )

    interest_rate = to_float(
        first_value(
            selected,
            ["interest_rate_current", "interest_rate"],
            10.5,
        ),
        10.5,
    )

    issue_date = random_date(
        max(
            date.fromisoformat(customer["customer_since"]),
            date(2019, 1, 1),
        ),
        TODAY - timedelta(days=30),
    )

    remaining_tenure = random.randint(6, 120)

    if "home" in category_lower:
        remaining_tenure = random.randint(36, 240)

    emi = max(
        1_000,
        round(
            outstanding
            * (
                interest_rate / 12 / 100
            )
            * (
                (1 + interest_rate / 12 / 100)
                ** remaining_tenure
            )
            / (
                (1 + interest_rate / 12 / 100)
                ** remaining_tenure - 1
            ),
            2,
        ),
    )

    rows.append({
        "customer_loan_id": f"CL{index:05d}",
        "customer_id": customer["customer_id"],
        "loan_product_id": loan_id,
        "loan_product_name": product_name,
        "loan_category": category,
        "loan_account_number_masked": (
            f"XXXXXX{random.randint(1000,9999)}"
        ),
        "loan_status": "Active",
        "sanctioned_amount": sanctioned,
        "disbursed_amount": disbursed,
        "outstanding_principal": outstanding,
        "interest_rate": interest_rate,
        "tenure_months": remaining_tenure + random.randint(12, 120),
        "remaining_tenure_months": remaining_tenure,
        "emi_amount": emi,
        "start_date": issue_date.isoformat(),
        "next_emi_date": (
            TODAY + timedelta(days=random.randint(1, 30))
        ).isoformat(),
        "repayment_status": choose_weighted([
            ("Regular", 95),
            ("Delayed", 5),
        ]),
    })

    return rows


def generate_deposits(customer, deposits, index):
    rows = []

    income = customer["annual_income"]
    customer_type = customer["customer_segment_type"]
    age = customer["age"]

    probability = 0.25

    if income >= 800_000:
        probability += 0.20
    if income >= 1_500_000:
        probability += 0.20
    if customer_type == "Premium":
        probability += 0.15
    if age >= 45:
        probability += 0.10

    if not weighted_bool(clamp(probability, 0, 0.90)):
        return rows

    # Prefer FD for meaningful surplus.
    selected = random.choice(deposits)

    product_id, product_name, product_type, rate = (
        selected
        if len(selected) == 4
        else (
            selected.get("deposit_product_id", "DEP001"),
            selected.get("product_name", "Fixed Deposit"),
            selected.get("deposit_type", "Fixed Deposit"),
            to_float(selected.get("interest_rate", 6.5), 6.5),
        )
    )

    if isinstance(selected, dict):
        product_id = first_value(
            selected,
            ["deposit_product_id", "product_code"],
            "DEP001",
        )
        product_name = first_value(
            selected,
            ["product_name", "deposit_name"],
            "Fixed Deposit",
        )
        product_type = first_value(
            selected,
            ["deposit_type", "product_type"],
            "Fixed Deposit",
        )
        rate = to_float(
            first_value(
                selected,
                ["interest_rate", "interest_rate_current"],
                "6.5",
            ),
            6.5,
        )

    amount = random.choice([
        50_000,
        100_000,
        150_000,
        250_000,
        300_000,
        500_000,
        750_000,
        1_000_000,
    ])

    if income < 600_000:
        amount = min(amount, 100_000)

    tenure_months = random.choice([
        6, 12, 18, 24, 36, 60
    ])

    opening_date = random_date(
        max(
            date.fromisoformat(customer["customer_since"]),
            date(2020, 1, 1),
        ),
        TODAY - timedelta(days=30),
    )

    maturity_date = opening_date + timedelta(
        days=int(tenure_months * 30.44)
    )

    maturity_amount = round(
        amount * (1 + rate / 100 * tenure_months / 12),
        2,
    )

    rows.append({
        "customer_deposit_id": f"DEP{index:05d}",
        "customer_id": customer["customer_id"],
        "deposit_product_id": product_id,
        "deposit_product_name": product_name,
        "deposit_type": product_type,
        "deposit_account_number_masked": (
            f"XXXXXX{random.randint(1000,9999)}"
        ),
        "principal_amount": amount,
        "interest_rate": rate,
        "tenure_months": tenure_months,
        "opening_date": opening_date.isoformat(),
        "maturity_date": maturity_date.isoformat(),
        "maturity_amount": maturity_amount,
        "deposit_status": (
            "Active"
            if maturity_date >= TODAY
            else "Matured"
        ),
        "auto_renewal": random.choice(["Yes", "No"]),
    })

    return rows


def investment_match_score(customer, row):
    age = customer["age"]
    income = customer["annual_income"]
    category = str(
        first_value(
            row,
            ["product_category", "product_subcategory", "product_type"],
            "",
        )
    ).lower()

    name = str(
        first_value(
            row,
            ["product_name"],
            "",
        )
    ).lower()

    score = 1

    if "sip" in category or "sip" in name:
        score += 5 if income >= 500_000 else 0

    if "mutual fund" in category:
        score += 4 if income >= 500_000 else 1

    if "nps" in category:
        score += 4 if 25 <= age <= 55 else 1

    if "demat" in category or "equity" in category or "stock" in category:
        score += 4 if age >= 21 and income >= 600_000 else 1

    if "wealth" in category or "private" in category:
        score += 8 if income >= 5_000_000 else 0

    if "bond" in category:
        score += 3 if income >= 1_000_000 else 1

    return score


def generate_investments(customer, investments, index):
    rows = []

    income = customer["annual_income"]
    age = customer["age"]
    occupation = customer["employment_type"]

    # No investment for many low-income / student customers.
    base_probability = 0.20

    if income >= 600_000:
        base_probability += 0.20
    if income >= 1_200_000:
        base_probability += 0.20
    if income >= 2_500_000:
        base_probability += 0.15
    if occupation == "Student":
        base_probability *= 0.25
    if age >= 30:
        base_probability += 0.10

    if not weighted_bool(clamp(base_probability, 0, 0.90)):
        return rows

    weighted_products = [
        (product, investment_match_score(customer, product))
        for product in investments
    ]

    selected = choose_weighted(weighted_products)

    product_id = first_value(
        selected,
        ["investment_product_id", "product_code"],
        "INV001",
    )
    product_name = first_value(
        selected,
        ["product_name"],
        "Investment Product",
    )
    category = first_value(
        selected,
        ["product_category", "product_subcategory", "product_type"],
        "Investment",
    )
    provider = first_value(
        selected,
        ["provider", "issuer", "brand_name"],
        "HDFC",
    )

    category_lower = category.lower()

    investment_id = f"INVH{index:05d}"

    # --------------------------------------------------------
    # SIP
    # --------------------------------------------------------

    if "sip" in category_lower or "sip" in product_name.lower():
        monthly_amount = random.choice([
            1_000, 2_000, 3_000, 5_000, 7_500,
            10_000, 15_000, 20_000, 25_000, 50_000,
        ])

        if income < 600_000:
            monthly_amount = min(monthly_amount, 3_000)

        start_date = random_date(
            max(
                date.fromisoformat(customer["customer_since"]),
                date(2020, 1, 1),
            ),
            TODAY - timedelta(days=30),
        )

        rows.append({
            "customer_investment_id": investment_id,
            "customer_id": customer["customer_id"],
            "investment_product_id": product_id,
            "investment_product_name": product_name,
            "investment_category": category,
            "provider": provider,
            "investment_type": "SIP",
            "investment_mode": "Monthly SIP",
            "monthly_amount": monthly_amount,
            "initial_investment_amount": monthly_amount,
            "total_invested_amount": monthly_amount * max(
                1,
                ((TODAY.year - start_date.year) * 12)
                + TODAY.month - start_date.month
            ),
            "current_value": monthly_amount * max(
                1,
                ((TODAY.year - start_date.year) * 12)
                + TODAY.month - start_date.month
            ) * random.uniform(1.02, 1.18),
            "start_date": start_date.isoformat(),
            "status": "Active",
        })

    # --------------------------------------------------------
    # DEMAT
    # --------------------------------------------------------

    elif "demat" in category_lower or "3-in-1" in product_name.lower():
        rows.append({
            "customer_investment_id": investment_id,
            "customer_id": customer["customer_id"],
            "investment_product_id": product_id,
            "investment_product_name": product_name,
            "investment_category": "Demat",
            "provider": provider,
            "investment_type": "Demat Account",
            "investment_mode": "Account",
            "monthly_amount": 0,
            "initial_investment_amount": 0,
            "total_invested_amount": 0,
            "current_value": 0,
            "start_date": random_date(
                date.fromisoformat(customer["customer_since"]),
                TODAY,
            ).isoformat(),
            "status": "Active",
        })

    # --------------------------------------------------------
    # NPS
    # --------------------------------------------------------

    elif "nps" in category_lower:
        monthly = random.choice([
            1_000, 2_000, 3_000, 5_000, 10_000
        ])

        start_date = random_date(
            max(
                date.fromisoformat(customer["customer_since"]),
                date(2020, 1, 1),
            ),
            TODAY - timedelta(days=30),
        )

        months = max(
            1,
            (TODAY.year - start_date.year) * 12
            + TODAY.month - start_date.month,
        )

        invested = monthly * months

        rows.append({
            "customer_investment_id": investment_id,
            "customer_id": customer["customer_id"],
            "investment_product_id": product_id,
            "investment_product_name": product_name,
            "investment_category": "NPS",
            "provider": provider,
            "investment_type": "NPS",
            "investment_mode": "Recurring",
            "monthly_amount": monthly,
            "initial_investment_amount": monthly,
            "total_invested_amount": invested,
            "current_value": round(
                invested * random.uniform(1.02, 1.15),
                2,
            ),
            "start_date": start_date.isoformat(),
            "status": "Active",
        })

    # --------------------------------------------------------
    # Direct Equity / IPO / ETF / Bond / Mutual Fund
    # --------------------------------------------------------

    else:
        amount = random.choice([
            10_000, 25_000, 50_000, 75_000,
            100_000, 200_000, 500_000, 1_000_000,
        ])

        if income < 600_000:
            amount = min(amount, 25_000)

        current_value = round(
            amount * random.uniform(0.92, 1.25),
            2,
        )

        investment_mode = (
            "Lumpsum"
            if "mutual fund" in category_lower
            else "Direct Purchase"
        )

        rows.append({
            "customer_investment_id": investment_id,
            "customer_id": customer["customer_id"],
            "investment_product_id": product_id,
            "investment_product_name": product_name,
            "investment_category": category,
            "provider": provider,
            "investment_type": category,
            "investment_mode": investment_mode,
            "monthly_amount": 0,
            "initial_investment_amount": amount,
            "total_invested_amount": amount,
            "current_value": current_value,
            "start_date": random_date(
                max(
                    date.fromisoformat(customer["customer_since"]),
                    date(2020, 1, 1),
                ),
                TODAY,
            ).isoformat(),
            "status": "Active",
        })

    return rows


def insurance_match_score(customer, row):
    age = customer["age"]
    marital = customer["marital_status"]
    income = customer["annual_income"]

    category = str(
        first_value(
            row,
            ["product_category", "product_subcategory", "insurance_type"],
            "",
        )
    ).lower()

    score = 1

    if "health" in category:
        score += 5
        if age >= 45:
            score += 2

    if "life" in category or "term" in category:
        score += 4
        if marital == "Married":
            score += 3
        if income >= 1_000_000:
            score += 2

    if "travel" in category:
        score += 2

    if "motor" in category:
        score += 2

    if "accident" in category:
        score += 2

    if "home" in category:
        score += 2

    return score


def generate_insurance(customer, insurance, index):
    rows = []

    income = customer["annual_income"]
    age = customer["age"]
    marital = customer["marital_status"]

    probability = 0.18

    if income >= 600_000:
        probability += 0.15

    if income >= 1_200_000:
        probability += 0.15

    if marital == "Married":
        probability += 0.15

    if age >= 30:
        probability += 0.10

    if age >= 45:
        probability += 0.10

    if not weighted_bool(clamp(probability, 0, 0.85)):
        return rows

    weighted_products = [
        (product, insurance_match_score(customer, product))
        for product in insurance
    ]

    selected = choose_weighted(weighted_products)

    product_id = first_value(
        selected,
        ["insurance_product_id", "product_code"],
        "INS001",
    )

    product_name = first_value(
        selected,
        ["product_name"],
        "Insurance Product",
    )

    category = first_value(
        selected,
        ["product_category", "product_subcategory", "insurance_type"],
        "Life",
    )

    insurer = first_value(
        selected,
        ["insurer_name", "provider", "issuer"],
        "HDFC ERGO",
    )

    category_lower = category.lower()

    if "life" in category_lower or "term" in category_lower:
        sum_assured = random.choice([
            2_500_000,
            5_000_000,
            7_500_000,
            10_000_000,
            20_000_000,
        ])

        premium = round(
            max(
                4_000,
                sum_assured * random.uniform(0.0015, 0.0040)
            ),
            2,
        )

        frequency = "Annual"

    elif "health" in category_lower:
        sum_assured = random.choice([
            500_000,
            1_000_000,
            1_500_000,
            2_000_000,
            3_000_000,
        ])

        premium = random.choice([
            10_000,
            15_000,
            20_000,
            25_000,
            35_000,
        ])

        frequency = "Annual"

    elif "travel" in category_lower:
        sum_assured = random.choice([
            500_000,
            1_000_000,
            2_500_000,
        ])

        premium = random.choice([
            1_000,
            2_000,
            3_000,
            5_000,
        ])

        frequency = "Single"

    elif "motor" in category_lower:
        sum_assured = random.choice([
            300_000,
            500_000,
            1_000_000,
            1_500_000,
        ])

        premium = random.choice([
            10_000,
            15_000,
            20_000,
            25_000,
        ])

        frequency = "Annual"

    else:
        sum_assured = random.choice([
            500_000,
            1_000_000,
            2_000_000,
        ])

        premium = random.choice([
            5_000,
            10_000,
            15_000,
        ])

        frequency = "Annual"

    policy_start = random_date(
        max(
            date.fromisoformat(customer["customer_since"]),
            date(2020, 1, 1),
        ),
        TODAY,
    )

    if frequency == "Single":
        policy_end = policy_start + timedelta(days=60)
    elif "life" in category_lower or "term" in category_lower:
        policy_end = policy_start + timedelta(days=365 * 25)
    else:
        policy_end = policy_start + timedelta(days=365)

    rows.append({
        "customer_insurance_id": f"INSC{index:05d}",
        "customer_id": customer["customer_id"],
        "insurance_product_id": product_id,
        "insurance_product_name": product_name,
        "insurance_category": category,
        "insurer_name": insurer,
        "policy_number_masked": (
            f"POLXXXX{random.randint(100000,999999)}"
        ),
        "sum_assured": sum_assured,
        "premium_amount": premium,
        "premium_frequency": frequency,
        "policy_start_date": policy_start.isoformat(),
        "policy_end_date": policy_end.isoformat(),
        "policy_status": "Active",
        "nominee_available": "Yes",
    })

    return rows


# ============================================================
# CUSTOMER 360 BUILDER
# ============================================================

def build_customer_360(
    customer,
    accounts,
    debit_cards,
    credit_cards,
    loans,
    deposits,
    investments,
    insurance,
):
    customer_id = customer["customer_id"]

    customer_credit_cards = [
        x for x in credit_cards
        if x["customer_id"] == customer_id
    ]

    customer_loans = [
        x for x in loans
        if x["customer_id"] == customer_id
    ]

    customer_deposits = [
        x for x in deposits
        if x["customer_id"] == customer_id
    ]

    customer_investments = [
        x for x in investments
        if x["customer_id"] == customer_id
    ]

    customer_insurance = [
        x for x in insurance
        if x["customer_id"] == customer_id
    ]

    customer_debit_cards = [
        x for x in debit_cards
        if x["customer_id"] == customer_id
    ]

    customer_accounts = [
        x for x in accounts
        if x["customer_id"] == customer_id
    ]

    sip_investments = [
        x for x in customer_investments
        if x["investment_type"].lower() == "sip"
    ]

    mutual_funds = [
        x for x in customer_investments
        if "mutual" in x["investment_category"].lower()
    ]

    stocks = [
        x for x in customer_investments
        if (
            "equity" in x["investment_category"].lower()
            or "stock" in x["investment_category"].lower()
        )
    ]

    bonds = [
        x for x in customer_investments
        if "bond" in x["investment_category"].lower()
    ]

    nps = [
        x for x in customer_investments
        if "nps" in x["investment_category"].lower()
    ]

    demat = [
        x for x in customer_investments
        if "demat" in x["investment_category"].lower()
    ]

    etfs = [
        x for x in customer_investments
        if "etf" in x["investment_category"].lower()
    ]

    life_insurance = [
        x for x in customer_insurance
        if (
            "life" in x["insurance_category"].lower()
            or "term" in x["insurance_category"].lower()
        )
    ]

    health_insurance = [
        x for x in customer_insurance
        if "health" in x["insurance_category"].lower()
    ]

    travel_insurance = [
        x for x in customer_insurance
        if "travel" in x["insurance_category"].lower()
    ]

    motor_insurance = [
        x for x in customer_insurance
        if "motor" in x["insurance_category"].lower()
    ]

    active_loans = [
        x for x in customer_loans
        if x["loan_status"] == "Active"
    ]

    total_loan_outstanding = round(
        sum(
            to_float(x["outstanding_principal"])
            for x in active_loans
        ),
        2,
    )

    total_credit_limit = round(
        sum(
            to_float(x["credit_limit"])
            for x in customer_credit_cards
        ),
        2,
    )

    total_credit_outstanding = round(
        sum(
            to_float(x["current_outstanding"])
            for x in customer_credit_cards
        ),
        2,
    )

    total_deposit_value = round(
        sum(
            to_float(x["principal_amount"])
            for x in customer_deposits
            if x["deposit_status"] == "Active"
        ),
        2,
    )

    total_investment_value = round(
        sum(
            to_float(x["current_value"])
            for x in customer_investments
        ),
        2,
    )

    total_insurance_cover = round(
        sum(
            to_float(x["sum_assured"])
            for x in customer_insurance
        ),
        2,
    )

    total_monthly_sip = round(
        sum(
            to_float(x["monthly_amount"])
            for x in sip_investments
        ),
        2,
    )

    total_monthly_emi = round(
        sum(
            to_float(x["emi_amount"])
            for x in active_loans
        ),
        2,
    )

    product_summary = {
        "total_accounts": len(customer_accounts),
        "total_debit_cards": len(customer_debit_cards),
        "total_credit_cards": len(customer_credit_cards),
        "total_active_loans": len(active_loans),
        "total_active_deposits": len([
            x for x in customer_deposits
            if x["deposit_status"] == "Active"
        ]),
        "total_investment_products": len(customer_investments),
        "total_insurance_policies": len(customer_insurance),

        "has_credit_card": len(customer_credit_cards) > 0,
        "has_debit_card": len(customer_debit_cards) > 0,
        "has_loan": len(active_loans) > 0,
        "has_fd_or_deposit": len(customer_deposits) > 0,
        "has_investment": len(customer_investments) > 0,
        "has_sip": len(sip_investments) > 0,
        "has_mutual_fund": len(mutual_funds) > 0,
        "has_stocks": len(stocks) > 0,
        "has_bonds": len(bonds) > 0,
        "has_nps": len(nps) > 0,
        "has_demat": len(demat) > 0,
        "has_etf": len(etfs) > 0,

        "has_life_insurance": len(life_insurance) > 0,
        "has_health_insurance": len(health_insurance) > 0,
        "has_travel_insurance": len(travel_insurance) > 0,
        "has_motor_insurance": len(motor_insurance) > 0,

        "total_credit_limit": total_credit_limit,
        "total_credit_outstanding": total_credit_outstanding,
        "credit_utilization_ratio": round(
            total_credit_outstanding / total_credit_limit,
            4,
        ) if total_credit_limit > 0 else 0,

        "total_loan_outstanding": total_loan_outstanding,
        "total_monthly_emi": total_monthly_emi,

        "total_deposit_value": total_deposit_value,
        "total_investment_value": total_investment_value,
        "total_monthly_sip": total_monthly_sip,
        "total_insurance_cover": total_insurance_cover,
    }

    return {
        "customer_id": customer_id,

        "personal_profile": {
            "customer_number": customer["customer_number"],
            "name": (
                f'{customer["first_name"]} '
                f'{customer["middle_name"]} '
                f'{customer["last_name"]}'
            ).replace("  ", " ").strip(),
            "first_name": customer["first_name"],
            "last_name": customer["last_name"],
            "age": customer["age"],
            "date_of_birth": customer["date_of_birth"],
            "gender": customer["gender"],
            "marital_status": customer["marital_status"],
            "nationality": customer["nationality"],
            "residential_status": customer["residential_status"],
            "city": customer["city"],
            "state": customer["state"],
            "country": customer["country"],
            "pincode": customer["pincode"],
            "education_level": customer["education_level"],
        },

        "employment_and_income": {
            "occupation_type": customer["occupation_type"],
            "occupation": customer["occupation"],
            "employer_name": customer["employer_name"],
            "employment_type": customer["employment_type"],
            "annual_income": customer["annual_income"],
            "income_range": customer["income_range"],
        },

        "banking_relationship": {
            "customer_since": customer["customer_since"],
            "customer_status": customer["customer_status"],
            "customer_segment_type": customer["customer_segment_type"],
            "kyc_status": customer["kyc_status"],
            "kyc_last_updated": customer["kyc_last_updated"],
            "risk_profile": customer["risk_profile"],
            "credit_score": customer["credit_score"],
            "relationship_manager_id": customer["relationship_manager_id"],
            "preferred_language": customer["preferred_language"],
            "preferred_channel": customer["preferred_channel"],
            "marketing_consent": customer["marketing_consent"],
        },

        "accounts": customer_accounts,

        "debit_cards": customer_debit_cards,

        "credit_cards": customer_credit_cards,

        "loans": customer_loans,

        "deposits": customer_deposits,

        "investments": {
            "all": customer_investments,
            "sip": sip_investments,
            "mutual_funds": mutual_funds,
            "stocks": stocks,
            "bonds": bonds,
            "nps": nps,
            "demat": demat,
            "etfs": etfs,
        },

        "insurance": {
            "all": customer_insurance,
            "life": life_insurance,
            "health": health_insurance,
            "travel": travel_insurance,
            "motor": motor_insurance,
        },

        "financial_relationship_summary": {
            "total_credit_limit": total_credit_limit,
            "total_credit_outstanding": total_credit_outstanding,
            "credit_utilization_ratio": product_summary[
                "credit_utilization_ratio"
            ],

            "total_loan_outstanding": total_loan_outstanding,
            "total_monthly_emi": total_monthly_emi,

            "total_deposit_value": total_deposit_value,

            "total_investment_value": total_investment_value,
            "total_monthly_sip": total_monthly_sip,

            "total_insurance_cover": total_insurance_cover,
        },

        "product_summary": product_summary,
    }


# ============================================================
# CSV WRITERS
# ============================================================

def write_csv(path: Path, rows: list[dict]):
    if not rows:
        # Keep an empty CSV valid.
        path.write_text("", encoding="utf-8")
        return

    # Use union of all keys so no information is lost.
    fieldnames = []
    seen = set()

    for row in rows:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)

    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )

        writer.writeheader()

        for row in rows:
            writer.writerow(row)


# ============================================================
# GENERATE ALL DATA
# ============================================================

def main():
    catalogues = load_catalogues()

    credit_cards = get_credit_cards(catalogues)
    loans = get_loans(catalogues)
    investments = get_investments(catalogues)
    insurance = get_insurance(catalogues)

    deposits = (
        load_csv_records("deposit_products.csv")
        or [
            {
                "deposit_product_id": item[0],
                "product_name": item[1],
                "deposit_type": item[2],
                "interest_rate": item[3],
            }
            for item in DEPOSIT_PRODUCTS_FALLBACK
        ]
    )

    all_customers = []
    all_accounts = []
    all_debit_cards = []
    all_credit_cards = []
    all_loans = []
    all_deposits = []
    all_investments = []
    all_insurance = []

    customer_360 = []

    for i in range(1, NUM_CUSTOMERS + 1):

        customer = generate_base_customer(i)

        # ----------------------------------------------------
        # ACCOUNT
        # ----------------------------------------------------

        accounts = (
            generate_accounts(customer, i)
            if should_have_account(customer)
            else []
        )

        # ----------------------------------------------------
        # DEBIT CARD
        # ----------------------------------------------------

        debit_cards = []

        debit_probability = 0.90

        if customer["customer_status"] == "Dormant":
            debit_probability = 0.70

        if weighted_bool(debit_probability):
            product = random.choice(DEBIT_CARD_PRODUCTS)

            debit_cards.append({
                "customer_debit_card_id": (
                    f"DCA{i:05d}"
                ),
                "customer_id": customer["customer_id"],
                "debit_card_product_id": product[0],
                "card_name": product[1],
                "card_network": product[2],
                "card_variant": product[3],
                "card_number_masked": (
                    f"XXXX-XXXX-XXXX-{random.randint(1000,9999)}"
                ),
                "issue_date": random_date(
                    date.fromisoformat(
                        customer["customer_since"]
                    ),
                    TODAY - timedelta(days=30),
                ).isoformat(),
                "expiry_date": (
                    TODAY + timedelta(
                        days=random.randint(365, 1800)
                    )
                ).isoformat(),
                "card_status": "Active",
                "daily_atm_limit": random.choice([
                    25000, 50000, 75000, 100000
                ]),
                "daily_pos_limit": random.choice([
                    50000, 100000, 150000, 200000
                ]),
                "international_enabled": random.choice([
                    "Yes", "Yes", "No"
                ]),
            })

        # ----------------------------------------------------
        # CREDIT CARD
        # ----------------------------------------------------

        credit_cards_for_customer = generate_credit_cards(
            customer,
            credit_cards,
            i,
        )

        # ----------------------------------------------------
        # LOANS
        # ----------------------------------------------------

        loans_for_customer = generate_loans(
            customer,
            loans,
            i,
        )

        # ----------------------------------------------------
        # DEPOSITS
        # ----------------------------------------------------

        deposits_for_customer = generate_deposits(
            customer,
            deposits,
            i,
        )

        # ----------------------------------------------------
        # INVESTMENTS
        # ----------------------------------------------------

        investments_for_customer = generate_investments(
            customer,
            investments,
            i,
        )

        # ----------------------------------------------------
        # INSURANCE
        # ----------------------------------------------------

        insurance_for_customer = generate_insurance(
            customer,
            insurance,
            i,
        )

        # ----------------------------------------------------
        # Store
        # ----------------------------------------------------

        all_customers.append(customer)
        all_accounts.extend(accounts)
        all_debit_cards.extend(debit_cards)
        all_credit_cards.extend(credit_cards_for_customer)
        all_loans.extend(loans_for_customer)
        all_deposits.extend(deposits_for_customer)
        all_investments.extend(investments_for_customer)
        all_insurance.extend(insurance_for_customer)

        # ----------------------------------------------------
        # Customer 360
        # ----------------------------------------------------

        profile = build_customer_360(
            customer,
            accounts,
            debit_cards,
            credit_cards_for_customer,
            loans_for_customer,
            deposits_for_customer,
            investments_for_customer,
            insurance_for_customer,
        )

        customer_360.append(profile)

    # ========================================================
    # WRITE FILES
    # ========================================================

    write_csv(CUSTOMERS_FILE, all_customers)
    write_csv(CUSTOMER_ACCOUNTS_FILE, all_accounts)
    write_csv(CUSTOMER_DEBIT_CARDS_FILE, all_debit_cards)
    write_csv(CUSTOMER_CREDIT_CARDS_FILE, all_credit_cards)
    write_csv(CUSTOMER_LOANS_FILE, all_loans)
    write_csv(CUSTOMER_DEPOSITS_FILE, all_deposits)
    write_csv(CUSTOMER_INVESTMENTS_FILE, all_investments)
    write_csv(CUSTOMER_INSURANCE_FILE, all_insurance)

    with CUSTOMER_360_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            customer_360,
            file,
            indent=2,
            ensure_ascii=False,
        )

    # ========================================================
    # SUMMARY
    # ========================================================

    resident_count = sum(
        x["residential_status"] == "Resident"
        for x in all_customers
    )

    nri_count = len(all_customers) - resident_count

    customers_with_credit_card = len({
        x["customer_id"]
        for x in all_credit_cards
    })

    customers_with_loan = len({
        x["customer_id"]
        for x in all_loans
    })

    customers_with_sip = len({
        x["customer_id"]
        for x in all_investments
        if x["investment_type"].lower() == "sip"
    })

    customers_with_investment = len({
        x["customer_id"]
        for x in all_investments
    })

    customers_with_insurance = len({
        x["customer_id"]
        for x in all_insurance
    })

    customers_with_demat = len({
        x["customer_id"]
        for x in all_investments
        if "demat" in x["investment_category"].lower()
    })

    print("\n" + "=" * 78)
    print("CUSTOMER 360 DATASET GENERATED")
    print("=" * 78)

    print(f"Customers                  : {len(all_customers)}")
    print(f"Resident customers         : {resident_count}")
    print(f"NRI customers              : {nri_count}")

    print(f"\nAccounts                   : {len(all_accounts)}")
    print(f"Debit cards                : {len(all_debit_cards)}")
    print(f"Credit cards               : {len(all_credit_cards)}")
    print(f"Loans                      : {len(all_loans)}")
    print(f"Deposits                   : {len(all_deposits)}")
    print(f"Investments                : {len(all_investments)}")
    print(f"Insurance policies         : {len(all_insurance)}")

    print("\nCUSTOMER COVERAGE")
    print("-" * 78)

    print(
        f"Customers with credit card : "
        f"{customers_with_credit_card}"
    )

    print(
        f"Customers with loan        : "
        f"{customers_with_loan}"
    )

    print(
        f"Customers with investment  : "
        f"{customers_with_investment}"
    )

    print(
        f"Customers with SIP         : "
        f"{customers_with_sip}"
    )

    print(
        f"Customers with insurance   : "
        f"{customers_with_insurance}"
    )

    print(
        f"Customers with demat       : "
        f"{customers_with_demat}"
    )

    print("\nFILES")
    print("-" * 78)

    print(CUSTOMERS_FILE)
    print(CUSTOMER_ACCOUNTS_FILE)
    print(CUSTOMER_DEBIT_CARDS_FILE)
    print(CUSTOMER_CREDIT_CARDS_FILE)
    print(CUSTOMER_LOANS_FILE)
    print(CUSTOMER_DEPOSITS_FILE)
    print(CUSTOMER_INVESTMENTS_FILE)
    print(CUSTOMER_INSURANCE_FILE)
    print(CUSTOMER_360_FILE)

    print("=" * 78)


if __name__ == "__main__":
    main()
