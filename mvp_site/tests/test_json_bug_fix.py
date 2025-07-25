#!/usr/bin/env python3
"""
Test the JSON bug fix by calling parse_structured_response directly
"""

import os
import sys

import json

mvp_site_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, mvp_site_path)

from narrative_response_schema import parse_structured_response


def test_parse_structured_response_fix():
    """Test that parse_structured_response correctly extracts narrative"""

    # This is the exact JSON that causes the bug
    raw_json = """{
    "narrative": "[Mode: STORY MODE]\\n[SESSION_HEADER]\\nTimestamp: Year 11 New Peace, Kythorn Day 2, 08:00\\nLocation: Character Creation\\nStatus: Lvl 1 Unknown | HP: 0/0 (Temp: 0) | XP: 0/300 | Gold: 0gp\\nResources: HD: 0/0 | Spells: L1 0/0, L2 0/0 | Class Features\\nConditions: None | Exhaustion: 0 | Inspiration: No | Potions: 0\\n\\nYou've chosen for me to craft your character, a noble path indeed!",
    "entities_mentioned": ["Ser Alderon Vance"],
    "location_confirmed": "Character Creation",
    "state_updates": {
        "player_character_data": {}
    }
}"""

    print("Testing parse_structured_response with raw JSON...")
    print(f"Input (first 100 chars): {raw_json[:100]}...")

    # Call the function
    response_text, structured_response = parse_structured_response(raw_json)

    print("\n🔍 Results:")
    print(f"   response_text type: {type(response_text)}")
    print(f"   response_text starts with '{{': {response_text.strip().startswith('{')}")
    print(f"   response_text first 200 chars: {response_text[:200]}")
    print(f"   structured_response exists: {structured_response is not None}")

    # Check if bug exists
    if response_text.strip().startswith("{"):
        print("\n🚨 BUG CONFIRMED: parse_structured_response returned raw JSON!")
        print("   This is the root cause of the JSON display bug")

        # What it should return


        expected = json.loads(raw_json)["narrative"]
        print(f"\n   Expected: {expected[:100]}...")
        print(f"   Actual:   {response_text[:100]}...")

        return False
    print("\n✅ parse_structured_response correctly extracted narrative!")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("JSON Bug Root Cause Test")
    print("=" * 60)

    success = test_parse_structured_response_fix()

    if not success:
        print("\n🔴 Bug confirmed in parse_structured_response")
        print(
            "   Fix needed: Make parse_structured_response return narrative text, not JSON"
        )
    else:
        print("\n🟢 parse_structured_response works correctly")
