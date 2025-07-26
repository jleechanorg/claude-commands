"""
Unit tests for refactored helper classes and methods.
Tests PromptBuilder, StateHelper, and MissionHandler classes.
"""

import os
import sys
import unittest
from unittest.mock import patch

from main import _cleanup_legacy_state, apply_automatic_combat_cleanup

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gemini_response import GeminiResponse

from gemini_service import PromptBuilder, _build_debug_instructions


# Create StateHelper wrapper for test compatibility
class StateHelper:
    """Test wrapper for state helper functions."""

    @staticmethod
    def strip_debug_content(text):
        """Strip debug content from text."""
        return GeminiResponse._strip_debug_content(text)

    @staticmethod
    def strip_state_updates_only(text):
        """Strip only state updates from text."""
        return GeminiResponse._strip_state_updates_only(text)

    @staticmethod
    def apply_automatic_combat_cleanup(state_dict, changes_dict):
        """Delegate to main.apply_automatic_combat_cleanup."""

        return apply_automatic_combat_cleanup(state_dict, changes_dict)

    @staticmethod
    def cleanup_legacy_state(state_dict):
        """Delegate to main._cleanup_legacy_state."""

        return _cleanup_legacy_state(state_dict)


from firestore_service import MissionHandler


class TestPromptBuilder(unittest.TestCase):
    """Test the PromptBuilder class."""

    def setUp(self):
        self.builder = PromptBuilder()

    @patch("gemini_service._load_instruction_file")
    def test_build_core_system_instructions(self, mock_load):
        """Test building core system instructions."""
        mock_load.return_value = "instruction content"

        parts = self.builder.build_core_system_instructions()

        self.assertEqual(
            len(parts), 3
        )  # Master directive + game state + debug instructions
        self.assertEqual(
            mock_load.call_count, 2
        )  # Only 2 calls to _load_instruction_file (master directive + game state)
        # First two parts are loaded instructions, last is debug instructions
        self.assertTrue(all(part == "instruction content" for part in parts[:2]))
        self.assertIn("DEBUG MODE", parts[2])  # Debug instructions are at index 2

    @patch("gemini_service._load_instruction_file")
    def test_add_character_instructions(self, mock_load):
        """Test adding character instructions based on selected prompts."""
        mock_load.return_value = "character instruction"
        parts = []

        # Test with narrative prompt - should add character template
        self.builder.add_character_instructions(parts, ["narrative"])
        self.assertEqual(len(parts), 1)

        # Test with mechanics prompt - should NOT add character template (only narrative triggers it)
        parts = []
        self.builder.add_character_instructions(parts, ["mechanics"])
        self.assertEqual(
            len(parts), 0
        )  # mechanics doesn't trigger character instructions

        # Test with both - should add 1 (only narrative triggers character instructions)
        parts = []
        self.builder.add_character_instructions(parts, ["narrative", "mechanics"])
        self.assertEqual(
            len(parts), 1
        )  # still only 1 since character template is only added for narrative

    def test_build_companion_instruction(self):
        """Test companion instruction generation."""
        instruction = self.builder.build_companion_instruction()
        self.assertIn("COMPANION GENERATION ACTIVATED", instruction)
        self.assertIn("3 starting companions", instruction)

    def test_build_background_summary_instruction(self):
        """Test background summary instruction generation."""
        instruction = self.builder.build_background_summary_instruction()
        self.assertIn("BACKGROUND SUMMARY", instruction)
        self.assertIn("World Background", instruction)
        self.assertIn("Character History", instruction)

    @patch("gemini_service._add_world_instructions_to_system")
    def test_finalize_instructions(self, mock_add_world):
        """Test finalizing instructions with world and debug content."""
        parts = ["part1", "part2"]

        # Test without world instructions
        result = self.builder.finalize_instructions(parts, use_default_world=False)
        self.assertIn("part1", result)
        self.assertIn("part2", result)
        # Debug instructions are now added in build_core_system_instructions, not finalize
        # So we shouldn't expect it here
        mock_add_world.assert_not_called()

        # Test with world instructions
        self.builder.finalize_instructions(parts, use_default_world=True)
        mock_add_world.assert_called_once()


