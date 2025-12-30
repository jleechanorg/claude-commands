#!/usr/bin/env python3
"""Test XP threshold accuracy for level-up calculations.

This test validates that the LLM correctly reports XP thresholds for leveling up,
specifically testing the fix for the common confusion between level 8 (34,000 XP)
and level 9 (48,000 XP) thresholds.

Root cause addressed: LLM was misreading the XP table, quoting 48,000 XP as the
threshold to reach level 8 (wrong!) instead of 34,000 XP (correct).

Evidence Standards Compliance:
- Git provenance capture (HEAD, origin/main, branch, changed files)
- SHA256 checksums for all evidence files
- Timestamp synchronization (single-pass collection)
- /tmp/<repo>/<branch>/<work>/<timestamp>/ structure

Run against preview server:
    cd testing_mcp
    python test_level_up_xp_thresholds.py --server-url https://mvp-site-app-s6-754683067800.us-central1.run.app

Run against local server:
    cd testing_mcp
    python test_level_up_xp_thresholds.py --server-url http://127.0.0.1:8001
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from mcp_client import MCPClient
from lib.campaign_utils import create_campaign, process_action, get_campaign_state


def get_evidence_dir(test_run_id: str) -> Path:
    """Get evidence directory following /savetmp structure.

    Args:
        test_run_id: Timestamp string to use for directory name (ensures consistency).

    Returns /tmp/<repo>/<branch>/level_up_xp_tests/<test_run_id>/
    """
    try:
        git_root = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5
        ).stdout.strip()
        repo_name = Path(git_root).name if git_root else "unknown_repo"

        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, timeout=5
        ).stdout.strip() or "unknown_branch"
    except Exception:
        repo_name = "unknown_repo"
        branch = "unknown_branch"

    return Path("/tmp") / repo_name / branch / "level_up_xp_tests" / test_run_id


def capture_git_provenance() -> dict[str, Any]:
    """Capture git provenance per evidence-standards.md requirements."""
    provenance = {
        "capture_timestamp": datetime.now(timezone.utc).isoformat(),
        "working_directory": os.getcwd(),
    }

    git_commands = {
        "head_commit": ["git", "rev-parse", "HEAD"],
        "origin_main_commit": ["git", "rev-parse", "origin/main"],
        "branch": ["git", "branch", "--show-current"],
        "git_root": ["git", "rev-parse", "--show-toplevel"],
    }

    for key, cmd in git_commands.items():
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            provenance[key] = result.stdout.strip() if result.returncode == 0 else f"ERROR: {result.stderr.strip()}"
        except Exception as e:
            provenance[key] = f"ERROR: {e}"

    # Get changed files vs origin/main
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "origin/main...HEAD"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            provenance["changed_files"] = [f for f in result.stdout.strip().split("\n") if f]
        else:
            provenance["changed_files"] = []
    except Exception as e:
        provenance["changed_files"] = [f"ERROR: {e}"]

    return provenance


def write_with_checksum(filepath: Path, content: str) -> str:
    """Write file and create SHA256 checksum file.

    Returns the SHA256 hash.
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content)

    sha256_hash = hashlib.sha256(content.encode()).hexdigest()
    checksum_file = Path(str(filepath) + ".sha256")
    checksum_file.write_text(f"{sha256_hash}  {filepath.name}\n")

    return sha256_hash


