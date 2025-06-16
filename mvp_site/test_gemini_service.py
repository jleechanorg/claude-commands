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
        # --- Arrange ---
        mock_model.generate_content.return_value.text = "The adventure begins!"
        test_prompt = "A wizard enters a tavern."

        # --- Act ---
        result = gemini_service.get_initial_story(test_prompt)

        # --- Assert ---
        self.assertEqual(result, "The adventure begins!")
        # --- THIS IS THE FIX ---
        # Assert that the model was called directly with the user's prompt.
        mock_model.generate_content.assert_called_once_with(test_prompt)

    @patch('gemini_service.model')
    def test_continue_story_character_mode(self, mock_model):
        """
        Tests the continue_story function in 'character' mode.
        """
        # --- Arrange ---
        mock_model.generate_content.return_value.text = "The story continues..."
        user_input = "I inspect the strange orb."
        story_context = [{'actor': 'gemini', 'text': 'You see a strange orb on a pedestal.'}]
        expected_prompt = "Character does {user_input}. \n\n context: {last_gemini_response}. Continue the story.".format(
            user_input=user_input, last_gemini_response=story_context[0]['text']
        )

        # --- Act ---
        result = gemini_service.continue_story(user_input, "character", story_context)

        # --- Assert ---
        self.assertEqual(result, "The story continues...")
        mock_model.generate_content.assert_called_with(expected_prompt)

    @patch('gemini_service.model')
    def test_continue_story_god_mode(self, mock_model):
        """
        Tests the continue_story function in 'god' mode.
        """
        # --- Arrange ---
        mock_model.generate_content.return_value.text = "The world changes."
        user_input = "A dragon suddenly appears."
        story_context = [{'actor': 'gemini', 'text': 'The room is quiet.'}]
        expected_prompt = "{user_input}. \n\n context: {last_gemini_response}".format(
            user_input=user_input, last_gemini_response=story_context[0]['text']
        )

        # --- Act ---
        result = gemini_service.continue_story(user_input, "god", story_context)

        # --- Assert ---
        self.assertEqual(result, "The world changes.")
        mock_model.generate_content.assert_called_with(expected_prompt)

    def test_continue_story_invalid_mode(self):
        """
        Tests that continue_story raises a ValueError for an invalid mode.
        """
        with self.assertRaises(ValueError):
            gemini_service.continue_story("test", "invalid_mode", [])

if __name__ == '__main__':
    unittest.main()
