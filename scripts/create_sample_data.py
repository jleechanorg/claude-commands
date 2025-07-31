#!/usr/bin/env python3
"""
Create sample user data in Firebase for testing analytics.
"""

import os
import traceback
from datetime import UTC, datetime

import firebase_admin
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
            print("✅ Firebase initialized")
        else:
            raise Exception(f"❌ Could not find Firebase key at {firebase_key_path}")

    return firestore.client()


def create_sample_data(db):
    """Create sample user data."""
    print("🔧 Creating sample user data...")

    # User 1: Active RPG player
    user1_id = "analytics_test_user_1"
    user1_ref = db.collection("users").document(user1_id)

    # Campaign 1: Dragon Quest
    campaign1_ref = user1_ref.collection("campaigns").document("dragon_quest")
    campaign1_ref.set(
        {
            "title": "The Dragon's Hoard",
            "created_at": datetime.now(UTC),
            "last_played": datetime.now(UTC),
        }
    )

    # Add story entries
    story_ref = campaign1_ref.collection("story")
    entries = [
        "I approach the ancient dragon's lair cautiously.",
        "The dragon emerges from the shadows, its eyes glowing like emeralds.",
        "I attempt to negotiate with the dragon rather than fight.",
        "The dragon speaks: 'Why do you seek my treasure, mortal?'",
        "I explain that I need the treasure to save my village.",
        "The dragon considers your words, then nods slowly.",
    ]

    for i, entry in enumerate(entries):
        story_ref.add(
            {
                "actor": "user" if i % 2 == 0 else "gemini",
                "text": entry,
                "timestamp": datetime.now(UTC),
            }
        )

    # Campaign 2: Space Adventure
    campaign2_ref = user1_ref.collection("campaigns").document("space_odyssey")
    campaign2_ref.set(
        {
            "title": "Galactic Explorer",
            "created_at": datetime.now(UTC),
            "last_played": datetime.now(UTC),
        }
    )

    story_ref2 = campaign2_ref.collection("story")
    space_entries = [
        "I pilot my starship toward the unknown nebula.",
        "Sensors detect an alien vessel approaching.",
        "I hail the alien ship on all frequencies.",
        "The aliens respond with mathematical sequences.",
    ]

    for i, entry in enumerate(space_entries):
        story_ref2.add(
            {
                "actor": "user" if i % 2 == 0 else "gemini",
                "text": entry,
                "timestamp": datetime.now(UTC),
            }
        )

    # User 2: Casual player
    user2_id = "analytics_test_user_2"
    user2_ref = db.collection("users").document(user2_id)

    campaign3_ref = user2_ref.collection("campaigns").document("fantasy_adventure")
    campaign3_ref.set(
        {
            "title": "Magical Forest Quest",
            "created_at": datetime.now(UTC),
            "last_played": datetime.now(UTC),
        }
    )

    story_ref3 = campaign3_ref.collection("story")
    for i in range(15):  # This user has a longer campaign
        story_ref3.add(
            {
                "actor": "user" if i % 2 == 0 else "gemini",
                "text": f"Forest adventure entry {i + 1}: Exploring the enchanted woods.",
                "timestamp": datetime.now(UTC),
            }
        )

    # User 3: Power user with multiple campaigns
    user3_id = "analytics_test_user_3"
    user3_ref = db.collection("users").document(user3_id)

    # Multiple campaigns for this user
    campaign_titles = [
        "Medieval Politics",
        "Cyberpunk Heist",
        "Zombie Apocalypse",
        "Pirate Adventure",
        "Wild West Showdown",
    ]

    for j, title in enumerate(campaign_titles):
        campaign_ref = user3_ref.collection("campaigns").document(f"campaign_{j + 1}")
        campaign_ref.set(
            {
                "title": title,
                "created_at": datetime.now(UTC),
                "last_played": datetime.now(UTC),
            }
        )

        # Add varying numbers of entries
        story_ref = campaign_ref.collection("story")
        num_entries = 3 + (j * 2)  # 3, 5, 7, 9, 11 entries
        for i in range(num_entries):
            story_ref.add(
                {
                    "actor": "user" if i % 2 == 0 else "gemini",
                    "text": f"{title} - Story entry {i + 1}",
                    "timestamp": datetime.now(UTC),
                }
            )

    print("✅ Sample data created successfully!")
    print("   - User 1: 2 campaigns, 10 entries")
    print("   - User 2: 1 campaign, 15 entries")
    print("   - User 3: 5 campaigns, 35 entries")
    print("   - Total: 3 users, 8 campaigns, 60 entries")

    # Verify the data was actually created
    print("\n🔍 Verifying data creation...")
    users_ref = db.collection("users")
    users = list(users_ref.stream())
    print(f"   Found {len(users)} users in database")
    for user in users:
        print(f"   - User: {user.id}")
        campaigns = list(user.reference.collection("campaigns").stream())
        print(f"     Campaigns: {len(campaigns)}")
        for campaign in campaigns:
            stories = list(campaign.reference.collection("story").stream())
            print(f"       - {campaign.id}: {len(stories)} entries")


def main():
    """Create sample data for analytics testing."""
    try:
        print("🔄 Initializing Firebase...")
        db = initialize_firebase()

        create_sample_data(db)

        print("\n🎯 Sample data ready for analytics!")
        print("Now run: ../venv/bin/python scripts/firebase_user_analytics.py")

    except Exception as e:
        print(f"❌ Error: {e}")

        traceback.print_exc()


if __name__ == "__main__":
    main()
