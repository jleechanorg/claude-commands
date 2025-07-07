#!/usr/bin/env python3
"""Quick test to trigger debug logging and see what's happening."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mvp_site'))

from narrative_response_schema import parse_structured_response

# Test with the user's exact JSON structure
user_json = '''{
    "narrative": "Scene content here",
    "god_mode_response": "",
    "entities_mentioned": ["Mark Grayson"],
    "location_confirmed": "Character Creation",
    "state_updates": {},
    "debug_info": {}
}'''

print("=== TESTING USER JSON ===")
result_text, result_obj = parse_structured_response(user_json)

print(f"Result text: {result_text}")
print(f"Contains JSON artifacts: {'"narrative":' in result_text}")
print(f"Result object: {result_obj}")