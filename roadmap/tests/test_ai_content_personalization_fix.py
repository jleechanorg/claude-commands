#!/usr/bin/env python3
"""
Quick integration test to verify the AI content personalization fix.
This tests the actual flow: campaign creation → AI content generation → personalization check
"""

import os
import sys

# Add mvp_site to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mvp_site'))

# Set testing mode to use mock services (but test the actual logic flow)
os.environ["TESTING"] = "true"
os.environ["MOCK_SERVICES_MODE"] = "true"

from world_logic import create_campaign_unified
import asyncio

async def test_campaign_personalization_fix():
    """Test that campaign creation now includes personalized AI content"""

    print("🧪 Testing AI Content Personalization Fix")
    print("=" * 50)

    # Test data - user creates campaign with specific character and setting
    test_request = {
        "user_id": "test-user-123",
        "title": "Zara's Crystal Quest",
        "character": "Zara the Mystic Warrior",
        "setting": "Eldoria Realm where crystal magic flows",
        "description": "A mystical adventure with elemental crystals",
        "selected_prompts": ["narrative"],
        "custom_options": []
    }

    print(f"📋 Test Campaign Data:")
    print(f"   Title: {test_request['title']}")
    print(f"   Character: {test_request['character']}")
    print(f"   Setting: {test_request['setting']}")
    print("")

    # Call the unified campaign creation function
    result = await create_campaign_unified(test_request)

    # Check if campaign creation was successful
    if not result.get("success"):
        print(f"❌ Campaign creation failed: {result.get('error', 'Unknown error')}")
        return False

    # Extract the opening story that was generated
    opening_story = result.get("opening_story", "")
    print(f"🎯 Generated Opening Story:")
    print(f"   Length: {len(opening_story)} characters")
    print(f"   Preview: {opening_story[:200]}...")
    print("")

    # Test for personalization - should contain user's data
    personalization_checks = {
        "User Character Found": test_request["character"] in opening_story,
        "User Setting Found": "Eldoria" in opening_story or "crystal" in opening_story,
        "User Title Reference": test_request["title"] in opening_story or "Zara" in opening_story,
    }

    # Test for hardcoded content - should NOT contain these
    hardcoded_checks = {
        "No Shadowheart": "Shadowheart" not in opening_story,
        "No Bastion": "Bastion of Eternal Radiance" not in opening_story,
        "No Shar": "Shar" not in opening_story,
    }

    print("✅ Personalization Tests:")
    all_personalization_passed = True
    for test_name, passed in personalization_checks.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if not passed:
            all_personalization_passed = False

    print("")
    print("🚫 Hardcoded Content Tests:")
    all_hardcoded_passed = True
    for test_name, passed in hardcoded_checks.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if not passed:
            all_hardcoded_passed = False

    print("")

    # Overall result
    if all_personalization_passed and all_hardcoded_passed:
        print("🎉 SUCCESS: AI Content Personalization Fix is Working!")
        print("   ✅ User campaign data is being used in AI generation")
        print("   ✅ No hardcoded content detected")
        return True
    else:
        print("⚠️  PARTIAL SUCCESS: Some issues remain")
        if not all_personalization_passed:
            print("   ❌ User campaign data not fully integrated")
        if not all_hardcoded_passed:
            print("   ❌ Hardcoded content still present")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_campaign_personalization_fix())
    sys.exit(0 if success else 1)
