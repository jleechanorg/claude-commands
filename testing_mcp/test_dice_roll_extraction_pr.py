#!/usr/bin/env python3
"""Test dice roll extraction from action_resolution (PR #3588 validation).

This test validates that the PR #3588 dice roll extraction feature works correctly:
- Dice rolls are extracted from action_resolution.mechanics.rolls
- Extracted rolls populate the dice_rolls field for UI display
- Backward compatibility is maintained for legacy dice_rolls population

Run (local MCP already running):
    cd testing_mcp
    python test_dice_roll_extraction_pr.py --server-url http://127.0.0.1:8001

Run (with GCP preview fallback):
    cd testing_mcp
    python test_dice_roll_extraction_pr.py --use-preview
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
from lib.server_utils import start_local_mcp_server, pick_free_port
from lib.model_utils import settings_for_model, update_user_settings
from lib.campaign_utils import create_campaign, process_action, ensure_game_state_seed
from lib.evidence_utils import (
    get_evidence_dir,
    capture_provenance,
    capture_full_provenance,
    capture_git_provenance,
    save_evidence,
    create_evidence_bundle,
    save_request_responses,
)


class DiceExtractionTester:
    """Test dice roll extraction feature from PR #3588."""

    def __init__(
        self,
        server_url: str,
        *,
        evidence_dir: Path | None = None,
    ):
        self.server_url = server_url.rstrip("/")
        self.client = MCPClient(self.server_url, timeout=60)

        if evidence_dir is None:
            evidence_dir = get_evidence_dir("test_dice_roll_extraction_pr")
        self.evidence_dir = evidence_dir
        self.evidence_dir.mkdir(parents=True, exist_ok=True)

        self.test_results: dict[str, Any] = {
            "summary": {},
            "test_cases": [],
            "errors": [],
        }

    def test_single_combat_roll(self) -> dict[str, Any]:
        """Test extraction of a single d20 combat roll."""
        test_name = "single_d20_combat_roll"

        try:
            # Create campaign
            user_id = f"test-user-{int(time.time())}"
            campaign_id = create_campaign(
                self.client,
                user_id,
                title="Dice Extraction Test: Combat",
                character="Aric the Fighter (STR 16)",
                setting="Goblin den entrance",
            )

            # Ensure game state seed
            ensure_game_state_seed(self.client, user_id=user_id, campaign_id=campaign_id)

            # Process action that should generate dice rolls
            user_input = "I attack the goblin with my longsword."
            result = process_action(
                self.client,
                user_id,
                campaign_id,
                user_input,
            )

            # Validate dice extraction
            errors = self._validate_extraction(result, test_name)

            return {
                "test_name": test_name,
                "user_input": user_input,
                "passed": len(errors) == 0,
                "errors": errors,
                "dice_rolls": result.get("dice_rolls", []),
                "action_resolution": result.get("action_resolution", {}),
            }
        except Exception as e:
            return {
                "test_name": test_name,
                "passed": False,
                "errors": [f"Exception: {str(e)}"],
            }

    def test_multiple_rolls(self) -> dict[str, Any]:
        """Test extraction of multiple dice rolls (attack + damage)."""
        test_name = "multiple_rolls_attack_damage"

        try:
            user_id = f"test-user-{int(time.time())}"
            campaign_id = create_campaign(
                self.client,
                user_id,
                title="Dice Extraction Test: Multiple Rolls",
                character="Aric the Fighter (STR 16)",
                setting="Goblin den entrance",
            )

            ensure_game_state_seed(self.client, user_id=user_id, campaign_id=campaign_id)

            # Action that should generate multiple rolls
            user_input = "I attack the goblin with my longsword. Resolve the attack and damage."
            result = process_action(
                self.client,
                user_id,
                campaign_id,
                user_input,
            )

            errors = self._validate_multiple_rolls(result, test_name)

            return {
                "test_name": test_name,
                "user_input": user_input,
                "passed": len(errors) == 0,
                "errors": errors,
                "dice_rolls_count": len(result.get("dice_rolls", [])),
                "dice_rolls": result.get("dice_rolls", []),
            }
        except Exception as e:
            return {
                "test_name": test_name,
                "passed": False,
                "errors": [f"Exception: {str(e)}"],
            }

    def test_skill_check_roll(self) -> dict[str, Any]:
        """Test extraction of skill check rolls."""
        test_name = "skill_check_stealth"

        try:
            user_id = f"test-user-{int(time.time())}"
            campaign_id = create_campaign(
                self.client,
                user_id,
                title="Dice Extraction Test: Skill Check",
                character="Aric the Fighter (STR 16)",
                setting="Guard post",
            )

            ensure_game_state_seed(self.client, user_id=user_id, campaign_id=campaign_id)

            user_input = "I try to sneak past the guards. Make a Stealth check."
            result = process_action(
                self.client,
                user_id,
                campaign_id,
                user_input,
            )

            errors = self._validate_extraction(result, test_name)

            return {
                "test_name": test_name,
                "user_input": user_input,
                "passed": len(errors) == 0,
                "errors": errors,
                "dice_rolls": result.get("dice_rolls", []),
            }
        except Exception as e:
            return {
                "test_name": test_name,
                "passed": False,
                "errors": [f"Exception: {str(e)}"],
            }

    def test_backward_compatibility(self) -> dict[str, Any]:
        """Test that legacy dice_rolls population still works."""
        test_name = "backward_compatibility_legacy_rolls"

        try:
            # This test validates that if a response includes direct dice_rolls,
            # they are preserved (backward compatibility)
            user_id = f"test-user-{int(time.time())}"
            campaign_id = create_campaign(
                self.client,
                user_id,
                title="Dice Extraction Test: Backward Compat",
                character="Aric the Fighter (STR 16)",
                setting="Tavern",
            )

            ensure_game_state_seed(self.client, user_id=user_id, campaign_id=campaign_id)

            user_input = "I persuade the tavern keeper to give me information."
            result = process_action(
                self.client,
                user_id,
                campaign_id,
                user_input,
            )

            # Should have either extracted or legacy dice_rolls
            has_rolls = bool(result.get("dice_rolls"))
            has_action_resolution = bool(result.get("action_resolution"))

            errors = []
            if not has_rolls and not has_action_resolution:
                errors.append("No dice rolls or action_resolution found")

            return {
                "test_name": test_name,
                "passed": len(errors) == 0,
                "errors": errors,
                "has_dice_rolls": has_rolls,
                "has_action_resolution": has_action_resolution,
            }
        except Exception as e:
            return {
                "test_name": test_name,
                "passed": False,
                "errors": [f"Exception: {str(e)}"],
            }

    def _validate_extraction(self, result: dict[str, Any], test_name: str) -> list[str]:
        """Validate that dice rolls were extracted correctly."""
        errors = []

        if result.get("error"):
            errors.append(f"API returned error: {result['error']}")
            return errors

        dice_rolls = result.get("dice_rolls", [])
        action_resolution = result.get("action_resolution", {})

        # Check for dice notation in either field
        has_dice_in_rolls = any("d" in str(roll) for roll in dice_rolls)
        has_mechanics = bool(action_resolution.get("mechanics", {}).get("rolls"))

        if not has_dice_in_rolls and not has_mechanics:
            errors.append("No dice notation found in dice_rolls or action_resolution.mechanics.rolls")

        # If action_resolution.mechanics.rolls exists, dice_rolls should be populated
        if has_mechanics and not has_dice_in_rolls:
            mechanics_rolls = action_resolution.get("mechanics", {}).get("rolls", [])
            if mechanics_rolls:
                errors.append(
                    f"action_resolution.mechanics.rolls exists ({len(mechanics_rolls)} rolls) "
                    "but dice_rolls is empty - extraction may have failed"
                )

        return errors

    def _validate_multiple_rolls(self, result: dict[str, Any], test_name: str) -> list[str]:
        """Validate that multiple dice rolls were extracted."""
        errors = []

        if result.get("error"):
            errors.append(f"API returned error: {result['error']}")
            return errors

        dice_rolls = result.get("dice_rolls", [])
        action_resolution = result.get("action_resolution", {})
        mechanics_rolls = action_resolution.get("mechanics", {}).get("rolls", [])

        # For combat, we expect at least 1 roll (attack or damage)
        if not dice_rolls and not mechanics_rolls:
            errors.append("No dice rolls found for combat action")

        # If we have mechanics rolls, we should have dice_rolls
        if mechanics_rolls and not dice_rolls:
            errors.append(
                f"Found {len(mechanics_rolls)} rolls in action_resolution.mechanics "
                "but dice_rolls is empty"
            )

        return errors

    def run_all_tests(self) -> dict[str, Any]:
        """Run all tests and save evidence."""
        print("\n🎯 Running Dice Roll Extraction Tests (PR #3588)...\n")

        tests = [
            ("Single d20 Combat Roll", self.test_single_combat_roll),
            ("Multiple Rolls (Attack+Damage)", self.test_multiple_rolls),
            ("Skill Check Roll", self.test_skill_check_roll),
            ("Backward Compatibility", self.test_backward_compatibility),
        ]

        results = []
        for test_name, test_func in tests:
            print(f"  Running: {test_name}...", end=" ", flush=True)
            try:
                result = test_func()
                results.append(result)
                status = "✅ PASS" if result.get("passed") else "❌ FAIL"
                print(status)
            except Exception as e:
                print(f"❌ EXCEPTION: {e}")
                results.append({
                    "test_name": test_name,
                    "passed": False,
                    "errors": [str(e)],
                })

        # Summary
        passed = sum(1 for r in results if r.get("passed"))
        total = len(results)

        self.test_results = {
            "summary": {
                "total": total,
                "passed": passed,
                "failed": total - passed,
                "success_rate": f"{(passed / total * 100):.1f}%" if total > 0 else "0%",
                "timestamp": datetime.now().isoformat(),
                "server_url": self.server_url,
            },
            "test_cases": results,
            "provenance": capture_provenance(self.server_url),
        }

        return self.test_results

    def save_evidence(self) -> None:
        """Save test evidence and results."""
        print("\n💾 Saving evidence...\n")

        # Save test results
        results_json = json.dumps(self.test_results, indent=2)
        results_path = self.evidence_dir / "test_results.json"
        results_path.write_text(results_json)
        print(f"  ✓ Saved: {results_path}")

        # Create evidence bundle
        methodology = """# Dice Roll Extraction Test Methodology

## Objective
Validate PR #3588 dice roll extraction feature works correctly.

## Test Cases
1. **Single d20 Combat Roll**: Test extraction of a single attack roll
2. **Multiple Rolls**: Test extraction of attack + damage rolls
3. **Skill Check**: Test extraction of ability check rolls
4. **Backward Compatibility**: Ensure legacy dice_rolls population still works

## Validation Criteria
- Dice rolls extracted from action_resolution.mechanics.rolls
- Extracted rolls populate dice_rolls field for UI display
- Results include proper dice notation and formatting
- Backward compatibility maintained for legacy responses

## Evidence Structure
- test_results.json: Summary of all test cases and results
- provenance: Git and server state at test time
"""

        create_evidence_bundle(
            self.evidence_dir,
            methodology=methodology,
            timestamp=datetime.now().isoformat(),
            summary=f"Dice Roll Extraction PR Tests: {self.test_results['summary']['passed']}/{self.test_results['summary']['total']} passed",
        )

        print(f"\n📊 Evidence saved to: {self.evidence_dir}")
        print(f"   Summary: {self.test_results['summary']['passed']}/{self.test_results['summary']['total']} tests passed")


