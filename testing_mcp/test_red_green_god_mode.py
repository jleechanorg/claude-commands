#!/usr/bin/env python3
"""RED-GREEN Test: CharacterCreationAgent with God Mode Templates

This test verifies that CharacterCreationAgent properly activates when users create
campaigns from templates with God Mode data. Originally designed as a RED-GREEN test
to reproduce and verify fix for a bug where CharacterCreationAgent was skipped.

Since the bug is fixed, this test now verifies the GREEN state (correct behavior).

Run (local MCP already running):
    python testing_mcp/test_red_green_god_mode.py --server-url http://127.0.0.1:8001

Run (start local MCP automatically):
    python testing_mcp/test_red_green_god_mode.py --start-local
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib import MCPClient
from lib.server_utils import (
    LocalServer,
    pick_free_port,
    start_local_mcp_server,
)
from lib.campaign_utils import create_campaign_with_god_mode, process_action
from lib.production_templates import MY_EPIC_ADVENTURE_GOD_MODE
from lib.evidence_utils import capture_provenance


def test_green_state(client: MCPClient) -> bool:
    """Test that CharacterCreationAgent activates with God Mode templates (GREEN state).

    This verifies the fix is working - CharacterCreationAgent should activate
    when users create campaigns from templates with God Mode data.
    """
    print("\n" + "=" * 70)
    print("🟢 GREEN STATE TEST: God Mode Template + Fix Applied")
    print("=" * 70)

    user_id = "test-red-green-user-green"

    # Create campaign exactly like production template
    print("\n📝 Creating campaign with God Mode template (like 'My Epic Adventure')...")
    try:
        campaign_id = create_campaign_with_god_mode(
            client,
            user_id,
            title="GREEN State Test - My Epic Adventure",
            god_mode_data=MY_EPIC_ADVENTURE_GOD_MODE,
        )
    except Exception as e:
        print(f"\n❌ FATAL: Campaign creation failed: {e}")
        return False
    print(f"✅ Campaign created: {campaign_id}")

    # User wants to create their character on Turn 1 (should activate CharacterCreationAgent)
    print("\n📝 User says: \"Let's create my character!\"")
    try:
        result = process_action(
            client,
            user_id=user_id,
            campaign_id=campaign_id,
            user_input="Let's create my character!",
            mode="character",
        )
    except Exception as e:
        print(f"\n❌ FATAL: Process action failed: {e}")
        return False

    # Check which agent activated
    debug_info = result.get("debug_info", {})
    system_files = debug_info.get("system_instruction_files", [])

    char_creation_active = any("character_creation" in f for f in system_files)

    print(f"\n📋 System Files: {[f.split('/')[-1] for f in system_files]}")
    print(f"🎭 CharacterCreationAgent active: {char_creation_active}")

    if char_creation_active:
        print("\n✅ GREEN STATE CONFIRMED: CharacterCreationAgent ACTIVATED!")
        print("   Bug is FIXED - agent activates with God Mode template")
        return True
    else:
        print("\n❌ FAIL: CharacterCreationAgent still skipped")
        print("   Fix did not work - bug regression detected!")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="RED-GREEN test for CharacterCreationAgent with God Mode templates"
    )
    parser.add_argument(
        "--server-url",
        default=None,
        help="MCP server URL (default: start local server)",
    )
    parser.add_argument(
        "--start-local",
        action="store_true",
        help="Start a local MCP server automatically",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=0,
        help="Port for --start-local (0 = random free port)",
    )
    args = parser.parse_args()

    local_server: LocalServer | None = None
    base_url: str

    # Determine server URL
    if args.start_local:
        port = args.port or pick_free_port()
        print(f"\n🚀 Starting local MCP server on port {port}...")
        local_server = start_local_mcp_server(port)
        base_url = local_server.base_url
        # Wait for server to be ready
        time.sleep(3)
        print(f"   Local server started on {base_url}")
    elif args.server_url:
        base_url = args.server_url
    else:
        print("❌ Error: Specify --server-url or --start-local")
        sys.exit(1)

    try:
        # Capture provenance
        print("\n📊 Capturing provenance...")
        provenance = capture_provenance(base_url)
        print(f"   Git HEAD: {provenance.get('git_sha', 'N/A')[:12]}")
        print(f"   Branch: {provenance.get('git_branch', 'N/A')}")

        # Create client and check health
        print(f"\n📡 Connecting to {base_url}")
        client = MCPClient(base_url)
        print("   Waiting for server to be healthy...")
        try:
            client.wait_healthy(timeout_s=30.0)
            print("   ✅ Server is healthy")
        except TimeoutError:
            print("   ❌ Server failed to become healthy")
            sys.exit(1)

        # Run test (GREEN state only - bug is fixed)
        success = test_green_state(client)

        # Summary
        print("\n" + "=" * 70)
        print("Summary")
        print("=" * 70)
        if success:
            print("✅ TEST PASSED: CharacterCreationAgent activates correctly")
            sys.exit(0)
        else:
            print("❌ TEST FAILED: CharacterCreationAgent regression detected")
            sys.exit(1)

    finally:
        if local_server:
            print("\n🛑 Stopping local server...")
            local_server.stop()


if __name__ == "__main__":
    main()
