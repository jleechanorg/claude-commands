#!/usr/bin/env python3
"""
Pair Execute - Orchestrated Dual-Agent Pair Programming

Launches two agents for pair programming: one for coding, one for verification.
Defaults to Claude (coder) and Codex (verifier), but supports any agent combination.

Usage:
    python3 .claude/scripts/pair_execute.py "Task description"
    python3 .claude/scripts/pair_execute.py --coder-cli gemini --verifier-cli claude "Task"
    python3 .claude/scripts/pair_execute.py --coder-cli claude --verifier-cli claude "Task"  # Claude + Claude
    python3 .claude/scripts/pair_execute.py --brainstorm "Task description"
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import random
import re
import shlex
import subprocess  # nosec
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

# Constants
BEADS_FILE = ".beads/beads.left.jsonl"

# Use resolved absolute paths to work correctly from any directory
# Script is at .claude/scripts/pair_execute.py, so parent.parent.parent gets to project root
ORCHESTRATE_SCRIPT = str(
    Path(__file__).resolve().parent.parent.parent / "orchestration" / "orchestrate_unified.py"
)
MONITOR_SCRIPT = str(Path(__file__).resolve().parent / "pair_monitor.py")

# Supported CLI options
SUPPORTED_CLIS = ["claude", "codex", "gemini", "cursor", "minimax"]
CLAUDE_FAMILY_CLIS = {"claude", "minimax"}

# Default settings
DEFAULT_CODER_CLI = "claude"
DEFAULT_VERIFIER_CLI = "codex"
DEFAULT_MAX_ITERATIONS = 60  # 1h default monitor budget at 60s interval
DEFAULT_MONITOR_INTERVAL = 60
DEFAULT_CLAUDE_PROVIDER = os.environ.get("PAIR_CLAUDE_PROVIDER", "").strip().lower() or None
MAX_AGENT_NAME_LENGTH = 128
AGENT_SESSION_HASH_LENGTH = 16

# Restart commands keyed by launched agent name for monitor-driven restarts.
_AGENT_RESTART_COMMANDS: dict[str, str] = {}


def _lazy_import_claude_pair_execute():
    """Compatibility shim for legacy tests expecting this helper."""
    return sys.modules[__name__]


def _get_pair_func(name: str):
    """Compatibility shim used by older tests."""
    return getattr(_lazy_import_claude_pair_execute(), name)


def log_mcp_mail_warning(session_dir: Path):
    """Log info about coordination methods."""
    log("ℹ️  Pair session uses file-based coordination via session directory.")
    log("   Agents will use MCP Mail if available, otherwise rely on file-based fallback.")
    log(f"   Coordination folder: {session_dir}/coordination/")


def _resolve_claude_backend(
    selected_cli: str,
    provider: str | None,
    role_name: str,
    strict: bool = False,
) -> str:
    """Resolve claude-family CLI backend for a role.

    Args:
        selected_cli: Requested CLI for role.
        provider: Optional backend override ("claude" or "minimax").
        role_name: Human-readable role label for error messages.
        strict: If True, provider on non-claude-family CLI is an error.
    """
    if not provider:
        return selected_cli

    if provider not in CLAUDE_FAMILY_CLIS:
        raise ValueError(f"Unsupported {role_name} provider '{provider}'")

    if selected_cli in CLAUDE_FAMILY_CLIS:
        return provider

    if strict:
        raise ValueError(
            f"{role_name} provider '{provider}' requires {role_name} CLI to be "
            f"'claude' or 'minimax' (got '{selected_cli}')"
        )

    return selected_cli


def _resolve_role_models(args: argparse.Namespace) -> tuple[str | None, str | None]:
    """Resolve coder/verifier model selection from CLI args.

    Backward compatibility:
    - `--model` remains a legacy alias for coder-only model selection.
    """
    coder_model = args.coder_model if args.coder_model is not None else args.model
    verifier_model = args.verifier_model
    return coder_model, verifier_model


def get_sanitized_branch() -> str:
    """Get alphanumeric-only branch name."""
    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        branch = "unknown"
    return re.sub(r'[^a-zA-Z0-9]', '', branch)


def get_session_root_dir() -> Path:
    """Get root directory for session artifacts: /tmp/<branch>/<run_ts>/"""
    sanitized_branch = get_sanitized_branch()
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return Path("/tmp") / sanitized_branch / timestamp


def generate_agent_names(cli_name: str, session_id: str, role: str) -> str:
    """Generate alphanumeric-only agent name for MCP Mail registration.

    MCP Mail sanitizes ALL non-alphanumeric characters (including underscores and dashes).
    We pre-sanitize to alphanumeric-only to ensure names are reusable and predictable.

    Format: {sanitized_branch}{session_id_hash}{role}
    Example: choreretry5389abc123coder

    Design: unique per-session identities to prevent tmux session collisions
    when running multiple pair sessions in parallel.

    Args:
        cli_name: CLI being used (unused, kept for compatibility)
        session_id: Session identifier - included to ensure uniqueness
        role: Agent role (coder or verifier)

    Returns:
        Alphanumeric-only agent name (no sanitization needed by MCP Mail)
    """
    sanitized_branch = get_sanitized_branch()
    # Hash the full session ID so runs with the same prefix remain distinct.
    session_hash = hashlib.sha256(session_id.encode("utf-8")).hexdigest()[:AGENT_SESSION_HASH_LENGTH]
    safe_role = re.sub(r"[^a-zA-Z0-9]", "", role) or "agent"
    suffix = f"{session_hash}{safe_role}"

    # Keep deterministic uniqueness while staying within backend limits.
    max_branch_length = MAX_AGENT_NAME_LENGTH - len(suffix)
    if max_branch_length < 1:
        trimmed_role = safe_role[: max(1, MAX_AGENT_NAME_LENGTH - len(session_hash))]
        suffix = f"{session_hash}{trimmed_role}"
        max_branch_length = max(1, MAX_AGENT_NAME_LENGTH - len(suffix))

    branch_part = sanitized_branch[:max_branch_length] or "branch"
    return f"{branch_part}{suffix}"[:MAX_AGENT_NAME_LENGTH]


def log(message: str):
    """Log message with timestamp."""
    timestamp = datetime.now(UTC).isoformat()
    print(f"[{timestamp}] {message}", flush=True)


def check_mcp_mail_for_message(
    inbox: list[dict], from_agent: str, subject: str
) -> dict | None:
    """Check MCP Mail inbox for specific message from agent.

    Args:
        inbox: List of MCP Mail messages
        from_agent: Agent name to filter by
        subject: Subject line to match

    Returns:
        Message dict if found, None otherwise
    """
    for message in inbox:
        if message.get("from") == from_agent and message.get("subject") == subject:
            return message
    return None


def restart_coder_with_feedback(
    session_id: str,
    bead_id: str,
    original_instructions: str,
    feedback: dict,
    cli: str,
    verifier_agent_name: str,
    session_dir: Path,
    no_worktree: bool,
    model: str | None,
) -> tuple[bool, str]:
    """Restart coder agent with verifier feedback.

    Args:
        session_id: Session ID
        bead_id: Bead ID
        original_instructions: Original coder instructions
        feedback: Feedback dict from verifier's VERIFICATION_FAILED message
        cli: CLI to use (claude, codex, etc)
        verifier_agent_name: Name of verifier agent
        session_dir: Session directory
        no_worktree: Whether to skip worktree isolation
        model: Model to use

    Returns:
        Tuple of (success, agent_name)
    """
    # Clean up existing coder session to prevent concurrent agents
    old_coder_name = generate_agent_names(cli, session_id, "coder")
    log(f"Terminating old coder session: {old_coder_name}")
    try:
        # Discover tmux sockets for cleanup
        coder_log = session_dir / f"{old_coder_name}.log"
        tmux_sockets = _discover_tmux_sockets(coder_log) if coder_log.exists() else []

        # Try to find and kill the session on known sockets
        session_killed = False
        for socket in tmux_sockets:
            # First check if session exists on this socket
            check_result = subprocess.run(
                ["tmux", "-L", socket, "has-session", "-t", old_coder_name],
                check=False,
                capture_output=True,
                timeout=10,
            )
            if check_result.returncode == 0:
                # Session exists, kill it
                kill_result = subprocess.run(
                    ["tmux", "-L", socket, "kill-session", "-t", old_coder_name],
                    check=False,
                    capture_output=True,
                    timeout=10,
                )
                if kill_result.returncode == 0:
                    log(f"✅ Killed old coder session on socket {socket}")
                    session_killed = True
                    break

        # Only try default socket if not found on known sockets
        if not session_killed:
            subprocess.run(
                ["tmux", "kill-session", "-t", old_coder_name],
                check=False,
                capture_output=True,
                timeout=10,
            )
    except (subprocess.TimeoutExpired, OSError) as exc:
        log(f"⚠️  Warning: Failed to cleanup old coder session: {exc}")
    
    # Build enhanced instructions with feedback
    feedback_text = json.dumps(feedback, indent=2)
    enhanced_instructions = f"""{original_instructions}

---
VERIFICATION FEEDBACK (ITERATION):
The verifier reviewed your previous implementation and found issues.
You MUST address ALL feedback below before re-sending IMPLEMENTATION_READY.

Feedback from verifier:
{feedback_text}

