"""
Test-Driven Development: Tests for GeminiResponse object

These tests define the expected behavior for the GeminiResponse object
that will clean up the architecture between gemini_service and main.py.

Updated for new API where GeminiResponse.create() takes raw response text.
"""

import json
import os
import sys
import unittest
from unittest.mock import Mock, patch

# Add the parent directory to the Python path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mvp_site'))

from game_state import GameState
from gemini_response import GeminiResponse
from gemini_service import continue_story
from gemini_service import get_initial_story
from narrative_response_schema import NarrativeResponse


class TestGeminiResponse(unittest.TestCase):
    """Test cases for GeminiResponse object."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_narrative = "The brave knight looked around the tavern."

        # Create mock raw JSON response
        self.sample_raw_response = json.dumps(
            {
                "narrative": self.sample_narrative,
                "debug_info": {
                    "dm_notes": ["Player seems cautious"],
                    "dice_rolls": ["Perception: 1d20+3 = 15"],
                    "resources": "HD: 2/3, Spells: L1 1/2",
                    "state_rationale": "Updated HP after healing",
                },
                "state_updates": {"player_character_data": {"hp_current": 18}},
                "entities_mentioned": ["knight", "tavern"],
                "location_confirmed": "Silver Stag Tavern",
            }
        )

    def test_gemini_response_creation(self):
        """Test creating a GeminiResponse object."""


        response = GeminiResponse.create(self.sample_raw_response)

        # Core fields should be set
        self.assertEqual(response.narrative_text, self.sample_narrative)
        self.assertIsNotNone(response.structured_response)

        # Should have debug tags detection
        self.assertIsInstance(response.debug_tags_present, dict)
        self.assertIn("dm_notes", response.debug_tags_present)
        self.assertIn("dice_rolls", response.debug_tags_present)
        self.assertIn("state_changes", response.debug_tags_present)

    def test_debug_tags_detection_with_content(self):
        """Test debug tags are properly detected when content exists."""


        response = GeminiResponse.create(self.sample_raw_response)

        # Should detect dm_notes and dice_rolls from structured response
        self.assertTrue(response.debug_tags_present["dm_notes"])
        self.assertTrue(response.debug_tags_present["dice_rolls"])

        # has_debug_content should be True
        self.assertTrue(response.has_debug_content)

    def test_debug_tags_detection_no_content(self):
        """Test debug tags detection when no debug content exists."""


        # Create raw response without debug content
        clean_raw_response = json.dumps(
            {
                "narrative": self.sample_narrative,
                "debug_info": {
                    "dm_notes": [],
                    "dice_rolls": [],
                    "resources": "HD: 2/3",
                    "state_rationale": "",
                },
                "entities_mentioned": ["knight", "tavern"],
                "location_confirmed": "Silver Stag Tavern",
            }
        )

        response = GeminiResponse.create(clean_raw_response)

        # Should detect no debug content
        self.assertFalse(response.debug_tags_present["dm_notes"])
        self.assertFalse(response.debug_tags_present["dice_rolls"])

        # has_debug_content should be False
        self.assertFalse(response.has_debug_content)

    def test_state_updates_property(self):
        """Test state_updates property returns correct data."""


        response = GeminiResponse.create(self.sample_raw_response)

        # Should return state updates from structured response
        self.assertEqual(
            response.state_updates, {"player_character_data": {"hp_current": 18}}
        )

    def test_entities_mentioned_property(self):
        """Test entities_mentioned property returns correct data."""


        response = GeminiResponse.create(self.sample_raw_response)

        # Should return entities from structured response
        self.assertEqual(response.entities_mentioned, ["knight", "tavern"])

    def test_location_confirmed_property(self):
        """Test location_confirmed property returns correct data."""


        response = GeminiResponse.create(self.sample_raw_response)

        # Should return location from structured response
        self.assertEqual(response.location_confirmed, "Silver Stag Tavern")

    def test_debug_info_property(self):
        """Test debug_info property returns correct data."""


        response = GeminiResponse.create(self.sample_raw_response)

        # Should return debug_info from structured response
        self.assertIsNotNone(response.debug_info)
        self.assertIn("dm_notes", response.debug_info)
        self.assertEqual(response.debug_info["dm_notes"], ["Player seems cautious"])

    def test_none_structured_response_handling(self):
        """Test GeminiResponse handles plain text gracefully."""


        # Test with plain text (no JSON)
        plain_response = self.sample_narrative
        response = GeminiResponse.create(plain_response)

        # Should extract the narrative
        self.assertEqual(response.narrative_text, self.sample_narrative)

        # Should have a structured response (even if empty)
        self.assertIsNotNone(response.structured_response)

        # Properties should return empty/default values gracefully
        self.assertEqual(response.state_updates, {})
        self.assertEqual(response.entities_mentioned, [])
        self.assertEqual(response.location_confirmed, "Unknown")  # Default value
        self.assertEqual(response.debug_info, {})

    @patch("gemini_service._call_gemini_api")
    @patch("gemini_service._get_text_from_response")
    def test_get_initial_story_returns_gemini_response(self, mock_get_text, mock_api):
        """Test that get_initial_story returns a GeminiResponse object."""


        # Setup mocks - return raw response text
        mock_api.return_value = Mock()
        mock_get_text.return_value = self.sample_raw_response

        # Call function
        result = get_initial_story(
            "Start a fantasy adventure", generate_companions=False
        )

        # Should return a GeminiResponse object
        self.assertEqual(type(result).__name__, "GeminiResponse")
        self.assertEqual(result.narrative_text, self.sample_narrative)

    @patch("gemini_service._call_gemini_api")
    @patch("gemini_service._get_text_from_response")
    def test_continue_story_returns_gemini_response(self, mock_get_text, mock_api):
        """Test that continue_story returns a GeminiResponse object."""



        # Setup mocks
        mock_api.return_value = Mock()
        mock_get_text.return_value = self.sample_raw_response

        game_state = GameState()
        story_context = []

        # Call function
        result = continue_story(
            user_input="I approach the barkeep",
            mode="story",
            story_context=story_context,
            current_game_state=game_state,
        )

        # Should return a GeminiResponse object
        self.assertEqual(type(result).__name__, "GeminiResponse")
        self.assertEqual(result.narrative_text, self.sample_narrative)

    def test_main_py_handles_gemini_response_object(self):
        """Test that main.py properly handles GeminiResponse objects."""
        # This is more of an integration test - checking the interface contract


        response = GeminiResponse.create(self.sample_raw_response)

        # Main.py expects these attributes/methods
        self.assertTrue(hasattr(response, "narrative_text"))
        self.assertTrue(hasattr(response, "state_updates"))
        self.assertTrue(hasattr(response, "debug_tags_present"))
        self.assertTrue(hasattr(response, "has_debug_content"))

        # Should be able to access all necessary data
        narrative = response.narrative_text
        updates = response.state_updates

        self.assertIsInstance(narrative, str)
        self.assertIsInstance(updates, dict)

    def test_legacy_create_method(self):
        """Test that the legacy create method still works for backwards compatibility."""


        # Mock structured response
        mock_structured = Mock(spec=NarrativeResponse)
        mock_structured.state_updates = {"hp": 10}
        mock_structured.entities_mentioned = ["dragon"]
        mock_structured.location_confirmed = "Dragon's Lair"
        mock_structured.debug_info = {"dm_notes": ["Boss fight"]}

        # Use legacy create method
        response = GeminiResponse.create_legacy(
            narrative_text="The dragon roars!", structured_response=mock_structured
        )

        # Should work correctly
        self.assertEqual(response.narrative_text, "The dragon roars!")
        self.assertEqual(response.state_updates, {"hp": 10})
        self.assertEqual(response.entities_mentioned, ["dragon"])


if __name__ == "__main__":
    unittest.main()
