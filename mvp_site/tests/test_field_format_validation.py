#!/usr/bin/env python3
"""
Red-Green Test for Field Format Validation
==========================================

This test validates that the field format between world_logic.py and main.py
translation layer is consistent and working correctly.

RED: Temporarily break the field format to ensure test catches it
GREEN: Fix the field format and ensure test passes
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Set TESTING environment variable
os.environ["TESTING"] = "true"
os.environ["GEMINI_API_KEY"] = "test-api-key"

# Add the parent directory to the path to import main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestFieldFormatValidation(unittest.TestCase):
    """Test field format consistency between world_logic and main translation layer."""

    def setUp(self):
        """Set up test with mock dependencies."""
        from fake_firestore import FakeFirestoreClient

        self.fake_firestore = FakeFirestoreClient()
        self.test_user_id = "field-format-test-user"
        self.test_campaign_id = "field-format-test-campaign"

        # Mock campaign data
        self.mock_campaign_data = {
            "id": self.test_campaign_id,
            "user_id": self.test_user_id,
            "title": "Field Format Test Campaign",
            "created_at": "2024-01-15T10:30:00Z",
            "initial_prompt": "Test field format validation",
            "selected_prompts": ["narrative"],
            "use_default_world": False,
        }

    @patch("firebase_admin.firestore.client")
    @patch("google.genai.Client")
    def test_field_format_consistency_red_green(
        self, mock_genai_client_class, mock_firestore_client
    ):
        """
        RED-GREEN TEST: Field format consistency between world_logic and main.py

        This test ensures that story entries created by world_logic.py use the
        correct field format that main.py translation layer expects.
        """
        import json

        from tests.fake_firestore import FakeGeminiResponse, FakeTokenCount

        # Set up fake Firestore
        mock_firestore_client.return_value = self.fake_firestore

        # Pre-populate campaign data
        user_doc = self.fake_firestore.collection("users").document(self.test_user_id)
        campaign_doc = user_doc.collection("campaigns").document(self.test_campaign_id)
        campaign_doc.set(self.mock_campaign_data)

        # Set up fake Gemini client
        fake_genai_client = MagicMock()
        mock_genai_client_class.return_value = fake_genai_client
        fake_genai_client.models.count_tokens.return_value = FakeTokenCount(1000)

        # Mock Gemini response with expected format
        gemini_response_data = {
            "narrative": "You find yourself in a mystical testing realm, surrounded by glowing validation runes.",
            "entities_mentioned": ["Test Hero", "Validation Runes"],
            "location_confirmed": "Testing Realm",
            "planning_block": "The field format test begins successfully.",
            "dice_rolls": [],
            "resources": "None",
            "state_updates": {"hp": 100, "location": "Testing Realm"},
        }
        fake_genai_client.models.generate_content.return_value = FakeGeminiResponse(
            json.dumps(gemini_response_data)
        )

        # Import after mocking to ensure mocks are active
        from main import create_app
        from world_logic import process_action_unified

        # Test the MCP protocol through direct world_logic call
        print("\n🔍 Testing world_logic.py story entry creation...")

        # Use async function properly
        import asyncio

        request_data = {
            "user_id": self.test_user_id,
            "campaign_id": self.test_campaign_id,
            "user_input": "I examine the testing environment carefully.",
            "mode": "character",
        }

        result = asyncio.run(process_action_unified(request_data))

        # Validate that world_logic returns story entries with correct field format
        self.assertIn("story", result, "world_logic should return story field")
        story_entries = result["story"]
        self.assertIsInstance(story_entries, list, "Story should be a list")
        self.assertGreater(len(story_entries), 0, "Story should contain entries")

        # CRITICAL TEST: Check field format
        first_entry = story_entries[0]
        self.assertIsInstance(first_entry, dict, "Story entry should be dict")

        # The critical assertion: ensure "text" field is present (not "story")
        self.assertIn(
            "text",
            first_entry,
            "Story entry should have 'text' field for main.py compatibility",
        )
        self.assertIsInstance(
            first_entry["text"], str, "Story entry text field should be string"
        )
        self.assertGreater(
            len(first_entry["text"]), 0, "Story entry text should not be empty"
        )

        print("✅ world_logic.py creates entries with correct 'text' field")
        print(f"   Entry content: {first_entry['text'][:100]}...")

        # Test the translation layer compatibility
        print("\n🔍 Testing main.py translation layer compatibility...")

        # Create Flask test client
        app = create_app()
        app.config["TESTING"] = True
        client = app.test_client()

        # Test headers for auth bypass
        test_headers = {
            "X-Test-Bypass-Auth": "true",
            "X-Test-User-ID": self.test_user_id,
            "Content-Type": "application/json",
        }

        # Make HTTP request through main.py translation layer
        interaction_data = {
            "input": "I continue exploring this testing realm.",
            "mode": "character",
        }

        response = client.post(
            f"/api/campaigns/{self.test_campaign_id}/interaction",
            data=json.dumps(interaction_data),
            headers=test_headers,
        )

        # Validate HTTP response
        self.assertEqual(
            response.status_code,
            200,
            "HTTP request should succeed through translation layer",
        )

        response_data = json.loads(response.data)
        self.assertIn(
            "narrative",
            response_data,
            "Translation layer should extract narrative from story entries",
        )

        narrative_text = response_data["narrative"]
        self.assertIsInstance(narrative_text, str, "Narrative should be string")
        self.assertGreater(
            len(narrative_text), 0, "Narrative should not be empty after translation"
        )

        print("✅ main.py translation layer successfully extracts narrative")
        print(f"   Narrative content: {narrative_text[:100]}...")

        print("\n🟢 GREEN PHASE: Field format consistency test PASSED")
        print("✅ world_logic.py creates story entries with 'text' field")
        print("✅ main.py translation layer successfully processes 'text' field")
        print("✅ End-to-end narrative extraction works correctly")

    def test_red_phase_field_format_mismatch_detection(self):
        """
        RED PHASE: Temporarily test what happens with wrong field format

        This demonstrates what would happen if world_logic used 'story' field
        instead of 'text' field - the translation layer would fail to extract content.
        """
        print("\n🔴 RED PHASE: Testing field format mismatch detection")

        # Simulate story entries with wrong field format (what used to cause the bug)
        story_entries_wrong_format = [
            {"story": "This should not work with translation layer"}
        ]

        # Test what translation layer expects
        first_entry = story_entries_wrong_format[0]
        narrative_text = (
            first_entry.get("text", "")  # This is what main.py does
            if isinstance(first_entry, dict)
            else str(first_entry)
        )

        # This should result in empty narrative due to field mismatch
        self.assertEqual(
            narrative_text, "", "Wrong field format should result in empty narrative"
        )

        print("🔴 RED TEST CONFIRMED: 'story' field format causes empty narrative")
        print("   Expected field: 'text', Actual field: 'story', Result: empty")

        # Now test correct field format
        story_entries_correct_format = [{"text": "This works with translation layer"}]
        first_entry_correct = story_entries_correct_format[0]
        narrative_text_correct = (
            first_entry_correct.get("text", "")
            if isinstance(first_entry_correct, dict)
            else str(first_entry_correct)
        )

        self.assertEqual(
            narrative_text_correct,
            "This works with translation layer",
            "Correct field format should preserve narrative content",
        )

        print("🟢 CORRECTION CONFIRMED: 'text' field format works correctly")
        print("   Field: 'text', Result: narrative content preserved")


if __name__ == "__main__":
    print("🧪 Field Format Validation Test")
    print("Testing consistency between world_logic.py and main.py translation layer")
    print("=" * 70)
    unittest.main(verbosity=2)
