#!/usr/bin/env python3
"""
Pair Monitor - Simplified health monitoring for dual-agent pair sessions.

Monitors agent health by checking log activity. If an agent has no new log output
for 5 minutes, it is restarted. Each agent gets max 3 restarts.

Usage:
    python3 .claude/scripts/pair_monitor.py \
        --session-id "pair-1234567890" \
        --coder-agent "<coder-agent-name>" \
        --verifier-agent "<verifier-agent-name>" \
        --bead-id "pair-1234567890" \
        --coder-cmd "python3 ... " \
        --verifier-cmd "python3 ... " \
        --interval 60 \
        --log-idle-timeout 300
"""

import argparse
import fcntl
import json
import os
import shlex
import shutil
import subprocess  # nosec
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

# Constants
DEFAULT_INTERVAL = 60  # Check every 60 seconds
DEFAULT_LOG_IDLE_TIMEOUT = 300  # 5 minutes of no log activity = stuck
DEFAULT_MAX_RESTARTS = 3
DEFAULT_MAX_ITERATIONS = 60  # 1 hour at default 60s interval
DEFAULT_STARTUP_MISS_GRACE_CHECKS = 3  # tolerate brief tmux startup races
TMUX_CMD_TIMEOUT = 30

# Status file paths
BEADS_FILE = ".beads/beads.left.jsonl"
STATUS_DIR = Path(tempfile.gettempdir()) / "pair_sessions"
TMUX_BIN = shutil.which("tmux")


class AgentState:
    """Tracks state for a single agent."""

    def __init__(self, name: str, tmux_session: str, restart_cmd: str):
        self.name = name
        self.tmux_session = tmux_session
        self.restart_cmd = restart_cmd
        self.restart_count = 0
        self.last_log_size = 0
        self.last_check_time = time.time()
        self.status = "starting"  # starting, running, stuck, restarted, completed, failed
        self.startup_miss_checks = 0  # consecutive startup checks with no discoverable tmux session


