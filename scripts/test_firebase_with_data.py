#!/usr/bin/env python3
"""
Test script to create some sample data in Firebase and then run analytics.
"""

import builtins
import contextlib
import os
import sys
import traceback
from datetime import UTC, datetime

import firebase_admin
import firebase_user_analytics
from firebase_admin import credentials, firestore


def initialize_firebase():
    """Initialize Firebase with service account key."""
    if not firebase_admin._apps:
        # Find the service account key
        script_dir = os.path.dirname(os.path.abspath(__file__))
        worktree_root = os.path.dirname(script_dir)
        project_root = os.path.dirname(worktree_root)
        firebase_key_path = os.path.join(project_root, "serviceAccountKey.json")

        if os.path.exists(firebase_key_path):
            cred = credentials.Certificate(firebase_key_path)
            firebase_admin.initialize_app(cred)
            print("✅ Firebase initialized with service account key")
        else:
            raise Exception(f"❌ Could not find Firebase key at {firebase_key_path}")

    return firestore.client()


def create_test_data(db):
    """Create some test users and campaigns for testing."""
    print("🔧 Creating test data...")

    # Test user 1
    user1_id = "test_user_analytics_1"
    user1_ref = db.collection("users").document(user1_id)

    # Create campaigns for user 1
    campaign1_ref = user1_ref.collection("campaigns").document("campaign1")
    campaign1_ref.set(
        {
            "title": "Dragon Quest Adventure",
            "created_at": datetime.now(UTC),
            "last_played": datetime.now(UTC),
        }
    )

    # Add story entries to campaign 1
    story_ref = campaign1_ref.collection("story")
    story_ref.add(
        {
            "actor": "user",
            "text": "I want to explore the ancient castle.",
            "timestamp": datetime.now(UTC),
        }
    )
    story_ref.add(
        {
            "actor": "gemini",
            "text": "You approach the imposing stone fortress...",
            "timestamp": datetime.now(UTC),
        }
    )
    story_ref.add(
        {
            "actor": "user",
            "text": "I draw my sword and enter.",
            "timestamp": datetime.now(UTC),
        }
    )

    # Create second campaign for user 1
    campaign2_ref = user1_ref.collection("campaigns").document("campaign2")
    campaign2_ref.set(
        {
            "title": "Pirate Adventure",
            "created_at": datetime.now(UTC),
            "last_played": datetime.now(UTC),
        }
    )

    # Add story entries to campaign 2
    story_ref2 = campaign2_ref.collection("story")
    story_ref2.add(
        {
            "actor": "user",
            "text": "I set sail for treasure island.",
            "timestamp": datetime.now(UTC),
        }
    )
    story_ref2.add(
        {
            "actor": "gemini",
            "text": "The winds fill your sails as you embark...",
            "timestamp": datetime.now(UTC),
        }
    )

    # Test user 2
    user2_id = "test_user_analytics_2"
    user2_ref = db.collection("users").document(user2_id)

    # Create one campaign for user 2
    campaign3_ref = user2_ref.collection("campaigns").document("campaign1")
    campaign3_ref.set(
        {
            "title": "Space Exploration",
            "created_at": datetime.now(UTC),
            "last_played": datetime.now(UTC),
        }
    )

    # Add many story entries to campaign 3
    story_ref3 = campaign3_ref.collection("story")
    for i in range(10):
        story_ref3.add(
            {
                "actor": "user" if i % 2 == 0 else "gemini",
                "text": f"Space adventure entry number {i + 1}",
                "timestamp": datetime.now(UTC),
            }
        )

    print("✅ Test data created successfully!")
    print(f"   - User 1 ({user1_id}): 2 campaigns, ~5 entries")
    print(f"   - User 2 ({user2_id}): 1 campaign, 10 entries")


def cleanup_test_data(db):
    """Clean up the test data."""
    print("🧹 Cleaning up test data...")

    test_users = ["test_user_analytics_1", "test_user_analytics_2"]

    for user_id in test_users:
        user_ref = db.collection("users").document(user_id)

        # Delete all campaigns and their story entries
        campaigns = user_ref.collection("campaigns").stream()
        for campaign in campaigns:
            # Delete story entries
            story_entries = campaign.reference.collection("story").stream()
            for story in story_entries:
                story.reference.delete()

            # Delete campaign
            campaign.reference.delete()

        # User document might not exist, but try to delete anyway
        with contextlib.suppress(builtins.BaseException):
            user_ref.delete()

    print("✅ Test data cleaned up!")


def main():
    """Main function to test Firebase analytics with sample data."""
    try:
        print("🔄 Initializing Firebase...")
        db = initialize_firebase()

        # Create test data
        create_test_data(db)

        # Now run our analytics script
        print("\n" + "=" * 60)
        print("🔥 RUNNING ANALYTICS ON TEST DATA")
        print("=" * 60)

        # Import and run the analytics
        sys.path.append(os.path.dirname(__file__))

        # Run the analytics
        firebase_user_analytics.main()

        print("\n" + "=" * 60)
        print("🧹 CLEANING UP TEST DATA")
        print("=" * 60)

        # Clean up
        cleanup_test_data(db)

    except Exception as e:
        print(f"❌ Error: {e}")

        traceback.print_exc()


if __name__ == "__main__":
    main()
