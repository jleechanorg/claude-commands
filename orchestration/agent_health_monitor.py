#!/usr/bin/env python3
"""
Agent Health Monitor for Multi-Agent Orchestration System
Monitors agent health, handles failures, and provides auto-recovery
"""

# Allow direct script execution - add parent directory to sys.path
import os
import sys

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import json
import shutil
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

# Use absolute imports with package name for __main__ compatibility
from orchestration.task_dispatcher import get_tmux_config_path


@dataclass
class AgentStatus:
    """Status of an individual agent"""

    name: str
    session_name: str
    status: str  # 'active', 'stopped', 'error', 'recovering'
    last_activity: datetime
    error_count: int
    uptime: timedelta
    current_task: str | None = None
    health_score: float = 1.0  # 0.0 to 1.0


class AgentHealthMonitor:
    """Monitors and manages agent health"""

    def __init__(self, orchestration_dir: str = None):
        self.orchestration_dir = orchestration_dir or os.path.dirname(__file__)
        self.tasks_dir = os.path.join(self.orchestration_dir, "tasks")
        self.agents = {}  # agent_name -> AgentStatus
        self.monitoring_interval = 30  # seconds
        self.max_error_count = 3
        self.startup_script = os.path.join(self.orchestration_dir, "start_system.sh")

        # Dynamic agent system - no fixed expected agents
        # Agents are created on-demand via /orch command
        self.expected_agents = {}

    # Redis initialization removed - using file-based health monitoring

    def get_tmux_sessions(self) -> list[str]:
        """Get list of active tmux sessions"""
        try:
            result = subprocess.run(
                ["tmux", "list-sessions"], shell=False, check=False, capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                sessions = []
                for line in result.stdout.strip().split("\n"):
                    if line and ":" in line:
                        session_name = line.split(":")[0]
                        sessions.append(session_name)
                return sessions
            return []
        except Exception as e:
            print(f"Error getting tmux sessions: {e}")
            return []

    def is_agent_responsive(self, session_name: str) -> bool:
        """Check if agent is responsive via tmux"""
        try:
            # Try to capture recent output
            result = subprocess.run(
                ["tmux", "capture-pane", "-t", session_name, "-p", "-S", "-10"],
                shell=False,
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                output = result.stdout.strip()
                # Look for signs of activity or Claude prompt
                return len(output) > 0 and ("claude" in output.lower() or "agent" in output.lower() or ">" in output)
            return False
        except Exception as e:
            print(f"Error checking agent responsiveness: {e}")
            return False

    def get_agent_last_activity(self, session_name: str) -> datetime:
        """Get last activity timestamp for an agent"""
        try:
            # Get session info
            result = subprocess.run(
                [
                    "tmux",
                    "display-message",
                    "-t",
                    session_name,
                    "-p",
                    "#{session_activity}",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                # tmux returns activity in seconds since epoch
                timestamp = int(result.stdout.strip())
                return datetime.fromtimestamp(timestamp)

            return datetime.now() - timedelta(hours=1)  # Default to old timestamp
        except Exception as e:
            print(f"Error getting agent activity: {e}")
            return datetime.now() - timedelta(hours=1)

    def calculate_health_score(self, agent: AgentStatus) -> float:
        """Calculate health score for an agent"""
        base_score = 1.0

        # Reduce score based on error count
        error_penalty = min(agent.error_count * 0.2, 0.8)
        base_score -= error_penalty

        # Reduce score based on time since last activity
        inactive_time = datetime.now() - agent.last_activity
        if inactive_time > timedelta(minutes=30):
            inactivity_penalty = min(inactive_time.total_seconds() / 3600 * 0.1, 0.5)
            base_score -= inactivity_penalty

        # Boost score if agent is active and has tasks
        if agent.status == "active" and agent.current_task:
            base_score += 0.1

        return max(0.0, min(1.0, base_score))

    def update_agent_status(self):
        """Update status of all agents"""
        active_sessions = self.get_tmux_sessions()

        for agent_name, _config in self.expected_agents.items():
            if agent_name in active_sessions:
                # Agent session exists - check health
                is_responsive = self.is_agent_responsive(agent_name)
                last_activity = self.get_agent_last_activity(agent_name)

                if agent_name in self.agents:
                    # Update existing agent
                    agent = self.agents[agent_name]
                    agent.last_activity = last_activity
                    agent.status = "active" if is_responsive else "error"
                    if not is_responsive:
                        agent.error_count += 1
                    agent.uptime = datetime.now() - (datetime.now() - agent.uptime)
                else:
                    # New agent discovered
                    agent = AgentStatus(
                        name=agent_name,
                        session_name=agent_name,
                        status="active" if is_responsive else "error",
                        last_activity=last_activity,
                        error_count=0 if is_responsive else 1,
                        uptime=timedelta(0),
                    )
                    self.agents[agent_name] = agent

                # Update health score
                agent.health_score = self.calculate_health_score(agent)
            # Agent session not found
            elif agent_name in self.agents:
                self.agents[agent_name].status = "stopped"
                self.agents[agent_name].error_count += 1
            else:
                # Create stopped agent entry
                agent = AgentStatus(
                    name=agent_name,
                    session_name=agent_name,
                    status="stopped",
                    last_activity=datetime.now() - timedelta(hours=1),
                    error_count=1,
                    uptime=timedelta(0),
                )
                self.agents[agent_name] = agent

    def restart_agent(self, agent_name: str) -> bool:
        """Restart a failed agent"""
        try:
            config = self.expected_agents.get(agent_name)
            if not config:
                return False

            print(f"Restarting {agent_name}...")

            # Kill existing session if it exists
            subprocess.run(
                ["tmux", "kill-session", "-t", agent_name],
                check=False,
                capture_output=True,
            )

            # Wait a moment
            time.sleep(2)

            # Restart dynamic agents (task-agent-*)
            # Start Claude agent with portable path discovery
            try:
                project_root = subprocess.run(
                    ["git", "rev-parse", "--show-toplevel"],
                    shell=False,
                    timeout=30,
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip()
            except subprocess.CalledProcessError as e:
                print(f"⚠️ Warning: Failed to determine project root using 'git rev-parse': {e}")
                project_root = os.path.dirname(self.orchestration_dir)

            # Find Claude executable portably
            claude_path = None
            if "CLAUDE_PATH" in os.environ and os.path.exists(os.environ["CLAUDE_PATH"]):
                claude_path = os.environ["CLAUDE_PATH"]
            else:
                claude_path = shutil.which("claude")
                if not claude_path:
                    claude_path = os.path.expanduser("~/.claude/local/claude")

            if not claude_path or not os.path.exists(claude_path):
                print(f"❌ Claude executable not found for agent {agent_name}")
                return False

            # Use agent-specific tmux config for 1-hour sessions
            tmux_config = get_tmux_config_path()

            # Build tmux command with optional config file
            tmux_cmd = ["tmux"]
            if os.path.exists(tmux_config):
                tmux_cmd.extend(["-f", tmux_config])
            else:
                print(f"⚠️ Warning: tmux config file not found at {tmux_config}, using default config")

            tmux_cmd.extend(["new-session", "-d", "-s", agent_name, "-c", project_root, claude_path])

            subprocess.run(tmux_cmd, capture_output=True, check=False)
            # Send initialization message
            time.sleep(3)
            subprocess.run(
                [
                    "tmux",
                    "send-keys",
                    "-t",
                    agent_name,
                    f"I am the {config['type'].title()} Agent specialized in {config['specialization']}.",
                    "Enter",
                ],
                check=False,
                capture_output=True,
            )

            # Update agent status
            if agent_name in self.agents:
                self.agents[agent_name].status = "recovering"
                self.agents[agent_name].error_count = 0

            print(f"✅ {agent_name} restarted successfully")
            return True

        except Exception as e:
            print(f"❌ Failed to restart {agent_name}: {e}")
            return False

    def get_system_health(self) -> dict[str, Any]:
        """Get overall system health report"""
        total_agents = len(self.expected_agents)
        active_agents = sum(1 for agent in self.agents.values() if agent.status == "active")
        avg_health = sum(agent.health_score for agent in self.agents.values()) / max(total_agents, 1)

        return {
            "timestamp": datetime.now(),
            "total_agents": total_agents,
            "active_agents": active_agents,
            "stopped_agents": total_agents - active_agents,
            "average_health_score": avg_health,
            "system_status": "healthy" if avg_health > 0.8 else "degraded" if avg_health > 0.5 else "critical",
            "agents": {
                name: {
                    "status": agent.status,
                    "health_score": agent.health_score,
                    "last_activity": agent.last_activity.isoformat(),
                    "error_count": agent.error_count,
                    "uptime": str(agent.uptime),
                }
                for name, agent in self.agents.items()
            },
        }

    def auto_recover_failed_agents(self):
        """Automatically recover failed agents"""
        for agent_name, agent in self.agents.items():
            if agent.status in ["stopped", "error"] and agent.error_count <= self.max_error_count:
                print(f"🔄 Auto-recovering {agent_name}...")
                self.restart_agent(agent_name)

    def save_health_report(self):
        """Save health report to file"""
        health_report = self.get_system_health()

        # Save to tasks directory
        report_file = os.path.join(self.tasks_dir, "health_report.json")
        with open(report_file, "w") as f:
            json.dump(health_report, f, indent=2, default=str)

        # Update shared status
        status_file = os.path.join(self.tasks_dir, "shared_status.txt")
        with open(status_file, "w") as f:
            f.write("=== Agent Status Dashboard ===\n")
            f.write(f"Updated: {datetime.now().strftime('%a %b %d %H:%M:%S %Z %Y')}\n")
            f.write(f"System Status: {health_report['system_status'].upper()}\n")
            f.write(f"Health Score: {health_report['average_health_score']:.2f}\n\n")

            for agent_name, agent_data in health_report["agents"].items():
                emoji = "✅" if agent_data["status"] == "active" else "❌"
                f.write(
                    f"{emoji} {agent_name}: {agent_data['status'].upper()} (Health: {agent_data['health_score']:.2f})\n"
                )

            f.write("\nConnection commands:\n")
            for agent_name in self.expected_agents:
                f.write(f"  tmux attach -t {agent_name}\n")

    def monitor_loop(self):
        """Main monitoring loop"""
        print("🔍 Agent Health Monitor starting...")
        print(f"Monitoring interval: {self.monitoring_interval} seconds")

        while True:
            try:
                # Update agent status
                self.update_agent_status()

                # Auto-recover failed agents
                self.auto_recover_failed_agents()

                # Save health report
                self.save_health_report()

                # Display summary
                health = self.get_system_health()
                print(
                    f"\n📊 System Health: {health['system_status'].upper()} "
                    f"({health['active_agents']}/{health['total_agents']} agents active)"
                )

                # Wait for next cycle
                time.sleep(self.monitoring_interval)

            except KeyboardInterrupt:
                print("\n🛑 Health monitor stopped by user")
                break
            except Exception as e:
                print(f"❌ Monitor error: {e}")
                time.sleep(10)


def main():
    """Main entry point"""
    monitor = AgentHealthMonitor()
    monitor.monitor_loop()


if __name__ == "__main__":
    main()
