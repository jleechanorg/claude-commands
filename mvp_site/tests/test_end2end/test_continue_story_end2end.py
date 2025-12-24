"""
End-to-end integration test for continuing a story.
Only mocks external services (LLM provider APIs and Firestore DB) at the lowest level.
Tests the full flow from API endpoint through all service layers including context compaction.
"""

from __future__ import annotations

import json
import os
import unittest
from unittest.mock import patch

# Ensure TESTING is set before importing app modules (world_logic applies clock-skew patch at import time).
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("GEMINI_API_KEY", "test-api-key")
os.environ.setdefault("CEREBRAS_API_KEY", "test-cerebras-key")

from mvp_site import main
from mvp_site.tests.fake_firestore import FakeFirestoreClient
from mvp_site.tests.fake_llm import FakeLLMResponse


class TestContinueStoryEnd2End(unittest.TestCase):
    """Test continuing a story through the full application stack."""

    def setUp(self):
        """Set up test client."""
        os.environ["TESTING"] = "true"
        os.environ.setdefault("GEMINI_API_KEY", "test-api-key")
        os.environ.setdefault("CEREBRAS_API_KEY", "test-cerebras-key")

        self.app = main.create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Use a stable test UID and stub Firebase verification
        self.test_user_id = "test-user-123"
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

        # Standard mock LLM response (used for all providers)
        self.mock_llm_response_data = {
            "narrative": "The story continues with new adventures...",
            "entities_mentioned": ["Thorin"],
            "location_confirmed": "Mountain Kingdom",
            "state_updates": {"story_progression": "continued"},
            "session_header": "Session 1: The Mountain Path",
            "planning_block": {
                "thinking": "The player wants to continue. I should describe the next leg of the journey.",
                "choices": {
                    "press_on": {"text": "Press On", "description": "Continue deeper into the mountains", "risk_level": "medium"},
                    "set_camp": {"text": "Set Camp", "description": "Rest for the night", "risk_level": "low"}
                }
            }
        }

    def _setup_fake_firestore_with_campaign(self, fake_firestore, campaign_id):
        """Helper to set up fake Firestore with campaign and game state."""
        # Create test campaign data
        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(campaign_id).set(
            {"title": "Test Campaign", "setting": "Fantasy realm"}
        )

        # Create game state with proper structure including combat_state
        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(campaign_id).collection("game_states").document("current_state").set(
            {
                "user_id": self.test_user_id,
                "story_text": "Previous story content",
                "characters": ["Thorin"],
                "locations": ["Mountain Kingdom"],
                "items": ["Magic Sword"],
                "combat_state": {"in_combat": False},
                "custom_campaign_state": {},
            }
        )

    @patch("mvp_site.firestore_service.get_db")
    @patch("mvp_site.llm_providers.gemini_provider.generate_content_with_code_execution")
    def test_continue_story_success_without_dice_rolls(
        self, mock_gemini_generate, mock_get_db
    ):
        """Test successful story continuation without dice rolls through full stack."""

        # Set up fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        campaign_id = "test_campaign_123"
        self._setup_fake_firestore_with_campaign(fake_firestore, campaign_id)

        # Mock Gemini native two-phase provider (default)
        mock_gemini_generate.return_value = FakeLLMResponse(
            json.dumps(self.mock_llm_response_data)
        )

        # Make the API request to the correct interaction endpoint
        response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps({"input": "continue the adventure", "mode": "character"}),
            content_type="application/json",
            headers=self.test_headers,
        )

        # Verify response - with auth stubbed, should get 200
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.data}"
        data = json.loads(response.data)

        # Verify story data structure
        assert "story" in data
        assert isinstance(data["story"], list)
        assert len(data["story"]) > 0

        # Verify it contains the narrative from our mock
        found_narrative = any(
            "The story continues with new adventures..." in entry.get("text", "")
            for entry in data["story"]
        )
        assert found_narrative, "Expected narrative not found in response"

        # Verify Gemini (default provider) was called at least once
        assert (
            mock_gemini_generate.call_count >= 1
        ), "Gemini native two-phase provider should be invoked as the default"

    @patch("mvp_site.firestore_service.get_db")
    @patch("mvp_site.llm_providers.gemini_provider.generate_content_with_code_execution")
    def test_time_anomaly_includes_dice_retry_notice(
        self, mock_gemini_generate, mock_get_db
    ):
        """Temporal anomaly warning should mention dice retry when reprompt occurs."""
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        campaign_id = "test_campaign_time_anomaly"
        self._setup_fake_firestore_with_campaign(fake_firestore, campaign_id)

        # Set a known world_time in current game state
        old_world_time = {"year": 1000, "month": 1, "day": 10, "hour": 10, "minute": 0, "second": 0}
        fake_firestore.collection("users").document(self.test_user_id).collection(
            "campaigns"
        ).document(campaign_id).collection("game_states").document("current_state").set(
            {
                "user_id": self.test_user_id,
                "story_text": "Previous story content",
                "characters": ["Thorin"],
                "locations": ["Mountain Kingdom"],
                "items": ["Magic Sword"],
                "combat_state": {"in_combat": False},
                "custom_campaign_state": {},
                "world_data": {"world_time": old_world_time, "current_location_name": "Bridge"},
            }
        )

        # First response: missing dice_rolls (forces reprompt due to combat input)
        first_response = {
            "narrative": "You swing at the goblin.",
            "entities_mentioned": ["Goblin"],
            "location_confirmed": "Bridge",
            "session_header": "Session 1: The Bridge",
            "planning_block": {
                "thinking": "Combat requires a roll.",
                "choices": {},
            },
            "dice_rolls": [],
            "dice_audit_events": [],
            "state_updates": {"world_data": {"world_time": old_world_time}},
        }

        # Second response: includes dice_rolls but moves time backward
        backward_world_time = {"year": 999, "month": 1, "day": 9, "hour": 10, "minute": 0, "second": 0}
        second_response = {
            "narrative": "Your blade strikes true.",
            "entities_mentioned": ["Goblin"],
            "location_confirmed": "Bridge",
            "session_header": "Session 1: The Bridge",
            "planning_block": {
                "thinking": "Resolve the hit.",
                "choices": {},
            },
            "dice_rolls": ["Attack: 1d20+5 = 10+5 = 15 vs AC 12 (Hit)"],
            "dice_audit_events": [],
            "state_updates": {"world_data": {"world_time": backward_world_time}},
        }

        second_fake_response = FakeLLMResponse(json.dumps(second_response))
        # Provide code_execution evidence to satisfy Gemini code-exec dice integrity checks.
        # Must include actual random.randint() call to pass RNG verification.
        second_fake_response.parts[0].executable_code = type(
            "ExecutableCode",
            (),
            {
                "language": "python",
                "code": "import random; roll = random.randint(1, 20); print(roll)",
            },
        )()

        mock_gemini_generate.side_effect = [
            FakeLLMResponse(json.dumps(first_response)),
            second_fake_response,
        ]

        response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps({"input": "I attack the goblin", "mode": "character"}),
            content_type="application/json",
            headers=self.test_headers,
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.data}"
        data = json.loads(response.data)

        god_mode_response = data.get("god_mode_response", "")
        assert "TEMPORAL ANOMALY DETECTED" in god_mode_response, (
            f"Expected temporal anomaly warning, got: {god_mode_response}"
        )
        assert "Dice Retry Notice" in god_mode_response, (
            "Expected dice retry notice to appear under temporal anomaly warning"
        )
        assert mock_gemini_generate.call_count == 2, (
            "Reprompt should trigger a second LLM call for dice retry"
        )

    @patch("mvp_site.firestore_service.get_db")
    def test_continue_story_campaign_not_found(self, mock_get_db):
        """Test continuing story with non-existent campaign."""

        # Set up empty fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        response = self.client.post(
            "/api/campaigns/nonexistent_campaign/interaction",
            data=json.dumps({"input": "continue", "mode": "character"}),
            content_type="application/json",
            headers=self.test_headers,
        )

        # With auth in place, should get 404 for missing campaign
        assert response.status_code == 404
        data = json.loads(response.data)
        assert "error" in data


if __name__ == "__main__":
    unittest.main()
