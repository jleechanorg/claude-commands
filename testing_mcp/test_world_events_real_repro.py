#!/usr/bin/env python3
"""
REAL REPRODUCTION: World Events Extraction Bug
Bead: W2-7m1

This test uses REAL Firestore data from production campaigns to prove the bug exists.
NO MOCKS - just actual data from the campaigns.

Evidence:
- Working campaign (sAV11o87CRsN93akPi31): world_events at correct location only
- Broken campaign (STpjRuwjeUt97tpCl5nK): world_events SPLIT between correct AND wrong locations
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set up environment
os.environ['WORLDAI_DEV_MODE'] = 'true'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.expanduser('~/serviceAccountKey.json')

from mvp_site.clock_skew_credentials import apply_clock_skew_patch
apply_clock_skew_patch()

import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
cred = credentials.Certificate(os.path.expanduser('~/serviceAccountKey.json'))
try:
    firebase_admin.initialize_app(cred, {'projectId': 'worldarchitecture-ai'})
except ValueError:
    pass  # Already initialized
db = firestore.client()


def get_campaign_world_events_state(user_id: str, campaign_id: str) -> dict:
    """Get world_events from both locations in a campaign's game state."""
    gs_ref = db.collection('users').document(user_id).collection('campaigns').document(campaign_id).collection('game_states').document('current_state')
    gs = gs_ref.get()

    if not gs.exists:
        return {"error": "Campaign not found"}

    gs_data = gs.to_dict()

    # Check correct location
    top_level_we = gs_data.get('world_events', {})

    # Check wrong location (nested in custom_campaign_state)
    ccs = gs_data.get('custom_campaign_state', {})
    nested_we = ccs.get('world_events', {}) if isinstance(ccs, dict) else {}

    return {
        "player_turn": gs_data.get('player_turn'),
        "top_level_world_events": {
            "exists": bool(top_level_we),
            "turn_generated": top_level_we.get('turn_generated') if top_level_we else None,
            "event_count": len(top_level_we.get('background_events', [])) if top_level_we else 0
        },
        "nested_world_events": {
            "exists": bool(nested_we),
            "turn_generated": nested_we.get('turn_generated') if nested_we else None,
            "event_count": len(nested_we.get('background_events', [])) if nested_we else 0
        }
    }


def main():
    print("=" * 70)
    print("REAL REPRODUCTION: World Events Extraction Bug (W2-7m1)")
    print("=" * 70)
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print()

    user_id = 'vnLp2G3m21PJL6kxcuAqmWSOtm73'

    # Check WORKING campaign
    print("--- WORKING CAMPAIGN (sAV11o87CRsN93akPi31) ---")
    working = get_campaign_world_events_state(user_id, 'sAV11o87CRsN93akPi31')
    print(f"player_turn: {working['player_turn']}")
    print(f"game_state.world_events: turn={working['top_level_world_events']['turn_generated']}, events={working['top_level_world_events']['event_count']}")
    print(f"custom_campaign_state.world_events: {'EXISTS' if working['nested_world_events']['exists'] else 'None'}")
    working_ok = working['top_level_world_events']['exists'] and not working['nested_world_events']['exists']
    print(f"Status: {'CORRECT - world_events only at top level' if working_ok else 'INCORRECT'}")
    print()

    # Check BROKEN campaign
    print("--- BROKEN CAMPAIGN (STpjRuwjeUt97tpCl5nK) ---")
    broken = get_campaign_world_events_state(user_id, 'STpjRuwjeUt97tpCl5nK')
    print(f"player_turn: {broken['player_turn']}")
    print(f"game_state.world_events: turn={broken['top_level_world_events']['turn_generated']}, events={broken['top_level_world_events']['event_count']}")
    print(f"custom_campaign_state.world_events: turn={broken['nested_world_events']['turn_generated']}, events={broken['nested_world_events']['event_count']}")

    # The bug: world_events is in BOTH locations, with newer events in the WRONG location
    has_split_storage = (
        broken['top_level_world_events']['exists'] and
        broken['nested_world_events']['exists']
    )

    newer_in_wrong_location = False
    if has_split_storage:
        top_turn = broken['top_level_world_events']['turn_generated'] or 0
        nested_turn = broken['nested_world_events']['turn_generated'] or 0
        newer_in_wrong_location = nested_turn > top_turn

    print()
    print("=" * 70)
    print("BUG EVIDENCE:")
    print("=" * 70)

    if has_split_storage and newer_in_wrong_location:
        print("BUG CONFIRMED: world_events is stored in TWO locations!")
        print(f"  - Top-level (correct): turn {broken['top_level_world_events']['turn_generated']} (OLD)")
        print(f"  - Nested in custom_campaign_state (WRONG): turn {broken['nested_world_events']['turn_generated']} (RECENT)")
        print()
        print("ROOT CAUSE: LLM output world_events inside custom_campaign_state,")
        print("which was merged by update_state_with_changes but NOT extracted")
        print("by structured_fields_utils.extract_structured_fields().")
        print()
        print("RESULT: New living world events go to wrong location,")
        print("old events remain stale in correct location.")

        # Save evidence
        evidence_dir = Path('/tmp/world_events_bug_evidence')
        evidence_dir.mkdir(parents=True, exist_ok=True)

        evidence = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "working_campaign": working,
            "broken_campaign": broken,
            "bug_confirmed": True,
            "explanation": "Newer world_events in nested location proves extraction bug"
        }

        evidence_file = evidence_dir / 'real_repro_evidence.json'
        with open(evidence_file, 'w') as f:
            json.dump(evidence, f, indent=2, default=str)

        print(f"\nEvidence saved to: {evidence_file}")
        return 1  # Bug confirmed
    else:
        print("Bug NOT reproduced in current state")
        return 0


if __name__ == "__main__":
    exit(main())
