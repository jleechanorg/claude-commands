"""
Shared constants used across multiple services in the application.
This prevents cyclical dependencies and keeps key values consistent.
"""

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
FILENAME_SRD = "5e_SRD_All.md"

# --- PROMPT TYPES ---
# Used as keys/identifiers for loading specific prompt content.
PROMPT_TYPE_NARRATIVE = "narrative"
PROMPT_TYPE_MECHANICS = "mechanics"
PROMPT_TYPE_CALIBRATION = "calibration"
PROMPT_TYPE_DESTINY = "destiny_ruleset"
PROMPT_TYPE_GAME_STATE = "game_state"
PROMPT_TYPE_SRD = "srd"
PROMPT_TYPE_CHARACTER_TEMPLATE = "character_template"

# --- Firestore Document Keys & Fields ---
# ... existing code ...