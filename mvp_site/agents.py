"""
Agent Architecture for WorldArchitect.AI

This module provides the agent architecture for handling different interaction
modes in the game. Each agent encapsulates mode-specific logic and has a focused
subset of system prompts.

Agent Hierarchy (priority order used by get_agent_for_input):
- BaseAgent: Abstract base class with common functionality
- GodModeAgent: Handles administrative commands (god mode)
- PlanningAgent: Handles strategic planning (think mode)
- InfoAgent: Handles equipment/inventory queries (trimmed prompts)
- CombatAgent: Handles active combat encounters (combat mode)
- RewardsAgent: Handles rewards, loot, and progression-related logic
- StoryModeAgent: Handles narrative storytelling (character mode)

Usage:
    from mvp_site.agents import (
        get_agent_for_input,
        StoryModeAgent,
        GodModeAgent,
        PlanningAgent,
        InfoAgent,
        CombatAgent,
    )

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
from mvp_site.agent_prompts import PromptBuilder

if TYPE_CHECKING:
    from mvp_site.game_state import GameState


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
        include_continuation_reminder: bool = True,
        turn_number: int = 0,
        llm_requested_sections: list[str] | None = None,
    ) -> str:
        """
        Build the complete system instructions for this agent.

        Args:
            selected_prompts: User-selected prompt types (narrative, mechanics, etc.)
            use_default_world: Whether to include world content in instructions
            include_continuation_reminder: Whether to include continuation reminders
            turn_number: Current turn number (used for living world advancement)

        Returns:
            Complete system instruction string for the LLM call
        """
        ...  # Abstract method - implemented by subclasses

    @classmethod
    def matches_input(cls, _user_input: str) -> bool:
        """
        Check if this agent should handle the given input.

        Override in subclasses to implement mode-specific detection logic.

        Args:
            _user_input: Raw user input text (unused in base class)

        Returns:
            True if this agent should handle the input
        """
        return False

    @classmethod
    def matches_game_state(cls, _game_state: "GameState | None") -> bool:
        """
        Check if this agent should handle the current game state.

        Override in subclasses to implement game-state-based detection logic.

        Args:
            _game_state: Current GameState object (unused in base class)

        Returns:
            True if this agent should handle the game state
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
    REQUIRED_PROMPTS: frozenset[str] = frozenset(
        {
            constants.PROMPT_TYPE_MASTER_DIRECTIVE,
            constants.PROMPT_TYPE_GAME_STATE,
            constants.PROMPT_TYPE_PLANNING_PROTOCOL,  # Planning block schema
            constants.PROMPT_TYPE_DND_SRD,
        }
    )

    # Optional prompts - loaded based on campaign settings
    OPTIONAL_PROMPTS: frozenset[str] = frozenset(
        {
            constants.PROMPT_TYPE_NARRATIVE,
            constants.PROMPT_TYPE_MECHANICS,
            constants.PROMPT_TYPE_CHARACTER_TEMPLATE,
        }
    )

    MODE: str = constants.MODE_CHARACTER

    def build_system_instructions(
        self,
        selected_prompts: list[str] | None = None,
        use_default_world: bool = False,
        include_continuation_reminder: bool = True,
        turn_number: int = 0,
        llm_requested_sections: list[str] | None = None,
    ) -> str:
        """
        Build system instructions for story mode.

        Uses the full prompt hierarchy for immersive storytelling:
        - Core instructions (master directive, game state, debug)
        - Character template (if narrative is selected)
        - Selected prompts (narrative, mechanics)
        - System references (D&D SRD)
        - Continuation reminders (planning blocks, temporal enforcement)
        - Living world instruction (every 3 turns)
        - World content (if enabled)

        Args:
            selected_prompts: User-selected prompt types
            use_default_world: Whether to include world content
            include_continuation_reminder: Whether to add planning block reminders
                                           (True for continue_story, False for initial)
            turn_number: Current turn number (used for living world advancement)
            llm_requested_sections: Sections the LLM requested via meta.needs_detailed_instructions
                                    from the previous turn (e.g., ["relationships", "reputation"])

        Returns:
            Complete system instruction string
        """
        parts = self.build_system_instruction_parts(
            selected_prompts=selected_prompts,
            include_continuation_reminder=include_continuation_reminder,
            turn_number=turn_number,
            llm_requested_sections=llm_requested_sections,
        )

        # Finalize with world content if requested
        return self._prompt_builder.finalize_instructions(parts, use_default_world)

    def build_system_instruction_parts(
        self,
        selected_prompts: list[str] | None = None,
        include_continuation_reminder: bool = True,
        turn_number: int = 0,
        llm_requested_sections: list[str] | None = None,
    ) -> list[str]:
        """
        Build the ordered instruction parts for story mode before finalization.

        This helper returns the base instruction list so callers (like initial
        story generation) can insert additional blocks before world lore is
        appended via finalize_instructions.

        Args:
            selected_prompts: User-selected prompt types
            include_continuation_reminder: Whether to add planning block reminders
            turn_number: Current turn number (used for living world advancement)
            llm_requested_sections: Sections the LLM requested via meta.needs_detailed_instructions
                                    from the previous turn (e.g., ["relationships", "reputation"])

        Returns:
            List of ordered system instruction parts (without world content).
        """
        if selected_prompts is None:
            selected_prompts = []

        builder = self._prompt_builder

        # Build core instructions (master directive, game state, debug)
        parts: list[str] = builder.build_core_system_instructions()

        # Add character-related instructions (conditional)
        builder.add_character_instructions(parts, selected_prompts)

        # Add selected prompt instructions (narrative, mechanics)
        # Pass LLM-requested sections to load detailed prompts dynamically
        builder.add_selected_prompt_instructions(
            parts, selected_prompts, llm_requested_sections=llm_requested_sections
        )

        # Add system reference instructions (D&D SRD)
        builder.add_system_reference_instructions(parts)

        # Add continuation-specific reminders for story continuation
        if include_continuation_reminder:
            parts.append(builder.build_continuation_reminder())

        # Add living world instruction every N turns (default: 3)
        # This advances world state for off-screen characters, factions, and events
        if turn_number > 0:
            living_world_instruction = builder.build_living_world_instruction(turn_number)
            if living_world_instruction:
                parts.append(living_world_instruction)

        return parts

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
    REQUIRED_PROMPTS: frozenset[str] = frozenset(
        {
            constants.PROMPT_TYPE_MASTER_DIRECTIVE,
            constants.PROMPT_TYPE_GOD_MODE,
            constants.PROMPT_TYPE_GAME_STATE,
            constants.PROMPT_TYPE_PLANNING_PROTOCOL,  # Canonical planning block schema
            constants.PROMPT_TYPE_DND_SRD,
            constants.PROMPT_TYPE_MECHANICS,
        }
    )

    # No optional prompts for god mode - it's focused on administration
    OPTIONAL_PROMPTS: frozenset[str] = frozenset()

    MODE: str = constants.MODE_GOD

    def build_system_instructions(
        self,
        selected_prompts: list[str] | None = None,
        use_default_world: bool = False,
        include_continuation_reminder: bool = True,
        turn_number: int = 0,
        llm_requested_sections: list[str] | None = None,
    ) -> str:
        """
        Build system instructions for god mode.

        Uses a focused prompt set for administrative operations:
        - Master directive (authority)
        - God mode instruction (administrative behavior)
        - Game state (state structure reference)
        - D&D SRD (game rules knowledge)
        - Mechanics (detailed game rules)

        Note: selected_prompts, use_default_world, and turn_number parameters are
        accepted to match the BaseAgent interface but are intentionally ignored
        because god mode always uses its fixed prompt set without world lore or
        living world advancement.

        Returns:
            Complete system instruction string for administrative commands
        """
        # Parameters intentionally unused - god mode uses fixed prompt set
        del selected_prompts, use_default_world, include_continuation_reminder, turn_number
        del llm_requested_sections

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


