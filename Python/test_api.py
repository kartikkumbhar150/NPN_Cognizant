import requests

url = "http://localhost:8000"

# 1. Login
resp = requests.post(
    f"{url}/auth/login",
    data={"username": "employee@npnbank.com", "password": "npnbank@2024"}
)
if resp.status_code != 200:
    print(f"Login failed: {resp.text}")
    exit(1)

token = resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 2. test dashboard stats
print("Testing dashboard stats...")
r = requests.get(f"{url}/api/dashboard/stats", headers=headers)
print(f"Dashboard Stats: {r.status_code}")
if r.status_code != 200:
    print(r.text)

# 3. test segments
print("Testing segments...")
r = requests.get(f"{url}/api/segments", headers=headers)
print(f"Segments: {r.status_code}")
if r.status_code != 200:
    print(r.text)

# 4. test customers
print("Testing customers...")
r = requests.get(f"{url}/api/customers?limit=6", headers=headers)
print(f"Customers: {r.status_code}")
if r.status_code != 200:
    print(r.text)
