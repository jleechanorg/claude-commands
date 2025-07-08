#!/usr/bin/env python3
"""
Quick debug script to see exactly what the interaction endpoint returns.
"""

import requests
import json

base_url = "http://localhost:6009"
headers = {
    'X-Test-Bypass-Auth': 'true',
    'X-Test-User-ID': 'test-user-json-bug',
    'Content-Type': 'application/json'
}

# Use the existing campaign
campaign_id = "khhT6InrIPDiPXScr1G9"

print("🔍 DEBUG: Testing interaction endpoint response...")

interaction_data = {
    "input": "I want to create a D&D character.",
    "mode": "character"
}

response = requests.post(
    f"{base_url}/api/campaigns/{campaign_id}/interaction",
    json=interaction_data,
    headers=headers,
    timeout=60
)

print(f"Status: {response.status_code}")
print(f"Headers: {dict(response.headers)}")

if response.status_code == 200:
    result = response.json()
    print(f"\nResponse keys: {list(result.keys())}")
    
    ai_response = result.get('response', '')
    print(f"\nAI Response length: {len(ai_response)}")
    print(f"AI Response preview (first 200 chars): {ai_response[:200]}")
    print(f"AI Response preview (last 200 chars): {ai_response[-200:]}")
    
    # Check for JSON structure
    if ai_response.startswith('{') and ai_response.endswith('}'):
        print("\n❌ RESPONSE IS RAW JSON!")
        try:
            parsed = json.loads(ai_response)
            print(f"JSON keys: {list(parsed.keys())}")
            if 'narrative' in parsed:
                print(f"Narrative content: {parsed['narrative'][:200]}...")
        except:
            print("Failed to parse as JSON")
    else:
        print("\n✅ Response is text (not raw JSON)")
        
    # Check for JSON artifacts
    has_artifacts = (
        '"narrative":' in ai_response or
        '"god_mode_response":' in ai_response or
        '{"narrative"' in ai_response
    )
    
    if has_artifacts:
        print("\n❌ JSON ARTIFACTS DETECTED!")
    else:
        print("\n✅ No JSON artifacts")
else:
    print(f"Error: {response.text}")