# --- CHARACTER CREATION / LEVEL-UP COMPLETION DETECTION ---
# Phrases that indicate the user is finished with character creation or level-up
CHARACTER_CREATION_DONE_PHRASES = [
    # Character creation completion
    "i'm done",
    "im done",
    "i am done",
    "i'm finished",
    "im finished",
    "i am finished",
    "start the story",
    "begin the story",
    "start adventure",
    "begin adventure",
    "start the adventure",
    "begin the adventure",
    "let's start",
    "lets start",
    "let's begin",
    "lets begin",
    "ready to play",
    "i'm ready",
    "im ready",
    "that's everything",
    "thats everything",
    "character complete",
    "character is complete",
    "done creating",
    "finished creating",
    # Level-up completion
    "level-up complete",
    "levelup complete",
    "level up complete",
    "done leveling",
    "finished leveling",
    "done with level",
    "back to adventure",
    "continue adventure",
    "return to game",
]


class CharacterCreationAgent(BaseAgent):
    """
    Agent for Character Creation & Level-Up Mode.

    This agent handles character creation AND level-ups with focused prompts.
    TIME DOES NOT ADVANCE during this mode - it's a "pause menu" for character
    building. The story only resumes when the user explicitly confirms they're done.

    PRECEDENCE: Second highest (just below GodModeAgent).

    Trigger Conditions (matches_game_state returns True when):
    1. New campaign: character_creation_completed is False
    2. No character: player_character_data.name is empty
    3. Level-up pending: level_up_pending flag is True

    Responsibilities:
    - Guide character concept development (new characters)
    - Handle race/class/background selection
    - Manage ability score assignment
    - Develop personality and backstory
    - Process level-ups with full D&D 5e rules
    - Handle ASI/Feat selection, new spells, class features
    - Confirm completion before transitioning to story

    System Prompt Hierarchy:
    1. Master directive (establishes AI authority)
    2. Character creation instruction (creation + level-up flow)
    3. D&D SRD (mechanics reference for options)
    4. Mechanics (detailed D&D rules for level-up choices)

    Note: NO narrative or combat prompts - time is frozen during this mode.
    """

    # Minimal prompts for focused character creation and level-up
    REQUIRED_PROMPTS: frozenset[str] = frozenset({
        constants.PROMPT_TYPE_MASTER_DIRECTIVE,
        constants.PROMPT_TYPE_CHARACTER_CREATION,
        constants.PROMPT_TYPE_DND_SRD,
        constants.PROMPT_TYPE_MECHANICS,  # Full D&D rules for creation and level-up
    })

    # No optional prompts - keep it focused
    OPTIONAL_PROMPTS: frozenset[str] = frozenset()

    MODE: str = constants.MODE_CHARACTER_CREATION

    def build_system_instructions(
        self,
        selected_prompts: list[str] | None = None,
        use_default_world: bool = False,
        include_continuation_reminder: bool = True,
        turn_number: int = 0,
        llm_requested_sections: list[str] | None = None,
    ) -> str:
        """
        Build MINIMAL system instructions for character creation mode.

        Uses a focused prompt set for character building:
        - Master directive (authority)
        - Character creation instruction (focused creation flow)
        - D&D SRD (mechanics reference)

        No narrative, no combat, no game state - keeps prompts minimal.

        Returns:
            Minimal system instruction string for character creation
        """
        # Parameters intentionally unused - character creation uses fixed minimal set
        del selected_prompts, use_default_world, include_continuation_reminder
        del turn_number, llm_requested_sections

        builder = self._prompt_builder

        # Build character creation instructions (minimal prompt set)
        parts: list[str] = builder.build_character_creation_instructions()

        # Finalize WITHOUT world lore (character creation doesn't need it)
        return builder.finalize_instructions(parts, use_default_world=False)

    @classmethod
    def matches_game_state(cls, game_state: "GameState | None") -> bool:
        """
        Check if character creation or level-up mode should be active.

        This mode is active when:
        1. game_state exists
        2. AND one of these conditions:
           a) character_creation_completed is False (new character)
           b) Character doesn't have a name/class yet
           c) level_up_pending flag is True (level-up in progress)

        Args:
            game_state: Current GameState object

        Returns:
            True if character creation or level-up is in progress
        """
        if game_state is None:
            logging_util.debug(
                "🎭 CHARACTER_CREATION_CHECK: game_state is None"
            )
            return False

        # Get custom_campaign_state
        custom_state = None
        if hasattr(game_state, "custom_campaign_state"):
            custom_state = game_state.custom_campaign_state
        elif isinstance(game_state, dict):
            custom_state = game_state.get("custom_campaign_state", {})

        if custom_state and isinstance(custom_state, dict):
            # Check for level-up pending (takes priority - always enter this mode)
            if custom_state.get("level_up_pending", False):
                logging_util.info(
                    "🎭 CHARACTER_CREATION_CHECK: level_up_pending=True, entering level-up mode"
                )
                return True

            # Check if character creation is explicitly completed
            if custom_state.get("character_creation_completed", False):
                logging_util.debug(
                    "🎭 CHARACTER_CREATION_CHECK: character_creation_completed=True"
                )
                return False

        # Check if character has a name (indicates creation may be done)
        pc_data = None
        if hasattr(game_state, "player_character_data"):
            pc_data = game_state.player_character_data
        elif isinstance(game_state, dict):
            pc_data = game_state.get("player_character_data", {})

        if pc_data and isinstance(pc_data, dict):
            # If character has a name AND class, likely creation is done
            # (unless explicitly marked as in-progress)
            char_name = pc_data.get("name", "")
            char_class = pc_data.get("class", "") or pc_data.get("character_class", "")

            if char_name and char_class:
                # Character has name and class - check if explicitly in creation mode
                in_creation_mode = custom_state.get(
                    "character_creation_in_progress", False
                ) if custom_state else False

                if not in_creation_mode:
                    logging_util.debug(
                        f"🎭 CHARACTER_CREATION_CHECK: Character has name='{char_name}' "
                        f"and class='{char_class}', creation assumed complete"
                    )
                    return False

        # Default: if campaign is new and character isn't complete, we're in creation
        logging_util.info(
            "🎭 CHARACTER_CREATION_CHECK: Character creation mode ACTIVE"
        )
        return True

    @classmethod
    def matches_input(cls, user_input: str) -> bool:
        """
        Check if user input indicates character creation completion.

        Returns True if the input suggests they want to START the story,
        which means we should transition OUT of character creation.

        Note: This returns True to MATCH when user is DONE with creation,
        which the get_agent_for_input logic uses to transition to StoryMode.

        Args:
            user_input: Raw user input text

        Returns:
            True if user indicates they're done with character creation
        """
        lower = user_input.lower().strip()
        return any(phrase in lower for phrase in CHARACTER_CREATION_DONE_PHRASES)


