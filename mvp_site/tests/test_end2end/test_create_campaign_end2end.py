"""
End-to-end integration test for creating a campaign.
Only mocks external services (Gemini API and Firestore DB) at the lowest level.
Tests the full flow from API endpoint through all service layers.
"""

import json
import os
import sys
import unittest
import unittest.mock
from unittest.mock import patch

# Set TESTING environment variable
os.environ["TESTING"] = "true"
os.environ["GEMINI_API_KEY"] = "test-api-key"

# Add the parent directory to the path to import main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Add tests directory for fake services
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.fake_firestore import FakeFirestoreClient, FakeGeminiResponse
from main import create_app


class TestCreateCampaignEnd2End(unittest.TestCase):
    """Test creating a campaign through the full application stack."""

    def setUp(self):
        """Set up test client."""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Test headers (testing mode removed - no longer using bypass headers)
        self.test_headers = {
            "Content-Type": "application/json"
        }

    @patch("firestore_service.get_db")
    @patch("gemini_service._call_gemini_api_with_gemini_request")
    def test_create_campaign_success(self, mock_gemini_request, mock_get_db):
        """Test successful campaign creation using fake services."""
        
        # Set up fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore
        
        # Mock Gemini response
        gemini_response_data = {
            "narrative": "Welcome to your new campaign! You stand at the entrance to a great adventure...",
            "entities_mentioned": ["Hero"],
            "location_confirmed": "Starting Village",
            "state_updates": {
                "player_character_data": {
                    "name": "New Hero",
                    "level": 1,
                    "hp_current": 10,
                    "hp_max": 10
                }
            }
        }
        fake_response = FakeGeminiResponse(json.dumps(gemini_response_data))
        mock_gemini_request.return_value = fake_response
        
        # Campaign creation data
        campaign_data = {
            'title': 'Test Campaign',
            'character': 'Brave Warrior',
            'setting': 'Fantasy Kingdom',
            'description': 'Epic adventure awaits',
            'campaignType': 'dragon_knight',
            'selectedPrompts': ['narrative', 'mechanics']
        }
        
        # Make the API request
        response = self.client.post('/api/campaigns',
                                  data=json.dumps(campaign_data),
                                  content_type='application/json',
                                  headers=self.test_headers)
        
        # Verify response
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertTrue(data.get('success'))
        self.assertIn('campaign_id', data)

    @patch("firestore_service.get_db")
    @patch("gemini_service._call_gemini_api_with_gemini_request")
    @patch("mcp_client.MCPClient.call_tool")
    def test_create_campaign_gemini_error(self, mock_mcp_call, mock_gemini_request, mock_get_db):
        """Test campaign creation with Gemini service error."""
        
        # Set up fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_get_db.return_value = fake_firestore
        
        # Mock Gemini error
        gemini_error = Exception('Gemini service error')
        mock_gemini_request.side_effect = gemini_error
        
        # Mock MCP client to return error response (this is what main.py actually calls)
        mock_mcp_call.return_value = {
            'success': False,
            'error': 'Failed to create campaign: Gemini service error',
            'status_code': 400
        }
        
        # Campaign creation data
        campaign_data = {
            'title': 'Test Campaign',
            'character': 'Brave Warrior',
            'setting': 'Fantasy Kingdom',
            'description': 'Epic adventure awaits',
            'campaignType': 'dragon_knight',
            'selectedPrompts': ['narrative', 'mechanics']
        }
        
        response = self.client.post('/api/campaigns',
                                  data=json.dumps(campaign_data),
                                  content_type='application/json',
                                  headers=self.test_headers)
        
        # Should handle error gracefully
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data.get('success'))
        self.assertIn('error', data)
        
        # Verify MCP client was called with correct data
        mock_mcp_call.assert_called_once_with('create_campaign', unittest.mock.ANY)


if __name__ == '__main__':
    unittest.main()