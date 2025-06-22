import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import shutil
import logging
import constants
from game_state import GameState
from gemini_service import _load_instruction_file, _loaded_instructions_cache

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
        # This now points to the original, canonical path map to ensure we create the right structure
        for key, path in gemini_service.PATH_MAP.items():
            full_path = os.path.join(cls.temp_dir, os.path.dirname(path))
            os.makedirs(full_path, exist_ok=True)
            with open(os.path.join(cls.temp_dir, path), 'w') as f:
                f.write(f"Content for {key}")

        cls.original_path_map = gemini_service.PATH_MAP.copy()
        # The patch needs to be on the gemini_service module's PATH_MAP
        cls.path_patcher = patch.dict(gemini_service.PATH_MAP, {key: os.path.join(cls.temp_dir, path) for key, path in cls.original_path_map.items()})
        cls.path_patcher.start()


    @classmethod
    def tearDownClass(cls):
        """Remove the temporary directory and files after all tests in this class."""
        cls.path_patcher.stop()
        shutil.rmtree(cls.temp_dir)

    def setUp(self):
        """Clear the cache before each test."""
        gemini_service._loaded_instructions_cache.clear()
        gemini_service._clear_client() # Also clear the client to reset mocks

    @patch('gemini_service._call_gemini_api')
    @patch('gemini_service._load_instruction_file')
    def test_all_checkboxes_scenario(self, mock_load_instruction_file, mock_call_gemini):
        """
        Tests that if all checkboxes are selected, all corresponding prompts
        are loaded in the correct order.
        """
        # --- Arrange ---
        mock_content_map = {
            constants.PROMPT_TYPE_NARRATIVE: "Narrative",
            constants.PROMPT_TYPE_MECHANICS: "Mechanics",
            constants.PROMPT_TYPE_CALIBRATION: "Calibration",
            constants.PROMPT_TYPE_CHARACTER_TEMPLATE: "CharTemplate",
        }
        mock_load_instruction_file.side_effect = lambda type: mock_content_map.get(type, f"UNEXPECTED_PROMPT_{type}")
        mock_call_gemini.return_value = MagicMock(text="Success")

        selected_prompts = ['narrative', 'mechanics', 'calibration']
        
        # This is the sequence we expect based on the NEW code
        expected_prompt_order = [
            "Narrative",       # Default
            "CharTemplate",    # Default
            "Mechanics",       # From loop
            "Calibration",     # From loop
        ]
        expected_system_instruction = "\\n\\n".join(expected_prompt_order)

        # --- Act ---
        gemini_service.get_initial_story("test prompt", selected_prompts=selected_prompts, include_srd=True)

        # --- Assert ---
        mock_call_gemini.assert_called_once()
        call_args = mock_call_gemini.call_args
        actual_system_instruction = call_args.kwargs['system_instruction_text']
        self.assertEqual(actual_system_instruction, expected_system_instruction)

    @patch('gemini_service._call_gemini_api')
    @patch('gemini_service._load_instruction_file')
    def test_get_initial_story_no_selected_prompts(self, mock_load_instruction_file, mock_call_gemini):
        """Tests that get_initial_story loads only default prompts when none are selected."""
        # --- Arrange ---
        mock_content_map = {
            constants.PROMPT_TYPE_NARRATIVE: "Narrative",
            constants.PROMPT_TYPE_CHARACTER_TEMPLATE: "CharTemplate",
        }
        mock_load_instruction_file.side_effect = lambda type: mock_content_map.get(type, "")
        mock_call_gemini.return_value = MagicMock(text="Success")
        
        expected_system_instruction = "Narrative\\n\\nCharTemplate"

        # --- Act ---
        gemini_service.get_initial_story("test prompt", selected_prompts=[], include_srd=False)

        # --- Assert ---
        call_args = mock_call_gemini.call_args
        actual_system_instruction = call_args.kwargs['system_instruction_text']
        self.assertEqual(actual_system_instruction, expected_system_instruction)

    @patch('gemini_service._call_gemini_api')
    @patch('gemini_service._load_instruction_file')
    def test_only_narrative_scenario(self, mock_load_instruction_file, mock_call_gemini):
        """Tests that selecting only 'narrative' does not add duplicates."""
        # --- Arrange ---
        mock_content_map = {
            constants.PROMPT_TYPE_NARRATIVE: "Narrative",
            constants.PROMPT_TYPE_CHARACTER_TEMPLATE: "CharTemplate",
        }
        mock_load_instruction_file.side_effect = lambda type: mock_content_map.get(type, "")
        mock_call_gemini.return_value = MagicMock(text="Success")
        
        expected_prompt_order = ["Narrative", "CharTemplate"] # Narrative is not added twice
        expected_system_instruction = "\\n\\n".join(expected_prompt_order)

        # --- Act ---
        gemini_service.get_initial_story("test", selected_prompts=['narrative'], include_srd=False)

        # --- Assert ---
        actual_system_instruction = mock_call_gemini.call_args.kwargs['system_instruction_text']
        self.assertEqual(actual_system_instruction, expected_system_instruction)

    @patch('gemini_service._call_gemini_api')
    @patch('gemini_service._load_instruction_file')
    def test_only_mechanics_scenario(self, mock_load_instruction_file, mock_call_gemini):
        """Tests that selecting only 'mechanics' loads the correct prompt set."""
        # --- Arrange ---
        mock_content_map = {
            constants.PROMPT_TYPE_NARRATIVE: "Narrative",
            constants.PROMPT_TYPE_CHARACTER_TEMPLATE: "CharTemplate",
            constants.PROMPT_TYPE_MECHANICS: "Mechanics",
        }
        mock_load_instruction_file.side_effect = lambda type: mock_content_map.get(type, "")
        mock_call_gemini.return_value = MagicMock(text="Success")
        
        expected_prompt_order = ["Narrative", "CharTemplate", "Mechanics"]
        expected_system_instruction = "\\n\\n".join(expected_prompt_order)

        # --- Act ---
        gemini_service.get_initial_story("test", selected_prompts=['mechanics'], include_srd=False)

        # --- Assert ---
        actual_system_instruction = mock_call_gemini.call_args.kwargs['system_instruction_text']
        self.assertEqual(actual_system_instruction, expected_system_instruction)

    @patch('gemini_service._call_gemini_api')
    @patch('gemini_service._load_instruction_file')
    def test_only_calibration_scenario(self, mock_load_instruction_file, mock_call_gemini):
        """Tests that selecting only 'calibration' loads the correct prompt set."""
        # --- Arrange ---
        mock_content_map = {
            constants.PROMPT_TYPE_NARRATIVE: "Narrative",
            constants.PROMPT_TYPE_CHARACTER_TEMPLATE: "CharTemplate",
            constants.PROMPT_TYPE_CALIBRATION: "Calibration",
        }
        mock_load_instruction_file.side_effect = lambda type: mock_content_map.get(type, "")
        mock_call_gemini.return_value = MagicMock(text="Success")
        
        expected_prompt_order = ["Narrative", "CharTemplate", "Calibration"]
        expected_system_instruction = "\\n\\n".join(expected_prompt_order)

        # --- Act ---
        gemini_service.get_initial_story("test", selected_prompts=['calibration'], include_srd=False)

        # --- Assert ---
        actual_system_instruction = mock_call_gemini.call_args.kwargs['system_instruction_text']
        self.assertEqual(actual_system_instruction, expected_system_instruction)

