"""Test that god mode responses use the god_mode_response field correctly."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import MagicMock, patch

import constants
from narrative_response_schema import parse_structured_response

import firestore_service


class TestGodModeResponseField(unittest.TestCase):
    """Test god_mode_response field handling."""

    def setUp(self):
        """Set up test environment"""
        # Set mock services mode to skip verification for unit tests
        os.environ["MOCK_SERVICES_MODE"] = "true"

    def tearDown(self):
        """Clean up test environment"""
        # Clean up environment variable
        if "MOCK_SERVICES_MODE" in os.environ:
            del os.environ["MOCK_SERVICES_MODE"]

    def test_god_mode_response_field_used(self):
        """Test that god_mode_response field is used when present."""
        god_response = """{
            "narrative": "",
            "god_mode_response": "A mystical fog rolls in from the mountains. The temperature drops suddenly.",
            "entities_mentioned": [],
            "location_confirmed": "Unknown Forest",
            "state_updates": {
                "environment": {
                    "weather": "foggy",
                    "temperature": "cold"
                }
            },
            "debug_info": {}
        }"""

        narrative, response_obj = parse_structured_response(god_response)

        # Should return the god_mode_response content
        self.assertEqual(
            narrative,
            "A mystical fog rolls in from the mountains. The temperature drops suddenly.",
        )
        self.assertEqual(
            response_obj.god_mode_response,
            "A mystical fog rolls in from the mountains. The temperature drops suddenly.",
        )
        self.assertEqual(response_obj.narrative, "")

    def test_normal_response_without_god_mode(self):
        """Test that normal responses work without god_mode_response field."""
        normal_response = """{
            "narrative": "You enter the tavern and see a hooded figure in the corner.",
            "entities_mentioned": ["hooded figure"],
            "location_confirmed": "The Rusty Tankard Tavern",
            "state_updates": {},
            "debug_info": {}
        }"""

        narrative, response_obj = parse_structured_response(normal_response)

        # Should return the narrative content
        self.assertEqual(
            narrative, "You enter the tavern and see a hooded figure in the corner."
        )
        self.assertEqual(
            response_obj.narrative,
            "You enter the tavern and see a hooded figure in the corner.",
        )
        self.assertIsNone(response_obj.god_mode_response)

    def test_god_mode_with_state_updates(self):
        """Test god mode response with complex state updates."""
        god_response = """{
            "narrative": "",
            "god_mode_response": "The ancient dragon Vermithrax awakens from his slumber. His eyes glow with malevolent intelligence.",
            "entities_mentioned": ["Vermithrax"],
            "location_confirmed": "Dragon's Lair",
            "state_updates": {
                "npc_data": {
                    "vermithrax": {
                        "name": "Vermithrax",
                        "type": "ancient_red_dragon",
                        "hp": 546,
                        "max_hp": 546,
                        "status": "hostile"
                    }
                }
            },
            "debug_info": {
                "dm_notes": ["Adding major boss encounter"]
            }
        }"""

        narrative, response_obj = parse_structured_response(god_response)

        # Should use god_mode_response
        self.assertIn("ancient dragon Vermithrax", narrative)
        self.assertEqual(response_obj.entities_mentioned, ["Vermithrax"])
        self.assertIsNotNone(response_obj.state_updates)
        self.assertIn("npc_data", response_obj.state_updates)

    def test_god_mode_empty_response(self):
        """Test god mode with empty god_mode_response field."""
        empty_response = """{
            "narrative": "",
            "god_mode_response": "",
            "entities_mentioned": [],
            "location_confirmed": "Unknown",
            "state_updates": {},
            "debug_info": {}
        }"""

        narrative, response_obj = parse_structured_response(empty_response)

        # Should return empty string, not try to extract from elsewhere
        self.assertEqual(narrative, "")
        self.assertEqual(response_obj.god_mode_response, "")

    def test_malformed_god_mode_response(self):
        """Test handling of malformed JSON with god_mode_response."""
        malformed = (
            """{"god_mode_response": "The world shifts...", "state_updates": {"""
        )

        narrative, response_obj = parse_structured_response(malformed)

        # Should extract the god_mode_response even from incomplete JSON
        self.assertIn("world shifts", narrative)

    def test_backward_compatibility(self):
        """Test that old god mode responses without god_mode_response field still work."""
        old_style_response = """{
            "narrative": "The ancient tome glows with an eerie light as you speak the command.",
            "entities_mentioned": ["ancient tome"],
            "location_confirmed": "Library",
            "state_updates": {
                "inventory": {
                    "ancient_tome": {
                        "activated": true
                    }
                }
            },
            "debug_info": {}
        }"""

        narrative, response_obj = parse_structured_response(old_style_response)

        # Should use narrative field as before
        self.assertEqual(
            narrative,
            "The ancient tome glows with an eerie light as you speak the command.",
        )
        self.assertIsNone(response_obj.god_mode_response)

    def test_god_mode_with_empty_narrative(self):
        """Test god mode response when narrative is empty string."""
        response = """{
            "narrative": "",
            "god_mode_response": "The world trembles at your command.",
            "entities_mentioned": [],
            "location_confirmed": "Unknown",
            "state_updates": {},
            "debug_info": {}
        }"""

        narrative, response_obj = parse_structured_response(response)

        # Should return god_mode_response when only god_mode_response is present
        self.assertEqual(narrative, "The world trembles at your command.")
        # Response object should also have god_mode_response
        self.assertEqual(
            response_obj.god_mode_response, "The world trembles at your command."
        )

    def test_combined_god_mode_and_narrative(self):
        """Test that only narrative is returned when both god_mode_response and narrative are present."""
        both_fields_response = """{
            "narrative": "Meanwhile, in the mortal realm, the players sense a change...",
            "god_mode_response": "The deity grants your wish. A shimmering portal opens.",
            "entities_mentioned": ["shimmering portal"],
            "location_confirmed": "Unknown",
            "state_updates": {},
            "debug_info": {}
        }"""

        narrative, response_obj = parse_structured_response(both_fields_response)

        # Should return only narrative - god_mode_response is passed separately to frontend
        self.assertEqual(
            narrative, "Meanwhile, in the mortal realm, the players sense a change..."
        )
        self.assertNotIn("The deity grants your wish", narrative)
        # Response object should have both fields separately
        self.assertEqual(
            response_obj.god_mode_response,
            "The deity grants your wish. A shimmering portal opens.",
        )
        self.assertEqual(
            response_obj.narrative,
            "Meanwhile, in the mortal realm, the players sense a change...",
        )

    def test_god_mode_response_saved_to_firestore(self):
        """Test that god_mode_response is saved to Firestore via add_story_entry."""
        god_response = {
            "narrative": "",
            "god_mode_response": "A test god mode response for Firestore.",
            "entities_mentioned": [],
            "location_confirmed": "Test Location",
            "state_updates": {},
            "debug_info": {},
        }
        with patch("firestore_service.add_story_entry") as mock_add_story_entry:
            from firestore_service import add_story_entry

            add_story_entry(
                "user123",
                "camp456",
                "gemini",
                god_response["god_mode_response"],
                structured_fields=god_response,
            )
            called_args, called_kwargs = mock_add_story_entry.call_args
            self.assertIn("god_mode_response", called_kwargs["structured_fields"])
            self.assertEqual(
                called_kwargs["structured_fields"]["god_mode_response"],
                "A test god mode response for Firestore.",
            )


class TestGodModeResponseIntegration(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        # Set mock services mode to skip verification for unit tests
        os.environ["MOCK_SERVICES_MODE"] = "true"

    def tearDown(self):
        """Clean up test environment"""
        # Clean up environment variable
        if "MOCK_SERVICES_MODE" in os.environ:
            del os.environ["MOCK_SERVICES_MODE"]

    def test_all_structured_fields_are_saved_in_firestore(self):
        # Patch the full Firestore chain
        mock_db = MagicMock()
        mock_users_collection = MagicMock()
        mock_user_doc = MagicMock()
        mock_campaigns_collection = MagicMock()
        mock_campaign_doc = MagicMock()
        mock_story_collection = MagicMock()

        # Chain the calls
        mock_db.collection.return_value = mock_users_collection
        mock_users_collection.document.return_value = mock_user_doc
        mock_user_doc.collection.return_value = mock_campaigns_collection
        mock_campaigns_collection.document.return_value = mock_campaign_doc
        mock_campaign_doc.collection.return_value = mock_story_collection

        with patch("firestore_service.get_db", return_value=mock_db):
            structured_fields = {
                constants.FIELD_SESSION_HEADER: "Session header value",
                constants.FIELD_PLANNING_BLOCK: "Planning block value",
                constants.FIELD_DICE_ROLLS: [1, 2, 3],
                constants.FIELD_RESOURCES: "Resource value",
                constants.FIELD_DEBUG_INFO: {"debug": True},
                constants.FIELD_GOD_MODE_RESPONSE: "Integration test god mode response",
            }
            firestore_service.add_story_entry(
                user_id="user123",
                campaign_id="camp456",
                actor=constants.ACTOR_GEMINI,
                text="Some narrative",
                structured_fields=structured_fields,
            )

            # Check that add() was called with all structured fields present
            self.assertTrue(mock_story_collection.add.called)
            add_call_args, add_call_kwargs = mock_story_collection.add.call_args
            written_data = add_call_args[0]
            for field, value in structured_fields.items():
                self.assertIn(field, written_data)
                self.assertEqual(written_data[field], value)


if __name__ == "__main__":
    unittest.main()
