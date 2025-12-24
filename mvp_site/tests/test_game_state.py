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
        assert gs.custom_campaign_state == {"attribute_system": "D&D", "arc_milestones": {}}

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
            "arc_milestones": {},
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
            "custom_campaign_state": {"attribute_system": "D&D", "arc_milestones": {}},
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


class TestCombatStateNormalization(unittest.TestCase):
    """Test cases for _normalize_combat_state() which handles LLM-generated malformed data."""

    def test_normalize_string_initiative_order_entries(self):
        """String entries in initiative_order are converted to proper dicts."""
        gs = GameState(
            combat_state={
                "in_combat": True,
                "initiative_order": ["Goblin 1", "Goblin 2"],
            }
        )

        # Should be normalized to dicts
        init_order = gs.combat_state["initiative_order"]
        assert len(init_order) == 2
        assert init_order[0] == {"name": "Goblin 1", "initiative": 0, "type": "unknown"}
        assert init_order[1] == {"name": "Goblin 2", "initiative": 0, "type": "unknown"}

    def test_normalize_dict_initiative_order_coerces_initiative(self):
        """Dict entries have initiative coerced to int."""
        gs = GameState(
            combat_state={
                "in_combat": True,
                "initiative_order": [
                    {"name": "Goblin", "initiative": "15", "type": "enemy"},
                ],
            }
        )

        init_order = gs.combat_state["initiative_order"]
        assert init_order[0]["initiative"] == 15  # String "15" -> int 15

    def test_normalize_string_combatant_values(self):
        """String combatant values are converted to proper dicts."""
        gs = GameState(
            combat_state={
                "in_combat": True,
                "combatants": {
                    "Goblin 1": "enemy",
                    "Goblin 2": "hostile",
                },
            }
        )

        combatants = gs.combat_state["combatants"]
        assert combatants["Goblin 1"] == {"hp_current": 1, "hp_max": 1, "status": []}
        assert combatants["Goblin 2"] == {"hp_current": 1, "hp_max": 1, "status": []}

    def test_normalize_combatant_hp_coerced_to_int(self):
        """Combatant HP values are coerced from strings to ints."""
        gs = GameState(
            combat_state={
                "in_combat": True,
                "combatants": {
                    "Goblin": {"hp_current": "15", "hp_max": "20", "status": []},
                },
            }
        )

        combatants = gs.combat_state["combatants"]
        assert combatants["Goblin"]["hp_current"] == 15
        assert combatants["Goblin"]["hp_max"] == 20

    def test_normalize_combatants_list_to_dict(self):
        """Combatants as list is converted to dict format."""
        gs = GameState(
            combat_state={
                "in_combat": True,
                "combatants": [
                    {"name": "Goblin 1", "hp_current": 10, "hp_max": 15},
                    {"name": "Goblin 2", "hp_current": 8, "hp_max": 12},
                ],
            }
        )

        combatants = gs.combat_state["combatants"]
        assert isinstance(combatants, dict)
        assert "Goblin 1" in combatants
        assert combatants["Goblin 1"]["hp_current"] == 10
        assert "Goblin 2" in combatants
        assert combatants["Goblin 2"]["hp_current"] == 8

    def test_normalize_preserves_type_and_role(self):
        """Type and role fields are preserved during normalization."""
        gs = GameState(
            combat_state={
                "in_combat": True,
                "combatants": {
                    "Goblin": {
                        "hp_current": 10,
                        "hp_max": 15,
                        "type": "enemy",
                        "role": "melee",
                    },
                },
            }
        )

        combatant = gs.combat_state["combatants"]["Goblin"]
        assert combatant["type"] == "enemy"
        assert combatant["role"] == "melee"

    def test_normalize_does_not_add_missing_fields(self):
        """Normalization does not add combatants/initiative_order if not present."""
        gs = GameState(combat_state={"in_combat": False})

        # Should NOT have combatants or initiative_order added
        assert "combatants" not in gs.combat_state
        assert "initiative_order" not in gs.combat_state

    def test_normalize_handles_non_dict_combat_state(self):
        """Non-dict combat_state is reset to default."""
        gs = GameState(combat_state="invalid")

        assert gs.combat_state == {"in_combat": False}

    def test_normalize_mixed_initiative_order(self):
        """Mixed string and dict entries in initiative_order are handled."""
        gs = GameState(
            combat_state={
                "in_combat": True,
                "initiative_order": [
                    "Goblin 1",  # String
                    {"name": "Hero", "initiative": 18, "type": "pc"},  # Dict
                ],
            }
        )

        init_order = gs.combat_state["initiative_order"]
        assert init_order[0] == {"name": "Goblin 1", "initiative": 0, "type": "unknown"}
        assert init_order[1] == {"name": "Hero", "initiative": 18, "type": "pc"}


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
        assert xp_to_next_level(current_xp=150, current_level=0) == 150
        assert xp_to_next_level(current_xp=150, current_level=-1) == 150
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

    def test_calculate_attack_roll_advantage_handles_empty_rolls(self):
        """Advantage should not crash if underlying roll objects have empty rolls."""
        from mvp_site.game_state import DiceRollResult, calculate_attack_roll
        from unittest.mock import patch

        def _fake_roll_with_advantage(_notation: str):
            r1 = DiceRollResult(notation="1d20+5", individual_rolls=[], modifier=5, total=5)
            r2 = DiceRollResult(notation="1d20+5", individual_rolls=[], modifier=5, total=5)
            return r1, r2, 5

        with patch("mvp_site.game_state.roll_with_advantage", new=_fake_roll_with_advantage):
            result = calculate_attack_roll(5, advantage=True, disadvantage=False)
        assert result["rolls"] == [0, 0]

    def test_execute_dice_tool_roll_attack_handles_empty_rolls(self):
        """roll_attack formatting should not crash if attack['rolls'] is empty."""
        import mvp_site.game_state as game_state
        from unittest.mock import patch

        def _fake_calculate_attack_roll(_mod: int, _adv: bool, _dis: bool):
            return {
                "rolls": [],
                "modifier": 5,
                "total": 5,
                "used_roll": "single",
                "is_critical": False,
                "is_fumble": False,
                "notation": "1d20+5",
            }

        with patch("mvp_site.game_state.calculate_attack_roll", new=_fake_calculate_attack_roll):
            result = game_state.execute_dice_tool(
                "roll_attack",
                {
                    "attack_modifier": 5,
                    "target_ac": 10,
                    "weapon_name": "Test Weapon",
                },
            )
        assert "formatted" in result

    def test_get_damage_total_for_log_handles_non_dict(self):
        """Damage total logging should tolerate non-dict damage values."""
        from mvp_site.dice import _get_damage_total_for_log

        assert _get_damage_total_for_log({"total": 7}) == 7
        assert _get_damage_total_for_log({"notation": "1d6"}) == "N/A"
        assert _get_damage_total_for_log(None) == "N/A"
        assert _get_damage_total_for_log("oops") == "N/A"

    def test_cleanup_defeated_enemies_coerces_hp_current_string(self):
        """cleanup_defeated_enemies should not crash when hp_current is a string."""
        from mvp_site.game_state import GameState

        gs = GameState.from_dict(
            {
                "game_state_version": 1,
                "player_character_data": {},
                "world_data": {},
                "npc_data": {"watch_patrol_6": {"role": "enemy"}},
                "custom_campaign_state": {},
                "combat_state": {
                    "in_combat": True,
                    "combatants": {"watch_patrol_6": {"hp_current": "0"}},
                    "initiative_order": [{"name": "watch_patrol_6", "type": "enemy"}],
                },
            }
        )
        assert gs is not None
        defeated = gs.cleanup_defeated_enemies()
        assert "watch_patrol_6" in defeated

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
# These tests verify the D&D 5e XP progression table and validation logic.
# =============================================================================


