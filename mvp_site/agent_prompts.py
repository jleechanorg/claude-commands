"""
Prompt building utilities for agent-based system instructions.

This module centralizes ALL prompt manipulation code for the application:
- System instruction loading and caching
- Continuation prompt building
- Reprompt message construction
- Temporal correction prompts
- Static prompt parts generation
- Current turn prompt formatting

llm_service and world_logic delegate prompt construction here,
focusing on request/response orchestration instead.
"""

import json
import os
import re
from typing import TYPE_CHECKING, Any

from mvp_site import constants, dice_integrity, logging_util
from mvp_site.file_cache import read_file_cached
from mvp_site.game_state import GameState
from mvp_site.memory_utils import format_memories_for_prompt, select_memories_by_budget
from mvp_site.narrative_response_schema import (
    CHOICE_SCHEMA,
    PLANNING_BLOCK_SCHEMA,
    VALID_CONFIDENCE_LEVELS,
    VALID_QUALITY_TIERS,
    VALID_RISK_LEVELS,
)
from mvp_site.world_loader import load_world_content_for_system_instruction
from mvp_site.world_time import format_world_time_for_prompt

if TYPE_CHECKING:
    from mvp_site.agents import BaseAgent

# Word count target for standard story continuations
TARGET_WORD_COUNT: int = 300

# NEW: Centralized map of prompt types to their file paths.
# This is now the single source of truth for locating prompt files.
PATH_MAP: dict[str, str] = {
    constants.PROMPT_TYPE_NARRATIVE: constants.NARRATIVE_SYSTEM_INSTRUCTION_PATH,
    constants.PROMPT_TYPE_MECHANICS: constants.MECHANICS_SYSTEM_INSTRUCTION_PATH,
    constants.PROMPT_TYPE_GAME_STATE: constants.GAME_STATE_INSTRUCTION_PATH,
    constants.PROMPT_TYPE_CHARACTER_TEMPLATE: constants.CHARACTER_TEMPLATE_PATH,
    # constants.PROMPT_TYPE_ENTITY_SCHEMA: constants.ENTITY_SCHEMA_INSTRUCTION_PATH, # Integrated into game_state
    constants.PROMPT_TYPE_MASTER_DIRECTIVE: constants.MASTER_DIRECTIVE_PATH,
    constants.PROMPT_TYPE_DND_SRD: constants.DND_SRD_INSTRUCTION_PATH,
    constants.PROMPT_TYPE_GOD_MODE: constants.GOD_MODE_INSTRUCTION_PATH,
    constants.PROMPT_TYPE_LIVING_WORLD: constants.LIVING_WORLD_INSTRUCTION_PATH,
    constants.PROMPT_TYPE_COMBAT: constants.COMBAT_SYSTEM_INSTRUCTION_PATH,
    constants.PROMPT_TYPE_REWARDS: constants.REWARDS_SYSTEM_INSTRUCTION_PATH,
    constants.PROMPT_TYPE_RELATIONSHIP: constants.RELATIONSHIP_INSTRUCTION_PATH,
    constants.PROMPT_TYPE_REPUTATION: constants.REPUTATION_INSTRUCTION_PATH,
    constants.PROMPT_TYPE_THINK: constants.THINK_MODE_INSTRUCTION_PATH,
    constants.PROMPT_TYPE_PLANNING_PROTOCOL: constants.PLANNING_PROTOCOL_PATH,
}

# Store loaded instruction content in a dictionary for easy access
_loaded_instructions_cache: dict[str, str] = {}

# Track which instruction files were loaded in the current request (for evidence)
_current_request_loaded_files: list[str] = []


def clear_loaded_files_tracking() -> None:
    """Clear the loaded files tracking list. Call at start of each request."""
    global _current_request_loaded_files  # noqa: PLW0603
    _current_request_loaded_files = []


def get_loaded_instruction_files() -> list[str]:
    """Get the list of instruction files loaded in the current request."""
    return _current_request_loaded_files.copy()


def _schema_to_json_string(schema: dict) -> str:
    """
    Convert a schema dict with Python types to a JSON-friendly string representation.

    The schema uses Python types (str, int, list, dict) as placeholders.
    This converts them to human-readable type names for prompts.
    """

    def convert_value(v: Any) -> Any:
        if v is str:
            mapped = "string"
        elif v is int:
            mapped = "integer"
        elif v is list:
            mapped = "array"
        elif v is dict:
            mapped = "object"
        elif isinstance(v, dict):
            mapped = {k: convert_value(vv) for k, vv in v.items()}
        elif isinstance(v, list):
            mapped = [convert_value(item) for item in v]
        else:
            mapped = v

        return mapped

    converted = convert_value(schema)
    return json.dumps(converted, indent=2)


def _inject_schema_placeholders(content: str) -> str:
    """
    Inject canonical schema definitions into prompt content.

    Replaces placeholders with actual schema JSON from narrative_response_schema.py.
    This ensures prompts and validation code use the same schema definitions.

    Supported placeholders:
    - {{PLANNING_BLOCK_SCHEMA}} - Full planning block structure
    - {{CHOICE_SCHEMA}} - Choice structure within planning blocks
    - {{VALID_RISK_LEVELS}} - Valid risk level values
    - {{VALID_CONFIDENCE_LEVELS}} - Valid confidence level values
    - {{VALID_QUALITY_TIERS}} - Valid quality tier values
    """
    if "{{" not in content:
        return content

    # Build schema JSON representations (convert Python types to strings)
    replacements = {
        "{{PLANNING_BLOCK_SCHEMA}}": _schema_to_json_string(PLANNING_BLOCK_SCHEMA),
        "{{CHOICE_SCHEMA}}": _schema_to_json_string(CHOICE_SCHEMA),
        "{{VALID_RISK_LEVELS}}": json.dumps(sorted(VALID_RISK_LEVELS)),
        "{{VALID_CONFIDENCE_LEVELS}}": json.dumps(sorted(VALID_CONFIDENCE_LEVELS)),
        "{{VALID_QUALITY_TIERS}}": json.dumps(sorted(VALID_QUALITY_TIERS)),
    }

    for placeholder, value in replacements.items():
        if placeholder in content:
            content = content.replace(placeholder, value)
            logging_util.debug(f"Injected {placeholder} into prompt")

    return content


def _load_instruction_file(instruction_type: str) -> str:
    """
    Loads a prompt instruction file from the 'prompts' directory.
    This function is now strict: it will raise an exception if a file
    cannot be found, ensuring the application does not continue with
    incomplete instructions.
    """
    if instruction_type not in _loaded_instructions_cache:
        relative_path = PATH_MAP.get(instruction_type)

        if not relative_path:
            logging_util.error(
                f"FATAL: Unknown instruction type requested: {instruction_type}"
            )
            raise ValueError(f"Unknown instruction type requested: {instruction_type}")

        file_path = os.path.join(os.path.dirname(__file__), relative_path)

        try:
            content = read_file_cached(file_path).strip()
            # Apply schema injection to replace placeholders with canonical schemas
            content = _inject_schema_placeholders(content)
            _loaded_instructions_cache[instruction_type] = content
        except FileNotFoundError:
            logging_util.error(
                f"CRITICAL: System instruction file not found: {file_path}. This is a fatal error for this request."
            )
            raise
        except Exception as e:
            logging_util.error(
                f"CRITICAL: Error loading system instruction file {file_path}: {e}"
            )
            raise

    # Track which files are loaded for evidence (only add if not already tracked)
    relative_path = PATH_MAP.get(instruction_type)
    if relative_path and relative_path not in _current_request_loaded_files:
        _current_request_loaded_files.append(relative_path)

    return _loaded_instructions_cache[instruction_type]


