#!/usr/bin/env python3
"""Test server-side level-up detection when XP crosses threshold.

This test validates the fix for the issue where level-up was not triggered
when XP was awarded outside the normal rewards pipeline (e.g., God Mode,
narrative milestones).

Root cause addressed: RewardsAgent only triggered when specific state conditions
existed (combat_phase="ended", encounter_completed=true). When XP was awarded
narratively, level-up detection never ran and players had to manually request
level-up in God Mode.

Fix: Added _check_and_set_level_up_pending() in world_logic.py that runs for
ALL modes and sets rewards_pending.level_up_available=True when XP crosses
a level threshold.

Evidence: docs/debugging/Undertale (2).txt - Player had 8006 XP (Level 5
threshold is 6500) but level remained at 4 until manually requested.

Run against preview server:
    cd testing_mcp
    python test_server_side_level_up_detection.py --server-url https://mvp-site-app-s6-754683067800.us-central1.run.app

Run against local server:
    cd testing_mcp
    python test_server_side_level_up_detection.py --server-url http://127.0.0.1:8001
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from lib import (
    MCPClient,
    get_evidence_dir,
    capture_full_provenance,
    write_with_checksum,
)
from lib.campaign_utils import create_campaign, process_action, get_campaign_state


# D&D 5e XP thresholds for levels 4-6
XP_THRESHOLDS = {
    4: 2700,   # Level 4 requires 2,700 XP
    5: 6500,   # Level 5 requires 6,500 XP  <-- Key threshold
    6: 14000,  # Level 6 requires 14,000 XP
}


def seed_level_4_character(
    client: MCPClient, *, user_id: str, campaign_id: str, xp: int = 6206
) -> dict[str, Any]:
    """Seed a level 4 character with specific XP for testing.

    This mimics the Undertale campaign scenario where the character had
    6206 XP (below level 5 threshold of 6500) at level 4.

    Args:
        client: MCPClient instance.
        user_id: User identifier.
        campaign_id: Campaign identifier.
        xp: XP to set (default 6,206 - just below level 5 threshold).

    Returns:
        The seeded player character data.
    """
    seeded_pc = {
        "string_id": "pc_frisk_001",
        "name": "Frisk",
        "level": 4,
        "class": "Sorcerer",
        "hp_current": 32,
        "hp_max": 32,
        "attributes": {
            "strength": 10,
            "dexterity": 14,
            "constitution": 14,
            "intelligence": 12,
            "wisdom": 10,
            "charisma": 18,
        },
        "proficiency_bonus": 2,
        "experience": {
            "current": xp,
            "needed_for_next_level": XP_THRESHOLDS[5],  # 6,500
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


def test_level_up_detection_via_xp_increase(
    client: MCPClient, *, user_id: str, campaign_id: str
) -> dict[str, Any]:
    """Test that increasing XP past threshold triggers level-up detection.

    This is the KEY test case - when XP is set to 8006 (above 6500 threshold),
    the server should automatically set rewards_pending.level_up_available=True.

    Returns:
        Dict with test results including pass/fail and evidence.
    """
    # Set XP to 8006 (crossing the 6,500 threshold for level 5)
    # This mimics the Undertale scenario
    new_xp = 8006

    state_changes = {
        "player_character_data": {
            "experience": {
                "current": new_xp,
            }
        }
    }
    god_mode_payload = f"GOD_MODE_UPDATE_STATE:{json.dumps(state_changes)}"

    result = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=god_mode_payload,
    )

    if result.get("error"):
        return {
            "passed": False,
            "error": result["error"],
            "query": god_mode_payload,
            "test_type": "level_up_detection",
        }

    # Get the updated state
    state_payload = get_campaign_state(
        client, user_id=user_id, campaign_id=campaign_id
    )
    game_state = state_payload.get("game_state") or {}
    pc = game_state.get("player_character_data") or {}
    rewards_pending = game_state.get("rewards_pending") or {}

    current_level = pc.get("level")
    current_xp = None
    experience = pc.get("experience")
    if isinstance(experience, dict):
        current_xp = experience.get("current")
    elif experience is not None:
        current_xp = experience

    # Check if level-up was detected
    level_up_available = rewards_pending.get("level_up_available", False)
    new_level = rewards_pending.get("new_level")

    # The fix should either:
    # 1. Set rewards_pending.level_up_available=True with new_level=5, OR
    # 2. Auto-correct the level to 5 (via validate_and_correct_state)
    # Either outcome indicates the fix is working
    passed = (
        (level_up_available and new_level == 5) or
        current_level == 5
    )

    return {
        "passed": passed,
        "current_level": current_level,
        "current_xp": current_xp,
        "expected_level": 5,
        "xp_set": new_xp,
        "level_up_available": level_up_available,
        "new_level_in_rewards": new_level,
        "rewards_pending": rewards_pending,
        "query": god_mode_payload,
        "test_type": "level_up_detection",
    }


def test_no_level_up_when_below_threshold(
    client: MCPClient, *, user_id: str, campaign_id: str
) -> dict[str, Any]:
    """Negative test: No level-up should be triggered when XP is below threshold.

    Sets XP to 6000 (below 6,500 threshold for level 5).
    Should NOT trigger level_up_available.
    """
    # Set XP to 6000 (below threshold)
    new_xp = 6000

    state_changes = {
        "player_character_data": {
            "level": 4,  # Keep at level 4
            "experience": {
                "current": new_xp,
            }
        }
    }
    god_mode_payload = f"GOD_MODE_UPDATE_STATE:{json.dumps(state_changes)}"

    result = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=god_mode_payload,
    )

    if result.get("error"):
        return {
            "passed": False,
            "error": result["error"],
            "query": god_mode_payload,
            "test_type": "negative_below_threshold",
        }

    # Get the updated state
    state_payload = get_campaign_state(
        client, user_id=user_id, campaign_id=campaign_id
    )
    game_state = state_payload.get("game_state") or {}
    pc = game_state.get("player_character_data") or {}
    rewards_pending = game_state.get("rewards_pending") or {}

    current_level = pc.get("level")
    level_up_available = rewards_pending.get("level_up_available", False)

    # Should NOT have level_up_available since XP < threshold
    passed = not level_up_available and current_level == 4

    return {
        "passed": passed,
        "current_level": current_level,
        "xp_set": new_xp,
        "level_up_available": level_up_available,
        "expected_level_up_available": False,
        "query": god_mode_payload,
        "test_type": "negative_below_threshold",
    }


def test_no_duplicate_when_level_correct(
    client: MCPClient, *, user_id: str, campaign_id: str
) -> dict[str, Any]:
    """Test that no duplicate level-up is triggered when level already matches XP.

    Sets character to level 5 with 8006 XP.
    Should NOT trigger level_up_available since level is already correct.
    """
    state_changes = {
        "player_character_data": {
            "level": 5,  # Already at level 5
            "experience": {
                "current": 8006,
            }
        }
    }
    god_mode_payload = f"GOD_MODE_UPDATE_STATE:{json.dumps(state_changes)}"

    result = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=god_mode_payload,
    )

    if result.get("error"):
        return {
            "passed": False,
            "error": result["error"],
            "query": god_mode_payload,
            "test_type": "no_duplicate",
        }

    # Get the updated state
    state_payload = get_campaign_state(
        client, user_id=user_id, campaign_id=campaign_id
    )
    game_state = state_payload.get("game_state") or {}
    pc = game_state.get("player_character_data") or {}
    rewards_pending = game_state.get("rewards_pending") or {}

    current_level = pc.get("level")
    level_up_available = rewards_pending.get("level_up_available", False)

    # Should NOT have level_up_available since level already matches XP
    passed = current_level == 5 and not level_up_available

    return {
        "passed": passed,
        "current_level": current_level,
        "level_up_available": level_up_available,
        "expected_level_up_available": False,
        "query": god_mode_payload,
        "test_type": "no_duplicate",
    }


def run_tests(server_url: str) -> dict[str, Any]:
    """Run all server-side level-up detection tests with evidence collection.

    Args:
        server_url: Base URL of the server to test.

    Returns:
        Dict with all test results including git provenance.
    """
    # Capture full provenance FIRST per evidence standards
    print("Capturing git provenance...")
    provenance = capture_full_provenance(server_url)
    collection_start = datetime.now(timezone.utc).isoformat()

    client = MCPClient(server_url, timeout_s=120.0)

    print(f"Testing server: {server_url}")
    print("Waiting for server to be healthy...")

    try:
        client.wait_healthy(timeout_s=30.0)
        print("Server is healthy!")
    except Exception as e:
        return {"error": f"Server health check failed: {e}"}

    # Create test identifiers
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    test_run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    results = {
        "server_url": server_url,
        "test_run_id": test_run_id,
        "user_id": user_id,
        "collection_started": collection_start,
        "provenance": provenance,
        "tests": {},
    }

    # Create campaign
    print("\n1. Creating test campaign...")
    try:
        campaign_id = create_campaign(
            client,
            user_id,
            title="Level-Up Detection Test Campaign",
            character="Frisk (Level 4 Sorcerer)",
            setting="Testing grounds for level-up detection",
            description="Campaign for testing server-side level-up detection fix",
        )
        results["campaign_id"] = campaign_id
        print(f"   Campaign created: {campaign_id}")
    except Exception as e:
        results["error"] = f"Campaign creation failed: {e}"
        return results

    # Seed level 4 character
    print("\n2. Seeding level 4 character with 6,206 XP...")
    try:
        pc_data = seed_level_4_character(
            client, user_id=user_id, campaign_id=campaign_id, xp=6206
        )
        results["seeded_character"] = {
            "name": pc_data["name"],
            "level": pc_data["level"],
            "xp": pc_data["experience"]["current"],
        }
        print(f"   Character seeded: {pc_data['name']} (Level {pc_data['level']}, XP: {pc_data['experience']['current']})")
    except Exception as e:
        results["error"] = f"Character seeding failed: {e}"
        return results

    # Test 1: Level-up detection when XP crosses threshold (KEY TEST)
    print("\n3. Testing level-up detection when XP increases to 8006 (KEY TEST)...")
    print("   This should trigger rewards_pending.level_up_available=True")
    levelup_result = test_level_up_detection_via_xp_increase(
        client, user_id=user_id, campaign_id=campaign_id
    )
    results["tests"]["level_up_detection"] = levelup_result

    if levelup_result["passed"]:
        if levelup_result.get("level_up_available"):
            print(f"   ✅ PASSED: rewards_pending.level_up_available=True, new_level={levelup_result.get('new_level_in_rewards')}")
        else:
            print(f"   ✅ PASSED: Level auto-corrected to {levelup_result.get('current_level')}")
    else:
        print(f"   ❌ FAILED: Level-up not detected!")
        print(f"      current_level={levelup_result.get('current_level')}")
        print(f"      level_up_available={levelup_result.get('level_up_available')}")
        print(f"      rewards_pending={levelup_result.get('rewards_pending')}")

    # Test 2: Negative test - no level-up when below threshold
    print("\n4. Testing no level-up when XP below threshold (negative test)...")
    negative_result = test_no_level_up_when_below_threshold(
        client, user_id=user_id, campaign_id=campaign_id
    )
    results["tests"]["no_level_up_below_threshold"] = negative_result

    if negative_result["passed"]:
        print("   ✅ PASSED: No level-up triggered when XP < threshold")
    else:
        print(f"   ❌ FAILED: Unexpected level-up triggered!")
        print(f"      level_up_available={negative_result.get('level_up_available')}")

    # Test 3: No duplicate level-up when level already correct
    print("\n5. Testing no duplicate level-up when level already matches XP...")
    no_dup_result = test_no_duplicate_when_level_correct(
        client, user_id=user_id, campaign_id=campaign_id
    )
    results["tests"]["no_duplicate_level_up"] = no_dup_result

    if no_dup_result["passed"]:
        print("   ✅ PASSED: No duplicate level-up when level already correct")
    else:
        print(f"   ❌ FAILED: Duplicate level-up triggered!")
        print(f"      level_up_available={no_dup_result.get('level_up_available')}")

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    all_passed = all(
        test.get("passed", False)
        for test in results["tests"].values()
    )

    for test_name, test_result in results["tests"].items():
        status = "✅ PASS" if test_result.get("passed") else "❌ FAIL"
        print(f"  {test_name}: {status}")

    results["all_passed"] = all_passed
    results["collection_ended"] = datetime.now(timezone.utc).isoformat()
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")

    # Save evidence to /tmp structure with checksums per evidence-standards.md
    evidence_base = get_evidence_dir("level_up_detection_tests", test_run_id)
    evidence_base.mkdir(parents=True, exist_ok=True)

    # Write main evidence file with checksum
    evidence_json = json.dumps(results, indent=2, default=str)
    evidence_file = evidence_base / "test_results.json"
    checksum = write_with_checksum(evidence_file, evidence_json)
    print(f"\nEvidence saved to: {evidence_file}")
    print(f"SHA256: {checksum}")

    # Write README for evidence bundle
    git_prov = provenance.get("git_provenance", {})
    readme_content = f"""# Server-Side Level-Up Detection Test Evidence

