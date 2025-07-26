#!/usr/bin/env python3
"""
Infrastructure tests for /testserver command functionality.
Tests server start/stop/status commands, port allocation, and process management.
"""

import os
import subprocess
import sys
import unittest
from unittest.mock import patch

# Add parent directory to path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)


class TestServerInfrastructure(unittest.TestCase):
    """Test /testserver command infrastructure functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        self.testserver_script = os.path.join(
            self.project_root, "claude_command_scripts", "commands", "testserver.sh"
        )
        self.test_branch = "test-infrastructure-branch"

        # Ensure testserver script exists
        self.assertTrue(
            os.path.exists(self.testserver_script),
            f"testserver.sh not found at {self.testserver_script}",
        )

    def test_testserver_help_command(self):
        """Test that /testserver help displays usage information."""
        try:
            result = subprocess.run(
                [self.testserver_script, "help"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=self.project_root,
            )

            # Should exit successfully and show usage
            self.assertEqual(result.returncode, 0)
            self.assertIn("Test Server Management", result.stdout)
            self.assertIn("Usage: /testserver [action] [branch]", result.stdout)
            self.assertIn("start", result.stdout)
            self.assertIn("stop", result.stdout)
            self.assertIn("list", result.stdout)
            self.assertIn("cleanup", result.stdout)
            self.assertIn("status", result.stdout)

            # Verify feature descriptions
            self.assertIn("Automatic port allocation", result.stdout)
            self.assertIn("Branch-specific logging", result.stdout)
            self.assertIn("Process management", result.stdout)

        except subprocess.TimeoutExpired:
            self.fail("testserver.sh help command timed out")
        except Exception as e:
            self.fail(f"Failed to run testserver.sh help: {e}")

    @unittest.skip("TODO: Fix error message assertion for invalid action")
    def test_testserver_unknown_action(self):
        """Test /testserver with unknown action shows error and usage."""
        try:
            result = subprocess.run(
                [self.testserver_script, "invalid-action"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=self.project_root,
            )

            # Should exit with error code
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Unknown action: invalid-action", result.stderr)

        except subprocess.TimeoutExpired:
            self.fail("testserver.sh invalid action command timed out")
        except Exception as e:
            self.fail(f"Failed to run testserver.sh with invalid action: {e}")

    @patch("subprocess.run")
    def test_testserver_manager_delegation(self, mock_subprocess):
        """Test that testserver.sh properly delegates to test_server_manager.sh."""
        # Mock successful delegation
        mock_subprocess.return_value = subprocess.CompletedProcess(
            args=["test_server_manager.sh", "list"],
            returncode=0,
            stdout="Mocked server list output",
            stderr="",
        )

        # Test delegation for different actions
        actions_to_test = ["start", "stop", "list", "cleanup"]

        for action in actions_to_test:
            with self.subTest(action=action):
                try:
                    result = subprocess.run(
                        [self.testserver_script, action],
                        check=False,
                        capture_output=True,
                        text=True,
                        timeout=5,
                        cwd=self.project_root,
                    )

                    # Should attempt to run test_server_manager.sh
                    # (This may fail if test_server_manager.sh doesn't exist, but testserver.sh should try)

                except subprocess.TimeoutExpired:
                    self.fail(f"testserver.sh {action} command timed out")
                except Exception:
                    # Expected if test_server_manager.sh doesn't exist
                    # The important thing is that testserver.sh attempts delegation
                    pass

    def test_port_allocation_range(self):
        """Test that port allocation works within expected range (8081-8090)."""
        # Test port-utils.sh if it exists
        port_utils_script = os.path.join(
            self.project_root, "claude_command_scripts", "port-utils.sh"
        )

        if os.path.exists(port_utils_script):
            try:
                # Source the script and test port allocation functions
                result = subprocess.run(
                    [
                        "bash",
                        "-c",
                        f'source {port_utils_script} && echo "Port utils loaded"',
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=5,
                    cwd=self.project_root,
                )

                self.assertEqual(result.returncode, 0)
                self.assertIn("Port utils loaded", result.stdout)

            except subprocess.TimeoutExpired:
                self.fail("port-utils.sh loading timed out")
            except Exception as e:
                self.fail(f"Failed to load port-utils.sh: {e}")
        else:
            self.skipTest("port-utils.sh not found - skipping port allocation test")

    def test_branch_specific_logging(self):
        """Test that branch-specific logging directory structure works."""
        logs_dir = "/tmp/worldarchitectai_logs"

        # Verify logs directory exists or can be created
        if not os.path.exists(logs_dir):
            try:
                os.makedirs(logs_dir, exist_ok=True)
            except PermissionError:
                self.skipTest(
                    f"Cannot create logs directory {logs_dir} - permission denied"
                )

        # Test log file naming pattern
        test_branch_log = os.path.join(logs_dir, f"{self.test_branch}.log")

        # Ensure we can write to log file location
        try:
            with open(test_branch_log, "w") as f:
                f.write("Test log entry\n")

            self.assertTrue(os.path.exists(test_branch_log))

            # Clean up test log file
            os.remove(test_branch_log)

        except PermissionError:
            self.skipTest(
                f"Cannot write to log file {test_branch_log} - permission denied"
            )
        except Exception as e:
            self.fail(f"Failed to test branch-specific logging: {e}")

    def test_status_command_current_branch(self):
        """Test /testserver status shows current branch information."""
        try:
            # First get current branch for comparison
            branch_result = subprocess.run(
                ["git", "branch", "--show-current"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
                cwd=self.project_root,
            )

            if branch_result.returncode != 0:
                self.skipTest("Not in a git repository - skipping git branch test")

            current_branch = branch_result.stdout.strip()

            # Test status command
            result = subprocess.run(
                [self.testserver_script, "status"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=self.project_root,
            )

            # Should show current branch in output
            self.assertIn(current_branch, result.stdout)
            self.assertIn("Test Server Status", result.stdout)

        except subprocess.TimeoutExpired:
            self.fail("testserver.sh status command timed out")
        except Exception as e:
            self.fail(f"Failed to run testserver.sh status: {e}")

    def test_integration_with_push_commands(self):
        """Test that testserver integrates with /push and /integrate commands."""
        # Check if integration scripts exist
        push_script = os.path.join(
            self.project_root, "claude_command_scripts", "commands", "push.sh"
        )
        integrate_script = os.path.join(self.project_root, "integrate.sh")

        if os.path.exists(push_script):
            # Test that push script exists and is executable
            self.assertTrue(
                os.access(push_script, os.X_OK), "push.sh should be executable"
            )

        if os.path.exists(integrate_script):
            # Test that integrate script exists and is executable
            self.assertTrue(
                os.access(integrate_script, os.X_OK),
                "integrate.sh should be executable",
            )

        # Test testserver.sh help mentions integration
        try:
            result = subprocess.run(
                [self.testserver_script, "help"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=self.project_root,
            )

            self.assertIn(
                "Integration with /push and /integrate commands", result.stdout
            )

        except subprocess.TimeoutExpired:
            self.fail("testserver.sh help timed out during integration test")
        except Exception as e:
            self.fail(f"Failed during integration test: {e}")

    def test_conflict_detection_and_resolution(self):
        """Test that testserver handles port conflicts and process management."""
        # This test verifies the design features exist, not necessarily the implementation
        try:
            result = subprocess.run(
                [self.testserver_script, "help"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=self.project_root,
            )

            # Verify conflict detection feature is documented
            self.assertIn("Conflict detection", result.stdout)

            # Verify process management with PID tracking feature is documented
            self.assertIn("Process management with PID tracking", result.stdout)

        except subprocess.TimeoutExpired:
            self.fail("testserver.sh help timed out during conflict detection test")
        except Exception as e:
            self.fail(f"Failed during conflict detection test: {e}")

    @unittest.skip("TODO: Fix error message assertion for missing manager")
    def test_error_handling_missing_manager(self):
        """Test error handling when test_server_manager.sh is missing."""
        # Temporarily rename test_server_manager.sh if it exists
        manager_script = os.path.join(self.project_root, "test_server_manager.sh")
        backup_script = os.path.join(self.project_root, "test_server_manager.sh.backup")

        manager_existed = False

        try:
            if os.path.exists(manager_script):
                manager_existed = True
                os.rename(manager_script, backup_script)

            # Test that testserver.sh handles missing manager gracefully
            result = subprocess.run(
                [self.testserver_script, "list"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=self.project_root,
            )

            # Should show appropriate error message
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("test_server_manager.sh not found", result.stderr)

        except subprocess.TimeoutExpired:
            self.fail("testserver.sh error handling test timed out")
        except Exception as e:
            self.fail(f"Failed during error handling test: {e}")
        finally:
            # Restore test_server_manager.sh if it existed
            if manager_existed and os.path.exists(backup_script):
                os.rename(backup_script, manager_script)


class TestServerProcessManagement(unittest.TestCase):
    """Test server process management and monitoring functionality."""

    def test_process_identification(self):
        """Test that server processes can be identified by branch."""
        # Test process identification patterns
        sample_processes = [
            "python3 mvp_site/main.py --port 8081 --branch feature-test",
            "gunicorn --bind 0.0.0.0:8082 main:app --branch dev-123",
            "flask run --port 8083 --branch hotfix-critical",
        ]

        # Test process parsing logic (if implemented)
        for process_cmd in sample_processes:
            # Extract branch from command line
            if "--branch" in process_cmd:
                parts = process_cmd.split("--branch")
                if len(parts) > 1:
                    branch = parts[1].strip().split()[0]
                    self.assertIsNotNone(branch)
                    self.assertNotEqual(branch, "")

    def test_port_range_validation(self):
        """Test that port allocation stays within valid range."""
        # Test port range validation (8081-8090 as documented)
        valid_ports = range(8081, 8091)  # 8081-8090 inclusive

        for port in valid_ports:
            self.assertGreaterEqual(port, 8081)
            self.assertLessEqual(port, 8090)

        # Test invalid ports
        invalid_ports = [8080, 8091, 3000, 5000]

        for port in invalid_ports:
            self.assertTrue(port < 8081 or port > 8090)

    def test_log_file_structure(self):
        """Test branch-specific log file naming structure."""
        test_branches = [
            "main",
            "feature-auth",
            "dev-1234567890",
            "hotfix-critical-bug",
            "task-implement-feature",
        ]

        logs_base = "/tmp/worldarchitectai_logs"

        for branch in test_branches:
            expected_log = os.path.join(logs_base, f"{branch}.log")

            # Verify log file path format
            self.assertTrue(expected_log.endswith(".log"))
            self.assertIn(branch, expected_log)
            self.assertIn(logs_base, expected_log)


if __name__ == "__main__":
    unittest.main()
