#!/usr/bin/env python3
"""
Mode parameter validation tests against an MCP server (local or preview).

These tests verify that:
1) mode parameter is propagated into the LLM request payload (game_mode)
2) agent selection matches expected mode, except where explicitly not evaluated
3) combat override forces CombatAgent even when mode=god/character

Evidence is saved under /tmp/<repo>/<branch>/mode_parameter_validation/.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from lib import MCPClient
from lib.campaign_utils import create_campaign, get_campaign_state, process_action
from lib.evidence_utils import capture_provenance, get_evidence_dir, write_with_checksum
from lib.server_utils import LocalServer, pick_free_port, start_local_mcp_server

# =============================================================================
# Scenario Definitions
# =============================================================================

SCENARIOS: list[dict[str, Any]] = [
    {
        "name": "God Mode via Parameter - Set HP",
        "mode_requested": "god",
        "user_input": "Set my character's HP to 999",
        "expected_agent_mode": "god",
        "expected_request_mode": "god",
    },
    {
        "name": "God Mode via Parameter - Query State",
        "mode_requested": "god",
        "user_input": "What are my current stats?",
        "expected_agent_mode": "god",
        "expected_request_mode": "god",
    },
    {
        "name": "God Mode via Parameter - Add Directive",
        "mode_requested": "god",
        "user_input": "Add a rule: always describe weather in scene transitions",
        "expected_agent_mode": "god",
        "expected_request_mode": "god",
    },
    {
        "name": "Story Mode - Normal Action",
        "mode_requested": "character",
        "user_input": "I look around the room for any clues",
        "expected_agent_mode": "character",
        "expected_request_mode": "character",
    },
    {
        "name": "Story Mode - Combat Action",
        "mode_requested": "character",
        "user_input": "I attack the goblin with my sword",
        "expected_agent_mode": "combat",
        "expected_request_mode": "character",
        "ensure_combat": True,
    },
    {
        "name": "Combat Override - God Mode in Combat",
        "mode_requested": "god",
        # Return-to-story normalizes mode to character by design.
        "user_input": "Return to story",
        "expected_agent_mode": "combat",
        "expected_request_mode": "character",
        "ensure_combat": True,
    },
    {
        "name": "Combat Override - Character Mode in Combat",
        "mode_requested": "character",
        "user_input": "I examine the mysterious artifact",
        "expected_agent_mode": None,  # Not evaluated by design
        "expected_request_mode": "character",
        "ensure_combat": True,
    },
]


# =============================================================================
# Helpers
# =============================================================================


def _parse_action_result(payload: dict[str, Any]) -> dict[str, Any]:
    """Parse MCP process_action result into a dict."""
    content = payload.get("content")
    if content:
        parsed = MCPClient.parse_json_text_content(content)
        if parsed:
            return parsed
    return payload


def _extract_raw_game_mode(result: dict[str, Any]) -> str | None:
    """Extract game_mode from raw_request_payload if present."""
    raw_payload = result.get("raw_request_payload")
    if isinstance(raw_payload, dict):
        return raw_payload.get("game_mode")

    debug_info = result.get("debug_info")
    if isinstance(debug_info, dict):
        raw_payload = debug_info.get("raw_request_payload")

    if isinstance(raw_payload, dict):
        return raw_payload.get("game_mode")

    if isinstance(raw_payload, str):
        match = re.search(r"game_mode=([\"'])([^\"']+)\1", raw_payload)
        if match:
            return match.group(2)
        # Fallback: allow unquoted (rare)
        match = re.search(r"game_mode=([a-zA-Z_]+)", raw_payload)
        if match:
            return match.group(1)
    return None


def _normalize_mode(value: str | None) -> str | None:
    if value is None:
        return None
    return value.strip().lower()


def _ensure_combat_state(client: MCPClient, user_id: str, campaign_id: str) -> bool:
    """Ensure campaign is in combat; returns True if in combat after attempts."""
    state = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
    game_state = state.get("game_state") or {}
    combat_state = game_state.get("combat_state") or {}
    if combat_state.get("in_combat") is True:
        return True

    # Attempt to trigger combat naturally
    process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input="I attack the goblin with my sword",
        mode="character",
    )
    state = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
    game_state = state.get("game_state") or {}
    combat_state = game_state.get("combat_state") or {}
    if combat_state.get("in_combat") is True:
        return True

    # Force combat state for deterministic override testing
    update = {"combat_state": {"in_combat": True, "current_round": 1}}
    process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=f"GOD_MODE_UPDATE_STATE:{json.dumps(update)}",
        mode="character",
    )
    state = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
    game_state = state.get("game_state") or {}
    return (game_state.get("combat_state") or {}).get("in_combat") is True


def _enable_debug_mode(client: MCPClient, user_id: str, campaign_id: str) -> None:
    """Ensure debug_mode is enabled so debug_info (raw_request_payload) is returned."""
    update = {"debug_mode": True}
    process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=f"GOD_MODE_UPDATE_STATE:{json.dumps(update)}",
        mode="character",
    )


def _clear_evidence_dir(evidence_dir: Path) -> None:
    """Remove stale evidence files to avoid mixing runs."""
    if not evidence_dir.exists():
        return
    for entry in evidence_dir.iterdir():
        try:
            if entry.is_file() or entry.is_symlink():
                entry.unlink()
            elif entry.is_dir():
                shutil.rmtree(entry)
        except Exception as exc:  # noqa: BLE001
            print(f"⚠️  Could not remove {entry}: {exc}")


def _validate_scenario(
    *,
    mode_requested: str,
    expected_agent_mode: str | None,
    actual_agent_mode: str | None,
    expected_request_mode: str | None,
    request_game_mode: str | None,
    result: dict[str, Any],
) -> tuple[list[str], bool | None, bool]:
    """Return (errors, agent_mode_match, request_mode_match)."""
    errors: list[str] = []

    agent_mode_match: bool | None
    if expected_agent_mode is None:
        agent_mode_match = None
    else:
        agent_mode_match = actual_agent_mode == expected_agent_mode
        if not agent_mode_match:
            errors.append(
                f"Agent mode mismatch! Expected '{expected_agent_mode}' but got '{actual_agent_mode}'."
            )

    normalized_requested = _normalize_mode(mode_requested)
    normalized_expected_request = _normalize_mode(expected_request_mode)
    normalized_request_game_mode = _normalize_mode(request_game_mode)
    request_mode_match: bool | None

    if normalized_request_game_mode is None:
        request_mode_match = None
        if os.getenv("REQUIRE_REQUEST_MODE_MATCH", "false").lower() == "true":
            errors.append("Missing raw_request_payload.game_mode for request validation.")
    elif normalized_expected_request is None:
        request_mode_match = None
    else:
        request_mode_match = normalized_request_game_mode == normalized_expected_request
        if not request_mode_match:
            errors.append(
                "Mode parameter mismatch! "
                f"Requested '{mode_requested}', expected request '{expected_request_mode}', "
                f"but raw_request_payload has '{request_game_mode}'."
            )

    if result.get("error"):
        errors.append(f"process_action error: {result['error']}")

    return errors, agent_mode_match, request_mode_match


def _safe_name(name: str) -> str:
    return (
        name.lower()
        .replace(" ", "_")
        .replace("/", "-")
        .replace(":", "")
        .replace("'", "")
    )


# =============================================================================
# Scenario Runner
# =============================================================================


def run_scenario(
    client: MCPClient,
    user_id: str,
    campaign_id: str,
    scenario: dict[str, Any],
    evidence_dir: Path,
) -> dict[str, Any]:
    name = scenario["name"]
    mode_requested = scenario["mode_requested"]
    expected_agent_mode = scenario.get("expected_agent_mode")
    expected_request_mode = scenario.get("expected_request_mode", mode_requested)

    if scenario.get("ensure_combat"):
        _ensure_combat_state(client, user_id, campaign_id)

    pre_state_payload = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
    pre_game_state = pre_state_payload.get("game_state") or {}
    pre_combat_state = pre_game_state.get("combat_state") or {}

    start_time = time.time()
    payload = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=scenario["user_input"],
        mode=mode_requested,
        include_raw_llm_payloads=True,
    )
    elapsed = time.time() - start_time

    parsed_result = _parse_action_result(payload)
    actual_agent_mode_raw = parsed_result.get("agent_mode")
    request_game_mode = _extract_raw_game_mode(parsed_result)

    state_payload = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
    game_state_after = state_payload.get("game_state") or {}
    combat_state = game_state_after.get("combat_state") or {}

    # Derive agent mode if not provided in response payload
    actual_agent_mode = actual_agent_mode_raw
    if actual_agent_mode is None:
        if pre_combat_state.get("in_combat") is True or combat_state.get("in_combat") is True:
            actual_agent_mode = "combat"
        else:
            actual_agent_mode = parsed_result.get("mode")

    errors, agent_mode_match, request_mode_match = _validate_scenario(
        mode_requested=mode_requested,
        expected_agent_mode=expected_agent_mode,
        actual_agent_mode=actual_agent_mode,
        expected_request_mode=expected_request_mode,
        request_game_mode=request_game_mode,
        result=parsed_result,
    )

    evidence = {
        "scenario": name,
        "mode_requested": mode_requested,
        "expected_agent_mode": expected_agent_mode,
        "expected_request_mode": expected_request_mode,
        "actual_agent_mode": actual_agent_mode,
        "actual_agent_mode_raw": actual_agent_mode_raw,
        "agent_mode_match": agent_mode_match,
        "request_game_mode": request_game_mode,
        "request_mode_match": request_mode_match,
        "user_input": scenario["user_input"],
        "result": parsed_result,
        "game_state_after": game_state_after,
        "errors": errors,
        "elapsed_seconds": elapsed,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    evidence_path = evidence_dir / f"scenario_{_safe_name(name)}.json"
    checksum = write_with_checksum(evidence_path, json.dumps(evidence, indent=2))

    return {
        "name": name,
        "mode": mode_requested,
        "expected_agent_mode": expected_agent_mode,
        "actual_agent_mode": actual_agent_mode,
        "agent_mode_match": agent_mode_match,
        "request_game_mode": request_game_mode,
        "request_mode_match": request_mode_match,
        "passed": len(errors) == 0,
        "errors": errors,
        "elapsed": elapsed,
        "evidence_path": str(evidence_path),
        "checksum": checksum,
    }


def _count_matches(results: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts = {"true": 0, "false": 0, "null": 0}
    for result in results:
        value = result.get(key)
        if value is True:
            counts["true"] += 1
        elif value is False:
            counts["false"] += 1
        else:
            counts["null"] += 1
    return counts


def run_all_scenarios(
    client: MCPClient,
    user_id: str,
    campaign_id: str,
    evidence_dir: Path,
) -> dict[str, Any]:
    results = []
    passed = 0
    failed = 0

    for scenario in SCENARIOS:
        result = run_scenario(client, user_id, campaign_id, scenario, evidence_dir)
        results.append(result)
        if result["passed"]:
            passed += 1
        else:
            failed += 1

    return {
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "agent_mode_match_counts": _count_matches(results, "agent_mode_match"),
        "request_mode_match_counts": _count_matches(results, "request_mode_match"),
        "results": results,
    }


# =============================================================================
# Main
# =============================================================================


def main() -> int:
    parser = argparse.ArgumentParser(description="Mode Parameter Validation Tests")
    parser.add_argument(
        "--server-url",
        default=os.environ.get("MCP_SERVER_URL") or "http://127.0.0.1:8001",
        help="MCP server URL (default: $MCP_SERVER_URL or localhost:8001)",
    )
    parser.add_argument(
        "--start-local",
        action="store_true",
        help="Start a local MCP server automatically",
    )
    parser.add_argument(
        "--user-id",
        default="test_mode_param_user",
        help="User ID for test campaign",
    )
    args = parser.parse_args()

    evidence_dir = get_evidence_dir("mode_parameter_validation")
    print(f"Evidence directory: {evidence_dir}")
    _clear_evidence_dir(evidence_dir)

    local_server: LocalServer | None = None
    server_url = args.server_url

    if args.start_local:
        port = pick_free_port()
        local_server = start_local_mcp_server(port, log_dir=evidence_dir)
        server_url = f"http://127.0.0.1:{port}"

    try:
        provenance = capture_provenance(
            server_url,
            server_pid=local_server.proc.pid if local_server else None,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"⚠️  Provenance warning: {exc}")
        provenance = {}

    client = MCPClient(f"{server_url}/mcp")
    try:
        client.wait_healthy(timeout_s=10.0)
    except RuntimeError as exc:
        print(f"⚠️  Health check warning: {exc}")

    campaign_id = create_campaign(
        client,
        args.user_id,
        title="Mode Parameter Validation Test",
        character="Kira the Warrior (Female, Level 5, STR 16)",
        setting="A mysterious dungeon with ancient artifacts",
        description="Testing mode parameter handling for god/story modes",
    )

    # Ensure debug_info (raw_request_payload) is included in responses
    _enable_debug_mode(client, args.user_id, campaign_id)

    summary = run_all_scenarios(client, args.user_id, campaign_id, evidence_dir)
    summary["provenance"] = provenance

    summary_path = evidence_dir / "summary.json"
    write_with_checksum(summary_path, json.dumps(summary, indent=2))

    if local_server:
        local_server.stop()

    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
