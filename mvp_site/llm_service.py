"""
LLM Service - AI Integration and Response Processing

This module provides comprehensive AI service integration for WorldArchitect.AI,
handling all aspects of story generation, prompt construction, and response processing.

Key Responsibilities:
- Gemini AI client management and model selection
- System instruction building and prompt construction
- Entity tracking and narrative validation
- JSON response parsing and structured data handling
- Model fallback and error handling
- Planning block enforcement and debug content management
- Token counting and context management
- **FIXED: Token limit management to prevent backstory cutoffs**

Architecture:
- Uses Google Generative AI (Gemini) for story generation
- Implements robust prompt building with PromptBuilder class
- Provides entity tracking with multiple mitigation strategies
- Includes comprehensive error handling
- Supports both initial story generation and continuation
- Manages complex state interactions and validation

Key Classes:
- PromptBuilder: Constructs system instructions and prompts
- LLMResponse: Custom response object with parsed data
- EntityPreloader: Pre-loads entity context for tracking
- EntityInstructionGenerator: Creates entity-specific instructions

Dependencies:
- Google Generative AI SDK for Gemini API calls
- Custom entity tracking and validation modules
- Game state management for context
- Token utilities for cost management
"""

import json
import logging
import os
import re
import sys
import traceback
from dataclasses import dataclass
from typing import Any

from firebase_admin import auth as firebase_auth
from google.genai import types

from mvp_site import constants, logging_util
from mvp_site.custom_types import UserId
from mvp_site.decorators import log_exceptions
from mvp_site.entity_instructions import EntityInstructionGenerator

# Import entity tracking mitigation modules
from mvp_site.entity_preloader import EntityPreloader
from mvp_site.entity_tracking import create_from_game_state
from mvp_site.entity_validator import EntityValidator
from mvp_site.file_cache import read_file_cached
from mvp_site.firestore_service import get_user_settings
from mvp_site.game_state import GameState
from mvp_site.llm_providers import (
    ContextTooLargeError,
    cerebras_provider,
    gemini_provider,
    openrouter_provider,
)
from mvp_site.llm_request import LLMRequest, LLMRequestError
from mvp_site.llm_response import LLMResponse

# Removed old json_input_schema import - now using LLMRequest for structured JSON
from mvp_site.narrative_response_schema import (
    NarrativeResponse,
    create_structured_prompt_injection,
    parse_structured_response,
    validate_entity_coverage,
)
from mvp_site.narrative_sync_validator import NarrativeSyncValidator
from mvp_site.schemas.entities_pydantic import sanitize_entity_name_for_id
from mvp_site.serialization import json_default_serializer
from mvp_site.token_utils import estimate_tokens, log_with_tokens
from mvp_site.world_loader import load_world_content_for_system_instruction

