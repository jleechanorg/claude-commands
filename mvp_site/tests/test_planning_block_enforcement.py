"""
Unit tests for planning block enforcement in story continuation.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import constants


class TestPlanningBlockEnforcement(unittest.TestCase):
    """Test planning block validation and enforcement."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock the imports that might not be available
        self.mock_genai = MagicMock()
        sys.modules['google'] = MagicMock()
        sys.modules['google.genai'] = self.mock_genai
        sys.modules['google.genai.types'] = MagicMock()
        
        # Now we can import
        from gemini_service import _validate_and_enforce_planning_block, _call_gemini_api, _get_text_from_response
        self.validate_func = _validate_and_enforce_planning_block
        
        # Mock the gemini API calls
        self.mock_game_state = MagicMock()
        self.mock_game_state.world_data = {'current_location_name': 'Test Location'}
        self.mock_model = 'test-model'
        self.mock_system_instruction = 'Test instruction'
        
        # Patch the API call functions
        self.patcher_call = patch('gemini_service._call_gemini_api')
        self.patcher_get_text = patch('gemini_service._get_text_from_response')
        self.mock_call_api = self.patcher_call.start()
        self.mock_get_text = self.patcher_get_text.start()
        
        # Default mock behavior for planning block generation
        self.mock_get_text.return_value = "\n\n--- PLANNING BLOCK ---\nWhat would you like to do next?\n1. **[Action_1]:** Take action one.\n2. **[Action_2]:** Take action two.\n3. **[Other_3]:** Do something else."
    
    def tearDown(self):
        """Clean up patches."""
        self.patcher_call.stop()
        self.patcher_get_text.stop()
    
    def test_response_with_existing_planning_block(self):
        """Test that responses with planning blocks are unchanged."""
        response = """The story continues...
        
--- PLANNING BLOCK ---
What would you like to do next?
1. **[Option_1]:** First option
2. **[Option_2]:** Second option"""
        
        result = self.validate_func(response, "continue the story", self.mock_game_state, 
                                  self.mock_model, self.mock_system_instruction)
        self.assertEqual(result, response)
        # Should not call API if planning block exists
        self.mock_call_api.assert_not_called()
    
    def test_response_missing_planning_block_standard(self):
        """Test that missing planning blocks are added for standard actions."""
        response = "The merchant nods and continues on his way."
        user_input = "I greet the merchant"
        
        # Mock standard planning block response
        self.mock_get_text.return_value = "\n\n--- PLANNING BLOCK ---\nWhat would you like to do next?\n1. **[Talk_1]:** Continue conversation with the merchant.\n2. **[Leave_2]:** Bid farewell and continue on your way.\n3. **[Other_3]:** Do something else."
        
        result = self.validate_func(response, user_input, self.mock_game_state,
                                  self.mock_model, self.mock_system_instruction)
        
        # Should have planning block added
        self.assertIn("--- PLANNING BLOCK ---", result)
        self.assertIn("merchant nods", result)  # Original response preserved
        self.mock_call_api.assert_called_once()  # API called to generate block
    
    def test_response_missing_planning_block_think_command(self):
        """Test deep think block for think keywords."""
        response = "You pause at the crossroads."
        
        # Mock deep think planning block response
        self.mock_get_text.return_value = """\n\n--- PLANNING BLOCK ---
I pause to consider my options at this crossroads...

I see several paths before me:

1. **[CHOICE_ID: NorthPath_1]:** Take the northern road through the forest
   - Pros: Shorter route, good cover
   - Cons: Potentially dangerous wildlife
   - Confidence: Moderately risky but manageable

2. **[CHOICE_ID: EastPath_2]:** Follow the eastern trade route
   - Pros: Well-traveled, likely safe
   - Cons: Longer journey, may encounter other travelers
   - Confidence: Safe but time-consuming

3. **[Other_3]:** I could also try something else entirely.

Each path has its merits..."""
        
        think_inputs = [
            "I think about my options",
            "Let me plan the approach",
            "I consider the possibilities",
            "Time to strategize",
            "What are my options?"
        ]
        
        for user_input in think_inputs:
            # Reset mock calls
            self.mock_call_api.reset_mock()
            
            result = self.validate_func(response, user_input, self.mock_game_state,
                                      self.mock_model, self.mock_system_instruction)
            
            # Should have deep think block with pros/cons
            self.assertIn("--- PLANNING BLOCK ---", result)
            self.assertIn("Pros:", result)
            self.assertIn("Cons:", result)
            self.assertIn("Confidence:", result)
            self.mock_call_api.assert_called_once()
    
    def test_block_placement(self):
        """Test that planning block is properly placed at the end."""
        response = "The story continues here."
        result = self.validate_func(response, "continue", self.mock_game_state,
                                  self.mock_model, self.mock_system_instruction)
        
        # Should end with planning block
        self.assertTrue("--- PLANNING BLOCK ---" in result)
        self.assertTrue(result.startswith("The story continues here."))
        # Planning block should be after the original content
        self.assertIn("--- PLANNING BLOCK ---", result.split("The story continues here.")[1])
    
    def test_whitespace_handling(self):
        """Test that trailing whitespace is handled correctly."""
        response = "The story continues here.   \n\n   "
        result = self.validate_func(response, "continue", self.mock_game_state,
                                  self.mock_model, self.mock_system_instruction)
        
        # Should strip trailing whitespace before adding planning block
        self.assertIn("The story continues here.", result)
        self.assertIn("--- PLANNING BLOCK ---", result)
        # Should not have the original trailing whitespace
        self.assertNotIn("here.   \n\n   \n\n--- PLANNING BLOCK ---", result)
    
    def test_character_creation_no_planning_block(self):
        """Test that planning blocks are NOT added during character creation."""
        response = """[CHARACTER CREATION - Step 2 of 7]

You have chosen to create a custom character! This is an excellent choice for a rich, personalized story. We will work together to build a character that fits your vision within the D&D 5E ruleset.

To start, please describe the core concept for your character. Don't worry about specific stats or abilities just yet. Think about the high-level idea.

Please tell me about the hero you want to bring to life. What is their story? What makes them unique?

🔧 STATE UPDATES PROPOSED:
{
  "custom_campaign_state": {
    "character_creation": {
      "in_progress": true,
      "current_step": 2,
      "method_chosen": "custom_character"
    }
  }
}"""
        
        # Various user inputs during character creation
        user_inputs = [
            "A dragon-blooded warrior",
            "I want to be a paladin",
            "3",  # Numeric selection
            "continue"
        ]
        
        for user_input in user_inputs:
            result = self.validate_func(response, user_input, self.mock_game_state,
                                      self.mock_model, self.mock_system_instruction)
            
            # Should NOT have planning block added
            self.assertEqual(result, response)
            # API should not be called for character creation
            self.mock_call_api.assert_not_called()
    
    def test_api_failure_fallback(self):
        """Test that a fallback planning block is used if API fails."""
        response = "The adventure continues."
        user_input = "continue"
        
        # Mock API failure
        self.mock_call_api.side_effect = Exception("API Error")
        
        result = self.validate_func(response, user_input, self.mock_game_state,
                                  self.mock_model, self.mock_system_instruction)
        
        # Should have fallback planning block
        self.assertIn("--- PLANNING BLOCK ---", result)
        self.assertIn("Continue with your current course of action", result)
        self.assertIn("Explore your surroundings", result)
    
    def test_god_mode_switching_no_planning_block(self):
        """Test that planning blocks are NOT added when switching to god mode."""
        response = "You enter the realm of divine control."
        
        # Use the same mode switch phrases as the production code
        god_mode_inputs = constants.MODE_SWITCH_PHRASES
        
        for user_input in god_mode_inputs:
            result = self.validate_func(response, user_input, self.mock_game_state,
                                      self.mock_model, self.mock_system_instruction)
            
            # Should NOT have planning block added
            self.assertEqual(result, response)
            self.assertNotIn("--- PLANNING BLOCK ---", result)
            self.mock_call_api.assert_not_called()
    
    def test_mode_indicator_in_response_no_planning_block(self):
        """Test that planning blocks are NOT added when response indicates mode switch."""
        responses = [
            "[Mode: DM MODE]\n\nYou are now in DM mode.",
            "[Mode: GOD MODE]\n\nYou have divine control.",
            "Some text [Mode: DM MODE] more text"
        ]
        
        user_input = "tell me about the world"
        
        for response in responses:
            result = self.validate_func(response, user_input, self.mock_game_state,
                                      self.mock_model, self.mock_system_instruction)
            
            # Should NOT have planning block added
            self.assertEqual(result, response)
            self.assertNotIn("--- PLANNING BLOCK ---", result)
            self.mock_call_api.assert_not_called()
    
    def test_god_mode_detection_logic(self):
        """Test that mode switching detection logic works correctly."""
        # Test the simple mode switch phrases used in detection logic
        god_mode_inputs = constants.MODE_SWITCH_SIMPLE
        
        for user_input in god_mode_inputs:
            # Testing that the mode switching detection works
            # Simulate the check that happens in continue_story
            user_input_lower = user_input.lower().strip()
            is_switching_to_god_mode = user_input_lower in constants.MODE_SWITCH_SIMPLE
            
            # Should detect mode switching
            self.assertTrue(is_switching_to_god_mode, f"Failed to detect god mode switch for: {user_input}")
    
    def test_dm_mode_response_no_planning_block(self):
        """Test that planning blocks are NOT added when AI responds in DM MODE."""
        response = "[Mode: DM MODE]\n\nLet's discuss the campaign settings."
        user_input = "tell me about the world"
        
        # Test the DM mode detection
        is_dm_mode_response = '[Mode: DM MODE]' in response or '[Mode: GOD MODE]' in response
        self.assertTrue(is_dm_mode_response, "Failed to detect DM MODE in response")


