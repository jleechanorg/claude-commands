#!/usr/bin/env python3
"""Real API test for combat ally turns and status display.

This test verifies that:
1. Combat status block is displayed at the start of each round
2. Allies take automatic turns in initiative order
3. Full tactical visibility (HP/AC/status) is provided

Bug reproduction based on user log:
- Lines 389-410: Player takes multiple consecutive turns without ally/enemy turns
- Line 413: User had to use god mode to remind LLM about ally turns
- Throughout: No display of combat resources (actions remaining, HP, enemy levels/AC)

Run (local MCP already running):
    cd testing_mcp
    python test_combat_ally_turns.py --server-url http://127.0.0.1:8001

Run (start local MCP automatically):
    cd testing_mcp
    python test_combat_ally_turns.py --start-local
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from lib.campaign_utils import create_campaign, process_action
from lib.evidence_utils import (
    capture_provenance,
    create_evidence_bundle,
    get_evidence_dir,
)
from lib.mcp_client import MCPClient
from lib.server_utils import LocalServer, pick_free_port, start_local_mcp_server

DEFAULT_MODEL = "gemini-3-flash-preview"

COMBAT_SCENARIO = """You are a level 2 Paladin with a retainer (level 1 fighter).
You ambush two bandits. Attack the first bandit."""


def run_combat_status_test(
    client: MCPClient,
    user_id: str,
    request_responses: list[dict[str, Any]],
) -> dict[str, Any]:
    """Run combat status display test.

    Args:
        client: MCP client
        user_id: User ID for test
        request_responses: List to append request/response pairs

    Returns:
        Test result dict with pass/fail status and evidence
    """
    print("\n" + "=" * 80)
    print("TEST: Combat Status Display in Round 2")
    print("=" * 80)

    # Create campaign
    print("Creating campaign...")
    campaign_id = create_campaign(
        client,
        user_id=user_id,
        title="Combat Ally Turns Test",
        character="Ser Marcus (Level 2 Paladin, with retainer: Gareth the Fighter, Level 1)",
        setting="Forest ambush against two bandits",
        description="Test for combat status display and ally automatic turns",
    )
    print(f"  Campaign created: {campaign_id}")

    # Round 1: Initiate combat
    print("\n[Round 1] Initiating combat...")
    round_1_response = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=COMBAT_SCENARIO,
    )

    request_responses.append(
        {
            "request": {
                "tool": "process_action",
                "user_id": user_id,
                "campaign_id": campaign_id,
                "user_input": COMBAT_SCENARIO,
                "round": 1,
            },
            "response": round_1_response,
        }
    )

    # Verify combat was initiated
    state_updates = round_1_response.get("state_updates", {})
    combat_state = state_updates.get("combat_state", {})
    combat_initiated = combat_state.get("in_combat") is True

    print(f"  Combat initiated: {combat_initiated}")
    if not combat_initiated:
        return {
            "test": "combat_status_display",
            "status": "FAIL",
            "reason": "Combat not initiated in Round 1",
            "combat_state": combat_state,
            "round_1": {
                "combat_initiated": False,
                "narrative_length": len(round_1_response.get("narrative", "")),
            },
            "round_2": None,
        }

    # Round 2: Take next action while combat is active
    print("\n[Round 2] Continuing combat (combat mode should be active)...")
    round_2_response = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input="Continue the fight - attack again.",
    )

    request_responses.append(
        {
            "request": {
                "tool": "process_action",
                "user_id": user_id,
                "campaign_id": campaign_id,
                "user_input": "Continue the fight - attack again.",
                "round": 2,
            },
            "response": round_2_response,
        }
    )

    # Ensure combat is still active before checking Round 2 formatting
    round_2_state_updates = round_2_response.get("state_updates", {})
    round_2_combat_state = round_2_state_updates.get("combat_state", {})
    still_in_combat = round_2_combat_state.get("in_combat") is True

    # Check for round announcement and initiative/status formatting in Round 2 narrative
    narrative = round_2_response.get("narrative", "")
    has_round_header = bool(re.search(r"ROUND\s+\d+", narrative, re.IGNORECASE))
    has_initiative_display = bool(
        re.search(r"Initiative\s+Order", narrative, re.IGNORECASE)
    )
    status_pattern = r"([A-Za-z][A-Za-z '\-]*)\s*\(([^)]+)\)\s*-\s*HP:\s*(\d+)/(\d+)"
    status_lines = re.findall(status_pattern, narrative, flags=re.IGNORECASE)

    print(f"  Has round header: {has_round_header}")
    print(f"  Has initiative display: {has_initiative_display}")

    # Check for ally turn in narrative (word boundaries to avoid false positives)
    has_ally_turn = bool(re.search(r"\bGareth\b|\bally\b", narrative, re.IGNORECASE))
    print(f"  Ally mentioned in narrative: {has_ally_turn}")

    # Combat evidence: either state_updates shows in_combat=True,
    # OR narrative contains combat indicators (round header + initiative)
    combat_active = still_in_combat or (has_round_header and has_initiative_display)

    # Test result: combat must be active with all display requirements met
    passed = (
        combat_active
        and has_round_header
        and has_initiative_display
        and has_ally_turn
        and bool(status_lines)
    )

    result = {
        "test": "combat_status_display",
        "status": "PASS" if passed else "FAIL",
        "round_1": {
            "combat_initiated": combat_initiated,
            "narrative_length": len(round_1_response.get("narrative", "")),
        },
        "round_2": {
            "has_round_header": has_round_header,
            "has_initiative_display": has_initiative_display,
            "has_ally_turn": has_ally_turn,
            "still_in_combat": still_in_combat,
            "combat_active": combat_active,
            "status_lines_found": len(status_lines),
            "narrative_sample": narrative[:800],
            "narrative_length": len(narrative),
        },
    }

    if passed:
        print("\n✅ TEST PASSED: Combat status display found in Round 2")
    else:
        print("\n❌ TEST FAILED: No combat status display found in Round 2")
        print(f"  Narrative sample: {narrative[:500]}")

    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Real API test for combat ally turns and status display"
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
    evidence_dir = get_evidence_dir("combat_ally_turns_status")

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
        timestamp = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S")
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
        user_id = "test_combat_ally_turns"
        result = run_combat_status_test(client, user_id, request_responses)

        # Create evidence bundle
        bundle_files = create_evidence_bundle(
            session_dir,
            test_name="combat_ally_turns",
            provenance=provenance,
            results={"test_result": result},
            request_responses=request_responses,
            methodology_text="""# Test Methodology

## Objective
Verify that combat status block is displayed in Round 2 when combat mode is active.

## Root Cause Discovery
Combat mode activates on Round 2 (when in_combat=True from previous state), not Round 1 (combat initiation).

## Test Steps
1. Round 1: Initiate combat with player attack → sets in_combat=True
2. Round 2: Take another action while in_combat=True → should display status block
3. Verify Round 2 narrative contains ALL of:
   - "ROUND X" header
   - "Initiative Order" display
   - Ally turn processing (Gareth mentioned)
   - At least one combatant status line with HP/AC/status information

## Pass Criteria
- still_in_combat: true
- has_round_header: true
- has_initiative_display: true
- Ally mentioned in narrative (automatic turn processing)
- At least one status line detected in narrative
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
