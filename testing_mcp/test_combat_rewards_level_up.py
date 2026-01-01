#!/usr/bin/env python3
"""Test that combat rewards trigger level-up detection by LLM.

This test validates that when combat ends and XP is awarded, the LLM:
1. Sets combat_summary with xp_earned
2. Detects that XP crosses level threshold
3. Offers level-up to the player

This is the PRIMARY path for level-up - the LLM should handle this case
directly without needing server-side fallback.

Run against preview server:
    cd testing_mcp
    python test_combat_rewards_level_up.py --server-url https://mvp-site-app-s6-754683067800.us-central1.run.app

Run against local server:
    cd testing_mcp
    python test_combat_rewards_level_up.py --server-url http://127.0.0.1:8001

Run with auto-started local server:
    cd testing_mcp
    python test_combat_rewards_level_up.py --start-local
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from lib import (
    MCPClient,
    XP_GAIN_PATTERNS,
    XP_THRESHOLDS,
    capture_provenance,
    create_evidence_bundle,
    get_evidence_dir,
    pick_free_port,
    start_local_mcp_server,
)
from lib.campaign_utils import create_campaign, get_campaign_state, process_action


def seed_character_near_threshold(
    client: MCPClient, *, user_id: str, campaign_id: str
) -> dict[str, Any]:
    """Seed a level 1 character with 250 XP (50 XP below level 2 threshold).

    Args:
        client: MCPClient instance.
        user_id: User identifier.
        campaign_id: Campaign identifier.

    Returns:
        The seeded player character data.
    """
    seeded_pc = {
        "string_id": "pc_test_combat_001",
        "name": "Ser Marcus",
        "level": 1,
        "class": "Fighter",
        "hp_current": 12,
        "hp_max": 12,
        "attributes": {
            "strength": 16,
            "dexterity": 14,
            "constitution": 14,
            "intelligence": 10,
            "wisdom": 12,
            "charisma": 10,
        },
        "proficiency_bonus": 2,
        "experience": {
            "current": 250,  # 50 XP below level 2 threshold (300)
            "needed_for_next_level": XP_THRESHOLDS[2],
        },
    }

    state_changes = {"player_character_data": seeded_pc}
    god_mode_payload = f"GOD_MODE_UPDATE_STATE:{json.dumps(state_changes)}"

    result = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=god_mode_payload,
    )
    if result.get("error"):
        raise RuntimeError(f"GOD_MODE_UPDATE_STATE failed: {result['error']}")

    return seeded_pc


def test_combat_rewards_level_up(
    client: MCPClient,
    *,
    user_id: str,
    campaign_id: str,
    request_responses: list[dict[str, Any]],
) -> dict[str, Any]:
    """Test that combat victory awards XP and triggers level-up.

    Steps:
    1. Seed character at level 1 with 250 XP (50 below threshold)
    2. Initiate combat against weak enemy (goblin = 50 XP)
    3. Kill the enemy
    4. Verify combat_summary.xp_earned is set
    5. Verify level-up is offered (rewards_pending.level_up_available or narrative mention)

    Returns:
        Dict with test results.
    """
    # Step 1: Seed character
    print("  Seeding level 1 character with 250 XP...")
    seed_character_near_threshold(client, user_id=user_id, campaign_id=campaign_id)

    # Verify seed
    state = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
    pc = (state.get("game_state") or {}).get("player_character_data") or {}
    initial_xp = (pc.get("experience") or {}).get("current", 0)
    initial_level = pc.get("level", 1)
    print(f"  Initial state: Level {initial_level}, XP {initial_xp}")

    # Step 2: Initiate combat
    print("  Initiating combat against a goblin...")
    combat_start = "I attack the goblin standing guard. I draw my longsword and strike!"

    result1 = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=combat_start,
    )
    request_responses.append({
        "step": "combat_initiation",
        "request": {"user_input": combat_start},
        "response": result1,
    })

    if result1.get("error"):
        return {
            "passed": False,
            "error": f"Combat initiation failed: {result1['error']}",
            "step": "combat_initiation",
        }

    # Step 3: Continue attacking until combat ends
    print("  Continuing combat...")
    max_rounds = 5
    combat_ended = False
    final_result = result1

    for round_num in range(2, max_rounds + 1):
        # Check if combat ended
        state_updates = final_result.get("state_updates") or {}
        combat_state = state_updates.get("combat_state") or {}

        if combat_state.get("combat_phase") == "ended":
            combat_ended = True
            break

        if not combat_state.get("in_combat", True):
            combat_ended = True
            break

        # Continue attacking
        attack_input = "I attack the goblin again with my longsword!"
        final_result = process_action(
            client,
            user_id=user_id,
            campaign_id=campaign_id,
            user_input=attack_input,
        )
        request_responses.append({
            "step": f"combat_round_{round_num}",
            "request": {"user_input": attack_input},
            "response": final_result,
        })

        if final_result.get("error"):
            return {
                "passed": False,
                "error": f"Combat round {round_num} failed: {final_result['error']}",
                "step": f"combat_round_{round_num}",
            }

    # Step 4: Check for combat_summary with XP
    state_updates = final_result.get("state_updates") or {}
    # combat_summary is nested under combat_state
    combat_state = state_updates.get("combat_state") or {}
    combat_summary = combat_state.get("combat_summary") or {}
    # Field is named xp_awarded, not xp_earned
    xp_earned = combat_summary.get("xp_awarded", 0)

    # Also check narrative for XP mention
    narrative = final_result.get("narrative", "")
    xp_in_narrative = any(re.search(p, narrative, re.IGNORECASE) for p in XP_GAIN_PATTERNS)

    # Step 5: Check for level-up detection
    final_state = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
    game_state = final_state.get("game_state") or {}
    final_pc = game_state.get("player_character_data") or {}
    rewards_pending = game_state.get("rewards_pending") or {}

    final_xp = (final_pc.get("experience") or {}).get("current", 0)
    final_level = final_pc.get("level", 1)
    level_up_available = rewards_pending.get("level_up_available", False)

    # Check narrative for level-up mention
    level_up_in_narrative = bool(re.search(
        r"level.{0,10}up|leveled up|reached level|advance.{0,10}level",
        narrative,
        re.IGNORECASE
    ))

    # Determine pass/fail
    xp_awarded = xp_earned > 0 or xp_in_narrative or final_xp > initial_xp
    level_up_detected = level_up_available or level_up_in_narrative or final_level > initial_level

    passed = combat_ended and xp_awarded and level_up_detected

    result = {
        "passed": passed,
        "combat_ended": combat_ended,
        "initial_state": {
            "level": initial_level,
            "xp": initial_xp,
        },
        "final_state": {
            "level": final_level,
            "xp": final_xp,
        },
        "combat_summary": {
            "xp_earned": xp_earned,
            "present": bool(combat_summary),
        },
        "level_up_detection": {
            "rewards_pending_available": level_up_available,
            "in_narrative": level_up_in_narrative,
            "level_increased": final_level > initial_level,
        },
        "xp_detection": {
            "in_combat_summary": xp_earned > 0,
            "in_narrative": xp_in_narrative,
            "xp_increased": final_xp > initial_xp,
        },
        "narrative_sample": narrative[:500] if narrative else "",
    }

    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Test combat rewards trigger level-up detection"
    )
    parser.add_argument(
        "--server-url",
        default=os.environ.get("MCP_SERVER_URL") or "http://127.0.0.1:8001",
        help="Server URL to test against",
    )
    parser.add_argument(
        "--start-local",
        action="store_true",
        help="Start local MCP server automatically",
    )
    args = parser.parse_args()

    local = None
    base_url = str(args.server_url)
    evidence_dir = get_evidence_dir("combat_rewards_level_up")

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

        client = MCPClient(base_url, timeout_s=180.0)
        print(f"Connecting to MCP server at {base_url}...")
        client.wait_healthy(timeout_s=45.0)
        print("Server is healthy")

        # Create session directory
        timestamp = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S")
        session_dir = evidence_dir / f"run_{timestamp}"
        session_dir.mkdir(parents=True, exist_ok=True)
        print(f"\nEvidence will be saved to: {session_dir}")

        # Capture provenance
        server_pid = local.proc.pid if local else None
        provenance = capture_provenance(
            base_url,
            server_pid,
            server_env_overrides=env_overrides if args.start_local else None,
        )

        # Create campaign
        user_id = f"test_combat_rewards_{timestamp}"
        print("\nCreating test campaign...")
        campaign_id = create_campaign(
            client,
            user_id=user_id,
            title="Combat Rewards Level-Up Test",
            character="Ser Marcus (Level 1 Fighter)",
            setting="A forest path with a goblin guard",
            description="Testing that combat XP triggers level-up detection",
        )
        print(f"Campaign created: {campaign_id}")

        # Run test
        print("\n" + "=" * 60)
        print("TEST: Combat Rewards Level-Up Detection")
        print("=" * 60)

        request_responses: list[dict[str, Any]] = []
        result = test_combat_rewards_level_up(
            client,
            user_id=user_id,
            campaign_id=campaign_id,
            request_responses=request_responses,
        )

        # Print results
        print("\n" + "=" * 60)
        print("TEST RESULTS")
        print("=" * 60)
        status = "PASS" if result["passed"] else "FAIL"
        print(f"Status: {'✅' if result['passed'] else '❌'} {status}")
        print(f"\nCombat ended: {result.get('combat_ended')}")
        print(f"Initial: Level {result['initial_state']['level']}, XP {result['initial_state']['xp']}")
        print(f"Final: Level {result['final_state']['level']}, XP {result['final_state']['xp']}")
        print(f"\nXP Detection:")
        for key, val in result.get("xp_detection", {}).items():
            print(f"  {key}: {val}")
        print(f"\nLevel-Up Detection:")
        for key, val in result.get("level_up_detection", {}).items():
            print(f"  {key}: {val}")

        # Create evidence bundle
        methodology_text = """# Methodology: Combat Rewards Level-Up Test