class TestXPLevelHelperFunctions(unittest.TestCase):
    """
    TDD tests for XP/level helper functions.

    D&D 5e XP Thresholds (cumulative XP required for each level):
    Level 1: 0, Level 2: 300, Level 3: 900, Level 4: 2700, Level 5: 6500,
    Level 6: 14000, Level 7: 23000, Level 8: 34000, Level 9: 48000, Level 10: 64000,
    Level 11: 85000, Level 12: 100000, Level 13: 120000, Level 14: 140000,
    Level 15: 165000, Level 16: 195000, Level 17: 225000, Level 18: 265000,
    Level 19: 305000, Level 20: 355000
    """

    def test_xp_thresholds_constant_exists(self):
        """Test that XP_THRESHOLDS constant is defined in game_state module."""
        self.assertTrue(
            hasattr(game_state_module, "XP_THRESHOLDS"),
            "XP_THRESHOLDS constant should be defined in game_state module"
        )

    def test_xp_thresholds_has_20_levels(self):
        """Test that XP_THRESHOLDS has 20 entries for levels 1-20."""
        thresholds = game_state_module.XP_THRESHOLDS
        self.assertEqual(
            len(thresholds), 20,
            "XP_THRESHOLDS should have 20 entries for levels 1-20"
        )

    def test_xp_thresholds_correct_values(self):
        """Test that XP_THRESHOLDS matches D&D 5e values."""
        expected = [
            0,       # Level 1
            300,     # Level 2
            900,     # Level 3
            2700,    # Level 4
            6500,    # Level 5
            14000,   # Level 6
            23000,   # Level 7
            34000,   # Level 8
            48000,   # Level 9
            64000,   # Level 10
            85000,   # Level 11
            100000,  # Level 12
            120000,  # Level 13
            140000,  # Level 14
            165000,  # Level 15
            195000,  # Level 16
            225000,  # Level 17
            265000,  # Level 18
            305000,  # Level 19
            355000,  # Level 20
        ]
        thresholds = game_state_module.XP_THRESHOLDS
        self.assertEqual(thresholds, expected, "XP_THRESHOLDS should match D&D 5e values")

    def test_level_from_xp_function_exists(self):
        """Test that level_from_xp function is defined."""
        self.assertTrue(
            hasattr(game_state_module, "level_from_xp"),
            "level_from_xp function should be defined in game_state module"
        )

    def test_level_from_xp_zero(self):
        """Test level_from_xp returns 1 for 0 XP."""
        level = game_state_module.level_from_xp(0)
        self.assertEqual(level, 1, "0 XP should be Level 1")

    def test_level_from_xp_level_1_boundary(self):
        """Test level_from_xp for XP values in Level 1 range (0-299)."""
        self.assertEqual(game_state_module.level_from_xp(0), 1)
        self.assertEqual(game_state_module.level_from_xp(150), 1)
        self.assertEqual(game_state_module.level_from_xp(299), 1)

    def test_level_from_xp_level_2_boundary(self):
        """Test level_from_xp for XP values at Level 2 boundary (300-899)."""
        self.assertEqual(game_state_module.level_from_xp(300), 2, "300 XP should be Level 2")
        self.assertEqual(game_state_module.level_from_xp(500), 2)
        self.assertEqual(game_state_module.level_from_xp(899), 2)

    def test_level_from_xp_level_3_boundary(self):
        """Test level_from_xp for XP values at Level 3 boundary (900-2699)."""
        self.assertEqual(game_state_module.level_from_xp(900), 3, "900 XP should be Level 3")
        self.assertEqual(game_state_module.level_from_xp(2699), 3)

    def test_level_from_xp_level_4_boundary(self):
        """Test level_from_xp for XP values at Level 4 boundary (2700-6499)."""
        self.assertEqual(game_state_module.level_from_xp(2700), 4, "2700 XP should be Level 4")
        self.assertEqual(game_state_module.level_from_xp(6499), 4)

    def test_level_from_xp_level_5_boundary(self):
        """Test level_from_xp for XP values at Level 5 boundary."""
        self.assertEqual(game_state_module.level_from_xp(6500), 5, "6500 XP should be Level 5")

    def test_level_from_xp_high_levels(self):
        """Test level_from_xp for high level boundaries."""
        self.assertEqual(game_state_module.level_from_xp(85000), 11)
        self.assertEqual(game_state_module.level_from_xp(165000), 15)
        self.assertEqual(game_state_module.level_from_xp(305000), 19)
        self.assertEqual(game_state_module.level_from_xp(355000), 20)

    def test_level_from_xp_caps_at_20(self):
        """Test level_from_xp caps at level 20 even with massive XP."""
        self.assertEqual(game_state_module.level_from_xp(500000), 20, "Should cap at Level 20")
        self.assertEqual(game_state_module.level_from_xp(1000000), 20)

    def test_level_from_xp_negative_returns_level_1(self):
        """Test level_from_xp returns Level 1 for negative XP (clamped)."""
        self.assertEqual(game_state_module.level_from_xp(-100), 1, "Negative XP should return Level 1")

    def test_xp_needed_for_level_function_exists(self):
        """Test that xp_needed_for_level function is defined."""
        self.assertTrue(
            hasattr(game_state_module, "xp_needed_for_level"),
            "xp_needed_for_level function should be defined in game_state module"
        )

    def test_xp_needed_for_level_values(self):
        """Test xp_needed_for_level returns correct thresholds."""
        self.assertEqual(game_state_module.xp_needed_for_level(1), 0)
        self.assertEqual(game_state_module.xp_needed_for_level(2), 300)
        self.assertEqual(game_state_module.xp_needed_for_level(3), 900)
        self.assertEqual(game_state_module.xp_needed_for_level(5), 6500)
        self.assertEqual(game_state_module.xp_needed_for_level(10), 64000)
        self.assertEqual(game_state_module.xp_needed_for_level(20), 355000)

    def test_xp_needed_for_level_clamps_bounds(self):
        """Test xp_needed_for_level clamps invalid levels."""
        self.assertEqual(game_state_module.xp_needed_for_level(0), 0, "Level 0 should return Level 1 threshold")
        self.assertEqual(game_state_module.xp_needed_for_level(-1), 0, "Negative level should return Level 1 threshold")
        self.assertEqual(game_state_module.xp_needed_for_level(21), 355000, "Level 21 should return Level 20 threshold")
        self.assertEqual(game_state_module.xp_needed_for_level(100), 355000, "Level 100 should return Level 20 threshold")

    def test_xp_to_next_level_function_exists(self):
        """Test that xp_to_next_level function is defined."""
        self.assertTrue(
            hasattr(game_state_module, "xp_to_next_level"),
            "xp_to_next_level function should be defined in game_state module"
        )

    def test_xp_to_next_level_at_level_start(self):
        """Test xp_to_next_level when XP is exactly at level boundary."""
        # At Level 1 start (0 XP), need 300 XP to reach Level 2
        self.assertEqual(game_state_module.xp_to_next_level(0), 300)
        # At Level 2 start (300 XP), need 600 XP to reach Level 3
        self.assertEqual(game_state_module.xp_to_next_level(300), 600)
        # At Level 3 start (900 XP), need 1800 XP to reach Level 4
        self.assertEqual(game_state_module.xp_to_next_level(900), 1800)

    def test_xp_to_next_level_mid_level(self):
        """Test xp_to_next_level when XP is in middle of a level."""
        # At 150 XP (Level 1), need 150 XP to reach Level 2
        self.assertEqual(game_state_module.xp_to_next_level(150), 150)
        # At 500 XP (Level 2), need 400 XP to reach Level 3
        self.assertEqual(game_state_module.xp_to_next_level(500), 400)

    def test_xp_to_next_level_at_level_20(self):
        """Test xp_to_next_level returns 0 at Level 20 (max level)."""
        self.assertEqual(game_state_module.xp_to_next_level(355000), 0, "Level 20 should need 0 XP to next")
        self.assertEqual(game_state_module.xp_to_next_level(500000), 0, "Beyond Level 20 should need 0 XP")


