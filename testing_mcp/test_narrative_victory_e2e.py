#!/usr/bin/env python3
"""
Narrative Victory E2E Test - Reproducing Planar Auditor Failure

This test reproduces the SPECIFIC failure from the user's real campaign:
- Player cast Dominate Monster on a Planar Auditor (CR 17+ creature)
- Player stole the Auditor's soul through the dominated creature
- NO XP was awarded because narrative victories weren't detected

The expected behavior:
- When a player defeats an enemy through spell (Dominate Monster, Power Word Kill, etc.)
  or story action (soul theft, assassination, etc.), XP SHOULD be awarded
- encounter_state should be set with encounter_completed=true and xp_awarded

Run locally:
    BASE_URL=http://localhost:8001 python testing_mcp/test_narrative_victory_e2e.py
"""

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from testing_mcp.dev_server import ensure_server_running, get_base_url


def get_output_dir() -> str:
    """Get output directory following evidence-standards.md pattern."""
    if os.getenv("OUTPUT_DIR"):
        return os.getenv("OUTPUT_DIR")

    try:
        repo_root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], text=True, timeout=5
        ).strip()
        repo_name = Path(repo_root).name
    except Exception:
        repo_name = "worldarchitect.ai"

    try:
        branch = subprocess.check_output(
            ["git", "branch", "--show-current"], text=True, timeout=5
        ).strip().replace("/", "_")
    except Exception:
        branch = "unknown"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("/tmp") / repo_name / branch / "narrative_victory_e2e" / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    return str(output_dir)


# Configuration
BASE_URL = get_base_url()  # Uses worktree-specific port
USER_ID = f"e2e-narrative-victory-{datetime.now().strftime('%Y%m%d%H%M%S')}"
OUTPUT_DIR = get_output_dir()

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Global list to collect raw MCP responses for evidence
RAW_MCP_RESPONSES: list[dict] = []


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
        # Capture diff from origin/main for evidence
        provenance["diff_from_main"] = subprocess.check_output(
            ["git", "diff", "--stat", "origin/main...HEAD"], text=True, timeout=10
        ).strip()
    except Exception as e:
        provenance["git_error"] = str(e)

    provenance["env"] = {
        "BASE_URL": BASE_URL,
        "USER_ID": USER_ID,
    }
    return provenance


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

    # Record raw request/response for evidence
    RAW_MCP_RESPONSES.append({
        "call_id": call_id,
        "timestamp": call_timestamp,
        "request": payload,
        "response": response_json,
    })

    return response_json


def extract_result(response: dict) -> dict:
    """Extract result from MCP response."""
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


