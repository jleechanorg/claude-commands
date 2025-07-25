#!/usr/bin/env python3
"""
Test to verify that the AI can identify where banned names come from.
This test checks structure and behavior, not exact content strings.
"""

import os
import sys
import unittest

# Add parent directory to path
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import world_loader


class TestBannedNamesVisibilityBehavior(unittest.TestCase):
    """Test that banned names are properly identified in world content."""

    def _has_naming_restrictions_section(self, content):
        """Check if content has a clearly marked naming restrictions section."""
        # Look for section markers and naming-related keywords
        has_section_marker = "##" in content or "**" in content
        has_naming = "naming" in content.lower()
        has_restrictions = (
            "restriction" in content.lower()
            or "forbidden" in content.lower()
            or "banned" in content.lower()
        )
        return has_section_marker and has_naming and has_restrictions

    def _has_source_identification(self, content):
        """Check if content identifies where the names come from."""
        # Should indicate this comes from a specific source/file
        has_from = "from " in content.lower()
        has_md_file = ".md" in content
        return has_from and has_md_file

    def _has_enforcement_directive(self, content):
        """Check if content includes enforcement instructions."""
        has_must = "must" in content.lower()
        has_never = "never" in content.lower()
        has_enforcement = (
            "enforcement" in content.lower() or "directive" in content.lower()
        )
        return (has_must or has_never) and has_enforcement

    def test_world_content_includes_naming_restrictions(self):
        """Test that world content includes identifiable naming restrictions."""
        try:
            content = world_loader.load_world_content_for_system_instruction()

            self.assertTrue(
                self._has_naming_restrictions_section(content),
                "World content should have identifiable naming restrictions section",
            )

            self.assertTrue(
                self._has_source_identification(content),
                "Should identify the source of naming restrictions",
            )

        except FileNotFoundError:
            self.skipTest("World files not found - skipping visibility test")

    def test_banned_names_loader_returns_content(self):
        """Test that the banned names loader returns non-empty content."""
        content = world_loader.load_banned_names()

        # Basic structural checks
        self.assertIsInstance(content, str, "Should return string content")
        self.assertGreater(len(content), 100, "Should have substantial content")

        # Check for directive structure
        self.assertTrue(
            self._has_enforcement_directive(content),
            "Banned names should include enforcement directive",
        )

    def test_world_content_structure_includes_all_sections(self):
        """Test that world content has proper structure with all expected sections."""
        try:
            content = world_loader.load_world_content_for_system_instruction()

            # Check for major section markers
            has_world_content_header = "world content" in content.lower()
            has_section_dividers = "---" in content or "##" in content

            self.assertTrue(
                has_world_content_header, "Should have world content header"
            )
            self.assertTrue(
                has_section_dividers, "Should have section dividers for organization"
            )

            # Verify it's a substantial document
            self.assertGreater(
                len(content), 1000, "Combined world content should be substantial"
            )

        except FileNotFoundError:
            self.skipTest("World files not found - skipping structure test")


if __name__ == "__main__":
    unittest.main()
