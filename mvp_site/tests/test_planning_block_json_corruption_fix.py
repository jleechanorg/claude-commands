#!/usr/bin/env python3
"""
Red/Green test to validate that planning block JSON corruption is fixed.

This test ensures that when planning block generation returns JSON (instead of plain text),
it gets properly parsed and only the narrative text is saved to Firestore.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory to the path so we can import from mvp_site
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from gemini_service import _validate_and_enforce_planning_block
from game_state import GameState

class TestPlanningBlockJSONCorruptionFix(unittest.TestCase):
    """Test that planning block generation properly parses JSON responses."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a minimal game state
        self.game_state = GameState()
        self.game_state.player_character_data = {'name': 'Test Hero'}
        self.game_state.world_data = {'current_location_name': 'Test Location'}
        
        # Sample response text that would normally get planning block appended
        self.response_text = "You enter the chamber. The air is thick with tension."
        
        # User input that would trigger planning block generation
        self.user_input = "I want to think about my options"
        
        # Mock models and system instruction
        self.chosen_model = "gemini-2.5-flash"
        self.system_instruction = "Test system instruction"
    
    @patch('gemini_service._call_gemini_api')
    @patch('gemini_service._get_text_from_response')
    def test_planning_block_json_response_gets_parsed(self, mock_get_text, mock_call_api):
        """
        RED TEST: Verify that when planning block generation returns JSON,
        it gets properly parsed and only narrative text is used.
        """
        # Simulate AI returning JSON structure for planning block (the problem scenario)
        mock_json_response = '''{
            "narrative": "--- PLANNING BLOCK ---\\nWhat would you like to do next?\\n1. **Investigate the chamber** - Look around for clues\\n2. **Proceed cautiously** - Move forward carefully\\n3. **Cast a detection spell** - Use magic to sense dangers",
            "entities_mentioned": ["Test Hero"],
            "location_confirmed": "Test Location",
            "debug_info": {
                "dm_notes": ["Generated planning block for user"]
            }
        }'''
        
        # Mock the API call to return a response object
        mock_response = MagicMock()
        mock_call_api.return_value = mock_response
        mock_get_text.return_value = mock_json_response
        
        # Call the function that should parse the JSON
        result = _validate_and_enforce_planning_block(
            self.response_text, 
            self.user_input, 
            self.game_state, 
            self.chosen_model, 
            self.system_instruction
        )
        
        # ASSERTIONS: Verify JSON was parsed and only narrative text was used
        
        # 1. Result should contain the original response text
        self.assertIn("You enter the chamber", result)
        
        # 2. Result should contain the parsed planning block text (not JSON structure)
        self.assertIn("--- PLANNING BLOCK ---", result)
        self.assertIn("What would you like to do next?", result)
        self.assertIn("Investigate the chamber", result)
        
        # 3. Result should NOT contain JSON structure elements
        self.assertNotIn('"narrative":', result, "Raw JSON structure should be parsed out")
        self.assertNotIn('"entities_mentioned":', result, "Raw JSON structure should be parsed out")
        self.assertNotIn('"debug_info":', result, "Raw JSON structure should be parsed out")
        self.assertNotIn('\\n', result, "JSON escape sequences should be converted to actual newlines")
        
        # 4. Result should have proper line breaks (not escaped)
        self.assertIn("\n1. **Investigate", result, "Should have actual newlines, not \\n")
        
        # 5. Planning block should be properly formatted with leading newlines
        self.assertTrue(result.endswith("Use magic to sense dangers"), "Should end with clean text")
        
        print("✅ Test passed: Planning block JSON response properly parsed")
        print(f"Result length: {len(result)} characters")
        print("Result preview:", repr(result[-100:]))  # Show end of result
    
    @patch('gemini_service._call_gemini_api')
    @patch('gemini_service._get_text_from_response')
    def test_planning_block_plain_text_response_unchanged(self, mock_get_text, mock_call_api):
        """
        GREEN TEST: Verify that when planning block generation returns plain text,
        it works correctly (existing functionality preserved).
        """
        # Simulate AI returning plain text for planning block (normal scenario)
        mock_plain_response = """--- PLANNING BLOCK ---
What would you like to do next?
1. **Investigate the chamber** - Look around for clues
2. **Proceed cautiously** - Move forward carefully
3. **Cast a detection spell** - Use magic to sense dangers"""
        
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
        
        # ASSERTIONS: Verify plain text response works correctly
        
        # 1. Result should contain the original response text
        self.assertIn("You enter the chamber", result)
        
        # 2. Result should contain the planning block
        self.assertIn("--- PLANNING BLOCK ---", result)
        self.assertIn("What would you like to do next?", result)
        
        # 3. Should have proper formatting
        self.assertIn("\n1. **Investigate", result)
        
        print("✅ Test passed: Planning block plain text response works correctly")
    
    @patch('gemini_service._call_gemini_api')
    def test_planning_block_api_failure_fallback(self, mock_call_api):
        """
        TEST: Verify that when planning block generation fails,
        fallback text is used (not corrupted).
        """
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
        
        # ASSERTIONS: Verify fallback works
        self.assertIn("You enter the chamber", result)
        self.assertIn("--- PLANNING BLOCK ---", result)
        self.assertIn("What would you like to do next?", result)
        self.assertIn("Continue with your current course", result)
        
        print("✅ Test passed: Planning block API failure fallback works")

if __name__ == '__main__':
    # Run the red/green tests
    print("🔴 RUNNING RED/GREEN TESTS: Planning Block JSON Corruption Fix")
    print("=" * 70)
    
    unittest.main(verbosity=2)