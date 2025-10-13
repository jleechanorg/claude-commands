import unittest
from pathlib import Path


class TestMCPConfiguration(unittest.TestCase):
    """Regression tests for claude_mcp.sh MCP server configuration."""

    def setUp(self):
        self.launcher_path = Path("claude_mcp.sh")
        if not self.launcher_path.exists():
            self.skipTest("claude_mcp.sh script is not available")

        self.common_path = Path("scripts/mcp_common.sh")
        if not self.common_path.exists():
            self.skipTest("scripts/mcp_common.sh script is not available")

    def test_slash_commands_removed_from_script(self):
        """Ensure deprecated claude-slash-commands server is no longer referenced."""
        contents = self.launcher_path.read_text()
        self.assertNotIn('claude-slash-commands', contents)

    def test_slash_commands_installer_removed(self):
        """The standalone slash commands installer should be deleted."""
        installer = Path('setup_slash_commands_mcp.sh')
        self.assertFalse(installer.exists())

    def test_serena_configuration_present(self):
        """Verify Serena MCP server configuration remains intact after cleanup."""
        contents = self.common_path.read_text()
        self.assertIn('Setting up Serena MCP Server', contents)
        self.assertIn('git+https://github.com/oraios/serena', contents)

    def test_worldarchitect_server_configuration(self):
        """Ensure the project-specific MCP server setup is still configured."""
        contents = self.common_path.read_text()
        self.assertIn('Setting up WorldArchitect MCP Server', contents)
        self.assertIn('worldarchitect', contents)


if __name__ == '__main__':
    unittest.main()
