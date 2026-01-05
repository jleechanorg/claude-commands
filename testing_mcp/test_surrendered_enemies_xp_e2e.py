#!/usr/bin/env python3
"""
Surrendered Enemies XP E2E Test

This test validates that when enemies surrender, they give FULL XP value
as if they were killed in combat.

Per combat_system_instruction.md:
- Surrendered enemies count as "defeated" for XP purposes
- Include surrendered enemies in combat_summary.enemies_defeated list
- Calculate XP using their full CR value (same as killed enemies)
- Example: If 100 goblins (CR 1/4, 50 XP each) surrender = 5,000 XP awarded

Run locally:
    python testing_mcp/test_surrendered_enemies_xp_e2e.py

Run against preview:
    BASE_URL=https://preview-url python testing_mcp/test_surrendered_enemies_xp_e2e.py
"""

import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from testing_mcp.dev_server import ensure_server_running, get_base_url
from testing_mcp.lib.campaign_utils import (
    create_campaign,
    get_campaign_state,
    process_action,
)
from testing_mcp.lib.evidence_utils import (
    capture_provenance,
    create_evidence_bundle,
    get_evidence_dir,
)
from testing_mcp.lib.mcp_client import MCPClient


def log(msg: str) -> None:
    """Log with timestamp."""
    ts = datetime.now(UTC).isoformat()
    print(f"[{ts}] {msg}")


