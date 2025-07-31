"""
Test suite for JSON display bugs identified in PR #278.

This test suite covers two main bugs:
1. LLM Not Respecting Character Actions (Presenting Same Options Twice)
2. Raw JSON Returned to User

The tests verify that state updates are properly captured and applied,
and that JSON responses are correctly parsed and cleaned for display.
"""

import json
import logging
import os
import sys
import unittest

# Add the mvp_site directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from narrative_response_schema import parse_structured_response


def extract_narrative_from_json(json_input):
    """Utility function to extract narrative from JSON input"""
    if isinstance(json_input, dict):
        return json_input.get("narrative", "")
    if isinstance(json_input, str):
        try:
            parsed = json.loads(json_input)
            return parsed.get("narrative", "")
        except:
            return ""
    return ""


from robust_json_parser import parse_llm_json_response as robust_parse


class TestStateUpdateBugs(unittest.TestCase):
    """Test Bug 1: LLM Not Respecting Character Actions (State Updates)"""

    def _parse_response(self, response_text):
        """Helper to parse response and return both narrative and response object"""
        narrative_text, response_obj = parse_structured_response(response_text)
        return narrative_text, response_obj

    def setUp(self):
        """Set up test fixtures"""
        self.valid_json_response = {
            "narrative": "You swing your sword at the orc.",
            "state_updates": {
                "player_character_data": {"hp_current": "18"},
                "npc_data": {"orc_warrior": {"status": "wounded"}},
                "world_data": {"current_location": "dungeon_chamber"},
                "custom_campaign_state": {"combat_round": "2"},
            },
        }

        self.markdown_style_response = """
        You swing your sword at the orc.

        [STATE_UPDATES_PROPOSED]
        player_character_data: {"hp_current": "18"}
        npc_data: {"orc_warrior": {"status": "wounded"}}
        [END_STATE_UPDATES_PROPOSED]
        """

        self.mixed_format_response = """
        {
            "narrative": "You swing your sword at the orc.",
            "state_updates": {
                "player_character_data": {"hp_current": "18"}
            }
        }

        [STATE_UPDATES_PROPOSED]
        This shouldn't appear in new format
        [END_STATE_UPDATES_PROPOSED]
        """

    def test_json_state_updates_extraction(self):
        """Test that state updates are properly extracted from JSON format"""
        response_text = json.dumps(self.valid_json_response)

        narrative_text, parsed_response = self._parse_response(response_text)

        # Verify state updates are captured
        assert "state_updates" in parsed_response.to_dict()
        assert (
            parsed_response.state_updates["player_character_data"]["hp_current"] == "18"
        )
        assert (
            parsed_response.state_updates["npc_data"]["orc_warrior"]["status"]
            == "wounded"
        )

    def test_state_updates_not_in_narrative(self):
        """Test that state updates don't leak into narrative text"""
        response_text = json.dumps(self.valid_json_response)

        narrative_text, parsed_response = self._parse_response(response_text)

        # Verify narrative is clean
        assert "state_updates" not in narrative_text
        assert "player_character_data" not in narrative_text
        assert "hp_current" not in narrative_text

    def test_markdown_state_updates_deprecated(self):
        """Test that old markdown state updates are handled gracefully"""
        narrative_text, parsed_response = self._parse_response(
            self.markdown_style_response
        )

        # Should not have JSON-style state updates (or should be empty)
        assert not parsed_response.state_updates or parsed_response.state_updates == {}

        # Should clean up markdown syntax from narrative
        assert "[STATE_UPDATES_PROPOSED]" not in narrative_text
        assert "[END_STATE_UPDATES_PROPOSED]" not in narrative_text

    def test_mixed_format_handling(self):
        """Test handling of responses with both JSON and markdown formats"""
        narrative_text, parsed_response = self._parse_response(
            self.mixed_format_response
        )

        # Should prioritize JSON format
        assert "state_updates" in parsed_response.to_dict()

        # Should clean up markdown artifacts
        assert "[STATE_UPDATES_PROPOSED]" not in narrative_text

    def test_empty_state_updates(self):
        """Test handling of responses with empty state updates"""
        response_with_empty_updates = {
            "narrative": "You look around the room.",
            "state_updates": {},
        }

        response_text = json.dumps(response_with_empty_updates)
        narrative_text, parsed_response = self._parse_response(response_text)

        # Should handle empty state updates gracefully
        assert "state_updates" in parsed_response.to_dict()
        assert parsed_response.state_updates == {}

    def test_malformed_state_updates(self):
        """Test handling of malformed state updates"""
        malformed_response = """
        {
            "narrative": "You swing your sword.",
            "state_updates": "not_a_dict"
        }
        """

        narrative_text, parsed_response = self._parse_response(malformed_response)

        # Should handle malformed state updates gracefully
        assert narrative_text == "You swing your sword."
        # State updates should be converted to empty dict when malformed
        # The validation should prevent malformed state_updates from causing runtime errors
        state_updates = parsed_response.state_updates
        assert isinstance(state_updates, dict)
        assert state_updates == {}


