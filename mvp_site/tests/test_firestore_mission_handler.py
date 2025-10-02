#!/usr/bin/env python3
"""
Phase 4: MissionHandler tests for firestore_service.py
Target coverage: 61% → 70%
Focus: MissionHandler class static methods
"""

import os

# Add parent directory to path
import sys
import unittest
from unittest.mock import patch

# Set test environment before any imports
os.environ["TESTING"] = "true"
os.environ["USE_MOCKS"] = "true"

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

# Mock Firebase before importing firestore_service
with patch("firestore_service.get_db"):
    from mvp_site.firestore_service import MissionHandler


class TestMissionHandler(unittest.TestCase):
    """Test MissionHandler static methods"""

    def test_initialize_missions_list_missing_key(self):
        """Test initialize_missions_list when key doesn't exist"""
        state = {"other_key": "value"}
        MissionHandler.initialize_missions_list(state, "active_missions")

        assert "active_missions" in state
        assert state["active_missions"] == []

    def test_initialize_missions_list_non_list_value(self):
        """Test initialize_missions_list when key exists but isn't a list"""
        state = {"active_missions": "not a list"}
        MissionHandler.initialize_missions_list(state, "active_missions")

        assert state["active_missions"] == []

    def test_initialize_missions_list_already_list(self):
        """Test initialize_missions_list when key already has a list"""
        existing_missions = [{"mission_id": "quest1"}]
        state = {"active_missions": existing_missions}
        MissionHandler.initialize_missions_list(state, "active_missions")

        # Should not modify existing list
        assert state["active_missions"] == existing_missions

    def test_initialize_missions_list_none_value(self):
        """Test initialize_missions_list when key has None value"""
        state = {"active_missions": None}
        MissionHandler.initialize_missions_list(state, "active_missions")

        assert state["active_missions"] == []

    def test_find_existing_mission_index_found(self):
        """Test find_existing_mission_index when mission exists"""
        missions = [
            {"mission_id": "quest1", "name": "First Quest"},
            {"mission_id": "quest2", "name": "Second Quest"},
            {"mission_id": "quest3", "name": "Third Quest"},
        ]

        index = MissionHandler.find_existing_mission_index(missions, "quest2")
        assert index == 1

    def test_find_existing_mission_index_not_found(self):
        """Test find_existing_mission_index when mission doesn't exist"""
        missions = [
            {"mission_id": "quest1", "name": "First Quest"},
            {"mission_id": "quest2", "name": "Second Quest"},
        ]

        index = MissionHandler.find_existing_mission_index(missions, "quest99")
        assert index == -1

    def test_find_existing_mission_index_empty_list(self):
        """Test find_existing_mission_index with empty list"""
        missions = []

        index = MissionHandler.find_existing_mission_index(missions, "quest1")
        assert index == -1

    def test_find_existing_mission_index_invalid_mission_objects(self):
        """Test find_existing_mission_index with non-dict items in list"""
        missions = [
            {"mission_id": "quest1", "name": "First Quest"},
            "not a dict",  # Invalid item
            None,  # Invalid item
            {"mission_id": "quest2", "name": "Second Quest"},
        ]

        # Should still find valid missions
        index = MissionHandler.find_existing_mission_index(missions, "quest2")
        assert index == 3

        # Invalid items are skipped
        index = MissionHandler.find_existing_mission_index(missions, "not a dict")
        assert index == -1

    def test_find_existing_mission_index_missing_mission_id(self):
        """Test find_existing_mission_index when dicts lack mission_id"""
        missions = [
            {"name": "Quest without ID"},  # Missing mission_id
            {"mission_id": "quest2", "name": "Second Quest"},
        ]

        index = MissionHandler.find_existing_mission_index(missions, "quest2")
        assert index == 1

    @patch("logging_util.info")
    def test_process_mission_data_new_mission(self, mock_log):
        """Test process_mission_data adding a new mission"""
        state = {"active_missions": []}
        mission_data = {"name": "Save the Princess", "reward": 100}

        MissionHandler.process_mission_data(
            state, "active_missions", "quest1", mission_data
        )

        # Mission should be added
        assert len(state["active_missions"]) == 1
        assert state["active_missions"][0]["mission_id"] == "quest1"
        assert state["active_missions"][0]["name"] == "Save the Princess"
        assert state["active_missions"][0]["reward"] == 100

        # Should log the addition
        mock_log.assert_called_with("Adding new mission: quest1")

    @patch("logging_util.info")
    def test_process_mission_data_update_existing(self, mock_log):
        """Test process_mission_data updating an existing mission"""
        state = {
            "active_missions": [
                {"mission_id": "quest1", "name": "Old Name", "status": "active"}
            ]
        }
        mission_data = {"name": "New Name", "progress": 50}

        MissionHandler.process_mission_data(
            state, "active_missions", "quest1", mission_data
        )

        # Mission should be updated
        assert len(state["active_missions"]) == 1
        assert state["active_missions"][0]["mission_id"] == "quest1"
        assert state["active_missions"][0]["name"] == "New Name"
        assert state["active_missions"][0]["status"] == "active"  # Kept
        assert state["active_missions"][0]["progress"] == 50  # Added

        # Should log the update
        mock_log.assert_called_with("Updating existing mission: quest1")

    @patch("logging_util.info")
    def test_process_mission_data_adds_missing_id(self, mock_log):
        """Test process_mission_data adds mission_id if missing"""
        state = {"active_missions": []}
        mission_data = {"name": "Quest without ID"}  # No mission_id

        MissionHandler.process_mission_data(
            state, "active_missions", "quest1", mission_data
        )

        # Should add mission_id
        assert state["active_missions"][0]["mission_id"] == "quest1"

    @patch("logging_util.warning")
    def test_handle_missions_dict_conversion(self, mock_warning):
        """Test handle_missions_dict_conversion with dict of missions"""
        state = {"active_missions": []}
        missions_dict = {
            "quest1": {"name": "First Quest", "level": 1},
            "quest2": {"name": "Second Quest", "level": 2},
            "invalid": "not a dict",  # Invalid mission data
        }

        MissionHandler.handle_missions_dict_conversion(
            state, "active_missions", missions_dict
        )

        # Valid missions should be added
        assert len(state["active_missions"]) == 2
        assert state["active_missions"][0]["mission_id"] == "quest1"
        assert state["active_missions"][1]["mission_id"] == "quest2"

        # Should warn about invalid data
        mock_warning.assert_called_once_with(
            "Skipping invalid mission data for invalid: not a dictionary"
        )

    @patch("logging_util.warning")
    @patch("logging_util.error")
    def test_handle_active_missions_conversion_dict(self, mock_error, mock_warning):
        """Test handle_active_missions_conversion with dict value"""
        state = {}
        value = {
            "main_quest": {"name": "Main Quest", "priority": "high"},
            "side_quest": {"name": "Side Quest", "priority": "low"},
        }

        MissionHandler.handle_active_missions_conversion(
            state, "active_missions", value
        )

        # Should convert dict to list
        assert "active_missions" in state
        assert len(state["active_missions"]) == 2
        assert state["active_missions"][0]["mission_id"] == "main_quest"
        assert state["active_missions"][1]["mission_id"] == "side_quest"

        # Should log conversion warning
        mock_warning.assert_called()
        assert "SMART CONVERSION" in mock_warning.call_args[0][0]

        # Should not log error for dict type
        mock_error.assert_not_called()

    @patch("logging_util.warning")
    @patch("logging_util.error")
    def test_handle_active_missions_conversion_invalid_type(
        self, mock_error, mock_warning
    ):
        """Test handle_active_missions_conversion with non-dict, non-list value"""
        state = {}
        value = "invalid string value"

        MissionHandler.handle_active_missions_conversion(
            state, "active_missions", value
        )

        # Should create empty list
        assert state["active_missions"] == []

        # Should log conversion warning and error
        mock_warning.assert_called()
        mock_error.assert_called_with("Cannot convert str to mission list. Skipping.")

    def test_handle_missions_dict_conversion_empty(self):
        """Test handle_missions_dict_conversion with empty dict"""
        state = {"active_missions": [{"mission_id": "existing", "name": "Existing"}]}

        MissionHandler.handle_missions_dict_conversion(state, "active_missions", {})

        # Should not modify existing missions
        assert len(state["active_missions"]) == 1
        assert state["active_missions"][0]["mission_id"] == "existing"

    @patch("logging_util.warning")
    def test_handle_missions_dict_conversion_mixed_types(self, mock_warning):
        """Test handle_missions_dict_conversion with various invalid types"""
        state = {"active_missions": []}
        missions_dict = {
            "valid": {"name": "Valid Mission"},
            "none_value": None,
            "list_value": ["not", "a", "dict"],
            "int_value": 42,
            "bool_value": True,
        }

        MissionHandler.handle_missions_dict_conversion(
            state, "active_missions", missions_dict
        )

        # Only valid mission should be added
        assert len(state["active_missions"]) == 1
        assert state["active_missions"][0]["mission_id"] == "valid"

        # Should warn about each invalid type
        assert mock_warning.call_count == 4  # 4 invalid types


if __name__ == "__main__":
    unittest.main(verbosity=2)
