import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import shutil
import logging
import constants
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
        # Create a story context with a known character count
        story_context = [
            {'text': 'a' * 100}, # 100 chars
            {'text': 'b' * 100}, # 100 chars
            {'text': 'c' * 100}  # 100 chars
        ] # Total 300 chars
        
        # Set a budget that is slightly larger than the context
        char_budget = 301
        
        # --- Act ---
        # We are testing _truncate_context directly
        truncated_context = gemini_service._truncate_context(
            story_context,
            max_chars=char_budget,
            model_name='test-model' # model name is needed for logging stats
        )
        
        # --- Assert ---
        # The context should be unchanged
        self.assertEqual(len(truncated_context), 3)
        self.assertEqual(story_context, truncated_context)

    @patch('gemini_service._get_context_stats')
    def test_context_over_limit_is_truncated(self, mock_get_stats):
        """
        Tests that if the context is over the char limit, it's truncated
        by keeping a few turns from the start and end.
        """
        # --- Arrange ---
        mock_get_stats.return_value = "Stats: N/A" # Mock the stats function
        # Create a long story context (e.g., 200 turns)
        story_context = [{'text': f'Turn {i}'} for i in range(200)]
        
        # Set a very small budget to force truncation
        char_budget = 10
        
        # Get the configured number of turns to keep from the constants
        turns_start = gemini_service.TURNS_TO_KEEP_AT_START
        turns_end = gemini_service.TURNS_TO_KEEP_AT_END

        # --- Act ---
        truncated_context = gemini_service._truncate_context(
            story_context,
            max_chars=char_budget,
            model_name='test-model'
        )
        
        # --- Assert ---
        # The total length should be start_turns + end_turns + 1 (for the marker)
        self.assertEqual(len(truncated_context), turns_start + turns_end + 1)
        
        # Check if the first part is correct
        self.assertEqual(truncated_context[0], story_context[0])
        self.assertEqual(truncated_context[turns_start - 1], story_context[turns_start - 1])
        
        # Check if the marker is present
        self.assertEqual(truncated_context[turns_start]['actor'], 'system')
        
        # Check if the last part is correct
        self.assertEqual(truncated_context[-1], story_context[-1])

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
        """
        Ensures that calling _load_instruction_file with an unknown type
        correctly raises a ValueError, following the strict loading policy.
        """
        logging.info("--- Running Test: test_loading_unknown_prompt_raises_error ---")
        with self.assertRaises(ValueError):
            _load_instruction_file("this_is_not_a_real_prompt_type")

    def test_all_prompt_files_are_registered_in_service(self):
        """
        Ensures that every .md file in the prompts directory is registered
        in the gemini_service.path_map, and vice-versa. This prevents
        un-loaded or orphaned prompt files.
        """
        logging.info("--- Running Test: test_all_prompt_files_are_registered_in_service ---")
        
        # This test needs to look in the actual prompts directory, not a temp one.
        # It's testing the real state of the project.
        prompts_dir = os.path.join(os.path.dirname(__file__), 'prompts')
        
        # 1. Get all .md files from the filesystem
        try:
            # We need to handle subdirectories like 'archive'
            disk_files = set()
            for root, dirs, files in os.walk(prompts_dir):
                # Exclude archive directory from this test
                if 'archive' in dirs:
                    dirs.remove('archive')
                for f in files:
                    if f.endswith('.md'):
                        disk_files.add(f)

        except FileNotFoundError:
            self.fail(f"Prompts directory not found at {prompts_dir}")

        # 2. Get all file basenames from the service's path_map
        service_files = {os.path.basename(p) for p in gemini_service.PATH_MAP.values()}

        # 3. Compare the sets
        unregistered_files = disk_files - service_files
        self.assertEqual(len(unregistered_files), 0,
                         f"Found .md files in prompts/ dir not registered in gemini_service.PATH_MAP: {unregistered_files}")

        missing_files = service_files - disk_files
        self.assertEqual(len(missing_files), 0,
                         f"Found files in gemini_service.PATH_MAP that do not exist in prompts/: {missing_files}")


if __name__ == '__main__':
    unittest.main()
