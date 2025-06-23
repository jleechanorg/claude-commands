"""
Unit tests for game_state.py module.
Tests the GameState class, MigrationStatus enum, and related functions.
"""
import unittest
import datetime
from unittest.mock import patch, MagicMock
import json

from game_state import GameState, MigrationStatus, get_initial_game_state
from firestore_service import update_state_with_changes, _perform_append
import main


class TestMigrationStatus(unittest.TestCase):
    """Test cases for the MigrationStatus enum."""
    
    def test_migration_status_values(self):
        """Test that all enum values are correct."""
        self.assertEqual(MigrationStatus.NOT_CHECKED.value, "NOT_CHECKED")
        self.assertEqual(MigrationStatus.MIGRATION_PENDING.value, "MIGRATION_PENDING")
        self.assertEqual(MigrationStatus.MIGRATED.value, "MIGRATED")
        self.assertEqual(MigrationStatus.NO_LEGACY_DATA.value, "NO_LEGACY_DATA")
    
    def test_migration_status_enum_creation(self):
        """Test creating enum instances from values."""
        self.assertEqual(MigrationStatus("NOT_CHECKED"), MigrationStatus.NOT_CHECKED)
        self.assertEqual(MigrationStatus("MIGRATED"), MigrationStatus.MIGRATED)


class TestGameState(unittest.TestCase):
    """Test cases for the GameState class."""
    
    def test_default_initialization(self):
        """Test GameState initialization with default values."""
        gs = GameState()
        
        # Test default values
        self.assertEqual(gs.game_state_version, 1)
        self.assertEqual(gs.player_character_data, {})
        self.assertEqual(gs.world_data, {})
        self.assertEqual(gs.npc_data, {})
        self.assertEqual(gs.custom_campaign_state, {})
        self.assertEqual(gs.migration_status, MigrationStatus.NOT_CHECKED)
        
        # Test that timestamp is recent
        now = datetime.datetime.now(datetime.timezone.utc)
        time_diff = abs((now - gs.last_state_update_timestamp).total_seconds())
        self.assertLess(time_diff, 5, "Timestamp should be within 5 seconds of now")
    
    def test_initialization_with_kwargs(self):
        """Test GameState initialization with provided values."""
        custom_time = datetime.datetime(2023, 1, 1, tzinfo=datetime.timezone.utc)
        custom_data = {
            "game_state_version": 2,
            "player_character_data": {"name": "Hero", "level": 5},
            "world_data": {"location": "Forest"},
            "npc_data": {"npc1": {"name": "Villager"}},
            "custom_campaign_state": {"quest_active": True},
            "last_state_update_timestamp": custom_time,
            "migration_status": MigrationStatus.MIGRATED.value,
            "extra_field": "extra_value"
        }
        
        gs = GameState(**custom_data)
        
        self.assertEqual(gs.game_state_version, 2)
        self.assertEqual(gs.player_character_data, {"name": "Hero", "level": 5})
        self.assertEqual(gs.world_data, {"location": "Forest"})
        self.assertEqual(gs.npc_data, {"npc1": {"name": "Villager"}})
        self.assertEqual(gs.custom_campaign_state, {"quest_active": True})
        self.assertEqual(gs.last_state_update_timestamp, custom_time)
        self.assertEqual(gs.migration_status, MigrationStatus.MIGRATED)
        self.assertEqual(gs.extra_field, "extra_value")
    
    def test_migration_status_invalid_value(self):
        """Test that invalid migration status defaults to NOT_CHECKED."""
        gs = GameState(migration_status="INVALID_STATUS")
        self.assertEqual(gs.migration_status, MigrationStatus.NOT_CHECKED)
    
    def test_migration_status_none_value(self):
        """Test that None migration status defaults to NOT_CHECKED."""
        gs = GameState(migration_status=None)
        self.assertEqual(gs.migration_status, MigrationStatus.NOT_CHECKED)
    
    def test_to_dict(self):
        """Test serialization to dictionary."""
        custom_time = datetime.datetime(2023, 1, 1, tzinfo=datetime.timezone.utc)
        gs = GameState(
            game_state_version=3,
            player_character_data={"name": "Test"},
            migration_status=MigrationStatus.MIGRATED.value,
            last_state_update_timestamp=custom_time,
            extra_field="test_value"
        )
        
        result = gs.to_dict()
        
        expected = {
            "game_state_version": 3,
            "player_character_data": {"name": "Test"},
            "world_data": {},
            "npc_data": {},
            "custom_campaign_state": {},
            "last_state_update_timestamp": custom_time,
            "migration_status": "MIGRATED",  # Should be string value
            "extra_field": "test_value"
        }
        
        self.assertEqual(result, expected)
    
    def test_to_dict_with_enum_object(self):
        """Test serialization when migration_status is an enum object."""
        gs = GameState()
        gs.migration_status = MigrationStatus.MIGRATED  # Set as enum object
        
        result = gs.to_dict()
        
        self.assertEqual(result["migration_status"], "MIGRATED")
    
    def test_from_dict_with_valid_data(self):
        """Test deserialization from dictionary."""
        custom_time = datetime.datetime(2023, 1, 1, tzinfo=datetime.timezone.utc)
        source_dict = {
            "game_state_version": 2,
            "player_character_data": {"name": "Hero"},
            "migration_status": "MIGRATED",
            "last_state_update_timestamp": custom_time,
            "custom_field": "custom_value"
        }
        
        gs = GameState.from_dict(source_dict)
        
        self.assertEqual(gs.game_state_version, 2)
        self.assertEqual(gs.player_character_data, {"name": "Hero"})
        self.assertEqual(gs.migration_status, MigrationStatus.MIGRATED)
        self.assertEqual(gs.last_state_update_timestamp, custom_time)
        self.assertEqual(gs.custom_field, "custom_value")
    
    def test_from_dict_with_none(self):
        """Test from_dict returns None when source is None."""
        result = GameState.from_dict(None)
        self.assertIsNone(result)
    
    def test_from_dict_with_empty_dict(self):
        """Test from_dict returns None when source is empty dict."""
        result = GameState.from_dict({})
        self.assertIsNone(result)
    
    def test_dynamic_attribute_setting(self):
        """Test that dynamic attributes are set correctly."""
        gs = GameState(
            custom_attr1="value1",
            custom_attr2=42,
            custom_attr3=["list", "value"]
        )
        
        self.assertEqual(gs.custom_attr1, "value1")
        self.assertEqual(gs.custom_attr2, 42)
        self.assertEqual(gs.custom_attr3, ["list", "value"])
    
    def test_attribute_precedence(self):
        """Test that existing attributes are not overwritten by dynamic setting."""
        gs = GameState(game_state_version=5)
        
        # The constructor should have already set game_state_version
        # Dynamic attribute setting should not create a duplicate
        self.assertEqual(gs.game_state_version, 5)
        self.assertFalse(hasattr(gs, 'game_state_version_duplicate'))


