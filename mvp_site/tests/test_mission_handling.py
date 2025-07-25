import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import unittest

from firestore_service import update_state_with_changes


class TestMissionHandling(unittest.TestCase):
    """Test that the smart conversion for active_missions works correctly."""

    def test_ai_dict_format_converts_to_list_append(self):
        """Test that AI's dictionary format for missions gets converted to list append."""
        # Initial state with one existing mission
        current_state = {
            "custom_campaign_state": {
                "active_missions": [
                    {
                        "mission_id": "rescue_merchant",
                        "title": "Rescue the Merchant",
                        "status": "in_progress",
                        "objective": "Find the kidnapped merchant",
                    }
                ]
            }
        }

        # AI tries to add missions using dictionary format (common mistake)
        ai_proposed_changes = {
            "custom_campaign_state": {
                "active_missions": {
                    "main_quest_1": {
                        "title": "Defeat the Dark Lord",
                        "status": "accepted",
                        "objective": "Travel to the Dark Tower",
                    },
                    "side_quest_1": {
                        "title": "Collect Herbs",
                        "status": "accepted",
                        "objective": "Gather 10 healing herbs",
                    },
                }
            }
        }

        # Apply the changes
        updated_state = update_state_with_changes(current_state, ai_proposed_changes)

        # Verify the result
        missions = updated_state["custom_campaign_state"]["active_missions"]

        # Should still be a list
        self.assertIsInstance(missions, list)

        # Should have 3 missions now (1 original + 2 new)
        self.assertEqual(len(missions), 3)

        # Check that mission_ids were auto-generated
        mission_ids = [m.get("mission_id") for m in missions]
        self.assertIn("rescue_merchant", mission_ids)
        self.assertIn("main_quest_1", mission_ids)
        self.assertIn("side_quest_1", mission_ids)

        # Verify the new missions have correct data
        main_quest = next(m for m in missions if m.get("mission_id") == "main_quest_1")
        self.assertEqual(main_quest["title"], "Defeat the Dark Lord")
        self.assertEqual(main_quest["status"], "accepted")

    def test_updating_existing_mission_by_id(self):
        """Test that providing a mission with existing ID updates rather than duplicates."""
        # Initial state
        current_state = {
            "custom_campaign_state": {
                "active_missions": [
                    {
                        "mission_id": "main_quest_1",
                        "title": "Defeat the Dark Lord",
                        "status": "accepted",
                        "objective": "Travel to the Dark Tower",
                    }
                ]
            }
        }

        # AI updates the mission status
        ai_proposed_changes = {
            "custom_campaign_state": {
                "active_missions": {
                    "main_quest_1": {
                        "status": "in_progress",
                        "objective": "Fight through the tower guards",
                    }
                }
            }
        }

        # Apply changes
        updated_state = update_state_with_changes(current_state, ai_proposed_changes)

        missions = updated_state["custom_campaign_state"]["active_missions"]

        # Should still have just 1 mission
        self.assertEqual(len(missions), 1)

        # Mission should be updated
        mission = missions[0]
        self.assertEqual(mission["mission_id"], "main_quest_1")
        self.assertEqual(mission["title"], "Defeat the Dark Lord")  # Title preserved
        self.assertEqual(mission["status"], "in_progress")  # Status updated
        self.assertEqual(
            mission["objective"], "Fight through the tower guards"
        )  # Objective updated

    def test_ai_provides_list_format_works_normally(self):
        """Test that if AI provides correct list format, it works without conversion."""
        current_state = {"custom_campaign_state": {"active_missions": []}}

        # AI provides correct list format
        ai_proposed_changes = {
            "custom_campaign_state": {
                "active_missions": [
                    {
                        "mission_id": "tutorial_1",
                        "title": "Learn the Basics",
                        "status": "completed",
                    }
                ]
            }
        }

        # Apply changes
        updated_state = update_state_with_changes(current_state, ai_proposed_changes)

        missions = updated_state["custom_campaign_state"]["active_missions"]

        # Should work normally as a list replacement
        self.assertEqual(len(missions), 1)
        self.assertEqual(missions[0]["mission_id"], "tutorial_1")


if __name__ == "__main__":
    unittest.main()
