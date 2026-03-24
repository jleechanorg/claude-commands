"""Tests for pair orchestration improvements.

Validates tmux socket discovery, flag passthrough, and startup verification
in pair_execute.py and pair_monitor.py.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

_REPO_ROOT = Path(__file__).resolve().parents[3]
_PAIR_EXECUTE_PATH = _REPO_ROOT / ".claude" / "scripts" / "pair_execute.py"
_PAIR_MONITOR_PATH = _REPO_ROOT / ".claude" / "scripts" / "pair_monitor.py"

_pair_execute_spec = importlib.util.spec_from_file_location("pair_execute", _PAIR_EXECUTE_PATH)
if _pair_execute_spec is None or _pair_execute_spec.loader is None:
    raise RuntimeError(f"Failed to load module spec for {_PAIR_EXECUTE_PATH}")
pair_execute = importlib.util.module_from_spec(_pair_execute_spec)
sys.modules["pair_execute"] = pair_execute
_pair_execute_spec.loader.exec_module(pair_execute)

_pair_monitor_spec = importlib.util.spec_from_file_location("pair_monitor", _PAIR_MONITOR_PATH)
if _pair_monitor_spec is None or _pair_monitor_spec.loader is None:
    raise RuntimeError(f"Failed to load module spec for {_PAIR_MONITOR_PATH}")
pair_monitor = importlib.util.module_from_spec(_pair_monitor_spec)
sys.modules["pair_monitor"] = pair_monitor
_pair_monitor_spec.loader.exec_module(pair_monitor)


# ============================================================================
# pair_execute.py tests
# ============================================================================


class TestDefaults:
    """Verify default configuration values."""

    def test_default_coder_cli_is_claude(self):
        assert pair_execute.DEFAULT_CODER_CLI == "claude"

    def test_default_verifier_cli_is_supported(self):
        assert pair_execute.DEFAULT_VERIFIER_CLI in pair_execute.SUPPORTED_CLIS

    def test_defaults_match_claude_implementation(self):
        """scripts/ and .claude/ implementations should stay aligned."""
        module_path = _REPO_ROOT / ".claude" / "scripts" / "pair_execute.py"
        spec = importlib.util.spec_from_file_location("claude_pair_execute", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert pair_execute.DEFAULT_CODER_CLI == module.DEFAULT_CODER_CLI
        assert pair_execute.DEFAULT_VERIFIER_CLI == module.DEFAULT_VERIFIER_CLI


class TestDiscoverTmuxSockets:
    """Test _discover_tmux_sockets log parsing."""

    def test_finds_socket_in_log(self, tmp_path):
        log_file = tmp_path / "agent.log"
        log_file.write_text(
            "[2026-02-12] Launching agent\n"
            "tmux -L orch-12345-1770908325 new-session -d -s agent-name\n"
            "[2026-02-12] Agent started\n"
        )
        sockets = pair_execute._discover_tmux_sockets(log_file)
        assert "orch-12345-1770908325" in sockets

    def test_finds_multiple_sockets(self, tmp_path):
        log_file = tmp_path / "agent.log"
        log_file.write_text(
            "tmux -L orch-111-222 new-session -d\n"
            "tmux -L orch-333-444 attach -t foo\n"
        )
        sockets = pair_execute._discover_tmux_sockets(log_file)
        assert len(sockets) == 2
        assert "orch-111-222" in sockets
        assert "orch-333-444" in sockets

    def test_deduplicates_sockets(self, tmp_path):
        log_file = tmp_path / "agent.log"
        log_file.write_text(
            "tmux -L orch-111-222 new-session -d\n"
            "tmux -L orch-111-222 attach -t foo\n"
        )
        sockets = pair_execute._discover_tmux_sockets(log_file)
        assert sockets.count("orch-111-222") == 1

    def test_returns_empty_for_missing_file(self, tmp_path):
        log_file = tmp_path / "nonexistent.log"
        sockets = pair_execute._discover_tmux_sockets(log_file)
        assert sockets == []

    def test_returns_empty_for_no_sockets_in_log(self, tmp_path):
        log_file = tmp_path / "agent.log"
        log_file.write_text("Agent started\nDoing work\nDone\n")
        with patch.object(pair_execute.Path, "glob", return_value=[]):
            sockets = pair_execute._discover_tmux_sockets(log_file)
        assert sockets == []


class TestBeadOperations:
    """Test bead creation and update with file locking."""

    def test_create_bead_entry(self, tmp_path):
        beads_file = tmp_path / ".beads" / "beads.left.jsonl"
        with patch.object(pair_execute, "BEADS_FILE", str(beads_file)):
            result = pair_execute.create_bead_entry("test-session-1", "Test task")
        assert result is True
        assert beads_file.exists()
        bead = json.loads(beads_file.read_text().strip())
        assert bead["id"] == "test-session-1"
        assert bead["status"] == "in_progress"
        assert "Test task" in bead["description"]

    def test_update_bead_status(self, tmp_path):
        beads_file = tmp_path / ".beads" / "beads.left.jsonl"
        beads_file.parent.mkdir(parents=True)
        bead = {
            "id": "test-1",
            "title": "Test",
            "status": "in_progress",
            "updated_at": "2026-01-01",
        }
        beads_file.write_text(json.dumps(bead) + "\n")
        with patch.object(pair_execute, "BEADS_FILE", str(beads_file)):
            result = pair_execute.update_bead_status("test-1", "completed")
        assert result is True
        updated = json.loads(beads_file.read_text().strip())
        assert updated["status"] == "completed"

    def test_update_nonexistent_bead_returns_false(self, tmp_path):
        beads_file = tmp_path / ".beads" / "beads.left.jsonl"
        beads_file.parent.mkdir(parents=True)
        beads_file.write_text(json.dumps({"id": "other", "status": "open"}) + "\n")
        with patch.object(pair_execute, "BEADS_FILE", str(beads_file)):
            result = pair_execute.update_bead_status("nonexistent", "closed")
        assert result is False


class TestLaunchFunctionSignatures:
    """Verify launch functions accept the new parameters."""

    def test_coder_accepts_no_worktree_and_model(self):
        import inspect

        sig = inspect.signature(pair_execute.launch_coder_agent)
        params = list(sig.parameters.keys())
        assert "no_worktree" in params
        assert "model" in params

    def test_verifier_accepts_no_worktree_and_model(self):
        import inspect

        sig = inspect.signature(pair_execute.launch_verifier_agent)
        params = list(sig.parameters.keys())
        assert "no_worktree" in params
        assert "model" in params

    def test_monitor_accepts_tmux_sockets(self):
        import inspect

        sig = inspect.signature(pair_execute.start_background_monitor)
        params = list(sig.parameters.keys())
        assert "tmux_sockets" in params


# ============================================================================
# pair_monitor.py tests
# ============================================================================


class TestPairMonitorInit:
    """Test PairMonitor initialization with tmux sockets."""

    def test_accepts_tmux_sockets(self):
        monitor = pair_monitor.PairMonitor(
            session_id="test-1",
            coder_agent="coder",
            verifier_agent="verifier",
            bead_id="test-1",
            coder_cmd="",
            verifier_cmd="",
            tmux_sockets=["orch-123-456"],
        )
        assert monitor.tmux_sockets == ["orch-123-456"]

    def test_default_empty_sockets(self):
        monitor = pair_monitor.PairMonitor(
            session_id="test-1",
            coder_agent="coder",
            verifier_agent="verifier",
            bead_id="test-1",
            coder_cmd="",
            verifier_cmd="",
        )
        assert monitor.tmux_sockets == []


class TestTmuxSocketSearch:
    """Test the socket search logic in pair_monitor."""

    def test_tmux_cmd_with_socket(self):
        monitor = pair_monitor.PairMonitor(
            session_id="t", coder_agent="c", verifier_agent="v", bead_id="b", coder_cmd="", verifier_cmd=""
        )
        cmd = monitor._tmux_cmd("orch-123-456")
        assert cmd == [pair_monitor.TMUX_BIN, "-L", "orch-123-456"]

    def test_tmux_cmd_without_socket(self):
        monitor = pair_monitor.PairMonitor(
            session_id="t", coder_agent="c", verifier_agent="v", bead_id="b", coder_cmd="", verifier_cmd=""
        )
        cmd = monitor._tmux_cmd(None)
        assert cmd == [pair_monitor.TMUX_BIN]

    @patch("subprocess.run")
    def test_find_session_tries_custom_sockets_first(self, mock_run):
        """Verify custom sockets are checked before default."""
        # First call (custom socket) succeeds
        mock_run.return_value = MagicMock(returncode=0)
        monitor = pair_monitor.PairMonitor(
            session_id="t",
            coder_agent="c",
            verifier_agent="v",
            bead_id="b",
            coder_cmd="",
            verifier_cmd="",
            tmux_sockets=["orch-123-456"],
        )
        result = monitor._find_session_on_sockets("my-session")
        assert result == "orch-123-456"
        # Should have called tmux -L orch-123-456 has-session
        first_call_args = mock_run.call_args_list[0][0][0]
        assert "-L" in first_call_args
        assert "orch-123-456" in first_call_args

    @patch("subprocess.run")
    def test_find_session_falls_back_to_default(self, mock_run):
        """When custom sockets fail, try default socket."""
        # All calls fail except the last (default socket)
        fail = MagicMock(returncode=1)
        success = MagicMock(returncode=0)
        mock_run.side_effect = [fail, success]

        monitor = pair_monitor.PairMonitor(
            session_id="t",
            coder_agent="c",
            verifier_agent="v",
            bead_id="b",
            coder_cmd="",
            verifier_cmd="",
            tmux_sockets=["orch-bad-socket"],
        )
        # Patch glob to return nothing (no /tmp scan results)
        with patch("pathlib.Path.glob", return_value=[]):
            result = monitor._find_session_on_sockets("my-session")
        assert result == ""  # Empty string = default socket

    @patch("subprocess.run")
    def test_find_session_returns_none_when_not_found(self, mock_run):
        """When no sockets have the session, return None."""
        mock_run.return_value = MagicMock(returncode=1)
        monitor = pair_monitor.PairMonitor(
            session_id="t",
            coder_agent="c",
            verifier_agent="v",
            bead_id="b",
            coder_cmd="",
            verifier_cmd="",
        )
        with patch("pathlib.Path.glob", return_value=[]):
            result = monitor._find_session_on_sockets("missing-session")
        assert result is None


class TestMonitorBeadUpdate:
    """Test monitor bead status updates."""

    def test_update_bead_status(self, tmp_path):
        beads_file = tmp_path / ".beads" / "beads.left.jsonl"
        beads_file.parent.mkdir(parents=True)
        bead = {"id": "monitor-test", "status": "in_progress", "updated_at": "x"}
        beads_file.write_text(json.dumps(bead) + "\n")

        with patch.object(pair_monitor, "BEADS_FILE", str(beads_file)):
            monitor = pair_monitor.PairMonitor(
                session_id="s",
                coder_agent="c",
                verifier_agent="v",
                bead_id="monitor-test",
                coder_cmd="",
                verifier_cmd="",
            )
            result = monitor.update_bead_status("completed")

        assert result is True
        updated = json.loads(beads_file.read_text().strip())
        assert updated["status"] == "completed"
