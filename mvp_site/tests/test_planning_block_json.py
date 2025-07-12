#!/usr/bin/env python3
"""
Consolidated tests for planning block JSON-first architecture.
Combines tests from test_planning_block_json_first_fix.py and test_planning_block_json_corruption_fix.py
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from narrative_response_schema import NarrativeResponse
from gemini_service import _validate_and_enforce_planning_block
from game_state import GameState
import constants


class TestPlanningBlockJSON(unittest.TestCase):
    """Test planning block JSON-first architecture"""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a minimal game state
        self.game_state = GameState()
        self.game_state.player_character_data = {'name': 'Test Hero'}
        self.game_state.world_data = {'current_location_name': 'Test Location'}
        
        # Sample response text
        self.response_text = "You enter the chamber. The air is thick with tension."
        
        # User input that triggers planning block
        self.user_input = "I want to think about my options"
        
        # Mock models and system instruction
        self.chosen_model = "gemini-2.5-flash"
        self.system_instruction = "Test system instruction"
    
    def test_planning_block_in_json_field_only(self):
        """Test that planning blocks should only be in JSON field, not narrative"""
        
        # Correct JSON-first architecture
        correct_narrative = """[CHARACTER CREATION - Step 1]

Scene #1: Excellent! I see you want to play as Astarion. Let's design Astarion with D&D 5e mechanics!

How would you like to design Astarion:"""
        
        correct_planning_block = {
            "thinking": "The player wants to create Astarion as their character. I need to offer character creation options.",
            "choices": {
                "ai_generated": {
                    "text": "AI Generated",
                    "description": "I'll create a complete D&D version based on their lore",
                    "risk_level": "safe"
                },
                "standard_dnd": {
                    "text": "Standard D&D",
                    "description": "You choose from D&D races and classes",
                    "risk_level": "safe"
                },
                "custom_class": {
                    "text": "Custom Class",
                    "description": "We'll create custom mechanics for their unique abilities",
                    "risk_level": "safe"
                }
            }
        }
        
        # Create structured response
        structured_response = NarrativeResponse(
            narrative=correct_narrative,
            planning_block=correct_planning_block
        )
        
        # Verify planning block content is NOT in narrative
        self.assertNotIn("**AIGenerated**", structured_response.narrative)
        self.assertNotIn("**StandardDND**", structured_response.narrative)
        self.assertNotIn("**CustomClass**", structured_response.narrative)
        
        # Verify planning block content IS in planning_block field as JSON
        self.assertIsInstance(structured_response.planning_block, dict)
        self.assertIn("choices", structured_response.planning_block)
        self.assertIn("ai_generated", structured_response.planning_block["choices"])
        self.assertIn("standard_dnd", structured_response.planning_block["choices"])
        self.assertIn("custom_class", structured_response.planning_block["choices"])
    
    def test_api_response_structure(self):
        """Test that API response has planning block in correct field"""
        
        # Simulate API response data structure
        api_response = {
            'success': True,
            'narrative': '[CHARACTER CREATION - Step 1]\n\nScene #1: Let\'s create your character!',
            constants.FIELD_PLANNING_BLOCK: {
                "thinking": "Player needs to choose character creation method.",
                "choices": {
                    "ai_generated": {
                        "text": "AI Generated",
                        "description": "AI creates the character"
                    },
                    "standard_dnd": {
                        "text": "Standard D&D",  
                        "description": "Use standard D&D rules"
                    },
                    "custom_class": {
                        "text": "Custom Class",
                        "description": "Create custom mechanics"
                    }
                }
            },
            'debug_mode': False,
            'sequence_id': 1
        }
        
        # Verify narrative doesn't contain planning block choices
        self.assertNotIn("AIGenerated", api_response['narrative'])
        
        # Verify planning block field contains choices as JSON
        self.assertIsInstance(api_response[constants.FIELD_PLANNING_BLOCK], dict)
        self.assertIn("choices", api_response[constants.FIELD_PLANNING_BLOCK])
        self.assertIn("ai_generated", api_response[constants.FIELD_PLANNING_BLOCK]["choices"])
    
    @patch('gemini_service._call_gemini_api')
    @patch('gemini_service._get_text_from_response')
    def test_json_response_parsing(self, mock_get_text, mock_call_api):
        """Test that JSON responses from Gemini are parsed correctly"""
        
        # Simulate AI returning JSON structure
        mock_json_response = '''{
            "narrative": "What would you like to do next?\\n1. **Investigate** - Look around\\n2. **Proceed** - Move forward\\n3. **Cast spell** - Use magic",
            "entities_mentioned": ["Test Hero"],
            "location_confirmed": "Test Location"
        }'''
        
        # Mock the API call
        mock_response = MagicMock()
        mock_call_api.return_value = mock_response
        mock_get_text.return_value = mock_json_response
        
        # Call the function
        result = _validate_and_enforce_planning_block(
            self.response_text, 
            self.user_input, 
            self.game_state, 
            self.chosen_model, 
            self.system_instruction
        )
        
        # Verify JSON was parsed correctly
        self.assertIn("You enter the chamber", result)
        self.assertIn("What would you like to do next?", result)
        self.assertIn("Investigate", result)
        
        # Verify no raw JSON in result
        self.assertNotIn('"narrative":', result)
        self.assertNotIn('"entities_mentioned":', result)
        self.assertNotIn('\\n', result)  # Escape sequences should be converted
    
    @patch('gemini_service._call_gemini_api')
    @patch('gemini_service._get_text_from_response')
    def test_plain_text_response_handling(self, mock_get_text, mock_call_api):
        """Test that plain text responses still work correctly"""
        
        # Simulate AI returning plain text
        mock_plain_response = """What would you like to do next?
