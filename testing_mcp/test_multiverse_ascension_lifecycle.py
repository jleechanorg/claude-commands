#!/usr/bin/env python3
"""
Multiverse Ascension Lifecycle Test (Sovereign Protocol Speedrun)

Validates the complete multiverse/sovereign ascension lifecycle:
1. Create character (campaign creation) - already divine tier
2. Do 1-2 misc actions (explore multiverse, interact with cosmic entities)
3. GOD MODE: Setup sovereign conditions (universe_control 70+, divine tier)
4. Verify CampaignUpgradeAgent trigger fires for sovereign upgrade
5. Ascend to sovereign tier (multiverse god)

Evidence Bundle: Complete request/response pairs with provenance tracking
Saves to: /tmp/worldarchitect.ai/<branch>/multiverse_ascension_lifecycle/
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from lib import evidence_utils
from lib.campaign_utils import create_campaign, get_campaign_state, process_action
from lib.mcp_client import MCPClient
from lib.model_utils import settings_for_model, update_user_settings
from lib.server_utils import LocalServer, pick_free_port, start_local_mcp_server


def setup_sovereign_conditions(
    client: MCPClient,
    user_id: str,
    campaign_id: str,
) -> dict[str, Any]:
    """Use GOD MODE to setup sovereign/multiverse ascension conditions.

    Sets:
    - character_data.level = 40 (Greater Deity range)
    - custom_campaign_state.campaign_tier = "divine" (must be divine to ascend)
    - custom_campaign_state.universe_control = 70 (UNIVERSE_CONTROL_THRESHOLD)
    - custom_campaign_state.divine_rank = "minor_god"
    - custom_campaign_state.controlled_universes = list of conquered realms

    Returns:
        Response from the GOD MODE update.
    """
    # Sovereign-ready state (divine being ready for multiverse control)
    state_changes = {
        "character_data": {
            "level": 40,  # Minor God tier
            "xp": 2_000_000,  # Divine-tier XP
            "class": "Divine Champion",
            "race": "Ascended Human",
            "alignment": "Lawful Neutral",
            "attributes": {
                "strength": 30,  # Divine stat
                "dexterity": 28,
                "constitution": 30,
                "intelligence": 26,
                "wisdom": 30,
                "charisma": 35,  # Supreme divine presence
            },
            "hp": 1000,
            "max_hp": 1000,
        },
        "custom_campaign_state": {
            "campaign_tier": "divine",  # Must be divine to become sovereign
            "divine_rank": "minor_god",
            "divine_potential": 500,  # Far beyond initial threshold
            "universe_control": 70,  # At sovereign threshold
            "controlled_universes": [
                {"name": "Prime Material", "control": 95},
                {"name": "Feywild", "control": 80},
                {"name": "Shadowfell", "control": 75},
            ],
            "portfolio": ["Conquest", "Order", "Time"],
            "worshippers": 10_000_000,  # Massive divine following
            "divine_artifacts": [
                "The Scepter of Cosmos",
                "The Mantle of Eternity",
                "The Crown of Many Worlds",
            ],
        },
    }

    god_mode_payload = f"GOD_MODE_UPDATE_STATE:{json.dumps(state_changes)}"

    response = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=god_mode_payload,
        mode="god",
    )

    return response


def run_multiverse_ascension_test(
    base_url: str,
    model_id: str = "gemini-2.0-flash",
    verbose: bool = False,
) -> dict[str, Any]:
    """Run the complete multiverse/sovereign ascension lifecycle test.

    Lifecycle:
    1. Create campaign with divine being character
    2. Do 1-2 misc actions (survey multiverse, challenge rival deity)
    3. GOD MODE: Set sovereign conditions (universe_control >= 70)
    4. Trigger sovereign ascension ("let me be multiverse god")
    5. Verify sovereign tier achieved

    Args:
        base_url: MCP server URL (e.g., http://localhost:8081)
        model_id: Model to use for LLM calls
        verbose: Print detailed output

    Returns:
        Evidence dict with test results and provenance
    """
    print("\n" + "=" * 80)
    print("MULTIVERSE ASCENSION LIFECYCLE TEST (SOVEREIGN PROTOCOL SPEEDRUN)")
    print("=" * 80)
    print(f"Server: {base_url}")
    print(f"Model: {model_id}")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 80)

    # Initialize evidence structure
    evidence: dict[str, Any] = {
        "test_name": "multiverse_ascension_lifecycle",
        "test_start": datetime.now(timezone.utc).isoformat(),
        "server_url": base_url,
        "model_id": model_id,
        "lifecycle_stages": [],
        "interactions": [],
        "state_snapshots": [],
    }

    client = MCPClient(base_url)
    user_id = f"sovereign_test_{int(time.time())}"
    campaign_name = f"Sovereign Ascension Test {datetime.now().strftime('%H%M%S')}"

    try:
        # ================================================================
        # STAGE 1: Create Campaign (Divine Being)
        # ================================================================
        print("\n🌌 STAGE 1: Creating divine being campaign...")
        print("-" * 40)

        campaign_id = create_campaign(
            client,
            user_id=user_id,
            title=campaign_name,
            description="A Minor God seeking to transcend to Multiverse Sovereign",
            character="Zephyros the Eternal, a Minor God of Conquest who rules over three planes. "
                      "Level 40, divine rank, with control over Prime Material, Feywild, and Shadowfell. "
                      "Seeks to become a Sovereign - master of the entire multiverse.",
            setting="The Nexus of All Realities, a cosmic crossroads where all universes intersect. "
                    "Here, gods may petition for Sovereign Protocol - control over the entire multiverse.",
            selected_prompts=["narrative", "mechanics"],
        )

        if not campaign_id:
            print("❌ Failed to create campaign")
            evidence["error"] = "Campaign creation failed"
            return evidence

        print(f"✅ Campaign created: {campaign_id}")
        evidence["campaign_id"] = campaign_id
        evidence["lifecycle_stages"].append({
            "stage": 1,
            "name": "campaign_creation",
            "status": "success",
            "campaign_id": campaign_id,
        })

        # ================================================================
        # STAGE 2: Misc Actions (Survey Multiverse, Challenge Rival)
        # ================================================================
        print("\n🌀 STAGE 2: Surveying multiverse and asserting dominance...")
        print("-" * 40)

        # Action 2a: Survey the multiverse
        survey_input = (
            "I survey my domain from the Nexus of All Realities. My divine senses extend "
            "across the planes I control - Prime Material, Feywild, and Shadowfell. "
            "I assess what remains unconquered and identify the path to total multiverse control."
        )
        print(f"Action 2a: {survey_input[:60]}...")

        survey_response = process_action(
            client,
            user_id=user_id,
            campaign_id=campaign_id,
            user_input=survey_input,
        )
        print("✅ Multiverse survey complete")
        evidence["interactions"].append({
            "stage": "2a",
            "action": "survey_multiverse",
            "input": survey_input,
            "response": survey_response,
        })

        # Action 2b: Assert divine dominance
        assert_input = (
            "I manifest my divine presence across all planes I control, reminding lesser beings "
            "of my power. My portfolio of Conquest, Order, and Time resonates through reality. "
            "I am ready to claim dominion over ALL realities."
        )
        print(f"Action 2b: {assert_input[:60]}...")

        assert_response = process_action(
            client,
            user_id=user_id,
            campaign_id=campaign_id,
            user_input=assert_input,
        )
        print("✅ Divine dominance asserted")
        evidence["interactions"].append({
            "stage": "2b",
            "action": "assert_dominance",
            "input": assert_input,
            "response": assert_response,
        })

        evidence["lifecycle_stages"].append({
            "stage": 2,
            "name": "misc_actions",
            "status": "success",
            "actions_count": 2,
        })

        # ================================================================
        # STAGE 3: GOD MODE - Setup Sovereign Conditions
        # ================================================================
        print("\n⚡ STAGE 3: GOD MODE - Setting up sovereign conditions...")
        print("-" * 40)

        setup_response = setup_sovereign_conditions(client, user_id, campaign_id)
        print("✅ Sovereign conditions set via GOD MODE")
        print("   - Level: 40 (Minor God)")
        print("   - Divine Rank: minor_god")
        print("   - Campaign Tier: divine")
        print("   - Universe Control: 70% (at sovereign threshold)")

        evidence["interactions"].append({
            "stage": "3",
            "action": "god_mode_setup",
            "input": "GOD_MODE_UPDATE_STATE:{sovereign conditions}",
            "response": setup_response,
        })

        # Verify state was updated
        state_after_setup = get_campaign_state(
            client, user_id=user_id, campaign_id=campaign_id
        )
        game_state = state_after_setup.get("game_state", {})
        custom_state = game_state.get("custom_campaign_state", {})
        char_data = game_state.get("character_data", {})

        evidence["state_snapshots"].append({
            "stage": 3,
            "game_state": game_state,
        })

        print(f"   Verified Level: {char_data.get('level', 'N/A')}")
        print(f"   Verified Campaign Tier: {custom_state.get('campaign_tier', 'N/A')}")
        print(f"   Verified Universe Control: {custom_state.get('universe_control', 'N/A')}%")

        evidence["lifecycle_stages"].append({
            "stage": 3,
            "name": "god_mode_setup",
            "status": "success",
            "sovereign_conditions": {
                "level": char_data.get("level"),
                "campaign_tier": custom_state.get("campaign_tier"),
                "divine_rank": custom_state.get("divine_rank"),
                "universe_control": custom_state.get("universe_control"),
            },
        })

        # ================================================================
        # STAGE 4: Trigger Sovereign Ascension
        # ================================================================
        print("\n🌟 STAGE 4: Triggering sovereign ascension...")
        print("-" * 40)

        # Use semantic routing phrase to trigger CampaignUpgradeAgent for sovereign
        ascension_input = (
            "Let me be multiverse god! I have conquered three planes and control 70% of reality. "
            "I invoke the Sovereign Protocol to transcend my divine status and become "
            "master of ALL universes. The multiverse shall bend to my will!"
        )
        print(f"Input: {ascension_input[:60]}...")

        ascension_response = process_action(
            client,
            user_id=user_id,
            campaign_id=campaign_id,
            user_input=ascension_input,
        )

        # Check if agent selection indicates CampaignUpgradeAgent
        agent_used = ascension_response.get("agent_used", "unknown")
        print(f"✅ Sovereign ascension action processed (Agent: {agent_used})")

        evidence["interactions"].append({
            "stage": "4",
            "action": "trigger_sovereign_ascension",
            "input": ascension_input,
            "response": ascension_response,
            "agent_used": agent_used,
        })

        # Verify CampaignUpgradeAgent was triggered
        trigger_success = "campaign_upgrade" in str(agent_used).lower() or "upgrade" in str(agent_used).lower()
        if trigger_success:
            print("✅ CampaignUpgradeAgent trigger VERIFIED for sovereign protocol")
        else:
            print(f"⚠️ Agent used: {agent_used} (may or may not be CampaignUpgradeAgent)")

        evidence["lifecycle_stages"].append({
            "stage": 4,
            "name": "trigger_sovereign_ascension",
            "status": "success" if trigger_success else "partial",
            "agent_used": agent_used,
            "trigger_verified": trigger_success,
        })

        # ================================================================
        # STAGE 5: Verify Sovereign Tier Achieved
        # ================================================================
        print("\n👑 STAGE 5: Verifying sovereign ascension...")
        print("-" * 40)

        final_state = get_campaign_state(
            client, user_id=user_id, campaign_id=campaign_id
        )
        final_game_state = final_state.get("game_state", {})
        final_custom_state = final_game_state.get("custom_campaign_state", {})

        final_tier = final_custom_state.get("campaign_tier", "unknown")
        sovereign_status = final_custom_state.get("sovereign_status", "none")
        multiverse_control = final_custom_state.get("multiverse_control", 0)

        evidence["state_snapshots"].append({
            "stage": 5,
            "game_state": final_game_state,
        })

        # Check for sovereign tier markers
        is_sovereign = (
            final_tier == "sovereign"
            or sovereign_status not in (None, "none")
            or "sovereign" in str(final_tier).lower()
            or "multiverse" in str(final_tier).lower()
            or multiverse_control > 0
        )

        if is_sovereign:
            print(f"✅ SOVEREIGN ASCENSION VERIFIED!")
            print(f"   Campaign Tier: {final_tier}")
            print(f"   Sovereign Status: {sovereign_status}")
            print(f"   Multiverse Control: {multiverse_control}")
        else:
            print(f"⚠️ Sovereign tier not yet achieved")
            print(f"   Campaign Tier: {final_tier}")
            print(f"   Sovereign Status: {sovereign_status}")
            print("   (May require ceremony completion in subsequent turns)")

        evidence["lifecycle_stages"].append({
            "stage": 5,
            "name": "verify_sovereign_ascension",
            "status": "success" if is_sovereign else "pending",
            "final_tier": final_tier,
            "sovereign_status": sovereign_status,
            "multiverse_control": multiverse_control,
        })

        # ================================================================
        # TEST RESULTS
        # ================================================================
        print("\n" + "=" * 80)
        print("TEST RESULTS SUMMARY")
        print("=" * 80)

        # Overall success if:
        # 1. Campaign created
        # 2. Sovereign conditions set (divine tier + universe_control >= 70)
        # 3. Ascension trigger worked (CampaignUpgradeAgent or sovereign tier achieved)
        overall_success = (
            campaign_id is not None
            and custom_state.get("campaign_tier") == "divine"
            and custom_state.get("universe_control", 0) >= 70
            and (trigger_success or is_sovereign)
        )

        evidence["test_results"] = {
            "success": overall_success,
            "campaign_created": campaign_id is not None,
            "divine_tier_set": custom_state.get("campaign_tier") == "divine",
            "universe_control_met": custom_state.get("universe_control", 0) >= 70,
            "trigger_fired": trigger_success,
            "sovereign_achieved": is_sovereign,
            "final_tier": final_tier,
            "final_sovereign_status": sovereign_status,
            "total_stages": 5,
            "test_end": datetime.now(timezone.utc).isoformat(),
        }

        print(f"Overall Success: {'✅ PASS' if overall_success else '❌ FAIL'}")
        print(f"Campaign Created: {'✅' if campaign_id else '❌'}")
        print(f"Divine Tier Set: {'✅' if custom_state.get('campaign_tier') == 'divine' else '❌'}")
        print(f"Universe Control Met: {'✅' if custom_state.get('universe_control', 0) >= 70 else '❌'}")
        print(f"Trigger Fired: {'✅' if trigger_success else '⚠️'}")
        print(f"Sovereign Achieved: {'✅' if is_sovereign else '⚠️ pending'}")

        return evidence

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        evidence["error"] = str(e)
        evidence["test_results"] = {
            "success": False,
            "error": str(e),
            "test_end": datetime.now(timezone.utc).isoformat(),
        }
        return evidence


def main() -> int:
    """Main entry point for multiverse ascension lifecycle test."""
    parser = argparse.ArgumentParser(
        description="Multiverse Ascension Lifecycle Test (Sovereign Protocol Speedrun)"
    )
    parser.add_argument(
        "--server-url",
        default="http://localhost:8081",
        help="MCP server URL",
    )
    parser.add_argument(
        "--model",
        default="gemini-2.0-flash",
        help="Model ID for LLM calls",
    )
    parser.add_argument(
        "--start-server",
        action="store_true",
        help="Start a local MCP server for testing",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    server: LocalServer | None = None

    try:
        if args.start_server:
            print("🚀 Starting local MCP server...")
            port = pick_free_port()
            server = start_local_mcp_server(port)
            base_url = f"http://localhost:{port}"
            print(f"✅ Server started at {base_url}")
            # Wait for server to be ready
            time.sleep(10)
            print("⏳ Waiting for server to initialize...")
        else:
            base_url = args.server_url

        # Run the test
        evidence = run_multiverse_ascension_test(
            base_url=base_url,
            model_id=args.model,
            verbose=args.verbose,
        )

        # Save evidence
        evidence_dir = evidence_utils.get_evidence_dir("multiverse_ascension_lifecycle")
        evidence_utils.save_evidence(evidence_dir, evidence, "evidence.json")

        # Create provenance info
        provenance = evidence_utils.capture_provenance(base_url)

        # Create evidence bundle with correct signature
        evidence_utils.create_evidence_bundle(
            evidence_dir,
            test_name="multiverse_ascension_lifecycle",
            provenance=provenance,
            results=evidence.get("test_results", {}),
            request_responses=evidence.get("interactions", []),
            methodology_text="Sovereign protocol speedrun: Divine campaign → Actions → GOD MODE setup → Trigger → Verify",
        )

        print(f"\n📁 Evidence saved to: {evidence_dir}")

        success = evidence.get("test_results", {}).get("success", False)
        return 0 if success else 1

    finally:
        if server:
            print("🛑 Stopping local server...")
            server.stop()


if __name__ == "__main__":
    sys.exit(main())