class PlanningAgent(BaseAgent):
    """
    Agent for Think Mode (Strategic Planning) interactions.

    This agent handles strategic planning and tactical analysis where the
    character pauses to think WITHOUT advancing the narrative. Time only
    advances by 1 microsecond to maintain temporal ordering.

    PlanningAgent sits at priority 2 in agent selection: it is checked
    immediately after GodModeAgent and before all other specialized
    agents (Info, Combat, Rewards) and StoryModeAgent. When a user
    explicitly enters Think Mode, this agent handles the input ahead of
    all non-god interactions.

    Responsibilities:
    - Deep strategic analysis with multiple options
    - Pros/cons evaluation for each approach
    - Confidence assessment for tactical choices
    - Internal monologue generation (character's thoughts)
    - Microsecond-only time advancement (no narrative time)

    System Prompt Hierarchy:
    1. Master directive (establishes AI authority)
    2. Think mode instruction (planning behavior)
    3. Game state instructions (state structure reference)
    4. D&D SRD (game rules knowledge)

    Note: No narrative advancement - world is frozen while character thinks.
    """

    # Required prompts - always loaded for think mode
    REQUIRED_PROMPTS: frozenset[str] = frozenset(
        {
            constants.PROMPT_TYPE_MASTER_DIRECTIVE,
            constants.PROMPT_TYPE_THINK,
            constants.PROMPT_TYPE_PLANNING_PROTOCOL,  # Planning block schema (canonical)
            constants.PROMPT_TYPE_GAME_STATE,
            constants.PROMPT_TYPE_DND_SRD,
        }
    )

    # No optional prompts for think mode - it's focused on planning
    OPTIONAL_PROMPTS: frozenset[str] = frozenset()

    MODE: str = constants.MODE_THINK

    def build_system_instructions(
        self,
        selected_prompts: list[str] | None = None,
        use_default_world: bool = False,
        include_continuation_reminder: bool = True,
        turn_number: int = 0,
        llm_requested_sections: list[str] | None = None,
    ) -> str:
        """
        Build system instructions for think mode.

        Uses a focused prompt set for strategic planning:
        - Master directive (authority)
        - Think mode instruction (planning behavior)
        - Game state (state structure reference)
        - D&D SRD (game rules knowledge)

        Note: selected_prompts, use_default_world, and turn_number parameters are
        accepted to match the BaseAgent interface but are intentionally ignored
        because think mode always uses its fixed prompt set without world lore or
        living world advancement.

        Returns:
            Complete system instruction string for strategic planning
        """
        # Parameters intentionally unused - think mode uses fixed prompt set
        del selected_prompts, use_default_world, include_continuation_reminder, turn_number
        del llm_requested_sections

        builder = self._prompt_builder

        # Build think mode instructions (fixed prompt set)
        parts: list[str] = builder.build_think_mode_instructions()

        # Finalize WITHOUT world instructions (think mode doesn't need world lore)
        return builder.finalize_instructions(parts, use_default_world=False)

    @classmethod
    def matches_input(cls, user_input: str, mode: str | None = None) -> bool:
        """
        Think mode is triggered by "THINK:" prefix or explicit mode selection.

        Uses constants.is_think_mode() for centralized detection logic.
        Note: matches_input() is called during agent selection, which happens
        AFTER the frontend has normalized the input (adding THINK: prefix when
        mode == "think"), so the mode parameter is typically not needed here.

        Args:
            user_input: Raw user input text
            mode: Optional mode parameter from request (rarely needed since
                  frontend normalizes input before agent selection)

        Returns:
            True if think mode is detected via prefix or mode
        """
        return constants.is_think_mode(user_input, mode)

    def preprocess_input(self, user_input: str) -> str:
        """
        Preprocess think mode input.

        Preserves the "THINK:" prefix for the LLM to recognize
        the planning command context.

        Args:
            user_input: Raw user input with "THINK:" prefix

        Returns:
            Input unchanged (LLM needs to see the THINK: prefix)
        """
        return user_input


