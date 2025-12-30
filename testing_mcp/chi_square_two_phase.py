#!/usr/bin/env python3
"""Run a native_two_phase (Gemini 2.0 Flash) d20 chi-square check via local MCP server.

This script tests the native_two_phase dice strategy where the server executes
dice tools (using Python's random module with OS-seeded RNG).

Unlike code_execution (Gemini 3.x), the LLM does NOT generate RNG code - the server
handles dice rolling directly, ensuring uniform distribution.
"""

from __future__ import annotations

import json
import os
import socket
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from mcp_client import MCPClient  # noqa: E402
from test_dice_rolls_comprehensive import (  # noqa: E402
    _chi_square_stat,
    create_campaign,
    start_local_mcp_server,
    update_user_settings,
)
from lib.evidence_utils import get_evidence_dir  # noqa: E402

PROJECT_ROOT = Path(__file__).parent.parent


def _pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def process_action(client: MCPClient, *, user_id: str, campaign_id: str, user_input: str) -> dict[str, Any]:
    return client.tools_call(
        "process_action",
        {"user_id": user_id, "campaign_id": campaign_id, "user_input": user_input, "mode": "character"},
    )


def main() -> int:
    rolls_target = int(os.environ.get("CHI_SQUARE_ROLLS", "20"))
    threshold = float(os.environ.get("CHI_SQUARE_THRESHOLD", "46"))

    # Evidence stored per evidence-standards.md: /tmp/<repo>/<branch>/<work>/<timestamp>/
    evidence_dir = get_evidence_dir("chi_square_two_phase")

    port = _pick_free_port()
    env_overrides: dict[str, str] = {
        "MOCK_SERVICES_MODE": "false",
        "TESTING": "false",
        "FORCE_TEST_MODEL": "false",
        "FAST_TESTS": "false",
        "CAPTURE_EVIDENCE": "true",
        "CAPTURE_RAW_LLM": "true",
        "CAPTURE_RAW_LLM_MAX_CHARS": "80000",
    }

    local = start_local_mcp_server(port, env_overrides=env_overrides, log_dir=evidence_dir)

    rolls: list[int] = []
    responses: list[dict[str, Any]] = []

    try:
        client = MCPClient(local.base_url, timeout_s=60.0)
        client.wait_healthy(timeout_s=60.0)

        user_id = f"two-phase-chi-{int(time.time())}"
        campaign_id = create_campaign(client, user_id)

        # Use gemini-2.0-flash which uses native_two_phase strategy
        update_user_settings(
            client,
            user_id=user_id,
            settings={"debug_mode": True, "llm_provider": "gemini", "gemini_model": "gemini-2.0-flash"},
        )

        prompt = "Roll a single d20 for a skill check. Just one roll."

        print(f"Running {rolls_target} rolls with gemini-2.0-flash (native_two_phase)...")
        for i in range(rolls_target):
            result = process_action(
                client,
                user_id=user_id,
                campaign_id=campaign_id,
                user_input=prompt,
            )
            responses.append(result)

            # For native_two_phase, extract rolls from dice_audit_events
            dice_audit = result.get("dice_audit_events", [])
            if dice_audit:
                for event in dice_audit:
                    event_rolls = event.get("rolls", [])
                    if event_rolls:
                        rolls.extend(event_rolls)

            debug_info = result.get("debug_info", {})
            strategy = debug_info.get("dice_strategy", result.get("dice_strategy", "unknown"))

            print(f"  Roll {i+1}: strategy={strategy}, audit_events={len(dice_audit)}, rolls_so_far={len(rolls)}")
            time.sleep(0.3)

        # Calculate chi-square
        if rolls:
            chi_square, counts = _chi_square_stat(rolls, faces=20)
        else:
            chi_square = 0.0
            counts = {}

        evidence = {
            "model": "gemini-2.0-flash",
            "strategy": "native_two_phase",
            "rolls": rolls,
            "counts": counts,
            "chi_square": chi_square,
            "threshold": threshold,
            "pass": chi_square <= threshold if rolls else False,
        }

        (evidence_dir / "responses.json").write_text(json.dumps(responses, indent=2))
        (evidence_dir / "result.json").write_text(json.dumps(evidence, indent=2))
        (evidence_dir / "server_log.txt").write_text(str(local.log_path) + "\n")

        print()
        print(json.dumps(evidence, indent=2))

        return 0 if evidence["pass"] else 2
    finally:
        local.stop()


if __name__ == "__main__":
    raise SystemExit(main())
