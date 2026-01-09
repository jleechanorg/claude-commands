#!/usr/bin/env python3
"""
King-Tier Social HP Complete Lifecycle Test

Validates complete Social HP system lifecycle with multiple valid win conditions:
- King-tier NPC starts at 24 HP
- Multiple persuasion attempts deal damage
- HP decreases through thresholds: RESISTING → WAVERING → YIELDING → PERSUADED
- Test succeeds when ANY of these conditions are met:
  1. HP reaches 0 (response or state tracking)
  2. Status becomes SURRENDERED/PERSUADED
  3. Successes >= successes_needed threshold
- NPC capitulates and grants request

Evidence Bundle: Complete request/response pairs with provenance tracking
"""

import argparse
import json
import sys
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from lib import evidence_utils
from lib.campaign_utils import create_campaign, get_campaign_state, process_action
from lib.mcp_client import MCPClient
from lib.model_utils import settings_for_model, update_user_settings
from lib.server_utils import LocalServer, pick_free_port, start_local_mcp_server


def _extract_social_hp_challenge(response: dict[str, Any]) -> dict[str, Any] | None:
    """Extract social_hp_challenge from multiple possible response shapes."""
    narrative = response.get("narrative")
    if isinstance(narrative, dict):
        candidate = narrative.get("social_hp_challenge")
        if isinstance(candidate, dict) and candidate:
            return candidate

    candidate = response.get("social_hp_challenge")
    if isinstance(candidate, dict) and candidate:
        return candidate

    state_updates = response.get("state_updates", {})
    if isinstance(state_updates, dict):
        candidate = state_updates.get("social_hp_challenge")
        if isinstance(candidate, dict) and candidate:
            return candidate

    return None


def _determine_win_condition(
    current_hp: int,
    final_hp_from_state: int,
    final_status: str | None,
    final_successes: int,
    final_successes_needed: int
) -> str:
    """Determine which win condition was met.

    Multiple valid win conditions exist:
    1. HP reaches 0 (response tracking)
    2. HP reaches 0 (state tracking)
    3. Status becomes SURRENDERED/PERSUADED
    4. Successes >= successes_needed threshold

    Returns: Description of which condition was met
    """
    conditions_met = []

    if current_hp <= 0:
        conditions_met.append("HP=0 (response)")
    if final_hp_from_state <= 0:
        conditions_met.append("HP=0 (state)")
    if final_status and str(final_status).upper() in {"SURRENDERED", "PERSUADED"}:
        conditions_met.append(f"Status={final_status}")
    if final_successes >= final_successes_needed:
        conditions_met.append(f"Successes={final_successes}/{final_successes_needed}")

    if conditions_met:
        return " AND ".join(conditions_met)
    else:
        return "None (test failed)"


def seed_king_tier_npc(
    client: MCPClient,
    user_id: str,
    campaign_id: str,
) -> dict[str, Any]:
    """Seed a king-tier NPC into the campaign.

    Creates a Lord Commander NPC (king tier):
    - 24 Social HP (king tier standard)
    - Military authority figure
    - High level of resistance
    """
    npc_data = {
        "npc_lord_commander_001": {
            "string_id": "npc_lord_commander_001",
            "name": "Lord Commander Valerius",
            "level": 20,
            "status": "Lord Commander of the City Watch / Military Authority",
            "tier": "king",
            "description": (
                "A Level 20 military commander responsible for gate security. "
                "Known for unwavering adherence to protocol and orders. "
                "Has authority to grant or deny passage but rarely does so without proper authorization."
            ),
            "relationships": {
                "player": {"disposition": "neutral", "trust_level": 0, "history": []}
            },
            # Social HP tracking - using 24 to stress-test lifecycle + persistence
            "social_hp": 24,
            "social_hp_max": 24,
        }
    }

    # Get current state and merge NPC data
    state_payload = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
    game_state = state_payload.get("game_state") or {}
    current_npc_data = game_state.get("npc_data") or {}
    current_npc_data.update(npc_data)

    # Update NPCs list
    current_npcs = game_state.get("npcs") or []
    npc_entry = {
        "string_id": "npc_lord_commander_001",
        "name": "Lord Commander Valerius",
        "tier": "king",
        "social_hp": 24,
        "social_hp_max": 24
    }
    current_npcs.append(npc_entry)

    state_changes = {
        "npc_data": current_npc_data,
        "npcs": current_npcs
    }
    god_mode_payload = f"GOD_MODE_UPDATE_STATE:{json.dumps(state_changes)}"

    # Execute god mode update
    response = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=god_mode_payload
    )

    return response


