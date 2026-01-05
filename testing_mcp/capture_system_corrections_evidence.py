#!/usr/bin/env python3
"""
Capture evidence of system_corrections discrepancy detection.

This script demonstrates the detection flow by:
1. Creating test state with rewards_processed=False (discrepancy)
2. Calling _detect_rewards_discrepancy() directly
3. Showing what system_corrections would be returned
4. Saving evidence bundle to /tmp

Run: python testing_mcp/capture_system_corrections_evidence.py
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the detection function
from mvp_site.world_logic import _detect_rewards_discrepancy


def log(msg: str) -> None:
    """Log with timestamp."""
    ts = datetime.now(timezone.utc).isoformat()
    print(f"[{ts}] {msg}")


def create_evidence_bundle(evidence_dir: Path, scenarios: list[dict]) -> None:
    """Save evidence to files."""
    evidence_dir.mkdir(parents=True, exist_ok=True)

    # Save scenarios
    scenarios_file = evidence_dir / "scenarios.json"
    with open(scenarios_file, "w") as f:
        json.dump(scenarios, f, indent=2, default=str)

    # Save summary
    summary_file = evidence_dir / "summary.md"
    with open(summary_file, "w") as f:
        f.write("# System Corrections Evidence Bundle\n\n")
        f.write(f"Generated: {datetime.now(timezone.utc).isoformat()}\n\n")
        f.write("## Purpose\n\n")
        f.write("This evidence demonstrates the `_detect_rewards_discrepancy()` function\n")
        f.write("detecting state discrepancies and generating `system_corrections` messages.\n\n")
        f.write("## Scenarios\n\n")

        for i, scenario in enumerate(scenarios, 1):
            f.write(f"### Scenario {i}: {scenario['name']}\n\n")
            f.write(f"**Input State:**\n```json\n{json.dumps(scenario['input_state'], indent=2)}\n```\n\n")
            f.write(f"**Expected Discrepancy:** {scenario['expected_discrepancy']}\n\n")
            f.write(f"**Actual Discrepancies:** {scenario['actual_discrepancies']}\n\n")
            f.write(f"**Result:** {'PASS' if scenario['passed'] else 'FAIL'}\n\n")
            f.write("---\n\n")


def run_evidence_capture() -> list[dict]:
    """Run scenarios and capture evidence."""
    scenarios = []

    # Scenario 1: Combat ended with rewards_processed=False (SHOULD DETECT)
    log("Scenario 1: Combat ended, rewards_processed=False")
    state1 = {
        "combat_state": {
            "in_combat": False,
            "combat_phase": "ended",
            "combat_summary": {
                "xp_awarded": 75,
                "enemies_defeated": ["goblin_001", "goblin_002"],
                "outcome": "victory",
            },
            "rewards_processed": False,  # BUG STATE
        },
        "player_character_data": {
            "experience": {"current": 500},
        },
    }

    discrepancies1 = _detect_rewards_discrepancy(state1)
    passed1 = len(discrepancies1) > 0 and any("REWARDS_STATE_ERROR" in d for d in discrepancies1)

    log(f"  Discrepancies found: {discrepancies1}")
    log(f"  Expected discrepancy: YES")
    log(f"  Result: {'PASS' if passed1 else 'FAIL'}")

    scenarios.append({
        "name": "Combat ended with rewards_processed=False",
        "input_state": state1,
        "expected_discrepancy": True,
        "actual_discrepancies": discrepancies1,
        "passed": passed1,
    })

    # Scenario 2: Combat ended with rewards_processed=True (SHOULD NOT DETECT)
    log("")
    log("Scenario 2: Combat ended, rewards_processed=True")
    state2 = {
        "combat_state": {
            "in_combat": False,
            "combat_phase": "ended",
            "combat_summary": {
                "xp_awarded": 75,
                "enemies_defeated": ["goblin_001"],
                "outcome": "victory",
            },
            "rewards_processed": True,  # CORRECT STATE
        },
    }

    discrepancies2 = _detect_rewards_discrepancy(state2)
    passed2 = len(discrepancies2) == 0

    log(f"  Discrepancies found: {discrepancies2}")
    log(f"  Expected discrepancy: NO")
    log(f"  Result: {'PASS' if passed2 else 'FAIL'}")

    scenarios.append({
        "name": "Combat ended with rewards_processed=True (no discrepancy)",
        "input_state": state2,
        "expected_discrepancy": False,
        "actual_discrepancies": discrepancies2,
        "passed": passed2,
    })

    # Scenario 3: Mid-combat (no discrepancy expected)
    log("")
    log("Scenario 3: Mid-combat (no discrepancy)")
    state3 = {
        "combat_state": {
            "in_combat": True,
            "combat_phase": "player_turn",
            "rewards_processed": False,
        },
    }

    discrepancies3 = _detect_rewards_discrepancy(state3)
    passed3 = len(discrepancies3) == 0

    log(f"  Discrepancies found: {discrepancies3}")
    log(f"  Expected discrepancy: NO")
    log(f"  Result: {'PASS' if passed3 else 'FAIL'}")

    scenarios.append({
        "name": "Mid-combat (no discrepancy expected)",
        "input_state": state3,
        "expected_discrepancy": False,
        "actual_discrepancies": discrepancies3,
        "passed": passed3,
    })

    # Scenario 4: Victory phase with rewards_processed=False
    log("")
    log("Scenario 4: Victory phase, rewards_processed=False")
    state4 = {
        "combat_state": {
            "in_combat": False,
            "combat_phase": "victory",
            "combat_summary": {
                "xp_awarded": 50,
                "outcome": "victory",
            },
            "rewards_processed": False,
        },
    }

    discrepancies4 = _detect_rewards_discrepancy(state4)
    passed4 = len(discrepancies4) > 0

    log(f"  Discrepancies found: {discrepancies4}")
    log(f"  Expected discrepancy: YES")
    log(f"  Result: {'PASS' if passed4 else 'FAIL'}")

    scenarios.append({
        "name": "Victory phase with rewards_processed=False",
        "input_state": state4,
        "expected_discrepancy": True,
        "actual_discrepancies": discrepancies4,
        "passed": passed4,
    })

    return scenarios


def main():
    log("=" * 70)
    log("SYSTEM CORRECTIONS EVIDENCE CAPTURE")
    log("=" * 70)
    log("")
    log("This demonstrates _detect_rewards_discrepancy() detecting state issues")
    log("and generating system_corrections messages for LLM self-correction.")
    log("")

    # Run scenarios
    scenarios = run_evidence_capture()

    # Calculate results
    total = len(scenarios)
    passed = sum(1 for s in scenarios if s["passed"])

    log("")
    log("=" * 70)
    log("RESULTS")
    log("=" * 70)
    log(f"Total scenarios: {total}")
    log(f"Passed: {passed}")
    log(f"Failed: {total - passed}")

    # Save evidence
    evidence_dir = Path("/tmp/system_corrections_evidence")
    create_evidence_bundle(evidence_dir, scenarios)
    log("")
    log(f"Evidence saved to: {evidence_dir}")
    log(f"  - scenarios.json: Raw scenario data")
    log(f"  - summary.md: Human-readable summary")

    # Show example of what system_corrections looks like in response
    log("")
    log("=" * 70)
    log("EXAMPLE: What system_corrections looks like in API response")
    log("=" * 70)

    example_response = {
        "narrative": "You catch your breath after the battle...",
        "state_updates": {
            "combat_state": {
                "combat_phase": "ended",
                "rewards_processed": False,  # LLM forgot to set this!
            }
        },
        "system_corrections": [
            "REWARDS_STATE_ERROR: Combat ended (phase=ended) with summary, "
            "but rewards_processed=False. You MUST set combat_state.rewards_processed=true."
        ],
    }

    log("Response JSON (showing system_corrections):")
    log(json.dumps(example_response, indent=2))

    log("")
    log("=" * 70)
    log("EXAMPLE: Next turn input includes system_corrections")
    log("=" * 70)

    example_input = {
        "current_input": "I check my inventory",
        "system_corrections": [
            "REWARDS_STATE_ERROR: Combat ended (phase=ended) with summary, "
            "but rewards_processed=False. You MUST set combat_state.rewards_processed=true."
        ],
        "game_state": {
            "combat_state": {
                "combat_phase": "ended",
                "rewards_processed": False,
            }
        }
    }

    log("Next turn LLM input (showing system_corrections):")
    log(json.dumps(example_input, indent=2))

    log("")
    log("The LLM reads system_corrections and MUST fix the state by setting")
    log("combat_state.rewards_processed=true in its response.")

    # Exit with appropriate code
    if passed == total:
        log("")
        log("ALL SCENARIOS PASSED")
        sys.exit(0)
    else:
        log("")
        log("SOME SCENARIOS FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
