#!/usr/bin/env python3
"""
Comprehensive Combat Cleanup Tests

This test file contains comprehensive tests for the automatic cleanup system,
including edge cases and realistic combat scenarios.
"""

import os
import sys
import unittest

# Add parent directory for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from firestore_service import update_state_with_changes
from game_state import GameState
from world_logic import apply_automatic_combat_cleanup


class TestCombatCleanupComprehensive(unittest.TestCase):
    """
    Comprehensive tests for combat cleanup functionality.
    Tests cover various scenarios including edge cases and realistic workflows.
    """

    def test_automatic_cleanup_via_state_updates_hp_defeat(self):
        """
        Test: Enemy defeated via AI HP update should be automatically cleaned up.

        This test verifies the fix is working correctly.
        """
        print("\nTesting: Automatic cleanup via HP state updates")

        # Step 1: Create realistic game state with active combat
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
                "name": "Orc Warrior",
                "initiative": 14,
                "type": "enemy",
                "hp_current": 30,
                "hp_max": 30,
            },  # Healthy enemy
            {
                "name": "Goblin",
                "initiative": 12,
                "type": "enemy",
                "hp_current": 15,
                "hp_max": 15,
            },  # Healthy enemy
        ]

        game_state.start_combat(combatants_data)

        # Add enemies to NPC data (as would happen in real game)
        game_state.npc_data = {
            "Orc Warrior": {
                "name": "Fierce Orc",
                "type": "enemy",
                "description": "A brutal warrior",
            },
            "Goblin": {
                "name": "Sneaky Goblin",
                "type": "enemy",
                "description": "Quick and cunning",
            },
            "Merchant": {
                "name": "Bob",
                "type": "neutral",
                "description": "Friendly trader",
            },
        }

        # Verify initial state
        assert "Orc Warrior" in game_state.combat_state["combatants"]
        assert "Goblin" in game_state.combat_state["combatants"]
        assert game_state.combat_state["combatants"]["Orc Warrior"]["hp_current"] == 30

        print(
            f"Initial combatants: {list(game_state.combat_state['combatants'].keys())}"
        )
        print(f"Initial NPC data: {list(game_state.npc_data.keys())}")

        # Step 2: Simulate AI defeating the Orc via state update (not direct manipulation)
        # This is how it actually happens in the real game workflow
        ai_proposed_changes = {
            "combat_state": {
                "combatants": {
                    "Orc Warrior": {
                        "hp_current": 0,  # AI sets enemy HP to 0
                        "status": ["bloodied", "unconscious"],
                    }
                }
            }
        }

        print(f"AI proposed changes: {ai_proposed_changes}")

        # Step 3: Apply the full state update + automatic cleanup workflow
        initial_state_dict = game_state.to_dict()
        updated_state_dict = update_state_with_changes(
            initial_state_dict, ai_proposed_changes
        )
        final_state_dict = apply_automatic_combat_cleanup(
            updated_state_dict, ai_proposed_changes
        )

        # Step 4: VERIFY the cleanup worked
        print(
            f"After automatic cleanup - Combatants: {list(final_state_dict['combat_state']['combatants'].keys())}"
        )
        print(
            f"After automatic cleanup - NPCs: {list(final_state_dict['npc_data'].keys())}"
        )

        # Verify the fix is working

        # The defeated enemy should be completely removed from combat
        assert (
            "Orc Warrior" not in final_state_dict["combat_state"]["combatants"]
        ), "Defeated enemy should be removed from combatants after HP=0 update"

        # The defeated enemy should be removed from initiative order
        initiative_names = [
            entry["name"]
            for entry in final_state_dict["combat_state"]["initiative_order"]
        ]
        assert (
            "Orc Warrior" not in initiative_names
        ), "Defeated enemy should be removed from initiative order"

        # The defeated enemy should be removed from NPC data
        assert (
            "Orc Warrior" not in final_state_dict["npc_data"]
        ), "Defeated enemy should be removed from NPC data"

        # Living entities should remain
        assert (
            "Hero" in final_state_dict["combat_state"]["combatants"]
        ), "Hero should remain in combat"
        assert (
            "Goblin" in final_state_dict["combat_state"]["combatants"]
        ), "Living enemy should remain in combat"
        assert (
            "Merchant" in final_state_dict["npc_data"]
        ), "Non-combat NPC should remain in NPC data"

    def test_combat_end_with_pre_defeated_enemies(self):
        """
        Test: When combat ends and there are already defeated enemies, they should be cleaned up.

        This tests the edge case where:
        1. Enemy is defeated in an earlier turn but not cleaned up
        2. AI ends combat without explicitly cleaning defeated enemies
        3. The automatic cleanup should catch and remove them
        """
        print("\nTesting: Combat end with pre-defeated enemies")

        # Step 1: Set up combat with one enemy already defeated
        game_state = GameState()
        combatants_data = [
            {
                "name": "Player",
                "initiative": 15,
                "type": "pc",
                "hp_current": 40,
                "hp_max": 50,
            },
            {
                "name": "Dead Orc",
                "initiative": 12,
                "type": "enemy",
                "hp_current": 0,
                "hp_max": 25,
            },  # Already dead
            {
                "name": "Living Wolf",
                "initiative": 10,
                "type": "companion",
                "hp_current": 20,
                "hp_max": 20,
            },
        ]

        game_state.start_combat(combatants_data)
        game_state.npc_data = {
            "Dead Orc": {"name": "Orc Scout", "type": "enemy"},
            "Trader": {"name": "Merchant", "type": "neutral"},
        }

        # Verify the defeated enemy is present initially (bug scenario)
        assert "Dead Orc" in game_state.combat_state["combatants"]
        assert game_state.combat_state["combatants"]["Dead Orc"]["hp_current"] == 0

        print(
            f"Before combat end - Combatants: {list(game_state.combat_state['combatants'].keys())}"
        )
        print(
            f"Dead Orc HP: {game_state.combat_state['combatants']['Dead Orc']['hp_current']}"
        )

        # Step 2: AI ends combat (common workflow)
        ai_proposed_changes = {"combat_state": {"in_combat": False, "current_round": 0}}

        # Step 3: Apply state update + cleanup
        initial_state_dict = game_state.to_dict()
        updated_state_dict = update_state_with_changes(
            initial_state_dict, ai_proposed_changes
        )
        final_state_dict = apply_automatic_combat_cleanup(
            updated_state_dict, ai_proposed_changes
        )

        print(
            f"After combat end - In combat: {final_state_dict['combat_state']['in_combat']}"
        )
        print(
            f"After combat end - Combatants: {list(final_state_dict['combat_state']['combatants'].keys())}"
        )

        # Verify expectations

        # Combat should be properly ended
        assert not final_state_dict["combat_state"][
            "in_combat"
        ], "Combat should be ended"

        # The pre-defeated enemy should be cleaned up when combat ends
        assert (
            "Dead Orc" not in final_state_dict["combat_state"]["combatants"]
        ), "Pre-defeated enemies should be cleaned up when combat ends"

        assert (
            "Dead Orc" not in final_state_dict["npc_data"]
        ), "Pre-defeated enemies should be removed from NPC data"

        # Living entities should remain
        assert (
            "Player" in final_state_dict["combat_state"]["combatants"]
        ), "Player should remain"
        assert (
            "Living Wolf" in final_state_dict["combat_state"]["combatants"]
        ), "Living companion should remain"

    def test_multiple_enemies_defeated_same_turn(self):
        """
        Test: Multiple enemies defeated in the same AI response should all be cleaned up.

        This tests area-effect damage scenarios where multiple enemies die simultaneously.
        """
        print("\nTesting: Multiple simultaneous defeats")

        # Step 1: Set up combat with multiple enemies
        game_state = GameState()
        combatants_data = [
            {
                "name": "Wizard",
                "initiative": 20,
                "type": "pc",
                "hp_current": 35,
                "hp_max": 35,
            },
            {
                "name": "Goblin A",
                "initiative": 15,
                "type": "enemy",
                "hp_current": 10,
                "hp_max": 10,
            },
            {
                "name": "Goblin B",
                "initiative": 14,
                "type": "enemy",
                "hp_current": 8,
                "hp_max": 8,
            },
            {
                "name": "Orc Chief",
                "initiative": 13,
                "type": "enemy",
                "hp_current": 25,
                "hp_max": 25,
            },
        ]

        game_state.start_combat(combatants_data)
        game_state.npc_data = {
            "Goblin A": {"name": "Goblin Scout A", "type": "enemy"},
            "Goblin B": {"name": "Goblin Scout B", "type": "enemy"},
            "Orc Chief": {"name": "Orc War Chief", "type": "enemy"},
            "Village Elder": {"name": "Wise Elder", "type": "ally"},
        }

        print(
            f"Before fireball - Combatants: {list(game_state.combat_state['combatants'].keys())}"
        )

        # Step 2: Simulate AI casting fireball that kills multiple enemies
        ai_proposed_changes = {
            "combat_state": {
                "combatants": {
                    "Goblin A": {
                        "hp_current": 0,
                        "status": ["dead"],
                    },  # Killed by fireball
                    "Goblin B": {
                        "hp_current": 0,
                        "status": ["dead"],
                    },  # Killed by fireball
                    "Orc Chief": {
                        "hp_current": 5,
                        "status": ["wounded"],
                    },  # Survived but wounded
                }
            }
        }

        # Step 3: Apply state update + cleanup
        initial_state_dict = game_state.to_dict()
        updated_state_dict = update_state_with_changes(
            initial_state_dict, ai_proposed_changes
        )
        final_state_dict = apply_automatic_combat_cleanup(
            updated_state_dict, ai_proposed_changes
        )

        print(
            f"After fireball - Combatants: {list(final_state_dict['combat_state']['combatants'].keys())}"
        )
        print(f"After fireball - NPCs: {list(final_state_dict['npc_data'].keys())}")

        # Verify cleanup worked correctly

        # Both goblins should be removed
        assert (
            "Goblin A" not in final_state_dict["combat_state"]["combatants"]
        ), "First defeated enemy should be removed"
        assert (
            "Goblin B" not in final_state_dict["combat_state"]["combatants"]
        ), "Second defeated enemy should be removed"

        assert (
            "Goblin A" not in final_state_dict["npc_data"]
        ), "First defeated enemy should be removed from NPCs"
        assert (
            "Goblin B" not in final_state_dict["npc_data"]
        ), "Second defeated enemy should be removed from NPCs"

        # Survivors should remain
        assert (
            "Wizard" in final_state_dict["combat_state"]["combatants"]
        ), "PC should remain"
        assert (
            "Orc Chief" in final_state_dict["combat_state"]["combatants"]
        ), "Wounded but living enemy should remain"
        assert (
            "Village Elder" in final_state_dict["npc_data"]
        ), "Non-combat NPC should remain"

        # Verify wounded enemy has correct HP
        assert (
            final_state_dict["combat_state"]["combatants"]["Orc Chief"]["hp_current"]
            == 5
        ), "Wounded enemy should have reduced HP"

    def test_cleanup_without_explicit_combat_state_changes(self):
        """
        Test: Cleanup should trigger even when combat_state isn't explicitly in proposed_changes.

        This tests whether the cleanup is robust enough to detect defeated enemies
        even when the AI makes other types of updates (like updating turn order).
        """
        print("\nTesting: Cleanup without explicit combat state changes")

        # Step 1: Set up combat with a defeated enemy (simulating a previous turn)
        game_state = GameState()
        combatants_data = [
            {
                "name": "Ranger",
                "initiative": 16,
                "type": "pc",
                "hp_current": 30,
                "hp_max": 30,
            },
            {
                "name": "Troll",
                "initiative": 8,
                "type": "enemy",
                "hp_current": 0,
                "hp_max": 45,
            },  # Defeated previously
        ]

        game_state.start_combat(combatants_data)
        game_state.npc_data = {"Troll": {"name": "Cave Troll", "type": "enemy"}}

        # Verify defeated enemy is present (bug scenario)
        assert game_state.combat_state["combatants"]["Troll"]["hp_current"] == 0

        print(
            f"Before update - Troll HP: {game_state.combat_state['combatants']['Troll']['hp_current']}"
        )
        print(
            f"Before update - Combatants: {list(game_state.combat_state['combatants'].keys())}"
        )

        # Step 2: AI makes a different type of update (not directly to combatants)
        ai_proposed_changes = {
            "combat_state": {"current_turn_index": 1, "current_round": 3},
            "world_data": {"current_weather": "stormy"},
        }

        # Step 3: Apply state update + cleanup
        initial_state_dict = game_state.to_dict()
        updated_state_dict = update_state_with_changes(
            initial_state_dict, ai_proposed_changes
        )
        final_state_dict = apply_automatic_combat_cleanup(
            updated_state_dict, ai_proposed_changes
        )

        print(
            f"After update - Combatants: {list(final_state_dict['combat_state']['combatants'].keys())}"
        )

        # Verify cleanup worked

        # Even though we didn't explicitly change combatants, the cleanup should still
        # notice the defeated enemy and remove it
        assert (
            "Troll" not in final_state_dict["combat_state"]["combatants"]
        ), "Pre-defeated enemies should be cleaned up even without explicit combatant changes"

        assert (
            "Troll" not in final_state_dict["npc_data"]
        ), "Pre-defeated enemies should be removed from NPCs"

        # Turn progression should work normally
        assert final_state_dict["combat_state"]["current_turn_index"] == 1
        assert final_state_dict["combat_state"]["current_round"] == 3

        # Living entities should remain
        assert "Ranger" in final_state_dict["combat_state"]["combatants"]


if __name__ == "__main__":
    print("Running comprehensive combat cleanup tests")
    print("These tests verify the automatic cleanup system works correctly")
    print("=" * 70)

    # Run with high verbosity to see detailed output
    unittest.main(verbosity=2)