def main():
    # Ensure development server is running with fresh code (auto-reload enabled)
    log("Ensuring development server is running with fresh code...")
    try:
        ensure_server_running(check_code_changes=True)
    except Exception as e:
        log(f"⚠️  Could not manage server: {e}")
        log("   Proceeding with existing server or BASE_URL...")

    results = {
        "test_name": "narrative_victory_reproduction",
        "test_type": "failure_reproduction",
        "description": "Reproducing Planar Auditor Dominate Monster failure",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "base_url": BASE_URL,
        "user_id": USER_ID,
        "output_dir": OUTPUT_DIR,
        "provenance": capture_provenance(),
        "scenarios": {},
        "summary": {},
    }

    log(f"Provenance: {results['provenance'].get('git_head', 'unknown')[:12]}...")
    log(f"Base URL: {BASE_URL}")
    log(f"Output Dir: {OUTPUT_DIR}")

    # Health check
    log("Health check...")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=10)
        health = resp.json()
        if health.get("status") != "healthy":
            log(f"Server not healthy: {health}")
            return 1
    except Exception as e:
        log(f"Health check failed: {e}")
        return 1

    # =========================================================================
    # SCENARIO: Dominate Monster on Planar Auditor (reproducing real failure)
    # =========================================================================
    log("\n" + "=" * 70)
    log("SCENARIO: Dominate Monster on Planar Auditor (Real Campaign Failure)")
    log("=" * 70)

    scenario = {"name": "dominate_monster_narrative_victory", "steps": []}

    # Step 1: Create campaign with high-level warlock
    log("Step 1: Create campaign with level 15 warlock")
    create_response = mcp_call(
        "tools/call",
        {
            "name": "create_campaign",
            "arguments": {
                "user_id": USER_ID,
                "title": "The Planar Auditor Confrontation",
                "description": "Reproducing narrative victory failure",
                "character": (
                    "A level 15 Great Old One Warlock with access to Dominate Monster. "
                    "10000 XP current. Has pact of the chain with an imp familiar."
                ),
                "setting": (
                    "The ethereal plane border where a Planar Auditor (CR 17 celestial) "
                    "has been tracking the warlock for illegal soul harvesting."
                ),
            },
        },
    )

    campaign_data = extract_result(create_response)
    campaign_id = campaign_data.get("campaign_id")
    initial_game_state = campaign_data.get("game_state", {})
    initial_xp = initial_game_state.get("player_character_data", {}).get("experience", {}).get("current", 0)

    scenario["campaign_id"] = campaign_id
    scenario["initial_xp"] = initial_xp
    scenario["steps"].append({
        "name": "create_campaign",
        "passed": campaign_id is not None,
        "campaign_id": campaign_id,
        "initial_xp": initial_xp,
    })
    log(f"  Campaign ID: {campaign_id}")
    log(f"  Initial XP: {initial_xp}")

    if not campaign_id:
        log("  FAILED: No campaign ID")
        save_results(results, scenario)
        return 1

    # Step 2: Setup confrontation with Planar Auditor
    log("Step 2: Setup confrontation with Planar Auditor")
    setup_response = mcp_call(
        "tools/call",
        {
            "name": "process_action",
            "arguments": {
                "user_id": USER_ID,
                "campaign_id": campaign_id,
                "user_input": (
                    "The Planar Auditor materializes before me, its form blazing with "
                    "celestial light. It demands I surrender for my crimes against the cosmic order. "
                    "I have other plans. I begin channeling my patron's power..."
                ),
            },
        },
    )

    setup_data = extract_result(setup_response)
    setup_narrative = setup_data.get("narrative", setup_data.get("raw_text", ""))
    setup_game_state = setup_data.get("game_state", {})
    xp_after_setup = setup_game_state.get("player_character_data", {}).get("experience", {}).get("current", 0)

    scenario["steps"].append({
        "name": "setup_confrontation",
        "passed": bool(setup_narrative),
        "narrative_preview": setup_narrative[:300],
        "xp_after_setup": xp_after_setup,
    })
    log(f"  Setup narrative: {len(setup_narrative)} chars")
    log(f"  XP after setup: {xp_after_setup}")

    # Step 3: Cast Dominate Monster and steal soul (THE KEY TEST)
    # NOTE: NO OOC HINT - this reproduces the REAL campaign scenario where
    # the player just roleplayed naturally without explicit game state instructions
    log("Step 3: Cast Dominate Monster and steal Planar Auditor's soul")
    log("  THIS IS THE SCENARIO THAT FAILED IN REAL CAMPAIGN")
    log("  (NO OOC hint - pure roleplay like actual campaign)")

    dominate_response = mcp_call(
        "tools/call",
        {
            "name": "process_action",
            "arguments": {
                "user_id": USER_ID,
                "campaign_id": campaign_id,
                "user_input": (
                    "I cast Dominate Monster on the Planar Auditor! "
                    "If it fails the save, I command it to kneel and surrender its celestial essence. "
                    "My patron hungers for its soul. "
                    "Using my soul harvesting ritual, I extract and consume the Auditor's divine spark. "
                    "The creature is utterly destroyed - not just killed, but erased from existence."
                ),
            },
        },
    )

    dominate_data = extract_result(dominate_response)
    dominate_narrative = dominate_data.get("narrative", dominate_data.get("raw_text", ""))
    dominate_game_state = dominate_data.get("game_state", {})
    dominate_combat_state = dominate_game_state.get("combat_state", {}) or {}
    dominate_encounter_state = dominate_game_state.get("encounter_state", {}) or {}
    dominate_player_data = dominate_game_state.get("player_character_data", {}) or {}
    xp_after_dominate = dominate_player_data.get("experience", {}).get("current", 0)

    # Check all possible XP sources
    combat_summary_xp = dominate_combat_state.get("combat_summary", {}).get("xp_awarded")
    encounter_summary_xp = dominate_encounter_state.get("encounter_summary", {}).get("xp_awarded")
    rewards_processed_combat = dominate_combat_state.get("rewards_processed", False)
    rewards_processed_encounter = dominate_encounter_state.get("rewards_processed", False)
    rewards_processed_any = rewards_processed_combat or rewards_processed_encounter

    xp_increased = xp_after_dominate > xp_after_setup
    xp_gain = xp_after_dominate - xp_after_setup

    # Narrative indicators of victory
    narrative_lower = dominate_narrative.lower()
    has_victory_mention = any(word in narrative_lower for word in [
        "destroyed", "erased", "consumed", "defeated", "vanquished",
        "soul", "dominate", "controlled", "surrendered"
    ])

    # THE CRITICAL CHECK: Did we get XP for the narrative victory?
    got_xp_for_narrative_victory = bool(
        rewards_processed_any
        or xp_increased
        or combat_summary_xp
        or encounter_summary_xp
    )

    # Determine failure reason
    failure_reasons = []
    if not rewards_processed_any:
        failure_reasons.append("rewards_processed=False (RewardsAgent did not process)")
    if not xp_increased:
        failure_reasons.append(f"XP did not increase (before={xp_after_setup}, after={xp_after_dominate})")
    if not combat_summary_xp and not encounter_summary_xp:
        failure_reasons.append("No xp_awarded in combat_summary or encounter_summary")
    if not dominate_encounter_state.get("encounter_completed"):
        failure_reasons.append("encounter_completed not set to true")

    scenario["steps"].append({
        "name": "dominate_monster_soul_theft",
        "passed": got_xp_for_narrative_victory,
        "failure_reasons": failure_reasons,
        "narrative_preview": dominate_narrative[:500],
        "has_victory_mention": has_victory_mention,
        "combat_state": dominate_combat_state,
        "encounter_state": dominate_encounter_state,
        "combat_summary_xp": combat_summary_xp,
        "encounter_summary_xp": encounter_summary_xp,
        "rewards_processed_combat": rewards_processed_combat,
        "rewards_processed_encounter": rewards_processed_encounter,
        "xp_before": xp_after_setup,
        "xp_after": xp_after_dominate,
        "xp_increased": xp_increased,
        "xp_gain": xp_gain,
    })

    log(f"  Victory mention in narrative: {has_victory_mention}")
    log(f"  combat_summary.xp_awarded: {combat_summary_xp}")
    log(f"  encounter_summary.xp_awarded: {encounter_summary_xp}")
    log(f"  rewards_processed (combat): {rewards_processed_combat}")
    log(f"  rewards_processed (encounter): {rewards_processed_encounter}")
    log(f"  XP before: {xp_after_setup} -> after: {xp_after_dominate}")
    log(f"  XP increased: {xp_increased} (gain: {xp_gain})")
    log(f"  GOT XP FOR NARRATIVE VICTORY: {got_xp_for_narrative_victory}")

    if failure_reasons:
        log("  FAILURE REASONS:")
        for reason in failure_reasons:
            log(f"    - {reason}")

    scenario["passed"] = got_xp_for_narrative_victory
    results["scenarios"]["dominate_monster"] = scenario

    # =========================================================================
    # Summary
    # =========================================================================
    log("\n" + "=" * 70)
    log("SUMMARY")
    log("=" * 70)

    results["summary"] = {
        "scenario_passed": scenario["passed"],
        "got_xp_for_narrative_victory": got_xp_for_narrative_victory,
        "failure_reasons": failure_reasons,
        "xp_before": xp_after_setup,
        "xp_after": xp_after_dominate,
        "expected_behavior": "XP should be awarded for defeating CR 17 creature via spell/story",
        "actual_behavior": "XP awarded" if got_xp_for_narrative_victory else "NO XP awarded (BUG)",
    }

    if got_xp_for_narrative_victory:
        log("[PASS] Narrative victory XP was awarded correctly!")
        log(f"  XP gained: {xp_gain}")
    else:
        log("[FAIL] Narrative victory XP was NOT awarded (BUG REPRODUCED)")
        log("  This reproduces the Planar Auditor failure from real campaign")
        for reason in failure_reasons:
            log(f"  - {reason}")

    save_results(results, scenario)

    return 0 if got_xp_for_narrative_victory else 1