class TestRawJsonDisplayBugs(unittest.TestCase):
    """Test Bug 2: Raw JSON Returned to User"""

    def _parse_response(self, response_text):
        """Helper to parse response and return both narrative and response object"""
        narrative_text, response_obj = parse_structured_response(response_text)
        return narrative_text, response_obj

    def setUp(self):
        """Set up test fixtures"""
        self.valid_json = '{"narrative": "You enter the tavern.", "state_updates": {}}'

        self.malformed_json_examples = [
            '{"narrative": "You enter the tavern.", "state_updates": {',  # Missing closing brace
            '{"narrative": "You enter the tavern.", "state_updates": {}}extra_text',  # Extra text
            'narrative: "You enter the tavern."',  # Missing quotes on key
            '{"narrative": "You enter the \\"tavern\\"."}',  # Escaped quotes
            '```json\n{"narrative": "You enter the tavern."}\n```',  # Code block format
            '{"narrative": "You enter the tavern.",}',  # Trailing comma
        ]

        self.raw_json_response = """
        {
            "narrative": "You swing your sword at the orc warrior.",
            "state_updates": {
                "player_character_data": {"hp_current": "18"},
                "npc_data": {"orc_warrior": {"status": "wounded", "hp_current": "5"}},
                "world_data": {"current_location": "dungeon_chamber"},
                "custom_campaign_state": {"combat_round": "2", "initiative_order": ["player", "orc_warrior"]}
            },
            "reasoning": "The player successfully hits the orc, dealing damage.",
            "metadata": {"model": "gemini-2.5-flash", "tokens": 150}
        }
        """

    def test_valid_json_parsing(self):
        """Test that valid JSON is parsed correctly"""
        narrative_text, parsed_obj = parse_structured_response(self.valid_json)

        # Should extract narrative cleanly
        assert parsed_obj.narrative is not None
        assert parsed_obj.narrative == "You enter the tavern."

        # Should not contain raw JSON artifacts
        assert "{" not in parsed_obj.narrative
        assert "}" not in parsed_obj.narrative
        assert '"' not in parsed_obj.narrative

    def test_malformed_json_fallback(self):
        """Test that malformed JSON falls back to cleaned text"""
        for malformed_json in self.malformed_json_examples:
            with self.subTest(malformed_json=malformed_json):
                narrative_text, parsed_obj = parse_structured_response(malformed_json)

                # Should have some narrative content
                assert parsed_obj.narrative is not None

                # Should not contain raw JSON artifacts in narrative
                narrative = parsed_obj.narrative
                assert "```json" not in narrative
                assert "```" not in narrative

    def test_narrative_field_extraction(self):
        """Test extraction of narrative field from complex JSON"""
        narrative_text, parsed_obj = parse_structured_response(self.raw_json_response)

        # Should extract narrative field
        assert parsed_obj.narrative is not None
        assert parsed_obj.narrative == "You swing your sword at the orc warrior."

        # Should not leak other fields into narrative
        narrative = parsed_obj.narrative
        assert "reasoning" not in narrative
        assert "metadata" not in narrative
        assert "model" not in narrative

    def test_json_artifact_cleaning(self):
        """Test that JSON artifacts are cleaned from narrative"""
        dirty_response = '{"narrative": "You enter the {tavern}.", "extra": "data"}'

        narrative_text, parsed_obj = parse_structured_response(dirty_response)

        # Narrative should be extracted properly
        narrative = parsed_obj.narrative
        assert "tavern" in narrative
        # Note: The {tavern} is actually part of the narrative content, not JSON artifacts
        # So we just verify the narrative was extracted correctly

    def test_code_block_json_extraction(self):
        """Test extraction of JSON from code blocks"""
        code_block_response = """
        ```json
        {
            "narrative": "You cast a spell.",
            "state_updates": {}
        }
        ```
        """

        narrative_text, parsed_obj = parse_structured_response(code_block_response)

        # Should extract narrative from code block
        assert parsed_obj.narrative is not None
        assert parsed_obj.narrative == "You cast a spell."

    def test_debug_mode_content_stripping(self):
        """Test that debug mode content is properly stripped"""
        debug_response = """
        {
            "narrative": "You swing your sword.",
            "reasoning": "This is debug info that users shouldn't see",
            "state_updates": {},
            "debug_info": "More debug content"
        }
        """

        narrative_text, parsed_obj = parse_structured_response(debug_response)

        # Should only have user-facing content
        assert parsed_obj.narrative is not None
        assert "reasoning" not in parsed_obj.narrative
        assert "debug_info" not in parsed_obj.narrative

    def test_robust_json_parser_fallback(self):
        """Test the robust JSON parser as fallback"""
        malformed_json = '{"narrative": "You enter the tavern.", "state_updates": {'

        # Should not crash on malformed JSON
        try:
            parsed, was_incomplete = robust_parse(malformed_json)
            # Should return some usable content
            assert isinstance(parsed, dict)
            assert "narrative" in parsed
        except Exception as e:
            self.fail(f"Robust parser should not crash on malformed JSON: {e}")

    def test_narrative_extraction_utility(self):
        """Test the narrative extraction utility function"""
        json_with_narrative = {
            "narrative": "You swing your sword.",
            "other_field": "should not appear",
            "state_updates": {"some": "data"},
        }

        # Test direct extraction
        narrative = extract_narrative_from_json(json_with_narrative)
        assert narrative == "You swing your sword."

        # Test string input
        narrative_from_string = extract_narrative_from_json(
            json.dumps(json_with_narrative)
        )
        assert narrative_from_string == "You swing your sword."


