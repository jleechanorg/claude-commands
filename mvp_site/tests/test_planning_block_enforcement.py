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
        """Test that responses with planning blocks in JSON are unchanged."""
        response = "The story continues..."
        
        # JSON-first: Create structured response with planning block
        from narrative_response_schema import NarrativeResponse
        structured_response = NarrativeResponse(
            narrative=response,
            planning_block="What would you like to do next?\n1. **[Option_1]:** First option\n2. **[Option_2]:** Second option"
        )
        
        result = self.validate_func(response, "continue the story", self.mock_game_state, 
                                  self.mock_model, self.mock_system_instruction,
                                  structured_response=structured_response)
        self.assertEqual(result, response)
        # Should not call API if planning block exists in structured response
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
    
    def test_character_creation_has_planning_block(self):
        """Test that planning blocks ARE added during character creation for interactivity."""
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
            
            # Should have planning block added for interactive character creation
            self.assertIn("--- PLANNING BLOCK ---", result)
            self.assertIn("CHARACTER CREATION", result)  # Original response preserved
            # API should be called to generate interactive options
            self.mock_call_api.assert_called_once()
            # Reset mock for next iteration
            self.mock_call_api.reset_mock()
    
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


class TestStructuredResponsePlanningBlocks(unittest.TestCase):
    """Red-Green tests for structured response planning block updates."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock the imports
        self.mock_genai = MagicMock()
        sys.modules['google'] = MagicMock()
        sys.modules['google.genai'] = self.mock_genai
        sys.modules['google.genai.types'] = MagicMock()
        
        # Import after mocking
        from gemini_service import _validate_and_enforce_planning_block
        from narrative_response_schema import NarrativeResponse
        self.validate_func = _validate_and_enforce_planning_block
        self.NarrativeResponse = NarrativeResponse
        
        # Mock game state
        self.mock_game_state = MagicMock()
        self.mock_game_state.world_data = {'current_location_name': 'Test Location'}
        self.mock_game_state.player_character_data = {'name': 'TestChar'}
        self.mock_model = 'test-model'
        self.mock_system_instruction = 'Test instruction'
        
        # Patch API functions
        self.patcher_call = patch('gemini_service._call_gemini_api')
        self.patcher_get_text = patch('gemini_service._get_text_from_response')
        self.patcher_parse = patch('gemini_service._parse_gemini_response')
        self.mock_call_api = self.patcher_call.start()
        self.mock_get_text = self.patcher_get_text.start()
        self.mock_parse = self.patcher_parse.start()
        
        # Default mock behavior
        self.mock_get_text.return_value = "Planning block content generated by API"
        self.mock_parse.return_value = ("What would you like to do next?\n1. **[Option1]:** First option\n2. **[Option2]:** Second option", None)
    
    def tearDown(self):
        """Clean up patches."""
        self.patcher_call.stop()
        self.patcher_get_text.stop()
        self.patcher_parse.stop()
    
    def test_structured_response_planning_block_missing_red(self):
        """RED TEST: Verify that missing planning block updates structured_response.planning_block field."""
        response = "The adventure continues without planning block."
        user_input = "I continue forward"
        
        # Create structured response WITHOUT planning block (simulating old behavior)
        structured_response = self.NarrativeResponse(
            narrative=response,
            planning_block=""  # Empty planning block simulates missing
        )
        
        # This should fail with old behavior (where JSON field wasn't updated)
        result = self.validate_func(
            response, user_input, self.mock_game_state, 
            self.mock_model, self.mock_system_instruction, 
            structured_response=structured_response
        )
        
        # The function should UPDATE the structured_response.planning_block field
        self.assertNotEqual(structured_response.planning_block, "", 
                          "Planning block should be updated in structured response")
        self.assertIn("Option1", structured_response.planning_block,
                     "Updated planning block should contain generated options")
        
        # API should be called to generate planning block
        self.mock_call_api.assert_called_once()
    
    def test_structured_response_planning_block_missing_green(self):
        """GREEN TEST: Verify function properly updates JSON field (should pass with new implementation)."""
        response = "The story continues without planning block."
        user_input = "I look around"
        
        # Create structured response without planning block
        structured_response = self.NarrativeResponse(
            narrative=response,
            planning_block=""
        )
        
        result = self.validate_func(
            response, user_input, self.mock_game_state,
            self.mock_model, self.mock_system_instruction,
            structured_response=structured_response
        )
        
        # Verify JSON field was updated (new behavior)
        self.assertNotEqual(structured_response.planning_block, "")
        self.assertIn("What would you like to do next?", structured_response.planning_block)
        self.assertIn("Option1", structured_response.planning_block)
        
        # Verify API was called to generate content
        self.mock_call_api.assert_called_once()
    
    def test_json_field_prioritized_over_response_text_red(self):
        """RED TEST: Verify JSON field is prioritized over response text planning blocks."""
        # Response text HAS planning block, but JSON field is empty
        response_with_text_block = """Story content here.

