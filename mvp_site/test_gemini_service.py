import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import logging # Import logging to patch it

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
with open('./prompts/destiny_ruleset.md', 'w') as f: # NEW DUMMY FILE
    f.write("Test destiny ruleset content.")

import gemini_service

# Define mock system instruction content for consistent testing
MOCK_NARRATIVE_CONTENT = "Mock narrative instruction."
MOCK_MECHANICS_CONTENT = "Mock mechanics instruction."
MOCK_CALIBRATION_CONTENT = "Mock calibration instruction."
MOCK_DESTINY_RULESET_CONTENT = "Mock destiny ruleset content." # NEW MOCK CONTENT

# Helper mock classes for types.Content and types.Part to avoid actual google.generativeai import in tests
# These mimic the essential attributes used by the _call_gemini_api logging logic and prompt construction.
class MockPart:
    def __init__(self, text):
        self.text = text
    def __repr__(self):
        # Shorten for easier debugging of mock objects in logs/errors
        return f"MockPart(text='{self.text[:50]}{'...' if len(self.text) > 50 else ''}')"

class MockContent:
    def __init__(self, role, parts):
        self.role = role
        self.parts = parts
    def __repr__(self):
        return f"MockContent(role='{self.role}', parts={self.parts})"


class TestGeminiService(unittest.TestCase):

    # Patch the _load_instruction_file helper directly
    @patch('gemini_service._load_instruction_file')
    @patch('gemini_service.get_client')
    def test_get_initial_story_with_selected_prompts(self, mock_get_client, mock_load_instruction_file):
        """
        Tests get_initial_story with specific selected prompts, using system_instruction parameter.
        Ensures destiny_ruleset is always included.
        """
        # Configure the mock for _load_instruction_file to return specific content based on argument
        def side_effect_for_loader(instruction_type):
            if instruction_type == "narrative":
                return MOCK_NARRATIVE_CONTENT
            elif instruction_type == "mechanics":
                return MOCK_MECHANICS_CONTENT
            elif instruction_type == "calibration":
                return MOCK_CALIBRATION_CONTENT
            elif instruction_type == "destiny_ruleset": # NEW
                return MOCK_DESTINY_RULESET_CONTENT
            return "" 

        mock_load_instruction_file.side_effect = side_effect_for_loader

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value.text = "The story begins as chosen!"
        mock_get_client.return_value = mock_client
        
        test_prompt = "Start a heroic fantasy."
        # Simulate user selecting narrative, mechanics, calibration
        selected_prompts = ['narrative', 'mechanics', 'calibration'] 

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
        self.assertTrue(hasattr(call_args.kwargs['config'], 'system_instruction')) 
        
        # Construct expected combined system instruction for assertion (all selected + destiny)
        expected_system_instruction = f"{MOCK_NARRATIVE_CONTENT}\n\n{MOCK_MECHANICS_CONTENT}\n\n{MOCK_CALIBRATION_CONTENT}\n\n{MOCK_DESTINY_RULESET_CONTENT}"
        self.assertEqual(call_args.kwargs['config'].system_instruction.text, expected_system_instruction)

        # Crucially, verify that the system instruction is NOT in the user prompt content
        full_user_prompt = call_args.kwargs['contents'][0].parts[0].text
        self.assertNotIn(MOCK_NARRATIVE_CONTENT, full_user_prompt)
        self.assertNotIn(MOCK_MECHANICS_CONTENT, full_user_prompt)
        self.assertNotIn(MOCK_CALIBRATION_CONTENT, full_user_prompt)
        self.assertNotIn(MOCK_DESTINY_RULESET_CONTENT, full_user_prompt)
        self.assertNotIn("SYSTEM INSTRUCTIONS:", full_user_prompt)


    @patch('gemini_service.get_client')
    # Mock loader to return only destiny_ruleset content and empty for others
    @patch('gemini_service._load_instruction_file', side_effect=lambda x: MOCK_DESTINY_RULESET_CONTENT if x == 'destiny_ruleset' else "") 
    def test_get_initial_story_no_selected_prompts(self, mock_load_instruction_file, mock_get_client):
        """
        Tests get_initial_story when no specific prompts are selected (default behavior).
        Ensures only destiny_ruleset is included in system_instruction.
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
        
        # Verify system_instruction contains ONLY destiny_ruleset content
        self.assertIn('config', call_args.kwargs) 
        self.assertTrue(hasattr(call_args.kwargs['config'], 'system_instruction')) 
        self.assertEqual(call_args.kwargs['config'].system_instruction.text, MOCK_DESTINY_RULESET_CONTENT)


    @patch('gemini_service.get_client')
    @patch('gemini_service._load_instruction_file') # Patch for continue_story
    def test_continue_story_character_mode(self, mock_load_instruction_file, mock_get_client):
        """
        Tests the continue_story function in 'character' mode.
        Verifies system_instruction is passed correctly (narrative, mechanics, destiny_ruleset).
        """
        # Configure the mock for _load_instruction_file for continue_story
        def side_effect_for_loader(instruction_type):
            if instruction_type == "narrative":
                return MOCK_NARRATIVE_CONTENT
            elif instruction_type == "mechanics":
                return MOCK_MECHANICS_CONTENT
            elif instruction_type == "calibration": # Should not be loaded by continue_story's filter
                return MOCK_CALIBRATION_CONTENT
            elif instruction_type == "destiny_ruleset": # NEW
                return MOCK_DESTINY_RULESET_CONTENT
            return "" 

        mock_load_instruction_file.side_effect = side_effect_for_loader

        mock_client = MagicMock()
        # Corrected mock return value to match assertion
        mock_client.models.generate_content.return_value.text = "The story continues!"
        mock_get_client.return_value = mock_client

        user_input = "I inspect the strange orb."
        story_context = [{'actor': 'gemini', 'text': 'You see a strange orb on a pedestal.'}]
        selected_prompts = ['narrative', 'mechanics', 'calibration'] # Simulate all three selected from UI
        
        result = gemini_service.continue_story(user_input, "character", story_context, selected_prompts)

        self.assertEqual(result, "The story continues!")
        mock_client.models.generate_content.assert_called_once()
        
        call_args = mock_client.models.generate_content.call_args
        self.assertEqual(len(call_args.kwargs['contents']), 2) # Original story context + new user input
        
        # Access the user's turn (the last item in contents) which contains the combined prompt
        full_user_prompt_content_part = call_args.kwargs['contents'][-1].parts[0].text
        
        self.assertIn("Acting as the main character " + user_input + ".", full_user_prompt_content_part) 
        self.assertIn("Story: You see a strange orb on a pedestal.", full_user_prompt_content_part)
        self.assertIn("CONTEXT:\n", full_user_prompt_content_part)
        self.assertIn("YOUR TURN:\n", full_user_prompt_content_part)
        
        # Verify system_instruction parameter is passed and contains combined content (narrative, mechanics, destiny_ruleset)
        self.assertIn('config', call_args.kwargs)
        self.assertTrue(hasattr(call_args.kwargs['config'], 'system_instruction'))
        
        # Expected: Narrative, Mechanics, AND Destiny Ruleset, but NOT Calibration
        expected_system_instruction = f"{MOCK_NARRATIVE_CONTENT}\n\n{MOCK_MECHANICS_CONTENT}\n\n{MOCK_DESTINY_RULESET_CONTENT}"
        self.assertEqual(call_args.kwargs['config'].system_instruction.text, expected_system_instruction)
        self.assertNotIn(MOCK_CALIBRATION_CONTENT, call_args.kwargs['config'].system_instruction.text)


    @patch('gemini_service.get_client')
    @patch('gemini_service._load_instruction_file') # Patch for continue_story
    def test_continue_story_god_mode(self, mock_load_instruction_file, mock_get_client):
        """
        Tests the continue_story function in 'god' mode.
        Verifies system_instruction is passed correctly (narrative, destiny_ruleset).
        """
        # Configure the mock for _load_instruction_file for continue_story
        def side_effect_for_loader(instruction_type):
            if instruction_type == "narrative":
                return MOCK_NARRATIVE_CONTENT
            elif instruction_type == "calibration": # Should not be loaded by continue_story's filter
                return MOCK_CALIBRATION_CONTENT
            elif instruction_type == "destiny_ruleset": # NEW
                return MOCK_DESTINY_RULESET_CONTENT
            return ""

        mock_load_instruction_file.side_effect = side_effect_for_loader

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value.text = "An earthquake shakes the room."
        mock_get_client.return_value = mock_client

        user_input = "A dragon suddenly appears."
        story_context = [{'actor': 'gemini', 'text': 'The room is quiet.'}]
        selected_prompts = ['narrative', 'calibration'] # Simulate narrative and calibration selected
        
        result = gemini_service.continue_story(user_input, "god", story_context, selected_prompts)
        self.assertEqual(result, "An earthquake shakes the room.")
        mock_client.models.generate_content.assert_called_once()
        
        call_args = mock_client.models.generate_content.call_args
        # Assert that the contents list has 2 entries (one for context, one for user's turn)
        # If this assertion fails (e.g., 1 != 2), please verify the model_contents list construction
        # within the continue_story function in gemini_service.py.
        self.assertEqual(len(call_args.kwargs['contents']), 2) 
        
        # Access the user's turn (the last item in contents) which contains the combined prompt
        full_user_prompt_content_part = call_args.kwargs['contents'][-1].parts[0].text
        
        self.assertIn("Story: The room is quiet.", full_user_prompt_content_part) 
        self.assertIn("YOUR TURN:\nActing as the Game Master. " + user_input, full_user_prompt_content_part) 
        self.assertIn("CONTEXT:\n", full_user_prompt_content_part)

        # Verify system_instruction parameter is passed and contains combined content (narrative, destiny_ruleset)
        self.assertIn('config', call_args.kwargs)
        self.assertTrue(hasattr(call_args.kwargs['config'], 'system_instruction'))
        
        expected_system_instruction = f"{MOCK_NARRATIVE_CONTENT}\n\n{MOCK_DESTINY_RULESET_CONTENT}" # Only narrative and destiny should be present
        self.assertEqual(call_args.kwargs['config'].system_instruction.text, expected_system_instruction)
        self.assertNotIn(MOCK_CALIBRATION_CONTENT, call_args.kwargs['config'].system_instruction.text)

    @patch('gemini_service.get_client')
    @patch('logging.info') # Patch logging.info to capture log messages
    def test_call_gemini_api_logging(self, mock_logging_info, mock_get_client):
        """
        Tests that _call_gemini_api logs the latest prompt and full prompt contents correctly.
        Uses more robust string checks for log messages.
        """
        # Mock the client and its generate_content method
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value.text = "Mocked API Response"
        mock_get_client.return_value = mock_client

        # Create mock prompt_contents using our MockContent/MockPart classes
        long_prompt_text = "This is the latest user prompt, which can be quite long, exceeding 300 characters to test truncation in logging. This part should be correctly identified as the 'Latest Prompt' in the logs and truncated at 300 characters. The full contents of the prompt object should also be logged, but potentially truncated at 500 characters, especially since the repr of MockContent/MockPart might add some overhead. We need to be careful with exact string matching here."
        
        mock_prompt_contents = [
            MockContent(role='user', parts=[MockPart(text='This is the first turn.')]),
            MockContent(role='model', parts=[MockPart(text='This is the AI response to the first turn.')]),
            MockContent(role='user', parts=[MockPart(text=long_prompt_text)])
        ]
        
        mock_system_instruction = "System instruction text."

        # Call the function under test
        gemini_service._call_gemini_api(mock_prompt_contents, mock_system_instruction)

        # Assert that logging.info was called at least twice
        self.assertGreaterEqual(mock_logging_info.call_count, 2)

        # Get all calls made to logging.info
        log_calls = [call.args[0] for call in mock_logging_info.call_args_list]

        # --- Assert the first log call: "Latest Prompt" ---
        expected_latest_logged_prefix = long_prompt_text[:300]
        self.assertTrue(log_calls[0].startswith(f"--- Latest Prompt: {expected_latest_logged_prefix}"))
        
        # Check for truncation ellipsis based on length
        if len(long_prompt_text) > 300:
            self.assertTrue(log_calls[0].endswith("... ---"))
        else:
            self.assertTrue(log_calls[0].endswith(" ---"))

        # --- Assert the second log call: "Full Prompt Contents" ---
        self.assertTrue(log_calls[1].startswith("--- Full Prompt Contents: ["))
        
        # Check for presence of key parts to ensure the content is there without exact string matching repr()
        self.assertIn("MockContent(role='user'", log_calls[1])
        self.assertIn("MockContent(role='model'", log_calls[1])
        self.assertIn(f"MockPart(text='{long_prompt_text[:50]}", log_calls[1]) # Check for the start of the long text in the full repr

        # Check for truncation ellipsis based on overall string length (approximation for full_prompt_str[:500])
        # This is less precise because `str(mock_prompt_contents)` can be variable,
        # but ensures it's either fully logged or truncated.
        if len(str(mock_prompt_contents)) > 500:
            self.assertTrue(log_calls[1].endswith("... ---"))
        else:
            self.assertTrue(log_calls[1].endswith(" ---"))


        # Verify that the generate_content method was called as expected
        mock_client.models.generate_content.assert_called_once()
        call_args = mock_client.models.generate_content.call_args
        self.assertEqual(call_args.kwargs['contents'], mock_prompt_contents)
        self.assertEqual(call_args.kwargs['config'].system_instruction.text, mock_system_instruction)


if __name__ == '__main__':
    unittest.main()
