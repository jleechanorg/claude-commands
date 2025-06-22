import unittest
import os
import json
from unittest.mock import patch, MagicMock
import constants

# We still need the dummy key for the import-time initialization check
os.environ["GEMINI_API_KEY"] = "DUMMY_KEY_FOR_INTEGRATION_TESTING"

# Create dummy prompts directory and files for integration tests to prevent FileNotFoundError during import
if not os.path.exists('./prompts'):
    os.makedirs('./prompts')
with open('./prompts/narrative_system_instruction.md', 'w') as f:
    f.write("Integration test narrative instruction.")
with open('./prompts/mechanics_system_instruction.md', 'w') as f:
    f.write("Integration test mechanics instruction.")
with open('./prompts/calibration_instruction.md', 'w') as f:
    f.write("Integration test calibration instruction.")


import main
import gemini_service # Import gemini_service to mock its internal _load_instruction_file

# Define mock system instruction content for consistent integration testing
MOCK_INTEGRATION_NARRATIVE = "Integration narrative."
MOCK_INTEGRATION_MECHANICS = "Integration mechanics."
MOCK_INTEGRATION_CALIBRATION = "Integration calibration."
MOCK_INTEGRATION_CHAR_TEMPLATE = "Integration char_template."
MOCK_INTEGRATION_CHAR_SHEET = "Integration char_sheet."
MOCK_INTEGRATION_DESTINY = "Integration destiny."
MOCK_INTEGRATION_GAME_STATE = "Integration game_state."


