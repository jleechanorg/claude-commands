#!/usr/bin/env python3
"""Strict reproduction test for level-up planning block bug.

This test attempts to reproduce the ACTUAL failure from the user's campaign:
- Level-up text ("LEVEL UP AVAILABLE!") was shown
- But NO planning_block with clickable choices was generated
- User had to manually enter God Mode to level up

The key difference from test_level_up_planning_block_real_api.py:
1. Uses ORGANIC XP award (combat victory) instead of GOD_MODE_UPDATE_STATE
2. STRICT validation: FAILS if planning_block is missing (no fallback to text-only)
3. Requires EXACT choice IDs: level_up_now AND continue_adventuring

Run:
    python test_levelup_strict_repro.py --start-local
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from lib import (
    MCPClient,
    capture_provenance,
    create_evidence_bundle,
    get_evidence_dir,
    pick_free_port,
    start_local_mcp_server,
)
from lib.campaign_utils import create_campaign, get_campaign_state, process_action


def test_organic_levelup_planning_block(
    client: MCPClient, *, user_id: str, campaign_id: str
) -> dict[str, Any]:
    """Test that ORGANIC level-up (from combat XP) includes planning_block.

    This reproduces the failure scenario from the user's campaign where:
    1. Combat victory awarded XP
    2. XP crossed level threshold
    3. "LEVEL UP AVAILABLE!" text was shown
    4. But NO planning_block choices were provided

    STRICT VALIDATION:
    - MUST have planning_block.choices with level_up_now
    - MUST have planning_block.choices with continue_adventuring
    - Test FAILS if planning_block is missing (unlike lenient test)
    """
    errors: list[str] = []

    # Step 1: Set up character at level 4 with XP just below threshold (6400/6500)
    setup_state = {
        "player_character_data": {
            "name": "Nocturne",
            "level": 4,
            "class": "Bard",
            "experience": {"current": 6400},
            "hp_current": 27,
            "hp_max": 27,
        },
        "encounter_state": {
            "in_encounter": False,
            "encounter_type": None,
        }
    }
    god_setup = f"GOD_MODE_UPDATE_STATE:{json.dumps(setup_state)}"

    setup_result = process_action(
        client, user_id=user_id, campaign_id=campaign_id, user_input=god_setup
    )
    if setup_result.get("error"):
        return {"passed": False, "error": f"Setup failed: {setup_result['error']}"}

    # Verify setup
    state = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
    game_state = state.get("game_state", {})
    pc = game_state.get("player_character_data", {})
    exp = pc.get("experience", {})
    current_xp = exp.get("current") if isinstance(exp, dict) else exp

    if current_xp != 6400 or pc.get("level") != 4:
        return {
            "passed": False,
            "error": f"Setup verification failed: level={pc.get('level')}, xp={current_xp}",
        }

    # Step 2: Trigger combat encounter that will award XP
    # Using a scenario similar to the original campaign (guards encounter)
    combat_action = (
        "I approach the two guards blocking the corridor. "
        "Using my charm and wit, I convince them I'm a noble guest. "
        "When they let their guard down, Shadowheart casts Hold Person "
        "and Astarion silently eliminates them both. Combat victory."
    )

    combat_result = process_action(
        client, user_id=user_id, campaign_id=campaign_id, user_input=combat_action
    )

    if combat_result.get("error"):
        return {"passed": False, "error": f"Combat action failed: {combat_result['error']}"}

    # Extract response components
    response_text = ""
    planning_block = {}

    # Handle different response formats
    if isinstance(combat_result.get("response"), str):
        response_text = combat_result["response"]
    elif isinstance(combat_result.get("narrative"), str):
        response_text = combat_result["narrative"]
    elif isinstance(combat_result.get("story"), list):
        response_text = "\n".join(
            e.get("text", "") for e in combat_result["story"] if isinstance(e, dict)
        )

    planning_block = combat_result.get("planning_block", {})
    if not isinstance(planning_block, dict):
        planning_block = {}

    # STRICT CHECKS
    checks = {}

    # Check 1: Does narrative mention XP award?
    checks["has_xp_award"] = "XP" in response_text.upper()

    # Check 2: Does narrative mention level up?
    checks["has_levelup_text"] = "LEVEL UP" in response_text.upper()

    # Check 3: Is planning_block present?
    checks["has_planning_block"] = bool(planning_block)

    # Check 4: Does planning_block have choices?
    choices = planning_block.get("choices", {})
    checks["has_choices"] = bool(choices)

    # Check 5: STRICT - level_up_now choice exists
    checks["has_level_up_now"] = "level_up_now" in choices

    # Check 6: STRICT - continue_adventuring choice exists
    checks["has_continue_adventuring"] = "continue_adventuring" in choices

    # Check 7: Check state for level_up_available
    post_state = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
    post_game_state = post_state.get("game_state", {})
    rewards_pending = post_game_state.get("rewards_pending", {})
    checks["level_up_available_in_state"] = rewards_pending.get("level_up_available", False)

    # Determine pass/fail - STRICT mode
    # Must have BOTH text AND planning_block with exact choices
    if not checks["has_planning_block"]:
        errors.append("CRITICAL: No planning_block in response")
    if not checks["has_level_up_now"]:
        errors.append("CRITICAL: Missing level_up_now choice in planning_block")
    if not checks["has_continue_adventuring"]:
        errors.append("CRITICAL: Missing continue_adventuring choice in planning_block")
    if checks["has_levelup_text"] and not checks["has_planning_block"]:
        errors.append("BUG REPRODUCED: Level-up text shown but NO planning_block!")

    passed = (
        checks["has_planning_block"]
        and checks["has_level_up_now"]
        and checks["has_continue_adventuring"]
    )

    return {
        "passed": passed,
        "errors": errors,
        "checks": checks,
        "response_text": response_text[:3000],
        "planning_block": planning_block,
        "choices_found": list(choices.keys()) if choices else [],
        "game_state": {
            "level_up_available": checks["level_up_available_in_state"],
            "rewards_pending": rewards_pending,
        }
    }


def run_tests(
    client: MCPClient,
    *,
    base_url: str,
    provenance: dict[str, Any],
    server_log_path: Path | None,
    num_runs: int = 3,
) -> dict[str, Any]:
    """Run strict level-up test multiple times to check for intermittent failures."""
    test_run_id = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")

    all_results: list[dict[str, Any]] = []

    for i in range(num_runs):
        print(f"\n{'='*60}")
        print(f"RUN {i+1}/{num_runs}")
        print(f"{'='*60}")

        # Create fresh campaign for each run
        user_id = f"test_strict_levelup_{test_run_id}_run{i+1}"
        try:
            campaign_id = create_campaign(
                client,
                user_id=user_id,
                title=f"Strict Level-Up Test Run {i+1}",
                description="Testing organic level-up planning block generation",
            )
        except RuntimeError as e:
            all_results.append({
                "run": i + 1,
                "passed": False,
                "error": f"Campaign creation failed: {e}",
            })
            continue

        result = test_organic_levelup_planning_block(
            client, user_id=user_id, campaign_id=campaign_id
        )
        result["run"] = i + 1
        result["campaign_id"] = campaign_id
        result["user_id"] = user_id

        all_results.append(result)

        # Print result
        status = "✅ PASS" if result.get("passed") else "❌ FAIL"
        print(f"\nResult: {status}")

        for check, value in result.get("checks", {}).items():
            icon = "✅" if value else "❌"
            print(f"  {icon} {check}: {value}")

        if result.get("errors"):
            print("\nErrors:")
            for err in result["errors"]:
                print(f"  ⚠️  {err}")

        if not result.get("passed"):
            print(f"\nResponse text (first 500 chars):")
            print(result.get("response_text", "")[:500])
            print(f"\nPlanning block: {result.get('planning_block')}")

    # Summary
    passed_count = sum(1 for r in all_results if r.get("passed"))
    failed_count = len(all_results) - passed_count

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Passed: {passed_count}/{len(all_results)}")
    print(f"Failed: {failed_count}/{len(all_results)}")

    if failed_count > 0:
        print("\n🔴 RED EVIDENCE CAPTURED - Bug reproduced!")
    else:
        print("\n🟢 All runs passed - Bug not reproduced in this session")

    # Save evidence
    evidence_dir = get_evidence_dir("levelup_strict_repro") / test_run_id
    evidence_dir.mkdir(parents=True, exist_ok=True)

    scenarios = [
        {
            "name": f"Organic Level-Up Run {r['run']}",
            "campaign_id": r.get("campaign_id"),
            "passed": r.get("passed", False),
            "errors": r.get("errors", []),
            "checks": r.get("checks", {}),
            "response_text": r.get("response_text", ""),
            "planning_block": r.get("planning_block", {}),
        }
        for r in all_results
    ]

    results_summary = {
        "scenarios": scenarios,
        "summary": {
            "total_runs": len(all_results),
            "passed": passed_count,
            "failed": failed_count,
        },
        "test_run_id": test_run_id,
    }

    methodology = f"""# Methodology: Strict Level-Up Planning Block Reproduction

