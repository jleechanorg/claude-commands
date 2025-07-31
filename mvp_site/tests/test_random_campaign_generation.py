#!/usr/bin/env python3
"""
Unit tests for random campaign generation bug fix.

Tests that _build_campaign_prompt properly utilizes RANDOM_CHARACTERS and
RANDOM_SETTINGS arrays when inputs are empty, instead of using generic fallback.
"""

import os
import sys
import unittest
from unittest.mock import patch

# Set TESTING environment variable
os.environ["TESTING"] = "true"
os.environ["GEMINI_API_KEY"] = "test-api-key"

# Add the parent directory to the path to import world_logic
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from world_logic import RANDOM_CHARACTERS, RANDOM_SETTINGS, _build_campaign_prompt


class TestRandomCampaignGeneration(unittest.TestCase):
    """Test random campaign generation functionality."""

    def test_build_campaign_prompt_with_all_inputs(self):
        """Test normal campaign prompt building with all inputs provided."""
        character = "A brave warrior"
        setting = "The bustling city"
        description = "An epic adventure"
        old_prompt = ""

        result = _build_campaign_prompt(character, setting, description, old_prompt)

        expected = "Character: A brave warrior | Setting: The bustling city | Description: An epic adventure"
        assert result == expected

    def test_build_campaign_prompt_uses_old_prompt(self):
        """Test that old_prompt is used when provided."""
        old_prompt = "This is an old prompt format"

        result = _build_campaign_prompt("", "", "", old_prompt)

        assert result == "This is an old prompt format"

    def test_build_campaign_prompt_partial_inputs(self):
        """Test campaign prompt building with partial inputs."""
        character = "A cunning rogue"
        setting = ""
        description = "A mysterious quest"
        old_prompt = ""

        result = _build_campaign_prompt(character, setting, description, old_prompt)

        expected = "Character: A cunning rogue | Description: A mysterious quest"
        assert result == expected

    def test_build_campaign_prompt_random_generation(self):
        """Test that empty inputs trigger random campaign generation using predefined arrays."""
        # Test with completely empty inputs
        result = _build_campaign_prompt("", "", "", "")

        # Verify result contains Character and Setting
        assert "Character:" in result
        assert "Setting:" in result
        assert "|" in result  # Should be joined with separator

        # Verify the result contains content from our predefined arrays
        parts = result.split(" | ")
        assert len(parts) == 2

        character_part = parts[0]
        setting_part = parts[1]

        # Extract the actual character and setting content
        character_content = character_part.replace("Character: ", "")
        setting_content = setting_part.replace("Setting: ", "")

        # Verify they come from our predefined arrays
        assert character_content in RANDOM_CHARACTERS
        assert setting_content in RANDOM_SETTINGS

    def test_build_campaign_prompt_random_generation_deterministic(self):
        """Test random generation with mocked random choice for deterministic testing."""
        with patch("random.choice") as mock_choice:
            # Mock random.choice to return specific values
            mock_choice.side_effect = [
                RANDOM_CHARACTERS[0],  # First call returns first character
                RANDOM_SETTINGS[0],  # Second call returns first setting
            ]

            result = _build_campaign_prompt("", "", "", "")

            expected = (
                f"Character: {RANDOM_CHARACTERS[0]} | Setting: {RANDOM_SETTINGS[0]}"
            )
            assert result == expected

            # Verify random.choice was called twice with correct arrays
            assert mock_choice.call_count == 2
            mock_choice.assert_any_call(RANDOM_CHARACTERS)
            mock_choice.assert_any_call(RANDOM_SETTINGS)

    def test_build_campaign_prompt_random_arrays_not_empty(self):
        """Test that our random arrays are properly defined and not empty."""
        assert len(RANDOM_CHARACTERS) > 0, "RANDOM_CHARACTERS should not be empty"
        assert len(RANDOM_SETTINGS) > 0, "RANDOM_SETTINGS should not be empty"

        # Verify they contain meaningful content (not just empty strings)
        for character in RANDOM_CHARACTERS:
            assert isinstance(character, str)
            assert len(character.strip()) > 0

        for setting in RANDOM_SETTINGS:
            assert isinstance(setting, str)
            assert len(setting.strip()) > 0

    def test_build_campaign_prompt_random_generation_variability(self):
        """Test that random generation produces different results on multiple calls."""
        results = set()

        # Generate multiple random campaigns
        for _ in range(10):
            result = _build_campaign_prompt("", "", "", "")
            results.add(result)

        # With 10 characters and 10 settings, we should get some variety
        # (This is probabilistic but very likely to pass)
        assert len(results) > 1, "Random generation should produce varied results"

    def test_build_campaign_prompt_whitespace_handling(self):
        """Test that whitespace-only inputs are treated as empty and trigger random generation."""
        result = _build_campaign_prompt("   ", "\t", "\n", "  ")

        # Should trigger random generation, not include whitespace
        assert "Character:" in result
        assert "Setting:" in result
        assert "   " not in result
        assert "\t" not in result
        assert "\n" not in result


if __name__ == "__main__":
    print("🎲 Random Campaign Generation Test")
    print(
        "Testing that _build_campaign_prompt uses RANDOM_CHARACTERS and RANDOM_SETTINGS arrays"
    )
    print("=" * 80)
    unittest.main(verbosity=2)