ACTION REQUIRED:
1. Review the failures and suggestions above
2. Fix ALL identified issues
3. Run tests to verify fixes
4. Send IMPLEMENTATION_READY when all issues are resolved
"""

    log("Restarting coder with verifier feedback...")
    return launch_coder_agent(
        session_id=session_id,
        bead_id=bead_id,
        instructions=enhanced_instructions,
        cli=cli,
        verifier_agent_name=verifier_agent_name,
        session_dir=session_dir,
        no_worktree=no_worktree,
        model=model,
    )


def run_pair_iteration_loop(
    session_id: str,
    bead_id: str,
    coder_agent: str,
    verifier_agent: str,
    coder_instructions: str,
    coder_cli: str,
    verifier_cli: str,
    session_dir: Path,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    poll_interval: int = 30,
    no_worktree: bool = False,
    model: str | None = None,
    timeout_seconds: int | None = 3600,  # Default 1 hour timeout to prevent infinite loop
) -> dict:
    """Run external iteration loop for pair programming.

    This function implements the external restart loop that enables
    iterative pair programming:
    1. Wait for verifier to send VERIFICATION_FAILED or VERIFICATION_COMPLETE
    2. If FAILED: restart coder with feedback, goto step 1
    3. If COMPLETE: mark bead done and exit
    4. If max_iterations reached: mark bead blocked and exit

    Args:
        session_id: Session ID
        bead_id: Bead ID
        coder_agent: Name of coder agent
        verifier_agent: Name of verifier agent
        coder_instructions: Original coder instructions
        coder_cli: CLI for coder (claude, codex, etc)
        verifier_cli: CLI for verifier
        session_dir: Session directory
        max_iterations: Maximum iterations before giving up (default: 5)
        poll_interval: Seconds between MCP Mail checks (default: 30)
        no_worktree: Whether to skip worktree isolation
        model: Model to use
        timeout_seconds: Hard timeout in seconds for the iteration loop (default: 3600 = 1 hour)

    Returns:
        Dict with status, iterations, and optional details
    """
    log("=" * 60)
    log("PAIR ITERATION LOOP STARTED")
    log(f"Max iterations: {max_iterations}")
    log(f"Poll interval: {poll_interval}s")
    log(f"Timeout: {timeout_seconds}s")
    log("=" * 60)

    # Initial coder agent (launched outside this loop) counts as iteration 1
    iteration = 1

    # Get project root for MCP Mail project_key
    project_root = str(Path.cwd().resolve())

    timeout_deadline = (
        time.monotonic() + timeout_seconds if timeout_seconds and timeout_seconds > 0 else None
    )

    # Poll indefinitely until message received or timeout
    # iteration tracks number of coder runs, not polling cycles
    while True:
        if timeout_deadline is not None and time.monotonic() >= timeout_deadline:
            log(
                f"⏱️ Pair iteration timeout reached ({timeout_seconds}s) "
                f"before iteration {iteration}"
            )
            update_bead_status(bead_id, "timeout")
            return {
                "status": "timeout",
                "iterations": iteration,
                "message": f"Pair session timeout reached ({timeout_seconds}s)",
            }

        log(f"\n--- Polling for messages (coder attempt {iteration}/{max_iterations}) ---")

        # Get session start timestamp for filtering stale messages
        session_start_ts = _get_session_start_timestamp(session_dir)

        # Poll MCP Mail inbox for coder agent to see messages FROM verifier
        log(f"Polling MCP Mail inbox of {coder_agent} for messages from {verifier_agent}...")

        # Fetch coder agent's inbox to see messages sent TO coder FROM verifier
        inbox = _fetch_mcp_mail_inbox(
            session_id=session_id,
            session_dir=session_dir,
            agent_name=coder_agent,
            source_agent_name=verifier_agent,
            project_key=project_root,
        )

        # ALSO poll file-based outbox as primary/fallback coordination method
        log("Polling file-based verifier outbox...")
        file_messages = poll_verifier_outbox(session_dir, session_start_ts)

        # Merge file messages into inbox (file-based takes precedence if MCP unavailable)
        if file_messages:
            log(f"📬 Found {len(file_messages)} message(s) from file-based outbox")
            inbox = inbox + file_messages
        else:
            log("No new messages in file-based outbox")

        # Short-circuit terminal monitor states to avoid polling timeouts.
        terminal_outcome = _read_monitor_terminal_outcome(session_dir, session_id)
        if terminal_outcome is not None:
            update_bead_status(bead_id, terminal_outcome["bead_status"])
            return {
                "status": terminal_outcome["status"],
                "iterations": iteration,
                "message": terminal_outcome["message"],
                "verification_source": terminal_outcome.get("verification_source"),
            }

        # Check for completion
        complete_msg = check_mcp_mail_for_message(
            inbox, verifier_agent, "VERIFICATION_COMPLETE"
        )
        if complete_msg:
            # FIX REV-mesfg: Trust VERIFICATION_COMPLETE but verify against verification_report.json
            # verification_report.json is the authoritative source of truth for pass/fail
            verification_report = session_dir / "verification_report.json"
            if verification_report.exists():
                try:
                    with open(verification_report, encoding="utf-8") as f:
                        report_data = json.load(f)
                    report_status = str(report_data.get("status") or "").upper()

                    if report_status == "PASS":
                        log("✅ VERIFICATION_COMPLETE received - pair session successful!")
                        log(f"   Verified: verification_report.json confirms status=PASS")
                        update_bead_status(bead_id, "done")
                        return {
                            "status": "success",
                            "iterations": iteration,
                            "message": "Verification complete",
                            "verification_source": "verification_report.json",
                        }
                    elif report_status == "FAIL":
                        log(f"⚠️  VERIFICATION_COMPLETE received but verification_report.json shows status=FAIL")
                        log(f"   Treating as verification failure - continuing iteration loop")
                        # Fall through to check for VERIFICATION_FAILED message
                    else:
                        log(f"⚠️  VERIFICATION_COMPLETE received but verification_report.json has unknown status: {report_status}")
                        log(f"   Cannot confirm success - continuing iteration loop")
                        # Fall through
                except (OSError, json.JSONDecodeError) as exc:
                    log(f"⚠️  VERIFICATION_COMPLETE received but cannot read verification_report.json: {exc}")
                    log("⚠️  Falling back to VERIFICATION_COMPLETE message as success signal")
                    update_bead_status(bead_id, "done")
                    return {
                        "status": "success",
                        "iterations": iteration,
                        "message": "Verification complete (fallback to verifier message)",
                        "verification_source": "verifier_message",
                    }
            else:
                log("⚠️  VERIFICATION_COMPLETE received but verification_report.json does not exist")
                log("⚠️  Falling back to VERIFICATION_COMPLETE message as success signal")
                update_bead_status(bead_id, "done")
                return {
                    "status": "success",
                    "iterations": iteration,
                    "message": "Verification complete (fallback to verifier message)",
                    "verification_source": "verifier_message",
                }

        # Check for failure requiring iteration
        failed_msg = check_mcp_mail_for_message(
            inbox, verifier_agent, "VERIFICATION_FAILED"
        )
        if failed_msg:
            # FIX REV-pbu2j: Single-coder architecture - no respawning
            
            feedback = failed_msg.get("body", {})
            status_snapshot = feedback.get("status_snapshot", {}) if isinstance(feedback, dict) else {}
            verifier_status = str(status_snapshot.get("verifier_status") or "").lower()
            log(f"❌ VERIFICATION_FAILED received - iteration {iteration}/{max_iterations}")
            log(f"Failure details: {json.dumps(feedback, indent=2)}")

            # Terminal verifier startup/runtime failures should fail fast.
            if verifier_status in {"not_found", "error", "tmux_missing"}:
                log(
                    "❌ Verifier is unavailable (terminal state) - failing pair session immediately"
                )
                update_bead_status(bead_id, "failed")
                return {
                    "status": "failed",
                    "iterations": iteration,
                    "message": f"Verifier unavailable ({verifier_status})",
                    "feedback": feedback,
                }

            # Check if max iterations reached
            if iteration >= max_iterations:
                log(f"❌ Max iterations ({max_iterations}) reached - marking as failed")
                update_bead_status(bead_id, "failed")
                return {
                    "status": "failed",
                    "iterations": max_iterations,
                    "message": f"Exceeded max iterations ({max_iterations})",
                    "feedback": feedback,
                }

            # Increment iteration counter (verifier polling count)
            iteration += 1

            # Continue polling - coder runs once, verifier decides
            log(f"⏳ Continuing to poll verifier for iteration {iteration}/{max_iterations}...")
            # Fall through to next poll cycle - don't return

        # PRIORITY 4: Check orchestration result files as final fallback
        # (more reliable than verification_report.json since agents always create these)
        session_start_ts = _get_session_start_timestamp(session_dir)
        verifier_result = _check_orchestration_result_file(
            verifier_agent,
            session_start_timestamp=session_start_ts,
            session_id=session_id,
        )
        coder_result = _check_orchestration_result_file(
            coder_agent,
            session_start_timestamp=session_start_ts,
            session_id=session_id,
        )

        # If both agents completed successfully, treat as VERIFICATION_COMPLETE only
        # when verifier explicitly reports a PASS outcome.
        if verifier_result and coder_result:
            verifier_status = str(verifier_result.get("status") or "").lower()
            coder_status = str(coder_result.get("status") or "").lower()
            coder_mcp_mail_status = str(coder_result.get("mcp_mail_status") or "").lower()

            if verifier_status == "error":
                log("❌ Verifier agent failed (detected via orchestration result file)")
                update_bead_status(bead_id, "failed")
                return {
                    "status": "failed",
                    "iterations": iteration,
                    "message": "Verifier agent encountered an error",
                    "exit_code": verifier_result.get("exit_code"),
                }

            if coder_mcp_mail_status == "unavailable":
                log("❌ Coder completed without MCP Mail availability")
                update_bead_status(bead_id, "failed")
                return {
                    "status": "failed",
                    "iterations": iteration,
                    "message": "Coder completed with MCP Mail unavailable",
                    "coder_result": coder_result,
                }

            if verifier_status == "completed" and coder_status == "completed":
                # FIX REV-mesfg: Treat status:completed as only "verifier finished," not success
                # verification_report.json is the authoritative source of truth
                verification_report = session_dir / "verification_report.json"

                # Try to read verification_report.json as source of truth
                report_status = None
                feedback_details = {}
                if verification_report.exists():
                    try:
                        with open(verification_report, encoding="utf-8") as f:
                            report_data = json.load(f)
                        report_status = str(report_data.get("status") or "").upper()
                        feedback_details = report_data
                    except (OSError, json.JSONDecodeError) as exc:
                        log(f"⚠️  Cannot read verification_report.json: {exc}")

                if report_status == "PASS":
                    log("✅ Both agents completed (detected via orchestration result files)")
                    log("✅ Verified: verification_report.json confirms status=PASS")
                    update_bead_status(bead_id, "done")
                    return {
                        "status": "success",
                        "iterations": iteration,
                        "message": "Verification complete",
                        "verification_source": "verification_report.json",
                    }
                elif report_status == "FAIL":
                    log("❌ Verification FAILED (detected via verification_report.json)")
                    log(f"   Details: {feedback_details.get('details', 'No details available')}")
                    update_bead_status(bead_id, "blocked")
                    return {
                        "status": "failed",
                        "iterations": iteration,
                        "message": "Verification failed",
                        "feedback": feedback_details,
                        "verification_source": "verification_report.json",
                    }
                else:
                    # No parseable PASS/FAIL in verification_report.json
                    log(f"⚠️  Both agents completed but no parseable verification result")
                    log(f"   verification_report.json status: {report_status or 'missing/unknown'}")
                    log(f"   Returning degraded/unknown status - this is NOT success")
                    update_bead_status(bead_id, "degraded")
                    return {
                        "status": "unknown",
                        "verification_status": "degraded",
                        "iterations": iteration,
                        "message": "Agents completed but verification outcome unclear",
                        "verification_source": "none" if not verification_report.exists() else "unparseable",
                    }

        # No message yet - keep polling
        log(f"No verifier response yet, waiting {poll_interval}s...")
        sleep_seconds = poll_interval
        if timeout_deadline is not None:
            remaining = timeout_deadline - time.monotonic()
            if remaining <= 0:
                log(f"⏱️ Pair iteration timeout reached while waiting ({timeout_seconds}s)")
                update_bead_status(bead_id, "timeout")
                return {
                    "status": "timeout",
                    "iterations": iteration,
                    "message": f"Pair session timeout reached ({timeout_seconds}s)",
                }
            sleep_seconds = min(poll_interval, remaining)

        time.sleep(sleep_seconds)
    # Loop continues - max_iterations is checked in VERIFICATION_FAILED handler
    # Timeout is the absolute limit for polling duration


def _get_session_start_timestamp(session_dir: Path) -> float:
    """Get session start timestamp for filtering stale orchestration results."""
    session_start_file = session_dir / ".session_start"
    try:
        raw = session_start_file.read_text(encoding="utf-8").strip()
    except OSError:
        return 0.0

    if not raw:
        return 0.0

    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).timestamp()
    except (ValueError, TypeError):
        return 0.0


def _read_monitor_terminal_outcome(session_dir: Path, session_id: str) -> dict | None:
    """Read terminal monitor status and convert to loop outcome.

    Returns:
        Outcome dict or None when monitor status is non-terminal/absent.
    """
    status_file = session_dir / "status.json"
    if not status_file.exists():
        return None

    try:
        status_data = json.loads(status_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    file_session_id = status_data.get("session_id")
    if file_session_id and file_session_id != session_id:
        return None

    session_status = str(status_data.get("session_status") or "").lower()
    if session_status != "completed":
        return None

    coder_status = str(status_data.get("coder_status") or "").lower()
    verifier_status = str(status_data.get("verifier_status") or "").lower()
    if coder_status != "completed" or verifier_status != "completed":
        return None

    verification_report = session_dir / "verification_report.json"
    if verification_report.exists():
        try:
            report_data = json.loads(verification_report.read_text(encoding="utf-8"))
            report_status = str(report_data.get("status") or "").upper()
            if report_status == "PASS":
                return {
                    "status": "success",
                    "bead_status": "done",
                    "message": "Verification complete",
                    "verification_source": "verification_report.json",
                }
            if report_status == "FAIL":
                return {
                    "status": "failed",
                    "bead_status": "blocked",
                    "message": "Verification failed",
                    "verification_source": "verification_report.json",
                }
        except (OSError, json.JSONDecodeError):
            pass

    # Terminal monitor completion without parseable report: return degraded terminal state
    # instead of polling until timeout.
    return {
        "status": "unknown",
        "bead_status": "degraded",
        "message": "Monitor reports completion but verification outcome is unavailable",
        "verification_source": "status.json",
    }


def _check_orchestration_result_file(
    agent_name: str,
    session_start_timestamp: float = 0.0,
    session_id: str | None = None,
) -> dict | None:
    """Check if agent has written orchestration result file indicating completion.

    Returns result data if found, None otherwise.
    Expected location: /tmp/orchestration_results/{agent_name}*_results*.json
    """
    results_dir = Path("/tmp/orchestration_results")
    if not results_dir.exists():
        return None

    # Find result files matching this agent
    result_files = list(results_dir.glob(f"{agent_name}*_results*.json"))
    if not result_files:
        return None

    # Iterate newest-first and return the first file scoped to this session.
    candidates: list[tuple[float, Path]] = []
    for p in result_files:
        try:
            mtime = p.stat().st_mtime
            if session_start_timestamp > 0 and mtime < session_start_timestamp:
                log(
                    f"⚠️  Ignoring stale result file for {agent_name}: {p.name}"
                )
                continue
            candidates.append((mtime, p))
        except OSError:
            continue

    for _mtime, result_file in sorted(candidates, key=lambda item: item[0], reverse=True):
        try:
            with open(result_file, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue

        file_session_id = data.get("session_id")
        if session_id and file_session_id and file_session_id != session_id:
            log(
                f"⚠️  Ignoring foreign-session result file for {agent_name}: "
                f"{result_file.name} (session_id={file_session_id})"
            )
            continue
        return data

    return None


def _fetch_mcp_mail_inbox(
    session_id: str,
    session_dir: Path,
    agent_name: str | None = None,
    project_key: str | None = None,
    source_agent_name: str | None = None,
) -> list[dict]:
    """Fetch messages intended for agent, falling back to file artifacts.

    PROTOCOL:
    1. (Future) Attempt to read real MCP Mail inbox if accessible.
    2. Fallback: Read file-based artifacts (status.json, verification_report.json).
       This allows the orchestrator to observe agent progress even if it cannot
       directly query the MCP Mail server.

    IDEMPOTENCY: Uses content-hash based deduplication instead of mtime to prevent
    re-processing of stale/transient status updates. Processed message IDs are
    persisted in processed_messages.json for crash recovery.

    Optional args are accepted for compatibility with call sites that pass agent
    context, but are not required for local file-based coordination.
    """
    default_source_agent = source_agent_name or agent_name or "verifier"

    # Load processed message IDs from persistent storage (content-hash based)
    processed_ids_file = session_dir / "processed_messages.json"
    processed_ids = set()
    if processed_ids_file.exists():
        try:
            with open(processed_ids_file, encoding="utf-8") as f:
                processed_ids = set(json.load(f))
        except (OSError, json.JSONDecodeError) as exc:
            log(f"⚠️  Warning: Failed to load processed message IDs: {exc}")

    def _mark_processed(message_id: str):
        """Mark a message ID as processed and persist to disk."""
        processed_ids.add(message_id)
        try:
            with open(processed_ids_file, "w", encoding="utf-8") as f:
                json.dump(list(processed_ids), f, indent=2)
        except OSError as exc:
            log(f"⚠️  Warning: Failed to persist processed message ID: {exc}")

    def _get_message_id(subject: str, body_data: dict) -> str:
        """Generate content-based message ID (SHA256 hash)."""
        content = json.dumps({"subject": subject, "body": body_data}, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]  # First 16 chars
    
    # PRIORITY 1: Check monitor's status.json (written by pair_monitor.py)
    monitor_status_file = session_dir / "status.json"
    if monitor_status_file.exists():
        try:
            with open(monitor_status_file, encoding="utf-8") as f:
                status_data = json.load(f)
            # Session scope guard: ignore monitor artifacts from other sessions.
            status_session_id = status_data.get("session_id")
            if status_session_id and status_session_id != session_id:
                log(
                    f"ℹ️  Ignoring status.json for session {status_session_id}; "
                    f"current session is {session_id}"
                )
            else:
                # Convert status file format to message format.
                # Monitor-authored status is authoritative for session-local completion
                # as long as verification_report.json confirms PASS/FAIL.
                messages = []
                v_status = str(status_data.get("verifier_status") or "").lower()
                session_status = str(status_data.get("session_status") or "").lower()
                if v_status in {"complete", "completed"}:
                    # Check verification_report.json for actual pass/fail result
                    verification_report = session_dir / "verification_report.json"
                    if verification_report.exists():
                        try:
                            with open(verification_report, encoding="utf-8") as f:
                                report_data = json.load(f)
                            report_status = str(report_data.get("status") or "").upper()

                            if report_status == "PASS":
                                subject = "VERIFICATION_COMPLETE"
                                message_id = _get_message_id(subject, report_data)
                                if message_id not in processed_ids:
                                    messages.append({
                                        "from": status_data.get("verifier_agent", "verifier"),
                                        "subject": subject,
                                        "body": report_data,
                                    })
                                    _mark_processed(message_id)
                                else:
                                    log(f"⚠️  Skipping duplicate VERIFICATION_COMPLETE (ID: {message_id})")
                            elif report_status == "FAIL":
                                subject = "VERIFICATION_FAILED"
                                message_id = _get_message_id(subject, report_data)
                                if message_id not in processed_ids:
                                    messages.append({
                                        "from": status_data.get("verifier_agent", "verifier"),
                                        "subject": subject,
                                        "body": report_data,
                                    })
                                    _mark_processed(message_id)
                                else:
                                    log(f"⚠️  Skipping duplicate VERIFICATION_FAILED (ID: {message_id})")
                        except (OSError, json.JSONDecodeError) as exc:
                            log(f"⚠️  Error reading verification report: {exc}")
                    # If no verification_report.json exists, do not emit VERIFICATION_COMPLETE
                    # Verifier completion without a report is not a valid success signal
                elif v_status in {"failed", "error"}:
                    messages.append({
                        "from": status_data.get("verifier_agent", "verifier"),
                        "subject": "VERIFICATION_FAILED",
                        "body": status_data.get("verification_feedback", {"status_snapshot": status_data}),
                    })
                elif session_status in {"ended", "timeout"}:
                    # Terminal monitor state without explicit verifier completion.
                    # Treat as verification failure to fail-fast the orchestration loop.
                    feedback = status_data.get("verification_feedback", {})
                    if not isinstance(feedback, dict):
                        feedback = {}
                    feedback.setdefault("status_snapshot", status_data)
                    feedback.setdefault(
                        "details",
                        f"Monitor reported terminal session_status={session_status}",
                    )
                    messages.append({
                        "from": status_data.get("verifier_agent", "verifier"),
                        "subject": "VERIFICATION_FAILED",
                        "body": feedback,
                    })
                # Only return if we found terminal status (non-empty messages)
                # If status is non-terminal (running, etc), fall through to other checks
                if messages:
                    return messages
        except (OSError, json.JSONDecodeError) as exc:
            log(f"⚠️  Error reading/parsing monitor status file {monitor_status_file}: {exc}")

    # PRIORITY 2: Check for agent_status.json (legacy coordination file)
    status_file = session_dir / "agent_status.json"
    if status_file.exists():
        try:
            with open(status_file, encoding="utf-8") as f:
                status_data = json.load(f)
            # Convert status file format to message format
            messages = []
            v_status = str(status_data.get("verifier_status") or "").lower()
            subject = None
            body: dict = {}
            if v_status in {"complete", "completed"}:
                subject = "VERIFICATION_COMPLETE"
                body = status_data.get("verification_result", {})
            elif v_status in {"failed", "error"}:
                subject = "VERIFICATION_FAILED"
                body = status_data.get("verification_feedback", {})

            if subject:
                message_id = _get_message_id(subject, body)
                if message_id not in processed_ids:
                    messages.append({
                        "from": status_data.get("verifier_agent", "verifier"),
                        "subject": subject,
                        "body": body,
                    })
                    _mark_processed(message_id)
                else:
                    log(f"⚠️  Skipping duplicate {subject} status (ID: {message_id})")

            # Only return if we found a terminal status (non-empty messages)
            # If status is non-terminal (running, etc), fall through to PRIORITY 3/4
            if messages:
                return messages
        except (OSError, json.JSONDecodeError) as exc:
            log(f"⚠️  Error reading/parsing status file {status_file}: {exc}")

    # PRIORITY 3: Check verification_report.json (fallback when monitor fails)
    verification_report = session_dir / "verification_report.json"
    if verification_report.exists():
        try:
            with open(verification_report, encoding="utf-8") as f:
                report_data = json.load(f)

            # Convert verification report to message format
            messages = []
            status = str(report_data.get("status") or "").upper()
            if status == "PASS":
                subject = "VERIFICATION_COMPLETE"
                message_id = _get_message_id(subject, report_data)
                if message_id not in processed_ids:
                    messages.append({
                        "from": default_source_agent,
                        "subject": subject,
                        "body": report_data,
                    })
                    _mark_processed(message_id)
                else:
                    log(f"⚠️  Skipping duplicate VERIFICATION_COMPLETE fallback (ID: {message_id})")
            elif status == "FAIL":
                subject = "VERIFICATION_FAILED"
                message_id = _get_message_id(subject, report_data)
                if message_id not in processed_ids:
                    messages.append({
                        "from": default_source_agent,
                        "subject": subject,
                        "body": report_data,
                    })
                    _mark_processed(message_id)
                else:
                    log(f"⚠️  Skipping duplicate VERIFICATION_FAILED fallback (ID: {message_id})")
            return messages
        except (OSError, json.JSONDecodeError) as exc:
            log(f"⚠️  Error reading/parsing verification report {verification_report}: {exc}")

    # Fallback: check for test inbox file
    inbox_file = session_dir / "mcp_mail_inbox.json"
    if inbox_file.exists():
        try:
            with open(inbox_file, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            log(f"⚠️  Error reading/parsing inbox file {inbox_file}: {exc}")
            return []
    return []


def generate_session_id() -> str:
    """Generate unique session ID with randomness to prevent collisions."""
    return f"pair-{int(time.time())}-{random.randint(10000, 99999)}"


def _terminate_tmux_session(agent_name: str, sockets: list[str] | None = None) -> bool:
    """Best-effort tmux session termination for a launched agent."""
    socket_list = sockets or []
    for socket in socket_list:
        try:
            check_result = subprocess.run(
                ["tmux", "-L", socket, "has-session", "-t", agent_name],
                check=False,
                capture_output=True,
                timeout=10,
            )
            if check_result.returncode == 0:
                kill_result = subprocess.run(
                    ["tmux", "-L", socket, "kill-session", "-t", agent_name],
                    check=False,
                    capture_output=True,
                    timeout=10,
                )
                if kill_result.returncode == 0:
                    log(f"✅ Terminated tmux session for {agent_name} on socket {socket}")
                    return True
        except (subprocess.TimeoutExpired, OSError) as exc:
            log(f"⚠️  Failed socket-based tmux cleanup for {agent_name} on {socket}: {exc}")

    try:
        kill_result = subprocess.run(
            ["tmux", "kill-session", "-t", agent_name],
            check=False,
            capture_output=True,
            timeout=10,
        )
        if kill_result.returncode == 0:
            log(f"✅ Terminated tmux session for {agent_name} on default socket")
            return True
    except (subprocess.TimeoutExpired, OSError) as exc:
        log(f"⚠️  Failed default-socket tmux cleanup for {agent_name}: {exc}")

    return False


def create_session_directory(session_id: str) -> Path:
    """Create session directory for artifacts."""
    # Structure: /tmp/<branch>/<run_ts>/pair_sessions/<session_id>
    session_root = get_session_root_dir() / "pair_sessions"
    session_dir = session_root / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    # Create coordination subfolders for file-based messaging
    coord_dir = session_dir / "coordination"
    coord_dir.mkdir(parents=True, exist_ok=True)

    coder_outbox = coord_dir / "coder_outbox"
    coder_outbox.mkdir(parents=True, exist_ok=True)

    verifier_outbox = coord_dir / "verifier_outbox"
    verifier_outbox.mkdir(parents=True, exist_ok=True)

    status_dir = coord_dir / "status"
    status_dir.mkdir(parents=True, exist_ok=True)

    log(f"Created coordination folders: {coord_dir}")

    # Record session start time for GitHub response validation
    session_start_file = session_dir / ".session_start"
    if not session_start_file.exists():
        session_start_time = datetime.now(UTC).isoformat()
        try:
            session_start_file.write_text(session_start_time, encoding="utf-8")
            log(f"Session start time: {session_start_time}")
        except OSError as exc:
            log(f"⚠️  Could not persist session start marker: {exc}")

    return session_dir


def _read_log_tail(log_file: Path, max_bytes: int = 4096, tail_chars: int = 500) -> str:
    """Read the tail of a log file for crash diagnostics.
    
    Args:
        log_file: Path to the log file
        max_bytes: Maximum bytes to read from end of file
        tail_chars: Number of characters to return from the decoded tail
        
    Returns:
        String containing the tail of the log file
    """
    try:
        with open(log_file, "rb") as lf:
            lf.seek(0, os.SEEK_END)
            file_size = lf.tell()
            if file_size > max_bytes:
                lf.seek(-max_bytes, os.SEEK_END)
            else:
                lf.seek(0, os.SEEK_SET)
            tail_bytes = lf.read(max_bytes)
        return tail_bytes.decode("utf-8", errors="replace")[-tail_chars:]
    except (OSError, TypeError, ValueError):
        return ""


def _check_tmux_session(agent_name: str, tmux_socket: str | None = None) -> bool:
    """Check if a tmux session exists for the given agent.

    Args:
        agent_name: Name of the agent to check
        tmux_socket: Optional tmux socket name to check (e.g., "orch-12345")

    Returns:
        True if tmux session exists and is running, False otherwise
    """
    try:
        # If socket provided, check that specific socket
        if tmux_socket:
            result = subprocess.run(
                ["tmux", "-L", tmux_socket, "has-session", "-t", agent_name],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0

        # Otherwise, search through all tmux sockets for the session
        # tmux stores sockets in /tmp/tmux-{uid}/
        tmux_base = "/tmp/tmux-501"  # Common location for user tmux sockets
        import glob

        # Find all socket directories - both orch-* and pair-* (and any numeric sockets)
        socket_dirs = glob.glob(f"{tmux_base}/orch-*")
        socket_dirs.extend(glob.glob(f"{tmux_base}/pair-*"))
        socket_dirs.extend(glob.glob(f"{tmux_base}/[0-9]*"))  # Numeric sockets like our pair session
        socket_dirs.append(f"{tmux_base}/default")

        for sock_dir in socket_dirs:
            sock_name = sock_dir.split("/")[-1]
            try:
                result = subprocess.run(
                    ["tmux", "-L", sock_name, "has-session", "-t", agent_name],
                    capture_output=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    return True
            except Exception:
                continue

        return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


# =============================================================================
# FILE-BASED COORDINATION PROTOCOL
# =============================================================================
# Primary coordination method when MCP Mail is unavailable.
# Directory structure:
#   session_dir/coordination/
#   ├── coder_outbox/      # Messages from coder -> verifier
#   │   └── IMPLEMENTATION_READY_<timestamp>.json
#   ├── verifier_outbox/   # Messages from verifier -> coder
#   │   ├── VERIFICATION_COMPLETE_<timestamp>.json
#   │   └── VERIFICATION_FAILED_<timestamp>.json
#   └── status/           # Agent status tracking
#       ├── coder.json
#       └── verifier.json


def _validate_session_path(target_path: Path, session_dir: Path) -> None:
    """Validate that a target path is within the active session directory.

    Raises ValueError if the path resolves outside the session_dir.
    """
    try:
        resolved_target = target_path.resolve()
        resolved_session = session_dir.resolve()
        if not str(resolved_target).startswith(str(resolved_session) + os.sep) and resolved_target != resolved_session:
            raise ValueError(
                f"Path integrity violation: {resolved_target} is outside "
                f"active session dir {resolved_session}"
            )
    except (OSError, RuntimeError) as exc:
        raise ValueError(f"Cannot validate path {target_path}: {exc}") from exc


def _write_message_atomically(outbox_dir: Path, filename: str, content: dict) -> Path:
    """Write message atomically using rename pattern.

    Args:
        outbox_dir: Directory to write to
        filename: Final filename (without .tmp)
        content: JSON-serializable message content

    Returns:
        Path to the written file
    """
    # Write to .tmp first, then rename for atomicity
    tmp_path = outbox_dir / f"{filename}.tmp"
    final_path = outbox_dir / filename

    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=2)
            f.flush()
            os.fsync(f.fileno())

        # Atomic rename
        os.replace(tmp_path, final_path)
        return final_path
    except OSError as exc:
        log(f"⚠️  Failed to write message {filename}: {exc}")
        # Clean up tmp file if it exists
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        raise


def write_coder_message(session_dir: Path, message_type: str, body: dict) -> Path:
    """Write message from coder to verifier outbox.

    Args:
        session_dir: Session directory
        message_type: Message type (IMPLEMENTATION_READY)
        body: Message body

    Returns:
        Path to written message file
    """
    outbox_dir = session_dir / "coordination" / "coder_outbox"
    _validate_session_path(outbox_dir, session_dir)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%f")
    filename = f"{message_type}_{timestamp}.json"

    message = {
        "from": "coder",
        "to": "verifier",
        "subject": message_type,
        "body": body,
        "session_id": session_dir.name,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    log(f"📤 Writing coder message: {message_type} -> {outbox_dir}/{filename}")
    return _write_message_atomically(outbox_dir, filename, message)


def write_verifier_message(session_dir: Path, message_type: str, body: dict) -> Path:
    """Write message from verifier to coder outbox.

    Args:
        session_dir: Session directory
        message_type: Message type (VERIFICATION_COMPLETE, VERIFICATION_FAILED)
        body: Message body

    Returns:
        Path to written message file
    """
    outbox_dir = session_dir / "coordination" / "verifier_outbox"
    _validate_session_path(outbox_dir, session_dir)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%f")
    filename = f"{message_type}_{timestamp}.json"

    message = {
        "from": "verifier",
        "to": "coder",
        "subject": message_type,
        "body": body,
        "session_id": session_dir.name,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    log(f"📤 Writing verifier message: {message_type} -> {outbox_dir}/{filename}")
    return _write_message_atomically(outbox_dir, filename, message)


def poll_for_messages(
    outbox_dir: Path,
    session_start_ts: float,
    processed_ids: set,
) -> list[dict]:
    """Poll for new messages in outbox directory.

    Args:
        outbox_dir: Directory to poll (coder_outbox or verifier_outbox)
        session_start_ts: Only process messages created after this timestamp
        processed_ids: Set of already-processed message IDs to skip

    Returns:
        List of new message dicts
    """
    messages = []

    if not outbox_dir.exists():
        return messages

    try:
        for msg_file in outbox_dir.iterdir():
            if not msg_file.is_file():
                continue

            # Skip .tmp files (still being written)
            if msg_file.name.endswith(".tmp"):
                continue

            # Skip files older than session start
            try:
                mtime = msg_file.stat().st_mtime
                if mtime < session_start_ts:
                    continue
            except OSError:
                continue

            # Generate message ID from filename
            msg_id = msg_file.stem  # filename without extension

            # Skip already-processed messages
            if msg_id in processed_ids:
                continue

            # Read and parse message
            try:
                with open(msg_file, encoding="utf-8") as f:
                    msg_data = json.load(f)

                # Add message ID to data
                msg_data["message_id"] = msg_id

                # Check message timestamp is after session start
                msg_ts = msg_data.get("timestamp", "")
                if msg_ts:
                    try:
                        msg_dt = datetime.fromisoformat(msg_ts.replace("Z", "+00:00"))
                        if msg_dt.timestamp() < session_start_ts:
                            continue
                    except (ValueError, TypeError):
                        pass

                messages.append(msg_data)
                processed_ids.add(msg_id)
                log(f"📥 Found new message: {msg_file.name}")

            except (OSError, json.JSONDecodeError) as exc:
                log(f"⚠️  Error reading message {msg_file}: {exc}")
                continue

    except OSError as exc:
        log(f"⚠️  Error polling outbox {outbox_dir}: {exc}")

    return messages


def poll_verifier_outbox(session_dir: Path, session_start_ts: float) -> list[dict]:
    """Poll verifier outbox for messages to coder.

    Args:
        session_dir: Session directory
        session_start_ts: Only process messages after this timestamp

    Returns:
        List of messages from verifier
    """
    outbox_dir = session_dir / "coordination" / "verifier_outbox"
    # Load persisted processed IDs to avoid re-processing messages
    processed_ids = _load_processed_message_ids(session_dir, "verifier")
    messages = poll_for_messages(outbox_dir, session_start_ts, processed_ids)
    # Persist updated processed IDs
    _save_processed_message_ids(session_dir, "verifier", processed_ids)
    return messages


def poll_coder_outbox(session_dir: Path, session_start_ts: float) -> list[dict]:
    """Poll coder outbox for messages to verifier.

    Args:
        session_dir: Session directory
        session_start_ts: Only process messages after this timestamp

    Returns:
        List of messages from coder
    """
    outbox_dir = session_dir / "coordination" / "coder_outbox"
    # Load persisted processed IDs to avoid re-processing messages
    processed_ids = _load_processed_message_ids(session_dir, "coder")
    messages = poll_for_messages(outbox_dir, session_start_ts, processed_ids)
    # Persist updated processed IDs
    _save_processed_message_ids(session_dir, "coder", processed_ids)
    return messages


def _load_processed_message_ids(session_dir: Path, agent: str) -> set:
    """Load persisted processed message IDs for an agent.

    Args:
        session_dir: Session directory
        agent: Agent name (coder or verifier)

    Returns:
        Set of already-processed message IDs
    """
    processed_ids_file = session_dir / "coordination" / f"processed_{agent}_ids.json"
    if processed_ids_file.exists():
        try:
            with open(processed_ids_file, encoding="utf-8") as f:
                return set(json.load(f))
        except (OSError, json.JSONDecodeError):
            pass
    return set()


def _save_processed_message_ids(session_dir: Path, agent: str, processed_ids: set):
    """Persist processed message IDs for an agent.

    Args:
        session_dir: Session directory
        agent: Agent name (coder or verifier)
        processed_ids: Set of message IDs to persist
    """
    processed_ids_file = session_dir / "coordination" / f"processed_{agent}_ids.json"
    try:
        with open(processed_ids_file, "w", encoding="utf-8") as f:
            json.dump(list(processed_ids), f)
    except OSError as exc:
        log(
            "❌ Failed to persist processed message IDs "
            f"(agent={agent}, path={processed_ids_file}): {exc}"
        )


def update_agent_status(session_dir: Path, agent: str, status: str, details: dict | None = None):
    """Update agent status in coordination/status directory.

    Args:
        session_dir: Session directory
        agent: Agent name (coder or verifier)
        status: Status string (launched, running, completed, failed)
        details: Optional additional status details
    """
    status_dir = session_dir / "coordination" / "status"
    _validate_session_path(status_dir, session_dir)

    status_data = {
        "agent": agent,
        "status": status,
        "session_id": session_dir.name,
        "updated_at": datetime.now(UTC).isoformat(),
    }

    if details:
        status_data["details"] = details

    try:
        _write_message_atomically(status_dir, f"{agent}.json", status_data)
        log(f"📊 Updated {agent} status: {status}")
    except OSError as exc:
        log(f"⚠️  Failed to update {agent} status: {exc}")


def create_bead_entry(bead_id: str, task_description: str) -> bool:
    """Create bead entry for state tracking with fcntl locking."""
    try:
        beads_path = Path(BEADS_FILE)
        beads_path.parent.mkdir(parents=True, exist_ok=True)

        title = f"Pair Session: {task_description[:50]}"
        if len(task_description) > 50:
            title += "..."

        timestamp = datetime.now(UTC).isoformat()
        bead = {
            "id": bead_id,
            "title": title,
            "description": f"Dual-agent pair programming session for: {task_description}",
            "status": "in_progress",
            "priority": 1,
            "issue_type": "task",
            "created_at": timestamp,
            "updated_at": timestamp,
        }

        with open(beads_path, "a", encoding="utf-8") as f:
            try:
                fcntl.flock(f, fcntl.LOCK_EX)
                f.write(json.dumps(bead) + "\n")
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

        log(f"Created bead: {bead_id}")
        return True

    except (OSError, json.JSONDecodeError) as e:
        log(f"Error creating bead: {e}")
        return False
    except Exception as e:
        log(f"Unexpected error creating bead: {e}")
        return False


def update_bead_status(bead_id: str, status: str) -> bool:
    """Update bead status in beads file with fcntl locking."""
    try:
        beads_path = Path(BEADS_FILE)
        if not beads_path.exists():
            log(f"Beads file not found: {beads_path}")
            return False

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
                    if bead.get("id") == bead_id:
                        bead["status"] = status
                        bead["updated_at"] = datetime.now(UTC).isoformat()
                        updated = True
                        break

                if not updated:
                    log(f"Bead {bead_id} not found")
                    return False

                # Write back
                f.seek(0)
                f.truncate()
                for bead in beads:
                    f.write(json.dumps(bead) + "\n")
                f.flush()
                os.fsync(f.fileno())

            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

        log(f"Bead {bead_id} updated to status: {status}")
        return True

    except (OSError, json.JSONDecodeError) as e:
        log(f"Error updating bead: {e}")
        return False
    except Exception as e:
        log(f"Unexpected error updating bead: {e}")
        return False


def create_tdd_paired_beads(session_id: str, task_description: str) -> dict | None:
    """Create TDD paired beads for tests, implementation, and verification.

    Returns dict with bead IDs or None if creation failed.
    """
    try:
        timestamp = datetime.now(UTC).isoformat()

        # Bead IDs following pattern: session-id-suffix
        tests_bead_id = f"{session_id}-tests"
        impl_bead_id = f"{session_id}-impl"
        verification_bead_id = f"{session_id}-verification"

        log("Creating TDD paired beads...")

        # Create tests bead
        tests_bead = {
            "id": tests_bead_id,
            "title": f"[TESTS] {task_description[:40]}...",
            "description": f"Write tests for: {task_description}",
            "status": "todo",
            "priority": 1,
            "issue_type": "task",
            "created_at": timestamp,
            "updated_at": timestamp,
        }

        # Create implementation bead
        impl_bead = {
            "id": impl_bead_id,
            "title": f"[IMPL] {task_description[:40]}...",
            "description": f"Implement: {task_description}",
            "status": "todo",
            "priority": 2,
            "issue_type": "task",
            "created_at": timestamp,
            "updated_at": timestamp,
        }

        # Create verification bead
        verification_bead = {
            "id": verification_bead_id,
            "title": f"[VERIFY] {task_description[:40]}...",
            "description": f"Verify implementation for: {task_description}",
            "status": "todo",
            "priority": 3,
            "issue_type": "task",
            "created_at": timestamp,
            "updated_at": timestamp,
        }

        beads_path = Path(BEADS_FILE)
        beads_path.parent.mkdir(parents=True, exist_ok=True)

        with open(beads_path, "a", encoding="utf-8") as f:
            try:
                fcntl.flock(f, fcntl.LOCK_EX)
                f.write(json.dumps(tests_bead) + "\n")
                f.write(json.dumps(impl_bead) + "\n")
                f.write(json.dumps(verification_bead) + "\n")
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

        log(f"✅ Created tests bead: {tests_bead_id}")
        log(f"✅ Created implementation bead: {impl_bead_id}")
        log(f"✅ Created verification bead: {verification_bead_id}")

        return {
            "tests_bead_id": tests_bead_id,
            "impl_bead_id": impl_bead_id,
            "verification_bead_id": verification_bead_id,
        }

    except (OSError, json.JSONDecodeError) as e:
        log(f"Error creating TDD paired beads: {e}")
        return None
    except Exception as e:
        log(f"Unexpected error creating TDD paired beads: {e}")
        return None


def generate_default_instructions(
    task_description: str, session_dir: Path, tdd_beads: dict | None = None
) -> dict | None:
    """Generate default task instructions without brainstorming.

    Args:
        task_description: The task to be implemented
        session_dir: Directory for session artifacts
        tdd_beads: Optional dict with tests_bead_id, impl_bead_id, verification_bead_id
    """
    # Build TDD bead instructions if beads were created
    tdd_bead_instructions = ""
    verification_bead_instructions = ""

    if tdd_beads:
        tdd_bead_instructions = f"""
