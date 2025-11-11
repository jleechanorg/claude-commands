"""Regression tests for the Second Opinion MCP server configuration."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

SECOND_OPINION_MCP_URL = "https://ai-universe-backend-dev-114133832173.us-central1.run.app/mcp"


class TestSecondOpinionMCPServer(unittest.TestCase):
    """Validate the Second Opinion MCP server configuration in mcp_common.sh."""

    def setUp(self) -> None:  # noqa: D401 - standard unittest hook
        self.script_path = Path("scripts/mcp_common.sh")
        if not self.script_path.exists():
            self.skipTest("scripts/mcp_common.sh is not available")

    def test_second_opinion_configuration_block_present(self) -> None:
        """Ensure the setup block contains the expected metadata and endpoint."""
        contents = self.script_path.read_text()

        self.assertIn("Setting up Second Opinion MCP Server", contents)
        self.assertIn("second-opinion-tool", contents)
        self.assertIn(
            f"local second_opinion_mcp_url=\"{SECOND_OPINION_MCP_URL}\"",
            contents,
        )
        self.assertIn(
            "log_with_timestamp \"Setting up MCP server: ${server_name} (HTTP: ${second_opinion_mcp_url})\"",
            contents,
        )

    def test_second_opinion_invoked_after_render(self) -> None:
        """Verify the new installer runs in the main execution flow after Render."""
        contents = self.script_path.read_text()

        render_positions = [m.start() for m in re.finditer(r"setup_render_mcp_server", contents)]
        second_opinion_positions = [
            m.start() for m in re.finditer(r"setup_second_opinion_mcp_server", contents)
        ]

        self.assertGreaterEqual(len(render_positions), 2)
        self.assertGreaterEqual(len(second_opinion_positions), 2)
        self.assertLess(render_positions[1], second_opinion_positions[1])

    def test_second_opinion_uses_add_json_command(self) -> None:
        """Ensure the configuration leverages the secure add-json helper."""
        contents = self.script_path.read_text()
        expected_add_json_line = (
            'capture_command_output add_output add_exit_code "${MCP_CLI_BIN}" mcp add-json '
            '"${MCP_SCOPE_ARGS[@]}" "$server_name" "$json_payload"'
        )
        expected_codex_line = (
            'capture_command_output add_output add_exit_code "${MCP_CLI_BIN}" mcp add --url '
            '"${second_opinion_mcp_url}" "$server_name"'
        )
        self.assertIn(expected_add_json_line, contents)
        self.assertIn(expected_codex_line, contents)


if __name__ == "__main__":
    unittest.main()
