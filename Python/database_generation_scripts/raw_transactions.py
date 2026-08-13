


import csv
import random
import uuid
from datetime import datetime, timedelta

# ============================================================
# CONFIG
# ============================================================

NUM_TRANSACTIONS = 10_000
NUM_CUSTOMERS = 300
OUTPUT_FILE = "raw_transactions.csv"

random.seed(42)

# Last 1 year from 13-Aug-2026
END_DATE = datetime(2026, 8, 13)
START_DATE = END_DATE - timedelta(days=365)

# ============================================================
# LOAD CUSTOMER IDS
# ============================================================

CUSTOMER_IDS = [
    f"CUST{i:05d}"
    for i in range(1, NUM_CUSTOMERS + 1)
]

# Every customer gets an account.
# Some will additionally get cards.
ACCOUNT_IDS = {
    customer_id: f"ACC{index:05d}"
    for index, customer_id in enumerate(CUSTOMER_IDS, start=1)
}

CARD_IDS = {
    customer_id: f"CARD{index:05d}"
    for index, customer_id in enumerate(CUSTOMER_IDS, start=1)
}

# Some transactions will not use cards.
CARD_USAGE_PROBABILITY = 0.35

# ============================================================
# MERCHANT MASTER
# ============================================================

MERCHANTS = {

    # --------------------------------------------------------
    # FLIGHTS
    # --------------------------------------------------------
    "AIRLINES": [
        ("MER0001", "IndiGo", "4511"),
        ("MER0002", "Air India", "4511"),
        ("MER0003", "Air India Express", "4511"),
        ("MER0004", "Vistara", "4511"),
        ("MER0005", "Akasa Air", "4511"),
        ("MER0006", "SpiceJet", "4511"),
        ("MER0007", "Emirates", "4511"),
        ("MER0008", "Qatar Airways", "4511"),
        ("MER0009", "Singapore Airlines", "4511"),
        ("MER0010", "Etihad Airways", "4511"),
        ("MER0011", "Lufthansa", "4511"),
    ],

    # --------------------------------------------------------
    # FOOD DELIVERY
    # --------------------------------------------------------
    "FOOD_DELIVERY": [
        ("MER0101", "Swiggy", "5812"),
        ("MER0102", "Zomato", "5812"),
        ("MER0103", "EatSure", "5812"),
        ("MER0104", "Dominos", "5812"),
        ("MER0105", "McDonalds", "5812"),
        ("MER0106", "KFC", "5812"),
        ("MER0107", "Pizza Hut", "5812"),
        ("MER0108", "Burger King", "5812"),
        ("MER0109", "Starbucks", "5814"),
        ("MER0110", "Subway", "5812"),
    ],

    # --------------------------------------------------------
    # E-COMMERCE
    # --------------------------------------------------------
    "E_COMMERCE": [
        ("MER0201", "Amazon India", "5311"),
        ("MER0202", "Flipkart", "5311"),
        ("MER0203", "Myntra", "5311"),
        ("MER0204", "Ajio", "5311"),
        ("MER0205", "Meesho", "5311"),
        ("MER0206", "Nykaa", "5311"),
        ("MER0207", "Croma", "5732"),
        ("MER0208", "Reliance Digital", "5732"),
        ("MER0209", "Tata Cliq", "5311"),
        ("MER0210", "Decathlon", "5941"),
    ],

    # --------------------------------------------------------
    # SHOPPING
    # --------------------------------------------------------
    "SHOPPING": [
        ("MER0301", "Reliance Trends", "5311"),
        ("MER0302", "Westside", "5311"),
        ("MER0303", "Lifestyle", "5311"),
        ("MER0304", "Pantaloons", "5311"),
        ("MER0305", "Shoppers Stop", "5311"),
        ("MER0306", "Zudio", "5311"),
        ("MER0307", "H&M", "5311"),
        ("MER0308", "Zara", "5311"),
        ("MER0309", "IKEA", "5712"),
        ("MER0310", "Home Centre", "5712"),
    ],

    # --------------------------------------------------------
    # SUPERMARKET / GROCERY
    # --------------------------------------------------------
    "GROCERY": [
        ("MER0401", "DMart", "5411"),
        ("MER0402", "Reliance Smart", "5411"),
        ("MER0403", "Nature's Basket", "5411"),
        ("MER0404", "BigBasket", "5411"),
        ("MER0405", "Blinkit", "5411"),
        ("MER0406", "Zepto", "5411"),
        ("MER0407", "Swiggy Instamart", "5411"),
    ],

    # --------------------------------------------------------
    # CAB / TRANSPORT
    # --------------------------------------------------------
    "CAB": [
        ("MER0501", "Uber", "4121"),
        ("MER0502", "Ola", "4121"),
        ("MER0503", "Rapido", "4121"),
        ("MER0504", "BluSmart", "4121"),
    ],

    # --------------------------------------------------------
    # BUS
    # --------------------------------------------------------
    "BUS": [
        ("MER0601", "RedBus", "4789"),
        ("MER0602", "AbhiBus", "4789"),
        ("MER0603", "MSRTC", "4131"),
        ("MER0604", "KSRTC", "4131"),
        ("MER0605", "APSRTC", "4131"),
        ("MER0606", "TNSTC", "4131"),
    ],

    # --------------------------------------------------------
    # TRAIN / RAIL
    # --------------------------------------------------------
    "TRAIN": [
        ("MER0701", "IRCTC", "4112"),
        ("MER0702", "Indian Railways", "4112"),
    ],

    # --------------------------------------------------------
    # HOTELS
    # --------------------------------------------------------
    "HOTELS": [
        ("MER0801", "Taj Hotels", "7011"),
        ("MER0802", "Marriott", "7011"),
        ("MER0803", "ITC Hotels", "7011"),
        ("MER0804", "Hyatt", "7011"),
        ("MER0805", "OYO", "7011"),
        ("MER0806", "MakeMyTrip", "4722"),
        ("MER0807", "Booking.com", "4722"),
        ("MER0808", "Agoda", "4722"),
    ],

    # --------------------------------------------------------
    # MOVIES / THEATRES
    # --------------------------------------------------------
    "MOVIES": [
        ("MER0901", "PVR INOX", "7832"),
        ("MER0902", "Cinepolis", "7832"),
        ("MER0903", "BookMyShow", "7832"),
        ("MER0904", "Carnival Cinemas", "7832"),
    ],

    # --------------------------------------------------------
    # FUEL
    # --------------------------------------------------------
    "FUEL": [
        ("MER1001", "Indian Oil", "5541"),
        ("MER1002", "Bharat Petroleum", "5541"),
        ("MER1003", "Hindustan Petroleum", "5541"),
        ("MER1004", "Shell", "5541"),
        ("MER1005", "Nayara Energy", "5541"),
    ],

    # --------------------------------------------------------
    # UTILITIES
    # --------------------------------------------------------
    "UTILITIES": [
        ("MER1101", "MSEDCL", "4900"),
        ("MER1102", "Adani Electricity", "4900"),
        ("MER1103", "Tata Power", "4900"),
        ("MER1104", "BESCOM", "4900"),
        ("MER1105", "BSES", "4900"),
        ("MER1106", "Airtel", "4814"),
        ("MER1107", "Jio", "4814"),
        ("MER1108", "Vi", "4814"),
        ("MER1109", "BSNL", "4814"),
        ("MER1110", "Mahanagar Gas", "4900"),
    ],

    # --------------------------------------------------------
    # ENTERTAINMENT / OTT
    # --------------------------------------------------------
    "ENTERTAINMENT": [
        ("MER1201", "Netflix", "4899"),
        ("MER1202", "Spotify", "4899"),
        ("MER1203", "Amazon Prime", "4899"),
        ("MER1204", "Disney+ Hotstar", "4899"),
        ("MER1205", "Sony LIV", "4899"),
        ("MER1206", "YouTube Premium", "4899"),
        ("MER1207", "JioHotstar", "4899"),
    ],

    # --------------------------------------------------------
    # HEALTHCARE
    # --------------------------------------------------------
    "HEALTHCARE": [
        ("MER1301", "Apollo Hospitals", "8011"),
        ("MER1302", "Fortis Healthcare", "8011"),
        ("MER1303", "Max Healthcare", "8011"),
        ("MER1304", "Manipal Hospitals", "8011"),
        ("MER1305", "Apollo Pharmacy", "5912"),
        ("MER1306", "Tata 1mg", "5912"),
        ("MER1307", "PharmEasy", "5912"),
    ],

    # --------------------------------------------------------
    # EDUCATION
    # --------------------------------------------------------
    "EDUCATION": [
        ("MER1401", "Coursera", "8299"),
        ("MER1402", "Udemy", "8299"),
        ("MER1403", "Unacademy", "8299"),
        ("MER1404", "BYJU'S", "8299"),
        ("MER1405", "upGrad", "8299"),
    ],

    # --------------------------------------------------------
    # INVESTMENTS / DEMAT / BROKING
    # --------------------------------------------------------
    "INVESTMENT": [
        ("MER1501", "Zerodha", "6211"),
        ("MER1502", "Groww", "6211"),
        ("MER1503", "Upstox", "6211"),
        ("MER1504", "Angel One", "6211"),
        ("MER1505", "HDFC Securities", "6211"),
        ("MER1506", "ICICI Direct", "6211"),
        ("MER1507", "NSE", "6211"),
        ("MER1508", "BSE", "6211"),
    ],

    # --------------------------------------------------------
    # SIP / MUTUAL FUNDS
    # --------------------------------------------------------
    "SIP": [
        ("MER1601", "HDFC Mutual Fund", "6211"),
        ("MER1602", "SBI Mutual Fund", "6211"),
        ("MER1603", "ICICI Prudential Mutual Fund", "6211"),
        ("MER1604", "Nippon India Mutual Fund", "6211"),
        ("MER1605", "Axis Mutual Fund", "6211"),
        ("MER1606", "Mirae Asset Mutual Fund", "6211"),
        ("MER1607", "Aditya Birla Sun Life Mutual Fund", "6211"),
    ],

    # --------------------------------------------------------
    # INSURANCE
    # --------------------------------------------------------
    "INSURANCE": [
        ("MER1701", "HDFC Life", "6300"),
        ("MER1702", "HDFC ERGO", "6300"),
        ("MER1703", "ICICI Lombard", "6300"),
        ("MER1704", "Tata AIA", "6300"),
        ("MER1705", "Niva Bupa", "6300"),
        ("MER1706", "Star Health", "6300"),
    ],

    # --------------------------------------------------------
    # BILL PAYMENTS
    # --------------------------------------------------------
    "BILLS": [
        ("MER1801", "Electricity Bill", "4900"),
        ("MER1802", "Water Bill", "4900"),
        ("MER1803", "Gas Bill", "4900"),
        ("MER1804", "Mobile Recharge", "4814"),
        ("MER1805", "DTH Recharge", "4899"),
        ("MER1806", "Broadband Bill", "4814"),
        ("MER1807", "Credit Card Bill", "6012"),
    ],

    # --------------------------------------------------------
    # RESTAURANTS
    # --------------------------------------------------------
    "RESTAURANTS": [
        ("MER1901", "Social", "5812"),
        ("MER1902", "Barbeque Nation", "5812"),
        ("MER1903", "Theobroma", "5812"),
        ("MER1904", "Biryani Blues", "5812"),
        ("MER1905", "Mainland China", "5812"),
        ("MER1906", "Cafe Coffee Day", "5814"),
    ],

    # --------------------------------------------------------
    # EDUCATION / COLLEGE FEES
    # --------------------------------------------------------
    "COLLEGE_FEES": [
        ("MER2001", "University Fee Portal", "8220"),
        ("MER2002", "College Fee Payment", "8220"),
        ("MER2003", "School Fee Payment", "8211"),
    ],

    # --------------------------------------------------------
    # RENT
    # --------------------------------------------------------
    "RENT": [
        ("MER2101", "Rent Payment", "6513"),
        ("MER2102", "Housing Rent", "6513"),
    ],

    # --------------------------------------------------------
    # P2P
    # --------------------------------------------------------
    "P2P": [
        ("MER2201", "UPI Transfer - Rahul",""),
        ("MER2202", "UPI Transfer - Priya",""),
        ("MER2203", "UPI Transfer - Amit",""),
        ("MER2204", "UPI Transfer - Neha",""),
        ("MER2205", "UPI Transfer - Family",""),
    ],
}

