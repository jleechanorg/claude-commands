"""
Unit tests for game_state.py module.
Tests the GameState class and related functions.
Comprehensive mocking implemented to handle CI environments that lack Firebase dependencies.
"""

import datetime
import os
import sys
import unittest
from importlib import import_module
from unittest.mock import MagicMock, patch

# Set test environment before any imports
os.environ["TESTING"] = "true"
os.environ["USE_MOCKS"] = "true"
os.environ["GEMINI_API_KEY"] = "test-api-key"

# CRITICAL FIX: Mock firebase_admin completely to avoid google.auth namespace conflicts
# This prevents the test from trying to import firebase_admin which triggers the google.auth issue
firebase_admin_mock = MagicMock()
firebase_admin_mock.firestore = MagicMock()
firebase_admin_mock.auth = MagicMock()
firebase_admin_mock._apps = {}  # Empty apps list to prevent initialization
sys.modules["firebase_admin"] = firebase_admin_mock
sys.modules["firebase_admin.firestore"] = firebase_admin_mock.firestore
sys.modules["firebase_admin.auth"] = firebase_admin_mock.auth

# Use proper fakes library instead of manual MagicMock setup
# Import fakes library components (will be imported after path setup)
try:
    # Fakes library will be imported after path setup below

    # Mock pydantic dependencies
    pydantic_module = MagicMock()
    pydantic_module.BaseModel = MagicMock()
    pydantic_module.Field = MagicMock()
    pydantic_module.field_validator = MagicMock()
    pydantic_module.model_validator = MagicMock()
    pydantic_module.ValidationError = (
        Exception  # Use regular Exception for ValidationError
    )
    sys.modules["pydantic"] = pydantic_module

    # Mock cachetools dependencies
    cachetools_module = MagicMock()
    cachetools_module.TTLCache = MagicMock()
    cachetools_module.cached = MagicMock()
    sys.modules["cachetools"] = cachetools_module

    # Mock google dependencies
    google_module = MagicMock()
    google_module.genai = MagicMock()
    google_module.genai.Client = MagicMock()
    sys.modules["google"] = google_module
    sys.modules["google.genai"] = google_module.genai

    # Mock other optional dependencies that might not be available
    docx_module = MagicMock()
    docx_module.Document = MagicMock()
    sys.modules["docx"] = docx_module

    # Mock fpdf dependencies
    fpdf_module = MagicMock()
    fpdf_module.FPDF = MagicMock()
    fpdf_module.XPos = MagicMock()
    fpdf_module.YPos = MagicMock()
    sys.modules["fpdf"] = fpdf_module
except Exception:
    pass  # If mocking fails, continue anyway

# Add parent directory to path AFTER mocking firebase_admin (append instead of insert to avoid shadowing google package)
mvp_site_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if mvp_site_path not in sys.path:
    sys.path.append(mvp_site_path)

# Import proper fakes library

firestore_service_module = import_module("mvp_site.firestore_service")
_perform_append = firestore_service_module._perform_append
update_state_with_changes = firestore_service_module.update_state_with_changes

game_state_module = import_module("mvp_site.game_state")
GameState = game_state_module.GameState

