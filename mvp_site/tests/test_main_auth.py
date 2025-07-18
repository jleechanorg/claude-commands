"""
Comprehensive tests for authentication middleware in main.py.
Tests the check_token decorator with various authentication scenarios.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

# Mock firebase_admin before imports
mock_firebase_admin = MagicMock()
mock_firestore = MagicMock()
mock_auth = MagicMock()
mock_firebase_admin.firestore = mock_firestore
mock_firebase_admin.auth = mock_auth

# Setup module mocks
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.modules["firebase_admin"] = mock_firebase_admin
sys.modules["firebase_admin.firestore"] = mock_firestore
sys.modules["firebase_admin.auth"] = mock_auth

# Import after mocking
from main import (
    DEFAULT_TEST_USER,
    HEADER_AUTH,
    HEADER_TEST_BYPASS,
    HEADER_TEST_USER_ID,
    KEY_ERROR,
    KEY_MESSAGE,
    KEY_SUCCESS,
    create_app,
)


class TestAuthenticationMiddleware(unittest.TestCase):
    """Test authentication middleware and check_token decorator."""

    def setUp(self):
        """Set up test client."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Reset mocks
        mock_firebase_admin.auth.verify_id_token.reset_mock()

    def test_auth_bypass_in_testing_mode(self):
        """Test that auth bypass works in testing mode."""
        test_headers = {
            HEADER_TEST_BYPASS: "true",
            HEADER_TEST_USER_ID: "custom-test-user",
        }

        # Mock firestore service to avoid actual calls
        with patch("main.firestore_service") as mock_firestore_service:
            mock_firestore_service.get_campaigns_for_user.return_value = []

            response = self.client.get("/api/campaigns", headers=test_headers)

            self.assertEqual(response.status_code, 200)
            # Should call with the custom user ID from header
            mock_firestore_service.get_campaigns_for_user.assert_called_once_with(
                "custom-test-user"
            )

    def test_auth_bypass_uses_default_user(self):
        """Test that auth bypass uses default user when no custom user specified."""
        test_headers = {
            HEADER_TEST_BYPASS: "true"
            # No HEADER_TEST_USER_ID provided
        }

        with patch("main.firestore_service") as mock_firestore_service:
            mock_firestore_service.get_campaigns_for_user.return_value = []

            response = self.client.get("/api/campaigns", headers=test_headers)

            self.assertEqual(response.status_code, 200)
            # Should use DEFAULT_TEST_USER
            mock_firestore_service.get_campaigns_for_user.assert_called_once_with(
                DEFAULT_TEST_USER
            )

    def test_no_auth_token_provided(self):
        """Test response when no auth token is provided."""
        # Don't set testing mode, no auth headers
        self.app.config["TESTING"] = False

        response = self.client.get("/api/campaigns")

        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertIn(KEY_MESSAGE, data)
        self.assertIn("No token provided", data[KEY_MESSAGE])

    def test_valid_firebase_token(self):
        """Test successful authentication with valid Firebase token."""
        # Don't set testing mode
        self.app.config["TESTING"] = False

        auth_headers = {HEADER_AUTH: "Bearer valid-firebase-token"}

        with (
            patch("main.auth.verify_id_token") as mock_verify_id_token,
            patch("main.firestore_service") as mock_firestore_service,
        ):
            # Mock successful token verification
            mock_verify_id_token.return_value = {
                "uid": "firebase-user-123",
                "email": "test@example.com",
            }
            mock_firestore_service.get_campaigns_for_user.return_value = []

            response = self.client.get("/api/campaigns", headers=auth_headers)

            self.assertEqual(response.status_code, 200)
            # Should call with Firebase user ID
            mock_firestore_service.get_campaigns_for_user.assert_called_once_with(
                "firebase-user-123"
            )
            # Should verify the token
            mock_verify_id_token.assert_called_once_with("valid-firebase-token")

    def test_invalid_firebase_token(self):
        """Test authentication failure with invalid Firebase token."""
        # Don't set testing mode
        self.app.config["TESTING"] = False

        # Mock token verification failure
        mock_firebase_admin.auth.verify_id_token.side_effect = Exception(
            "Invalid token"
        )

        auth_headers = {HEADER_AUTH: "Bearer invalid-firebase-token"}

        response = self.client.get("/api/campaigns", headers=auth_headers)

        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertFalse(data[KEY_SUCCESS])
        self.assertIn(KEY_ERROR, data)
        self.assertIn("Auth failed", data[KEY_ERROR])
        self.assertIn("Invalid token", data[KEY_ERROR])

    def test_malformed_auth_header(self):
        """Test authentication with malformed auth header."""
        # Don't set testing mode
        self.app.config["TESTING"] = False

        # Mock token verification - should not be called due to malformed header
        mock_firebase_admin.auth.verify_id_token.return_value = {"uid": "test-user"}

        auth_headers = {HEADER_AUTH: "malformed-header-without-bearer"}

        response = self.client.get("/api/campaigns", headers=auth_headers)

        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertFalse(data[KEY_SUCCESS])
        self.assertIn(KEY_ERROR, data)

    def test_empty_auth_header(self):
        """Test authentication with empty auth header."""
        # Don't set testing mode
        self.app.config["TESTING"] = False

        auth_headers = {HEADER_AUTH: ""}

        response = self.client.get("/api/campaigns", headers=auth_headers)

        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertIn(KEY_MESSAGE, data)
        self.assertIn("No token provided", data[KEY_MESSAGE])

    def test_auth_with_multiple_space_bearer_token(self):
        """Test authentication with Bearer token containing multiple spaces."""
        # Don't set testing mode
        self.app.config["TESTING"] = False

        # Mock successful token verification
        mock_firebase_admin.auth.verify_id_token.return_value = {"uid": "test-user-456"}

        auth_headers = {HEADER_AUTH: "Bearer  token-with-spaces  "}

        with patch("main.firestore_service") as mock_firestore_service:
            mock_firestore_service.get_campaigns_for_user.return_value = []

            response = self.client.get("/api/campaigns", headers=auth_headers)

            self.assertEqual(response.status_code, 200)
            # Should extract the last part after split
            mock_firebase_admin.auth.verify_id_token.assert_called_once_with("")

    def test_auth_bypass_false_in_testing_mode(self):
        """Test that auth bypass doesn't work when header is 'false'."""
        test_headers = {
            HEADER_TEST_BYPASS: "false",
            HEADER_TEST_USER_ID: "custom-test-user",
        }

        response = self.client.get("/api/campaigns", headers=test_headers)

        self.assertEqual(response.status_code, 401)
        data = response.get_json()
        self.assertIn(KEY_MESSAGE, data)
        self.assertIn("No token provided", data[KEY_MESSAGE])

    def test_auth_bypass_mixed_case(self):
        """Test that auth bypass works with mixed case 'True'."""
        test_headers = {
            HEADER_TEST_BYPASS: "True",
            HEADER_TEST_USER_ID: "case-test-user",
        }

        with patch("main.firestore_service") as mock_firestore_service:
            mock_firestore_service.get_campaigns_for_user.return_value = []

            response = self.client.get("/api/campaigns", headers=test_headers)

            self.assertEqual(response.status_code, 200)
            mock_firestore_service.get_campaigns_for_user.assert_called_once_with(
                "case-test-user"
            )

    def test_auth_required_on_all_api_routes(self):
        """Test that authentication is required on all API routes."""
        # Don't set testing mode
        self.app.config["TESTING"] = False

        # List of routes that require authentication
        protected_routes = [
            ("/api/campaigns", "GET"),
            ("/api/campaigns/test-id", "GET"),
            ("/api/campaigns", "POST"),
            ("/api/campaigns/test-id", "PATCH"),
            ("/api/campaigns/test-id/interaction", "POST"),
            ("/api/campaigns/test-id/export", "GET"),
        ]

        for route, method in protected_routes:
            with self.subTest(route=route, method=method):
                if method == "GET":
                    response = self.client.get(route)
                elif method == "POST":
                    response = self.client.post(route, json={})
                elif method == "PATCH":
                    response = self.client.patch(route, json={})

                self.assertEqual(response.status_code, 401)
                data = response.get_json()
                self.assertIn(KEY_MESSAGE, data)
                self.assertIn("No token provided", data[KEY_MESSAGE])

    def test_firebase_token_extraction_edge_cases(self):
        """Test Firebase token extraction with various edge cases."""
        # Don't set testing mode
        self.app.config["TESTING"] = False

        # Test cases for different header formats
        test_cases = [
            ("Bearer token123", "token123"),
            ("Bearer ", ""),  # Empty token after Bearer
            ("Bearer token with spaces", "spaces"),  # Multiple spaces - takes last part
            ("Bearer token-with-dashes", "token-with-dashes"),
            ("Bearer token_with_underscores", "token_with_underscores"),
        ]

        for header_value, expected_token in test_cases:
            with self.subTest(header=header_value):
                # Mock token verification to capture what token is passed
                mock_firebase_admin.auth.verify_id_token.reset_mock()
                mock_firebase_admin.auth.verify_id_token.return_value = {
                    "uid": "test-user"
                }

                auth_headers = {HEADER_AUTH: header_value}

                with patch("main.firestore_service") as mock_firestore_service:
                    mock_firestore_service.get_campaigns_for_user.return_value = []

                    response = self.client.get("/api/campaigns", headers=auth_headers)

                    if expected_token:
                        self.assertEqual(response.status_code, 200)
                        mock_firebase_admin.auth.verify_id_token.assert_called_once_with(
                            expected_token
                        )
                    else:
                        # Empty token should still try to verify but might fail
                        mock_firebase_admin.auth.verify_id_token.assert_called_once_with(
                            expected_token
                        )


if __name__ == "__main__":
    unittest.main()
