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


# --- DICTIONARY KEYS ---
# Used in request/response payloads and when passing data between services
KEY_ACTOR = 'actor'
KEY_MODE = 'mode'
KEY_TEXT = 'text'
KEY_TITLE = 'title'
KEY_FORMAT = 'format'
KEY_USER_INPUT = "user_input"
KEY_SELECTED_PROMPTS = "selected_prompts"

# --- NEW: Character attribute keys ---
KEY_MBTI = "mbti"

# --- ATTRIBUTE SYSTEMS ---
# Used to determine which attribute system a campaign uses
ATTRIBUTE_SYSTEM_DND = "D&D"
ATTRIBUTE_SYSTEM_DESTINY = "Destiny"

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

# Destiny Attribute System
DESTINY_ATTRIBUTES = [
    "Physique",
    "Coordination",
    "Health", 
    "Intelligence",
    "Wisdom"
]

# Note: Destiny uses Big Five personality traits instead of Charisma
BIG_FIVE_TRAITS = [
    "Openness",
    "Conscientiousness", 
    "Extraversion",
    "Agreeableness",
    "Neuroticism"
]

# Default attribute system for new campaigns
DEFAULT_ATTRIBUTE_SYSTEM = ATTRIBUTE_SYSTEM_DND

# Helper functions for attribute system validation
def is_valid_attribute_system(system):
    """Check if the given system is a valid attribute system."""
    return system in [ATTRIBUTE_SYSTEM_DND, ATTRIBUTE_SYSTEM_DESTINY]

def get_attributes_for_system(system):
    """Get the list of attributes for the given system."""
    if system == ATTRIBUTE_SYSTEM_DND:
        return DND_ATTRIBUTES.copy()
    elif system == ATTRIBUTE_SYSTEM_DESTINY:
        return DESTINY_ATTRIBUTES.copy()
    else:
        raise ValueError(f"Unknown attribute system: {system}")

def get_attribute_codes_for_system(system):
    """Get the list of attribute codes for the given system."""
    if system == ATTRIBUTE_SYSTEM_DND:
        return DND_ATTRIBUTE_CODES.copy()
    elif system == ATTRIBUTE_SYSTEM_DESTINY:
        # Destiny doesn't use abbreviated codes, return full names
        return DESTINY_ATTRIBUTES.copy()
    else:
        raise ValueError(f"Unknown attribute system: {system}")

def uses_charisma(system):
    """Check if the given system uses Charisma attribute."""
    return system == ATTRIBUTE_SYSTEM_DND

def uses_big_five(system):
    """Check if the given system uses Big Five personality traits for social mechanics."""
    return system == ATTRIBUTE_SYSTEM_DESTINY

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
FILENAME_CALIBRATION = "calibration_instruction.md"
FILENAME_DESTINY = "destiny_ruleset.md"
FILENAME_GAME_STATE = "game_state_instruction.md"
FILENAME_ENTITY_SCHEMA = "entity_schema_instruction.md"
FILENAME_DUAL_SYSTEM_REFERENCE = "dual_system_quick_reference.md"
FILENAME_MASTER_DIRECTIVE = "master_directive.md"
FILENAME_ATTRIBUTE_CONVERSION = "attribute_conversion_guide.md"

# --- PROMPT TYPES ---
# Used as keys/identifiers for loading specific prompt content.
PROMPT_TYPE_NARRATIVE = "narrative"
PROMPT_TYPE_MECHANICS = "mechanics"
PROMPT_TYPE_CALIBRATION = "calibration"
PROMPT_TYPE_DESTINY = "destiny_ruleset"
PROMPT_TYPE_GAME_STATE = "game_state"
PROMPT_TYPE_CHARACTER_TEMPLATE = "character_template"
PROMPT_TYPE_CHARACTER_SHEET = "character_sheet"
PROMPT_TYPE_ENTITY_SCHEMA = "entity_schema"
PROMPT_TYPE_DUAL_SYSTEM_REFERENCE = "dual_system_reference"
PROMPT_TYPE_MASTER_DIRECTIVE = "master_directive"
PROMPT_TYPE_ATTRIBUTE_CONVERSION = "attribute_conversion"

# --- PROMPT PATHS ---
PROMPTS_DIR = "prompts"
NARRATIVE_SYSTEM_INSTRUCTION_PATH = os.path.join(PROMPTS_DIR, "narrative_system_instruction.md")
MECHANICS_SYSTEM_INSTRUCTION_PATH = os.path.join(PROMPTS_DIR, "mechanics_system_instruction.md")
CHARACTER_TEMPLATE_PATH = os.path.join(PROMPTS_DIR, "character_template.md")
CHARACTER_SHEET_TEMPLATE_PATH = os.path.join(PROMPTS_DIR, "character_sheet_template.md")
GAME_STATE_INSTRUCTION_PATH = os.path.join(PROMPTS_DIR, "game_state_instruction.md")
CALIBRATION_INSTRUCTION_PATH = os.path.join(PROMPTS_DIR, "calibration_instruction.md")

# Game mechanics
DESTINY_RULESET_PATH = os.path.join(PROMPTS_DIR, "destiny_ruleset.md")

# Entity management
ENTITY_SCHEMA_INSTRUCTION_PATH = os.path.join(PROMPTS_DIR, "entity_schema_instruction.md")

# Additional prompts
DUAL_SYSTEM_REFERENCE_PATH = os.path.join(PROMPTS_DIR, "dual_system_quick_reference.md")
MASTER_DIRECTIVE_PATH = os.path.join(PROMPTS_DIR, "master_directive.md")
ATTRIBUTE_CONVERSION_PATH = os.path.join(PROMPTS_DIR, "attribute_conversion_guide.md")

# --- PROMPT LOADING ORDER ---
# User-selectable prompts that are conditionally added based on campaign settings
# These are loaded in this specific order when selected
USER_SELECTABLE_PROMPTS = [
    PROMPT_TYPE_NARRATIVE,
    PROMPT_TYPE_MECHANICS, 
    PROMPT_TYPE_CALIBRATION
]