class PairMonitor:
    """Simplified health monitor for dual-agent pair sessions."""

    def __init__(
        self,
        session_id: str,
        coder_agent: str,
        verifier_agent: str,
        bead_id: str,
        coder_cmd: str,
        verifier_cmd: str,
        interval: int = DEFAULT_INTERVAL,
        log_idle_timeout: int = DEFAULT_LOG_IDLE_TIMEOUT,
        max_restarts: int = DEFAULT_MAX_RESTARTS,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
        startup_miss_grace_checks: int = DEFAULT_STARTUP_MISS_GRACE_CHECKS,
        tmux_sockets: list[str] | None = None,
        session_dir: Path | None = None,
    ):
        self.session_id = session_id
        self.coder_agent = coder_agent
        self.verifier_agent = verifier_agent
        self.bead_id = bead_id
        self.coder_cmd = coder_cmd
        self.verifier_cmd = verifier_cmd
        self.interval = interval
        self.log_idle_timeout = log_idle_timeout
        self.max_restarts = max_restarts
        self.max_iterations = max_iterations
        self.startup_miss_grace_checks = max(0, startup_miss_grace_checks)

        # Custom tmux sockets from orchestration
        self.tmux_sockets = tmux_sockets or []

        # Session directory
        if session_dir:
            self.session_dir = session_dir
        else:
            self.session_dir = STATUS_DIR / session_id
        self.session_dir.mkdir(parents=True, exist_ok=True)

        # Agent log files (monitor writes to these for each agent)
        self.coder_log = self.session_dir / f"{coder_agent}.log"
        self.verifier_log = self.session_dir / f"{verifier_agent}.log"

        # Agent states - will be initialized after we find their tmux sessions
        self.coder_state: AgentState | None = None
        self.verifier_state: AgentState | None = None

        # Track which agent is which for commands
        self._agent_by_session = {}

        self.log(f"Pair Monitor initialized for session {session_id}")
        self.log(f"Session directory: {self.session_dir}")
        self.log(f"Interval: {interval}s, Log idle timeout: {log_idle_timeout}s, Max restarts: {max_restarts}")

        if TMUX_BIN is None:
            self.log("Error: tmux not found on PATH")

    def log(self, message: str):
        """Log message with timestamp."""
        timestamp = datetime.now(UTC).isoformat()
        print(f"[{timestamp}] {message}", flush=True)

    def _tmux_cmd(self, socket_name: str | None = None) -> list[str]:
        """Build tmux base command, optionally with custom socket."""
        if TMUX_BIN is None:
            raise RuntimeError("tmux binary not available")
        cmd = [TMUX_BIN]
        if socket_name:
            cmd.extend(["-L", socket_name])
        return cmd

    def _find_session_on_sockets(self, session_name: str) -> str | None:
        """Try to find a tmux session across custom sockets, then default."""
        if TMUX_BIN is None:
            return None
        # Try custom sockets first
        for socket in self.tmux_sockets:
            try:
                result = subprocess.run(
                    [TMUX_BIN, "-L", socket, "has-session", "-t", session_name],
                    capture_output=True, text=True, check=False, timeout=TMUX_CMD_TIMEOUT,
                )
                if result.returncode == 0:
                    return socket
            except (subprocess.TimeoutExpired, OSError):
                continue

        # Scan /tmp for orchestration sockets only when no explicit socket list
        # is provided. Explicit sockets are session-scoped and must be authoritative.
        if not self.tmux_sockets:
            tmp_dir = Path("/tmp")
            for tmux_dir in tmp_dir.glob("tmux-*/"):
                try:
                    dir_entries = list(tmux_dir.iterdir())
                except OSError:
                    continue
                for socket_file in dir_entries:
                    sock_name = socket_file.name
                    if sock_name.startswith("orch-") and sock_name not in self.tmux_sockets:
                        try:
                            result = subprocess.run(
                                [TMUX_BIN, "-L", sock_name, "has-session", "-t", session_name],
                                capture_output=True, text=True, check=False, timeout=TMUX_CMD_TIMEOUT,
                            )
                            if result.returncode == 0:
                                self.tmux_sockets.append(sock_name)
                                return sock_name
                        except (subprocess.TimeoutExpired, OSError):
                            continue

        # Fall back to default socket
        try:
            result = subprocess.run(
                [TMUX_BIN, "has-session", "-t", session_name],
                capture_output=True, text=True, check=False, timeout=TMUX_CMD_TIMEOUT,
            )
            if result.returncode == 0:
                return ""
        except (subprocess.TimeoutExpired, OSError):
            pass

        return None

    def get_agent_log_path(self, agent_name: str) -> Path:
        """Get the log file path for an agent."""
        return self.session_dir / f"{agent_name}.log"

    def _check_orchestration_result_file(self, agent_name: str) -> dict | None:
        """Read the newest orchestration result file for this agent and session."""
        result_dir = Path(tempfile.gettempdir()) / "orchestration_results"
        if not result_dir.exists():
            return None

        pattern = f"{agent_name}_results_*.json"
        candidates = sorted(result_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
        for candidate in candidates:
            try:
                with open(candidate, encoding="utf-8") as f:
                    data = json.load(f)
            except (OSError, json.JSONDecodeError):
                continue

            file_session_id = data.get("session_id")
            if file_session_id and file_session_id != self.session_id:
                continue
            return data
        return None

    def _check_agent_finished(self, agent_state: AgentState) -> bool:
        """Check if agent has finished by looking for completion signals in log."""
        log_path = self.get_agent_log_path(agent_state.name)
        if not log_path or not log_path.exists():
            return False

        try:
            with open(log_path, encoding="utf-8", errors="ignore") as f:
                content = f.read()
            # Check for completion signals
            completion_signals = [
                "Agent execution completed",
                "session completed",
                "exit code: 0",
                "successfully exiting",
            ]
            for signal in completion_signals:
                if signal.lower() in content.lower():
                    return True
        except OSError:
            pass
        return False

    def check_log_activity(self, agent_state: AgentState) -> tuple[bool, int]:
        """Check if agent has new log output since last check.

        Args:
            agent_state: AgentState object to track log size

        Returns (has_activity, current_log_size).
        """
        log_path = self.get_agent_log_path(agent_state.name)

        if not log_path.exists():
            return True, 0  # First check - assume active

        try:
            current_size = log_path.stat().st_size
            has_activity = current_size > agent_state.last_log_size
            agent_state.last_log_size = current_size
            return has_activity, current_size
        except OSError:
            return True, 0

    def restart_agent(self, agent_state: AgentState) -> bool:
        """Restart a stuck agent.

        Returns True if restart was successful, False if max restarts exceeded.
        """
        if agent_state.restart_count >= self.max_restarts:
            self.log(f"❌ {agent_state.name}: Max restarts ({self.max_restarts}) exceeded")
            agent_state.status = "failed"
            return False

        agent_state.restart_count += 1
        self.log(f"🔄 {agent_state.name}: Restarting (attempt {agent_state.restart_count}/{self.max_restarts})")

        # Kill existing session
        socket = self._find_session_on_sockets(agent_state.tmux_session)
        if socket is not None:
            try:
                subprocess.run(
                    self._tmux_cmd(socket if socket else None) + ["kill-session", "-t", agent_state.tmux_session],
                    capture_output=True, check=False, timeout=TMUX_CMD_TIMEOUT,
                )
            except (subprocess.TimeoutExpired, OSError, RuntimeError):
                pass

        # Wait a moment for session to be cleaned up
        time.sleep(2)

        # Start new session with the restart command
        if not agent_state.restart_cmd.strip():
            self.log(f"❌ {agent_state.name}: Missing restart command")
            agent_state.status = "failed"
            return False

        try:
            restart_cmd_parts = shlex.split(agent_state.restart_cmd)
            # Launch restart bootstrap outside the target tmux session name.
            # The orchestration command will create/own the agent tmux session itself.
            subprocess.Popen(  # noqa: S603 # nosec
                restart_cmd_parts,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )

            # Wait briefly for orchestrator to recreate the target agent session.
            for _ in range(5):
                if self._find_session_on_sockets(agent_state.tmux_session) is not None:
                    agent_state.status = "running"
                    self.log(f"✅ {agent_state.name}: Restarted successfully")
                    return True
                time.sleep(1)

            raise RuntimeError(
                f"target session '{agent_state.tmux_session}' not found after restart bootstrap"
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError, RuntimeError) as exc:
            self.log(f"❌ {agent_state.name}: Restart failed: {exc}")
            agent_state.status = "failed"
            return False

    def update_bead_status(self, status: str) -> bool:
        """Update bead status in beads file."""
        try:
            beads_path = Path(BEADS_FILE)
            if not beads_path.exists():
                return False

            with open(beads_path, "r+", encoding="utf-8") as f:
                try:
                    fcntl.flock(f, fcntl.LOCK_EX)
                    lines = f.readlines()
                    beads = []
                    for line in lines:
                        if line.strip():
                            beads.append(json.loads(line.strip()))

                    updated = False
                    for bead in beads:
                        if bead.get("id") == self.bead_id:
                            bead["status"] = status
                            bead["updated_at"] = datetime.now(UTC).isoformat()
                            updated = True
                            break

                    if not updated:
                        beads.append({
                            "id": self.bead_id,
                            "title": f"Pair Session: {self.session_id}",
                            "description": "Dual-agent pair programming session",
                            "status": status,
                            "priority": 1,
                            "issue_type": "task",
                            "created_at": datetime.now(UTC).isoformat(),
                            "updated_at": datetime.now(UTC).isoformat(),
                        })

                    f.seek(0)
                    f.truncate()
                    for bead in beads:
                        f.write(json.dumps(bead) + "\n")
                    f.flush()
                    os.fsync(f.fileno())
                finally:
                    fcntl.flock(f, fcntl.LOCK_UN)

            return True
        except Exception as e:
            self.log(f"Error updating bead: {e}")
            return False

    def run_iteration(self) -> str:
        """Run a single monitoring iteration. Returns session status."""
        # Guard: ensure run() has been called to initialize agent states
        if not hasattr(self, 'coder_state') or not hasattr(self, 'verifier_state'):
            raise RuntimeError("run_iteration() called before run() - must call run() first to initialize agent states")
        if self.coder_state is None or self.verifier_state is None:
            raise RuntimeError("run_iteration() called before run() - must call run() first to initialize agent states")

        iteration = getattr(self, '_iteration', 0) + 1
        self._iteration = iteration
        self.log(f"--- Iteration {iteration} ---")

        # Track overall status
        coder_running = False
        verifier_running = False
        coder_completed = False
        verifier_completed = False

        # Check coder agent
        coder_result = self._check_orchestration_result_file(self.coder_state.name)
        if coder_result and str(coder_result.get("status")).lower() in {"completed", "success", "passed"}:
            self.coder_state.status = "completed"
            coder_completed = True

        coder_socket = self._find_session_on_sockets(self.coder_state.tmux_session)
        if coder_socket is not None:
            coder_running = True
            self.coder_state.startup_miss_checks = 0

            # Check log activity
            has_activity, log_size = self.check_log_activity(self.coder_state)
            previous_check_time = self.coder_state.last_check_time
            idle_time = time.time() - previous_check_time

            if self.coder_state.status == "completed":
                self.log(f"✓ {self.coder_state.name}: completed (result file present)")
            elif not has_activity and idle_time >= self.log_idle_timeout:
                self.log(f"⚠️ {self.coder_state.name}: No activity for {idle_time:.0f}s (>{self.log_idle_timeout}s)")
                if self.restart_agent(self.coder_state):
                    self.coder_state.last_check_time = time.time()
                else:
                    self.log(f"❌ {self.coder_state.name}: Failed - max restarts exceeded")
            else:
                self.coder_state.status = "running"
                if has_activity:
                    self.coder_state.last_check_time = time.time()
                    self.log(f"✓ {self.coder_state.name}: running (log size: {log_size})")
                else:
                    # Preserve timestamp so sustained inactivity can trigger restart on later checks.
                    self.coder_state.last_check_time = previous_check_time
                    self.log(
                        f"⏳ {self.coder_state.name}: idle for {idle_time:.0f}s "
                        f"(threshold {self.log_idle_timeout}s)"
                    )
        else:
            self.log(f"✗ {self.coder_state.name}: not found")
            # Check if agent finished (by looking at log for completion signal)
            if self._check_agent_finished(self.coder_state):
                self.coder_state.status = "completed"
                coder_completed = True
                self.coder_state.startup_miss_checks = 0
            elif (
                self.coder_state.status == "starting"
                and self.coder_state.startup_miss_checks < self.startup_miss_grace_checks
            ):
                self.coder_state.startup_miss_checks += 1
                self.log(
                    f"⏳ {self.coder_state.name}: startup tmux session not visible yet "
                    f"({self.coder_state.startup_miss_checks}/{self.startup_miss_grace_checks})"
                )
            elif self.coder_state.status != "completed":
                self.coder_state.status = "failed"

        # Check verifier agent
        verifier_result = self._check_orchestration_result_file(self.verifier_state.name)
        if verifier_result and str(verifier_result.get("status")).lower() in {"completed", "success", "passed"}:
            self.verifier_state.status = "completed"
            verifier_completed = True

        verifier_socket = self._find_session_on_sockets(self.verifier_state.tmux_session)
        if verifier_socket is not None:
            verifier_running = True
            self.verifier_state.startup_miss_checks = 0

            # Check log activity
            has_activity, log_size = self.check_log_activity(self.verifier_state)
            previous_check_time = self.verifier_state.last_check_time
            idle_time = time.time() - previous_check_time

            if self.verifier_state.status == "completed":
                self.log(f"✓ {self.verifier_state.name}: completed (result file present)")
            elif not has_activity and idle_time >= self.log_idle_timeout:
                self.log(f"⚠️ {self.verifier_state.name}: No activity for {idle_time:.0f}s (>{self.log_idle_timeout}s)")
                if self.restart_agent(self.verifier_state):
                    self.verifier_state.last_check_time = time.time()
                else:
                    self.log(f"❌ {self.verifier_state.name}: Failed - max restarts exceeded")
            else:
                self.verifier_state.status = "running"
                if has_activity:
                    self.verifier_state.last_check_time = time.time()
                    self.log(f"✓ {self.verifier_state.name}: running (log size: {log_size})")
                else:
                    # Preserve timestamp so sustained inactivity can trigger restart on later checks.
                    self.verifier_state.last_check_time = previous_check_time
                    self.log(
                        f"⏳ {self.verifier_state.name}: idle for {idle_time:.0f}s "
                        f"(threshold {self.log_idle_timeout}s)"
                    )
        else:
            self.log(f"✗ {self.verifier_state.name}: not found")
            # Check if agent finished (by looking at log for completion signal)
            if self._check_agent_finished(self.verifier_state):
                self.verifier_state.status = "completed"
                verifier_completed = True
                self.verifier_state.startup_miss_checks = 0
            elif (
                self.verifier_state.status == "starting"
                and self.verifier_state.startup_miss_checks < self.startup_miss_grace_checks
            ):
                self.verifier_state.startup_miss_checks += 1
                self.log(
                    f"⏳ {self.verifier_state.name}: startup tmux session not visible yet "
                    f"({self.verifier_state.startup_miss_checks}/{self.startup_miss_grace_checks})"
                )
            elif self.verifier_state.status != "completed":
                self.verifier_state.status = "failed"

        # Determine completion
        coder_completed = self.coder_state.status == "completed"
        verifier_completed = self.verifier_state.status == "completed"

        # Emit session-local status artifact each iteration for orchestrator handoff.
        self._write_status_file(coder_running=coder_running, verifier_running=verifier_running)

        # Check for failures
        if self.coder_state.status == "failed" or self.verifier_state.status == "failed":
            self.log("❌ Agent failed - max restarts exceeded")
            self.update_bead_status("failed")
            return "failed"

        # Both completed
        if coder_completed and verifier_completed:
            self.log("✅ Both agents completed!")
            self.update_bead_status("completed")
            return "completed"

        # During startup grace, temporary socket misses are non-terminal.
        if self.coder_state.status == "starting" or self.verifier_state.status == "starting":
            return "in_progress"

        # Both not running (session ended)
        if not coder_running and not verifier_running:
            self.log("⚠️ Both agents not running - session ended")
            self.update_bead_status("ended")
            return "ended"

        return "in_progress"

    def _write_status_file(self, coder_running: bool, verifier_running: bool) -> None:
        """Persist monitor status to session_dir/status.json."""
        status_payload = {
            "session_id": self.session_id,
            "bead_id": self.bead_id,
            "coder_agent": self.coder_agent,
            "verifier_agent": self.verifier_agent,
            "coder_status": self.coder_state.status if self.coder_state else "unknown",
            "verifier_status": self.verifier_state.status if self.verifier_state else "unknown",
            "coder_running": bool(coder_running),
            "verifier_running": bool(verifier_running),
            "iteration": int(getattr(self, "_iteration", 0)),
            "updated_at": datetime.now(UTC).isoformat(),
        }
        coder_status = str(status_payload["coder_status"]).lower()
        verifier_status = str(status_payload["verifier_status"]).lower()
        if coder_status in {"completed", "failed", "error"} and verifier_status in {"completed", "failed", "error"}:
            status_payload["session_status"] = "completed" if coder_status == verifier_status == "completed" else "failed"
        elif coder_status in {"failed", "error"} or verifier_status in {"failed", "error"}:
            status_payload["session_status"] = "failed"
        elif not coder_running and not verifier_running and coder_status not in {"starting", "unknown"} and verifier_status not in {"starting", "unknown"}:
            status_payload["session_status"] = "ended"
        else:
            status_payload["session_status"] = "in_progress"

        status_file = self.session_dir / "status.json"
        try:
            with open(status_file, "w", encoding="utf-8") as f:
                json.dump(status_payload, f, indent=2)
        except OSError as exc:
            self.log(f"Warning: failed to write status file {status_file}: {exc}")

    def run(self):
        """Run the monitoring loop."""
        self.log(f"Starting pair monitor for session {self.session_id}")
        self.update_bead_status("in_progress")

        # Initialize agent states (we need the tmux session names, not the agent names)
        # The coder_agent and verifier_agent args are actually tmux session names
        self.coder_state = AgentState(
            name=self.coder_agent,
            tmux_session=self.coder_agent,
            restart_cmd=self.coder_cmd,
        )
        self.verifier_state = AgentState(
            name=self.verifier_agent,
            tmux_session=self.verifier_agent,
            restart_cmd=self.verifier_cmd,
        )

        while True:
            status = self.run_iteration()

            if status in ("completed", "failed", "ended"):
                self.log(f"Monitor exiting with status: {status}")
                break

            # Skip iteration check if max_iterations is 0 or None (run forever)
            if self.max_iterations and self._iteration >= self.max_iterations:
                self.log(
                    f"⚠️ Reached monitor iteration budget ({self.max_iterations}); timing out session"
                )
                self.update_bead_status("timeout")
                status = "timeout"
                self._write_status_file(coder_running=False, verifier_running=False)
                break

            # Wait for next interval
            self.log(f"Sleeping for {self.interval}s...")
            time.sleep(self.interval)

        self.log("Pair monitor finished")
        return status


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Monitor dual-agent pair programming sessions - simplified health monitoring",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
    python3 .claude/scripts/pair_monitor.py \\
        --session-id pair-1234567890 \\
        --coder-agent coder-session-name \\
        --verifier-agent verifier-session-name \\
        --bead-id pair-1234567890 \\
        --interval 60 \\
        --log-idle-timeout 300
        """,
    )

    parser.add_argument("--session-id", required=True, help="Unique session identifier")
    parser.add_argument("--coder-agent", required=True, help="Coder tmux session name")
    parser.add_argument("--verifier-agent", required=True, help="Verifier tmux session name")
    parser.add_argument("--bead-id", required=True, help="Bead ID for state tracking")
    parser.add_argument("--coder-cmd", default="", help="Command to restart coder (not implemented)")
    parser.add_argument("--verifier-cmd", default="", help="Command to restart verifier (not implemented)")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL, help=f"Check interval in seconds (default: {DEFAULT_INTERVAL})")
    parser.add_argument("--log-idle-timeout", type=int, default=DEFAULT_LOG_IDLE_TIMEOUT, help=f"Log idle timeout in seconds (default: {DEFAULT_LOG_IDLE_TIMEOUT})")
    parser.add_argument("--max-restarts", type=int, default=DEFAULT_MAX_RESTARTS, help=f"Max restarts per agent (default: {DEFAULT_MAX_RESTARTS})")
    parser.add_argument("--max-iterations", type=int, default=DEFAULT_MAX_ITERATIONS, help=f"Max monitor iterations before timeout (default: {DEFAULT_MAX_ITERATIONS})")
    parser.add_argument("--tmux-sockets", nargs="*", default=[], help="Custom tmux socket names")
    parser.add_argument("--session-dir", help="Path to session directory")

    args = parser.parse_args()

    monitor = PairMonitor(
        session_id=args.session_id,
        coder_agent=args.coder_agent,
        verifier_agent=args.verifier_agent,
        bead_id=args.bead_id,
        coder_cmd=args.coder_cmd,
        verifier_cmd=args.verifier_cmd,
        interval=args.interval,
        log_idle_timeout=args.log_idle_timeout,
        max_restarts=args.max_restarts,
        max_iterations=args.max_iterations,
        tmux_sockets=args.tmux_sockets,
        session_dir=Path(args.session_dir) if args.session_dir else None,
    )

    status = monitor.run()

    if status == "completed":
        sys.exit(0)
    elif status == "failed":
        sys.exit(1)
    elif status in {"ended", "timeout"}:
        sys.exit(2)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()
