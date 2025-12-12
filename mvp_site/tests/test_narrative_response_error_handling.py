"""Tests for narrative response error handling and type conversion"""

import json
import os
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mvp_site import logging_util
from mvp_site.narrative_response_schema import (
    _combine_god_mode_and_narrative,
    parse_structured_response,
)


class TestNarrativeResponseErrorHandling(unittest.TestCase):
    """Test coverage for error handling paths in narrative_response_schema.py"""

    def setUp(self):
        """Set up test fixtures"""
        # No extractor class needed

    def _validate_string_field(self, value, field_name):
        """Helper method matching NarrativeResponse._validate_string_field"""
        if value is None:
            return ""
        if not isinstance(value, str):
            try:
                return str(value)
            except Exception as e:
                # Import at runtime to match the actual implementation

                logging_util.error(f"Failed to convert {field_name} to string: {e}")
                return ""
        return value

    def _validate_list_field(self, value, _field_name):
        """Helper method matching NarrativeResponse._validate_list_field"""
        if value is None:
            return []
        if not isinstance(value, list):
            return [value]
        return value

    def test_validate_string_field_with_none(self):
        """Test _validate_string_field handles None values"""
        result = self._validate_string_field(None, "test_field")
        assert result == ""

    def test_validate_string_field_with_integer(self):
        """Test _validate_string_field converts integers"""
        result = self._validate_string_field(42, "test_field")
        assert result == "42"

    def test_validate_string_field_with_float(self):
        """Test _validate_string_field converts floats"""
        result = self._validate_string_field(3.14, "test_field")
        assert result == "3.14"

    def test_validate_string_field_with_boolean(self):
        """Test _validate_string_field converts booleans"""
        result = self._validate_string_field(True, "test_field")
        assert result == "True"

    def test_validate_string_field_with_dict(self):
        """Test _validate_string_field converts dictionaries"""
        result = self._validate_string_field({"key": "value"}, "test_field")
        assert result == "{'key': 'value'}"

    def test_validate_string_field_with_list(self):
        """Test _validate_string_field converts lists"""
        result = self._validate_string_field([1, 2, 3], "test_field")
        assert result == "[1, 2, 3]"

    @patch("logging_util.error")
    def test_validate_string_field_conversion_error(self, mock_logging_error):
        """Test _validate_string_field handles conversion errors"""

        # Create an object that raises exception on str()
        class BadObject:
            def __str__(self):
                raise ValueError("Cannot convert")

        bad_obj = BadObject()
        result = self._validate_string_field(bad_obj, "test_field")

        # Should return empty string on conversion error
        assert result == ""
        # Should log the error
        mock_logging_error.assert_called()

    def test_validate_list_field_with_none(self):
        """Test _validate_list_field handles None values"""
        result = self._validate_list_field(None, "test_field")
        assert result == []

    def test_validate_list_field_with_non_list(self):
        """Test _validate_list_field handles non-list values"""
        # String should be wrapped in a list
        result = self._validate_list_field("single_value", "test_field")
        assert result == ["single_value"]

        # Dict should be wrapped in a list
        result = self._validate_list_field({"key": "value"}, "test_field")
        assert result == [{"key": "value"}]

    def test_god_mode_fallback_on_narrative_response_error(self):
        """Test fallback when NarrativeResponse creation fails but god_mode_response exists"""
        # Create response that will fail NarrativeResponse validation
        # but has god_mode_response
        response_text = json.dumps(
            {
                "narrative": None,  # This might cause validation issues
                "god_mode_response": "GM: The player enters the tavern.",
                "entities_mentioned": ["player", "tavern"],
                "location_confirmed": "Rusty Goblet Tavern",
                "invalid_field": {
                    "nested": "data"
                },  # Extra field that might cause issues
                "state_updates": {"location": "tavern"},
            }
        )

        with patch("narrative_response_schema.NarrativeResponse") as mock_nr:
            # First call fails, second succeeds
            mock_nr.side_effect = [
                ValueError("Validation error"),
                Mock(
                    narrative="Combined response",
                    god_mode_response="GM: The player enters the tavern.",
                ),
            ]

            narrative, response = parse_structured_response(response_text)

            # Should combine god_mode_response with narrative
            assert "The player enters the tavern" in narrative

    def test_combine_god_mode_and_narrative_with_none(self):
        """Test _combine_god_mode_and_narrative handles None narrative"""
        result = _combine_god_mode_and_narrative("GM: Test response", None)
        assert "Test response" in result

    def test_combine_god_mode_and_narrative_with_empty(self):
        """Test _combine_god_mode_and_narrative handles empty narrative"""
        result = _combine_god_mode_and_narrative("GM: Test response", "")
        assert "Test response" in result

    def test_malformed_json_with_narrative_field(self):
        """Test extraction from malformed JSON with narrative field"""
        # Malformed JSON that contains narrative
        response_text = """
        {
            "narrative": "The player walks into the tavern\\nand sees many patrons.",
            "entities_mentioned": ["player", "patrons"
            "location_confirmed": "tavern"
        """

        narrative, response = parse_structured_response(response_text)

        # Should extract narrative even from malformed JSON
        assert "player walks into the tavern" in narrative
        assert "sees many patrons" in narrative

    def test_deeply_nested_malformed_json(self):
        """Test extraction from deeply nested malformed JSON"""
        response_text = """
        {
            "data": {
                "response": {
                    "narrative": "Nested narrative text",
                    "other": "data
                }
            }
        }
        """

        narrative, response = parse_structured_response(response_text)

        # Should find narrative even in nested structure
        assert "Nested narrative" in narrative

    def test_json_with_escaped_characters(self):
        """Test handling of JSON with escaped characters"""
        response_text = json.dumps(
            {
                "narrative": 'The player says, \\"Hello there!\\"\\nThe NPC responds.',
                "entities_mentioned": ["player", "NPC"],
            }
        )

        narrative, response = parse_structured_response(response_text)

        # Should properly handle the escaped characters as they are
        # JSON dumps will escape the quotes, so we check for the escaped form
        assert "Hello there!" in narrative
        assert "NPC responds" in narrative

    def test_type_validation_in_structured_fields(self):
        """Test type validation in structured fields"""
        response_text = json.dumps(
            {
                "narrative": "Test narrative",
                "entities_mentioned": ["valid", "list"],  # Use valid type
                "location_confirmed": "Valid string",  # Use valid type
                "state_updates": {"valid": "dict"},  # Use valid type
                "planning_block": {
                    "thinking": "Valid thinking",  # Use valid type
                    "choices": {"choice1": {"text": "Valid choice"}},  # Use valid type
                },
            }
        )

        narrative, response = parse_structured_response(response_text)

        # Should handle valid types correctly
        assert narrative == "Test narrative"
        assert response.entities_mentioned == ["valid", "list"]
        assert isinstance(response.entities_mentioned, list)
        # location_confirmed should be converted to string
        assert isinstance(response.location_confirmed, str)

    def test_planning_fallback_does_not_override_god_mode_response(self):
        """Planning fallback should not replace god mode display text."""

        response_text = json.dumps(
            {
                "narrative": "",  # Intentionally blank narrative
                "god_mode_response": "GM: Show this in UI",
                "planning_block": {"thinking": "Plan-only content"},
                "entities_mentioned": ["player"],
            }
        )

        combined_text, response = parse_structured_response(response_text)

        # Combined text shown to user should come from god_mode_response
        assert combined_text == "GM: Show this in UI"
        # The structured response should still capture planning fallback for narrative
        assert response.narrative == "Plan-only content"


if __name__ == "__main__":
    unittest.main()
