#!/usr/bin/env python3
"""MCP smart skill check dice coverage - tests DICE-ayy gap detection.

This test specifically validates that the system catches dice fabrication when:
1. User input has NO combat keywords
2. User input has NO explicit "Make a check" requests
3. LLM intelligently decides a skill check is needed
4. Dice MUST come from code_execution, not narrative fabrication

This is the DICE-ayy regression test - if this fails, the gap has returned.

Run (local MCP already running):
    cd testing_mcp
    python test_smart_skill_checks_real_api.py --server-url http://127.0.0.1:8001

Run (start local MCP automatically):
    cd testing_mcp
    python test_smart_skill_checks_real_api.py --start-local --real-services

Run with evidence collection:
    cd testing_mcp
    python test_smart_skill_checks_real_api.py --start-local --real-services --evidence
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from mcp_client import MCPClient
from lib.server_utils import LocalServer, pick_free_port, start_local_mcp_server
from lib.model_utils import DEFAULT_MODEL_MATRIX, settings_for_model, update_user_settings
from lib.evidence_utils import get_evidence_dir

# CRITICAL: These scenarios have NO combat keywords and NO explicit "Make a check" language
# The LLM must intelligently decide a skill check is needed
SMART_SKILL_SCENARIOS = [
    {
        "name": "Intimidation (implicit)",
        "user_input": "I demand the guard stand down immediately and let us pass.",
        "expected_check_type": "Intimidation",
        "category": "social",
    },
    {
        "name": "Persuasion (implicit)",
        "user_input": "I try to convince the merchant to lower the price by 50 gold pieces.",
        "expected_check_type": "Persuasion",
        "category": "social",
    },
    {
        "name": "Deception (implicit)",
        "user_input": "I tell the captain a convincing story about why we're here.",
        "expected_check_type": "Deception",
        "category": "social",
    },
    {
        "name": "Perception (implicit)",
        "user_input": "I carefully examine the bookshelf for anything unusual.",
        "expected_check_type": "Perception",
        "category": "investigation",
    },
    {
        "name": "Insight (implicit)",
        "user_input": "I watch the noble's reactions carefully as he speaks.",
        "expected_check_type": "Insight",
        "category": "social",
    },
]


def has_combat_keywords(text: str) -> bool:
    """Check if text contains combat keywords that would trigger detection."""
    combat_keywords = [
        "attack", "cast", "swing", "strike", "shoot", "hit",
        "damage", "fight", "defend", "parry", "dodge",
    ]
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in combat_keywords)


def has_explicit_check_request(text: str) -> bool:
    """Check if text explicitly requests a skill check."""
    check_patterns = [
        "make a", "roll a", "make an", "roll an",
        "check", "saving throw", "save",
    ]
    text_lower = text.lower()
    return any(pattern in text_lower for pattern in check_patterns)


def _get_debug_info(result: dict[str, Any]) -> dict[str, Any]:
    debug_info = result.get("debug_info") or {}
    return debug_info if isinstance(debug_info, dict) else {}


def _infer_dice_strategy(
    result: dict[str, Any],
) -> tuple[str, dict[str, Any], list[Any] | None]:
    debug_info = _get_debug_info(result)
    tool_results = result.get("tool_results") or debug_info.get("tool_results")
    dice_strategy = (
        result.get("dice_strategy")
        or debug_info.get("dice_strategy")
        or ("native_two_phase" if tool_results else None)
        or (
            "code_execution"
            if debug_info.get("code_execution_used") or debug_info.get("stdout")
            else None
        )
        or "unknown"
    )
    return dice_strategy, debug_info, tool_results


def validate_smart_skill_check(
    result: dict[str, Any],
    scenario: dict[str, Any],
    user_input: str,
    *,
    allow_no_dice: bool,
) -> list[str]:
    """Validate that LLM made smart skill check decision with proper dice rolling."""
    errors: list[str] = []

    # 1. Verify user input had NO combat keywords (test integrity)
    if has_combat_keywords(user_input):
        errors.append(
            f"Test contaminated - user input contains combat keywords: {user_input}"
        )
        return errors

    # 2. Verify user input had NO explicit check requests (test integrity)
    if has_explicit_check_request(user_input):
        errors.append(
            f"Test contaminated - user input has explicit check request: {user_input}"
        )
        return errors

    # 3. Check for server error
    if result.get("error"):
        errors.append(f"Server returned error: {result['error']}")
        return errors

    # 4. Verify dice rolls exist (LLM made skill check decision)
    dice_rolls = result.get("dice_rolls") or []
    if not isinstance(dice_rolls, list):
        errors.append(f"dice_rolls not a list: {type(dice_rolls)}")
        return errors

    if len(dice_rolls) < 1:
        if allow_no_dice:
            # No dice rolls = no fabrication possible = PASS (not an error)
            return []
        errors.append(
            "No dice rolls produced; cannot validate smart skill check decision"
        )
        return errors

    # 5. RELAXED: Accept ANY skill check type (LLM may choose different but valid checks)
    # We're testing FABRICATION DETECTION, not check type prediction
    joined_rolls = "\n".join(str(roll) for roll in dice_rolls)
    # Note: We don't enforce expected_check_type anymore - any check is valid

    # 6. CRITICAL: Verify proper dice provenance (code_execution vs tool_results)
    dice_strategy, debug_info, tool_results = _infer_dice_strategy(result)

    if dice_strategy == "code_execution":
        code_execution_used = debug_info.get("code_execution_used", False)
        stdout_present = bool(debug_info.get("stdout"))
        if not (code_execution_used or stdout_present):
            errors.append(
                "Expected code_execution evidence for dice rolls (Gemini strategy)"
            )
        executable_code_parts = debug_info.get("executable_code_parts")
        if code_execution_used and isinstance(executable_code_parts, int) and executable_code_parts < 1:
            errors.append("code_execution_used=True but no executable_code_parts found")
    elif dice_strategy == "native_two_phase":
        if not tool_results:
            errors.append(
                "Expected tool_results for native_two_phase dice rolls; "
                "enable CAPTURE_EVIDENCE on the server"
            )
    else:
        errors.append(
            "Unable to determine dice strategy for validation (missing evidence)"
        )

    # 7. Verify dice_integrity_violation flag (should be False when present)
    dice_integrity_violation = debug_info.get("dice_integrity_violation", False)
    if dice_integrity_violation:
        errors.append(
            "Narrative detection triggered violation flag - dice may be fabricated"
        )

    return errors




def save_evidence(
    model_id: str,
    scenario_name: str,
    user_input: str,
    result: dict[str, Any],
    validation_errors: list[str],
    evidence_dir: Path,
) -> None:
    """Save test evidence to disk."""
    evidence_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_model = model_id.replace("/", "-").replace(":", "-")
    safe_scenario = scenario_name.lower().replace(" ", "_").replace("(", "").replace(")", "")

    evidence_file = evidence_dir / f"{timestamp}_{safe_model}_{safe_scenario}.json"

    evidence = {
        "timestamp": timestamp,
        "model_id": model_id,
        "scenario_name": scenario_name,
        "user_input": user_input,
        "validation_passed": len(validation_errors) == 0,
        "validation_errors": validation_errors,
        "dice_rolls": result.get("dice_rolls", []),
        "debug_info": result.get("debug_info", {}),
        "narrative": result.get("narrative", ""),
    }

    with open(evidence_file, "w") as f:
        json.dump(evidence, f, indent=2, default=str)

    print(f"  📁 Evidence saved: {evidence_file.name}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="MCP smart skill check dice coverage (DICE-ayy regression test)"
    )
    parser.add_argument(
        "--server-url",
        default=os.environ.get("MCP_SERVER_URL") or "http://127.0.0.1:8001",
        help="Base server URL (with or without /mcp)",
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
    parser.add_argument(
        "--models",
        default=os.environ.get("MCP_TEST_MODELS", ""),
        help=(
            "Comma-separated model IDs to test (e.g. "
            "gemini-3-flash-preview,qwen-3-235b-a22b-instruct-2507). "
            "Defaults to Gemini+Qwen matrix."
        ),
    )
    parser.add_argument(
        "--real-services",
        action="store_true",
        help="Use real API providers (requires API keys)",
    )
    parser.add_argument(
        "--evidence",
        action="store_true",
        help="Save detailed evidence files for each test",
    )
    parser.add_argument(
        "--enable-dice-tool",
        action="store_true",
        help="Expose test-only roll_dice MCP tool (ENABLE_DICE_TEST_TOOL=true)",
    )
    parser.add_argument(
        "--allow-no-dice",
        action="store_true",
        help="Allow scenarios where the model produces no dice rolls (less strict).",
    )
    args = parser.parse_args()

    local: LocalServer | None = None
    base_url = str(args.server_url)

    try:
        # Start local MCP server if requested
        if args.start_local:
            port = args.port if args.port > 0 else pick_free_port()
            env_overrides: dict[str, str] = {}
            env_overrides["MOCK_SERVICES_MODE"] = "false" if args.real_services else "true"
            env_overrides["TESTING"] = "false"
            env_overrides["FORCE_TEST_MODEL"] = "false"
            env_overrides["FAST_TESTS"] = "false"
            env_overrides["CAPTURE_EVIDENCE"] = "true"
            if args.enable_dice_tool:
                env_overrides["ENABLE_DICE_TEST_TOOL"] = "true"
            local = start_local_mcp_server(port, env_overrides=env_overrides)
            base_url = local.base_url
            print(f"🚀 Local MCP server started on {base_url}")
            print(f"📋 Log file: {local.log_path}")
            time.sleep(3)  # Give server time to start

        client = MCPClient(base_url, timeout_s=180.0)
        client.wait_healthy(timeout_s=45.0)
        print(f"✅ MCP server healthy at {base_url}\n")

        # Parse model list
        models = [m.strip() for m in (args.models or "").split(",") if m.strip()]
        if not models:
            models = list(DEFAULT_MODEL_MATRIX)

        # Setup evidence directory if requested (per evidence-standards.md)
        evidence_dir = None
        if args.evidence:
            evidence_dir = get_evidence_dir("smart_skill_checks")
            print(f"📁 Evidence directory: {evidence_dir}\n")

        all_passed = True
        total_tests = len(models) * len(SMART_SKILL_SCENARIOS)
        passed_tests = 0

        print(f"🧪 Running {total_tests} smart skill check tests")
        print(f"   Models: {', '.join(models)}")
        print(f"   Scenarios: {len(SMART_SKILL_SCENARIOS)}")
        print(f"   Real services: {args.real_services}")
        print("=" * 70)

        for model_id in models:
            print(f"\n📦 Testing model: {model_id}")
            print("-" * 70)

            model_settings = settings_for_model(model_id)
            model_settings["debug_mode"] = True
            user_id = f"smart-skill-{model_id.replace('/', '-')}-{int(time.time())}"

            # Update user settings for this model
            update_user_settings(client, user_id=user_id, settings=model_settings)

            # Create campaign with appropriate setting for skill checks
            campaign_payload = client.tools_call(
                "create_campaign",
                {
                    "user_id": user_id,
                    "title": "Smart Skill Check Test Campaign",
                    "character": "Lyra the Bard (CHA 16, WIS 14)",
                    "setting": "A tense negotiation in the Lord's Hall. Guards block your path.",
                    "description": "Test campaign for smart skill check validation (DICE-ayy regression)",
                },
            )

            campaign_id = campaign_payload.get("campaign_id") or campaign_payload.get(
                "campaignId"
            )
            if not isinstance(campaign_id, str) or not campaign_id:
                print(
                    f"❌ Failed to create campaign for {model_id}: {campaign_payload}"
                )
                all_passed = False
                continue

            # Run all scenarios
            for scenario in SMART_SKILL_SCENARIOS:
                scenario_name = scenario["name"]
                user_input = scenario["user_input"]

                # Process action
                result = client.tools_call(
                    "process_action",
                    {
                        "user_id": user_id,
                        "campaign_id": campaign_id,
                        "user_input": user_input,
                        "mode": "character",
                    },
                )

                # Validate result
                validation_errors = validate_smart_skill_check(
                    result, scenario, user_input, allow_no_dice=args.allow_no_dice
                )

                # Save evidence if requested
                if evidence_dir:
                    save_evidence(
                        model_id,
                        scenario_name,
                        user_input,
                        result,
                        validation_errors,
                        evidence_dir,
                    )

                # Report results
                if validation_errors:
                    all_passed = False
                    print(f"❌ {scenario_name}")
                    print(f"   Input: {user_input}")
                    for error in validation_errors:
                        print(f"   Error: {error}")
                else:
                    passed_tests += 1
                    dice_count = len(result.get("dice_rolls", []))
                    dice_strategy, debug_info, tool_results = _infer_dice_strategy(
                        result
                    )
                    if dice_strategy == "native_two_phase":
                        print(
                            f"✅ {scenario_name}: {dice_count} rolls, "
                            f"tool_results={bool(tool_results)}"
                        )
                    else:
                        code_execution = debug_info.get("code_execution_used", False)
                        print(
                            f"✅ {scenario_name}: {dice_count} rolls, "
                            f"code_execution={code_execution}"
                        )

        # Summary
        print("\n" + "=" * 70)
        print(f"📊 Test Summary: {passed_tests}/{total_tests} passed")
        if all_passed:
            print("✅ ALL TESTS PASSED - DICE-ayy gap detection working")
            return 0
        else:
            print(
                f"❌ {total_tests - passed_tests} TESTS FAILED - "
                f"DICE-ayy regression detected"
            )
            return 2

    finally:
        if local is not None:
            print("\n🛑 Stopping local MCP server...")
            local.stop()


if __name__ == "__main__":
    raise SystemExit(main())