class TestStaticPromptParts(unittest.TestCase):
    def test_core_memories_formatting_with_memories(self):
        """
        Tests that core memories are correctly formatted into a summary string when they exist.
        """
        # --- Arrange ---
        mock_game_state = MagicMock()
        mock_game_state.custom_campaign_state = {
            'core_memories': [
                "Defeated the goblin king.",
                "Found the ancient amulet."
            ]
        }
        mock_game_state.world_data = {}
        mock_game_state.player_character_data = {}

        expected_summary = (
            "CORE MEMORY LOG (SUMMARY OF KEY EVENTS):\\n"
            "- Defeated the goblin king.\\n"
            "- Found the ancient amulet.\\n\\n"
        )

        # --- Act ---
        _, core_memories_summary, _ = gemini_service._get_static_prompt_parts(mock_game_state, [])

        # --- Assert ---
        self.assertEqual(core_memories_summary, expected_summary)

    def test_core_memories_formatting_no_memories(self):
        """
        Tests that an empty string is returned when there are no core memories.
        """
        # --- Arrange ---
        mock_game_state = MagicMock()
        mock_game_state.custom_campaign_state = {'core_memories': []}
        mock_game_state.world_data = {}
        mock_game_state.player_character_data = {}

        # --- Act ---
        _, core_memories_summary, _ = gemini_service._get_static_prompt_parts(mock_game_state, [])

        # --- Assert ---
        self.assertEqual(core_memories_summary, "")

