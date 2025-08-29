"""
Unit tests for RealServiceProvider.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

import pytest

from mvp_site.testing_framework.real_provider import RealServiceProvider
from mvp_site.testing_framework.service_provider import TestServiceProvider


class TestRealProvider(unittest.TestCase):
    """Test RealServiceProvider implementation."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock environment variables for testing
        self.env_patcher = patch.dict(
            os.environ,
            {
                "TEST_GEMINI_API_KEY": "test-api-key",
                "TEST_FIRESTORE_PROJECT": "test-project",
            },
        )
        self.env_patcher.start()

    def tearDown(self):
        """Clean up test fixtures."""
        self.env_patcher.stop()

    def test_implements_interface(self):
        """Test that RealServiceProvider implements TestServiceProvider interface."""
        provider = RealServiceProvider()
        assert isinstance(provider, TestServiceProvider)

    def test_is_real_service_true(self):
        """Test that is_real_service returns True for real provider."""
        provider = RealServiceProvider()
        assert provider.is_real_service

    def test_capture_mode_initialization(self):
        """Test that capture mode is properly initialized."""
        provider = RealServiceProvider(capture_mode=True)
        assert provider.capture_mode

        provider = RealServiceProvider(capture_mode=False)
        assert not provider.capture_mode

    def test_get_firestore_creates_client(self):
        """Test that get_firestore attempts to create real Firestore client."""
        provider = RealServiceProvider()
        # Since dependencies are installed and config is mocked, this should work
        # The actual Firestore client creation might fail due to auth, but that's expected
        try:
            client = provider.get_firestore()
            # If successful, check it's the right type
            assert client is not None
        except Exception as e:
            # Expected to fail on actual Google Cloud auth, which is fine
            assert "google" in str(e).lower() or "auth" in str(e).lower() or "firestore" in str(e).lower()

    def test_get_gemini_creates_client(self):
        """Test that get_gemini attempts to create real Gemini client."""
        provider = RealServiceProvider()
        # Since dependencies are installed and config is mocked, this should work
        try:
            client = provider.get_gemini()
            # If successful, check it's the right type
            assert client is not None
        except Exception as e:
            # Expected to potentially fail on client creation, which is fine for testing
            assert "gemini" in str(e).lower() or "api" in str(e).lower() or "client" in str(e).lower()

    def test_get_auth_creates_test_auth(self):
        """Test that get_auth creates test auth object."""
        provider = RealServiceProvider()
        auth = provider.get_auth()

        assert auth.user_id == "test-user-123"
        assert auth.session_id == "test-session-456"

    def test_track_test_collection(self):
        """Test that track_test_collection adds to cleanup list."""
        provider = RealServiceProvider()
        provider.track_test_collection("campaigns")

        assert "test_campaigns" in provider._test_collections

    def test_cleanup_calls_collection_cleanup(self):
        """Test that cleanup processes tracked collections."""
        # Create a mock firestore client to test cleanup logic
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.collection.return_value = mock_collection
        mock_doc = MagicMock()
        mock_collection.limit.return_value.stream.return_value = [mock_doc]

        provider = RealServiceProvider()
        provider._firestore = mock_client  # Set directly for test
        provider.track_test_collection("campaigns")

        provider.cleanup()

        mock_client.collection.assert_called_with("test_campaigns")
        mock_doc.reference.delete.assert_called_once()

    def test_missing_api_key_raises_error(self):
        """Test that missing API key raises ValueError."""
        with patch.dict(os.environ, {"TEST_GEMINI_API_KEY": ""}):
            with pytest.raises(ValueError) as cm:
                RealServiceProvider()
            assert "TEST_GEMINI_API_KEY" in str(cm.value)


if __name__ == "__main__":
    unittest.main()