def _extract_essentials(content: str) -> str:
    """Extract the ESSENTIALS block from instruction content.

    The instruction files include a concise, token-optimized block wrapped
    between `<!-- ESSENTIALS ...` and `/ESSENTIALS -->`. This parser confines
    the opening match to the end of the marker line and captures only the inner
    block to avoid stripping content. If no block is present, it returns a
    trimmed prefix to keep token usage bounded.
    """

    essentials_match = re.search(
        r"<!--\s*ESSENTIALS[^\n]*\n(.*?)\n\s*/ESSENTIALS\s*-->",
        content,
        re.DOTALL,
    )

    if essentials_match:
        return essentials_match.group(1).strip()

    # Fallback: return a trimmed prefix for files without an ESSENTIALS block
    # so token-constrained modes still receive a concise summary.
    return content[:2000].strip()


# Map section names to their prompt types for conditional loading
SECTION_TO_PROMPT_TYPE: dict[str, str] = {
    "relationships": constants.PROMPT_TYPE_RELATIONSHIP,
    "reputation": constants.PROMPT_TYPE_REPUTATION,
}


def load_detailed_sections(requested_sections: list[str]) -> str:
    """
    Load detailed instruction sections based on LLM hints from previous turn.

    Args:
        requested_sections: List of section names like ["relationships", "reputation"]

    Returns:
        Combined detailed sections as a string
    """
    if not requested_sections:
        return ""

    parts = []
    for section in requested_sections:
        prompt_type = SECTION_TO_PROMPT_TYPE.get(section)
        if prompt_type:
            try:
                content = _load_instruction_file(prompt_type)
                parts.append(f"\n--- {section.upper()} MECHANICS ---\n")
                parts.append(content)
            except (FileNotFoundError, ValueError) as e:
                logging_util.warning(f"Could not load section {section}: {e}")

    return "\n".join(parts)


def extract_llm_instruction_hints(llm_response: dict[str, Any]) -> list[str]:
    """
    Extract instruction hints from an LLM response's debug_info.meta field.

    The LLM can signal that it needs detailed instructions for the next turn
    by including: {"debug_info": {"meta": {"needs_detailed_instructions": ["relationships"]}}}

    Args:
        llm_response: The parsed JSON response from the LLM

    Returns:
        List of requested section names, or empty list if none requested
    """
    if not isinstance(llm_response, dict):
        return []

    # Look for meta inside debug_info (as documented in game_state_instruction.md)
    debug_info = llm_response.get("debug_info", {})
    if not isinstance(debug_info, dict):
        return []

    meta = debug_info.get("meta", {})
    if not isinstance(meta, dict):
        return []

    hints = meta.get("needs_detailed_instructions", [])
    if not isinstance(hints, list):
        return []

    # Validate hint values (only sections currently supported by detailed loaders)
    valid_hints = set(SECTION_TO_PROMPT_TYPE.keys())
    return [h for h in hints if isinstance(h, str) and h in valid_hints]


def _add_world_instructions_to_system(system_instruction_parts: list[str]) -> None:
    """
    Add world content instructions to system instruction parts if world is enabled.
    Avoids code duplication between get_initial_story and continue_story.
    """

    world_instruction = (
        "\n**CRITICAL INSTRUCTION: USE ESTABLISHED WORLD LORE**\n"
        "This campaign MUST use the Celestial Wars/Assiah world setting provided below. "
        "DO NOT create new factions, characters, or locations - USE the established ones from the world content. "
        "ACTIVELY reference characters, factions, and locations from the provided lore. "
        "The Celestial Wars Alexiel Book takes precedence over World of Assiah documentation for conflicts. "
        "When introducing NPCs or factions, draw from the established character dossiers and faction information. "
        "DO NOT invent generic fantasy elements when rich, detailed lore is provided.\n\n"
    )
    system_instruction_parts.append(world_instruction)

    # Load world content directly into system instruction
    world_content = load_world_content_for_system_instruction()
    system_instruction_parts.append(world_content)


def _build_debug_instructions() -> str:
    """
    Build the debug mode instructions that are always included for game state management.
    The backend will strip debug content for users when debug_mode is False.

    Returns:
        str: The formatted debug instruction string
    """
    return (
        "\n**DEBUG MODE - ALWAYS GENERATE**\n"
        "You must ALWAYS include the following debug information in your response for game state management:\n"
        "\n"
        "1. **DM COMMENTARY**: Wrap any behind-the-scenes DM thoughts, rule considerations, or meta-game commentary in [DEBUG_START] and [DEBUG_END] tags.\n"
        "\n"
        "2. **DICE ROLLS**: Show ALL dice rolls throughout your response:\n"
        "   - **During Narrative**: Show important rolls (skill checks, saving throws, random events) using [DEBUG_ROLL_START] and [DEBUG_ROLL_END] tags\n"
        "   - **During Combat**: Show ALL combat rolls including attack rolls, damage rolls, initiative, saving throws, and any other dice mechanics\n"
        "   - Format: [DEBUG_ROLL_START]Rolling Perception check: 1d20+3 = 15+3 = 18 vs DC 15 (Success)[DEBUG_ROLL_END]\n"
        "   - Include both the dice result and the final total with modifiers, **and always state the DC/target you rolled against** (e.g., 'vs DC 15' or 'vs AC 17')\n"
        "\n"
        "3. **RESOURCES USED**: Track resources expended during the scene:\n"
        "   - Format: [DEBUG_RESOURCES_START]Resources: 1 HD used (2/3 remaining), 1 spell slot level 2 (2/3 remaining), short rests: 1/2[DEBUG_RESOURCES_END]\n"
        "   - Include: Hit Dice (HD), spell slots by level, class features (ki points, rage, etc.), consumables, exhaustion\n"
        "   - Show both used and remaining for each resource\n"
        "\n"
        "4. **STATE CHANGES**: After your main narrative, include a section wrapped in [DEBUG_STATE_START] and [DEBUG_STATE_END] tags that explains what state changes you're proposing and why.\n"
        "\n"
        "**Examples:**\n"
        "- [DEBUG_START]The player is attempting a stealth approach, so I need to roll for the guards' perception...[DEBUG_END]\n"
        "- [DEBUG_ROLL_START]Guard Perception: 1d20+2 = 12+2 = 14 vs DC 15 (Failure - guards don't notice)[DEBUG_ROLL_END]\n"
        "- [DEBUG_RESOURCES_START]Resources: 0 HD used (3/3 remaining), no spell slots used, short rests: 2/2[DEBUG_RESOURCES_END]\n"
        "- [DEBUG_STATE_START]Updating player position to 'hidden behind crates' and setting guard alertness to 'unaware'[DEBUG_STATE_END]\n"
        "\n"
        "NOTE: This debug information helps maintain game state consistency and will be conditionally shown to players based on their debug mode setting.\n\n"
    )


