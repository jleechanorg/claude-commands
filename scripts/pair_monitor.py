#!/usr/bin/env python3
"""
Pair Monitor - Background monitoring script for dual-agent pair sessions.

Monitors agent progress every minute, coordinates via Beads and MCP Mail,
and enforces max 10 iterations per agent.

Usage:
    python3 scripts/pair_monitor.py \
        --session-id "pair-1234567890" \
        --coder-agent "<coder-agent-name>" \
        --verifier-agent "<verifier-agent-name>" \
        --bead-id "pair-1234567890" \
        --max-iterations 10 \
        --interval 60
"""

import argparse
import fcntl
import json
import os
import shutil
import subprocess  # nosec
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

# Constants
DEFAULT_INTERVAL = 60  # 1 minute
DEFAULT_MAX_ITERATIONS = 10
STUCK_THRESHOLD = 3  # Iterations without progress before warning

# Status file paths
BEADS_FILE = ".beads/beads.left.jsonl"
STATUS_DIR = Path(tempfile.gettempdir()) / "pair_sessions"
TMUX_BIN = shutil.which("tmux")


class PairMonitor:
    """Monitor for dual-agent pair programming sessions."""

    def __init__(
        self,
        session_id: str,
        coder_agent: str,
        verifier_agent: str,
        bead_id: str,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
        interval: int = DEFAULT_INTERVAL,
    ):
        self.session_id = session_id
        self.coder_agent = coder_agent
        self.verifier_agent = verifier_agent
        self.bead_id = bead_id
        self.max_iterations = max_iterations
        self.interval = interval

        # Tracking state
        self.coder_iterations = 0
        self.verifier_iterations = 0
        self.coder_last_progress: dict | None = None
        self.verifier_last_progress: dict | None = None
        self.coder_stuck_count = 0
        self.verifier_stuck_count = 0

        # Session directory
        self.session_dir = STATUS_DIR / session_id
        self.session_dir.mkdir(parents=True, exist_ok=True)

        # Status file for file-based fallback
        self.status_file = self.session_dir / "status.json"

        self.log(f"Pair Monitor initialized for session {session_id}")
        self.log(f"Coder agent: {coder_agent}")
        self.log(f"Verifier agent: {verifier_agent}")
        self.log(f"Max iterations: {max_iterations}")
        self.log(f"Interval: {interval}s")
        self.log("Note: MCP Mail integration is stubbed; file-based fallback is used.")
        if TMUX_BIN is None:
            self.log("Error: tmux not found on PATH; agent monitoring will fail.")

    def log(self, message: str):
        """Log message with timestamp."""
        timestamp = datetime.now(UTC).isoformat()
        print(f"[{timestamp}] {message}", flush=True)

    def get_tmux_session_status(self, session_name: str) -> dict:
        """Check status of a tmux session."""
        if TMUX_BIN is None:
            return {"exists": False, "status": "tmux_missing"}

        try:
            # Check if session exists
            result = subprocess.run(  # noqa: S603 # nosec
                [TMUX_BIN, "has-session", "-t", session_name],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )

            if result.returncode != 0:
                return {"exists": False, "status": "not_found"}

            # Get last output from session
            result = subprocess.run(  # noqa: S603 # nosec
                [TMUX_BIN, "capture-pane", "-t", session_name, "-p", "-S", "-50"],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )

            output = result.stdout.strip() if result.returncode == 0 else ""

            # Detect status from output
            status = "running"
            completion_indicators = [
                "Agent completed successfully",
                "Session will auto-close",
                "Task completed",
                "BUILD_COMPLETE",
            ]

            for indicator in completion_indicators:
                if indicator in output:
                    status = "completed"
                    break

            error_indicators = (
                "Traceback (most recent call last):",
                "FATAL:",
                "fatal:",
                # "ERROR:",  # Too generic, triggers on log messages
                # "Error:",  # Too generic
                # "FAILED",  # Too generic
            )
            output_lines = output.splitlines()
            for line in output_lines:
                stripped_line = line.strip()
                if stripped_line.startswith(error_indicators):
                    status = "error"
                    break
                if stripped_line == "exit 1": # Explicit exit code
                    status = "error"
                    break

            return {
                "exists": True,
                "status": status,
                "last_output": output[-500:] if output else "",  # Last 500 chars
            }

        except subprocess.TimeoutExpired:
            return {"exists": True, "status": "timeout", "last_output": ""}
        except Exception as e:
            return {"exists": False, "status": "error", "error": str(e)}

    def check_mcp_mail(self, _agent_id: str, _subject: str | None = None) -> list:
        """Check MCP mail for messages (stub - actual implementation depends on MCP server)."""
        # This would integrate with actual MCP mail server
        # For now, return empty list as placeholder
        # In production, this would call mcp__agentmail__check_inbox
        return []

    def send_mcp_mail(self, to: str, subject: str, body: dict) -> bool:
        """Send MCP mail message (stub - actual implementation depends on MCP server)."""
        # This would integrate with actual MCP mail server
        # For now, log the message as placeholder
        # In production, this would call mcp__agentmail__send_message
        self.log(f"MCP Mail -> {to}: {subject} | Body: {body}")
        return True

    def update_bead_status(self, status: str) -> bool:
        """Update bead status in beads file with fcntl locking."""
        try:
            beads_path = Path(BEADS_FILE)
            if not beads_path.exists():
                self.log(f"Beads file not found: {beads_path}")
                return False

            # Use fcntl for atomic file locking
            with open(beads_path, "r+", encoding="utf-8") as f:
                try:
                    fcntl.flock(f, fcntl.LOCK_EX)
                    
                    # Read all beads
                    lines = f.readlines()
                    beads = []
                    for line in lines:
                        stripped_line = line.strip()
                        if stripped_line:
                            beads.append(json.loads(stripped_line))

                    # Update matching bead
                    updated = False
                    for bead in beads:
                        if bead.get("id") == self.bead_id:
                            bead["status"] = status
                            bead["updated_at"] = datetime.now(UTC).isoformat()
                            updated = True
                            break

                    if not updated:
                        self.log(f"Bead {self.bead_id} not found, creating new entry")
                        beads.append(
                            {
                                "id": self.bead_id,
                                "title": f"Pair Session: {self.session_id}",
                                "description": "Dual-agent pair programming session",
                                "status": status,
                                "priority": 1,
                                "issue_type": "task",
                                "created_at": datetime.now(UTC).isoformat(),
                                "updated_at": datetime.now(UTC).isoformat(),
                            }
                        )

                    # Write back
                    f.seek(0)
                    f.truncate()
                    for bead in beads:
                        f.write(json.dumps(bead) + "\n")
                    f.flush()
                    os.fsync(f.fileno())
                    
                finally:
                    fcntl.flock(f, fcntl.LOCK_UN)

            self.log(f"Bead {self.bead_id} updated to status: {status}")
            return True

        except (OSError, json.JSONDecodeError) as e:
            self.log(f"Error updating bead: {type(e).__name__}: {e}")
            return False
        except Exception as e:
            self.log(f"Unexpected error updating bead: {e}")
            return False

    def update_status_file(self, status: dict):
        """Update file-based status (fallback coordination)."""
        try:
            status["updated_at"] = datetime.now(UTC).isoformat()
            with open(self.status_file, "w", encoding="utf-8") as f:
                json.dump(status, f, indent=2)
        except OSError as e:
            self.log(f"Error updating status file: {e}")
        except Exception as e:
            self.log(f"Unexpected error updating status file: {e}")

    def check_progress(
        self, _agent_name: str, current_status: dict, last_status: dict | None
    ) -> bool:
        """Check if agent has made progress since last check."""
        if last_status is None:
            return True  # First check, assume progress

        # Compare output to detect progress
        current_output = current_status.get("last_output", "")
        last_output = last_status.get("last_output", "")

        # If output changed, there's progress
        if current_output != last_output:
            return True

        # If status changed to completed, there's progress
        return current_status.get("status") == "completed"

    def handle_stuck_agent(self, agent_name: str, stuck_count: int):
        """Handle an agent that appears stuck."""
        if stuck_count >= STUCK_THRESHOLD:
            self.log(
                f"⚠️ {agent_name} appears stuck ({stuck_count} iterations without progress)"
            )

            # Send timeout warning
            self.send_mcp_mail(
                to=agent_name,
                subject="TIMEOUT_WARNING",
                body={
                    "session_id": self.session_id,
                    "phase": "monitoring",
                    "message": f"No progress detected for {stuck_count} iterations",
                    "iterations_remaining": self.max_iterations
                    - max(self.coder_iterations, self.verifier_iterations),
                },
            )

            # Update bead to blocked
            self.update_bead_status("blocked")

    def run_iteration(self) -> str:  # noqa: PLR0911, PLR0912, PLR0915
        """Run a single monitoring iteration. Returns session status."""
        self.log(
            f"--- Iteration {max(self.coder_iterations, self.verifier_iterations) + 1} ---"
        )

        # Check Coder agent
        coder_status = self.get_tmux_session_status(self.coder_agent)
        self.log(f"Coder ({self.coder_agent}): {coder_status.get('status', 'unknown')}")

        if coder_status.get("status") == "tmux_missing":
            self.log("❌ tmux not available; cannot monitor agent sessions")
            self.update_bead_status("failed")
            return "error"

        if coder_status.get("exists"):
            self.coder_iterations += 1
            if not self.check_progress(
                self.coder_agent, coder_status, self.coder_last_progress
            ):
                self.coder_stuck_count += 1
                self.handle_stuck_agent(self.coder_agent, self.coder_stuck_count)
            else:
                self.coder_stuck_count = 0
            self.coder_last_progress = coder_status

        # Check Verifier agent
        verifier_status = self.get_tmux_session_status(self.verifier_agent)
        self.log(
            f"Verifier ({self.verifier_agent}): {verifier_status.get('status', 'unknown')}"
        )

        if verifier_status.get("status") == "tmux_missing":
            self.log("❌ tmux not available; cannot monitor agent sessions")
            self.update_bead_status("failed")
            return "error"

        if verifier_status.get("exists"):
            self.verifier_iterations += 1
            if not self.check_progress(
                self.verifier_agent, verifier_status, self.verifier_last_progress
            ):
                self.verifier_stuck_count += 1
                self.handle_stuck_agent(self.verifier_agent, self.verifier_stuck_count)
            else:
                self.verifier_stuck_count = 0
            self.verifier_last_progress = verifier_status

        # Determine overall session status
        coder_completed = coder_status.get("status") == "completed"
        verifier_completed = verifier_status.get("status") == "completed"
        coder_error = coder_status.get("status") == "error"
        verifier_error = verifier_status.get("status") == "error"
        coder_missing = not coder_status.get("exists")
        verifier_missing = not verifier_status.get("exists")

        # Update status file
        self.update_status_file(
            {
                "session_id": self.session_id,
                "coder_status": coder_status.get("status", "unknown"),
                "verifier_status": verifier_status.get("status", "unknown"),
                "coder_iterations": self.coder_iterations,
                "verifier_iterations": self.verifier_iterations,
                "max_iterations": self.max_iterations,
            }
        )

        # Check completion conditions
        if coder_completed and verifier_completed:
            self.log("✅ Both agents completed successfully!")
            self.update_bead_status("completed")
            self.send_mcp_mail(
                to=self.coder_agent,
                subject="SESSION_COMPLETE",
                body={"session_id": self.session_id, "status": "success"},
            )
            self.send_mcp_mail(
                to=self.verifier_agent,
                subject="SESSION_COMPLETE",
                body={"session_id": self.session_id, "status": "success"},
            )
            return "completed"

        # Check error conditions
        if coder_error or verifier_error:
            self.log("❌ Agent error detected")
            self.update_bead_status("failed")
            return "error"

        # Check if both agents are missing (session ended)
        if coder_missing and verifier_missing:
            self.log("⚠️ Both agents are missing - session may have ended")
            # Update bead status to avoid stale state if it ended prematurely or successfully without detection
            # If we reached here, it wasn't marked completed above, so likely aborted or crashed cleanly
            self.update_bead_status("ended")
            return "ended"

        # Check for single agent failure (missing but not completed)
        # If an agent is missing but the other is still running, and we haven't marked it as completed,
        # it might have crashed.
        if coder_missing and not coder_completed:
             self.log(f"❌ Coder agent {self.coder_agent} is missing but not completed (CRASHED?)")
             self.update_bead_status("failed")
             return "error"
             
        if verifier_missing and not verifier_completed:
             self.log(f"❌ Verifier agent {self.verifier_agent} is missing but not completed (CRASHED?)")
             self.update_bead_status("failed")
             return "error"

        # Check max iterations
        if (
            self.coder_iterations >= self.max_iterations
            or self.verifier_iterations >= self.max_iterations
        ):
            self.log(f"⏱️ Max iterations ({self.max_iterations}) reached")
            self.update_bead_status("timeout")
            self.send_mcp_mail(
                to=self.coder_agent,
                subject="SESSION_TIMEOUT",
                body={
                    "session_id": self.session_id,
                    "reason": "max_iterations_exceeded",
                },
            )
            self.send_mcp_mail(
                to=self.verifier_agent,
                subject="SESSION_TIMEOUT",
                body={
                    "session_id": self.session_id,
                    "reason": "max_iterations_exceeded",
                },
            )
            return "timeout"

        # Session still in progress
        if coder_completed:
            self.update_bead_status("verification")
        else:
            self.update_bead_status("implementation")

        return "in_progress"

    def run(self):
        """Run the monitoring loop."""
        self.log(f"Starting pair monitor for session {self.session_id}")
        self.update_bead_status("in_progress")

        while True:
            status = self.run_iteration()

            if status in ("completed", "error", "ended", "timeout"):
                self.log(f"Monitor exiting with status: {status}")
                break

            # Wait for next interval
            self.log(f"Sleeping for {self.interval}s...")
            time.sleep(self.interval)

        self.log("Pair monitor finished")
        return status


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Monitor dual-agent pair programming sessions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
    python3 scripts/pair_monitor.py \\
        --session-id pair-1234567890 \\
        --coder-agent <coder-agent-name> \\
        --verifier-agent <verifier-agent-name> \\
        --bead-id pair-1234567890 \\
        --max-iterations 10 \\
        --interval 60
        """,
    )

    parser.add_argument("--session-id", required=True, help="Unique session identifier")
    parser.add_argument(
        "--coder-agent", required=True, help="Coder agent tmux session name"
    )
    parser.add_argument(
        "--verifier-agent", required=True, help="Verifier agent tmux session name"
    )
    parser.add_argument("--bead-id", required=True, help="Bead ID for state tracking")
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=DEFAULT_MAX_ITERATIONS,
        help=f"Maximum iterations per agent (default: {DEFAULT_MAX_ITERATIONS})",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=DEFAULT_INTERVAL,
        help=f"Check interval in seconds (default: {DEFAULT_INTERVAL})",
    )

    args = parser.parse_args()

    if args.max_iterations < 1:
        print("Error: --max-iterations must be >= 1", file=sys.stderr)
        sys.exit(1)

    if args.interval < 1:
        print("Error: --interval must be >= 1", file=sys.stderr)
        sys.exit(1)

    monitor = PairMonitor(
        session_id=args.session_id,
        coder_agent=args.coder_agent,
        verifier_agent=args.verifier_agent,
        bead_id=args.bead_id,
        max_iterations=args.max_iterations,
        interval=args.interval,
    )

    status = monitor.run()

    # Exit with appropriate code
    if status == "completed":
        sys.exit(0)
    elif status == "timeout":
        sys.exit(2)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
