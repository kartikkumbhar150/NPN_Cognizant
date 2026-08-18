import requests, sys

BASE = "http://localhost:8000"

# Login
r = requests.post(f"{BASE}/auth/login", data={"username": "employee@npnbank.com", "password": "npnbank@2024"})
assert r.status_code == 200, f"Login failed: {r.text}"
token = r.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Analyze customer
r2 = requests.get(f"{BASE}/api/customers/CUST00003/analyze", headers=headers)
assert r2.status_code == 200, f"Analyze failed: {r2.status_code}"
data = r2.json()

# Check gaps
gaps = data.get("financial_analysis", {}).get("gaps", [])
gap_codes = [g["code"] for g in gaps]
print(f"Gaps ({len(gaps)}): {gap_codes}")

# Check NBO
nbo = data.get("nbo", {})
print(f"NBO: {nbo.get('category')} -> {nbo.get('specific_product')} ({nbo.get('propensity')})")

# Check marketing message
msg = data.get("genai_message", "")
print(f"\nMarketing message ({len(msg)} chars):")
# Print first 300 chars safely (no emojis to console)
safe_msg = msg.encode("ascii", errors="replace").decode("ascii")
print(safe_msg[:300])

if msg and len(msg) > 50:
    print("\nSUCCESS: Marketing message generated correctly!")
elif not nbo.get('category'):
    print("\nNo NBO for this customer, no message generated (expected).")
else:
    print("\nWARNING: Marketing message is unexpectedly short (mock fallback?)")
