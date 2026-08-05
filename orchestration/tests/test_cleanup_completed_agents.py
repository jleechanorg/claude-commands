#!/usr/bin/env python3
"""
Comprehensive unit tests for tmux cleanup script following TDD principles.
Tests all key functions with mocking for subprocess calls and file operations.
"""

import os
import subprocess
import tempfile
from unittest.mock import Mock, patch

import pytest

from orchestration.cleanup_completed_agents import (
    check_agent_completion,
    check_session_timeout,
    cleanup_agent_session,
    cleanup_completed_agents,
    get_all_monitoring_sessions,
    get_session_timeout,
    get_tmux_sessions,
)


class TestGetTmuxSessions:
    """Test tmux session discovery functionality."""

    @patch("orchestration.cleanup_completed_agents.subprocess.run")
    def test_get_tmux_sessions_success_returns_session_list(self, mock_run):
        """Test successful tmux session listing returns parsed session names."""
        # Arrange
        mock_run.return_value = Mock(stdout="task-agent-123\ngh-comment-monitor-456\ncopilot-analysis\n", returncode=0)

        # Act
        result = get_tmux_sessions()

        # Assert
        assert result == ["task-agent-123", "gh-comment-monitor-456", "copilot-analysis"]
        mock_run.assert_called_once_with(
            ["tmux", "list-sessions", "-F", "#{session_name}"],
            shell=False,
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )

    @patch("orchestration.cleanup_completed_agents.subprocess.run")
    def test_get_tmux_sessions_empty_output_returns_empty_list(self, mock_run):
        """Test empty tmux output returns empty list."""
        # Arrange
        mock_run.return_value = Mock(stdout="", returncode=0)

        # Act
        result = get_tmux_sessions()

        # Assert
        assert result == []

    @patch("orchestration.cleanup_completed_agents.subprocess.run")
    def test_get_tmux_sessions_whitespace_only_returns_empty_list(self, mock_run):
        """Test whitespace-only tmux output returns empty list."""
        # Arrange
        mock_run.return_value = Mock(stdout="   \n  \n   \n", returncode=0)

        # Act
        result = get_tmux_sessions()

        # Assert
        assert result == []

    @patch("orchestration.cleanup_completed_agents.subprocess.run")
    def test_get_tmux_sessions_command_failure_returns_empty_list(self, mock_run):
        """Test tmux command failure returns empty list."""
        # Arrange
        mock_run.side_effect = subprocess.CalledProcessError(1, "tmux")

        # Act
        result = get_tmux_sessions()

        # Assert
        assert result == []

    @patch("orchestration.cleanup_completed_agents.subprocess.run")
    def test_get_tmux_sessions_strips_whitespace_from_names(self, mock_run):
        """Test session names have whitespace stripped."""
        # Arrange
        mock_run.return_value = Mock(stdout="  task-agent-123  \n  copilot-test  \n", returncode=0)

        # Act
        result = get_tmux_sessions()

        # Assert
        assert result == ["task-agent-123", "copilot-test"]


