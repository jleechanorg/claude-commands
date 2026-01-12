#!/usr/bin/env python3
"""Test LLM's ability to refuse or clarify mechanically impossible player actions.

This test validates that the LLM properly handles situations where players request
actions that are mechanically impossible according to D&D 5e rules, such as:
- Casting spells without spell slots
- Using class features when resources are exhausted
- Attempting actions beyond character capabilities

The LLM should either:
1. REFUSE: Reject the action with a narrative explanation
2. CLARIFY: Offer alternatives (e.g., upcast with higher slot)

Run (local MCP already running):
    cd testing_mcp
    python test_llm_refuse_impossible_actions.py --server-url http://127.0.0.1:8001

Run (start local MCP automatically):
    cd testing_mcp
    python test_llm_refuse_impossible_actions.py --start-local --real-services

Run with evidence collection:
    cd testing_mcp
    python test_llm_refuse_impossible_actions.py --start-local --real-services --evidence
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from lib import MCPClient
from lib.evidence_utils import (
    get_evidence_dir,
    capture_provenance,
    create_evidence_bundle,
)
from lib.firestore_validation import validate_action_resolution_in_firestore
from lib.model_utils import DEFAULT_MODEL_MATRIX, settings_for_model, update_user_settings
from lib.server_utils import LocalServer, pick_free_port, start_local_mcp_server

# =============================================================================
# CHARACTER SETUPS - Designed with exhausted resources
# =============================================================================

CHARACTER_WIZARD_NO_SLOTS = """
Elara the Wizard (Level 5, School of Evocation)
Race: High Elf
Attributes: STR 8, DEX 14, CON 12, INT 18 (+4), WIS 12, CHA 10

SPELL SLOTS (D&D 5E Level 5 Wizard):
- 1st Level: 0/4 (ALL EXHAUSTED)
- 2nd Level: 0/3 (ALL EXHAUSTED)
- 3rd Level: 0/2 (ALL EXHAUSTED)
- NO 4th level slots (Wizard gets 4th-level slots at level 7)

Cantrips: Fire Bolt, Prestidigitation, Mage Hand, Light
Spells Known:
- 1st: Magic Missile, Shield, Mage Armor, Detect Magic
- 2nd: Misty Step, Scorching Ray
- 3rd: Fireball, Counterspell

IMPORTANT: ALL spell slots are EXHAUSTED (0 remaining at all levels).
IMPORTANT: Cannot cast ANY leveled spells until long rest.

Equipment:
- Quarterstaff, spellbook, component pouch
- Robes, 40gp
HP: 27/27
"""

CHARACTER_MONK_NO_KI = """
Kira the Monk (Level 5, Way of the Open Hand)
Race: Human
Attributes: STR 12, DEX 18 (+4), CON 14, WIS 16 (+3), INT 10, CHA 8

KI POINTS (Equal to Monk level):
- Current: 0/5 (ALL EXHAUSTED)

MARTIAL ARTS: d6
UNARMORED DEFENSE: AC 17 (10 + DEX + WIS)

Ki Abilities (Cost 1 ki each):
- Flurry of Blows: 2 bonus unarmed strikes after Attack action
- Patient Defense: Dodge action as bonus action
- Step of the Wind: Disengage/Dash as bonus action, jump doubled
- Stunning Strike: Target must save or be stunned (costs 1 ki)

IMPORTANT: Ki Points are EXHAUSTED (0 remaining).
IMPORTANT: Cannot use Flurry of Blows, Patient Defense, Step of the Wind, or Stunning Strike.

Equipment:
- Quarterstaff, 10 darts
- Monk robes
- 25gp
HP: 38/38
"""

CHARACTER_BARD_PARTIAL_SLOTS = """
Lyra the Bard (Level 5, College of Lore)
Race: Half-Elf
Attributes: STR 10, DEX 14, CON 12, INT 10, WIS 12, CHA 18 (+4)

SPELL SLOTS (D&D 5E Level 5 Bard):
- 1st Level: 0/4 (ALL EXHAUSTED)
- 2nd Level: 2/3 (2 remaining)
- 3rd Level: 2/2 (2 remaining)

Cantrips: Vicious Mockery, Minor Illusion
Spells Known:
- 1st: Healing Word, Dissonant Whispers, Faerie Fire, Charm Person
- 2nd: Hold Person, Suggestion
- 3rd: Hypnotic Pattern, Fear

BARDIC INSPIRATION (CHA mod per long rest):
- Uses: 0/4 (ALL EXHAUSTED)