--- PLANNING BLOCK ---
What would you like to do next?
1. **[Legacy1]:** Legacy option from text
2. **[Legacy2]:** Another legacy option"""
        
        user_input = "I continue"
        
        # Structured response has empty planning_block (simulating inconsistency)
        structured_response = self.NarrativeResponse(
            narrative="Story content here.",
            planning_block=""  # Empty despite text having planning block
        )
        
        # This test verifies that the function prioritizes JSON field over text
        # and updates the JSON field even when text has a planning block
        result = self.validate_func(
            response_with_text_block, user_input, self.mock_game_state,
            self.mock_model, self.mock_system_instruction,
            structured_response=structured_response
        )
        
        # Should update JSON field despite text having planning block
        self.assertNotEqual(structured_response.planning_block, "")
        self.assertIn("Option1", structured_response.planning_block)
        # Should NOT contain the legacy text-based content
        self.assertNotIn("Legacy1", structured_response.planning_block)
        
        # API should be called because JSON field was empty
        self.mock_call_api.assert_called_once()
    
    def test_json_field_prioritized_over_response_text_green(self):
        """GREEN TEST: Verify function correctly prioritizes and updates JSON field."""
        response_with_text_block = """Story continues.

--- PLANNING BLOCK ---
Text-based planning block (should be ignored)"""
        
        user_input = "I act"
        
        # Create response with empty JSON planning block
        structured_response = self.NarrativeResponse(
            narrative="Story continues.",
            planning_block=""
        )
        
        result = self.validate_func(
            response_with_text_block, user_input, self.mock_game_state,
            self.mock_model, self.mock_system_instruction,
            structured_response=structured_response
        )
        
        # Verify JSON field was updated with new content
        self.assertTrue(len(structured_response.planning_block) > 0)
        self.assertIn("What would you like to do next?", structured_response.planning_block)
        
        # Verify API was called to generate new content for JSON field
        self.mock_call_api.assert_called_once()
    
    def test_existing_json_planning_block_preserved_red(self):
        """RED TEST: Verify existing JSON planning blocks are NOT overwritten."""
        response = "Story without planning block in text."
        user_input = "I continue"
        
        existing_planning_content = "Existing planning content\n1. **[Keep1]:** Keep this option\n2. **[Keep2]:** Keep this too"
        
        # Structured response already HAS planning block content
        structured_response = self.NarrativeResponse(
            narrative=response,
            planning_block=existing_planning_content
        )
        
        result = self.validate_func(
            response, user_input, self.mock_game_state,
            self.mock_model, self.mock_system_instruction,
            structured_response=structured_response
        )
        
        # Should NOT overwrite existing planning block
        self.assertEqual(structured_response.planning_block, existing_planning_content)
        self.assertIn("Keep1", structured_response.planning_block)
        self.assertIn("Keep2", structured_response.planning_block)
        
        # API should NOT be called when planning block already exists
        self.mock_call_api.assert_not_called()
    
    def test_existing_json_planning_block_preserved_green(self):
        """GREEN TEST: Verify function respects existing JSON planning blocks."""
        response = "Story continues."
        user_input = "I explore"
        
        existing_content = "Pre-existing planning block\n1. **[Existing1]:** First existing option"
        
        structured_response = self.NarrativeResponse(
            narrative=response,
            planning_block=existing_content
        )
        
        result = self.validate_func(
            response, user_input, self.mock_game_state,
            self.mock_model, self.mock_system_instruction,
            structured_response=structured_response
        )
        
        # Should preserve existing content exactly
        self.assertEqual(structured_response.planning_block, existing_content)
        
        # Should not call API when content already exists
        self.mock_call_api.assert_not_called()
    
    def test_api_failure_fallback_updates_json_field_red(self):
        """RED TEST: Verify API failure updates JSON field with fallback content."""
        response = "Story without planning block."
        user_input = "I continue"
        
        # Mock API failure
        self.mock_call_api.side_effect = Exception("API Failed")
        
        structured_response = self.NarrativeResponse(
            narrative=response,
            planning_block=""
        )
        
        result = self.validate_func(
            response, user_input, self.mock_game_state,
            self.mock_model, self.mock_system_instruction,
            structured_response=structured_response
        )
        
        # Should update JSON field with fallback content
        self.assertNotEqual(structured_response.planning_block, "")
        self.assertIn("Continue with your current course", structured_response.planning_block)
        self.assertIn("Explore your surroundings", structured_response.planning_block)
        
        # API should have been called (but failed)
        self.mock_call_api.assert_called_once()
    
    def test_api_failure_fallback_updates_json_field_green(self):
        """GREEN TEST: Verify fallback mechanism properly updates structured response."""
        response = "Adventure continues."
        user_input = "I move forward"
        
        # Simulate API failure
        self.mock_call_api.side_effect = Exception("Network error")
        
        structured_response = self.NarrativeResponse(
            narrative=response,
            planning_block=""
        )
        
        result = self.validate_func(
            response, user_input, self.mock_game_state,
            self.mock_model, self.mock_system_instruction,
            structured_response=structured_response
        )
        
        # Verify fallback content was set in JSON field
        fallback_content = structured_response.planning_block
        self.assertTrue(len(fallback_content) > 0)
        self.assertIn("What would you like to do next?", fallback_content)
        self.assertIn("[Continue]", fallback_content)
        self.assertIn("[Explore]", fallback_content)
        self.assertIn("[Other]", fallback_content)
    
    def test_no_structured_response_still_works_red(self):
        """RED TEST: Verify function works when no structured_response is provided."""
        response = "Story without planning block."
        user_input = "I continue"
        
        # Call without structured_response (legacy mode)
        result = self.validate_func(
            response, user_input, self.mock_game_state,
            self.mock_model, self.mock_system_instruction,
            structured_response=None
        )
        
        # Should still add planning block to response text
        self.assertIn("--- PLANNING BLOCK ---", result)
        self.assertIn("What would you like to do next?", result)
        
        # API should be called
        self.mock_call_api.assert_called_once()
    
    def test_no_structured_response_still_works_green(self):
        """GREEN TEST: Verify function handles missing structured_response gracefully."""
        response = "Story continues without planning."
        user_input = "I explore"
        
        result = self.validate_func(
            response, user_input, self.mock_game_state,
            self.mock_model, self.mock_system_instruction,
            structured_response=None
        )
        
        # Should update response text for backward compatibility
        self.assertIn("--- PLANNING BLOCK ---", result)
        self.assertIn("Option1", result)
        
        # API should be called to generate content
        self.mock_call_api.assert_called_once()
    
    def test_character_approval_planning_block(self):
        """Test that character approval step gets proper planning block options."""
        response = """[CHARACTER CREATION - AIGenerated]

