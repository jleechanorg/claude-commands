#!/usr/bin/env python3
"""Real API test for inventory preservation safeguards.

Tests that character inventory and companion equipment are never lost,
compressed, or overwritten during game state updates.

Run against GCP preview server:
    cd testing_mcp
    python test_inventory_preservation_real_api.py --server-url https://mvp-site-app-s10-i6xf2p72ka-uc.a.run.app

Run against local server:
    cd testing_mcp
    python test_inventory_preservation_real_api.py --server-url http://127.0.0.1:8001
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from mcp_client import MCPClient
from lib.campaign_utils import create_campaign, process_action, get_campaign_state

EVIDENCE_DIR = Path(__file__).parent / "evidence" / "inventory_preservation"


def save_evidence(name: str, data: Any) -> None:
    """Save test evidence to file."""
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = EVIDENCE_DIR / f"{timestamp}_{name}.json"
    try:
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, default=str)
        print(f"  📁 Evidence saved: {filepath}")
    except Exception as exc:  # noqa: BLE001 - best-effort evidence save
        print(f"  ⚠️  Failed to save evidence to {filepath}: {exc}")


def seed_inventory_state(
    client: MCPClient, *, user_id: str, campaign_id: str
) -> dict[str, Any]:
    """Seed the campaign with specific inventory items for testing.

    Creates a character with known inventory items and a companion NPC
    with specific equipment.

    Uses GOD_MODE_UPDATE_STATE via process_action (same pattern as other tests).
    """
    seeded_pc = {
        "string_id": "pc_test_001",
        "name": "TestHero",
        "level": 3,
        "class": "Fighter",
        "hp_current": 28,
        "hp_max": 28,
        "attributes": {
            "strength": 16,
            "dexterity": 14,
            "constitution": 14,
            "intelligence": 10,
            "wisdom": 12,
            "charisma": 10,
        },
        "proficiency_bonus": 2,
        "armor_class": 16,
        # Critical: Specific inventory items to track
        "inventory": {
            "gold": 150,
            "items": [
                {"name": "Sunstone Amulet", "magical": True, "value": 500},
                {"name": "Health Potion", "uses": 2},
                {"name": "Rope (50 ft)", "weight": 10},
            ],
        },
        "equipment": [
            {"name": "Longsword +1", "damage": "1d8+1", "magical": True},
            {"name": "Chain Mail", "ac_bonus": 6},
            {"name": "Shield", "ac_bonus": 2},
        ],
    }

    seeded_companion = {
        "string_id": "npc_companion_001",
        "name": "Elara",
        "role": "companion",
        "relationship": "companion",
        "level": 2,
        "class": "Ranger",
        "hp_current": 18,
        "hp_max": 18,
        "is_important": True,
        # Critical: Companion equipment to track
        "equipment": [
            {"name": "Elven Bow", "damage": "1d8", "magical": True},
            {"name": "Leather Armor", "ac_bonus": 2},
            {"name": "Quiver of Arrows", "quantity": 20},
        ],
        "inventory": ["Healing Herbs", "Trail Rations"],
    }

    state_changes = {
        "player_character_data": seeded_pc,
        "npc_data": {"Elara": seeded_companion},
    }

    # Use GOD_MODE_UPDATE_STATE via process_action (same pattern as ensure_game_state_seed)
    god_mode_payload = f"GOD_MODE_UPDATE_STATE:{json.dumps(state_changes)}"
    result = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=god_mode_payload,
    )

    if result.get("error"):
        raise RuntimeError(f"GOD_MODE_UPDATE_STATE failed: {result['error']}")

    return {"player_character_data": seeded_pc, "npc_data": {"Elara": seeded_companion}}


def verify_inventory_preserved(
    current_state: dict[str, Any],
    expected_items: list[str],
) -> tuple[bool, list[str]]:
    """Verify that expected inventory items are still present.

    Returns (success, list of missing items).
    """
    pc_data = current_state.get("player_character_data", {})
    inventory = pc_data.get("inventory", {})
    equipment = pc_data.get("equipment", [])

    # Flatten all item names
    found_items = set()

    # Check inventory items
    if isinstance(inventory, dict):
        items_list = inventory.get("items", [])
        if isinstance(items_list, list):
            for item in items_list:
                if isinstance(item, dict):
                    name = item.get("name", "")
                    if name:
                        found_items.add(name)
                elif isinstance(item, str):
                    if item:
                        found_items.add(item)
    elif isinstance(inventory, list):
        for item in inventory:
            if isinstance(item, dict):
                name = item.get("name", "")
                if name:
                    found_items.add(name)
            elif isinstance(item, str):
                if item:
                    found_items.add(item)

    # Check equipment
    if isinstance(equipment, list):
        for item in equipment:
            if isinstance(item, dict):
                name = item.get("name", "")
                if name:
                    found_items.add(name)
            elif isinstance(item, str):
                if item:
                    found_items.add(item)

    missing = [item for item in expected_items if item not in found_items]
    return len(missing) == 0, missing


def verify_companion_equipment_preserved(
    current_state: dict[str, Any],
    companion_name: str,
    expected_equipment: list[str],
) -> tuple[bool, list[str]]:
    """Verify companion equipment is preserved.

    Returns (success, list of missing equipment).
    """
    npc_data = current_state.get("npc_data", {})
    companion = npc_data.get(companion_name, {})

    found_items = set()

    # Check equipment
    equipment = companion.get("equipment", [])
    if isinstance(equipment, list):
        for item in equipment:
            if isinstance(item, dict):
                name = item.get("name", "")
                if name:
                    found_items.add(name)
            elif isinstance(item, str):
                if item:
                    found_items.add(item)

    # Check inventory
    inventory = companion.get("inventory", [])
    if isinstance(inventory, list):
        for item in inventory:
            if isinstance(item, dict):
                name = item.get("name", "")
                if name:
                    found_items.add(name)
            elif isinstance(item, str):
                if item:
                    found_items.add(item)

    missing = [item for item in expected_equipment if item not in found_items]
    return len(missing) == 0, missing


def run_inventory_preservation_test(client: MCPClient, user_id: str) -> dict[str, Any]:
    """Run the main inventory preservation test.

    Tests:
    1. Create campaign and seed inventory
    2. Perform multiple actions that trigger state updates
    3. Verify inventory is preserved after each action
    4. Verify companion equipment is preserved
    """
    results = {
        "passed": 0,
        "failed": 0,
        "tests": [],
    }

    print("\n" + "=" * 60)
    print("🎒 INVENTORY PRESERVATION TEST")
    print("=" * 60)

    # Step 1: Create campaign
    print("\n📋 Step 1: Creating test campaign...")
    try:
        campaign_id = create_campaign(
            client,
            user_id,
            title="Inventory Preservation Test",
            character="TestHero the Fighter (STR 16, DEX 14)",
            setting="A merchant's shop in Waterdeep",
            description="Testing inventory preservation safeguards",
        )
        print(f"  ✅ Campaign created: {campaign_id}")
    except Exception as e:
        print(f"  ❌ Campaign creation failed: {e}")
        results["failed"] += 1
        results["tests"].append({
            "name": "Campaign Creation",
            "passed": False,
            "error": str(e),
        })
        return results

    # Step 2: Seed inventory
    print("\n📦 Step 2: Seeding inventory with test items...")
    try:
        seeded_data = seed_inventory_state(client, user_id=user_id, campaign_id=campaign_id)
        print("  ✅ Inventory seeded successfully")

        # Define expected items to track
        expected_pc_items = ["Sunstone Amulet", "Health Potion", "Rope (50 ft)",
                            "Longsword +1", "Chain Mail", "Shield"]
        expected_companion_items = ["Elven Bow", "Leather Armor", "Quiver of Arrows",
                                    "Healing Herbs", "Trail Rations"]
    except Exception as e:
        print(f"  ❌ Inventory seeding failed: {e}")
        results["failed"] += 1
        results["tests"].append({
            "name": "Inventory Seeding",
            "passed": False,
            "error": str(e),
        })
        return results

    # Step 3: Verify initial state
    print("\n🔍 Step 3: Verifying initial inventory state...")
    try:
        state_payload = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
        game_state = state_payload.get("game_state", {})

        pc_ok, pc_missing = verify_inventory_preserved(game_state, expected_pc_items)
        companion_ok, companion_missing = verify_companion_equipment_preserved(
            game_state, "Elara", expected_companion_items
        )

        if pc_ok and companion_ok:
            print("  ✅ Initial inventory verified - all items present")
            results["passed"] += 1
            results["tests"].append({"name": "Initial Inventory Verification", "passed": True})
        else:
            print(f"  ❌ Initial inventory incomplete!")
            if pc_missing:
                print(f"    Missing PC items: {pc_missing}")
            if companion_missing:
                print(f"    Missing companion items: {companion_missing}")
            results["failed"] += 1
            results["tests"].append({
                "name": "Initial Inventory Verification",
                "passed": False,
                "pc_missing": pc_missing,
                "companion_missing": companion_missing,
            })

        save_evidence("01_initial_state", game_state)
    except Exception as e:
        print(f"  ❌ State verification failed: {e}")
        results["failed"] += 1
        results["tests"].append({
            "name": "Initial State Verification",
            "passed": False,
            "error": str(e),
        })

    # Step 4: Perform actions that trigger state updates
    test_actions = [
        {
            "name": "Combat Action",
            "input": "I draw my Longsword +1 and attack the training dummy. Elara practices with her Elven Bow.",
        },
        {
            "name": "Exploration Action",
            "input": "I check my backpack to make sure I have the Sunstone Amulet and all my gear. Elara does the same.",
        },
        {
            "name": "Rest Action",
            "input": "We take a short rest. I drink one of my Health Potions to recover.",
        },
    ]

    for i, action in enumerate(test_actions, start=4):
        print(f"\n⚔️  Step {i}: Testing {action['name']}...")
        try:
            response = process_action(
                client,
                user_id=user_id,
                campaign_id=campaign_id,
                user_input=action["input"],
            )

            narrative = response.get("narrative", response.get("text", ""))
            print(f"  📜 Response received ({len(narrative)} chars)")

            # Verify inventory after action
            state_payload = get_campaign_state(client, user_id=user_id, campaign_id=campaign_id)
            game_state = state_payload.get("game_state", {})

            pc_ok, pc_missing = verify_inventory_preserved(game_state, expected_pc_items)
            companion_ok, companion_missing = verify_companion_equipment_preserved(
                game_state, "Elara", expected_companion_items
            )

            if pc_ok and companion_ok:
                print(f"  ✅ Inventory preserved after {action['name']}")
                results["passed"] += 1
                results["tests"].append({
                    "name": f"Inventory After {action['name']}",
                    "passed": True,
                })
            else:
                print(f"  ❌ Inventory lost after {action['name']}!")
                if pc_missing:
                    print(f"    Missing PC items: {pc_missing}")
                if companion_missing:
                    print(f"    Missing companion items: {companion_missing}")
                results["failed"] += 1
                results["tests"].append({
                    "name": f"Inventory After {action['name']}",
                    "passed": False,
                    "pc_missing": pc_missing,
                    "companion_missing": companion_missing,
                })

            save_evidence(f"0{i}_{action['name'].lower().replace(' ', '_')}", {
                "action": action,
                "response_length": len(narrative),
                "game_state": game_state,
            })

        except Exception as e:
            print(f"  ❌ Action failed: {e}")
            results["failed"] += 1
            results["tests"].append({
                "name": f"Action: {action['name']}",
                "passed": False,
                "error": str(e),
            })

    # Final summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"  Passed: {results['passed']}")
    print(f"  Failed: {results['failed']}")
    print(f"  Total:  {results['passed'] + results['failed']}")

    if results["failed"] == 0:
        print("\n🎉 ALL TESTS PASSED - Inventory preservation working correctly!")
    else:
        print(f"\n⚠️  {results['failed']} test(s) failed - check evidence files")

    save_evidence("final_results", results)

    return results


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Test inventory preservation against MCP server"
    )
    parser.add_argument(
        "--server-url",
        default="https://mvp-site-app-s10-i6xf2p72ka-uc.a.run.app",
        help="MCP server URL (default: GCP preview)",
    )
    parser.add_argument(
        "--user-id",
        default=None,
        help="User ID for testing (default: auto-generated)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=120.0,
        help="Request timeout in seconds (default: 120)",
    )
    args = parser.parse_args()

    user_id = args.user_id or f"test_inventory_{uuid.uuid4().hex[:8]}"

    print("=" * 60)
    print("🔬 INVENTORY PRESERVATION REAL API TEST")
    print("=" * 60)
    print(f"  Server: {args.server_url}")
    print(f"  User:   {user_id}")
    print(f"  Time:   {datetime.now().isoformat()}")

    client = MCPClient(args.server_url, timeout_s=args.timeout)

    print("\n🏥 Checking server health...")
    try:
        client.wait_healthy(timeout_s=args.timeout)
        print("  ✅ Server is healthy")
    except RuntimeError as e:
        print(f"  ❌ Server health check failed: {e}")
        return 1

    results = run_inventory_preservation_test(client, user_id)

    return 0 if results["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
