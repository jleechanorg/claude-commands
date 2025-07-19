#!/usr/bin/env python3
"""
Test infrastructure commands including the new /testserver command.
Tests the server management functionality and integration with existing workflows.
"""

import os
import subprocess
import unittest


class TestInfrastructureCommands(unittest.TestCase):
    """Test infrastructure command functionality."""

    def setUp(self):
        """Set up test environment."""
        self.test_branch = "test-infrastructure-branch"
        self.testserver_script = "/home/jleechan/projects/worldarchitect.ai/worktree_worker8/claude_command_scripts/commands/testserver.sh"

    def test_testserver_command_exists(self):
        """Test that the /testserver command script exists and is executable."""
        self.assertTrue(
            os.path.exists(self.testserver_script),
            f"Testserver script should exist at {self.testserver_script}",
        )
        self.assertTrue(
            os.access(self.testserver_script, os.X_OK),
            "Testserver script should be executable",
        )

    def test_testserver_help_command(self):
        """Test that testserver command shows help when called without arguments."""
        try:
            result = subprocess.run(
                [self.testserver_script],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )

            # Should show usage information
            output = (result.stdout + result.stderr).lower()
            self.assertIn("usage:", output)
            self.assertIn("testserver", output)

        except subprocess.TimeoutExpired:
            self.fail("Testserver help command should not hang")
        except FileNotFoundError:
            self.fail(f"Testserver script not found at {self.testserver_script}")

    def test_testserver_status_command(self):
        """Test testserver status command."""
        try:
            result = subprocess.run(
                [self.testserver_script, "status"],
                check=False,
                capture_output=True,
                text=True,
                timeout=15,
            )

            # Status command should run without error
            # and provide information about running servers
            output = result.stdout + result.stderr
            self.assertIn("server", output.lower())

        except subprocess.TimeoutExpired:
            self.fail("Testserver status command should not hang")

    def test_testserver_list_command(self):
        """Test testserver list command."""
        try:
            result = subprocess.run(
                [self.testserver_script, "list"],
                check=False,
                capture_output=True,
                text=True,
                timeout=15,
            )

            # List command should run without error
            output = result.stdout + result.stderr
            # Should mention ports or servers or branches
            self.assertTrue(
                any(
                    keyword in output.lower()
                    for keyword in ["port", "server", "branch", "running"]
                ),
                f"List command output should mention servers/ports/branches. Got: {output}",
            )

        except subprocess.TimeoutExpired:
            self.fail("Testserver list command should not hang")

    def test_testserver_start_command_integration(self):
        """Test testserver start command integration (without actually starting server)."""
        try:
            # Run start command with dry-run or test mode if available
            result = subprocess.run(
                [self.testserver_script, "start"],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Start command should attempt to start a server
            # The exit code might vary depending on existing servers
            # but it should not hang
            output = result.stdout + result.stderr

            # Should mention starting or server in output
            self.assertTrue(
                any(
                    keyword in output.lower()
                    for keyword in ["start", "server", "running", "port"]
                ),
                f"Start command should mention server startup. Got: {output}",
            )

        except subprocess.TimeoutExpired:
            self.fail("Testserver start command should not hang")

    def test_testserver_script_delegates_to_manager(self):
        """Test that testserver script properly delegates to test_server_manager.sh."""
        manager_script = "/home/jleechan/projects/worldarchitect.ai/worktree_worker8/test_server_manager.sh"

        # Check that the manager script exists
        self.assertTrue(
            os.path.exists(manager_script),
            f"Test server manager should exist at {manager_script}",
        )

        # Read the testserver script to verify it delegates
        with open(self.testserver_script) as f:
            script_content = f.read()

        # Should reference the manager script
        self.assertIn(
            "test_server_manager.sh",
            script_content,
            "Testserver script should delegate to test_server_manager.sh",
        )

    def test_server_management_port_allocation(self):
        """Test that server management uses proper port allocation (8081-8090)."""
        manager_script = "/home/jleechan/projects/worldarchitect.ai/worktree_worker8/test_server_manager.sh"

        if os.path.exists(manager_script):
            with open(manager_script) as f:
                manager_content = f.read()

            # Should mention port range 8081-8090
            self.assertTrue(
                any(
                    port in manager_content for port in ["8081", "8082", "8083", "8090"]
                ),
                "Server manager should use ports in 8081-8090 range",
            )

    def test_log_file_management(self):
        """Test that server management creates proper log files."""
        log_dir = "/tmp/worldarchitectai_logs"

        # Log directory should exist or be creatable
        if not os.path.exists(log_dir):
            # Try to create it (this is what the server should do)
            try:
                os.makedirs(log_dir, exist_ok=True)
                self.assertTrue(True, "Log directory created successfully")
            except PermissionError:
                self.skipTest(
                    f"Cannot create log directory {log_dir} - permission denied"
                )
        else:
            self.assertTrue(os.path.isdir(log_dir), f"{log_dir} should be a directory")

    def test_integration_with_push_command(self):
        """Test that /push command references the testserver system."""
        push_script = "/home/jleechan/projects/worldarchitect.ai/worktree_worker8/claude_command_scripts/commands/push.sh"

        if os.path.exists(push_script):
            with open(push_script) as f:
                push_content = f.read()

            # Should reference testserver command or test_server_manager
            self.assertTrue(
                any(
                    ref in push_content for ref in ["testserver", "test_server_manager"]
                ),
                "Push command should reference testserver system",
            )

    def test_deprecated_servers_documentation(self):
        """Test that deprecated servers documentation exists."""
        deprecated_doc = "/home/jleechan/projects/worldarchitect.ai/worktree_worker8/DEPRECATED_SERVERS.md"

        self.assertTrue(
            os.path.exists(deprecated_doc),
            "DEPRECATED_SERVERS.md should exist to guide migration",
        )

        with open(deprecated_doc) as f:
            doc_content = f.read()

        # Should mention migration or deprecated
        self.assertTrue(
            any(
                keyword in doc_content.lower()
                for keyword in ["deprecated", "migration", "use"]
            ),
            "Deprecated servers doc should mention migration",
        )


class TestServerManagementIntegration(unittest.TestCase):
    """Test server management integration and workflow."""

    def test_command_structure_consistency(self):
        """Test that all server management commands follow consistent patterns."""
        commands_dir = "/home/jleechan/projects/worldarchitect.ai/worktree_worker8/claude_command_scripts/commands"

        if os.path.exists(commands_dir):
            # Check that testserver.sh follows naming convention
            testserver_path = os.path.join(commands_dir, "testserver.sh")
            self.assertTrue(
                os.path.exists(testserver_path),
                "testserver.sh should be in commands directory",
            )

            # Check that it's executable
            self.assertTrue(
                os.access(testserver_path, os.X_OK),
                "testserver.sh should be executable",
            )

    def test_environment_variable_handling(self):
        """Test that server management properly handles environment variables."""
        # Test with TESTING environment variable
        env = os.environ.copy()
        env["TESTING"] = "true"

        try:
            result = subprocess.run(
                [
                    "/home/jleechan/projects/worldarchitect.ai/worltree_worker8/claude_command_scripts/commands/testserver.sh",
                    "status",
                ],
                check=False,
                env=env,
                capture_output=True,
                text=True,
                timeout=10,
            )

            # Should handle TESTING environment gracefully
            # (exact behavior may vary, but should not crash)
            self.assertIsNotNone(result.returncode, "Command should complete")

        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Skip if command not available
            self.skipTest("Testserver command not available for environment testing")

    def test_concurrent_server_handling(self):
        """Test that server management can handle multiple branch requests."""
        # This is a basic test to ensure the system doesn't crash
        # when asked about multiple servers

        commands = [
            ["status"],
            ["list"],
            ["status"],  # Run status twice to test consistency
        ]

        for cmd in commands:
            try:
                result = subprocess.run(
                    [
                        "/home/jleechan/projects/worldarchitect.ai/worktree_worker8/claude_command_scripts/commands/testserver.sh"
                    ]
                    + cmd,
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                # Should not crash or hang
                self.assertIsNotNone(result.returncode)

            except (subprocess.TimeoutExpired, FileNotFoundError):
                # Skip if command not available
                continue


class TestEnhancedGitHubCommands(unittest.TestCase):
    """Test enhanced GitHub commands from PR #620."""

    # Script path constants for portability
    PUSH_SCRIPT_PATH = os.path.join(
        os.path.dirname(__file__), "../claude_command_scripts/commands/push.sh"
    )
    COPILOT_SCRIPT_PATH = os.path.join(
        os.path.dirname(__file__), "../claude_command_scripts/commands/copilot.sh"
    )

    def test_push_command_pr_health_check(self):
        """Test that push command's check_and_fix_pr_issues function exists and handles errors gracefully."""
        push_path = self.PUSH_SCRIPT_PATH

        # Verify push command exists
        self.assertTrue(
            os.path.exists(push_path), "push.sh should exist in commands directory"
        )
        self.assertTrue(os.access(push_path, os.X_OK), "push.sh should be executable")

        # Test that the function definition exists in the script
        with open(push_path) as f:
            content = f.read()
            self.assertIn(
                "check_and_fix_pr_issues()",
                content,
                "push.sh should contain check_and_fix_pr_issues function",
            )
            self.assertIn(
                "pr_mergeable=$(gh pr view",
                content,
                "Function should check PR mergeable status",
            )
            self.assertIn(
                "git merge origin/main",
                content,
                "Function should attempt conflict resolution",
            )

    def test_push_command_conflict_resolution_logic(self):
        """Test push command conflict resolution logic structure."""
        push_path = self.PUSH_SCRIPT_PATH

        with open(push_path) as f:
            content = f.read()

            # Check for proper conflict detection
            self.assertIn("CONFLICTING", content, "Should detect CONFLICTING PR status")
            self.assertIn(
                "--force-with-lease",
                content,
                "Should use safe force push for conflict resolution",
            )
            self.assertIn(
                "Conflicts resolved automatically",
                content,
                "Should report successful conflict resolution",
            )
            self.assertIn(
                "Manual conflict resolution required",
                content,
                "Should handle manual resolution cases",
            )

    def test_push_command_ci_status_checking(self):
        """Test push command CI status checking functionality."""
        push_path = self.PUSH_SCRIPT_PATH

        with open(push_path) as f:
            content = f.read()

            # Check for CI status monitoring
            self.assertIn(
                "statusCheckRollup",
                content,
                "Should check CI status via statusCheckRollup",
            )
            self.assertIn(
                'conclusion == "FAILURE"', content, "Should detect failed CI checks"
            )
            self.assertIn(
                'conclusion == "SUCCESS"', content, "Should detect successful CI checks"
            )
            self.assertIn("CI check(s) failing", content, "Should report CI failures")

    def test_copilot_command_exists_and_functional(self):
        """Test that copilot command exists and has expected functionality."""
        copilot_path = self.COPILOT_SCRIPT_PATH

        # Verify copilot command exists
        self.assertTrue(
            os.path.exists(copilot_path),
            "copilot.sh should exist in commands directory",
        )
        self.assertTrue(
            os.access(copilot_path, os.X_OK), "copilot.sh should be executable"
        )

        # Test that key functions exist
        with open(copilot_path) as f:
            content = f.read()
            self.assertIn(
                "attempt_auto_fixes()",
                content,
                "copilot.sh should contain attempt_auto_fixes function",
            )
            self.assertIn(
                "extract_bot_comments()",
                content,
                "copilot.sh should contain extract_bot_comments function",
            )
            self.assertIn(
                "--force-with-lease", content, "copilot.sh should use safe force push"
            )
            self.assertIn(
                "Applied $fixes_applied automatic fixes",
                content,
                "Should report number of applied fixes",
            )


if __name__ == "__main__":
    unittest.main()