# --- INFO QUERY CLASSIFICATION ---
# Conservative patterns: Only route to InfoAgent for CLEAR info-only queries

INFO_QUERY_PATTERNS = [
    "show me my",  # "show me my equipment"
    "what do i have",  # "what do I have equipped"
    "list my",  # "list my items"
    "check my",  # "check my inventory"
    "what's in my",  # "what's in my backpack"
    "what am i wearing",
    "what am i carrying",
    "my equipment",  # "show my equipment"
    "my inventory",  # "check my inventory"
    "my gear",  # "list my gear"
    "my items",  # "show my items"
    "my weapons",  # "what are my weapons"
    "what weapons",  # "what weapons do I have"
    "do i have",  # "what items do I have" - broader pattern
]

# If ANY action verb present, stay in StoryMode (conservative)
STORY_ACTION_VERBS = [
    "find",
    "buy",
    "sell",
    "search",
    "look for",
    "upgrade",
    "equip",
    "unequip",
    "drop",
    "pick up",
    "use",
    "trade",
    "get",
    "acquire",
    "steal",
    "loot",
    "craft",
    "repair",
]


class InfoAgent(BaseAgent):
    """
    Agent for Information Queries (Equipment, Inventory, Stats).

    This agent handles pure information queries with TRIMMED system prompts
    to improve LLM compliance with exact item naming. It does NOT advance
    the narrative - use StoryModeAgent for any action-based queries.

    Responsibilities:
    - Equipment listing with exact item names
    - Inventory display (backpack, weapons, equipped items)
    - Character stats display
    - Pure information retrieval (no story advancement)

    System Prompt Hierarchy (TRIMMED for focus):
    1. Master directive (establishes AI authority)
    2. Game state instructions (contains Equipment Query Protocol)
    3. Planning protocol (canonical planning_block schema)

    Note: NO narrative, mechanics, or character_template prompts.
    This reduces prompt from ~2000 lines to ~1100 lines, improving
    LLM focus on the Equipment Query Protocol.
    """

    # TRIMMED prompts - only essentials for info queries
    REQUIRED_PROMPTS: frozenset[str] = frozenset(
        {
            constants.PROMPT_TYPE_MASTER_DIRECTIVE,
            constants.PROMPT_TYPE_GAME_STATE,  # Contains Equipment Query Protocol
            constants.PROMPT_TYPE_PLANNING_PROTOCOL,  # Canonical planning block schema
        }
    )

    # No optional prompts - keep it focused
    OPTIONAL_PROMPTS: frozenset[str] = frozenset()

    MODE: str = constants.MODE_INFO

    def build_system_instructions(
        self,
        selected_prompts: list[str] | None = None,
        use_default_world: bool = False,
        include_continuation_reminder: bool = True,
        turn_number: int = 0,
        llm_requested_sections: list[str] | None = None,
    ) -> str:
        """
        Build TRIMMED system instructions for info queries.

        Uses minimal prompt set to maximize LLM focus on Equipment Query Protocol:
        - Master directive (authority)
        - Game state instruction (contains Equipment Query Protocol)
        - Current game state (for context)

        Note: selected_prompts and turn_number are intentionally ignored -
        info mode uses fixed set without living world advancement.

        Returns:
            Trimmed system instruction string for information queries
        """
        # Parameters intentionally unused - info mode uses fixed prompt set
        del selected_prompts, use_default_world, include_continuation_reminder, turn_number
        del llm_requested_sections

        builder = self._prompt_builder

        # Build info mode instructions (trimmed prompt set)
        parts: list[str] = builder.build_info_mode_instructions()

        # Finalize WITHOUT world lore (info mode doesn't need it)
        return builder.finalize_instructions(parts, use_default_world=False)

    @classmethod
    def matches_input(cls, user_input: str) -> bool:
        """
        Conservative detection: Only match CLEAR info-only queries.

        Route to InfoAgent only when:
        1. Input matches an info query pattern (show/list/check)
        2. No action verbs present (find/buy/sell/search)

        If uncertain, returns False (defaults to StoryModeAgent).

        Args:
            user_input: Raw user input text

        Returns:
            True only for clear info-only queries
        """
        lower = user_input.lower()

        # If ANY action verb present, it's a story query
        if any(verb in lower for verb in STORY_ACTION_VERBS):
            return False

        # Only route to InfoAgent for clear info patterns
        return any(pattern in lower for pattern in INFO_QUERY_PATTERNS)


