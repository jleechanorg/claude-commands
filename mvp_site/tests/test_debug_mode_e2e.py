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
        
        # Check that _build_debug_instructions exists and contains the right content
        build_debug_source = inspect.getsource(gemini_service._build_debug_instructions)
        self.assertIn("DEBUG MODE - ALWAYS GENERATE", build_debug_source)
        
        # Check that build_core_system_instructions adds debug instructions
        build_core_source = inspect.getsource(gemini_service.PromptBuilder.build_core_system_instructions)
        
        # Verify debug instructions are added (third in the sequence after master directive and game state)
        self.assertIn("# Add debug mode instructions THIRD for technical functionality", build_core_source)
        self.assertIn("parts.append(_build_debug_instructions())", build_core_source)
        
        # Verify there's no conditional check for debug_mode
        lines = build_core_source.split('\n')
        for i, line in enumerate(lines):
            if '_build_debug_instructions' in line:
                # Check previous lines for any 'if' statement
                found_conditional = False
                for j in range(max(0, i - 5), i):
                    if 'if' in lines[j] and 'debug' in lines[j]:
                        found_conditional = True
                        break
                self.assertFalse(found_conditional, 
                    "Debug instructions should not be conditional on debug_mode")
    
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
        def capture_story_entry(user_id, campaign_id, actor, text, mode=None, structured_fields=None):
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
        
        # Create mock GeminiResponse
        mock_gemini_response = MagicMock()
        mock_gemini_response.narrative_text = ai_response_with_debug
        mock_gemini_response.debug_tags_present = {"dm_notes": True, "dice_rolls": True, "state_changes": False}
        mock_gemini_response.state_updates = {}
        mock_gemini_response.structured_response = None
        # Mock get_narrative_text to return stripped version when debug_mode=False
        def mock_get_narrative_text(debug_mode=True):
            if debug_mode:
                return ai_response_with_debug
            else:
                # Strip debug content
                import re
                text = ai_response_with_debug
                text = re.sub(r'\[DEBUG_START\].*?\[DEBUG_END\]', '', text, flags=re.DOTALL)
                text = re.sub(r'\[DEBUG_ROLL_START\].*?\[DEBUG_ROLL_END\]', '', text, flags=re.DOTALL)
                return text.strip()
        mock_gemini_response.get_narrative_text = MagicMock(side_effect=mock_get_narrative_text)

        with patch('gemini_service.continue_story', return_value=mock_gemini_response):
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
        
        # Create mock GeminiResponse
        mock_gemini_response = MagicMock()
        mock_gemini_response.narrative_text = ai_response_with_debug
        mock_gemini_response.debug_tags_present = {"dm_notes": True, "dice_rolls": True, "state_changes": False}
        mock_gemini_response.state_updates = {}
        mock_gemini_response.structured_response = None
        # Mock get_narrative_text to return stripped version when debug_mode=False
        def mock_get_narrative_text(debug_mode=True):
            if debug_mode:
                return ai_response_with_debug
            else:
                # Strip debug content
                import re
                text = ai_response_with_debug
                text = re.sub(r'\[DEBUG_START\].*?\[DEBUG_END\]', '', text, flags=re.DOTALL)
                text = re.sub(r'\[DEBUG_ROLL_START\].*?\[DEBUG_ROLL_END\]', '', text, flags=re.DOTALL)
                return text.strip()
        mock_gemini_response.get_narrative_text = MagicMock(side_effect=mock_get_narrative_text)

        with patch('gemini_service.continue_story', return_value=mock_gemini_response):
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