import datetime
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add parent directory to path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

import constants

from firestore_service import add_story_entry

# Mock firebase_admin before importing the service
mock_firestore = MagicMock()
# Configure the mock to have the sentinel values using MagicMock for identity checks
mock_firestore.DELETE_FIELD = MagicMock(name="DELETE_FIELD")
mock_firestore.SERVER_TIMESTAMP = MagicMock(name="SERVER_TIMESTAMP")

# We need to import the service we are testing
import firestore_service

# Disable logging for most tests to keep output clean, can be enabled for debugging
# logging.disable(logging_util.logging.CRITICAL)

sys.modules["firebase_admin.firestore"] = mock_firestore

# Now import the service, which will use the mock
from firestore_service import json_default_serializer, update_state_with_changes

# Create sentinel mock objects for use in the tests.
DELETE_SENTINEL = MagicMock(name="DELETE_FIELD")
TIMESTAMP_SENTINEL = MagicMock(name="SERVER_TIMESTAMP")


@patch("firestore_service.firestore.SERVER_TIMESTAMP", TIMESTAMP_SENTINEL)
@patch("firestore_service.firestore.DELETE_FIELD", DELETE_SENTINEL)
class TestJsonDefaultSerializer(unittest.TestCase):
    def test_datetime_serialization(self):
        """Tests that datetime objects are serialized to ISO 8601 strings."""
        now = datetime.datetime(2025, 6, 22, 12, 30, 0)
        self.assertEqual(json_default_serializer(now), "2025-06-22T12:30:00")

    def test_delete_field_sentinel(self):
        """Tests that the DELETE_FIELD sentinel is serialized to None."""
        # The serializer will now correctly see the patched DELETE_SENTINEL
        self.assertIsNone(json_default_serializer(DELETE_SENTINEL))

    def test_server_timestamp_sentinel(self):
        """Tests that the SERVER_TIMESTAMP sentinel is serialized to a specific string."""
        # The serializer will now correctly see the patched TIMESTAMP_SENTINEL
        self.assertEqual(
            json_default_serializer(TIMESTAMP_SENTINEL), "<SERVER_TIMESTAMP>"
        )

    def test_unserializable_object(self):
        """Tests that a generic object raises a TypeError."""

        class Unserializable:
            pass

        with self.assertRaises(TypeError):
            json_default_serializer(Unserializable())


