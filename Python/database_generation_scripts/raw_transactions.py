


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
# REAL PAYMENT / MONEY-FLOW RULES
# ============================================================
#
# Important business rule:
#   A merchant does NOT randomly credit a customer's bank account.
#
# Examples:
#   Customer -> Insurance company     = DEBIT
#   Customer -> Amazon                = DEBIT
#   Employer -> Employee              = CREDIT
#   Friend -> Customer                = CREDIT
#   Merchant -> Customer (refund)    = CREDIT
#   Customer -> Friend                = DEBIT
#   ATM withdrawal                    = DEBIT
#   Cash deposit at branch            = CREDIT
#
# We therefore generate INCOMING and OUTGOING transactions separately.
# =====================================================================

MERCHANT_PAYMENT_CATEGORIES = {
    "AIRLINES", "FOOD_DELIVERY", "E_COMMERCE", "SHOPPING", "GROCERY",
    "CAB", "BUS", "TRAIN", "HOTELS", "MOVIES", "FUEL", "UTILITIES",
    "ENTERTAINMENT", "HEALTHCARE", "EDUCATION", "INVESTMENT", "SIP",
    "INSURANCE", "BILLS", "RESTAURANTS", "COLLEGE_FEES", "RENT"
}

# These are genuine sources of money entering a customer's account.
INCOMING_TYPES = [
    ("SALARY", 45),
    ("P2P_RECEIPT", 22),
    ("REFUND", 12),
    ("CASH_DEPOSIT", 6),
    ("INTEREST", 4),
    ("CASHBACK", 3),
    ("REVERSAL", 2),
    ("OTHER_BANK_TRANSFER", 6),
]

INCOMING_TYPE_NAMES = [x[0] for x in INCOMING_TYPES]
INCOMING_TYPE_WEIGHTS = [x[1] for x in INCOMING_TYPES]

# Customer -> merchant / person / account.
OUTGOING_TYPES = [
    ("MERCHANT_PAYMENT", 78),
    ("P2P_TRANSFER", 10),
    ("BILL_PAYMENT", 4),
    ("ATM_WITHDRAWAL", 4),
    ("CASH_WITHDRAWAL", 2),
    ("BANK_TRANSFER", 2),
]

OUTGOING_TYPE_NAMES = [x[0] for x in OUTGOING_TYPES]
OUTGOING_TYPE_WEIGHTS = [x[1] for x in OUTGOING_TYPES]

# Estimated cash opening balance for each customer.
# This allows us to enforce: no successful debit > available balance.
ACCOUNT_BALANCE = {
    customer_id: random.randint(20_000, 200_000)
    for customer_id in CUSTOMER_IDS
}

# Some customers receive a salary; salary is always an incoming bank credit.
# The source is the employer, not a merchant purchase.
EMPLOYERS = [
    ("EMP0001", "TCS"),
    ("EMP0002", "Infosys"),
    ("EMP0003", "HDFC Bank"),
    ("EMP0004", "ICICI Bank"),
    ("EMP0005", "Accenture"),
    ("EMP0006", "Deloitte"),
    ("EMP0007", "Capgemini"),
    ("EMP0008", "Wipro"),
    ("EMP0009", "Tech Mahindra"),
    ("EMP0010", "Reliance Industries"),
]

P2P_SENDERS = [
    ("P2P001", "Rahul"),
    ("P2P002", "Priya"),
    ("P2P003", "Amit"),
    ("P2P004", "Neha"),
    ("P2P005", "Family"),
]

REFUND_REASONS = [
    "ORDER REFUND",
    "CANCELLED TICKET REFUND",
    "MERCHANT REFUND",
    "CARD PURCHASE REFUND",
    "EXCESS PAYMENT REFUND",
]