class TestContextTruncation(unittest.TestCase):
    @patch('gemini_service._get_context_stats')
    def test_context_just_under_limit_no_truncation(self, mock_get_stats):
        """
        Tests that if the context is under the char limit, it's returned unmodified.
        """
        # --- Arrange ---
        mock_get_stats.return_value = "Stats: N/A" # Mock the stats function
        mock_game_state = MagicMock(spec=GameState)
        story_context = [{'actor': 'system', 'text': 'a' * 100}]
        
        # --- Act ---
        truncated_context = gemini_service._truncate_context(
            story_context, 
            max_chars=101, 
            model_name='test-model',
            current_game_state=mock_game_state
        )
        
        # --- Assert ---
        self.assertEqual(len(truncated_context), 1)

    @patch('gemini_service._get_context_stats')
    def test_context_over_limit_is_truncated(self, mock_get_stats):
        """
        Tests that if the context is over the char limit, it's truncated
        correctly according to the start/end turn counts.
        """
        # --- Arrange ---
        mock_get_stats.return_value = "Stats: N/A"
        mock_game_state = MagicMock(spec=GameState)
        # Create a context that is definitely over the limit
        story_context = [{'actor': 'system', 'text': 'a' * 100}] * 20 

        # --- Act ---
        truncated_context = gemini_service._truncate_context(
            story_context, 
            max_chars=500, # Much smaller than the context
            model_name='test-model',
            turns_to_keep_at_start=5,
            turns_to_keep_at_end=5,
            current_game_state=mock_game_state
        )
        
        # --- Assert ---
        # 5 start + 5 end + 1 marker = 11
        self.assertEqual(len(truncated_context), 11)
        self.assertIn('[...several moments, scenes, or days have passed...]', truncated_context[5]['text'])

# The list of all known prompt types to test, using shared constants.
PROMPT_TYPES_TO_TEST = [
    constants.PROMPT_TYPE_NARRATIVE,
    constants.PROMPT_TYPE_MECHANICS,
    constants.PROMPT_TYPE_CALIBRATION,
    constants.PROMPT_TYPE_DESTINY,
    constants.PROMPT_TYPE_GAME_STATE,
    constants.PROMPT_TYPE_SRD
]

class TestPromptLoading(unittest.TestCase):

    def setUp(self):
        """Clear the instruction cache before each test to ensure isolation."""
        _loaded_instructions_cache.clear()

    def test_all_prompts_are_loadable_via_service(self):
        """
        Ensures that all referenced prompt files can be loaded successfully
        by calling the actual _load_instruction_file function.
        """
        logging.info("--- Running Test: test_all_prompts_are_loadable_via_service ---")
        
        for p_type in gemini_service.PATH_MAP.keys():
            content = _load_instruction_file(p_type)
            self.assertIsInstance(content, str)
            self.assertGreater(len(content), 0, f"Prompt file for {p_type} should not be empty.")

    def test_loading_unknown_prompt_raises_error(self):
        """Ensures that requesting a non-existent prompt type raises a ValueError."""
        logging.info("--- Running Test: test_loading_unknown_prompt_raises_error ---")
        with self.assertRaises(ValueError):
            _load_instruction_file("this_is_not_a_real_prompt_type")

    def test_all_prompt_files_are_registered_in_service(self):
        """
        Ensures that every .md file in the top-level prompts directory is
        registered in gemini_service.PATH_MAP. It ignores subdirectories.
        """
        logging.info("--- Running Test: test_all_prompt_files_are_registered_in_service ---")
        prompts_dir = os.path.join(os.path.dirname(__file__), 'prompts')
        registered_filenames = {os.path.basename(p) for p in gemini_service.PATH_MAP.values()}
        
        found_files = set()
        # We only walk the top-level directory, ignoring subdirectories
        for item in os.listdir(prompts_dir):
            if os.path.isfile(os.path.join(prompts_dir, item)) and item.endswith('.md'):
                found_files.add(item)
                
        unregistered_files = found_files - registered_filenames
        
        self.assertEqual(len(unregistered_files), 0, 
            f"Found .md files in prompts/ dir not registered in gemini_service.PATH_MAP: {unregistered_files}")


if __name__ == '__main__':
    unittest.main()
