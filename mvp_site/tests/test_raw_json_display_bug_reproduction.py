#!/usr/bin/env python3
"""
RED TEST: Reproduce the raw JSON display bug in god mode responses

This test reproduces the exact issue where structured JSON is displayed
instead of just the narrative content.
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from narrative_response_schema import parse_structured_response


class TestRawJsonDisplayBugReproduction(unittest.TestCase):
    """Test to reproduce the raw JSON display bug"""
    
    def test_parse_structured_response_works_correctly(self):
        """
        This test confirms that parse_structured_response actually works fine.
        The issue must be that raw JSON is being displayed WITHOUT parsing.
        """
        # This is the exact type of JSON response that's being displayed raw
        raw_json_response = """{
    "narrative": "[Mode: STORY MODE]\\n[CHARACTER CREATION - Step 2 of 7]\\n\\nExcellent choice! Character created successfully.",
    "entities_mentioned": ["Aerion Vance"],
    "location_confirmed": "Character Creation",
    "state_updates": {
        "custom_campaign_state": {
            "character_creation": {
                "in_progress": true,
                "current_step": 2
            }
        }
    },
    "debug_info": {
        "dm_notes": ["Player chose AI character generation"],
        "dice_rolls": [],
        "resources": "HD: 1/1"
    }
}"""
        
        # Parse the structured response - returns tuple (narrative_text, parsed_response)
        narrative_text, parsed_response = parse_structured_response(raw_json_response)
        
        # The narrative_text should be JUST the narrative content, not the full JSON
        expected_narrative = "[Mode: STORY MODE]\n[CHARACTER CREATION - Step 2 of 7]\n\nExcellent choice! Character created successfully."
        
        # This should pass - proving the parsing function works
        self.assertEqual(narrative_text, expected_narrative)
        self.assertNotIn('"narrative":', narrative_text, "Should not contain JSON keys")
        
    def test_reproduce_actual_raw_json_display_bug(self):
        """
        RED TEST: Reproduce the actual bug where the system displays raw JSON
        instead of calling parse_structured_response.
        
        This test simulates what happens when the response bypasses parsing.
        """
        # This is exactly what the user is seeing - raw JSON displayed directly
        raw_json_that_user_sees = """{
    "narrative": "[Mode: STORY MODE]\\n[CHARACTER CREATION - Step 2 of 7]\\n\\nExcellent choice! Character created successfully.",
    "entities_mentioned": ["Aerion Vance"],
    "location_confirmed": "Character Creation",
    "state_updates": {
        "custom_campaign_state": {
            "character_creation": {
                "in_progress": true,
                "current_step": 2
            }
        }
    }
}"""
        
        # The bug is that this raw JSON is being displayed directly to the user
        # instead of being parsed first. Let's simulate this:
        
        # What the user SHOULD see (after parsing):
        expected_user_display = "[Mode: STORY MODE]\n[CHARACTER CREATION - Step 2 of 7]\n\nExcellent choice! Character created successfully."
        
        # What the user ACTUALLY sees (the bug):
        actual_user_display = raw_json_that_user_sees  # This is the bug!
        
        # This assertion SHOULD FAIL - proving the bug exists
        self.assertEqual(actual_user_display, expected_user_display, 
                        "BUG: User is seeing raw JSON instead of parsed narrative!")
        
        # These should also fail if raw JSON is being displayed
        self.assertNotIn('"narrative":', actual_user_display, "User should not see JSON keys")
        self.assertNotIn('"entities_mentioned":', actual_user_display, "User should not see JSON keys")


if __name__ == '__main__':
    unittest.main()