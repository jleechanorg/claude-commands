"""
RED-GREEN TEST: Firestore Empty Narrative Persistence Bug

This test demonstrates the bug described in roadmap/scratchpad_planb_rates.md:
- Think commands with empty narrative weren't being saved to Firestore
- Bug: chunks=0 logic prevented database writes for empty narratives
- Impact: AI responses disappeared on page reload

RED: Test fails when empty narrative + structured fields aren't saved
GREEN: Test passes after fix handles empty narrative correctly
"""

import os
import sys
import unittest
from unittest.mock import patch

# Set TESTING environment variable
os.environ["TESTING"] = "true"
os.environ["GEMINI_API_KEY"] = "test-api-key"

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import constants

from firestore_service import add_story_entry
from tests.fake_firestore import FakeFirestoreClient


class TestFirestoreEmptyNarrativeBug(unittest.TestCase):
    """
    RED-GREEN demonstration of the Firestore empty narrative persistence bug.

    The Bug Scenario:
    1. AI generates response with empty narrative but valid structured fields
    2. Original code: chunks=0 → no database write → data lost
    3. Fixed code: handles empty narrative + structured fields correctly
    """

    def setUp(self):
        """Set up test environment with fake Firestore client."""
        self.fake_firestore = FakeFirestoreClient()

    @patch("firestore_service.get_db")
    def test_empty_narrative_with_structured_fields_persists(self, mock_get_db):
        """
        RED-GREEN TEST: Empty narrative + structured fields should be saved.

        This tests the specific bug from planb_rates scratchpad:
        - Think commands generate empty narrative but valid structured fields
        - Original bug: chunks=0 prevented any database write
        - Fix: empty narrative with structured fields should still save
        """
        # Arrange: Set up fake Firestore client
        mock_get_db.return_value = self.fake_firestore

        # Test data: Empty narrative but with structured fields (think command scenario)
        user_id = "test-user-123"
        campaign_id = "test-campaign-456"
        actor = constants.ACTOR_GEMINI
        narrative_text = ""  # EMPTY NARRATIVE (the bug scenario)
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

        # Act: Add story entry with empty narrative + structured fields
        # This is the exact scenario that caused the bug
        try:
            add_story_entry(
                user_id=user_id,
                campaign_id=campaign_id,
                actor=actor,
                text=narrative_text,  # Empty!
                mode=None,
                structured_fields=structured_fields,
            )
            story_saved = True
        except Exception as e:
            story_saved = False
            error = str(e)

        # Assert: Story should be saved despite empty narrative
        # GREEN: After fix, this should work
        # RED: Before fix, this would fail due to chunks=0 logic
        self.assertTrue(
            story_saved,
            "Empty narrative with structured fields should be saved to Firestore",
        )

        # Verify the story was actually written to fake Firestore
        # This simulates what would happen on page reload
        user_campaigns = (
            self.fake_firestore.collection("users")
            .document(user_id)
            .collection("campaigns")
        )
        campaign_doc = user_campaigns.document(campaign_id)

        # Check if story collection exists and has entries
        story_collection = campaign_doc.collection("story")
        story_docs = story_collection._docs  # Access internal storage

        self.assertGreater(
            len(story_docs), 0, "Story entry should exist despite empty narrative"
        )

        # Verify structured fields were preserved in the story entry
        story_entry = list(story_docs.values())[0]  # Get first story entry
        entry_data = story_entry._data

        # Verify structured fields were preserved (they're flattened into the entry)
        self.assertIn(
            "planning_block", entry_data, "Planning block should be preserved"
        )
        self.assertIn("state_changes", entry_data, "State changes should be preserved")

        # Verify empty narrative was handled properly
        self.assertNotEqual(
            entry_data["text"],
            "",
            "Empty narrative should be replaced with placeholder text",
        )
        self.assertIn(
            "Internal thoughts",
            entry_data["text"],
            "Empty narrative should have meaningful placeholder",
        )

    def test_bug_reproduction_scenario(self):
        """
        Reproduce the exact bug scenario from the scratchpad:
        1. Think command generates response with empty narrative
        2. Response has valid structured fields (planning block, state changes)
        3. Original bug: chunks=0 → no save → response disappears on reload
        """
        # This test documents the exact scenario that caused the bug
        narrative = ""  # Think commands often generate empty narrative
        structured_fields = {
            "planning_block": {
                "choices": [{"action": "think", "analysis": {"pros": [], "cons": []}}]
            },
            "state_changes": {"thinking_mode": {"active": True}},
        }

        # Calculate chunks using the original logic
        chunks = [narrative[i : i + 10000] for i in range(0, len(narrative), 10000)]
        chunks = [chunk.strip() for chunk in chunks if chunk.strip()]

        # Original bug logic: if no chunks, don't save anything
        would_save_with_original_logic = len(chunks) > 0

        # Document the bug scenario
        self.assertFalse(
            would_save_with_original_logic,
            "Original logic would NOT save empty narrative + structured fields",
        )

        # The fix should save structured fields even with empty narrative
        should_save_with_fix = (
            structured_fields is not None and len(structured_fields) > 0
        )
        self.assertTrue(
            should_save_with_fix,
            "Fixed logic SHOULD save empty narrative + structured fields",
        )


if __name__ == "__main__":
    unittest.main()
