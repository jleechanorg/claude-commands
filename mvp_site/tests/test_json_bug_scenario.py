#!/usr/bin/env python3
"""
Test the exact scenario that causes the JSON bug
"""

import os
import sys

mvp_site_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, mvp_site_path)


def test_exact_bug_scenario():
    """Reproduce the exact scenario from the error log"""

    # This is from the error log - the raw_response that Gemini returns
    raw_response = """{
    "narrative": "[Mode: STORY MODE]\\n[CHARACTER CREATION - Step 2 of 7]\\n\\n\\"Excellent choice, adventurer!\\" The voice that guided you through your first decision warms with a hint of excitement.",
    "entities_mentioned": ["Ser Alderon Vance"],
    "location_confirmed": "Character Creation",
    "state_updates": {
        "player_character_data": {
            "name": "Ser Alderon Vance"
        }
    },
    "debug_info": {}
}"""

    print("1. Testing _get_text_from_response simulation...")
    raw_response_text = raw_response  # This simulates _get_text_from_response

    print("2. Testing _process_structured_response...")
    from gemini_service import _process_structured_response

    response_text, structured_response = _process_structured_response(
        raw_response_text, []
    )

    print("\n🔍 After _process_structured_response:")
    print(f"   response_text type: {type(response_text)}")
    print(f"   response_text starts with '{{': {response_text.strip().startswith('{')}")
    print(f"   response_text[:100]: {response_text[:100]}")

    if response_text.strip().startswith("{"):
        print("\n🚨 BUG FOUND: _process_structured_response returned JSON!")

        # Now let's see what happens in continue_story
        print("\n3. Testing continue_story logic...")

        # Check for JSON (like continue_story does)
        if '"narrative":' in response_text:
            print("   ERROR: JSON_BUG_DETECTED_IN_GEMINI_SERVICE_CONTINUE!")
            print("   This matches the error log!")

        # This is what gets passed to GeminiResponse.create
        print("\n4. What gets passed to GeminiResponse.create:")
        print(f"   narrative_text = response_text = {response_text[:100]}...")

        return True  # Bug found
    print("\n✅ No bug found - response_text is clean narrative")
    return False


if __name__ == "__main__":
    print("=" * 60)
    print("Exact JSON Bug Scenario Test")
    print("=" * 60)

    bug_found = test_exact_bug_scenario()

    if bug_found:
        print("\n🔴 Bug reproduced successfully!")
        print("   The issue is in _process_structured_response or its dependencies")
    else:
        print("\n🟢 Could not reproduce bug with this scenario")
