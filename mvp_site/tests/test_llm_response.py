#!/usr/bin/env python3
"""
Test the new LLMResponse unified interface for TASK-121.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from llm_response import LLMResponse, GeminiLLMResponse, create_llm_response
from gemini_response import GeminiResponse
from narrative_response_schema import NarrativeResponse
import json


class TestLLMResponse(unittest.TestCase):
    """Test the unified LLMResponse interface."""
    
    def setUp(self):
        """Set up test data."""
        self.sample_narrative = "The dragon roars as you approach the castle gates."
        self.sample_raw = '{"narrative": "The dragon roars...", "state_updates": {"player_hp": 95}}'
        self.sample_model = "gemini-2.5-flash"
        
        # Create a mock structured response
        self.mock_structured = type('MockNarrativeResponse', (), {
            'state_updates': {'player_hp': 95, 'location': 'castle_gates'},
            'entities_mentioned': ['dragon', 'player'],
            'location_confirmed': 'castle_gates',
            'debug_info': {'dm_notes': 'Player seems confident'}
        })()
    
    def test_gemini_llm_response_creation(self):
        """Test creating GeminiLLMResponse directly."""
        # Use the legacy create method for direct GeminiLLMResponse creation
        # since the base class doesn't have the new create() method
        response = GeminiLLMResponse(
            narrative_text=self.sample_narrative,
            structured_response=self.mock_structured,
            model=self.sample_model,
            provider="gemini"
        )
        
        self.assertEqual(response.narrative_text, self.sample_narrative)
        self.assertEqual(response.provider, "gemini")
        self.assertEqual(response.model, self.sample_model)
        self.assertTrue(response.is_valid)
        
        # Test unified interface methods
        self.assertEqual(response.get_state_updates(), {'player_hp': 95, 'location': 'castle_gates'})
        self.assertEqual(response.get_entities_mentioned(), ['dragon', 'player'])
        self.assertEqual(response.get_location_confirmed(), 'castle_gates')
        self.assertEqual(response.get_debug_info(), {'dm_notes': 'Player seems confident'})
    
    def test_factory_function(self):
        """Test the factory function for creating responses."""
        response = create_llm_response(
            provider="gemini",
            narrative_text=self.sample_narrative,
            model=self.sample_model,
            structured_response=self.mock_structured
        )
        
        self.assertIsInstance(response, GeminiLLMResponse)
        self.assertEqual(response.provider, "gemini")
        self.assertEqual(response.narrative_text, self.sample_narrative)
    
    def test_backwards_compatibility(self):
        """Test that old GeminiResponse interface still works."""
        # Create a mock JSON response that would come from Gemini API
        mock_json = '''{
            "narrative": "The dragon roars as you approach the castle gates.",
            "state_updates": {"player_hp": 95, "location": "castle_gates"},
            "entities_mentioned": ["dragon", "player"],
            "location_confirmed": "castle_gates",
            "debug_info": {"dm_notes": "Player seems confident"}
        }'''
        
        response = GeminiResponse.create(
            raw_response_text=mock_json
        )
        
        # Test old property interface
        self.assertEqual(response.state_updates, {'player_hp': 95, 'location': 'castle_gates'})
        self.assertEqual(response.entities_mentioned, ['dragon', 'player'])
        self.assertEqual(response.location_confirmed, 'castle_gates')
        self.assertEqual(response.debug_info, {'dm_notes': 'Player seems confident'})
        
        # Test new method interface also works
        self.assertEqual(response.get_state_updates(), {'player_hp': 95, 'location': 'castle_gates'})
        self.assertEqual(response.get_entities_mentioned(), ['dragon', 'player'])
    
    def test_debug_tag_detection(self):
        """Test automatic debug tag detection."""
        response = GeminiLLMResponse(
            narrative_text=self.sample_narrative,
            structured_response=self.mock_structured,
            provider="gemini",
            model=self.sample_model
        )
        
        # Should detect dm_notes and state_changes
        self.assertTrue(response.debug_tags_present.get('dm_notes', False))
        self.assertTrue(response.debug_tags_present.get('state_changes', False))
        self.assertTrue(response.has_debug_content)
    
    def test_invalid_response_handling(self):
        """Test handling of invalid responses."""
        # Empty narrative should be invalid
        response = GeminiLLMResponse(
            narrative_text="",
            structured_response=None,
            provider="gemini",
            model=self.sample_model
        )
        
        self.assertFalse(response.is_valid)
        self.assertEqual(response.get_state_updates(), {})
        self.assertEqual(response.get_entities_mentioned(), [])
        self.assertEqual(response.get_location_confirmed(), 'Unknown')
    
    def test_to_dict_serialization(self):
        """Test converting response to dictionary for API usage."""
        response = GeminiLLMResponse(
            narrative_text=self.sample_narrative,
            structured_response=self.mock_structured,
            provider="gemini",
            model=self.sample_model
        )
        
        result = response.to_dict()
        
        self.assertEqual(result['narrative_text'], self.sample_narrative)
        self.assertEqual(result['provider'], 'gemini')
        self.assertEqual(result['state_updates'], {'player_hp': 95, 'location': 'castle_gates'})
        self.assertEqual(result['entities_mentioned'], ['dragon', 'player'])
        self.assertEqual(result['location_confirmed'], 'castle_gates')
        self.assertTrue(result['is_valid'])
    
    def test_unsupported_provider(self):
        """Test that unsupported providers raise appropriate errors."""
        with self.assertRaises(ValueError) as context:
            create_llm_response(
                provider="unsupported_provider",
                narrative_text=self.sample_narrative,
                    model="some-model"
            )
        
        self.assertIn("Unsupported LLM provider", str(context.exception))


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)