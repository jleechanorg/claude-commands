#!/usr/bin/env python3
"""
Unit tests for scripts/pair_monitor.py

Tests the background monitoring script for dual-agent pair sessions.
Mocks all external dependencies (subprocess, file I/O, tmux) for CI/local parity.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, mock_open, patch

# Add project root to Python path
project_root = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, project_root)

# Import the module under test
from scripts.pair_monitor import PairMonitor

PAIR_MONITOR_AVAILABLE = True


class TestPairMonitorInitialization(unittest.TestCase):
    """Test PairMonitor class initialization."""

    def setUp(self):
        """Set up test fixtures."""
        if not PAIR_MONITOR_AVAILABLE:
            self.skipTest("PairMonitor module not available")

    def test_initialization(self):
        """Test PairMonitor initializes with correct parameters."""
        with patch.object(Path, "mkdir"):
            monitor = PairMonitor(
                session_id="pair-test-123",
                coder_agent="claude-coder-pair-test-123",
                verifier_agent="codex-verifier-pair-test-123",
                bead_id="bd-test-123",
                max_iterations=5,
                interval=30,
            )

            self.assertEqual(monitor.session_id, "pair-test-123")
            self.assertEqual(monitor.coder_agent, "claude-coder-pair-test-123")
            self.assertEqual(monitor.verifier_agent, "codex-verifier-pair-test-123")
            self.assertEqual(monitor.bead_id, "bd-test-123")
            self.assertEqual(monitor.max_iterations, 5)
            self.assertEqual(monitor.interval, 30)

            # Verify tracking state initialized
            self.assertEqual(monitor.coder_iterations, 0)
            self.assertEqual(monitor.verifier_iterations, 0)
            self.assertIsNone(monitor.coder_last_progress)
            self.assertIsNone(monitor.verifier_last_progress)





class TestPairMonitorTmuxStatus(unittest.TestCase):
    """Test tmux session status checking."""

    def setUp(self):
        """Set up test fixtures."""
        if not PAIR_MONITOR_AVAILABLE:
            self.skipTest("PairMonitor module not available")

    def test_get_tmux_session_status_running(self):
        """Test detecting running tmux session."""
        with patch.object(Path, "mkdir"), patch("subprocess.run") as mock_run, patch(
            "scripts.pair_monitor.TMUX_BIN", "/usr/bin/tmux"
        ):

            # Mock tmux has-session (success) and capture-pane
            mock_run.side_effect = [
                MagicMock(returncode=0),  # has-session
                MagicMock(returncode=0, stdout="Agent is running..."),  # capture-pane
            ]

            monitor = PairMonitor(
                session_id="pair-test-123",
                coder_agent="coder",
                verifier_agent="verifier",
                bead_id="bd-123",
            )

            status = monitor.get_tmux_session_status("test-session")

            self.assertTrue(status["exists"])
            self.assertEqual(status["status"], "running")

    def test_get_tmux_session_status_completed(self):
        """Test detecting completed tmux session."""
        with patch.object(Path, "mkdir"), patch("subprocess.run") as mock_run, patch(
            "scripts.pair_monitor.TMUX_BIN", "/usr/bin/tmux"
        ):

            # Mock tmux output with completion indicator
            mock_run.side_effect = [
                MagicMock(returncode=0),  # has-session
                MagicMock(
                    returncode=0, stdout="Agent completed successfully\nExit"
                ),  # capture-pane
            ]

            monitor = PairMonitor(
                session_id="pair-test-123",
                coder_agent="coder",
                verifier_agent="verifier",
                bead_id="bd-123",
            )

            status = monitor.get_tmux_session_status("test-session")

            self.assertTrue(status["exists"])
            self.assertEqual(status["status"], "completed")

    def test_get_tmux_session_status_error(self):
        """Test detecting error in tmux session."""
        with patch.object(Path, "mkdir"), patch("subprocess.run") as mock_run, patch(
            "scripts.pair_monitor.TMUX_BIN", "/usr/bin/tmux"
        ):

            # Mock tmux output with error indicator
            mock_run.side_effect = [
                MagicMock(returncode=0),  # has-session
                MagicMock(
                    returncode=0,
                    stdout="Traceback (most recent call last):\nSome error",
                ),  # capture-pane
            ]

            monitor = PairMonitor(
                session_id="pair-test-123",
                coder_agent="coder",
                verifier_agent="verifier",
                bead_id="bd-123",
            )

            status = monitor.get_tmux_session_status("test-session")

            self.assertTrue(status["exists"])
            self.assertEqual(status["status"], "error")

    def test_get_tmux_session_status_not_found(self):
        """Test detecting non-existent tmux session."""
        with patch.object(Path, "mkdir"), patch("subprocess.run") as mock_run, patch(
            "scripts.pair_monitor.TMUX_BIN", "/usr/bin/tmux"
        ):

            # Mock tmux has-session failure
            mock_run.return_value = MagicMock(returncode=1)  # Session not found

            monitor = PairMonitor(
                session_id="pair-test-123",
                coder_agent="coder",
                verifier_agent="verifier",
                bead_id="bd-123",
            )

            status = monitor.get_tmux_session_status("test-session")

            self.assertFalse(status["exists"])
            self.assertEqual(status["status"], "not_found")

    def test_get_tmux_session_status_tmux_missing(self):
        """Test graceful handling when tmux is not installed."""
        with patch.object(Path, "mkdir"), patch(
            "scripts.pair_monitor.TMUX_BIN", None
        ):

            monitor = PairMonitor(
                session_id="pair-test-123",
                coder_agent="coder",
                verifier_agent="verifier",
                bead_id="bd-123",
            )

            status = monitor.get_tmux_session_status("test-session")

            self.assertFalse(status["exists"])
            self.assertEqual(status["status"], "tmux_missing")


class TestPairMonitorProgressTracking(unittest.TestCase):
    """Test agent progress tracking."""

    def setUp(self):
        """Set up test fixtures."""
        if not PAIR_MONITOR_AVAILABLE:
            self.skipTest("PairMonitor module not available")

    def test_check_progress_first_check(self):
        """Test progress check on first iteration (always True)."""
        with patch.object(Path, "mkdir"):
            monitor = PairMonitor(
                session_id="pair-test-123",
                coder_agent="coder",
                verifier_agent="verifier",
                bead_id="bd-123",
            )

            current_status = {"status": "running", "last_output": "Working..."}
            has_progress = monitor.check_progress("coder", current_status, None)

            self.assertTrue(has_progress)

    def test_check_progress_output_changed(self):
        """Test progress detected when output changes."""
        with patch.object(Path, "mkdir"):
            monitor = PairMonitor(
                session_id="pair-test-123",
                coder_agent="coder",
                verifier_agent="verifier",
                bead_id="bd-123",
            )

            last_status = {"status": "running", "last_output": "Working..."}
            current_status = {
                "status": "running",
                "last_output": "Working... step 2",
            }

            has_progress = monitor.check_progress("coder", current_status, last_status)

            self.assertTrue(has_progress)

    def test_check_progress_no_change(self):
        """Test no progress when output unchanged."""
        with patch.object(Path, "mkdir"):
            monitor = PairMonitor(
                session_id="pair-test-123",
                coder_agent="coder",
                verifier_agent="verifier",
                bead_id="bd-123",
            )

            last_status = {"status": "running", "last_output": "Working..."}
            current_status = {"status": "running", "last_output": "Working..."}

            has_progress = monitor.check_progress("coder", current_status, last_status)

            self.assertFalse(has_progress)

    def test_check_progress_completed(self):
        """Test progress detected when status changes to completed."""
        with patch.object(Path, "mkdir"):
            monitor = PairMonitor(
                session_id="pair-test-123",
                coder_agent="coder",
                verifier_agent="verifier",
                bead_id="bd-123",
            )

            last_status = {"status": "running", "last_output": "Working..."}
            current_status = {"status": "completed", "last_output": "Working..."}

            has_progress = monitor.check_progress("coder", current_status, last_status)

            self.assertTrue(has_progress)


class TestPairMonitorStuckAgentHandling(unittest.TestCase):
    """Test stuck agent detection and handling."""

    def setUp(self):
        """Set up test fixtures."""
        if not PAIR_MONITOR_AVAILABLE:
            self.skipTest("PairMonitor module not available")

    def test_handle_stuck_agent(self):
        """Test stuck agent warning and bead update."""
        with patch.object(Path, "mkdir"):
            monitor = PairMonitor(
                session_id="pair-test-123",
                coder_agent="coder",
                verifier_agent="verifier",
                bead_id="bd-123",
            )

            with patch.object(
                monitor, "send_mcp_mail"
            ) as mock_send, patch.object(monitor, "update_bead_status") as mock_update:

                monitor.handle_stuck_agent("coder", 3)

                # Verify warning sent
                mock_send.assert_called_once()
                call_args = mock_send.call_args
                self.assertEqual(call_args[1]["to"], "coder")
                self.assertEqual(call_args[1]["subject"], "TIMEOUT_WARNING")

                # Verify bead updated to blocked
                mock_update.assert_called_once_with("blocked")


class TestPairMonitorBeadOperations(unittest.TestCase):
    """Test Beads file operations."""

    def setUp(self):
        """Set up test fixtures."""
        if not PAIR_MONITOR_AVAILABLE:
            self.skipTest("PairMonitor module not available")

    def test_update_bead_status_success(self):
        """Test successful bead status update."""
        existing_beads = [
            {
                "id": "bd-123",
                "title": "Test Task",
                "status": "in_progress",
                "updated_at": "2024-01-01T00:00:00Z",
            }
        ]

        mock_read_data = "\n".join(json.dumps(bead) for bead in existing_beads)

        with patch.object(Path, "mkdir"), patch(
            "builtins.open", mock_open(read_data=mock_read_data)
        ) as mock_file, patch("pathlib.Path.exists") as mock_exists, patch(
            "fcntl.flock"
        ) as mock_flock, patch("os.fsync"):

            mock_exists.return_value = True

            monitor = PairMonitor(
                session_id="pair-test-123",
                coder_agent="coder",
                verifier_agent="verifier",
                bead_id="bd-123",
            )

            result = monitor.update_bead_status("completed")

            self.assertTrue(result)
            self.assertEqual(mock_flock.call_count, 2)

    def test_update_bead_status_file_not_found(self):
        """Test bead update when file doesn't exist."""
        with patch.object(Path, "mkdir"), patch(
            "pathlib.Path.exists"
        ) as mock_exists:

            mock_exists.return_value = False

            monitor = PairMonitor(
                session_id="pair-test-123",
                coder_agent="coder",
                verifier_agent="verifier",
                bead_id="bd-123",
            )

            result = monitor.update_bead_status("completed")

            self.assertFalse(result)


