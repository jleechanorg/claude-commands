#!/usr/bin/env python3
"""Unit tests for `structured_fields_utils.extract_structured_fields`."""

import unittest
from unittest.mock import Mock

from mvp_site import constants, structured_fields_utils
from mvp_site.llm_response import LLMResponse
from mvp_site.narrative_response_schema import NarrativeResponse


class TestStructuredFieldsUtils(unittest.TestCase):
    """Test cases for structured_fields_utils.extract_structured_fields function."""

    def setUp(self):
        """Set up test fixtures for each test."""
        # Sample structured response data
        self.sample_structured_data = {
            "session_header": "Turn 3 - Combat Phase\nHP: 25/30 | AC: 16 | Status: Engaged",
            "planning_block": "What would you like to do next?\n1. Attack with sword\n2. Cast spell\n3. Use item\n4. Retreat",
            "dice_rolls": [
                "Initiative: d20+2 = 15",
                "Attack roll: d20+5 = 18",
                "Damage: 1d8+3 = 7",
            ],
            "resources": "HP: 25/30, SP: 8/12, Gold: 150, Arrows: 24",
            "debug_info": {
                "turn_number": 3,
                "combat_active": True,
                "dm_notes": "Player chose aggressive approach",
                "dice_rolls": ["d20+5", "1d8+3"],
                "enemy_hp": 12,
            },
        }

        # Create a mock structured response object
        self.mock_structured_response = Mock(spec=NarrativeResponse)
        self.mock_structured_response.session_header = self.sample_structured_data[
            "session_header"
        ]
        self.mock_structured_response.planning_block = self.sample_structured_data[
            "planning_block"
        ]
        self.mock_structured_response.dice_rolls = self.sample_structured_data[
            "dice_rolls"
        ]
        self.mock_structured_response.resources = self.sample_structured_data[
            "resources"
        ]
        self.mock_structured_response.debug_info = self.sample_structured_data[
            "debug_info"
        ]

    def test_extract_structured_fields_with_full_data(self):
        """Test extraction with complete structured response data."""
        # Create a mock LLMResponse with structured_response
        mock_gemini_response = Mock(spec=LLMResponse)
        mock_gemini_response.structured_response = self.mock_structured_response

        # Extract structured fields
        result = structured_fields_utils.extract_structured_fields(mock_gemini_response)

        # Verify all fields are extracted correctly
        assert (
            result[constants.FIELD_SESSION_HEADER]
            == self.sample_structured_data["session_header"]
        )
        assert (
            result[constants.FIELD_PLANNING_BLOCK]
            == self.sample_structured_data["planning_block"]
        )
        assert (
            result[constants.FIELD_DICE_ROLLS]
            == self.sample_structured_data["dice_rolls"]
        )
        assert (
            result[constants.FIELD_RESOURCES]
            == self.sample_structured_data["resources"]
        )
        assert (
            result[constants.FIELD_DEBUG_INFO]
            == self.sample_structured_data["debug_info"]
        )

    def test_extract_structured_fields_with_empty_fields(self):
        """Test extraction with empty structured response fields."""
        # Create a mock structured response with empty fields
        mock_structured_response = Mock(spec=NarrativeResponse)
        mock_structured_response.session_header = ""
        mock_structured_response.planning_block = ""
        mock_structured_response.dice_rolls = []
        mock_structured_response.resources = ""
        mock_structured_response.debug_info = {}

        mock_gemini_response = Mock(spec=LLMResponse)
        mock_gemini_response.structured_response = mock_structured_response

        # Extract structured fields
        result = structured_fields_utils.extract_structured_fields(mock_gemini_response)

        # Verify all fields are empty but present
        assert result[constants.FIELD_SESSION_HEADER] == ""
        assert result[constants.FIELD_PLANNING_BLOCK] == ""
        assert result[constants.FIELD_DICE_ROLLS] == []
        assert result[constants.FIELD_RESOURCES] == {}
        assert result[constants.FIELD_DEBUG_INFO] == {}

    def test_extract_structured_fields_with_missing_attributes(self):
        """Test extraction when structured response lacks some attributes."""
        # Create a mock structured response with missing attributes
        mock_structured_response = Mock(spec=NarrativeResponse)
        mock_structured_response.session_header = "Available header"
        mock_structured_response.planning_block = "Available planning"
        # dice_rolls, resources, debug_info are missing (will use getattr default)

        mock_gemini_response = Mock(spec=LLMResponse)
        mock_gemini_response.structured_response = mock_structured_response

        # Extract structured fields
        result = structured_fields_utils.extract_structured_fields(mock_gemini_response)

        # Verify available fields are extracted, missing ones default to empty
        assert result[constants.FIELD_SESSION_HEADER] == "Available header"
        assert result[constants.FIELD_PLANNING_BLOCK] == "Available planning"
        assert result[constants.FIELD_DICE_ROLLS] == []  # Default empty list
        assert result[constants.FIELD_RESOURCES] == {}  # Default empty dict
        assert result[constants.FIELD_DEBUG_INFO] == {}  # Default empty dict

    def test_extract_structured_fields_with_no_structured_response(self):
        """Test extraction when LLMResponse has no structured_response."""
        # Create a mock LLMResponse without structured_response
        mock_gemini_response = Mock(spec=LLMResponse)
        mock_gemini_response.structured_response = None

        # Extract structured fields
        result = structured_fields_utils.extract_structured_fields(mock_gemini_response)

        # Verify result is empty dict
        assert result == {}

    def test_extract_structured_fields_with_none_values(self):
        """Test extraction when structured response has None values."""
        # Create a mock structured response with None values
        mock_structured_response = Mock(spec=NarrativeResponse)
        mock_structured_response.session_header = None
        mock_structured_response.planning_block = None
        mock_structured_response.dice_rolls = None
        mock_structured_response.resources = None
        mock_structured_response.debug_info = None

        mock_gemini_response = Mock(spec=LLMResponse)
        mock_gemini_response.structured_response = mock_structured_response

        # Extract structured fields
        result = structured_fields_utils.extract_structured_fields(mock_gemini_response)

        # Verify all fields use defaults when None
        assert result[constants.FIELD_SESSION_HEADER] == ""
        assert result[constants.FIELD_PLANNING_BLOCK] == ""
        assert result[constants.FIELD_DICE_ROLLS] == []
        assert result[constants.FIELD_RESOURCES] == {}
        assert result[constants.FIELD_DEBUG_INFO] == {}

    def test_extract_structured_fields_constants_mapping(self):
        """Test that function uses correct constants for field names."""
        # Create a mock response with data
        mock_structured_response = Mock(spec=NarrativeResponse)
        mock_structured_response.session_header = "Test session"
        mock_structured_response.planning_block = "Test planning"
        mock_structured_response.dice_rolls = ["Test roll"]
        mock_structured_response.resources = "Test resources"
        mock_structured_response.debug_info = {"test": "data"}

        mock_gemini_response = Mock(spec=LLMResponse)
        mock_gemini_response.structured_response = mock_structured_response

        # Extract structured fields
        result = structured_fields_utils.extract_structured_fields(mock_gemini_response)

        # Verify all constants are used as keys
        # Note: world_events is only included when state_updates.world_events exists
        # action_resolution and outcome_resolution are always included (even if empty) for audit trail
        expected_keys = {
            constants.FIELD_SESSION_HEADER,
            constants.FIELD_PLANNING_BLOCK,
            constants.FIELD_DICE_ROLLS,
            constants.FIELD_DICE_AUDIT_EVENTS,
            constants.FIELD_RESOURCES,
            constants.FIELD_DEBUG_INFO,
            constants.FIELD_GOD_MODE_RESPONSE,
            constants.FIELD_DIRECTIVES,
            "action_resolution",
            "outcome_resolution",
        }
        assert set(result.keys()) == expected_keys

    def test_extract_structured_fields_with_complex_debug_info(self):
        """Test extraction with complex debug info structure."""
        complex_debug_info = {
            "turn_number": 5,
            "combat_active": True,
            "dm_notes": "Player used clever strategy",
            "dice_rolls": ["d20+3", "2d6+2"],
            "enemy_status": {
                "goblin_1": {"hp": 8, "status": "wounded"},
                "goblin_2": {"hp": 12, "status": "healthy"},
            },
            "environmental_factors": ["heavy_rain", "difficult_terrain"],
        }

        mock_structured_response = Mock(spec=NarrativeResponse)
        mock_structured_response.session_header = "Complex Combat Turn"
        mock_structured_response.planning_block = "Multiple options available"
        mock_structured_response.dice_rolls = [
            "Attack: d20+3 = 16",
            "Damage: 2d6+2 = 8",
        ]
        mock_structured_response.resources = "HP: 30/30, SP: 15/20"
        mock_structured_response.debug_info = complex_debug_info

        mock_gemini_response = Mock(spec=LLMResponse)
        mock_gemini_response.structured_response = mock_structured_response

        # Extract structured fields
        result = structured_fields_utils.extract_structured_fields(mock_gemini_response)

        # Verify complex debug info is preserved
        assert result[constants.FIELD_DEBUG_INFO] == complex_debug_info
        assert result[constants.FIELD_DEBUG_INFO]["enemy_status"]["goblin_1"]["hp"] == 8
        assert result[constants.FIELD_DEBUG_INFO]["environmental_factors"] == [
            "heavy_rain",
            "difficult_terrain",
        ]

    def test_extract_structured_fields_with_long_text_fields(self):
        """Test extraction with longer text content."""
        long_session_header = """Turn 7 - Dungeon Exploration
=====================================
Current Location: Ancient Temple - Main Chamber
Party Status: All members healthy
Light Sources: 2 torches remaining (30 minutes)
Detected Threats: None visible
Recent Actions: Successfully disarmed pressure plate trap
Next Objective: Investigate the glowing altar"""

        long_planning_block = """The ancient chamber holds many secrets. What would you like to do?

1. Approach the glowing altar carefully
2. Search the walls for hidden passages
3. Cast Detect Magic on the altar
4. Have the rogue check for additional traps
5. Examine the hieroglyphs on the walls
6. Rest and tend to wounds before proceeding
7. Retreat to the previous chamber
8. Use a different approach (describe your action)"""

        mock_structured_response = Mock(spec=NarrativeResponse)
        mock_structured_response.session_header = long_session_header
        mock_structured_response.planning_block = long_planning_block
        mock_structured_response.dice_rolls = [
            "Perception: d20+4 = 18",
            "Investigation: d20+2 = 14",
        ]
        mock_structured_response.resources = "HP: 28/30, SP: 12/15, Torch time: 30 min"
        mock_structured_response.debug_info = {
            "location": "temple_chamber",
            "trap_disarmed": True,
        }

        mock_gemini_response = Mock(spec=LLMResponse)
        mock_gemini_response.structured_response = mock_structured_response

        # Extract structured fields
        result = structured_fields_utils.extract_structured_fields(mock_gemini_response)

        # Verify long text fields are preserved
        assert result[constants.FIELD_SESSION_HEADER] == long_session_header
        assert result[constants.FIELD_PLANNING_BLOCK] == long_planning_block
        assert "Ancient Temple - Main Chamber" in result[constants.FIELD_SESSION_HEADER]
        assert "different approach" in result[constants.FIELD_PLANNING_BLOCK]

    def test_extract_structured_fields_with_world_events(self):
        """Test extraction of world_events from state_updates."""
        world_events_data = {
            "background_events": [
                {"description": "A caravan arrives", "turn_generated": 5}
            ],
            "rumors": [
                {"description": "Strange sounds from the forest", "turn_generated": 5}
            ],
            "faction_updates": {
                "merchant_guild": {"activity": "Trading routes expanded"}
            },
        }
        state_updates = {"world_events": world_events_data, "other_data": "ignored"}

        mock_structured_response = Mock(spec=NarrativeResponse)
        mock_structured_response.session_header = "Turn 5"
        mock_structured_response.planning_block = "Options"
        mock_structured_response.dice_rolls = []
        mock_structured_response.dice_audit_events = []
        mock_structured_response.resources = {}
        mock_structured_response.debug_info = {}
        mock_structured_response.god_mode_response = ""
        mock_structured_response.state_updates = state_updates

        mock_gemini_response = Mock(spec=LLMResponse)
        mock_gemini_response.structured_response = mock_structured_response

        result = structured_fields_utils.extract_structured_fields(mock_gemini_response)

        # Verify world_events is extracted and state_updates is filtered
        assert "world_events" in result
        assert result["world_events"] == world_events_data
        assert result[constants.FIELD_STATE_UPDATES] == {
            "world_events": world_events_data
        }
        # other_data from state_updates should NOT be present
        assert "other_data" not in result

    def test_extract_structured_fields_without_world_events(self):
        """Test extraction when state_updates has no world_events."""
        state_updates = {"some_other_field": "value"}

        mock_structured_response = Mock(spec=NarrativeResponse)
        mock_structured_response.session_header = "Turn 1"
        mock_structured_response.planning_block = ""
        mock_structured_response.dice_rolls = []
        mock_structured_response.dice_audit_events = []
        mock_structured_response.resources = {}
        mock_structured_response.debug_info = {}
        mock_structured_response.god_mode_response = ""
        mock_structured_response.state_updates = state_updates

        mock_gemini_response = Mock(spec=LLMResponse)
        mock_gemini_response.structured_response = mock_structured_response

        result = structured_fields_utils.extract_structured_fields(mock_gemini_response)

        # world_events should NOT be in result if not present in state_updates
        assert "world_events" not in result
        assert constants.FIELD_STATE_UPDATES not in result

    def test_regression_dice_rolls_extracted_from_action_resolution_mechanics(self):
        """Test that dice_rolls are extracted from action_resolution.mechanics.rolls.

        Bug: When LLM correctly places dice rolls in action_resolution.mechanics.rolls
        (as per game_state_instruction.md:236 which says "DO NOT populate dice_rolls
        directly"), the extract_structured_fields function should extract them to
        populate the dice_rolls field for Firestore storage.

        Previously, dice_rolls was only read directly from the LLM response, resulting
        in empty [] even when action_resolution.mechanics.rolls had data.
        """
        # This matches the real Firestore data where LLM correctly puts dice in action_resolution
        action_resolution_data = {
            "interpreted_as": "Deception check",
            "audit_flags": [],
            "narrative_outcome": "Success",
            "mechanics": {
                "rolls": [
                    {
                        "success": True,
                        "result": 32,
                        "notation": "1d20+19",
                        "purpose": "Deception (The Absolute's Harvest)",
                        "dc": 15,
                    }
                ],
                "type": "skill_check",
            },
            "reinterpreted": False,
            "player_input": "some input",
        }

        mock_structured_response = Mock(spec=NarrativeResponse)
        mock_structured_response.session_header = "Turn 1"
        mock_structured_response.planning_block = {"choices": {"1": "option"}}
        mock_structured_response.dice_rolls = []  # LLM correctly leaves this empty
        mock_structured_response.dice_audit_events = []
        mock_structured_response.resources = "HP: 49/49"
        mock_structured_response.debug_info = {}
        mock_structured_response.god_mode_response = ""
        mock_structured_response.action_resolution = action_resolution_data
        mock_structured_response.outcome_resolution = {}

        mock_gemini_response = Mock(spec=LLMResponse)
        mock_gemini_response.structured_response = mock_structured_response

        result = structured_fields_utils.extract_structured_fields(mock_gemini_response)

        # Key assertion: dice_rolls should be EXTRACTED from action_resolution.mechanics.rolls
        # Format matches extract_dice_rolls_from_action_resolution output
        assert result[constants.FIELD_DICE_ROLLS] == [
            "1d20+19 = 32 vs DC 15 - Success (Deception (The Absolute's Harvest))"
        ], f"Expected dice_rolls to be extracted from action_resolution.mechanics.rolls, got: {result[constants.FIELD_DICE_ROLLS]}"

    def test_regression_dice_rolls_preserved_when_llm_provides_directly(self):
        """Test backward compatibility: if LLM provides dice_rolls directly, preserve them.

        Some older prompts may still have the LLM populate dice_rolls directly.
        This test ensures backward compatibility.
        """
        mock_structured_response = Mock(spec=NarrativeResponse)
        mock_structured_response.session_header = "Turn 1"
        mock_structured_response.planning_block = {}
        mock_structured_response.dice_rolls = ["Attack: d20+5 = 18"]  # LLM provided directly
        mock_structured_response.dice_audit_events = []
        mock_structured_response.resources = {}
        mock_structured_response.debug_info = {}
        mock_structured_response.god_mode_response = ""
        mock_structured_response.action_resolution = {}  # Empty action_resolution
        mock_structured_response.outcome_resolution = {}

        mock_gemini_response = Mock(spec=LLMResponse)
        mock_gemini_response.structured_response = mock_structured_response

        result = structured_fields_utils.extract_structured_fields(mock_gemini_response)

        # dice_rolls should be preserved from LLM response when action_resolution is empty
        assert result[constants.FIELD_DICE_ROLLS] == ["Attack: d20+5 = 18"]

    def test_regression_action_resolution_rolls_override_empty_dice_rolls(self):
        """Test that action_resolution.mechanics.rolls OVERRIDES empty dice_rolls.

        This is the single-source-of-truth principle: if action_resolution has rolls,
        they should be used even if dice_rolls is empty.
        """
        action_resolution_data = {
            "mechanics": {
                "rolls": [
                    {"notation": "1d20+5", "result": 17, "dc": 18, "success": False, "purpose": "Attack"},
                    {"notation": "1d8+3", "result": 8, "purpose": "Damage"},
                ],
            },
        }

        mock_structured_response = Mock(spec=NarrativeResponse)
        mock_structured_response.session_header = ""
        mock_structured_response.planning_block = {}
        mock_structured_response.dice_rolls = []  # Empty as per instruction
        mock_structured_response.dice_audit_events = []
        mock_structured_response.resources = {}
        mock_structured_response.debug_info = {}
        mock_structured_response.god_mode_response = ""
        mock_structured_response.action_resolution = action_resolution_data
        mock_structured_response.outcome_resolution = {}

        mock_gemini_response = Mock(spec=LLMResponse)
        mock_gemini_response.structured_response = mock_structured_response

        result = structured_fields_utils.extract_structured_fields(mock_gemini_response)

        # Should have 2 extracted dice rolls
        assert len(result[constants.FIELD_DICE_ROLLS]) == 2
        assert "1d20+5 = 17 vs DC 18 - Failure (Attack)" in result[constants.FIELD_DICE_ROLLS]
        assert "1d8+3 = 8 (Damage)" in result[constants.FIELD_DICE_ROLLS]
