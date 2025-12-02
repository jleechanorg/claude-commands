"""
Regression test for integer conversion bug in PromptBuilder.build_continuation_reminder()

Bug: LLM can return string time values like "15" instead of integers like 15.
Using :02d format specifier without int() conversion causes ValueError.

Related cursor[bot] comment: PR #2235
"""
import unittest
from unittest.mock import MagicMock
from mvp_site.llm_service import PromptBuilder
from mvp_site.game_state import GameState


class TestStringTimeFormattingRegression(unittest.TestCase):
    """Test that string time values from LLM don't crash time formatting"""

    def setUp(self):
        """Set up test PromptBuilder instance"""
        self.prompt_builder = PromptBuilder()

    def test_string_time_values_should_not_crash(self):
        """
        🔴 RED TEST - This should FAIL initially

        Reproduces bug where LLM returns string time values like "15"
        instead of integers, causing ValueError with :02d format.
        """
        # Create GameState with STRING time values (bug scenario)
        game_state = GameState(world_data={
            "world_time": {
                "hour": "15",      # STRING not int - will crash with :02d
                "minute": "30",    # STRING not int - will crash with :02d
                "second": "45"     # STRING not int - will crash with :02d
            },
            "current_location_name": "Test Location"
        })

        # Attach game state to prompt builder
        self.prompt_builder.game_state = game_state

        # This should NOT crash - should handle strings gracefully
        try:
            result = self.prompt_builder.build_continuation_reminder()

            # Verify time is properly formatted in result
            self.assertIn("15:30:45", result,
                         "Time should be formatted correctly even with string inputs")

        except ValueError as e:
            self.fail(f"build_continuation_reminder() crashed with string time values: {e}")

    def test_integer_time_values_work_correctly(self):
        """Control test - integer values should always work"""
        game_state = GameState(world_data={
            "world_time": {
                "hour": 15,        # INTEGER - should work
                "minute": 30,      # INTEGER - should work
                "second": 45       # INTEGER - should work
            },
            "current_location_name": "Test Location"
        })

        self.prompt_builder.game_state = game_state

        # This should work fine with integer values
        result = self.prompt_builder.build_continuation_reminder()
        self.assertIn("15:30:45", result)

    def test_mixed_string_and_integer_values(self):
        """Edge case - mixed types should be handled gracefully"""
        game_state = GameState(world_data={
            "world_time": {
                "hour": "12",      # STRING
                "minute": 30,      # INTEGER
                "second": "00"     # STRING
            },
            "current_location_name": "Test Location"
        })

        self.prompt_builder.game_state = game_state

        try:
            result = self.prompt_builder.build_continuation_reminder()
            self.assertIn("12:30:00", result)
        except ValueError as e:
            self.fail(f"Mixed string/int values crashed: {e}")


if __name__ == "__main__":
    unittest.main()
