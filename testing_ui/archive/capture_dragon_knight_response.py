#!/usr/bin/env python3
"""
Simple test to capture Dragon Knight campaign creation response for mock data
"""

import json
import os
import sys
import time

import requests

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


def test_dragon_knight_creation():
    """Test Dragon Knight campaign creation and capture response"""
    print("🐲 Testing Dragon Knight Campaign Creation with Real API...")

    # Test data - Dragon Knight campaign
    campaign_data = {
        "title": "Test Dragon Knight Campaign",
        "character": "Ser Arion",
        "setting": "World of Assiah",
        "campaign_type": "dragon-knight",
        "selected_prompts": ["narrative", "mechanics"],
        "custom_options": ["defaultWorld"],
    }

    headers = {
        "Content-Type": "application/json",
        "X-Test-Bypass-Auth": "true",
        "X-Test-User-ID": "test-capture-user",
    }

    try:
        # Create campaign
        print("📤 Creating Dragon Knight campaign...")
        response = requests.post(
            "http://localhost:6007/api/campaigns",
            json=campaign_data,
            headers=headers,
            timeout=60,
        )

        if response.status_code == 201:
            result = response.json()
            campaign_id = result.get("campaign_id")
            print(f"✅ Campaign created successfully: {campaign_id}")

            # Wait for initial story generation (async process)
            print("⏳ Waiting for initial story generation...")
            time.sleep(10)

            # Get the campaign to see the initial story
            print("📥 Fetching campaign data...")
            campaign_response = requests.get(
                f"http://localhost:6007/api/campaigns/{campaign_id}",
                headers=headers,
                timeout=30,
            )

            if campaign_response.status_code == 200:
                campaign_data = campaign_response.json()
                story = campaign_data.get("data", {}).get("story", [])

                if story:
                    first_story_entry = story[0]
                    narrative_text = first_story_entry.get("text", "")

                    print("\n🎭 CAPTURED DRAGON KNIGHT NARRATIVE:")
                    print("=" * 60)
                    print(
                        narrative_text[:500] + "..."
                        if len(narrative_text) > 500
                        else narrative_text
                    )
                    print("=" * 60)

                    # Save for mock data
                    mock_data = {
                        "test_type": "dragon_knight_creation",
                        "campaign_data": campaign_data,
                        "api_response": result,
                        "narrative_response": {
                            "full_text": narrative_text,
                            "story_entry": first_story_entry,
                        },
                        "captured_at": time.time(),
                    }

                    # Save to mock data directory
                    os.makedirs("testing_ui/mock_data", exist_ok=True)
                    with open(
                        "testing_ui/mock_data/dragon_knight_responses.json", "w"
                    ) as f:
                        json.dump(mock_data, f, indent=2)

                    print(
                        "\n💾 Mock data saved to testing_ui/mock_data/dragon_knight_responses.json"
                    )

                    # Check if we got the rich Dragon Knight narrative
                    if (
                        "Celestial Imperium" in narrative_text
                        and "Empress Sariel" in narrative_text
                    ):
                        print("🎉 SUCCESS: Rich Dragon Knight narrative detected!")
                        return True
                    print(
                        "⚠️  WARNING: Generic narrative returned instead of Dragon Knight content"
                    )
                    print("This suggests the campaign_type fix needs verification")
                    return False
                print("❌ No story entries found in campaign")
                return False
            print(f"❌ Failed to fetch campaign: {campaign_response.status_code}")
            return False
        print(f"❌ Campaign creation failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False

    except Exception as e:
        print(f"💥 Error: {e}")
        return False


if __name__ == "__main__":
    success = test_dragon_knight_creation()
    sys.exit(0 if success else 1)