## Purpose
Reproduce the ACTUAL bug from user's campaign (Nocturne bg3 v4):
- Level-up text was shown but NO planning_block choices
- User had to manually enter God Mode to level up

## Key Difference from Standard Test
1. Uses ORGANIC XP award (combat scenario) not GOD_MODE_UPDATE_STATE
2. STRICT validation - FAILS if planning_block missing
3. Requires EXACT choice IDs: level_up_now, continue_adventuring
4. Multiple runs to detect intermittent failures

## Execution
1. Set character to level 4, XP=6400 (below 6500 threshold)
2. Trigger combat encounter → expect XP award
3. XP crosses threshold → expect level-up notification
4. STRICT CHECK: Must have planning_block with exact choices

## Pass/Fail Criteria (STRICT)
PASS only if ALL conditions met:
- planning_block is present
- planning_block.choices.level_up_now exists
- planning_block.choices.continue_adventuring exists

FAIL if planning_block missing (even if text mentions level-up)
"""

    bundle_files = create_evidence_bundle(
        evidence_dir,
        test_name="levelup_strict_repro",
        provenance=provenance,
        results=results_summary,
        request_responses=client.get_captures_as_dict(),
        methodology_text=methodology,
        server_log_path=server_log_path,
    )

    print(f"\nEvidence saved to: {evidence_dir}")

    return {
        "all_passed": failed_count == 0,
        "results": all_results,
        "evidence_dir": str(evidence_dir),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Strict reproduction test for level-up planning block bug"
    )
    parser.add_argument(
        "--server-url",
        default="http://127.0.0.1:8001",
        help="Server URL to test against",
    )
    parser.add_argument(
        "--start-local",
        action="store_true",
        help="Start local MCP server automatically",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=3,
        help="Number of test runs (default: 3)",
    )
    args = parser.parse_args()

    local = None
    base_url = str(args.server_url)
    evidence_dir = get_evidence_dir("levelup_strict_repro")

    try:
        if args.start_local:
            port = pick_free_port()
            env_overrides = {
                "MOCK_SERVICES_MODE": "false",
                "TESTING": "false",
                "CAPTURE_RAW_LLM": "true",
            }
            local = start_local_mcp_server(
                port,
                env_overrides=env_overrides,
                log_dir=evidence_dir,
            )
            base_url = local.base_url

        client = MCPClient(base_url, timeout_s=180.0)
        client.wait_healthy(timeout_s=60.0)

        server_pid = local.proc.pid if local else None
        provenance = capture_provenance(base_url, server_pid)

        results = run_tests(
            client,
            base_url=base_url,
            provenance=provenance,
            server_log_path=local.log_path if local else None,
            num_runs=args.runs,
        )

        return 0 if results.get("all_passed") else 1

    finally:
        if local:
            local.stop()


if __name__ == "__main__":
    sys.exit(main())