TDD PAIRED BEADS (CRITICAL):
This task has 3 beads that MUST be updated in order:

1. TESTS BEAD: {tdd_beads['tests_bead_id']}
   - Write tests FIRST (TDD approach)
   - Update status: todo -> in_progress -> done
   - Mark done ONLY when tests are written and failing (RED phase)

2. IMPLEMENTATION BEAD: {tdd_beads['impl_bead_id']}
   - Implement code to make tests pass
   - Update status: todo -> in_progress -> done
   - Mark done ONLY when all tests pass (GREEN phase)

3. VERIFICATION BEAD: {tdd_beads['verification_bead_id']}
   - VERIFIER ONLY can update this bead
   - DO NOT mark this bead as done - only the verifier can
   - This tracks the verifier's review and approval

Update beads using: mcp__beads__update --id <bead-id> --status <status>
"""
        verification_bead_instructions = f"""
VERIFICATION BEAD RESPONSIBILITY (CRITICAL):
YOU are the ONLY agent who can mark the verification bead as done.

Verification Bead: {tdd_beads['verification_bead_id']}
- Update status: todo -> in_progress (when you start review)
- Update status: in_progress -> done (ONLY when ALL verification passes)
- Update status: in_progress -> blocked (if major issues found)

The coder has completed the tests and impl beads. Your job is to verify their work.
"""

    # MCP setup instructions
    mcp_setup_instructions = """
