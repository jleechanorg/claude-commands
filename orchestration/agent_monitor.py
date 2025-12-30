#!/usr/bin/env python3
"""
Agent Monitoring Coordinator
A lightweight Python process that monitors orchestration agents using A2A protocol
Pings agents every 2 minutes and logs status to a central log file
Enhanced with converge agent restart capabilities
"""

import json
import logging
import os
import re
import shlex
import subprocess
import sys
import time
from datetime import datetime, timedelta

# Add orchestration directory to path
sys.path.insert(0, os.path.dirname(__file__))

# MessageBroker removed - using file-based A2A only

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


class ConvergeAgentRestarter:
    """Handles detection and restart of stuck converge agents"""

    def __init__(self, logger):
        self.logger = logger
        self.restart_attempts = {}  # Track restart attempts per agent
        self.last_activity = {}  # Track last activity per agent
        self.max_restart_attempts = 3
        self.stuck_threshold = timedelta(minutes=10)

    def is_converge_agent(self, agent_name: str) -> bool:
        """Check if agent is a converge agent based on workspace analysis"""
        workspace_path = os.path.join("orchestration", "agent_workspaces", f"agent_workspace_{agent_name}")

        # Check for converge-specific indicators
        indicators = [
            f"{workspace_path}/converge_state.json",
            f"{workspace_path}/convergence_progress.log",
            f"{workspace_path}/.converge_marker",
        ]

        return any(os.path.exists(indicator) for indicator in indicators)

    def detect_stuck_agent(self, agent_name: str, status: dict) -> bool:
        """Detect if a converge agent appears stuck"""
        if not self.is_converge_agent(agent_name):
            return False

        current_time = datetime.now()

        # Check for signs of activity
        workspace_modified = status.get("workspace_info", {}).get("last_modified")
        recent_output = status.get("recent_output", [])

        # Determine last activity time
        last_activity = None
        if workspace_modified:
            last_activity = workspace_modified

        # Initialize tracking if first encounter
        if agent_name not in self.last_activity:
            # For first encounter, use workspace modification time if available
            if workspace_modified:
                self.last_activity[agent_name] = workspace_modified
            else:
                self.last_activity[agent_name] = current_time
                return False  # Can't determine stuck status on first encounter without workspace info

        # Check if agent has been inactive too long
        if last_activity:
            time_since_activity = current_time - last_activity
        else:
            time_since_activity = current_time - self.last_activity[agent_name]

        self.logger.debug(f"Agent {agent_name} - Time since activity: {time_since_activity.total_seconds()} seconds")

        # Update last activity if we see recent changes
        if workspace_modified and workspace_modified > self.last_activity[agent_name]:
            self.last_activity[agent_name] = workspace_modified
            return False

        # Check for progress indicators in recent output
        if recent_output:
            progress_indicators = [
                "completing",
                "progress",
                "processing",
                "currently working",
                "converging",
                "analyzing",
                "generating",
                "updating",
                "creating",
                "building",
            ]

            # Exclude stuck indicators
            stuck_indicators = ["stuck", "waiting", "error", "failed", "timeout", "hanging"]

            for line in recent_output:
                line_lower = line.lower()

                # Skip lines that indicate stuck state
                if any(stuck_word in line_lower for stuck_word in stuck_indicators):
                    continue

                # Check for actual progress indicators
                if any(indicator in line_lower for indicator in progress_indicators):
                    self.last_activity[agent_name] = current_time
                    return False

        # Agent appears stuck if no activity for threshold period
        is_stuck = time_since_activity > self.stuck_threshold

        if is_stuck:
            self.logger.warning(f"🚨 Converge agent {agent_name} appears stuck (inactive for {time_since_activity})")

        return is_stuck

    def check_and_restart(self, agent_name: str) -> bool:
        """Check if a converge agent is stuck and restart if needed"""
        # Build agent status from available info
        last_modified = self.get_workspace_modified_time(agent_name)
        self.logger.info(f"🕐 Workspace last modified for {agent_name}: {last_modified}")

        status = {"workspace_info": {"last_modified": last_modified}, "recent_output": []}

        # Check if stuck
        if self.detect_stuck_agent(agent_name, status):
            self.logger.warning(f"⚠️ Agent {agent_name} appears to be stuck!")
            return self.restart_stuck_agent(agent_name)
        else:
            self.logger.info(f"Agent {agent_name} considered still active")

        return False

    def get_workspace_modified_time(self, agent_name: str):
        """Get the last modified time of agent workspace"""
        # Validate agent name first
        if not self._validate_agent_name(agent_name):
            self.logger.warning(f"Invalid agent name format in get_workspace_modified_time: {agent_name}")
            return None

        # Check various possible workspace locations
        workspace_paths = [
            os.path.join("orchestration", "agent_workspaces", f"agent_workspace_{agent_name}"),
            os.path.expanduser(f"~/projects/worldarchitect.ai/worktree_human/{agent_name}"),
        ]

        for path in workspace_paths:
            expanded_path = os.path.expanduser(path)
            if os.path.exists(expanded_path):
                try:
                    # Find most recently modified file
                    latest_time = 0
                    for root, dirs, files in os.walk(expanded_path):
                        # Skip hidden and cache directories
                        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__" and d != "venv"]
                        for file in files:
                            if not file.startswith("."):
                                file_path = os.path.join(root, file)
                                try:
                                    mtime = os.path.getmtime(file_path)
                                    if mtime > latest_time:
                                        latest_time = mtime
                                except OSError:
                                    pass

                    if latest_time > 0:
                        return datetime.fromtimestamp(latest_time)
                except Exception as e:
                    self.logger.debug(f"Error checking workspace {path}: {e}")

        return None

    def _validate_agent_name(self, agent_name: str) -> bool:
        """Validate agent name to prevent path traversal"""
        # Basic checks
        if not agent_name or len(agent_name) > 100:
            return False

        # Only allow alphanumeric, hyphens, and underscores
        safe_pattern = r"^[a-zA-Z0-9_-]+$"
        return bool(re.match(safe_pattern, agent_name))

    def _is_safe_command(self, cmd: str) -> bool:
        """Validate command against safe patterns"""
        cmd_clean = cmd.strip()

        # Basic validation
        if not cmd_clean or len(cmd_clean) > 1000:
            return False

        # Check for dangerous characters that could enable command injection
        dangerous_chars = [";", "|", "&", "$", "`", "$(", "&&", "||", ">", "<", ">>", "\n", "\r"]
        if any(char in cmd_clean for char in dangerous_chars):
            return False

        # Check against allowed command patterns - more strict validation
        safe_patterns = [
            r"^/converge\b[^;|&$`<>\n\r]*$",
            r"^/orch\b[^;|&$`<>\n\r]*$",
            r"^/execute\b[^;|&$`<>\n\r]*$",
            r"^/plan\b[^;|&$`<>\n\r]*$",
            r"^/test\b[^;|&$`<>\n\r]*$",
        ]
        return any(re.match(pattern, cmd_clean) for pattern in safe_patterns)

    def _get_fallback_command(self, agent_name: str) -> str:
        """Generate safe fallback command"""
        if "converge" in agent_name.lower():
            return "/converge Resume previous convergence task"
        return "/orch Resume task execution"

    def get_original_command(self, agent_name: str) -> str:
        """Extract original command from agent workspace with security validation"""
        # Validate agent name first
        if not self._validate_agent_name(agent_name):
            self.logger.warning(f"Invalid agent name format: {agent_name}")
            return self._get_fallback_command(agent_name)

        # Construct safe workspace path
        workspace_path = os.path.join("orchestration", "agent_workspaces", f"agent_workspace_{agent_name}")
        command_file = os.path.join(workspace_path, "original_command.txt")

        # Verify path is within expected workspace
        abs_command_file = os.path.abspath(command_file)
        expected_prefix = os.path.abspath(workspace_path)
        if not abs_command_file.startswith(expected_prefix):
            self.logger.error(f"Path traversal attempt detected for {agent_name}")
            return self._get_fallback_command(agent_name)

        if os.path.exists(command_file):
            try:
                with open(command_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()

                # Validate command content
                if content and self._is_safe_command(content):
                    return content
                else:
                    self.logger.warning(f"Unsafe command content detected for {agent_name}: {content}")
                    return self._get_fallback_command(agent_name)

            except Exception as e:
                self.logger.warning(f"Failed to read command file for {agent_name}: {e}")

        return self._get_fallback_command(agent_name)

    def restart_converge_agent(self, agent_name: str) -> bool:
        """Restart a stuck converge agent"""
        # Validate agent name first
        if not self._validate_agent_name(agent_name):
            self.logger.error(f"Invalid agent name format in restart_converge_agent: {agent_name}")
            return False

        # Check restart attempt limits
        attempts = self.restart_attempts.get(agent_name, 0)
        if attempts >= self.max_restart_attempts:
            self.logger.error(f"❌ Agent {agent_name} exceeded max restart attempts ({attempts})")
            return False

        self.logger.info(f"🔄 Restarting stuck converge agent: {agent_name}")

        try:
            # Kill existing tmux session
            subprocess.run(["tmux", "kill-session", "-t", agent_name], check=False, capture_output=True)

            # Get original command (already validated)
            original_cmd = self.get_original_command(agent_name)

            # Validate the retrieved command for extra safety
            if not self._is_safe_command(original_cmd):
                self.logger.error(f"Unsafe command detected for {agent_name}: {original_cmd}")
                return False

            # Create enhanced converge prompt for autonomous execution
            if "/converge" in original_cmd or "converge" in agent_name.lower():
                enhanced_prompt = (
                    f"{original_cmd} - Continue autonomous execution until all goals are met. "
                    f"Do not stop for approval. Work continuously until complete convergence achieved."
                )
            else:
                enhanced_prompt = original_cmd

            # Create new tmux session with same name (agent_name already validated)
            # Ensure the working directory path is safe
            work_dir = os.path.expanduser("~/projects/worldarchitect.ai/worktree_human")
            work_dir = os.path.abspath(work_dir)  # Get absolute path

            # Log security event
            self.logger.info(
                f"🔐 Security: Restarting validated agent {agent_name} with command: {enhanced_prompt[:100]}..."
            )

            tmux_cmd = [
                "tmux",
                "new-session",
                "-d",
                "-s",
                agent_name,
                "bash",
                "-c",
                f"cd {shlex.quote(work_dir)} && "
                f'source "$HOME/.bashrc" 2>/dev/null || true && '
                f"echo 'Restarting agent due to inactivity...' && "
                f"echo 'Enhanced prompt: {shlex.quote(enhanced_prompt)}' && "
                f"claude --model sonnet {shlex.quote(enhanced_prompt)}",
            ]

            result = subprocess.run(tmux_cmd, check=True, capture_output=True, text=True, timeout=30)

            # Update restart tracking
            self.restart_attempts[agent_name] = attempts + 1
            self.last_activity[agent_name] = datetime.now()

            self.logger.info(
                f"✅ Agent {agent_name} restarted successfully "
                f"(attempt {self.restart_attempts[agent_name]}/{self.max_restart_attempts})"
            )

            return True

        except subprocess.TimeoutExpired:
            self.logger.error(f"⏰ Timeout restarting agent {agent_name}")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"💥 Failed to restart agent {agent_name}: {e}")
        except Exception as e:
            self.logger.error(f"🚨 Unexpected error restarting {agent_name}: {e}")

        return False


