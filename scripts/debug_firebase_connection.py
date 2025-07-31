#!/usr/bin/env python3
"""
Debug Firebase connection to see what's actually in the database.
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
            print(f"✅ Connected to project: {cred.project_id}")
        else:
            raise Exception("❌ Could not find Firebase key")

    return firestore.client()


def debug_firebase_state(db):
    """Debug current Firebase state."""
    print("🔍 Firebase Debug Information")
    print("=" * 50)

    # Check root collections
    print("📁 Root collections:")
    collections = list(db.collections())
    for collection in collections:
        print(f"   - {collection.id}")

    if not collections:
        print("   No collections found!")
        return

    # Check users collection specifically
    users_ref = db.collection("users")
    print("\n👥 Users collection details:")
    print(f"   Collection path: {users_ref._path}")

    # Try different ways to get users
    users_list = list(users_ref.stream())
    print(f"   Users found via stream(): {len(users_list)}")

    # Try to get the test user specifically
    test_user_id = "test-integration-user"
    test_user_ref = users_ref.document(test_user_id)
    test_user_doc = test_user_ref.get()

    print(f"\n🔍 Checking specific test user: {test_user_id}")
    print(f"   Document exists: {test_user_doc.exists}")

    if test_user_doc.exists:
        print(f"   Document data: {test_user_doc.to_dict()}")

        # Check campaigns for this user
        campaigns_ref = test_user_ref.collection("campaigns")
        campaigns = list(campaigns_ref.stream())
        print(f"   Campaigns: {len(campaigns)}")

        for campaign in campaigns:
            print(f"     Campaign {campaign.id}: {campaign.to_dict()}")

            # Check stories for this campaign
            stories = list(campaign.reference.collection("story").stream())
            print(f"       Stories: {len(stories)}")

    # Also try to list documents with a limit
    print("\n📝 First 10 documents in users collection:")
    docs = users_ref.limit(10).stream()
    doc_count = 0
    for doc in docs:
        doc_count += 1
        print(f"   Document {doc_count}: {doc.id}")

    if doc_count == 0:
        print("   No documents found")


def main():
    """Debug Firebase connection."""
    try:
        db = initialize_firebase()
        debug_firebase_state(db)

    except Exception as e:
        print(f"❌ Error: {e}")

        traceback.print_exc()


if __name__ == "__main__":
    main()