def capture_server_health(server_url: str) -> dict[str, Any]:
    """Capture server health endpoint for version/build info.

    Returns server health data including version if available.
    """
    health_url = f"{server_url.rstrip('/')}/health"
    try:
        req = urllib.request.Request(health_url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            return {
                "url": health_url,
                "status_code": response.status,
                "response": data,
                "captured_at": datetime.now(timezone.utc).isoformat(),
            }
    except urllib.error.HTTPError as e:
        return {
            "url": health_url,
            "status_code": e.code,
            "error": str(e),
            "captured_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {
            "url": health_url,
            "error": str(e),
            "captured_at": datetime.now(timezone.utc).isoformat(),
        }


# Evidence stored per evidence-standards.md: /tmp/<repo>/<branch>/<work>/<timestamp>/
# No longer using testing_mcp/evidence/ - see get_evidence_dir() above

# D&D 5e XP thresholds - authoritative reference
XP_THRESHOLDS = {
    7: 23000,   # Level 7 requires 23,000 XP
    8: 34000,   # Level 8 requires 34,000 XP  <-- THE KEY TEST CASE
    9: 48000,   # Level 9 requires 48,000 XP
    10: 64000,  # Level 10 requires 64,000 XP
}

# Boundary test configurations
BOUNDARY_TESTS = [
    {"from_level": 7, "to_level": 8, "threshold": 34000, "test_xp": 34500},
    {"from_level": 8, "to_level": 9, "threshold": 48000, "test_xp": 48500},
    {"from_level": 9, "to_level": 10, "threshold": 64000, "test_xp": 64500},
]


def seed_level_7_character(
    client: MCPClient, *, user_id: str, campaign_id: str, xp: int = 33025
) -> dict[str, Any]:
    """Seed a level 7 character with specific XP for testing.

    Args:
        client: MCPClient instance.
        user_id: User identifier.
        campaign_id: Campaign identifier.
        xp: XP to set (default 33,025 - close to level 8 threshold).

    Returns:
        The seeded player character data.
    """
    seeded_pc = {
        "string_id": "pc_alexiel_001",
        "name": "Alexiel",
        "level": 7,
        "class": "Aberrant Mind Sorcerer / Assassin Rogue",
        "hp_current": 79,
        "hp_max": 79,
        "attributes": {
            "strength": 10,
            "dexterity": 18,
            "constitution": 14,
            "intelligence": 14,
            "wisdom": 12,
            "charisma": 16,
        },
        "proficiency_bonus": 3,
        "experience": {
            "current": xp,
            "needed_for_next_level": XP_THRESHOLDS[8],  # 34,000
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


def test_xp_threshold_query(
    client: MCPClient, *, user_id: str, campaign_id: str
) -> dict[str, Any]:
    """Ask the LLM about XP threshold for level 8 and validate response.

    This is the KEY test case - the LLM should correctly report 34,000 XP
    for level 8, NOT 48,000 XP (which is for level 9).

    Returns:
        Dict with test results including pass/fail and evidence.
    """
    query = "How much XP do I need for level 8? What is the exact threshold?"

    result = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=query,
        mode="character",
    )

    if result.get("error"):
        return {
            "passed": False,
            "error": result["error"],
            "query": query,
        }

    # Extract narrative and god_mode_response
    narrative = result.get("narrative", "")
    god_mode_response = result.get("god_mode_response", "")
    full_response = f"{narrative} {god_mode_response}".lower()

    # Check for CORRECT threshold (34,000 for level 8)
    has_correct_34k = any(
        pattern in full_response
        for pattern in ["34,000", "34000", "34k"]
    )

    # Check for WRONG threshold (48,000 is for level 9, not level 8!)
    has_wrong_48k_for_level8 = (
        "48,000" in full_response or "48000" in full_response
    ) and "level 8" in full_response

    # Also check if 48k is incorrectly associated with level 8
    level8_48k_confusion = bool(re.search(
        r"level\s*8.*48[,.]?000|48[,.]?000.*level\s*8",
        full_response,
        re.IGNORECASE
    ))

    passed = has_correct_34k and not level8_48k_confusion

    return {
        "passed": passed,
        "query": query,
        "narrative": narrative,  # Full response for evidence
        "has_correct_34k": has_correct_34k,
        "has_wrong_48k_for_level8": has_wrong_48k_for_level8,
        "level8_48k_confusion": level8_48k_confusion,
        "full_response": full_response,  # Full response for verification
    }


def test_level_up_via_xp_award(
    client: MCPClient, *, user_id: str, campaign_id: str
) -> dict[str, Any]:
    """Test that awarding XP correctly triggers level-up.

    Uses GOD_MODE_UPDATE_STATE to set XP to 34,525 (crossing the 34,000 threshold)
    and verifies the backend correctly triggers level-up to level 8.

    Note: Uses deterministic GOD_MODE_UPDATE_STATE command instead of natural
    language to ensure reliable state update. The backend should automatically
    compute level from XP.
    """
    # Set XP to cross the threshold (34,525 > 34,000 threshold for level 8)
    new_xp = 34525  # 33,025 + 1,500 = 34,525

    # Use GOD_MODE_UPDATE_STATE for reliable state update
    # Only set experience.current - backend should compute level from XP
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
        }

    # Get the updated state
    state_payload = get_campaign_state(
        client, user_id=user_id, campaign_id=campaign_id
    )
    game_state = state_payload.get("game_state") or {}
    pc = game_state.get("player_character_data") or {}

    current_level = pc.get("level")
    current_xp = None
    experience = pc.get("experience")
    if isinstance(experience, dict):
        current_xp = experience.get("current")
    elif experience is not None:
        current_xp = experience

    # The character should now be level 8 (XP >= 34,000)
    # Note: If backend doesn't auto-compute level from XP, this tests that too
    passed = current_level == 8 and current_xp is not None and current_xp >= 34000

    return {
        "passed": passed,
        "current_level": current_level,
        "current_xp": current_xp,
        "expected_level": 8,
        "expected_xp_min": 34000,
        "xp_set": new_xp,
        "query": god_mode_payload,
    }


def test_negative_48k_not_level8(
    client: MCPClient, *, user_id: str, campaign_id: str
) -> dict[str, Any]:
    """Negative test: Verify LLM does NOT associate 48,000 with level 8.

    This is the KEY negative test - 48,000 is for level 9, NOT level 8.
    The LLM should never say "48,000 XP for level 8".
    """
    # Ask about level 8 specifically and check for wrong answer
    query = "What is the exact XP threshold for level 8? Just give me the number."

    result = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=query,
        mode="character",
    )

    if result.get("error"):
        return {
            "passed": False,
            "error": result["error"],
            "query": query,
        }

    narrative = result.get("narrative", "")
    god_mode_response = result.get("god_mode_response", "")
    full_response = f"{narrative} {god_mode_response}".lower()

    # NEGATIVE CHECK: 48,000 should NOT be DIRECTLY attributed to level 8
    # Pattern: "48,000 for level 8" or "level 8 requires 48,000" or "level 8 is 48,000"
    # But NOT: "level 8 is 34,000... level 9 requires 48,000" (this is correct)
    bad_patterns = [
        r"level\s*8\s*(requires?|needs?|is|=|:)\s*48[,.]?000",
        r"48[,.]?000\s*(for|to reach|to get to)\s*level\s*8",
        r"reach\s*level\s*8.*48[,.]?000\s*(xp|points|experience)",
    ]
    has_48k_for_level8 = any(
        bool(re.search(pattern, full_response, re.IGNORECASE))
        for pattern in bad_patterns
    )

    # POSITIVE CHECK: Should have 34,000
    has_correct_34k = any(
        pattern in full_response
        for pattern in ["34,000", "34000", "34k"]
    )

    passed = has_correct_34k and not has_48k_for_level8

    return {
        "passed": passed,
        "query": query,
        "has_correct_34k": has_correct_34k,
        "has_wrong_48k_for_level8": has_48k_for_level8,
        "full_response": full_response,
        "test_type": "negative",
    }


