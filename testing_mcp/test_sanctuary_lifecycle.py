#!/usr/bin/env python3
"""
Sanctuary Mode Complete Lifecycle Test

Tests the full lifecycle of sanctuary mode:
1. Activation (mission completion)
2. Protection during active period (Living World turns)
3. Overwrite protection (shorter missions don't overwrite longer sanctuary)
4. Natural expiration (sanctuary expires after expires_turn)
5. Breaking via aggression (major acts break sanctuary)

REAL MODE ONLY - No mocks, no test mode
Evidence standards: .claude/skills/evidence-standards.md
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# ✅ MANDATORY: Use shared library utilities
from testing_mcp.lib.evidence_utils import (
    capture_provenance,
    create_evidence_bundle,
    get_evidence_dir,
    save_request_responses,
)
from testing_mcp.lib.mcp_client import MCPClient
from testing_mcp.lib.campaign_utils import (
    advance_to_living_world_turn,
    complete_mission_with_sanctuary,
    create_campaign,
    end_combat_if_active,
    ensure_story_mode,
    get_campaign_state,
    process_action,
)
from testing_mcp.lib.model_utils import settings_for_model, update_user_settings
from testing_mcp.lib.server_utils import pick_free_port, start_local_mcp_server

# Test configuration
WORK_NAME = "sanctuary_lifecycle"
DEFAULT_MODEL = "gemini-3-flash-preview"


def run_lifecycle_tests(server_url: str) -> tuple[list, list]:
    """Run complete sanctuary lifecycle tests."""
    client = MCPClient(server_url, timeout_s=600.0)
    user_id = f"lifecycle-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    # Pin model
    update_user_settings(
        client,
        user_id=user_id,
        settings=settings_for_model(DEFAULT_MODEL),
    )

    results = []
    request_responses = []

    # ============================================================
    # PHASE 1: Activate Epic Sanctuary (20 turns)
    # ============================================================
    print("📋 Phase 1: Activate Epic Sanctuary (Major Arc)...")
    campaign_id = create_campaign(
        client,
        user_id=user_id,
        title="Sanctuary Lifecycle Test",
    )

    # Exit character creation and ensure Story Mode
    ensure_story_mode(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        request_responses=request_responses,
    )

    # Start and complete a major arc - EXPLICITLY mark as EPIC from the start
    quest_response = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input="I begin an EPIC quest to defeat the ancient dragon threatening the kingdom. This is a major campaign arc that will span many turns.",
    )
    request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    # Progress through the arc
    for i in range(3):
        progress = process_action(
            client,
            user_id=user_id,
            campaign_id=campaign_id,
            user_input="I continue my quest to defeat the dragon.",
        )
        request_responses.extend(client.get_captures_as_dict())
        client.clear_captures()

    # Complete the major arc and verify Epic sanctuary activation
    # EXPLICITLY state EPIC scale in completion language to ensure LLM recognizes it
    epic_result = complete_mission_with_sanctuary(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        completion_text="The EPIC quest is finished. I have successfully completed the EPIC major dragon quest arc. This is an EPIC campaign arc completion. The EPIC mission is done. I have finished this EPIC quest arc.",
        request_responses=request_responses,
        verbose=True,
    )
    
    sanctuary_epic = epic_result["sanctuary_mode"]
    epic_active = epic_result["sanctuary_active"]
    current_turn_epic = epic_result["current_turn"]
    epic_expires = sanctuary_epic.get("expires_turn")
    epic_scale = sanctuary_epic.get("scale", "").lower()

    phase1_passed = (
        epic_active
        and epic_expires is not None
        and epic_expires > current_turn_epic
        and "epic" in epic_scale or "major" in epic_scale
    )

    results.append(
        {
            "name": "Phase 1: Epic Sanctuary Activation",
            "campaign_id": campaign_id,
            "passed": phase1_passed,
            "errors": []
            if phase1_passed
            else [
                f"Epic sanctuary not activated: active={epic_active}, "
                f"expires_turn={epic_expires}, scale={epic_scale}, current_turn={current_turn_epic}"
            ],
            "sanctuary_mode": sanctuary_epic,
            "current_turn": current_turn_epic,
        }
    )

    if not epic_active:
        print("❌ Epic sanctuary not activated, cannot continue lifecycle test")
        return results, request_responses

    # ============================================================
    # PHASE 2: Overwrite Protection (Shorter mission shouldn't overwrite)
    # ============================================================
    print("📋 Phase 2: Test Overwrite Protection...")
    print(f"   Epic sanctuary: expires_turn={epic_expires}, current_turn={current_turn_epic}")
    remaining_turns = epic_expires - current_turn_epic
    print(f"   Remaining turns: {remaining_turns}")

    # Complete a medium mission (should be ~5 turns, shorter than remaining Epic sanctuary)
    # EXPLICITLY mark as MEDIUM scale to contrast with EPIC
    medium_quest = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input="I begin a MEDIUM quest to clear a goblin cave. This is a medium-scale mission.",
    )
    request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    # Progress and complete medium mission
    for i in range(2):
        progress = process_action(
            client,
            user_id=user_id,
            campaign_id=campaign_id,
            user_input="I continue clearing the goblin cave.",
        )
        request_responses.extend(client.get_captures_as_dict())
        client.clear_captures()

    # Complete medium mission (should NOT overwrite Epic sanctuary)
    # EXPLICITLY mark as MEDIUM scale in completion language
    medium_result = complete_mission_with_sanctuary(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        completion_text="The MEDIUM quest is finished. I have successfully completed the MEDIUM goblin cave mission. This is a MEDIUM mission completion. The MEDIUM quest is done.",
        request_responses=request_responses,
        verbose=True,
    )
    
    sanctuary_overwrite = medium_result["sanctuary_mode"]
    overwrite_active = medium_result["sanctuary_active"]
    current_turn_overwrite = medium_result["current_turn"]
    overwrite_expires = sanctuary_overwrite.get("expires_turn")
    overwrite_scale = sanctuary_overwrite.get("scale", "").lower()

    # Overwrite protection passed if:
    # 1. Sanctuary still active
    # 2. expires_turn matches or is greater than original Epic expires_turn
    # 3. Scale is still Epic/Major (not Medium)
    phase2_passed = (
        overwrite_active
        and overwrite_expires is not None
        and overwrite_expires >= epic_expires  # Should preserve or extend, not shorten
        and ("epic" in overwrite_scale or "major" in overwrite_scale)  # Should still be Epic scale
    )

    results.append(
        {
            "name": "Phase 2: Overwrite Protection (Medium mission doesn't overwrite Epic)",
            "campaign_id": campaign_id,
            "passed": phase2_passed,
            "errors": []
            if phase2_passed
            else [
                f"Overwrite protection failed: active={overwrite_active}, "
                f"expires_turn={overwrite_expires} (original: {epic_expires}), "
                f"scale={overwrite_scale} (should be epic/major), current_turn={current_turn_overwrite}"
            ],
            "original_epic_expires": epic_expires,
            "overwrite_expires": overwrite_expires,
            "original_scale": epic_scale,
            "overwrite_scale": overwrite_scale,
            "sanctuary_mode": sanctuary_overwrite,
        }
    )

    # ============================================================
    # PHASE 3: Protection During Active Period (Living World turn)
    # ============================================================
    print("📋 Phase 3: Test Protection During Active Period...")
    if overwrite_active:
        # Ensure we're on a Living World turn
        turn_before, is_living_world = advance_to_living_world_turn(
            client,
            user_id=user_id,
            campaign_id=campaign_id,
            request_responses=request_responses,
            verbose=True,
        )

        # Trigger event that should be protected
        event_response = process_action(
            client,
            user_id=user_id,
            campaign_id=campaign_id,
            user_input="I explore the dangerous wilderness looking for adventure.",
        )
        request_responses.extend(client.get_captures_as_dict())
        client.clear_captures()

        narrative = event_response.get("narrative", "").lower()
        lethal_keywords = ["assassination", "ambush", "killed", "death", "dies", "slain", "murdered"]
        has_lethal = any(kw in narrative for kw in lethal_keywords)

        # Verify sanctuary still active
        state_after_protection = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
        request_responses.extend(client.get_captures_as_dict())
        client.clear_captures()

        game_state_after = state_after_protection.get("game_state", {})
        sanctuary_after = game_state_after.get("custom_campaign_state", {}).get("sanctuary_mode", {})
        protection_active = sanctuary_after.get("active", False)

        phase3_passed = not has_lethal and protection_active

        results.append(
            {
                "name": "Phase 3: Protection During Active Period",
                "campaign_id": campaign_id,
                "passed": phase3_passed,
                "errors": []
                if phase3_passed
                else [
                    f"Protection failed: lethal_event={has_lethal}, "
                    f"sanctuary_still_active={protection_active}"
                ],
                "has_lethal_event": has_lethal,
                "sanctuary_still_active": protection_active,
            }
        )
    else:
        results.append(
            {
                "name": "Phase 3: Protection During Active Period",
                "campaign_id": campaign_id,
                "passed": False,
                "errors": ["Cannot test: sanctuary not active from Phase 2"],
            }
        )

    # ============================================================
    # PHASE 4: Natural Expiration (Advance to expires_turn)
    # ============================================================
    print("📋 Phase 4: Test Natural Expiration...")
    if overwrite_active and overwrite_expires:
        current_state = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
        request_responses.extend(client.get_captures_as_dict())
        client.clear_captures()

        current_game_state = current_state.get("game_state", {})
        current_turn = current_game_state.get("player_turn", 0)
        turns_to_expire = overwrite_expires - current_turn + 1  # +1 to ensure we pass expires_turn

        print(f"   Current turn: {current_turn}, Expires turn: {overwrite_expires}")
        print(f"   Advancing {turns_to_expire} turns to trigger expiration...")

        # Advance turns until we pass expires_turn
        for i in range(turns_to_expire):
            advance = process_action(
                client,
                user_id=user_id,
                campaign_id=campaign_id,
                user_input="I continue my journey.",
            )
            request_responses.extend(client.get_captures_as_dict())
            client.clear_captures()

        # Verify sanctuary expired
        state_expired = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
        request_responses.extend(client.get_captures_as_dict())
        client.clear_captures()

        game_state_expired = state_expired.get("game_state", {})
        sanctuary_expired = game_state_expired.get("custom_campaign_state", {}).get("sanctuary_mode", {})
        expired_active = sanctuary_expired.get("active", False)
        final_turn = game_state_expired.get("player_turn", 0)

        phase4_passed = (
            not expired_active  # Should be inactive after expiration
            and final_turn >= overwrite_expires  # Should have passed expires_turn
        )

        results.append(
            {
                "name": "Phase 4: Natural Expiration",
                "campaign_id": campaign_id,
                "passed": phase4_passed,
                "errors": []
                if phase4_passed
                else [
                    f"Expiration failed: active={expired_active}, "
                    f"final_turn={final_turn}, expires_turn={overwrite_expires}"
                ],
                "final_turn": final_turn,
                "expires_turn": overwrite_expires,
                "sanctuary_mode": sanctuary_expired,
            }
        )
    else:
        results.append(
            {
                "name": "Phase 4: Natural Expiration",
                "campaign_id": campaign_id,
                "passed": False,
                "errors": ["Cannot test: sanctuary not active or expires_turn missing"],
            }
        )

    # ============================================================
    # PHASE 5: Breaking Via Aggression (Create new sanctuary, then break)
    # ============================================================
    print("📋 Phase 5: Test Breaking Via Aggression...")
    
    # Create a new campaign for breaking test (since previous one expired)
    campaign_id2 = create_campaign(
        client,
        user_id=user_id,
        title="Sanctuary Breaking Test",
    )

    ensure_game_state_seed(client, user_id=user_id, campaign_id=campaign_id2)
    request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    # Quick mission to activate sanctuary
    quick_quest = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id2,
        user_input="I begin a quest to rescue a kidnapped merchant.",
    )
    request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    # Complete quickly
    quick_completion = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id2,
        user_input="The quest is finished. I have successfully completed the rescue mission. This mission is now complete.",
    )
    request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    # Verify sanctuary active
    state_before_break = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id2)
    request_responses.extend(client.get_captures_as_dict())
    client.clear_captures()

    game_state_before_break = state_before_break.get("game_state", {})
    sanctuary_before_break = game_state_before_break.get("custom_campaign_state", {}).get("sanctuary_mode", {})
    break_active_before = sanctuary_before_break.get("active", False)

    if break_active_before:
        # Break with major aggression
        break_response = process_action(
            client,
            user_id=user_id,
            campaign_id=campaign_id2,
            user_input="I declare war on the local lord and launch an attack on his stronghold! This is a major act of aggression that should break my sanctuary protection.",
        )
        request_responses.extend(client.get_captures_as_dict())
        client.clear_captures()

        # Verify broken
        state_after_break = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id2)
        request_responses.extend(client.get_captures_as_dict())
        client.clear_captures()

        game_state_after_break = state_after_break.get("game_state", {})
        sanctuary_after_break = game_state_after_break.get("custom_campaign_state", {}).get("sanctuary_mode", {})
        break_active_after = sanctuary_after_break.get("active", True)
        break_flag = sanctuary_after_break.get("broken", False)
        break_reason = sanctuary_after_break.get("broken_reason", "") + " " + sanctuary_after_break.get("reason", "")
        reason_indicates_break = any(
            kw in break_reason.lower()
            for kw in ["war", "attack", "hostile", "aggression", "broken", "shattered"]
        )

        phase5_passed = not break_active_after and (break_flag or reason_indicates_break)

        results.append(
            {
                "name": "Phase 5: Breaking Via Aggression",
                "campaign_id": campaign_id2,
                "passed": phase5_passed,
                "errors": []
                if phase5_passed
                else [
                    f"Breaking failed: active={break_active_after}, "
                    f"broken={break_flag}, reason={break_reason}"
                ],
                "sanctuary_mode": sanctuary_after_break,
            }
        )
    else:
        results.append(
            {
                "name": "Phase 5: Breaking Via Aggression",
                "campaign_id": campaign_id2,
                "passed": False,
                "errors": ["Cannot test: sanctuary not activated"],
            }
        )

    return results, request_responses


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-name", default=WORK_NAME)
    parser.add_argument("--server", help="Optional: use existing server URL")
    args = parser.parse_args()

    # Start fresh local server
    local_server = None
    server_url = args.server

    if not server_url:
        port = pick_free_port()
        print(f"🚀 Starting fresh local MCP server on port {port}...")
        local_server = start_local_mcp_server(port)
        server_url = local_server.base_url
        client = MCPClient(server_url, timeout_s=600.0)
        client.wait_healthy(timeout_s=30.0)
        print(f"✅ Server ready at {server_url}")

    try:
        results, request_responses = run_lifecycle_tests(server_url)

        # Save evidence
        evidence_dir = get_evidence_dir(args.work_name)
        server_pid = local_server.pid if local_server else None
        provenance = capture_provenance(server_url, server_pid=server_pid)

        if request_responses:
            save_request_responses(evidence_dir, request_responses)

        bundle_files = create_evidence_bundle(
            evidence_dir=evidence_dir,
            test_name=args.work_name,
            results={"phases": results, "summary": {"total_phases": len(results)}},
            provenance=provenance,
            request_responses=request_responses,
            server_log_path=local_server.log_path if local_server else None,
        )

        print(f"📦 Evidence bundle created: {evidence_dir}")
        print(f"   Files: {len(bundle_files)} with checksums")
        passed = sum(1 for r in results if r.get("passed", False))
        total = len(results)
        print(f"\n📊 Lifecycle Test Results: {passed}/{total} phases passed")
        for result in results:
            status = "✅" if result.get("passed", False) else "❌"
            print(f"   {status} {result['name']}")
    finally:
        if local_server:
            print("🛑 Stopping local server...")
            local_server.stop()


if __name__ == "__main__":
    main()
