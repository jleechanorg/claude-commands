#!/usr/bin/env python3
"""
Investigate campaign issues: dice rolls not showing and god mode agent ignoring messages.

Usage:
    WORLDAI_DEV_MODE=true python scripts/investigate_campaign_issues.py <campaign_id>
"""

import json
import os
import sys
from datetime import datetime, timedelta
from typing import Any

# Apply clock skew patch BEFORE importing firebase_admin
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mvp_site.clock_skew_credentials import apply_clock_skew_patch

apply_clock_skew_patch()

import firebase_admin  # noqa: E402
from firebase_admin import credentials, firestore  # noqa: E402


def initialize_firebase() -> firestore.Client:
    """Initialize Firebase connection."""
    if not firebase_admin._apps:
        try:
            cred_path = os.environ.get("WORLDAI_GOOGLE_APPLICATION_CREDENTIALS")
            if not cred_path:
                cred_path = os.path.expanduser("~/serviceAccountKey.json")

            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                print(f"Firebase initialized with: {cred_path}")
            else:
                firebase_admin.initialize_app()
                print("Firebase initialized with default credentials")
        except Exception as e:
            print(f"Failed to initialize Firebase: {e}")
            raise

    return firestore.client()


def find_campaign_by_id(
    db: firestore.Client, campaign_id: str
) -> tuple[str | None, dict | None]:
    """Find a campaign across all users using collection group query."""
    print(f"\nSearching for campaign: {campaign_id}")

    campaigns_group = db.collection_group("campaigns")

    try:
        for campaign_doc in campaigns_group.stream():
            if campaign_doc.id == campaign_id:
                path_parts = campaign_doc.reference.path.split("/")
                if len(path_parts) >= 4 and path_parts[0] == "users":
                    user_id = path_parts[1]
                    campaign_data = campaign_doc.to_dict() or {}
                    return user_id, campaign_data
    except Exception as e:
        print(f"Error querying campaigns collection group: {e}")
        return None, None

    return None, None


def get_story_entries(
    db: firestore.Client, user_id: str, campaign_id: str, limit: int = 100
) -> list[dict]:
    """Get recent story entries for a campaign."""
    story_ref = (
        db.collection("users")
        .document(user_id)
        .collection("campaigns")
        .document(campaign_id)
        .collection("story")
        .order_by("timestamp", direction=firestore.Query.DESCENDING)
        .limit(limit)
    )

    entries = []
    for entry in story_ref.stream():
        entries.append(entry.to_dict())

    return list(reversed(entries))  # Return in chronological order


def get_game_state(
    db: firestore.Client, user_id: str, campaign_id: str
) -> dict | None:
    """Get game state for a campaign."""
    game_state_ref = (
        db.collection("users")
        .document(user_id)
        .collection("campaigns")
        .document(campaign_id)
        .collection("game_states")
        .document("current_state")
    )

    doc = game_state_ref.get()
    if doc.exists:
        return doc.to_dict()
    return None


def analyze_dice_rolls(story_entries: list[dict]) -> dict[str, Any]:
    """Analyze dice rolls in story entries."""
    dice_found = []
    entries_with_dice = []
    entries_without_dice_but_should_have = []

    for i, entry in enumerate(story_entries):
        actor = entry.get("actor", "")
        text = entry.get("text", "")
        mode = entry.get("mode", "")

        # Check for dice_rolls field
        dice_rolls = entry.get("dice_rolls")
        structured_fields = entry.get("structured_fields", {})
        debug_info = entry.get("debug_info", {})

        # Check various locations for dice data
        has_dice_rolls_field = dice_rolls is not None and len(dice_rolls) > 0
        has_dice_in_structured = (
            isinstance(structured_fields, dict)
            and "dice_rolls" in structured_fields
            and len(structured_fields.get("dice_rolls", [])) > 0
        )
        has_dice_in_debug = (
            isinstance(debug_info, dict)
            and "dice_rolls" in debug_info
            and len(debug_info.get("dice_rolls", [])) > 0
        )

        if has_dice_rolls_field:
            dice_found.extend(dice_rolls)
            entries_with_dice.append(
                {
                    "index": i,
                    "timestamp": entry.get("timestamp"),
                    "actor": actor,
                    "mode": mode,
                    "dice_rolls": dice_rolls,
                    "source": "dice_rolls_field",
                }
            )
        elif has_dice_in_structured:
            dice_found.extend(structured_fields["dice_rolls"])
            entries_with_dice.append(
                {
                    "index": i,
                    "timestamp": entry.get("timestamp"),
                    "actor": actor,
                    "mode": mode,
                    "dice_rolls": structured_fields["dice_rolls"],
                    "source": "structured_fields",
                }
            )
        elif has_dice_in_debug:
            dice_found.extend(debug_info["dice_rolls"])
            entries_with_dice.append(
                {
                    "index": i,
                    "timestamp": entry.get("timestamp"),
                    "actor": actor,
                    "mode": mode,
                    "dice_rolls": debug_info["dice_rolls"],
                    "source": "debug_info",
                }
            )

        # Check if text mentions dice but no dice_rolls field exists
        if actor == "gemini" and (
            "roll" in text.lower()
            or "dice" in text.lower()
            or "d20" in text.lower()
            or "attack" in text.lower()
            or "damage" in text.lower()
        ):
            if not (has_dice_rolls_field or has_dice_in_structured or has_dice_in_debug):
                entries_without_dice_but_should_have.append(
                    {
                        "index": i,
                        "timestamp": entry.get("timestamp"),
                        "actor": actor,
                        "mode": mode,
                        "text_preview": text[:200],
                    }
                )

    return {
        "total_dice_rolls": len(dice_found),
        "entries_with_dice": entries_with_dice,
        "entries_without_dice_but_should_have": entries_without_dice_but_should_have,
        "all_dice_rolls": dice_found,
    }