world_logic_module = import_module("mvp_site.world_logic")
KEY_RESPONSE = world_logic_module.KEY_RESPONSE
KEY_SUCCESS = world_logic_module.KEY_SUCCESS
_cleanup_legacy_state = world_logic_module._cleanup_legacy_state
_handle_debug_mode_command = world_logic_module._handle_debug_mode_command
format_game_state_updates = world_logic_module.format_game_state_updates
parse_set_command = world_logic_module.parse_set_command


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
        assert isinstance(discrepancies, list)

    def test_debug_mode_default_true(self):
        """Test that debug_mode defaults to True per updated DEFAULT_DEBUG_MODE."""
        gs = GameState()
        assert gs.debug_mode

        # Also test it's included in serialization
        data = gs.to_dict()
        assert "debug_mode" in data
        assert data["debug_mode"]

    def test_debug_mode_can_be_set_false(self):
        """Test that debug_mode can be explicitly set to False."""
        gs = GameState(debug_mode=False)
        assert not gs.debug_mode

        # Test serialization
        data = gs.to_dict()
        assert "debug_mode" in data
        assert not data["debug_mode"]

    def test_debug_mode_from_dict(self):
        """Test that debug_mode is properly loaded from dict."""
        # Test loading True
        data = {"debug_mode": True}
        gs = GameState.from_dict(data)
        assert gs.debug_mode

        # Test loading False
        data = {"debug_mode": False}
        gs = GameState.from_dict(data)
        assert not gs.debug_mode

        # Test missing debug_mode defaults to True
        data = {"game_state_version": 1}
        gs = GameState.from_dict(data)
        assert gs.debug_mode

    def test_default_initialization(self):
        """Test GameState initialization with default values."""
        gs = GameState()

        # Test default values
        assert gs.game_state_version == 1
        assert gs.player_character_data == {}
        assert gs.world_data == {}
        assert gs.npc_data == {}
        assert gs.custom_campaign_state == {"attribute_system": "D&D"}

        # Test that timestamp is recent
        now = datetime.datetime.now(datetime.UTC)
        time_diff = abs((now - gs.last_state_update_timestamp).total_seconds())
        assert time_diff < 5, "Timestamp should be within 5 seconds of now"

        # Test debug_mode defaults to True (updated DEFAULT_DEBUG_MODE)
        assert gs.debug_mode, "debug_mode should default to True"

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

        assert gs.game_state_version == 2
        assert gs.player_character_data == {"name": "Hero", "level": 5}
        assert gs.world_data == {"location": "Forest"}
        assert gs.npc_data == {"npc1": {"name": "Villager"}}
        assert gs.custom_campaign_state == {
            "quest_active": True,
            "attribute_system": "D&D",
        }
        assert gs.last_state_update_timestamp == custom_time
        assert gs.extra_field == "extra_value"

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
            "debug_mode": True,  # Should default to True per updated DEFAULT_DEBUG_MODE
        }

        assert result == expected

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

        assert gs.game_state_version == 2
        assert gs.player_character_data == {"name": "Hero"}
        assert gs.last_state_update_timestamp == custom_time
        assert gs.custom_field == "custom_value"

    def test_from_dict_with_none(self):
        """Test from_dict returns None when source is None."""
        result = GameState.from_dict(None)
        assert result is None

    def test_from_dict_with_empty_dict(self):
        """Test from_dict returns None when source is empty dict."""
        result = GameState.from_dict({})
        assert result is None

    def test_dynamic_attribute_setting(self):
        """Test that dynamic attributes are set correctly."""
        gs = GameState(
            custom_attr1="value1", custom_attr2=42, custom_attr3=["list", "value"]
        )

        assert gs.custom_attr1 == "value1"
        assert gs.custom_attr2 == 42
        assert gs.custom_attr3 == ["list", "value"]

    def test_attribute_precedence(self):
        """Test that existing attributes are not overwritten by dynamic setting."""
        gs = GameState(game_state_version=5)

        # The constructor should have already set game_state_version
        # Dynamic attribute setting should not create a duplicate
        assert gs.game_state_version == 5
        assert not hasattr(gs, "game_state_version_duplicate")

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
        assert (
            gs.player_character_data["personal_info"]["basic_stats"]["name"]
            == "TestHero"
        )
        assert (
            gs.world_data["locations"]["current_area"]["area_name"]
            == "Enchanted Forest"
        )
        assert gs.npc_data["relationships"]["allies"]["leader_info"]["name"] == "Alice"
        assert (
            gs.custom_campaign_state["progression"]["chapter_data"]["chapter_metadata"][
                "title"
            ]
            == "The Dark Tower"
        )

        # Test integer values at 3rd level
        assert gs.player_character_data["personal_info"]["basic_stats"]["level"] == 42
        assert gs.npc_data["relationships"]["allies"]["count"] == 3
        assert (
            gs.custom_campaign_state["progression"]["chapter_data"]["current_chapter"]
            == 5
        )

        # Test float values at 3rd level
        assert (
            gs.player_character_data["personal_info"]["basic_stats"]["experience_ratio"]
            == 0.75
        )
        assert gs.world_data["locations"]["current_area"]["temperature"] == 22.5
        assert gs.npc_data["relationships"]["allies"]["average_trust"] == 0.8
        assert (
            gs.custom_campaign_state["progression"]["chapter_data"][
                "completion_percentage"
            ]
            == 67.8
        )

        # Test boolean values at 3rd level
        assert gs.player_character_data["personal_info"]["basic_stats"]["is_alive"]
        assert not gs.world_data["locations"]["current_area"]["is_safe"]
        assert gs.npc_data["relationships"]["allies"]["all_trusted"]
        assert not (
            gs.custom_campaign_state["progression"]["chapter_data"][
                "all_objectives_complete"
            ]
        )

        # Test None values at 3rd level
        assert (
            gs.player_character_data["personal_info"]["basic_stats"][
                "special_abilities"
            ]
            is None
        )
        assert gs.world_data["locations"]["current_area"]["discovered_secrets"] is None
        assert gs.npc_data["relationships"]["allies"]["special_ally"] is None
        assert (
            gs.custom_campaign_state["progression"]["chapter_data"]["bonus_content"]
            is None
        )

        # Test list values at 3rd level
        assert gs.player_character_data["personal_info"]["basic_stats"][
            "inventory"
        ] == ["sword", "potion"]
        assert gs.world_data["locations"]["current_area"]["coordinates"] == [100, 250]
        assert gs.npc_data["relationships"]["allies"]["trust_levels"] == [0.8, 0.9, 0.7]
        assert gs.custom_campaign_state["progression"]["chapter_data"][
            "completed_objectives"
        ] == ["find_key", "defeat_boss"]

        # Test nested dict values at 3rd level
        assert (
            gs.player_character_data["personal_info"]["basic_stats"]["equipped_gear"][
                "weapon"
            ]
            == "magic_sword"
        )
        assert (
            gs.world_data["locations"]["current_area"]["environmental_effects"][
                "weather"
            ]
            == "misty"
        )
        assert (
            gs.npc_data["relationships"]["allies"]["leader_info"]["rank"] == "Captain"
        )
        assert (
            gs.custom_campaign_state["progression"]["chapter_data"]["chapter_metadata"][
                "difficulty"
            ]
            == "hard"
        )

        # Test datetime
        assert gs.last_state_update_timestamp == test_datetime

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
        assert combat_data["strength"] == 18  # int
        assert combat_data["dexterity"] == 14.5  # float
        assert combat_data["is_veteran"]  # bool
        assert combat_data["special_training"] is None  # None
        assert combat_data["weapon_proficiencies"] == ["sword", "bow"]  # list
        assert combat_data["combat_style"]["preferred"] == "aggressive"  # nested dict

        # Verify enum is serialized as string

        # Verify datetime is preserved
        assert result["last_state_update_timestamp"] == test_datetime

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
        assert region_data["population"] == 50000  # int
        assert region_data["tax_rate"] == 0.15  # float
        assert not region_data["is_at_war"]  # bool
        assert region_data["ruler"] is None  # None
        assert region_data["major_cities"] == ["Northgate", "Frostholm"]  # list
        assert region_data["trade_routes"]["primary"] == "sea_route"  # nested dict

        # Verify enum conversion

        # Verify datetime preservation
        assert gs.last_state_update_timestamp == test_datetime

    def test_manifest_cache_not_serialized(self):
        """Test that internal cache attributes like _manifest_cache are excluded from serialization."""
        # Create a game state
        gs = GameState()

        # Add some normal data
        gs.player_character_data = {"name": "TestHero", "level": 5}
        gs.world_data = {"current_location": "Test Town"}

        # Add an internal cache attribute (simulating what happens in llm_service.py)
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
        assert (
            "_manifest_cache" not in state_dict
        ), "_manifest_cache should be excluded from serialization"
        assert (
            "_internal_temp" not in state_dict
        ), "Internal attributes starting with _ should be considered for exclusion"
        assert (
            "_another_cache" not in state_dict
        ), "Internal cache attributes should be excluded"

        # GREEN phase assertions - these should always pass
        # Verify normal attributes ARE in the serialized data
        assert "game_state_version" in state_dict
        assert "player_character_data" in state_dict
        assert "world_data" in state_dict
        assert "npc_data" in state_dict
        assert "custom_campaign_state" in state_dict

        # Verify the normal data is preserved correctly
        assert state_dict["player_character_data"]["name"] == "TestHero"
        assert state_dict["player_character_data"]["level"] == 5
        assert state_dict["world_data"]["current_location"] == "Test Town"