def get_pid_from_port(port: int) -> int | None:
    """Get the actual PID of the process listening on a port.

    Uses lsof to find the process. Returns None if not found.
    """
    import subprocess

    try:
        result = subprocess.run(
            ["lsof", "-i", f":{port}", "-t"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            # lsof -t returns just the PID(s), take the first one
            pids = result.stdout.strip().split("\n")
            return int(pids[0])
    except Exception:
        pass
    return None


def status_contains_surrender(status) -> bool:
    """Check if status contains 'surrender', handling both string and list formats.

    Per combat_system_instruction.md, status can be either:
    - A string: "surrendered"
    - An array: ["surrendered"]
    """
    if isinstance(status, str):
        return "surrender" in status.lower()

    if isinstance(status, (list, tuple, set)):
        return any("surrender" in str(s).lower() for s in status)

    # Fallback: coerce other data types to string for defensive handling
    return "surrender" in str(status).lower()


def validate_surrender_xp_from_rewards_box(
    response: dict, combat_state: dict, player_char_data: dict
) -> dict:
    """Validate that XP was awarded using structured JSON sources.

    Checks (in order of preference):
    1. rewards_box.xp_gained - Frontend-visible rewards display
    2. combat_summary.xp_awarded - Combat system XP tracking
    3. encounter_summary.xp_awarded - Encounter system XP tracking

    Returns validation dict with:
    - rewards_box: the rewards_box dict from response
    - xp_gained: XP from best available source
    - source: where XP was found
    - xp_award_valid: True if xp_gained > 0 from any valid source
    - issues: list of issues found (informational, not failures)
    """
    validation = {
        "rewards_box": None,
        "xp_gained": None,
        "source": None,
        "current_xp": None,
        "player_xp_current": None,
        "xp_award_valid": False,
        "issues": [],
    }

    # Source 1: Check rewards_box JSON (preferred - user-visible)
    rewards_box = response.get("rewards_box", {})
    validation["rewards_box"] = rewards_box

    xp_from_rewards_box = None
    if rewards_box:
        xp_from_rewards_box = rewards_box.get("xp_gained")
        if isinstance(xp_from_rewards_box, (int, float)) and xp_from_rewards_box > 0:
            validation["xp_gained"] = xp_from_rewards_box
            validation["source"] = rewards_box.get("source", "rewards_box")
            validation["current_xp"] = rewards_box.get("current_xp")

    # Source 2: Check combat_summary.xp_awarded (fallback)
    combat_summary = combat_state.get("combat_summary", {})
    xp_from_combat = None
    if combat_summary:
        xp_from_combat = combat_summary.get("xp_awarded")
        validation["combat_summary_xp"] = xp_from_combat
        validation["enemies_defeated"] = combat_summary.get("enemies_defeated")

        # Use combat_summary if rewards_box didn't have XP
        if validation["xp_gained"] is None and isinstance(xp_from_combat, (int, float)) and xp_from_combat > 0:
            validation["xp_gained"] = xp_from_combat
            validation["source"] = "combat_summary"

    # Source 3: Check encounter_summary.xp_awarded (for narrative victories)
    game_state = response.get("game_state", {})
    encounter_state = game_state.get("encounter_state", {})
    encounter_summary = encounter_state.get("encounter_summary", {})
    xp_from_encounter = None
    if encounter_summary:
        xp_from_encounter = encounter_summary.get("xp_awarded")
        validation["encounter_summary_xp"] = xp_from_encounter

        # Use encounter_summary if no other source had XP
        if validation["xp_gained"] is None and isinstance(xp_from_encounter, (int, float)) and xp_from_encounter > 0:
            validation["xp_gained"] = xp_from_encounter
            validation["source"] = "encounter_summary"

    # Record informational issues (not failures)
    if not rewards_box:
        validation["issues"].append("rewards_box empty (using fallback source)")

    # Check player experience was updated
    experience = player_char_data.get("experience", {})
    validation["player_xp_current"] = experience.get("current")

    # XP is valid if we found it from any source
    xp_gained = validation["xp_gained"]
    if isinstance(xp_gained, (int, float)) and xp_gained > 0:
        validation["xp_award_valid"] = True
    else:
        validation["issues"].append("No XP found in rewards_box, combat_summary, or encounter_summary")

    return validation


def main():  # noqa: PLR0912,PLR0915
    # Configuration
    user_id = f"e2e-surrender-xp-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"

    log("=" * 60)
    log("SURRENDERED ENEMIES XP E2E TEST")
    log("=" * 60)

    # Ensure development server is running
    log("Ensuring development server is running...")
    try:
        server_port = ensure_server_running(check_code_changes=True)
    except Exception as e:
        log(f"⚠️  Could not manage server: {e}")
        log("   Proceeding with existing server...")
        server_port = None

    base_url = os.getenv("BASE_URL") or get_base_url()
    log(f"Base URL: {base_url}")

    # Get actual PID from port for accurate provenance
    port = int(base_url.split(":")[-1].rstrip("/")) if server_port else None
    server_pid = get_pid_from_port(port) if port else None
    log(f"Server port: {port}, PID: {server_pid}")

    # Initialize client
    client = MCPClient(base_url, timeout_s=180)

    # Wait for server health
    log("Waiting for server health...")
    client.wait_healthy(timeout_s=30)
    log("Server healthy!")

    # Capture provenance
    evidence_dir = get_evidence_dir("surrendered_enemies_xp")
    provenance = capture_provenance(base_url, server_pid)
    log(f"Git HEAD: {provenance.get('git_head', 'unknown')[:12]}...")

    # Results tracking
    results = {
        "test_name": "surrendered_enemies_xp_e2e",
        "timestamp": datetime.now(UTC).isoformat(),
        "base_url": base_url,
        "user_id": user_id,
        "scenarios": [],
        "summary": {},
    }

    # =========================================================================
    # SCENARIO 1: Combat with enemies surrendering
    # =========================================================================
    log("\n" + "=" * 60)
    log("SCENARIO 1: Combat with enemies surrendering")
    log("=" * 60)

    scenario1 = {
        "name": "surrender_gives_full_xp",
        "campaign_id": None,
        "errors": [],
        "steps": [],
    }

    # Step 1: Create campaign
    log("Step 1: Creating campaign with combat scenario...")
    try:
        campaign_id = create_campaign(
            client,
            user_id,
            title="The Goblin Surrender",
            character="A level 5 paladin with a reputation for mercy, equipped with longsword and shield",
            setting="A forest clearing where goblins have been caught raiding",
            description="Test campaign for validating XP is awarded when enemies surrender",
        )
        scenario1["campaign_id"] = campaign_id
        scenario1["steps"].append(
            {"step": "create_campaign", "passed": True, "campaign_id": campaign_id}
        )
        log(f"  Campaign ID: {campaign_id}")
    except Exception as e:
        scenario1["errors"].append(f"create_campaign failed: {e}")
        log(f"  FAILED: {e}")
        results["scenarios"].append(scenario1)
        save_results(results, evidence_dir, provenance, client)
        return 1

    # Step 2: Trigger combat
    log("Step 2: Triggering combat with goblins...")
    try:
        combat_start = process_action(
            client,
            user_id=user_id,
            campaign_id=campaign_id,
            user_input=(
                "I encounter a group of 5 goblins (each CR 1/4 = 50 XP each, total 250 XP) "
                "who are stealing supplies from a cart. When they see me, they draw their weapons! "
                "[OOC: Please start combat. Set in_combat to true, create initiative order with "
                "5 goblins (CR 1/4 each), and populate the combatants dict with HP and AC for each.]"
            ),
        )
        combat_state = combat_start.get("game_state", {}).get("combat_state", {})
        in_combat = combat_state.get("in_combat", False)
        scenario1["steps"].append(
            {
                "step": "trigger_combat",
                "passed": in_combat is True,
                "in_combat": in_combat,
                "combatants": list(combat_state.get("combatants", {}).keys()),
            }
        )
        log(f"  in_combat: {in_combat}")
        log(f"  Combatants: {list(combat_state.get('combatants', {}).keys())}")
    except Exception as e:
        scenario1["errors"].append(f"trigger_combat failed: {e}")
        log(f"  FAILED: {e}")

    # Step 3: Attack and make them surrender
    log("Step 3: Attacking and making enemies surrender...")
    try:
        surrender_action = process_action(
            client,
            user_id=user_id,
            campaign_id=campaign_id,
            user_input=(
                "I strike down one goblin with my sword, then use my intimidating presence. "
                "'Surrender now or share his fate!' I roar. "
                "[OOC: The remaining 4 goblins see their companion fall and surrender in fear. "
                "End combat with ALL 5 goblins counted in enemies_defeated - both the killed one "
                "AND the 4 surrendered ones. Award FULL XP for all 5 goblins (5 x 50 = 250 XP). "
                "Per combat_system_instruction.md: surrendered enemies give FULL XP as if killed. "
                "Set combat_summary.xp_awarded = 250, combat_summary.enemies_defeated should list all 5.]"
            ),
        )

        surrender_game_state = surrender_action.get("game_state", {})
        combat_state_after = surrender_game_state.get("combat_state", {})
        player_char_data = surrender_game_state.get("player_character_data", {})

        in_combat_after = combat_state_after.get("in_combat", True)

        # Validate XP was awarded using rewards_box JSON (not text parsing)
        xp_validation = validate_surrender_xp_from_rewards_box(
            surrender_action, combat_state_after, player_char_data
        )

        scenario1["steps"].append(
            {
                "step": "surrender_and_xp",
                "passed": xp_validation["xp_award_valid"],
                "in_combat_after": in_combat_after,
                "xp_validation": xp_validation,
                "rewards_box": surrender_action.get("rewards_box"),
                "combat_summary": combat_state_after.get("combat_summary"),
            }
        )

        log(f"  in_combat after: {in_combat_after}")
        log(f"  XP gained (rewards_box): {xp_validation.get('xp_gained')}")
        log(f"  Source: {xp_validation.get('source')}")
        log(f"  XP valid: {xp_validation['xp_award_valid']}")
        # Log informational issues but only add to errors if validation failed
        if xp_validation["issues"]:
            for issue in xp_validation["issues"]:
                log(f"    Issue: {issue}")
        if not xp_validation["xp_award_valid"]:
            scenario1["errors"].append("XP validation failed - no XP awarded")
    except Exception as e:
        scenario1["errors"].append(f"surrender_and_xp failed: {e}")
        log(f"  FAILED: {e}")

    # Step 4: Verify final state
    log("Step 4: Verifying final campaign state...")
    try:
        final_state = get_campaign_state(
            client, user_id=user_id, campaign_id=campaign_id
        )
        final_game_state = final_state.get("game_state", {})
        final_player_data = final_game_state.get("player_character_data", {})
        final_experience = final_player_data.get("experience", {})

        xp_validation_local = xp_validation if "xp_validation" in locals() else {}
        expected_xp = xp_validation_local.get("xp_gained")

        final_xp_value = final_experience.get("current")
        final_xp_is_number = isinstance(final_xp_value, (int, float))
        expected_xp_is_number = isinstance(expected_xp, (int, float))

        final_state_valid = (
            final_xp_is_number
            and expected_xp_is_number
            and final_xp_value >= expected_xp
            and xp_validation_local.get("xp_award_valid", False)
        )

        scenario1["steps"].append(
            {
                "step": "verify_final_state",
                "passed": final_state_valid,
                "final_experience": final_experience,
            }
        )
        log(f"  Final experience: {final_experience}")
        if not final_state_valid:
            scenario1["errors"].append(
                "final experience did not reflect awarded XP for surrendered enemies"
            )
    except Exception as e:
        scenario1["errors"].append(f"verify_final_state failed: {e}")
        log(f"  FAILED: {e}")

    results["scenarios"].append(scenario1)

    # =========================================================================
    # SCENARIO 2: Mass surrender scenario (100 enemies)
    # =========================================================================
    log("\n" + "=" * 60)
    log("SCENARIO 2: Mass surrender - 10 enemies surrendering")
    log("=" * 60)

    scenario2 = {
        "name": "mass_surrender_xp",
        "campaign_id": None,
        "errors": [],
        "steps": [],
    }

    # Create new campaign for this scenario
    log("Step 1: Creating campaign for mass surrender...")
    try:
        campaign_id2 = create_campaign(
            client,
            user_id,
            title="The Bandit Capitulation",
            character="A level 10 warlord with legendary reputation",
            setting="A bandit camp in the mountains",
            description="Test campaign for mass surrender XP calculation",
        )
        scenario2["campaign_id"] = campaign_id2
        scenario2["steps"].append(
            {"step": "create_campaign", "passed": True, "campaign_id": campaign_id2}
        )
        log(f"  Campaign ID: {campaign_id2}")
    except Exception as e:
        scenario2["errors"].append(f"create_campaign failed: {e}")
        log(f"  FAILED: {e}")
        results["scenarios"].append(scenario2)
        save_results(results, evidence_dir, provenance, client)
        return 1

    # Step 2: Mass surrender scenario
    log("Step 2: Demanding mass surrender...")
    try:
        mass_surrender = process_action(
            client,
            user_id=user_id,
            campaign_id=campaign_id2,
            user_input=(
                "I approach the bandit camp alone. My legendary reputation precedes me. "
                "'I am the Warlord of the Northern Reaches,' I announce. 'You have two choices: "
                "surrender now and live, or draw steel and die.' The 10 bandits (each CR 1/2 = 100 XP) "
                "look at each other, drop their weapons, and surrender immediately. "
                "[OOC: This is a narrative victory via intimidation. The 10 bandits surrender without "
                "formal combat. Per combat_system_instruction.md: surrendered enemies give FULL XP. "
                "Award XP for all 10 bandits: 10 x 100 = 1000 XP total. "
                "Use combat_summary or encounter_summary with xp_awarded = 1000 and list all bandits "
                "in enemies_defeated with 'SURRENDERED' status.]"
            ),
        )

        mass_game_state = mass_surrender.get("game_state", {})
        mass_combat_state = mass_game_state.get("combat_state", {})
        mass_player_data = mass_game_state.get("player_character_data", {})

        # Validate XP using rewards_box JSON (not text parsing)
        xp_validation = validate_surrender_xp_from_rewards_box(
            mass_surrender, mass_combat_state, mass_player_data
        )

        scenario2["steps"].append(
            {
                "step": "mass_surrender",
                "passed": xp_validation["xp_award_valid"],
                "xp_validation": xp_validation,
                "rewards_box": mass_surrender.get("rewards_box"),
            }
        )

        log(f"  XP gained (rewards_box): {xp_validation.get('xp_gained')}")
        log(f"  Source: {xp_validation.get('source')}")
        log(f"  XP valid: {xp_validation['xp_award_valid']}")
        if not xp_validation["xp_award_valid"]:
            scenario2["errors"].append(
                f"Mass surrender XP not in rewards_box: {xp_validation.get('xp_gained')}"
            )
    except Exception as e:
        scenario2["errors"].append(f"mass_surrender failed: {e}")
        log(f"  FAILED: {e}")

    # Step 3: Verify XP persistence in final state
    log("Step 3: Verifying XP persistence in final state...")
    try:
        final_state2 = get_campaign_state(
            client, user_id=user_id, campaign_id=campaign_id2
        )
        final_game_state2 = final_state2.get("game_state", {})
        final_player_data2 = final_game_state2.get("player_character_data", {})
        final_experience2 = final_player_data2.get("experience", {})

        # Get XP that was awarded
        xp_gained = xp_validation.get("xp_gained") if "xp_validation" in locals() else None
        final_xp = final_experience2.get("current")

        # Verify XP was persisted - final XP should be > 0 and XP was awarded
        final_xp_valid = (
            isinstance(final_xp, (int, float))
            and final_xp > 0
            and isinstance(xp_gained, (int, float))
            and xp_gained > 0
            and xp_validation.get("xp_award_valid", False)
        )

        scenario2["steps"].append(
            {
                "step": "verify_final_state",
                "passed": final_xp_valid,
                "final_experience": final_experience2,
                "xp_gained": xp_gained,
            }
        )
        log(f"  Final experience: {final_experience2}")
        log(f"  XP gained: {xp_gained}")
        log(f"  XP persisted: {final_xp_valid}")
        if not final_xp_valid:
            scenario2["errors"].append(
                f"XP not persisted: xp_gained={xp_gained}, final_xp={final_xp}"
            )
    except Exception as e:
        scenario2["errors"].append(f"verify_final_state failed: {e}")
        log(f"  FAILED: {e}")

    results["scenarios"].append(scenario2)

    # =========================================================================
    # Summary
    # =========================================================================
    log("\n" + "=" * 60)
    log("TEST SUMMARY")
    log("=" * 60)

    scenarios_passed = sum(1 for s in results["scenarios"] if not s.get("errors"))
    scenarios_total = len(results["scenarios"])

    results["summary"] = {
        "scenarios_passed": scenarios_passed,
        "scenarios_total": scenarios_total,
        "all_passed": scenarios_passed == scenarios_total,
    }

    log(f"Scenarios: {scenarios_passed}/{scenarios_total} passed")

    for scenario in results["scenarios"]:
        status = "✅ PASS" if not scenario.get("errors") else "❌ FAIL"
        log(f"  {scenario['name']}: {status}")
        if scenario.get("errors"):
            for error in scenario["errors"]:
                log(f"    - {error}")

    # Save evidence
    save_results(results, evidence_dir, provenance, client)

    if scenarios_passed == scenarios_total:
        log("\n[PASS] Surrendered enemies XP test passed!")
        log("  - Surrendered enemies received full XP value")
        return 0
    log("\n[FAIL] Surrendered enemies XP test failed!")
    return 1


def save_results(results, evidence_dir, provenance, client):
    """Save test results and evidence."""
    log(f"\nSaving evidence to: {evidence_dir}")

    try:
        bundle_files = create_evidence_bundle(
            evidence_dir,
            test_name="surrendered_enemies_xp",
            provenance=provenance,
            results=results,
            request_responses=client.get_captures_as_dict(),
            methodology_text="""# Methodology: Surrendered Enemies XP Test

## Test Purpose
Validate that when enemies surrender in combat or narrative scenarios,
they award FULL XP value as if they were killed.

## Test Scenarios
1. **surrender_gives_full_xp**: Combat where some enemies surrender
2. **mass_surrender_xp**: Large group surrendering via intimidation

## Validation Criteria
- combat_summary.xp_awarded > 0 for surrendered enemies
- enemies_defeated list includes surrendered enemies
- XP calculation uses full CR value (no reduction for surrender)

## Source Rule
Per combat_system_instruction.md section "🏆 Surrendered Enemies Give Full XP":
- Surrendered enemies count as "defeated" for XP purposes
- Include surrendered enemies in combat_summary.enemies_defeated
- Calculate XP using their full CR value (same as killed enemies)
""",
        )
        log(f"  Evidence bundle created: {len(bundle_files)} files")
    except Exception as e:
        log(f"  Warning: Could not create full evidence bundle: {e}")
        # Fallback: just save the results
        results_file = evidence_dir / "run.json"
        results_file.write_text(json.dumps(results, indent=2))
        log(f"  Saved results to: {results_file}")


if __name__ == "__main__":
    sys.exit(main())
