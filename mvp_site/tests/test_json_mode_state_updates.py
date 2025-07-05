#!/usr/bin/env python3
"""Test that state updates work properly in JSON response mode."""

import os
import sys
import json
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


import logging_util
import unittest
from gemini_service import _process_structured_response
from narrative_response_schema import NarrativeResponse

class TestJsonModeStateUpdates(unittest.TestCase):
    """Test that state updates are properly extracted from JSON responses."""
    
    def setUp(self):
        """Set up test environment."""
        os.environ['TESTING'] = 'true'
        logging_util.basicConfig(level=logging_util.INFO)
    
    def test_json_response_with_state_updates(self):
        """Test that state updates from JSON response are appended to response text."""
        # Create a JSON response with state updates
        json_response = {
            "narrative": "Drake swings his sword at the goblin, dealing a mighty blow!",
            "entities_mentioned": ["Drake", "goblin"],
            "location_confirmed": "Forest clearing",
            "state_updates": {
                "npc_data": {
                    "goblin_001": {
                        "hp_current": 0,
                        "status": "Defeated"
                    }
                },
                "player_character_data": {
                    "xp_current": 150
                }
            }
        }
        
        raw_response = json.dumps(json_response)
        expected_entities = ["Drake", "goblin"]
        
        # Process the response
        result, structured_response = _process_structured_response(raw_response, expected_entities)
        
        # Check that narrative is included
        self.assertIn("Drake swings his sword", result)
        
        # Check that STATE_UPDATES_PROPOSED block is appended
        self.assertIn("[STATE_UPDATES_PROPOSED]", result)
        self.assertIn("[END_STATE_UPDATES_PROPOSED]", result)
        
        # Check that state updates are included
        self.assertIn('"npc_data"', result)
        self.assertIn('"goblin_001"', result)
        self.assertIn('"hp_current": 0', result)
        self.assertIn('"player_character_data"', result)
        self.assertIn('"xp_current": 150', result)
        
        print("✅ JSON response with state updates properly converted")
    
    def test_json_response_without_state_updates(self):
        """Test that responses without state updates work correctly."""
        # Create a JSON response without state updates
        json_response = {
            "narrative": "Drake explores the peaceful forest.",
            "entities_mentioned": ["Drake"],
            "location_confirmed": "Forest"
        }
        
        raw_response = json.dumps(json_response)
        expected_entities = ["Drake"]
        
        # Process the response
        result, structured_response = _process_structured_response(raw_response, expected_entities)
        
        # Check that narrative is included
        self.assertIn("Drake explores the peaceful forest", result)
        
        # Check that no STATE_UPDATES_PROPOSED block is added
        self.assertNotIn("[STATE_UPDATES_PROPOSED]", result)
        
        print("✅ JSON response without state updates handled correctly")
    
    def test_json_response_with_empty_state_updates(self):
        """Test that empty state updates are handled correctly."""
        # Create a JSON response with empty state updates
        json_response = {
            "narrative": "The scene is quiet.",
            "entities_mentioned": [],
            "location_confirmed": "Town square",
            "state_updates": {}
        }
        
        raw_response = json.dumps(json_response)
        expected_entities = []
        
        # Process the response
        result, structured_response = _process_structured_response(raw_response, expected_entities)
        
        # Check that narrative is included
        self.assertIn("The scene is quiet", result)
        
        # Check that no STATE_UPDATES_PROPOSED block is added for empty updates
        self.assertNotIn("[STATE_UPDATES_PROPOSED]", result)
        
        print("✅ Empty state updates handled correctly")

if __name__ == '__main__':
    unittest.main()