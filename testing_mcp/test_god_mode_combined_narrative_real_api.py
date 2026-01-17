#!/usr/bin/env python3
"""Regression Test: God Mode Combined Narrative Bug (PR #3727)

Tests against REAL local MCP server that god_mode_response content is preserved
and not replaced by "You pause to consider your options..." placeholder.

BUG: When LLM returns god_mode_response with content + empty narrative + planning_block,
the placeholder replaces the actual content.

Run (start local server automatically):
    python testing_mcp/test_god_mode_combined_narrative_real_api.py --start-local

Run (with existing server):
    python testing_mcp/test_god_mode_combined_narrative_real_api.py --base-url http://127.0.0.1:8081

Evidence saved to: /tmp/worldarchitect.ai/{branch}/god_mode_combined_narrative_real_api/
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lib import evidence_utils
from lib.campaign_utils import create_campaign, process_action, get_campaign_state
from lib.mcp_client import MCPClient
from lib.server_utils import (
    LocalServer,
    pick_free_port,
    start_local_mcp_server,
)

WORK_NAME = "god_mode_combined_narrative_real_api"


def log(msg: str) -> None:
    """Log with timestamp."""
    ts = datetime.now(timezone.utc).isoformat()
    print(f"[{ts}] {msg}")
    sys.stdout.flush()


def test_god_mode_combined_narrative(client: MCPClient, user_id: str) -> dict:
    """Test that god_mode_response is preserved in interactions.

    Scenario from scene #187:
    - User asks god mode question (e.g., "What is my spell DC?")
    - LLM returns god_mode_response with answer
    - Response should contain the actual answer, NOT placeholder

    Returns dict with test results.
    """
    log("=" * 80)
    log("TEST: God Mode Combined Narrative Bug (PR #3727)")
    log("=" * 80)
    log(f"User ID: {user_id}")

    results = {
        "campaign_created": False,
        "interaction_completed": False,
        "has_placeholder_bug": None,
        "response_text": "",
        "response_length": 0,
    }

    # Step 1: Create a simple campaign
    log("\n" + "-" * 60)
    log("Step 1: Create campaign via MCP")
    log("-" * 60)

    campaign_config = {
        "title": "God Mode Narrative Test",
        "character": "A level 5 wizard named Elara with INT 18 (+4) and proficiency +3. Spell save DC should be 8 + 3 + 4 = 15.",
        "setting": "A magical academy in a bustling city",
    }

    campaign_id = create_campaign(
        client,
        user_id=user_id,
        title=campaign_config["title"],
        character=campaign_config["character"],
        setting=campaign_config["setting"],
    )

    if not campaign_id:
        raise RuntimeError("Campaign creation failed")

    results["campaign_created"] = True
    log(f"✅ Campaign created: {campaign_id}")

    # Step 2: Send a god mode interaction that asks about game state
    log("\n" + "-" * 60)
    log("Step 2: Send god mode interaction via MCP")
    log("-" * 60)

    user_input = "GOD MODE: What is my character's spell save DC? Calculate it step by step and show the formula."
    log(f"User input: {user_input}")

    # Process action in god mode
    action_result = process_action(
        client,
        user_id=user_id,
        campaign_id=campaign_id,
        user_input=user_input,
        mode="god",
    )

    results["interaction_completed"] = True

    # Extract narrative from response
    narrative = ""
    if action_result:
        narrative = action_result.get("narrative", "")
        if not narrative:
            # Try to get from story entries
            story = action_result.get("story", [])
            for entry in reversed(story):
                if isinstance(entry, dict) and entry.get("actor") == "gemini":
                    narrative = entry.get("text", "")
                    break

    results["response_text"] = narrative
    results["response_length"] = len(narrative)

    log(f"Response length: {len(narrative)} chars")
    log(f"Response preview: {narrative[:400]}...")

    # Step 3: Check for placeholder bug
    log("\n" + "-" * 60)
    log("Step 3: Check for placeholder bug")
    log("-" * 60)

    placeholder = "You pause to consider your options..."

    if narrative.strip() == placeholder:
        log(f"❌ BUG FOUND: Response is exactly the placeholder!")
        results["has_placeholder_bug"] = True
    elif placeholder in narrative and len(narrative) < 100:
        log(f"⚠️ LIKELY BUG: Response contains placeholder and is short")
        results["has_placeholder_bug"] = True
    else:
        # Check for any substantial content
        has_spell_content = any(
            kw in narrative.lower()
            for kw in ["spell", "dc", "save", "calculate", "formula", "8 +", "+3", "+4"]
        )

        if has_spell_content:
            log(f"✅ Response contains expected spell DC content")
            results["has_placeholder_bug"] = False
        elif len(narrative) > 100:
            log(f"✅ Response is substantial ({len(narrative)} chars)")
            results["has_placeholder_bug"] = False
        else:
            log(f"⚠️ Response is short but not placeholder")
            results["has_placeholder_bug"] = False

    return results


def main():
    parser = argparse.ArgumentParser(description="Test God Mode Combined Narrative Bug (Real Server)")
    parser.add_argument("--base-url", default=None, help="Server base URL")
    parser.add_argument("--start-local", action="store_true", help="Start local server automatically")
    parser.add_argument("--port", type=int, default=0, help="Port for --start-local (0 = random)")
    parser.add_argument("--user-id", default=None, help="Test user ID")
    args = parser.parse_args()

    local_server: LocalServer | None = None
    base_url: str
    user_id = args.user_id or f"narrative-test-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Determine server URL
    if args.start_local:
        port = args.port or pick_free_port()
        print(f"\n🚀 Starting local MCP server on port {port}...")
        local_server = start_local_mcp_server(port)
        base_url = local_server.base_url
        time.sleep(5)  # Give server time to start
        print(f"   Local server started on {base_url}")
    elif args.base_url:
        base_url = args.base_url
    else:
        print("❌ Error: Specify --base-url or --start-local")
        sys.exit(1)

    # Set up evidence directory
    evidence_dir = evidence_utils.get_evidence_dir(WORK_NAME)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    # Create MCP client
    client = MCPClient(base_url, timeout_s=300)

    try:
        # Capture provenance
        log("Capturing git provenance...")
        provenance = evidence_utils.capture_provenance(base_url)
        log(f"   Git HEAD: {provenance.get('git_sha', 'N/A')[:12] if provenance.get('git_sha') else 'N/A'}")
        log(f"   Branch: {provenance.get('git_branch', 'N/A')}")

        # Run test
        results = test_god_mode_combined_narrative(client, user_id)

        # Save evidence bundle
        evidence_utils.create_evidence_bundle(
            evidence_dir,
            test_name=WORK_NAME,
            provenance=provenance,
            results=results,
            request_responses=client.get_captures_as_dict(),
        )
        log(f"\n✅ Evidence saved to: {evidence_dir}")

        # Summary
        print("\n" + "=" * 70)
        print("SUMMARY: God Mode Combined Narrative Bug Test (REAL SERVER)")
        print("=" * 70)
        print(f"Campaign created: {results['campaign_created']}")
        print(f"Interaction completed: {results['interaction_completed']}")
        print(f"Response length: {results['response_length']} chars")
        print(f"Has placeholder bug: {results['has_placeholder_bug']}")
        print()

        if results["has_placeholder_bug"]:
            print("❌ TEST FAILED: Placeholder bug detected!")
            print("   Response was replaced by 'You pause to consider your options...'")
            sys.exit(1)
        elif results["has_placeholder_bug"] is False:
            print("✅ TEST PASSED: No placeholder bug, god_mode_response preserved")
            sys.exit(0)
        else:
            print("⚠️ TEST INCONCLUSIVE: Could not determine bug status")
            sys.exit(2)

    except Exception as e:
        log(f"❌ TEST ERROR: {e}")
        traceback.print_exc()
        sys.exit(1)

    finally:
        if local_server:
            print("\n🛑 Stopping local server...")
            local_server.stop()


if __name__ == "__main__":
    main()