# ============================================================
# CATEGORY WEIGHTS
#
# These make the 10,000 transactions more realistic.
# ============================================================

CATEGORY_WEIGHTS = {
    "P2P": 14,
    "GROCERY": 11,
    "FOOD_DELIVERY": 9,
    "RESTAURANTS": 7,
    "E_COMMERCE": 8,
    "SHOPPING": 7,
    "UTILITIES": 7,
    "CAB": 5,
    "FUEL": 5,
    "ENTERTAINMENT": 4,
    "BILLS": 4,
    "TRAVEL": 0,  # special handling below
    "AIRLINES": 3,
    "BUS": 2,
    "TRAIN": 3,
    "HOTELS": 2,
    "MOVIES": 3,
    "HEALTHCARE": 3,
    "EDUCATION": 2,
    "COLLEGE_FEES": 2,
    "INVESTMENT": 2,
    "SIP": 3,
    "INSURANCE": 1,
    "RENT": 2,
}

CATEGORIES = list(CATEGORY_WEIGHTS.keys())
WEIGHTS = list(CATEGORY_WEIGHTS.values())

# Remove zero weight
FILTERED = [
    (c, w)
    for c, w in zip(CATEGORIES, WEIGHTS)
    if w > 0
]

CATEGORIES = [x[0] for x in FILTERED]
WEIGHTS = [x[1] for x in FILTERED]

