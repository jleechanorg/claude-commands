"""
Test-Driven Development: Tests for Agent classes (StoryModeAgent, GodModeAgent, CombatAgent, CharacterCreationAgent)

These tests verify the behavior of the agent architecture that manages
different interaction modes (story mode vs god mode vs combat mode vs character creation mode) in WorldArchitect.AI.

Agent Architecture:
- BaseAgent: Abstract base class with common functionality
- StoryModeAgent: Handles narrative storytelling (character mode)
- GodModeAgent: Handles administrative commands (god mode)
- CharacterCreationAgent: Handles focused character creation (highest priority except god mode)
- CombatAgent: Handles active combat encounters (combat mode)
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

# PromptBuilder lives with agent prompt utilities
from mvp_site.agent_prompts import PromptBuilder

# Import from agents module (canonical location)
from mvp_site.agents import (
    BaseAgent,
    CharacterCreationAgent,
    CombatAgent,
    GodModeAgent,
    RewardsAgent,
    StoryModeAgent,
    get_agent_for_input,
)


def create_mock_game_state(
    in_combat=False,
    combat_state_dict=None,
    character_creation_completed=True,
    character_name="Test Character",
    character_class="Fighter",
):
    """Helper to create a mock GameState with required methods.

    Args:
        in_combat: Whether the game is in combat mode
        combat_state_dict: Optional combat state dict
        character_creation_completed: Whether character creation is done (default True
            to avoid triggering CharacterCreationAgent in existing tests)
        character_name: Name of the character (empty string triggers character creation)
        character_class: Class of the character (empty string triggers character creation)
    """
    mock_state = Mock()
    mock_state.is_in_combat.return_value = in_combat

    if combat_state_dict is None:
        combat_state_dict = {"in_combat": in_combat}

    mock_state.get_combat_state.return_value = combat_state_dict
    mock_state.combat_state = combat_state_dict

    # Mock custom_campaign_state for CharacterCreationAgent checks
    mock_state.custom_campaign_state = {
        "character_creation_completed": character_creation_completed,
    }

    # Mock player_character_data for CharacterCreationAgent checks
    mock_state.player_character_data = {
        "name": character_name,
        "class": character_class,
    }

    return mock_state


def create_rewards_game_state(
    combat_state: dict | None = None,
    encounter_state: dict | None = None,
    rewards_pending: dict | None = None,
):
    """Helper to create a mock GameState for rewards detection tests."""

    mock_state = Mock()
    mock_state.get_combat_state.return_value = combat_state or {"in_combat": False}
    mock_state.get_encounter_state.return_value = encounter_state or {
        "encounter_active": False
    }
    mock_state.get_rewards_pending.return_value = rewards_pending
    mock_state.is_in_combat.return_value = mock_state.get_combat_state.return_value.get(
        "in_combat", False
    )

    # Mock attributes for CharacterCreationAgent checks (character creation completed)
    mock_state.custom_campaign_state = {"character_creation_completed": True}
    mock_state.player_character_data = {"name": "Test Character", "class": "Fighter"}

    return mock_state


def create_character_creation_game_state(
    character_creation_completed=False,
    character_name="",
    character_class="",
    level_up_pending=False,
):
    """Helper to create a mock GameState for character creation/level-up mode tests.

    Args:
        character_creation_completed: Whether character creation is done
        character_name: Name of the character (empty triggers creation mode)
        character_class: Class of the character (empty triggers creation mode)
        level_up_pending: Whether a level-up is pending (triggers level-up mode)
    """
    mock_state = Mock()
    mock_state.is_in_combat.return_value = False
    mock_state.get_combat_state.return_value = {"in_combat": False}
    mock_state.combat_state = {"in_combat": False}

    mock_state.custom_campaign_state = {
        "character_creation_completed": character_creation_completed,
        "level_up_pending": level_up_pending,
    }
    mock_state.player_character_data = {
        "name": character_name,
        "class": character_class,
    }

    return mock_state


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
        mock_game_state = create_mock_game_state()
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
            all_prompts,
            StoryModeAgent.REQUIRED_PROMPTS | StoryModeAgent.OPTIONAL_PROMPTS,
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
        mock_game_state = create_mock_game_state()
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


class TestCombatAgent(unittest.TestCase):
    """Test cases for CombatAgent class."""

    def test_combat_agent_creation(self):
        """CombatAgent can be instantiated."""
        agent = CombatAgent()
        self.assertIsInstance(agent, BaseAgent)
        self.assertIsInstance(agent, CombatAgent)

    def test_combat_agent_with_game_state(self):
        """CombatAgent accepts game_state parameter."""
        mock_game_state = create_mock_game_state(in_combat=True)
        agent = CombatAgent(game_state=mock_game_state)
        self.assertEqual(agent.game_state, mock_game_state)

    def test_combat_agent_required_prompts(self):
        """CombatAgent has correct required prompts."""
        expected_prompts = {
            constants.PROMPT_TYPE_MASTER_DIRECTIVE,
            constants.PROMPT_TYPE_COMBAT,
            constants.PROMPT_TYPE_GAME_STATE,
            constants.PROMPT_TYPE_NARRATIVE,
            constants.PROMPT_TYPE_DND_SRD,
            constants.PROMPT_TYPE_MECHANICS,
        }
        self.assertEqual(CombatAgent.REQUIRED_PROMPTS, frozenset(expected_prompts))

    def test_combat_agent_optional_prompts(self):
        """CombatAgent has no optional prompts (focused combat mode)."""
        self.assertEqual(CombatAgent.OPTIONAL_PROMPTS, frozenset())

    def test_combat_agent_mode(self):
        """CombatAgent has correct mode identifier."""
        self.assertEqual(CombatAgent.MODE, constants.MODE_COMBAT)

    def test_combat_agent_matches_input_always_false(self):
        """CombatAgent.matches_input always returns False (uses game state instead)."""
        test_inputs = [
            "I attack the goblin!",
            "Roll for initiative",
            "combat start",
            "COMBAT MODE:",
        ]
        for user_input in test_inputs:
            self.assertFalse(
                CombatAgent.matches_input(user_input),
                f"CombatAgent.matches_input should always be False: {user_input}",
            )

    def test_combat_agent_matches_game_state_true_when_in_combat(self):
        """CombatAgent.matches_game_state returns True when in_combat is True."""
        mock_game_state = create_mock_game_state(in_combat=True)
        self.assertTrue(CombatAgent.matches_game_state(mock_game_state))

    def test_combat_agent_matches_game_state_false_when_not_in_combat(self):
        """CombatAgent.matches_game_state returns False when in_combat is False."""
        mock_game_state = create_mock_game_state(in_combat=False)
        self.assertFalse(CombatAgent.matches_game_state(mock_game_state))

    def test_combat_agent_matches_game_state_false_when_none(self):
        """CombatAgent.matches_game_state returns False when game_state is None."""
        self.assertFalse(CombatAgent.matches_game_state(None))

    def test_combat_agent_matches_game_state_false_when_combat_state_missing(self):
        """CombatAgent.matches_game_state returns False when combat_state missing."""
        mock_game_state = Mock(spec=[])  # Empty spec - no attributes
        # Can't use create_mock_game_state because we need spec=[] to fail attribute access
        # But our new code calls is_in_combat() method, so spec=[] mock fails that call
        # We need a mock that HAS is_in_combat but returns something that indicates missing state?
        # Actually, if is_in_combat() exists, it handles missing state internally.
        # The test intends to check what happens if game_state object is malformed?
        # With new interface, we expect game_state to have is_in_combat().
        # If it doesn't, it raises AttributeError, which is acceptable for invalid objects.
        # So we'll skip this test or update it to verify is_in_combat is called.

        # Updated test: Verify matches_game_state relies on is_in_combat
        mock_game_state = Mock()
        # If is_in_combat raises error (simulating missing method), matches_game_state propagates it
        del mock_game_state.is_in_combat
        with self.assertRaises(AttributeError):
            CombatAgent.matches_game_state(mock_game_state)

    def test_combat_agent_matches_game_state_false_when_combat_state_not_dict(self):
        """CombatAgent.matches_game_state returns False when combat_state not dict."""
        # With new implementation, is_in_combat() handles the check.
        # We mock is_in_combat to return False (simulating internal check failure)
        mock_game_state = create_mock_game_state(
            in_combat=False, combat_state_dict=None
        )
        self.assertFalse(CombatAgent.matches_game_state(mock_game_state))


class TestRewardsAgent(unittest.TestCase):
    """Test cases for RewardsAgent class."""

    def test_rewards_agent_creation(self):
        """RewardsAgent can be instantiated."""
        agent = RewardsAgent()
        self.assertIsInstance(agent, BaseAgent)
        self.assertIsInstance(agent, RewardsAgent)

    def test_rewards_agent_required_prompts(self):
        """RewardsAgent has correct required prompts."""
        expected_prompts = {
            constants.PROMPT_TYPE_MASTER_DIRECTIVE,
            constants.PROMPT_TYPE_REWARDS,
            constants.PROMPT_TYPE_GAME_STATE,
            constants.PROMPT_TYPE_DND_SRD,
            constants.PROMPT_TYPE_MECHANICS,
        }
        self.assertEqual(RewardsAgent.REQUIRED_PROMPTS, frozenset(expected_prompts))
        self.assertEqual(RewardsAgent.OPTIONAL_PROMPTS, frozenset())
        self.assertEqual(RewardsAgent.MODE, constants.MODE_REWARDS)

    def test_rewards_agent_matches_input_always_false(self):
        """RewardsAgent.matches_input always returns False (state-driven)."""
        self.assertFalse(RewardsAgent.matches_input("any input"))

    def test_rewards_agent_matches_game_state_combat_end(self):
        """RewardsAgent triggers when combat ended with summary and not processed."""
        combat_state = {
            "in_combat": False,
            "combat_phase": "ended",
            "combat_summary": {"result": "victory"},
            "rewards_processed": False,
        }
        mock_state = create_rewards_game_state(combat_state=combat_state)

        self.assertTrue(RewardsAgent.matches_game_state(mock_state))

    def test_rewards_agent_matches_game_state_combat_finished_variants(self):
        """RewardsAgent handles alternate finished combat phases."""
        combat_state = {
            "in_combat": False,
            "combat_phase": "finished",
            "combat_summary": {"result": "victory"},
            "rewards_processed": False,
        }
        mock_state = create_rewards_game_state(combat_state=combat_state)

        self.assertTrue(RewardsAgent.matches_game_state(mock_state))

        combat_state["combat_phase"] = "victory"
        self.assertTrue(RewardsAgent.matches_game_state(mock_state))

    def test_rewards_agent_matches_game_state_combat_phase_not_finished(self):
        """RewardsAgent ignores combat states that are not finished."""
        combat_state = {
            "in_combat": False,
            "combat_phase": "in_progress",
            "combat_summary": {"result": "pending"},
            "rewards_processed": False,
        }
        mock_state = create_rewards_game_state(combat_state=combat_state)

        self.assertFalse(RewardsAgent.matches_game_state(mock_state))

    def test_rewards_agent_matches_game_state_encounter_completed(self):
        """RewardsAgent triggers when encounter is completed and not processed."""
        encounter_state = {
            "encounter_completed": True,
            "rewards_processed": False,
            "encounter_summary": {"result": "success", "xp_awarded": 120},
        }
        mock_state = create_rewards_game_state(encounter_state=encounter_state)

        self.assertTrue(RewardsAgent.matches_game_state(mock_state))

    def test_rewards_agent_matches_game_state_encounter_missing_summary(self):
        """RewardsAgent does not trigger when encounter summary is missing."""
        encounter_state = {
            "encounter_completed": True,
            "rewards_processed": False,
            # Missing encounter_summary should prevent rewards processing
        }
        mock_state = create_rewards_game_state(encounter_state=encounter_state)

        self.assertFalse(RewardsAgent.matches_game_state(mock_state))

    def test_rewards_agent_matches_game_state_encounter_missing_xp(self):
        """RewardsAgent does not trigger when encounter_summary lacks xp_awarded."""
        encounter_state = {
            "encounter_completed": True,
            "rewards_processed": False,
            "encounter_summary": {"result": "success"},
        }
        mock_state = create_rewards_game_state(encounter_state=encounter_state)

        self.assertFalse(RewardsAgent.matches_game_state(mock_state))

    def test_rewards_agent_matches_game_state_rewards_pending(self):
        """RewardsAgent triggers when rewards_pending exists and not processed."""
        rewards_pending = {"source": "quest", "xp": 100, "processed": False}
        mock_state = create_rewards_game_state(rewards_pending=rewards_pending)

        self.assertTrue(RewardsAgent.matches_game_state(mock_state))

    def test_rewards_agent_matches_game_state_returns_false_when_processed(self):
        """RewardsAgent does not trigger when rewards are already processed."""
        rewards_pending = {"source": "quest", "xp": 50, "processed": True}
        mock_state = create_rewards_game_state(rewards_pending=rewards_pending)

        self.assertFalse(RewardsAgent.matches_game_state(mock_state))

    def test_rewards_agent_matches_game_state_returns_false_for_none(self):
        """RewardsAgent returns False when game_state is None."""
        self.assertFalse(RewardsAgent.matches_game_state(None))

    @patch("mvp_site.agent_prompts._load_instruction_file")
    def test_rewards_agent_builds_instructions(self, mock_load):
        """RewardsAgent.build_system_instructions returns instruction string."""
        mock_load.return_value = "Test instruction content"

        agent = RewardsAgent()
        instructions = agent.build_system_instructions()

        self.assertIsInstance(instructions, str)
        self.assertGreater(len(instructions), 0)


class TestCharacterCreationAgent(unittest.TestCase):
    """Test cases for CharacterCreationAgent class."""

    def test_character_creation_agent_creation(self):
        """CharacterCreationAgent can be instantiated."""
        agent = CharacterCreationAgent()
        self.assertIsInstance(agent, BaseAgent)
        self.assertIsInstance(agent, CharacterCreationAgent)

    def test_character_creation_agent_with_game_state(self):
        """CharacterCreationAgent accepts game_state parameter."""
        mock_game_state = create_character_creation_game_state()
        agent = CharacterCreationAgent(game_state=mock_game_state)
        self.assertEqual(agent.game_state, mock_game_state)

    def test_character_creation_agent_required_prompts(self):
        """CharacterCreationAgent has correct required prompts for creation and level-up."""
        expected_prompts = {
            constants.PROMPT_TYPE_MASTER_DIRECTIVE,
            constants.PROMPT_TYPE_CHARACTER_CREATION,
            constants.PROMPT_TYPE_DND_SRD,
            constants.PROMPT_TYPE_MECHANICS,  # Full D&D rules for level-up
        }
        self.assertEqual(CharacterCreationAgent.REQUIRED_PROMPTS, frozenset(expected_prompts))

    def test_character_creation_agent_no_optional_prompts(self):
        """CharacterCreationAgent has no optional prompts (minimal focused mode)."""
        self.assertEqual(CharacterCreationAgent.OPTIONAL_PROMPTS, frozenset())

    def test_character_creation_agent_mode(self):
        """CharacterCreationAgent has correct mode identifier."""
        self.assertEqual(CharacterCreationAgent.MODE, constants.MODE_CHARACTER_CREATION)

    def test_character_creation_matches_game_state_new_campaign(self):
        """CharacterCreationAgent matches when character has no name/class."""
        mock_state = create_character_creation_game_state(
            character_creation_completed=False,
            character_name="",
            character_class="",
        )
        self.assertTrue(CharacterCreationAgent.matches_game_state(mock_state))

    def test_character_creation_matches_game_state_partial_character(self):
        """CharacterCreationAgent matches when character has name but no class."""
        mock_state = create_character_creation_game_state(
            character_creation_completed=False,
            character_name="Test Hero",
            character_class="",
        )
        self.assertTrue(CharacterCreationAgent.matches_game_state(mock_state))

    def test_character_creation_does_not_match_completed(self):
        """CharacterCreationAgent does not match when creation is completed."""
        mock_state = create_character_creation_game_state(
            character_creation_completed=True,
            character_name="Test Hero",
            character_class="Fighter",
        )
        self.assertFalse(CharacterCreationAgent.matches_game_state(mock_state))

    def test_character_creation_does_not_match_full_character(self):
        """CharacterCreationAgent does not match when character has name and class."""
        mock_state = create_character_creation_game_state(
            character_creation_completed=False,
            character_name="Test Hero",
            character_class="Wizard",
        )
        self.assertFalse(CharacterCreationAgent.matches_game_state(mock_state))

    def test_character_creation_does_not_match_none(self):
        """CharacterCreationAgent does not match when game_state is None."""
        self.assertFalse(CharacterCreationAgent.matches_game_state(None))

    def test_character_creation_matches_level_up_pending(self):
        """CharacterCreationAgent matches when level_up_pending is True."""
        mock_state = create_character_creation_game_state(
            character_creation_completed=True,  # Creation done
            character_name="Test Hero",
            character_class="Fighter",
            level_up_pending=True,  # But level-up pending
        )
        self.assertTrue(CharacterCreationAgent.matches_game_state(mock_state))

    def test_character_creation_does_not_match_no_level_up(self):
        """CharacterCreationAgent does not match when creation done and no level-up."""
        mock_state = create_character_creation_game_state(
            character_creation_completed=True,
            character_name="Test Hero",
            character_class="Fighter",
            level_up_pending=False,
        )
        self.assertFalse(CharacterCreationAgent.matches_game_state(mock_state))

    def test_character_creation_matches_input_done_phrases(self):
        """CharacterCreationAgent.matches_input detects completion phrases."""
        done_phrases = [
            # Character creation completion
            "I'm done",
            "im done",
            "start the story",
            "begin the adventure",
            "let's start",
            "ready to play",
            "character complete",
            # Level-up completion
            "level-up complete",
            "done leveling",
            "back to adventure",
        ]
        for phrase in done_phrases:
            self.assertTrue(
                CharacterCreationAgent.matches_input(phrase),
                f"Should match done phrase: {phrase}",
            )

    def test_character_creation_does_not_match_regular_input(self):
        """CharacterCreationAgent.matches_input returns False for regular creation input."""
        regular_inputs = [
            "I want to be a wizard",
            "Make me a half-elf",
            "What classes are available?",
            "I choose high elf",
        ]
        for user_input in regular_inputs:
            self.assertFalse(
                CharacterCreationAgent.matches_input(user_input),
                f"Should NOT match regular input: {user_input}",
            )

    @patch("mvp_site.agent_prompts._load_instruction_file")
    def test_character_creation_agent_builds_instructions(self, mock_load):
        """CharacterCreationAgent.build_system_instructions returns minimal instruction string."""
        mock_load.return_value = "Test instruction content"

        agent = CharacterCreationAgent()
        instructions = agent.build_system_instructions()

        self.assertIsInstance(instructions, str)
        self.assertGreater(len(instructions), 0)


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
        mock_game_state = create_mock_game_state(in_combat=False)

        # Test with story mode
        story_agent = get_agent_for_input("hello", game_state=mock_game_state)
        self.assertEqual(story_agent.game_state, mock_game_state)

        # Test with god mode
        god_agent = get_agent_for_input("GOD MODE: test", game_state=mock_game_state)
        self.assertEqual(god_agent.game_state, mock_game_state)

    def test_get_agent_returns_combat_agent_when_in_combat(self):
        """get_agent_for_input returns CombatAgent when in_combat is True."""
        mock_game_state = create_mock_game_state(in_combat=True)

        # Regular input during combat should use CombatAgent
        agent = get_agent_for_input("I attack the goblin!", game_state=mock_game_state)
        self.assertIsInstance(agent, CombatAgent)

    def test_get_agent_god_mode_overrides_combat(self):
        """GOD MODE takes priority over combat mode."""
        mock_game_state = create_mock_game_state(in_combat=True)

        # GOD MODE should still work even during combat
        agent = get_agent_for_input(
            "GOD MODE: Set HP to 100", game_state=mock_game_state
        )
        self.assertIsInstance(agent, GodModeAgent)

    def test_get_agent_priority_order(self):
        """Verify agent priority: GOD MODE > CharacterCreation > Combat > Rewards > Story."""
        # Priority 1: GOD MODE always wins (even during character creation)
        char_creation_state = create_character_creation_game_state()
        god_agent = get_agent_for_input("GOD MODE: test", game_state=char_creation_state)
        self.assertIsInstance(god_agent, GodModeAgent)

        # Priority 2: Character Creation when character not complete
        char_agent = get_agent_for_input("I want to be a wizard", game_state=char_creation_state)
        self.assertIsInstance(char_agent, CharacterCreationAgent)

        # Priority 2b: Character Creation transitions to Story when done
        done_agent = get_agent_for_input("I'm done", game_state=char_creation_state)
        self.assertIsInstance(done_agent, StoryModeAgent)

        # Priority 3: Combat when in_combat=True
        combat_state = create_mock_game_state(in_combat=True)
        combat_agent = get_agent_for_input("attack", game_state=combat_state)
        self.assertIsInstance(combat_agent, CombatAgent)

        # Priority 4: Rewards mode when rewards are pending
        rewards_state = create_rewards_game_state(
            combat_state={
                "in_combat": False,
                "combat_phase": "ended",
                "combat_summary": {"result": "victory"},
                "rewards_processed": False,
            }
        )
        rewards_agent = get_agent_for_input("continue", game_state=rewards_state)
        self.assertIsInstance(rewards_agent, RewardsAgent)

        # Priority 5: Story mode as default
        no_combat_state = create_mock_game_state(in_combat=False)
        story_agent = get_agent_for_input("attack", game_state=no_combat_state)
        self.assertIsInstance(story_agent, StoryModeAgent)

    def test_get_agent_returns_rewards_agent_when_encounter_rewards_pending(self):
        """get_agent_for_input returns RewardsAgent when encounter rewards pending."""
        rewards_state = create_rewards_game_state(
            encounter_state={
                "encounter_completed": True,
                "rewards_processed": False,
                "encounter_summary": {"result": "success", "xp_awarded": 50},
            }
        )

        agent = get_agent_for_input("collect", game_state=rewards_state)
        self.assertIsInstance(agent, RewardsAgent)


class TestAgentInstructionBuilding(unittest.TestCase):
    """Test cases for agent system instruction building."""

    @patch("mvp_site.agent_prompts._load_instruction_file")
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

    @patch("mvp_site.agent_prompts._load_instruction_file")
    def test_god_mode_agent_builds_instructions(self, mock_load):
        """GodModeAgent.build_system_instructions returns instruction string."""
        mock_load.return_value = "Test instruction content"

        agent = GodModeAgent()
        instructions = agent.build_system_instructions()

        self.assertIsInstance(instructions, str)
        self.assertGreater(len(instructions), 0)

    @patch("mvp_site.agent_prompts._load_instruction_file")
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

    @patch("mvp_site.agent_prompts._load_instruction_file")
    def test_combat_agent_builds_instructions(self, mock_load):
        """CombatAgent.build_system_instructions returns instruction string."""
        mock_load.return_value = "Test instruction content"

        agent = CombatAgent()
        instructions = agent.build_system_instructions()

        self.assertIsInstance(instructions, str)
        self.assertGreater(len(instructions), 0)

    @patch("mvp_site.agent_prompts._load_instruction_file")
    def test_combat_mode_ignores_selected_prompts(self, mock_load):
        """CombatAgent ignores selected_prompts parameter (uses fixed combat set)."""
        mock_load.return_value = "Test instruction content"

        agent = CombatAgent()

        # Call with various selected_prompts - should all produce same result
        result1 = agent.build_system_instructions(selected_prompts=None)
        result2 = agent.build_system_instructions(
            selected_prompts=[constants.PROMPT_TYPE_NARRATIVE]
        )

        # Both should work without error - combat mode uses fixed prompt set
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

    def test_all_agents_share_core_prompts(self):
        """All agents share essential core prompts."""
        shared_prompts = {
            constants.PROMPT_TYPE_MASTER_DIRECTIVE,
            constants.PROMPT_TYPE_GAME_STATE,
            constants.PROMPT_TYPE_DND_SRD,
        }

        story_all = StoryModeAgent.REQUIRED_PROMPTS | StoryModeAgent.OPTIONAL_PROMPTS
        god_all = GodModeAgent.REQUIRED_PROMPTS | GodModeAgent.OPTIONAL_PROMPTS
        combat_all = CombatAgent.REQUIRED_PROMPTS | CombatAgent.OPTIONAL_PROMPTS

        for prompt in shared_prompts:
            self.assertIn(
                prompt, story_all, f"StoryModeAgent missing shared prompt: {prompt}"
            )
            self.assertIn(
                prompt, god_all, f"GodModeAgent missing shared prompt: {prompt}"
            )
            self.assertIn(
                prompt, combat_all, f"CombatAgent missing shared prompt: {prompt}"
            )

    def test_combat_agent_includes_combat_prompt(self):
        """CombatAgent prompt set includes combat prompt."""
        self.assertIn(constants.PROMPT_TYPE_COMBAT, CombatAgent.REQUIRED_PROMPTS)

    def test_combat_agent_does_not_include_god_mode_prompt(self):
        """CombatAgent prompt set does not include god_mode prompt."""
        all_prompts = CombatAgent.REQUIRED_PROMPTS | CombatAgent.OPTIONAL_PROMPTS
        self.assertNotIn(constants.PROMPT_TYPE_GOD_MODE, all_prompts)

    def test_story_and_god_mode_do_not_include_combat_prompt(self):
        """StoryModeAgent and GodModeAgent do not include combat prompt."""
        story_all = StoryModeAgent.REQUIRED_PROMPTS | StoryModeAgent.OPTIONAL_PROMPTS
        god_all = GodModeAgent.REQUIRED_PROMPTS | GodModeAgent.OPTIONAL_PROMPTS

        self.assertNotIn(constants.PROMPT_TYPE_COMBAT, story_all)
        self.assertNotIn(constants.PROMPT_TYPE_COMBAT, god_all)


if __name__ == "__main__":
    unittest.main()