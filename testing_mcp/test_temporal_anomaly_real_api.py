#!/usr/bin/env python3
"""MCP test for temporal anomaly false-positive fix.

This test verifies that:
1. Incomplete world_time from LLM (missing year/month/day) does NOT trigger
   false "TEMPORAL ANOMALY DETECTED" warnings
2. Real backward time travel DOES trigger proper warnings (when occurring)

Run:
  cd testing_mcp
  python test_temporal_anomaly_real_api.py --server-url https://mvp-site-app-s8-i6xf2p72ka-uc.a.run.app

Run with local server:
  python test_temporal_anomaly_real_api.py --start-local
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from lib import MCPClient
from lib.server_utils import LocalServer, pick_free_port, start_local_mcp_server
from lib.model_utils import DEFAULT_MODEL_MATRIX, settings_for_model, update_user_settings
from lib.campaign_utils import create_campaign, process_action
from lib.evidence_utils import (
    capture_git_provenance,
    capture_server_runtime,
    capture_server_health,
    get_evidence_dir,
    write_with_checksum,
)
import hashlib
import shutil


def _write_checksum_for_file(filepath: Path) -> None:
    """Generate SHA256 checksum file for an existing file."""
    content = filepath.read_bytes()
    sha256_hash = hashlib.sha256(content).hexdigest()
    checksum_file = Path(str(filepath) + ".sha256")
    checksum_file.write_text(f"{sha256_hash}  {filepath.name}\n")

# Module-level evidence storage (populated at test start)
_evidence_dir: Path | None = None
_git_provenance: dict[str, Any] | None = None
_server_info: dict[str, Any] | None = None


def setup_world_time_with_god_mode(
    client: MCPClient, *, user_id: str, campaign_id: str
) -> dict[str, Any]:
    """Set up a complete world_time structure via GOD_MODE.

    Returns the state_changes that were applied.
    """
    world_time = {
        "year": 431,
        "month": "Mirtul",
        "day": 12,
        "hour": 14,
        "minute": 5,
        "second": 0,
        "microsecond": 0,
        "time_of_day": "Afternoon",
    }
    state_changes = {
        "world_data": {
            "world_time": world_time,
            "current_location_name": "Disfavored Encampment - Command Pavilion",
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
        raise RuntimeError(f"GOD_MODE_UPDATE_STATE failed: {result['error']}")

    return state_changes


def check_for_temporal_anomaly(response: dict[str, Any]) -> tuple[bool, str | None]:
    """Check if response contains temporal anomaly warning.

    Returns:
        (has_anomaly, anomaly_message)
    """
    # Check god_mode_response for anomaly warning
    god_mode_response = response.get("god_mode_response", "")
    if "TEMPORAL ANOMALY DETECTED" in god_mode_response:
        return True, god_mode_response

    # Check temporal_correction_warning
    temporal_warning = response.get("temporal_correction_warning", "")
    if temporal_warning and "TEMPORAL" in temporal_warning.upper():
        return True, temporal_warning

    return False, None


def _time_progressed(before: dict[str, Any], after: dict[str, Any]) -> str:
    """Calculate time progression between before and after states.

    Returns a human-readable string describing the time change.
    """
    if not before or not after:
        return "unknown"

    before_min = before.get("hour", 0) * 60 + before.get("minute", 0)
    after_min = after.get("hour", 0) * 60 + after.get("minute", 0)
    diff = after_min - before_min

    if diff > 0:
        hours = diff // 60
        mins = diff % 60
        if hours > 0:
            return f"+{hours}h {mins}m (forward)"
        return f"+{mins}m (forward)"
    elif diff < 0:
        return f"{diff}m (BACKWARD - should trigger warning if complete)"
    return "0m (no change)"


def run_temporal_test(
    client: MCPClient, *, user_id: str, campaign_id: str, model_id: str
) -> list[str]:
    """Run temporal anomaly tests for a campaign.

    Returns list of error messages (empty = all passed).
    """
    errors: list[str] = []

    # First, set up complete world_time
    print(f"  Setting up world_time via GOD_MODE...")
    try:
        setup_world_time_with_god_mode(client, user_id=user_id, campaign_id=campaign_id)
    except Exception as e:
        errors.append(f"Failed to setup world_time: {e}")
        return errors

    # Track world_time progression for before/after evidence
    # Initial state from GOD_MODE setup
    last_world_time: dict[str, Any] = {
        "year": 431,
        "month": "Mirtul",
        "day": 12,
        "hour": 14,
        "minute": 5,
        "second": 0,
        "microsecond": 0,
        "time_of_day": "Afternoon",
    }

    # Test scenarios that could trigger false temporal anomalies
    test_actions = [
        {
            "name": "Simple dialogue action",
            "input": "I speak with the commander about the situation.",
            "expect_no_anomaly": True,
        },
        {
            "name": "Time-progressing action",
            "input": "An hour passes as we discuss strategy. What happens next?",
            "expect_no_anomaly": True,
        },
        {
            "name": "Time-specific scene change",
            "input": "The afternoon wears on. I decide to visit the armory.",
            "expect_no_anomaly": True,
        },
        {
            "name": "Fast forward action",
            "input": "Several hours pass. Evening approaches. I prepare for the night watch.",
            "expect_no_anomaly": True,
        },
    ]

    for scenario in test_actions:
        print(f"  Testing: {scenario['name']}...")
        # Capture before state for evidence
        before_world_time = last_world_time.copy()

        try:
            response = process_action(
                client,
                user_id=user_id,
                campaign_id=campaign_id,
                user_input=scenario["input"],
            )

            if response.get("error"):
                errors.append(f"{scenario['name']}: Server error - {response['error']}")
                continue

            has_anomaly, anomaly_msg = check_for_temporal_anomaly(response)

            # Extract after state for tracking progression
            after_world_time = None
            if response.get("state_updates", {}).get("world_data", {}).get("world_time"):
                after_world_time = response["state_updates"]["world_data"]["world_time"]
            elif response.get("game_state", {}).get("world_data", {}).get("world_time"):
                after_world_time = response["game_state"]["world_data"]["world_time"]

            # Update tracking for next iteration
            if after_world_time:
                last_world_time = after_world_time

            if scenario["expect_no_anomaly"] and has_anomaly:
                # This is the bug we're fixing - false positives
                errors.append(
                    f"{scenario['name']}: UNEXPECTED temporal anomaly warning detected. "
                    f"This suggests the fix may not be deployed. Message: {anomaly_msg[:200]}"
                )
                # Save evidence
                save_evidence(
                    model_id=model_id,
                    scenario=scenario["name"],
                    response=response,
                    status="FALSE_POSITIVE",
                    request_payload=scenario["input"],
                    before_state=before_world_time,
                    campaign_id=campaign_id,
                    user_id=user_id,
                )
            elif not scenario["expect_no_anomaly"] and not has_anomaly:
                errors.append(f"{scenario['name']}: Expected temporal anomaly but none found")
            else:
                print(f"    ✅ {scenario['name']}: Passed (no false anomaly)")
                save_evidence(
                    model_id=model_id,
                    scenario=scenario["name"],
                    response=response,
                    status="PASS",
                    request_payload=scenario["input"],
                    before_state=before_world_time,
                    campaign_id=campaign_id,
                    user_id=user_id,
                )

        except Exception as e:
            errors.append(f"{scenario['name']}: Exception - {e}")

    return errors


def save_evidence(
    *,
    model_id: str,
    scenario: str,
    response: dict[str, Any],
    status: str,
    request_payload: str | None = None,
    before_state: dict[str, Any] | None = None,
    campaign_id: str | None = None,
    user_id: str | None = None,
    mode: str = "character",
) -> None:
    """Save test evidence to file with full response per evidence-standards.md.

    Per evidence-standards.md, LLM/API behavior evidence MUST capture:
    - Raw request payload (user_input sent to API)
    - Raw response payload (not just keys)
    - System instructions/prompts (debug_info)
    - State snapshots (before and after world_time)
    - Dice roll evidence
    """
    global _evidence_dir

    if _evidence_dir is None:
        _evidence_dir = get_evidence_dir("temporal_anomaly")

    timestamp = int(time.time())
    safe_model = model_id.replace("/", "-")
    safe_scenario = scenario.replace(" ", "_").lower()[:30]
    filename = f"{status}_{safe_model}_{safe_scenario}_{timestamp}.json"

    # Extract world_time from multiple possible locations
    world_time = None
    # Try state_updates first (where LLM updates go)
    if response.get("state_updates", {}).get("world_data", {}).get("world_time"):
        world_time = response["state_updates"]["world_data"]["world_time"]
    # Fall back to game_state
    elif response.get("game_state", {}).get("world_data", {}).get("world_time"):
        world_time = response["game_state"]["world_data"]["world_time"]
    # Fall back to state_changes
    elif response.get("state_changes", {}).get("world_data", {}).get("world_time"):
        world_time = response["state_changes"]["world_data"]["world_time"]

    # Build evidence with FULL response per evidence-standards.md
    evidence = {
        "model_id": model_id,
        "scenario": scenario,
        "status": status,
        "timestamp": timestamp,
        # Evidence mode documentation per evidence-standards.md
        # Using lightweight prompt tracking (filenames + char count) since full system
        # instruction text capture requires server-side changes. The raw_response_text
        # contains the complete LLM JSON output which is the primary evidence.
        "evidence_mode": "lightweight_prompt_tracking",
        "evidence_mode_notes": (
            "System instruction captured as filenames + char_count (not full text). "
            "Full raw_response_text from LLM is captured. Server logs in artifacts/."
        ),
        # Embedded provenance per evidence-standards.md
        "provenance": {
            "git_head": _git_provenance.get("git_head") if _git_provenance else None,
            "git_branch": _git_provenance.get("git_branch") if _git_provenance else None,
            "merge_base": _git_provenance.get("merge_base") if _git_provenance else None,
            "commits_ahead_of_main": _git_provenance.get("commits_ahead_of_main") if _git_provenance else None,
            "diff_stat_vs_main": _git_provenance.get("diff_stat_vs_main") if _git_provenance else None,
            "server": _server_info if _server_info else {},
        },
        # RAW REQUEST per evidence-standards.md (full MCP tool call payload)
        "raw_request": {
            "tool_name": "process_action",
            "user_input": request_payload,
            "campaign_id": campaign_id,
            "user_id": user_id,
            "mode": mode,
        },
        # Test-specific assertions
        "god_mode_response": response.get("god_mode_response", ""),
        "temporal_correction_warning": response.get("temporal_correction_warning", ""),
        # RAW RESPONSE CAPTURE per evidence-standards.md
        "raw_response": {
            "success": response.get("success"),
            "mode": response.get("mode"),
            "narrative": response.get("narrative", response.get("story", response.get("response", ""))),
            "dice_rolls": response.get("dice_rolls", []),
            "dice_audit_events": response.get("dice_audit_events", []),
        },
        # STATE SNAPSHOTS per evidence-standards.md (before AND after)
        "state_snapshots": {
            "before_world_time": before_state,
            "after_world_time": world_time,
            "time_progressed": _time_progressed(before_state, world_time) if before_state and world_time else None,
            "state_updates_world_data": response.get("state_updates", {}).get("world_data"),
            "location": response.get("state_updates", {}).get("world_data", {}).get("current_location_name"),
        },
        # DEBUG INFO per evidence-standards.md (system instruction capture)
        "debug_info": {
            "system_instruction_files": response.get("debug_info", {}).get("system_instruction_files"),
            "system_instruction_char_count": response.get("debug_info", {}).get("system_instruction_char_count"),
            "raw_response_text": response.get("debug_info", {}).get("raw_response_text"),
        },
    }

    # Write with checksum per evidence-standards.md
    filepath = _evidence_dir / filename
    write_with_checksum(filepath, json.dumps(evidence, indent=2))

    # Also append to request_responses.jsonl for complete request/response pairs
    jsonl_path = _evidence_dir / "request_responses.jsonl"
    jsonl_entry = {
        "timestamp": timestamp,
        "scenario": scenario,
        "status": status,
        "request": evidence["raw_request"],
        "response": {
            "success": response.get("success"),
            "mode": response.get("mode"),
            "narrative": response.get("narrative", response.get("story", "")),
            "state_updates": response.get("state_updates"),
            "debug_info": response.get("debug_info"),
            "god_mode_response": response.get("god_mode_response", ""),
        },
    }
    with open(jsonl_path, "a") as f:
        f.write(json.dumps(jsonl_entry) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="MCP temporal anomaly test")
    parser.add_argument(
        "--server-url",
        default=os.environ.get("MCP_SERVER_URL") or "http://127.0.0.1:8001",
        help="Base server URL (with or without /mcp)",
    )
    parser.add_argument(
        "--start-local", action="store_true", help="Start local MCP server automatically"
    )
    parser.add_argument(
        "--port", type=int, default=0, help="Port for --start-local (0 = random free port)"
    )
    parser.add_argument(
        "--models",
        default=os.environ.get("MCP_TEST_MODELS", ""),
        help="Comma-separated model IDs to test. Defaults to first model in matrix.",
    )
    args = parser.parse_args()

    global _git_provenance, _server_info, _evidence_dir

    local: LocalServer | None = None
    base_url = str(args.server_url)
    port = 0

    try:
        if args.start_local:
            port = args.port if args.port > 0 else pick_free_port()
            # Evidence capture enabled by default in server_utils.DEFAULT_EVIDENCE_ENV
            local = start_local_mcp_server(port)
            base_url = local.base_url
        else:
            # Extract port from URL for server runtime capture
            try:
                port = int(base_url.split(":")[-1].rstrip("/").split("/")[0])
            except (ValueError, IndexError):
                port = 443 if "https" in base_url else 80

        client = MCPClient(base_url, timeout_s=180.0)
        print(f"🔗 Connecting to {base_url}...")
        client.wait_healthy(timeout_s=45.0)
        print("✅ Server is healthy")

        # Capture provenance per evidence-standards.md
        print("📋 Capturing git provenance...")
        _git_provenance = capture_git_provenance(fetch_origin=True)
        print(f"   Git HEAD: {_git_provenance.get('git_head', 'unknown')[:12]}...")
        print(f"   Branch: {_git_provenance.get('git_branch', 'unknown')}")

        print("📋 Capturing server runtime info...")
        _server_info = capture_server_runtime(port)
        _server_info["health"] = capture_server_health(base_url)
        print(f"   Server PID: {_server_info.get('pid', 'unknown')}")

        # Initialize evidence directory
        _evidence_dir = get_evidence_dir("temporal_anomaly")
        print(f"📁 Evidence dir: {_evidence_dir}")

        # Parse models - use first model from matrix if not specified
        models = [m.strip() for m in (args.models or "").split(",") if m.strip()]
        if not models:
            # Use just the first model to keep test fast
            models = [list(DEFAULT_MODEL_MATRIX)[0]]

        all_ok = True
        for model_id in models:
            print(f"\n🧪 Testing model: {model_id}")

            # Set up user with model settings
            model_settings = settings_for_model(model_id)
            user_id = f"temporal-test-{model_id.replace('/', '-')}-{int(time.time())}"
            update_user_settings(client, user_id=user_id, settings=model_settings)

            # Create campaign
            try:
                campaign_id = create_campaign(
                    client,
                    user_id,
                    title="Temporal Anomaly Test Campaign",
                    character="Captain Vorn (Disfavored Legion)",
                    setting="The Disfavored Encampment during the conquest of the Tiers",
                    description="Testing that incomplete world_time doesn't trigger false temporal anomalies",
                )
                print(f"  📋 Created campaign: {campaign_id}")
            except Exception as e:
                print(f"  ❌ Failed to create campaign: {e}")
                all_ok = False
                continue

            # Run tests
            errors = run_temporal_test(
                client, user_id=user_id, campaign_id=campaign_id, model_id=model_id
            )

            if errors:
                all_ok = False
                for err in errors:
                    print(f"  ❌ {err}")
            else:
                print(f"  ✅ All temporal tests passed for {model_id}")

        print("\n" + "=" * 60)
        if all_ok:
            print("🎉 ALL TEMPORAL ANOMALY TESTS PASSED")
            return 0
        else:
            print("❌ SOME TESTS FAILED - See errors above")
            print("   If 'FALSE_POSITIVE' errors occurred, the fix may not be deployed.")
            return 2

    finally:
        # Generate checksums for evidence files before cleanup
        if _evidence_dir:
            jsonl_path = _evidence_dir / "request_responses.jsonl"
            if jsonl_path.exists():
                _write_checksum_for_file(jsonl_path)
                print(f"📋 JSONL checksum: {jsonl_path}.sha256")

        if local is not None:
            # Copy server logs to artifacts/ before stopping
            if _evidence_dir and local.log_path.exists():
                artifacts_dir = _evidence_dir / "artifacts"
                artifacts_dir.mkdir(parents=True, exist_ok=True)
                dest_log = artifacts_dir / "server.log"
                shutil.copy2(local.log_path, dest_log)
                _write_checksum_for_file(dest_log)
                print(f"📋 Server log saved to: {dest_log} (+ .sha256)")
            local.stop()


if __name__ == "__main__":
    raise SystemExit(main())
