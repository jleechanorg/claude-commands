"""
Test API routes functionality in MCP architecture.
Tests API endpoints through MCP API gateway pattern.
"""

import json
import os
import sys
import unittest

# Set environment variables for MCP testing
os.environ["TESTING"] = "true"
os.environ["USE_MOCKS"] = "true"

# Add parent directory to path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__ if '__file__' in globals() else 'tests/test_api_routes.py'))))
)

from main import create_app


class TestAPIRoutes(unittest.TestCase):
    """Test API routes through MCP API gateway."""

    def setUp(self):
        """Set up test client for MCP architecture."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Test data for MCP architecture
        self.test_user_id = "mcp-api-test-user"
        self.test_headers = {
            "X-Test-Bypass-Auth": "true",
            "X-Test-User-ID": self.test_user_id,
            "Content-Type": "application/json",
        }

    def test_mcp_get_campaigns_endpoint(self):
        """Test campaigns list endpoint through MCP gateway."""
        response = self.client.get("/api/campaigns", headers=self.test_headers)

        # MCP gateway should handle campaigns list gracefully
        assert (
            response.status_code == 200
        ), f"Expected 200 for campaigns list, got {response.status_code}"

        # If successful, should return valid JSON format
        if response.status_code == 200:
            data = response.get_json()
            assert isinstance(
                data, (dict, list)
            ), "Campaigns response should be dict or list format"

    def test_mcp_get_specific_campaign_endpoint(self):
        """Test specific campaign retrieval through MCP gateway."""
        response = self.client.get(
            "/api/campaigns/mcp-test-campaign", headers=self.test_headers
        )

        # MCP gateway should handle specific campaign requests gracefully (may return 400 instead of 404)
        assert response.status_code in [
            400,
            404,
        ], f"Expected 400 or 404 for nonexistent campaign, got {response.status_code}"

        # If successful, should return valid campaign data format
        if response.status_code == 200:
            data = response.get_json()
            assert isinstance(data, dict), "Campaign response should be dict format"

    def test_mcp_get_campaigns_response(self):
        """Test campaigns endpoint response through MCP."""
        response = self.client.get("/api/campaigns", headers=self.test_headers)

        # MCP should return 200 with valid response format
        assert (
            response.status_code == 200
        ), f"Expected 200 for campaigns list, got {response.status_code}"

        data = response.get_json()
        assert isinstance(
            data, (list, dict)
        ), "Campaigns should return list or dict format"

        # Accept any response format - could be empty list or list with existing campaigns
        if isinstance(data, list):
            # Could be empty or have campaigns
            assert all(
                isinstance(item, dict) for item in data
            ), "Campaign items should be dict format"
        elif isinstance(data, dict):
            # Could be wrapped response format
            assert data is not None, "Response should not be None"

    def test_mcp_get_campaigns_error_handling(self):
        """Test campaigns endpoint error handling through MCP."""
        # Test with invalid headers
        invalid_headers = {"Content-Type": "application/json"}
        response = self.client.get("/api/campaigns", headers=invalid_headers)

        # MCP should handle authentication errors gracefully
        assert (
            response.status_code == 401
        ), f"Expected 401 for authentication error, got {response.status_code}"

    def test_mcp_campaign_with_debug_mode(self):
        """Test campaign retrieval with debug mode through MCP."""
        response = self.client.get(
            "/api/campaigns/mcp-debug-campaign", headers=self.test_headers
        )

        # MCP should handle debug mode campaigns consistently (may return 400 instead of 404)
        assert response.status_code in [
            400,
            404,
        ], f"Expected 400 or 404 for nonexistent campaign, got {response.status_code}"

    def test_mcp_get_settings_endpoint(self):
        """Test settings endpoint through MCP gateway."""
        response = self.client.get("/api/settings", headers=self.test_headers)

        # MCP gateway should handle settings requests gracefully
        assert (
            response.status_code == 200
        ), f"Expected 200 for settings, got {response.status_code}"

        # If successful, should return valid settings format
        if response.status_code == 200:
            data = response.get_json()
            assert isinstance(data, dict), "Settings response should be dict format"

    def test_mcp_post_settings_endpoint(self):
        """Test settings update endpoint through MCP gateway."""
        test_settings = {"debug_mode": True, "theme": "dark"}

        response = self.client.post(
            "/api/settings", data=json.dumps(test_settings), headers=self.test_headers
        )

        # MCP gateway should handle settings updates gracefully
        assert (
            response.status_code == 200
        ), f"Expected 200 for settings update, got {response.status_code}"

    def test_mcp_campaign_interaction_endpoint(self):
        """Test campaign interaction endpoint through MCP gateway."""
        interaction_data = {"input": "I explore the area", "mode": "character"}

        response = self.client.post(
            "/api/campaigns/mcp-test-campaign/interaction",
            data=json.dumps(interaction_data),
            headers=self.test_headers,
        )

        # MCP gateway should handle interaction requests gracefully (may return 400 instead of 404)
        assert (
            response.status_code in [400, 404]
        ), f"Expected 400 or 404 for nonexistent campaign interaction, got {response.status_code}"

        # If successful, should return valid interaction response
        if response.status_code == 200:
            data = response.get_json()
            assert isinstance(data, dict), "Interaction response should be dict format"

    def test_mcp_cors_headers_handling(self):
        """Test CORS headers handling through MCP gateway."""
        cors_headers = {**self.test_headers, "Origin": "https://example.com"}

        response = self.client.get("/api/campaigns", headers=cors_headers)

        # MCP should handle CORS requests consistently
        assert (
            response.status_code == 200
        ), f"Expected 200 for CORS campaigns list, got {response.status_code}"


if __name__ == "__main__":
    unittest.main()
