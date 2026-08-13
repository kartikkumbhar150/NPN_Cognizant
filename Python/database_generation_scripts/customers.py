import csv
import random
from datetime import date, timedelta

# ============================================================
# CONFIGURATION
# ============================================================

NUM_CUSTOMERS = 300
OUTPUT_FILE = "customers.csv"

random.seed(42)  # Same output every time

# ============================================================
# LARGE NAME DATASET
# ============================================================

FIRST_NAMES_MALE = [
    "Aarav", "Aaryan", "Abhay", "Abhinav", "Abhishek", "Adarsh",
    "Aditya", "Advaith", "Agastya", "Ajay", "Akash", "Akshay",
    "Alok", "Aman", "Amar", "Amit", "Anand", "Aniket",
    "Anil", "Anirudh", "Ankit", "Anmol", "Ansh", "Anshul",
    "Arjun", "Armaan", "Arnav", "Arun", "Aryan", "Ashish",
    "Ashok", "Atharv", "Avinash", "Ayush", "Bharat", "Bhavesh",
    "Chaitanya", "Chetan", "Chirag", "Daksh", "Darshan", "Deepak",
    "Dev", "Devaansh", "Dhruv", "Dinesh", "Divyansh", "Eshan",
    "Gaurav", "Girish", "Harish", "Harsh", "Harshad", "Himanshu",
    "Hrithik", "Ishaan", "Jai", "Jay", "Jayesh", "Karan",
    "Kartik", "Kartikeya", "Keshav", "Krishna", "Kunal", "Lakshya",
    "Manav", "Manish", "Mayank", "Mihir", "Mohit", "Nakul",
    "Naman", "Naveen", "Neel", "Nikhil", "Nirav", "Nitin",
    "Om", "Parth", "Pranav", "Pratik", "Rahul", "Raj",
    "Rajat", "Rajesh", "Rajiv", "Rakesh", "Rohan", "Rohit",
    "Sachin", "Sagar", "Sahil", "Sameer", "Sanjay", "Sanket",
    "Sarthak", "Shashank", "Shivam", "Shrey", "Siddharth", "Soham",
    "Sourabh", "Srinivas", "Sumit", "Suraj", "Tanay", "Tanish",
    "Tarun", "Tejas", "Uday", "Utkarsh", "Vaibhav", "Varun",
    "Ved", "Veer", "Vicky", "Vijay", "Vikas", "Vikram",
    "Vinay", "Vishal", "Vivek", "Yash", "Yashwant", "Yuvraj"
]

FIRST_NAMES_FEMALE = [
    "Aadhya", "Aakanksha", "Aaliya", "Aaradhya", "Aastha", "Aditi",
    "Akanksha", "Alisha", "Amrita", "Ananya", "Anika", "Anjali",
    "Ankita", "Anushka", "Anvi", "Aparna", "Aradhana", "Avani",
    "Avantika", "Bhavana", "Bhumika", "Charita", "Charvi", "Deepa",
    "Deepika", "Deepti", "Diya", "Esha", "Garima", "Gauri",
    "Gayatri", "Geetanjali", "Harini", "Ira", "Isha", "Ishita",
    "Jahnavi", "Janhvi", "Jiya", "Kajal", "Kalpana", "Kanchan",
    "Kareena", "Kavita", "Kavya", "Khushi", "Kirti", "Komal",
    "Krisha", "Lakshmi", "Lavanya", "Madhuri", "Mahima", "Mahi",
    "Manisha", "Meera", "Megha", "Mihika", "Mitali", "Manya",
    "Muskan", "Naina", "Namrata", "Neha", "Nidhi", "Nikita",
    "Nisha", "Nishita", "Palak", "Pallavi", "Pooja", "Prachi",
    "Pragya", "Pranita", "Priya", "Radhika", "Ragini", "Rashi",
    "Rashmi", "Reema", "Rekha", "Rhea", "Riddhi", "Riya",
    "Roshni", "Sakshi", "Saloni", "Sana", "Sandhya", "Sanjana",
    "Sapna", "Sarika", "Shalini", "Shanaya", "Sharanya", "Shreya",
    "Shruti", "Simran", "Sneha", "Sonali", "Sonia", "Sonal",
    "Suhani", "Swati", "Tanisha", "Tanya", "Trisha", "Vaishnavi",
    "Vandana", "Varsha", "Vidhi", "Vineeta", "Yamini", "Zoya"
]

