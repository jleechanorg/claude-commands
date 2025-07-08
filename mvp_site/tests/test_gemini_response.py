"""
Test-Driven Development: Tests for GeminiResponse object

These tests define the expected behavior for the GeminiResponse object
that will clean up the architecture between gemini_service and main.py.

Written FIRST before implementation following TDD principles.
"""

import unittest
import sys
import os
from unittest.mock import Mock

# Add the parent directory to the Python path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from narrative_response_schema import NarrativeResponse


class TestGeminiResponse(unittest.TestCase):
    """Test cases for GeminiResponse object."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_narrative = "The brave knight looked around the tavern."
        # raw_response field removed - only clean narrative and structured response needed
        
        # Mock structured response
        self.mock_structured_response = Mock(spec=NarrativeResponse)
        self.mock_structured_response.debug_info = {
            "dm_notes": ["Player seems cautious"],
            "dice_rolls": ["Perception: 1d20+3 = 15"],
            "resources": "HD: 2/3, Spells: L1 1/2",
            "state_rationale": "Updated HP after healing"
        }
        self.mock_structured_response.state_updates = {
            "player_character_data": {"hp_current": 18}
        }
        self.mock_structured_response.entities_mentioned = ["knight", "tavern"]
        self.mock_structured_response.location_confirmed = "Silver Stag Tavern"
    
    def test_gemini_response_creation(self):
        """Test creating a GeminiResponse object."""
        from gemini_response import GeminiResponse
        
        response = GeminiResponse.create(
            narrative_text=self.sample_narrative,
            structured_response=self.mock_structured_response,
        )
        
        # Core fields should be set
        self.assertEqual(response.narrative_text, self.sample_narrative)
        self.assertEqual(response.structured_response, self.mock_structured_response)
        # raw_response field removed - response only contains clean narrative
        
        # Should have debug tags detection
        self.assertIsInstance(response.debug_tags_present, dict)
        self.assertIn('dm_notes', response.debug_tags_present)
        self.assertIn('dice_rolls', response.debug_tags_present)
        self.assertIn('state_changes', response.debug_tags_present)
    
    def test_debug_tags_detection_with_content(self):
        """Test debug tags are properly detected when content exists."""
        from gemini_response import GeminiResponse
        
        response = GeminiResponse.create(
            narrative_text=self.sample_narrative,
            structured_response=self.mock_structured_response,
        )
        
        # Should detect dm_notes and dice_rolls from structured response
        self.assertTrue(response.debug_tags_present['dm_notes'])
        self.assertTrue(response.debug_tags_present['dice_rolls'])
        
        # has_debug_content should be True
        self.assertTrue(response.has_debug_content)
    
    def test_debug_tags_detection_no_content(self):
        """Test debug tags detection when no debug content exists."""
        from gemini_response import GeminiResponse
        
        empty_structured_response = Mock(spec=NarrativeResponse)
        empty_structured_response.debug_info = {
            "dm_notes": [],
            "dice_rolls": [],
            "resources": "HD: 2/3",
            "state_rationale": ""
        }
        
        response = GeminiResponse.create(
            narrative_text=self.sample_narrative,
            structured_response=empty_structured_response,
        )
        
        # Should detect no debug content
        self.assertFalse(response.debug_tags_present['dm_notes'])
        self.assertFalse(response.debug_tags_present['dice_rolls'])
        
        # has_debug_content should be False
        self.assertFalse(response.has_debug_content)
    
    def test_state_updates_property(self):
        """Test state_updates property returns correct data."""
        from gemini_response import GeminiResponse
        
        response = GeminiResponse.create(
            narrative_text=self.sample_narrative,
            structured_response=self.mock_structured_response,
        )
        
        expected_state_updates = {"player_character_data": {"hp_current": 18}}
        self.assertEqual(response.state_updates, expected_state_updates)
    
    def test_entities_mentioned_property(self):
        """Test entities_mentioned property returns correct data."""
        from gemini_response import GeminiResponse
        
        response = GeminiResponse.create(
            narrative_text=self.sample_narrative,
            structured_response=self.mock_structured_response,
        )
        
        expected_entities = ["knight", "tavern"]
        self.assertEqual(response.entities_mentioned, expected_entities)
    
    def test_location_confirmed_property(self):
        """Test location_confirmed property returns correct data."""
        from gemini_response import GeminiResponse
        
        response = GeminiResponse.create(
            narrative_text=self.sample_narrative,
            structured_response=self.mock_structured_response,
        )
        
        self.assertEqual(response.location_confirmed, "Silver Stag Tavern")
    
    def test_debug_info_property(self):
        """Test debug_info property returns correct data."""
        from gemini_response import GeminiResponse
        
        response = GeminiResponse.create(
            narrative_text=self.sample_narrative,
            structured_response=self.mock_structured_response,
        )
        
        expected_debug_info = {
            "dm_notes": ["Player seems cautious"],
            "dice_rolls": ["Perception: 1d20+3 = 15"],
            "resources": "HD: 2/3, Spells: L1 1/2",
            "state_rationale": "Updated HP after healing"
        }
        self.assertEqual(response.debug_info, expected_debug_info)
    
    def test_none_structured_response_handling(self):
        """Test GeminiResponse handles None structured_response gracefully."""
        from gemini_response import GeminiResponse
        
        response = GeminiResponse.create(
            narrative_text=self.sample_narrative,
            structured_response=None,
        )
        
        # Should handle None gracefully
        self.assertEqual(response.state_updates, {})
        self.assertEqual(response.entities_mentioned, [])
        self.assertEqual(response.location_confirmed, 'Unknown')
        self.assertEqual(response.debug_info, {})
        self.assertFalse(response.has_debug_content)
    
    def test_continue_story_returns_gemini_response(self):
        """Test that continue_story returns a GeminiResponse object."""
        from gemini_service import continue_story
        from gemini_response import GeminiResponse
        from game_state import GameState
        from unittest.mock import patch
        
        # Mock the API call
        with patch('gemini_service._call_gemini_api') as mock_api, \
             patch('gemini_service._get_text_from_response') as mock_get_text:
            
            mock_get_text.return_value = self.sample_raw_response
            mock_api.return_value = Mock()
            
            game_state = GameState()
            result = continue_story("test input", "character", [], game_state, [])
            
            # Should return GeminiResponse object
            self.assertIsInstance(result, GeminiResponse)
            self.assertIsInstance(result.narrative_text, str)
            self.assertIsNotNone(result.debug_tags_present)
    
    def test_get_initial_story_returns_gemini_response(self):
        """Test that get_initial_story returns a GeminiResponse object."""
        from gemini_service import get_initial_story
        from gemini_response import GeminiResponse
        from unittest.mock import patch
        
        # Mock the API call
        with patch('gemini_service._call_gemini_api') as mock_api, \
             patch('gemini_service._get_text_from_response') as mock_get_text:
            
            mock_get_text.return_value = self.sample_raw_response
            mock_api.return_value = Mock()
            
            result = get_initial_story("test prompt", [])
            
            # Should return GeminiResponse object
            self.assertIsInstance(result, GeminiResponse)
            self.assertIsInstance(result.narrative_text, str)
    
    def test_main_py_handles_gemini_response_object(self):
        """Test that main.py properly handles GeminiResponse objects."""
        from gemini_response import GeminiResponse
        
        # Create a mock GeminiResponse
        mock_response = GeminiResponse.create(
            narrative_text=self.sample_narrative,
            structured_response=self.mock_structured_response,
        )
        
        # Test that it has all the properties main.py needs
        self.assertTrue(hasattr(mock_response, 'narrative_text'))
        self.assertTrue(hasattr(mock_response, 'debug_tags_present'))
        self.assertTrue(hasattr(mock_response, 'state_updates'))
        self.assertTrue(hasattr(mock_response, 'has_debug_content'))
        
        # Test the debug monitoring interface
        debug_tags = mock_response.debug_tags_present
        self.assertIsInstance(debug_tags, dict)
        self.assertIn('dm_notes', debug_tags)
        self.assertIn('dice_rolls', debug_tags)
        self.assertIn('state_changes', debug_tags)
        
        # Test that any() works on debug_tags.values()
        has_any_debug = any(debug_tags.values())
        self.assertIsInstance(has_any_debug, bool)


if __name__ == '__main__':
    unittest.main()