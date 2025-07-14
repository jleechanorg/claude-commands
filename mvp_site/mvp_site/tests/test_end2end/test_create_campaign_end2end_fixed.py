"""
End-to-end integration test for creating a campaign - FIXED VERSION.
Only mocks external services (Gemini API and Firestore DB).
Tests the full flow from API endpoint through all service layers.
"""

import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os
from datetime import datetime

# Set TESTING environment variable
os.environ['TESTING'] = 'true'
os.environ['GEMINI_API_KEY'] = 'test-api-key'

# Add the parent directory to the path to import main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from main import create_app, HEADER_TEST_BYPASS, HEADER_TEST_USER_ID, DEFAULT_TEST_USER
import constants
from game_state import GameState
import gemini_service
from tests.fake_firestore import FakeFirestoreClient, FakeGeminiResponse, FakeTokenCount


class TestCreateCampaignEnd2End(unittest.TestCase):
    """Test creating a campaign through the full application stack."""
    
    def setUp(self):
        """Set up test client and mocks."""
        # Reset gemini service client to ensure our mock is used
        gemini_service._client = None
        
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Test data
        self.test_user_id = "test-user-123"
        
        # Test headers for bypassing auth in test mode
        self.test_headers = {
            HEADER_TEST_BYPASS: 'true',
            HEADER_TEST_USER_ID: self.test_user_id
        }
        self.test_campaign_data = {
            "title": "Epic Dragon Quest",
            "character": "Thorin the Bold",
            "setting": "Mountain Kingdom",
            "description": "A brave dwarf warrior seeks to reclaim his homeland",
            "campaignType": "custom",
            "selectedPrompts": ["narrative", "mechanics"],
            "customOptions": ["companions"]
        }
    
    def tearDown(self):
        """Reset gemini service client after each test."""
        gemini_service._client = None
        
    @patch('firebase_admin.firestore.client')
    @patch('google.genai.Client')
    def test_create_campaign_success(self, mock_genai_client_class, mock_firestore_client):
        """Test successful campaign creation with full flow."""
        
        # Set up fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_firestore_client.return_value = fake_firestore
        
        # Set up fake Gemini client
        fake_genai_client = MagicMock()
        mock_genai_client_class.return_value = fake_genai_client
        
        # Mock token counting to return a simple object
        fake_genai_client.models.count_tokens.return_value = FakeTokenCount(1000)
        
        # Mock Gemini response
        response_json = json.dumps({
            "narrative": "The mountain winds howled as Thorin the Bold stood at the gates...",
            "entities_mentioned": ["Thorin the Bold"],
            "location_confirmed": "Mountain Kingdom Gates",
            "state_updates": {
                "player_character_data": {
                    "name": "Thorin the Bold",
                    "level": 1,
                    "hp_current": 10,
                    "hp_max": 10
                }
            }
        })
        fake_genai_client.models.generate_content.return_value = FakeGeminiResponse(response_json)
        
        # Make the API request
        response = self.client.post(
            '/api/campaigns',
            data=json.dumps(self.test_campaign_data),
            content_type='application/json',
            headers=self.test_headers
        )
        
        # Assert response
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.data)
        self.assertTrue(response_data['success'])
        self.assertIn('campaign_id', response_data)
        
        # Verify Firestore operations
        users_collection = fake_firestore._collections.get('users')
        self.assertIsNotNone(users_collection)
        
        user_doc = users_collection._docs.get(self.test_user_id)
        self.assertIsNotNone(user_doc)
        
        campaigns_collection = user_doc._collections.get('campaigns')
        self.assertIsNotNone(campaigns_collection)
        
        # Should have one campaign
        campaign_docs = list(campaigns_collection._docs.values())
        self.assertEqual(len(campaign_docs), 1)
        
        # Verify Gemini was called
        fake_genai_client.models.generate_content.assert_called_once()
        
    @patch('firebase_admin.firestore.client')
    @patch('google.genai.Client')
    def test_create_campaign_gemini_error(self, mock_genai_client_class, mock_firestore_client):
        """Test campaign creation when Gemini API fails."""
        
        # Set up fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_firestore_client.return_value = fake_firestore
        
        # Set up fake Gemini client to raise an error
        fake_genai_client = MagicMock()
        mock_genai_client_class.return_value = fake_genai_client
        fake_genai_client.models.count_tokens.return_value = FakeTokenCount(1000)
        fake_genai_client.models.generate_content.side_effect = Exception("Gemini API error")
        
        # Make the API request
        response = self.client.post(
            '/api/campaigns',
            data=json.dumps(self.test_campaign_data),
            content_type='application/json',
            headers=self.test_headers
        )
        
        # Assert error response
        self.assertEqual(response.status_code, 500)
        response_data = json.loads(response.data)
        self.assertIn('error', response_data)
        
    def test_create_campaign_no_auth(self):
        """Test campaign creation without authentication."""
        
        # Make the API request without test headers
        response = self.client.post(
            '/api/campaigns',
            data=json.dumps(self.test_campaign_data),
            content_type='application/json',
            headers={'Authorization': 'Bearer invalid-token'}
        )
        
        # Assert auth error
        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.data)
        self.assertIn('error', response_data)
        
    def test_create_campaign_missing_fields(self):
        """Test campaign creation with missing required fields."""
        
        # Remove required field
        incomplete_data = self.test_campaign_data.copy()
        del incomplete_data['title']
        
        # Make the API request
        response = self.client.post(
            '/api/campaigns',
            data=json.dumps(incomplete_data),
            content_type='application/json',
            headers=self.test_headers
        )
        
        # Assert validation error
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertIn('error', response_data)


if __name__ == '__main__':
    unittest.main()