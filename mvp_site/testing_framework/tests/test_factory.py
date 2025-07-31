"""
Unit tests for service provider factory.
"""

import os
import sys
import unittest
from unittest.mock import patch

from mvp_site.testing_framework.simple_mock_provider import SimpleMockServiceProvider

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

# Import the same way the factory does to get consistent behavior
import pytest

from mvp_site.testing_framework import factory
from mvp_site.testing_framework.factory import (
    get_current_provider,
    get_service_provider,
    reset_global_provider,
    set_service_provider,
)
from mvp_site.testing_framework.real_provider import RealServiceProvider

# Get the MockServiceProvider class that the factory actually uses
try:
    from mvp_site.testing_framework.factory import ServiceProviderFactory

    factory = ServiceProviderFactory()
    from mvp_site.testing_framework.mock_provider import (
        MockServiceProvider as OriginalMockServiceProvider,
    )

    if factory._use_full_mocks:
        MockProviderClass = OriginalMockServiceProvider
    else:
        from mvp_site.testing_framework.simple_mock_provider import (
            SimpleMockServiceProvider,
        )

        MockProviderClass = SimpleMockServiceProvider
except ImportError:
    from mvp_site.testing_framework.simple_mock_provider import (
        SimpleMockServiceProvider,
    )

    MockProviderClass = SimpleMockServiceProvider


class TestFactory(unittest.TestCase):
    """Test service provider factory functions."""

    def setUp(self):
        """Set up test fixtures."""
        # Reset global state before each test
        reset_global_provider()

        # Mock environment for real provider tests
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
        reset_global_provider()
        self.env_patcher.stop()

    def test_get_service_provider_default_mock(self):
        """Test that get_service_provider returns MockServiceProvider by default."""
        provider = get_service_provider()
        assert isinstance(provider, MockProviderClass)
        assert not provider.is_real_service

    def test_get_service_provider_explicit_mock(self):
        """Test that get_service_provider returns MockServiceProvider for 'mock' mode."""
        provider = get_service_provider("mock")
        assert isinstance(provider, MockProviderClass)
        assert not provider.is_real_service

    def test_get_service_provider_real_mode(self):
        """Test that get_service_provider returns RealServiceProvider for 'real' mode."""
        provider = get_service_provider("real")
        assert isinstance(provider, RealServiceProvider)
        assert not provider.capture_mode

    def test_get_service_provider_capture_mode(self):
        """Test that get_service_provider returns RealServiceProvider with capture mode."""
        provider = get_service_provider("capture")
        assert isinstance(provider, RealServiceProvider)
        assert provider.capture_mode

    def test_get_service_provider_invalid_mode(self):
        """Test that get_service_provider raises ValueError for invalid mode."""
        with pytest.raises(ValueError) as cm:
            get_service_provider("invalid")
        assert "Invalid TEST_MODE" in str(cm.value)

    @patch.dict(os.environ, {"TEST_MODE": "real"})
    def test_get_service_provider_from_env(self):
        """Test that get_service_provider reads from TEST_MODE environment variable."""
        provider = get_service_provider()
        assert isinstance(provider, RealServiceProvider)

    def test_set_and_get_current_provider(self):
        """Test setting and getting the current provider."""
        mock_provider = MockProviderClass()
        set_service_provider(mock_provider)

        current = get_current_provider()
        assert current is mock_provider

    def test_get_current_provider_creates_default(self):
        """Test that get_current_provider creates default if none set."""
        current = get_current_provider()
        assert isinstance(current, MockProviderClass)
        assert not current.is_real_service

    def test_get_current_provider_consistent(self):
        """Test that get_current_provider returns same instance on multiple calls."""
        current1 = get_current_provider()
        current2 = get_current_provider()
        assert current1 is current2

    def test_reset_global_provider(self):
        """Test that reset_global_provider clears the global state."""
        # Set a provider
        mock_provider = MockProviderClass()
        set_service_provider(mock_provider)

        # Verify it's set
        current = get_current_provider()
        assert current is mock_provider

        # Reset
        reset_global_provider()

        # Verify new instance is created
        new_current = get_current_provider()
        assert new_current is not mock_provider


if __name__ == "__main__":
    unittest.main()
