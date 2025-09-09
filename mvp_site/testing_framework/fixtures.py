"""
Test fixtures for pytest and unittest integration with the Real-Mode Testing Framework.
Provides seamless switching between mock and real services based on TEST_MODE.
"""

import os
import unittest
from collections.abc import Generator

import pytest

from .factory import get_service_provider, reset_global_provider
from .service_provider import TestServiceProvider

# ============================================================================
# PYTEST FIXTURES
# ============================================================================


@pytest.fixture
def service_provider() -> Generator[TestServiceProvider, None, None]:
    """Provide appropriate service provider based on TEST_MODE.

    Usage in pytest:
        def test_something(service_provider):
            firestore = service_provider.get_firestore()
            # Test logic works with mock or real services
    """
    provider = get_service_provider()
    try:
        yield provider
    finally:
        provider.cleanup()


@pytest.fixture
def firestore_client(service_provider: TestServiceProvider):
    """Provide Firestore client (mock or real) based on TEST_MODE."""
    return service_provider.get_firestore()


@pytest.fixture
def gemini_client(service_provider: TestServiceProvider):
    """Provide Gemini client (mock or real) based on TEST_MODE."""
    return service_provider.get_gemini()


@pytest.fixture
def auth_service(service_provider: TestServiceProvider):
    """Provide auth service (mock or real) based on TEST_MODE."""
    return service_provider.get_auth()


@pytest.fixture
def test_mode() -> str:
    """Get current test mode from environment."""
    return os.getenv("TEST_MODE", "mock")


@pytest.fixture
def is_real_service(service_provider: TestServiceProvider) -> bool:
    """Check if using real services."""
    return service_provider.is_real_service


# ============================================================================
# UNITTEST BASE CLASSES
# ============================================================================


class BaseTestCase(unittest.TestCase):
    """Base test case with service provider integration.

    Usage:
        class TestMyFeature(BaseTestCase):
            def test_something(self):
                result = self.firestore.get_document('test/doc')
                # Works with mock or real services
    """

    def setUp(self):
        """Set up test with appropriate service provider."""
        self.provider = get_service_provider()
        self.firestore = self.provider.get_firestore()
        self.gemini = self.provider.get_gemini()
        self.auth = self.provider.get_auth()
        self.is_real = self.provider.is_real_service

    def tearDown(self):
        """Clean up after test."""
        if hasattr(self, "provider"):
            self.provider.cleanup()


class IsolatedTestCase(BaseTestCase):
    """Test case with isolated test environment.

    Each test gets a fresh service provider to ensure complete isolation.
    Use when tests might interfere with each other.
    """

    def setUp(self):
        """Set up with fresh provider and reset global state."""
        reset_global_provider()
        super().setUp()

    def tearDown(self):
        """Clean up and reset global state."""
        super().tearDown()
        reset_global_provider()


# ============================================================================
# HELPER FUNCTIONS FOR MANUAL SETUP
# ============================================================================


def setup_test_services(test_mode: str | None = None) -> TestServiceProvider:
    """Manually set up test services for non-fixture usage.

    Args:
        test_mode: Override TEST_MODE environment variable

    Returns:
        Service provider instance

    Usage:
        provider = setup_test_services('mock')
        try:
            firestore = provider.get_firestore()
            # Use services
        finally:
            provider.cleanup()
    """
    return get_service_provider(test_mode)


def cleanup_test_services(provider: TestServiceProvider) -> None:
    """Manually clean up test services."""
    provider.cleanup()


# ============================================================================
# MIGRATION HELPERS
# ============================================================================


def get_test_client_for_mode(test_mode: str = None):
    """Get appropriate test client based on mode.

    Helper for gradually migrating existing tests.
    """
    if test_mode is None:
        test_mode = os.getenv("TEST_MODE", "mock")

    provider = get_service_provider(test_mode)
    return {
        "provider": provider,
        "firestore": provider.get_firestore(),
        "gemini": provider.get_gemini(),
        "auth": provider.get_auth(),
        "is_real": provider.is_real_service,
    }


# ============================================================================
# BACKWARDS COMPATIBILITY HELPERS
# ============================================================================


class MockCompatibilityMixin:
    """Mixin to help existing tests work with new framework.

    Provides mock-like attributes that delegate to service provider.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not hasattr(self, "provider"):
            self.provider = get_service_provider()

    @property
    def mock_firestore(self):
        """Compatibility property for tests expecting mock_firestore."""
        return self.provider.get_firestore()

    @property
    def mock_gemini(self):
        """Compatibility property for tests expecting mock_gemini."""
        return self.provider.get_gemini()

    @property
    def mock_auth(self):
        """Compatibility property for tests expecting mock_auth."""
        return self.provider.get_auth()
