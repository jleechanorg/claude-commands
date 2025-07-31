"""
Test suite for authentication functionality in MCP architecture
Tests authentication handling through the MCP API gateway pattern.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["TESTING"] = "true"
os.environ["USE_MOCKS"] = "true"

import unittest

from main import create_app


class TestMainAuthenticationAdvanced(unittest.TestCase):
    """Test authentication scenarios in MCP architecture"""

    def setUp(self):
        """Set up test client for MCP architecture"""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Test headers for MCP authentication
        self.test_user_id = "mcp-auth-test-user"
        self.auth_headers = {
            "X-Test-Bypass-Auth": "true",
            "X-Test-User-ID": self.test_user_id,
            "Content-Type": "application/json",
        }

    def tearDown(self):
        """Clean up after tests"""

    # MCP Architecture Authentication Tests

    def test_mcp_auth_bypass_headers(self):
        """Test MCP authentication bypass headers work correctly"""
        # Test request with auth bypass headers
        response = self.client.get("/api/campaigns", headers=self.auth_headers)

        # MCP gateway should handle request gracefully
        assert response.status_code == 200, "Should handle requests successfully"

        # Should return valid JSON response
        if response.status_code == 200:
            data = response.get_json()
            assert isinstance(data, (list, dict)), "Response should be valid JSON"

    def test_mcp_auth_without_headers(self):
        """Test MCP authentication without bypass headers"""
        # Test request without auth headers
        response = self.client.get("/api/campaigns")

        # Should require authentication without bypass headers
        assert response.status_code == 401, "Should require authentication without bypass headers"

    def test_mcp_user_specific_requests(self):
        """Test MCP handles user-specific requests correctly"""
        # Test user-specific endpoint
        response = self.client.get("/api/settings", headers=self.auth_headers)

        # MCP gateway should handle user-specific requests
        assert response.status_code == 200, "Should handle requests successfully"

        # If successful, should return user data format
        if response.status_code == 200:
            data = response.get_json()
            assert isinstance(data, dict), "User settings should be dict format"

    def test_mcp_cors_headers(self):
        """Test CORS headers in MCP architecture"""
        # Test preflight OPTIONS request
        response = self.client.options(
            "/api/campaigns",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Method": "GET",
            },
        )

        # Should handle preflight requests appropriately
        assert response.status_code == 200, "MCP gateway should handle preflight requests"

        # Check for CORS headers if present
        if "Access-Control-Allow-Origin" in response.headers:
            assert response.headers.get("Access-Control-Allow-Origin") is not None

    def test_mcp_authentication_consistency(self):
        """Test authentication consistency across different endpoints"""
        endpoints = ["/api/campaigns", "/api/settings", "/"]

        for endpoint in endpoints:
            response = self.client.get(endpoint, headers=self.auth_headers)

            # All endpoints should handle authentication consistently
            assert response.status_code == 200, f"MCP gateway should handle {endpoint} consistently"


if __name__ == "__main__":
    unittest.main()
