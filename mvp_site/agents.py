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


# ============================================================================
# PROMPT ORDER INVARIANTS
# ============================================================================
# These invariants ensure consistent prompt loading order across all agents.
# The LLM processes prompts in order, so the head order establishes authority.

# Mandatory head order invariants:
# 1. master_directive MUST be first (establishes authority)
# 2. game_state and planning_protocol MUST be consecutive (anchors schema)
#    - Mode-specific prompts (god_mode, think) may appear between master_directive
#      and the game_state→planning_protocol pair, but not between those two elements

MANDATORY_FIRST_PROMPT = constants.PROMPT_TYPE_MASTER_DIRECTIVE
GAME_STATE_PLANNING_PAIR = (
    constants.PROMPT_TYPE_GAME_STATE,
    constants.PROMPT_TYPE_PLANNING_PROTOCOL,
)


def validate_prompt_order(
    order: tuple[str, ...], agent_name: str = "unknown"
) -> list[str]:
    """
    Validate that prompt order satisfies head invariants.

    Invariants checked:
    1. master_directive is first (index 0)
    2. game_state and planning_protocol are consecutive (game_state → planning_protocol)

    Args:
        order: Ordered tuple of prompt types
        agent_name: Agent name for error messages

    Returns:
        List of validation errors (empty if valid)
    """
    errors: list[str] = []

    if not order:
        errors.append(f"{agent_name}: REQUIRED_PROMPT_ORDER is empty")
        return errors

    # Invariant 0b: duplicates not allowed (catch early, with indices)
    seen: dict[str, int] = {}
    for idx, prompt in enumerate(order):
        if prompt in seen:
            errors.append(
                f"{agent_name}: Duplicate prompt type in REQUIRED_PROMPT_ORDER: "
                f"{prompt!r} at indices {seen[prompt]} and {idx}"
            )
        else:
            seen[prompt] = idx

    # Invariant 1: master_directive must be first
    if order[0] != MANDATORY_FIRST_PROMPT:
        errors.append(
            f"{agent_name}: First prompt must be {MANDATORY_FIRST_PROMPT!r}, "
            f"got {order[0]!r}"
        )

    # Invariant 2: game_state and planning_protocol must both exist and be consecutive
    req_gs, req_pp = GAME_STATE_PLANNING_PAIR
    missing_prompts = [p for p in (req_gs, req_pp) if p not in order]
    if missing_prompts:
        missing_list = ", ".join(repr(p) for p in missing_prompts)
        errors.append(
            f"{agent_name}: Missing required prompt(s) in order: {missing_list}"
        )
        return errors  # Can't check adjacency if members are missing

    gs_idx = order.index(req_gs)
    pp_idx = order.index(req_pp)
    if pp_idx != gs_idx + 1:
        errors.append(
            f"{agent_name}: planning_protocol must immediately follow game_state. "
            f"game_state at index {gs_idx}, planning_protocol at {pp_idx}"
        )

    return errors


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
        REQUIRED_PROMPT_ORDER: Ordered tuple of prompts always loaded (explicit order)
        REQUIRED_PROMPTS: Prompts that are always loaded for this agent (set view)
        OPTIONAL_PROMPTS: Prompts that may be conditionally loaded
        MODE: The mode identifier for this agent
    """

    # Class-level prompt definitions - override in subclasses
    # REQUIRED_PROMPT_ORDER: Explicit ordered tuple (source of truth for order)
    REQUIRED_PROMPT_ORDER: tuple[str, ...] = ()
    # REQUIRED_PROMPTS: Set view for membership testing (derived from order)
    REQUIRED_PROMPTS: frozenset[str] = frozenset()
    OPTIONAL_PROMPTS: frozenset[str] = frozenset()
    MODE: str = ""
    # Cache to avoid re-validating prompt order on every instantiation
    _prompt_order_validated: bool = False

    def __init__(self, game_state: "GameState | None" = None) -> None:
        """
        Initialize the agent.

        Args:
            game_state: GameState object for dynamic instruction generation.
                        If None, static fallback instructions will be used.
        """
        self._ensure_prompt_order_valid()
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

    @classmethod
    def validate_prompt_order(cls) -> list[str]:
        """
        Validate this agent's REQUIRED_PROMPT_ORDER against head invariants.

        Returns:
            List of validation errors (empty if valid)
        """
        return validate_prompt_order(cls.REQUIRED_PROMPT_ORDER, cls.__name__)

    @classmethod
    def _ensure_prompt_order_valid(cls) -> None:
        """
        Runtime validation hook for prompt order invariants.

        Raises:
            ValueError if REQUIRED_PROMPT_ORDER violates invariants.
        """
        if cls._prompt_order_validated:
            return

        errors = cls.validate_prompt_order()
        if errors:
            logging_util.error(
                "Invalid REQUIRED_PROMPT_ORDER for %s: %s", cls.__name__, errors
            )
            raise ValueError(
                f"Invalid REQUIRED_PROMPT_ORDER for {cls.__name__}: "
                + "; ".join(errors)
            )

        cls._prompt_order_validated = True

    def prompt_order(self) -> tuple[str, ...]:
        """
        Return the ordered prompt types for this agent.

        Override in subclasses if dynamic ordering is needed.
        Default returns the class-level REQUIRED_PROMPT_ORDER.

        Returns:
            Ordered tuple of prompt type constants
        """
        return self.REQUIRED_PROMPT_ORDER

    def builder_flags(self) -> dict[str, bool]:
        """
        Return builder configuration flags for this agent.

        Override in subclasses to customize builder behavior.
        Default: no debug instructions.

        Returns:
            Dict with builder flags (include_debug, etc.)
        """
        return {"include_debug": False}

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(mode={self.MODE}, required={len(self.REQUIRED_PROMPTS)}, optional={len(self.OPTIONAL_PROMPTS)})"


class FixedPromptAgent(BaseAgent):
    """
    Base class for agents with a fixed prompt set.

    Provides a default build_system_instructions() that uses build_for_agent(),
    eliminating the need for `del unused_params` patterns in subclasses.

    Subclasses only need to:
    - Define REQUIRED_PROMPT_ORDER (inherited from BaseAgent)
    - Override builder_flags() if they need debug instructions
    - Override finalize_with_world() if they need world content

    This simplifies agents that don't use selected_prompts, turn_number,
    or other dynamic parameters.
    """

    # Whether this agent should include world content in finalized instructions
    INCLUDE_WORLD_CONTENT: bool = False

    def build_system_instructions(
        self,
        selected_prompts: list[str] | None = None,
        use_default_world: bool = False,
        include_continuation_reminder: bool = True,
        turn_number: int = 0,
        llm_requested_sections: list[str] | None = None,
    ) -> str:
        """
        Build system instructions using the fixed prompt set.

        This default implementation ignores dynamic parameters and builds
        instructions using the agent's REQUIRED_PROMPT_ORDER and builder_flags().

        Subclasses can override if they need dynamic behavior.
        """
        # Use build_for_agent for consistent instruction building
        parts = self._prompt_builder.build_for_agent(self)

        # Finalize with world content based on class setting
        return self._prompt_builder.finalize_instructions(
            parts, use_default_world=self.INCLUDE_WORLD_CONTENT
        )


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

    # Required prompts - ordered tuple (source of truth for loading order)
    # Order: master → game_state → planning_protocol → dnd_srd
    REQUIRED_PROMPT_ORDER: tuple[str, ...] = (
        constants.PROMPT_TYPE_MASTER_DIRECTIVE,
        constants.PROMPT_TYPE_GAME_STATE,
        constants.PROMPT_TYPE_PLANNING_PROTOCOL,  # Planning block schema
        constants.PROMPT_TYPE_DND_SRD,
    )
    REQUIRED_PROMPTS: frozenset[str] = frozenset(REQUIRED_PROMPT_ORDER)

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

    def builder_flags(self) -> dict[str, bool]:
        """Story mode includes debug instructions."""
        return {"include_debug": True}

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


class GodModeAgent(FixedPromptAgent):
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

    # Required prompts - ordered tuple (source of truth for loading order)
    # Order: master → god_mode → game_state → planning_protocol → dnd_srd → mechanics
    REQUIRED_PROMPT_ORDER: tuple[str, ...] = (
        constants.PROMPT_TYPE_MASTER_DIRECTIVE,
        constants.PROMPT_TYPE_GOD_MODE,
        constants.PROMPT_TYPE_GAME_STATE,
        constants.PROMPT_TYPE_PLANNING_PROTOCOL,  # Canonical planning block schema
        constants.PROMPT_TYPE_DND_SRD,
        constants.PROMPT_TYPE_MECHANICS,
    )
    REQUIRED_PROMPTS: frozenset[str] = frozenset(REQUIRED_PROMPT_ORDER)

    # No optional prompts for god mode - it's focused on administration
    OPTIONAL_PROMPTS: frozenset[str] = frozenset()

    MODE: str = constants.MODE_GOD

    # Uses FixedPromptAgent.build_system_instructions() - no del patterns needed

    @classmethod
    def matches_input(cls, user_input: str, mode: str | None = None) -> bool:
        """
        God mode is triggered by "GOD MODE:" prefix OR mode="god" parameter.

        Uses constants.is_god_mode() for centralized detection logic.

        Args:
            user_input: Raw user input text
            mode: Optional mode parameter from request (e.g., "god", "character")

        Returns:
            True if god mode should be activated (via prefix or mode param)
        """
        return constants.is_god_mode(user_input, mode)

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


class PlanningAgent(FixedPromptAgent):
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

    # Required prompts - ordered tuple (source of truth for loading order)
    # Order: master → think → game_state → planning_protocol → dnd_srd
    REQUIRED_PROMPT_ORDER: tuple[str, ...] = (
        constants.PROMPT_TYPE_MASTER_DIRECTIVE,
        constants.PROMPT_TYPE_THINK,
        constants.PROMPT_TYPE_GAME_STATE,
        constants.PROMPT_TYPE_PLANNING_PROTOCOL,  # Planning block schema (canonical)
        constants.PROMPT_TYPE_DND_SRD,
    )
    REQUIRED_PROMPTS: frozenset[str] = frozenset(REQUIRED_PROMPT_ORDER)

    # No optional prompts for think mode - it's focused on planning
    OPTIONAL_PROMPTS: frozenset[str] = frozenset()

    MODE: str = constants.MODE_THINK

    # Uses FixedPromptAgent.build_system_instructions() - no del patterns needed

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


class InfoAgent(FixedPromptAgent):
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

    # Required prompts - ordered tuple (TRIMMED for focus)
    # Order: master → game_state → planning_protocol
    REQUIRED_PROMPT_ORDER: tuple[str, ...] = (
        constants.PROMPT_TYPE_MASTER_DIRECTIVE,
        constants.PROMPT_TYPE_GAME_STATE,  # Contains Equipment Query Protocol
        constants.PROMPT_TYPE_PLANNING_PROTOCOL,  # Canonical planning block schema
    )
    REQUIRED_PROMPTS: frozenset[str] = frozenset(REQUIRED_PROMPT_ORDER)

    # No optional prompts - keep it focused
    OPTIONAL_PROMPTS: frozenset[str] = frozenset()

    MODE: str = constants.MODE_INFO

    # Info mode doesn't need world lore - keep focused on equipment/inventory
    INCLUDE_WORLD_CONTENT: bool = False

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

    # Required prompts - ordered tuple (source of truth for loading order)
    # Order: master → game_state → planning_protocol → combat → narrative → dnd_srd → mechanics
    REQUIRED_PROMPT_ORDER: tuple[str, ...] = (
        constants.PROMPT_TYPE_MASTER_DIRECTIVE,
        constants.PROMPT_TYPE_GAME_STATE,
        constants.PROMPT_TYPE_PLANNING_PROTOCOL,  # Canonical planning block schema
        constants.PROMPT_TYPE_COMBAT,
        constants.PROMPT_TYPE_NARRATIVE,  # For DM Note protocol and cinematic style
        constants.PROMPT_TYPE_DND_SRD,
        constants.PROMPT_TYPE_MECHANICS,
    )
    REQUIRED_PROMPTS: frozenset[str] = frozenset(REQUIRED_PROMPT_ORDER)

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

        Uses build_from_order() with REQUIRED_PROMPT_ORDER to enforce invariants,
        then finalizes with optional world content for combat in specific locations.

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

        # Use build_from_order() with REQUIRED_PROMPT_ORDER to enforce invariants
        # This ensures prompts are loaded in the validated order with debug included
        parts: list[str] = builder.build_from_order(
            self.REQUIRED_PROMPT_ORDER, include_debug=True
        )

        # Finalize with optional world instructions (for combat in specific locations)
        return builder.finalize_instructions(parts, use_default_world=use_default_world)

    def builder_flags(self) -> dict[str, bool]:
        """Combat mode includes debug instructions for combat logging."""
        return {"include_debug": True}

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


class RewardsAgent(FixedPromptAgent):
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

    # Required prompts - ordered tuple (source of truth for loading order)
    # Order: master → game_state → planning_protocol → rewards → dnd_srd → mechanics
    REQUIRED_PROMPT_ORDER: tuple[str, ...] = (
        constants.PROMPT_TYPE_MASTER_DIRECTIVE,
        constants.PROMPT_TYPE_GAME_STATE,
        constants.PROMPT_TYPE_PLANNING_PROTOCOL,  # Canonical planning block schema
        constants.PROMPT_TYPE_REWARDS,
        constants.PROMPT_TYPE_DND_SRD,
        constants.PROMPT_TYPE_MECHANICS,
    )
    REQUIRED_PROMPTS: frozenset[str] = frozenset(REQUIRED_PROMPT_ORDER)

    # No optional prompts for rewards mode - focused on reward processing
    OPTIONAL_PROMPTS: frozenset[str] = frozenset()

    MODE: str = constants.MODE_REWARDS

    # Rewards mode doesn't need world lore - focused on reward processing
    INCLUDE_WORLD_CONTENT: bool = False

    def builder_flags(self) -> dict[str, bool]:
        """Rewards mode includes debug instructions for reward processing logging."""
        return {"include_debug": True}

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
    1. GodModeAgent if input starts with "GOD MODE:" OR mode="god" (highest priority)
    2. PlanningAgent if input starts with "THINK:" or mode is "think" (strategic planning)
    3. InfoAgent for pure info queries (equipment, inventory, stats)
    4. CombatAgent if game_state.combat_state.in_combat is True
    5. RewardsAgent if rewards are pending (combat end, encounter completion)
    6. StoryModeAgent for all other inputs (default)

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
    # Uses centralized constants.is_god_mode() via GodModeAgent.matches_input()
    if GodModeAgent.matches_input(user_input, mode):
        logging_util.info("🔮 GOD_MODE_DETECTED: Using GodModeAgent")
        return GodModeAgent(game_state)

    # Priority 2: Think mode for strategic planning (higher than all non-god modes)
    # Supports both THINK: prefix and explicit mode="think" from API clients
    if PlanningAgent.matches_input(user_input, mode):
        logging_util.info("🧠 THINK_MODE_DETECTED: Using PlanningAgent")
        return PlanningAgent(game_state)

    # Priority 3: Info queries (equipment, inventory, stats) - trimmed prompts
    if InfoAgent.matches_input(user_input):
        logging_util.info("📦 INFO_QUERY_DETECTED: Using InfoAgent (trimmed prompts)")
        return InfoAgent(game_state)

    # Priority 4: Combat mode when in active combat
    if CombatAgent.matches_game_state(game_state):
        logging_util.info("⚔️ COMBAT_MODE_ACTIVE: Using CombatAgent")
        return CombatAgent(game_state)

    # Priority 5: Rewards mode when rewards are pending
    if RewardsAgent.matches_game_state(game_state):
        logging_util.info("🏆 REWARDS_MODE_ACTIVE: Using RewardsAgent")
        return RewardsAgent(game_state)

    # Priority 6: Default to story mode
    return StoryModeAgent(game_state)


# ============================================================================
# ALL AGENT CLASSES (for validation)
# ============================================================================
ALL_AGENT_CLASSES: tuple[type[BaseAgent], ...] = (
    StoryModeAgent,
    GodModeAgent,
    PlanningAgent,
    InfoAgent,
    CombatAgent,
    RewardsAgent,
)


def validate_all_agent_prompt_orders() -> dict[str, list[str]]:
    """
    Validate prompt order invariants for all agent classes.

    Returns:
        Dict mapping agent class names to their validation errors.
        Empty dict means all agents are valid.
    """
    errors = {}
    for agent_cls in ALL_AGENT_CLASSES:
        agent_errors = agent_cls.validate_prompt_order()
        if agent_errors:
            errors[agent_cls.__name__] = agent_errors
    return errors


# Export all public classes and functions
__all__ = [
    "BaseAgent",
    "StoryModeAgent",
    "GodModeAgent",
    "PlanningAgent",
    "InfoAgent",
    "CombatAgent",
    "RewardsAgent",
    "get_agent_for_input",
    "validate_prompt_order",
    "validate_all_agent_prompt_orders",
    "ALL_AGENT_CLASSES",
    "MANDATORY_FIRST_PROMPT",
    "GAME_STATE_PLANNING_PAIR",
]
