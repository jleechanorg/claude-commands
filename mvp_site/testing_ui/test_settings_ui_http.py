"""
TDD HTTP tests for settings page UI functionality.
Tests settings page using HTTP requests against a real prod server.

This simulates user interactions via HTTP calls rather than browser automation.
"""

import unittest

import requests


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
        self.test_mode_url = (
            f"{self.base_url}?test_mode=true&test_user_id=test-user-123"
        )

    def test_settings_button_in_homepage(self):
        """🔴 RED: Homepage should contain settings button."""
        response = requests.get(self.test_mode_url)
        self.assertEqual(response.status_code, 200)

        # Should contain settings button
        self.assertIn(b"Settings", response.content)
        self.assertIn(b'href="/settings"', response.content)
        self.assertIn(b"bi bi-gear", response.content)  # Bootstrap icon

    def test_settings_page_loads(self):
        """🔴 RED: Settings page should load with proper content."""
        response = requests.get(
            f"{self.base_url}/settings?test_mode=true&test_user_id=test-user-123"
        )
        self.assertEqual(response.status_code, 200)

        # Should contain settings page elements
        self.assertIn(b"Settings", response.content)
        self.assertIn(b"AI Model Selection", response.content)
        self.assertIn(b"Gemini Pro 2.5", response.content)
        self.assertIn(b"Gemini Flash 2.5", response.content)
        self.assertIn(b"radio", response.content)

    def test_settings_api_get_empty_default(self):
        """🔴 RED: Settings API should return empty default for new user."""
        response = requests.get(f"{self.base_url}/api/settings", headers=self.headers)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data, {})

    def test_settings_api_post_valid_model(self):
        """🔴 RED: Settings API should accept valid model selection."""
        payload = {"gemini_model": "flash-2.5"}

        response = requests.post(
            f"{self.base_url}/api/settings", headers=self.headers, json=payload
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("message"), "Settings saved")

    def test_settings_api_post_invalid_model(self):
        """🔴 RED: Settings API should reject invalid model selection."""
        payload = {"gemini_model": "invalid-model"}

        response = requests.post(
            f"{self.base_url}/api/settings", headers=self.headers, json=payload
        )
        self.assertEqual(response.status_code, 400)

        data = response.json()
        self.assertIn("error", data)
        self.assertIn("Invalid model selection", data["error"])

    def test_settings_persistence(self):
        """🔴 RED: Settings should persist across requests."""
        # Set a model preference
        payload = {"gemini_model": "pro-2.5"}
        response = requests.post(
            f"{self.base_url}/api/settings", headers=self.headers, json=payload
        )
        self.assertEqual(response.status_code, 200)

        # Retrieve and verify persistence
        response = requests.get(f"{self.base_url}/api/settings", headers=self.headers)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data.get("gemini_model"), "pro-2.5")

    def test_settings_page_javascript_functionality(self):
        """🔴 RED: Settings page should include required JavaScript."""
        response = requests.get(
            f"{self.base_url}/settings?test_mode=true&test_user_id=test-user-123"
        )
        self.assertEqual(response.status_code, 200)

        # Should include settings.js
        self.assertIn(b"settings.js", response.content)

        # Should include proper form elements with IDs
        self.assertIn(b'id="modelPro"', response.content)
        self.assertIn(b'id="modelFlash"', response.content)
        self.assertIn(b'id="save-message"', response.content)

    def test_settings_unauthorized_access(self):
        """🔴 RED: Settings endpoints should require authentication."""
        # Test without auth headers
        headers_no_auth = {"Content-Type": "application/json"}

        # Settings page
        response = requests.get(f"{self.base_url}/settings", headers=headers_no_auth)
        self.assertEqual(response.status_code, 401)

        # Settings API GET
        response = requests.get(
            f"{self.base_url}/api/settings", headers=headers_no_auth
        )
        self.assertEqual(response.status_code, 401)

        # Settings API POST
        response = requests.post(
            f"{self.base_url}/api/settings",
            headers=headers_no_auth,
            json={"gemini_model": "pro-2.5"},
        )
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
