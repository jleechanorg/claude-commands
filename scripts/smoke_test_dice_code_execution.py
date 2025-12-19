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
import time
from datetime import datetime
from pathlib import Path

import requests

# Test configuration
DEFAULT_SERVER_URL = "http://localhost:8081"
TEST_USER_EMAIL = "jleechan@gmail.com"  # Use existing test user
EVIDENCE_DIR = Path("/tmp/worldarchitect.ai/dice_code_execution_tests")


def get_auth_headers(server_url: str) -> dict:
    """Get auth headers for test user.

    Uses X-Test-Bypass-Auth header for TESTING mode.
    """
    return {
        "Content-Type": "application/json",
        "X-Test-Bypass-Auth": "true",
        "X-Test-User-ID": TEST_USER_EMAIL,
    }


def create_test_campaign(server_url: str) -> dict:
    """Create a test campaign that will trigger dice rolls."""
    headers = get_auth_headers(server_url)

    # Campaign setup that encourages dice rolls - character must be a string
    payload = {
        "title": f"Dice Code Execution Test - {datetime.now().isoformat()}",
        "character": "TestFighter, a level 5 Human Fighter with 16 STR, 14 DEX, 15 CON",
        "setting": "generic_fantasy",
        "description": "A combat-focused test to verify dice code execution. Start in a dungeon facing a goblin.",
    }

    response = requests.post(
        f"{server_url}/api/campaigns",
        json=payload,
        headers=headers,
        timeout=120,
    )

    if response.status_code not in (200, 201):
        print(f"❌ Failed to create campaign: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        return {}

    return response.json()


def trigger_dice_roll_action(server_url: str, campaign_id: str) -> dict:
    """Send a player action that should trigger dice rolls."""
    headers = get_auth_headers(server_url)

    # Action that MUST trigger dice rolls (combat/skill check)
    # Note: main.py API expects "input" field, not "user_input"
    payload = {
        "input": "I attack the goblin with my longsword. Roll to hit and damage.",
    }

    print(f"📤 Sending action: {payload['input']}")

    response = requests.post(
        f"{server_url}/api/campaigns/{campaign_id}/interaction",
        json=payload,
        headers=headers,
        timeout=180,  # LLM calls can be slow
    )

    if response.status_code != 200:
        print(f"❌ Failed to continue game: {response.status_code}")
        print(f"Response: {response.text[:500]}")
        return {}

    return response.json()


def validate_code_execution(response_data: dict) -> dict:
    """Validate that code_execution was actually used for dice rolls."""
    result = {
        "timestamp": datetime.now().isoformat(),
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
        result["has_dice_rolls"] = True
        result["dice_rolls"] = dice_rolls
        print(f"🎲 Found dice_rolls: {dice_rolls}")

    # Check for dice_audit_events
    audit_events = response_data.get("dice_audit_events", [])
    if audit_events:
        result["dice_audit_events"] = audit_events
        print(f"📋 Found dice_audit_events: {len(audit_events)} events")

    # Check debug_info for code_execution evidence
    # The evidence might be in the game_state or nested response
    debug_info = response_data.get("debug_info", {})

    # Also check nested structures
    if not debug_info:
        game_state = response_data.get("game_state", {})
        debug_info = game_state.get("debug_info", {})

    # Check story entries for debug info
    story = response_data.get("story", [])
    for entry in story:
        if entry.get("actor") == "gemini":
            entry_debug = entry.get("debug_info", {})
            if entry_debug:
                debug_info = entry_debug
                break

    if debug_info:
        result["code_execution_used"] = debug_info.get("code_execution_used", False)
        result["executable_code_parts"] = debug_info.get("executable_code_parts", 0)
        result["code_execution_result_parts"] = debug_info.get(
            "code_execution_result_parts", 0
        )

        print(f"🔍 Debug info found:")
        print(f"   code_execution_used: {result['code_execution_used']}")
        print(f"   executable_code_parts: {result['executable_code_parts']}")
        print(f"   code_execution_result_parts: {result['code_execution_result_parts']}")

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
            print("🚨 VALIDATION FAILED: Dice rolls were FABRICATED (no code execution)")
    else:
        result["errors"].append("No dice_rolls found in response")
        print("⚠️ WARNING: No dice rolls found - test inconclusive")

    return result


def save_evidence(
    evidence_dir: Path,
    campaign_response: dict,
    action_response: dict,
    validation_result: dict,
) -> Path:
    """Save all evidence to the specified directory."""
    evidence_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
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
    print(f"\n{'='*60}")
    print("🧪 DICE CODE EXECUTION SMOKE TEST")
    print(f"{'='*60}")
    print(f"Server: {server_url}")
    print(f"Time: {datetime.now().isoformat()}")
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

    # Step 4: Validate code execution
    print("\n🔍 Validating code execution...")
    validation_result = validate_code_execution(action_response)

    # Step 5: Save evidence
    evidence_path = save_evidence(
        EVIDENCE_DIR, campaign_response, action_response, validation_result
    )

    # Final result
    print(f"\n{'='*60}")
    if validation_result["validation_passed"]:
        print("✅ SMOKE TEST PASSED: Code execution verified for dice rolls")
        print(f"   Evidence: {evidence_path}")
        return True
    else:
        print("❌ SMOKE TEST FAILED: Code execution NOT verified")
        print(f"   Errors: {validation_result['errors']}")
        print(f"   Evidence: {evidence_path}")
        return False


def main():
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
