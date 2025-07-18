"""
Comprehensive tests for god mode commands in main.py.
Focuses on GOD_MODE_SET, GOD_MODE_UPDATE_STATE, GOD_ASK_STATE commands.
"""

import json
import os
import unittest
from unittest.mock import MagicMock, patch

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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.modules["firebase_admin"] = mock_firebase_admin
sys.modules["firebase_admin.firestore"] = mock_firestore
sys.modules["firebase_admin.auth"] = mock_auth

# Import after mocking
from main import (
    DEFAULT_TEST_USER,
    HEADER_TEST_BYPASS,
    HEADER_TEST_USER_ID,
    KEY_ERROR,
    KEY_RESPONSE,
    KEY_SUCCESS,
    KEY_USER_INPUT,
    _handle_ask_state_command,
    _handle_set_command,
    _handle_update_state_command,
    create_app,
)


class TestGodModeCommands(unittest.TestCase):
    """Test god mode command handlers."""

    def setUp(self):
        """Set up test client and headers."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.test_headers = {
            HEADER_TEST_BYPASS: "true",
            HEADER_TEST_USER_ID: DEFAULT_TEST_USER,
        }

    def test_god_mode_set_valid_json(self):
        """Test GOD_MODE_SET command with valid JSON."""
        with (
            patch("main.firestore_service") as mock_firestore_service,
            patch("gemini_response.GeminiResponse") as mock_gemini_response,
        ):
            # Mock StateHelper
            mock_gemini_response.cleanup_legacy_state.return_value = (
                {"current_scene": 1, "npcs": []},
                False,
                0,
            )

            # Mock current game state
            mock_game_state = MagicMock()
            mock_game_state.to_dict.return_value = {"current_scene": 1, "npcs": []}
            mock_firestore_service.get_campaign_game_state.return_value = (
                mock_game_state
            )

            # Valid key=value payload format
            user_input = (
                'GOD_MODE_SET: current_scene = 2\nnpcs = [{"name": "Test NPC"}]'
            )

            response = self.client.post(
                "/api/campaigns/test-campaign/interaction",
                headers=self.test_headers,
                json={KEY_USER_INPUT: user_input},
            )

            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertTrue(data[KEY_SUCCESS])
            self.assertIn("response", data)

            # Verify state update was called
            mock_firestore_service.update_campaign_game_state.assert_called_once()

    def test_god_mode_set_invalid_json(self):
        """Test GOD_MODE_SET command with invalid JSON."""
        with (
            patch("main.firestore_service") as mock_firestore_service,
            patch("gemini_response.GeminiResponse") as mock_gemini_response,
        ):
            # Mock StateHelper
            mock_gemini_response.cleanup_legacy_state.return_value = (
                {"current_scene": 1},
                False,
                0,
            )

            mock_game_state = MagicMock()
            mock_game_state.to_dict.return_value = {"current_scene": 1}
            mock_firestore_service.get_campaign_game_state.return_value = (
                mock_game_state
            )

            # Invalid JSON value in key=value format
            user_input = (
                "GOD_MODE_SET: current_scene = {invalid: json, missing_quotes: true}"
            )

            response = self.client.post(
                "/api/campaigns/test-campaign/interaction",
                headers=self.test_headers,
                json={KEY_USER_INPUT: user_input},
            )

            # The implementation logs warning but returns 200 with empty changes
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertTrue(data[KEY_SUCCESS])
            # The command will succeed but contain no valid instructions
            self.assertIn("no valid instructions", data[KEY_RESPONSE])

    def test_god_mode_set_non_object_json(self):
        """Test GOD_MODE_SET command with non-object JSON."""
        with (
            patch("main.firestore_service") as mock_firestore_service,
            patch("gemini_response.GeminiResponse") as mock_gemini_response,
        ):
            # Mock StateHelper
            mock_gemini_response.cleanup_legacy_state.return_value = (
                {"current_scene": 1},
                False,
                0,
            )

            mock_game_state = MagicMock()
            mock_game_state.to_dict.return_value = {"current_scene": 1}
            mock_firestore_service.get_campaign_game_state.return_value = (
                mock_game_state
            )

            # The SET command expects key=value format, this will be treated as invalid
            user_input = 'GOD_MODE_SET: ["not", "an", "object"]'

            response = self.client.post(
                "/api/campaigns/test-campaign/interaction",
                headers=self.test_headers,
                json={KEY_USER_INPUT: user_input},
            )

            # No = sign means no valid lines, returns success with no changes
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertTrue(data[KEY_SUCCESS])
            self.assertIn("no valid instructions", data[KEY_RESPONSE])

    def test_god_mode_set_no_game_state(self):
        """Test GOD_MODE_SET command when game state doesn't exist."""
        with (
            patch("main.firestore_service") as mock_firestore_service,
            patch("gemini_response.GeminiResponse") as mock_gemini_response,
        ):
            # Mock StateHelper for empty game state
            mock_gemini_response.cleanup_legacy_state.return_value = ({}, False, 0)

            mock_firestore_service.get_campaign_game_state.return_value = None

            # Using key=value format
            user_input = "GOD_MODE_SET: current_scene = 2"

            response = self.client.post(
                "/api/campaigns/test-campaign/interaction",
                headers=self.test_headers,
                json={KEY_USER_INPUT: user_input},
            )

            # When game state is None, it creates an empty GameState()
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertTrue(data[KEY_SUCCESS])
            # Verify the update was called with the changes
            mock_firestore_service.update_campaign_game_state.assert_called_once()

    def test_god_ask_state_command(self):
        """Test GOD_ASK_STATE command returns current state."""
        with patch("main.firestore_service") as mock_firestore_service:
            # Mock game state with complex data
            mock_game_state = MagicMock()
            test_state = {
                "current_scene": 5,
                "npcs": [{"name": "Gandalf", "level": 20}],
                "player_character": {"name": "Hero", "hp": 100},
            }
            mock_game_state.to_dict.return_value = test_state
            mock_firestore_service.get_campaign_game_state.return_value = (
                mock_game_state
            )

            response = self.client.post(
                "/api/campaigns/test-campaign/interaction",
                headers=self.test_headers,
                json={KEY_USER_INPUT: "GOD_ASK_STATE"},
            )

            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertTrue(data[KEY_SUCCESS])
            self.assertIn("response", data)

            # Response should contain JSON representation of the state
            response_text = data["response"]
            self.assertIn("current_scene", response_text)
            self.assertIn("Gandalf", response_text)
            self.assertIn("Hero", response_text)

            # Verify story entry was added
            mock_firestore_service.add_story_entry.assert_called_once()

    def test_god_update_state_valid_json(self):
        """Test GOD_MODE_UPDATE_STATE command with valid JSON."""
        with (
            patch("main.firestore_service") as mock_firestore_service,
            patch("gemini_response.GeminiResponse") as mock_gemini_response,
        ):
            # Mock StateHelper
            mock_gemini_response.cleanup_legacy_state.return_value = (
                {"current_scene": 1, "hp": 100},
                False,
                0,
            )

            # Mock current game state
            mock_game_state = MagicMock()
            mock_game_state.to_dict.return_value = {"current_scene": 1, "hp": 100}
            mock_firestore_service.get_campaign_game_state.return_value = (
                mock_game_state
            )

            # Mock state update helpers
            mock_gemini_response.apply_automatic_combat_cleanup.return_value = {
                "current_scene": 2,
                "hp": 80,
            }

            # Mock GameState.from_dict
            with patch("main.GameState") as mock_gamestate_class:
                mock_final_state = MagicMock()
                mock_final_state.to_dict.return_value = {"current_scene": 2, "hp": 80}
                mock_gamestate_class.from_dict.return_value = mock_final_state

                state_changes = {"current_scene": 2, "hp": 80}
                user_input = f"GOD_MODE_UPDATE_STATE: {json.dumps(state_changes)}"

                response = self.client.post(
                    "/api/campaigns/test-campaign/interaction",
                    headers=self.test_headers,
                    json={KEY_USER_INPUT: user_input},
                )

                self.assertEqual(response.status_code, 200)
                data = response.get_json()
                self.assertTrue(data[KEY_SUCCESS])
                self.assertIn("response", data)

                # Verify update operations were called
                mock_firestore_service.update_campaign_game_state.assert_called_once()

    def test_god_update_state_invalid_json(self):
        """Test GOD_MODE_UPDATE_STATE command with invalid JSON."""
        user_input = "GOD_MODE_UPDATE_STATE: {invalid json}"

        response = self.client.post(
            "/api/campaigns/test-campaign/interaction",
            headers=self.test_headers,
            json={KEY_USER_INPUT: user_input},
        )

        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn(KEY_ERROR, data)
        self.assertIn("Invalid JSON", data[KEY_ERROR])

    def test_god_update_state_non_object_json(self):
        """Test GOD_MODE_UPDATE_STATE command with non-object JSON."""
        user_input = 'GOD_MODE_UPDATE_STATE: "not an object"'

        response = self.client.post(
            "/api/campaigns/test-campaign/interaction",
            headers=self.test_headers,
            json={KEY_USER_INPUT: user_input},
        )

        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn(KEY_ERROR, data)
        self.assertIn("not a JSON object", data[KEY_ERROR])

    def test_god_update_state_no_game_state(self):
        """Test GOD_MODE_UPDATE_STATE command when game state doesn't exist."""
        with patch("main.firestore_service") as mock_firestore_service:
            mock_firestore_service.get_campaign_game_state.return_value = None

            state_changes = {"current_scene": 2}
            user_input = f"GOD_MODE_UPDATE_STATE: {json.dumps(state_changes)}"

            response = self.client.post(
                "/api/campaigns/test-campaign/interaction",
                headers=self.test_headers,
                json={KEY_USER_INPUT: user_input},
            )

            self.assertEqual(response.status_code, 404)
            data = response.get_json()
            self.assertIn(KEY_ERROR, data)
            self.assertIn("not found", data[KEY_ERROR])

    def test_god_update_state_gamestate_validation_error(self):
        """Test GOD_MODE_UPDATE_STATE when GameState validation fails."""
        with (
            patch("main.firestore_service") as mock_firestore_service,
            patch("gemini_response.GeminiResponse") as mock_gemini_response,
        ):
            # Mock StateHelper
            mock_gemini_response.cleanup_legacy_state.return_value = (
                {"current_scene": 1},
                False,
                0,
            )

            mock_game_state = MagicMock()
            mock_game_state.to_dict.return_value = {"current_scene": 1}
            mock_firestore_service.get_campaign_game_state.return_value = (
                mock_game_state
            )

            mock_gemini_response.apply_automatic_combat_cleanup.return_value = {
                "current_scene": 2
            }

            # Mock GameState.from_dict to raise exception
            with patch("main.GameState") as mock_gamestate_class:
                mock_gamestate_class.from_dict.side_effect = ValueError(
                    "Invalid state data"
                )

                state_changes = {"current_scene": 2}
                user_input = f"GOD_MODE_UPDATE_STATE: {json.dumps(state_changes)}"

                # Try to handle both Flask behaviors
                try:
                    response = self.client.post(
                        "/api/campaigns/test-campaign/interaction",
                        headers=self.test_headers,
                        json={KEY_USER_INPUT: user_input},
                    )

                    # If we get here, Flask converted to 500
                    self.assertEqual(response.status_code, 500)
                    data = response.get_json()
                    self.assertIn(KEY_ERROR, data)
                except ValueError as e:
                    # Flask re-raised the exception (TESTING mode)
                    self.assertEqual(str(e), "Invalid state data")

    def test_god_update_state_unexpected_error(self):
        """Test GOD_MODE_UPDATE_STATE with unexpected error during processing."""
        with (
            patch("main.firestore_service") as mock_firestore_service,
            patch("gemini_response.GeminiResponse") as mock_gemini_response,
        ):
            # Mock StateHelper
            mock_gemini_response.cleanup_legacy_state.return_value = ({}, False, 0)

            mock_firestore_service.get_campaign_game_state.side_effect = Exception(
                "Unexpected database error"
            )

            state_changes = {"current_scene": 2}
            user_input = f"GOD_MODE_UPDATE_STATE: {json.dumps(state_changes)}"

            # Try to handle both Flask behaviors
            try:
                response = self.client.post(
                    "/api/campaigns/test-campaign/interaction",
                    headers=self.test_headers,
                    json={KEY_USER_INPUT: user_input},
                )

                # If we get here, Flask converted to 500
                self.assertEqual(response.status_code, 500)
                data = response.get_json()
                self.assertIn(KEY_ERROR, data)
            except Exception as e:
                # Flask re-raised the exception (TESTING mode)
                self.assertEqual(str(e), "Unexpected database error")


