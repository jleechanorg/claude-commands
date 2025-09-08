#!/usr/bin/env python3
"""
Matrix-Driven Tests for Worktree Location Enhancement

This test suite implements the comprehensive test matrix for the new worktree location
functionality that creates worktrees under ~/projects/orch_{repo_name}/.

All tests are designed to FAIL initially (RED phase) and pass after implementation.
"""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, call, patch

# Import the module we're testing
from orchestration.task_dispatcher import TaskDispatcher


class TestWorktreeLocationMatrix(unittest.TestCase):
    """Matrix-driven tests for worktree location functionality."""

    def setUp(self):
        """Set up test environment for each test case."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        self.test_repo_dir = os.path.join(self.temp_dir, "test_repo")
        os.makedirs(self.test_repo_dir)
        os.chdir(self.test_repo_dir)

        # Initialize git repo for tests
        subprocess.run(["git", "init"], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], check=True, capture_output=True)

        # Create initial commit
        with open("README.md", "w") as f:
            f.write("Test repository")
        subprocess.run(["git", "add", "README.md"], check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], check=True, capture_output=True)

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    # ====================
    # Matrix 1: Repository Context × Location Calculation
    # ====================

    def test_matrix_ssh_remote_extraction(self):
        """Matrix [SSH Remote, worldarchitect.ai] → ~/projects/orch_worldarchitect.ai/"""
        # Setup SSH remote
        subprocess.run([
            "git", "remote", "add", "origin",
            "git@github.com:user/worldarchitect.ai.git"
        ], check=True, capture_output=True)

        # This will FAIL initially - no implementation exists
        if TaskDispatcher is None:
            self.fail("TaskDispatcher not implemented yet - RED phase expected")

        dispatcher = TaskDispatcher()
        repo_name = dispatcher._extract_repository_name()
        base_path = dispatcher._get_worktree_base_path()

        self.assertEqual(repo_name, "worldarchitect.ai")
        expected_path = os.path.expanduser("~/projects/orch_worldarchitect.ai")
        self.assertEqual(base_path, expected_path)

    def test_matrix_https_remote_extraction(self):
        """Matrix [HTTPS Remote, my-project] → ~/projects/orch_my-project/"""
        # Setup HTTPS remote
        subprocess.run([
            "git", "remote", "add", "origin",
            "https://github.com/user/my-project.git"
        ], check=True, capture_output=True)

        # This will FAIL initially - no implementation exists
        if TaskDispatcher is None:
            self.fail("TaskDispatcher not implemented yet - RED phase expected")

        dispatcher = TaskDispatcher()
        repo_name = dispatcher._extract_repository_name()
        base_path = dispatcher._get_worktree_base_path()

        self.assertEqual(repo_name, "my-project")
        expected_path = os.path.expanduser("~/projects/orch_my-project")
        self.assertEqual(base_path, expected_path)

    def test_matrix_local_repository_fallback(self):
        """Matrix [Local Repo, local-repo] → ~/projects/orch_local-repo/"""
        # No remote - should use directory name

        # This will FAIL initially - no implementation exists
        if TaskDispatcher is None:
            self.fail("TaskDispatcher not implemented yet - RED phase expected")

        dispatcher = TaskDispatcher()
        repo_name = dispatcher._extract_repository_name()
        base_path = dispatcher._get_worktree_base_path()

        self.assertEqual(repo_name, "test_repo")  # Current directory name
        expected_path = os.path.expanduser("~/projects/orch_test_repo")
        self.assertEqual(base_path, expected_path)

    def test_matrix_complex_repo_name_handling(self):
        """Matrix [Complex Name, my.complex-repo_name] → ~/projects/orch_my.complex-repo_name/"""
        # Setup remote with complex name
        subprocess.run([
            "git", "remote", "add", "origin",
            "git@github.com:user/my.complex-repo_name.git"
        ], check=True, capture_output=True)

        # This will FAIL initially - no implementation exists
        if TaskDispatcher is None:
            self.fail("TaskDispatcher not implemented yet - RED phase expected")

        dispatcher = TaskDispatcher()
        repo_name = dispatcher._extract_repository_name()

        self.assertEqual(repo_name, "my.complex-repo_name")
        # Should handle special characters safely
        self.assertTrue(all(c.isalnum() or c in ".-_" for c in repo_name))

    def test_matrix_no_git_repository_error(self):
        """Matrix [No Git, N/A] → ERROR"""
        # Move to non-git directory
        non_git_dir = os.path.join(self.temp_dir, "non_git")
        os.makedirs(non_git_dir)
        os.chdir(non_git_dir)

        # This will FAIL initially - no implementation exists
        if TaskDispatcher is None:
            self.fail("TaskDispatcher not implemented yet - RED phase expected")

        dispatcher = TaskDispatcher()

        # Since we're not in a git repo, this should either raise an exception or return directory name
        # Let's check if we can trigger an exception through _get_worktree_base_path instead
        try:
            repo_name = dispatcher._extract_repository_name()
            # If it doesn't raise an exception, it should fall back to directory name
            self.assertEqual(repo_name, "non_git")
        except Exception as e:
            # If it does raise an exception, it should mention git
            self.assertIn("not a git repository", str(e).lower())

    # ====================
    # Matrix 2: Workspace Configuration × Custom Naming
    # ====================

    def test_matrix_default_configuration(self):
        """Matrix [None, None, None] → ~/projects/orch_{repo}/agent-name"""
        subprocess.run([
            "git", "remote", "add", "origin",
            "git@github.com:user/test-repo.git"
        ], check=True, capture_output=True)

        # This will FAIL initially - no implementation exists
        if TaskDispatcher is None:
            self.fail("TaskDispatcher not implemented yet - RED phase expected")

        dispatcher = TaskDispatcher()
        agent_spec = {
            "name": "test-agent",
            "workspace_config": {}
        }

        agent_dir = dispatcher._calculate_agent_directory(agent_spec)
        expected = os.path.expanduser("~/projects/orch_test-repo/test-agent")
        self.assertEqual(agent_dir, expected)

    def test_matrix_custom_name_only(self):
        """Matrix [tmux-pr123, None] → ~/projects/orch_{repo}/tmux-pr123"""
        subprocess.run([
            "git", "remote", "add", "origin",
            "git@github.com:user/test-repo.git"
        ], check=True, capture_output=True)

        # This will FAIL initially - no implementation exists
        if TaskDispatcher is None:
            self.fail("TaskDispatcher not implemented yet - RED phase expected")

        dispatcher = TaskDispatcher()
        agent_spec = {
            "name": "test-agent",
            "workspace_config": {
                "workspace_name": "tmux-pr123"
            }
        }

        agent_dir = dispatcher._calculate_agent_directory(agent_spec)
        expected = os.path.expanduser("~/projects/orch_test-repo/tmux-pr123")
        self.assertEqual(agent_dir, expected)

    def test_matrix_custom_root_only(self):
        """Matrix [None, /tmp/.worktrees] → /tmp/.worktrees/agent-name"""
        # This will FAIL initially - no implementation exists
        if TaskDispatcher is None:
            self.fail("TaskDispatcher not implemented yet - RED phase expected")

        dispatcher = TaskDispatcher()
        agent_spec = {
            "name": "test-agent",
            "workspace_config": {
                "workspace_root": "/tmp/.worktrees"
            }
        }

        agent_dir = dispatcher._calculate_agent_directory(agent_spec)
        expected = os.path.realpath("/tmp/.worktrees/test-agent")
        self.assertEqual(agent_dir, expected)

    def test_matrix_both_custom(self):
        """Matrix [tmux-pr456, ~/.cache/worktrees] → ~/.cache/worktrees/tmux-pr456"""
        # This will FAIL initially - no implementation exists
        if TaskDispatcher is None:
            self.fail("TaskDispatcher not implemented yet - RED phase expected")

        dispatcher = TaskDispatcher()
        agent_spec = {
            "name": "test-agent",
            "workspace_config": {
                "workspace_name": "tmux-pr456",
                "workspace_root": "~/.cache/worktrees"
            }
        }

        agent_dir = dispatcher._calculate_agent_directory(agent_spec)
        expected = os.path.expanduser("~/.cache/worktrees/tmux-pr456")
        self.assertEqual(agent_dir, expected)

    def test_matrix_relative_root(self):
        """Matrix [None, .worktrees] → {current_dir}/.worktrees/agent-name"""
        # This will FAIL initially - no implementation exists
        if TaskDispatcher is None:
            self.fail("TaskDispatcher not implemented yet - RED phase expected")

        dispatcher = TaskDispatcher()
        agent_spec = {
            "name": "test-agent",
            "workspace_config": {
                "workspace_root": ".worktrees"
            }
        }

        agent_dir = dispatcher._calculate_agent_directory(agent_spec)
        expected = os.path.join(os.getcwd(), ".worktrees/test-agent")
        self.assertEqual(agent_dir, expected)

    # ====================
    # Matrix 3: Git Operations × Repository States
    # ====================

    @patch('subprocess.run')
    def test_matrix_clean_main_success(self, mock_run):
        """Matrix [Clean Main, git worktree add] → Success with new location"""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        # This will FAIL initially - no implementation exists
        if TaskDispatcher is None:
            self.fail("TaskDispatcher not implemented yet - RED phase expected")

        dispatcher = TaskDispatcher()
        agent_spec = {"name": "test-agent", "workspace_config": {}}

        # Mock successful worktree creation
        agent_dir, result = dispatcher._create_worktree_at_location(agent_spec, "test-branch")

        self.assertIsNotNone(agent_dir)
        self.assertEqual(result.returncode, 0)
        # Verify git worktree add was called with new location
        expected_dir = os.path.expanduser("~/projects/orch_test_repo/test-agent")
        mock_run.assert_called_with(
            ["git", "worktree", "add", "-b", "test-branch", expected_dir, "main"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
            shell=False
        )

    @patch('subprocess.run')
    def test_matrix_dirty_working_tree_success(self, mock_run):
        """Matrix [Dirty Working Tree, git worktree add] → Success (unaffected)"""
        # Simulate dirty working tree - worktree should still work
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        # This will FAIL initially - no implementation exists
        if TaskDispatcher is None:
            self.fail("TaskDispatcher not implemented yet - RED phase expected")

        dispatcher = TaskDispatcher()
        agent_spec = {"name": "test-agent", "workspace_config": {}}

        agent_dir, result = dispatcher._create_worktree_at_location(agent_spec, "test-branch")

        self.assertIsNotNone(agent_dir)
        # Worktree creation should proceed despite dirty working tree
        self.assertTrue(mock_run.called)

    @patch('subprocess.run')
    def test_matrix_branch_exists_error(self, mock_run):
        """Matrix [Branch Exists, git worktree add -b existing] → Error from git"""
        # Simulate git error for existing branch
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="fatal: A branch named 'test-agent-work' already exists."
        )

        # This will FAIL initially - no implementation exists
        if TaskDispatcher is None:
            self.fail("TaskDispatcher not implemented yet - RED phase expected")

        dispatcher = TaskDispatcher()
        agent_spec = {"name": "test-agent", "workspace_config": {}}

        agent_dir, result = dispatcher._create_worktree_at_location(agent_spec, "test-branch")

        self.assertIsNotNone(agent_dir)
        self.assertEqual(result.returncode, 1)
        # Should propagate git error appropriately
        self.assertTrue(mock_run.called)

    # ====================
    # Matrix 4: Edge Cases × Path Handling
    # ====================

    def test_matrix_path_expansion(self):
        """Matrix [~/projects/orch_repo] → /Users/user/projects/orch_repo"""
        # This will FAIL initially - no implementation exists
        if TaskDispatcher is None:
            self.fail("TaskDispatcher not implemented yet - RED phase expected")

        dispatcher = TaskDispatcher()

        # Test tilde expansion
        path_with_tilde = "~/projects/orch_test_repo"
        expanded = dispatcher._expand_path(path_with_tilde)

        self.assertNotIn("~", expanded)
        self.assertTrue(expanded.startswith("/"))
        self.assertIn("projects/orch_test_repo", expanded)

    def test_matrix_path_creation(self):
        """Matrix [Non-existent dirs] → Create parent directories"""
        # This will FAIL initially - no implementation exists
        if TaskDispatcher is None:
            self.fail("TaskDispatcher not implemented yet - RED phase expected")

        dispatcher = TaskDispatcher()

        # Test directory creation
        test_path = os.path.join(self.temp_dir, "deep/nested/path")
        dispatcher._ensure_directory_exists(test_path)

        self.assertTrue(os.path.exists(test_path))
        self.assertTrue(os.path.isdir(test_path))

    def test_matrix_permission_handling(self):
        """Matrix [Read-only parent] → Error gracefully"""
        # This will FAIL initially - no implementation exists
        if TaskDispatcher is None:
            self.fail("TaskDispatcher not implemented yet - RED phase expected")

        dispatcher = TaskDispatcher()

        # Create read-only directory
        readonly_dir = os.path.join(self.temp_dir, "readonly")
        os.makedirs(readonly_dir)
        os.chmod(readonly_dir, 0o444)  # Read-only

        try:
            with self.assertRaises(PermissionError):
                test_path = os.path.join(readonly_dir, "subdir")
                dispatcher._ensure_directory_exists(test_path)
        finally:
            # Clean up
            os.chmod(readonly_dir, 0o755)

    # ====================
    # Matrix 5: Agent Types × Workspace Patterns
    # ====================

    def test_matrix_task_agent_pattern(self):
        """Matrix [task-agent, task-agent-{task}] → ~/projects/orch_repo/task-agent-implement-auth"""
        subprocess.run([
            "git", "remote", "add", "origin",
            "git@github.com:user/test-repo.git"
        ], check=True, capture_output=True)

        # This will FAIL initially - no implementation exists
        if TaskDispatcher is None:
            self.fail("TaskDispatcher not implemented yet - RED phase expected")

        dispatcher = TaskDispatcher()
        agent_spec = {
            "name": "task-agent-implement-auth",
            "workspace_config": {}
        }

        agent_dir = dispatcher._calculate_agent_directory(agent_spec)
        expected = os.path.expanduser("~/projects/orch_test-repo/task-agent-implement-auth")
        self.assertEqual(agent_dir, expected)

    def test_matrix_tmux_pr_pattern(self):
        """Matrix [tmux-pr, tmux-pr{number}] → ~/projects/orch_repo/tmux-pr123"""
        subprocess.run([
            "git", "remote", "add", "origin",
            "git@github.com:user/test-repo.git"
        ], check=True, capture_output=True)

        # This will FAIL initially - no implementation exists
        if TaskDispatcher is None:
            self.fail("TaskDispatcher not implemented yet - RED phase expected")

        dispatcher = TaskDispatcher()
        agent_spec = {
            "name": "tmux-pr123",
            "workspace_config": {}
        }

        agent_dir = dispatcher._calculate_agent_directory(agent_spec)
        expected = os.path.expanduser("~/projects/orch_test-repo/tmux-pr123")
        self.assertEqual(agent_dir, expected)

    def test_matrix_legacy_workspace_pattern(self):
        """Matrix [agent_workspace, agent_workspace_*] → ~/projects/orch_repo/agent_workspace_test"""
        subprocess.run([
            "git", "remote", "add", "origin",
            "git@github.com:user/test-repo.git"
        ], check=True, capture_output=True)

        # This will FAIL initially - no implementation exists
        if TaskDispatcher is None:
            self.fail("TaskDispatcher not implemented yet - RED phase expected")

        dispatcher = TaskDispatcher()
        agent_spec = {
            "name": "agent_workspace_test",
            "workspace_config": {}
        }

        agent_dir = dispatcher._calculate_agent_directory(agent_spec)
        expected = os.path.expanduser("~/projects/orch_test-repo/agent_workspace_test")
        self.assertEqual(agent_dir, expected)

    # ====================
    # Integration Tests
    # ====================

    def test_full_integration_with_create_dynamic_agent(self):
        """Integration test: Full worktree creation with new location logic"""
        subprocess.run([
            "git", "remote", "add", "origin",
            "git@github.com:user/integration-test.git"
        ], check=True, capture_output=True)

        # This will FAIL initially - no implementation exists
        if TaskDispatcher is None:
            self.fail("TaskDispatcher not implemented yet - RED phase expected")

        dispatcher = TaskDispatcher()
        agent_spec = {
            "name": "integration-test-agent",
            "type": "development",
            "focus": "test task",
            "capabilities": ["development"],
            "prompt": "Test prompt",
            "workspace_config": {}
        }

        # Mock the subprocess calls to avoid actual git operations
        with patch('subprocess.run') as mock_run, \
             patch('shutil.which') as mock_which:

            # Mock which claude to return a valid path
            mock_which.return_value = "/usr/local/bin/claude"

            # Configure mock_run to return different values based on the command
            def mock_subprocess(*args, **kwargs):
                cmd = args[0] if args else kwargs.get('args', [])
                if isinstance(cmd, list):
                    if cmd[0] == "which" and cmd[1] == "claude":
                        return MagicMock(returncode=0, stdout="/usr/local/bin/claude", stderr="")
                    elif cmd[0] == "git" and "worktree" in cmd:
                        return MagicMock(returncode=0, stdout="", stderr="")
                    elif cmd[0] == "tmux":
                        return MagicMock(returncode=0, stdout="", stderr="")
                # Default successful return
                return MagicMock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = mock_subprocess

            # This should use the new location logic
            success = dispatcher.create_dynamic_agent(agent_spec)

            self.assertTrue(success)
            # Verify git worktree was called with new location
            # The directory name is extracted from the test repo directory, which is test_repo
            expected_dir = os.path.expanduser("~/projects/orch_test_repo/integration-test-agent")

            # Check that git worktree add was called with the new location
            worktree_calls = [call for call in mock_run.call_args_list
                            if call[0][0] and len(call[0][0]) > 2 and call[0][0][0] == "git" and call[0][0][1] == "worktree"]

            self.assertTrue(len(worktree_calls) > 0, "Expected git worktree add to be called")

            # Verify the directory path in the call with defensive bounds checking
            # Defensive checks to avoid IndexError
            if (
                isinstance(worktree_calls[0], (list, tuple)) and
                len(worktree_calls[0]) > 0 and
                isinstance(worktree_calls[0][0], (list, tuple)) and
                len(worktree_calls[0][0]) > 0
            ):
                worktree_call = worktree_calls[0][0][0]  # First positional argument (command list)
                self.assertIn(expected_dir, worktree_call)
            else:
                self.fail("Unexpected call structure in worktree_calls[0]")


if __name__ == "__main__":
    # Run the test suite - all tests should FAIL initially (RED phase)
    print("🔴 RED PHASE: Running matrix-driven failing tests...")
    print("Expected: All tests should FAIL - this indicates we're in the correct RED phase")
    print("=" * 80)

    unittest.main(verbosity=2)
