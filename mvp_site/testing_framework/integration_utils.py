"""
Integration utilities for updating existing tests to support the Real-Mode Testing Framework.
Provides helpers for gradual migration and backwards compatibility.
"""

import os
import sys
import time
from typing import Any
from unittest.mock import patch

# Import main module - fail fast if not available
import main

from .factory import get_service_provider

# Removed circular import - update_test_imports is defined in this file

# Add the project root to the path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# ============================================================================
# MIGRATION DECORATORS
# ============================================================================


def dual_mode_test(test_func):
    """Decorator to make existing test functions work in dual mode.

    Usage:
        @dual_mode_test
        def test_something(self):
            # Existing test code works unchanged
    """

    def wrapper(self, *args, **kwargs):
        # Setup dual mode if not already done
        if not hasattr(self, "_dual_mode_setup"):
            self._setup_dual_mode()

        return test_func(self, *args, **kwargs)

    return wrapper


def skip_in_real_mode(reason="Test not suitable for real services"):
    """Decorator to skip tests in real mode.

    Usage:
        @skip_in_real_mode("Uses hardcoded test data")
        def test_something(self):
            # This test only runs in mock mode
    """

    def decorator(test_func):
        def wrapper(self, *args, **kwargs):
            provider = get_service_provider()
            if provider.is_real_service:
                self.skipTest(f"Skipped in real mode: {reason}")
            return test_func(self, *args, **kwargs)

        return wrapper

    return decorator


def real_mode_only(reason="Test requires real services"):
    """Decorator for tests that only work with real services.

    Usage:
        @real_mode_only("Tests actual API integration")
        def test_something(self):
            # This test only runs in real mode
    """

    def decorator(test_func):
        def wrapper(self, *args, **kwargs):
            provider = get_service_provider()
            if not provider.is_real_service:
                self.skipTest(f"Skipped in mock mode: {reason}")
            return test_func(self, *args, **kwargs)

        return wrapper

    return decorator


# ============================================================================
# MIXIN CLASSES FOR EXISTING TESTS
# ============================================================================


class DualModeTestMixin:
    """Mixin to add dual-mode support to existing test classes.

    Usage:
        class MyExistingTest(DualModeTestMixin, unittest.TestCase):
            # Existing test methods work unchanged
    """

    def setUp(self):
        """Setup dual-mode support."""
        super().setUp()
        self._setup_dual_mode()

    def tearDown(self):
        """Cleanup dual-mode resources."""
        if hasattr(self, "_test_provider"):
            self._test_provider.cleanup()
        super().tearDown()

    def _setup_dual_mode(self):
        """Initialize dual-mode testing support."""
        self._test_provider = get_service_provider()
        self.is_real_mode = self._test_provider.is_real_service

        # Provide services for backward compatibility
        self.test_firestore = self._test_provider.get_firestore()
        self.test_gemini = self._test_provider.get_gemini()
        self.test_auth = self._test_provider.get_auth()

        # Mark as setup to avoid double initialization
        self._dual_mode_setup = True

        print(f"🔧 Test running in {'REAL' if self.is_real_mode else 'MOCK'} mode")


class MockCompatibilityMixin:
    """Mixin for tests that expect specific mock attributes.

    Provides backward compatibility for tests that reference mock objects directly.
    """

    def setUp(self):
        """Setup mock compatibility layer."""
        super().setUp()
        self._setup_mock_compatibility()

    def _setup_mock_compatibility(self):
        """Setup compatibility attributes for existing mock-based tests."""
        provider = get_service_provider()

        # Common mock attribute names
        self.mock_firestore = provider.get_firestore()
        self.mock_gemini = provider.get_gemini()
        self.mock_auth = provider.get_auth()

        # Legacy attribute names sometimes used
        self.firestore_mock = self.mock_firestore
        self.gemini_mock = self.mock_gemini
        self.auth_mock = self.mock_auth


# ============================================================================
# PATCH HELPERS
# ============================================================================


