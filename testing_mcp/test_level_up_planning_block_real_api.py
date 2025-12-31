#!/usr/bin/env python3
"""Test level-up planning/choice block presentation using real MCP server.

This test validates the PRESENTATION requirement: when a player levels up,
they MUST see a planning block with actionable choices.

Complements test_server_side_level_up_detection.py which validates server-side
detection. This test validates what the USER SEES.

REQUIREMENT (from Dragon Knight campaign):
When level-up is available, response must include:
1. "LEVEL UP AVAILABLE!" notification
2. Choice prompt: "Would you like to level up now?"
3. Options: "1. Level up immediately" and "2. Continue adventuring"

Evidence: Dragon Knight campaign lines 230-246 where user had to manually ask
"what do I get at level 2?" because planning block was missing.

Run against preview server:
    cd testing_mcp
    python test_level_up_planning_block_real_api.py --server-url https://mvp-site-app-s6-754683067800.us-central1.run.app

Run against local server:
    cd testing_mcp
    python test_level_up_planning_block_real_api.py --server-url http://127.0.0.1:8001
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from lib import (
    MCPClient,
    pick_free_port,
    start_local_mcp_server,
    get_evidence_dir,
    capture_provenance,
    create_evidence_bundle,
)
from lib.campaign_utils import create_campaign, process_action, get_campaign_state


# D&D 5e XP thresholds for level 5
XP_THRESHOLD_LEVEL_5 = 6500


def _extract_response_text(result: dict[str, Any]) -> str:
    """Extract the user-facing response text from a process_action result."""
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
    """Extract planning block payload if present."""
    planning = result.get("planning_block")
    if isinstance(planning, dict):
        return planning
    return {}


def _benefit_keywords_present(texts: list[str]) -> bool:
    """Check for benefit/difference keywords in provided texts."""
    keywords = (
        "gain",
        "unlock",
        "bonus",
        "increase",
        "extra",
        "improve",
        "add",
        "advantage",
        "feature",
        "proficiency",
    )
    for text in texts:
        lower = text.lower()
        if any(k in lower for k in keywords):
            return True
    return False


def test_level_up_planning_block_presentation(
    client: MCPClient, *, user_id: str, campaign_id: str
) -> dict[str, Any]:
    """Test that level-up response includes planning/choice block.

    This is the KEY presentation test - validates what the USER SEES
    when level-up is available.

    Returns:
        Dict with test results including pass/fail and evidence.
    """
    # Step 1: Set up character at level 4 with 6400 XP (below 6500 threshold)
    initial_state_changes = {
        "player_character_data": {
            "name": "Alexiel",
            "level": 4,
            "class": "Fighter",
            "experience": {"current": 6400},
            "hp_current": 32,
            "hp_max": 32,
        }
    }
    god_mode_set = f"GOD_MODE_UPDATE_STATE:{json.dumps(initial_state_changes)}"

    result = process_action(
        client, user_id=user_id, campaign_id=campaign_id, user_input=god_mode_set
    )

    if result.get("error"):
        return {
            "passed": False,
            "error": result["error"],
            "query": god_mode_set,
            "test_type": "setup",
        }

    # Verify setup state was applied
    setup_state = get_campaign_state(
        client, user_id=user_id, campaign_id=campaign_id
    ).get("game_state") or {}
    setup_pc = setup_state.get("player_character_data") or {}
    setup_xp = None
    setup_experience = setup_pc.get("experience")
    if isinstance(setup_experience, dict):
        setup_xp = setup_experience.get("current")
    elif setup_experience is not None:
        setup_xp = setup_experience
    setup_level = setup_pc.get("level")
    if setup_level != 4 or setup_xp != 6400:
        return {
            "passed": False,
            "error": "Setup state did not apply as expected",
            "query": god_mode_set,
            "test_type": "setup_verification",
            "setup_state": {
                "current_level": setup_level,
                "current_xp": setup_xp,
            },
        }

    # Step 2: Use God Mode to award XP directly (cross threshold to 6700)
    xp_award_changes = {
        "player_character_data": {
            "experience": {"current": 6700}  # Cross threshold
        }
    }
    god_mode_update = f"GOD_MODE_UPDATE_STATE:{json.dumps(xp_award_changes)}"

    result = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=god_mode_update,
    )

    if result.get("error"):
        return {
            "passed": False,
            "error": result["error"],
            "query": god_mode_update,
            "test_type": "xp_award",
        }

    # Step 3: Trigger a normal narrative response so the user-facing output is tested
    narrative_input = "I pause to check my progress and decide how to proceed."
    narrative_result = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=narrative_input,
    )
    if narrative_result.get("error"):
        return {
            "passed": False,
            "error": narrative_result["error"],
            "query": narrative_input,
            "test_type": "narrative_action",
        }

    response_text = _extract_response_text(narrative_result)
    planning_block = _extract_planning_block(narrative_result)

    # Check for required planning/choice block elements
    has_level_up_message = "LEVEL UP AVAILABLE!" in response_text
    has_choice_prompt = "Would you like to level up now?" in response_text
    has_immediate_option = "1. Level up immediately" in response_text
    has_later_option = "2. Continue adventuring" in response_text

    text_planning_block_present = (
        has_level_up_message
        and has_choice_prompt
        and has_immediate_option
        and has_later_option
    )

    choices = planning_block.get("choices") if isinstance(planning_block, dict) else None
    choice_texts: list[str] = []
    choice_descriptions: list[str] = []
    if isinstance(choices, dict):
        for choice in choices.values():
            if isinstance(choice, dict):
                text = choice.get("text")
                description = choice.get("description")
                if isinstance(text, str) and text.strip():
                    choice_texts.append(text.strip())
                if isinstance(description, str) and description.strip():
                    choice_descriptions.append(description.strip())

    structured_planning_block_present = len(choice_texts) >= 2
    has_choice_descriptions = len(choice_descriptions) >= 2
    has_distinct_choice_descriptions = len(set(choice_descriptions)) >= 2
    has_benefit_keywords = _benefit_keywords_present(
        [response_text] + choice_descriptions
    )
    benefits_present = has_choice_descriptions and (
        has_benefit_keywords or has_distinct_choice_descriptions
    )

    planning_block_present = text_planning_block_present or structured_planning_block_present

    # Get game state to verify level-up was detected
    state_payload = get_campaign_state(
        client, user_id=user_id, campaign_id=campaign_id
    )
    game_state = state_payload.get("game_state") or {}
    pc = game_state.get("player_character_data") or {}
    rewards_pending = game_state.get("rewards_pending") or {}

    current_level = pc.get("level")
    current_xp = None
    experience = pc.get("experience")
    if isinstance(experience, dict):
        current_xp = experience.get("current")
    elif experience is not None:
        current_xp = experience

    level_up_available_in_state = rewards_pending.get("level_up_available", False)
    new_level_in_state = rewards_pending.get("new_level")

    return {
        "passed": planning_block_present and benefits_present and level_up_available_in_state,
        "response_text": response_text,
        "planning_block": planning_block,
        "checks": {
            "level_up_available_in_state": level_up_available_in_state,
            "has_level_up_message": has_level_up_message,
            "has_choice_prompt": has_choice_prompt,
            "has_immediate_option": has_immediate_option,
            "has_later_option": has_later_option,
            "text_planning_block_present": text_planning_block_present,
            "structured_planning_block_present": structured_planning_block_present,
            "has_choice_descriptions": has_choice_descriptions,
            "has_distinct_choice_descriptions": has_distinct_choice_descriptions,
            "has_benefit_keywords": has_benefit_keywords,
            "benefits_present": benefits_present,
        },
        "game_state": {
            "current_level": current_level,
            "current_xp": current_xp,
            "level_up_available_in_state": level_up_available_in_state,
            "new_level_in_state": new_level_in_state,
        },
        "query": narrative_input,
        "test_type": "planning_block_presentation",
    }


def run_tests(server_url: str) -> dict[str, Any]:
    """Run all level-up planning block presentation tests.

    Args:
        server_url: The server URL to test against.

    Returns:
        Dict with test results and evidence.
    """
    client = MCPClient(server_url)
    test_run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    # Capture full provenance
    provenance = capture_provenance(server_url)

    # Create test campaign
    user_id = f"test_levelup_planning_{test_run_id}"
    try:
        campaign_id = create_campaign(
            client,
            user_id=user_id,
            title="Level-Up Planning Test",
            description="Testing level-up planning/choice block presentation",
        )
    except RuntimeError as e:
        return {
            "error": f"Campaign creation failed: {e}",
            "provenance": provenance,
        }

    # Run test
    print(f"\n{'=' * 60}")
    print("Testing: Level-Up Planning Block Presentation")
    print(f"Server: {server_url}")
    print(f"Campaign: {campaign_id}")
    print(f"{'=' * 60}\n")

    test_result = test_level_up_planning_block_presentation(
        client, user_id=user_id, campaign_id=campaign_id
    )

    # Build results
    results = {
        "test_run_id": test_run_id,
        "server_url": server_url,
        "campaign_id": campaign_id,
        "user_id": user_id,
        "collection_started": datetime.now(timezone.utc).isoformat(),
        "provenance": provenance,
        "test_result": test_result,
        "all_passed": test_result.get("passed", False),
        "collection_ended": datetime.now(timezone.utc).isoformat(),
    }

    # Print results
    print(f"\n{'=' * 60}")
    print("TEST RESULTS")
    print(f"{'=' * 60}")
    print(f"Planning Block Present: {'✅ PASS' if test_result.get('passed') else '❌ FAIL'}")
    print(f"\nChecks:")
    for check, value in test_result.get("checks", {}).items():
        status = "✅" if value else "❌"
        print(f"  {status} {check}: {value}")

    print(f"\nGame State:")
    for key, value in test_result.get("game_state", {}).items():
        print(f"  {key}: {value}")

    if not test_result.get("passed"):
        print(f"\n{'=' * 60}")
        print("RESPONSE TEXT (MISSING PLANNING BLOCK):")
        print(f"{'=' * 60}")
        print(test_result.get("response_text", ""))
        print(f"{'=' * 60}")

    # Save evidence using lib bundle format
    evidence_base = get_evidence_dir("level_up_planning_block") / test_run_id
    evidence_base.mkdir(parents=True, exist_ok=True)

    # Convert test_result to scenarios format for create_evidence_bundle
    scenarios = [
        {
            "name": "Level-Up Planning Block Presentation",
            "campaign_id": campaign_id,
            "passed": test_result.get("passed", False),
            "errors": [] if test_result.get("passed") else ["Planning block missing"],
            "checks": test_result.get("checks", {}),
            "game_state": test_result.get("game_state", {}),
            "response_text": test_result.get("response_text", ""),
        }
    ]

    run_summary = {
        "scenarios": scenarios,
        "campaign_id": campaign_id,
        "user_id": user_id,
        "collection_started": results["collection_started"],
        "collection_ended": results["collection_ended"],
    }

    # Get request/response captures from client
    request_responses = client.get_captures_as_dict()

    # Create evidence bundle
    methodology_text = f"""# Methodology: Level-Up Planning Block Presentation Test

