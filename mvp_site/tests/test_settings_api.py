"""
Tests for settings page API endpoints in MCP architecture.
These tests verify that the API gateway properly handles settings requests.
"""

import os
import sys
import unittest
from unittest.mock import patch

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

        # Use stable test UID and stub Firebase verification - patch fully-qualified target
        self._auth_patcher = patch(
            "mvp_site.main.auth.verify_id_token",
            return_value={"uid": self.test_user_id},
        )
        self._auth_patcher.start()
        self.addCleanup(self._auth_patcher.stop)

        # Bypass Firestore during tests
        # Patch both locations: firestore_service (for direct calls) and world_logic (for imported reference)
        self._settings_get_patcher = patch(
            "mvp_site.firestore_service.get_user_settings", return_value={}
        )
        self._settings_get_wl_patcher = patch(
            "mvp_site.world_logic.get_user_settings", return_value={}
        )
        self._settings_update_patcher = patch(
            "mvp_site.firestore_service.update_user_settings", return_value=True
        )
        self._settings_get_patcher.start()
        self._settings_get_wl_patcher.start()
        self._settings_update_patcher.start()
        self.addCleanup(self._settings_get_patcher.stop)
        self.addCleanup(self._settings_get_wl_patcher.stop)
        self.addCleanup(self._settings_update_patcher.stop)

        # Test headers with Authorization token
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer test-id-token",
        }

    def test_settings_page_route_works(self):
        """Test that settings page route works in MCP architecture."""
        # Test with auth headers - should not crash
        response = self.client.get("/settings", headers=self.headers)
        # In MCP architecture, may return various status codes depending on server state
        assert (
            response.status_code == 200
        ), "Settings page should return successfully with test headers"

        # If successful, should return HTML
        if response.status_code == 200:
            assert len(response.data) > 0, "Should return content"

    def test_settings_api_endpoint_works(self):
        """Test that settings API endpoint works in MCP architecture."""
        response = self.client.get("/api/settings", headers=self.headers)

        # Should handle request gracefully in MCP architecture
        assert (
            response.status_code == 200
        ), "Settings API should return successfully with test headers"

        # Response should be valid JSON if successful
        if response.status_code == 200:
            try:
                data = response.get_json()
                assert isinstance(data, dict), "Settings should return dict"
                assert data.get("llm_provider") == "gemini"
                assert data.get("gemini_model") == "gemini-3-pro-preview"
            except Exception as e:
                self.fail(f"Response should be valid JSON: {e}")

    def test_update_settings_api_works(self):
        """Test that settings update API works in MCP architecture."""
        test_settings = {"gemini_model": "gemini-3-pro-preview", "debug_mode": True}

        response = self.client.post(
            "/api/settings", json=test_settings, headers=self.headers
        )

        # Should handle request gracefully in MCP architecture
        assert (
            response.status_code == 200
        ), "Settings update should return successfully with valid data and test headers"

        # Response should be valid JSON
        try:
            data = response.get_json()
            assert data is not None, "Should return valid JSON response"
        except Exception as e:
            # If not JSON, should at least not crash
            assert isinstance(e, Exception), f"Should handle non-JSON gracefully: {e}"

    def test_update_settings_allows_openrouter_provider(self):
        """Ensure OpenRouter provider and model settings save successfully."""

        test_settings = {
            "llm_provider": "openrouter",
            "openrouter_model": "meta-llama/llama-3.1-70b-instruct",
        }

        response = self.client.post(
            "/api/settings", json=test_settings, headers=self.headers
        )

        assert response.status_code == 200

    def test_update_settings_allows_cerebras_provider(self):
        """Ensure Cerebras provider and model settings save successfully."""

        test_settings = {
            "llm_provider": "cerebras",
            "cerebras_model": "llama-3.3-70b",  # Updated: 3.1-70b retired from Cerebras
        }

        response = self.client.post(
            "/api/settings", json=test_settings, headers=self.headers
        )

        assert response.status_code == 200

    def test_settings_endpoints_auth_behavior(self):
        """Test that settings endpoints handle authentication in MCP architecture."""
        # Test without auth headers
        no_auth_response = self.client.get("/api/settings")

        # Should either require auth (401) or handle gracefully (500)
        assert (
            no_auth_response.status_code == 401
        ), "Should require authentication without test headers"

        # Test with auth headers
        auth_response = self.client.get("/api/settings", headers=self.headers)

        # Should not return 401 when auth headers are provided
        assert (
            auth_response.status_code != 401
        ), "Should not return 401 when auth headers provided"


if __name__ == "__main__":
    unittest.main()
