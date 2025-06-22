import unittest
from unittest.mock import patch, MagicMock
import logging
import datetime

# We need to import the service we are testing
import firestore_service

# Disable logging for most tests to keep output clean, can be enabled for debugging
# logging.disable(logging.CRITICAL)

# Mock firebase_admin before importing the service
mock_firestore = MagicMock()
# Configure the mock to have the sentinel values using MagicMock for identity checks
mock_firestore.DELETE_FIELD = MagicMock(name="DELETE_FIELD")
mock_firestore.SERVER_TIMESTAMP = MagicMock(name="SERVER_TIMESTAMP")

import sys
sys.modules['firebase_admin.firestore'] = mock_firestore

# Now import the service, which will use the mock
from firestore_service import json_default_serializer, update_state_with_changes

# Create sentinel mock objects for use in the tests.
DELETE_SENTINEL = MagicMock(name="DELETE_FIELD")
TIMESTAMP_SENTINEL = MagicMock(name="SERVER_TIMESTAMP")

@patch('firestore_service.firestore.SERVER_TIMESTAMP', TIMESTAMP_SENTINEL)
@patch('firestore_service.firestore.DELETE_FIELD', DELETE_SENTINEL)
class TestJsonDefaultSerializer(unittest.TestCase):

    def test_datetime_serialization(self):
        """Tests that datetime objects are serialized to ISO 8601 strings."""
        now = datetime.datetime(2025, 6, 22, 12, 30, 0)
        self.assertEqual(json_default_serializer(now), "2025-06-22T12:30:00")

    def test_delete_field_sentinel(self):
        """Tests that the DELETE_FIELD sentinel is serialized to None."""
        # The serializer will now correctly see the patched DELETE_SENTINEL
        self.assertIsNone(json_default_serializer(DELETE_SENTINEL))

    def test_server_timestamp_sentinel(self):
        """Tests that the SERVER_TIMESTAMP sentinel is serialized to a specific string."""
        # The serializer will now correctly see the patched TIMESTAMP_SENTINEL
        self.assertEqual(json_default_serializer(TIMESTAMP_SENTINEL), "<SERVER_TIMESTAMP>")

    def test_unserializable_object(self):
        """Tests that a generic object raises a TypeError."""
        class Unserializable:
            pass
        with self.assertRaises(TypeError):
            json_default_serializer(Unserializable())

class TestUpdateStateWithChanges(unittest.TestCase):
    
    def setUp(self):
        """This method is called before each test."""
        # It's good practice to start with a fresh state for each test.
        self.state = {
            'player': {
                'inventory': ['sword', 'shield'],
                'stats': {'hp': 100, 'mp': 50}
            },
            'world_data': {
                'events': ['event A'],
                'timestamp': {'year': 1}
            },
            'custom_campaign_state': {
                'core_memories': ['memory A', 'memory B']
            }
        }

    def test_simple_overwrite(self):
        """Should overwrite a top-level value."""
        changes = {'game_version': '1.1'}
        firestore_service.update_state_with_changes(self.state, changes)
        self.assertEqual(self.state['game_version'], '1.1')

    def test_nested_overwrite(self):
        """Should overwrite a nested value."""
        changes = {'player': {'stats': {'hp': 90}}}
        firestore_service.update_state_with_changes(self.state, changes)
        self.assertEqual(self.state['player']['stats']['hp'], 90)
        self.assertEqual(self.state['player']['stats']['mp'], 50) # Ensure other values are untouched

    def test_deep_merge_preserves_unrelated_keys(self):
        """A deep merge should not delete sibling keys in a nested object."""
        state = {
            'player': {
                'stats': {
                    'str': 10,
                    'dex': 10
                }
            }
        }
        changes = {
            'player': {
                'stats': {
                    'dex': 15
                }
            }
        }
        updated_state = firestore_service.update_state_with_changes(state, changes)
        # This will fail in the old buggy version because 'str' will be missing
        self.assertIn('str', updated_state['player']['stats'])
        self.assertEqual(updated_state['player']['stats']['str'], 10)
        self.assertEqual(updated_state['player']['stats']['dex'], 15)

    def test_explicit_append_single_item(self):
        """Should append a single item using the {'append':...} syntax."""
        changes = {'player': {'inventory': {'append': 'potion'}}}
        firestore_service.update_state_with_changes(self.state, changes)
        self.assertIn('potion', self.state['player']['inventory'])
        self.assertEqual(len(self.state['player']['inventory']), 3)

    def test_explicit_append_list_of_items(self):
        """Should append a list of items using the {'append':...} syntax."""
        changes = {'player': {'inventory': {'append': ['gold coin', 'key']}}}
        firestore_service.update_state_with_changes(self.state, changes)
        self.assertIn('gold coin', self.state['player']['inventory'])
        self.assertIn('key', self.state['player']['inventory'])
        self.assertEqual(len(self.state['player']['inventory']), 4)

    def test_core_memories_safeguard_converts_overwrite(self):
        """CRITICAL: Should convert a direct overwrite of core_memories into a safe, deduplicated append."""
        changes = {'custom_campaign_state': {'core_memories': ['memory B', 'memory C']}}
        firestore_service.update_state_with_changes(self.state, changes)
        final_memories = self.state['custom_campaign_state']['core_memories']
        self.assertEqual(len(final_memories), 3)
        self.assertIn('memory A', final_memories)
        self.assertIn('memory B', final_memories)
        self.assertIn('memory C', final_memories)

    def test_core_memories_safeguard_handles_no_new_items(self):
        """CRITICAL: Should not add duplicate memories during a safeguard append."""
        changes = {'custom_campaign_state': {'core_memories': ['memory A', 'memory B']}}
        firestore_service.update_state_with_changes(self.state, changes)
        final_memories = self.state['custom_campaign_state']['core_memories']
        self.assertEqual(len(final_memories), 2)

    def test_core_memories_explicit_append_is_deduplicated(self):
        """CRITICAL: Explicit appends to core_memories should also be deduplicated."""
        changes = {'custom_campaign_state': {'core_memories': {'append': 'memory A'}}}
        firestore_service.update_state_with_changes(self.state, changes)
        final_memories = self.state['custom_campaign_state']['core_memories']
        self.assertEqual(len(final_memories), 2) # Should not add the duplicate 'memory A'

    def test_append_to_non_core_memories_is_not_deduplicated(self):
        """Append to any list other than core_memories should allow duplicates."""
        changes = {'world_data': {'events': {'append': 'event A'}}}
        firestore_service.update_state_with_changes(self.state, changes)
        self.assertEqual(self.state['world_data']['events'], ['event A', 'event A'])
        self.assertEqual(len(self.state['world_data']['events']), 2)

    def test_safeguard_handles_non_list_value(self):
        """Safeguard should correctly append a non-list value by wrapping it."""
        state = {'custom_campaign_state': {'core_memories': ['memory A']}}
        changes = {'custom_campaign_state': {'core_memories': 'a new string memory'}}
        expected_memories = ['memory A', 'a new string memory']
        
        firestore_service.update_state_with_changes(state, changes)
        
        self.assertEqual(state['custom_campaign_state']['core_memories'], expected_memories)

if __name__ == '__main__':
    unittest.main()