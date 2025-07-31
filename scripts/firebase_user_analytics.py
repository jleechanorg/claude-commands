#!/usr/bin/env python3
"""
Firebase User Analytics Script

Analyzes Firebase database to count campaigns and entries per user.
Generates a report sorted by user activity (most active first).
"""

import csv
import os
import sys
import traceback
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


def get_all_users(db):
    """Get all user IDs from the users collection."""
    users_ref = db.collection("users")

    # Use list_documents() which returns all document references,
    # even if they only contain subcollections (which is our case)
    try:
        user_docs = users_ref.list_documents()
        user_ids = []
        for doc in user_docs:
            user_ids.append(doc.id)
            print(f"   Found user: {doc.id}")

        print(f"✅ Found {len(user_ids)} users total")
        return user_ids

    except Exception as e:
        print(f"❌ Error getting users: {e}")
        return []


def analyze_user_campaigns(db, user_id):
    """Analyze campaigns and entries for a specific user."""
    user_data = {
        "user_id": user_id,
        "total_campaigns": 0,
        "total_entries": 0,
        "campaigns": [],
        "most_active_campaign": None,
        "avg_entries_per_campaign": 0,
    }

    # Get all campaigns for this user
    campaigns_ref = db.collection("users").document(user_id).collection("campaigns")
    campaigns = campaigns_ref.stream()

    max_entries = 0
    most_active_campaign = None

    for campaign in campaigns:
        campaign_data = campaign.to_dict()
        campaign_id = campaign.id

        # Count story entries for this campaign
        story_ref = campaigns_ref.document(campaign_id).collection("story")
        story_entries = story_ref.stream()

        entry_count = sum(1 for _ in story_entries)

        campaign_info = {
            "campaign_id": campaign_id,
            "title": campaign_data.get("title", "Untitled"),
            "entry_count": entry_count,
            "created_at": campaign_data.get("created_at"),
            "last_played": campaign_data.get("last_played"),
        }

        user_data["campaigns"].append(campaign_info)
        user_data["total_entries"] += entry_count

        # Track most active campaign
        if entry_count > max_entries:
            max_entries = entry_count
            most_active_campaign = campaign_info

    user_data["total_campaigns"] = len(user_data["campaigns"])
    user_data["most_active_campaign"] = most_active_campaign

    if user_data["total_campaigns"] > 0:
        user_data["avg_entries_per_campaign"] = (
            user_data["total_entries"] / user_data["total_campaigns"]
        )

    return user_data


def generate_report(user_analytics):
    """Generate a formatted report of user analytics."""
    print("=" * 80)
    print("🔥 FIREBASE USER ANALYTICS REPORT")
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
        f"{'Rank':<4} {'User ID':<20} {'Campaigns':<10} {'Entries':<8} {'Avg/Campaign':<12} {'Most Active Campaign'}"
    )
    print("-" * 80)

    for i, user in enumerate(sorted_users[:10], 1):
        most_active = user["most_active_campaign"]
        most_active_str = f"{most_active['title'][:20]}..." if most_active else "N/A"
        if most_active and len(most_active["title"]) <= 20:
            most_active_str = most_active["title"]

        print(
            f"{i:<4} {user['user_id']:<20} {user['total_campaigns']:<10} "
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


def export_to_csv(user_analytics, filename="firebase_user_analytics.csv"):
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

        print("📋 Fetching all users...")
        user_ids = get_all_users(db)
        print(f"   Found {len(user_ids)} users")

        print("🔍 Analyzing user data...")
        user_analytics = []

        # Limit to first 10 users for faster processing
        limited_user_ids = user_ids[:10] if len(user_ids) > 10 else user_ids
        print(
            f"   Processing first {len(limited_user_ids)} of {len(user_ids)} users for performance..."
        )

        for i, user_id in enumerate(limited_user_ids, 1):
            print(f"   Analyzing user {i}/{len(limited_user_ids)}: {user_id}")
            user_data = analyze_user_campaigns(db, user_id)
            user_analytics.append(user_data)
            if user_data["total_campaigns"] > 0:
                print(
                    f"     ✅ {user_data['total_campaigns']} campaigns, {user_data['total_entries']} entries"
                )

        print("📊 Generating report...")
        generate_report(user_analytics)

        # Export to CSV
        export_to_csv(user_analytics)

        print("\n✅ Analysis complete!")

    except Exception as e:
        print(f"❌ Error: {e}")

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