class TestUpdateStateWithChanges(unittest.TestCase):
    """Test cases for the update_state_with_changes function."""

    def test_simple_overwrite(self):
        """Test simple value overwriting."""
        state = {"key1": "old_value", "key2": 42}
        changes = {"key1": "new_value", "key3": "added_value"}

        result = update_state_with_changes(state, changes)

        expected = {"key1": "new_value", "key2": 42, "key3": "added_value"}
        assert result == expected

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
        assert result == expected

    def test_explicit_append_syntax(self):
        """Test explicit append using {'append': ...} syntax."""
        state = {"items": ["sword", "shield"]}
        changes = {"items": {"append": ["potion", "key"]}}

        result = update_state_with_changes(state, changes)

        expected = {"items": ["sword", "shield", "potion", "key"]}
        assert result == expected

    def test_explicit_append_to_nonexistent_key(self):
        """Test append to a key that doesn't exist yet."""
        state = {"other_key": "value"}
        changes = {"new_list": {"append": ["item1", "item2"]}}

        result = update_state_with_changes(state, changes)

        expected = {"other_key": "value", "new_list": ["item1", "item2"]}
        assert result == expected

    def test_explicit_append_to_non_list(self):
        """Test append to a key that exists but isn't a list."""
        state = {"key": "not_a_list"}
        changes = {"key": {"append": ["item1"]}}

        result = update_state_with_changes(state, changes)

        expected = {"key": ["item1"]}
        assert result == expected

    def test_core_memories_safeguard(self):
        """Test that core_memories is protected from direct overwrite."""
        state = {"core_memories": ["memory1", "memory2"]}
        changes = {"core_memories": ["new_memory1", "new_memory2"]}

        result = update_state_with_changes(state, changes)

        # Should append, not overwrite
        expected = {
            "core_memories": ["memory1", "memory2", "new_memory1", "new_memory2"]
        }
        assert result == expected

    def test_core_memories_deduplication(self):
        """Test that core_memories deduplicates when appending."""
        state = {"core_memories": ["memory1", "memory2"]}
        changes = {"core_memories": ["memory2", "memory3"]}  # memory2 is duplicate

        result = update_state_with_changes(state, changes)

        # Should deduplicate memory2
        expected = {"core_memories": ["memory1", "memory2", "memory3"]}
        assert result == expected

    def test_core_memories_to_nonexistent_key(self):
        """Test core_memories safeguard when key doesn't exist."""
        state = {"other_key": "value"}
        changes = {"core_memories": ["memory1", "memory2"]}

        result = update_state_with_changes(state, changes)

        expected = {"other_key": "value", "core_memories": ["memory1", "memory2"]}
        assert result == expected

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
        assert result == expected

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
        assert result == expected

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
        assert (
            result["game_data"]["player_info"]["character_sheet"]["name"]
            == "UpdatedHero"
        )
        assert (
            result["world_state"]["environment"]["current_location"]["name"]
            == "Starting Village"
        )  # unchanged
        assert (
            result["metadata"]["session_info"]["settings"]["difficulty"] == "normal"
        )  # new

        # Test int updates at 3rd level
        assert result["game_data"]["player_info"]["character_sheet"]["level"] == 5
        assert (
            result["world_state"]["environment"]["current_location"]["danger_level"]
            == 2
        )
        assert result["metadata"]["session_info"]["session_id"] == 12345  # new

        # Test float updates at 3rd level
        assert (
            result["game_data"]["player_info"]["character_sheet"]["health_ratio"] == 0.8
        )
        assert (
            result["world_state"]["environment"]["current_location"]["weather_factor"]
            == 0.3
        )

        # Test bool updates at 3rd level
        assert not (result["game_data"]["player_info"]["character_sheet"]["is_active"])
        assert not (
            result["world_state"]["environment"]["current_location"]["is_discovered"]
        )
        assert not result["metadata"]["session_info"]["is_tutorial"]  # new

        # Test None updates at 3rd level
        assert result["game_data"]["player_info"]["character_sheet"][
            "special_items"
        ] == ["magic_ring"]  # None -> list
        assert (
            result["world_state"]["environment"]["current_location"]["hidden_treasure"]
            == "gold_coins"
        )  # None -> string
        assert result["metadata"]["session_info"]["notes"] is None  # new None
        assert (
            result["world_state"]["environment"]["current_location"]["connections"][
                "west"
            ]
            is None
        )  # new nested None

        # Test list updates at 3rd level (append operations)
        assert result["game_data"]["player_info"]["character_sheet"]["skills"] == [
            "basic_attack",
            "fireball",
            "heal",
        ]
        assert result["world_state"]["environment"]["current_location"]["npcs"] == [
            "village_elder",
            "merchant",
            "guard",
        ]
        assert result["metadata"]["session_info"]["participants"] == ["player1"]  # new

        # Test nested dict updates at 3rd level
        assert (
            result["game_data"]["player_info"]["character_sheet"]["attributes"][
                "strength"
            ]
            == 15
        )  # updated
        assert (
            result["game_data"]["player_info"]["character_sheet"]["attributes"][
                "intelligence"
            ]
            == 12
        )  # preserved
        assert (
            result["game_data"]["player_info"]["character_sheet"]["attributes"][
                "wisdom"
            ]
            == 14
        )  # new
        assert (
            result["world_state"]["environment"]["current_location"]["connections"][
                "north"
            ]
            == "forest"
        )  # preserved
        assert (
            result["world_state"]["environment"]["current_location"]["connections"][
                "east"
            ]
            == "mountain"
        )  # new
        assert result["metadata"]["session_info"]["settings"]["auto_save"]  # new nested

        # Test datetime at 3rd level
        assert result["metadata"]["session_info"]["start_time"] == test_datetime

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
        assert result["container1"]["container2"]["container3"]["empty_list"] == [
            "first_item"
        ]
        assert result["container1"]["container2"]["container3"]["empty_dict"] == {
            "new_key": "new_value"
        }
        assert result["container1"]["container2"]["container3"]["zero_int"] == 42
        assert result["container1"]["container2"]["container3"]["zero_float"] == 3.14
        assert result["container1"]["container2"]["container3"]["false_bool"]
        assert (
            result["container1"]["container2"]["container3"]["empty_string"]
            == "now_has_content"
        )
        assert (
            result["container1"]["container2"]["container3"]["completely_new"]
            == "brand_new_value"
        )


