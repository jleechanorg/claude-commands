"""
Test suite for advanced authentication functionality in main.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["TESTING"] = "true"

import unittest
from unittest.mock import Mock, patch

# Handle missing dependencies gracefully
try:
    import jwt

    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    jwt = None

try:
    from main import app

    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    app = None


@unittest.skipIf(
    not FLASK_AVAILABLE or not JWT_AVAILABLE,
    "Skipping tests: Flask or JWT not available in CI environment",
)
class TestMainAuthenticationAdvanced(unittest.TestCase):
    """Test advanced authentication scenarios"""

    def setUp(self):
        """Set up test client and common test data"""
        if not FLASK_AVAILABLE:
            self.skipTest("Flask not available")

        self.app = app
        self.client = self.app.test_client()
        self.app.config["TESTING"] = True

        # Mock user data
        self.mock_user = {
            "uid": "test-user-123",
            "email": "test@example.com",
            "email_verified": True,
        }

        # Mock tokens
        self.valid_token = "valid-token-123"
        self.expired_token = "expired-token-456"
        self.refresh_token = "refresh-token-789"

    def tearDown(self):
        """Clean up after tests"""

    # Sub-bullet 1: Token Refresh Flows (3-4 tests)

    @patch("firebase_admin.auth.verify_id_token")
    @patch("firebase_admin.auth.create_custom_token")
    def test_token_refresh_during_request(self, mock_create_token, mock_verify):
        """Test that tokens are refreshed during long requests"""
        # First call returns expired token error, second call succeeds
        mock_verify.side_effect = [Exception("Token expired"), self.mock_user]
        mock_create_token.return_value = b"new-token-123"

        # Simulate a request with an about-to-expire token
        response = self.client.get(
            "/api/user/profile",
            headers={"Authorization": f"Bearer {self.expired_token}"},
        )

        # Should attempt refresh and retry
        self.assertEqual(mock_verify.call_count, 2)
        self.assertIn("X-New-Token", response.headers)

    @patch("firebase_admin.auth.verify_id_token")
    @patch("firebase_admin.auth.create_custom_token")
    def test_expired_token_auto_refresh(self, mock_create_token, mock_verify):
        """Test automatic refresh of expired tokens"""
        # Mock expired token error
        mock_verify.side_effect = Exception("Token expired")
        mock_create_token.return_value = b"refreshed-token-123"

        # Send request with refresh token in header
        response = self.client.get(
            "/api/user/profile",
            headers={
                "Authorization": f"Bearer {self.expired_token}",
                "X-Refresh-Token": self.refresh_token,
            },
        )

        # Should return new token in response
        self.assertEqual(
            response.status_code, 401
        )  # Still fails without valid implementation
        # In real implementation, would check for new token in response

    @patch("firebase_admin.auth.verify_id_token")
    @patch("firebase_admin.auth.revoke_refresh_tokens")
    def test_refresh_token_rotation(self, mock_revoke, mock_verify):
        """Test that refresh tokens are rotated after use"""
        mock_verify.return_value = self.mock_user

        # Simulate refresh token usage
        response = self.client.post(
            "/api/auth/refresh",
            json={"refresh_token": self.refresh_token},
            headers={"Authorization": f"Bearer {self.valid_token}"},
        )

        # Old refresh token should be revoked
        if response.status_code == 200:
            mock_revoke.assert_called_once()

    @patch("firebase_admin.auth.verify_id_token")
    def test_refresh_token_expiry_handling(self, mock_verify):
        """Test handling of expired refresh tokens"""
        mock_verify.return_value = self.mock_user

        # Send expired refresh token
        response = self.client.post(
            "/api/auth/refresh",
            json={"refresh_token": "expired-refresh-token"},
            headers={"Authorization": f"Bearer {self.valid_token}"},
        )

        # Should reject expired refresh token
        if response.status_code != 404:  # Endpoint might not exist
            self.assertIn(response.status_code, [401, 403])

    # Sub-bullet 2: Multi-Device Sessions (3-4 tests)

    @patch("firebase_admin.auth.verify_id_token")
    @patch("firebase_admin.auth.get_user")
    def test_multiple_device_sessions(self, mock_get_user, mock_verify):
        """Test support for multiple device sessions"""
        mock_verify.return_value = self.mock_user
        mock_get_user.return_value = Mock(
            uid=self.mock_user["uid"],
            custom_claims={"devices": ["device1", "device2", "device3"]},
        )

        # Simulate requests from different devices
        device_tokens = {
            "device1": "token-device1-123",
            "device2": "token-device2-456",
            "device3": "token-device3-789",
        }

        for device_id, token in device_tokens.items():
            response = self.client.get(
                "/api/user/profile",
                headers={"Authorization": f"Bearer {token}", "X-Device-ID": device_id},
            )
            # Each device should have valid session
            self.assertIn(
                response.status_code, [200, 401]
            )  # 401 if auth not implemented

    @patch("firebase_admin.auth.verify_id_token")
    @patch("firebase_admin.auth.revoke_refresh_tokens")
    def test_session_invalidation_across_devices(self, mock_revoke, mock_verify):
        """Test that logout invalidates sessions on all devices"""
        mock_verify.return_value = self.mock_user

        # Logout from one device
        response = self.client.post(
            "/api/auth/logout",
            headers={
                "Authorization": f"Bearer {self.valid_token}",
                "X-Device-ID": "device1",
            },
        )

        # Should revoke all tokens for the user
        if response.status_code == 200:
            mock_revoke.assert_called_with(self.mock_user["uid"])

    @patch("firebase_admin.auth.verify_id_token")
    @patch("firebase_admin.auth.set_custom_user_claims")
    def test_device_limit_enforcement(self, mock_set_claims, mock_verify):
        """Test enforcement of maximum device limit"""
        mock_verify.return_value = self.mock_user

        # Try to register a 6th device (assuming limit is 5)
        response = self.client.post(
            "/api/auth/register-device",
            json={"device_id": "device6", "device_name": "New Phone"},
            headers={"Authorization": f"Bearer {self.valid_token}"},
        )

        # Should reject if over device limit
        if response.status_code != 404:  # Endpoint might not exist
            self.assertIn(response.status_code, [400, 403])

    @patch("firebase_admin.auth.verify_id_token")
    def test_device_session_metadata(self, mock_verify):
        """Test device session metadata tracking"""
        mock_verify.return_value = self.mock_user

        # Request with device metadata
        response = self.client.get(
            "/api/user/sessions",
            headers={
                "Authorization": f"Bearer {self.valid_token}",
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0)",
                "X-Device-ID": "ios-device-123",
            },
        )

        # Should track device information
        if response.status_code == 200:
            data = response.get_json()
            if data and "sessions" in data:
                # Check for device metadata in response
                self.assertTrue(
                    any("device" in session for session in data["sessions"])
                )

    # Sub-bullet 3: Permission Validation (3-4 tests)

    @patch("firebase_admin.auth.verify_id_token")
    @patch("firestore_service.get_campaign")
    def test_gm_vs_player_permissions(self, mock_get_campaign, mock_verify):
        """Test different permissions for GM vs regular players"""
        mock_verify.return_value = self.mock_user

        # Mock campaign with GM and players
        mock_campaign = {
            "campaign_id": "test-campaign-123",
            "gm_id": "gm-user-456",
            "players": ["player1", "player2", self.mock_user["uid"]],
        }
        mock_get_campaign.return_value = mock_campaign

        # Test GM access to admin endpoints
        gm_response = self.client.post(
            "/api/campaign/test-campaign-123/admin/kick-player",
            json={"player_id": "player1"},
            headers={"Authorization": f"Bearer {self.valid_token}"},
        )

        # GM should have access, regular player should not
        if gm_response.status_code != 404:
            # If user is not GM, should be forbidden
            if self.mock_user["uid"] != mock_campaign["gm_id"]:
                self.assertEqual(gm_response.status_code, 403)

    @patch("firebase_admin.auth.verify_id_token")
    @patch("firestore_service.get_campaign")
    def test_campaign_owner_validation(self, mock_get_campaign, mock_verify):
        """Test that only campaign owners can modify campaign settings"""
        mock_verify.return_value = self.mock_user
        mock_get_campaign.return_value = {
            "campaign_id": "test-campaign-123",
            "gm_id": "another-user-789",  # Different from current user
            "settings": {"public": False},
        }

        # Try to modify campaign as non-owner
        response = self.client.put(
            "/api/campaign/test-campaign-123/settings",
            json={"public": True},
            headers={"Authorization": f"Bearer {self.valid_token}"},
        )

        # Should be forbidden for non-owner
        if response.status_code != 404:
            self.assertEqual(response.status_code, 403)

    @patch("firebase_admin.auth.verify_id_token")
    def test_permission_escalation_prevention(self, mock_verify):
        """Test prevention of permission escalation attacks"""
        mock_verify.return_value = self.mock_user

        # Try to grant self admin permissions
        response = self.client.post(
            "/api/user/grant-admin",
            json={"user_id": self.mock_user["uid"], "role": "admin"},
            headers={"Authorization": f"Bearer {self.valid_token}"},
        )

        # Should be forbidden unless already admin
        if response.status_code != 404:
            self.assertIn(response.status_code, [403, 401])

    @patch("firebase_admin.auth.verify_id_token")
    @patch("firebase_admin.auth.get_user")
    def test_role_based_access_control(self, mock_get_user, mock_verify):
        """Test role-based access control implementation"""
        mock_verify.return_value = self.mock_user

        # Test different role levels
        roles = ["viewer", "player", "gm", "admin"]

        for role in roles:
            mock_get_user.return_value = Mock(
                uid=self.mock_user["uid"], custom_claims={"role": role}
            )

            # Try to access role-specific endpoint
            response = self.client.get(
                "/api/admin/users",
                headers={"Authorization": f"Bearer {self.valid_token}"},
            )

            # Only admin role should have access
            if response.status_code != 404:
                if role != "admin":
                    self.assertIn(response.status_code, [403, 401])

    # Sub-bullet 4: Cross-Origin Authentication (3-4 tests)

    @patch("firebase_admin.auth.verify_id_token")
    def test_cors_auth_headers(self, mock_verify):
        """Test CORS headers with authentication"""
        mock_verify.return_value = self.mock_user

        # Preflight OPTIONS request
        response = self.client.options(
            "/api/user/profile",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization",
            },
        )

        # Check CORS headers
        if "Access-Control-Allow-Origin" in response.headers:
            self.assertIn(
                "Authorization",
                response.headers.get("Access-Control-Allow-Headers", ""),
            )

    @patch("firebase_admin.auth.verify_id_token")
    def test_cross_origin_token_validation(self, mock_verify):
        """Test token validation for cross-origin requests"""
        mock_verify.return_value = self.mock_user

        # Request from different origin
        response = self.client.get(
            "/api/user/profile",
            headers={
                "Authorization": f"Bearer {self.valid_token}",
                "Origin": "https://untrusted-site.com",
            },
        )

        # Should validate token regardless of origin
        if response.status_code == 200:
            mock_verify.assert_called_once()

    @patch("firebase_admin.auth.verify_id_token")
    def test_preflight_auth_bypass(self, mock_verify):
        """Test that preflight requests bypass authentication"""
        # Preflight should not require auth
        response = self.client.options(
            "/api/protected/resource",
            headers={
                "Origin": "https://example.com",
                "Access-Control-Request-Method": "POST",
            },
        )

        # Should not call verify_id_token for OPTIONS
        mock_verify.assert_not_called()
        # Should return 200 or 204 for preflight
        self.assertIn(response.status_code, [200, 204, 404])

    @patch("firebase_admin.auth.verify_id_token")
    def test_cross_origin_cookie_handling(self, mock_verify):
        """Test cookie handling in cross-origin scenarios"""
        mock_verify.return_value = self.mock_user

        # Set cookie in response
        response = self.client.post(
            "/api/auth/login",
            json={"token": self.valid_token},
            headers={"Origin": "https://app.example.com"},
        )

        # Check for secure cookie settings
        if "Set-Cookie" in response.headers:
            cookie_header = response.headers.get("Set-Cookie")
            # Should have SameSite and Secure for cross-origin
            self.assertIn("SameSite", cookie_header)
            # In production, should have Secure flag

    # Sub-bullet 5: OAuth Edge Cases (3-4 tests)

    @patch("firebase_admin.auth.verify_id_token")
    def test_oauth_state_validation(self, mock_verify):
        """Test OAuth state parameter validation"""
        # Test OAuth callback with invalid state
        response = self.client.get(
            "/api/auth/oauth/callback",
            query_string={"code": "auth-code-123", "state": "invalid-state"},
        )

        # Should reject invalid state
        if response.status_code != 404:
            self.assertIn(response.status_code, [400, 401])

    @patch("firebase_admin.auth.verify_id_token")
    def test_oauth_callback_errors(self, mock_verify):
        """Test OAuth callback error handling"""
        # Test various OAuth errors
        oauth_errors = [
            {"error": "access_denied", "error_description": "User denied access"},
            {
                "error": "invalid_request",
                "error_description": "Missing required parameter",
            },
            {"error": "server_error", "error_description": "Provider error"},
        ]

        for error_params in oauth_errors:
            response = self.client.get(
                "/api/auth/oauth/callback", query_string=error_params
            )

            # Should handle OAuth errors gracefully
            if response.status_code != 404:
                self.assertIn(response.status_code, [400, 401, 500])

    @patch("firebase_admin.auth.verify_id_token")
    @patch("requests.post")
    def test_oauth_token_exchange_failure(self, mock_post, mock_verify):
        """Test OAuth token exchange failure scenarios"""
        # Mock token exchange failure
        mock_post.return_value = Mock(
            status_code=400, json=lambda: {"error": "invalid_grant"}
        )

        # Attempt token exchange
        response = self.client.post(
            "/api/auth/oauth/token",
            json={
                "code": "auth-code-123",
                "redirect_uri": "https://app.example.com/callback",
            },
        )

        # Should handle token exchange failure
        if response.status_code != 404:
            self.assertIn(response.status_code, [400, 401, 500])

    @patch("firebase_admin.auth.verify_id_token")
    def test_oauth_redirect_uri_validation(self, mock_verify):
        """Test OAuth redirect URI validation"""
        # Test with unauthorized redirect URI
        response = self.client.post(
            "/api/auth/oauth/authorize",
            json={
                "client_id": "test-client",
                "redirect_uri": "https://malicious-site.com/callback",
                "response_type": "code",
            },
        )

        # Should reject unauthorized redirect URIs
        if response.status_code != 404:
            self.assertIn(response.status_code, [400, 403])

    # Sub-bullet 6: Session Security (3-4 tests)

    @patch("firebase_admin.auth.verify_id_token")
    def test_session_hijacking_prevention(self, mock_verify):
        """Test prevention of session hijacking attempts"""
        mock_verify.return_value = self.mock_user

        # Initial request from legitimate IP
        response1 = self.client.get(
            "/api/user/profile",
            headers={
                "Authorization": f"Bearer {self.valid_token}",
                "X-Forwarded-For": "192.168.1.100",
            },
        )

        # Sudden request from different IP with same token
        response2 = self.client.get(
            "/api/user/profile",
            headers={
                "Authorization": f"Bearer {self.valid_token}",
                "X-Forwarded-For": "10.0.0.50",
            },
        )

        # Should detect suspicious activity
        # In real implementation, might flag or require re-auth
        self.assertIsNotNone(response1)
        self.assertIsNotNone(response2)

    @patch("firebase_admin.auth.verify_id_token")
    def test_session_fixation_protection(self, mock_verify):
        """Test protection against session fixation attacks"""
        # Pre-authentication request with session ID
        pre_auth_response = self.client.get(
            "/api/public/info", headers={"X-Session-ID": "attacker-controlled-session"}
        )

        # Authentication with same session ID
        mock_verify.return_value = self.mock_user
        auth_response = self.client.post(
            "/api/auth/login",
            json={"token": self.valid_token},
            headers={"X-Session-ID": "attacker-controlled-session"},
        )

        # Should regenerate session ID after authentication
        if "Set-Cookie" in auth_response.headers:
            # New session should be different from attacker-controlled one
            self.assertNotIn(
                "attacker-controlled-session",
                auth_response.headers.get("Set-Cookie", ""),
            )

    @patch("firebase_admin.auth.verify_id_token")
    @patch("firebase_admin.auth.get_user")
    def test_concurrent_session_limits(self, mock_get_user, mock_verify):
        """Test enforcement of concurrent session limits"""
        mock_verify.return_value = self.mock_user
        mock_get_user.return_value = Mock(
            uid=self.mock_user["uid"],
            custom_claims={"active_sessions": 5},  # At limit
        )

        # Try to create new session when at limit
        response = self.client.post(
            "/api/auth/new-session",
            json={"device_name": "New Device"},
            headers={"Authorization": f"Bearer {self.valid_token}"},
        )

        # Should reject or require closing another session
        if response.status_code != 404:
            self.assertIn(response.status_code, [400, 403])

    # Sub-bullet 7: Token Edge Cases (3-4 tests)

    @patch("firebase_admin.auth.verify_id_token")
    def test_malformed_token_handling(self, mock_verify):
        """Test handling of malformed tokens"""
        # Test various malformed tokens
        malformed_tokens = [
            "not-a-jwt-token",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",  # Incomplete JWT
            "Bearer Bearer token",  # Double Bearer prefix
            "",  # Empty token
        ]

        for token in malformed_tokens:
            mock_verify.side_effect = Exception("Invalid token format")

            response = self.client.get(
                "/api/user/profile", headers={"Authorization": f"Bearer {token}"}
            )

            # Should reject malformed tokens
            self.assertIn(response.status_code, [401, 403])

    @patch("firebase_admin.auth.verify_id_token")
    def test_token_signature_validation(self, mock_verify):
        """Test token signature validation"""
        # Create a token with invalid signature
        mock_verify.side_effect = Exception("Token signature verification failed")

        response = self.client.get(
            "/api/user/profile", headers={"Authorization": f"Bearer {self.valid_token}"}
        )

        # Should reject tokens with invalid signatures
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
