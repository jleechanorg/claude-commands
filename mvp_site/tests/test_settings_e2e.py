"""
Layer 4: End-to-end tests with real services

Tests the complete system with minimal mocking - only external APIs like
actual Gemini calls are mocked, but internal services run normally.

Coverage:
- Real Flask app with real settings persistence
- Real model selection logic
- Real campaign creation flow
- Only external API calls are mocked for cost control

NOTE: This simulates production-like behavior while controlling costs
"""

import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add the parent directory to the path to import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fake_firestore import FakeFirestoreClient
from main import create_app


class TestSettingsE2E(unittest.TestCase):
    """Layer 4: End-to-end tests with minimal mocking"""

    def setUp(self):
        """Set up test fixtures"""
        self.app = create_app()
        self.app.config["TESTING"] = True
        # Force testing mode for CI compatibility
        os.environ["TESTING"] = "true"
        self.client = self.app.test_client()

        # Add Firestore mocking for CI compatibility
        self.firestore_patcher = patch("firestore_service.get_db")
        self.mock_get_db = self.firestore_patcher.start()
        self.fake_db = FakeFirestoreClient()
        self.mock_get_db.return_value = self.fake_db

        # Test data
        self.test_user_id = "e2e-test-user"
        self.auth_headers = {
            "X-Test-Bypass-Auth": "true",
            "X-Test-User-ID": self.test_user_id,
            "Content-Type": "application/json",
        }

    def tearDown(self):
        """Clean up after each test for CI isolation"""
        # Stop Firestore mocking
        self.firestore_patcher.stop()
        # Ensure clean state for CI environment
        if "TESTING" in os.environ:
            pass  # Keep TESTING env var for other tests

    def test_complete_user_journey_flash_model(self):
        """🟢 E2E: Complete user journey from settings to campaign with flash model"""

        # Only mock the expensive external API call
        with (
            patch("gemini_service._call_gemini_api") as mock_api_call,
            patch("gemini_service._get_text_from_response") as mock_get_text,
        ):
            # Arrange
            mock_api_call.return_value = MagicMock()
            mock_get_text.return_value = '{"narrative": "E2E Flash Story!", "state_changes": {}, "player_character_data": {"name": "E2E Hero"}}'

            # Act 1: User saves gemini-2.5-flash preference
            settings_response = self.client.post(
                "/api/settings",
                headers=self.auth_headers,
                data=json.dumps({"gemini_model": "gemini-2.5-flash"}),
            )

            # Verify settings were saved with error details for CI debugging
            if settings_response.status_code != 200:
                response_data = settings_response.get_data(as_text=True)
                self.fail(
                    f"Settings save failed with {settings_response.status_code}: {response_data}"
                )
            self.assertEqual(settings_response.status_code, 200)

            # Act 2: User retrieves settings (to verify persistence)
            get_response = self.client.get("/api/settings", headers=self.auth_headers)
            if get_response.status_code != 200:
                response_data = get_response.get_data(as_text=True)
                self.fail(
                    f"Settings get failed with {get_response.status_code}: {response_data}"
                )
            self.assertEqual(get_response.status_code, 200)
            saved_settings = json.loads(get_response.data)
            self.assertEqual(saved_settings.get("gemini_model"), "gemini-2.5-flash")

            # Act 3: User creates campaign (should use gemini-2.5-flash)
            campaign_data = {
                "title": "E2E Flash Campaign",
                "character": "E2E Hero",
                "setting": "E2E World",
                "description": "End-to-end test with flash model",
                "selected_prompts": ["narrative"],
                "custom_options": [],
                "attribute_system": "D&D",
            }

            campaign_response = self.client.post(
                "/api/campaigns",
                headers=self.auth_headers,
                data=json.dumps(campaign_data),
            )

            # Assert
            self.assertEqual(campaign_response.status_code, 201)

            # Verify flash model was used
            mock_api_call.assert_called_once()
            call_args = mock_api_call.call_args
            model_used = call_args[0][1]  # Second positional argument is model
            self.assertEqual(model_used, "gemini-2.5-flash")

    def test_complete_user_journey_pro_model(self):
        """🟢 E2E: Complete user journey from settings to campaign with pro model"""

        # Only mock the expensive external API call
        with (
            patch("gemini_service._call_gemini_api") as mock_api_call,
            patch("gemini_service._get_text_from_response") as mock_get_text,
        ):
            # Arrange
            mock_api_call.return_value = MagicMock()
            mock_get_text.return_value = '{"narrative": "E2E Pro Story!", "state_changes": {}, "player_character_data": {"name": "E2E Pro Hero"}}'

            # Act 1: User saves gemini-2.5-pro preference
            settings_response = self.client.post(
                "/api/settings",
                headers=self.auth_headers,
                data=json.dumps({"gemini_model": "gemini-2.5-pro"}),
            )

            # Verify settings were saved
            self.assertEqual(settings_response.status_code, 200)

            # Act 2: User creates campaign (should use gemini-2.5-pro)
            campaign_data = {
                "title": "E2E Pro Campaign",
                "character": "E2E Pro Hero",
                "setting": "E2E Pro World",
                "description": "End-to-end test with pro model",
                "selected_prompts": ["narrative"],
                "custom_options": [],
                "attribute_system": "D&D",
            }

            campaign_response = self.client.post(
                "/api/campaigns",
                headers=self.auth_headers,
                data=json.dumps(campaign_data),
            )

            # Assert
            self.assertEqual(campaign_response.status_code, 201)

            # Verify pro model was used
            mock_api_call.assert_called_once()
            call_args = mock_api_call.call_args
            model_used = call_args[0][1]  # Second positional argument is model
            self.assertEqual(model_used, "gemini-2.5-pro")

    def test_settings_change_persistence_across_sessions(self):
        """🟢 E2E: Settings changes persist across multiple user sessions"""

        # Session 1: User sets flash model
        session1_response = self.client.post(
            "/api/settings",
            headers=self.auth_headers,
            data=json.dumps({"gemini_model": "gemini-2.5-flash"}),
        )
        self.assertEqual(session1_response.status_code, 200)

        # Session 2: User retrieves settings
        session2_response = self.client.get("/api/settings", headers=self.auth_headers)
        self.assertEqual(session2_response.status_code, 200)
        settings = json.loads(session2_response.data)
        self.assertEqual(settings.get("gemini_model"), "gemini-2.5-flash")

        # Session 3: User changes to pro model
        session3_response = self.client.post(
            "/api/settings",
            headers=self.auth_headers,
            data=json.dumps({"gemini_model": "gemini-2.5-pro"}),
        )
        self.assertEqual(session3_response.status_code, 200)

        # Session 4: User retrieves updated settings
        session4_response = self.client.get("/api/settings", headers=self.auth_headers)
        self.assertEqual(session4_response.status_code, 200)
        updated_settings = json.loads(session4_response.data)
        self.assertEqual(updated_settings.get("gemini_model"), "gemini-2.5-pro")

    def test_multiple_users_independent_settings(self):
        """🟢 E2E: Different users maintain independent settings"""

        # User 1 settings
        user1_headers = {**self.auth_headers, "X-Test-User-ID": "e2e-user-1"}
        user1_response = self.client.post(
            "/api/settings",
            headers=user1_headers,
            data=json.dumps({"gemini_model": "gemini-2.5-flash"}),
        )
        self.assertEqual(user1_response.status_code, 200)

        # User 2 settings
        user2_headers = {**self.auth_headers, "X-Test-User-ID": "e2e-user-2"}
        user2_response = self.client.post(
            "/api/settings",
            headers=user2_headers,
            data=json.dumps({"gemini_model": "gemini-2.5-pro"}),
        )
        self.assertEqual(user2_response.status_code, 200)

        # Verify User 1 still has flash
        user1_get = self.client.get("/api/settings", headers=user1_headers)
        user1_settings = json.loads(user1_get.data)
        self.assertEqual(user1_settings.get("gemini_model"), "gemini-2.5-flash")

        # Verify User 2 still has pro
        user2_get = self.client.get("/api/settings", headers=user2_headers)
        user2_settings = json.loads(user2_get.data)
        self.assertEqual(user2_settings.get("gemini_model"), "gemini-2.5-pro")

    @patch("gemini_service._call_gemini_api")
    @patch("gemini_service._get_text_from_response")
    def test_campaign_creation_with_model_switching(self, mock_get_text, mock_api_call):
        """🟢 E2E: User can switch models and create campaigns with each"""

        # Arrange
        mock_api_call.return_value = MagicMock()
        mock_get_text.return_value = '{"narrative": "Switching story!", "state_changes": {}, "player_character_data": {"name": "Switch Hero"}}'

        campaign_data = {
            "title": "Model Switch Campaign",
            "character": "Switch Hero",
            "setting": "Switch World",
            "description": "Testing model switching",
            "selected_prompts": ["narrative"],
            "custom_options": [],
            "attribute_system": "D&D",
        }

        # Act 1: Set flash model and create campaign
        self.client.post(
            "/api/settings",
            headers=self.auth_headers,
            data=json.dumps({"gemini_model": "gemini-2.5-flash"}),
        )

        response1 = self.client.post(
            "/api/campaigns", headers=self.auth_headers, data=json.dumps(campaign_data)
        )

        # Verify flash was used
        self.assertEqual(response1.status_code, 201)
        flash_call_args = mock_api_call.call_args
        self.assertEqual(flash_call_args[0][1], "gemini-2.5-flash")

        # Reset mock for next call
        mock_api_call.reset_mock()

        # Act 2: Set pro model and create another campaign
        self.client.post(
            "/api/settings",
            headers=self.auth_headers,
            data=json.dumps({"gemini_model": "gemini-2.5-pro"}),
        )

        response2 = self.client.post(
            "/api/campaigns", headers=self.auth_headers, data=json.dumps(campaign_data)
        )

        # Verify pro was used
        self.assertEqual(response2.status_code, 201)
        pro_call_args = mock_api_call.call_args
        self.assertEqual(pro_call_args[0][1], "gemini-2.5-pro")


if __name__ == "__main__":
    print("🔵 Layer 4: Running end-to-end tests with real services")
    print("📝 NOTE: External APIs are mocked to control costs")
    unittest.main()
