#!/usr/bin/env python3
"""
Test code execution artifact handling in JSON parsing.

This test verifies that parse_structured_response() correctly handles
responses from Gemini when code execution mode is used, which can include
whitespace or code output before the actual JSON response.
"""

import json
import os
import sys
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from mvp_site.narrative_response_schema import NarrativeResponse, parse_structured_response


class TestCodeExecutionJSONParsing(unittest.TestCase):
    """Test JSON parsing with code execution artifacts"""

    def test_code_execution_whitespace_prefix(self):
        """Test that whitespace before JSON is removed"""
        # Simulate code execution output with leading whitespace/newlines
        response_text = "\n\n   \n{\"narrative\": \"The hero enters the tavern.\", \"entities_mentioned\": [\"hero\"], \"location_confirmed\": \"Tavern\"}"

        narrative, response = parse_structured_response(response_text)

        # Should successfully parse despite leading whitespace
        assert isinstance(response, NarrativeResponse)
        assert narrative == "The hero enters the tavern."
        assert response.entities_mentioned == ["hero"]
        assert response.location_confirmed == "Tavern"

    def test_code_execution_stdout_prefix(self):
        """Test that code execution stdout output before JSON is removed"""
        # Simulate code execution that outputs text before JSON
        # This matches the actual error pattern: "Expecting value: line 1 column 2 (char 1)"
        # Note: When array comes first, we should find the JSON object (not parse the array)
        response_text = '[{"notation": "1d20+5", "rolls": [12], "total": 17}]\n{"narrative": "You roll the dice and succeed.", "entities_mentioned": [], "location_confirmed": "Unknown"}'

        narrative, response = parse_structured_response(response_text)

        # Should successfully parse by finding the JSON object after the array
        # The fix prefers { over [ so it should find the object, not the array
        assert isinstance(response, NarrativeResponse)
        assert narrative == "You roll the dice and succeed."
        assert response.entities_mentioned == []

    def test_code_execution_mixed_output(self):
        """Test handling of mixed code execution output and JSON"""
        # Simulate realistic code execution scenario from production logs
        # Code execution outputs dice roll JSON array, then main response JSON object follows
        # The fix should prefer the JSON object { over the array [
        response_text = 'stdout: [{"notation": "1d20+799", "rolls": [9], "total": 808}]\n{"narrative": "The Morninglord deletion proceeds.", "entities_mentioned": ["Morninglord"], "location_confirmed": "Celestial Plane"}'

        narrative, response = parse_structured_response(response_text)

        # Should successfully parse the main JSON object (not the array)
        assert isinstance(response, NarrativeResponse)
        assert "Morninglord deletion" in narrative
        assert "Morninglord" in response.entities_mentioned

    def test_code_execution_tab_prefix(self):
        """Test that tab characters before JSON are handled"""
        response_text = "\t\t{\"narrative\": \"Tab-prefixed response.\", \"entities_mentioned\": []}"

        narrative, response = parse_structured_response(response_text)

        assert isinstance(response, NarrativeResponse)
        assert narrative == "Tab-prefixed response."

    def test_code_execution_carriage_return_prefix(self):
        """Test that carriage return characters are handled"""
        response_text = "\r\r\n{\"narrative\": \"CR-prefixed response.\", \"entities_mentioned\": []}"

        narrative, response = parse_structured_response(response_text)

        assert isinstance(response, NarrativeResponse)
        assert narrative == "CR-prefixed response."

    def test_code_execution_with_array_first(self):
        """Test when code execution outputs an array before the main JSON object"""
        # This matches production pattern where dice rolls come first as array
        # The fix prefers { over [ so it should find the object, not parse the array
        response_text = '[{"dice": "1d20", "result": 15}]\n{"narrative": "The dice roll completes.", "entities_mentioned": []}'

        narrative, response = parse_structured_response(response_text)

        # Should find and parse the JSON object (not the array)
        # The fix looks for { first, so it should skip the array and find the object
        assert isinstance(response, NarrativeResponse)
        assert narrative == "The dice roll completes."

    def test_code_execution_no_prefix_valid_json(self):
        """Test that valid JSON without prefix still works"""
        response_text = '{"narrative": "Normal response.", "entities_mentioned": []}'

        narrative, response = parse_structured_response(response_text)

        assert isinstance(response, NarrativeResponse)
        assert narrative == "Normal response."

    def test_code_execution_error_position_one(self):
        """Test the specific error pattern seen in production: 'Expecting value: line 1 column 2 (char 1)'"""
        # This error occurs when response starts with a single character before JSON
        # Position 1 means the second character, suggesting first char is invalid
        response_text = ' \n{"narrative": "Fixed response.", "entities_mentioned": []}'

        narrative, response = parse_structured_response(response_text)

        # Should successfully parse by removing the prefix
        assert isinstance(response, NarrativeResponse)
        assert narrative == "Fixed response."
        assert "Invalid JSON response received" not in narrative

    def test_code_execution_production_scenario(self):
        """Test realistic production scenario based on GCP logs"""
        # Based on logs showing code execution with stdout containing valid JSON
        # but main response having artifacts before JSON
        # Error: "Expecting value: line 1 column 2 (char 1)"
        response_text = '\n\n{"narrative": "Execute All Simultaneously - Finalize the Morninglord\'s deletion.", "entities_mentioned": ["Morninglord"], "location_confirmed": "Celestial Plane"}'

        narrative, response = parse_structured_response(response_text)

        # Should parse successfully
        assert isinstance(response, NarrativeResponse)
        assert "Morninglord" in narrative or "Morninglord" in response.entities_mentioned
        assert "Invalid JSON response received" not in narrative

    def test_code_execution_with_markdown_block(self):
        """Test that markdown code blocks still work with code execution artifacts"""
        response_text = '\n```json\n{"narrative": "In markdown block.", "entities_mentioned": []}\n```'

        narrative, response = parse_structured_response(response_text)

        assert isinstance(response, NarrativeResponse)
        assert narrative == "In markdown block."


if __name__ == "__main__":
    unittest.main()