class TestUpdateStateWithChanges(unittest.TestCase):
    def setUp(self):
        """This method is called before each test."""
        # It's good practice to start with a fresh state for each test.
        self.state = {
            "player": {
                "inventory": ["sword", "shield"],
                "stats": {"hp": 100, "mp": 50},
            },
            "world_data": {"events": ["event A"], "timestamp": {"year": 1}},
            "custom_campaign_state": {"core_memories": ["memory A", "memory B"]},
        }

    def test_simple_overwrite(self):
        """Should overwrite a top-level value."""
        changes = {"game_version": "1.1"}
        firestore_service.update_state_with_changes(self.state, changes)
        self.assertEqual(self.state["game_version"], "1.1")

    def test_nested_overwrite(self):
        """Should overwrite a nested value."""
        changes = {"player": {"stats": {"hp": 90}}}
        firestore_service.update_state_with_changes(self.state, changes)
        self.assertEqual(self.state["player"]["stats"]["hp"], 90)
        self.assertEqual(
            self.state["player"]["stats"]["mp"], 50
        )  # Ensure other values are untouched

    def test_deep_merge_preserves_unrelated_keys(self):
        """A deep merge should not delete sibling keys in a nested object."""
        state = {"player": {"stats": {"str": 10, "dex": 10}}}
        changes = {"player": {"stats": {"dex": 15}}}
        updated_state = firestore_service.update_state_with_changes(state, changes)
        # This will fail in the old buggy version because 'str' will be missing
        self.assertIn("str", updated_state["player"]["stats"])
        self.assertEqual(updated_state["player"]["stats"]["str"], 10)
        self.assertEqual(updated_state["player"]["stats"]["dex"], 15)

    def test_explicit_append_single_item(self):
        """Should append a single item using the {'append':...} syntax."""
        changes = {"player": {"inventory": {"append": "potion"}}}
        firestore_service.update_state_with_changes(self.state, changes)
        self.assertIn("potion", self.state["player"]["inventory"])
        self.assertEqual(len(self.state["player"]["inventory"]), 3)

    def test_explicit_append_list_of_items(self):
        """Should append a list of items using the {'append':...} syntax."""
        changes = {"player": {"inventory": {"append": ["gold coin", "key"]}}}
        firestore_service.update_state_with_changes(self.state, changes)
        self.assertIn("gold coin", self.state["player"]["inventory"])
        self.assertIn("key", self.state["player"]["inventory"])
        self.assertEqual(len(self.state["player"]["inventory"]), 4)

    def test_core_memories_safeguard_converts_overwrite(self):
        """CRITICAL: Should convert a direct overwrite of core_memories into a safe, deduplicated append."""
        changes = {"custom_campaign_state": {"core_memories": ["memory B", "memory C"]}}
        firestore_service.update_state_with_changes(self.state, changes)
        final_memories = self.state["custom_campaign_state"]["core_memories"]
        self.assertEqual(len(final_memories), 3)
        self.assertIn("memory A", final_memories)
        self.assertIn("memory B", final_memories)
        self.assertIn("memory C", final_memories)

    def test_core_memories_safeguard_handles_no_new_items(self):
        """CRITICAL: Should not add duplicate memories during a safeguard append."""
        changes = {"custom_campaign_state": {"core_memories": ["memory A", "memory B"]}}
        firestore_service.update_state_with_changes(self.state, changes)
        final_memories = self.state["custom_campaign_state"]["core_memories"]
        self.assertEqual(len(final_memories), 2)

    def test_core_memories_explicit_append_is_deduplicated(self):
        """CRITICAL: Explicit appends to core_memories should also be deduplicated."""
        changes = {"custom_campaign_state": {"core_memories": {"append": "memory A"}}}
        firestore_service.update_state_with_changes(self.state, changes)
        final_memories = self.state["custom_campaign_state"]["core_memories"]
        self.assertEqual(
            len(final_memories), 2
        )  # Should not add the duplicate 'memory A'

    def test_append_to_non_core_memories_is_not_deduplicated(self):
        """Append to any list other than core_memories should allow duplicates."""
        changes = {"world_data": {"events": {"append": "event A"}}}
        firestore_service.update_state_with_changes(self.state, changes)
        self.assertEqual(self.state["world_data"]["events"], ["event A", "event A"])
        self.assertEqual(len(self.state["world_data"]["events"]), 2)

    def test_safeguard_handles_non_list_value(self):
        """Safeguard should correctly append a non-list value by wrapping it."""
        state = {"custom_campaign_state": {"core_memories": ["memory A"]}}
        changes = {"custom_campaign_state": {"core_memories": "a new string memory"}}
        expected_memories = ["memory A", "a new string memory"]

        firestore_service.update_state_with_changes(state, changes)

        self.assertEqual(
            state["custom_campaign_state"]["core_memories"], expected_memories
        )


