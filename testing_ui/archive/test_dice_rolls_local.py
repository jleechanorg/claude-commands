"""
Test dice rolls via local MCP server to verify Gemini 3 randomness fix.

This script:
1. Creates a campaign via MCP
2. Executes 5 actions that trigger dice rolls
3. Collects all d20 results
4. Analyzes distribution (should be ~10.5 avg, not 16.19)
"""

import json
import re
import requests
import statistics
from typing import Any


LOCAL_URL = "http://localhost:8081/mcp"


def mcp_call(tool_name: str, arguments: dict) -> dict[str, Any]:
    """Make an MCP JSON-RPC call to local server"""
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        },
        "id": 1
    }
    response = requests.post(LOCAL_URL, json=payload, timeout=300)
    response.raise_for_status()
    result = response.json()

    if "error" in result:
        raise Exception(f"MCP Error: {result['error']}")

    return result.get("result", {})


def create_campaign() -> dict[str, Any]:
    """Create a test campaign"""
    print("\n📝 Creating test campaign...")
    result = mcp_call("create_campaign", {
        "user_id": "test-user-123",
        "title": "Dice Roll Test Campaign",
        "setting": "A dangerous dungeon filled with goblins and traps",
        "character": "A brave adventurer with sword and shield",
        "description": "Test campaign for verifying Gemini 3 dice roll randomness"
    })
    print(f"DEBUG: Full result: {result}")
    print(f"✅ Campaign created: {result.get('campaign_id')}")
    return result


def process_action(campaign_id: str, action: str) -> dict[str, Any]:
    """Process an action that should trigger dice rolls"""
    print(f"🎲 Action: {action}")
    result = mcp_call("process_action", {
        "user_id": "test-user-123",
        "campaign_id": campaign_id,
        "user_input": action
    })
    print(f"DEBUG: Response keys: {list(result.keys()) if result else 'None'}")
    if result and 'error' in result:
        print(f"   ERROR: {result['error']}")
    if result and 'dice_rolls' in result:
        print(f"DEBUG: dice_rolls = {result['dice_rolls']}")
    return result


def extract_dice_rolls(result: dict[str, Any]) -> list[int]:
    """Extract d20 results from action result

    Handles string format like:
    - "Initiative (Goblin): 1d20+2 = 14+2 = 16" -> extracts 14
    - "Attack Roll: 1d20+5 = 8+5 = 13" -> extracts 8
    """
    dice_rolls = []

    # Check if there are dice_rolls in the result
    if "dice_rolls" in result and isinstance(result["dice_rolls"], list):
        for roll_str in result["dice_rolls"]:
            # Parse format like "1d20+2 = 14+2 = 16"
            # Extract the first number after "1d20" (the raw roll before modifiers)
            match = re.search(r'1d20[+\-]?\d*\s*=\s*(\d+)', str(roll_str))
            if match:
                dice_rolls.append(int(match.group(1)))

    return dice_rolls


def main():
    """Main test execution"""
    print("🚀 Starting Gemini 3 Dice Roll Test")
    print("=" * 60)

    # Create campaign
    campaign = create_campaign()
    campaign_id = campaign.get("campaign_id")

    if not campaign_id:
        print("❌ Failed to create campaign")
        return

    # Actions that should trigger dice rolls (5 actions for quick verification)
    actions = [
        "I attack the goblin with my sword",
        "I try to dodge the goblin's attack",
        "I attempt to persuade the goblin to flee",
        "I make a stealth check to hide",
        "I investigate the room for traps",
    ]

    all_d20_rolls = []

    print(f"\n🎲 Executing {len(actions)} dice roll actions...")
    print("=" * 60)

    for i, action in enumerate(actions, 1):
        try:
            result = process_action(campaign_id, action)
            dice_rolls = extract_dice_rolls(result)

            if dice_rolls:
                all_d20_rolls.extend(dice_rolls)
                print(f"   Roll #{i}: {dice_rolls} (avg: {statistics.mean(dice_rolls):.1f})")
            else:
                print(f"   No dice rolls in response")

        except Exception as e:
            print(f"   ⚠️ Error: {e}")

    # Analyze results
    print("\n📊 ANALYSIS")
    print("=" * 60)

    if all_d20_rolls:
        avg = statistics.mean(all_d20_rolls)
        median = statistics.median(all_d20_rolls)
        stdev = statistics.stdev(all_d20_rolls) if len(all_d20_rolls) > 1 else 0

        print(f"Total d20 rolls: {len(all_d20_rolls)}")
        print(f"Rolls: {all_d20_rolls}")
        print(f"\nAverage: {avg:.2f} (expected: ~10.5)")
        print(f"Median: {median}")
        print(f"Std Dev: {stdev:.2f}")
        print(f"Min: {min(all_d20_rolls)}")
        print(f"Max: {max(all_d20_rolls)}")

        # Distribution
        print("\nDistribution:")
        for i in range(1, 21):
            count = all_d20_rolls.count(i)
            bar = "█" * count
            print(f"  {i:2d}: {bar} ({count})")

        # Verdict
        print("\n🔍 VERDICT")
        print("=" * 60)
        if 9.0 <= avg <= 12.0:
            print(f"✅ PASS: Average {avg:.2f} is within expected range (9-12)")
            print("✅ Gemini 3 code execution is working correctly!")
        else:
            print(f"❌ FAIL: Average {avg:.2f} is outside expected range (9-12)")
            print("❌ This suggests Gemini is still inferring results instead of executing code")

    else:
        print("❌ No d20 rolls were collected!")
        print("Check if Gemini is actually executing code for dice rolls")


if __name__ == "__main__":
    main()
