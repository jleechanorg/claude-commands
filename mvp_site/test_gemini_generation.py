"""
Unit tests for gemini_service.py generation logic.

This module tests the story generation functionality,
including edge cases, validation, and error recovery.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set dummy API key before importing gemini_service
os.environ["GEMINI_API_KEY"] = "DUMMY_KEY_FOR_TESTING"

import gemini_service
from game_state import GameState
import constants


class TestGeminiGenerationLogic(unittest.TestCase):
    """Tests for story generation logic in gemini_service.py"""
    
    def setUp(self):
        """Set up test environment before each test"""
        gemini_service._clear_client()
        # Clear any cached instructions
        gemini_service._loaded_instructions_cache.clear()
        
    def tearDown(self):
        """Clean up after each test"""
        gemini_service._clear_client()
    
    @patch('gemini_service.genai.Client')
    def test_initial_story_generation_success(self, mock_client_class):
        """Test successful initial story generation"""
        # Create mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Create mock response
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "narrative": "Welcome to the Crystal Cavern adventure!",
            "entities_mentioned": ["Crystal Cavern", "party"],
            "mechanics": "",
            "next_scene": "The party enters a mysterious cave"
        })
        mock_client.models.generate_content.return_value = mock_response
        
        # Test initial story generation
        result = gemini_service.get_initial_story("Start a cave adventure")
        
        # Verify result is GeminiResponse object
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, 'narrative_text'))
        self.assertIn("Welcome to the Crystal Cavern", result.narrative_text)
    
    @patch('gemini_service.genai.Client')
    def test_empty_prompt_handling(self, mock_client_class):
        """Test handling of empty prompts"""
        # Create mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Create mock response for empty prompt
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "narrative": "Please provide more details about your adventure.",
            "entities_mentioned": [],
            "mechanics": ""
        })
        mock_client.models.generate_content.return_value = mock_response
        
        # Test with empty prompt
        result = gemini_service.get_initial_story("")
        
        # Should still generate something
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, 'narrative_text'))
        self.assertGreater(len(result.narrative_text), 0)
    
    @patch('gemini_service.genai.Client')
    def test_unicode_emoji_in_generation(self, mock_client_class):
        """Test generation with unicode and emoji content"""
        # Create mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Create response with unicode/emoji
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "narrative": "The wizard Élara 🧙‍♀️ casts a spell ✨",
            "entities_mentioned": ["Élara", "wizard"],
            "mechanics": "Spell: Λήθη (Lethe) - Forget spell"
        })
        mock_client.models.generate_content.return_value = mock_response
        
        # Test generation
        result = gemini_service.get_initial_story("Create wizard character")
        
        # Verify unicode/emoji preserved
        self.assertIn("🧙‍♀️", result.narrative_text)
        self.assertIn("✨", result.narrative_text)
        self.assertIn("Élara", result.narrative_text)
    
    @patch('gemini_service.genai.Client')
    def test_very_long_prompt_handling(self, mock_client_class):
        """Test handling of very long prompts"""
        # Create mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Create response
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "narrative": "Processing your detailed request...",
            "entities_mentioned": ["party"],
            "mechanics": ""
        })
        mock_client.models.generate_content.return_value = mock_response
        
        # Create very long prompt (but within limits)
        long_prompt = "Create an adventure with " + " many details " * 1000
        
        # Should handle without error
        result = gemini_service.get_initial_story(long_prompt)
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, 'narrative_text'))
    
    @patch('gemini_service.genai.Client')
    def test_continue_story_with_game_state(self, mock_client_class):
        """Test continuing story with existing game state"""
        # Create mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Create mock response
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "narrative": "The party moves deeper into the cave.",
            "entities_mentioned": ["party", "cave"],
            "mechanics": "Perception check: DC 15"
        })
        mock_client.models.generate_content.return_value = mock_response
        
        # Create game state
        game_state = GameState()
        game_state.campaign_id = "test_campaign"
        game_state.current_scene = "Cave entrance"
        
        # Create story context
        story_context = [
            {"actor": "user", "text": "I want to enter the cave"},
            {"actor": "gemini", "text": "The party enters the cave"}
        ]
        
        # Test continue story
        result = gemini_service.continue_story(
            "Move deeper", 
            constants.MODE_CHARACTER,
            story_context,
            game_state
        )
        
        # Verify result - continue_story returns GeminiResponse object
        self.assertIn("deeper into the cave", result.narrative_text)
    
    @patch('gemini_service.genai.Client')
    def test_special_characters_in_generation(self, mock_client_class):
        """Test handling of special characters in generation"""
        # Create mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Response with special characters
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "narrative": "The rogue says: \"I'll pick the lock!\" *click*",
            "entities_mentioned": ["rogue"],
            "mechanics": "Lockpicking: 1d20+5 >= 15"
        })
        mock_client.models.generate_content.return_value = mock_response
        
        # Test generation
        result = gemini_service.get_initial_story("Rogue picks lock")
        
        # Verify special characters preserved
        self.assertIn('"', result.narrative_text)
        self.assertIn('*click*', result.narrative_text)
    
    @patch('gemini_service.genai.Client')
    def test_malformed_response_recovery(self, mock_client_class):
        """Test recovery from malformed JSON responses"""
        # Create mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # First response is malformed, second is valid
        mock_response_bad = MagicMock()
        mock_response_bad.text = "This is not valid JSON{"
        
        mock_response_good = MagicMock()
        mock_response_good.text = json.dumps({
            "narrative": "Adventure begins!",
            "entities_mentioned": ["party"],
            "mechanics": ""
        })
        
        # First call returns malformed, second returns good
        mock_client.models.generate_content.side_effect = [
            mock_response_bad,
            mock_response_good
        ]
        
        # Should recover and return valid response
        result = gemini_service.get_initial_story("Start adventure")
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, 'narrative_text'))
    
    @patch('gemini_service.genai.Client')
    def test_empty_response_handling(self, mock_client_class):
        """Test handling of empty responses"""
        # Create mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock empty response
        mock_response = MagicMock()
        mock_response.text = ""
        mock_client.models.generate_content.return_value = mock_response
        
        # Should handle gracefully
        result = gemini_service.get_initial_story("Test prompt")
        # Should return a response object even for empty responses
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, 'narrative_text'))
    
    @patch('gemini_service.genai.Client')
    def test_multiline_narrative_generation(self, mock_client_class):
        """Test generation with multiline narratives"""
        # Create mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Response with multiline content
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "narrative": """The ancient door creaks open.

