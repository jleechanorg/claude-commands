"""Test to reproduce the exact fallback logic bug causing raw JSON display."""

import os
import sys
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from narrative_response_schema import parse_structured_response


class TestFallbackLogicJsonBug(unittest.TestCase):
    """Test the specific fallback logic that can return partial JSON."""

    def test_malformed_god_mode_json_triggers_fallback(self):
        """Test that malformed God mode JSON triggers fallback logic."""
        # This is malformed JSON - missing closing brace, will trigger fallback
        malformed_god_mode_response = """{
    "narrative": "",
    "god_mode_response": "The gods have spoken and reality bends to their will.",
    "entities_mentioned": ["gods"],
    "location_confirmed": "Divine Realm",
    "state_updates": {
        "divine_intervention": true
    },
    "debug_info": {}"""  # Missing closing brace - malformed JSON

        # This should trigger the fallback logic
        narrative_text, structured_response = parse_structured_response(
            malformed_god_mode_response
        )

        # CRITICAL BUG: The fallback logic may return JSON structure instead of clean text
        # Check that we don't get any JSON artifacts in the final output
        assert '"god_mode_response":' not in narrative_text, "Fallback should not return JSON keys"
        assert '"entities_mentioned":' not in narrative_text, "Fallback should not return JSON keys"
        assert '"state_updates":' not in narrative_text, "Fallback should not return JSON keys"
        assert '{"' not in narrative_text, "Fallback should not return JSON structure"
        assert '"}' not in narrative_text, "Fallback should not return JSON structure"

        # Should return clean readable text
        assert "The gods have spoken" in narrative_text, "Should extract the actual god mode response text"

    def test_incomplete_json_with_quotes_in_content(self):
        """Test JSON with escaped quotes that breaks parsing."""
        # This type of malformed JSON could trigger fallback cleanup that leaves artifacts
        problematic_response = """{
    "narrative": "",
    "god_mode_response": "He said \\"I will not yield\\" as darkness falls.",
    "entities_mentioned": ["he"],
    "location_confirmed": "Battlefield",
    "state_updates": {}"""  # Incomplete - no closing brace

        narrative_text, structured_response = parse_structured_response(
            problematic_response
        )

        # Should NOT contain JSON structure
        assert '"god_mode_response":' not in narrative_text
        assert '"entities_mentioned":' not in narrative_text
        assert '{"' not in narrative_text

        # Should contain the actual content with properly unescaped quotes
        assert 'He said "I will not yield"' in narrative_text
        assert "darkness falls" in narrative_text

    def test_fallback_with_aggressive_cleanup_scenario(self):
        """Test the aggressive cleanup path that could leave JSON artifacts."""
        # Create a scenario where NARRATIVE_PATTERN.search fails but we have JSON structure
        # This should trigger the aggressive cleanup path
        json_without_extractable_narrative = """{
    "narrative_field": "Wrong field name - pattern won't match",
    "god_mode_response": "Power flows through the ancient artifact.",
    "entities_mentioned": ["artifact"],
    "state_updates": {"artifact_power": "activated"}
    "debug_info": {"notes": "test"}"""  # Malformed - missing comma, wrong narrative field

        narrative_text, structured_response = parse_structured_response(
            json_without_extractable_narrative
        )

        # This triggers the aggressive cleanup - should NOT leave JSON structure
        assert '"god_mode_response":' not in narrative_text, "Aggressive cleanup should remove all JSON keys"
        assert '"entities_mentioned":' not in narrative_text, "Aggressive cleanup should remove all JSON keys"
        assert '"state_updates":' not in narrative_text, "Aggressive cleanup should remove all JSON keys"
        assert "artifact_power" not in narrative_text, "Aggressive cleanup should remove nested JSON content"

        # Should contain readable text
        assert "Power flows through" in narrative_text
        assert "ancient artifact" in narrative_text

    def test_mixed_content_json_structure(self):
        """Test mixed content that current fallback might not handle well."""
        # Scenario: JSON with text that looks like JSON keys but isn't
        mixed_content = """{
    "narrative": "",
    "god_mode_response": "The wizard casts a spell with \\"mana_cost\\": 50 points.",
    "entities_mentioned": ["wizard"],
    "state_updates": {"wizard_mana": 50}
}"""  # This is valid JSON but contains JSON-like text in the content

        narrative_text, structured_response = parse_structured_response(mixed_content)

        # Should parse correctly and return the god mode response
        assert narrative_text == 'The wizard casts a spell with "mana_cost": 50 points.'

        # The content should preserve the internal JSON-like text but not have structure artifacts
        assert '"god_mode_response":' not in narrative_text
        assert '"mana_cost":' in narrative_text  # This should be preserved as content


if __name__ == "__main__":
    unittest.main()
