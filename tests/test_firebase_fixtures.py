import sys
from unittest.mock import MagicMock

from tests.fixtures.firebase_fixtures import setup_firebase_mocks


def test_setup_firebase_mocks_registers_modules():
    mock_firebase = setup_firebase_mocks()
    assert isinstance(sys.modules.get('firebase_admin'), MagicMock)
    assert isinstance(sys.modules.get('firebase_admin.firestore'), MagicMock)
    assert 'google' in sys.modules
    assert 'google.genai' in sys.modules
    # returned object should be the same as stored in sys.modules
    assert sys.modules['firebase_admin'] is mock_firebase
