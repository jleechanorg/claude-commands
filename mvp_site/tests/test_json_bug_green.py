#!/usr/bin/env python3
"""
GREEN Test: This test should PASS after the fix is applied.
It verifies that narrative_text no longer contains raw JSON.
"""

import os
import sys
mvp_site_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, mvp_site_path)

from gemini_response import GeminiResponse
from narrative_response_schema import parse_structured_response

def test_json_bug_fixed():
    """
    GREEN TEST: This test proves the fix works by showing that
    _process_structured_response now correctly extracts narrative even from malformed JSON.
    """
    
    # Test case 1: Well-formed JSON (should work)
    print("Test 1: Well-formed JSON")
    raw_json = '''{
    "narrative": "[Mode: STORY MODE]\\nYou enter the dark cave...",
    "entities_mentioned": ["Dragon"],
    "location_confirmed": "Dark Cave"
}'''
    
    # Use the new GeminiResponse.create API
    gemini_response = GeminiResponse.create(raw_json)
    response_text = gemini_response.narrative_text
    print(f"  Result starts with '{{': {response_text.strip().startswith('{')}")
    print(f"  Result: {response_text[:50]}...")
    assert not response_text.strip().startswith('{'), "Well-formed JSON should extract narrative"
    
    # Test case 2: Malformed JSON (the bug case)
    print("\nTest 2: Malformed JSON without proper structure")
    malformed_json = '{"Some malformed JSON that would cause the bug'
    
    # Use the new GeminiResponse.create API
    gemini_response = GeminiResponse.create(malformed_json)
    response_text = gemini_response.narrative_text
    print(f"  Result starts with '{{': {response_text.strip().startswith('{')}")
    print(f"  Result: {response_text[:50]}...")
    
    # With the fix, this should NOT return raw JSON
    if response_text.strip().startswith('{'):
        print("  🚨 BUG STILL EXISTS: Malformed JSON returned as-is")
        return False
    else:
        print("  ✅ FIX WORKING: No raw JSON returned")
    
    # Test case 3: JSON with narrative field
    print("\nTest 3: JSON that triggers the temporary fix")
    json_with_narrative = '''{
    "narrative": "The story text that should be extracted",
    "other": "fields"
}'''
    
    # Use the new GeminiResponse.create API
    gemini_response = GeminiResponse.create(json_with_narrative)
    response_text = gemini_response.narrative_text
    print(f"  Result: {response_text}")
    assert response_text == "The story text that should be extracted", "Should extract narrative field"
    print("  ✅ Narrative correctly extracted")
    
    return True


def test_full_flow():
    """Test the full flow from raw response to GeminiResponse"""
    
    print("\nTest 4: Full flow with GeminiResponse creation")
    
    # Simulate the full flow
    raw_response = '''{
    "narrative": "You chose option 2. Let me create a character for you...",
    "entities_mentioned": ["Ser Alderon"],
    "state_updates": {"player_character_data": {"name": "Ser Alderon"}}
}'''
    
    # Create GeminiResponse using new API
    gemini_response = GeminiResponse.create(raw_response)
    
    print(f"  narrative_text: {gemini_response.narrative_text[:50]}...")
    print(f"  narrative_text starts with '{{': {gemini_response.narrative_text.strip().startswith('{')}")
    
    assert not gemini_response.narrative_text.strip().startswith('{'), \
        "GeminiResponse.narrative_text should not contain JSON"
    
    print("  ✅ Full flow works correctly - no JSON in narrative_text")
    
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("🟢 GREEN TEST: JSON Bug Fix Verification")
    print("=" * 60)
    
    try:
        # Run all tests
        test1_pass = test_json_bug_fixed()
        test2_pass = test_full_flow()
        
        if test1_pass and test2_pass:
            print("\n✅ ALL TESTS PASSED!")
            print("The JSON bug has been fixed successfully.")
            sys.exit(0)
        else:
            print("\n❌ Some tests failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)