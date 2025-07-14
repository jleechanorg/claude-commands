"""
Abstract base class for test service providers.
Defines the interface for switching between mock and real services.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class TestServiceProvider(ABC):
    """Abstract base class for test service providers."""
    
    @abstractmethod
    def get_firestore(self) -> Any:
        """Return Firestore client (mock or real)."""
        pass
    
    @abstractmethod  
    def get_gemini(self) -> Any:
        """Return Gemini client (mock or real)."""
        pass
    
    @abstractmethod
    def get_auth(self) -> Any:
        """Return auth service (mock or real)."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources after test execution."""
        pass
    
    @property
    @abstractmethod
    def is_real_service(self) -> bool:
        """Return True if using real services."""
        pass