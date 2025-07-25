#!/usr/bin/env python3
"""
Unit test for the JSON display bug fix in narrative_response_schema.py

This test validates that the indentation fix in narrative_response_schema.py:142
correctly handles fallback scenarios when NarrativeResponse creation fails.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mvp_site'))

from narrative_response_schema import NarrativeResponse, parse_structured_response


class TestJSONDisplayFix(unittest.TestCase):
    """Test suite for the JSON display bug fix"""

    def test_narrative_extraction_with_invalid_field_fallback(self):
        """
        Test that the indentation fix correctly handles the fallback path.

        This test reproduces the exact scenario where the bug occurred:
        1. JSON parses successfully
        2. NarrativeResponse creation fails due to invalid field
        3. Exception handler creates fallback response
        4. Fixed indentation ensures return statement is inside except block
        """
        # JSON with invalid field that triggers the exception path
        test_json = """
        {
            "narrative": "Scene #10: [Mode: DM MODE] The campaign is working correctly now.",
            "entities_mentioned": ["Ser Caius of House Varrick", "Ser Bastion"],
            "location_confirmed": "Starfall Command Barracks, Aeterna",
            "state_updates": {},
            "invalid_field": "this causes NarrativeResponse creation to fail"
        }
        """

        # Parse the response - this should succeed with the fix
        result_narrative, result_response = parse_structured_response(test_json)

        # Validate the fix works correctly
        self.assertIsNotNone(result_narrative, "Should return narrative text, not None")
        self.assertIsInstance(
            result_narrative, str, "Should return narrative as string"
        )

        # Critical assertion: should return the extracted narrative, not raw JSON
        self.assertIn(
            "Scene #10", result_narrative, "Should contain the actual narrative text"
        )
        self.assertIn(
            "DM MODE", result_narrative, "Should contain the narrative content"
        )
        self.assertNotIn(
            '"narrative":', result_narrative, "Should NOT contain raw JSON structure"
        )
        self.assertNotIn(
            '"entities_mentioned":',
            result_narrative,
            "Should NOT contain raw JSON structure",
        )

        # Response object should be valid fallback
        self.assertIsInstance(
            result_response, NarrativeResponse, "Should return NarrativeResponse object"
        )
        self.assertEqual(
            result_response.narrative,
            result_narrative,
            "Response narrative should match returned narrative",
        )
        self.assertEqual(
            result_response.entities_mentioned,
            ["Ser Caius of House Varrick", "Ser Bastion"],
        )
        self.assertEqual(
            result_response.location_confirmed, "Starfall Command Barracks, Aeterna"
        )

    def test_json_with_markdown_code_blocks(self):
        """
        Test parsing JSON wrapped in markdown code blocks.

        This tests the scenario where AI returns JSON in markdown format,
        which should be properly extracted by the robust JSON parser.
        """
        markdown_json_response = """```json
{
  "narrative": "[Mode: DM MODE] Understanding confirmed. Processing user request.",
  "entities_mentioned": ["Test Entity"],
  "location_confirmed": "Test Location",
  "state_updates": {}
}
```"""

        result_narrative, result_response = parse_structured_response(
            markdown_json_response
        )

        # Should extract narrative from markdown-wrapped JSON
        self.assertIsNotNone(result_narrative)
        self.assertIn("DM MODE", result_narrative)
        self.assertIn("Understanding confirmed", result_narrative)
        self.assertNotIn(
            "```json", result_narrative, "Should strip markdown formatting"
        )
        self.assertNotIn(
            '"narrative":',
            result_narrative,
            "Should extract narrative, not return raw JSON",
        )

        # Response object should be properly constructed
        self.assertIsInstance(result_response, NarrativeResponse)
        self.assertEqual(result_response.entities_mentioned, ["Test Entity"])

    def test_plain_text_fallback(self):
        """
        Test the final fallback for non-JSON text.

        When input is not JSON at all, should return the original text
        with a basic NarrativeResponse wrapper.
        """
        plain_text = "This is just plain narrative text, not JSON at all."

        result_narrative, result_response = parse_structured_response(plain_text)

        # Should return original text as-is
        self.assertEqual(result_narrative, plain_text)
        self.assertIsInstance(result_response, NarrativeResponse)
        self.assertEqual(result_response.narrative, plain_text)
        self.assertEqual(result_response.entities_mentioned, [])
        self.assertEqual(result_response.location_confirmed, "Unknown")

    def test_successful_json_parsing(self):
        """
        Test normal case where JSON parsing succeeds without errors.

        This ensures the fix doesn't break the normal success path.
        """
        valid_json = """
        {
            "narrative": "The knight approaches the dragon's lair.",
            "entities_mentioned": ["Sir Knight", "Ancient Dragon"],
            "location_confirmed": "Dragon's Lair",
            "state_updates": {"dragon_encountered": true}
        }
        """

        result_narrative, result_response = parse_structured_response(valid_json)

        # Should parse successfully
        self.assertEqual(result_narrative, "The knight approaches the dragon's lair.")
        self.assertIsInstance(result_response, NarrativeResponse)
        self.assertEqual(
            result_response.entities_mentioned, ["Sir Knight", "Ancient Dragon"]
        )
        self.assertEqual(result_response.location_confirmed, "Dragon's Lair")
        self.assertEqual(result_response.state_updates, {"dragon_encountered": True})

    def test_regression_no_raw_json_in_narrative(self):
        """
        Regression test to ensure users never see raw JSON structures.

        This is the core issue that was reported - users seeing JSON output
        instead of narrative text in their campaign responses.
        """
        # Test various JSON structures that could be returned raw
        test_cases = [
            '{"narrative": "Test story", "entities_mentioned": []}',
            '{\n  "narrative": "Multi-line\\nstory",\n  "location_confirmed": "Test"\n}',
            '{"narrative": "Story with \\"quotes\\"", "state_updates": {}}',
        ]

        for test_json in test_cases:
            with self.subTest(json_input=test_json[:50] + "..."):
                result_narrative, result_response = parse_structured_response(test_json)

                # The core fix: narrative should never contain JSON structure
                self.assertNotIn(
                    '"narrative":',
                    result_narrative,
                    f"Narrative should not contain JSON structure: {result_narrative}",
                )
                self.assertNotIn(
                    '"entities_mentioned":',
                    result_narrative,
                    f"Narrative should not contain JSON structure: {result_narrative}",
                )
                self.assertNotIn(
                    '"location_confirmed":',
                    result_narrative,
                    f"Narrative should not contain JSON structure: {result_narrative}",
                )
                self.assertNotIn(
                    '"state_updates":',
                    result_narrative,
                    f"Narrative should not contain JSON structure: {result_narrative}",
                )

    def test_narrative_extraction_from_partial_json(self):
        """Test extracting narrative from JSON-like text when parsing fails"""
        partial_json = 'Some prefix {"narrative": "The story continues with action", "other": "data"}'

        result_narrative, result_response = parse_structured_response(partial_json)

        # Should extract just the narrative
        self.assertEqual(result_narrative, "The story continues with action")
        self.assertNotIn("Some prefix", result_narrative)
        self.assertNotIn("other", result_narrative)

    def test_generic_code_block_extraction(self):
        """Test JSON extraction from generic code blocks without 'json' language identifier"""
        generic_code_block = """```
{
  "narrative": "Story text from generic code block",
  "entities_mentioned": ["Entity1"],
  "location_confirmed": "TestLocation",
  "state_updates": {}
}
```"""

        result_narrative, result_response = parse_structured_response(
            generic_code_block
        )

        # Should extract narrative from generic code block
        self.assertEqual(result_narrative, "Story text from generic code block")
        self.assertIsNotNone(result_response)
        self.assertEqual(result_response.entities_mentioned, ["Entity1"])
        self.assertEqual(result_response.location_confirmed, "TestLocation")

    def test_escaped_character_handling(self):
        """Test proper handling of escaped characters in narrative"""
        escaped_json = (
            '"narrative": "She said \\"Hello!\\"\\nNew line here\\nAnother line"'
        )

        result_narrative, result_response = parse_structured_response(escaped_json)

        # Should properly unescape characters
        self.assertIn('She said "Hello!"', result_narrative)
        self.assertIn("\n", result_narrative)  # Should have actual newlines
        self.assertEqual(result_narrative.count("\n"), 2)

    def test_json_cleanup_fallback(self):
        """Test the final cleanup fallback for malformed JSON"""
        malformed_json = (
            '{"narrative": "Story text", "entities_mentioned": ["Hero"], broken json...'
        )

        result_narrative, result_response = parse_structured_response(malformed_json)

        # Should clean up JSON syntax
        self.assertNotIn("{", result_narrative)
        self.assertNotIn('"narrative":', result_narrative)
        self.assertNotIn('["Hero"]', result_narrative)
        self.assertIn("Story text", result_narrative)


if __name__ == "__main__":
    unittest.main()
