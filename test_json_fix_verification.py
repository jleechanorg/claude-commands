#!/usr/bin/env python3
"""
Test script to verify the JSON display bug fix.
Tests the parse_structured_response function with problematic JSON inputs.
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mvp_site'))

from narrative_response_schema import parse_structured_response
import logging_util

def test_json_artifact_cleanup():
    """Test that JSON artifacts are properly cleaned up."""
    
    # Test case 1: Raw JSON with Scene prefix (the exact bug scenario)
    test_input_1 = '''Scene #2: {
    "narrative": "[Mode: STORY MODE]\\n[CHARACTER CREATION - Step 2 of 7]...",
    "god_mode_response": "",
    "entities_mentioned": ["Mark Grayson", "Nolan"],
    "location_confirmed": "Omni-Man's House"
}'''
    
    print("=== Test 1: Raw JSON with Scene prefix ===")
    print(f"Input: {test_input_1[:100]}...")
    
    narrative_text, response_obj = parse_structured_response(test_input_1)
    
    print(f"Output narrative: {narrative_text[:100]}...")
    print(f"Contains JSON artifacts: {'"narrative":' in narrative_text or '"god_mode_response":' in narrative_text}")
    print(f"Response object type: {type(response_obj)}")
    print()
    
    # Test case 2: Pure JSON without Scene prefix
    test_input_2 = '''{
    "narrative": "The story continues with great adventure...",
    "god_mode_response": "",
    "entities_mentioned": ["Hero", "Villain"],
    "location_confirmed": "Castle"
}'''
    
    print("=== Test 2: Pure JSON ===")
    print(f"Input: {test_input_2[:100]}...")
    
    narrative_text_2, response_obj_2 = parse_structured_response(test_input_2)
    
    print(f"Output narrative: {narrative_text_2[:100]}...")
    print(f"Contains JSON artifacts: {'"narrative":' in narrative_text_2 or '"god_mode_response":' in narrative_text_2}")
    print(f"Response object type: {type(response_obj_2)}")
    print()
    
    # Test case 3: Properly formatted markdown JSON
    test_input_3 = '''```json
{
    "narrative": "This is properly formatted narrative text.",
    "god_mode_response": "",
    "entities_mentioned": ["Alice", "Bob"],
    "location_confirmed": "Forest"
}
```'''
    
    print("=== Test 3: Properly formatted markdown JSON ===")
    print(f"Input: {test_input_3[:100]}...")
    
    narrative_text_3, response_obj_3 = parse_structured_response(test_input_3)
    
    print(f"Output narrative: {narrative_text_3[:100]}...")
    print(f"Contains JSON artifacts: {'"narrative":' in narrative_text_3 or '"god_mode_response":' in narrative_text_3}")
    print(f"Response object type: {type(response_obj_3)}")
    print()
    
    # Summary
    all_clean = True
    for i, (text, label) in enumerate([(narrative_text, "Test 1"), (narrative_text_2, "Test 2"), (narrative_text_3, "Test 3")], 1):
        has_artifacts = '"narrative":' in text or '"god_mode_response":' in text
        if has_artifacts:
            print(f"❌ {label} still contains JSON artifacts")
            all_clean = False
        else:
            print(f"✅ {label} is clean")
    
    print(f"\n🎯 Overall result: {'All tests passed' if all_clean else 'Some tests failed'}")
    return all_clean

if __name__ == "__main__":
    print("Testing JSON artifact cleanup fix...\n")
    success = test_json_artifact_cleanup()
    sys.exit(0 if success else 1)