# ============================================================
# TRANSACTION MODES
# ============================================================

TRANSACTION_MODES = [
    ("UPI", 45),
    ("Debit Card", 20),
    ("Credit Card", 15),
    ("NEFT", 5),
    ("IMPS", 5),
    ("RTGS", 2),
    ("ATM", 4),
    ("Cash", 2),
    ("Cheque", 1),
    ("Auto Debit", 1),
]

MODE_NAMES = [x[0] for x in TRANSACTION_MODES]
MODE_WEIGHTS = [x[1] for x in TRANSACTION_MODES]

CHANNELS = [
    ("Mobile App", 45),
    ("POS", 20),
    ("Internet Banking", 15),
    ("ATM", 8),
    ("Branch", 4),
    ("Auto Debit", 4),
    ("UPI App", 4),
]

CHANNEL_NAMES = [x[0] for x in CHANNELS]
CHANNEL_WEIGHTS = [x[1] for x in CHANNELS]

CITIES = [
    ("Mumbai", "Maharashtra", "India"),
    ("Pune", "Maharashtra", "India"),
    ("Delhi", "Delhi", "India"),
    ("New Delhi", "Delhi", "India"),
    ("Bengaluru", "Karnataka", "India"),
    ("Hyderabad", "Telangana", "India"),
    ("Chennai", "Tamil Nadu", "India"),
    ("Ahmedabad", "Gujarat", "India"),
    ("Surat", "Gujarat", "India"),
    ("Kolkata", "West Bengal", "India"),
    ("Jaipur", "Rajasthan", "India"),
    ("Lucknow", "Uttar Pradesh", "India"),
    ("Noida", "Uttar Pradesh", "India"),
    ("Indore", "Madhya Pradesh", "India"),
    ("Nagpur", "Maharashtra", "India"),
    ("Nashik", "Maharashtra", "India"),
    ("Kochi", "Kerala", "India"),
    ("Chandigarh", "Chandigarh", "India"),
    ("Bhopal", "Madhya Pradesh", "India"),
]

