"""
Simple test of fake services without external dependencies.
Verifies that fakes work correctly in isolation.
"""

import json
import os
import sys
import unittest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fake_auth import FakeFirebaseAuth
from fake_firestore import FakeFirestoreClient
from fake_gemini import create_fake_gemini_client


class TestFakeServicesSimple(unittest.TestCase):
    """Test fake services in isolation."""

    def test_fake_firestore_basic_operations(self):
        """Test that fake Firestore behaves like the real thing."""
        client = FakeFirestoreClient()

        # Test document creation and retrieval
        doc = client.collection("campaigns").document("test-campaign")
        test_data = {
            "title": "Test Campaign",
            "character": "Test Hero",
            "user_id": "test-user",
        }
        doc.set(test_data)

        # Verify data was stored
        retrieved = doc.get().to_dict()
        self.assertEqual(retrieved["title"], "Test Campaign")
        self.assertEqual(retrieved["character"], "Test Hero")

        # Test subcollections
        story_doc = doc.collection("story").document("scene-1")
        story_data = {"narrative": "The adventure begins..."}
        story_doc.set(story_data)

        story_retrieved = story_doc.get().to_dict()
        self.assertEqual(story_retrieved["narrative"], "The adventure begins...")

        # Test that data is JSON serializable (no Mock objects)
        json_str = json.dumps(retrieved)
        self.assertIn("Test Campaign", json_str)

    def test_fake_gemini_response_generation(self):
        """Test that fake Gemini generates realistic responses."""
        client = create_fake_gemini_client()
        model = client.models.get("gemini-2.5-flash")

        # Test campaign creation prompt
        prompt = """
        Create a campaign for:
        Character: Brave Knight
        Setting: Medieval Kingdom
        """

        response = model.generate_content(prompt)

        # Response should be valid JSON string
        self.assertIsInstance(response.text, str)
        response_data = json.loads(response.text)

        # Should contain expected structure
        self.assertIn("narrative", response_data)
        self.assertIn("mechanics", response_data)
        self.assertIn("scene", response_data)

        # Should contain context from prompt
        self.assertIn("Brave Knight", response_data["narrative"])

        # Test story continuation
        continue_prompt = """
        Character: Brave Knight
        User Input: approaches the castle gate
        """

        continue_response = model.generate_content(continue_prompt)
        continue_data = json.loads(continue_response.text)

        self.assertIn("approaches the castle gate", continue_data["narrative"])

    def test_fake_auth_user_management(self):
        """Test that fake Auth manages users realistically."""
        auth = FakeFirebaseAuth()

        # Test getting default users
        user = auth.get_user("test-user-123")
        self.assertEqual(user.uid, "test-user-123")
        self.assertEqual(user.email, "test@example.com")

        # Test creating new user
        new_user = auth.create_user(
            uid="new-user", email="new@test.com", display_name="New User"
        )
        self.assertEqual(new_user.uid, "new-user")
        self.assertEqual(new_user.email, "new@test.com")

        # Test token creation and verification
        token = auth.create_custom_token("test-user-123")
        self.assertIsInstance(token, str)

        decoded = auth.verify_id_token(token)
        self.assertEqual(decoded.uid, "test-user-123")

        # Test user data is JSON serializable
        user_dict = user.to_dict()
        json_str = json.dumps(user_dict)
        self.assertIn("test-user-123", json_str)

    def test_fake_services_integration(self):
        """Test that all fake services work together."""
        # Set up services
        firestore = FakeFirestoreClient()
        gemini = create_fake_gemini_client()
        auth = FakeFirebaseAuth()

        # Create user
        user = auth.create_user(uid="integration-user", email="integration@test.com")

        # Create campaign in Firestore
        campaign_doc = firestore.collection("campaigns").document(
            "integration-campaign"
        )
        campaign_data = {
            "title": "Integration Test",
            "character": "Test Warrior",
            "setting": "Test Realm",
            "user_id": user.uid,
        }
        campaign_doc.set(campaign_data)

        # Generate story with Gemini
        model = gemini.models.get("gemini-2.5-flash")
        prompt = f"Create story for {campaign_data['character']} in {campaign_data['setting']}"
        response = model.generate_content(prompt)
        story_data = json.loads(response.text)

        # Store story in Firestore
        story_doc = campaign_doc.collection("story").document("current")
        story_doc.set(story_data)

        # Verify complete flow
        stored_campaign = campaign_doc.get().to_dict()
        stored_story = story_doc.get().to_dict()

        self.assertEqual(stored_campaign["user_id"], user.uid)
        self.assertIn("Test Warrior", stored_story["narrative"])

        # Verify no Mock objects in the data
        full_data = {
            "user": user.to_dict(),
            "campaign": stored_campaign,
            "story": stored_story,
        }

        # Should serialize without issues
        json_output = json.dumps(full_data, indent=2)
        self.assertGreater(len(json_output), 500)  # Should have substantial content

        print("✅ Integration test passed - all fake services working together")
        print(f"Data size: {len(json_output)} characters")


if __name__ == "__main__":
    unittest.main(verbosity=2)
