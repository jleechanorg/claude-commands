#!/usr/bin/env python3
"""Real integration tests for .claude/scripts/pair_execute.py.

These tests run the real pair command (no subprocess mocking) and validate
session artifacts/logs produced by the launcher.

Run explicitly:
    RUN_REAL_PAIR_INTEGRATION=1 ./vpython -m pytest .claude/scripts/integration/test_pair_real_integration.py -q
"""

from __future__ import annotations

import json
import os
import re
import shutil
import signal
import subprocess
import tempfile
import time
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PAIR_EXECUTE = PROJECT_ROOT / ".claude" / "scripts" / "pair_execute.py"


def _require_real_env() -> None:
    if os.environ.get("RUN_REAL_PAIR_INTEGRATION") != "1":
        raise unittest.SkipTest(
            "Set RUN_REAL_PAIR_INTEGRATION=1 to run real pair integration tests."
        )
    if not PAIR_EXECUTE.exists():
        raise unittest.SkipTest(f"Missing pair_execute.py at {PAIR_EXECUTE}")
    if shutil.which("python3") is None:
        raise unittest.SkipTest("python3 not found in PATH")
    if shutil.which("tmux") is None:
        raise unittest.SkipTest("tmux not found in PATH")
    if not os.environ.get("MINIMAX_API_KEY"):
        raise unittest.SkipTest("MINIMAX_API_KEY is required for real MiniMax pair integration tests")


def _parse_session_dir(stdout: str) -> Path | None:
    match = re.search(r"Session Dir:\s*(.+)", stdout)
    if not match:
        return None
    return Path(match.group(1).strip())


def _parse_pair_socket(stdout: str) -> str | None:
    match = re.search(r"Using shared tmux socket for pair session:\s*([^\s]+)", stdout)
    if not match:
        return None
    return match.group(1).strip()


def _parse_coder_agent(stdout: str) -> str | None:
    match = re.search(r"Coder Agent \([^)]+\):\s*([^\s]+)", stdout)
    if not match:
        return None
    return match.group(1).strip()


def _parse_verifier_agent(stdout: str) -> str | None:
    match = re.search(r"Verifier Agent \([^)]+\):\s*([^\s]+)", stdout)
    if not match:
        return None
    return match.group(1).strip()


def _wait_for_log_pattern(
    log_path: Path, pattern: str, timeout: int = 90, poll_interval: int = 5
) -> str | None:
    """Poll an orchestration log file for a regex pattern.

    Returns the matched text if found within timeout, else None.
    """
    deadline = time.time() + timeout
    compiled = re.compile(pattern, re.IGNORECASE)
    while time.time() < deadline:
        if log_path.exists():
            try:
                content = log_path.read_text(encoding="utf-8", errors="replace")
                match = compiled.search(content)
                if match:
                    return match.group(0)
            except OSError:
                pass
        time.sleep(poll_interval)
    return None


def _kill_monitor(session_dir: Path) -> None:
    pid_file = session_dir / "monitor.pid"
    if not pid_file.exists():
        return
    try:
        pid = int(pid_file.read_text(encoding="utf-8").strip())
        os.kill(pid, signal.SIGTERM)
    except (OSError, ValueError):
        return


def _cleanup_tmux_socket(socket_name: str | None) -> None:
    if not socket_name:
        return
    subprocess.run(
        ["tmux", "-L", socket_name, "kill-server"],
        check=False,
        capture_output=True,
        text=True,
    )