# ============================================================
# AMOUNT RANGES BY CATEGORY
# ============================================================

AMOUNT_RANGES = {

    "AIRLINES": (2500, 45000),
    "FOOD_DELIVERY": (150, 2500),
    "E_COMMERCE": (300, 40000),
    "SHOPPING": (300, 60000),
    "GROCERY": (100, 12000),
    "CAB": (80, 3000),
    "BUS": (200, 2500),
    "TRAIN": (100, 5000),
    "HOTELS": (1500, 50000),
    "MOVIES": (200, 3000),
    "FUEL": (500, 10000),
    "UTILITIES": (500, 12000),
    "ENTERTAINMENT": (99, 2500),
    "HEALTHCARE": (200, 30000),
    "EDUCATION": (500, 50000),
    "INVESTMENT": (1000, 100000),
    "SIP": (500, 50000),
    "INSURANCE": (1000, 100000),
    "BILLS": (200, 20000),
    "RESTAURANTS": (200, 8000),
    "COLLEGE_FEES": (5000, 150000),
    "RENT": (8000, 70000),
    "P2P": (500, 100000),
}

# ============================================================
# HELPERS
# ============================================================

def random_datetime():
    total_seconds = int((END_DATE - START_DATE).total_seconds())
    random_seconds = random.randint(0, total_seconds)
    return START_DATE + timedelta(seconds=random_seconds)


