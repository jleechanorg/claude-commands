"""
End-to-end test for debug mode functionality.
Tests that AI generates debug content and it's properly stripped/shown based on debug_mode.
"""
import unittest
import json
from unittest.mock import Mock, patch, MagicMock
import sys
import os

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
import gemini_service


class TestDebugModeE2E(unittest.TestCase):
    """End-to-end test for debug mode functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        self.mock_user_id = DEFAULT_TEST_USER
        self.mock_campaign_id = "test_campaign_e2e"
        
        self.test_headers = {
            HEADER_TEST_BYPASS: 'true',
            HEADER_TEST_USER_ID: self.mock_user_id
        }
        
        self.campaign_data = {
            'id': self.mock_campaign_id,
            'title': 'E2E Test Campaign',
            'prompt': 'Test campaign for E2E debug mode',
            'selected_prompts': ['narrative', 'mechanics']
        }
    
    def test_debug_content_always_in_ai_response(self):
        """Test that AI is instructed to always generate debug content."""
        # This test verifies the implementation by checking that the gemini_service
        # has the debug instructions that tell AI to always generate debug content
        import inspect
        
        source = inspect.getsource(gemini_service.continue_story)
        
        # Verify that the debug instructions are always added (not conditional)
        self.assertIn("DEBUG MODE - ALWAYS GENERATE", source)
        self.assertIn("system_instruction_parts.append(debug_instruction)", source)
        
        # Verify there's no conditional check for debug_mode before adding instructions
        # The old code had: if current_game_state.debug_mode:
        # The new code should not have this condition
        lines = source.split('\n')
        debug_instruction_line = None
        for i, line in enumerate(lines):
            if "DEBUG MODE - ALWAYS GENERATE" in line:
                debug_instruction_line = i
                break
        
        self.assertIsNotNone(debug_instruction_line, "Debug instruction not found")
        
        # Check that there's no 'if' statement controlling the debug instruction
        # Look backwards from the debug instruction line
        found_conditional = False
        for i in range(max(0, debug_instruction_line - 10), debug_instruction_line):
            if 'if' in lines[i] and 'debug_mode' in lines[i]:
                found_conditional = True
                break
        
        self.assertFalse(found_conditional, "Debug instructions should not be conditional on debug_mode")
    
    @patch('main.firestore_service')
    def test_full_e2e_debug_mode_disabled(self, mock_firestore_service):
        """Test full flow when debug mode is disabled."""
        # Set up game state with debug mode disabled
        game_state = GameState(
            player_character_data={'name': 'Test Hero', 'hp_current': 10, 'hp_max': 10},
            debug_mode=False
        )
        
        mock_firestore_service.get_campaign_game_state.return_value = game_state
        mock_firestore_service.get_campaign_by_id.return_value = (self.campaign_data, [])
        
        # Track what gets saved to database
        saved_responses = []
        def capture_story_entry(user_id, campaign_id, actor, text, mode=None):
            if actor == 'gemini':
                saved_responses.append(text)
        
        mock_firestore_service.add_story_entry.side_effect = capture_story_entry
        
        # Mock AI response with debug content
        ai_response_with_debug = (
            "You enter the tavern. "
            "[DEBUG_START]Rolling to see if any interesting NPCs are present...[DEBUG_END] "
            "[DEBUG_ROLL_START]Random Encounter: 1d20 = 17 (Interesting NPC present)[DEBUG_ROLL_END] "
            "A mysterious hooded figure sits in the corner."
        )
        
        with patch('gemini_service.continue_story', return_value=ai_response_with_debug):
            with patch('gemini_service.parse_llm_response_for_state_changes', return_value={}):
                response = self.client.post(
                    f'/api/campaigns/{self.mock_campaign_id}/interaction',
                    json={'input': 'I enter the tavern', 'mode': 'character'},
                    headers=self.test_headers
                )
                
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.data)
                
                # User should NOT see debug content
                user_response = data.get('response', '')
                self.assertNotIn('[DEBUG_START]', user_response)
                self.assertNotIn('[DEBUG_ROLL_START]', user_response)
                self.assertIn('You enter the tavern', user_response)
                self.assertIn('A mysterious hooded figure', user_response)
                
                # Database should have FULL response with debug
                self.assertEqual(len(saved_responses), 1)
                self.assertEqual(saved_responses[0], ai_response_with_debug)
    
    @patch('main.firestore_service')
    def test_full_e2e_debug_mode_enabled(self, mock_firestore_service):
        """Test full flow when debug mode is enabled."""
        # Set up game state with debug mode enabled
        game_state = GameState(
            player_character_data={'name': 'Test Hero', 'hp_current': 10, 'hp_max': 10},
            debug_mode=True
        )
        
        mock_firestore_service.get_campaign_game_state.return_value = game_state
        mock_firestore_service.get_campaign_by_id.return_value = (self.campaign_data, [])
        mock_firestore_service.add_story_entry.return_value = None
        
        # Mock AI response with debug content
        ai_response_with_debug = (
            "You enter the tavern. "
            "[DEBUG_START]Rolling to see if any interesting NPCs are present...[DEBUG_END] "
            "[DEBUG_ROLL_START]Random Encounter: 1d20 = 17 (Interesting NPC present)[DEBUG_ROLL_END] "
            "A mysterious hooded figure sits in the corner."
        )
        
        with patch('gemini_service.continue_story', return_value=ai_response_with_debug):
            with patch('gemini_service.parse_llm_response_for_state_changes', return_value={}):
                response = self.client.post(
                    f'/api/campaigns/{self.mock_campaign_id}/interaction',
                    json={'input': 'I enter the tavern', 'mode': 'character'},
                    headers=self.test_headers
                )
                
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.data)
                
                # User SHOULD see debug content
                user_response = data.get('response', '')
                self.assertIn('[DEBUG_START]', user_response)
                self.assertIn('[DEBUG_ROLL_START]', user_response)
                self.assertIn('Rolling to see if any interesting NPCs', user_response)
                self.assertIn('Random Encounter: 1d20 = 17', user_response)


if __name__ == '__main__':
    unittest.main()