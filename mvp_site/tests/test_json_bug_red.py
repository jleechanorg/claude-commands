#!/usr/bin/env python3
"""
RED Test: This test MUST FAIL to prove the JSON bug exists.
It checks that narrative_text should NOT contain raw JSON.
"""

import os
import sys
# Add mvp_site to path
mvp_site_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, mvp_site_path)

from unittest.mock import patch, MagicMock
from gemini_response import GeminiResponse

def test_narrative_text_should_not_contain_json():
    """
    RED TEST: This test proves the bug exists by showing that
    narrative_text currently contains raw JSON instead of extracted narrative.
    
    This test SHOULD FAIL while the bug exists.
    """
    
    # Simulate what happens in continue_story when it receives JSON from Gemini
    raw_json_response = '''{
    "narrative": "[Mode: STORY MODE]\\n[SESSION_HEADER]\\nTimestamp: Year 11 New Peace...\\n\\nYou've chosen for me to craft your character...",
    "entities_mentioned": ["Ser Alderon Vance"],
    "location_confirmed": "Character Creation",
    "state_updates": {
        "player_character_data": {}
    }
}'''
    
    # Create a GeminiResponse using the new API
    gemini_response = GeminiResponse.create(raw_json_response)
    
    print(f"\n   narrative_text type: {type(gemini_response.narrative_text)}")
    print(f"   narrative_text[:100]: {gemini_response.narrative_text[:100]}")
    print(f"   narrative_text contains JSON: {gemini_response.narrative_text.strip().startswith('{')}")
    
    # THIS ASSERTION SHOULD FAIL - proving the bug exists
    # The narrative_text SHOULD NOT start with '{' (should not be JSON)
    assert not gemini_response.narrative_text.strip().startswith('{'), \
        f"BUG: narrative_text contains raw JSON! First 200 chars: {gemini_response.narrative_text[:200]}"
    
    # Also check it shouldn't contain JSON markers
    assert '"narrative":' not in gemini_response.narrative_text, \
        "BUG: narrative_text contains JSON structure markers!"
    
    print("\n✅ narrative_text correctly contains only narrative text (no JSON)")


if __name__ == "__main__":
    print("=" * 60)
    print("🔴 RED TEST: JSON Bug Detection")
    print("This test SHOULD FAIL to prove the bug exists")
    print("=" * 60)
    
    try:
        test_narrative_text_should_not_contain_json()
        print("\n❌ UNEXPECTED: Test passed! This means the bug might be fixed already.")
        sys.exit(1)  # Exit with error because we expected failure
    except AssertionError as e:
        print(f"\n✅ EXPECTED FAILURE: {e}")
        print("\n🔴 RED TEST CONFIRMED: The JSON bug exists!")
        print("   narrative_text contains raw JSON instead of extracted narrative")
        sys.exit(0)  # Exit success because we got expected failure