#!/usr/bin/env python3
"""
A2A-Enhanced Task Dispatcher for Multi-Agent Orchestration
Handles dynamic agent creation with Agent-to-Agent communication support
"""

import glob
import json
import os
import re
import shlex
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any
from .a2a_integration import TaskPool, get_a2a_status
from .a2a_monitor import get_monitor
from .constants import (
    AGENT_SESSION_TIMEOUT_SECONDS,
    DEFAULT_MAX_CONCURRENT_AGENTS,
    TIMESTAMP_MODULO,
)

A2A_AVAILABLE = True

# Default Gemini model can be overridden via GEMINI_MODEL; prefer gemini-3-pro-preview by default
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3-pro-preview")
# Cursor model can be overridden via CURSOR_MODEL; default to composer-1 (configurable)
CURSOR_MODEL = os.environ.get("CURSOR_MODEL", "composer-1")

CLI_PROFILES = {
    "claude": {
        "binary": "claude",
        "display_name": "Claude",
        "generated_with": "🤖 Generated with [Claude Code](https://claude.ai/code)",
        "co_author": "Claude <noreply@anthropic.com>",
        "supports_continue": True,
        "conversation_dir": "~/.claude/conversations",
        "continue_flag": "--continue",
        "restart_env": "CLAUDE_RESTART",
        "command_template": (
            "{binary} --model sonnet -p @{prompt_file} "
            "--output-format stream-json --verbose{continue_flag} --dangerously-skip-permissions"
        ),
        "stdin_template": "/dev/null",
        "quote_prompt": False,
        "detection_keywords": ["claude", "anthropic"],
    },
    "codex": {
        "binary": "codex",
        "display_name": "Codex",
        "generated_with": "🤖 Generated with [Codex CLI](https://openai.com/)",
        "co_author": "Codex <noreply@openai.com>",
        "supports_continue": False,
        "conversation_dir": None,
        "continue_flag": "",
        "restart_env": "CODEX_RESTART",
        "command_template": "{binary} exec --yolo",
        "stdin_template": "{prompt_file}",
        "quote_prompt": True,
        "detection_keywords": [
            "codex",
            "codex exec",
            "codex cli",
            "use codex",
            "use the codex cli",
        ],
    },
    "gemini": {
        "binary": "gemini",
        "display_name": "Gemini",
        "generated_with": "🤖 Generated with [Gemini CLI](https://github.com/google-gemini/gemini-cli)",
        "co_author": "Gemini <noreply@google.com>",
        "supports_continue": False,
        "conversation_dir": None,
        "continue_flag": "",
        "restart_env": "GEMINI_RESTART",
        # Stick to configured GEMINI_MODEL (default gemini-3-pro-preview) unless overridden
        # YOLO mode enabled to allow file access outside workspace (user directive)
        # NOTE: Prompt must come via stdin (not -p flag which is deprecated and only appends to stdin)
        "command_template": f"{{binary}} -m {GEMINI_MODEL} --yolo",
        "stdin_template": "{prompt_file}",
        "quote_prompt": False,
        "detection_keywords": [
            "gemini",
            "gemini cli",
            "google ai",
            "use gemini",
            "use the gemini cli",
            "google gemini",
        ],
    },
    "cursor": {
        "binary": "cursor-agent",
        "display_name": "Cursor",
        "generated_with": "🤖 Generated with [Cursor Agent](https://www.cursor.com/)",
        "co_author": "Cursor <noreply@cursor.com>",
        "supports_continue": False,
        "conversation_dir": None,
        "continue_flag": "",
        "restart_env": "CURSOR_RESTART",
        # Cursor Agent CLI with -f (force) for non-interactive execution, configurable model
        "command_template": f"{{binary}} -f -p @{{prompt_file}} --model {CURSOR_MODEL} --output-format text",
        "stdin_template": "/dev/null",
        "quote_prompt": False,
        "detection_keywords": [
            "cursor",
            "cursor-agent",
            "cursor agent",
            "cursor cli",
            "use cursor",
            "use the cursor cli",
            "cursor ai",
        ],
    },
}


# Shared sanitization helper
def _sanitize_agent_token(name: str) -> str:
    """Return a filesystem-safe token for agent-derived file paths."""
    sanitized = re.sub(r"[^A-Za-z0-9_.-]", "_", name)
    return sanitized or "agent"


# Constraint system removed - using simple safety rules only

# Production safety limits - only counts actively working agents (not idle)
MAX_CONCURRENT_AGENTS = int(os.environ.get("MAX_CONCURRENT_AGENTS", DEFAULT_MAX_CONCURRENT_AGENTS))


# Shared configuration paths
def get_tmux_config_path():
    """Get the path to the tmux agent configuration file."""
    return os.path.join(os.path.dirname(__file__), "tmux-agent.conf")


def _kill_tmux_session_if_exists(name: str) -> None:
    """Ensure tmux session name is free; kill existing session if present."""
    try:
        # Tmux converts dots to underscores in session names
        name_tmux_safe = name.replace(".", "_")
        base = name.rstrip(".")
        base_tmux_safe = base.replace(".", "_")

        # Check all possible variants
        candidates = [
            name,
            f"{name}_",  # Original name
            base,
            f"{base}_",  # Without trailing dot
            name_tmux_safe,
            f"{name_tmux_safe}_",  # Tmux-safe version
            base_tmux_safe,
            f"{base_tmux_safe}_",  # Tmux-safe without trailing dot
        ]

        # Try direct has-session matches
        for candidate in candidates:
            check = subprocess.run(
                ["tmux", "has-session", "-t", candidate], check=False, capture_output=True, timeout=30
            )
            if check.returncode == 0:
                print(f"🧹 Killing existing tmux session {candidate} to allow reuse")
                subprocess.run(["tmux", "kill-session", "-t", candidate], check=False, capture_output=True, timeout=30)
    except Exception as exc:
        print(f"⚠️ Warning: unable to check/kill tmux session {name}: {exc}")


