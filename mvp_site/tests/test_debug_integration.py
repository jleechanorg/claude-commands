"""
Test debug hybrid system integration with main.py.
"""

import pytest
from unittest.mock import Mock, patch
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game_state import GameState


class TestDebugIntegration:
    """Test integration of hybrid debug system with main API."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock campaign data
        self.campaign = {
            'id': 'test123',
            'title': 'Test Campaign',
            'created_at': '2024-01-01'
        }
        
        # Mock story with old-style debug tags
        self.old_style_story = [
            {
                'actor': 'user',
                'text': 'I attack the goblin!',
                'timestamp': '2024-01-01T10:00:00'
            },
            {
                'actor': 'gemini',
                'text': 'You swing your sword! [DEBUG_START]Attack roll: 15[DEBUG_END] You hit the goblin!',
                'timestamp': '2024-01-01T10:00:01'
            },
            {
                'actor': 'gemini',
                'text': 'The goblin falls! [STATE_UPDATES_PROPOSED]xp: +50[END_STATE_UPDATES_PROPOSED]',
                'timestamp': '2024-01-01T10:00:02'
            }
        ]
        
        # Mock story with new-style clean text
        self.new_style_story = [
            {
                'actor': 'user',
                'text': 'I cast fireball!',
                'timestamp': '2024-01-01T11:00:00'
            },
            {
                'actor': 'gemini',
                'text': 'The fireball explodes in the room!',
                'timestamp': '2024-01-01T11:00:01',
                'debug_info': {
                    'dm_notes': ['Damage: 8d6 = 28'],
                    'dice_rolls': ['8d6: 28 fire damage']
                }
            }
        ]
        
    @patch('main.firestore_service.get_campaign_by_id')
    @patch('main.firestore_service.get_campaign_game_state')
    def test_old_campaign_debug_off(self, mock_get_state, mock_get_campaign):
        """Test old campaign with debug mode off strips debug content."""
        from main import app
        
        # Mock returns
        mock_get_campaign.return_value = (self.campaign, self.old_style_story)
        mock_get_state.return_value = GameState(debug_mode=False)
        
        with app.test_client() as client:
            # Mock authentication
            with patch('main.check_token', lambda f: f):
                response = client.get('/api/campaigns/test123', 
                                    headers={'Authorization': 'Bearer fake'})
                
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Check that debug content was stripped
        story = data['story']
        assert len(story) == 3
        assert '[DEBUG_START]' not in story[1]['text']
        assert 'You hit the goblin!' in story[1]['text']
        assert '[STATE_UPDATES_PROPOSED]' not in story[2]['text']
        
    @patch('main.firestore_service.get_campaign_by_id')
    @patch('main.firestore_service.get_campaign_game_state')
    def test_old_campaign_debug_on(self, mock_get_state, mock_get_campaign):
        """Test old campaign with debug mode on preserves debug content."""
        from main import app
        
        # Mock returns
        mock_get_campaign.return_value = (self.campaign, self.old_style_story)
        mock_get_state.return_value = GameState(debug_mode=True)
        
        with app.test_client() as client:
            # Mock authentication
            with patch('main.check_token', lambda f: f):
                response = client.get('/api/campaigns/test123',
                                    headers={'Authorization': 'Bearer fake'})
                
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Check that debug content was preserved (except STATE_UPDATES)
        story = data['story']
        assert '[DEBUG_START]Attack roll: 15[DEBUG_END]' in story[1]['text']
        assert '[STATE_UPDATES_PROPOSED]' not in story[2]['text']  # Always stripped
        
    @patch('main.firestore_service.get_campaign_by_id')
    @patch('main.firestore_service.get_campaign_game_state')
    def test_new_campaign_unchanged(self, mock_get_state, mock_get_campaign):
        """Test new campaign with clean text remains unchanged."""
        from main import app
        
        # Mock returns
        mock_get_campaign.return_value = (self.campaign, self.new_style_story)
        mock_get_state.return_value = GameState(debug_mode=False)
        
        with app.test_client() as client:
            # Mock authentication
            with patch('main.check_token', lambda f: f):
                response = client.get('/api/campaigns/test123',
                                    headers={'Authorization': 'Bearer fake'})
                
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Check that new style story is unchanged
        story = data['story']
        assert story[1]['text'] == 'The fireball explodes in the room!'
        # Debug info would be in separate field (not implemented yet)