class TestGetInitialGameState(unittest.TestCase):
    """Test cases for get_initial_game_state function."""
    
    def test_get_initial_game_state(self):
        """Test that get_initial_game_state returns a proper dictionary."""
        result = get_initial_game_state()
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["game_state_version"], 1)
        self.assertEqual(result["player_character_data"], {})
        self.assertEqual(result["world_data"], {})
        self.assertEqual(result["npc_data"], {})
        self.assertEqual(result["custom_campaign_state"], {})
        self.assertEqual(result["migration_status"], "NOT_CHECKED")
        self.assertIn("last_state_update_timestamp", result)


class TestUpdateStateWithChanges(unittest.TestCase):
    """Test cases for the update_state_with_changes function."""
    
    def test_simple_overwrite(self):
        """Test simple value overwriting."""
        state = {"key1": "old_value", "key2": 42}
        changes = {"key1": "new_value", "key3": "added_value"}
        
        result = update_state_with_changes(state, changes)
        
        expected = {"key1": "new_value", "key2": 42, "key3": "added_value"}
        self.assertEqual(result, expected)
    
    def test_nested_dict_merge(self):
        """Test recursive merging of nested dictionaries."""
        state = {
            "player": {"name": "Hero", "level": 1, "stats": {"hp": 100}},
            "world": {"location": "Town"}
        }
        changes = {
            "player": {"level": 2, "stats": {"mp": 50}},
            "world": {"weather": "sunny"}
        }
        
        result = update_state_with_changes(state, changes)
        
        expected = {
            "player": {"name": "Hero", "level": 2, "stats": {"hp": 100, "mp": 50}},
            "world": {"location": "Town", "weather": "sunny"}
        }
        self.assertEqual(result, expected)
    
    def test_explicit_append_syntax(self):
        """Test explicit append using {'append': ...} syntax."""
        state = {"items": ["sword", "shield"]}
        changes = {"items": {"append": ["potion", "key"]}}
        
        result = update_state_with_changes(state, changes)
        
        expected = {"items": ["sword", "shield", "potion", "key"]}
        self.assertEqual(result, expected)
    
    def test_explicit_append_to_nonexistent_key(self):
        """Test append to a key that doesn't exist yet."""
        state = {"other_key": "value"}
        changes = {"new_list": {"append": ["item1", "item2"]}}
        
        result = update_state_with_changes(state, changes)
        
        expected = {"other_key": "value", "new_list": ["item1", "item2"]}
        self.assertEqual(result, expected)
    
    def test_explicit_append_to_non_list(self):
        """Test append to a key that exists but isn't a list."""
        state = {"key": "not_a_list"}
        changes = {"key": {"append": ["item1"]}}
        
        result = update_state_with_changes(state, changes)
        
        expected = {"key": ["item1"]}
        self.assertEqual(result, expected)
    
    def test_core_memories_safeguard(self):
        """Test that core_memories is protected from direct overwrite."""
        state = {"core_memories": ["memory1", "memory2"]}
        changes = {"core_memories": ["new_memory1", "new_memory2"]}
        
        result = update_state_with_changes(state, changes)
        
        # Should append, not overwrite
        expected = {"core_memories": ["memory1", "memory2", "new_memory1", "new_memory2"]}
        self.assertEqual(result, expected)
    
    def test_core_memories_deduplication(self):
        """Test that core_memories deduplicates when appending."""
        state = {"core_memories": ["memory1", "memory2"]}
        changes = {"core_memories": ["memory2", "memory3"]}  # memory2 is duplicate
        
        result = update_state_with_changes(state, changes)
        
        # Should deduplicate memory2
        expected = {"core_memories": ["memory1", "memory2", "memory3"]}
        self.assertEqual(result, expected)
    
    def test_core_memories_to_nonexistent_key(self):
        """Test core_memories safeguard when key doesn't exist."""
        state = {"other_key": "value"}
        changes = {"core_memories": ["memory1", "memory2"]}
        
        result = update_state_with_changes(state, changes)
        
        expected = {"other_key": "value", "core_memories": ["memory1", "memory2"]}
        self.assertEqual(result, expected)
    
    def test_mixed_operations(self):
        """Test a complex scenario with multiple operation types."""
        state = {
            "player": {"name": "Hero", "level": 1},
            "inventory": ["sword"],
            "core_memories": ["memory1"],
            "simple_value": "old"
        }
        changes = {
            "player": {"level": 2, "gold": 100},
            "inventory": {"append": ["potion"]},
            "core_memories": ["memory1", "memory2"],  # Should deduplicate
            "simple_value": "new",
            "new_key": "new_value"
        }
        
        result = update_state_with_changes(state, changes)
        
        expected = {
            "player": {"name": "Hero", "level": 2, "gold": 100},
            "inventory": ["sword", "potion"],
            "core_memories": ["memory1", "memory2"],  # Deduplicated
            "simple_value": "new",
            "new_key": "new_value"
        }
        self.assertEqual(result, expected)
    
    def test_deep_nesting(self):
        """Test very deep nested dictionary merging."""
        state = {
            "level1": {
                "level2": {
                    "level3": {
                        "value": "old",
                        "keep": "this"
                    }
                }
            }
        }
        changes = {
            "level1": {
                "level2": {
                    "level3": {
                        "value": "new",
                        "add": "this"
                    }
                }
            }
        }
        
        result = update_state_with_changes(state, changes)
        
        expected = {
            "level1": {
                "level2": {
                    "level3": {
                        "value": "new",
                        "keep": "this",
                        "add": "this"
                    }
                }
            }
        }
        self.assertEqual(result, expected)


