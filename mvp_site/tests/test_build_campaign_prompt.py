"""
Test suite for _build_campaign_prompt function using Test-Driven Development.

This module tests all combinations of character, setting, and description inputs,
including edge cases and backward compatibility.

The function should:
1. Generate random content when inputs are empty/None
2. Use provided inputs when available
3. Support backward compatibility with old_prompt
4. Validate inputs and raise errors appropriately
"""

import os
import sys
import unittest

# Add mvp_site to path to import main module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import _build_campaign_prompt


class TestBuildCampaignPrompt(unittest.TestCase):
    """Test cases for _build_campaign_prompt function."""

    def test_all_empty_inputs_should_generate_random_content(self):
        """When all inputs are empty, should generate random character and setting."""
        result = _build_campaign_prompt("", "", "", "")

        # Should not contain literal "random character" string
        self.assertNotIn("random character", result.lower())
        self.assertNotIn("Character: random character", result)

        # Should contain actual character and setting content
        self.assertIn("Character:", result)
        self.assertIn("Setting:", result)

        # Should have meaningful content, not just placeholder text
        lines = result.split("\n")
        character_line = [line for line in lines if line.startswith("Character:")][0]
        setting_line = [line for line in lines if line.startswith("Setting:")][0]

        # Character should be more than just "Character: random character"
        self.assertGreater(len(character_line), 25)  # More than placeholder
        self.assertGreater(len(setting_line), 30)  # More than placeholder

    def test_none_inputs_should_generate_random_content(self):
        """When all inputs are None, should generate random character and setting."""
        result = _build_campaign_prompt(None, None, None, None)

        # Should contain actual character and setting content
        self.assertIn("Character:", result)
        self.assertIn("Setting:", result)

        # Should not contain literal "random character" string
        self.assertNotIn("random character", result.lower())

    def test_character_only_provided(self):
        """When only character is provided, should use it and generate random setting."""
        character = "A brave warrior from the northern kingdoms"
        result = _build_campaign_prompt(character, "", "", "")

        # Should use provided character
        self.assertIn(f"Character: {character}", result)

        # Should generate random setting, not literal text
        self.assertIn("Setting:", result)
        self.assertNotIn("Setting: random fantasy", result)

        # Should NOT contain description line
        self.assertNotIn("Campaign Description:", result)

    def test_setting_only_provided(self):
        """When only setting is provided, should generate random character and use setting."""
        setting = "A mystical realm where magic and technology coexist"
        result = _build_campaign_prompt("", setting, "", "")

        # Should generate random character, not literal text
        self.assertIn("Character:", result)
        self.assertNotIn("Character: random character", result)

        # Should use provided setting
        self.assertIn(f"Setting: {setting}", result)

        # Should NOT contain description line
        self.assertNotIn("Campaign Description:", result)

    def test_description_only_provided(self):
        """When only description is provided, should generate random character and setting."""
        description = "An epic quest to save the world from ancient evil"
        result = _build_campaign_prompt("", "", description, "")

        # Should generate random character and setting
        self.assertIn("Character:", result)
        self.assertIn("Setting:", result)
        self.assertNotIn("Character: random character", result)
        self.assertNotIn("Setting: random fantasy", result)

        # Should include description
        self.assertIn(f"Campaign Description: {description}", result)

    def test_character_and_setting_provided(self):
        """When character and setting are provided, should use both."""
        character = "A cunning rogue with a mysterious past"
        setting = "The sprawling city of Waterdeep"
        result = _build_campaign_prompt(character, setting, "", "")

        # Should use both provided inputs
        self.assertIn(f"Character: {character}", result)
        self.assertIn(f"Setting: {setting}", result)

        # Should NOT contain description line
        self.assertNotIn("Campaign Description:", result)

    def test_character_and_description_provided(self):
        """When character and description are provided, should use both and generate setting."""
        character = "A wise wizard seeking ancient knowledge"
        description = "A journey through forgotten libraries and dangerous ruins"
        result = _build_campaign_prompt(character, "", description, "")

        # Should use provided character and description
        self.assertIn(f"Character: {character}", result)
        self.assertIn(f"Campaign Description: {description}", result)

        # Should generate random setting
        self.assertIn("Setting:", result)
        self.assertNotIn("Setting: random fantasy", result)

    def test_setting_and_description_provided(self):
        """When setting and description are provided, should use both and generate character."""
        setting = "The frozen wastelands of the north"
        description = "Survive the harsh winter and uncover ancient secrets"
        result = _build_campaign_prompt("", setting, description, "")

        # Should use provided setting and description
        self.assertIn(f"Setting: {setting}", result)
        self.assertIn(f"Campaign Description: {description}", result)

        # Should generate random character
        self.assertIn("Character:", result)
        self.assertNotIn("Character: random character", result)

    def test_all_fields_provided(self):
        """When all fields are provided, should use all of them."""
        character = "A paladin devoted to justice"
        setting = "The kingdom of Baldur's Gate"
        description = "Restore peace to a war-torn land"
        result = _build_campaign_prompt(character, setting, description, "")

        # Should use all provided inputs
        self.assertIn(f"Character: {character}", result)
        self.assertIn(f"Setting: {setting}", result)
        self.assertIn(f"Campaign Description: {description}", result)

        # Should have proper format
        lines = result.split("\n")
        self.assertEqual(len(lines), 3)

    def test_dragon_knight_campaign_type(self):
        """Dragon Knight campaign type is now ignored - handled by frontend pre-filling description."""
        # Test that campaign_type='dragon-knight' no longer triggers special behavior
        result1 = _build_campaign_prompt("", "", "", "")
        result2 = _build_campaign_prompt(
            "Some character", "Some setting", "Some desc", ""
        )

        # Should NOT return identical results (different inputs, different outputs)
        self.assertNotEqual(result1, result2)

        # Should use normal format with provided inputs
        self.assertIn("Character:", result2)
        self.assertIn("Some character", result2)
        self.assertIn("Setting:", result2)
        self.assertIn("Some setting", result2)
        self.assertIn("Campaign Description:", result2)
        self.assertIn("Some desc", result2)

    def test_backward_compatibility_with_old_prompt(self):
        """Should use old_prompt when provided and new fields are empty."""
        old_prompt = "This is a legacy campaign prompt format"
        result = _build_campaign_prompt("", "", "", old_prompt)

        self.assertEqual(result, old_prompt)

    def test_new_format_takes_precedence_over_old_prompt(self):
        """When new fields are provided, should ignore old_prompt."""
        character = "A test character"
        old_prompt = "This should be ignored"
        result = _build_campaign_prompt(character, "", "", old_prompt)

        # Should use new format
        self.assertIn(f"Character: {character}", result)

        # Should NOT use old prompt
        self.assertNotIn(old_prompt, result)

    def test_no_inputs_provided_generates_random_content(self):
        """When no inputs provided, should generate random character and setting."""
        result = _build_campaign_prompt("", "", "", "")

        # Should generate random content
        self.assertIn("Character:", result)
        self.assertIn("Setting:", result)

        # Should not contain literal placeholders
        self.assertNotIn("random character", result.lower())
        self.assertNotIn("random fantasy", result.lower())

    def test_all_none_inputs_generates_random_content(self):
        """When all inputs are None, should generate random character and setting."""
        result = _build_campaign_prompt(None, None, None, None)

        # Should generate random content
        self.assertIn("Character:", result)
        self.assertIn("Setting:", result)

        # Should not contain literal placeholders
        self.assertNotIn("random character", result.lower())
        self.assertNotIn("random fantasy", result.lower())

    def test_whitespace_only_inputs_treated_as_empty(self):
        """Whitespace-only inputs should be treated as empty."""
        result = _build_campaign_prompt("   ", "\t", "\n", "  ")

        # Should generate random content, not use whitespace
        self.assertIn("Character:", result)
        self.assertIn("Setting:", result)
        self.assertNotIn("Character:    ", result)  # No trailing whitespace

    def test_random_character_generation_varies(self):
        """Random character generation should produce different results."""
        # Generate multiple random prompts - test with more iterations for better chance of variation
        results = []
        for _ in range(
            20
        ):  # Increase iterations to improve chance of getting different results
            result = _build_campaign_prompt("", "", "", "")
            results.append(result)

        # Should not all be identical (random generation should vary)
        unique_results = set(results)
        self.assertGreater(
            len(unique_results), 1, "Random generation should produce varied results"
        )

    def test_random_setting_generation_varies(self):
        """Random setting generation should produce different results."""
        character = "Fixed character for testing"
        results = []
        for _ in range(
            20
        ):  # Increase iterations to improve chance of getting different results
            result = _build_campaign_prompt(character, "", "", "")
            results.append(result)

        # Should not all be identical (random generation should vary)
        unique_results = set(results)
        self.assertGreater(
            len(unique_results),
            1,
            "Random setting generation should produce varied results",
        )

    def test_special_characters_in_inputs(self):
        """Should handle special characters in inputs properly."""
        character = "A character with 'quotes' and \"double quotes\" & symbols"
        setting = "A realm with émojis 🐉 and ñoñó"
        description = "Description with <tags> and [brackets] {curly}"

        result = _build_campaign_prompt(character, setting, description, "")

        # Should preserve all special characters
        self.assertIn(character, result)
        self.assertIn(setting, result)
        self.assertIn(description, result)

    def test_very_long_inputs(self):
        """Should handle very long inputs without truncation."""
        long_character = "A" * 1000  # Very long character description
        long_setting = "B" * 1000  # Very long setting description
        long_description = "C" * 1000  # Very long campaign description

        result = _build_campaign_prompt(
            long_character, long_setting, long_description, ""
        )

        # Should preserve full length inputs
        self.assertIn(long_character, result)
        self.assertIn(long_setting, result)
        self.assertIn(long_description, result)

    def test_campaign_type_removed(self):
        """Campaign type parameter has been removed - frontend handles Dragon Knight pre-filling."""
        # Test that we can build prompts without campaign_type parameter
        result = _build_campaign_prompt("Hero", "Fantasy", "Epic quest", "")

        # Should use the provided inputs in standard format
        self.assertIn("Character: Hero", result)
        self.assertIn("Setting: Fantasy", result)
        self.assertIn("Campaign Description: Epic quest", result)


if __name__ == "__main__":
    unittest.main()