class TestGetAllMonitoringSessions:
    """Test monitoring session pattern matching functionality."""

    @patch("orchestration.cleanup_completed_agents.get_tmux_sessions")
    def test_get_all_monitoring_sessions_task_agent_pattern_matches(self, mock_get_sessions):
        """Test task-agent-* pattern is included in monitoring sessions."""
        # Arrange
        mock_get_sessions.return_value = ["task-agent-123", "regular-session", "task-agent-456"]

        # Act
        result = get_all_monitoring_sessions()

        # Debug: Check what we actually got

        # Assert
        assert "task-agent-123" in result
        assert "task-agent-456" in result
        assert "regular-session" not in result

    @patch("orchestration.cleanup_completed_agents.get_tmux_sessions")
    def test_get_all_monitoring_sessions_gh_comment_monitor_pattern_matches(self, mock_get_sessions):
        """Test gh-comment-monitor-* pattern is included in monitoring sessions."""
        # Arrange
        mock_get_sessions.return_value = [
            "gh-comment-monitor-backup_fix1231",
            "other-session",
            "gh-comment-monitor-pr456",
        ]

        # Act
        result = get_all_monitoring_sessions()

        # Assert
        assert "gh-comment-monitor-backup_fix1231" in result
        assert "gh-comment-monitor-pr456" in result
        assert "other-session" not in result

    @patch("orchestration.cleanup_completed_agents.get_tmux_sessions")
    def test_get_all_monitoring_sessions_copilot_pattern_matches(self, mock_get_sessions):
        """Test copilot-* pattern is included in monitoring sessions."""
        # Arrange
        mock_get_sessions.return_value = ["copilot-analysis", "copilot-fixpr-test", "not-copilot-session"]

        # Act
        result = get_all_monitoring_sessions()

        # Assert
        assert "copilot-analysis" in result
        assert "copilot-fixpr-test" in result
        assert "not-copilot-session" not in result

    @patch("orchestration.cleanup_completed_agents.get_tmux_sessions")
    def test_get_all_monitoring_sessions_agent_pattern_matches(self, mock_get_sessions):
        """Test agent-* pattern is included in monitoring sessions."""
        # Arrange
        mock_get_sessions.return_value = ["agent-generic", "agent-worker-123", "not-an-agent"]

        # Act
        result = get_all_monitoring_sessions()

        # Assert
        assert "agent-generic" in result
        assert "agent-worker-123" in result
        assert "not-an-agent" not in result

    @patch("orchestration.cleanup_completed_agents.get_tmux_sessions")
    def test_get_all_monitoring_sessions_mixed_patterns_all_match(self, mock_get_sessions):
        """Test all monitoring patterns are matched in mixed session list."""
        # Arrange
        mock_get_sessions.return_value = [
            "task-agent-123",
            "gh-comment-monitor-pr456",
            "copilot-analysis",
            "agent-worker",
            "random-session",
            "another-session",
        ]

        # Act
        result = get_all_monitoring_sessions()

        # Assert
        expected_monitoring = ["task-agent-123", "gh-comment-monitor-pr456", "copilot-analysis", "agent-worker"]
        assert all(session in result for session in expected_monitoring)
        assert "random-session" not in result
        assert "another-session" not in result
        assert len(result) == 4

    @patch("orchestration.cleanup_completed_agents.get_tmux_sessions")
    def test_get_all_monitoring_sessions_no_matches_returns_empty_list(self, mock_get_sessions):
        """Test no monitoring pattern matches returns empty list."""
        # Arrange
        mock_get_sessions.return_value = ["random-session", "another-session", "third-session"]

        # Act
        result = get_all_monitoring_sessions()

        # Assert
        assert result == []


class TestGetSessionTimeout:
    """Test pattern-based timeout logic functionality."""

    def test_get_session_timeout_task_agent_returns_one_hour(self):
        """Test task-agent-* sessions return 1 hour timeout."""
        # Act & Assert
        assert get_session_timeout("task-agent-123") == 3600  # 1 hour
        assert get_session_timeout("task-agent-worker-456") == 3600

    def test_get_session_timeout_gh_comment_monitor_returns_four_hours(self):
        """Test gh-comment-monitor-* sessions return 4 hour timeout."""
        # Act & Assert
        assert get_session_timeout("gh-comment-monitor-pr123") == 14400  # 4 hours
        assert get_session_timeout("gh-comment-monitor-backup_fix1231") == 14400

    def test_get_session_timeout_copilot_returns_two_hours(self):
        """Test copilot-* sessions return 2 hour timeout."""
        # Act & Assert
        assert get_session_timeout("copilot-analysis") == 7200  # 2 hours
        assert get_session_timeout("copilot-fixpr-test") == 7200

    def test_get_session_timeout_agent_returns_three_hours(self):
        """Test agent-* sessions return 3 hour timeout."""
        # Act & Assert
        assert get_session_timeout("agent-worker") == 10800  # 3 hours
        assert get_session_timeout("agent-generic-123") == 10800

    def test_get_session_timeout_unknown_pattern_returns_default_24_hours(self):
        """Test unknown session patterns return default 24 hour timeout."""
        # Act & Assert
        assert get_session_timeout("unknown-session") == 86400  # 24 hours
        assert get_session_timeout("random-name") == 86400
        assert get_session_timeout("") == 86400

    def test_get_session_timeout_partial_match_uses_default(self):
        """Test partial pattern matches use default timeout."""
        # Act & Assert
        assert get_session_timeout("task-agentfoo") == 86400  # Doesn't match "task-agent-"
        assert get_session_timeout("atask-agent-123") == 86400  # Doesn't start with pattern


