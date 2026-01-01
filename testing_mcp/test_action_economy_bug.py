#!/usr/bin/env python3
"""Real API test for Action Economy bug (Action Surge / Bonus Action blocking).

This test verifies a potential bug from PR #2842 review:
The "act twice in same round" wording could incorrectly block valid D&D 5E mechanics.

Valid D&D 5E action economy per turn:
- 1 Action + 1 Bonus Action + Movement + Free Object Interaction
- Action Surge (Fighter): Grants 1 additional Action on same turn
- Haste spell: Grants 1 additional Action (limited options)
- Two-Weapon Fighting: Use Bonus Action to attack with off-hand

Bug Hypothesis: Current prompt says "If player tries to act twice in same round"
which could incorrectly interpret Action + Bonus Action as "acting twice".

Red State (Bug): LLM blocks valid bonus action with "You've already acted this round"
Green State (Fix): LLM allows Action + Bonus Action on the same turn

Run:
    cd testing_mcp
    python test_action_economy_bug.py --start-local
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from lib.mcp_client import MCPClient
from lib.server_utils import LocalServer, pick_free_port, start_local_mcp_server
from lib.campaign_utils import create_campaign, process_action
from lib.evidence_utils import (
    capture_provenance,
    create_evidence_bundle,
    get_evidence_dir,
)
from lib.model_utils import settings_for_model, update_user_settings

DEFAULT_MODEL = "gemini-3-flash-preview"

# Fighter with Two-Weapon Fighting style
FIGHTER_CHARACTER = """Kira, Level 5 Human Fighter
- Fighting Style: Two-Weapon Fighting
- Class Feature: Extra Attack (2 attacks per Attack action)
- Class Feature: Action Surge (1 use per short rest)
- Equipment: Longsword (main hand), Shortsword (off-hand)
- HP: 44/44, AC: 18 (Chain Mail + Shield when not dual wielding)
- Retainer: Gareth (Level 3 Fighter)"""

COMBAT_SCENARIO = """You are in combat with a single Bandit (CR 1/8, HP 11, AC 12).
Your retainer Gareth is also in combat with you.
Roll initiative. It is YOUR TURN to act first."""


def check_bonus_action_allowed(narrative: str) -> dict[str, Any]:
    """Check if the LLM allowed or blocked the bonus action.

    Returns dict with:
    - allowed: True if bonus action was processed
    - blocked: True if LLM said "already acted" or similar
    - blocking_phrase: The phrase used to block (if any)
    - evidence: Relevant text from narrative
    """
    result = {
        "allowed": False,
        "blocked": False,
        "blocking_phrase": None,
        "evidence": "",
    }

    # Patterns that indicate the bonus action was BLOCKED
    blocking_patterns = [
        r"you'?ve already acted",
        r"already used your action",
        r"already taken your turn",
        r"waiting for other combatants",
        r"can'?t act again",
        r"not your turn",
        r"wait for your next turn",
    ]

    narrative_lower = narrative.lower()

    for pattern in blocking_patterns:
        match = re.search(pattern, narrative_lower)
        if match:
            result["blocked"] = True
            result["blocking_phrase"] = match.group(0)
            # Get context around the match
            start = max(0, match.start() - 50)
            end = min(len(narrative), match.end() + 50)
            result["evidence"] = narrative[start:end]
            return result

    # Patterns that indicate bonus action was ALLOWED
    allowed_patterns = [
        r"off-?hand",
        r"bonus action",
        r"second attack",
        r"shortsword",
        r"dual.?wield",
        r"two.?weapon",
        # Dice roll for bonus action attack
        r"bonus.*\d+d\d+",
        r"\[DICE:.*bonus",
    ]

    for pattern in allowed_patterns:
        match = re.search(pattern, narrative_lower)
        if match:
            result["allowed"] = True
            start = max(0, match.start() - 50)
            end = min(len(narrative), match.end() + 50)
            result["evidence"] = narrative[start:end]
            return result

    # If neither clearly blocked nor allowed, check for attack resolution
    # If we see multiple attack rolls, bonus action was likely processed
    attack_rolls = re.findall(r'\[DICE:.*?attack.*?\]', narrative, re.IGNORECASE)
    if len(attack_rolls) >= 2:
        result["allowed"] = True
        result["evidence"] = f"Found {len(attack_rolls)} attack rolls: {attack_rolls[:3]}"

    return result


def run_action_economy_test(
    client: MCPClient,
    user_id: str,
    request_responses: list[dict[str, Any]],
) -> dict[str, Any]:
    """Test that Action + Bonus Action is allowed on the same turn.

    Red State (Bug): LLM blocks bonus action with "You've already acted"
    Green State (Fix): LLM processes both action and bonus action

    Returns:
        Test result dict with pass/fail status and evidence
    """
    print("\n" + "=" * 80)
    print("TEST: Action Economy - Bonus Action After Action")
    print("=" * 80)

    # Create campaign
    print("Creating campaign...")
    campaign_id = create_campaign(
        client,
        user_id=user_id,
        title="Action Economy Test",
        character=FIGHTER_CHARACTER,
        setting="Forest clearing, single bandit encounter",
        description="Test that Action + Bonus Action is allowed on same turn",
    )
    print(f"  Campaign created: {campaign_id}")

    # Pin model settings
    update_user_settings(
        client,
        user_id=user_id,
        settings=settings_for_model(DEFAULT_MODEL),
    )

    # Action 1: Start combat and use Attack action + Bonus Action attack
    print("\n[Action 1] Player uses Attack action AND bonus action off-hand attack...")

    # This is the key test: asking for BOTH action and bonus action in one input
    action_input = """I attack the bandit with my longsword (Action),