MCP SETUP (Required for Pair Programming):

This session requires two MCP servers for coordination:

1. Beads MCP (steveyegge/beads) - Task tracking
   - Check if available: Try calling mcp__beads__list
   - If not installed: Follow setup at https://github.com/steveyegge/beads
   - Configuration: Add to ~/.claude/mcp.json (server named "beads")
   - IMPORTANT: Before using any beads MCP tools, FIRST call mcp__beads__context with:
     action="set", workspace_root="/Users/$USER/projects/worktree_pair2"
     This is required for beads to find the workspace

2. Agent Mail MCP (jleechanorg/mcp_mail) - Inter-agent messaging
   - Check if available: Try calling mcp__mcp_mail__fetch_inbox
   - If not installed:
     ```bash
     # Clone and install mcp_mail
     git clone https://github.com/jleechanorg/mcp_mail.git ~/mcp_mail
     cd ~/mcp_mail && npm install && npm run build
     ```
   - Configuration: Add to ~/.claude/mcp.json:
     ```json
     {
       "agentmail": {
         "command": "node",
         "args": ["/path/to/mcp_mail/build/index.js"],
         "env": {}
       }
     }
     ```
   - Verify: Check inbox with mcp__mcp_mail__fetch_inbox

If either MCP is unavailable, just continue - the session will use fallback coordination via session directory files.

