#!/usr/bin/env python3
"""Run a seeded Gemini 3 Flash d20 chi-square check via local MCP server.

This script relies on the game code to include RNG seeding instructions in the
Gemini code_execution system prompt. It does NOT inject any seeding itself.
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
    _extract_rolls_from_stdout,
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
    evidence_dir = get_evidence_dir("chi_square_seeded")

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

        user_id = f"seeded-chi-{int(time.time())}"
        campaign_id = create_campaign(client, user_id)
        update_user_settings(
            client,
            user_id=user_id,
            settings={"debug_mode": True, "llm_provider": "gemini", "gemini_model": "gemini-3-flash-preview"},
        )

        prompt = (
            "Use code_execution to generate exactly one d20 roll and return it in dice_rolls. "
            "Do not add extra rolls or damage."
        )
        for _ in range(rolls_target):
            result = process_action(
                client,
                user_id=user_id,
                campaign_id=campaign_id,
                user_input=prompt,
            )
            responses.append(result)
            debug_info = result.get("debug_info") if isinstance(result, dict) else None
            stdout = debug_info.get("stdout") if isinstance(debug_info, dict) else None
            parsed = _extract_rolls_from_stdout(stdout)
            if parsed:
                rolls.append(parsed[0])
            time.sleep(0.5)

        chi_square, counts = _chi_square_stat(rolls, faces=20)
        evidence = {
            "rolls": rolls,
            "counts": counts,
            "chi_square": chi_square,
            "threshold": threshold,
            "pass": chi_square <= threshold if rolls else False,
        }
        (evidence_dir / "responses.json").write_text(json.dumps(responses, indent=2))
        (evidence_dir / "result.json").write_text(json.dumps(evidence, indent=2))
        (evidence_dir / "server_log.txt").write_text(str(local.log_path) + "\n")
        print(json.dumps(evidence, indent=2))
        return 0 if evidence["pass"] else 2
    finally:
        local.stop()


if __name__ == "__main__":
    raise SystemExit(main())