class TestPairMonitorRunIteration(unittest.TestCase):
    """Test monitoring iteration logic."""

    def setUp(self):
        """Set up test fixtures."""
        if not PAIR_MONITOR_AVAILABLE:
            self.skipTest("PairMonitor module not available")

    def test_run_iteration_both_completed(self):
        """Test iteration when both agents complete successfully."""
        with patch.object(Path, "mkdir"):
            monitor = PairMonitor(
                session_id="pair-test-123",
                coder_agent="coder",
                verifier_agent="verifier",
                bead_id="bd-123",
            )

            with patch.object(
                monitor, "get_tmux_session_status"
            ) as mock_status, patch.object(
                monitor, "update_bead_status"
            ) as mock_update_bead, patch.object(
                monitor, "update_status_file"
            ) as mock_update_file, patch.object(
                monitor, "send_mcp_mail"
            ):

                # Both agents completed
                mock_status.side_effect = [
                    {"exists": True, "status": "completed", "last_output": "Done"},
                    {"exists": True, "status": "completed", "last_output": "Done"},
                ]

                status = monitor.run_iteration()

                self.assertEqual(status, "completed")
                mock_update_bead.assert_called_with("completed")

    def test_run_iteration_agent_error(self):
        """Test iteration when agent encounters error."""
        with patch.object(Path, "mkdir"):
            monitor = PairMonitor(
                session_id="pair-test-123",
                coder_agent="coder",
                verifier_agent="verifier",
                bead_id="bd-123",
            )

            with patch.object(
                monitor, "get_tmux_session_status"
            ) as mock_status, patch.object(
                monitor, "update_bead_status"
            ) as mock_update_bead, patch.object(
                monitor, "update_status_file"
            ):

                # Coder has error
                mock_status.side_effect = [
                    {"exists": True, "status": "error", "last_output": "Traceback..."},
                    {"exists": True, "status": "running", "last_output": "Running"},
                ]

                status = monitor.run_iteration()

                self.assertEqual(status, "error")
                mock_update_bead.assert_called_with("failed")

    def test_run_iteration_max_iterations(self):
        """Test iteration when max iterations exceeded."""
        with patch.object(Path, "mkdir"):
            monitor = PairMonitor(
                session_id="pair-test-123",
                coder_agent="coder",
                verifier_agent="verifier",
                bead_id="bd-123",
                max_iterations=2,
            )

            # Simulate 2 iterations already done
            monitor.coder_iterations = 2

            with patch.object(
                monitor, "get_tmux_session_status"
            ) as mock_status, patch.object(
                monitor, "update_bead_status"
            ) as mock_update_bead, patch.object(
                monitor, "update_status_file"
            ), patch.object(
                monitor, "send_mcp_mail"
            ):

                # Both still running
                mock_status.side_effect = [
                    {"exists": True, "status": "running", "last_output": "Working"},
                    {"exists": True, "status": "running", "last_output": "Working"},
                ]

                status = monitor.run_iteration()

                self.assertEqual(status, "timeout")
                mock_update_bead.assert_called_with("timeout")

    def test_run_iteration_in_progress(self):
        """Test iteration when session still in progress."""
        with patch.object(Path, "mkdir"):
            monitor = PairMonitor(
                session_id="pair-test-123",
                coder_agent="coder",
                verifier_agent="verifier",
                bead_id="bd-123",
            )

            with patch.object(
                monitor, "get_tmux_session_status"
            ) as mock_status, patch.object(
                monitor, "update_bead_status"
            ) as mock_update_bead, patch.object(
                monitor, "update_status_file"
            ):

                # Both still running
                mock_status.side_effect = [
                    {"exists": True, "status": "running", "last_output": "Working"},
                    {"exists": True, "status": "running", "last_output": "Testing"},
                ]

                status = monitor.run_iteration()

                self.assertEqual(status, "in_progress")
                mock_update_bead.assert_called_with("implementation")


