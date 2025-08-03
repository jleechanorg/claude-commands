#!/usr/bin/env python3
from test_config import BASE_URL, get_test_session

"""
Test god mode interactions.
"""

import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Using BASE_URL from test_config
SESSION = get_test_session()


def test_god_mode():
    """Test god mode commands and switching."""
    print("🔮 TEST: God Mode Interactions")
    print("=" * 50)

    # Create campaign
    print("\n1️⃣ Creating campaign...")
    campaign_data = {
        "prompt": "A wizard exploring a haunted tower",
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

    # Test various god mode commands
    god_commands = [
        "GOD MODE: A ghostly figure appears at the top of the stairs",
        "GOD MODE: The temperature drops suddenly, frost forming on the walls",
        "GOD MODE: Add a magical sword hidden behind a painting",
        "GOD MODE: The wizard finds 50 gold coins in a dusty chest",
    ]

    print(f"\n2️⃣ Testing {len(god_commands)} god mode commands...")

    for i, command in enumerate(god_commands, 1):
        print(f"\n  Command {i}: '{command[:60]}...'")

        story_data = {
            "campaignId": campaign_id,
            "input": command,
            "mode": "character",  # API detects god mode from "GOD MODE:" prefix
        }

        response = SESSION.post(
            f"{BASE_URL}/api/campaigns/{campaign_id}/interaction", json=story_data
        )

        if response.status_code == 200:
            result = response.json()
            print("  ✅ God command executed")

            # Check if response indicates god mode was used
            result.get("text", "")
            if "god_mode_response" in result:
                print("  🔮 God response field present")
        else:
            print(f"  ❌ Failed: {response.status_code}")
            return False

    # Test switching between modes
    print("\n3️⃣ Testing mode switching...")

    # Character mode
    story_data = {
        "campaignId": campaign_id,
        "input": "I pick up the magical sword",
        "mode": "character",
    }
    response = SESSION.post(
        f"{BASE_URL}/api/campaigns/{campaign_id}/interaction", json=story_data
    )
    print(f"  ✅ Character mode: {response.status_code}")

    # Back to god mode
    story_data = {
        "campaignId": campaign_id,
        "input": "GOD MODE: The sword begins to glow with blue light",
        "mode": "character",
    }
    response = SESSION.post(
        f"{BASE_URL}/api/campaigns/{campaign_id}/interaction", json=story_data
    )
    print(f"  ✅ God mode again: {response.status_code}")

    return response.status_code == 200


if __name__ == "__main__":
    try:
        response = requests.get(BASE_URL, timeout=2)
        print(f"✅ Server running at {BASE_URL}\n")

        success = test_god_mode()
        print(f"\n{'✅ TEST PASSED' if success else '❌ TEST FAILED'}")

    except Exception as e:
        print(f"❌ Error: {e}")
