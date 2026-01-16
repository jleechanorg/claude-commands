"""
End-to-end test for game_state persistence (core_memories, world_events).

Tests LW-uz5: Verify that core_memories and world_events are persisted to Firestore
so Living World updates can access critical plot facts even after story truncation.
"""

from __future__ import annotations

import os
import unittest
from unittest.mock import Mock, patch

# Ensure TESTING_AUTH_BYPASS is set before importing app modules
os.environ["TESTING_AUTH_BYPASS"] = "true"
os.environ.setdefault("GEMINI_API_KEY", "test-api-key")
os.environ.setdefault("CEREBRAS_API_KEY", "test-cerebras-key")

from mvp_site import world_logic
from mvp_site.llm_response import LLMResponse
from mvp_site.tests.fake_firestore import FakeFirestoreClient


class TestGameStatePersistenceEnd2End(unittest.TestCase):
    """Test that core_memories and world_events persist to Firestore."""

    def setUp(self):
        """Set up test environment."""
        os.environ.setdefault("GEMINI_API_KEY", "test-api-key")
        os.environ.setdefault("CEREBRAS_API_KEY", "test-cerebras-key")
        os.environ["MOCK_SERVICES_MODE"] = "false"

        self.test_user_id = "test-user-persistence"
        self.test_campaign_id = "test-campaign-persistence"

    @patch("mvp_site.firestore_service.get_db")
    @patch("mvp_site.llm_service.continue_story")
    def test_core_memories_persisted_to_firestore(
        self, mock_continue_story, mock_get_db
    ):
        """Test that core_memories are persisted to game_states/current_state."""
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        # Set up initial game state with core_memories
        initial_game_state = {
            "user_id": self.test_user_id,
            "player_character_data": {"name": "Hero", "level": 5},
            "core_memories": {
                "captured_npc": "Horgus",
                "important_event": "Defeated the dragon",
            },
            "world_events": {
                "background_events": [
                    {"description": "Merchants arrive from the east"}
                ],
                "rumors": [{"description": "Strange lights in the forest"}],
            },
            "custom_campaign_state": {},
        }

        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(self.test_campaign_id).set({"title": "Test Campaign"})

        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(self.test_campaign_id).collection("game_states").document(
            "current_state"
        ).set(initial_game_state)

        # Create real LLMResponse object (not a mock to avoid deepcopy recursion)
        llm_response = LLMResponse(
            narrative_text="The adventure continues...",
            structured_response=None,
            agent_mode="character",
        )
        # Mock get_state_updates method
        llm_response.get_state_updates = Mock(
            return_value={"player_character_data": {"hp": 50}}
        )
        mock_continue_story.return_value = llm_response

        # Process an action
        request_data = {
            "user_id": self.test_user_id,
            "campaign_id": self.test_campaign_id,
            "user_input": "I explore the forest",  # Note: user_input not input
            "mode": "character",
        }

        import asyncio

        result = asyncio.run(world_logic.process_action_unified(request_data))

        # Verify core_memories persisted
        persisted_state = (
            fake_firestore.collection("users")
            .document(self.test_user_id)
            .collection("campaigns")
            .document(self.test_campaign_id)
            .collection("game_states")
            .document("current_state")
            .get()
        )

        self.assertIsNotNone(persisted_state, "Game state should be persisted")
        persisted_data = persisted_state.to_dict() if persisted_state else {}

        self.assertIn(
            "core_memories",
            persisted_data,
            "core_memories should be persisted to Firestore",
        )
        self.assertEqual(
            persisted_data["core_memories"],
            initial_game_state["core_memories"],
            "core_memories should match original values",
        )

    @patch("mvp_site.firestore_service.get_db")
    @patch("mvp_site.llm_service.continue_story")
    def test_world_events_persisted_to_firestore(
        self, mock_continue_story, mock_get_db
    ):
        """Test that world_events are persisted to game_states/current_state."""
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        # Set up initial game state with world_events
        initial_game_state = {
            "user_id": self.test_user_id,
            "player_character_data": {"name": "Hero", "level": 5},
            "world_events": {
                "background_events": [
                    {"description": "Merchants arrive from the east"}
                ],
                "rumors": [{"description": "Strange lights in the forest"}],
                "faction_updates": {"guild": {"status": "allied"}},
            },
            "custom_campaign_state": {},
        }

        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(self.test_campaign_id).set({"title": "Test Campaign"})

        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(self.test_campaign_id).collection("game_states").document(
            "current_state"
        ).set(initial_game_state)

        # Create real LLMResponse object (not a mock to avoid deepcopy recursion)
        llm_response = LLMResponse(
            narrative_text="The adventure continues...",
            structured_response=None,
            agent_mode="character",
        )
        # Mock get_state_updates method
        llm_response.get_state_updates = Mock(
            return_value={"player_character_data": {"hp": 50}}
        )
        mock_continue_story.return_value = llm_response

        # Process an action
        request_data = {
            "user_id": self.test_user_id,
            "campaign_id": self.test_campaign_id,
            "user_input": "I explore the forest",  # Note: user_input not input
            "mode": "character",
        }

        import asyncio

        result = asyncio.run(world_logic.process_action_unified(request_data))

        # Verify world_events persisted
        persisted_state = (
            fake_firestore.collection("users")
            .document(self.test_user_id)
            .collection("campaigns")
            .document(self.test_campaign_id)
            .collection("game_states")
            .document("current_state")
            .get()
        )

        self.assertIsNotNone(persisted_state, "Game state should be persisted")
        persisted_data = persisted_state.to_dict() if persisted_state else {}

        self.assertIn(
            "world_events",
            persisted_data,
            "world_events should be persisted to Firestore",
        )
        self.assertIn(
            "background_events",
            persisted_data["world_events"],
            "world_events.background_events should be persisted",
        )
        self.assertIn(
            "rumors",
            persisted_data["world_events"],
            "world_events.rumors should be persisted",
        )

    @patch("mvp_site.firestore_service.get_db")
    @patch("mvp_site.llm_service.continue_story")
    def test_story_entry_includes_game_state_fields(
        self, mock_continue_story, mock_get_db
    ):
        """Test that story entries include core_memories and world_events for traceability."""
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        # Set up initial game state with core_memories and world_events
        initial_game_state = {
            "user_id": self.test_user_id,
            "player_character_data": {"name": "Hero", "level": 5},
            "core_memories": {
                "captured_npc": "Horgus",
                "important_event": "Defeated the dragon",
            },
            "world_events": {
                "background_events": [
                    {"description": "Merchants arrive from the east"}
                ],
                "rumors": [{"description": "Strange lights in the forest"}],
            },
            "custom_campaign_state": {},
        }

        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(self.test_campaign_id).set({"title": "Test Campaign"})

        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(self.test_campaign_id).collection("game_states").document(
            "current_state"
        ).set(initial_game_state)

        # Create real LLMResponse object (not a mock to avoid deepcopy recursion)
        llm_response = LLMResponse(
            narrative_text="The adventure continues...",
            structured_response=None,
            agent_mode="character",
        )
        # Mock get_state_updates method
        llm_response.get_state_updates = Mock(
            return_value={"player_character_data": {"hp": 50}}
        )
        mock_continue_story.return_value = llm_response

        # Process an action
        request_data = {
            "user_id": self.test_user_id,
            "campaign_id": self.test_campaign_id,
            "user_input": "I explore the forest",  # Note: user_input not input
            "mode": "character",
        }

        import asyncio

        result = asyncio.run(world_logic.process_action_unified(request_data))

        # Verify the action was processed successfully
        self.assertIn("success", result, "Action should return success status")
        if not result.get("success"):
            self.fail(f"Action failed: {result.get('error', 'Unknown error')}")

        # Verify story entry includes game_state fields
        campaign_doc = (
            fake_firestore.collection("users")
            .document(self.test_user_id)
            .collection("campaigns")
            .document(self.test_campaign_id)
            .get()
        )
        self.assertIsNotNone(campaign_doc, "Campaign document should exist")

        story_collection = campaign_doc.collection("story")
        story_entries = story_collection.stream()

        # Find the AI response entry (actor == "gemini")
        ai_entry = None
        all_entries = []
        for entry in story_entries:
            entry_data = entry.to_dict() if hasattr(entry, "to_dict") else {}
            all_entries.append(entry_data)
            if entry_data.get("actor") == "gemini":
                ai_entry = entry_data
                break

        self.assertIsNotNone(
            ai_entry,
            f"AI story entry should exist. Found entries: {[e.get('actor') for e in all_entries]}",
        )

        # Check if story entry includes game_state fields
        # NOTE: This test will FAIL initially, proving the bug exists
        # After fix, story entries should include core_memories and world_events
        self.assertIn(
            "core_memories",
            ai_entry,
            "Story entry should include core_memories for traceability",
        )
        self.assertIn(
            "world_events",
            ai_entry,
            "Story entry should include world_events for traceability",
        )


if __name__ == "__main__":
    unittest.main()