def _assert_no_leaked_tmux_sessions(socket_name: str | None) -> list[str]:
    """Return list of live tmux sessions on the tested socket (should be empty)."""
    if not socket_name:
        return []
    result = subprocess.run(
        ["tmux", "-L", socket_name, "list-sessions", "-F", "#{session_name}"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []  # No server = no leaked sessions
    return [s.strip() for s in result.stdout.strip().splitlines() if s.strip()]


def _assert_no_leaked_monitor(session_dir: Path) -> int | None:
    """Return monitor PID if it's still alive (should be None)."""
    pid_file = session_dir / "monitor.pid"
    if not pid_file.exists():
        return None
    try:
        pid = int(pid_file.read_text(encoding="utf-8").strip())
        os.kill(pid, 0)  # Check if process exists (signal 0)
        return pid  # Still alive - leaked
    except (OSError, ValueError):
        return None  # Process is gone - clean


def _cli_preflight_unavailable(stdout: str, cli_upper: str, role: str) -> bool:
    out_lower = stdout.lower()
    return (
        f"failed to launch {cli_upper.lower()} {role.lower()} agent" in out_lower
        and "no fallback available" in out_lower
    )


def _write_pair_program(tmpdir: Path, broken: bool) -> None:
    if broken:
        test_program = """#!/usr/bin/env python3
\"\"\"Simple test program for /pair command testing.\"\"\"

def hello_world():
    return None


def add(a: int, b: int) -> int:
    return None
"""
    else:
        test_program = """#!/usr/bin/env python3
\"\"\"Simple test program for /pair command testing.\"\"\"

def hello_world():
    return \"Hello from pair test program!\"


def add(a: int, b: int) -> int:
    return a + b
"""

    test_pair_program = """#!/usr/bin/env python3
import pytest
from test_program import hello_world, add


def test_hello_world():
    assert hello_world() == "Hello from pair test program!"


def test_add_positive():
    assert add(2, 3) == 5


def test_add_negative():
    assert add(-1, 1) == 0


def test_add_zero():
    assert add(0, 0) == 0
"""
    (tmpdir / "test_program.py").write_text(test_program, encoding="utf-8")
    (tmpdir / "test_pair_program.py").write_text(test_pair_program, encoding="utf-8")

    # Initialize git repo with an initial commit so get_sanitized_branch()
    # returns a real branch name instead of "unknown".
    # git rev-parse --abbrev-ref HEAD fails if there are no commits.
    git_env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "test",
        "GIT_AUTHOR_EMAIL": "test@test.com",
        "GIT_COMMITTER_NAME": "test",
        "GIT_COMMITTER_EMAIL": "test@test.com",
    }
    subprocess.run(
        ["git", "init", "-b", "test-pair-integration"],
        cwd=tmpdir,
        capture_output=True,
        check=False,
        env=git_env,
    )
    subprocess.run(
        ["git", "add", "."],
        cwd=tmpdir,
        capture_output=True,
        check=False,
        env=git_env,
    )
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=tmpdir,
        capture_output=True,
        check=False,
        env=git_env,
    )