class TestXPLevelValidation(unittest.TestCase):
    """
    TDD tests for XP/level validation in GameState.

    Tests verify:
    - Level is auto-corrected when it doesn't match XP
    - Strict mode raises errors on mismatch
    - Invalid XP/level values are clamped
    """

    def test_validate_xp_level_function_exists(self):
        """Test that validate_xp_level method exists on GameState."""
        gs = GameState()
        self.assertTrue(
            hasattr(gs, "validate_xp_level"),
            "GameState should have validate_xp_level method"
        )

    def test_validate_xp_level_correct_data_passes(self):
        """Test validation passes when XP and level match."""
        gs = GameState(
            player_character_data={
                "experience": {"current": 900},
                "level": 3
            }
        )
        # Should not raise, should return True or the corrected data
        result = gs.validate_xp_level()
        self.assertTrue(result.get("valid", True), "Valid XP/level should pass validation")

    def test_validate_xp_level_mismatch_autocorrects(self):
        """Test validation auto-corrects level when XP doesn't match."""
        # Level 1 with 5000 XP should be corrected to Level 4 (2700-6499 range)
        gs = GameState(
            player_character_data={
                "experience": {"current": 5000},
                "level": 1  # Wrong! Should be Level 4
            }
        )
        result = gs.validate_xp_level()
        self.assertTrue(result.get("corrected", False), "Should flag as corrected")
        self.assertEqual(result.get("expected_level"), 4, "Expected level should be 4")
        self.assertEqual(result.get("provided_level"), 1, "Provided level should be recorded as 1")
        self.assertEqual(gs.player_character_data.get("level"), 4, "Level should be auto-corrected in state")

    def test_validate_xp_level_strict_mode_raises(self):
        """Test strict mode raises error on XP/level mismatch."""
        gs = GameState(
            player_character_data={
                "experience": {"current": 5000},
                "level": 1  # Wrong!
            }
        )
        with self.assertRaises(ValueError) as context:
            gs.validate_xp_level(strict=True)
        self.assertIn("mismatch", str(context.exception).lower())

    def test_validate_xp_level_negative_xp_clamped(self):
        """Test negative XP is clamped to 0."""
        gs = GameState(
            player_character_data={
                "experience": {"current": -100},
                "level": 1
            }
        )
        result = gs.validate_xp_level()
        self.assertEqual(result.get("clamped_xp"), 0, "Negative XP should be clamped to 0")
        self.assertEqual(
            gs.player_character_data.get("experience", {}).get("current"),
            0,
            "Clamped XP should persist to player data",
        )

    def test_validate_xp_level_zero_level_clamped(self):
        """Test level 0 is clamped to 1."""
        gs = GameState(
            player_character_data={
                "experience": {"current": 0},
                "level": 0  # Invalid, should be 1
            }
        )
        result = gs.validate_xp_level()
        self.assertEqual(result.get("clamped_level"), 1, "Level 0 should be clamped to 1")
        self.assertEqual(gs.player_character_data.get("level"), 1, "Level clamp should persist")

    def test_validate_xp_level_level_over_20_clamped(self):
        """Test level over 20 is clamped to 20."""
        gs = GameState(
            player_character_data={
                "experience": {"current": 355000},
                "level": 25  # Invalid, should be 20
            }
        )
        result = gs.validate_xp_level()
        self.assertEqual(result.get("clamped_level"), 20, "Level over 20 should be clamped to 20")
        self.assertEqual(gs.player_character_data.get("level"), 20, "Max level clamp should persist")

    def test_validate_xp_level_missing_xp_uses_default(self):
        """Test validation handles missing XP gracefully."""
        gs = GameState(
            player_character_data={
                "level": 1
                # No experience field
            }
        )
        result = gs.validate_xp_level()
        # Should not crash, should assume XP=0 for Level 1
        self.assertTrue(result.get("valid", True))

    def test_validate_xp_level_missing_level_uses_xp(self):
        """Test validation handles missing level by computing from XP."""
        gs = GameState(
            player_character_data={
                "experience": {"current": 2700}
                # No level field
            }
        )
        result = gs.validate_xp_level()
        self.assertEqual(result.get("expected_level"), 4, "Should compute level 4 from 2700 XP")
        self.assertEqual(
            gs.player_character_data.get("level"),
            4,
            "Computed level should be persisted to player_character_data",
        )


