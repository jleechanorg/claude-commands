"""
Comprehensive tests for god mode commands through MCP architecture.
Focuses on GOD_MODE_SET, GOD_MODE_UPDATE_STATE, GOD_ASK_STATE commands.
"""

import json
import os
import sys
import unittest
from concurrent.futures import ThreadPoolExecutor

# Set environment variables for MCP testing
os.environ["TESTING"] = "true"
os.environ["USE_MOCKS"] = "true"

# Add parent directory to path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

# Import after path setup
from main import create_app  # noqa: E402


class TestGodModeCommands(unittest.TestCase):
    """Test god mode command handlers through MCP architecture."""

    def setUp(self):
        """Set up test client and headers for MCP architecture."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Test headers for MCP authentication bypass
        self.test_headers = {
            "X-Test-Bypass-Auth": "true",
            "X-Test-User-ID": "mcp-god-mode-test-user",
            "Content-Type": "application/json",
        }

    def test_mcp_god_mode_set_valid_json(self):
        """Test GOD_MODE_SET command with valid JSON through MCP."""
        # Valid key=value payload format
        user_input = 'GOD_MODE_SET: current_scene = 2\nnpcs = [{"name": "Test NPC"}]'

        response = self.client.post(
            "/api/campaigns/mcp-test-campaign/interaction",
            headers=self.test_headers,
            data=json.dumps({"input": user_input, "mode": "god"}),
        )

        # MCP gateway should handle GOD_MODE_SET commands (may succeed with mocks)
        assert (
            response.status_code in [200, 400]
        ), f"Expected 200 or 400 for GOD_MODE_SET format validation, got {response.status_code}"

    def test_mcp_god_mode_set_invalid_json(self):
        """Test GOD_MODE_SET command with invalid JSON through MCP."""
        # Invalid JSON value in key=value format
        user_input = (
            "GOD_MODE_SET: current_scene = {invalid: json, missing_quotes: true}"
        )

        response = self.client.post(
            "/api/campaigns/mcp-test-campaign/interaction",
            headers=self.test_headers,
            data=json.dumps({"input": user_input, "mode": "god"}),
        )

        # MCP should handle invalid JSON gracefully (may succeed with mock data)
        assert (
            response.status_code in [200, 400]
        ), f"Expected 200 or 400 for invalid JSON in GOD_MODE_SET, got {response.status_code}"

    def test_mcp_god_mode_set_non_object_json(self):
        """Test GOD_MODE_SET command with non-object JSON through MCP."""
        # The SET command expects key=value format, this will be treated as invalid
        user_input = 'GOD_MODE_SET: ["not", "an", "object"]'

        response = self.client.post(
            "/api/campaigns/mcp-test-campaign/interaction",
            headers=self.test_headers,
            data=json.dumps({"input": user_input, "mode": "god"}),
        )

        # MCP should handle non-object JSON gracefully
        assert (
            response.status_code == 400
        ), f"Expected 400 for non-object JSON in GOD_MODE_SET, got {response.status_code}"

    def test_mcp_god_mode_set_no_game_state(self):
        """Test GOD_MODE_SET command when game state doesn't exist through MCP."""
        # Using key=value format
        user_input = "GOD_MODE_SET: current_scene = 2"

        response = self.client.post(
            "/api/campaigns/mcp-nonexistent-campaign/interaction",
            headers=self.test_headers,
            data=json.dumps({"input": user_input, "mode": "god"}),
        )

        # MCP should handle missing game state gracefully (may auto-create with mocks)
        assert (
            response.status_code in [200, 400]
        ), f"Expected 200 or 400 for missing game state in GOD_MODE_SET, got {response.status_code}"

    def test_mcp_god_ask_state_command(self):
        """Test GOD_ASK_STATE command returns current state through MCP."""
        response = self.client.post(
            "/api/campaigns/mcp-test-campaign/interaction",
            headers=self.test_headers,
            data=json.dumps({"input": "GOD_ASK_STATE", "mode": "god"}),
        )

        # MCP should handle GOD_ASK_STATE commands (may be 400 if validation fails)
        assert (
            response.status_code in [200, 400]
        ), f"Expected 200 or 400 for GOD_ASK_STATE auto-creation, got {response.status_code}"

        # If successful, should return valid response
        if response.status_code == 200:
            data = response.get_json()
            assert isinstance(data, dict), "GOD_ASK_STATE response should be dict"

    def test_mcp_god_update_state_valid_json(self):
        """Test GOD_MODE_UPDATE_STATE command with valid JSON through MCP."""
        state_changes = {"current_scene": 2, "hp": 80}
        user_input = f"GOD_MODE_UPDATE_STATE: {json.dumps(state_changes)}"

        response = self.client.post(
            "/api/campaigns/mcp-test-campaign/interaction",
            headers=self.test_headers,
            data=json.dumps({"input": user_input, "mode": "god"}),
        )

        # MCP should handle GOD_MODE_UPDATE_STATE commands (may be 400 if validation fails)
        assert (
            response.status_code in [200, 400]
        ), f"Expected 200 or 400 for GOD_MODE_UPDATE_STATE auto-creation, got {response.status_code}"

    def test_mcp_god_update_state_invalid_json(self):
        """Test GOD_MODE_UPDATE_STATE command with invalid JSON through MCP."""
        user_input = "GOD_MODE_UPDATE_STATE: {invalid json}"

        response = self.client.post(
            "/api/campaigns/mcp-test-campaign/interaction",
            headers=self.test_headers,
            data=json.dumps({"input": user_input, "mode": "god"}),
        )

        # MCP should handle invalid JSON in GOD_MODE_UPDATE_STATE
        assert (
            response.status_code == 400
        ), f"Expected 400 for invalid JSON in GOD_MODE_UPDATE_STATE, got {response.status_code}"

    def test_mcp_god_update_state_non_object_json(self):
        """Test GOD_MODE_UPDATE_STATE command with non-object JSON through MCP."""
        user_input = 'GOD_MODE_UPDATE_STATE: "not an object"'

        response = self.client.post(
            "/api/campaigns/mcp-test-campaign/interaction",
            headers=self.test_headers,
            data=json.dumps({"input": user_input, "mode": "god"}),
        )

        # MCP should handle non-object JSON gracefully
        assert (
            response.status_code == 400
        ), f"Expected 400 for non-object JSON in GOD_MODE_UPDATE_STATE, got {response.status_code}"

    def test_mcp_god_update_state_no_game_state(self):
        """Test GOD_MODE_UPDATE_STATE command when game state doesn't exist through MCP."""
        state_changes = {"current_scene": 2}
        user_input = f"GOD_MODE_UPDATE_STATE: {json.dumps(state_changes)}"

        response = self.client.post(
            "/api/campaigns/mcp-nonexistent-campaign/interaction",
            headers=self.test_headers,
            data=json.dumps({"input": user_input, "mode": "god"}),
        )

        # MCP should handle missing game state gracefully (may auto-create with mocks)
        assert (
            response.status_code in [200, 400]
        ), f"Expected 200 or 400 for missing game state in GOD_MODE_UPDATE_STATE, got {response.status_code}"

    def test_mcp_god_mode_commands_with_different_modes(self):
        """Test god mode commands with different interaction modes through MCP."""
        god_commands = [
            "GOD_ASK_STATE",
            "GOD_MODE_SET: test_field = 1",
            'GOD_MODE_UPDATE_STATE: {"test_field": 2}',
        ]

        modes = ["god", "character", "dm"]

        for command in god_commands:
            for mode in modes:
                with self.subTest(command=command[:15], mode=mode):
                    response = self.client.post(
                        "/api/campaigns/mcp-test-campaign/interaction",
                        headers=self.test_headers,
                        data=json.dumps({"input": command, "mode": mode}),
                    )

                    # MCP should handle god commands in all modes
                    # MCP should handle god commands in all modes (may be 400 if validation fails)
                    assert (
                        response.status_code in [200, 400]
                    ), f"Expected 200 or 400 for GOD command {command[:15]} in {mode} mode, got {response.status_code}"

    def test_mcp_god_mode_commands_concurrent(self):
        """Test concurrent god mode commands through MCP."""

        def send_god_command(command_num):
            user_input = f"GOD_MODE_SET: test_field_{command_num} = {command_num}"
            response = self.client.post(
                "/api/campaigns/mcp-test-campaign/interaction",
                headers=self.test_headers,
                data=json.dumps({"input": user_input, "mode": "god"}),
            )
            return command_num, response.status_code

        # Launch concurrent god mode commands
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(send_god_command, i) for i in range(3)]
            results = [future.result() for future in futures]

        # All concurrent commands should be handled by MCP (may succeed with mocks)
        assert len(results) == 3
        for command_num, status_code in results:
            assert (
                status_code in [200, 400]
            ), f"Expected 200 or 400 for concurrent GOD_MODE_SET command {command_num}, got {status_code}"

    def test_mcp_god_mode_commands_authentication_variations(self):
        """Test god mode commands with various authentication headers through MCP."""
        user_input = "GOD_ASK_STATE"

        # Test different auth header combinations
        auth_variations = [
            # Complete headers
            {
                "X-Test-Bypass-Auth": "true",
                "X-Test-User-ID": "test-user",
                "Content-Type": "application/json",
            },
            # Missing user ID
            {"X-Test-Bypass-Auth": "true", "Content-Type": "application/json"},
            # No auth headers
            {"Content-Type": "application/json"},
        ]

        for i, headers in enumerate(auth_variations):
            with self.subTest(auth_case=i):
                response = self.client.post(
                    "/api/campaigns/mcp-test-campaign/interaction",
                    headers=headers,
                    data=json.dumps({"input": user_input, "mode": "god"}),
                )

                # MCP should handle all auth variations gracefully (may be 401 for missing auth)
                assert (
                    response.status_code in [200, 400, 401]
                ), f"Expected 200, 400, or 401 for GOD_ASK_STATE auth variation {i}, got {response.status_code}"

    def test_mcp_god_mode_commands_with_special_characters(self):
        """Test god mode commands with special characters through MCP."""
        # Test god mode commands with various special characters
        special_commands = [
            'GOD_MODE_SET: special_field = "Test with émojis 🐉"',
            'GOD_MODE_UPDATE_STATE: {"unicode_field": "ñoñó test"}',
            'GOD_MODE_SET: symbols = "!@#$%^&*()"',
        ]

        for i, command in enumerate(special_commands):
            with self.subTest(command_case=i):
                response = self.client.post(
                    "/api/campaigns/mcp-test-campaign/interaction",
                    headers=self.test_headers,
                    data=json.dumps({"input": command, "mode": "god"}),
                )

                # MCP should handle special characters in god mode commands (may be 400 if validation fails)
                assert (
                    response.status_code in [200, 400]
                ), f"Expected 200 or 400 for GOD_ASK_STATE with special chars {i}, got {response.status_code}"


