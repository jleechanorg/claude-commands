"""
TDD HTTP tests for settings page UI functionality.
Tests settings page using HTTP requests against a real prod server.

This simulates user interactions via HTTP calls rather than browser automation.
"""

import os
import unittest

import requests


# Skip HTTP tests when network tests are disabled in CI
@unittest.skipIf(
    os.getenv("ENABLE_NETWORK_TESTS") == "0",
    "HTTP tests disabled (ENABLE_NETWORK_TESTS=0)",
)
class TestSettingsUIHTTP(unittest.TestCase):
    """HTTP tests for settings page UI."""

    def setUp(self):
        """Set up HTTP client with test mode headers."""
        self.base_url = "http://localhost:6006"
        self.headers = {
            "X-Test-Bypass": "true",
            "X-Test-User-ID": "test-user-123",
            "Content-Type": "application/json",
        }
        self.timeout = 10  # 10 second timeout for all requests
        self.test_mode_url = (
            f"{self.base_url}?test_mode=true&test_user_id=test-user-123"
        )

    def test_settings_button_in_homepage(self):
        """🔴 RED: Homepage should contain settings button."""
        response = requests.get(self.test_mode_url, timeout=10)
        assert response.status_code == 200

        # Should contain settings button
        assert b"Settings" in response.content
        assert b'href="/settings"' in response.content
        assert b"bi bi-gear" in response.content  # Bootstrap icon

    def test_settings_page_loads(self):
        """🔴 RED: Settings page should load with proper content."""
        response = requests.get(
            f"{self.base_url}/settings?test_mode=true&test_user_id=test-user-123",
            timeout=self.timeout,
        )
        assert response.status_code == 200

        # Should contain settings page elements
        assert b"Settings" in response.content
        assert b"AI Model Selection" in response.content
        assert b"Gemini Pro 2.5" in response.content
        assert b"Gemini Flash 2.5" in response.content
        assert b"radio" in response.content

    def test_settings_api_get_empty_default(self):
        """🔴 RED: Settings API should return empty default for new user."""
        response = requests.get(
            f"{self.base_url}/api/settings", headers=self.headers, timeout=self.timeout
        )
        assert response.status_code == 200

        data = response.json()
        assert data == {}

    def test_settings_api_post_valid_model(self):
        """🔴 RED: Settings API should accept valid model selection."""
        payload = {"gemini_model": "flash-2.5"}

        response = requests.post(
            f"{self.base_url}/api/settings",
            headers=self.headers,
            json=payload,
            timeout=self.timeout,
        )
        assert response.status_code == 200

        data = response.json()
        assert data.get("success")
        assert data.get("message") == "Settings saved"

    def test_settings_api_post_invalid_model(self):
        """🔴 RED: Settings API should reject invalid model selection."""
        payload = {"gemini_model": "invalid-model"}

        response = requests.post(
            f"{self.base_url}/api/settings",
            headers=self.headers,
            json=payload,
            timeout=self.timeout,
        )
        assert response.status_code == 400

        data = response.json()
        assert "error" in data
        assert "Invalid model selection" in data["error"]

    def test_settings_persistence(self):
        """🔴 RED: Settings should persist across requests."""
        # Set a model preference
        payload = {"gemini_model": "pro-2.5"}
        response = requests.post(
            f"{self.base_url}/api/settings",
            headers=self.headers,
            json=payload,
            timeout=self.timeout,
        )
        assert response.status_code == 200

        # Retrieve and verify persistence
        response = requests.get(
            f"{self.base_url}/api/settings", headers=self.headers, timeout=self.timeout
        )
        assert response.status_code == 200

        data = response.json()
        assert data.get("gemini_model") == "pro-2.5"

    def test_settings_page_javascript_functionality(self):
        """🔴 RED: Settings page should include required JavaScript."""
        response = requests.get(
            f"{self.base_url}/settings?test_mode=true&test_user_id=test-user-123",
            timeout=self.timeout,
        )
        assert response.status_code == 200

        # Should include settings.js
        assert b"settings.js" in response.content

        # Should include proper form elements with IDs
        assert b'id="modelPro"' in response.content
        assert b'id="modelFlash"' in response.content
        assert b'id="save-message"' in response.content

    def test_settings_unauthorized_access(self):
        """🔴 RED: Settings endpoints should require authentication."""
        # Test without auth headers
        headers_no_auth = {"Content-Type": "application/json"}

        # Settings page
        response = requests.get(
            f"{self.base_url}/settings", headers=headers_no_auth, timeout=self.timeout
        )
        assert response.status_code == 401

        # Settings API GET
        response = requests.get(
            f"{self.base_url}/api/settings",
            headers=headers_no_auth,
            timeout=self.timeout,
        )
        assert response.status_code == 401

        # Settings API POST
        response = requests.post(
            f"{self.base_url}/api/settings",
            headers=headers_no_auth,
            json={"gemini_model": "pro-2.5"},
            timeout=self.timeout,
        )
        assert response.status_code == 401


if __name__ == "__main__":
    unittest.main()
