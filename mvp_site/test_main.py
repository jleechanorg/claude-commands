import unittest
import json
from unittest.mock import patch, MagicMock

# Mock firebase_admin before it's used in main
# This is a common pattern for testing Flask apps with Firebase
mock_firebase_admin = MagicMock()
mock_firestore = MagicMock()
mock_firebase_admin.firestore = mock_firestore

# The special DELETE_FIELD sentinel object we need to test against
DELETE_FIELD = object()
mock_firestore.DELETE_FIELD = DELETE_FIELD

# Apply the mock
import sys
sys.modules['firebase_admin'] = mock_firebase_admin
sys.modules['firebase_admin.firestore'] = mock_firestore


from main import create_app, DEFAULT_TEST_USER, HEADER_TEST_BYPASS, HEADER_TEST_USER_ID

class TestApiEndpoints(unittest.TestCase):

    def setUp(self):
        """Set up a test client for the Flask application."""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.test_headers = {
            HEADER_TEST_BYPASS: 'true',
            HEADER_TEST_USER_ID: DEFAULT_TEST_USER
        }

    @patch('main.firestore_service')
    def test_god_ask_state_with_delete_sentinel(self, mock_firestore_service):
        """
        Tests that the GOD_ASK_STATE command correctly serializes a game state
        containing the firestore.DELETE_FIELD sentinel value without crashing.
        """
        # 1. Arrange: Create a mock game state containing the sentinel
        mock_game_state = {
            "player": {"name": "Astarion", "hp": 23},
            "npcs": {
                "Goblin": {"status": "alive"},
                "Mind Flayer": DELETE_FIELD  # This field should be deleted
            }
        }
        # Mock the document snapshot and its to_dict method
        mock_doc_snapshot = MagicMock()
        mock_doc_snapshot.to_dict.return_value = mock_game_state
        mock_firestore_service.get_campaign_game_state.return_value = mock_doc_snapshot

        # 2. Act: Make the API call
        response = self.client.post(
            '/api/campaigns/test-campaign/interaction',
            headers=self.test_headers,
            json={'input': 'GOD_ASK_STATE'}
        )
        
        # 3. Assert
        self.assertEqual(response.status_code, 200)
        
        # The response text should be a JSON string inside a code block
        response_data = json.loads(response.get_data(as_text=True))
        response_json_str = response_data['response'].replace('```json\\n', '').replace('\\n```', '')
        final_state = json.loads(response_json_str)

        # Check that the 'Mind Flayer' key is now null (None in Python)
        self.assertIn('npcs', final_state)
        self.assertIn('Mind Flayer', final_state['npcs'])
        self.assertIsNone(final_state['npcs']['Mind Flayer'])
        # Verify other data is still present
        self.assertEqual(final_state['player']['name'], 'Astarion')

if __name__ == '__main__':
    unittest.main() 