class TestCheckSessionTimeout:
    """Test session timeout calculation and validation functionality."""

    @patch("orchestration.cleanup_completed_agents.time.time")
    @patch("orchestration.cleanup_completed_agents.subprocess.run")
    def test_check_session_timeout_exceeded_timeout_returns_true(self, mock_run, mock_time):
        """Test session exceeding timeout returns timeout=True."""
        # Arrange
        current_time = 1000000000
        session_activity = current_time - 7200  # 2 hours ago
        mock_time.return_value = current_time
        mock_run.return_value = Mock(stdout=str(session_activity), returncode=0)

        # Act
        result = check_session_timeout("task-agent-test")  # 1 hour timeout

        # Assert
        assert result["timeout"] is True
        assert result["reason"] == "timeout_exceeded"
        assert result["elapsed_hours"] == 2.0
        assert result["timeout_seconds"] == 3600

    @patch("orchestration.cleanup_completed_agents.time.time")
    @patch("orchestration.cleanup_completed_agents.subprocess.run")
    def test_check_session_timeout_within_timeout_returns_false(self, mock_run, mock_time):
        """Test session within timeout returns timeout=False."""
        # Arrange
        current_time = 1000000000
        session_activity = current_time - 1800  # 30 minutes ago
        mock_time.return_value = current_time
        mock_run.return_value = Mock(stdout=str(session_activity), returncode=0)

        # Act
        result = check_session_timeout("task-agent-test")  # 1 hour timeout

        # Assert
        assert result["timeout"] is False
        assert result["reason"] == "within_timeout"
        assert result["elapsed_seconds"] == 1800

    @patch("orchestration.cleanup_completed_agents.subprocess.run")
    def test_check_session_timeout_session_not_found_returns_false(self, mock_run):
        """Test non-existent session returns timeout=False with session_not_found."""
        # Arrange
        mock_run.return_value = Mock(stdout="", returncode=0)

        # Act
        result = check_session_timeout("non-existent-session")

        # Assert
        assert result["timeout"] is False
        assert result["reason"] == "session_not_found"

    @patch("orchestration.cleanup_completed_agents.subprocess.run")
    def test_check_session_timeout_invalid_format_returns_false(self, mock_run):
        """Test invalid tmux output format returns timeout=False with invalid_timestamp."""
        # Arrange
        mock_run.return_value = Mock(stdout="invalid-timestamp", returncode=0)

        # Act
        result = check_session_timeout("test-session")

        # Assert
        assert result["timeout"] is False
        assert result["reason"] == "invalid_timestamp"

    @patch("orchestration.cleanup_completed_agents.subprocess.run")
    def test_check_session_timeout_subprocess_error_returns_false(self, mock_run):
        """Test subprocess error returns timeout=False with error reason."""
        # Arrange
        mock_run.side_effect = subprocess.CalledProcessError(1, "tmux")

        # Act
        result = check_session_timeout("test-session")

        # Assert
        assert result["timeout"] is False
        assert "error" in result["reason"]

    @patch("orchestration.cleanup_completed_agents.subprocess.run")
    def test_check_session_timeout_calls_tmux_with_correct_filter(self, mock_run):
        """Test tmux command uses correct display-message syntax."""
        # Arrange
        mock_run.return_value = Mock(stdout="", returncode=0)

        # Act
        check_session_timeout("test-session")

        # Assert
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "tmux" in call_args
        assert "display-message" in call_args
        assert "-t" in call_args
        assert "test-session" in call_args
        assert "#{session_activity}" in call_args


