#!/usr/bin/env python3
"""
Test character creation flow.
"""

import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_config import BASE_URL, get_test_session

# Using BASE_URL from test_config
SESSION = get_test_session()


def test_character_creation():
    """Test the 7-step character creation process."""
    print("🧙 TEST: Character Creation Flow")
    print("=" * 50)

    # Step 1: Create campaign with mechanics enabled
    print("\n1️⃣ Creating campaign with mechanics enabled...")
    campaign_data = {
        "prompt": "A classic fantasy adventure in a medieval kingdom",
        "enableNarrative": True,
        "enableMechanics": True,  # This triggers character creation
    }

    # Note: This would work on a real server with auth
    response = SESSION.post(f"{BASE_URL}/api/campaigns", json=campaign_data)

    if response.status_code not in [200, 201]:
        print(f"❌ Campaign creation failed: {response.status_code}")
        print("⚠️ Note: Character creation requires auth-enabled server")
        return False

    campaign = response.json()
    campaign_id = campaign.get("campaign_id")
    print(f"✅ Campaign created: {campaign_id}")

    # Step 2: Character creation should start automatically
    print("\n2️⃣ Character Creation Steps:")

    # Simulate the 7 steps
    character_steps = [
        ("1", "Choose Quick Build option"),  # Step 1: Method selection
        ("Human", "Select Human race"),  # Step 2: Race
        ("Fighter", "Select Fighter class"),  # Step 3: Class
        ("Folk Hero", "Choose Folk Hero background"),  # Step 4: Background
        ("15,14,13,12,10,8", "Standard array"),  # Step 5: Abilities
        ("Aldric", "Character name"),  # Step 6: Name
        ("Lawful Good", "Alignment"),  # Step 7: Alignment
    ]

    for i, (choice, description) in enumerate(character_steps, 1):
        print(f"\n  Step {i}/7: {description}")
        print(f"  📝 Input: '{choice}'")

        # Send character creation choice
        story_data = {"campaignId": campaign_id, "input": choice, "mode": "character"}

        response = SESSION.post(
            f"{BASE_URL}/api/campaigns/{campaign_id}/interaction", json=story_data
        )

        if response.status_code == 200:
            print(f"  ✅ Step {i} completed")
        else:
            print(f"  ❌ Step {i} failed: {response.status_code}")
            return False

    # Step 3: Verify character was created
    print("\n3️⃣ Verifying character creation...")
    response = SESSION.get(f"{BASE_URL}/api/campaigns/{campaign_id}")

    if response.status_code == 200:
        campaign_data = response.json()
        state = campaign_data.get("state", {})

        # Check for character data
        if "player_character" in state:
            pc = state["player_character"]
            print("✅ Character created:")
            print(f"   Name: {pc.get('name', 'Unknown')}")
            print(f"   Race: {pc.get('race', 'Unknown')}")
            print(f"   Class: {pc.get('class', 'Unknown')}")
            print(f"   Level: {pc.get('level', 1)}")
            return True
        print("❌ No character data found in state")
        return False

    return False


if __name__ == "__main__":
    try:
        response = requests.get(BASE_URL, timeout=2)
        print(f"✅ Server running at {BASE_URL}\n")

        success = test_character_creation()
        print(f"\n{'✅ TEST PASSED' if success else '❌ TEST FAILED'}")

    except Exception as e:
        print(f"❌ Error: {e}")