def weighted_choice(names, weights):
    return random.choices(names, weights=weights, k=1)[0]


def random_amount(category):
    low, high = AMOUNT_RANGES[category]

    # Bias toward smaller transactions
    value = random.triangular(low, high, low)

    # Round to realistic amount
    if value < 1000:
        return round(value / 10) * 10
    elif value < 10000:
        return round(value / 50) * 50
    else:
        return round(value / 100) * 100


def generate_reference():
    return "REF" + uuid.uuid4().hex[:14].upper()


def generate_receiver_identifier(category, merchant_id):
    if category in [
        "AIRLINES",
        "FOOD_DELIVERY",
        "E_COMMERCE",
        "SHOPPING",
        "GROCERY",
        "CAB",
        "BUS",
        "TRAIN",
        "HOTELS",
        "MOVIES",
        "FUEL",
        "UTILITIES",
        "ENTERTAINMENT",
        "HEALTHCARE",
        "EDUCATION",
        "INVESTMENT",
        "SIP",
        "INSURANCE",
        "BILLS",
        "RESTAURANTS",
        "COLLEGE_FEES",
        "RENT",
    ]:
        return f"merchant{merchant_id[-4:]}@upi"

    return f"UPI{random.randint(100000, 999999)}@upi"


def generate_description(
    category,
    merchant_name,
    transaction_mode,
    reference
):
    if transaction_mode == "UPI":
        return f"UPI/{merchant_name.upper()}/{reference}"

    if transaction_mode == "Credit Card":
        return f"CC PURCHASE {merchant_name.upper()}"

    if transaction_mode == "Debit Card":
        return f"POS/{merchant_name.upper()}"

    if transaction_mode == "NEFT":
        return f"NEFT/{merchant_name.upper()}/{reference}"

    if transaction_mode == "IMPS":
        return f"IMPS/{merchant_name.upper()}/{reference}"

    if transaction_mode == "RTGS":
        return f"RTGS/{merchant_name.upper()}/{reference}"

    if transaction_mode == "ATM":
        return "ATM CASH WITHDRAWAL"

    if transaction_mode == "Cash":
        return "CASH TRANSACTION"

    if transaction_mode == "Cheque":
        return f"CHEQUE/{reference}"

    if transaction_mode == "Auto Debit":
        return f"AUTO DEBIT/{merchant_name.upper()}"

    return f"{transaction_mode}/{merchant_name.upper()}"


# ============================================================
# GENERATE TRANSACTIONS
# ============================================================