class TestTimeMonotonicity(unittest.TestCase):
    """
    TDD tests for time monotonicity validation.

    Tests verify:
    - Time cannot go backwards (warn or reject)
    - Default behavior: warn and keep old time
    - Strict mode: reject backwards time
    """

    def test_validate_time_monotonicity_function_exists(self):
        """Test that validate_time_monotonicity method exists on GameState."""
        gs = GameState()
        self.assertTrue(
            hasattr(gs, "validate_time_monotonicity"),
            "GameState should have validate_time_monotonicity method"
        )

    def test_time_monotonicity_forward_time_passes(self):
        """Test that forward time progression passes validation."""
        gs = GameState(
            world_data={
                "world_time": {"hour": 10, "minute": 0}
            }
        )
        new_time = {"hour": 12, "minute": 0}  # Later time
        result = gs.validate_time_monotonicity(new_time)
        self.assertTrue(result.get("valid", True), "Forward time should pass")

    def test_time_monotonicity_backwards_time_warns(self):
        """Test that backwards time triggers warning in default mode."""
        gs = GameState(
            world_data={
                "world_time": {"hour": 14, "minute": 0}
            }
        )
        new_time = {"hour": 10, "minute": 0}  # Earlier time (regression!)
        result = gs.validate_time_monotonicity(new_time)
        self.assertTrue(result.get("warning", False), "Backwards time should trigger warning")
        self.assertIn("regression", result.get("message", "").lower())

    def test_time_monotonicity_backwards_time_strict_raises(self):
        """Test that backwards time raises error in strict mode."""
        gs = GameState(
            world_data={
                "world_time": {"hour": 14, "minute": 0}
            }
        )
        new_time = {"hour": 10, "minute": 0}  # Earlier time
        with self.assertRaises(ValueError) as context:
            gs.validate_time_monotonicity(new_time, strict=True)
        self.assertIn("backwards", str(context.exception).lower())

    def test_time_monotonicity_same_time_passes(self):
        """Test that same time passes validation (no progression, but not regression)."""
        gs = GameState(
            world_data={
                "world_time": {"hour": 10, "minute": 30}
            }
        )
        new_time = {"hour": 10, "minute": 30}  # Same time
        result = gs.validate_time_monotonicity(new_time)
        self.assertTrue(result.get("valid", True), "Same time should pass")

    def test_time_monotonicity_day_boundary_handles_correctly(self):
        """Test time progression across day boundary (23:00 -> 01:00 next day)."""
        gs = GameState(
            world_data={
                "world_time": {"hour": 23, "minute": 0, "day": 1}
            }
        )
        # Next day, earlier hour but later overall
        new_time = {"hour": 1, "minute": 0, "day": 2}
        result = gs.validate_time_monotonicity(new_time)
        self.assertTrue(result.get("valid", True), "Day boundary crossing should be valid")

    def test_time_monotonicity_missing_new_day_defaults_to_previous_day(self):
        """New time without day should use previous day's context to avoid false regression."""
        gs = GameState(
            world_data={
                "world_time": {"hour": 10, "minute": 0, "day": 5}
            }
        )
        new_time = {"hour": 12, "minute": 0}  # Later on same day, day omitted
        result = gs.validate_time_monotonicity(new_time)
        self.assertTrue(result.get("valid", True), "Should treat missing day as previous day")
        self.assertFalse(result.get("warning", False), "No warning expected when time moves forward")

    def test_time_monotonicity_missing_old_time_passes(self):
        """Test validation passes when there's no previous time."""
        gs = GameState(
            world_data={}  # No world_time
        )
        new_time = {"hour": 10, "minute": 0}
        result = gs.validate_time_monotonicity(new_time)
        self.assertTrue(result.get("valid", True), "No previous time should pass")

    def test_time_monotonicity_mutation_bug_without_deepcopy(self):
        """
        RED TEST: Demonstrates the bug WITHOUT deepcopy.

        BUG: When original_world_time is a reference (not a copy), it gets mutated
        by update_state_with_changes(), so backward time compares equal to itself.

        This test PROVES the bug exists when deepcopy is not used.
        """
        from mvp_site.firestore_service import update_state_with_changes

        # Setup: state with time 14:00 (2pm)
        state_dict = {
            "world_data": {
                "world_time": {"hour": 14, "minute": 0, "day": 1}
            }
        }

        # BUGGY pattern: NO deepcopy - just get reference
        original_world_time = (state_dict.get("world_data") or {}).get("world_time")

        # Changes that set time backward to 10:00 (10am)
        changes = {
            "world_data": {
                "world_time": {"hour": 10, "minute": 0, "day": 1}  # Backward!
            }
        }

        # This mutates state_dict in place - AND mutates our reference!
        update_state_with_changes(state_dict, changes)

        # BUG PROOF: original_world_time WAS mutated (now shows 10, not 14)
        self.assertEqual(
            original_world_time["hour"], 10,
            "BUG: Without deepcopy, original_world_time gets mutated to 10"
        )

        # BUG CONSEQUENCE: backward time is NOT detected because both are 10:00
        gs = GameState(world_data={"world_time": original_world_time})
        new_time = {"hour": 10, "minute": 0, "day": 1}
        result = gs.validate_time_monotonicity(new_time)
        self.assertFalse(
            result.get("warning", False),
            "BUG: Backward time NOT detected because reference was mutated"
        )

    def test_time_monotonicity_mutation_fix_with_deepcopy(self):
        """
        GREEN TEST: Demonstrates the fix WITH deepcopy.

        FIX: Use copy.deepcopy() to capture original_world_time before mutation.
        This preserves the original value so backward time IS detected.

        See: world_logic.py lines 902, 1812, 1881
        """
        import copy
        from mvp_site.firestore_service import update_state_with_changes

        # Setup: state with time 14:00 (2pm)
        state_dict = {
            "world_data": {
                "world_time": {"hour": 14, "minute": 0, "day": 1}
            }
        }

        # FIXED pattern: deep-copy before mutation
        original_world_time = copy.deepcopy(
            (state_dict.get("world_data") or {}).get("world_time")
        )

        # Changes that set time backward to 10:00 (10am)
        changes = {
            "world_data": {
                "world_time": {"hour": 10, "minute": 0, "day": 1}  # Backward!
            }
        }

        # This mutates state_dict in place - but NOT our deep copy
        update_state_with_changes(state_dict, changes)

        # FIX PROOF: original_world_time is preserved (still 14)
        self.assertEqual(
            original_world_time["hour"], 14,
            "FIX: With deepcopy, original_world_time is preserved at 14"
        )

        # FIX CONSEQUENCE: backward time IS detected
        gs = GameState(world_data={"world_time": original_world_time})
        new_time = {"hour": 10, "minute": 0, "day": 1}
        result = gs.validate_time_monotonicity(new_time)
        self.assertTrue(
            result.get("warning", False),
            "FIX: Backward time (14:00 -> 10:00) IS detected with deepcopy"
        )


