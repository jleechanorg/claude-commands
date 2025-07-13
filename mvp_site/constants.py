"""
Shared constants used across multiple services in the application.
This prevents cyclical dependencies and keeps key values consistent.
"""

import os

# --- ACTORS ---
# Used to identify the source of a story entry
ACTOR_USER = 'user'
ACTOR_GEMINI = 'gemini'


# --- INTERACTION MODES ---
# Used to determine the style of user input and AI response
MODE_CHARACTER = 'character'
MODE_GOD = 'god'

# Mode switching detection phrases
MODE_SWITCH_PHRASES = ['god mode', 'dm mode', 'gm mode', 'enter dm mode', 'enter god mode']
MODE_SWITCH_SIMPLE = ['god mode', 'god', 'dm mode', 'dm']


# --- DICTIONARY KEYS ---
# Used in request/response payloads and when passing data between services
KEY_ACTOR = 'actor'
KEY_MODE = 'mode'
KEY_TEXT = 'text'
KEY_TITLE = 'title'
KEY_FORMAT = 'format'

# --- STRUCTURED FIELDS ---
# Used for AI response structured data fields
FIELD_SESSION_HEADER = 'session_header'
FIELD_PLANNING_BLOCK = 'planning_block'
FIELD_DICE_ROLLS = 'dice_rolls'
FIELD_RESOURCES = 'resources'
FIELD_DEBUG_INFO = 'debug_info'
FIELD_GOD_MODE_RESPONSE = 'god_mode_response'
KEY_USER_INPUT = "user_input"
KEY_SELECTED_PROMPTS = "selected_prompts"

# --- NEW: Character attribute keys ---
KEY_MBTI = "mbti"

# --- ATTRIBUTE SYSTEMS ---
# Used to determine which attribute system a campaign uses
ATTRIBUTE_SYSTEM_DND = "D&D"
# ATTRIBUTE_SYSTEM_DESTINY = "Destiny" # Archived with dual-system files

# D&D Attribute System
DND_ATTRIBUTES = [
    "Strength",
    "Dexterity", 
    "Constitution",
    "Intelligence",
    "Wisdom",
    "Charisma"
]

DND_ATTRIBUTE_CODES = [
    "STR",
    "DEX",
    "CON", 
    "INT",
    "WIS",
    "CHA"
]

# ARCHIVED: Destiny Attribute System (moved to prompt_archive/)
# DESTINY_ATTRIBUTES = [
#     "Physique", "Coordination", "Health", "Intelligence", "Wisdom"
# ]
# BIG_FIVE_TRAITS = [
#     "Openness", "Conscientiousness", "Extraversion", "Agreeableness", "Neuroticism"
# ]

# Default attribute system for new campaigns
DEFAULT_ATTRIBUTE_SYSTEM = ATTRIBUTE_SYSTEM_DND

# Helper functions for attribute system validation
def get_attributes_for_system(system):
    """Get the list of attributes for the given system."""
    if system == ATTRIBUTE_SYSTEM_DND:
        return DND_ATTRIBUTES.copy()
    # elif system == ATTRIBUTE_SYSTEM_DESTINY: # Archived
    #     return DESTINY_ATTRIBUTES.copy()
    else:
        # Default to D&D for unknown systems
        return DND_ATTRIBUTES.copy()

def get_attribute_codes_for_system(system):
    """Get the list of attribute codes for the given system."""
    if system == ATTRIBUTE_SYSTEM_DND:
        return DND_ATTRIBUTE_CODES.copy()
    # elif system == ATTRIBUTE_SYSTEM_DESTINY: # Archived
    #     return DESTINY_ATTRIBUTES.copy()
    else:
        # Default to D&D for unknown systems
        return DND_ATTRIBUTE_CODES.copy()

def uses_charisma(system):
    """Check if the given system uses Charisma attribute."""
    return system == ATTRIBUTE_SYSTEM_DND

def uses_big_five(system):
    """Check if the given system uses Big Five personality traits for social mechanics."""
    # return system == ATTRIBUTE_SYSTEM_DESTINY # Archived
    return False  # No current systems use Big Five

# --- EXPORT FORMATS ---
FORMAT_PDF = 'pdf'
FORMAT_DOCX = 'docx'
FORMAT_TXT = 'txt'
MIMETYPE_PDF = 'application/pdf'
MIMETYPE_DOCX = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
MIMETYPE_TXT = 'text/plain'


