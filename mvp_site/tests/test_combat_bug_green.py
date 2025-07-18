#!/usr/bin/env python3
"""
GREEN TEST: Verify the combat AttributeError bug is fixed
This test MUST PASS to confirm the bug is resolved
"""

import os
import sys
import unittest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_state import GameState


class TestCombatBugGreen(unittest.TestCase):
    """Test to verify the AttributeError fix works correctly"""

    def test_cleanup_defeated_enemies_handles_list_combatants(self):
        """
        GREEN TEST: This should PASS without errors

        Verifies that cleanup_defeated_enemies now handles list format
        """
        # Create a game state with the problematic structure
        game_state = GameState()

        # Set up combat state with combatants as a LIST
        game_state.combat_state = {
            "active": True,
            "combatants": [  # This is a LIST - previously caused bug
                {
                    "name": "Dragon",
                    "hp_current": 0,  # Defeated
                    "hp_max": 100,
                    "ac": 18,
                },
                {"name": "Player Character", "hp_current": 25, "hp_max": 30, "ac": 15},
            ],
            "initiative_order": [
                {"name": "Player Character", "initiative": 15, "type": "pc"},
                {"name": "Dragon", "initiative": 10, "type": "enemy"},
            ],
        }

        print("\n✅ GREEN TEST: Attempting to call cleanup_defeated_enemies()...")
        print("Expected: No errors, returns list of defeated enemies")

        # This should now work without raising AttributeError
        defeated = game_state.cleanup_defeated_enemies()

        # Verify it worked correctly
        self.assertIsInstance(defeated, list)
        self.assertIn("Dragon", defeated)
        print(f"✅ Successfully cleaned up defeated enemies: {defeated}")

        # Verify the combatants was normalized to dict format
        self.assertIsInstance(game_state.combat_state["combatants"], dict)
        self.assertNotIn("Dragon", game_state.combat_state["combatants"])
        self.assertIn("Player Character", game_state.combat_state["combatants"])
        print("✅ Combatants normalized to dict format and Dragon removed")

    def test_cleanup_defeated_enemies_preserves_dict_combatants(self):
        """
        Verify that dict format still works correctly (regression test)
        """
        game_state = GameState()

        # Set up combat state with combatants as a DICT (correct format)
        game_state.combat_state = {
            "active": True,
            "combatants": {  # This is a DICT - the expected format
                "Goblin": {
                    "hp_current": 0,  # Defeated
                    "hp_max": 7,
                    "ac": 15,
                },
                "Orc": {"hp_current": 5, "hp_max": 15, "ac": 13},
            },
            "initiative_order": [
                {"name": "Orc", "initiative": 12, "type": "enemy"},
                {"name": "Goblin", "initiative": 8, "type": "enemy"},
            ],
        }

        # This should work as before
        defeated = game_state.cleanup_defeated_enemies()

        # Verify it worked correctly
        self.assertIsInstance(defeated, list)
        self.assertIn("Goblin", defeated)
        self.assertNotIn("Orc", defeated)

        # Verify combatants remains a dict
        self.assertIsInstance(game_state.combat_state["combatants"], dict)
        self.assertNotIn("Goblin", game_state.combat_state["combatants"])
        self.assertIn("Orc", game_state.combat_state["combatants"])
        print("\n✅ Dict format still works correctly (no regression)")

    def test_cleanup_with_complex_list_structure(self):
        """
        Test with more complex list structure that AI might generate
        """
        game_state = GameState()

        # More complex structure with mixed HP values
        game_state.combat_state = {
            "active": True,
            "combatants": [
                {"name": "Bandit Leader", "hp_current": 0, "hp_max": 20},
                {"name": "Bandit 1", "hp_current": 0, "hp_max": 8},
                {"name": "Bandit 2", "hp_current": 3, "hp_max": 8},
                {"name": "Player", "hp_current": 15, "hp_max": 25},
            ],
            "initiative_order": [
                {"name": "Player", "initiative": 18, "type": "pc"},
                {"name": "Bandit Leader", "initiative": 14, "type": "enemy"},
                {"name": "Bandit 1", "initiative": 10, "type": "enemy"},
                {"name": "Bandit 2", "initiative": 8, "type": "enemy"},
            ],
        }

        defeated = game_state.cleanup_defeated_enemies()

        # Should clean up both defeated bandits
        self.assertEqual(len(defeated), 2)
        self.assertIn("Bandit Leader", defeated)
        self.assertIn("Bandit 1", defeated)
        self.assertNotIn("Bandit 2", defeated)
        self.assertNotIn("Player", defeated)

        # Verify remaining combatants
        remaining = game_state.combat_state["combatants"]
        self.assertEqual(len(remaining), 2)
        self.assertIn("Bandit 2", remaining)
        self.assertIn("Player", remaining)
        print("\n✅ Complex list structure handled correctly")


if __name__ == "__main__":
    print("=" * 70)
    print("🟢 RUNNING GREEN TEST - THIS SHOULD PASS!")
    print("If this test PASSES, the bug is fixed.")
    print("=" * 70)
    unittest.main(verbosity=2)
