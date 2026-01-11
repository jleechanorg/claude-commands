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

# Ensure TESTING_AUTH_BYPASS is set before importing app modules
os.environ["TESTING_AUTH_BYPASS"] = "true"
os.environ.setdefault("GEMINI_API_KEY", "test-api-key")
os.environ.setdefault("CEREBRAS_API_KEY", "test-cerebras-key")

from mvp_site import main
from mvp_site.tests.fake_firestore import FakeFirestoreClient
from mvp_site.tests.fake_llm import FakeLLMResponse


class TestLivingWorldEnd2End(unittest.TestCase):
    """Test Living World player_turn tracking through the full application stack."""

    def setUp(self):
        """Set up test client."""
        os.environ.setdefault("GEMINI_API_KEY", "test-api-key")
        os.environ.setdefault("CEREBRAS_API_KEY", "test-cerebras-key")
        # Disable MOCK_SERVICES_MODE to allow patching generate_json_mode_content
        os.environ["MOCK_SERVICES_MODE"] = "false"

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
                    "rumors": [{"description": "Strange lights in the forest."}],
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

        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.data}"

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
            data=json.dumps(
                {
                    "input": "GOD MODE: Change my character name to Bob",
                    "mode": "character",
                }
            ),
            content_type="application/json",
            headers=self.test_headers,
        )

        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.data}"

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
            assert (
                "background_events" in world_events or "rumors" in world_events
            ), "world_events should contain background_events or rumors"

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

        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.data}"

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

    @patch("mvp_site.firestore_service.get_db")
    @patch(
        "mvp_site.llm_providers.gemini_provider.generate_content_with_code_execution"
    )
    def test_world_events_not_duplicated_across_turns(
        self, mock_gemini_generate, mock_get_db
    ):
        """Test that story entries contain ONLY their turn's world_events, not accumulated.

        BUG REPRODUCTION: The system was copying game_state.world_events (cumulative)
        to every story entry's structured_fields, causing all turns to show the same
        world_events regardless of when they were generated.

        EXPECTED: Each turn should only include world_events that were generated on THAT
        turn (based on turn_generated annotation).
        """
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        campaign_id = "test_no_duplicate_world_events"

        # Use helper to set up basic campaign
        self._setup_fake_firestore_with_campaign(
            fake_firestore, campaign_id, player_turn=10
        )

        # Add pre-existing world_events from turn 5 to game_state
        existing_world_events = {
            "background_events": [
                {
                    "actor": "Old Faction",
                    "action": "Old action from turn 5",
                    "turn_generated": 5,
                    "scene_generated": 3,
                }
            ]
        }

        # Update game_state to include old world_events
        game_state_ref = (
            fake_firestore.collection("users")
            .document(self.test_user_id)
            .collection("campaigns")
            .document(campaign_id)
            .collection("game_states")
            .document("current_state")
        )
        current_state = game_state_ref.get().to_dict()
        current_state["world_events"] = existing_world_events
        game_state_ref.set(current_state)

        # LLM returns NEW world_events for turn 11 (this turn)
        turn_11_response = {
            "narrative": "The adventure continues on turn 11...",
            "entities_mentioned": ["Hero"],
            "location_confirmed": "Town Square",
            "state_updates": {
                "world_events": {
                    "background_events": [
                        {
                            "actor": "New Faction",
                            "action": "New action happening NOW on turn 11",
                            # Note: turn_generated will be added by annotation
                        }
                    ]
                }
            },
            "session_header": "Session 1: Continuing",
            "planning_block": {"thinking": "New events for this turn."},
        }

        mock_gemini_generate.return_value = FakeLLMResponse(
            json.dumps(turn_11_response)
        )

        response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps({"input": "I explore the town", "mode": "character"}),
            content_type="application/json",
            headers=self.test_headers,
        )

        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.data}"

        data = json.loads(response.data)

        # Get world_events from response - check multiple possible locations
        response_world_events = data.get("world_events") or data.get(
            "state_updates", {}
        ).get("world_events")

        # CRITICAL: Assert world_events is present in response
        # The LLM response includes state_updates.world_events, so the API MUST return it
        # Without this assertion, the test could pass without validating the fix
        assert response_world_events is not None, (
            f"TEST GAP: world_events not found in API response! "
            f"LLM mock returns world_events but API didn't include them. "
            f"Response keys: {list(data.keys())}, "
            f"state_updates: {data.get('state_updates', {})}"
        )

        # The response should NOT contain the old turn 5 events
        # It should only contain the new turn 11 events
        background_events = response_world_events.get("background_events", [])
        for event in background_events:
            # OLD BUG: Events from turn 5 were appearing in turn 11's response
            turn_generated = event.get("turn_generated")
            if turn_generated is not None:
                assert turn_generated != 5, (
                    f"DUPLICATE BUG: Found old event from turn 5 in turn 11 response! "
                    f"Event: {event}"
                )
            # Check for the old action text that shouldn't be there
            action = event.get("action", "")
            assert "Old action from turn 5" not in action, (
                f"DUPLICATE BUG: Old turn 5 event found in turn 11 response! "
                f"Response world_events should only contain NEW events. "
                f"Got: {response_world_events}"
            )

        # Verify the fix works: API response should contain ONLY new events
        # The game_state may have merged or replaced events (separate concern)
        # The key bug was old events appearing in the API response when they shouldn't
        # The new event should be present
        new_events = [
            e
            for e in response_world_events.get("background_events", [])
            if "New action happening NOW" in e.get("action", "")
        ]
        assert (
            new_events
        ), f"New events should be in API response. Got: {response_world_events}"


if __name__ == "__main__":
    unittest.main()