logging_util.basicConfig(
    level=logging_util.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Create module logger
logger = logging.getLogger(__name__)

# Initialize entity tracking mitigation modules
entity_preloader = EntityPreloader()
instruction_generator = EntityInstructionGenerator()
entity_validator = EntityValidator()

# Expected companion count for validation
EXPECTED_COMPANION_COUNT = 3


# Remove redundant json_datetime_serializer - use json_default_serializer instead
# which properly handles Firestore Sentinels, datetime objects, and other special types


# --- CONSTANTS ---
# Default model selection based on the configured DEFAULT_LLM_PROVIDER
# This ensures provider-model consistency across all code paths
if constants.DEFAULT_LLM_PROVIDER == constants.LLM_PROVIDER_CEREBRAS:
    DEFAULT_MODEL: str = constants.DEFAULT_CEREBRAS_MODEL
    TEST_MODEL: str = constants.DEFAULT_CEREBRAS_MODEL
elif constants.DEFAULT_LLM_PROVIDER == constants.LLM_PROVIDER_OPENROUTER:
    DEFAULT_MODEL: str = constants.DEFAULT_OPENROUTER_MODEL
    TEST_MODEL: str = constants.DEFAULT_OPENROUTER_MODEL
else:  # Gemini (default fallback)
    DEFAULT_MODEL: str = constants.DEFAULT_GEMINI_MODEL
    TEST_MODEL: str = constants.DEFAULT_GEMINI_MODEL

@dataclass(frozen=True)
class ProviderSelection:
    provider: str
    model: str


def _select_provider_with_fallback() -> tuple[str, str]:
    """Select the best available provider based on API key availability.

    Returns the default provider if its API key is available, otherwise falls
    back to an alternative provider with an available key.

    This prevents hard failures when the default provider's API key is missing
    but other provider keys are available.

    Returns:
        tuple[str, str]: (provider_name, model_name)
    """
    default_provider = constants.DEFAULT_LLM_PROVIDER

    # Check if default provider's API key is available
    api_key_map = {
        constants.LLM_PROVIDER_GEMINI: os.environ.get("GEMINI_API_KEY", ""),
        constants.LLM_PROVIDER_CEREBRAS: os.environ.get("CEREBRAS_API_KEY", ""),
        constants.LLM_PROVIDER_OPENROUTER: os.environ.get("OPENROUTER_API_KEY", ""),
    }

    model_map = {
        constants.LLM_PROVIDER_GEMINI: constants.DEFAULT_GEMINI_MODEL,
        constants.LLM_PROVIDER_CEREBRAS: constants.DEFAULT_CEREBRAS_MODEL,
        constants.LLM_PROVIDER_OPENROUTER: constants.DEFAULT_OPENROUTER_MODEL,
    }

    # Try default provider first
    if api_key_map.get(default_provider):
        return default_provider, model_map[default_provider]

    # Fall back to first available provider
    fallback_order = [
        constants.LLM_PROVIDER_CEREBRAS,
        constants.LLM_PROVIDER_GEMINI,
        constants.LLM_PROVIDER_OPENROUTER,
    ]

    for provider in fallback_order:
        if api_key_map.get(provider):
            logging_util.warning(
                f"Default provider {default_provider} API key missing, "
                f"falling back to {provider}"
            )
            return provider, model_map[provider]

    # No API keys available - return default and let it fail with clear error
    return default_provider, model_map[default_provider]


# No longer using pro model for any inputs

# Gemini 2.5 Flash OUTPUT token limits (corrected based on updated specs)
# Gemini 2.5 Flash = 65,535 output tokens (not 8,192 as initially thought)
# Using conservative 50,000 output token limit to stay well below maximum
MAX_OUTPUT_TOKENS: int = (
    50000  # Conservative output token limit below Gemini 2.5 Flash max (65,535)
)
TEMPERATURE: float = 0.9
TARGET_WORD_COUNT: int = 300
# Add a safety margin for JSON responses to prevent mid-response cutoffs

# Fallback content constants to avoid code duplication
DEFAULT_CHOICES: dict[str, str] = {
    "Continue": "Continue with your current course of action.",
    "Explore": "Explore your surroundings.",
    "Other": "Describe a different action you'd like to take.",
}

FALLBACK_PLANNING_BLOCK_VALIDATION: dict[str, Any] = {
    "thinking": "The AI response was incomplete. Here are some default options:",
    "choices": DEFAULT_CHOICES,
}

FALLBACK_PLANNING_BLOCK_EXCEPTION: dict[str, Any] = {
    "thinking": "Failed to generate planning block. Here are some default options:",
    "choices": DEFAULT_CHOICES,
}
# For JSON mode, use same output token limit as regular mode
# This ensures complete character backstories and complex JSON responses
JSON_MODE_MAX_OUTPUT_TOKENS: int = MAX_OUTPUT_TOKENS  # Same limit for consistency
MAX_INPUT_TOKENS: int = 300000
SAFE_CHAR_LIMIT: int = MAX_INPUT_TOKENS * 4
GEMINI_COMPACTION_TOKEN_LIMIT: int = 300_000  # Cap compaction well below 1M max
# Dynamic output reserve: 12k default for normal gameplay, scales up for combat/complex
OUTPUT_TOKEN_RESERVE_DEFAULT: int = 12_000  # Typical responses are 1-3k tokens
OUTPUT_TOKEN_RESERVE_COMBAT: int = 24_000  # Combat/complex scenes need more
OUTPUT_TOKEN_RESERVE_MIN: int = 1024
OUTPUT_TOKEN_RESERVE_RATIO: float = 0.20  # Reserve 20% of context for output tokens

# Entity tracking token reserves - these are added AFTER truncation so must be pre-budgeted
# Sizes based on production data with 10+ NPCs:
# - entity_preload_text: ~2000-3000 tokens (NPC summaries)
# - entity_specific_instructions: ~1500-2000 tokens (per-turn instructions)
# - entity_tracking_instruction: ~1000-1500 tokens (tracking rules)
# NOTE: timeline_log text is constructed for diagnostics/entity instructions but is NOT
# serialized into the structured LLMRequest payload. If serialization is ever enabled,
# TIMELINE_LOG_INCLUDED_IN_STRUCTURED_REQUEST must be flipped and budgeting adjusted.
ENTITY_TRACKING_TOKEN_RESERVE: int = 10_500  # Conservative reserve for entity tracking

# Timeline log handling
# The structured LLMRequest path serializes only `story_history` (no timeline log).
# The duplication factor remains available as a guardrail for any prompt path that
# explicitly serializes timeline_log text alongside story_history. Prompt builders must
# flip TIMELINE_LOG_INCLUDED_IN_STRUCTURED_REQUEST to True and update docs/tests if they
# start sending the timeline log string again.
TIMELINE_LOG_DUPLICATION_FACTOR: float = 2.05
TIMELINE_LOG_INCLUDED_IN_STRUCTURED_REQUEST: bool = False

# Entity tiering configuration for LRU-style token reduction
# Reduces entity_tracking from ~40K tokens to ~1K tokens by:
# 1. Only including recently-active entities (mentioned in last N turns)
# 2. Trimming fields to essential info only (name, role, status, hp)
ENTITY_TIER_ACTIVE_MAX: int = 5  # Max entities with essential field tracking
ENTITY_TIER_PRESENT_MAX: int = 10  # Max entities with minimal (name+role) tracking
ENTITY_LOOKBACK_TURNS: int = 5  # Turns to scan for recent entity mentions


def _apply_timeline_log_duplication_guard(
    available_story_tokens_raw: int, include_timeline_log_in_prompt: bool
) -> tuple[int, str]:
    """Apply the duplication guard only when timeline_log is serialized.

    Args:
        available_story_tokens_raw: Story tokens available before duplication check.
        include_timeline_log_in_prompt: Whether the outgoing request will contain
            a timeline_log string alongside story_history text.

    Returns:
        tuple[int, str]: (Adjusted story token budget, explanation note)
    """

    if include_timeline_log_in_prompt:
        adjusted_budget = int(
            available_story_tokens_raw / TIMELINE_LOG_DUPLICATION_FACTOR
        )
        note = (
            "timeline_log included; divided by duplication factor "
            f"{TIMELINE_LOG_DUPLICATION_FACTOR}"
        )
    else:
        adjusted_budget = available_story_tokens_raw
        note = (
            "timeline_log not serialized in structured LLMRequest; no duplication"
            " factor applied"
        )

    return adjusted_budget, note


def _extract_recently_mentioned_entities(
    story_context: list[dict[str, Any]],
    npc_names: list[str],
    lookback_turns: int = ENTITY_LOOKBACK_TURNS,
) -> dict[str, int]:
    """
    Scan recent story turns to find which NPCs were mentioned.

    Uses LRU-style recency scoring: entities mentioned more recently get higher scores.
    This allows us to prioritize active entities over dormant ones.

    Args:
        story_context: List of story turn entries with 'text' field
        npc_names: List of known NPC names to search for
        lookback_turns: Number of recent turns to scan

    Returns:
        Dict of {npc_name: recency_score} where higher = more recent
    """
    recent_turns = story_context[-lookback_turns:] if story_context else []
    mentioned: dict[str, int] = {}

    for turn_idx, turn in enumerate(recent_turns):
        text = turn.get("text", "").lower()
        for npc_name in npc_names:
            if npc_name.lower() in text:
                # Higher index = more recent = higher score
                mentioned[npc_name] = turn_idx

    return mentioned


def _tier_entities(
    npc_data: dict[str, Any],
    recently_mentioned: dict[str, int],
    current_location: str,
) -> tuple[list[str], list[str], list[str]]:
    """
    Categorize NPCs into ACTIVE, PRESENT, DORMANT tiers for token optimization.

    ACTIVE: Recently mentioned, get essential field tracking (~50 tokens each)
    PRESENT: In current location, get minimal tracking (~10 tokens each)
    DORMANT: Not active, excluded from entity_tracking (rely on story_history)

    Args:
        npc_data: Dict of NPC name -> NPC data from game_state
        recently_mentioned: Dict of NPC name -> recency score from story scan
        current_location: Current location name for presence check

    Returns:
        Tuple of (active_names, present_names, dormant_names)
    """
    active_candidates: list[tuple[str, int]] = []
    present: list[str] = []
    dormant: list[str] = []

    for name, data in npc_data.items():
        npc_location = data.get("current_location", data.get("location", ""))

        if name in recently_mentioned:
            # Recently mentioned - candidate for ACTIVE tier
            active_candidates.append((name, recently_mentioned[name]))
        elif npc_location and current_location and npc_location.lower() in current_location.lower():
            # In same location but not recently mentioned - PRESENT tier
            present.append(name)
        else:
            # Not mentioned, different location - DORMANT (excluded)
            dormant.append(name)

    # Sort active by recency (higher score = more recent), take top N
    active_candidates.sort(key=lambda x: x[1], reverse=True)
    active = [name for name, _ in active_candidates[:ENTITY_TIER_ACTIVE_MAX]]

    # Limit present entities
    present = present[:ENTITY_TIER_PRESENT_MAX]

    return active, present, dormant


def _trim_entity_fields(npc_data: dict[str, Any], tier: str) -> dict[str, Any]:
    """
    Extract only essential fields based on entity tier.

    ACTIVE tier (~50 tokens): name, role, attitude, status, hp, location
    PRESENT tier (~10 tokens): name, role only

    This reduces per-entity tokens from ~500 to ~50 or ~10.

    Args:
        npc_data: Full NPC data dict from game_state
        tier: Either "ACTIVE" or "PRESENT"

    Returns:
        Trimmed dict with only essential fields
    """
    if tier == "ACTIVE":
        # Extract health info safely
        health = npc_data.get("health", {})
        if isinstance(health, dict):
            hp_current = health.get("hp", "?")
            hp_max = health.get("hp_max", "?")
        else:
            hp_current = npc_data.get("hp_current", npc_data.get("hp", "?"))
            hp_max = npc_data.get("hp_max", "?")

        # Extract status safely
        status_list = npc_data.get("status", ["conscious"])
        if isinstance(status_list, list) and status_list:
            status = status_list[0] if isinstance(status_list[0], str) else "conscious"
        elif isinstance(status_list, str):
            status = status_list
        else:
            status = "conscious"

        return {
            "name": npc_data.get("display_name", npc_data.get("name", "Unknown")),
            "role": npc_data.get("role", "NPC"),
            "attitude": npc_data.get("attitude_to_party", "neutral"),
            "status": status,
            "hp": f"{hp_current}/{hp_max}",
            "location": npc_data.get("current_location", npc_data.get("location", "unknown")),
        }

    elif tier == "PRESENT":
        return {
            "name": npc_data.get("display_name", npc_data.get("name", "Unknown")),
            "role": npc_data.get("role", "NPC"),
        }

    # DORMANT - return empty (should not be called)
    return {}


def _build_trimmed_entity_tracking(
    npc_data: dict[str, Any],
    story_context: list[dict[str, Any]],
    current_location: str,
) -> tuple[dict[str, Any], str]:
    """
    Build entity_tracking_data with tiered, trimmed entities.

    Reduces token usage from ~40K to ~1K by:
    1. Only including recently-active and present entities
    2. Trimming fields to essentials only

    Args:
        npc_data: Dict of NPC name -> NPC data from game_state.npc_data
        story_context: List of story turn entries
        current_location: Current location name

    Returns:
        Tuple of (entity_tracking_data, log_summary)
    """
    if not npc_data:
        return {"active_entities": [], "present_entities": []}, "ENTITY_TIERS: no NPCs"

    # Get NPC names for scanning
    npc_names = list(npc_data.keys())

    # Find recently mentioned entities via LRU scan
    recently_mentioned = _extract_recently_mentioned_entities(
        story_context, npc_names
    )

    # Tier the entities
    active, present, dormant = _tier_entities(
        npc_data, recently_mentioned, current_location
    )

    # Build trimmed entity lists
    active_entities = [
        _trim_entity_fields(npc_data[name], "ACTIVE")
        for name in active
        if name in npc_data
    ]
    present_entities = [
        _trim_entity_fields(npc_data[name], "PRESENT")
        for name in present
        if name in npc_data
    ]

    # Build tracking data - much smaller than before
    entity_tracking_data = {
        "active_entities": active_entities,
        "present_entities": present_entities,
        # DORMANT entities excluded - LLM has story_history for context
    }

    log_summary = (
        f"ENTITY_TIERS: active={len(active)}/{ENTITY_TIER_ACTIVE_MAX}, "
        f"present={len(present)}/{ENTITY_TIER_PRESENT_MAX}, "
        f"dormant={len(dormant)} (excluded)"
    )

    return entity_tracking_data, log_summary


def _get_context_window_tokens(model_name: str) -> int:
    """Return the configured context window size for a model in tokens."""

    return constants.MODEL_CONTEXT_WINDOW_TOKENS.get(
        model_name, constants.DEFAULT_CONTEXT_WINDOW_TOKENS
    )


def _get_safe_context_token_budget(provider: str, model_name: str) -> int:
    """Apply a 90% safety margin to the model's context window before truncation."""

    context_tokens = _get_context_window_tokens(model_name)
    safe_tokens = int(context_tokens * constants.CONTEXT_WINDOW_SAFETY_RATIO)

    # Gemini supports 1M tokens; compact earlier for latency/stability.
    if provider == constants.LLM_PROVIDER_GEMINI:
        return min(safe_tokens, GEMINI_COMPACTION_TOKEN_LIMIT)

    return safe_tokens


def _calculate_context_budget(
    provider: str,
    model_name: str,
    is_combat_or_complex: bool = False,
) -> tuple[int, int, int]:
    """
    CENTRALIZED context budget calculation for both truncation and validation.

    This single function ensures truncation and validation use identical logic,
    preventing bugs where content passes truncation but fails validation.

    Args:
        provider: LLM provider name (e.g., 'gemini', 'cerebras')
        model_name: Model identifier
        is_combat_or_complex: Whether combat/complex scenes need extra output reserve

    Returns:
        tuple of (safe_token_budget, output_reserve, max_input_allowed)
        - safe_token_budget: Total safe tokens for this model (90% of context)
        - output_reserve: Tokens reserved for output (20% of safe budget, or combat minimum)
        - max_input_allowed: Maximum tokens allowed for input (80% of safe budget)
    """
    safe_token_budget = _get_safe_context_token_budget(provider, model_name)

    # Use consistent 20% ratio for output reserve
    output_reserve = int(safe_token_budget * OUTPUT_TOKEN_RESERVE_RATIO)

    # For combat/complex scenes, use the larger of ratio-based or fixed reserve
    if is_combat_or_complex:
        output_reserve = max(output_reserve, OUTPUT_TOKEN_RESERVE_COMBAT)

    max_input_allowed = safe_token_budget - output_reserve

    return safe_token_budget, output_reserve, max_input_allowed


def _get_safe_output_token_limit(
    model_name: str,
    prompt_tokens: int,
    system_tokens: int,
) -> int:
    """
    Compute a conservative max_output_tokens based on remaining context.

    - Uses actual model context window (not compaction limit) for output calculation.
    - Compaction limit is only for INPUT compaction decisions, not output budgeting.
    - Reserves 20% of context for output tokens to ensure quality responses.
    - Caps by JSON_MODE_MAX_OUTPUT_TOKENS so we don't exceed API limits.
    """
    # Use actual model context window for output calculation
    # The compaction limit is only for INPUT compaction, not output budgeting
    model_context = constants.MODEL_CONTEXT_WINDOW_TOKENS.get(
        model_name, constants.DEFAULT_CONTEXT_WINDOW_TOKENS
    )
    safe_context = int(model_context * constants.CONTEXT_WINDOW_SAFETY_RATIO)

    # Reserve 20% of context for output tokens
    output_reserve = int(safe_context * OUTPUT_TOKEN_RESERVE_RATIO)
    max_input_allowed = safe_context - output_reserve

    total_input = prompt_tokens + system_tokens
    if total_input > max_input_allowed:
        # Input exceeds 80% of context - not enough room for output
        # Fail fast with a clear error instead of sending a doomed request
        # Use ContextTooLargeError for consistent upstream handling
        raise ContextTooLargeError(
            f"Context too large for model {model_name}: "
            f"input uses {total_input:,} tokens, "
            f"max allowed is {max_input_allowed:,} tokens (80% of {safe_context:,}), "
            f"reserving {output_reserve:,} tokens (20%) for output. "
            "Reduce prompt size or use a model with larger context window.",
            prompt_tokens=total_input,
            completion_tokens=0,
            finish_reason="context_exceeded",
        )

    # Calculate remaining space for output
    raw_remaining = safe_context - total_input
    # Ensure at least the minimum reserve or the remaining context, whichever is larger
    remaining = max(OUTPUT_TOKEN_RESERVE_MIN, raw_remaining)

    model_cap = constants.MODEL_MAX_OUTPUT_TOKENS.get(
        model_name, JSON_MODE_MAX_OUTPUT_TOKENS
    )
    return min(JSON_MODE_MAX_OUTPUT_TOKENS, model_cap, remaining)


def _calculate_prompt_and_system_tokens(
    user_prompt_contents: list[Any],
    system_instruction_text: str | None,
    provider_name: str,
    model_name: str,
) -> tuple[int, int]:
    """Provider-aware token estimation for prompt + system parts."""

    if provider_name != constants.LLM_PROVIDER_GEMINI:
        combined_prompt = " ".join(str(item) for item in user_prompt_contents)
        prompt_tokens = estimate_tokens(combined_prompt)
        system_tokens = estimate_tokens(system_instruction_text or "")
        return prompt_tokens, system_tokens

    # Gemini provider uses API for token counting with fallback to estimation
    try:
        raw_prompt_tokens = gemini_provider.count_tokens(
            model_name, user_prompt_contents
        )
        # Guard against non-numeric returns (e.g., Mock objects in tests)
        user_prompt_tokens = (
            raw_prompt_tokens if isinstance(raw_prompt_tokens, int) else 0
        )
    except Exception:
        # Fallback to estimation if API call fails
        combined_prompt = " ".join(str(item) for item in user_prompt_contents)
        user_prompt_tokens = estimate_tokens(combined_prompt)

    system_tokens = 0
    if system_instruction_text:
        try:
            raw_system_tokens = gemini_provider.count_tokens(
                model_name, [system_instruction_text]
            )
            # Guard against non-numeric returns (e.g., Mock objects in tests)
            system_tokens = (
                raw_system_tokens if isinstance(raw_system_tokens, int) else 0
            )
        except Exception:
            # Fallback to estimation if API call fails
            system_tokens = estimate_tokens(system_instruction_text)

    return user_prompt_tokens, system_tokens


# Fixed turn counts (legacy - used as maximums)
TURNS_TO_KEEP_AT_START: int = 20
TURNS_TO_KEEP_AT_END: int = 20

# =============================================================================
# CONTEXT BUDGET ALLOCATION SYSTEM
# =============================================================================
#
# This system ensures LLM prompts fit within model-specific token limits.
# See docs/context_budget_design.md for full design documentation.
#
# ARCHITECTURE DECISION: NO AUTO-FALLBACK TO LARGER MODELS
# ---------------------------------------------------------
# DO NOT add automatic fallback to larger context models (e.g., Gemini 1M).
# This was explicitly removed in PR #2311. Reasons:
# 1. Cost unpredictability - larger models cost more per token
# 2. Voice inconsistency - different models have different personalities
# 3. Latency variance - larger contexts increase response time
# 4. Proper solution is adaptive truncation, not model switching
#
# If ContextTooLargeError occurs, the solution is to improve truncation,
# not to silently switch models. See bead WA-1 for tracking.
#
# CONTEXT BUDGET HIERARCHY (% of model context window)
# ----------------------------------------------------
# Model Context Window (100%)
# └── Safe Budget (90% - CONTEXT_WINDOW_SAFETY_RATIO)
#     ├── Output Reserve (20% - OUTPUT_TOKEN_RESERVE_RATIO)
#     │   └── Reserved for LLM response generation
#     └── Max Input Allowed (80%)
#         ├── Scaffold (~15-20% of input)
#         │   ├── System instruction (~5-8K tokens)
#         │   ├── Game state JSON (~2-4K tokens)
#         │   ├── Checkpoint block (~1-2K tokens)
#         │   └── Core memories/companions (~2-3K tokens)
#         ├── Entity Tracking Reserve (10.5K tokens fixed)
#         │   ├── entity_preload_text (~2-3K)
#         │   ├── entity_specific_instructions (~1.5-2K)
#         │   └── entity_tracking_instruction (~1-1.5K)
#         └── Story Budget (remaining ~50-60%)
#             ├── Start Turns (25% - STORY_BUDGET_START_RATIO)
#             ├── Middle Compaction (10% - STORY_BUDGET_MIDDLE_RATIO)
#             ├── End Turns (60% - STORY_BUDGET_END_RATIO)
#             └── Truncation marker (5% safety margin)
#
# Middle compaction is implemented via _compact_middle_turns() which extracts
# key events (deaths, level-ups, discoveries) from dropped middle turns.
# =============================================================================

# Percentage-based story budget allocation
# Story budget = available tokens after scaffold and output reserve
# These ratios ensure turns scale with model context size
STORY_BUDGET_START_RATIO: float = 0.25  # 25% of story budget for first turns (context setup)
STORY_BUDGET_MIDDLE_RATIO: float = 0.10  # 10% for compacted middle (key events summary)
STORY_BUDGET_END_RATIO: float = 0.60    # 60% of story budget for recent turns (most important)
# Remaining 5% reserved for truncation marker and safety margin

# Keywords that indicate important events worth preserving in middle compaction
# Organized by category for maintainability
MIDDLE_COMPACTION_KEYWORDS: set[str] = {
    # Combat and conflict (English)
    "attack", "hit", "damage", "kill", "defeat", "victory", "died", "death",
    "combat", "fight", "battle", "wound", "heal", "critical", "strike", "slash",
    "stab", "shoot", "cast", "spell", "miss", "dodge", "block", "parry",
    # Discovery and acquisition
    "discover", "find", "found", "acquire", "obtain", "receive", "gain", "loot",
    "treasure", "gold", "item", "weapon", "armor", "artifact", "key", "unlock",
    "open", "chest", "reward", "coins", "gems", "potion", "scroll", "map",
    # Story progression
    "quest", "mission", "objective", "complete", "accomplish", "learn", "warn",
    "reveal", "secret", "clue", "mystery", "truth", "prophecy", "legend", "oath",
    "promise", "vow", "betray", "deceive", "lie", "confess", "admit",
    # Location and movement
    "arrive", "enter", "leave", "travel", "reach", "escape", "flee", "run",
    "climb", "descend", "cross", "portal", "gate", "door", "passage", "hidden",
    # Character interactions
    "meet", "ally", "join", "hire", "recruit", "dismiss", "farewell", "greet",
    "negotiate", "bargain", "trade", "buy", "sell", "steal", "pickpocket",
    # Major events and mechanics
    "level", "experience", "rest", "camp", "merchant", "shop", "inn", "tavern",
    "save", "rescue", "capture", "imprison", "free", "liberate", "transform",
    # Emotional/dramatic markers
    "suddenly", "finally", "unfortunately", "fortunately", "surprisingly",
    "importantly", "critically", "desperately", "triumphantly",
}

# Regex patterns for importance detection (language-agnostic)
# Pattern for dice rolls (e.g., "d20", "2d6", "1d8+3", "rolls a 15")
DICE_ROLL_PATTERN = re.compile(r'\b\d*d\d+(?:\s*[+\-]\s*\d+)?\b|\brolls?\s+(?:a\s+)?\d+\b', re.IGNORECASE)

# Pattern for numeric results (damage, HP, gold amounts - "15 damage", "50 gold", "-10 HP")
NUMERIC_RESULT_PATTERN = re.compile(r'\b[+\-]?\d+\s*(?:damage|hp|gold|coins|xp|exp|points?|gp|sp|cp)\b', re.IGNORECASE)

# Pattern for quoted dialogue (may contain important information)
DIALOGUE_PATTERN = re.compile(r'"[^"]{20,}"')

# Common abbreviations to avoid splitting on (case-insensitive)
ABBREVIATIONS = {
    "mr", "mrs", "ms", "dr", "prof", "sr", "jr", "vs", "etc", "inc", "ltd",
    "st", "ave", "blvd", "no", "vol", "pg", "pp", "fig", "approx", "dept",
}


def _split_into_sentences(text: str) -> list[str]:
    """
    Split text into sentences, handling abbreviations and decimal numbers.

    This is more robust than simple split on '.!?' because it:
    - Preserves abbreviations like "Dr.", "Mr.", "etc."
    - Preserves decimal numbers like "3.14"
    - Handles multiple punctuation like "..." and "!?"

    Args:
        text: The text to split into sentences

    Returns:
        List of sentence strings
    """
    if not text:
        return []

    sentences = []
    current = []
    words = text.split()

    for i, word in enumerate(words):
        current.append(word)

        # Check if this word ends a sentence
        if word and word[-1] in '.!?':
            # Check if it's an abbreviation (word without punctuation, lowercase)
            word_base = word.rstrip('.!?').lower()

            # Don't split on abbreviations
            if word_base in ABBREVIATIONS:
                continue

            # Don't split on single letters followed by period (initials like "J.")
            if len(word_base) == 1 and word.endswith('.'):
                continue

            # Don't split on numbers (decimal numbers like "3.14")
            if word_base.replace('.', '').replace(',', '').isdigit():
                continue

            # This looks like a real sentence ending
            sentence = ' '.join(current).strip()
            if len(sentence) > 10:  # Minimum sentence length
                sentences.append(sentence)
            current = []

    # Add any remaining text as final sentence
    if current:
        sentence = ' '.join(current).strip()
        if len(sentence) > 10:
            sentences.append(sentence)

    return sentences


def _is_important_sentence(sentence: str) -> bool:
    """
    Determine if a sentence is important using keywords AND patterns.

    This is more robust than keyword-only matching because it also detects:
    - Dice rolls (language-agnostic game mechanics)
    - Numeric results (damage, gold, HP changes)
    - Long quoted dialogue (often contains important information)
    - Exclamatory sentences (often dramatic moments)

    Args:
        sentence: The sentence to evaluate

    Returns:
        True if the sentence appears important
    """
    sentence_lower = sentence.lower()

    # Check for keywords (fast path)
    if any(kw in sentence_lower for kw in MIDDLE_COMPACTION_KEYWORDS):
        return True

    # Check for dice roll patterns (language-agnostic)
    if DICE_ROLL_PATTERN.search(sentence):
        return True

    # Check for numeric results (damage, gold, etc.)
    if NUMERIC_RESULT_PATTERN.search(sentence):
        return True

    # Check for significant dialogue (long quoted text)
    if DIALOGUE_PATTERN.search(sentence):
        return True

    # Exclamatory sentences are often important dramatic moments
    if sentence.rstrip().endswith('!') and len(sentence) > 30:
        return True

    return False

SAFETY_SETTINGS: list[types.SafetySetting] = [
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=types.HarmBlockThreshold.BLOCK_NONE,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=types.HarmBlockThreshold.BLOCK_NONE,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=types.HarmBlockThreshold.BLOCK_NONE,
    ),
    types.SafetySetting(
        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=types.HarmBlockThreshold.BLOCK_NONE,
    ),
]

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
}

# --- END CONSTANTS ---

# Store loaded instruction content in a dictionary for easy access
_loaded_instructions_cache: dict[str, str] = {}


def _clear_client() -> None:
    """FOR TESTING ONLY: Clears the cached Gemini client."""
    gemini_provider.clear_cached_client()


def _load_instruction_file(instruction_type: str) -> str:
    """
    Loads a prompt instruction file from the 'prompts' directory.
    This function is now strict: it will raise an exception if a file
    cannot be found, ensuring the application does not continue with
    incomplete instructions.
    """
    global _loaded_instructions_cache
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
    else:
        pass

    return _loaded_instructions_cache[instruction_type]


