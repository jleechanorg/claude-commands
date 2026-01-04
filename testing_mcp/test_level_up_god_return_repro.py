#!/usr/bin/env python3
"""Repro test for level-up prompt on GOD MODE return to story.

This test exercises the explicit "GOD MODE: return to story" transition and
verifies whether level-up visibility and choices are present in the response.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from lib import (
    MCPClient,
    capture_provenance,
    create_evidence_bundle,
    get_evidence_dir,
    pick_free_port,
    start_local_mcp_server,
)
from lib.campaign_utils import create_campaign, get_campaign_state, process_action


def _extract_response_text(result: dict[str, Any]) -> str:
    for key in ("response", "narrative"):
        text = result.get(key)
        if isinstance(text, str) and text.strip():
            return text
    story = result.get("story")
    if isinstance(story, list):
        parts = []
        for entry in story:
            if isinstance(entry, dict) and isinstance(entry.get("text"), str):
                parts.append(entry["text"])
        if parts:
            return "\n".join(parts)
    return ""


def _extract_planning_block(result: dict[str, Any]) -> dict[str, Any]:
    planning = result.get("planning_block")
    return planning if isinstance(planning, dict) else {}


def test_god_return_levelup(
    client: MCPClient, *, user_id: str, campaign_id: str
) -> dict[str, Any]:
    """Return from GOD MODE and check for level-up visibility/choices."""
    # Setup: level 4, XP just below threshold
    setup_state = {
        "player_character_data": {
            "name": "Alexiel",
            "level": 4,
            "class": "Fighter",
            "experience": {"current": 6400},
            "hp_current": 32,
            "hp_max": 32,
        }
    }
    setup_payload = f"GOD_MODE_UPDATE_STATE:{json.dumps(setup_state)}"
    setup_result = process_action(
        client, user_id=user_id, campaign_id=campaign_id, user_input=setup_payload
    )
    if setup_result.get("error"):
        return {"passed": False, "error": setup_result["error"], "stage": "setup"}

    # Cross the level threshold
    award_state = {
        "player_character_data": {"experience": {"current": 6700}}
    }
    award_payload = f"GOD_MODE_UPDATE_STATE:{json.dumps(award_state)}"
    award_result = process_action(
        client, user_id=user_id, campaign_id=campaign_id, user_input=award_payload
    )
    if award_result.get("error"):
        return {"passed": False, "error": award_result["error"], "stage": "award"}

    state_payload = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
    game_state = state_payload.get("game_state") or {}
    rewards_pending = game_state.get("rewards_pending") or {}

    # Trigger explicit god-mode return
    return_result = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input="GOD MODE: return to story",
    )

    response_text = _extract_response_text(return_result)
    planning_block = _extract_planning_block(return_result)
    choices = planning_block.get("choices", {}) if isinstance(planning_block, dict) else {}

    checks = {
        "level_up_available_in_state": rewards_pending.get("level_up_available", False),
        "has_level_up_message": "LEVEL UP AVAILABLE!" in response_text,
        "has_choice_prompt": "level up" in response_text.lower(),
        "has_level_up_now_choice": "level_up_now" in choices,
        "has_continue_adventuring_choice": "continue_adventuring" in choices,
        "has_god_return_choice": "god:return_story" in choices,
    }

    passed = (
        checks["level_up_available_in_state"]
        and checks["has_level_up_message"]
        and checks["has_level_up_now_choice"]
        and checks["has_continue_adventuring_choice"]
    )

    return {
        "passed": passed,
        "checks": checks,
        "response_text": response_text,
        "planning_block": planning_block,
        "game_state": {
            "rewards_pending": rewards_pending,
        },
        "stage": "god_return",
    }


def run_tests(server_url: str) -> dict[str, Any]:
    client = MCPClient(server_url, timeout_s=120.0)
    client.wait_healthy(timeout_s=45.0)
    test_run_id = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")

    provenance = capture_provenance(server_url)

    user_id = f"test_levelup_god_return_{test_run_id}"
    campaign_id = create_campaign(
        client,
        user_id=user_id,
        title="Level-Up God Return Test",
        description="Testing level-up prompt on GOD MODE return",
    )

    result = test_god_return_levelup(
        client, user_id=user_id, campaign_id=campaign_id
    )

    scenarios = [
        {
            "name": "God Return Level-Up Presentation",
            "campaign_id": campaign_id,
            "passed": result.get("passed", False),
            "errors": [] if result.get("passed") else ["Level-up prompt/choices missing"],
            "checks": result.get("checks", {}),
            "game_state": result.get("game_state", {}),
            "response_text": result.get("response_text", ""),
            "planning_block": result.get("planning_block", {}),
        }
    ]

    run_summary = {
        "scenarios": scenarios,
        "campaign_id": campaign_id,
        "user_id": user_id,
        "collection_started": datetime.now(UTC).isoformat(),
        "collection_ended": datetime.now(UTC).isoformat(),
    }

    evidence_base = get_evidence_dir("level_up_god_return") / test_run_id
    evidence_base.mkdir(parents=True, exist_ok=True)
    request_responses = client.get_captures_as_dict()

    methodology_text = """# Methodology: Level-Up on GOD MODE Return

## Test Type
Real API test against MCP server (not mock mode).

## Purpose
Reproduces the transition from GOD MODE to story mode via "GOD MODE: return to story"
and checks whether level-up visibility and choices appear.

## Steps
1. Create campaign
2. Set character to level 4 with 6400 XP via GOD_MODE_UPDATE_STATE
3. Award XP to cross threshold (6400 → 6700)
4. Issue "GOD MODE: return to story"
5. Check for level-up banner and choices in the response
"""

    create_evidence_bundle(
        evidence_base,
        test_name="level_up_god_return",
        provenance=provenance,
        results=run_summary,
        request_responses=request_responses,
        methodology_text=methodology_text,
    )

    return {
        "test_run_id": test_run_id,
        "server_url": server_url,
        "campaign_id": campaign_id,
        "user_id": user_id,
        "result": result,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Repro test for level-up on GOD MODE return"
    )
    parser.add_argument(
        "--server-url",
        default="http://127.0.0.1:8001",
        help="Server URL to test against",
    )
    parser.add_argument(
        "--start-local",
        action="store_true",
        help="Start local MCP server automatically",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=0,
        help="Port for --start-local (0 = random free port)",
    )
    args = parser.parse_args()

    base_url = args.server_url
    local = None

    try:
        if args.start_local:
            port = int(args.port) if int(args.port) > 0 else pick_free_port()
            local = start_local_mcp_server(
                port,
                env_overrides={
                    "MOCK_SERVICES_MODE": "false",
                    "TESTING": "false",
                    "FORCE_TEST_MODEL": "false",
                    "CAPTURE_RAW_LLM": "true",
                },
                log_dir=get_evidence_dir("level_up_god_return"),
            )
            base_url = local.base_url

        run_tests(base_url)
    finally:
        if local:
            local.stop()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
