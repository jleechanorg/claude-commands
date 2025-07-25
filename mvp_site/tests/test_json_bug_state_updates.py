#!/usr/bin/env python3
"""
Test if state updates cause the JSON bug
"""

import os
import sys

import json

mvp_site_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, mvp_site_path)
from narrative_response_schema import parse_structured_response


def test_state_updates_scenario():
    """Test if appending state updates causes JSON to appear"""

    # Start with clean narrative
    response_text = """[Mode: STORY MODE]
[CHARACTER CREATION - Step 2 of 7]

"Excellent choice, adventurer!" The voice that guided you through your first decision warms with a hint of excitement."""

    print("Initial response_text (clean):")
    print(f"  Starts with '{{': {response_text.strip().startswith('{')}")
    print(f"  First 100 chars: {response_text[:100]}")

    # Simulate appending state updates (from gemini_service.py line ~510)
    state_updates = {
        "player_character_data": {"name": "Ser Alderon Vance", "hp_max": 10}
    }



    state_updates_text = f"\n\n[STATE_UPDATES_PROPOSED]\n{json.dumps(state_updates, indent=2)}\n[END_STATE_UPDATES_PROPOSED]"
    response_text = response_text + state_updates_text

    print("\nAfter appending state updates:")
    print(f"  Length increased from 155 to {len(response_text)}")
    print(f"  Still starts with '{{': {response_text.strip().startswith('{')}")
    print(
        f"  Contains 'STATE_UPDATES_PROPOSED': {'STATE_UPDATES_PROPOSED' in response_text}"
    )

    # This is still not JSON at the start
    print("\nConclusion: State updates don't cause the JSON bug")

    return response_text


def test_different_parse_result():
    """What if parse_structured_response returns JSON in some cases?"""

    print("\n" + "=" * 60)
    print("Testing edge cases where parse_structured_response might return JSON")



    # Test case 1: Malformed JSON
    test_cases = [
        # Missing closing brace
        '{"narrative": "Test story", "entities_mentioned": ["Bob"]',
        # Invalid JSON with narrative
        '{"narrative": "Test story" "broken json here',
        # Just raw text that looks like JSON
        '{"Some weird text that starts with brace',
        # Empty response
        "",
        # Just a string
        '"Just a quoted string"',
    ]

    for i, test_input in enumerate(test_cases):
        print(f"\nTest case {i + 1}: {test_input[:50]}...")
        try:
            response_text, _ = parse_structured_response(test_input)
            print(f"  Result starts with '{{': {response_text.strip().startswith('{')}")
            print(f"  Result: {response_text[:100]}")

            if response_text.strip().startswith("{"):
                print("  🚨 FOUND IT! This input causes JSON to be returned!")
                return True
        except Exception as e:
            print(f"  Exception: {e}")

    return False


if __name__ == "__main__":
    # Test 1: State updates
    test_state_updates_scenario()

    # Test 2: Edge cases
    found_bug = test_different_parse_result()

    if found_bug:
        print("\n🔴 Found a case where parse_structured_response returns JSON!")
    else:
        print("\n🟡 Could not reproduce the exact bug scenario")
