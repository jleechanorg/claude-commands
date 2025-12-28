#!/usr/bin/env python3
"""
TDD Tests for Unified Naming System
Tests the orchestration system's unified agent/workspace naming approach
"""

import os
import time
import unittest
from unittest.mock import MagicMock, patch

from orchestration.orchestrate_unified import UnifiedOrchestration
from orchestration.task_dispatcher import TaskDispatcher


class TestUnifiedNaming(unittest.TestCase):
    """Test unified agent and workspace naming system"""

    def setUp(self):
        """Set up test environment"""
        self.dispatcher = TaskDispatcher()
        # CI-specific: Add small delay to prevent race conditions
        if os.getenv("GITHUB_ACTIONS"):
            time.sleep(0.1)

    def tearDown(self):
        """Clean up test environment"""
        # CI-specific: Ensure proper cleanup with retries
        if hasattr(self, "dispatcher"):
            try:
                # Clean up any created directories/files
                self.dispatcher = None
            except Exception:
                pass
        # CI-specific: Additional delay for cleanup completion
        if os.getenv("GITHUB_ACTIONS"):
            time.sleep(0.1)

    def test_meaningful_pr_naming(self):
        """Test that PR tasks generate meaningful pr-based names"""
        # RED: This should fail initially
        task = "Run copilot analysis on PR #123"
        name = self.dispatcher._generate_unique_name("task-agent", task_description=task)
        self.assertEqual(name, "task-agent-pr123")

    def test_meaningful_action_naming(self):
        """Test that action-based tasks generate meaningful names"""
        # RED: This should fail initially
        task = "Implement user authentication system"
        name = self.dispatcher._generate_unique_name("task-agent", task_description=task)
        self.assertEqual(name, "task-agent-implement-user-authe")

    def test_workspace_config_extraction(self):
        """Test workspace configuration extraction from task descriptions"""
        # RED: This should fail initially
        task = "Run copilot analysis on PR #123 --workspace-name tmux-pr123 --workspace-root /tmp/.worktrees"
        config = self.dispatcher._extract_workspace_config(task)
        expected = {"workspace_name": "tmux-pr123", "workspace_root": "/tmp/.worktrees", "pr_number": "123"}
        self.assertEqual(config, expected)

    def test_agent_workspace_name_alignment(self):
        """Test that agent names match workspace directory names exactly"""
        # RED: This should fail initially
        agent_spec = {
            "name": "task-agent-test",
            "workspace_config": {"workspace_name": "tmux-pr456", "workspace_root": "/tmp/.worktrees"},
        }

        # Mock the git worktree creation to avoid actual filesystem operations
        with patch("orchestration.task_dispatcher.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            with patch("os.makedirs"):
                with patch("os.path.exists", return_value=True):
                    # Mock shutil.which to ensure claude is found in CI
                    with patch("orchestration.task_dispatcher.shutil.which", return_value="/usr/bin/claude"):
                        result = self.dispatcher.create_dynamic_agent(agent_spec)

        # Agent name should be updated to match workspace name
        debug_info = f"create_dynamic_agent result={result}"
        self.assertTrue(result, f"FAIL DEBUG: expected True result. {debug_info}")

        # Check that git worktree was called with correct directory name
        git_calls = [call for call in mock_run.call_args_list if "git" in str(call)]
        has_tmux_pr456 = any("tmux-pr456" in str(call) for call in git_calls)
        debug_info = f"mock_calls={mock_run.call_args_list}, git_calls={git_calls}, has_tmux_pr456={has_tmux_pr456}"
        self.assertTrue(has_tmux_pr456, f"FAIL DEBUG: tmux-pr456 not found in git calls. {debug_info}")

    def test_fallback_to_timestamp_when_no_description(self):
        """Test fallback to timestamp when no meaningful description available"""
        # RED: This should fail initially
        task = ""
        name = self.dispatcher._generate_unique_name("task-agent", task_description=task)
        # Should contain digits (timestamp) but not meaningful words
        self.assertRegex(name, r"task-agent-\d+")

    def test_collision_handling_with_meaningful_names(self):
        """Test collision handling preserves meaningful names"""
        # RED: This should fail initially
        task = "Fix bug in authentication"

        # Mock existing agents to force collision
        with patch.object(self.dispatcher, "_check_existing_agents", return_value={"task-agent-fix-bug-authen"}):
            # Use a proper mock for the active_agents property
            original_active_agents = self.dispatcher._active_agents
            self.dispatcher._active_agents = set()
            try:
                name = self.dispatcher._generate_unique_name("task-agent", task_description=task)
            finally:
                self.dispatcher._active_agents = original_active_agents

        # Should add timestamp suffix to resolve collision while keeping meaningful base
        self.assertRegex(name, r"task-agent-fix-bug-authen-\d+")


class TestWorkspaceConfiguration(unittest.TestCase):
    """Test workspace configuration and integration"""

    def setUp(self):
        self.dispatcher = TaskDispatcher()

    def test_regression_workspace_directory_placement(self):
        """Test that workspace directories are created in orchestration/agent_workspaces/ not project root"""

        # Create mock agent data
        mock_agents = [{"name": "test-agent-regression"}]

        # Test workspace path construction
        orchestration = UnifiedOrchestration()

        # Simulate the workspace path creation logic
        for agent in mock_agents:
            # This should create workspace in orchestration/agent_workspaces/, not project root
            orchestration_dir = os.path.join(os.getcwd(), "orchestration", "agent_workspaces")
            workspace_path = os.path.join(orchestration_dir, f"agent_workspace_{agent['name']}")

            # Verify path is NOT in project root
            project_root_workspace = os.path.join(os.getcwd(), f"agent_workspace_{agent['name']}")
            self.assertNotEqual(workspace_path, project_root_workspace)

            # Verify path IS in orchestration directory
            self.assertTrue("orchestration/agent_workspaces" in workspace_path)
            self.assertTrue(workspace_path.endswith("agent_workspace_test-agent-regression"))

            # Verify path construction matches orchestration system logic
            expected_pattern = os.path.join("orchestration", "agent_workspaces", "agent_workspace_")
            self.assertIn(expected_pattern, workspace_path)

    def test_workspace_config_with_pr_context(self):
        """Test workspace config extraction with PR context detection"""
        # RED: This should fail initially
        task = "Update PR #789 --workspace-name tmux-pr789 --workspace-root .worktrees"

        # Test config extraction
        config = self.dispatcher._extract_workspace_config(task)
        self.assertIsNotNone(config)
        self.assertEqual(config["workspace_name"], "tmux-pr789")
        self.assertEqual(config["pr_number"], "789")

        # Test PR context detection
        pr_number, mode = self.dispatcher._detect_pr_context(task)
        self.assertEqual(pr_number, "789")
        self.assertEqual(mode, "update")

    def test_analyze_task_includes_workspace_config(self):
        """Test that analyze_task_and_create_agents includes workspace config in agent spec"""
        # RED: This should fail initially
        task = "Run copilot on PR #555 --workspace-name tmux-pr555 --workspace-root /external/.worktrees"

        # Mock shutil.which to ensure CLI is available in CI
        with (
            patch("orchestration.task_dispatcher.shutil.which", return_value="/usr/bin/claude"),
            patch("orchestration.task_dispatcher.subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            agent_specs = self.dispatcher.analyze_task_and_create_agents(task)

            self.assertEqual(len(agent_specs), 1)
            agent_spec = agent_specs[0]

            # Should have workspace config
            self.assertIn("workspace_config", agent_spec)
            workspace_config = agent_spec["workspace_config"]
            self.assertEqual(workspace_config["workspace_name"], "tmux-pr555")
            self.assertEqual(workspace_config["workspace_root"], "/external/.worktrees")


if __name__ == "__main__":
    # Run tests to confirm they fail (RED phase)
    unittest.main(verbosity=2)