class SmartPatcher:
    """Context manager that patches services only when needed (mock mode)."""

    def __init__(self, **service_patches):
        """Initialize with service patches.

        Args:
            **service_patches: Dict mapping service names to mock objects
                              e.g., llm_service=mock_gemini
        """
        self.service_patches = service_patches
        self.provider = get_service_provider()
        self.patches = []

    def __enter__(self):
        """Enter context - apply patches only in mock mode."""
        if not self.provider.is_real_service:
            # Mock mode - apply patches
            for service_name, mock_obj in self.service_patches.items():
                if mock_obj is None:
                    # Get mock from provider if not specified
                    if "firestore" in service_name.lower():
                        mock_obj = self.provider.get_firestore()
                    elif "gemini" in service_name.lower():
                        mock_obj = self.provider.get_gemini()
                    elif "auth" in service_name.lower():
                        mock_obj = self.provider.get_auth()

                if mock_obj and hasattr(main, service_name):
                    # Use module-level main import
                    patch_obj = patch(f"main.{service_name}", mock_obj)
                    self.patches.append(patch_obj)
                    patch_obj.__enter__()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context - clean up patches."""
        for patch_obj in reversed(self.patches):
            patch_obj.__exit__(exc_type, exc_val, exc_tb)
        self.patches.clear()


def smart_patch(**service_patches):
    """Smart patching that only applies in mock mode.

    Usage:
        with smart_patch(llm_service=None, firestore_service=None):
            # Code works in both mock and real mode
            # In mock mode: services are patched with framework mocks
            # In real mode: no patching, uses real services
    """
    return SmartPatcher(**service_patches)


# ============================================================================
# CONVERSION HELPERS
# ============================================================================


def convert_test_class(test_class, add_mixins=True):
    """Convert existing test class to dual-mode.

    Args:
        test_class: The test class to convert
        add_mixins: Whether to add dual-mode mixins

    Returns:
        Modified test class
    """
    if add_mixins and not issubclass(test_class, DualModeTestMixin):
        # Add dual-mode support
        test_class.__bases__ = (DualModeTestMixin,) + test_class.__bases__

    # Convert test methods
    for attr_name in dir(test_class):
        if attr_name.startswith("test_"):
            attr = getattr(test_class, attr_name)
            if callable(attr):
                # Apply dual-mode decorator
                setattr(test_class, attr_name, dual_mode_test(attr))

    return test_class


def update_test_imports(_test_module):
    """Update test module to import testing framework.

    Call this at the top of existing test files:

        update_test_imports(__name__)

    Args:
        _test_module: The module name (typically __name__)
    """
    # This is a placeholder for future import manipulation if needed


# ============================================================================
# RESOURCE MANAGEMENT
# ============================================================================


class TestResourceManager:
    """Manages test resources and prevents resource leaks in real mode."""

    def __init__(self):
        self.provider = get_service_provider()
        self.created_resources = []

    def create_test_collection(self, base_name: str) -> str:
        """Create a test-specific collection name."""
        if self.provider.is_real_service:
            # Real mode - use unique names

            collection_name = f"test_{base_name}_{int(time.time())}"
        else:
            # Mock mode - use simple names
            collection_name = f"test_{base_name}"

        self.created_resources.append(("collection", collection_name))
        return collection_name

    def cleanup(self):
        """Clean up created resources."""
        if self.provider.is_real_service:
            firestore = self.provider.get_firestore()
            for resource_type, resource_name in self.created_resources:
                if resource_type == "collection":
                    try:
                        # Delete all documents in the test collection
                        docs = firestore.collection(resource_name).stream()
                        for doc in docs:
                            doc.reference.delete()
                    except Exception as e:
                        print(f"Warning: Failed to cleanup {resource_name}: {e}")

        self.created_resources.clear()


# ============================================================================
# VALIDATION HELPERS
# ============================================================================


def validate_test_environment():
    """Validate that the test environment is properly configured."""
    try:
        provider = get_service_provider()

        # Test basic provider functionality
        provider.get_firestore()
        provider.get_gemini()
        provider.get_auth()

        print(
            f"✅ Test environment validated - Mode: {'REAL' if provider.is_real_service else 'MOCK'}"
        )
        return True

    except Exception as e:
        print(f"❌ Test environment validation failed: {e}")
        return False


def get_test_mode_info() -> dict[str, Any]:
    """Get information about current test mode."""
    provider = get_service_provider()
    return {
        "mode": "real" if provider.is_real_service else "mock",
        "is_real": provider.is_real_service,
        "provider_type": type(provider).__name__,
        "test_mode_env": os.getenv("TEST_MODE", "mock"),
    }