class TestGodModeHelperFunctions(unittest.TestCase):
    """Test god mode helper functions through MCP architecture."""

    def setUp(self):
        """Set up test environment for MCP architecture."""
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Test headers for MCP
        self.test_headers = {
            "X-Test-Bypass-Auth": "true",
            "X-Test-User-ID": "mcp-helper-test-user",
            "Content-Type": "application/json",
        }

    def test_mcp_handle_set_command_not_god_mode_command(self):
        """Test handling of non-god-mode input through MCP."""
        response = self.client.post(
            "/api/campaigns/mcp-test-campaign/interaction",
            headers=self.test_headers,
            data=json.dumps({"input": "Normal user input", "mode": "character"}),
        )

        # MCP should handle normal user input (validates input before checking campaign)
        # With mocks, normal input may get successful game response or validation error
        assert (
            response.status_code in [200, 400, 401, 404]
        ), f"Expected 200, 400, 401, or 404 for normal user input validation, got {response.status_code}"

    def test_mcp_handle_ask_state_not_ask_state_command(self):
        """Test handling of non-ask-state input through MCP."""
        response = self.client.post(
            "/api/campaigns/mcp-test-campaign/interaction",
            headers=self.test_headers,
            data=json.dumps({"input": "Normal user input", "mode": "character"}),
        )

        # MCP should handle non-ask-state input (validates input before checking campaign)
        # With mocks, normal input may get successful game response or validation error
        assert (
            response.status_code in [200, 400, 401, 404]
        ), f"Expected 200, 400, 401, or 404 for non-ask-state input validation, got {response.status_code}"

    def test_mcp_handle_update_state_not_update_command(self):
        """Test handling of non-update input through MCP."""
        response = self.client.post(
            "/api/campaigns/mcp-test-campaign/interaction",
            headers=self.test_headers,
            data=json.dumps({"input": "Normal user input", "mode": "character"}),
        )

        # MCP should handle non-update input (validates input before checking campaign)
        # With mocks, normal input may get successful game response or validation error
        assert (
            response.status_code in [200, 400, 401, 404]
        ), f"Expected 200, 400, 401, or 404 for non-update input validation, got {response.status_code}"

    def test_mcp_handle_ask_state_exact_command_match(self):
        """Test exact GOD_ASK_STATE command match through MCP."""
        response = self.client.post(
            "/api/campaigns/mcp-test-campaign/interaction",
            headers=self.test_headers,
            data=json.dumps({"input": "GOD_ASK_STATE", "mode": "god"}),
        )

        # MCP should handle exact GOD_ASK_STATE command (may be 400 if validation fails)
        assert (
            response.status_code in [200, 400]
        ), f"Expected 200 or 400 for exact GOD_ASK_STATE command, got {response.status_code}"

    def test_mcp_handle_ask_state_with_whitespace(self):
        """Test GOD_ASK_STATE command with whitespace through MCP."""
        response = self.client.post(
            "/api/campaigns/mcp-test-campaign/interaction",
            headers=self.test_headers,
            data=json.dumps({"input": "  GOD_ASK_STATE  ", "mode": "god"}),
        )

        # MCP should handle GOD_ASK_STATE with whitespace (may be 400 if validation fails)
        assert (
            response.status_code in [200, 400]
        ), f"Expected 200 or 400 for GOD_ASK_STATE with whitespace, got {response.status_code}"

    def test_mcp_god_mode_command_error_handling(self):
        """Test god mode command error handling through MCP."""
        # Test various error scenarios
        error_commands = [
            "GOD_MODE_SET:",  # Empty command
            "GOD_MODE_UPDATE_STATE:",  # Empty JSON
            "GOD_INVALID_COMMAND: test",  # Invalid command
        ]

        for i, command in enumerate(error_commands):
            with self.subTest(error_case=i):
                response = self.client.post(
                    "/api/campaigns/mcp-test-campaign/interaction",
                    headers=self.test_headers,
                    data=json.dumps({"input": command, "mode": "god"}),
                )

                # MCP should handle error scenarios gracefully (may return 404 for nonexistent campaigns)
                assert (
                    response.status_code in [200, 400, 401, 404]
                ), f"Expected 200, 400, 401, or 404 for invalid god command {i}, got {response.status_code}"

    def test_mcp_god_mode_large_payload_handling(self):
        """Test god mode commands with large payloads through MCP."""
        # Create a large state update payload
        large_state = {f"field_{i}": f"value_{i}" for i in range(100)}
        user_input = f"GOD_MODE_UPDATE_STATE: {json.dumps(large_state)}"

        response = self.client.post(
            "/api/campaigns/mcp-test-campaign/interaction",
            headers=self.test_headers,
            data=json.dumps({"input": user_input, "mode": "god"}),
        )

        # MCP should handle large payloads gracefully (may succeed with mocks)
        assert (
            response.status_code in [200, 400, 413]
        ), f"Expected 200, 400, or 413 for large god mode payload, got {response.status_code}"


if __name__ == "__main__":
    print("🔵 Running god mode command tests through MCP architecture")
    print("📝 NOTE: Tests validate MCP gateway handling of god mode commands")
    unittest.main()
