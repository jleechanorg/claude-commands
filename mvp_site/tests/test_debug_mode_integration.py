#!/usr/bin/env python3
"""
🔴 RED PHASE: Layer 2 HTTP Integration Tests for Debug Mode Setting

Tests the complete HTTP API flow for debug mode settings.
Uses Flask test client to simulate HTTP requests.

Coverage:
- POST /api/settings with debug_mode parameter
- GET /api/settings returns debug_mode value
- Settings page includes debug mode checkbox
- Form validation for debug mode values
- Error handling for invalid debug mode values
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import json

# Add the parent directory to the path to import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the actual Flask app
from main import create_app
import constants


class TestDebugModeIntegration(unittest.TestCase):
    """Layer 2: HTTP integration tests for debug mode settings"""

    def setUp(self):
        """Set up test fixtures"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.test_user_id = "test-user-debug-integration"
        
        # Headers for auth bypass
        self.headers = {
            "X-Test-Bypass-Auth": "true",
            "X-Test-User-ID": self.test_user_id,
            "Content-Type": "application/json"
        }

    @patch('firestore_service.update_user_settings')
    def test_save_debug_mode_enabled_via_api(self, mock_update_settings):
        """🟢 GREEN: Should save debug mode enabled via POST /api/settings"""
        # Arrange
        mock_update_settings.return_value = True
        payload = {"debug_mode": True}
        
        # Act
        response = self.client.post('/api/settings', 
                                  headers=self.headers,
                                  json=payload)
        
        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.get_json()
        self.assertTrue(response_data.get('success'))
        mock_update_settings.assert_called_once()
        
        # Verify the debug_mode was included in the save call
        call_args = mock_update_settings.call_args
        saved_settings = call_args[0][1]  # Second argument is the settings dict
        self.assertTrue(saved_settings.get('debug_mode'))

    @patch('firestore_service.update_user_settings')
    def test_save_debug_mode_disabled_via_api(self, mock_update_settings):
        """🟢 GREEN: Should save debug mode disabled via POST /api/settings"""
        # Arrange
        mock_update_settings.return_value = True
        payload = {"debug_mode": False}
        
        # Act
        response = self.client.post('/api/settings', 
                                  headers=self.headers,
                                  json=payload)
        
        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.get_json()
        self.assertTrue(response_data.get('success'))
        mock_update_settings.assert_called_once()
        
        # Verify the debug_mode was included in the save call
        call_args = mock_update_settings.call_args
        saved_settings = call_args[0][1]  # Second argument is the settings dict
        self.assertFalse(saved_settings.get('debug_mode'))

    @patch('firestore_service.get_user_settings')
    def test_get_debug_mode_setting_via_api(self, mock_get_settings):
        """🟢 GREEN: Should retrieve debug mode setting via GET /api/settings"""
        # Arrange
        mock_get_settings.return_value = {'debug_mode': True, 'gemini_model': 'pro-2.5'}
        
        # Act
        response = self.client.get('/api/settings', headers=self.headers)
        
        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.get_json()
        self.assertTrue(response_data.get('debug_mode'))
        mock_get_settings.assert_called_once_with(self.test_user_id)

    @patch('firestore_service.update_user_settings')
    def test_save_combined_settings_with_debug_mode(self, mock_update_settings):
        """🟢 GREEN: Should save debug mode along with other settings"""
        # Arrange
        mock_update_settings.return_value = True
        payload = {
            "gemini_model": "flash-2.5",
            "debug_mode": True
        }
        
        # Act
        response = self.client.post('/api/settings', 
                                  headers=self.headers,
                                  json=payload)
        
        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.get_json()
        self.assertTrue(response_data.get('success'))
        
        # Verify both settings were saved
        call_args = mock_update_settings.call_args
        saved_settings = call_args[0][1]
        self.assertEqual(saved_settings.get('gemini_model'), 'flash-2.5')
        self.assertTrue(saved_settings.get('debug_mode'))

    @patch('firestore_service.update_user_settings')
    def test_invalid_debug_mode_value_rejected(self, mock_update_settings):
        """🟢 GREEN: Should reject invalid debug mode values"""
        # Arrange
        payload = {"debug_mode": "invalid"}
        
        # Act
        response = self.client.post('/api/settings', 
                                  headers=self.headers,
                                  json=payload)
        
        # Assert
        self.assertEqual(response.status_code, 400)
        response_data = response.get_json()
        self.assertFalse(response_data.get('success'))
        self.assertIn('debug_mode', response_data.get('error', '').lower())
        mock_update_settings.assert_not_called()

    @patch('firestore_service.get_user_settings')
    def test_settings_page_includes_debug_mode_checkbox(self, mock_get_settings):
        """🟢 GREEN: Settings page should include debug mode checkbox"""
        # Arrange
        mock_get_settings.return_value = {'debug_mode': False, 'gemini_model': 'pro-2.5'}
        
        # Act
        response = self.client.get('/settings', headers=self.headers)
        
        # Assert
        self.assertEqual(response.status_code, 200)
        html_content = response.get_data(as_text=True)
        
        # Check for debug mode checkbox in HTML
        self.assertIn('debug_mode', html_content)
        self.assertIn('checkbox', html_content.lower())
        self.assertIn('debug', html_content.lower())

    @patch('firestore_service.get_user_settings')
    def test_settings_page_debug_mode_checked_when_enabled(self, mock_get_settings):
        """🟢 GREEN: Debug mode checkbox should be checked when enabled"""
        # Arrange
        mock_get_settings.return_value = {'debug_mode': True, 'gemini_model': 'pro-2.5'}
        
        # Act
        response = self.client.get('/settings', headers=self.headers)
        
        # Assert
        self.assertEqual(response.status_code, 200)
        html_content = response.get_data(as_text=True)
        
        # Check for checked debug mode checkbox
        self.assertIn('checked', html_content)
        

if __name__ == '__main__':
    print("🔴 RED PHASE: Running failing HTTP integration tests for debug mode")
    print("Expected: All tests should FAIL because API endpoints are not implemented")
    unittest.main()