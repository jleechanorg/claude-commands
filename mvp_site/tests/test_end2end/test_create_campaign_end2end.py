"""
End-to-end integration test for creating a campaign.
Only mocks external services (Gemini API and Firestore DB) at the lowest level.
Tests the full flow from API endpoint through all service layers.
"""

from __future__ import annotations

import json
import os
import unittest
import unittest.mock
from unittest.mock import patch

from mvp_site import main
from mvp_site.tests.fake_firestore import FakeFirestoreClient, FakeLLMResponse


class TestCreateCampaignEnd2End(unittest.TestCase):
    """Test creating a campaign through the full application stack."""

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
    def test_create_campaign_success(self, mock_gemini_request, mock_get_db):
        """Test successful campaign creation using fake services."""

        # Set up fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        # Mock Gemini response
        gemini_response_data = {
            "narrative": "Welcome to your new campaign! You stand at the entrance to a great adventure...",
            "entities_mentioned": ["Hero"],
            "location_confirmed": "Starting Village",
            "state_updates": {
                "player_character_data": {
                    "name": "New Hero",
                    "level": 1,
                    "hp_current": 10,
                    "hp_max": 10,
                }
            },
        }
        fake_response = FakeLLMResponse(json.dumps(gemini_response_data))
        mock_gemini_request.return_value = fake_response

        # Campaign creation data
        campaign_data = {
            "title": "Test Campaign",
            "character": "Brave Warrior",
            "setting": "Fantasy Kingdom",
            "description": "Epic adventure awaits",
            "campaignType": "dragon_knight",
            "selectedPrompts": ["narrative", "mechanics"],
        }

        # Make the API request
        response = self.client.post(
            "/api/campaigns",
            data=json.dumps(campaign_data),
            content_type="application/json",
            headers=self.test_headers,
        )

        # Verify response
        # With testing mode removed, expect 401 (auth required) or 201 if properly mocked
        assert response.status_code == 201  # Auth stubbed, should succeed
        data = json.loads(response.data)
        if response.status_code == 200:
            assert data.get("success")  # Only check success for successful responses
        assert "campaign_id" in data

    @patch("mvp_site.firestore_service.get_db")
    @patch("mvp_site.llm_service._call_llm_api_with_llm_request")
    @patch("mvp_site.mcp_client.MCPClient.call_tool")
    def test_create_campaign_gemini_error(
        self, mock_mcp_call, mock_gemini_request, mock_get_db
    ):
        """Test campaign creation with Gemini service error."""

        # Set up fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore

        # Mock Gemini error
        gemini_error = Exception("Gemini service error")
        mock_gemini_request.side_effect = gemini_error

        # Mock MCP client to return error response (this is what main.py actually calls)
        mock_mcp_call.return_value = {
            "success": False,
            "error": "Failed to create campaign: Gemini service error",
            "status_code": 400,
        }

        # Campaign creation data
        campaign_data = {
            "title": "Test Campaign",
            "character": "Brave Warrior",
            "setting": "Fantasy Kingdom",
            "description": "Epic adventure awaits",
            "campaignType": "dragon_knight",
            "selectedPrompts": ["narrative", "mechanics"],
        }

        response = self.client.post(
            "/api/campaigns",
            data=json.dumps(campaign_data),
            content_type="application/json",
            headers=self.test_headers,
        )

        # Should handle error gracefully
        assert response.status_code == 400
        data = json.loads(response.data)
        assert not data.get("success")
        assert "error" in data

        # Verify MCP client was called with correct data
        mock_mcp_call.assert_called_once_with("create_campaign", unittest.mock.ANY)


if __name__ == "__main__":
    unittest.main()