MCP MAIL REGISTRATION (REQUIRED before sending or fetching messages):
Before using MCP Mail send_message or fetch_inbox, you MUST register using your MCP tools directly:
1. Call mcp__mcp_mail__ensure_project with project_key set to your working directory path
2. Call mcp__mcp_mail__register_agent with project_key and your agent_name
3. ONLY THEN can you call mcp__mcp_mail__send_message or mcp__mcp_mail__fetch_inbox
IMPORTANT: Do NOT use mcp-cli shell commands - use your built-in MCP tools (mcp__mcp_mail__*) directly.
If registration fails, fall back to file-based coordination via the session directory.
"""

    brainstorm_result = {
        "task": task_description,
        "coder_instructions": f"""IMPLEMENTATION TASK: {task_description}

Your role is IMPLEMENTATION. You are the coding agent in a pair programming session.

IMPORTANT: This is an ITERATIVE session. You will continue to run and communicate with
the Verifier agent until BOTH of you agree the work is complete and meets all requirements.

{mcp_setup_instructions}
{tdd_bead_instructions}
Instructions:
1. Write tests FIRST (update tests bead to in_progress, then done when tests written)
2. Implement the requested feature/fix following best practices (update impl bead)
3. Ensure code passes all existing tests
4. Commit your changes with descriptive messages
5. Send IMPLEMENTATION_READY message via MCP Mail when complete

