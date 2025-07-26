import os
import sys

# Add parent directory to path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import unittest

import logging_util

from firestore_service import update_state_with_changes


class TestMissionConversionHelpers(unittest.TestCase):
    """Test all branches of the mission conversion logic with comprehensive coverage."""

    def setUp(self):
        """Set up logging to capture conversion messages."""
        self.log_messages = []
        self.handler = logging_util.StreamHandler()
        self.handler.emit = lambda record: self.log_messages.append(record.getMessage())
        logging_util.getLogger().addHandler(self.handler)
        logging_util.getLogger().setLevel(logging_util.INFO)

    def tearDown(self):
        """Clean up logging handler."""
        logging_util.getLogger().removeHandler(self.handler)

    def test_missions_dict_with_valid_mission_data(self):
        """Test converting dict with valid mission objects."""
        current_state = {"custom_campaign_state": {"active_missions": []}}
        changes = {
            "custom_campaign_state": {
                "active_missions": {
                    "quest_1": {
                        "title": "Find the Sword",
                        "status": "active",
                        "objective": "Search the cave",
                    },
                    "quest_2": {"title": "Rescue the Prince", "status": "pending"},
                }
            }
        }

        result = update_state_with_changes(current_state, changes)
        missions = result["custom_campaign_state"]["active_missions"]

        # Should convert to list with 2 missions
        self.assertIsInstance(missions, list)
        self.assertEqual(len(missions), 2)

        # Check mission_ids were auto-generated
        mission_ids = [m.get("mission_id") for m in missions]
        self.assertIn("quest_1", mission_ids)
        self.assertIn("quest_2", mission_ids)

        # Check logging
        self.assertTrue(any("SMART CONVERSION" in msg for msg in self.log_messages))
        self.assertTrue(
            any("Adding new mission: quest_1" in msg for msg in self.log_messages)
        )

    def test_missions_dict_with_existing_mission_update(self):
        """Test updating existing mission when mission_id matches."""
        current_state = {
            "custom_campaign_state": {
                "active_missions": [
                    {
                        "mission_id": "quest_1",
                        "title": "Find the Sword",
                        "status": "active",
                        "progress": 50,
                    }
                ]
            }
        }

        changes = {
            "custom_campaign_state": {
                "active_missions": {"quest_1": {"status": "completed", "progress": 100}}
            }
        }

        result = update_state_with_changes(current_state, changes)
        missions = result["custom_campaign_state"]["active_missions"]

        # Should still have 1 mission (updated, not duplicated)
        self.assertEqual(len(missions), 1)

        mission = missions[0]
        self.assertEqual(mission["mission_id"], "quest_1")
        self.assertEqual(mission["title"], "Find the Sword")  # Preserved
        self.assertEqual(mission["status"], "completed")  # Updated
        self.assertEqual(mission["progress"], 100)  # Updated

        # Check logging
        self.assertTrue(
            any(
                "Updating existing mission: quest_1" in msg for msg in self.log_messages
            )
        )

    def test_missions_dict_with_invalid_mission_data(self):
        """Test handling invalid mission data (non-dict values)."""
        current_state = {"custom_campaign_state": {"active_missions": []}}
        changes = {
            "custom_campaign_state": {
                "active_missions": {
                    "quest_1": {"title": "Valid Quest"},
                    "quest_2": "invalid string data",
                    "quest_3": 123,
                    "quest_4": None,
                }
            }
        }

        result = update_state_with_changes(current_state, changes)
        missions = result["custom_campaign_state"]["active_missions"]

        # Should only have 1 valid mission
        self.assertEqual(len(missions), 1)
        self.assertEqual(missions[0]["mission_id"], "quest_1")

        # Check warning logs for invalid data
        warning_messages = [
            msg for msg in self.log_messages if "Skipping invalid mission data" in msg
        ]
        self.assertEqual(len(warning_messages), 3)  # For quest_2, quest_3, quest_4

    def test_missions_dict_with_existing_mission_id_in_data(self):
        """Test that existing mission_id in data is preserved."""
        current_state = {"custom_campaign_state": {"active_missions": []}}
        changes = {
            "custom_campaign_state": {
                "active_missions": {
                    "quest_key": {
                        "mission_id": "custom_id",  # Different from key
                        "title": "Custom Mission",
                    }
                }
            }
        }

        result = update_state_with_changes(current_state, changes)
        missions = result["custom_campaign_state"]["active_missions"]

        # Should preserve the custom mission_id, not use the key
        self.assertEqual(missions[0]["mission_id"], "custom_id")
        self.assertEqual(missions[0]["title"], "Custom Mission")

    def test_missions_non_dict_non_list_value(self):
        """Test handling non-dict, non-list values for active_missions."""
        current_state = {"custom_campaign_state": {"active_missions": []}}
        changes = {"custom_campaign_state": {"active_missions": "invalid string"}}

        result = update_state_with_changes(current_state, changes)
        missions = result["custom_campaign_state"]["active_missions"]

        # Should preserve original empty list
        self.assertIsInstance(missions, list)
        self.assertEqual(len(missions), 0)

        # Check error logging
        self.assertTrue(
            any(
                "Cannot convert str to mission list" in msg for msg in self.log_messages
            )
        )

    def test_missions_initialization_when_missing(self):
        """Test that active_missions is initialized when missing."""
        current_state = {"custom_campaign_state": {}}  # No active_missions
        changes = {
            "custom_campaign_state": {
                "active_missions": {"quest_1": {"title": "New Quest"}}
            }
        }

        result = update_state_with_changes(current_state, changes)
        missions = result["custom_campaign_state"]["active_missions"]

        # Should initialize as list and add mission
        self.assertIsInstance(missions, list)
        self.assertEqual(len(missions), 1)
        self.assertEqual(missions[0]["mission_id"], "quest_1")

    def test_missions_initialization_when_wrong_type(self):
        """Test that active_missions is reinitialized when wrong type."""
        current_state = {
            "custom_campaign_state": {
                "active_missions": "wrong type"  # Should be list
            }
        }
        changes = {
            "custom_campaign_state": {
                "active_missions": {"quest_1": {"title": "New Quest"}}
            }
        }

        result = update_state_with_changes(current_state, changes)
        missions = result["custom_campaign_state"]["active_missions"]

        # Should reinitialize as list and add mission
        self.assertIsInstance(missions, list)
        self.assertEqual(len(missions), 1)
        self.assertEqual(missions[0]["mission_id"], "quest_1")

    def test_mixed_valid_and_invalid_missions(self):
        """Test handling mix of valid and invalid mission data."""
        current_state = {"custom_campaign_state": {"active_missions": []}}
        changes = {
            "custom_campaign_state": {
                "active_missions": {
                    "valid_1": {"title": "Valid Quest 1"},
                    "invalid_1": "string",
                    "valid_2": {"title": "Valid Quest 2"},
                    "invalid_2": 42,
                    "valid_3": {"title": "Valid Quest 3"},
                }
            }
        }

        result = update_state_with_changes(current_state, changes)
        missions = result["custom_campaign_state"]["active_missions"]

        # Should have 3 valid missions, 2 invalid skipped
        self.assertEqual(len(missions), 3)

        titles = [m["title"] for m in missions]
        self.assertIn("Valid Quest 1", titles)
        self.assertIn("Valid Quest 2", titles)
        self.assertIn("Valid Quest 3", titles)

        # Should have 2 warning messages for invalid data
        warning_messages = [
            msg for msg in self.log_messages if "Skipping invalid mission data" in msg
        ]
        self.assertEqual(len(warning_messages), 2)

    def test_update_mission_preserves_other_fields(self):
        """Test that updating mission preserves fields not in the update."""
        current_state = {
            "custom_campaign_state": {
                "active_missions": [
                    {
                        "mission_id": "quest_1",
                        "title": "Original Title",
                        "status": "active",
                        "progress": 25,
                        "rewards": ["gold", "xp"],
                        "notes": "Important quest",
                    }
                ]
            }
        }

        changes = {
            "custom_campaign_state": {
                "active_missions": {"quest_1": {"status": "completed", "progress": 100}}
            }
        }

        result = update_state_with_changes(current_state, changes)
        mission = result["custom_campaign_state"]["active_missions"][0]

        # Updated fields
        self.assertEqual(mission["status"], "completed")
        self.assertEqual(mission["progress"], 100)

        # Preserved fields
        self.assertEqual(mission["title"], "Original Title")
        self.assertEqual(mission["rewards"], ["gold", "xp"])
        self.assertEqual(mission["notes"], "Important quest")


if __name__ == "__main__":
    unittest.main()
