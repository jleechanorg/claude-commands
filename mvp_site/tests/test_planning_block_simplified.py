"""Test that simplified planning block prompts work correctly."""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


import logging_util
import gemini_service
import constants
from game_state import GameState

class TestSimplifiedPlanningBlockPrompts(unittest.TestCase):
    """Test that the simplified planning block prompts reference the correct templates."""
    
    def setUp(self):
        super().setUp()
        self.game_state = GameState()
        self.game_state.player_character_data = {'name': 'TestHero'}
        self.game_state.world_data = {'current_location_name': 'Test Town'}
        
    @patch('gemini_service._get_text_from_response')
    @patch('gemini_service._call_gemini_api')
    def test_simplified_prompt_for_think_command(self, mock_api, mock_get_text):
        """Test that think commands use simplified prompt referencing think_planning_block."""
        # Mock the response object and text extraction
        mock_api.return_value = MagicMock()
        mock_get_text.return_value = "Generated planning block content"
        
        # Test response without planning block
        response_text = "You stand in the town square, pondering your next move."
        user_input = "I think about my options"
        
        # Mock the API to capture the prompt
        captured_prompt = None
        def capture_prompt(prompts, *args, **kwargs):
            nonlocal captured_prompt
            captured_prompt = prompts[0]
            return MagicMock()
        mock_api.side_effect = capture_prompt
        
        # Call the function
        gemini_service._validate_and_enforce_planning_block(
            response_text, user_input, self.game_state, 
            'test-model', 'test-instruction'
        )
        
        # Verify the simplified prompt
        self.assertIsNotNone(captured_prompt)
        self.assertIn("think_planning_block template", captured_prompt)
        self.assertNotIn("--- PLANNING BLOCK ---", captured_prompt)  # Should not redefine the format
        self.assertNotIn("Pros:", captured_prompt)  # Should not include template details
        self.assertIn("TestHero", captured_prompt)
        self.assertIn("Test Town", captured_prompt)
        
    @patch('gemini_service._get_text_from_response')
    @patch('gemini_service._call_gemini_api')
    def test_simplified_prompt_for_standard_action(self, mock_api, mock_get_text):
        """Test that standard actions use simplified prompt referencing standard_choice_block."""
        # Mock the response object and text extraction
        mock_api.return_value = MagicMock()
        mock_get_text.return_value = "Generated planning block content"
        
        # Test response without planning block
        response_text = "You enter the tavern and see several patrons."
        user_input = "I look around"
        
        # Mock the API to capture the prompt
        captured_prompt = None
        def capture_prompt(prompts, *args, **kwargs):
            nonlocal captured_prompt
            captured_prompt = prompts[0]
            return MagicMock()
        mock_api.side_effect = capture_prompt
        
        # Call the function
        gemini_service._validate_and_enforce_planning_block(
            response_text, user_input, self.game_state, 
            'test-model', 'test-instruction'
        )
        
        # Verify the simplified prompt
        self.assertIsNotNone(captured_prompt)
        self.assertIn("standard_choice_block template", captured_prompt)
        self.assertNotIn("What would you like to do next?", captured_prompt)  # Should not redefine
        self.assertNotIn("**[Option_1]:**", captured_prompt)  # Should not include template details
        self.assertIn("TestHero", captured_prompt)
        self.assertIn("Test Town", captured_prompt)
        
    @patch('gemini_service._get_text_from_response')
    @patch('gemini_service._call_gemini_api')
    def test_full_context_provided(self, mock_api, mock_get_text):
        """Test that full context is now provided, not limited to 500 characters."""
        # Mock the response object and text extraction
        mock_api.return_value = MagicMock()
        mock_get_text.return_value = "Generated planning block content"
        
        # Create a very long response
        long_response = "A" * 1000 + " The important ending part."
        user_input = "continue"
        
        # Mock the API to capture the prompt
        captured_prompt = None
        def capture_prompt(prompts, *args, **kwargs):
            nonlocal captured_prompt
            captured_prompt = prompts[0]
            return MagicMock()
        mock_api.side_effect = capture_prompt
        
        # Call the function
        gemini_service._validate_and_enforce_planning_block(
            long_response, user_input, self.game_state, 
            'test-model', 'test-instruction'
        )
        
        # Verify full context is provided
        self.assertIsNotNone(captured_prompt)
        self.assertIn("The important ending part.", captured_prompt)
        self.assertIn("A" * 600, captured_prompt)  # Should include the full 1000 As now
        
    def test_all_think_keywords_detected(self):
        """Test that all think keywords are properly detected."""
        think_keywords = ['think', 'plan', 'consider', 'strategize', 'options']
        
        for keyword in think_keywords:
            with patch('gemini_service._call_gemini_api') as mock_api, \
                 patch('gemini_service._get_text_from_response') as mock_get_text:
                mock_api.return_value = MagicMock()
                mock_get_text.return_value = "Generated planning block content"
                
                captured_prompt = None
                def capture_prompt(prompts, *args, **kwargs):
                    nonlocal captured_prompt
                    captured_prompt = prompts[0]
                    return MagicMock()
                mock_api.side_effect = capture_prompt
                
                user_input = f"I {keyword} about what to do"
                response_text = "You pause to gather your thoughts."
                
                gemini_service._validate_and_enforce_planning_block(
                    response_text, user_input, self.game_state, 
                    'test-model', 'test-instruction'
                )
                
                self.assertIn("think_planning_block template", captured_prompt, 
                            f"Keyword '{keyword}' should trigger think planning block")

if __name__ == '__main__':
    logging_util.basicConfig(level=logging_util.INFO)
    unittest.main()