class TaskDispatcher:
    """Creates and manages dynamic agents for orchestration tasks"""

    def __init__(self, orchestration_dir: str = None):
        self.orchestration_dir = orchestration_dir or os.path.dirname(__file__)
        self.tasks_dir = os.path.join(self.orchestration_dir, "tasks")
        # Removed complex task management - system just creates agents on demand
        # Default agent capabilities - all agents have these basic capabilities
        # Dynamic capability registration can be added in the future via Redis/file system
        self.agent_capabilities = self._get_default_agent_capabilities()

        # LLM-driven enhancements - lazy loading to avoid subprocess overhead
        self._active_agents = None  # Will be loaded lazily when needed
        self._last_agent_check = 0  # Track when agents were last refreshed
        self.result_dir = "/tmp/orchestration_results"
        os.makedirs(self.result_dir, exist_ok=True)
        self._mock_claude_path = None

        # A2A Integration with enhanced robustness
        self.a2a_enabled = A2A_AVAILABLE
        if self.a2a_enabled:
            try:
                self.task_pool = TaskPool()
                print("A2A task broadcasting enabled")
            except Exception as e:
                print(f"A2A TaskPool initialization failed: {e}")
                print("Falling back to legacy mode")
                self.a2a_enabled = False
                self.task_pool = None
        else:
            self.task_pool = None
            print("A2A not available - running in legacy mode")

        # Basic safety rules only - no constraint system needed

        # All tasks are now dynamic - no static loading needed

    @property
    def active_agents(self) -> set:
        """Lazy loading property for active agents with 30-second caching."""
        current_time = time.time()
        # Cache for 30 seconds to avoid excessive subprocess calls
        if self._active_agents is None or (current_time - self._last_agent_check) > 30:
            self._active_agents = self._get_active_tmux_agents()
            self._last_agent_check = current_time
        return self._active_agents

    @active_agents.setter
    def active_agents(self, value: set):
        """Setter for active agents."""
        self._active_agents = value
        self._last_agent_check = time.time()

    def _get_active_tmux_agents(self) -> set:
        """Get set of actively working task-agent tmux sessions (not idle)."""
        try:
            # Check if tmux is available
            if shutil.which("tmux") is None:
                print("⚠️ 'tmux' command not found. Ensure tmux is installed and in PATH.")
                return set()
            result = subprocess.run(
                ["tmux", "list-sessions", "-F", "#{session_name}"],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
            if result.returncode != 0:
                return set()

            sessions = result.stdout.strip().split("\n")
            # Get all task-agent-* sessions
            all_agent_sessions = {s for s in sessions if s.startswith("task-agent-")}

            # Filter to only actively working agents (not idle)
            active_agents = set()
            idle_agents = set()

            for session in all_agent_sessions:
                if self._is_agent_actively_working(session):
                    active_agents.add(session)
                else:
                    idle_agents.add(session)

            # Print current status with breakdown
            total_count = len(all_agent_sessions)
            active_count = len(active_agents)
            idle_count = len(idle_agents)

            if total_count > 0:
                print(f"📊 Found {active_count} actively working agent(s) (limit: {MAX_CONCURRENT_AGENTS})")
                if idle_count > 0:
                    print(f"   Plus {idle_count} idle agent(s) (completed but monitoring)")

            return active_agents
        except Exception as e:
            print(f"⚠️ Error checking tmux sessions: {e}")
            return set()

    def _is_agent_actively_working(self, session_name: str) -> bool:
        """Check if an agent session is actively working or idle."""
        try:
            # Capture the last few lines of the tmux session to check status
            result = subprocess.run(
                ["tmux", "capture-pane", "-t", session_name, "-p"],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
            if result.returncode != 0:
                return False

            output = result.stdout.strip()

            # Check for completion indicators in the output
            completion_indicators = [
                "Agent completed successfully",
                "Agent execution completed. Session remains active for monitoring",
                "Session will auto-close in 1 hour",
                "Monitor with: tmux attach",
            ]

            # If any completion indicator is found, agent is idle
            for indicator in completion_indicators:
                if indicator in output:
                    return False

            # If no completion indicators found, assume agent is actively working
            return True

        except Exception:
            # If we can't determine, assume it's active to be safe
            return True

    def _get_default_agent_capabilities(self) -> dict:
        """Get default capabilities that all dynamic agents should have."""
        return {
            "task_execution": "Execute assigned development tasks",
            "command_acceptance": "Accept and process commands",
            "status_reporting": "Report task progress and completion status",
            "git_operations": "Perform git operations (commit, push, PR creation)",
            "development": "General software development capabilities",
            "testing": "Run and debug tests",
            "server_management": "Start/stop servers and services",
        }

    # =================== LLM-DRIVEN ENHANCEMENTS ===================

    def _check_existing_agents(self) -> set:
        """Check for existing tmux sessions and worktrees to avoid collisions."""
        existing = set()

        # Check tmux sessions
        try:
            if shutil.which("tmux") is None:
                return existing
            result = subprocess.run(
                ["tmux", "list-sessions", "-F", "#{session_name}"],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                existing.update(result.stdout.strip().split("\n"))
        except subprocess.SubprocessError:
            pass

        # Check worktrees
        try:
            # Look for workspaces in the orchestration directory
            workspace_pattern = os.path.join("orchestration", "agent_workspaces", "agent_workspace_*")
            workspaces = glob.glob(workspace_pattern)
            for ws in workspaces:
                ws_name = os.path.basename(ws)
                agent_name = ws_name.replace("agent_workspace_", "")
                existing.add(agent_name)
        except Exception as e:
            # Log specific error for debugging
            print(f"Warning: Failed to check existing workspaces due to error: {e}")

        return existing

    def _cleanup_stale_prompt_files(self, agent_name: str):
        """Clean up stale prompt files to prevent task reuse from previous runs."""
        try:
            # Clean up specific agent prompt file only - exact match to avoid deleting other agents' files
            agent_prompt_file = f"/tmp/agent_prompt_{agent_name}.txt"
            if os.path.exists(agent_prompt_file):
                os.remove(agent_prompt_file)
                print(f"🧹 Cleaned up stale prompt file: {agent_prompt_file}")
        except Exception as e:
            # Don't fail agent creation if cleanup fails
            print(f"⚠️ Warning: Could not clean up stale prompt files: {e}")

    def _generate_unique_name(self, base_name: str, task_description: str = "", role_suffix: str = "") -> str:
        """Generate meaningful agent name based on task content with collision detection."""

        # Extract meaningful components from task description
        task_suffix = ""
        if task_description:
            # Check for PR references first
            pr_match = re.search(r"(?:PR|pull request)\s*#?(\d+)", task_description, re.IGNORECASE)
            if pr_match:
                task_suffix = f"pr{pr_match.group(1)}"
            else:
                # Extract key action words for general tasks
                action_words = re.findall(
                    r"\b(?:implement|create|build|fix|test|deploy|analyze|review|update|add|remove|refactor|optimize)\b",
                    task_description.lower(),
                )
                if action_words:
                    # Use first action word + key object words
                    action = action_words[0]
                    # Extract key nouns/objects after cleaning
                    clean_desc = re.sub(r"[^a-zA-Z0-9\s]", "", task_description.lower())
                    words = [
                        word
                        for word in clean_desc.split()
                        if word
                        not in [
                            "the",
                            "and",
                            "or",
                            "for",
                            "with",
                            "in",
                            "on",
                            "at",
                            "to",
                            "from",
                            "by",
                            "of",
                            "a",
                            "an",
                        ]
                    ]

                    # Skip action word and take next meaningful words
                    content_words = [w for w in words if w != action][:2]
                    if content_words:
                        desc_part = "-".join(word[:6] for word in content_words)
                        task_suffix = f"{action}-{desc_part}"
                    else:
                        task_suffix = action
                else:
                    # Fallback to first few meaningful words
                    clean_desc = re.sub(r"[^a-zA-Z0-9\s]", "", task_description.lower())
                    words = [word for word in clean_desc.split() if len(word) > 2][:2]
                    if words:
                        task_suffix = "-".join(word[:6] for word in words)
                    else:
                        task_suffix = "task"

        # Limit task_suffix length for readability
        if len(task_suffix) > 20:
            task_suffix = task_suffix[:20]

        # Use microsecond precision for uniqueness only as fallback
        timestamp = int(time.time() * 1000000) % 10000  # 4 digits for brevity

        # Get existing agents
        existing = self._check_existing_agents()
        existing.update(self.active_agents)

        # Build candidate name
        if task_suffix:
            if role_suffix:
                candidate = f"{base_name}-{task_suffix}-{role_suffix}"
            else:
                candidate = f"{base_name}-{task_suffix}"
        else:
            # Fallback to timestamp-based
            if role_suffix:
                candidate = f"{base_name}-{role_suffix}-{timestamp}"
            else:
                candidate = f"{base_name}-{timestamp}"

        # If collision, add timestamp suffix
        original_candidate = candidate
        counter = 1
        while candidate in existing:
            if task_suffix:
                candidate = f"{original_candidate}-{timestamp}"
                if candidate in existing:
                    candidate = f"{original_candidate}-{timestamp}-{counter}"
                    counter += 1
            else:
                candidate = f"{original_candidate}-{counter}"
                counter += 1

        self.active_agents.add(candidate)
        return candidate

    def _extract_workspace_config(self, task_description: str):
        """Extract workspace configuration from task description if present.

        Looks for patterns like:
        - --workspace-name tmux-pr123
        - --workspace-root /path/to/.worktrees
        """

        workspace_config = {}

        # Extract workspace name
        workspace_name_match = re.search(r"--workspace-name\s+([^\s]+)", task_description)
        if workspace_name_match:
            workspace_config["workspace_name"] = workspace_name_match.group(1)

        # Extract workspace root
        workspace_root_match = re.search(r"--workspace-root\s+([^\s]+)", task_description)
        if workspace_root_match:
            workspace_config["workspace_root"] = workspace_root_match.group(1)

        # Extract PR number from workspace name if it follows tmux-pr pattern
        if "workspace_name" in workspace_config:
            pr_match = re.search(r"tmux-pr(\d+)", workspace_config["workspace_name"])
            if pr_match:
                workspace_config["pr_number"] = pr_match.group(1)

        return workspace_config if workspace_config else None

    def _detect_agent_cli(self, task_description: str, forced_cli: str | None = None) -> str:
        """
        Determine which CLI should be used for the agent.

        Args:
            task_description: The task description which may contain CLI preferences.
            forced_cli: If provided, forces the use of this CLI (e.g., from --fixpr-agent).
                Takes highest precedence over all other selection methods.

        Returns:
            The CLI name to use (e.g., 'claude', 'codex', 'gemini', 'cursor').

        Raises:
            ValueError: If an invalid forced_cli value is supplied.
            RuntimeError: If no CLI is available in PATH.

        Selection precedence (highest to lowest):
            1. forced_cli parameter
            2. --agent-cli flag in task_description
            3. Keyword detection (CLI profile detection_keywords / binary names)
            4. Auto-select if only one CLI is installed
            5. Default to 'claude' if multiple CLIs available
        """

        cli_flag = re.search(r"--agent-cli(?:=|\s+)(\w+)", task_description, re.IGNORECASE)

        # Hard override when explicitly provided by caller (e.g., --fixpr-agent)
        if forced_cli is not None:
            forced_cli = forced_cli.lower()
            if forced_cli not in CLI_PROFILES:
                raise ValueError(f"Invalid forced_cli: {forced_cli}. Must be one of {list(CLI_PROFILES.keys())}")

            if cli_flag:
                requested_cli = cli_flag.group(1).lower()
                if requested_cli != forced_cli:
                    print(f"⚠️ Forced CLI '{forced_cli}' overrides --agent-cli request for '{requested_cli}'.")

            return forced_cli

        # Explicit override via flag (--agent-cli codex) or (--agent-cli=codex)
        if cli_flag:
            requested_cli = cli_flag.group(1).lower()
            if requested_cli in CLI_PROFILES:
                return requested_cli

        task_lower = task_description.lower()

        # Keyword and binary-name detection sourced from CLI profiles
        for cli_name, profile in CLI_PROFILES.items():
            keywords = profile.get("detection_keywords", [])
            binary_name = profile.get("binary")

            if any(keyword and keyword.lower() in task_lower for keyword in keywords):
                return cli_name

            if binary_name:
                pattern = rf"\b{re.escape(binary_name.lower())}\b"
                if re.search(pattern, task_lower):
                    return cli_name

        # Auto-select an available CLI if only one is installed
        available_clis = []
        for cli_name, profile in CLI_PROFILES.items():
            cli_binary = profile.get("binary")
            if cli_binary and shutil.which(cli_binary):
                available_clis.append(cli_name)

        if len(available_clis) == 0:
            raise RuntimeError(
                "No agent CLI is available. Please install at least one supported CLI "
                "(e.g., 'claude', 'codex', 'gemini', or 'cursor-agent') and ensure it is in your PATH."
            )

        if len(available_clis) == 1:
            return available_clis[0]

        # Default to Claude when multiple CLIs are available
        # Fallback logic: Prioritize Claude CLI as the most tested and supported option.
        # If Claude is not available, use the first available CLI from the list.
        if "claude" in available_clis:
            return "claude"
        return available_clis[0]

    def _detect_pr_context(self, task_description: str) -> tuple[str | None, str]:
        """Detect if task is about updating an existing PR.
        Returns: (pr_number, mode) where mode is 'update' or 'create'
        """
        # Patterns that indicate PR update mode
        pr_update_patterns = [
            # Action + anything + PR number
            r"(?:fix|adjust|update|modify|enhance|improve)\s+.*?(?:PR|pull request)\s*#?(\d+)",
            # PR number + needs/should/must
            r"PR\s*#?(\d+)\s+(?:needs|should|must)",
            # Add/apply to PR number
            r"(?:add|apply)\s+.*?to\s+(?:PR|pull request)\s*#?(\d+)",
            # Direct PR number reference
            r"(?:PR|pull request)\s*#(\d+)",
        ]

        # Check for explicit PR number
        for pattern in pr_update_patterns:
            match = re.search(pattern, task_description, re.IGNORECASE)
            if match:
                pr_number = match.group(1)
                return pr_number, "update"

        # Check for contextual PR reference without number
        contextual_patterns = [
            r"(?:the|that|this)\s+PR",
            r"(?:the|that)\s+pull\s+request",
            r"existing\s+PR",
            r"current\s+(?:PR|pull request)",
        ]

        for pattern in contextual_patterns:
            if re.search(pattern, task_description, re.IGNORECASE):
                # Try to find recent PR from current branch or user
                recent_pr = self._find_recent_pr()
                if recent_pr:
                    return recent_pr, "update"
                print("🤔 Ambiguous PR reference detected. Agent will ask for clarification.")
                return None, "update"  # Signal update mode but need clarification

        return None, "create"

    def _resolve_cli_binary(self, cli_name: str) -> str | None:
        """Locate the CLI binary for the requested agent type."""

        profile = CLI_PROFILES.get(cli_name, {})
        cli_binary = profile.get("binary")
        if not cli_binary:
            return None

        cli_path = shutil.which(cli_binary) or ""
        if not cli_path and cli_name == "claude":
            cli_path = self._ensure_mock_claude_binary() or ""

        return cli_path or None

    def _find_recent_pr(self) -> str | None:
        """Try to find a recent PR from current branch or user."""
        try:
            # Try to get PR from current branch
            # Get current branch name first for better readability
            branch_result = subprocess.run(
                ["git", "branch", "--show-current"],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
            current_branch = branch_result.stdout.strip() if branch_result.returncode == 0 else None

            if current_branch:
                result = subprocess.run(
                    [
                        "gh",
                        "pr",
                        "list",
                        "--head",
                        current_branch,
                        "--json",
                        "number",
                        "--limit",
                        "1",
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0 and result.stdout.strip():
                    data = json.loads(result.stdout)
                    if data:
                        return str(data[0]["number"])

            # Fallback: get most recent PR by current user
            result = subprocess.run(
                [
                    "gh",
                    "pr",
                    "list",
                    "--author",
                    "@me",
                    "--json",
                    "number",
                    "--limit",
                    "1",
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout)
                if data:
                    return str(data[0]["number"])
        except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
            # Silently handle errors as this is a fallback mechanism
            pass

        return None

    def broadcast_task_to_a2a(self, task_description: str, requirements: list[str] | None = None) -> str | None:
        """Broadcast task to A2A system for agent claiming"""
        if not self.a2a_enabled or self.task_pool is None:
            return None

        try:
            task_id = self.task_pool.publish_task(
                task_id=f"orch-{int(time.time() * 1000000) % TIMESTAMP_MODULO}",
                task_description=task_description,
                requirements=requirements or [],
            )
            if task_id:
                print(f"Task broadcast to A2A system: {task_id}")
                return task_id
        except Exception as e:
            print(f"Error broadcasting task to A2A: {e}")

        return None

    def get_a2a_status(self) -> dict[str, Any]:
        """Get A2A system status including agents and tasks"""
        if not self.a2a_enabled:
            return {"a2a_enabled": False, "message": "A2A system not available"}

        try:
            # Get overall A2A status - only if A2A is available
            if not A2A_AVAILABLE:
                return {"a2a_enabled": False, "message": "A2A system not available"}

            status = get_a2a_status()

            # Get monitor health
            monitor = get_monitor()
            health = monitor.get_system_health()

            return {
                "a2a_enabled": True,
                "system_status": status,
                "health": health,
                "timestamp": time.time(),
            }
        except Exception as e:
            return {"a2a_enabled": True, "error": str(e), "timestamp": time.time()}

    def analyze_task_and_create_agents(self, task_description: str, forced_cli: str | None = None) -> list[dict]:
        """
        Create appropriate agent for the given task with PR context awareness.

        Args:
            task_description: The task description to analyze and create agents for.
            forced_cli: Optional; the CLI to force agent selection (e.g., from --fixpr-agent flag).
                When provided, this overrides any CLI detection logic and forces the use of the specified CLI.

        Returns:
            List of agent specification dictionaries.
        """
        print("\n🧠 Processing task request...")

        # Extract workspace configuration if present
        workspace_config = self._extract_workspace_config(task_description)
        if workspace_config:
            print(f"🏗️ Extracted workspace config: {workspace_config}")

        agent_cli = self._detect_agent_cli(task_description, forced_cli=forced_cli)
        if agent_cli != "claude":
            print(f"🤖 Selected {agent_cli.capitalize()} CLI based on task request")

        # Detect PR context
        pr_number, mode = self._detect_pr_context(task_description)

        # Show user what was detected
        if mode == "update":
            if pr_number:
                print(f"\n🔍 Detected PR context: #{pr_number} - Agent will UPDATE existing PR")
                # Get PR details for better context
                try:
                    result = subprocess.run(
                        [
                            "gh",
                            "pr",
                            "view",
                            pr_number,
                            "--json",
                            "title,state,headRefName",
                        ],
                        check=False,
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    if result.returncode == 0:
                        pr_data = json.loads(result.stdout)
                        print(f"   Branch: {pr_data['headRefName']}")
                        print(f"   Status: {pr_data['state']}")
                except Exception:
                    pass
            else:
                print("\n🔍 Detected PR update request but no specific PR number")
                print("   Agent will check for recent PRs and ask for clarification if needed")
        else:
            print("\n🆕 No PR context detected - Agent will create NEW PR")
            print("   New branch will be created from main")

        # Use the same unique name generation as other methods
        agent_name = self._generate_unique_name("task-agent", task_description)

        # Get default capabilities from discovery method
        capabilities = list(self.agent_capabilities.keys())

        # Build appropriate prompt based on mode
        if mode == "update":
            if pr_number:
                prompt = f"""Task: {task_description}

🔄 PR UPDATE MODE - You must UPDATE existing PR #{pr_number}

🚧 Checkout rule:
- If `gh pr checkout {pr_number}` fails because the branch is already checked out elsewhere, create a fresh worktree and use it:
  git worktree add /private/tmp/{self._extract_repository_name()}/pr-{pr_number}-rerun {pr_number}
  cd /private/tmp/{self._extract_repository_name()}/pr-{pr_number}-rerun

IMPORTANT INSTRUCTIONS:
1. First, checkout the PR branch: gh pr checkout {pr_number}
2. Make the requested changes on that branch
3. Commit and push to update the existing PR
4. DO NOT create a new branch or new PR
5. Use 'git push' (not 'git push -u origin new-branch')

Key points:
- This is about UPDATING an existing PR, not creating a new one
- Stay on the PR's branch throughout your work
- Your commits will automatically update the PR

🔧 EXECUTION GUIDELINES:
1. **Always use /execute for your work**: Use the /execute command for all task execution to ensure proper planning and execution. This provides structured approach and prevents missing critical steps.

2. **Consider subagents for complex tasks**: For complex or multi-part tasks, always evaluate if subagents would help:
   - Use Task() tool to spawn subagents for parallel work
   - Consider subagents when task has 3+ independent components
   - Use subagents for different skill areas (testing, documentation, research)
   - Example: Task(description="Run comprehensive tests", prompt="Execute all test suites and report results")

3. **Task delegation patterns**:
   - Research tasks: Delegate investigation of large codebases
   - Testing tasks: Separate agents for different test types
   - Documentation: Dedicated agents for complex documentation needs
   - Code analysis: Parallel analysis of multiple files/systems"""
            else:
                prompt = f"""Task: {task_description}

🔄 PR UPDATE MODE - You need to update an existing PR

🚧 Checkout rule:
- If `gh pr checkout` fails because the branch is already checked out elsewhere, create a fresh worktree and use it:
  git worktree add /private/tmp/{self._extract_repository_name()}/pr-update-rerun <branch-or-pr-number>
  cd /private/tmp/{self._extract_repository_name()}/pr-update-rerun

The user referenced "the PR" but didn't specify which one. You must:
1. List recent PRs: gh pr list --author @me --limit 5
2. Identify which PR the user meant based on the task context
3. If unclear, show the PRs and ask: "Which PR should I update? Please specify the PR number."
4. Once identified, checkout that PR's branch and make the requested changes
5. DO NOT create a new PR

🔧 EXECUTION GUIDELINES:
1. **Always use /execute for your work**: Use the /execute command for all task execution to ensure proper planning and execution. This provides structured approach and prevents missing critical steps.

2. **Consider subagents for complex tasks**: For complex or multi-part tasks, always evaluate if subagents would help:
   - Use Task() tool to spawn subagents for parallel work
   - Consider subagents when task has 3+ independent components
   - Use subagents for different skill areas (testing, documentation, research)
   - Example: Task(description="Run comprehensive tests", prompt="Execute all test suites and report results")

3. **Task delegation patterns**:
   - Research tasks: Delegate investigation of large codebases
   - Testing tasks: Separate agents for different test types
   - Documentation: Dedicated agents for complex documentation needs
   - Code analysis: Parallel analysis of multiple files/systems"""
        else:
            prompt = f"""Task: {task_description}

🆕 NEW PR MODE - Create a fresh pull request

Execute the task exactly as requested. Key points:
- Create a new branch from main for your work
- If asked to start a server, start it on the specified port
- If asked to modify files, make those exact modifications
- If asked to run commands, execute them
- If asked to test, run the appropriate tests
- Always follow the specific instructions given

🔧 EXECUTION GUIDELINES:
1. **Always use /execute for your work**: Use the /execute command for all task execution to ensure proper planning and execution. This provides structured approach and prevents missing critical steps.

2. **Consider subagents for complex tasks**: For complex or multi-part tasks, always evaluate if subagents would help:
   - Use Task() tool to spawn subagents for parallel work
   - Consider subagents when task has 3+ independent components
   - Use subagents for different skill areas (testing, documentation, research)
   - Example: Task(description="Run comprehensive tests", prompt="Execute all test suites and report results")

3. **Task delegation patterns**:
   - Research tasks: Delegate investigation of large codebases
   - Testing tasks: Separate agents for different test types
   - Documentation: Dedicated agents for complex documentation needs
   - Code analysis: Parallel analysis of multiple files/systems

Complete the task, then use /pr to create a new pull request."""

        agent_spec = {
            "name": agent_name,
            "type": "development",
            "focus": task_description,
            "capabilities": capabilities,
            "prompt": prompt,
            "cli": agent_cli,
        }

        # Add PR context if updating existing PR
        if mode == "update":
            agent_spec["pr_context"] = {"mode": mode, "pr_number": pr_number}

        # Add workspace configuration if specified
        if workspace_config:
            agent_spec["workspace_config"] = workspace_config
            print(f"🏗️ Custom workspace config: {workspace_config}")

        return [agent_spec]

    def _extract_repository_name(self):
        """Extract repository name from git remote origin URL or fallback to directory name."""
        try:
            # Get the remote origin URL
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                check=True,
                timeout=30,
                shell=False,
            )
            remote_url = result.stdout.strip()

            # Parse SSH format: git@github.com:user/repo.git → repo
            ssh_pattern = r"git@[^:]+:(?P<user>[^/]+)/(?P<repo>[^/]+)\.git"
            ssh_match = re.match(ssh_pattern, remote_url)
            if ssh_match:
                return ssh_match.group("repo")

            # Parse HTTPS format: https://github.com/user/repo.git → repo
            https_pattern = r"https://[^/]+/(?P<user>[^/]+)/(?P<repo>[^/]+)\.git"
            https_match = re.match(https_pattern, remote_url)
            if https_match:
                return https_match.group("repo")

            # If we can't parse the URL, fallback to current directory name
            current_dir = os.getcwd()
            return os.path.basename(current_dir)
        except subprocess.CalledProcessError:
            # If there's no remote origin, fallback to current directory name
            current_dir = os.getcwd()
            return os.path.basename(current_dir)
        except subprocess.TimeoutExpired:
            print("Timeout while extracting repository name")
            # Fallback to current directory name like other errors
            current_dir = os.getcwd()
            return os.path.basename(current_dir)
        except Exception as e:
            print(f"Error extracting repository name: {e}")
            # Fallback to current directory name
            current_dir = os.getcwd()
            return os.path.basename(current_dir)

    def _expand_path(self, path):
        """Expand ~ and resolve paths."""
        try:
            expanded_path = os.path.expanduser(path)
            resolved_path = os.path.realpath(expanded_path)
            return resolved_path
        except Exception as e:
            print(f"Error expanding path {path}: {e}")
            raise

    def _get_worktree_base_path(self):
        """Calculate ~/projects/orch_{repo_name}/ base path."""
        try:
            repo_name = self._extract_repository_name()
            base_path = os.path.join("~", "projects", f"orch_{repo_name}")
            return self._expand_path(base_path)
        except Exception as e:
            print(f"Error getting worktree base path: {e}")
            raise

    def _ensure_directory_exists(self, path):
        """Create directories with proper error handling."""
        try:
            expanded_path = self._expand_path(path)
            Path(expanded_path).mkdir(parents=True, exist_ok=True)
            return expanded_path
        except PermissionError as e:
            print(f"Permission denied creating directory {path}: {e}")
            raise
        except Exception as e:
            print(f"Error creating directory {path}: {e}")
            raise

    def _calculate_agent_directory(self, agent_spec):
        """Calculate final agent directory path based on configuration."""
        try:
            # Get workspace configuration if it exists
            workspace_config = agent_spec.get("workspace_config", {})

            # Check if custom workspace_root is specified
            if "workspace_root" in workspace_config:
                workspace_root = workspace_config["workspace_root"]
                # If workspace_name is also specified, use it
                if "workspace_name" in workspace_config:
                    agent_dir = os.path.join(workspace_root, workspace_config["workspace_name"])
                else:
                    agent_name = agent_spec.get("name", "agent")
                    agent_dir = os.path.join(workspace_root, agent_name)
                return self._expand_path(agent_dir)

            # Check if custom workspace_name is specified
            if "workspace_name" in workspace_config:
                base_path = self._get_worktree_base_path()
                self._ensure_directory_exists(base_path)
                agent_dir = os.path.join(base_path, workspace_config["workspace_name"])
                return self._expand_path(agent_dir)

            # Default case: ~/projects/orch_{repo_name}/{agent_name}
            base_path = self._get_worktree_base_path()
            self._ensure_directory_exists(base_path)
            agent_name = agent_spec.get("name", "agent")
            agent_dir = os.path.join(base_path, agent_name)
            return self._expand_path(agent_dir)

        except Exception as e:
            print(f"Error calculating agent directory: {e}")
            raise

    def _create_worktree_at_location(self, agent_spec, branch_name):
        """Create git worktree at the calculated location."""
        try:
            agent_dir = self._calculate_agent_directory(agent_spec)

            # Ensure parent directory exists
            parent_dir = os.path.dirname(agent_dir)
            self._ensure_directory_exists(parent_dir)

            # Create the worktree
            result = subprocess.run(
                ["git", "worktree", "add", "-b", branch_name, agent_dir, "main"],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
                shell=False,
            )

            return agent_dir, result
        except subprocess.TimeoutExpired:
            print("Timeout while creating worktree")
            raise
        except Exception as e:
            print(f"Error creating worktree at location: {e}")
            raise

    def create_dynamic_agent(self, agent_spec: dict) -> bool:
        """Create agent with enhanced Redis coordination and worktree management."""
        original_agent_name = agent_spec.get("name")
        agent_focus = agent_spec.get("focus", "general task completion")
        agent_prompt = agent_spec.get("prompt", "Complete the assigned task")
        agent_type = agent_spec.get("type", "general")
        capabilities = agent_spec.get("capabilities", [])
        workspace_config = agent_spec.get("workspace_config", {})

        # Refresh actively working agents count from tmux sessions (excludes idle agents)
        # This ensures we check against the actual running system state,
        # clearing any temporary reservations from analysis phase.
        self.active_agents = self._get_active_tmux_agents()

        # 1. Determine the authoritative base name
        # If workspace_name is specified, it takes precedence as the intended name
        if workspace_config and workspace_config.get("workspace_name"):
            base_name = workspace_config["workspace_name"]
            if base_name != original_agent_name:
                print(f"🔄 Aligning agent name: {original_agent_name} → {base_name} (workspace alignment)")
        else:
            base_name = original_agent_name

        # 2. Ensure uniqueness
        existing = self._check_existing_agents()
        existing.update(self.active_agents)

        agent_name = base_name
        # If collision detected, generate a unique variation
        if agent_name in existing:
            timestamp = int(time.time() * 1000000) % 10000
            counter = 1
            original_candidate = f"{base_name}-{timestamp}"
            agent_name = original_candidate

            while agent_name in existing:
                agent_name = f"{original_candidate}-{counter}"
                counter += 1

            print(f"⚠️ Name collision resolved: {base_name} → {agent_name}")

        # 3. Update agent_spec to reflect the final unique name
        # This ensures _create_worktree_at_location uses the correct, unique name
        agent_spec["name"] = agent_name
        if workspace_config:
            # Keep workspace name in sync with agent name
            workspace_config["workspace_name"] = agent_name

        # Clean up any existing stale prompt files for this agent to prevent task reuse
        # Use final agent name for cleanup (after workspace alignment)
        self._cleanup_stale_prompt_files(agent_name)

        # Check concurrent active agent limit
        if len(self.active_agents) >= MAX_CONCURRENT_AGENTS:
            print(f"❌ Active agent limit reached ({MAX_CONCURRENT_AGENTS} max). Cannot create {agent_name}")
            print(f"   Currently working agents: {sorted(self.active_agents)}")
            return False

        # Initialize A2A protocol integration if available
        # File-based A2A protocol is always available
        print(f"📁 File-based A2A protocol available for {agent_name}")

        try:
            agent_cli = (agent_spec.get("cli") or "claude").lower()
            if agent_cli not in CLI_PROFILES:
                print(f"❌ Unsupported agent CLI requested: {agent_cli}")
                return False

            cli_profile = CLI_PROFILES[agent_cli]
            cli_path = self._resolve_cli_binary(agent_cli)

            if not cli_path:
                print(f"⚠️ Requested CLI '{cli_profile['binary']}' not available for {agent_name}")

                fallback_cli = None
                fallback_path = None
                for candidate_cli in CLI_PROFILES:
                    if candidate_cli == agent_cli:
                        continue
                    candidate_path = self._resolve_cli_binary(candidate_cli)
                    if candidate_path:
                        fallback_cli = candidate_cli
                        fallback_path = candidate_path
                        break

                if fallback_cli and fallback_path:
                    print(f"   ➡️ Falling back to {CLI_PROFILES[fallback_cli]['display_name']} CLI")
                    agent_cli = fallback_cli
                    cli_profile = CLI_PROFILES[agent_cli]
                    cli_path = fallback_path
                    agent_spec["cli"] = agent_cli
                else:
                    print(f"❌ Required CLI '{cli_profile['binary']}' not found for agent {agent_name}")
                    if agent_cli == "claude":
                        print("   Install Claude Code CLI: https://docs.anthropic.com/en/docs/claude-code")
                    elif agent_cli == "codex":
                        print("   Install Codex CLI and ensure the 'codex' command is available on your PATH")
                    elif agent_cli == "gemini":
                        print("   Install Gemini CLI and ensure the 'gemini' command is available on your PATH")
                    elif agent_cli == "cursor":
                        print(
                            "   Install Cursor Agent CLI and ensure the 'cursor-agent' command is available on your PATH"
                        )
                    return False

            print(f"🛠️ Using {cli_profile['display_name']} CLI for {agent_name}")

            # Create worktree for agent using new location logic
            try:
                branch_name = f"{agent_name}-work"
                agent_dir, git_result = self._create_worktree_at_location(agent_spec, branch_name)

                print(f"🏗️ Created worktree at: {agent_dir}")

                if git_result.returncode != 0:
                    print(f"⚠️ Git worktree creation warning: {git_result.stderr}")
                    if "already exists" in git_result.stderr:
                        print(f"📁 Using existing worktree at {agent_dir}")
                    else:
                        print(f"❌ Git worktree failed: {git_result.stderr}")
                        return False

            except Exception as e:
                print(f"❌ Failed to create worktree: {e}")
                return False

            agent_token = _sanitize_agent_token(agent_name)

            # Create result collection file
            result_file = os.path.join(self.result_dir, f"{agent_token}_results.json")

            # Enhanced prompt with completion enforcement
            # Determine if we're in PR update mode
            pr_context = agent_spec.get("pr_context", {})
            is_update_mode = pr_context and pr_context.get("mode") == "update"

            attribution_line = cli_profile["generated_with"]
            co_author_line = cli_profile["co_author"]
            attribution_block = f"   {attribution_line}\n\n   Co-Authored-By: {co_author_line}"

            if is_update_mode:
                completion_instructions = f"""
🚨 MANDATORY COMPLETION STEPS FOR PR UPDATE:

1. Complete the assigned task on the existing PR branch
2. Commit and push your changes:

   git add -A
   git commit -m "Update PR #{pr_context.get("pr_number", "unknown")}: {agent_focus}

   Agent: {agent_name}
   Task: {agent_focus}

{attribution_block}"

   git push

3. Verify the PR was updated (if PR number exists):
   {f"gh pr view {pr_context.get('pr_number')} --json state,mergeable" if pr_context.get("pr_number") else "echo 'No PR number provided, skipping verification'"}

4. Create completion report:
   echo '{{"agent": "{agent_name}", "status": "completed", "pr_updated": "{pr_context.get("pr_number", "none")}"}}' > {result_file}

🛑 EXIT CRITERIA - AGENT MUST NOT TERMINATE UNTIL:
1. ✓ Task completed and tested
2. ✓ All changes committed and pushed
3. ✓ PR #{pr_context.get("pr_number", "unknown")} successfully updated
4. ✓ Completion report written to {result_file}
"""
            else:
                completion_instructions = f"""
🚨 MANDATORY COMPLETION STEPS:

1. Complete the assigned task
2. Commit your changes:

   git add -A
   git commit -m "Complete: {agent_focus}

   Agent: {agent_name}
   Task: {agent_focus}

{attribution_block}"

3. Push your branch:
   git push -u origin {branch_name}

4. Decide if a PR is needed based on the context and nature of the work:

   # Use your judgment to determine if a PR is appropriate:
   # - Did the user ask for review or collaboration?
   # - Are the changes significant enough to warrant review?
   # - Would a PR help with tracking or documentation?
   # - Is this experimental work that needs feedback?

   # If you determine a PR is needed:
   /pr  # Or use gh pr create with appropriate title and body

5. Create completion report:
   echo '{{"agent": "{agent_name}", "status": "completed", "branch": "{branch_name}"}}' > {result_file}

🛑 EXIT CRITERIA - AGENT MUST NOT TERMINATE UNTIL:
1. ✓ Task completed and tested
2. ✓ All changes committed
3. ✓ Branch pushed to origin
4. ✓ Completion report written to {result_file}

Note: PR creation is OPTIONAL - use your judgment based on:
- User intent: Did they ask for review, collaboration, or visibility?
- Change significance: Are these substantial modifications?
- Work nature: Is this exploratory, fixing issues, or adding features?
- Context: Would a PR help track this work or get feedback?

Trust your understanding of the task context, not keyword patterns.
"""

            full_prompt = f"""{agent_prompt}

Agent Configuration:
- Name: {agent_name}
- Type: {agent_type}
- Focus: {agent_focus}
- Capabilities: {", ".join(capabilities)}
- Working Directory: {agent_dir}
- Branch: {branch_name} {"(updating existing PR)" if is_update_mode else "(fresh from main)"}

🚨 CRITICAL: {"You are updating an EXISTING PR" if is_update_mode else "You are starting with a FRESH BRANCH from main"}
- {"Work on the existing PR branch" if is_update_mode else "Your branch contains ONLY the main branch code"}
- Make ONLY the changes needed for this specific task
- Do NOT include unrelated changes

🔧 EXECUTION GUIDELINES:
1. **Always use /execute for your work**: Use the /execute command for all task execution to ensure proper planning and execution. This provides structured approach and prevents missing critical steps.

2. **Consider subagents for complex tasks**: For complex or multi-part tasks, always evaluate if subagents would help:
   - Use Task() tool to spawn subagents for parallel work
   - Consider subagents when task has 3+ independent components
   - Use subagents for different skill areas (testing, documentation, research)
   - Example: Task(description="Run comprehensive tests", prompt="Execute all test suites and report results")

3. **Task delegation patterns**:
   - Research tasks: Delegate investigation of large codebases
   - Testing tasks: Separate agents for different test types
   - Documentation: Dedicated agents for complex documentation needs
   - Code analysis: Parallel analysis of multiple files/systems

{completion_instructions}
"""

            # Write prompt to file to avoid shell quoting issues
            prompt_file = os.path.join("/tmp", f"agent_prompt_{agent_token}.txt")
            with open(prompt_file, "w") as f:
                f.write(full_prompt)

            # Create log directory
            log_dir = "/tmp/orchestration_logs"
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, f"{agent_token}.log")

            log_file_quoted = shlex.quote(log_file)
            result_file_quoted = shlex.quote(result_file)
            prompt_file_quoted = shlex.quote(prompt_file)

            # Determine if this is a restart or first run for the selected CLI
            continue_flag = ""
            if cli_profile.get("supports_continue"):
                conversation_file = None
                conversation_dir = cli_profile.get("conversation_dir")
                if conversation_dir:
                    conversation_path = os.path.join(os.path.expanduser(conversation_dir), f"{agent_name}.json")
                    conversation_file = conversation_path
                restart_env = cli_profile.get("restart_env")
                restart_requested = bool(restart_env and os.environ.get(restart_env, "false").strip().lower() == "true")
                if (conversation_file and os.path.exists(conversation_file)) or restart_requested:
                    continue_flag = cli_profile.get("continue_flag", "")
                    print(f"🔄 {agent_name}: Continuing existing {cli_profile['display_name']} session")
                else:
                    print(f"🆕 {agent_name}: Starting new {cli_profile['display_name']} session")
            else:
                print(f"🆕 {agent_name}: Starting {cli_profile['display_name']} session")

            continue_segment = f" {continue_flag}" if continue_flag else ""
            prompt_value_raw = prompt_file
            prompt_value_quoted = shlex.quote(prompt_file)
            prompt_value = prompt_value_quoted if cli_profile.get("quote_prompt") else prompt_value_raw
            binary_value = shlex.quote(cli_path)
            try:
                cli_command = (
                    cli_profile["command_template"]
                    .format(
                        binary=binary_value,
                        binary_path=cli_path,
                        prompt_file=prompt_value,
                        prompt_file_path=prompt_value_raw,
                        prompt_file_quoted=prompt_value_quoted,
                        continue_flag=continue_segment,
                    )
                    .strip()
                )
            except KeyError as exc:
                missing = exc.args[0]
                raise ValueError(f"CLI command template for {agent_cli} missing placeholder '{missing}'") from exc

            stdin_template = cli_profile.get("stdin_template", "/dev/null")
            if stdin_template == "{prompt_file}":
                stdin_target = prompt_file
            else:
                stdin_target = stdin_template

            stdin_redirect = ""
            if stdin_target:
                stdin_redirect = f" < {shlex.quote(stdin_target)}"

            stdin_log_target = stdin_target or "/dev/null"
            stdin_log_target_quoted = shlex.quote(stdin_log_target)
            command_execution_line = cli_command + stdin_redirect
            prompt_env_export = f"export ORCHESTRATION_PROMPT_FILE={prompt_file_quoted}"

            agent_name_quoted = shlex.quote(agent_name)
            cli_display_name_quoted = shlex.quote(cli_profile["display_name"])
            agent_dir_quoted = shlex.quote(agent_dir)
            log_file_display = shlex.quote(log_file)
            monitor_hint = shlex.quote(agent_name)
            agent_name_json = json.dumps(agent_name)
            agent_name_json_shell = agent_name_json.replace('"', '\\"')

            # Enhanced bash command with error handling and logging
            bash_cmd = f"""
# Signal handler to log interruptions
trap 'echo "[$(date)] Agent interrupted with signal SIGINT" | tee -a {log_file_quoted}; exit 130' SIGINT
trap 'echo "[$(date)] Agent terminated with signal SIGTERM" | tee -a {log_file_quoted}; exit 143' SIGTERM

echo "[$(date)] Starting agent {agent_name_quoted}" | tee -a {log_file_quoted}
echo "[$(date)] Working directory: {agent_dir_quoted}" | tee -a {log_file_quoted}
echo "[$(date)] Executing CLI command:" | tee -a {log_file_quoted}
cat <<'__ORCH_CLI_COMMAND__' | tee -a {log_file_quoted}
{cli_command}
__ORCH_CLI_COMMAND__
echo "[$(date)] SAFETY: stdin redirected to {stdin_log_target_quoted}" | tee -a {log_file_quoted}

{prompt_env_export}

# Run CLI with configured stdin handling
{command_execution_line} 2>&1 | tee -a {log_file_quoted}
CLI_EXIT=$?

echo "[$(date)] {cli_display_name_quoted} exit code: $CLI_EXIT" | tee -a {log_file_quoted}

if [ $CLI_EXIT -eq 0 ]; then
    echo "[$(date)] Agent completed successfully" | tee -a {log_file_quoted}
    echo "{{\"agent\": {agent_name_json_shell}, \"status\": \"completed\", \"exit_code\": 0}}" > {result_file_quoted}
else
    echo "[$(date)] Agent failed with exit code $CLI_EXIT" | tee -a {log_file_quoted}
    echo "{{\"agent\": {agent_name_json_shell}, \"status\": \"failed\", \"exit_code\": $CLI_EXIT}}" > {result_file_quoted}
fi

# Keep session alive for 1 hour for monitoring and debugging
echo "[$(date)] Agent execution completed. Session remains active for monitoring." | tee -a {log_file_quoted}
echo "[$(date)] Session will auto-close in 1 hour. Check log at: {log_file_display}" | tee -a {log_file_quoted}
echo "[$(date)] Monitor with: tmux attach -t {monitor_hint}" | tee -a {log_file_quoted}
sleep {AGENT_SESSION_TIMEOUT_SECONDS}
"""

            script_path = Path("/tmp") / f"{agent_token}_run.sh"
            script_path.write_text(bash_cmd, encoding="utf-8")
            os.chmod(script_path, 0o700)

            # Use agent-specific tmux config for 1-hour sessions
            tmux_config = get_tmux_config_path()

            # Kill existing tmux session if present to allow reuse
            _kill_tmux_session_if_exists(agent_name)

            # Build tmux command with optional config file
            tmux_cmd = ["tmux"]
            if os.path.exists(tmux_config):
                tmux_cmd.extend(["-f", tmux_config])
            else:
                print(f"⚠️ Warning: tmux config file not found at {tmux_config}, using default config")

            tmux_cmd.extend(
                [
                    "new-session",
                    "-d",
                    "-s",
                    agent_name,
                    "-c",
                    agent_dir,
                    "bash",
                    str(script_path),
                ]
            )

            result = subprocess.run(tmux_cmd, check=False, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                print(f"⚠️ Error creating tmux session: {result.stderr}")
                return False

            # A2A registration happens automatically via file system
            # Agent will register itself when it starts using A2AAgentWrapper

            print(f"✅ Created {agent_name} - Focus: {agent_focus}")
            return True

        except Exception as e:
            print(f"❌ Failed to create {agent_name}: {e}")
            return False

    def _ensure_mock_claude_binary(self) -> str:
        """Provide a lightweight mock Claude binary when running in testing mode."""

        def _is_truthy(value: str | None) -> bool:
            return (value or "").strip().lower() in {"1", "true", "yes"}

        testing_mode = any(
            _is_truthy(os.environ.get(env_var)) for env_var in ("MOCK_SERVICES_MODE", "TESTING", "FAST_TESTS")
        )

        if not testing_mode:
            return ""

        if self._mock_claude_path and os.path.exists(self._mock_claude_path):
            return self._mock_claude_path

        try:
            mock_dir = Path(tempfile.gettempdir()) / "worldarchitect_ai"
            mock_dir.mkdir(parents=True, exist_ok=True)
            mock_path = mock_dir / "mock_claude.sh"

            # Simple shim that echoes the call for logging and exits successfully
            script_contents = """#!/usr/bin/env bash
echo "[mock claude] $@"
exit 0
"""
            mock_path.write_text(script_contents, encoding="utf-8")
            os.chmod(mock_path, 0o755)
            self._mock_claude_path = str(mock_path)
            print("⚠️ 'claude' command not found. Using mock binary for testing.")
            return self._mock_claude_path
        except Exception as exc:
            print(f"⚠️ Failed to create mock Claude binary: {exc}")
            return ""


if __name__ == "__main__":
    # Simple test mode - create single agent
    dispatcher = TaskDispatcher()
    print("Task Dispatcher ready for dynamic agent creation")
