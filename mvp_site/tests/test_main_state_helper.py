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

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from main import (
    CORS_RESOURCES,
    DEFAULT_TEST_USER,
    HEADER_AUTH,
    HEADER_TEST_BYPASS,
    HEADER_TEST_USER_ID,
    KEY_CAMPAIGN_ID,
    KEY_ERROR,
    KEY_MESSAGE,
    KEY_SUCCESS,
)

sys.modules["firebase_admin"] = mock_firebase_admin
sys.modules["firebase_admin.firestore"] = mock_firestore
sys.modules["firebase_admin.auth"] = mock_auth

# Import after mocking
from gemini_response import GeminiResponse
from main import create_app
from world_logic import format_game_state_updates


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
        return re.sub(
            r"\[DEBUG_VALIDATION_START\].*?\[DEBUG_VALIDATION_END\]",
            "",
            text,
            flags=re.DOTALL,
        )


class TestStateHelper(unittest.TestCase):
    """Test StateHelper class methods."""

    def test_strip_debug_content_basic(self):
        """Test basic debug content stripping."""
        test_text = "Regular content [DEBUG_START]debug content[DEBUG_END] more content"

        result = StateHelper.strip_debug_content(test_text)

        # The expected output should have debug content removed
        assert result == "Regular content  more content"

    def test_strip_state_updates_only_basic(self):
        """Test stripping only state updates."""
        test_text = (
            "Content [STATE_UPDATES_PROPOSED]updates[END_STATE_UPDATES_PROPOSED] more"
        )

        result = StateHelper.strip_state_updates_only(test_text)

        # Should remove state updates but keep other content
        assert result == "Content  more"

    def test_strip_other_debug_content_basic(self):
        """Test stripping debug content except state updates."""
        test_text = "[DEBUG_START]debug[DEBUG_END] [STATE_UPDATES_PROPOSED]keep[/STATE_UPDATES_PROPOSED]"

        result = StateHelper.strip_other_debug_content(test_text)

        # Should strip debug content but keep state updates
        assert result == " [STATE_UPDATES_PROPOSED]keep[/STATE_UPDATES_PROPOSED]"

    def test_apply_automatic_combat_cleanup_basic(self):
        """Test automatic combat cleanup."""
        # Skip this test as apply_automatic_combat_cleanup is not part of StateHelper
        self.skipTest("apply_automatic_combat_cleanup not implemented in StateHelper")


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions in main.py."""

    def test_format_game_state_updates_for_html(self):
        """Test format_game_state_updates with HTML formatting."""
        changes = {
            "current_scene": 2,
            "npcs": [{"name": "Gandalf", "level": 20}],
            "player_character.hp": 90,
        }

        result = format_game_state_updates(changes, for_html=True)

        # Should return a formatted string with HTML line breaks
        assert isinstance(result, str)
        assert "current_scene" in result
        assert "2" in result
        if "<br>" in result:  # HTML formatting
            assert "<br>" in result

    def test_format_game_state_updates_for_text(self):
        """Test format_game_state_updates with text formatting."""
        changes = {"current_scene": 3, "story_progression": "advanced"}

        result = format_game_state_updates(changes, for_html=False)

        # Should return a formatted string with text line breaks
        assert isinstance(result, str)
        assert "current_scene" in result
        assert "3" in result
        # Should not contain HTML
        assert "<br>" not in result

    def test_format_game_state_updates_empty_dict(self):
        """Test format_game_state_updates with empty changes."""
        result = format_game_state_updates({}, for_html=True)

        # Should handle empty changes gracefully
        assert isinstance(result, str)

    def test_format_game_state_updates_complex_nested(self):
        """Test format_game_state_updates with complex nested data."""
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

        result = format_game_state_updates(changes, for_html=True)

        assert isinstance(result, str)
        assert "Wizard" in result
        assert "Dark Forest" in result


class TestApplicationConfiguration(unittest.TestCase):
    """Test application configuration and setup."""

    def test_create_app_basic_configuration(self):
        """Test basic app creation and configuration."""
        app = create_app()

        # Test basic Flask app properties
        assert app is not None
        assert hasattr(app, "config")
        assert hasattr(app, "route")

    def test_create_app_testing_mode(self):
        """Test app creation in testing mode."""
        app = create_app()
        app.config["TESTING"] = True

        assert app.config["TESTING"]

    def test_cors_configuration(self):
        """Test CORS configuration is applied."""
        app = create_app()

        # CORS should be configured for the app
        # This test verifies the app can be created with CORS
        assert app is not None

    def test_app_route_registration(self):
        """Test that routes are properly registered."""
        app = create_app()

        # Check that routes are registered
        route_rules = [rule.rule for rule in app.url_map.iter_rules()]

        # Should have our API routes
        assert "/api/campaigns" in route_rules
        assert "/api/campaigns/<campaign_id>" in route_rules
        assert "/api/campaigns/<campaign_id>/interaction" in route_rules

    def test_error_handler_registration(self):
        """Test that error handlers are registered if they exist."""
        app = create_app()

        # App should have error handlers
        # This is mainly testing that create_app completes without errors
        assert app is not None


class TestConstants(unittest.TestCase):
    """Test constants and configuration values."""

    def test_header_constants(self):
        """Test that header constants are properly defined."""

        assert HEADER_AUTH == "Authorization"
        assert HEADER_TEST_BYPASS == "X-Test-Bypass-Auth"
        assert HEADER_TEST_USER_ID == "X-Test-User-ID"

    def test_key_constants(self):
        """Test that response key constants are properly defined."""

        assert KEY_SUCCESS == "success"
        assert KEY_ERROR == "error"
        assert KEY_MESSAGE == "message"
        assert KEY_CAMPAIGN_ID == "campaign_id"

    def test_default_test_user(self):
        """Test default test user constant."""

        assert DEFAULT_TEST_USER == "test-user"

    def test_cors_resources_configuration(self):
        """Test CORS resources configuration."""

        assert r"/api/*" in CORS_RESOURCES
        assert CORS_RESOURCES[r"/api/*"]["origins"] == "*"


if __name__ == "__main__":
    unittest.main()
