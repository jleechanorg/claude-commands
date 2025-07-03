import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Firebase mocks before importing
from tests.fixtures.firebase_fixtures import setup_firebase_mocks
setup_firebase_mocks()

from gemini_service import PromptBuilder
from game_state import GameState


class TestPromptBuilder(unittest.TestCase):
    """Test the PromptBuilder class methods."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.game_state = GameState({
            'campaign_id': 'test_campaign',
            'timestamp': datetime.now().isoformat(),
            'game_state': {
                'locations': {
                    'current_location': 'Test Town'
                },
                'narrative': {
                    'current_scene': 'A bustling marketplace'
                }
            }
        })
        self.builder = PromptBuilder(self.game_state)
    
    def test_build_companion_instruction_with_companions(self):
        """Test building companion instructions when companions exist."""
        # Add companions to game state
        self.game_state.data['game_state']['companions'] = {
            'Gandalf': {'class': 'Wizard', 'status': 'active'},
            'Aragorn': {'class': 'Ranger', 'status': 'active'}
        }
        
        result = self.builder.build_companion_instruction()
        
        self.assertIn('ACTIVE COMPANIONS', result)
        self.assertIn('Gandalf', result)
        self.assertIn('Aragorn', result)
        self.assertIn('Wizard', result)
        self.assertIn('Ranger', result)
    
    def test_build_companion_instruction_without_companions(self):
        """Test building companion instructions when no companions exist."""
        # Ensure no companions
        self.game_state.data['game_state']['companions'] = {}
        
        result = self.builder.build_companion_instruction()
        
        self.assertEqual(result, '')
    
    def test_build_companion_instruction_with_none_companions(self):
        """Test building companion instructions when companions is None."""
        # Set companions to None
        self.game_state.data['game_state']['companions'] = None
        
        result = self.builder.build_companion_instruction()
        
        self.assertEqual(result, '')
    
    def test_build_background_summary_instruction_with_summary(self):
        """Test building background summary when story summary exists."""
        # Add story summary
        self.game_state.data['game_state']['story'] = {
            'summary': 'An epic tale of adventure and magic'
        }
        
        result = self.builder.build_background_summary_instruction()
        
        self.assertIn('STORY SUMMARY', result)
        self.assertIn('An epic tale of adventure and magic', result)
    
    def test_build_background_summary_instruction_without_summary(self):
        """Test building background summary when no summary exists."""
        # Ensure no story summary
        self.game_state.data['game_state']['story'] = {}
        
        result = self.builder.build_background_summary_instruction()
        
        self.assertEqual(result, '')
    
    def test_build_background_summary_instruction_with_none_story(self):
        """Test building background summary when story is None."""
        # Set story to None
        self.game_state.data['game_state']['story'] = None
        
        result = self.builder.build_background_summary_instruction()
        
        self.assertEqual(result, '')
    
    def test_finalize_instructions_combines_all_parts(self):
        """Test that finalize_instructions properly combines all instruction parts."""
        # Mock the individual builder methods
        self.builder.build_core_system_instructions = Mock(return_value='Core instructions\n')
        self.builder.add_character_instructions = Mock(return_value='Character instructions\n')
        self.builder.add_selected_prompt_instructions = Mock(return_value='Prompt instructions\n')
        self.builder.add_system_reference_instructions = Mock(return_value='Reference instructions\n')
        self.builder.build_companion_instruction = Mock(return_value='Companion instructions\n')
        self.builder.build_background_summary_instruction = Mock(return_value='Background instructions\n')
        
        # Mock parameters
        character_name = 'Test Character'
        campaign_instructions = 'Campaign rules'
        selected_prompt = {'instruction': 'Do something'}
        system_reference = 'System ref'
        
        result = self.builder.finalize_instructions(
            character_name=character_name,
            campaign_instructions=campaign_instructions,
            selected_prompt=selected_prompt,
            system_reference=system_reference
        )
        
        # Verify all methods were called
        self.builder.build_core_system_instructions.assert_called_once()
        self.builder.add_character_instructions.assert_called_once_with(character_name, campaign_instructions)
        self.builder.add_selected_prompt_instructions.assert_called_once_with(selected_prompt)
        self.builder.add_system_reference_instructions.assert_called_once_with(system_reference)
        self.builder.build_companion_instruction.assert_called_once()
        self.builder.build_background_summary_instruction.assert_called_once()
        
        # Verify result contains all parts
        self.assertIn('Core instructions', result)
        self.assertIn('Character instructions', result)
        self.assertIn('Prompt instructions', result)
        self.assertIn('Reference instructions', result)
        self.assertIn('Companion instructions', result)
        self.assertIn('Background instructions', result)
    
    def test_finalize_instructions_strips_whitespace(self):
        """Test that finalize_instructions strips extra whitespace."""
        # Mock methods to return strings with extra whitespace
        self.builder.build_core_system_instructions = Mock(return_value='  Core  \n\n')
        self.builder.add_character_instructions = Mock(return_value='  Character  \n\n')
        self.builder.add_selected_prompt_instructions = Mock(return_value='')
        self.builder.add_system_reference_instructions = Mock(return_value='')
        self.builder.build_companion_instruction = Mock(return_value='')
        self.builder.build_background_summary_instruction = Mock(return_value='')
        
        result = self.builder.finalize_instructions('char', 'campaign', {}, '')
        
        # Should have single newline between sections, no trailing whitespace
        self.assertEqual(result, 'Core\n\nCharacter')
    
    def test_prompt_builder_with_complex_companions(self):
        """Test PromptBuilder with complex companion data structures."""
        # Add complex companion data
        self.game_state.data['game_state']['companions'] = {
            'Gandalf': {
                'class': 'Wizard',
                'status': 'active',
                'level': 20,
                'health': {'current': 100, 'max': 100}
            },
            'Injured Knight': {
                'class': 'Fighter',
                'status': 'injured',
                'health': {'current': 10, 'max': 50}
            }
        }
        
        result = self.builder.build_companion_instruction()
        
        # Should include active companions
        self.assertIn('Gandalf', result)
        self.assertIn('Wizard', result)
        # Could include injured companion depending on implementation
        # Main point is it shouldn't crash with complex data
    
    def test_prompt_builder_with_malformed_companions(self):
        """Test PromptBuilder handles malformed companion data gracefully."""
        # Add malformed companion data
        self.game_state.data['game_state']['companions'] = {
            'BadCompanion': 'not a dict',  # Wrong type
            'GoodCompanion': {'class': 'Fighter', 'status': 'active'}
        }
        
        # Should not raise an exception
        result = self.builder.build_companion_instruction()
        
        # Should still include good companion
        self.assertIn('GoodCompanion', result)
    
    def test_background_summary_with_long_text(self):
        """Test background summary handles very long summaries."""
        # Add very long summary
        long_summary = 'A' * 10000  # 10k characters
        self.game_state.data['game_state']['story'] = {
            'summary': long_summary
        }
        
        result = self.builder.build_background_summary_instruction()
        
        # Should include the summary (may be truncated in real implementation)
        self.assertIn('STORY SUMMARY', result)
        self.assertIn('A' * 100, result)  # At least first 100 chars
    
    def test_prompt_builder_initialization(self):
        """Test PromptBuilder initializes correctly with game state."""
        builder = PromptBuilder(self.game_state)
        
        # Should store game state reference
        self.assertEqual(builder.game_state, self.game_state)
    
    def test_empty_instruction_methods_return_empty_strings(self):
        """Test that instruction methods return empty strings for missing data."""
        # Create minimal game state
        minimal_state = GameState({
            'campaign_id': 'test',
            'timestamp': datetime.now().isoformat(),
            'game_state': {}
        })
        builder = PromptBuilder(minimal_state)
        
        # All these should return empty strings
        self.assertEqual(builder.build_companion_instruction(), '')
        self.assertEqual(builder.build_background_summary_instruction(), '')


if __name__ == '__main__':
    unittest.main()