class TestPerformAppend(unittest.TestCase):
    """Test cases for the _perform_append helper function."""
    
    def test_append_single_item(self):
        """Test appending a single item."""
        target_list = ["item1", "item2"]
        _perform_append(target_list, "item3", "test_key")
        
        self.assertEqual(target_list, ["item1", "item2", "item3"])
    
    def test_append_multiple_items(self):
        """Test appending multiple items."""
        target_list = ["item1"]
        _perform_append(target_list, ["item2", "item3"], "test_key")
        
        self.assertEqual(target_list, ["item1", "item2", "item3"])
    
    def test_append_with_deduplication(self):
        """Test appending with deduplication enabled."""
        target_list = ["item1", "item2"]
        _perform_append(target_list, ["item2", "item3"], "test_key", deduplicate=True)
        
        self.assertEqual(target_list, ["item1", "item2", "item3"])
    
    def test_append_without_deduplication(self):
        """Test appending without deduplication (default)."""
        target_list = ["item1", "item2"]
        _perform_append(target_list, ["item2", "item3"], "test_key", deduplicate=False)
        
        self.assertEqual(target_list, ["item1", "item2", "item2", "item3"])
    
    def test_append_all_duplicates(self):
        """Test appending when all items are duplicates."""
        target_list = ["item1", "item2"]
        _perform_append(target_list, ["item1", "item2"], "test_key", deduplicate=True)
        
        # Should remain unchanged
        self.assertEqual(target_list, ["item1", "item2"])


