#!/usr/bin/env python3
"""
TMux Agent Cleanup Utility

This script identifies and cleans up completed tmux agents that are sitting idle.
Agents are considered completed if they have completion markers in their logs.
"""

# Allow direct script execution - add parent directory to sys.path
import os
import sys

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import argparse
import json
import subprocess
import time
from typing import Any, Dict, List

# Use absolute imports with package name for __main__ compatibility
from orchestration.constants import IDLE_MINUTES_THRESHOLD


def get_tmux_sessions() -> List[str]:
    """Get list of all tmux session names."""
    try:
        result = subprocess.run(
            ["tmux", "list-sessions", "-F", "#{session_name}"],
            shell=False,
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        return [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]
    except subprocess.CalledProcessError:
        return []


def get_task_agent_sessions() -> List[str]:
    """Get list of task-agent-* tmux sessions."""
    all_sessions = get_tmux_sessions()
    return [s for s in all_sessions if s.startswith("task-agent-")]


def get_all_monitoring_sessions() -> List[str]:
    """Get list of ALL monitoring tmux sessions (orchestration + manual)."""
    all_sessions = get_tmux_sessions()
    monitoring_patterns = [
        "task-agent-",  # Orchestration agents
        "gh-comment-monitor-",  # GitHub comment monitoring
        "copilot-",  # Copilot analysis sessions
        "agent-",  # Generic agent sessions
    ]
    return [s for s in all_sessions if any(s.startswith(pattern) for pattern in monitoring_patterns)]


def get_session_timeout(session_name: str) -> int:
    """Get timeout in seconds based on session name pattern.

    Args:
        session_name: The tmux session name to check

    Returns:
        Timeout value in seconds based on session name pattern
    """
    # Pattern-based timeouts (in seconds)
    SESSION_TIMEOUTS = {
        "task-agent-": 3600,  # 1 hour (orchestration)
        "gh-comment-monitor-": 14400,  # 4 hours (monitoring)
        "copilot-": 7200,  # 2 hours (analysis)
        "agent-": 10800,  # 3 hours (generic agents)
    }

    for pattern, timeout in SESSION_TIMEOUTS.items():
        if session_name.startswith(pattern):
            return timeout

    return 86400  # 24 hours default for unknown patterns


def check_agent_completion(agent_name: str) -> Dict[str, Any]:
    """Check if an agent has completed by examining its log."""
    log_path = f"/tmp/orchestration_logs/{agent_name}.log"

    if not os.path.exists(log_path):
        return {"completed": False, "reason": "no_log_file"}

    completion_markers = [
        "Claude exit code: 0",
        "Agent completed successfully",
        '"subtype":"success"',
        '"is_error":false,"duration_ms"',
    ]

    try:
        # Check last 50 lines for completion markers
        result = subprocess.run(["tail", "-50", log_path], shell=False, capture_output=True, text=True, timeout=30)

        log_content = result.stdout.lower()

        for marker in completion_markers:
            if marker.lower() in log_content:
                return {"completed": True, "reason": f"found_marker: {marker}", "log_path": log_path}

        # Check if session has been idle (no recent activity)
        stat = os.stat(log_path)
        last_modified = stat.st_mtime
        now = time.time()
        idle_minutes = (now - last_modified) / 60

        if idle_minutes > IDLE_MINUTES_THRESHOLD:  # Minutes of no activity threshold
            return {"completed": True, "reason": f"idle_for_{idle_minutes:.1f}_minutes", "log_path": log_path}

        return {"completed": False, "reason": "still_active"}

    except Exception as e:
        return {"completed": False, "reason": f"error: {e}"}


def check_session_timeout(session_name: str) -> Dict[str, Any]:
    """Check if a session has exceeded its timeout based on last activity.

    Args:
        session_name: The tmux session name to check

    Returns:
        Dict containing timeout status, reason, and timing information
    """
    try:
        # Get session activity timestamp using display-message for specific session
        result = subprocess.run(
            ["tmux", "display-message", "-p", "-t", session_name, "#{session_activity}"],
            shell=False,
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )

        if not result.stdout.strip():
            return {"timeout": False, "reason": "session_not_found"}

        # Parse session activity timestamp directly
        try:
            session_activity = int(result.stdout.strip())
        except ValueError:
            return {"timeout": False, "reason": "invalid_timestamp"}
        current_time = int(time.time())
        elapsed_seconds = current_time - session_activity

        timeout_seconds = get_session_timeout(session_name)

        if elapsed_seconds > timeout_seconds:
            return {
                "timeout": True,
                "reason": "timeout_exceeded",
                "elapsed_seconds": elapsed_seconds,
                "timeout_seconds": timeout_seconds,
                "elapsed_hours": elapsed_seconds / 3600,
            }
        else:
            return {
                "timeout": False,
                "reason": "within_timeout",
                "elapsed_seconds": elapsed_seconds,
                "timeout_seconds": timeout_seconds,
            }

    except Exception as e:
        return {"timeout": False, "reason": f"error: {e}"}


def cleanup_agent_session(agent_name: str, dry_run: bool = False) -> bool:
    """Cleanup a completed agent session.

    Args:
        agent_name: Name of the agent session to cleanup
        dry_run: If True, only show what would be cleaned up

    Returns:
        True if cleanup succeeded (or would succeed in dry-run), False otherwise
    """
    print(f"{'[DRY RUN] ' if dry_run else ''}Cleaning up session: {agent_name}")

    if not dry_run:
        try:
            # Kill the tmux session
            subprocess.run(["tmux", "kill-session", "-t", agent_name], shell=False, check=True, timeout=30)
            print(f"  ✅ Session {agent_name} terminated")
            return True
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Failed to kill session {agent_name}: {e}")
            return False
    else:
        print(f"  Would terminate session: {agent_name}")
        return True


def cleanup_completed_agents(dry_run: bool = False) -> Dict[str, Any]:
    """Main cleanup function for all monitoring sessions.

    Args:
        dry_run: If True, only show what would be cleaned up without doing it

    Returns:
        Dict containing cleanup statistics and session information
    """

    print("🔍 Scanning for all monitoring tmux sessions...")

    # Get all monitoring sessions (not just task-agent)
    all_monitoring = get_all_monitoring_sessions()
    print(f"Found {len(all_monitoring)} monitoring sessions")

    completed_agents = []
    timeout_agents = []
    active_agents = []

    for session in all_monitoring:
        # Check for completion (for task-agent sessions with logs)
        if session.startswith("task-agent-"):
            status = check_agent_completion(session)
            if status["completed"]:
                completed_agents.append(
                    {
                        "name": session,
                        "reason": status["reason"],
                        "log_path": status.get("log_path"),
                        "cleanup_type": "completion",
                    }
                )
                continue

        # Check for timeout (all sessions including manual ones)
        timeout_status = check_session_timeout(session)
        if timeout_status["timeout"]:
            timeout_agents.append(
                {
                    "name": session,
                    "reason": timeout_status["reason"],
                    "elapsed_hours": timeout_status.get("elapsed_hours", 0),
                    "cleanup_type": "timeout",
                }
            )
        else:
            active_agents.append(
                {
                    "name": session,
                    "reason": timeout_status["reason"],
                    "elapsed_seconds": timeout_status.get("elapsed_seconds", 0),
                }
            )

    total_to_cleanup = len(completed_agents) + len(timeout_agents)

    print("\n📊 Analysis Results:")
    print(f"  ✅ Completed agents: {len(completed_agents)}")
    print(f"  ⏰ Timeout agents: {len(timeout_agents)}")
    print(f"  🔄 Active agents: {len(active_agents)}")

    cleanup_success = 0

    # Clean up completed agents
    if completed_agents:
        print(f"\n🧹 Cleaning up {len(completed_agents)} completed agents:")
        for agent_info in completed_agents:
            agent_name = agent_info["name"]
            reason = agent_info["reason"]
            print(f"  Agent: {agent_name} (reason: {reason})")

            if cleanup_agent_session(agent_name, dry_run):
                cleanup_success += 1

    # Clean up timeout agents
    if timeout_agents:
        print(f"\n⏰ Cleaning up {len(timeout_agents)} timeout agents:")
        for agent_info in timeout_agents:
            agent_name = agent_info["name"]
            hours = agent_info["elapsed_hours"]
            print(f"  Agent: {agent_name} (idle for {hours:.1f} hours)")

            if cleanup_agent_session(agent_name, dry_run):
                cleanup_success += 1

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Cleanup summary:")
    print(f"  Successfully cleaned up: {cleanup_success}/{total_to_cleanup}")

    if active_agents:
        print("\n🔄 Active agents (not cleaned up):")
        for agent_info in active_agents:
            elapsed_min = agent_info.get("elapsed_seconds", 0) / 60
            print(f"  {agent_info['name']} - {agent_info['reason']} (active {elapsed_min:.1f} min ago)")

    return {
        "total_sessions": len(all_monitoring),
        "completed": len(completed_agents),
        "timeout": len(timeout_agents),
        "active": len(active_agents),
        "cleaned_up": cleanup_success if not dry_run else 0,
        "completed_agents": completed_agents,
        "timeout_agents": timeout_agents,
        "active_agents": active_agents,
    }


def main():
    """Main entry point."""

    parser = argparse.ArgumentParser(description="Cleanup completed tmux agents")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be cleaned up without actually doing it"
    )
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    args = parser.parse_args()

    results = cleanup_completed_agents(dry_run=args.dry_run)

    if args.json:
        print(json.dumps(results, indent=2))

    # Return success (0) if cleanup found sessions to process, failure (1) if error occurred
    return 0


if __name__ == "__main__":
    exit(main())
