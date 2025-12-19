#!/usr/bin/env python3
"""Smoke test for dice roll code_execution validation.

This test:
1. Creates a test campaign via API
2. Triggers a player action that requires dice rolls (attack/skill check)
3. Validates that code_execution_used is True in the response
4. Saves evidence to /tmp subdirectory

Usage:
    python scripts/smoke_test_dice_code_execution.py [--server-url URL]
"""

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests

# Test configuration
DEFAULT_SERVER_URL = "http://localhost:8081"
TEST_USER_EMAIL = os.getenv("TEST_USER_EMAIL", "test-user@example.com")
PROJECT_ROOT = Path(__file__).resolve().parent.parent
EVIDENCE_DIR = PROJECT_ROOT / "tmp" / "worldarchitect.ai" / "dice_code_execution_tests"


def get_auth_headers() -> dict[str, str]:
    """Get auth headers for test user.

    Uses X-Test-Bypass-Auth header for TESTING mode.
    """
    return {
        "Content-Type": "application/json",
        "X-Test-Bypass-Auth": "true",
        "X-Test-User-ID": TEST_USER_EMAIL,
    }


def create_test_campaign(server_url: str) -> dict[str, Any]:
    """Create a test campaign that will trigger dice rolls."""
    headers = get_auth_headers()

    # Campaign setup that encourages dice rolls - character must be a string
    payload = {
        "title": f"Dice Code Execution Test - {datetime.now(UTC).isoformat()}",
        "character": "TestFighter, a level 5 Human Fighter with 16 STR, 14 DEX, 15 CON",
        "setting": "generic_fantasy",
        "description": "A combat-focused test to verify dice code execution. Start in a dungeon facing a goblin.",
    }

    try:
        response = requests.post(
            f"{server_url}/api/campaigns",
            json=payload,
            headers=headers,
            timeout=120,
        )
    except requests.exceptions.RequestException as exc:
        print(f"❌ Network error creating campaign: {exc}")
        return {}

    if response.status_code not in (200, 201):
        print(f"❌ Failed to create campaign: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        return {}

    try:
        return response.json()
    except json.JSONDecodeError as exc:
        print(f"❌ Failed to parse campaign response JSON: {exc}")
        return {}


def trigger_dice_roll_action(server_url: str, campaign_id: str) -> dict[str, Any]:
    """Send a player action that should trigger dice rolls."""
    headers = get_auth_headers()

    # Action that MUST trigger dice rolls (combat/skill check)
    # Note: main.py API expects "input" field, not "user_input"
    payload = {
        "input": "I attack the goblin with my longsword. Roll to hit and damage.",
    }

    print(f"📤 Sending action: {payload['input']}")

    try:
        response = requests.post(
            f"{server_url}/api/campaigns/{campaign_id}/interaction",
            json=payload,
            headers=headers,
            timeout=180,  # LLM calls can be slow
        )
    except requests.exceptions.RequestException as exc:
        print(f"❌ Network error during action: {exc}")
        return {}

    if response.status_code != 200:
        print(f"❌ Failed to continue game: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        return {}

    try:
        return response.json()
    except json.JSONDecodeError as exc:
        print(f"❌ Failed to parse action response JSON: {exc}")
        return {}


def _extract_debug_info(response_data: dict[str, Any]) -> dict[str, Any]:
    """Extract debug_info from response, game_state, or story entries."""
    debug_info = response_data.get("debug_info")
    if isinstance(debug_info, dict) and debug_info:
        return debug_info

    game_state = response_data.get("game_state", {})
    if isinstance(game_state, dict):
        debug_info = game_state.get("debug_info")
        if isinstance(debug_info, dict) and debug_info:
            return debug_info

    story = response_data.get("story", [])
    if isinstance(story, list):
        for entry in story:
            if entry.get("actor") == "gemini":
                entry_debug = entry.get("debug_info", {})
                if isinstance(entry_debug, dict) and entry_debug:
                    return entry_debug

    return {}


def validate_code_execution(response_data: dict[str, Any]) -> dict[str, Any]:
    """Validate that code_execution was actually used for dice rolls."""
    result = {
        "timestamp": datetime.now(UTC).isoformat(),
        "has_dice_rolls": False,
        "code_execution_used": False,
        "executable_code_parts": 0,
        "code_execution_result_parts": 0,
        "dice_rolls": [],
        "dice_audit_events": [],
        "validation_passed": False,
        "errors": [],
    }

    # Check for dice_rolls in response
    dice_rolls = response_data.get("dice_rolls", [])
    if dice_rolls:
        result["dice_rolls"] = dice_rolls
        print(f"🎲 Found dice_rolls: {dice_rolls}")

    # Check for dice_audit_events
    audit_events = response_data.get("dice_audit_events", [])
    if audit_events:
        result["dice_audit_events"] = audit_events
        print(f"📋 Found dice_audit_events: {len(audit_events)} events")

    result["has_dice_rolls"] = bool(dice_rolls or audit_events)

    debug_info = _extract_debug_info(response_data)
    if debug_info:
        result["code_execution_used"] = debug_info.get("code_execution_used", False)
        result["executable_code_parts"] = debug_info.get("executable_code_parts", 0)
        result["code_execution_result_parts"] = debug_info.get(
            "code_execution_result_parts", 0
        )

        print("🔍 Debug info found:")
        print(f"   code_execution_used: {result['code_execution_used']}")
        print(f"   executable_code_parts: {result['executable_code_parts']}")
        print(
            f"   code_execution_result_parts: {result['code_execution_result_parts']}"
        )

    # Validation logic
    if result["has_dice_rolls"]:
        if result["code_execution_used"]:
            if result["executable_code_parts"] > 0:
                result["validation_passed"] = True
                print("✅ VALIDATION PASSED: Gemini used code_execution for dice rolls")
            else:
                result["errors"].append(
                    "code_execution_used=True but no executable_code_parts found"
                )
                print("⚠️ WARNING: code_execution_used but no code parts detected")
        else:
            result["errors"].append(
                "Dice rolls present but code_execution_used=False - FABRICATED DICE!"
            )
            print(
                "🚨 VALIDATION FAILED: Dice rolls were FABRICATED (no code execution)"
            )
    else:
        result["errors"].append("No dice rolls or dice_audit_events found in response")
        print("⚠️ WARNING: No dice rolls found - test inconclusive")

    return result


def save_evidence(
    evidence_dir: Path,
    campaign_response: dict[str, Any],
    action_response: dict[str, Any],
    validation_result: dict[str, Any],
) -> Path:
    """Save all evidence to the specified directory."""
    evidence_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    test_dir = evidence_dir / f"test_{timestamp}"
    test_dir.mkdir(exist_ok=True)

    # Save campaign creation response
    with open(test_dir / "01_campaign_creation.json", "w") as f:
        json.dump(campaign_response, f, indent=2, default=str)

    # Save action response
    with open(test_dir / "02_action_response.json", "w") as f:
        json.dump(action_response, f, indent=2, default=str)

    # Save validation result
    with open(test_dir / "03_validation_result.json", "w") as f:
        json.dump(validation_result, f, indent=2, default=str)

    # Save summary
    summary = {
        "timestamp": timestamp,
        "validation_passed": validation_result["validation_passed"],
        "code_execution_used": validation_result["code_execution_used"],
        "has_dice_rolls": validation_result["has_dice_rolls"],
        "dice_rolls": validation_result["dice_rolls"],
        "errors": validation_result["errors"],
    }
    with open(test_dir / "00_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n📁 Evidence saved to: {test_dir}")
    return test_dir


def run_smoke_test(server_url: str) -> bool:
    """Run the complete smoke test."""
    print(f"\n{'=' * 60}")
    print("🧪 DICE CODE EXECUTION SMOKE TEST")
    print(f"{'=' * 60}")
    print(f"Server: {server_url}")
    print(f"Time: {datetime.now(UTC).isoformat()}")
    print()

    # Step 1: Create test campaign (uses X-Test-Bypass-Auth headers)
    print("📝 Creating test campaign...")
    campaign_response = create_test_campaign(server_url)
    if not campaign_response:
        print("❌ TEST FAILED: Could not create campaign")
        return False

    campaign_id = campaign_response.get("campaign_id")
    if not campaign_id:
        print(f"❌ TEST FAILED: No campaign_id in response: {campaign_response}")
        return False

    print(f"✅ Campaign created: {campaign_id}")

    # Step 2: Trigger dice roll action
    print("\n⚔️ Triggering combat action (requires dice rolls)...")
    action_response = trigger_dice_roll_action(server_url, campaign_id)
    if not action_response:
        print("❌ TEST FAILED: No response from game action")
        return False

    # Step 3: Validate code execution
    print("\n🔍 Validating code execution...")
    validation_result = validate_code_execution(action_response)

    # Step 4: Save evidence
    evidence_path = save_evidence(
        EVIDENCE_DIR, campaign_response, action_response, validation_result
    )

    # Final result
    print(f"\n{'=' * 60}")
    if validation_result["validation_passed"]:
        print("✅ SMOKE TEST PASSED: Code execution verified for dice rolls")
        print(f"   Evidence: {evidence_path}")
        return True
    print("❌ SMOKE TEST FAILED: Code execution NOT verified")
    print(f"   Errors: {validation_result['errors']}")
    print(f"   Evidence: {evidence_path}")
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Dice code execution smoke test")
    parser.add_argument(
        "--server-url",
        default=DEFAULT_SERVER_URL,
        help=f"Server URL (default: {DEFAULT_SERVER_URL})",
    )
    args = parser.parse_args()

    success = run_smoke_test(args.server_url)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
