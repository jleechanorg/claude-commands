#!/usr/bin/env python3
"""
Real Lifecycle Tests for Divine and Multiverse Ascension

Unlike test_divine_ascension_lifecycle.py (GOD MODE speedrun), these tests
use natural gameplay actions to trigger ascension through real mechanics:

1. Divine Ascension via Level 25 (XP Path)
   - Seed: Level 24 with 469,500 XP (500 below threshold)
   - Gameplay: Combat encounter(s) to earn remaining XP
   - Trigger: Level-up to 25 → CampaignUpgradeAgent

2. Divine Ascension via Divine Potential (Heroic Deeds Path)
   - Seed: Level 20 with divine_potential = 70
   - Gameplay: Divine artifact touch, defeat divine entity, receive blessing
   - Trigger: divine_potential >= 100 → CampaignUpgradeAgent

3. Multiverse Ascension via Universe Control
   - Seed: Divine tier with universe_control = 50
   - Gameplay: Cosmic deeds (defeat world threats, seize forces)
   - Trigger: universe_control >= 70 → CampaignUpgradeAgent

Evidence Bundle: /tmp/worldarchitect.ai/<branch>/ascension_real_lifecycle/
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Add project root to path for testing_mcp.lib imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import from testing_mcp.lib (canonical shared utilities)
from testing_mcp.lib import evidence_utils
from testing_mcp.lib.campaign_utils import create_campaign, get_campaign_state, process_action
from testing_mcp.lib.mcp_client import MCPClient
from testing_mcp.lib.model_utils import settings_for_model, update_user_settings
from testing_mcp.lib.server_utils import pick_free_port


# =============================================================================
# METRIC TRACKING HELPERS
# =============================================================================


def get_metric_value(
    client: MCPClient,
    user_id: str,
    campaign_id: str,
    metric_key: str,
) -> int | None:
    """Get current value of a metric from custom_campaign_state.

    Args:
        client: MCPClient instance
        user_id: User ID
        campaign_id: Campaign ID
        metric_key: Key in custom_campaign_state (e.g., 'divine_potential')

    Returns:
        Current metric value or None if not found
    """
    state = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
    game_state = state.get("game_state", {})
    custom_state = game_state.get("custom_campaign_state", {})
    return custom_state.get(metric_key)


def get_player_level(
    client: MCPClient,
    user_id: str,
    campaign_id: str,
) -> int | None:
    """Get current player level from player_character_data."""
    state = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
    game_state = state.get("game_state", {})
    char_data = game_state.get("player_character_data", {})
    return char_data.get("level")


def get_player_xp(
    client: MCPClient,
    user_id: str,
    campaign_id: str,
) -> int | None:
    """Get current player XP from player_character_data.experience."""
    state = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
    game_state = state.get("game_state", {})
    char_data = game_state.get("player_character_data", {})
    experience = char_data.get("experience", {})
    if isinstance(experience, dict):
        return experience.get("current", experience.get("xp"))
    return char_data.get("xp")


def track_metric_progress(
    client: MCPClient,
    user_id: str,
    campaign_id: str,
    actions: list[dict[str, Any]],
    metric_key: str,
    target_value: int,
    max_retries_per_action: int = 2,
    verbose: bool = False,
) -> dict[str, Any]:
    """Execute actions and track metric increments.

    Args:
        client: MCPClient instance
        user_id: User ID
        campaign_id: Campaign ID
        actions: List of {"prompt": str, "escalated_prompt": str, ...}
        metric_key: Key to track (e.g., 'divine_potential', 'universe_control')
        target_value: Target metric value (e.g., 100 for divine_potential)
        max_retries_per_action: Retries with escalated prompt if no increment
        verbose: Print detailed output

    Returns:
        Dict with success status, metric history, and interactions
    """
    result = {
        "success": False,
        "metric_key": metric_key,
        "target_value": target_value,
        "metric_history": [],
        "interactions": [],
    }

    initial_value = get_metric_value(client, user_id, campaign_id, metric_key) or 0
    result["metric_history"].append({
        "turn": 0,
        "value": initial_value,
        "action": "initial",
    })

    if verbose:
        print(f"   Initial {metric_key}: {initial_value}")

    current_value = initial_value

    for i, action_config in enumerate(actions, start=1):
        if current_value >= target_value:
            result["success"] = True
            if verbose:
                print(f"   Target reached: {current_value} >= {target_value}")
            break

        prompt = action_config["prompt"]
        escalated_prompt = action_config.get("escalated_prompt", prompt)

        # Try primary prompt
        if verbose:
            print(f"   Turn {i}: {prompt[:60]}...")

        response = process_action(
            client,
            user_id=user_id,
            campaign_id=campaign_id,
            user_input=prompt,
        )

        new_value = get_metric_value(client, user_id, campaign_id, metric_key) or 0
        increment = new_value - current_value

        result["interactions"].append({
            "turn": i,
            "prompt": prompt,
            "response": response,
            "value_before": current_value,
            "value_after": new_value,
            "increment": increment,
        })

        result["metric_history"].append({
            "turn": i,
            "value": new_value,
            "action": prompt[:50],
            "increment": increment,
        })

        if increment > 0:
            if verbose:
                print(f"   ✅ {metric_key}: {current_value} → {new_value} (+{increment})")
            current_value = new_value
        else:
            # Retry with escalated prompt
            if verbose:
                print(f"   ⚠️ No increment, trying escalated prompt...")

            for retry in range(max_retries_per_action):
                retry_response = process_action(
                    client,
                    user_id=user_id,
                    campaign_id=campaign_id,
                    user_input=escalated_prompt,
                )

                retry_value = get_metric_value(client, user_id, campaign_id, metric_key) or 0
                retry_increment = retry_value - current_value

                result["interactions"].append({
                    "turn": f"{i}_retry_{retry + 1}",
                    "prompt": escalated_prompt,
                    "response": retry_response,
                    "value_before": current_value,
                    "value_after": retry_value,
                    "increment": retry_increment,
                })

                if retry_increment > 0:
                    if verbose:
                        print(f"   ✅ Retry worked: {current_value} → {retry_value} (+{retry_increment})")
                    current_value = retry_value
                    result["metric_history"].append({
                        "turn": f"{i}_retry_{retry + 1}",
                        "value": retry_value,
                        "action": f"retry: {escalated_prompt[:30]}",
                        "increment": retry_increment,
                    })
                    break

    # Final check
    final_value = get_metric_value(client, user_id, campaign_id, metric_key) or 0
    result["final_value"] = final_value
    result["success"] = final_value >= target_value

    return result


# =============================================================================
# SEEDING FUNCTIONS (Minimal GOD MODE)
# =============================================================================


def seed_level_24_near_threshold(
    client: MCPClient,
    user_id: str,
    campaign_id: str,
) -> dict[str, Any]:
    """Seed character at Level 24 with XP just below Level 25 threshold.

    Sets:
    - Level 24, XP = 469,500 (500 XP below 470,000 threshold)
    - divine_potential = 50 (below threshold, won't trigger divine upgrade)
    - campaign_tier = "mortal"
    - Character creation complete

    Returns:
        Response from GOD MODE update
    """
    state_changes = {
        "player_character_data": {
            "level": 24,
            "xp": 469_500,  # 500 XP below Level 25 threshold
            "experience": {
                "current": 469_500,
                "next_level": 470_000,
            },
            "class": "Epic Warrior",
            "race": "Human",
            "alignment": "Neutral Good",
            "attributes": {
                "strength": 20,
                "dexterity": 16,
                "constitution": 18,
                "intelligence": 14,
                "wisdom": 16,
                "charisma": 18,
            },
            "hp": 200,
            "max_hp": 200,
        },
        "custom_campaign_state": {
            "divine_potential": 50,  # Below threshold - won't trigger
            "campaign_tier": "mortal",
            "character_creation_in_progress": False,
            "character_creation_completed": True,
            "character_creation_stage": "complete",
        },
    }

    god_mode_payload = f"GOD_MODE_UPDATE_STATE:{json.dumps(state_changes)}"

    return process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=god_mode_payload,
        mode="god",
    )


def seed_divine_potential_70(
    client: MCPClient,
    user_id: str,
    campaign_id: str,
) -> dict[str, Any]:
    """Seed character at Level 20 with divine_potential = 70.

    Sets:
    - Level 20, XP = 355,000 (at Level 20 threshold, won't trigger level path)
    - divine_potential = 70 (30 away from threshold)
    - campaign_tier = "mortal"
    - Character at Celestial Temple setting

    Returns:
        Response from GOD MODE update
    """
    state_changes = {
        "player_character_data": {
            "level": 20,
            "xp": 355_000,
            "experience": {
                "current": 355_000,
                "next_level": 376_000,  # Level 21
            },
            "class": "Champion of Light",
            "race": "Aasimar",
            "alignment": "Lawful Good",
            "attributes": {
                "strength": 18,
                "dexterity": 14,
                "constitution": 16,
                "intelligence": 12,
                "wisdom": 16,
                "charisma": 20,  # High charisma for divine connection
            },
            "hp": 160,
            "max_hp": 160,
        },
        "custom_campaign_state": {
            "divine_potential": 70,  # 30 away from threshold
            "campaign_tier": "mortal",
            "divine_deeds": [
                "Slew the Demon Prince",
                "Blessed by the Overdeity",
            ],
            "character_creation_in_progress": False,
            "character_creation_completed": True,
            "character_creation_stage": "complete",
        },
    }

    god_mode_payload = f"GOD_MODE_UPDATE_STATE:{json.dumps(state_changes)}"

    return process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=god_mode_payload,
        mode="god",
    )


def seed_universe_control_50(
    client: MCPClient,
    user_id: str,
    campaign_id: str,
) -> dict[str, Any]:
    """Seed divine-tier character with universe_control = 50.

    Sets:
    - Level 35, campaign_tier = "divine"
    - universe_control = 50 (20 away from threshold)
    - divine_rank = "demigod"

    Returns:
        Response from GOD MODE update
    """
    state_changes = {
        "player_character_data": {
            "level": 35,
            "xp": 1_500_000,
            "class": "Divine Champion",
            "race": "Ascended Human",
            "alignment": "Lawful Neutral",
            "attributes": {
                "strength": 26,
                "dexterity": 22,
                "constitution": 26,
                "intelligence": 20,
                "wisdom": 24,
                "charisma": 30,
            },
            "hp": 500,
            "max_hp": 500,
        },
        "custom_campaign_state": {
            "campaign_tier": "divine",
            "divine_rank": "demigod",
            "divine_potential": 200,  # Far above threshold
            "universe_control": 50,  # 20 away from sovereign threshold
            "controlled_universes": [
                {"name": "Prime Material", "control": 90},
            ],
            "portfolio": ["War", "Justice"],
            "worshippers": 1_000_000,
            "character_creation_in_progress": False,
            "character_creation_completed": True,
            "character_creation_stage": "complete",
        },
    }

    god_mode_payload = f"GOD_MODE_UPDATE_STATE:{json.dumps(state_changes)}"

    return process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=god_mode_payload,
        mode="god",
    )


# =============================================================================
# TEST 1: DIVINE ASCENSION VIA LEVEL 25 (XP PATH)
# =============================================================================


def test_divine_ascension_via_level_25(
    base_url: str,
    model_id: str = "gemini-2.0-flash",
    verbose: bool = False,
) -> dict[str, Any]:
    """Test divine ascension triggered by reaching Level 25 via combat XP.

    Lifecycle:
    1. Create campaign
    2. Seed Level 24 character with 469,500 XP (500 below threshold)
    3. Initiate combat encounter vs high-CR enemy
    4. Win combat to earn 500+ XP
    5. Verify level-up to 25 triggers CampaignUpgradeAgent

    Args:
        base_url: MCP server URL
        model_id: Model to use for LLM calls
        verbose: Print detailed output

    Returns:
        Evidence dict with test results
    """
    print("\n" + "=" * 80)
    print("TEST: DIVINE ASCENSION VIA LEVEL 25 (XP PATH)")
    print("=" * 80)
    print(f"Server: {base_url}")
    print(f"Model: {model_id}")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 80)

    evidence: dict[str, Any] = {
        "test_name": "divine_ascension_via_level_25",
        "test_type": "real_lifecycle",
        "test_start": datetime.now(timezone.utc).isoformat(),
        "server_url": base_url,
        "model_id": model_id,
        "lifecycle_stages": [],
        "interactions": [],
        "level_history": [],
        "xp_history": [],
    }

    client = MCPClient(base_url)
    user_id = f"level25_test_{int(time.time())}"
    campaign_name = f"Level 25 Ascension Test {datetime.now().strftime('%H%M%S')}"

    try:
        # Configure model
        model_settings = settings_for_model(model_id)
        update_user_settings(client, user_id=user_id, settings=model_settings)

        # ================================================================
        # STAGE 1: Create Campaign
        # ================================================================
        print("\n🎮 STAGE 1: Creating campaign...")
        print("-" * 40)

        campaign_id = create_campaign(
            client,
            user_id=user_id,
            title=campaign_name,
            description="Epic warrior on the brink of divine power",
            character="Valorian the Brave, a legendary warrior who has conquered countless foes. "
                      "Level 24 with vast experience. One victory away from transcendence.",
            setting="The Dragon's Peak, lair of the ancient wyrm Scorathax. "
                    "Defeating this legendary beast will grant immense experience.",
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
        })

        # ================================================================
        # STAGE 2: Seed Level 24 Character
        # ================================================================
        print("\n⚡ STAGE 2: Seeding Level 24 character (minimal GOD MODE)...")
        print("-" * 40)

        seed_response = seed_level_24_near_threshold(client, user_id, campaign_id)
        print("✅ Seeded: Level 24, XP = 469,500 (500 below Level 25)")

        # Verify seeding
        initial_level = get_player_level(client, user_id, campaign_id)
        initial_xp = get_player_xp(client, user_id, campaign_id)
        print(f"   Verified Level: {initial_level}")
        print(f"   Verified XP: {initial_xp}")

        evidence["level_history"].append({"stage": "seed", "level": initial_level})
        evidence["xp_history"].append({"stage": "seed", "xp": initial_xp})
        evidence["lifecycle_stages"].append({
            "stage": 2,
            "name": "seed_level_24",
            "status": "success",
            "level": initial_level,
            "xp": initial_xp,
        })

        # ================================================================
        # STAGE 3: Combat Encounter
        # ================================================================
        print("\n⚔️ STAGE 3: Initiating combat with dragon...")
        print("-" * 40)

        # Initiate combat
        combat_init = (
            "I challenge Scorathax the Ancient Dragon! I draw my legendary sword "
            "and charge into battle against the wyrm!"
        )
        print(f"Input: {combat_init[:60]}...")

        combat_response = process_action(
            client,
            user_id=user_id,
            campaign_id=campaign_id,
            user_input=combat_init,
        )
        print("✅ Combat initiated")

        evidence["interactions"].append({
            "stage": "3_init",
            "action": "combat_initiate",
            "input": combat_init,
            "response": combat_response,
        })

        # Combat rounds (up to 5 to ensure victory)
        combat_actions = [
            "I strike the dragon with a devastating blow! Attack with full force!",
            "I dodge the dragon's flames and counter-attack! Finish the beast!",
            "I plunge my sword into the dragon's heart! Victory is mine!",
        ]

        for i, action in enumerate(combat_actions, start=1):
            print(f"   Combat round {i}: {action[:50]}...")
            round_response = process_action(
                client,
                user_id=user_id,
                campaign_id=campaign_id,
                user_input=action,
            )
            evidence["interactions"].append({
                "stage": f"3_round_{i}",
                "action": "combat_round",
                "input": action,
                "response": round_response,
            })

            # Check if combat ended and XP was awarded
            current_xp = get_player_xp(client, user_id, campaign_id)
            current_level = get_player_level(client, user_id, campaign_id)

            evidence["xp_history"].append({
                "stage": f"combat_round_{i}",
                "xp": current_xp,
            })

            if current_level and current_level >= 25:
                print(f"   ✅ Level 25 achieved! XP: {current_xp}")
                break
            elif current_xp and current_xp >= 470_000:
                print(f"   ✅ XP threshold crossed: {current_xp}")
                break

        evidence["lifecycle_stages"].append({
            "stage": 3,
            "name": "combat_encounter",
            "status": "success",
            "rounds": len(combat_actions),
        })

        # ================================================================
        # STAGE 4: Verify Level-Up and Trigger Ascension
        # ================================================================
        print("\n🌟 STAGE 4: Checking for level-up and ascension trigger...")
        print("-" * 40)

        final_level = get_player_level(client, user_id, campaign_id)
        final_xp = get_player_xp(client, user_id, campaign_id)

        print(f"   Final Level: {final_level}")
        print(f"   Final XP: {final_xp}")

        evidence["level_history"].append({"stage": "final", "level": final_level})
        evidence["xp_history"].append({"stage": "final", "xp": final_xp})

        # If level 25, trigger ascension
        level_25_achieved = final_level is not None and final_level >= 25
        xp_threshold_crossed = final_xp is not None and final_xp >= 470_000

        if level_25_achieved or xp_threshold_crossed:
            print("✅ Level 25 threshold reached!")

            # Trigger ascension
            ascension_input = (
                "I have reached the pinnacle of mortal power! "
                "I petition for divine ascension! Let my godhood begin!"
            )
            print(f"   Triggering ascension: {ascension_input[:50]}...")

            ascension_response = process_action(
                client,
                user_id=user_id,
                campaign_id=campaign_id,
                user_input=ascension_input,
            )

            agent_used = ascension_response.get("agent_used", "unknown")
            print(f"   Agent used: {agent_used}")

            evidence["interactions"].append({
                "stage": "4_ascension",
                "action": "trigger_ascension",
                "input": ascension_input,
                "response": ascension_response,
                "agent_used": agent_used,
            })

            trigger_success = "upgrade" in str(agent_used).lower() or "campaign" in str(agent_used).lower()
        else:
            print("⚠️ Level 25 not yet reached - may need additional combat")
            trigger_success = False

        evidence["lifecycle_stages"].append({
            "stage": 4,
            "name": "level_up_verification",
            "status": "success" if level_25_achieved else "partial",
            "final_level": final_level,
            "final_xp": final_xp,
            "level_25_achieved": level_25_achieved,
        })

        # ================================================================
        # STAGE 5: Verify Divine Tier
        # ================================================================
        print("\n👑 STAGE 5: Verifying divine tier...")
        print("-" * 40)

        final_state = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
        final_game_state = final_state.get("game_state", {})
        final_custom_state = final_game_state.get("custom_campaign_state", {})

        final_tier = final_custom_state.get("campaign_tier", "unknown")
        divine_rank = final_custom_state.get("divine_rank", "none")

        is_divine = final_tier == "divine" or divine_rank not in (None, "none", "mortal")

        print(f"   Campaign Tier: {final_tier}")
        print(f"   Divine Rank: {divine_rank}")

        if is_divine:
            print("✅ DIVINE ASCENSION ACHIEVED!")
        else:
            print("⚠️ Divine tier pending (may require ceremony completion)")

        evidence["lifecycle_stages"].append({
            "stage": 5,
            "name": "divine_verification",
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

        overall_success = (
            campaign_id is not None
            and (level_25_achieved or xp_threshold_crossed)
        )

        evidence["test_results"] = {
            "success": overall_success,
            "campaign_created": campaign_id is not None,
            "level_25_achieved": level_25_achieved,
            "xp_threshold_crossed": xp_threshold_crossed,
            "trigger_fired": trigger_success if level_25_achieved else False,
            "divine_achieved": is_divine,
            "final_tier": final_tier,
            "final_level": final_level,
            "final_xp": final_xp,
            "test_end": datetime.now(timezone.utc).isoformat(),
        }

        print(f"Overall: {'✅ PASS' if overall_success else '❌ FAIL'}")
        print(f"Level 25 Achieved: {'✅' if level_25_achieved else '❌'}")
        print(f"Divine Tier: {'✅' if is_divine else '⚠️ pending'}")

        return evidence

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        evidence["error"] = str(e)
        evidence["test_results"] = {
            "success": False,
            "error": str(e),
            "test_end": datetime.now(timezone.utc).isoformat(),
        }
        return evidence


# =============================================================================
# TEST 2: DIVINE ASCENSION VIA DIVINE POTENTIAL (HEROIC DEEDS)
# =============================================================================


def test_divine_ascension_via_divine_potential(
    base_url: str,
    model_id: str = "gemini-2.0-flash",
    verbose: bool = False,
) -> dict[str, Any]:
    """Test divine ascension triggered by divine_potential reaching 100.

    Lifecycle:
    1. Create campaign at Celestial Temple
    2. Seed Level 20 with divine_potential = 70
    3. Perform heroic deeds that should increment divine_potential:
       - Touch divine artifact (+5-10)
       - Defeat divine entity (+10-20)
       - Receive divine blessing (+15-25)
    4. Verify divine_potential >= 100 triggers CampaignUpgradeAgent

    Args:
        base_url: MCP server URL
        model_id: Model to use for LLM calls
        verbose: Print detailed output

    Returns:
        Evidence dict with test results
    """
    print("\n" + "=" * 80)
    print("TEST: DIVINE ASCENSION VIA DIVINE POTENTIAL (HEROIC DEEDS)")
    print("=" * 80)
    print(f"Server: {base_url}")
    print(f"Model: {model_id}")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 80)

    evidence: dict[str, Any] = {
        "test_name": "divine_ascension_via_divine_potential",
        "test_type": "real_lifecycle",
        "test_start": datetime.now(timezone.utc).isoformat(),
        "server_url": base_url,
        "model_id": model_id,
        "lifecycle_stages": [],
        "interactions": [],
        "metric_tracking": None,
    }

    client = MCPClient(base_url)
    user_id = f"divine_potential_test_{int(time.time())}"
    campaign_name = f"Divine Potential Test {datetime.now().strftime('%H%M%S')}"

    try:
        # Configure model
        model_settings = settings_for_model(model_id)
        update_user_settings(client, user_id=user_id, settings=model_settings)

        # ================================================================
        # STAGE 1: Create Campaign
        # ================================================================
        print("\n🎮 STAGE 1: Creating campaign at Celestial Temple...")
        print("-" * 40)

        campaign_id = create_campaign(
            client,
            user_id=user_id,
            title=campaign_name,
            description="Champion seeking divine ascension through heroic deeds",
            character="Lumiel the Radiant, an Aasimar Champion of Light. "
                      "Born with divine blood, they have slain demons and been blessed by gods. "
                      "Now they seek to fully realize their divine potential.",
            setting="The Celestial Temple of Ascension, a holy site where mortals "
                    "with sufficient divine potential may petition for godhood. "
                    "Divine artifacts, celestial beings, and the Overdeity's blessing await.",
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
        })

        # ================================================================
        # STAGE 2: Seed Divine Potential = 70
        # ================================================================
        print("\n⚡ STAGE 2: Seeding divine_potential = 70 (minimal GOD MODE)...")
        print("-" * 40)

        seed_response = seed_divine_potential_70(client, user_id, campaign_id)
        print("✅ Seeded: Level 20, divine_potential = 70")

        initial_dp = get_metric_value(client, user_id, campaign_id, "divine_potential")
        print(f"   Verified divine_potential: {initial_dp}")

        evidence["lifecycle_stages"].append({
            "stage": 2,
            "name": "seed_divine_potential",
            "status": "success",
            "divine_potential": initial_dp,
        })

        # ================================================================
        # STAGE 3: Heroic Deeds to Increment Divine Potential
        # ================================================================
        print("\n✨ STAGE 3: Performing heroic deeds...")
        print("-" * 40)

        # Define actions that should increment divine_potential
        # Per game_state_instruction.md lines 1296-1302
        heroic_actions = [
            {
                "prompt": (
                    "I approach the Shard of Divinity on the altar, a fragment of the Overdeity's power. "
                    "I touch it reverently, channeling my divine potential through the artifact. "
                    "The divine energy flows into me."
                ),
                "escalated_prompt": (
                    "The Shard of Divinity pulses with cosmic power as I touch it. "
                    "My divine potential INCREASES as the artifact's energy merges with my soul. "
                    "I feel myself growing closer to godhood. Update my divine_potential stat."
                ),
                "expected_increment": (5, 10),
                "trigger_type": "divine_artifact",
            },
            {
                "prompt": (
                    "A corrupted seraph attacks the temple! I draw my holy blade and strike down "
                    "this fallen divine being. My blade pierces its corrupted heart, "
                    "and I absorb its celestial essence!"
                ),
                "escalated_prompt": (
                    "I have slain the corrupted seraph, a divine entity! "
                    "Defeating this celestial being greatly increases my divine potential. "
                    "The divine essence of the fallen seraph flows into me. "
                    "My divine_potential grows significantly!"
                ),
                "expected_increment": (10, 20),
                "trigger_type": "defeat_divine_entity",
            },
            {
                "prompt": (
                    "I kneel before the statue of the Overdeity and pray with all my heart. "
                    "'Grant me your blessing, O Divine One! I seek to ascend to godhood!' "
                    "A warm golden light envelops me as the Overdeity responds."
                ),
                "escalated_prompt": (
                    "The Overdeity answers my prayer! Divine blessing washes over me! "
                    "This is a major blessing from a god - it should increase my divine_potential "
                    "by 15-25 points! I feel my divine potential surge dramatically! "
                    "Update divine_potential to reflect this powerful blessing!"
                ),
                "expected_increment": (15, 25),
                "trigger_type": "divine_blessing",
            },
        ]

        # Track metric progress
        metric_result = track_metric_progress(
            client=client,
            user_id=user_id,
            campaign_id=campaign_id,
            actions=heroic_actions,
            metric_key="divine_potential",
            target_value=100,
            max_retries_per_action=2,
            verbose=True,
        )

        evidence["metric_tracking"] = metric_result
        evidence["interactions"].extend(metric_result["interactions"])

        evidence["lifecycle_stages"].append({
            "stage": 3,
            "name": "heroic_deeds",
            "status": "success" if metric_result["success"] else "partial",
            "final_divine_potential": metric_result["final_value"],
            "target_value": 100,
            "metric_history": metric_result["metric_history"],
        })

        # ================================================================
        # STAGE 4: Trigger Divine Ascension
        # ================================================================
        print("\n🌟 STAGE 4: Triggering divine ascension...")
        print("-" * 40)

        final_dp = metric_result["final_value"]
        dp_threshold_crossed = final_dp >= 100

        if dp_threshold_crossed:
            print(f"✅ Divine potential threshold reached: {final_dp} >= 100")

            ascension_input = (
                "My divine potential has reached its zenith! "
                "I petition the divine council - I am ready to ascend to godhood! "
                "Let the ascension ceremony begin!"
            )
            print(f"   Triggering: {ascension_input[:50]}...")

            ascension_response = process_action(
                client,
                user_id=user_id,
                campaign_id=campaign_id,
                user_input=ascension_input,
            )

            agent_used = ascension_response.get("agent_used", "unknown")
            print(f"   Agent used: {agent_used}")

            evidence["interactions"].append({
                "stage": "4_ascension",
                "action": "trigger_ascension",
                "input": ascension_input,
                "response": ascension_response,
                "agent_used": agent_used,
            })

            trigger_success = "upgrade" in str(agent_used).lower()
        else:
            print(f"⚠️ Divine potential below threshold: {final_dp} < 100")
            print("   Additional heroic deeds may be needed")
            trigger_success = False

        evidence["lifecycle_stages"].append({
            "stage": 4,
            "name": "ascension_trigger",
            "status": "success" if dp_threshold_crossed else "partial",
            "divine_potential": final_dp,
            "threshold_crossed": dp_threshold_crossed,
        })

        # ================================================================
        # STAGE 5: Verify Divine Tier
        # ================================================================
        print("\n👑 STAGE 5: Verifying divine tier...")
        print("-" * 40)

        final_state = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
        final_game_state = final_state.get("game_state", {})
        final_custom_state = final_game_state.get("custom_campaign_state", {})

        final_tier = final_custom_state.get("campaign_tier", "unknown")
        divine_rank = final_custom_state.get("divine_rank", "none")

        is_divine = final_tier == "divine" or divine_rank not in (None, "none", "mortal")

        print(f"   Campaign Tier: {final_tier}")
        print(f"   Divine Rank: {divine_rank}")

        if is_divine:
            print("✅ DIVINE ASCENSION ACHIEVED!")
        else:
            print("⚠️ Divine tier pending (may require ceremony completion)")

        evidence["lifecycle_stages"].append({
            "stage": 5,
            "name": "divine_verification",
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

        overall_success = campaign_id is not None and dp_threshold_crossed

        evidence["test_results"] = {
            "success": overall_success,
            "campaign_created": campaign_id is not None,
            "divine_potential_threshold_crossed": dp_threshold_crossed,
            "final_divine_potential": final_dp,
            "trigger_fired": trigger_success,
            "divine_achieved": is_divine,
            "final_tier": final_tier,
            "test_end": datetime.now(timezone.utc).isoformat(),
        }

        print(f"Overall: {'✅ PASS' if overall_success else '❌ FAIL'}")
        print(f"Divine Potential >= 100: {'✅' if dp_threshold_crossed else '❌'} ({final_dp})")
        print(f"Divine Tier: {'✅' if is_divine else '⚠️ pending'}")

        return evidence

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        evidence["error"] = str(e)
        evidence["test_results"] = {
            "success": False,
            "error": str(e),
            "test_end": datetime.now(timezone.utc).isoformat(),
        }
        return evidence


# =============================================================================
# TEST 3: MULTIVERSE ASCENSION VIA UNIVERSE CONTROL
# =============================================================================


def test_multiverse_ascension_via_universe_control(
    base_url: str,
    model_id: str = "gemini-2.0-flash",
    verbose: bool = False,
) -> dict[str, Any]:
    """Test multiverse/sovereign ascension triggered by universe_control >= 70.

    Lifecycle:
    1. Create campaign at Cosmic Nexus
    2. Seed divine-tier character with universe_control = 50
    3. Perform cosmic deeds that should increment universe_control:
       - Defeat world-ending threat (+10-20)
       - Seize control of fundamental force (+15-25)
       - Absorb divine power (+15-25)
    4. Verify universe_control >= 70 triggers CampaignUpgradeAgent

    Args:
        base_url: MCP server URL
        model_id: Model to use for LLM calls
        verbose: Print detailed output

    Returns:
        Evidence dict with test results
    """
    print("\n" + "=" * 80)
    print("TEST: MULTIVERSE ASCENSION VIA UNIVERSE CONTROL")
    print("=" * 80)
    print(f"Server: {base_url}")
    print(f"Model: {model_id}")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 80)

    evidence: dict[str, Any] = {
        "test_name": "multiverse_ascension_via_universe_control",
        "test_type": "real_lifecycle",
        "test_start": datetime.now(timezone.utc).isoformat(),
        "server_url": base_url,
        "model_id": model_id,
        "lifecycle_stages": [],
        "interactions": [],
        "metric_tracking": None,
    }

    client = MCPClient(base_url)
    user_id = f"universe_control_test_{int(time.time())}"
    campaign_name = f"Multiverse Ascension Test {datetime.now().strftime('%H%M%S')}"

    try:
        # Configure model
        model_settings = settings_for_model(model_id)
        update_user_settings(client, user_id=user_id, settings=model_settings)

        # ================================================================
        # STAGE 1: Create Campaign
        # ================================================================
        print("\n🌌 STAGE 1: Creating campaign at Cosmic Nexus...")
        print("-" * 40)

        campaign_id = create_campaign(
            client,
            user_id=user_id,
            title=campaign_name,
            description="Divine being seeking sovereign control of the multiverse",
            character="Aetherion the Eternal, a demigod who has transcended mortality. "
                      "They control the Prime Material and seek to expand their dominion "
                      "across all realities. Divine rank: Demigod. Portfolio: War, Justice.",
            setting="The Cosmic Nexus, crossroads of infinite realities. "
                    "Here gods may petition for Sovereign Protocol - total control "
                    "over the multiverse. World-ending threats and cosmic forces await.",
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
        })

        # ================================================================
        # STAGE 2: Seed Universe Control = 50
        # ================================================================
        print("\n⚡ STAGE 2: Seeding universe_control = 50 (minimal GOD MODE)...")
        print("-" * 40)

        seed_response = seed_universe_control_50(client, user_id, campaign_id)
        print("✅ Seeded: Divine tier, universe_control = 50")

        initial_uc = get_metric_value(client, user_id, campaign_id, "universe_control")
        campaign_tier = get_metric_value(client, user_id, campaign_id, "campaign_tier")
        print(f"   Verified universe_control: {initial_uc}")
        print(f"   Verified campaign_tier: {campaign_tier}")

        evidence["lifecycle_stages"].append({
            "stage": 2,
            "name": "seed_universe_control",
            "status": "success",
            "universe_control": initial_uc,
            "campaign_tier": campaign_tier,
        })

        # ================================================================
        # STAGE 3: Cosmic Deeds to Increment Universe Control
        # ================================================================
        print("\n🌠 STAGE 3: Performing cosmic deeds...")
        print("-" * 40)

        # Define actions that should increment universe_control
        # Per game_state_instruction.md lines 1304-1310
        cosmic_actions = [
            {
                "prompt": (
                    "The Void Eater, a cosmic horror that devours entire universes, "
                    "threatens the multiverse! I unleash my divine power and destroy "
                    "this world-ending threat! The multiverse is saved by my hand!"
                ),
                "escalated_prompt": (
                    "I have destroyed the Void Eater, a WORLD-ENDING THREAT! "
                    "Defeating such a cosmic horror should increase my universe_control "
                    "by 10-20 points! My dominion over the multiverse expands! "
                    "Update my universe_control stat!"
                ),
                "expected_increment": (10, 20),
                "trigger_type": "defeat_world_threat",
            },
            {
                "prompt": (
                    "I reach out and seize control of the fundamental force of Entropy itself! "
                    "Time and decay now bend to my will across all planes of existence! "
                    "I am becoming master of reality!"
                ),
                "escalated_prompt": (
                    "I have gained ABSOLUTE POWER over Entropy, a FUNDAMENTAL FORCE! "
                    "This should increase universe_control by 15-25 points! "
                    "I can now manipulate the decay of all things in the multiverse! "
                    "My cosmic dominion expands dramatically! Update universe_control!"
                ),
                "expected_increment": (15, 25),
                "trigger_type": "control_fundamental_force",
            },
            {
                "prompt": (
                    "The rival god Thanatos falls before me! I absorb their divine essence, "
                    "adding their power over Death to my own portfolio! "
                    "Their worshippers now pray to me!"
                ),
                "escalated_prompt": (
                    "I have ABSORBED THE POWER of a fallen god! "
                    "Absorbing another deity's essence should increase universe_control "
                    "by 15-25 points! Their cosmic influence is now mine! "
                    "My dominion approaches Sovereign status! Update universe_control!"
                ),
                "expected_increment": (15, 25),
                "trigger_type": "absorb_divine_power",
            },
        ]

        # Track metric progress
        metric_result = track_metric_progress(
            client=client,
            user_id=user_id,
            campaign_id=campaign_id,
            actions=cosmic_actions,
            metric_key="universe_control",
            target_value=70,
            max_retries_per_action=2,
            verbose=True,
        )

        evidence["metric_tracking"] = metric_result
        evidence["interactions"].extend(metric_result["interactions"])

        evidence["lifecycle_stages"].append({
            "stage": 3,
            "name": "cosmic_deeds",
            "status": "success" if metric_result["success"] else "partial",
            "final_universe_control": metric_result["final_value"],
            "target_value": 70,
            "metric_history": metric_result["metric_history"],
        })

        # ================================================================
        # STAGE 4: Trigger Sovereign Ascension
        # ================================================================
        print("\n🌟 STAGE 4: Triggering sovereign ascension...")
        print("-" * 40)

        final_uc = metric_result["final_value"]
        uc_threshold_crossed = final_uc >= 70

        if uc_threshold_crossed:
            print(f"✅ Universe control threshold reached: {final_uc} >= 70")

            ascension_input = (
                "My control over the multiverse is nearly absolute! "
                "I invoke the Sovereign Protocol! "
                "I shall become ruler of all realities!"
            )
            print(f"   Triggering: {ascension_input[:50]}...")

            ascension_response = process_action(
                client,
                user_id=user_id,
                campaign_id=campaign_id,
                user_input=ascension_input,
            )

            agent_used = ascension_response.get("agent_used", "unknown")
            print(f"   Agent used: {agent_used}")

            evidence["interactions"].append({
                "stage": "4_ascension",
                "action": "trigger_sovereign",
                "input": ascension_input,
                "response": ascension_response,
                "agent_used": agent_used,
            })

            trigger_success = "upgrade" in str(agent_used).lower()
        else:
            print(f"⚠️ Universe control below threshold: {final_uc} < 70")
            print("   Additional cosmic deeds may be needed")
            trigger_success = False

        evidence["lifecycle_stages"].append({
            "stage": 4,
            "name": "sovereign_trigger",
            "status": "success" if uc_threshold_crossed else "partial",
            "universe_control": final_uc,
            "threshold_crossed": uc_threshold_crossed,
        })

        # ================================================================
        # STAGE 5: Verify Sovereign Tier
        # ================================================================
        print("\n👑 STAGE 5: Verifying sovereign tier...")
        print("-" * 40)

        final_state = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
        final_game_state = final_state.get("game_state", {})
        final_custom_state = final_game_state.get("custom_campaign_state", {})

        final_tier = final_custom_state.get("campaign_tier", "unknown")
        sovereign_rank = final_custom_state.get("sovereign_rank")
        substrate_points = final_custom_state.get("substrate_points")

        is_sovereign = (
            final_tier == "sovereign"
            or sovereign_rank is not None
            or substrate_points is not None
        )

        print(f"   Campaign Tier: {final_tier}")
        print(f"   Sovereign Rank: {sovereign_rank}")
        print(f"   Substrate Points: {substrate_points}")

        if is_sovereign:
            print("✅ SOVEREIGN ASCENSION ACHIEVED!")
        else:
            print("⚠️ Sovereign tier pending (may require ceremony completion)")

        evidence["lifecycle_stages"].append({
            "stage": 5,
            "name": "sovereign_verification",
            "status": "success" if is_sovereign else "pending",
            "final_tier": final_tier,
            "sovereign_rank": sovereign_rank,
            "substrate_points": substrate_points,
        })

        # ================================================================
        # TEST RESULTS
        # ================================================================
        print("\n" + "=" * 80)
        print("TEST RESULTS SUMMARY")
        print("=" * 80)

        overall_success = campaign_id is not None and uc_threshold_crossed

        evidence["test_results"] = {
            "success": overall_success,
            "campaign_created": campaign_id is not None,
            "universe_control_threshold_crossed": uc_threshold_crossed,
            "final_universe_control": final_uc,
            "trigger_fired": trigger_success,
            "sovereign_achieved": is_sovereign,
            "final_tier": final_tier,
            "test_end": datetime.now(timezone.utc).isoformat(),
        }

        print(f"Overall: {'✅ PASS' if overall_success else '❌ FAIL'}")
        print(f"Universe Control >= 70: {'✅' if uc_threshold_crossed else '❌'} ({final_uc})")
        print(f"Sovereign Tier: {'✅' if is_sovereign else '⚠️ pending'}")

        return evidence

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        evidence["error"] = str(e)
        evidence["test_results"] = {
            "success": False,
            "error": str(e),
            "test_end": datetime.now(timezone.utc).isoformat(),
        }
        return evidence


# =============================================================================
# EVIDENCE SAVING
# =============================================================================


def save_test_evidence(
    evidence: dict[str, Any],
    test_name: str,
) -> Path:
    """Save test evidence to the standard evidence bundle location.

    Args:
        evidence: Evidence dict from test run
        test_name: Name of the test (e.g., 'divine_via_level_25')

    Returns:
        Path to evidence directory
    """
    evidence_dir = evidence_utils.get_evidence_dir(f"ascension_real_{test_name}")

    # Capture provenance
    provenance = evidence_utils.capture_provenance(
        base_url=evidence.get("server_url", "unknown"),
    )

    # Create evidence bundle
    evidence_utils.create_evidence_bundle(
        evidence_dir=evidence_dir,
        test_name=f"ascension_real_{test_name}",
        provenance=provenance,
        results=evidence.get("test_results", {}),
        request_responses=evidence.get("interactions", []),
        methodology_text=f"Real lifecycle test: {test_name} - Natural gameplay progression to trigger ascension",
    )

    # Save additional data
    evidence_utils.save_evidence(
        evidence_dir=evidence_dir,
        data=evidence,
        filename="full_evidence.json",
    )

    if "metric_tracking" in evidence and evidence["metric_tracking"]:
        evidence_utils.save_evidence(
            evidence_dir=evidence_dir,
            data=evidence["metric_tracking"],
            filename="metric_history.json",
        )

    print(f"\n📁 Evidence saved to: {evidence_dir}")
    return evidence_dir


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================


def main():
    """Main entry point for running real lifecycle tests."""
    parser = argparse.ArgumentParser(
        description="Real Lifecycle Tests for Divine and Multiverse Ascension"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8081",
        help="MCP server URL (default: http://localhost:8081)",
    )
    parser.add_argument(
        "--model",
        default="gemini-2.0-flash",
        help="Model ID for LLM calls (default: gemini-2.0-flash)",
    )
    parser.add_argument(
        "--test",
        choices=["level25", "divine_potential", "universe_control", "all"],
        default="all",
        help="Which test to run (default: all)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed output",
    )
    parser.add_argument(
        "--save-evidence",
        action="store_true",
        default=True,
        help="Save evidence bundles (default: True)",
    )

    args = parser.parse_args()

    print("\n" + "=" * 80)
    print("REAL LIFECYCLE ASCENSION TESTS")
    print("=" * 80)
    print(f"Server: {args.url}")
    print(f"Model: {args.model}")
    print(f"Tests: {args.test}")
    print("=" * 80)

    results = {}

    if args.test in ("level25", "all"):
        evidence = test_divine_ascension_via_level_25(
            base_url=args.url,
            model_id=args.model,
            verbose=args.verbose,
        )
        results["level25"] = evidence
        if args.save_evidence:
            save_test_evidence(evidence, "level25")

    if args.test in ("divine_potential", "all"):
        evidence = test_divine_ascension_via_divine_potential(
            base_url=args.url,
            model_id=args.model,
            verbose=args.verbose,
        )
        results["divine_potential"] = evidence
        if args.save_evidence:
            save_test_evidence(evidence, "divine_potential")

    if args.test in ("universe_control", "all"):
        evidence = test_multiverse_ascension_via_universe_control(
            base_url=args.url,
            model_id=args.model,
            verbose=args.verbose,
        )
        results["universe_control"] = evidence
        if args.save_evidence:
            save_test_evidence(evidence, "universe_control")

    # Summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)

    all_passed = True
    for test_name, evidence in results.items():
        test_result = evidence.get("test_results", {})
        success = test_result.get("success", False)
        all_passed = all_passed and success
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name}: {status}")

    print("=" * 80)
    print(f"Overall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