Quality Requirements:
- Follow existing code patterns in the codebase
- Include proper error handling
- Add docstrings/comments for complex logic
- Ensure test coverage for new code

Beads MCP Integration:
- FIRST: Call mcp__beads__context with action="set", workspace_root="/Users/$USER/projects/worktree_pair2"
- Then update bead status as you progress (use mcp__beads__update)
- Track your work in the bead system for visibility
- TDD workflow: tests (todo->done) -> impl (todo->done) -> verification (VERIFIER ONLY)

Iterative Coordination Protocol (INDEPENDENT POLLING):
- YOU are a long-running process - do NOT exit until VERIFICATION_COMPLETE
- Send IMPLEMENTATION_READY to Verifier via MCP Mail (mcp__mcp_mail__send_message)
- Poll inbox in a loop to wait for Verifier response (check every 30 seconds)
- Example polling pattern: while True: fetch_inbox, if messages: break, sleep(30)
- If VERIFICATION_FAILED: Review feedback, fix issues, re-send IMPLEMENTATION_READY, resume polling
- If VERIFICATION_COMPLETE: Update beads, create PR, EXIT successfully
- You may iterate multiple times - this is expected and encouraged for quality
- MCP Mail is optional - agents will use file-based coordination if MCP Mail is unavailable

MCP Mail Communication:
- Use mcp__mcp_mail__send_message to send messages to Verifier
- Use mcp__mcp_mail__fetch_inbox to poll for Verifier responses (every 30s)
- Message body should include: files_changed (list), test_result (pass/fail), test_summary (string)
- Include detailed context in message bodies (files changed, test results, etc.)
""",
        "verifier_instructions": f"""VERIFICATION TASK: Verify implementation for {task_description}

Your role is VERIFICATION. You are the testing agent in a pair programming session.

IMPORTANT: This is an ITERATIVE session. You will continue to run and communicate with
the Coder agent until BOTH of you agree the work is complete and meets all requirements.

{mcp_setup_instructions}
{tdd_bead_instructions}
{verification_bead_instructions}
Instructions:
1. Check MCP Mail for IMPLEMENTATION_READY message from Coder agent
2. Verify tests bead is marked done (tests were written first - TDD)
3. Verify impl bead is marked done (implementation complete)
4. Review the implementation files listed in the message
5. Run all tests: TESTING=true python -m pytest
6. Verify code quality and test coverage
7. Check for common issues:
   - Missing edge cases
   - Security vulnerabilities
   - Performance concerns
   - Documentation gaps

Verification Checklist:
- [ ] Tests bead is marked done
- [ ] Implementation bead is marked done
- [ ] All tests pass
- [ ] New code has test coverage
- [ ] No regressions introduced
- [ ] Code follows project conventions
- [ ] Implementation fully addresses the task requirements

Beads MCP Integration:
- Update verification bead status as you progress (mcp__beads__update)
- YOU ALONE control the verification bead
- Status flow: todo -> in_progress -> done (or blocked if issues)
- Mark done ONLY when you're fully confident in the implementation

Iterative Coordination Protocol (INDEPENDENT POLLING):
- YOU are a long-running process - do NOT exit until you send VERIFICATION_COMPLETE
- Poll inbox in a loop to wait for IMPLEMENTATION_READY from Coder (check every 30 seconds)
- Example polling pattern: while True: fetch_inbox, filter for IMPLEMENTATION_READY, if found: break, sleep(30)
- Receive IMPLEMENTATION_READY → run thorough verification checks
- If issues found: Send VERIFICATION_FAILED with detailed feedback, resume polling for next attempt
- If all checks pass: Send VERIFICATION_COMPLETE, mark verification bead done, EXIT successfully
- You may request fixes multiple times - this is expected and encouraged for quality
- Be thorough and demand excellence - you are the quality gatekeeper
- MCP Mail is optional - agents will use file-based coordination if MCP Mail is unavailable

MCP Mail Communication:
- Use mcp__mcp_mail__fetch_inbox to poll for messages from Coder (every 30s)
- Use mcp__mcp_mail__send_message to send responses to Coder
- Message body should include: feedback (string), files (list), test_result (pass/fail)
- Include detailed feedback in VERIFICATION_FAILED messages (specific files, line numbers, issues)

Response Protocol:
- VERIFICATION_COMPLETE: Only send when ALL criteria met and you're confident
- VERIFICATION_FAILED: Include specific actionable feedback for Coder to address
- After sending FAILED: Resume polling for updated IMPLEMENTATION_READY messages
- When sending VERIFICATION_COMPLETE: ALSO mark verification bead as done, then EXIT
""",
        "success_criteria": [
            "All tests pass",
            "Code implements requested functionality",
            "No regressions introduced",
            "Test coverage meets standards",
        ],
    }

    # Save brainstorm results
    brainstorm_file = session_dir / "brainstorm_results.json"
    try:
        with open(brainstorm_file, "w", encoding="utf-8") as f:
            json.dump(brainstorm_result, f, indent=2)
        log(f"Task plan saved to: {brainstorm_file}")
    except OSError as exc:
        log(
            "Warning: Failed to save task plan to disk; "
            f"continuing with in-memory plan only ({exc})."
        )
    return brainstorm_result


def brainstorm_task(
    task_description: str, session_dir: Path, tdd_beads: dict | None = None
) -> dict | None:
    """Use Superpowers to brainstorm the task (placeholder for actual implementation)."""
    # This would integrate with Chrome Superpowers MCP for actual brainstorming
    # For now, generate a structured plan
    log("Generating task plan via brainstorm...")
    return generate_default_instructions(task_description, session_dir, tdd_beads)


def launch_coder_agent(
    session_id: str,
    bead_id: str,
    instructions: str,
    cli: str = DEFAULT_CODER_CLI,
    verifier_agent_name: str | None = None,
    session_dir: Path | None = None,
    no_worktree: bool = False,
    model: str | None = None,
    agent_suffix: str | None = None,
    agent_name_override: str | None = None,
) -> tuple[bool, str]:
    """Launch coder agent for implementation.

    Args:
        agent_suffix: Optional suffix to make agent name unique (e.g., "iter2" for retries)
        agent_name_override: Pre-sanitized agent name (takes precedence over auto-generation)
    """
    if agent_name_override:
        # Use exact pre-sanitized name from caller (centralized naming)
        agent_name = agent_name_override
    else:
        # Fallback: generate name here for backward compatibility
        agent_name = _get_pair_func("generate_agent_names")(cli, session_id, "coder")
        if agent_suffix:
            agent_name = f"{agent_name}_{agent_suffix}"

    # Generate verifier name if not provided
    if verifier_agent_name:
        verifier_name = verifier_agent_name
    else:
        verifier_name = _get_pair_func("generate_agent_names")(DEFAULT_VERIFIER_CLI, session_id, "verifier")

    # Build the full prompt
    full_prompt = f"""{instructions}

---
PAIR SESSION CONFIGURATION:
- Session ID: {session_id}
- Agent Role: IMPLEMENTATION ({cli.upper()})
- Partner Agent: {verifier_name}
- Bead ID: {bead_id}
- MCP Mail Protocol: Send IMPLEMENTATION_READY when done

MCP MAIL REGISTRATION (do this FIRST, before any send/fetch):
1. Call mcp__mcp_mail__ensure_project with project_key="{os.getcwd()}"
2. Call mcp__mcp_mail__register_agent with project_key="{os.getcwd()}" and agent_name="{agent_name}"
3. ONLY THEN can you send or fetch messages
IMPORTANT: Use your built-in MCP tools (mcp__mcp_mail__*) directly. Do NOT use mcp-cli shell commands.

COMMUNICATION:
When implementation is complete, send this MCP mail message:
MCP Tool: mcp__mcp_mail__send_message
Parameters:
- sender_name: {agent_name}
- to: ["{verifier_name}"]  # MUST be a list, not a string!
- subject: IMPLEMENTATION_READY
- body_md: <include summary of changes>
"""

    log(f"Launching {cli.upper()} coder agent: {agent_name}")

    # Use orchestration to create the agent
    # Run in background with nohup to ensure agent persists
    cmd = [
        sys.executable,
        ORCHESTRATE_SCRIPT,
        "--agent-cli",
        cli,
        "--no-wrap-prompt",
        "--bead",
        bead_id,
        "--mcp-agent",
        agent_name,
        "--lite-mode",  # Skip monitoring loop - caller handles coordination
    ]
    if no_worktree:
        cmd.append("--no-worktree")
    if model:
        cmd.extend(["--model", model])
    cmd.append(full_prompt)
    _AGENT_RESTART_COMMANDS[agent_name] = shlex.join(cmd)

    try:
        # Launch orchestration in background - don't wait for it
        log_file = (
            session_dir / f"{agent_name}.log"
            if session_dir
            else Path(tempfile.gettempdir()) / f"{agent_name}.log"
        )
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # Pass session_dir to agent via environment variable for terminal marker creation
        agent_env = os.environ.copy()
        if session_dir:
            agent_env["PAIR_SESSION_DIR"] = str(session_dir)

        with open(log_file, "w", encoding="utf-8") as f:
            process = subprocess.Popen(  # noqa: S603 # nosec
                cmd,
                stdout=f,
                stderr=subprocess.STDOUT,
                start_new_session=True,  # Detach from parent
                env=agent_env,
            )

        # Give it a moment to start, then verify still running
        time.sleep(3)

        # Check if process is still running (good sign)
        if process.poll() is None:
            log(f"{cli.upper()} coder agent launched successfully: {agent_name}")
            log(f"  Agent log: {log_file}")
            return True, agent_name
        
        # Process exited - check if it was a successful lite-mode launch
        # In lite-mode, orchestrator exits immediately after agent creation
        log_content = _read_log_tail(log_file, max_bytes=8192, tail_chars=2000)
        # Check for success indicators: either summary banner OR successful agent launch message
        if "SESSION COMPLETION SUMMARY" in log_content:
            # Extract agent count from "Successful Agents: N" line
            match = re.search(r"Successful Agents:\s+(\d+)", log_content)
            if match and int(match.group(1)) > 0:
                log(f"{cli.upper()} coder agent launched successfully (lite-mode): {agent_name}")
                log(f"  Agent log: {log_file}")
                return True, agent_name
        elif "launched successfully" in log_content.lower():
            # Also check for general "launched successfully" message
            log(f"{cli.upper()} coder agent launched successfully (lite-mode): {agent_name}")
            log(f"  Agent log: {log_file}")
            return True, agent_name

        # Check if tmux session exists - agent may be running in tmux even if subprocess exited
        # This handles lite-mode where orchestrate_unified.py exits but tmux session continues
        if _check_tmux_session(agent_name):
            log(f"{cli.upper()} coder agent launched successfully (tmux session running): {agent_name}")
            log(f"  Agent log: {log_file}")
            return True, agent_name

        # Process died with no success indicators - real failure
        if log_content:
            log(f"Failed to launch {cli.upper()} coder agent (process exited). Last output:")
            log(f"  {log_content[-500:]}")
        else:
            log(f"Failed to launch {cli.upper()} coder agent (process exited)")
        return False, agent_name

    except Exception as e:
        log(f"Error launching {cli.upper()} coder agent: {e}")
        return False, agent_name


def launch_verifier_agent(
    session_id: str,
    bead_id: str,
    instructions: str,
    cli: str = DEFAULT_VERIFIER_CLI,
    coder_agent_name: str | None = None,
    session_dir: Path | None = None,
    no_worktree: bool = False,
    model: str | None = None,
    agent_name_override: str | None = None,
) -> tuple[bool, str]:
    """Launch verifier agent for test verification.

    Args:
        agent_name_override: Pre-sanitized agent name (takes precedence over auto-generation)
    """
    if agent_name_override:
        # Use exact pre-sanitized name from caller (centralized naming)
        agent_name = agent_name_override
    else:
        # Fallback: generate name here for backward compatibility
        agent_name = _get_pair_func("generate_agent_names")(cli, session_id, "verifier")

    # Generate coder name if not provided
    if coder_agent_name:
        coder_name = coder_agent_name
    else:
        coder_name = _get_pair_func("generate_agent_names")(DEFAULT_CODER_CLI, session_id, "coder")

    # Build the full prompt
    full_prompt = f"""{instructions}

