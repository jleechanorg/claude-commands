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

# Gemini defaults - using 3-flash-preview for best value ($0.50/M input, $3/M output)
# Gemini 3 Flash: 3x faster than 2.5 Pro, Pro-grade reasoning, 78% SWE-bench Verified
# Gemini 3 Pro is expensive ($2-4/M input, $12-18/M output) and reserved for premium users only
# Can be overridden via WORLDAI_DEFAULT_GEMINI_MODEL env var for testing
DEFAULT_GEMINI_MODEL = os.getenv("WORLDAI_DEFAULT_GEMINI_MODEL", "gemini-3-flash-preview")

# Premium model for allowlisted users only (expensive: $2-4/M input, $12-18/M output)
GEMINI_PREMIUM_MODEL = "gemini-3-pro-preview"

# Users allowed to access Gemini 3 Pro (expensive model)
# These users can select gemini-3-pro-preview in settings
GEMINI_3_ALLOWED_USERS = [
    "jleechan@gmail.com",
    "jleechantest@gmail.com",
]

# Allowed Gemini model selections for user preferences (default - all users).
# NOTE:
# - Gemini 3.x supports code_execution + JSON together (single inference).
# - Gemini 2.0-flash is allowed for backwards compatibility but uses native two-phase
#   tool calling for dice because Gemini 2.x cannot combine code_execution with JSON mode.
ALLOWED_GEMINI_MODELS = [
    DEFAULT_GEMINI_MODEL,  # ✅ Gemini 3 Flash (best value: $0.50/M input, $3/M output)
    "gemini-2.0-flash",  # ✅ Legacy option (native_two_phase dice strategy)
    GEMINI_PREMIUM_MODEL,  # ✅ Premium option (allowlist enforced downstream)
]

# Premium Gemini models (only for GEMINI_3_ALLOWED_USERS)
PREMIUM_GEMINI_MODELS = [
    GEMINI_PREMIUM_MODEL,  # ✅ WORKS with code_execution + JSON (expensive: $2-4/M)
]

# Gemini model mapping from user preference to full model name
# Official docs: https://ai.google.dev/gemini-api/docs/gemini-3
GEMINI_MODEL_MAPPING = {
    # gemini-3-flash-preview: 1M context, 64K output, streaming function calling,
    # Google Search, File Search, Code Execution, URL Context support.
    # Knowledge cutoff: Jan 2025. Can handle 100+ tools simultaneously.
    # Source: https://blog.google/products/gemini/gemini-3-flash/
    "gemini-3-flash-preview": "gemini-3-flash-preview",  # ✅ New default (Dec 2025)
    # gemini-3-pro-preview: 1M context, 64K output, thought signatures for multi-step
    # reasoning, function calling, Google Search, Code Execution. Requires passing
    # thought signatures in conversation history for reliable agent behavior.
    # Source: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/3-pro
    "gemini-3-pro-preview": "gemini-3-pro-preview",
    # gemini-2.0-flash: 1M context, 50K output, compositional function calling,
    # code execution, native tool calling (search, code_execution, user functions).
    # Source: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/2-0-flash
    "gemini-2.0-flash": "gemini-2.0-flash",
    # Legacy compatibility - redirect 2.5 users to Gemini 3 Flash (better & similar price)
    "gemini-2.5-flash": "gemini-3-flash-preview",  # Auto-redirect to Gemini 3 Flash
    "gemini-2.5-pro": "gemini-3-flash-preview",  # Auto-redirect to Gemini 3 Flash
    "pro-2.5": "gemini-3-flash-preview",  # Auto-redirect to Gemini 3 Flash
    "flash-2.5": "gemini-3-flash-preview",  # Auto-redirect to Gemini 3 Flash
}

# Models that support code_execution + JSON mode TOGETHER (single phase)
# UNIQUE TO GEMINI: Only Google's Gemini 3.x models can execute code AND
# return structured JSON in a SINGLE inference call.
#
# Research (Dec 2025):
# - Gemini 3: https://ai.google.dev/gemini-api/docs/structured-output
#   "Gemini 3 lets you combine Structured Outputs with built-in tools,
#    including Grounding with Google Search, URL Context, and Code Execution."
#
# - OpenAI GPT-4o: Has Code Interpreter + Structured Outputs, but CANNOT
#   combine them (separate tools). https://platform.openai.com/docs/guides/structured-outputs
#
# - Anthropic Claude: Has Code Execution Tool, but uses orchestration-based
#   approach (programmatic tool calling). https://docs.claude.com/en/docs/agents-and-tools/tool-use/code-execution-tool
#
# VERIFIED MODELS (single-inference code execution + JSON):
MODELS_WITH_CODE_EXECUTION: set[str] = {
    # Gemini 3.x - Full support (confirmed Dec 2025)
    "gemini-3-flash-preview",  # ✅ Released Dec 17, 2025 - default model
    "gemini-3-pro-preview",  # ✅ Released Nov 2025 - most capable
}