class TestInteractionIntegration(unittest.TestCase):

    @patch('gemini_service._load_personality_profile_file')
    @patch('gemini_service._load_instruction_file')
    def setUp(self, mock_load_instruction_file, mock_load_personality_file):
        """
        Set up a test client and create a new campaign for each test.
        """
        # Configure the mock for the new personality file loader
        mock_load_personality_file.return_value = ""
        
        # Configure the mock for _load_instruction_file to return specific content for integration tests
        def side_effect_for_loader(instruction_type):
            if instruction_type == constants.PROMPT_TYPE_NARRATIVE:
                return MOCK_INTEGRATION_NARRATIVE
            elif instruction_type == constants.PROMPT_TYPE_MECHANICS:
                return MOCK_INTEGRATION_MECHANICS
            elif instruction_type == constants.PROMPT_TYPE_CALIBRATION:
                return MOCK_INTEGRATION_CALIBRATION
            elif instruction_type == constants.PROMPT_TYPE_CHARACTER_TEMPLATE:
                return MOCK_INTEGRATION_CHAR_TEMPLATE
            elif instruction_type == constants.PROMPT_TYPE_CHARACTER_SHEET:
                return MOCK_INTEGRATION_CHAR_SHEET
            elif instruction_type == constants.PROMPT_TYPE_DESTINY:
                return MOCK_INTEGRATION_DESTINY
            elif instruction_type == constants.PROMPT_TYPE_GAME_STATE:
                return MOCK_INTEGRATION_GAME_STATE
            return f"UNHANDLED_PROMPT_{instruction_type}"

        mock_load_instruction_file.side_effect = side_effect_for_loader

        # 1. Create a patcher for the get_client function.
        self.patcher = patch('gemini_service.get_client')
        
        # 2. Start the patcher and get the mock object.
        mock_get_client = self.patcher.start()
        
        # 3. Configure the mock client that all tests in this class will use.
        self.mock_client = MagicMock()
        mock_get_client.return_value = self.mock_client
        
        # Configure the mock for the 'create campaign' call in this setUp method
        # This will be called by gemini_service.get_initial_story
        self.mock_client.models.generate_content.return_value.text = "This is a test opening story."
        
        # Standard setup
        self.app = main.create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.user_id = "test-suite-user-123"

        print("\n--- (setUp) Creating a new campaign for the test ---")
        # Define the selected prompts for the campaign creation
        self.test_selected_prompts = ['narrative', 'mechanics'] 
        
        create_response = self.client.post(
            '/api/campaigns',
            headers={'Content-Type': 'application/json', 'X-Test-Bypass-Auth': 'true', 'X-Test-User-ID': self.user_id},
            # Pass selected_prompts in the data payload
            data=json.dumps({'prompt': 'A test campaign', 'title': 'Integration Test', 'selected_prompts': self.test_selected_prompts})
        )
        self.assertEqual(create_response.status_code, 201, "Failed to create campaign in setUp")
        create_data = create_response.get_json()
        self.campaign_id = create_data.get('campaign_id')
        self.assertIsNotNone(self.campaign_id, "Campaign ID not found in setUp response")
        print(f"--- (setUp) Campaign {self.campaign_id} created ---")

        # Now, fetch the campaign to ensure selected_prompts are stored
        campaign_check_response = self.client.get(
            f'/api/campaigns/{self.campaign_id}',
            headers={'X-Test-Bypass-Auth': 'true', 'X-Test-User-ID': self.user_id}
        )
        self.assertEqual(campaign_check_response.status_code, 200)
        campaign_data = campaign_check_response.get_json().get('campaign')
        self.assertEqual(campaign_data.get('selected_prompts'), self.test_selected_prompts)


    def tearDown(self):
        """
        Clean up any test data and stop the patcher.
        """
        # 4. Stop the patcher to clean up the environment after each test.
        self.patcher.stop()
        print(f"--- (tearDown) Test finished for campaign {self.campaign_id} ---")
        pass

    def test_character_mode_interaction(self):
        """
        Tests a full interaction flow using 'character' mode.
        Verifies system_instruction is passed correctly on continue_story.
        """
        self.mock_client.models.generate_content.return_value.text = "The character sees a door."
        
        print("\n--- RUNNING: test_character_mode_interaction ---")
        response = self.client.post(
            f'/api/campaigns/{self.campaign_id}/interaction',
            headers={'Content-Type': 'application/json', 'X-Test-Bypass-Auth': 'true', 'X-Test-User-ID': self.user_id},
            data=json.dumps({'input': 'I check the door for traps.', 'mode': 'character'})
        )
        print(f"Character Mode Response: {response.get_data(as_text=True)}")
        self.assertEqual(response.status_code, 200)
        response_data = response.get_json()
        self.assertEqual(response_data.get('response'), "The character sees a door.")

        # Verify gemini_service._call_gemini_api was called with correct system_instruction
        self.mock_client.models.generate_content.assert_called() # Ensure it was called at least once
        call_args = self.mock_client.models.generate_content.call_args_list[-1] # Get the last call

        # Check that the system_instruction parameter was part of the config
        self.assertIn('config', call_args.kwargs)
        self.assertIn('system_instruction', call_args.kwargs['config'])
        
        # Based on the logic in continue_story and selected_prompts=['narrative', 'mechanics']
        expected_parts = [
            MOCK_INTEGRATION_CHAR_TEMPLATE,
            MOCK_INTEGRATION_CHAR_SHEET,
            MOCK_INTEGRATION_NARRATIVE,
            MOCK_INTEGRATION_MECHANICS,
            MOCK_INTEGRATION_DESTINY,
            MOCK_INTEGRATION_GAME_STATE,
        ]
        expected_system_instruction = "\\n\\n".join(expected_parts)
        self.assertEqual(call_args.kwargs['config'].system_instruction.text, expected_system_instruction)


    def test_god_mode_interaction(self):
        """
        Tests a full interaction flow using 'god' mode.
        Verifies system_instruction is passed correctly on continue_story.
        """
        self.mock_client.models.generate_content.return_value.text = "An earthquake shakes the room."

        print("\n--- RUNNING: test_god_mode_interaction ---")
        response = self.client.post(
            f'/api/campaigns/{self.campaign_id}/interaction',
            headers={'Content-Type': 'application/json', 'X-Test-Bypass-Auth': 'true', 'X-Test-User-ID': self.user_id},
            data=json.dumps({'input': 'A sudden earthquake shakes the dungeon.', 'mode': 'god'})
        )
        print(f"God Mode Response: {response.get_data(as_text=True)}")
        self.assertEqual(response.status_code, 200)
        response_data = response.get_json()
        self.assertEqual(response_data.get('response'), "An earthquake shakes the room.")

        # Verify gemini_service._call_gemini_api was called with correct system_instruction
        self.mock_client.models.generate_content.assert_called() # Ensure it was called at least once
        call_args = self.mock_client.models.generate_content.call_args_list[-1] # Get the last call

        self.assertIn('config', call_args.kwargs)
        self.assertIn('system_instruction', call_args.kwargs['config'])
        
        expected_parts = [
            MOCK_INTEGRATION_CHAR_TEMPLATE,
            MOCK_INTEGRATION_CHAR_SHEET,
            MOCK_INTEGRATION_NARRATIVE,
            MOCK_INTEGRATION_MECHANICS,
            MOCK_INTEGRATION_DESTINY,
            MOCK_INTEGRATION_GAME_STATE,
        ]
        expected_system_instruction = "\\n\\n".join(expected_parts)
        self.assertEqual(call_args.kwargs['config'].system_instruction.text, expected_system_instruction)


if __name__ == '__main__':
    unittest.main()
