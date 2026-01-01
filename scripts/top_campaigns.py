#!/usr/bin/env python3
"""
Top Campaigns Query Tool

Queries Firebase for the longest (most entries) campaigns within a date range.
Counts story subcollection entries for accurate entry counts.

Usage:
    python scripts/top_campaigns.py --days 14 --exclude "jleechan*" --top 10
    python scripts/top_campaigns.py --email kevinzsalleh@gmail.com
"""

import argparse
import fnmatch
import os
import sys
from datetime import datetime, timedelta, timezone

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Firebase credentials and apply clock skew fix
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.expanduser('~/serviceAccountKey.json')
os.environ['WORLDAI_DEV_MODE'] = 'true'

from mvp_site.clock_skew_credentials import apply_clock_skew_patch
apply_clock_skew_patch()

import firebase_admin
from firebase_admin import auth, credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter


def init_firebase():
    """Initialize Firebase connection."""
    if not firebase_admin._apps:
        cred = credentials.Certificate(os.path.expanduser('~/serviceAccountKey.json'))
        firebase_admin.initialize_app(cred)
    return firestore.client()


def get_user_email(uid: str, cache: dict) -> str:
    """Get user email from Firebase Auth with caching."""
    if uid not in cache:
        try:
            user_record = auth.get_user(uid)
            cache[uid] = user_record.email or ''
        except Exception:
            cache[uid] = ''
    return cache[uid]


def count_story_entries(campaign_ref) -> int:
    """Count entries in the story subcollection."""
    return sum(1 for _ in campaign_ref.collection('story').stream())


def query_top_campaigns(
    days: int = 14,
    exclude_pattern: str = None,
    include_email: str = None,
    top_n: int = 10,
    verbose: bool = False,
    require_email: bool = False
):
    """
    Query top campaigns by entry count.

    Args:
        days: Number of days to look back
        exclude_pattern: Glob pattern for emails to exclude (e.g., "jleechan*")
        include_email: Only include this specific email
        top_n: Number of results to return
        verbose: Print progress messages
        require_email: Only include campaigns from users with email (skip anonymous)
    """
    db = init_firebase()
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

    if verbose:
        print(f"Querying campaigns from last {days} days (since {cutoff_date.strftime('%Y-%m-%d')})...")

    results = []
    total_users = 0
    total_campaigns = 0

    # Iterate through Firebase Auth users (not Firestore users collection!)
    # This ensures we find campaigns even when user doc doesn't exist
    for user in auth.list_users().iterate_all():
        total_users += 1
        uid = user.uid
        email = user.email or ''

        # Filter by include_email if specified
        if include_email and email != include_email:
            continue

        # Filter by exclude_pattern if specified
        if exclude_pattern and email and fnmatch.fnmatch(email, exclude_pattern):
            continue

        # Skip anonymous users if require_email is set
        if require_email and not email:
            continue

        if verbose and total_users % 50 == 0:
            print(f"  Scanned {total_users} users, {total_campaigns} campaigns...")

        # Query nested campaigns for this user
        campaigns_ref = db.collection('users').document(uid).collection('campaigns')
        try:
            campaigns = campaigns_ref.where(
                filter=FieldFilter('last_played', '>=', cutoff_date)
            ).stream()

            for camp in campaigns:
                total_campaigns += 1
                data = camp.to_dict()

                # Count story entries
                entry_count = count_story_entries(camp.reference)

                results.append({
                    'id': camp.id,
                    'title': data.get('title', 'Untitled'),
                    'email': email,
                    'entries': entry_count,
                    'created_at': data.get('created_at'),
                    'last_played': data.get('last_played'),
                })
        except Exception:
            pass  # Skip users with no campaigns subcollection

    if verbose:
        print(f"Scanned {total_users} users, {total_campaigns} campaigns, {len(results)} match filters")

    # Sort by entries descending (handle potential None values defensively)
    results.sort(key=lambda x: x.get('entries') or 0, reverse=True)

    return results[:top_n], len(results)


def print_results(results: list, total_matched: int, days: int, exclude_pattern: str):
    """Print formatted results table."""
    filter_desc = f"excluding '{exclude_pattern}'" if exclude_pattern else "no exclusions"
    print(f"\nTop {len(results)} campaigns (last {days} days, {filter_desc}):\n")

    print(f"{'#':<3} {'Entries':<8} {'Title':<40} {'Email':<32} {'Last Played'}")
    print("-" * 115)

    for i, r in enumerate(results, 1):
        last_played = r['last_played'].strftime('%Y-%m-%d') if r['last_played'] else 'N/A'
        title = (r['title'][:38] + '..') if len(r['title']) > 40 else r['title']
        email = (r['email'][:30] + '..') if len(r['email']) > 32 else r['email']
        print(f"{i:<3} {r['entries']:<8} {title:<40} {email:<32} {last_played}")

    print(f"\nTotal matching campaigns: {total_matched}")


def main():
    parser = argparse.ArgumentParser(
        description='Query top campaigns by entry count',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Top 10 campaigns from last 2 weeks, excluding jleechan*
  python scripts/top_campaigns.py --days 14 --exclude "jleechan*" --top 10

  # All campaigns for a specific user
  python scripts/top_campaigns.py --email kevinzsalleh@gmail.com --top 50

  # Top 20 campaigns from last month, no exclusions
  python scripts/top_campaigns.py --days 30 --top 20
        """
    )

    parser.add_argument('--days', type=int, default=14,
                        help='Number of days to look back (default: 14)')
    parser.add_argument('--exclude', type=str, default=None,
                        help='Glob pattern for emails to exclude (e.g., "jleechan*")')
    parser.add_argument('--email', type=str, default=None,
                        help='Only include campaigns from this email')
    parser.add_argument('--top', type=int, default=10,
                        help='Number of top results to show (default: 10)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Print progress messages')
    parser.add_argument('--json', action='store_true',
                        help='Output as JSON instead of table')
    parser.add_argument('--require-email', action='store_true',
                        help='Only show campaigns from users with email (skip anonymous)')

    args = parser.parse_args()

    results, total = query_top_campaigns(
        days=args.days,
        exclude_pattern=args.exclude,
        include_email=args.email,
        top_n=args.top,
        verbose=args.verbose,
        require_email=args.require_email
    )

    if args.json:
        import json
        # Convert datetime objects for JSON serialization
        for r in results:
            if r['created_at']:
                r['created_at'] = r['created_at'].isoformat()
            if r['last_played']:
                r['last_played'] = r['last_played'].isoformat()
        print(json.dumps({'results': results, 'total_matched': total}, indent=2))
    else:
        print_results(results, total, args.days, args.exclude)


if __name__ == '__main__':
    main()
