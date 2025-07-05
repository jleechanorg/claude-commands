#!/usr/bin/env python3
"""Test that character creation triggers properly when mechanics is enabled."""

import unittest
import os
import sys
import logging_util
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gemini_service import get_initial_story
import constants

class TestCharacterCreationTrigger(unittest.TestCase):
    """Test that character creation prompt is properly injected when mechanics is enabled."""
    
    def setUp(self):
        """Set up test environment."""
        os.environ['TESTING'] = 'true'
        logging_util.basicConfig(level=logging_util.INFO)
    
    @patch('gemini_service._call_gemini_api')
    @patch('gemini_service.get_client')
    def test_character_creation_with_mechanics_enabled(self, mock_get_client, mock_call_api):
        """Test that character creation reminder is added when mechanics is selected."""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.text = "Welcome, adventurer! Before we begin your journey..."
        mock_call_api.return_value = mock_response
        
        # Mock the client for token counting
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Test with mechanics enabled
        user_prompt = "I want to play as a knight in a fantasy kingdom"
        selected_prompts = ['mechanics', 'narrative']
        
        # Capture the actual prompt sent to the API
        actual_prompt = None
        def capture_prompt(contents, *args, **kwargs):
            nonlocal actual_prompt
            actual_prompt = contents[0].parts[0].text
            return mock_response
        
        mock_call_api.side_effect = capture_prompt
        
        # Call the function
        result = get_initial_story(user_prompt, selected_prompts=selected_prompts)
        
        # Verify the character creation reminder was added
        self.assertIsNotNone(actual_prompt)
        # Check that the constant text is in the prompt
        self.assertIn(constants.CHARACTER_CREATION_REMINDER, actual_prompt)
        
        # Verify the original user prompt is still there
        self.assertIn(user_prompt, actual_prompt)
        
        print(f"✓ Character creation reminder properly added to prompt")
        print(f"✓ Actual prompt sent: {actual_prompt[:200]}...")
    
    @patch('gemini_service._call_gemini_api')
    @patch('gemini_service.get_client')
    def test_no_character_creation_without_mechanics(self, mock_get_client, mock_call_api):
        """Test that character creation reminder is NOT added when mechanics is disabled."""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.text = "The kingdom awaits..."
        mock_call_api.return_value = mock_response
        
        # Mock the client
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Test with only narrative enabled (no mechanics)
        user_prompt = "I want to play as a knight in a fantasy kingdom"
        selected_prompts = ['narrative']
        
        # Capture the actual prompt
        actual_prompt = None
        def capture_prompt(contents, *args, **kwargs):
            nonlocal actual_prompt
            actual_prompt = contents[0].parts[0].text
            return mock_response
        
        mock_call_api.side_effect = capture_prompt
        
        # Call the function
        result = get_initial_story(user_prompt, selected_prompts=selected_prompts)
        
        # Verify NO character creation reminder was added
        self.assertIsNotNone(actual_prompt)
        self.assertNotIn("CRITICAL REMINDER", actual_prompt)
        self.assertNotIn("character creation", actual_prompt)
        
        print(f"✓ No character creation reminder when mechanics disabled")
    
    @patch('gemini_service._call_gemini_api')
    @patch('gemini_service.get_client')
    def test_character_creation_with_mechanics_only(self, mock_get_client, mock_call_api):
        """Test that character creation works with mechanics only (no narrative)."""
        # Mock the API response
        mock_response = MagicMock()
        mock_response.text = "Welcome, adventurer! Before we begin..."
        mock_call_api.return_value = mock_response
        
        # Mock the client
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        # Test with only mechanics enabled
        user_prompt = "I want to create a character"
        selected_prompts = ['mechanics']
        
        # Capture the actual prompt
        actual_prompt = None
        def capture_prompt(contents, *args, **kwargs):
            nonlocal actual_prompt
            actual_prompt = contents[0].parts[0].text
            return mock_response
        
        mock_call_api.side_effect = capture_prompt
        
        # Call the function
        result = get_initial_story(user_prompt, selected_prompts=selected_prompts)
        
        # Verify the character creation reminder was added
        self.assertIsNotNone(actual_prompt)
        self.assertIn(constants.CHARACTER_CREATION_REMINDER, actual_prompt)
        
        print(f"✓ Character creation reminder added with mechanics only")

if __name__ == '__main__':
    unittest.main()