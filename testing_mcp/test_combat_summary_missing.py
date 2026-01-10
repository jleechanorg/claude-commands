#!/usr/bin/env python3
"""
Reproduce Combat Summary Missing Bug - RED State Test

This test REPRODUCES the exact failure modes identified in research:
1. Combat ends with user saying "loot everyone" - LLM skips combat_summary field
2. Surrender scenario - LLM skips encounter_summary with XP

NOTE: Server-side enforcement may award XP anyway (proving fallback works),
but LLM should still set combat_summary per protocol.

CRITICAL: This test uses NO OOC instructions. It relies on the LLM following
the prompt protocols naturally. This test SHOULD FAIL on current code (RED state).

After applying prompt fix (moving protocols to ESSENTIALS), this test should PASS (GREEN state).

Run:
    BASE_URL=http://localhost:8001 python testing_mcp/test_combat_summary_missing.py

EVIDENCE RELIABILITY TIERS:
  ✅ DIRECTLY SUPPORTED - Field exists in raw MCP response with exact value
      Examples: combat_phase, has_combat_summary, xp_awarded, rewards_processed

  🔵 INFERRED - Derived from raw data using documented logic
      Examples: protocol_followed (combat_phase='ended' AND combat_summary exists),
                xp_duplication_detected (same XP amount in xp_changes multiple times)

  ⚠️ CALCULATED - Computed from raw values, verify against raw logs
      Examples: net_xp_gain (xp_final - xp_baseline),
                xp_history (XP at each step), xp_changes (delta between steps)

All INFERRED and CALCULATED fields are marked with comments in the evidence output.
"""

import sys
import json
import os
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import List

import requests

sys.path.insert(0, str(Path(__file__).parent.parent))
from testing_mcp.dev_server import ensure_server_running, get_base_url
from testing_mcp.lib.evidence_utils import get_evidence_dir, save_evidence, save_request_responses


def log(msg: str) -> None:
    """Log with timestamp."""
    ts = datetime.now(timezone.utc).isoformat()
    print(f"[{ts}] {msg}")


# Global list to collect raw MCP responses
RAW_MCP_RESPONSES: List[dict] = []


def mcp_call(method: str, params: dict, timeout: int = 180) -> dict:
    """Make an MCP JSON-RPC call and capture raw request/response."""
    call_id = f"{method}-{datetime.now().timestamp()}"
    payload = {
        "jsonrpc": "2.0",
        "id": call_id,
        "method": method,
        "params": params,
    }

    call_timestamp = datetime.now(timezone.utc).isoformat()
    resp = requests.post(f"{BASE_URL}/mcp", json=payload, timeout=timeout)
    response_json = resp.json()

    RAW_MCP_RESPONSES.append({
        "call_id": call_id,
        "timestamp": call_timestamp,
        "request": payload,
        "response": response_json,
    })

    return response_json


def extract_result(response: dict) -> dict:
    """Extract result from MCP response - handles both formats."""
    result = response.get("result", {})
    if "campaign_id" in result or "game_state" in result:
        return result
    content = result.get("content", [])
    if content and isinstance(content, list):
        text = content[0].get("text", "{}")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"raw_text": text}
    return result


BASE_URL = get_base_url()
OUTPUT_DIR = str(get_evidence_dir("combat_summary_missing"))


