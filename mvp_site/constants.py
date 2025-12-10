"""
Shared constants used across multiple services in the application.
This prevents cyclical dependencies and keeps key values consistent.
"""

import os

# --- ACTORS ---
# Used to identify the source of a story entry
ACTOR_USER = "user"
ACTOR_GEMINI = "gemini"
ACTOR_UNKNOWN = "NO_ACTOR"  # Default when actor is missing from data


# --- SETTINGS ---
# Provider selection
LLM_PROVIDER_GEMINI = "gemini"
LLM_PROVIDER_OPENROUTER = "openrouter"
LLM_PROVIDER_CEREBRAS = "cerebras"

DEFAULT_LLM_PROVIDER = LLM_PROVIDER_GEMINI
ALLOWED_LLM_PROVIDERS = [
    LLM_PROVIDER_GEMINI,
    LLM_PROVIDER_OPENROUTER,
    LLM_PROVIDER_CEREBRAS,
]

# Gemini defaults - using 2.0-flash for cost efficiency ($0.10/M input, ~$0.40/M output)
# Gemini 3 Pro is ~20x more expensive on input ($2.00/M) and reserved for premium users only
DEFAULT_GEMINI_MODEL = "gemini-2.0-flash"

# Premium model for allowlisted users only (expensive: $2-4/M input, $12-18/M output)
GEMINI_PREMIUM_MODEL = "gemini-3-pro-preview"

# Users allowed to access Gemini 3 Pro (expensive model)
# These users can select gemini-3-pro-preview in settings
GEMINI_3_ALLOWED_USERS = [
    "jleechan@gmail.com",
    "jleechantest@gmail.com",
]

# Allowed Gemini model selections for user preferences (default - all users)
# NOTE: Only models that support BOTH code_execution AND JSON response mode are allowed
# Gemini 2.5 models are EXCLUDED - they don't support code_execution + JSON mode together
# See PR #2052 for compatibility testing details
ALLOWED_GEMINI_MODELS = [
    DEFAULT_GEMINI_MODEL,  # ✅ WORKS with code_execution + JSON (cheap: $0.10/M)
    GEMINI_PREMIUM_MODEL,  # ✅ Premium option (allowlist enforced downstream)
]

# Premium Gemini models (only for GEMINI_3_ALLOWED_USERS)
PREMIUM_GEMINI_MODELS = [
    GEMINI_PREMIUM_MODEL,  # ✅ WORKS with code_execution + JSON (expensive: $2-4/M)
]

# Gemini model mapping from user preference to full model name
GEMINI_MODEL_MAPPING = {
    "gemini-3-pro-preview": "gemini-3-pro-preview",
    "gemini-2.0-flash": "gemini-2.0-flash",
    # Legacy compatibility - redirect 2.5 users to cost-efficient model
    "gemini-2.5-flash": "gemini-2.0-flash",  # Auto-redirect to compatible (cheaper)
    "gemini-2.5-pro": "gemini-2.0-flash",  # Auto-redirect to compatible (cheaper)
    "pro-2.5": "gemini-2.0-flash",  # Auto-redirect to compatible (cheaper)
    "flash-2.5": "gemini-2.0-flash",  # Auto-redirect to compatible (cheaper)
}

# OpenRouter model selection tuned for narrative-heavy D&D play
DEFAULT_OPENROUTER_MODEL = "meta-llama/llama-3.1-70b-instruct"
ALLOWED_OPENROUTER_MODELS = [
    DEFAULT_OPENROUTER_MODEL,
    "meta-llama/llama-3.1-405b-instruct",  # 131K context, long campaigns
    "z-ai/glm-4.6",  # 200K context, fast tools
    "x-ai/grok-4.1-fast",  # 2M context, $0.20/$0.50 per M tokens (supports json_schema)
]

# Cerebras direct provider defaults (per Cerebras docs as of 2025-12-03)
# Pricing comparison (input/output per M tokens):
#   Llama 3.1 8B: $0.10/$0.10 (CHEAPEST, not in list - too small for RPG campaigns)
#   GPT OSS 120B: $0.35/$0.75 (not in list - good budget option)
#   Qwen 3 32B: $0.40/$0.80 (not in list - lower context)
#   Qwen 3 235B: $0.60/$1.20 (highest context 131K) <- DEFAULT
#   Llama 3.3 70B: $0.85/$1.20 (65K context)
#   ZAI GLM 4.6: $2.25/$2.75 (preview, 131K context)
DEFAULT_CEREBRAS_MODEL = "qwen-3-235b-a22b-instruct-2507"
ALLOWED_CEREBRAS_MODELS = [
    DEFAULT_CEREBRAS_MODEL,  # 131K context, $0.60/$1.20 per M
    "zai-glm-4.6",  # 131K context, $2.25/$2.75 per M (preview)
    "llama-3.3-70b",  # 65K context, $0.85/$1.20 per M
]

