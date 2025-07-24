#!/usr/bin/env python3
"""
Test to verify that AI character generation instructions prevent banned names.
This test checks behavior and structure, not exact content strings.
"""

import os
import sys
import unittest

import re

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestBannedNamePreventionBehavior(unittest.TestCase):
    """Test that instructions prevent AI from suggesting banned names."""

    def setUp(self):
        """Set up test paths."""
        self.prompts_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "prompts"
        )
        self.master_directive_path = os.path.join(
            self.prompts_dir, "master_directive.md"
        )
        self.mechanics_path = os.path.join(
            self.prompts_dir, "mechanics_system_instruction.md"
        )

    def _contains_pre_generation_directive(self, content):
        """Check if content contains pre-generation check directive."""
        # Look for key concepts, not exact wording
        has_mandatory = "mandatory" in content.lower()
        has_pre_gen = (
            "pre-generation" in content.lower() or "before generat" in content.lower()
        )
        has_check = "check" in content.lower()
        return has_mandatory and has_pre_gen and has_check

    def _contains_banned_name_examples(self, content):
        """Check if content includes example banned names."""
        # These are the commonly overused names we're trying to avoid
        example_names = ["Alaric", "Corvus", "Lysander", "Seraphina"]
        return any(name in content for name in example_names)

    def _contains_scope_directive(self, content):
        """Check if directive applies to all characters."""
        has_all = "all character" in content.lower()
        has_npc = "npc" in content.lower()
        has_campaign = "campaign" in content.lower()
        return has_all or (has_npc and has_campaign)

    def test_master_directive_has_prevention_behavior(self):
        """Test that master directive includes prevention behavior."""
        with open(self.master_directive_path, encoding="utf-8") as f:
            content = f.read()

        # Test behavior, not exact strings
        self.assertTrue(
            self._contains_pre_generation_directive(content),
            "Master directive should contain pre-generation check behavior",
        )
        self.assertTrue(
            self._contains_banned_name_examples(content),
            "Should include examples of names to avoid",
        )
        self.assertTrue(
            self._contains_scope_directive(content),
            "Should apply to all characters in campaign",
        )

    def test_mechanics_instruction_has_prevention_behavior(self):
        """Test that mechanics instruction includes prevention for Option 2."""
        with open(self.mechanics_path, encoding="utf-8") as f:
            content = f.read()

        # Look for Option 2 section
        has_option_2 = "option 2" in content.lower()
        self.assertTrue(has_option_2, "Should have Option 2 character generation")

        # Check for prevention behavior in character generation
        has_critical = "critical" in content.lower()
        has_before = "before" in content.lower()
        has_name_gen = "character name" in content.lower()

        self.assertTrue(
            has_critical and has_before and has_name_gen,
            "Should have critical directive for name generation",
        )

    def test_version_indicates_changes(self):
        """Test that version number reflects banned name changes."""
        with open(self.master_directive_path, encoding="utf-8") as f:
            content = f.read()

        # Check that version is at least 1.5 (when banned name prevention was added)


        version_match = re.search(r"Version:\s*(\d+)\.(\d+)", content)
        self.assertIsNotNone(version_match, "Should have version number")

        major = int(version_match.group(1))
        minor = int(version_match.group(2))
        version = major + minor * 0.1

        self.assertGreaterEqual(
            version, 1.5, "Version should be at least 1.5 (when prevention was added)"
        )

    def test_critical_reminders_include_naming(self):
        """Test that critical reminders section addresses naming."""
        with open(self.master_directive_path, encoding="utf-8") as f:
            content = f.read()

        # Find critical reminders section
        reminders_start = content.lower().find("critical reminders")
        self.assertNotEqual(
            reminders_start, -1, "Should have critical reminders section"
        )

        reminders_content = content[reminders_start:].lower()

        # Check for naming-related reminder
        has_naming_reminder = "nam" in reminders_content and (
            "restriction" in reminders_content or "check" in reminders_content
        )
        self.assertTrue(
            has_naming_reminder, "Critical reminders should include naming checks"
        )


if __name__ == "__main__":
    unittest.main()
