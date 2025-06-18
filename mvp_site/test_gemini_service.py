import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Ensure a dummy API key is set BEFORE we import the service.
os.environ["GEMINI_API_KEY"] = "DUMMY_KEY_FOR_TESTING"

# Ensure the prompts directory exists for tests
if not os.path.exists('./prompts'):
    os.makedirs('./prompts')

# Create dummy system instruction files for the test environment
with open('./prompts/narrative_system_instruction.md', 'w') as f:
    f.write("Test narrative instruction content.")
with open('./prompts/mechanics_system_instruction.md', 'w') as f:
    f.write("Test mechanics instruction content.")
with open('./prompts/calibration_instruction.md', 'w') as f:
    f.write("Test calibration instruction content.")

import gemini_service

# Define mock system instruction content for consistent testing
MOCK_NARRATIVE_CONTENT = "Mock narrative instruction."
MOCK_MECHANICS_CONTENT = "Mock mechanics instruction."
MOCK_CALIBRATION_CONTENT = "Mock calibration instruction."

class TestGeminiService(unittest.TestCase):

    # Patch the _load_instruction_file helper directly
    @patch('gemini_service._load_instruction_file')
    @patch('gemini_service.get_client')
    def test_get_initial_story_with_selected_prompts(self, mock_get_client, mock_load_instruction_file):
        """
        Tests get_initial_story with specific selected prompts, using system_instruction parameter.
        """
        # Configure the mock for _load_instruction_file to return specific content based on argument
        def side_effect_for_loader(instruction_type):
            if instruction_type == "narrative":
                return MOCK_NARRATIVE_CONTENT
            elif instruction_type == "mechanics":
                return MOCK_MECHANICS_CONTENT
            elif instruction_type == "calibration":
                return MOCK_CALIBRATION_CONTENT
            return "" 

        mock_load_instruction_file.side_effect = side_effect_for_loader

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value.text = "The story begins as chosen!"
        mock_get_client.return_value = mock_client
        
        test_prompt = "Start a heroic fantasy."
        selected_prompts = ['narrative', 'calibration'] # User selected these two

        result = gemini_service.get_initial_story(test_prompt, selected_prompts=selected_prompts)

        self.assertEqual(result, "The story begins as chosen!")
        mock_client.models.generate_content.assert_called_once()
        
        call_args = mock_client.models.generate_content.call_args
        
        # Verify the user prompt content
        self.assertEqual(call_args.kwargs['contents'][0].role, "user")
        self.assertIn(test_prompt, call_args.kwargs['contents'][0].parts[0].text)
        self.assertIn("(Please keep the response to about", call_args.kwargs['contents'][0].parts[0].text)
        
        # Verify system_instruction parameter is used and contains combined content
        self.assertIn('config', call_args.kwargs) 
        self.assertTrue(hasattr(call_args.kwargs['config'], 'system_instruction')) # Check if attribute exists
        
        # Construct expected combined system instruction for assertion
        expected_system_instruction = f"{MOCK_NARRATIVE_CONTENT}\n\n{MOCK_CALIBRATION_CONTENT}"
        self.assertEqual(call_args.kwargs['config'].system_instruction.text, expected_system_instruction)

        # Verify unselected prompt content is NOT in system_instruction
        self.assertNotIn(MOCK_MECHANICS_CONTENT, call_args.kwargs['config'].system_instruction.text)
        
        # Crucially, verify that the system instruction is NOT in the user prompt content
        full_user_prompt = call_args.kwargs['contents'][0].parts[0].text
        self.assertNotIn(MOCK_NARRATIVE_CONTENT, full_user_prompt)
        self.assertNotIn(MOCK_MECHANICS_CONTENT, full_user_prompt)
        self.assertNotIn(MOCK_CALIBRATION_CONTENT, full_user_prompt)
        self.assertNotIn("SYSTEM INSTRUCTIONS:", full_user_prompt)


    @patch('gemini_service.get_client')
    @patch('gemini_service._load_instruction_file', return_value="") # Mock loader to return no content
    def test_get_initial_story_no_selected_prompts(self, mock_load_instruction_file, mock_get_client):
        """
        Tests get_initial_story when no specific prompts are selected (default behavior).
        Ensures system_instruction is None.
        """
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value.text = "A simple story begins."
        mock_get_client.return_value = mock_client
        
        test_prompt = "A simple beginning."
        result = gemini_service.get_initial_story(test_prompt, selected_prompts=[]) # Explicitly pass empty list

        self.assertEqual(result, "A simple story begins.")
        mock_client.models.generate_content.assert_called_once()
        
        call_args = mock_client.models.generate_content.call_args
        
        # Verify user prompt is correct
        self.assertEqual(call_args.kwargs['contents'][0].role, "user")
        self.assertIn(test_prompt, call_args.kwargs['contents'][0].parts[0].text)
        self.assertIn("(Please keep the response to about", call_args.kwargs['contents'][0].parts[0].text)
        
        # Corrected Assertion: Check if system_instruction is None
        self.assertIn('config', call_args.kwargs) # Config should still exist
        # When no system instruction is provided (empty string passed to _call_gemini_api),
        # the system_instruction attribute on config is None by the SDK's design.
        self.assertIsNone(call_args.kwargs['config'].system_instruction)


    @patch('gemini_service.get_client')
    @patch('gemini_service._load_instruction_file') # Patch for continue_story
    def test_continue_story_character_mode(self, mock_load_instruction_file, mock_get_client):
        """
        Tests the continue_story function in 'character' mode.
        Reverted to expecting concatenated history string, now passes system_instruction.
        """
        # Configure the mock for _load_instruction_file for continue_story
        def side_effect_for_loader(instruction_type):
            if instruction_type == "narrative":
                return MOCK_NARRATIVE_CONTENT
            elif instruction_type == "mechanics":
                return MOCK_MECHANICS_CONTENT
            return "" # Return empty string for other types or unmocked calls

        mock_load_instruction_file.side_effect = side_effect_for_loader

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value.text = "The story continues..."
        mock_get_client.return_value = mock_client

        user_input = "I inspect the strange orb."
        story_context = [{'actor': 'gemini', 'text': 'You see a strange orb on a pedestal.'}]
        selected_prompts = ['narrative', 'mechanics'] # Example selected prompts for continue_story
        
        result = gemini_service.continue_story(user_input, "character", story_context, selected_prompts)

        self.assertEqual(result, "The story continues...")
        mock_client.models.generate_content.assert_called_once()
        
        call_args = mock_client.models.generate_content.call_args
        self.assertEqual(len(call_args.kwargs['contents']), 1) 
        
        full_prompt_sent = call_args.kwargs['contents'][0] 
        
        self.assertIn("Acting as the main character " + user_input + ".", full_prompt_sent) 
        self.assertIn("Story: You see a strange orb on a pedestal.", full_prompt_sent)
        self.assertIn("CONTEXT:\n", full_prompt_sent)
        self.assertIn("YOUR TURN:\n", full_prompt_sent)
        
        # Verify system_instruction parameter is passed and contains combined content
        self.assertIn('config', call_args.kwargs)
        self.assertTrue(hasattr(call_args.kwargs['config'], 'system_instruction'))
        
        expected_system_instruction = f"{MOCK_NARRATIVE_CONTENT}\n\n{MOCK_MECHANICS_CONTENT}"
        self.assertEqual(call_args.kwargs['config'].system_instruction.text, expected_system_instruction)


    @patch('gemini_service.get_client')
    @patch('gemini_service._load_instruction_file') # Patch for continue_story
    def test_continue_story_god_mode(self, mock_load_instruction_file, mock_get_client):
        """
        Tests the continue_story function in 'god' mode.
        Reverted to expecting concatenated history string, now passes system_instruction.
        """
        # Configure the mock for _load_instruction_file for continue_story
        def side_effect_for_loader(instruction_type):
            if instruction_type == "narrative":
                return MOCK_NARRATIVE_CONTENT
            return ""

        mock_load_instruction_file.side_effect = side_effect_for_loader

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value.text = "An earthquake shakes the room."
        mock_get_client.return_value = mock_client

        user_input = "A dragon suddenly appears."
        story_context = [{'actor': 'gemini', 'text': 'The room is quiet.'}]
        selected_prompts = ['narrative'] # Example selected prompts for continue_story
        
        result = gemini_service.continue_story(user_input, "god", story_context, selected_prompts)
        self.assertEqual(result, "An earthquake shakes the room.")
        mock_client.models.generate_content.assert_called_once()
        
        call_args = mock_client.models.generate_content.call_args
        self.assertEqual(len(call_args.kwargs['contents']), 1) 
        
        full_prompt_sent = call_args.kwargs['contents'][0] 
        
        self.assertIn("Story: The room is quiet.", full_prompt_sent) 
        self.assertIn("YOUR TURN:\n" + user_input, full_prompt_sent) 
        self.assertIn("CONTEXT:\n", full_prompt_sent)
        self.assertIn("YOUR TURN:\n", full_prompt_sent)

        # Verify system_instruction parameter is passed and contains combined content
        self.assertIn('config', call_args.kwargs)
        self.assertTrue(hasattr(call_args.kwargs['config'], 'system_instruction'))
        
        expected_system_instruction = MOCK_NARRATIVE_CONTENT
        self.assertEqual(call_args.kwargs['config'].system_instruction.text, expected_system_instruction)

if __name__ == '__main__':
    unittest.main()
