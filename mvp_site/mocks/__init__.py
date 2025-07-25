"""
Mock libraries for function testing.
Provides realistic mocks for external dependencies like Gemini API and Firestore.
"""

from . import mock_firestore_service_wrapper, mock_gemini_service_wrapper
from .data_fixtures import (
    SAMPLE_AI_RESPONSES,
    SAMPLE_CAMPAIGN,
    SAMPLE_GAME_STATE,
    SAMPLE_STATE_UPDATES,
    SAMPLE_STORY_CONTEXT,
)
from .mock_firestore_service import MockFirestoreClient, MockFirestoreDocument
from .mock_gemini_service import MockGeminiClient, MockGeminiResponse

__all__ = [
    'MockGeminiClient',
    'MockGeminiResponse',
    'MockFirestoreClient',
    'MockFirestoreDocument',
    'SAMPLE_CAMPAIGN',
    'SAMPLE_GAME_STATE',
    'SAMPLE_STORY_CONTEXT',
    'SAMPLE_AI_RESPONSES',
    'SAMPLE_STATE_UPDATES'
]