# OpenRouter model selection tuned for narrative-heavy D&D play
# Official docs: https://openrouter.ai/docs
DEFAULT_OPENROUTER_MODEL = "meta-llama/llama-3.1-70b-instruct"
SPICY_OPENROUTER_MODEL = "x-ai/grok-4.1-fast"
ALLOWED_OPENROUTER_MODELS = [
    # meta-llama/llama-3.1-70b-instruct: 128K context, native function calling,
    # parallel tool calls, zero-shot/few-shot tool use, multilingual (8 languages).
    # Source: https://ai.meta.com/blog/meta-llama-3-1/
    DEFAULT_OPENROUTER_MODEL,
    # meta-llama/llama-3.1-405b-instruct: 128K context, native function calling,
    # built-in tools (brave_search, wolfram_alpha), multilingual, state-of-the-art
    # tool use. Rivals frontier models on general knowledge and math.
    # Source: https://huggingface.co/blog/llama31
    "meta-llama/llama-3.1-405b-instruct",
    # openai/gpt-oss-120b: 131K context, native function calling, tool use,
    # structured outputs, browsing. Matches o4-mini on tool calling (TauBench).
    # Runs at 3K tokens/sec on Cerebras. $0.35/$0.75 per M tokens.
    # Source: https://openai.com/index/introducing-gpt-oss/
    "openai/gpt-oss-120b",
    # z-ai/glm-4.6: 200K context, OpenAI-style function calling, native tool use.
    # Note: OpenRouter spelling differs from Cerebras "zai-glm-4.6" (same model).
    # Source: https://docs.z.ai/guides/llm/glm-4.6
    "z-ai/glm-4.6",
    # x-ai/grok-4.1-fast: 2M context, frontier tool-calling performance, real-time
    # X data, web search, code execution in secure Python sandbox, Files/Collections
    # Search, MCP tools. Multi-turn RL training across full context window.
    # Reasoning mode toggleable. $0.20/$0.05 per M input, $0.50/M output.
    # Source: https://x.ai/news/grok-4-1-fast
    SPICY_OPENROUTER_MODEL,
]

# Cerebras direct provider defaults
# Official docs: https://inference-docs.cerebras.ai/
# Pricing comparison (input/output per M tokens):
#   Llama 3.1 8B: $0.10/$0.10 (CHEAPEST)
#   GPT OSS 120B: $0.35/$0.75 (budget option)
#   Qwen 3 32B: $0.40/$0.80 (not in list - lower context)
#   Qwen 3 235B: $0.60/$1.20 (highest context 256K)
#   Llama 3.3 70B: $0.85/$1.20 (65K context)
#   ZAI GLM 4.6: $2.25/$2.75 (preview, 200K context) <- DEFAULT (prioritize quality/tools)
# NOTE: Defaulting to GLM 4.6 is a conscious trade-off (higher cost vs. Qwen 235B) to prioritize
# quality/tooling; choose Qwen below for cost-sensitive workloads.
DEFAULT_CEREBRAS_MODEL = "zai-glm-4.6"
ALLOWED_CEREBRAS_MODELS = [
    # zai-glm-4.6: 200K context, OpenAI-style function calling, native multimodal
    # function calling (images as tool params), supports both thinking and non-thinking
    # modes. Stronger tool use and search-based agents. $2.25/$2.75 per M tokens.
    # Source: https://docs.z.ai/guides/llm/glm-4.6
    DEFAULT_CEREBRAS_MODEL,
    # qwen-3-235b-a22b-instruct-2507: 256K context (extendable to 1M), excellent
    # tool calling, Qwen-Agent framework support. MoE model (235B total, 22B active).
    # Enhanced long-context understanding, multilingual, strong code/math/reasoning.
    # Most cost-efficient option at $0.60/$1.20 per M tokens.
    # Source: https://huggingface.co/Qwen/Qwen3-235B-A22B-Instruct-2507
    "qwen-3-235b-a22b-instruct-2507",
    # llama-3.3-70b: 65K context, function calling supported BUT multi-turn tool
    # calling NOT supported on Cerebras. Will error if tool_calls array included
    # in assistant turn. Use single-turn pattern only. $0.85/$1.20 per M tokens.
    # Source: https://inference-docs.cerebras.ai/capabilities/tool-use
    "llama-3.3-70b",
    # gpt-oss-120b: 131K context, full function calling support, tool use,
    # structured outputs. TauBench tested for tool calling. Runs at 3K tokens/sec
    # on Cerebras infrastructure. Budget reasoning model at $0.35/$0.75 per M.
    # Source: https://www.cerebras.ai/blog/openai-gpt-oss-120b-runs-fastest-on-cerebras
    "gpt-oss-120b",
]