def get_client():
    """Initializes and returns a singleton Gemini client."""
    return gemini_provider.get_client()


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
            temporal_enforcement +
            "**CRITICAL REMINDER FOR STORY CONTINUATION**\n"
            "1. **MANDATORY PLANNING BLOCK**: Every STORY MODE response MUST end with '--- PLANNING BLOCK ---'\n"
            "2. **Think Commands**: If the user says 'think', 'plan', 'consider', 'strategize', or 'options', "
            "generate ONLY internal thoughts with a deep think block. Each choice MUST have an 'analysis' field with 'pros' array, 'cons' array, and 'confidence' string. DO NOT take narrative actions.\n"
            "3. **Standard Responses**: All other responses should include narrative continuation followed by "
            "a standard planning block with 3-4 action options.\n"
            "4. **Never Skip**: The planning block is MANDATORY - never end a response without one.\n\n"
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


def _prepare_entity_tracking(
    game_state: GameState, story_context: list[dict[str, Any]], session_number: int
) -> tuple[str, list[str], str]:
    """
    Prepare entity tracking manifest and expected entities.

    Args:
        game_state: Current GameState object
        story_context: List of story context entries
        session_number: Current session number

    Returns:
        tuple: (entity_manifest_text, expected_entities, entity_tracking_instruction)
    """
    # Extract turn number from story context
    turn_number: int = len(story_context) + 1

    # Create entity manifest from current game state (with basic caching)
    game_state_dict: dict[str, Any] = game_state.to_dict()
    manifest_cache_key = f"manifest_{session_number}_{turn_number}_{hash(str(sorted(game_state_dict.get('npc_data', {}).items())))}"

    # Simple in-memory cache for the request duration
    if not hasattr(game_state, "_manifest_cache"):
        game_state._manifest_cache = {}

    if manifest_cache_key in game_state._manifest_cache:
        entity_manifest = game_state._manifest_cache[manifest_cache_key]
        logging_util.debug("Using cached entity manifest")
    else:
        entity_manifest = create_from_game_state(
            game_state_dict, session_number, turn_number
        )
        game_state._manifest_cache[manifest_cache_key] = entity_manifest
        logging_util.debug("Created new entity manifest")

    if entity_manifest is None:
        # CI safety: some test fixtures can yield a None manifest; skip entity tracking in that case
        logging_util.warning(
            "Entity manifest generation returned None; skipping entity tracking for this turn"
        )
        entity_manifest_text = ""
        expected_entities: list[str] = []
    else:
        try:
            entity_manifest_text = entity_manifest.to_prompt_format()
        except Exception as e:
            logging_util.error(f"Entity manifest to_prompt_format() failed: {e}")
            entity_manifest_text = ""

        try:
            expected_entities = entity_manifest.get_expected_entities() or []
        except Exception as e:
            logging_util.error(f"Entity manifest get_expected_entities() failed: {e}")
            expected_entities = []

    # Always add structured response format instruction (for both entity tracking and general JSON response)
    entity_tracking_instruction = create_structured_prompt_injection(
        entity_manifest_text, expected_entities
    )

    return entity_manifest_text, expected_entities, entity_tracking_instruction


def _build_timeline_log(story_context: list[dict[str, Any]]) -> str:
    """
    Build the timeline log string from story context.

    Args:
        story_context: List of story context entries

    Returns:
        str: Formatted timeline log
    """
    timeline_log_parts = []
    for entry in story_context:
        actor_label = (
            "Story"
            if entry.get(constants.KEY_ACTOR) == constants.ACTOR_GEMINI
            else "You"
        )
        seq_id = entry.get("sequence_id", "N/A")
        timeline_log_parts.append(
            f"[SEQ_ID: {seq_id}] {actor_label}: {entry.get(constants.KEY_TEXT)}"
        )

    return "\n\n".join(timeline_log_parts)


def _build_continuation_prompt(
    checkpoint_block: str,
    core_memories_summary: str,
    sequence_id_list_string: str,
    serialized_game_state: str,
    entity_tracking_instruction: str,
    timeline_log_string: str,
    current_prompt_text: str,
) -> str:
    """
    Build the full continuation prompt.

    Returns:
        str: Complete prompt for continuation
    """
    return (
        f"{checkpoint_block}\\n\\n"
        f"{core_memories_summary}"
        f"REFERENCE TIMELINE (SEQUENCE ID LIST):\\n[{sequence_id_list_string}]\\n\\n"
        f"CURRENT GAME STATE:\\n{serialized_game_state}\\n\\n"
        f"{entity_tracking_instruction}"
        f"TIMELINE LOG (FOR CONTEXT):\\n{timeline_log_string}\\n\\n"
        f"YOUR TURN:\\n{current_prompt_text}"
    )


def _select_model_for_continuation(_user_input_count: int) -> str:
    """
    Select the appropriate model based on testing mode and input count.

    Args:
        user_input_count: Number of user inputs so far

    Returns:
        str: Model name to use
    """
    # Use test model in mock services mode for faster/cheaper testing
    mock_mode = os.environ.get("MOCK_SERVICES_MODE") == "true"
    if mock_mode:
        return TEST_MODEL
    return DEFAULT_MODEL


def _parse_gemini_response(
    raw_response_text: str, context: str = "general"
) -> tuple[str, NarrativeResponse | None]:
    """
    Centralized JSON parsing logic for all Gemini responses.
    Handles JSON extraction, parsing, and fallback logic.

    Args:
        raw_response_text: Raw text from Gemini API
        context: Context of the parse ("general", "planning_block", etc.)

    Returns:
        tuple: (narrative_text, structured_data) where:
               - narrative_text is clean text for display
               - structured_data is parsed data (NarrativeResponse or None)
    """
    # Log raw response for debugging
    logging_util.debug(f"[{context}] Raw Gemini response: {raw_response_text[:500]}...")

    # Use the existing robust parsing logic
    response_text, structured_response = parse_structured_response(raw_response_text)

    return response_text, structured_response


def _process_structured_response(
    raw_response_text: str, expected_entities: list[str]
) -> tuple[str, NarrativeResponse | None]:
    """
    Process structured JSON response and validate entity coverage.

    Args:
        raw_response_text: Raw response from API
        expected_entities: List of expected entity names

    Returns:
        tuple: (response_text, structured_response) where structured_response is NarrativeResponse or None
    """
    # Use centralized parsing logic
    response_text, structured_response = _parse_gemini_response(
        raw_response_text, context="structured_response"
    )

    # Validate structured response coverage
    if isinstance(structured_response, NarrativeResponse):
        coverage_validation = validate_entity_coverage(
            structured_response, expected_entities
        )
        logging_util.info(
            f"STRUCTURED_GENERATION: Coverage rate {coverage_validation['coverage_rate']:.2f}, "
            f"Schema valid: {coverage_validation['schema_valid']}"
        )

        if not coverage_validation["schema_valid"]:
            logging_util.warning(
                f"STRUCTURED_GENERATION: Missing from schema: {coverage_validation['missing_from_schema']}"
            )

        # State updates are now handled via structured_response object only
        # Legacy STATE_UPDATES_PROPOSED text blocks are no longer used in JSON mode
    else:
        logging_util.warning(
            "STRUCTURED_GENERATION: Failed to parse JSON response, falling back to plain text"
        )

    return response_text, structured_response


def _validate_entity_tracking(
    response_text: str, expected_entities: list[str], game_state: GameState
) -> str:
    """
    Validate that the narrative includes all expected entities.

    Args:
        response_text: Generated narrative text
        expected_entities: List of expected entity names
        game_state: Current GameState object

    Returns:
        str: Response text with debug validation if in debug mode
    """
    validator = NarrativeSyncValidator()
    validation_result = validator.validate(
        narrative_text=response_text,
        expected_entities=expected_entities,
        location=game_state.world_data.get("current_location_name", "Unknown"),
    )

    if not validation_result.all_entities_present:
        logging_util.warning(
            "ENTITY_TRACKING_VALIDATION: Narrative failed entity validation"
        )
        logging_util.warning(f"Missing entities: {validation_result.entities_missing}")
        if validation_result.warnings:
            for warning in validation_result.warnings:
                logging_util.warning(f"Validation warning: {warning}")

    # Debug validation is now handled via structured_response.debug_info
    # No longer append debug content to narrative text in JSON mode

    return response_text


def _log_token_count(
    model_name: str,
    user_prompt_contents: list[Any],
    system_instruction_text: str | None = None,
    provider_name: str = constants.DEFAULT_LLM_PROVIDER,
) -> None:
    """Helper function to count and log the number of tokens being sent, with a breakdown.

    Also warns when approaching output token limits to prevent truncation issues.
    """
    try:
        prompt_tokens, system_tokens = _calculate_prompt_and_system_tokens(
            user_prompt_contents, system_instruction_text, provider_name, model_name
        )
        total_tokens = prompt_tokens + system_tokens

        current_output_limit = _get_safe_output_token_limit(
            model_name, prompt_tokens, system_tokens
        )
        logging_util.debug(
            f"🔍 TOKEN_ANALYSIS: Sending {total_tokens} input tokens to API (Prompt: {prompt_tokens or 0}, System: {system_tokens or 0})"
        )
        logging_util.debug(
            f"🔍 TOKEN_LIMITS: Output limit set to {current_output_limit} tokens (conservative limit, API max: 65535)"
        )

        model_info_msg = f"🔍 MODEL_INFO: Using provider '{provider_name}', model '{model_name}'"
        logging_util.info(model_info_msg)

    except Exception as e:
        logging_util.warning(f"Could not count tokens before API call: {e}")


def _call_llm_api_with_llm_request(
    gemini_request: LLMRequest,
    model_name: str,
    system_instruction_text: str | None = None,
    provider_name: str = constants.DEFAULT_LLM_PROVIDER,
) -> Any:
    """
    Calls LLM API with structured JSON from LLMRequest.

    This function sends the JSON structure to Gemini API as a formatted string.
    The Gemini API expects string content, so we convert the structured data
    to a JSON string for proper communication.

    Args:
        gemini_request: LLMRequest object with structured data
        model_name: Model to use for API call
        system_instruction_text: System instructions (optional)

    Returns:
        Gemini API response object

    Raises:
        TypeError: If parameters are of incorrect type
        ValueError: If parameters are invalid
        LLMRequestError: If LLMRequest validation fails
    """
    # Input validation - critical for API stability
    if gemini_request is None:
        raise TypeError("gemini_request cannot be None")

    if not isinstance(gemini_request, LLMRequest):
        raise TypeError(
            f"gemini_request must be LLMRequest instance, got {type(gemini_request)}"
        )

    if not model_name or not isinstance(model_name, str):
        raise ValueError(
            f"model_name must be non-empty string, got {type(model_name)}: {model_name}"
        )

    if system_instruction_text is not None and not isinstance(
        system_instruction_text, str
    ):
        raise TypeError(
            f"system_instruction_text must be string or None, got {type(system_instruction_text)}"
        )

    # Log validation success for debugging
    logging_util.debug(
        f"Input validation passed for LLMRequest with user_id: {gemini_request.user_id}, "
        f"model: {model_name}"
    )

    # Convert LLMRequest to JSON for API call
    try:
        json_data = gemini_request.to_json()
    except Exception as e:
        logging_util.error(f"Failed to convert LLMRequest to JSON: {e}")
        raise ValueError(f"LLMRequest serialization failed: {e}") from e

    # Validate JSON data structure before API call
    if not isinstance(json_data, dict):
        raise ValueError(
            f"Expected dict from LLMRequest.to_json(), got {type(json_data)}"
        )

    # Ensure critical fields are present
    required_fields = ["user_action", "game_mode", "user_id"]
    missing_fields = [field for field in required_fields if field not in json_data]
    if missing_fields:
        raise ValueError(f"Missing required fields in JSON data: {missing_fields}")

    logging_util.debug(f"JSON validation passed with {len(json_data)} fields")

    # Convert JSON dict to formatted string for Gemini API
    # The API expects string content, not raw dicts
    # Uses centralized json_default_serializer from mvp_site.serialization
    json_string = json.dumps(json_data, indent=2, default=json_default_serializer)

    # Send the structured JSON as string to the API
    return _call_llm_api(
        [json_string],  # Send JSON as formatted string
        model_name,
        f"LLMRequest: {gemini_request.user_action[:100]}...",  # Logging
        system_instruction_text,
        provider_name,
    )


def _call_llm_api(
    prompt_contents: list[Any],
    model_name: str,
    current_prompt_text_for_logging: str | None = None,
    system_instruction_text: str | None = None,
    provider_name: str = constants.DEFAULT_LLM_PROVIDER,
) -> Any:
    """
    Calls the configured LLM provider.

    Args:
        prompt_contents: The content to send to the API
        model_name: Primary model to use
        current_prompt_text_for_logging: Text for logging purposes (optional)
        system_instruction_text: System instructions (optional)
        provider_name: LLM provider name (gemini, openrouter, cerebras)

    Returns:
        Provider-specific response object (Gemini, OpenRouter, or Cerebras)
    """
    if current_prompt_text_for_logging:
        logging_util.info(
            f"Calling LLM API with prompt: {str(current_prompt_text_for_logging)[:500]}..."
        )

    # Log token estimate for prompt
    all_prompt_text = []
    for p in prompt_contents:
        if isinstance(p, str):
            all_prompt_text.append(p)
        elif isinstance(p, dict):
            # Handle JSON data for logging purposes
            all_prompt_text.append(f"JSON({len(str(p))} chars)")

    if system_instruction_text:
        all_prompt_text.append(system_instruction_text)

    combined_text = " ".join(all_prompt_text)
    log_with_tokens("Calling LLM API", combined_text, logging_util)

    current_selection = ProviderSelection(provider_name, model_name)
    try:
        prompt_tokens, system_tokens = _calculate_prompt_and_system_tokens(
            prompt_contents, system_instruction_text, provider_name, model_name
        )
        _log_token_count(
            model_name,
            prompt_contents,
            system_instruction_text,
            provider_name,
        )

        logging_util.info(
            f"Calling LLM provider/model: {provider_name}/{model_name}"
        )

        safe_output_limit = _get_safe_output_token_limit(
            model_name,
            prompt_tokens,
            system_tokens,
        )

        # DIAGNOSTIC: Log which provider branch we're about to execute
        logging_util.info(
            f"🔍 CALL_LLM_API_DISPATCH: provider_name={provider_name}, "
            f"model_name={model_name}, "
            f"is_gemini={provider_name == constants.LLM_PROVIDER_GEMINI}, "
            f"is_cerebras={provider_name == constants.LLM_PROVIDER_CEREBRAS}, "
            f"is_openrouter={provider_name == constants.LLM_PROVIDER_OPENROUTER}"
        )

        if provider_name == constants.LLM_PROVIDER_GEMINI:
            logging_util.info(
                "🔍 CALL_LLM_API_GEMINI: Calling gemini_provider.generate_json_mode_content"
            )
            return gemini_provider.generate_json_mode_content(
                prompt_contents=prompt_contents,
                model_name=model_name,
                system_instruction_text=system_instruction_text,
                max_output_tokens=safe_output_limit,
                temperature=TEMPERATURE,
                safety_settings=SAFETY_SETTINGS,
                json_mode_max_output_tokens=safe_output_limit,
            )
        if provider_name == constants.LLM_PROVIDER_OPENROUTER:
            return openrouter_provider.generate_content(
                prompt_contents=prompt_contents,
                model_name=model_name,
                system_instruction_text=system_instruction_text,
                temperature=TEMPERATURE,
                max_output_tokens=safe_output_limit,
            )
        if provider_name == constants.LLM_PROVIDER_CEREBRAS:
            logging_util.info(
                "🔍 CALL_LLM_API_CEREBRAS: Calling cerebras_provider.generate_content"
            )
            return cerebras_provider.generate_content(
                prompt_contents=prompt_contents,
                model_name=model_name,
                system_instruction_text=system_instruction_text,
                temperature=TEMPERATURE,
                max_output_tokens=safe_output_limit,
            )
        logging_util.error(
            f"🔍 CALL_LLM_API_UNSUPPORTED: provider_name={provider_name} is not supported!"
        )
        raise ValueError(f"Unsupported provider: {provider_name}")
    except ContextTooLargeError as e:
        logging_util.error(
            "Context too large for selected model. "
            "Reduce prompt size or choose a model with a larger context window."
        )
        raise LLMRequestError(str(e), status_code=422) from e
    except ValueError as e:
        message = str(e)
        if "context" in message.lower() or "too large" in message.lower():
            raise LLMRequestError(message, status_code=422) from e
        raise
    except Exception as e:
        error_message = str(e)
        status_code = None

        if hasattr(e, "status_code"):
            status_code = e.status_code
        elif hasattr(e, "response") and hasattr(e.response, "status_code"):
            status_code = e.response.status_code
        elif "503" in error_message:
            status_code = 503
        elif "429" in error_message:
            status_code = 429

        if status_code in (503, 429):
            human_reason = "service unavailable" if status_code == 503 else "rate limited"
            logging_util.error(
                f"Provider {current_selection.provider}/{current_selection.model} {human_reason}: {error_message}"
            )
            raise LLMRequestError(
                f"LLM provider error ({status_code}): {human_reason}. Please try again shortly.",
                status_code=status_code,
            ) from e

        logging_util.error(
            f"🔥🔴 Non-recoverable error with model {current_selection.model}: {e}"
        )
        raise


