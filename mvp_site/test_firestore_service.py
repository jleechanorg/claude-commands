import unittest
from unittest.mock import patch, MagicMock

# We need to import the service we are testing
import firestore_service

class TestFirestoreService(unittest.TestCase):

    @patch('firestore_service.get_db')
    def test_update_campaign_title(self, mock_get_db):
        """Tests that the title update function calls the correct Firestore method."""
        # 1. Setup the mock
        mock_db = mock_get_db.return_value
        mock_campaign_ref = mock_db.collection.return_value.document.return_value

        # 2. Call the function
        user_id = 'test_user'
        campaign_id = 'test_campaign'
        new_title = 'A Brand New Title'
        result = firestore_service.update_campaign_title(user_id, campaign_id, new_title)

        # 3. Assert the results
        # Check that the function returns True as expected
        self.assertTrue(result)

        # Check that the mocked database was called correctly
        mock_db.collection.assert_called_with('users')
        mock_db.collection.return_value.document.assert_called_with(user_id)
        mock_campaign_ref.collection.return_value.document.assert_called_with(campaign_id)
        
        # Check that the `update` method was called with the correct payload
        mock_campaign_ref.collection.return_value.document.return_value.update.assert_called_once_with({'title': new_title})

if __name__ == '__main__':
    unittest.main() 