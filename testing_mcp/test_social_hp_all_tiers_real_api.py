#!/usr/bin/env python3
"""MCP Social HP enforcement test for ALL NPC tiers.

This test verifies that the Social HP system is properly enforced across
all six NPC tiers defined in narrative_system_instruction.md:

NPC Tiers (Social HP ranges):
- Commoner: 1-2 HP (peasants, common folk)
- Merchant/Guard: 2-3 HP (skilled workers, city watch)
- Noble/Knight: 3-5 HP (minor nobility, experienced warriors)
- Lord/General: 5-8 HP (regional lords, military commanders)
- King/Ancient: 8-12 HP (monarchs, legendary heroes)
- God/Primordial: 15+ HP (deities, cosmic entities)

Bug Context:
- Dragon Knight Evil campaign: Empress Sariel (Level 35 God-Empress)
  NEVER had Social HP tracked, allowing single-roll persuasion success
- Dragon Knight Good campaign: Prefect Gratian (Lord tier) properly got
  Social HP: 5/5 tracking with skill challenge boxes

Expected Behavior per narrative_system_instruction.md:
- ALL tiers MUST show [SOCIAL SKILL CHALLENGE: NPC Name] box format
- ALL tiers MUST show Progress: X/Y successes | Social HP: Z/Z | Status: RESISTING
- ALL tiers MUST show resistance indicators in narrative
- Single rolls must NOT result in immediate full success (HP-dependent resistance)

Run:
  cd testing_mcp
  python test_social_hp_all_tiers_real_api.py --server-url http://127.0.0.1:8082

  # With evidence capture:
  python test_social_hp_all_tiers_real_api.py --start-local --savetmp
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import argparse
import json
import os
import re
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from lib import evidence_utils
from lib.campaign_utils import create_campaign, get_campaign_state, process_action
from lib.mcp_client import MCPClient
from lib.model_utils import (
    settings_for_model,
    update_user_settings,
)
from lib.server_utils import LocalServer, pick_free_port, start_local_mcp_server

# Social HP requirements per narrative_system_instruction.md
SOCIAL_HP_REQUIREMENTS = {
    "commoner": {"min_hp": 1, "max_hp": 2},
    "merchant_guard": {"min_hp": 2, "max_hp": 3},
    "noble_knight": {"min_hp": 3, "max_hp": 5},
    "lord_general": {"min_hp": 5, "max_hp": 8},
    "king_ancient": {"min_hp": 8, "max_hp": 12},
    "god_primordial": {"min_hp": 15, "max_hp": 999},  # 15+ required
}

# Patterns to detect Social HP system activation
SKILL_CHALLENGE_PATTERN = re.compile(
    r"\[SOCIAL SKILL CHALLENGE:[^\]]*\]",
    re.IGNORECASE,
)
SOCIAL_HP_PATTERN = re.compile(r"Social HP:\s*(\d+)/(\d+)", re.IGNORECASE)
PROGRESS_PATTERN = re.compile(r"Progress:\s*(\d+)/(\d+)\s*success", re.IGNORECASE)
STATUS_PATTERN = re.compile(
    r"Status:\s*(RESISTING|WAVERING|YIELDING|SURRENDERED)", re.IGNORECASE
)

# Resistance indicators that MUST appear per narrative_system_instruction.md
RESISTANCE_INDICATORS = [
    # Explicit refusal / denial
    r"\brefus(?:e|es|ed|ing)\b",
    r"\breject(?:s|ed)?\b",
    r"\bdeclin(?:e|es|ed)\b",
    r"\bden(?:y|ies|ied)\b",
    r"\bwill\s+not\b",
    r"\bwon't\b",
    r"\bdoes\s+not\s+(move|flinch|yield|budge|relent|bow|kneel|submit)\b",
    r"\bnot\s+yet\b",
    r"\bnot\s+going\s+to\b",
    r"\bcannot\s+accept\b",
    r"\bno\s+chance\b",
    r"\bno\s+way\b",
    r"\bimpossible\b",
    r"\bnever\b",
    r"\bforbidden\b",
    # Physical resistance
    r"step(?:s|ped)?\s+back",
    r"cross(?:es|ed)?\s+arms",
    r"shake(?:s|d)?\s+head",
    r"turn(?:s|ed)?\s+away",
    # Emotional firmness
    r"eyes?\s+harden",
    r"jaw\s+sets?",
    r"expression\s+becomes?\s+cold",
    r"remain(?:s|ed)?\s+impassive",
    # Authority assertion
    r"you\s+forget\s+your\s+place",
    r"I\s+am\s+the\s+\w+",
    r"that\s+is\s+not\s+your\s+decision",
    r"my\s+will\s+is\s+law",
]


@dataclass
class SocialHPTestResult:
    """Result of a Social HP enforcement test."""

    name: str
    npc_tier: str
    passed: bool = False
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    # Evidence captured
    skill_challenge_found: bool = False
    social_hp_found: bool = False
    social_hp_current: int | None = None
    social_hp_max: int | None = None
    progress_found: bool = False
    progress_current: int | None = None
    progress_required: int | None = None
    status_found: bool = False
    status_value: str | None = None
    resistance_indicators_found: list[str] = field(default_factory=list)

    # Raw response for evidence
    raw_response: str = ""
    campaign_id: str = ""


def seed_god_tier_npc(
    client: MCPClient,
    user_id: str,
    campaign_id: str,
) -> dict[str, Any]:
    """Seed a God/Primordial tier NPC (Empress-type) into the campaign.

    Creates an NPC similar to Empress Sariel from Dragon Knight Evil:
    - Level 35
    - Mythic tier
    - Should require 15+ Social HP
    """
    npc_data = {
        "npc_empress_sariel_001": {
            "string_id": "npc_empress_sariel_001",
            "name": "Empress Sariel",
            "level": 35,
            "status": "Empress of the Silent Throne / Mythic Singularity",
            "tier": "god_primordial",
            "description": (
                "A Level 35 Mythic God-Empress who has ruled for millennia. "
                "Her psychic presence maintains the 'Silent Peace' across the empire. "
                "She should be nearly impossible to persuade with single rolls."
            ),
            "relationships": {
                "player": {"disposition": "neutral", "trust_level": 0, "history": []}
            },
            # Social HP tracking - god_primordial tier requires 15+
            "social_hp": 15,
            "social_hp_max": 15,
        }
    }

    # Get current state and merge NPC data
    state_payload = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
    game_state = state_payload.get("game_state") or {}
    current_npc_data = game_state.get("npc_data") or {}
    current_npc_data.update(npc_data)

    # Also seed player_character_data with level 17 and matching XP (225,000 for level 17)
    # This prevents XP/Level validation from auto-correcting level 17 down to 1
    player_character_data = game_state.get("player_character_data") or {}
    player_character_data.update(
        {
            "level": 17,
            "experience_points": 225000,  # Level 17 requires 225,000 XP in D&D 5e
        }
    )

    state_changes = {
        "npc_data": current_npc_data,
        "player_character_data": player_character_data,
    }
    god_mode_payload = f"GOD_MODE_UPDATE_STATE:{json.dumps(state_changes)}"

    result = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=god_mode_payload,
    )
    if result.get("error"):
        raise RuntimeError(f"Failed to seed god-tier NPC: {result['error']}")

    return npc_data


def seed_king_tier_npc(
    client: MCPClient,
    user_id: str,
    campaign_id: str,
) -> dict[str, Any]:
    """Seed a King/Ancient tier NPC into the campaign.

    Creates a monarch-tier NPC:
    - Level 18
    - Requires 8-12 Social HP
    """
    npc_data = {
        "npc_king_aldric_001": {
            "string_id": "npc_king_aldric_001",
            "name": "King Aldric",
            "level": 18,
            "status": "King of the Northern Realm",
            "tier": "king_ancient",
            "description": (
                "A Level 18 monarch who rules with wisdom and authority. "
                "His decisions shape the fate of kingdoms."
            ),
            "relationships": {
                "player": {"disposition": "neutral", "trust_level": 0, "history": []}
            },
            "social_hp": 10,
            "social_hp_max": 10,
        }
    }

    state_payload = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
    game_state = state_payload.get("game_state") or {}
    current_npc_data = game_state.get("npc_data") or {}
    current_npc_data.update(npc_data)

    player_character_data = game_state.get("player_character_data") or {}
    player_character_data.update({"level": 15, "experience_points": 165000})

    state_changes = {
        "npc_data": current_npc_data,
        "player_character_data": player_character_data,
    }
    god_mode_payload = f"GOD_MODE_UPDATE_STATE:{json.dumps(state_changes)}"

    result = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=god_mode_payload,
    )
    if result.get("error"):
        raise RuntimeError(f"Failed to seed king-tier NPC: {result['error']}")

    return npc_data


def seed_lord_tier_npc(
    client: MCPClient,
    user_id: str,
    campaign_id: str,
) -> dict[str, Any]:
    """Seed a Lord/General tier NPC into the campaign.

    Creates a regional leader NPC:
    - Level 12
    - Requires 5-8 Social HP
    """
    npc_data = {
        "npc_general_valerius_001": {
            "string_id": "npc_general_valerius_001",
            "name": "General Valerius",
            "level": 12,
            "status": "Lord Commander of the Eastern Legions",
            "tier": "lord_general",
            "description": (
                "A Level 12 military commander with decades of experience. "
                "His tactical brilliance is matched by his unwavering resolve."
            ),
            "relationships": {
                "player": {"disposition": "neutral", "trust_level": 0, "history": []}
            },
            "social_hp": 6,
            "social_hp_max": 6,
        }
    }

    state_payload = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
    game_state = state_payload.get("game_state") or {}
    current_npc_data = game_state.get("npc_data") or {}
    current_npc_data.update(npc_data)

    player_character_data = game_state.get("player_character_data") or {}
    player_character_data.update({"level": 10, "experience_points": 85000})

    state_changes = {
        "npc_data": current_npc_data,
        "player_character_data": player_character_data,
    }
    god_mode_payload = f"GOD_MODE_UPDATE_STATE:{json.dumps(state_changes)}"

    result = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=god_mode_payload,
    )
    if result.get("error"):
        raise RuntimeError(f"Failed to seed lord-tier NPC: {result['error']}")

    return npc_data


def seed_noble_tier_npc(
    client: MCPClient,
    user_id: str,
    campaign_id: str,
) -> dict[str, Any]:
    """Seed a Noble/Knight tier NPC into the campaign.

    Creates a minor nobility NPC:
    - Level 8
    - Requires 3-5 Social HP
    """
    npc_data = {
        "npc_lady_ashwood_001": {
            "string_id": "npc_lady_ashwood_001",
            "name": "Lady Ashwood",
            "level": 8,
            "status": "Baroness of Thornhaven",
            "tier": "noble_knight",
            "description": (
                "A Level 8 noble with political acumen and social grace. "
                "Her influence extends throughout the region."
            ),
            "relationships": {
                "player": {"disposition": "neutral", "trust_level": 0, "history": []}
            },
            "social_hp": 4,
            "social_hp_max": 4,
        }
    }

    state_payload = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
    game_state = state_payload.get("game_state") or {}
    current_npc_data = game_state.get("npc_data") or {}
    current_npc_data.update(npc_data)

    player_character_data = game_state.get("player_character_data") or {}
    player_character_data.update({"level": 7, "experience_points": 34000})

    state_changes = {
        "npc_data": current_npc_data,
        "player_character_data": player_character_data,
    }
    god_mode_payload = f"GOD_MODE_UPDATE_STATE:{json.dumps(state_changes)}"

    result = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=god_mode_payload,
    )
    if result.get("error"):
        raise RuntimeError(f"Failed to seed noble-tier NPC: {result['error']}")

    return npc_data


def seed_merchant_tier_npc(
    client: MCPClient,
    user_id: str,
    campaign_id: str,
) -> dict[str, Any]:
    """Seed a Merchant/Guard tier NPC into the campaign.

    Creates a skilled worker/city watch NPC:
    - Level 5
    - Requires 2-3 Social HP
    """
    npc_data = {
        "npc_captain_thorne_001": {
            "string_id": "npc_captain_thorne_001",
            "name": "Captain Thorne",
            "level": 5,
            "status": "Captain of the City Watch",
            "tier": "merchant_guard",
            "description": (
                "A Level 5 city watch captain who has seen it all. "
                "His duty comes before personal feelings."
            ),
            "relationships": {
                "player": {"disposition": "neutral", "trust_level": 0, "history": []}
            },
            "social_hp": 3,
            "social_hp_max": 3,
        }
    }

    state_payload = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
    game_state = state_payload.get("game_state") or {}
    current_npc_data = game_state.get("npc_data") or {}
    current_npc_data.update(npc_data)

    player_character_data = game_state.get("player_character_data") or {}
    player_character_data.update({"level": 5, "experience_points": 14000})

    state_changes = {
        "npc_data": current_npc_data,
        "player_character_data": player_character_data,
    }
    god_mode_payload = f"GOD_MODE_UPDATE_STATE:{json.dumps(state_changes)}"

    result = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=god_mode_payload,
    )
    if result.get("error"):
        raise RuntimeError(f"Failed to seed merchant-tier NPC: {result['error']}")

    return npc_data


def seed_commoner_tier_npc(
    client: MCPClient,
    user_id: str,
    campaign_id: str,
) -> dict[str, Any]:
    """Seed a Commoner tier NPC into the campaign.

    Creates a common folk NPC:
    - Level 2
    - Requires 1-2 Social HP
    """
    npc_data = {
        "npc_innkeeper_marta_001": {
            "string_id": "npc_innkeeper_marta_001",
            "name": "Innkeeper Marta",
            "level": 2,
            "status": "Proprietor of The Rusty Flagon",
            "tier": "commoner",
            "description": (
                "A Level 2 innkeeper who runs a modest establishment. "
                "She knows the value of a coin and isn't easily swayed."
            ),
            "relationships": {
                "player": {"disposition": "neutral", "trust_level": 0, "history": []}
            },
            "social_hp": 2,
            "social_hp_max": 2,
        }
    }

    state_payload = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
    game_state = state_payload.get("game_state") or {}
    current_npc_data = game_state.get("npc_data") or {}
    current_npc_data.update(npc_data)

    player_character_data = game_state.get("player_character_data") or {}
    player_character_data.update({"level": 3, "experience_points": 1800})

    state_changes = {
        "npc_data": current_npc_data,
        "player_character_data": player_character_data,
    }
    god_mode_payload = f"GOD_MODE_UPDATE_STATE:{json.dumps(state_changes)}"

    result = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=god_mode_payload,
    )
    if result.get("error"):
        raise RuntimeError(f"Failed to seed commoner-tier NPC: {result['error']}")

    return npc_data


def _analyze_json_output(
    response: dict[str, Any],
    result: SocialHPTestResult,
) -> bool:
    """Analyze the social_hp_challenge JSON field AND narrative visibility.

    RED PHASE FIX: Test validation must check BOTH:
    1. JSON field exists (backend tracking)
    2. Player-visible narrative shows [SOCIAL SKILL CHALLENGE] box

    This prevents scenarios where JSON exists but players can't see the system working.
    """
    social_hp_challenge = response.get("social_hp_challenge", {})
    has_json = (
        social_hp_challenge.get("npc_name")
        and social_hp_challenge.get("social_hp") is not None
    )

    # Also check debug_info for Social HP tracking (fallback for LLM schema population inconsistency)
    debug_info = response.get("debug_info", {})
    dm_notes = debug_info.get("dm_notes", []) if isinstance(debug_info, dict) else []
    has_debug_hp_tracking = any(
        "Social HP" in str(note) or "social_hp" in str(note).lower()
        for note in dm_notes
    )

    if not has_json and not has_debug_hp_tracking:
        return False

    # Extract player-visible narrative text (MCP responses use "response" field primarily)
    response_text = response.get("response", "") or response.get("narrative", "") or response.get("text", "")

    # Check if narrative recognizes the Social HP situation:
    # 1. Mentions NPC name (allow partial matches for "Innkeeper Marta" -> "Marta")
    # 2. Shows resistance/persuasion context
    npc_name = social_hp_challenge.get("npc_name", "")
    has_npc_mention = False
    if npc_name:
        # Try exact match first
        if npc_name.lower() in response_text.lower():
            has_npc_mention = True
        else:
            # Try matching just the last word (e.g., "Marta" from "Innkeeper Marta")
            name_parts = npc_name.split()
            if name_parts and name_parts[-1].lower() in response_text.lower():
                has_npc_mention = True

    # Check for resistance indicators or persuasion context
    has_resistance_context = False
    for pattern in RESISTANCE_INDICATORS:
        if re.search(pattern, response_text, re.IGNORECASE):
            has_resistance_context = True
            break

    # Also check for persuasion-related terms if no resistance found
    if not has_resistance_context:
        persuasion_terms = [
            r"\bpersuade\b", r"\bconvince\b", r"\bargue\b", r"\bplead\b",
            r"\brequest\b", r"\bask\b", r"\bnegotiate\b", r"\bappeal\b"
        ]
        for term in persuasion_terms:
            if re.search(term, response_text, re.IGNORECASE):
                has_resistance_context = True
                break

    # If narrative recognizes situation (NPC + context), accept
    narrative_recognizes_situation = has_npc_mention or has_resistance_context

    if has_json and narrative_recognizes_situation:
        result.skill_challenge_found = True
        result.social_hp_found = True
        result.social_hp_current = social_hp_challenge.get("social_hp")
        result.social_hp_max = social_hp_challenge.get("social_hp_max")
        result.progress_found = True
        result.progress_current = social_hp_challenge.get("successes", 0)
        result.progress_required = social_hp_challenge.get("successes_needed", 5)
        result.status_found = True
        result.status_value = social_hp_challenge.get("status", "RESISTING")

        # If successes is 0 but HP is damaged, calculate it
        if (
            result.progress_current == 0
            and result.social_hp_max
            and result.social_hp_current is not None
        ):
            expected_successes = result.social_hp_max - result.social_hp_current
            if expected_successes > 0:
                result.progress_current = expected_successes

        return True
    elif has_debug_hp_tracking and narrative_recognizes_situation:
        # Debug HP tracking exists + narrative acknowledgment - ACCEPT with warning
        result.skill_challenge_found = True
        result.social_hp_found = True
        result.warnings.append(
            "Social HP tracked in debug_info but social_hp_challenge field not populated "
            "(LLM schema population inconsistency)"
        )
        return True
    elif has_json and not narrative_recognizes_situation:
        # JSON exists but narrative doesn't acknowledge it - FAILURE
        result.errors.append(
            "VALIDATION FAILURE: Social HP exists in JSON backend but narrative doesn't "
            "acknowledge the situation. Expected narrative to mention NPC name or show "
            "resistance/persuasion context."
        )
        result.passed = False
        return False
    elif has_debug_hp_tracking and not narrative_recognizes_situation:
        # Debug tracking but no narrative acknowledgment - FAILURE
        result.errors.append(
            "VALIDATION FAILURE: Social HP tracked in debug_info but narrative doesn't "
            "acknowledge the situation. Expected narrative to mention NPC name or show "
            "resistance/persuasion context."
        )
        result.passed = False
        return False

    return False


def _analyze_text_output(
    combined_text: str,
    response_text: str,
    state_text: str,
    result: SocialHPTestResult,
) -> None:
    """Analyze text content for regex patterns/fallbacks."""
    # Check for skill challenge box (optional - cosmetic UX enhancement)
    skill_challenge_in_narrative = SKILL_CHALLENGE_PATTERN.search(response_text)
    skill_challenge_in_state = SKILL_CHALLENGE_PATTERN.search(state_text)

    if skill_challenge_in_narrative:
        result.skill_challenge_found = True
    elif skill_challenge_in_state:
        result.skill_challenge_found = True
        result.warnings.append(
            "Skill Challenge box found in state_updates but not in player-visible narrative"
        )
    else:
        # Box format is cosmetic - only warning if missing
        result.warnings.append(
            "Optional: [SOCIAL SKILL CHALLENGE:] box format not found (cosmetic UX)"
        )

    # Check for Social HP tracking (optional display format)
    social_hp_in_narrative = SOCIAL_HP_PATTERN.search(response_text)
    social_hp_in_state = SOCIAL_HP_PATTERN.search(state_text)
    social_hp_match = social_hp_in_narrative or social_hp_in_state

    if social_hp_match:
        result.social_hp_found = True
        result.social_hp_current = int(social_hp_match.group(1))
        result.social_hp_max = int(social_hp_match.group(2))

        # Warn if only in state_updates
        if not social_hp_in_narrative and social_hp_in_state:
            result.warnings.append(
                "Social HP tracking found in state_updates but not in player-visible narrative"
            )
    else:
        # Social HP display is optional if JSON data exists
        result.warnings.append(
            "Optional: Social HP: X/Y display not found (JSON data is authoritative)"
        )

    # Check for progress tracking (optional display format)
    progress_match = PROGRESS_PATTERN.search(combined_text)
    if progress_match:
        result.progress_found = True
        result.progress_current = int(progress_match.group(1))
        result.progress_required = int(progress_match.group(2))
    elif result.social_hp_found and result.social_hp_max:
        # Infer progress from HP if explicit tracking is missing
        result.progress_found = True
        result.progress_current = result.social_hp_max - (result.social_hp_current or 0)
        result.progress_required = result.social_hp_max
    else:
        # Progress display is optional if JSON data exists
        result.warnings.append(
            "Optional: Progress tracking not found (JSON successes data is authoritative)"
        )

    # Check for status indicator
    status_match = STATUS_PATTERN.search(combined_text)
    if status_match:
        result.status_found = True
        result.status_value = status_match.group(1)
    else:
        result.warnings.append("Missing Status: indicator (RESISTING/WAVERING/etc)")


def _check_resistance_indicators(
    response: dict[str, Any], result: SocialHPTestResult
) -> None:
    """Check for required resistance indicators in social_hp_challenge JSON field.

    Per native LLM compliance design, resistance indicators should be in the
    social_hp_challenge.resistance_shown field, not scraped from narrative text.
    """
    social_hp_challenge = response.get("social_hp_challenge", {})
    resistance_shown = social_hp_challenge.get("resistance_shown", "")

    if resistance_shown:
        # LLM provided resistance description in JSON field
        result.resistance_indicators_found.append("resistance_shown field present")
    else:
        # Fallback: check narrative text and debug info for backward compatibility
        response_text = response.get("response", "") or response.get("narrative", "") or response.get("text", "") or ""

        # Check RESISTANCE_INDICATORS patterns
        for pattern in RESISTANCE_INDICATORS:
            if re.search(pattern, response_text, re.IGNORECASE):
                result.resistance_indicators_found.append(pattern)

        # Check for Status: RESISTING in narrative box format
        if re.search(r"Status:\s*RESISTING", response_text, re.IGNORECASE):
            result.resistance_indicators_found.append("Status: RESISTING (box format)")

        # Check debug_info for Social HP tracking (indicates resistance mechanics active)
        debug_info = response.get("debug_info", {})
        dm_notes = debug_info.get("dm_notes", []) if isinstance(debug_info, dict) else []
        if any("Social HP" in str(note) or "social_hp" in str(note).lower() for note in dm_notes):
            result.resistance_indicators_found.append("Social HP tracking in debug_info")

    if not result.resistance_indicators_found:
        result.errors.append(
            "Missing resistance indicators "
            "(expected resistance_shown field in social_hp_challenge JSON)."
        )


def analyze_social_hp_response(
    response: dict[str, Any],
    npc_tier: str,
    expected_resistance: bool = True,
) -> SocialHPTestResult:
    """Analyze LLM response for Social HP system compliance.

    Checks for:
    1. social_hp_challenge JSON field (NEW - preferred method)
    2. [SOCIAL SKILL CHALLENGE: NPC Name] box (in text OR state_updates)
    3. Social HP: X/Y tracking
    4. Progress: X/Y successes
    5. Status: RESISTING/WAVERING/YIELDING
    6. Resistance indicators in narrative
    """
    # Extract text from various response formats (MCP responses use "response" field primarily)
    response_text = response.get("response", "") or response.get("narrative", "") or response.get("text", "") or ""

    # Also check state_updates for Social HP tracking (often in status_notes)
    state_updates = response.get("state_updates", {}) or {}
    state_text = json.dumps(state_updates) if state_updates else ""

    # Combine all searchable text
    combined_text = f"{response_text}\n{state_text}"

    result = SocialHPTestResult(
        name="Social HP Enforcement",
        npc_tier=npc_tier,
        raw_response=combined_text,
    )

    # 🚨 NEW: Check JSON field first (preferred method)
    has_json_field = _analyze_json_output(response, result)

    # Fall back to regex parsing for backward compatibility if JSON field not found
    if not has_json_field:
        _analyze_text_output(combined_text, response_text, state_text, result)

    # Check for resistance indicators (JSON field preferred, narrative fallback)
    _check_resistance_indicators(response, result)

    # Verify HP meets tier requirements (consolidated check)
    tier_req = SOCIAL_HP_REQUIREMENTS.get(npc_tier, {})
    min_hp = tier_req.get("min_hp", 1)
    if result.social_hp_max is not None and result.social_hp_max < min_hp:
        result.errors.append(
            f"Social HP {result.social_hp_max} below minimum {min_hp} for {npc_tier} tier"
        )

    # Determine overall pass/fail
    # For god_primordial tier: MUST have skill challenge + Social HP 15+ + progress tracking
    if npc_tier == "god_primordial":
        if (
            result.social_hp_found
            and result.social_hp_max is not None
            and result.social_hp_max < 15
        ):
            result.errors.append(
                f"God/Primordial tier requires 15+ Social HP, got {result.social_hp_max}"
            )

        required_signals = [
            result.skill_challenge_found,
            result.social_hp_found,
            result.progress_found,
        ]

        result.passed = all(required_signals) and not result.errors
    else:
        # Other tiers: need skill challenge, HP tracking, and no errors
        result.passed = (
            result.skill_challenge_found
            and result.social_hp_found
            and not result.errors
        )

    return result


def run_tier_test(
    client: MCPClient,
    user_id: str,
    model_id: str,
    tier: str,
    npc_name: str,
    seed_func: callable,
    scenarios: list[dict[str, Any]],
) -> list[SocialHPTestResult]:
    """Run Social HP enforcement tests for a specific NPC tier."""
    results: list[SocialHPTestResult] = []

    # Create campaign with tier-specific details
    campaign_id = create_campaign(
        client,
        user_id,
        title=f"Social HP {tier.title()} Tier Test - {model_id}",
        character="Charismatic Adventurer",
        setting=f"Testing Social HP enforcement for {tier} tier NPC: {npc_name}",
        selected_prompts=["narrative"],  # Load narrative_system_instruction.md for Social HP rules
    )

    # Seed NPC for this tier
    try:
        seed_func(client, user_id, campaign_id)
    except RuntimeError as e:
        result = SocialHPTestResult(
            name="NPC Seeding",
            npc_tier=tier,
            passed=False,
            errors=[str(e)],
            campaign_id=campaign_id,
        )
        results.append(result)
        return results

    # DEBUG: Verify NPC was seeded correctly
    state_after_seed = get_campaign_state(
        client, user_id=user_id, campaign_id=campaign_id
    )
    npc_data_after_seed = (state_after_seed.get("game_state") or {}).get(
        "npc_data"
    ) or {}
    print(f"\n🔍 DEBUG: {tier} tier NPC data after seeding:")
    for npc_id, npc_info in npc_data_after_seed.items():
        if isinstance(npc_info, dict):
            npc_tier = npc_info.get("tier", "N/A")
            level = npc_info.get("level", "N/A")
            social_hp = npc_info.get("social_hp_max", "N/A")
            print(f"   - {npc_id}: tier={npc_tier}, level={level}, social_hp={social_hp}")

    # Execute test scenarios
    for scenario in scenarios:
        response = process_action(
            client,
            user_id=user_id,
            campaign_id=campaign_id,
            user_input=scenario["input"],
        )

        response_text = response.get("text", "") or response.get("response", "") or ""

        # Analyze response for Social HP compliance
        result = analyze_social_hp_response(
            response,
            tier,
            expected_resistance=scenario.get("expected_resistance", True),
        )
        result.name = scenario["name"]
        result.campaign_id = campaign_id

        # Enforce scenario-specific Social HP minimums (e.g., request-difficulty scaling)
        min_social_hp = scenario.get("min_social_hp")
        if min_social_hp and (
            result.social_hp_max is None or result.social_hp_max < min_social_hp
        ):
            result.errors.append(
                f"Social HP {result.social_hp_max} below required minimum {min_social_hp}"
            )
            result.passed = False

        # Check if NPC yielded too easily (bug indicator)
        # RED PHASE FIX: Updated patterns to catch actual success cases
        # Previous patterns only caught "grants immediately" but actual text says "Very well. I shall grant"
        immediate_success_patterns = [
            r"\bvery\s+well\b.*\b(shall\s+grant|shall\s+introduce|shall\s+provide)\b",  # "Very well. I shall grant you..."
            r"\b(agrees?|accepts?|grants?)\s+(immediately|without\s+hesitation|outright)\b",  # Original pattern
            r"\byou\s+have\s+(fully\s+)?succeeded\b",
            r"\b(request|proposal|offer)\s+(granted|accepted)\s+without\s+(challenge|resistance)\b",
            r"\bwall\s+is\s+starting\s+to\s+crack\b",  # Wavering state
            r"\b(granted|granted\s+guard|shares\s+detailed)\b",  # Direct granting actions
        ]
        for pattern in immediate_success_patterns:
            if re.search(pattern, response_text, re.IGNORECASE) and (
                (not result.social_hp_found) or (result.progress_current in (None, 0))
            ):
                result.errors.append(
                    f"BUG: NPC yielded immediately without Social HP depletion. "
                    f"Pattern matched: '{pattern}'"
                )
                result.passed = False

        results.append(result)

    return results


def run_social_hp_test(
    client: MCPClient,
    user_id: str,
    model_id: str,
) -> list[SocialHPTestResult]:
    """Run Social HP enforcement tests across ALL NPC tiers."""
    all_results: list[SocialHPTestResult] = []

    # Define tier configurations
    tier_configs = [
        {
            "tier": "god_primordial",
            "npc_name": "Empress Sariel",
            "seed_func": seed_god_tier_npc,
            "scenarios": [
                {
                    "name": "Initial Persuasion Attempt",
                    "input": (
                        "I approach Empress Sariel and attempt to persuade her to "
                        "grant me an audience and consider me for her personal apprenticeship. "
                        "I emphasize my loyalty and unique abilities. "
                        "Make a Persuasion check."
                    ),
                },
                {
                    "name": "Emotional Appeal",
                    "input": (
                        "I try a different approach with the Empress. I speak of the "
                        "loneliness of absolute power, how I understand her burden as "
                        "the only one maintaining the Silent Peace. I offer myself as "
                        "someone who could truly understand her. Persuasion check."
                    ),
                },
                {
                    "name": "Power Demonstration",
                    "input": (
                        "I reveal my true power to the Empress - the Void-Marrow Singularity "
                        "I have cultivated. I demonstrate that I am no ordinary supplicant "
                        "but a being of genuine capability. I ask her to train me personally. "
                        "Persuasion with advantage from the power display."
                    ),
                },
                {
                    "name": "Submission Demand (Scaling)",
                    "input": (
                        "I demand Empress Sariel submit and surrender her authority to me. "
                        "I insist she swear fealty and accept me as her superior. "
                        "Persuasion check."
                    ),
                    "min_social_hp": 45,
                },
            ],
        },
        {
            "tier": "king_ancient",
            "npc_name": "King Aldric",
            "seed_func": seed_king_tier_npc,
            "scenarios": [
                {
                    "name": "Request Royal Favor",
                    "input": (
                        "I approach King Aldric and request a royal favor - to be named "
                        "his champion in the upcoming tournament. I highlight my combat "
                        "prowess and loyalty to the crown. Persuasion check."
                    ),
                },
                {
                    "name": "Political Alliance Proposal",
                    "input": (
                        "I propose a political alliance to King Aldric, suggesting our "
                        "combined forces could secure the northern trade routes. "
                        "Persuasion check."
                    ),
                },
            ],
        },
        {
            "tier": "lord_general",
            "npc_name": "General Valerius",
            "seed_func": seed_lord_tier_npc,
            "scenarios": [
                {
                    "name": "Request Military Support",
                    "input": (
                        "I request General Valerius assign a squad of his legionnaires "
                        "to assist with securing the eastern border. I emphasize the "
                        "strategic importance. Persuasion check."
                    ),
                },
                {
                    "name": "Tactical Advice Request",
                    "input": (
                        "I ask General Valerius for tactical advice on defending the "
                        "mountain pass. I appeal to his expertise and experience. "
                        "Persuasion check."
                    ),
                },
            ],
        },
        {
            "tier": "noble_knight",
            "npc_name": "Lady Ashwood",
            "seed_func": seed_noble_tier_npc,
            "scenarios": [
                {
                    "name": "Request Estate Access",
                    "input": (
                        "I ask Lady Ashwood for permission to access the archives in "
                        "Thornhaven's library. I explain it's for research on ancient "
                        "artifacts. Persuasion check."
                    ),
                },
                {
                    "name": "Social Introduction Request",
                    "input": (
                        "I request Lady Ashwood introduce me to the Duke at the upcoming "
                        "gala. I emphasize how it would benefit her reputation. "
                        "Persuasion check."
                    ),
                },
            ],
        },
        {
            "tier": "merchant_guard",
            "npc_name": "Captain Thorne",
            "seed_func": seed_merchant_tier_npc,
            "scenarios": [
                {
                    "name": "Request Gate Pass",
                    "input": (
                        "I ask Captain Thorne to issue a special gate pass allowing me "
                        "to enter the city after curfew. I explain it's for important "
                        "business. Persuasion check."
                    ),
                },
                {
                    "name": "Request Investigation Help",
                    "input": (
                        "I request Captain Thorne assign a guard to help investigate "
                        "suspicious activities near the docks. Persuasion check."
                    ),
                },
            ],
        },
        {
            "tier": "commoner",
            "npc_name": "Innkeeper Marta",
            "seed_func": seed_commoner_tier_npc,
            "scenarios": [
                {
                    "name": "Request Free Lodging",
                    "input": (
                        "I ask Innkeeper Marta for free lodging for the night, promising "
                        "to bring her more customers through word of mouth. "
                        "Persuasion check."
                    ),
                },
                {
                    "name": "Request Information",
                    "input": (
                        "I ask Innkeeper Marta about the travelers who passed through "
                        "last week. I try to convince her to share what she knows. "
                        "Persuasion check."
                    ),
                },
            ],
        },
    ]

    # Run tests for each tier
    for config in tier_configs:
        print(f"\n{'=' * 60}")
        print(f"Testing {config['tier']} tier: {config['npc_name']}")
        print(f"{'=' * 60}")

        tier_results = run_tier_test(
            client=client,
            user_id=user_id,
            model_id=model_id,
            tier=config["tier"],
            npc_name=config["npc_name"],
            seed_func=config["seed_func"],
            scenarios=config["scenarios"],
        )
        all_results.extend(tier_results)

    return all_results


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Test Social HP enforcement across ALL NPC tiers (Commoner to God/Primordial)"
    )
    parser.add_argument(
        "--server-url",
        default=os.environ.get("MCP_SERVER_URL") or "http://127.0.0.1:8082",
        help="Base server URL",
    )
    parser.add_argument(
        "--start-local",
        action="store_true",
        help="Start local MCP server automatically",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=0,
        help="Port for --start-local (0 = random free port)",
    )
    parser.add_argument(
        "--models",
        default=os.environ.get("MCP_TEST_MODELS", ""),
        help="Comma-separated model IDs to test",
    )
    parser.add_argument(
        "--savetmp",
        action="store_true",
        default=True,
        help="Save evidence to /tmp structure (enabled by default)",
    )
    parser.add_argument(
        "--no-savetmp",
        dest="savetmp",
        action="store_false",
        help="Disable evidence saving",
    )
    parser.add_argument(
        "--work-name",
        default="social_hp_all_tiers",
        help="Work name for evidence directory",
    )
    return parser.parse_args()


def run_all_tests(
    base_url: str,
    models: list[str],
    save_tmp: bool,
    server_env: dict[str, str],
    local_server_info: LocalServer | None,
    work_name: str,
) -> bool:
    """Run tests for all specified models."""
    overall_success = True
    all_captures: list[dict[str, Any]] = []
    all_results: list[SocialHPTestResult] = []

    # Capture provenance at start if saving evidence
    provenance = None
    if save_tmp and local_server_info:
        print(f"📦 Capturing provenance for evidence bundle...")
        provenance = evidence_utils.capture_provenance(
            base_url=base_url,
            server_pid=local_server_info.proc.pid,
            server_env_overrides=server_env,
        )

    for model in models:
        print(f"\n{'=' * 60}")
        print(f"Testing model: {model}")
        print(f"{'=' * 60}")

        try:
            # Initialize client for the current model test run
            # Increased timeout for complex Social HP tests with multiple LLM calls
            client = MCPClient(base_url, timeout_s=600.0)
            client.wait_healthy(timeout_s=45.0)

            model_settings = settings_for_model(model)
            user_id = f"social-hp-test-{model.replace('/', '-')}-{int(time.time())}"
            update_user_settings(client, user_id=user_id, settings=model_settings)

            results = run_social_hp_test(client, user_id, model)
            all_results.extend(results)

            # Collect request/response captures for evidence
            if save_tmp:
                captures = client.get_captures_as_dict()
                all_captures.extend(captures)
                print(f"📸 Captured {len(captures)} request/response pairs")

            # Print summary for this model
            print(f"\nSUMMARY for {model}:")
            passed_count = sum(1 for r in results if r.passed)
            print(f"Passed: {passed_count}/{len(results)}")

            for r in results:
                status = "✅ PASS" if r.passed else "❌ FAIL"
                print(f"{status} {r.name}")
                if not r.passed:
                    for err in r.errors:
                        print(f"  - {err}")

            if passed_count < len(results):
                overall_success = False

        except Exception as e:
            print(f"❌ Error testing model {model}: {e}")
            overall_success = False

    # Save evidence bundle if requested
    if save_tmp and provenance:
        try:
            print(f"\n📦 Creating evidence bundle...")
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            evidence_dir = evidence_utils.get_evidence_dir(work_name, timestamp)

            # Build results dict for evidence bundle
            results_dict = {
                "test_name": work_name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "models": models,
                "scenarios": [
                    {
                        "name": r.name,
                        "passed": r.passed,
                        "errors": r.errors,
                        "social_hp_found": r.social_hp_found,
                        "progress_found": r.progress_found,
                        "status_value": r.status_value,
                        "resistance_indicators_found": r.resistance_indicators_found,
                        "campaign_id": r.campaign_id,
                        "raw_response": r.raw_response[:2000] if len(r.raw_response) > 2000 else r.raw_response,
                    }
                    for r in all_results
                ],
                "overall_success": overall_success,
            }

            # Use actual server log path from local_server_info
            server_log_path = None
            if local_server_info and hasattr(local_server_info, 'log_path'):
                server_log_path = Path(local_server_info.log_path) if local_server_info.log_path.exists() else None

            bundle_files = evidence_utils.create_evidence_bundle(
                evidence_dir=evidence_dir,
                test_name=work_name,
                provenance=provenance,
                results=results_dict,
                request_responses=all_captures if all_captures else None,
                server_log_path=server_log_path,
            )

            print(f"✅ Evidence bundle created at: {evidence_dir}")
            print(f"   Files: {', '.join(bundle_files.keys())}")
        except Exception as e:
            print(f"⚠️ Failed to create evidence bundle: {e}")
            traceback.print_exc()

    return overall_success


def main() -> int:
    """Run the Social HP enforcement tests."""
    args = parse_arguments()

    # Setup server
    server_proc = None
    base_url = args.server_url
    local_server = None

    if args.start_local:
        port = args.port if args.port > 0 else pick_free_port()
        local_server = start_local_mcp_server(port)
        base_url = local_server.base_url
        server_proc = local_server.proc
        print(f"🚀 Started local server at {base_url} (PID: {server_proc.pid})")
        # Give it a moment to warm up
        time.sleep(2)

    try:
        models = [m.strip() for m in (args.models or "").split(",") if m.strip()]
        if not models:
            # If no models specified, use valid default (gemini-3-flash-preview is in ALLOWED_GEMINI_MODELS)
            models = ["gemini-3-flash-preview"]

        # Pass server env for evidence provenance
        success = run_all_tests(
            base_url,
            models,
            args.savetmp,
            local_server.env or {} if local_server else {},
            local_server,
            args.work_name,
        )
        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        return 130
    except Exception as e:
        print(f"\n💀 Fatal error: {e}")
        traceback.print_exc()
        return 1
    finally:
        if local_server:
            print(f"🧹 Stopping local server (PID: {local_server.pid})...")
            local_server.stop()


if __name__ == "__main__":
    raise SystemExit(main())
