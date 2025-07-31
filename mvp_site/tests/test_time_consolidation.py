"""
Unit tests for time consolidation functionality in GameState.
Tests the migration of separate time_of_day fields into unified world_time objects.
"""

import os
import sys
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from game_state import GameState


class TestTimeConsolidation(unittest.TestCase):
    """Test cases for time tracking consolidation."""

    def test_legacy_time_migration(self):
        """Test migration of legacy separate time_of_day field."""
        # Create state with old format
        legacy_state = GameState(
            world_data={
                "current_location": "Tavern",
                "world_time": {"hour": 18, "minute": 30, "second": 0},
                "time_of_day": "Evening",  # Old separate field
            }
        )

        # Verify consolidation
        assert "time_of_day" not in legacy_state.world_data
        assert "world_time" in legacy_state.world_data
        assert legacy_state.world_data["world_time"]["time_of_day"] == "Evening"

    def test_time_of_day_calculation(self):
        """Test automatic calculation of time_of_day from hour."""
        # Create state without time_of_day
        state = GameState(
            world_data={
                "current_location": "Forest",
                "world_time": {"hour": 6, "minute": 0, "second": 0},
            }
        )

        # Verify calculation
        assert state.world_data["world_time"]["time_of_day"] == "Dawn"

    def test_already_consolidated_data(self):
        """Test that already consolidated data is not modified."""
        # Create state with modern format
        modern_state = GameState(
            world_data={
                "current_location": "Castle",
                "world_time": {
                    "hour": 12,
                    "minute": 0,
                    "second": 0,
                    "time_of_day": "Midday",
                },
            }
        )

        # Verify unchanged
        assert modern_state.world_data["world_time"]["time_of_day"] == "Midday"

    def test_hour_to_time_of_day_mappings(self):
        """Test all hour-to-description mappings."""
        test_cases = [
            (0, "Deep Night"),
            (3, "Deep Night"),
            (4, "Deep Night"),
            (5, "Dawn"),
            (6, "Dawn"),
            (7, "Morning"),
            (11, "Morning"),
            (12, "Midday"),
            (13, "Midday"),
            (14, "Afternoon"),
            (17, "Afternoon"),
            (18, "Evening"),
            (19, "Evening"),
            (20, "Night"),
            (23, "Night"),
        ]

        for hour, expected in test_cases:
            with self.subTest(hour=hour):
                state = GameState(
                    world_data={"world_time": {"hour": hour, "minute": 0, "second": 0}}
                )
                assert (
                    state.world_data["world_time"]["time_of_day"] == expected
                ), f"Hour {hour} should map to '{expected}'"

    def test_missing_world_data(self):
        """Test handling of missing world_data."""
        # Empty state
        empty_state = GameState()
        # Should not raise error
        assert isinstance(empty_state, GameState)

        # State without world_data
        no_world_state = GameState(player_character_data={"name": "Test"})
        # Should not raise error
        assert isinstance(no_world_state, GameState)

    def test_no_time_data_unchanged(self):
        """Test that world_data without any time fields remains unchanged."""
        state = GameState(world_data={"current_location": "Town Square"})

        # Should NOT create world_time when no time data exists
        assert "world_time" not in state.world_data
        # Should only have the original data
        assert state.world_data == {"current_location": "Town Square"}

    def test_invalid_world_time_format(self):
        """Test handling of invalid world_time format."""
        # world_time as non-dict should be replaced
        state = GameState(
            world_data={"world_time": "invalid", "time_of_day": "Evening"}
        )

        # Should convert to proper dict
        assert isinstance(state.world_data["world_time"], dict)
        assert state.world_data["world_time"]["time_of_day"] == "Evening"

    def test_edge_case_hours(self):
        """Test edge cases for hour values."""
        # Test boundary hours
        edge_cases = [
            (0, "Deep Night"),  # Midnight
            (5, "Dawn"),  # Dawn boundary
            (7, "Morning"),  # Morning boundary
            (12, "Midday"),  # Noon
            (14, "Afternoon"),  # Afternoon boundary
            (18, "Evening"),  # Evening boundary
            (20, "Night"),  # Night boundary
            (23, "Night"),  # Last hour
        ]

        for hour, expected in edge_cases:
            with self.subTest(hour=hour):
                state = GameState(
                    world_data={
                        "world_time": {"hour": hour, "minute": 59, "second": 59}
                    }
                )
                assert state.world_data["world_time"]["time_of_day"] == expected

    def test_time_of_day_without_world_time(self):
        """Test migration of time_of_day when world_time doesn't exist."""
        state = GameState(
            world_data={
                "current_location": "Market",
                "time_of_day": "Morning",  # Only time_of_day, no world_time
            }
        )

        # Should create world_time with estimated hour
        assert "world_time" in state.world_data
        assert "time_of_day" not in state.world_data
        assert state.world_data["world_time"]["time_of_day"] == "Morning"
        assert state.world_data["world_time"]["hour"] == 9  # Estimated hour for morning
        assert state.world_data["world_time"]["minute"] == 0
        assert state.world_data["world_time"]["second"] == 0


if __name__ == "__main__":
    unittest.main()
