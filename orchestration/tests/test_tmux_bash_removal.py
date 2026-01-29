"""Tests for tmux command generation without explicit bash invocation.

This test verifies that agent scripts are executed directly using their shebang
instead of explicitly invoking bash, which avoids macOS permission prompts.
"""

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from orchestration.task_dispatcher import TaskDispatcher
from orchestration.cli_validation import ValidationResult


class TestTmuxBashRemoval(unittest.TestCase):
    """Verify that tmux commands do not explicitly invoke bash."""

    def setUp(self):
        """Set up test fixtures."""
        self.dispatcher = TaskDispatcher()

    @patch("orchestration.task_dispatcher.TaskDispatcher._validate_cli_availability")
    @patch("orchestration.task_dispatcher.subprocess.run")
    @patch("orchestration.task_dispatcher._kill_tmux_session_if_exists")
    @patch("orchestration.task_dispatcher.os.path.exists")
    @patch("orchestration.task_dispatcher.shutil.which")
    def test_tmux_command_no_explicit_bash(self, mock_which, mock_exists, mock_kill, mock_run, mock_validate_cli):
        """Verify tmux command does not include explicit 'bash' argument."""
        # Setup mocks - make CLI validation always pass
        mock_validate_cli.return_value = True
        mock_which.return_value = "/usr/bin/claude"  # CLI binary exists
        mock_exists.return_value = True  # Config file exists

        # Mock subprocess.run to capture calls
        subprocess_calls = []
        validation_temp_file = None

        def track_subprocess_calls(cmd, *args, **kwargs):
            nonlocal validation_temp_file
            subprocess_calls.append(cmd)
            result = MagicMock(returncode=0)
            result.stdout = "test output"
            result.stderr = ""
            # Create validation output file if needed
            if isinstance(cmd, list) and len(cmd) > 0 and "claude" in str(cmd):
                # Use tempfile for proper cleanup
                validation_temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
                validation_temp_file.write("test validation output")
                validation_temp_file.close()
            return result

        mock_run.side_effect = track_subprocess_calls

        # Create test agent
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir)

            agent_spec = {
                "name": "test-agent-bash-check",
                "focus": "Test task for bash removal",
                "cli": "claude",
                "model": "claude-opus-4",
                "workspace_root": str(agent_dir),
                "workspace_name": "test-workspace"
            }

            # Call the method that creates tmux session
            result = self.dispatcher.create_dynamic_agent(agent_spec)

            # Find the tmux new-session command in the subprocess calls
            # Filter for tmux commands that contain "new-session"
            tmux_cmds = [cmd for cmd in subprocess_calls
                        if isinstance(cmd, list) and len(cmd) > 1 and
                        cmd[0] == "tmux" and "new-session" in cmd]

            # Verify we found the tmux new-session command
            self.assertGreater(len(tmux_cmds), 0,
                             "Should have at least one tmux new-session command")

            # Check the tmux command
            tmux_cmd = tmux_cmds[0]

            # Critical assertion: bash should NOT be in the command
            self.assertNotIn("bash", tmux_cmd,
                           "tmux command should not explicitly invoke bash")

            # Verify command structure
            self.assertEqual(tmux_cmd[0], "tmux")
            self.assertIn("new-session", tmux_cmd)
            self.assertIn("-d", tmux_cmd)  # Detached mode
            self.assertIn("-s", tmux_cmd)  # Session name

            # Clean up temp validation file if created
            if validation_temp_file:
                Path(validation_temp_file.name).unlink(missing_ok=True)

    @patch("orchestration.task_dispatcher.TaskDispatcher._validate_cli_availability")
    @patch("orchestration.task_dispatcher.shutil.which")
    @patch("orchestration.task_dispatcher.os.path.exists")
    def test_generated_script_no_bash_c(self, mock_exists, mock_which, mock_validate_cli):
        """Verify that generated agent scripts don't use 'bash -c'."""
        # Setup mocks
        mock_validate_cli.return_value = True
        mock_which.return_value = "/usr/bin/claude"
        mock_exists.return_value = True

        # Create test agent and capture generated script
        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir)

            agent_spec = {
                "name": "test-bash-c-check",
                "focus": "Test for bash -c in generated script",
                "cli": "claude",
                "model": "claude-opus-4",
                "workspace_root": str(agent_dir),
                "workspace_name": "test-workspace"
            }

            # Generate the script by calling the method
            # The script is written to /tmp/{agent_name}_run.sh
            script_path = Path(f"/tmp/{agent_spec['name']}_run.sh")

            # Clean up any existing script
            if script_path.exists():
                script_path.unlink()

            # Try to create agent (will fail validation but should generate script)
            try:
                self.dispatcher.create_dynamic_agent(agent_spec)
            except:
                pass

            # Check if script was generated
            if script_path.exists():
                script_content = script_path.read_text()

                # Critical assertion: script should NOT contain "bash -c"
                self.assertNotIn("bash -c", script_content,
                               "Generated agent script should not contain 'bash -c' (use 'sh -c' instead)")

                # Verify it uses sh -c instead
                self.assertIn("sh -c", script_content,
                            "Generated agent script should use 'sh -c' for timeout wrapper")

                # Verify shebang is present
                lines = script_content.split('\n')
                self.assertTrue(len(lines) > 0, "Script should have content")
                self.assertTrue(lines[0].startswith('#!'),
                              f"Generated script should have shebang, got: {lines[0]}")
                self.assertIn('/bash', lines[0],
                            f"Generated script shebang should use /bash, got: {lines[0]}")

                # Clean up
                script_path.unlink()

    def test_script_shebang_compatibility(self):
        """Verify that typical agent scripts have proper shebangs."""
        # This is a sanity check that our orchestration scripts have shebangs
        orchestration_dir = Path(__file__).parent.parent

        # Check some key scripts that might be used
        potential_scripts = [
            orchestration_dir / "start_system.sh",
            orchestration_dir / "cleanup_agents.sh"
        ]

        scripts_found = False
        for script_path in potential_scripts:
            if script_path.exists():
                scripts_found = True
                with open(script_path, 'r') as f:
                    first_line = f.readline()
                    self.assertTrue(first_line.startswith('#!'),
                                  f"{script_path.name} should have a shebang")
                    self.assertTrue('bash' in first_line.lower(),
                                  f"{script_path.name} shebang should specify bash")

        if not scripts_found:
            self.skipTest("No orchestration scripts found to verify shebang compatibility")


if __name__ == "__main__":
    unittest.main()