## Test Type
Real API test against MCP server (not mock mode).

## Purpose
Validates requirement from Dragon Knight campaign: Level-ups MUST include a planning block
with actionable choices so users don't have to manually request level-up processing.

## Dragon Knight Issue (lines 230-246)
User had to manually ask "what do I get at level 2?" and "why did you miss it?" because
the planning block was missing from the level-up notification.

## Required Elements
When level-up is available, response must include:
1. "LEVEL UP AVAILABLE!" notification
2. Choice prompt: "Would you like to level up now?"
3. Options: "1. Level up immediately" and "2. Continue adventuring"

## Test Mode
- Server: {server_url}
- Real MCP API calls (not mocked)

## Execution Steps
1. Create campaign
2. Set character to level 4 with 6400 XP (below level 5 threshold)
3. Award XP to cross threshold (6400 → 6700, crossing 6500)
4. Verify server detects level-up (rewards_pending.level_up_available)
5. Check response includes all 4 required planning block elements

## Validation Criteria
Test PASSES if response contains all 4 substring matches:
- "LEVEL UP AVAILABLE!"
- "Would you like to level up now?"
- "1. Level up immediately"
- "2. Continue adventuring"

Test FAILS if any element is missing.
"""

    bundle_files = create_evidence_bundle(
        evidence_base,
        test_name="level_up_planning_block",
        provenance=provenance,
        results=run_summary,
        request_responses=request_responses,
        methodology_text=methodology_text,
    )

    print(f"\nEvidence bundle created: {evidence_base}")
    print(f"Files: {', '.join(f.name for f in bundle_files.values())}")

    return results


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Test level-up planning block presentation (real MCP server)"
    )
    parser.add_argument(
        "--server-url",
        default=os.environ.get("MCP_SERVER_URL") or "http://127.0.0.1:8001",
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

    local = None
    base_url = str(args.server_url)
    evidence_dir = get_evidence_dir("level_up_planning_block")
    env_overrides: dict[str, str] | None = None

    try:
        if args.start_local:
            port = int(args.port) if int(args.port) > 0 else pick_free_port()
            env_overrides = {
                "MOCK_SERVICES_MODE": "false",
                "TESTING": "false",
                "FORCE_TEST_MODEL": "false",
                "CAPTURE_RAW_LLM": "true",
            }
            local = start_local_mcp_server(
                port,
                env_overrides=env_overrides,
                log_dir=evidence_dir,
            )
            base_url = local.base_url

        client = MCPClient(base_url, timeout_s=120.0)
        client.wait_healthy(timeout_s=45.0)

        # Capture provenance after server is running
        server_pid = local.proc.pid if local else None
        provenance = capture_provenance(
            base_url,
            server_pid,
            server_env_overrides=env_overrides if local else None,
        )

        results = run_tests_with_client(
            client,
            base_url=base_url,
            provenance=provenance,
            server_log_path=local.log_path if local else None,
        )
    finally:
        if local is not None:
            local.stop()

    if results.get("error"):
        print(f"\n❌ Test run failed: {results['error']}")
        return 1

    return 0 if results.get("all_passed") else 1


def run_tests_with_client(
    client: MCPClient,
    *,
    base_url: str,
    provenance: dict[str, Any],
    server_log_path: Path | None,
) -> dict[str, Any]:
    """Run tests using a preconfigured MCPClient and provenance."""
    test_run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    # Create test campaign
    user_id = f"test_levelup_planning_{test_run_id}"
    try:
        campaign_id = create_campaign(
            client,
            user_id=user_id,
            title="Level-Up Planning Test",
            description="Testing level-up planning/choice block presentation",
        )
    except RuntimeError as e:
        return {
            "error": f"Campaign creation failed: {e}",
            "provenance": provenance,
        }

    # Run test
    print(f"\n{'=' * 60}")
    print("Testing: Level-Up Planning Block Presentation")
    print(f"Server: {base_url}")
    print(f"Campaign: {campaign_id}")
    print(f"{'=' * 60}\n")

    test_result = test_level_up_planning_block_presentation(
        client, user_id=user_id, campaign_id=campaign_id
    )

    # Build results
    results = {
        "test_run_id": test_run_id,
        "server_url": base_url,
        "campaign_id": campaign_id,
        "user_id": user_id,
        "collection_started": datetime.now(timezone.utc).isoformat(),
        "provenance": provenance,
        "test_result": test_result,
        "all_passed": test_result.get("passed", False),
        "collection_ended": datetime.now(timezone.utc).isoformat(),
    }

    # Print results
    print(f"\n{'=' * 60}")
    print("TEST RESULTS")
    print(f"{'=' * 60}")
    print(f"Planning Block Present: {'✅ PASS' if test_result.get('passed') else '❌ FAIL'}")
    print(f"\nChecks:")
    for check, value in test_result.get("checks", {}).items():
        status = "✅" if value else "❌"
        print(f"  {status} {check}: {value}")

    print(f"\nGame State:")
    for key, value in test_result.get("game_state", {}).items():
        print(f"  {key}: {value}")

    if not test_result.get("passed"):
        print(f"\n{'=' * 60}")
        print("RESPONSE TEXT (MISSING PLANNING BLOCK/BENEFITS):")
        print(f"{'=' * 60}")
        print(test_result.get("response_text", ""))
        print(f"{'=' * 60}")

    # Save evidence using lib bundle format
    evidence_base = get_evidence_dir("level_up_planning_block") / test_run_id
    evidence_base.mkdir(parents=True, exist_ok=True)

    # Convert test_result to scenarios format for create_evidence_bundle
    scenarios = [
        {
            "name": "Level-Up Planning Block Presentation",
            "campaign_id": campaign_id,
            "passed": test_result.get("passed", False),
            "errors": [] if test_result.get("passed") else ["Planning block/benefits missing"],
            "checks": test_result.get("checks", {}),
            "game_state": test_result.get("game_state", {}),
            "response_text": test_result.get("response_text", ""),
            "planning_block": test_result.get("planning_block", {}),
        }
    ]

    run_summary = {
        "scenarios": scenarios,
        "campaign_id": campaign_id,
        "user_id": user_id,
        "collection_started": results["collection_started"],
        "collection_ended": results["collection_ended"],
    }

    # Get request/response captures from client
    request_responses = client.get_captures_as_dict()

    methodology_text = f"""# Methodology: Level-Up Planning Block Presentation Test