class PromptBuilder:
    """
    Encapsulates prompt building logic for the Gemini service.

    This class is responsible for constructing comprehensive system instructions
    that guide the AI's behavior as a digital D&D Game Master. It manages the
    complex hierarchy of instructions and ensures proper ordering and integration.

    Key Responsibilities:
    - Build core system instructions in proper precedence order
    - Add character-related instructions conditionally
    - Include selected prompt types (narrative, mechanics)
    - Add system reference instructions (D&D SRD)
    - Generate companion and background summary instructions
    - Manage world content integration
    - Ensure debug instructions are properly included

    Instruction Hierarchy (in order of loading):
    1. Master directive (establishes authority)
    2. Game state instructions (data structure compliance)
    3. Planning protocol (canonical planning_block schema)
    4. Debug instructions (technical functionality)
    5. Character template (conditional)
    6. Selected prompts (narrative/mechanics)
    7. System references (D&D SRD)
    8. World content (conditional)

    The class ensures that instructions are loaded in the correct order to
    prevent "instruction fatigue" and maintain proper AI behavior hierarchy.
    """

    def __init__(self, game_state: GameState | None = None) -> None:
        """
        Initialize the PromptBuilder.

        Args:
            game_state (GameState, optional): GameState object used for dynamic
                instruction generation, companion lists, and story summaries.
                If None, static fallback instructions will be used.
        """
        self.game_state = game_state

    def _append_game_state_with_planning(self, parts: list[str]) -> None:
        """Append game_state plus planning_protocol in a single, centralized step."""
        # Load game_state instruction first (highest authority after master directive)
        parts.append(_load_instruction_file(constants.PROMPT_TYPE_GAME_STATE))
        # Load planning protocol immediately after game_state to anchor schema references
        parts.append(_load_instruction_file(constants.PROMPT_TYPE_PLANNING_PROTOCOL))

    def build_from_order(
        self,
        prompt_order: tuple[str, ...],
        *,
        include_debug: bool = False,
    ) -> list[str]:
        """
        Build system instructions from an ordered tuple of prompt types.

        This is the generic builder that replaces mode-specific builders.
        It loads prompts in the exact order specified, with special handling
        for the game_state + planning_protocol consecutive pair.

        Args:
            prompt_order: Ordered tuple of prompt types to load
            include_debug: Whether to append debug instructions at the end

        Returns:
            List of instruction parts in the specified order
        """
        parts: list[str] = []
        skip_next = False

        for i, prompt_type in enumerate(prompt_order):
            if skip_next:
                skip_next = False
                continue

            # Special handling: game_state and planning_protocol must load together
            if prompt_type == constants.PROMPT_TYPE_GAME_STATE:
                # Verify next is planning_protocol (invariant from Phase 0)
                if (
                    i + 1 < len(prompt_order)
                    and prompt_order[i + 1] == constants.PROMPT_TYPE_PLANNING_PROTOCOL
                ):
                    self._append_game_state_with_planning(parts)
                    skip_next = True
                else:
                    # Fallback: load individually (shouldn't happen with valid orders)
                    parts.append(_load_instruction_file(prompt_type))
            elif prompt_type == constants.PROMPT_TYPE_PLANNING_PROTOCOL:
                # Should have been handled with game_state above
                # Load individually as fallback
                parts.append(_load_instruction_file(prompt_type))
            else:
                # Standard prompt loading
                parts.append(_load_instruction_file(prompt_type))

        # Optionally append debug instructions
        if include_debug:
            parts.append(_build_debug_instructions())

        return parts

    def build_for_agent(self, agent: "BaseAgent") -> list[str]:
        """
        Build system instructions for a given agent using its prompt order and flags.

        This is the single entry point for prompt building (Phase 3).
        It delegates to build_from_order() with the agent's configuration.

        Args:
            agent: The agent instance to build instructions for

        Returns:
            List of instruction parts in the agent's specified order
        """
        # Import here to avoid circular imports
        from mvp_site.agents import BaseAgent

        if not isinstance(agent, BaseAgent):
            raise TypeError(f"Expected BaseAgent, got {type(agent).__name__}")

        prompt_order = agent.prompt_order()
        flags = agent.builder_flags()

        return self.build_from_order(
            prompt_order,
            include_debug=flags.get("include_debug", False),
        )

    def build_core_system_instructions(self) -> list[str]:
        """
        Build the core system instructions that are always loaded first.
        Returns a list of instruction parts.
        """
        parts = []

        # CRITICAL: Load master directive FIRST to establish hierarchy and authority
        # This must come before all other instructions to set the precedence rules
        parts.append(_load_instruction_file(constants.PROMPT_TYPE_MASTER_DIRECTIVE))

        # Load game_state + planning protocol together (single entry point)
        self._append_game_state_with_planning(parts)

        # Add debug mode instructions THIRD for technical functionality
        # The backend will strip debug content for users when debug_mode is False
        parts.append(_build_debug_instructions())

        return parts

    def build_god_mode_instructions(self) -> list[str]:
        """
        Build system instructions for GOD MODE.
        God mode is for administrative control (correcting mistakes, modifying campaign),
        NOT for playing the game. Includes game rules knowledge for proper corrections.
        """
        parts = []

        # CRITICAL: Load master directive FIRST to establish hierarchy and authority
        parts.append(_load_instruction_file(constants.PROMPT_TYPE_MASTER_DIRECTIVE))

        # Load god mode specific instruction (administrative commands)
        parts.append(_load_instruction_file(constants.PROMPT_TYPE_GOD_MODE))

        # Load game_state + planning protocol together (single entry point)
        # God mode can still emit planning blocks for structured choices.
        self._append_game_state_with_planning(parts)

        # Load D&D SRD for game rules knowledge
        # (AI needs to understand game mechanics to make proper corrections)
        parts.append(_load_instruction_file(constants.PROMPT_TYPE_DND_SRD))

        # Load mechanics instruction for detailed game rules
        # (spell slots, class features, combat rules, etc.)
        parts.append(_load_instruction_file(constants.PROMPT_TYPE_MECHANICS))

        return parts

    def build_info_mode_instructions(self) -> list[str]:
        """
        Build TRIMMED system instructions for INFO MODE.
        Info mode is for pure information queries (equipment, inventory, stats).
        Uses minimal prompts to maximize LLM focus on Equipment Query Protocol.

        Note: NO narrative, mechanics, or combat prompts - keeps system instruction
        under ~1100 lines vs ~2000 lines for story mode, improving LLM compliance.
        The actual game state JSON is added by llm_service when building the prompt.
        """
        parts = []

        # CRITICAL: Load master directive FIRST to establish hierarchy and authority
        parts.append(_load_instruction_file(constants.PROMPT_TYPE_MASTER_DIRECTIVE))

        # Load game_state + planning protocol together (single entry point)
        # Info mode still returns planning_block per game_state_instruction.md
        self._append_game_state_with_planning(parts)

        return parts

    def build_combat_mode_instructions(self) -> list[str]:
        """
        Build system instructions for COMBAT MODE.
        Combat mode is for active combat encounters with focused tactical prompts.
        Emphasizes: dice rolls, initiative, combat rewards, boss equipment.
        """
        parts = []

        # CRITICAL: Load master directive FIRST to establish hierarchy and authority
        parts.append(_load_instruction_file(constants.PROMPT_TYPE_MASTER_DIRECTIVE))

        # Load game_state + planning protocol together (single entry point)
        self._append_game_state_with_planning(parts)

        # Load combat-specific instruction (tactical combat management)
        # (References game_state schema for combat_state updates)
        parts.append(_load_instruction_file(constants.PROMPT_TYPE_COMBAT))

        # Load narrative instruction for DM Note protocol and cinematic style
        # (Enables out-of-character communication during combat)
        parts.append(_load_instruction_file(constants.PROMPT_TYPE_NARRATIVE))

        # Load D&D SRD for combat rules
        # (Attack rolls, saving throws, damage, conditions)
        parts.append(_load_instruction_file(constants.PROMPT_TYPE_DND_SRD))

        # Load mechanics instruction for detailed combat mechanics
        # (Initiative, action economy, combat XP, etc.)
        parts.append(_load_instruction_file(constants.PROMPT_TYPE_MECHANICS))

        # Add debug instructions for combat logging
        parts.append(_build_debug_instructions())

        return parts

    def build_rewards_mode_instructions(self) -> list[str]:
        """
        Build system instructions for REWARDS MODE.
        Rewards mode handles XP, loot, and level-up processing from any source:
        - Combat victories (when combat_phase == "ended")
        - Non-combat encounters (heists, social victories, stealth)
        - Quest completions
        - Milestone achievements
        """
        parts = []

        # CRITICAL: Load master directive FIRST to establish hierarchy and authority
        parts.append(_load_instruction_file(constants.PROMPT_TYPE_MASTER_DIRECTIVE))

        # Load game_state + planning protocol together (single entry point)
        self._append_game_state_with_planning(parts)

        # Load rewards-specific instruction (XP, loot, level-up rules)
        parts.append(_load_instruction_file(constants.PROMPT_TYPE_REWARDS))

        # Load D&D SRD for XP thresholds and level rules
        parts.append(_load_instruction_file(constants.PROMPT_TYPE_DND_SRD))

        # Load mechanics instruction for detailed level-up mechanics
        parts.append(_load_instruction_file(constants.PROMPT_TYPE_MECHANICS))

        # Add debug instructions for reward processing logging
        parts.append(_build_debug_instructions())

        return parts

    def build_think_mode_instructions(self) -> list[str]:
        """
        Build system instructions for THINK MODE.
        Think mode is for strategic planning and tactical analysis without
        narrative advancement. Time only advances by 1 microsecond.

        Uses a focused prompt set for deep planning operations:
        - Master directive (authority)
        - Think mode instruction (planning behavior)
        - Game state instruction (state structure reference)
        - D&D SRD (game rules knowledge for informed planning)
        """
        parts = []

        # CRITICAL: Load master directive FIRST to establish hierarchy and authority
        parts.append(_load_instruction_file(constants.PROMPT_TYPE_MASTER_DIRECTIVE))

        # Load think mode specific instruction (planning/thinking behavior)
        parts.append(_load_instruction_file(constants.PROMPT_TYPE_THINK))

        # Load game_state + planning protocol together (single entry point)
        self._append_game_state_with_planning(parts)

        # Load D&D SRD for game rules knowledge
        # (AI needs to understand game mechanics for strategic planning)
        parts.append(_load_instruction_file(constants.PROMPT_TYPE_DND_SRD))

        return parts

    def add_character_instructions(
        self, parts: list[str], selected_prompts: list[str]
    ) -> None:
        """
        Conditionally add character-related instructions based on selected prompts.
        """
        # Conditionally add the character template if narrative instructions are selected
        if constants.PROMPT_TYPE_NARRATIVE in selected_prompts:
            parts.append(
                _load_instruction_file(constants.PROMPT_TYPE_CHARACTER_TEMPLATE)
            )

    def add_selected_prompt_instructions(
        self,
        parts: list[str],
        selected_prompts: list[str],
        llm_requested_sections: list[str] | None = None,
        essentials_only: bool = False,
    ) -> None:
        """
        Add instructions for selected prompt types in consistent order.

        Args:
            parts: List to append instruction parts to
            selected_prompts: List of prompt types to include
            llm_requested_sections: Sections the LLM requested via meta.needs_detailed_instructions
            essentials_only: When True, append detailed sections (for token-constrained mode).
                When False, assume the full narrative prompt already contains these sections
                and avoid duplicating them.
        """
        # Define the order for consistency (calibration archived)
        prompt_order = [
            constants.PROMPT_TYPE_NARRATIVE,
            constants.PROMPT_TYPE_MECHANICS,
        ]

        # Add in order
        for p_type in prompt_order:
            if p_type in selected_prompts:
                content = _load_instruction_file(p_type)
                parts.append(
                    _extract_essentials(content) if essentials_only else content
                )

        # Append detailed sections based on mode and LLM requests
        if essentials_only:
            # ESSENTIALS mode: Always load detailed sections (either LLM-requested or all)
            if llm_requested_sections:
                requested = llm_requested_sections
            elif constants.PROMPT_TYPE_NARRATIVE in selected_prompts:
                requested = list(SECTION_TO_PROMPT_TYPE.keys())
            else:
                requested = []

            detailed_content = load_detailed_sections(requested)
            if detailed_content:
                parts.append(detailed_content)
        elif llm_requested_sections:
            # NON-ESSENTIALS (Story Mode): Load ONLY LLM-requested detailed sections
            # This enables dynamic prompt loading where the LLM can request specific
            # sections (e.g., relationships, reputation) for the next turn via
            # debug_info.meta.needs_detailed_instructions.
            # These detailed sections are separate files, not duplicated in narrative.
            detailed_content = load_detailed_sections(llm_requested_sections)
            if detailed_content:
                parts.append(detailed_content)

    def add_system_reference_instructions(self, parts: list[str]) -> None:
        """
        Add system reference instructions that are always included.
        """
        # Always include the D&D SRD instruction (replaces complex dual-system approach)
        parts.append(_load_instruction_file(constants.PROMPT_TYPE_DND_SRD))

    def build_companion_instruction(self) -> str:
        """Build companion instruction text."""

        state: dict[str, Any] | None = None
        if self.game_state is not None:
            if hasattr(self.game_state, "to_dict"):
                state = self.game_state.to_dict()
            elif hasattr(self.game_state, "data"):
                state = self.game_state.data

        companions: dict[str, Any] | None = None
        if isinstance(state, dict):
            companions = state.get("game_state", {}).get("companions")

        if companions and isinstance(companions, dict):
            lines = ["**ACTIVE COMPANIONS**"]
            for name, info in companions.items():
                if not isinstance(info, dict):
                    continue
                cls = info.get("class", "Unknown")
                lines.append(f"- {name} ({cls})")
            return "\n".join(lines)

        # Fallback to static instruction used during initial story generation
        return (
            "\n**SPECIAL INSTRUCTION: COMPANION GENERATION ACTIVATED**\n"
            "You have been specifically requested to generate EXACTLY 3 starting companions for this campaign.\n\n"
            "**MANDATORY REQUIREMENTS:**\n"
            "1. Generate exactly 3 unique companions with diverse party roles (e.g., warrior, healer, scout)\n"
            "2. Each companion MUST have a valid MBTI personality type (e.g., ISTJ, INFP, ESTP)\n"
            "3. Each companion MUST include: name, background story, skills array, personality traits, equipment\n"
            "4. Set relationship field to 'companion' for all generated NPCs\n"
            "5. Include all companions in the npc_data section of your JSON response\n\n"
            "**JSON STRUCTURE EXAMPLE:**\n"
            '"npc_data": {\n'
            '  "Companion Name": {\n'
            '    "mbti": "ISTJ",\n'
            '    "role": "warrior",\n'
            '    "background": "Detailed background story",\n'
            '    "relationship": "companion",\n'
            '    "skills": ["combat", "defense", "weapon mastery"],\n'
            '    "personality_traits": ["loyal", "protective", "methodical"],\n'
            '    "equipment": ["enchanted shield", "battle axe", "chainmail"]\n'
            "  }\n"
            "}\n\n"
            "**VERIFICATION:** Ensure your response contains exactly 3 NPCs with relationship='companion' in npc_data.\n\n"
        )

    def build_background_summary_instruction(self) -> str:
        """Build background summary instruction text."""

        state: dict[str, Any] | None = None
        if self.game_state is not None:
            if hasattr(self.game_state, "to_dict"):
                state = self.game_state.to_dict()
            elif hasattr(self.game_state, "data"):
                state = self.game_state.data

        story: dict[str, Any] | None = None
        if isinstance(state, dict):
            story = state.get("game_state", {}).get("story")

        summary: str | None = None
        if isinstance(story, dict):
            summary = story.get("summary")

        if summary:
            return f"**STORY SUMMARY**\n{summary}"

        # Fallback to static background instruction
        return (
            "\n**CRITICAL INSTRUCTION: START WITH BACKGROUND SUMMARY**\n"
            "Before beginning the actual narrative, you MUST provide a background summary section that orients the player. "
            "This should be 2-4 paragraphs covering:\n"
            "1. **World Background:** A brief overview of the setting, key factions, current political situation, and important world elements (without major spoilers)\n"
            "2. **Character History:** Who the character is, their background, motivations, and current situation (based on the prompt provided)\n"
            "3. **Current Context:** What brings them to this moment and why their story is beginning now\n\n"
            "**Requirements:**\n"
            "- Keep it concise but informative (2-4 paragraphs total)\n"
            "- NO future plot spoilers or major story reveals\n"
            "- Focus on established facts the character would know\n"
            "- End with a transition into the opening scene\n"
            "- Use a clear header like '**--- BACKGROUND ---**' to separate this from the main narrative\n\n"
            "After the background summary, proceed with the normal opening scene and narrative.\n\n"
        )

    def build_character_identity_block(self) -> str:  # noqa: PLR0912
        """
        Build character identity block for system prompts.

        This ensures the LLM always has access to immutable character facts
        like name, gender, pronouns, and key relationships, preventing
        misgendering and identity confusion.

        Returns:
            Formatted string block or empty string if no game state
        """
        if not self.game_state:
            return ""

        # Use the GameState method if available
        if hasattr(self.game_state, "get_character_identity_block"):
            return self.game_state.get_character_identity_block()

        # Fallback for dict-based game state
        pc = None
        if hasattr(self.game_state, "player_character_data"):
            pc = self.game_state.player_character_data
        elif isinstance(self.game_state, dict):
            pc = self.game_state.get("player_character_data", {})

        if not pc or not isinstance(pc, dict):
            return ""

        lines = ["## Character Identity (IMMUTABLE)"]

        # Name
        name = pc.get("name")
        if name:
            lines.append(f"- **Name**: {name}")

        # Gender and pronouns - handle None values properly
        gender_raw = pc.get("gender")
        gender = str(gender_raw).lower() if gender_raw else ""
        if gender:
            if gender in ("female", "woman", "f"):
                lines.append("- **Gender**: Female (she/her)")
                lines.append(
                    "- **NEVER** refer to this character as 'he', 'him', "
                    "or use male-gendered familial terms for them"
                )
            elif gender in ("male", "man", "m"):
                lines.append("- **Gender**: Male (he/him)")
                lines.append(
                    "- **NEVER** refer to this character as 'she', 'her', "
                    "or use female-gendered familial terms for them"
                )
            else:
                lines.append(f"- **Gender**: {gender}")

        # Race
        race = pc.get("race")
        if race:
            lines.append(f"- **Race**: {race}")

        # Class
        char_class = pc.get("class") or pc.get("character_class")
        if char_class:
            lines.append(f"- **Class**: {char_class}")

        # Key relationships
        relationships = pc.get("relationships", {})
        if isinstance(relationships, dict) and relationships:
            lines.append("- **Key Relationships**:")
            for rel_name, rel_type in relationships.items():
                lines.append(f"  - {rel_name}: {rel_type}")

        # Parentage (important for characters like Alexiel)
        parentage = pc.get("parentage") or pc.get("parents")
        if parentage:
            if isinstance(parentage, dict):
                for parent_type, parent_name in parentage.items():
                    lines.append(f"- **{parent_type.title()}**: {parent_name}")
            elif isinstance(parentage, str):
                lines.append(f"- **Parentage**: {parentage}")

        if len(lines) == 1:
            return ""  # Only header, no actual data

        return "\n".join(lines)

    def build_god_mode_directives_block(self) -> str:  # noqa: PLR0912, PLR0915
        """
        Build god mode directives block for system prompts.

        These are player-defined rules that persist across sessions
        and MUST be followed by the LLM. Also includes DM notes that
        may contain important context the LLM wrote but didn't formally
        save as directives.

        Directives are shown NEWEST FIRST for precedence - if there are
        conflicting rules, the most recent one takes priority.

        Returns:
            Formatted string block or empty string if no directives
        """
        if not self.game_state:
            return ""

        # Fallback for dict-based game state
        custom_state = None
        debug_info = None
        if hasattr(self.game_state, "custom_campaign_state"):
            custom_state = self.game_state.custom_campaign_state
        elif isinstance(self.game_state, dict):
            custom_state = self.game_state.get("custom_campaign_state", {})

        # Get debug_info for dm_notes
        if hasattr(self.game_state, "debug_info"):
            debug_info = self.game_state.debug_info
        elif isinstance(self.game_state, dict):
            debug_info = self.game_state.get("debug_info", {})

        # Build directives section - sorted NEWEST FIRST for precedence
        base_block = ""
        if custom_state and isinstance(custom_state, dict):
            directives = custom_state.get("god_mode_directives", [])
            if directives:
                # Sort by 'added' timestamp descending (newest first)
                def get_added_ts(d):
                    if isinstance(d, dict):
                        return d.get("added", "")
                    return ""

                sorted_directives = sorted(directives, key=get_added_ts, reverse=True)

                lines = ["## Active God Mode Directives (Newest First)"]
                lines.append(
                    "The following rules were set by the player and MUST be followed."
                )
                lines.append(
                    "In case of conflicts, earlier rules take precedence (newest first):"
                )
                for i, directive in enumerate(sorted_directives, 1):
                    if isinstance(directive, dict):
                        rule = directive.get("rule", str(directive))
                    else:
                        rule = str(directive)
                    lines.append(f"{i}. {rule}")
                base_block = "\n".join(lines)

        # Add DM notes section if present (also newest first - reverse order)
        dm_notes = []
        if debug_info and isinstance(debug_info, dict):
            dm_notes = debug_info.get("dm_notes", [])

        if dm_notes:
            # Prefer timestamp-based ordering if available; otherwise fall back to reverse
            def get_note_added_ts(note: Any) -> str:
                if isinstance(note, dict):
                    return note.get("added", "")
                return ""

            has_timestamped_notes = any(
                isinstance(note, dict) and "added" in note for note in dm_notes
            )

            if has_timestamped_notes:
                ordered_notes = sorted(dm_notes, key=get_note_added_ts, reverse=True)
            else:
                # Maintain previous behavior when no timestamps are present
                ordered_notes = list(reversed(dm_notes))

            dm_lines = ["\n## DM Notes (Context from God Mode, Newest First)"]
            dm_lines.append(
                "These notes were set during God Mode and provide important context."
            )
            dm_lines.append("In case of conflicts, earlier notes take precedence:")

            for note in ordered_notes:
                if isinstance(note, dict):
                    note_text = note.get("note") or note.get("text") or str(note)
                else:
                    note_text = str(note)

                if isinstance(note_text, str):
                    note_text = note_text.strip()

                if note_text:
                    dm_lines.append(f"- {note_text}")

            # Only include the DM notes block if at least one valid note was added
            if len(dm_lines) > 3:
                dm_block = "\n".join(dm_lines)

                if base_block:
                    return base_block + "\n" + dm_block
                return dm_block

            # If no valid notes remain after filtering, fall through to base_block

        return base_block

    def build_continuation_reminder(self) -> str:
        """
        Build reminders for story continuation, especially planning blocks.
        Includes temporal enforcement to prevent backward time jumps.
        """
        # Extract current world_time for temporal enforcement
        world_data = None
        if (
            self.game_state is not None
            and getattr(self.game_state, "world_data", None) is not None
        ):
            world_data = self.game_state.world_data
        world_time = (
            world_data.get("world_time", {}) if isinstance(world_data, dict) else {}
        )
        current_location = (
            world_data.get("current_location_name", "current location")
            if isinstance(world_data, dict)
            else "current location"
        )

        # Format current time for the prompt (including hidden microsecond for uniqueness)
        time_parts = []
        if world_time.get("year"):
            time_parts.append(f"{world_time.get('year')} DR")
        if world_time.get("month"):
            time_parts.append(f"{world_time.get('month')} {world_time.get('day', '')}")
        if world_time.get("hour") is not None:
            try:
                hour = int(world_time.get("hour", 0))
                minute = int(world_time.get("minute", 0))
                second = int(world_time.get("second", 0))
                time_parts.append(f"{hour:02d}:{minute:02d}:{second:02d}")
            except (ValueError, TypeError):
                time_parts.append("00:00:00")  # Fallback for invalid time values
        current_time_str = ", ".join(time_parts) if time_parts else "current timestamp"

        # Include microsecond for precise temporal tracking
        current_microsecond = world_time.get("microsecond", 0)

        temporal_enforcement = (
            f"\n**🚨 TEMPORAL CONSISTENCY ENFORCEMENT**\n"
            f"CURRENT STORY STATE: {current_time_str} at {current_location}\n"
            f"HIDDEN TIMESTAMP: microsecond={current_microsecond} (for think-block uniqueness)\n"
            f"⚠️ TIME BOUNDARY: Your response MUST have a timestamp AFTER {current_time_str}\n"
            f"- DO NOT generate events from before this time\n"
            f"- DO NOT jump backward to earlier scenes or locations\n"
            f"- Focus on the LATEST entries in the TIMELINE LOG (not older ones)\n"
            f"- For THINK/PLAN actions: increment microsecond by +1 (no narrative time advancement)\n"
            f"- For STORY actions: increment by meaningful time units (minutes/hours)\n"
            f"- EXCEPTION: Only GOD MODE commands can move time backward\n\n"
        )

        # Build arc completion reminder to prevent LLM from revisiting completed arcs
        arc_reminder = self.build_arc_completion_reminder()

        return (
            temporal_enforcement
            + arc_reminder
            + "**CRITICAL REMINDER FOR STORY CONTINUATION**\n"
            "1. **MANDATORY PLANNING BLOCK FIELD**: Every STORY MODE response MUST have a `planning_block` field (JSON object) as a SEPARATE top-level field.\n"
            "2. **MANDATORY NARRATIVE FIELD**: Every response MUST have a `narrative` field with story prose. NEVER embed JSON in narrative.\n"
            "3. **FIELD SEPARATION**: `narrative` = prose text ONLY. `planning_block` = JSON object with thinking/choices. NEVER mix them.\n"
            "4. **Think Commands**: If the user says 'think', 'plan', 'consider', 'strategize', or 'options':\n"
            "   - **NARRATIVE FIELD**: Include brief text showing the character pausing to think (e.g., 'You pause to consider your options...')\n"
            "   - **PLANNING_BLOCK FIELD**: Generate deep think block with 'thinking', 'choices', and 'analysis' (pros/cons/confidence)\n"
            "   - **NO ACTIONS**: The character MUST NOT take any story-advancing actions - no combat, dialogue, movement, or decisions\n"
            "5. **Standard Responses**: Include narrative continuation in `narrative` field, planning block in `planning_block` field with 3-4 action options.\n"
            "6. **Never Skip**: Both `narrative` AND `planning_block` fields are MANDATORY - never leave either empty.\n\n"
        )

    def build_arc_completion_reminder(self) -> str:
        """
        Build arc completion reminder to prevent LLM from revisiting completed arcs.

        This prevents timeline confusion where the LLM "forgets" that major
        narrative arcs have concluded and tries to revisit them as in-progress.

        Returns:
            Formatted string with completed arcs summary, or empty string if none.
        """
        if self.game_state is None:
            return ""

        summary = self.game_state.get_completed_arcs_summary()
        if not summary:
            return ""

        return (
            f"\n**🚨 ARC COMPLETION ENFORCEMENT**\n"
            f"{summary}\n"
            f"⚠️ DO NOT revisit these arcs as if they are still in progress.\n"
            f"⚠️ DO NOT reset or regress the status of completed arcs.\n"
            f"⚠️ References to these arcs should acknowledge they are COMPLETE.\n\n"
        )

    def should_include_living_world(self, turn_number: int) -> bool:
        """
        Check if living world instruction should be included based on turn number.

        The living world instruction is included every N turns (configured via
        constants.LIVING_WORLD_TURN_INTERVAL, default 3) to advance world state
        without overwhelming every response.

        Args:
            turn_number: Current turn number (1-indexed)

        Returns:
            True if living world instruction should be included this turn
        """
        if turn_number < 1:
            return False
        return turn_number % constants.LIVING_WORLD_TURN_INTERVAL == 0

    def build_living_world_instruction(self, turn_number: int) -> str:
        """
        Build living world advancement instruction for this turn.

        This instruction triggers the LLM to advance world state for characters,
        factions, and events that are not directly in the player's current scene.
        The world continues to move even when the player isn't watching.

        Args:
            turn_number: Current turn number for context

        Returns:
            Living world instruction with turn context, or empty string if not
            a living world turn.
        """
        if not self.should_include_living_world(turn_number):
            return ""

        # Load the living world instruction file
        base_instruction = _load_instruction_file(constants.PROMPT_TYPE_LIVING_WORLD)

        # Add turn context header
        turn_context = (
            f"\n**🌍 LIVING WORLD TURN {turn_number}**\n"
            f"This is turn {turn_number} - a living world advancement turn.\n"
            f"You MUST generate background world events as specified below.\n\n"
        )

        return turn_context + base_instruction

    def finalize_instructions(
        self, parts: list[str], use_default_world: bool = False
    ) -> str:
        """
        Finalize the system instructions by adding world instructions.
        Returns the complete system instruction string.

        Includes:
        - Character identity block (immutable facts like name, gender, pronouns)
        - God mode directives (player-defined rules that persist across sessions)
        - World instructions (if requested)
        """
        # Add character identity block early (after core instructions)
        # This ensures the LLM always knows immutable character facts
        identity_block = self.build_character_identity_block()
        if identity_block:
            parts.insert(1, identity_block)  # Insert after first (master directive)

        # Add god mode directives (player-defined rules)
        # These MUST be followed by the LLM
        directives_block = self.build_god_mode_directives_block()
        if directives_block:
            # Insert after identity block (or after master directive if no identity)
            insert_pos = 2 if identity_block else 1
            parts.insert(insert_pos, directives_block)

        # Add world instructions if requested
        if use_default_world:
            _add_world_instructions_to_system(parts)

        # Debug instructions already added at the beginning in build_core_system_instructions

        return "\n\n".join(parts)