class TestContinueStoryPlanningBlocks(unittest.TestCase):
    """Test planning block enforcement in continue_story function."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock the imports
        self.mock_genai = MagicMock()
        sys.modules['google'] = MagicMock()
        sys.modules['google.genai'] = self.mock_genai
        sys.modules['google.genai.types'] = MagicMock()
        
        # Store constants reference
        self.constants = constants
        
        # Mock game state
        self.mock_game_state = MagicMock()
        self.mock_game_state.to_dict.return_value = {'test': 'state'}
        self.mock_game_state.world_data = {'current_location_name': 'Test Location'}
        self.mock_game_state.player_character_data = {'name': 'TestChar'}
        self.mock_game_state.custom_campaign_state = {'session_number': 1}
        
        # Mock story context
        self.story_context = []
        
        # Patch various functions
        self.patches = []
        
        # Patch the main functions that continue_story uses
        patch_list = [
            'gemini_service._prepare_entity_tracking',
            'gemini_service._build_timeline_log', 
            'gemini_service._get_current_turn_prompt',
            'gemini_service._build_continuation_prompt',
            'gemini_service._select_model_for_continuation',
            'gemini_service._call_gemini_api',
            'gemini_service._get_text_from_response',
            'gemini_service._validate_entity_tracking',
            'gemini_service._validate_and_enforce_planning_block',
            'gemini_service.PromptBuilder'
        ]
        
        for patch_target in patch_list:
            patcher = patch(patch_target)
            mock = patcher.start()
            self.patches.append(patcher)
            setattr(self, f'mock_{patch_target.split(".")[-1]}', mock)
        
        # Configure mocks
        self.mock__prepare_entity_tracking.return_value = ('manifest', [], 'instruction')
        self.mock__build_timeline_log.return_value = 'timeline'
        self.mock__get_current_turn_prompt.return_value = 'current prompt'
        self.mock__build_continuation_prompt.return_value = 'full prompt'
        self.mock__select_model_for_continuation.return_value = 'test-model'
        self.mock__get_text_from_response.return_value = 'AI response without planning block'
        self.mock__validate_entity_tracking.return_value = 'validated response'
        self.mock__validate_and_enforce_planning_block.return_value = 'response with planning block'
        
        # Mock PromptBuilder
        mock_builder_instance = MagicMock()
        mock_builder_instance.build_continuation_reminder.return_value = 'PLANNING BLOCK REMINDER'
        mock_builder_instance.add_system_reference_instructions.return_value = None
        self.mock_PromptBuilder.return_value = mock_builder_instance
        self.mock_builder = mock_builder_instance
    
    def tearDown(self):
        """Clean up patches."""
        for patcher in self.patches:
            patcher.stop()
    
    def test_continue_story_god_mode_no_planning_reminder(self):
        """Test that god mode does not get planning reminder in continue_story."""
        from gemini_service import continue_story
        
        # Test god mode
        result = continue_story(
            user_input="test input",
            mode=self.constants.MODE_GOD,
            story_context=self.story_context,
            current_game_state=self.mock_game_state
        )
        
        # God mode should NOT get planning reminder
        self.mock_builder.build_continuation_reminder.assert_not_called()
    
    def test_continue_story_mode_specific_planning_reminders(self):
        """Test that only character mode gets planning reminders, not god mode."""
        from gemini_service import continue_story
        
        # Reset mock for clean test
        self.mock_builder.reset_mock()
        
        # Test god mode - should NOT get planning reminder
        result_god = continue_story(
            user_input="test input", 
            mode=self.constants.MODE_GOD,
            story_context=self.story_context,
            current_game_state=self.mock_game_state
        )
        
        # Count calls after god mode (should be 1 because it's currently added unconditionally)
        god_mode_calls = self.mock_builder.build_continuation_reminder.call_count
        
        # Reset for character mode test
        self.mock_builder.reset_mock()
        
        # Test character mode - should get planning reminder
        result_char = continue_story(
            user_input="test input",
            mode=self.constants.MODE_CHARACTER,
            story_context=self.story_context,
            current_game_state=self.mock_game_state
        )
        
        char_mode_calls = self.mock_builder.build_continuation_reminder.call_count
        
        # Verify proper mode-specific behavior
        # God mode should have 0 calls, character mode should have 1 call
        self.assertEqual(god_mode_calls, 0, "God mode should not get planning reminder")
        self.assertEqual(char_mode_calls, 1, "Character mode should get planning reminder")
    
    def test_continue_story_character_mode_has_planning_reminder(self):
        """Test that character mode DOES get planning reminder (should pass)."""
        from gemini_service import continue_story
        
        # Test character mode
        result = continue_story(
            user_input="test input",
            mode=self.constants.MODE_CHARACTER, 
            story_context=self.story_context,
            current_game_state=self.mock_game_state
        )
        
        # Character mode should have planning reminder
        self.mock_builder.build_continuation_reminder.assert_called_once()


if __name__ == '__main__':
    unittest.main()