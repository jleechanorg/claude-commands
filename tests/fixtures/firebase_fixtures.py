from unittest.mock import MagicMock
import sys


def setup_firebase_mocks():
    """Insert Firebase and Google API mocks into sys.modules."""
    mock_firebase = MagicMock(name="firebase_admin")
    mock_firestore = MagicMock(name="firestore")
    mock_firebase.firestore = mock_firestore
    mock_firebase.initialize_app = MagicMock()
    mock_firebase.credentials = MagicMock()
    mock_firebase.auth = MagicMock()

    sys.modules['firebase_admin'] = mock_firebase
    sys.modules['firebase_admin.firestore'] = mock_firestore

    # Mock Google GenAI client modules used by gemini_service
    sys.modules.setdefault('google', MagicMock())
    sys.modules.setdefault('google.genai', MagicMock())

    return mock_firebase