# =============================================================================
# CENTRALIZED PROMPT BUILDING FUNCTIONS
# =============================================================================
# These functions are centralized here from llm_service.py and world_logic.py
# to ensure all prompt manipulation code lives in one module.


def build_reprompt_for_missing_fields(
    original_response_text: str,
    missing_fields: list[str],
    tool_results: list[dict[str, Any]] | None = None,
    dice_roll_strategy: str | None = None,
) -> str:
    """Build a reprompt message to request missing fields from the LLM.

    When the LLM response is missing required fields (planning_block, session_header,
    dice_rolls, etc.), this function constructs a clear reprompt message explaining
    what's missing and how to provide it.

    Args:
        original_response_text: The original response from the LLM
        missing_fields: List of missing field names
        tool_results: Optional list of tool execution results to include
            in the reprompt. This preserves dice roll provenance when
            reprompting after malformed JSON in Phase 2.
        dice_roll_strategy: Strategy to determine available dice remediation
            (code_execution only vs tool_requests only)

    Returns:
        Reprompt message asking for the missing fields
    """
    if not missing_fields:
        return (
            "Your response was evaluated for required JSON fields, but none were "
            "identified as missing. Please ensure your response conforms to the "
            "expected schema."
        )

    fields_str = " and ".join(missing_fields)

    requested_lines: list[str] = []
    if "planning_block" in missing_fields:
        requested_lines.append(
            "- planning_block: An object with 'thinking' (your GM reasoning) and 'choices' (2-4 player options, each with 'text', 'description', 'risk_level')"
        )
    if "session_header" in missing_fields:
        requested_lines.append(
            "- session_header: A brief session context string (e.g., 'Session 3: The Quest Continues')"
        )
    if "dice_rolls" in missing_fields:
        requested_lines.append(
            "- dice_rolls: A non-empty list of dice roll strings for this turn. In combat actions, you MUST include the rolls and results."
        )
    if "dice_integrity" in missing_fields:
        requested_lines.extend(
            dice_integrity.build_dice_integrity_reprompt_lines(dice_roll_strategy)
        )

    requested_block = "\n".join(requested_lines)

    # Build tool results context if available (preserves dice provenance)
    tool_results_context = ""
    if tool_results:
        tool_lines: list[str] = []
        for tr in tool_results:
            if not isinstance(tr, dict):
                continue
            tool_name = tr.get("tool", "unknown")
            result = tr.get("result", {})
            if isinstance(result, dict):
                total = result.get("total", result.get("result"))
                purpose = tr.get("args", {}).get("purpose", "")
                tool_lines.append(
                    f"  - {tool_name}: {total}" + (f" ({purpose})" if purpose else "")
                )
            else:
                tool_lines.append(f"  - {tool_name}: {result}")
        if tool_lines:
            tool_results_context = (
                "\n\nIMPORTANT - Tool results from prior execution (use these EXACT values, do NOT fabricate):\n"
                + "\n".join(tool_lines)
                + "\n"
            )

    return (
        f"Your response is missing the required {fields_str} field(s). "
        f"Please provide the complete JSON response including:\n{requested_block}\n\n"
        f"Keep the narrative and other fields from your previous response. "
        f"{tool_results_context}"
        f"Here is your previous response for reference:\n{original_response_text[:2000]}"
    )


