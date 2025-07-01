"""
Test debug mode functionality.
"""
import unittest
import json
import tempfile
import shutil
import os
from unittest.mock import Mock, patch, MagicMock

# Mock firebase_admin before importing main - following working test pattern
mock_firebase_admin = MagicMock()
mock_firestore = MagicMock()
mock_auth = MagicMock()
mock_firebase_admin.firestore = mock_firestore
mock_firebase_admin.auth = mock_auth

# Apply the mock to sys.modules
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

sys.modules['firebase_admin'] = mock_firebase_admin
sys.modules['firebase_admin.firestore'] = mock_firestore
sys.modules['firebase_admin.auth'] = mock_auth

from game_state import GameState
from main import create_app, DEFAULT_TEST_USER, HEADER_TEST_BYPASS, HEADER_TEST_USER_ID
import constants
import gemini_service


class TestDebugMode(unittest.TestCase):
    """Test debug mode toggle and visibility features."""
    
    def setUp(self):
        """Set up test environment."""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.temp_dir = tempfile.mkdtemp()
        self.mock_user_id = DEFAULT_TEST_USER
        self.mock_campaign_id = "test_campaign_456"
        
        # Use consistent test headers like working tests
        self.test_headers = {
            HEADER_TEST_BYPASS: 'true',
            HEADER_TEST_USER_ID: self.mock_user_id
        }
        
        # Create a basic campaign
        self.campaign_data = {
            'id': self.mock_campaign_id,
            'title': 'Test Debug Campaign',
            'prompt': 'A test campaign for debug mode',
            'selected_prompts': ['narrative', 'mechanics']
        }
        
        # Initialize game state with debug mode off
        self.game_state = GameState(
            player_character_data={'name': 'Test Hero', 'hp_current': 10, 'hp_max': 10},
            debug_mode=False
        )
        
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('main.firestore_service')
    def test_debug_mode_toggle_commands(self, mock_firestore_service):
        """Test that debug mode can be toggled with commands."""
        # Set up mock data using pattern from working tests
        mock_firestore_service.get_campaign_game_state.return_value = self.game_state
        mock_firestore_service.get_campaign_by_id.return_value = (self.campaign_data, [])
        mock_firestore_service.update_campaign_game_state.return_value = None
        mock_firestore_service.add_story_entry.return_value = None
        
        # Test enabling debug mode
        response = self.client.post(
            f'/api/campaigns/{self.mock_campaign_id}/interaction',
            json={'input': 'enable debug mode', 'mode': 'god'},
            headers=self.test_headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data.get('success'))
        self.assertIn('Debug mode enabled', data.get('response', ''))
        self.assertTrue(data.get('debug_mode'))
        
        # Verify state was updated
        updated_state = mock_firestore_service.update_campaign_game_state.call_args[0][2]
        self.assertTrue(updated_state.get('debug_mode'))
        
        # Test disabling debug mode
        self.game_state.debug_mode = True  # Set it to enabled first
        response = self.client.post(
            f'/api/campaigns/{self.mock_campaign_id}/interaction',
            json={'input': 'disable debug mode', 'mode': 'god'},
            headers=self.test_headers
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data.get('success'))
        self.assertIn('Debug mode disabled', data.get('response', ''))
        self.assertFalse(data.get('debug_mode'))
    
    @patch('main.firestore_service')
    def test_debug_content_shown_when_enabled(self, mock_firestore_service):
        """Test that debug content is shown when debug mode is enabled."""
        # Enable debug mode
        self.game_state.debug_mode = True
        mock_firestore_service.get_campaign_game_state.return_value = self.game_state
        mock_firestore_service.get_campaign_by_id.return_value = (self.campaign_data, [])
        mock_firestore_service.add_story_entry.return_value = None
        
        # Mock Gemini to return debug content (AI now always generates debug content)
        mock_response = (
            "You enter the dark cave. "
            "[DEBUG_START]As the DM, I'm rolling a perception check...[DEBUG_END] "
            "[DEBUG_ROLL_START]Perception: 1d20+3 = 15+3 = 18 (Success)[DEBUG_ROLL_END] "
            "You notice a glimmer in the darkness."
        )
        
        with patch('gemini_service.continue_story', return_value=mock_response):
            with patch('gemini_service.parse_llm_response_for_state_changes', return_value={}):
                response = self.client.post(
                    f'/api/campaigns/{self.mock_campaign_id}/interaction',
                    json={'input': 'I enter the cave', 'mode': 'character'},
                    headers=self.test_headers
                )
                
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.data)
                self.assertTrue(data.get('debug_mode'))
                # When debug mode is enabled, user should see debug content
                self.assertIn('[DEBUG_START]', data.get('response', ''))
                self.assertIn('[DEBUG_END]', data.get('response', ''))
                self.assertIn('[DEBUG_ROLL_START]', data.get('response', ''))
                self.assertIn('[DEBUG_ROLL_END]', data.get('response', ''))
                
                # Verify full response was saved to database
                mock_firestore_service.add_story_entry.assert_called_with(
                    self.mock_user_id, self.mock_campaign_id, 'gemini', mock_response
                )
    
    @patch('main.firestore_service')
    def test_enhanced_dice_roll_display(self, mock_firestore_service):
        """Test that enhanced dice roll information is displayed in debug mode."""
        # Enable debug mode
        self.game_state.debug_mode = True
        mock_firestore_service.get_campaign_game_state.return_value = self.game_state
        mock_firestore_service.get_campaign_by_id.return_value = (self.campaign_data, [])
        mock_firestore_service.add_story_entry.return_value = None
        
        # Mock Gemini to return enhanced dice roll content
        mock_response = (
            "You attack the orc! "
            "[DEBUG_ROLL_START]Attack Roll: 1d20+5 = 14+5 = 19 vs AC 15 (Hit!)[DEBUG_ROLL_END] "
            "[DEBUG_ROLL_START]Damage Roll: 1d8+3 = 6+3 = 9 slashing damage[DEBUG_ROLL_END] "
            "Your sword strikes true, dealing a devastating blow!"
        )
        
        with patch('gemini_service.continue_story', return_value=mock_response):
            with patch('gemini_service.parse_llm_response_for_state_changes', return_value={}):
                response = self.client.post(
                    f'/api/campaigns/{self.mock_campaign_id}/interaction',
                    json={'input': 'I attack with my sword', 'mode': 'character'},
                    headers=self.test_headers
                )
                
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.data)
                self.assertTrue(data.get('debug_mode'))
                response_text = data.get('response', '')
                
                # Verify multiple dice rolls are shown
                self.assertEqual(response_text.count('[DEBUG_ROLL_START]'), 2)
                self.assertEqual(response_text.count('[DEBUG_ROLL_END]'), 2)
                
                # Verify specific roll information
                self.assertIn('Attack Roll: 1d20+5', response_text)
                self.assertIn('Damage Roll: 1d8+3', response_text)
                self.assertIn('vs AC 15', response_text)
                self.assertIn('slashing damage', response_text)
    
    @patch('main.firestore_service')
    def test_debug_content_hidden_when_disabled(self, mock_firestore_service):
        """Test that debug content is hidden when debug mode is disabled."""
        # Disable debug mode (default)
        self.game_state.debug_mode = False
        mock_firestore_service.get_campaign_game_state.return_value = self.game_state
        mock_firestore_service.get_campaign_by_id.return_value = (self.campaign_data, [])
        mock_firestore_service.add_story_entry.return_value = None
        
        # Mock Gemini to return debug content (AI now always generates debug content)
        mock_response = (
            "You enter the dark cave. "
            "[DEBUG_START]As the DM, I'm rolling a perception check...[DEBUG_END] "
            "[DEBUG_ROLL_START]Perception: 1d20+3 = 15+3 = 18 (Success)[DEBUG_ROLL_END] "
            "You notice a glimmer in the darkness."
        )
        
        with patch('gemini_service.continue_story', return_value=mock_response):
            with patch('gemini_service.parse_llm_response_for_state_changes', return_value={}):
                response = self.client.post(
                    f'/api/campaigns/{self.mock_campaign_id}/interaction',
                    json={'input': 'I enter the cave', 'mode': 'character'},
                    headers=self.test_headers
                )
                
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.data)
                self.assertFalse(data.get('debug_mode'))
                # When debug mode is disabled, user should NOT see debug content
                self.assertNotIn('[DEBUG_START]', data.get('response', ''))
                self.assertNotIn('[DEBUG_END]', data.get('response', ''))
                self.assertNotIn('[DEBUG_ROLL_START]', data.get('response', ''))
                self.assertNotIn('[DEBUG_ROLL_END]', data.get('response', ''))
                # But should still see the main narrative
                self.assertIn('You enter the dark cave', data.get('response', ''))
                self.assertIn('You notice a glimmer in the darkness', data.get('response', ''))
                
                # Verify full response (with debug content) was saved to database
                mock_firestore_service.add_story_entry.assert_called_with(
                    self.mock_user_id, self.mock_campaign_id, 'gemini', mock_response
                )
    
    @patch('main.firestore_service')
    def test_debug_mode_only_in_god_mode(self, mock_firestore_service):
        """Test that debug mode commands only work in god mode."""
        mock_firestore_service.get_campaign_game_state.return_value = self.game_state
        mock_firestore_service.get_campaign_by_id.return_value = (self.campaign_data, [])
        mock_firestore_service.add_story_entry.return_value = None
        
        # Mock Gemini to return a normal response
        with patch('gemini_service.continue_story', return_value="You speak the words but nothing happens."):
            with patch('gemini_service.parse_llm_response_for_state_changes', return_value={}):
                response = self.client.post(
                    f'/api/campaigns/{self.mock_campaign_id}/interaction',
                    json={'input': 'enable debug mode', 'mode': 'character'},
                    headers=self.test_headers
                )
                
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.data)
                # Should get AI response, not system message
                self.assertNotIn('System Message', data.get('response', ''))
                self.assertFalse(data.get('debug_mode', False))


if __name__ == '__main__':
    unittest.main()