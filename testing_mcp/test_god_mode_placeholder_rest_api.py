#!/usr/bin/env python3
"""Regression Test: God Mode Placeholder Bug via REST API

Tests that Scene 1 doesn't show placeholder text when creating campaigns.
Uses REST API calls (like real users) instead of MCP protocol.

Run (local server already running):
    python testing_mcp/test_god_mode_placeholder_rest_api.py --base-url http://127.0.0.1:8081

Run (start local server automatically):
    python testing_mcp/test_god_mode_placeholder_rest_api.py --start-local
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

import requests

sys.path.insert(0, str(Path(__file__).parent))

from lib import evidence_utils
from lib.server_utils import (
    LocalServer,
    pick_free_port,
    start_local_mcp_server,
)

WORK_NAME = "god_mode_placeholder_rest_api"
API_CALLS: list[dict] = []


def log(msg: str) -> None:
    """Log with timestamp."""
    ts = datetime.now(timezone.utc).isoformat()
    print(f"[{ts}] {msg}")
    sys.stdout.flush()


def api_call(base_url: str, method: str, endpoint: str, data: dict = None, headers: dict = None) -> dict:
    """Make REST API call (like real users do)."""
    url = f"{base_url}{endpoint}"
    call_timestamp = datetime.now(timezone.utc).isoformat()
    log(f"🔵 REST API CALL: {method} {endpoint}")

    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=120)
        elif method == "POST":
            response = requests.post(
                url,
                json=data,
                headers=headers or {"Content-Type": "application/json"},
                timeout=120,
            )
        else:
            raise ValueError(f"Unsupported method: {method}")

        response.raise_for_status()
        result = response.json()

        API_CALLS.append({
            "timestamp": call_timestamp,
            "method": method,
            "endpoint": endpoint,
            "request_data": data,
            "response": result,
            "status_code": response.status_code,
        })
        return result

    except requests.exceptions.HTTPError as e:
        error_text = e.response.text if e.response else str(e)
        log(f"❌ HTTP ERROR {e.response.status_code}: {error_text}")
        API_CALLS.append({
            "timestamp": call_timestamp,
            "method": method,
            "endpoint": endpoint,
            "request_data": data,
            "error": str(e),
            "status_code": e.response.status_code if e.response else None,
        })
        raise
    except Exception as e:
        log(f"❌ ERROR: {e}")
        API_CALLS.append({
            "timestamp": call_timestamp,
            "method": method,
            "endpoint": endpoint,
            "request_data": data,
            "error": str(e),
        })
        raise


def test_god_mode_placeholder_via_rest_api(base_url: str, user_id: str) -> bool:
    """Test that Scene 1 doesn't show placeholder text.

    This is a regression test for a bug where Scene 1 showed:
    "[Character Creation Mode - Story begins after character is complete]"
    instead of proper narrative.
    """
    log("=" * 80)
    log("TEST: God Mode Placeholder Bug via REST API")
    log("=" * 80)
    log(f"Base URL: {base_url}")
    log(f"User ID: {user_id}")

    # Create campaign with frontend format (separate fields)
    character = "A stealthy monk trained in martial arts and inner discipline"
    setting = "The haunted moors of Barovia, trapped in eternal mist and ruled by dark powers"

    log("Step 1: Creating campaign via POST /api/campaigns (frontend format)")
    create_data = {
        "title": "REST API Placeholder Test",
        "character": character,
        "setting": setting,
        "description": "",
        "selectedPrompts": [],
        "use_default_world": False,
    }

    # Set up authentication headers for testing
    auth_headers = {
        "X-Test-Bypass-Auth": "true",
        "X-Test-User-ID": user_id,
    }

    create_response = api_call(base_url, "POST", "/api/campaigns", data=create_data, headers=auth_headers)

    campaign_id = create_response.get("campaign_id")
    if not campaign_id:
        raise RuntimeError(f"Campaign creation failed: {create_response}")
    log(f"✅ Campaign created: {campaign_id}")

    # Get campaign state
    log("Step 2: Getting campaign state via GET /api/campaigns/{id}")
    state_response = api_call(base_url, "GET", f"/api/campaigns/{campaign_id}", headers=auth_headers)

    # Extract Scene 1 from campaign state
    story_entries = state_response.get("story", [])
    log(f"Found {len(story_entries)} story entries")

    # Find Scene 1 (first agent/gemini narrative entry)
    scene1_text = ""
    for entry in story_entries:
        if isinstance(entry, dict):
            actor = entry.get("actor", "")
            text = entry.get("text", "")
            user_scene_number = entry.get("user_scene_number")

            if actor in ("gemini", "agent", "system") and text:
                if user_scene_number == 1 or not scene1_text:
                    scene1_text = text
                    if user_scene_number == 1:
                        break
        elif isinstance(entry, str) and not scene1_text:
            scene1_text = entry
            break

    # Fallback: check campaign metadata
    if not scene1_text:
        scene1_text = state_response.get("opening_story", "") or state_response.get("initial_story", "") or ""

    log(f"Scene 1 length: {len(scene1_text)} chars")
    log(f"Scene 1 preview: {scene1_text[:300]}...")

    # Check for placeholder bug
    placeholder_text = "[Character Creation Mode - Story begins after character is complete]"
    has_placeholder = placeholder_text in scene1_text

    if has_placeholder:
        log(f"❌ BUG: Scene 1 contains placeholder text")
        return False

    # Check for substantial content
    is_substantial = len(scene1_text) > 100

    if not is_substantial:
        log(f"⚠️ WARNING: Scene 1 is too short ({len(scene1_text)} chars)")

    if not has_placeholder and is_substantial:
        log("✅ TEST PASSED: No placeholder, proper content in Scene 1")
        return True
    else:
        log("❌ TEST FAILED")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test God Mode Placeholder Bug via REST API")
    parser.add_argument("--base-url", default=None, help="Server base URL")
    parser.add_argument("--start-local", action="store_true", help="Start local server automatically")
    parser.add_argument("--port", type=int, default=0, help="Port for --start-local (0 = random)")
    parser.add_argument("--user-id", default=None, help="Test user ID")
    args = parser.parse_args()

    local_server: LocalServer | None = None
    base_url: str
    user_id = args.user_id or f"rest-api-test-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Determine server URL
    if args.start_local:
        port = args.port or pick_free_port()
        print(f"\n🚀 Starting local MCP server on port {port}...")
        local_server = start_local_mcp_server(port)
        base_url = local_server.base_url
        time.sleep(3)
        print(f"   Local server started on {base_url}")
    elif args.base_url:
        base_url = args.base_url
    else:
        print("❌ Error: Specify --base-url or --start-local")
        sys.exit(1)

    # Set up evidence directory
    evidence_dir = evidence_utils.get_evidence_dir(WORK_NAME) / datetime.now().strftime("%Y%m%d_%H%M%S")
    evidence_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Capture provenance
        log("Capturing git provenance...")
        provenance = evidence_utils.capture_provenance(base_url)
        log(f"   Git HEAD: {provenance.get('git_sha', 'N/A')[:12]}")

        # Run test
        test_passed = test_god_mode_placeholder_via_rest_api(base_url, user_id)

        # Save evidence bundle
        evidence_utils.create_evidence_bundle(
            evidence_dir,
            test_name=WORK_NAME,
            provenance=provenance,
            results={"test_passed": test_passed},
            request_responses=API_CALLS,
        )
        log(f"✅ Evidence saved to: {evidence_dir}")

        # Summary
        print("\n" + "=" * 70)
        print("Summary")
        print("=" * 70)
        if test_passed:
            print("✅ TEST PASSED")
            sys.exit(0)
        else:
            print("❌ TEST FAILED")
            sys.exit(1)

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
