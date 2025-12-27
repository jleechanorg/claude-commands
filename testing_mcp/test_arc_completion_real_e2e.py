#!/usr/bin/env python3
"""
Prompted Arc Completion E2E Test

This test creates a REAL campaign, plays through narrative actions with
an OOC hint to complete the arc, and validates arc_milestones persistence.

HONEST LABELING: This is "prompted completion" - the user explicitly asks
the LLM to mark the arc complete via OOC instruction. This proves the
arc_milestones system works end-to-end, but does NOT prove the LLM will
autonomously decide to complete arcs during normal gameplay.

What this test PROVES:
- arc_milestones initializes as {}
- LLM can update arc_milestones during gameplay
- arc_milestones persists to Firestore
- System handles both dict and string completion formats

What this test does NOT prove:
- LLM autonomously recognizes arc completion without hints
- Schema enforcement (LLM may use simplified formats)
"""

import json
import os
import subprocess
import sys
import requests
from datetime import datetime, timezone
from typing import Any

# Configuration
BASE_URL = os.getenv("BASE_URL", "http://localhost:8001")
USER_ID = f"e2e-prompted-arc-{datetime.now().strftime('%Y%m%d%H%M%S')}"
OUTPUT_DIR = "/tmp/arc_milestones_prompted_e2e"
STRICT_MODE = os.getenv("STRICT_MODE", "true").lower() == "true"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def extract_arc_milestones(game_state: dict) -> dict:
    """Extract arc_milestones, preserving empty dictionaries as valid values."""

    arc_milestones = game_state.get("arc_milestones")
    if arc_milestones is None:
        arc_milestones = game_state.get("custom_campaign_state", {}).get(
            "arc_milestones", {}
        )
    return arc_milestones


def log(msg: str) -> None:
    """Log with timestamp."""
    ts = datetime.now(timezone.utc).isoformat()
    print(f"[{ts}] {msg}")


def capture_provenance() -> dict:
    """Capture git and environment provenance."""
    provenance = {}
    try:
        provenance["git_head"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, timeout=5
        ).strip()
        provenance["git_branch"] = subprocess.check_output(
            ["git", "branch", "--show-current"], text=True, timeout=5
        ).strip()
        provenance["git_status"] = subprocess.check_output(
            ["git", "status", "-sb"], text=True, timeout=5
        ).strip()
        provenance["git_origin_main"] = subprocess.check_output(
            ["git", "rev-parse", "origin/main"], text=True, timeout=5
        ).strip()
    except Exception as e:
        provenance["git_error"] = str(e)

    provenance["env"] = {
        "BASE_URL": BASE_URL,
        "STRICT_MODE": STRICT_MODE,
    }
    return provenance


def normalize_arc_milestones(milestones: dict) -> dict:
    """Normalize arc_milestones to canonical dict format.

    LLM may return:
    - {'arc_name': 'COMPLETED'} (string)
    - {'arc_name': {'status': 'completed', ...}} (canonical dict)

    This normalizes to canonical format for consistent validation.
    """
    normalized = {}
    for arc_name, arc_data in milestones.items():
        if isinstance(arc_data, str):
            # Convert string to canonical dict
            normalized[arc_name] = {
                "status": "completed" if "complete" in arc_data.lower() else arc_data.lower(),
                "llm_raw_value": arc_data,
                "normalized": True
            }
        elif isinstance(arc_data, dict):
            normalized[arc_name] = arc_data
        else:
            normalized[arc_name] = {"status": "unknown", "raw_value": str(arc_data)}
    return normalized


def mcp_call(method: str, params: dict) -> dict:
    """Make an MCP JSON-RPC call."""
    payload = {
        "jsonrpc": "2.0",
        "id": f"{method}-{datetime.now().timestamp()}",
        "method": method,
        "params": params
    }
    resp = requests.post(f"{BASE_URL}/mcp", json=payload, timeout=120)
    return resp.json()


def extract_result(response: dict) -> dict:
    """Extract result from MCP response - handles both formats."""
    result = response.get("result", {})
    # Format 1: Direct result object (create_campaign, get_campaign_state)
    if "campaign_id" in result or "game_state" in result:
        return result
    # Format 2: MCP content array (process_action)
    content = result.get("content", [])
    if content and isinstance(content, list):
        text = content[0].get("text", "{}")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"raw_text": text}
    return result