def get_static_prompt_parts(
    current_game_state: GameState, story_context: list[dict[str, Any]]
) -> tuple[str, str, str]:
    """Helper to generate the non-timeline parts of the prompt.

    This builds the checkpoint block, core memories summary, and sequence ID list
    that provide stable context for story continuation.

    Args:
        current_game_state: The current GameState object
        story_context: List of story entries with sequence_id fields

    Returns:
        tuple: (checkpoint_block, core_memories_summary, sequence_id_list_string)
    """
    sequence_ids = [str(entry.get("sequence_id", "N/A")) for entry in story_context]
    sequence_id_list_string = ", ".join(sequence_ids)
    latest_seq_id = sequence_ids[-1] if sequence_ids else "N/A"

    current_location = current_game_state.world_data.get(
        "current_location_name", "Unknown"
    )

    pc_data: dict[str, Any] = current_game_state.player_character_data
    # The key stats are now generated by the LLM in the [CHARACTER_RESOURCES] block.
    active_missions: list[Any] = current_game_state.custom_campaign_state.get(
        "active_missions", []
    )
    if active_missions:
        # Handle both old style (list of strings) and new style (list of dicts)
        mission_names = []
        for m in active_missions:
            if isinstance(m, dict):
                # For dict format, try to get 'name' field, fallback to 'title' or convert to string
                name = m.get("name") or m.get("title") or str(m)
            else:
                # For string format, use as-is
                name = str(m)
            mission_names.append(name)
        missions_summary = "Missions: " + (
            ", ".join(mission_names) if mission_names else "None"
        )
    else:
        missions_summary = "Missions: None"

    ambition: str | None = pc_data.get("core_ambition")
    milestone: str | None = pc_data.get("next_milestone")
    ambition_summary: str = ""
    if ambition and milestone:
        ambition_summary = f"Ambition: {ambition} | Next Milestone: {milestone}"

    all_core_memories: list[str] = current_game_state.custom_campaign_state.get(
        "core_memories", []
    )
    # Apply token budget to prevent memory overflow
    selected_memories = select_memories_by_budget(all_core_memories)
    core_memories_summary: str = format_memories_for_prompt(selected_memories)

    checkpoint_block: str = (
        f"[CHECKPOINT BLOCK:]\\n"
        f"Sequence ID: {latest_seq_id} | Location: {current_location}\\n"
        f"{missions_summary}\\n"
        f"{ambition_summary}"
    )

    return checkpoint_block, core_memories_summary, sequence_id_list_string


