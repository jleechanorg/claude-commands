#!/usr/bin/env python3
"""
Red-Green test for orchestration task dispatcher fix.
Verifies that the system creates general task agents instead of hardcoded test agents.
"""

import os
import sys
import unittest

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from task_dispatcher import TaskDispatcher


class TestTaskDispatcherFix(unittest.TestCase):
    """Test that task dispatcher creates appropriate agents for requested tasks."""

    def setUp(self):
        """Set up test dispatcher."""
        self.dispatcher = TaskDispatcher()

    def test_server_start_task_creates_general_agent(self):
        """Test that server start request creates general task agent, not test agent."""
        # RED: This would have failed before the fix
        task = "Start a test server on port 8082"
        agents = self.dispatcher.analyze_task_and_create_agents(task)

        # Should create exactly one agent
        self.assertEqual(len(agents), 1)

        # Should be a general task agent, not test-analyzer or test-writer
        agent = agents[0]
        self.assertIn("task-agent", agent["name"])
        self.assertNotIn("test-analyzer", agent["name"])
        self.assertNotIn("test-writer", agent["name"])

        # Should have the exact task as focus
        self.assertEqual(agent["focus"], task)

        # Should have general capabilities
        self.assertIn("task_execution", agent["capabilities"])
        self.assertIn("server_management", agent["capabilities"])

    def test_testserver_command_creates_general_agent(self):
        """Test that /testserver command creates general agent."""
        task = "tell the agent to start the test server on 8082 instead"
        agents = self.dispatcher.analyze_task_and_create_agents(task)

        # Should not create test coverage agents
        self.assertEqual(len(agents), 1)
        agent = agents[0]
        self.assertNotIn("test-analyzer", agent["name"])
        self.assertNotIn("test-writer", agent["name"])
        self.assertNotIn("coverage", agent["focus"].lower())

    def test_copilot_task_creates_general_agent(self):
        """Test that copilot tasks create general agents."""
        task = "run /copilot on PR 825"
        agents = self.dispatcher.analyze_task_and_create_agents(task)

        # Should create general task agent
        self.assertEqual(len(agents), 1)
        agent = agents[0]
        self.assertIn("task-agent", agent["name"])
        self.assertEqual(agent["focus"], task)

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
            "Write documentation"
        ]

        for task in test_tasks:
            with self.subTest(task=task):
                agents = self.dispatcher.analyze_task_and_create_agents(task)

                # All tasks should create single general agent
                self.assertEqual(len(agents), 1)
                agent = agents[0]

                # Should always be task-agent, never specialized types
                self.assertIn("task-agent", agent["name"])
                self.assertNotIn("test-analyzer", agent["name"])
                self.assertNotIn("test-writer", agent["name"])
                self.assertNotIn("security-scanner", agent["name"])
                self.assertNotIn("frontend-developer", agent["name"])
                self.assertNotIn("backend-developer", agent["name"])

                # Focus should be the exact task
                self.assertEqual(agent["focus"], task)


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