class TestPairRealIntegration(unittest.TestCase):
    """Real pair integration tests (no mocks)."""

    @classmethod
    def setUpClass(cls) -> None:
        _require_real_env()

    def test_real_pair_launches_and_writes_session_artifacts(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pair-real-success-") as tmpdir:
            workdir = Path(tmpdir)
            _write_pair_program(workdir, broken=False)

            cmd = [
                "python3",
                str(PAIR_EXECUTE),
                "--no-worktree",
                "--coder-cli",
                "minimax",
                "--verifier-cli",
                "minimax",
                "Run pytest on test_pair_program.py and report result",
            ]
            result = subprocess.run(
                cmd,
                cwd=workdir,
                capture_output=True,
                text=True,
                timeout=180,
                check=False,
            )

            session_dir = _parse_session_dir(result.stdout)
            socket_name = _parse_pair_socket(result.stdout)
            coder_agent = _parse_coder_agent(result.stdout)
            try:
                if _cli_preflight_unavailable(result.stdout, "MINIMAX", "coder"):
                    self.skipTest("Skipping: minimax coder preflight unavailable in this environment")

                self.assertEqual(
                    result.returncode,
                    0,
                    msg=f"pair launch failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}",
                )
                self.assertIn("Coder Agent (MINIMAX)", result.stdout)
                self.assertIn("Verifier Agent (MINIMAX)", result.stdout)
                self.assertIsNotNone(session_dir, "Session Dir not found in launcher output")
                assert session_dir is not None

                # REV-79tmf: Exactly one session directory per test execution
                session_dir_count = result.stdout.count("Session Dir:")
                self.assertEqual(
                    session_dir_count,
                    1,
                    f"Expected exactly 1 session creation, found {session_dir_count}",
                )
                self.assertTrue(session_dir.exists())
                self.assertTrue((session_dir / "monitor.log").exists())
                self.assertTrue((session_dir / "status.json").exists())

                status_text = (session_dir / "status.json").read_text(encoding="utf-8")
                self.assertIn("session_status", status_text)

                # REV-b2kd8: Require terminal status - in_progress is NOT acceptable
                status_data = json.loads(status_text)
                terminal_states = {"completed", "failed", "ended", "timeout"}
                session_status = status_data.get("session_status", "")
                self.assertIn(
                    session_status,
                    terminal_states,
                    f"Monitor status must be terminal, got '{session_status}'. "
                    f"status.json: {status_text[:500]}",
                )

                # Issue 1 fix: verify branch detection works (not "unknown")
                self.assertNotIn(
                    "unknown",
                    result.stdout.split("Coder Agent")[0],
                    "Branch should resolve to 'testpairintegration', not 'unknown'",
                )

                # Issue 2+3+7 fix: validate agent actually ran pytest
                if coder_agent:
                    orch_log = Path("/tmp/orchestration_logs") / f"{coder_agent}.log"
                    match = _wait_for_log_pattern(
                        orch_log, r"\d+ passed", timeout=90
                    )
                    self.assertIsNotNone(
                        match,
                        f"Coder agent should have run pytest (looked in {orch_log})",
                    )

                    # Verify MCP Mail registration instructions present
                    brainstorm = session_dir / "brainstorm_results.json"
                    if brainstorm.exists():
                        brainstorm_text = brainstorm.read_text(encoding="utf-8")
                        self.assertIn(
                            "register_agent",
                            brainstorm_text,
                            "Instructions must include MCP Mail registration step",
                        )
            finally:
                if session_dir and session_dir.exists():
                    _kill_monitor(session_dir)
                _cleanup_tmux_socket(socket_name)

                # REV-58kq8: Verify teardown hygiene
                leaked_sessions = _assert_no_leaked_tmux_sessions(socket_name)
                self.assertEqual(
                    leaked_sessions,
                    [],
                    f"Leaked tmux sessions after teardown: {leaked_sessions}",
                )
                if session_dir:
                    leaked_pid = _assert_no_leaked_monitor(session_dir)
                    self.assertIsNone(
                        leaked_pid,
                        f"Monitor process {leaked_pid} still alive after teardown",
                    )

    def test_real_pair_uses_minimax_for_both_roles_in_session_output(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pair-real-strict-") as tmpdir:
            workdir = Path(tmpdir)
            _write_pair_program(workdir, broken=True)

            cmd = [
                "python3",
                str(PAIR_EXECUTE),
                "--no-worktree",
                "--interval",
                "5",
                "--max-iterations",
                "2",
                "--coder-cli",
                "minimax",
                "--verifier-cli",
                "minimax",
                "Implement and test test_program.py",
            ]
            result = subprocess.run(
                cmd,
                cwd=workdir,
                capture_output=True,
                text=True,
                timeout=180,
                check=False,
            )

            session_dir = _parse_session_dir(result.stdout)
            socket_name = _parse_pair_socket(result.stdout)
            coder_agent = _parse_coder_agent(result.stdout)
            verifier_agent = _parse_verifier_agent(result.stdout)
            try:
                if _cli_preflight_unavailable(result.stdout, "MINIMAX", "coder"):
                    self.skipTest(
                        "Skipping minimax role test: minimax coder preflight unavailable in this environment"
                    )
                self.assertEqual(
                    result.returncode,
                    0,
                    msg=f"pair launcher unexpectedly failed\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}",
                )
                self.assertIn("Coder Agent (MINIMAX)", result.stdout)
                self.assertIn("Verifier Agent (MINIMAX)", result.stdout)
                self.assertNotIn("Coder Agent (CLAUDE)", result.stdout)
                self.assertNotIn("Verifier Agent (CODEX)", result.stdout)

                # REV-79tmf: Exactly one session directory per test execution
                session_dir_count = result.stdout.count("Session Dir:")
                self.assertEqual(
                    session_dir_count,
                    1,
                    f"Expected exactly 1 session creation, found {session_dir_count}",
                )

                if session_dir and session_dir.exists():
                    verifier_logs = sorted(session_dir.glob("*verifier.log"))
                    self.assertTrue(verifier_logs, "expected verifier log in session dir")
                    verifier_log = verifier_logs[-1].read_text(encoding="utf-8", errors="replace")
                    self.assertNotIn("using Claude CLI", verifier_log)

                    # Give monitor one cycle to reflect verifier failure state.
                    time.sleep(7)
                    status_text = (session_dir / "status.json").read_text(
                        encoding="utf-8",
                        errors="replace",
                    )
                    self.assertIn("verifier_status", status_text)
                    self.assertRegex(
                        status_text,
                        r'"verifier_status"\s*:\s*"(starting|running|not_found|failed|error|ended|completed)"',
                    )

                    # REV-b2kd8: Require terminal session status
                    status_data = json.loads(status_text)
                    terminal_states = {"completed", "failed", "ended", "timeout"}
                    session_status = status_data.get("session_status", "")
                    self.assertIn(
                        session_status,
                        terminal_states,
                        f"Monitor status must be terminal, got '{session_status}'",
                    )

                # REV-cqq4w: Validate both agents performed real work (not just launch)
                if coder_agent:
                    orch_log = Path("/tmp/orchestration_logs") / f"{coder_agent}.log"
                    # Launch marker (must exist)
                    match = _wait_for_log_pattern(
                        orch_log, r"CLI chain: minimax", timeout=90
                    )
                    self.assertIsNotNone(
                        match,
                        f"Coder orchestration log should show MiniMax CLI chain ({orch_log})",
                    )
                    # Work marker: agent must show evidence of task execution
                    work_match = _wait_for_log_pattern(
                        orch_log,
                        r"(pytest|test_|IMPLEMENTATION_READY|implement|reading file|writing file)",
                        timeout=90,
                    )
                    self.assertIsNotNone(
                        work_match,
                        f"Coder agent must show task-execution evidence, not just launch ({orch_log})",
                    )

                if verifier_agent:
                    orchestration_log = Path("/tmp/orchestration_logs") / f"{verifier_agent}.log"
                    # Launch marker (must exist)
                    match = _wait_for_log_pattern(
                        orchestration_log, r"CLI chain: minimax", timeout=90
                    )
                    self.assertIsNotNone(
                        match,
                        f"Verifier orchestration log should show MiniMax CLI chain ({orchestration_log})",
                    )
                    orchestration_log_text = orchestration_log.read_text(
                        encoding="utf-8",
                        errors="replace",
                    )
                    self.assertNotIn("using Claude CLI", orchestration_log_text)

                    # Work marker: verifier must show verification evidence
                    work_match = _wait_for_log_pattern(
                        orchestration_log,
                        r"(VERIFICATION|verify|pytest|test_|review|checking)",
                        timeout=90,
                    )
                    self.assertIsNotNone(
                        work_match,
                        f"Verifier agent must show verification evidence, not just launch ({orchestration_log})",
                    )
            finally:
                if session_dir and session_dir.exists():
                    _kill_monitor(session_dir)
                _cleanup_tmux_socket(socket_name)

                # REV-58kq8: Verify teardown hygiene
                leaked_sessions = _assert_no_leaked_tmux_sessions(socket_name)
                self.assertEqual(
                    leaked_sessions,
                    [],
                    f"Leaked tmux sessions after teardown: {leaked_sessions}",
                )
                if session_dir:
                    leaked_pid = _assert_no_leaked_monitor(session_dir)
                    self.assertIsNone(
                        leaked_pid,
                        f"Monitor process {leaked_pid} still alive after teardown",
                    )


if __name__ == "__main__":
    unittest.main(verbosity=2)
