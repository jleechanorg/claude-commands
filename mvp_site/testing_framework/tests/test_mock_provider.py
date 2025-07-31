"""
Unit tests for MockServiceProvider.
"""

import os
import sys
import unittest

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from mvp_site.mocks.mock_firestore_service import MockFirestoreClient
from mvp_site.mocks.mock_gemini_service import MockGeminiClient
from mvp_site.testing_framework.mock_provider import MockServiceProvider
from mvp_site.testing_framework.service_provider import TestServiceProvider


class TestMockProvider(unittest.TestCase):
    """Test MockServiceProvider implementation."""

    def setUp(self):
        """Set up test fixtures."""
        self.provider = MockServiceProvider()

    def test_implements_interface(self):
        """Test that MockServiceProvider implements TestServiceProvider interface."""
        assert isinstance(self.provider, TestServiceProvider)

    def test_get_firestore_returns_mock(self):
        """Test that get_firestore returns MockFirestoreClient."""
        firestore = self.provider.get_firestore()
        assert isinstance(firestore, MockFirestoreClient)

    def test_get_gemini_returns_mock(self):
        """Test that get_gemini returns MockGeminiClient."""
        gemini = self.provider.get_gemini()
        assert isinstance(gemini, MockGeminiClient)

    def test_get_auth_returns_mock(self):
        """Test that get_auth returns mock auth (currently None)."""
        auth = self.provider.get_auth()
        # Currently returns None, which is fine for mock auth
        assert auth is None

    def test_is_real_service_false(self):
        """Test that is_real_service returns False for mock provider."""
        assert not self.provider.is_real_service

    def test_cleanup_resets_services(self):
        """Test that cleanup resets mock services."""
        # Use firestore to create some data
        firestore = self.provider.get_firestore()
        initial_count = firestore.operation_count

        # Make some operations
        firestore.get_campaigns_for_user("test_user")
        assert firestore.operation_count > initial_count

        # Cleanup should reset
        self.provider.cleanup()
        assert firestore.operation_count == 0

    def test_consistent_instances(self):
        """Test that multiple calls return the same instances."""
        firestore1 = self.provider.get_firestore()
        firestore2 = self.provider.get_firestore()
        assert firestore1 is firestore2

        gemini1 = self.provider.get_gemini()
        gemini2 = self.provider.get_gemini()
        assert gemini1 is gemini2


if __name__ == "__main__":
    unittest.main()
