#!/usr/bin/env python3
"""
Test REST API character placeholder bug with exact user parameters.

User scenario:
- Custom campaign
- Character: "A brave warrior seeking to prove their worth in battle"
- Setting: "The haunted moors of Barovia, trapped in eternal mist and ruled by dark powers"
- Description: (blank)
- Result: Shows placeholder instead of character creation narrative
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
from testing_mcp.lib.server_utils import DEFAULT_MCP_BASE_URL

# Configuration
BASE_URL = os.getenv("BASE_URL") or DEFAULT_MCP_BASE_URL
USER_ID = f"rest-api-bug-test-{datetime.now().strftime('%Y%m%d%H%M%S')}"
WORK_NAME = "rest_api_character_placeholder_bug"

# Evidence directory
EVIDENCE_DIR = evidence_utils.get_evidence_dir(WORK_NAME) / datetime.now().strftime("%Y%m%d_%H%M%S")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


def log(msg: str) -> None:
    """Log with timestamp."""
    ts = datetime.now(timezone.utc).isoformat()
    print(f"[{ts}] {msg}")
    sys.stdout.flush()


def test_rest_api_character_placeholder_bug():
    """
    Test REST API with exact user parameters.
    
    Reproduces bug where placeholder is shown instead of character creation narrative.
    """
    log("=" * 80)
    log("TEST: REST API Character Placeholder Bug (Exact User Parameters)")
    log("=" * 80)
    log(f"Base URL: {BASE_URL}")
    log(f"User ID: {USER_ID}")
    log(f"Evidence Dir: {EVIDENCE_DIR}")
    
    # Exact user parameters
    character = "A brave warrior seeking to prove their worth in battle"
    setting = "The haunted moors of Barovia, trapped in eternal mist and ruled by dark powers"
    description = ""  # Blank, as user said
    
    log(f"\nCreating campaign with:")
    log(f"  Character: {character}")
    log(f"  Setting: {setting}")
    log(f"  Description: {description or '(blank)'}")
    
    # Set up authentication headers
    auth_headers = {}
    if os.getenv("TESTING_AUTH_BYPASS") == "true":
        auth_headers["X-Test-Bypass-Auth"] = "true"
        auth_headers["X-Test-User-ID"] = USER_ID
        log(f"Using TESTING_AUTH_BYPASS mode with user_id={USER_ID}")
    else:
        token = os.getenv("AUTH_TOKEN")
        if token:
            auth_headers["Authorization"] = f"Bearer {token}"
        else:
            log("⚠️ WARNING: No AUTH_TOKEN provided and TESTING_AUTH_BYPASS not set")
            log("   Set TESTING_AUTH_BYPASS=true for local testing")
            return False
    
    # Create campaign via REST API (exact user flow)
    log("\nStep 1: POST /api/campaigns")
    create_data = {
        "title": "REST API Bug Test - Brave Warrior",
        "character": character,  # ← Frontend format: separate field
        "setting": setting,      # ← Not god_mode_data string!
        "description": description,
        "selected_prompts": [],
        "custom_options": [],
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/campaigns",
            json=create_data,
            headers={**auth_headers, "Content-Type": "application/json"},
            timeout=120,
        )
        response.raise_for_status()
        create_result = response.json()
        campaign_id = create_result.get("campaign_id")
        
        if not campaign_id:
            log(f"❌ Campaign creation failed: {create_result}")
            return False
        
        log(f"✅ Campaign created: {campaign_id}")
    except Exception as e:
        log(f"❌ Campaign creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Get campaign state via REST API
    log("\nStep 2: GET /api/campaigns/{id}?story_limit=10")
    try:
        response = requests.get(
            f"{BASE_URL}/api/campaigns/{campaign_id}?story_limit=10",
            headers=auth_headers,
            timeout=120,
        )
        response.raise_for_status()
        state = response.json()
        log("✅ Campaign state retrieved")
    except Exception as e:
        log(f"❌ Failed to get campaign state: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Extract Scene 1 (opening story)
    story_entries = state.get("story", [])
    log(f"\nFound {len(story_entries)} story entries")
    
    scene1_text = ""
    scene1_entry = None
    
    # Find Scene 1 (first agent/gemini narrative entry)
    for entry in story_entries:
        if isinstance(entry, dict):
            actor = entry.get("actor", "")
            text = entry.get("text", "")
            user_scene_number = entry.get("user_scene_number")
            
            if actor in ("gemini", "agent", "system") and text:
                if user_scene_number == 1 or (not scene1_text and not user_scene_number):
                    scene1_text = text
                    scene1_entry = entry
                    if user_scene_number == 1:
                        break
        elif isinstance(entry, str) and not scene1_text:
            scene1_text = entry
            break
    
    # Fallback: check campaign metadata
    if not scene1_text:
        scene1_text = state.get("opening_story", "") or state.get("initial_story", "") or ""
    
    log(f"\nScene 1 length: {len(scene1_text)} chars")
    log(f"Scene 1 preview: {scene1_text[:300]}...")
    
    # Check for placeholder
    placeholder_text = "[Character Creation Mode - Story begins after character is complete]"
    has_placeholder = placeholder_text in scene1_text
    
    # Save evidence
    evidence_data = {
        "campaign_id": campaign_id,
        "character": character,
        "setting": setting,
        "description": description,
        "scene1_text": scene1_text,
        "scene1_entry": scene1_entry,
        "has_placeholder": has_placeholder,
        "placeholder_text": placeholder_text,
        "story_entries_count": len(story_entries),
        "story_entries": story_entries[:5],  # First 5 for debugging
        "full_state_keys": list(state.keys()),
    }
    
    evidence_file = EVIDENCE_DIR / "test_evidence.json"
    with open(evidence_file, "w") as f:
        json.dump(evidence_data, f, indent=2)
    log(f"\nEvidence saved to: {evidence_file}")
    
    # Verify bug reproduction
    if has_placeholder:
        log(f"\n❌ BUG REPRODUCED: Scene 1 contains placeholder '{placeholder_text}'")
        log(f"   This means frontend format (separate fields) was not handled correctly")
        log(f"   Full Scene 1: {scene1_text}")
        return False
    
    # Check for character creation narrative
    has_char_creation = "[CHARACTER CREATION" in scene1_text or "character creation" in scene1_text.lower()
    is_substantial = len(scene1_text) > 100
    
    if not has_placeholder and (has_char_creation or is_substantial):
        log("\n✅ TEST PASSED: No placeholder, proper character creation narrative in Scene 1")
        return True
    else:
        log("\n❌ TEST FAILED: Placeholder present or missing character creation narrative")
        log(f"   Scene 1: {scene1_text[:500]}...")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test REST API Character Placeholder Bug")
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
    log("REST API CHARACTER PLACEHOLDER BUG TEST")
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
        test_passed = test_rest_api_character_placeholder_bug()
        
        # Save evidence bundle
        log("Creating evidence bundle...")
        results = {
            "test_passed": test_passed,
            "test_name": WORK_NAME,
        }
        
        evidence_utils.create_evidence_bundle(
            EVIDENCE_DIR,
            test_name=WORK_NAME,
            provenance=provenance,
            results=results,
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
        sys.exit(1)


if __name__ == "__main__":
    main()