class TestPerformAppend(unittest.TestCase):
    """Test cases for the _perform_append helper function."""

    def test_append_single_item(self):
        """Test appending a single item."""
        target_list = ["item1", "item2"]
        _perform_append(target_list, "item3", "test_key")

        assert target_list == ["item1", "item2", "item3"]

    def test_append_multiple_items(self):
        """Test appending multiple items."""
        target_list = ["item1"]
        _perform_append(target_list, ["item2", "item3"], "test_key")

        assert target_list == ["item1", "item2", "item3"]

    def test_append_with_deduplication(self):
        """Test appending with deduplication enabled."""
        target_list = ["item1", "item2"]
        _perform_append(target_list, ["item2", "item3"], "test_key", deduplicate=True)

        assert target_list == ["item1", "item2", "item3"]

    def test_append_without_deduplication(self):
        """Test appending without deduplication (default)."""
        target_list = ["item1", "item2"]
        _perform_append(target_list, ["item2", "item3"], "test_key", deduplicate=False)

        assert target_list == ["item1", "item2", "item2", "item3"]

    def test_append_all_duplicates(self):
        """Test appending when all items are duplicates."""
        target_list = ["item1", "item2"]
        _perform_append(target_list, ["item1", "item2"], "test_key", deduplicate=True)

        # Should remain unchanged
        assert target_list == ["item1", "item2"]

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

        assert target_list == expected


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
        assert len(discrepancies) > 0, "Should detect HP/consciousness discrepancy"
        assert any(
            "unconscious" in d.lower() and "hp" in d.lower() for d in discrepancies
        ), "Should specifically mention unconscious/HP mismatch"

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
        assert len(discrepancies) > 0, "Should detect location discrepancy"
        assert any(
            "location" in d.lower() for d in discrepancies
        ), "Should specifically mention location mismatch"

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
        assert (
            len(discrepancies) > 0
        ), "Should detect completed mission still marked active"
        assert any(
            "mission" in d.lower() or "quest" in d.lower() for d in discrepancies
        ), "Should specifically mention mission/quest discrepancy"


