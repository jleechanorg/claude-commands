import unittest
from unittest.mock import patch, MagicMock
import logging
import sys
import constants
from gemini_service import _load_instruction_file, _loaded_instructions_cache
import gemini_service
import os

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
        
        prompts_dir = os.path.join(os.path.dirname(__file__), 'prompts')
        
        # 1. Get all .md files from the filesystem
        try:
            disk_files = {f for f in os.listdir(prompts_dir) if f.endswith('.md')}
        except FileNotFoundError:
            self.fail(f"Prompts directory not found at {prompts_dir}")

        # 2. Get all file basenames from the service's path_map
        service_files = {os.path.basename(p) for p in gemini_service.PATH_MAP.values()}

        # 3. Compare the sets
        unregistered_files = disk_files - service_files
        self.assertEqual(len(unregistered_files), 0,
                         f"Found .md files in prompts/ dir not registered in gemini_service.path_map: {unregistered_files}")

        missing_files = service_files - disk_files
        self.assertEqual(len(missing_files), 0,
                         f"Found files in gemini_service.path_map that do not exist in prompts/: {missing_files}")

if __name__ == '__main__':
    unittest.main() 