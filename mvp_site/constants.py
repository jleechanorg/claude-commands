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

# Gemini 2.5 Flash model constant
GEMINI_2_5_FLASH = "gemini-2.5-flash"

# Users allowed to access Gemini 3 Pro (expensive model)
# These users can select gemini-3-pro-preview in settings
GEMINI_3_ALLOWED_USERS = [
    "jleechan@gmail.com",
    "jleechantest@gmail.com",
]

# Allowed Gemini model selections for user preferences (default - all users)
# Model capabilities:
#   - gemini-2.0-flash: code_execution + JSON mode together ✅ (true dice randomness)
#   - gemini-3-pro-preview: code_execution + JSON mode together ✅ (premium)
#   - gemini-2.5-flash: JSON mode only, NO code_execution combo (uses precompute dice)
ALLOWED_GEMINI_MODELS = [
    DEFAULT_GEMINI_MODEL,  # ✅ gemini-2.0-flash: code_execution + JSON (cheap: $0.10/M)
    "gemini-2.5-flash",    # ✅ JSON mode only, precompute dice (alternative option)
    GEMINI_PREMIUM_MODEL,  # ✅ gemini-3-pro-preview: code_execution + JSON (allowlist)
]

# Premium Gemini models (only for GEMINI_3_ALLOWED_USERS)
PREMIUM_GEMINI_MODELS = [
    GEMINI_PREMIUM_MODEL,  # ✅ WORKS with code_execution + JSON (expensive: $2-4/M)
]

# Gemini 3.x models - can use code_execution + JSON mode together (single phase)
# All other Gemini models (2.x) require two-phase separation
GEMINI_3_MODELS: set[str] = {
    "gemini-3-pro-preview",
    # Add future Gemini 3 models here as they become available
}

# =============================================================================
# MODEL CAPABILITIES FOR DICE ROLLING
# =============================================================================
# Models that support native code_execution WITH JSON response mode
# These can run Python code (random.randint) directly during inference
#
# GEMINI MODEL BEHAVIOR (as of Dec 2024):
# ┌─────────────────────┬───────────────┬───────────┬──────────────┬───────────────┐
# │ Model               │ Code Exec     │ JSON Mode │ Both Together│ Dice Strategy │
# ├─────────────────────┼───────────────┼───────────┼──────────────┼───────────────┤
# │ gemini-3-pro-preview│ ✅ Yes        │ ✅ Yes    │ ✅ YES       │ code_execution│
# │ gemini-2.0-flash    │ ✅ Yes        │ ✅ Yes    │ ❌ No        │ tool_use_phased│
# │ gemini-2.5-flash    │ ✅ Yes        │ ✅ Yes    │ ❌ No        │ tool_use_phased│
# │ gemini-2.5-pro      │ ✅ Yes        │ ✅ Yes    │ ❌ No        │ tool_use_phased│
# └─────────────────────┴───────────────┴───────────┴──────────────┴───────────────┘
#
# Gemini 3.x: CAN use code_execution + JSON together (single-phase)
# Gemini 2.x: CANNOT use both together - use tool_use with phase separation
#
# ARCHITECTURE (Dec 2024): Tool loops restored for all providers.
# - Gemini 3: Single-phase with code_execution + JSON (model runs Python for dice)
# - Gemini 2.x: Two-phase (tools→JSON phase separation)
# - Cerebras/OpenRouter: Function calling with tool_use
MODELS_WITH_CODE_EXECUTION: set[str] = GEMINI_3_MODELS  # Gemini 3 models support code_execution + JSON

# Models that support tool use / function calling
# These require two-stage inference: LLM requests tool → we execute → send result back
# NOTE: Only add models with 100k+ token context window
# NOTE: llama-3.3-70b does NOT support multi-turn tool calling (uses precompute fallback)
MODELS_WITH_TOOL_USE = {
    # Cerebras models with multi-turn tool support (100k+ context)
    "qwen-3-235b-a22b-instruct-2507",  # 131K context - Confirmed working
    "zai-glm-4.6",  # 131K context - #1 on Berkeley Function Calling Leaderboard (quota limited)
    "gpt-oss-120b",  # 131K context - OpenAI reasoning model with native tool use
    # OpenRouter models with tool support (100k+ context)
    "openai/gpt-oss-120b",  # OpenRouter variant (use provider=openrouter)
    "meta-llama/llama-3.1-70b-instruct",  # 128K context
    # Note: llama-3.1-405b removed (too expensive)
}

