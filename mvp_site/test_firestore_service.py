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

class TestUpdateStateWithChanges(unittest.TestCase):
    def test_simple_overwrite(self):
        state = {'a': 1, 'b': 2}
        changes = {'b': 3, 'c': 4}
        expected = {'a': 1, 'b': 3, 'c': 4}
        # The function modifies the dict in place, so we check the original
        firestore_service.update_state_with_changes(state, changes)
        self.assertEqual(state, expected)

    def test_nested_overwrite(self):
        state = {'a': {'b': 1}}
        changes = {'a': {'c': 2}}
        expected = {'a': {'b': 1, 'c': 2}}
        firestore_service.update_state_with_changes(state, changes)
        self.assertEqual(state, expected)

    # --- Comprehensive Append Tests ---

    def test_append_single_item_to_existing_list(self):
        """Should append a single string to a list that already exists."""
        state = {'memories': ['memory A']}
        changes = {'memories': {'append': 'memory B'}}
        expected = {'memories': ['memory A', 'memory B']}
        firestore_service.update_state_with_changes(state, changes)
        self.assertEqual(state, expected)

    def test_append_list_of_items_to_existing_list(self):
        """Should extend an existing list with a list of new items."""
        state = {'memories': ['memory A']}
        changes = {'memories': {'append': ['memory B', 'memory C']}}
        expected = {'memories': ['memory A', 'memory B', 'memory C']}
        firestore_service.update_state_with_changes(state, changes)
        self.assertEqual(state, expected)

    def test_append_single_item_to_new_key(self):
        """Should create a new list when appending to a key that doesn't exist."""
        state = {'other_data': 123}
        changes = {'memories': {'append': 'memory A'}}
        expected = {'other_data': 123, 'memories': ['memory A']}
        firestore_service.update_state_with_changes(state, changes)
        self.assertEqual(state, expected)

    def test_append_list_to_new_key(self):
        """Should create a new list with multiple items for a key that doesn't exist."""
        state = {'other_data': 123}
        changes = {'memories': {'append': ['memory A', 'memory B']}}
        expected = {'other_data': 123, 'memories': ['memory A', 'memory B']}
        firestore_service.update_state_with_changes(state, changes)
        self.assertEqual(state, expected)

    def test_append_does_not_interfere_with_other_updates(self):
        """Should correctly append to one key while overwriting another."""
        state = {'memories': ['memory A'], 'status': 'old'}
        changes = {
            'memories': {'append': 'memory B'},
            'status': 'new'
        }
        expected = {'memories': ['memory A', 'memory B'], 'status': 'new'}
        firestore_service.update_state_with_changes(state, changes)
        self.assertEqual(state, expected)
        
    def test_append_to_non_list_key_replaces_it(self):
        """Should replace a non-list value with a new list containing the appended item."""
        state = {'memories': 'this is not a list'}
        changes = {'memories': {'append': 'memory A'}}
        expected = {'memories': ['memory A']}
        firestore_service.update_state_with_changes(state, changes)
        self.assertEqual(state, expected)

    def test_complex_nested_append_and_overwrite(self):
        """Should handle appends and overwrites at different levels of nesting."""
        state = {
            'world_data': {
                'events': ['event A'],
                'timestamp': {'year': 1}
            },
            'player': {'inventory': ['sword']}
        }
        changes = {
            'world_data': {
                'events': {'append': 'event B'},
                'timestamp': {'year': 2}
            },
            'player': { 'inventory': {'append': 'shield'}, 'xp': 100 }
        }
        expected = {
            'world_data': {
                'events': ['event A', 'event B'],
                'timestamp': {'year': 2}
            },
            'player': {'inventory': ['sword', 'shield'], 'xp': 100}
        }
        firestore_service.update_state_with_changes(state, changes)
        self.assertEqual(state, expected)


if __name__ == '__main__':
    unittest.main()