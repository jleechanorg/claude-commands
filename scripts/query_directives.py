#!/usr/bin/env python3
"""
Query and manage God Mode directives for campaigns.

Usage:
    # List all directives for a campaign
    python scripts/query_directives.py CAMPAIGN_ID

    # Debug why a directive wasn't saved (search god mode entries)
    python scripts/query_directives.py CAMPAIGN_ID --debug-missing "power scaling"

    # Manually add a missing directive
    python scripts/query_directives.py CAMPAIGN_ID --add "Level 9 is extremely powerful"

    # Remove a directive
    python scripts/query_directives.py CAMPAIGN_ID --drop "old rule to remove"

Environment variables required:
    WORLDAI_DEV_MODE=true
    WORLDAI_GOOGLE_APPLICATION_CREDENTIALS=~/serviceAccountKey.json
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# CRITICAL: Apply clock skew patch BEFORE importing Firebase
from mvp_site.clock_skew_credentials import apply_clock_skew_patch
apply_clock_skew_patch()

import firebase_admin
from firebase_admin import auth, credentials, firestore


def init_firebase():
    """Initialize Firebase with explicit credentials."""
    if firebase_admin._apps:
        firebase_admin.delete_app(firebase_admin.get_app())

    cred_path = os.environ.get(
        'WORLDAI_GOOGLE_APPLICATION_CREDENTIALS',
        os.path.expanduser('~/serviceAccountKey.json')
    )
    cred = credentials.Certificate(os.path.expanduser(cred_path))
    firebase_admin.initialize_app(cred)
    return firestore.client()


def get_user_uid(email: str = 'jleechan@gmail.com') -> str:
    """Get Firebase UID for user email."""
    user_record = auth.get_user_by_email(email)
    return user_record.uid


def get_campaign_ref(db, uid: str, campaign_id: str):
    """Get campaign document reference."""
    return db.collection('users').document(uid).collection('campaigns').document(campaign_id)


def list_directives(db, uid: str, campaign_id: str) -> list:
    """List all god mode directives for a campaign."""
    campaign_ref = get_campaign_ref(db, uid, campaign_id)
    game_state_ref = campaign_ref.collection('game_states').document('current_state')
    game_state = game_state_ref.get()

    if not game_state.exists:
        print(f"ERROR: Game state not found for campaign {campaign_id}")
        return []

    gs_data = game_state.to_dict()
    custom_state = gs_data.get('custom_campaign_state', {})
    directives = custom_state.get('god_mode_directives', [])

    print(f"\n{'='*60}")
    print(f"CAMPAIGN: {campaign_id}")
    print(f"DIRECTIVES: {len(directives)}")
    print(f"{'='*60}")

    if not directives:
        print("\nNo god mode directives found.")
        return []

    for i, directive in enumerate(directives, 1):
        if isinstance(directive, dict):
            rule = directive.get('rule', 'N/A')
            added = directive.get('added', 'N/A')
            print(f"\n[{i}] Added: {added}")
            print(f"    Rule: {rule}")
        else:
            print(f"\n[{i}] Rule: {directive}")

    return directives


def debug_missing_directive(db, uid: str, campaign_id: str, search_term: str):
    """Debug why a directive wasn't saved by examining god mode entries."""
    campaign_ref = get_campaign_ref(db, uid, campaign_id)
    story_ref = campaign_ref.collection('story')

    print(f"\n{'='*60}")
    print(f"DEBUGGING MISSING DIRECTIVE: '{search_term}'")
    print(f"{'='*60}")

    # Search god mode entries
    entries = list(story_ref.order_by('timestamp', direction='DESCENDING').limit(500).stream())
    god_mode_entries = []

    for entry in entries:
        data = entry.to_dict()
        text = data.get('text', '')

        # Check if it's a god mode response or contains search term
        is_god_mode = data.get('actor') == 'gemini' and 'God Mode' in text
        contains_term = search_term.lower() in text.lower()

        if is_god_mode or contains_term:
            god_mode_entries.append((entry.id, data))

    print(f"\nFound {len(god_mode_entries)} potentially relevant entries")

    for entry_id, data in god_mode_entries[:10]:
        print(f"\n{'-'*60}")
        print(f"Entry ID: {entry_id}")
        print(f"Actor: {data.get('actor')}")
        print(f"Timestamp: {data.get('timestamp')}")
        print(f"Text preview: {data.get('text', '')[:200]}...")

        # Check for raw response with directives field
        debug_info = data.get('debug_info', {})
        raw_response = debug_info.get('raw_response_text', '')

        if raw_response:
            try:
                parsed = json.loads(raw_response)
                has_directives = 'directives' in parsed

                print(f"\n  RAW RESPONSE ANALYSIS:")
                print(f"  - Has 'directives' field: {has_directives}")

                if has_directives:
                    print(f"  - Directives: {json.dumps(parsed['directives'], indent=4)}")
                else:
                    print(f"  - Top-level keys: {list(parsed.keys())}")

                    # Check for dm_notes (common mistake)
                    state_updates = parsed.get('state_updates', {})
                    dm_notes = state_updates.get('debug_info', {}).get('dm_notes', [])
                    if dm_notes:
                        print(
                            "  - dm_notes found (written to debug_info instead of directives field):"
                        )
                        for note in dm_notes:
                            print(f"      * {note}")

                    # Show god_mode_response
                    god_response = parsed.get('god_mode_response', '')
                    if god_response:
                        print(f"  - god_mode_response: {god_response[:300]}...")

            except json.JSONDecodeError:
                print(f"  - Could not parse raw response")


