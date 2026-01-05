#!/usr/bin/env python3
"""
Clean up bloated debug_info from campaign story entries.

Campaign kuXKa6vrYY6P99MfhWBn has 33MB of data, with 30MB (88.8%) being debug_info.
The bloat comes from storing full LLM context in every entry:
- raw_request_payload: ~20KB per entry
- system_instruction_text: ~8KB per entry
- raw_response_text: ~8KB per entry

This script removes these fields while preserving useful debug metadata.

Usage:
    # Dry run (default) - shows what would be cleaned
    WORLDAI_DEV_MODE=true python scripts/cleanup_debug_info.py --campaign-id kuXKa6vrYY6P99MfhWBn

    # Actually clean the data
    WORLDAI_DEV_MODE=true python scripts/cleanup_debug_info.py --campaign-id kuXKa6vrYY6P99MfhWBn --execute

    # Clean all campaigns for a user
    WORLDAI_DEV_MODE=true python scripts/cleanup_debug_info.py --all --execute
"""

import argparse
import json
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import firebase_admin
from firebase_admin import credentials, firestore

from mvp_site.clock_skew_credentials import apply_clock_skew_patch

apply_clock_skew_patch()

# Fields to remove from debug_info (the bloated ones)
BATCH_COMMIT_LIMIT = 400  # Firestore limit is 500
FIELDS_TO_REMOVE = {
    "raw_request_payload",
    "raw_response_text",
    "system_instruction_text",
}


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


def calculate_size(data):
    """Calculate JSON size of data."""
    return len(json.dumps(data, default=str))


def cleanup_campaign(db, user_id: str, campaign_id: str, execute: bool = False):  # noqa: PLR0915
    """Clean up debug_info in a campaign's story entries."""
    print(f"\n{'=' * 60}")
    print(f"Campaign: {campaign_id}")
    print(f"User: {user_id}")
    print(f"Mode: {'EXECUTE' if execute else 'DRY RUN'}")
    print("=" * 60)

    story_ref = (
        db.collection("users")
        .document(user_id)
        .collection("campaigns")
        .document(campaign_id)
        .collection("story")
    )

    entries = list(story_ref.stream())
    print(f"Total entries: {len(entries)}")

    # Analyze and optionally clean
    total_before = 0
    total_after = 0
    entries_with_debug_info = 0
    entries_cleaned = 0

    batch = db.batch()
    batch_count = 0

    for entry in entries:
        data = entry.to_dict()
        entry_size_before = calculate_size(data)
        total_before += entry_size_before

        debug_info = data.get("debug_info")
        if debug_info and isinstance(debug_info, dict):
            entries_with_debug_info += 1

            # Check if any bloated fields exist
            has_bloat = any(field in debug_info for field in FIELDS_TO_REMOVE)

            if has_bloat:
                # Create cleaned debug_info
                cleaned_debug_info = {
                    k: v for k, v in debug_info.items() if k not in FIELDS_TO_REMOVE
                }

                if execute:
                    batch.update(entry.reference, {"debug_info": cleaned_debug_info})
                    batch_count += 1
                    entries_cleaned += 1

                    # Commit batch if reaching limit
                    if batch_count >= BATCH_COMMIT_LIMIT:
                        batch.commit()
                        print(f"  Committed batch of {batch_count} updates...")
                        batch = db.batch()
                        batch_count = 0
                else:
                    entries_cleaned += 1

                # Calculate cleaned size
                cleaned_data = data.copy()
                cleaned_data["debug_info"] = cleaned_debug_info
                entry_size_after = calculate_size(cleaned_data)
            else:
                entry_size_after = entry_size_before
        else:
            entry_size_after = entry_size_before

        total_after += entry_size_after

    # Commit remaining batch
    if execute and batch_count > 0:
        batch.commit()
        print(f"  Committed final batch of {batch_count} updates...")

    # Summary
    print("\n--- Results ---")
    print(f"Entries with debug_info: {entries_with_debug_info}")
    print(f"Entries {'cleaned' if execute else 'to clean'}: {entries_cleaned}")
    size_before_mb = total_before / 1024 / 1024
    size_after_mb = total_after / 1024 / 1024
    savings_mb = (total_before - total_after) / 1024 / 1024
    savings_pct = (1 - total_after / total_before) * 100 if total_before > 0 else 0.0

    print(f"Size before: {size_before_mb:.2f} MB")
    print(f"Size after:  {size_after_mb:.2f} MB")
    print(f"Savings:     {savings_mb:.2f} MB ({savings_pct:.1f}%)")

    return {
        "campaign_id": campaign_id,
        "entries_total": len(entries),
        "entries_cleaned": entries_cleaned,
        "size_before": total_before,
        "size_after": total_after,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Clean up bloated debug_info from campaigns"
    )
    parser.add_argument("--campaign-id", help="Specific campaign ID to clean")
    parser.add_argument(
        "--all", action="store_true", help="Clean all campaigns for user"
    )
    parser.add_argument("--user-id", required=True, help="User ID to target campaigns")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually perform cleanup (default: dry run)",
    )
    args = parser.parse_args()

    if not args.campaign_id and not args.all:
        parser.error("Must specify --campaign-id or --all")

    db = init_firebase()

    if args.campaign_id:
        cleanup_campaign(db, args.user_id, args.campaign_id, args.execute)
    elif args.all:
        # Get all campaigns for user
        campaigns_ref = (
            db.collection("users").document(args.user_id).collection("campaigns")
        )
        campaigns = list(campaigns_ref.stream())
        print(f"Found {len(campaigns)} campaigns for user {args.user_id}")

        total_savings = 0
        for campaign in campaigns:
            result = cleanup_campaign(db, args.user_id, campaign.id, args.execute)
            total_savings += result["size_before"] - result["size_after"]

        print(f"\n{'=' * 60}")
        print(f"TOTAL SAVINGS: {total_savings / 1024 / 1024:.2f} MB")
        print("=" * 60)


if __name__ == "__main__":
    main()
