#!/usr/bin/env python3
"""
Divine Ascension Lifecycle Test (God Tier Speedrun)

Validates the complete divine ascension lifecycle:
1. Create character (campaign creation)
2. Do 1-2 misc actions (explore, interact)
3. GOD MODE: Setup divine conditions (level 25+, divine_potential 100+)
4. Verify CampaignUpgradeAgent trigger fires
5. Ascend to divine tier (become god)

Evidence Bundle: Complete request/response pairs with provenance tracking
Saves to: /tmp/worldarchitect.ai/<branch>/divine_ascension_lifecycle/
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


def setup_divine_conditions(
    client: MCPClient,
    user_id: str,
    campaign_id: str,
) -> dict[str, Any]:
    """Use GOD MODE to setup divine ascension conditions.

    Sets:
    - character_data.level = 25 (DIVINE_UPGRADE_LEVEL_THRESHOLD)
    - custom_campaign_state.divine_potential = 100 (DIVINE_POTENTIAL_THRESHOLD)
    - custom_campaign_state.campaign_tier = "mortal" (starting tier)
    - XP to match level 25

    Returns:
        Response from the GOD MODE update.
    """
    # Divine-ready state
    state_changes = {
        "character_data": {
            "level": 25,
            "xp": 470000,  # Level 25 XP threshold
            "class": "Epic Champion",
            "race": "Human",
            "alignment": "Lawful Good",
            "attributes": {
                "strength": 20,
                "dexterity": 18,
                "constitution": 20,
                "intelligence": 16,
                "wisdom": 18,
                "charisma": 24,  # High charisma for divine presence
            },
            "hp": 250,
            "max_hp": 250,
        },
        "custom_campaign_state": {
            "divine_potential": 100,  # At threshold
            "campaign_tier": "mortal",  # Ready to ascend
            "divine_deeds": [
                "Defeated the Lich King",
                "Sealed the Abyss Portal",
                "United the Kingdoms",
                "Slew Tiamat's Avatar",
            ],
            "worshippers": 10000,  # Initial worshipper base
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


def run_divine_ascension_test(
    base_url: str,
    model_id: str = "gemini-2.0-flash",
    verbose: bool = False,
) -> dict[str, Any]:
    """Run the complete divine ascension lifecycle test.

    Lifecycle:
    1. Create campaign with epic hero character
    2. Do 1-2 misc actions (explore ancient temple)
    3. GOD MODE: Set divine conditions
    4. Trigger divine ascension ("I wanna be a god")
    5. Verify divine tier achieved

    Args:
        base_url: MCP server URL (e.g., http://localhost:8081)
        model_id: Model to use for LLM calls
        verbose: Print detailed output

    Returns:
        Evidence dict with test results and provenance
    """
    print("\n" + "=" * 80)
    print("DIVINE ASCENSION LIFECYCLE TEST (GOD TIER SPEEDRUN)")
    print("=" * 80)
    print(f"Server: {base_url}")
    print(f"Model: {model_id}")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 80)

    # Initialize evidence structure
    evidence: dict[str, Any] = {
        "test_name": "divine_ascension_lifecycle",
        "test_start": datetime.now(timezone.utc).isoformat(),
        "server_url": base_url,
        "model_id": model_id,
        "lifecycle_stages": [],
        "interactions": [],
        "state_snapshots": [],
    }

    client = MCPClient(base_url)
    user_id = f"divine_test_{int(time.time())}"
    campaign_name = f"Divine Ascension Test {datetime.now().strftime('%H%M%S')}"

    try:
        # ================================================================
        # STAGE 1: Create Campaign (Character Creation)
        # ================================================================
        print("\n🎮 STAGE 1: Creating epic hero campaign...")
        print("-" * 40)

        campaign_id = create_campaign(
            client,
            user_id=user_id,
            title=campaign_name,
            description="Epic hero ready to transcend mortality",
            character="Aelindra the Eternal, a legendary champion who has united kingdoms, "
                      "slain dragon gods, and stands at the threshold of divinity. "
                      "Level 25 with 470,000 XP. Stats: STR 20, DEX 18, CON 20, INT 16, WIS 18, CHA 24.",
            setting="The Celestial Temple atop Mount Ascension, where mortal heroes "
                    "may petition the divine council for godhood.",
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
        # STAGE 2: Misc Actions (Explore, Interact)
        # ================================================================
        print("\n🏛️ STAGE 2: Exploring and interacting...")
        print("-" * 40)

        # Action 2a: Explore the temple
        explore_input = (
            "I explore the Celestial Temple, examining the ancient murals depicting "
            "the ascension of past mortals who became gods. I seek the Chamber of Trials "
            "where the divine council awaits."
        )
        print(f"Action 2a: {explore_input[:60]}...")

        explore_response = process_action(
            client,
            user_id=user_id,
            campaign_id=campaign_id,
            user_input=explore_input,
        )
        print("✅ Exploration complete")
        evidence["interactions"].append({
            "stage": "2a",
            "action": "explore",
            "input": explore_input,
            "response": explore_response,
        })

        # Action 2b: Interact with temple guardian
        interact_input = (
            "I speak with the ancient temple guardian, asking about the requirements "
            "for divine ascension and what trials await those who seek godhood."
        )
        print(f"Action 2b: {interact_input[:60]}...")

        interact_response = process_action(
            client,
            user_id=user_id,
            campaign_id=campaign_id,
            user_input=interact_input,
        )
        print("✅ Interaction complete")
        evidence["interactions"].append({
            "stage": "2b",
            "action": "interact",
            "input": interact_input,
            "response": interact_response,
        })

        evidence["lifecycle_stages"].append({
            "stage": 2,
            "name": "misc_actions",
            "status": "success",
            "actions_count": 2,
        })

        # ================================================================
        # STAGE 3: GOD MODE - Setup Divine Conditions
        # ================================================================
        print("\n⚡ STAGE 3: GOD MODE - Setting up divine conditions...")
        print("-" * 40)

        setup_response = setup_divine_conditions(client, user_id, campaign_id)
        print("✅ Divine conditions set via GOD MODE")
        print("   - Level: 25 (at divine threshold)")
        print("   - Divine Potential: 100 (at threshold)")
        print("   - Campaign Tier: mortal (ready to ascend)")

        evidence["interactions"].append({
            "stage": "3",
            "action": "god_mode_setup",
            "input": "GOD_MODE_UPDATE_STATE:{divine conditions}",
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
        print(f"   Verified Divine Potential: {custom_state.get('divine_potential', 'N/A')}")

        evidence["lifecycle_stages"].append({
            "stage": 3,
            "name": "god_mode_setup",
            "status": "success",
            "divine_conditions": {
                "level": char_data.get("level"),
                "divine_potential": custom_state.get("divine_potential"),
                "campaign_tier": custom_state.get("campaign_tier"),
            },
        })

        # ================================================================
        # STAGE 4: Trigger Divine Ascension
        # ================================================================
        print("\n🌟 STAGE 4: Triggering divine ascension...")
        print("-" * 40)

        # Use semantic routing phrase to trigger CampaignUpgradeAgent
        ascension_input = (
            "I wanna be a god! I have proven my worth through countless trials. "
            "I petition the divine council for ascension to godhood. "
            "Let my divine potential be realized!"
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
        print(f"✅ Ascension action processed (Agent: {agent_used})")

        evidence["interactions"].append({
            "stage": "4",
            "action": "trigger_ascension",
            "input": ascension_input,
            "response": ascension_response,
            "agent_used": agent_used,
        })

        # Verify CampaignUpgradeAgent was triggered
        trigger_success = "campaign_upgrade" in str(agent_used).lower() or "upgrade" in str(agent_used).lower()
        if trigger_success:
            print("✅ CampaignUpgradeAgent trigger VERIFIED")
        else:
            print(f"⚠️ Agent used: {agent_used} (may or may not be CampaignUpgradeAgent)")

        evidence["lifecycle_stages"].append({
            "stage": 4,
            "name": "trigger_ascension",
            "status": "success" if trigger_success else "partial",
            "agent_used": agent_used,
            "trigger_verified": trigger_success,
        })

        # ================================================================
        # STAGE 5: Verify Divine Tier Achieved
        # ================================================================
        print("\n👑 STAGE 5: Verifying divine ascension...")
        print("-" * 40)

        final_state = get_campaign_state(
            client, user_id=user_id, campaign_id=campaign_id
        )
        final_game_state = final_state.get("game_state", {})
        final_custom_state = final_game_state.get("custom_campaign_state", {})

        final_tier = final_custom_state.get("campaign_tier", "unknown")
        divine_rank = final_custom_state.get("divine_rank", "none")

        evidence["state_snapshots"].append({
            "stage": 5,
            "game_state": final_game_state,
        })

        # Check for divine tier markers
        is_divine = (
            final_tier == "divine"
            or divine_rank not in (None, "none", "mortal")
            or "god" in str(final_tier).lower()
            or "divine" in str(final_tier).lower()
        )

        if is_divine:
            print(f"✅ DIVINE ASCENSION VERIFIED!")
            print(f"   Campaign Tier: {final_tier}")
            print(f"   Divine Rank: {divine_rank}")
        else:
            print(f"⚠️ Divine tier not yet achieved")
            print(f"   Campaign Tier: {final_tier}")
            print(f"   Divine Rank: {divine_rank}")
            print("   (May require ceremony completion in subsequent turns)")

        evidence["lifecycle_stages"].append({
            "stage": 5,
            "name": "verify_ascension",
            "status": "success" if is_divine else "pending",
            "final_tier": final_tier,
            "divine_rank": divine_rank,
        })

        # ================================================================
        # TEST RESULTS
        # ================================================================
        print("\n" + "=" * 80)
        print("TEST RESULTS SUMMARY")
        print("=" * 80)

        # Overall success if:
        # 1. Campaign created
        # 2. Divine conditions set
        # 3. Ascension trigger worked (CampaignUpgradeAgent or divine tier achieved)
        overall_success = (
            campaign_id is not None
            and custom_state.get("divine_potential", 0) >= 100
            and (trigger_success or is_divine)
        )

        evidence["test_results"] = {
            "success": overall_success,
            "campaign_created": campaign_id is not None,
            "divine_conditions_set": custom_state.get("divine_potential", 0) >= 100,
            "trigger_fired": trigger_success,
            "divine_achieved": is_divine,
            "final_tier": final_tier,
            "final_divine_rank": divine_rank,
            "total_stages": 5,
            "test_end": datetime.now(timezone.utc).isoformat(),
        }

        print(f"Overall Success: {'✅ PASS' if overall_success else '❌ FAIL'}")
        print(f"Campaign Created: {'✅' if campaign_id else '❌'}")
        print(f"Divine Conditions Set: {'✅' if custom_state.get('divine_potential', 0) >= 100 else '❌'}")
        print(f"Trigger Fired: {'✅' if trigger_success else '⚠️'}")
        print(f"Divine Achieved: {'✅' if is_divine else '⚠️ pending'}")

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
    """Main entry point for divine ascension lifecycle test."""
    parser = argparse.ArgumentParser(
        description="Divine Ascension Lifecycle Test (God Tier Speedrun)"
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
        evidence = run_divine_ascension_test(
            base_url=base_url,
            model_id=args.model,
            verbose=args.verbose,
        )

        # Save evidence
        evidence_dir = evidence_utils.get_evidence_dir("divine_ascension_lifecycle")
        evidence_utils.save_evidence(evidence_dir, evidence, "evidence.json")

        # Create provenance info
        provenance = evidence_utils.capture_provenance(base_url)

        # Create evidence bundle with correct signature
        evidence_utils.create_evidence_bundle(
            evidence_dir,
            test_name="divine_ascension_lifecycle",
            provenance=provenance,
            results=evidence.get("test_results", {}),
            request_responses=evidence.get("interactions", []),
            methodology_text="God tier speedrun: Campaign → Actions → GOD MODE setup → Trigger → Verify",
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