LAST_NAMES = [
    "Agarwal", "Ahire", "Bansal", "Bhat", "Bhatia", "Bhosale",
    "Bhatt", "Chakraborty", "Chaudhary", "Chavan", "Chopra",
    "Das", "Desai", "Deshmukh", "Dhawan", "Dixit", "Dubey",
    "Gandhi", "Garg", "Ghosh", "Goel", "Gokhale", "Goswami",
    "Gupta", "Iyer", "Jadhav", "Jain", "Joshi", "Kale",
    "Kapoor", "Karnik", "Kaur", "Kulkarni", "Kumar", "Mahajan",
    "Malhotra", "Mane", "Mehta", "Menon", "Mishra", "Modi",
    "More", "Naik", "Nair", "Narayan", "Nayak", "Patel",
    "Patil", "Pawar", "Pillai", "Pradhan", "Rao", "Rane",
    "Rathod", "Roy", "Saha", "Saini", "Salunke", "Sarkar",
    "Shah", "Sharma", "Shetty", "Shinde", "Singh", "Sinha",
    "Solanki", "Soman", "Sonawane", "Srivastava", "Subramanian",
    "Suresh", "Tiwari", "Trivedi", "Tripathi", "Upadhyay",
    "Vaidya", "Varma", "Verma", "Wagh", "Yadav"
]

# ============================================================
# CITIES
# ============================================================

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
    ("Dehradun", "Uttarakhand", "248001")
]

# ============================================================
# OCCUPATIONS
# ============================================================

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
    ("Retired Professional", "Retired")
]

# ============================================================
# EMPLOYERS
# ============================================================

EMPLOYERS = [
    "TCS",
    "Infosys",
    "Wipro",
    "HCLTech",
    "Accenture",
    "IBM India",
    "Cognizant",
    "Capgemini",
    "Tech Mahindra",
    "Deloitte",
    "EY India",
    "KPMG India",
    "PwC India",
    "Amazon India",
    "Microsoft India",
    "Google India",
    "Flipkart",
    "Reliance Industries",
    "Tata Motors",
    "Mahindra & Mahindra",
    "Bajaj Finserv",
    "ICICI Bank",
    "Axis Bank",
    "HDFC Bank",
    "Larsen & Toubro",
    "Aditya Birla Group",
    "State Government",
    "Central Government",
    "Self Employed",
    "Independent Consultant",
    "Family Business",
    "Startup",
    "Private Company"
]

# ============================================================
# EDUCATION
# ============================================================

EDUCATION_LEVELS = [
    "Higher Secondary",
    "Diploma",
    "Graduate",
    "Postgraduate",
    "Doctorate"
]

# ============================================================
# LANGUAGES
# ============================================================

LANGUAGES = [
    "English",
    "Hindi",
    "Marathi",
    "Gujarati",
    "Tamil",
    "Telugu",
    "Kannada",
    "Bengali",
    "Malayalam",
    "Punjabi",
    "Odia"
]

# ============================================================
# OTHER MASTER DATA
# ============================================================

MARITAL_STATUS = [
    "Single",
    "Married",
    "Divorced",
    "Widowed"
]

CUSTOMER_TYPES = [
    "Retail",
    "Retail",
    "Retail",
    "Premium",
    "Premium",
    "Business"
]

CUSTOMER_STATUS = [
    "Active",
    "Active",
    "Active",
    "Active",
    "Active",
    "Dormant"
]

KYC_STATUS = [
    "Verified",
    "Verified",
    "Verified",
    "Verified",
    "Pending"
]

RISK_PROFILES = [
    "Low",
    "Low",
    "Moderate",
    "Moderate",
    "Moderate",
    "High"
]

CHANNELS = [
    "Mobile App",
    "NetBanking",
    "Mobile App",
    "Mobile App",
    "Email",
    "SMS",
    "Branch"
]

# ============================================================
# HELPERS
# ============================================================

def random_date(start_date, end_date):
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    return start_date + timedelta(days=random_days)


def generate_phone():
    return "9" + "".join(str(random.randint(0, 9)) for _ in range(9))


def generate_email(first_name, last_name, index):
    domains = [
        "example.com",
        "mail.com",
        "demo.in",
        "sample.com"
    ]

    return (
        f"{first_name.lower()}.{last_name.lower()}"
        f"{index}@{random.choice(domains)}"
    )


def get_income(occupation_type, age):
    if occupation_type == "Student":
        return random.randint(0, 300000)

    if occupation_type == "Retired":
        return random.randint(300000, 1200000)

    if occupation_type == "Business":
        return random.randint(600000, 8000000)

    if occupation_type == "Self-employed":
        return random.randint(500000, 5000000)

    # Salaried
    if age < 25:
        return random.randint(300000, 700000)

    elif age < 35:
        return random.randint(500000, 1800000)

    elif age < 50:
        return random.randint(700000, 3500000)

    else:
        return random.randint(900000, 5000000)


def get_income_range(income):
    if income < 300000:
        return "0-3L"
    elif income < 500000:
        return "3-5L"
    elif income < 1000000:
        return "5-10L"
    elif income < 2000000:
        return "10-20L"
    elif income < 5000000:
        return "20-50L"
    else:
        return "50L+"


# ============================================================
# GENERATE CUSTOMERS
# ============================================================

customers = []

