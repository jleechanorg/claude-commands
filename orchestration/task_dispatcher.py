#!/usr/bin/env python3
"""
Simplified Task Dispatcher for Multi-Agent Orchestration
Handles dynamic agent creation without complex task categorization
"""

import glob
import json
import os
import subprocess
import time
from datetime import datetime
from typing import Any, Dict, List


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

    def analyze_task_and_create_agents(self, task_description: str) -> List[Dict]:
        """Create appropriate agent for the given task."""
        print("\n🧠 Processing task request...")
        
        # Use the same unique name generation as other methods
        agent_name = self._generate_unique_name("task-agent")
        
        # Get default capabilities from discovery method
        capabilities = list(self.agent_capabilities.keys())
        
        # Always create a general development agent that can handle any task
        # The agent itself will understand what to do based on the task description
        return [{
            "name": agent_name,
            "type": "development",
            "focus": task_description,
            "capabilities": capabilities,
            "prompt": f"""Task: {task_description}

Execute the task exactly as requested. Key points:
- If asked to start a server, start it on the specified port
- If asked to modify files, make those exact modifications
- If asked to run commands, execute them
- If asked to test, run the appropriate tests
- Always follow the specific instructions given

Complete the task, then use /pr to create a pull request."""
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