def _call_llm_api_with_json_structure(
    json_input: dict[str, Any],
    model_name: str,
    system_instruction_text: str | None = None,
    provider_name: str = constants.DEFAULT_LLM_PROVIDER,
) -> Any:
    """
    Core function that handles structured JSON input to Gemini API.

    This function receives structured JSON and formats it as structured
    prompt content that preserves the field separation, rather than
    concatenating everything into a single string blob.

    Args:
        json_input: Validated structured JSON input
        model_name: Primary model to try first
        system_instruction_text: System instructions (optional)

    Returns:
        Gemini API response object
    """
    # Format the structured JSON as a clear, structured prompt
    # This maintains field separation while being readable by the LLM
    message_type = json_input.get("message_type", "")

    if message_type == "story_continuation":
        # Format story continuation with clear field separation
        context = json_input.get("context", {})
        structured_prompt = [
            f"MESSAGE_TYPE: {message_type}",
            f"USER_ACTION: {json_input.get('user_action', '')}",
            f"GAME_MODE: {json_input.get('game_mode', '')}",
            f"USER_ID: {context.get('user_id', '')}",
            f"GAME_STATE: {json.dumps(context.get('game_state', {}), indent=2, default=json_default_serializer)}",
            f"STORY_HISTORY: {json.dumps(context.get('story_history', []), indent=2, default=json_default_serializer)}",
            f"ENTITY_TRACKING: {json.dumps(context.get('entity_tracking', {}), indent=2, default=json_default_serializer)}",
            f"SELECTED_PROMPTS: {json.dumps(context.get('selected_prompts', []), default=json_default_serializer)}",
            f"CHECKPOINT_BLOCK: {context.get('checkpoint_block', '')}",
            f"CORE_MEMORIES: {json.dumps(context.get('core_memories', []), default=json_default_serializer)}",
        ]
        prompt_content = "\n\n".join(structured_prompt)
    elif message_type == "user_input":
        # Format user input with clear structure
        context = json_input.get("context", {})
        structured_prompt = [
            f"MESSAGE_TYPE: {message_type}",
            f"CONTENT: {json_input.get('content', '')}",
            f"GAME_MODE: {context.get('game_mode', '')}",
            f"USER_ID: {context.get('user_id', '')}",
        ]
        prompt_content = "\n\n".join(structured_prompt)
    elif message_type == "system_instruction":
        # Format system instruction with clear structure
        context = json_input.get("context", {})
        structured_prompt = [
            f"MESSAGE_TYPE: {message_type}",
            f"CONTENT: {json_input.get('content', '')}",
            f"INSTRUCTION_TYPE: {context.get('instruction_type', '')}",
        ]
        if context.get("game_state"):
            structured_prompt.append(
                f"GAME_STATE: {json.dumps(context['game_state'], indent=2)}"
            )
        prompt_content = "\n\n".join(structured_prompt)
    else:
        # Fallback: use JSON structure as-is
        prompt_content = json.dumps(json_input, indent=2)

    # Call the existing API with structured content
    return _call_llm_api(
        [prompt_content],
        model_name,
        f"Structured JSON: {message_type}",  # for logging
        system_instruction_text,
        provider_name,
    )


def _call_llm_api_with_structured_json(
    json_input: dict[str, Any],
    model_name: str,
    system_instruction_text: str | None = None,
    provider_name: str = constants.DEFAULT_LLM_PROVIDER,
) -> Any:
    """
    LEGACY: Call Gemini API using structured JSON input (DEPRECATED).

    NOTE: This function is deprecated. New code should use LLMRequest class
    with _call_llm_api_with_llm_request() instead.

    This function remains for backward compatibility with existing tests.

    Args:
        json_input: Structured JSON input (legacy JsonInputBuilder format)
        model_name: Primary model to try first
        system_instruction_text: System instructions (optional)

    Returns:
        Gemini API response object
    """
    # LEGACY: JsonInputBuilder removed - using direct JSON
    # Legacy json_input_schema removed - using LLMRequest now

    # Direct JSON usage (no additional validation needed)
    validated_json = json_input

    # Pass structured JSON to the new handler
    return _call_llm_api_with_json_structure(
        validated_json,
        model_name,
        system_instruction_text=system_instruction_text,
        provider_name=provider_name,
    )


def _call_llm_api_with_json_schema(
    content: str,
    message_type: str,
    model_name: str,
    user_id: str | None = None,
    game_mode: str | None = None,
    game_state: dict[str, Any] | None = None,
    system_instruction_text: str | None = None,
) -> Any:
    """
    LEGACY: Call Gemini API using structured JSON input schema (DEPRECATED).

    NOTE: This function is deprecated. New code should use LLMRequest class
    with _call_llm_api_with_llm_request() instead.

    This function remains for backward compatibility with existing tests.

    Args:
        content: The main content/prompt text
        message_type: Type of message (user_input, system_instruction, etc.)
        model_name: Primary model to try first
        user_id: User identifier (required for user_input)
        game_mode: Game mode (required for user_input)
        game_state: Game state context (optional)
        system_instruction_text: System instructions (optional)

    Returns:
        Gemini API response object with JSON response
    """
    # LEGACY: JsonInputBuilder removed - using direct JSON
    # Legacy json_input_schema removed - using LLMRequest now

    # Build structured JSON input based on message type
    if message_type == "user_input":
        if not user_id or not game_mode:
            raise ValueError("user_id and game_mode required for user_input messages")
        json_input = {
            "message_type": "user_input",
            "content": content,
            "context": {"game_mode": game_mode, "user_id": user_id},
        }
    elif message_type == "system_instruction":
        json_input = {
            "message_type": "system_instruction",
            "content": content,
            "context": {
                "instruction_type": "base_system",
                "game_state": game_state or {},
            },
        }
    elif message_type == "story_continuation":
        json_input = {
            "message_type": "story_continuation",
            "content": content,
            "context": {"checkpoint_block": "", "timeline_log": [], "sequence_id": ""},
        }
    else:
        # For unknown message types, use basic structure that bypasses validation
        # by directly formatting for Gemini API without JSON schema validation
        return _call_llm_api(
            [content],  # Direct string content bypass
            model_name,
            content,  # for logging
            system_instruction_text,
        )

    # NEW APPROACH: Use structured JSON directly instead of string conversion
    return _call_llm_api_with_structured_json(
        json_input,
        model_name,
        system_instruction_text,
    )
def _get_text_from_response(response: Any) -> str:
    """Safely extracts text from a Gemini response object."""
    try:
        if response.text:
            return response.text
    except ValueError as e:
        logging_util.warning(f"ValueError while extracting text: {e}")
    except Exception as e:
        logging_util.error(f"Unexpected error in _get_text_from_response: {e}")

    logging_util.warning(
        f"Response did not contain valid text. Response object: {response}"
    )
    return "[System Message: The model returned a non-text response. Please check the logs for details.]"


def _get_context_stats(
    context: list[dict[str, Any]],
    model_name: str,
    current_game_state: GameState,
    provider_name: str = constants.DEFAULT_LLM_PROVIDER,
) -> str:
    """Helper to calculate and format statistics for a given story context."""
    if not context:
        return "Turns: 0, Tokens: 0"

    combined_text = "".join(entry.get(constants.KEY_TEXT, "") for entry in context)
    estimated_tokens = estimate_tokens(combined_text)

    # Try to get exact token count via API, fall back to estimate
    actual_tokens = "N/A"
    try:
        if provider_name == constants.LLM_PROVIDER_GEMINI:
            text_contents = [entry.get(constants.KEY_TEXT, "") for entry in context]
            actual_tokens = gemini_provider.count_tokens(model_name, text_contents)
        else:
            actual_tokens = estimated_tokens
    except Exception as e:
        logging_util.warning(f"Could not count tokens for context stats: {e}")
        actual_tokens = estimated_tokens  # Fall back to estimate

    all_core_memories = current_game_state.custom_campaign_state.get(
        "core_memories", []
    )
    stats_string = f"Turns: {len(context)}, Tokens: {actual_tokens} (est: {estimated_tokens}), Core Memories: {len(all_core_memories)}"

    if all_core_memories:
        last_three = all_core_memories[-3:]
        stats_string += "\\n--- Last 3 Core Memories ---\\n"
        for i, memory in enumerate(last_three, 1):
            stats_string += (
                f"  {len(all_core_memories) - len(last_three) + i}: {memory}\\n"
            )
        stats_string += "--------------------------"

    return stats_string


def _calculate_percentage_based_turns(
    story_context: list[dict[str, Any]],
    max_tokens: int,
) -> tuple[int, int]:
    """
    Calculate how many turns to keep based on percentage of story budget.

    Uses STORY_BUDGET_START_RATIO (25%), STORY_BUDGET_MIDDLE_RATIO (10%),
    and STORY_BUDGET_END_RATIO (60%) to allocate tokens proportionally,
    then converts to turn counts. Middle turns are compacted separately.

    Args:
        story_context: Full story context to analyze
        max_tokens: Maximum tokens available for story

    Returns:
        (start_turns, end_turns) tuple based on percentage allocation
    """
    total_turns = len(story_context)
    if total_turns == 0:
        return (0, 0)

    # Calculate average tokens per turn
    combined_text = "".join(
        entry.get(constants.KEY_TEXT, "") for entry in story_context
    )
    total_story_tokens = estimate_tokens(combined_text)
    if total_story_tokens <= 0 or total_turns <= 0:
        # Fallback average when text is empty or invalid; keeps math safe.
        avg_tokens_per_turn = 500
    else:
        avg_tokens_per_turn = total_story_tokens / total_turns

    # Calculate token budgets for start and end
    start_token_budget = int(max_tokens * STORY_BUDGET_START_RATIO)
    end_token_budget = int(max_tokens * STORY_BUDGET_END_RATIO)

    # Convert to turn counts (cap at legacy maximums for safety)
    raw_start_turns = min(
        int(start_token_budget / avg_tokens_per_turn),
        TURNS_TO_KEEP_AT_START,
        total_turns // 2,  # Never take more than half for start
    )

    # Apply start minimum but never exceed total turns
    start_turns = min(max(3, raw_start_turns), total_turns)

    raw_end_turns = min(
        int(end_token_budget / avg_tokens_per_turn),
        TURNS_TO_KEEP_AT_END,
    )
    desired_end_turns = max(5, raw_end_turns) if total_turns >= 5 else min(total_turns, raw_end_turns)

    # Enforce non-overlap using the post-minimum start_turns value
    remaining_turns = max(0, total_turns - start_turns)
    end_turns = min(desired_end_turns, remaining_turns)

    # Final safety: if minimums still force overlap, trim the start portion first
    if start_turns + end_turns > total_turns:
        end_turns = max(0, total_turns - start_turns)

    logging_util.info(
        f"📊 PERCENTAGE-BASED TURNS: avg_tokens/turn={avg_tokens_per_turn:.0f}, "
        f"start_budget={start_token_budget}tk→{start_turns} turns (25%), "
        f"end_budget={end_token_budget}tk→{end_turns} turns (60%), "
        f"middle_budget={int(max_tokens * STORY_BUDGET_MIDDLE_RATIO)}tk (10% for compaction)"
    )

    return (start_turns, end_turns)