class CombatAgent(BaseAgent):
    """
    Agent for Combat Mode (Active Combat Encounters).

    This agent handles tactical combat encounters with focused prompts for
    dice rolls, initiative tracking, combat rewards, and boss equipment.
    It is automatically selected when game_state.combat_state.in_combat is True.

    Responsibilities:
    - Initiative and turn order management
    - Combat dice roll enforcement (attacks, saves, damage)
    - Combat state tracking (HP, conditions, position)
    - Combat end rewards (XP, loot, resources)
    - Boss/Special NPC equipment enforcement
    - Combat session tracking with unique IDs

    System Prompt Hierarchy:
    1. Master directive (establishes AI authority)
    2. Game state instructions (combat_state schema - loaded before combat rules)
    3. Combat system instruction (tactical combat rules)
    4. Narrative instruction (DM Note protocol, cinematic style)
    5. D&D SRD (combat rules reference)
    6. Mechanics (detailed combat mechanics)
    7. Debug instructions (combat logging)

    Note: Combat mode automatically transitions back to story mode when combat ends.
    """

    # Required prompts - always loaded for combat mode
    REQUIRED_PROMPTS: frozenset[str] = frozenset(
        {
            constants.PROMPT_TYPE_MASTER_DIRECTIVE,
            constants.PROMPT_TYPE_COMBAT,
            constants.PROMPT_TYPE_GAME_STATE,
            constants.PROMPT_TYPE_PLANNING_PROTOCOL,  # Canonical planning block schema
            constants.PROMPT_TYPE_NARRATIVE,  # For DM Note protocol and cinematic style
            constants.PROMPT_TYPE_DND_SRD,
            constants.PROMPT_TYPE_MECHANICS,
        }
    )

    # No optional prompts for combat mode - it's focused on tactical combat
    OPTIONAL_PROMPTS: frozenset[str] = frozenset()

    MODE: str = constants.MODE_COMBAT

    def build_system_instructions(
        self,
        selected_prompts: list[str] | None = None,
        use_default_world: bool = False,
        include_continuation_reminder: bool = True,
        turn_number: int = 0,
        llm_requested_sections: list[str] | None = None,
    ) -> str:
        """
        Build system instructions for combat mode.

        Uses a focused prompt set for tactical combat operations:
        - Master directive (authority)
        - Combat system instruction (tactical rules, dice, rewards)
        - Game state (combat_state structure)
        - D&D SRD (combat rules)
        - Mechanics (detailed combat mechanics)
        - Debug instructions (combat logging)

        Note: selected_prompts and turn_number parameters are accepted for
        interface consistency but combat mode uses its fixed combat-focused
        prompt set without living world advancement.

        Returns:
            Complete system instruction string for combat encounters
        """
        # Parameters intentionally unused - combat mode uses fixed prompt set
        del selected_prompts, include_continuation_reminder, turn_number
        del llm_requested_sections

        builder = self._prompt_builder

        # Build combat mode instructions (fixed prompt set)
        parts: list[str] = builder.build_combat_mode_instructions()

        # Finalize with optional world instructions (for combat in specific locations)
        return builder.finalize_instructions(parts, use_default_world=use_default_world)

    @classmethod
    def matches_game_state(cls, game_state: "GameState | None") -> bool:
        """
        Check if combat mode should be active based on game state.

        Combat mode is triggered when:
        - game_state is not None
        - game_state.is_in_combat() returns True

        Uses standardized GameState.is_in_combat() helper for consistent access.

        Args:
            game_state: Current GameState object

        Returns:
            True if combat is active and CombatAgent should be used
        """
        if game_state is None:
            logging_util.debug("⚔️ COMBAT_CHECK: game_state is None, not in combat")
            return False

        # Use standardized helper method for consistent combat state access
        in_combat = game_state.is_in_combat()
        combat_state = game_state.get_combat_state()

        logging_util.info(
            f"⚔️ COMBAT_CHECK: in_combat={in_combat}, "
            f"combat_state_keys={list(combat_state.keys())}"
        )
        return in_combat

    @classmethod
    def matches_input(cls, _user_input: str) -> bool:
        """
        Combat mode is NOT triggered by input - only by game state.

        Args:
            _user_input: Raw user input text (unused)

        Returns:
            Always False - use matches_game_state instead
        """
        return False


