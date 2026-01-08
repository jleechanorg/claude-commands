#!/usr/bin/env python3
"""RED-GREEN Test: CharacterCreationAgent with God Mode Templates

This test reproduces the production bug where CharacterCreationAgent
is skipped when users create campaigns from templates with God Mode data.

RED STATE: CharacterCreationAgent skips on Turn 1 with "let's begin"
GREEN STATE: CharacterCreationAgent activates even with God Mode template
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from testing_mcp.lib.mcp_client import MCPClient
from testing_mcp.lib.campaign_utils import create_campaign_with_god_mode, process_action
from testing_mcp.lib.production_templates import MY_EPIC_ADVENTURE_GOD_MODE


def test_red_state():
    """Test that reproduces the production bug (should FAIL in RED state)."""
    print("\n" + "=" * 70)
    print("🔴 RED STATE TEST: God Mode Template + Completion Phrase on Turn 1")
    print("=" * 70)

    client = MCPClient("http://localhost:8080")
    user_id = "test-red-green-user"

    # Create campaign exactly like production template
    print("\n📝 Creating campaign with God Mode template (like 'My Epic Adventure')...")
    campaign_id = create_campaign_with_god_mode(
        client,
        user_id,
        title="RED State Test - My Epic Adventure",
        god_mode_data=MY_EPIC_ADVENTURE_GOD_MODE,
    )
    print(f"✅ Campaign created: {campaign_id}")

    # User says "Let's begin!" on Turn 1 (completion phrase that triggers bug)
    print("\n📝 User says: \"Let's begin the adventure!\" (completion phrase)")
    result = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input="Let's begin the adventure!",
        mode="character",
    )

    # Check which agent activated
    debug_info = result.get("debug_info", {})
    system_files = debug_info.get("system_instruction_files", [])

    char_creation_active = any("character_creation" in f for f in system_files)

    print(f"\n📋 System Files: {[f.split('/')[-1] for f in system_files]}")
    print(f"🎭 CharacterCreationAgent active: {char_creation_active}")

    if char_creation_active:
        print(f"\n❌ UNEXPECTED: CharacterCreationAgent activated")
        print(f"   This means the bug is NOT present (already fixed)")
        return False
    else:
        print(f"\n✅ RED STATE CONFIRMED: CharacterCreationAgent SKIPPED!")
        print(f"   StoryMode activated instead - production bug reproduced")
        return True


def test_green_state():
    """Test after fix is applied (should PASS in GREEN state)."""
    print("\n" + "=" * 70)
    print("🟢 GREEN STATE TEST: God Mode Template + Fix Applied")
    print("=" * 70)

    client = MCPClient("http://localhost:8080")
    user_id = "test-red-green-user-green"

    # Create campaign exactly like production template
    print("\n📝 Creating campaign with God Mode template...")
    campaign_id = create_campaign_with_god_mode(
        client,
        user_id,
        title="GREEN State Test - My Epic Adventure",
        god_mode_data=MY_EPIC_ADVENTURE_GOD_MODE,
    )
    print(f"✅ Campaign created: {campaign_id}")

    # User says "Let's begin!" on Turn 1 (should NOT skip CharacterCreationAgent)
    print("\n📝 User says: \"Let's begin the adventure!\"")
    result = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input="Let's begin the adventure!",
        mode="character",
    )

    # Check which agent activated
    debug_info = result.get("debug_info", {})
    system_files = debug_info.get("system_instruction_files", [])

    char_creation_active = any("character_creation" in f for f in system_files)

    print(f"\n📋 System Files: {[f.split('/')[-1] for f in system_files]}")
    print(f"🎭 CharacterCreationAgent active: {char_creation_active}")

    if char_creation_active:
        print(f"\n✅ GREEN STATE CONFIRMED: CharacterCreationAgent ACTIVATED!")
        print(f"   Bug is FIXED - agent activates even with completion phrase")
        return True
    else:
        print(f"\n❌ FAIL: CharacterCreationAgent still skipped")
        print(f"   Fix did not work")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "green":
        # GREEN state test (after fix)
        success = test_green_state()
        sys.exit(0 if success else 1)
    else:
        # RED state test (before fix)
        success = test_red_state()
        sys.exit(0 if success else 1)
