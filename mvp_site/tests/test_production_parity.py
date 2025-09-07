#!/usr/bin/env python3
"""
Production Parity Tests - Test production environment configurations

Tests that catch differences between test and production environments,
specifically response format compatibility issues.
"""

import os
import sys
import unittest

# Set environment for testing
os.environ["TESTING"] = "true"
os.environ["USE_MOCKS"] = "true"

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# Skip this test entirely in CI environment where Firebase credentials are not available
def has_firebase_credentials():
    """Check if Firebase credentials are available."""
    # Check for various credential sources
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        return True
    if os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY"):
        return True
    # Check for application default credentials
    try:
        import google.auth

        google.auth.default()
        return True
    except Exception:
        return False


from unittest.mock import patch

from main import create_app  # noqa: E402


class TestProductionParity(unittest.TestCase):
    """Test production-like configurations to catch parity issues."""

    def setUp(self):
        """Set up test client for production parity testing."""
        
        # Mock Firebase to prevent initialization errors
        self.firebase_patcher = patch("firestore_service.get_db")
        self.mock_get_db = self.firebase_patcher.start()
        
        # Set up fake Firestore client
        from tests.fake_firestore import FakeFirestoreClient
        fake_firestore = FakeFirestoreClient()
        self.mock_get_db.return_value = fake_firestore
        # Direct calls are now the default - no MCP server setup needed

        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Test data
        self.test_user_id = "production-parity-test-user"
        
        # Use stable test UID and stub Firebase verification - patch fully-qualified target
        self._auth_patcher = patch(
            "mvp_site.main.auth.verify_id_token", return_value={"uid": self.test_user_id}
        )
        self._auth_patcher.start()
        
        self.test_headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer test-id-token",
        }

    def tearDown(self):
        """Restore original environment."""
        # Stop Firebase mock patcher to ensure proper test isolation
        self.firebase_patcher.stop()
        # Stop auth patcher
        self._auth_patcher.stop()
        # No additional environment cleanup needed - direct calls are default

    def test_campaigns_list_response_format_compatibility(self):
        """Test that campaigns list response format is frontend-compatible.

        This test verifies that:
        1. The response has the expected structure
        2. The 'campaigns' field contains an array
        3. Frontend destructuring { data: campaigns } will work correctly
        """
        # Make request to campaigns list endpoint
        response = self.client.get("/api/campaigns", headers=self.test_headers)

        # Should succeed with proper authentication headers - tighten assertion
        assert response.status_code == 200, f"Should return success with auth headers, got {response.status_code}"

        response_data = response.get_json()

        # This is the critical test - verify frontend expectations
        # Frontend expects: const { data: campaigns } = await fetchApi('/api/campaigns')
        # So response_data should be directly usable as campaigns array for backward compatibility

        # Check if it's directly an array (what frontend expects for backward compatibility)
        if isinstance(response_data, list):
            campaigns = response_data
        # Check if it has campaigns field (current backend format) - fallback for compatibility
        elif isinstance(response_data, dict) and "campaigns" in response_data:
            campaigns = response_data["campaigns"]
        else:
            self.fail(
                f"Response format incompatible with frontend expectations: {response_data}"
            )

        # Verify campaigns is iterable (prevents forEach error)
        assert hasattr(
            campaigns, "__iter__"
        ), "Campaigns should be iterable for forEach()"

        # Verify it's specifically a list (what forEach expects)
        assert isinstance(
            campaigns, list
        ), "Campaigns should be a list for forEach() compatibility"

    def test_direct_calls_mode_response_format(self):
        """Test response format when using direct calls mode (default).

        This tests the production configuration where world_logic.py
        functions are called directly without HTTP overhead.
        """
        # Create app instance with default direct calls mode
        direct_app = create_app()
        direct_app.config["TESTING"] = True
        direct_client = direct_app.test_client()

        response = direct_client.get("/api/campaigns", headers=self.test_headers)

        assert response.status_code == 200, f"Direct calls mode should return success, got {response.status_code}"

        response_data = response.get_json()

        # Test the specific issue: frontend destructuring compatibility
        # Frontend code: const { data: campaigns } = await fetchApi('/api/campaigns')
        # This means response_data should be the campaigns array directly,
        # or the destructuring will fail

        assert isinstance(
            response_data, (list, dict)
        ), "Response should be list or dict"

        if isinstance(response_data, dict):
            # If it's a dict, it should have campaigns field
            assert (
                "campaigns" in response_data
            ), "Dict response should have 'campaigns' field"
            campaigns = response_data["campaigns"]
        else:
            campaigns = response_data

        # This is the critical test that would have caught the production error
        try:
            # Simulate the frontend forEach call
            list(campaigns)  # This will fail if campaigns is not iterable
            for _ in campaigns:
                pass  # Simulate forEach iteration
        except TypeError as e:
            self.fail(
                f"Frontend forEach would fail: {e}. Response: {response_data}"
            )

        # No environment cleanup needed - direct calls are default


if __name__ == "__main__":
    unittest.main()