def add_directive(db, uid: str, campaign_id: str, rule: str):
    """Manually add a god mode directive to a campaign."""
    campaign_ref = get_campaign_ref(db, uid, campaign_id)
    game_state_ref = campaign_ref.collection('game_states').document('current_state')

    # Get current state
    game_state = game_state_ref.get()
    if not game_state.exists:
        print(f"ERROR: Game state not found for campaign {campaign_id}")
        return False

    gs_data = game_state.to_dict()
    custom_state = gs_data.get('custom_campaign_state', {})
    directives = custom_state.get('god_mode_directives', [])

    # Check for duplicates
    existing_rules = [
        d.get('rule', '').lower() if isinstance(d, dict) else str(d).lower()
        for d in directives
    ]

    if rule.lower() in existing_rules:
        print(f"Directive already exists: {rule}")
        return False

    # Add new directive
    new_directive = {
        'rule': rule,
        'added': datetime.now(timezone.utc).isoformat(),
    }
    directives.append(new_directive)

    # Update Firestore
    game_state_ref.update({
        'custom_campaign_state.god_mode_directives': directives
    })

    print(f"\n{'='*60}")
    print(f"DIRECTIVE ADDED")
    print(f"{'='*60}")
    print(f"Rule: {rule}")
    print(f"Campaign: {campaign_id}")
    print(f"Total directives: {len(directives)}")

    return True


def drop_directive(db, uid: str, campaign_id: str, rule_to_drop: str):
    """Remove a god mode directive from a campaign."""
    campaign_ref = get_campaign_ref(db, uid, campaign_id)
    game_state_ref = campaign_ref.collection('game_states').document('current_state')

    # Get current state
    game_state = game_state_ref.get()
    if not game_state.exists:
        print(f"ERROR: Game state not found for campaign {campaign_id}")
        return False

    gs_data = game_state.to_dict()
    custom_state = gs_data.get('custom_campaign_state', {})
    directives = custom_state.get('god_mode_directives', [])

    # Find and remove matching directive
    original_count = len(directives)
    rule_lower = rule_to_drop.lower()

    directives = [
        d for d in directives
        if (d.get('rule', '').lower() if isinstance(d, dict) else str(d).lower()) != rule_lower
    ]

    if len(directives) == original_count:
        print(f"Directive not found: {rule_to_drop}")
        return False

    # Update Firestore
    game_state_ref.update({
        'custom_campaign_state.god_mode_directives': directives
    })

    print(f"\n{'='*60}")
    print(f"DIRECTIVE REMOVED")
    print(f"{'='*60}")
    print(f"Removed: {rule_to_drop}")
    print(f"Remaining directives: {len(directives)}")

    return True


def main():
    parser = argparse.ArgumentParser(
        description='Query and manage God Mode directives for campaigns.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('campaign_id', help='Campaign ID to query')
    parser.add_argument('--email', default='jleechan@gmail.com',
                        help='User email (default: jleechan@gmail.com)')
    parser.add_argument('--debug-missing', metavar='TERM',
                        help='Debug why a directive containing TERM was not saved')
    parser.add_argument('--add', metavar='RULE',
                        help='Add a new directive with this rule')
    parser.add_argument('--drop', metavar='RULE',
                        help='Remove a directive matching this rule')

    args = parser.parse_args()

    # Initialize Firebase
    db = init_firebase()
    uid = get_user_uid(args.email)

    print(f"User: {args.email} ({uid})")

    if args.debug_missing:
        debug_missing_directive(db, uid, args.campaign_id, args.debug_missing)
    elif args.add:
        add_directive(db, uid, args.campaign_id, args.add)
    elif args.drop:
        drop_directive(db, uid, args.campaign_id, args.drop)
    else:
        list_directives(db, uid, args.campaign_id)


if __name__ == '__main__':
    main()
