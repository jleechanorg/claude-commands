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