# Very strong preference toward Resident customers
# ~99% Resident, ~1% NRI
residential_status_pool = [
    "Resident"
] * 99 + [
    "NRI"
]

today = date.today()

for i in range(1, NUM_CUSTOMERS + 1):

    customer_id = f"CUST{i:05d}"
    customer_number = f"CIF{i:08d}"

    gender = random.choice(["Male", "Female"])

    if gender == "Male":
        first_name = random.choice(FIRST_NAMES_MALE)
    else:
        first_name = random.choice(FIRST_NAMES_FEMALE)

    last_name = random.choice(LAST_NAMES)

    age = random.randint(18, 70)

    birth_year = today.year - age

    dob = date(
        birth_year,
        random.randint(1, 12),
        random.randint(1, 28)
    )

    city, state, pincode = random.choice(CITIES)

    occupation, employment_type = random.choice(OCCUPATIONS)

    annual_income = get_income(employment_type, age)

    income_range = get_income_range(annual_income)

    # Higher chance of married status for older customers
    if age < 25:
        marital_status = random.choice([
            "Single",
            "Single",
            "Single",
            "Married"
        ])
    elif age < 35:
        marital_status = random.choice([
            "Single",
            "Married",
            "Married",
            "Married"
        ])
    else:
        marital_status = random.choice([
            "Married",
            "Married",
            "Married",
            "Divorced",
            "Widowed"
        ])

    # Relationship start date
    customer_since = random_date(
        date(2017, 1, 1),
        date(2025, 12, 31)
    )

    # NRI is very rare
    residential_status = random.choice(residential_status_pool)

    # NRI customers are more likely to have higher income
    if residential_status == "NRI":
        annual_income = random.randint(1500000, 8000000)
        income_range = get_income_range(annual_income)

    # Students generally have lower income
    if employment_type == "Student":
        employer_name = "College / University"
    elif employment_type == "Business":
        employer_name = random.choice([
            "Family Business",
            "Independent Business",
            "Self Employed",
            "Retail Business",
            "Startup",
            "Restaurant Business"
        ])
    elif employment_type == "Retired":
        employer_name = "Retired"
    else:
        employer_name = random.choice(EMPLOYERS)

    customer = {
        "customer_id": customer_id,
        "customer_number": customer_number,

        "first_name": first_name,
        "middle_name": "",
        "last_name": last_name,

        "date_of_birth": dob.isoformat(),
        "age": age,
        "gender": gender,
        "marital_status": marital_status,

        "nationality": "Indian",
        "residential_status": residential_status,

        "occupation_type": employment_type,
        "occupation": occupation,
        "employer_name": employer_name,
        "employment_type": employment_type,

        "annual_income": annual_income,
        "income_range": income_range,

        "education_level": random.choice(EDUCATION_LEVELS),

        "address_line_1":
            f"{random.randint(1, 999)} "
            f"{random.choice(['MG Road', 'Station Road', 'Main Street', 'Park Road', 'Market Road'])}",

        "address_line_2":
            f"Apartment {random.randint(1, 500)}",

        "city": city,
        "state": state,
        "country": "India",
        "pincode": pincode,

        "mobile_number": generate_phone(),
        "email": generate_email(first_name, last_name, i),

        "customer_since": customer_since.isoformat(),

        "customer_segment_type":
            random.choice(CUSTOMER_TYPES),

        "customer_status":
            random.choice(CUSTOMER_STATUS),

        "kyc_status":
            random.choice(KYC_STATUS),

        "kyc_last_updated":
            random_date(
                date(2024, 1, 1),
                date(2026, 8, 1)
            ).isoformat(),

        "risk_profile":
            random.choice(RISK_PROFILES),

        "credit_score":
            random.randint(650, 850),

        "branch_id":
            f"BR{random.randint(1, 30):03d}",

        "relationship_manager_id":
            f"RM{random.randint(1, 50):03d}",

        "preferred_language":
            random.choice(LANGUAGES),

        "preferred_channel":
            random.choice(CHANNELS),

        "marketing_consent":
            random.choice([
                "Yes",
                "Yes",
                "Yes",
                "Yes",
                "No"
            ])
    }

    customers.append(customer)


# ============================================================
# SAVE TO CSV
# ============================================================

fieldnames = list(customers[0].keys())

with open(
    OUTPUT_FILE,
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames
    )

    writer.writeheader()
    writer.writerows(customers)


# ============================================================
# SUMMARY
# ============================================================

resident_count = sum(
    1 for c in customers
    if c["residential_status"] == "Resident"
)

nri_count = NUM_CUSTOMERS - resident_count

print("=" * 50)
print("CUSTOMER DATA GENERATED")
print("=" * 50)
print(f"Total customers : {NUM_CUSTOMERS}")
print(f"Resident        : {resident_count}")
print(f"NRI             : {nri_count}")
print(f"Output file     : {OUTPUT_FILE}")
print("=" * 50)