class TestCheckAgentCompletion:
    """Test log file analysis for agent completion."""

    @patch("orchestration.cleanup_completed_agents.os.path.exists")
    def test_check_agent_completion_no_log_file_returns_false(self, mock_exists):
        """Test missing log file returns completed=False with no_log_file reason."""
        # Arrange
        mock_exists.return_value = False

        # Act
        result = check_agent_completion("test-agent")

        # Assert
        assert result["completed"] is False
        assert result["reason"] == "no_log_file"

    @patch("orchestration.cleanup_completed_agents.os.path.exists")
    @patch("orchestration.cleanup_completed_agents.subprocess.run")
    def test_check_agent_completion_found_completion_marker_returns_true(self, mock_run, mock_exists):
        """Test completion marker in log returns completed=True."""
        # Arrange
        mock_exists.return_value = True
        mock_run.return_value = Mock(stdout="Some log content\nClaude exit code: 0\nMore content")

        # Act
        result = check_agent_completion("test-agent")

        # Assert
        assert result["completed"] is True
        assert "found_marker" in result["reason"]
        assert result["log_path"] == "/tmp/orchestration_logs/test-agent.log"

    @patch("orchestration.cleanup_completed_agents.os.path.exists")
    @patch("orchestration.cleanup_completed_agents.subprocess.run")
    @patch("orchestration.cleanup_completed_agents.os.stat")
    @patch("orchestration.cleanup_completed_agents.time.time")
    def test_check_agent_completion_idle_threshold_exceeded_returns_true(
        self, mock_time, mock_stat, mock_run, mock_exists
    ):
        """Test log idle beyond threshold returns completed=True."""
        # Arrange
        mock_exists.return_value = True
        mock_run.return_value = Mock(stdout="No completion markers")
        mock_time.return_value = 1000000000
        mock_stat.return_value = Mock(st_mtime=1000000000 - 2400)  # 40 minutes old

        # Act
        result = check_agent_completion("test-agent")

        # Assert
        assert result["completed"] is True
        assert "idle_for_40.0_minutes" in result["reason"]

    @patch("orchestration.cleanup_completed_agents.os.path.exists")
    @patch("orchestration.cleanup_completed_agents.subprocess.run")
    @patch("orchestration.cleanup_completed_agents.os.stat")
    @patch("orchestration.cleanup_completed_agents.time.time")
    def test_check_agent_completion_within_idle_threshold_returns_false(
        self, mock_time, mock_stat, mock_run, mock_exists
    ):
        """Test log recent and no markers returns completed=False."""
        # Arrange
        mock_exists.return_value = True
        mock_run.return_value = Mock(stdout="No completion markers")
        mock_time.return_value = 1000000000
        mock_stat.return_value = Mock(st_mtime=1000000000 - 600)  # 10 minutes old

        # Act
        result = check_agent_completion("test-agent")

        # Assert
        assert result["completed"] is False
        assert result["reason"] == "still_active"

    @patch("orchestration.cleanup_completed_agents.os.path.exists")
    @patch("orchestration.cleanup_completed_agents.subprocess.run")
    def test_check_agent_completion_multiple_markers_detected(self, mock_run, mock_exists):
        """Test various completion markers are all detected."""
        # Arrange
        mock_exists.return_value = True
        test_cases = [
            "Claude exit code: 0",
            "Agent completed successfully",
            '"subtype":"success"',
            '"is_error":false,"duration_ms"',
        ]

        for marker in test_cases:
            mock_run.return_value = Mock(stdout=f"Log content\n{marker}\nMore content")

            # Act
            result = check_agent_completion("test-agent")

            # Assert
            assert result["completed"] is True
            assert marker.lower() in result["reason"].lower()

    @patch("orchestration.cleanup_completed_agents.os.path.exists")
    @patch("orchestration.cleanup_completed_agents.subprocess.run")
    def test_check_agent_completion_subprocess_error_returns_false(self, mock_run, mock_exists):
        """Test subprocess error returns completed=False with error reason."""
        # Arrange
        mock_exists.return_value = True
        mock_run.side_effect = subprocess.CalledProcessError(1, "tail")

        # Act
        result = check_agent_completion("test-agent")

        # Assert
        assert result["completed"] is False
        assert "error" in result["reason"]


