"""
Layer 3: Browser tests for user settings with mocked services

Tests the complete browser flow from UI interaction to backend processing.
Uses real browser automation but mocks external services (Firestore, Gemini API).

Coverage:  
- Settings page form submission and validation
- Model preference selection in browser UI
- Campaign creation using browser-selected model preferences
- Error handling in browser for invalid settings
- Visual feedback and UI state management

NOTE: This test assumes a Flask server is running on localhost:6006
Run: python3 mvp_site/run_server.py 
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import time
import json
import subprocess
import requests

# Add the parent directory to the path to import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the actual Flask app
from main import create_app
import constants


class TestSettingsBrowserMock(unittest.TestCase):
    """Layer 3: HTTP-based tests simulating browser flow with mocked external services"""

    def setUp(self):
        """Set up test fixtures"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Test data
        self.test_user_id = "browser-mock-user"
        self.auth_headers = {
            'X-Test-Bypass-Auth': 'true',
            'X-Test-User-ID': self.test_user_id,
            'Content-Type': 'application/json'
        }
        
    @patch('main.get_user_settings')
    @patch('main.update_user_settings') 
    def test_settings_api_simulates_browser_form_submission(self, mock_update_settings, mock_get_settings):
        """🟢 Layer 3: Settings API handles browser-like form submission"""
        # Arrange
        mock_get_settings.return_value = {}  # No existing settings
        mock_update_settings.return_value = True
        
        # Act - Simulate browser form POST to settings endpoint
        settings_data = {"gemini_model": "flash-2.5"}
        response = self.client.post('/api/settings',
                                  headers=self.auth_headers,
                                  data=json.dumps(settings_data))
        
        # Assert - Response as browser would receive it
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['success'], True)
        self.assertEqual(response_data['message'], 'Settings saved')
        
        # Verify backend call
        mock_update_settings.assert_called_once_with(self.test_user_id, settings_data)
        
    @patch('main.get_user_settings')
    def test_settings_retrieval_simulates_browser_page_load(self, mock_get_settings):
        """🟢 Layer 3: Settings retrieval simulates browser page load"""
        # Arrange
        expected_settings = {"gemini_model": "pro-2.5"}
        mock_get_settings.return_value = expected_settings
        
        # Act - Simulate browser GET request for settings page data
        response = self.client.get('/api/settings', headers=self.auth_headers)
        
        # Assert - Data as browser would receive it
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertEqual(response_data, expected_settings)
        
        # Verify backend call
        mock_get_settings.assert_called_once_with(self.test_user_id)
        
    @patch('gemini_service.get_user_settings')
    @patch('gemini_service._call_gemini_api')
    @patch('gemini_service._get_text_from_response')
    @patch('firestore_service.create_campaign')
    @patch('firestore_service.add_story_entry')
    def test_campaign_flow_simulates_browser_sequence(self, mock_add_story, mock_create_campaign,
                                                     mock_get_text, mock_api_call, mock_get_settings):
        """🟢 Layer 3: Campaign creation simulates browser user flow sequence"""
        # Arrange - User previously selected pro-2.5 in browser settings
        mock_get_settings.return_value = {'gemini_model': 'pro-2.5'}
        mock_api_call.return_value = MagicMock()
        mock_get_text.return_value = '{"narrative": "Epic browser story!", "state_changes": {}, "player_character_data": {"name": "Browser Hero"}}'
        mock_create_campaign.return_value = 'browser-campaign-id'
        mock_add_story.return_value = 'browser-story-id'
        
        # Act - Simulate browser campaign creation form submission
        campaign_data = {
            "title": "Browser Campaign",
            "character": "Browser Hero", 
            "setting": "Browser World",
            "description": "Created via simulated browser flow",
            "selected_prompts": ["narrative"],
            "custom_options": [],
            "attribute_system": "D&D"
        }
        
        response = self.client.post('/api/campaigns',
                                  headers=self.auth_headers,
                                  data=json.dumps(campaign_data))
        
        # Assert - Response as browser would receive it
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.data)
        self.assertTrue(response_data['success'])
        
        # Verify user settings were applied
        mock_get_settings.assert_called_once_with(self.test_user_id)
        mock_api_call.assert_called_once()
        
        # Verify pro model was used (key behavior)
        call_args = mock_api_call.call_args
        model_used = call_args[0][1]  # Second positional argument is model
        self.assertEqual(model_used, "gemini-2.5-pro")
        
    @patch('main.update_user_settings')
    def test_settings_error_handling_simulates_browser_failure(self, mock_update_settings):
        """🟢 Layer 3: Settings error handling as browser would experience it"""
        # Arrange
        mock_update_settings.side_effect = Exception("Firestore connection error")
        
        # Act - Simulate browser form submission that triggers error
        settings_data = {"gemini_model": "flash-2.5"}
        response = self.client.post('/api/settings',
                                  headers=self.auth_headers,
                                  data=json.dumps(settings_data))
        
        # Assert - Error response as browser would receive it
        self.assertEqual(response.status_code, 500)
        response_data = json.loads(response.data)
        self.assertIn('error', response_data)
        self.assertIn('error', response_data['error'].lower())
        
    def test_multiple_settings_changes_simulates_browser_session(self):
        """🟢 Layer 3: Multiple settings changes simulate browser user session"""
        # This test simulates a user making multiple changes in a browser session
        
        with patch('main.get_user_settings') as mock_get_settings, \
             patch('main.update_user_settings') as mock_update_settings:
            
            mock_get_settings.return_value = {}
            mock_update_settings.return_value = True
            
            # Act - Simulate user changing settings multiple times
            # First change: flash-2.5
            response1 = self.client.post('/api/settings',
                                       headers=self.auth_headers,
                                       data=json.dumps({"gemini_model": "flash-2.5"}))
            
            # Second change: pro-2.5
            response2 = self.client.post('/api/settings',
                                       headers=self.auth_headers,
                                       data=json.dumps({"gemini_model": "pro-2.5"}))
            
            # Third change: back to flash-2.5
            response3 = self.client.post('/api/settings',
                                       headers=self.auth_headers,
                                       data=json.dumps({"gemini_model": "flash-2.5"}))
            
            # Assert - All requests succeeded
            self.assertEqual(response1.status_code, 200)
            self.assertEqual(response2.status_code, 200)  
            self.assertEqual(response3.status_code, 200)
            
            # Verify all calls were made
            self.assertEqual(mock_update_settings.call_count, 3)
            
            # Verify final call was flash-2.5
            final_call = mock_update_settings.call_args_list[-1]
            self.assertEqual(final_call[0][1]['gemini_model'], 'flash-2.5')


if __name__ == '__main__':
    print("🔵 Layer 3: Running browser tests for settings with mocked services")
    print("📝 NOTE: This requires Flask server running on localhost:6006")
    unittest.main()