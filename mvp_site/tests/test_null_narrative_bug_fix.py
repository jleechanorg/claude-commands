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
        assert narrative == "", "Null narrative should result in empty string"

        # Verify NO raw JSON appears in the output
        assert '"narrative"' not in narrative, "Raw JSON key should not appear"
        assert '"entities_mentioned"' not in narrative, "Raw JSON key should not appear"
        assert '"state_updates"' not in narrative, "Raw JSON key should not appear"
        assert "{" not in narrative, "Raw JSON braces should not appear"
        assert "}" not in narrative, "Raw JSON braces should not appear"
        assert "null" not in narrative, "Raw null value should not appear"

        # Verify the response object is still properly created
        assert isinstance(response_obj, NarrativeResponse)
        assert response_obj.entities_mentioned == ["dragon"]
        assert response_obj.location_confirmed == "Forest"

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
        assert narrative == "", "Missing narrative should result in empty string"

        # Verify NO raw JSON appears in the output
        assert '"entities_mentioned"' not in narrative, "Raw JSON key should not appear"
        assert '"state_updates"' not in narrative, "Raw JSON key should not appear"
        assert "{" not in narrative, "Raw JSON braces should not appear"
        assert "}" not in narrative, "Raw JSON braces should not appear"

        # Verify the response object is still properly created
        assert isinstance(response_obj, NarrativeResponse)
        assert response_obj.entities_mentioned == ["dragon"]
        assert response_obj.location_confirmed == "Forest"

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
        assert narrative == ""
        assert isinstance(response_obj, NarrativeResponse)
        assert response_obj.narrative == ""

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
        assert narrative == "A dragon appears!"
        assert isinstance(response_obj, NarrativeResponse)
        assert response_obj.narrative == "A dragon appears!"

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
        assert narrative == "Divine intervention occurs"
        assert isinstance(response_obj, NarrativeResponse)
        assert response_obj.god_mode_response == "Divine intervention occurs"

        # Verify NO raw JSON appears
        assert '"narrative"' not in narrative, "Raw JSON should not appear"
        assert "null" not in narrative, "Raw null should not appear"


if __name__ == "__main__":
    unittest.main()