def analyze_god_mode(story_entries: list[dict], game_state: dict | None) -> dict[str, Any]:
    """Analyze god mode behavior."""
    god_mode_entries = []
    user_messages_in_god_mode = []
    ai_responses_in_god_mode = []
    god_mode_directives = []

    # Get god mode directives from game state
    if game_state:
        custom_state = game_state.get("custom_campaign_state", {})
        god_mode_directives = custom_state.get("god_mode_directives", [])

    for i, entry in enumerate(story_entries):
        actor = entry.get("actor", "")
        mode = entry.get("mode", "")
        text = entry.get("text", "")
        god_mode_response = entry.get("god_mode_response")

        if mode == "god" or "GOD MODE" in text.upper():
            god_mode_entries.append(
                {
                    "index": i,
                    "timestamp": entry.get("timestamp"),
                    "actor": actor,
                    "mode": mode,
                    "text_preview": text[:200],
                    "has_god_mode_response": bool(god_mode_response),
                }
            )

            if actor == "user":
                user_messages_in_god_mode.append(
                    {
                        "index": i,
                        "timestamp": entry.get("timestamp"),
                        "text": text,
                    }
                )
            elif actor == "gemini":
                ai_responses_in_god_mode.append(
                    {
                        "index": i,
                        "timestamp": entry.get("timestamp"),
                        "text_preview": text[:200],
                        "god_mode_response": god_mode_response,
                        "has_response": bool(text or god_mode_response),
                    }
                )

    # Check for user messages that might have been ignored
    ignored_messages = []
    for i, user_msg in enumerate(user_messages_in_god_mode):
        # Check if there's a corresponding AI response
        msg_timestamp = user_msg.get("timestamp")
        if msg_timestamp is None:
            continue  # Skip entries without timestamps
        found_response = False
        for ai_resp in ai_responses_in_god_mode:
            ai_timestamp = ai_resp.get("timestamp")
            if ai_timestamp is not None and ai_timestamp > msg_timestamp:
                found_response = True
                break

        if not found_response and i < len(user_messages_in_god_mode) - 1:
            # Check if next user message exists (meaning AI didn't respond)
            ignored_messages.append(user_msg)

    return {
        "god_mode_entries": god_mode_entries,
        "user_messages_in_god_mode": user_messages_in_god_mode,
        "ai_responses_in_god_mode": ai_responses_in_god_mode,
        "ignored_messages": ignored_messages,
        "god_mode_directives": god_mode_directives,
        "total_directives": len(god_mode_directives),
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/investigate_campaign_issues.py <campaign_id>")
        sys.exit(1)

    campaign_id = sys.argv[1]

    # Initialize Firebase
    db = initialize_firebase()

    # Find campaign
    user_id, campaign_data = find_campaign_by_id(db, campaign_id)
    if not user_id or not campaign_data:
        print(f"Campaign {campaign_id} not found!")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"CAMPAIGN INVESTIGATION REPORT")
    print(f"{'='*60}")
    print(f"Campaign ID: {campaign_id}")
    print(f"Campaign Title: {campaign_data.get('title', 'N/A')}")
    print(f"User ID: {user_id}")
    print(f"{'='*60}\n")

    # Get story entries
    print("Fetching story entries...")
    story_entries = get_story_entries(db, user_id, campaign_id, limit=200)
    print(f"Found {len(story_entries)} story entries\n")

    # Get game state
    print("Fetching game state...")
    game_state = get_game_state(db, user_id, campaign_id)
    print(f"Game state found: {game_state is not None}\n")

    # Analyze dice rolls
    print("=" * 60)
    print("DICE ROLLS ANALYSIS")
    print("=" * 60)
    dice_analysis = analyze_dice_rolls(story_entries)
    print(f"\nTotal dice rolls found: {dice_analysis['total_dice_rolls']}")
    print(f"Entries with dice rolls: {len(dice_analysis['entries_with_dice'])}")
    print(
        f"Entries that mention dice but have no dice_rolls field: {len(dice_analysis['entries_without_dice_but_should_have'])}"
    )

    if dice_analysis["entries_with_dice"]:
        print("\n--- Entries WITH dice rolls ---")
        for entry in dice_analysis["entries_with_dice"][:10]:
            print(
                f"  Entry {entry['index']} ({entry['timestamp']}): {entry['actor']} mode={entry['mode']} source={entry['source']}"
            )
            print(f"    Dice: {json.dumps(entry['dice_rolls'], indent=4)}")

    if dice_analysis["entries_without_dice_but_should_have"]:
        print("\n--- Entries WITHOUT dice rolls (but should have) ---")
        for entry in dice_analysis["entries_without_dice_but_should_have"][:10]:
            print(
                f"  Entry {entry['index']} ({entry['timestamp']}): {entry['actor']} mode={entry['mode']}"
            )
            print(f"    Text preview: {entry['text_preview']}...")

    # Analyze god mode
    print("\n" + "=" * 60)
    print("GOD MODE ANALYSIS")
    print("=" * 60)
    god_mode_analysis = analyze_god_mode(story_entries, game_state)
    print(f"\nTotal god mode entries: {len(god_mode_analysis['god_mode_entries'])}")
    print(
        f"User messages in god mode: {len(god_mode_analysis['user_messages_in_god_mode'])}"
    )
    print(
        f"AI responses in god mode: {len(god_mode_analysis['ai_responses_in_god_mode'])}"
    )
    print(f"Potentially ignored messages: {len(god_mode_analysis['ignored_messages'])}")
    print(f"God mode directives: {god_mode_analysis['total_directives']}")

    if god_mode_analysis["god_mode_directives"]:
        print("\n--- God Mode Directives ---")
        for i, directive in enumerate(god_mode_analysis["god_mode_directives"][:10]):
            if isinstance(directive, dict):
                print(f"  {i+1}. {directive.get('rule', directive)}")
            else:
                print(f"  {i+1}. {directive}")

    if god_mode_analysis["ignored_messages"]:
        print("\n--- Potentially Ignored Messages ---")
        for msg in god_mode_analysis["ignored_messages"][:10]:
            print(f"  Entry {msg['index']} ({msg['timestamp']}):")
            print(f"    {msg['text'][:200]}...")

    if god_mode_analysis["ai_responses_in_god_mode"]:
        print("\n--- Recent AI Responses in God Mode ---")
        for resp in god_mode_analysis["ai_responses_in_god_mode"][-5:]:
            print(f"  Entry {resp['index']} ({resp['timestamp']}):")
            print(f"    Has response: {resp['has_response']}")
            if resp.get("god_mode_response"):
                print(f"    God mode response: {resp['god_mode_response'][:200]}...")
            print(f"    Text preview: {resp['text_preview']}...")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"✓ Story entries analyzed: {len(story_entries)}")
    print(f"✓ Dice rolls found: {dice_analysis['total_dice_rolls']}")
    print(
        f"⚠ Entries missing dice_rolls field: {len(dice_analysis['entries_without_dice_but_should_have'])}"
    )
    print(f"✓ God mode messages: {len(god_mode_analysis['user_messages_in_god_mode'])}")
    print(
        f"⚠ Potentially ignored messages: {len(god_mode_analysis['ignored_messages'])}"
    )

    # Recommendations
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)
    if dice_analysis["entries_without_dice_but_should_have"]:
        print(
            "1. Check backend logs for entries that mention dice but don't have dice_rolls field"
        )
        print("2. Verify LLM is returning dice_rolls in structured_fields")
        print("3. Check if dice_rolls are being stripped in _strip_game_state_fields")
    if god_mode_analysis["ignored_messages"]:
        print("4. Check GCP logs for god mode requests that didn't get responses")
        print("5. Verify god mode agent is being invoked correctly")
        print("6. Check for errors in MCP client when processing god mode requests")


if __name__ == "__main__":
    main()
