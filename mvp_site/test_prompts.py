import unittest
import logging
import constants
from gemini_service import _load_instruction_file, _loaded_instructions_cache

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
        
        for p_type in PROMPT_TYPES_TO_TEST:
            with self.subTest(prompt_type=p_type):
                # Call the actual function from the service
                content = _load_instruction_file(p_type)
                
                # Assert that the content is a non-empty string
                self.assertIsInstance(content, str, f"Content for {p_type} should be a string.")
                self.assertGreater(len(content), 0, f"Prompt file for {p_type} should not be empty.")

    def test_loading_unknown_prompt_returns_empty_string(self):
        """
        Ensures that calling _load_instruction_file with an unknown type
        returns an empty string and does not raise an error.
        """
        logging.info("--- Running Test: test_loading_unknown_prompt_returns_empty_string ---")
        content = _load_instruction_file("this_is_not_a_real_prompt_type")
        self.assertEqual(content, "")

if __name__ == '__main__':
    unittest.main() 