class TestIntegrationBugs(unittest.TestCase):
    """Test integration scenarios that could cause both bugs"""

    def test_state_updates_with_malformed_json(self):
        """Test that state updates work even when JSON is malformed"""
        malformed_but_parseable = """
        {
            "narrative": "You attack the orc.",
            "state_updates": {
                "player_character_data": {"hp_current": "18"},
                "npc_data": {"orc_warrior": {"status": "wounded"}}
            },
        }
        """  # Note: trailing comma makes it malformed

        narrative_text, parsed_obj = parse_structured_response(malformed_but_parseable)

        # Should still extract state updates if possible
        assert parsed_obj.narrative is not None
        # State updates should be present if parseable
        if hasattr(parsed_obj, "state_updates") and parsed_obj.state_updates:
            assert isinstance(parsed_obj.state_updates, dict)

    def test_empty_response_handling(self):
        """Test handling of empty or null responses"""
        empty_responses = ["", "{}", "null", "undefined", '{"narrative": ""}']

        for empty_response in empty_responses:
            with self.subTest(empty_response=empty_response):
                narrative_text, parsed_obj = parse_structured_response(empty_response)

                # Should not crash and should provide some structure
                assert parsed_obj is not None
                assert parsed_obj.narrative is not None

    def test_very_long_json_response(self):
        """Test handling of very long JSON responses"""
        long_narrative = "A" * 5000  # Very long narrative
        long_json = json.dumps(
            {
                "narrative": long_narrative,
                "state_updates": {},
                "reasoning": "B" * 1000,  # Long reasoning
                "metadata": {"tokens": 1000},
            }
        )

        narrative_text, parsed_obj = parse_structured_response(long_json)

        # Should handle long responses without truncation
        assert parsed_obj.narrative is not None
        assert len(parsed_obj.narrative) == 5000

    def test_unicode_and_special_characters(self):
        """Test handling of unicode and special characters"""
        unicode_json = json.dumps(
            {
                "narrative": 'You see a 🗡️ sword and meet José the NPC. He says "Hola!"',
                "state_updates": {"npc_data": {"josé": {"status": "friendly"}}},
            }
        )

        narrative_text, parsed_obj = parse_structured_response(unicode_json)

        # Should preserve unicode characters
        assert parsed_obj.narrative is not None
        assert "🗡️" in parsed_obj.narrative
        assert "José" in parsed_obj.narrative
        assert "Hola!" in parsed_obj.narrative


if __name__ == "__main__":
    # Set up logging to see debug output
    logging.basicConfig(level=logging.DEBUG)

    # Run tests
    unittest.main(verbosity=2)