Inside, you see:
- Glowing crystals
- A mysterious altar
- Strange symbols

The air feels heavy with magic.""",
            "entities_mentioned": ["door", "crystals", "altar", "symbols"],
            "mechanics": ""
        })
        mock_client.models.generate_content.return_value = mock_response
        
        # Test generation
        result = gemini_service.get_initial_story("Open the door")
        
        # Verify multiline preserved
        self.assertIn("\n", result.narrative_text)
        self.assertIn("- Glowing crystals", result.narrative_text)
    
    @patch('gemini_service.genai.Client')
    def test_dice_notation_in_mechanics(self, mock_client_class):
        """Test dice notation in mechanics responses"""
        # Create mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Response with dice notation
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "narrative": "The wizard casts fireball!",
            "entities_mentioned": ["wizard"],
            "mechanics": "Damage: 8d6 fire damage, DC 15 Dex save for half"
        })
        mock_client.models.generate_content.return_value = mock_response
        
        # Test generation - continue_story returns string not GeminiResponse
        result = gemini_service.continue_story(
            "Cast fireball",
            constants.MODE_GOD,
            [{"actor": "user", "text": "Combat started"}],
            GameState()
        )
        
        # Verify dice notation - continue_story returns GeminiResponse object
        self.assertIn("8d6", result.narrative_text)
        self.assertIn("DC 15", result.narrative_text)
    
    @patch('gemini_service.genai.Client')
    def test_companion_generation(self, mock_client_class):
        """Test companion character generation"""
        # Create mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Response with companion info
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "narrative": "Your companion, Elena the ranger, joins the party.",
            "entities_mentioned": ["Elena", "ranger", "party"],
            "mechanics": "Elena: Level 3 Ranger, HP 28, AC 15"
        })
        mock_client.models.generate_content.return_value = mock_response
        
        # Test with companion generation
        result = gemini_service.get_initial_story(
            "Start with companion",
            generate_companions=True
        )
        
        # Verify companion mentioned
        self.assertIn("Elena", result.narrative_text)
        self.assertIn("ranger", result.narrative_text.lower())

    def test_campaign_world_building(self):
        """Test campaign world building generation."""
        mock_client = MagicMock()
        gemini_service._client = mock_client
        
        # Mock response for world building
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "narrative": "The kingdom of Eldoria faces a dire threat from the Shadow Legion.",
            "entities_mentioned": ["Eldoria", "Shadow Legion", "kingdom"],
            "mechanics": "Setting: High Fantasy, Political tensions"
        })
        mock_client.models.generate_content.return_value = mock_response
        
        # Test world building prompt
        result = gemini_service.generate_story_continuation(
            "Describe the political landscape",
            {"setting": "fantasy", "world": "Eldoria"}
        )
        
        # Verify world building elements
        self.assertIn("Eldoria", result.narrative_text)
        self.assertIn("kingdom", result.narrative_text.lower())

    def test_narrative_consistency(self):
        """Test narrative consistency across multiple generations."""
        mock_client = MagicMock()
        gemini_service._client = mock_client
        
        # Mock consistent responses
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "narrative": "The adventurer recalls their promise to Elena.",
            "entities_mentioned": ["Elena", "promise", "adventurer"],
            "mechanics": "Consistency check: Elena mentioned from previous context"
        })
        mock_client.models.generate_content.return_value = mock_response
        
        # Test with context from previous story
        game_state = {
            "npcs": [{"name": "Elena", "role": "ranger"}],
            "history": ["Met Elena in the forest"]
        }
        
        result = gemini_service.generate_story_continuation(
            "What promise was made?",
            game_state
        )
        
        # Verify narrative consistency
        self.assertIn("Elena", result.narrative_text)
        self.assertIn("promise", result.narrative_text.lower())


if __name__ == '__main__':
    unittest.main()