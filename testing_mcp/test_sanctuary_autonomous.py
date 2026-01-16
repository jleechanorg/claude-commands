#!/usr/bin/env python3
"""
Autonomous Sanctuary Mode Tests

Tests that prove LLM AUTONOMOUSLY recognizes quest completion without explicit
completion language. Also tests natural expiration, overwrite protection, and
all duration scales.

Key differentiator from test_sanctuary_mode.py:
- NO explicit "quest complete" language
- Player defeats boss → says neutral action → LLM recognizes victory autonomously
- Evidence logs trigger_source to prove autonomous detection

Evidence standards: .claude/skills/evidence-standards.md
"""
import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# ✅ MANDATORY: Use shared library utilities
from testing_mcp.lib.campaign_utils import (
    advance_to_living_world_turn,
    create_campaign,
    end_combat_if_active,
    ensure_story_mode,
    get_campaign_state,
    get_turn_count,
    process_action,
    reset_turn_tracking,
)
from testing_mcp.lib.evidence_utils import (
    capture_provenance,
    create_evidence_bundle,
    get_evidence_dir,
    save_request_responses,
)
from testing_mcp.lib.mcp_client import MCPClient
from testing_mcp.lib.model_utils import settings_for_model, update_user_settings
from testing_mcp.lib.server_utils import pick_free_port, start_local_mcp_server

# Test configuration
WORK_NAME = "sanctuary_autonomous"
DEFAULT_MODEL = "gemini-3-flash-preview"  # Pin model to avoid fallback noise
AUTONOMOUS_RUNS = 10  # Number of iterations for statistical test
AUTONOMOUS_SUCCESS_RATE = 0.70  # Require 70%+ success


def extract_sanctuary_mode(game_state: dict) -> dict:
    """Extract sanctuary_mode from game state."""
    return game_state.get("custom_campaign_state", {}).get("sanctuary_mode", {})


def get_current_turn(game_state: dict) -> int:
    """Get current turn number from game state."""
    return game_state.get("player_turn", 0)


def test_autonomous_activation(
    client: MCPClient, user_id: str, run_number: int, request_responses: list
) -> dict:
    """
    Test autonomous sanctuary activation (no explicit completion language).

    Scenario:
    - Player fights through Cragmaw Hideout naturally
    - Defeats Klarg (boss) through combat
    - NO 'quest complete' language used
    - Player says neutral action: 'I search Klarg's body'
    - Verify sanctuary activates on boss defeat

    Returns dict with test results including trigger_source.
    """
    print(f"   Run {run_number + 1}/{AUTONOMOUS_RUNS}: Testing autonomous activation...")

    # Create fresh campaign
    campaign_id = create_campaign(
        client,
        user_id=user_id,
        title=f"Autonomous Test {run_number + 1}",
    )
    request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    # Exit character creation
    ensure_story_mode(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        request_responses=request_responses,
    )
    client.clear_captures()

    # Set character to level 20 to avoid level-up distractions
    level_20_state = '{"player_character_data": {"level": 20, "xp_current": 355000}}'
    process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=f"GOD_MODE_UPDATE_STATE:{level_20_state}",
        track_turn=False,
    )
    request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    # Start quest naturally
    process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input="I begin my quest to clear the goblin cave near Phandalin.",
    )
    request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    # Enter cave and fight through goblins
    process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input="I enter the goblin cave and fight through the goblins, reaching the chief's chamber.",
    )
    request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    # Defeat boss through combat (may trigger combat)
    combat_response = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input="I attack Klarg the bugbear chief with my sword.",
    )
    request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    # End combat if it started
    end_combat_if_active(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        request_responses=request_responses,
    )
    client.clear_captures()

    # CRITICAL: Neutral action with NO completion language
    # This is where LLM should autonomously recognize victory
    neutral_action = "I search Klarg's body for valuables."
    neutral_response = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=neutral_action,
    )
    request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    # Check if sanctuary activated
    state = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
    request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    game_state = state.get("game_state", {})
    sanctuary_mode = extract_sanctuary_mode(game_state)
    sanctuary_active = sanctuary_mode.get("active", False)
    current_turn = get_current_turn(game_state)

    # Analyze narrative for victory signals (prove autonomous detection)
    narrative = neutral_response.get("narrative", "").lower()
    victory_signals = [
        "complete",
        "finished",
        "victory",
        "defeated",
        "triumph",
        "success",
        "accomplished",
        "cleared",
        "conquered",
    ]
    narrative_signals = [signal for signal in victory_signals if signal in narrative]

    # Determine trigger source
    trigger_source = "unknown"
    if sanctuary_active:
        if "defeated" in narrative or "victory" in narrative:
            trigger_source = "boss_defeated"
        elif "cleared" in narrative or "conquered" in narrative:
            trigger_source = "dungeon_cleared"
        elif any(signal in narrative for signal in victory_signals):
            trigger_source = "victory_detected"
        else:
            trigger_source = "state_only"  # Activated but no narrative signals

    return {
        "run_number": run_number + 1,
        "campaign_id": campaign_id,
        "passed": sanctuary_active,
        "sanctuary_mode": sanctuary_mode,
        "current_turn": current_turn,
        "trigger_source": trigger_source,
        "player_input": neutral_action,
        "narrative_signals": narrative_signals,
        "sanctuary_activated": sanctuary_active,
        "narrative_preview": narrative[:200] if narrative else "",
    }


