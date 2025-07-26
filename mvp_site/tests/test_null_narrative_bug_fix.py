"""Test for the null narrative bug fix."""

import os
import sys
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from narrative_response_schema import NarrativeResponse, parse_structured_response


class TestNullNarrativeBugFix(unittest.TestCase):
    """Test the fix for the null narrative raw JSON display bug."""

    def test_null_narrative_field_no_raw_json(self):
        """Test that null narrative field doesn't show raw JSON."""
        # This was the actual bug - when narrative is null (JSON null),
        # the system would display the entire raw JSON to the user
        null_narrative_response = """{
            "narrative": null,
            "entities_mentioned": ["dragon"],
            "location_confirmed": "Forest",
            "state_updates": {"npc_data": {"dragon": {"status": "alive"}}},
            "debug_info": {}
        }"""

        narrative, response_obj = parse_structured_response(null_narrative_response)

        # The fix ensures we get an empty string instead of raw JSON
        self.assertEqual(narrative, "", "Null narrative should result in empty string")

        # Verify NO raw JSON appears in the output
        self.assertNotIn('"narrative"', narrative, "Raw JSON key should not appear")
        self.assertNotIn(
            '"entities_mentioned"', narrative, "Raw JSON key should not appear"
        )
        self.assertNotIn('"state_updates"', narrative, "Raw JSON key should not appear")
        self.assertNotIn("{", narrative, "Raw JSON braces should not appear")
        self.assertNotIn("}", narrative, "Raw JSON braces should not appear")
        self.assertNotIn("null", narrative, "Raw null value should not appear")

        # Verify the response object is still properly created
        self.assertIsInstance(response_obj, NarrativeResponse)
        self.assertEqual(response_obj.entities_mentioned, ["dragon"])
        self.assertEqual(response_obj.location_confirmed, "Forest")

    def test_missing_narrative_field_no_raw_json(self):
        """Test that missing narrative field doesn't show raw JSON."""
        # Test case where narrative field is completely missing
        missing_narrative_response = """{
            "entities_mentioned": ["dragon"],
            "location_confirmed": "Forest",
            "state_updates": {"npc_data": {"dragon": {"status": "alive"}}},
            "debug_info": {}
        }"""

        narrative, response_obj = parse_structured_response(missing_narrative_response)

        # Should get empty string instead of raw JSON
        self.assertEqual(
            narrative, "", "Missing narrative should result in empty string"
        )

        # Verify NO raw JSON appears in the output
        self.assertNotIn(
            '"entities_mentioned"', narrative, "Raw JSON key should not appear"
        )
        self.assertNotIn('"state_updates"', narrative, "Raw JSON key should not appear")
        self.assertNotIn("{", narrative, "Raw JSON braces should not appear")
        self.assertNotIn("}", narrative, "Raw JSON braces should not appear")

        # Verify the response object is still properly created
        self.assertIsInstance(response_obj, NarrativeResponse)
        self.assertEqual(response_obj.entities_mentioned, ["dragon"])
        self.assertEqual(response_obj.location_confirmed, "Forest")

    def test_empty_string_narrative_works(self):
        """Test that empty string narrative works correctly."""
        empty_narrative_response = """{
            "narrative": "",
            "entities_mentioned": ["dragon"],
            "location_confirmed": "Forest",
            "state_updates": {},
            "debug_info": {}
        }"""

        narrative, response_obj = parse_structured_response(empty_narrative_response)

        # Should get empty string (same as input)
        self.assertEqual(narrative, "")
        self.assertIsInstance(response_obj, NarrativeResponse)
        self.assertEqual(response_obj.narrative, "")

    def test_normal_narrative_still_works(self):
        """Test that normal narrative processing still works."""
        normal_response = """{
            "narrative": "A dragon appears!",
            "entities_mentioned": ["dragon"],
            "location_confirmed": "Forest",
            "state_updates": {},
            "debug_info": {}
        }"""

        narrative, response_obj = parse_structured_response(normal_response)

        # Should get the normal narrative
        self.assertEqual(narrative, "A dragon appears!")
        self.assertIsInstance(response_obj, NarrativeResponse)
        self.assertEqual(response_obj.narrative, "A dragon appears!")

    def test_god_mode_response_with_null_narrative(self):
        """Test god mode response handling with null narrative."""
        god_mode_null_narrative = """{
            "narrative": null,
            "god_mode_response": "Divine intervention occurs",
            "entities_mentioned": [],
            "location_confirmed": "Unknown",
            "state_updates": {},
            "debug_info": {}
        }"""

        narrative, response_obj = parse_structured_response(god_mode_null_narrative)

        # Should get the god mode response, not raw JSON
        self.assertEqual(narrative, "Divine intervention occurs")
        self.assertIsInstance(response_obj, NarrativeResponse)
        self.assertEqual(response_obj.god_mode_response, "Divine intervention occurs")

        # Verify NO raw JSON appears
        self.assertNotIn('"narrative"', narrative, "Raw JSON should not appear")
        self.assertNotIn("null", narrative, "Raw null should not appear")


if __name__ == "__main__":
    unittest.main()
