#!/usr/bin/env python3
"""
🟢 Layer 2: HTTP Integration Tests for Settings API
Real HTTP tests against live server with real services (no mocks)

These tests verify the settings API works end-to-end with:
- Real Firestore database
- Real authentication bypass
- Real HTTP requests
- Real data persistence
"""

import unittest
import requests
import json
import time

class TestSettingsHttpIntegration(unittest.TestCase):
    """Layer 2: HTTP integration tests for settings functionality"""

    def setUp(self):
        """Set up HTTP client for real server testing"""
        self.base_url = "http://localhost:8081"
        self.test_user_id = "http-test-user-layer2"

        self.headers = {
            "X-Test-Bypass-Auth": "true",
            "X-Test-User-ID": self.test_user_id,
            "Content-Type": "application/json"
        }

        # Ensure server is ready
        self.wait_for_server()

    def wait_for_server(self, max_retries=5):
        """Wait for test server to be available"""
        for i in range(max_retries):
            try:
                response = requests.get(f"{self.base_url}/", timeout=2)
                if response.status_code == 200:
                    return
            except:
                pass
            time.sleep(1)
        raise Exception("Test server not available")

    def test_get_settings_empty_default(self):
        """✅ GET /api/settings returns empty dict for new user"""
        response = requests.get(f"{self.base_url}/api/settings", headers=self.headers)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data, {}, "New user should have empty settings")

    def test_post_settings_valid_model(self):
        """✅ POST /api/settings accepts valid Gemini model"""
        payload = {"gemini_model": "flash-2.5"}

        response = requests.post(
            f"{self.base_url}/api/settings",
            headers=self.headers,
            json=payload
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'), f"Should return success, got: {data}")
        self.assertEqual(data.get('message'), 'Settings saved')

    def test_post_settings_invalid_model(self):
        """✅ POST /api/settings rejects invalid model"""
        payload = {"gemini_model": "invalid-model"}

        response = requests.post(
            f"{self.base_url}/api/settings",
            headers=self.headers,
            json=payload
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('Invalid model selection', data['error'])

    def test_settings_persistence_round_trip(self):
        """✅ Settings persist across requests (real Firestore test)"""
        # Set a preference
        payload = {"gemini_model": "pro-2.5"}

        response = requests.post(
            f"{self.base_url}/api/settings",
            headers=self.headers,
            json=payload
        )
        self.assertEqual(response.status_code, 200)

        # Verify it persisted by retrieving it
        response = requests.get(f"{self.base_url}/api/settings", headers=self.headers)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data.get('gemini_model'), 'pro-2.5',
                        f"Settings should persist in Firestore, got: {data}")

    def test_settings_overwrite_existing(self):
        """✅ New settings overwrite existing ones"""
        # Set initial setting
        requests.post(
            f"{self.base_url}/api/settings",
            headers=self.headers,
            json={"gemini_model": "pro-2.5"}
        )

        # Change to different setting
        requests.post(
            f"{self.base_url}/api/settings",
            headers=self.headers,
            json={"gemini_model": "flash-2.5"}
        )

        # Verify change persisted
        response = requests.get(f"{self.base_url}/api/settings", headers=self.headers)
        data = response.json()
        self.assertEqual(data.get('gemini_model'), 'flash-2.5',
                        "Settings should be updated, not appended")

    def test_missing_gemini_model_parameter(self):
        """✅ POST /api/settings rejects missing parameters"""
        payload = {"wrong_field": "value"}

        response = requests.post(
            f"{self.base_url}/api/settings",
            headers=self.headers,
            json=payload
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('Missing gemini_model parameter', data['error'])

    def test_settings_page_loads_with_auth_bypass(self):
        """✅ /settings page loads successfully with auth bypass"""
        response = requests.get(f"{self.base_url}/settings", headers=self.headers)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Settings", response.text)
        self.assertIn("AI Model Selection", response.text)
        self.assertIn("Gemini Pro 2.5", response.text)
        self.assertIn("Gemini Flash 2.5", response.text)
        self.assertIn("settings.js", response.text)

    def test_unauthorized_access_without_headers(self):
        """✅ Endpoints require auth when bypass headers missing"""
        # Test without auth bypass headers
        headers_no_auth = {"Content-Type": "application/json"}

        # Settings page should require auth
        response = requests.get(f"{self.base_url}/settings", headers=headers_no_auth)
        self.assertEqual(response.status_code, 401)

        # Settings API should require auth
        response = requests.get(f"{self.base_url}/api/settings", headers=headers_no_auth)
        self.assertEqual(response.status_code, 401)

        response = requests.post(
            f"{self.base_url}/api/settings",
            headers=headers_no_auth,
            json={"gemini_model": "pro-2.5"}
        )
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    print("🧪 Running Layer 2: HTTP Integration Tests")
    print("📡 Testing against real server with real Firestore")
    print("🔒 Testing authentication bypass functionality")
    print("=" * 50)

    unittest.main(verbosity=2)
