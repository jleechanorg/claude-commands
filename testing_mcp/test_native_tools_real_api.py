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
import json
import os
import time
from datetime import UTC, datetime

from lib import MCPClient


def main() -> int:
    parser = argparse.ArgumentParser(description="MCP smoke test (no direct provider calls)")
    parser.add_argument(
        "--server-url",
        default=os.environ.get("MCP_SERVER_URL") or "http://127.0.0.1:8001",
        help="Base server URL (with or without /mcp)",
    )
    parser.add_argument(
        "--evidence-dir",
        default=os.environ.get("MCP_EVIDENCE_DIR", ""),
        help="Directory to write evidence artifacts (defaults to /tmp/worldarchitect/<timestamp>).",
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
    # Enable debug_mode for evidence when supported.
    client.tools_call(
        "update_user_settings",
        {"user_id": user_id, "settings": {"debug_mode": True}},
    )
    # Create campaign with god_mode to skip character creation and go straight to StoryModeAgent
    # StoryModeAgent loads game_state_instruction.md which contains the tool_requests guidance fix
    # CharacterCreationAgent doesn't load game_state_instruction.md and explicitly says "DO NOT roll dice"
    payload = client.tools_call(
        "create_campaign",
        {
            "user_id": user_id,
            "title": "MCP Smoke Campaign",
            "god_mode": {
                "title": "MCP Smoke Campaign",
                "setting": "A dungeon entrance",
                "character": {
                    "name": "Test Fighter",
                    "race": "Human",
                    "class": "Fighter",
                    "level": 5,
                    "hp_current": 50,
                    "hp_max": 50,
                    "armor_class": 18,
                    "attributes": {
                        "strength": 16,
                        "dexterity": 14,
                        "constitution": 15,
                        "intelligence": 10,
                        "wisdom": 12,
                        "charisma": 8,
                    },
                },
            },
        },
    )
    campaign_id = payload.get("campaign_id") or payload.get("campaignId")
    if not isinstance(campaign_id, str) or not campaign_id:
        print(f"❌ create_campaign returned unexpected payload: {payload}")
        return 2

    print(f"✅ create_campaign ok: {campaign_id}")
    
    # Verify we're in story mode (god_mode campaigns should skip character creation)
    state = client.tools_call(
        "get_campaign_state",
        {"user_id": user_id, "campaign_id": campaign_id},
    )
    creation_in_progress = state.get("custom_campaign_state", {}).get("character_creation_in_progress", True)
    if creation_in_progress:
        # If still in creation, complete it with a story action
        completion_result = client.tools_call(
            "process_action",
            {
                "user_id": user_id,
                "campaign_id": campaign_id,
                "user_input": "Yes, let's play",
                "mode": "character",
            },
        )
        debug_info = completion_result.get("debug_info", {})
        if debug_info.get("agent_name") != "StoryModeAgent":
            print(f"⚠️ Warning: Still using {debug_info.get('agent_name')} after completion attempt")

    # Use explicit combat action that MUST trigger dice rolls
    # This tests the tool_requests guidance from game_state_instruction.md
    action = "I attack the goblin with my longsword. Roll to hit and damage."
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
    if not dice_rolls:
        print("❌ process_action returned no dice_rolls (expected at least one)")
        return 2

    dice_audit_events = payload2.get("dice_audit_events") or []
    debug_info = payload2.get("debug_info") or {}
    if not isinstance(dice_audit_events, list):
        dice_audit_events = []
    if not isinstance(debug_info, dict):
        debug_info = {}

    dice_tool_names = {"roll_dice", "roll_attack", "roll_skill_check", "roll_saving_throw"}
    tool_event = any(
        isinstance(event, dict)
        and isinstance(event.get("tool"), str)
        and event.get("tool") in dice_tool_names
        for event in dice_audit_events
    )
    code_exec_event = any(
        isinstance(event, dict)
        and event.get("source") == "code_execution"
        for event in dice_audit_events
    )
    code_exec_used = bool(debug_info.get("code_execution_used"))

    if dice_rolls and not (tool_event or code_exec_event or code_exec_used):
        print("❌ dice_rolls present but no tool/code_execution evidence in response")
        return 2

    print(f"✅ process_action ok (dice_rolls={len(dice_rolls)})")

    # Evidence capture
    evidence_root = args.evidence_dir.strip()
    if not evidence_root:
        evidence_root = "/tmp/worldarchitect/mcp_real_mode_preview_" + datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    evidence_dir = Path(evidence_root)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "campaign_create.json").write_text(json.dumps(payload, indent=2))
    (evidence_dir / "process_action.json").write_text(json.dumps(payload2, indent=2))
    (evidence_dir / "evidence_summary.json").write_text(
        json.dumps(
            {
                "server_url": str(args.server_url),
                "user_id": user_id,
                "campaign_id": campaign_id,
                "dice_rolls": dice_rolls,
                "dice_audit_events_count": len(dice_audit_events),
                "tool_event_present": tool_event,
                "code_execution_event_present": code_exec_event,
                "code_execution_used": code_exec_used,
            },
            indent=2,
        )
    )
    print(f"📁 Evidence saved to: {evidence_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