class TestCleanupAgentSession:
    """Test session termination functionality."""

    @patch("orchestration.cleanup_completed_agents.subprocess.run")
    def test_cleanup_agent_session_dry_run_true_does_not_kill_session(self, mock_run):
        """Test dry run mode does not execute tmux kill command."""
        # Act
        result = cleanup_agent_session("test-agent", dry_run=True)

        # Assert
        assert result is True
        mock_run.assert_not_called()

    @patch("orchestration.cleanup_completed_agents.subprocess.run")
    def test_cleanup_agent_session_success_kills_session_and_returns_true(self, mock_run):
        """Test successful session termination returns True."""
        # Arrange
        mock_run.return_value = Mock(returncode=0)

        # Act
        result = cleanup_agent_session("test-agent", dry_run=False)

        # Assert
        assert result is True
        mock_run.assert_called_once_with(
            ["tmux", "kill-session", "-t", "test-agent"], shell=False, check=True, timeout=30
        )

    @patch("orchestration.cleanup_completed_agents.subprocess.run")
    def test_cleanup_agent_session_failure_returns_false(self, mock_run):
        """Test failed session termination returns False."""
        # Arrange
        mock_run.side_effect = subprocess.CalledProcessError(1, "tmux")

        # Act
        result = cleanup_agent_session("test-agent", dry_run=False)

        # Assert
        assert result is False

    @patch("orchestration.cleanup_completed_agents.subprocess.run")
    def test_cleanup_agent_session_handles_special_characters_in_name(self, mock_run):
        """Test session names with special characters are handled correctly."""
        # Arrange
        mock_run.return_value = Mock(returncode=0)

        # Act
        result = cleanup_agent_session("test-agent-with-dashes_and_underscores", dry_run=False)

        # Assert
        assert result is True
        mock_run.assert_called_once_with(
            ["tmux", "kill-session", "-t", "test-agent-with-dashes_and_underscores"],
            shell=False,
            check=True,
            timeout=30,
        )


