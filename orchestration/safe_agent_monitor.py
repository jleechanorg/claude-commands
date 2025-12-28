#!/usr/bin/env python3
"""
Safe Agent Monitor - Read-only monitoring without accidental input
Prevents SIGINT and other keyboard interruptions during agent monitoring
"""

import argparse
import subprocess
import time
from datetime import datetime


class SafeAgentMonitor:
    """Monitor agent progress without risk of keyboard input interference"""

    def __init__(self):
        self.monitored_agents = []

    def list_agents(self):
        """List all running agent tmux sessions"""
        try:
            result = subprocess.run(["tmux", "ls"], check=False, capture_output=True, text=True)
            if result.returncode == 0:
                sessions = []
                for line in result.stdout.strip().split("\n"):
                    if "agent" in line:
                        session_name = line.split(":")[0]
                        sessions.append(session_name)
                return sessions
            return []
        except:
            return []

    def capture_pane(self, session_name, lines=50):
        """Safely capture tmux pane content - READ ONLY"""
        try:
            # ONLY use capture-pane, NEVER send-keys
            cmd = ["tmux", "capture-pane", "-t", session_name, "-p"]
            result = subprocess.run(cmd, check=False, capture_output=True, text=True)

            if result.returncode == 0:
                output = result.stdout.strip().split("\n")
                return output[-lines:] if len(output) > lines else output
            return [f"Error: Could not capture pane for {session_name}"]
        except Exception as e:
            return [f"Error: {str(e)}"]

    def monitor_agent(self, session_name, continuous=False, interval=5):
        """Monitor a specific agent safely"""
        print(f"📺 Monitoring {session_name} (READ-ONLY MODE)")
        print("=" * 60)

        if continuous:
            print(f"Continuous monitoring every {interval}s. Press Ctrl+C to stop.")
            print("⚠️  This monitor is READ-ONLY - no keyboard input will be sent to agent")
            print("=" * 60)

        try:
            while True:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"\n[{timestamp}] Latest output:")
                print("-" * 60)

                lines = self.capture_pane(session_name)
                for line in lines:
                    if line.strip():  # Only print non-empty lines
                        print(line)

                if not continuous:
                    break

                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\n✅ Monitoring stopped safely (agent still running)")

    def check_agent_status(self, session_name):
        """Check if agent is still running"""
        sessions = self.list_agents()
        return session_name in sessions

    def monitor_all(self, interval=10):
        """Monitor all agents with status updates"""
        print("📊 Monitoring All Agents (READ-ONLY)")
        print("=" * 60)

        try:
            while True:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                sessions = self.list_agents()

                print(f"\n[{timestamp}] Active agents: {len(sessions)}")

                for session in sessions:
                    print(f"\n🤖 {session}:")
                    # Get last 5 lines from each agent
                    lines = self.capture_pane(session, lines=5)
                    for line in lines[-3:]:  # Show last 3 lines
                        if line.strip():
                            print(f"   {line[:80]}...")  # Truncate long lines

                print(f"\nNext update in {interval}s... (Ctrl+C to stop)")
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\n✅ Monitoring stopped (all agents still running)")


def main():
    parser = argparse.ArgumentParser(description="Safe agent monitoring without keyboard interference")
    parser.add_argument("agent", nargs="?", help="Agent session name to monitor")
    parser.add_argument("-a", "--all", action="store_true", help="Monitor all agents")
    parser.add_argument("-l", "--list", action="store_true", help="List running agents")
    parser.add_argument("-c", "--continuous", action="store_true", help="Continuous monitoring")
    parser.add_argument("-i", "--interval", type=int, default=5, help="Update interval in seconds")
    parser.add_argument("-n", "--lines", type=int, default=50, help="Number of lines to show")

    args = parser.parse_args()
    monitor = SafeAgentMonitor()

    if args.list:
        agents = monitor.list_agents()
        if agents:
            print("🤖 Running agents:")
            for agent in agents:
                status = "✅ Active" if monitor.check_agent_status(agent) else "❌ Inactive"
                print(f"  - {agent} {status}")
        else:
            print("No agents currently running")

    elif args.all:
        monitor.monitor_all(interval=args.interval)

    elif args.agent:
        if monitor.check_agent_status(args.agent):
            monitor.monitor_agent(args.agent, continuous=args.continuous, interval=args.interval)
        else:
            print(f"❌ Agent '{args.agent}' not found")
            print("\nAvailable agents:")
            for agent in monitor.list_agents():
                print(f"  - {agent}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
