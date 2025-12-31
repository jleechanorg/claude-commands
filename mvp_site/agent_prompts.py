"""
Prompt building utilities for agent-based system instructions.

This module centralizes prompt file loading and instruction assembly so
llm_service can focus on request/response orchestration.
"""

import os
import re
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
    constants.PROMPT_TYPE_LIVING_WORLD: constants.LIVING_WORLD_INSTRUCTION_PATH,
    constants.PROMPT_TYPE_COMBAT: constants.COMBAT_SYSTEM_INSTRUCTION_PATH,
    constants.PROMPT_TYPE_REWARDS: constants.REWARDS_SYSTEM_INSTRUCTION_PATH,
    constants.PROMPT_TYPE_RELATIONSHIP: constants.RELATIONSHIP_INSTRUCTION_PATH,
    constants.PROMPT_TYPE_REPUTATION: constants.REPUTATION_INSTRUCTION_PATH,
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

        # Load game state instruction - contains Equipment Query Protocol
        # This is the key prompt with exact item naming requirements
        parts.append(_load_instruction_file(constants.PROMPT_TYPE_GAME_STATE))

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

        # Load game state instruction SECOND - establishes authoritative state schema
        # (AI needs to know combat_state structure before combat rules)
        parts.append(_load_instruction_file(constants.PROMPT_TYPE_GAME_STATE))

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

        # Load game state instruction SECOND - establishes authoritative state schema
        # (AI needs to know reward/encounter state structure)
        parts.append(_load_instruction_file(constants.PROMPT_TYPE_GAME_STATE))

        # Load rewards-specific instruction (XP, loot, level-up rules)
        parts.append(_load_instruction_file(constants.PROMPT_TYPE_REWARDS))

        # Load D&D SRD for XP thresholds and level rules
        parts.append(_load_instruction_file(constants.PROMPT_TYPE_DND_SRD))

        # Load mechanics instruction for detailed level-up mechanics
        parts.append(_load_instruction_file(constants.PROMPT_TYPE_MECHANICS))

        # Add debug instructions for reward processing logging
        parts.append(_build_debug_instructions())

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

    def build_god_mode_directives_block(self) -> str:
        """
        Build god mode directives block for system prompts.

        These are player-defined rules that persist across sessions
        and MUST be followed by the LLM.

        Returns:
            Formatted string block or empty string if no directives
        """
        if not self.game_state:
            return ""

        # Use the GameState method if available
        if hasattr(self.game_state, "get_god_mode_directives_block"):
            return self.game_state.get_god_mode_directives_block()

        # Fallback for dict-based game state
        custom_state = None
        if hasattr(self.game_state, "custom_campaign_state"):
            custom_state = self.game_state.custom_campaign_state
        elif isinstance(self.game_state, dict):
            custom_state = self.game_state.get("custom_campaign_state", {})

        if not custom_state or not isinstance(custom_state, dict):
            return ""

        directives = custom_state.get("god_mode_directives", [])
        if not directives:
            return ""

        lines = ["## Active God Mode Directives"]
        lines.append("The following rules were set by the player and MUST be followed:")

        for i, directive in enumerate(directives, 1):
            if isinstance(directive, dict):
                rule = directive.get("rule", str(directive))
            else:
                rule = str(directive)
            lines.append(f"{i}. {rule}")

        return "\n".join(lines)

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
