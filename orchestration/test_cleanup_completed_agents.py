#!/usr/bin/env python3
"""
Test suite for cleanup_completed_agents.py

Following TDD methodology - tests written before/during implementation.
"""

import json
import os
import tempfile
import time
import unittest
from unittest.mock import MagicMock, mock_open, patch

from .cleanup_completed_agents import (
    IDLE_MINUTES_THRESHOLD,
    check_agent_completion,
    cleanup_agent_session,
    cleanup_completed_agents,
    get_task_agent_sessions,
    get_tmux_sessions,
)


class TestTmuxSessionHandling(unittest.TestCase):
    """Test tmux session discovery and filtering."""

    @patch('cleanup_completed_agents.subprocess.run')
    def test_get_tmux_sessions_success(self, mock_run):
        """Test successful tmux session listing."""
        mock_run.return_value.stdout = "session1\nsession2\ntask-agent-123\n"
        mock_run.return_value.returncode = 0

        sessions = get_tmux_sessions()

        self.assertEqual(sessions, ["session1", "session2", "task-agent-123"])
        mock_run.assert_called_once_with(
            ["tmux", "list-sessions", "-F", "#{session_name}"],
            capture_output=True,
            text=True,
            check=True
        )

    @patch('cleanup_completed_agents.subprocess.run')
    def test_get_tmux_sessions_failure(self, mock_run):
        """Test tmux session listing failure."""
        mock_run.side_effect = Exception("tmux not running")

        sessions = get_tmux_sessions()

        self.assertEqual(sessions, [])

    @patch('cleanup_completed_agents.get_tmux_sessions')
    def test_get_task_agent_sessions_filtering(self, mock_get_sessions):
        """Test filtering for task-agent sessions only."""
        mock_get_sessions.return_value = [
            "main-session",
            "task-agent-123",
            "task-agent-456",
            "other-session",
            "task-agent-789"
        ]

        task_sessions = get_task_agent_sessions()

        expected = ["task-agent-123", "task-agent-456", "task-agent-789"]
        self.assertEqual(task_sessions, expected)


class TestAgentCompletionDetection(unittest.TestCase):
    """Test agent completion detection logic."""

    def test_check_agent_completion_no_log_file(self):
        """Test behavior when log file doesn't exist."""
        result = check_agent_completion("nonexistent-agent")

        self.assertFalse(result["completed"])
        self.assertEqual(result["reason"], "no_log_file")

    @patch('cleanup_completed_agents.os.path.exists')
    @patch('cleanup_completed_agents.subprocess.run')
    def test_check_agent_completion_success_marker(self, mock_run, mock_exists):
        """Test completion detection via success marker."""
        mock_exists.return_value = True
        mock_run.return_value.stdout = "Some log content\nClaude exit code: 0\nEnd of log"

        result = check_agent_completion("test-agent")

        self.assertTrue(result["completed"])
        self.assertIn("found_marker", result["reason"])
        self.assertIn("Claude exit code: 0", result["reason"])

    @patch('cleanup_completed_agents.os.path.exists')
    @patch('cleanup_completed_agents.subprocess.run')
    @patch('cleanup_completed_agents.os.stat')
    @patch('cleanup_completed_agents.time.time')
    def test_check_agent_completion_idle_detection(self, mock_time, mock_stat, mock_run, mock_exists):
        """Test completion detection via idle time."""
        mock_exists.return_value = True
        mock_run.return_value.stdout = "Some log content without completion markers"

        # Mock file stats - 35 minutes ago (past 30 min threshold)
        mock_stat_result = MagicMock()
        mock_stat_result.st_mtime = 1000
        mock_stat.return_value = mock_stat_result
        mock_time.return_value = 1000 + (35 * 60)  # 35 minutes later

        result = check_agent_completion("test-agent")

        self.assertTrue(result["completed"])
        self.assertIn("idle_for", result["reason"])

    @patch('cleanup_completed_agents.os.path.exists')
    @patch('cleanup_completed_agents.subprocess.run')
    @patch('cleanup_completed_agents.os.stat')
    @patch('cleanup_completed_agents.time.time')
    def test_check_agent_completion_still_active(self, mock_time, mock_stat, mock_run, mock_exists):
        """Test detection of still active agent."""
        mock_exists.return_value = True
        mock_run.return_value.stdout = "Recent log content without completion markers"

        # Mock recent file activity - 10 minutes ago (within 30 min threshold)
        mock_stat_result = MagicMock()
        mock_stat_result.st_mtime = 1000
        mock_stat.return_value = mock_stat_result
        mock_time.return_value = 1000 + (10 * 60)  # 10 minutes later

        result = check_agent_completion("test-agent")

        self.assertFalse(result["completed"])
        self.assertEqual(result["reason"], "still_active")


class TestAgentCleanup(unittest.TestCase):
    """Test agent cleanup operations."""

    @patch('cleanup_completed_agents.subprocess.run')
    def test_cleanup_agent_session_success(self, mock_run):
        """Test successful agent session cleanup."""
        mock_run.return_value.returncode = 0

        result = cleanup_agent_session("test-agent", dry_run=False)

        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ["tmux", "kill-session", "-t", "test-agent"],
            check=True
        )

    @patch('cleanup_completed_agents.subprocess.run')
    def test_cleanup_agent_session_failure(self, mock_run):
        """Test failed agent session cleanup."""
        mock_run.side_effect = Exception("Session not found")

        result = cleanup_agent_session("test-agent", dry_run=False)

        self.assertFalse(result)

    def test_cleanup_agent_session_dry_run(self):
        """Test dry run mode doesn't execute actual cleanup."""
        result = cleanup_agent_session("test-agent", dry_run=True)

        self.assertTrue(result)
        # No subprocess calls should be made in dry run


class TestCleanupWorkflow(unittest.TestCase):
    """Test the main cleanup workflow."""

    @patch('cleanup_completed_agents.get_task_agent_sessions')
    @patch('cleanup_completed_agents.check_agent_completion')
    @patch('cleanup_completed_agents.cleanup_agent_session')
    def test_cleanup_completed_agents_mixed_results(self, mock_cleanup, mock_check, mock_get_sessions):
        """Test cleanup with mix of completed and active agents."""
        # Setup mocks
        mock_get_sessions.return_value = ["agent-1", "agent-2", "agent-3"]
        mock_check.side_effect = [
            {"completed": True, "reason": "found_marker: Claude exit code: 0"},
            {"completed": False, "reason": "still_active"},
            {"completed": True, "reason": "idle_for_45.0_minutes"}
        ]
        mock_cleanup.return_value = True

        results = cleanup_completed_agents(dry_run=True)

        # Verify results structure
        self.assertEqual(results["total_sessions"], 3)
        self.assertEqual(results["completed"], 2)
        self.assertEqual(results["active"], 1)
        self.assertEqual(len(results["completed_agents"]), 2)
        self.assertEqual(len(results["active_agents"]), 1)

        # Verify completed agents details
        completed_names = [agent["name"] for agent in results["completed_agents"]]
        self.assertIn("agent-1", completed_names)
        self.assertIn("agent-3", completed_names)

        # Verify active agents details
        active_names = [agent["name"] for agent in results["active_agents"]]
        self.assertIn("agent-2", active_names)


class TestConstants(unittest.TestCase):
    """Test that constants are properly imported and used."""

    def test_idle_threshold_import(self):
        """Test that IDLE_MINUTES_THRESHOLD is properly imported."""
        self.assertIsInstance(IDLE_MINUTES_THRESHOLD, int)
        self.assertGreater(IDLE_MINUTES_THRESHOLD, 0)


if __name__ == '__main__':
    unittest.main()