class TestTypeSafetyCoercion(unittest.TestCase):
    """
    Tests for type safety in XP/level validation and time functions.

    Verifies that string values (common from JSON/LLM responses) are handled
    correctly without crashing or causing incorrect comparisons.
    """

    # =========================================================================
    # Helper Function Type Safety Tests
    # =========================================================================

    def test_level_from_xp_string_input(self):
        """Test level_from_xp handles string XP values from JSON."""
        # String "5000" should be coerced to int and return level 4
        result = game_state_module.level_from_xp("5000")
        self.assertEqual(result, 4, "String '5000' should coerce to level 4")

    def test_level_from_xp_string_zero(self):
        """Test level_from_xp handles string '0' correctly."""
        result = game_state_module.level_from_xp("0")
        self.assertEqual(result, 1, "String '0' should return level 1")

    def test_level_from_xp_float_input(self):
        """Test level_from_xp handles float XP values."""
        result = game_state_module.level_from_xp(5000.5)
        self.assertEqual(result, 4, "Float 5000.5 should coerce to level 4")

    def test_level_from_xp_invalid_string_returns_level_1(self):
        """Test level_from_xp handles non-numeric strings gracefully."""
        result = game_state_module.level_from_xp("invalid")
        self.assertEqual(result, 1, "Invalid string should default to level 1")

    def test_xp_needed_for_level_string_input(self):
        """Test xp_needed_for_level handles string level values."""
        result = game_state_module.xp_needed_for_level("5")
        self.assertEqual(result, 6500, "String '5' should return XP for level 5")

    def test_xp_to_next_level_string_input(self):
        """Test xp_to_next_level handles string XP values."""
        result = game_state_module.xp_to_next_level("150")
        self.assertEqual(result, 150, "String '150' should return 150 XP to level 2")

    # =========================================================================
    # validate_xp_level Type Safety Tests
    # =========================================================================

    def test_validate_xp_level_string_xp(self):
        """Test validate_xp_level handles string XP values from JSON/LLM."""
        gs = GameState(
            player_character_data={
                "xp": "5000",  # String from JSON
                "level": 4
            }
        )
        result = gs.validate_xp_level()
        self.assertTrue(result.get("valid", False), "String XP '5000' should validate for level 4")

    def test_validate_xp_level_string_level(self):
        """Test validate_xp_level handles string level values from JSON/LLM."""
        gs = GameState(
            player_character_data={
                "xp": 5000,
                "level": "4"  # String from JSON
            }
        )
        result = gs.validate_xp_level()
        self.assertTrue(result.get("valid", False), "String level '4' should validate for 5000 XP")

    def test_validate_xp_level_both_strings(self):
        """Test validate_xp_level handles both XP and level as strings."""
        gs = GameState(
            player_character_data={
                "xp": "5000",  # String from JSON
                "level": "4"  # String from JSON
            }
        )
        result = gs.validate_xp_level()
        self.assertTrue(result.get("valid", False), "Both string XP and level should validate")

    def test_validate_xp_level_string_xp_in_experience_dict(self):
        """Test validate_xp_level handles string XP in experience.current structure."""
        gs = GameState(
            player_character_data={
                "experience": {"current": "2700"},  # String from JSON
                "level": 4
            }
        )
        result = gs.validate_xp_level()
        self.assertTrue(result.get("valid", False), "String XP in experience dict should validate")

    def test_validate_xp_level_string_mismatch_detected(self):
        """Test that string type doesn't cause false mismatch (string '5' != int 5)."""
        gs = GameState(
            player_character_data={
                "xp": "300",
                "level": "2"  # Correct for 300 XP
            }
        )
        result = gs.validate_xp_level()
        # String "2" should equal int 2 after coercion
        self.assertTrue(result.get("valid", False), "String '2' should match expected level 2")
        self.assertFalse(result.get("corrected", False), "No correction needed for matching values")

    def test_validate_xp_level_missing_level_persists_computed(self):
        """Test that missing level is computed and persisted to state."""
        gs = GameState(
            player_character_data={
                "xp": 2700
                # No level field
            }
        )
        result = gs.validate_xp_level()
        self.assertEqual(result.get("computed_level"), 4, "Should compute level 4")
        # Check that level was persisted to state
        self.assertEqual(
            gs.player_character_data.get("level"), 4,
            "Computed level should be persisted to player_character_data"
        )

    def test_validate_xp_level_scalar_negative_persisted(self):
        """Test that scalar negative experience is clamped and persisted."""
        # Bug fix test: scalar experience (not dict) negative values
        # must be clamped and persisted back to the state
        gs = GameState(
            player_character_data={
                "experience": -100,  # Scalar negative (not dict)
                "level": 1
            }
        )
        result = gs.validate_xp_level()
        self.assertEqual(result.get("clamped_xp"), 0, "Negative XP should be clamped to 0")
        # Critical: scalar experience must be updated (not just dict format)
        self.assertEqual(
            gs.player_character_data.get("experience"),
            0,
            "Scalar negative experience should be persisted as 0"
        )

    # =========================================================================
    # Time Validation Type Safety Tests
    # =========================================================================

    def test_time_to_minutes_string_values(self):
        """Test _time_to_minutes handles string time values from JSON/LLM."""
        gs = GameState(
            world_data={
                "world_time": {"hour": 10, "minute": 0}
            }
        )
        # String time values
        new_time = {"hour": "12", "minute": "30"}
        result = gs.validate_time_monotonicity(new_time)
        self.assertTrue(result.get("valid", True), "String time values should work")

    def test_time_to_minutes_string_day(self):
        """Test _time_to_minutes handles string day values."""
        gs = GameState(
            world_data={
                "world_time": {"hour": 10, "minute": 0, "day": 1}
            }
        )
        new_time = {"hour": "12", "minute": "0", "day": "2"}
        result = gs.validate_time_monotonicity(new_time)
        self.assertTrue(result.get("valid", True), "String day should work")

    def test_time_to_minutes_mixed_types(self):
        """Test _time_to_minutes handles mixed int/string types."""
        gs = GameState(
            world_data={
                "world_time": {"hour": "10", "minute": 0, "day": 1}  # hour is string
            }
        )
        new_time = {"hour": 12, "minute": "30", "day": "1"}  # mixed types
        result = gs.validate_time_monotonicity(new_time)
        self.assertTrue(result.get("valid", True), "Mixed types should work")

    # =========================================================================
    # Scalar Experience Value Tests
    # =========================================================================

    def test_validate_xp_level_scalar_experience_int(self):
        """Test validate_xp_level handles scalar int experience values."""
        gs = GameState(
            player_character_data={
                "experience": 2700,  # Scalar int (not dict with "current")
                "level": 4
            }
        )
        result = gs.validate_xp_level()
        self.assertTrue(result.get("valid", False), "Scalar int experience should validate")
        self.assertEqual(result.get("expected_level"), 4, "Should compute level 4 from 2700 XP")

    def test_validate_xp_level_scalar_experience_str(self):
        """Test validate_xp_level handles scalar string experience values."""
        gs = GameState(
            player_character_data={
                "experience": "5000",  # Scalar string (not dict with "current")
                "level": 4
            }
        )
        result = gs.validate_xp_level()
        self.assertTrue(result.get("valid", False), "Scalar string experience should validate")
        self.assertEqual(result.get("expected_level"), 4, "Should compute level 4 from 5000 XP")

    def test_validate_xp_level_scalar_experience_mismatch(self):
        """Test that scalar experience correctly detects level mismatch."""
        gs = GameState(
            player_character_data={
                "experience": 2700,  # Scalar int - should be level 4
                "level": 1  # Incorrect level
            }
        )
        result = gs.validate_xp_level()
        self.assertFalse(result.get("valid", True), "Mismatch should be detected")
        self.assertTrue(result.get("corrected", False), "Level should be corrected")
        self.assertEqual(gs.player_character_data.get("level"), 4, "Level should be corrected to 4")

    def test_validate_xp_level_scalar_experience_missing_level(self):
        """Test that missing level is computed from scalar experience."""
        gs = GameState(
            player_character_data={
                "experience": 6500  # Scalar int, no level field
            }
        )
        result = gs.validate_xp_level()
        self.assertEqual(result.get("computed_level"), 5, "Should compute level 5 from 6500 XP")
        self.assertEqual(
            gs.player_character_data.get("level"), 5,
            "Computed level should be persisted"
        )


