#!/usr/bin/env python3
"""MCP smoke tests (tools/list + basic workflow) against a running MCP server.

Historically this file called provider SDKs directly (Gemini/Cerebras/OpenRouter).
That made the *test runner* require provider API keys.

Now it tests via MCP (`/mcp`) so the runner itself does not need provider keys.
The target server (preview or local) is responsible for provider configuration.

Run:
  cd testing_mcp
  python test_native_tools_real_api.py --server-url http://127.0.0.1:8001

Tip:
  For a deploy preview, set:
    export MCP_SERVER_URL=https://<preview-app>.run.app
"""

from __future__ import annotations

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))

import argparse
import os
import time

from mcp_client import MCPClient


def main() -> int:
    parser = argparse.ArgumentParser(description="MCP smoke test (no direct provider calls)")
    parser.add_argument(
        "--server-url",
        default=os.environ.get("MCP_SERVER_URL") or "http://127.0.0.1:8001",
        help="Base server URL (with or without /mcp)",
    )
    args = parser.parse_args()

    client = MCPClient(str(args.server_url), timeout_s=120.0)
    client.wait_healthy(timeout_s=45.0)

    tools = client.tools_list()
    names = {t.get("name") for t in tools if isinstance(t, dict)}

    required = {
        "create_campaign",
        "get_campaign_state",
        "process_action",
        "update_campaign",
        "export_campaign",
        "get_campaigns_list",
        "get_user_settings",
        "update_user_settings",
    }

    missing = sorted(required - names)
    if missing:
        print(f"❌ tools/list missing: {missing}")
        return 2

    print(f"✅ tools/list returned {len(tools)} tool(s)")

    user_id = f"mcp-smoke-{int(time.time())}"
    payload = client.tools_call(
        "create_campaign",
        {"user_id": user_id, "title": "MCP Smoke Campaign"},
    )
    campaign_id = payload.get("campaign_id") or payload.get("campaignId")
    if not isinstance(campaign_id, str) or not campaign_id:
        print(f"❌ create_campaign returned unexpected payload: {payload}")
        return 2

    print(f"✅ create_campaign ok: {campaign_id}")

    action = "I look around for threats and prepare for combat."
    payload2 = client.tools_call(
        "process_action",
        {"user_id": user_id, "campaign_id": campaign_id, "user_input": action, "mode": "character"},
    )
    if payload2.get("error"):
        print(f"❌ process_action error: {payload2['error']}")
        return 2

    dice_rolls = payload2.get("dice_rolls") or []
    if not isinstance(dice_rolls, list):
        print(f"❌ process_action dice_rolls not list: {type(dice_rolls)}")
        return 2

    print(f"✅ process_action ok (dice_rolls={len(dice_rolls)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
