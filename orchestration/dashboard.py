#!/usr/bin/env python3
"""
Real-time Orchestration Dashboard
Provides a comprehensive view of the multi-agent system
"""

import json
import os
import subprocess
import time
from datetime import datetime, timedelta
from typing import Any


class OrchestrationDashboard:
    """Real-time dashboard for agent orchestration system"""

    def __init__(self, orchestration_dir: str = None):
        self.orchestration_dir = orchestration_dir or os.path.dirname(__file__)
        self.tasks_dir = os.path.join(self.orchestration_dir, "tasks")
        self.refresh_interval = 5  # seconds

    def get_tmux_session_info(self) -> dict[str, Any]:
        """Get detailed tmux session information"""
        sessions = {}

        try:
            # Get list of sessions
            result = subprocess.run(["tmux", "list-sessions"], check=False, capture_output=True, text=True)

            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if line and ":" in line:
                        session_name = line.split(":")[0]

                        # Get session details
                        details = {}

                        # Get creation time
                        create_result = subprocess.run(
                            [
                                "tmux",
                                "display-message",
                                "-t",
                                session_name,
                                "-p",
                                "#{session_created}",
                            ],
                            check=False,
                            capture_output=True,
                            text=True,
                        )

                        if create_result.returncode == 0:
                            created_timestamp = int(create_result.stdout.strip())
                            details["created"] = datetime.fromtimestamp(created_timestamp)
                            details["uptime"] = datetime.now() - details["created"]

                        # Get recent activity
                        activity_result = subprocess.run(
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

                        if activity_result.returncode == 0:
                            activity_timestamp = int(activity_result.stdout.strip())
                            details["last_activity"] = datetime.fromtimestamp(activity_timestamp)

                        # Get recent output
                        output_result = subprocess.run(
                            [
                                "tmux",
                                "capture-pane",
                                "-t",
                                session_name,
                                "-p",
                                "-S",
                                "-20",
                            ],
                            check=False,
                            capture_output=True,
                            text=True,
                        )

                        if output_result.returncode == 0:
                            details["recent_output"] = output_result.stdout.strip()

                        sessions[session_name] = details

        except Exception as e:
            print(f"Error getting tmux info: {e}")

        return sessions

    def load_health_report(self) -> dict[str, Any]:
        """Load health report if available"""
        health_file = os.path.join(self.tasks_dir, "health_report.json")

        if os.path.exists(health_file):
            try:
                with open(health_file) as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading health report: {e}")

        return {"system_status": "unknown", "agents": {}}

    def load_task_report(self) -> dict[str, Any]:
        """Load task report if available"""
        task_file = os.path.join(self.tasks_dir, "task_report.json")

        if os.path.exists(task_file):
            try:
                with open(task_file) as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading task report: {e}")

        return {"total_tasks": 0, "agent_workload": {}}

    def get_task_files_status(self) -> dict[str, int]:
        """Get status of task files"""
        # No static task files - check orchestration/results/ for completed tasks
        task_files = []
        status = {}

        for filename in task_files:
            filepath = os.path.join(self.tasks_dir, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath) as f:
                        lines = f.readlines()
                        status[filename] = len([line for line in lines if line.strip()])
                except Exception:
                    status[filename] = 0
            else:
                status[filename] = 0

        return status

    def get_recent_pr_activity(self) -> list[dict[str, Any]]:
        """Get recent PR activity from agents"""
        try:
            # Get recent PRs
            result = subprocess.run(
                [
                    "gh",
                    "pr",
                    "list",
                    "--limit",
                    "5",
                    "--json",
                    "number,title,author,createdAt,state",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                return json.loads(result.stdout)
        except Exception as e:
            print(f"Error getting PR activity: {e}")

        return []

    def format_uptime(self, uptime: timedelta) -> str:
        """Format uptime duration"""
        total_seconds = int(uptime.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if hours > 0:
            return f"{hours}h {minutes}m"
        if minutes > 0:
            return f"{minutes}m {seconds}s"
        return f"{seconds}s"

    def format_time_ago(self, timestamp: datetime) -> str:
        """Format time since timestamp"""
        delta = datetime.now() - timestamp
        return self.format_uptime(delta) + " ago"

    def render_dashboard(self):
        """Render the full dashboard"""
        # Clear screen
        os.system("clear")

        # Header
        print("=" * 80)
        print("🤖 REAL MULTI-AGENT ORCHESTRATION DASHBOARD")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        # System Health
        health_report = self.load_health_report()
        system_status = health_report.get("system_status", "unknown")

        status_emoji = {
            "healthy": "🟢",
            "degraded": "🟡",
            "critical": "🔴",
            "unknown": "⚪",
        }

        print(f"\n🏥 SYSTEM HEALTH: {status_emoji.get(system_status, '⚪')} {system_status.upper()}")

        if "average_health_score" in health_report:
            print(f"   Health Score: {health_report['average_health_score']:.2f}/1.0")

        # Agent Status
        print("\n🤖 AGENT STATUS:")
        sessions = self.get_tmux_session_info()

        # Only task-coordinator is predefined - all others are dynamic
        expected_agents = [("task-coordinator", "🎯 Task Coordinator", "Task coordination")]

        for agent_name, display_name, _description in expected_agents:
            if agent_name in sessions:
                session_info = sessions[agent_name]
                uptime = session_info.get("uptime", timedelta(0))
                last_activity = session_info.get("last_activity", datetime.now())

                print(f"   {display_name}: ✅ ACTIVE (up {self.format_uptime(uptime)})")
                print(f"      Last activity: {self.format_time_ago(last_activity)}")

                # Show recent output snippet
                recent_output = session_info.get("recent_output", "")
                if recent_output:
                    # Get last non-empty line
                    lines = [line.strip() for line in recent_output.split("\n") if line.strip()]
                    if lines:
                        last_line = lines[-1][:60]  # Truncate long lines
                        print(f"      Recent: {last_line}")

                # Show health score if available
                if agent_name in health_report.get("agents", {}):
                    health_score = health_report["agents"][agent_name]["health_score"]
                    print(f"      Health: {health_score:.2f}/1.0")
            else:
                print(f"   {display_name}: ❌ STOPPED")

        # Task Status
        print("\n📋 TASK STATUS:")
        task_report = self.load_task_report()
        task_files = self.get_task_files_status()

        if task_report.get("total_tasks", 0) > 0:
            print(f"   Total tasks: {task_report['total_tasks']}")
            print(f"   Pending: {task_report.get('pending_tasks', 0)}")
            print(f"   Assigned: {task_report.get('assigned_tasks', 0)}")
            print(f"   Completed: {task_report.get('completed_tasks', 0)}")
            print(f"   Completion rate: {task_report.get('completion_rate', 0):.1%}")

        # Agent workload
        print("\n⚖️  AGENT WORKLOAD:")
        for filename, count in task_files.items():
            agent_type = filename.replace("_tasks.txt", "").title()
            print(f"   {agent_type}: {count} pending tasks")

        # Recent PR Activity
        print("\n🔀 RECENT PR ACTIVITY:")
        recent_prs = self.get_recent_pr_activity()

        if recent_prs:
            for pr in recent_prs[:3]:  # Show top 3
                created = datetime.fromisoformat(pr["createdAt"].replace("Z", "+00:00"))
                age = self.format_time_ago(created)
                state_emoji = "🟢" if pr["state"] == "OPEN" else "🔴"
                print(f"   {state_emoji} PR #{pr['number']}: {pr['title'][:50]}...")
                print(f"      By {pr['author']['login']} - {age}")
        else:
            print("   No recent PR activity")

        # Quick Commands
        print("\n🎮 QUICK COMMANDS:")
        print("   Agent connections:")
        for agent_name, display_name, _ in expected_agents:
            if agent_name in sessions:
                print(f"      tmux attach -t {agent_name}")

        print("   System control:")
        print("      ./orchestration/start_system.sh status")
        print("      ./orchestration/start_system.sh stop")
        print("      ./orchestration/monitor_agents.sh")

        # System Resources
        print("\n💾 SYSTEM RESOURCES:")

        # Check Redis
        try:
            redis_result = subprocess.run(["redis-cli", "ping"], check=False, capture_output=True, text=True)
            redis_status = "🟢 ONLINE" if redis_result.returncode == 0 else "🔴 OFFLINE"
        except:
            redis_status = "🔴 OFFLINE"

        print(f"   Redis: {redis_status}")

        # Check disk usage for tasks directory
        try:
            disk_usage = subprocess.run(
                ["du", "-sh", self.tasks_dir],
                check=False,
                capture_output=True,
                text=True,
            )
            if disk_usage.returncode == 0:
                size = disk_usage.stdout.split()[0]
                print(f"   Tasks directory: {size}")
        except (subprocess.SubprocessError, OSError, FileNotFoundError):
            pass

        print(f"\n{'=' * 80}")
        print(f"Dashboard refreshes every {self.refresh_interval}s | Press Ctrl+C to exit")

    def run_dashboard(self):
        """Run the dashboard in a loop"""
        try:
            while True:
                self.render_dashboard()
                time.sleep(self.refresh_interval)
        except KeyboardInterrupt:
            print("\n\n🛑 Dashboard stopped by user")
            print("Thanks for using the orchestration dashboard!")


def main():
    """Main entry point"""
    dashboard = OrchestrationDashboard()
    dashboard.run_dashboard()


if __name__ == "__main__":
    main()
