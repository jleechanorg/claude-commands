#!/usr/bin/env python3
"""
Show top 10 users with campaign details and story snippets.
"""

import os
import traceback

import firebase_admin
from firebase_admin import credentials, firestore


def initialize_firebase():
    """Initialize Firebase with service account key."""
    if not firebase_admin._apps:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        worktree_root = os.path.dirname(script_dir)
        project_root = os.path.dirname(worktree_root)
        firebase_key_path = os.path.join(project_root, "serviceAccountKey.json")

        if os.path.exists(firebase_key_path):
            cred = credentials.Certificate(firebase_key_path)
            firebase_admin.initialize_app(cred)
        else:
            raise Exception("❌ Could not find Firebase key")

    return firestore.client()


def get_all_users(db):
    """Get all user IDs using the correct method."""
    users_ref = db.collection("users")
    user_docs = users_ref.list_documents()
    return [doc.id for doc in user_docs]


def analyze_user_with_details(db, user_id):
    """Analyze user with campaign details and story snippets."""
    user_ref = db.collection("users").document(user_id)
    campaigns = list(user_ref.collection("campaigns").stream())

    campaign_details = []
    total_entries = 0

    for campaign in campaigns:
        campaign_data = campaign.to_dict()
        campaign_id = campaign.id

        # Get story entries
        stories = list(campaign.reference.collection("story").stream())
        entry_count = len(stories)
        total_entries += entry_count

        # Get first few story snippets
        story_snippets = []
        for story in stories[:3]:  # First 3 entries
            story_data = story.to_dict()
            snippet = {
                "actor": story_data.get("actor", "unknown"),
                "text": story_data.get("text", "")[:100] + "..."
                if len(story_data.get("text", "")) > 100
                else story_data.get("text", ""),
            }
            story_snippets.append(snippet)

        campaign_info = {
            "id": campaign_id,
            "title": campaign_data.get("title", "Untitled"),
            "entry_count": entry_count,
            "created_at": campaign_data.get("created_at"),
            "story_snippets": story_snippets,
        }
        campaign_details.append(campaign_info)

    # Sort campaigns by entry count
    campaign_details.sort(key=lambda x: x["entry_count"], reverse=True)

    return {
        "user_id": user_id,
        "total_campaigns": len(campaigns),
        "total_entries": total_entries,
        "campaigns": campaign_details,
    }


def show_top_users():
    """Show top 10 users with detailed campaign information."""
    db = initialize_firebase()

    print("🔍 Getting all users...")
    user_ids = get_all_users(db)

    print(f"📊 Analyzing {len(user_ids)} users...")
    user_analytics = []

    for i, user_id in enumerate(user_ids, 1):
        if i % 10 == 0:
            print(f"   Processed {i}/{len(user_ids)} users...")

        user_data = analyze_user_with_details(db, user_id)
        if user_data["total_campaigns"] > 0:  # Only include users with campaigns
            user_analytics.append(user_data)

    # Sort by total activity (campaigns + entries)
    user_analytics.sort(
        key=lambda x: x["total_campaigns"] + x["total_entries"], reverse=True
    )

    print("\n" + "=" * 80)
    print("🏆 TOP 10 USERS WITH CAMPAIGN DETAILS")
    print("=" * 80)

    for i, user in enumerate(user_analytics[:10], 1):
        print(f"\n#{i} USER: {user['user_id']}")
        print(
            f"   📊 {user['total_campaigns']} campaigns, {user['total_entries']} total entries"
        )
        print("   📝 Top Campaigns:")

        for j, campaign in enumerate(user["campaigns"][:3], 1):  # Show top 3 campaigns
            print(
                f"      {j}. '{campaign['title']}' - {campaign['entry_count']} entries"
            )

            # Show story snippets
            if campaign["story_snippets"]:
                print("         Story snippets:")
                for k, snippet in enumerate(campaign["story_snippets"], 1):
                    print(f"           {k}. {snippet['actor']}: {snippet['text']}")
            else:
                print("         (No story entries)")

        if len(user["campaigns"]) > 3:
            print(f"      ... and {len(user['campaigns']) - 3} more campaigns")

        print("-" * 60)


def main():
    """Main function."""
    try:
        show_top_users()
    except Exception as e:
        print(f"❌ Error: {e}")

        traceback.print_exc()


if __name__ == "__main__":
    main()