transactions = []

# Salary transactions happen separately
salary_transactions = []

for customer_id in CUSTOMER_IDS:

    # 6-12 salary credits for most customers
    if random.random() < 0.90:

        number_of_salary_credits = random.randint(8, 12)

        for month_index in range(number_of_salary_credits):

            salary_date = END_DATE - timedelta(
                days=random.randint(
                    0,
                    30 * (month_index + 1)
                )
            )

            salary_date = salary_date.replace(
                day=random.randint(1, 7)
            )

            salary_amount = random.choice([
                30000,
                40000,
                50000,
                60000,
                75000,
                90000,
                100000,
                125000,
                150000,
                200000
            ])

            transaction_id = f"TX{len(transactions) + 1:08d}"

            salary_transactions.append({
                "transaction_id": transaction_id,
                "customer_id": customer_id,
                "account_id": ACCOUNT_IDS[customer_id],
                "card_id": "",

                "transaction_date": salary_date.strftime("%Y-%m-%d"),
                "transaction_time": "09:00:00",
                "transaction_type": "Credit",
                "transaction_mode": "NEFT",
                "amount": salary_amount,
                "currency": "INR",
                "transaction_status": "Success",

                "merchant_id": "",
                "merchant_name": "Employer",
                "receiver_name": customer_id,
                "receiver_identifier": "",
                "mcc_code": "",
                "transaction_description": "SALARY CREDIT",
                "reference_number": generate_reference(),

                "channel": "Internet Banking",
                "location_city": "",
                "location_state": "",
                "location_country": "India",
                "created_at": salary_date.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "updated_at": salary_date.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            })

# Add salary transactions
transactions.extend(salary_transactions)

# Remaining random transactions
while len(transactions) < NUM_TRANSACTIONS:

    customer_id = random.choice(CUSTOMER_IDS)

    transaction_datetime = random_datetime()

    category = weighted_choice(
        CATEGORIES,
        WEIGHTS
    )

    merchant_data = random.choice(MERCHANTS[category])
    merchant_id, merchant_name, mcc_code = merchant_data

    transaction_mode = weighted_choice(
        MODE_NAMES,
        MODE_WEIGHTS
    )

    # Keep transaction mode sensible
    if category in ["AIRLINES", "HOTELS", "MOVIES"]:
        transaction_mode = random.choice([
            "Credit Card",
            "Debit Card",
            "UPI"
        ])

    elif category in ["SIP", "INVESTMENT", "INSURANCE"]:
        transaction_mode = random.choice([
            "UPI",
            "Auto Debit",
            "NEFT"
        ])

    elif category in ["BILLS"]:
        transaction_mode = random.choice([
            "UPI",
            "Auto Debit",
            "Debit Card"
        ])

    elif category in ["TRAIN", "BUS"]:
        transaction_mode = random.choice([
            "UPI",
            "Debit Card",
            "Credit Card"
        ])

    amount = random_amount(category)

    # Most generated transactions are debits.
    transaction_type = "Debit"

    # Occasionally create credits/refunds.
    if random.random() < 0.05:

        transaction_type = "Credit"

        if category in [
            "E_COMMERCE",
            "SHOPPING",
            "FOOD_DELIVERY"
        ]:
            amount = random_amount(category)

    # Card ID only for card transactions
    card_id = ""

    if transaction_mode in [
        "Credit Card",
        "Debit Card"
    ]:
        if random.random() < CARD_USAGE_PROBABILITY:
            card_id = CARD_IDS[customer_id]

    # Channel
    channel = weighted_choice(
        CHANNEL_NAMES,
        CHANNEL_WEIGHTS
    )

    if transaction_mode == "UPI":
        channel = random.choice([
            "Mobile App",
            "UPI App"
        ])

    elif transaction_mode == "ATM":
        channel = "ATM"

    elif transaction_mode == "Cash":
        channel = "Branch"

    elif transaction_mode == "Auto Debit":
        channel = "Auto Debit"

    # Location
    city, state, country = random.choice(CITIES)

    # Reference
    reference_number = generate_reference()

    # Receiver
    receiver_name = merchant_name

    receiver_identifier = generate_receiver_identifier(
        category,
        merchant_id
    )

    # Description
    description = generate_description(
        category,
        merchant_name,
        transaction_mode,
        reference_number
    )

    # Occasional failed transaction
    if random.random() < 0.02:
        status = "Failed"

    else:
        status = "Success"

    # Very occasional reversal
    if random.random() < 0.005 and status == "Success":
        status = "Reversed"

    transaction_id = (
        f"TX{len(transactions) + 1:08d}"
    )

    transaction = {
        "transaction_id": transaction_id,

        "customer_id": customer_id,

        "account_id": ACCOUNT_IDS[customer_id],

        "card_id": card_id,

        "transaction_date":
            transaction_datetime.strftime("%Y-%m-%d"),

        "transaction_time":
            transaction_datetime.strftime("%H:%M:%S"),

        "transaction_type":
            transaction_type,

        "transaction_mode":
            transaction_mode,

        "amount":
            round(amount, 2),

        "currency":
            "INR",

        "transaction_status":
            status,

        "merchant_id":
            merchant_id,

        "merchant_name":
            merchant_name,

        "receiver_name":
            receiver_name,

        "receiver_identifier":
            receiver_identifier,

        "mcc_code":
            mcc_code,

        "transaction_description":
            description,

        "reference_number":
            reference_number,

        "channel":
            channel,

        "location_city":
            city,

        "location_state":
            state,

        "location_country":
            country,

        "created_at":
            transaction_datetime.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

        "updated_at":
            transaction_datetime.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
    }

    transactions.append(transaction)

