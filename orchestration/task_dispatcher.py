#!/usr/bin/env python3
"""
A2A-Enhanced Task Dispatcher for Multi-Agent Orchestration
Handles dynamic agent creation with Agent-to-Agent communication support
"""

import glob
import json
import os
import re
import subprocess
import time
from datetime import datetime
from typing import Any

# Import A2A components
try:
    from a2a_integration import TaskPool, get_a2a_status
    from a2a_monitor import get_monitor
    A2A_AVAILABLE = True
except ImportError:
    A2A_AVAILABLE = False

# Constraint system removed - using simple safety rules only

# Constants
TIMESTAMP_MODULO = 100000000  # 8 digits from microseconds for unique name generation
AGENT_SESSION_TIMEOUT_SECONDS = 86400  # 24 hours

# Production safety limits
MAX_CONCURRENT_AGENTS = 5

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
        # Dynamic agent capabilities - agents register their own capabilities
        # This allows agents to determine what they can handle based on task content
        self.agent_capabilities = self._discover_agent_capabilities()

        # LLM-driven enhancements
        self.active_agents = set()  # Track active agent names for collision detection
        self.result_dir = "/tmp/orchestration_results"
        os.makedirs(self.result_dir, exist_ok=True)

        # A2A Integration
        self.a2a_enabled = A2A_AVAILABLE
        if self.a2a_enabled:
            self.task_pool = TaskPool()
            print("A2A task broadcasting enabled")
        else:
            print("A2A not available - running in legacy mode")

        # Basic safety rules only - no constraint system needed

        # All tasks are now dynamic - no static loading needed

    def _discover_agent_capabilities(self) -> dict:
        """Discover agent capabilities dynamically from registered agents"""
        # Default capabilities that all agents should have
        default_capabilities = {
            "task_execution": "Execute assigned development tasks",
            "command_acceptance": "Accept and process commands",
            "status_reporting": "Report task progress and completion status",
            "git_operations": "Perform git operations (commit, push, PR creation)",
            "development": "General software development capabilities",
            "testing": "Run and debug tests",
            "server_management": "Start/stop servers and services"
        }

        # In production, this would query Redis for registered agents
        # and their self-reported capabilities, merged with defaults
        return default_capabilities


    # =================== LLM-DRIVEN ENHANCEMENTS ===================

    def _check_existing_agents(self) -> set:
        """Check for existing tmux sessions and worktrees to avoid collisions."""
        existing = set()

        # Check tmux sessions
        try:
            result = subprocess.run(
                ["tmux", "list-sessions", "-F", "#{session_name}"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                existing.update(result.stdout.strip().split('\n'))
        except subprocess.SubprocessError:
            pass

        # Check worktrees
        try:
            workspaces = glob.glob("agent_workspace_*")
            for ws in workspaces:
                agent_name = ws.replace("agent_workspace_", "")
                existing.add(agent_name)
        except Exception as e:
            # Log specific error for debugging
            print(f"Warning: Failed to check existing workspaces due to error: {e}")

        return existing

    def _generate_unique_name(self, base_name: str, role_suffix: str = "") -> str:
        """Generate unique agent name with collision detection."""
        # Use microsecond precision for better uniqueness
        timestamp = int(time.time() * 1000000) % TIMESTAMP_MODULO  # 8 digits from microseconds

        # Get existing agents
        existing = self._check_existing_agents()
        existing.update(self.active_agents)

        # Try base name with timestamp
        if role_suffix:
            candidate = f"{base_name}-{role_suffix}-{timestamp}"
        else:
            candidate = f"{base_name}-{timestamp}"

        # If collision, increment until unique
        counter = 1
        original_candidate = candidate
        while candidate in existing:
            candidate = f"{original_candidate}-{counter}"
            counter += 1

        self.active_agents.add(candidate)
        return candidate

    def _detect_pr_context(self, task_description: str) -> tuple[str | None, str]:
        """Detect if task is about updating an existing PR.
        Returns: (pr_number, mode) where mode is 'update' or 'create'
        """
        # Patterns that indicate PR update mode
        pr_update_patterns = [
            # Action + anything + PR number
            r'(?:fix|adjust|update|modify|enhance|improve)\s+.*?(?:PR|pull request)\s*#?(\d+)',
            # PR number + needs/should/must
            r'PR\s*#?(\d+)\s+(?:needs|should|must)',
            # Add/apply to PR number
            r'(?:add|apply)\s+.*?to\s+(?:PR|pull request)\s*#?(\d+)',
            # Direct PR number reference
            r'(?:PR|pull request)\s*#(\d+)',
        ]

        # Check for explicit PR number
        for pattern in pr_update_patterns:
            match = re.search(pattern, task_description, re.IGNORECASE)
            if match:
                pr_number = match.group(1)
                return pr_number, 'update'

        # Check for contextual PR reference without number
        contextual_patterns = [
            r'(?:the|that|this)\s+PR',
            r'(?:the|that)\s+pull\s+request',
            r'existing\s+PR',
            r'current\s+(?:PR|pull request)'
        ]

        for pattern in contextual_patterns:
            if re.search(pattern, task_description, re.IGNORECASE):
                # Try to find recent PR from current branch or user
                recent_pr = self._find_recent_pr()
                if recent_pr:
                    return recent_pr, 'update'
                else:
                    print("🤔 Ambiguous PR reference detected. Agent will ask for clarification.")
                    return None, 'update'  # Signal update mode but need clarification

        return None, 'create'

    def _find_recent_pr(self) -> str | None:
        """Try to find a recent PR from current branch or user."""
        try:
            # Try to get PR from current branch
            # Get current branch name first for better readability
            branch_result = subprocess.run(
                ['git', 'branch', '--show-current'],
                capture_output=True, text=True
            )
            current_branch = branch_result.stdout.strip() if branch_result.returncode == 0 else None

            if current_branch:
                result = subprocess.run(
                    ['gh', 'pr', 'list', '--head', current_branch, '--json', 'number', '--limit', '1'],
                    capture_output=True, text=True
                )
                if result.returncode == 0 and result.stdout.strip():
                    data = json.loads(result.stdout)
                    if data:
                        return str(data[0]['number'])

            # Fallback: get most recent PR by current user
            result = subprocess.run(
                ['gh', 'pr', 'list', '--author', '@me', '--json', 'number', '--limit', '1'],
                capture_output=True, text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout)
                if data:
                    return str(data[0]['number'])
        except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError) as e:
            # Silently handle errors as this is a fallback mechanism
            pass

        return None

    def broadcast_task_to_a2a(self, task_description: str, requirements: list[str] | None = None) -> str | None:
        """Broadcast task to A2A system for agent claiming"""
        if not self.a2a_enabled:
            return None

        try:
            task_id = self.task_pool.publish_task(
                task_id=f"orch-{int(time.time() * 1000000) % TIMESTAMP_MODULO}",
                task_description=task_description,
                requirements=requirements or []
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
            # Get overall A2A status
            status = get_a2a_status()

            # Get monitor health
            monitor = get_monitor()
            health = monitor.get_system_health()

            return {
                "a2a_enabled": True,
                "system_status": status,
                "health": health,
                "timestamp": time.time()
            }
        except Exception as e:
            return {
                "a2a_enabled": True,
                "error": str(e),
                "timestamp": time.time()
            }

    def analyze_task_and_create_agents(self, task_description: str) -> list[dict]:
        """Create appropriate agent for the given task with PR context awareness."""
        print("\n🧠 Processing task request...")

        # Detect PR context
        pr_number, mode = self._detect_pr_context(task_description)

        # Show user what was detected
        if mode == 'update':
            if pr_number:
                print(f"\n🔍 Detected PR context: #{pr_number} - Agent will UPDATE existing PR")
                # Get PR details for better context
                try:
                    result = subprocess.run(
                        ['gh', 'pr', 'view', pr_number, '--json', 'title,state,headRefName'],
                        capture_output=True, text=True
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
        agent_name = self._generate_unique_name("task-agent")

        # Get default capabilities from discovery method
        capabilities = list(self.agent_capabilities.keys())

        # Build appropriate prompt based on mode
        if mode == 'update':
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

        return [{
            "name": agent_name,
            "type": "development",
            "focus": task_description,
            "capabilities": capabilities,
            "pr_context": {"mode": mode, "pr_number": pr_number} if mode == 'update' else None,
            "prompt": prompt
        }]


    def create_dynamic_agent(self, agent_spec: dict) -> bool:
        """Create agent with enhanced Redis coordination and worktree management."""
        agent_name = agent_spec.get("name")
        agent_focus = agent_spec.get("focus", "general task completion")
        agent_prompt = agent_spec.get("prompt", "Complete the assigned task")
        agent_type = agent_spec.get("type", "general")
        capabilities = agent_spec.get("capabilities", [])

        # Check concurrent agent limit
        if len(self.active_agents) >= MAX_CONCURRENT_AGENTS:
            print(f"⚠️ Agent limit reached ({MAX_CONCURRENT_AGENTS} max). Cannot create {agent_name}")
            return False

        # Initialize A2A protocol integration if available
        # File-based A2A protocol is always available
        print(f"📁 File-based A2A protocol available for {agent_name}")

        try:
            # Find Claude
            claude_path = subprocess.run(
                ["which", "claude"], capture_output=True, text=True
            ).stdout.strip()
            if not claude_path:
                return False

            # Create worktree for agent (inherit from current branch)
            current_dir = os.getcwd()
            agent_dir = os.path.join(current_dir, f"agent_workspace_{agent_name}")
            branch_name = f'{agent_name}-work'

            # Always create fresh branch from main (equivalent to /nb)
            # This prevents inheriting unrelated changes from current branch
            subprocess.run([
                'git', 'worktree', 'add', '-b', branch_name,
                agent_dir, 'main'
            ], capture_output=True)

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
   git commit -m "Update PR #{pr_context.get('pr_number', 'unknown')}: {agent_focus}

   Agent: {agent_name}
   Task: {agent_focus}

   🤖 Generated with [Claude Code](https://claude.ai/code)

   Co-Authored-By: Claude <noreply@anthropic.com>"

   git push

3. Verify the PR was updated (if PR number exists):
   {f"gh pr view {pr_context.get('pr_number')} --json state,mergeable" if pr_context.get('pr_number') else "echo 'No PR number provided, skipping verification'"}

4. Create completion report:
   echo '{{"agent": "{agent_name}", "status": "completed", "pr_updated": "{pr_context.get('pr_number', 'none')}"}}' > {result_file}

🛑 EXIT CRITERIA - AGENT MUST NOT TERMINATE UNTIL:
1. ✓ Task completed and tested
2. ✓ All changes committed and pushed
3. ✓ PR #{pr_context.get('pr_number', 'unknown')} successfully updated
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
- Capabilities: {', '.join(capabilities)}
- Working Directory: {agent_dir}
- Branch: {branch_name} {'(updating existing PR)' if is_update_mode else '(fresh from main)'}

🚨 CRITICAL: {'You are updating an EXISTING PR' if is_update_mode else 'You are starting with a FRESH BRANCH from main'}
- {'Work on the existing PR branch' if is_update_mode else 'Your branch contains ONLY the main branch code'}
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
            conversation_file = f"{os.path.expanduser('~')}/.claude/conversations/{agent_name}.json"
            if os.path.exists(conversation_file) or os.environ.get('CLAUDE_RESTART', 'false') == 'true':
                continue_flag = "--continue"
                print(f"🔄 {agent_name}: Continuing existing conversation")
            else:
                print(f"🆕 {agent_name}: Starting new conversation")

            claude_cmd = f'{claude_path} --model sonnet -p @{prompt_file} --output-format stream-json --verbose {continue_flag} --dangerously-skip-permissions'

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

# Keep session alive for 24 hours for monitoring and debugging
echo "[$(date)] Agent execution completed. Session remains active for monitoring."
echo "[$(date)] Session will auto-close in 24 hours. Check log at: {log_file}"
echo "[$(date)] Monitor with: tmux attach -t {agent_name}"
sleep {AGENT_SESSION_TIMEOUT_SECONDS}
'''

            # Use agent-specific tmux config for 24-hour sessions
            tmux_config = get_tmux_config_path()

            # Build tmux command with optional config file
            tmux_cmd = ["tmux"]
            if os.path.exists(tmux_config):
                tmux_cmd.extend(["-f", tmux_config])
            else:
                print(f"⚠️ Warning: tmux config file not found at {tmux_config}, using default config")

            tmux_cmd.extend([
                "new-session", "-d", "-s", agent_name,
                "-c", agent_dir, "bash", "-c", bash_cmd
            ])

            result = subprocess.run(tmux_cmd, capture_output=True, text=True)
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



if __name__ == "__main__":
    # Simple test mode - create single agent
    dispatcher = TaskDispatcher()
    print("Task Dispatcher ready for dynamic agent creation")
