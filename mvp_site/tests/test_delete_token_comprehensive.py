#!/usr/bin/env python3
"""
Comprehensive test for __DELETE__ token processing in firestore_service.
Tests the actual implementation, not a simplified version.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock firebase_admin before importing firestore_service
sys.modules["firebase_admin"] = MagicMock()
sys.modules["firebase_admin.firestore"] = MagicMock()

from firestore_service import update_state_with_changes


class TestDeleteTokenProcessing(unittest.TestCase):
    """Test DELETE token handling in the actual update_state_with_changes function."""

    def setUp(self):
        """Set up test data."""
        # Mock logging to avoid clutter
        self.log_patcher = patch("firestore_service.logging_util")
        self.mock_logging = self.log_patcher.start()

    def tearDown(self):
        """Clean up."""
        self.log_patcher.stop()

    def test_nested_npc_deletion(self):
        """Test deleting NPCs from nested npc_data structure (most common case)."""
        state = {
            "npc_data": {
                "Drake 1": {"name": "Drake 1", "hp": 0, "status": "defeated"},
                "Drake 2": {"name": "Drake 2", "hp": 0, "status": "defeated"},
                "Lyra": {"name": "Lyra", "hp": 50, "status": "ally"},
            },
            "combat_active": True,
        }

        changes = {"npc_data": {"Drake 1": "__DELETE__", "Drake 2": "__DELETE__"}}

        result = update_state_with_changes(state, changes)

        # Verify defeated enemies are removed
        self.assertNotIn("Drake 1", result["npc_data"])
        self.assertNotIn("Drake 2", result["npc_data"])
        # Verify ally remains
        self.assertIn("Lyra", result["npc_data"])
        self.assertEqual(result["npc_data"]["Lyra"]["status"], "ally")
        # Verify other state unchanged
        self.assertTrue(result["combat_active"])

    def test_top_level_deletion(self):
        """Test deleting top-level keys."""
        state = {
            "temporary_effect": {"type": "buff", "duration": 0},
            "player_data": {"hp": 100},
            "world_data": {"location": "forest"},
        }

        changes = {"temporary_effect": "__DELETE__"}

        result = update_state_with_changes(state, changes)

        # Verify temporary effect is removed
        self.assertNotIn("temporary_effect", result)
        # Verify other data remains
        self.assertIn("player_data", result)
        self.assertIn("world_data", result)

    def test_delete_non_dict_value(self):
        """Test deleting keys that have non-dict values (strings, numbers, etc)."""
        state = {
            "counter": 5,
            "status_message": "In combat",
            "flags": ["combat_started", "boss_encountered"],
            "data": {"nested": "value"},
        }

        changes = {
            "counter": "__DELETE__",
            "status_message": "__DELETE__",
            "flags": "__DELETE__",
        }

        result = update_state_with_changes(state, changes)

        # DELETE token now properly handles all value types
        self.assertNotIn("counter", result, "Should delete numeric values")
        self.assertNotIn("status_message", result, "Should delete string values")
        self.assertNotIn("flags", result, "Should delete list values")
        self.assertIn("data", result, "Should preserve untouched data")

    def test_deeply_nested_deletion(self):
        """Test deletion in deeply nested structures."""
        state = {
            "world": {
                "regions": {
                    "forest": {
                        "npcs": {
                            "goblin1": {"hp": 0},
                            "goblin2": {"hp": 0},
                            "merchant": {"hp": 100},
                        }
                    }
                }
            }
        }

        changes = {
            "world": {
                "regions": {
                    "forest": {
                        "npcs": {"goblin1": "__DELETE__", "goblin2": "__DELETE__"}
                    }
                }
            }
        }

        result = update_state_with_changes(state, changes)

        # Verify goblins are removed
        forest_npcs = result["world"]["regions"]["forest"]["npcs"]
        self.assertNotIn("goblin1", forest_npcs)
        self.assertNotIn("goblin2", forest_npcs)
        # Verify merchant remains
        self.assertIn("merchant", forest_npcs)

    def test_mixed_updates_and_deletions(self):
        """Test mixing regular updates with deletions in same operation."""
        state = {
            "npc_data": {
                "enemy1": {"hp": 0, "status": "defeated"},
                "enemy2": {"hp": 30, "status": "active"},
                "ally1": {"hp": 50, "status": "ally"},
            },
            "combat_round": 5,
        }

        changes = {
            "npc_data": {
                "enemy1": "__DELETE__",  # Delete defeated enemy
                "enemy2": {"hp": 10, "status": "wounded"},  # Update active enemy
                "ally1": {"hp": 60},  # Heal ally
            },
            "combat_round": 6,
        }

        result = update_state_with_changes(state, changes)

        # Verify deletion
        self.assertNotIn("enemy1", result["npc_data"])
        # Verify updates
        self.assertEqual(result["npc_data"]["enemy2"]["hp"], 10)
        self.assertEqual(result["npc_data"]["enemy2"]["status"], "wounded")
        self.assertEqual(result["npc_data"]["ally1"]["hp"], 60)
        self.assertEqual(result["combat_round"], 6)


if __name__ == "__main__":
    unittest.main()