class TestExecuteToolRequests(unittest.TestCase):
    """Test cases for execute_tool_requests function."""

    def test_invalid_input_type(self):
        result = game_state_module.execute_tool_requests("not a list")
        self.assertEqual(result, [])

    def test_invalid_item_type(self):
        result = game_state_module.execute_tool_requests(["not a dict"])
        self.assertEqual(result, [])

    def test_invalid_tool_name(self):
        requests = [{"tool": 123, "args": {}}, {"tool": "", "args": {}}]
        result = game_state_module.execute_tool_requests(requests)
        self.assertEqual(result, [])

    @patch("mvp_site.game_state.execute_dice_tool")
    def test_valid_request(self, mock_execute):
        mock_execute.return_value = {"success": True}
        requests = [{"tool": "roll_dice", "args": {"notation": "1d20"}}]

        result = game_state_module.execute_tool_requests(requests)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["tool"], "roll_dice")
        self.assertEqual(result[0]["result"], {"success": True})
        mock_execute.assert_called_with("roll_dice", {"notation": "1d20"})

    @patch("mvp_site.game_state.execute_dice_tool")
    def test_exception_handling(self, mock_execute):
        mock_execute.side_effect = Exception("Tool error")
        requests = [{"tool": "roll_dice", "args": {}}]

        result = game_state_module.execute_tool_requests(requests)

        self.assertEqual(len(result), 1)
        self.assertIn("error", result[0]["result"])
        self.assertEqual(result[0]["result"]["error"], "Tool error")