def test_natural_expiration(
    client: MCPClient, user_id: str, request_responses: list
) -> dict:
    """
    Test sanctuary expires naturally at expires_turn.

    - Activate sanctuary (expires_turn = current + 5)
    - Advance 6 turns with neutral actions
    - Verify sanctuary.active becomes False
    - Verify sanctuary.expired == True (if field exists)
    """
    print("📋 Testing natural expiration...")

    # Create campaign and activate sanctuary via explicit completion (for setup)
    campaign_id = create_campaign(
        client,
        user_id=user_id,
        title="Expiration Test",
    )
    request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    ensure_story_mode(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        request_responses=request_responses,
    )
    client.clear_captures()

    # Set level 20
    level_20_state = '{"player_character_data": {"level": 20, "xp_current": 355000}}'
    process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=f"GOD_MODE_UPDATE_STATE:{level_20_state}",
        track_turn=False,
    )
    request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    # Start and complete quest to activate sanctuary
    process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input="I begin my quest to clear the goblin cave.",
    )
    request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input="I enter the cave and defeat all goblins.",
    )
    request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    # Activate sanctuary with explicit completion (for test setup)
    process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input="The quest is finished. I have successfully completed the Cragmaw Hideout mission.",
    )
    request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    # Get initial sanctuary state
    state_initial = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
    request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    game_state_initial = state_initial.get("game_state", {})
    sanctuary_initial = extract_sanctuary_mode(game_state_initial)
    expires_turn = sanctuary_initial.get("expires_turn", 0)
    initial_turn = get_current_turn(game_state_initial)

    if not sanctuary_initial.get("active", False):
        return {
            "name": "Natural expiration",
            "campaign_id": campaign_id,
            "passed": False,
            "errors": ["Sanctuary not activated for expiration test"],
        }

    # Advance turns until we pass expires_turn
    turns_to_advance = expires_turn - initial_turn + 1  # +1 to ensure we pass expiration
    print(f"   Initial turn: {initial_turn}, Expires turn: {expires_turn}")
    print(f"   Advancing {turns_to_advance} turns...")

    for i in range(turns_to_advance):
        process_action(
            client,
            user_id=user_id,
            campaign_id=campaign_id,
            user_input="I rest at the inn.",
        )
        request_responses.extend(client.get_captures_as_dict())
        client.clear_captures()

    # Check sanctuary after expiration
    state_after = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
    request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    game_state_after = state_after.get("game_state", {})
    sanctuary_after = extract_sanctuary_mode(game_state_after)
    final_turn = get_current_turn(game_state_after)
    sanctuary_active_after = sanctuary_after.get("active", False)
    sanctuary_expired = sanctuary_after.get("expired", False)

    passed = not sanctuary_active_after and final_turn >= expires_turn

    return {
        "name": "Natural expiration",
        "campaign_id": campaign_id,
        "passed": passed,
        "errors": []
        if passed
        else [
            f"Sanctuary still active: {sanctuary_active_after}, "
            f"final_turn: {final_turn}, expires_turn: {expires_turn}"
        ],
        "initial_turn": initial_turn,
        "expires_turn": expires_turn,
        "final_turn": final_turn,
        "sanctuary_active_after": sanctuary_active_after,
        "sanctuary_expired": sanctuary_expired,
        "sanctuary_after": sanctuary_after,
    }


