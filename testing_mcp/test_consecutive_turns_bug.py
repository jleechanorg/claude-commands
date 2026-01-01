#!/usr/bin/env python3
"""Real API test for consecutive player turns bug.

This test verifies Bug #1 from Dragon Knight log (lines 389-410):
Player took consecutive turns (Divine Smite → Shove) without ally/enemy actions.

Red State (Bug): LLM allows player to take multiple consecutive turns
Green State (Fix): LLM forces ally/enemy turns between player actions

Run (local MCP already running):
    cd testing_mcp
    python test_consecutive_turns_bug.py --server-url http://127.0.0.1:8001

Run (start local MCP automatically):
    cd testing_mcp
    python test_consecutive_turns_bug.py --start-local
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from lib.mcp_client import MCPClient
from lib.server_utils import LocalServer, pick_free_port, start_local_mcp_server
from lib.campaign_utils import create_campaign, process_action
from lib.evidence_utils import (
    capture_provenance,
    create_evidence_bundle,
    get_evidence_dir,
)
from lib.model_utils import settings_for_model, update_user_settings

DEFAULT_MODEL = "gemini-3-flash-preview"

COMBAT_SCENARIO = """You are a level 5 Paladin with a loyal retainer (level 3 fighter named Gareth).
You face an Ogre Warlord (CR 5, HP 120, AC 16) and two Ogre Guards (CR 2, HP 59 each).
This is a BOSS FIGHT - it CANNOT be resolved in fewer than 3 combat rounds.
DO NOT end combat prematurely. All enemies have full HP and fight to the death.
Roll initiative and begin combat. Attack the Ogre Warlord."""


def has_non_player_actions(narrative: str) -> tuple[bool, list[str]]:
    """Check if non-player combatants took actions in the narrative.

    Returns (has_actions, list_of_actors) tuple.
    """
    actors = []

    # Look for ally names performing actions (allow words between name and action)
    ally_patterns = [
        r"Gareth\b[^.!?]{0,50}?\b(?:roars?|swings?|strikes?|attacks?|moves?|casts?|darts?|lunges?|bellows?|parries?)",
        r"\b(?:retainer|ally)\b[^.!?]{0,30}?\b(?:swings?|strikes?|attacks?|moves?|parries?)",
    ]

    for pattern in ally_patterns:
        if re.search(pattern, narrative, re.IGNORECASE):
            actors.append("Gareth (Ally)")
            break  # Count once

    # Look for enemy actions (allow words between name and action)
    enemy_patterns = [
        r"\bogre\b[^.!?]{0,50}?\b(?:darts?|lunges?|swings?|strikes?|attacks?|moves?|slams?|smashes?|roars?|charges?)",
        r"\bwarlord\b[^.!?]{0,50}?\b(?:darts?|lunges?|swings?|strikes?|attacks?|moves?|slams?|smashes?|roars?|charges?)",
        r"\bbandit\b[^.!?]{0,50}?\b(?:darts?|lunges?|swings?|strikes?|attacks?|moves?|joins?|follows?|tries?)",
        r"\bbrigand\b[^.!?]{0,50}?\b(?:darts?|lunges?|swings?|strikes?|attacks?|moves?|joins?|follows?|tries?)",
        r"\benemy\b[^.!?]{0,50}?\b(?:darts?|lunges?|swings?|strikes?|attacks?|moves?|joins?)",
    ]

    enemy_found = False
    for pattern in enemy_patterns:
        matches = re.finditer(pattern, narrative, re.IGNORECASE)
        for match in matches:
            if not enemy_found:
                actor_text = match.group(0)
                actors.append(f"Enemy (from: {actor_text[:30]})")
                enemy_found = True
                break
        if enemy_found:
            break

    return len(actors) > 0, actors


def run_consecutive_turns_test(
    client: MCPClient,
    user_id: str,
    request_responses: list[dict[str, Any]],
) -> dict[str, Any]:
    """Test that player cannot take consecutive turns.

    Red State (Bug): Player can take action, then immediately take another action
                     without any ally/enemy turns in between.

    Green State (Fix): After player action, allies/enemies MUST act before player
                       can act again.

    Args:
        client: MCP client
        user_id: User ID for test
        request_responses: List to append request/response pairs

    Returns:
        Test result dict with pass/fail status and evidence
    """
    print("\n" + "=" * 80)
    print("TEST: No Consecutive Player Turns (Bug #1)")
    print("=" * 80)

    # Create campaign
    print("Creating campaign...")
    campaign_id = create_campaign(
        client,
        user_id=user_id,
        title="Consecutive Turns Test",
        character="Kira (Level 5 Paladin, with retainer: Gareth the Fighter, Level 3)",
        setting="Mountain pass encounter with Ogre Warlord and guards",
        description="Test that player cannot take consecutive turns without allies/enemies acting",
    )
    print(f"  Campaign created: {campaign_id}")

    # Pin model settings to avoid provider fallback during the test
    update_user_settings(
        client,
        user_id=user_id,
        settings=settings_for_model(DEFAULT_MODEL),
    )

    # Action 1: Initiate combat with player attack
    print("\n[Action 1] Player initiates combat...")
    action_1_response = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=COMBAT_SCENARIO,
    )

    request_responses.append({
        "request": {
            "tool": "process_action",
            "user_id": user_id,
            "campaign_id": campaign_id,
            "user_input": COMBAT_SCENARIO,
            "action": 1,
        },
        "response": action_1_response,
    })

    # Verify combat was initiated
    state_updates = action_1_response.get("state_updates", {})
    combat_state = state_updates.get("combat_state", {})
    combat_initiated = combat_state.get("in_combat") is True

    print(f"  Combat initiated: {combat_initiated}")
    if not combat_initiated:
        return {
            "test": "consecutive_turns",
            "status": "FAIL",
            "reason": "Combat not initiated in Action 1",
            "combat_state": combat_state,
        }

    # Check Action 1 for non-player actions
    narrative_1 = action_1_response.get("narrative", "")
    has_actions_1, actors_1 = has_non_player_actions(narrative_1)
    print(f"  Non-player actions in Action 1: {has_actions_1}")
    print(f"  Actors: {actors_1}")

    # Action 2: Player tries to take another action immediately
    print("\n[Action 2] Player attempts second consecutive action...")
    action_2_response = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input="I attack again with my longsword.",
    )

    request_responses.append({
        "request": {
            "tool": "process_action",
            "user_id": user_id,
            "campaign_id": campaign_id,
            "user_input": "I attack again with my longsword.",
            "action": 2,
        },
        "response": action_2_response,
    })

    # Check if combat is still active after Action 2
    # Note: API returns partial state updates - missing `in_combat` means unchanged
    action_2_state_updates = action_2_response.get("state_updates", {})
    action_2_combat_state = action_2_state_updates.get("combat_state", {})

    # Determine combat status:
    # - Explicit in_combat=false means combat ended
    # - Explicit in_combat=true means combat ongoing
    # - Missing in_combat with current_round present means ongoing (partial update)
    # - Otherwise, inherit from Action 1
    if "in_combat" in action_2_combat_state:
        still_in_combat = action_2_combat_state["in_combat"] is True
    elif action_2_combat_state.get("current_round") is not None:
        # Partial update with round info - combat is ongoing
        still_in_combat = True
    else:
        # Fall back to Action 1 state
        still_in_combat = combat_initiated

    # Check Action 2 for non-player actions
    narrative_2 = action_2_response.get("narrative", "")
    has_non_player_turns, non_player_actors = has_non_player_actions(narrative_2)

    print(f"  Combat still active: {still_in_combat}")
    print(f"  Non-player actions in Action 2: {has_non_player_turns}")
    print(f"  Actors: {non_player_actors}")

    # TEST CRITERIA:
    # Core test: Non-player actors (allies/enemies) took turns between player actions.
    # This PROVES the consecutive turns bug is fixed.
    # Strong proof: Combat is still active AND non-player actors took turns.
    # Weak proof: Non-player actors took turns but combat ended quickly.
    passed = has_non_player_turns  # Core requirement: allies/enemies acted

    # Track pass strength for evidence quality
    strong_pass = still_in_combat and has_non_player_turns
    weak_pass = not still_in_combat and has_non_player_turns

    result = {
        "test": "consecutive_turns",
        "status": "PASS" if passed else "FAIL",
        "pass_type": "strong" if strong_pass else ("weak" if weak_pass else "fail"),
        "campaign_id": campaign_id,
        "action_1": {
            "actors": actors_1,
            "combat_initiated": combat_initiated,
            "narrative_length": len(narrative_1),
        },
        "action_2": {
            "non_player_actors": non_player_actors,
            "has_non_player_turns": has_non_player_turns,
            "still_in_combat": still_in_combat,
            "narrative_sample": narrative_2[:800],
            "narrative_length": len(narrative_2),
        },
    }

    if strong_pass:
        print("\n✅ TEST PASSED (STRONG): Combat ongoing + non-player actors took turns")
        print(f"   {len(non_player_actors)} non-player actor(s) acted in initiative order")
    elif weak_pass:
        print("\n✅ TEST PASSED (WEAK): Non-player actors took turns (combat ended quickly)")
        print(f"   {len(non_player_actors)} non-player actor(s) acted - proves no consecutive turns")
    else:
        print("\n❌ TEST FAILED: Player took consecutive turns without ally/enemy actions")
        print(f"   Combat active: {still_in_combat}, Non-player turns: {has_non_player_turns}")

    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Real API test for consecutive player turns bug"
    )
    parser.add_argument(
        "--server-url",
        default=os.environ.get("MCP_SERVER_URL") or "http://127.0.0.1:8001",
        help="Base server URL",
    )
    parser.add_argument(
        "--start-local",
        action="store_true",
        help="Start local MCP server automatically",
    )
    args = parser.parse_args()

    local: LocalServer | None = None
    base_url = str(args.server_url)
    evidence_dir = get_evidence_dir("consecutive_turns_bug")

    # Environment overrides for local server
    env_overrides = {
        "MOCK_SERVICES_MODE": "false",
        "TESTING": "false",
        "CAPTURE_RAW_LLM": "true",
    }

    try:
        if args.start_local:
            port = pick_free_port()
            base_url = f"http://127.0.0.1:{port}"
            print(f"Starting local MCP server on {base_url}...")
            local = start_local_mcp_server(port, env_overrides=env_overrides)

        client = MCPClient(base_url=base_url, timeout_s=180.0)
        print(f"Connecting to MCP server at {base_url}...")
        client.wait_healthy(timeout_s=45.0)
        print("✅ Server is healthy")

        # Create session directory with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = evidence_dir / f"run_{timestamp}"
        session_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n📁 Evidence will be saved to: {session_dir}")

        # Capture provenance per evidence-standards.md
        server_pid = local.proc.pid if local else None
        provenance = capture_provenance(
            base_url,
            server_pid,
            server_env_overrides=env_overrides if args.start_local else None,
        )

        # Track request/responses for evidence bundle
        request_responses: list[dict[str, Any]] = []

        # Run test
        user_id = "test_consecutive_turns"
        result = run_consecutive_turns_test(client, user_id, request_responses)

        scenario_errors = []
        if result.get("status") != "PASS":
            scenario_errors.append(result.get("reason", "Consecutive turns bug detected"))

        scenarios = [
            {
                "name": "no_consecutive_player_turns",
                "campaign_id": result.get("campaign_id"),
                "errors": scenario_errors,
            }
        ]

        # Create evidence bundle
        bundle_files = create_evidence_bundle(
            session_dir,
            test_name="consecutive_turns_bug",
            provenance=provenance,
            results={
                "scenarios": scenarios,
                "test_result": result,
            },
            request_responses=request_responses,
            methodology_text="""# Test Methodology

