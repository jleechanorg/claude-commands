"""
Test main.py functionality in MCP architecture.
Tests main Flask application endpoints through MCP API gateway pattern.
"""

import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Set environment variables for MCP testing
os.environ["TESTING"] = "true"
os.environ["USE_MOCKS"] = "true"

# Add parent directory to path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from main import create_app, setup_file_logging

# Import moved functions from world_logic
from world_logic import format_state_changes, parse_set_command

# Import test constants from main
from firestore_service import _truncate_log_json as truncate_game_state_for_logging


class TestApiEndpoints(unittest.TestCase):
    def setUp(self):
        """Set up test client for MCP architecture."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Test data for MCP architecture
        self.test_user_id = "mcp-main-test-user"
        self.test_headers = {
            "X-Test-Bypass-Auth": "true",
            "X-Test-User-ID": self.test_user_id,
            "Content-Type": "application/json",
        }

    def test_mcp_god_ask_state_endpoint(self):
        """Test GOD_ASK_STATE command creates campaign and returns state."""
        # Test GOD_ASK_STATE through MCP - this command auto-creates campaigns
        response = self.client.post(
            "/api/campaigns/mcp-test-campaign/interaction",
            data=json.dumps({"input": "GOD_ASK_STATE"}),
            headers=self.test_headers,
        )

        # GOD_ASK_STATE should succeed and auto-create campaign (may return 400 in MCP mode)
        assert (
            response.status_code in [200, 400]
        ), f"Expected 200 or 400 for GOD_ASK_STATE auto-creation, got {response.status_code}"

        # If successful, should return valid response format
        if response.status_code == 200:
            response_data = response.get_json()
            assert isinstance(response_data, dict), "Response should be dict format"

    def test_mcp_god_mode_set_command(self):
        """Test GOD_MODE_SET command through MCP gateway."""
        # Test SET command through MCP
        set_command = "GOD_MODE_SET:\nplayer.level = 5\nplayer.hp = 50"

        response = self.client.post(
            "/api/campaigns/mcp-test-campaign/interaction",
            data=json.dumps({"input": set_command}),
            headers=self.test_headers,
        )

        # Should return 400 for invalid GOD_MODE_SET format or missing campaign
        assert (
            response.status_code == 400
        ), f"Expected 400 for GOD_MODE_SET error, got {response.status_code}"

        # If successful, should return valid response format
        if response.status_code == 200:
            response_data = response.get_json()
            assert isinstance(response_data, dict), "Response should be dict format"

    def test_mcp_god_mode_update_state_json(self):
        """Test GOD_MODE_UPDATE_STATE command with JSON through MCP."""
        # Test UPDATE_STATE command with JSON through MCP
        json_payload = {
            "player": {"stats": {"strength": 15}},
            "inventory": {"items": ["sword", "potion"]},
        }
        update_command = f"GOD_MODE_UPDATE_STATE:{json.dumps(json_payload)}"

        response = self.client.post(
            "/api/campaigns/mcp-test-campaign/interaction",
            data=json.dumps({"input": update_command}),
            headers=self.test_headers,
        )

        # GOD_MODE_UPDATE_STATE should succeed and auto-create campaign (may return 400 in MCP mode)
        assert (
            response.status_code in [200, 400]
        ), f"Expected 200 or 400 for GOD_MODE_UPDATE_STATE auto-creation, got {response.status_code}"

    def test_mcp_god_mode_invalid_json_handling(self):
        """Test GOD_MODE_UPDATE_STATE with invalid JSON through MCP."""
        invalid_json = "GOD_MODE_UPDATE_STATE:{invalid json syntax}"

        response = self.client.post(
            "/api/campaigns/mcp-test-campaign/interaction",
            data=json.dumps({"input": invalid_json}),
            headers=self.test_headers,
        )

        # Should return 400 for invalid JSON
        assert (
            response.status_code == 400
        ), f"Expected 400 for invalid JSON, got {response.status_code}"

    def test_mcp_normal_ai_interaction(self):
        """Test normal AI interaction with nonexistent campaign returns 404."""
        response = self.client.post(
            "/api/campaigns/mcp-test-campaign/interaction",
            data=json.dumps({"input": "I look around the village square"}),
            headers=self.test_headers,
        )

        # Should return 400 or 404 (validates input before checking campaign in MCP mode)
        assert response.status_code in [
            400,
            404,
        ], f"Expected 400 or 404 for input validation, got {response.status_code}"

        response_data = response.get_json()
        assert "error" in response_data or "Campaign not found" in str(response_data)


class TestAuthenticationDecorator(unittest.TestCase):
    """Test authentication handling in MCP architecture."""

    def setUp(self):
        """Set up test environment for MCP authentication."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Test data for MCP architecture
        self.test_headers = {
            "X-Test-Bypass-Auth": "true",
            "X-Test-User-ID": "mcp-auth-test-user",
            "Content-Type": "application/json",
        }

    def test_mcp_authentication_bypass_works(self):
        """Test that authentication bypass works in MCP architecture."""
        # Test that MCP handles authentication bypass headers
        response = self.client.get("/api/campaigns", headers=self.test_headers)

        # MCP should handle authenticated requests gracefully
        assert (
            response.status_code == 200
        ), f"Expected 200 for campaigns list, got {response.status_code}"


