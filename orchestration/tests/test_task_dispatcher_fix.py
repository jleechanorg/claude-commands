#!/usr/bin/env python3
"""
Red-Green test for orchestration task dispatcher fix.
Verifies that the system creates general task agents instead of hardcoded test agents.
"""

import unittest
from unittest.mock import MagicMock, patch

from orchestration.task_dispatcher import TaskDispatcher


class TestTaskDispatcherFix(unittest.TestCase):
    """Test that task dispatcher creates appropriate agents for requested tasks."""

    def setUp(self):
        """Set up test dispatcher."""
        self.dispatcher = TaskDispatcher()

    def test_server_start_task_creates_general_agent(self):
        """Test that server start request creates general task agent, not test agent."""
        # RED: This would have failed before the fix
        task = "Start a test server on port 8082"
        # Mock shutil.which to ensure CLI is available in CI
        with (
            patch("orchestration.task_dispatcher.shutil.which", return_value="/usr/bin/claude"),
            patch("orchestration.task_dispatcher.subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            agents = self.dispatcher.analyze_task_and_create_agents(task)

        # Should create exactly one agent
        assert len(agents) == 1

        # Should be a general task agent, not test-analyzer or test-writer
        agent = agents[0]
        assert "task-agent" in agent["name"]
        assert "test-analyzer" not in agent["name"]
        assert "test-writer" not in agent["name"]

        # Should have the exact task as focus
        assert agent["focus"] == task

        # Should have general capabilities
        assert "task_execution" in agent["capabilities"]
        assert "server_management" in agent["capabilities"]

    def test_testserver_command_creates_general_agent(self):
        """Test that /testserver command creates general agent."""
        task = "tell the agent to start the test server on 8082 instead"
        # Mock shutil.which to ensure CLI is available in CI
        with (
            patch("orchestration.task_dispatcher.shutil.which", return_value="/usr/bin/claude"),
            patch("orchestration.task_dispatcher.subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            agents = self.dispatcher.analyze_task_and_create_agents(task)

        # Should not create test coverage agents
        assert len(agents) == 1
        agent = agents[0]
        assert "test-analyzer" not in agent["name"]
        assert "test-writer" not in agent["name"]
        assert "coverage" not in agent["focus"].lower()

    def test_copilot_task_creates_general_agent(self):
        """Test that copilot tasks create general agents."""
        task = "run /copilot on PR 825"
        # Mock shutil.which to ensure CLI is available in CI
        with (
            patch("orchestration.task_dispatcher.shutil.which", return_value="/usr/bin/claude"),
            patch("orchestration.task_dispatcher.subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            agents = self.dispatcher.analyze_task_and_create_agents(task)

        # Should create general task agent
        assert len(agents) == 1
        agent = agents[0]
        assert "task-agent" in agent["name"]
        assert agent["focus"] == task

    def test_no_hardcoded_patterns(self):
        """Test that various tasks all create general agents, not pattern-matched types."""
        test_tasks = [
            "Start server on port 6006",
            "Run copilot analysis",
            "Execute test server with production mode",
            "Modify testserver command to use prod mode",
            "Update configuration files",
            "Create a new feature",
            "Fix a bug in the system",
            "Write documentation",
        ]

        for task in test_tasks:
            with self.subTest(task=task):
                # Mock shutil.which to ensure CLI is available in CI
                with (
                    patch("orchestration.task_dispatcher.shutil.which", return_value="/usr/bin/claude"),
                    patch("orchestration.task_dispatcher.subprocess.run") as mock_run,
                ):
                    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
                    agents = self.dispatcher.analyze_task_and_create_agents(task)

                    # All tasks should create single general agent
                    assert len(agents) == 1
                    agent = agents[0]

                    # Should always be task-agent, never specialized types
                    assert "task-agent" in agent["name"]
                    assert "test-analyzer" not in agent["name"]
                    assert "test-writer" not in agent["name"]
                    assert "security-scanner" not in agent["name"]
                    assert "frontend-developer" not in agent["name"]
                    assert "backend-developer" not in agent["name"]

                    # Focus should be the exact task
                    assert agent["focus"] == task


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