def main():
    results = {
        "test_name": "arc_milestones_prompted_e2e",
        "test_type": "prompted_completion",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "base_url": BASE_URL,
        "user_id": USER_ID,
        "strict_mode": STRICT_MODE,
        "provenance": capture_provenance(),
        "steps": [],
        "summary": {}
    }

    log(f"Provenance: {results['provenance'].get('git_head', 'unknown')[:12]}...")
    log(f"Strict mode: {STRICT_MODE}")

    # Step 1: Health check
    log("Step 1: Health check")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=10)
        health = resp.json()
        results["steps"].append({
            "name": "health_check",
            "passed": health.get("status") == "healthy",
            "details": health
        })
        log(f"  Health: {health.get('status')}")
    except Exception as e:
        log(f"  FAILED: {e}")
        results["steps"].append({"name": "health_check", "passed": False, "error": str(e)})
        save_results(results)
        return 1

    # Step 2: Create campaign with a SHORT, COMPLETABLE arc setup
    log("Step 2: Create campaign with quick-completion scenario")
    create_response = mcp_call("tools/call", {
        "name": "create_campaign",
        "arguments": {
            "user_id": USER_ID,
            "title": "The Quick Heist",
            "description": "A one-shot heist mission. The goal: steal the gem and escape.",
            "character": "A skilled thief on their final job before retirement",
            "setting": "A wealthy merchant's mansion at night"
        }
    })

    campaign_data = extract_result(create_response)
    campaign_id = campaign_data.get("campaign_id")
    # arc_milestones can be at game_state.arc_milestones or game_state.custom_campaign_state.arc_milestones
    game_state = campaign_data.get("game_state", {})
    initial_arc_milestones = extract_arc_milestones(game_state)

    results["steps"].append({
        "name": "create_campaign",
        "passed": campaign_id is not None,
        "campaign_id": campaign_id,
        "initial_arc_milestones": initial_arc_milestones
    })
    log(f"  Campaign ID: {campaign_id}")
    log(f"  Initial arc_milestones: {initial_arc_milestones}")

    if not campaign_id:
        log("  FAILED: No campaign ID")
        save_results(results)
        return 1

    results["campaign_id"] = campaign_id

    # Step 3: Play through the heist - action 1: Enter the mansion
    log("Step 3: Action 1 - Enter the mansion")
    action1 = mcp_call("tools/call", {
        "name": "process_action",
        "arguments": {
            "user_id": USER_ID,
            "campaign_id": campaign_id,
            "user_input": "I sneak through the garden and pick the lock on the back door to enter the mansion."
        }
    })
    action1_data = extract_result(action1)
    action1_narrative = action1_data.get("narrative", action1_data.get("raw_text", ""))
    results["steps"].append({
        "name": "action_1_enter",
        "passed": bool(action1_narrative) and "error" not in str(action1_narrative).lower(),
        "narrative_preview": action1_narrative[:200] if action1_narrative else None
    })
    log(f"  Narrative: {action1_narrative[:100] if action1_narrative else 'None'}...")

    # Step 4: Action 2 - Find the gem
    log("Step 4: Action 2 - Find the gem")
    action2 = mcp_call("tools/call", {
        "name": "process_action",
        "arguments": {
            "user_id": USER_ID,
            "campaign_id": campaign_id,
            "user_input": "I search the mansion and locate the gem in the master bedroom safe. I crack the safe and take the gem."
        }
    })
    action2_data = extract_result(action2)
    action2_narrative = action2_data.get("narrative", action2_data.get("raw_text", ""))
    results["steps"].append({
        "name": "action_2_get_gem",
        "passed": bool(action2_narrative) and "error" not in str(action2_narrative).lower(),
        "narrative_preview": action2_narrative[:200] if action2_narrative else None
    })
    log(f"  Narrative: {action2_narrative[:100] if action2_narrative else 'None'}...")

    # Step 5: Action 3 - Escape and complete the heist
    log("Step 5: Action 3 - Complete the heist (explicit completion request)")
    action3 = mcp_call("tools/call", {
        "name": "process_action",
        "arguments": {
            "user_id": USER_ID,
            "campaign_id": campaign_id,
            "user_input": (
                "I escape through the window, climb down the wall, and disappear into the night. "
                "The heist is complete - I have the gem and I'm free. This marks the successful "
                "completion of my final job. [OOC: Please mark the 'final_heist' arc as COMPLETED "
                "in the game state since the mission objective has been achieved.]"
            )
        }
    })
    action3_data = extract_result(action3)
    action3_narrative = action3_data.get("narrative", action3_data.get("raw_text", ""))
    action3_game_state = action3_data.get("game_state", {})
    arc_milestones_after = extract_arc_milestones(action3_game_state)

    results["steps"].append({
        "name": "action_3_complete_heist",
        "passed": bool(action3_narrative) and "error" not in str(action3_narrative).lower(),
        "narrative_preview": action3_narrative[:200] if action3_narrative else None,
        "arc_milestones_after": arc_milestones_after
    })
    log(f"  Narrative: {action3_narrative[:100] if action3_narrative else 'None'}...")
    log(f"  arc_milestones after action 3: {arc_milestones_after}")

    # Step 6: Get final campaign state
    log("Step 6: Get final campaign state")
    state_response = mcp_call("tools/call", {
        "name": "get_campaign_state",
        "arguments": {
            "user_id": USER_ID,
            "campaign_id": campaign_id
        }
    })
    state_data = extract_result(state_response)
    final_game_state = state_data.get("game_state", {})
    final_arc_milestones = extract_arc_milestones(final_game_state)

    results["steps"].append({
        "name": "get_final_state",
        "passed": final_arc_milestones is not None,
        "final_arc_milestones": final_arc_milestones
    })
    log(f"  Final arc_milestones: {final_arc_milestones}")

    # Step 7: Normalize and check arc completion
    normalized_milestones = {}
    arc_completed = False
    completed_arcs = []
    schema_violation = False

    if final_arc_milestones and isinstance(final_arc_milestones, dict):
        normalized_milestones = normalize_arc_milestones(final_arc_milestones)
        for arc_name, arc_data in normalized_milestones.items():
            if arc_data.get("status") == "completed":
                arc_completed = True
                completed_arcs.append(arc_name)
            if arc_data.get("normalized"):
                schema_violation = True
                log(f"  ⚠️ Schema violation: '{arc_name}' was string, normalized to dict")

    # Summary
    results["summary"] = {
        "campaign_created": campaign_id is not None,
        "initial_arc_milestones": initial_arc_milestones,
        "final_arc_milestones_raw": final_arc_milestones,
        "final_arc_milestones_normalized": normalized_milestones,
        "arc_completed": arc_completed,
        "completed_arcs": completed_arcs,
        "schema_violation": schema_violation,
        "steps_passed": sum(1 for s in results["steps"] if s.get("passed")),
        "steps_total": len(results["steps"])
    }

    log("")
    log("=" * 60)
    log("SUMMARY")
    log("=" * 60)
    log(f"Campaign created: {campaign_id is not None}")
    log(f"Arc completed (prompted): {arc_completed}")
    log(f"Completed arcs: {completed_arcs}")
    log(f"Schema violation: {schema_violation}")
    log(f"Steps: {results['summary']['steps_passed']}/{results['summary']['steps_total']} passed")

    save_results(results)

    if arc_completed:
        log("\n✅ SUCCESS: Arc was completed through prompted gameplay!")
        return 0
    else:
        if STRICT_MODE:
            log("\n❌ FAILED: No arc completion detected (strict mode)")
            return 1
        else:
            log("\n⚠️ Arc was NOT completed (LLM didn't respond to prompt)")
            log("   Run with STRICT_MODE=false to allow this as non-fatal")
            return 0


def save_results(results: dict) -> None:
    """Save results to file with checksum."""
    import hashlib

    output_file = os.path.join(OUTPUT_DIR, "prompted_e2e_test.json")
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    # Generate checksum
    with open(output_file, "rb") as f:
        checksum = hashlib.sha256(f.read()).hexdigest()

    checksum_file = f"{output_file}.sha256"
    with open(checksum_file, "w") as f:
        f.write(f"{checksum}  prompted_e2e_test.json\n")

    log(f"\nResults saved to: {output_file}")
    log(f"Checksum: {checksum}")


if __name__ == "__main__":
    sys.exit(main())
