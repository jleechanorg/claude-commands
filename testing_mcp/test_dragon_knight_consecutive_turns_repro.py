#!/usr/bin/env python3
"""
Reproduce Dragon Knight consecutive turns bug using exact scenario from production.

This test reproduces Bug #1 from Dragon Knight campaign (wBoMKQuMnvLfyjTFTBHd):
- Entry #58: Player Divine Smite
- Entry #59: LLM response (NO ally/enemy turns)
- Entry #60: Player Shove (CONSECUTIVE TURN - BUG!)
- Entry #62: User complaint "make sure my team is also taking combat turns automatically"

Evidence: docs/combat_turns_dragon_knight_bug.json

Run (local MCP already running):
    cd testing_mcp
    python test_dragon_knight_consecutive_turns_repro.py --server-url http://127.0.0.1:8001

Run (start local MCP automatically):
    cd testing_mcp
    python test_dragon_knight_consecutive_turns_repro.py --start-local
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

DEFAULT_MODEL = "gemini-3-flash-preview"

# Exact scenario from Dragon Knight campaign entries 56-60
DRAGON_KNIGHT_SETUP = """You are Ser Arion, a 16-year-old knight of the Geffen Empire.

You burst into a solar (fancy room) after kicking open the doors.
You are facing:
- Shadow-born (a creature of darkness, flickering form)
- Malakor agent (sneering human with dueling blade)

You have two retainers (level 1 fighters) with you who should act automatically in combat.

The doors just exploded inward and you've entered combat."""


def has_non_player_actions(narrative: str) -> tuple[bool, list[str]]:
    """Check if non-player combatants took actions in the narrative.

    Returns (has_actions, list_of_actors) tuple.
    """
    actors = []

    # Look for retainer/ally actions (allow words between name and action)
    ally_patterns = [
        r"\bretainer\b[^.!?]{0,50}?\b(?:roars?|swings?|strikes?|attacks?|moves?|casts?|darts?|lunges?|bellows?|parries?)",
        r"\bally\b[^.!?]{0,50}?\b(?:swings?|strikes?|attacks?|moves?|parries?)",
        r"\bfighter\b[^.!?]{0,50}?\b(?:swings?|strikes?|attacks?|moves?|parries?)",
    ]

    for pattern in ally_patterns:
        if re.search(pattern, narrative, re.IGNORECASE):
            actors.append("Retainer/Ally")
            break

    # Look for enemy actions (Shadow-born, Malakor agent, bandits)
    enemy_patterns = [
        r"\b(?:shadow-born|shadow born)\b[^.!?]{0,50}?\b(?:flickers?|darts?|lunges?|swings?|strikes?|attacks?|moves?)",
        r"\b(?:malakor|agent)\b[^.!?]{0,50}?\b(?:sneers?|darts?|lunges?|swings?|strikes?|attacks?|moves?|lashes?)",
        r"\benemy\b[^.!?]{0,50}?\b(?:darts?|lunges?|swings?|strikes?|attacks?|moves?)",
    ]

    enemy_found = False
    for pattern in enemy_patterns:
        if re.search(pattern, narrative, re.IGNORECASE):
            if not enemy_found:
                actors.append("Enemy (Shadow-born/Malakor)")
                enemy_found = True
                break

    return len(actors) > 0, actors