---
PAIR SESSION CONFIGURATION:
- Session ID: {session_id}
- Agent Role: VERIFICATION ({cli.upper()})
- Partner Agent: {coder_name}
- Bead ID: {bead_id}
- MCP Mail Protocol: Poll for IMPLEMENTATION_READY, send VERIFICATION_COMPLETE/FAILED

MCP MAIL REGISTRATION (do this FIRST, before any send/fetch):
1. Call mcp__mcp_mail__ensure_project with project_key="{os.getcwd()}"
2. Call mcp__mcp_mail__register_agent with project_key="{os.getcwd()}" and agent_name="{agent_name}"
3. ONLY THEN can you send or fetch messages
IMPORTANT: Use your built-in MCP tools (mcp__mcp_mail__*) directly. Do NOT use mcp-cli shell commands.

COMMUNICATION:
1. Poll for IMPLEMENTATION_READY from {coder_name} using mcp__mcp_mail__fetch_inbox
2. After verification, send response using mcp__mcp_mail__send_message:
   MCP Tool: mcp__mcp_mail__send_message
   Parameters:
   - sender_name: {agent_name}
   - to: ["{coder_name}"]  # MUST be a list, not a string!
   - subject: VERIFICATION_COMPLETE or VERIFICATION_FAILED
   - body_md: <verification summary>
