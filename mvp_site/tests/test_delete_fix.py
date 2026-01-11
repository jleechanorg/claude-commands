#!/usr/bin/env python3
"""
Test to verify __DELETE__ token processing works correctly.
"""
import os
import sys
import unittest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from mvp_site.firestore_service import update_state_with_changes

class TestDeleteTokenProcessing(unittest.TestCase):
    """Test that __DELETE__ tokens work correctly."""

    def test_delete_token_processing(self):
        """Test that __DELETE__ tokens work correctly."""
        # Test 1: Simple deletion
        state = {
            "npc_data": {
                "Drake 1": {"name": "Drake 1", "type": "enemy"},
                "Drake 2": {"name": "Drake 2", "type": "enemy"},
                "Friendly NPC": {"name": "Friend", "type": "ally"},
            },
            "other_data": "should remain",
        }

        changes = {"npc_data": {"Drake 1": "__DELETE__", "Drake 2": "__DELETE__"}}

        updated_state = update_state_with_changes(state, changes)

        # Verify Drake 1 and Drake 2 are gone, but Friendly NPC remains
        self.assertNotIn(
            "Drake 1", updated_state["npc_data"], "Drake 1 should be deleted"
        )
        self.assertNotIn(
            "Drake 2", updated_state["npc_data"], "Drake 2 should be deleted"
        )
        self.assertIn(
            "Friendly NPC", updated_state["npc_data"], "Friendly NPC should remain"
        )
        self.assertEqual(
            updated_state["other_data"],
            "should remain",
            "Other data should be unchanged",
        )

        # Test 2: Top-level deletion
        state2 = {
            "defeated_enemy": {"name": "Orc", "hp": 0},
            "alive_ally": {"name": "Ranger", "hp": 50},
            "world_data": {"location": "forest"},
        }

        changes2 = {"defeated_enemy": "__DELETE__"}

        updated_state2 = update_state_with_changes(state2, changes2)

        self.assertNotIn("defeated_enemy", updated_state2, "defeated_enemy should be deleted")
        self.assertIn("alive_ally", updated_state2, "alive_ally should remain")
        self.assertIn("world_data", updated_state2, "world_data should remain")

if __name__ == "__main__":
    unittest.main()
