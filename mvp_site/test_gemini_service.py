import unittest
from unittest.mock import patch, MagicMock
import os

# Set a dummy API key BEFORE we import the service.
os.environ["GEMINI_API_KEY"] = "DUMMY_KEY_FOR_TESTING"
import gemini_service

class TestGeminiService(unittest.TestCase):

    @patch('gemini_service.model')
    def test_get_initial_story(self, mock_model):
        """
        Tests the get_initial_story function, expecting no boilerplate.
        """
        mock_model.generate_content.return_value.text = "The adventure begins!"
        test_prompt = "A wizard enters a tavern."
        result = gemini_service.get_initial_story(test_prompt)
        self.assertEqual(result, "The adventure begins!")
        mock_model.generate_content.assert_called_once_with(test_prompt)

    @patch('gemini_service.model')
    def test_continue_story_character_mode(self, mock_model):
        """
        Tests the continue_story function in 'character' mode.
        """
        mock_model.generate_content.return_value.text = "The story continues..."
        user_input = "I inspect the strange orb."
        story_context = [{'actor': 'gemini', 'text': 'You see a strange orb on a pedestal.'}]
        expected_prompt = "Character does {user_input}. \n\n context: {last_gemini_response}. Continue the story.".format(
            user_input=user_input, last_gemini_response=story_context[0]['text']
        )
        result = gemini_service.continue_story(user_input, "character", story_context)
        self.assertEqual(result, "The story continues...")
        mock_model.generate_content.assert_called_with(expected_prompt)

    @patch('gemini_service.model')
    def test_continue_story_god_mode(self, mock_model):
        """
        Tests the continue_story function in 'god' mode.
        """
        mock_model.generate_content.return_value.text = "The world changes."
        user_input = "A dragon suddenly appears."
        story_context = [{'actor': 'gemini', 'text': 'The room is quiet.'}]
        expected_prompt = "{user_input}. \n\n context: {last_gemini_response}".format(
            user_input=user_input, last_gemini_response=story_context[0]['text']
        )
        result = gemini_service.continue_story(user_input, "god", story_context)
        self.assertEqual(result, "The world changes.")
        mock_model.generate_content.assert_called_with(expected_prompt)

    def test_continue_story_invalid_mode(self):
        """
        Tests that continue_story raises a ValueError for an invalid mode using an explicit try/except block.
        """
        # --- THIS IS THE REFACTORED TEST ---
        try:
            # We call the function with bad data, expecting it to raise an error.
            gemini_service.continue_story("test", "invalid_mode", [])
            
            # If the line above does NOT raise an error, this fail() line will be executed.
            # This is how we know the test failed: the expected error did not happen.
            self.fail("Expected continue_story to raise a ValueError, but it did not.")
            
        except ValueError as e:
            # If we land in this block, it means a ValueError was correctly raised.
            # We can optionally check if the error message is what we expect.
            self.assertEqual(str(e), "Invalid interaction mode specified.")
            # We can print a success message for clarity during test runs.
            print("\nSUCCESS: Correctly caught expected ValueError.")
            # Reaching the end of the 'except' block without a self.fail() means the test is a SUCCESS.
            pass

if __name__ == '__main__':
    unittest.main()
