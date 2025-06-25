#!/usr/bin/env python3
"""
Data Integrity Test Suite

Tests to catch data corruption bugs like NPCs being converted to strings,
state inconsistencies, and other data structure violations.
"""
import unittest
import sys
import os
import tempfile
import json
from unittest.mock import patch, MagicMock

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from game_state import GameState
# Import the functions we need for testing (avoid Firebase dependencies)
import collections.abc

def _validate_npc_data_integrity_test(npc_data: dict) -> list:
    """Test version of NPC validation that returns issues instead of logging."""
    issues = []
    for npc_id, npc_info in npc_data.items():
        if not isinstance(npc_info, dict):
            issues.append(f"NPC '{npc_id}' is {type(npc_info).__name__}, not dict: {npc_info}")
    return issues

def update_state_with_changes_test(state_to_update: dict, changes: dict) -> dict:
    """Test version of update_state_with_changes without Firebase dependencies."""
    for key, value in changes.items():
        # Handle __DELETE__ tokens
        if value == "__DELETE__":
            if key in state_to_update:
                del state_to_update[key]
            continue
        
        # Handle explicit append
        if isinstance(value, dict) and 'append' in value:
            if key not in state_to_update or not isinstance(state_to_update.get(key), list):
                state_to_update[key] = []
            if not isinstance(value['append'], list):
                state_to_update[key].append(value['append'])
            else:
                state_to_update[key].extend(value['append'])
        
        # Handle recursive merge
        elif isinstance(value, dict) and isinstance(state_to_update.get(key), collections.abc.Mapping):
            state_to_update[key] = update_state_with_changes_test(state_to_update.get(key, {}), value)
        
        # Create new dictionary when incoming value is dict but existing is not
        elif isinstance(value, dict):
            state_to_update[key] = update_state_with_changes_test({}, value)

        # Handle string updates to existing dictionaries (preserve dict structure)
        elif isinstance(state_to_update.get(key), collections.abc.Mapping):
            # Don't overwrite the entire dictionary with a string
            # Instead, treat string values as status updates
            existing_dict = state_to_update[key].copy()
            existing_dict['status'] = value
            state_to_update[key] = existing_dict
        
        # Simple overwrite
        else:
            state_to_update[key] = value
    
    return state_to_update