# Context window budgeting (tokens)
DEFAULT_CONTEXT_WINDOW_TOKENS = 128_000
CONTEXT_WINDOW_SAFETY_RATIO = 0.9
MODEL_CONTEXT_WINDOW_TOKENS = {
    # Gemini
    DEFAULT_GEMINI_MODEL: 1_000_000,  # gemini-3-flash-preview (1M context)
    "gemini-3-flash-preview": 1_000_000,
    "gemini-3-pro-preview": 1_000_000,
    "gemini-2.0-flash": 1_000_000,
    # OpenRouter
    "meta-llama/llama-3.1-70b-instruct": 131_072,
    "meta-llama/llama-3.1-405b-instruct": 131_072,
    "openai/gpt-oss-120b": 131_072,  # 131K context
    "z-ai/glm-4.6": 200_000,  # OpenRouter spelling differs from Cerebras "zai-glm-4.6"
    "x-ai/grok-4.1-fast": 2_000_000,  # Grok 4.1 Fast - 2M context
    # Cerebras
    # IMPORTANT: Cerebras provider context limits are ~128K/131K even when the upstream
    # model family may advertise larger windows elsewhere (e.g., via other providers).
    "qwen-3-235b-a22b-instruct-2507": 131_072,
    "zai-glm-4.6": 131_072,
    "llama-3.3-70b": 65_536,
    "gpt-oss-120b": 131_072,  # 131K context window
}

# Provider/model-specific max output tokens (conservative to avoid API 400s)
# Values pulled from provider docs (OpenRouter as of 2025-12-01; Cerebras as of 2025-12-11).
MODEL_MAX_OUTPUT_TOKENS = {
    # Gemini (we cap at JSON_MODE_MAX_OUTPUT_TOKENS in code; keep for completeness)
    DEFAULT_GEMINI_MODEL: 65_536,  # gemini-3-flash-preview (65K max output)
    "gemini-3-flash-preview": 65_536,
    "gemini-3-pro-preview": 65_536,
    "gemini-2.0-flash": 50_000,
    # OpenRouter
    # Llama 3.1 caps are not reported in the model catalog; OpenRouter commonly limits
    # completion tokens to ~8k for these models, so we adopt 8,192 to avoid 400s while
    # still allowing larger replies than the previous 4k cap. Cerebras-hosted Llama 3.1
    # can safely emit longer replies (see provider-specific entries below).
    "meta-llama/llama-3.1-70b-instruct": 8_192,
    "meta-llama/llama-3.1-405b-instruct": 8_192,
    "openai/gpt-oss-120b": 40_000,  # 40K max output on Cerebras provider
    # Pulled from OpenRouter model metadata (2025-12-01 curl https://openrouter.ai/api/v1/models)
    "z-ai/glm-4.6": 202_752,
    "x-ai/grok-4.1-fast": 30_000,
    # Cerebras (actual limit ~64K, using conservative 32K for safety)
    "qwen-3-235b-a22b-instruct-2507": 32_000,
    "zai-glm-4.6": 32_000,
    "llama-3.3-70b": 32_000,
    "gpt-oss-120b": 40_000,  # 40K max output per Cerebras docs
}

# Debug mode settings
DEFAULT_DEBUG_MODE = True
ALLOWED_DEBUG_MODE_VALUES = [True, False]


# --- INTERACTION MODES ---
# Used to determine the style of user input and AI response
MODE_CHARACTER = "character"
MODE_GOD = "god"
MODE_THINK = "think"  # For planning/thinking without narrative advancement
MODE_COMBAT = "combat"
MODE_REWARDS = "rewards"
MODE_INFO = "info"  # For equipment/inventory/stats queries with trimmed prompts
MODE_CHARACTER_CREATION = "character_creation"  # For focused character creation flow
MODE_CAMPAIGN_UPGRADE = "campaign_upgrade"  # For divine/multiverse ascension ceremonies

# Mode prefixes - used for input detection
THINK_MODE_PREFIX = "THINK:"
GOD_MODE_PREFIX = "GOD MODE:"


def is_god_mode(user_input: str, mode: str | None = None) -> bool:
    """
    Centralized god mode detection.

    SINGLE SOURCE OF TRUTH for determining if an interaction is in God Mode.
    Used by: GodModeAgent.matches_input(), world_logic.py, and any other callers.

    God Mode is active when either:
    1. The mode parameter equals MODE_GOD (case-insensitive), OR
    2. The user input starts with "GOD MODE:" prefix (case-insensitive)

    Args:
        user_input: Raw user input text
        mode: Optional mode parameter from request (e.g., "god", "character")

    Returns:
        True if god mode should be activated
    """
    normalized_input = user_input.strip().upper()
    # Type validation per coding guidelines - use isinstance() checks
    normalized_mode = mode.lower() if isinstance(mode, str) else None
    return normalized_mode == MODE_GOD or normalized_input.startswith(GOD_MODE_PREFIX)


def is_think_mode(user_input: str, mode: str | None = None) -> bool:
    """
    Centralized think mode detection.

    SINGLE SOURCE OF TRUTH for determining if an interaction is in Think Mode.
    Used by: PlanningAgent.matches_input(), world_logic.py, and any other callers.

    Think Mode is active when either:
    1. The mode parameter equals MODE_THINK, OR
    2. The user input starts with "THINK:" prefix (case-insensitive)

    Args:
        user_input: Raw user input text
        mode: Optional mode parameter from request (e.g., "think", "character")

    Returns:
        True if think mode should be activated
    """
    normalized = user_input.strip().upper()
    # Type validation per coding guidelines - use isinstance() checks
    normalized_mode = mode.lower() if isinstance(mode, str) else None
    return normalized_mode == MODE_THINK or normalized.startswith(THINK_MODE_PREFIX)

