import unittest
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import constants


class TestConstants(unittest.TestCase):
    """Test constants module values and structure."""
    
    def test_actor_constants(self):
        """Test actor constants are properly defined."""
        self.assertEqual(constants.ACTOR_USER, 'user')
        self.assertEqual(constants.ACTOR_GEMINI, 'gemini')
    
    def test_interaction_mode_constants(self):
        """Test interaction mode constants."""
        self.assertEqual(constants.MODE_CHARACTER, 'character')
        self.assertEqual(constants.MODE_GOD, 'god')
    
    def test_dictionary_key_constants(self):
        """Test dictionary key constants."""
        self.assertEqual(constants.KEY_ACTOR, 'actor')
        self.assertEqual(constants.KEY_MODE, 'mode')
        self.assertEqual(constants.KEY_TEXT, 'text')
        self.assertEqual(constants.KEY_TITLE, 'title')
        self.assertEqual(constants.KEY_FORMAT, 'format')
        self.assertEqual(constants.KEY_USER_INPUT, 'user_input')
        self.assertEqual(constants.KEY_SELECTED_PROMPTS, 'selected_prompts')
        self.assertEqual(constants.KEY_MBTI, 'mbti')
    
    def test_export_format_constants(self):
        """Test export format constants."""
        self.assertEqual(constants.FORMAT_PDF, 'pdf')
        self.assertEqual(constants.FORMAT_DOCX, 'docx')
        self.assertEqual(constants.FORMAT_TXT, 'txt')
        
        # Test MIME types
        self.assertEqual(constants.MIMETYPE_PDF, 'application/pdf')
        self.assertEqual(constants.MIMETYPE_DOCX, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        self.assertEqual(constants.MIMETYPE_TXT, 'text/plain')
    
    def test_prompt_filename_constants(self):
        """Test prompt filename constants."""
        self.assertEqual(constants.FILENAME_NARRATIVE, "narrative_system_instruction.md")
        self.assertEqual(constants.FILENAME_MECHANICS, "mechanics_system_instruction.md")
        self.assertEqual(constants.FILENAME_GAME_STATE, "game_state_instruction.md")
        self.assertEqual(constants.FILENAME_CHARACTER_TEMPLATE, "character_template.md")
        self.assertEqual(constants.FILENAME_MASTER_DIRECTIVE, "master_directive.md")
        self.assertEqual(constants.FILENAME_DND_SRD, "dnd_srd_instruction.md")
    
    def test_prompt_type_constants(self):
        """Test prompt type constants."""
        self.assertEqual(constants.PROMPT_TYPE_NARRATIVE, "narrative")
        self.assertEqual(constants.PROMPT_TYPE_MECHANICS, "mechanics")
        self.assertEqual(constants.PROMPT_TYPE_GAME_STATE, "game_state")
        self.assertEqual(constants.PROMPT_TYPE_CHARACTER_TEMPLATE, "character_template")
        self.assertEqual(constants.PROMPT_TYPE_MASTER_DIRECTIVE, "master_directive")
        self.assertEqual(constants.PROMPT_TYPE_DND_SRD, "dnd_srd")
    
    def test_prompt_path_constants(self):
        """Test prompt path constants are properly constructed."""
        expected_prompts_dir = "prompts"
        self.assertEqual(constants.PROMPTS_DIR, expected_prompts_dir)
        
        # Test that paths are properly joined with os.path.join
        self.assertEqual(
            constants.NARRATIVE_SYSTEM_INSTRUCTION_PATH,
            os.path.join(expected_prompts_dir, "narrative_system_instruction.md")
        )
        self.assertEqual(
            constants.MECHANICS_SYSTEM_INSTRUCTION_PATH,
            os.path.join(expected_prompts_dir, "mechanics_system_instruction.md")
        )
        self.assertEqual(
            constants.CHARACTER_TEMPLATE_PATH,
            os.path.join(expected_prompts_dir, "character_template.md")
        )
        self.assertEqual(
            constants.GAME_STATE_INSTRUCTION_PATH,
            os.path.join(expected_prompts_dir, "game_state_instruction.md")
        )
        self.assertEqual(
            constants.MASTER_DIRECTIVE_PATH,
            os.path.join(expected_prompts_dir, "master_directive.md")
        )
        self.assertEqual(
            constants.DND_SRD_INSTRUCTION_PATH,
            os.path.join(expected_prompts_dir, "dnd_srd_instruction.md")
        )
    
    def test_constants_are_strings(self):
        """Test that all constants are strings (no accidental None values)."""
        string_constants = [
            constants.ACTOR_USER, constants.ACTOR_GEMINI,
            constants.MODE_CHARACTER, constants.MODE_GOD,
            constants.KEY_ACTOR, constants.KEY_MODE, constants.KEY_TEXT,
            constants.KEY_TITLE, constants.KEY_FORMAT, constants.KEY_USER_INPUT,
            constants.KEY_SELECTED_PROMPTS, constants.KEY_MBTI,
            constants.FORMAT_PDF, constants.FORMAT_DOCX, constants.FORMAT_TXT,
            constants.MIMETYPE_PDF, constants.MIMETYPE_DOCX, constants.MIMETYPE_TXT,
            constants.FILENAME_NARRATIVE, constants.FILENAME_MECHANICS,
            constants.FILENAME_GAME_STATE, constants.FILENAME_CHARACTER_TEMPLATE,
            constants.FILENAME_MASTER_DIRECTIVE, constants.FILENAME_DND_SRD,
            constants.PROMPT_TYPE_NARRATIVE, constants.PROMPT_TYPE_MECHANICS,
            constants.PROMPT_TYPE_GAME_STATE, constants.PROMPT_TYPE_CHARACTER_TEMPLATE,
            constants.PROMPT_TYPE_MASTER_DIRECTIVE, constants.PROMPT_TYPE_DND_SRD,
            constants.PROMPTS_DIR, constants.NARRATIVE_SYSTEM_INSTRUCTION_PATH,
            constants.MECHANICS_SYSTEM_INSTRUCTION_PATH, constants.CHARACTER_TEMPLATE_PATH,
            constants.GAME_STATE_INSTRUCTION_PATH, constants.MASTER_DIRECTIVE_PATH,
            constants.DND_SRD_INSTRUCTION_PATH
        ]
        
        for constant in string_constants:
            with self.subTest(constant=constant):
                self.assertIsInstance(constant, str)
                self.assertNotEqual(constant, "")  # Ensure no empty strings
    
    def test_constants_immutability_pattern(self):
        """Test that constants follow immutability patterns (uppercase naming)."""
        # Test that key constants are uppercase
        self.assertTrue(hasattr(constants, 'ACTOR_USER'))
        self.assertTrue(hasattr(constants, 'MODE_CHARACTER'))
        self.assertTrue(hasattr(constants, 'KEY_ACTOR'))
        self.assertTrue(hasattr(constants, 'FORMAT_PDF'))
        self.assertTrue(hasattr(constants, 'PROMPT_TYPE_NARRATIVE'))
        
        # Test that constants have expected string values
        self.assertIsInstance(constants.ACTOR_USER, str)
        self.assertIsInstance(constants.PROMPTS_DIR, str)

    def test_attribute_system_constants(self):
        """Test that attribute system constants are defined correctly."""
        self.assertEqual(constants.ATTRIBUTE_SYSTEM_DND, "D&D")
        self.assertEqual(constants.DEFAULT_ATTRIBUTE_SYSTEM, "D&D")
    
    def test_attribute_lists(self):
        """Test that attribute lists are defined correctly."""
        # D&D attributes
        self.assertEqual(len(constants.DND_ATTRIBUTES), 6)
        self.assertIn("Strength", constants.DND_ATTRIBUTES)
        self.assertIn("Charisma", constants.DND_ATTRIBUTES)
        
        # D&D codes
        self.assertEqual(len(constants.DND_ATTRIBUTE_CODES), 6)
        self.assertIn("STR", constants.DND_ATTRIBUTE_CODES)
        self.assertIn("CHA", constants.DND_ATTRIBUTE_CODES)
    
    def test_helper_functions(self):
        """Test the attribute system helper functions."""
        # Test get attributes
        dnd_attrs = constants.get_attributes_for_system("D&D")
        self.assertEqual(len(dnd_attrs), 6)
        self.assertIn("Charisma", dnd_attrs)
        
        # Test default behavior for unknown systems
        unknown_attrs = constants.get_attributes_for_system("Unknown")
        self.assertEqual(len(unknown_attrs), 6)  # Should default to D&D
        self.assertIn("Charisma", unknown_attrs)
        
        # Test characteristic checks
        self.assertTrue(constants.uses_charisma("D&D"))
        self.assertFalse(constants.uses_charisma("Unknown"))  # Unknown defaults to False
        self.assertFalse(constants.uses_big_five("D&D"))
        self.assertFalse(constants.uses_big_five("Unknown"))  # Always False now
        
        # Test attribute codes
        dnd_codes = constants.get_attribute_codes_for_system("D&D")
        self.assertEqual(len(dnd_codes), 6)
        self.assertIn("STR", dnd_codes)
        self.assertIn("CHA", dnd_codes)


    def test_character_creation_constants(self):
        """Test character creation constants."""
        self.assertIsInstance(constants.CHARACTER_DESIGN_REMINDER, str)
        self.assertIn("CRITICAL REMINDER", constants.CHARACTER_DESIGN_REMINDER)
        self.assertIn("mechanics is enabled", constants.CHARACTER_DESIGN_REMINDER)
        self.assertIn("character design", constants.CHARACTER_DESIGN_REMINDER)
    
    def test_mode_switching_constants(self):
        """Test mode switching detection constants."""
        # Test MODE_SWITCH_PHRASES
        self.assertIsInstance(constants.MODE_SWITCH_PHRASES, list)
        self.assertIn('god mode', constants.MODE_SWITCH_PHRASES)
        self.assertIn('dm mode', constants.MODE_SWITCH_PHRASES)
        
        # Test MODE_SWITCH_SIMPLE
        self.assertIsInstance(constants.MODE_SWITCH_SIMPLE, list)
        self.assertIn('god mode', constants.MODE_SWITCH_SIMPLE)
        self.assertIn('dm', constants.MODE_SWITCH_SIMPLE)
    
    def test_user_selectable_prompts(self):
        """Test user selectable prompts list."""
        self.assertIsInstance(constants.USER_SELECTABLE_PROMPTS, list)
        self.assertEqual(len(constants.USER_SELECTABLE_PROMPTS), 2)
        self.assertIn(constants.PROMPT_TYPE_NARRATIVE, constants.USER_SELECTABLE_PROMPTS)
        self.assertIn(constants.PROMPT_TYPE_MECHANICS, constants.USER_SELECTABLE_PROMPTS)


if __name__ == '__main__':
    unittest.main()