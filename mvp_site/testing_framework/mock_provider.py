"""
Mock service provider implementation.
Uses existing mock services for testing without external dependencies.
"""

import os
import sys
from typing import Any

# Ensure the project root is in Python path for imports
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mocks.mock_firestore_service import MockFirestoreClient
from mocks.mock_gemini_service import MockGeminiClient

from .service_provider import TestServiceProvider


class MockServiceProvider(TestServiceProvider):
    """Provider that uses existing mock services."""

    def __init__(self):
        self._firestore = MockFirestoreClient()
        self._gemini = MockGeminiClient()
        self._auth = None  # Use existing mock auth

    def get_firestore(self) -> MockFirestoreClient:
        """Return mock Firestore client."""
        return self._firestore

    def get_gemini(self) -> MockGeminiClient:
        """Return mock Gemini client."""
        return self._gemini

    def get_auth(self) -> Any:
        """Return mock auth service."""
        return self._auth

    def cleanup(self) -> None:
        """Clean up mock services (reset to initial state)."""
        self._firestore.reset()
        self._gemini.reset()

    @property
    def is_real_service(self) -> bool:
        """Return False since using mock services."""
        return False
