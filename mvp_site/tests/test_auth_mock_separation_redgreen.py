"""
RED-GREEN test for AUTH_SKIP_MODE vs MOCK_SERVICES_MODE separation.

This test demonstrates that:
1. Current TESTING mode bypasses production code paths (RED)
2. New separation allows testing real services with auth bypass (GREEN)
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

from tests.fake_firestore import FakeFirestoreClient

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mvp_site'))

import firestore_service


class TestAuthMockSeparation(unittest.TestCase):
    """Test that demonstrates the need for separating auth skip from mock services."""

    def test_current_mock_mode_bypasses_verification(self):
        """GREEN: MOCK_SERVICES_MODE=true bypasses verification for unit tests."""
        # Set new mock services mode
        os.environ["MOCK_SERVICES_MODE"] = "true"
        # Clear old TESTING mode
        if "TESTING" in os.environ:
            del os.environ["TESTING"]

        with patch("firestore_service.get_db") as mock_db:
            # Mock Firestore to return proper tuple format
            mock_doc_ref = MagicMock()
            mock_doc_ref.id = "test-doc-123"
            mock_timestamp = MagicMock()
            mock_add_result = (mock_timestamp, mock_doc_ref)

            mock_db.return_value.collection.return_value.document.return_value.collection.return_value.add.return_value = mock_add_result

            # This bypasses verification due to MOCK_SERVICES_MODE=true
            result = firestore_service.add_story_entry(
                user_id="test-user",
                campaign_id="test-campaign",
                actor="user",
                text="Test story entry",
            )

            # GOOD: This returns None because MOCK_SERVICES_MODE=true bypasses verification for unit tests
            self.assertIsNone(
                result, "Mock services mode bypasses verification, returns None"
            )

            # This is appropriate for unit tests that need speed

    def test_auth_skip_with_real_services(self):
        """GREEN: AUTH_SKIP_MODE=true allows testing real services without auth."""
        # Clear mock mode - we want to test real service logic
        if "MOCK_SERVICES_MODE" in os.environ:
            del os.environ["MOCK_SERVICES_MODE"]
        if "TESTING" in os.environ:
            del os.environ["TESTING"]

        # Set auth skip mode for testing without authentication
        os.environ["AUTH_SKIP_MODE"] = "true"

        with patch("firestore_service.get_db") as mock_db:
            # Use FakeFirestoreClient for realistic behavior


            fake_db = FakeFirestoreClient()
            mock_db.return_value = fake_db

            # Now this should run the REAL production verification flow!
            result = firestore_service.add_story_entry(
                user_id="test-user",
                campaign_id="test-campaign",
                actor="user",
                text="Test story entry",
            )

            # Production mode runs verification and returns None after success
            self.assertIsNone(
                result, "Production mode should run verification and return None"
            )

            # Verify that verification was attempted (this tests the production code path)
            # Check that the fake database contains the written entry
            users_collection = fake_db._collections.get("users")
            self.assertIsNotNone(users_collection, "Should create users collection")

            # Verify data was written to fake database
            user_doc = users_collection._docs.get("test-user")
            self.assertIsNotNone(user_doc, "Should create user document")


if __name__ == "__main__":
    unittest.main()