"""

    log(f"Launching {cli.upper()} verifier agent: {agent_name}")

    # Use orchestration to create the agent
    # Run in background with nohup to ensure agent persists
    cmd = [
        sys.executable,
        ORCHESTRATE_SCRIPT,
        "--agent-cli",
        cli,
        "--no-wrap-prompt",
        "--bead",
        bead_id,
        "--mcp-agent",
        agent_name,
        "--lite-mode",  # Skip monitoring loop - caller handles coordination
    ]
    if no_worktree:
        cmd.append("--no-worktree")
    if model:
        cmd.extend(["--model", model])
    cmd.append(full_prompt)
    _AGENT_RESTART_COMMANDS[agent_name] = shlex.join(cmd)

    try:
        # Launch orchestration in background - don't wait for it
        log_file = (
            session_dir / f"{agent_name}.log"
            if session_dir
            else Path(tempfile.gettempdir()) / f"{agent_name}.log"
        )
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # Pass session_dir to agent via environment variable for terminal marker creation
        agent_env = os.environ.copy()
        if session_dir:
            agent_env["PAIR_SESSION_DIR"] = str(session_dir)

        with open(log_file, "w", encoding="utf-8") as f:
            process = subprocess.Popen(  # noqa: S603 # nosec
                cmd,
                stdout=f,
                stderr=subprocess.STDOUT,
                start_new_session=True,  # Detach from parent
                env=agent_env,
            )

        # Give it a moment to start, then verify still running
        time.sleep(3)

        # Check if process is still running (good sign)
        if process.poll() is None:
            log(f"{cli.upper()} verifier agent launched successfully: {agent_name}")
            log(f"  Agent log: {log_file}")
            return True, agent_name
        
        # Process exited - check if it was a successful lite-mode launch
        # In lite-mode, orchestrator exits immediately after agent creation
        log_content = _read_log_tail(log_file, max_bytes=8192, tail_chars=2000)
        if "SESSION COMPLETION SUMMARY" in log_content:
            # Extract agent count from "Successful Agents: N" line
            match = re.search(r"Successful Agents:\s+(\d+)", log_content)
            if match and int(match.group(1)) > 0:
                log(f"{cli.upper()} verifier agent launched successfully (lite-mode): {agent_name}")
                log(f"  Agent log: {log_file}")
                return True, agent_name

        # Check if tmux session exists - agent may be running in tmux even if subprocess exited
        # This handles lite-mode where orchestrate_unified.py exits but tmux session continues
        if _check_tmux_session(agent_name):
            log(f"{cli.upper()} verifier agent launched successfully (tmux session running): {agent_name}")
            log(f"  Agent log: {log_file}")
            return True, agent_name

        # Process died with no success indicators - real failure
        if log_content:
            log(f"Failed to launch {cli.upper()} verifier agent (process exited). Last output:")
            log(f"  {log_content[-500:]}")
        else:
            log(f"Failed to launch {cli.upper()} verifier agent (process exited)")
        return False, agent_name

    except Exception as e:
        log(f"Error launching {cli.upper()} verifier agent: {e}")
        return False, agent_name


def start_background_monitor(
    session_id: str,
    coder_agent: str,
    verifier_agent: str,
    bead_id: str,
    session_dir: Path,
    coder_restart_cmd: str = "",
    verifier_restart_cmd: str = "",
    max_run_attempts: int = DEFAULT_MAX_ITERATIONS,
    interval: int = DEFAULT_MONITOR_INTERVAL,
    tmux_sockets: list[str] | None = None,
) -> int | None:
    """Start background monitor process."""
    log("Starting background monitor...")

    monitor_log = session_dir / "monitor.log"
    pid_file = session_dir / "monitor.pid"

    if not coder_restart_cmd:
        coder_restart_cmd = _AGENT_RESTART_COMMANDS.get(coder_agent, "")
    if not verifier_restart_cmd:
        verifier_restart_cmd = _AGENT_RESTART_COMMANDS.get(verifier_agent, "")

    # Treat max_run_attempts as total allowed launches per agent.
    # Initial launch counts as run 1, so monitor restarts are (run_attempts - 1).
    max_run_attempts = max(1, int(max_run_attempts))
    max_restarts = max_run_attempts - 1

    cmd = [
        sys.executable,
        MONITOR_SCRIPT,
        "--session-id",
        session_id,
        "--coder-agent",
        coder_agent,
        "--verifier-agent",
        verifier_agent,
        "--bead-id",
        bead_id,
        "--coder-cmd",
        coder_restart_cmd,
        "--verifier-cmd",
        verifier_restart_cmd,
        "--max-restarts",
        str(max_restarts),
        "--interval",
        str(interval),
        "--session-dir",
        str(session_dir),
    ]
    if tmux_sockets:
        cmd.append("--tmux-sockets")
        cmd.extend(tmux_sockets)

    try:
        # Start monitor as background process
        with open(monitor_log, "w", encoding="utf-8") as log_file:
            process = subprocess.Popen(  # noqa: S603 # nosec
                cmd,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                start_new_session=True,  # Detach from parent
            )

        # Give it a moment to start
        time.sleep(1)

        # Check if process is still running (good sign)
        if process.poll() is not None:
            # Fast-exit can be valid when monitor immediately writes a terminal status.
            status_file = session_dir / "status.json"
            if status_file.exists():
                try:
                    with open(status_file, encoding="utf-8") as f:
                        status_data = json.load(f)
                    if status_data.get("session_id") == session_id:
                        v_status = str(status_data.get("verifier_status") or "").lower()
                        c_status = str(status_data.get("coder_status") or "").lower()
                        terminal_statuses = {"completed", "failed", "error", "not_found", "ended", "timeout"}
                        if c_status in terminal_statuses and v_status in terminal_statuses:
                            log(
                                "Monitor exited immediately after writing terminal session status "
                                f"(coder={c_status}, verifier={v_status})"
                            )
                            return 0
                except (OSError, json.JSONDecodeError):
                    pass
            log("Failed to start monitor (process exited immediately)")
            return None

        # Write PID
        with open(pid_file, "w", encoding="utf-8") as f:
            f.write(str(process.pid))

        log(f"Monitor started (PID: {process.pid})")
        log(f"Monitor log: {monitor_log}")
        return process.pid

    except Exception as e:
        log(f"Error starting monitor: {e}")
        return None


def _discover_tmux_sockets(agent_log: Path) -> list[str]:
    """Discover custom tmux socket names from orchestration log output.

    Orchestrate_unified.py creates tmux sessions on custom sockets
    named orch-{pid}-{timestamp}. This function parses the agent log
    to find those socket names so the monitor can find the sessions.
    """
    sockets = []
    try:
        if not agent_log.exists():
            return sockets
        content = agent_log.read_text(encoding="utf-8", errors="replace")
        # Look for "tmux -L orch-XXXXX-YYYYY" patterns in the log
        matches = re.findall(r"tmux -L (orch-\d+-\d+)", content)
        sockets = list(set(matches))
        if sockets:
            log(f"Discovered tmux sockets from {agent_log.name}: {sockets}")
    except OSError as e:
        # Log file unreadable; fall through to /tmp socket scan below
        log(f"OSError reading {agent_log}: {e}")
    # Also scan /tmp for recently-created orchestration sockets
    if not sockets:
        tmp_dir = Path("/tmp")
        for tmux_dir in tmp_dir.glob("tmux-*/"):
            try:
                dir_entries = list(tmux_dir.iterdir())
            except OSError as e:
                # Skip unreadable dirs (e.g. other users' tmux-* with 0700 perms)
                log(f"OSError reading tmux dir {tmux_dir}: {e}")
                continue
            for socket_file in dir_entries:
                if socket_file.name.startswith("orch-"):
                    # Check if socket was created recently (last 30 seconds)
                    try:
                        age = time.time() - socket_file.stat().st_mtime
                        if age < 30:
                            sockets.append(socket_file.name)
                    except OSError as e:
                        log(f"OSError stat-ing socket {socket_file}: {e}")
                        continue
    return list(set(sockets))


def main():  # noqa: PLR0915
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Launch dual-agent pair programming session (default: Claude + Codex)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
    # Default: Claude coder + Codex verifier
    python3 .claude/scripts/pair_execute.py "Add user authentication with JWT"

    # Custom: Gemini coder + Claude verifier
    python3 .claude/scripts/pair_execute.py --coder-cli gemini --verifier-cli claude "Task"

    # Same CLI for both: Claude + Claude
    python3 .claude/scripts/pair_execute.py --coder-cli claude --verifier-cli claude "Task"

    # Switch Claude-family backend to MiniMax with one flag
    python3 .claude/scripts/pair_execute.py --claude-provider minimax --verifier-cli claude "Task"

    # With brainstorm phase
    python3 .claude/scripts/pair_execute.py --brainstorm "Implement dark mode toggle"

    # Custom run-attempt budget (initial launch + restarts)
    python3 .claude/scripts/pair_execute.py --max-iterations 5 --interval 30 "Fix bug"

    # Role-specific models (recommended)
    python3 .claude/scripts/pair_execute.py --coder-model opus --verifier-model gpt-5 "Task"

    Supported CLIs: {", ".join(SUPPORTED_CLIS)}
        """,
    )

    parser.add_argument("task", help="Task description")
    parser.add_argument(
        "--coder-cli",
        "-_coder_cli",
        dest="coder_cli",
        choices=SUPPORTED_CLIS,
        default=DEFAULT_CODER_CLI,
        help=f"CLI for coder agent (default: {DEFAULT_CODER_CLI})",
    )
    parser.add_argument(
        "--verifier-cli",
        "-_verifier_cli",
        dest="verifier_cli",
        choices=SUPPORTED_CLIS,
        default=DEFAULT_VERIFIER_CLI,
        help=f"CLI for verifier agent (default: {DEFAULT_VERIFIER_CLI})",
    )
    parser.add_argument(
        "--claude-provider",
        choices=sorted(CLAUDE_FAMILY_CLIS),
        default=DEFAULT_CLAUDE_PROVIDER if DEFAULT_CLAUDE_PROVIDER in CLAUDE_FAMILY_CLIS else None,
        help=(
            "Global backend override for claude-family roles "
            "(claude|minimax). Applies only when role CLI is claude/minimax. "
            "Can also be set via PAIR_CLAUDE_PROVIDER."
        ),
    )
    parser.add_argument(
        "--coder-claude-provider",
        choices=sorted(CLAUDE_FAMILY_CLIS),
        default=None,
        help=(
            "Coder backend override for claude-family CLI "
            "(requires --coder-cli claude|minimax)."
        ),
    )
    parser.add_argument(
        "--verifier-claude-provider",
        choices=sorted(CLAUDE_FAMILY_CLIS),
        default=None,
        help=(
            "Verifier backend override for claude-family CLI "
            "(requires --verifier-cli claude|minimax)."
        ),
    )
    parser.add_argument(
        "--brainstorm",
        action="store_true",
        help="Run brainstorm phase before launching agents",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=DEFAULT_MAX_ITERATIONS,
        help=(
            "Maximum run attempts per agent (initial launch counts as 1; "
            f"default: {DEFAULT_MAX_ITERATIONS})"
        ),
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=DEFAULT_MONITOR_INTERVAL,
        help=f"Monitor check interval in seconds (default: {DEFAULT_MONITOR_INTERVAL})",
    )
    parser.add_argument(
        "--no-worktree",
        action="store_true",
        help="Run agents in current directory (no git worktree isolation)",
    )
    parser.add_argument(
        "--coder-model",
        default=None,
        help="Model for coder agent only (e.g., opus, sonnet, haiku)",
    )
    parser.add_argument(
        "--verifier-model",
        default=None,
        help="Model for verifier agent only (e.g., gpt-5)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Legacy alias for --coder-model (coder agent only)",
    )

    args = parser.parse_args()
    coder_model, verifier_model = _resolve_role_models(args)

    try:
        resolved_coder_cli = _resolve_claude_backend(
            selected_cli=args.coder_cli,
            provider=args.claude_provider,
            role_name="coder",
            strict=False,
        )
        resolved_verifier_cli = _resolve_claude_backend(
            selected_cli=args.verifier_cli,
            provider=args.claude_provider,
            role_name="verifier",
            strict=False,
        )
        resolved_coder_cli = _resolve_claude_backend(
            selected_cli=resolved_coder_cli,
            provider=args.coder_claude_provider,
            role_name="coder",
            strict=True,
        )
        resolved_verifier_cli = _resolve_claude_backend(
            selected_cli=resolved_verifier_cli,
            provider=args.verifier_claude_provider,
            role_name="verifier",
            strict=True,
        )
    except ValueError as exc:
        log(f"❌ {exc}")
        sys.exit(2)

    if (
        resolved_coder_cli == "minimax" or resolved_verifier_cli == "minimax"
    ) and not os.environ.get("MINIMAX_API_KEY"):
        log("❌ MiniMax selected but MINIMAX_API_KEY is not set.")
        log("   Export MINIMAX_API_KEY, then retry /pair.")
        sys.exit(2)

    # Initialize session
    log("=" * 60)
    log("PAIR PROGRAMMING SESSION")
    log("=" * 60)

    session_id = generate_session_id()
    session_dir = create_session_directory(session_id)
    bead_id = session_id

    log(f"Session ID: {session_id}")
    log(f"Task: {args.task}")
    log(f"Session Dir: {session_dir}")

    # Check MCP Mail availability and warn if not available
    log_mcp_mail_warning(session_dir)

    # Phase 1: Create TDD paired beads
    log("")
    log("Phase 1: Creating TDD paired beads (tests, impl, verification)...")
    tdd_beads = create_tdd_paired_beads(session_id, args.task)
    if not tdd_beads:
        log("Warning: Failed to create TDD paired beads, continuing anyway")

    # Also create session tracking bead
    log("")
    log("Phase 1b: Creating session tracking bead...")
    if not create_bead_entry(bead_id, args.task):
        log("Warning: Failed to create session bead entry, continuing anyway")

    # Phase 2: Brainstorm (if requested)
    brainstorm_result = None
    if args.brainstorm:
        log("")
        log("Phase 2: Brainstorming task...")
        brainstorm_result = brainstorm_task(args.task, session_dir, tdd_beads)
    else:
        # Generate default instructions without brainstorming
        log("")
        log("Phase 2: Generating default task plan...")
        brainstorm_result = generate_default_instructions(args.task, session_dir, tdd_beads)

    if not brainstorm_result:
        log("Failed to generate task plan")
        sys.exit(1)

    # Build agent names based on CLI selection
    verifier_agent_name = generate_agent_names(resolved_verifier_cli, session_id, "verifier")

    # Generate a shared tmux socket for this pair session
    # Both agents will use the same socket so we can monitor them together
    pair_socket = session_id.replace("pair-", "")  # session_id is like "pair-123-456", extract "123-456"
    os.environ["ORCHESTRATION_TMUX_SOCKET"] = pair_socket
    log(f"Using shared tmux socket for pair session: {pair_socket}")

    # Phase 3: Launch coder agent
    log("")
    log(f"Phase 3: Launching {resolved_coder_cli.upper()} coder agent (Implementation)...")
    coder_success, coder_agent = launch_coder_agent(
        session_id,
        bead_id,
        brainstorm_result["coder_instructions"],
        cli=resolved_coder_cli,
        verifier_agent_name=verifier_agent_name,
        session_dir=session_dir,
        no_worktree=args.no_worktree,
        model=coder_model,
    )

    if not coder_success:
        log(f"Failed to launch {resolved_coder_cli.upper()} coder agent")
        update_bead_status(bead_id, "failed")
        sys.exit(1)

    # Update file-based coordination status
    update_agent_status(session_dir, "coder", "launched", {"cli": resolved_coder_cli})

    # Brief delay to stagger agent launches
    time.sleep(2)

    # Phase 4: Launch verifier agent
    log("")
    log(
        f"Phase 4: Launching {resolved_verifier_cli.upper()} verifier agent (Verification)..."
    )
    verifier_success, verifier_agent = launch_verifier_agent(
        session_id,
        bead_id,
        brainstorm_result["verifier_instructions"],
        cli=resolved_verifier_cli,
        coder_agent_name=coder_agent,
        session_dir=session_dir,
        no_worktree=args.no_worktree,
        model=verifier_model,
    )

    if not verifier_success:
        log(f"Failed to launch {resolved_verifier_cli.upper()} verifier agent")
        # Update bead status to partial-failure
        update_bead_status(bead_id, "partial-failure")
        log(f"⚠️  PARTIAL SESSION: Only {resolved_coder_cli.upper()} coder agent is running")
        log("⚠️  Background monitor will NOT start (requires both agents)")
        log("🛑 Terminating orphaned coder session to avoid unsupervised repo mutations")
        _terminate_tmux_session(coder_agent, tmux_sockets)
        sys.exit(1)
    else:
        # Update file-based coordination status
        update_agent_status(session_dir, "verifier", "launched", {"cli": resolved_verifier_cli})

        # Use the socket we set via ORCHESTRATION_TMUX_SOCKET env var
        # Both agents used the same socket so we can monitor them together
        tmux_sockets = [pair_socket]
        log(f"Using pair session tmux socket: {tmux_sockets}")

        # Phase 5: Start background monitor (requires both agents running)
        monitor_pid = None
        log("")
        log("Phase 5: Starting background monitor...")
        # Enforce user-provided run budget as restart limit for each agent.
        monitor_pid = start_background_monitor(
            session_id,
            coder_agent,
            verifier_agent,
            bead_id,
            session_dir,
            coder_restart_cmd="",
            verifier_restart_cmd="",
            max_run_attempts=args.max_iterations,
            interval=args.interval,
            tmux_sockets=tmux_sockets,
        )
        if monitor_pid is None:
            log("❌ Background monitor failed to start; terminating both agent sessions")
            update_agent_status(session_dir, "coder", "failed", {"reason": "monitor_start_failed"})
            update_agent_status(session_dir, "verifier", "failed", {"reason": "monitor_start_failed"})
            _terminate_tmux_session(coder_agent, tmux_sockets)
            _terminate_tmux_session(verifier_agent, tmux_sockets)
            update_bead_status(bead_id, "failed")
            sys.exit(1)

        # REV-x7lm1: Transition from launched -> running once monitor is active
        update_agent_status(session_dir, "coder", "running", {"cli": resolved_coder_cli})
        update_agent_status(session_dir, "verifier", "running", {"cli": resolved_verifier_cli})

    # Summary
    log("")
    log("=" * 60)
    log("PAIR SESSION LAUNCHED")
    log("=" * 60)
    log(f"Session ID: {session_id}")
    log(f"Coder Agent ({resolved_coder_cli.upper()}): {coder_agent}")
    log(f"Verifier Agent ({resolved_verifier_cli.upper()}): {verifier_agent}")
    log(f"Bead ID: {bead_id}")
    log(f"Monitor PID: {monitor_pid or 'N/A'}")
    log("")
    log("File-Based Coordination:")
    log(f"  {session_dir}/coordination/")
    log(f"  - coder_outbox/     # Messages from coder")
    log(f"  - verifier_outbox/  # Messages from verifier")
    log(f"  - status/           # Agent status")
    log("")
    log("Monitoring Commands:")
    log(f"  tmux attach -t {coder_agent}  # View coder agent")
    log(f"  tmux attach -t {verifier_agent}   # View verifier agent")
    log(f"  tail -f {session_dir}/monitor.log  # View monitor log")
    log("")
    log("Stop Session:")
    if monitor_pid:
        log(f"  kill {monitor_pid}  # Stop monitor")
    else:
        log("  # Monitor not running")
    log(f"  tmux kill-session -t {coder_agent}")
    log(f"  tmux kill-session -t {verifier_agent}")
    log("=" * 60)


if __name__ == "__main__":
    main()