def random_incoming_amount(incoming_type):
    """Generate realistic amounts for genuine credit events."""
    ranges = {
        "SALARY": (30_000, 2_00_000),
        "P2P_RECEIPT": (500, 50_000),
        "REFUND": (200, 25_000),
        "CASH_DEPOSIT": (1_000, 75_000),
        "INTEREST": (10, 5_000),
        "CASHBACK": (50, 5_000),
        "REVERSAL": (100, 20_000),
        "OTHER_BANK_TRANSFER": (1_000, 1_00_000),
    }

    low, high = ranges[incoming_type]
    value = random.triangular(low, high, low)

    if value < 1000:
        return round(value / 10) * 10
    elif value < 10000:
        return round(value / 50) * 50
    return round(value / 100) * 100


def random_outgoing_amount(category):
    """Generate a payment amount, then validate it against account balance."""
    low, high = AMOUNT_RANGES[category]
    value = random.triangular(low, high, low)

    if value < 1000:
        return round(value / 10) * 10
    elif value < 10000:
        return round(value / 50) * 50
    return round(value / 100) * 100


def choose_payment_mode(category, outgoing_type):
    """Choose a payment rail that makes sense for the business event."""
    if outgoing_type == "ATM_WITHDRAWAL":
        return "ATM"

    if outgoing_type == "CASH_WITHDRAWAL":
        return "Cash"

    if outgoing_type == "P2P_TRANSFER":
        return random.choice(["UPI", "IMPS", "NEFT"])

    if outgoing_type in {"BANK_TRANSFER", "BILL_PAYMENT"}:
        return random.choice(["UPI", "NEFT", "IMPS", "Auto Debit"])

    if category in ["AIRLINES", "HOTELS", "MOVIES", "SHOPPING", "E_COMMERCE"]:
        return random.choice(["UPI", "Debit Card", "Credit Card"])

    if category in ["SIP", "INVESTMENT", "INSURANCE"]:
        return random.choice(["UPI", "Auto Debit", "NEFT"])

    if category == "BILLS":
        return random.choice(["UPI", "Auto Debit", "Debit Card"])

    return weighted_choice(MODE_NAMES, MODE_WEIGHTS)