# Context window budgeting (tokens)
DEFAULT_CONTEXT_WINDOW_TOKENS = 128_000
CONTEXT_WINDOW_SAFETY_RATIO = 0.9
MODEL_CONTEXT_WINDOW_TOKENS = {
    # Gemini
    DEFAULT_GEMINI_MODEL: 1_000_000,
    "gemini-2.0-flash": 1_000_000,
    # OpenRouter
    "meta-llama/llama-3.1-70b-instruct": 131_072,
    "meta-llama/llama-3.1-405b-instruct": 131_072,
    "z-ai/glm-4.6": 200_000,
    "x-ai/grok-4.1-fast": 2_000_000,  # Grok 4.1 Fast - 2M context
    "x-ai/grok-4.1-fast:free": 2_000_000,  # Free tier shares same window
    # Cerebras
    "qwen-3-235b-a22b-instruct-2507": 131_072,  # Highest context on Cerebras
    "zai-glm-4.6": 131_072,
    "llama-3.3-70b": 65_536,
}

# Provider/model-specific max output tokens (conservative to avoid API 400s)
# Values pulled from provider docs as of 2025-12-01.
MODEL_MAX_OUTPUT_TOKENS = {
    # Gemini (we cap at JSON_MODE_MAX_OUTPUT_TOKENS in code; keep for completeness)
    DEFAULT_GEMINI_MODEL: 50_000,
    "gemini-2.0-flash": 50_000,
    # OpenRouter
    # Llama 3.1 caps are not reported in the model catalog; OpenRouter commonly limits
    # completion tokens to ~8k for these models, so we adopt 8,192 to avoid 400s while
    # still allowing larger replies than the previous 4k cap.
    "meta-llama/llama-3.1-70b-instruct": 8_192,
    "meta-llama/llama-3.1-405b-instruct": 8_192,
    # Pulled from OpenRouter model metadata (2025-12-01 curl https://openrouter.ai/api/v1/models)
    "z-ai/glm-4.6": 202_752,
    "x-ai/grok-4.1-fast": 30_000,
    # Cerebras (actual limit ~64K, using conservative 32K for safety)
    "qwen-3-235b-a22b-instruct-2507": 32_000,
    "zai-glm-4.6": 32_000,
    "llama-3.3-70b": 32_000,
}

# Debug mode settings
DEFAULT_DEBUG_MODE = True
ALLOWED_DEBUG_MODE_VALUES = [True, False]


# --- INTERACTION MODES ---
# Used to determine the style of user input and AI response
MODE_CHARACTER = "character"
MODE_GOD = "god"

# Mode switching detection phrases
MODE_SWITCH_PHRASES = [
    "god mode",
    "dm mode",
    "gm mode",
    "enter dm mode",
    "enter god mode",
]


# --- VERIFICATION ---
# Write-then-read verification retry settings
VERIFICATION_MAX_ATTEMPTS = 3
VERIFICATION_INITIAL_DELAY = 0.1  # seconds
VERIFICATION_DELAY_INCREMENT = 0.2  # seconds per attempt
MODE_SWITCH_SIMPLE = ["god mode", "god", "dm mode", "dm"]


# --- DICTIONARY KEYS ---
# Used in request/response payloads and when passing data between services
KEY_ACTOR = "actor"
KEY_MODE = "mode"
KEY_TEXT = "text"
KEY_TITLE = "title"
KEY_FORMAT = "format"

# --- STRUCTURED FIELDS ---
# Used for AI response structured data fields
FIELD_SESSION_HEADER = "session_header"
FIELD_PLANNING_BLOCK = "planning_block"
FIELD_DICE_ROLLS = "dice_rolls"
FIELD_RESOURCES = "resources"
FIELD_DEBUG_INFO = "debug_info"
FIELD_GOD_MODE_RESPONSE = "god_mode_response"
KEY_USER_INPUT = "user_input"
KEY_SELECTED_PROMPTS = "selected_prompts"

# --- NEW: Character attribute keys ---
KEY_MBTI = "mbti"

# --- ATTRIBUTE SYSTEMS ---
# Used to determine which attribute system a campaign uses
ATTRIBUTE_SYSTEM_DND = "D&D"

# D&D Attribute System
DND_ATTRIBUTES = [
    "Strength",
    "Dexterity",
    "Constitution",
    "Intelligence",
    "Wisdom",
    "Charisma",
]

DND_ATTRIBUTE_CODES = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]


# Default attribute system for new campaigns
DEFAULT_ATTRIBUTE_SYSTEM = ATTRIBUTE_SYSTEM_DND


# Helper functions for attribute system validation
def get_attributes_for_system(system):
    """Get the list of attributes for the given system."""
    if system == ATTRIBUTE_SYSTEM_DND:
        return DND_ATTRIBUTES.copy()
    # Default to D&D for unknown systems
    return DND_ATTRIBUTES.copy()