class TestDataIntegrity(unittest.TestCase):
    """Test suite for data integrity validation."""

    def setUp(self):
        """Set up test fixtures."""
        self.valid_npc_data = {
            "dragon_boss": {
                "name": "Ancient Red Dragon",
                "type": "enemy",
                "relationship": "hostile",
                "hp_current": 200,
                "hp_max": 200
            },
            "friendly_merchant": {
                "name": "Bob the Trader",
                "type": "ally", 
                "relationship": "friendly",
                "background": "Sells magical items"
            }
        }
        
        self.valid_missions = [
            "Find the lost crown",
            {
                "name": "Defeat the dragon",
                "description": "Slay the ancient red dragon",
                "objective": "Dragon must be defeated"
            }
        ]

    def test_npc_data_integrity_validation(self):
        """Test that NPC data validation catches corruption."""
        
        # Test with valid data - should return no issues
        issues = _validate_npc_data_integrity_test(self.valid_npc_data)
        self.assertEqual(len(issues), 0, f"Valid NPC data should have no issues: {issues}")
        
        # Test with corrupted data - should detect issues
        corrupted_npc_data = {
            "dragon_boss": "Ancient Red Dragon",  # String instead of dict!
            "friendly_merchant": self.valid_npc_data["friendly_merchant"]
        }
        
        issues = _validate_npc_data_integrity_test(corrupted_npc_data)
        self.assertGreater(len(issues), 0, "Corrupted NPC data should be detected")
        self.assertTrue(any("dragon_boss" in issue for issue in issues))

    def test_state_update_preserves_npc_structure(self):
        """Test that state updates don't corrupt NPC data structure."""
        initial_state = {
            "npc_data": self.valid_npc_data.copy(),
            "custom_campaign_state": {
                "active_missions": self.valid_missions.copy()
            }
        }
        
        # Simulate AI update that modifies NPCs
        changes = {
            "npc_data": {
                "dragon_boss": {
                    "hp_current": 150  # Dragon takes damage
                }
            }
        }
        
        updated_state = update_state_with_changes_test(initial_state, changes)
        
        # Verify NPC data is still dictionaries
        for npc_id, npc_data in updated_state["npc_data"].items():
            self.assertIsInstance(npc_data, dict, 
                f"NPC '{npc_id}' should be dict, got {type(npc_data)}: {npc_data}")
        
        # Verify specific NPC was updated correctly
        self.assertEqual(updated_state["npc_data"]["dragon_boss"]["hp_current"], 150)
        self.assertEqual(updated_state["npc_data"]["dragon_boss"]["name"], "Ancient Red Dragon")

    def test_delete_token_processing(self):
        """Test that __DELETE__ tokens work without corrupting other data."""
        initial_state = {
            "npc_data": self.valid_npc_data.copy(),
            "other_data": {"some_key": "some_value"}
        }
        
        # Delete one NPC
        changes = {
            "npc_data": {
                "dragon_boss": "__DELETE__"
            }
        }
        
        updated_state = update_state_with_changes_test(initial_state, changes)
        
        # Verify deletion worked
        self.assertNotIn("dragon_boss", updated_state["npc_data"])
        
        # Verify other NPC is still a dict
        self.assertIn("friendly_merchant", updated_state["npc_data"])
        self.assertIsInstance(updated_state["npc_data"]["friendly_merchant"], dict)
        
        # Verify other data unchanged
        self.assertEqual(updated_state["other_data"]["some_key"], "some_value")

    def test_mission_processing_doesnt_corrupt_npcs(self):
        """Test that mission processing safely handles different data types."""
        game_state = GameState(
            npc_data=self.valid_npc_data.copy(),
            custom_campaign_state={
                "active_missions": self.valid_missions.copy()
            }
        )
        
        # Verify NPCs are still dictionaries after GameState initialization
        for npc_id, npc_data in game_state.npc_data.items():
            self.assertIsInstance(npc_data, dict,
                f"NPC '{npc_id}' should be dict after GameState init, got {type(npc_data)}")

    def test_combat_cleanup_preserves_data_types(self):
        """Test that combat cleanup doesn't corrupt NPC data types."""
        game_state = GameState()
        
        # Set up combat with NPCs
        combatants_data = [
            {"name": "Player", "initiative": 15, "type": "pc", "hp_current": 25, "hp_max": 25},
            {"name": "Dragon Boss", "initiative": 12, "type": "enemy", "hp_current": 0, "hp_max": 200},  # Defeated
            {"name": "Friendly Wolf", "initiative": 8, "type": "ally", "hp_current": 8, "hp_max": 12}
        ]
        
        game_state.start_combat(combatants_data)
        
        # Add NPC data
        game_state.npc_data = {
            "Dragon Boss": {
                "name": "Ancient Red Dragon",
                "type": "enemy",
                "relationship": "hostile"
            },
            "Friendly Wolf": {
                "name": "Wolf Companion", 
                "type": "ally",
                "relationship": "companion"
            },
            "Village Merchant": {
                "name": "Bob the Trader",
                "type": "neutral",
                "relationship": "friendly"
            }
        }
        
        # Run cleanup
        defeated = game_state.cleanup_defeated_enemies()
        
        # Verify all remaining NPCs are still dictionaries
        for npc_id, npc_data in game_state.npc_data.items():
            self.assertIsInstance(npc_data, dict,
                f"NPC '{npc_id}' should be dict after cleanup, got {type(npc_data)}: {npc_data}")
        
        # Verify expected cleanup happened
        self.assertIn("Dragon Boss", defeated)
        self.assertNotIn("Dragon Boss", game_state.npc_data)
        self.assertIn("Friendly Wolf", game_state.npc_data)  # Ally should remain
        self.assertIn("Village Merchant", game_state.npc_data)  # Non-combat NPC should remain

    def test_mixed_mission_data_handling(self):
        """Test handling of missions that might contain mixed data types."""
        # This tests the scenario where NPCs might accidentally get into missions
        mixed_missions = [
            "Find the lost crown",  # String mission
            {
                "name": "Defeat the dragon",
                "description": "Slay the dragon"
            },  # Dict mission
            {
                "name": "Suspicious NPC-like entry",
                "relationship": "friendly",  # NPC-like field that shouldn't be in missions
                "background": "This looks like NPC data"
            }
        ]
        
        game_state = GameState(
            custom_campaign_state={"active_missions": mixed_missions},
            npc_data=self.valid_npc_data.copy()
        )
        
        # Verify NPCs are still dictionaries even with suspicious mission data
        for npc_id, npc_data in game_state.npc_data.items():
            self.assertIsInstance(npc_data, dict,
                f"NPC '{npc_id}' should be dict despite mixed mission data, got {type(npc_data)}")

    def test_state_consistency_after_multiple_updates(self):
        """Test that multiple state updates maintain data integrity."""
        initial_state = {
            "npc_data": self.valid_npc_data.copy(),
            "custom_campaign_state": {
                "active_missions": ["Find crown"],
                "core_memories": []
            }
        }
        
        # Simulate multiple AI updates
        updates = [
            {
                "npc_data": {
                    "dragon_boss": {"hp_current": 180}  # Dragon takes damage
                }
            },
            {
                "custom_campaign_state": {
                    "core_memories": {"append": "Dragon battle began"}
                }
            },
            {
                "npc_data": {
                    "new_ally": {
                        "name": "Wizard Helper",
                        "type": "ally",
                        "relationship": "friendly"
                    }
                }
            }
        ]
        
        current_state = initial_state
        for changes in updates:
            current_state = update_state_with_changes_test(current_state, changes)
            
            # After each update, verify NPC data integrity
            for npc_id, npc_data in current_state["npc_data"].items():
                self.assertIsInstance(npc_data, dict,
                    f"After update, NPC '{npc_id}' should be dict, got {type(npc_data)}: {npc_data}")

    def test_npc_string_update_preservation(self):
        """
        Test the specific bug where updating an NPC with a string value
        corrupts the entire NPC dictionary structure.
        
        This test ensures that string updates to NPCs are handled intelligently
        by preserving the dictionary structure and treating strings as status updates.
        """
        # Initial state with an NPC
        initial_state = {
            'npc_data': {
                'goblin_skirmisher_1': {
                    'hp_current': 7,
                    'hp_max': 7,
                    'ac': 13,
                    'status': 'active',
                    'alignment': 'chaotic evil'
                }
            }
        }
        
        # Update the NPC with a simple string (this used to cause corruption)
        string_update = {
            'npc_data': {
                'goblin_skirmisher_1': 'defeated'
            }
        }
        
        # Apply the update
        updated_state = update_state_with_changes_test(initial_state, string_update)
        
        # Verify the NPC data structure is preserved
        npc_data = updated_state['npc_data']['goblin_skirmisher_1']
        self.assertIsInstance(npc_data, dict, 
                            f"NPC data was corrupted! Expected dict but got {type(npc_data)}: {npc_data}")
        
        # Original data should be preserved
        self.assertEqual(npc_data.get('hp_current'), 7)
        self.assertEqual(npc_data.get('ac'), 13)
        self.assertEqual(npc_data.get('alignment'), 'chaotic evil')
        
        # String value should be intelligently merged as status
        self.assertEqual(npc_data.get('status'), 'defeated')
        
    def test_multiple_npc_string_updates_isolation(self):
        """
        Test that string updates to one NPC don't corrupt other NPCs.
        """
        initial_state = {
            'npc_data': {
                'goblin_1': {'hp': 7, 'status': 'active'},
                'goblin_2': {'hp': 5, 'status': 'active'}
            }
        }
        
        # Update just one NPC with a string
        changes = {
            'npc_data': {
                'goblin_1': 'defeated'
            }
        }
        
        final_state = update_state_with_changes_test(initial_state, changes)
        
        # Both NPCs should remain as dictionaries
        self.assertIsInstance(final_state['npc_data']['goblin_1'], dict)
        self.assertIsInstance(final_state['npc_data']['goblin_2'], dict)
        
        # goblin_2 should be completely unchanged
        self.assertEqual(final_state['npc_data']['goblin_2']['hp'], 5)
        self.assertEqual(final_state['npc_data']['goblin_2']['status'], 'active')
        
        # goblin_1 should have preserved hp but updated status
        self.assertEqual(final_state['npc_data']['goblin_1']['hp'], 7)
        self.assertEqual(final_state['npc_data']['goblin_1']['status'], 'defeated')

if __name__ == "__main__":
    # Set up logging to see corruption detection in action
    import logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    unittest.main()