1. **Investigate** - Look around for clues
2. **Proceed** - Move forward carefully
3. **Cast spell** - Use magic to sense dangers"""
        
        # Mock the API call
        mock_response = MagicMock()
        mock_call_api.return_value = mock_response
        mock_get_text.return_value = mock_plain_response
        
        # Call the function
        result = _validate_and_enforce_planning_block(
            self.response_text, 
            self.user_input, 
            self.game_state, 
            self.chosen_model, 
            self.system_instruction
        )
        
        # Verify plain text works correctly
        self.assertIn("You enter the chamber", result)
        self.assertIn("What would you like to do next?", result)
        self.assertIn("Investigate", result)
    
    @patch('gemini_service._call_gemini_api')
    def test_api_failure_fallback(self, mock_call_api):
        """Test fallback behavior when API fails"""
        
        # Simulate API failure
        mock_call_api.side_effect = Exception("API Error")
        
        # Call the function
        result = _validate_and_enforce_planning_block(
            self.response_text, 
            self.user_input, 
            self.game_state, 
            self.chosen_model, 
            self.system_instruction
        )
        
        # Verify fallback works
        self.assertIn("You enter the chamber", result)
        self.assertIn("What would you like to do next?", result)
    
    def test_empty_planning_block_handling(self):
        """Test handling of empty or null planning blocks"""
        
        # Test empty string
        response1 = NarrativeResponse(
            narrative="Some narrative text",
            planning_block=""
        )
        # Empty string planning blocks are rejected and return empty dict
        self.assertEqual(response1.planning_block, {})
        
        # Test None value (gets converted to empty string)
        response2 = NarrativeResponse(
            narrative="Some narrative text",
            planning_block=None
        )
        # None is converted to empty dict
        self.assertEqual(response2.planning_block, {})
    
    def test_no_narrative_markers_in_json(self):
        """Test that planning blocks in JSON don't have narrative markers"""
        
        # Planning block should NOT have these markers
        bad_planning_block = """--- PLANNING BLOCK ---
What would you like to do?
1. **Option1**
2. **Option2**"""
        
        # Should just have the content
        good_planning_block = """What would you like to do?
1. **Option1**
2. **Option2**"""
        
        response = NarrativeResponse(
            narrative="Some narrative",
            planning_block=good_planning_block
        )
        
        # Verify no narrative markers in planning block
        self.assertNotIn("--- PLANNING BLOCK ---", response.planning_block)


if __name__ == '__main__':
    unittest.main(verbosity=2)