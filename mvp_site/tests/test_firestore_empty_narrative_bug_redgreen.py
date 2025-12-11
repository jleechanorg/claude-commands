"""
RED-GREEN TEST: Firestore Empty Narrative Error Handling

This test demonstrates the new behavior for empty AI narratives:
- Empty narrative from AI is now an ERROR (LLM compliance failure)
- The system prompts require AI to ALWAYS provide narrative content
- Even Deep Think responses must include brief narrative (character pausing to think)

Updated behavior: Empty AI narrative raises FirestoreWriteError
"""

# ruff: noqa: PT027,PT009

import os
import sys
import unittest
from unittest.mock import patch

# Set TESTING environment variable
os.environ["TESTING"] = "true"
os.environ["GEMINI_API_KEY"] = "test-api-key"

# Add the parent directory to the path
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from tests.fake_firestore import FakeFirestoreClient

from mvp_site import constants
from mvp_site.firestore_service import FirestoreWriteError, add_story_entry


class TestFirestoreEmptyNarrativeError(unittest.TestCase):
    """
    Test that empty AI narratives now raise errors instead of using placeholders.

    New Behavior:
    1. AI generates response with empty narrative = LLM compliance error
    2. System prompts require narrative even during Deep Think
    3. Empty narrative from AI raises FirestoreWriteError
    """

    def setUp(self):
        """Set up test environment with fake Firestore client."""
        self.fake_firestore = FakeFirestoreClient()

    @patch("mvp_site.firestore_service.get_db")
    def test_empty_narrative_from_ai_raises_error(self, mock_get_db):
        """
        TEST: Empty narrative from AI should raise FirestoreWriteError.

        The AI MUST always provide narrative content per system prompts.
        Even Deep Think responses require brief narrative showing character thinking.
        """
        # Arrange: Set up fake Firestore client
        mock_get_db.return_value = self.fake_firestore

        # Test data: Empty narrative from AI (this is now an error condition)
        user_id = "test-user-123"
        campaign_id = "test-campaign-456"
        actor = constants.ACTOR_GEMINI
        narrative_text = ""  # EMPTY NARRATIVE (now an error for AI actor)
        structured_fields = {
            "planning_block": {
                "choices": [
                    {
                        "action": "Attack the dragon",
                        "analysis": {
                            "pros": ["High damage potential", "Direct approach"],
                            "cons": ["High risk", "Could fail spectacularly"],
                        },
                    }
                ]
            },
            "state_changes": {"thinking_mode": {"active": True, "depth": "deep"}},
        }

        # Act & Assert: Empty AI narrative should raise FirestoreWriteError
        with self.assertRaises(FirestoreWriteError) as context:
            add_story_entry(
                user_id=user_id,
                campaign_id=campaign_id,
                actor=actor,
                text=narrative_text,  # Empty - should error!
                mode=None,
                structured_fields=structured_fields,
            )

        # Verify error message indicates LLM compliance issue
        error_message = str(context.exception)
        self.assertIn("empty narrative", error_message.lower())
        self.assertIn(campaign_id, error_message)

    @patch("mvp_site.firestore_service.get_db")
    def test_empty_user_input_still_saves_with_placeholder(self, mock_get_db):
        """
        TEST: Empty USER input should still save with placeholder.

        Empty user submissions are valid (user pressed enter without typing).
        Only AI responses require non-empty narrative.
        """
        # Arrange: Set up fake Firestore client
        mock_get_db.return_value = self.fake_firestore

        # Test data: Empty narrative from USER (this is still valid)
        user_id = "test-user-123"
        campaign_id = "test-campaign-456"
        actor = "user"  # User actor, not AI
        narrative_text = ""  # Empty user input is valid

        # Act: Add story entry with empty user input
        add_story_entry(
            user_id=user_id,
            campaign_id=campaign_id,
            actor=actor,
            text=narrative_text,  # Empty but valid for user
            mode=None,
            structured_fields=None,
        )

        # Assert: Story should be saved with placeholder
        user_campaigns = (
            self.fake_firestore.collection("users")
            .document(user_id)
            .collection("campaigns")
        )
        campaign_doc = user_campaigns.document(campaign_id)
        story_collection = campaign_doc.collection("story")
        story_docs = story_collection._docs

        assert len(story_docs) > 0, "Empty user input should still save"
        story_entry = list(story_docs.values())[0]
        entry_data = story_entry._data
        assert entry_data["text"] == "[Empty input]", (
            "Empty user input gets placeholder"
        )

    @patch("mvp_site.firestore_service.get_db")
    def test_god_mode_allows_empty_narrative(self, mock_get_db):
        """GOD mode responses can include an empty narrative with structured data."""

        mock_get_db.return_value = self.fake_firestore

        user_id = "test-user-123"
        campaign_id = "test-campaign-456"
        actor = constants.ACTOR_GEMINI
        narrative_text = ""
        structured_fields = {
            "god_mode_response": "Reveal secret path (opens hidden route)",
        }

        add_story_entry(
            user_id=user_id,
            campaign_id=campaign_id,
            actor=actor,
            text=narrative_text,
            mode=None,
            structured_fields=structured_fields,
        )

        story_collection = (
            self.fake_firestore.collection("users")
            .document(user_id)
            .collection("campaigns")
            .document(campaign_id)
            .collection("story")
        )
        story_docs = story_collection._docs

        assert len(story_docs) == 1, (
            "God mode response with empty narrative should save"
        )
        entry_data = list(story_docs.values())[0]._data
        assert entry_data["text"] == ""
        assert entry_data["god_mode_response"] == structured_fields["god_mode_response"]

    def test_empty_narrative_detection_logic(self):
        """
        Document the detection logic for empty narratives.
        """
        # Empty narrative detection
        narrative = ""
        text_bytes = narrative.encode("utf-8")
        max_bytes = 10000
        chunks = [
            text_bytes[i : i + max_bytes] for i in range(0, len(text_bytes), max_bytes)
        ]

        # Empty narratives produce no chunks
        assert len(chunks) == 0, "Empty narrative produces no chunks"

        # For AI actor, this should now be an error condition
        actor = constants.ACTOR_GEMINI
        should_error = actor == constants.ACTOR_GEMINI and len(chunks) == 0
        assert should_error, "Empty AI narrative should trigger error"


if __name__ == "__main__":
    unittest.main()
