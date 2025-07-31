#!/usr/bin/env python3
"""
Firebase Collection Group Analytics Script

Uses collection group queries to analyze all campaigns and story entries
across all users in the Firebase database.
"""

import csv
import os
import sys
import traceback
from collections import defaultdict
from datetime import datetime

import firebase_admin
from firebase_admin import credentials, firestore


def initialize_firebase():
    """Initialize Firebase connection using the same pattern as live tests."""
    if not firebase_admin._apps:
        try:
            # First try to find serviceAccountKey.json like the live tests
            script_dir = os.path.dirname(os.path.abspath(__file__))
            worktree_root = os.path.dirname(script_dir)  # Go up one level from scripts/
            project_root = os.path.dirname(
                worktree_root
            )  # Go up one more level from worktree_tweaks/
            firebase_key_path = os.path.join(project_root, "serviceAccountKey.json")

            if os.path.exists(firebase_key_path):
                cred = credentials.Certificate(firebase_key_path)
                firebase_admin.initialize_app(cred)
                print(
                    f"✅ Firebase initialized with service account key from {firebase_key_path}"
                )
            else:
                # Fallback to default credentials
                firebase_admin.initialize_app()
                print("✅ Firebase initialized with default credentials")
        except Exception as e:
            print(f"❌ Failed to initialize Firebase: {e}")
            raise

    return firestore.client()


def analyze_with_collection_groups(db):
    """Use collection groups to analyze all campaigns and stories across all users."""

    print("🔍 Using collection group queries to analyze data...")

    # Dictionary to store user analytics
    user_data = defaultdict(
        lambda: {
            "user_id": None,
            "total_campaigns": 0,
            "total_entries": 0,
            "campaigns": {},
            "most_active_campaign": None,
            "avg_entries_per_campaign": 0,
        }
    )

    # Query all campaigns using collection group
    print("📋 Querying all campaigns across all users...")
    campaigns_group = db.collection_group("campaigns")
    campaign_count = 0

    for campaign_doc in campaigns_group.stream():
        campaign_count += 1
        campaign_data = campaign_doc.to_dict()
        campaign_id = campaign_doc.id

        # Extract user ID from the document path
        # Path format: users/{user_id}/campaigns/{campaign_id}
        path_parts = campaign_doc.reference.path.split("/")
        if (
            len(path_parts) >= 4
            and path_parts[0] == "users"
            and path_parts[2] == "campaigns"
        ):
            user_id = path_parts[1]

            # Initialize user data
            if user_data[user_id]["user_id"] is None:
                user_data[user_id]["user_id"] = user_id

            # Store campaign info
            campaign_info = {
                "campaign_id": campaign_id,
                "title": campaign_data.get("title", "Untitled"),
                "entry_count": 0,  # Will be updated when we count stories
                "created_at": campaign_data.get("created_at"),
                "last_played": campaign_data.get("last_played"),
            }

            user_data[user_id]["campaigns"][campaign_id] = campaign_info
            user_data[user_id]["total_campaigns"] += 1

            if campaign_count % 10 == 0:
                print(f"   Processed {campaign_count} campaigns...")

    print(f"✅ Found {campaign_count} total campaigns across all users")

    # Query all story entries using collection group
    print("📖 Querying all story entries across all campaigns...")
    story_group = db.collection_group("story")
    story_count = 0

    for story_doc in story_group.stream():
        story_count += 1

        # Extract user ID and campaign ID from the document path
        # Path format: users/{user_id}/campaigns/{campaign_id}/story/{story_id}
        path_parts = story_doc.reference.path.split("/")
        if (
            len(path_parts) >= 6
            and path_parts[0] == "users"
            and path_parts[2] == "campaigns"
            and path_parts[4] == "story"
        ):
            user_id = path_parts[1]
            campaign_id = path_parts[3]

            # Update entry count for this campaign
            if user_id in user_data and campaign_id in user_data[user_id]["campaigns"]:
                user_data[user_id]["campaigns"][campaign_id]["entry_count"] += 1
                user_data[user_id]["total_entries"] += 1

            if story_count % 100 == 0:
                print(f"   Processed {story_count} story entries...")

    print(f"✅ Found {story_count} total story entries across all campaigns")

    # Calculate aggregated statistics for each user
    print("📊 Calculating user statistics...")
    user_analytics = []

    for user_id, data in user_data.items():
        # Convert campaigns dict to list
        data["campaigns"] = list(data["campaigns"].values())

        # Find most active campaign
        if data["campaigns"]:
            data["most_active_campaign"] = max(
                data["campaigns"], key=lambda x: x["entry_count"]
            )
            data["avg_entries_per_campaign"] = (
                data["total_entries"] / data["total_campaigns"]
                if data["total_campaigns"] > 0
                else 0
            )

        user_analytics.append(data)

    return user_analytics