class TestCleanupCompletedAgents:
    """Test main cleanup workflow with various scenarios."""

    @patch("orchestration.cleanup_completed_agents.get_all_monitoring_sessions")
    @patch("orchestration.cleanup_completed_agents.check_agent_completion")
    @patch("orchestration.cleanup_completed_agents.check_session_timeout")
    @patch("orchestration.cleanup_completed_agents.cleanup_agent_session")
    def test_cleanup_completed_agents_mixed_session_types_processed_correctly(
        self, mock_cleanup, mock_timeout, mock_completion, mock_get_sessions
    ):
        """Test mixed session types are processed with correct logic."""
        # Arrange
        mock_get_sessions.return_value = ["task-agent-123", "copilot-analysis", "agent-worker"]

        # task-agent-123: completed by markers
        mock_completion.side_effect = [
            {"completed": True, "reason": "found_marker: Claude exit code: 0"},
            {"completed": False, "reason": "no_log_file"},  # copilot (no logs)
            {"completed": False, "reason": "no_log_file"},  # agent (no logs)
        ]

        # copilot-analysis: timeout exceeded
        # agent-worker: within timeout
        mock_timeout.side_effect = [
            {"timeout": False, "reason": "within_timeout"},  # task-agent (already completed)
            {"timeout": True, "reason": "timeout_exceeded", "elapsed_hours": 3.0},  # copilot
            {"timeout": False, "reason": "within_timeout", "elapsed_seconds": 1800},  # agent
        ]

        mock_cleanup.return_value = True

        # Act
        result = cleanup_completed_agents(dry_run=False)

        # Assert
        assert result["total_sessions"] == 3
        assert result["completed"] == 1  # task-agent-123
        assert result["timeout"] == 1  # copilot-analysis
        assert result["active"] == 1  # agent-worker
        assert result["cleaned_up"] == 2  # Both completed and timeout cleaned
        assert mock_cleanup.call_count == 2

    @patch("orchestration.cleanup_completed_agents.get_all_monitoring_sessions")
    def test_cleanup_completed_agents_no_sessions_returns_zero_counts(self, mock_get_sessions):
        """Test no monitoring sessions returns all zero counts."""
        # Arrange
        mock_get_sessions.return_value = []

        # Act
        result = cleanup_completed_agents(dry_run=False)

        # Assert
        assert result["total_sessions"] == 0
        assert result["completed"] == 0
        assert result["timeout"] == 0
        assert result["active"] == 0
        assert result["cleaned_up"] == 0

    @patch("orchestration.cleanup_completed_agents.get_all_monitoring_sessions")
    @patch("orchestration.cleanup_completed_agents.check_agent_completion")
    @patch("orchestration.cleanup_completed_agents.check_session_timeout")
    @patch("orchestration.cleanup_completed_agents.cleanup_agent_session")
    def test_cleanup_completed_agents_dry_run_mode_does_not_cleanup(
        self, mock_cleanup, mock_timeout, mock_completion, mock_get_sessions
    ):
        """Test dry run mode counts sessions but does not cleanup."""
        # Arrange
        mock_get_sessions.return_value = ["task-agent-123"]
        mock_completion.return_value = {"completed": True, "reason": "found_marker"}
        mock_cleanup.return_value = True

        # Act
        result = cleanup_completed_agents(dry_run=True)

        # Assert
        assert result["completed"] == 1
        assert result["cleaned_up"] == 0  # Dry run doesn't increment cleanup count
        mock_cleanup.assert_called_once_with("task-agent-123", True)

    @patch("orchestration.cleanup_completed_agents.get_all_monitoring_sessions")
    @patch("orchestration.cleanup_completed_agents.check_agent_completion")
    @patch("orchestration.cleanup_completed_agents.check_session_timeout")
    @patch("orchestration.cleanup_completed_agents.cleanup_agent_session")
    def test_cleanup_completed_agents_cleanup_failures_counted_correctly(
        self, mock_cleanup, mock_timeout, mock_completion, mock_get_sessions
    ):
        """Test cleanup failures are counted correctly."""
        # Arrange
        mock_get_sessions.return_value = ["task-agent-123", "task-agent-456"]
        mock_completion.side_effect = [
            {"completed": True, "reason": "found_marker"},
            {"completed": True, "reason": "found_marker"},
        ]
        mock_cleanup.side_effect = [True, False]  # First succeeds, second fails

        # Act
        result = cleanup_completed_agents(dry_run=False)

        # Assert
        assert result["completed"] == 2
        assert result["cleaned_up"] == 1  # Only successful cleanup counted
        assert mock_cleanup.call_count == 2

    @patch("orchestration.cleanup_completed_agents.get_all_monitoring_sessions")
    @patch("orchestration.cleanup_completed_agents.check_session_timeout")
    def test_cleanup_completed_agents_only_task_agents_check_completion_logs(self, mock_timeout, mock_get_sessions):
        """Test only task-agent sessions check completion via logs."""
        # Arrange
        mock_get_sessions.return_value = ["task-agent-123", "copilot-analysis", "gh-comment-monitor-test"]
        mock_timeout.return_value = {"timeout": False, "reason": "within_timeout"}

        # Act
        with patch("orchestration.cleanup_completed_agents.check_agent_completion") as mock_completion:
            mock_completion.return_value = {"completed": False, "reason": "still_active"}
            result = cleanup_completed_agents(dry_run=True)

            # Assert
            mock_completion.assert_called_once_with("task-agent-123")  # Only task-agent checked

    @patch("orchestration.cleanup_completed_agents.get_all_monitoring_sessions")
    @patch("orchestration.cleanup_completed_agents.check_session_timeout")
    def test_cleanup_completed_agents_all_sessions_check_timeout(self, mock_timeout, mock_get_sessions):
        """Test all session types check timeout regardless of pattern."""
        # Arrange
        sessions = ["task-agent-123", "copilot-analysis", "gh-comment-monitor-test", "agent-worker"]
        mock_get_sessions.return_value = sessions
        mock_timeout.return_value = {"timeout": False, "reason": "within_timeout"}

        # Act
        with patch("orchestration.cleanup_completed_agents.check_agent_completion") as mock_completion:
            mock_completion.return_value = {"completed": False, "reason": "still_active"}
            result = cleanup_completed_agents(dry_run=True)

            # Assert
            assert mock_timeout.call_count == 4  # All sessions checked for timeout
            timeout_calls = [call[0][0] for call in mock_timeout.call_args_list]
            for session in sessions:
                assert session in timeout_calls