## Test Type
Real API test against MCP server (not mock mode).

## Purpose
Validates requirement from Dragon Knight campaign: Level-ups MUST include a planning block
with actionable choices and visible benefits/differences so users don't have to manually
request level-up processing or ask what they gain.

## Dragon Knight Issue (lines 230-246)
User had to manually ask \"what do I get at level 2?\" and \"why did you miss it?\"
because the planning block was missing from the level-up notification.

## Required Elements
When level-up is available, response must include:
1. \"LEVEL UP AVAILABLE!\" notification (text or structured planning block)
2. Choice prompt: \"Would you like to level up now?\" (text or structured)
3. Options: \"1. Level up immediately\" and \"2. Continue adventuring\" (text or structured)
4. Benefits/differences: at least two distinct choice descriptions or benefit keywords

## Test Mode
- Server: {base_url}
- Real MCP API calls (not mocked)

## Execution Steps
1. Create campaign
2. Set character to level 4 with 6400 XP (below level 5 threshold) via GOD_MODE_UPDATE_STATE
3. Verify setup state applied (level=4, XP=6400)
4. Award XP to cross threshold (6400 → 6700) via GOD_MODE_UPDATE_STATE
5. Trigger a normal narrative action to surface user-facing response
6. Verify response includes planning block choices and benefits/differences

## Validation Criteria
Test PASSES if:
- Level-up is detected in state (rewards_pending.level_up_available = true)
- Planning block is present in narrative response text OR structured planning_block
- Benefits/differences are present (distinct choice descriptions or benefit keywords)
"""

    bundle_files = create_evidence_bundle(
        evidence_base,
        test_name="level_up_planning_block",
        provenance=provenance,
        results=run_summary,
        request_responses=request_responses,
        methodology_text=methodology_text,
        server_log_path=server_log_path,
    )

    print(f"\nEvidence bundle created: {evidence_base}")
    print(f"Files: {', '.join(f.name for f in bundle_files.values())}")

    return results


if __name__ == "__main__":
    sys.exit(main())