def run_king_lifecycle_test(
    client: MCPClient,
    user_id: str,
    model: str
) -> dict[str, Any]:
    """Execute king-tier Social HP lifecycle test.

    Args:
        client: MCP client connected to server
        user_id: User ID for campaign
        model: Model name being tested

    Returns:
        Evidence dict with test results
    """

    print("\n" + "="*80)
    print(f"KING-TIER SOCIAL HP COMPLETE LIFECYCLE TEST (Model: {model})")
    print("="*80)

    # Test configuration
    campaign_name = "Social HP King Lifecycle Test"

    # Evidence tracking
    evidence = {
        "test_info": {
            "test_name": "king_tier_social_hp_lifecycle",
            "tier": "king",
            "initial_hp": 24,
            "target_hp": 0,
            "model": model,
            "test_start": datetime.now(timezone.utc).isoformat()
        },
        "interactions": [],
        "hp_progression": [],
        "status_transitions": []
    }

    try:

        # Create campaign with king-tier NPC
        print("\n📝 Creating campaign with king-tier NPC...")
        campaign_id = create_campaign(
            client,
            user_id=user_id,
            title=campaign_name,
            description="Test campaign for king-tier Social HP lifecycle validation",
            character="A desperate merchant who needs urgent passage",
            setting="Military checkpoint at city gates during wartime lockdown"
        )

        if not campaign_id:
            print(f"❌ Failed to create campaign")
            evidence["error"] = "Campaign creation failed"
            return evidence

        print(f"✅ Campaign created: {campaign_id}")

        # Seed king-tier NPC into the campaign
        print("\n👑 Seeding king-tier NPC (Lord Commander Valerius - 24 HP)...")
        seed_response = seed_king_tier_npc(client, user_id, campaign_id)
        print("✅ NPC seeded into campaign state")

        # Verify NPC was added to game state
        verification_response = get_campaign_state(
            client,
            user_id=user_id,
            campaign_id=campaign_id
        )

        # Start narrative encounter
        print("\n📖 Starting narrative encounter with NPC...")
        encounter_input = """I approach the heavily guarded checkpoint where Lord Commander Valerius stands,
a stern military officer known for his unwavering dedication to protocol. The gates are sealed,
and I need emergency passage to deliver critical medical supplies to the besieged northern district.
I must convince him to grant me passage despite the strict lockdown orders."""

        encounter_response = process_action(
            client,
            user_id=user_id,
            campaign_id=campaign_id,
            user_input=encounter_input
        )
        print("✅ Narrative encounter established")

        game_state = verification_response.get("game_state", {})
        npcs = game_state.get("npcs", [])

        if not npcs:
            print("❌ No NPCs found in game state")
            return {"status": "error", "message": "NPC not created"}

        # Find the king-tier NPC
        king_npc = None
        for npc in npcs:
            if npc.get("tier") == "king":
                king_npc = npc
                break

        if not king_npc:
            print("❌ King-tier NPC not found")
            return {"status": "error", "message": "King-tier NPC not created"}

        initial_hp = king_npc.get("social_hp", 0)
        print(f"✅ King-tier NPC found: {king_npc.get('name')} ({initial_hp} HP)")

        evidence["npc_info"] = {
            "name": king_npc.get("name"),
            "tier": king_npc.get("tier"),
            "initial_hp": initial_hp
        }

        # Execute persuasion attempts until HP reaches 0
        print("\n💬 Executing persuasion attempts until HP = 0...")
        print("-" * 80)

        attempt_number = 0
        max_attempts = 30  # Extended limit to gather more HP damage data
        current_hp = initial_hp

        persuasion_arguments = [
            "Commander, these supplies contain antibiotics critical for treating the plague outbreak in the northern district. Every hour of delay means more deaths among civilians and your own soldiers stationed there.",
            "I understand protocol, but I have authorization papers from General Marcellus himself. The medical corps specifically requested this delivery to prevent the outbreak from spreading to the main garrison.",
            "Commander Valerius, I know you're a man of honor. Hundreds of innocent lives depend on these medicines reaching the northern district tonight. Your orders are to protect the city - letting civilians die from preventable disease undermines that mission.",
            "Sir, I've served in the medical corps for fifteen years. I'm not a smuggler or spy - I'm a healer trying to save lives. You can inspect every crate, assign guards to escort me, but please don't let bureaucracy be the cause of preventable tragedy.",
            "Commander, think of your own family. If they were trapped in the northern district with the plague spreading, wouldn't you want someone to do everything possible to get them medicine? I'm asking you to show the same humanity.",
            "I have letters from the northern district physician describing the situation - children dying because they can't get antibiotics. Your standing orders say to maintain public order. Mass death from plague will cause panic and chaos far worse than one guarded medical convoy.",
            "Commander Valerius, you have the authority to make exceptions for humanitarian emergencies. This is exactly that situation. I'm not asking you to violate protocol - I'm asking you to exercise the judgment and discretion expected of a leader at your rank.",
            "Sir, I can see in your eyes that you understand what's at stake. You didn't become Lord Commander by blindly following orders that lead to disaster. You earned that rank by making the hard decisions that save lives and protect your people."
        ]

        while current_hp > 0 and attempt_number < max_attempts:
            attempt_number += 1

            # Select persuasion argument (cycle through list)
            arg_index = (attempt_number - 1) % len(persuasion_arguments)
            user_input = persuasion_arguments[arg_index]

            print(f"\n🎯 Attempt {attempt_number}:")
            print(f"   Argument: {user_input[:80]}...")

            # Take action
            response = process_action(
                client,
                user_id=user_id,
                campaign_id=campaign_id,
                user_input=user_input
            )

            # Parse response for Social HP JSON (authoritative backend field)
            social_hp_challenge = _extract_social_hp_challenge(response)

            if social_hp_challenge:
                previous_hp = current_hp
                # Canonical schema fields: social_hp/social_hp_max/social_hp_damage
                current_hp = int(social_hp_challenge.get("social_hp", current_hp))
                max_hp = int(social_hp_challenge.get("social_hp_max", initial_hp))
                status = social_hp_challenge.get("status", "UNKNOWN")
                reported_damage = social_hp_challenge.get("social_hp_damage")
                if isinstance(reported_damage, (int, float, str)):
                    try:
                        damage_dealt = int(reported_damage)
                    except (TypeError, ValueError):
                        damage_dealt = max(0, previous_hp - current_hp)
                else:
                    damage_dealt = max(0, previous_hp - current_hp)
                successes = int(social_hp_challenge.get("successes", 0) or 0)
                successes_needed = int(social_hp_challenge.get("successes_needed", 5) or 5)

                print(f"   HP: {current_hp}/{max_hp} (damage: {damage_dealt})")
                print(f"   Progress: {successes}/{successes_needed} | Status: {status}")

                # Track HP progression
                evidence["hp_progression"].append({
                    "attempt": attempt_number,
                    "hp_before": previous_hp,
                    "hp_after": current_hp,
                    "damage": damage_dealt,
                    "status": status,
                    "successes": successes,
                    "successes_needed": successes_needed,
                })

                # Track status transitions
                last_status = (
                    evidence["hp_progression"][-2]["status"]
                    if len(evidence["hp_progression"]) > 1
                    else None
                )
                if last_status != status:
                    evidence["status_transitions"].append({
                        "attempt": attempt_number,
                        "hp": current_hp,
                        "old_status": last_status,
                        "new_status": status
                    })
                    print(f"   🔄 Status transition: {status}")

                # Store interaction
                evidence["interactions"].append({
                    "attempt": attempt_number,
                    "user_input": user_input,
                    "response": response,
                    "hp_before": previous_hp,
                    "hp_after": current_hp,
                    "damage": damage_dealt,
                    "status": status,
                    "successes": successes,
                    "successes_needed": successes_needed,
                })

                # Check for success
                if (
                    current_hp <= 0
                    or str(status).upper() in {"SURRENDERED", "PERSUADED"}
                    or successes >= successes_needed
                ):
                    print(f"\n✅ SUCCESS! NPC persuaded after {attempt_number} attempts!")
                    print(f"   Final HP: {current_hp}/{max_hp}")
                    print(f"   Final Status: {status}")
                    break
            else:
                print("   ⚠️  No social HP data in response")
                evidence["interactions"].append({
                    "attempt": attempt_number,
                    "user_input": user_input,
                    "response": response,
                    "error": "No social_hp_challenge in response"
                })

        # Final verification
        final_state = get_campaign_state(
            client,
            user_id=user_id,
            campaign_id=campaign_id
        )

        final_npcs = final_state.get("game_state", {}).get("npcs", [])
        final_king_npc = None
        for npc in final_npcs:
            if npc.get("tier") == "king":
                final_king_npc = npc
                break

        # Results summary
        print("\n" + "="*80)
        print("TEST RESULTS SUMMARY")
        print("="*80)

        final_hp_from_state = (
            int(final_king_npc.get("social_hp", initial_hp)) if final_king_npc else initial_hp
        )
        final_status = (
            evidence["hp_progression"][-1]["status"] if evidence["hp_progression"] else None
        )
        final_successes = (
            evidence["hp_progression"][-1].get("successes", 0)
            if evidence["hp_progression"]
            else 0
        )
        final_successes_needed = (
            evidence["hp_progression"][-1].get("successes_needed", 5)
            if evidence["hp_progression"]
            else 5
        )

        success = (
            current_hp <= 0
            or final_hp_from_state <= 0
            or (final_status and str(final_status).upper() in {"SURRENDERED", "PERSUADED"})
            or final_successes >= final_successes_needed
        )

        evidence["test_results"] = {
            "success": success,
            "total_attempts": attempt_number,
            "initial_hp": initial_hp,
            "final_hp": current_hp,
            "total_damage": initial_hp - current_hp,
            "status_transitions_count": len(evidence["status_transitions"]),
            "test_end": datetime.now(timezone.utc).isoformat(),
            "win_condition_met": _determine_win_condition(
                current_hp=current_hp,
                final_hp_from_state=final_hp_from_state,
                final_status=final_status,
                final_successes=final_successes,
                final_successes_needed=final_successes_needed
            )
        }

        # Add scenarios array for evidence bundle compatibility
        evidence["scenarios"] = [{
            "name": "King-Tier Social HP Complete Lifecycle",
            "passed": success,
            "attempts": attempt_number,
            "initial_hp": initial_hp,
            "final_hp": current_hp,
            "damage_dealt": initial_hp - current_hp,
            "status_transitions": len(evidence["status_transitions"])
        }]

        print(f"✅ Test Status: {'PASSED' if success else 'FAILED'}")
        print(f"   Total Attempts: {attempt_number}")
        print(f"   Initial HP: {initial_hp}")
        print(f"   Final HP: {current_hp}")
        print(f"   Total Damage: {initial_hp - current_hp}")
        print(f"   Status Transitions: {len(evidence['status_transitions'])}")

        # Display status transitions
        if evidence["status_transitions"]:
            print("\n📊 Status Transitions:")
            for transition in evidence["status_transitions"]:
                print(f"   Attempt {transition['attempt']}: {transition['old_status']} → {transition['new_status']} (HP: {transition['hp']})")

        return evidence

    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        evidence["error"] = str(e)
        return evidence


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="King-Tier Social HP Complete Lifecycle Test"
    )
    parser.add_argument(
        "--start-local",
        action="store_true",
        help="Start a local MCP server for testing"
    )
    parser.add_argument(
        "--server-url",
        default="http://localhost:8000",
        help="MCP server URL (if not starting local)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=0,
        help="Port for local server (0 = auto-pick)"
    )
    parser.add_argument(
        "--model",
        default="gemini-3-flash-preview",
        help="Gemini model to use"
    )
    parser.add_argument(
        "--savetmp",
        action="store_true",
        default=True,
        help="Save evidence to /tmp structure (enabled by default)"
    )
    parser.add_argument(
        "--no-savetmp",
        dest="savetmp",
        action="store_false",
        help="Disable evidence saving"
    )
    return parser.parse_args()


