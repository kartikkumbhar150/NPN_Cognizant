import requests

BASE = "http://localhost:8000"

# Login
resp = requests.post(f"{BASE}/auth/login", data={"username": "employee@npnbank.com", "password": "npnbank@2024"})
data = resp.json()
token = data.get("access_token")
if not token:
    print("Login failed:", resp.text)
    exit(1)
print("Logged in as:", data.get("employee_name"))

headers = {"Authorization": f"Bearer {token}"}

# 1. Test NBO customers endpoint
print("\n--- NBO Customers (Travel Credit Card) ---")
r = requests.get(f"{BASE}/api/campaigns/Travel%20Credit%20Card/customers?limit=3", headers=headers)
if r.ok:
    d = r.json()
    print(f"  count={d['count']}, segment={d['segment']}")
    for c in d["customers"][:3]:
        print(f"  {c['customer_id']} {c['first_name']} {c['last_name']} age={c['age']} propensity={c['propensity']}%")
else:
    print("  ERROR:", r.text[:300])

# 2. Test personalised message
print("\n--- Personalised Message (CUST00001, email, auto) ---")
r = requests.post(f"{BASE}/api/campaigns/generate-personalised-message", headers=headers, json={
    "customer_id": "CUST00001",
    "product": "Travel Credit Card",
    "channel": "email",
    "age_group": "auto",
})
if r.ok:
    d = r.json()
    print(f"  customer={d['customer_name']} age={d['age']} age_group={d['age_group']}")
    print(f"  subject: {d['subject']}")
    print(f"  strategy: {d['strategy_used']}")
    print(f"  preview: {d['preview_text']}")
else:
    print("  ERROR:", r.text[:300])

# 3. Create a test campaign and get analytics
print("\n--- Create Campaign & Analytics ---")
r = requests.post(f"{BASE}/api/campaigns", headers=headers, json={
    "customer_id": "CUST00001",
    "customer_name": "Test Customer",
    "product": "Travel Credit Card",
    "campaign_name": "Test Campaign",
    "description": "Test",
    "channel": "Email",
    "message_preview": "Test preview",
    "customer_ids": ["CUST00001", "CUST00002", "CUST00003"],
    "age_group_strategy": "auto",
})
if r.ok:
    cmp = r.json()
    cid = cmp["id"]
    print(f"  Created campaign: {cid}, audience={cmp['audience_count']}")
    # Get analytics
    r2 = requests.get(f"{BASE}/api/campaigns/{cid}/analytics", headers=headers)
    if r2.ok:
        a = r2.json()
        print(f"  Analytics: sent={a['metrics']['sent']} opened={a['metrics']['opened']} conv_rate={a['rates']['overall_conv']}%")
    else:
        print("  Analytics ERROR:", r2.text[:200])
else:
    print("  ERROR:", r.text[:300])

# 4. Test AI insights
print("\n--- AI Insights ---")
r = requests.get(f"{BASE}/api/campaigns/insights", headers=headers)
if r.ok:
    d = r.json()
    print(f"  overall_health: {d['overall_health']}")
    print(f"  top_rec: {d['top_recommendation']}")
    print(f"  insights count: {len(d.get('insights', []))}")
else:
    print("  ERROR:", r.text[:200])

print("\nAll tests complete!")
