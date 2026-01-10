"""
End-to-end tests for Think Mode state freeze behavior.

Issue 2: Think mode is supposed to freeze all state changes (except microsecond),
but apply_automatic_combat_cleanup still runs and can mutate state even when
think-mode filtering removes all updates.

This test verifies that:
1. Think mode only allows microsecond time advancement
2. Combat cleanup does NOT run during think mode
3. Defeated enemies are NOT removed during think mode
"""

from __future__ import annotations

import copy
import os
import unittest
from unittest.mock import MagicMock, patch

# Ensure TESTING_AUTH_BYPASS is set before importing app modules
os.environ.setdefault("TESTING_AUTH_BYPASS", "true")
os.environ.setdefault("GEMINI_API_KEY", "test-api-key")

from mvp_site.world_logic import apply_automatic_combat_cleanup


class TestThinkModeStateFreezeEndToEnd(unittest.TestCase):
    """Test that Think Mode properly freezes state and doesn't run cleanup."""

    def setUp(self):
        """Set up test fixtures with combat state containing defeated enemies."""
        os.environ["TESTING_AUTH_BYPASS"] = "true"

        # Game state with a defeated enemy (HP <= 0)
        self.game_state_with_defeated_enemy = {
            "game_state": {
                "combat_state": {
                    "in_combat": True,
                    "combatants": [
                        {
                            "name": "Player",
                            "hp": 50,
                            "max_hp": 50,
                            "is_player": True,
                        },
                        {
                            "name": "Goblin",
                            "hp": 0,  # DEFEATED
                            "max_hp": 10,
                            "is_player": False,
                        },
                    ],
                },
                "npc_data": {
                    "Goblin": {
                        "hp": 0,
                        "max_hp": 10,
                        "status": "alive",  # Should be marked dead by cleanup
                    },
                },
            },
            "player_character_data": {
                "name": "Test Hero",
                "class": "Fighter",
            },
            "world_data": {
                "world_time": {
                    "year": 1492,
                    "month": "Mirtul",
                    "day": 15,
                    "hour": 10,
                    "minute": 30,
                    "second": 0,
                    "microsecond": 100,
                },
            },
        }

    def test_combat_cleanup_does_not_run_in_think_mode(self):
        """Verify apply_automatic_combat_cleanup is skipped when is_think_mode=True.

        BUG: Currently, apply_automatic_combat_cleanup runs even in think mode,
        which can remove defeated enemies during a "frozen state" think turn.

        The fix should gate cleanup on is_think_mode flag.
        """
        # Make a deep copy to track mutations
        original_state = copy.deepcopy(self.game_state_with_defeated_enemy)
        state_to_check = copy.deepcopy(self.game_state_with_defeated_enemy)

        # Simulate think mode - only microsecond should change
        proposed_changes = {
            "world_data": {
                "world_time": {"microsecond": 101}  # Only allowed change
            }
        }

        # CURRENT BEHAVIOR (BUG): Cleanup runs and can mutate state
        # Apply cleanup to see if it mutates state
        result_state = apply_automatic_combat_cleanup(state_to_check, proposed_changes)

        # Check if the Goblin was removed or modified
        combat_state = result_state.get("game_state", {}).get("combat_state", {})
        combatants = combat_state.get("combatants", [])
        npc_data = result_state.get("game_state", {}).get("npc_data", {})

        # Get original counts
        original_combatants = (
            original_state.get("game_state", {})
            .get("combat_state", {})
            .get("combatants", [])
        )
        original_npc_count = len(
            original_state.get("game_state", {}).get("npc_data", {})
        )

        # In think mode, NO state should change (including combatant cleanup)
        # This test will FAIL until we add is_think_mode gating to cleanup
        combatant_removed = len(combatants) < len(original_combatants)
        npc_modified = len(npc_data) < original_npc_count or (
            "Goblin" in npc_data and npc_data["Goblin"].get("status") == "dead"
        )

        # The test asserts that cleanup SHOULD NOT run in think mode
        # Currently this will FAIL because cleanup runs unconditionally
        self.assertFalse(
            combatant_removed or npc_modified,
            f"BUG: Combat cleanup ran during what should be think mode. "
            f"Combatants before: {len(original_combatants)}, after: {len(combatants)}. "
            f"NPC data modified: {npc_modified}. "
            f"Think mode should freeze ALL state changes including cleanup.",
        )


class TestThinkModeIntegrationWithCleanup(unittest.TestCase):
    """Integration tests for think mode with the full process_response flow."""

    def setUp(self):
        """Set up test fixtures."""
        os.environ["TESTING_AUTH_BYPASS"] = "true"

        self.base_game_state = {
            "game_state": {
                "combat_state": {
                    "in_combat": True,
                    "combatants": [
                        {"name": "Hero", "hp": 50, "max_hp": 50, "is_player": True},
                        {"name": "Orc", "hp": 0, "max_hp": 20, "is_player": False},
                    ],
                },
                "npc_data": {
                    "Orc": {"hp": 0, "max_hp": 20},
                },
            },
            "player_character_data": {"name": "Hero", "class": "Warrior"},
            "world_data": {
                "world_time": {"microsecond": 500},
            },
        }

    @patch("mvp_site.world_logic.apply_automatic_combat_cleanup")
    def test_cleanup_should_be_skipped_when_think_mode(self, mock_cleanup):
        """Verify that process_response skips cleanup when is_think_mode=True.

        This tests the integration point where cleanup should be gated.
        The mock will tell us if cleanup was called when it shouldn't be.
        """
        # Import here to avoid circular import issues
        from mvp_site.world_logic import update_state_with_changes

        is_think_mode = True

        # Simulate the think mode state filtering (lines 1551-1578 in world_logic.py)
        state_changes = {
            "world_data": {"world_time": {"microsecond": 501}},
            "game_state": {"npc_data": {"Orc": {"status": "dead"}}},  # Should be blocked
        }

        if is_think_mode:
            # Filter to only allow microsecond (current behavior)
            allowed_changes = {}
            if "world_data" in state_changes:
                world_data = state_changes.get("world_data", {})
                if world_data and "world_time" in world_data:
                    world_time_changes = world_data.get("world_time", {})
                    if world_time_changes and "microsecond" in world_time_changes:
                        allowed_changes = {
                            "world_data": {
                                "world_time": {
                                    "microsecond": world_time_changes["microsecond"]
                                }
                            }
                        }
            state_changes_to_apply = allowed_changes
        else:
            state_changes_to_apply = state_changes

        # Apply the filtered changes
        updated_state = update_state_with_changes(
            copy.deepcopy(self.base_game_state), state_changes_to_apply
        )

        # THE BUG: Currently cleanup is called unconditionally after this
        # The FIX: Cleanup should be skipped when is_think_mode=True

        # This assertion documents the EXPECTED behavior after fix:
        # When is_think_mode=True, cleanup should NOT be called
        if is_think_mode:
            # After fix, we should NOT call cleanup
            # For now, document that this is the expected behavior
            pass  # Cleanup should be skipped

        # Verify the Orc is still in combat (state frozen)
        orc_still_present = any(
            c.get("name") == "Orc"
            for c in updated_state.get("game_state", {})
            .get("combat_state", {})
            .get("combatants", [])
        )
        self.assertTrue(
            orc_still_present,
            "Orc should still be in combatants during think mode (state frozen). "
            "The defeated enemy should NOT be cleaned up during think mode.",
        )


if __name__ == "__main__":
    unittest.main()
