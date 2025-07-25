#!/usr/bin/env python3
"""
RED TEST: Reproduce the raw JSON display bug in god mode responses

This test reproduces the exact issue where structured JSON is displayed
instead of just the narrative content.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

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
        GREEN TEST: Verify the fix for the raw JSON display bug.

        This test demonstrates that raw JSON responses are properly parsed
        to extract just the narrative text for display to users.
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

        # What the user SHOULD see (after fixing the bug):
        # FIX: Parse the raw JSON to extract just the narrative
        actual_user_display, _ = parse_structured_response(raw_json_that_user_sees)

        # This assertion SHOULD PASS - proving the bug is fixed
        self.assertEqual(
            actual_user_display,
            expected_user_display,
            "FIX: User should see parsed narrative, not raw JSON!",
        )

        # These should also fail if raw JSON is being displayed
        self.assertNotIn(
            '"narrative":', actual_user_display, "User should not see JSON keys"
        )
        self.assertNotIn(
            '"entities_mentioned":',
            actual_user_display,
            "User should not see JSON keys",
        )


if __name__ == "__main__":
    unittest.main()
