#!/usr/bin/env python3
"""
Unit tests for banned names loading functionality.
Verifies that the real banned_names.md file is loaded correctly.
"""

import os
import sys
import unittest

# Add parent directory to path so we can import world_loader
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import world_loader


class TestBannedNamesLoading(unittest.TestCase):
    """Test that banned names are loaded correctly from banned_names.md."""

    def test_banned_names_file_exists(self):
        """Test that the banned_names.md file exists."""
        assert os.path.exists(
            world_loader.BANNED_NAMES_PATH
        ), f"Banned names file not found at {world_loader.BANNED_NAMES_PATH}"

    def test_load_banned_names_returns_content(self):
        """Test that load_banned_names returns non-empty content."""
        content = world_loader.load_banned_names()
        assert content is not None, "load_banned_names returned None"
        assert isinstance(content, str), "load_banned_names should return a string"
        assert len(content) > 0, "load_banned_names returned empty content"

    def test_banned_names_contains_master_directive(self):
        """Test that banned names content contains the MASTER DIRECTIVE."""
        content = world_loader.load_banned_names()
        assert (
            "MASTER DIRECTIVE" in content
        ), "Banned names content should contain MASTER DIRECTIVE"
        assert (
            "ABSOLUTELY FORBIDDEN" in content
        ), "Banned names content should emphasize absolute prohibition"

    def test_banned_names_contains_all_primary_names(self):
        """Test that all 10 primary banned names are present."""
        content = world_loader.load_banned_names()
        primary_names = [
            "Alaric",
            "Blackwood",
            "Corvus",
            "Elara",
            "Kaelen",
            "Lyra",
            "Seraphina",
            "Thorne",
            "Valerius",
            "Isolde",
        ]
        for name in primary_names:
            assert name in content, f"Primary banned name '{name}' not found in content"

    def test_banned_names_contains_extended_names(self):
        """Test that extended banned names are present in the simplified list."""
        content = world_loader.load_banned_names()

        # Test a sample of extended names (they're now in the single list)
        sample_extended = ["Aiden", "Phoenix", "Raven", "Luna", "Orion", "Zephyr"]
        for name in sample_extended:
            assert (
                name in content
            ), f"Extended banned name '{name}' not found in content"

    def test_banned_names_count_verification(self):
        """Test that the content mentions 56 total banned names."""
        content = world_loader.load_banned_names()
        assert "56" in content, "Content should mention total count of 56 banned names"
        assert "10 Primary" in content, "Content should mention 10 primary names"
        assert "46 Extended" in content, "Content should mention 46 extended names"

    def test_banned_names_enforcement_directive(self):
        """Test that enforcement directive is present."""
        content = world_loader.load_banned_names()
        assert (
            "Enforcement Directive" in content
        ), "Content should contain Enforcement Directive section"
        assert (
            "NO EXCEPTIONS" in content
        ), "Content should emphasize no exceptions policy"

    def test_world_content_includes_banned_names(self):
        """Test that the full world content includes banned names section."""
        try:
            full_content = world_loader.load_world_content_for_system_instruction()
            assert (
                "BANNED" in full_content.upper()
            ), "World content should include banned names section"
            assert (
                "MASTER DIRECTIVE" in full_content
            ), "World content should include the master directive"
            # Check that at least some banned names are present
            assert (
                "Lyra" in full_content
            ), "Banned name 'Lyra' should be in world content"
            assert (
                "Kaelen" in full_content
            ), "Banned name 'Kaelen' should be in world content"
        except FileNotFoundError as e:
            self.skipTest(
                f"Skipping world content test - required files not found: {e}"
            )


if __name__ == "__main__":
    unittest.main()
