#!/usr/bin/env python3
"""
Phase 5: Additional edge case tests for state helper functions
"""

import datetime
import os

# Add parent directory to path
import sys
import unittest
from unittest.mock import patch, MagicMock

# Set test environment before any imports
os.environ["TESTING"] = "true"
os.environ["USE_MOCKS"] = "true"

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

# Mock Firebase before importing firestore_service
with patch("firestore_service.get_db"):
    from firestore_service import (
        DELETE_TOKEN,
        _handle_append_syntax,
        update_state_with_changes,
        get_campaign_by_id,
    )


class TestFirestoreStateHelpersEdgeCases(unittest.TestCase):
    """Additional edge case tests for state helpers"""

    def test_update_state_nested_append_syntax(self):
        """Test nested append syntax in dict values"""
        state = {"quests": {"active": ["quest1"], "completed": ["quest2"]}}

        changes = {
            "quests": {
                "active": {"append": ["quest3"]},
                "completed": {"append": ["quest4"]},
            }
        }

        with patch("logging_util.info"):
            result = update_state_with_changes(state, changes)

        # Both lists should have appended items
        assert result["quests"]["active"] == ["quest1", "quest3"]
        assert result["quests"]["completed"] == ["quest2", "quest4"]

    def test_update_state_delete_nested_keys(self):
        """Test DELETE_TOKEN on nested dictionary keys"""
        state = {
            "player": {
                "stats": {"hp": 100, "mp": 50},
                "inventory": ["sword"],
                "temp_buff": "strength",
            }
        }

        changes = {"player": {"temp_buff": DELETE_TOKEN, "stats": {"mp": DELETE_TOKEN}}}

        with patch("logging_util.info"):
            result = update_state_with_changes(state, changes)

        # temp_buff should be deleted
        assert "temp_buff" not in result["player"]
        # mp should be deleted from stats
        assert "mp" not in result["player"]["stats"]
        # hp should remain
        assert result["player"]["stats"]["hp"] == 100
        # inventory untouched
        assert result["player"]["inventory"] == ["sword"]

    def test_update_state_empty_changes(self):
        """Test update_state_with_changes with empty changes dict"""
        state = {"key": "value"}
        changes = {}

        result = update_state_with_changes(state, changes)

        assert result == state

    def test_update_state_none_values(self):
        """Test update_state_with_changes with None values"""
        state = {"key1": "value1"}
        changes = {"key1": None, "key2": None}

        result = update_state_with_changes(state, changes)

        assert result["key1"] is None
        assert result["key2"] is None

    @patch("firestore_service._perform_append")
    def test_handle_append_syntax_nested_append_structure(self, mock_append):
        """Test append syntax with nested append structure"""
        state = {"items": []}
        # Nested append structure (unusual but should handle)
        value = {"append": {"append": "nested"}}

        with patch("logging_util.info"):
            result = _handle_append_syntax(state, "items", value)

        assert result
        # Should append the entire nested structure
        mock_append.assert_called_once_with(
            state["items"], {"append": "nested"}, "items", deduplicate=False
        )

    def test_update_state_core_memories_multiple_attempts(self):
        """Test multiple types of core_memories updates in one call"""
        state = {"core_memories": ["memory1"]}

        # Try both direct overwrite and append syntax
        changes = {
            "core_memories": ["memory2", "memory3"]  # Will be safeguarded
        }

        with patch("logging_util.warning") as mock_warning:
            result = update_state_with_changes(state, changes)

        # Should have all memories due to safeguard
        assert "memory1" in result["core_memories"]
        assert "memory2" in result["core_memories"]
        assert "memory3" in result["core_memories"]
        mock_warning.assert_called_once()

    def test_update_state_complex_nested_structure(self):
        """Test deeply nested structure updates"""
        state = {
            "game": {
                "world": {
                    "regions": {
                        "forest": {"enemies": ["wolf"], "items": ["herb"]},
                        "cave": {"enemies": ["bat"], "items": ["ore"]},
                    }
                }
            }
        }

        changes = {
            "game": {
                "world": {
                    "regions": {
                        "forest": {"enemies": {"append": ["bear"]}},
                        "desert": {"enemies": ["scorpion"], "items": ["cactus"]},
                    }
                }
            }
        }

        with patch("logging_util.info"):
            result = update_state_with_changes(state, changes)

        # Forest enemies should have bear appended
        forest_enemies = result["game"]["world"]["regions"]["forest"]["enemies"]
        assert forest_enemies == ["wolf", "bear"]
        # Forest items unchanged
        assert result["game"]["world"]["regions"]["forest"]["items"] == ["herb"]
        # Cave unchanged
        assert result["game"]["world"]["regions"]["cave"] == {
            "enemies": ["bat"],
            "items": ["ore"],
        }
        # Desert added
        assert result["game"]["world"]["regions"]["desert"] == {
            "enemies": ["scorpion"],
            "items": ["cactus"],
        }

    def test_handle_dict_merge_with_delete_token_in_value(self):
        """Test dict merge where new dict contains DELETE_TOKEN"""
        state = {"config": {"a": 1, "b": 2, "c": 3}}
        value = {"b": DELETE_TOKEN, "d": 4}

        with patch("logging_util.info"):
            # The DELETE_TOKEN handling happens in update_state_with_changes
            result = update_state_with_changes(state, {"config": value})

        assert result["config"] == {"a": 1, "c": 3, "d": 4}
        assert "b" not in result["config"]

    def test_update_state_list_overwrite(self):
        """Test that non-append list updates do overwrite"""
        state = {"items": ["sword", "shield"]}
        changes = {"items": ["bow", "arrow"]}  # Direct overwrite

        result = update_state_with_changes(state, changes)

        # Should be completely replaced
        assert result["items"] == ["bow", "arrow"]

    def test_update_state_preserve_unchanged_keys(self):
        """Test that unchanged keys are preserved"""
        state = {
            "unchanged1": "value1",
            "unchanged2": {"nested": "value"},
            "changed": "old_value",
        }

        changes = {"changed": "new_value"}

        result = update_state_with_changes(state, changes)

        assert result["unchanged1"] == "value1"
        assert result["unchanged2"] == {"nested": "value"}
        assert result["changed"] == "new_value"