def build_money_flow_fields(
    transaction_type,
    incoming_type=None,
    outgoing_type=None,
    merchant_id="",
    merchant_name="",
    category=None
):
    """
    Return source/destination fields.

    For merchant purchases:
        source = CUSTOMER ACCOUNT
        destination = MERCHANT

    For salary:
        source = EMPLOYER
        destination = CUSTOMER ACCOUNT

    For P2P receipt:
        source = OTHER PERSON
        destination = CUSTOMER ACCOUNT
    """
    fields = {
        "sender_name": "",
        "sender_identifier": "",
        "receiver_name": "",
        "receiver_identifier": "",
        "counterparty_type": "",
        "fund_flow": "",
    }

    if transaction_type == "Credit":
        fields["fund_flow"] = "INCOMING"

        if incoming_type == "SALARY":
            employer_id, employer_name = random.choice(EMPLOYERS)
            fields["sender_name"] = employer_name
            fields["sender_identifier"] = employer_id
            fields["receiver_name"] = "CUSTOMER ACCOUNT"
            fields["counterparty_type"] = "EMPLOYER"

        elif incoming_type == "P2P_RECEIPT":
            sender_id, sender_name = random.choice(P2P_SENDERS)
            fields["sender_name"] = sender_name
            fields["sender_identifier"] = sender_id
            fields["receiver_name"] = "CUSTOMER ACCOUNT"
            fields["counterparty_type"] = "P2P"

        elif incoming_type in {"REFUND", "CASHBACK", "REVERSAL"}:
            fields["sender_name"] = merchant_name or "Merchant"
            fields["sender_identifier"] = merchant_id
            fields["receiver_name"] = "CUSTOMER ACCOUNT"
            fields["counterparty_type"] = (
                "MERCHANT" if incoming_type != "REVERSAL" else "BANK"
            )

        elif incoming_type == "CASH_DEPOSIT":
            fields["sender_name"] = "CUSTOMER"
            fields["sender_identifier"] = ""
            fields["receiver_name"] = "CUSTOMER ACCOUNT"
            fields["counterparty_type"] = "SELF"

        elif incoming_type == "INTEREST":
            fields["sender_name"] = "BANK"
            fields["sender_identifier"] = "BANK-INTEREST"
            fields["receiver_name"] = "CUSTOMER ACCOUNT"
            fields["counterparty_type"] = "BANK"

        else:
            fields["sender_name"] = "OTHER BANK ACCOUNT"
            fields["sender_identifier"] = "BANK-TRANSFER"
            fields["receiver_name"] = "CUSTOMER ACCOUNT"
            fields["counterparty_type"] = "BANK"

    else:
        fields["fund_flow"] = "OUTGOING"

        if outgoing_type == "P2P_TRANSFER":
            receiver_id, receiver_name = random.choice(P2P_SENDERS)
            fields["sender_name"] = "CUSTOMER"
            fields["sender_identifier"] = ""
            fields["receiver_name"] = receiver_name
            fields["receiver_identifier"] = receiver_id
            fields["counterparty_type"] = "P2P"

        elif merchant_name:
            fields["sender_name"] = "CUSTOMER ACCOUNT"
            fields["sender_identifier"] = ""
            fields["receiver_name"] = merchant_name
            fields["receiver_identifier"] = (
                f"merchant{merchant_id[-4:]}@upi"
                if merchant_id else ""
            )
            fields["counterparty_type"] = "MERCHANT"

        elif outgoing_type == "BANK_TRANSFER":
            fields["sender_name"] = "CUSTOMER"
            fields["receiver_name"] = "OTHER BANK ACCOUNT"
            fields["receiver_identifier"] = "BANK-TRANSFER"
            fields["counterparty_type"] = "BANK"

        else:
            fields["sender_name"] = "CUSTOMER ACCOUNT"
            fields["receiver_name"] = "CASH / ATM"
            fields["counterparty_type"] = "SELF"

    return fields


# ============================================================
# GENERATE TRANSACTIONS
# ============================================================

transactions = []

for customer_id in CUSTOMER_IDS:

    # --------------------------------------------------------
    # 1. MONTHLY SALARY CREDITS
    # --------------------------------------------------------
    # Salary is never generated as a "merchant payment".
    # Employer is the actual sender of funds.
    # --------------------------------------------------------
    if random.random() < 0.90:

        salary_months = random.randint(8, 12)

        for month_index in range(salary_months):
            salary_date = END_DATE - timedelta(days=30 * (month_index + 1))
            salary_date = salary_date.replace(day=random.randint(1, 7))

            employer_id, employer_name = random.choice(EMPLOYERS)
            salary_amount = random.choice([
                30_000, 40_000, 50_000, 60_000,
                75_000, 90_000, 1_00_000,
                1_25_000, 1_50_000, 2_00_000
            ])

            transaction_id = f"TX{len(transactions) + 1:08d}"
            reference_number = generate_reference()

            transactions.append({
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
                "merchant_name": "",
                "receiver_name": "CUSTOMER ACCOUNT",
                "receiver_identifier": "",
                "mcc_code": "",
                "transaction_description": f"SALARY CREDIT/{employer_name.upper()}",
                "reference_number": reference_number,

                "channel": "Internet Banking",
                "location_city": "",
                "location_state": "",
                "location_country": "India",

                "sender_name": employer_name,
                "sender_identifier": employer_id,
                "counterparty_type": "EMPLOYER",
                "fund_flow": "INCOMING",

                "created_at": salary_date.strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": salary_date.strftime("%Y-%m-%d %H:%M:%S"),
            })

            ACCOUNT_BALANCE[customer_id] += salary_amount

    # --------------------------------------------------------
