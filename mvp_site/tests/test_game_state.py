"""
Unit tests for game_state.py module.
Tests the GameState class and related functions.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import datetime
import unittest

import main

from firestore_service import _perform_append, update_state_with_changes
from game_state import GameState


class TestGameState(unittest.TestCase):
    """Test cases for the GameState class."""

    def test_validate_checkpoint_consistency_dict_location_bug(self):
        """Test that validate_checkpoint_consistency handles dict location objects correctly."""
        # Create a GameState with dict location (reproduces bug)
        gs = GameState()
        gs.world_data = {
            "current_location": {
                "name": "Forest",
                "type": "outdoor",
            },  # Dict, not string
            "current_location_name": None,
        }

        # This should not raise AttributeError
        discrepancies = gs.validate_checkpoint_consistency(
            "The character is in the forest"
        )

        # Should handle dict gracefully and not crash
        self.assertIsInstance(discrepancies, list)

    def test_debug_mode_default_true(self):
        """Test that debug_mode defaults to True per PR changes."""
        gs = GameState()
        self.assertTrue(gs.debug_mode)

        # Also test it's included in serialization
        data = gs.to_dict()
        self.assertIn("debug_mode", data)
        self.assertTrue(data["debug_mode"])

    def test_debug_mode_can_be_set_false(self):
        """Test that debug_mode can be explicitly set to False."""
        gs = GameState(debug_mode=False)
        self.assertFalse(gs.debug_mode)

        # Test serialization
        data = gs.to_dict()
        self.assertIn("debug_mode", data)
        self.assertFalse(data["debug_mode"])

    def test_debug_mode_from_dict(self):
        """Test that debug_mode is properly loaded from dict."""
        # Test loading True
        data = {"debug_mode": True}
        gs = GameState.from_dict(data)
        self.assertTrue(gs.debug_mode)

        # Test loading False
        data = {"debug_mode": False}
        gs = GameState.from_dict(data)
        self.assertFalse(gs.debug_mode)

        # Test missing debug_mode defaults to True
        data = {"game_state_version": 1}
        gs = GameState.from_dict(data)
        self.assertTrue(gs.debug_mode)

    def test_default_initialization(self):
        """Test GameState initialization with default values."""
        gs = GameState()

        # Test default values
        self.assertEqual(gs.game_state_version, 1)
        self.assertEqual(gs.player_character_data, {})
        self.assertEqual(gs.world_data, {})
        self.assertEqual(gs.npc_data, {})
        self.assertEqual(gs.custom_campaign_state, {"attribute_system": "D&D"})

        # Test that timestamp is recent
        now = datetime.datetime.now(datetime.UTC)
        time_diff = abs((now - gs.last_state_update_timestamp).total_seconds())
        self.assertLess(time_diff, 5, "Timestamp should be within 5 seconds of now")

        # Test debug_mode defaults to True (PR change)
        self.assertTrue(gs.debug_mode, "debug_mode should default to True")

    def test_initialization_with_kwargs(self):
        """Test GameState initialization with provided values."""
        custom_time = datetime.datetime(2023, 1, 1, tzinfo=datetime.UTC)
        custom_data = {
            "game_state_version": 2,
            "player_character_data": {"name": "Hero", "level": 5},
            "world_data": {"location": "Forest"},
            "npc_data": {"npc1": {"name": "Villager"}},
            "custom_campaign_state": {"quest_active": True},
            "last_state_update_timestamp": custom_time,
            "extra_field": "extra_value",
        }

        gs = GameState(**custom_data)

        self.assertEqual(gs.game_state_version, 2)
        self.assertEqual(gs.player_character_data, {"name": "Hero", "level": 5})
        self.assertEqual(gs.world_data, {"location": "Forest"})
        self.assertEqual(gs.npc_data, {"npc1": {"name": "Villager"}})
        self.assertEqual(
            gs.custom_campaign_state, {"quest_active": True, "attribute_system": "D&D"}
        )
        self.assertEqual(gs.last_state_update_timestamp, custom_time)
        self.assertEqual(gs.extra_field, "extra_value")

    def test_to_dict(self):
        """Test serialization to dictionary."""
        custom_time = datetime.datetime(2023, 1, 1, tzinfo=datetime.UTC)
        gs = GameState(
            game_state_version=3,
            player_character_data={"name": "Test"},
            last_state_update_timestamp=custom_time,
            extra_field="test_value",
        )

        result = gs.to_dict()

        expected = {
            "game_state_version": 3,
            "player_character_data": {"name": "Test"},
            "world_data": {},
            "npc_data": {},
            "custom_campaign_state": {"attribute_system": "D&D"},
            "combat_state": {"in_combat": False},  # Added combat_state field
            "last_state_update_timestamp": custom_time,
            "extra_field": "test_value",
            # Time pressure structures
            "time_sensitive_events": {},
            "npc_agendas": {},
            "world_resources": {},
            "time_pressure_warnings": {},
            "debug_mode": True,  # Should default to True per PR changes
        }

        self.assertEqual(result, expected)

    def test_from_dict_with_valid_data(self):
        """Test deserialization from dictionary."""
        custom_time = datetime.datetime(2023, 1, 1, tzinfo=datetime.UTC)
        source_dict = {
            "game_state_version": 2,
            "player_character_data": {"name": "Hero"},
            "last_state_update_timestamp": custom_time,
            "custom_field": "custom_value",
        }

        gs = GameState.from_dict(source_dict)

        self.assertEqual(gs.game_state_version, 2)
        self.assertEqual(gs.player_character_data, {"name": "Hero"})
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
            custom_attr1="value1", custom_attr2=42, custom_attr3=["list", "value"]
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
        self.assertFalse(hasattr(gs, "game_state_version_duplicate"))

    def test_three_layer_nesting_all_types(self):
        """Test GameState with 3 layers of nesting and all valid Python data types."""
        test_datetime = datetime.datetime(2023, 6, 15, 14, 30, 45, tzinfo=datetime.UTC)

        complex_data = {
            "game_state_version": 1,
            "player_character_data": {
                "personal_info": {
                    "basic_stats": {
                        "name": "TestHero",  # string
                        "level": 42,  # int
                        "experience_ratio": 0.75,  # float
                        "is_alive": True,  # boolean
                        "special_abilities": None,  # None
                        "inventory": ["sword", "potion"],  # list
                        "equipped_gear": {  # nested dict
                            "weapon": "magic_sword",
                            "armor": "leather_vest",
                        },
                    }
                }
            },
            "world_data": {
                "locations": {
                    "current_area": {
                        "area_name": "Enchanted Forest",
                        "coordinates": [100, 250],
                        "temperature": 22.5,
                        "is_safe": False,
                        "discovered_secrets": None,
                        "available_quests": [],
                        "environmental_effects": {
                            "weather": "misty",
                            "visibility": 0.6,
                        },
                    }
                }
            },
            "npc_data": {
                "relationships": {
                    "allies": {
                        "count": 3,
                        "trust_levels": [0.8, 0.9, 0.7],
                        "average_trust": 0.8,
                        "all_trusted": True,
                        "special_ally": None,
                        "names": ["Alice", "Bob", "Charlie"],
                        "leader_info": {"name": "Alice", "rank": "Captain"},
                    }
                }
            },
            "custom_campaign_state": {
                "progression": {
                    "chapter_data": {
                        "current_chapter": 5,
                        "completion_percentage": 67.8,
                        "all_objectives_complete": False,
                        "bonus_content": None,
                        "completed_objectives": ["find_key", "defeat_boss"],
                        "chapter_metadata": {
                            "title": "The Dark Tower",
                            "difficulty": "hard",
                        },
                    }
                }
            },
            "last_state_update_timestamp": test_datetime,
        }

        gs = GameState(**complex_data)

        # Test string values at 3rd level
        self.assertEqual(
            gs.player_character_data["personal_info"]["basic_stats"]["name"], "TestHero"
        )
        self.assertEqual(
            gs.world_data["locations"]["current_area"]["area_name"], "Enchanted Forest"
        )
        self.assertEqual(
            gs.npc_data["relationships"]["allies"]["leader_info"]["name"], "Alice"
        )
        self.assertEqual(
            gs.custom_campaign_state["progression"]["chapter_data"]["chapter_metadata"][
                "title"
            ],
            "The Dark Tower",
        )

        # Test integer values at 3rd level
        self.assertEqual(
            gs.player_character_data["personal_info"]["basic_stats"]["level"], 42
        )
        self.assertEqual(gs.npc_data["relationships"]["allies"]["count"], 3)
        self.assertEqual(
            gs.custom_campaign_state["progression"]["chapter_data"]["current_chapter"],
            5,
        )

        # Test float values at 3rd level
        self.assertEqual(
            gs.player_character_data["personal_info"]["basic_stats"][
                "experience_ratio"
            ],
            0.75,
        )
        self.assertEqual(
            gs.world_data["locations"]["current_area"]["temperature"], 22.5
        )
        self.assertEqual(gs.npc_data["relationships"]["allies"]["average_trust"], 0.8)
        self.assertEqual(
            gs.custom_campaign_state["progression"]["chapter_data"][
                "completion_percentage"
            ],
            67.8,
        )

        # Test boolean values at 3rd level
        self.assertEqual(
            gs.player_character_data["personal_info"]["basic_stats"]["is_alive"], True
        )
        self.assertEqual(gs.world_data["locations"]["current_area"]["is_safe"], False)
        self.assertEqual(gs.npc_data["relationships"]["allies"]["all_trusted"], True)
        self.assertEqual(
            gs.custom_campaign_state["progression"]["chapter_data"][
                "all_objectives_complete"
            ],
            False,
        )

        # Test None values at 3rd level
        self.assertIsNone(
            gs.player_character_data["personal_info"]["basic_stats"][
                "special_abilities"
            ]
        )
        self.assertIsNone(
            gs.world_data["locations"]["current_area"]["discovered_secrets"]
        )
        self.assertIsNone(gs.npc_data["relationships"]["allies"]["special_ally"])
        self.assertIsNone(
            gs.custom_campaign_state["progression"]["chapter_data"]["bonus_content"]
        )

        # Test list values at 3rd level
        self.assertEqual(
            gs.player_character_data["personal_info"]["basic_stats"]["inventory"],
            ["sword", "potion"],
        )
        self.assertEqual(
            gs.world_data["locations"]["current_area"]["coordinates"], [100, 250]
        )
        self.assertEqual(
            gs.npc_data["relationships"]["allies"]["trust_levels"], [0.8, 0.9, 0.7]
        )
        self.assertEqual(
            gs.custom_campaign_state["progression"]["chapter_data"][
                "completed_objectives"
            ],
            ["find_key", "defeat_boss"],
        )

        # Test nested dict values at 3rd level
        self.assertEqual(
            gs.player_character_data["personal_info"]["basic_stats"]["equipped_gear"][
                "weapon"
            ],
            "magic_sword",
        )
        self.assertEqual(
            gs.world_data["locations"]["current_area"]["environmental_effects"][
                "weather"
            ],
            "misty",
        )
        self.assertEqual(
            gs.npc_data["relationships"]["allies"]["leader_info"]["rank"], "Captain"
        )
        self.assertEqual(
            gs.custom_campaign_state["progression"]["chapter_data"]["chapter_metadata"][
                "difficulty"
            ],
            "hard",
        )

        # Test datetime
        self.assertEqual(gs.last_state_update_timestamp, test_datetime)

        # Test enum conversion

    def test_to_dict_three_layer_nesting_all_types(self):
        """Test serialization of GameState with 3 layers of nesting and all data types."""
        test_datetime = datetime.datetime(2023, 6, 15, 14, 30, 45, tzinfo=datetime.UTC)

        gs = GameState(
            player_character_data={
                "stats": {
                    "combat": {
                        "strength": 18,
                        "dexterity": 14.5,
                        "is_veteran": True,
                        "special_training": None,
                        "weapon_proficiencies": ["sword", "bow"],
                        "combat_style": {
                            "preferred": "aggressive",
                            "fallback": "defensive",
                        },
                    }
                }
            },
            last_state_update_timestamp=test_datetime,
        )

        result = gs.to_dict()

        # Verify all data types are preserved in serialization
        combat_data = result["player_character_data"]["stats"]["combat"]
        self.assertEqual(combat_data["strength"], 18)  # int
        self.assertEqual(combat_data["dexterity"], 14.5)  # float
        self.assertEqual(combat_data["is_veteran"], True)  # bool
        self.assertIsNone(combat_data["special_training"])  # None
        self.assertEqual(combat_data["weapon_proficiencies"], ["sword", "bow"])  # list
        self.assertEqual(
            combat_data["combat_style"]["preferred"], "aggressive"
        )  # nested dict

        # Verify enum is serialized as string

        # Verify datetime is preserved
        self.assertEqual(result["last_state_update_timestamp"], test_datetime)

    def test_from_dict_three_layer_nesting_all_types(self):
        """Test deserialization from dict with 3 layers of nesting and all data types."""
        test_datetime = datetime.datetime(2023, 6, 15, 14, 30, 45, tzinfo=datetime.UTC)

        source_dict = {
            "game_state_version": 2,
            "world_data": {
                "regions": {
                    "northern_kingdoms": {
                        "population": 50000,
                        "tax_rate": 0.15,
                        "is_at_war": False,
                        "ruler": None,
                        "major_cities": ["Northgate", "Frostholm"],
                        "trade_routes": {
                            "primary": "sea_route",
                            "secondary": "mountain_pass",
                        },
                    }
                }
            },
            "last_state_update_timestamp": test_datetime,
        }

        gs = GameState.from_dict(source_dict)

        # Verify all data types are correctly deserialized
        region_data = gs.world_data["regions"]["northern_kingdoms"]
        self.assertEqual(region_data["population"], 50000)  # int
        self.assertEqual(region_data["tax_rate"], 0.15)  # float
        self.assertEqual(region_data["is_at_war"], False)  # bool
        self.assertIsNone(region_data["ruler"])  # None
        self.assertEqual(
            region_data["major_cities"], ["Northgate", "Frostholm"]
        )  # list
        self.assertEqual(
            region_data["trade_routes"]["primary"], "sea_route"
        )  # nested dict

        # Verify enum conversion

        # Verify datetime preservation
        self.assertEqual(gs.last_state_update_timestamp, test_datetime)

    def test_manifest_cache_not_serialized(self):
        """Test that internal cache attributes like _manifest_cache are excluded from serialization."""
        # Create a game state
        gs = GameState()

        # Add some normal data
        gs.player_character_data = {"name": "TestHero", "level": 5}
        gs.world_data = {"current_location": "Test Town"}

        # Add an internal cache attribute (simulating what happens in gemini_service.py)
        # This should NOT be included in the serialized output
        class DummyManifest:
            """Dummy class to simulate SceneManifest objects"""

            def __init__(self):
                self.data = "This should not be serialized"

        gs._manifest_cache = {
            "manifest_key_123": DummyManifest(),
            "another_key": {"nested": DummyManifest()},
        }

        # Also test other potential internal attributes
        gs._internal_temp = "temporary data"
        gs._another_cache = [1, 2, 3]

        # Convert to dict for Firestore
        state_dict = gs.to_dict()

        # RED phase assertions - these should fail without the fix
        # Verify cache attributes are NOT in the serialized data
        self.assertNotIn(
            "_manifest_cache",
            state_dict,
            "_manifest_cache should be excluded from serialization",
        )
        self.assertNotIn(
            "_internal_temp",
            state_dict,
            "Internal attributes starting with _ should be considered for exclusion",
        )
        self.assertNotIn(
            "_another_cache", state_dict, "Internal cache attributes should be excluded"
        )

        # GREEN phase assertions - these should always pass
        # Verify normal attributes ARE in the serialized data
        self.assertIn("game_state_version", state_dict)
        self.assertIn("player_character_data", state_dict)
        self.assertIn("world_data", state_dict)
        self.assertIn("npc_data", state_dict)
        self.assertIn("custom_campaign_state", state_dict)

        # Verify the normal data is preserved correctly
        self.assertEqual(state_dict["player_character_data"]["name"], "TestHero")
        self.assertEqual(state_dict["player_character_data"]["level"], 5)
        self.assertEqual(state_dict["world_data"]["current_location"], "Test Town")


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
            "world": {"location": "Town"},
        }
        changes = {
            "player": {"level": 2, "stats": {"mp": 50}},
            "world": {"weather": "sunny"},
        }

        result = update_state_with_changes(state, changes)

        expected = {
            "player": {"name": "Hero", "level": 2, "stats": {"hp": 100, "mp": 50}},
            "world": {"location": "Town", "weather": "sunny"},
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
        expected = {
            "core_memories": ["memory1", "memory2", "new_memory1", "new_memory2"]
        }
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
            "simple_value": "old",
        }
        changes = {
            "player": {"level": 2, "gold": 100},
            "inventory": {"append": ["potion"]},
            "core_memories": ["memory1", "memory2"],  # Should deduplicate
            "simple_value": "new",
            "new_key": "new_value",
        }

        result = update_state_with_changes(state, changes)

        expected = {
            "player": {"name": "Hero", "level": 2, "gold": 100},
            "inventory": ["sword", "potion"],
            "core_memories": ["memory1", "memory2"],  # Deduplicated
            "simple_value": "new",
            "new_key": "new_value",
        }
        self.assertEqual(result, expected)

    def test_deep_nesting(self):
        """Test very deep nested dictionary merging."""
        state = {"level1": {"level2": {"level3": {"value": "old", "keep": "this"}}}}
        changes = {"level1": {"level2": {"level3": {"value": "new", "add": "this"}}}}

        result = update_state_with_changes(state, changes)

        expected = {
            "level1": {
                "level2": {"level3": {"value": "new", "keep": "this", "add": "this"}}
            }
        }
        self.assertEqual(result, expected)

    def test_three_layer_nesting_all_data_types(self):
        """Test update_state_with_changes with 3 layers of nesting and all Python data types."""
        test_datetime = datetime.datetime(2023, 6, 15, 14, 30, 45, tzinfo=datetime.UTC)

        state = {
            "game_data": {
                "player_info": {
                    "character_sheet": {
                        "name": "OldHero",
                        "level": 1,
                        "health_ratio": 1.0,
                        "is_active": True,
                        "special_items": None,
                        "skills": ["basic_attack"],
                        "attributes": {"strength": 10, "intelligence": 12},
                    }
                }
            },
            "world_state": {
                "environment": {
                    "current_location": {
                        "name": "Starting Village",
                        "danger_level": 0,
                        "weather_factor": 0.5,
                        "is_discovered": True,
                        "hidden_treasure": None,
                        "npcs": ["village_elder"],
                        "connections": {"north": "forest", "south": "plains"},
                    }
                }
            },
        }

        changes = {
            "game_data": {
                "player_info": {
                    "character_sheet": {
                        "name": "UpdatedHero",  # string update
                        "level": 5,  # int update
                        "health_ratio": 0.8,  # float update
                        "is_active": False,  # bool update
                        "special_items": ["magic_ring"],  # None -> list
                        "skills": {"append": ["fireball", "heal"]},  # append to list
                        "attributes": {
                            "strength": 15,  # nested int update
                            "wisdom": 14,  # new nested int
                        },
                    }
                }
            },
            "world_state": {
                "environment": {
                    "current_location": {
                        "danger_level": 2,  # int update
                        "weather_factor": 0.3,  # float update
                        "is_discovered": False,  # bool update (should not happen in practice)
                        "hidden_treasure": "gold_coins",  # None -> string
                        "npcs": {"append": ["merchant", "guard"]},  # append to list
                        "connections": {
                            "east": "mountain",  # new nested string
                            "west": None,  # new nested None
                        },
                    }
                }
            },
            "metadata": {  # completely new top-level
                "session_info": {
                    "start_time": test_datetime,
                    "session_id": 12345,
                    "is_tutorial": False,
                    "notes": None,
                    "participants": ["player1"],
                    "settings": {"difficulty": "normal", "auto_save": True},
                }
            },
        }

        result = update_state_with_changes(state, changes)

        # Test string updates at 3rd level
        self.assertEqual(
            result["game_data"]["player_info"]["character_sheet"]["name"], "UpdatedHero"
        )
        self.assertEqual(
            result["world_state"]["environment"]["current_location"]["name"],
            "Starting Village",
        )  # unchanged
        self.assertEqual(
            result["metadata"]["session_info"]["settings"]["difficulty"], "normal"
        )  # new

        # Test int updates at 3rd level
        self.assertEqual(
            result["game_data"]["player_info"]["character_sheet"]["level"], 5
        )
        self.assertEqual(
            result["world_state"]["environment"]["current_location"]["danger_level"], 2
        )
        self.assertEqual(result["metadata"]["session_info"]["session_id"], 12345)  # new

        # Test float updates at 3rd level
        self.assertEqual(
            result["game_data"]["player_info"]["character_sheet"]["health_ratio"], 0.8
        )
        self.assertEqual(
            result["world_state"]["environment"]["current_location"]["weather_factor"],
            0.3,
        )

        # Test bool updates at 3rd level
        self.assertEqual(
            result["game_data"]["player_info"]["character_sheet"]["is_active"], False
        )
        self.assertEqual(
            result["world_state"]["environment"]["current_location"]["is_discovered"],
            False,
        )
        self.assertEqual(
            result["metadata"]["session_info"]["is_tutorial"], False
        )  # new

        # Test None updates at 3rd level
        self.assertEqual(
            result["game_data"]["player_info"]["character_sheet"]["special_items"],
            ["magic_ring"],
        )  # None -> list
        self.assertEqual(
            result["world_state"]["environment"]["current_location"]["hidden_treasure"],
            "gold_coins",
        )  # None -> string
        self.assertIsNone(result["metadata"]["session_info"]["notes"])  # new None
        self.assertIsNone(
            result["world_state"]["environment"]["current_location"]["connections"][
                "west"
            ]
        )  # new nested None

        # Test list updates at 3rd level (append operations)
        self.assertEqual(
            result["game_data"]["player_info"]["character_sheet"]["skills"],
            ["basic_attack", "fireball", "heal"],
        )
        self.assertEqual(
            result["world_state"]["environment"]["current_location"]["npcs"],
            ["village_elder", "merchant", "guard"],
        )
        self.assertEqual(
            result["metadata"]["session_info"]["participants"], ["player1"]
        )  # new

        # Test nested dict updates at 3rd level
        self.assertEqual(
            result["game_data"]["player_info"]["character_sheet"]["attributes"][
                "strength"
            ],
            15,
        )  # updated
        self.assertEqual(
            result["game_data"]["player_info"]["character_sheet"]["attributes"][
                "intelligence"
            ],
            12,
        )  # preserved
        self.assertEqual(
            result["game_data"]["player_info"]["character_sheet"]["attributes"][
                "wisdom"
            ],
            14,
        )  # new
        self.assertEqual(
            result["world_state"]["environment"]["current_location"]["connections"][
                "north"
            ],
            "forest",
        )  # preserved
        self.assertEqual(
            result["world_state"]["environment"]["current_location"]["connections"][
                "east"
            ],
            "mountain",
        )  # new
        self.assertEqual(
            result["metadata"]["session_info"]["settings"]["auto_save"], True
        )  # new nested

        # Test datetime at 3rd level
        self.assertEqual(
            result["metadata"]["session_info"]["start_time"], test_datetime
        )

    def test_three_layer_nesting_edge_cases(self):
        """Test edge cases with 3-layer nesting including empty structures and type conflicts."""
        state = {
            "container1": {
                "container2": {
                    "container3": {
                        "empty_list": [],
                        "empty_dict": {},
                        "zero_int": 0,
                        "zero_float": 0.0,
                        "false_bool": False,
                        "empty_string": "",
                    }
                }
            }
        }

        changes = {
            "container1": {
                "container2": {
                    "container3": {
                        "empty_list": {
                            "append": ["first_item"]
                        },  # append to empty list
                        "empty_dict": {"new_key": "new_value"},  # add to empty dict
                        "zero_int": 42,  # update zero
                        "zero_float": 3.14,  # update zero
                        "false_bool": True,  # update false
                        "empty_string": "now_has_content",  # update empty string
                        "completely_new": "brand_new_value",  # add new key
                    }
                }
            }
        }

        result = update_state_with_changes(state, changes)

        # Test updates to "falsy" values
        self.assertEqual(
            result["container1"]["container2"]["container3"]["empty_list"],
            ["first_item"],
        )
        self.assertEqual(
            result["container1"]["container2"]["container3"]["empty_dict"],
            {"new_key": "new_value"},
        )
        self.assertEqual(
            result["container1"]["container2"]["container3"]["zero_int"], 42
        )
        self.assertEqual(
            result["container1"]["container2"]["container3"]["zero_float"], 3.14
        )
        self.assertEqual(
            result["container1"]["container2"]["container3"]["false_bool"], True
        )
        self.assertEqual(
            result["container1"]["container2"]["container3"]["empty_string"],
            "now_has_content",
        )
        self.assertEqual(
            result["container1"]["container2"]["container3"]["completely_new"],
            "brand_new_value",
        )


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

    def test_append_all_data_types(self):
        """Test appending various data types to a list."""
        target_list = ["string"]
        test_datetime = datetime.datetime(2023, 1, 1, tzinfo=datetime.UTC)

        items_to_append = [
            42,  # int
            3.14,  # float
            True,  # bool
            None,  # None
            ["nested", "list"],  # list
            {"nested": "dict"},  # dict
            test_datetime,  # datetime
        ]

        _perform_append(target_list, items_to_append, "test_key")

        expected = [
            "string",
            42,
            3.14,
            True,
            None,
            ["nested", "list"],
            {"nested": "dict"},
            test_datetime,
        ]

        self.assertEqual(target_list, expected)


class TestGameStateValidation(unittest.TestCase):
    """Test cases for the GameState validation methods."""

    def test_validate_checkpoint_consistency_hp_mismatch_fails_without_implementation(
        self,
    ):
        """RED TEST: This should fail without the validate_checkpoint_consistency implementation."""
        # Create a game state with HP data
        gs = GameState(player_character_data={"hp_current": 25, "hp_max": 100})

        # Narrative that contradicts the HP state
        narrative = (
            "The hero lies unconscious on the ground, completely drained of life force."
        )

        # This should detect the discrepancy between narrative (unconscious) and state (25 HP)
        discrepancies = gs.validate_checkpoint_consistency(narrative)

        # We expect to find at least one discrepancy
        self.assertGreater(
            len(discrepancies), 0, "Should detect HP/consciousness discrepancy"
        )
        self.assertTrue(
            any(
                "unconscious" in d.lower() and "hp" in d.lower() for d in discrepancies
            ),
            "Should specifically mention unconscious/HP mismatch",
        )

    def test_validate_checkpoint_consistency_location_mismatch_fails_without_implementation(
        self,
    ):
        """RED TEST: This should fail without the validate_checkpoint_consistency implementation."""
        # Create a game state with location data
        gs = GameState(world_data={"current_location_name": "Tavern"})

        # Narrative that contradicts the location
        narrative = (
            "Standing in the middle of the dark forest, surrounded by ancient trees."
        )

        # This should detect the location discrepancy
        discrepancies = gs.validate_checkpoint_consistency(narrative)

        # We expect to find at least one discrepancy
        self.assertGreater(len(discrepancies), 0, "Should detect location discrepancy")
        self.assertTrue(
            any("location" in d.lower() for d in discrepancies),
            "Should specifically mention location mismatch",
        )

    def test_validate_checkpoint_consistency_mission_completion_fails_without_implementation(
        self,
    ):
        """RED TEST: This should fail without the validate_checkpoint_consistency implementation."""
        # Create a game state with active missions
        gs = GameState(
            custom_campaign_state={
                "active_missions": ["Find the lost treasure", "Defeat the dragon"]
            }
        )

        # Narrative that indicates mission completion
        narrative = "With the dragon finally defeated and the treasure secured, the quest was complete."

        # This should detect that missions are still marked active despite completion
        discrepancies = gs.validate_checkpoint_consistency(narrative)

        # We expect to find at least one discrepancy
        self.assertGreater(
            len(discrepancies), 0, "Should detect completed mission still marked active"
        )
        self.assertTrue(
            any("mission" in d.lower() or "quest" in d.lower() for d in discrepancies),
            "Should specifically mention mission/quest discrepancy",
        )


class TestMainStateFunctions(unittest.TestCase):
    """Test cases for state-related functions in main.py."""

    def test_cleanup_legacy_state_with_dot_keys(self):
        """Test cleanup of legacy keys with dots."""
        state_dict = {
            "player.name": "Hero",
            "player.level": 5,
            "normal_key": "value",
            "world.location": "Forest",
        }

        cleaned, was_changed, num_deleted = main._cleanup_legacy_state(state_dict)

        expected_cleaned = {"normal_key": "value"}
        self.assertEqual(cleaned, expected_cleaned)
        self.assertTrue(was_changed)
        self.assertEqual(num_deleted, 3)

    def test_cleanup_legacy_state_with_world_time(self):
        """Test cleanup of legacy world_time key."""
        state_dict = {"world_time": "12:00", "normal_key": "value"}

        cleaned, was_changed, num_deleted = main._cleanup_legacy_state(state_dict)

        expected_cleaned = {"normal_key": "value"}
        self.assertEqual(cleaned, expected_cleaned)
        self.assertTrue(was_changed)
        self.assertEqual(num_deleted, 1)

    def test_cleanup_legacy_state_no_changes(self):
        """Test cleanup when no legacy keys are present."""
        state_dict = {"normal_key1": "value1", "normal_key2": "value2"}

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
        self.assertIn('player_name: "Hero"', result)
        self.assertIn("level: 5", result)

    def test_format_state_changes_nested(self):
        """Test formatting nested state changes."""
        changes = {
            "player": {"name": "Hero", "stats": {"hp": 100}},
            "world": {"location": "Forest"},
        }

        result = main.format_state_changes(changes, for_html=False)

        self.assertIn("Game state updated (3 entries):", result)
        self.assertIn('player.name: "Hero"', result)
        self.assertIn("player.stats.hp: 100", result)
        self.assertIn('world.location: "Forest"', result)

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
        payload = 'key1 = "value1"\nkey2 = 42'

        result = main.parse_set_command(payload)

        expected = {"key1": "value1", "key2": 42}
        self.assertEqual(result, expected)

    def test_parse_set_command_nested(self):
        """Test parsing nested dot notation."""
        payload = 'player.name = "Hero"\nplayer.level = 5\nworld.location = "Forest"'

        result = main.parse_set_command(payload)

        expected = {
            "player": {"name": "Hero", "level": 5},
            "world": {"location": "Forest"},
        }
        self.assertEqual(result, expected)

    def test_parse_set_command_append(self):
        """Test parsing append operations."""
        payload = 'items.append = "sword"\nitems.append = "shield"'

        result = main.parse_set_command(payload)

        expected = {"items": {"append": ["sword", "shield"]}}
        self.assertEqual(result, expected)

    def test_parse_set_command_invalid_json(self):
        """Test parsing with invalid JSON values."""
        payload = 'valid_key = "valid_value"\ninvalid_key = invalid_json'

        result = main.parse_set_command(payload)

        # Should skip invalid line
        expected = {"valid_key": "valid_value"}
        self.assertEqual(result, expected)

    def test_parse_set_command_empty_lines(self):
        """Test parsing with empty lines and no equals signs."""
        payload = 'key1 = "value1"\n\nkey2 = "value2"\nno_equals_sign\n'

        result = main.parse_set_command(payload)

        expected = {"key1": "value1", "key2": "value2"}
        self.assertEqual(result, expected)

    def test_parse_set_command_three_layer_nesting_all_types(self):
        """Test parsing set commands with 3 layers of nesting and all data types."""
        test_datetime_str = "2023-06-15T14:30:45+00:00"

        payload = f'''
        player.stats.combat.strength = 18
        player.stats.combat.dexterity = 14.5
        player.stats.combat.is_veteran = true
        player.stats.combat.special_training = null
        player.stats.combat.weapon_proficiencies.append = "sword"
        player.stats.combat.weapon_proficiencies.append = "bow"
        world.regions.north.population = 50000
        world.regions.north.tax_rate = 0.15
        world.regions.north.is_at_war = false
        world.regions.north.ruler = null
        world.regions.north.major_cities.append = "Northgate"
        world.regions.north.major_cities.append = "Frostholm"
        metadata.session.start_time = "{test_datetime_str}"
        metadata.session.session_id = 12345
        metadata.session.is_tutorial = false
        metadata.session.notes = null
        metadata.session.participants.append = "player1"
        metadata.session.participants.append = "player2"
        '''

        result = main.parse_set_command(payload)

        # Test int values at 3rd level
        self.assertEqual(result["player"]["stats"]["combat"]["strength"], 18)
        self.assertEqual(result["world"]["regions"]["north"]["population"], 50000)
        self.assertEqual(result["metadata"]["session"]["session_id"], 12345)

        # Test float values at 3rd level
        self.assertEqual(result["player"]["stats"]["combat"]["dexterity"], 14.5)
        self.assertEqual(result["world"]["regions"]["north"]["tax_rate"], 0.15)

        # Test bool values at 3rd level
        self.assertEqual(result["player"]["stats"]["combat"]["is_veteran"], True)
        self.assertEqual(result["world"]["regions"]["north"]["is_at_war"], False)
        self.assertEqual(result["metadata"]["session"]["is_tutorial"], False)

        # Test None values at 3rd level
        self.assertIsNone(result["player"]["stats"]["combat"]["special_training"])
        self.assertIsNone(result["world"]["regions"]["north"]["ruler"])
        self.assertIsNone(result["metadata"]["session"]["notes"])

        # Test string values at 3rd level
        self.assertEqual(result["metadata"]["session"]["start_time"], test_datetime_str)

        # Test append operations at 3rd level
        self.assertEqual(
            result["player"]["stats"]["combat"]["weapon_proficiencies"]["append"],
            ["sword", "bow"],
        )
        self.assertEqual(
            result["world"]["regions"]["north"]["major_cities"]["append"],
            ["Northgate", "Frostholm"],
        )
        self.assertEqual(
            result["metadata"]["session"]["participants"]["append"],
            ["player1", "player2"],
        )


if __name__ == "__main__":
    unittest.main()