class TestPairMonitorSubprocessSecurity(unittest.TestCase):
    """Test subprocess security (no shell=True)."""

    def setUp(self):
        """Set up test fixtures."""
        if not PAIR_MONITOR_AVAILABLE:
            self.skipTest("PairMonitor module not available")

    def test_tmux_commands_no_shell_injection(self):
        """Test that tmux commands don't use shell=True."""
        with patch.object(Path, "mkdir"), patch("subprocess.run") as mock_run, patch(
            "shutil.which"
        ) as mock_which:

            mock_which.return_value = "/usr/bin/tmux"
            mock_run.return_value = MagicMock(returncode=0, stdout="output")

            monitor = PairMonitor(
                session_id="pair-test-123",
                coder_agent="coder",
                verifier_agent="verifier",
                bead_id="bd-123",
            )

            monitor.get_tmux_session_status("test-session")

            # Verify all subprocess.run calls use list arguments
            for call_args in mock_run.call_args_list:
                args, kwargs = call_args
                cmd = args[0]
                self.assertIsInstance(
                    cmd, list, "Subprocess calls must use list arguments"
                )
                # Verify no shell=True
                if "shell" in kwargs:
                    self.assertFalse(kwargs["shell"])

                # Verify timeout is set
                self.assertIn("timeout", kwargs)
                self.assertEqual(kwargs["timeout"], 30)


if __name__ == "__main__":
    unittest.main(verbosity=2)