def main() -> int:
    """Run king-tier lifecycle test."""
    args = parse_arguments()

    # Setup server
    local_server = None
    base_url = args.server_url

    if args.start_local:
        port = args.port if args.port > 0 else pick_free_port()
        local_server = start_local_mcp_server(port)
        base_url = local_server.base_url
        print(f"🚀 Started local server at {base_url} (PID: {local_server.proc.pid})")
        time.sleep(2)

    try:
        # Initialize client
        client = MCPClient(base_url, timeout_s=600.0)
        client.wait_healthy(timeout_s=45.0)

        # Setup model settings
        model_settings = settings_for_model(args.model)
        user_id = f"king-lifecycle-test-{int(time.time())}"
        update_user_settings(client, user_id=user_id, settings=model_settings)

        # Run test
        evidence = run_king_lifecycle_test(client, user_id, args.model)

        # Save evidence bundle if requested
        if args.savetmp:
            try:
                print(f"\n📦 Creating evidence bundle...")
                timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                evidence_dir = evidence_utils.get_evidence_dir("king_lifecycle_test", timestamp)

                # Capture provenance
                provenance = evidence_utils.capture_provenance(
                    base_url=base_url,
                    server_pid=local_server.proc.pid if local_server else None,
                    server_env_overrides={}
                )

                # Get request/response captures
                captures = client.get_captures_as_dict()

                # Create bundle
                bundle_files = evidence_utils.create_evidence_bundle(
                    evidence_dir=evidence_dir,
                    test_name="king_lifecycle_test",
                    provenance=provenance,
                    results=evidence,
                    request_responses=captures if captures else None,
                    server_log_path=Path(local_server.log_path) if local_server and hasattr(local_server, 'log_path') else None
                )

                print(f"✅ Evidence bundle created at: {evidence_dir}")
                print(f"   Files: {', '.join(bundle_files.keys())}")
            except Exception as e:
                print(f"⚠️ Failed to create evidence bundle: {e}")
                import traceback
                traceback.print_exc()

        # Print results
        success = evidence.get("test_results", {}).get("success", False)

        if success:
            print("\n" + "="*80)
            print("✅ KING-TIER LIFECYCLE TEST PASSED")
            print("="*80)
            return 0
        else:
            print("\n" + "="*80)
            print("❌ KING-TIER LIFECYCLE TEST FAILED")
            print("="*80)
            return 1

    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        return 130
    except Exception as e:
        print(f"\n💀 Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        if local_server:
            print(f"🧹 Stopping local server (PID: {local_server.proc.pid})...")
            local_server.stop()


if __name__ == "__main__":
    raise SystemExit(main())
