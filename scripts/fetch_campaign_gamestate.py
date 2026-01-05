#!/usr/bin/env python3
"""
Fetch and display game state data from Firestore for a specific campaign.

Uses shared code from mvp_site for equipment/stats/spells extraction to ensure
consistency with the production API endpoints.

Usage:
    WORLDAI_DEV_MODE=true python scripts/fetch_campaign_gamestate.py <campaign_id>

Example:
    WORLDAI_DEV_MODE=true python scripts/fetch_campaign_gamestate.py kuXKa6vrYY6P99MfhWBn
"""

import os
import sys

# Add project root to path for mvp_site imports
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, project_root)

# CRITICAL: Apply clock skew patch BEFORE importing Firebase
from mvp_site.clock_skew_credentials import apply_clock_skew_patch
apply_clock_skew_patch()

import firebase_admin
from firebase_admin import credentials, firestore

# Import shared display modules from mvp_site
from mvp_site import equipment_display
from mvp_site import stats_display
from mvp_site.game_state import GameState
from mvp_site.main import get_spell_level  # Spell level lookup for legacy string data


def init_firebase():
    """Initialize Firebase if not already initialized."""
    if not firebase_admin._apps:
        cred_path = os.path.expanduser("~/serviceAccountKey.json")
        if not os.path.exists(cred_path):
            print(f"Error: Firebase credentials not found at {cred_path}")
            sys.exit(1)
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    return firestore.client()


# Known user UID (jleechan@gmail.com) - avoids auth lookup
PRIMARY_USER_UID = "vnLp2G3m21PJL6kxcuAqmWSOtm73"


def find_campaign(db, campaign_id):
    """Find a campaign by ID - try known user first, then search all users."""
    # Try primary user first (most likely)
    uid = PRIMARY_USER_UID
    print(f"Checking primary user: {uid}")

    campaign_ref = db.collection("users").document(uid).collection("campaigns").document(campaign_id)
    campaign_doc = campaign_ref.get()

    if campaign_doc.exists:
        return uid, campaign_doc.to_dict()

    print("Campaign not found for primary user, searching all users...")

    # Fall back to iterating through users
    users_ref = db.collection("users")

    for user_doc in users_ref.stream():
        user_id = user_doc.id
        if user_id == uid:
            continue  # Already checked
        campaign_ref = users_ref.document(user_id).collection("campaigns").document(campaign_id)
        campaign_doc = campaign_ref.get()

        if campaign_doc.exists:
            return user_id, campaign_doc.to_dict()

    return None, None


def get_game_state(db, user_id, campaign_id):
    """Fetch the current game state for a campaign."""
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


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/fetch_campaign_gamestate.py <campaign_id>")
        sys.exit(1)

    campaign_id = sys.argv[1]
    print(f"🔍 Looking up campaign: {campaign_id}")

    db = init_firebase()

    # Find the campaign
    user_id, campaign_data = find_campaign(db, campaign_id)

    if not user_id:
        print(f"❌ Campaign {campaign_id} not found")
        sys.exit(1)

    print(f"✅ Found campaign owned by user: {user_id}")
    print(f"📋 Campaign title: {campaign_data.get('title', 'Untitled')}")

    # Get game state
    game_state = get_game_state(db, user_id, campaign_id)

    if not game_state:
        print("❌ No game state found for this campaign")
        sys.exit(1)

    # Convert to GameState object for shared module compatibility
    game_state_obj = GameState(**game_state)

    # ==========================================================================
    # EQUIPMENT SUMMARY (using shared equipment_display module)
    # ==========================================================================
    print("\n" + "=" * 60)
    print("📦 EQUIPMENT (matches GET /api/campaigns/{id}/equipment)")
    print("=" * 60)

    equipment_list = equipment_display.extract_equipment_display(game_state_obj)
    if equipment_list:
        equipment_summary = equipment_display.build_equipment_summary(equipment_list, "Your Equipment")
        print(equipment_summary)
    else:
        print("No equipment found")

    # ==========================================================================
    # STATS SUMMARY (using shared stats_display module)
    # ==========================================================================
    print("\n" + "=" * 60)
    print("📊 STATS (matches GET /api/campaigns/{id}/stats)")
    print("=" * 60)

    stats_summary = stats_display.build_stats_summary(game_state)
    print(stats_summary)

    # ==========================================================================
    # SPELLS SUMMARY (using shared stats_display module)
    # ==========================================================================
    print("\n" + "=" * 60)
    print("🔮 SPELLS (matches GET /api/campaigns/{id}/spells)")
    print("=" * 60)

    spells_summary = stats_display.build_spells_summary(game_state, get_spell_level)
    print(spells_summary)

    # ==========================================================================
    # API ENDPOINT SUMMARY
    # ==========================================================================
    print("\n" + "=" * 60)
    print("✅ All summaries use shared code with production API")
    print("=" * 60)
    print("  GET /api/campaigns/{id}/equipment → equipment_display module")
    print("  GET /api/campaigns/{id}/stats     → stats_display module")
    print("  GET /api/campaigns/{id}/spells    → stats_display module")


if __name__ == "__main__":
    main()
