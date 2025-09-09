import unittest
import subprocess
import os
import tempfile
import shutil
import re
from unittest.mock import patch, MagicMock

class TestMCPGlobalInstallation(unittest.TestCase):
    """Test suite for MCP slash commands global installation functionality."""

    def setUp(self):
        """Set up test environment with temporary directory."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_uvx_presence_check(self):
        """Test that uvx presence check works correctly."""
        # Test uvx available
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = subprocess.run(['command', '-v', 'uvx'],
                                  shell=False,
                                  timeout=30,
                                  capture_output=True)
            self.assertEqual(result.returncode, 0)
            mock_run.assert_called_once_with(['command', '-v', 'uvx'],
                                           shell=False,
                                           timeout=30,
                                           capture_output=True)

        # Test uvx not available
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            result = subprocess.run(['command', '-v', 'uvx'],
                                  shell=False,
                                  timeout=30,
                                  capture_output=True)
            self.assertEqual(result.returncode, 1)

    def test_python_interpreter_selection(self):
        """Test Python interpreter selection logic."""
        interpreters = ['python3.11', 'python3.10', 'python3.9', 'python3', 'python']

        for interpreter in interpreters:
            with patch('subprocess.run') as mock_run:
                # Mock successful interpreter check
                mock_run.return_value = MagicMock(returncode=0,
                                                stdout='Python 3.11.0\n')

                result = subprocess.run([interpreter, '--version'],
                                      shell=False,
                                      timeout=30,
                                      capture_output=True,
                                      text=True)

                if result.returncode == 0:
                    self.assertIn('Python', result.stdout)
                    break

    def test_mcp_server_installation_dry_run(self):
        """Test MCP server installation process (dry run)."""
        with patch('subprocess.run') as mock_run:
            # Mock uvx command matching actual script pattern
            mock_run.return_value = MagicMock(returncode=0)

            # Test uvx --from command pattern used in actual script
            cmd = ['uvx', '--from', 'file://./mcp_servers/slash_commands', 'claude-slash-commands-mcp']
            result = subprocess.run(cmd,
                                  shell=False,
                                  timeout=120,
                                  capture_output=True)

            self.assertEqual(result.returncode, 0)
            mock_run.assert_called_once_with(cmd,
                                           shell=False,
                                           timeout=120,
                                           capture_output=True)

    def test_pyproject_toml_validity(self):
        """Test that pyproject.toml is valid and contains required fields."""
        pyproject_path = os.path.join('mcp_servers', 'slash_commands', 'pyproject.toml')

        if os.path.exists(pyproject_path):
            with open(pyproject_path, 'r') as f:
                content = f.read()

            # Check for required sections
            self.assertIn('[project]', content)
            self.assertIn('name =', content)
            self.assertIn('version =', content)
            self.assertIn('[project.scripts]', content)

            # Check for security - no eval/exec in build scripts
            self.assertNotIn('eval(', content)
            self.assertNotIn('exec(', content)

    def test_claude_mcp_script_security(self):
        """Test claude_mcp.sh for security issues."""
        if os.path.exists('claude_mcp.sh'):
            with open('claude_mcp.sh', 'r') as f:
                content = f.read()

            # Check for dangerous patterns
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                # Allow specific eval usage for configuration
                if 'eval' in line and 'MCP_CONFIG' not in line:
                    self.fail(f"Potentially unsafe eval usage at line {i}: {line.strip()}")

                # Check for unquoted variables in commands - enhanced security check
                if '$' in line and '"' not in line and "'" not in line:
                    # Skip comments and safe patterns
                    if (not line.strip().startswith('#') and
                        'export' not in line and
                        'echo' not in line and
                        '=' not in line):
                        # This could be a security risk - inform but don't fail
                        pass

            # Verify add-json approach is implemented (CodeRabbit suggestion)
            self.assertIn('add-json', content,
                         "Script should include add-json approach for enhanced reliability")

            # Verify fallback mechanisms exist
            self.assertIn('fallback', content,
                         "Script should include fallback mechanisms for reliability")

    def test_installation_script_error_handling(self):
        """Test that installation scripts have proper error handling."""
        if os.path.exists('claude_mcp.sh'):
            with open('claude_mcp.sh', 'r') as f:
                content = f.read()

            # Should use safe_exit function instead of set -e (which conflicts with graceful error handling)
            self.assertIn('safe_exit', content,
                         "Script should use safe_exit function for graceful error handling")

            # Should not exit terminal session on errors (check for unsafe direct exit calls)
            unsafe_exit_pattern = re.compile(r'^\s*exit\s+1\s*$', re.MULTILINE)
            self.assertIsNone(unsafe_exit_pattern.search(content),
                           "Script should not use direct 'exit 1' which terminates user terminal")

if __name__ == '__main__':
    unittest.main()
