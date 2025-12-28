#!/usr/bin/env python3
"""
Specific test for the agent name collision bug fix.
Verifies that custom workspace names properly prevent collisions and use correct cleanup names.
"""

import os
import time
import unittest
from unittest.mock import MagicMock, patch

from orchestration.task_dispatcher import TaskDispatcher


class TestCollisionBugFix(unittest.TestCase):
    """Test the specific agent name collision bug fix"""

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

    def test_original_collision_bug_scenario(self):
        """Test the exact scenario that caused the original bug"""
        # This is the scenario reported by the user:
        # "When a custom workspace name is used, the agent_name is reassigned within create_dynamic_agent.
        # This bypasses the initial collision detection for the final name"

        # Create a task with custom workspace name
        task = "Run copilot analysis on PR #1234 --workspace-name tmux-pr1234 --workspace-root /tmp/.worktrees"

        # Get agent specification
        with (
            patch("orchestration.task_dispatcher.shutil.which", return_value="/usr/bin/claude"),
            patch("orchestration.task_dispatcher.subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            agent_specs = self.dispatcher.analyze_task_and_create_agents(task)
        agent_spec = agent_specs[0]

        # Should have workspace config
        debug_info = f"agent_spec keys: {list(agent_spec.keys())}, agent_spec: {agent_spec}"
        self.assertIn("workspace_config", agent_spec, f"FAIL DEBUG: workspace_config missing. {debug_info}")
        workspace_config = agent_spec["workspace_config"]
        self.assertEqual(
            workspace_config["workspace_name"], "tmux-pr1234", f"FAIL DEBUG: wrong workspace_name. {debug_info}"
        )

        # The original agent name should be meaningful
        original_name = agent_spec["name"]
        debug_info = f"original_name={original_name}"
        self.assertIn("task-agent", original_name, f"FAIL DEBUG: expected task-agent in name. {debug_info}")

        # Mock existing agents to force collision with FINAL name
        with patch.object(self.dispatcher, "_check_existing_agents", return_value={"tmux-pr1234"}):
            with patch.object(self.dispatcher, "_active_agents", set()):
                with patch("orchestration.task_dispatcher.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(returncode=0)
                    with patch("os.makedirs"):
                        with patch("os.path.exists", return_value=True):
                            with patch("builtins.open", create=True):
                                # This should NOT fail - collision should be resolved
                                # Mock shutil.which to ensure claude is found in CI
                                with patch(
                                    "orchestration.task_dispatcher.shutil.which", return_value="/usr/bin/claude"
                                ):
                                    result = self.dispatcher.create_dynamic_agent(agent_spec)
                                debug_info = f"create_dynamic_agent result={result}"
                                self.assertTrue(result, f"FAIL DEBUG: expected True result. {debug_info}")

    def test_cleanup_uses_final_name(self):
        """Test that cleanup operations use the final resolved agent name"""
        task = "Run copilot analysis on PR #5678 --workspace-name tmux-pr5678"

        # Mock shutil.which before calling analyze_task_and_create_agents
        with (
            patch("orchestration.task_dispatcher.shutil.which", return_value="/usr/bin/claude"),
            patch("orchestration.task_dispatcher.subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            agent_specs = self.dispatcher.analyze_task_and_create_agents(task)
            agent_spec = agent_specs[0]

            # Mock the cleanup method to track what name is used
            with patch.object(self.dispatcher, "_cleanup_stale_prompt_files") as mock_cleanup:
                with patch("orchestration.task_dispatcher.subprocess.run") as mock_run:
                    mock_run.return_value = MagicMock(returncode=0)
                    with patch("os.makedirs"):
                        with patch("os.path.exists", return_value=True):
                            with patch("builtins.open", create=True):
                                self.dispatcher.create_dynamic_agent(agent_spec)

                                # Cleanup should be called with the final name (tmux-pr5678), not original
                                mock_cleanup.assert_called_once_with("tmux-pr5678")

    def test_workspace_alignment_prevents_confusion(self):
        """Test that agent name aligns with workspace name to prevent confusion"""
        task = "Update documentation --workspace-name custom-docs-workspace"

        # Mock shutil.which before calling analyze_task_and_create_agents
        with (
            patch("orchestration.task_dispatcher.shutil.which", return_value="/usr/bin/claude"),
            patch("orchestration.task_dispatcher.subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            agent_specs = self.dispatcher.analyze_task_and_create_agents(task)
            agent_spec = agent_specs[0]

            original_name = agent_spec["name"]
            workspace_name = agent_spec["workspace_config"]["workspace_name"]

            # When create_dynamic_agent runs, it should align the names
            with patch("orchestration.task_dispatcher.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0)
                with patch("os.makedirs"):
                    with patch("os.path.exists", return_value=True):
                        with patch("builtins.open", create=True):
                            # Capture the tmux command to verify agent name
                            result = self.dispatcher.create_dynamic_agent(agent_spec)
                            self.assertTrue(result)

                            # Check that tmux session was created with workspace name
                            tmux_calls = [call for call in mock_run.call_args_list if "tmux" in str(call)]
                            self.assertTrue(any("custom-docs-workspace" in str(call) for call in tmux_calls))

    def test_no_workspace_config_uses_original_behavior(self):
        """Test that agents without workspace config use original behavior"""
        task = "Run tests without workspace config"

        # Mock shutil.which before calling analyze_task_and_create_agents
        with (
            patch("orchestration.task_dispatcher.shutil.which", return_value="/usr/bin/claude"),
            patch("orchestration.task_dispatcher.subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            agent_specs = self.dispatcher.analyze_task_and_create_agents(task)
            agent_spec = agent_specs[0]

            # Should not have workspace config
            debug_info = f"agent_spec keys: {list(agent_spec.keys())}, agent_spec: {agent_spec}"
            self.assertNotIn("workspace_config", agent_spec, f"FAIL DEBUG: workspace_config found. {debug_info}")

            # Original name should be preserved
            original_name = agent_spec["name"]

            with patch.object(self.dispatcher, "_cleanup_stale_prompt_files") as mock_cleanup:
                with patch("orchestration.task_dispatcher.subprocess.run") as mock_run:
                    # Ensure no collisions are detected by returning empty stdout for tmux list-sessions
                    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
                    with patch("os.makedirs"):
                        with patch("os.path.exists", return_value=True):
                            with patch("builtins.open", create=True):
                                result = self.dispatcher.create_dynamic_agent(agent_spec)
                                self.assertTrue(result)

                                # Cleanup should use original name
                                debug_info = f"original_name={original_name}, mock_calls={mock_cleanup.call_args_list}"
                                try:
                                    mock_cleanup.assert_called_once_with(original_name)
                                except AssertionError as e:
                                    self.fail(f"FAIL DEBUG: {debug_info}. Original error: {e}")


if __name__ == "__main__":
    # Run tests to verify bug is fixed
    unittest.main(verbosity=2)
