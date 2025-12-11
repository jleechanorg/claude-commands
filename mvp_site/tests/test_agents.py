"""
Test-Driven Development: Tests for Agent classes (StoryModeAgent, GodModeAgent)

These tests verify the behavior of the agent architecture that manages
different interaction modes (story mode vs god mode) in WorldArchitect.AI.

Agent Architecture:
- BaseAgent: Abstract base class with common functionality
- StoryModeAgent: Handles narrative storytelling (character mode)
- GodModeAgent: Handles administrative commands (god mode)
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch

# Add the parent directory to the Python path so we can import modules
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from mvp_site import constants

# Import from agents module (canonical location)
from mvp_site.agents import (
    BaseAgent,
    StoryModeAgent,
    GodModeAgent,
    get_agent_for_input,
)

# PromptBuilder remains in llm_service
from mvp_site.llm_service import PromptBuilder


class TestBaseAgent(unittest.TestCase):
    """Test cases for BaseAgent abstract class."""

    def test_base_agent_is_abstract(self):
        """BaseAgent cannot be instantiated directly."""
        with self.assertRaises(TypeError) as context:
            BaseAgent()
        self.assertIn("abstract", str(context.exception).lower())

    def test_base_agent_class_attributes(self):
        """BaseAgent has required class attributes."""
        self.assertTrue(hasattr(BaseAgent, "REQUIRED_PROMPTS"))
        self.assertTrue(hasattr(BaseAgent, "OPTIONAL_PROMPTS"))
        self.assertTrue(hasattr(BaseAgent, "MODE"))
        self.assertIsInstance(BaseAgent.REQUIRED_PROMPTS, frozenset)
        self.assertIsInstance(BaseAgent.OPTIONAL_PROMPTS, frozenset)


class TestStoryModeAgent(unittest.TestCase):
    """Test cases for StoryModeAgent class."""

    def test_story_mode_agent_creation(self):
        """StoryModeAgent can be instantiated."""
        agent = StoryModeAgent()
        self.assertIsInstance(agent, BaseAgent)
        self.assertIsInstance(agent, StoryModeAgent)

    def test_story_mode_agent_with_game_state(self):
        """StoryModeAgent accepts game_state parameter."""
        mock_game_state = Mock()
        agent = StoryModeAgent(game_state=mock_game_state)
        self.assertEqual(agent.game_state, mock_game_state)

    def test_story_mode_agent_required_prompts(self):
        """StoryModeAgent has correct required prompts."""
        expected_prompts = {
            constants.PROMPT_TYPE_MASTER_DIRECTIVE,
            constants.PROMPT_TYPE_GAME_STATE,
            constants.PROMPT_TYPE_DND_SRD,
        }
        self.assertEqual(StoryModeAgent.REQUIRED_PROMPTS, frozenset(expected_prompts))

    def test_story_mode_agent_optional_prompts(self):
        """StoryModeAgent has correct optional prompts."""
        expected_prompts = {
            constants.PROMPT_TYPE_NARRATIVE,
            constants.PROMPT_TYPE_MECHANICS,
            constants.PROMPT_TYPE_CHARACTER_TEMPLATE,
        }
        self.assertEqual(StoryModeAgent.OPTIONAL_PROMPTS, frozenset(expected_prompts))

    def test_story_mode_agent_mode(self):
        """StoryModeAgent has correct mode identifier."""
        self.assertEqual(StoryModeAgent.MODE, constants.MODE_CHARACTER)

    def test_story_mode_matches_regular_input(self):
        """StoryModeAgent matches regular story inputs."""
        test_inputs = [
            "I attack the goblin!",
            "Let me think about this",
            "Search the room for traps",
            "god",  # Not "GOD MODE:" - should match story mode
            "Tell me about god mode",
            "What is god?",
        ]
        for user_input in test_inputs:
            self.assertTrue(
                StoryModeAgent.matches_input(user_input),
                f"StoryModeAgent should match: {user_input}",
            )

    def test_story_mode_does_not_match_god_mode_input(self):
        """StoryModeAgent does not match god mode inputs."""
        test_inputs = [
            "GOD MODE: Set my HP to 50",
            "god mode: heal me",
            "  GOD MODE: fix my stats",
            "GOD MODE:",
        ]
        for user_input in test_inputs:
            self.assertFalse(
                StoryModeAgent.matches_input(user_input),
                f"StoryModeAgent should NOT match: {user_input}",
            )

    def test_story_mode_agent_has_prompt_builder(self):
        """StoryModeAgent provides access to its PromptBuilder."""
        agent = StoryModeAgent()
        self.assertIsInstance(agent.prompt_builder, PromptBuilder)

    def test_story_mode_agent_get_all_prompts(self):
        """StoryModeAgent.get_all_prompts returns union of required and optional."""
        agent = StoryModeAgent()
        all_prompts = agent.get_all_prompts()
        self.assertEqual(
            all_prompts, StoryModeAgent.REQUIRED_PROMPTS | StoryModeAgent.OPTIONAL_PROMPTS
        )

    def test_story_mode_agent_repr(self):
        """StoryModeAgent has informative repr."""
        agent = StoryModeAgent()
        repr_str = repr(agent)
        self.assertIn("StoryModeAgent", repr_str)
        self.assertIn("mode=", repr_str)


class TestGodModeAgent(unittest.TestCase):
    """Test cases for GodModeAgent class."""

    def test_god_mode_agent_creation(self):
        """GodModeAgent can be instantiated."""
        agent = GodModeAgent()
        self.assertIsInstance(agent, BaseAgent)
        self.assertIsInstance(agent, GodModeAgent)

    def test_god_mode_agent_with_game_state(self):
        """GodModeAgent accepts game_state parameter."""
        mock_game_state = Mock()
        agent = GodModeAgent(game_state=mock_game_state)
        self.assertEqual(agent.game_state, mock_game_state)

    def test_god_mode_agent_required_prompts(self):
        """GodModeAgent has correct required prompts."""
        expected_prompts = {
            constants.PROMPT_TYPE_MASTER_DIRECTIVE,
            constants.PROMPT_TYPE_GOD_MODE,
            constants.PROMPT_TYPE_GAME_STATE,
            constants.PROMPT_TYPE_DND_SRD,
            constants.PROMPT_TYPE_MECHANICS,
        }
        self.assertEqual(GodModeAgent.REQUIRED_PROMPTS, frozenset(expected_prompts))

    def test_god_mode_agent_no_optional_prompts(self):
        """GodModeAgent has no optional prompts (focused on administration)."""
        self.assertEqual(GodModeAgent.OPTIONAL_PROMPTS, frozenset())

    def test_god_mode_agent_mode(self):
        """GodModeAgent has correct mode identifier."""
        self.assertEqual(GodModeAgent.MODE, constants.MODE_GOD)

    def test_god_mode_matches_god_mode_input(self):
        """GodModeAgent matches god mode inputs."""
        test_inputs = [
            "GOD MODE: Set my HP to 50",
            "god mode: heal me",
            "  GOD MODE: fix my stats",
            "GOD MODE:",
            "GOD MODE: anything",
        ]
        for user_input in test_inputs:
            self.assertTrue(
                GodModeAgent.matches_input(user_input),
                f"GodModeAgent should match: {user_input}",
            )

    def test_god_mode_does_not_match_regular_input(self):
        """GodModeAgent does not match regular story inputs."""
        test_inputs = [
            "I attack the goblin!",
            "Let me think about this",
            "god",  # Not "GOD MODE:"
            "Tell me about god mode",
            "god mode but not at start",
            "This is not GOD MODE: command",
        ]
        for user_input in test_inputs:
            self.assertFalse(
                GodModeAgent.matches_input(user_input),
                f"GodModeAgent should NOT match: {user_input}",
            )

    def test_god_mode_agent_has_prompt_builder(self):
        """GodModeAgent provides access to its PromptBuilder."""
        agent = GodModeAgent()
        self.assertIsInstance(agent.prompt_builder, PromptBuilder)

    def test_god_mode_agent_preprocess_input(self):
        """GodModeAgent.preprocess_input preserves GOD MODE prefix."""
        agent = GodModeAgent()
        test_input = "GOD MODE: Set HP to 50"
        processed = agent.preprocess_input(test_input)
        self.assertEqual(processed, test_input)

    def test_god_mode_agent_repr(self):
        """GodModeAgent has informative repr."""
        agent = GodModeAgent()
        repr_str = repr(agent)
        self.assertIn("GodModeAgent", repr_str)
        self.assertIn("mode=", repr_str)


class TestGetAgentForInput(unittest.TestCase):
    """Test cases for get_agent_for_input factory function."""

    def test_get_agent_returns_god_mode_for_god_mode_input(self):
        """get_agent_for_input returns GodModeAgent for god mode inputs."""
        test_inputs = [
            "GOD MODE: Set my HP to 50",
            "god mode: heal me",
            "GOD MODE:",
        ]
        for user_input in test_inputs:
            agent = get_agent_for_input(user_input)
            self.assertIsInstance(
                agent, GodModeAgent, f"Should return GodModeAgent for: {user_input}"
            )

    def test_get_agent_returns_story_mode_for_regular_input(self):
        """get_agent_for_input returns StoryModeAgent for regular inputs."""
        test_inputs = [
            "I attack the goblin!",
            "Think about my options",
            "god",
            "What is god mode?",
        ]
        for user_input in test_inputs:
            agent = get_agent_for_input(user_input)
            self.assertIsInstance(
                agent, StoryModeAgent, f"Should return StoryModeAgent for: {user_input}"
            )

    def test_get_agent_passes_game_state(self):
        """get_agent_for_input passes game_state to the agent."""
        mock_game_state = Mock()

        # Test with story mode
        story_agent = get_agent_for_input("hello", game_state=mock_game_state)
        self.assertEqual(story_agent.game_state, mock_game_state)

        # Test with god mode
        god_agent = get_agent_for_input("GOD MODE: test", game_state=mock_game_state)
        self.assertEqual(god_agent.game_state, mock_game_state)


class TestAgentInstructionBuilding(unittest.TestCase):
    """Test cases for agent system instruction building."""

    @patch("mvp_site.llm_service._load_instruction_file")
    def test_story_mode_agent_builds_instructions(self, mock_load):
        """StoryModeAgent.build_system_instructions returns instruction string."""
        mock_load.return_value = "Test instruction content"

        agent = StoryModeAgent()
        instructions = agent.build_system_instructions(
            selected_prompts=[constants.PROMPT_TYPE_NARRATIVE],
            use_default_world=False,
            include_continuation_reminder=False,
        )

        self.assertIsInstance(instructions, str)
        self.assertGreater(len(instructions), 0)

    @patch("mvp_site.llm_service._load_instruction_file")
    def test_god_mode_agent_builds_instructions(self, mock_load):
        """GodModeAgent.build_system_instructions returns instruction string."""
        mock_load.return_value = "Test instruction content"

        agent = GodModeAgent()
        instructions = agent.build_system_instructions()

        self.assertIsInstance(instructions, str)
        self.assertGreater(len(instructions), 0)

    @patch("mvp_site.llm_service._load_instruction_file")
    def test_god_mode_ignores_selected_prompts(self, mock_load):
        """GodModeAgent ignores selected_prompts parameter."""
        mock_load.return_value = "Test instruction content"

        agent = GodModeAgent()

        # Call with various selected_prompts - should all produce same result
        result1 = agent.build_system_instructions(selected_prompts=None)
        result2 = agent.build_system_instructions(
            selected_prompts=[constants.PROMPT_TYPE_NARRATIVE]
        )

        # Both should work without error - god mode uses fixed prompt set
        self.assertIsInstance(result1, str)
        self.assertIsInstance(result2, str)


class TestAgentPromptSets(unittest.TestCase):
    """Test cases verifying agents have correct prompt subsets."""

    def test_story_mode_does_not_include_god_mode_prompt(self):
        """StoryModeAgent prompt set does not include god_mode prompt."""
        all_prompts = StoryModeAgent.REQUIRED_PROMPTS | StoryModeAgent.OPTIONAL_PROMPTS
        self.assertNotIn(constants.PROMPT_TYPE_GOD_MODE, all_prompts)

    def test_god_mode_includes_god_mode_prompt(self):
        """GodModeAgent prompt set includes god_mode prompt."""
        self.assertIn(constants.PROMPT_TYPE_GOD_MODE, GodModeAgent.REQUIRED_PROMPTS)

    def test_god_mode_does_not_include_narrative_prompt(self):
        """GodModeAgent prompt set does not include narrative prompt."""
        all_prompts = GodModeAgent.REQUIRED_PROMPTS | GodModeAgent.OPTIONAL_PROMPTS
        self.assertNotIn(constants.PROMPT_TYPE_NARRATIVE, all_prompts)

    def test_both_agents_share_core_prompts(self):
        """Both agents share essential core prompts."""
        shared_prompts = {
            constants.PROMPT_TYPE_MASTER_DIRECTIVE,
            constants.PROMPT_TYPE_GAME_STATE,
            constants.PROMPT_TYPE_DND_SRD,
        }

        story_all = StoryModeAgent.REQUIRED_PROMPTS | StoryModeAgent.OPTIONAL_PROMPTS
        god_all = GodModeAgent.REQUIRED_PROMPTS | GodModeAgent.OPTIONAL_PROMPTS

        for prompt in shared_prompts:
            self.assertIn(
                prompt, story_all, f"StoryModeAgent missing shared prompt: {prompt}"
            )
            self.assertIn(
                prompt, god_all, f"GodModeAgent missing shared prompt: {prompt}"
            )


if __name__ == "__main__":
    unittest.main()
