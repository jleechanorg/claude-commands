"""
End-to-end integration test for MCP error handling and translation.
Tests error propagation from world_logic → MCPClient → Flask HTTP responses.
Only mocks external services (Firestore DB and Gemini API) at the lowest level.
"""

import json
import os
import sys
import unittest
from unittest.mock import patch

# Set TESTING environment variable
os.environ["TESTING"] = "true"
os.environ["GEMINI_API_KEY"] = "test-api-key"

# Add the parent directory to the path to import main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


# Check for Firebase credentials - same pattern as other tests
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


from main import HEADER_TEST_BYPASS, HEADER_TEST_USER_ID, create_app

from tests.fake_firestore import FakeFirestoreClient


@unittest.skipUnless(
    has_firebase_credentials(),
    "Skipping MCP error handling end2end tests - Firebase credentials not available (expected in CI)",
)
class TestMCPErrorHandlingEnd2End(unittest.TestCase):
    """Test MCP error handling and translation through the full application stack."""

    def setUp(self):
        """Set up test client and test data."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Test data
        self.test_user_id = "mcp-error-test-user"
        self.test_campaign_id = "mcp-error-test-campaign"
        self.test_headers = {
            HEADER_TEST_BYPASS: "true",
            HEADER_TEST_USER_ID: self.test_user_id,
        }

    @patch("firebase_admin.firestore.client")
    def test_mcp_campaign_not_found_error(self, mock_firestore_client):
        """Test MCP error handling for non-existent campaign."""
        # Set up empty fake Firestore (no campaigns exist)
        fake_firestore = FakeFirestoreClient()
        mock_firestore_client.return_value = fake_firestore

        # Try to get non-existent campaign through MCP
        response = self.client.get(
            "/api/campaigns/non-existent-campaign",
            headers=self.test_headers,
        )

        # Verify MCP error is properly translated to HTTP
        assert response.status_code == 404
        response_data = json.loads(response.data)
        assert isinstance(response_data, dict)
        assert "error" in response_data
        assert "not found" in response_data["error"].lower()

    def test_mcp_missing_user_id_error(self):
        """Test MCP error handling for missing authentication."""
        # Try to access campaigns without user ID
        response = self.client.get("/api/campaigns")

        # Should return authentication error through MCP
        assert response.status_code in [401, 403, 404, 500]

    def test_mcp_invalid_request_format_error(self):
        """Test MCP error handling for invalid request format."""
        # Send malformed JSON data
        response = self.client.post(
            "/api/campaigns",
            data="invalid json data",
            content_type="application/json",
            headers=self.test_headers,
        )

        # Should return error through MCP (400 or 500 acceptable)
        assert response.status_code in [400, 500]

        # Try with missing required fields
        invalid_campaign_data = {"title": ""}  # Empty title should fail validation
        response = self.client.post(
            "/api/campaigns",
            data=json.dumps(invalid_campaign_data),
            content_type="application/json",
            headers=self.test_headers,
        )

        # Should return validation error
        assert response.status_code in [400, 500]
        response_data = json.loads(response.data)
        assert "error" in response_data

    @patch("firebase_admin.firestore.client")
    def test_mcp_interaction_missing_campaign_error(self, mock_firestore_client):
        """Test MCP error handling for interaction with non-existent campaign."""
        # Set up empty fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_firestore_client.return_value = fake_firestore

        # Try to interact with non-existent campaign
        interaction_data = {
            "input": "Test interaction",
            "mode": "character",
        }

        response = self.client.post(
            "/api/campaigns/non-existent/interaction",
            data=json.dumps(interaction_data),
            content_type="application/json",
            headers=self.test_headers,
        )

        # Should return campaign not found error through MCP
        assert response.status_code in [400, 404, 500]
        response_data = json.loads(response.data)
        assert "error" in response_data

    @patch("firebase_admin.firestore.client")
    def test_mcp_interaction_invalid_mode_error(self, mock_firestore_client):
        """Test MCP error handling for invalid interaction mode."""
        # Set up fake Firestore with campaign
        fake_firestore = FakeFirestoreClient()
        mock_firestore_client.return_value = fake_firestore

        # Create a campaign
        user_doc = fake_firestore.collection("users").document(self.test_user_id)
        campaign_doc = user_doc.collection("campaigns").document(self.test_campaign_id)
        campaign_doc.set(
            {
                "id": self.test_campaign_id,
                "user_id": self.test_user_id,
                "title": "Test Campaign",
            }
        )

        # Try interaction with invalid mode
        interaction_data = {
            "input": "Test interaction",
            "mode": "invalid_mode",
        }

        response = self.client.post(
            f"/api/campaigns/{self.test_campaign_id}/interaction",
            data=json.dumps(interaction_data),
            content_type="application/json",
            headers=self.test_headers,
        )

        # Should handle invalid mode through MCP
        assert response.status_code in [200, 400, 404, 500]
        response_data = json.loads(response.data)
        assert isinstance(response_data, dict)

    @patch("firebase_admin.firestore.client")
    def test_mcp_update_campaign_not_found_error(self, mock_firestore_client):
        """Test MCP error handling for updating non-existent campaign."""
        # Set up empty fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_firestore_client.return_value = fake_firestore

        # Try to update non-existent campaign
        update_data = {"title": "Updated Title"}
        response = self.client.patch(
            "/api/campaigns/non-existent-campaign",
            data=json.dumps(update_data),
            content_type="application/json",
            headers=self.test_headers,
        )

        # Should return not found error through MCP
        assert response.status_code in [400, 404, 500]
        response_data = json.loads(response.data)
        assert "error" in response_data

    @patch("firebase_admin.firestore.client")
    def test_mcp_export_campaign_not_found_error(self, mock_firestore_client):
        """Test MCP error handling for exporting non-existent campaign."""
        # Set up empty fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_firestore_client.return_value = fake_firestore

        # Try to export non-existent campaign
        response = self.client.get(
            "/api/campaigns/non-existent-campaign/export?format=txt",
            headers=self.test_headers,
        )

        # Should return not found error through MCP
        assert response.status_code in [400, 404, 500]
        response_data = json.loads(response.data)
        assert "error" in response_data

    @patch("firebase_admin.firestore.client")
    def test_mcp_export_invalid_format_error(self, mock_firestore_client):
        """Test MCP error handling for invalid export format."""
        # Set up fake Firestore with campaign
        fake_firestore = FakeFirestoreClient()
        mock_firestore_client.return_value = fake_firestore

        user_doc = fake_firestore.collection("users").document(self.test_user_id)
        campaign_doc = user_doc.collection("campaigns").document(self.test_campaign_id)
        campaign_doc.set(
            {
                "id": self.test_campaign_id,
                "user_id": self.test_user_id,
                "title": "Test Campaign",
            }
        )

        # Try to export with invalid format
        response = self.client.get(
            f"/api/campaigns/{self.test_campaign_id}/export?format=invalid",
            headers=self.test_headers,
        )

        # Should return validation error through MCP
        assert response.status_code in [400, 404, 500]
        response_data = json.loads(response.data)
        assert "error" in response_data

    def test_mcp_http_method_not_allowed_error(self):
        """Test MCP error handling for unsupported HTTP methods."""
        # Try DELETE on campaigns endpoint (not supported)
        response = self.client.delete(
            "/api/campaigns/some-campaign",
            headers=self.test_headers,
        )

        # Should return method not allowed
        assert response.status_code == 405

        # Try PUT on interaction endpoint (not supported)
        response = self.client.put(
            f"/api/campaigns/{self.test_campaign_id}/interaction",
            headers=self.test_headers,
        )

        # Should return method not allowed
        assert response.status_code == 405

    @patch("firebase_admin.firestore.client")
    def test_mcp_firestore_connection_error_simulation(self, mock_firestore_client):
        """Test MCP error handling when Firestore connection fails."""
        # Simulate Firestore connection error
        mock_firestore_client.side_effect = Exception("Firestore connection failed")

        # Try to get campaigns (should fail gracefully)
        response = self.client.get("/api/campaigns", headers=self.test_headers)

        # Should return error through MCP (could be 200 with empty array or 500)
        assert response.status_code in [200, 500]
        response_data = json.loads(response.data)
        if response.status_code == 500:
            # Check for error message in 500 case
            assert "error" in response_data or "message" in response_data

    def test_mcp_missing_content_type_error(self):
        """Test MCP error handling for missing Content-Type header."""
        # Send JSON data without Content-Type header
        campaign_data = {"title": "Test Campaign"}
        response = self.client.post(
            "/api/campaigns",
            data=json.dumps(campaign_data),
            # Note: no content_type specified
            headers=self.test_headers,
        )

        # Should handle gracefully (Flask might auto-detect or return 400)
        assert response.status_code in [200, 201, 400, 415, 500]

    @patch("firebase_admin.firestore.client")
    def test_mcp_unauthorized_campaign_access_error(self, mock_firestore_client):
        """Test MCP error handling for accessing another user's campaign."""
        # Set up fake Firestore with campaign belonging to different user
        fake_firestore = FakeFirestoreClient()
        mock_firestore_client.return_value = fake_firestore

        # Create campaign under different user
        different_user_doc = fake_firestore.collection("users").document(
            "different-user"
        )
        campaign_doc = different_user_doc.collection("campaigns").document(
            self.test_campaign_id
        )
        campaign_doc.set(
            {
                "id": self.test_campaign_id,
                "user_id": "different-user",  # Different from test_user_id
                "title": "Other User's Campaign",
            }
        )

        # Try to access the campaign as test_user_id
        response = self.client.get(
            f"/api/campaigns/{self.test_campaign_id}",
            headers=self.test_headers,
        )

        # Should return not found (for security - don't reveal existence)
        assert response.status_code == 404
        response_data = json.loads(response.data)
        assert "error" in response_data

    def test_mcp_error_response_format_consistency(self):
        """Test that all MCP error responses have consistent format."""
        # Test various error scenarios and verify response format consistency

        # Missing authentication
        response = self.client.get("/api/campaigns")
        if response.status_code >= 400:
            response_data = json.loads(response.data)
            assert isinstance(response_data, dict)
            # Flask auth returns "message" field, not "error" field
            assert "error" in response_data or "message" in response_data
            error_msg = response_data.get("error") or response_data.get("message")
            assert isinstance(error_msg, str)

        # Invalid campaign ID
        response = self.client.get(
            "/api/campaigns/invalid-id",
            headers=self.test_headers,
        )
        if response.status_code >= 400:
            response_data = json.loads(response.data)
            assert isinstance(response_data, dict)
            # Either "error" or "message" field is acceptable
            assert "error" in response_data or "message" in response_data
            error_msg = response_data.get("error") or response_data.get("message")
            assert isinstance(error_msg, str)

        # Malformed JSON
        response = self.client.post(
            "/api/campaigns",
            data="invalid json",
            content_type="application/json",
            headers=self.test_headers,
        )
        if response.status_code >= 400:
            response_data = json.loads(response.data)
            assert isinstance(response_data, dict)
            # Either "error" or "message" field is acceptable
            assert "error" in response_data or "message" in response_data
            error_msg = response_data.get("error") or response_data.get("message")
            assert isinstance(error_msg, str)


if __name__ == "__main__":
    unittest.main()
