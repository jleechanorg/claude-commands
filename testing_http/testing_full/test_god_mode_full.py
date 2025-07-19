#!/usr/bin/env python3
"""
FULL API Test: God mode interactions using real Firebase and Gemini APIs.

WARNING: This test uses REAL APIs and will incur costs!
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_config_full import BASE_URL, CostTracker, get_test_session, validate_config


def test_god_mode_full():
    """Test god mode commands with full APIs."""
    print("🔮 FULL API TEST: God Mode Interactions")
    print("⚠️  This test uses REAL Gemini API and costs money!")
    print("=" * 50)

    # Validate configuration
    if not validate_config():
        return False

    SESSION = get_test_session()
    tracker = CostTracker()

    try:
        # Create campaign
        print("\n1️⃣ Creating campaign with REAL Gemini...")
        campaign_data = {
            "prompt": "A wizard in a tower",  # Keep short
            "enableNarrative": True,
            "enableMechanics": False,
        }

        response = SESSION.post(f"{BASE_URL}/api/campaigns", json=campaign_data)
        tracker.track_gemini(estimated_tokens=2000)
        tracker.track_firestore("write", 2)

        if response.status_code not in [200, 201]:
            print(f"❌ Failed to create campaign: {response.status_code}")
            return False

        campaign = response.json()
        campaign_id = campaign.get("campaign_id")
        print(f"✅ Campaign created: {campaign_id}")

        # Test god mode commands (keep minimal)
        god_commands = ["GOD MODE: A ghost appears", "GOD MODE: Add magical sword"]

        print(f"\n2️⃣ Testing {len(god_commands)} god mode commands...")

        for i, command in enumerate(god_commands, 1):
            print(f"\n  Command {i}: '{command}'")

            story_data = {
                "campaignId": campaign_id,
                "input": command,
                "mode": "character",  # API detects god mode from prefix
            }

            response = SESSION.post(
                f"{BASE_URL}/api/campaigns/{campaign_id}/interaction", json=story_data
            )
            tracker.track_gemini(estimated_tokens=1000)
            tracker.track_firestore("read", 2)
            tracker.track_firestore("write", 1)

            if response.status_code == 200:
                print("  ✅ God command executed")
            else:
                print(f"  ❌ Failed: {response.status_code}")
                return False

        # Test mode switching
        print("\n3️⃣ Testing mode switching...")

        # Character mode
        story_data = {
            "campaignId": campaign_id,
            "input": "I take the sword",
            "mode": "character",
        }

        response = SESSION.post(
            f"{BASE_URL}/api/campaigns/{campaign_id}/interaction", json=story_data
        )
        tracker.track_gemini(estimated_tokens=1000)
        tracker.track_firestore("read", 2)
        tracker.track_firestore("write", 1)

        if response.status_code == 200:
            print("  ✅ Character mode works")
            return True
        print(f"  ❌ Character mode failed: {response.status_code}")
        return False

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return False

    finally:
        # Always print cost summary
        tracker.print_summary()


if __name__ == "__main__":
    # Safety confirmation
    print("⚠️  WARNING: This test uses REAL APIs and will cost money!")
    print("Estimated cost: ~$0.001-0.002")
    response = input("Continue? (y/n): ")

    if response.lower() != "y":
        print("Test cancelled.")
        sys.exit(0)

    # Run test
    success = test_god_mode_full()
    print(f"\n{'✅ TEST PASSED' if success else '❌ TEST FAILED'}")
