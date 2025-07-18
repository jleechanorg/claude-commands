import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest

from firestore_service import update_state_with_changes


class TestNPCDataHandling(unittest.TestCase):
    """Test that the smart handling for npc_data prevents string corruption."""

    def test_ai_string_update_converts_to_status_field(self):
        """Test that AI's string updates to NPCs get converted to status field updates."""
        # Initial state with NPCs
        current_state = {
            "npc_data": {
                "Goblin_Leader": {
                    "name": "Grishnak",
                    "hp_current": 15,
                    "hp_max": 15,
                    "role": "Goblin Warband Leader",
                    "status": "hostile",
                },
                "Merchant_Tim": {
                    "name": "Timothy the Trader",
                    "role": "Traveling Merchant",
                    "status": "friendly",
                    "inventory": ["healing potions", "rope", "torches"],
                },
            }
        }

        # AI tries to update NPCs with string values (common mistake)
        ai_proposed_changes = {
            "npc_data": {
                "Goblin_Leader": "defeated",
                "Merchant_Tim": "grateful for rescue",
            }
        }

        # Apply the changes
        updated_state = update_state_with_changes(current_state, ai_proposed_changes)

        # Verify the NPCs are still dictionaries
        self.assertIsInstance(updated_state["npc_data"]["Goblin_Leader"], dict)
        self.assertIsInstance(updated_state["npc_data"]["Merchant_Tim"], dict)

        # Verify original data is preserved
        goblin = updated_state["npc_data"]["Goblin_Leader"]
        self.assertEqual(goblin["name"], "Grishnak")
        self.assertEqual(goblin["hp_current"], 15)
        self.assertEqual(goblin["role"], "Goblin Warband Leader")

        # Verify status was updated with the string value
        self.assertEqual(goblin["status"], "defeated")
        self.assertEqual(
            updated_state["npc_data"]["Merchant_Tim"]["status"], "grateful for rescue"
        )

    def test_ai_updates_specific_npc_fields(self):
        """Test that AI can update specific fields of an NPC normally."""
        # Initial state
        current_state = {
            "npc_data": {
                "Guard_Captain": {
                    "name": "Captain Marcus",
                    "hp_current": 45,
                    "hp_max": 45,
                    "status": "neutral",
                }
            }
        }

        # AI updates specific fields (correct way)
        ai_proposed_changes = {
            "npc_data": {
                "Guard_Captain": {"hp_current": 20, "status": "wounded but allied"}
            }
        }

        # Apply changes
        updated_state = update_state_with_changes(current_state, ai_proposed_changes)

        guard = updated_state["npc_data"]["Guard_Captain"]

        # Original fields preserved
        self.assertEqual(guard["name"], "Captain Marcus")
        self.assertEqual(guard["hp_max"], 45)

        # Updated fields changed
        self.assertEqual(guard["hp_current"], 20)
        self.assertEqual(guard["status"], "wounded but allied")

    def test_ai_delete_npc_with_delete_token(self):
        """Test that AI can properly delete an NPC using __DELETE__ token."""
        # Initial state
        current_state = {
            "npc_data": {
                "Bandit_1": {"name": "Bandit Thug", "hp_current": 0, "status": "dead"},
                "Bandit_2": {
                    "name": "Bandit Archer",
                    "hp_current": 10,
                    "status": "fleeing",
                },
            }
        }

        # AI deletes dead NPC
        ai_proposed_changes = {"npc_data": {"Bandit_1": "__DELETE__"}}

        # Apply changes
        updated_state = update_state_with_changes(current_state, ai_proposed_changes)

        # Verify NPC was deleted
        self.assertNotIn("Bandit_1", updated_state["npc_data"])

        # Verify other NPC remains
        self.assertIn("Bandit_2", updated_state["npc_data"])
        self.assertEqual(updated_state["npc_data"]["Bandit_2"]["name"], "Bandit Archer")

    def test_ai_creates_new_npc_correctly(self):
        """Test that AI can create a new NPC with proper dictionary structure."""
        # Initial state
        current_state = {"npc_data": {}}

        # AI creates new NPC
        ai_proposed_changes = {
            "npc_data": {
                "Mysterious_Stranger": {
                    "name": "Hooded Figure",
                    "status": "watching from shadows",
                    "role": "Unknown",
                    "first_seen": "tavern",
                }
            }
        }

        # Apply changes
        updated_state = update_state_with_changes(current_state, ai_proposed_changes)

        # Verify NPC was created correctly
        self.assertIn("Mysterious_Stranger", updated_state["npc_data"])
        stranger = updated_state["npc_data"]["Mysterious_Stranger"]
        self.assertEqual(stranger["name"], "Hooded Figure")
        self.assertEqual(stranger["status"], "watching from shadows")

    def test_mixed_updates_in_single_change(self):
        """Test handling mixed updates - some NPCs get strings, others get dicts."""
        # Initial state
        current_state = {
            "npc_data": {
                "Enemy_1": {"name": "Orc Warrior", "hp_current": 30},
                "Enemy_2": {"name": "Orc Shaman", "hp_current": 20},
                "Ally_1": {"name": "Sir Galahad", "hp_current": 50},
            }
        }

        # AI sends mixed updates
        ai_proposed_changes = {
            "npc_data": {
                "Enemy_1": "slain in battle",  # String update
                "Enemy_2": {"hp_current": 5, "status": "badly wounded"},  # Dict update
                "Ally_1": {"hp_current": 45},  # Dict update
            }
        }

        # Apply changes
        updated_state = update_state_with_changes(current_state, ai_proposed_changes)

        # Check Enemy_1 - should have string converted to status
        enemy1 = updated_state["npc_data"]["Enemy_1"]
        self.assertIsInstance(enemy1, dict)
        self.assertEqual(enemy1["name"], "Orc Warrior")
        self.assertEqual(enemy1["status"], "slain in battle")

        # Check Enemy_2 - should have normal dict merge
        enemy2 = updated_state["npc_data"]["Enemy_2"]
        self.assertEqual(enemy2["hp_current"], 5)
        self.assertEqual(enemy2["status"], "badly wounded")

        # Check Ally_1 - should have normal update
        ally1 = updated_state["npc_data"]["Ally_1"]
        self.assertEqual(ally1["hp_current"], 45)


if __name__ == "__main__":
    unittest.main()
