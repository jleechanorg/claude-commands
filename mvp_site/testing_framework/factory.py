"""
Service provider factory for creating appropriate providers based on configuration.
Manages global provider state for tests.
"""

import os
import sys

# Ensure the project root is in Python path for imports
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from .real_provider import RealServiceProvider
from .service_provider import TestServiceProvider

# Try to import the full mock provider, fall back to simple one
try:
    from .mock_provider import MockServiceProvider

    _use_full_mocks = True
except ImportError:
    from .simple_mock_provider import SimpleMockServiceProvider as MockServiceProvider

    _use_full_mocks = False


def get_service_provider(mode: str | None = None) -> TestServiceProvider:
    """Create appropriate service provider based on TEST_MODE."""
    if mode is None:
        mode = os.getenv("TEST_MODE", "mock")

    if mode == "mock":
        return MockServiceProvider()
    if mode in ["real", "capture"]:
        return RealServiceProvider(capture_mode=(mode == "capture"))
    raise ValueError(f"Invalid TEST_MODE: {mode}. Must be 'mock', 'real', or 'capture'")


# Global provider instance for tests
_current_provider: TestServiceProvider | None = None


def set_service_provider(provider: TestServiceProvider) -> None:
    """Set the global service provider for tests."""
    global _current_provider
    _current_provider = provider


def get_current_provider() -> TestServiceProvider:
    """Get the current service provider, creating default if needed."""
    global _current_provider
    if _current_provider is None:
        _current_provider = get_service_provider()
    return _current_provider


def reset_global_provider() -> None:
    """Reset the global provider (useful for test cleanup)."""
    global _current_provider
    if _current_provider:
        _current_provider.cleanup()
    _current_provider = None
