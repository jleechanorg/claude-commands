#!/usr/bin/env python3
"""Check the 500 error details"""

import requests
import json

BASE_URL = "http://localhost:8083"
CAMPAIGN_ID = "rIvZHVZGFHUVcCG6tZsn"  # From previous test

headers = {
    "Content-Type": "application/json",
    "X-Test-Bypass-Auth": "true",
    "X-Test-User-ID": "complete-test"
}

print("Checking 500 error details...")

resp = requests.post(
    f"{BASE_URL}/api/campaigns/{CAMPAIGN_ID}/interaction",
    headers=headers,
    json={
        "input": "I cast a spell at the enemy!",
        "mode": "character"
    }
)

print(f"\nStatus: {resp.status_code}")
print(f"Headers: {dict(resp.headers)}")
print(f"\nResponse text (first 1000 chars):")
print(resp.text[:1000])

# Try to parse as JSON
try:
    data = resp.json()
    print("\n\nParsed as JSON:")
    print(json.dumps(data, indent=2)[:2000])
except:
    print("\n\nCould not parse as JSON - likely HTML error page")