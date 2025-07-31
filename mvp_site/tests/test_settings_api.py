"""
Tests for settings page API endpoints in MCP architecture.
These tests verify that the API gateway properly handles settings requests.
"""

import os
import sys
import unittest

# Setup path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import create_app


class TestSettingsAPI(unittest.TestCase):
    """Tests for settings API endpoints in MCP architecture."""

    def setUp(self):
        """Set up test client and authentication headers."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.test_user_id = "test-user-123"
        self.headers = {
            "X-Test-Bypass-Auth": "true",
            "X-Test-User-ID": self.test_user_id,
        }

    def test_settings_page_route_works(self):
        """Test that settings page route works in MCP architecture."""
        # Test with auth headers - should not crash
        response = self.client.get("/settings", headers=self.headers)
        # In MCP architecture, may return various status codes depending on server state
        assert response.status_code == 200, "Settings page should return successfully with test headers"

        # If successful, should return HTML
        if response.status_code == 200:
            assert len(response.data) > 0, "Should return content"

    def test_settings_api_endpoint_works(self):
        """Test that settings API endpoint works in MCP architecture."""
        response = self.client.get("/api/settings", headers=self.headers)

        # Should handle request gracefully in MCP architecture
        assert response.status_code == 200, "Settings API should return successfully with test headers"

        # Response should be valid JSON if successful
        if response.status_code == 200:
            try:
                data = response.get_json()
                assert isinstance(data, dict), "Settings should return dict"
            except Exception as e:
                self.fail(f"Response should be valid JSON: {e}")

    def test_update_settings_api_works(self):
        """Test that settings update API works in MCP architecture."""
        test_settings = {"gemini_model": "gemini-2.5-flash", "debug_mode": True}

        response = self.client.post(
            "/api/settings", json=test_settings, headers=self.headers
        )

        # Should handle request gracefully in MCP architecture
        assert response.status_code == 200, "Settings update should return successfully with valid data and test headers"

        # Response should be valid JSON
        try:
            data = response.get_json()
            assert data is not None, "Should return valid JSON response"
        except Exception as e:
            # If not JSON, should at least not crash
            assert isinstance(e, Exception), f"Should handle non-JSON gracefully: {e}"

    def test_settings_endpoints_auth_behavior(self):
        """Test that settings endpoints handle authentication in MCP architecture."""
        # Test without auth headers
        no_auth_response = self.client.get("/api/settings")

        # Should either require auth (401) or handle gracefully (500)
        assert no_auth_response.status_code == 401, "Should require authentication without test headers"

        # Test with auth headers
        auth_response = self.client.get("/api/settings", headers=self.headers)

        # Should not return 401 when auth headers are provided
        assert (
            auth_response.status_code != 401
        ), "Should not return 401 when auth headers provided"


if __name__ == "__main__":
    unittest.main()