class TestGodModeHelperFunctions(unittest.TestCase):
    """Test god mode helper functions directly."""

    def setUp(self):
        """Set up test environment."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.user_id = "test-user"
        self.campaign_id = "test-campaign"

    def tearDown(self):
        """Clean up test environment."""
        self.app_context.pop()

    def test_handle_set_command_not_god_mode_command(self):
        """Test _handle_set_command with non-god-mode input."""
        result = _handle_set_command(
            "Normal user input", None, self.user_id, self.campaign_id
        )
        self.assertIsNone(result)

    def test_handle_ask_state_not_ask_state_command(self):
        """Test _handle_ask_state_command with non-ask-state input."""
        result = _handle_ask_state_command(
            "Normal user input", None, self.user_id, self.campaign_id
        )
        self.assertIsNone(result)

    def test_handle_update_state_not_update_command(self):
        """Test _handle_update_state_command with non-update input."""
        result = _handle_update_state_command(
            "Normal user input", self.user_id, self.campaign_id
        )
        self.assertIsNone(result)

    def test_handle_ask_state_exact_command_match(self):
        """Test _handle_ask_state_command with exact command match."""
        with patch("main.firestore_service") as mock_firestore_service:
            mock_game_state = MagicMock()
            mock_game_state.to_dict.return_value = {"test": "data"}

            result = _handle_ask_state_command(
                "GOD_ASK_STATE", mock_game_state, self.user_id, self.campaign_id
            )

            self.assertIsNotNone(result)
            # Should return a Flask response
            self.assertTrue(
                hasattr(result, "get_json") or hasattr(result, "status_code")
            )

    def test_handle_ask_state_with_whitespace(self):
        """Test _handle_ask_state_command with whitespace around command."""
        with patch("main.firestore_service") as mock_firestore_service:
            mock_game_state = MagicMock()
            mock_game_state.to_dict.return_value = {"test": "data"}

            result = _handle_ask_state_command(
                "  GOD_ASK_STATE  ", mock_game_state, self.user_id, self.campaign_id
            )

            self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