# --- COMBAT PHASE CONSTANTS ---
# Canonical set of combat phases indicating combat has ended
# Used by RewardsAgent, world_logic enforcement, and state archival
# IMPORTANT: This is the SINGLE SOURCE OF TRUTH - all combat phase checks must use this set
COMBAT_FINISHED_PHASES = frozenset(
    {
        "ended",
        "concluding",
        "concluded",
        "finished",
        "complete",
        "completed",
        "resolved",
        "victory",
    }
)

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
FIELD_DICE_AUDIT_EVENTS = "dice_audit_events"
FIELD_RESOURCES = "resources"
FIELD_DEBUG_INFO = "debug_info"
FIELD_GOD_MODE_RESPONSE = "god_mode_response"
FIELD_DIRECTIVES = "directives"  # God mode directives: {add: [...], drop: [...]}
FIELD_STATE_UPDATES = "state_updates"
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

# --- CAMPAIGN TIER CONSTANTS ---
# Used to track campaign progression for divine/multiverse upgrades
CAMPAIGN_TIER_MORTAL = "mortal"  # Standard D&D 5e gameplay
CAMPAIGN_TIER_DIVINE = "divine"  # Divine Leverage system (god tier)
CAMPAIGN_TIER_SOVEREIGN = "sovereign"  # Sovereign Protocol (multiverse tier)

# Thresholds for campaign upgrades
DIVINE_UPGRADE_LEVEL_THRESHOLD = 25  # Level at which divine upgrade becomes available
DIVINE_POTENTIAL_THRESHOLD = 100  # divine_potential value to trigger upgrade
UNIVERSE_CONTROL_THRESHOLD = 70  # universe_control value to trigger multiverse upgrade

# --- DIVINE RANK SYSTEM ---
# Level-based divine rank progression (inspired by 3.5e Epic/Deities & Demigods)
# Divine Rank determines automatic bonuses to AC, attacks, saves, DCs
# Scales existing stats instead of separate resource pools

# Divine Rank names and level thresholds
DIVINE_RANK_MORTAL = "mortal"  # Level 1-20
DIVINE_RANK_EPIC_MORTAL = "epic_mortal"  # Level 21-25
DIVINE_RANK_QUASI_DEITY = "quasi_deity"  # Level 26-30
DIVINE_RANK_DEMIGOD = "demigod"  # Level 31-35
DIVINE_RANK_MINOR_GOD = "minor_god"  # Level 36-40
DIVINE_RANK_LESSER_DEITY = "lesser_deity"  # Level 41-45
DIVINE_RANK_INTERMEDIATE_DEITY = "intermediate_deity"  # Level 46-50
DIVINE_RANK_GREATER_DEITY = "greater_deity"  # Level 51+

# Level thresholds for divine rank progression
DIVINE_RANK_LEVEL_THRESHOLDS: dict[str, tuple[int, int]] = {
    DIVINE_RANK_MORTAL: (1, 20),
    DIVINE_RANK_EPIC_MORTAL: (21, 25),
    DIVINE_RANK_QUASI_DEITY: (26, 30),
    DIVINE_RANK_DEMIGOD: (31, 35),
    DIVINE_RANK_MINOR_GOD: (36, 40),
    DIVINE_RANK_LESSER_DEITY: (41, 45),
    DIVINE_RANK_INTERMEDIATE_DEITY: (46, 50),
    DIVINE_RANK_GREATER_DEITY: (51, 999),  # No upper limit
}

# Divine rank numeric values (for bonus calculations)
DIVINE_RANK_VALUES: dict[str, int] = {
    DIVINE_RANK_MORTAL: 0,
    DIVINE_RANK_EPIC_MORTAL: 0,  # Epic but not yet divine
    DIVINE_RANK_QUASI_DEITY: 1,
    DIVINE_RANK_DEMIGOD: 2,
    DIVINE_RANK_MINOR_GOD: 3,
    DIVINE_RANK_LESSER_DEITY: 4,
    DIVINE_RANK_INTERMEDIATE_DEITY: 5,
    DIVINE_RANK_GREATER_DEITY: 6,
}

# Divine rank display names (for UI/narrative)
DIVINE_RANK_DISPLAY_NAMES: dict[str, str] = {
    DIVINE_RANK_MORTAL: "Mortal",
    DIVINE_RANK_EPIC_MORTAL: "Epic Mortal",
    DIVINE_RANK_QUASI_DEITY: "Quasi-Deity",
    DIVINE_RANK_DEMIGOD: "Demigod",
    DIVINE_RANK_MINOR_GOD: "Minor God",
    DIVINE_RANK_LESSER_DEITY: "Lesser Deity",
    DIVINE_RANK_INTERMEDIATE_DEITY: "Intermediate Deity",
    DIVINE_RANK_GREATER_DEITY: "Greater Deity",
}

