#!/usr/bin/env python3
"""Test that narrative XP awards trigger level-up detection by LLM.

This test validates that when XP is awarded for narrative reasons (quest
completion, story milestones), the LLM:
1. Awards XP in the narrative response
2. Detects that XP crosses level threshold
3. Offers level-up to the player

Evidence: docs/debugging/Undertale (2).txt - Player received narrative XP
(6,206 → 8,006) but LLM forgot to offer level-up. Player had to ask in
God Mode "shouldnt i be level 5 now?"

This test validates the LLM's PRIMARY responsibility to detect level-up
when awarding narrative XP.

Run against preview server:
    cd testing_mcp
    python test_narrative_xp_level_up.py --server-url https://mvp-site-app-s6-754683067800.us-central1.run.app

Run against local server:
    cd testing_mcp
    python test_narrative_xp_level_up.py --server-url http://127.0.0.1:8001

Run with auto-started local server:
    cd testing_mcp
    python test_narrative_xp_level_up.py --start-local
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


def seed_character_with_active_quest(
    client: MCPClient, *, user_id: str, campaign_id: str
) -> dict[str, Any]:
    """Seed a level 4 character with 6400 XP and an active quest near completion.

    This mimics the Undertale scenario where the character had XP just below
    level 5 threshold and was about to complete a major story quest.

    Args:
        client: MCPClient instance.
        user_id: User identifier.
        campaign_id: Campaign identifier.

    Returns:
        The seeded game state.
    """
    seeded_pc = {
        "string_id": "pc_test_narrative_001",
        "name": "Aldric",
        "level": 4,
        "class": "Wizard",
        "hp_current": 24,
        "hp_max": 24,
        "attributes": {
            "strength": 8,
            "dexterity": 14,
            "constitution": 12,
            "intelligence": 18,
            "wisdom": 14,
            "charisma": 10,
        },
        "proficiency_bonus": 2,
        "experience": {
            "current": 6400,  # 100 XP below level 5 threshold (6500)
            "needed_for_next_level": XP_THRESHOLDS[5],
        },
    }

    # Set up a quest that's ready to be completed
    quest_data = {
        "active_quests": [
            {
                "id": "quest_ancient_tome",
                "title": "The Ancient Tome",
                "description": "Recover the lost tome of Archmage Valdris from the ruins",
                "status": "in_progress",
                "objectives": [
                    {"description": "Find the hidden entrance", "completed": True},
                    {"description": "Navigate the trapped corridors", "completed": True},
                    {"description": "Retrieve the tome from the vault", "completed": False},
                ],
                "reward_xp": 500,  # Will push 6400 → 6900, crossing 6500 threshold
            }
        ]
    }

    state_changes = {
        "player_character_data": seeded_pc,
        "quests": quest_data,
    }
    god_mode_payload = f"GOD_MODE_UPDATE_STATE:{json.dumps(state_changes)}"

    result = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=god_mode_payload,
    )
    if result.get("error"):
        raise RuntimeError(f"GOD_MODE_UPDATE_STATE failed: {result['error']}")

    return state_changes


def test_narrative_xp_level_up(
    client: MCPClient,
    *,
    user_id: str,
    campaign_id: str,
    request_responses: list[dict[str, Any]],
) -> dict[str, Any]:
    """Test that completing a quest awards XP and triggers level-up.

    Steps:
    1. Seed character at level 4 with 6400 XP and active quest
    2. Complete the quest (retrieve the tome)
    3. Verify XP is awarded in narrative
    4. Verify level-up is offered (rewards_pending or narrative mention)

    Returns:
        Dict with test results.
    """
    # Step 1: Seed character with quest
    print("  Seeding level 4 character with 6400 XP and active quest...")
    seed_character_with_active_quest(client, user_id=user_id, campaign_id=campaign_id)

    # Verify seed
    state = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
    pc = (state.get("game_state") or {}).get("player_character_data") or {}
    initial_xp = (pc.get("experience") or {}).get("current", 0)
    initial_level = pc.get("level", 1)
    print(f"  Initial state: Level {initial_level}, XP {initial_xp}")

    # Step 2: Complete the quest
    print("  Completing the quest (retrieving the ancient tome)...")
    quest_completion = """I reach into the ancient vault and carefully retrieve the Tome of Archmage Valdris.
