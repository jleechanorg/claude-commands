"""
Test debug mode integration with GameState class.
"""
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from game_state import GameState


class TestDebugModeGameState(unittest.TestCase):
    """Test debug mode functionality in GameState."""
    
    def test_debug_mode_default_true(self):
        """Test that debug_mode defaults to True."""
        game_state = GameState()
        self.assertTrue(game_state.debug_mode)
    
    def test_debug_mode_initialization(self):
        """Test that debug_mode can be set during initialization."""
        # Test with True
        game_state_true = GameState(debug_mode=True)
        self.assertTrue(game_state_true.debug_mode)
        
        # Test with False
        game_state_false = GameState(debug_mode=False)
        self.assertFalse(game_state_false.debug_mode)
    
    def test_debug_mode_in_to_dict(self):
        """Test that debug_mode is included in to_dict()."""
        # Default case
        game_state = GameState()
        state_dict = game_state.to_dict()
        self.assertIn('debug_mode', state_dict)
        self.assertTrue(state_dict['debug_mode'])
        
        # When set to True
        game_state.debug_mode = True
        state_dict = game_state.to_dict()
        self.assertIn('debug_mode', state_dict)
        self.assertTrue(state_dict['debug_mode'])
    
    def test_debug_mode_from_dict(self):
        """Test that debug_mode is restored from dict."""
        # Test with debug_mode True
        source_dict = {
            'debug_mode': True,
            'player_character_data': {'name': 'Test Hero'}
        }
        game_state = GameState.from_dict(source_dict)
        self.assertTrue(game_state.debug_mode)
        
        # Test with debug_mode False
        source_dict['debug_mode'] = False
        game_state = GameState.from_dict(source_dict)
        self.assertFalse(game_state.debug_mode)
        
        # Test without debug_mode (should default to True)
        del source_dict['debug_mode']
        game_state = GameState.from_dict(source_dict)
        self.assertTrue(game_state.debug_mode)
    
    def test_debug_mode_attribute_access(self):
        """Test that debug_mode can be accessed and modified as attribute."""
        game_state = GameState()
        
        # Should start as True
        self.assertTrue(game_state.debug_mode)
        
        # Set to True
        game_state.debug_mode = True
        self.assertTrue(game_state.debug_mode)
        
        # Set back to False
        game_state.debug_mode = False
        self.assertFalse(game_state.debug_mode)
    
    def test_debug_mode_persists_through_serialization(self):
        """Test that debug_mode persists through to_dict/from_dict cycle."""
        # Create state with debug mode on
        original_state = GameState(
            debug_mode=True,
            player_character_data={'name': 'Test', 'hp_current': 10}
        )
        
        # Serialize to dict
        state_dict = original_state.to_dict()
        
        # Recreate from dict
        restored_state = GameState.from_dict(state_dict)
        
        # Verify debug mode is preserved
        self.assertTrue(restored_state.debug_mode)
        self.assertEqual(restored_state.player_character_data['name'], 'Test')


if __name__ == '__main__':
    unittest.main()