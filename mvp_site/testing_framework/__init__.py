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
from .mock_provider import MockServiceProvider
from .real_provider import RealServiceProvider
from .service_provider import TestServiceProvider


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