class RewardsAgent(BaseAgent):
    """
    Agent for Rewards Mode (XP, Loot, Level-Up Processing).

    This agent handles ALL reward processing from any source:
    - Combat victories (triggered after combat ends)
    - Non-combat encounters (heists, social victories, stealth successes)
    - Quest completions
    - Milestone achievements

    Responsibilities:
    - XP calculation and awarding from any source
    - Loot distribution and inventory updates
    - Level-up detection and processing
    - Encounter history archival
    - Resource restoration (if applicable)

    Trigger Conditions (matches_game_state returns True when):
    1. combat_phase == "ended" AND combat_summary exists
    2. encounter_state.encounter_completed == true
    3. rewards_pending exists in game_state

    System Prompt Hierarchy:
    1. Master directive (establishes AI authority)
    2. Game state instructions (state structure reference)
    3. Rewards system instruction (XP/loot/level-up rules)
    4. D&D SRD (game rules for XP thresholds)
    5. Mechanics (detailed level-up rules)

    Note: After rewards are processed, this agent transitions back to story mode.
    """

    # Required prompts - always loaded for rewards mode
    REQUIRED_PROMPTS: frozenset[str] = frozenset({
        constants.PROMPT_TYPE_MASTER_DIRECTIVE,
        constants.PROMPT_TYPE_GAME_STATE,
        constants.PROMPT_TYPE_PLANNING_PROTOCOL,  # Canonical planning block schema
        constants.PROMPT_TYPE_REWARDS,
        constants.PROMPT_TYPE_DND_SRD,
        constants.PROMPT_TYPE_MECHANICS,
    })

    # No optional prompts for rewards mode - focused on reward processing
    OPTIONAL_PROMPTS: frozenset[str] = frozenset()

    MODE: str = constants.MODE_REWARDS

    def build_system_instructions(
        self,
        selected_prompts: list[str] | None = None,
        use_default_world: bool = False,
        include_continuation_reminder: bool = True,
        turn_number: int = 0,
        llm_requested_sections: list[str] | None = None,
    ) -> str:
        """
        Build system instructions for rewards mode.

        Uses a focused prompt set for reward processing:
        - Master directive (authority)
        - Rewards system instruction (XP/loot/level-up rules)
        - Game state (state structure reference)
        - D&D SRD (XP thresholds, level rules)
        - Mechanics (detailed level-up mechanics)

        Args:
            selected_prompts: List of prompt types to include
            use_default_world: Whether to use default world background
            include_continuation_reminder: Whether to include continuation reminder
            turn_number: Current turn number
            llm_requested_sections: Sections requested by LLM (compatibility parameter, unused)

        Returns:
            Complete system instruction string for rewards processing
        """
        # Parameters intentionally unused - rewards mode uses fixed prompt set
        del selected_prompts, include_continuation_reminder, use_default_world, turn_number, llm_requested_sections

        builder = self._prompt_builder

        # Build rewards mode instructions (fixed prompt set)
        parts: list[str] = builder.build_rewards_mode_instructions()

        # Finalize without world instructions (rewards don't need world lore)
        return builder.finalize_instructions(parts, use_default_world=False)

    @classmethod
    def matches_game_state(cls, game_state: "GameState | None") -> bool:
        """
        Check if rewards mode should be active based on game state.

        Rewards mode is triggered when ANY of these conditions are true:
        1. combat_phase == "ended" AND combat_summary exists
        2. encounter_state.encounter_completed == true AND encounter_summary exists
        3. rewards_pending exists in game_state

        Args:
            game_state: Current GameState object

        Returns:
            True if rewards are pending and RewardsAgent should be used
        """
        if game_state is None:
            logging_util.debug("🏆 REWARDS_CHECK: game_state is None, no rewards pending")
            return False

        # Check 1: Combat just ended with summary (needs reward processing)
        combat_state = game_state.get_combat_state()
        # Use centralized constant for combat finished phases
        if (
            combat_state.get("combat_phase") in constants.COMBAT_FINISHED_PHASES
            and combat_state.get("combat_summary")
            and not combat_state.get("rewards_processed", False)
        ):
            logging_util.info(
                "🏆 REWARDS_CHECK: Combat ended with summary, rewards pending"
            )
            return True

        # Check 2: Encounter completed (non-combat rewards)
        encounter_state = game_state.get_encounter_state()
        encounter_completed = encounter_state.get("encounter_completed", False)
        encounter_summary = encounter_state.get("encounter_summary")
        encounter_processed = encounter_state.get("rewards_processed", False)

        if encounter_completed:
            if not isinstance(encounter_summary, dict):
                logging_util.debug(
                    "🏆 REWARDS_CHECK: Encounter completed but encounter_summary missing/invalid"
                )
            elif encounter_summary.get("xp_awarded") is None:
                logging_util.debug(
                    "🏆 REWARDS_CHECK: Encounter completed but encounter_summary missing xp_awarded"
                )
            elif not encounter_processed:
                logging_util.info(
                    "🏆 REWARDS_CHECK: Encounter completed, rewards pending"
                )
                return True

        # Check 3: Explicit rewards_pending flag
        rewards_pending = game_state.get_rewards_pending()
        if rewards_pending and not rewards_pending.get("processed", False):
            logging_util.info(
                f"🏆 REWARDS_CHECK: Explicit rewards_pending={rewards_pending}"
            )
            return True

        logging_util.debug("🏆 REWARDS_CHECK: No rewards pending")
        return False

    @classmethod
    def matches_input(cls, _user_input: str) -> bool:
        """
        Rewards mode is NOT triggered by input - only by game state.

        Args:
            _user_input: Raw user input text (unused)

        Returns:
            Always False - use matches_game_state instead
        """
        return False


