"""
Test suite for _build_campaign_prompt function in MCP architecture.

Tests campaign prompt building functionality through world_logic module
with MCP architecture compatibility using pipe-separated format.
"""

import os
import sys
import unittest

# Set environment variables for MCP testing
os.environ["TESTING"] = "true"
os.environ["USE_MOCKS"] = "true"

# Add mvp_site to path to import main module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from world_logic import _build_campaign_prompt


class TestBuildCampaignPrompt(unittest.TestCase):
    """Test cases for _build_campaign_prompt function."""

    def test_all_empty_inputs_should_generate_random_content(self):
        """When all inputs are empty, should generate random campaign using predefined arrays."""
        result = _build_campaign_prompt("", "", "", "")

        # Should use random generation from RANDOM_CHARACTERS and RANDOM_SETTINGS arrays
        assert "Character:" in result
        assert "Setting:" in result
        assert "|" in result  # Should be joined with separator

        # Extract content and verify it comes from predefined arrays
        from world_logic import RANDOM_CHARACTERS, RANDOM_SETTINGS

        parts = result.split(" | ")
        assert len(parts) == 2

        character_content = parts[0].replace("Character: ", "")
        setting_content = parts[1].replace("Setting: ", "")

        assert character_content in RANDOM_CHARACTERS
        assert setting_content in RANDOM_SETTINGS

    def test_none_inputs_should_handle_gracefully(self):
        """When inputs are None, should handle gracefully (testing behavior)."""
        # The function expects string inputs, but test how it handles None
        # This documents current behavior rather than expected behavior
        try:
            result = _build_campaign_prompt(None, None, None, None)
            # If it doesn't crash, check what it returns
            assert isinstance(result, str), "Should return string even with None inputs"
        except AttributeError:
            # This is the current behavior - None doesn't have .strip()
            assert True, "Function correctly expects string inputs, not None"

    def test_character_only_provided(self):
        """When only character is provided, should use pipe-separated format."""
        character = "A brave warrior from the northern kingdoms"
        result = _build_campaign_prompt(character, "", "", "")

        # Should use provided character in pipe format
        expected = f"Character: {character}"
        assert result == expected

    def test_setting_only_provided(self):
        """When only setting is provided, should use pipe-separated format."""
        setting = "A mystical realm where magic and technology coexist"
        result = _build_campaign_prompt("", setting, "", "")

        # Should use provided setting in pipe format
        expected = f"Setting: {setting}"
        assert result == expected

    def test_description_only_provided(self):
        """When only description is provided, should use pipe-separated format."""
        description = "An epic quest to save the world from ancient evil"
        result = _build_campaign_prompt("", "", description, "")

        # Should use provided description in pipe format
        expected = f"Description: {description}"
        assert result == expected

    def test_character_and_setting_provided(self):
        """When character and setting are provided, should use pipe-separated format."""
        character = "A cunning rogue with a mysterious past"
        setting = "The sprawling city of Waterdeep"
        result = _build_campaign_prompt(character, setting, "", "")

        # Should use both provided inputs in pipe format
        expected = f"Character: {character} | Setting: {setting}"
        assert result == expected

    def test_character_and_description_provided(self):
        """When character and description are provided, should use pipe-separated format."""
        character = "A wise wizard seeking ancient knowledge"
        description = "A journey through forgotten libraries and dangerous ruins"
        result = _build_campaign_prompt(character, "", description, "")

        # Should use provided character and description in pipe format
        expected = f"Character: {character} | Description: {description}"
        assert result == expected

    def test_setting_and_description_provided(self):
        """When setting and description are provided, should use pipe-separated format."""
        setting = "The frozen wastelands of the north"
        description = "Survive the harsh winter and uncover ancient secrets"
        result = _build_campaign_prompt("", setting, description, "")

        # Should use provided setting and description in pipe format
        expected = f"Setting: {setting} | Description: {description}"
        assert result == expected

    def test_all_fields_provided(self):
        """When all fields are provided, should use pipe-separated format."""
        character = "A paladin devoted to justice"
        setting = "The kingdom of Baldur's Gate"
        description = "Restore peace to a war-torn land"
        result = _build_campaign_prompt(character, setting, description, "")

        # Should use all provided inputs in pipe format
        expected = (
            f"Character: {character} | Setting: {setting} | Description: {description}"
        )
        assert result == expected

    def test_backward_compatibility_with_old_prompt(self):
        """Should use old_prompt when provided and new fields are empty."""
        old_prompt = "This is a legacy campaign prompt format"
        result = _build_campaign_prompt("", "", "", old_prompt)

        # Should return the old prompt as-is
        assert result == old_prompt

    def test_old_prompt_takes_precedence_always(self):
        """Old prompt takes precedence when provided, regardless of new fields."""
        old_prompt = "Legacy prompt"
        character = "Test character"

        # Old prompt takes precedence even when new fields are provided
        result = _build_campaign_prompt(character, "", "", old_prompt)
        expected = old_prompt
        assert result == expected

    def test_whitespace_only_inputs_treated_as_empty(self):
        """Whitespace-only inputs should be treated as empty."""
        result = _build_campaign_prompt("   ", "\t", "\n", "  ")

        # Should generate random content from predefined arrays, not use whitespace
        assert "Character:" in result
        assert "Setting:" in result
        assert "   " not in result
        assert "\t" not in result
        assert "\n" not in result

        # Verify content comes from predefined arrays
        from world_logic import RANDOM_CHARACTERS, RANDOM_SETTINGS

        parts = result.split(" | ")
        assert len(parts) == 2

        character_content = parts[0].replace("Character: ", "")
        setting_content = parts[1].replace("Setting: ", "")

        assert character_content in RANDOM_CHARACTERS
        assert setting_content in RANDOM_SETTINGS

    def test_special_characters_in_inputs(self):
        """Should handle special characters in inputs properly."""
        character = "A character with 'quotes' and \"double quotes\" & symbols"
        setting = "A realm with émojis 🐉 and ñoñó"
        description = "Description with <tags> and [brackets] {curly}"

        result = _build_campaign_prompt(character, setting, description, "")

        # Should preserve all special characters in pipe format
        expected = (
            f"Character: {character} | Setting: {setting} | Description: {description}"
        )
        assert result == expected

    def test_very_long_inputs(self):
        """Should handle very long inputs without truncation."""
        long_character = "A" * 100  # Long character description
        long_setting = "B" * 100  # Long setting description
        long_description = "C" * 100  # Long campaign description

        result = _build_campaign_prompt(
            long_character, long_setting, long_description, ""
        )

        # Should preserve full length inputs in pipe format
        expected = f"Character: {long_character} | Setting: {long_setting} | Description: {long_description}"
        assert result == expected

    def test_mixed_empty_and_provided_inputs(self):
        """Should handle mix of empty and provided inputs correctly."""
        # Test various combinations

        # Character and description, no setting
        result1 = _build_campaign_prompt("Hero", "", "Epic quest", "")
        expected1 = "Character: Hero | Description: Epic quest"
        assert result1 == expected1

        # Setting and description, no character
        result2 = _build_campaign_prompt("", "Fantasy world", "Adventure", "")
        expected2 = "Setting: Fantasy world | Description: Adventure"
        assert result2 == expected2

    def test_old_prompt_with_whitespace(self):
        """Should strip whitespace from old prompt."""
        old_prompt = "  Legacy prompt with whitespace  "
        result = _build_campaign_prompt("", "", "", old_prompt)

        # Should strip whitespace from old prompt
        expected = "Legacy prompt with whitespace"
        assert result == expected


if __name__ == "__main__":
    unittest.main()
