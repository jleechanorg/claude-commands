#!/usr/bin/env python3
"""
TDD Tests for NPC Death State Persistence Bug

Bug: When a user kills an NPC (e.g., Marcus), the game still presents options to
kill them again on subsequent turns. The death state is not being properly synced
between combat_state and npc_data.

Root Causes:
1. apply_automatic_combat_cleanup NOT called in main story flow
2. cleanup_defeated_enemies DELETES named NPCs instead of marking them dead

These tests are written BEFORE the fix to verify they fail, demonstrating TDD.
"""

import os
import sys
import unittest

# Add parent directory for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from mvp_site.firestore_service import update_state_with_changes
from mvp_site.game_state import GameState
from mvp_site.world_logic import apply_automatic_combat_cleanup


class TestNamedNPCDeathStatePersistence(unittest.TestCase):
    """
    Tests for Issue 2: Named NPCs should be marked as dead instead of deleted.

    For named NPCs (Marcus, important characters), we need to KEEP the NPC record
    with status: ["dead"] so:
    - The LLM knows they're dead in future turns
    - The game can reference dead NPCs in narrative
    - Entity tracking shows them as deceased
    """

    def test_named_npc_with_role_marked_dead_not_deleted(self):
        """
        Test: Named NPC with a role should be marked dead, not deleted.

        Named NPCs are identified by having a role that isn't generic (enemy/minion).
        These NPCs should be preserved with status: ["dead"] for narrative continuity.
        """
        # Setup: Create game state with a named NPC (has role "merchant")
        game_state = GameState()
        combatants_data = [
            {
                "name": "Hero",
                "initiative": 18,
                "type": "pc",
                "hp_current": 50,
                "hp_max": 50,
            },
            {
                "name": "Marcus",
                "initiative": 14,
                "type": "enemy",
                "hp_current": 0,
                "hp_max": 30,
            },
        ]

        game_state.start_combat(combatants_data)

        # Marcus is a named NPC with a role - should be preserved when killed
        game_state.npc_data = {
            "Marcus": {
                "name": "Marcus the Betrayer",
                "role": "merchant",  # Named NPC - has meaningful role
                "backstory": "A corrupt merchant who betrayed the town",
                "description": "A well-dressed man with shifty eyes",
            }
        }

        # Act: Run cleanup (Marcus has hp_current=0)
        defeated = game_state.cleanup_defeated_enemies()

        # Assert: Marcus should still exist in npc_data with status: ["dead"]
        self.assertIn("Marcus", defeated, "Marcus should be in defeated list")

        # CRITICAL TEST: Named NPC should NOT be deleted
        self.assertIn(
            "Marcus",
            game_state.npc_data,
            f"Named NPC 'Marcus' should be preserved in npc_data, not deleted. "
            f"Current npc_data: {game_state.npc_data}",
        )

        # The NPC should be marked as dead
        marcus_data = game_state.npc_data.get("Marcus", {})
        self.assertIn(
            "dead",
            marcus_data.get("status", []),
            f"Marcus should have 'dead' in status. Current data: {marcus_data}",
        )

        # HP should be 0
        self.assertEqual(
            marcus_data.get("hp_current", -1),
            0,
            f"Marcus hp_current should be 0. Current data: {marcus_data}",
        )

    def test_named_npc_with_backstory_marked_dead_not_deleted(self):
        """
        Test: Named NPC with backstory should be marked dead, not deleted.
        """
        game_state = GameState()
        combatants_data = [
            {
                "name": "Hero",
                "initiative": 18,
                "type": "pc",
                "hp_current": 50,
                "hp_max": 50,
            },
            {
                "name": "Lady Vex",
                "initiative": 10,
                "type": "enemy",
                "hp_current": 0,
                "hp_max": 25,
            },
        ]

        game_state.start_combat(combatants_data)

        # Lady Vex is a named NPC with backstory - should be preserved when killed
        game_state.npc_data = {
            "Lady Vex": {
                "name": "Lady Vex",
                "backstory": "A mysterious assassin from the eastern kingdoms",
                "description": "A cloaked figure with deadly grace",
            }
        }

        defeated = game_state.cleanup_defeated_enemies()

        self.assertIn("Lady Vex", defeated)

        # Named NPC should be preserved
        self.assertIn(
            "Lady Vex",
            game_state.npc_data,
            f"Named NPC 'Lady Vex' should be preserved. npc_data: {game_state.npc_data}",
        )

        lady_vex_data = game_state.npc_data.get("Lady Vex", {})
        self.assertIn(
            "dead",
            lady_vex_data.get("status", []),
            f"Lady Vex should have 'dead' status. Data: {lady_vex_data}",
        )

    def test_named_npc_with_background_marked_dead_not_deleted(self):
        """
        Test: NPCs with narrative background should be preserved even if role looks generic.
        """
        game_state = GameState()
        combatants_data = [
            {
                "name": "Hero",
                "initiative": 18,
                "type": "pc",
                "hp_current": 50,
                "hp_max": 50,
            },
            {
                "name": "Archivist",
                "initiative": 9,
                "type": "enemy",
                "hp_current": 0,
                "hp_max": 18,
            },
        ]

        game_state.start_combat(combatants_data)

        # Background should flag this as a named NPC even with a generic role
        game_state.npc_data = {
            "Archivist": {
                "name": "Archivist",
                "role": "enemy",
                "background": "Caretaker of the ancient library",
                "description": "Quiet scholar with hidden motives",
            }
        }

        game_state.cleanup_defeated_enemies()

        self.assertIn(
            "Archivist",
            game_state.npc_data,
            f"NPCs with narrative background should be preserved. npc_data: {game_state.npc_data}",
        )

        archivist = game_state.npc_data.get("Archivist", {})
        self.assertIn(
            "dead",
            archivist.get("status", []),
            f"NPC with background should be marked dead. Data: {archivist}",
        )
        self.assertEqual(
            archivist.get("hp_current"),
            0,
            f"HP should be zeroed for preserved NPCs. Data: {archivist}",
        )

    def test_named_npc_with_is_important_flag_marked_dead(self):
        """
        Test: NPCs with is_important=True should be marked dead, not deleted.
        """
        game_state = GameState()
        combatants_data = [
            {
                "name": "Hero",
                "initiative": 18,
                "type": "pc",
                "hp_current": 50,
                "hp_max": 50,
            },
            {
                "name": "King Aldric",
                "initiative": 5,
                "type": "enemy",
                "hp_current": 0,
                "hp_max": 100,
            },
        ]

        game_state.start_combat(combatants_data)

        game_state.npc_data = {
            "King Aldric": {
                "name": "King Aldric",
                "is_important": True,  # Explicitly marked as important
                "description": "The corrupt king",
            }
        }

        defeated = game_state.cleanup_defeated_enemies()

        self.assertIn("King Aldric", defeated)
        self.assertIn(
            "King Aldric",
            game_state.npc_data,
            f"Important NPC should be preserved. npc_data: {game_state.npc_data}",
        )

        king_data = game_state.npc_data.get("King Aldric", {})
        self.assertIn("dead", king_data.get("status", []))

    def test_named_npc_status_string_converted_and_marked_dead(self):
        """
        Test: Named NPCs with non-list status values should be normalized and marked dead.
        """
        game_state = GameState()
        combatants_data = [
            {
                "name": "Hero",
                "initiative": 18,
                "type": "pc",
                "hp_current": 50,
                "hp_max": 50,
            },
            {
                "name": "Archivist",
                "initiative": 7,
                "type": "enemy",
                "hp_current": 0,
                "hp_max": 18,
            },
        ]

        game_state.start_combat(combatants_data)
        game_state.npc_data = {
            "Archivist": {
                "name": "The Archivist",
                "role": "librarian",
                "backstory": "Keeper of forbidden tomes",
                "status": "exhausted",
            }
        }

        game_state.cleanup_defeated_enemies()

        archivist = game_state.npc_data.get("Archivist", {})
        self.assertIsInstance(
            archivist.get("status"),
            list,
            f"Status should be normalized to list. Current: {archivist.get('status')}",
        )
        self.assertIn(
            "dead",
            archivist.get("status", []),
            f"Named NPC should be marked dead even when status was a string. Data: {archivist}",
        )
        self.assertIn(
            "exhausted",
            archivist.get("status", []),
            f"Existing status value should be preserved. Data: {archivist}",
        )

    def test_named_npc_status_none_becomes_dead_list(self):
        """
        Test: Named NPCs with status=None should get ['dead'] and retain record.
        """
        game_state = GameState()
        combatants_data = [
            {
                "name": "Hero",
                "initiative": 18,
                "type": "pc",
                "hp_current": 50,
                "hp_max": 50,
            },
            {
                "name": "Chronicler",
                "initiative": 9,
                "type": "enemy",
                "hp_current": 0,
                "hp_max": 12,
            },
        ]

        game_state.start_combat(combatants_data)
        game_state.npc_data = {
            "Chronicler": {
                "name": "Chronicler",
                "role": "historian",
                "status": None,
            }
        }

        game_state.cleanup_defeated_enemies()

        chronicler = game_state.npc_data.get("Chronicler", {})
        self.assertListEqual(
            chronicler.get("status"),
            ["dead"],
            f"Status None should normalize to ['dead']. Data: {chronicler}",
        )

    def test_generic_enemy_still_deleted(self):
        """
        Test: Generic enemies (role=enemy, minion, or no special attributes) should be deleted.

        This is a regression test - generic enemies should continue to be removed entirely.
        """
        game_state = GameState()
        combatants_data = [
            {
                "name": "Hero",
                "initiative": 18,
                "type": "pc",
                "hp_current": 50,
                "hp_max": 50,
            },
            {
                "name": "Goblin Scout",
                "initiative": 12,
                "type": "enemy",
                "hp_current": 0,
                "hp_max": 10,
            },
        ]

        game_state.start_combat(combatants_data)

        # Generic enemy - no backstory, role is "enemy", not important
        game_state.npc_data = {
            "Goblin Scout": {
                "name": "Goblin Scout",
                "role": "enemy",  # Generic role
                "description": "A sneaky goblin",
            }
        }

        defeated = game_state.cleanup_defeated_enemies()

        self.assertIn("Goblin Scout", defeated)

        # Generic enemy should be deleted
        self.assertNotIn(
            "Goblin Scout",
            game_state.npc_data,
            f"Generic enemy should be deleted. npc_data: {game_state.npc_data}",
        )

    def test_generic_minion_enemy_deleted(self):
        """
        Test: Enemies with role='minion' should be deleted (generic type).
        """
        game_state = GameState()
        combatants_data = [
            {
                "name": "Hero",
                "initiative": 18,
                "type": "pc",
                "hp_current": 50,
                "hp_max": 50,
            },
            {
                "name": "Orc Minion",
                "initiative": 8,
                "type": "enemy",
                "hp_current": 0,
                "hp_max": 15,
            },
        ]

        game_state.start_combat(combatants_data)

        game_state.npc_data = {
            "Orc Minion": {
                "name": "Orc Minion",
                "role": "minion",  # Minion = generic
                "description": "A brutish orc",
            }
        }

        defeated = game_state.cleanup_defeated_enemies()

        self.assertIn("Orc Minion", defeated)
        self.assertNotIn("Orc Minion", game_state.npc_data)

    def test_enemy_with_no_attributes_deleted(self):
        """
        Test: Enemies with no role/backstory/is_important should be deleted (generic).
        """
        game_state = GameState()
        combatants_data = [
            {
                "name": "Hero",
                "initiative": 18,
                "type": "pc",
                "hp_current": 50,
                "hp_max": 50,
            },
            {
                "name": "Random Wolf",
                "initiative": 6,
                "type": "enemy",
                "hp_current": 0,
                "hp_max": 8,
            },
        ]

        game_state.start_combat(combatants_data)

        # No special attributes - this is a generic enemy
        game_state.npc_data = {
            "Random Wolf": {
                "name": "Random Wolf",
                "description": "A hungry wolf",
            }
        }

        defeated = game_state.cleanup_defeated_enemies()

        self.assertIn("Random Wolf", defeated)
        self.assertNotIn("Random Wolf", game_state.npc_data)

    def test_enemy_with_empty_role_treated_as_generic_and_deleted(self):
        """
        Test: Enemies with empty string role are treated as generic and deleted.
        """
        game_state = GameState()
        combatants_data = [
            {
                "name": "Hero",
                "initiative": 18,
                "type": "pc",
                "hp_current": 50,
                "hp_max": 50,
            },
            {
                "name": "Silent Thug",
                "initiative": 11,
                "type": "enemy",
                "hp_current": 0,
                "hp_max": 12,
            },
        ]

        game_state.start_combat(combatants_data)

        game_state.npc_data = {
            "Silent Thug": {
                "name": "Silent Thug",
                "role": "",
                "description": "A faceless henchman",
            }
        }

        defeated = game_state.cleanup_defeated_enemies()

        self.assertIn("Silent Thug", defeated)
        self.assertNotIn(
            "Silent Thug",
            game_state.npc_data,
            f"Enemies with empty role should be treated as generic. npc_data: {game_state.npc_data}",
        )

    def test_enemy_with_uppercase_role_treated_as_generic_and_deleted(self):
        """
        Test: Enemies with role provided in uppercase are normalized and deleted as generic.
        """
        game_state = GameState()
        combatants_data = [
            {
                "name": "Hero",
                "initiative": 18,
                "type": "pc",
                "hp_current": 50,
                "hp_max": 50,
            },
            {
                "name": "Shouted Bandit",
                "initiative": 9,
                "type": "enemy",
                "hp_current": 0,
                "hp_max": 14,
            },
        ]

        game_state.start_combat(combatants_data)

        game_state.npc_data = {
            "Shouted Bandit": {
                "name": "Shouted Bandit",
                "role": "Enemy",  # Uppercase generic role should still be treated as generic
                "description": "A loud brigand",
            }
        }

        defeated = game_state.cleanup_defeated_enemies()

        self.assertIn("Shouted Bandit", defeated)
        self.assertNotIn(
            "Shouted Bandit",
            game_state.npc_data,
            f"Uppercase generic roles should be normalized and deleted. npc_data: {game_state.npc_data}",
        )

    def test_enemy_with_unknown_type_defaulted_to_generic_and_deleted(self):
        """
        Regression: Enemies created without an explicit type (defaulting to 'unknown') should
        still be cleaned up when defeated, instead of lingering in combat.
        """
        game_state = GameState()
        combatants_data = [
            {
                "name": "Hero",
                "initiative": 18,
                "type": "pc",
                "hp_current": 50,
                "hp_max": 50,
            },
            # No type provided -> start_combat will default to "unknown"
            {"name": "Shadowy Figure", "initiative": 9, "hp_current": 0, "hp_max": 12},
        ]

        game_state.start_combat(combatants_data)
        game_state.npc_data = {"Shadowy Figure": {"name": "Shadowy Figure"}}

        defeated = game_state.cleanup_defeated_enemies()

        self.assertIn(
            "Shadowy Figure",
            defeated,
            f"Enemies with missing type should still be treated as defeated. defeated: {defeated}",
        )
        self.assertNotIn(
            "Shadowy Figure",
            game_state.combat_state["combatants"],
            f"Unknown-type enemies should be removed from combatants. combatants: {game_state.combat_state['combatants']}",
        )
        self.assertNotIn(
            "Shadowy Figure",
            game_state.npc_data,
            f"Unknown-type enemies should be removed from npc_data as generic foes. npc_data: {game_state.npc_data}",
        )

    def test_pc_not_removed_when_initiative_entry_missing_type(self):
        """
        Edge Case: PCs/allies should not be removed if initiative data is missing type.
        """
        game_state = GameState()
        combatants_data = [
            {
                "name": "Hero",
                "initiative": 18,
                "type": "pc",
                "hp_current": 0,
                "hp_max": 50,
            },
            {
                "name": "Goblin Raider",
                "initiative": 12,
                "type": "enemy",
                "hp_current": 0,
                "hp_max": 20,
            },
        ]

        game_state.start_combat(combatants_data)
        # Simulate missing initiative entry/type for the PC (e.g., LLM omitted it)
        game_state.combat_state["initiative_order"] = [
            entry
            for entry in game_state.combat_state["initiative_order"]
            if entry["name"] != "Hero"
        ]
        game_state.npc_data = {
            "Hero": {"name": "Hero", "role": "pc", "status": ["unconscious"]},
            "Goblin Raider": {"name": "Goblin Raider", "role": "enemy"},
        }

        final_state = apply_automatic_combat_cleanup(game_state.to_dict(), {})

        self.assertIn(
            "Hero",
            final_state["combat_state"]["combatants"],
            f"Friendly combatant should remain even when initiative type is missing. "
            f"Combatants: {final_state['combat_state']['combatants']}",
        )
        self.assertIn(
            "Hero",
            final_state["npc_data"],
            f"Friendly combatant should not be removed from npc_data. npc_data: {final_state.get('npc_data', {})}",
        )
        self.assertNotIn(
            "Goblin Raider",
            final_state["combat_state"]["combatants"],
            f"Enemy should still be cleaned up. Combatants: {final_state['combat_state']['combatants']}",
        )
        self.assertNotIn(
            "Goblin Raider",
            final_state["npc_data"],
            f"Enemy should be removed from npc_data. npc_data: {final_state.get('npc_data', {})}",
        )

    def test_mixed_named_and_generic_enemies(self):
        """
        Test: In a multi-enemy scenario, named NPCs are preserved, generic deleted.
        """
        game_state = GameState()
        combatants_data = [
            {
                "name": "Hero",
                "initiative": 20,
                "type": "pc",
                "hp_current": 50,
                "hp_max": 50,
            },
            {
                "name": "Marcus",
                "initiative": 14,
                "type": "enemy",
                "hp_current": 0,
                "hp_max": 30,
            },
            {
                "name": "Goblin 1",
                "initiative": 12,
                "type": "enemy",
                "hp_current": 0,
                "hp_max": 8,
            },
            {
                "name": "Goblin 2",
                "initiative": 10,
                "type": "enemy",
                "hp_current": 0,
                "hp_max": 8,
            },
        ]

        game_state.start_combat(combatants_data)

        game_state.npc_data = {
            "Marcus": {
                "name": "Marcus the Betrayer",
                "role": "villain",  # Named NPC
                "backstory": "The big bad guy",
            },
            "Goblin 1": {
                "name": "Goblin 1",
                "role": "minion",  # Generic
            },
            "Goblin 2": {
                "name": "Goblin 2",
                "role": "enemy",  # Generic
            },
        }

        defeated = game_state.cleanup_defeated_enemies()

        # All three should be defeated
        self.assertEqual(len(defeated), 3)

        # Marcus (named) should be preserved with dead status
        self.assertIn("Marcus", game_state.npc_data)
        self.assertIn("dead", game_state.npc_data["Marcus"].get("status", []))

        # Goblins (generic) should be deleted
        self.assertNotIn("Goblin 1", game_state.npc_data)
        self.assertNotIn("Goblin 2", game_state.npc_data)

    def test_dead_npc_not_offered_as_combat_target_next_turn(self):
        """
        Integration test: Dead NPC should NOT appear as a valid target next turn.

        This simulates the full workflow where:
        1. NPC is killed
        2. Next turn starts
        3. The dead NPC should NOT be in active combatants
        """
        game_state = GameState()
        combatants_data = [
            {
                "name": "Hero",
                "initiative": 18,
                "type": "pc",
                "hp_current": 50,
                "hp_max": 50,
            },
            {
                "name": "Marcus",
                "initiative": 14,
                "type": "enemy",
                "hp_current": 30,
                "hp_max": 30,
            },
        ]

        game_state.start_combat(combatants_data)
        game_state.npc_data = {
            "Marcus": {
                "name": "Marcus the Betrayer",
                "role": "villain",
                "backstory": "Betrayed the guild",
            }
        }

        # Simulate AI response setting Marcus HP to 0
        ai_proposed_changes = {
            "combat_state": {
                "combatants": {"Marcus": {"hp_current": 0, "status": ["dead"]}}
            }
        }

        # Apply changes and cleanup
        initial_state = game_state.to_dict()
        updated_state = update_state_with_changes(initial_state, ai_proposed_changes)
        final_state = apply_automatic_combat_cleanup(updated_state, ai_proposed_changes)

        # Marcus should NOT be in combatants (can't target dead enemies in combat)
        self.assertNotIn(
            "Marcus",
            final_state["combat_state"]["combatants"],
            "Dead NPC should not be in combatants list",
        )

        # But Marcus SHOULD still exist in npc_data with dead status
        self.assertIn(
            "Marcus",
            final_state["npc_data"],
            f"Named dead NPC should be preserved in npc_data. npc_data: {final_state.get('npc_data', {})}",
        )

        marcus_npc = final_state["npc_data"].get("Marcus", {})
        self.assertIn(
            "dead",
            marcus_npc.get("status", []),
            f"Marcus should have dead status in npc_data. Data: {marcus_npc}",
        )