def get_current_turn_prompt(user_input: str, mode: str) -> str:
    """Helper to generate the text for the user's current action.

    This formats the user's input into a proper prompt based on the current mode
    (character mode vs god mode) and detects think/plan commands.

    Args:
        user_input: The user's raw input text
        mode: Either "character" or "god" to determine prompt formatting

    Returns:
        str: Formatted prompt text for the current turn
    """
    if mode == constants.MODE_CHARACTER:
        # Check if user is requesting planning/thinking
        # Note: Thinking detection simplified to avoid hardcoded keyword lists
        user_input_lower = user_input.lower()
        is_think_command = "think" in user_input_lower or "plan" in user_input_lower

        if is_think_command:
            # Emphasize planning for think commands (planning block handled separately in JSON)
            prompt_template = (
                "Main character: {user_input}. Generate the character's internal thoughts and strategic analysis. "
                "NARRATIVE: Write the character's inner thoughts and contemplation as narrative text. "
                "PLANNING: Generate detailed analysis in the planning block with pros/cons for each option. "
                "DO NOT take any physical actions or advance the scene. Focus on mental deliberation only. "
                "CRITICAL: Each choice in the planning block MUST include an 'analysis' field with 'pros' array, 'cons' array, and 'confidence' string."
            )
        else:
            # Standard story continuation (planning block handled separately in JSON)
            prompt_template = (
                "Main character: {user_input}. Continue the story in about {word_count} words and "
                "add details for narrative, descriptions of scenes, character dialog, character emotions."
            )
        return prompt_template.format(
            user_input=user_input, word_count=TARGET_WORD_COUNT
        )
    # god mode (and any non-character mode)
    return f"GOD MODE: {user_input}"


