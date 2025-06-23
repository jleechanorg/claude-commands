"""
Mock libraries for function testing.
Provides realistic mocks for external dependencies like Gemini API and Firestore.
"""

from .mock_gemini_service import MockGeminiClient, MockGeminiResponse
from .mock_firestore_service import MockFirestoreClient, MockFirestoreDocument
from .test_data_fixtures import (
    SAMPLE_CAMPAIGN,
    SAMPLE_GAME_STATE,
    SAMPLE_STORY_CONTEXT,
    SAMPLE_AI_RESPONSES,
    SAMPLE_STATE_UPDATES
)

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