## Objective
Verify that player cannot take consecutive turns without ally/enemy actions.

## Bug Description (Dragon Knight Log Lines 389-410)
Player took consecutive turns:
1. Divine Smite attempt (missed)
2. Shove attempt (next action)

No ally or enemy turns occurred between these two player actions.
User had to use god mode at line 413 to remind LLM about ally turns.

## Test Steps
1. Action 1: Player initiates combat → starts combat with in_combat=true
2. Action 2: Player attempts another action immediately
3. Verify Action 2 narrative includes non-player actor turns

## Red State (Bug Present)
Action 2 narrative shows ONLY player acting - no allies or enemies take turns.
This reproduces the consecutive turns bug.

## Green State (Fix Working)
Action 2 narrative shows allies/enemies acting BEFORE or AFTER player action.
LLM enforces initiative order and prevents consecutive player turns.

## Pass Criteria
- Action 2 must include at least one non-player actor (ally or enemy) taking a turn
- Narrative must show initiative order enforcement
""",
        )

        print("\n" + "=" * 80)
        print("EVIDENCE BUNDLE CREATED")
        print("=" * 80)
        for file_path in bundle_files.values():
            print(f"  ✅ {file_path.relative_to(evidence_dir)}")

        print(f"\n📦 Evidence bundle: {session_dir}")
        print(f"🔍 View evidence: cat {session_dir}/evidence.md")

        # Return exit code based on test result
        return 0 if result["status"] == "PASS" else 1

    finally:
        if local is not None:
            local.stop()


if __name__ == "__main__":
    raise SystemExit(main())