def test_overwrite_protection(
    client: MCPClient, user_id: str, request_responses: list
) -> dict:
    """
    Test Epic sanctuary isn't overwritten by Medium completion.

    - Complete Epic arc -> sanctuary expires turn 30
    - At turn 15, complete Medium side quest
    - Verify Epic sanctuary preserved (still expires turn 30)
    """
    print("📋 Testing overwrite protection...")

    campaign_id = create_campaign(
        client,
        user_id=user_id,
        title="Overwrite Protection Test",
    )
    request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    ensure_story_mode(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        request_responses=request_responses,
    )
    client.clear_captures()

    # Set level 20
    level_20_state = '{"player_character_data": {"level": 20, "xp_current": 355000}}'
    process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=f"GOD_MODE_UPDATE_STATE:{level_20_state}",
        track_turn=False,
    )
    request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    # Complete Epic arc (via explicit completion for test setup)
    process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input="I complete the epic quest chain that saves the kingdom. This is an EPIC arc completion.",
    )
    request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    # Get Epic sanctuary state
    state_epic = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
    request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    game_state_epic = state_epic.get("game_state", {})
    sanctuary_epic = extract_sanctuary_mode(game_state_epic)
    epic_expires_turn = sanctuary_epic.get("expires_turn", 0)
    epic_scale = sanctuary_epic.get("scale", "")

    if epic_scale != "epic" or not sanctuary_epic.get("active", False):
        return {
            "name": "Overwrite protection",
            "campaign_id": campaign_id,
            "passed": False,
            "errors": [
                f"Epic sanctuary not activated: scale={epic_scale}, "
                f"active={sanctuary_epic.get('active')}"
            ],
        }

    # Advance to turn 15 (midway through Epic sanctuary)
    current_turn = get_current_turn(game_state_epic)
    turns_to_advance = 15 - current_turn
    if turns_to_advance > 0:
        print(f"   Advancing {turns_to_advance} turns to reach turn 15...")
        for _ in range(turns_to_advance):
            process_action(
                client,
                user_id=user_id,
                campaign_id=campaign_id,
                user_input="I continue my journey.",
            )
            request_responses.extend(client.get_captures_as_dict())
            client.clear_captures()

    # Complete Medium side quest (should NOT overwrite Epic)
    process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input="I complete a medium side quest. This is a MEDIUM scale completion.",
    )
    request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    # Check sanctuary after Medium completion
    state_after = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
    request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    game_state_after = state_after.get("game_state", {})
    sanctuary_after = extract_sanctuary_mode(game_state_after)
    after_expires_turn = sanctuary_after.get("expires_turn", 0)
    after_scale = sanctuary_after.get("scale", "")

    # Epic should be preserved (expires_turn should still be epic_expires_turn)
    passed = (
        after_expires_turn == epic_expires_turn
        and after_scale == "epic"
        and sanctuary_after.get("active", False)
    )

    return {
        "name": "Overwrite protection",
        "campaign_id": campaign_id,
        "passed": passed,
        "errors": []
        if passed
        else [
            f"Epic sanctuary overwritten: epic_expires={epic_expires_turn}, "
            f"after_expires={after_expires_turn}, after_scale={after_scale}"
        ],
        "epic_expires_turn": epic_expires_turn,
        "epic_scale": epic_scale,
        "after_expires_turn": after_expires_turn,
        "after_scale": after_scale,
        "sanctuary_after": sanctuary_after,
    }


def test_duration_scale(
    client: MCPClient, user_id: str, scale: str, expected_duration: int, request_responses: list
) -> dict:
    """
    Test duration calculation for a specific scale.

    Args:
        scale: "minor", "medium", "major", or "epic"
        expected_duration: Expected duration in turns (3, 5, 10, or 20)
    """
    print(f"📋 Testing {scale} scale (expected duration: {expected_duration} turns)...")

    campaign_id = create_campaign(
        client,
        user_id=user_id,
        title=f"Duration Test - {scale}",
    )
    request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    ensure_story_mode(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        request_responses=request_responses,
    )
    client.clear_captures()

    # Set level 20
    level_20_state = '{"player_character_data": {"level": 20, "xp_current": 355000}}'
    process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=f"GOD_MODE_UPDATE_STATE:{level_20_state}",
        track_turn=False,
    )
    request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    # Complete quest with explicit scale language
    scale_completion_text = {
        "minor": "I complete a minor task. This is a MINOR scale completion.",
        "medium": "I complete a medium side quest. This is a MEDIUM scale completion.",
        "major": "I complete a major quest chain. This is a MAJOR scale completion.",
        "epic": "I complete an epic quest that saves the kingdom. This is an EPIC scale completion.",
    }

    process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=scale_completion_text.get(scale, scale_completion_text["medium"]),
    )
    request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    # Check sanctuary duration
    state = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
    request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    game_state = state.get("game_state", {})
    sanctuary_mode = extract_sanctuary_mode(game_state)
    activated_turn = sanctuary_mode.get("activated_turn", 0)
    expires_turn = sanctuary_mode.get("expires_turn", 0)
    actual_duration = expires_turn - activated_turn
    actual_scale = sanctuary_mode.get("scale", "")

    passed = (
        actual_duration == expected_duration
        and actual_scale.lower() == scale.lower()
        and sanctuary_mode.get("active", False)
    )

    return {
        "name": f"Duration scale: {scale}",
        "campaign_id": campaign_id,
        "passed": passed,
        "errors": []
        if passed
        else [
            f"Duration mismatch: expected={expected_duration}, "
            f"actual={actual_duration}, scale={actual_scale}"
        ],
        "scale": scale,
        "expected_duration": expected_duration,
        "actual_duration": actual_duration,
        "activated_turn": activated_turn,
        "expires_turn": expires_turn,
        "actual_scale": actual_scale,
        "sanctuary_mode": sanctuary_mode,
    }


