#!/usr/bin/env python3
"""Mission Auto-Completion Bug Reproduction Test.

This test reproduces the bug where missions remain in active_missions
even after their objectives are narratively completed, requiring manual
god mode intervention to close them.

Bug Context:
- User completed Sunderbrook mission (raided vault, transferred souls, cleared debt)
- Mission showed as active even after narrative completion
- Required god mode to manually close
- Firebase showed 0 completed_missions despite multiple finished arcs

Run (local):
    python testing_mcp/test_mission_auto_completion_bug.py --start-local

Run (preview):
    export MCP_SERVER_URL=https://mvp-site-app-s1-<hash>.us-central1.run.app
    python testing_mcp/test_mission_auto_completion_bug.py --server-url $MCP_SERVER_URL
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from lib import MCPClient
from lib.server_utils import (
    LocalServer,
    pick_free_port,
    start_local_mcp_server,
)
from lib.campaign_utils import (
    create_campaign,
    process_action,
    get_campaign_state,
)
from lib.evidence_utils import (
    get_evidence_dir,
    capture_git_provenance,
    write_with_checksum,
)


def setup_mission_state(
    client: MCPClient, user_id: str, campaign_id: str
) -> dict[str, Any]:
    """Setup a test mission in active_missions WITHOUT completed_missions field.

    This reproduces the EXACT bug from production:
    - active_missions field exists
    - completed_missions field DOES NOT EXIST (like Nocturne campaign)
    - When mission completes, there's nowhere for it to go
    """
    mission_state = {
        "custom_campaign_state": {
            "active_missions": [
                {
                    "id": "test_vault_heist_001",
                    "title": "Retrieve the Soul Vessel",
                    "description": "Raid the Counting House vault, steal the soul vessel containing 10,000 souls, and transfer it to clear Sunderbrook's debt.",
                    "objectives": [
                        {
                            "id": "obj_001",
                            "description": "Infiltrate the Counting House",
                            "completed": False,
                        },
                        {
                            "id": "obj_002",
                            "description": "Steal the soul vessel from the vault",
                            "completed": False,
                        },
                        {
                            "id": "obj_003",
                            "description": "Transfer souls to clear the debt",
                            "completed": False,
                        },
                    ],
                    "status": "active",
                    "created_at": datetime.now().isoformat(),
                }
            ],
            # NOTE: NO completed_missions field - this is the bug!
            # In production Nocturne campaign: has_completed_missions=False
        }
    }

    payload = f"GOD_MODE_UPDATE_STATE:{json.dumps(mission_state)}"
    result = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=payload,
        mode="character",
    )

    if result.get("error"):
        raise RuntimeError(f"Failed to setup mission state: {result['error']}")

    # Verify mission was added
    state = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
    game_state = state.get("game_state", {})
    ccs = game_state.get("custom_campaign_state", {})
    active = ccs.get("active_missions", [])

    if not active:
        raise RuntimeError("Mission setup failed - no active missions found")

    return game_state


def execute_mission_narrative(
    client: MCPClient, user_id: str, campaign_id: str
) -> list[dict[str, Any]]:
    """Execute narrative actions that complete all mission objectives.

    Returns:
        List of responses from each narrative action.
    """
    responses = []

    # Objective 1: Infiltrate
    print("    Executing: Infiltrate the Counting House...")
    resp1 = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input="I use my stealth expertise to bypass the guards and disable the alarm system, successfully infiltrating the Counting House vault level.",
        mode="character",
    )
    responses.append(resp1)
    time.sleep(1)

    # Objective 2: Steal the vessel
    print("    Executing: Steal the soul vessel...")
    resp2 = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input="I locate the massive crystal vessel containing the 10,000 souls and use my magic to extract it from the vault, securing it in my bag of holding.",
        mode="character",
    )
    responses.append(resp2)
    time.sleep(1)

    # Objective 3: Complete the transfer
    print("    Executing: Transfer souls to clear debt...")
    resp3 = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input="I deliver the soul vessel to the Solicitor, completing the transfer of all 10,000 souls. Sunderbrook's debt is now cleared and I am the Primary Creditor.",
        mode="character",
    )
    responses.append(resp3)
    time.sleep(1)

    return responses


def check_mission_completion(game_state: dict[str, Any]) -> dict[str, Any]:
    """Check if mission was auto-completed.

    Returns:
        Dict with analysis of mission state.
    """
    ccs = game_state.get("custom_campaign_state", {})
    active = ccs.get("active_missions", [])

    # Check if completed_missions field exists (production bug: it doesn't)
    has_completed_field = "completed_missions" in ccs
    completed = ccs.get("completed_missions", [])

    # Find our test mission
    test_mission = None
    mission_location = None

    for mission in active:
        if isinstance(mission, dict) and mission.get("id") == "test_vault_heist_001":
            test_mission = mission
            mission_location = "active"
            break

    if not test_mission:
        for mission in completed:
            if isinstance(mission, dict) and mission.get("id") == "test_vault_heist_001":
                test_mission = mission
                mission_location = "completed"
                break

    return {
        "mission_found": test_mission is not None,
        "mission_location": mission_location,
        "mission_data": test_mission,
        "active_missions_count": len(active),
        "completed_missions_count": len(completed),
        "has_completed_field": has_completed_field,
        "bug_reproduced": (
            mission_location == "active"  # Mission didn't move
            or not has_completed_field  # Or no completed_missions field exists
        ),
    }


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Mission Auto-Completion Bug Test")
    parser.add_argument(
        "--server-url",
        default=os.environ.get("MCP_SERVER_URL") or "http://127.0.0.1:8001",
        help="MCP server URL",
    )
    parser.add_argument(
        "--start-local",
        action="store_true",
        help="Start a local MCP server automatically",
    )
    parser.add_argument(
        "--user-id",
        default="test_mission_user",
        help="User ID for test campaign",
    )
    args = parser.parse_args()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    evidence_dir = get_evidence_dir("mission_auto_completion_bug", timestamp)

    print("=" * 60)
    print("Mission Auto-Completion Bug Reproduction Test")
    print("=" * 60)
    print(f"Evidence directory: {evidence_dir}")

    # Capture provenance
    print("\n📊 Capturing provenance...")
    try:
        git_provenance = capture_git_provenance(fetch_origin=False)
        print(f"   Git HEAD: {git_provenance.get('git_head', 'unknown')[:12]}")
        print(f"   Branch: {git_provenance.get('git_branch', 'unknown')}")
    except Exception as e:
        print(f"   ⚠️  Warning: {e}")
        git_provenance = {}

    # Start local server if requested
    local_server: LocalServer | None = None
    server_url = args.server_url

    if args.start_local:
        print("\n🚀 Starting local MCP server...")
        port = pick_free_port()
        local_server = start_local_mcp_server(port)
        server_url = f"http://127.0.0.1:{port}"
        print(f"   Local server started on {server_url}")

    try:
        # Connect
        print(f"\n📡 Connecting to {server_url}")
        client = MCPClient(f"{server_url}/mcp")

        print("   Checking health...")
        client.wait_healthy(timeout_s=10.0)
        print("   ✅ Server is healthy")

        # Create campaign
        print("\n📋 Creating test campaign...")
        campaign_id = create_campaign(
            client,
            args.user_id,
            title="Mission Auto-Completion Bug Test",
            character="Nocturne (Rogue, Level 10)",
            setting="Baldur's Gate - Testing mission completion detection",
            description="Reproducing the bug where completed missions don't auto-close",
        )
        print(f"   Campaign ID: {campaign_id}")

        # Setup mission
        print("\n🎯 Setting up test mission...")
        initial_state = setup_mission_state(client, args.user_id, campaign_id)
        initial_analysis = check_mission_completion(initial_state)
        print(f"   ✅ Mission added to active_missions")
        print(f"   Active missions: {initial_analysis['active_missions_count']}")
        print(f"   Completed missions: {initial_analysis['completed_missions_count']}")

        # Execute narrative that completes all objectives
        print("\n📖 Executing mission narrative (completing all objectives)...")
        narrative_responses = execute_mission_narrative(
            client, args.user_id, campaign_id
        )

        # Check if mission auto-completed
        print("\n🔍 Checking mission state after narrative completion...")
        final_state = get_campaign_state(
            client, user_id=args.user_id, campaign_id=campaign_id
        )
        final_game_state = final_state.get("game_state", {})
        final_analysis = check_mission_completion(final_game_state)

        print(f"   Mission location: {final_analysis['mission_location']}")
        print(f"   Active missions: {final_analysis['active_missions_count']}")
        print(f"   Completed missions: {final_analysis['completed_missions_count']}")
        print(f"   Has completed_missions field: {final_analysis['has_completed_field']}")

        # Determine result
        bug_reproduced = final_analysis["bug_reproduced"]
        has_completed_field = final_analysis["has_completed_field"]

        if bug_reproduced:
            print("\n❌ BUG REPRODUCED!")
            if not has_completed_field:
                print("   completed_missions field doesn't exist!")
                print("   This matches production Nocturne campaign structure")
                print("   Missions have nowhere to go when completed")
            elif final_analysis['mission_location'] == "active":
                print("   Mission stayed in active_missions despite completing all objectives")
            print("   This requires manual god mode intervention to close missions")
        else:
            print("\n✅ Bug NOT reproduced (mission auto-completed correctly)")
            print("   Mission was automatically moved to completed_missions")

        # Save evidence
        evidence = {
            "test": "mission_auto_completion_bug",
            "timestamp": datetime.now().isoformat(),
            "provenance": {"git": git_provenance},
            "initial_state": {
                "active_missions": initial_analysis["active_missions_count"],
                "completed_missions": initial_analysis["completed_missions_count"],
            },
            "narrative_actions": [
                {
                    "action": "Infiltrate the Counting House",
                    "response": resp.get("response", "")[:200],
                }
                for resp in narrative_responses
            ],
            "final_state": {
                "active_missions": final_analysis["active_missions_count"],
                "completed_missions": final_analysis["completed_missions_count"],
                "mission_location": final_analysis["mission_location"],
            },
            "bug_reproduced": bug_reproduced,
            "expected_behavior": "Mission should auto-move to completed_missions",
            "actual_behavior": (
                "Mission stayed in active_missions"
                if bug_reproduced
                else "Mission moved to completed_missions"
            ),
        }

        evidence_path = evidence_dir / "bug_reproduction_evidence.json"
        checksum = write_with_checksum(
            evidence_path, json.dumps(evidence, indent=2, default=str)
        )

        print(f"\n📄 Evidence saved: {evidence_path}")
        print(f"   SHA256: {checksum}")

        # Return exit code: 0 if auto-init worked (fix validated), 1 if bug still exists
        fix_validated = has_completed_field and final_analysis['mission_location'] == "completed"
        if fix_validated:
            print("\n✅ FIX VALIDATED: Auto-initialization working correctly!")
            return 0
        else:
            print("\n❌ FIX FAILED: Bug still exists")
            return 1

    finally:
        if local_server:
            print("\n🛑 Stopping local server...")
            local_server.stop()


if __name__ == "__main__":
    sys.exit(main())
