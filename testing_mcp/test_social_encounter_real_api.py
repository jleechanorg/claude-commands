#!/usr/bin/env python3
"""MCP social-encounter dice coverage against a running MCP server.

This is a server-level test: it calls MCP tools over HTTP and validates that
social skill checks produce dice_rolls.

Run:
  cd testing_mcp
  python test_social_encounter_real_api.py --server-url http://127.0.0.1:8001
"""

from __future__ import annotations

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))

import argparse
import os
import time
from typing import Any

from mcp_client import MCPClient
from lib.server_utils import LocalServer, pick_free_port, start_local_mcp_server
from lib.model_utils import DEFAULT_MODEL_MATRIX, settings_for_model, update_user_settings


def _expect_dice(payload: dict[str, Any], *, label: str) -> list[str]:
    errors: list[str] = []
    if payload.get("error"):
        errors.append(f"{label}: error={payload['error']}")
        return errors

    dice_rolls = payload.get("dice_rolls") or []
    if not isinstance(dice_rolls, list):
        return [f"{label}: dice_rolls not list"]

    if len(dice_rolls) < 1:
        errors.append(f"{label}: expected dice_rolls >= 1, got 0")

    joined = "\n".join(str(x) for x in dice_rolls)
    if "1d20" not in joined:
        errors.append(f"{label}: expected dice_rolls to contain '1d20'")

    return errors




def main() -> int:
    parser = argparse.ArgumentParser(description="MCP social encounter dice coverage")
    parser.add_argument(
        "--server-url",
        default=os.environ.get("MCP_SERVER_URL") or "http://127.0.0.1:8001",
        help="Base server URL (with or without /mcp)",
    )
    parser.add_argument("--start-local", action="store_true", help="Start local MCP server automatically")
    parser.add_argument("--port", type=int, default=0, help="Port for --start-local (0 = random free port)")
    parser.add_argument(
        "--models",
        default=os.environ.get("MCP_TEST_MODELS", ""),
        help=(
            "Comma-separated model IDs to test (e.g. "
            "gemini-3-flash-preview,qwen-3-235b-a22b-instruct-2507). "
            "Defaults to a Gemini+Qwen matrix."
        ),
    )
    args = parser.parse_args()

    local: LocalServer | None = None
    base_url = str(args.server_url)

    try:
        if args.start_local:
            port = args.port if args.port > 0 else pick_free_port()
            local = start_local_mcp_server(port)
            base_url = local.base_url

        client = MCPClient(base_url, timeout_s=180.0)
        client.wait_healthy(timeout_s=45.0)

        models = [m.strip() for m in (args.models or "").split(",") if m.strip()]
        if not models:
            models = list(DEFAULT_MODEL_MATRIX)

        scenarios = [
            (
                "Intimidation",
                "I stare down the guard and demand entry. Make an Intimidation check.",
            ),
            (
                "Deception",
                "I lie smoothly about our business here. Make a Deception check.",
            ),
        ]

        ok = True
        for model_id in models:
            model_settings = settings_for_model(model_id)
            user_id = f"mcp-social-{model_id.replace('/', '-')}-{int(time.time())}"
            update_user_settings(client, user_id=user_id, settings=model_settings)
            created = client.tools_call(
                "create_campaign",
                {
                    "user_id": user_id,
                    "title": "MCP Social Dice Campaign",
                    "character": "Lyra the Rogue (CHA 14)",
                    "setting": "A tense parley in a candlelit tavern",
                },
            )
            campaign_id = created.get("campaign_id") or created.get("campaignId")
            if not isinstance(campaign_id, str) or not campaign_id:
                print(f"❌ {model_id} :: create_campaign returned unexpected payload: {created}")
                ok = False
                continue

            for label, user_input in scenarios:
                payload = client.tools_call(
                    "process_action",
                    {
                        "user_id": user_id,
                        "campaign_id": campaign_id,
                        "user_input": user_input,
                        "mode": "character",
                    },
                )
                errors = _expect_dice(payload, label=label)
                if errors:
                    ok = False
                    print(f"❌ {model_id} :: {label}: {errors}")
                else:
                    dice_count = len(payload.get("dice_rolls") or [])
                    print(f"✅ {model_id} :: {label}: dice_rolls={dice_count}")

        return 0 if ok else 2
    finally:
        if local is not None:
            local.stop()


if __name__ == "__main__":
    raise SystemExit(main())