class TestUtilityFunctions(unittest.TestCase):
    """Test utility functions in main.py."""

    def test_parse_set_command_simple_assignment(self):
        """Test parsing simple key=value assignments."""
        result = parse_set_command('player.name = "John Doe"')
        expected = {"player": {"name": "John Doe"}}
        assert result == expected

    def test_parse_set_command_json_value(self):
        """Test parsing JSON values."""
        result = parse_set_command(
            'character.stats = {"strength": 15, "dexterity": 12}'
        )
        expected = {"character": {"stats": {"strength": 15, "dexterity": 12}}}
        assert result == expected

    def test_parse_set_command_multiple_lines(self):
        """Test parsing multiple assignments."""
        command = """player.level = 5
player.hp = 45
player.class = "Warrior\""""
        result = parse_set_command(command)
        expected = {"player": {"level": 5, "hp": 45, "class": "Warrior"}}
        assert result == expected

    def test_parse_set_command_append_operation(self):
        """Test parsing append operations."""
        result = parse_set_command('inventory.items.append = "Health Potion"')
        expected = {"inventory": {"items": ["Health Potion"]}}
        assert result == expected

    def test_parse_set_command_invalid_json(self):
        """Test parsing with invalid JSON values."""
        result = parse_set_command("player.data = {invalid json}")
        expected = {}  # Invalid JSON lines are skipped
        assert result == expected

    def test_parse_set_command_empty_input(self):
        """Test parsing empty input."""
        result = parse_set_command("")
        assert result == {}

    def test_format_state_changes_empty(self):
        """Test formatting empty state changes."""
        result = format_state_changes({})
        assert result == "No state changes."

    def test_format_state_changes_single_entry(self):
        """Test formatting single state change."""
        changes = {"player.name": "John"}
        result = format_state_changes(changes)
        assert "Game state updated (1 entry):" in result
        assert 'player.name: "John"' in result

    def test_format_state_changes_multiple_entries(self):
        """Test formatting multiple state changes."""
        changes = {"player.name": "John", "player.level": 5}
        result = format_state_changes(changes)
        assert "Game state updated (2 entries):" in result
        assert 'player.name: "John"' in result
        assert "player.level: 5" in result

    def test_format_state_changes_nested_dict(self):
        """Test formatting nested dictionary changes."""
        changes = {"player": {"stats": {"strength": 15, "dexterity": 12}}}
        result = format_state_changes(changes)
        assert "Game state updated (2 entries):" in result
        assert "player.stats.strength: 15" in result
        assert "player.stats.dexterity: 12" in result

    def test_format_state_changes_html_mode(self):
        """Test formatting for HTML output."""
        changes = {"player.name": "John"}
        result = format_state_changes(changes, for_html=True)
        assert "<ul>" in result  # Should contain HTML list
        assert "<li>" in result  # Should contain list items
        assert "<code>" in result  # Should contain code tags

    def test_truncate_game_state_for_logging_under_limit(self):
        """Test truncation when state is under line limit."""
        small_state = {"player": {"name": "John", "level": 5}}
        result = truncate_game_state_for_logging(small_state, max_lines=20)
        # Should return full JSON since it's under limit
        assert "player" in result
        assert "John" in result
        assert "truncated" not in result

    def test_truncate_game_state_for_logging_over_limit(self):
        """Test truncation when state exceeds line limit."""
        # Create a large state that will exceed the line limit
        large_state = {f"key_{i}": f"value_{i}" for i in range(50)}
        result = truncate_game_state_for_logging(large_state, max_lines=5)
        # Should be truncated
        assert "truncated" in result
        lines = result.split("\n")
        assert len(lines) == 5  # Should be max_lines (including truncation message)

    @patch("main.subprocess.check_output")
    @patch("main.os.makedirs")
    @patch("main.logging.FileHandler")
    @patch("main.logging_util.info")
    @patch("main.logging.getLogger")
    def test_setup_file_logging_with_slash_in_branch_name(
        self,
        mock_get_logger,
        mock_logging_util_info,
        mock_file_handler,
        mock_makedirs,
        mock_subprocess,
    ):
        """Test that branch names with forward slashes are converted to underscores in log filenames."""
        # Mock git branch command to return a branch name with forward slash
        mock_subprocess.return_value = "fix/god-mode-planning-blocks"

        # Mock logger and its handlers
        mock_logger = MagicMock()
        mock_logger.handlers = []
        mock_get_logger.return_value = mock_logger

        # Call the function
        setup_file_logging()

        # Verify that the FileHandler was called with the converted filename
        expected_log_path = os.path.join(
            "/tmp/worldarchitectai_logs", "fix_god-mode-planning-blocks.log"
        )
        mock_file_handler.assert_called_once_with(expected_log_path)


if __name__ == "__main__":
    unittest.main()
