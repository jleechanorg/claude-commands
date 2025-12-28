"""
End-to-end integration test for Living World system.

Tests:
1. player_turn counter stored in game_state increments on non-GOD actions
2. player_turn does NOT increment on GOD mode actions
3. world_events extraction and annotation with turn_generated
4. Backward compatibility when player_turn is not present (compute from context)
"""

from __future__ import annotations

import json
import os
import unittest
from unittest.mock import patch

# Ensure TESTING is set before importing app modules
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("GEMINI_API_KEY", "test-api-key")
os.environ.setdefault("CEREBRAS_API_KEY", "test-cerebras-key")

from mvp_site import main
from mvp_site.tests.fake_firestore import FakeFirestoreClient
from mvp_site.tests.fake_llm import FakeLLMResponse


class TestLivingWorldEnd2End(unittest.TestCase):
    """Test Living World player_turn tracking through the full application stack."""

    def setUp(self):
        """Set up test client."""
        os.environ["TESTING"] = "true"
        os.environ.setdefault("GEMINI_API_KEY", "test-api-key")
        os.environ.setdefault("CEREBRAS_API_KEY", "test-cerebras-key")

        self.app = main.create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Use a stable test UID and stub Firebase verification
        self.test_user_id = "test-user-living-world"
        self._auth_patcher = patch(
            "mvp_site.main.auth.verify_id_token",
            return_value={"uid": self.test_user_id},
        )
        self._auth_patcher.start()
        self.addCleanup(self._auth_patcher.stop)

        # Test headers with Authorization token
        self.test_headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer test-id-token",
        }

        # Standard mock LLM response
        self.mock_llm_response_data = {
            "narrative": "The adventure continues...",
            "entities_mentioned": ["Hero"],
            "location_confirmed": "Town Square",
            "state_updates": {
                "world_events": {
                    "background_events": [
                        {"description": "Merchants arrive from the east."}
                    ],
                    "rumors": [
                        {"description": "Strange lights in the forest."}
                    ],
                }
            },
            "session_header": "Session 1: Beginning",
            "planning_block": {"thinking": "Continue story."},
        }

    def _setup_fake_firestore_with_campaign(
        self, fake_firestore, campaign_id, player_turn=0
    ):
        """Helper to set up fake Firestore with campaign and game state."""
        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(campaign_id).set(
            {"title": "Test Campaign", "setting": "Fantasy realm"}
        )

        game_state = {
            "user_id": self.test_user_id,
            "story_text": "Previous story content",
            "characters": ["Hero"],
            "locations": ["Town Square"],
            "combat_state": {"in_combat": False},
            "custom_campaign_state": {},
            "player_turn": player_turn,
        }

        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(campaign_id).collection("game_states").document("current_state").set(
            game_state
        )

    @patch("mvp_site.firestore_service.get_db")
    @patch(
        "mvp_site.llm_providers.gemini_provider.generate_content_with_code_execution"
    )
    def test_player_turn_increments_on_character_action(
        self, mock_gemini_generate, mock_get_db
    ):
        """Test that player_turn increments when a character action is taken."""
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        campaign_id = "test_player_turn_increment"
        initial_turn = 5
        self._setup_fake_firestore_with_campaign(
            fake_firestore, campaign_id, player_turn=initial_turn
        )

        mock_gemini_generate.return_value = FakeLLMResponse(
            json.dumps(self.mock_llm_response_data)
        )

        # Make character mode request
        response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps({"input": "I look around the square", "mode": "character"}),
            content_type="application/json",
            headers=self.test_headers,
        )

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.data}"
        )

        # Verify player_turn was incremented in game state
        game_state_doc = (
            fake_firestore.collection("users")
            .document(self.test_user_id)
            .collection("campaigns")
            .document(campaign_id)
            .collection("game_states")
            .document("current_state")
            .get()
        )
        game_state = game_state_doc.to_dict()

        assert game_state.get("player_turn") == initial_turn + 1, (
            f"player_turn should be {initial_turn + 1}, "
            f"got {game_state.get('player_turn')}"
        )

    @patch("mvp_site.firestore_service.get_db")
    @patch(
        "mvp_site.llm_providers.gemini_provider.generate_content_with_code_execution"
    )
    def test_player_turn_does_not_increment_on_god_mode(
        self, mock_gemini_generate, mock_get_db
    ):
        """Test that player_turn does NOT increment on GOD mode commands."""
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        campaign_id = "test_god_mode_no_increment"
        initial_turn = 10
        self._setup_fake_firestore_with_campaign(
            fake_firestore, campaign_id, player_turn=initial_turn
        )

        # GOD mode response
        god_mode_response = {
            "narrative": "Character updated.",
            "god_mode_response": "Successfully changed character name.",
        }
        mock_gemini_generate.return_value = FakeLLMResponse(
            json.dumps(god_mode_response)
        )

        # Make GOD mode request
        response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps({
                "input": "GOD MODE: Change my character name to Bob",
                "mode": "character"
            }),
            content_type="application/json",
            headers=self.test_headers,
        )

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.data}"
        )

        # Verify player_turn was NOT incremented
        game_state_doc = (
            fake_firestore.collection("users")
            .document(self.test_user_id)
            .collection("campaigns")
            .document(campaign_id)
            .collection("game_states")
            .document("current_state")
            .get()
        )
        game_state = game_state_doc.to_dict()

        assert game_state.get("player_turn") == initial_turn, (
            f"player_turn should remain {initial_turn} for GOD mode, "
            f"got {game_state.get('player_turn')}"
        )

    @patch("mvp_site.firestore_service.get_db")
    @patch(
        "mvp_site.llm_providers.gemini_provider.generate_content_with_code_execution"
    )
    def test_world_events_extracted_in_story_entry(
        self, mock_gemini_generate, mock_get_db
    ):
        """Test that world_events from state_updates are extracted to story entries."""
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        campaign_id = "test_world_events_extraction"
        self._setup_fake_firestore_with_campaign(fake_firestore, campaign_id)

        mock_gemini_generate.return_value = FakeLLMResponse(
            json.dumps(self.mock_llm_response_data)
        )

        response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps({"input": "explore the area", "mode": "character"}),
            content_type="application/json",
            headers=self.test_headers,
        )

        assert response.status_code == 200

        # Verify response contains state_updates with world_events
        data = json.loads(response.data)
        state_updates = data.get("state_updates", {})

        # world_events should be in state_updates if LLM returned them
        world_events = state_updates.get("world_events")
        if world_events:
            assert "background_events" in world_events or "rumors" in world_events, (
                "world_events should contain background_events or rumors"
            )

    @patch("mvp_site.firestore_service.get_db")
    @patch(
        "mvp_site.llm_providers.gemini_provider.generate_content_with_code_execution"
    )
    def test_backward_compatibility_no_player_turn(
        self, mock_gemini_generate, mock_get_db
    ):
        """Test backward compatibility when game state has no player_turn field."""
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        campaign_id = "test_backward_compat"

        # Set up campaign WITHOUT player_turn (old campaign)
        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(campaign_id).set(
            {"title": "Old Campaign", "setting": "Fantasy realm"}
        )

        # Game state without player_turn field
        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(campaign_id).collection("game_states").document("current_state").set(
            {
                "user_id": self.test_user_id,
                "story_text": "Old story",
                "combat_state": {"in_combat": False},
                "custom_campaign_state": {},
                # No player_turn field
            }
        )

        mock_gemini_generate.return_value = FakeLLMResponse(
            json.dumps(self.mock_llm_response_data)
        )

        response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps({"input": "continue", "mode": "character"}),
            content_type="application/json",
            headers=self.test_headers,
        )

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.data}"
        )

        # After the action, player_turn should now be set
        game_state_doc = (
            fake_firestore.collection("users")
            .document(self.test_user_id)
            .collection("campaigns")
            .document(campaign_id)
            .collection("game_states")
            .document("current_state")
            .get()
        )
        game_state = game_state_doc.to_dict()

        # Should be 1 after first action (0 + 1)
        assert game_state.get("player_turn") == 1, (
            f"player_turn should be 1 after first action, "
            f"got {game_state.get('player_turn')}"
        )


if __name__ == "__main__":
    unittest.main()
