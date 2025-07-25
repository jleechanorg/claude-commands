#!/usr/bin/env python3
"""
Simplified Task Dispatcher for Multi-Agent Orchestration
Handles dynamic agent creation without complex task categorization
"""

import glob
import json
import os
import re
import subprocess
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


# Production safety limits
MAX_CONCURRENT_AGENTS = 5


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
        except:
            pass
            
        # Check worktrees  
        try:
            workspaces = glob.glob("agent_workspace_*")
            for ws in workspaces:
                agent_name = ws.replace("agent_workspace_", "")
                existing.add(agent_name)
        except Exception as e:
            # Log specific error for debugging
            print(f"Warning: Failed to check existing workspaces: {e}")
            
        return existing

    def _generate_unique_name(self, base_name: str, role_suffix: str = "") -> str:
        """Generate unique agent name with collision detection."""
        # Use microsecond precision for better uniqueness
        timestamp = int(time.time() * 1000000) % 100000000  # 8 digits from microseconds
        
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

    def _detect_pr_context(self, task_description: str) -> Tuple[Optional[str], str]:
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
    
    def _find_recent_pr(self) -> Optional[str]:
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

    def analyze_task_and_create_agents(self, task_description: str) -> List[Dict]:
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
- Your commits will automatically update the PR"""
            else:
                prompt = f"""Task: {task_description}

🔄 PR UPDATE MODE - You need to update an existing PR

The user referenced "the PR" but didn't specify which one. You must:
1. List recent PRs: gh pr list --author @me --limit 5
2. Identify which PR the user meant based on the task context
3. If unclear, show the PRs and ask: "Which PR should I update? Please specify the PR number."
4. Once identified, checkout that PR's branch and make the requested changes
5. DO NOT create a new PR"""
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

Complete the task, then use /pr to create a new pull request."""
        
        return [{
            "name": agent_name,
            "type": "development",
            "focus": task_description,
            "capabilities": capabilities,
            "pr_context": {"mode": mode, "pr_number": pr_number} if mode == 'update' else None,
            "prompt": prompt
        }]

    def create_dynamic_agent(self, agent_spec: Dict) -> bool:
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
        message_broker = None
        try:
            # Try to import and initialize message broker for A2A protocol
            import sys
            sys.path.insert(0, self.orchestration_dir)
            from message_broker import MessageBroker
            message_broker = MessageBroker()
            print(f"✅ A2A protocol available for {agent_name}")
        except Exception as e:
            print(f"⚠️ A2A protocol unavailable for {agent_name}: {e}")
            message_broker = None
        
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
            full_prompt = f"""{agent_prompt}

Agent Configuration:
- Name: {agent_name}
- Type: {agent_type}
- Focus: {agent_focus}
- Capabilities: {', '.join(capabilities)}
- Working Directory: {agent_dir}
- Branch: {branch_name} (fresh from main)

🚨 CRITICAL: You are starting with a FRESH BRANCH from main
- Your branch contains ONLY the main branch code
- Make ONLY the changes needed for this specific task
- Do NOT include unrelated changes

🚨 MANDATORY COMPLETION STEPS - DO NOT SKIP:

1. Complete the assigned task
2. When done, use the /pr command to create a pull request:
   
   /pr
   
   This will automatically:
   - Stage and commit all changes
   - Push the branch to origin
   - Create a properly formatted PR
   
   If /pr fails for any reason, fall back to manual commands:
   
   # Stage and commit all changes
   git add -A
   git commit -m "Complete {agent_focus}
   
   Agent: {agent_name}
   Task: {agent_focus}
   
   🤖 Generated with [Claude Code](https://claude.ai/code)
   
   Co-Authored-By: Claude <noreply@anthropic.com>"
   
   # Push the branch
   git push -u origin {branch_name}
   
   # Create the PR (REQUIRED - DO NOT SKIP)
   gh pr create --title "Agent {agent_name}: {agent_focus}" \\
     --body "## Summary
   Agent {agent_name} completed task: {agent_focus}
   
   ## Changes
   [List changes made]
   
   ## Test Plan
   [Describe testing if applicable]
   
   Auto-generated by orchestration system
   
   🤖 Generated with [Claude Code](https://claude.ai/code)
   
   Co-Authored-By: Claude <noreply@anthropic.com>"
   
   # Verify PR was created
   gh pr view --json number,url || echo "ERROR: PR creation failed!"
   
3. Create completion report:
   echo '{{"agent": "{agent_name}", "status": "completed", "branch": "{branch_name}"}}' > {result_file}

🛑 EXIT CRITERIA - AGENT MUST NOT TERMINATE UNTIL:
1. ✓ Task completed and tested
2. ✓ All changes committed
3. ✓ Branch pushed to origin
4. ✓ Pull Request created successfully (verify with gh pr view)
5. ✓ Completion report written to {result_file}

❌ FAILURE TO CREATE PR = INCOMPLETE TASK
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

# Keep session alive for debugging
echo "[$(date)] Session ending. Check log at: {log_file}"
echo "Session will close in 5 seconds (stdin redirected, no keyboard input)..."
sleep 5
'''
            
            tmux_cmd = [
                "tmux", "new-session", "-d", "-s", agent_name,
                "-c", agent_dir, "bash", "-c", bash_cmd
            ]
            
            result = subprocess.run(tmux_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"⚠️ Error creating tmux session: {result.stderr}")
                return False
            
            # Register agent with A2A protocol if available
            if message_broker:
                try:
                    message_broker.register_agent(
                        agent_name,
                        agent_type,
                        capabilities
                    )
                    print(f"📡 Registered {agent_name} with A2A protocol")
                except Exception as e:
                    print(f"⚠️ Failed to register {agent_name} with A2A: {e}")
            
            print(f"✅ Created {agent_name} - Focus: {agent_focus}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create {agent_name}: {e}")
            return False


if __name__ == "__main__":
    # Simple test mode - create single agent
    dispatcher = TaskDispatcher()
    print("Task Dispatcher ready for dynamic agent creation")