def get_agent_for_input(
    user_input: str, game_state: "GameState | None" = None, mode: str | None = None
) -> BaseAgent:
    """
    Factory function to get the appropriate agent for user input.

    Determines which agent should handle the input based on mode detection:
    1. GodModeAgent if input starts with "GOD MODE:" (highest priority)
    2. CharacterCreationAgent if character creation is in progress (second highest)
       - UNLESS user indicates they're done, then transitions to StoryMode
    3. PlanningAgent if input starts with "THINK:" or mode is "think" (strategic planning)
    4. InfoAgent for pure info queries (equipment, inventory, stats)
    5. CombatAgent if game_state.combat_state.in_combat is True
    6. RewardsAgent if rewards are pending (combat end, encounter completion)
    7. StoryModeAgent for all other inputs (default)

    Args:
        user_input: Raw user input text
        game_state: GameState for context (passed to agent)
        mode: Optional mode string from API client (e.g., "think", "character")

    Returns:
        The appropriate agent instance for handling the input

    Example:
        >>> agent = get_agent_for_input("GOD MODE: Set my HP to 50")
        >>> isinstance(agent, GodModeAgent)
        True
        >>> # During character creation
        >>> agent = get_agent_for_input("I want to be a wizard", new_campaign_state)
        >>> isinstance(agent, CharacterCreationAgent)
        True
        >>> # When done with character creation
        >>> agent = get_agent_for_input("I'm done", new_campaign_state)
        >>> isinstance(agent, StoryModeAgent)  # Transitions out
        True
        >>> agent = get_agent_for_input("list my equipment")
        >>> isinstance(agent, InfoAgent)
        True
        >>> # With combat_state.in_combat = True
        >>> agent = get_agent_for_input("I attack the goblin!", combat_game_state)
        >>> isinstance(agent, CombatAgent)
        True
        >>> # With rewards pending (combat ended or encounter completed)
        >>> agent = get_agent_for_input("continue", rewards_pending_state)
        >>> isinstance(agent, RewardsAgent)
        True
        >>> agent = get_agent_for_input("THINK: what are my options?")
        >>> isinstance(agent, PlanningAgent)
        True
        >>> agent = get_agent_for_input("I explore the tavern.")
        >>> isinstance(agent, StoryModeAgent)
        True
    """
    # Priority 1: GOD MODE always takes precedence (administrative override)
    if GodModeAgent.matches_input(user_input):
        logging_util.info("🔮 GOD_MODE_DETECTED: Using GodModeAgent")
        return GodModeAgent(game_state)

    # Priority 2: Character Creation mode (second highest priority)
    # Check if we're in character creation AND user isn't indicating they're done
    if CharacterCreationAgent.matches_game_state(game_state):
        # If user says they're done, transition to story mode
        if CharacterCreationAgent.matches_input(user_input):
            logging_util.info(
                "🎭 CHARACTER_CREATION_COMPLETE: User finished, transitioning to StoryModeAgent"
            )
            return StoryModeAgent(game_state)
        # Otherwise, stay in character creation mode
        logging_util.info("🎭 CHARACTER_CREATION_ACTIVE: Using CharacterCreationAgent")
        return CharacterCreationAgent(game_state)

    # Priority 3: Think mode for strategic planning (higher than all non-god modes)
    # Supports both THINK: prefix and explicit mode="think" from API clients
    if PlanningAgent.matches_input(user_input, mode):
        logging_util.info("🧠 THINK_MODE_DETECTED: Using PlanningAgent")
        return PlanningAgent(game_state)

    # Priority 4: Info queries (equipment, inventory, stats) - trimmed prompts
    if InfoAgent.matches_input(user_input):
        logging_util.info("📦 INFO_QUERY_DETECTED: Using InfoAgent (trimmed prompts)")
        return InfoAgent(game_state)

    # Priority 5: Combat mode when in active combat
    if CombatAgent.matches_game_state(game_state):
        logging_util.info("⚔️ COMBAT_MODE_ACTIVE: Using CombatAgent")
        return CombatAgent(game_state)

    # Priority 6: Rewards mode when rewards are pending
    if RewardsAgent.matches_game_state(game_state):
        logging_util.info("🏆 REWARDS_MODE_ACTIVE: Using RewardsAgent")
        return RewardsAgent(game_state)

    # Priority 7: Default to story mode
    return StoryModeAgent(game_state)


# Export all public classes and functions
__all__ = [
    "BaseAgent",
    "StoryModeAgent",
    "GodModeAgent",
    "CharacterCreationAgent",
    "PlanningAgent",
    "InfoAgent",
    "CombatAgent",
    "RewardsAgent",
    "get_agent_for_input",
]
