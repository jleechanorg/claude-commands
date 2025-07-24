"""
Layer 2: Integration tests for user settings flow

Tests the complete backend flow from API endpoint to Gemini service.
Mocks only external services (Firestore, Gemini API) but tests actual integration.

Coverage:
- Complete API → Gemini service flow
- User settings retrieval and application
- Model selection with real user preferences
- Error handling for invalid settings
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


class TestSettingsIntegration(unittest.TestCase):
    """Layer 2: Integration tests for complete settings flow"""

    def setUp(self):
        """Set up test fixtures"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Test data
        self.test_user_id = "integration-test-user"
        self.auth_headers = {
            'X-Test-Bypass-Auth': 'true',
            'X-Test-User-ID': self.test_user_id,
            'Content-Type': 'application/json'
        }
        
        self.campaign_data = {
            "title": "Test Campaign",
            "character": "Test Hero",
            "setting": "Test World",
            "description": "Integration test campaign",
            "selected_prompts": ["narrative"],
            "custom_options": [],
            "attribute_system": "D&D"
        }

    @patch('gemini_service.get_user_settings')
    @patch('gemini_service._call_gemini_api')
    @patch('gemini_service._get_text_from_response')
    @patch('firestore_service.create_campaign')
    @patch('firestore_service.add_story_entry')
    def test_campaign_creation_uses_flash_model(self, mock_add_story, mock_create_campaign, 
                                               mock_get_text, mock_api_call, mock_get_settings):
        """🟢 Integration: Campaign creation uses user's flash-2.5 preference"""
        # Arrange
        mock_get_settings.return_value = {'gemini_model': 'flash-2.5'}
        mock_api_call.return_value = MagicMock()
        mock_get_text.return_value = '{"narrative": "Test story", "state_changes": {}, "player_character_data": {"name": "Test Hero"}}'
        mock_create_campaign.return_value = 'test-campaign-id'
        mock_add_story.return_value = 'test-story-id'
        
        # Act
        response = self.client.post('/api/campaigns', 
                                  headers=self.auth_headers,
                                  data=json.dumps(self.campaign_data))
        
        # Assert
        self.assertEqual(response.status_code, 201)
        
        # Verify user settings were retrieved
        mock_get_settings.assert_called_once_with(self.test_user_id)
        
        # Verify Gemini API was called with flash model
        mock_api_call.assert_called_once()
        call_args = mock_api_call.call_args
        model_used = call_args[0][1]  # Second positional argument is model
        self.assertEqual(model_used, "gemini-2.5-flash")

    @patch('gemini_service.get_user_settings')
    @patch('gemini_service._call_gemini_api')
    @patch('gemini_service._get_text_from_response')
    @patch('firestore_service.create_campaign')
    @patch('firestore_service.add_story_entry')
    def test_campaign_creation_uses_pro_model(self, mock_add_story, mock_create_campaign,
                                             mock_get_text, mock_api_call, mock_get_settings):
        """🟢 Integration: Campaign creation uses user's pro-2.5 preference"""
        # Arrange
        mock_get_settings.return_value = {'gemini_model': 'pro-2.5'}
        mock_api_call.return_value = MagicMock()
        mock_get_text.return_value = '{"narrative": "Test story", "state_changes": {}, "player_character_data": {"name": "Test Hero"}}'
        mock_create_campaign.return_value = 'test-campaign-id'
        mock_add_story.return_value = 'test-story-id'
        
        # Act
        response = self.client.post('/api/campaigns',
                                  headers=self.auth_headers,
                                  data=json.dumps(self.campaign_data))
        
        # Assert
        self.assertEqual(response.status_code, 201)
        
        # Verify user settings were retrieved
        mock_get_settings.assert_called_once_with(self.test_user_id)
        
        # Verify Gemini API was called with pro model
        mock_api_call.assert_called_once()
        call_args = mock_api_call.call_args
        model_used = call_args[0][1]  # Second positional argument is model  
        self.assertEqual(model_used, "gemini-2.5-pro")

    @patch('gemini_service.get_user_settings')
    @patch('gemini_service._call_gemini_api')
    @patch('gemini_service._get_text_from_response')
    @patch('firestore_service.create_campaign')
    @patch('firestore_service.add_story_entry')
    def test_campaign_creation_fallback_to_default(self, mock_add_story, mock_create_campaign,
                                                  mock_get_text, mock_api_call, mock_get_settings):
        """🟢 Integration: Campaign creation falls back to default when no settings"""
        # Arrange
        mock_get_settings.return_value = {}  # No settings
        mock_api_call.return_value = MagicMock()
        mock_get_text.return_value = '{"narrative": "Test story", "state_changes": {}, "player_character_data": {"name": "Test Hero"}}'
        mock_create_campaign.return_value = 'test-campaign-id'
        mock_add_story.return_value = 'test-story-id'
        
        # Act
        response = self.client.post('/api/campaigns',
                                  headers=self.auth_headers,
                                  data=json.dumps(self.campaign_data))
        
        # Assert
        self.assertEqual(response.status_code, 201)
        
        # Verify user settings were retrieved
        mock_get_settings.assert_called_once_with(self.test_user_id)
        
        # Verify Gemini API was called with default model
        mock_api_call.assert_called_once()
        call_args = mock_api_call.call_args
        model_used = call_args[0][1]  # Second positional argument is model
        self.assertEqual(model_used, "gemini-2.5-flash")  # DEFAULT_MODEL

    @patch('gemini_service.get_user_settings')
    @patch('gemini_service._call_gemini_api')
    @patch('gemini_service._get_text_from_response')
    @patch('firestore_service.create_campaign')
    @patch('firestore_service.add_story_entry')
    def test_settings_error_handling(self, mock_add_story, mock_create_campaign,
                                    mock_get_text, mock_api_call, mock_get_settings):
        """🟢 Integration: Campaign creation handles settings retrieval errors gracefully"""
        # Arrange
        mock_get_settings.side_effect = Exception("Firestore error")
        mock_api_call.return_value = MagicMock()
        mock_get_text.return_value = '{"narrative": "Test story", "state_changes": {}, "player_character_data": {"name": "Test Hero"}}'
        mock_create_campaign.return_value = 'test-campaign-id'
        mock_add_story.return_value = 'test-story-id'
        
        # Act
        response = self.client.post('/api/campaigns',
                                  headers=self.auth_headers,
                                  data=json.dumps(self.campaign_data))
        
        # Assert
        self.assertEqual(response.status_code, 201)
        
        # Verify campaign creation still succeeded despite settings error
        mock_get_settings.assert_called_once_with(self.test_user_id)
        
        # Verify Gemini API was called with default model (fallback)
        mock_api_call.assert_called_once()
        call_args = mock_api_call.call_args
        model_used = call_args[0][1]  # Second positional argument is model
        self.assertEqual(model_used, "gemini-2.5-flash")  # DEFAULT_MODEL

    @patch('main.update_user_settings')
    def test_settings_api_saves_preferences(self, mock_update_settings):
        """🟢 Integration: Settings API correctly saves user preferences"""
        # Arrange
        settings_data = {"gemini_model": "pro-2.5"}
        
        # Act
        response = self.client.post('/api/settings',
                                  headers=self.auth_headers,
                                  data=json.dumps(settings_data))
        
        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertEqual(response_data['success'], True)
        self.assertEqual(response_data['message'], 'Settings saved')
        
        # Verify settings were saved with correct user_id
        mock_update_settings.assert_called_once_with(self.test_user_id, settings_data)

    @patch('main.get_user_settings')
    def test_settings_api_retrieves_preferences(self, mock_get_settings):
        """🟢 Integration: Settings API correctly retrieves user preferences"""
        # Arrange
        expected_settings = {"gemini_model": "flash-2.5"}
        mock_get_settings.return_value = expected_settings
        
        # Act
        response = self.client.get('/api/settings', headers=self.auth_headers)
        
        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertEqual(response_data, expected_settings)
        
        # Verify settings were retrieved for correct user_id
        mock_get_settings.assert_called_once_with(self.test_user_id)


if __name__ == '__main__':
    print("🔵 Layer 2: Running integration tests for settings flow")
    unittest.main()