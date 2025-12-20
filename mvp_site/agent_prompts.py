"""
Prompt building utilities for agent-based system instructions.

This module centralizes prompt file loading and instruction assembly so
llm_service can focus on request/response orchestration.
"""

import os
from typing import Any

from mvp_site import constants, logging_util
from mvp_site.file_cache import read_file_cached
from mvp_site.game_state import GameState
from mvp_site.world_loader import load_world_content_for_system_instruction

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
}

# Store loaded instruction content in a dictionary for easy access
_loaded_instructions_cache: dict[str, str] = {}


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

    return _loaded_instructions_cache[instruction_type]


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
    3. Debug instructions (technical functionality)
    4. Character template (conditional)
    5. Selected prompts (narrative/mechanics)
    6. System references (D&D SRD)
    7. World content (conditional)

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

    def build_core_system_instructions(self) -> list[str]:
        """
        Build the core system instructions that are always loaded first.
        Returns a list of instruction parts.
        """
        parts = []

        # CRITICAL: Load master directive FIRST to establish hierarchy and authority
        # This must come before all other instructions to set the precedence rules
        parts.append(_load_instruction_file(constants.PROMPT_TYPE_MASTER_DIRECTIVE))

        # CRITICAL: Load game_state instructions SECOND (highest authority per master directive)
        # This prevents "instruction fatigue" and ensures data structure compliance
        # NOTE: Entity schemas are now integrated into game_state_instruction.md for LLM optimization
        parts.append(_load_instruction_file(constants.PROMPT_TYPE_GAME_STATE))

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

        # Load game state instruction for state structure reference
        # (AI needs to know the schema to make valid state_updates)
        parts.append(_load_instruction_file(constants.PROMPT_TYPE_GAME_STATE))

        # Load D&D SRD for game rules knowledge
        # (AI needs to understand game mechanics to make proper corrections)
        parts.append(_load_instruction_file(constants.PROMPT_TYPE_DND_SRD))

        # Load mechanics instruction for detailed game rules
        # (spell slots, class features, combat rules, etc.)
        parts.append(_load_instruction_file(constants.PROMPT_TYPE_MECHANICS))

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
        self, parts: list[str], selected_prompts: list[str]
    ) -> None:
        """
        Add instructions for selected prompt types in consistent order.
        """
        # Define the order for consistency (calibration archived)
        prompt_order = [
            constants.PROMPT_TYPE_NARRATIVE,
            constants.PROMPT_TYPE_MECHANICS,
        ]

        # Add in order
        for p_type in prompt_order:
            if p_type in selected_prompts:
                parts.append(_load_instruction_file(p_type))

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

    def build_continuation_reminder(self) -> str:
        """
        Build reminders for story continuation, especially planning blocks.
        Includes temporal enforcement to prevent backward time jumps.
        """
        # Extract current world_time for temporal enforcement
        world_time = self.game_state.world_data.get("world_time", {}) if (hasattr(self.game_state, "world_data") and self.game_state.world_data) else {}
        current_location = self.game_state.world_data.get("current_location_name", "current location") if (hasattr(self.game_state, "world_data") and self.game_state.world_data) else "current location"

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

        return (
            temporal_enforcement
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

    def finalize_instructions(
        self, parts: list[str], use_default_world: bool = False
    ) -> str:
        """
        Finalize the system instructions by adding world instructions.
        Returns the complete system instruction string.
        """
        # Add world instructions if requested
        if use_default_world:
            _add_world_instructions_to_system(parts)

        # Debug instructions already added at the beginning in build_core_system_instructions

        return "\n\n".join(parts)
