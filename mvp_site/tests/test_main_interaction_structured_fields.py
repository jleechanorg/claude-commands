#!/usr/bin/env python3
"""
Unit tests for main.py interaction endpoint with structured fields.
Tests that structured fields are properly extracted and returned to the frontend.
"""
import unittest
import sys
import os
import json
from unittest.mock import Mock, patch, MagicMock

# Add the mvp_site directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import create_app, DEFAULT_TEST_USER, HEADER_TEST_BYPASS, HEADER_TEST_USER_ID
import constants
from narrative_response_schema import NarrativeResponse
from gemini_response import GeminiResponse
from game_state import GameState


class TestMainInteractionStructuredFields(unittest.TestCase):
    """Test structured fields in main.py interaction endpoint"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Test headers for authentication bypass
        self.test_headers = {
            HEADER_TEST_BYPASS: 'true',
            HEADER_TEST_USER_ID: DEFAULT_TEST_USER
        }
        
        # Mock user data
        self.user_id = DEFAULT_TEST_USER
        self.campaign_id = 'test-campaign-456'
        
        # Sample structured response data
        self.structured_data = {
            'session_header': 'Turn 5 - Combat Round\nHP: 20/30 | AC: 16',
            'planning_block': '1. Attack with sword\n2. Cast spell\n3. Defend',
            'dice_rolls': ['d20+3: 18', '1d8+2: 6'],
            'resources': 'HP: 20/30, SP: 8/15',
            'debug_info': {
                'turn_number': 5,
                'combat_active': True,
                'dm_notes': 'Player chose aggressive approach'
            }
        }
    
    def create_mock_gemini_response(self, with_structured_fields=True):
        """Create a mock GeminiResponse with structured fields"""
        mock_response = Mock(spec=GeminiResponse)
        mock_response.narrative_text = "The battle rages on!"
        mock_response.debug_tags_present = {'dm_notes': True, 'dice_rolls': True, 'state_changes': False}
        mock_response.state_updates = {}
        mock_response.get_narrative_text = Mock(return_value="The battle rages on!")
        
        if with_structured_fields:
            mock_structured_response = Mock(spec=NarrativeResponse)
            mock_structured_response.session_header = self.structured_data['session_header']
            mock_structured_response.planning_block = self.structured_data['planning_block']
            mock_structured_response.dice_rolls = self.structured_data['dice_rolls']
            mock_structured_response.resources = self.structured_data['resources']
            mock_structured_response.debug_info = self.structured_data['debug_info']
            mock_response.structured_response = mock_structured_response
        else:
            mock_response.structured_response = None
        
        return mock_response

    def setup_common_mocks(self, mock_firestore_service, mock_gemini_service, mock_gemini_response):
        """Helper method to set up common mocks used by all test methods"""
        # Setup user and campaign mocks
        mock_firestore_service.get_user_by_id.return_value = {'id': self.user_id}
        mock_firestore_service.get_campaign_by_id.return_value = ({'id': self.campaign_id}, [])
        
        # Setup game state mock
        mock_game_state = {
            'player_character_data': {'name': 'Test Hero', 'hp_current': 20, 'hp_max': 30},
            'debug_mode': True
        }
        mock_firestore_service.get_game_state.return_value = mock_game_state
        mock_game_state_obj = GameState.from_dict(mock_game_state)
        mock_firestore_service.get_campaign_game_state.return_value = mock_game_state_obj
        
        # Setup gemini service mocks
        mock_gemini_service.continue_story.return_value = mock_gemini_response
        mock_gemini_service.parse_llm_response_for_state_changes.return_value = {}
    
    @patch('main.firestore_service')
    @patch('main.gemini_service')
    def test_interaction_endpoint_with_structured_fields(self, mock_gemini_service, mock_firestore_service):
        """Test that interaction endpoint properly extracts and returns structured fields"""
        # Create mock GeminiResponse with structured fields
        mock_gemini_response = self.create_mock_gemini_response(with_structured_fields=True)
        
        # Setup all common mocks
        self.setup_common_mocks(mock_firestore_service, mock_gemini_service, mock_gemini_response)
        
        # Make request to interaction endpoint
        response = self.client.post(
            f'/api/campaigns/{self.campaign_id}/interaction',
            headers=self.test_headers,
            json={'input': 'I attack the goblin!'}
        )
        
        # Verify response is successful
        self.assertEqual(response.status_code, 200)
        
        # Parse response data
        response_data = json.loads(response.data.decode('utf-8'))
        
        # Verify structured fields are included directly in response
        self.assertEqual(response_data[constants.FIELD_SESSION_HEADER], 
                        self.structured_data['session_header'])
        self.assertEqual(response_data[constants.FIELD_PLANNING_BLOCK], 
                        self.structured_data['planning_block'])
        self.assertEqual(response_data[constants.FIELD_DICE_ROLLS], 
                        self.structured_data['dice_rolls'])
        self.assertEqual(response_data[constants.FIELD_RESOURCES], 
                        self.structured_data['resources'])
        self.assertEqual(response_data[constants.FIELD_DEBUG_INFO], 
                        self.structured_data['debug_info'])
        
        # Verify structured fields are passed to firestore
        mock_firestore_service.add_story_entry.assert_called()
        call_args = mock_firestore_service.add_story_entry.call_args
        self.assertIn('structured_fields', call_args[1])
        firestore_structured_fields = call_args[1]['structured_fields']
        self.assertEqual(firestore_structured_fields[constants.FIELD_SESSION_HEADER], 
                        self.structured_data['session_header'])
    
    @patch('main.firestore_service')
    @patch('main.gemini_service')
    def test_interaction_endpoint_without_structured_fields(self, mock_gemini_service, mock_firestore_service):
        """Test interaction endpoint when GeminiResponse has no structured fields"""
        # Create mock GeminiResponse without structured fields
        mock_gemini_response = self.create_mock_gemini_response(with_structured_fields=False)
        
        # Setup all common mocks
        self.setup_common_mocks(mock_firestore_service, mock_gemini_service, mock_gemini_response)
        
        # Make request to interaction endpoint
        response = self.client.post(
            f'/api/campaigns/{self.campaign_id}/interaction',
            headers=self.test_headers,
            json={'input': 'I look around the room.'}
        )
        
        # Verify response is successful
        self.assertEqual(response.status_code, 200)
        
        # Parse response data
        response_data = json.loads(response.data.decode('utf-8'))
        
        # Verify structured fields are not present when gemini response has no structured fields
        self.assertNotIn(constants.FIELD_SESSION_HEADER, response_data)
        self.assertNotIn(constants.FIELD_PLANNING_BLOCK, response_data)
        self.assertNotIn(constants.FIELD_DICE_ROLLS, response_data)
        self.assertNotIn(constants.FIELD_RESOURCES, response_data)
        self.assertNotIn(constants.FIELD_DEBUG_INFO, response_data)
        
        # Verify empty structured fields are passed to firestore
        mock_firestore_service.add_story_entry.assert_called()
        call_args = mock_firestore_service.add_story_entry.call_args
        self.assertIn('structured_fields', call_args[1])
        firestore_structured_fields = call_args[1]['structured_fields']
        self.assertEqual(firestore_structured_fields, {})
    
    @patch('main.firestore_service')
    @patch('main.gemini_service')
    def test_interaction_endpoint_with_empty_structured_fields(self, mock_gemini_service, mock_firestore_service):
        """Test interaction endpoint when structured fields are empty"""
        # Setup mocks
        mock_firestore_service.get_user_by_id.return_value = {'id': self.user_id}
        mock_firestore_service.get_campaign_by_id.return_value = ({'id': self.campaign_id}, [])
        
        # Create mock GeminiResponse with empty structured fields
        mock_response = Mock(spec=GeminiResponse)
        mock_response.narrative_text = "You explore the empty room."
        mock_response.debug_tags_present = {'dm_notes': False, 'dice_rolls': False, 'state_changes': False}
        mock_response.state_updates = {}
        mock_response.get_narrative_text = Mock(return_value="You explore the empty room.")
        
        mock_structured_response = Mock(spec=NarrativeResponse)
        mock_structured_response.session_header = ''
        mock_structured_response.planning_block = ''
        mock_structured_response.dice_rolls = []
        mock_structured_response.resources = ''
        mock_structured_response.debug_info = {}
        mock_response.structured_response = mock_structured_response
        
        mock_gemini_service.continue_story.return_value = mock_response
        
        # Mock game state
        mock_firestore_service.get_game_state.return_value = {
            'player_character_data': {'name': 'Test Hero', 'hp_current': 30, 'hp_max': 30},
            'debug_mode': False
        }
        
        # Make request to interaction endpoint
        response = self.client.post(
            f'/api/campaigns/{self.campaign_id}/interaction',
            headers=self.test_headers,
            json={'input': 'I examine the room.'}
        )
        
        # Verify response is successful
        self.assertEqual(response.status_code, 200)
        
        # Parse response data
        response_data = json.loads(response.data.decode('utf-8'))
        
        # Verify structured fields are present but empty
        self.assertEqual(response_data[constants.FIELD_SESSION_HEADER], '')
        self.assertEqual(response_data[constants.FIELD_PLANNING_BLOCK], '')
        self.assertEqual(response_data[constants.FIELD_DICE_ROLLS], [])
        self.assertEqual(response_data[constants.FIELD_RESOURCES], '')
        self.assertEqual(response_data[constants.FIELD_DEBUG_INFO], {})
    
    @patch('main.firestore_service')
    @patch('main.gemini_service') 
    def test_interaction_endpoint_preserves_structured_field_types(self, mock_gemini_service, mock_firestore_service):
        """Test that structured fields preserve their data types"""
        # Setup mocks
        mock_firestore_service.get_user_by_id.return_value = {'id': self.user_id}
        mock_firestore_service.get_campaign_by_id.return_value = ({'id': self.campaign_id}, [])
        
        # Create mock with complex structured fields
        mock_response = Mock(spec=GeminiResponse)
        mock_response.narrative_text = "Complex response with various data types."
        mock_response.debug_tags_present = {'dm_notes': True, 'dice_rolls': True, 'state_changes': False}
        mock_response.state_updates = {}
        mock_response.get_narrative_text = Mock(return_value="Complex response with various data types.")
        
        mock_structured_response = Mock(spec=NarrativeResponse)
        mock_structured_response.session_header = 'String field'
        mock_structured_response.planning_block = 'Another string field'
        mock_structured_response.dice_rolls = ['d20: 15', 'd8: 6']  # List of strings
        mock_structured_response.resources = 'Resource string'
        mock_structured_response.debug_info = {  # Dict with various types
            'turn_number': 3,
            'combat_active': True,
            'enemy_list': ['goblin', 'orc'],
            'player_stats': {'hp': 25, 'ac': 16}
        }
        mock_response.structured_response = mock_structured_response
        
        mock_gemini_service.continue_story.return_value = mock_response
        
        # Mock game state
        mock_firestore_service.get_game_state.return_value = {
            'player_character_data': {'name': 'Test Hero', 'hp_current': 25, 'hp_max': 30},
            'debug_mode': True
        }
        
        # Make request to interaction endpoint
        response = self.client.post(
            f'/api/campaigns/{self.campaign_id}/interaction',
            headers=self.test_headers,
            json={'input': 'Cast fireball!'}
        )
        
        # Verify response is successful
        self.assertEqual(response.status_code, 200)
        
        # Parse response data
        response_data = json.loads(response.data.decode('utf-8'))
        
        # Verify data types are preserved
        self.assertIsInstance(response_data[constants.FIELD_SESSION_HEADER], str)
        self.assertIsInstance(response_data[constants.FIELD_PLANNING_BLOCK], str)
        self.assertIsInstance(response_data[constants.FIELD_DICE_ROLLS], list)
        self.assertIsInstance(response_data[constants.FIELD_RESOURCES], str)
        self.assertIsInstance(response_data[constants.FIELD_DEBUG_INFO], dict)
        
        # Verify nested data types in debug_info
        debug_info = response_data[constants.FIELD_DEBUG_INFO]
        self.assertIsInstance(debug_info['turn_number'], int)
        self.assertIsInstance(debug_info['combat_active'], bool)
        self.assertIsInstance(debug_info['enemy_list'], list)
        self.assertIsInstance(debug_info['player_stats'], dict)
        self.assertIsInstance(debug_info['player_stats']['hp'], int)


if __name__ == '__main__':
    unittest.main()