# Divine immunities granted at each rank (cumulative)
DIVINE_RANK_IMMUNITIES: dict[str, list[str]] = {
    DIVINE_RANK_MORTAL: [],
    DIVINE_RANK_EPIC_MORTAL: [],
    DIVINE_RANK_QUASI_DEITY: ["sleep"],
    DIVINE_RANK_DEMIGOD: ["sleep", "paralysis"],
    DIVINE_RANK_MINOR_GOD: ["sleep", "paralysis", "charm"],
    DIVINE_RANK_LESSER_DEITY: ["sleep", "paralysis", "charm", "fear"],
    DIVINE_RANK_INTERMEDIATE_DEITY: ["sleep", "paralysis", "charm", "fear", "disease", "poison"],
    DIVINE_RANK_GREATER_DEITY: ["sleep", "paralysis", "charm", "fear", "disease", "poison", "death_effects", "energy_drain"],
}


def get_divine_rank_from_level(level: int) -> str:
    """Get the divine rank name for a given character level.

    Args:
        level: Character level (1+)

    Returns:
        Divine rank constant (e.g., DIVINE_RANK_MINOR_GOD)
    """
    if not isinstance(level, int) or level < 1:
        return DIVINE_RANK_MORTAL

    for rank_name, (min_level, max_level) in DIVINE_RANK_LEVEL_THRESHOLDS.items():
        if min_level <= level <= max_level:
            return rank_name

    # Fallback for very high levels
    return DIVINE_RANK_GREATER_DEITY


def get_divine_rank_bonus(level: int) -> int:
    """Get the divine rank bonus for a given level.

    The bonus is applied to AC, attack rolls, saving throws, ability checks,
    and spell DCs. This replaces the separate DPP system with scaled stats.

    Args:
        level: Character level (1+)

    Returns:
        Divine rank bonus (0-6+)
    """
    rank_name = get_divine_rank_from_level(level)
    return DIVINE_RANK_VALUES.get(rank_name, 0)


def get_divine_safe_limit(level: int) -> int:
    """Get the safe leverage limit for a given level.

    Using Divine Leverage beyond this limit generates Dissonance.
    Safe Limit = Divine Rank × 5

    Args:
        level: Character level (1+)

    Returns:
        Safe leverage limit (0, 5, 10, 15, 20, 25, 30)
    """
    return get_divine_rank_bonus(level) * 5


def get_divine_immunities(level: int) -> list[str]:
    """Get the list of immunities for a given level.

    Immunities are cumulative as divine rank increases.

    Args:
        level: Character level (1+)

    Returns:
        List of immunity names
    """
    rank_name = get_divine_rank_from_level(level)
    return DIVINE_RANK_IMMUNITIES.get(rank_name, []).copy()


def is_epic_level(level: int) -> bool:
    """Check if a level qualifies as epic (21+).

    Args:
        level: Character level

    Returns:
        True if level 21 or higher
    """
    return isinstance(level, int) and level >= 21


def is_divine_level(level: int) -> bool:
    """Check if a level qualifies as divine (26+, has divine rank bonuses).

    Args:
        level: Character level

    Returns:
        True if level 26 or higher (Quasi-Deity+)
    """
    return isinstance(level, int) and level >= 26


# --- EPIC XP TABLE (3.5e Adapted with Exponential Divine Scaling) ---
# Standard 5e XP for levels 1-20
# Linear epic formula for levels 21-25: XP(N) = XP(N-1) + (N × 1,000)
# Exponential divine formula for levels 26+: XP(N) = XP(N-1) × 1.15

# 5e XP thresholds (total XP needed to reach each level)
XP_TABLE_5E: dict[int, int] = {
    1: 0,
    2: 300,
    3: 900,
    4: 2_700,
    5: 6_500,
    6: 14_000,
    7: 23_000,
    8: 34_000,
    9: 48_000,
    10: 64_000,
    11: 85_000,
    12: 100_000,
    13: 120_000,
    14: 140_000,
    15: 165_000,
    16: 195_000,
    17: 225_000,
    18: 265_000,
    19: 305_000,
    20: 355_000,
}

# Exponential growth rate for divine levels (26+)
# Each level requires 15% more XP than the previous
DIVINE_XP_GROWTH_RATE = 1.15

# XP source caps for divine beings (mortals don't impress gods)
XP_SOURCE_CAPS: dict[str, int] = {
    "mortal_combat": 1_000,      # CR 1-10 enemies, max per encounter
    "epic_mortal_combat": 10_000,  # CR 11-20 enemies, max per encounter
    "epic_creature": -1,         # CR 21-30, full XP (no cap)
    "divine_rival": -1,          # Full XP × 10 multiplier
    "great_work_minor": 100_000,  # Minor divine quest
    "great_work_major": 500_000,  # Major divine quest
    "great_work_cosmic": 1_000_000,  # Cosmic-scale achievement
    "worshipper_milestone": 50_000,  # Per 10,000 new followers
}

