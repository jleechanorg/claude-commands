#!/usr/bin/env python3
"""MCP inventory validation tests - ensures players can only use items they possess.

This test validates that the LLM correctly handles:
1. Players claiming items that don't exist in their inventory
2. Players using wrong stats for items they do have (e.g., +3 vs +1)
3. Players claiming magical containers (Bag of Holding) they don't possess

The LLM should either:
- Reject the action narratively ("You reach for [item] but don't have one")
- Correct to actual inventory and use proper stats
- NOT blindly accept player claims about their equipment

Run (local MCP already running):
    cd testing_mcp
    python test_inventory_validation_real_api.py --server-url http://127.0.0.1:8001

Run (start local MCP automatically):
    cd testing_mcp
    python test_inventory_validation_real_api.py --start-local --real-services

Run with evidence collection:
    cd testing_mcp
    python test_inventory_validation_real_api.py --start-local --real-services --evidence
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from lib.model_utils import (
    DEFAULT_MODEL_MATRIX,
    settings_for_model,
    update_user_settings,
)
from lib.server_utils import LocalServer, pick_free_port, start_local_mcp_server
from mcp_client import MCPClient

# Character setup: Known inventory for validation
# The character has specific items - tests will try to use items NOT in this list
CHARACTER_INVENTORY = """
Kira the Fighter (Level 5)
Equipment:
- Weapon (Main): Longsword +1 (1d8+1 slashing, +6 to hit)
- Armor: Chain Mail (AC 16)
- Shield: Wooden Shield (+2 AC)
- Backpack: 50ft rope, 10 torches, bedroll, waterskin, 3 days rations
- Gold: 150gp
NO magical containers. NO legendary items. NO +3 weapons.
"""

# Test scenarios: Player claims items they DON'T have
INVENTORY_CHEAT_SCENARIOS = [
    {
        "name": "Claim non-existent legendary weapon",
        "user_input": "I draw my Vorpal Sword and attack the goblin!",
        "false_claim": "Vorpal Sword",
        "actual_item": "Longsword +1",
        "expected_behavior": "reject_or_correct",
        # Note: "vorpal" is the key indicator - beheading/decapitation effects
        "cheat_indicators": ["vorpal", "decapitate", "beheading", "sever"],
    },
    {
        "name": "Claim wrong weapon stats (+3 vs +1)",
        "user_input": "I attack with my +3 Flaming Longsword!",
        "false_claim": "+3 Flaming Longsword",
        "actual_item": "Longsword +1",
        "expected_behavior": "use_actual_stats",
        # Detect both the flaming property AND the wrong +3 modifier in narrative
        # "+3 longsword" catches cases where LLM drops "flaming" but keeps wrong stats
        "cheat_indicators": [
            "flaming sword",
            "flaming longsword",
            "fire damage",
            "wreathed in flame",
            "blade of fire",
            "+3 longsword",
            "+3 sword",  # Wrong modifier in narrative
        ],
    },
    {
        "name": "Claim Bag of Holding they don't have",
        "user_input": "I reach into my Bag of Holding and pull out a healing potion.",
        "false_claim": "Bag of Holding",
        "actual_item": "backpack",
        "expected_behavior": "reject_or_correct",
        "cheat_indicators": ["bag of holding", "extradimensional", "bottomless"],
    },
    {
        "name": "Claim magical armor they don't have",
        "user_input": "My Plate Armor of Invulnerability protects me from the attack!",
        "false_claim": "Plate Armor of Invulnerability",
        "actual_item": "Chain Mail",
        "expected_behavior": "reject_or_correct",
        # Note: Don't use "AC 18" as cheat indicator - character's actual AC is 18 (Chain Mail 16 + Shield +2)
        "cheat_indicators": ["invulnerability", "plate armor", "resistance"],
    },
    {
        "name": "Claim spell scroll not in inventory",
        "user_input": "I use my Scroll of Fireball to blast the enemies!",
        "false_claim": "Scroll of Fireball",
        "actual_item": None,
        "expected_behavior": "reject",
        "cheat_indicators": ["fireball", "8d6", "explosion", "scroll"],
    },
]


def validate_inventory_check(  # noqa: PLR0912 - complex validation across narrative and game state
    result: dict[str, Any],
    scenario: dict[str, Any],
) -> tuple[bool, list[str]]:
    """Validate that LLM properly handled the false inventory claim.

    Returns (passed, errors) tuple.
    """
    errors: list[str] = []
    # Use `or ""` pattern to handle both missing key AND explicit None value
    narrative = (result.get("narrative") or "").lower()

    # Check for server error
    if result.get("error"):
        errors.append(f"Server returned error: {result['error']}")
        return False, errors

    false_claim = scenario["false_claim"].lower()
    actual_item = (scenario.get("actual_item") or "").lower()
    cheat_indicators = [ind.lower() for ind in scenario.get("cheat_indicators", [])]

    def _flatten_strings(value: Any) -> list[str]:
        if isinstance(value, str):
            return [value.lower()]
        if isinstance(value, dict):
            flattened: list[str] = []
            for v in value.values():
                flattened.extend(_flatten_strings(v))
            return flattened
        if isinstance(value, (list, tuple, set)):
            flattened = []
            for item in value:
                flattened.extend(_flatten_strings(item))
            return flattened
        return []

    # Detection criteria:
    # 1. Narrative should NOT contain cheat indicators (LLM accepted the cheat)
    # 2. OR narrative should contain correction language

    # Phrases that indicate the LLM REJECTED/CORRECTED the false claim
    rejection_phrases = [
        "don't have",
        "do not have",
        "realize you don't",
        "realize you do not",
        "you don't actually have",
        "don't actually have",
        "something's wrong",
        "not in your",
        "no such",
        "find no",
        "but find no",
        "offers no additional",
        "no additional protection",
        "cannot find",
        "isn't in",
        "is not in",
        "isn't there",
        "is not there",
        "isn't here",
        "never acquired",
        "never obtained",
        "never had",
        "find none",
        "no scroll",
        "no potion",
        "search your pack but",
        "reach for a scroll but",
        # Correction patterns where LLM acknowledges claim then corrects
        "however, your hand",
        "however, you see",
        "however, your fingers",
        "however, you find",
        "but your hand meets",
        "but you find only",
        "but your fingers find",
        "but your fingers close",
        "but your hands find",
        "your fingers close",
        "your hands find only",
        "only the sturdy",
        "only the mundane",
        "only the cold",
        "only the familiar",
        "only the coarse",
        "find only the",
        "close once more around",
        "standard traveling",
        "standard traveler",
        "standard pack",
        "mundane canvas",
        "coarse canvas",
        "iron rings",  # Chain mail description
        "+1 longsword",  # Alternate phrasing
        "longsword +1",  # Standard phrasing
        "figment of your",  # "remains a figment of your ambition"
        "not a part of your",  # "not a part of your equipment"
    ]
    # Dynamically add actual item as a correction indicator
    if actual_item:
        rejection_phrases.append(actual_item)

    # Check if cheat was rejected (explicit rejection language)
    has_rejection = any(phrase in narrative for phrase in rejection_phrases)

    # Check if ANY cheat indicator appears in narrative (LLM accepted the cheat)
    has_cheat_accepted = any(indicator in narrative for indicator in cheat_indicators)

    # For weapon stat claims: check if narrative uses the actual item name WITHOUT cheat properties
    # Example: narrative should mention "longsword +1" (the actual item) but not "flaming" / "+3" enhancements
    uses_actual_item = bool(actual_item) and actual_item in narrative

    # Validate that false items were not injected into INVENTORY-SPECIFIC fields
    # Note: We only check inventory/equipment fields, NOT echo fields like narrative
    # or player_action which naturally contain the player's original (rejected) claim
    game_state = result.get("game_state") or {}
    state_updates = result.get("state_updates") or {}

    # Extract only inventory-related fields for validation
    inventory_fields = {}
    for key in ["equipment", "inventory", "items", "resources", "backpack", "gear"]:
        if key in game_state:
            inventory_fields[key] = game_state[key]
        if key in state_updates:
            inventory_fields[f"update_{key}"] = state_updates[key]
    # Also check nested player_character_data
    pcd = game_state.get("player_character_data") or {}
    for key in ["equipment", "inventory", "items", "resources"]:
        if key in pcd:
            inventory_fields[f"pcd_{key}"] = pcd[key]

    inventory_text = " ".join(_flatten_strings(inventory_fields))

    if false_claim and false_claim in inventory_text:
        errors.append(
            f"CHEAT ACCEPTED: Inventory fields contain the false item '{false_claim}'."
        )

    for indicator in cheat_indicators:
        if indicator in inventory_text and (
            not actual_item or indicator not in actual_item
        ):
            errors.append(
                "CHEAT ACCEPTED: Inventory fields include cheat indicator "
                f"'{indicator}' without correction."
            )

    # Special check: If they claimed wrong weapon stats, check for +8 attack modifier
    # Note: We check specifically for d20+8 pattern (attack roll with +3 weapon + 5 STR)
    # rather than just "+3" anywhere, because damage rolls legitimately contain
    # STR modifiers like "1d8+3" which would cause false positives.
    dice_rolls = result.get("dice_rolls", [])
    dice_text = " ".join(str(d).lower() for d in dice_rolls)

    # If +3 weapon was claimed, check if attack roll used +8 (3 weapon + 5 STR)
    # instead of correct +6 (1 weapon + 5 STR)
    if "+3" in scenario["false_claim"].lower():
        # Look for attack roll pattern with wrong modifier
        # d20+8 would indicate +3 weapon + 5 STR (cheat)
        # d20+6 would indicate +1 weapon + 5 STR (correct)
        attack_roll_pattern = r"d20\s*\+\s*8\b"
        if re.search(attack_roll_pattern, dice_text):
            errors.append(
                f"CHEAT ACCEPTED: Attack roll uses +8 modifier (indicating +3 weapon) "
                f"when actual weapon is +1 (should be +6). Dice: {dice_rolls}"
            )

    # Check if cheat was accepted (cheat indicators present without proper rejection)
    if has_cheat_accepted and not has_rejection:
        errors.append(
            f"CHEAT ACCEPTED: Narrative contains cheat indicators {cheat_indicators} "
            f"without rejection. The LLM allowed the player to use '{false_claim}' "
            f"which they don't have. Narrative snippet: '{narrative[:150]}...'"
        )

    # CRITICAL: The LLM must ACTIVELY reject or correct the false claim.
    # A generic response like "You attack the goblin" is NOT acceptable - it means
    # the LLM ignored the false claim without correcting it, which enables cheating.
    # Require either: explicit rejection, OR use of actual item in narrative.
    properly_handled = has_rejection or (uses_actual_item and not has_cheat_accepted)

    if not properly_handled and not has_cheat_accepted:
        # LLM gave a generic response without addressing the false claim at all
        errors.append(
            f"VALIDATION MISSING: LLM did not explicitly reject or correct the false claim "
            f"'{scenario['false_claim']}'. A generic response that ignores the claim "
            f"enables cheating. Expected rejection language or use of actual item "
            f"'{scenario.get('actual_item', 'N/A')}'. Narrative: '{narrative[:150]}...'"
        )

    passed = len(errors) == 0
    return passed, errors


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

    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    safe_model = model_id.replace("/", "-").replace(":", "-")
    safe_scenario = (
        scenario_name.lower().replace(" ", "_").replace("(", "").replace(")", "")
    )

    evidence_file = evidence_dir / f"{timestamp}_{safe_model}_{safe_scenario}.json"

    evidence = {
        "timestamp": timestamp,
        "model_id": model_id,
        "scenario_name": scenario_name,
        "user_input": user_input,
        "validation_passed": len(validation_errors) == 0,
        "validation_errors": validation_errors,
        "narrative": result.get("narrative", ""),
        "dice_rolls": result.get("dice_rolls", []),
        "game_state": result.get("game_state", {}),
        "debug_info": result.get("debug_info", {}),
    }

    with open(evidence_file, "w") as f:
        json.dump(evidence, f, indent=2, default=str)

    print(f"  📁 Evidence saved: {evidence_file.name}")


def main() -> int:  # noqa: PLR0912, PLR0915 - integration harness needs explicit steps
    parser = argparse.ArgumentParser(
        description="MCP inventory validation tests (anti-cheat)"
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
        help=("Comma-separated model IDs to test. Defaults to Gemini+Qwen matrix."),
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
    args = parser.parse_args()

    local: LocalServer | None = None
    client: MCPClient | None = None
    created_campaigns: list[tuple[str, str]] = []
    base_url = str(args.server_url)

    try:
        # Start local MCP server if requested
        if args.start_local:
            port = args.port if args.port > 0 else pick_free_port()
            env_overrides: dict[str, str] = {}
            env_overrides["MOCK_SERVICES_MODE"] = (
                "false" if args.real_services else "true"
            )
            env_overrides["TESTING"] = "false"
            env_overrides["FORCE_TEST_MODEL"] = "false"
            env_overrides["FAST_TESTS"] = "false"
            env_overrides["CAPTURE_EVIDENCE"] = "true"
            local = start_local_mcp_server(port, env_overrides=env_overrides)
            base_url = local.base_url
            print(f"🚀 Local MCP server started on {base_url}")
            print(f"📋 Log file: {local.log_path}")

        client = MCPClient(base_url, timeout_s=180.0)
        client.wait_healthy(timeout_s=45.0)
        print(f"✅ MCP server healthy at {base_url}\n")

        # Parse model list
        models = [m.strip() for m in (args.models or "").split(",") if m.strip()]
        if not models:
            models = list(DEFAULT_MODEL_MATRIX)

        # Setup evidence directory if requested
        evidence_dir = None
        if args.evidence:
            evidence_dir = Path(__file__).parent / "evidence" / "inventory_validation"
            evidence_dir.mkdir(parents=True, exist_ok=True)
            print(f"📁 Evidence directory: {evidence_dir}\n")

        all_passed = True
        total_tests = len(models) * len(INVENTORY_CHEAT_SCENARIOS)
        passed_tests = 0

        print(f"🛡️ Running {total_tests} inventory validation tests")
        print(f"   Models: {', '.join(models)}")
        print(f"   Scenarios: {len(INVENTORY_CHEAT_SCENARIOS)}")
        print(f"   Real services: {args.real_services}")
        print("=" * 70)

        for model_id in models:
            print(f"\n📦 Testing model: {model_id}")
            print("-" * 70)

            model_settings = settings_for_model(model_id)
            model_settings["debug_mode"] = True
            user_id = f"inv-val-{model_id.replace('/', '-')}-{int(time.time())}"

            # Update user settings for this model
            update_user_settings(client, user_id=user_id, settings=model_settings)

            # Create campaign with KNOWN inventory
            # Setting explicitly states what the character HAS and DOESN'T HAVE
            campaign_payload = client.tools_call(
                "create_campaign",
                {
                    "user_id": user_id,
                    "title": "Inventory Validation Test",
                    "character": CHARACTER_INVENTORY,
                    "setting": "A dungeon corridor. A goblin blocks your path, ready to fight.",
                    "description": "Test campaign for inventory validation (anti-cheat)",
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

            print(f"   Campaign created: {campaign_id}")
            created_campaigns.append((user_id, campaign_id))

            # Run all scenarios
            for scenario in INVENTORY_CHEAT_SCENARIOS:
                scenario_name = scenario["name"]
                user_input = scenario["user_input"]

                scenario_timeout_s = 60.0

                print(f"\n   Testing: {scenario_name}")
                print(f'   Input: "{user_input[:60]}..."')

                # Process action with the cheat attempt
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(
                        client.tools_call,
                        "process_action",
                        {
                            "user_id": user_id,
                            "campaign_id": campaign_id,
                            "user_input": user_input,
                            "mode": "character",
                        },
                    )
                    try:
                        result = future.result(timeout=scenario_timeout_s)
                    except TimeoutError:
                        validation_errors = [
                            f"CHEAT VALIDATION TIMED OUT after {scenario_timeout_s}s"
                        ]
                        all_passed = False
                        print(f"   ❌ FAILED: {scenario_name}")
                        print(f"      Error: {validation_errors[0]}")
                        continue

                # Validate result
                passed, validation_errors = validate_inventory_check(result, scenario)

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
                    print(f"   ❌ FAILED: {scenario_name}")
                    for error in validation_errors:
                        print(f"      Error: {error}")
                    # Show what the narrative said (handle None values)
                    narrative_preview = (result.get("narrative") or "")[:200]
                    print(f'      Narrative: "{narrative_preview}..."')
                else:
                    passed_tests += 1
                    print("   ✅ PASSED: LLM properly handled false claim")
                    # Show correction if present (handle None values)
                    narrative = result.get("narrative") or ""
                    if any(
                        p in narrative.lower()
                        for p in ["don't have", "instead", "actually"]
                    ):
                        print("      Correction detected in narrative")

        # Summary
        print("\n" + "=" * 70)
        print(f"📊 Test Summary: {passed_tests}/{total_tests} passed")
        if all_passed:
            print("✅ ALL TESTS PASSED - Inventory validation working")
            return 0
        print(
            f"❌ {total_tests - passed_tests} TESTS FAILED - "
            f"Inventory cheating not properly blocked"
        )
        return 2

    finally:
        if client is not None and created_campaigns:
            for user_id, campaign_id in created_campaigns:
                try:
                    client.tools_call(
                        "delete_campaign",
                        {"user_id": user_id, "campaign_id": campaign_id},
                    )
                except Exception as exc:  # noqa: BLE001
                    print(f"⚠️ Cleanup failed for campaign {campaign_id}: {exc}")

        if local is not None:
            print("\n🛑 Stopping local MCP server...")
            local.stop()


if __name__ == "__main__":
    sys.exit(main())