# ============================================================
# SORT BY DATE/TIME
# ============================================================

transactions.sort(
    key=lambda x: (
        x["transaction_date"],
        x["transaction_time"]
    )
)

# ============================================================
# WRITE CSV
# ============================================================

FIELDNAMES = [
    "transaction_id",
    "customer_id",
    "account_id",
    "card_id",

    "transaction_date",
    "transaction_time",
    "transaction_type",
    "transaction_mode",
    "amount",
    "currency",
    "transaction_status",

    "merchant_id",
    "merchant_name",
    "receiver_name",
    "receiver_identifier",
    "mcc_code",
    "transaction_description",
    "reference_number",

    "channel",
    "location_city",
    "location_state",
    "location_country",

    "created_at",
    "updated_at",
]

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
    writer.writerows(transactions)

# ============================================================
# SUMMARY
# ============================================================

print("=" * 60)
print("RAW TRANSACTION DATA GENERATED")
print("=" * 60)

print(f"Transactions : {len(transactions):,}")
print(f"Customers    : {NUM_CUSTOMERS:,}")
print(f"Date range   : {START_DATE.date()} to {END_DATE.date()}")
print(f"Output       : {OUTPUT_FILE}")

print("\nTransaction mode distribution:")
mode_counts = {}

for t in transactions:
    mode = t["transaction_mode"]
    mode_counts[mode] = mode_counts.get(mode, 0) + 1

for mode, count in sorted(
    mode_counts.items(),
    key=lambda x: x[1],
    reverse=True
):
    print(f"{mode:20s}: {count}")

print("\nMerchant/category distribution:")

category_lookup = {}

for category, merchants in MERCHANTS.items():

    for merchant in merchants:

        merchant_id = merchant[0]

        category_lookup[merchant_id] = category

category_counts = {}

for t in transactions:

    merchant_id = t["merchant_id"]

    if merchant_id in category_lookup:

        category = category_lookup[merchant_id]

    elif merchant_id == "":
        category = "Salary"

    else:
        category = "Other"

    category_counts[category] = (
        category_counts.get(category, 0) + 1
    )

for category, count in sorted(
    category_counts.items(),
    key=lambda x: x[1],
    reverse=True
):
    print(f"{category:20s}: {count}")

print("=" * 60)