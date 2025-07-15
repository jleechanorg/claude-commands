#!/usr/bin/env python3
"""
Unit tests for firestore_service structured fields handling.
Tests that structured fields are properly stored in Firestore.
"""
import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock, call

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import constants
from firestore_service import add_story_entry


class TestFirestoreStructuredFields(unittest.TestCase):
    """Test structured fields handling in firestore_service"""
    
    def setUp(self):
        """Set up test environment"""
        # Set mock services mode to skip verification for unit tests
        os.environ['MOCK_SERVICES_MODE'] = 'true'
    
    def tearDown(self):
        """Clean up test environment"""
        # Clean up environment variable
        if 'MOCK_SERVICES_MODE' in os.environ:
            del os.environ['MOCK_SERVICES_MODE']
    
    @patch('firestore_service.get_db')
    def test_add_story_entry_with_structured_fields(self, mock_get_db):
        """Test add_story_entry properly stores structured fields"""
        # Mock the database and its chain of calls
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Test data
        user_id = 'test-user-123'
        campaign_id = 'test-campaign-456'
        story_type = 'player'
        content = 'Test story content'
        
        structured_fields = {
            constants.FIELD_SESSION_HEADER: 'Session 1: The Beginning',
            constants.FIELD_PLANNING_BLOCK: '1. Explore\n2. Fight\n3. Rest',
            constants.FIELD_DICE_ROLLS: ['Attack: 1d20+5 = 18'],
            constants.FIELD_RESOURCES: 'HP: 20/30 | Gold: 100',
            constants.FIELD_DEBUG_INFO: {'turn': 1, 'mode': 'combat'}
        }
        
        # Call the function
        add_story_entry(
            user_id, 
            campaign_id, 
            story_type, 
            content,
            structured_fields=structured_fields
        )
        
        # Verify the database calls were made
        mock_db.collection.assert_called_with('users')
        
        # Get the actual data passed to add()
        # The chain is: db.collection('users').document(user_id).collection('campaigns').document(campaign_id).collection('story').add(entry_data)
        story_add_calls = mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value.collection.return_value.add.call_args_list
        
        # Should have exactly one call (content fits in one chunk)
        self.assertEqual(len(story_add_calls), 1)
        
        # Get the story data from the call
        story_data = story_add_calls[0][0][0]
        
        # Verify structured fields are included
        self.assertEqual(story_data[constants.FIELD_SESSION_HEADER], 'Session 1: The Beginning')
        self.assertEqual(story_data[constants.FIELD_PLANNING_BLOCK], '1. Explore\n2. Fight\n3. Rest')
        self.assertEqual(story_data[constants.FIELD_DICE_ROLLS], ['Attack: 1d20+5 = 18'])
        self.assertEqual(story_data[constants.FIELD_RESOURCES], 'HP: 20/30 | Gold: 100')
        self.assertEqual(story_data[constants.FIELD_DEBUG_INFO], {'turn': 1, 'mode': 'combat'})
        
        # Verify basic fields
        self.assertEqual(story_data['text'], content)
        self.assertEqual(story_data['actor'], story_type)
        self.assertIn('timestamp', story_data)
        self.assertEqual(story_data['part'], 1)
    
    @patch('firestore_service.get_db')
    def test_add_story_entry_without_structured_fields(self, mock_get_db):
        """Test add_story_entry works without structured fields"""
        # Mock the database
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Call without structured fields
        add_story_entry(
            'user-123',
            'campaign-789',
            'gemini',
            'Simple story'
        )
        
        # Get the story data
        story_add_calls = mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value.collection.return_value.add.call_args_list
        self.assertEqual(len(story_add_calls), 1)
        story_data = story_add_calls[0][0][0]
        
        # Verify no structured fields are added
        self.assertNotIn(constants.FIELD_SESSION_HEADER, story_data)
        self.assertNotIn(constants.FIELD_PLANNING_BLOCK, story_data)
        self.assertNotIn(constants.FIELD_DICE_ROLLS, story_data)
        self.assertNotIn(constants.FIELD_RESOURCES, story_data)
        self.assertNotIn(constants.FIELD_DEBUG_INFO, story_data)
        
        # But basic fields should exist
        self.assertEqual(story_data['text'], 'Simple story')
        self.assertEqual(story_data['actor'], 'gemini')
    
    @patch('firestore_service.get_db')
    def test_add_story_entry_with_partial_structured_fields(self, mock_get_db):
        """Test add_story_entry with only some structured fields"""
        # Mock the database
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Only provide some structured fields
        structured_fields = {
            constants.FIELD_SESSION_HEADER: 'Session 2',
            constants.FIELD_DICE_ROLLS: ['Initiative: 1d20+2 = 14']
            # Other fields missing
        }
        
        # Call the function
        add_story_entry(
            'user-123',
            'campaign-789',
            'player',
            'Player action',
            structured_fields=structured_fields
        )
        
        # Get the story data
        story_add_calls = mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value.collection.return_value.add.call_args_list
        story_data = story_add_calls[0][0][0]
        
        # Verify only provided fields are included
        self.assertEqual(story_data[constants.FIELD_SESSION_HEADER], 'Session 2')
        self.assertEqual(story_data[constants.FIELD_DICE_ROLLS], ['Initiative: 1d20+2 = 14'])
        
        # Missing fields should not be included
        self.assertNotIn(constants.FIELD_PLANNING_BLOCK, story_data)
        self.assertNotIn(constants.FIELD_RESOURCES, story_data)
        self.assertNotIn(constants.FIELD_DEBUG_INFO, story_data)
    
    @patch('firestore_service.get_db')
    def test_add_story_entry_with_empty_structured_fields(self, mock_get_db):
        """Test add_story_entry with empty structured fields dict"""
        # Mock the database
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Call with empty structured fields dict
        add_story_entry(
            'user-123',
            'campaign-789',
            'player',
            'Test action',
            structured_fields={}  # Empty dict
        )
        
        # Get the story data
        story_add_calls = mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value.collection.return_value.add.call_args_list
        story_data = story_add_calls[0][0][0]
        
        # Verify no structured fields are added
        self.assertNotIn(constants.FIELD_SESSION_HEADER, story_data)
        self.assertNotIn(constants.FIELD_PLANNING_BLOCK, story_data)
        self.assertNotIn(constants.FIELD_DICE_ROLLS, story_data)
        self.assertNotIn(constants.FIELD_RESOURCES, story_data)
        self.assertNotIn(constants.FIELD_DEBUG_INFO, story_data)
        
        # Basic fields should still exist
        self.assertEqual(story_data['text'], 'Test action')
    
    @patch('firestore_service.get_db')
    def test_add_story_entry_with_none_values_in_structured_fields(self, mock_get_db):
        """Test add_story_entry handles None values in structured fields"""
        # Mock the database
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Provide structured fields with None values
        structured_fields = {
            constants.FIELD_SESSION_HEADER: 'Valid header',
            constants.FIELD_PLANNING_BLOCK: None,  # None value
            constants.FIELD_DICE_ROLLS: [],  # Empty list
            constants.FIELD_RESOURCES: '',  # Empty string
            constants.FIELD_DEBUG_INFO: None  # None value
        }
        
        # Call the function
        add_story_entry(
            'user-123',
            'campaign-789',
            'gemini',
            'AI response',
            structured_fields=structured_fields
        )
        
        # Get the story data
        story_add_calls = mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value.collection.return_value.add.call_args_list
        story_data = story_add_calls[0][0][0]
        
        # Non-None fields should be included
        self.assertEqual(story_data[constants.FIELD_SESSION_HEADER], 'Valid header')
        self.assertEqual(story_data[constants.FIELD_DICE_ROLLS], [])  # Empty list is saved
        self.assertEqual(story_data[constants.FIELD_RESOURCES], '')  # Empty string is saved
        
        # Only None fields should be excluded
        self.assertNotIn(constants.FIELD_PLANNING_BLOCK, story_data)  # None
        self.assertNotIn(constants.FIELD_DEBUG_INFO, story_data)  # None


if __name__ == '__main__':
    unittest.main()