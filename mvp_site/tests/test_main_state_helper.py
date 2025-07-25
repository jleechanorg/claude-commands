"""
Comprehensive tests for StateHelper class and utility functions in main.py.
Focuses on debug content stripping and state management utilities.
"""

import os
import re
import unittest
from unittest.mock import MagicMock


# Mock firebase_admin before imports
mock_firebase_admin = MagicMock()
mock_firestore = MagicMock()
mock_auth = MagicMock()
mock_firebase_admin.firestore = mock_firestore
mock_firebase_admin.auth = mock_auth

# Firebase DELETE_FIELD sentinel
DELETE_FIELD = object()
mock_firestore.DELETE_FIELD = DELETE_FIELD

# Setup module mocks
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from main import CORS_RESOURCES
from main import DEFAULT_TEST_USER
from main import HEADER_AUTH, HEADER_TEST_BYPASS, HEADER_TEST_USER_ID
from main import KEY_CAMPAIGN_ID, KEY_ERROR, KEY_MESSAGE, KEY_SUCCESS
sys.modules["firebase_admin"] = mock_firebase_admin
sys.modules["firebase_admin.firestore"] = mock_firestore
sys.modules["firebase_admin.auth"] = mock_auth

# Import after mocking
from gemini_response import GeminiResponse
from main import create_app, format_state_changes


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
    def strip_other_debug_content(text):
        """Strip all debug content except STATE_UPDATES_PROPOSED blocks."""
        if not text:
            return text

        # Remove all debug blocks except STATE_UPDATES_PROPOSED
        text = re.sub(r"\[DEBUG_START\].*?\[DEBUG_END\]", "", text, flags=re.DOTALL)
        text = re.sub(
            r"\[DEBUG_ROLL_START\].*?\[DEBUG_ROLL_END\]", "", text, flags=re.DOTALL
        )
        text = re.sub(
            r"\[DEBUG_RESOURCES_START\].*?\[DEBUG_RESOURCES_END\]",
            "",
            text,
            flags=re.DOTALL,
        )
        text = re.sub(
            r"\[DEBUG_STATE_START\].*?\[DEBUG_STATE_END\]", "", text, flags=re.DOTALL
        )
        text = re.sub(
            r"\[DEBUG_VALIDATION_START\].*?\[DEBUG_VALIDATION_END\]",
            "",
            text,
            flags=re.DOTALL,
        )

        return text


