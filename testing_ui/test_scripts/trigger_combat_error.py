#!/usr/bin/env python3
"""
Trigger the combat error and see the actual traceback
"""

import requests
import json
import time

BASE_URL = "http://localhost:8085"

headers = {
    "Content-Type": "application/json",
    "X-Test-Bypass-Auth": "true",
    "X-Test-User-ID": "error-test"
}

print("Waiting for server...")
time.sleep(3)

# Create campaign
print("\n1. Creating campaign...")
resp = requests.post(
    f"{BASE_URL}/api/campaigns",
    headers=headers,
    json={
        "title": "Error Test",
        "prompt": "A warrior battles a dragon",
        "selectedPrompts": ["narrative", "mechanics"]
    }
)

if resp.status_code == 201:
    campaign_id = resp.json().get("campaignId")
    print(f"✅ Campaign created: {campaign_id}")
    
    # Try combat to trigger error
    print("\n2. Triggering combat...")
    combat_resp = requests.post(
        f"{BASE_URL}/api/campaigns/{campaign_id}/interaction",
        headers=headers,
        json={
            "input": "I attack the dragon with my sword!",
            "mode": "character"
        }
    )
    
    print(f"\nStatus: {combat_resp.status_code}")
    
    if combat_resp.status_code == 500:
        try:
            error_data = combat_resp.json()
            print("\n🔍 ERROR DETAILS:")
            print(json.dumps(error_data, indent=2))
            
            if "traceback" in error_data:
                print("\n📍 KEY ERROR LINES:")
                for line in error_data["traceback"].split("\n"):
                    if any(word in line for word in ["AttributeError", ".items()", "NPCs", "game_state"]):
                        print(f"  → {line}")
        except:
            print("HTML error response (not JSON)")
else:
    print(f"❌ Campaign creation failed: {resp.status_code}")
    print(resp.text[:500])