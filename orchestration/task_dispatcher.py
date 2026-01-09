#!/usr/bin/env python3
"""
A2A-Enhanced Task Dispatcher for Multi-Agent Orchestration
Handles dynamic agent creation with Agent-to-Agent communication support
"""

from __future__ import annotations

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

# Default Gemini model can be overridden via GEMINI_MODEL; always use gemini-3-pro-preview
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
            "{binary} --model {model} -p @{prompt_file} "
            "--output-format stream-json --verbose{continue_flag} --dangerously-skip-permissions"
        ),
        "stdin_template": "/dev/null",
        "quote_prompt": False,
        # Unset API key to force OAuth/interactive auth (consistent with other CLIs)
        "env_unset": ["ANTHROPIC_API_KEY"],
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
        # Unset API key to force OAuth/interactive auth (consistent with other CLIs)
        "env_unset": ["OPENAI_API_KEY"],
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
        # Stick to configured GEMINI_MODEL (default gemini-3-pro) unless overridden
        # YOLO mode enabled to allow file access outside workspace (user directive)
        # NOTE: Prompt must come via stdin (not -p flag which is deprecated and only appends to stdin)
        "command_template": f"{{binary}} -m {GEMINI_MODEL} --yolo",
        "stdin_template": "{prompt_file}",
        "quote_prompt": False,
        # Unset GEMINI_API_KEY to force OAuth authentication (higher quotas than API key)
        # See: https://github.com/google-gemini/gemini-cli/blob/main/docs/get-started/authentication.md
        "env_unset": ["GEMINI_API_KEY"],
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
        # No known API key to unset for Cursor (uses its own auth)
        "env_unset": [],
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
            5. Default to 'gemini' if multiple CLIs available
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
            if self._is_testing_mode():
                return "claude"
            raise RuntimeError(
                "No agent CLI is available. Please install at least one supported CLI "
                "(e.g., 'claude', 'codex', 'gemini', or 'cursor-agent') and ensure it is in your PATH."
            )

        if len(available_clis) == 1:
            return available_clis[0]

        # Default to Gemini when multiple CLIs are available
        # Fallback logic: Prioritize Gemini CLI as the default orchestration agent.
        # If Gemini is not available, fall back to Claude, then the first available CLI.
        if "gemini" in available_clis:
            return "gemini"
        if "claude" in available_clis:
            return "claude"
        return available_clis[0]

    def _parse_cli_chain(self, cli_value: str) -> list[str]:
        """Parse a comma-separated CLI chain string (e.g., 'gemini,codex') into validated CLI keys."""
        if not isinstance(cli_value, str):
            raise ValueError("CLI chain value must be a string")

        parts = [part.strip().lower() for part in cli_value.split(",")]
        chain = [part for part in parts if part]
        if not chain:
            raise ValueError("CLI chain is empty")

        invalid = [cli for cli in chain if cli not in CLI_PROFILES]
        if invalid:
            raise ValueError(f"Invalid CLI(s) in chain: {invalid}. Must be subset of {list(CLI_PROFILES.keys())}")

        # De-duplicate while preserving order
        seen = set()
        ordered = []
        for cli in chain:
            if cli not in seen:
                ordered.append(cli)
                seen.add(cli)
        return ordered

    def _detect_agent_cli_chain(self, task_description: str, forced_cli: str | None = None) -> list[str]:
        """
        Determine which CLI (or CLI chain) should be used for the agent.

        Supports comma-separated chains via:
        - forced_cli (e.g., "gemini,codex")
        - --agent-cli flag in task_description (e.g., --agent-cli=gemini,codex)
        """

        cli_flag = re.search(r"--agent-cli(?:=|\s+)([A-Za-z0-9_,]+)", task_description, re.IGNORECASE)

        if forced_cli is not None:
            forced_cli = forced_cli.strip().lower()
            chain = self._parse_cli_chain(forced_cli) if "," in forced_cli else [forced_cli]
            if len(chain) == 1 and chain[0] not in CLI_PROFILES:
                raise ValueError(f"Invalid forced_cli: {forced_cli}. Must be one of {list(CLI_PROFILES.keys())}")
            if cli_flag:
                requested = cli_flag.group(1).strip().lower()
                if requested != forced_cli:
                    print(f"⚠️ Forced CLI '{forced_cli}' overrides --agent-cli request for '{requested}'.")
            return chain

        if cli_flag:
            requested = cli_flag.group(1).strip().lower()
            if "," in requested:
                return self._parse_cli_chain(requested)
            if requested in CLI_PROFILES:
                return [requested]
            raise ValueError(f"Invalid --agent-cli: {requested}. Must be one of {list(CLI_PROFILES.keys())}")

        return [self._detect_agent_cli(task_description, forced_cli=None)]

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
        if not cli_path and self._is_testing_mode():
            cli_path = self._ensure_mock_cli_binary(cli_name) or ""

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

        cli_chain = self._detect_agent_cli_chain(task_description, forced_cli=forced_cli)
        agent_cli = cli_chain[0]
        if len(cli_chain) > 1:
            print(f"🤖 Selected CLI chain based on task request: {', '.join(cli_chain)}")
        elif agent_cli != "claude":
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
        if len(cli_chain) > 1:
            agent_spec["cli_chain"] = cli_chain

        # Add PR context if updating existing PR
        if mode == "update":
            agent_spec["pr_context"] = {"mode": mode, "pr_number": pr_number}

        # Add workspace configuration if specified
        if workspace_config:
            agent_spec["workspace_config"] = workspace_config
            print(f"🏗️ Custom workspace config: {workspace_config}")

        return [agent_spec]

    @staticmethod
    def _is_safe_branch_name(branch_name: str) -> bool:
        """Validate branch name against safe pattern to avoid injection risks."""
        return bool(re.match(r"^[A-Za-z0-9._/-]+$", branch_name))

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

    def _create_worktree_at_location(self, agent_spec, branch_name, base_ref="main", create_new_branch=True):
        """Create git worktree at the calculated location."""
        try:
            agent_dir = self._calculate_agent_directory(agent_spec)

            # Ensure parent directory exists
            parent_dir = os.path.dirname(agent_dir)
            self._ensure_directory_exists(parent_dir)

            # Create the worktree
            command = ["git", "worktree", "add"]
            if create_new_branch:
                command.extend(["-b", branch_name, agent_dir, base_ref])
            else:
                command.extend([agent_dir, branch_name])
            result = subprocess.run(
                command,
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
        existing_branch = agent_spec.get("existing_branch")
        existing_pr = agent_spec.get("existing_pr")
        mcp_agent_name = agent_spec.get("mcp_agent_name")
        bead_id = agent_spec.get("bead_id")
        validation_command = agent_spec.get("validation_command")
        model = agent_spec.get("model", "sonnet")  # Default to sonnet if not specified

        # Sanitize model to prevent injection
        raw_model = str(model)
        if not re.fullmatch(r"[A-Za-z0-9_.\-]+", raw_model):
            print(f"❌ Invalid model name requested: {raw_model!r}")
            return False
        model = raw_model
        no_new_pr = bool(agent_spec.get("no_new_pr"))
        no_new_branch = bool(agent_spec.get("no_new_branch"))

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
            # Support optional comma-separated CLI chains (preferred order)
            raw_cli_chain = agent_spec.get("cli_chain")
            if raw_cli_chain is None:
                raw_cli_chain = agent_spec.get("cli")

            cli_chain = []
            if isinstance(raw_cli_chain, str):
                value = raw_cli_chain.strip().lower()
                cli_chain = self._parse_cli_chain(value) if "," in value else [value or "claude"]
            elif isinstance(raw_cli_chain, list):
                cli_chain = [str(item).strip().lower() for item in raw_cli_chain if str(item).strip()]
                if not cli_chain:
                    cli_chain = ["claude"]
            else:
                cli_chain = ["claude"]

            invalid_chain = [cli for cli in cli_chain if cli not in CLI_PROFILES]
            if invalid_chain:
                print(f"❌ Unsupported agent CLI requested: {invalid_chain}")
                return False

            # Resolve the first available CLI in the chain (keeps behavior predictable)
            agent_cli = cli_chain[0]
            cli_profile = CLI_PROFILES[agent_cli]
            cli_path = None
            for candidate in cli_chain:
                candidate_path = self._resolve_cli_binary(candidate)
                if candidate_path:
                    agent_cli = candidate
                    cli_profile = CLI_PROFILES[agent_cli]
                    cli_path = candidate_path
                    break

            # Persist chain for downstream script-generation
            agent_spec["cli"] = agent_cli
            if len(cli_chain) > 1:
                agent_spec["cli_chain"] = cli_chain

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
                    agent_spec["cli_chain"] = [agent_cli]
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
                if no_new_branch and not existing_branch:
                    print("❌ Branch creation is blocked but no existing branch was provided.")
                    return False

                if existing_branch:
                    if not self._is_safe_branch_name(existing_branch):
                        print(f"❌ Unsafe branch name provided: {existing_branch}")
                        return False
                    branch_name = existing_branch
                    agent_dir, git_result = self._create_worktree_at_location(
                        agent_spec, branch_name, create_new_branch=False
                    )
                else:
                    branch_name = f"{agent_name}-work"
                    if not self._is_safe_branch_name(branch_name):
                        print(f"❌ Unsafe branch name generated: {branch_name}")
                        return False
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
            if existing_pr and not pr_context:
                pr_context = {"mode": "update", "pr_number": existing_pr}
                agent_spec["pr_context"] = pr_context
            is_update_mode = pr_context and pr_context.get("mode") == "update"
            if existing_pr is None and pr_context.get("pr_number"):
                existing_pr = pr_context.get("pr_number")

            attribution_line = cli_profile["generated_with"]
            co_author_line = cli_profile["co_author"]
            attribution_block = f"   {attribution_line}\n\n   Co-Authored-By: {co_author_line}"

            validation_instructions = ""
            if validation_command:
                validation_instructions = f"""
✅ Validation command:
- Run: {validation_command}
- Report results in your completion summary.
"""

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

{validation_instructions}

4. Create completion report:
   echo '{{"agent": "{agent_name}", "status": "completed", "pr_updated": "{pr_context.get("pr_number", "none")}"}}' > {result_file}

🛑 EXIT CRITERIA - AGENT MUST NOT TERMINATE UNTIL:
1. ✓ Task completed and tested
2. ✓ All changes committed and pushed
3. ✓ PR #{pr_context.get("pr_number", "unknown")} successfully updated
4. ✓ Completion report written to {result_file}
"""
            else:
                if no_new_pr:
                    pr_creation_instructions = "4. Do NOT create a PR. PR creation is blocked by orchestration."
                    pr_creation_note = "PR creation is BLOCKED."
                else:
                    pr_creation_instructions = """
4. Decide if a PR is needed based on the context and nature of the work:

   # Use your judgment to determine if a PR is appropriate:
   # - Did the user ask for review or collaboration?
   # - Are the changes significant enough to warrant review?
   # - Would a PR help with tracking or documentation?
   # - Is this experimental work that needs feedback?

   # If you determine a PR is needed:
   /pr  # Or use gh pr create with appropriate title and body
"""
                    pr_creation_note = """
Note: PR creation is OPTIONAL - use your judgment based on:
- User intent: Did they ask for review, collaboration, or visibility?
- Change significance: Are these substantial modifications?
- Work nature: Is this exploratory, fixing issues, or adding features?
- Context: Would a PR help track this work or get feedback?

Trust your understanding of the task context, not keyword patterns.
"""

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

{pr_creation_instructions}
{validation_instructions}

5. Create completion report:
   echo '{{"agent": "{agent_name}", "status": "completed", "branch": "{branch_name}"}}' > {result_file}

🛑 EXIT CRITERIA - AGENT MUST NOT TERMINATE UNTIL:
1. ✓ Task completed and tested
2. ✓ All changes committed
3. ✓ Branch pushed to origin
4. ✓ Completion report written to {result_file}

{pr_creation_note}
"""

            full_prompt = f"""{agent_prompt}

Agent Configuration:
- Name: {agent_name}
- Type: {agent_type}
- Focus: {agent_focus}
- Capabilities: {", ".join(capabilities)}
- Working Directory: {agent_dir}
- Branch: {branch_name} {"(existing branch)" if existing_branch else "(fresh from main)"}
- PR Creation: {"BLOCKED" if no_new_pr else "ALLOWED"}
- Branch Creation: {"BLOCKED" if no_new_branch else "ALLOWED"}
{f"- Target PR: #{existing_pr}" if existing_pr else ""}
{f"- MCP Agent Name: {mcp_agent_name}" if mcp_agent_name else ""}
{f"- Bead ID: {bead_id}" if bead_id else ""}
{f"- Validation Command: {validation_command}" if validation_command else ""}

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

            prompt_env_export = f"export ORCHESTRATION_PROMPT_FILE={prompt_file_quoted}"

            agent_name_quoted = shlex.quote(agent_name)
            agent_dir_quoted = shlex.quote(agent_dir)
            log_file_display = shlex.quote(log_file)
            monitor_hint = shlex.quote(agent_name)
            agent_name_json = json.dumps(agent_name)

            # Optional multi-CLI chain support (e.g., --agent-cli=gemini,codex)
            raw_cli_chain = agent_spec.get("cli_chain")
            cli_chain = []
            if isinstance(raw_cli_chain, str):
                cli_chain = (
                    self._parse_cli_chain(raw_cli_chain) if "," in raw_cli_chain else [raw_cli_chain.strip().lower()]
                )
            elif isinstance(raw_cli_chain, list):
                cli_chain = [str(item).strip().lower() for item in raw_cli_chain if str(item).strip()]
            if not cli_chain:
                cli_chain = [agent_cli]

            # Validate chain entries
            invalid_chain = [cli for cli in cli_chain if cli not in CLI_PROFILES]
            if invalid_chain:
                raise ValueError(f"Invalid CLI(s) in cli_chain for {agent_name}: {invalid_chain}")

            # Compute per-CLI execution blocks (command + stdin + env unsets)
            cli_chain_str = ",".join(cli_chain)
            cli_chain_json = json.dumps(cli_chain_str)
            rate_limit_pattern = "exhausted your daily quota|rate limit|quota exceeded|resource_exhausted"

            attempt_blocks = ""
            for idx, attempt_cli in enumerate(cli_chain, start=1):
                attempt_profile = CLI_PROFILES[attempt_cli]
                attempt_path = self._resolve_cli_binary(attempt_cli) or attempt_profile.get("binary") or attempt_cli
                attempt_binary_value = shlex.quote(attempt_path)

                # Continue logic per CLI (only meaningful for CLIs that support it)
                attempt_continue_flag = ""
                if attempt_profile.get("supports_continue"):
                    conversation_file = None
                    conversation_dir = attempt_profile.get("conversation_dir")
                    if conversation_dir:
                        conversation_path = os.path.join(os.path.expanduser(conversation_dir), f"{agent_name}.json")
                        conversation_file = conversation_path
                    restart_env = attempt_profile.get("restart_env")
                    restart_requested = bool(
                        restart_env and os.environ.get(restart_env, "false").strip().lower() == "true"
                    )
                    if (conversation_file and os.path.exists(conversation_file)) or restart_requested:
                        attempt_continue_flag = attempt_profile.get("continue_flag", "")

                attempt_continue_segment = f" {attempt_continue_flag}" if attempt_continue_flag else ""

                attempt_prompt_value_raw = prompt_file
                attempt_prompt_value_quoted = shlex.quote(prompt_file)
                attempt_prompt_value = (
                    attempt_prompt_value_quoted if attempt_profile.get("quote_prompt") else attempt_prompt_value_raw
                )

                attempt_cli_command = (
                    attempt_profile["command_template"]
                    .format(
                        binary=attempt_binary_value,
                        binary_path=attempt_path,
                        prompt_file=attempt_prompt_value,
                        prompt_file_path=attempt_prompt_value_raw,
                        prompt_file_quoted=attempt_prompt_value_quoted,
                        continue_flag=attempt_continue_segment,
                        model=model,
                    )
                    .strip()
                )

                attempt_stdin_template = attempt_profile.get("stdin_template", "/dev/null")
                if attempt_stdin_template == "{prompt_file}":
                    attempt_stdin_target = prompt_file
                else:
                    attempt_stdin_target = attempt_stdin_template

                attempt_stdin_redirect = ""
                if attempt_stdin_target:
                    attempt_stdin_redirect = f" < {shlex.quote(attempt_stdin_target)}"

                attempt_execution_line = attempt_cli_command + attempt_stdin_redirect

                attempt_env_unset_list = attempt_profile.get("env_unset", [])
                for var in attempt_env_unset_list:
                    if not isinstance(var, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", var):
                        raise ValueError(
                            f"Invalid environment variable name in env_unset for CLI profile "
                            f"'{attempt_profile.get('display_name', attempt_cli)}': {var!r}"
                        )
                attempt_env_unset_commands = (
                    "\n".join(f"unset {var}" for var in attempt_env_unset_list) if attempt_env_unset_list else ""
                )

                attempt_display_name = attempt_profile.get("display_name", attempt_cli)

                attempt_blocks += f"""
if [ $RESULT_WRITTEN -eq 0 ]; then
    ATTEMPT_NUM={idx}
    ATTEMPT_CLI={shlex.quote(attempt_cli)}
    if [ -z "$FIRST_ATTEMPT_CLI" ]; then FIRST_ATTEMPT_CLI="$ATTEMPT_CLI"; fi
    if [ "$ATTEMPT_CLI" != "$FIRST_ATTEMPT_CLI" ]; then
        FALLBACK_ATTEMPTED=1
        FALLBACK_FROM="$FIRST_ATTEMPT_CLI"
        FALLBACK_TO="$ATTEMPT_CLI"
    fi

    echo "[$(date)] 🔁 Attempt $ATTEMPT_NUM: {attempt_display_name}" | tee -a {log_file_quoted}
    echo "[$(date)] Executing: {attempt_execution_line}" | tee -a {log_file_quoted}

    LOG_START_LINE=$(wc -l < {log_file_quoted} 2>/dev/null || echo 0)

    {prompt_env_export}
    {attempt_env_unset_commands}

    {attempt_execution_line} 2>&1 | tee -a {log_file_quoted}
    ATTEMPT_EXIT=${{PIPESTATUS[0]}}

    LOG_END_LINE=$(wc -l < {log_file_quoted} 2>/dev/null || echo "$LOG_START_LINE")

    echo "[$(date)] {attempt_display_name} exit code: $ATTEMPT_EXIT" | tee -a {log_file_quoted}

    RATE_LIMITED=0
    if [ "$LOG_END_LINE" -ge "$LOG_START_LINE" ]; then
        if sed -n "$((LOG_START_LINE+1)),$LOG_END_LINE p" {log_file_quoted} 2>/dev/null | grep -Eqi "{rate_limit_pattern}"; then
            RATE_LIMITED=1
            RATE_LIMITED_SEEN=1
            echo "[$(date)] ⚠️  Detected rate limit/quota output (treating as failure)" | tee -a {log_file_quoted}
        fi
    fi

    if [ $ATTEMPT_EXIT -eq 0 ] && [ $RATE_LIMITED -eq 0 ]; then
        RESULT_STATUS="completed"
        FINAL_EXIT_CODE=0
        CLI_USED="$ATTEMPT_CLI"
        RESULT_WRITTEN=1
        echo "[$(date)] ✅ Agent completed successfully via {attempt_display_name}" | tee -a {log_file_quoted}
    else
        CLI_LAST="$ATTEMPT_CLI"
        FINAL_EXIT_CODE=$ATTEMPT_EXIT
        echo "[$(date)] ❌ Attempt failed via {attempt_display_name} (exit=$ATTEMPT_EXIT rate_limited=$RATE_LIMITED)" | tee -a {log_file_quoted}
    fi
fi
"""

            # Enhanced bash command with error handling and logging
            bash_cmd = f"""
# Signal handler to log interruptions
trap 'echo "[$(date)] Agent interrupted with signal SIGINT" | tee -a {log_file_quoted}; exit 130' SIGINT
trap 'echo "[$(date)] Agent terminated with signal SIGTERM" | tee -a {log_file_quoted}; exit 143' SIGTERM

echo "[$(date)] Starting agent {agent_name_quoted}" | tee -a {log_file_quoted}
echo "[$(date)] Working directory: {agent_dir_quoted}" | tee -a {log_file_quoted}
echo "[$(date)] CLI chain: {cli_chain_str}" | tee -a {log_file_quoted}

RESULT_WRITTEN=0
RESULT_STATUS="failed"
FINAL_EXIT_CODE=1
CLI_USED=""
CLI_LAST=""
FALLBACK_ATTEMPTED=0
FALLBACK_FROM=""
FALLBACK_TO=""
FIRST_ATTEMPT_CLI=""
RATE_LIMITED_SEEN=0

{attempt_blocks}

if [ "$RESULT_STATUS" = "completed" ]; then
    if [ $FALLBACK_ATTEMPTED -eq 1 ]; then
        if [ $RATE_LIMITED_SEEN -eq 1 ]; then
            cat > {result_file_quoted} <<EOF
{{"agent": {agent_name_json}, "status": "completed", "exit_code": 0, "cli_used": "${{CLI_USED}}", "cli_chain": {cli_chain_json}, "fallback_from": "${{FALLBACK_FROM}}", "fallback_to": "${{CLI_USED}}", "fallback_attempted": true, "rate_limited": true}}
EOF
        else
            cat > {result_file_quoted} <<EOF
{{"agent": {agent_name_json}, "status": "completed", "exit_code": 0, "cli_used": "${{CLI_USED}}", "cli_chain": {cli_chain_json}, "fallback_from": "${{FALLBACK_FROM}}", "fallback_to": "${{CLI_USED}}", "fallback_attempted": true}}
EOF
        fi
    else
        cat > {result_file_quoted} <<EOF
{{"agent": {agent_name_json}, "status": "completed", "exit_code": 0, "cli_used": "${{CLI_USED}}", "cli_chain": {cli_chain_json}}}
EOF
    fi
else
    if [ $FALLBACK_ATTEMPTED -eq 1 ]; then
        if [ $RATE_LIMITED_SEEN -eq 1 ]; then
            cat > {result_file_quoted} <<EOF
{{"agent": {agent_name_json}, "status": "failed", "exit_code": $FINAL_EXIT_CODE, "cli_last": "${{CLI_LAST}}", "cli_chain": {cli_chain_json}, "fallback_from": "${{FALLBACK_FROM}}", "fallback_to": "${{FALLBACK_TO}}", "fallback_attempted": true, "rate_limited": true}}
EOF
        else
            cat > {result_file_quoted} <<EOF
{{"agent": {agent_name_json}, "status": "failed", "exit_code": $FINAL_EXIT_CODE, "cli_last": "${{CLI_LAST}}", "cli_chain": {cli_chain_json}, "fallback_from": "${{FALLBACK_FROM}}", "fallback_to": "${{FALLBACK_TO}}", "fallback_attempted": true}}
EOF
        fi
    else
        if [ $RATE_LIMITED_SEEN -eq 1 ]; then
            cat > {result_file_quoted} <<EOF
{{"agent": {agent_name_json}, "status": "failed", "exit_code": $FINAL_EXIT_CODE, "cli_last": "${{CLI_LAST}}", "cli_chain": {cli_chain_json}, "rate_limited": true}}
EOF
        else
            cat > {result_file_quoted} <<EOF
{{"agent": {agent_name_json}, "status": "failed", "exit_code": $FINAL_EXIT_CODE, "cli_last": "${{CLI_LAST}}", "cli_chain": {cli_chain_json}}}
EOF
        fi
    fi
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

    def _is_testing_mode(self) -> bool:
        """Return True when running in a testing/CI context."""

        def _is_truthy(value: str | None) -> bool:
            return (value or "").strip().lower() in {"1", "true", "yes"}

        return any(_is_truthy(os.environ.get(env_var)) for env_var in ("MOCK_SERVICES_MODE", "TESTING", "FAST_TESTS"))

    def _ensure_mock_cli_binary(self, cli_name: str) -> str:
        """Provide a lightweight mock CLI binary when running in testing mode."""

        if not self._is_testing_mode():
            return ""

        if cli_name == "claude" and self._mock_claude_path and os.path.exists(self._mock_claude_path):
            return self._mock_claude_path

        try:
            mock_dir = Path(tempfile.gettempdir()) / "worldarchitect_ai"
            mock_dir.mkdir(parents=True, exist_ok=True)
            mock_path = mock_dir / f"mock_{cli_name}.sh"

            # Simple shim that echoes the call for logging and exits successfully
            script_contents = f"""#!/usr/bin/env bash
echo "[mock {cli_name}] $@"
exit 0
"""
            mock_path.write_text(script_contents, encoding="utf-8")
            os.chmod(mock_path, 0o755)
            if cli_name == "claude":
                self._mock_claude_path = str(mock_path)
            print(f"⚠️ '{cli_name}' command not found. Using mock binary for testing.")
            return str(mock_path)
        except Exception as exc:
            print(f"⚠️ Failed to create mock {cli_name} binary: {exc}")
            return ""

    def _ensure_mock_claude_binary(self) -> str:
        """Provide a lightweight mock Claude binary when running in testing mode."""
        return self._ensure_mock_cli_binary("claude")


if __name__ == "__main__":
    # Simple test mode - create single agent
    dispatcher = TaskDispatcher()
    print("Task Dispatcher ready for dynamic agent creation")
