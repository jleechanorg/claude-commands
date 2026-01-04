"""
End-to-end tests for planning_protocol.md loading across ALL modes.

Issue 1: Combat, Rewards, and Info modes reference "Planning Protocol" in
game_state_instruction.md but don't actually load planning_protocol.md.
This causes a dangling reference where the LLM sees "See Planning Protocol"
but never receives the actual schema.

These tests verify that planning_protocol.md content is loaded into ALL
modes that use planning_block (which is all modes except DM mode).
"""

from __future__ import annotations

import os
import unittest

# Ensure TESTING is set before importing app modules
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("GEMINI_API_KEY", "test-api-key")

from mvp_site import constants
from mvp_site.agents import CombatAgent, InfoAgent, RewardsAgent
from mvp_site.game_state import GameState


class TestPlanningProtocolInAllModes(unittest.TestCase):
    """Test that planning_protocol.md is loaded in all modes that use planning_block."""

    def setUp(self):
        """Set up test fixtures."""
        os.environ["TESTING"] = "true"
        # Create a minimal game state for agent instantiation
        self.game_state = GameState(
            player_character_data={
                "name": "Test Character",
                "class": "Fighter",
            },
        )

    def test_combat_agent_includes_planning_protocol(self):
        """Verify CombatAgent system instructions include planning_protocol.md content.

        Combat mode uses planning_block for tactical choices during combat.
        It references "Planning Protocol" in game_state_instruction.md:179 but
        currently doesn't load the actual file.
        """
        agent = CombatAgent(game_state=self.game_state)

        # Build system instructions
        system_instructions = agent.build_system_instructions()

        # The planning_protocol.md file contains this unique header
        expected_header = "# Planning Protocol (Unified)"
        self.assertIn(
            expected_header,
            system_instructions,
            f"planning_protocol.md header not found in CombatAgent system instructions. "
            f"Combat mode references 'Planning Protocol' in game_state_instruction.md:179 "
            f"but doesn't load the file. This causes a dangling reference. "
            f"Instructions length: {len(system_instructions)} chars",
        )

        # Verify the purpose statement is present (unique to planning_protocol.md)
        expected_purpose = "Single source of truth for planning block structure"
        self.assertIn(
            expected_purpose,
            system_instructions,
            f"planning_protocol.md purpose statement not found in CombatAgent. "
            f"The canonical planning block schema is missing from combat mode.",
        )

    def test_rewards_agent_includes_planning_protocol(self):
        """Verify RewardsAgent system instructions include planning_protocol.md content.

        Rewards mode REQUIRES planning_block for level-up choices (see rewards_system:21-231).
        It references "Planning Protocol" in game_state_instruction.md:179 but
        currently doesn't load the actual file.
        """
        agent = RewardsAgent(game_state=self.game_state)

        # Build system instructions
        system_instructions = agent.build_system_instructions()

        # The planning_protocol.md file contains this unique header
        expected_header = "# Planning Protocol (Unified)"
        self.assertIn(
            expected_header,
            system_instructions,
            f"planning_protocol.md header not found in RewardsAgent system instructions. "
            f"Rewards mode REQUIRES planning_block for level-up choices but doesn't load "
            f"the Planning Protocol schema. This causes a dangling reference. "
            f"Instructions length: {len(system_instructions)} chars",
        )

    def test_info_agent_includes_planning_protocol(self):
        """Verify InfoAgent system instructions include planning_protocol.md content.

        Info mode still uses planning_block per game_state_instruction.md:764:
        "include the standard response fields (session_header, narrative, planning_block, etc.)"
        It references "Planning Protocol" in game_state_instruction.md:179.
        """
        agent = InfoAgent(game_state=self.game_state)

        # Build system instructions
        system_instructions = agent.build_system_instructions()

        # The planning_protocol.md file contains this unique header
        expected_header = "# Planning Protocol (Unified)"
        self.assertIn(
            expected_header,
            system_instructions,
            f"planning_protocol.md header not found in InfoModeAgent system instructions. "
            f"Info mode uses planning_block per game_state_instruction.md:764 but doesn't "
            f"load the Planning Protocol schema. This causes a dangling reference. "
            f"Instructions length: {len(system_instructions)} chars",
        )

    def test_all_modes_have_valid_risk_levels(self):
        """Verify all modes have risk levels injected from planning_protocol.md.

        The planning_protocol.md contains {{VALID_RISK_LEVELS}} placeholder that
        gets replaced with actual risk level values. Without loading the file,
        modes don't have this schema information.
        """
        agents = [
            ("CombatAgent", CombatAgent(game_state=self.game_state)),
            ("RewardsAgent", RewardsAgent(game_state=self.game_state)),
            ("InfoAgent", InfoAgent(game_state=self.game_state)),
        ]

        for agent_name, agent in agents:
            system_instructions = agent.build_system_instructions()

            # Risk levels should be present (from schema injection)
            # The raw placeholder should NOT be present
            self.assertNotIn(
                "{{VALID_RISK_LEVELS}}",
                system_instructions,
                f"{agent_name}: Raw {{{{VALID_RISK_LEVELS}}}} placeholder found. "
                f"Either planning_protocol.md is not loaded or schema injection failed.",
            )

            # The injected values should be present (if planning_protocol is loaded)
            # Valid risk levels are: safe, low, medium, high
            self.assertIn(
                '"safe"',
                system_instructions,
                f"{agent_name}: Injected risk level 'safe' not found. "
                f"planning_protocol.md may not be loaded for this mode.",
            )


if __name__ == "__main__":
    unittest.main()