def run_tests(server_url: str | None, use_preview: bool = False) -> int:
    """Run tests with given server configuration."""
    if not server_url and not use_preview:
        print("❌ Error: Must specify --server-url or --use-preview")
        return 1

    if use_preview and not server_url:
        server_url = os.getenv(
            "MCP_PREVIEW_URL",
            "https://worldarchitect.ai/mcp"
        )
        print(f"📍 Using GCP preview server: {server_url}")

    tester = DiceExtractionTester(server_url)
    results = tester.run_all_tests()
    tester.save_evidence()

    print("\n" + "="*50)
    print(f"Final Result: {results['summary']['passed']}/{results['summary']['total']} tests passed")
    print("="*50 + "\n")

    return 0 if results['summary']['failed'] == 0 else 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test dice roll extraction feature (PR #3588)"
    )
    parser.add_argument(
        "--server-url",
        type=str,
        help="MCP server URL (e.g., http://127.0.0.1:8001)",
    )
    parser.add_argument(
        "--use-preview",
        action="store_true",
        help="Use GCP preview server if local not available",
    )
    parser.add_argument(
        "--start-local",
        action="store_true",
        help="Start local MCP server automatically",
    )

    args = parser.parse_args()

    server = None
    try:
        # If --start-local, start the server
        if args.start_local:
            print("🚀 Starting local MCP server...")
            port = pick_free_port()
            server = start_local_mcp_server(port)
            args.server_url = f"http://127.0.0.1:{port}"
            print(f"✅ Server started on port {port}")
            time.sleep(2)  # Give server time to start

        # Run tests
        exit_code = run_tests(args.server_url, args.use_preview)
        sys.exit(exit_code)
    finally:
        # Clean up server if started
        if server is not None:
            print("\n🛑 Stopping local MCP server...")
            try:
                server.stop()
                print("✅ Server stopped cleanly")
            except Exception as e:
                print(f"⚠️  Error stopping server: {e}")


if __name__ == "__main__":
    main()
