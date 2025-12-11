"""
Agent Architecture for WorldArchitect.AI

This module provides the agent architecture for handling different interaction
modes in the game. Each agent encapsulates mode-specific logic and has a focused
subset of system prompts.

Agent Hierarchy:
- BaseAgent: Abstract base class with common functionality
- StoryModeAgent: Handles narrative storytelling (character mode)
- GodModeAgent: Handles administrative commands (god mode)

Usage:
    from mvp_site.agents import get_agent_for_input, StoryModeAgent, GodModeAgent

    # Get appropriate agent for user input
    agent = get_agent_for_input(user_input, game_state)

    # Build system instructions
    instructions = agent.build_system_instructions(
        selected_prompts=["narrative", "mechanics"],
        use_default_world=False
    )

Each agent has:
- REQUIRED_PROMPTS: Prompts that are always loaded
- OPTIONAL_PROMPTS: Prompts that may be conditionally loaded
- MODE: The mode identifier for this agent
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from mvp_site import constants, logging_util

if TYPE_CHECKING:
    from mvp_site.game_state import GameState
    from mvp_site.llm_service import PromptBuilder


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the system.

    Agents are responsible for:
    - Defining which system prompts they require/support
    - Building system instructions for LLM calls
    - Detecting whether they should handle a given input
    - Pre-processing user input if needed

    Each agent has a focused subset of all possible system prompts,
    allowing it to specialize in its task without prompt overload.

    Attributes:
        REQUIRED_PROMPTS: Prompts that are always loaded for this agent
        OPTIONAL_PROMPTS: Prompts that may be conditionally loaded
        MODE: The mode identifier for this agent
    """

    # Class-level prompt definitions - override in subclasses
    REQUIRED_PROMPTS: frozenset[str] = frozenset()
    OPTIONAL_PROMPTS: frozenset[str] = frozenset()
    MODE: str = ""

    def __init__(self, game_state: "GameState | None" = None) -> None:
        """
        Initialize the agent.

        Args:
            game_state: GameState object for dynamic instruction generation.
                        If None, static fallback instructions will be used.
        """
        # Import here to avoid circular dependency
        from mvp_site.llm_service import PromptBuilder

        self.game_state = game_state
        self._prompt_builder = PromptBuilder(game_state)

    @property
    def prompt_builder(self) -> "PromptBuilder":
        """Access the underlying PromptBuilder for advanced operations."""
        return self._prompt_builder

    @abstractmethod
    def build_system_instructions(
        self,
        selected_prompts: list[str] | None = None,
        use_default_world: bool = False,
    ) -> str:
        """
        Build the complete system instructions for this agent.

        Args:
            selected_prompts: User-selected prompt types (narrative, mechanics, etc.)
            use_default_world: Whether to include world content in instructions

        Returns:
            Complete system instruction string for the LLM call
        """
        pass

    @classmethod
    def matches_input(cls, user_input: str) -> bool:
        """
        Check if this agent should handle the given input.

        Override in subclasses to implement mode-specific detection logic.

        Args:
            user_input: Raw user input text

        Returns:
            True if this agent should handle the input
        """
        return False

    def preprocess_input(self, user_input: str) -> str:
        """
        Preprocess user input before sending to LLM.

        Override in subclasses if input transformation is needed.

        Args:
            user_input: Raw user input text

        Returns:
            Processed input text
        """
        return user_input

    def get_all_prompts(self) -> frozenset[str]:
        """Get the union of required and optional prompts for this agent."""
        return self.REQUIRED_PROMPTS | self.OPTIONAL_PROMPTS

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(mode={self.MODE}, required={len(self.REQUIRED_PROMPTS)}, optional={len(self.OPTIONAL_PROMPTS)})"


class StoryModeAgent(BaseAgent):
    """
    Agent for Story Mode (Character Mode) interactions.

    This agent handles narrative storytelling, character actions,
    and standard gameplay. It uses the full set of narrative and
    mechanics prompts to generate immersive story content.

    Responsibilities:
    - Narrative generation with planning blocks
    - Character action handling
    - Game mechanics integration (combat, skill checks)
    - Entity tracking and state updates
    - Temporal consistency enforcement

    System Prompt Hierarchy:
    1. Master directive (establishes AI authority)
    2. Game state instructions (data structure compliance)
    3. Debug instructions (dice rolls, state tracking)
    4. Character template (conditional - when narrative enabled)
    5. Narrative/Mechanics (based on campaign settings)
    6. D&D SRD reference
    7. World content (conditional)
    """

    # Required prompts - always loaded for story mode
    REQUIRED_PROMPTS: frozenset[str] = frozenset({
        constants.PROMPT_TYPE_MASTER_DIRECTIVE,
        constants.PROMPT_TYPE_GAME_STATE,
        constants.PROMPT_TYPE_DND_SRD,
    })

    # Optional prompts - loaded based on campaign settings
    OPTIONAL_PROMPTS: frozenset[str] = frozenset({
        constants.PROMPT_TYPE_NARRATIVE,
        constants.PROMPT_TYPE_MECHANICS,
        constants.PROMPT_TYPE_CHARACTER_TEMPLATE,
    })

    MODE: str = constants.MODE_CHARACTER

    def build_system_instructions(
        self,
        selected_prompts: list[str] | None = None,
        use_default_world: bool = False,
        include_continuation_reminder: bool = True,
    ) -> str:
        """
        Build system instructions for story mode.

        Uses the full prompt hierarchy for immersive storytelling:
        - Core instructions (master directive, game state, debug)
        - Character template (if narrative is selected)
        - Selected prompts (narrative, mechanics)
        - System references (D&D SRD)
        - Continuation reminders (planning blocks, temporal enforcement)
        - World content (if enabled)

        Args:
            selected_prompts: User-selected prompt types
            use_default_world: Whether to include world content
            include_continuation_reminder: Whether to add planning block reminders
                                           (True for continue_story, False for initial)

        Returns:
            Complete system instruction string
        """
        if selected_prompts is None:
            selected_prompts = []

        builder = self._prompt_builder

        # Build core instructions (master directive, game state, debug)
        parts: list[str] = builder.build_core_system_instructions()

        # Add character-related instructions (conditional)
        builder.add_character_instructions(parts, selected_prompts)

        # Add selected prompt instructions (narrative, mechanics)
        builder.add_selected_prompt_instructions(parts, selected_prompts)

        # Add system reference instructions (D&D SRD)
        builder.add_system_reference_instructions(parts)

        # Add continuation-specific reminders for story continuation
        if include_continuation_reminder:
            parts.append(builder.build_continuation_reminder())

        # Finalize with world content if requested
        return builder.finalize_instructions(parts, use_default_world)

    @classmethod
    def matches_input(cls, user_input: str) -> bool:
        """
        Story mode is the default - matches any non-god-mode input.

        Args:
            user_input: Raw user input text

        Returns:
            True if the input does NOT start with "GOD MODE:"
        """
        return not user_input.strip().upper().startswith("GOD MODE:")