# 2. OTHER REALISTIC TRANSACTIONS
# --------------------------------------------------------
while len(transactions) < NUM_TRANSACTIONS:

    transaction_datetime = random_datetime()

    # Use the customer whose transaction is being generated.
    # We choose an account first so balance validation is per account.
    customer_id = random.choice(CUSTOMER_IDS)
    account_id = ACCOUNT_IDS[customer_id]
    city, state, country = random.choice(CITIES)

    # ~85% outgoing payments, ~15% genuine incoming credits.
    is_incoming = random.random() < 0.15

    # ====================================================
    # INCOMING MONEY
    # ====================================================
    if is_incoming:

        incoming_type = weighted_choice(
            INCOMING_TYPE_NAMES,
            INCOMING_TYPE_WEIGHTS
        )

        # No merchant purchase category is selected for a normal credit.
        merchant_id = ""
        merchant_name = ""
        mcc_code = ""
        amount = random_incoming_amount(incoming_type)

        transaction_type = "Credit"

        # Refund / cashback / reversal must have a real merchant source.
        if incoming_type in {"REFUND", "CASHBACK", "REVERSAL"}:
            refund_category = random.choice([
                "E_COMMERCE",
                "SHOPPING",
                "FOOD_DELIVERY",
                "AIRLINES",
                "HOTELS",
                "RESTAURANTS",
                "INSURANCE",
                "BILLS",
            ])

            merchant_id, merchant_name, mcc_code = random.choice(
                MERCHANTS[refund_category]
            )

            # Refunds cannot exceed a plausible purchase amount.
            amount = min(
                amount,
                ACCOUNT_BALANCE[customer_id] * 0.50 + amount
            )

        if incoming_type == "SALARY":
            mode = "NEFT"
            channel = "Internet Banking"
            description = "SALARY CREDIT"

        elif incoming_type == "P2P_RECEIPT":
            mode = random.choice(["UPI", "IMPS", "NEFT"])
            channel = "UPI App" if mode == "UPI" else "Mobile App"
            description = "P2P RECEIPT"

        elif incoming_type == "REFUND":
            mode = random.choice(["UPI", "NEFT", "IMPS"])
            channel = "Mobile App"
            description = f"REFUND/{merchant_name.upper()}/{generate_reference()}"

        elif incoming_type == "CASH_DEPOSIT":
            mode = "Cash"
            channel = "Branch"
            description = "CASH DEPOSIT"

        elif incoming_type == "INTEREST":
            mode = "NEFT"
            channel = "Banking System"
            description = "INTEREST CREDIT"

        elif incoming_type == "CASHBACK":
            mode = "UPI"
            channel = "Mobile App"
            description = f"CASHBACK/{merchant_name.upper()}"

        elif incoming_type == "REVERSAL":
            mode = "Reversal"
            channel = "Banking System"
            description = f"PAYMENT REVERSAL/{merchant_name.upper()}"

        else:
            mode = random.choice(["NEFT", "IMPS", "RTGS"])
            channel = "Internet Banking"
            description = "BANK TRANSFER CREDIT"

        money_flow = build_money_flow_fields(
            "Credit",
            incoming_type=incoming_type,
            merchant_id=merchant_id,
            merchant_name=merchant_name
        )

    # ====================================================
    # OUTGOING MONEY
    # ====================================================
    else:

        # 90% of outgoing money is a genuine merchant purchase/bill.
        outgoing_type = weighted_choice(
            OUTGOING_TYPE_NAMES,
            OUTGOING_TYPE_WEIGHTS
        )

        # Merchant payment / bill payment
        if outgoing_type in {"MERCHANT_PAYMENT", "BILL_PAYMENT"}:

            if outgoing_type == "BILL_PAYMENT":
                category = random.choice(["BILLS", "UTILITIES"])
            else:
                category = weighted_choice(CATEGORIES, WEIGHTS)

            # Every merchant/insurance payment is an OUTGOING debit.
            transaction_type = "Debit"

            merchant_id, merchant_name, mcc_code = random.choice(
                MERCHANTS[category]
            )

            amount = random_outgoing_amount(category)

            # Never create a successful debit larger than available cash.
            available_balance = ACCOUNT_BALANCE[customer_id]

            if available_balance < amount:
                # Keep the requested category but make the amount affordable.
                low, high = AMOUNT_RANGES[category]

                if available_balance < max(100, low):
                    # The account cannot afford this payment.
                    # Replace this event with a genuine incoming event.
                    is_incoming = True
                    continue

                amount = random.uniform(
                    low,
                    min(high, available_balance)
                )

            amount = round(amount, 2)

            mode = choose_payment_mode(category, outgoing_type)

            if category == "INSURANCE":
                description = f"INSURANCE PREMIUM/{merchant_name.upper()}"
            elif category == "RENT":
                description = f"RENT PAYMENT/{merchant_name.upper()}"
            elif category in {"SIP", "INVESTMENT"}:
                description = f"{category} PAYMENT/{merchant_name.upper()}"
            else:
                reference = generate_reference()
                description = generate_description(
                    category,
                    merchant_name,
                    mode,
                    reference
                )

            channel = weighted_choice(
                CHANNEL_NAMES,
                CHANNEL_WEIGHTS
            )

            if mode == "UPI":
                channel = random.choice(["Mobile App", "UPI App"])
            elif mode == "ATM":
                channel = "ATM"
            elif mode == "Cash":
                channel = "Branch"
            elif mode == "Auto Debit":
                channel = "Auto Debit"

            money_flow = build_money_flow_fields(
                "Debit",
                outgoing_type=outgoing_type,
                merchant_id=merchant_id,
                merchant_name=merchant_name,
                category=category
            )

            # Credit-card purchase creates card liability rather than
            # immediately reducing the customer's bank cash balance.
            if mode != "Credit Card":
                ACCOUNT_BALANCE[customer_id] -= amount

        # Person-to-person transfer
        elif outgoing_type == "P2P_TRANSFER":

            category = "P2P"
            merchant_id = ""
            merchant_name = ""
            mcc_code = ""

            amount = random_amount("P2P")

            available_balance = ACCOUNT_BALANCE[customer_id]
            if available_balance < 100:
                continue

            if available_balance < amount:
                amount = round(
                    random.uniform(100, available_balance),
                    2
                )

            mode = choose_payment_mode(category, outgoing_type)
            channel = "UPI App" if mode == "UPI" else "Mobile App"

            transaction_type = "Debit"
            description = f"P2P TRANSFER/{generate_reference()}"

            money_flow = build_money_flow_fields(
                "Debit",
                outgoing_type=outgoing_type
            )

            ACCOUNT_BALANCE[customer_id] -= amount

        # Bank transfer
        elif outgoing_type == "BANK_TRANSFER":

            category = "P2P"
            merchant_id = ""
            merchant_name = ""
            mcc_code = ""

            available_balance = ACCOUNT_BALANCE[customer_id]
            if available_balance < 1_000:
                continue

            amount = random.uniform(1_000, 50_000)
            amount = round(min(amount, available_balance), 2)

            mode = random.choice(["NEFT", "IMPS", "RTGS"])
            channel = "Internet Banking"

            transaction_type = "Debit"
            description = f"BANK TRANSFER/{generate_reference()}"

            money_flow = build_money_flow_fields(
                "Debit",
                outgoing_type=outgoing_type
            )

            ACCOUNT_BALANCE[customer_id] -= amount

        # ATM withdrawal
        elif outgoing_type == "ATM_WITHDRAWAL":

            category = "CASH_WITHDRAWAL"
            merchant_id = ""
            merchant_name = ""
            mcc_code = ""

            available_balance = ACCOUNT_BALANCE[customer_id]
            if available_balance < 500:
                continue

            amount = random.choice([
                500, 1000, 2000, 3000, 5000, 10000
            ])

            amount = min(amount, available_balance)

            mode = "ATM"
            channel = "ATM"
            transaction_type = "Debit"
            description = "ATM CASH WITHDRAWAL"

            money_flow = build_money_flow_fields(
                "Debit",
                outgoing_type=outgoing_type
            )

            ACCOUNT_BALANCE[customer_id] -= amount

        # Branch cash withdrawal
        else:

            category = "CASH_WITHDRAWAL"
            merchant_id = ""
            merchant_name = ""
            mcc_code = ""

            available_balance = ACCOUNT_BALANCE[customer_id]
            if available_balance < 2_000:
                continue

            amount = random.choice([
                2_000, 5_000, 10_000, 20_000, 50_000
            ])

            amount = min(amount, available_balance)

            mode = "Cash"
            channel = "Branch"
            transaction_type = "Debit"
            description = "CASH WITHDRAWAL"

            money_flow = build_money_flow_fields(
                "Debit",
                outgoing_type=outgoing_type
            )

            ACCOUNT_BALANCE[customer_id] -= amount

    # ----------------------------------------------------
    # Status rules
    # ----------------------------------------------------
    # Failed/reversed transactions must not change the final
    # available balance.
    #
    # The balance has already been updated for successful
    # outgoing transactions, so put it back if the event fails.
    # ----------------------------------------------------
    status = "Success"

    # Keep failed events rare, but do not create impossible
    # "failed credits" that change balance.
    if random.random() < 0.02:
        status = "Failed"

    elif random.random() < 0.005:
        status = "Reversed"

    if transaction_type == "Credit":
        if status == "Success":
            ACCOUNT_BALANCE[customer_id] += amount

        # For failed/reversed incoming credits, do not add money.

    else:
        # Failed/reversed cash-account debits are rolled back.
        # Credit-card purchases never reduced the bank cash balance.
        if mode != "Credit Card":
            if status == "Failed":
                ACCOUNT_BALANCE[customer_id] += amount

            elif status == "Reversed":
                ACCOUNT_BALANCE[customer_id] += amount

    # ----------------------------------------------------
    # Card ID only for actual card payments.
    # ----------------------------------------------------
    card_id = ""
    if mode in {"Credit Card", "Debit Card"}:
        if random.random() < CARD_USAGE_PROBABILITY:
            card_id = CARD_IDS[customer_id]

    reference_number = generate_reference()

    # Merchant fields are deliberately blank for salary/P2P/
    # bank transfers/cash operations. A merchant is a payee,
    # not an arbitrary source of credit.
    receiver_name = money_flow["receiver_name"]
    receiver_identifier = money_flow["receiver_identifier"]

    transaction_id = f"TX{len(transactions) + 1:08d}"

    transactions.append({
        "transaction_id": transaction_id,

        "customer_id": customer_id,

        "account_id": account_id,

        "card_id": card_id,

        "transaction_date":
            transaction_datetime.strftime("%Y-%m-%d"),

        "transaction_time":
            transaction_datetime.strftime("%H:%M:%S"),

        "transaction_type":
            transaction_type,

        "transaction_mode":
            mode,

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
            city if 'city' in locals() else "",

        "location_state":
            state if 'state' in locals() else "",

        "location_country":
            "India",

        # New fields explaining the actual money movement.
        "sender_name":
            money_flow["sender_name"],

        "sender_identifier":
            money_flow["sender_identifier"],

        "counterparty_type":
            money_flow["counterparty_type"],

        "fund_flow":
            money_flow["fund_flow"],

        "created_at":
            transaction_datetime.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

        "updated_at":
            transaction_datetime.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
    })

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

    # Money-flow / counterparty fields
    "sender_name",
    "sender_identifier",
    "counterparty_type",
    "fund_flow",

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

print("\nMoney-flow distribution:")
flow_counts = {}
for t in transactions:
    key = t["transaction_type"] + " / " + t["counterparty_type"]
    flow_counts[key] = flow_counts.get(key, 0) + 1

for key, count in sorted(flow_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"{key:30s}: {count}")

print("=" * 60)