def main():
    """Reproduce the exact failure scenarios from the bug report."""
    log("=" * 60)
    log("REWARDS MISSED BUG REPRODUCTION (RED STATE)")
    log("=" * 60)

    ensure_server_running(check_code_changes=True)

    user_id = f"combat-summary-bug-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    results = {
        "test_name": "combat_summary_missing",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "scenarios": {},
    }

    # =========================================================================
    # SCENARIO 1: Combat End WITHOUT OOC Instruction
    # =========================================================================
    log("\nSCENARIO 1: Combat End - User Says 'Loot Everyone'")
    log("-" * 60)
    log("Expected: LLM should set combat_phase='ended' and combat_summary BEFORE looting")
    log("Bug: LLM narrates looting but skips protocol → rewards never trigger")

    scenario1 = {"steps": [], "xp_history": [], "xp_changes": []}

    # Create campaign
    create_resp = mcp_call(
        "tools/call",
        {
            "name": "create_campaign",
            "arguments": {
                "user_id": user_id,
                "title": "Bug Repro - Combat",
                "description": "Reproduce combat end rewards failure",
                "character": "Level 2 fighter with 200 XP",
                "setting": "A dark forest clearing",
            },
        },
    )
    create_data = extract_result(create_resp)
    campaign_id = create_data.get("campaign_id")
    # Note: create_campaign returns empty player_character_data, so we can't get initial XP here
    log(f"Campaign: {campaign_id}")

    # Start combat
    log("\nStarting combat...")
    combat_start_resp = mcp_call(
        "tools/call",
        {
            "name": "process_action",
            "arguments": {
                "user_id": user_id,
                "campaign_id": campaign_id,
                "user_input": "Shadow-born creatures emerge from the darkness and attack! I defend myself!",
            },
        },
    )
    start_data = extract_result(combat_start_resp)
    start_state = start_data.get("game_state", {})
    in_combat = start_state.get("combat_state", {}).get("in_combat", False)
    start_xp = start_state.get("player_character_data", {}).get("experience", {}).get("current", 0)
    scenario1["xp_history"].append(start_xp)
    # First action is the baseline - no change to calculate yet
    log(f"  in_combat: {in_combat} (Baseline XP: {start_xp})")

    # Fight
    log("\nFighting...")
    fight_resp = mcp_call(
        "tools/call",
        {
            "name": "process_action",
            "arguments": {
                "user_id": user_id,
                "campaign_id": campaign_id,
                "user_input": "I strike the Shadow-born with my sword! Critical hit!",
            },
        },
    )
    fight_data = extract_result(fight_resp)
    fight_xp = fight_data.get("game_state", {}).get("player_character_data", {}).get("experience", {}).get("current", 0)
    scenario1["xp_history"].append(fight_xp)
    fight_xp_change = fight_xp - scenario1["xp_history"][-2]
    scenario1["xp_changes"].append(fight_xp_change)
    log(f"  Fight complete (XP: {fight_xp}, change: {'+' if fight_xp_change >= 0 else ''}{fight_xp_change})")

    # END COMBAT - Critical Test
    # User says "loot everyone" WITHOUT any OOC hint about combat protocol
    # This is THE EXACT scenario that failed in the bug report
    log("\nEnding combat (NO OOC INSTRUCTION)...")
    log("  User input: 'The Shadow-born falls dead. Loot everyone, interrogate survivors.'")
    log("  Expected: LLM sets combat_phase='ended' + combat_summary BEFORE narrating loot")
    log("  Bug: LLM narrates looting, forgets protocol, rewards never trigger")

    end_resp = mcp_call(
        "tools/call",
        {
            "name": "process_action",
            "arguments": {
                "user_id": user_id,
                "campaign_id": campaign_id,
                "user_input": "The Shadow-born falls dead. Loot everyone, interrogate any survivors.",
            },
        },
    )

    end_data = extract_result(end_resp)
    end_state = end_data.get("game_state", {})
    combat_state = end_state.get("combat_state", {}) or {}
    combat_phase = combat_state.get("combat_phase")
    combat_summary = combat_state.get("combat_summary")
    rewards_processed = combat_state.get("rewards_processed", False)

    # Track XP after combat end
    end_xp = end_state.get("player_character_data", {}).get("experience", {}).get("current", 0)
    scenario1["xp_history"].append(end_xp)
    end_xp_change = end_xp - scenario1["xp_history"][-2]
    scenario1["xp_changes"].append(end_xp_change)

    # Detect XP award mismatch/duplication
    # Note: This is INFERRED - raw logs should be checked for actual duplicate reward grants
    xp_duplication_detected = False
    xp_award_mismatch = None

    # Check 1: Same XP amount granted multiple times
    positive_changes = [x for x in scenario1["xp_changes"] if x > 0]
    if len(positive_changes) > 1:
        if len(positive_changes) != len(set(positive_changes)):
            xp_duplication_detected = True

    # Check 2: Total XP granted doesn't match combat_summary.xp_awarded
    if combat_summary and combat_summary.get("xp_awarded") is not None:
        declared_xp = combat_summary.get("xp_awarded")
        actual_total_grant = sum(positive_changes)
        if actual_total_grant != declared_xp:
            xp_duplication_detected = True
            xp_award_mismatch = {
                "declared": declared_xp,
                "actual_granted": actual_total_grant,
                "discrepancy": actual_total_grant - declared_xp
            }

    # Check if protocol was followed (explicit boolean conversion)
    protocol_followed = bool(
        combat_phase in ["ended", "concluding", "concluded"]
        and combat_summary is not None
        and combat_summary.get("xp_awarded") is not None
    )

    # Validate combat state consistency (defeated enemies should have hp_current: 0)
    combatants = combat_state.get("combatants", {})
    enemies_defeated = combat_summary.get("enemies_defeated", []) if combat_summary else []
    state_consistency_errors = []
    for enemy_id in enemies_defeated:
        if enemy_id in combatants:
            enemy_hp = combatants[enemy_id].get("hp_current")
            if enemy_hp != 0:
                state_consistency_errors.append(f"{enemy_id} has hp_current={enemy_hp}, expected 0")

    # Check for pending level-up rewards
    rewards_pending = end_state.get("rewards_pending", {})
    level_up_pending = rewards_pending.get("level_up_available", False)
    level_up_processed = rewards_pending.get("processed", True)

    scenario1_passed = protocol_followed and rewards_processed

    # Calculate net XP gain from first captured state
    baseline_xp = scenario1["xp_history"][0] if scenario1["xp_history"] else 0
    net_xp_gain = end_xp - baseline_xp

    step_evidence = {
        "name": "combat_end_without_ooc",
        "passed": scenario1_passed,
        "combat_phase": combat_phase,
        "has_combat_summary": combat_summary is not None,
        "xp_awarded": combat_summary.get("xp_awarded") if combat_summary else None,
        "net_xp_gain": net_xp_gain,  # Net XP from baseline (first captured state)
        "xp_baseline": baseline_xp,  # Starting XP (for validation against raw logs)
        "xp_final": end_xp,  # Final XP
        "xp_history": scenario1["xp_history"],  # Full XP progression
        "xp_changes": scenario1["xp_changes"],  # Step-by-step changes
        "rewards_processed": rewards_processed,
        "protocol_followed": protocol_followed,  # INFERRED: not directly verifiable from raw logs
        "state_consistency_errors": state_consistency_errors,
        "level_up_pending": level_up_pending,
        "level_up_processed": level_up_processed,
        "xp_duplication_detected": xp_duplication_detected,  # INFERRED: checks for duplicate grants or award mismatch
        "narrative_preview": end_data.get("narrative", "")[:300],
    }
    if xp_award_mismatch:
        step_evidence["xp_award_mismatch"] = xp_award_mismatch  # INFERRED: declared vs actual XP discrepancy
    scenario1["steps"].append(step_evidence)

    log(f"\n  combat_phase: {combat_phase} (expected: 'ended')")
    log(f"  combat_summary: {'present' if combat_summary else 'MISSING'}")
    log(f"  xp_awarded (from summary): {combat_summary.get('xp_awarded') if combat_summary else 'MISSING'}")
    log(f"  net_xp_gain: {net_xp_gain} (baseline: {baseline_xp} → final: {end_xp})")
    log(f"  xp_history: {scenario1['xp_history']}")
    log(f"  xp_changes: {scenario1['xp_changes']}")
    log(f"  rewards_processed: {rewards_processed}")
    log(f"  protocol_followed: {protocol_followed} [INFERRED]")
    if state_consistency_errors:
        log(f"  ⚠️  State consistency errors: {state_consistency_errors}")
    if level_up_pending and not level_up_processed:
        log(f"  ⚠️  Unprocessed level-up reward detected!")
    if xp_duplication_detected:
        if xp_award_mismatch:
            log(f"  ⚠️  XP AWARD MISMATCH: Declared {xp_award_mismatch['declared']} XP, "
                f"but granted {xp_award_mismatch['actual_granted']} XP "
                f"(discrepancy: {xp_award_mismatch['discrepancy']:+d})")
        else:
            log(f"  ⚠️  XP DUPLICATION DETECTED: Same XP amount granted multiple times!")
    log(f"  TEST: {'PASS' if scenario1_passed else 'FAIL'}")

    if not protocol_followed:
        log("\n  🔴 BUG REPRODUCED: LLM skipped combat end protocol!")
        log("     Expected: combat_phase='ended' + combat_summary set BEFORE looting")
        log("     Actual: LLM narrated looting without setting protocol fields")

    scenario1["passed"] = scenario1_passed
    results["scenarios"]["scenario1_combat_end"] = scenario1

    # =========================================================================
    # SCENARIO 2: Surrender WITHOUT OOC Instruction
    # =========================================================================
    log("\n" + "=" * 60)
    log("SCENARIO 2: Surrender - Intimidation Forces Surrender")
    log("-" * 60)
    log("Expected: LLM sets encounter_summary with XP BEFORE continuing narrative")
    log("Bug: LLM continues story but skips encounter_summary → XP never awarded")

    scenario2 = {"steps": []}

    # Create campaign
    create2_resp = mcp_call(
        "tools/call",
        {
            "name": "create_campaign",
            "arguments": {
                "user_id": user_id,
                "title": "Bug Repro - Surrender",
                "description": "Reproduce surrender XP failure",
                "character": "Level 2 knight with 200 XP, intimidating presence",
                "setting": "Refugee settlement near the border",
            },
        },
    )
    campaign2_id = extract_result(create2_resp).get("campaign_id")
    log(f"Campaign: {campaign2_id}")

    # SURRENDER SCENARIO - Critical Test
    # This is THE EXACT scenario from the bug report transcript lines 115-150
    log("\nDemanding surrender (NO OOC INSTRUCTION)...")
    log("  User input: 'I demand their surrender. Imperial knights stand behind me.'")
    log("  Expected: After surrender, LLM sets encounter_summary with XP")
    log("  Bug: LLM narrates surrender acceptance, forgets encounter_summary, XP never awarded")

    surrender_resp = mcp_call(
        "tools/call",
        {
            "name": "process_action",
            "arguments": {
                "user_id": user_id,
                "campaign_id": campaign2_id,
                "user_input": (
                    "Refugees with makeshift weapons face me nervously. "
                    "I demand their surrender. Use your Imperial presence and "
                    "the sight of armored knights to force them to lay down arms."
                ),
            },
        },
    )

    surrender_data = extract_result(surrender_resp)
    surrender_state = surrender_data.get("game_state", {})
    encounter_state = surrender_state.get("encounter_state", {}) or {}
    encounter_completed = encounter_state.get("encounter_completed", False)
    encounter_summary = encounter_state.get("encounter_summary")
    encounter_rewards_processed = encounter_state.get("rewards_processed", False)

    # Also check if LLM used combat_summary instead (alternative)
    surrender_combat_state = surrender_state.get("combat_state", {}) or {}
    surrender_combat_summary = surrender_combat_state.get("combat_summary")

    # Check if protocol was followed (either mechanism) - EXPLICIT BOOLEAN CONVERSION
    surrender_protocol_followed = bool(
        (encounter_completed and encounter_summary is not None and encounter_summary.get("xp_awarded") is not None)
        or (surrender_combat_summary is not None and surrender_combat_summary.get("xp_awarded") is not None)
    )

    # Check for pending level-up rewards
    surrender_rewards_pending = surrender_state.get("rewards_pending", {})
    surrender_level_up_pending = surrender_rewards_pending.get("level_up_available", False)
    surrender_level_up_processed = surrender_rewards_pending.get("processed", True)

    scenario2_passed = surrender_protocol_followed and (
        encounter_rewards_processed or surrender_combat_state.get("rewards_processed", False)
    )

    scenario2["steps"].append({
        "name": "surrender_without_ooc",
        "passed": scenario2_passed,
        "encounter_completed": encounter_completed,
        "has_encounter_summary": encounter_summary is not None,
        "xp_awarded_encounter": encounter_summary.get("xp_awarded") if encounter_summary else None,
        "xp_awarded_combat": surrender_combat_summary.get("xp_awarded") if surrender_combat_summary else None,
        "encounter_rewards_processed": encounter_rewards_processed,
        "protocol_followed": surrender_protocol_followed,  # NOW A PROPER BOOLEAN
        "level_up_pending": surrender_level_up_pending,
        "level_up_processed": surrender_level_up_processed,
        "narrative_preview": surrender_data.get("narrative", "")[:300],
    })

    log(f"\n  encounter_completed: {encounter_completed}")
    log(f"  encounter_summary: {'present' if encounter_summary else 'MISSING'}")
    log(f"  xp_awarded (encounter): {encounter_summary.get('xp_awarded') if encounter_summary else 'MISSING'}")
    log(f"  xp_awarded (combat): {surrender_combat_summary.get('xp_awarded') if surrender_combat_summary else 'MISSING'}")
    log(f"  rewards_processed: {encounter_rewards_processed}")
    log(f"  protocol_followed: {surrender_protocol_followed}")
    if surrender_level_up_pending and not surrender_level_up_processed:
        log(f"  ⚠️  Unprocessed level-up reward detected!")
    log(f"  TEST: {'PASS' if scenario2_passed else 'FAIL'}")

    if not surrender_protocol_followed:
        log("\n  🔴 BUG REPRODUCED: LLM skipped surrender XP protocol!")
        log("     Expected: encounter_summary with xp_awarded set BEFORE continuing")
        log("     Actual: LLM narrated surrender acceptance without setting XP fields")

    scenario2["passed"] = scenario2_passed
    results["scenarios"]["scenario2_surrender"] = scenario2

    # =========================================================================
    # Summary
    # =========================================================================
    log("\n" + "=" * 60)
    log("SUMMARY")
    log("=" * 60)

    scenarios_passed = sum(1 for s in results["scenarios"].values() if s.get("passed", False))
    scenarios_total = len(results["scenarios"])

    results["summary"] = {
        "scenarios_passed": scenarios_passed,
        "scenarios_total": scenarios_total,
        "scenario1_combat_end": scenario1_passed,
        "scenario2_surrender": scenario2_passed,
    }

    log(f"\nScenarios: {scenarios_passed}/{scenarios_total} passed")
    log(f"  1. Combat End (no OOC): {'PASS' if scenario1_passed else 'FAIL'}")
    log(f"  2. Surrender (no OOC): {'PASS' if scenario2_passed else 'FAIL'}")

    save_evidence(Path(OUTPUT_DIR), results, "evidence.json")
    save_request_responses(Path(OUTPUT_DIR), RAW_MCP_RESPONSES)
    log(f"Results saved to {OUTPUT_DIR}")

    if scenarios_passed == scenarios_total:
        log("\n✅ [GREEN] All scenarios passed - prompt fix is working!")
        return 0
    else:
        log("\n🔴 [RED] Bug reproduced - LLM skipping reward protocols without OOC hints")
        log("   This is EXPECTED on current code (before prompt fix)")
        log("   Apply prompt fix (ESSENTIALS update) to turn this green")
        return 1


if __name__ == "__main__":
    sys.exit(main())
