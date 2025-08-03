#!/usr/bin/env python3
"""
TMux Agent Cleanup Utility

This script identifies and cleans up completed tmux agents that are sitting idle.
Agents are considered completed if they have completion markers in their logs.
"""

import os
import subprocess
import json
import time
from pathlib import Path
from typing import List, Dict, Set, Any

# Import shared constants
try:
    from .constants import IDLE_MINUTES_THRESHOLD
except ImportError:
    # Fallback for direct execution
    from constants import IDLE_MINUTES_THRESHOLD


def get_tmux_sessions() -> List[str]:
    """Get list of all tmux session names."""
    try:
        result = subprocess.run(
            ["tmux", "list-sessions", "-F", "#{session_name}"],
            capture_output=True,
            text=True,
            check=True
        )
        return [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
    except subprocess.CalledProcessError:
        return []


def get_task_agent_sessions() -> List[str]:
    """Get list of task-agent-* tmux sessions."""
    all_sessions = get_tmux_sessions()
    return [s for s in all_sessions if s.startswith('task-agent-')]


def check_agent_completion(agent_name: str) -> Dict[str, Any]:
    """Check if an agent has completed by examining its log."""
    log_path = f"/tmp/orchestration_logs/{agent_name}.log"

    if not os.path.exists(log_path):
        return {"completed": False, "reason": "no_log_file"}

    completion_markers = [
        "Claude exit code: 0",
        "Agent completed successfully",
        '"subtype":"success"',
        '"is_error":false,"duration_ms"'
    ]

    try:
        # Check last 50 lines for completion markers
        result = subprocess.run(
            ["tail", "-50", log_path],
            capture_output=True,
            text=True
        )

        log_content = result.stdout.lower()

        for marker in completion_markers:
            if marker.lower() in log_content:
                return {
                    "completed": True,
                    "reason": f"found_marker: {marker}",
                    "log_path": log_path
                }

        # Check if session has been idle (no recent activity)
        stat = os.stat(log_path)
        last_modified = stat.st_mtime
        now = time.time()
        idle_minutes = (now - last_modified) / 60

        if idle_minutes > IDLE_MINUTES_THRESHOLD:  # Minutes of no activity threshold
            return {
                "completed": True,
                "reason": f"idle_for_{idle_minutes:.1f}_minutes",
                "log_path": log_path
            }

        return {"completed": False, "reason": "still_active"}

    except Exception as e:
        return {"completed": False, "reason": f"error: {e}"}


def cleanup_agent_session(agent_name: str, dry_run: bool = False) -> bool:
    """Cleanup a completed agent session."""
    print(f"{'[DRY RUN] ' if dry_run else ''}Cleaning up session: {agent_name}")

    if not dry_run:
        try:
            # Kill the tmux session
            subprocess.run(
                ["tmux", "kill-session", "-t", agent_name],
                check=True
            )
            print(f"  ✅ Session {agent_name} terminated")
            return True
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Failed to kill session {agent_name}: {e}")
            return False
    else:
        print(f"  Would terminate session: {agent_name}")
        return True


def cleanup_completed_agents(dry_run: bool = False) -> Dict[str, Any]:
    """Main cleanup function."""

    print("🔍 Scanning for completed tmux agents...")

    task_agents = get_task_agent_sessions()
    print(f"Found {len(task_agents)} task-agent sessions")

    completed_agents = []
    active_agents = []

    for agent in task_agents:
        status = check_agent_completion(agent)

        if status["completed"]:
            completed_agents.append({
                "name": agent,
                "reason": status["reason"],
                "log_path": status.get("log_path")
            })
        else:
            active_agents.append({
                "name": agent,
                "reason": status["reason"]
            })

    print(f"\n📊 Analysis Results:")
    print(f"  ✅ Completed agents: {len(completed_agents)}")
    print(f"  🔄 Active agents: {len(active_agents)}")

    if completed_agents:
        print(f"\n🧹 Cleaning up {len(completed_agents)} completed agents:")
        cleanup_success = 0

        for agent_info in completed_agents:
            agent_name = agent_info["name"]
            reason = agent_info["reason"]
            print(f"  Agent: {agent_name} (reason: {reason})")

            if cleanup_agent_session(agent_name, dry_run):
                cleanup_success += 1

        print(f"\n{'[DRY RUN] ' if dry_run else ''}Cleanup summary:")
        print(f"  Successfully cleaned up: {cleanup_success}/{len(completed_agents)}")

    if active_agents:
        print(f"\n🔄 Active agents (not cleaned up):")
        for agent_info in active_agents:
            print(f"  {agent_info['name']} - {agent_info['reason']}")

    return {
        "total_sessions": len(task_agents),
        "completed": len(completed_agents),
        "active": len(active_agents),
        "cleaned_up": len(completed_agents) if not dry_run else 0,
        "completed_agents": completed_agents,
        "active_agents": active_agents
    }


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Cleanup completed tmux agents")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be cleaned up without actually doing it"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format"
    )

    args = parser.parse_args()

    results = cleanup_completed_agents(dry_run=args.dry_run)

    if args.json:
        print(json.dumps(results, indent=2))

    # Return success (0) if cleanup found sessions to process, failure (1) if error occurred
    return 0


if __name__ == "__main__":
    exit(main())
