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
        """Create a temporary prompts directory and dummy files for testing."""
        cls.prompts_dir = './prompts_test_temp'
        if os.path.exists(cls.prompts_dir):
            shutil.rmtree(cls.prompts_dir)
        os.makedirs(cls.prompts_dir)

        files_to_create = {
            "narrative_system_instruction.md": "Narrative",
            "mechanics_system_instruction.md": "Mechanics",
            "calibration_instruction.md": "Calibration",
            "destiny_ruleset.md": "Destiny",
            "character_template.md": "CharTemplate",
            "character_sheet_template.md": "CharSheet",
            "game_state_instruction.md": "GameState",
            "5e_SRD_All.md": "SRD"
        }
        for filename, content in files_to_create.items():
            with open(os.path.join(cls.prompts_dir, filename), 'w') as f:
                f.write(content)

    @classmethod
    def tearDownClass(cls):
        """Remove the temporary prompts directory and its contents after tests."""
        shutil.rmtree(cls.prompts_dir)

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

if __name__ == '__main__':
    unittest.main()