def run_dragon_knight_repro_test(
    client: MCPClient,
    user_id: str,
    request_responses: list[dict[str, Any]],
) -> dict[str, Any]:
    """Reproduce Dragon Knight consecutive turns bug with exact scenario.

    This test reproduces the exact bug from production:
    1. Setup: Burst into room with Shadow-born + Malakor agent + 2 retainers
    2. Action 1: Divine Smite on Shadow-born
    3. Action 2: Shove Malakor agent
    4. Expected: Retainers/enemies should act between player actions
    5. Bug: Player takes both actions consecutively without NPC turns

    Args:
        client: MCP client
        user_id: User ID for test
        request_responses: List to append request/response pairs

    Returns:
        Test result dict with pass/fail status and evidence
    """
    print("\n" + "=" * 80)
    print("TEST: Dragon Knight Consecutive Turns Bug Reproduction")
    print("=" * 80)

    # Create campaign with exact Dragon Knight scenario
    print("Creating campaign with Dragon Knight scenario...")
    campaign_id = create_campaign(
        client,
        user_id=user_id,
        title="Dragon Knight Bug Reproduction",
        character="Ser Arion (Level 5 Paladin, with retainers: 2x Level 1 Fighters)",
        setting="Solar (room) - facing Shadow-born creature and Malakor agent",
        description=DRAGON_KNIGHT_SETUP,
    )
    print(f"  Campaign created: {campaign_id}")

    # Action 1: Divine Smite Shadow-born (exact text from entry #58)
    print("\n[Action 1] Divine Smite Shadow-born...")
    action_1_response = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input="Divine Smite Shadow-born - Unleash a Divine Smite on the creature of darkness to burn away its shadows.",
    )

    request_responses.append({
        "request": {
            "tool": "process_action",
            "user_id": user_id,
            "campaign_id": campaign_id,
            "user_input": "Divine Smite Shadow-born - Unleash a Divine Smite on the creature of darkness to burn away its shadows.",
            "action": 1,
        },
        "response": action_1_response,
    })

    # Check Action 1 for combat state
    state_updates = action_1_response.get("state_updates", {})
    combat_state = state_updates.get("combat_state", {})
    combat_initiated = combat_state.get("in_combat") is True

    print(f"  Combat initiated: {combat_initiated}")

    # Check Action 1 narrative for NPC actions
    narrative_1 = action_1_response.get("narrative", "")
    has_actions_1, actors_1 = has_non_player_actions(narrative_1)
    print(f"  Non-player actions in Action 1: {has_actions_1}")
    print(f"  Actors: {actors_1}")

    # Action 2: Shove Agent into Shadow (exact text from entry #60)
    print("\n[Action 2] Shove Agent into Shadow...")
    action_2_response = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input="Shove Agent into Shadow - Use your Strength to shove the Malakor agent into the path of the Shadow-born's shifting form.",
    )

    request_responses.append({
        "request": {
            "tool": "process_action",
            "user_id": user_id,
            "campaign_id": campaign_id,
            "user_input": "Shove Agent into Shadow - Use your Strength to shove the Malakor agent into the path of the Shadow-born's shifting form.",
            "action": 2,
        },
        "response": action_2_response,
    })

    # Check Action 2 narrative for NPC actions
    narrative_2 = action_2_response.get("narrative", "")
    has_non_player_turns, non_player_actors = has_non_player_actions(narrative_2)

    print(f"  Non-player actions in Action 2: {has_non_player_turns}")
    print(f"  Actors: {non_player_actors}")

    # Test passes if non-player actors took turns (fix working)
    # Test fails if only player acted (bug present - consecutive turns)
    passed = has_non_player_turns

    result = {
        "test": "dragon_knight_consecutive_turns",
        "status": "PASS" if passed else "FAIL",
        "scenario": "Dragon Knight campaign bug reproduction (entries 58-60)",
        "action_1": {
            "input": "Divine Smite Shadow-born",
            "actors": actors_1,
            "combat_initiated": combat_initiated,
            "narrative_length": len(narrative_1),
        },
        "action_2": {
            "input": "Shove Agent into Shadow",
            "non_player_actors": non_player_actors,
            "has_non_player_turns": has_non_player_turns,
            "narrative_sample": narrative_2[:800],
            "narrative_length": len(narrative_2),
        },
    }

    if passed:
        print("\n✅ TEST PASSED: Non-player combatants acted between player turns")
        print(f"   {len(non_player_actors)} non-player actor(s) took turns")
        print("   FIX WORKING: LLM enforces initiative order")
    else:
        print("\n❌ TEST FAILED: Player took consecutive turns without ally/enemy actions")
        print(f"   Only player acted in Action 2 - BUG REPRODUCED")
        print(f"   This matches the original Dragon Knight bug (entries 58-60)")
        print(f"   User had to manually complain at entry #62")

    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Reproduce Dragon Knight consecutive turns bug"
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
    evidence_dir = get_evidence_dir("dragon_knight_bug_repro")

    # Environment overrides for local server (REAL MODE - no mocks!)
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
        user_id = "test_dragon_knight_repro"
        result = run_dragon_knight_repro_test(client, user_id, request_responses)

        # Create evidence bundle
        bundle_files = create_evidence_bundle(
            session_dir,
            test_name="dragon_knight_bug_reproduction",
            provenance=provenance,
            results={"test_result": result},
            request_responses=request_responses,
            methodology_text="""# Test Methodology

## Objective
Reproduce the exact consecutive turns bug from Dragon Knight production campaign.

## Original Bug (Campaign wBoMKQuMnvLfyjTFTBHd, Entries 58-62)
- Entry #58 (user): "Divine Smite Shadow-born"
- Entry #59 (gemini): Response to Divine Smite (NO ally/enemy turns)
- Entry #60 (user): "Shove Agent into Shadow" (CONSECUTIVE PLAYER TURN - BUG!)
- Entry #61 (gemini): Response to Shove (still NO ally/enemy turns)
- Entry #62 (user): "make sure my team is also taking combat turns automatically" (USER COMPLAINT)

## Test Scenario
Exact scenario from Dragon Knight campaign:
- Character: Ser Arion (Level 5 Paladin)
- Allies: 2x retainers (Level 1 fighters)
- Enemies: Shadow-born (creature), Malakor agent (human)
- Location: Solar (room) after bursting through doors

## Test Steps
1. Create campaign with Dragon Knight scenario
2. Action 1: "Divine Smite Shadow-born" (exact text from entry #58)
3. Action 2: "Shove Agent into Shadow" (exact text from entry #60)
4. Verify Action 2 narrative includes non-player actor turns

## Red State (Bug Present)
Action 2 narrative shows ONLY player acting - no retainers or enemies take turns.
This reproduces the consecutive turns bug from the original Dragon Knight campaign.

## Green State (Fix Working)
Action 2 narrative shows retainers/enemies acting BEFORE or AFTER player action.
LLM enforces initiative order and prevents consecutive player turns.

## Pass Criteria
- Action 2 must include at least one non-player actor (retainer or enemy) taking a turn
- Narrative must show initiative order enforcement
- Combat system must automatically include NPC turns
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