def build_temporal_correction_prompt(
    original_user_input: str,
    old_time: dict[str, Any],
    new_time: dict[str, Any],
    old_location: str | None,
    new_location: str | None,
) -> str:
    """Build correction prompt when temporal violation detected.

    This prompts the LLM to regenerate the ENTIRE response with correct context
    when the story timeline has gone backward (which shouldn't happen).

    Args:
        original_user_input: The original user action that triggered the response
        old_time: The correct current time state (dict with year, month, day, etc.)
        new_time: The invalid time from LLM response that went backward
        old_location: The correct current location
        new_location: The invalid location from LLM response

    Returns:
        str: Formatted correction prompt explaining the violation and how to fix it
    """
    old_time_str = format_world_time_for_prompt(old_time)
    new_time_str = format_world_time_for_prompt(new_time)
    old_loc = old_location or "Unknown location"
    new_loc = new_location or "Unknown location"

    return f"""⚠️ TEMPORAL VIOLATION - FULL REGENERATION REQUIRED

Your previous response was REJECTED because time went BACKWARD:
- CORRECT current state: {old_time_str} at {old_loc}
- YOUR invalid output: {new_time_str} at {new_loc}

🚨 CRITICAL ERROR: You appear to have lost track of the story timeline.

## ROOT CAUSE ANALYSIS
You likely focused on OLDER entries in the TIMELINE LOG instead of the MOST RECENT ones.
This caused you to generate a response for a scene that already happened in the past.

## MANDATORY CORRECTION INSTRUCTIONS

1. **FOCUS ON THE LATEST ENTRIES**: Look at the LAST 2-3 entries in the TIMELINE LOG.
   These represent where the story CURRENTLY is, not where it was earlier.

2. **IDENTIFY THE CURRENT SCENE**: The player is currently at:
   - Time: {old_time_str}
   - Location: {old_loc}
   - This is where you must CONTINUE from.

3. **GENERATE THE NEXT ENTRY**: Your response must continue the story forward.
   - Time MUST be AFTER {old_time_str} (move forward, even if just by minutes)
   - Location should logically follow from {old_loc}
   - Do NOT jump back to earlier scenes or locations

4. **IGNORE YOUR PREVIOUS ATTEMPT**: Your output of "{new_time_str} at {new_loc}" was WRONG.
   Do not use that as a reference.

## PLAYER ACTION TO RESPOND TO:
{original_user_input}

Generate a NEW response that is the NEXT logical entry in the timeline, continuing from the CURRENT state."""


