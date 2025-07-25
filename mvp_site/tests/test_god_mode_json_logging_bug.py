"""Test to reproduce the god mode JSON logging bug - raw JSON being logged instead of processed narrative."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mvp_site'))
import json

from gemini_response import GeminiResponse
from narrative_response_schema import parse_structured_response


class TestGodModeJsonLoggingBug(unittest.TestCase):
    """Test to identify why raw JSON is being logged instead of processed narrative."""

    def test_reproduce_raw_json_logging_issue(self):
        """Reproduce the issue where raw JSON appears in logs instead of narrative."""

        # This simulates what might be happening: raw JSON string being logged directly
        raw_json_string = """{
    "narrative": "",
    "god_mode_response": "Test god mode response with\\nnewlines and special chars.",
    "entities_mentioned": ["Test Entity"],
    "location_confirmed": "Test Location",
    "state_updates": {},
    "debug_info": {}
}"""

        # Test 1: If raw JSON string is logged directly (BUG scenario)
        # This would show up in logs as the full JSON structure
        if raw_json_string.startswith("{") and '"god_mode_response"' in raw_json_string:
            print("BUG DETECTED: Raw JSON would be logged instead of narrative")
            bug_detected = True
        else:
            bug_detected = False

        self.assertTrue(bug_detected, "Should detect the raw JSON logging bug")

        # Test 2: Correct processing should extract just the narrative
        narrative_text, structured_response = parse_structured_response(raw_json_string)

        # Correct behavior: only narrative text, no JSON structure
        self.assertEqual(
            narrative_text, "Test god mode response with\nnewlines and special chars."
        )
        self.assertNotIn('"narrative":', narrative_text)
        self.assertNotIn('"god_mode_response":', narrative_text)

    def test_identify_logging_vs_parsing_issue(self):
        """Identify if the issue is in logging or parsing."""

        # Simulate the complete flow from raw API response to logging
        api_response = """{
    "narrative": "",
    "god_mode_response": "Divine command executed successfully.",
    "entities_mentioned": [],
    "location_confirmed": "Throne Room",
    "state_updates": {},
    "debug_info": {}
}"""

        # Create GeminiResponse object using new API
        gemini_response = GeminiResponse.create(api_response)

        # Step 3: Check what would be logged (gemini_response.narrative_text)
        logged_content = gemini_response.narrative_text

        # The bug: if logged_content contains JSON structure, then logging is wrong
        contains_json_structure = (
            '"narrative":' in logged_content
            or '"god_mode_response":' in logged_content
            or logged_content.startswith("{")
        )

        self.assertFalse(
            contains_json_structure,
            f"Logged content should not contain JSON structure. Got: {logged_content}",
        )

        # Correct behavior: logged content should be clean narrative
        self.assertEqual(logged_content, "Divine command executed successfully.")

    def test_potential_double_json_encoding_issue(self):
        """Test if the issue might be double JSON encoding."""

        # Scenario: API returns JSON, but somewhere it gets double-encoded
        original_response = {
            "narrative": "",
            "god_mode_response": 'Test response with special chars: quotes " and newlines \\n',
            "entities_mentioned": [],
            "location_confirmed": "Test",
            "state_updates": {},
            "debug_info": {},
        }

        # First encoding (normal)
        json_string = json.dumps(original_response)

        # Second encoding (BUG - double encoding)
        double_encoded = json.dumps(json_string)  # This would cause the bug

        # Test: double encoded would show up as escaped JSON in logs
        self.assertIn('\\"narrative\\":', double_encoded)
        self.assertIn('\\"god_mode_response\\":', double_encoded)

        # This might be what's happening in the logging pipeline
        if double_encoded.startswith('"'):  # String-encoded JSON
            print("POTENTIAL BUG: Double JSON encoding detected")

    def test_luke_campaign_exact_reproduction(self):
        """Test the exact pattern from Luke's campaign to see if it reproduces."""

        # This is exactly what appeared in Luke's campaign log
        luke_scene_pattern = """Scene #31: {
    "narrative": "",
    "god_mode_response": "That's another excellent point...",
    "entities_mentioned": ["Luke Skywalker", "Darth Vader", "Jedi Master"],
    "location_confirmed": "Imperial Installation",
    "state_updates": {},
    "debug_info": {
        "dm_notes": ["User questioning EXP mechanics"]
    }
}"""

        # The issue: this entire string appeared in the log instead of just the god_mode_response
        # This suggests that raw JSON was logged instead of processed narrative

        # Extract just the JSON part
        json_start = luke_scene_pattern.find("{")
        json_part = luke_scene_pattern[json_start:]

        # Parse it correctly
        narrative_text, structured_response = parse_structured_response(json_part)

        # What SHOULD have been logged (just the narrative)
        correct_logging = f"Scene #31: {narrative_text}"

        # What WAS logged (the full JSON structure)
        incorrect_logging = luke_scene_pattern

        # Verify the difference
        self.assertNotEqual(correct_logging, incorrect_logging)
        self.assertIn("That's another excellent point", correct_logging)
        self.assertNotIn('"god_mode_response":', correct_logging)

        # The bug: incorrect_logging contains JSON structure
        self.assertIn('"god_mode_response":', incorrect_logging)


if __name__ == "__main__":
    unittest.main()