## Test Run: {test_run_id}
## Server: {server_url}
## Result: {'PASSED' if all_passed else 'FAILED'}

## Purpose
Validates fix for: Level-up not triggered when XP awarded outside rewards pipeline.

Root cause: RewardsAgent only triggered on combat_phase="ended" or encounter_completed.
Fix: Added _check_and_set_level_up_pending() that runs for ALL modes.

## Git Provenance
- HEAD: {git_prov.get('head_commit', 'N/A')}
- Branch: {git_prov.get('branch', 'N/A')}
- Origin/Main: {git_prov.get('origin_main_commit', 'N/A')}

## Changed Files
{chr(10).join('- ' + f for f in git_prov.get('changed_files', []))}

## Collection Window
- Started: {results.get('collection_started', 'N/A')}
- Ended: {results.get('collection_ended', 'N/A')}

## Files
- test_results.json - Full test results with provenance
- test_results.json.sha256 - Checksum for verification
"""
    write_with_checksum(evidence_base / "README.md", readme_content)

    return results


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Test server-side level-up detection when XP crosses threshold"
    )
    parser.add_argument(
        "--server-url",
        default="https://mvp-site-app-s6-754683067800.us-central1.run.app",
        help="Server URL to test against",
    )
    args = parser.parse_args()

    results = run_tests(args.server_url)

    if results.get("error"):
        print(f"\n❌ Test run failed: {results['error']}")
        return 1

    return 0 if results.get("all_passed") else 1


if __name__ == "__main__":
    sys.exit(main())
