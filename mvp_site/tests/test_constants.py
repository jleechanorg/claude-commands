import os
import sys
import unittest

# Add parent directory to path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from mvp_site import constants


class TestConstants(unittest.TestCase):
    """Test constants module values and structure."""

    def test_actor_constants(self):
        """Test actor constants are properly defined."""
        assert constants.ACTOR_USER == "user"
        assert constants.ACTOR_GEMINI == "gemini"

    def test_interaction_mode_constants(self):
        """Test interaction mode constants."""
        assert constants.MODE_CHARACTER == "character"
        assert constants.MODE_GOD == "god"

    def test_dictionary_key_constants(self):
        """Test dictionary key constants."""
        assert constants.KEY_ACTOR == "actor"
        assert constants.KEY_MODE == "mode"
        assert constants.KEY_TEXT == "text"
        assert constants.KEY_TITLE == "title"
        assert constants.KEY_FORMAT == "format"
        assert constants.KEY_USER_INPUT == "user_input"
        assert constants.KEY_SELECTED_PROMPTS == "selected_prompts"
        assert constants.KEY_MBTI == "mbti"

    def test_export_format_constants(self):
        """Test export format constants."""
        assert constants.FORMAT_PDF == "pdf"
        assert constants.FORMAT_DOCX == "docx"
        assert constants.FORMAT_TXT == "txt"

        # Test MIME types
        assert constants.MIMETYPE_PDF == "application/pdf"
        assert (
            constants.MIMETYPE_DOCX
            == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        assert constants.MIMETYPE_TXT == "text/plain"

    def test_prompt_filename_constants(self):
        """Test prompt filename constants."""
        assert constants.FILENAME_NARRATIVE == "narrative_system_instruction.md"
        assert constants.FILENAME_MECHANICS == "mechanics_system_instruction.md"
        assert constants.FILENAME_GAME_STATE == "game_state_instruction.md"
        assert constants.FILENAME_CHARACTER_TEMPLATE == "character_template.md"
        assert constants.FILENAME_MASTER_DIRECTIVE == "master_directive.md"
        assert constants.FILENAME_DND_SRD == "dnd_srd_instruction.md"

    def test_prompt_type_constants(self):
        """Test prompt type constants."""
        assert constants.PROMPT_TYPE_NARRATIVE == "narrative"
        assert constants.PROMPT_TYPE_MECHANICS == "mechanics"
        assert constants.PROMPT_TYPE_GAME_STATE == "game_state"
        assert constants.PROMPT_TYPE_CHARACTER_TEMPLATE == "character_template"
        assert constants.PROMPT_TYPE_MASTER_DIRECTIVE == "master_directive"
        assert constants.PROMPT_TYPE_DND_SRD == "dnd_srd"

    def test_prompt_path_constants(self):
        """Test prompt path constants are properly constructed."""
        expected_prompts_dir = "prompts"
        assert expected_prompts_dir == constants.PROMPTS_DIR

        # Test that paths are properly joined with os.path.join
        assert (
            os.path.join(expected_prompts_dir, "narrative_system_instruction.md")
            == constants.NARRATIVE_SYSTEM_INSTRUCTION_PATH
        )
        assert (
            os.path.join(expected_prompts_dir, "mechanics_system_instruction.md")
            == constants.MECHANICS_SYSTEM_INSTRUCTION_PATH
        )
        assert (
            os.path.join(expected_prompts_dir, "character_template.md")
            == constants.CHARACTER_TEMPLATE_PATH
        )
        assert (
            os.path.join(expected_prompts_dir, "game_state_instruction.md")
            == constants.GAME_STATE_INSTRUCTION_PATH
        )
        assert (
            os.path.join(expected_prompts_dir, "master_directive.md")
            == constants.MASTER_DIRECTIVE_PATH
        )
        assert (
            os.path.join(expected_prompts_dir, "dnd_srd_instruction.md")
            == constants.DND_SRD_INSTRUCTION_PATH
        )

    def test_constants_are_strings(self):
        """Test that all constants are strings (no accidental None values)."""
        string_constants = [
            constants.ACTOR_USER,
            constants.ACTOR_GEMINI,
            constants.MODE_CHARACTER,
            constants.MODE_GOD,
            constants.KEY_ACTOR,
            constants.KEY_MODE,
            constants.KEY_TEXT,
            constants.KEY_TITLE,
            constants.KEY_FORMAT,
            constants.KEY_USER_INPUT,
            constants.KEY_SELECTED_PROMPTS,
            constants.KEY_MBTI,
            constants.FORMAT_PDF,
            constants.FORMAT_DOCX,
            constants.FORMAT_TXT,
            constants.MIMETYPE_PDF,
            constants.MIMETYPE_DOCX,
            constants.MIMETYPE_TXT,
            constants.FILENAME_NARRATIVE,
            constants.FILENAME_MECHANICS,
            constants.FILENAME_GAME_STATE,
            constants.FILENAME_CHARACTER_TEMPLATE,
            constants.FILENAME_MASTER_DIRECTIVE,
            constants.FILENAME_DND_SRD,
            constants.PROMPT_TYPE_NARRATIVE,
            constants.PROMPT_TYPE_MECHANICS,
            constants.PROMPT_TYPE_GAME_STATE,
            constants.PROMPT_TYPE_CHARACTER_TEMPLATE,
            constants.PROMPT_TYPE_MASTER_DIRECTIVE,
            constants.PROMPT_TYPE_DND_SRD,
            constants.PROMPTS_DIR,
            constants.NARRATIVE_SYSTEM_INSTRUCTION_PATH,
            constants.MECHANICS_SYSTEM_INSTRUCTION_PATH,
            constants.CHARACTER_TEMPLATE_PATH,
            constants.GAME_STATE_INSTRUCTION_PATH,
            constants.MASTER_DIRECTIVE_PATH,
            constants.DND_SRD_INSTRUCTION_PATH,
        ]

        for constant in string_constants:
            with self.subTest(constant=constant):
                assert isinstance(constant, str)
                assert constant != ""  # Ensure no empty strings

    def test_constants_immutability_pattern(self):
        """Test that constants follow immutability patterns (uppercase naming)."""
        # Test that key constants are uppercase
        assert hasattr(constants, "ACTOR_USER")
        assert hasattr(constants, "MODE_CHARACTER")
        assert hasattr(constants, "KEY_ACTOR")
        assert hasattr(constants, "FORMAT_PDF")
        assert hasattr(constants, "PROMPT_TYPE_NARRATIVE")

        # Test that constants have expected string values
        assert isinstance(constants.ACTOR_USER, str)
        assert isinstance(constants.PROMPTS_DIR, str)

    def test_attribute_system_constants(self):
        """Test that attribute system constants are defined correctly."""
        assert constants.ATTRIBUTE_SYSTEM_DND == "D&D"
        assert constants.DEFAULT_ATTRIBUTE_SYSTEM == "D&D"

    def test_attribute_lists(self):
        """Test that attribute lists are defined correctly."""
        # D&D attributes
        assert len(constants.DND_ATTRIBUTES) == 6
        assert "Strength" in constants.DND_ATTRIBUTES
        assert "Charisma" in constants.DND_ATTRIBUTES

        # D&D codes
        assert len(constants.DND_ATTRIBUTE_CODES) == 6
        assert "STR" in constants.DND_ATTRIBUTE_CODES
        assert "CHA" in constants.DND_ATTRIBUTE_CODES

    def test_helper_functions(self):
        """Test the attribute system helper functions."""
        # Test get attributes
        dnd_attrs = constants.get_attributes_for_system("D&D")
        assert len(dnd_attrs) == 6
        assert "Charisma" in dnd_attrs

        # Test default behavior for unknown systems
        unknown_attrs = constants.get_attributes_for_system("Unknown")
        assert len(unknown_attrs) == 6  # Should default to D&D
        assert "Charisma" in unknown_attrs

        # Test characteristic checks
        assert constants.uses_charisma("D&D")
        assert not constants.uses_charisma("Unknown")  # Unknown defaults to False
        assert not constants.uses_big_five("D&D")
        assert not constants.uses_big_five("Unknown")  # Always False now

        # Test attribute codes
        dnd_codes = constants.get_attribute_codes_for_system("D&D")
        assert len(dnd_codes) == 6
        assert "STR" in dnd_codes
        assert "CHA" in dnd_codes

    def test_character_creation_constants(self):
        """Test character creation constants."""
        assert isinstance(constants.CHARACTER_DESIGN_REMINDER, str)
        assert "CRITICAL REMINDER" in constants.CHARACTER_DESIGN_REMINDER
        assert "mechanics is enabled" in constants.CHARACTER_DESIGN_REMINDER
        assert "character design" in constants.CHARACTER_DESIGN_REMINDER

    def test_mode_switching_constants(self):
        """Test mode switching detection constants."""
        # Test MODE_SWITCH_PHRASES
        assert isinstance(constants.MODE_SWITCH_PHRASES, list)
        assert "god mode" in constants.MODE_SWITCH_PHRASES
        assert "dm mode" in constants.MODE_SWITCH_PHRASES

        # Test MODE_SWITCH_SIMPLE
        assert isinstance(constants.MODE_SWITCH_SIMPLE, list)
        assert "god mode" in constants.MODE_SWITCH_SIMPLE
        assert "dm" in constants.MODE_SWITCH_SIMPLE

    def test_user_selectable_prompts(self):
        """Test user selectable prompts list."""
        assert isinstance(constants.USER_SELECTABLE_PROMPTS, list)
        assert len(constants.USER_SELECTABLE_PROMPTS) == 2
        assert constants.PROMPT_TYPE_NARRATIVE in constants.USER_SELECTABLE_PROMPTS
        assert constants.PROMPT_TYPE_MECHANICS in constants.USER_SELECTABLE_PROMPTS


if __name__ == "__main__":
    unittest.main()
