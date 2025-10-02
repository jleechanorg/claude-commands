#!/usr/bin/env python3
"""
A2A-Enhanced Task Dispatcher for Multi-Agent Orchestration
Handles dynamic agent creation with Agent-to-Agent communication support
"""

import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any
from a2a_integration import TaskPool, get_a2a_status
from a2a_monitor import get_monitor
from constants import (
    AGENT_SESSION_TIMEOUT_SECONDS,
    DEFAULT_MAX_CONCURRENT_AGENTS,
    TIMESTAMP_MODULO,
)

A2A_AVAILABLE = True

# Constraint system removed - using simple safety rules only

# Production safety limits - only counts actively working agents (not idle)
MAX_CONCURRENT_AGENTS = int(os.environ.get('MAX_CONCURRENT_AGENTS', DEFAULT_MAX_CONCURRENT_AGENTS))


# Shared configuration paths
def get_tmux_config_path():
    """Get the path to the tmux agent configuration file."""
    return os.path.join(os.path.dirname(__file__), "tmux-agent.conf")


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

            sessions = result.stdout.strip().split('\n')
            # Get all task-agent-* sessions
            all_agent_sessions = {s for s in sessions if s.startswith('task-agent-')}

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
                "Monitor with: tmux attach"
            ]

            # If any completion indicator is found, agent is idle
            for indicator in completion_indicators:
                if indicator in output:
                    return False

            # If no completion indicators found, assume agent is actively working
            return True

        except Exception as e:
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
            pr_match = re.search(r'(?:PR|pull request)\s*#?(\d+)', task_description, re.IGNORECASE)
            if pr_match:
                task_suffix = f"pr{pr_match.group(1)}"
            else:
                # Extract key action words for general tasks
                action_words = re.findall(r'\b(?:implement|create|build|fix|test|deploy|analyze|review|update|add|remove|refactor|optimize)\b',
                                        task_description.lower())
                if action_words:
                    # Use first action word + key object words
                    action = action_words[0]
                    # Extract key nouns/objects after cleaning
                    clean_desc = re.sub(r'[^a-zA-Z0-9\s]', '', task_description.lower())
                    words = [word for word in clean_desc.split() if word not in ['the', 'and', 'or', 'for', 'with', 'in', 'on', 'at', 'to', 'from', 'by', 'of', 'a', 'an']]

                    # Skip action word and take next meaningful words
                    content_words = [w for w in words if w != action][:2]
                    if content_words:
                        desc_part = '-'.join(word[:6] for word in content_words)
                        task_suffix = f"{action}-{desc_part}"
                    else:
                        task_suffix = action
                else:
                    # Fallback to first few meaningful words
                    clean_desc = re.sub(r'[^a-zA-Z0-9\s]', '', task_description.lower())
                    words = [word for word in clean_desc.split() if len(word) > 2][:2]
                    if words:
                        task_suffix = '-'.join(word[:6] for word in words)
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
        workspace_name_match = re.search(r'--workspace-name\s+([^\s]+)', task_description)
        if workspace_name_match:
            workspace_config["workspace_name"] = workspace_name_match.group(1)

        # Extract workspace root
        workspace_root_match = re.search(r'--workspace-root\s+([^\s]+)', task_description)
        if workspace_root_match:
            workspace_config["workspace_root"] = workspace_root_match.group(1)

        # Extract PR number from workspace name if it follows tmux-pr pattern
        if "workspace_name" in workspace_config:
            pr_match = re.search(r'tmux-pr(\d+)', workspace_config["workspace_name"])
            if pr_match:
                workspace_config["pr_number"] = pr_match.group(1)

        return workspace_config if workspace_config else None

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
                print(
                    "🤔 Ambiguous PR reference detected. Agent will ask for clarification."
                )
                return None, "update"  # Signal update mode but need clarification

        return None, "create"

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
            current_branch = (
                branch_result.stdout.strip() if branch_result.returncode == 0 else None
            )

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

    def broadcast_task_to_a2a(
        self, task_description: str, requirements: list[str] | None = None
    ) -> str | None:
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

    def analyze_task_and_create_agents(self, task_description: str) -> list[dict]:
        """Create appropriate agent for the given task with PR context awareness."""
        print("\n🧠 Processing task request...")

        # Extract workspace configuration if present
        workspace_config = self._extract_workspace_config(task_description)
        if workspace_config:
            print(f"🏗️ Extracted workspace config: {workspace_config}")

        # Detect PR context
        pr_number, mode = self._detect_pr_context(task_description)

        # Show user what was detected
        if mode == "update":
            if pr_number:
                print(
                    f"\n🔍 Detected PR context: #{pr_number} - Agent will UPDATE existing PR"
                )
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
                print(
                    "   Agent will check for recent PRs and ask for clarification if needed"
                )
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
                shell=False
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
            workspace_config = agent_spec.get('workspace_config', {})

            # Check if custom workspace_root is specified
            if 'workspace_root' in workspace_config:
                workspace_root = workspace_config['workspace_root']
                # If workspace_name is also specified, use it
                if 'workspace_name' in workspace_config:
                    agent_dir = os.path.join(workspace_root, workspace_config['workspace_name'])
                else:
                    agent_name = agent_spec.get('name', 'agent')
                    agent_dir = os.path.join(workspace_root, agent_name)
                return self._expand_path(agent_dir)

            # Check if custom workspace_name is specified
            if 'workspace_name' in workspace_config:
                base_path = self._get_worktree_base_path()
                self._ensure_directory_exists(base_path)
                agent_dir = os.path.join(base_path, workspace_config['workspace_name'])
                return self._expand_path(agent_dir)

            # Default case: ~/projects/orch_{repo_name}/{agent_name}
            base_path = self._get_worktree_base_path()
            self._ensure_directory_exists(base_path)
            agent_name = agent_spec.get('name', 'agent')
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
                shell=False
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

        # Handle workspace name alignment - if workspace config specifies a name, use it
        if workspace_config and workspace_config.get("workspace_name"):
            agent_name = workspace_config["workspace_name"]
            print(f"🔄 Aligning agent name: {original_agent_name} → {agent_name} (workspace alignment)")
        else:
            agent_name = original_agent_name

        # Clean up any existing stale prompt files for this agent to prevent task reuse
        # Use final agent name for cleanup (after workspace alignment)
        self._cleanup_stale_prompt_files(agent_name)

        # Refresh actively working agents count from tmux sessions (excludes idle agents)
        self.active_agents = self._get_active_tmux_agents()

        # Check concurrent active agent limit
        if len(self.active_agents) >= MAX_CONCURRENT_AGENTS:
            print(
                f"❌ Active agent limit reached ({MAX_CONCURRENT_AGENTS} max). Cannot create {agent_name}"
            )
            print(f"   Currently working agents: {sorted(self.active_agents)}")
            return False

        # Initialize A2A protocol integration if available
        # File-based A2A protocol is always available
        print(f"📁 File-based A2A protocol available for {agent_name}")

        try:
            # Find Claude
            claude_path = shutil.which("claude") or ""
            if not claude_path:
                claude_path = self._ensure_mock_claude_binary()
            if not claude_path:
                return False

            # Create worktree for agent using new location logic
            try:
                branch_name = f"{agent_name}-work"
                agent_dir, git_result = self._create_worktree_at_location(agent_spec, branch_name)

                # Update agent_name if workspace_name was specified for consistency
                workspace_config = agent_spec.get("workspace_config", {})
                if workspace_config.get("workspace_name"):
                    agent_name = workspace_config["workspace_name"]

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

            # Create result collection file
            result_file = os.path.join(self.result_dir, f"{agent_name}_results.json")

            # Enhanced prompt with completion enforcement
            # Determine if we're in PR update mode
            pr_context = agent_spec.get("pr_context", {})
            is_update_mode = pr_context and pr_context.get("mode") == "update"

            if is_update_mode:
                completion_instructions = f"""
🚨 MANDATORY COMPLETION STEPS FOR PR UPDATE:

1. Complete the assigned task on the existing PR branch
2. Commit and push your changes:

   git add -A
   git commit -m "Update PR #{pr_context.get("pr_number", "unknown")}: {agent_focus}

   Agent: {agent_name}
   Task: {agent_focus}

   🤖 Generated with [Claude Code](https://claude.ai/code)

   Co-Authored-By: Claude <noreply@anthropic.com>"

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

   🤖 Generated with [Claude Code](https://claude.ai/code)

   Co-Authored-By: Claude <noreply@anthropic.com>"

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
            prompt_file = os.path.join("/tmp", f"agent_prompt_{agent_name}.txt")
            with open(prompt_file, "w") as f:
                f.write(full_prompt)

            # Create log directory
            log_dir = "/tmp/orchestration_logs"
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, f"{agent_name}.log")

            # Determine if this is a restart or first run
            continue_flag = ""
            conversation_file = (
                f"{os.path.expanduser('~')}/.claude/conversations/{agent_name}.json"
            )
            if (
                os.path.exists(conversation_file)
                or os.environ.get("CLAUDE_RESTART", "false") == "true"
            ):
                continue_flag = "--continue"
                print(f"🔄 {agent_name}: Continuing existing conversation")
            else:
                print(f"🆕 {agent_name}: Starting new conversation")

            claude_cmd = f"{claude_path} --model sonnet -p @{prompt_file} --output-format stream-json --verbose {continue_flag} --dangerously-skip-permissions"

            # Enhanced bash command with error handling and logging
            bash_cmd = f'''
# Signal handler to log interruptions
trap 'echo "[$(date)] Agent interrupted with signal SIGINT" | tee -a {log_file}; exit 130' SIGINT
trap 'echo "[$(date)] Agent terminated with signal SIGTERM" | tee -a {log_file}; exit 143' SIGTERM

echo "[$(date)] Starting agent {agent_name}" | tee -a {log_file}
echo "[$(date)] Working directory: {agent_dir}" | tee -a {log_file}
echo "[$(date)] Executing: {claude_cmd}" | tee -a {log_file}
echo "[$(date)] SAFETY: stdin redirected to /dev/null to prevent keyboard interference" | tee -a {log_file}

# Run claude with stdin redirected to prevent accidental input
{claude_cmd} < /dev/null 2>&1 | tee -a {log_file}
CLAUDE_EXIT=$?

echo "[$(date)] Claude exit code: $CLAUDE_EXIT" | tee -a {log_file}

if [ $CLAUDE_EXIT -eq 0 ]; then
    echo "[$(date)] Agent completed successfully" | tee -a {log_file}
    echo '{{"agent": "{agent_name}", "status": "completed", "exit_code": 0}}' > {result_file}
else
    echo "[$(date)] Agent failed with exit code $CLAUDE_EXIT" | tee -a {log_file}
    echo '{{"agent": "{agent_name}", "status": "failed", "exit_code": '$CLAUDE_EXIT'}}' > {result_file}
fi

# Keep session alive for 1 hour for monitoring and debugging
echo "[$(date)] Agent execution completed. Session remains active for monitoring."
echo "[$(date)] Session will auto-close in 1 hour. Check log at: {log_file}"
echo "[$(date)] Monitor with: tmux attach -t {agent_name}"
sleep {AGENT_SESSION_TIMEOUT_SECONDS}
'''

            script_path = Path("/tmp") / f"{agent_name}_run.sh"
            script_path.write_text(bash_cmd, encoding="utf-8")
            os.chmod(script_path, 0o700)

            # Use agent-specific tmux config for 1-hour sessions
            tmux_config = get_tmux_config_path()

            # Build tmux command with optional config file
            tmux_cmd = ["tmux"]
            if os.path.exists(tmux_config):
                tmux_cmd.extend(["-f", tmux_config])
            else:
                print(
                    f"⚠️ Warning: tmux config file not found at {tmux_config}, using default config"
                )

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

            result = subprocess.run(
                tmux_cmd, check=False, capture_output=True, text=True, timeout=30
            )
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
            _is_truthy(os.environ.get(env_var))
            for env_var in ("MOCK_SERVICES_MODE", "TESTING", "FAST_TESTS")
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
