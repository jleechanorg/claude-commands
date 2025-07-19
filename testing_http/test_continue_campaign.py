#!/usr/bin/env python3
"""
Test continuing an existing campaign.
"""

import os
import sys
import time

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_config import BASE_URL, get_test_session

SESSION = get_test_session()


def test_continue_campaign():
    """Test loading and continuing an existing campaign."""
    print("🎮 TEST: Continue Existing Campaign")
    print("=" * 50)

    # Step 1: Create a campaign first
    print("\n1️⃣ Creating initial campaign...")
    campaign_data = {
        "prompt": "A knight defending a castle from invaders",
        "enableNarrative": True,
        "enableMechanics": False,
    }

    response = SESSION.post(f"{BASE_URL}/api/campaigns", json=campaign_data)
    if response.status_code not in [200, 201]:
        print(f"❌ Failed to create campaign: {response.status_code}")
        return False

    campaign = response.json()
    campaign_id = campaign.get("campaign_id")
    print(f"✅ Campaign created: {campaign_id}")

    # Step 2: Make some initial moves
    print("\n2️⃣ Making initial moves...")
    moves = [
        "I inspect the castle walls for weaknesses",
        "I rally the defenders and give an inspiring speech",
    ]

    for move in moves:
        story_data = {"campaignId": campaign_id, "input": move, "mode": "character"}
        response = SESSION.post(
            f"{BASE_URL}/api/campaigns/{campaign_id}/interaction", json=story_data
        )
        print(f"  ✅ Move: '{move[:50]}...'")
        time.sleep(0.5)

    # Step 3: Simulate closing and reopening (new session)
    print("\n3️⃣ Simulating browser close/reopen...")
    NEW_SESSION = get_test_session()  # Need auth headers in new session too!

    # Step 4: Load campaign list
    print("\n4️⃣ Loading campaign list...")
    response = NEW_SESSION.get(f"{BASE_URL}/api/campaigns")
    campaigns = response.json() if response.status_code == 200 else []

    print(f"  📊 Found {len(campaigns)} campaigns")
    found = False
    for camp in campaigns:
        camp_id = camp.get("id")
        print(f"    - Campaign ID: {camp_id}")
        if camp_id == campaign_id:
            found = True
            print(f"  ✅ Found campaign: {camp.get('title', 'Untitled')}")
            break

    if not found:
        print("  ❌ Campaign not found in list!")
        return False

    # Step 5: Load the specific campaign
    print(f"\n5️⃣ Loading campaign {campaign_id}...")
    response = NEW_SESSION.get(f"{BASE_URL}/api/campaigns/{campaign_id}")
    if response.status_code != 200:
        print(f"  ❌ Failed to load campaign: {response.status_code}")
        return False

    campaign_data = response.json()
    entries = campaign_data.get("entries", [])
    print(f"  ✅ Campaign loaded with {len(entries)} entries")

    # Step 6: Continue playing
    print("\n6️⃣ Continuing gameplay...")
    continue_move = "I order the archers to take positions on the walls"
    story_data = {
        "campaignId": campaign_id,
        "input": continue_move,
        "mode": "character",
    }

    response = NEW_SESSION.post(
        f"{BASE_URL}/api/campaigns/{campaign_id}/interaction", json=story_data
    )
    if response.status_code == 200:
        print(f"  ✅ Successfully continued: '{continue_move}'")
        result = response.json()
        print(f"  📜 AI responded with {len(result.get('text', ''))} characters")
        return True
    print(f"  ❌ Failed to continue: {response.status_code}")
    if response.status_code == 500:
        print(f"  💥 Error: {response.json().get('error', 'Unknown error')}")
    return False


if __name__ == "__main__":
    try:
        # Check server
        response = requests.get(BASE_URL, timeout=2)
        print(f"✅ Server running at {BASE_URL}\n")

        success = test_continue_campaign()
        print(f"\n{'✅ TEST PASSED' if success else '❌ TEST FAILED'}")

    except Exception as e:
        print(f"❌ Error: {e}")
