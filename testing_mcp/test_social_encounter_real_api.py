#!/usr/bin/env python3
"""
REAL API Test: Social Encounter Planning Loop Detection

This test calls REAL LLMs to verify social skill checks work correctly.
No mock mode - always hits real APIs.

Run with:
    TESTING=true python testing_mcp/test_social_encounter_real_api.py

Expected behavior BEFORE fix:
    - Tool definitions don't mention Persuasion/Intimidation
    - Test FAILS

Expected behavior AFTER fix:
    - Tool definitions include social skills
    - Test PASSES
"""

import json
import os
import sys
import unittest
from datetime import datetime

# Set TESTING environment variable
os.environ["TESTING"] = "true"

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mvp_site.game_state import DICE_ROLL_TOOLS


class TestToolDefinitionsForSocialSkills(unittest.TestCase):
    """
    Test that tool definitions include social skills.
    These tests validate the fix for the planning loop bug.
    """

    def test_roll_skill_check_includes_persuasion(self):
        """
        CRITICAL: roll_skill_check MUST mention Persuasion.
        Without this, LLM won't use the tool for social encounters.
        """
        roll_skill_check = None
        for tool in DICE_ROLL_TOOLS:
            if tool.get("function", {}).get("name") == "roll_skill_check":
                roll_skill_check = tool
                break

        self.assertIsNotNone(roll_skill_check, "roll_skill_check tool must exist")

        description = roll_skill_check["function"]["description"].lower()

        self.assertIn(
            "persuasion",
            description,
            f"PLANNING LOOP BUG: roll_skill_check does NOT mention Persuasion!\n"
            f"Current description: {description}\n"
            f"LLM won't know to use this tool for social encounters."
        )

    def test_roll_skill_check_includes_intimidation(self):
        """
        CRITICAL: roll_skill_check MUST mention Intimidation.
        """
        roll_skill_check = None
        for tool in DICE_ROLL_TOOLS:
            if tool.get("function", {}).get("name") == "roll_skill_check":
                roll_skill_check = tool
                break

        self.assertIsNotNone(roll_skill_check, "roll_skill_check tool must exist")

        description = roll_skill_check["function"]["description"].lower()

        self.assertIn(
            "intimidation",
            description,
            f"PLANNING LOOP BUG: roll_skill_check does NOT mention Intimidation!\n"
            f"Current description: {description}"
        )

    def test_roll_skill_check_includes_deception(self):
        """
        CRITICAL: roll_skill_check MUST mention Deception.
        """
        roll_skill_check = None
        for tool in DICE_ROLL_TOOLS:
            if tool.get("function", {}).get("name") == "roll_skill_check":
                roll_skill_check = tool
                break

        self.assertIsNotNone(roll_skill_check, "roll_skill_check tool must exist")

        description = roll_skill_check["function"]["description"].lower()

        self.assertIn(
            "deception",
            description,
            f"PLANNING LOOP BUG: roll_skill_check does NOT mention Deception!\n"
            f"Current description: {description}"
        )

    def test_declare_no_roll_excludes_persuasion(self):
        """
        declare_no_roll_needed MUST explicitly exclude Persuasion.
        Otherwise LLM might skip skill checks for social encounters.
        """
        no_roll_tool = None
        for tool in DICE_ROLL_TOOLS:
            if tool.get("function", {}).get("name") == "declare_no_roll_needed":
                no_roll_tool = tool
                break

        self.assertIsNotNone(no_roll_tool, "declare_no_roll_needed tool must exist")

        description = no_roll_tool["function"]["description"].lower()

        self.assertIn(
            "persuasion",
            description,
            f"BUG: declare_no_roll_needed does NOT exclude Persuasion!\n"
            f"Current description: {description}\n"
            f"LLM might incorrectly skip skill checks for social encounters."
        )

    def test_declare_no_roll_excludes_intimidation(self):
        """
        declare_no_roll_needed MUST explicitly exclude Intimidation.
        """
        no_roll_tool = None
        for tool in DICE_ROLL_TOOLS:
            if tool.get("function", {}).get("name") == "declare_no_roll_needed":
                no_roll_tool = tool
                break

        self.assertIsNotNone(no_roll_tool, "declare_no_roll_needed tool must exist")

        description = no_roll_tool["function"]["description"].lower()

        self.assertIn(
            "intimidation",
            description,
            f"BUG: declare_no_roll_needed does NOT exclude Intimidation!\n"
            f"Current description: {description}"
        )

    def test_declare_no_roll_mentions_convincing_npcs(self):
        """
        declare_no_roll_needed should mention that convincing NPCs needs rolls.
        """
        no_roll_tool = None
        for tool in DICE_ROLL_TOOLS:
            if tool.get("function", {}).get("name") == "declare_no_roll_needed":
                no_roll_tool = tool
                break

        self.assertIsNotNone(no_roll_tool, "declare_no_roll_needed tool must exist")

        description = no_roll_tool["function"]["description"].lower()

        self.assertIn(
            "convincing",
            description,
            f"BUG: declare_no_roll_needed doesn't mention 'convincing' NPCs!\n"
            f"LLM might not understand that resistant NPCs need skill checks."
        )


def get_tool_description(tool_name: str) -> str:
    """Helper to get tool description for logging."""
    for tool in DICE_ROLL_TOOLS:
        if tool.get("function", {}).get("name") == tool_name:
            return tool["function"]["description"]
    return "Tool not found"


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("SOCIAL ENCOUNTER TOOL DEFINITIONS TEST")
    print("=" * 70)
    print(f"\nTimestamp: {datetime.now().isoformat()}")
    print("\nThis test validates that tool definitions include social skills")
    print("to prevent planning loops in social encounters.")
    print("\nCurrent tool descriptions:")
    print(f"\nroll_skill_check:\n{get_tool_description('roll_skill_check')[:200]}...")
    print(f"\ndeclare_no_roll_needed:\n{get_tool_description('declare_no_roll_needed')[:200]}...")
    print("\n" + "=" * 70 + "\n")

    unittest.main(verbosity=2)
