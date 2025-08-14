"""
Test demonstrating proper mocking of Firestore client in tests.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add mvp_site to path for imports
mvp_site_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if mvp_site_path not in sys.path:
    sys.path.insert(0, mvp_site_path)


class TestFirestoreMocking(unittest.TestCase):
    """Demonstrate proper mocking of Firestore operations."""

    @patch('firestore_service.get_db')
    def test_firestore_operations_with_mock(self, mock_get_db):
        """Test that Firestore operations can be properly mocked."""
        # Create a mock Firestore client
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_document = MagicMock()
        
        # Set up the mock chain
        mock_client.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_document
        mock_document.get.return_value.exists = True
        mock_document.get.return_value.to_dict.return_value = {
            'campaign_id': 'test_id',
            'name': 'Test Campaign'
        }
        
        # Configure get_db to return our mock
        mock_get_db.return_value = mock_client
        
        # Import the module that uses get_db
        import firestore_service
        
        # Test that get_db returns our mock
        db = firestore_service.get_db()
        self.assertEqual(db, mock_client)
        
        # Demonstrate that operations work with the mock
        doc_ref = db.collection('campaigns').document('test_id')
        doc = doc_ref.get()
        
        self.assertTrue(doc.exists)
        self.assertEqual(doc.to_dict()['name'], 'Test Campaign')
        
        # Verify the mock was called correctly
        mock_client.collection.assert_called_with('campaigns')
        mock_collection.document.assert_called_with('test_id')

    @patch('firestore_service.firestore.client')
    def test_mock_at_firestore_client_level(self, mock_firestore_client):
        """Test mocking at the firestore.client() level."""
        # Create a mock client
        mock_client = MagicMock()
        mock_firestore_client.return_value = mock_client
        
        # Import and use the service
        import firestore_service
        
        db = firestore_service.get_db()
        self.assertEqual(db, mock_client)
        
        # Verify firestore.client() was called
        mock_firestore_client.assert_called_once()

    def test_mock_with_context_manager(self):
        """Test using mock as a context manager for isolated tests."""
        with patch('firestore_service.get_db') as mock_get_db:
            mock_client = MagicMock()
            mock_get_db.return_value = mock_client
            
            import firestore_service
            
            db = firestore_service.get_db()
            self.assertEqual(db, mock_client)


if __name__ == '__main__':
    unittest.main()