# Test Fixtures and Utilities
@pytest.fixture
def temp_log_file():
    """Create a temporary log file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("Test log content\n")
        temp_path = f.name

    yield temp_path

    # Cleanup
    try:
        os.unlink(temp_path)
    except OSError:
        pass


@pytest.fixture
def mock_constants():
    """Mock the constants module import."""
    with patch("cleanup_completed_agents.IDLE_MINUTES_THRESHOLD", 30):
        yield


# Integration Test Examples
class TestCleanupIntegration:
    """Integration tests combining multiple functions."""

    @patch("orchestration.cleanup_completed_agents.get_tmux_sessions")
    @patch("orchestration.cleanup_completed_agents.subprocess.run")
    @patch("orchestration.cleanup_completed_agents.os.path.exists")
    @patch("orchestration.cleanup_completed_agents.os.stat")
    @patch("orchestration.cleanup_completed_agents.time.time")
    def test_full_cleanup_workflow_realistic_scenario(
        self, mock_time, mock_stat, mock_exists, mock_subprocess, mock_get_sessions
    ):
        """Test realistic cleanup scenario with mixed session states."""
        # Arrange
        mock_get_sessions.return_value = [
            "task-agent-completed",
            "task-agent-active",
            "gh-comment-monitor-timeout",
            "copilot-active",
            "regular-session",  # Should be ignored
        ]

        current_time = 1000000000
        mock_time.return_value = current_time

        # Mock subprocess calls for different scenarios
        def subprocess_side_effect(cmd, **kwargs):
            if "tail" in cmd:
                # Check if the log path contains the session name
                log_path = " ".join(cmd) if isinstance(cmd, list) else cmd
                if "task-agent-completed.log" in log_path:
                    return Mock(stdout="Claude exit code: 0")
                else:
                    return Mock(stdout="Still running...")
            elif "display-message" in cmd and "-t" in cmd:
                # Extract session name from -t parameter
                t_index = cmd.index("-t")
                session_name = cmd[t_index + 1] if t_index + 1 < len(cmd) else ""
                if "timeout" in session_name:
                    # 5 hours ago for gh-comment-monitor (4h timeout)
                    activity_time = current_time - 18000
                elif "active" in session_name:
                    # 1 hour ago for active sessions
                    activity_time = current_time - 3600
                elif "completed" in session_name:
                    # 30 minutes ago for completed sessions (within timeout)
                    activity_time = current_time - 1800
                else:
                    activity_time = current_time - 1800
                return Mock(stdout=str(activity_time))
            elif "kill-session" in cmd:
                return Mock(returncode=0)

            return Mock(stdout="", returncode=0)

        mock_subprocess.side_effect = subprocess_side_effect
        mock_exists.return_value = True
        # Mock os.stat for log files (make them appear fresh so they don't get cleaned up by idle timeout)
        mock_stat.return_value = Mock(st_mtime=current_time - 600)  # 10 minutes old

        # Act
        result = cleanup_completed_agents(dry_run=False)

        # Assert
        assert result["total_sessions"] == 4  # Excludes regular-session
        assert result["completed"] >= 1  # task-agent-completed
        assert result["timeout"] >= 1  # gh-comment-monitor-timeout
        assert result["cleaned_up"] >= 2  # At least both completed and timeout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