class TestMainStateFunctions(unittest.TestCase):
    """Test cases for state-related functions in main.py."""
    
    def test_cleanup_legacy_state_with_dot_keys(self):
        """Test cleanup of legacy keys with dots."""
        state_dict = {
            "player.name": "Hero",
            "player.level": 5,
            "normal_key": "value",
            "world.location": "Forest"
        }
        
        cleaned, was_changed, num_deleted = main._cleanup_legacy_state(state_dict)
        
        expected_cleaned = {"normal_key": "value"}
        self.assertEqual(cleaned, expected_cleaned)
        self.assertTrue(was_changed)
        self.assertEqual(num_deleted, 3)
    
    def test_cleanup_legacy_state_with_world_time(self):
        """Test cleanup of legacy world_time key."""
        state_dict = {
            "world_time": "12:00",
            "normal_key": "value"
        }
        
        cleaned, was_changed, num_deleted = main._cleanup_legacy_state(state_dict)
        
        expected_cleaned = {"normal_key": "value"}
        self.assertEqual(cleaned, expected_cleaned)
        self.assertTrue(was_changed)
        self.assertEqual(num_deleted, 1)
    
    def test_cleanup_legacy_state_no_changes(self):
        """Test cleanup when no legacy keys are present."""
        state_dict = {
            "normal_key1": "value1",
            "normal_key2": "value2"
        }
        
        cleaned, was_changed, num_deleted = main._cleanup_legacy_state(state_dict)
        
        self.assertEqual(cleaned, state_dict)
        self.assertFalse(was_changed)
        self.assertEqual(num_deleted, 0)
    
    def test_cleanup_legacy_state_empty_dict(self):
        """Test cleanup with empty dictionary."""
        state_dict = {}
        
        cleaned, was_changed, num_deleted = main._cleanup_legacy_state(state_dict)
        
        self.assertEqual(cleaned, {})
        self.assertFalse(was_changed)
        self.assertEqual(num_deleted, 0)
    
    def test_format_state_changes_simple(self):
        """Test formatting simple state changes."""
        changes = {"player_name": "Hero", "level": 5}
        
        result = main.format_state_changes(changes, for_html=False)
        
        self.assertIn("Game state updated (2 entries):", result)
        self.assertIn("player_name: \"Hero\"", result)
        self.assertIn("level: 5", result)
    
    def test_format_state_changes_nested(self):
        """Test formatting nested state changes."""
        changes = {
            "player": {"name": "Hero", "stats": {"hp": 100}},
            "world": {"location": "Forest"}
        }
        
        result = main.format_state_changes(changes, for_html=False)
        
        self.assertIn("Game state updated (3 entries):", result)
        self.assertIn("player.name: \"Hero\"", result)
        self.assertIn("player.stats.hp: 100", result)
        self.assertIn("world.location: \"Forest\"", result)
    
    def test_format_state_changes_html(self):
        """Test formatting state changes for HTML output."""
        changes = {"key": "value"}
        
        result = main.format_state_changes(changes, for_html=True)
        
        self.assertIn("<ul>", result)
        self.assertIn("<li><code>", result)
        self.assertIn("</code></li>", result)
        self.assertIn("</ul>", result)
    
    def test_format_state_changes_empty(self):
        """Test formatting empty state changes."""
        result = main.format_state_changes({}, for_html=False)
        self.assertEqual(result, "No state changes.")
        
        result = main.format_state_changes(None, for_html=False)
        self.assertEqual(result, "No state changes.")
    
    def test_parse_set_command_simple(self):
        """Test parsing simple set commands."""
        payload = "key1 = \"value1\"\nkey2 = 42"
        
        result = main.parse_set_command(payload)
        
        expected = {"key1": "value1", "key2": 42}
        self.assertEqual(result, expected)
    
    def test_parse_set_command_nested(self):
        """Test parsing nested dot notation."""
        payload = "player.name = \"Hero\"\nplayer.level = 5\nworld.location = \"Forest\""
        
        result = main.parse_set_command(payload)
        
        expected = {
            "player": {"name": "Hero", "level": 5},
            "world": {"location": "Forest"}
        }
        self.assertEqual(result, expected)
    
    def test_parse_set_command_append(self):
        """Test parsing append operations."""
        payload = "items.append = \"sword\"\nitems.append = \"shield\""
        
        result = main.parse_set_command(payload)
        
        expected = {"items": {"append": ["sword", "shield"]}}
        self.assertEqual(result, expected)
    
    def test_parse_set_command_invalid_json(self):
        """Test parsing with invalid JSON values."""
        payload = "valid_key = \"valid_value\"\ninvalid_key = invalid_json"
        
        result = main.parse_set_command(payload)
        
        # Should skip invalid line
        expected = {"valid_key": "valid_value"}
        self.assertEqual(result, expected)
    
    def test_parse_set_command_empty_lines(self):
        """Test parsing with empty lines and no equals signs."""
        payload = "key1 = \"value1\"\n\nkey2 = \"value2\"\nno_equals_sign\n"
        
        result = main.parse_set_command(payload)
        
        expected = {"key1": "value1", "key2": "value2"}
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main() 