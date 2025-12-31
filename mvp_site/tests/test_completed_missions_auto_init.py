"""Test completed_missions auto-initialization for older campaigns.

This test validates the fix for the bug where older campaigns don't have
the completed_missions field, preventing mission auto-completion.

Bug Context:
- Production Nocturne campaign had active_missions but no completed_missions
- Missions couldn't auto-complete because there was nowhere to move them
- Required manual god mode intervention
"""

import unittest
from unittest.mock import MagicMock, patch

from mvp_site.firestore_service import update_state_with_changes


class TestCompletedMissionsAutoInit(unittest.TestCase):
    """Test auto-initialization of completed_missions field."""

    def test_auto_init_when_active_missions_exists_but_completed_doesnt(self):
        """Test that completed_missions is auto-created when active_missions is updated."""
        # Simulate an older campaign state (has active_missions, no completed_missions)
        state = {
            "active_missions": [
                {
                    "mission_id": "old_quest_001",
                    "title": "Ancient Quest",
                    "status": "active",
                }
            ]
        }

        # Verify initial state
        self.assertIn("active_missions", state)
        self.assertNotIn("completed_missions", state)

        # Apply a change to active_missions
        changes = {
            "active_missions": [
                {
                    "mission_id": "new_quest_001",
                    "title": "New Quest",
                    "status": "active",
                }
            ]
        }

        # Execute
        result = update_state_with_changes(state, changes)

        # Verify completed_missions was auto-initialized
        self.assertIn("completed_missions", result)
        self.assertIsInstance(result["completed_missions"], list)
        self.assertEqual(result["completed_missions"], [])

    def test_auto_init_when_state_has_active_missions_at_start(self):
        """Test that completed_missions is auto-created at function start."""
        # Simulate older campaign
        state = {
            "active_missions": [
                {"mission_id": "quest_001", "title": "Quest", "status": "active"}
            ],
            "player_character_data": {"name": "Hero", "level": 5},
        }

        # Apply unrelated change
        changes = {"player_character_data": {"level": 6}}

        # Execute
        result = update_state_with_changes(state, changes)

        # Verify completed_missions was auto-initialized even though
        # we didn't directly update active_missions
        self.assertIn("completed_missions", result)
        self.assertEqual(result["completed_missions"], [])

    def test_no_auto_init_when_completed_missions_already_exists(self):
        """Test that existing completed_missions field is not overwritten."""
        state = {
            "active_missions": [
                {"mission_id": "quest_001", "title": "Quest", "status": "active"}
            ],
            "completed_missions": [
                {
                    "mission_id": "old_quest",
                    "title": "Finished Quest",
                    "status": "completed",
                }
            ],
        }

        # Apply change
        changes = {"active_missions": [{"mission_id": "quest_002"}]}

        # Execute
        result = update_state_with_changes(state, changes)

        # Verify completed_missions wasn't reset
        self.assertEqual(len(result["completed_missions"]), 1)
        self.assertEqual(result["completed_missions"][0]["mission_id"], "old_quest")

    def test_no_auto_init_when_no_active_missions_field(self):
        """Test that completed_missions is not created if active_missions doesn't exist."""
        state = {"player_character_data": {"name": "Hero", "level": 5}}

        # Apply change
        changes = {"player_character_data": {"level": 6}}

        # Execute
        result = update_state_with_changes(state, changes)

        # Verify completed_missions was NOT created
        self.assertNotIn("completed_missions", result)

    def test_completed_missions_smart_conversion(self):
        """Test that completed_missions supports smart conversion like active_missions."""
        state = {
            "active_missions": [],
            "completed_missions": [],
        }

        # Try to set completed_missions as dict (wrong format)
        changes = {
            "completed_missions": {
                "quest_001": {
                    "title": "Finished Quest",
                    "status": "completed",
                }
            }
        }

        # Execute (should auto-convert)
        result = update_state_with_changes(state, changes)

        # Verify it was converted to list format
        self.assertIsInstance(result["completed_missions"], list)
        if result["completed_missions"]:
            self.assertEqual(result["completed_missions"][0]["mission_id"], "quest_001")

    def test_append_syntax_works_for_completed_missions(self):
        """Test that append syntax works correctly for completed_missions."""
        state = {
            "active_missions": [],
            "completed_missions": [
                {
                    "mission_id": "quest_001",
                    "title": "First Quest",
                    "status": "completed",
                }
            ],
        }

        # Append new completed mission
        changes = {
            "completed_missions": {
                "append": [
                    {
                        "mission_id": "quest_002",
                        "title": "Second Quest",
                        "status": "completed",
                    }
                ]
            }
        }

        # Execute
        result = update_state_with_changes(state, changes)

        # Verify both missions exist
        self.assertEqual(len(result["completed_missions"]), 2)
        mission_ids = [m["mission_id"] for m in result["completed_missions"]]
        self.assertIn("quest_001", mission_ids)
        self.assertIn("quest_002", mission_ids)

    def test_auto_init_with_dict_active_missions_smart_conversion(self):
        """Test auto-init works when active_missions arrives as dict (smart conversion path).

        Regression test for bug where smart conversion's continue statement
        skipped the auto-init block.
        """
        # Simulate old campaign (no completed_missions)
        state = {
            "player_character_data": {"name": "Hero", "level": 5}
            # NOTE: No active_missions or completed_missions
        }

        # LLM sends active_missions as dict (wrong format, triggers smart conversion)
        changes = {
            "active_missions": {
                "quest_001": {
                    "title": "New Quest",
                    "status": "active",
                    "objective": "Complete the mission",
                }
            }
        }

        # Execute
        result = update_state_with_changes(state, changes)

        # CRITICAL: completed_missions must be auto-initialized
        # even though active_missions went through smart conversion
        self.assertIn("completed_missions", result,
                     "Auto-init must work even with dict active_missions (smart conversion)")
        self.assertIsInstance(result["completed_missions"], list)
        self.assertEqual(result["completed_missions"], [])


if __name__ == "__main__":
    unittest.main()