class TestMainStoryFlowCombatCleanup(unittest.TestCase):
    """
    Tests for Issue 1: apply_automatic_combat_cleanup should be called in main story flow.

    The main story processing flow (process_story_submission) must call
    apply_automatic_combat_cleanup after update_state_with_changes, just like
    the GOD_MODE flow does.
    """

    def test_automatic_cleanup_called_after_state_update(self):
        """
        Test: The state update workflow should automatically clean up defeated enemies.

        This test simulates what the main story flow should do:
        1. Get AI response with combat state changes
        2. Apply state changes via update_state_with_changes
        3. Apply automatic combat cleanup (THIS IS WHAT'S MISSING!)
        """
        # Setup initial state with active combat
        game_state = GameState()
        combatants_data = [
            {
                "name": "Hero",
                "initiative": 18,
                "type": "pc",
                "hp_current": 50,
                "hp_max": 50,
            },
            {
                "name": "Bandit Leader",
                "initiative": 14,
                "type": "enemy",
                "hp_current": 25,
                "hp_max": 25,
            },
        ]

        game_state.start_combat(combatants_data)
        game_state.npc_data = {
            "Bandit Leader": {
                "name": "Bandit Leader",
                "role": "boss",
                "backstory": "Leader of the highway bandits",
            }
        }

        initial_state = game_state.to_dict()

        # Simulate AI response killing the bandit leader
        ai_response_state_changes = {
            "combat_state": {
                "combatants": {"Bandit Leader": {"hp_current": 0, "status": ["dead"]}}
            }
        }

        # Apply state changes (simulating update_state_with_changes call)
        updated_state = update_state_with_changes(
            initial_state, ai_response_state_changes
        )

        # CRITICAL: This cleanup call is what's missing in main story flow!
        # Without this, defeated enemies persist
        final_state = apply_automatic_combat_cleanup(
            updated_state, ai_response_state_changes
        )

        # Verify the dead enemy is removed from combat
        self.assertNotIn(
            "Bandit Leader",
            final_state["combat_state"]["combatants"],
            "Defeated enemy should be removed from combatants after cleanup",
        )

        # For named NPCs: Should be preserved with dead status (after Fix 2)
        # NOTE: This will fail until Fix 2 is implemented
        self.assertIn(
            "Bandit Leader",
            final_state["npc_data"],
            f"Named NPC should be preserved in npc_data. npc_data: {final_state.get('npc_data', {})}",
        )

    def test_cleanup_without_explicit_changes_still_cleans_defeated(self):
        """
        Test: Cleanup should work even when combat_state isn't in proposed changes.

        This covers the case where an enemy was defeated in a previous turn
        but the cleanup wasn't triggered until a later state update.
        """
        game_state = GameState()
        combatants_data = [
            {
                "name": "Hero",
                "initiative": 18,
                "type": "pc",
                "hp_current": 50,
                "hp_max": 50,
            },
            {
                "name": "Dead Boss",
                "initiative": 14,
                "type": "enemy",
                "hp_current": 0,
                "hp_max": 50,
            },
        ]

        game_state.start_combat(combatants_data)
        game_state.npc_data = {
            "Dead Boss": {
                "name": "Dead Boss",
                "role": "boss",
                "backstory": "Was a boss",
            }
        }

        initial_state = game_state.to_dict()

        # AI makes unrelated changes (no combat_state updates)
        ai_response_state_changes = {"world_data": {"world_time": "afternoon"}}

        updated_state = update_state_with_changes(
            initial_state, ai_response_state_changes
        )
        final_state = apply_automatic_combat_cleanup(
            updated_state, ai_response_state_changes
        )

        # The pre-existing defeated enemy should be cleaned up
        self.assertNotIn(
            "Dead Boss",
            final_state["combat_state"]["combatants"],
            "Pre-defeated enemies should be cleaned up even without explicit combat changes",
        )


if __name__ == "__main__":
    print("=" * 70)
    print("TDD Tests for NPC Death State Persistence Bug")
    print("These tests should FAIL before the fix is applied")
    print("=" * 70)
    unittest.main(verbosity=2)
