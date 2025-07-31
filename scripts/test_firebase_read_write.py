#!/usr/bin/env python3
"""
Test Firebase read/write operations by inserting data and reading it back.
"""

import os
import sys
import traceback
import uuid
from datetime import UTC, datetime

import firebase_admin
import firebase_user_analytics
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
            print(f"✅ Connected to Firebase project: {cred.project_id}")
        else:
            raise Exception("❌ Could not find Firebase key")

    return firestore.client()


def test_write_and_read(db):
    """Test writing data and reading it back immediately."""
    print("\n🔧 Testing Firebase Write Operations...")

    # Generate unique test user ID
    test_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    campaign_id = f"test_campaign_{uuid.uuid4().hex[:8]}"

    print(f"   Creating test user: {test_user_id}")
    print(f"   Creating test campaign: {campaign_id}")

    # Create user and campaign
    user_ref = db.collection("users").document(test_user_id)
    campaign_ref = user_ref.collection("campaigns").document(campaign_id)

    # Write campaign data
    campaign_data = {
        "title": "Test Campaign for Read/Write Verification",
        "created_at": datetime.now(UTC),
        "last_played": datetime.now(UTC),
        "test_field": "firebase_test_value",
    }

    print("   Writing campaign data...")
    campaign_ref.set(campaign_data)
    print("   ✅ Campaign data written")

    # Write story entries
    story_ref = campaign_ref.collection("story")
    story_entries = [
        {"actor": "user", "text": "Test story entry 1", "timestamp": datetime.now(UTC)},
        {
            "actor": "gemini",
            "text": "Test story entry 2",
            "timestamp": datetime.now(UTC),
        },
        {"actor": "user", "text": "Test story entry 3", "timestamp": datetime.now(UTC)},
    ]

    print("   Writing story entries...")
    story_refs = []
    for i, entry in enumerate(story_entries):
        doc_ref = story_ref.add(entry)
        story_refs.append(doc_ref[1])
        print(f"     Entry {i + 1}: {doc_ref[1].id}")

    print("   ✅ All story entries written")

    return test_user_id, campaign_id


def verify_data_exists(db, test_user_id, campaign_id):
    """Verify the data we just wrote can be read back."""
    print("\n🔍 Testing Firebase Read Operations...")

    # Read user data
    user_ref = db.collection("users").document(test_user_id)
    campaigns_ref = user_ref.collection("campaigns")

    print(f"   Reading campaigns for user: {test_user_id}")
    campaigns = list(campaigns_ref.stream())
    print(f"   ✅ Found {len(campaigns)} campaigns")

    if len(campaigns) == 0:
        print("   ❌ ERROR: No campaigns found!")
        return False

    # Read specific campaign
    campaign_ref = campaigns_ref.document(campaign_id)
    campaign_doc = campaign_ref.get()

    if not campaign_doc.exists:
        print(f"   ❌ ERROR: Campaign {campaign_id} not found!")
        return False

    campaign_data = campaign_doc.to_dict()
    print(f"   ✅ Campaign found: {campaign_data['title']}")
    print(f"   ✅ Test field: {campaign_data.get('test_field', 'MISSING')}")

    # Read story entries
    story_ref = campaign_ref.collection("story")
    stories = list(story_ref.stream())
    print(f"   ✅ Found {len(stories)} story entries")

    for i, story in enumerate(stories):
        story_data = story.to_dict()
        print(
            f"     Entry {i + 1}: {story_data['actor']} - {story_data['text'][:30]}..."
        )

    if len(stories) == 0:
        print("   ❌ ERROR: No story entries found!")
        return False

    return True


def test_analytics_on_test_data(db, test_user_id):
    """Test our analytics functions on the test data."""
    print("\n📊 Testing Analytics Functions...")

    # Import our analytics functions

    sys.path.append(os.path.dirname(__file__))

    # Get all users (should include our test user)
    user_ids = firebase_user_analytics.get_all_users(db)
    print(f"   Total users found: {len(user_ids)}")

    if test_user_id in user_ids:
        print(f"   ✅ Test user {test_user_id} found in analytics!")

        # Analyze the test user
        user_data = firebase_user_analytics.analyze_user_campaigns(db, test_user_id)
        print("   ✅ User analysis complete:")
        print(f"     Campaigns: {user_data['total_campaigns']}")
        print(f"     Entries: {user_data['total_entries']}")
        if user_data["most_active_campaign"]:
            print(f"     Most active: {user_data['most_active_campaign']['title']}")

        return True
    print(f"   ❌ Test user {test_user_id} NOT found in analytics")
    print(f"   Found users: {user_ids}")
    return False


def cleanup_test_data(db, test_user_id, campaign_id):
    """Clean up the test data."""
    print("\n🧹 Cleaning up test data...")

    user_ref = db.collection("users").document(test_user_id)
    campaign_ref = user_ref.collection("campaigns").document(campaign_id)

    # Delete story entries
    story_entries = list(campaign_ref.collection("story").stream())
    for story in story_entries:
        story.reference.delete()
    print(f"   ✅ Deleted {len(story_entries)} story entries")

    # Delete campaign
    campaign_ref.delete()
    print("   ✅ Deleted campaign")

    print(f"   ✅ Cleanup complete for user {test_user_id}")


def main():
    """Main test function."""
    test_user_id = None
    campaign_id = None

    try:
        print("🚀 Starting Firebase Read/Write Test...")
        db = initialize_firebase()

        # Test write operations
        test_user_id, campaign_id = test_write_and_read(db)

        # Test read operations
        read_success = verify_data_exists(db, test_user_id, campaign_id)

        if not read_success:
            print("\n❌ READ TEST FAILED!")
            return

        # Test analytics on the data
        analytics_success = test_analytics_on_test_data(db, test_user_id)

        if analytics_success:
            print("\n✅ ALL TESTS PASSED!")
            print("   - Firebase write operations: ✅")
            print("   - Firebase read operations: ✅")
            print("   - Analytics functions: ✅")
        else:
            print("\n⚠️  ANALYTICS TEST FAILED!")
            print("   Write/Read work but analytics has issues")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")

        traceback.print_exc()

    finally:
        # Always try to clean up
        if test_user_id and campaign_id:
            try:
                cleanup_test_data(db, test_user_id, campaign_id)
            except Exception as e:
                print(f"⚠️  Cleanup error: {e}")


if __name__ == "__main__":
    main()
