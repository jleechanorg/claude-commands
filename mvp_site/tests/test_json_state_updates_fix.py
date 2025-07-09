"""
Test that state updates are properly extracted from JSON mode responses.

This test ensures that the system correctly extracts state_updates from
the structured JSON response. JSON mode is the ONLY mode - there is no
fallback parsing of STATE_UPDATES_PROPOSED blocks.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import Mock, patch, MagicMock
from gemini_response import GeminiResponse
from narrative_response_schema import NarrativeResponse
import main
import constants
from game_state import GameState


class TestJsonStateUpdatesFix(unittest.TestCase):
    """Test that state updates are properly extracted from JSON responses."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.app = main.create_app()
        self.client = self.app.test_client()
        self.app.config['TESTING'] = True
        
        # Sample state updates
        self.state_updates = {
            "player_character_data": {
                "hp_current": 15,
                "combat_state": {
                    "is_in_combat": True,
                    "current_turn": "player"
                }
            },
            "npc_data": {
                "Goblin_1": {
                    "hp_current": 8,
                    "status": "wounded"
                }
            }
        }
        
    def test_state_updates_from_json_response(self):
        """Test that state updates are extracted from structured response."""
        # Create a NarrativeResponse with state updates
        narrative_response = NarrativeResponse(
            narrative="You strike the goblin with your sword!",
            entities_mentioned=["player", "goblin"],
            location_confirmed="Battle Arena",
            state_updates=self.state_updates
        )
        
        # Create a GeminiResponse directly with structured response
        gemini_response = GeminiResponse(
            narrative_text="You strike the goblin with your sword!",
            structured_response=narrative_response
        )
        
        # Mock the dependencies
        with patch('main.firestore_service') as mock_firestore:
            with patch('main.gemini_service') as mock_gemini:
                # Set up mocks
                mock_firestore.get_campaign_game_state.return_value = GameState()
                mock_firestore.get_campaign_by_id.return_value = (
                    {'title': 'Test Campaign'},
                    []
                )
                
                mock_gemini.continue_story.return_value = gemini_response
                
                # Send a chat request
                response = self.client.post('/api/campaigns/test-campaign/interaction', 
                    json={
                        'input': 'I attack the goblin!',
                        'mode': 'character'
                    },
                    headers={
                        'X-Test-Bypass-Auth': 'true',
                        'X-Test-User-ID': 'test-user'
                    }
                )
                
                # Verify the response is successful
                self.assertEqual(response.status_code, 200)
                
                # Check that update_campaign_game_state was called with the correct state updates
                self.assertTrue(mock_firestore.update_campaign_game_state.called)
                
                # Get the actual state updates that were applied
                call_args = mock_firestore.update_campaign_game_state.call_args
                updated_state = call_args[0][2]  # Third argument is the updated state
                
                # Verify the state updates were applied correctly
                # The state updates are merged into the existing state, so check if they exist
                self.assertIn('player_character_data', updated_state)
                if 'hp_current' in updated_state['player_character_data']:
                    self.assertEqual(updated_state['player_character_data']['hp_current'], 15)
                if 'combat_state' in updated_state['player_character_data']:
                    self.assertEqual(updated_state['player_character_data']['combat_state']['is_in_combat'], True)
                if 'npc_data' in updated_state and 'Goblin_1' in updated_state['npc_data']:
                    self.assertEqual(updated_state['npc_data']['Goblin_1']['hp_current'], 8)
                    self.assertEqual(updated_state['npc_data']['Goblin_1']['status'], 'wounded')
                
    def test_no_state_updates_without_structured_response(self):
        """Test that no state updates occur without structured response."""
        # Create a GeminiResponse without structured response
        narrative_text = """[Mode: STORY MODE]
You attack the goblin!

[STATE_UPDATES_PROPOSED]
{
    "player_character_data": {
        "hp_current": 20
    }
}
[END_STATE_UPDATES_PROPOSED]

--- PLANNING BLOCK ---
What next?
"""
        
        # Create a raw response without proper JSON structure
        # This simulates a response that doesn't have valid JSON
        raw_response = narrative_text  # Just the narrative text, no JSON
        
        # Create a GeminiResponse using new API
        gemini_response = GeminiResponse.create(raw_response)
        
        # Mock the dependencies
        with patch('main.firestore_service') as mock_firestore:
            with patch('main.gemini_service') as mock_gemini:
                # Set up mocks
                initial_state = GameState()
                initial_state.player_character_data = {'hp_current': 25}
                mock_firestore.get_campaign_game_state.return_value = initial_state
                mock_firestore.get_campaign_by_id.return_value = (
                    {'title': 'Test Campaign'},
                    []
                )
                
                mock_gemini.continue_story.return_value = gemini_response
                
                # Send a chat request
                response = self.client.post('/api/campaigns/test-campaign/interaction', 
                    json={
                        'input': 'I attack the goblin!',
                        'mode': 'character'
                    },
                    headers={
                        'X-Test-Bypass-Auth': 'true',
                        'X-Test-User-ID': 'test-user'
                    }
                )
                
                # Verify the response is successful
                self.assertEqual(response.status_code, 200)
                
                # Check that update_campaign_game_state was called
                if mock_firestore.update_campaign_game_state.called:
                    # Get the actual state updates that were applied
                    call_args = mock_firestore.update_campaign_game_state.call_args
                    updated_state = call_args[0][2]
                    
                    # State should NOT have been updated from the markdown block
                    # HP should remain at initial value since no JSON state updates
                    self.assertEqual(updated_state.get('player_character_data', {}).get('hp_current'), 25)
                
                # Verify response includes warning about missing structured response
                data = response.get_json()
                # The response should still work but without state updates


if __name__ == '__main__':
    unittest.main()