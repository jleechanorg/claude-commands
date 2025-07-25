"""
Testing framework for service provider abstraction.
Enables seamless switching between mock and real services for testing.
"""

from .config import TestConfig
from .factory import (
    get_current_provider,
    get_service_provider,
    reset_global_provider,
    set_service_provider,
)
from .real_provider import RealServiceProvider
from .service_provider import TestServiceProvider

# Try to import the full mock provider, fall back to simple one
try:
    from .mock_provider import MockServiceProvider
except ImportError:
    from .simple_mock_provider import SimpleMockServiceProvider as MockServiceProvider


__all__ = [
    "TestServiceProvider",
    "MockServiceProvider",
    "RealServiceProvider",
    "TestConfig",
    "get_service_provider",
    "get_current_provider",
    "set_service_provider",
    "reset_global_provider",
]
