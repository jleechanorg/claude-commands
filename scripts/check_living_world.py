#!/usr/bin/env python3
"""
check_living_world.py - Living World Updates Diagnostic Tool

Query Firestore to check if living world updates are being generated and stored
for a given campaign. Useful for debugging when UI isn't showing updates.

Usage:
    python scripts/check_living_world.py <campaign_id> [--turns N]
    python scripts/check_living_world.py STpjRuwjeUt97tpCl5nK --turns 20
    WORLDAI_DEV_MODE=true python scripts/check_living_world.py <campaign_id>

Options:
    --turns N       Number of recent turns to analyze (default: 10)
    --verbose       Show full JSON for world_events
    --help          Show this help message

Environment:
    WORLDAI_DEV_MODE=true  Required for clock skew patch
"""

import argparse
import json
import os
import sys
from pathlib import Path


def setup_firebase():
    """Initialize Firebase with proper credentials."""
    # Set credentials path
    creds_path = os.path.expanduser("~/serviceAccountKey.json")
    if os.path.exists(creds_path):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path
    else:
        print(f"Warning: Credentials not found at {creds_path}")

    # Set project explicitly
    project_id = "worldarchitecture-ai"
    os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
    os.environ["GCLOUD_PROJECT"] = project_id
    os.environ["WORLDAI_DEV_MODE"] = "true"

    # Import and apply clock skew patch first (critical for local dev)
    script_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(script_dir))
    try:
        from mvp_site.clock_skew_credentials import apply_clock_skew_patch
    except ImportError as e:
        print(f"Error importing clock skew patch: {e}")
        print("Ensure mvp_site is in your Python path")
        sys.exit(1)

    try:
        apply_clock_skew_patch()
    except Exception as e:
        print(f"Error applying clock skew patch: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    try:
        # Use firebase-admin for consistency with the app
        import firebase_admin
        from firebase_admin import credentials, firestore

        try:
            firebase_admin.get_app()
        except ValueError:
            if os.path.exists(creds_path):
                cred = credentials.Certificate(creds_path)
                firebase_admin.initialize_app(cred, {"projectId": project_id})
            else:
                firebase_admin.initialize_app(options={"projectId": project_id})

        db = firestore.client()
        return db

    except Exception as e:
        print(f"Error initializing Firebase: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def get_campaign_info(db, campaign_id: str) -> tuple[dict | None, str | None]:
    """Get campaign info. Returns (campaign_data, user_id) tuple.

    Campaigns are stored under /users/{userId}/campaigns/{campaignId}
    Uses collection group query for efficient lookup across all users.
    """
    # First try direct collection (legacy support)
    doc = db.collection("campaigns").document(campaign_id).get()
    if doc.exists:
        return doc.to_dict(), None

    # Use collection group query for efficient lookup across all users
    # This avoids iterating through every user document
    from google.cloud.firestore_v1 import FieldPath

    campaigns_query = (
        db.collection_group("campaigns")
        .where(FieldPath.document_id(), "==", campaign_id)
        .limit(1)
    )
    for campaign_doc in campaigns_query.stream():
        data = campaign_doc.to_dict()
        # Extract user_id from parent path: /users/{userId}/campaigns/{campaignId}
        parent_ref = campaign_doc.reference.parent.parent
        user_id = parent_ref.id if parent_ref is not None else None
        return data, user_id

    return None, None


def get_recent_turns(db, campaign_id: str, user_id: str | None = None, limit: int = 10) -> list:
    """Get the most recent story entries for a campaign.

    Story entries are stored in /users/{uid}/campaigns/{campaign_id}/story/
    """
    from google.cloud.firestore_v1 import Query

    # Build the path based on where the campaign is stored
    if user_id:
        campaign_ref = (
            db.collection("users")
            .document(user_id)
            .collection("campaigns")
            .document(campaign_id)
        )
    else:
        campaign_ref = db.collection("campaigns").document(campaign_id)

    # Story entries are in "story" subcollection, ordered by timestamp
    # Fetch 3x requested limit to account for user/AI turn pairs and filtering
    # (typical ratio: ~50% AI responses in interleaved user/AI turns)
    story_ref = (
        campaign_ref.collection("story")
        .order_by("timestamp", direction=Query.DESCENDING)
        .limit(limit * 3)
    )

    turns = []
    for doc in story_ref.stream():
        turn_data = doc.to_dict()
        turn_data["_doc_id"] = doc.id
        # Only include AI responses which have structured fields
        # Note: "gemini" is the standard actor name for AI responses in this codebase
        if turn_data.get("actor") == "gemini":
            turns.append(turn_data)
            if len(turns) >= limit:
                break

    return list(reversed(turns))  # Return in chronological order


def analyze_living_world_data(turn: dict) -> dict:
    """Analyze a turn for living world data presence."""
    analysis = {
        "turn_number": turn.get("turn_number", "N/A"),
        "has_state_updates": False,
        "has_world_events": False,
        "has_structured_fields": False,
        "world_events": None,
        "faction_updates": None,
        "time_events": None,
        "rumors": None,
        "scene_event": None,
        "complications": None,
    }

    # Check for state_updates in turn data
    state_updates = turn.get("state_updates", {})
    if state_updates and isinstance(state_updates, dict):
        analysis["has_state_updates"] = True
        analysis["world_events"] = state_updates.get("world_events")
        analysis["faction_updates"] = state_updates.get("faction_updates")
        analysis["time_events"] = state_updates.get("time_events")
        analysis["rumors"] = state_updates.get("rumors")
        analysis["scene_event"] = state_updates.get("scene_event")
        analysis["complications"] = state_updates.get("complications")

    # Check for direct world_events field
    if turn.get("world_events"):
        analysis["has_world_events"] = True
        if not analysis["world_events"]:
            analysis["world_events"] = turn.get("world_events")

    # Check structured_fields
    structured_fields = turn.get("structured_fields", {})
    if structured_fields and isinstance(structured_fields, dict):
        analysis["has_structured_fields"] = True
        if structured_fields.get("state_updates"):
            su = structured_fields["state_updates"]
            if not analysis["world_events"]:
                analysis["world_events"] = su.get("world_events")
            if not analysis["faction_updates"]:
                analysis["faction_updates"] = su.get("faction_updates")
            if not analysis["scene_event"]:
                analysis["scene_event"] = su.get("scene_event")

    return analysis


def format_world_event(event: dict, indent: int = 4) -> str:
    """Format a single world event for display."""
    prefix = " " * indent
    lines = []

    actor = event.get("actor", "Unknown")
    action = event.get("action", "Unknown action")
    event_type = event.get("event_type", "unknown")
    status = event.get("status", "pending")

    status_emoji = {
        "pending": "⏳",
        "discovered": "👁️",
        "resolved": "✅"
    }.get(status, "❓")

    lines.append(f"{prefix}{status_emoji} {actor}: {action}")
    lines.append(f"{prefix}   Type: {event_type}, Status: {status}")

    if event.get("turn_generated"):
        lines.append(f"{prefix}   Generated: Turn {event.get('turn_generated')}")
    if event.get("discovery_condition"):
        discovery = str(event.get("discovery_condition") or "")
        if len(discovery) > 60:
            lines.append(f"{prefix}   Discovery: {discovery[:60]}...")
        else:
            lines.append(f"{prefix}   Discovery: {discovery}")

    return "\n".join(lines)


def print_turn_analysis(analysis: dict, verbose: bool = False):
    """Print analysis for a single turn."""
    turn_num = analysis["turn_number"]

    # Determine status indicators
    indicators = []
    if analysis["has_state_updates"]:
        indicators.append("state_updates")
    if analysis["has_world_events"]:
        indicators.append("world_events")
    if analysis["has_structured_fields"]:
        indicators.append("structured_fields")

    status = " | ".join(indicators) if indicators else "No living world data"
    print(f"\n{'='*60}")
    print(f"Turn {turn_num}: {status}")
    print(f"{'='*60}")

    # World Events
    world_events = analysis.get("world_events")
    if world_events and isinstance(world_events, dict):
        bg_events = world_events.get("background_events", [])
        if bg_events:
            print(f"\n  📜 Background Events ({len(bg_events)}):")
            for event in bg_events[:5]:  # Show max 5
                if isinstance(event, dict):
                    print(format_world_event(event, indent=6))

        if verbose:
            print(f"\n  [Full world_events JSON]:")
            print(json.dumps(world_events, indent=4, default=str))

    # Scene Event
    scene_event = analysis.get("scene_event")
    if scene_event and isinstance(scene_event, dict):
        print(f"\n  ⚡ Scene Event:")
        print(f"      Type: {scene_event.get('type', 'N/A')}")
        print(f"      Actor: {scene_event.get('actor', 'N/A')}")
        desc = scene_event.get('description', 'N/A')
        print(f"      Description: {desc[:80]}..." if len(str(desc)) > 80 else f"      Description: {desc}")

    # Faction Updates
    faction_updates = analysis.get("faction_updates")
    if faction_updates and isinstance(faction_updates, dict):
        print(f"\n  ⚔️ Faction Updates ({len(faction_updates)}):")
        for faction, update in list(faction_updates.items())[:3]:  # Show max 3
            if isinstance(update, dict):
                obj = update.get("current_objective") or "N/A"
                obj_str = str(obj)
                print(f"      {faction}: {obj_str[:60]}..." if len(obj_str) > 60 else f"      {faction}: {obj_str}")

    # Complications
    complications = analysis.get("complications")
    if complications and isinstance(complications, dict):
        if complications.get("triggered"):
            print(f"\n  ⚠️ Complication Triggered:")
            print(f"      Type: {complications.get('type', 'N/A')}")
            print(f"      Severity: {complications.get('severity', 'N/A')}")

    # Rumors
    rumors = analysis.get("rumors")
    if rumors and isinstance(rumors, list) and len(rumors) > 0:
        print(f"\n  💬 Rumors ({len(rumors)}):")
        for rumor in rumors[:2]:  # Show max 2
            if isinstance(rumor, dict):
                content = rumor.get("content") or "N/A"
                content_str = str(content)
                print(f"      - {content_str[:60]}..." if len(content_str) > 60 else f"      - {content_str}")


def main():
    parser = argparse.ArgumentParser(
        description="Check Living World updates for a campaign",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("campaign_id", help="Campaign ID to analyze")
    parser.add_argument("--turns", type=int, default=10, help="Number of turns to analyze (default: 10)")
    parser.add_argument("--verbose", action="store_true", help="Show full JSON for world_events")

    args = parser.parse_args()

    print("=" * 60)
    print("Living World Updates Diagnostic Tool")
    print("=" * 60)

    # Initialize Firebase
    print("\n🔥 Connecting to Firestore...")
    db = setup_firebase()
    print("   Connected ✅")

    # Get campaign info
    campaign, user_id = get_campaign_info(db, args.campaign_id)
    if not campaign:
        print(f"   ❌ Campaign not found: {args.campaign_id}")
        print(f"   Searched in /campaigns and /users/*/campaigns")
        sys.exit(1)

    if user_id:
        print(f"   Found under user: {user_id}")

    # Get campaign details
    print(f"\n📋 Campaign: {args.campaign_id}")
    campaign_name = campaign.get("name") or campaign.get("title") or "Unnamed"
    # Handle case where game_state is explicitly None (not just missing)
    game_state = campaign.get("game_state") or {}
    player_turn = game_state.get("player_turn", "N/A")
    print(f"   Name: {campaign_name}")
    print(f"   Current Turn: {player_turn}")

    # Check campaign-level living_world_state
    living_world_state = campaign.get("living_world_state", {})
    game_state_world_events = game_state.get("world_events", {})

    print(f"\n📊 Campaign-Level Data:")
    print(f"   living_world_state: {'Present ✅' if living_world_state else 'Missing ❌'}")
    print(f"   game_state.world_events: {'Present ✅' if game_state_world_events else 'Missing ❌'}")

    if game_state_world_events:
        bg_events = game_state_world_events.get("background_events", [])
        print(f"   Background events in state: {len(bg_events)}")

    # Get recent turns
    turns = get_recent_turns(db, args.campaign_id, user_id=user_id, limit=args.turns)

    print(f"\n🔍 Analyzing last {args.turns} turns...")

    if not turns:
        print("   ❌ No turns found!")
        sys.exit(1)

    print(f"   Found {len(turns)} turns")

    # Analyze each turn
    turns_with_living_world = 0
    turns_with_world_events = 0
    turns_with_scene_events = 0

    for turn in turns:
        analysis = analyze_living_world_data(turn)
        print_turn_analysis(analysis, verbose=args.verbose)

        if analysis["has_state_updates"] or analysis["has_world_events"]:
            turns_with_living_world += 1
        if analysis["world_events"]:
            turns_with_world_events += 1
        if analysis["scene_event"]:
            turns_with_scene_events += 1

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Turns analyzed: {len(turns)}")
    print(f"  Turns with living world data: {turns_with_living_world}")
    print(f"  Turns with world_events: {turns_with_world_events}")
    print(f"  Turns with scene_events: {turns_with_scene_events}")

    if turns_with_living_world == 0:
        print("\n⚠️  No living world data found in any turn!")
        print("   Possible causes:")
        print("   1. Living World instruction not included in prompts")
        print("   2. LLM not generating state_updates field")
        print("   3. Data not being stored properly")
    elif turns_with_living_world < max(1, len(turns) // 3):
        # Living world triggers every 3 turns, so expect ~1/3 of turns to have data
        print(f"\n⚠️  Living world data found in only {turns_with_living_world}/{len(turns)} turns")
        print("   Living world triggers every 3 turns - this may be normal")
    else:
        print("\n✅ Living world system appears to be working!")

    print("\n💡 UI Display Reminder:")
    print("   Living World Updates panel requires Debug Mode to be enabled in Settings")
    print("   Go to Settings > Enable Debug Mode to see the panel in the game UI")


if __name__ == "__main__":
    main()