class GodModeAgent(BaseAgent):
    """
    Agent for God Mode (Administrative) interactions.

    This agent handles administrative commands for correcting mistakes,
    modifying campaign state, and making out-of-game changes. It does
    NOT advance the narrative - that's story mode's job.

    Responsibilities:
    - Administrative state modifications
    - Campaign corrections and fixes
    - Character stat adjustments
    - Inventory modifications
    - Timeline/location corrections
    - NPC relationship changes

    System Prompt Hierarchy:
    1. Master directive (establishes AI authority)
    2. God mode instruction (administrative behavior)
    3. Game state instructions (state structure reference)
    4. D&D SRD (game rules knowledge)
    5. Mechanics (detailed game rules)

    Note: No narrative instructions - god mode doesn't tell stories.
    """

    # Required prompts - always loaded for god mode
    REQUIRED_PROMPTS: frozenset[str] = frozenset({
        constants.PROMPT_TYPE_MASTER_DIRECTIVE,
        constants.PROMPT_TYPE_GOD_MODE,
        constants.PROMPT_TYPE_GAME_STATE,
        constants.PROMPT_TYPE_DND_SRD,
        constants.PROMPT_TYPE_MECHANICS,
    })

    # No optional prompts for god mode - it's focused on administration
    OPTIONAL_PROMPTS: frozenset[str] = frozenset()

    MODE: str = constants.MODE_GOD

    def build_system_instructions(
        self,
        selected_prompts: list[str] | None = None,
        use_default_world: bool = False,
    ) -> str:
        """
        Build system instructions for god mode.

        Uses a focused prompt set for administrative operations:
        - Master directive (authority)
        - God mode instruction (administrative behavior)
        - Game state (state structure reference)
        - D&D SRD (game rules knowledge)
        - Mechanics (detailed game rules)

        Note: selected_prompts is ignored - god mode uses its fixed prompt set.
        Note: use_default_world is always False - god mode doesn't need world lore.

        Args:
            selected_prompts: Ignored for god mode
            use_default_world: Ignored for god mode (always False)

        Returns:
            Complete system instruction string for administrative commands
        """
        # Explicitly ignore selected_prompts and use_default_world
        del selected_prompts
        del use_default_world

        builder = self._prompt_builder

        # Build god mode instructions (fixed prompt set)
        parts: list[str] = builder.build_god_mode_instructions()

        # Finalize WITHOUT world instructions (god mode doesn't need world lore)
        return builder.finalize_instructions(parts, use_default_world=False)

    @classmethod
    def matches_input(cls, user_input: str) -> bool:
        """
        God mode is triggered by "GOD MODE:" prefix.

        Args:
            user_input: Raw user input text

        Returns:
            True if the input starts with "GOD MODE:" (case-insensitive)
        """
        return user_input.strip().upper().startswith("GOD MODE:")

    def preprocess_input(self, user_input: str) -> str:
        """
        Preprocess god mode input.

        Preserves the "GOD MODE:" prefix for the LLM to recognize
        the administrative command context.

        Args:
            user_input: Raw user input with "GOD MODE:" prefix

        Returns:
            Input unchanged (LLM needs to see the GOD MODE: prefix)
        """
        return user_input


def get_agent_for_input(
    user_input: str, game_state: "GameState | None" = None
) -> BaseAgent:
    """
    Factory function to get the appropriate agent for user input.

    Determines which agent should handle the input based on mode detection:
    - GodModeAgent if input starts with "GOD MODE:"
    - StoryModeAgent for all other inputs (default)

    Args:
        user_input: Raw user input text
        game_state: GameState for context (passed to agent)

    Returns:
        The appropriate agent instance for handling the input

    Example:
        >>> agent = get_agent_for_input("GOD MODE: Set my HP to 50")
        >>> isinstance(agent, GodModeAgent)
        True
        >>> agent = get_agent_for_input("I attack the goblin!")
        >>> isinstance(agent, StoryModeAgent)
        True
    """
    if GodModeAgent.matches_input(user_input):
        logging_util.info("🔮 GOD_MODE_DETECTED: Using GodModeAgent")
        return GodModeAgent(game_state)

    return StoryModeAgent(game_state)


# Export all public classes and functions
__all__ = [
    "BaseAgent",
    "StoryModeAgent",
    "GodModeAgent",
    "get_agent_for_input",
]