class TestMainStateFunctions(unittest.TestCase):
    """Test cases for state-related functions in main.py."""

    def test_cleanup_legacy_state_with_dot_keys(self):
        """Test cleanup of legacy keys with dots."""
        state_dict = {
            "player.name": "Hero",
            "player.level": 5,
            "normal_key": "value",
            "world.location": "Forest",
            "party_data": "legacy",  # Actual legacy field
        }

        cleaned, was_changed, num_deleted = _cleanup_legacy_state(state_dict)

        # MCP architecture: only removes specific legacy fields, not dot keys
        expected_cleaned = {
            "player.name": "Hero",
            "player.level": 5,
            "normal_key": "value",
            "world.location": "Forest",
        }
        assert cleaned == expected_cleaned
        assert was_changed
        assert num_deleted == 1

    def test_cleanup_legacy_state_with_world_time(self):
        """Test cleanup of legacy world_time key."""
        state_dict = {
            "world_time": "12:00",
            "normal_key": "value",
            "legacy_prompt_data": "old",
        }

        cleaned, was_changed, num_deleted = _cleanup_legacy_state(state_dict)

        # MCP architecture: world_time is not considered legacy, only specific fields
        expected_cleaned = {"world_time": "12:00", "normal_key": "value"}
        assert cleaned == expected_cleaned
        assert was_changed
        assert num_deleted == 1

    def test_cleanup_legacy_state_no_changes(self):
        """Test cleanup when no legacy keys are present."""
        state_dict = {"normal_key1": "value1", "normal_key2": "value2"}

        cleaned, was_changed, num_deleted = _cleanup_legacy_state(state_dict)

        assert cleaned == state_dict
        assert not was_changed
        assert num_deleted == 0

    def test_cleanup_legacy_state_empty_dict(self):
        """Test cleanup with empty dictionary."""
        state_dict = {}

        cleaned, was_changed, num_deleted = _cleanup_legacy_state(state_dict)

        assert cleaned == {}
        assert not was_changed
        assert num_deleted == 0

    def test_format_game_state_updates_simple(self):
        """Test formatting simple state changes."""
        changes = {"player_name": "Hero", "level": 5}

        result = format_game_state_updates(changes, for_html=False)

        assert "Game state updated (2 entries):" in result
        assert 'player_name: "Hero"' in result
        assert "level: 5" in result

    def test_format_game_state_updates_nested(self):
        """Test formatting nested state changes."""
        changes = {
            "player": {"name": "Hero", "stats": {"hp": 100}},
            "world": {"location": "Forest"},
        }

        result = format_game_state_updates(changes, for_html=False)

        assert "Game state updated (3 entries):" in result
        assert 'player.name: "Hero"' in result
        assert "player.stats.hp: 100" in result
        assert 'world.location: "Forest"' in result

    def test_format_game_state_updates_html(self):
        """Test formatting state changes for HTML output."""
        changes = {"key": "value"}

        result = format_game_state_updates(changes, for_html=True)

        assert "<ul>" in result
        assert "<li><code>" in result
        assert "</code></li>" in result
        assert "</ul>" in result

    def test_format_game_state_updates_empty(self):
        """Test formatting empty state changes."""
        result = format_game_state_updates({}, for_html=False)
        assert result == "No state updates."

        result = format_game_state_updates(None, for_html=False)
        assert result == "No state updates."

    def test_parse_set_command_simple(self):
        """Test parsing simple set commands."""
        payload = 'key1 = "value1"\nkey2 = 42'

        result = parse_set_command(payload)

        expected = {"key1": "value1", "key2": 42}
        assert result == expected

    def test_parse_set_command_nested(self):
        """Test parsing nested dot notation."""
        payload = 'player.name = "Hero"\nplayer.level = 5\nworld.location = "Forest"'

        result = parse_set_command(payload)

        expected = {
            "player": {"name": "Hero", "level": 5},
            "world": {"location": "Forest"},
        }
        assert result == expected

    def test_parse_set_command_append(self):
        """Test parsing append operations."""
        payload = 'items.append = "sword"\nitems.append = "shield"'

        result = parse_set_command(payload)

        # MCP architecture: append operations return list directly
        expected = {"items": ["sword", "shield"]}
        assert result == expected

    def test_parse_set_command_invalid_json(self):
        """Test parsing with invalid JSON values."""
        payload = 'valid_key = "valid_value"\ninvalid_key = invalid_json'

        result = parse_set_command(payload)

        # Should skip invalid line
        expected = {"valid_key": "valid_value"}
        assert result == expected

    def test_parse_set_command_empty_lines(self):
        """Test parsing with empty lines and no equals signs."""
        payload = 'key1 = "value1"\n\nkey2 = "value2"\nno_equals_sign\n'

        result = parse_set_command(payload)

        expected = {"key1": "value1", "key2": "value2"}
        assert result == expected

    def test_parse_set_command_three_layer_nesting_all_types(self):
        """Test parsing set commands with 3 layers of nesting and all data types."""
        test_datetime_str = "2023-06-15T14:30:45+00:00"

        payload = f"""
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
        """

        result = parse_set_command(payload)

        # Test int values at 3rd level
        assert result["player"]["stats"]["combat"]["strength"] == 18
        assert result["world"]["regions"]["north"]["population"] == 50000
        assert result["metadata"]["session"]["session_id"] == 12345

        # Test float values at 3rd level
        assert result["player"]["stats"]["combat"]["dexterity"] == 14.5
        assert result["world"]["regions"]["north"]["tax_rate"] == 0.15

        # Test bool values at 3rd level
        assert result["player"]["stats"]["combat"]["is_veteran"]
        assert not result["world"]["regions"]["north"]["is_at_war"]
        assert not result["metadata"]["session"]["is_tutorial"]

        # Test None values at 3rd level
        assert result["player"]["stats"]["combat"]["special_training"] is None
        assert result["world"]["regions"]["north"]["ruler"] is None
        assert result["metadata"]["session"]["notes"] is None

        # Test string values at 3rd level
        assert result["metadata"]["session"]["start_time"] == test_datetime_str

        # Test append operations at 3rd level - MCP architecture returns lists directly
        assert result["player"]["stats"]["combat"]["weapon_proficiencies"] == [
            "sword",
            "bow",
        ]
        assert result["world"]["regions"]["north"]["major_cities"] == [
            "Northgate",
            "Frostholm",
        ]
        assert result["metadata"]["session"]["participants"] == ["player1", "player2"]

    def test_debug_mode_command_applies_multiline_god_mode_set(self):
        """Ensure GOD_MODE_SET blocks with nested paths are applied through the debug handler."""

        game_state = GameState()
        game_state.player_character_data = {
            "stats": {
                "hp": 3,
            }
        }
        game_state.world_data = {}

        user_input = (
            "GOD_MODE_SET:\n"
            "player_character_data.stats.hp = 18\n"
            'world_data.current_location.name = "Oakvale"\n'
        )

        with patch(
            "mvp_site.world_logic.firestore_service.update_campaign_game_state"
        ) as mock_update_state:
            response = _handle_debug_mode_command(
                user_input,
                game_state,
                "user-123",
                "campaign-456",
            )

        assert response[KEY_SUCCESS] is True
        assert "player_character_data.stats.hp" in response[KEY_RESPONSE]

        mock_update_state.assert_called_once()
        _, _, updated_state = mock_update_state.call_args[0]
        assert (
            updated_state["player_character_data"]["stats"]["hp"]
            == 18
        ), "HP should be updated via GOD_MODE_SET"
        assert (
            updated_state["world_data"]["current_location"]["name"]
            == "Oakvale"
        ), "Nested world data should be merged"

    def test_debug_mode_command_returns_structured_state_for_ask(self):
        """GOD_ASK_STATE should return the raw game_state alongside the formatted response."""

        game_state = GameState()
        game_state.player_character_data = {"name": "Debugger"}

        with patch("mvp_site.world_logic.firestore_service.add_story_entry"):
            response = _handle_debug_mode_command(
                "GOD_ASK_STATE",
                game_state,
                "user-ask",
                "campaign-ask",
            )

        assert response[KEY_SUCCESS] is True
        assert "game_state" in response
        assert response["game_state"]["player_character_data"]["name"] == "Debugger"
        assert KEY_RESPONSE in response