class TestNumericFieldConversion(unittest.TestCase):
    """Test that numeric fields are automatically converted from strings to integers"""

    def test_hp_values_stored_as_integers_in_state_updates(self):
        """Test that HP values in state updates are integers, not strings"""
        # Current game state
        current_state = {
            "player_character_data": {
                "name": "Test Hero",
                "hp_current": 15,  # Currently an integer
                "hp_max": 20,
            },
            "npc_data": {
                "Guard": {"name": "Guard Captain", "hp_current": 25, "hp_max": 30}
            },
        }

        # Proposed changes from AI (simulating what AI might send)
        # This simulates the problem: AI sending HP as strings
        proposed_changes = {
            "player_character_data": {
                "hp_current": "10"  # String from AI response
            },
            "npc_data": {
                "Guard": {
                    "hp_current": "22"  # String from AI response
                }
            },
        }

        # Apply the updates
        updated_state = update_state_with_changes(current_state, proposed_changes)

        # HP values should be stored as integers, not strings
        self.assertIsInstance(
            updated_state["player_character_data"]["hp_current"],
            int,
            "Player HP should be stored as integer, not string",
        )
        self.assertIsInstance(
            updated_state["npc_data"]["Guard"]["hp_current"],
            int,
            "NPC HP should be stored as integer, not string",
        )

        # Verify the actual values
        self.assertEqual(updated_state["player_character_data"]["hp_current"], 10)
        self.assertEqual(updated_state["npc_data"]["Guard"]["hp_current"], 22)

    def test_hp_max_updates_stored_as_integers(self):
        """Test that hp_max updates are stored as integers"""
        current_state = {
            "player_character_data": {
                "name": "Test Hero",
                "hp_current": 15,
                "hp_max": 20,
            }
        }

        proposed_changes = {
            "player_character_data": {
                "hp_max": "25"  # String from AI
            }
        }

        updated_state = update_state_with_changes(current_state, proposed_changes)

        self.assertIsInstance(
            updated_state["player_character_data"]["hp_max"],
            int,
            "hp_max should be stored as integer",
        )
        self.assertEqual(updated_state["player_character_data"]["hp_max"], 25)

    def test_new_character_hp_stored_as_integers(self):
        """Test that new character creation stores HP as integers"""
        current_state = {"npc_data": {}}

        # Adding a new NPC with HP values
        proposed_changes = {
            "npc_data": {
                "NewGuard": {
                    "name": "New Guard",
                    "hp_current": "30",  # String from AI
                    "hp_max": "30",  # String from AI
                }
            }
        }

        updated_state = update_state_with_changes(current_state, proposed_changes)

        new_npc = updated_state["npc_data"]["NewGuard"]
        self.assertIsInstance(
            new_npc["hp_current"], int, "New NPC hp_current should be integer"
        )
        self.assertIsInstance(
            new_npc["hp_max"], int, "New NPC hp_max should be integer"
        )
        # Verify the actual values
        self.assertEqual(new_npc["hp_current"], 30)
        self.assertEqual(new_npc["hp_max"], 30)

    def test_combat_damage_hp_updates_as_integers(self):
        """Test that combat damage updates store HP as integers"""
        current_state = {
            "player_character_data": {
                "name": "Test Hero",
                "hp_current": 20,
                "hp_max": 20,
            }
        }

        # Simulating combat damage
        proposed_changes = {
            "player_character_data": {
                "hp_current": "12"  # After taking 8 damage, sent as string
            }
        }

        updated_state = update_state_with_changes(current_state, proposed_changes)

        self.assertIsInstance(
            updated_state["player_character_data"]["hp_current"],
            int,
            "HP after damage should be integer",
        )
        self.assertEqual(updated_state["player_character_data"]["hp_current"], 12)

    def test_all_numeric_fields_should_be_integers(self):
        """Test that other numeric fields are also stored as integers"""
        current_state = {"player_character_data": {"level": 1, "xp": 0}}

        proposed_changes = {
            "player_character_data": {
                "level": "2",  # String from AI
                "xp": "300",  # String from AI
            }
        }

        updated_state = update_state_with_changes(current_state, proposed_changes)

        self.assertIsInstance(
            updated_state["player_character_data"]["level"],
            int,
            "Level should be integer",
        )
        self.assertIsInstance(
            updated_state["player_character_data"]["xp"], int, "XP should be integer"
        )
        # Verify the actual values
        self.assertEqual(updated_state["player_character_data"]["level"], 2)
        self.assertEqual(updated_state["player_character_data"]["xp"], 300)

    def test_nested_numeric_fields_converted(self):
        """Test that deeply nested numeric fields are converted"""
        current_state = {"combat_state": {"round_number": 1}}

        proposed_changes = {
            "combat_state": {
                "round_number": "3"  # String from AI
            }
        }

        updated_state = update_state_with_changes(current_state, proposed_changes)

        self.assertIsInstance(
            updated_state["combat_state"]["round_number"],
            int,
            "Round number should be integer",
        )
        self.assertEqual(updated_state["combat_state"]["round_number"], 3)

    def test_invalid_numeric_strings_unchanged(self):
        """Test that invalid numeric strings are left as-is"""
        current_state = {"player_character_data": {"hp_current": 15}}

        proposed_changes = {
            "player_character_data": {
                "hp_current": "not-a-number"  # Invalid numeric string
            }
        }

        updated_state = update_state_with_changes(current_state, proposed_changes)

        # Should remain as string since it can't be converted
        self.assertEqual(
            updated_state["player_character_data"]["hp_current"], "not-a-number"
        )


