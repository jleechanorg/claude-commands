#!/usr/bin/env python3
"""
Test God Mode Placeholder Bug using REST API (Real User Flow)

This test reproduces the bug where Scene 1 shows placeholder text:
"[Character Creation Mode - Story begins after character is complete]"

Instead of proper character creation narrative.

Uses REST API calls (like real users) instead of MCP protocol:
- POST /api/campaigns (create campaign)
- GET /api/campaigns/{id} (get campaign state)
- POST /api/campaigns/{id}/interaction (process action)

This matches the REAL USER FLOW exactly.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from testing_mcp.lib import evidence_utils
from testing_mcp.lib.production_templates import MY_EPIC_ADVENTURE_GOD_MODE
from testing_mcp.lib.server_utils import DEFAULT_MCP_BASE_URL, pick_free_port

# Configuration
BASE_URL = os.getenv("BASE_URL") or DEFAULT_MCP_BASE_URL
USER_ID = f"rest-api-test-{datetime.now().strftime('%Y%m%d%H%M%S')}"
WORK_NAME = "god_mode_placeholder_rest_api"

# Evidence directory
EVIDENCE_DIR = evidence_utils.get_evidence_dir(WORK_NAME) / datetime.now().strftime("%Y%m%d_%H%M%S")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

# Track API calls for evidence
API_CALLS: list[dict] = []


def log(msg: str) -> None:
    """Log with timestamp."""
    ts = datetime.now(timezone.utc).isoformat()
    print(f"[{ts}] {msg}")
    sys.stdout.flush()


def api_call(method: str, endpoint: str, data: dict = None, headers: dict = None) -> dict:
    """
    Make REST API call (like real users do).
    
    Args:
        method: HTTP method (GET, POST)
        endpoint: API endpoint (e.g., "/api/campaigns")
        data: Request body (for POST)
        headers: Request headers
    
    Returns:
        Response JSON as dict
    """
    url = f"{BASE_URL}{endpoint}"
    
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
        
        # Capture for evidence
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


def test_god_mode_placeholder_via_rest_api():
    """
    RED TEST: Reproduce placeholder bug using REST API (real user flow).
    
    This test:
    1. Creates campaign via POST /api/campaigns with god_mode_data (string)
    2. Gets campaign state via GET /api/campaigns/{id}
    3. Checks Scene 1 (opening story) for placeholder text
    
    Expected to FAIL (RED) until bug is fixed.
    """
    log("=" * 80)
    log("TEST: God Mode Placeholder Bug via REST API")
    log("=" * 80)
    log(f"Base URL: {BASE_URL}")
    log(f"User ID: {USER_ID}")
    log(f"Evidence Dir: {EVIDENCE_DIR}")
    
    # Test with frontend format (separate fields) - matches user's exact scenario
    # User reported: "Character: A stealthy monk trained in martial arts and inner discipline | Setting: The haunted moors of Barovia..."
    character = "A stealthy monk trained in martial arts and inner discipline"
    setting = "The haunted moors of Barovia, trapped in eternal mist and ruled by dark powers"
    description = ""
    
    # Step 1: Create campaign via REST API (real user flow - frontend format)
    log("Step 1: Creating campaign via POST /api/campaigns (frontend format)")
    log(f"  Character: {character}")
    log(f"  Setting: {setting}")
    create_data = {
        "title": "REST API Test - Frontend Format (Separate Fields)",
        "character": character,  # ← Frontend format: separate fields
        "setting": setting,      # ← Not god_mode_data string!
        "description": description,
        "selectedPrompts": [],
        "use_default_world": False,
    }
    
    # Set up authentication headers
    # For local testing with TESTING_AUTH_BYPASS=true, we can bypass Firebase auth
    # but still need to provide user_id header
    auth_headers = {}
    if os.getenv("TESTING_AUTH_BYPASS") == "true":
        # Testing mode: bypass Firebase auth, but provide user_id header
        auth_headers["X-Test-Bypass-Auth"] = "true"
        auth_headers["X-Test-User-ID"] = USER_ID
        log(f"Using TESTING_AUTH_BYPASS mode with user_id={USER_ID}")
    else:
        # Real server: try to get auth token
        token = os.getenv("AUTH_TOKEN")
        if token:
            auth_headers["Authorization"] = f"Bearer {token}"
        else:
            log("⚠️ WARNING: No AUTH_TOKEN provided and TESTING_AUTH_BYPASS not set")
            log("   Set TESTING_AUTH_BYPASS=true for local testing")
    
    create_response = api_call("POST", "/api/campaigns", data=create_data, headers=auth_headers)
    
    campaign_id = create_response.get("campaign_id")
    if not campaign_id:
        raise RuntimeError(f"Campaign creation failed: {create_response}")
    
    log(f"✅ Campaign created: {campaign_id}")
    
    # Step 2: Get campaign state via REST API (real user flow)
    log("Step 2: Getting campaign state via GET /api/campaigns/{id}")
    state_response = api_call("GET", f"/api/campaigns/{campaign_id}", headers=auth_headers)
    
    # Extract Scene 1 from campaign state
    # Scene 1 is the first narrative entry (opening story) from the agent/gemini
    story_entries = state_response.get("story", [])
    
    log(f"Found {len(story_entries)} story entries")
    
    # Find Scene 1 (first agent/gemini narrative entry)
    scene1_text = ""
    scene1_entry = None
    
    # Check story entries (most recent first, so we need to find the FIRST one chronologically)
    # Story entries are typically ordered newest-first, so we need to reverse or find the first agent entry
    for entry in story_entries:
        if isinstance(entry, dict):
            actor = entry.get("actor", "")
            text = entry.get("text", "")
            user_scene_number = entry.get("user_scene_number")
            
            # Scene 1 is the first narrative from agent/gemini (opening story)
            # Check for Scene 1 specifically, or just the first agent entry
            if actor in ("gemini", "agent", "system") and text:
                if user_scene_number == 1 or (not scene1_text and not user_scene_number):
                    # This is Scene 1 or the first agent entry
                    scene1_text = text
                    scene1_entry = entry
                    # If we found Scene 1 specifically, break; otherwise continue to find Scene 1
                    if user_scene_number == 1:
                        break
        elif isinstance(entry, str) and not scene1_text:
            scene1_text = entry
            break
    
    # Fallback: check campaign metadata for opening story
    if not scene1_text:
        scene1_text = state_response.get("opening_story", "") or state_response.get("initial_story", "") or ""
    
    log(f"Scene 1 length: {len(scene1_text)} chars")
    log(f"Scene 1 preview: {scene1_text[:300]}...")
    
    # Also log all story entries for debugging
    log(f"Story entries structure:")
    for i, entry in enumerate(story_entries[:5]):  # First 5 entries
        if isinstance(entry, dict):
            log(f"  Entry {i}: actor={entry.get('actor')}, scene={entry.get('user_scene_number')}, text_len={len(entry.get('text', ''))}")
        else:
            log(f"  Entry {i}: {type(entry).__name__}, len={len(str(entry))}")
    
    # Step 3: VERIFY BUG REPRODUCTION
    placeholder_text = "[Character Creation Mode - Story begins after character is complete]"
    
    # BUG CHECK 1: Placeholder should NOT be present in Scene 1
    has_placeholder = placeholder_text in scene1_text
    
    if has_placeholder:
        log(f"❌ BUG REPRODUCED: Scene 1 contains placeholder '{placeholder_text}'")
        log(f"   This means god_mode_data (string) was not parsed correctly")
        log(f"   Full Scene 1: {scene1_text}")
        
        # Save evidence
        evidence_file = EVIDENCE_DIR / "bug_reproduction_evidence.json"
        with open(evidence_file, "w") as f:
            json.dump({
                "campaign_id": campaign_id,
                "scene1_text": scene1_text,
                "scene1_entry": scene1_entry,
                "has_placeholder": True,
                "placeholder_text": placeholder_text,
                "story_entries_count": len(story_entries),
                "story_entries": story_entries[:10],  # First 10 for debugging
                "api_calls": API_CALLS,
            }, f, indent=2)
        log(f"   Evidence saved to: {evidence_file}")
        
        return False  # Test fails (RED state)
    
    # BUG CHECK 2: Character creation narrative SHOULD be present
    has_char_creation = "[CHARACTER CREATION" in scene1_text or "character creation" in scene1_text.lower()
    
    if not has_char_creation:
        log(f"⚠️ WARNING: Scene 1 doesn't contain character creation narrative")
        log(f"   Got: {scene1_text[:300]}...")
    
    # BUG CHECK 3: Scene 1 should be substantial (not placeholder)
    is_substantial = len(scene1_text) > 100
    
    if not is_substantial:
        log(f"⚠️ WARNING: Scene 1 is too short ({len(scene1_text)} chars)")
        log(f"   Got: {scene1_text}")
    
    # Test passes if no placeholder and has character creation content
    if not has_placeholder and (has_char_creation or is_substantial):
        log("✅ TEST PASSED: No placeholder, proper character creation narrative in Scene 1")
        return True
    else:
        log("❌ TEST FAILED: Placeholder present or missing character creation narrative in Scene 1")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test God Mode Placeholder Bug via REST API")
    parser.add_argument("--base-url", default=None, help="Server base URL")
    parser.add_argument("--user-id", default=None, help="Test user ID")
    args = parser.parse_args()
    
    # Update globals if provided via args
    if args.base_url:
        global BASE_URL
        BASE_URL = args.base_url
    if args.user_id:
        global USER_ID
        USER_ID = args.user_id
    
    log("=" * 80)
    log("GOD MODE PLACEHOLDER BUG TEST (REST API)")
    log("=" * 80)
    log(f"Server: {BASE_URL}")
    log(f"User ID: {USER_ID}")
    log(f"Evidence Dir: {EVIDENCE_DIR}")
    log("=" * 80)
    
    # Capture git provenance
    log("Capturing git provenance...")
    provenance = evidence_utils.capture_provenance(BASE_URL)
    
    # Run test
    try:
        test_passed = test_god_mode_placeholder_via_rest_api()
        
        # Save evidence bundle
        log("Creating evidence bundle...")
        results = {
            "test_passed": test_passed,
            "test_name": WORK_NAME,
            "campaign_id": None,  # Will be filled from API_CALLS
        }
        
        # Extract campaign_id from API calls
        for call in API_CALLS:
            if call.get("endpoint") == "/api/campaigns" and call.get("method") == "POST":
                response = call.get("response", {})
                if "campaign_id" in response:
                    results["campaign_id"] = response["campaign_id"]
                    break
        
        evidence_utils.create_evidence_bundle(
            EVIDENCE_DIR,
            test_name=WORK_NAME,
            provenance=provenance,
            results=results,
            request_responses=API_CALLS,
        )
        
        log(f"✅ Evidence bundle created: {EVIDENCE_DIR}")
        
        if test_passed:
            log("🎉 TEST PASSED")
            sys.exit(0)
        else:
            log("💥 TEST FAILED - Bug reproduced")
            sys.exit(1)
            
    except Exception as e:
        log(f"❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        
        # Save error evidence
        error_file = EVIDENCE_DIR / "test_error.json"
        with open(error_file, "w") as f:
            json.dump({
                "error": str(e),
                "traceback": traceback.format_exc(),
                "api_calls": API_CALLS,
            }, f, indent=2)
        
        sys.exit(1)


if __name__ == "__main__":
    main()
