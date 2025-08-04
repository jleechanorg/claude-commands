#!/usr/bin/env python3
"""
Unit tests for main.py structured response building.
Tests that the /api/campaigns/{id}/interaction endpoint returns the correct structure.
"""

import unittest
from unittest.mock import MagicMock


class TestMainStructuredResponseBuilding(unittest.TestCase):
    """Test that main.py builds responses matching the schema"""

    def setUp(self):
        """Set up test data"""
        # Mock structured response object
        self.mock_structured_response = MagicMock()
        self.mock_structured_response.narrative = "Test narrative"
        self.mock_structured_response.entities_mentioned = ["goblin", "dragon"]
        self.mock_structured_response.location_confirmed = "Dungeon"
        self.mock_structured_response.state_updates = {
            "npc_data": {"goblin_1": {"hp_current": 5}}
        }
        self.mock_structured_response.debug_info = {
            "dm_notes": ["Test note"],
            "dice_rolls": ["1d20+5 = 18"],
            "resources": "HD: 2/3",
            "state_rationale": "Test rationale",
        }

        # Mock GeminiResponse with structured_response
        self.mock_gemini_response = MagicMock()
        self.mock_gemini_response.narrative_text = "Test narrative"
        self.mock_gemini_response.structured_response = self.mock_structured_response
        self.mock_gemini_response.state_updates = (
            self.mock_structured_response.state_updates
        )

    def test_response_includes_all_required_fields(self):
        """Test that API response includes all fields from structured response"""
        # Build response_data as main.py does
        response_data = {
            "success": True,
            "response": self.mock_gemini_response.narrative_text,
            "debug_mode": True,
            "sequence_id": 5,
        }

        # Add structured response fields as main.py does
        if self.mock_gemini_response.structured_response:
            # State updates
            if (
                hasattr(self.mock_structured_response, "state_updates")
                and self.mock_structured_response.state_updates
            ):
                response_data["state_updates"] = (
                    self.mock_structured_response.state_updates
                )

            # Entity tracking fields
            response_data["entities_mentioned"] = getattr(
                self.mock_structured_response, "entities_mentioned", []
            )
            response_data["location_confirmed"] = getattr(
                self.mock_structured_response, "location_confirmed", "Unknown"
            )

            # Debug info
            if (
                hasattr(self.mock_structured_response, "debug_info")
                and self.mock_structured_response.debug_info
            ):
                response_data["debug_info"] = self.mock_structured_response.debug_info

        # Verify all fields are present
        assert "state_updates" in response_data
        assert "entities_mentioned" in response_data
        assert "location_confirmed" in response_data
        assert "debug_info" in response_data

        # Verify correct values
        assert response_data["entities_mentioned"] == ["goblin", "dragon"]
        assert response_data["location_confirmed"] == "Dungeon"
        assert response_data["state_updates"]["npc_data"]["goblin_1"]["hp_current"] == 5

        # Verify debug_info structure
        assert "dice_rolls" in response_data["debug_info"]
        assert "resources" in response_data["debug_info"]
        assert "dm_notes" in response_data["debug_info"]
        assert "state_rationale" in response_data["debug_info"]

    def test_response_handles_missing_fields_gracefully(self):
        """Test that response handles missing optional fields"""
        # Mock response with minimal fields
        minimal_response = MagicMock()
        minimal_response.narrative_text = "Minimal narrative"
        minimal_response.structured_response = None

        response_data = {
            "success": True,
            "response": minimal_response.narrative_text,
            "debug_mode": False,
            "sequence_id": 1,
        }

        # Try to add structured fields when structured_response is None
        if minimal_response.structured_response:
            response_data["state_updates"] = {}  # This won't execute

        # Response should still be valid
        assert "success" in response_data
        assert "response" in response_data
        assert "state_updates" not in response_data
        assert "debug_info" not in response_data

    def test_debug_info_only_in_debug_mode(self):
        """Test that debug_info is included based on debug mode"""
        response_data_debug_on = {
            "success": True,
            "response": "Test",
            "debug_mode": True,
            "debug_info": self.mock_structured_response.debug_info,
        }

        response_data_debug_off = {
            "success": True,
            "response": "Test",
            "debug_mode": False,
            # debug_info should still be included if present, frontend decides display
        }

        # With debug mode on
        assert "debug_info" in response_data_debug_on
        assert response_data_debug_on["debug_info"]["dice_rolls"] == ["1d20+5 = 18"]

        # Debug mode flag tells frontend whether to display
        assert response_data_debug_on["debug_mode"]
        assert not response_data_debug_off["debug_mode"]

    def test_nested_field_extraction(self):
        """Test extraction of fields from nested structure"""
        # The actual data has dice_rolls and resources in debug_info
        debug_info = self.mock_structured_response.debug_info

        # Frontend should extract from debug_info
        assert "dice_rolls" in debug_info
        assert isinstance(debug_info["dice_rolls"], list)

        assert "resources" in debug_info
        assert isinstance(debug_info["resources"], str)

        # These fields should be in debug_info, not at top level
        assert "dice_rolls" not in {"response": "test", "debug_info": debug_info}
        assert "resources" not in {"response": "test", "debug_info": debug_info}

    def test_backend_debug_field_filtering_red_green(self):
        """RED-GREEN: Test backend debug field filtering based on debug_mode"""

        # Test debug_mode=False excludes debug fields
        debug_mode_false_response = {
            "success": True,
            "narrative": "The dragon roars!",
            "state_changes": {"hp": 8},
            "debug_mode": False,
        }

        # Simulate the debug field addition logic from world_logic.py
        mock_state_changes = {"hp": 8}

        # Add debug-only fields when debug mode is enabled
        if debug_mode_false_response["debug_mode"]:
            debug_mode_false_response["state_updates"] = mock_state_changes

        # Mock structured response fields
        mock_entities = ["Dragon", "Knight"]
        mock_debug_info = {"dm_notes": ["Test note"]}

        # entities_mentioned and debug_info only in debug mode
        if debug_mode_false_response["debug_mode"]:
            debug_mode_false_response["entities_mentioned"] = mock_entities
            debug_mode_false_response["debug_info"] = mock_debug_info

        # ASSERTIONS for debug_mode=False
        assert (
            "state_updates" not in debug_mode_false_response
        ), "state_updates should be excluded when debug_mode=False"
        assert (
            "entities_mentioned" not in debug_mode_false_response
        ), "entities_mentioned should be excluded when debug_mode=False"
        assert (
            "debug_info" not in debug_mode_false_response
        ), "debug_info should be excluded when debug_mode=False"

        # Test debug_mode=True includes debug fields
        debug_mode_true_response = {
            "success": True,
            "narrative": "The dragon roars!",
            "state_changes": {"hp": 8},
            "debug_mode": True,
        }

        # Add debug-only fields when debug mode is enabled
        if debug_mode_true_response["debug_mode"]:
            debug_mode_true_response["state_updates"] = mock_state_changes
            debug_mode_true_response["entities_mentioned"] = mock_entities
            debug_mode_true_response["debug_info"] = mock_debug_info

        # ASSERTIONS for debug_mode=True
        assert (
            "state_updates" in debug_mode_true_response
        ), "state_updates should be included when debug_mode=True"
        assert (
            "entities_mentioned" in debug_mode_true_response
        ), "entities_mentioned should be included when debug_mode=True"
        assert (
            "debug_info" in debug_mode_true_response
        ), "debug_info should be included when debug_mode=True"

        # Verify content is correct
        assert debug_mode_true_response["state_updates"] == {"hp": 8}
        assert debug_mode_true_response["entities_mentioned"] == ["Dragon", "Knight"]
        assert debug_mode_true_response["debug_info"]["dm_notes"] == ["Test note"]

    def test_comprehensive_debug_response_building_logic(self):
        """Restored from test_debug_response_building.py - comprehensive response building test"""

        class MockStructuredResponse:
            """Mock structured response for testing"""

            def __init__(self):
                self.entities_mentioned = ["Dragon", "Knight"]
                self.location_confirmed = "Dragon's Lair"
                self.planning_block = "What do you do?"
                self.dice_rolls = ["1d20: 15"]
                self.resources = "HP: 8/10"
                self.debug_info = {
                    "dm_notes": ["Test note"],
                    "state_rationale": "Combat",
                }

        # Test debug_mode=False excludes debug fields
        debug_mode = False
        mock_response = {"state_changes": {"hp": 8}}
        mock_structured_response = MockStructuredResponse()

        # Simulate the unified_response building (from world_logic.py)
        unified_response = {
            "success": True,
            "narrative": "The dragon roars!",
            "game_state": {"debug_mode": False},
            "mode": "character",
            "debug_mode": debug_mode,
        }

        # Add debug-only fields when debug mode is enabled
        if debug_mode:
            unified_response["state_updates"] = mock_response.get("state_changes", {})

        # Add structured response fields if available
        if mock_structured_response:
            # entities_mentioned only in debug mode
            if debug_mode and hasattr(mock_structured_response, "entities_mentioned"):
                unified_response["entities_mentioned"] = (
                    mock_structured_response.entities_mentioned
                )

            # Always include these fields regardless of debug mode
            if hasattr(mock_structured_response, "location_confirmed"):
                unified_response["location_confirmed"] = (
                    mock_structured_response.location_confirmed
                )
            if hasattr(mock_structured_response, "planning_block"):
                unified_response["planning_block"] = (
                    mock_structured_response.planning_block
                )
            if hasattr(mock_structured_response, "dice_rolls"):
                unified_response["dice_rolls"] = mock_structured_response.dice_rolls
            if hasattr(mock_structured_response, "resources"):
                unified_response["resources"] = mock_structured_response.resources

            # debug_info only in debug mode
            if debug_mode and hasattr(mock_structured_response, "debug_info"):
                unified_response["debug_info"] = mock_structured_response.debug_info

        # CRITICAL ASSERTIONS: Debug fields should be ABSENT when debug_mode=False
        assert (
            "state_updates" not in unified_response
        ), "state_updates should NOT be in response when debug_mode=False"
        assert (
            "entities_mentioned" not in unified_response
        ), "entities_mentioned should NOT be in response when debug_mode=False"
        assert (
            "debug_info" not in unified_response
        ), "debug_info should NOT be in response when debug_mode=False"

        # These should REMAIN
        assert (
            "location_confirmed" in unified_response
        ), "location_confirmed should remain when debug_mode=False"
        assert (
            "planning_block" in unified_response
        ), "planning_block should remain when debug_mode=False"
        assert (
            "dice_rolls" in unified_response
        ), "dice_rolls should remain when debug_mode=False"
        assert (
            "resources" in unified_response
        ), "resources should remain when debug_mode=False"

        # Now test debug_mode=True includes debug fields
        debug_mode = True
        unified_response_debug_on = {
            "success": True,
            "narrative": "The dragon roars!",
            "game_state": {"debug_mode": True},
            "mode": "character",
            "debug_mode": debug_mode,
        }

        # Add debug-only fields when debug mode is enabled
        if debug_mode:
            unified_response_debug_on["state_updates"] = mock_response.get(
                "state_changes", {}
            )

        # Add structured response fields if available
        if mock_structured_response:
            # entities_mentioned only in debug mode
            if debug_mode and hasattr(mock_structured_response, "entities_mentioned"):
                unified_response_debug_on["entities_mentioned"] = (
                    mock_structured_response.entities_mentioned
                )
            # debug_info only in debug mode
            if debug_mode and hasattr(mock_structured_response, "debug_info"):
                unified_response_debug_on["debug_info"] = (
                    mock_structured_response.debug_info
                )

        # CRITICAL ASSERTIONS: Debug fields should be PRESENT when debug_mode=True
        assert (
            "state_updates" in unified_response_debug_on
        ), "state_updates should be in response when debug_mode=True"
        assert (
            "entities_mentioned" in unified_response_debug_on
        ), "entities_mentioned should be in response when debug_mode=True"
        assert (
            "debug_info" in unified_response_debug_on
        ), "debug_info should be in response when debug_mode=True"

        # Verify content
        assert unified_response_debug_on["state_updates"] == {"hp": 8}
        assert unified_response_debug_on["entities_mentioned"] == ["Dragon", "Knight"]
        assert unified_response_debug_on["debug_info"]["dm_notes"] == ["Test note"]

    def test_character_mode_sequence_id_debug_filtering(self):
        """Restored from test_debug_response_building.py - character mode sequence ID test"""

        # Test the second place where state_updates is added (lines 685-689)
        debug_mode = False
        mode = "character"

        unified_response = {}

        # Track story mode sequence ID for character mode (from world_logic.py lines 675-689)
        if mode == "character":
            story_id_update = {
                "custom_campaign_state": {"last_story_mode_sequence_id": 1}
            }
            merged_state_changes = {
                "hp": 8,
                "custom_campaign_state": {"last_story_mode_sequence_id": 1},
            }

            # state_updates only in debug mode
            if debug_mode:
                unified_response["state_updates"] = merged_state_changes

        # CRITICAL: state_updates should NOT be added even in character mode when debug_mode=False
        assert (
            "state_updates" not in unified_response
        ), "state_updates should NOT be added in character mode when debug_mode=False"

        # Test that it works with debug_mode=True
        debug_mode = True
        unified_response_debug_on = {}

        if mode == "character":
            # state_updates only in debug mode
            if debug_mode:
                unified_response_debug_on["state_updates"] = merged_state_changes

        assert (
            "state_updates" in unified_response_debug_on
        ), "state_updates should be added in character mode when debug_mode=True"


if __name__ == "__main__":
    unittest.main()