IMPORTANT: 1st level spell slots are EXHAUSTED (0 remaining).
IMPORTANT: Bardic Inspiration uses are EXHAUSTED (0 remaining).
IMPORTANT: 2nd and 3rd level slots are still available.

Equipment:
- Rapier, Leather Armor (AC 13)
- Lute, component pouch
- 50gp
HP: 33/33
"""

# =============================================================================
# TEST SCENARIOS
# =============================================================================

IMPOSSIBLE_ACTION_SCENARIOS = [
    # SCENARIO 1: Cast spell with absolutely no slots available
    {
        "name": "Cast spell with 0 slots at all levels",
        "character": "WIZARD",
        "user_input": "I cast Fireball at the group of orcs charging at us!",
        "expected_behavior": "refuse",
        "description": "Wizard has 0 spell slots at all levels - Fireball requires 3rd level slot",
        # These phrases indicate the LLM INCORRECTLY allowed the spell
        "cheat_indicators": [
            "fireball explodes",
            "flames erupt",
            "orcs are engulfed",
            "fire consumes",
            "ball of fire",
            "you launch",
        ],
        # These phrases indicate the LLM CORRECTLY refused
        "refuse_indicators": [
            "no spell slots",
            "exhausted",
            "depleted",
            "cannot cast",
            "can't cast",
            "no magic",
            "no slots",
            "empty",
            "fizzle",
            "fails",
            "beyond",
            "reserves",
        ],
    },
    # SCENARIO 2: Use Ki ability with 0 Ki points
    {
        "name": "Use Flurry of Blows with 0 Ki",
        "character": "MONK",
        "user_input": "I attack the goblin and use Flurry of Blows for extra strikes!",
        "expected_behavior": "refuse",
        "description": "Monk has 0 Ki points - Flurry of Blows requires 1 Ki",
        "cheat_indicators": [
            "bonus strikes",
            "extra attacks",
            "rapid strikes",
            "flurry connects",
            "two additional",
            "four strikes",
        ],
        "refuse_indicators": [
            "no ki",
            "ki exhausted",
            "ki depleted",
            "cannot use",
            "can't use",
            "empty",
            "spent",
            "body refuses",
            "meditate",
            "short rest",
            "inner energy",
        ],
    },
    # SCENARIO 3: Cast 1st level spell with 0 1st-level slots but higher available
    {
        "name": "Cast 1st level spell with upcast option available",
        "character": "BARD",
        "user_input": "I cast Healing Word on myself!",
        "expected_behavior": "clarify",
        "description": "Bard has 0 first-level slots but 2nd/3rd level available - should offer upcast",
        "cheat_indicators": [
            # Auto-healing without asking about upcast is cheating
            # These indicate the spell ACTUALLY HAPPENED without consent
            "you heal",
            "regain hp",
            "wounds close",
            "feel better",
            "healing energy",
            "hp restored",
            # Note: We don't flag "upcast" or "2nd level slot" as cheating
            # because those phrases appear in valid clarification questions.
            # The key distinction is whether healing OCCURRED vs being OFFERED.
        ],
        "refuse_indicators": [
            # Outright refusal is acceptable
            "no 1st level",
            "first level",
            "exhausted",
            "depleted",
        ],
        "clarify_indicators": [
            # Offering upcast option is ideal
            "upcast",
            "higher level",
            "2nd level slot",
            "second level",
            "would you like",
            "do you want",
            "instead",
            "alternatively",
        ],
    },
    # SCENARIO 4: Use Bardic Inspiration with 0 uses
    {
        "name": "Use Bardic Inspiration with 0 uses",
        "character": "BARD",
        "user_input": "I give Bardic Inspiration to the fighter before his attack!",
        "expected_behavior": "refuse",
        "description": "Bard has 0 Bardic Inspiration uses - cannot inspire",
        "cheat_indicators": [
            "gains a d8",
            "inspiration die",
            "add to",
            "receives inspiration",
            "fighter gains",
            "bonus die",
        ],
        "refuse_indicators": [
            "no bardic",
            "inspiration exhausted",
            "no uses",
            "cannot inspire",
            "can't inspire",
            "depleted",
            "spent",
            "dry",
            "need a rest",
            "long rest",
        ],
    },
    # SCENARIO 5: Cast spell WAY beyond character level
    {
        "name": "Cast 7th level spell at level 5",
        "character": "WIZARD",
        "user_input": "I cast Teleport to escape to safety!",
        "expected_behavior": "refuse",
        "description": "Level 5 Wizard cannot access 7th level magic - Teleport is impossible",
        "cheat_indicators": [
            # These indicate teleportation ACTUALLY HAPPENED
            "you teleport",
            "vanish",
            "disappear",
            "materialize",
            "transported",
            "appear at",
            # Note: Removed "find yourself" - too generic, matches valid refusals
            # like "You find yourself unable to channel magic of that magnitude"
        ],
        "refuse_indicators": [
            "cannot cast",
            "can't cast",
            "too powerful",
            "beyond your",
            "level 7",
            "7th level",
            "7th-level",
            "not yet",
            "abilities",
            "magnitude",
            "access",
        ],
    },
]

CHARACTER_MAP = {
    "WIZARD": CHARACTER_WIZARD_NO_SLOTS,
    "MONK": CHARACTER_MONK_NO_KI,
    "BARD": CHARACTER_BARD_PARTIAL_SLOTS,
}

# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================


def validate_refuse_or_clarify(
    result: dict[str, Any],
    scenario: dict[str, Any],
) -> tuple[bool, str, list[str]]:
    """Validate that LLM properly handled the impossible action.

    Returns (passed, outcome, errors) tuple.
    - passed: True if test passed
    - outcome: "refused", "clarified", "cheated", or "ambiguous"
    - errors: List of specific error messages
    """
    errors: list[str] = []
    narrative = (result.get("narrative") or "").lower()

    # Check for server error
    if result.get("error"):
        return False, "error", [f"Server returned error: {result['error']}"]

    expected = scenario["expected_behavior"]
    cheat_indicators = [ind.lower() for ind in scenario.get("cheat_indicators", [])]
    refuse_indicators = [ind.lower() for ind in scenario.get("refuse_indicators", [])]
    clarify_indicators = [ind.lower() for ind in scenario.get("clarify_indicators", [])]

    # Check for cheating (LLM allowed the impossible action)
    cheats_found = [ind for ind in cheat_indicators if ind in narrative]
    has_cheat = bool(cheats_found)

    # Check for proper refusal
    refuses_found = [ind for ind in refuse_indicators if ind in narrative]
    has_refuse = bool(refuses_found)

    # Check for clarification (asking about alternatives)
    clarifies_found = [ind for ind in clarify_indicators if ind in narrative]
    has_clarify = bool(clarifies_found)

    # Also check planning_block for clarification choices
    planning_block = result.get("planning_block") or {}
    choices = planning_block.get("choices") or {}
    choices_text = " ".join(
        f"{k} {str(v.get('text', '') or '')} {str(v.get('description', '') or '')}"
        for k, v in choices.items()
        if isinstance(v, dict)
    ).lower()
    if any(ind in choices_text for ind in clarify_indicators):
        has_clarify = True

    # Determine outcome
    if has_cheat and not has_refuse and not has_clarify:
        outcome = "cheated"
        errors.append(
            f"CHEAT DETECTED: LLM allowed impossible action. "
            f"Indicators found: {cheats_found[:3]}. "
            f"Narrative: '{narrative[:150]}...'"
        )
    elif has_refuse and not has_cheat:
        outcome = "refused"
    elif has_clarify and not has_cheat:
        outcome = "clarified"
    elif has_refuse or has_clarify:
        # Has both refuse/clarify AND cheat indicators - ambiguous
        outcome = "ambiguous"
        errors.append(
            f"AMBIGUOUS: Found both refusal AND cheat indicators. "
            f"Cheats: {cheats_found[:2]}, Refuses: {refuses_found[:2]}. "
            f"Manual review needed. Narrative: '{narrative[:150]}...'"
        )
    else:
        outcome = "ambiguous"
        errors.append(
            f"AMBIGUOUS: No clear refuse, clarify, or cheat indicators found. "
            f"Narrative: '{narrative[:150]}...'"
        )

    # Determine if test passed based on expected behavior
    if expected == "refuse":
        passed = outcome == "refused"
    elif expected == "clarify":
        passed = outcome in ("clarified", "refused")  # Refusing is also acceptable
    else:
        passed = outcome in ("refused", "clarified")

    if not passed and not errors:
        errors.append(
            f"Expected '{expected}' but got '{outcome}'. "
            f"Narrative: '{narrative[:150]}...'"
        )

    return passed, outcome, errors


# Evidence saving is now handled by create_evidence_bundle at the end
# Individual scenario evidence is collected in results dict


# =============================================================================
# MAIN TEST RUNNER
# =============================================================================


def run_tests(
    client: MCPClient,
    model_id: str,
    scenarios: list[dict],
    evidence_dir: Path | None,
    created_campaigns: list[tuple[str, str]],
    save_evidence: bool = True,
) -> tuple[int, int, list[dict]]:
    """Run test scenarios and return (passed, total, results) tuple."""
    passed = 0
    total = 0
    results = []

    # Group scenarios by character
    by_char: dict[str, list[dict]] = {}
    for s in scenarios:
        char = s.get("character", "WIZARD")
        by_char.setdefault(char, []).append(s)

    for char_name, char_scenarios in by_char.items():
        # Setup: Create campaign with character
        model_settings = settings_for_model(model_id)
        model_settings["debug_mode"] = True
        user_id = f"refuse-test-{char_name.lower()}-{model_id.replace('/', '-')[:20]}-{int(time.time())}"

        update_user_settings(client, user_id=user_id, settings=model_settings)

        character_sheet = CHARACTER_MAP.get(char_name, CHARACTER_WIZARD_NO_SLOTS)
        campaign_result = client.tools_call(
            "create_campaign",
            {
                "user_id": user_id,
                "title": f"Refuse/Clarify Test - {char_name}",
                "character": character_sheet,
                "setting": "You stand in a dangerous dungeon. Enemies approach.",
                "description": f"Test for LLM refusing impossible actions ({char_name})",
            },
        )

        campaign_id = campaign_result.get("campaign_id") or campaign_result.get("campaignId")
        if not isinstance(campaign_id, str) or not campaign_id:
            print(f"   Failed to create campaign for {char_name}: {campaign_result}")
            # Count these scenarios as skipped/failed since we couldn't run them
            for scenario in char_scenarios:
                total += 1
                print(f"\n   [{total}] SKIPPED: {scenario['name']} (Setup Failed)")
            continue

        print(f"\n   Campaign created ({char_name}): {campaign_id[:12]}...")
        created_campaigns.append((user_id, campaign_id))

        # Run each scenario
        for scenario in char_scenarios:
            total += 1
            name = scenario["name"]
            user_input = scenario["user_input"]
            expected = scenario["expected_behavior"]

            print(f"\n   [{total}] Testing: {name}")
            print(f'       Input: "{user_input[:50]}..."')
            print(f"       Expected: {expected.upper()}")

            # Execute action
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
                    result = future.result(timeout=90.0)
                except FuturesTimeoutError:
                    print("       TIMEOUT after 90s")
                    continue

            # Validate
            test_passed, outcome, errors = validate_refuse_or_clarify(result, scenario)

            # Validate Firestore persistence (CRITICAL: Check that audit trail is actually saved)
            firestore_validation = validate_action_resolution_in_firestore(
                user_id=user_id,
                campaign_id=campaign_id,
                limit=1,  # Check latest entry (should be the one we just created)
                require_audit_flags=True,
            )
            
            # Merge Firestore validation errors
            combined_errors = list(errors)
            combined_errors.extend(firestore_validation["errors"])
            
            # Test fails if either API validation OR Firestore validation fails
            # Note: Firestore validation warnings don't fail the test, but errors do
            final_passed = test_passed and firestore_validation["passed"]

            # Collect evidence for bundle
            # Use 'passed' field (not 'validation_passed') to match evidence bundle expectations
            scenario_result = {
                "model_id": model_id,
                "scenario_name": scenario["name"],
                "scenario_description": scenario["description"],
                "user_input": scenario["user_input"],
                "expected_behavior": scenario["expected_behavior"],
                "actual_outcome": outcome,
                "passed": final_passed,  # Evidence bundle expects 'passed' field
                "errors": combined_errors if not final_passed else [],  # Only include errors if failed
                "narrative": result.get("narrative", ""),
                "planning_block": result.get("planning_block", {}),
                "state_updates": result.get("state_updates", {}),
                "debug_info": result.get("debug_info", {}),
                "firestore_validation": {
                    "passed": firestore_validation["passed"],
                    "entries_checked": firestore_validation["entries_checked"],
                    "entries_with_action_resolution": firestore_validation["entries_with_action_resolution"],
                    "warnings": firestore_validation["warnings"],
                },
            }
            results.append(scenario_result)

            # Report
            if final_passed:
                passed += 1
                print(f"       PASSED: LLM {outcome} the impossible action")
                if firestore_validation["warnings"]:
                    for warn in firestore_validation["warnings"][:1]:
                        print(f"         ⚠️  {warn}")
            else:
                print(f"       FAILED: {outcome}")
                for err in combined_errors[:3]:
                    print(f"         {err}")

    return passed, total, results


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Test LLM's ability to refuse/clarify impossible D&D actions"
    )
    parser.add_argument(
        "--server-url",
        default=os.environ.get("MCP_SERVER_URL") or "http://127.0.0.1:8001",
        help="Base server URL",
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
        help="Port for --start-local (0 = random)",
    )
    parser.add_argument(
        "--models",
        default=os.environ.get("MCP_TEST_MODELS", ""),
        help="Comma-separated model IDs to test (default: all in matrix)",
    )
    parser.add_argument(
        "--real-services",
        action="store_true",
        help="Use real API providers (requires API keys)",
    )
    args = parser.parse_args()

    local: LocalServer | None = None
    client: MCPClient | None = None
    created_campaigns: list[tuple[str, str]] = []
    base_url = str(args.server_url)

    try:
        # Always use gemini-3-flash-preview
        models = ["gemini-3-flash-preview"]

        # Start server if requested
        if args.start_local:
            port = args.port if args.port > 0 else pick_free_port()
            # Use first model as server default to avoid 403 on preview models
            first_model = models[0] if models else "gemini-2.0-flash"
            env_overrides = {
                "MOCK_SERVICES_MODE": "false" if args.real_services else "true",
                "TESTING": "false",
                "CAPTURE_EVIDENCE": "true",
            }
            
            # Only set default if it looks like a Gemini model
            if "gemini" in first_model.lower():
                env_overrides["WORLDAI_DEFAULT_GEMINI_MODEL"] = first_model

            local = start_local_mcp_server(port, env_overrides=env_overrides)
            base_url = local.base_url
            print(f"Local MCP server started on {base_url}")
            print(f"Log file: {local.log_path}")
            print(f"Default model: {first_model}")

        client = MCPClient(base_url, timeout_s=180.0)
        client.wait_healthy(timeout_s=45.0)
        print(f"MCP server healthy at {base_url}\n")

        # Evidence directory (always generated)
        evidence_dir = get_evidence_dir("llm_refuse_impossible")
        print(f"📂 Evidence directory: {evidence_dir}\n")
        save_evidence = True

        total_passed = 0
        total_ran = 0
        all_results = []

        print("=" * 70)
        print("LLM REFUSE/CLARIFY IMPOSSIBLE ACTIONS TEST")
        print("=" * 70)
        print(f"Models: {', '.join(models)}")
        print(f"Scenarios: {len(IMPOSSIBLE_ACTION_SCENARIOS)}")
        print("=" * 70)

        for model_id in models:
            print(f"\nTesting model: {model_id}")
            print("-" * 70)

            passed, ran, model_results = run_tests(
                client, model_id, IMPOSSIBLE_ACTION_SCENARIOS, evidence_dir, created_campaigns, True
            )
            total_passed += passed
            total_ran += ran
            all_results.extend(model_results)

        # Save evidence bundle (always generated)
        if evidence_dir and all_results:
            provenance = capture_provenance(base_url=base_url, server_pid=None)
            test_results = {
                "scenarios": all_results,
                "test_result": {
                    "passed": total_passed,
                    "total": total_ran,
                },
            }
            request_responses = client.get_captures_as_dict()
            create_evidence_bundle(
                evidence_dir=evidence_dir,
                test_name="llm_refuse_impossible_actions",
                provenance=provenance,
                results=test_results,
                request_responses=request_responses,
                methodology_text=None,
            )
            print(f"\n✅ Evidence saved to: {evidence_dir}")

        # Summary
        print("\n" + "=" * 70)
        print(f"SUMMARY: {total_passed}/{total_ran} passed")

        if total_ran == 0:
            print("NO TESTS RAN - Campaign creation or setup failed for all scenarios")
            return 3

        if total_passed == total_ran:
            print("ALL TESTS PASSED - LLM properly refuses/clarifies impossible actions")
            return 0

        failed = max(total_ran - total_passed, 0)
        print(f"{failed} TESTS FAILED - LLM allowed impossible actions")
        return 2

    finally:
        # Cleanup campaigns
        if client is not None and created_campaigns:
            for user_id, campaign_id in created_campaigns:
                try:
                    client.tools_call(
                        "delete_campaign",
                        {"user_id": user_id, "campaign_id": campaign_id},
                    )
                except Exception as exc:
                    print(f"Cleanup failed for {campaign_id}: {exc}")

        if local is not None:
            print("\nStopping local MCP server...")
            local.stop()


if __name__ == "__main__":
    sys.exit(main())