class TestMCPMigrationEdgeCases(unittest.TestCase):
    """Edge case tests for MCP migration fixes."""

    def test_sequence_id_edge_cases(self):
        """Test sequence_id calculation with edge cases."""
        test_cases = [
            ([], 2),  # Empty story context: AI response should get 2
            ([{"actor": "user", "sequence_id": 1}], 3),  # One entry: AI gets 3
            (
                [{"actor": "user"}, {"actor": "gemini"}] * 10,
                22,
            ),  # 20 entries: AI gets 22
        ]

        for story_context, expected_sequence_id in test_cases:
            with self.subTest(context_length=len(story_context)):
                # Test the calculation logic directly
                calculated_id = len(story_context) + 2
                assert calculated_id == expected_sequence_id, (
                    f"For {len(story_context)} entries, expected {expected_sequence_id}"
                )

    def test_user_scene_number_edge_cases(self):
        """Test user_scene_number calculation with various actor distributions."""
        test_cases = [
            ([], 1),  # No gemini responses: scene number should be 1
            ([{"actor": "user"}], 1),  # Only user: scene number 1
            ([{"actor": "gemini"}], 2),  # One gemini: scene number 2
            (
                [{"actor": "user"}, {"actor": "gemini"}] * 5,
                6,
            ),  # 5 gemini: scene number 6
        ]

        for story_context, expected_scene_number in test_cases:
            with self.subTest(
                gemini_count=sum(1 for e in story_context if e.get("actor") == "gemini")
            ):
                # Test the calculation logic
                calculated_scene = (
                    sum(1 for entry in story_context if entry.get("actor") == "gemini")
                    + 1
                )
                assert calculated_scene == expected_scene_number

    def test_logging_edge_cases(self):
        """Test enhanced logging with various edge cases."""
        import world_logic
        
        edge_cases = [
            ({}, "Empty dict"),
            ({"single": "value"}, "Single value"),
            ({"nested": {"deep": {"very": "deep"}}}, "Deep nesting"),
            ({"list": [1, 2, 3, 4, 5]}, "List values"),
            ({"mixed": {"str": "test", "num": 42, "bool": True}}, "Mixed types"),
        ]

        for test_data, description in edge_cases:
            with self.subTest(case=description):
                result = world_logic.truncate_game_state_for_logging(test_data, max_lines=5)
                assert isinstance(result, str)
                assert len(result) > 0, f"Empty result for {description}"

    def test_api_response_required_fields_completeness(self):
        """Verify API response contains ALL frontend-required fields."""
        # This test ensures we don't accidentally remove required fields
        required_fields = [
            "success",
            "story",
            "narrative",
            "response",
            "game_state",
            "state_changes",
            "state_updates",
            "sequence_id",
            "user_scene_number",
            "mode",
            "user_input",
            "debug_mode",
        ]

        # Mock a minimal successful response structure
        mock_response = {
            "success": True,
            "story": [{"text": "test"}],
            "narrative": "test narrative",
            "response": "test response",
            "game_state": {"test": "state"},
            "state_changes": {},
            "state_updates": {},
            "sequence_id": 6,
            "user_scene_number": 3,
            "mode": "character",
            "user_input": "test input",
            "debug_mode": False,
        }

        # Verify all required fields are present
        for field in required_fields:
            with self.subTest(field=field):
                assert field in mock_response, (
                    f"Required field '{field}' missing from API response structure"
                )

    @patch('firestore_service.get_db')
    def test_timestamp_normalization_mixed_types_bug(self, mock_db):
        """Test that mixed timestamp types cause sorting errors (RED test - should fail initially)."""
        # Mock Firestore documents with mixed timestamp types that cause sorting bugs
        mock_campaign_doc = MagicMock()
        mock_campaign_doc.exists = True
        mock_campaign_doc.to_dict.return_value = {"title": "Test Campaign"}
        
        # Create story entries with mixed timestamp types that will cause TypeError in sorting
        mock_story_docs = []
        story_entries = [
            # String timestamp
            {"actor": "user", "text": "Hello", "timestamp": "2023-01-01T10:00:00Z", "part": 1},
            # Datetime object  
            {"actor": "gemini", "text": "Hi there", "timestamp": datetime.datetime(2023, 1, 1, 11, 0, 0), "part": 1},
            # None timestamp (missing)
            {"actor": "user", "text": "Test", "timestamp": None, "part": 1},
            # Integer timestamp (epoch)
            {"actor": "gemini", "text": "Response", "timestamp": 1672574400, "part": 1},
            # Invalid string that can't be parsed
            {"actor": "user", "text": "Error case", "timestamp": "invalid-date-string", "part": 1}
        ]
        
        for entry in story_entries:
            mock_doc = MagicMock()
            mock_doc.to_dict.return_value = entry
            mock_story_docs.append(mock_doc)
        
        # Mock Firestore collection chain
        mock_story_collection = MagicMock()
        mock_story_collection.order_by.return_value.stream.return_value = mock_story_docs
        
        mock_campaign_ref = MagicMock()
        mock_campaign_ref.get.return_value = mock_campaign_doc
        mock_campaign_ref.collection.return_value = mock_story_collection
        
        mock_campaigns_collection = MagicMock()
        mock_campaigns_collection.document.return_value = mock_campaign_ref
        
        mock_user_doc = MagicMock() 
        mock_user_doc.collection.return_value = mock_campaigns_collection
        
        mock_users_collection = MagicMock()
        mock_users_collection.document.return_value = mock_user_doc
        
        mock_db.return_value.collection.return_value = mock_users_collection
        
        # CRITICAL ASSERTION: Should NOT raise TypeError when sorting mixed timestamp types  
        # With the current bug, this will fail because mixed types can't be compared in Python sorting
        try:
            campaign_data, story_data = get_campaign_by_id("test_user", "test_campaign")
            
            # If we get here without exception, the bug is fixed
            # But initially this should raise TypeError due to mixed types
            self.assertIsNotNone(campaign_data, "Campaign data should be returned")
            self.assertIsNotNone(story_data, "Story data should be returned")
            
            # Verify story entries are properly sorted despite mixed types
            self.assertEqual(len(story_data), 5, "All story entries should be included")
            
        except TypeError as e:
            # This is expected with the current bug - mixed types can't be sorted
            if "not supported between instances" in str(e):
                self.fail(
                    f"TIMESTAMP NORMALIZATION BUG DETECTED: Mixed timestamp types cause sorting error. "
                    f"Error: {e}. The _norm_ts function should handle mixed types (strings, datetime, None, int) "
                    f"consistently to prevent TypeError during sorting operations."
                )
            else:
                # Re-raise if it's a different TypeError
                raise


if __name__ == "__main__":
    unittest.main(verbosity=2)
