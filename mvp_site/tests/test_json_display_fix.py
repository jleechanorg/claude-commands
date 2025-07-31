#!/usr/bin/env python3
"""
Unit test for the JSON display bug fix in narrative_response_schema.py

This test validates that the indentation fix in narrative_response_schema.py:142
correctly handles fallback scenarios when NarrativeResponse creation fails.
"""

import os
import sys
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

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
        assert result_narrative is not None, "Should return narrative text, not None"
        assert isinstance(result_narrative, str), "Should return narrative as string"

        # Critical assertion: should return the extracted narrative, not raw JSON
        assert "Scene #10" in result_narrative, "Should contain the actual narrative text"
        assert "DM MODE" in result_narrative, "Should contain the narrative content"
        assert '"narrative":' not in result_narrative, "Should NOT contain raw JSON structure"
        assert '"entities_mentioned":' not in result_narrative, "Should NOT contain raw JSON structure"

        # Response object should be valid fallback
        assert isinstance(result_response, NarrativeResponse), "Should return NarrativeResponse object"
        assert result_response.narrative == result_narrative, "Response narrative should match returned narrative"
        assert result_response.entities_mentioned == ["Ser Caius of House Varrick", "Ser Bastion"]
        assert result_response.location_confirmed == "Starfall Command Barracks, Aeterna"

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
        assert result_narrative is not None
        assert "DM MODE" in result_narrative
        assert "Understanding confirmed" in result_narrative
        assert "```json" not in result_narrative, "Should strip markdown formatting"
        assert '"narrative":' not in result_narrative, "Should extract narrative, not return raw JSON"

        # Response object should be properly constructed
        assert isinstance(result_response, NarrativeResponse)
        assert result_response.entities_mentioned == ["Test Entity"]

    def test_plain_text_fallback(self):
        """
        Test the final fallback for non-JSON text.

        When input is not JSON at all, should return the original text
        with a basic NarrativeResponse wrapper.
        """
        plain_text = "This is just plain narrative text, not JSON at all."

        result_narrative, result_response = parse_structured_response(plain_text)

        # Should return original text as-is
        assert result_narrative == plain_text
        assert isinstance(result_response, NarrativeResponse)
        assert result_response.narrative == plain_text
        assert result_response.entities_mentioned == []
        assert result_response.location_confirmed == "Unknown"

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
        assert result_narrative == "The knight approaches the dragon's lair."
        assert isinstance(result_response, NarrativeResponse)
        assert result_response.entities_mentioned == ["Sir Knight", "Ancient Dragon"]
        assert result_response.location_confirmed == "Dragon's Lair"
        assert result_response.state_updates == {"dragon_encountered": True}

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
                assert '"narrative":' not in result_narrative, f"Narrative should not contain JSON structure: {result_narrative}"
                assert '"entities_mentioned":' not in result_narrative, f"Narrative should not contain JSON structure: {result_narrative}"
                assert '"location_confirmed":' not in result_narrative, f"Narrative should not contain JSON structure: {result_narrative}"
                assert '"state_updates":' not in result_narrative, f"Narrative should not contain JSON structure: {result_narrative}"

    def test_narrative_extraction_from_partial_json(self):
        """Test extracting narrative from JSON-like text when parsing fails"""
        partial_json = 'Some prefix {"narrative": "The story continues with action", "other": "data"}'

        result_narrative, result_response = parse_structured_response(partial_json)

        # Should extract just the narrative
        assert result_narrative == "The story continues with action"
        assert "Some prefix" not in result_narrative
        assert "other" not in result_narrative

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
        assert result_narrative == "Story text from generic code block"
        assert result_response is not None
        assert result_response.entities_mentioned == ["Entity1"]
        assert result_response.location_confirmed == "TestLocation"

    def test_escaped_character_handling(self):
        """Test proper handling of escaped characters in narrative"""
        escaped_json = (
            '"narrative": "She said \\"Hello!\\"\\nNew line here\\nAnother line"'
        )

        result_narrative, result_response = parse_structured_response(escaped_json)

        # Should properly unescape characters
        assert 'She said "Hello!"' in result_narrative
        assert "\n" in result_narrative  # Should have actual newlines
        assert result_narrative.count("\n") == 2

    def test_json_cleanup_fallback(self):
        """Test the final cleanup fallback for malformed JSON"""
        malformed_json = (
            '{"narrative": "Story text", "entities_mentioned": ["Hero"], broken json...'
        )

        result_narrative, result_response = parse_structured_response(malformed_json)

        # Should clean up JSON syntax
        assert "{" not in result_narrative
        assert '"narrative":' not in result_narrative
        assert '["Hero"]' not in result_narrative
        assert "Story text" in result_narrative


if __name__ == "__main__":
    unittest.main()
