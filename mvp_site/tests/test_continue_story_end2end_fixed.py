"""
End-to-end integration test for continuing a story - FIXED VERSION.
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
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import create_app, HEADER_TEST_BYPASS, HEADER_TEST_USER_ID, DEFAULT_TEST_USER
import constants
from game_state import GameState
import gemini_service
from fake_firestore import FakeFirestoreClient, FakeFirestoreDocument, FakeGeminiResponse, FakeTokenCount


class TestContinueStoryEnd2End(unittest.TestCase):
    """Test continuing a story through the full application stack."""
    
    def setUp(self):
        """Set up test client and mocks."""
        # Reset gemini service client to ensure our mock is used
        gemini_service._client = None
        
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Test data
        self.test_user_id = "test-user-123"
        self.test_campaign_id = "test-campaign-456"
        
        # Test headers for bypassing auth in test mode
        self.test_headers = {
            HEADER_TEST_BYPASS: 'true',
            HEADER_TEST_USER_ID: self.test_user_id
        }
        
        self.test_interaction_data = {
            "input": "I draw my sword and approach the dragon cautiously",
            "mode": "character"
        }
        
        # Mock campaign data
        self.mock_campaign_data = {
            'id': self.test_campaign_id,
            'user_id': self.test_user_id,
            'title': 'Dragon Quest',
            'created_at': '2024-01-15T10:30:00Z',
            'initial_prompt': 'A brave warrior faces a dragon',
            'selected_prompts': ['narrative', 'mechanics']
        }
        
        # Mock existing game state
        self.mock_game_state = GameState(
            player_character_data={
                'name': 'Thorin the Bold',
                'level': 3,
                'hp_current': 25,
                'hp_max': 30
            },
            world_data={
                'current_location_name': 'Dragon\'s Lair'
            }
        )
        
        # Mock existing story entries
        self.mock_story_entries = [
            {
                'actor': 'user',
                'text': 'A brave warrior faces a dragon',
                'timestamp': '2024-01-15T10:30:00Z',
                'sequence_id': 1,
                'mode': 'god'
            },
            {
                'actor': 'gemini', 
                'text': 'You stand before the mighty dragon...',
                'timestamp': '2024-01-15T10:31:00Z',
                'sequence_id': 2,
                'user_scene_number': 1
            }
        ]
        
    def tearDown(self):
        """Reset gemini service client after each test."""
        gemini_service._client = None
        
    @patch('firebase_admin.firestore.client')
    @patch('google.genai.Client')
    def test_continue_story_success(self, mock_genai_client_class, mock_firestore_client):
        """Test successfully continuing a story."""
        
        # Set up fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_firestore_client.return_value = fake_firestore
        
        # Pre-populate campaign data in the correct location
        user_doc = fake_firestore.collection('users').document(self.test_user_id)
        campaign_doc = user_doc.collection('campaigns').document(self.test_campaign_id)
        campaign_doc.set(self.mock_campaign_data)
        
        # Pre-populate game state
        game_state_doc = fake_firestore.document(f'campaigns/{self.test_campaign_id}/game_state')
        game_state_doc.set(self.mock_game_state.to_dict())
        
        # Pre-populate story entries
        story_collection = fake_firestore.collection(f'campaigns/{self.test_campaign_id}/story')
        for entry in self.mock_story_entries:
            story_collection.add(entry)
        
        # Set up fake Gemini client
        fake_genai_client = MagicMock()
        mock_genai_client_class.return_value = fake_genai_client
        fake_genai_client.models.count_tokens.return_value = FakeTokenCount(1000)
        
        # Mock Gemini response with proper JSON planning block
        response_json = json.dumps({
            "narrative": "As you draw your sword, the dragon's eyes narrow...",
            "planning_block": {
                "thinking": "The dragon prepares for combat. Your next move will be crucial.",
                "choices": {
                    "1": {"text": "Attack", "description": "Attack the dragon with your sword"},
                    "2": {"text": "Defend", "description": "Defend and raise your shield"}, 
                    "3": {"text": "Communicate", "description": "Try to communicate with the dragon"}
                }
            },
            "state_updates": {
                "combat_state": {
                    "in_combat": True
                }
            },
            "dice_rolls": ["Initiative: 1d20+2 = 15"],
            "choices": {
                "1": {"text": "Attack", "description": "Strike with your sword"},
                "2": {"text": "Defend", "description": "Raise your shield"}
            }
        })
        fake_genai_client.models.generate_content.return_value = FakeGeminiResponse(response_json)
        
        # Make the API request
        response = self.client.post(
            f'/api/campaigns/{self.test_campaign_id}/interaction',
            data=json.dumps(self.test_interaction_data),
            content_type='application/json',
            headers=self.test_headers
        )
        
        # Assert response
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        
        # Verify response structure (robust assertions)
        self.assertIn('narrative', response_data)
        # Basic structure validation
        self.assertIsInstance(response_data, dict)
        self.assertTrue(response_data['success'])
        
        # Verify narrative
        self.assertIn("dragon's eyes narrow", response_data['narrative'])
        
        # Verify state update happened
        self.assertIn('state_updates', response_data)
        self.assertTrue(response_data['state_updates']['combat_state']['in_combat'])
        
        # Verify Gemini was called (may be called multiple times due to dual-pass generation)
        self.assertTrue(fake_genai_client.models.generate_content.called)
        
    @patch('firebase_admin.firestore.client')
    def test_continue_story_unauthorized(self, mock_firestore_client):
        """Test continuing a story for a campaign owned by another user."""
        
        # Set up fake Firestore
        fake_firestore = FakeFirestoreClient()
        mock_firestore_client.return_value = fake_firestore
        
        # Pre-populate campaign data with different user
        different_user_campaign = self.mock_campaign_data.copy()
        different_user_campaign['user_id'] = 'different-user-999'
        
        # Put campaign under different user's collection
        different_user_doc = fake_firestore.collection('users').document('different-user-999')
        campaign_doc = different_user_doc.collection('campaigns').document(self.test_campaign_id)
        campaign_doc.set(different_user_campaign)
        
        # Make the API request
        response = self.client.post(
            f'/api/campaigns/{self.test_campaign_id}/interaction',
            data=json.dumps(self.test_interaction_data),
            content_type='application/json',
            headers=self.test_headers
        )
        
        # Assert forbidden
        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.data)
        self.assertIn('error', response_data)


if __name__ == '__main__':
    unittest.main()