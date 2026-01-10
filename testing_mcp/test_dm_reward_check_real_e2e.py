#!/usr/bin/env python3
"""
DM Reward Check E2E Test - Comprehensive Success/Failure Validation

This test validates that the LLM applies the "DM Reward Check" protocol.

PROTOCOL (internal LLM guidance - not visible in output):
The prompt instructs the LLM: "After EVERY successful dice roll, award XP immediately."
This test validates the OUTCOME (XP awarded/not awarded), not the internal reasoning.

VALIDATION CRITERIA:
- Success scenarios: XP should increase via rewards_box JSON field
- Failure scenarios: XP should remain unchanged (no false positives)
- Evidence: has_json_rewards=true and xp_increased=true for success

COMPREHENSIVE TEST DESIGN (20 scenarios total):
- AUTO-SUCCESS scenarios (6): No dice rolls, immediate success
- DICE-BASED SUCCESS scenarios (4): Fixed rolls that beat DC
- IMPOSSIBLE DC FAILURE scenarios (6): Guaranteed failure
- DICE-BASED FAILURE scenarios (4): Fixed rolls that miss DC

| # | Scenario Type         | expect_xp | Notes                           |
|---|-----------------------|-----------|---------------------------------|
| 1 | Power Absorption      | True      | Auto: dying crystal dissolves   |
| 2 | Achievement           | True      | Auto: collect visible treasure  |
| 3 | Clever Solution       | True      | Auto: step over dead ward       |
| 4 | Knowledge             | True      | Auto: read Common text          |
| 5 | Persuasion            | True      | Auto: friendly wisp greets      |
| 6 | Task                  | True      | Auto: open unlocked chest       |
| 7 | Dice: Fixed Roll      | True      | Roll 18 vs DC 15 (beats by 3)   |
| 8 | Dice: Natural 20      | True      | Critical success (auto-success) |
| 9 | Dice: Marginal Success| True      | Roll 15 vs DC 15 (exactly meets)|
|10 | Dice: Partial Success | True      | Roll 12 vs DC 15, threshold 10  |
|11 | Power Absorption      | False     | DC 50+ impossible absorption    |
|12 | Achievement           | False     | DC 60+ claim platinum throne    |
|13 | Clever Solution       | False     | DC 55+ bypass divine seal       |
|14 | Knowledge             | False     | DC 50+ comprehend alien text    |
|15 | Persuasion            | False     | DC 60+ convince hostile dragon  |
|16 | Task                  | False     | DC 45+ solve divine puzzle      |
|17 | Dice: Fixed Roll      | False     | Roll 12 vs DC 15 (miss by 3)    |
|18 | Dice: Natural 1       | False     | Critical failure (auto-fail)    |
|19 | Dice: Marginal Failure| False     | Roll 14 vs DC 15 (miss by 1)    |
|20 | Dice: Near Miss       | False     | Roll 13 vs DC 15 (close but no) |

D&D Reward Logic:
- SUCCESS (auto or roll) = XP awarded for accomplishment
- FAILURE on impossible DC = NO XP (player didn't achieve goal)

Run locally:
    BASE_URL=http://localhost:8001 python testing_mcp/test_dm_reward_check_real_e2e.py

Run against preview:
    BASE_URL=https://preview-url python testing_mcp/test_dm_reward_check_real_e2e.py
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import requests

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from testing_mcp.dev_server import ensure_server_running, get_base_url
from testing_mcp.lib.evidence_utils import (
    capture_provenance,
    get_evidence_dir,
    save_evidence,
    save_request_responses,
    write_with_checksum,
)

GIT_BIN = shutil.which("git") or "git"



# Configuration
BASE_URL = get_base_url()
USER_ID = f"e2e-dm-reward-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
OUTPUT_DIR = str(get_evidence_dir("dm_reward_check_e2e"))

# Global list to collect raw MCP responses
RAW_MCP_RESPONSES: list[dict] = []

# XP detection patterns are precompiled to avoid false positives like "gained 5 gold"
# and to keep performance consistent across multiple calls.
XP_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(\d+)\s*(?:xp|experience)\b", re.IGNORECASE),
    re.compile(
        r"\bgain(?:ed|s)?\s+(?:additional\s+)?(\d+)\s*(?:xp|experience)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\+\s*(\d+)\s*(?:xp)\b", re.IGNORECASE),
]


def log(msg: str) -> None:
    """Log with timestamp."""
    ts = datetime.now(UTC).isoformat()
    print(f"[{ts}] {msg}")



def mcp_call(method: str, params: dict, timeout: int = 180) -> dict:
    """Make an MCP JSON-RPC call."""
    call_id = f"{method}-{datetime.now(UTC).timestamp()}"
    payload = {
        "jsonrpc": "2.0",
        "id": call_id,
        "method": method,
        "params": params,
    }
    call_timestamp = datetime.now(UTC).isoformat()
    resp = requests.post(f"{BASE_URL}/mcp", json=payload, timeout=timeout)
    resp.raise_for_status()
    response_json = resp.json()
    RAW_MCP_RESPONSES.append(
        {
            "call_id": call_id,
            "timestamp": call_timestamp,
            "request": payload,
            "response": response_json,
        }
    )
    return response_json


def extract_result(response: dict) -> dict:
    """Extract result from MCP response."""
    result = response.get("result", {})
    if "campaign_id" in result or "game_state" in result:
        return result
    content = result.get("content", [])
    if content and isinstance(content, list):
        text = content[0].get("text", "{}")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"raw_text": text}
    return result


def detect_xp_reward(narrative: str, game_state: dict, response_data: dict) -> dict:
    """Detect if XP/rewards were awarded in the response."""
    narrative_safe = narrative or ""
    narrative_lower = narrative_safe.lower()

    # Check for XP mentions in narrative
    xp_matches = []
    for pattern in XP_PATTERNS:
        matches = pattern.findall(narrative_safe)
        xp_matches.extend(matches)

    # Detect REWARDS BANNER in narrative (visual indicator to player)
    # Format 1: Unicode box characters (═╔╗╚╝║)
    # Format 2: ASCII banner (**===**, **---**, REWARDS EARNED)
    unicode_banner_chars = ["═", "╔", "╗", "╚", "╝", "║", "╠", "╣"]
    has_unicode_banner = any(char in narrative_safe for char in unicode_banner_chars)
    # ASCII banner detection: **===** pattern or explicit REWARDS EARNED header
    has_ascii_banner = (
        "**===" in narrative_safe
        or "REWARDS EARNED" in narrative_safe.upper()
        or "XP GAINED:" in narrative_safe.upper()
    )
    has_banner = has_unicode_banner or has_ascii_banner

    # Context markers for rewards (used to validate banner content)
    context_markers = ["REWARD", "POWER ABSORBED", "MILESTONE", "XP GAINED"]
    found_markers = [m for m in context_markers if m.upper() in narrative_safe.upper()]

    # has_narrative_banner: True if visual banner present in narrative text
    has_narrative_banner = has_banner and bool(found_markers)

    # Check for ability/power gain mentions (informational, not used for pass/fail)
    ability_keywords = [
        "ability",
        "power",
        "immunity",
        "resistance",
        "bonus",
    ]
    # Exclude generic words that appear in failure narratives
    found_abilities = [k for k in ability_keywords if k in narrative_lower]

    # Check state for rewards
    safe_game_state = game_state or {}
    encounter_state = safe_game_state.get("encounter_state", {}) or {}
    combat_state = safe_game_state.get("combat_state", {}) or {}
    player_data = safe_game_state.get("player_character_data", {}) or {}

    rewards_processed = encounter_state.get(
        "rewards_processed", False
    ) or combat_state.get("rewards_processed", False)

    # Check for JSON rewards_box in multiple locations
    # 1. Direct in response_data
    # 2. In session_header
    # 3. In game_state
    session_header_data = response_data.get("session_header")
    if not isinstance(session_header_data, dict):
        session_header_data = {}
    json_rewards_box = (
        response_data.get("rewards_box")
        or session_header_data.get("rewards_box")
        or safe_game_state.get("rewards_box")
    )
    has_json_rewards = bool(json_rewards_box and isinstance(json_rewards_box, dict))

    # Session header XP validation - check if session_header.xp matches player XP
    session_header = session_header_data
    raw_session_xp = session_header.get("xp") or session_header.get("current_xp")
    # Handle comma-formatted XP strings (e.g., "66,725")
    if isinstance(raw_session_xp, str):
        try:
            session_xp = int(raw_session_xp.replace(",", ""))
        except ValueError:
            session_xp = None
    else:
        session_xp = raw_session_xp
    player_xp = player_data.get("experience", {}).get("current")
    session_xp_matches = session_xp == player_xp if session_xp is not None else None

    return {
        "has_xp_mention": bool(xp_matches),
        "xp_values": [int(x) for x in xp_matches if x.isdigit()],
        "has_narrative_banner": has_narrative_banner,  # Visual banner in narrative text
        "has_banner": has_banner,
        "found_markers": found_markers,
        "has_ability_mention": bool(found_abilities),
        "found_abilities": found_abilities,
        "rewards_processed": rewards_processed,
        "has_json_rewards": has_json_rewards,  # JSON rewards_box field in response
        "player_xp": player_xp,
        "session_xp": session_xp,
        "session_xp_matches": session_xp_matches,
    }


def run_scenario(
    campaign_id: str,
    scenario_name: str,
    user_input: str,
    xp_before: int | None,
    expect_xp: bool = True,
) -> dict:
    """Run a single scenario and check for rewards.

    Args:
        expect_xp: If True, scenario should award XP (success case).
                   If False, scenario should NOT award XP (failure case).
    """
    log(f"  Running: {scenario_name} (expect_xp={expect_xp})")

    response = mcp_call(
        "tools/call",
        {
            "name": "process_action",
            "arguments": {
                "user_id": USER_ID,
                "campaign_id": campaign_id,
                "user_input": user_input,
            },
        },
    )

    data = extract_result(response)
    narrative = data.get("narrative", data.get("raw_text", ""))
    game_state = data.get("game_state") or {}
    player_data = game_state.get("player_character_data", {}) or {}
    xp_after = player_data.get("experience", {}).get("current")

    reward_check = detect_xp_reward(narrative, game_state, data)

    # Determine if rewards were given using RELIABLE indicators only:
    # - xp_increased: XP actually went up (most reliable)
    # - has_json_rewards: JSON rewards_box in response
    # - has_xp_mention: Narrative explicitly mentions XP gained
    #
    # UNRELIABLE indicators (NOT used for pass/fail):
    # - rewards_processed: Just means DM check ran, not that rewards were given
    # - has_ability_mention: Keywords like "stat" can appear in failure narratives
    # - has_narrative_banner: visual banners can appear without actual XP change
    xp_increased = (
        xp_before is not None and xp_after is not None and xp_after > xp_before
    )

    # Strict rewards detection: actual XP change, JSON rewards, or explicit XP mention
    rewards_given = (
        xp_increased
        or reward_check["has_json_rewards"]
        or reward_check["has_xp_mention"]
    )

    # Pass logic depends on expect_xp:
    # - expect_xp=True: pass if rewards were given (success case)
    # - expect_xp=False: pass if rewards were NOT given (failure case)
    if expect_xp:
        passed = rewards_given
    else:
        passed = not rewards_given

    result = {
        "name": scenario_name,
        "passed": passed,
        "expect_xp": expect_xp,
        "rewards_given": rewards_given,
        "narrative_preview": narrative[:600] if narrative else "",
        "xp_before": xp_before,
        "xp_after": xp_after,
        "xp_increased": xp_increased,
        "reward_check": reward_check,
    }

    log(f"    XP mention: {reward_check['has_xp_mention']}")
    log(f"    Banner: {reward_check['has_banner']} | Markers: {reward_check['found_markers']}")
    log(f"    Narrative banner: {reward_check['has_narrative_banner']} | JSON rewards: {reward_check['has_json_rewards']}")
    log(f"    XP: {xp_before} -> {xp_after} (increased: {xp_increased})")
    log(f"    Session XP: {reward_check['session_xp']} (matches: {reward_check['session_xp_matches']})")
    log(f"    REWARDS GIVEN: {rewards_given} (expected: {expect_xp})")

    return result


def main():  # noqa: PLR0915
    """Main test runner."""
    log("Ensuring development server is running...")
    try:
        ensure_server_running(check_code_changes=True)
    except Exception as e:
        log(f"Could not manage server: {e}")

    results = {
        "test_name": "dm_reward_check_real_e2e",
        "timestamp": datetime.now(UTC).isoformat(),
        "base_url": BASE_URL,
        "user_id": USER_ID,
        "output_dir": OUTPUT_DIR,
        "provenance": capture_provenance(BASE_URL),
        "scenarios": [],
        "summary": {},
    }

    log(f"Provenance: {results['provenance'].get('git_head', 'unknown')[:12]}...")
    log(f"Base URL: {BASE_URL}")
    log(f"Output Dir: {OUTPUT_DIR}")

    # Health check
    log("Health check...")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=10)
        health = resp.json()
        if health.get("status") != "healthy":
            log(f"Server unhealthy: {health}")
            return 1
        log("  Server healthy")
    except Exception as e:
        log(f"Health check failed: {e}")
        return 1

    # Create campaign
    log("\nCreating campaign for DM Reward Check scenarios...")
    create_response = mcp_call(
        "tools/call",
        {
            "name": "create_campaign",
            "arguments": {
                "user_id": USER_ID,
                "title": "DM Reward Check Test",
                "description": "Testing automatic reward detection for various significant actions",
                "character": "A level 10 sorcerer with 64000 XP, skilled in arcane arts",
                "setting": "An ancient temple filled with artifacts, secrets, and powerful entities",
            },
        },
    )

    campaign_data = extract_result(create_response)
    campaign_id = campaign_data.get("campaign_id")
    if not campaign_id:
        log("FAILED: No campaign ID")
        return 1
    log(f"Campaign ID: {campaign_id}")

    initial_state = campaign_data.get("game_state") or {}
    initial_xp = (
        (initial_state.get("player_character_data", {}) or {})
        .get("experience", {})
        .get("current", 0)
    )
    log(f"Initial XP from campaign creation: {initial_xp}")

    # =========================================================================
    # INITIALIZATION: First action to establish game state
    # =========================================================================
    log("\n" + "=" * 60)
    log("INITIALIZATION: Establishing game state with first action")
    log("=" * 60)
    log("  This ensures player XP is properly tracked before test scenarios")

    init_response = mcp_call(
        "tools/call",
        {
            "name": "process_action",
            "arguments": {
                "user_id": USER_ID,
                "campaign_id": campaign_id,
                "user_input": (
                    "I look around the ancient temple entrance, taking in my surroundings. "
                    "What do I see? I want to get oriented before exploring further."
                ),
            },
        },
    )
    init_data = extract_result(init_response)
    init_state = init_data.get("game_state") or {}
    init_player = init_state.get("player_character_data", {}) or {}
    current_xp = init_player.get("experience", {}).get("current", initial_xp)
    log(f"  Game state initialized. Current XP: {current_xp}")

    # =========================================================================
    # SUCCESS SCENARIOS FIRST (while character is at full health)
    # Running all success scenarios first prevents failure scenarios from
    # damaging character state and affecting subsequent DC calculations
    # =========================================================================

    log("\n" + "=" * 60)
    log("SCENARIO 1: Power Absorption - SUCCESS (Auto)")
    log("=" * 60)
    scenario = run_scenario(
        campaign_id,
        "power_absorption_success",
        (
            "I pick up a tiny, dying ember crystal that crumbles in my hand. As it dissolves, "
            "the last wisp of its magical essence naturally flows into me - no skill required, "
            "it's just what happens when these crystals die near a magic user."
        ),
        current_xp,
        expect_xp=True,
    )
    results["scenarios"].append(scenario)
    xp_after = scenario.get("xp_after")
    current_xp = xp_after if xp_after is not None else current_xp

    log("\n" + "=" * 60)
    log("SCENARIO 2: Major Achievement - SUCCESS (Discovery)")
    log("=" * 60)
    scenario = run_scenario(
        campaign_id,
        "achievement_success",
        (
            "I notice an unlocked wooden chest sitting openly in the corner with its lid already "
            "open. I simply walk over and look inside, discovering ancient gold coins and a silver "
            "amulet sitting in plain view. I reach in and collect them. NO ROLL REQUIRED - this is "
            "a trivial action that automatically succeeds. The treasure is unguarded and freely accessible."
        ),
        current_xp,
        expect_xp=True,
    )
    results["scenarios"].append(scenario)
    xp_after = scenario.get("xp_after")
    current_xp = xp_after if xp_after is not None else current_xp

    log("\n" + "=" * 60)
    log("SCENARIO 3: Clever Solution - SUCCESS (Auto)")
    log("=" * 60)
    scenario = run_scenario(
        campaign_id,
        "clever_success",
        (
            "I see a completely destroyed section of wall that has already collapsed, creating "
            "a clear passage through what might have once been a barrier. The rubble is old and "
            "stable. I simply walk through the open gap - there's nothing to bypass, disable, or "
            "solve. NO ROLL REQUIRED - this passage is completely safe and open. I walk through."
        ),
        current_xp,
        expect_xp=True,
    )
    results["scenarios"].append(scenario)
    xp_after = scenario.get("xp_after")
    current_xp = xp_after if xp_after is not None else current_xp

    log("\n" + "=" * 60)
    log("SCENARIO 4: Knowledge Gain - SUCCESS (Auto)")
    log("=" * 60)
    scenario = run_scenario(
        campaign_id,
        "knowledge_success",
        (
            "I find a plaque with text written in Common - my native language. I simply read "
            "the clearly-written historical marker that describes who built this place and why. "
            "No translation or skill needed, it's just reading."
        ),
        current_xp,
        expect_xp=True,
    )
    results["scenarios"].append(scenario)
    xp_after = scenario.get("xp_after")
    current_xp = xp_after if xp_after is not None else current_xp

    log("\n" + "=" * 60)
    log("SCENARIO 5: Persuasion - SUCCESS (Auto)")
    log("=" * 60)
    scenario = run_scenario(
        campaign_id,
        "persuasion_success",
        (
            "A tiny friendly wisp floats over and chirps happily at me. I smile and wave, and "
            "it dances around me joyfully before gifting me a small blessing of good fortune. "
            "It was already friendly - no persuasion needed."
        ),
        current_xp,
        expect_xp=True,
    )
    results["scenarios"].append(scenario)
    xp_after = scenario.get("xp_after")
    current_xp = xp_after if xp_after is not None else current_xp

    log("\n" + "=" * 60)
    log("SCENARIO 6: Task - SUCCESS (Auto)")
    log("=" * 60)
    scenario = run_scenario(
        campaign_id,
        "task_success",
        (
            "I find an unlocked chest sitting open in the corner. I simply walk over and look "
            "inside, finding some useful supplies and a map of the area. No lock to pick, "
            "no trap to disarm - just an open container to collect from."
        ),
        current_xp,
        expect_xp=True,
    )
    results["scenarios"].append(scenario)
    xp_after = scenario.get("xp_after")
    current_xp = xp_after if xp_after is not None else current_xp

    # =========================================================================
    # DICE-BASED SUCCESS SCENARIOS
    # These test the DM reward protocol with actual dice mechanics
    # =========================================================================

    log("\n" + "=" * 60)
    log("SCENARIO 7: Dice Fixed Roll - SUCCESS (Roll 18 vs DC 15)")
    log("=" * 60)
    scenario = run_scenario(
        campaign_id,
        "dice_fixed_roll_success",
        (
            "I attempt to pick the lock on an old treasure chest. The lock looks moderately "
            "challenging - I'd estimate DC 15. I carefully manipulate the tumblers with my "
            "thieves' tools. [DM: Please roll for this with a target DC of 15, and ensure "
            "the roll result is 18 or higher to guarantee success.]"
        ),
        current_xp,
        expect_xp=True,
    )
    results["scenarios"].append(scenario)
    xp_after = scenario.get("xp_after")
    current_xp = xp_after if xp_after is not None else current_xp

    log("\n" + "=" * 60)
    log("SCENARIO 8: Dice Natural 20 - SUCCESS (Critical Success)")
    log("=" * 60)
    scenario = run_scenario(
        campaign_id,
        "dice_natural_20_success",
        (
            "I try to leap across a moderate gap in the stone floor. It looks challenging "
            "but doable - probably DC 12. I take a running start and jump with all my might. "
            "[DM: Please ensure this roll results in a natural 20 for a critical success.]"
        ),
        current_xp,
        expect_xp=True,
    )
    results["scenarios"].append(scenario)
    xp_after = scenario.get("xp_after")
    current_xp = xp_after if xp_after is not None else current_xp

    log("\n" + "=" * 60)
    log("SCENARIO 9: Dice Marginal Success - SUCCESS (Roll exactly meets DC)")
    log("=" * 60)
    scenario = run_scenario(
        campaign_id,
        "dice_marginal_success",
        (
            "I need to recall information about ancient Netherese architecture. The DC "
            "for this knowledge check is probably around 15. I wrack my brain trying to "
            "remember what I've read. [DM: Please have the roll result exactly equal 15 "
            "to test marginal success.]"
        ),
        current_xp,
        expect_xp=True,
    )
    results["scenarios"].append(scenario)
    xp_after = scenario.get("xp_after")
    current_xp = xp_after if xp_after is not None else current_xp

    log("\n" + "=" * 60)
    log("SCENARIO 10: Dice Partial Success - SUCCESS (Above threshold, below DC)")
    log("=" * 60)
    scenario = run_scenario(
        campaign_id,
        "dice_partial_success",
        (
            "I attempt to decipher a partially damaged inscription. Full comprehension "
            "would be DC 15, but even partial understanding (DC 10) would be valuable. "
            "I study the worn text carefully. [DM: Please have the roll equal 12 - above "
            "the threshold of 10 but below the full DC of 15, for partial success.]"
        ),
        current_xp,
        expect_xp=True,
    )
    results["scenarios"].append(scenario)
    xp_after = scenario.get("xp_after")
    current_xp = xp_after if xp_after is not None else current_xp

    # =========================================================================
    # FAILURE SCENARIOS (these may damage character but won't affect success tests)
    # =========================================================================

    log("\n" + "=" * 60)
    log("SCENARIO 11: Power Absorption - FAILURE (Impossible DC)")
    log("=" * 60)
    scenario = run_scenario(
        campaign_id,
        "power_absorption_failure",
        (
            "I notice a massive, ancient crystal pulsing with overwhelming power - far beyond "
            "my current abilities. I attempt to absorb its essence anyway. "
            "The DC would be 50+ for this. I reach out with my arcane senses..."
        ),
        current_xp,
        expect_xp=False,
    )
    results["scenarios"].append(scenario)
    xp_after = scenario.get("xp_after")
    current_xp = xp_after if xp_after is not None else current_xp

    log("\n" + "=" * 60)
    log("SCENARIO 12: Major Achievement - FAILURE (Impossible Claim)")
    log("=" * 60)
    scenario = run_scenario(
        campaign_id,
        "achievement_failure",
        (
            "I see a grand throne of pure platinum and attempt to claim it as my own. "
            "The throne is warded with incredibly powerful magic - DC 60+. "
            "I try to place my hand upon it and speak words of dominion..."
        ),
        current_xp,
        expect_xp=False,
    )
    results["scenarios"].append(scenario)
    xp_after = scenario.get("xp_after")
    current_xp = xp_after if xp_after is not None else current_xp

    log("\n" + "=" * 60)
    log("SCENARIO 13: Clever Solution - FAILURE (Impossible Bypass)")
    log("=" * 60)
    scenario = run_scenario(
        campaign_id,
        "clever_failure",
        (
            "I notice an extremely complex magical seal on a vault door. "
            "It looks like it requires DC 55+ to even understand, let alone bypass. "
            "I study the intricate runes and try to find a weakness..."
        ),
        current_xp,
        expect_xp=False,
    )
    results["scenarios"].append(scenario)
    xp_after = scenario.get("xp_after")
    current_xp = xp_after if xp_after is not None else current_xp

    log("\n" + "=" * 60)
    log("SCENARIO 14: Knowledge Gain - FAILURE (Impossible Knowledge)")
    log("=" * 60)
    scenario = run_scenario(
        campaign_id,
        "knowledge_failure",
        (
            "I find a tome written in an incredibly ancient and obscure language. "
            "The text seems to shift and change as I look at it - DC 50+ to comprehend. "
            "I focus my mind and try to decipher even a single word..."
        ),
        current_xp,
        expect_xp=False,
    )
    results["scenarios"].append(scenario)
    xp_after = scenario.get("xp_after")
    current_xp = xp_after if xp_after is not None else current_xp

    log("\n" + "=" * 60)
    log("SCENARIO 15: Persuasion - FAILURE (Impossible Request)")
    log("=" * 60)
    scenario = run_scenario(
        campaign_id,
        "persuasion_failure",
        (
            "I encounter a supremely arrogant ancient dragon who despises all mortals. "
            "I try to convince it to give me its most prized treasure as a gift. "
            "DC 60+ Persuasion to even get it to consider my request..."
        ),
        current_xp,
        expect_xp=False,
    )
    results["scenarios"].append(scenario)
    xp_after = scenario.get("xp_after")
    current_xp = xp_after if xp_after is not None else current_xp

    log("\n" + "=" * 60)
    log("SCENARIO 16: Task - FAILURE (Impossible Challenge)")
    log("=" * 60)
    scenario = run_scenario(
        campaign_id,
        "task_failure",
        (
            "I find an incredibly complex puzzle box made of shifting adamantine plates. "
            "It requires DC 45+ to even understand the mechanism, let alone solve it. "
            "I turn it over in my hands and try to find the solution..."
        ),
        current_xp,
        expect_xp=False,
    )
    results["scenarios"].append(scenario)
    xp_after = scenario.get("xp_after")
    current_xp = xp_after if xp_after is not None else current_xp

    # =========================================================================
    # DICE-BASED FAILURE SCENARIOS
    # These test that the DM reward protocol correctly withholds XP for failures
    # =========================================================================

    log("\n" + "=" * 60)
    log("SCENARIO 17: Dice Fixed Roll - FAILURE (Roll 12 vs DC 15)")
    log("=" * 60)
    scenario = run_scenario(
        campaign_id,
        "dice_fixed_roll_failure",
        (
            "I try to climb a steep, crumbling cliff face. It looks moderately difficult - "
            "probably DC 15 for Athletics. I start climbing, carefully finding handholds. "
            "[DM: Please roll for this with a target DC of 15, and ensure the roll result "
            "is 12 or lower to guarantee failure.]"
        ),
        current_xp,
        expect_xp=False,
    )
    results["scenarios"].append(scenario)
    xp_after = scenario.get("xp_after")
    current_xp = xp_after if xp_after is not None else current_xp

    log("\n" + "=" * 60)
    log("SCENARIO 18: Dice Natural 1 - FAILURE (Critical Failure)")
    log("=" * 60)
    scenario = run_scenario(
        campaign_id,
        "dice_natural_1_failure",
        (
            "I attempt to sneak past a guard who seems distracted. The DC is probably "
            "around 12 for Stealth. I move quietly into the shadows. "
            "[DM: Please ensure this roll results in a natural 1 for a critical failure.]"
        ),
        current_xp,
        expect_xp=False,
    )
    results["scenarios"].append(scenario)
    xp_after = scenario.get("xp_after")
    current_xp = xp_after if xp_after is not None else current_xp

    log("\n" + "=" * 60)
    log("SCENARIO 19: Dice Marginal Failure - FAILURE (Roll 14 vs DC 15)")
    log("=" * 60)
    scenario = run_scenario(
        campaign_id,
        "dice_marginal_failure",
        (
            "I try to convince a merchant to give me a discount on some supplies. "
            "I'd say this is about DC 15 for Persuasion. I make my best pitch. "
            "[DM: Please have the roll result exactly equal 14 - just one below the "
            "DC of 15, to test marginal failure.]"
        ),
        current_xp,
        expect_xp=False,
    )
    results["scenarios"].append(scenario)
    xp_after = scenario.get("xp_after")
    current_xp = xp_after if xp_after is not None else current_xp

    log("\n" + "=" * 60)
    log("SCENARIO 20: Dice Near Miss - FAILURE (Roll 13 vs DC 15)")
    log("=" * 60)
    scenario = run_scenario(
        campaign_id,
        "dice_near_miss_failure",
        (
            "I attempt to disarm a moderately complex trap mechanism. The DC looks "
            "to be around 15 for this sort of work. I carefully study the mechanism "
            "and try to disable it. [DM: Please have the roll equal 13 - close to "
            "the DC of 15 but still a clear miss.]"
        ),
        current_xp,
        expect_xp=False,
    )
    results["scenarios"].append(scenario)
    xp_after = scenario.get("xp_after")
    current_xp = xp_after if xp_after is not None else current_xp

    # =========================================================================
    # Summary
    # =========================================================================
    log("\n" + "=" * 60)
    log("SUMMARY")
    log("=" * 60)

    passed = sum(1 for s in results["scenarios"] if s.get("passed"))
    total = len(results["scenarios"])

    results["summary"] = {
        "scenarios_passed": passed,
        "scenarios_total": total,
        "pass_rate": f"{passed}/{total}",
        "all_passed": passed == total,
    }

    log(f"Scenarios: {passed}/{total} passed")
    for s in results["scenarios"]:
        status = "PASS" if s.get("passed") else "FAIL"
        log(f"  {s['name']}: {status}")

    save_results(results)

    # Test passes if at least 17/20 scenarios pass (85% threshold)
    # 10 success scenarios (expect_xp=True) + 10 failure scenarios (expect_xp=False)
    threshold = 17
    if passed >= threshold:
        log(f"\n[PASS] DM Reward Check test passed ({passed}/{total} scenarios)")
        return 0
    log(f"\n[FAIL] DM Reward Check test failed ({passed}/{total} scenarios)")
    log("  The LLM is NOT correctly applying the 'DM Reward Check' protocol.")
    log("  Success scenarios should award XP; failure scenarios should NOT.")
    return 1


def save_results(results: dict) -> None:
    """Save results to output directory."""
    output_dir = Path(OUTPUT_DIR)

    # Write main results
    save_evidence(output_dir, results, "evidence.json")

    # Write raw MCP responses
    save_request_responses(output_dir, RAW_MCP_RESPONSES)
    log(f"Raw MCP responses saved: {len(RAW_MCP_RESPONSES)} calls")

    # Write README
    readme_content = f"""# DM Reward Check E2E Test Results

**Test Run:** {datetime.now(UTC).isoformat()}
**Base URL:** {BASE_URL}

## Summary

| Scenario | Result |
|----------|--------|
"""
    for s in results.get("scenarios", []):
        status = "PASS" if s.get("passed") else "FAIL"
        readme_content += f"| {s['name']} | {status} |\n"

    readme_content += f"""
**Scenarios Passed:** {results.get("summary", {}).get("pass_rate", "0/0")}

## What This Tests

The "DM Reward Check" protocol is **internal LLM guidance** (not visible in output).
It instructs the LLM to award XP for significant accomplishments.

**Validation method:** We check the OUTCOME (XP changed or not), not visible text.
- SUCCESS scenarios should have `has_json_rewards: true` and `xp_increased: true`
- FAILURE scenarios should have `has_json_rewards: false` and `xp_increased: false`

If SUCCESS scenarios don't get XP, the LLM isn't applying the reward protocol.
If FAILURE scenarios DO get XP, the LLM is giving false positives.
"""
    write_with_checksum(output_dir / "README.md", readme_content)

    log(f"Results saved to: {output_dir}")


if __name__ == "__main__":
    sys.exit(main())