def test_boundary_level_transition(
    client: MCPClient, *, user_id: str, campaign_id: str,
    from_level: int, to_level: int, threshold: int, test_xp: int
) -> dict[str, Any]:
    """Test boundary case: level transition at specific XP threshold.

    Sets character to from_level with XP just above threshold,
    verifies backend computes to_level correctly.
    """
    # Set character to from_level with XP above threshold
    state_changes = {
        "player_character_data": {
            "level": from_level,
            "experience": {
                "current": test_xp,
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
            "from_level": from_level,
            "to_level": to_level,
            "threshold": threshold,
            "test_xp": test_xp,
        }

    # Get updated state
    state_payload = get_campaign_state(
        client, user_id=user_id, campaign_id=campaign_id
    )
    game_state = state_payload.get("game_state") or {}
    pc = game_state.get("player_character_data") or {}

    current_level = pc.get("level")
    current_xp = None
    experience = pc.get("experience")
    if isinstance(experience, dict):
        current_xp = experience.get("current")
    elif experience is not None:
        current_xp = experience

    # Backend should compute to_level from XP
    passed = current_level == to_level and current_xp == test_xp

    return {
        "passed": passed,
        "from_level": from_level,
        "to_level": to_level,
        "threshold": threshold,
        "test_xp": test_xp,
        "current_level": current_level,
        "current_xp": current_xp,
        "test_type": "boundary",
    }


def run_tests(server_url: str) -> dict[str, Any]:
    """Run all XP threshold tests with evidence collection.

    Args:
        server_url: Base URL of the server to test.

    Returns:
        Dict with all test results including git provenance.
    """
    # Capture git provenance FIRST per evidence standards
    print("Capturing git provenance...")
    git_provenance = capture_git_provenance()
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

    # Capture server health/version info
    print("Capturing server health...")
    server_health = capture_server_health(server_url)
    print(f"   Server health captured: status={server_health.get('status_code', 'N/A')}")

    results = {
        "server_url": server_url,
        "test_run_id": test_run_id,
        "user_id": user_id,
        "collection_started": collection_start,
        "git_provenance": git_provenance,
        "server_health": server_health,
        "tests": {},
    }

    # Create campaign
    print("\n1. Creating test campaign...")
    try:
        campaign_id = create_campaign(
            client,
            user_id,
            title="XP Threshold Test Campaign",
            character="Alexiel (Level 7 Sorcerer/Rogue)",
            setting="Testing grounds for XP calculations",
            description="Campaign for testing XP threshold accuracy",
        )
        results["campaign_id"] = campaign_id
        print(f"   Campaign created: {campaign_id}")
    except Exception as e:
        results["error"] = f"Campaign creation failed: {e}"
        return results

    # Seed level 7 character
    print("\n2. Seeding level 7 character with 33,025 XP...")
    try:
        pc_data = seed_level_7_character(
            client, user_id=user_id, campaign_id=campaign_id, xp=33025
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

    # Test 1: XP threshold query
    print("\n3. Testing XP threshold query (KEY TEST)...")
    print("   Asking: 'How much XP do I need for level 8?'")
    threshold_result = test_xp_threshold_query(
        client, user_id=user_id, campaign_id=campaign_id
    )
    results["tests"]["xp_threshold_query"] = threshold_result

    if threshold_result["passed"]:
        print("   ✅ PASSED: LLM correctly reported 34,000 XP for level 8")
    else:
        print("   ❌ FAILED: LLM gave incorrect threshold")
        if threshold_result.get("level8_48k_confusion"):
            print("      ERROR: LLM confused level 8 (34,000) with level 9 (48,000)!")
        print(f"      Response preview: {threshold_result.get('full_response', 'N/A')[:200]}...")

    # Test 2: Level-up via XP award (only if first test passed)
    if threshold_result["passed"]:
        print("\n4. Testing level-up via XP award...")
        levelup_result = test_level_up_via_xp_award(
            client, user_id=user_id, campaign_id=campaign_id
        )
        results["tests"]["level_up_xp_award"] = levelup_result

        if levelup_result["passed"]:
            print(f"   ✅ PASSED: Character leveled up to {levelup_result['current_level']} with {levelup_result['current_xp']} XP")
        else:
            print(f"   ❌ FAILED: Expected level 8, got level {levelup_result.get('current_level')}")
            print(f"      Current XP: {levelup_result.get('current_xp')}")

    # Test 3: Negative test - 48,000 should NOT be associated with level 8
    print("\n5. Testing negative case (48,000 should NOT be level 8)...")
    negative_result = test_negative_48k_not_level8(
        client, user_id=user_id, campaign_id=campaign_id
    )
    results["tests"]["negative_48k_not_level8"] = negative_result

    if negative_result["passed"]:
        print("   ✅ PASSED: LLM correctly did NOT say 48,000 for level 8")
    else:
        print("   ❌ FAILED: LLM incorrectly associated 48,000 with level 8")
        if negative_result.get("has_wrong_48k_for_level8"):
            print("      ERROR: Found '48,000' associated with 'level 8' in response!")

    # Test 4-6: Boundary case tests (level 7→8, 8→9, 9→10)
    print("\n6. Testing boundary cases (level transitions)...")
    for i, boundary in enumerate(BOUNDARY_TESTS):
        test_name = f"boundary_{boundary['from_level']}_to_{boundary['to_level']}"
        print(f"   Testing level {boundary['from_level']}→{boundary['to_level']} at {boundary['threshold']:,} XP...")

        boundary_result = test_boundary_level_transition(
            client,
            user_id=user_id,
            campaign_id=campaign_id,
            from_level=boundary["from_level"],
            to_level=boundary["to_level"],
            threshold=boundary["threshold"],
            test_xp=boundary["test_xp"],
        )
        results["tests"][test_name] = boundary_result

        if boundary_result["passed"]:
            print(f"      ✅ PASSED: Level {boundary['from_level']}→{boundary['to_level']} at {boundary['test_xp']:,} XP")
        else:
            print(f"      ❌ FAILED: Expected level {boundary['to_level']}, got {boundary_result.get('current_level')}")

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
    # Use test_run_id for consistent naming (fixes timestamp mismatch)
    evidence_base = get_evidence_dir(test_run_id)
    evidence_base.mkdir(parents=True, exist_ok=True)

    # Write main evidence file with checksum
    evidence_json = json.dumps(results, indent=2, default=str)
    evidence_file = evidence_base / "test_results.json"
    checksum = write_with_checksum(evidence_file, evidence_json)
    print(f"\nEvidence saved to: {evidence_file}")
    print(f"SHA256: {checksum}")

    # Write README for evidence bundle
    readme_content = f"""# XP Threshold Test Evidence

## Test Run: {test_run_id}
## Server: {server_url}
## Result: {'PASSED' if all_passed else 'FAILED'}

## Git Provenance
- HEAD: {git_provenance.get('head_commit', 'N/A')}
- Branch: {git_provenance.get('branch', 'N/A')}
- Origin/Main: {git_provenance.get('origin_main_commit', 'N/A')}

## Changed Files
{chr(10).join('- ' + f for f in git_provenance.get('changed_files', []))}

## Collection Window
- Started: {results.get('collection_started', 'N/A')}
- Ended: {results.get('collection_ended', 'N/A')}

## Files
- test_results.json - Full test results with git provenance
- test_results.json.sha256 - Checksum for verification
"""
    write_with_checksum(evidence_base / "README.md", readme_content)

    return results


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Test XP threshold accuracy for level-up calculations"
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
