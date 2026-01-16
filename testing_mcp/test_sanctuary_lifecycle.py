#!/usr/bin/env python3
"""
Sanctuary Mode Lifecycle Test (Optimized)

Single comprehensive test that validates the complete sanctuary lifecycle:
1. Activation (autonomous or prompted)
2. Protection (blocks lethal events)
3. Natural expiration

Uses minor scale (3 turns) for fastest execution.

Evidence standards: .claude/skills/evidence-standards.md
"""
import argparse
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
    process_action,
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
WORK_NAME = "sanctuary_lifecycle"
DEFAULT_MODEL = "gemini-3-flash-preview"


def extract_sanctuary_mode(game_state: dict) -> dict:
    """Extract sanctuary_mode from game state."""
    return game_state.get("custom_campaign_state", {}).get("sanctuary_mode", {})


def get_current_turn(game_state: dict) -> int:
    """Get current turn number from game state."""
    return game_state.get("player_turn", 0)


def test_sanctuary_lifecycle(
    client: MCPClient, user_id: str, request_responses: list, autonomous: bool = False
) -> dict:
    """
    Test complete sanctuary lifecycle: activation → protection → expiration.

    Uses minor scale (3 turns) for fastest execution.

    Args:
        autonomous: If True, use neutral action after boss defeat (no explicit completion).
                   If False, use explicit completion language.
    """
    print("📋 Testing sanctuary lifecycle (activation → protection → expiration)...")

    # Create campaign
    campaign_id = create_campaign(
        client,
        user_id=user_id,
        title="Sanctuary Lifecycle Test",
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

    # Set level 20 to avoid level-up distractions
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

    # Start quest
    process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input="I begin my quest to clear the goblin cave near Phandalin.",
    )
    request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    # Enter cave and fight
    process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input="I enter the goblin cave and fight through the goblins, reaching the chief's chamber.",
    )
    request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    # Defeat boss
    process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input="I attack Klarg the bugbear chief with my sword.",
    )
    request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    # End combat if active
    end_combat_if_active(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        request_responses=request_responses,
    )
    client.clear_captures()

    # PHASE 1: ACTIVATION
    print("   Phase 1: Testing activation...")
    if autonomous:
        # Autonomous: neutral action (no completion keywords)
        activation_input = "I search Klarg's body for valuables."
        trigger_source = "autonomous"
    else:
        # Prompted: explicit completion (faster, more reliable)
        # Use more explicit language to ensure activation
        activation_input = "The quest is finished. I have successfully completed the Cragmaw Hideout mission. This is a MINOR scale quest completion."
        trigger_source = "prompted"

    activation_response = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=activation_input,
    )
    request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    # Check activation
    state_activation = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
    request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    game_state_activation = state_activation.get("game_state", {})
    sanctuary_activation = extract_sanctuary_mode(game_state_activation)
    activated_turn = get_current_turn(game_state_activation)
    expires_turn = sanctuary_activation.get("expires_turn", 0)
    duration = expires_turn - activated_turn
    sanctuary_active = sanctuary_activation.get("active", False)
    scale = sanctuary_activation.get("scale", "")

    # Focus on lifecycle validation - just verify sanctuary activated with future expiration
    # Duration validation is a separate concern (tested in duration_scale tests)
    activation_passed = (
        sanctuary_active
        and expires_turn > activated_turn
        and duration > 0  # Just verify it's a positive duration
    )

    if not activation_passed:
        return {
            "name": "Sanctuary lifecycle",
            "campaign_id": campaign_id,
            "passed": False,
            "errors": [
                f"Activation failed: active={sanctuary_active}, "
                f"duration={duration}, expires_turn={expires_turn}, "
                f"activated_turn={activated_turn}, scale={scale}"
            ],
            "phase": "activation",
            "trigger_source": trigger_source,
        }

    print(f"   ✅ Sanctuary activated: turn {activated_turn} → expires turn {expires_turn}")

    # PHASE 2: PROTECTION
    print("   Phase 2: Testing protection...")
    # Advance to a Living World turn (when complications can occur)
    current_turn, is_living_world = advance_to_living_world_turn(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        request_responses=request_responses,
        verbose=False,
    )
    client.clear_captures()

    # Take action that could trigger lethal events
    protection_response = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input="I explore the forest looking for adventure.",
    )
    request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    # Check narrative for lethal events (more specific patterns to avoid false positives)
    narrative = protection_response.get("narrative", "").lower()
    # Look for actual lethal threats, not just past-tense descriptions
    lethal_patterns = [
        "you are killed",
        "you die",
        "you are slain",
        "you are murdered",
        "you are ambushed",
        "assassination attempt",
        "lethal attack",
        "fatal blow",
    ]
    has_lethal_event = any(pattern in narrative for pattern in lethal_patterns)

    # Verify sanctuary still active
    state_protection = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
    request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    game_state_protection = state_protection.get("game_state", {})
    sanctuary_protection = extract_sanctuary_mode(game_state_protection)
    sanctuary_still_active = sanctuary_protection.get("active", False)

    protection_passed = not has_lethal_event and sanctuary_still_active

    if not protection_passed:
        return {
            "name": "Sanctuary lifecycle",
            "campaign_id": campaign_id,
            "passed": False,
            "errors": [
                f"Protection failed: lethal_event={has_lethal_event}, "
                f"sanctuary_active={sanctuary_still_active}"
            ],
            "phase": "protection",
            "trigger_source": trigger_source,
            "has_lethal_event": has_lethal_event,
            "sanctuary_still_active": sanctuary_still_active,
        }

    print(f"   ✅ Protection verified: no lethal events, sanctuary still active")

    # PHASE 3: EXPIRATION
    print("   Phase 3: Testing natural expiration...")
    # Advance past expires_turn (need to advance enough that LLM processes expiration)
    current_turn = get_current_turn(game_state_protection)
    turns_to_advance = expires_turn - current_turn + 2  # +2 to ensure expiration is processed

    print(f"   Advancing {turns_to_advance} turns past expiration (turn {expires_turn})...")
    for i in range(turns_to_advance):
        process_action(
            client,
            user_id=user_id,
            campaign_id=campaign_id,
            user_input="I rest at the inn.",
        )
        request_responses.extend(client.get_captures_as_dict())
        client.clear_captures()

    # Check expiration
    state_expiration = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
    request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    game_state_expiration = state_expiration.get("game_state", {})
    sanctuary_expiration = extract_sanctuary_mode(game_state_expiration)
    final_turn = get_current_turn(game_state_expiration)
    sanctuary_expired = not sanctuary_expiration.get("active", False)

    # Expiration should happen when final_turn > expires_turn (LLM checks at start of turn)
    expiration_passed = sanctuary_expired and final_turn > expires_turn

    if not expiration_passed:
        return {
            "name": "Sanctuary lifecycle",
            "campaign_id": campaign_id,
            "passed": False,
            "errors": [
                f"Expiration failed: active={sanctuary_expiration.get('active')}, "
                f"final_turn={final_turn}, expires_turn={expires_turn}"
            ],
            "phase": "expiration",
            "trigger_source": trigger_source,
            "final_turn": final_turn,
            "expires_turn": expires_turn,
        }

    print(f"   ✅ Expiration verified: sanctuary inactive at turn {final_turn}")

    # All phases passed
    return {
        "name": "Sanctuary lifecycle",
        "campaign_id": campaign_id,
        "passed": True,
        "errors": [],
        "trigger_source": trigger_source,
        "phases": {
            "activation": {
                "passed": activation_passed,
                "activated_turn": activated_turn,
                "expires_turn": expires_turn,
                "duration": duration,
            },
            "protection": {
                "passed": protection_passed,
                "has_lethal_event": has_lethal_event,
                "sanctuary_still_active": sanctuary_still_active,
                "turn": current_turn,
            },
            "expiration": {
                "passed": expiration_passed,
                "final_turn": final_turn,
                "expires_turn": expires_turn,
                "sanctuary_expired": sanctuary_expired,
            },
        },
    }


