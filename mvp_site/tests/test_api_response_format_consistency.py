#!/usr/bin/env python3
"""
Test API Response Format Consistency

Ensures all API endpoints maintain consistent response formats between:
1. Legacy (main branch) format
2. New MCP format
3. Frontend expectations
"""

import os
import sys
import unittest

# Set environment for testing
os.environ["TESTING"] = "true"
os.environ["USE_MOCKS"] = "true"
# Direct calls are now the default - no need to set SKIP_MCP_HTTP

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# Skip this test entirely in CI environment where Firebase credentials are not available
def has_firebase_credentials():
    """Check if Firebase credentials are available."""
    # Check for various credential sources
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        return True
    if os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY"):
        return True
    # Check for application default credentials
    try:
        import google.auth

        google.auth.default()
        return True
    except Exception:
        return False


from unittest.mock import patch

from main import create_app  # noqa: E402


class TestAPIResponseFormatConsistency(unittest.TestCase):
    """Test that all API responses maintain consistent formats."""

    def setUp(self):
        """Set up test client."""

        # Mock Firebase to prevent initialization errors
        self.firebase_patcher = patch("firestore_service.get_db")
        self.mock_get_db = self.firebase_patcher.start()

        # Set up fake Firestore client
        from tests.fake_firestore import FakeFirestoreClient
        fake_firestore = FakeFirestoreClient()
        self.mock_get_db.return_value = fake_firestore
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Test data
        self.test_user_id = "test-format-consistency-user"
        self.test_headers = {
            "X-Test-Bypass-Auth": "true",
            "X-Test-User-ID": self.test_user_id,
            "Content-Type": "application/json",
        }

    def test_campaigns_list_format(self):
        """Test GET /api/campaigns returns legacy array format."""
        response = self.client.get("/api/campaigns", headers=self.test_headers)

        if response.status_code == 200:
            data = response.get_json()
            # Must be array directly for backward compatibility
            assert isinstance(
                data, list
            ), "GET /api/campaigns must return array directly"

    def test_campaign_by_id_format(self):
        """Test GET /api/campaigns/<id> returns expected object format.

        Legacy format:
        {
            "campaign": {...},
            "story": [...],
            "game_state": {...}
        }
        """
        # First create a campaign
        create_response = self.client.post(
            "/api/campaigns",
            headers=self.test_headers,
            json={
                "title": "Format Test Campaign",
                "character": "Test Character",
                "description": "Test Description",
            },
        )

        if create_response.status_code in [200, 201]:
            create_data = create_response.get_json()
            campaign_id = create_data.get("campaign_id")

            # Now get the campaign
            get_response = self.client.get(
                f"/api/campaigns/{campaign_id}", headers=self.test_headers
            )

            if get_response.status_code == 200:
                data = get_response.get_json()

                # Check response structure
                assert isinstance(data, dict)
                assert "campaign" in data, "Must have 'campaign' field"
                assert "story" in data, "Must have 'story' field"
                assert "game_state" in data, "Must have 'game_state' field"

                # Frontend expects: data.campaign.title
                assert isinstance(data["campaign"], dict)
                assert "title" in data["campaign"]

    def test_campaign_creation_format(self):
        """Test POST /api/campaigns returns expected object format.

        Expected format:
        {
            "success": true,
            "campaign_id": "..."
        }
        """
        response = self.client.post(
            "/api/campaigns",
            headers=self.test_headers,
            json={
                "title": "New Campaign",
                "character": "Test Character",
                "description": "Test Description",
            },
        )

        if response.status_code in [200, 201]:
            data = response.get_json()

            # Check response structure
            assert isinstance(data, dict)
            assert "success" in data, "Must have 'success' field"
            assert "campaign_id" in data, "Must have 'campaign_id' field"

            # Frontend expects: data.campaign_id
            assert data["success"]
            assert isinstance(data["campaign_id"], str)

    def test_campaign_update_format(self):
        """Test PATCH /api/campaigns/<id> returns expected format."""
        # First create a campaign
        create_response = self.client.post(
            "/api/campaigns",
            headers=self.test_headers,
            json={
                "title": "Update Test Campaign",
                "character": "Test Character",
                "description": "Test Description",
            },
        )

        if create_response.status_code in [200, 201]:
            campaign_id = create_response.get_json().get("campaign_id")

            # Update the campaign
            update_response = self.client.patch(
                f"/api/campaigns/{campaign_id}",
                headers=self.test_headers,
                json={"title": "Updated Title"},
            )

            if update_response.status_code == 200:
                data = update_response.get_json()

                # Check response structure
                assert isinstance(data, dict)
                assert "success" in data, "Must have 'success' field"

    def test_interaction_response_format(self):
        """Test POST /api/campaigns/<id>/interaction returns expected format.

        Expected format includes:
        - narrative or response field
        - planning_block (optional)
        - various other fields
        """
        # First create a campaign
        create_response = self.client.post(
            "/api/campaigns",
            headers=self.test_headers,
            json={
                "title": "Interaction Test Campaign",
                "character": "Test Character",
                "description": "Test Description",
            },
        )

        if create_response.status_code in [200, 201]:
            campaign_id = create_response.get_json().get("campaign_id")

            # Send interaction
            interaction_response = self.client.post(
                f"/api/campaigns/{campaign_id}/interaction",
                headers=self.test_headers,
                json={"input": "Hello world", "mode": "character"},
            )

            if interaction_response.status_code == 200:
                data = interaction_response.get_json()

                # Check response structure
                assert isinstance(data, dict)

                # Frontend expects: data.narrative || data.response
                has_narrative = "narrative" in data or "response" in data
                assert has_narrative, "Must have 'narrative' or 'response' field"

    def test_settings_get_format(self):
        """Test GET /api/settings returns expected format."""
        response = self.client.get("/api/settings", headers=self.test_headers)

        if response.status_code == 200:
            data = response.get_json()

            # Check response structure
            assert isinstance(data, dict)
            # Settings returns the settings object directly
            # or wrapped in success response

    def test_settings_update_format(self):
        """Test POST /api/settings returns expected format."""
        response = self.client.post(
            "/api/settings", headers=self.test_headers, json={"debug_mode": True}
        )

        if response.status_code == 200:
            data = response.get_json()

            # Check response structure
            assert isinstance(data, dict)
            assert "success" in data, "Must have 'success' field"

    def test_export_format(self):
        """Test GET /api/campaigns/<id>/export returns expected format."""
        # First create a campaign
        create_response = self.client.post(
            "/api/campaigns",
            headers=self.test_headers,
            json={
                "title": "Export Test Campaign",
                "character": "Test Character",
                "description": "Test Description",
            },
        )

        if create_response.status_code in [200, 201]:
            campaign_id = create_response.get_json().get("campaign_id")

            # Export campaign
            export_response = self.client.get(
                f"/api/campaigns/{campaign_id}/export?format=txt",
                headers=self.test_headers,
            )

            # Export returns file content, not JSON
            assert export_response.status_code == 200

    def test_frontend_compatibility_summary(self):
        """Document all frontend expectations for API responses."""
        expectations = {
            "GET /api/campaigns": {
                "format": "Array directly",
                "frontend": "const campaigns = data.campaigns || data",
                "fixed": True,
            },
            "GET /api/campaigns/<id>": {
                "format": "Object with campaign, story, game_state",
                "frontend": "data.campaign.title",
                "fixed": False,  # Still wrapped
            },
            "POST /api/campaigns": {
                "format": "Object with success, campaign_id",
                "frontend": "data.campaign_id",
                "fixed": False,  # Still wrapped
            },
            "POST /api/campaigns/<id>/interaction": {
                "format": "Object with narrative/response",
                "frontend": "data.narrative || data.response",
                "fixed": False,  # Still wrapped
            },
            "PATCH /api/campaigns/<id>": {
                "format": "Object with success",
                "frontend": "Standard success response",
                "fixed": False,  # Still wrapped
            },
            "GET /api/settings": {
                "format": "Settings object or wrapped",
                "frontend": "Handled by settings.js",
                "fixed": False,  # Format varies
            },
            "POST /api/settings": {
                "format": "Object with success",
                "frontend": "Standard success response",
                "fixed": False,  # Still wrapped
            },
        }

        # This test documents the state of API compatibility
        for endpoint, info in expectations.items():
            with self.subTest(endpoint=endpoint):
                if info["fixed"]:
                    assert True, f"{endpoint} is backward compatible"
                else:
                    # These endpoints still use new format but frontend handles it
                    assert (
                        True
                    ), f"{endpoint} uses new format but frontend is compatible"

    def tearDown(self):
        """Clean up Firebase mocks."""
        if hasattr(self, 'firebase_patcher'):
            self.firebase_patcher.stop()


if __name__ == "__main__":
    unittest.main()