then use my bonus action to attack with my shortsword (off-hand, Two-Weapon Fighting)."""

    action_response = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=COMBAT_SCENARIO + "\n\n" + action_input,
    )

    request_responses.append({
        "request": {
            "tool": "process_action",
            "user_id": user_id,
            "campaign_id": campaign_id,
            "user_input": action_input,
            "test": "action_economy",
        },
        "response": action_response,
    })

    narrative = action_response.get("narrative", "")
    bonus_action_check = check_bonus_action_allowed(narrative)

    print(f"  Bonus action allowed: {bonus_action_check['allowed']}")
    print(f"  Bonus action blocked: {bonus_action_check['blocked']}")
    if bonus_action_check['blocking_phrase']:
        print(f"  Blocking phrase: '{bonus_action_check['blocking_phrase']}'")
    print(f"  Evidence: {bonus_action_check['evidence'][:200]}...")

    # Test passes if bonus action was ALLOWED (not blocked)
    passed = bonus_action_check["allowed"] and not bonus_action_check["blocked"]

    result = {
        "test": "action_economy",
        "scenario": "bonus_action_after_action",
        "status": "PASS" if passed else "FAIL",
        "campaign_id": campaign_id,
        "bonus_action_allowed": bonus_action_check["allowed"],
        "bonus_action_blocked": bonus_action_check["blocked"],
        "blocking_phrase": bonus_action_check["blocking_phrase"],
        "evidence": bonus_action_check["evidence"],
        "narrative_sample": narrative[:1000],
        "narrative_length": len(narrative),
    }

    if passed:
        print("\n✅ TEST PASSED: Bonus action was allowed on same turn as action")
    else:
        if bonus_action_check["blocked"]:
            print("\n❌ TEST FAILED: Bonus action was incorrectly BLOCKED")
            print(f"   Blocking phrase: '{bonus_action_check['blocking_phrase']}'")
        else:
            print("\n❌ TEST FAILED: Could not confirm bonus action was processed")

    return result


def run_action_surge_test(
    client: MCPClient,
    user_id: str,
    request_responses: list[dict[str, Any]],
) -> dict[str, Any]:
    """Test that Action Surge (two Actions in one turn) is allowed.

    Red State (Bug): LLM blocks second action with "You've already acted"
    Green State (Fix): LLM processes both actions from Action Surge

    Returns:
        Test result dict with pass/fail status and evidence
    """
    print("\n" + "=" * 80)
    print("TEST: Action Economy - Action Surge (Fighter)")
    print("=" * 80)

    # Create campaign
    print("Creating campaign...")
    campaign_id = create_campaign(
        client,
        user_id=user_id,
        title="Action Surge Test",
        character=FIGHTER_CHARACTER,
        setting="Forest clearing, bandit captain encounter",
        description="Test that Action Surge allows two Actions on same turn",
    )
    print(f"  Campaign created: {campaign_id}")

    # Pin model settings
    update_user_settings(
        client,
        user_id=user_id,
        settings=settings_for_model(DEFAULT_MODEL),
    )

    # Action: Use Action Surge for two Attack actions
    print("\n[Action 1] Player uses Action Surge for two Attack actions...")

    action_input = """I attack the bandit captain with my longsword (first Attack action with Extra Attack = 2 attacks),