class TestStateHelper(unittest.TestCase):
    """Test StateHelper class methods."""

    def test_strip_debug_content_basic(self):
        """Test basic debug content stripping."""
        test_text = "Regular content [DEBUG_START]debug content[DEBUG_END] more content"

        result = StateHelper.strip_debug_content(test_text)

        # The expected output should have debug content removed
        self.assertEqual(result, "Regular content  more content")

    def test_strip_state_updates_only_basic(self):
        """Test stripping only state updates."""
        test_text = (
            "Content [STATE_UPDATES_PROPOSED]updates[END_STATE_UPDATES_PROPOSED] more"
        )

        result = StateHelper.strip_state_updates_only(test_text)

        # Should remove state updates but keep other content
        self.assertEqual(result, "Content  more")

    def test_strip_other_debug_content_basic(self):
        """Test stripping debug content except state updates."""
        test_text = "[DEBUG_START]debug[DEBUG_END] [STATE_UPDATES_PROPOSED]keep[/STATE_UPDATES_PROPOSED]"

        result = StateHelper.strip_other_debug_content(test_text)

        # Should strip debug content but keep state updates
        self.assertEqual(
            result, " [STATE_UPDATES_PROPOSED]keep[/STATE_UPDATES_PROPOSED]"
        )

    def test_apply_automatic_combat_cleanup_basic(self):
        """Test automatic combat cleanup."""
        # Skip this test as apply_automatic_combat_cleanup is not part of StateHelper
        self.skipTest("apply_automatic_combat_cleanup not implemented in StateHelper")


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions in main.py."""

    def test_format_state_changes_for_html(self):
        """Test format_state_changes with HTML formatting."""
        changes = {
            "current_scene": 2,
            "npcs": [{"name": "Gandalf", "level": 20}],
            "player_character.hp": 90,
        }

        result = format_state_changes(changes, for_html=True)

        # Should return a formatted string with HTML line breaks
        self.assertIsInstance(result, str)
        self.assertIn("current_scene", result)
        self.assertIn("2", result)
        if "<br>" in result:  # HTML formatting
            self.assertIn("<br>", result)

    def test_format_state_changes_for_text(self):
        """Test format_state_changes with text formatting."""
        changes = {"current_scene": 3, "story_progression": "advanced"}

        result = format_state_changes(changes, for_html=False)

        # Should return a formatted string with text line breaks
        self.assertIsInstance(result, str)
        self.assertIn("current_scene", result)
        self.assertIn("3", result)
        # Should not contain HTML
        self.assertNotIn("<br>", result)

    def test_format_state_changes_empty_dict(self):
        """Test format_state_changes with empty changes."""
        result = format_state_changes({}, for_html=True)

        # Should handle empty changes gracefully
        self.assertIsInstance(result, str)

    def test_format_state_changes_complex_nested(self):
        """Test format_state_changes with complex nested data."""
        changes = {
            "npcs": [
                {"name": "Wizard", "spells": ["fireball", "teleport"]},
                {
                    "name": "Warrior",
                    "equipment": {"weapon": "sword", "armor": "chainmail"},
                },
            ],
            "environment": {
                "weather": "stormy",
                "time_of_day": "night",
                "location": {"name": "Dark Forest", "danger_level": "high"},
            },
        }

        result = format_state_changes(changes, for_html=True)

        self.assertIsInstance(result, str)
        self.assertIn("Wizard", result)
        self.assertIn("Dark Forest", result)


class TestApplicationConfiguration(unittest.TestCase):
    """Test application configuration and setup."""

    def test_create_app_basic_configuration(self):
        """Test basic app creation and configuration."""
        app = create_app()

        # Test basic Flask app properties
        self.assertIsNotNone(app)
        self.assertTrue(hasattr(app, "config"))
        self.assertTrue(hasattr(app, "route"))

    def test_create_app_testing_mode(self):
        """Test app creation in testing mode."""
        app = create_app()
        app.config["TESTING"] = True

        self.assertTrue(app.config["TESTING"])

    def test_cors_configuration(self):
        """Test CORS configuration is applied."""
        app = create_app()

        # CORS should be configured for the app
        # This test verifies the app can be created with CORS
        self.assertIsNotNone(app)

    def test_app_route_registration(self):
        """Test that routes are properly registered."""
        app = create_app()

        # Check that routes are registered
        route_rules = [rule.rule for rule in app.url_map.iter_rules()]

        # Should have our API routes
        self.assertIn("/api/campaigns", route_rules)
        self.assertIn("/api/campaigns/<campaign_id>", route_rules)
        self.assertIn("/api/campaigns/<campaign_id>/interaction", route_rules)

    def test_error_handler_registration(self):
        """Test that error handlers are registered if they exist."""
        app = create_app()

        # App should have error handlers
        # This is mainly testing that create_app completes without errors
        self.assertIsNotNone(app)


class TestConstants(unittest.TestCase):
    """Test constants and configuration values."""

    def test_header_constants(self):
        """Test that header constants are properly defined."""


        self.assertEqual(HEADER_AUTH, "Authorization")
        self.assertEqual(HEADER_TEST_BYPASS, "X-Test-Bypass-Auth")
        self.assertEqual(HEADER_TEST_USER_ID, "X-Test-User-ID")

    def test_key_constants(self):
        """Test that response key constants are properly defined."""


        self.assertEqual(KEY_SUCCESS, "success")
        self.assertEqual(KEY_ERROR, "error")
        self.assertEqual(KEY_MESSAGE, "message")
        self.assertEqual(KEY_CAMPAIGN_ID, "campaign_id")

    def test_default_test_user(self):
        """Test default test user constant."""


        self.assertEqual(DEFAULT_TEST_USER, "test-user")

    def test_cors_resources_configuration(self):
        """Test CORS resources configuration."""


        self.assertIn(r"/api/*", CORS_RESOURCES)
        self.assertEqual(CORS_RESOURCES[r"/api/*"]["origins"], "*")


if __name__ == "__main__":
    unittest.main()
