#!/usr/bin/env python3
"""Test _process_structured_response function directly to isolate the issue."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mvp_site'))

# Mock testing environment
os.environ['TESTING'] = 'true'

from gemini_service import _process_structured_response

# Test with raw JSON that looks like what the AI returns
test_raw_json = '''{
    "narrative": "[CHARACTER CREATION - Step 1 of 7]\\n\\nWelcome, adventurer! This is the character creation process.",
    "god_mode_response": "",
    "entities_mentioned": [],
    "location_confirmed": "Character Creation",
    "state_updates": {
        "custom_campaign_state": {
            "character_creation": {
                "in_progress": true,
                "current_step": 1
            }
        }
    },
    "debug_info": {
        "dm_notes": ["Starting character creation"]
    }
}'''

print("=== Testing _process_structured_response ===")
print(f"Input: {test_raw_json[:200]}...")
print()

try:
    response_text, structured_response = _process_structured_response(test_raw_json, [])
    
    print(f"✅ Function completed successfully")
    print(f"Response text length: {len(response_text)}")
    print(f"Response text preview: {response_text[:200]}...")
    print()
    
    # Check for the critical bug
    has_json_artifacts = (
        '"narrative":' in response_text or 
        '"god_mode_response":' in response_text or
        '"entities_mentioned":' in response_text
    )
    
    print(f"Contains JSON artifacts: {has_json_artifacts}")
    
    if has_json_artifacts:
        print("❌ BUG CONFIRMED: _process_structured_response is returning JSON artifacts!")
        print(f"Full response text: {response_text}")
    else:
        print("✅ _process_structured_response working correctly - no JSON artifacts")
        
    print(f"Structured response type: {type(structured_response)}")
    print(f"Structured response: {structured_response}")
    
except Exception as e:
    print(f"❌ Exception in _process_structured_response: {e}")
    import traceback
    traceback.print_exc()