def get_attribute_codes_for_system(system):
    """Get the list of attribute codes for the given system."""
    if system == ATTRIBUTE_SYSTEM_DND:
        return DND_ATTRIBUTE_CODES.copy()
    # Default to D&D for unknown systems
    return DND_ATTRIBUTE_CODES.copy()


def uses_charisma(system):
    """Check if the given system uses Charisma attribute."""
    return system == ATTRIBUTE_SYSTEM_DND


def uses_big_five(system):
    """Check if the given system uses Big Five personality traits for social mechanics."""
    del system  # Unused argument - no current systems use Big Five
    return False  # No current systems use Big Five


def infer_provider_from_model(model_name: str, provider_hint: str | None = None) -> str:
    """Infer the LLM provider from a model name.

    This function automatically determines which provider should be used based on
    the model name provided. This is critical for settings updates where the frontend
    only sends the model name without the provider.

    Args:
        model_name: The model name (e.g., "gemini-2.0-flash", "meta-llama/llama-3.1-70b-instruct")
        provider_hint: Optional provider hint to respect when model_name is unknown

    Returns:
        str: The provider name ("gemini", "openrouter", or "cerebras")

    Examples:
        >>> infer_provider_from_model("gemini-2.0-flash")
        "gemini"
        >>> infer_provider_from_model("meta-llama/llama-3.1-70b-instruct")
        "openrouter"
        >>> infer_provider_from_model("qwen-3-235b-a22b-instruct-2507")
        "cerebras"
        >>> infer_provider_from_model("custom-openrouter-model", provider_hint="openrouter")
        "openrouter"
    """
    # Check if model is in Gemini models list
    if model_name in ALLOWED_GEMINI_MODELS or model_name in GEMINI_MODEL_MAPPING:
        return LLM_PROVIDER_GEMINI

    # Check if model is in OpenRouter models list
    if model_name in ALLOWED_OPENROUTER_MODELS:
        return LLM_PROVIDER_OPENROUTER

    # Check if model is in Cerebras models list
    if model_name in ALLOWED_CEREBRAS_MODELS:
        return LLM_PROVIDER_CEREBRAS

    if provider_hint in {LLM_PROVIDER_GEMINI, LLM_PROVIDER_OPENROUTER, LLM_PROVIDER_CEREBRAS}:
        return provider_hint

    # Default to gemini if model not recognized (safe default)
    return DEFAULT_LLM_PROVIDER


# --- EXPORT FORMATS ---
FORMAT_PDF = "pdf"
FORMAT_DOCX = "docx"
FORMAT_TXT = "txt"
MIMETYPE_PDF = "application/pdf"
MIMETYPE_DOCX = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)
MIMETYPE_TXT = "text/plain"


# --- PROMPT FILENAMES ---
FILENAME_NARRATIVE = "narrative_system_instruction.md"
FILENAME_MECHANICS = "mechanics_system_instruction.md"
FILENAME_GAME_STATE = "game_state_instruction.md"
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
PROMPT_TYPE_MASTER_DIRECTIVE = "master_directive"
PROMPT_TYPE_DND_SRD = "dnd_srd"


# --- PROMPT PATHS ---
PROMPTS_DIR = "prompts"
NARRATIVE_SYSTEM_INSTRUCTION_PATH = os.path.join(
    PROMPTS_DIR, "narrative_system_instruction.md"
)
MECHANICS_SYSTEM_INSTRUCTION_PATH = os.path.join(
    PROMPTS_DIR, "mechanics_system_instruction.md"
)
CHARACTER_TEMPLATE_PATH = os.path.join(PROMPTS_DIR, "character_template.md")
GAME_STATE_INSTRUCTION_PATH = os.path.join(PROMPTS_DIR, "game_state_instruction.md")
MASTER_DIRECTIVE_PATH = os.path.join(PROMPTS_DIR, "master_directive.md")
DND_SRD_INSTRUCTION_PATH = os.path.join(PROMPTS_DIR, "dnd_srd_instruction.md")

# --- PROMPT LOADING ORDER ---
# User-selectable prompts that are conditionally added based on campaign settings
# These are loaded in this specific order when selected
USER_SELECTABLE_PROMPTS = [PROMPT_TYPE_NARRATIVE, PROMPT_TYPE_MECHANICS]

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

🚨 MANDATORY CAMPAIGN LAUNCH SUMMARY: After character approval, you MUST display the CAMPAIGN LAUNCH SUMMARY showing:
- Character details and mechanics choices made
- Campaign setting and world details
- Available companions (if enabled)
- Starting location and campaign theme
This summary helps players see their choices before the story begins.
""".strip()

# Legacy alias for backwards compatibility with tests
CHARACTER_CREATION_REMINDER = CHARACTER_DESIGN_REMINDER