class TestStructuredFieldsSaving(unittest.TestCase):
    """Test that all structured fields are saved to Firestore"""

    def setUp(self):
        """Set up test environment with mocked Firestore"""
        self.mock_db = MagicMock()
        self.mock_users_collection = MagicMock()
        self.mock_user_doc = MagicMock()
        self.mock_campaigns_collection = MagicMock()
        self.mock_campaign_doc = MagicMock()
        self.mock_story_collection = MagicMock()

        # Set up the chain of mocks for users/user_id/campaigns/campaign_id structure
        self.mock_db.collection.return_value = self.mock_users_collection
        self.mock_users_collection.document.return_value = self.mock_user_doc
        self.mock_user_doc.collection.return_value = self.mock_campaigns_collection
        self.mock_campaigns_collection.document.return_value = self.mock_campaign_doc
        self.mock_campaign_doc.collection.return_value = self.mock_story_collection

        # Mock the update method for last_played timestamp
        self.mock_campaign_doc.update = MagicMock()

        # Patch get_db to return our mock
        self.patcher = patch("firestore_service.get_db", return_value=self.mock_db)
        self.patcher.start()

    def tearDown(self):
        """Clean up patches"""
        self.patcher.stop()

    @patch.dict("os.environ", {"MOCK_SERVICES_MODE": "true"})
    def test_all_structured_fields_saved_to_firestore(self):
        """Test that all fields from structured_fields are saved to Firestore"""
        # Import constants to get field names

        # Create comprehensive structured_fields dict with all 10 fields
        structured_fields = {
            constants.FIELD_SESSION_HEADER: "Battle Round 5",
            constants.FIELD_PLANNING_BLOCK: {
                "thinking": "The player is in combat...",
                "choices": {
                    "attack": {"text": "Attack", "description": "Strike with weapon"},
                    "defend": {"text": "Defend", "description": "Raise shield"},
                },
            },
            constants.FIELD_DICE_ROLLS: ["Attack roll: 18", "Damage: 12"],
            constants.FIELD_RESOURCES: "HP: 45/60, MP: 20/30",
            constants.FIELD_GOD_MODE_RESPONSE: "Behind the scenes: Dragon has 150 HP",
            constants.FIELD_DEBUG_INFO: {"combat_round": 5, "enemy_ac": 16},
            "entities_mentioned": ["Dragon", "Player", "Guard"],
            "location_confirmed": "Dragon's Lair",
            "state_updates": {
                "player_character_data": {"hp_current": 45},
                "npc_data": {"Dragon": {"hp_current": 150}},
            },
            "turn_summary": "Player attacked the dragon for 12 damage",
        }

        # Call add_story_entry with all structured fields

        add_story_entry(
            user_id="test-user",
            campaign_id="test-campaign",
            actor=constants.ACTOR_GEMINI,
            text="The dragon roars in pain as your sword strikes true!",
            mode="combat",
            structured_fields=structured_fields,
        )

        # Verify story collection add was called
        self.mock_story_collection.add.assert_called()

        # Get the data that was passed to Firestore
        call_args = self.mock_story_collection.add.call_args[0][0]

        # Verify all structured fields were saved
        self.assertEqual(call_args["actor"], "gemini")
        self.assertEqual(call_args["mode"], "combat")
        self.assertEqual(call_args[constants.FIELD_SESSION_HEADER], "Battle Round 5")
        self.assertEqual(
            call_args[constants.FIELD_PLANNING_BLOCK]["thinking"],
            "The player is in combat...",
        )
        self.assertEqual(
            call_args[constants.FIELD_DICE_ROLLS], ["Attack roll: 18", "Damage: 12"]
        )
        self.assertEqual(call_args[constants.FIELD_RESOURCES], "HP: 45/60, MP: 20/30")
        self.assertEqual(
            call_args[constants.FIELD_GOD_MODE_RESPONSE],
            "Behind the scenes: Dragon has 150 HP",
        )
        self.assertEqual(call_args[constants.FIELD_DEBUG_INFO]["combat_round"], 5)
        self.assertEqual(call_args["entities_mentioned"], ["Dragon", "Player", "Guard"])
        self.assertEqual(call_args["location_confirmed"], "Dragon's Lair")
        self.assertEqual(
            call_args["state_updates"]["player_character_data"]["hp_current"], 45
        )
        self.assertEqual(
            call_args["turn_summary"], "Player attacked the dragon for 12 damage"
        )

        # Verify timestamp was added
        self.assertIn("timestamp", call_args)

    @patch.dict("os.environ", {"MOCK_SERVICES_MODE": "true"})
    def test_none_fields_not_saved(self):
        """Test that None values in structured_fields are not saved to Firestore"""

        # Create structured_fields with some None values
        structured_fields = {
            constants.FIELD_SESSION_HEADER: "Turn 1",
            constants.FIELD_PLANNING_BLOCK: None,  # None value
            constants.FIELD_DICE_ROLLS: [],
            constants.FIELD_RESOURCES: None,  # None value
            constants.FIELD_GOD_MODE_RESPONSE: None,  # None value
            "entities_mentioned": ["Player"],
            "location_confirmed": "Town Square",
        }

        add_story_entry(
            user_id="test-user",
            campaign_id="test-campaign",
            actor=constants.ACTOR_GEMINI,
            text="You stand in the town square.",
            structured_fields=structured_fields,
        )

        # Get the data that was passed to Firestore
        call_args = self.mock_story_collection.add.call_args[0][0]

        # Verify None fields were not saved
        self.assertNotIn(constants.FIELD_PLANNING_BLOCK, call_args)
        self.assertNotIn(constants.FIELD_RESOURCES, call_args)
        self.assertNotIn(constants.FIELD_GOD_MODE_RESPONSE, call_args)

        # Verify non-None fields were saved
        self.assertEqual(call_args[constants.FIELD_SESSION_HEADER], "Turn 1")
        self.assertEqual(call_args[constants.FIELD_DICE_ROLLS], [])
        self.assertEqual(call_args["entities_mentioned"], ["Player"])
        self.assertEqual(call_args["location_confirmed"], "Town Square")

    @patch.dict("os.environ", {"MOCK_SERVICES_MODE": "true"})
    def test_warning_logged_for_missing_structured_fields(self):
        """Test that a warning is logged when AI response lacks structured_fields"""

        with patch("firestore_service.logging_util.warning") as mock_warning:
            add_story_entry(
                user_id="test-user",
                campaign_id="test-campaign",
                actor=constants.ACTOR_GEMINI,  # AI actor
                text="Some AI response",
                structured_fields=None,  # Missing structured fields
            )

            # Verify warning was logged
            mock_warning.assert_called_once()
            warning_message = mock_warning.call_args[0][0]
            self.assertIn("AI response missing structured_fields", warning_message)
            self.assertIn("test-campaign", warning_message)

    @patch.dict("os.environ", {"MOCK_SERVICES_MODE": "true"})
    def test_no_warning_for_user_entries(self):
        """Test that no warning is logged for user entries without structured_fields"""

        with patch("firestore_service.logging_util.warning") as mock_warning:
            add_story_entry(
                user_id="test-user",
                campaign_id="test-campaign",
                actor="user",  # User actor
                text="User input",
                structured_fields=None,  # OK for user entries
            )

            # Verify no warning was logged
            mock_warning.assert_not_called()

    @patch.dict("os.environ", {"MOCK_SERVICES_MODE": "true"})
    def test_empty_narrative_with_structured_fields_creates_entry(self):
        """Test that AI responses with empty narrative but structured_fields still create Firestore entries"""

        # Mock structured fields (like from a think command)
        structured_fields = {
            "planning_block": {
                "thinking": "Analyzing the situation...",
                "choices": {
                    "choice1": {
                        "text": "Option 1",
                        "description": "First option",
                        "analysis": {
                            "pros": ["Good", "Better"],
                            "cons": ["Bad"],
                            "confidence": "High",
                        },
                    }
                },
            }
        }

        # Mock the add method to return a document reference
        mock_doc_ref = MagicMock()
        mock_doc_ref.id = "test-doc-id"
        self.mock_story_collection.add.return_value = (None, mock_doc_ref)

        # This should not raise an error even with empty text
        add_story_entry(
            user_id="test-user",
            campaign_id="test-campaign",
            actor=constants.ACTOR_GEMINI,  # AI actor
            text="",  # Empty narrative (critical test case)
            structured_fields=structured_fields,
        )

        # Verify that add was called (entry was created)
        self.mock_story_collection.add.assert_called_once()

        # Verify the placeholder text was added
        call_args = self.mock_story_collection.add.call_args[0][0]
        self.assertEqual(
            call_args["text"], "[Internal thoughts and analysis - see planning block]"
        )
        self.assertEqual(call_args["actor"], constants.ACTOR_GEMINI)

        # Verify structured fields were merged into the entry data
        self.assertIn("planning_block", call_args)
        self.assertEqual(
            call_args["planning_block"], structured_fields["planning_block"]
        )


# NOTE: TestWriteThenReadFeatureFlag class removed
# Since write-then-read is now the default behavior (no feature flag),
# the conditional logic tests are no longer relevant.
# Write-then-read verification is always enabled for data integrity.


if __name__ == "__main__":
    unittest.main()