class TestD5EMechanicsCalculations(unittest.TestCase):
    """Test cases for D&D 5E mechanics calculation functions."""

    def test_calculate_modifier_standard_scores(self):
        """Test modifier calculation for standard ability scores."""
        from mvp_site.game_state import calculate_modifier

        # Test standard D&D ability scores
        assert calculate_modifier(10) == 0, "Score 10 should give +0"
        assert calculate_modifier(11) == 0, "Score 11 should give +0"
        assert calculate_modifier(8) == -1, "Score 8 should give -1"
        assert calculate_modifier(9) == -1, "Score 9 should give -1"
        assert calculate_modifier(14) == 2, "Score 14 should give +2"
        assert calculate_modifier(15) == 2, "Score 15 should give +2"
        assert calculate_modifier(18) == 4, "Score 18 should give +4"
        assert calculate_modifier(20) == 5, "Score 20 should give +5"
        assert calculate_modifier(1) == -5, "Score 1 should give -5"
        assert calculate_modifier(30) == 10, "Score 30 should give +10"

    def test_calculate_proficiency_bonus(self):
        """Test proficiency bonus calculation by level."""
        from mvp_site.game_state import calculate_proficiency_bonus

        # Test proficiency progression
        assert calculate_proficiency_bonus(1) == 2
        assert calculate_proficiency_bonus(4) == 2
        assert calculate_proficiency_bonus(5) == 3
        assert calculate_proficiency_bonus(8) == 3
        assert calculate_proficiency_bonus(9) == 4
        assert calculate_proficiency_bonus(12) == 4
        assert calculate_proficiency_bonus(13) == 5
        assert calculate_proficiency_bonus(16) == 5
        assert calculate_proficiency_bonus(17) == 6
        assert calculate_proficiency_bonus(20) == 6

        # Edge cases
        assert calculate_proficiency_bonus(0) == 2, "Level 0 should default to +2"
        assert calculate_proficiency_bonus(21) == 6, "Level 21+ should cap at +6"

    def test_calculate_armor_class(self):
        """Test armor class calculation."""
        from mvp_site.game_state import calculate_armor_class

        # Base AC (no armor, no shield)
        assert calculate_armor_class(dex_modifier=0) == 10
        assert calculate_armor_class(dex_modifier=2) == 12
        assert calculate_armor_class(dex_modifier=-1) == 9

        # With armor bonus
        assert calculate_armor_class(dex_modifier=2, armor_bonus=3) == 15
        assert calculate_armor_class(dex_modifier=0, armor_bonus=5) == 15

        # With shield
        assert calculate_armor_class(dex_modifier=2, shield_bonus=2) == 14
        assert calculate_armor_class(dex_modifier=2, armor_bonus=3, shield_bonus=2) == 17

    def test_calculate_passive_perception(self):
        """Test passive perception calculation."""
        from mvp_site.game_state import calculate_passive_perception

        # Not proficient
        assert calculate_passive_perception(wis_modifier=0, proficient=False, proficiency_bonus=2) == 10
        assert calculate_passive_perception(wis_modifier=3, proficient=False, proficiency_bonus=2) == 13

        # Proficient
        assert calculate_passive_perception(wis_modifier=0, proficient=True, proficiency_bonus=2) == 12
        assert calculate_passive_perception(wis_modifier=3, proficient=True, proficiency_bonus=3) == 16

    def test_xp_for_cr(self):
        """Test XP lookup by Challenge Rating."""
        from mvp_site.game_state import xp_for_cr

        assert xp_for_cr(0) == 10
        assert xp_for_cr(0.125) == 25  # CR 1/8
        assert xp_for_cr(0.25) == 50   # CR 1/4
        assert xp_for_cr(0.5) == 100   # CR 1/2
        assert xp_for_cr(1) == 200
        assert xp_for_cr(3) == 700
        assert xp_for_cr(5) == 1800
        assert xp_for_cr(10) == 5900
        assert xp_for_cr(20) == 25000
        assert xp_for_cr(999) == 0  # Unknown CR returns 0

    def test_level_from_xp(self):
        """Test level calculation from total XP."""
        from mvp_site.game_state import level_from_xp

        assert level_from_xp(0) == 1
        assert level_from_xp(299) == 1
        assert level_from_xp(300) == 2
        assert level_from_xp(899) == 2
        assert level_from_xp(900) == 3
        assert level_from_xp(2699) == 3
        assert level_from_xp(2700) == 4
        assert level_from_xp(355000) == 20
        assert level_from_xp(999999) == 20  # Cap at 20

    def test_xp_needed_for_level(self):
        """Test XP threshold lookup."""
        from mvp_site.game_state import xp_needed_for_level

        assert xp_needed_for_level(1) == 0
        assert xp_needed_for_level(2) == 300
        assert xp_needed_for_level(5) == 6500
        assert xp_needed_for_level(10) == 64000
        assert xp_needed_for_level(20) == 355000

    def test_xp_to_next_level(self):
        """Test XP remaining to next level."""
        from mvp_site.game_state import xp_to_next_level

        assert xp_to_next_level(current_xp=0, current_level=1) == 300
        assert xp_to_next_level(current_xp=150, current_level=1) == 150
        assert xp_to_next_level(current_xp=300, current_level=2) == 600
        assert xp_to_next_level(current_xp=355000, current_level=20) == 0  # Max level

    def test_roll_dice_basic(self):
        """Test basic dice rolling."""
        from mvp_site.game_state import roll_dice

        # Test 1d20
        for _ in range(10):
            result = roll_dice("1d20")
            assert 1 <= result.total <= 20
            assert len(result.individual_rolls) == 1

        # Test 2d6+3
        for _ in range(10):
            result = roll_dice("2d6+3")
            assert 5 <= result.total <= 15  # 2+3 to 12+3
            assert len(result.individual_rolls) == 2
            assert result.modifier == 3

        # Test negative modifier
        result = roll_dice("1d20-2")
        assert result.modifier == -2

    def test_roll_dice_invalid_notation(self):
        """Test dice rolling with invalid notation."""
        from mvp_site.game_state import roll_dice

        result = roll_dice("invalid")
        assert result.total == 0
        assert len(result.individual_rolls) == 0

    def test_roll_dice_zero_sided_die_returns_modifier(self):
        """Invalid die sizes should not crash and should return the modifier only."""
        from mvp_site.game_state import roll_dice

        result = roll_dice("1d0")
        assert result.total == 0
        assert result.individual_rolls == []
        assert result.modifier == 0

    def test_calculate_resource_depletion(self):
        """Test resource depletion calculation."""
        from mvp_site.game_state import calculate_resource_depletion

        # 100 units at 10/day for 5 days
        remaining = calculate_resource_depletion(
            current_amount=100,
            depletion_rate=10,
            time_elapsed=5
        )
        assert remaining == 50

        # Depleted to 0
        remaining = calculate_resource_depletion(
            current_amount=100,
            depletion_rate=10,
            time_elapsed=15
        )
        assert remaining == 0  # Capped at 0, not negative


if __name__ == "__main__":
    unittest.main()
