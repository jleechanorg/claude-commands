"""Tests for action_resolution_utils helper functions.

Tests cover:
- get_action_resolution() fallback logic
- get_outcome_resolution() backward compat accessor
- add_action_resolution_to_response() API response builder
"""

import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mvp_site.action_resolution_utils import (
    add_action_resolution_to_response,
    get_action_resolution,
    get_outcome_resolution,
)


class TestActionResolutionUtils(unittest.TestCase):
    """Test action_resolution_utils helper functions"""

    def test_get_action_resolution_with_action_resolution(self):
        """Test get_action_resolution returns action_resolution when present"""
        mock_response = MagicMock()
        mock_response.action_resolution = {"player_input": "I attack", "interpreted_as": "attack"}
        mock_response.outcome_resolution = {"player_input": "legacy", "interpreted_as": "legacy"}

        result = get_action_resolution(mock_response)
        self.assertEqual(result["player_input"], "I attack")
        self.assertEqual(result["interpreted_as"], "attack")

    def test_get_action_resolution_falls_back_to_outcome_resolution(self):
        """Test get_action_resolution falls back to outcome_resolution when action_resolution missing"""
        mock_response = MagicMock()
        del mock_response.action_resolution  # Remove action_resolution
        mock_response.outcome_resolution = {"player_input": "The king agrees", "interpreted_as": "persuasion"}

        result = get_action_resolution(mock_response)
        self.assertEqual(result["player_input"], "The king agrees")
        self.assertEqual(result["interpreted_as"], "persuasion")

    def test_get_action_resolution_returns_empty_dict_when_neither_present(self):
        """Test get_action_resolution returns empty dict when neither field present"""
        mock_response = MagicMock()
        del mock_response.action_resolution
        del mock_response.outcome_resolution

        result = get_action_resolution(mock_response)
        self.assertEqual(result, {})

    def test_get_action_resolution_handles_none_action_resolution(self):
        """Test get_action_resolution handles None action_resolution by falling back"""
        mock_response = MagicMock()
        mock_response.action_resolution = None
        mock_response.outcome_resolution = {"player_input": "fallback", "interpreted_as": "fallback"}

        result = get_action_resolution(mock_response)
        self.assertEqual(result["player_input"], "fallback")

    def test_get_action_resolution_handles_empty_dict_action_resolution(self):
        """Test get_action_resolution preserves empty dict {} as present (not None)"""
        mock_response = MagicMock()
        mock_response.action_resolution = {}  # Empty dict is considered present
        mock_response.outcome_resolution = {"player_input": "should not use", "interpreted_as": "should not use"}

        result = get_action_resolution(mock_response)
        self.assertEqual(result, {})  # Should return empty dict, not fallback

    def test_get_action_resolution_handles_none_structured_response(self):
        """Test get_action_resolution handles None structured_response"""
        result = get_action_resolution(None)
        self.assertEqual(result, {})

    def test_get_outcome_resolution_with_outcome_resolution(self):
        """Test get_outcome_resolution returns outcome_resolution when present"""
        mock_response = MagicMock()
        mock_response.outcome_resolution = {"player_input": "The king agrees", "interpreted_as": "persuasion"}

        result = get_outcome_resolution(mock_response)
        self.assertEqual(result["player_input"], "The king agrees")
        self.assertEqual(result["interpreted_as"], "persuasion")

    def test_get_outcome_resolution_returns_empty_dict_when_missing(self):
        """Test get_outcome_resolution returns empty dict when outcome_resolution missing"""
        mock_response = MagicMock()
        del mock_response.outcome_resolution

        result = get_outcome_resolution(mock_response)
        self.assertEqual(result, {})

    def test_get_outcome_resolution_handles_none_outcome_resolution(self):
        """Test get_outcome_resolution handles None outcome_resolution"""
        mock_response = MagicMock()
        mock_response.outcome_resolution = None

        result = get_outcome_resolution(mock_response)
        self.assertEqual(result, {})

    def test_get_outcome_resolution_handles_none_structured_response(self):
        """Test get_outcome_resolution handles None structured_response"""
        result = get_outcome_resolution(None)
        self.assertEqual(result, {})

    def test_add_action_resolution_to_response_with_action_resolution(self):
        """Test add_action_resolution_to_response adds action_resolution to unified_response"""
        mock_response = MagicMock()
        mock_response.action_resolution = {"player_input": "I attack", "interpreted_as": "attack"}
        del mock_response.outcome_resolution

        unified_response = {}
        add_action_resolution_to_response(mock_response, unified_response)

        self.assertIn("action_resolution", unified_response)
        self.assertEqual(unified_response["action_resolution"]["player_input"], "I attack")
        self.assertNotIn("outcome_resolution", unified_response)

    def test_add_action_resolution_to_response_with_outcome_resolution(self):
        """Test add_action_resolution_to_response adds outcome_resolution to unified_response"""
        mock_response = MagicMock()
        del mock_response.action_resolution
        mock_response.outcome_resolution = {"player_input": "The king agrees", "interpreted_as": "persuasion"}

        unified_response = {}
        add_action_resolution_to_response(mock_response, unified_response)

        self.assertIn("outcome_resolution", unified_response)
        self.assertEqual(unified_response["outcome_resolution"]["player_input"], "The king agrees")
        self.assertNotIn("action_resolution", unified_response)

    def test_add_action_resolution_to_response_with_both_fields(self):
        """Test add_action_resolution_to_response adds both fields when both present"""
        mock_response = MagicMock()
        mock_response.action_resolution = {"player_input": "I attack", "interpreted_as": "attack"}
        mock_response.outcome_resolution = {"player_input": "legacy", "interpreted_as": "legacy"}

        unified_response = {}
        add_action_resolution_to_response(mock_response, unified_response)

        self.assertIn("action_resolution", unified_response)
        self.assertIn("outcome_resolution", unified_response)
        self.assertEqual(unified_response["action_resolution"]["player_input"], "I attack")
        self.assertEqual(unified_response["outcome_resolution"]["player_input"], "legacy")

    def test_add_action_resolution_to_response_handles_none_values(self):
        """Test add_action_resolution_to_response skips None values"""
        mock_response = MagicMock()
        mock_response.action_resolution = None
        mock_response.outcome_resolution = None

        unified_response = {}
        add_action_resolution_to_response(mock_response, unified_response)

        self.assertNotIn("action_resolution", unified_response)
        self.assertNotIn("outcome_resolution", unified_response)

    def test_add_action_resolution_to_response_type_coercion(self):
        """Test add_action_resolution_to_response coerces non-dict to empty dict"""
        mock_response = MagicMock()
        mock_response.action_resolution = "not a dict"  # Invalid type
        mock_response.outcome_resolution = ["not a dict"]  # Invalid type

        unified_response = {}
        add_action_resolution_to_response(mock_response, unified_response)

        # Should coerce to empty dict
        self.assertIn("action_resolution", unified_response)
        self.assertIn("outcome_resolution", unified_response)
        self.assertEqual(unified_response["action_resolution"], {})
        self.assertEqual(unified_response["outcome_resolution"], {})

    def test_add_action_resolution_to_response_handles_empty_dict(self):
        """Test add_action_resolution_to_response includes empty dict {} as valid"""
        mock_response = MagicMock()
        mock_response.action_resolution = {}  # Empty dict is valid
        del mock_response.outcome_resolution

        unified_response = {}
        add_action_resolution_to_response(mock_response, unified_response)

        self.assertIn("action_resolution", unified_response)
        self.assertEqual(unified_response["action_resolution"], {})

    def test_add_action_resolution_to_response_handles_none_structured_response(self):
        """Test add_action_resolution_to_response handles None structured_response"""
        unified_response = {}
        add_action_resolution_to_response(None, unified_response)

        self.assertNotIn("action_resolution", unified_response)
        self.assertNotIn("outcome_resolution", unified_response)

    def test_add_action_resolution_to_response_handles_missing_hasattr(self):
        """Test add_action_resolution_to_response handles objects without hasattr support"""
        # Create object that doesn't support hasattr (edge case)
        class NoHasattr:
            def __getattr__(self, name):
                raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

        mock_response = NoHasattr()
        unified_response = {}
        add_action_resolution_to_response(mock_response, unified_response)

        # Should handle gracefully without crashing
        self.assertNotIn("action_resolution", unified_response)
        self.assertNotIn("outcome_resolution", unified_response)


if __name__ == "__main__":
    unittest.main()