# --- SOUL HARVESTING SYSTEM (Fiendish Deities) ---
# Fiendish deities can harvest mortal souls for XP, BYPASSING normal caps
# This gives demons/devils a unique progression path

# Soul types and their base XP values
SOUL_VALUES: dict[str, int] = {
    "commoner": 10,           # Tier 1: Peasants, laborers
    "soldier": 25,            # Tier 2: Guards, trained combatants
    "named_npc": 250,         # Tier 3: Shopkeepers, minor nobles
    "hero": 1_000,            # Tier 4: Adventurers level 5-10
    "champion": 5_000,        # Tier 5: Famous warriors level 11-15
    "legend": 25_000,         # Tier 6: World-renowned level 16-20
    "epic_mortal": 100_000,   # Tier 7: Demigod-tier mortals level 21+
    "celestial": 500_000,     # Tier 8: Angels, rival demons
    "divine_fragment": 1_000_000,  # Tier 9: Piece of another god
}

# Soul tier numbers (for Dissonance calculation)
SOUL_TIERS: dict[str, int] = {
    "commoner": 1,
    "soldier": 2,
    "named_npc": 3,
    "hero": 4,
    "champion": 5,
    "legend": 6,
    "epic_mortal": 7,
    "celestial": 8,
    "divine_fragment": 9,
}

# Soul acquisition methods and their multipliers/costs
SOUL_ACQUISITION_METHODS: dict[str, dict[str, float]] = {
    "contract": {       # Willing soul via deal/bargain
        "xp_multiplier": 2.0,
        "dissonance_per_tier": 0.0,
    },
    "corruption": {     # Led astray, chose evil
        "xp_multiplier": 1.5,
        "dissonance_per_tier": 2.0,
    },
    "theft": {          # Violent extraction
        "xp_multiplier": 1.0,
        "dissonance_per_tier": 5.0,
    },
}


def calculate_soul_xp(soul_type: str, method: str) -> int:
    """Calculate XP gained from harvesting a soul.

    Soul harvesting BYPASSES normal mortal XP caps for fiendish deities.

    Args:
        soul_type: Type of soul (from SOUL_VALUES keys)
        method: Acquisition method (contract, corruption, theft)

    Returns:
        XP amount after applying method multiplier
    """
    base_xp = SOUL_VALUES.get(soul_type, 10)
    method_data = SOUL_ACQUISITION_METHODS.get(method, SOUL_ACQUISITION_METHODS["theft"])
    multiplier = method_data["xp_multiplier"]
    return int(base_xp * multiplier)


def calculate_soul_dissonance(soul_type: str, method: str) -> float:
    """Calculate Dissonance from harvesting a soul.

    Args:
        soul_type: Type of soul (from SOUL_TIERS keys)
        method: Acquisition method (contract, corruption, theft)

    Returns:
        Dissonance percentage (0.0 for contracts, scales with tier for others)
    """
    tier = SOUL_TIERS.get(soul_type, 1)
    method_data = SOUL_ACQUISITION_METHODS.get(method, SOUL_ACQUISITION_METHODS["theft"])
    dissonance_per_tier = method_data["dissonance_per_tier"]
    return tier * dissonance_per_tier


def is_fiendish_portfolio(portfolio: str | None) -> bool:
    """Check if a divine portfolio qualifies for soul harvesting.

    Args:
        portfolio: The deity's portfolio/domain

    Returns:
        True if the portfolio is fiendish (demons, devils, dark gods)
    """
    if not portfolio:
        return False

    fiendish_keywords = {
        "demon", "devil", "fiend", "hell", "abyss", "infernal",
        "darkness", "evil", "death", "undeath", "corruption",
        "tyranny", "suffering", "torment", "souls", "bargains",
    }

    portfolio_lower = portfolio.lower()
    return any(keyword in portfolio_lower for keyword in fiendish_keywords)


def get_xp_for_level(level: int) -> int:
    """Get the total XP required to reach a given level.

    Uses 5e XP table for levels 1-20.
    Linear formula for epic levels 21-25: XP(N) = XP(N-1) + (N × 1,000)
    Exponential formula for divine levels 26+: Each level costs 15% more.

    Args:
        level: Target level (1+)

    Returns:
        Total XP required to reach that level
    """
    if not isinstance(level, int) or level < 1:
        return 0

    # Use 5e table for levels 1-20
    if level <= 20:
        return XP_TABLE_5E.get(level, 0)

    # Epic levels 21-25: linear formula
    xp = XP_TABLE_5E[20]  # 355,000
    for lvl in range(21, min(level + 1, 26)):
        xp += lvl * 1000

    # Divine levels 26+: exponential formula
    if level >= 26:
        # XP at level 25 (end of linear)
        xp_at_25 = XP_TABLE_5E[20]
        for lvl in range(21, 26):
            xp_at_25 += lvl * 1000  # 355k + 21k + 22k + 23k + 24k + 25k = 470k

        # Base XP to go from 25→26
        base_divine_xp = 27_000

        # Calculate cumulative XP for divine levels
        xp = xp_at_25
        for lvl in range(26, level + 1):
            # Each level costs base × 1.15^(lvl-25)
            level_cost = int(base_divine_xp * (DIVINE_XP_GROWTH_RATE ** (lvl - 25)))
            xp += level_cost

    return xp


