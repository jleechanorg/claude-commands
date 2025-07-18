#!/usr/bin/env python3
"""
API Test: Test the actual API to see if JSON is returned in text field
"""

import json
import sys

import requests

# Test configuration
BASE_URL = "http://localhost:6006"
TEST_USER_ID = "json-bug-api-test"


def test_api_json_bug():
    """Test if the API returns JSON in the text field"""

    print("1. Creating campaign...")
    # Create campaign
    campaign_data = {
        "title": "JSON Bug API Test",
        "premise": "A brave knight in a land of dragons needs to choose between killing an evil dragon or joining its side.",
        "customization": {"use_default_world": True},
    }

    headers = {"X-Test-Mode": "true", "X-Test-User-Id": TEST_USER_ID}

    resp = requests.post(
        f"{BASE_URL}/api/campaigns", json=campaign_data, headers=headers
    )

    if resp.status_code != 201:
        print(f"❌ Failed to create campaign: {resp.status_code}")
        print(resp.text)
        return False

    campaign = resp.json()
    campaign_id = campaign["id"]
    print(f"✅ Created campaign: {campaign_id}")

    # Send interaction to trigger bug
    print("\n2. Sending interaction (option 2)...")
    interaction_data = {"text": "2", "mode": "character"}

    resp = requests.post(
        f"{BASE_URL}/api/campaigns/{campaign_id}/interaction",
        json=interaction_data,
        headers=headers,
    )

    if resp.status_code != 200:
        print(f"❌ Failed to send interaction: {resp.status_code}")
        return False

    response_data = resp.json()

    # Check if text field contains JSON
    response_text = response_data.get("text", "")

    print("\n🔍 API Response Analysis:")
    print(f"   Response text type: {type(response_text)}")
    print(f"   Response text length: {len(response_text)}")
    print(f"   Response text starts with '{{': {response_text.strip().startswith('{')}")
    print(f"   Response text first 200 chars: {response_text[:200]}")

    # Save full response for analysis
    with open("/tmp/json_bug_api_response.json", "w") as f:
        json.dump(response_data, f, indent=2)
    print("\n💾 Full API response saved to /tmp/json_bug_api_response.json")

    if response_text.strip().startswith("{") and '"narrative":' in response_text:
        print("\n🚨 JSON BUG CONFIRMED!")
        print("   The API is returning raw JSON in the text field!")

        # Save the problematic text
        with open("/tmp/json_bug_text_field.txt", "w") as f:
            f.write(response_text)
        print("   Problematic text saved to /tmp/json_bug_text_field.txt")

        return True
    print("\n✅ No JSON bug detected in API response")
    print("   The text field contains proper narrative text")
    return False


if __name__ == "__main__":
    print("=" * 60)
    print("🔍 JSON Bug API Test")
    print("=" * 60)

    # Check server
    try:
        r = requests.get(BASE_URL, timeout=2)
        print("✅ Server is running\n")
    except:
        print("❌ Server not running!")
        print("   Start with: TESTING=true PORT=6006 python mvp_site/main.py serve")
        sys.exit(1)

    bug_found = test_api_json_bug()

    if bug_found:
        print("\n🔴 TEST RESULT: JSON bug exists in API!")
        sys.exit(0)  # Success - we found the bug
    else:
        print("\n🟢 TEST RESULT: No JSON bug found")
        sys.exit(1)  # Unexpected - bug should exist
