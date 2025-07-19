#!/usr/bin/env python3
"""Test campaign creation to debug the empty narrative issue"""

import json

import requests

BASE_URL = "http://localhost:6006"
headers = {
    "X-Test-Mode": "true",
    "X-Test-User-ID": "debug-test-user",
    "X-Test-Token": "test-token",
    "Content-Type": "application/json",
}

print("🔍 Testing Campaign Creation...")
print("=" * 50)

# Create a new campaign
payload = {
    "title": "Debug Test Campaign",
    "campaign_type": "dragon-knight",
    "character_name": "Test Knight",
    "setting": "World of Assiah",
    "description": "",
    "custom_options": ["defaultWorld"],
    "selected_prompts": ["narrative", "mechanics"],
}

print("\n📤 Creating campaign with payload:")
print(json.dumps(payload, indent=2))

response = requests.post(f"{BASE_URL}/api/campaigns", headers=headers, json=payload)

print(f"\n📥 Response status: {response.status_code}")

if response.status_code == 201:
    campaign_data = response.json()
    campaign_id = campaign_data.get("id")
    print(f"✅ Campaign created with ID: {campaign_id}")

    # Check the campaign data
    print("\n📋 Campaign Data:")
    print(
        json.dumps(campaign_data, indent=2)[:500] + "..."
        if len(json.dumps(campaign_data)) > 500
        else json.dumps(campaign_data, indent=2)
    )

    # Check for narrative content
    if "narrative_history" in campaign_data:
        history = campaign_data["narrative_history"]
        if history:
            first_entry = history[0] if isinstance(history, list) else history
            narrative_text = (
                first_entry.get("narrative_text", "")
                if isinstance(first_entry, dict)
                else ""
            )
            print(f"\n📖 Narrative Text Length: {len(narrative_text)} characters")
            if narrative_text:
                print(f"First 200 chars: {narrative_text[:200]}...")
            else:
                print("❌ ERROR: Narrative text is empty!")
        else:
            print("❌ ERROR: No narrative history!")
    else:
        print("❌ ERROR: No narrative_history field in response!")

    # Check for god text
    god_text = campaign_data.get("god_text", "")
    if god_text:
        print(f"\n🎭 God Text (first 200 chars): {god_text[:200]}...")

else:
    print(f"❌ Failed to create campaign: {response.text}")
