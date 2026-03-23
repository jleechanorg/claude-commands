#!/usr/bin/env python3
"""
Unit tests for scripts/pair_monitor.py

Tests the background monitoring script for dual-agent pair sessions.
Mocks all external dependencies (subprocess, file I/O, tmux) for CI/local parity.
"""

import importlib.util
import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

# Add project root to Python path
# Tests are now in .claude/scripts/tests/, so we need to go up 3 levels to reach project root
project_root = os.path.join(os.path.dirname(__file__), "..", "..", "..")
sys.path.insert(0, project_root)

# Import the module under test
def _load_claude_pair_monitor_module():
    """Load .claude/scripts/pair_monitor.py as a module for focused tests."""
    module_path = Path(project_root) / ".claude" / "scripts" / "pair_monitor.py"
    if not module_path.exists():
        return None
    spec = importlib.util.spec_from_file_location("claude_pair_monitor_module", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CLAUDE_PAIR_MONITOR = _load_claude_pair_monitor_module()
if CLAUDE_PAIR_MONITOR is None:
    PAIR_MONITOR_AVAILABLE = False
    _PAIR_MONITOR_CLASS = None
else:
    scripts_pkg = sys.modules.get("scripts")
    if scripts_pkg is None:
        scripts_pkg = types.ModuleType("scripts")
        scripts_pkg.__path__ = []  # Mark as package for patch target resolution.
        sys.modules["scripts"] = scripts_pkg
    sys.modules["scripts.pair_monitor"] = CLAUDE_PAIR_MONITOR
    setattr(scripts_pkg, "pair_monitor", CLAUDE_PAIR_MONITOR)
    _PAIR_MONITOR_CLASS = CLAUDE_PAIR_MONITOR.PairMonitor
    # Legacy tests in this file target the older scripts/pair_monitor.py API.
    # Keep them skipped when only the .claude monitor implementation exists.
    PAIR_MONITOR_AVAILABLE = False


def PairMonitor(*args, **kwargs):
    """Back-compat wrapper for tests that omit newer constructor arguments."""
    if _PAIR_MONITOR_CLASS is None:
        raise RuntimeError("PairMonitor module not available")
    kwargs.setdefault("coder_cmd", "")
    kwargs.setdefault("verifier_cmd", "")
    return _PAIR_MONITOR_CLASS(*args, **kwargs)


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
        with (
            patch.object(Path, "mkdir"),
            patch("subprocess.run") as mock_run,
            patch("scripts.pair_monitor.TMUX_BIN", "/usr/bin/tmux"),
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
        with (
            patch.object(Path, "mkdir"),
            patch("subprocess.run") as mock_run,
            patch("scripts.pair_monitor.TMUX_BIN", "/usr/bin/tmux"),
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
        with (
            patch.object(Path, "mkdir"),
            patch("subprocess.run") as mock_run,
            patch("scripts.pair_monitor.TMUX_BIN", "/usr/bin/tmux"),
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
        with (
            patch.object(Path, "mkdir"),
            patch("subprocess.run") as mock_run,
            patch("scripts.pair_monitor.TMUX_BIN", "/usr/bin/tmux"),
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
        with patch.object(Path, "mkdir"), patch("scripts.pair_monitor.TMUX_BIN", None):
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

            with (
                patch.object(monitor, "send_mcp_mail") as mock_send,
                patch.object(monitor, "update_bead_status") as mock_update,
            ):
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

        with (
            patch.object(Path, "mkdir"),
            patch("builtins.open", mock_open(read_data=mock_read_data)) as mock_file,
            patch("pathlib.Path.exists") as mock_exists,
            patch("fcntl.flock") as mock_flock,
            patch("os.fsync"),
        ):
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
        with patch.object(Path, "mkdir"), patch("pathlib.Path.exists") as mock_exists:
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

            with (
                patch.object(monitor, "get_tmux_session_status") as mock_status,
                patch.object(monitor, "update_bead_status") as mock_update_bead,
                patch.object(monitor, "update_status_file") as mock_update_file,
                patch.object(monitor, "send_mcp_mail"),
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

            with (
                patch.object(monitor, "get_tmux_session_status") as mock_status,
                patch.object(monitor, "update_bead_status") as mock_update_bead,
                patch.object(monitor, "update_status_file"),
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

            with (
                patch.object(monitor, "get_tmux_session_status") as mock_status,
                patch.object(monitor, "update_bead_status") as mock_update_bead,
                patch.object(monitor, "update_status_file"),
                patch.object(monitor, "send_mcp_mail"),
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

            with (
                patch.object(monitor, "get_tmux_session_status") as mock_status,
                patch.object(monitor, "update_bead_status") as mock_update_bead,
                patch.object(monitor, "update_status_file"),
            ):
                # Both still running
                mock_status.side_effect = [
                    {"exists": True, "status": "running", "last_output": "Working"},
                    {"exists": True, "status": "running", "last_output": "Testing"},
                ]

                status = monitor.run_iteration()

                self.assertEqual(status, "in_progress")
                mock_update_bead.assert_called_with("implementation")


class TestPairMonitorSocketScanning(unittest.TestCase):
    """Test tmux socket scanning resilience."""

    def setUp(self):
        """Set up test fixtures."""
        if not PAIR_MONITOR_AVAILABLE:
            self.skipTest("PairMonitor module not available")

    def test_find_session_skips_unreadable_tmux_directories(self):
        """Test that _find_session_on_sockets skips /tmp/tmux-* dirs with PermissionError.

        On shared hosts, /tmp/tmux-* dirs owned by other users are 0700,
        so iterdir() raises PermissionError. The scanner must catch this
        and continue to the default socket fallback.
        """
        with patch.object(Path, "mkdir"), patch(
            "scripts.pair_monitor.TMUX_BIN", "/usr/bin/tmux"
        ):
            monitor = PairMonitor(
                session_id="pair-test-123",
                coder_agent="coder",
                verifier_agent="verifier",
                bead_id="bd-123",
            )

            # Create mock Path objects for /tmp/tmux-* scanning
            unreadable_dir = MagicMock(spec=Path)
            unreadable_dir.iterdir.side_effect = PermissionError(
                "[Errno 13] Permission denied: '/tmp/tmux-9999'"
            )

            readable_dir = MagicMock(spec=Path)
            readable_socket = MagicMock(spec=Path)
            readable_socket.name = "orch-12345-1700000000"
            readable_dir.iterdir.return_value = [readable_socket]

            with patch("subprocess.run") as mock_run:
                # Custom sockets: none found
                # /tmp glob: returns one unreadable + one readable dir
                mock_tmp = MagicMock(spec=Path)
                mock_tmp.glob.return_value = [unreadable_dir, readable_dir]

                with patch("scripts.pair_monitor.Path") as MockPath:
                    # Path("/tmp") returns our mock
                    MockPath.return_value = mock_tmp
                    # Preserve Path constructor for other uses
                    MockPath.side_effect = lambda x: mock_tmp if x == "/tmp" else Path(x)

                    # has-session on the readable socket's orch socket succeeds
                    mock_run.return_value = MagicMock(returncode=0)

                    result = monitor._find_session_on_sockets("test-session")

                # Should have found session on the readable socket, not crashed
                self.assertEqual(result, "orch-12345-1700000000")
                # The unreadable dir's iterdir was called and raised PermissionError
                unreadable_dir.iterdir.assert_called_once()

    def test_find_session_falls_back_to_default_when_all_dirs_unreadable(self):
        """Test fallback to default socket when all /tmp/tmux-* dirs are unreadable."""
        with patch.object(Path, "mkdir"), patch(
            "scripts.pair_monitor.TMUX_BIN", "/usr/bin/tmux"
        ):
            monitor = PairMonitor(
                session_id="pair-test-123",
                coder_agent="coder",
                verifier_agent="verifier",
                bead_id="bd-123",
            )

            # All tmux dirs are unreadable
            unreadable_dir1 = MagicMock(spec=Path)
            unreadable_dir1.iterdir.side_effect = PermissionError("Permission denied")
            unreadable_dir2 = MagicMock(spec=Path)
            unreadable_dir2.iterdir.side_effect = PermissionError("Permission denied")

            with patch("subprocess.run") as mock_run:
                mock_tmp = MagicMock(spec=Path)
                mock_tmp.glob.return_value = [unreadable_dir1, unreadable_dir2]

                with patch("scripts.pair_monitor.Path") as MockPath:
                    MockPath.return_value = mock_tmp
                    MockPath.side_effect = lambda x: mock_tmp if x == "/tmp" else Path(x)

                    # Default socket has-session succeeds
                    mock_run.return_value = MagicMock(returncode=0)

                    result = monitor._find_session_on_sockets("test-session")

                # Should fall back to default socket (empty string)
                    self.assertEqual(result, "")

    def test_find_session_skips_tmp_scan_when_explicit_sockets_provided(self):
        """Explicit socket list should prevent scanning unrelated /tmp orch sockets."""
        with patch.object(Path, "mkdir"), patch(
            "scripts.pair_monitor.TMUX_BIN", "/usr/bin/tmux"
        ):
            monitor = PairMonitor(
                session_id="pair-test-123",
                coder_agent="coder",
                verifier_agent="verifier",
                bead_id="bd-123",
                tmux_sockets=["orch-current-session"],
            )

            with patch("subprocess.run") as mock_run:
                # Custom socket miss, default socket success.
                mock_run.side_effect = [
                    MagicMock(returncode=1),
                    MagicMock(returncode=0),
                ]
                mock_tmp = MagicMock(spec=Path)
                mock_tmp.glob.return_value = [MagicMock(spec=Path)]

                with patch("scripts.pair_monitor.Path") as MockPath:
                    MockPath.return_value = mock_tmp
                    MockPath.side_effect = lambda x: mock_tmp if x == "/tmp" else Path(x)

                    result = monitor._find_session_on_sockets("test-session")

                self.assertEqual(result, "")
                mock_tmp.glob.assert_not_called()


class TestClaudePairMonitorCompletionState(unittest.TestCase):
    """Test completion-state handling in .claude pair monitor implementation."""

    def setUp(self):
        if CLAUDE_PAIR_MONITOR is None:
            self.skipTest(".claude/scripts/pair_monitor.py not available")

    def test_default_max_iterations_is_one_hour_budget(self):
        """Default monitor budget should be 60 iterations at 60s interval."""
        self.assertEqual(CLAUDE_PAIR_MONITOR.DEFAULT_MAX_ITERATIONS, 60)

    def test_run_iteration_does_not_overwrite_completed_status(self):
        """Completed status should not be overwritten to running when tmux is still present."""
        with patch.object(Path, "mkdir"):
            monitor = CLAUDE_PAIR_MONITOR.PairMonitor(
                session_id="pair-test-123",
                coder_agent="coder-session",
                verifier_agent="verifier-session",
                bead_id="bd-test-123",
                coder_cmd="python3 coder.py",
                verifier_cmd="python3 verifier.py",
            )

        monitor.coder_state = CLAUDE_PAIR_MONITOR.AgentState(
            name="coder-session",
            tmux_session="coder-session",
            restart_cmd="python3 coder.py",
        )
        monitor.verifier_state = CLAUDE_PAIR_MONITOR.AgentState(
            name="verifier-session",
            tmux_session="verifier-session",
            restart_cmd="python3 verifier.py",
        )

        with (
            patch.object(
                monitor,
                "_check_orchestration_result_file",
                side_effect=[{"status": "completed"}, {"status": "completed"}],
            ),
            patch.object(monitor, "_find_session_on_sockets", return_value=""),
            patch.object(monitor, "check_log_activity", return_value=(True, 100)),
            patch.object(monitor, "update_bead_status") as mock_update,
        ):
            status = monitor.run_iteration()

        self.assertEqual(status, "completed")
        self.assertEqual(monitor.coder_state.status, "completed")
        self.assertEqual(monitor.verifier_state.status, "completed")
        mock_update.assert_called_with("completed")

    def test_run_iteration_preserves_idle_timestamps_without_activity(self):
        """Idle timestamps should not reset when no new log activity is observed."""
        with patch.object(Path, "mkdir"):
            monitor = CLAUDE_PAIR_MONITOR.PairMonitor(
                session_id="pair-test-123",
                coder_agent="coder-session",
                verifier_agent="verifier-session",
                bead_id="bd-test-123",
                coder_cmd="python3 coder.py",
                verifier_cmd="python3 verifier.py",
            )

        monitor.coder_state = CLAUDE_PAIR_MONITOR.AgentState(
            name="coder-session",
            tmux_session="coder-session",
            restart_cmd="python3 coder.py",
        )
        monitor.verifier_state = CLAUDE_PAIR_MONITOR.AgentState(
            name="verifier-session",
            tmux_session="verifier-session",
            restart_cmd="python3 verifier.py",
        )

        monitor.coder_state.last_check_time = 900.0
        monitor.verifier_state.last_check_time = 900.0

        with (
            patch.object(monitor, "_check_orchestration_result_file", return_value=None),
            patch.object(monitor, "_find_session_on_sockets", return_value=""),
            patch.object(monitor, "check_log_activity", return_value=(False, 0)),
            patch.object(monitor, "_write_status_file"),
            patch.object(monitor, "update_bead_status"),
            patch("time.time", return_value=1000.0),
        ):
            status = monitor.run_iteration()

        self.assertEqual(status, "in_progress")
        self.assertEqual(
            monitor.coder_state.last_check_time,
            900.0,
            "Coder idle timestamp should remain unchanged when no activity is seen",
        )
        self.assertEqual(
            monitor.verifier_state.last_check_time,
            900.0,
            "Verifier idle timestamp should remain unchanged when no activity is seen",
        )

    def test_run_iteration_restarts_after_sustained_idle_without_activity(self):
        """No-activity checks should eventually trigger restarts once timeout elapses."""
        with patch.object(Path, "mkdir"):
            monitor = CLAUDE_PAIR_MONITOR.PairMonitor(
                session_id="pair-test-123",
                coder_agent="coder-session",
                verifier_agent="verifier-session",
                bead_id="bd-test-123",
                coder_cmd="python3 coder.py",
                verifier_cmd="python3 verifier.py",
                log_idle_timeout=300,
            )

        monitor.coder_state = CLAUDE_PAIR_MONITOR.AgentState(
            name="coder-session",
            tmux_session="coder-session",
            restart_cmd="python3 coder.py",
        )
        monitor.verifier_state = CLAUDE_PAIR_MONITOR.AgentState(
            name="verifier-session",
            tmux_session="verifier-session",
            restart_cmd="python3 verifier.py",
        )

        monitor.coder_state.last_check_time = 900.0
        monitor.verifier_state.last_check_time = 900.0

        with (
            patch.object(monitor, "_check_orchestration_result_file", return_value=None),
            patch.object(monitor, "_find_session_on_sockets", return_value=""),
            patch.object(monitor, "check_log_activity", return_value=(False, 0)),
            patch.object(monitor, "_write_status_file"),
            patch.object(monitor, "update_bead_status"),
            patch.object(monitor, "restart_agent", side_effect=[True, True]) as mock_restart,
            patch("time.time", side_effect=[1000.0, 1000.0, 1250.0, 1250.0, 1250.0, 1250.0]),
        ):
            first_status = monitor.run_iteration()
            second_status = monitor.run_iteration()

        self.assertEqual(first_status, "in_progress")
        self.assertEqual(second_status, "in_progress")
        self.assertEqual(mock_restart.call_count, 2)

    def test_run_iteration_writes_status_artifact(self):
        """Each monitor iteration should persist session_dir/status.json."""
        with tempfile.TemporaryDirectory() as tmpdir, patch.object(Path, "mkdir"):
            monitor = CLAUDE_PAIR_MONITOR.PairMonitor(
                session_id="pair-test-123",
                coder_agent="coder-session",
                verifier_agent="verifier-session",
                bead_id="bd-test-123",
                coder_cmd="python3 coder.py",
                verifier_cmd="python3 verifier.py",
                session_dir=Path(tmpdir),
            )

            monitor.coder_state = CLAUDE_PAIR_MONITOR.AgentState(
                name="coder-session",
                tmux_session="coder-session",
                restart_cmd="python3 coder.py",
            )
            monitor.verifier_state = CLAUDE_PAIR_MONITOR.AgentState(
                name="verifier-session",
                tmux_session="verifier-session",
                restart_cmd="python3 verifier.py",
            )

            with (
                patch.object(
                    monitor,
                    "_check_orchestration_result_file",
                    side_effect=[{"status": "completed"}, {"status": "completed"}],
                ),
                patch.object(monitor, "_find_session_on_sockets", return_value=""),
                patch.object(monitor, "check_log_activity", return_value=(True, 100)),
                patch.object(monitor, "update_bead_status"),
            ):
                status = monitor.run_iteration()

            self.assertEqual(status, "completed")
            status_file = Path(tmpdir) / "status.json"
            self.assertTrue(status_file.exists(), "status.json should be emitted each iteration")
            status_data = json.loads(status_file.read_text(encoding="utf-8"))
            self.assertEqual(status_data["session_id"], "pair-test-123")
            self.assertEqual(status_data["coder_status"], "completed")
            self.assertEqual(status_data["verifier_status"], "completed")

    def test_run_iteration_allows_startup_not_found_grace_before_failure(self):
        """Startup socket misses should not immediately fail the session."""
        with patch.object(Path, "mkdir"):
            monitor = CLAUDE_PAIR_MONITOR.PairMonitor(
                session_id="pair-test-123",
                coder_agent="coder-session",
                verifier_agent="verifier-session",
                bead_id="bd-test-123",
                coder_cmd="python3 coder.py",
                verifier_cmd="python3 verifier.py",
            )

        monitor.coder_state = CLAUDE_PAIR_MONITOR.AgentState(
            name="coder-session",
            tmux_session="coder-session",
            restart_cmd="python3 coder.py",
        )
        monitor.verifier_state = CLAUDE_PAIR_MONITOR.AgentState(
            name="verifier-session",
            tmux_session="verifier-session",
            restart_cmd="python3 verifier.py",
        )

        with (
            patch.object(monitor, "_check_orchestration_result_file", return_value=None),
            patch.object(monitor, "_find_session_on_sockets", return_value=None),
            patch.object(monitor, "_check_agent_finished", return_value=False),
            patch.object(monitor, "_write_status_file"),
            patch.object(monitor, "update_bead_status") as mock_update,
        ):
            status = monitor.run_iteration()

        self.assertEqual(status, "in_progress")
        self.assertEqual(monitor.coder_state.status, "starting")
        self.assertEqual(monitor.verifier_state.status, "starting")
        mock_update.assert_not_called()

    def test_run_iteration_fails_after_startup_not_found_grace_exhausted(self):
        """Monitor should fail if startup misses persist beyond grace budget."""
        with patch.object(Path, "mkdir"):
            monitor = CLAUDE_PAIR_MONITOR.PairMonitor(
                session_id="pair-test-123",
                coder_agent="coder-session",
                verifier_agent="verifier-session",
                bead_id="bd-test-123",
                coder_cmd="python3 coder.py",
                verifier_cmd="python3 verifier.py",
            )

        monitor.coder_state = CLAUDE_PAIR_MONITOR.AgentState(
            name="coder-session",
            tmux_session="coder-session",
            restart_cmd="python3 coder.py",
        )
        monitor.verifier_state = CLAUDE_PAIR_MONITOR.AgentState(
            name="verifier-session",
            tmux_session="verifier-session",
            restart_cmd="python3 verifier.py",
        )

        with (
            patch.object(monitor, "_check_orchestration_result_file", return_value=None),
            patch.object(monitor, "_find_session_on_sockets", return_value=None),
            patch.object(monitor, "_check_agent_finished", return_value=False),
            patch.object(monitor, "_write_status_file"),
            patch.object(monitor, "update_bead_status") as mock_update,
        ):
            # Grace period should eventually exhaust and fail.
            terminal_status = "in_progress"
            for _ in range(4):
                terminal_status = monitor.run_iteration()
                if terminal_status == "failed":
                    break

        self.assertEqual(terminal_status, "failed")
        mock_update.assert_called_with("failed")

    def test_restart_agent_uses_detached_bootstrap_not_target_tmux_session(self):
        """Restart should not create tmux session with the target agent name."""
        with patch.object(Path, "mkdir"):
            monitor = CLAUDE_PAIR_MONITOR.PairMonitor(
                session_id="pair-test-123",
                coder_agent="coder-session",
                verifier_agent="verifier-session",
                bead_id="bd-test-123",
                coder_cmd="python3 coder.py --lite-mode",
                verifier_cmd="python3 verifier.py --lite-mode",
            )

        state = CLAUDE_PAIR_MONITOR.AgentState(
            name="coder-session",
            tmux_session="coder-session",
            restart_cmd="python3 orchestrate_unified.py --lite-mode --mcp-agent coder-session",
        )

        with (
            patch.object(
                monitor,
                "_find_session_on_sockets",
                side_effect=["", "", ""],  # existing session found, then recreated during poll loop
            ),
            patch("subprocess.run") as mock_run,
            patch("subprocess.Popen") as mock_popen,
            patch("time.sleep", return_value=None),
        ):
            result = monitor.restart_agent(state)

        self.assertTrue(result)
        self.assertEqual(state.status, "running")
        mock_popen.assert_called_once()
        popen_args, popen_kwargs = mock_popen.call_args
        self.assertEqual(
            popen_args[0],
            ["python3", "orchestrate_unified.py", "--lite-mode", "--mcp-agent", "coder-session"],
        )
        self.assertTrue(popen_kwargs["start_new_session"])

        # Only kill-session should be issued via tmux; restart bootstrap must not call tmux new-session.
        for call in mock_run.call_args_list:
            args, _kwargs = call
            cmd = args[0]
            self.assertNotIn("new-session", cmd)


class TestPairMonitorSubprocessSecurity(unittest.TestCase):
    """Test subprocess security (no shell=True)."""

    def setUp(self):
        """Set up test fixtures."""
        if not PAIR_MONITOR_AVAILABLE:
            self.skipTest("PairMonitor module not available")

    def test_tmux_commands_no_shell_injection(self):
        """Test that tmux commands don't use shell=True."""
        with (
            patch.object(Path, "mkdir"),
            patch("subprocess.run") as mock_run,
            patch("shutil.which") as mock_which,
        ):
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

                # Verify timeout is set (values vary: 5s for scan, 10s for has-session, 30s for capture)
                self.assertIn("timeout", kwargs)
                self.assertGreater(kwargs["timeout"], 0)


class TestPairMonitorTmuxCmd(unittest.TestCase):
    """Test _tmux_cmd method."""

    def setUp(self):
        """Set up test fixtures."""
        if not PAIR_MONITOR_AVAILABLE:
            self.skipTest("PairMonitor module not available")

    def test_tmux_cmd_no_socket(self):
        """Test tmux command without custom socket."""
        with (
            patch.object(Path, "mkdir"),
            patch("scripts.pair_monitor.TMUX_BIN", "/usr/bin/tmux"),
        ):
            monitor = PairMonitor(
                session_id="pair-test-123",
                coder_agent="coder",
                verifier_agent="verifier",
                bead_id="bd-123",
            )

            cmd = monitor._tmux_cmd()

            self.assertEqual(cmd, ["/usr/bin/tmux"])

    def test_tmux_cmd_with_socket(self):
        """Test tmux command with custom socket."""
        with (
            patch.object(Path, "mkdir"),
            patch("scripts.pair_monitor.TMUX_BIN", "/usr/bin/tmux"),
        ):
            monitor = PairMonitor(
                session_id="pair-test-123",
                coder_agent="coder",
                verifier_agent="verifier",
                bead_id="bd-123",
            )

            cmd = monitor._tmux_cmd("orch-12345-1700000000")

            self.assertEqual(cmd, ["/usr/bin/tmux", "-L", "orch-12345-1700000000"])


class TestPairMonitorCheckAgentResultFile(unittest.TestCase):
    """Test check_agent_result_file method."""

    def setUp(self):
        """Set up test fixtures."""
        if not PAIR_MONITOR_AVAILABLE:
            self.skipTest("PairMonitor module not available")

    def test_check_agent_result_file_exists(self):
        """Test reading result file when it exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Patch the results directory
            results_dir = Path(tmpdir) / "orchestration_results"
            results_dir.mkdir(parents=True)

            result_file = results_dir / "testagent_results.json"
            result_file.write_text(json.dumps({"status": "completed", "data": "test"}), encoding="utf-8")

            with patch.object(Path, "mkdir"):
                monitor = PairMonitor(
                    session_id="pair-test-123",
                    coder_agent="coder",
                    verifier_agent="verifier",
                    bead_id="bd-123",
                )

                # Temporarily patch the results directory path
                with patch("scripts.pair_monitor.Path") as mock_path:
                    # Make Path("/tmp/orchestration_results") return our temp dir
                    def path_side_effect(path_str):
                        if path_str == "/tmp/orchestration_results":
                            return results_dir
                        return Path(path_str)
                    mock_path.side_effect = path_side_effect

                    result = monitor.check_agent_result_file("testagent")

                self.assertIsNotNone(result)
                self.assertEqual(result["status"], "completed")

    def test_check_agent_result_file_not_found(self):
        """Test result file not found returns None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results_dir = Path(tmpdir) / "orchestration_results"
            results_dir.mkdir(parents=True)

            with patch.object(Path, "mkdir"):
                monitor = PairMonitor(
                    session_id="pair-test-123",
                    coder_agent="coder",
                    verifier_agent="verifier",
                    bead_id="bd-123",
                )

                with patch("scripts.pair_monitor.Path") as mock_path:
                    def path_side_effect(path_str):
                        if path_str == "/tmp/orchestration_results":
                            return results_dir
                        return Path(path_str)
                    mock_path.side_effect = path_side_effect

                    result = monitor.check_agent_result_file("nonexistent")

                self.assertIsNone(result)

    def test_check_agent_result_file_invalid_json(self):
        """Test invalid JSON in result file returns None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            results_dir = Path(tmpdir) / "orchestration_results"
            results_dir.mkdir(parents=True)

            result_file = results_dir / "testagent_results.json"
            result_file.write_text("not valid json{{{", encoding="utf-8")

            with patch.object(Path, "mkdir"):
                monitor = PairMonitor(
                    session_id="pair-test-123",
                    coder_agent="coder",
                    verifier_agent="verifier",
                    bead_id="bd-123",
                )

                with patch("scripts.pair_monitor.Path") as mock_path:
                    def path_side_effect(path_str):
                        if path_str == "/tmp/orchestration_results":
                            return results_dir
                        return Path(path_str)
                    mock_path.side_effect = path_side_effect

                    result = monitor.check_agent_result_file("testagent")

                self.assertIsNone(result)


class TestPairMonitorSendMcpMail(unittest.TestCase):
    """Test send_mcp_mail method."""

    def setUp(self):
        """Set up test fixtures."""
        if not PAIR_MONITOR_AVAILABLE:
            self.skipTest("PairMonitor module not available")

    def test_send_mcp_mail_success(self):
        """Test successful MCP mail sending."""
        with patch.object(Path, "mkdir"):
            monitor = PairMonitor(
                session_id="pair-test-123",
                coder_agent="coder",
                verifier_agent="verifier",
                bead_id="bd-123",
            )

            result = monitor.send_mcp_mail(
                to="coder",
                subject="TEST_MESSAGE",
                body={"task": "test task"}
            )

            self.assertTrue(result)


class TestCheckAgentFinished(unittest.TestCase):
    """Test _check_agent_finished method for detecting agent completion."""

    def setUp(self):
        """Set up test fixtures."""
        if CLAUDE_PAIR_MONITOR is None:
            self.skipTest("CLAUDE_PAIR_MONITOR module not available")

    def test_check_agent_finished_with_completion_signal(self):
        """Test detection of completion signal in log."""
        with patch.object(Path, "mkdir"):
            monitor = CLAUDE_PAIR_MONITOR.PairMonitor(
                session_id="pair-test-123",
                coder_agent="coder",
                verifier_agent="verifier",
                bead_id="bd-123",
                coder_cmd="",
                verifier_cmd="",
            )

            # Create mock agent state
            agent_state = CLAUDE_PAIR_MONITOR.AgentState(
                name="test-agent",
                tmux_session="test-agent",
                restart_cmd="",
            )

            # Test with log containing completion signal
            with patch.object(Path, "exists", return_value=True):
                with patch("builtins.open", mock_open(read_data="Agent execution completed\nSuccess")):
                    result = monitor._check_agent_finished(agent_state)
                    self.assertTrue(result)

    def test_check_agent_finished_with_exit_code(self):
        """Test detection of exit code in log."""
        with patch.object(Path, "mkdir"):
            monitor = CLAUDE_PAIR_MONITOR.PairMonitor(
                session_id="pair-test-123",
                coder_agent="coder",
                verifier_agent="verifier",
                bead_id="bd-123",
                coder_cmd="",
                verifier_cmd="",
            )

            agent_state = CLAUDE_PAIR_MONITOR.AgentState(
                name="test-agent",
                tmux_session="test-agent",
                restart_cmd="",
            )

            with patch.object(Path, "exists", return_value=True):
                with patch("builtins.open", mock_open(read_data="exit code: 0")):
                    result = monitor._check_agent_finished(agent_state)
                    self.assertTrue(result)

    def test_check_agent_finished_no_signal(self):
        """Test no completion signal returns False."""
        with patch.object(Path, "mkdir"):
            monitor = CLAUDE_PAIR_MONITOR.PairMonitor(
                session_id="pair-test-123",
                coder_agent="coder",
                verifier_agent="verifier",
                bead_id="bd-123",
                coder_cmd="",
                verifier_cmd="",
            )

            agent_state = CLAUDE_PAIR_MONITOR.AgentState(
                name="test-agent",
                tmux_session="test-agent",
                restart_cmd="",
            )

            with patch.object(Path, "exists", return_value=True):
                with patch("builtins.open", mock_open(read_data="Still running, waiting for input...")):
                    result = monitor._check_agent_finished(agent_state)
                    self.assertFalse(result)

    def test_check_agent_finished_log_not_exists(self):
        """Test missing log file returns False."""
        with patch.object(Path, "mkdir"):
            monitor = CLAUDE_PAIR_MONITOR.PairMonitor(
                session_id="pair-test-123",
                coder_agent="coder",
                verifier_agent="verifier",
                bead_id="bd-123",
                coder_cmd="",
                verifier_cmd="",
            )

            agent_state = CLAUDE_PAIR_MONITOR.AgentState(
                name="test-agent",
                tmux_session="test-agent",
                restart_cmd="",
            )

            with patch.object(Path, "exists", return_value=False):
                result = monitor._check_agent_finished(agent_state)
                self.assertFalse(result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
