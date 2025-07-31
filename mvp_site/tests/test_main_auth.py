"""
Test authentication functionality in MCP architecture.
Tests authentication handling through MCP API gateway pattern.
"""

# Set environment variables for MCP testing
import os

os.environ["TESTING"] = "true"
os.environ["USE_MOCKS"] = "true"

import json
import sys
import unittest

# Add parent directory to path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from main import create_app


class TestAuthenticationMiddleware(unittest.TestCase):
    """Test authentication middleware through MCP API gateway."""

    def setUp(self):
        """Set up test client for MCP architecture."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Test data for MCP architecture
        self.test_user_id = "mcp-auth-test-user"
        self.test_headers = {
            "X-Test-Bypass-Auth": "true",
            "X-Test-User-ID": self.test_user_id,
            "Content-Type": "application/json",
        }

    def test_mcp_authentication_bypass_headers(self):
        """Test authentication bypass headers through MCP gateway."""
        response = self.client.get("/api/campaigns", headers=self.test_headers)

        # MCP gateway should handle authentication bypass gracefully
        assert (
            response.status_code == 200
        ), f"Expected 200 for auth bypass headers, got {response.status_code}"

    def test_mcp_unauthenticated_request(self):
        """Test unauthenticated request through MCP gateway."""
        # Request without authentication headers
        response = self.client.get("/api/campaigns")

        # MCP gateway should handle unauthenticated requests appropriately
        assert (
            response.status_code == 401
        ), "MCP gateway should handle unauthenticated requests"

    def test_mcp_invalid_auth_headers(self):
        """Test invalid authentication headers through MCP gateway."""
        invalid_headers = {
            "X-Test-User-ID": "invalid-user",
            "Content-Type": "application/json",
            # Missing X-Test-Bypass-Auth
        }

        response = self.client.get("/api/campaigns", headers=invalid_headers)

        # MCP gateway should handle invalid auth headers gracefully
        assert (
            response.status_code == 401
        ), "MCP gateway should handle invalid auth headers"

    def test_mcp_campaign_access_with_auth(self):
        """Test campaign access with authentication through MCP."""
        response = self.client.get(
            "/api/campaigns/mcp-test-campaign", headers=self.test_headers
        )

        # MCP gateway should handle authenticated campaign access (404 = campaign not found)
        assert (
            response.status_code == 404
        ), "MCP gateway should handle authenticated campaign access"

    def test_mcp_settings_access_with_auth(self):
        """Test settings access with authentication through MCP."""
        response = self.client.get("/api/settings", headers=self.test_headers)

        # MCP gateway should handle authenticated settings access
        assert (
            response.status_code == 200
        ), f"Expected 200 for authenticated settings access, got {response.status_code}"

    def test_mcp_interaction_endpoint_auth(self):
        """Test interaction endpoint authentication through MCP."""
        interaction_data = {"input": "Test interaction", "mode": "character"}

        response = self.client.post(
            "/api/campaigns/mcp-test-campaign/interaction",
            data=json.dumps(interaction_data),
            headers=self.test_headers,
        )

        # MCP gateway should handle authenticated interactions (may return 404 for nonexistent campaigns)
        assert (
            response.status_code in [400, 404]
        ), f"MCP gateway should handle authenticated interactions, got {response.status_code}"

    def test_mcp_different_user_isolation(self):
        """Test user isolation through MCP authentication."""
        # Test with different user IDs
        user1_headers = {**self.test_headers, "X-Test-User-ID": "mcp-user-1"}
        user2_headers = {**self.test_headers, "X-Test-User-ID": "mcp-user-2"}

        response1 = self.client.get("/api/campaigns", headers=user1_headers)
        response2 = self.client.get("/api/campaigns", headers=user2_headers)

        # MCP should handle different users consistently
        assert (
            response1.status_code == 200
        ), f"Expected 200 for user1 authenticated request, got {response1.status_code}"
        assert (
            response2.status_code == 200
        ), f"Expected 200 for user2 authenticated request, got {response2.status_code}"

    def test_mcp_auth_header_case_sensitivity(self):
        """Test authentication header case sensitivity through MCP."""
        # Test with different header cases
        lower_headers = {
            "x-test-bypass-auth": "true",
            "x-test-user-id": self.test_user_id,
            "content-type": "application/json",
        }

        response = self.client.get("/api/campaigns", headers=lower_headers)

        # MCP should handle header case variations appropriately (200 = case-insensitive auth works)
        assert (
            response.status_code == 200
        ), f"MCP should handle header case variations, got {response.status_code}"

    def test_mcp_cors_with_auth(self):
        """Test CORS handling with authentication through MCP."""
        cors_headers = {**self.test_headers, "Origin": "https://example.com"}

        response = self.client.get("/api/campaigns", headers=cors_headers)

        # MCP should handle CORS with authentication consistently (200 = auth bypass works)
        assert response.status_code == 200, "MCP should handle CORS with authentication"

    def test_mcp_long_user_id_handling(self):
        """Test handling of long user IDs through MCP."""
        long_user_id = "mcp-very-long-user-id-" + "x" * 100
        long_headers = {**self.test_headers, "X-Test-User-ID": long_user_id}

        response = self.client.get("/api/campaigns", headers=long_headers)

        # MCP should handle long user IDs gracefully (200 = auth bypass works)
        assert response.status_code == 200, "MCP should handle long user IDs"


if __name__ == "__main__":
    unittest.main()