def run_tests(server_url: str, autonomous: bool = False) -> tuple[list, list]:
    """Run sanctuary lifecycle test."""
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

    # Run lifecycle test
    result = test_sanctuary_lifecycle(client, user_id, request_responses, autonomous=autonomous)
    results.append(result)

    return results, request_responses


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-name", default=WORK_NAME)
    parser.add_argument("--server", help="Optional: use existing server URL")
    parser.add_argument(
        "--autonomous",
        action="store_true",
        help="Use autonomous activation (neutral action, no completion keywords)",
    )
    args = parser.parse_args()

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

        mode = "autonomous" if args.autonomous else "prompted"
        print(f"🧪 Running sanctuary lifecycle test ({mode} activation mode)...")

        results, request_responses = run_tests(server_url, autonomous=args.autonomous)

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
            if result.get("passed"):
                phases = result.get("phases", {})
                print(f"   {status} {name}")
                print(f"      Activation: ✅ (turn {phases.get('activation', {}).get('activated_turn')} → {phases.get('activation', {}).get('expires_turn')})")
                print(f"      Protection: ✅ (no lethal events)")
                print(f"      Expiration: ✅ (expired at turn {phases.get('expiration', {}).get('final_turn')})")
            else:
                phase = result.get("phase", "unknown")
                errors = result.get("errors", [])
                print(f"   {status} {name} (failed at {phase} phase)")
                for error in errors:
                    print(f"      - {error}")

    finally:
        if local_server:
            print("🛑 Stopping local server...")
            local_server.stop()


if __name__ == "__main__":
    main()
