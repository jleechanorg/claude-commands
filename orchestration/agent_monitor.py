#!/usr/bin/env python3
"""
Agent Monitoring Coordinator
A lightweight Python process that monitors orchestration agents using A2A protocol
Pings agents every 2 minutes and logs status to a central log file
"""

import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime

# Add orchestration directory to path
sys.path.insert(0, os.path.dirname(__file__))

# MessageBroker removed - using file-based A2A only

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class AgentMonitor:
    """Lightweight coordinator that monitors agents without LLM capabilities"""

    def __init__(self):
        self.running = False
        self.monitored_agents: dict[str, dict] = {}
        self.last_ping_time = 0
        self.ping_interval = 120  # 2 minutes

        # Setup logging
        self.setup_logging()

        self.logger.info("🤖 Agent Monitor starting up...")

    def setup_logging(self):
        """Setup centralized logging for agent monitoring"""
        self.logger = logger
        # Ensure log directory exists
        log_dir = "/tmp/orchestration_logs"
        os.makedirs(log_dir, exist_ok=True)

    # Redis/MessageBroker functionality removed - using file-based A2A only

    def discover_active_agents(self) -> set[str]:
        """Discover currently active agents from tmux sessions"""
        active_agents = set()

        try:
            # Get all tmux sessions
            result = subprocess.run(
                ["tmux", "list-sessions", "-F", "#{session_name}"],
                check=False, capture_output=True, text=True
            )

            if result.returncode == 0:
                sessions = result.stdout.strip().split('\n')
                for session in sessions:
                    if session.startswith('task-agent-'):
                        active_agents.add(session)

        except Exception as e:
            self.logger.error(f"Failed to discover tmux sessions: {e}")

        return active_agents

    def check_agent_workspace(self, agent_name: str) -> dict:
        """Check if agent workspace exists and get basic info"""
        workspace_path = f"agent_workspace_{agent_name}"

        workspace_info = {
            "workspace_exists": os.path.exists(workspace_path),
            "workspace_path": workspace_path,
            "last_modified": None
        }

        if workspace_info["workspace_exists"]:
            try:
                stat = os.stat(workspace_path)
                workspace_info["last_modified"] = datetime.fromtimestamp(stat.st_mtime)
            except OSError as e:
                self.logger.debug(f"Failed to stat workspace {workspace_path}: {e}")

        return workspace_info

    def check_agent_results(self, agent_name: str) -> dict:
        """Check agent completion status from result files"""
        result_file = f"/tmp/orchestration_results/{agent_name}_results.json"

        result_info = {
            "result_file_exists": os.path.exists(result_file),
            "status": "unknown",
            "completion_time": None
        }

        if result_info["result_file_exists"]:
            try:
                with open(result_file) as f:
                    result_data = json.load(f)
                    result_info["status"] = result_data.get("status", "unknown")
                    if "completion_time" in result_data:
                        result_info["completion_time"] = result_data["completion_time"]
            except Exception as e:
                self.logger.warning(f"Failed to read result file for {agent_name}: {e}")

        return result_info

    def get_agent_output_tail(self, agent_name: str, lines: int = 5) -> list[str]:
        """Get last few lines of agent tmux output"""
        try:
            result = subprocess.run(
                ["tmux", "capture-pane", "-t", agent_name, "-p", "-S", f"-{lines}"],
                check=False, capture_output=True, text=True
            )

            if result.returncode == 0:
                return result.stdout.strip().split('\n')
        except Exception as e:
            self.logger.debug(f"Failed to capture pane for {agent_name}: {e}")

        return []

    def ping_agent(self, agent_name: str) -> dict:
        """Ping an agent and collect comprehensive status"""
        ping_time = datetime.now()

        # Collect all agent information
        agent_status = {
            "agent_name": agent_name,
            "ping_time": ping_time.isoformat(),
            "tmux_active": False,
            "workspace_info": self.check_agent_workspace(agent_name),
            "result_info": self.check_agent_results(agent_name),
            "recent_output": [],
            "uptime_estimate": None
        }

        # Check if tmux session is active
        try:
            result = subprocess.run(
                ["tmux", "has-session", "-t", agent_name],
                check=False, capture_output=True
            )
            agent_status["tmux_active"] = result.returncode == 0
        except (subprocess.SubprocessError, OSError) as e:
            self.logger.debug(f"Failed to check tmux session {agent_name}: {e}")

        # Get recent output if tmux is active
        if agent_status["tmux_active"]:
            agent_status["recent_output"] = self.get_agent_output_tail(agent_name)

        # Estimate uptime from workspace modification time
        if agent_status["workspace_info"]["last_modified"]:
            uptime = ping_time - agent_status["workspace_info"]["last_modified"]
            agent_status["uptime_estimate"] = str(uptime)

        return agent_status

    def ping_all_agents(self):
        """Ping all discovered agents and log status"""
        self.logger.info("🔍 Pinging all active agents...")

        # Discover current agents
        active_agents = self.discover_active_agents()

        if not active_agents:
            self.logger.info("📭 No active agents found")
            return

        self.logger.info(f"👥 Found {len(active_agents)} active agents: {', '.join(active_agents)}")

        # Ping each agent
        for agent_name in active_agents:
            try:
                status = self.ping_agent(agent_name)
                self.log_agent_status(status)

                # Update our tracking
                self.monitored_agents[agent_name] = status

            except Exception as e:
                self.logger.error(f"❌ Failed to ping {agent_name}: {e}")

    def log_agent_status(self, status: dict):
        """Log detailed agent status"""
        agent_name = status["agent_name"]
        tmux_status = "🟢 Active" if status["tmux_active"] else "🔴 Inactive"

        # Determine overall status
        if status["result_info"]["status"] == "completed":
            overall_status = "✅ Completed"
        elif status["result_info"]["status"] == "failed":
            overall_status = "❌ Failed"
        elif status["tmux_active"]:
            overall_status = "🔄 Working"
        else:
            overall_status = "❓ Unknown"

        self.logger.info(f"📊 {agent_name}: {overall_status} | tmux: {tmux_status}")

        # Log recent activity if available
        recent_output = status.get("recent_output", [])
        if recent_output and len(recent_output) > 0:
            last_line = recent_output[-1].strip()
            if last_line:
                self.logger.info(f"📝 {agent_name} recent: {last_line}")

        # Log completion info
        if status["result_info"]["status"] in ["completed", "failed"]:
            self.logger.info(f"🏁 {agent_name} finished with status: {status['result_info']['status']}")

    def register_with_a2a(self):
        """A2A registration handled via file-based protocol only"""
        self.logger.info("📡 File-based A2A monitoring active")

    def cleanup_completed_agents(self):
        """Clean up completed agents from monitoring"""
        completed = []
        for agent_name, status in self.monitored_agents.items():
            if status.get("result_info", {}).get("status") == "completed":
                if not status.get("tmux_active", True):  # Only cleanup if tmux is also done
                    completed.append(agent_name)

        for agent_name in completed:
            self.logger.info(f"🧹 Removing completed agent from monitoring: {agent_name}")
            del self.monitored_agents[agent_name]

    def run(self):
        """Main monitoring loop"""
        self.running = True
        self.register_with_a2a()

        self.logger.info("🚀 Agent Monitor started - pinging every 2 minutes")
        self.logger.info("📋 Monitor logs: tail -f /tmp/orchestration_logs/agent_monitor.log")

        try:
            while self.running:
                current_time = time.time()

                # Check if it's time to ping
                if current_time - self.last_ping_time >= self.ping_interval:
                    self.ping_all_agents()
                    self.cleanup_completed_agents()
                    self.last_ping_time = current_time

                # Sleep for 10 seconds between checks
                time.sleep(10)

        except KeyboardInterrupt:
            self.logger.info("🛑 Monitor shutdown requested")
        except Exception as e:
            self.logger.error(f"💥 Monitor error: {e}")
        finally:
            self.shutdown()

    def shutdown(self):
        """Shutdown monitor gracefully"""
        self.logger.info("👋 Agent Monitor shutting down...")
        self.running = False
        # File-based A2A cleanup handled automatically via filesystem


def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # Run once and exit (useful for testing)
        monitor = AgentMonitor()
        monitor.ping_all_agents()
        return

    # Run continuous monitoring
    monitor = AgentMonitor()
    monitor.run()


if __name__ == "__main__":
    main()