The quest is complete - I have recovered the lost tome! I examine my accomplishment."""

    result = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=quest_completion,
    )
    request_responses.append({
        "step": "quest_completion",
        "request": {"user_input": quest_completion},
        "response": result,
    })

    if result.get("error"):
        return {
            "passed": False,
            "error": f"Quest completion failed: {result['error']}",
            "step": "quest_completion",
        }

    # Step 3: Check for XP award in narrative
    narrative = result.get("narrative", "")
    xp_in_narrative = any(re.search(p, narrative, re.IGNORECASE) for p in XP_GAIN_PATTERNS)

    # Step 4: Check for level-up detection
    final_state = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
    game_state = final_state.get("game_state") or {}
    final_pc = game_state.get("player_character_data") or {}
    rewards_pending = game_state.get("rewards_pending") or {}

    final_xp = (final_pc.get("experience") or {}).get("current", 0)
    final_level = final_pc.get("level", 1)
    level_up_available = rewards_pending.get("level_up_available", False)

    # Check narrative for level-up mention
    level_up_patterns = [
        r"level.{0,10}up",
        r"leveled up",
        r"reached level\s*\d+",
        r"advance.{0,10}level",
        r"now level\s*\d+",
        r"level\s*\d+\s*!",
    ]
    level_up_in_narrative = any(re.search(p, narrative, re.IGNORECASE) for p in level_up_patterns)

    # Determine pass/fail
    xp_awarded = xp_in_narrative or final_xp > initial_xp
    level_up_detected = level_up_available or level_up_in_narrative or final_level > initial_level

    passed = xp_awarded and level_up_detected

    result_data = {
        "passed": passed,
        "initial_state": {
            "level": initial_level,
            "xp": initial_xp,
        },
        "final_state": {
            "level": final_level,
            "xp": final_xp,
        },
        "level_up_detection": {
            "rewards_pending_available": level_up_available,
            "in_narrative": level_up_in_narrative,
            "level_increased": final_level > initial_level,
        },
        "xp_detection": {
            "in_narrative": xp_in_narrative,
            "xp_increased": final_xp > initial_xp,
            "xp_delta": final_xp - initial_xp if final_xp > initial_xp else 0,
        },
        "narrative_sample": narrative[:800] if narrative else "",
    }

    return result_data


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Test narrative XP awards trigger level-up detection"
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
    evidence_dir = get_evidence_dir("narrative_xp_level_up")

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
        user_id = f"test_narrative_xp_{timestamp}"
        print("\nCreating test campaign...")
        campaign_id = create_campaign(
            client,
            user_id=user_id,
            title="Narrative XP Level-Up Test",
            character="Aldric (Level 4 Wizard)",
            setting="Ancient ruins containing the lost Tome of Archmage Valdris",
            description="Testing that narrative XP triggers level-up detection",
        )
        print(f"Campaign created: {campaign_id}")

        # Run test
        print("\n" + "=" * 60)
        print("TEST: Narrative XP Level-Up Detection")
        print("=" * 60)

        request_responses: list[dict[str, Any]] = []
        result = test_narrative_xp_level_up(
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
        print(f"\nInitial: Level {result['initial_state']['level']}, XP {result['initial_state']['xp']}")
        print(f"Final: Level {result['final_state']['level']}, XP {result['final_state']['xp']}")
        print(f"\nXP Detection:")
        for key, val in result.get("xp_detection", {}).items():
            print(f"  {key}: {val}")
        print(f"\nLevel-Up Detection:")
        for key, val in result.get("level_up_detection", {}).items():
            print(f"  {key}: {val}")

        if not result["passed"]:
            print("\n" + "=" * 60)
            print("NARRATIVE SAMPLE (for debugging):")
            print("=" * 60)
            print(result.get("narrative_sample", ""))

        # Create evidence bundle
        methodology_text = """# Methodology: Narrative XP Level-Up Test

## Test Type
Real API test against MCP server (not mock mode).

## Purpose
Validates that when XP is awarded for narrative reasons (quest completion,
story milestones), the LLM:
1. Awards XP in the narrative response
2. Detects that XP crosses level threshold
3. Offers level-up to the player

## Evidence Background
docs/debugging/Undertale (2).txt - Player received narrative XP (6,206 → 8,006)
but LLM forgot to offer level-up. Player had to ask in God Mode "shouldnt i be
level 5 now?"

## Test Steps
1. Seed character at level 4 with 6400 XP (100 below level 5 threshold of 6500)
2. Set up active quest with 500 XP reward
3. Complete the quest (narrative action)
4. Verify XP is mentioned in narrative or state
5. Verify level-up is offered (rewards_pending or narrative)

## Pass Criteria
- XP was awarded (in narrative or state increased)
- Level-up was detected (rewards_pending.level_up_available, narrative mention, or level increased)

## Known Issue
LLM sometimes forgets to check level threshold after awarding narrative XP.
Server-side fallback exists but LLM should handle this case.
"""

        bundle_files = create_evidence_bundle(
            session_dir,
            test_name="narrative_xp_level_up",
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
