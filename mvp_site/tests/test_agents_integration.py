"""
Integration tests for Agent architecture in WorldArchitect.AI.

This test suite verifies the complete flow of agent-based mode handling,
including mode detection, system instruction building, and integration
with the PromptBuilder class.

Tests cover:
- End-to-end agent selection based on user input
- System instruction building with actual prompt files
- Mode-specific prompt sets (story mode vs god mode)
- Integration between agents and PromptBuilder
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch

# Add the project root to the Python path so we can import modules
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.insert(0, project_root)

from mvp_site import constants
from mvp_site.agents import (
    BaseAgent,
    StoryModeAgent,
    GodModeAgent,
    get_agent_for_input,
)


class TestAgentModeDetectionIntegration(unittest.TestCase):
    """Integration tests for agent mode detection flow."""

    def test_story_mode_flow_with_various_inputs(self):
        """Test complete story mode flow with various input types."""
        story_inputs = [
            "I attack the goblin with my sword!",
            "Let me think about my options here...",
            "Search the room for hidden traps",
            "Cast fireball at the enemies",
            "I want to talk to the merchant",
            "What do I see around me?",
            "Rest for the night at the inn",
        ]

        for user_input in story_inputs:
            with self.subTest(input=user_input):
                agent = get_agent_for_input(user_input)
                self.assertIsInstance(agent, StoryModeAgent)
                self.assertEqual(agent.MODE, constants.MODE_CHARACTER)

    def test_god_mode_flow_with_various_inputs(self):
        """Test complete god mode flow with various input types."""
        god_inputs = [
            "GOD MODE: Set my HP to 50",
            "god mode: Add 100 gold to my inventory",
            "GOD MODE: Change my level to 10",
            "God Mode: Reset the combat encounter",
            "GOD MODE: Teleport me to the tavern",
            "  GOD MODE: Fix the broken quest state",
        ]

        for user_input in god_inputs:
            with self.subTest(input=user_input):
                agent = get_agent_for_input(user_input)
                self.assertIsInstance(agent, GodModeAgent)
                self.assertEqual(agent.MODE, constants.MODE_GOD)

    def test_mode_boundary_cases(self):
        """Test edge cases in mode detection."""
        # These should NOT trigger god mode
        not_god_mode = [
            "god",  # Just the word
            "god mode please",  # Not at start with colon
            "Tell me about god mode",
            "How does god mode work?",
            "GOD_MODE: test",  # Wrong format (underscore)
            "GODMODE: test",  # Missing space
        ]

        for user_input in not_god_mode:
            with self.subTest(input=user_input):
                agent = get_agent_for_input(user_input)
                self.assertIsInstance(
                    agent,
                    StoryModeAgent,
                    f"Expected StoryModeAgent for: {user_input}",
                )


class TestAgentInstructionBuildingIntegration(unittest.TestCase):
    """Integration tests for agent instruction building."""

    @patch("mvp_site.llm_service._load_instruction_file")
    def test_story_mode_instruction_building_flow(self, mock_load):
        """Test complete story mode instruction building flow."""
        # Mock instruction file loading
        mock_load.return_value = "Mock instruction content"

        agent = StoryModeAgent()
        instructions = agent.build_system_instructions(
            selected_prompts=[constants.PROMPT_TYPE_NARRATIVE, constants.PROMPT_TYPE_MECHANICS],
            use_default_world=False,
            include_continuation_reminder=True,
        )

        # Verify instruction building
        self.assertIsInstance(instructions, str)
        self.assertGreater(len(instructions), 0)

        # Verify that instruction files were loaded
        self.assertTrue(mock_load.called)

    @patch("mvp_site.llm_service._load_instruction_file")
    def test_god_mode_instruction_building_flow(self, mock_load):
        """Test complete god mode instruction building flow."""
        # Mock instruction file loading
        mock_load.return_value = "Mock instruction content"

        agent = GodModeAgent()
        instructions = agent.build_system_instructions()

        # Verify instruction building
        self.assertIsInstance(instructions, str)
        self.assertGreater(len(instructions), 0)

        # Verify that instruction files were loaded
        self.assertTrue(mock_load.called)

    @patch("mvp_site.llm_service._load_instruction_file")
    def test_story_mode_without_continuation_reminder(self, mock_load):
        """Test story mode instruction building for initial story (no continuation reminder)."""
        mock_load.return_value = "Mock instruction content"

        agent = StoryModeAgent()
        instructions = agent.build_system_instructions(
            selected_prompts=[constants.PROMPT_TYPE_NARRATIVE],
            use_default_world=False,
            include_continuation_reminder=False,  # For initial story
        )

        self.assertIsInstance(instructions, str)
        self.assertGreater(len(instructions), 0)


class TestAgentGameStateIntegration(unittest.TestCase):
    """Integration tests for agents with game state."""

    def test_agent_with_game_state(self):
        """Test that agents properly receive and use game state."""
        # Create mock game state
        mock_game_state = Mock()
        mock_game_state.world_data = {
            "world_time": {"year": 1492, "month": "Mirtul", "day": 15},
            "current_location_name": "Waterdeep",
        }
        mock_game_state.combat_state = {"in_combat": False}

        # Test story mode agent
        story_agent = get_agent_for_input("I look around", game_state=mock_game_state)
        self.assertEqual(story_agent.game_state, mock_game_state)
        self.assertIsInstance(story_agent, StoryModeAgent)

        # Test god mode agent
        god_agent = get_agent_for_input("GOD MODE: test", game_state=mock_game_state)
        self.assertEqual(god_agent.game_state, mock_game_state)
        self.assertIsInstance(god_agent, GodModeAgent)

    def test_agent_without_game_state(self):
        """Test that agents work correctly without game state."""
        story_agent = get_agent_for_input("Hello world", game_state=None)
        self.assertIsNone(story_agent.game_state)
        self.assertIsNotNone(story_agent.prompt_builder)


class TestAgentPromptSetIntegration(unittest.TestCase):
    """Integration tests for agent prompt sets."""

    def test_story_mode_prompt_set_completeness(self):
        """Test that story mode has all required prompts for storytelling."""
        all_prompts = StoryModeAgent.REQUIRED_PROMPTS | StoryModeAgent.OPTIONAL_PROMPTS

        # Must have core prompts
        self.assertIn(constants.PROMPT_TYPE_MASTER_DIRECTIVE, all_prompts)
        self.assertIn(constants.PROMPT_TYPE_GAME_STATE, all_prompts)

        # Must have storytelling prompts
        self.assertIn(constants.PROMPT_TYPE_NARRATIVE, all_prompts)
        self.assertIn(constants.PROMPT_TYPE_DND_SRD, all_prompts)

        # Should NOT have god mode prompt
        self.assertNotIn(constants.PROMPT_TYPE_GOD_MODE, all_prompts)

    def test_god_mode_prompt_set_completeness(self):
        """Test that god mode has all required prompts for administration."""
        all_prompts = GodModeAgent.REQUIRED_PROMPTS | GodModeAgent.OPTIONAL_PROMPTS

        # Must have core prompts
        self.assertIn(constants.PROMPT_TYPE_MASTER_DIRECTIVE, all_prompts)
        self.assertIn(constants.PROMPT_TYPE_GAME_STATE, all_prompts)
        self.assertIn(constants.PROMPT_TYPE_GOD_MODE, all_prompts)

        # Must have mechanics knowledge for proper corrections
        self.assertIn(constants.PROMPT_TYPE_DND_SRD, all_prompts)
        self.assertIn(constants.PROMPT_TYPE_MECHANICS, all_prompts)

        # Should NOT have narrative prompt
        self.assertNotIn(constants.PROMPT_TYPE_NARRATIVE, all_prompts)
        self.assertNotIn(constants.PROMPT_TYPE_CHARACTER_TEMPLATE, all_prompts)

    def test_prompt_set_overlap(self):
        """Test that both agents share appropriate core prompts."""
        story_prompts = StoryModeAgent.REQUIRED_PROMPTS | StoryModeAgent.OPTIONAL_PROMPTS
        god_prompts = GodModeAgent.REQUIRED_PROMPTS | GodModeAgent.OPTIONAL_PROMPTS

        # Both should have these fundamental prompts
        shared_required = {
            constants.PROMPT_TYPE_MASTER_DIRECTIVE,
            constants.PROMPT_TYPE_GAME_STATE,
            constants.PROMPT_TYPE_DND_SRD,
        }

        for prompt in shared_required:
            self.assertIn(prompt, story_prompts, f"StoryMode missing: {prompt}")
            self.assertIn(prompt, god_prompts, f"GodMode missing: {prompt}")


class TestAgentBackwardCompatibility(unittest.TestCase):
    """Integration tests for backward compatibility."""

    def test_import_from_llm_service(self):
        """Test that agents can still be imported from llm_service."""
        # This tests backward compatibility
        from mvp_site.llm_service import (
            BaseAgent as LLMBaseAgent,
            StoryModeAgent as LLMStoryModeAgent,
            GodModeAgent as LLMGodModeAgent,
            get_agent_for_input as llm_get_agent,
        )

        # Verify they are the same classes
        self.assertIs(LLMBaseAgent, BaseAgent)
        self.assertIs(LLMStoryModeAgent, StoryModeAgent)
        self.assertIs(LLMGodModeAgent, GodModeAgent)
        self.assertIs(llm_get_agent, get_agent_for_input)

    def test_import_from_agents_module(self):
        """Test that agents can be imported from agents module."""
        from mvp_site.agents import (
            BaseAgent,
            StoryModeAgent,
            GodModeAgent,
            get_agent_for_input,
        )

        # Verify classes are properly defined
        self.assertTrue(hasattr(BaseAgent, "REQUIRED_PROMPTS"))
        self.assertTrue(hasattr(StoryModeAgent, "build_system_instructions"))
        self.assertTrue(hasattr(GodModeAgent, "matches_input"))
        self.assertTrue(callable(get_agent_for_input))


class TestAgentPreprocessingIntegration(unittest.TestCase):
    """Integration tests for agent input preprocessing."""

    def test_story_mode_preserves_input(self):
        """Test that story mode agent preserves user input."""
        agent = StoryModeAgent()
        test_input = "I attack the goblin!"
        processed = agent.preprocess_input(test_input)
        self.assertEqual(processed, test_input)

    def test_god_mode_preserves_prefix(self):
        """Test that god mode agent preserves GOD MODE prefix."""
        agent = GodModeAgent()
        test_input = "GOD MODE: Set HP to 50"
        processed = agent.preprocess_input(test_input)
        self.assertEqual(processed, test_input)
        self.assertTrue(processed.upper().startswith("GOD MODE:"))


if __name__ == "__main__":
    unittest.main()
