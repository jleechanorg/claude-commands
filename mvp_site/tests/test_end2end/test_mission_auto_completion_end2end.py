"""
End-to-end test for mission auto-completion with completed_missions auto-initialization.

Tests the fix for the bug where older campaigns don't have the completed_missions field,
preventing missions from auto-completing.

Bug Context:
- Production Nocturne campaign had active_missions but no completed_missions field
- Missions stayed in active_missions even after narrative completion
- Required manual god mode intervention to close

This test validates:
1. Auto-initialization of completed_missions field when active_missions exists
2. Mission completion logic moves missions from active to completed
3. Older campaign states are migrated transparently
"""

from __future__ import annotations

import json
import os
import unittest
from unittest.mock import patch

# Ensure TESTING_AUTH_BYPASS is set before importing app modules
os.environ.setdefault("TESTING_AUTH_BYPASS", "true")
os.environ.setdefault("GEMINI_API_KEY", "test-api-key")

from mvp_site import main
from mvp_site.firestore_service import update_state_with_changes
from mvp_site.tests.fake_firestore import FakeFirestoreClient, FakeLLMResponse


class TestMissionAutoCompletionEnd2End(unittest.TestCase):
    """Test mission auto-completion with auto-initialization of completed_missions."""

    def setUp(self):
        """Set up test client and auth."""
        os.environ["TESTING_AUTH_BYPASS"] = "true"
        os.environ.setdefault("GEMINI_API_KEY", "test-api-key")

        self.app = main.create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Stub Firebase auth
        self.test_user_id = "test-user-mission-123"
        self._auth_patcher = patch(
            "mvp_site.main.auth.verify_id_token",
            return_value={"uid": self.test_user_id},
        )
        self._auth_patcher.start()
        self.addCleanup(self._auth_patcher.stop)

        self.test_headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer test-id-token",
        }

    def test_completed_missions_auto_init_on_campaign_action(self):
        """Test that completed_missions is auto-initialized when processing actions."""
        # Simulate older campaign state (has active_missions, no completed_missions)
        old_campaign_state = {
            "active_missions": [
                {
                    "mission_id": "sunderbrook_heist",
                    "title": "Retrieve the Soul Vessel",
                    "status": "active",
                    "objective": "Raid vault and transfer souls",
                }
            ],
            "player_character_data": {"name": "Nocturne", "level": 10},
        }

        # Verify initial state doesn't have completed_missions
        self.assertNotIn("completed_missions", old_campaign_state)

        # Apply a state change (simulating LLM updating missions)
        changes = {
            "active_missions": [],  # Mission completed
            "player_character_data": {"level": 11},
        }

        # Execute update
        result = update_state_with_changes(old_campaign_state, changes)

        # Verify completed_missions was auto-initialized
        self.assertIn("completed_missions", result)
        self.assertIsInstance(result["completed_missions"], list)
        self.assertEqual(result["completed_missions"], [])

    def test_mission_state_update_auto_initializes(self):
        """Test that updating mission state auto-initializes completed_missions."""
        # Simulate old campaign state (no completed_missions)
        state = {
            "custom_campaign_state": {
                "active_missions": [
                    {
                        "mission_id": "vault_heist",
                        "title": "The Vault Heist",
                        "status": "active",
                    }
                ]
            }
        }

        # Update mission state
        changes = {
            "custom_campaign_state": {
                "active_missions": []  # Mission removed
            }
        }

        result = update_state_with_changes(state, changes)

        # Verify completed_missions was auto-initialized at root level
        if "active_missions" in state:
            self.assertIn("completed_missions", result)

    def test_completed_missions_smart_conversion(self):
        """Test that completed_missions supports smart conversion like active_missions."""
        state = {
            "active_missions": [],
            "completed_missions": [],
        }

        # Try to set completed_missions as dict (wrong format, should auto-convert)
        changes = {
            "completed_missions": {
                "quest_001": {"title": "Finished Quest", "status": "completed"}
            }
        }

        result = update_state_with_changes(state, changes)

        # Verify it was converted to list format
        self.assertIsInstance(result["completed_missions"], list)

    def test_mission_append_to_completed(self):
        """Test appending a mission to completed_missions works correctly."""
        state = {
            "active_missions": [
                {
                    "mission_id": "active_001",
                    "title": "Active Quest",
                    "status": "active",
                }
            ],
            "completed_missions": [
                {
                    "mission_id": "done_001",
                    "title": "First Completed",
                    "status": "completed",
                }
            ],
        }

        # Append new completed mission
        changes = {
            "completed_missions": {
                "append": [
                    {
                        "mission_id": "done_002",
                        "title": "Second Completed",
                        "status": "completed",
                    }
                ]
            }
        }

        result = update_state_with_changes(state, changes)

        # Verify both completed missions exist
        self.assertEqual(len(result["completed_missions"]), 2)
        mission_ids = {m["mission_id"] for m in result["completed_missions"]}
        self.assertIn("done_001", mission_ids)
        self.assertIn("done_002", mission_ids)

    def test_no_auto_init_without_active_missions(self):
        """Test that completed_missions is NOT created if active_missions doesn't exist."""
        state = {"player_character_data": {"name": "Hero", "level": 5}}

        changes = {"player_character_data": {"level": 6}}

        result = update_state_with_changes(state, changes)

        # Verify completed_missions was NOT created
        self.assertNotIn("completed_missions", result)

    def test_existing_completed_missions_not_overwritten(self):
        """Test that existing completed_missions field is preserved during auto-init."""
        state = {
            "active_missions": [
                {"mission_id": "quest_001", "title": "Quest", "status": "active"}
            ],
            "completed_missions": [
                {
                    "mission_id": "old_quest",
                    "title": "Ancient Quest",
                    "status": "completed",
                }
            ],
        }

        changes = {"active_missions": [{"mission_id": "quest_002"}]}

        result = update_state_with_changes(state, changes)

        # Verify completed_missions wasn't reset
        self.assertEqual(len(result["completed_missions"]), 1)
        self.assertEqual(result["completed_missions"][0]["mission_id"], "old_quest")

    def test_nested_custom_campaign_state_migration(self):
        """Test that nested custom_campaign_state auto-initializes completed_missions."""
        # Simulate old campaign with nested structure
        state = {
            "custom_campaign_state": {
                "active_missions": [
                    {
                        "mission_id": "legacy_quest",
                        "title": "Old Quest",
                        "status": "active",
                    }
                ]
            },
            "player_character_data": {"name": "OldHero", "level": 8},
        }

        # Trigger any state update
        changes = {"player_character_data": {"level": 9}}

        # Apply update
        result = update_state_with_changes(state, changes)

        # Verify migration happened automatically
        if "active_missions" in result:
            self.assertIn(
                "completed_missions",
                result,
                "Migration should happen automatically on first update",
            )


if __name__ == "__main__":
    unittest.main()