class TestFormatToolResultsText(unittest.TestCase):
    def test_non_list_returns_empty(self):
        self.assertEqual(game_state_module.format_tool_results_text("nope"), "")

    def test_formats_valid_results(self):
        tool_results = [
            {"tool": "roll_dice", "args": {"notation": "1d20"}, "result": {"total": 12}},
        ]
        text = game_state_module.format_tool_results_text(tool_results)
        self.assertIn("- roll_dice:", text)
        self.assertIn('"total": 12', text)

    def test_prefers_formatted_string(self):
        tool_results = [
            {
                "tool": "roll_attack",
                "args": {"attack_modifier": 5},
                "result": {"formatted": "Attack: 1d20+5 = 12+5 = 17 vs AC 15 (Hit!)"},
            }
        ]
        text = game_state_module.format_tool_results_text(tool_results)
        self.assertEqual(text, "- Attack: 1d20+5 = 12+5 = 17 vs AC 15 (Hit!)")

    def test_ignores_invalid_items(self):
        tool_results = [
            "not a dict",
            {"tool": "", "args": {}, "result": {}},
            {"tool": 123, "args": {}, "result": {}},
        ]
        self.assertEqual(game_state_module.format_tool_results_text(tool_results), "")


if __name__ == "__main__":
    unittest.main()
