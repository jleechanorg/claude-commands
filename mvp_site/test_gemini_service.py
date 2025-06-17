import unittest
from unittest.mock import patch, MagicMock
import os

# Set a dummy API key BEFORE we import the service.
# This is required for the genai.Client() initialization.
os.environ["GEMINI_API_KEY"] = "DUMMY_KEY_FOR_TESTING"
import gemini_service

class TestGeminiService(unittest.TestCase):

    # --- THIS IS THE FIX: We now patch 'get_client' instead of 'model' ---
    @patch('gemini_service.get_client')
    def test_get_initial_story(self, mock_get_client):
        """
        Tests the get_initial_story function with the new client SDK.
        """
        # Create a mock client object that our test can control.
        mock_client = MagicMock()
        # Configure the mock to simulate the new method call chain.
        mock_client.models.generate_content.return_value.text = "The adventure begins!"
        # Make our patched function return this mock client.
        mock_get_client.return_value = mock_client
        
        test_prompt = "A wizard enters a tavern."
        result = gemini_service.get_initial_story(test_prompt)

        self.assertEqual(result, "The adventure begins!")
        # Verify that the correct method on our mock client was called.
        mock_client.models.generate_content.assert_called_once()
        # Optional: A more detailed check of what it was called with
        call_args = mock_client.models.generate_content.call_args
        self.assertIn(test_prompt, call_args.kwargs['contents'])


    @patch('gemini_service.get_client')
    def test_continue_story_character_mode(self, mock_get_client):
        """
        Tests the continue_story function in 'character' mode with the new SDK.
        """
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value.text = "The story continues..."
        mock_get_client.return_value = mock_client

        user_input = "I inspect the strange orb."
        story_context = [{'actor': 'gemini', 'text': 'You see a strange orb on a pedestal.'}]
        expected_prompt_fragment = "Character does I inspect the strange orb." # Check for a key part
        
        result = gemini_service.continue_story(user_input, "character", story_context)

        self.assertEqual(result, "The story continues...")
        mock_client.models.generate_content.assert_called_once()
        call_args = mock_client.models.generate_content.call_args
        # Check that the generated prompt contains the expected text
        self.assertIn(expected_prompt_fragment, call_args.kwargs['contents'][0])

    @patch('gemini_service.get_client')
    def test_continue_story_god_mode(self, mock_get_client):
        """
        Tests the continue_story function in 'god' mode with the new SDK.
        """
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value.text = "The world changes."
        mock_get_client.return_value = mock_client

        user_input = "A dragon suddenly appears."
        story_context = [{'actor': 'gemini', 'text': 'The room is quiet.'}]
        
        result = gemini_service.continue_story(user_input, "god", story_context)
        self.assertEqual(result, "The world changes.")
        mock_client.models.generate_content.assert_called_once()
        call_args = mock_client.models.generate_content.call_args
        self.assertIn(user_input, call_args.kwargs['contents'][0])

    def test_continue_story_invalid_mode(self):
        """
        Tests that continue_story raises a ValueError for an invalid mode. No change needed here.
        """
        with self.assertRaises(ValueError) as context:
            gemini_service.continue_story("test", "invalid_mode", [])
        
        self.assertEqual(str(context.exception), "Invalid interaction mode specified.")

if __name__ == '__main__':
    unittest.main()
