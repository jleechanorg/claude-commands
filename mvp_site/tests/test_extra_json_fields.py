#!/usr/bin/env python3
"""
Test handling of extra JSON fields from Gemini
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mvp_site'))

from narrative_response_schema import NarrativeResponse, parse_structured_response


class TestExtraJSONFields(unittest.TestCase):
    """Test that we handle extra fields Gemini might include"""

    def test_parse_json_with_extra_fields(self):
        """Test parsing JSON that includes fields not in NarrativeResponse schema"""
        # This is the actual JSON from the bug report (with updated format)
        test_json = """{
  "narrative": "Welcome, adventurer! Before we begin your journey in the World of Assiah, we need to create your character.\\n\\nWould you like to:\\n1. **Create a D&D character** - Choose from established D&D races and classes\\n2. **Let me create one for you** - I'll design a character based on the campaign setting\\n3. **Create a custom character** - Design your own unique character concept with custom class/abilities\\n\\nWhich option would you prefer? (1, 2, or 3)",
  "entities_mentioned": [],
  "location_confirmed": null,
  "state_updates": {
    "custom_campaign_state": {
      "character_creation": {
        "in_progress": true,
        "current_step": 1,
        "method_chosen": null
      }
    }
  },
  "debug_info": {
    "dm_notes": ["Starting character creation process"],
    "dice_rolls": [],
    "resources_used": "None",
    "state_rationale": "Tracking character creation progress"
  }
}"""

        # Parse the response
        narrative, response = parse_structured_response(test_json)

        # Should extract just the narrative, not the full JSON
        self.assertIsNotNone(narrative)
        self.assertIn("Welcome, adventurer!", narrative)
        # Planning blocks are no longer extracted from narrative - they must come from JSON
        # The entire narrative including choices should be preserved
        self.assertIn("Which option would you prefer?", narrative)

        # Should NOT contain JSON structure
        self.assertNotIn('"narrative":', narrative)
        self.assertNotIn('"entities_mentioned":', narrative)
        self.assertNotIn('"debug_info":', narrative)

        # Response object should be valid
        self.assertIsInstance(response, NarrativeResponse)
        self.assertEqual(response.entities_mentioned, [])
        self.assertEqual(
            response.location_confirmed, "Unknown"
        )  # null becomes "Unknown"
        self.assertIsNotNone(response.state_updates)
        self.assertIsNotNone(response.debug_info)
        self.assertIn("dm_notes", response.debug_info)
        # Planning block should be empty since it's not in the JSON
        # Planning block should be empty dict since it's not in the JSON
        self.assertEqual(response.planning_block, {})

    def test_narrative_response_with_debug_info(self):
        """Test that NarrativeResponse properly handles debug_info field"""
        response = NarrativeResponse(
            narrative="Test narrative",
            entities_mentioned=["Entity1"],
            location_confirmed="Test Location",
            state_updates={},
            debug_info={
                "dm_notes": ["Test note"],
                "dice_rolls": ["1d20+3 = 18"],
                "resources": "HD: 1/3, Spells: L1 2/2",
                "state_rationale": "Test rationale",
            },
        )

        # Core fields should work
        self.assertEqual(response.narrative, "Test narrative")
        self.assertEqual(response.entities_mentioned, ["Entity1"])

        # Debug info should be properly stored
        self.assertIsNotNone(response.debug_info)
        self.assertEqual(response.debug_info["dm_notes"], ["Test note"])
        self.assertEqual(response.debug_info["dice_rolls"], ["1d20+3 = 18"])


if __name__ == "__main__":
    unittest.main()