# --- PROMPT FILENAMES ---
FILENAME_NARRATIVE = "narrative_system_instruction.md"
FILENAME_MECHANICS = "mechanics_system_instruction.md"
FILENAME_GAME_STATE = "game_state_instruction.md"
# FILENAME_ENTITY_SCHEMA = "entity_schema_instruction.md" # Integrated into game_state_instruction.md
FILENAME_MASTER_DIRECTIVE = "master_directive.md"
FILENAME_DND_SRD = "dnd_srd_instruction.md"
FILENAME_CHARACTER_TEMPLATE = "character_template.md"

# --- ARCHIVED FILENAMES (for reference) ---
# These files have been archived to prompt_archive/ directory:
# FILENAME_CALIBRATION = "calibration_instruction.md" (2,808 words)
# FILENAME_DESTINY = "destiny_ruleset.md" (1,012 words)
# FILENAME_DUAL_SYSTEM_REFERENCE = "dual_system_quick_reference.md" (354 words)
# FILENAME_ATTRIBUTE_CONVERSION = "attribute_conversion_guide.md" (822 words)
# FILENAME_CHARACTER_SHEET = "character_sheet_template.md" (659 words)

# --- PROMPT TYPES ---
# Used as keys/identifiers for loading specific prompt content.
PROMPT_TYPE_NARRATIVE = "narrative"
PROMPT_TYPE_MECHANICS = "mechanics"
PROMPT_TYPE_GAME_STATE = "game_state"
PROMPT_TYPE_CHARACTER_TEMPLATE = "character_template"
# PROMPT_TYPE_ENTITY_SCHEMA = "entity_schema" # Integrated into game_state_instruction.md
PROMPT_TYPE_MASTER_DIRECTIVE = "master_directive"
PROMPT_TYPE_DND_SRD = "dnd_srd"

# --- ARCHIVED PROMPT TYPES (for reference) ---
# These prompt types have been archived:
# PROMPT_TYPE_CALIBRATION = "calibration"
# PROMPT_TYPE_DESTINY = "destiny_ruleset" 
# PROMPT_TYPE_DUAL_SYSTEM_REFERENCE = "dual_system_reference"
# PROMPT_TYPE_ATTRIBUTE_CONVERSION = "attribute_conversion"
# PROMPT_TYPE_CHARACTER_SHEET = "character_sheet"

# --- PROMPT PATHS ---
PROMPTS_DIR = "prompts"
NARRATIVE_SYSTEM_INSTRUCTION_PATH = os.path.join(PROMPTS_DIR, "narrative_system_instruction.md")
MECHANICS_SYSTEM_INSTRUCTION_PATH = os.path.join(PROMPTS_DIR, "mechanics_system_instruction.md")
CHARACTER_TEMPLATE_PATH = os.path.join(PROMPTS_DIR, "character_template.md")
GAME_STATE_INSTRUCTION_PATH = os.path.join(PROMPTS_DIR, "game_state_instruction.md")
# ENTITY_SCHEMA_INSTRUCTION_PATH = os.path.join(PROMPTS_DIR, "entity_schema_instruction.md") # Integrated into game_state
MASTER_DIRECTIVE_PATH = os.path.join(PROMPTS_DIR, "master_directive.md")
DND_SRD_INSTRUCTION_PATH = os.path.join(PROMPTS_DIR, "dnd_srd_instruction.md")

# --- PROMPT LOADING ORDER ---
# User-selectable prompts that are conditionally added based on campaign settings
# These are loaded in this specific order when selected
USER_SELECTABLE_PROMPTS = [
    PROMPT_TYPE_NARRATIVE,
    PROMPT_TYPE_MECHANICS
]

# --- CHARACTER DESIGN ---
# Reminder text injected into initial prompt when mechanics is enabled
CHARACTER_DESIGN_REMINDER = """
🔥 CRITICAL REMINDER: Since mechanics is enabled, you MUST start with character design! 🔥
FIRST: Check if the player has specified a character in their prompt (e.g., "play as Astarion", "I want to be a knight", etc.)
- If YES: Acknowledge their character choice and flesh it out with D&D mechanics following the "When Character is Pre-Specified" protocol
- If NO: Present the standard character design options exactly as specified in the Campaign Initialization section

DO NOT design a character or start the story - work with the player to establish their character first!
IMPORTANT: During character design, numeric responses (1, 2, 3, etc.) are selections from the presented list, NOT story continuation requests.
Use the clean [CHARACTER DESIGN - Step X of 7] format without DM notes or debug blocks.
IMPORTANT: State updates must be included in a JSON field, not in the narrative text.
""".strip()
