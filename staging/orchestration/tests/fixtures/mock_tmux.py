"""Mock fixtures for tmux operations in orchestration tests."""

from contextlib import contextmanager
from unittest.mock import Mock, patch


class MockTmuxSession:
    """Mock tmux session for testing."""

    def __init__(self, session_name):
        self.session_name = session_name
        self.running = True
        self.output_lines = []

    def add_output(self, line):
        """Add output line to mock session."""
        self.output_lines.append(line)

    def capture_pane(self):
        """Mock tmux capture-pane output."""
        return "\n".join(self.output_lines[-10:])  # Last 10 lines


class MockTmux:
    """Mock tmux command handler."""

    def __init__(self):
        self.sessions = {}
        self.call_history = []

    def mock_subprocess_run(self, cmd, **kwargs):
        """Mock subprocess.run for tmux commands."""
        self.call_history.append(cmd)

        if not cmd or "tmux" not in cmd[0]:
            # Not a tmux command, return original behavior
            return Mock(returncode=1, stdout="", stderr="command not found")

        if "new-session" in cmd:
            return self._handle_new_session(cmd)
        if "list-sessions" in cmd:
            return self._handle_list_sessions(cmd)
        if "capture-pane" in cmd:
            return self._handle_capture_pane(cmd)
        if "has-session" in cmd:
            return self._handle_has_session(cmd)

        return Mock(returncode=0, stdout="", stderr="")

    def _handle_new_session(self, cmd):
        """Handle tmux new-session command."""
        session_name = None

        # Parse session name from command
        for i, arg in enumerate(cmd):
            if arg == "-s" and i + 1 < len(cmd):
                session_name = cmd[i + 1]
                break

        if session_name:
            self.sessions[session_name] = MockTmuxSession(session_name)
            return Mock(returncode=0, stdout="", stderr="")

        return Mock(returncode=1, stdout="", stderr="no session name")

    def _handle_list_sessions(self, cmd):
        """Handle tmux list-sessions command."""
        if not self.sessions:
            return Mock(returncode=1, stdout="", stderr="no sessions")

        session_list = []
        for name, session in self.sessions.items():
            if session.running:
                session_list.append(f"{name}: 1 windows")

        return Mock(returncode=0, stdout="\n".join(session_list), stderr="")

    def _handle_capture_pane(self, cmd):
        """Handle tmux capture-pane command."""
        session_name = None

        # Parse session name from -t flag
        for i, arg in enumerate(cmd):
            if arg == "-t" and i + 1 < len(cmd):
                session_name = cmd[i + 1]
                break

        if session_name and session_name in self.sessions:
            output = self.sessions[session_name].capture_pane()
            return Mock(returncode=0, stdout=output, stderr="")

        return Mock(returncode=1, stdout="", stderr="session not found")

    def _handle_has_session(self, cmd):
        """Handle tmux has-session command."""
        session_name = None

        # Parse session name from -t flag
        for i, arg in enumerate(cmd):
            if arg == "-t" and i + 1 < len(cmd):
                session_name = cmd[i + 1]
                break

        if session_name and session_name in self.sessions:
            return Mock(returncode=0, stdout="", stderr="")

        return Mock(returncode=1, stdout="", stderr="no such session")

    def add_session_output(self, session_name, output):
        """Add output to a mock session."""
        if session_name in self.sessions:
            self.sessions[session_name].add_output(output)

    def kill_session(self, session_name):
        """Mark session as terminated."""
        if session_name in self.sessions:
            self.sessions[session_name].running = False


@contextmanager
def mock_tmux_fixture():
    """Fixture that provides a mock tmux environment."""
    mock_tmux = MockTmux()

    with patch("subprocess.run", side_effect=mock_tmux.mock_subprocess_run):
        yield mock_tmux
