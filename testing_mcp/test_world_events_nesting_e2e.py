#!/usr/bin/env python3
"""
REAL E2E TEST: World Events Nesting Bug Reproduction
Bead: W2-7m1

This test makes REAL LLM calls to reproduce the bug where world_events
gets nested inside custom_campaign_state instead of at the top level.

Test Flow:
1. Create a real campaign on the dev server
2. Play 6+ turns to trigger at least 2 living world turns (turns 3 and 6)
3. Check game_state for world_events in BOTH locations
4. Prove the bug by showing world_events in wrong location

Requirements:
- Dev server running at https://mvp-site-app-dev-i6xf2p72ka-uc.a.run.app
- OR local server at http://localhost:8001
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))
from testing_mcp.lib.evidence_utils import get_evidence_dir

# Configuration - prefer local, fall back to dev
LOCAL_URL = "http://localhost:8001"
DEV_URL = "https://mvp-site-app-dev-i6xf2p72ka-uc.a.run.app"
OUTPUT_DIR = get_evidence_dir("world_events_nesting_e2e")


def check_server(url: str) -> bool:
    """Check if server is available."""
    try:
        req = urllib.request.Request(f"{url}/health", method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except Exception:
        return False


def api_call(base_url: str, endpoint: str, data: dict) -> dict:
    """Make API call to server."""
    url = f"{base_url}{endpoint}"
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        return {"error": f"HTTP {e.code}: {error_body}"}
    except Exception as e:
        return {"error": str(e)}


def create_campaign(base_url: str, user_id: str) -> dict:
    """Create a campaign with factions for living world testing."""
    return api_call(base_url, "/api/campaigns", {
        "user_id": user_id,
        "title": f"LW Nesting Test {datetime.now(timezone.utc).strftime('%H%M%S')}",
        "initial_prompt": """You are a mercenary in a war-torn kingdom.
The Merchant Guild controls trade. The Iron Legion controls the military.
The Shadow Court operates in secret. You must navigate these factions.""",
        "selected_prompts": ["narrative", "mechanics"]
    })


def process_turn(base_url: str, user_id: str, campaign_id: str, action: str) -> dict:
    """Process a player turn."""
    return api_call(base_url, "/api/action", {
        "user_id": user_id,
        "campaign_id": campaign_id,
        "user_input": action
    })


def get_game_state(base_url: str, user_id: str, campaign_id: str) -> dict:
    """Get current game state."""
    return api_call(base_url, "/api/game_state", {
        "user_id": user_id,
        "campaign_id": campaign_id
    })


def main():
    print("=" * 70)
    print("REAL E2E TEST: World Events Nesting Bug (W2-7m1)")
    print("=" * 70)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print()

    # Find available server
    if check_server(LOCAL_URL):
        base_url = LOCAL_URL
        print(f"Using LOCAL server: {base_url}")
    elif check_server(DEV_URL):
        base_url = DEV_URL
        print(f"Using DEV server: {base_url}")
    else:
        print("ERROR: No server available")
        print(f"  Tried: {LOCAL_URL}")
        print(f"  Tried: {DEV_URL}")
        return 1

    user_id = f"e2e-nesting-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    print(f"User ID: {user_id}")
    print()

    # Step 1: Create campaign
    print("Step 1: Creating campaign...")
    result = create_campaign(base_url, user_id)
    if "error" in result:
        print(f"  FAILED: {result['error']}")
        return 1

    campaign_id = result.get("campaign_id")
    print(f"  Campaign ID: {campaign_id}")

    # Step 2: Play 6 turns to trigger living world on turns 3 and 6
    actions = [
        "I look around the tavern and observe the patrons.",
        "I approach the barkeep and ask about local news.",
        "I check my equipment and prepare for the day ahead.",  # Turn 3 = LW
        "I step outside and survey the marketplace.",
        "I visit a weapon smith to inquire about blade repairs.",
        "I head to the guild hall to check for available contracts.",  # Turn 6 = LW
    ]

    living_world_turns = []
    for i, action in enumerate(actions, 1):
        print(f"\nStep 2.{i}: Turn {i} - {action[:50]}...")
        result = process_turn(base_url, user_id, campaign_id, action)

        if "error" in result:
            print(f"  FAILED: {result['error']}")
            continue

        # Check for living world content
        structured = result.get("structured_fields", {})
        world_events = structured.get("world_events")
        state_updates = structured.get("state_updates", {})
        su_world_events = state_updates.get("world_events") if isinstance(state_updates, dict) else None

        if world_events or su_world_events:
            we = world_events or su_world_events
            print(f"  LIVING WORLD TURN!")
            print(f"    turn_generated: {we.get('turn_generated')}")
            print(f"    background_events: {len(we.get('background_events', []))}")
            living_world_turns.append({
                "turn": i,
                "turn_generated": we.get("turn_generated"),
                "in_structured_fields": bool(world_events),
                "in_state_updates": bool(su_world_events)
            })
        else:
            print(f"  Regular turn (no world_events in response)")

    # Step 3: Get final game state and check for nesting bug
    print("\nStep 3: Checking game state for nesting bug...")
    state = get_game_state(base_url, user_id, campaign_id)

    if "error" in state:
        print(f"  FAILED to get state: {state['error']}")
        return 1

    game_state = state.get("game_state", {})
    player_turn = game_state.get("player_turn", 0)

    # Check correct location
    top_level_we = game_state.get("world_events", {})

    # Check wrong location
    ccs = game_state.get("custom_campaign_state", {})
    nested_we = ccs.get("world_events", {}) if isinstance(ccs, dict) else {}

    print(f"\n  player_turn: {player_turn}")
    print(f"  game_state.world_events: {bool(top_level_we)}")
    if top_level_we:
        print(f"    turn_generated: {top_level_we.get('turn_generated')}")
        print(f"    events: {len(top_level_we.get('background_events', []))}")

    print(f"  custom_campaign_state.world_events: {bool(nested_we)}")
    if nested_we:
        print(f"    turn_generated: {nested_we.get('turn_generated')}")
        print(f"    events: {len(nested_we.get('background_events', []))}")

    # Determine bug status
    print("\n" + "=" * 70)
    print("RESULTS:")
    print("=" * 70)

    has_bug = bool(nested_we)

    if has_bug:
        print("BUG REPRODUCED: world_events found in custom_campaign_state!")
        print("This proves the LLM is outputting world_events to the wrong location.")
    elif top_level_we:
        print("NO BUG: world_events correctly at top level only.")
        print("The LLM output world_events to the correct location this time.")
    else:
        print("INCONCLUSIVE: No world_events found in either location.")
        print("Living world may not have triggered, or events were empty.")

    # Save evidence
    evidence = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "server": base_url,
        "user_id": user_id,
        "campaign_id": campaign_id,
        "player_turn": player_turn,
        "living_world_turns": living_world_turns,
        "top_level_world_events": {
            "exists": bool(top_level_we),
            "turn_generated": top_level_we.get("turn_generated") if top_level_we else None
        },
        "nested_world_events": {
            "exists": bool(nested_we),
            "turn_generated": nested_we.get("turn_generated") if nested_we else None
        },
        "bug_reproduced": has_bug
    }

    evidence_file = OUTPUT_DIR / "e2e_evidence.json"
    with open(evidence_file, "w") as f:
        json.dump(evidence, f, indent=2, default=str)

    print(f"\nEvidence saved to: {evidence_file}")

    return 1 if has_bug else 0


if __name__ == "__main__":
    exit(main())