class TestStateHelper(unittest.TestCase):
    """Test the StateHelper class."""

    def test_strip_debug_content(self):
        """Test stripping debug content from text."""
        text = "Normal text [DEBUG_START]Debug info[DEBUG_END] more text"
        result = StateHelper.strip_debug_content(text)
        self.assertNotIn("[DEBUG_START]", result)
        self.assertNotIn("Debug info", result)
        self.assertIn("Normal text", result)
        self.assertIn("more text", result)

    @patch("main.apply_automatic_combat_cleanup")
    def test_apply_automatic_combat_cleanup(self, mock_cleanup):
        """Test combat cleanup delegation."""
        mock_cleanup.return_value = {"cleaned": True}

        result = StateHelper.apply_automatic_combat_cleanup({}, {})
        self.assertEqual(result, {"cleaned": True})
        mock_cleanup.assert_called_once()

    @patch("main._cleanup_legacy_state")
    def test_cleanup_legacy_state(self, mock_cleanup):
        """Test legacy state cleanup delegation."""
        mock_cleanup.return_value = ({"cleaned": True}, True, 5)

        result = StateHelper.cleanup_legacy_state({})
        self.assertEqual(result, ({"cleaned": True}, True, 5))
        mock_cleanup.assert_called_once()


class TestMissionHandler(unittest.TestCase):
    """Test the MissionHandler class."""

    def test_initialize_missions_list(self):
        """Test initializing missions list."""
        state = {}
        MissionHandler.initialize_missions_list(state, "active_missions")
        self.assertEqual(state["active_missions"], [])

        # Test with existing non-list value
        state = {"active_missions": "not a list"}
        MissionHandler.initialize_missions_list(state, "active_missions")
        self.assertEqual(state["active_missions"], [])

    def test_find_existing_mission_index(self):
        """Test finding mission by ID."""
        missions = [
            {"mission_id": "quest1", "name": "First Quest"},
            {"mission_id": "quest2", "name": "Second Quest"},
        ]

        # Test finding existing mission
        index = MissionHandler.find_existing_mission_index(missions, "quest2")
        self.assertEqual(index, 1)

        # Test not finding mission
        index = MissionHandler.find_existing_mission_index(missions, "quest3")
        self.assertEqual(index, -1)

    def test_process_mission_data(self):
        """Test processing individual mission data."""
        state = {"active_missions": []}

        # Test adding new mission
        MissionHandler.process_mission_data(
            state, "active_missions", "quest1", {"name": "New Quest"}
        )
        self.assertEqual(len(state["active_missions"]), 1)
        self.assertEqual(state["active_missions"][0]["mission_id"], "quest1")

        # Test updating existing mission
        MissionHandler.process_mission_data(
            state, "active_missions", "quest1", {"status": "completed"}
        )
        self.assertEqual(len(state["active_missions"]), 1)
        self.assertEqual(state["active_missions"][0]["status"], "completed")

    def test_handle_missions_dict_conversion(self):
        """Test converting dict format to list format."""
        state = {"active_missions": []}
        missions_dict = {
            "quest1": {"name": "First Quest"},
            "quest2": {"name": "Second Quest"},
        }

        MissionHandler.handle_missions_dict_conversion(
            state, "active_missions", missions_dict
        )
        self.assertEqual(len(state["active_missions"]), 2)
        self.assertTrue(
            any(m["mission_id"] == "quest1" for m in state["active_missions"])
        )
        self.assertTrue(
            any(m["mission_id"] == "quest2" for m in state["active_missions"])
        )

    @patch("firestore_service.logging")
    def test_handle_active_missions_conversion(self, mock_logging):
        """Test smart conversion of active missions."""
        state = {}

        # Test with dict value
        missions_dict = {"quest1": {"name": "Quest"}}
        MissionHandler.handle_active_missions_conversion(
            state, "active_missions", missions_dict
        )
        self.assertEqual(len(state["active_missions"]), 1)

        # Test with invalid value
        state = {}
        MissionHandler.handle_active_missions_conversion(
            state, "active_missions", "invalid"
        )
        self.assertEqual(state["active_missions"], [])
        mock_logging.error.assert_called()


class TestDebugInstructions(unittest.TestCase):
    """Test the debug instructions helper."""

    def test_build_debug_instructions(self):
        """Test debug instructions contain all required sections."""
        instructions = _build_debug_instructions()

        # Check for all required sections
        self.assertIn("DEBUG MODE - ALWAYS GENERATE", instructions)
        self.assertIn("DM COMMENTARY", instructions)
        self.assertIn("DICE ROLLS", instructions)
        self.assertIn("RESOURCES USED", instructions)
        self.assertIn("STATE CHANGES", instructions)
        self.assertIn("[DEBUG_START]", instructions)
        self.assertIn("[DEBUG_ROLL_START]", instructions)
        self.assertIn("[DEBUG_RESOURCES_START]", instructions)
        self.assertIn("[DEBUG_STATE_START]", instructions)


if __name__ == "__main__":
    unittest.main()
