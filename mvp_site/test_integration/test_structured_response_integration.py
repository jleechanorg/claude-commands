#!/usr/bin/env python3
"""Integration test for structured response fields flow"""
import unittest
from unittest.mock import MagicMock, patch
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import create_app
import constants


class TestStructuredResponseIntegration(unittest.TestCase):
    """Test structured fields flow with only external mocks"""
    
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.test_headers = {
            'X-Test-Bypass-Auth': 'true',
            'X-Test-User-ID': 'test-user'
        }
    
    @patch('gemini_service.genai.Client')
    @patch('firestore_service.firestore')
    def test_structured_response_flow(self, mock_firestore, mock_genai_client):
        """Test complete flow returns structured fields"""
        # Mock Firestore
        mock_db = MagicMock()
        mock_firestore.client.return_value = mock_db
        
        # Mock campaign exists
        mock_campaign = MagicMock()
        mock_campaign.to_dict.return_value = {
            'id': 'test-123',
            'title': 'Test Campaign',
            'game_state': {'debug_mode': True}
        }
        mock_campaign.exists = True
        
        # Mock Gemini response with schema fields
        mock_client_instance = MagicMock()
        mock_genai_client.return_value = mock_client_instance
        
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "narrative": "You attack! --- PLANNING BLOCK ---\nWhat next?",
            "entities_mentioned": ["goblin"],
            "location_confirmed": "Cave",
            "state_updates": {"npc_data": {"goblin_1": {"hp_current": 3}}},
            "debug_info": {
                "dice_rolls": ["1d20+5 = 18"],
                "resources": "HD: 2/2",
                "dm_notes": ["Test note"],
                "state_rationale": "Damage applied"
            }
        })
        
        mock_client_instance.models.generate_content.return_value = mock_response
        mock_client_instance.models.count_tokens.return_value = MagicMock(total_tokens=100)
        
        # Setup Firestore responses
        mock_db.collection.return_value.document.return_value.get.return_value = mock_campaign
        mock_db.collection.return_value.document.return_value.collection.return_value.stream.return_value = []
        
        # Make request
        response = self.client.post(
            '/api/campaigns/test-123/interaction',
            headers=self.test_headers,
            json={'input': 'I attack the goblin!'}
        )
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Check all fields present
        self.assertIn('response', data)
        self.assertIn('debug_info', data)
        self.assertIn('entities_mentioned', data)
        self.assertIn('location_confirmed', data)
        self.assertIn('state_updates', data)
        
        # Verify nested structure
        self.assertIn('dice_rolls', data['debug_info'])
        self.assertIn('resources', data['debug_info'])
        self.assertEqual(data['entities_mentioned'], ["goblin"])


if __name__ == '__main__':
    unittest.main()