# Models that need pre-computed dice rolls (no code_execution or tool_use)
# Fallback: LLM generates dice values (not truly random, but works)
# Any model NOT in the above sets falls back to precompute automatically
# Note: Precompute is "good enough" - LLM just picks plausible dice values
MODELS_PRECOMPUTE_ONLY = {
    # Explicitly list models that should never use tool_use even if capable
    # (empty - all unlisted models auto-fallback to precompute)
}


def get_dice_roll_strategy(model_name: str, provider: str = "") -> str:
    """
    Determine the dice rolling strategy for a given model.

    ARCHITECTURE UPDATE (Dec 2024): Tool loops restored for all providers.
    LLM decides what dice to roll, server executes with true randomness.

    Args:
        model_name: Model identifier
        provider: Provider name (gemini, cerebras, openrouter)

    Returns:
        Strategy string:
        - 'code_execution' - Gemini 3.x: code_execution + JSON together
        - 'tool_use_phased' - Gemini 2.x: tools→JSON phase separation
        - 'tool_use' - Cerebras/OpenRouter: function calling + JSON
        - 'precompute' - Fallback for models without tool support
    """
    # Gemini provider has special handling
    if provider == "gemini":
        if model_name in GEMINI_3_MODELS:
            return "code_execution"  # Single-phase: code_execution + JSON
        return "tool_use_phased"  # Two-phase: tools then JSON

    # Cerebras/OpenRouter models with tool support
    if model_name in MODELS_WITH_TOOL_USE:
        return "tool_use"

    # Fallback: precompute (pre-rolled dice in prompt)
    return "precompute"

# Gemini model mapping from user preference to full model name
# Maps user-selected values to actual API model names
GEMINI_MODEL_MAPPING = {
    # Primary models (selectable in settings)
    "gemini-2.0-flash": "gemini-2.0-flash",      # Default: code_execution + JSON
    "gemini-2.5-flash": "gemini-2.5-flash",      # Alternative: JSON only, precompute dice
    "gemini-3-pro-preview": "gemini-3-pro-preview",  # Premium: code_execution + JSON
    # Legacy aliases (redirect to 2.0 for backwards compatibility)
    "gemini-2.5-pro": "gemini-2.0-flash",  # Redirect: 2.5-pro → 2.0-flash
    "pro-2.5": "gemini-2.0-flash",         # Redirect: legacy alias
    "flash-2.5": "gemini-2.5-flash",       # Alias: maps to actual 2.5-flash
}

# OpenRouter model selection tuned for narrative-heavy D&D play
DEFAULT_OPENROUTER_MODEL = "meta-llama/llama-3.1-70b-instruct"
ALLOWED_OPENROUTER_MODELS = [
    DEFAULT_OPENROUTER_MODEL,
    "meta-llama/llama-3.1-405b-instruct",  # 131K context, long campaigns
    "meta-llama/llama-3.1-8b-instruct",  # 131K context, $0.10/$0.10 per M (Cerebras provider)
    "openai/gpt-oss-120b",  # 131K context, $0.35/$0.75 per M (reasoning model)
    "z-ai/glm-4.6",  # 200K context, fast tools (OpenRouter spelling differs from Cerebras "zai-glm-4.6")
    "x-ai/grok-4.1-fast",  # 2M context, $0.20/$0.50 per M tokens (supports json_schema)
    "x-ai/grok-4.1-fast:free",  # Legacy alias to preserve existing user selections
]

