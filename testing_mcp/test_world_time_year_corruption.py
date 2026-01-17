#!/usr/bin/env python3
"""MCP test for world_time year corruption fix.

This test verifies that:
1. Forgotten Realms campaigns use in-game year (1492 DR) NOT real-world year (2026)
2. The world_time.year in state_updates matches the campaign's era

Run:
  cd testing_mcp
  python test_world_time_year_corruption.py --server-url https://mvp-site-app-dev-i6xf2p72ka-uc.a.run.app

Run with local server:
  python test_world_time_year_corruption.py --start-local

RED/GREEN Testing:
  1. RED: Revert game_state_instruction.md to use timestamp_iso → test should FAIL
  2. GREEN: Apply fix (use world_time object) → test should PASS
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from lib import MCPClient
from lib.campaign_utils import create_campaign, process_action
from lib.evidence_utils import (
    capture_provenance,
    get_evidence_dir,
    save_evidence as save_evidence_lib,
    save_request_responses,
)
from lib.model_utils import DEFAULT_MODEL_MATRIX, settings_for_model, update_user_settings
from lib.server_utils import LocalServer, pick_free_port, start_local_mcp_server

# Module-level evidence storage
_provenance: dict[str, Any] | None = None
_captured_requests: list[dict[str, Any]] = []
_evidence_dir: Path | None = None

# Expected in-game year for Forgotten Realms
FORGOTTEN_REALMS_YEAR = 1492

# Real-world years that indicate corruption (the bug)
REAL_WORLD_YEARS = {2024, 2025, 2026, 2027}


def extract_world_time_year(response: dict[str, Any]) -> int | None:
    """Extract world_time.year from response.

    Checks multiple locations where world_time might be stored.
    Returns None if year not found.
    """
    # Try state_updates first (LLM response)
    state_updates = response.get("state_updates", {})
    world_data = state_updates.get("world_data", {})
    world_time = world_data.get("world_time", {})
    if isinstance(world_time, dict) and "year" in world_time:
        return int(world_time["year"])

    # Try game_state (full state)
    game_state = response.get("game_state", {})
    world_data = game_state.get("world_data", {})
    world_time = world_data.get("world_time", {})
    if isinstance(world_time, dict) and "year" in world_time:
        return int(world_time["year"])

    return None


def check_year_corruption(year: int | None) -> tuple[bool, str]:
    """Check if year indicates corruption.

    Returns:
        (is_corrupted, message)
    """
    if year is None:
        return False, "No year found in response (inconclusive)"

    if year in REAL_WORLD_YEARS:
        return True, f"CORRUPTED: year={year} is real-world year, expected ~{FORGOTTEN_REALMS_YEAR} DR"

    if 1400 <= year <= 1600:
        return False, f"OK: year={year} is valid Forgotten Realms era"

    # Unknown era - could be different campaign setting
    return False, f"UNKNOWN: year={year} (not FR era, not real-world)"


def run_year_corruption_test(
    client: MCPClient, *, user_id: str, campaign_id: str, model_id: str
) -> list[str]:
    """Run year corruption tests for a Forgotten Realms campaign.

    Returns list of error messages (empty = all passed).
    """
    errors: list[str] = []

    # Test scenarios - simple actions that should return world_time
    test_actions = [
        {
            "name": "Initial story action",
            "input": "I look around the tavern and take note of who's present.",
        },
        {
            "name": "Time-progressing action",
            "input": "An hour passes as I enjoy my ale. What time is it now?",
        },
        {
            "name": "Next day action",
            "input": "I wake up the next morning refreshed. What's the date today?",
        },
    ]

    for scenario in test_actions:
        print(f"  Testing: {scenario['name']}...")

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

            year = extract_world_time_year(response)
            is_corrupted, message = check_year_corruption(year)

            if is_corrupted:
                errors.append(f"{scenario['name']}: {message}")
                save_evidence(
                    model_id=model_id,
                    scenario=scenario["name"],
                    response=response,
                    status="YEAR_CORRUPTED",
                    request_payload=scenario["input"],
                    campaign_id=campaign_id,
                    user_id=user_id,
                    year_found=year,
                )
                print(f"    ❌ {message}")
            else:
                print(f"    ✅ {message}")
                save_evidence(
                    model_id=model_id,
                    scenario=scenario["name"],
                    response=response,
                    status="PASS",
                    request_payload=scenario["input"],
                    campaign_id=campaign_id,
                    user_id=user_id,
                    year_found=year,
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
    campaign_id: str | None = None,
    user_id: str | None = None,
    year_found: int | None = None,
) -> None:
    """Save test evidence to file per evidence-standards.md."""
    global _evidence_dir

    if _evidence_dir is None:
        _evidence_dir = get_evidence_dir("world_time_year_corruption")

    timestamp = int(time.time())
    safe_model = model_id.replace("/", "-")
    safe_scenario = scenario.replace(" ", "_").lower()[:30]
    filename = f"{status}_{safe_model}_{safe_scenario}_{timestamp}.json"

    # Extract world_time from response
    world_time = None
    state_updates = response.get("state_updates", {})
    world_data = state_updates.get("world_data", {})
    if world_data.get("world_time"):
        world_time = world_data["world_time"]

    evidence = {
        "model_id": model_id,
        "scenario": scenario,
        "status": status,
        "timestamp": timestamp,
        "test_name": "world_time_year_corruption",
        "provenance": _provenance if _provenance else {},
        "raw_request": {
            "tool_name": "process_action",
            "user_input": request_payload,
            "campaign_id": campaign_id,
            "user_id": user_id,
        },
        "year_analysis": {
            "year_found": year_found,
            "expected_era": "Forgotten Realms (~1492 DR)",
            "is_real_world_year": year_found in REAL_WORLD_YEARS if year_found else None,
        },
        "world_time_extracted": world_time,
        "raw_response": {
            "success": response.get("success"),
            "mode": response.get("mode"),
            "narrative": response.get("narrative", response.get("story", ""))[:500],
            "state_updates_world_data": state_updates.get("world_data"),
        },
        "debug_info": {
            "system_instruction_files": response.get("debug_info", {}).get(
                "system_instruction_files"
            ),
            "system_instruction_char_count": response.get("debug_info", {}).get(
                "system_instruction_char_count"
            ),
        },
    }

    save_evidence_lib(_evidence_dir, evidence, filename)
    _captured_requests.append(
        {
            "timestamp": timestamp,
            "scenario": scenario,
            "status": status,
            "year_found": year_found,
            "request": evidence["raw_request"],
        }
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="MCP world_time year corruption test")
    parser.add_argument(
        "--server-url",
        default=os.environ.get("MCP_SERVER_URL") or "http://127.0.0.1:8001",
        help="Base server URL",
    )
    parser.add_argument(
        "--start-local", action="store_true", help="Start local MCP server automatically"
    )
    parser.add_argument(
        "--port", type=int, default=0, help="Port for --start-local (0 = random)"
    )
    parser.add_argument(
        "--models",
        default=os.environ.get("MCP_TEST_MODELS", ""),
        help="Comma-separated model IDs to test",
    )
    args = parser.parse_args()

    global _provenance, _evidence_dir

    local: LocalServer | None = None
    base_url = str(args.server_url)

    try:
        if args.start_local:
            port = args.port if args.port > 0 else pick_free_port()
            local = start_local_mcp_server(port)
            base_url = local.base_url

        client = MCPClient(base_url, timeout_s=180.0)
        print(f"🔗 Connecting to {base_url}...")
        client.wait_healthy(timeout_s=45.0)
        print("✅ Server is healthy")

        print("📋 Capturing provenance...")
        _provenance = capture_provenance(base_url)

        _evidence_dir = get_evidence_dir("world_time_year_corruption")
        print(f"📁 Evidence dir: {_evidence_dir}")

        models = [m.strip() for m in (args.models or "").split(",") if m.strip()]
        if not models:
            models = [list(DEFAULT_MODEL_MATRIX)[0]]

        all_ok = True
        for model_id in models:
            print(f"\n🧪 Testing model: {model_id}")

            model_settings = settings_for_model(model_id)
            user_id = f"year-corruption-test-{model_id.replace('/', '-')}-{int(time.time())}"
            update_user_settings(client, user_id=user_id, settings=model_settings)

            # Create Forgotten Realms campaign WITH explicit year context
            # This ensures LLM has clear instruction on what year to use
            try:
                campaign_id = create_campaign(
                    client,
                    user_id,
                    title="Year Corruption Test - Forgotten Realms",
                    character="Varis the Elf Ranger (Forgotten Realms, 1492 DR)",
                    setting="The Sword Coast, Forgotten Realms, 1492 DR - Waterdeep's Yawning Portal tavern",
                    description="Test that world_time uses in-game year (1492 DR) not real-world year (2026)",
                )
                print(f"  📋 Created campaign: {campaign_id}")
            except Exception as e:
                print(f"  ❌ Failed to create campaign: {e}")
                all_ok = False
                continue

            errors = run_year_corruption_test(
                client, user_id=user_id, campaign_id=campaign_id, model_id=model_id
            )

            if errors:
                all_ok = False
                for err in errors:
                    print(f"  ❌ {err}")
            else:
                print(f"  ✅ All year corruption tests passed for {model_id}")

        print("\n" + "=" * 60)
        if all_ok:
            print("🎉 ALL YEAR CORRUPTION TESTS PASSED")
            print("   world_time.year correctly uses in-game year (1492 DR)")
            return 0
        else:
            print("❌ YEAR CORRUPTION DETECTED")
            print("   world_time.year is using real-world year (2026) instead of 1492 DR")
            print("   This indicates the prompt fix is NOT deployed.")
            return 2

    finally:
        if _evidence_dir and _captured_requests:
            try:
                save_request_responses(_evidence_dir, _captured_requests)
                print(f"📋 Captured {len(_captured_requests)} request/response pairs")
            except Exception as exc:
                print(f"⚠️ Failed to write request_responses.jsonl: {exc}")

        if local is not None:
            if _evidence_dir and local.log_path.exists():
                artifacts_dir = _evidence_dir / "artifacts"
                artifacts_dir.mkdir(parents=True, exist_ok=True)
                dest_log = artifacts_dir / "server.log"
                shutil.copy2(local.log_path, dest_log)
                # Generate checksum
                content = dest_log.read_bytes()
                sha256_hash = hashlib.sha256(content).hexdigest()
                checksum_file = Path(str(dest_log) + ".sha256")
                checksum_file.write_text(f"{sha256_hash}  {dest_log.name}\n")
                print(f"📋 Server log saved to: {dest_log}")
            local.stop()


if __name__ == "__main__":
    raise SystemExit(main())