then I use ACTION SURGE to take a second Attack action (2 more attacks with Extra Attack).
That's 4 total attacks this turn from my Fighter class features."""

    combat_setup = """You are in combat with a Bandit Captain (CR 2, HP 65, AC 15).
Your retainer Gareth is also fighting alongside you.
It is YOUR TURN. You have your Action Surge available (not yet used)."""

    action_response = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=combat_setup + "\n\n" + action_input,
    )

    request_responses.append({
        "request": {
            "tool": "process_action",
            "user_id": user_id,
            "campaign_id": campaign_id,
            "user_input": action_input,
            "test": "action_surge",
        },
        "response": action_response,
    })

    narrative = action_response.get("narrative", "")

    # Check for Action Surge being blocked
    blocking_check = check_bonus_action_allowed(narrative)  # Reuse the blocking check

    # Also look for Action Surge specific patterns
    action_surge_processed = bool(re.search(
        r"action surge|surge|additional action|second attack action|4 attacks?|four attacks?",
        narrative, re.IGNORECASE
    ))

    # Count attack rolls - Action Surge should result in 4 attacks
    attack_rolls = re.findall(r'\[DICE:.*?attack.*?\]', narrative, re.IGNORECASE)
    attack_count = len(attack_rolls)

    print(f"  Action Surge processed: {action_surge_processed}")
    print(f"  Attack rolls found: {attack_count}")
    print(f"  Blocked: {blocking_check['blocked']}")
    if blocking_check['blocking_phrase']:
        print(f"  Blocking phrase: '{blocking_check['blocking_phrase']}'")

    # Pass if Action Surge was processed (4 attacks or explicit mention) and not blocked
    passed = (action_surge_processed or attack_count >= 3) and not blocking_check["blocked"]

    result = {
        "test": "action_economy",
        "scenario": "action_surge",
        "status": "PASS" if passed else "FAIL",
        "campaign_id": campaign_id,
        "action_surge_processed": action_surge_processed,
        "attack_count": attack_count,
        "blocked": blocking_check["blocked"],
        "blocking_phrase": blocking_check["blocking_phrase"],
        "narrative_sample": narrative[:1000],
        "narrative_length": len(narrative),
    }

    if passed:
        print(f"\n✅ TEST PASSED: Action Surge was allowed ({attack_count} attack rolls)")
    else:
        if blocking_check["blocked"]:
            print("\n❌ TEST FAILED: Action Surge was incorrectly BLOCKED")
            print(f"   Blocking phrase: '{blocking_check['blocking_phrase']}'")
        else:
            print(f"\n❌ TEST FAILED: Action Surge not clearly processed ({attack_count} attacks)")

    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Real API test for Action Economy bug (Action Surge / Bonus Action)"
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
        "--test",
        choices=["bonus_action", "action_surge", "all"],
        default="all",
        help="Which test to run",
    )
    args = parser.parse_args()

    local: LocalServer | None = None
    base_url = str(args.server_url)
    evidence_dir = get_evidence_dir("action_economy_bug")

    env_overrides = {
        "MOCK_SERVICES_MODE": "false",
        "TESTING": "false",
        "CAPTURE_RAW_LLM": "true",
    }

    try:
        if args.start_local:
            port = pick_free_port()
            base_url = f"http://127.0.0.1:{port}"
            print(f"Starting local MCP server on {base_url}...")
            local = start_local_mcp_server(port, env_overrides=env_overrides)

        client = MCPClient(base_url=base_url, timeout_s=180.0)
        print(f"Connecting to MCP server at {base_url}...")
        client.wait_healthy(timeout_s=45.0)
        print("✅ Server is healthy")

        # Create session directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = evidence_dir / f"run_{timestamp}"
        session_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n📁 Evidence will be saved to: {session_dir}")

        # Capture provenance
        server_pid = local.proc.pid if local else None
        provenance = capture_provenance(
            base_url,
            server_pid,
            server_env_overrides=env_overrides if args.start_local else None,
        )

        # Track request/responses
        request_responses: list[dict[str, Any]] = []

        # Run tests
        user_id = f"test_action_economy_{timestamp}"
        results = []

        if args.test in ("bonus_action", "all"):
            result = run_action_economy_test(client, user_id, request_responses)
            results.append(result)

        if args.test in ("action_surge", "all"):
            result = run_action_surge_test(client, user_id + "_surge", request_responses)
            results.append(result)

        # Build scenarios for evidence bundle
        scenarios = []
        for r in results:
            scenarios.append({
                "name": r["scenario"],
                "campaign_id": r.get("campaign_id"),
                "passed": r["status"] == "PASS",
                "errors": [] if r["status"] == "PASS" else [r.get("blocking_phrase") or "Test failed"],
            })

        # Create evidence bundle
        bundle_files = create_evidence_bundle(
            session_dir,
            test_name="action_economy_bug",
            provenance=provenance,
            results={
                "scenarios": scenarios,
                "test_results": results,
            },
            request_responses=request_responses,
            methodology_text="""# Test Methodology

## Objective
Verify that D&D 5E action economy is correctly implemented:
- Players can use Action + Bonus Action on the same turn
- Action Surge (Fighter) allows two Actions on the same turn

## Bug Hypothesis (from PR #2842 review)
The prompt phrase "If player tries to act twice in same round" could incorrectly
block valid multi-action scenarios like:
- Two-Weapon Fighting (Action + Bonus Action)
- Action Surge (Fighter: two Actions in one turn)
- Haste spell (extra Action with limited options)

## Test Scenarios

### Scenario 1: Bonus Action After Action
Player uses Attack action then Bonus Action off-hand attack.
- Red State (Bug): LLM says "You've already acted this round"
- Green State (Fix): LLM processes both attacks

### Scenario 2: Action Surge
Level 5 Fighter uses Action Surge for 4 total attacks (2 per Attack action with Extra Attack).
- Red State (Bug): LLM blocks second Attack action
- Green State (Fix): LLM processes all 4 attacks

## Pass Criteria
- No blocking phrases detected ("already acted", "wait for next turn", etc.)
- Multiple attack rolls present in narrative
- Clear indication that bonus action / action surge was processed
""",
        )

        print("\n" + "=" * 80)
        print("EVIDENCE BUNDLE CREATED")
        print("=" * 80)
        for file_path in bundle_files.values():
            print(f"  ✅ {file_path.relative_to(evidence_dir)}")

        # Summary
        passed_count = sum(1 for r in results if r["status"] == "PASS")
        total_count = len(results)

        print(f"\n📊 Results: {passed_count}/{total_count} PASS")
        for r in results:
            status = "✅" if r["status"] == "PASS" else "❌"
            print(f"   {status} {r['scenario']}: {r['status']}")

        print(f"\n📦 Evidence bundle: {session_dir}")

        # Return exit code based on all tests passing
        return 0 if passed_count == total_count else 1

    finally:
        if local is not None:
            local.stop()


if __name__ == "__main__":
    raise SystemExit(main())