## Test Type
Real API test against MCP server (not mock mode).

## Purpose
Validates that when combat ends and XP is awarded, the LLM:
1. Sets combat_summary with xp_earned
2. Detects that XP crosses level threshold
3. Offers level-up to the player

This is the PRIMARY path for level-up detection - LLM should handle this
directly without needing server-side fallback.

## Test Steps
1. Seed character at level 1 with 250 XP (50 below level 2 threshold of 300)
2. Initiate combat against weak enemy (goblin = ~50 XP)
3. Continue combat until enemy defeated
4. Verify combat_summary.xp_earned is set
5. Verify level-up is offered (rewards_pending or narrative)

## Pass Criteria
- Combat ended successfully
- XP was awarded (in combat_summary, narrative, or state)
- Level-up was detected (rewards_pending.level_up_available, narrative mention, or level increased)
"""

        bundle_files = create_evidence_bundle(
            session_dir,
            test_name="combat_rewards_level_up",
            provenance=provenance,
            results={"test_result": result, "campaign_id": campaign_id},
            request_responses=request_responses,
            methodology_text=methodology_text,
        )

        print(f"\nEvidence bundle created: {session_dir}")
        print(f"Files: {', '.join(f.name for f in bundle_files.values())}")

        return 0 if result["passed"] else 1

    finally:
        if local is not None:
            local.stop()


if __name__ == "__main__":
    raise SystemExit(main())
