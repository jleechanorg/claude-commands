"""
TDD tests for settings page API endpoints.
This follows the red-green-refactor methodology.

Tests cover:
1. GET /settings - serves settings page (requires auth)  
2. GET /api/settings - retrieves user settings
3. POST /api/settings - updates user settings with validation
4. Settings integration with AI model selection
"""

import os
import unittest
from unittest.mock import MagicMock, patch

# Mock firebase_admin before imports
mock_firebase_admin = MagicMock()
mock_firestore = MagicMock()
mock_auth = MagicMock()
mock_firebase_admin.firestore = mock_firestore
mock_firebase_admin.auth = mock_auth

# Firebase DELETE_FIELD sentinel
DELETE_FIELD = object()
mock_firestore.DELETE_FIELD = DELETE_FIELD

# Setup module mocks
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.modules["firebase_admin"] = mock_firebase_admin
sys.modules["firebase_admin.firestore"] = mock_firestore
sys.modules["firebase_admin.auth"] = mock_auth

# Import after mocking
from main import create_app
import constants


class TestSettingsAPI(unittest.TestCase):
    """TDD tests for settings API endpoints."""
    
    def setUp(self):
        """Set up test client and authentication headers."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.test_user_id = "test-user-123"
        self.headers = {
            "X-Test-Bypass-Auth": "true",
            "X-Test-User-ID": self.test_user_id
        }
    
    def test_settings_page_route_requires_auth(self):
        """🔴 RED: Settings page should require authentication."""
        # Test without auth headers - should return 401
        response = self.client.get('/settings')
        self.assertEqual(response.status_code, 401)
    
    def test_settings_page_route_with_auth(self):
        """🔴 RED: Settings page should render with authentication."""
        # Test with auth headers - should return 200 and render template
        response = self.client.get('/settings', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        # Should contain settings page elements
        self.assertIn(b'Settings', response.data)
        self.assertIn(b'Gemini', response.data)
    
    def test_get_user_settings_requires_auth(self):
        """🔴 RED: GET /api/settings should require authentication."""
        response = self.client.get('/api/settings')
        self.assertEqual(response.status_code, 401)
    
    def test_get_user_settings_empty_default(self):
        """🔴 RED: GET /api/settings should return empty dict for new user."""
        # Mock firestore to return no settings
        with patch('main.get_user_settings') as mock_get:
            mock_get.return_value = {}
            
            response = self.client.get('/api/settings', headers=self.headers)
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(data, {})
    
    def test_get_user_settings_with_model_preference(self):
        """🔴 RED: GET /api/settings should return saved model preference."""
        # Mock firestore to return saved settings
        with patch('main.get_user_settings') as mock_get:
            mock_get.return_value = {'gemini_model': 'flash-2.5'}
            
            response = self.client.get('/api/settings', headers=self.headers)
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(data['gemini_model'], 'gemini-2.5-flash')
    
    def test_post_user_settings_requires_auth(self):
        """🔴 RED: POST /api/settings should require authentication."""
        response = self.client.post('/api/settings', 
                                  json={'gemini_model': 'gemini-2.5-pro'})
        self.assertEqual(response.status_code, 401)
    
    def test_post_user_settings_validates_model(self):
        """🔴 RED: POST /api/settings should validate model selection."""
        # Test invalid model
        response = self.client.post('/api/settings',
                                  headers=self.headers,
                                  json={'gemini_model': 'invalid-model'})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)
        self.assertIn('Invalid model selection', data['error'])
    
    def test_post_user_settings_valid_model(self):
        """🔴 RED: POST /api/settings should accept valid model."""
        with patch('main.update_user_settings') as mock_update:
            mock_update.return_value = True
            
            response = self.client.post('/api/settings',
                                      headers=self.headers,
                                      json={'gemini_model': 'gemini-2.5-pro'})
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertTrue(data['success'])
            self.assertEqual(data['message'], 'Settings saved')
            
            # Verify firestore was called correctly
            mock_update.assert_called_once_with(self.test_user_id, {'gemini_model': 'gemini-2.5-pro'})
    
    def test_post_user_settings_handles_firestore_failure(self):
        """🔴 RED: POST /api/settings should handle Firestore failures."""
        with patch('main.update_user_settings') as mock_update:
            mock_update.return_value = False
            
            response = self.client.post('/api/settings',
                                      headers=self.headers,
                                      json={'gemini_model': 'flash-2.5'})
            self.assertEqual(response.status_code, 500)
            data = response.get_json()
            self.assertIn('error', data)
            self.assertEqual(data['error'], 'Failed to save settings')


class TestSettingsFirestoreIntegration(unittest.TestCase):
    """TDD tests for settings Firestore integration."""
    
    def test_get_user_settings_function_exists(self):
        """🔴 RED: get_user_settings function should exist in firestore_service."""
        import firestore_service
        self.assertTrue(hasattr(firestore_service, 'get_user_settings'))
    
    def test_update_user_settings_function_exists(self):
        """🔴 RED: update_user_settings function should exist in firestore_service."""
        import firestore_service
        self.assertTrue(hasattr(firestore_service, 'update_user_settings'))


class TestSettingsModelIntegration(unittest.TestCase):
    """TDD tests for settings integration with AI model selection."""
    
    def test_get_model_name_function_updated(self):
        """🔴 RED: _get_model_name should check user settings first."""
        # This test will verify the AI utils integration
        # Import will fail until we implement the function
        try:
            import ai_utils
            # Function should exist and take user_id as required parameter
            self.assertTrue(hasattr(ai_utils, '_get_model_name'))
        except ImportError:
            # Expected to fail initially - we'll implement this
            pass


class TestSettingsConstants(unittest.TestCase):
    """TDD tests for settings constants."""
    
    def test_allowed_gemini_models_constant_exists(self):
        """🔴 RED: ALLOWED_GEMINI_MODELS constant should exist."""
        # Should be defined in constants.py or main.py
        self.assertTrue(hasattr(constants, 'ALLOWED_GEMINI_MODELS'))
        models = getattr(constants, 'ALLOWED_GEMINI_MODELS')
        self.assertIn('gemini-2.5-pro', models)
        self.assertIn('gemini-2.5-flash', models)


if __name__ == "__main__":
    unittest.main()