def get_xp_to_next_level(current_level: int) -> int:
    """Get the XP needed to advance from current level to next level.

    Args:
        current_level: Current character level

    Returns:
        XP needed for next level (or 0 if invalid)
    """
    if not isinstance(current_level, int) or current_level < 1:
        return 0

    # For divine levels (26+), use exponential formula
    if current_level >= 25:
        base_divine_xp = 27_000
        return int(base_divine_xp * (DIVINE_XP_GROWTH_RATE ** (current_level + 1 - 25)))

    # For epic levels (20-24), use linear formula
    if current_level >= 20:
        return (current_level + 1) * 1000

    # For standard levels, calculate difference
    current_xp = get_xp_for_level(current_level)
    next_xp = get_xp_for_level(current_level + 1)
    return next_xp - current_xp


def get_level_from_xp(total_xp: int) -> int:
    """Get the character level for a given total XP.

    Args:
        total_xp: Total experience points

    Returns:
        Character level (1+)
    """
    if not isinstance(total_xp, int) or total_xp < 0:
        return 1

    # Binary search would be more efficient, but this is clear
    level = 1
    while get_xp_for_level(level + 1) <= total_xp:
        level += 1
        # Safety cap at level 100
        if level >= 100:
            break

    return level


def get_capped_xp(xp_amount: int, source_type: str, divine_rank: int = 0) -> int:
    """Apply XP source caps for divine beings.

    Gods don't gain meaningful XP from mortal victories.

    Args:
        xp_amount: Raw XP from the source
        source_type: Type of XP source (from XP_SOURCE_CAPS keys)
        divine_rank: Character's divine rank (0 = mortal, 1+ = divine)

    Returns:
        Capped XP amount (or full amount if no cap applies)
    """
    # Mortals get full XP from everything
    if divine_rank == 0:
        return xp_amount

    # Divine rivals give 10x XP
    if source_type == "divine_rival":
        return xp_amount * 10

    # Check for caps
    cap = XP_SOURCE_CAPS.get(source_type, -1)
    if cap == -1:
        return xp_amount  # No cap

    return min(xp_amount, cap)


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
FILENAME_GAME_STATE_EXAMPLES = "game_state_examples.md"
FILENAME_MASTER_DIRECTIVE = "master_directive.md"
FILENAME_DND_SRD = "dnd_srd_instruction.md"
FILENAME_CHARACTER_TEMPLATE = "character_template.md"
FILENAME_LIVING_WORLD = "living_world_instruction.md"
FILENAME_COMBAT_SYSTEM = "combat_system_instruction.md"
FILENAME_REWARDS_SYSTEM = "rewards_system_instruction.md"
FILENAME_THINK_MODE = "think_mode_instruction.md"

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
PROMPT_TYPE_GAME_STATE_EXAMPLES = "game_state_examples"
PROMPT_TYPE_CHARACTER_TEMPLATE = "character_template"
PROMPT_TYPE_MASTER_DIRECTIVE = "master_directive"
PROMPT_TYPE_DND_SRD = "dnd_srd"
PROMPT_TYPE_GOD_MODE = "god_mode"
PROMPT_TYPE_LIVING_WORLD = "living_world"
PROMPT_TYPE_COMBAT = "combat"
PROMPT_TYPE_REWARDS = "rewards"
PROMPT_TYPE_RELATIONSHIP = "relationship"
PROMPT_TYPE_REPUTATION = "reputation"
PROMPT_TYPE_CHARACTER_CREATION = "character_creation"
PROMPT_TYPE_THINK = "think"
PROMPT_TYPE_PLANNING_PROTOCOL = "planning_protocol"
# Divine Leverage (god tier) prompt types
PROMPT_TYPE_DIVINE_ASCENSION = "divine_ascension"
PROMPT_TYPE_DIVINE_SYSTEM = "divine_system"
# Sovereign Protocol (multiverse tier) prompt types
PROMPT_TYPE_SOVEREIGN_ASCENSION = "sovereign_ascension"
PROMPT_TYPE_SOVEREIGN_SYSTEM = "sovereign_system"


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
GAME_STATE_EXAMPLES_PATH = os.path.join(PROMPTS_DIR, "game_state_examples.md")
MASTER_DIRECTIVE_PATH = os.path.join(PROMPTS_DIR, "master_directive.md")
DND_SRD_INSTRUCTION_PATH = os.path.join(PROMPTS_DIR, "dnd_srd_instruction.md")
GOD_MODE_INSTRUCTION_PATH = os.path.join(PROMPTS_DIR, "god_mode_instruction.md")
LIVING_WORLD_INSTRUCTION_PATH = os.path.join(PROMPTS_DIR, FILENAME_LIVING_WORLD)
COMBAT_SYSTEM_INSTRUCTION_PATH = os.path.join(
    PROMPTS_DIR, "combat_system_instruction.md"
)
REWARDS_SYSTEM_INSTRUCTION_PATH = os.path.join(
    PROMPTS_DIR, "rewards_system_instruction.md"
)
RELATIONSHIP_INSTRUCTION_PATH = os.path.join(PROMPTS_DIR, "relationship_instruction.md")
REPUTATION_INSTRUCTION_PATH = os.path.join(PROMPTS_DIR, "reputation_instruction.md")
CHARACTER_CREATION_INSTRUCTION_PATH = os.path.join(
    PROMPTS_DIR, "character_creation_instruction.md"
)
THINK_MODE_INSTRUCTION_PATH = os.path.join(PROMPTS_DIR, FILENAME_THINK_MODE)
PLANNING_PROTOCOL_PATH = os.path.join(PROMPTS_DIR, "planning_protocol.md")
# Divine Leverage prompt paths
DIVINE_PROMPTS_DIR = os.path.join(PROMPTS_DIR, "divine")
DIVINE_ASCENSION_PATH = os.path.join(DIVINE_PROMPTS_DIR, "divine_ascension_ceremony.md")
DIVINE_SYSTEM_PATH = os.path.join(DIVINE_PROMPTS_DIR, "divine_leverage_system.md")
# Sovereign Protocol prompt paths
MULTIVERSE_PROMPTS_DIR = os.path.join(PROMPTS_DIR, "multiverse")
SOVEREIGN_ASCENSION_PATH = os.path.join(MULTIVERSE_PROMPTS_DIR, "sovereign_ascension_ceremony.md")
SOVEREIGN_SYSTEM_PATH = os.path.join(MULTIVERSE_PROMPTS_DIR, "sovereign_system.md")

