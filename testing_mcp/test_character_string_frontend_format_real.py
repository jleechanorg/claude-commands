#!/usr/bin/env python3
"""
Test character string interpretation with frontend format (separate fields).

Reproduces user-reported issue:
- Character: "A stealthy monk trained in martial arts and inner discipline"
- Setting: "The haunted moors of Barovia..."
- Shows placeholder instead of character creation narrative

Uses MCP client to match real server behavior.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from testing_mcp.lib import evidence_utils
from testing_mcp.lib.campaign_utils import create_campaign, get_campaign_state
from testing_mcp.lib.mcp_client import MCPClient
from testing_mcp.lib.server_utils import DEFAULT_MCP_BASE_URL, pick_free_port

# Configuration
BASE_URL = os.getenv("BASE_URL") or DEFAULT_MCP_BASE_URL
USER_ID = f"frontend-format-test-{datetime.now().strftime('%Y%m%d%H%M%S')}"
WORK_NAME = "character_string_frontend_format_real"

# Evidence directory
EVIDENCE_DIR = evidence_utils.get_evidence_dir(WORK_NAME) / datetime.now().strftime("%Y%m%d_%H%M%S")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


def log(msg: str) -> None:
    """Log with timestamp."""
    ts = datetime.now(timezone.utc).isoformat()
    print(f"[{ts}] {msg}")
    sys.stdout.flush()


def test_frontend_format_character_string():
    """
    Test frontend format (separate character/setting fields).
    
    Reproduces user-reported bug where placeholder is shown instead of
    character creation narrative.
    """
    log("=" * 80)
    log("TEST: Frontend Format Character String (Separate Fields)")
    log("=" * 80)
    log(f"Base URL: {BASE_URL}")
    log(f"User ID: {USER_ID}")
    log(f"Evidence Dir: {EVIDENCE_DIR}")
    
    # Initialize MCP client
    client = MCPClient(BASE_URL)
    log("✅ MCP client initialized")
    
    # User's exact scenario
    character = "A stealthy monk trained in martial arts and inner discipline"
    setting = "The haunted moors of Barovia, trapped in eternal mist and ruled by dark powers"
    description = ""
    
    log(f"Creating campaign with:")
    log(f"  Character: {character}")
    log(f"  Setting: {setting}")
    log(f"  Description: {description or '(empty)'}")
    
    # Create campaign using frontend format (separate fields)
    try:
        campaign_id = create_campaign(
            client=client,
            user_id=USER_ID,
            title="Frontend Format Test - Stealthy Monk",
            character=character,  # ← Frontend format: separate field
            setting=setting,      # ← Not god_mode_data string!
            description=description,
            selected_prompts=[],
        )
        log(f"✅ Campaign created: {campaign_id}")
    except Exception as e:
        log(f"❌ Campaign creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Get campaign state (with story entries)
    try:
        state = get_campaign_state(client, user_id=USER_ID, campaign_id=campaign_id, include_story=True)
        log("✅ Campaign state retrieved")
    except Exception as e:
        log(f"❌ Failed to get campaign state: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Extract Scene 1 (opening story)
    story_entries = state.get("story", [])
    log(f"Found {len(story_entries)} story entries")
    
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
    
    log(f"Scene 1 length: {len(scene1_text)} chars")
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
        "story_entries": story_entries[:10],
    }
    
    evidence_file = EVIDENCE_DIR / "test_evidence.json"
    with open(evidence_file, "w") as f:
        json.dump(evidence_data, f, indent=2)
    log(f"Evidence saved to: {evidence_file}")
    
    # Verify bug reproduction
    if has_placeholder:
        log(f"❌ BUG REPRODUCED: Scene 1 contains placeholder '{placeholder_text}'")
        log(f"   This means frontend format (separate fields) was not handled correctly")
        log(f"   Full Scene 1: {scene1_text}")
        return False
    
    # Check for character creation narrative
    has_char_creation = "[CHARACTER CREATION" in scene1_text or "character creation" in scene1_text.lower()
    is_substantial = len(scene1_text) > 100
    
    if not has_placeholder and (has_char_creation or is_substantial):
        log("✅ TEST PASSED: No placeholder, proper character creation narrative in Scene 1")
        return True
    else:
        log("❌ TEST FAILED: Placeholder present or missing character creation narrative")
        log(f"   Scene 1: {scene1_text[:500]}...")
        return False


def main():
    parser = argparse.ArgumentParser(description="Test Frontend Format Character String")
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
    log("FRONTEND FORMAT CHARACTER STRING TEST")
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
        test_passed = test_frontend_format_character_string()
        
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
