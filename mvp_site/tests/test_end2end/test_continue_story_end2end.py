"""
End-to-end integration test for continuing a story.
Only mocks external services (Gemini API and Firestore DB) at the lowest level.
Tests the full flow from API endpoint through all service layers.
"""

from __future__ import annotations

import json
import os
import unittest
from unittest.mock import patch

from mvp_site import main
from mvp_site.tests.fake_firestore import FakeFirestoreClient
from mvp_site.tests.fake_llm import FakeLLMResponse


class TestContinueStoryEnd2End(unittest.TestCase):
    """Test continuing a story through the full application stack."""

    def setUp(self):
        """Set up test client."""
        os.environ["TESTING"] = "true"
        os.environ.setdefault("GEMINI_API_KEY", "test-api-key")

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

    @patch("mvp_site.firestore_service.get_db")
    @patch("mvp_site.llm_service._call_llm_api_with_llm_request")
    def test_continue_story_success(self, mock_gemini_request, mock_get_db):
        """Test successful story continuation using fake services."""

        # Set up fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        # Create test campaign data
        campaign_id = "test_campaign_123"
        fake_firestore.collection("users").document("test-user-123").collection(
            "campaigns"
        ).document(campaign_id).set(
            {"title": "Test Campaign", "setting": "Fantasy realm"}
        )

        # Create game state
        fake_firestore.collection("users").document("test-user-123").collection(
            "campaigns"
        ).document(campaign_id).collection("game_states").document("current_state").set(
            {
                "user_id": "test-user-123",
                "story_text": "Previous story content",
                "characters": ["Thorin"],
                "locations": ["Mountain Kingdom"],
                "items": ["Magic Sword"],
            }
        )

        # Mock Gemini response
        gemini_response_data = {
            "narrative": "The story continues with new adventures...",
            "entities_mentioned": ["Thorin"],
            "location_confirmed": "Mountain Kingdom",
            "state_updates": {"story_progression": "continued"},
        }
        mock_gemini_request.return_value = FakeLLMResponse(
            json.dumps(gemini_response_data)
        )

        # Make the API request to the correct interaction endpoint
        response = self.client.post(
            f"/api/campaigns/{campaign_id}/interaction",
            data=json.dumps({"input": "continue the adventure", "mode": "character"}),
            content_type="application/json",
            headers=self.test_headers,
        )

        # Verify response - with auth stubbed, should get 200
        assert response.status_code == 200
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