# --- LIVING WORLD SETTINGS ---
# The living world instruction is included every N turns to advance world state.
# If this value changes, update living_world_instruction.md and references in
# narrative_system_instruction.md to keep cadence documentation in sync.
LIVING_WORLD_TURN_INTERVAL = 3
COMPANION_ARC_INITIAL_TURN = 3
COMPANION_ARC_PHASES = ("discovery", "development", "crisis", "resolution")
COMPANION_ARC_TYPES = (
    "personal_redemption",
    "lost_family",
    "rival_nemesis",
    "forbidden_love",
    "dark_secret",
    "homeland_crisis",
    "mentor_legacy",
    "prophetic_destiny",
)

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


# --- COMBAT DISPOSITION CONSTANTS ---
# Used for determining how to handle combatants during combat cleanup
# These centralize the keyword sets from game_state.py for maintainability

# Combatant types that should NOT be removed during cleanup
# These represent friendly/allied combatants that persist after combat
FRIENDLY_COMBATANT_TYPES: frozenset[str] = frozenset(
    {
        "pc",  # Player character
        "player",  # Alternative player designation
        "party",  # Party member
        "companion",  # Animal companion, familiar, etc.
        "ally",  # Friendly NPC fighting alongside party
        "friendly",  # Explicitly friendly combatant
        "support",  # Support character (healer, etc.)
    }
)

# Neutral combatant types that are non-hostile but not allied
NEUTRAL_COMBATANT_TYPES: frozenset[str] = frozenset(
    {
        "neutral",  # Explicitly neutral
        "bystander",  # Passive observer
        "civilian",  # Non-combatant civilian
        "noncombatant",  # Explicit non-combatant
    }
)

# Generic/enemy roles that indicate a combatant can be removed after defeat
# NPCs with these roles (or None/empty) are considered generic enemies
GENERIC_ENEMY_ROLES: frozenset[str | None] = frozenset(
    {
        None,  # No role assigned
        "",  # Empty role
        "enemy",  # Standard enemy
        "minion",  # Expendable enemy
        "generic",  # Generic combatant
        "unknown",  # Unknown type (default to enemy)
        "hostile",  # Hostile NPC
        "foe",  # Alternative enemy designation
        "monster",  # Monster/creature enemy
    }
)


def is_friendly_combatant(combatant_type: str | None) -> bool:
    """Check if a combatant type indicates a friendly entity.

    Args:
        combatant_type: The type/role of the combatant (will be normalized)

    Returns:
        True if the combatant should be preserved (not removed) after combat
    """
    if combatant_type is None:
        return False
    normalized = (
        combatant_type.lower().strip()
        if isinstance(combatant_type, str)
        else combatant_type
    )
    return normalized in FRIENDLY_COMBATANT_TYPES


def is_generic_enemy_role(role: str | None) -> bool:
    """Check if a role indicates a generic/removable enemy.

    Args:
        role: The role of the NPC (will be normalized)

    Returns:
        True if the NPC is a generic enemy that can be deleted after defeat
    """
    if role is None or role == "":
        return True
    normalized = role.lower().strip() if isinstance(role, str) else role
    return normalized in GENERIC_ENEMY_ROLES