# Cerebras direct provider defaults (per Cerebras docs as of 2025-12-11)
# Pricing comparison (input/output per M tokens):
#   Llama 3.1 8B: $0.10/$0.10 (CHEAPEST - now included)
#   GPT OSS 120B: $0.35/$0.75 (budget option - now included)
#   Qwen 3 32B: $0.40/$0.80 (not in list - lower context)
#   Qwen 3 235B: $0.60/$1.20 (highest context 131K)
#   Llama 3.3 70B: $0.85/$1.20 (65K context)
#   ZAI GLM 4.6: $2.25/$2.75 (preview, 131K context) <- DEFAULT (request: prioritize quality/tools)
# NOTE: Defaulting to GLM 4.6 is a conscious trade-off (higher cost vs. Qwen 235B) to prioritize
# quality/tooling; choose Qwen below for cost-sensitive workloads.
DEFAULT_CEREBRAS_MODEL = "zai-glm-4.6"
ALLOWED_CEREBRAS_MODELS = [
    DEFAULT_CEREBRAS_MODEL,  # 131K context, $2.25/$2.75 per M (default: higher quality/tools, higher cost)
    "qwen-3-235b-a22b-instruct-2507",  # 131K context, $0.60/$1.20 per M (cost-efficient alternative)
    "llama-3.3-70b",  # 65K context, $0.85/$1.20 per M
    "llama-3.1-8b",  # 131K context, $0.10/$0.10 per M (cheapest option)
    "gpt-oss-120b",  # 131K context, $0.35/$0.75 per M (budget reasoning model)
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
    "meta-llama/llama-3.1-8b-instruct": 131_072,  # 131K context
    "openai/gpt-oss-120b": 131_072,  # 131K context
    "z-ai/glm-4.6": 200_000,  # OpenRouter spelling differs from Cerebras "zai-glm-4.6"
    "x-ai/grok-4.1-fast": 2_000_000,  # Grok 4.1 Fast - 2M context
    "x-ai/grok-4.1-fast:free": 2_000_000,  # Free tier shares same window
    # Cerebras
    "qwen-3-235b-a22b-instruct-2507": 131_072,  # Highest context on Cerebras
    "zai-glm-4.6": 131_072,
    # Paid tier supports 128k context; use 128k for budgeting
    "llama-3.3-70b": 128_000,
    "llama-3.1-8b": 131_072,  # 131K context window (Cerebras advertises 128K)
    "gpt-oss-120b": 131_072,  # 131K context window
}

# Provider/model-specific max output tokens (conservative to avoid API 400s)
# Values pulled from provider docs (OpenRouter as of 2025-12-01; Cerebras as of 2025-12-11).
MODEL_MAX_OUTPUT_TOKENS = {
    # Gemini (we cap at JSON_MODE_MAX_OUTPUT_TOKENS in code; keep for completeness)
    DEFAULT_GEMINI_MODEL: 50_000,
    "gemini-2.0-flash": 50_000,
    # OpenRouter
    # Llama 3.1 caps are not reported in the model catalog; OpenRouter commonly limits
    # completion tokens to ~8k for these models, so we adopt 8,192 to avoid 400s while
    # still allowing larger replies than the previous 4k cap. Cerebras-hosted Llama 3.1
    # can safely emit longer replies (see provider-specific entries below).
    "meta-llama/llama-3.1-70b-instruct": 8_192,
    "meta-llama/llama-3.1-405b-instruct": 8_192,
    "meta-llama/llama-3.1-8b-instruct": 8_192,  # Same cap as other Llama 3.1 models
    "openai/gpt-oss-120b": 40_000,  # 40K max output on Cerebras provider
    # Pulled from OpenRouter model metadata (2025-12-01 curl https://openrouter.ai/api/v1/models)
    "z-ai/glm-4.6": 202_752,
    "x-ai/grok-4.1-fast": 30_000,
    "x-ai/grok-4.1-fast:free": 30_000,  # Legacy alias shares the same cap
    # Cerebras (paid tier limits)
    "qwen-3-235b-a22b-instruct-2507": 32_000,
    "zai-glm-4.6": 32_000,
    # Llama 3.3: Paid tier supports up to 65k completion tokens
    "llama-3.3-70b": 65_000,
    "llama-3.1-8b": 32_000,  # Cerebras allows longer completions than OpenRouter
    "gpt-oss-120b": 40_000,  # 40K max output per Cerebras docs
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

    if provider_hint in {
        LLM_PROVIDER_GEMINI,
        LLM_PROVIDER_OPENROUTER,
        LLM_PROVIDER_CEREBRAS,
    }:
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
PROMPT_TYPE_GOD_MODE = "god_mode"


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
GOD_MODE_INSTRUCTION_PATH = os.path.join(PROMPTS_DIR, "god_mode_instruction.md")

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