class AgentMonitor:
    """Lightweight coordinator that monitors agents without LLM capabilities"""

    def __init__(self):
        self.running = False
        self.monitored_agents: dict[str, dict] = {}
        self.last_ping_time = 0
        self.ping_interval = 120  # 2 minutes

        # Setup logging
        self.setup_logging()

        # Initialize converge agent restarter
        self.restarter = ConvergeAgentRestarter(self.logger)

        self.logger.info("🤖 Agent Monitor starting up with converge restart capabilities...")

    def setup_logging(self):
        """Setup centralized logging for agent monitoring"""
        self.logger = logger
        # Ensure log directory exists
        log_dir = "/tmp/orchestration_logs"
        os.makedirs(log_dir, exist_ok=True)

    def _validate_agent_name(self, agent_name: str) -> bool:
        """Validate agent name to prevent path traversal (AgentMonitor copy)"""
        # Basic checks
        if not agent_name or len(agent_name) > 100:
            return False

        # Only allow alphanumeric, hyphens, and underscores
        safe_pattern = r"^[a-zA-Z0-9_-]+$"
        return bool(re.match(safe_pattern, agent_name))

    # Redis/MessageBroker functionality removed - using file-based A2A only

    def discover_active_agents(self) -> set[str]:
        """Discover currently active agents from tmux sessions"""
        active_agents = set()

        try:
            # Get all tmux sessions
            result = subprocess.run(
                ["tmux", "list-sessions", "-F", "#{session_name}"],
                check=False,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                sessions = result.stdout.strip().split("\n")
                for session in sessions:
                    if session.startswith("task-agent-") and self._validate_agent_name(session):
                        active_agents.add(session)
                    elif session.startswith("task-agent-"):
                        self.logger.warning(f"🔐 Security: Skipping invalid agent name: {session}")

        except Exception as e:
            self.logger.error(f"Failed to discover tmux sessions: {e}")

        return active_agents

    def check_agent_workspace(self, agent_name: str) -> dict:
        """Check if agent workspace exists and get basic info"""
        # Validate agent name first
        if not self._validate_agent_name(agent_name):
            self.logger.warning(f"Invalid agent name format in check_agent_workspace: {agent_name}")
            return {
                "workspace_exists": False,
                "workspace_path": None,
                "last_modified": None,
            }

        workspace_path = os.path.join("orchestration", "agent_workspaces", f"agent_workspace_{agent_name}")

        workspace_info = {
            "workspace_exists": os.path.exists(workspace_path),
            "workspace_path": workspace_path,
            "last_modified": None,
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
        # Validate agent name first
        if not self._validate_agent_name(agent_name):
            self.logger.warning(f"Invalid agent name format in check_agent_results: {agent_name}")
            return {
                "result_file_exists": False,
                "status": "invalid_name",
                "completion_time": None,
            }

        result_file = f"/tmp/orchestration_results/{agent_name}_results.json"

        result_info = {
            "result_file_exists": os.path.exists(result_file),
            "status": "unknown",
            "completion_time": None,
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
        # Validate agent name first
        if not self._validate_agent_name(agent_name):
            self.logger.warning(f"Invalid agent name format in get_agent_output_tail: {agent_name}")
            return []

        try:
            result = subprocess.run(
                ["tmux", "capture-pane", "-t", agent_name, "-p", "-S", f"-{lines}"],
                check=False,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                return result.stdout.strip().split("\n")
        except Exception as e:
            self.logger.debug(f"Failed to capture pane for {agent_name}: {e}")

        return []

    def ping_agent(self, agent_name: str) -> dict:
        """Ping an agent and collect comprehensive status"""
        # Validate agent name first
        if not self._validate_agent_name(agent_name):
            self.logger.warning(f"Invalid agent name format in ping_agent: {agent_name}")
            return {
                "agent_name": agent_name,
                "ping_time": datetime.now().isoformat(),
                "tmux_active": False,
                "workspace_info": {"workspace_exists": False},
                "result_info": {"status": "invalid_name"},
                "recent_output": [],
                "uptime_estimate": None,
                "validation_error": "Invalid agent name format",
            }

        ping_time = datetime.now()

        # Collect all agent information
        agent_status = {
            "agent_name": agent_name,
            "ping_time": ping_time.isoformat(),
            "tmux_active": False,
            "workspace_info": self.check_agent_workspace(agent_name),
            "result_info": self.check_agent_results(agent_name),
            "recent_output": [],
            "uptime_estimate": None,
        }

        # Check if tmux session is active
        try:
            # Agent name already validated, safe to use in command
            result = subprocess.run(
                ["tmux", "has-session", "-t", agent_name],
                check=False,
                capture_output=True,
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

                # Check if converge agent needs restart
                if status.get("tmux_active", False) and self.restarter.detect_stuck_agent(agent_name, status):
                    self.logger.warning(f"🔄 Attempting to restart stuck agent: {agent_name}")
                    restart_success = self.restarter.restart_converge_agent(agent_name)

                    if restart_success:
                        # Update status to reflect restart
                        status["restarted"] = True
                        status["restart_time"] = datetime.now().isoformat()

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

                    # Check for stuck converge agents and restart if needed
                    for agent_name in list(self.monitored_agents.keys()):
                        if (
                            "converge" in agent_name.lower()
                            or "conver" in agent_name.lower()
                            or "compre" in agent_name.lower()
                        ):
                            self.logger.info(f"🔍 Checking {agent_name} for stuck state...")
                            if self.restarter.check_and_restart(agent_name):
                                self.logger.info(f"✅ Successfully restarted {agent_name}")
                            else:
                                self.logger.debug(f"Agent {agent_name} is still active")

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