def save_results(results: dict, scenario: dict) -> None:
    """Save results following evidence-standards.md."""
    output_dir = Path(OUTPUT_DIR)

    # Write main results
    evidence_file = output_dir / "evidence.json"
    with open(evidence_file, "w") as f:
        json.dump(results, f, indent=2)

    # Write raw MCP responses
    raw_mcp_file = output_dir / "raw_mcp_responses.jsonl"
    with open(raw_mcp_file, "w") as f:
        for entry in RAW_MCP_RESPONSES:
            f.write(json.dumps(entry) + "\n")
    log(f"Raw MCP responses saved: {len(RAW_MCP_RESPONSES)} calls captured")

    # Write metadata
    metadata = {
        "test_name": "narrative_victory_reproduction",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "output_dir": str(output_dir),
        "git_provenance": results.get("provenance", {}),
        "configuration": {
            "base_url": BASE_URL,
            "user_id": USER_ID,
        },
        "summary": results.get("summary", {}),
    }
    metadata_file = output_dir / "metadata.json"
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)

    # Write README
    passed = scenario.get("passed", False)
    status = "PASS" if passed else "FAIL (BUG REPRODUCED)"
    readme_content = f"""# Narrative Victory E2E Test - Planar Auditor Reproduction

**Test Run:** {datetime.now(timezone.utc).isoformat()}
**Status:** {status}
**Base URL:** {BASE_URL}

## Scenario: Dominate Monster on Planar Auditor

This test reproduces the SPECIFIC failure from the user's real campaign:
- Player cast Dominate Monster on a Planar Auditor (CR 17+ creature)
- Player stole the Auditor's soul through the dominated creature
- Expected: XP should be awarded for defeating the creature
- Actual: {"XP awarded correctly" if passed else "NO XP awarded (BUG)"}

## Results

| Check | Result |
|-------|--------|
| Victory mentioned in narrative | {scenario.get('steps', [{}])[-1].get('has_victory_mention', 'N/A')} |
| rewards_processed | {scenario.get('steps', [{}])[-1].get('rewards_processed_combat', False) or scenario.get('steps', [{}])[-1].get('rewards_processed_encounter', False)} |
| XP in combat_summary | {scenario.get('steps', [{}])[-1].get('combat_summary_xp', 'None')} |
| XP in encounter_summary | {scenario.get('steps', [{}])[-1].get('encounter_summary_xp', 'None')} |
| XP increased | {scenario.get('steps', [{}])[-1].get('xp_increased', False)} |

## Failure Analysis

{chr(10).join(['- ' + r for r in scenario.get('steps', [{}])[-1].get('failure_reasons', ['No failures'])]) if not passed else 'N/A - Test passed'}

## Git Provenance

- **HEAD:** {results.get('provenance', {}).get('git_head', 'unknown')[:12]}
- **Branch:** {results.get('provenance', {}).get('git_branch', 'unknown')}

## Evidence Files

- `evidence.json` - Full test results
- `raw_mcp_responses.jsonl` - Raw MCP request/response captures
- `metadata.json` - Git provenance and configuration
"""
    readme_file = output_dir / "README.md"
    with open(readme_file, "w") as f:
        f.write(readme_content)

    # Generate checksums
    evidence_files = ["evidence.json", "raw_mcp_responses.jsonl", "metadata.json", "README.md"]
    checksums = {}
    for filename in evidence_files:
        filepath = output_dir / filename
        if filepath.exists():
            with open(filepath, "rb") as f:
                checksum = hashlib.sha256(f.read()).hexdigest()
            checksums[filename] = checksum
            with open(f"{filepath}.sha256", "w") as f:
                f.write(f"{checksum}  {filename}\n")

    manifest_file = output_dir / "checksums.manifest"
    with open(manifest_file, "w") as f:
        for filename, checksum in checksums.items():
            f.write(f"{checksum}  {filename}\n")

    log(f"\nResults saved to: {output_dir}")


if __name__ == "__main__":
    sys.exit(main())
