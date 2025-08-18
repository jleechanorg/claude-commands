#!/usr/bin/env python3
"""
Test coverage for the enhanced get_db() function in firestore_service.py

Tests the new Firebase initialization and fallback logic added in the type safety foundation.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class TestGetDbFoundation(unittest.TestCase):
    """Test the enhanced get_db() function with Firebase initialization logic."""

    def setUp(self):
        """Set up test environment."""
        # Ensure we start with clean environment
        self.original_testing = os.environ.get('TESTING')
        self.original_ci = os.environ.get('CI')
        
    def tearDown(self):
        """Clean up environment after tests."""
        # Restore original environment variables
        if self.original_testing is not None:
            os.environ['TESTING'] = self.original_testing
        elif 'TESTING' in os.environ:
            del os.environ['TESTING']
            
        if self.original_ci is not None:
            os.environ['CI'] = self.original_ci
        elif 'CI' in os.environ:
            del os.environ['CI']

    @patch('firestore_service.firebase_utils.should_skip_firebase_init')
    @patch('firestore_service.firestore.client')
    def test_get_db_skip_firebase_init(self, mock_firestore_client, mock_should_skip):
        """Test get_db() when Firebase initialization should be skipped."""
        from firestore_service import get_db
        
        # Mock that Firebase init should be skipped
        mock_should_skip.return_value = True
        
        # Call get_db
        result = get_db()
        
        # Should return a mock client
        self.assertIsNotNone(result)
        # firestore.client() should not be called when skipping init
        mock_firestore_client.assert_not_called()
        # should_skip_firebase_init should be checked
        mock_should_skip.assert_called_once()

    @patch('firestore_service.firebase_utils.should_skip_firebase_init')
    @patch('firestore_service.firebase_admin._apps', {})
    @patch('firestore_service.firebase_admin.initialize_app')
    @patch('firestore_service.firestore.client')
    def test_get_db_firebase_not_initialized_success(self, mock_firestore_client, mock_init_app, mock_should_skip):
        """Test get_db() when Firebase is not initialized but initialization succeeds."""
        from firestore_service import get_db
        
        # Mock that Firebase init should not be skipped
        mock_should_skip.return_value = False
        
        # Mock successful initialization and client creation
        mock_client = MagicMock()
        mock_firestore_client.return_value = mock_client
        
        # Call get_db
        result = get_db()
        
        # Should initialize Firebase and return real client
        mock_init_app.assert_called_once()
        mock_firestore_client.assert_called_once()
        self.assertEqual(result, mock_client)

    @patch('firestore_service.firebase_utils.should_skip_firebase_init')
    @patch('firestore_service.firebase_admin._apps', {})
    @patch('firestore_service.firebase_admin.initialize_app')
    @patch('firestore_service.firestore.client')
    def test_get_db_firebase_init_fails_testing_env(self, mock_firestore_client, mock_init_app, mock_should_skip):
        """Test get_db() when Firebase initialization fails in testing environment."""
        from firestore_service import get_db
        
        # Set testing environment
        os.environ['TESTING'] = 'true'
        
        # Mock that Firebase init should not be skipped
        mock_should_skip.return_value = False
        
        # Mock initialization failure
        mock_init_app.side_effect = Exception("Firebase init failed")
        
        # Call get_db
        result = get_db()
        
        # Should return mock client due to testing environment
        self.assertIsNotNone(result)
        mock_init_app.assert_called_once()
        # firestore.client() should not be called due to init failure
        mock_firestore_client.assert_not_called()

    @patch('firestore_service.firebase_utils.should_skip_firebase_init')
    @patch('firestore_service.firebase_admin._apps', {})
    @patch('firestore_service.firebase_admin.initialize_app')
    def test_get_db_firebase_init_fails_production(self, mock_init_app, mock_should_skip):
        """Test get_db() when Firebase initialization fails in production environment."""
        from firestore_service import get_db
        
        # Ensure not in testing environment
        if 'TESTING' in os.environ:
            del os.environ['TESTING']
        if 'CI' in os.environ:
            del os.environ['CI']
        
        # Mock that Firebase init should not be skipped
        mock_should_skip.return_value = False
        
        # Mock initialization failure
        mock_init_app.side_effect = Exception("Firebase init failed")
        
        # Call get_db - should raise ValueError in production
        with self.assertRaises(ValueError) as context:
            get_db()
        
        self.assertIn("Firebase app initialization failed", str(context.exception))
        mock_init_app.assert_called_once()

    @patch('firestore_service.firebase_utils.should_skip_firebase_init')
    @patch('firestore_service.firebase_admin._apps', {'default': MagicMock()})
    @patch('firestore_service.firestore.client')
    def test_get_db_firebase_already_initialized(self, mock_firestore_client, mock_should_skip):
        """Test get_db() when Firebase is already initialized."""
        from firestore_service import get_db
        
        # Mock that Firebase init should not be skipped
        mock_should_skip.return_value = False
        
        # Mock successful client creation
        mock_client = MagicMock()
        mock_firestore_client.return_value = mock_client
        
        # Call get_db
        result = get_db()
        
        # Should not try to initialize (already initialized) but create client
        mock_firestore_client.assert_called_once()
        self.assertEqual(result, mock_client)

    @patch('firestore_service.firebase_utils.should_skip_firebase_init')
    @patch('firestore_service.firebase_admin._apps', {'default': MagicMock()})
    @patch('firestore_service.firestore.client')
    def test_get_db_client_creation_fails_testing(self, mock_firestore_client, mock_should_skip):
        """Test get_db() when client creation fails in testing environment."""
        from firestore_service import get_db
        
        # Set testing environment
        os.environ['TESTING'] = 'true'
        
        # Mock that Firebase init should not be skipped
        mock_should_skip.return_value = False
        
        # Mock client creation failure
        mock_firestore_client.side_effect = Exception("Client creation failed")
        
        # Call get_db
        result = get_db()
        
        # Should return mock client due to testing environment
        self.assertIsNotNone(result)
        mock_firestore_client.assert_called_once()

    @patch('firestore_service.firebase_utils.should_skip_firebase_init')
    @patch('firestore_service.firebase_admin._apps', {'default': MagicMock()})
    @patch('firestore_service.firestore.client')
    def test_get_db_client_creation_fails_production(self, mock_firestore_client, mock_should_skip):
        """Test get_db() when client creation fails in production environment."""
        from firestore_service import get_db
        
        # Ensure not in testing environment
        if 'TESTING' in os.environ:
            del os.environ['TESTING']
        if 'CI' in os.environ:
            del os.environ['CI']
        
        # Mock that Firebase init should not be skipped
        mock_should_skip.return_value = False
        
        # Mock client creation failure
        mock_firestore_client.side_effect = Exception("Client creation failed")
        
        # Call get_db - should raise ValueError in production
        with self.assertRaises(ValueError) as context:
            get_db()
        
        self.assertIn("Failed to create Firestore client", str(context.exception))
        mock_firestore_client.assert_called_once()

    @patch('firestore_service.firebase_utils.should_skip_firebase_init')
    @patch('firestore_service.firebase_admin._apps', {'default': MagicMock()})
    @patch('firestore_service.firestore.client')
    def test_get_db_ci_environment_fallback(self, mock_firestore_client, mock_should_skip):
        """Test get_db() fallback behavior in CI environment."""
        from firestore_service import get_db
        
        # Set CI environment
        os.environ['CI'] = 'true'
        
        # Mock that Firebase init should not be skipped initially
        mock_should_skip.return_value = False
        
        # Mock client creation failure
        mock_firestore_client.side_effect = Exception("Client creation failed")
        
        # Call get_db
        result = get_db()
        
        # Should return mock client due to CI environment
        self.assertIsNotNone(result)
        mock_firestore_client.assert_called_once()

    def test_foundation_documentation(self):
        """Document the get_db() foundation changes and their purpose."""
        print("\n" + "="*60)
        print("GET_DB() FOUNDATION CHANGES")
        print("="*60)
        print("This test validates the enhanced get_db() function changes:")
        print()
        print("🔧 ENHANCED FEATURES:")
        print("- Robust Firebase initialization across different environments")
        print("- Production: Ensures Firebase is initialized before returning client")
        print("- Testing: Uses mocks when Firebase initialization is skipped")
        print("- CI: Gracefully handles missing initialization with fallbacks")
        print()
        print("🔧 ERROR HANDLING:")
        print("- Firebase initialization failure handling")
        print("- Client creation failure recovery")
        print("- Environment-aware fallback strategies")
        print("- Comprehensive error messages for debugging")
        print()
        print("🎯 FOUNDATION PURPOSE:")
        print("- Enables reliable Firestore operations across environments")
        print("- Prevents service failures due to initialization issues")
        print("- Provides consistent interface regardless of environment")
        print("- Supports both production reliability and testing flexibility")
        print()
        print("✅ VALIDATION COVERAGE:")
        print("- Firebase skip logic verified")
        print("- Initialization flow tested")
        print("- Error handling patterns confirmed")
        print("- Environment-specific behaviors validated")
        print("="*60)
        
        # This test always passes - it's for documentation
        self.assertTrue(True)


if __name__ == '__main__':
    print("🔧 get_db() Foundation Tests")
    print("="*50)
    print("Testing enhanced Firebase initialization and fallback logic")
    print("="*50)
    
    # Run with detailed output
    unittest.main(verbosity=2)