#!/usr/bin/env python3
"""
Unit tests for orchestrate.py command.

Tests:
- Dynamic agent status detection
- Agent cleanup functionality
- Status display improvements
"""

import os
import sys
import unittest
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrate import OrchestrationCLI


class TestOrchestrateCLI(unittest.TestCase):
    """Test orchestration CLI improvements."""

    def setUp(self):
        """Set up test fixtures."""
        self.cli = OrchestrationCLI()

    @patch("subprocess.run")
    def test_dynamic_agent_detection(self, mock_run):
        """Test that status detection works with dynamic agent names."""
        # Mock Redis ping success
        redis_result = Mock()
        redis_result.returncode = 0
        redis_result.stdout = "PONG"

        # Mock tmux sessions with intelligent agents
        tmux_result = Mock()
        tmux_result.returncode = 0
        tmux_result.stdout = """github-api-agent: 1 windows (created Thu Jul 17 13:23:38 2025)
processing-agent: 1 windows (created Thu Jul 17 13:23:40 2025)
genai-docs-agent: 1 windows (created Thu Jul 17 14:02:05 2025)
frontend-agent: 1 windows (created Thu Jul 17 13:49:48 2025)"""

        mock_run.side_effect = [redis_result, tmux_result]

        # Test that orchestration is detected as running
        self.assertTrue(self.cli.is_orchestration_running())

        # Verify correct command calls
        mock_run.assert_any_call(
            ["redis-cli", "ping"], capture_output=True, text=True, timeout=5
        )
        mock_run.assert_any_call(
            ["tmux", "list-sessions"], capture_output=True, text=True, timeout=5
        )

    @patch("subprocess.run")
    def test_agent_cleanup_stuck_detection(self, mock_run):
        """Test agent cleanup detects stuck agents correctly."""
        # Mock tmux list-sessions
        list_result = Mock()
        list_result.returncode = 0
        list_result.stdout = "github-api-agent: 1 windows\nprocessing-agent: 1 windows"

        # Mock capture-pane with stuck output
        capture_result1 = Mock()
        capture_result1.returncode = 0
        capture_result1.stdout = "Do you want to proceed?\n❯ 1. Yes"

        capture_result2 = Mock()
        capture_result2.returncode = 0
        capture_result2.stdout = "Context low (NaN% remaining)"

        # Mock send-keys (no output expected)
        send_result = Mock()
        send_result.returncode = 0

        mock_run.side_effect = [
            list_result,
            capture_result1,
            send_result,
            capture_result2,
            send_result,
        ]

        result = self.cli._cleanup_agents()

        # Verify cleanup report contains expected content
        self.assertIn("Agent Cleanup Report", result)
        self.assertIn("github-api-agent", result)
        self.assertIn("processing-agent", result)
        self.assertIn("Unstuck", result)

        # Verify send-keys was called to unstick agents
        self.assertEqual(mock_run.call_count, 5)

    @patch("subprocess.run")
    def test_agent_cleanup_inactive_detection(self, mock_run):
        """Test cleanup detects inactive agents."""
        # Mock tmux list-sessions
        list_result = Mock()
        list_result.returncode = 0
        list_result.stdout = "inactive-agent: 1 windows"

        # Mock capture-pane with empty output (inactive)
        capture_result = Mock()
        capture_result.returncode = 0
        capture_result.stdout = ""  # Empty output indicates inactive

        mock_run.side_effect = [list_result, capture_result]

        result = self.cli._cleanup_agents()

        # Verify inactive agent detected
        self.assertIn("Inactive", result)
        self.assertIn("inactive-agent", result)
        self.assertIn("< 10 chars output", result)  # Uses INACTIVITY_THRESHOLD

    @patch("subprocess.run")
    def test_agent_cleanup_active_detection(self, mock_run):
        """Test cleanup correctly identifies active working agents."""
        # Mock tmux list-sessions
        list_result = Mock()
        list_result.returncode = 0
        list_result.stdout = "active-agent: 1 windows"

        # Mock capture-pane with active output
        capture_result = Mock()
        capture_result.returncode = 0
        capture_result.stdout = (
            "Processing task: Implementing user authentication...\n"
            + "✅ Created auth module\n"
            + "🔄 Writing tests..."
        )

        mock_run.side_effect = [list_result, capture_result]

        result = self.cli._cleanup_agents()

        # Verify active agent detected correctly
        self.assertIn("Active and working", result)
        self.assertIn("active-agent", result)

    @patch("subprocess.run")
    def test_cleanup_handles_tmux_errors(self, mock_run):
        """Test cleanup handles tmux errors gracefully."""
        # Mock tmux list-sessions failure
        list_result = Mock()
        list_result.returncode = 1
        list_result.stdout = ""

        mock_run.side_effect = [list_result]

        result = self.cli._cleanup_agents()

        # Should return error message, not crash
        self.assertIn("No tmux sessions found", result)

    @patch("subprocess.run")
    def test_cleanup_handles_capture_errors(self, mock_run):
        """Test cleanup handles individual agent capture errors."""
        # Mock successful list
        list_result = Mock()
        list_result.returncode = 0
        list_result.stdout = "error-agent: 1 windows"

        # Mock capture failure
        mock_run.side_effect = [list_result, Exception("tmux error")]

        result = self.cli._cleanup_agents()

        # Should report error for specific agent
        self.assertIn("Error checking", result)
        self.assertIn("error-agent", result)

    @patch("subprocess.run")
    @patch.object(OrchestrationCLI, "connect_to_broker")
    def test_status_display_improvements(self, mock_connect, mock_run):
        """Test status display shows both legacy and intelligent agents."""
        # Mock broker connection
        mock_connect.return_value = True
        self.cli.broker = Mock()
        self.cli.broker.redis_client.ping.return_value = True

        # Mock tmux list-sessions for agent detection
        tmux_status = Mock()
        tmux_status.returncode = 0
        tmux_status.stdout = """github-api-agent: 1 windows (created Thu Jul 17 13:23:38 2025)
frontend-agent: 1 windows (created Thu Jul 17 13:49:48 2025)"""

        mock_run.side_effect = [tmux_status]

        # Mock file operations for task counting
        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.readlines.return_value = [
                "task1\n",
                "task2\n",
            ]

            status = self.cli._check_status()

            # Verify key status elements
            self.assertIn("Real Claude Agent Orchestration Status", status)
            self.assertIn("Redis: ✅ Connected", status)
            self.assertIn("Active Claude Agents:", status)
            self.assertIn("Task Queue Status", status)

    def test_configuration_constants(self):
        """Test that configuration constants are properly defined."""
        # Import the module to check constants
        import orchestrate

        # Verify all constants exist
        self.assertTrue(hasattr(orchestrate, "DEFAULT_UNSTICK_OPTION"))
        self.assertTrue(hasattr(orchestrate, "INACTIVITY_THRESHOLD"))
        self.assertTrue(hasattr(orchestrate, "STUCK_PATTERNS"))
        self.assertTrue(hasattr(orchestrate, "TMUX_TIMEOUT"))

        # Verify types and values
        self.assertEqual(orchestrate.DEFAULT_UNSTICK_OPTION, "1")
        self.assertEqual(orchestrate.INACTIVITY_THRESHOLD, 10)
        self.assertIsInstance(orchestrate.STUCK_PATTERNS, list)
        self.assertGreater(len(orchestrate.STUCK_PATTERNS), 0)

    def test_unstick_patterns_comprehensive(self):
        """Test all patterns that indicate a stuck agent."""
        import orchestrate

        stuck_outputs = [
            "Do you want to proceed?",
            "Context low (NaN% remaining)",
            "❯ 1. Yes",
            "❯ 2. Yes, and don't ask again",
            "Do you want to proceed?\n❯ 1. Yes\n  2. No",
        ]

        for output in stuck_outputs:
            is_stuck = any(pattern in output for pattern in orchestrate.STUCK_PATTERNS)
            self.assertTrue(is_stuck, f"Failed to detect stuck pattern in: {output}")


if __name__ == "__main__":
    unittest.main()
