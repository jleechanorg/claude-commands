import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import shutil

# Ensure a dummy API key is set BEFORE we import the service.
os.environ["GEMINI_API_KEY"] = "DUMMY_KEY_FOR_TESTING"

import gemini_service

class TestInitialStoryPromptAssembly(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Create a temporary directory and dummy prompt files for all tests in this class."""
        cls.temp_dir = 'temp_test_prompts'
        os.makedirs(cls.temp_dir, exist_ok=True)
        
        # Create dummy files for all known prompt types
        for key, path in gemini_service.PATH_MAP.items():
            # We need to create the subdirectory if it doesn't exist
            full_path = os.path.join(cls.temp_dir, os.path.dirname(path))
            os.makedirs(full_path, exist_ok=True)
            
            # Now create the file
            with open(os.path.join(cls.temp_dir, path), 'w') as f:
                f.write(f"Content for {key}")

        # IMPORTANT: We must patch the PATH_MAP in gemini_service to point to our temp dir
        cls.original_path_map = gemini_service.PATH_MAP.copy()
        
        # New map pointing to the temp directory
        temp_path_map = {key: os.path.join(cls.temp_dir, path) for key, path in gemini_service.PATH_MAP.items()}
        
        # Create a patcher that we can start and stop
        cls.path_patcher = patch.dict(gemini_service.PATH_MAP, temp_path_map)
        cls.path_patcher.start()

    @classmethod
    def tearDownClass(cls):
        """Remove the temporary directory and files after all tests in this class."""
        # Stop the patcher
        cls.path_patcher.stop()
        
        # Clean up the temp directory
        shutil.rmtree(cls.temp_dir)

    def setUp(self):
        """Clear the cache before each test."""
        gemini_service._loaded_instructions_cache.clear()

    @patch('gemini_service.get_client')
    @patch('gemini_service._load_instruction_file')
    def test_all_checkboxes_scenario(self, mock_load_instruction_file, mock_get_client):
        """
        Tests that if all checkboxes are selected, all corresponding prompts
        are loaded in the correct order.
        """
        # --- Arrange ---
        # Mock the file loader to return simple, identifiable strings
        mock_content_map = {
            "narrative": "Narrative",
            "mechanics": "Mechanics",
            "calibration": "Calibration",
            "destiny_ruleset": "Destiny",
            "character_template": "CharTemplate",
            "character_sheet": "CharSheet",
            "game_state": "GameState",
            "srd": "SRD",
        }
        mock_load_instruction_file.side_effect = lambda type: mock_content_map.get(type, "")

        # Mock the Gemini client
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value.text = "Success"
        mock_get_client.return_value = mock_client

        # Define the input for this specific scenario
        selected_prompts = ['narrative', 'mechanics', 'calibration']
        include_srd = True
        
        # This is the sequence we expect based on the FIXED code
        expected_prompt_order = [
            "CharTemplate",      # From narrative checkbox
            "CharSheet",       # From mechanics checkbox
            "SRD",             # From SRD checkbox
            "Narrative",       # From loop
            "Mechanics",       # From loop
            "Calibration",     # From loop
            "Destiny",         # Default
            "GameState"        # Default
        ]
        expected_system_instruction = "\n\n".join(expected_prompt_order)

        # --- Act ---
        gemini_service.get_initial_story(
            "test prompt",
            selected_prompts=selected_prompts,
            include_srd=include_srd
        )

        # --- Assert ---
        mock_client.models.generate_content.assert_called_once()
        call_args = mock_client.models.generate_content.call_args
        actual_system_instruction = call_args.kwargs['config'].system_instruction.text
        
        self.assertEqual(actual_system_instruction, expected_system_instruction)

    @patch('gemini_service.get_client')
    @patch('gemini_service._load_instruction_file')
    def test_get_initial_story_no_selected_prompts(self, mock_load_instruction_file, mock_get_client):
        """Tests that get_initial_story loads only default prompts when none are selected."""
        # --- Arrange ---
        mock_content_map = { "destiny_ruleset": "Destiny", "game_state": "GameState" }
        mock_load_instruction_file.side_effect = lambda type: mock_content_map.get(type, "")
        
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value.text = "Success"
        mock_get_client.return_value = mock_client
        
        expected_system_instruction = "Destiny\n\nGameState"

        # --- Act ---
        gemini_service.get_initial_story("test prompt", selected_prompts=[], include_srd=False)

        # --- Assert ---
        call_args = mock_get_client.return_value.models.generate_content.call_args
        actual_system_instruction = call_args.kwargs['config'].system_instruction.text
        
        self.assertEqual(actual_system_instruction, expected_system_instruction)

    @patch('gemini_service.get_client')
    @patch('gemini_service._load_instruction_file')
    def test_only_narrative_scenario(self, mock_load_instruction_file, mock_get_client):
        """Tests that selecting only 'narrative' loads the correct prompt set."""
        # --- Arrange ---
        mock_content_map = { "narrative": "Narrative", "character_template": "CharTemplate", "destiny_ruleset": "Destiny", "game_state": "GameState" }
        mock_load_instruction_file.side_effect = lambda type: mock_content_map.get(type, "")
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value.text = "Success"
        mock_get_client.return_value = mock_client
        
        expected_prompt_order = ["CharTemplate", "Narrative", "Destiny", "GameState"]
        expected_system_instruction = "\n\n".join(expected_prompt_order)

        # --- Act ---
        gemini_service.get_initial_story("test", selected_prompts=['narrative'], include_srd=False)

        # --- Assert ---
        actual_system_instruction = mock_get_client.return_value.models.generate_content.call_args.kwargs['config'].system_instruction.text
        self.assertEqual(actual_system_instruction, expected_system_instruction)

    @patch('gemini_service.get_client')
    @patch('gemini_service._load_instruction_file')
    def test_only_mechanics_scenario(self, mock_load_instruction_file, mock_get_client):
        """Tests that selecting only 'mechanics' loads the correct prompt set."""
        # --- Arrange ---
        mock_content_map = { "mechanics": "Mechanics", "character_sheet": "CharSheet", "destiny_ruleset": "Destiny", "game_state": "GameState" }
        mock_load_instruction_file.side_effect = lambda type: mock_content_map.get(type, "")
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value.text = "Success"
        mock_get_client.return_value = mock_client
        
        expected_prompt_order = ["CharSheet", "Mechanics", "Destiny", "GameState"]
        expected_system_instruction = "\n\n".join(expected_prompt_order)

        # --- Act ---
        gemini_service.get_initial_story("test", selected_prompts=['mechanics'], include_srd=False)

        # --- Assert ---
        actual_system_instruction = mock_get_client.return_value.models.generate_content.call_args.kwargs['config'].system_instruction.text
        self.assertEqual(actual_system_instruction, expected_system_instruction)

    @patch('gemini_service.get_client')
    @patch('gemini_service._load_instruction_file')
    def test_only_calibration_scenario(self, mock_load_instruction_file, mock_get_client):
        """Tests that selecting only 'calibration' loads the correct prompt set."""
        # --- Arrange ---
        mock_content_map = { "calibration": "Calibration", "destiny_ruleset": "Destiny", "game_state": "GameState" }
        mock_load_instruction_file.side_effect = lambda type: mock_content_map.get(type, "")
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value.text = "Success"
        mock_get_client.return_value = mock_client
        
        expected_prompt_order = ["Calibration", "Destiny", "GameState"]
        expected_system_instruction = "\n\n".join(expected_prompt_order)

        # --- Act ---
        gemini_service.get_initial_story("test", selected_prompts=['calibration'], include_srd=False)

        # --- Assert ---
        actual_system_instruction = mock_get_client.return_value.models.generate_content.call_args.kwargs['config'].system_instruction.text
        self.assertEqual(actual_system_instruction, expected_system_instruction)

if __name__ == '__main__':
    unittest.main()