def run_tests(server_url: str) -> tuple[list, list]:
    """Run all autonomous sanctuary mode tests."""
    client = MCPClient(server_url)
    user_id = f"test-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"

    # Pin model
    update_user_settings(
        client,
        user_id=user_id,
        settings=settings_for_model(DEFAULT_MODEL),
    )

    results = []
    request_responses = []

    # Test 1: Autonomous activation (statistical, 10 runs)
    print("📋 Test 1: Autonomous activation (statistical, 10 runs)...")
    autonomous_results = []
    for run_num in range(AUTONOMOUS_RUNS):
        reset_turn_tracking()  # Reset turn tracking for clean runs
        result = test_autonomous_activation(client, user_id, run_num, request_responses)
        autonomous_results.append(result)

    # Calculate success rate
    successful_runs = sum(1 for r in autonomous_results if r.get("passed", False))
    success_rate = successful_runs / AUTONOMOUS_RUNS
    passed = success_rate >= AUTONOMOUS_SUCCESS_RATE

    results.append(
        {
            "name": "Autonomous activation (statistical)",
            "passed": passed,
            "success_rate": success_rate,
            "successful_runs": successful_runs,
            "total_runs": AUTONOMOUS_RUNS,
            "required_rate": AUTONOMOUS_SUCCESS_RATE,
            "runs": autonomous_results,
            "errors": []
            if passed
            else [
                f"Success rate {success_rate:.1%} below required {AUTONOMOUS_SUCCESS_RATE:.1%}"
            ],
        }
    )

    # Test 2: Natural expiration
    reset_turn_tracking()
    result = test_natural_expiration(client, user_id, request_responses)
    results.append(result)

    # Test 3: Overwrite protection
    reset_turn_tracking()
    result = test_overwrite_protection(client, user_id, request_responses)
    results.append(result)

    # Test 4: Duration scales (parameterized)
    print("📋 Test 4: Duration scales (parameterized)...")
    scale_tests = [
        ("minor", 3),
        ("medium", 5),
        ("major", 10),
        ("epic", 20),
    ]
    for scale, duration in scale_tests:
        reset_turn_tracking()
        result = test_duration_scale(client, user_id, scale, duration, request_responses)
        results.append(result)

    return results, request_responses


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-name", default=WORK_NAME)
    parser.add_argument("--server", help="Optional: use existing server URL")
    parser.add_argument("--quick", action="store_true", help="Quick test: reduce autonomous runs to 3")
    args = parser.parse_args()
    
    # Override runs for quick test
    global AUTONOMOUS_RUNS
    if args.quick:
        AUTONOMOUS_RUNS = 3
        print("⚡ Quick test mode: Running 3 autonomous activation tests instead of 10")

    local_server = None
    server_url = args.server

    try:
        if not server_url:
            port = pick_free_port()
            print(f"🚀 Starting fresh local MCP server on port {port}...")
            local_server = start_local_mcp_server(port)
            server_url = local_server.base_url

            client = MCPClient(server_url)
            client.wait_healthy(timeout_s=30.0)
            print(f"✅ Server ready at {server_url}")

        results, request_responses = run_tests(server_url)

        # Save evidence
        evidence_dir = get_evidence_dir(args.work_name)
        server_pid = local_server.pid if local_server else None
        provenance = capture_provenance(server_url, server_pid=server_pid)

        if request_responses:
            save_request_responses(evidence_dir, request_responses)

        bundle_files = create_evidence_bundle(
            evidence_dir=evidence_dir,
            test_name=args.work_name,
            results={"scenarios": results, "summary": {"total_scenarios": len(results)}},
            provenance=provenance,
            request_responses=request_responses,
            server_log_path=local_server.log_path if local_server else None,
        )

        print(f"📦 Evidence bundle created: {evidence_dir}")
        print(f"   Files: {len(bundle_files)} with checksums")

        # Print summary
        passed = sum(1 for r in results if r.get("passed", False))
        total = len(results)
        print(f"\n📊 Test Results: {passed}/{total} passed")
        for result in results:
            status = "✅" if result.get("passed", False) else "❌"
            name = result.get("name", "Unknown")
            if "statistical" in name.lower():
                success_rate = result.get("success_rate", 0)
                print(f"   {status} {name} ({success_rate:.1%} success rate)")
            else:
                print(f"   {status} {name}")

    finally:
        if local_server:
            print("🛑 Stopping local server...")
            local_server.stop()


if __name__ == "__main__":
    main()