def _compact_middle_turns(
    middle_turns: list[dict[str, Any]],
    max_tokens: int,
) -> dict[str, Any]:
    """
    Compact middle turns into a summary preserving key events.

    Instead of completely dropping middle turns, extract important sentences
    using multiple detection methods:
    1. Keyword matching (expanded set with action verbs, story markers)
    2. Pattern matching (dice rolls, damage numbers - language-agnostic)
    3. Structural markers (dialogue, exclamations)
    4. Fallback sampling (when no important sentences found)

    The sentence splitting is robust against abbreviations (Dr., Mr.) and
    decimal numbers (3.14, 2.5).

    Args:
        middle_turns: The turns being dropped from the middle section
        max_tokens: Maximum tokens allowed for the compacted summary

    Returns:
        A system message containing the compacted middle summary
    """
    if not middle_turns:
        return {
            "actor": "system",
            "text": "[...time passes...]",
        }

    # Extract important sentences from middle turns
    important_events: list[str] = []
    all_sentences: list[str] = []  # For fallback sampling
    total_tokens = 0

    # Reserve tokens for formatting overhead (header + footer + bullets buffer)
    FORMATTING_OVERHEAD = 30
    effective_max_tokens = max(10, max_tokens - FORMATTING_OVERHEAD)

    for turn in middle_turns:
        text = turn.get(constants.KEY_TEXT, "")
        if not text:
            continue

        # Use robust sentence splitting (handles abbreviations, decimals)
        sentences = _split_into_sentences(text)
        all_sentences.extend(sentences)

        # Check each sentence for importance using keywords AND patterns
        for sentence in sentences:
            if _is_important_sentence(sentence):
                sentence_tokens = estimate_tokens(sentence)
                if total_tokens + sentence_tokens <= effective_max_tokens:
                    important_events.append(sentence)
                    total_tokens += sentence_tokens
                else:
                    # Reached token limit
                    break

        if total_tokens >= effective_max_tokens:
            break

    # Fallback: If no important events found, sample evenly from all sentences
    if not important_events and all_sentences:
        # Sample every Nth sentence to get representative coverage
        sample_count = min(5, len(all_sentences))
        if sample_count > 0:
            step = max(1, len(all_sentences) // sample_count)
            sampled = all_sentences[::step][:sample_count]

            for sentence in sampled:
                sentence_tokens = estimate_tokens(sentence)
                if total_tokens + sentence_tokens <= effective_max_tokens:
                    important_events.append(sentence)
                    total_tokens += sentence_tokens

    # Format the compacted summary
    unique_events: list[str] = []  # Initialize for post-format budget check
    if important_events:
        # Deduplicate while preserving order
        seen: set[str] = set()
        for event in important_events:
            # Normalize for dedup (lowercase, strip)
            normalized = event.lower().strip()
            if normalized not in seen:
                seen.add(normalized)
                unique_events.append(event)

        # Limit to reasonable number of events
        max_events = 15
        if len(unique_events) > max_events:
            unique_events = unique_events[:max_events]

        summary_text = (
            "[...time passes, and these key events occurred...]\n\n"
            + "\n".join(f"- {event}" for event in unique_events)
            + "\n\n[...the story continues from the most recent events...]"
        )
    else:
        # No sentences at all - use minimal marker
        summary_text = (
            f"[...{len(middle_turns)} turns of exploration and conversation passed...]\n"
            "[...the story continues from the most recent events...]"
        )

    # FIX Bug 3: Post-format budget verification
    # Ensure the formatted output actually fits in the budget
    actual_tokens = estimate_tokens(summary_text)
    if actual_tokens > max_tokens:
        logging_util.warning(
            f"Middle compaction exceeded budget: {actual_tokens} > {max_tokens} tokens. Trimming events."
        )
        # Progressively remove events until we fit
        while unique_events and actual_tokens > max_tokens:
            unique_events.pop()  # Remove last event
            if unique_events:
                summary_text = (
                    "[...time passes, and these key events occurred...]\n\n"
                    + "\n".join(f"- {event}" for event in unique_events)
                    + "\n\n[...the story continues from the most recent events...]"
                )
            else:
                # All events removed - use minimal marker
                summary_text = (
                    f"[...{len(middle_turns)} turns passed...]\n"
                    "[...the story continues...]"
                )
            actual_tokens = estimate_tokens(summary_text)

    logging_util.info(
        f"📊 MIDDLE COMPACTION: {len(middle_turns)} turns → "
        f"{len(important_events)} key events, {actual_tokens} tokens (budget: {max_tokens})"
    )

    return {
        "actor": "system",
        "text": summary_text,
    }


def _truncate_context(
    story_context: list[dict[str, Any]],
    max_chars: int,
    model_name: str,
    current_game_state: GameState,
    provider_name: str = constants.DEFAULT_LLM_PROVIDER,
    turns_to_keep_at_start: int = TURNS_TO_KEEP_AT_START,
    turns_to_keep_at_end: int = TURNS_TO_KEEP_AT_END,
) -> list[dict[str, Any]]:
    """
    Intelligently truncates the story context to fit within a given character budget.

    PERCENTAGE-BASED TRUNCATION: Uses 25%/10%/60% ratio for start/middle/end allocation.
    ADAPTIVE FALLBACK: If initial allocation still exceeds budget, iteratively
    reduces turn count until it fits.
    HARD-TRIM GUARANTEE: If even minimum turns exceed budget, text is hard-trimmed
    to guarantee the result fits within budget.
    """
    initial_stats = _get_context_stats(
        story_context, model_name, current_game_state, provider_name
    )
    logging_util.info(f"Initial context stats: {initial_stats}")

    combined_text = "".join(
        entry.get(constants.KEY_TEXT, "") for entry in story_context
    )
    current_tokens = estimate_tokens(combined_text)
    max_tokens = estimate_tokens(
        " " * max_chars
    )  # Convert char budget to token budget using estimate_tokens

    if current_tokens <= max_tokens:
        logging_util.info("Context is within token budget. No truncation needed.")
        return story_context

    logging_util.warning(
        f"Context ({current_tokens} tokens) exceeds budget of {max_tokens} tokens. Truncating..."
    )

    total_turns = len(story_context)

    # Calculate percentage-based turn limits instead of using fixed counts
    pct_start, pct_end = _calculate_percentage_based_turns(story_context, max_tokens)
    turns_to_keep_at_start = min(turns_to_keep_at_start, pct_start)
    turns_to_keep_at_end = min(turns_to_keep_at_end, pct_end)

    if total_turns <= turns_to_keep_at_start + turns_to_keep_at_end:
        # Few turns - but still need to check if they fit in budget
        # If over budget with few turns, we must hard-trim the text content
        total_keep = turns_to_keep_at_start + turns_to_keep_at_end
        # FIX: Handle [-0:] which returns full list in Python
        candidate = story_context[-total_keep:] if total_keep > 0 else []

        if not candidate:
            # No turns to keep - return empty
            return []

        candidate_text = "".join(e.get(constants.KEY_TEXT, "") for e in candidate)
        candidate_tokens = estimate_tokens(candidate_text)

        if candidate_tokens <= max_tokens:
            return candidate

        # Still over budget - iteratively hard-trim until we fit
        # Start with proportional trim based on current vs target
        trim_ratio = max_tokens / max(1, candidate_tokens)
        trimmed_context = list(candidate)  # Copy to avoid mutation

        # FIX: Loop until we actually fit, not just 10 iterations
        max_iterations = 50  # Increased from 10
        for iteration in range(max_iterations):
            trimmed_entries = []
            for entry in trimmed_context:
                text = entry.get(constants.KEY_TEXT, "")
                # FIX: Remove 50-char floor - allow trimming to any size
                entry_max_chars = int(len(text) * trim_ratio)

                # FIX: If entry would be empty or near-empty, drop it entirely
                if entry_max_chars <= 10:
                    # Skip this entry (drop it)
                    continue

                # FIX: Check for JSON/structured content - don't corrupt it
                if text.strip().startswith('{') or text.strip().startswith('['):
                    # This looks like JSON - either keep fully or drop
                    if len(text) > entry_max_chars:
                        continue  # Drop JSON entry rather than corrupt it
                    trimmed_entries.append(entry)
                    continue

                if len(text) > entry_max_chars:
                    trimmed_text = text[:entry_max_chars] + "... [truncated]"
                    trimmed_entries.append({**entry, constants.KEY_TEXT: trimmed_text})
                else:
                    trimmed_entries.append(entry)

            # If we've dropped all entries, keep at least one minimal marker
            if not trimmed_entries:
                trimmed_entries = [{
                    "actor": "system",
                    "text": "[...context truncated to fit budget...]"
                }]

            trimmed_text = "".join(e.get(constants.KEY_TEXT, "") for e in trimmed_entries)
            trimmed_tokens = estimate_tokens(trimmed_text)

            if trimmed_tokens <= max_tokens:
                logging_util.warning(
                    f"Hard-trimmed {len(candidate)} turns to fit budget: "
                    f"{candidate_tokens} tokens -> {trimmed_tokens} tokens"
                )
                return trimmed_entries

            # Still over - reduce ratio further and try again
            trim_ratio *= 0.7
            trimmed_context = trimmed_entries

        # Final fallback - return minimal marker if still over budget
        logging_util.warning(
            f"Hard-trim exhausted iterations, returning minimal marker: "
            f"{candidate_tokens} tokens -> budget: {max_tokens}"
        )
        return [{
            "actor": "system",
            "text": "[...context truncated to fit budget...]"
        }]

    # Calculate middle token budget (10% of story budget)
    middle_token_budget = int(max_tokens * STORY_BUDGET_MIDDLE_RATIO)

    # ADAPTIVE LOOP: Reduce turns until content fits within token budget
    # Use absolute minimums but respect passed-in values if they're smaller
    ABS_MIN_START = 3
    ABS_MIN_END = 5
    min_start = min(ABS_MIN_START, turns_to_keep_at_start) if turns_to_keep_at_start > 0 else 0
    min_end = min(ABS_MIN_END, turns_to_keep_at_end)

    current_start = turns_to_keep_at_start
    current_end = turns_to_keep_at_end

    while current_start >= min_start and current_end >= min_end:
        start_context = story_context[:current_start] if current_start > 0 else []
        end_context = story_context[-current_end:] if current_end > 0 else []

        # Extract and compact middle turns instead of dropping them
        middle_start_idx = current_start
        middle_end_idx = total_turns - current_end
        middle_turns = story_context[middle_start_idx:middle_end_idx] if middle_end_idx > middle_start_idx else []

        # Compact middle turns to preserve key events
        middle_summary = _compact_middle_turns(middle_turns, middle_token_budget)

        truncated_context = start_context + [middle_summary] + end_context

        truncated_text = "".join(
            entry.get(constants.KEY_TEXT, "") for entry in truncated_context
        )
        truncated_tokens = estimate_tokens(truncated_text)

        if truncated_tokens <= max_tokens:
            # Found a fit
            final_stats = _get_context_stats(
                truncated_context, model_name, current_game_state, provider_name
            )
            if current_start < turns_to_keep_at_start or current_end < turns_to_keep_at_end:
                logging_util.warning(
                    f"Adaptive truncation reduced to {current_start}+{current_end} turns "
                    f"(from {turns_to_keep_at_start}+{turns_to_keep_at_end}) to fit budget. "
                    f"Middle: {len(middle_turns)} turns compacted. "
                    f"Final: {truncated_tokens} tokens <= {max_tokens} budget"
                )
            else:
                logging_util.info(
                    f"Truncation: {current_start} start + {len(middle_turns)} middle (compacted) + "
                    f"{current_end} end = {truncated_tokens} tokens"
                )
            logging_util.info(f"Final context stats after truncation: {final_stats}")
            return truncated_context

        # Still over budget - reduce turns (alternate between start and end)
        # Prioritize keeping recent context, reduce start turns faster
        if current_start > min_start and current_start >= current_end:
            step = 2 if current_start - 2 >= min_start else 1
            current_start -= step
        elif current_end > min_end:
            step = 2 if current_end - 2 >= min_end else 1
            current_end -= step
        elif current_start > min_start:
            current_start -= 1
        else:
            # Can't reduce further - exit loop and use last resort
            break

    # Last resort: minimum turns with compacted middle
    start_context = story_context[:min_start] if min_start > 0 else []
    end_context = story_context[-min_end:] if min_end > 0 else []

    # Extract and compact middle turns for last resort
    middle_start_idx = min_start
    middle_end_idx = total_turns - min_end
    middle_turns = story_context[middle_start_idx:middle_end_idx] if middle_end_idx > middle_start_idx else []
    middle_summary = _compact_middle_turns(middle_turns, middle_token_budget)

    truncated_context = start_context + [middle_summary] + end_context

    truncated_text = "".join(
        entry.get(constants.KEY_TEXT, "") for entry in truncated_context
    )
    truncated_tokens = estimate_tokens(truncated_text)

    logging_util.warning(
        f"Aggressive truncation to {min_start}+{min_end} turns. "
        f"Tokens: {truncated_tokens} (budget: {max_tokens})"
    )

    # If STILL over budget after minimum turns, iteratively hard-trim the text content
    if truncated_tokens > max_tokens:
        trim_ratio = max_tokens / max(1, truncated_tokens)
        original_context = truncated_context

        for iteration in range(50):  # Increased iterations for convergence
            hard_trimmed = []
            for entry in original_context:
                text = entry.get(constants.KEY_TEXT, "")
                # FIX: Remove 50-char floor - allow trimming to any size
                entry_max_chars = int(len(text) * trim_ratio)

                # FIX: If entry would be too small, drop it entirely
                if entry_max_chars <= 10:
                    # Drop this entry - not enough content to be useful
                    continue

                # FIX: Detect JSON content and drop instead of corrupting
                text_stripped = text.strip()
                if (text_stripped.startswith("{") or text_stripped.startswith("[")) and len(text) > entry_max_chars:
                    # JSON content would be corrupted by truncation - drop it
                    continue

                if len(text) > entry_max_chars:
                    trimmed_text = text[:entry_max_chars] + "... [truncated]"
                    hard_trimmed.append({**entry, constants.KEY_TEXT: trimmed_text})
                else:
                    hard_trimmed.append(entry)

            # If we dropped all entries, return minimal marker
            if not hard_trimmed:
                hard_trimmed = [{
                    "actor": "system",
                    "text": "[...previous context truncated to fit model limits...]",
                }]

            trimmed_text = "".join(e.get(constants.KEY_TEXT, "") for e in hard_trimmed)
            new_tokens = estimate_tokens(trimmed_text)

            if new_tokens <= max_tokens:
                logging_util.warning(
                    f"Hard-trimmed last resort to fit budget: "
                    f"{truncated_tokens} tokens -> {new_tokens} tokens (iteration {iteration + 1})"
                )
                truncated_context = hard_trimmed
                break

            # Still over - reduce ratio further
            trim_ratio *= 0.7
            truncated_context = hard_trimmed

    final_stats = _get_context_stats(
        truncated_context, model_name, current_game_state, provider_name
    )
    logging_util.info(f"Final context stats after truncation: {final_stats}")

    return truncated_context


# Mock response constants for better maintainability
MOCK_INITIAL_STORY_WITH_COMPANIONS = """{
"narrative": "Welcome to your adventure! You find yourself at the entrance of a mysterious dungeon, with stone walls covered in ancient runes. The air is thick with magic and possibility. As you approach, three skilled adventurers emerge from the shadows to join your quest.",
"entities_mentioned": ["dungeon", "runes"],
"location_confirmed": "Dungeon Entrance",
"characters": [{"name": "Aria Moonwhisper", "class": "Elf Ranger", "background": "A skilled archer from the Silverleaf Forest"}],
"setting": {"location": "Dungeon Entrance", "atmosphere": "mysterious"},
"mechanics": {"initiative_rolled": false, "characters_need_setup": true},
"npc_data": {
  "Thorin Ironshield": {
    "mbti": "ISTJ",
    "role": "warrior",
    "background": "A steadfast dwarf fighter with decades of battle experience",
    "relationship": "companion",
    "skills": ["combat", "defense", "weapon mastery"],
    "personality_traits": ["loyal", "protective", "methodical"],
    "equipment": ["enchanted shield", "battle axe", "chainmail"]
  },
  "Luna Starweaver": {
    "mbti": "INFP",
    "role": "healer",
    "background": "A gentle elf cleric devoted to the healing arts",
    "relationship": "companion",
    "skills": ["healing magic", "divine spells", "herbalism"],
    "personality_traits": ["compassionate", "wise", "intuitive"],
    "equipment": ["holy symbol", "healing potions", "staff of light"]
  },
  "Zara Swiftblade": {
    "mbti": "ESTP",
    "role": "scout",
    "background": "A quick-witted halfling rogue skilled in stealth and traps",
    "relationship": "companion",
    "skills": ["stealth", "lockpicking", "trap detection"],
    "personality_traits": ["agile", "clever", "bold"],
    "equipment": ["thieves' tools", "daggers", "studded leather armor"]
  }
}
}"""

MOCK_INITIAL_STORY_NO_COMPANIONS = """{
"narrative": "Welcome to your adventure! You find yourself at the entrance of a mysterious dungeon, with stone walls covered in ancient runes. The air is thick with magic and possibility.",
"entities_mentioned": ["dungeon", "runes"],
"location_confirmed": "Dungeon Entrance",
"characters": [{"name": "Aria Moonwhisper", "class": "Elf Ranger", "background": "A skilled archer from the Silverleaf Forest"}],
"setting": {"location": "Dungeon Entrance", "atmosphere": "mysterious"},
"mechanics": {"initiative_rolled": false, "characters_need_setup": true}
}"""


def _select_provider_and_model(user_id: UserId | None) -> ProviderSelection:
    """Select the configured LLM provider and model for a user.

    In test/mock mode (MOCK_SERVICES_MODE=true, FORCE_TEST_MODEL=true, or TESTING=true),
    always returns default Gemini provider to avoid hitting real OpenRouter/Cerebras APIs.
    """
    # DIAGNOSTIC: Log entry with all relevant env vars
    logging_util.info(
        f"🔍 PROVIDER_SELECTION_START: user_id={user_id}, "
        f"MOCK_SERVICES_MODE={os.environ.get('MOCK_SERVICES_MODE')}, "
        f"FORCE_TEST_MODEL={os.environ.get('FORCE_TEST_MODEL')}, "
        f"TESTING={os.environ.get('TESTING')}"
    )

    # Test mode guard: avoid hitting real providers during CI/test runs
    force_test_model = (
        os.environ.get("MOCK_SERVICES_MODE") == "true"
        or os.environ.get("FORCE_TEST_MODEL") == "true"
        or os.environ.get("TESTING") == "true"
    )
    if force_test_model:
        logging_util.info(
            "🔍 PROVIDER_SELECTION_FORCED_TEST: Returning Gemini due to test mode flags"
        )
        return ProviderSelection(constants.DEFAULT_LLM_PROVIDER, TEST_MODEL)

    provider = constants.DEFAULT_LLM_PROVIDER
    model = DEFAULT_MODEL

    if not user_id:
        logging_util.info(
            "🔍 PROVIDER_SELECTION_NO_USER: No user_id provided, returning default Gemini"
        )
        return ProviderSelection(provider, model)

    try:
        user_settings = get_user_settings(user_id)
        logging_util.info(
            f"🔍 PROVIDER_SELECTION_SETTINGS: user_id={user_id}, "
            f"settings={user_settings}"
        )
        if user_settings is None:
            logging_util.warning(
                f"🔍 PROVIDER_SELECTION_NULL_SETTINGS: Database error retrieving settings "
                f"for user {user_id}, falling back to default model (Gemini)"
            )
            return ProviderSelection(provider, model)

        requested_provider = user_settings.get("llm_provider")
        if requested_provider in constants.ALLOWED_LLM_PROVIDERS:
            provider = requested_provider

        if provider == constants.LLM_PROVIDER_OPENROUTER:
            preferred_openrouter = user_settings.get("openrouter_model")
            if preferred_openrouter in constants.ALLOWED_OPENROUTER_MODELS:
                model = preferred_openrouter
            else:
                model = constants.DEFAULT_OPENROUTER_MODEL
        elif provider == constants.LLM_PROVIDER_CEREBRAS:
            preferred_cerebras = user_settings.get("cerebras_model")
            if preferred_cerebras in constants.ALLOWED_CEREBRAS_MODELS:
                model = preferred_cerebras
            else:
                model = constants.DEFAULT_CEREBRAS_MODEL
        else:
            model = constants.DEFAULT_GEMINI_MODEL
            user_preferred_model = user_settings.get("gemini_model")

            if user_preferred_model in constants.GEMINI_MODEL_MAPPING:
                mapped_model = constants.GEMINI_MODEL_MAPPING[user_preferred_model]
                logging_util.info(
                    f"Remapping Gemini model {user_preferred_model} -> {mapped_model}"
                )
                user_preferred_model = mapped_model

            # Check if user wants Gemini 3 (premium model)
            if user_preferred_model in constants.PREMIUM_GEMINI_MODELS:
                # Get user email to check allowlist
                try:
                    user_record = firebase_auth.get_user(user_id)
                    user_email = (user_record.email or "").lower()
                    allowed_users = [email.lower() for email in constants.GEMINI_3_ALLOWED_USERS]
                    if user_email in allowed_users:
                        model = constants.GEMINI_PREMIUM_MODEL
                        logging_util.info(f"Premium user {user_email} using Gemini 3")
                        return ProviderSelection(provider, model)
                    logging_util.info(
                        f"User {user_email} not in Gemini 3 allowlist, falling back to default"
                    )
                    user_preferred_model = constants.DEFAULT_GEMINI_MODEL
                except Exception as e:
                    logging_util.warning(f"Failed to check Gemini 3 allowlist: {e}")
                    user_preferred_model = constants.DEFAULT_GEMINI_MODEL

            # Standard model selection
            if user_preferred_model in constants.ALLOWED_GEMINI_MODELS:
                model = user_preferred_model
            else:
                model = constants.DEFAULT_GEMINI_MODEL

        logging_util.info(
            f"🔍 PROVIDER_SELECTION_FINAL: user_id={user_id}, "
            f"provider={provider}, model={model}"
        )
        return ProviderSelection(provider, model)
    except (KeyError, AttributeError, ValueError) as e:
        logging_util.warning(
            f"🔍 PROVIDER_SELECTION_EXCEPTION: Failed to get user settings for {user_id}: {e}, "
            f"falling back to provider={provider}, model={model}"
        )
        return ProviderSelection(provider, model)


def _select_model_for_user(user_id: UserId | None) -> str:
    return _select_provider_and_model(user_id).model


@log_exceptions
def get_initial_story(
    prompt: str,
    user_id: UserId | None = None,
    selected_prompts: list[str] | None = None,
    generate_companions: bool = False,
    use_default_world: bool = False,
) -> LLMResponse:
    """
    Generates the initial story part, including character, narrative, and mechanics instructions.

    Returns:
        LLMResponse: Custom response object containing:
            - narrative_text: Clean text for display (guaranteed to be clean narrative)
            - structured_response: Parsed JSON with state updates, entities, etc.
    """
    # Check for mock mode and return mock response immediately
    mock_mode = os.environ.get("MOCK_SERVICES_MODE") == "true"
    if mock_mode:
        logging_util.info("Using mock mode - returning mock initial story response")
        if generate_companions:
            logging_util.info("Mock mode: Generating companions as requested")
            mock_response_text = MOCK_INITIAL_STORY_WITH_COMPANIONS
        else:
            logging_util.info("Mock mode: No companions requested")
            mock_response_text = MOCK_INITIAL_STORY_NO_COMPANIONS

        # Parse the mock response to get structured data
        narrative_text, structured_response = parse_structured_response(
            mock_response_text
        )

        if structured_response:
            return LLMResponse.create_from_structured_response(
                structured_response, "mock-model"
            )
        return LLMResponse.create_legacy(
            "Welcome to your adventure! You find yourself at the entrance of a mysterious dungeon, with stone walls covered in ancient runes. The air is thick with magic and possibility.",
            "mock-model",
        )

    if selected_prompts is None:
        selected_prompts = []
        logging_util.warning(
            "No specific system prompts selected for initial story. Using none."
        )

    # Use PromptBuilder to construct system instructions
    builder: PromptBuilder = PromptBuilder()

    # Build core instructions
    system_instruction_parts: list[str] = builder.build_core_system_instructions()

    # Add character-related instructions
    builder.add_character_instructions(system_instruction_parts, selected_prompts)

    # Add selected prompt instructions
    builder.add_selected_prompt_instructions(system_instruction_parts, selected_prompts)

    # Add system reference instructions
    builder.add_system_reference_instructions(system_instruction_parts)

    # Add companion generation instruction if requested
    if generate_companions:
        system_instruction_parts.append(builder.build_companion_instruction())

    # Add background summary instruction for initial story
    system_instruction_parts.append(builder.build_background_summary_instruction())

    # Finalize with world and debug instructions
    system_instruction_final = builder.finalize_instructions(
        system_instruction_parts, use_default_world
    )

    # Add clear indication when using default world setting
    if use_default_world:
        prompt = f"Use default setting Assiah. {prompt}"

    # --- ENTITY TRACKING FOR INITIAL STORY ---
    # Extract expected entities from the prompt for initial tracking
    expected_entities: list[str] = []
    entity_preload_text: str = ""
    entity_specific_instructions: str = ""
    entity_tracking_instruction: str = ""

    # Let the LLM determine and provide character names in the response
    # rather than extracting them via regex patterns from the prompt
    # Character names will be handled by structured generation and entity tracking

    # Player character name should come from LLM structured response (player_character_data.name)
    # NOT from fragile regex parsing of user prompts

    # Create a minimal initial game state for entity tracking
    # Use default player character - actual name will come from LLM response
    pc_name = "Player Character"

    if expected_entities:
        initial_game_state = {
            "player_character_data": {
                "name": pc_name,
                "hp": 10,
                "max_hp": 10,
                "level": 1,
                "string_id": f"pc_{sanitize_entity_name_for_id(pc_name)}_001",
            },
            "npc_data": {},
            "world_data": {"current_location_name": "The throne room"},
            "combat_state": {"in_combat": False},
        }

        # 1. Entity Pre-Loading (Option 3)
        entity_preload_text = entity_preloader.create_entity_preload_text(
            initial_game_state, 1, 1, "Starting Location"
        )

        # 2. Entity-Specific Instructions (Option 5)
        entity_instructions = instruction_generator.generate_entity_instructions(
            entities=expected_entities,
            player_references=[prompt],
            location="Starting Location",
            story_context="",
        )
        entity_specific_instructions = entity_instructions

        # 3. Create entity manifest for tracking using create_from_game_state
        # For initial story, we use session 1, turn 1
        entity_manifest = create_from_game_state(initial_game_state, 1, 1)
        entity_manifest_text = entity_manifest.to_prompt_format()
        entity_tracking_instruction = create_structured_prompt_injection(
            entity_manifest_text, expected_entities
        )

    # Build enhanced prompt with entity tracking
    enhanced_prompt: str = prompt
    if (
        entity_preload_text
        or entity_specific_instructions
        or entity_tracking_instruction
    ):
        enhanced_prompt = (
            f"{entity_preload_text}"
            f"{entity_specific_instructions}"
            f"{entity_tracking_instruction}"
            f"\nUSER REQUEST:\n{prompt}"
        )
        logging_util.info(
            f"Added entity tracking to initial story. Expected entities: {expected_entities}"
        )

    # Add character creation reminder if mechanics is enabled
    if selected_prompts and constants.PROMPT_TYPE_MECHANICS in selected_prompts:
        enhanced_prompt = constants.CHARACTER_DESIGN_REMINDER + "\n\n" + enhanced_prompt
        logging_util.info("Added character creation reminder to initial story prompt")

    # --- MODEL SELECTION ---
    # Use centralized helper for consistent model selection across all story generation
    provider_selection = _select_provider_and_model(user_id)
    model_to_use: str = provider_selection.model
    logging_util.info(
        f"Using provider/model: {provider_selection.provider}/{model_to_use} for initial story generation."
    )

    # ONLY use LLMRequest structured JSON architecture (NO legacy fallbacks)
    if not user_id:
        raise ValueError("user_id is required for initial story generation")

    # NEW ARCHITECTURE: Use LLMRequest for structured JSON (NO string concatenation)
    world_data = {}  # Could be extracted from builder if needed

    # Build LLMRequest with structured data
    gemini_request = LLMRequest.build_initial_story(
        character_prompt=prompt,
        user_id=str(user_id),
        selected_prompts=selected_prompts or [],
        generate_companions=generate_companions,
        use_default_world=use_default_world,
        world_data=world_data,
    )

    # Send structured JSON directly to Gemini API (NO string conversion)
    api_response = _call_llm_api_with_llm_request(
        gemini_request=gemini_request,
        model_name=model_to_use,
        system_instruction_text=system_instruction_final,
        provider_name=provider_selection.provider,
    )
    logging_util.info("Successfully used LLMRequest for initial story generation")
    # Extract text from raw API response object
    raw_response_text: str = _get_text_from_response(api_response)

    # Create LLMResponse from raw response, which handles all parsing internally
    # Parse the structured response to extract clean narrative and debug data
    narrative_text, structured_response = parse_structured_response(raw_response_text)

    # DIAGNOSTIC LOGGING: Log parsed response details for debugging empty narrative issues
    logging_util.info(
        f"📊 PARSED_RESPONSE (initial_story): narrative_length={len(narrative_text)}, "
        f"structured_response={'present' if structured_response else 'None'}, "
        f"raw_response_length={len(raw_response_text)}"
    )
    if len(narrative_text) == 0:
        # Include preview suffix only if response was truncated
        raw_preview = raw_response_text[:500]
        preview_suffix = "..." if len(raw_response_text) > 500 else ""
        logging_util.warning(
            f"⚠️ EMPTY_NARRATIVE (initial_story): LLM returned empty narrative. "
            f"Raw response preview: {raw_preview}{preview_suffix}"
        )
        # Log structured response fields if available (consistent with continue_story)
        if structured_response:
            has_planning = bool(
                structured_response.planning_block
                if hasattr(structured_response, "planning_block")
                else False
            )
            has_session = bool(
                structured_response.session_header
                if hasattr(structured_response, "session_header")
                else False
            )
            logging_util.warning(
                f"⚠️ EMPTY_NARRATIVE (initial_story): structured_response has "
                f"planning_block={has_planning}, session_header={has_session}"
            )

    # Create LLMResponse with proper debug content separation
    if structured_response:
        # Use structured response (preferred) - ensures clean separation
        gemini_response = LLMResponse.create_from_structured_response(
            structured_response, model_to_use
        )
    else:
        # Fallback to legacy mode for non-JSON responses
        gemini_response = LLMResponse.create_legacy(narrative_text, model_to_use)

    # --- ENTITY VALIDATION FOR INITIAL STORY ---
    if expected_entities:
        validator = NarrativeSyncValidator()
        validation_result = validator.validate(
            narrative_text=gemini_response.narrative_text,
            expected_entities=expected_entities,
            location="Starting Location",
        )

        if not validation_result.all_entities_present:
            logging_util.warning(
                f"Initial story failed entity validation. Missing: {validation_result.entities_missing}"
            )
            # For initial story, we'll log but not retry to avoid complexity
            # The continue_story function will handle retry logic for subsequent interactions

    # Log LLMResponse creation - INFO level for production visibility
    logging_util.info(
        f"📝 FINAL_RESPONSE (initial_story): narrative_length={len(gemini_response.narrative_text)}, "
        f"has_structured_response={gemini_response.structured_response is not None}"
    )

    # Companion validation (moved from world_logic.py for proper SRP)
    if generate_companions:
        _validate_companion_generation(gemini_response)

    # Return our custom LLMResponse object (not raw API response)
    # This object contains:
    # - narrative_text: Clean text for display (guaranteed to be clean narrative)
    # - structured_response: Parsed JSON structure with state updates, entities, etc.
    return gemini_response


# Note: _is_in_character_creation function removed as we now include planning blocks
# during character creation for better interactivity


def _log_api_response_safely(
    response_text: str | None, context: str = "", max_length: int = 400
) -> None:
    """
    Log API response content safely with truncation and redaction.

    Args:
        response_text: The response content to log
        context: Context description for the log
        max_length: Maximum length to log (default 400 chars)
    """
    if not response_text:
        logging_util.warning(
            f"🔍 API_RESPONSE_DEBUG ({context}): Response is empty or None"
        )
        return

    # Convert to string safely
    response_str = str(response_text)

    # Log basic info
    logging_util.info(
        f"🔍 API_RESPONSE_DEBUG ({context}): Length: {len(response_str)} chars"
    )

    # Log truncated content for debugging
    if len(response_str) <= max_length:
        logging_util.info(f"🔍 API_RESPONSE_DEBUG ({context}): Content: {response_str}")
    else:
        half_length = max_length // 2
        start_content = response_str[:half_length]
        end_content = response_str[-half_length:]
        logging_util.info(
            f"🔍 API_RESPONSE_DEBUG ({context}): Content: {start_content}...[{len(response_str) - max_length} chars omitted]...{end_content}"
        )


def _validate_and_enforce_planning_block(
    response_text: str | None,
    user_input: str,
    game_state: GameState,
    chosen_model: str,
    system_instruction: str,
    structured_response: NarrativeResponse | None = None,
    provider_name: str = constants.DEFAULT_LLM_PROVIDER,
) -> str:
    """
    CRITICAL: Validates that structured_response.planning_block exists and is valid JSON.
    The structured_response.planning_block field is the PRIMARY and AUTHORITATIVE source.

    If missing or invalid, asks the LLM to generate an appropriate planning block.

    Args:
        response_text: The AI's response text (for context only)
        user_input: The user's input to determine if deep think block is needed
        game_state: Current game state for context
        chosen_model: Model to use for generation
        system_instruction: System instruction for the LLM
        structured_response: NarrativeResponse object to update (REQUIRED)

    Returns:
        str: Response text with planning block added (for backward compatibility only)
    """
    # Handle None response_text gracefully
    if response_text is None:
        logging_util.warning(
            "🔍 VALIDATION_INPUT: Response text is None, returning empty string"
        )
        return ""

    # Note: We now INCLUDE planning blocks during character creation for interactivity
    # The previous behavior of skipping them has been removed to support
    # interactive character creation with player choices

    # Skip planning block if user is switching to god/dm mode
    # Note: Mode detection is now handled by the main Gemini response generation
    # which naturally understands mode switching requests through system instructions

    # Skip planning block if AI response indicates mode switch
    if response_text and (
        "[Mode: DM MODE]" in response_text or "[Mode: GOD MODE]" in response_text
    ):
        logging_util.info("Response indicates mode switch - skipping planning block")
        return response_text

    # Check if response already contains a planning block
    # JSON-ONLY: Only check structured response for JSON planning blocks
    if (
        structured_response
        and hasattr(structured_response, "planning_block")
        and structured_response.planning_block
    ):
        planning_block = structured_response.planning_block

        # Only accept JSON format
        if isinstance(planning_block, dict):
            # JSON format - check if it has choices or thinking content
            has_content = planning_block.get("thinking", "").strip() or (
                planning_block.get("choices")
                and len(planning_block.get("choices", {})) > 0
            )

            if has_content:
                logging_util.info("Planning block found in JSON structured response")
                return response_text
        else:
            # String format no longer supported
            logging_util.error(
                f"❌ STRING PLANNING BLOCKS NO LONGER SUPPORTED: Found {type(planning_block).__name__} planning block, only JSON format is allowed"
            )
            # Continue to generate proper planning block below

    # REMOVED LEGACY FALLBACK: No longer check response text for planning blocks
    # The JSON field is authoritative - if it's empty, we generate content regardless of text

    logging_util.warning(
        "⚠️ PLANNING_BLOCK_MISSING: Story mode response missing required planning block"
    )

    # Determine if we need a deep think block
    # Note: Deep thinking detection is now handled by enhanced system instructions
    # that guide Gemini to naturally recognize when strategic thinking is needed
    needs_deep_think: bool = (
        "think" in user_input.lower() or "plan" in user_input.lower()
    )

    # Strip any trailing whitespace
    response_text = response_text.rstrip()

    # Create prompt to generate planning block with proper context isolation
    # Extract current character info for context
    pc_name: str = (
        game_state.player_character_data.get("name", "the character")
        if game_state.player_character_data
        else "the character"
    )
    current_location: str = (
        game_state.world_data.get("current_location_name", "current location")
        if game_state.world_data
        else "current location"
    )

    planning_prompt: str
    if needs_deep_think:
        planning_prompt = f"""
CRITICAL: Generate planning options ONLY for {pc_name} in {current_location}.
DO NOT reference other characters, campaigns, or unrelated narrative elements.

The player just said: "{user_input}"

They are asking to think/plan/consider their options. Generate ONLY a planning block using the think_planning_block template format from your system instructions.

Full narrative context:
{response_text}"""
    else:
        # Check if this is character creation approval step
        response_lower: str = response_text.lower()
        is_character_approval: bool = (
            "[character creation" in response_lower
            and "character sheet" in response_lower
            and (
                "would you like to play as this character" in response_lower
                or "what is your choice?" in response_lower
                or "approve this character" in response_lower
                or
                # Handle truncated responses that contain character creation elements
                (
                    "**why this character:**" in response_lower
                    and (
                        "ability scores:" in response_lower
                        or "equipment:" in response_lower
                        or "background:" in response_lower
                    )
                )
            )
        )

        if is_character_approval:
            planning_prompt = f"""
CRITICAL: This is the CHARACTER CREATION APPROVAL step.

The player has just been shown a complete character sheet and needs to approve it before starting the adventure.

Generate ONLY a planning block with these EXACT options:
1. **PlayCharacter:** Begin the adventure!
2. **MakeChanges:** Tell me what you'd like to adjust
3. **StartOver:** Design a completely different character

Full narrative context:
{response_text}"""
        else:
            planning_prompt = f"""
CRITICAL: Generate planning options ONLY for {pc_name} in {current_location}.
DO NOT reference other characters, campaigns, or unrelated narrative elements.

Generate ONLY a planning block using the standard_choice_block template format from your system instructions.

Full narrative context:
{response_text}"""

    # Early return if planning block is already set
    if structured_response and structured_response.planning_block:
        logging_util.info(
            "🔍 PLANNING_BLOCK_SKIPPED: structured_response.planning_block is already set, skipping API call"
        )
        return response_text

    # Generate planning block using LLM
    try:
        logging_util.info("🔍 PLANNING_BLOCK_REGENERATION: Sending prompt to API")
        logging_util.info(f"🔍 PLANNING_BLOCK_PROMPT: {planning_prompt[:200]}...")

        planning_response = _call_llm_api(
            [planning_prompt],
            chosen_model,
            current_prompt_text_for_logging="Planning block generation",
            system_instruction_text=system_instruction,
            provider_name=provider_name,
        )
        raw_planning_response: str = _get_text_from_response(planning_response)

        # CRITICAL LOGGING: Log what we actually received from API
        _log_api_response_safely(raw_planning_response, "PLANNING_BLOCK_RAW_RESPONSE")

        # Use centralized parsing for planning block
        logging_util.info("🔍 PLANNING_BLOCK_PARSING: Attempting to parse response")
        planning_text: str
        structured_planning_response: NarrativeResponse | None
        planning_text, structured_planning_response = _parse_gemini_response(
            raw_planning_response, context="planning_block"
        )

        # Log parsing results
        logging_util.info(
            f"🔍 PLANNING_BLOCK_PARSING_RESULT: planning_text length: {len(planning_text) if planning_text else 0}"
        )
        logging_util.info(
            f"🔍 PLANNING_BLOCK_PARSING_RESULT: structured_response exists: {structured_planning_response is not None}"
        )

        # If we got a structured response with planning_block field, use that
        if (
            structured_planning_response
            and hasattr(structured_planning_response, "planning_block")
            and structured_planning_response.planning_block
        ):
            planning_block = structured_planning_response.planning_block
            logging_util.info(
                f"🔍 PLANNING_BLOCK_SOURCE: Using structured_response.planning_block (type: {type(planning_block)})"
            )
            _log_api_response_safely(
                str(planning_block), "PLANNING_BLOCK_STRUCTURED_CONTENT"
            )
        else:
            # Otherwise use the raw text
            planning_block = planning_text
            logging_util.info(
                f"🔍 PLANNING_BLOCK_SOURCE: Using raw planning_text (length: {len(planning_block) if planning_block else 0})"
            )
            _log_api_response_safely(planning_block, "PLANNING_BLOCK_RAW_CONTENT")

        # Handle both string and dict planning blocks
        if isinstance(planning_block, str):
            # Ensure it starts with newlines and the header for backward compatibility
            if not planning_block.startswith("\n\n--- PLANNING BLOCK ---"):
                planning_block = "\n\n" + planning_block.strip()

        # PRIMARY: Update structured_response.planning_block (this is what frontend uses)
        if structured_response and isinstance(structured_response, NarrativeResponse):
            if isinstance(planning_block, dict):
                # Already in JSON format
                structured_response.planning_block = planning_block
                logging_util.info(
                    "Updated structured_response.planning_block with JSON content"
                )
            elif isinstance(planning_block, str):
                # Use the actual planning block content we extracted
                clean_planning_block = planning_block.strip()
                # Remove the header if present
                if clean_planning_block.startswith("--- PLANNING BLOCK ---"):
                    clean_planning_block = clean_planning_block.replace(
                        "--- PLANNING BLOCK ---", ""
                    ).strip()

                if clean_planning_block:
                    # Try to parse the LLM-generated content as structured choices
                    logging_util.info(
                        f"🔍 VALIDATION_SUCCESS: String planning block passed validation (length: {len(clean_planning_block)})"
                    )

                    # Attempt to parse the string content as structured choices
                    try:
                        # Try to parse as JSON first
                        parsed_content = json.loads(clean_planning_block)
                        if (
                            isinstance(parsed_content, dict)
                            and "choices" in parsed_content
                        ):
                            structured_response.planning_block = parsed_content
                            logging_util.info(
                                "Updated structured_response.planning_block with parsed JSON content"
                            )
                        else:
                            # If it's not structured JSON, treat as raw content but preserve it
                            structured_response.planning_block = {
                                "thinking": "Generated planning block based on current situation:",
                                "raw_content": clean_planning_block,
                            }
                            logging_util.info(
                                "Updated structured_response.planning_block with raw LLM content preserved"
                            )
                    except (json.JSONDecodeError, ValueError):
                        # If JSON parsing fails, preserve the raw content
                        structured_response.planning_block = {
                            "thinking": "Generated planning block based on current situation:",
                            "raw_content": clean_planning_block,
                        }
                        logging_util.info(
                            "Updated structured_response.planning_block with raw LLM content (JSON parse failed)"
                        )
                else:
                    # Log validation failure details
                    logging_util.warning(
                        "🔍 VALIDATION_FAILURE: String planning block failed validation"
                    )
                    logging_util.warning(
                        f"🔍 VALIDATION_FAILURE: Original planning_block type: {type(planning_block)}"
                    )
                    logging_util.warning(
                        f"🔍 VALIDATION_FAILURE: Original planning_block content: {repr(planning_block)}"
                    )
                    logging_util.warning(
                        f"🔍 VALIDATION_FAILURE: clean_planning_block after processing: {repr(clean_planning_block)}"
                    )

                    # Fallback content for empty generation - use JSON format
                    structured_response.planning_block = (
                        FALLBACK_PLANNING_BLOCK_VALIDATION
                    )
                    logging_util.info(
                        "Used fallback JSON content for structured_response.planning_block"
                    )

        # SECONDARY: Update response_text for backward compatibility only
        if isinstance(planning_block, str):
            if not planning_block.startswith("\n\n--- PLANNING BLOCK ---"):
                planning_block = "\n\n--- PLANNING BLOCK ---\n" + planning_block.strip()
            response_text = response_text + planning_block

        logging_util.info(
            f"Added LLM-generated {'deep think' if needs_deep_think else 'standard'} planning block"
        )

    except Exception as e:
        logging_util.error(
            f"🔍 PLANNING_BLOCK_EXCEPTION: Failed to generate planning block: {e}"
        )
        logging_util.error(f"🔍 PLANNING_BLOCK_EXCEPTION: Exception type: {type(e)}")
        logging_util.error(f"🔍 PLANNING_BLOCK_EXCEPTION: Exception details: {repr(e)}")

        # Log traceback for debugging
        logging_util.error(
            f"🔍 PLANNING_BLOCK_EXCEPTION: Traceback: {traceback.format_exc()}"
        )

        # PRIMARY: Update structured_response.planning_block with fallback in JSON format
        fallback_content = FALLBACK_PLANNING_BLOCK_EXCEPTION
        if structured_response and isinstance(structured_response, NarrativeResponse):
            structured_response.planning_block = fallback_content
            logging_util.info(
                "🔍 FALLBACK_USED: Updated structured_response.planning_block with fallback JSON content due to exception"
            )

        # SECONDARY: Update response_text for backward compatibility
        fallback_text = "What would you like to do next?\n" + "\n".join(
            [
                f"{i + 1}. **[{choice}]:** {description}"
                for i, (choice, description) in enumerate(DEFAULT_CHOICES.items())
            ]
        )
        fallback_block = "\n\n--- PLANNING BLOCK ---\n" + fallback_text
        response_text = response_text + fallback_block

    return response_text


@log_exceptions
def continue_story(
    user_input: str,
    mode: str,
    story_context: list[dict[str, Any]],
    current_game_state: GameState,
    selected_prompts: list[str] | None = None,
    use_default_world: bool = False,
    user_id: UserId | None = None,
) -> LLMResponse:
    """
    Continues the story by calling the Gemini API with the current context and game state.

    Args:
        user_input: The user's input text
        mode: The interaction mode (e.g., 'character', 'story')
        story_context: List of previous story entries
        current_game_state: Current GameState object
        selected_prompts: List of selected prompt types
        use_default_world: Whether to include world content in system instructions
        user_id: Optional user ID to retrieve user-specific settings (e.g., preferred model)

    Returns:
        LLMResponse: Custom response object containing:
            - narrative_text: Clean text for display (guaranteed to be clean narrative)
            - structured_response: Parsed JSON with state updates, entities, etc.
    """
    # NOTE: Mock mode short-circuit is NOT added here (unlike get_initial_story)
    # because tests use patches on _call_llm_api_with_llm_request to control responses.
    # The _select_provider_and_model() guard already prevents hitting real providers
    # in test mode by returning default Gemini provider which is then mocked.

    # Determine which model to use based on user preferences
    # Use centralized helper for consistent model selection across all story generation
    provider_selection = _select_provider_and_model(user_id)
    model_to_use = provider_selection.model
    logging_util.info(
        f"Using provider/model: {provider_selection.provider}/{model_to_use} for story continuation."
    )

    # Check for multiple think commands in input using regex
    think_pattern: str = r"Main Character:\s*think[^\n]*"
    think_matches: list[str] = re.findall(think_pattern, user_input, re.IGNORECASE)
    if len(think_matches) > 1:
        logging_util.warning(
            f"Multiple think commands detected: {len(think_matches)}. Processing as single response."
        )

    # --- NEW: Validate checkpoint consistency before generating response ---
    if story_context:
        # Get the most recent AI response to validate against current state
        recent_ai_responses = [
            entry.get(constants.KEY_TEXT, "")
            for entry in story_context[-3:]
            if entry.get(constants.KEY_ACTOR) == constants.ACTOR_GEMINI
        ]
        if recent_ai_responses:
            latest_narrative = recent_ai_responses[-1]
            discrepancies = current_game_state.validate_checkpoint_consistency(
                latest_narrative
            )

            if discrepancies:
                logging_util.warning(
                    f"CHECKPOINT_VALIDATION: Found {len(discrepancies)} potential discrepancies:"
                )
                for i, discrepancy in enumerate(discrepancies, 1):
                    logging_util.warning(f"  {i}. {discrepancy}")

                # Add validation prompt to ensure AI addresses inconsistencies
                validation_instruction = (
                    "IMPORTANT: State validation detected potential inconsistencies between the game state "
                    "and recent narrative. Please ensure your response maintains strict consistency with the "
                    "CURRENT GAME STATE data, especially regarding character health, location, and mission status."
                )
                user_input = f"{validation_instruction}\n\n{user_input}"

    if selected_prompts is None:
        selected_prompts = []
        logging_util.warning(
            "No specific system prompts selected for continue_story. Using none."
        )

    # Use PromptBuilder to construct system instructions
    builder: PromptBuilder = PromptBuilder(current_game_state)

    # Build core instructions
    system_instruction_parts: list[str] = builder.build_core_system_instructions()

    # Add character-related instructions
    builder.add_character_instructions(system_instruction_parts, selected_prompts)

    # Add selected prompt instructions (filter calibration for continue_story)
    builder.add_selected_prompt_instructions(system_instruction_parts, selected_prompts)

    # Add system reference instructions
    builder.add_system_reference_instructions(system_instruction_parts)

    # Add continuation-specific reminders (planning blocks) only in character mode
    if mode == constants.MODE_CHARACTER:
        system_instruction_parts.append(builder.build_continuation_reminder())

    # Finalize with world and debug instructions
    system_instruction_final = builder.finalize_instructions(
        system_instruction_parts, use_default_world
    )

    # --- NEW: Budget-based Truncation ---
    # 1. Calculate the size of the "prompt scaffold" (everything except the timeline log)
    serialized_game_state = json.dumps(
        current_game_state.to_dict(), indent=2, default=json_default_serializer
    )

    # Temporarily generate other prompt parts to measure them.
    # We will generate them again *after* truncation with the final context.
    temp_checkpoint_block, temp_core_memories, temp_seq_ids = _get_static_prompt_parts(
        current_game_state, []
    )

    # Calculate tokens for each component - INCLUDING system instruction
    system_instruction_tokens = estimate_tokens(system_instruction_final)
    checkpoint_tokens = estimate_tokens(temp_checkpoint_block)
    core_memories_tokens = estimate_tokens(temp_core_memories)
    seq_ids_tokens = estimate_tokens(temp_seq_ids)
    game_state_tokens = estimate_tokens(serialized_game_state)

    # Log individual component sizes
    logging_util.info(
        f"📊 CONTEXT BREAKDOWN: system_instruction={system_instruction_tokens}tk, "
        f"checkpoint={checkpoint_tokens}tk, core_memories={core_memories_tokens}tk, "
        f"seq_ids={seq_ids_tokens}tk, game_state={game_state_tokens}tk"
    )

    # Include ALL major components in scaffold estimate
    prompt_scaffold = (
        f"{system_instruction_final}\\n\\n"  # System instruction is often HUGE
        f"{temp_checkpoint_block}\\n\\n"
        f"{temp_core_memories}"
        f"REFERENCE TIMELINE (SEQUENCE ID LIST):\\n[{temp_seq_ids}]\\n\\n"
        f"GAME STATE:\\n{serialized_game_state}\\n\\n"
    )

    # Calculate the character budget for the story context using CENTRALIZED budget logic
    # This ensures truncation uses the same formula as validation in _get_safe_output_token_limit
    is_combat_or_complex = current_game_state and (
        current_game_state.combat_state.get("in_combat", False)
    )
    safe_token_budget, output_token_reserve, max_input_allowed = _calculate_context_budget(
        provider_selection.provider, model_to_use, is_combat_or_complex
    )

    scaffold_tokens_raw = estimate_tokens(prompt_scaffold)
    # FIX: Add explicit reserve for entity tracking tokens that are added AFTER truncation
    # Entity tracking includes: entity_preload_text, entity_specific_instructions,
    # entity_tracking_instruction (NOT timeline_log - that's handled separately below)
    scaffold_tokens = scaffold_tokens_raw + ENTITY_TRACKING_TOKEN_RESERVE

    # Use max_input_allowed from centralized budget (accounts for output reserve)
    # Then subtract scaffold tokens to get available story budget
    available_story_tokens_raw = max(0, max_input_allowed - scaffold_tokens)

    include_timeline_log_in_prompt = TIMELINE_LOG_INCLUDED_IN_STRUCTURED_REQUEST
    available_story_tokens, timeline_log_budget_note = _apply_timeline_log_duplication_guard(
        available_story_tokens_raw=available_story_tokens_raw,
        include_timeline_log_in_prompt=include_timeline_log_in_prompt,
    )
    char_budget_for_story = available_story_tokens * 4

    # Calculate story context tokens
    story_text = "".join(entry.get(constants.KEY_TEXT, "") for entry in story_context)
    story_tokens = estimate_tokens(story_text)

    reserve_mode = "combat" if is_combat_or_complex else "normal"
    logging_util.info(
        f"📊 BUDGET: model_limit={_get_context_window_tokens(model_to_use)}tk, "
        f"safe_budget={safe_token_budget}tk, scaffold={scaffold_tokens}tk (raw:{scaffold_tokens_raw}+entity_reserve:{ENTITY_TRACKING_TOKEN_RESERVE}), "
        f"output_reserve={output_token_reserve}tk ({reserve_mode}), "
        f"story_budget={available_story_tokens}tk ({timeline_log_budget_note}), "
        f"actual_story={story_tokens}tk {'⚠️ OVER' if story_tokens > available_story_tokens else '✅ OK'}"
    )

    # Truncate the story context if it exceeds the budget
    truncated_story_context = _truncate_context(
        story_context,
        char_budget_for_story,
        model_to_use,
        current_game_state,
        provider_selection.provider,
    )

    # Now that we have the final, truncated context, we can generate the real prompt parts.
    checkpoint_block, core_memories_summary, sequence_id_list_string = (
        _get_static_prompt_parts(current_game_state, truncated_story_context)
    )

    # Serialize the game state for inclusion in the prompt
    serialized_game_state: str = json.dumps(
        current_game_state.to_dict(), indent=2, default=json_default_serializer
    )

    # --- ENTITY TRACKING: Create scene manifest for entity tracking ---
    # Always prepare entity tracking to ensure JSON response format
    session_number: int = current_game_state.custom_campaign_state.get(
        "session_number", 1
    )
    _, expected_entities, entity_tracking_instruction = _prepare_entity_tracking(
        current_game_state, truncated_story_context, session_number
    )

    # Build timeline log (used for entity prompts and diagnostics, not serialized in LLMRequest)
    timeline_log_string: str = _build_timeline_log(truncated_story_context)

    # Enhanced entity tracking with mitigation strategies
    entity_preload_text: str = ""
    entity_specific_instructions: str = ""

    if expected_entities:
        # 1. Entity Pre-Loading (Option 3)
        game_state_dict = current_game_state.to_dict()
        turn_number = len(truncated_story_context) + 1
        current_location = current_game_state.world_data.get(
            "current_location_name", "Unknown"
        )
        entity_preload_text = entity_preloader.create_entity_preload_text(
            game_state_dict, session_number, turn_number, current_location
        )

        # 2. Entity-Specific Instructions (Option 5)
        player_references = [user_input] if user_input else []
        entity_instructions = instruction_generator.generate_entity_instructions(
            entities=expected_entities,
            player_references=player_references,
            location=current_location,
            story_context=timeline_log_string,
        )
        entity_specific_instructions = entity_instructions

    # Create the final prompt for the current user turn (User's preferred method)
    current_prompt_text: str = _get_current_turn_prompt(user_input, mode)

    # Build the full prompt with entity tracking enhancements
    enhanced_entity_tracking = entity_tracking_instruction
    if entity_preload_text or entity_specific_instructions:
        enhanced_entity_tracking = (
            f"{entity_preload_text}"
            f"{entity_specific_instructions}"
            f"{entity_tracking_instruction}"
        )

    # Legacy/debug-only: we still assemble the string prompt for diagnostics and
    # future prompt-experiment branches. The structured request path below sends
    # only the serialized LLMRequest JSON (story_history, game_state, etc.), not
    # `full_prompt`. If timeline_log text is ever re-serialized, flip
    # TIMELINE_LOG_INCLUDED_IN_STRUCTURED_REQUEST and update budgeting/tests.
    full_prompt = _build_continuation_prompt(
        checkpoint_block,
        core_memories_summary,
        sequence_id_list_string,
        serialized_game_state,
        enhanced_entity_tracking,
        timeline_log_string,
        current_prompt_text,
    )

    # Select appropriate model (use user preference if available, otherwise default selection)
    chosen_model: str = model_to_use

    # ONLY use LLMRequest structured JSON architecture (NO legacy fallbacks)
    user_id_from_state = getattr(current_game_state, "user_id", None)
    if not user_id_from_state:
        raise ValueError("user_id is required in game state for story continuation")

    # Build trimmed entity tracking data using LRU-style tiering
    # This reduces entity_tracking from ~40K tokens to ~1K tokens
    current_location = current_game_state.world_data.get(
        "current_location_name", current_game_state.world_data.get("location", "")
    )
    entity_tracking_data, entity_tier_log = _build_trimmed_entity_tracking(
        npc_data=current_game_state.npc_data,
        story_context=truncated_story_context,
        current_location=current_location,
    )
    logging_util.info(entity_tier_log)

    # Measure and log actual entity tracking token usage
    entity_tracking_tokens = estimate_tokens(json.dumps(entity_tracking_data))
    logging_util.info(
        f"ENTITY_TRACKING_SIZE: {entity_tracking_tokens}tk "
        f"(reserve was {ENTITY_TRACKING_TOKEN_RESERVE}tk)"
    )

    # Build LLMRequest with structured data (NO string concatenation)
    gemini_request = LLMRequest.build_story_continuation(
        user_action=user_input,
        user_id=str(user_id_from_state),
        game_mode=mode,
        game_state=current_game_state.to_dict(),
        story_history=truncated_story_context,
        checkpoint_block=checkpoint_block,
        core_memories=core_memories_summary.split("\n")
        if core_memories_summary
        else [],
        sequence_ids=sequence_id_list_string.split(", ")
        if sequence_id_list_string
        else [],
        entity_tracking=entity_tracking_data,
        selected_prompts=selected_prompts or [],
        use_default_world=use_default_world,
    )

    # Send structured JSON directly to Gemini API (NO string conversion)
    api_response = _call_llm_api_with_llm_request(
        gemini_request=gemini_request,
        model_name=chosen_model,
        system_instruction_text=system_instruction_final,
        provider_name=provider_selection.provider,
    )
    logging_util.info(
        "Successfully used LLMRequest for structured JSON communication"
    )
    # Extract text from raw API response object
    raw_response_text: str = _get_text_from_response(api_response)

    # Create initial LLMResponse from raw response
    # Parse the structured response to extract clean narrative and debug data
    narrative_text: str
    structured_response: NarrativeResponse | None
    narrative_text, structured_response = parse_structured_response(raw_response_text)

    # DIAGNOSTIC LOGGING: Log parsed response details for debugging empty narrative issues
    logging_util.info(
        f"📊 PARSED_RESPONSE: narrative_length={len(narrative_text)}, "
        f"structured_response={'present' if structured_response else 'None'}, "
        f"raw_response_length={len(raw_response_text)}"
    )
    if len(narrative_text) == 0:
        # Include preview suffix only if response was truncated
        raw_preview = raw_response_text[:500]
        preview_suffix = "..." if len(raw_response_text) > 500 else ""
        logging_util.warning(
            f"⚠️ EMPTY_NARRATIVE: LLM returned empty narrative. "
            f"Raw response preview: {raw_preview}{preview_suffix}"
        )
        # Log structured response fields if available
        if structured_response:
            has_planning = bool(
                structured_response.planning_block
                if hasattr(structured_response, "planning_block")
                else False
            )
            has_session = bool(
                structured_response.session_header
                if hasattr(structured_response, "session_header")
                else False
            )
            logging_util.warning(
                f"⚠️ EMPTY_NARRATIVE: structured_response has planning_block={has_planning}, "
                f"session_header={has_session}"
            )

    # Create LLMResponse with proper debug content separation
    if structured_response:
        # Use structured response (preferred) - ensures clean separation
        gemini_response = LLMResponse.create_from_structured_response(
            structured_response, chosen_model
        )
    else:
        # Fallback to legacy mode for non-JSON responses
        gemini_response = LLMResponse.create_legacy(narrative_text, chosen_model)

    response_text: str = gemini_response.narrative_text

    # Validate entity tracking if enabled
    if expected_entities:
        # Use the common validation function for entity tracking validation
        # (No longer modifies response_text - validation goes to logs only)
        _validate_entity_tracking(response_text, expected_entities, current_game_state)

    # Validate and enforce planning block for story mode
    # Check if user is switching to god mode with their input
    user_input_lower: str = user_input.lower().strip()
    is_switching_to_god_mode: bool = user_input_lower in constants.MODE_SWITCH_SIMPLE

    # Also check if the AI response indicates DM MODE
    is_dm_mode_response: bool = (
        "[Mode: DM MODE]" in response_text or "[Mode: GOD MODE]" in response_text
    )

    # Only add planning blocks if:
    # 1. Currently in character mode
    # 2. User isn't switching to god mode
    # 3. AI response isn't in DM mode
    if (
        mode == constants.MODE_CHARACTER
        and not is_switching_to_god_mode
        and not is_dm_mode_response
    ):
        response_text = _validate_and_enforce_planning_block(
            response_text,
            user_input,
            current_game_state,
            chosen_model,
            system_instruction_final,
            structured_response=gemini_response.structured_response,
            provider_name=provider_selection.provider,
        )

    # MODERNIZED: No longer recreate LLMResponse based on response_text modifications
    # The structured_response is now the authoritative source, response_text is for backward compatibility only
    # The frontend uses gemini_response.structured_response directly, not narrative_text

    # Log LLMResponse creation - INFO level for production visibility
    logging_util.info(
        f"📝 FINAL_RESPONSE: narrative_length={len(gemini_response.narrative_text)}, "
        f"has_structured_response={gemini_response.structured_response is not None}"
    )

    # Return our custom LLMResponse object (not raw API response)
    # This object contains:
    # - narrative_text: Clean text for display (guaranteed to be clean narrative)
    # - structured_response: Parsed JSON structure with state updates, entities, etc.
    return gemini_response


def _get_static_prompt_parts(
    current_game_state: GameState, story_context: list[dict[str, Any]]
) -> tuple[str, str, str]:
    """Helper to generate the non-timeline parts of the prompt."""
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

    core_memories: list[str] = current_game_state.custom_campaign_state.get(
        "core_memories", []
    )
    core_memories_summary: str = ""
    if core_memories:
        core_memories_list: str = "\\n".join([f"- {item}" for item in core_memories])
        core_memories_summary = (
            f"CORE MEMORY LOG (SUMMARY OF KEY EVENTS):\\n{core_memories_list}\\n\\n"
        )

    checkpoint_block: str = (
        f"[CHECKPOINT BLOCK:]\\n"
        f"Sequence ID: {latest_seq_id} | Location: {current_location}\\n"
        f"{missions_summary}\\n"
        f"{ambition_summary}"
    )

    return checkpoint_block, core_memories_summary, sequence_id_list_string


def _extract_multiple_think_commands(user_input: str) -> list[str]:
    """
    Extract multiple 'Main Character: think' commands from user input.

    Returns:
        list: List of individual think commands, or [user_input] if no multiple commands found
    """
    # Pattern to match "Main Character: think..." commands
    think_pattern = r"Main Character:\s*think[^\n]*"
    matches = re.findall(think_pattern, user_input, re.IGNORECASE)

    if len(matches) > 1:
        return matches
    # No multiple commands found, return original input
    return [user_input]


def _get_current_turn_prompt(user_input: str, mode: str) -> str:
    """Helper to generate the text for the user's current action."""
    if mode == "character":
        # Check if user is requesting planning/thinking
        # Note: Thinking detection simplified to avoid hardcoded keyword lists
        user_input_lower = user_input.lower()
        is_think_command = "think" in user_input_lower or "plan" in user_input_lower

        # Check for multiple "Main Character: think" patterns using regex
        think_pattern = r"Main Character:\s*think[^\n]*"
        think_matches = re.findall(think_pattern, user_input, re.IGNORECASE)
        len(think_matches)

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
    # god mode
    prompt_template = "GOD MODE: {user_input}"
    return prompt_template.format(user_input=user_input)


def _validate_companion_generation(gemini_response: LLMResponse) -> None:
    """Validate companion generation results.

    Moved from world_logic.py to maintain Single Responsibility Principle.
    Companion validation should be near companion generation logic.

    Args:
        gemini_response: The response from Gemini to validate
    """
    structured_response = getattr(gemini_response, "structured_response", None)
    if not structured_response:
        logging_util.error(
            "🎭 COMPANION GENERATION: ❌ No structured response received from Gemini!"
        )
        return

    # Access companions and npc_data from extra_fields (since they're not standard schema fields)
    extra_fields = getattr(structured_response, "extra_fields", {})
    companions = extra_fields.get("companions", {})
    npc_data = extra_fields.get("npc_data", {})

    # Also check state_updates in case they're there
    state_updates = getattr(structured_response, "state_updates", {}) or {}
    if not npc_data and "npc_data" in state_updates:
        npc_data = state_updates["npc_data"]
    if not companions and "companions" in state_updates:
        companions = state_updates["companions"]

    # Type safety check and deduplication
    if not isinstance(companions, dict):
        companions = {}
    if not isinstance(npc_data, dict):
        npc_data = {}

    # Count unique companions (avoiding double-counting)
    companion_names = set(companions.keys())
    allied_npcs = {
        name
        for name, data in npc_data.items()
        if isinstance(data, dict) and data.get("relationship") in ["companion", "ally"]
    }
    # Remove any companions already counted to avoid double-counting
    unique_allied_npcs = allied_npcs - companion_names

    companion_count = len(companion_names)
    allied_npc_count = len(unique_allied_npcs)
    total_companions = companion_count + allied_npc_count

    # Minimal logging for companion validation
    if total_companions == 0:
        logging_util.warning("🎭 No companions generated despite request")
    elif total_companions < EXPECTED_COMPANION_COUNT:
        logging_util.warning(
            f"🎭 Only {total_companions}/{EXPECTED_COMPANION_COUNT} companions generated"
        )
    else:
        logging_util.info(f"🎭 {total_companions} companions generated successfully")


# --- Main block for rapid, direct testing ---
if __name__ == "__main__":
    print("--- Running llm_service.py in chained conversation test mode ---")

    try:
        # Look for Google API key in home directory first, then project root
        home_key_path = os.path.expanduser("~/.gemini_api_key.txt")
        project_key_path = "gemini_api_key.txt"

        if os.path.exists(home_key_path):
            api_key = read_file_cached(home_key_path).strip()
            print(f"Successfully loaded API key from {home_key_path}")
        elif os.path.exists(project_key_path):
            api_key = read_file_cached(project_key_path).strip()
            print(f"Successfully loaded API key from {project_key_path}")
        else:
            print(
                "\nERROR: API key not found in ~/.gemini_api_key.txt or gemini_api_key.txt"
            )
            sys.exit(1)

        os.environ["GEMINI_API_KEY"] = api_key
    except Exception as e:
        print(f"\nERROR: Failed to load API key: {e}")
        sys.exit(1)

    get_client()  # Initialize client

    # Example usage for testing: pass all prompt types
    test_selected_prompts = ["narrative", "mechanics", "calibration"]
    test_game_state = GameState(
        player_character_data={"name": "Test Character", "hp_current": 10},
        world_data={"current_location_name": "The Testing Grounds"},
        npc_data={},
        custom_campaign_state={},
    )

    # --- Turn 1: Initial Story ---
    print("\n--- Turn 1: get_initial_story ---")
    turn_1_prompt = "start a story about a haunted lighthouse"
    print(
        f"Using prompt: '{turn_1_prompt}' with selected prompts: {test_selected_prompts}"
    )
    turn_1_response = get_initial_story(
        turn_1_prompt, selected_prompts=test_selected_prompts
    )
    print("\n--- LIVE RESPONSE 1 ---")
    print(turn_1_response)
    print("--- END OF RESPONSE 1 ---\n")

    # Create the initial history from the real response
    history = [
        {"actor": "user", "text": turn_1_prompt},
        {"actor": "gemini", "text": turn_1_response},
    ]

    # --- Turn 2: Continue Story ---
    print("\n--- Turn 2: continue_story ---")
    turn_2_prompt = "A lone ship, tossed by the raging sea, sees a faint, flickering light from the abandoned tower."
    print(f"Using prompt: '{turn_2_prompt}'")
    turn_2_response = continue_story(
        turn_2_prompt,
        "god",
        history,
        test_game_state,
        selected_prompts=test_selected_prompts,
    )
    print("\n--- LIVE RESPONSE 2 ---")
    print(turn_2_response)
    print("--- END OF RESPONSE 2 ---\n")

    # Update the history with the real response from turn 2
    history.append({"actor": "user", "text": turn_2_prompt})
    history.append({"actor": "gemini", "text": turn_2_response})

    # --- Turn 3: Continue Story Again ---
    print("\n--- Turn 3: continue_story ---")
    turn_3_prompt = "The ship's captain, a grizzled old sailor named Silas, decides to steer towards the light, ignoring the warnings of his crew."
    print(f"Using prompt: '{turn_3_prompt}'")
    turn_3_response = continue_story(
        turn_3_prompt,
        "god",
        history,
        test_game_state,
        selected_prompts=test_selected_prompts,
    )
    print("\n--- LIVE RESPONSE 3 ---")
    print(turn_3_response)
    print("--- END OF RESPONSE 3 ---\n")