def generate_report(user_analytics):
    """Generate a formatted report of user analytics."""
    print("\n" + "=" * 80)
    print("🔥 FIREBASE COLLECTION GROUP ANALYTICS REPORT")
    print("=" * 80)
    print(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total users analyzed: {len(user_analytics)}")
    print()

    # Sort by total data volume (campaigns + entries)
    sorted_users = sorted(
        user_analytics,
        key=lambda x: (x["total_campaigns"] + x["total_entries"]),
        reverse=True,
    )

    # Summary statistics
    total_campaigns = sum(user["total_campaigns"] for user in user_analytics)
    total_entries = sum(user["total_entries"] for user in user_analytics)

    print("📊 SUMMARY STATISTICS")
    print("-" * 40)
    print(f"Total campaigns across all users: {total_campaigns}")
    print(f"Total entries across all users: {total_entries}")
    if len(user_analytics) > 0:
        print(
            f"Average campaigns per user: {total_campaigns / len(user_analytics):.2f}"
        )
        print(f"Average entries per user: {total_entries / len(user_analytics):.2f}")
    else:
        print("No users found - averages cannot be calculated")
    print()

    # Top 10 most active users
    print("🏆 TOP USERS BY ACTIVITY")
    print("-" * 40)
    print(
        f"{'Rank':<4} {'User ID':<30} {'Campaigns':<10} {'Entries':<8} {'Avg/Campaign':<12} {'Most Active Campaign'}"
    )
    print("-" * 100)

    for i, user in enumerate(sorted_users[:10], 1):
        most_active = user["most_active_campaign"]
        most_active_str = f"{most_active['title'][:25]}..." if most_active else "N/A"
        if most_active and len(most_active["title"]) <= 25:
            most_active_str = most_active["title"]

        # Truncate user ID if too long
        user_id_display = (
            user["user_id"][:27] + "..."
            if len(user["user_id"]) > 30
            else user["user_id"]
        )

        print(
            f"{i:<4} {user_id_display:<30} {user['total_campaigns']:<10} "
            f"{user['total_entries']:<8} {user['avg_entries_per_campaign']:<12.1f} {most_active_str}"
        )

    print()

    # Detailed breakdown for top 3 users
    print("🔍 DETAILED BREAKDOWN - TOP 3 USERS")
    print("-" * 40)

    for i, user in enumerate(sorted_users[:3], 1):
        print(f"\n{i}. User: {user['user_id']}")
        print(f"   Total Campaigns: {user['total_campaigns']}")
        print(f"   Total Entries: {user['total_entries']}")
        print(f"   Average Entries/Campaign: {user['avg_entries_per_campaign']:.1f}")

        if user["most_active_campaign"]:
            mac = user["most_active_campaign"]
            print(
                f"   Most Active Campaign: {mac['title']} ({mac['entry_count']} entries)"
            )

        # Show top 3 campaigns for this user
        top_campaigns = sorted(
            user["campaigns"], key=lambda x: x["entry_count"], reverse=True
        )[:3]
        print("   Top Campaigns:")
        for j, campaign in enumerate(top_campaigns, 1):
            print(f"     {j}. {campaign['title']} - {campaign['entry_count']} entries")

    print("\n" + "=" * 80)


def export_to_csv(
    user_analytics, filename="analysis/firebase_collection_group_analytics.csv"
):
    """Export analytics data to CSV file."""

    # Sort by total activity
    sorted_users = sorted(
        user_analytics,
        key=lambda x: (x["total_campaigns"] + x["total_entries"]),
        reverse=True,
    )

    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "rank",
            "user_id",
            "total_campaigns",
            "total_entries",
            "avg_entries_per_campaign",
            "most_active_campaign_title",
            "most_active_campaign_entries",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for i, user in enumerate(sorted_users, 1):
            mac = user["most_active_campaign"]
            row = {
                "rank": i,
                "user_id": user["user_id"],
                "total_campaigns": user["total_campaigns"],
                "total_entries": user["total_entries"],
                "avg_entries_per_campaign": round(user["avg_entries_per_campaign"], 2),
                "most_active_campaign_title": mac["title"] if mac else "N/A",
                "most_active_campaign_entries": mac["entry_count"] if mac else 0,
            }
            writer.writerow(row)

    print(f"📄 Analytics data exported to {filename}")


def main():
    """Main function to run the analytics."""
    try:
        print("🔄 Initializing Firebase connection...")
        db = initialize_firebase()

        # Run collection group analysis
        user_analytics = analyze_with_collection_groups(db)

        print(f"\n✅ Analysis complete! Found {len(user_analytics)} users with data.")

        if user_analytics:
            # Generate report
            generate_report(user_analytics)

            # Export to CSV
            export_to_csv(user_analytics)
        else:
            print("\n⚠️  No user data found in the database.")
            print("   This could mean:")
            print("   - The database is empty")
            print("   - Collection group queries need to be enabled in Firebase")
            print("   - The service account lacks necessary permissions")

        print("\n✅ Script execution complete!")

    except Exception as e:
        print(f"\n❌ Error: {e}")

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
