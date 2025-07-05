"""
Test debug content logging functionality.
"""
import unittest
import json
import logging
import os
from unittest.mock import Mock, patch, MagicMock
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Mock firebase_admin before importing main
mock_firebase_admin = MagicMock()
mock_firestore = MagicMock()
mock_auth = MagicMock()
mock_firebase_admin.firestore = mock_firestore
mock_firebase_admin.auth = mock_auth

sys.modules['firebase_admin'] = mock_firebase_admin
sys.modules['firebase_admin.firestore'] = mock_firestore
sys.modules['firebase_admin.auth'] = mock_auth

from game_state import GameState
from main import create_app, DEFAULT_TEST_USER, HEADER_TEST_BYPASS, HEADER_TEST_USER_ID
import constants


class TestDebugLogging(unittest.TestCase):
    """Test debug content logging for monitoring."""
    
    def setUp(self):
        """Set up test environment."""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.mock_user_id = DEFAULT_TEST_USER
        self.mock_campaign_id = "test_campaign_logging"
        
        self.test_headers = {
            HEADER_TEST_BYPASS: 'true',
            HEADER_TEST_USER_ID: self.mock_user_id
        }
        
        self.campaign_data = {
            'id': self.mock_campaign_id,
            'title': 'Test Logging Campaign',
            'prompt': 'Test campaign for debug logging',
            'selected_prompts': ['narrative', 'mechanics']
        }
        
        self.game_state = GameState(
            player_character_data={'name': 'Test Hero', 'hp_current': 10, 'hp_max': 10},
            debug_mode=True
        )
    
    @patch('main.firestore_service')
    def test_logs_when_debug_content_present(self, mock_firestore_service):
        """Test that system logs when debug content is generated."""
        mock_firestore_service.get_campaign_game_state.return_value = self.game_state
        mock_firestore_service.get_campaign_by_id.return_value = (self.campaign_data, [])
        mock_firestore_service.add_story_entry.return_value = None
        
        # Mock AI response with all debug content types
        ai_response = (
            "You enter the room. "
            "[DEBUG_START]Checking for traps...[DEBUG_END] "
            "[DEBUG_ROLL_START]Perception: 1d20+3 = 18[DEBUG_ROLL_END] "
            "[DEBUG_STATE_START]No traps found[DEBUG_STATE_END]"
        )
        
        # Create mock GeminiResponse
        mock_gemini_response = MagicMock()
        mock_gemini_response.narrative_text = ai_response
        mock_gemini_response.debug_tags_present = {'dm_notes': True, 'dice_rolls': True, 'state_changes': True}
        mock_gemini_response.state_updates = {}
        mock_gemini_response.structured_response = None
        
        with patch('gemini_service.continue_story', return_value=mock_gemini_response):
            with self.assertLogs(level='INFO') as log:
                    response = self.client.post(
                        f'/api/campaigns/{self.mock_campaign_id}/interaction',
                        json={'input': 'I enter the room', 'mode': 'character'},
                        headers=self.test_headers
                    )
                    
                    self.assertEqual(response.status_code, 200)
                    
                    # Check that info log was created
                    log_output = '\n'.join(log.output)
                    self.assertIn('Debug content generated for campaign', log_output)
                    self.assertIn("'dm_notes': True", log_output)
                    self.assertIn("'dice_rolls': True", log_output)
                    self.assertIn("'state_changes': True", log_output)
    
    @patch('main.firestore_service')
    def test_logs_warning_when_debug_content_missing(self, mock_firestore_service):
        """Test that system logs warning when debug content is missing."""
        mock_firestore_service.get_campaign_game_state.return_value = self.game_state
        mock_firestore_service.get_campaign_by_id.return_value = (self.campaign_data, [])
        mock_firestore_service.add_story_entry.return_value = None
        
        # Mock AI response WITHOUT debug content (simulating AI not following instructions)
        ai_response = "You enter the room. It appears to be empty."
        
        # Create mock GeminiResponse
        mock_gemini_response = MagicMock()
        mock_gemini_response.narrative_text = ai_response
        mock_gemini_response.debug_tags_present = {'dm_notes': False, 'dice_rolls': False, 'state_changes': False}
        mock_gemini_response.state_updates = {}
        mock_gemini_response.structured_response = None
        
        with patch('gemini_service.continue_story', return_value=mock_gemini_response):
            with self.assertLogs(level='WARNING') as log:
                    response = self.client.post(
                        f'/api/campaigns/{self.mock_campaign_id}/interaction',
                        json={'input': 'I enter the room', 'mode': 'character'},
                        headers=self.test_headers
                    )
                    
                    self.assertEqual(response.status_code, 200)
                    
                    # Check that warning logs were created
                    log_output = '\n'.join(log.output)
                    self.assertIn('AI response missing debug content', log_output)
                    self.assertIn("'dm_notes': False", log_output)
                    self.assertIn("'dice_rolls': False", log_output)
                    self.assertIn("'state_changes': False", log_output)
                    self.assertIn('Response length:', log_output)
    
    @patch('main.firestore_service')
    def test_logs_partial_debug_content(self, mock_firestore_service):
        """Test logging when only some debug content types are present."""
        mock_firestore_service.get_campaign_game_state.return_value = self.game_state
        mock_firestore_service.get_campaign_by_id.return_value = (self.campaign_data, [])
        mock_firestore_service.add_story_entry.return_value = None
        
        # Mock AI response with only dice rolls (missing DM notes and state changes)
        ai_response = (
            "You attack the goblin! "
            "[DEBUG_ROLL_START]Attack: 1d20+5 = 19 (Hit!)[DEBUG_ROLL_END] "
            "Your sword strikes true!"
        )
        
        # Create mock GeminiResponse
        mock_gemini_response = MagicMock()
        mock_gemini_response.narrative_text = ai_response
        mock_gemini_response.debug_tags_present = {'dm_notes': False, 'dice_rolls': True, 'state_changes': False}
        mock_gemini_response.state_updates = {}
        mock_gemini_response.structured_response = None
        
        with patch('gemini_service.continue_story', return_value=mock_gemini_response):
            with self.assertLogs(level='INFO') as log:
                    response = self.client.post(
                        f'/api/campaigns/{self.mock_campaign_id}/interaction',
                        json={'input': 'I attack the goblin', 'mode': 'character'},
                        headers=self.test_headers
                    )
                    
                    self.assertEqual(response.status_code, 200)
                    
                    # Check that info log shows partial content
                    log_output = '\n'.join(log.output)
                    self.assertIn('Debug content generated for campaign', log_output)
                    self.assertIn("'dm_notes': False", log_output)
                    self.assertIn("'dice_rolls': True", log_output)
                    self.assertIn("'state_changes': False", log_output)


if __name__ == '__main__':
    unittest.main()