def build_temporal_warning_message(
    temporal_correction_attempts: int,
    max_attempts: int = 3,
) -> str | None:
    """Build user-facing temporal warning text based on attempts taken.

    When temporal corrections are needed, this generates an appropriate
    warning message to inform the user about timeline consistency issues.

    Args:
        temporal_correction_attempts: Number of correction attempts made
        max_attempts: Maximum correction attempts allowed (default 3)

    Returns:
        Warning message string or None if no warning needed
    """
    if temporal_correction_attempts <= 0:
        return None

    # Always surface a warning once at least one correction was attempted.
    # When max_attempts is 0 (corrections disabled), we still emit a warning
    # and treat the effective max as at least one attempt so the message
    # doesn't silently disappear.
    effective_max_attempts = max(1, max_attempts)

    if temporal_correction_attempts > effective_max_attempts:
        return (
            f"⚠️ TEMPORAL CORRECTION EXCEEDED: The AI repeatedly generated responses that jumped "
            f"backward in time. After {temporal_correction_attempts} failed correction attempts "
            f"(configured max {max_attempts}), the system accepted the response "
            f"to avoid infinite loops. Timeline consistency may be compromised."
        )

    return (
        f"⚠️ TEMPORAL CORRECTION: The AI initially generated a response that jumped "
        f"backward in time. {temporal_correction_attempts} correction(s) were required "
        f"to fix the timeline continuity."
    )
