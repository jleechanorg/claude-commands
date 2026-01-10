"""
End-to-end test verifying planning_protocol.md is loaded into system prompts.

This test ensures that:
1. planning_protocol.md is actually loaded into system instructions (not just declared)
2. Schema placeholders ({{PLANNING_BLOCK_SCHEMA}}, etc.) are replaced with real schemas
3. Both StoryModeAgent and PlanningAgent include the planning protocol

The planning_protocol.md file is the single source of truth for planning block structure.
If it's not loaded, the LLM never sees the canonical schema definitions.
"""

from __future__ import annotations

import os
import unittest

# Ensure TESTING_AUTH_BYPASS is set before importing app modules
os.environ.setdefault("TESTING_AUTH_BYPASS", "true")
os.environ.setdefault("GEMINI_API_KEY", "test-api-key")

from mvp_site import constants
from mvp_site.agents import PlanningAgent, StoryModeAgent
from mvp_site.game_state import GameState


class TestPlanningProtocolLoaded(unittest.TestCase):
    """Test that planning_protocol.md is loaded into system prompts."""

    def setUp(self):
        """Set up test fixtures."""
        os.environ["TESTING_AUTH_BYPASS"] = "true"
        # Create a minimal game state for agent instantiation
        # GameState uses **kwargs, not a single dict argument
        self.game_state = GameState(
            player_character_data={
                "name": "Test Character",
                "class": "Fighter",
            },
        )

    def test_story_mode_agent_includes_planning_protocol(self):
        """Verify StoryModeAgent system instructions include planning_protocol.md content."""
        agent = StoryModeAgent(game_state=self.game_state)

        # Build system instructions
        system_instructions = agent.build_system_instructions(
            selected_prompts=[
                constants.PROMPT_TYPE_NARRATIVE,
                constants.PROMPT_TYPE_MECHANICS,
            ],
            use_default_world=False,
        )

        # The planning_protocol.md file contains this unique header
        expected_header = "# Planning Protocol (Unified)"
        self.assertIn(
            expected_header,
            system_instructions,
            f"planning_protocol.md header not found in StoryModeAgent system instructions. "
            f"The file is declared in REQUIRED_PROMPTS but never actually loaded. "
            f"Instructions length: {len(system_instructions)} chars",
        )

        # Verify the purpose statement is present (unique to planning_protocol.md)
        expected_purpose = "Single source of truth for planning block structure"
        self.assertIn(
            expected_purpose,
            system_instructions,
            "planning_protocol.md purpose statement not found. "
            "File may not be loaded into system prompt.",
        )

    def test_planning_agent_includes_planning_protocol(self):
        """Verify PlanningAgent (Think Mode) system instructions include planning_protocol.md content."""
        agent = PlanningAgent(game_state=self.game_state)

        # Build system instructions
        system_instructions = agent.build_system_instructions(
            use_default_world=False,
        )

        # The planning_protocol.md file contains this unique header
        expected_header = "# Planning Protocol (Unified)"
        self.assertIn(
            expected_header,
            system_instructions,
            f"planning_protocol.md header not found in PlanningAgent system instructions. "
            f"The file is declared in REQUIRED_PROMPTS but never actually loaded. "
            f"Instructions length: {len(system_instructions)} chars",
        )

    def test_planning_protocol_content_present(self):
        """Verify unique planning_protocol.md content is in system instructions.

        This tests for content that ONLY exists in planning_protocol.md,
        not just generic schema fields that might appear in other prompts.
        """
        agent = StoryModeAgent(game_state=self.game_state)

        system_instructions = agent.build_system_instructions(
            selected_prompts=[constants.PROMPT_TYPE_NARRATIVE],
            use_default_world=False,
        )

        # Content unique to planning_protocol.md (not in other prompt files)
        unique_content = "Single source of truth for planning block structure"
        self.assertIn(
            unique_content,
            system_instructions,
            "planning_protocol.md unique content not found. "
            "File is in PATH_MAP but never loaded via _load_instruction_file(). "
            "REQUIRED_PROMPTS is declarative metadata only - it doesn't trigger loading.",
        )

        # Also check for the table explaining mode differences (unique to this file)
        mode_table_content = "Time FROZEN (+1 microsecond only)"
        self.assertIn(
            mode_table_content,
            system_instructions,
            "planning_protocol.md mode table content not found. "
            "The canonical time-handling rules for Think Mode are not reaching the LLM.",
        )

    def test_planning_protocol_in_path_map(self):
        """Verify planning_protocol is registered in PATH_MAP (prerequisite for loading)."""
        from mvp_site.agent_prompts import PATH_MAP

        self.assertIn(
            constants.PROMPT_TYPE_PLANNING_PROTOCOL,
            PATH_MAP,
            "PROMPT_TYPE_PLANNING_PROTOCOL not in PATH_MAP - cannot be loaded",
        )

        # Verify the path points to the correct file
        expected_path = "prompts/planning_protocol.md"
        self.assertIn(
            "planning_protocol.md",
            PATH_MAP[constants.PROMPT_TYPE_PLANNING_PROTOCOL],
            "PATH_MAP entry should point to planning_protocol.md",
        )


class TestPlanningProtocolFileExists(unittest.TestCase):
    """Sanity checks that the planning_protocol.md file exists and has expected content."""

    def test_planning_protocol_file_exists(self):
        """Verify planning_protocol.md file exists at the expected path."""
        file_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "prompts",
            "planning_protocol.md",
        )
        self.assertTrue(
            os.path.exists(file_path),
            f"planning_protocol.md not found at {file_path}",
        )

    def test_planning_protocol_has_schema_placeholders(self):
        """Verify planning_protocol.md contains placeholders for schema injection."""
        file_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "prompts",
            "planning_protocol.md",
        )

        with open(file_path) as f:
            content = f.read()

        # The file should contain placeholders that get replaced at runtime
        self.assertIn(
            "{{PLANNING_BLOCK_SCHEMA}}",
            content,
            "planning_protocol.md should contain {{PLANNING_BLOCK_SCHEMA}} placeholder",
        )
        self.assertIn(
            "{{CHOICE_SCHEMA}}",
            content,
            "planning_protocol.md should contain {{CHOICE_SCHEMA}} placeholder",
        )


if __name__ == "__main__":
    unittest.main()