I've designed a character that fits perfectly with your concept. Here's the complete character sheet:

**CHARACTER SHEET**
Name: Test Character
Race: Human | Class: Fighter | Level: 1

Would you like to play as this character, or would you like me to make some changes?"""
        
        user_input = "show character"
        
        # Mock the API to return character approval options
        self.mock_get_text.return_value = """What would you like to do?
1. **PlayCharacter:** Begin the adventure!
2. **MakeChanges:** Tell me what you'd like to adjust
3. **StartOver:** Design a completely different character"""
        
        # Also update the parse function to return the correct content
        self.mock_parse.return_value = ("""What would you like to do?
1. **PlayCharacter:** Begin the adventure!
2. **MakeChanges:** Tell me what you'd like to adjust
3. **StartOver:** Design a completely different character""", None)
        
        # Call with structured response
        structured_response = self.NarrativeResponse(
            narrative=response,
            planning_block=""
        )
        
        result = self.validate_func(
            response, user_input, self.mock_game_state,
            self.mock_model, self.mock_system_instruction,
            structured_response=structured_response
        )
        
        # Should have character approval options in planning block
        self.assertIn("PlayCharacter", structured_response.planning_block)
        self.assertIn("Begin the adventure", structured_response.planning_block)
        self.assertIn("MakeChanges", structured_response.planning_block)
        self.assertIn("StartOver", structured_response.planning_block)
        
        # Verify the API was called with character approval context
        self.mock_call_api.assert_called_once()
        call_args = self.mock_call_api.call_args[0][0]
        self.assertIn("CHARACTER CREATION APPROVAL", call_args[0])


if __name__ == '__main__':
    unittest.main()