#!/usr/bin/env python3
"""
/orchestrate - Claude-Driven Agent Orchestration

How it works:
1. You describe a task to Claude (me)
2. I analyze the task and create a detailed agent plan
3. I input the specific agents I want created via this script
4. This script executes my plan by launching the agents I specified

No fake intelligence - I'M the intelligence, this is just the executor.
"""

import os
import subprocess
import sys

# Add orchestration directory to path
orchestration_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "orchestration",
)
sys.path.insert(0, orchestration_path)

# Claude provides the intelligence - no fake NLP parsers needed
# This script just executes the agent plans that Claude creates


class OrchestrationCLI:
    """Claude Code CLI integration for orchestration system."""

    def __init__(self):
        # No fake parsers or planners - Claude is the real intelligence
        self.broker = None

    def is_orchestration_running(self) -> bool:
        """Check if orchestration system is running."""
        try:
            # Basic orchestration just needs tmux (Redis is optional)
            result = subprocess.run(
                ["tmux", "list-sessions"], capture_output=True, text=True, timeout=5
            )
            # Even if no sessions exist, tmux is available so orchestration can work
            return True

        except Exception:
            return False

    def start_orchestration_system(self) -> bool:
        """Start the orchestration system."""
        try:
            print("🚀 Starting orchestration system...")
            script_path = os.path.join(orchestration_path, "start_system.sh")
            result = subprocess.run(
                [script_path, "start"], capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                print("✅ Orchestration system started successfully")
                return True
            else:
                print(f"❌ Failed to start orchestration system: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Error starting orchestration system: {e}")
            return False

    def connect_to_broker(self) -> bool:
        """Connect to the message broker (optional for basic functionality)."""
        try:
            # For now, skip Redis connection - agents work without it
            # In future, Redis could enable inter-agent coordination
            print("📡 Skipping Redis connection - agents work independently")
            self.broker = None
            return True
        except Exception as e:
            print(f"❌ Failed to connect to message broker: {e}")
            return False

    def execute_orchestration_command(self, command: str) -> str:
        """Execute orchestration-specific command using simple string matching."""
        command_lower = command.lower()

        if any(word in command_lower for word in ["status", "check", "what"]):
            return self._check_status()
        elif any(word in command_lower for word in ["help", "how", "?"]):
            return self._show_help()
        elif any(word in command_lower for word in ["monitor", "watch"]):
            return self._monitor_agents()
        elif any(word in command_lower for word in ["connect", "attach"]):
            return self._connect_to_agent_simple(command)
        # Note: cleanup and terminate commands not yet implemented
        else:
            # Default to task delegation - Claude analyzed the task already
            return self._delegate_task(command)

    def _delegate_task(self, task_description: str) -> str:
        """Execute Claude's agent plan for the given task."""
        if not task_description:
            return "❌ Please specify what you want me to build or create."

        print("🤖 **Claude's Agent Orchestration Plan**")
        print("=" * 50)
        print(f"📋 Task: {task_description}")
        print()
        print("🧠 **Claude's Analysis & Agent Strategy:**")
        print("The real intelligence happened when you described this task to Claude.")
        print(
            "Claude analyzed the requirements and decided on the optimal agent approach."
        )
        print("This script is now executing Claude's agent plan.")
        print()

        # Get current branch to pass to agent creation
        current_branch_result = subprocess.run(
            ["git", "branch", "--show-current"], capture_output=True, text=True
        )
        current_branch = (
            current_branch_result.stdout.strip()
            if current_branch_result.returncode == 0
            else "main"
        )

        # Create a simple agent to handle this task
        import time

        agent_name = f"task-agent-{int(time.time()) % 10000}"

        success = self._create_simple_agent(
            agent_name, task_description, current_branch
        )

        if success:
            agent_workspace = f"agent_workspace_{agent_name}"
            return f"""✅ Agent created and working on your task!

🤖 Agent: {agent_name}
📋 Task: {task_description}
🏢 Agent workspace: ./{agent_workspace}/
🌿 Agent will create clean branch from main in its workspace
🏠 You remain on: {current_branch} in current directory

🔗 Connect to monitor progress:
   tmux attach -t {agent_name}

💡 The agent will work autonomously in its isolated workspace.
📂 Workspace: {os.path.join(os.getcwd(), agent_workspace)}
📝 Note: Agent works in its own directory copy - your work is unaffected"""
        else:
            return "❌ Failed to create agent. Check that tmux and Claude CLI are available."

    def _create_simple_agent(
        self, agent_name: str, task_description: str, current_branch: str
    ) -> bool:
        """Create a simple Claude agent in a tmux session."""
        try:
            # Find Claude executable
            import subprocess

            claude_path = subprocess.run(
                ["which", "claude"], capture_output=True, text=True
            ).stdout.strip()
            if not claude_path:
                return False

            # Clean up any existing session
            subprocess.run(
                ["tmux", "kill-session", "-t", agent_name], capture_output=True
            )

            # Create agent working directory as subdir of current worktree
            current_dir = os.getcwd()
            agent_dir = os.path.join(current_dir, f"agent_workspace_{agent_name}")

            # Create fresh worktree from main branch for agent
            # First create the directory
            os.makedirs(agent_dir, exist_ok=True)

            # Create a git worktree from main branch
            worktree_result = subprocess.run(
                ["git", "worktree", "add", agent_dir, "main"],
                capture_output=True,
                text=True,
                cwd=current_dir,
            )
            if worktree_result.returncode != 0:
                # Fallback: copy current directory but checkout main
                subprocess.run(
                    ["cp", "-r", current_dir, f"{agent_dir}_temp"], capture_output=True
                )
                subprocess.run(
                    ["mv", f"{agent_dir}_temp", agent_dir], capture_output=True
                )
                subprocess.run(
                    ["git", "checkout", "main"], capture_output=True, cwd=agent_dir
                )

            # Build task instruction
            task_instruction = self._build_task_instruction(
                task_description, current_branch, agent_dir
            )

            # Use claude -p with stream-json for proper headless execution with visible output
            claude_cmd = f'{claude_path} -p "{task_instruction}" --output-format stream-json --verbose --dangerously-skip-permissions'

            # Create tmux session with proper headless Claude execution
            tmux_cmd = [
                "tmux",
                "new-session",
                "-d",
                "-s",
                agent_name,
                "-c",
                agent_dir,
                "bash",
                "-c",
                f'echo "🤖 {agent_name} starting with claude -p..."; echo "Task: {task_description}"; echo ""; {claude_cmd}; echo "Task completed"; exec bash',
            ]

            result = subprocess.run(tmux_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return False
            return True

        except Exception:
            return False

    def _build_task_instruction(
        self, task_description: str, current_branch: str, agent_dir: str
    ) -> str:
        """Build the complete task instruction for the agent."""
        return f"""I need you to complete this specific task: {task_description}

WORKING ENVIRONMENT:
- You are working in your own dedicated worktree: {agent_dir}
- This is a fresh git worktree created from the main branch
- You start on the main branch and should create a new feature branch
- The user remains in their original directory working on: {current_branch}

AUTONOMOUS WORKFLOW:
1. Create a new feature branch: /nb (this will create a new branch from main)
2. Locate the relevant file and make the specific change requested
3. Test that the change works correctly
4. Run tests to ensure nothing breaks: ./run_tests.sh
5. Create a NEW PR when complete: /pr (this will be a separate PR from the user's work)
6. Your PR will be independent of the user's current branch: {current_branch}
6. Task complete - you can exit or wait

IMPORTANT INSTRUCTIONS:
- Work in your dedicated directory: {agent_dir}
- Follow all existing code conventions and patterns
- Run tests before creating your PR: ./run_tests.sh
- Your PR should only contain changes related to your specific focus area
- IGNORE any "/compact" warnings about context - this is a known false positive
- Continue working normally if you see "Context low" messages - they are inaccurate

AUTONOMOUS OPERATION:
- Work autonomously - make decisions and proceed without waiting
- Focus on the specific task only
- Complete the task efficiently without asking for permission

WORKSPACE ISOLATION:
- You work in your own isolated workspace: {agent_dir}
- Create your own feature branch for this specific task
- Your work won't interfere with the user's current work
- The user stays in their original directory on branch: {current_branch}

Begin working on your assigned task now."""

    def _create_specialized_agents(
        self, agent_plan, task_description: str, priority: str
    ) -> list:
        """Create specialized Claude agents with actual autonomous execution - Pure Python."""
        import datetime

        created_agents = []

        for agent_spec in agent_plan.agents:
            agent_name = agent_spec.name

            try:
                # Generate specialized Claude prompt
                claude_prompt = self._generate_agent_prompt(
                    agent_spec, task_description
                )

                # Spawn actual Claude instance in tmux session
                claude_success = self._spawn_claude_agent(agent_spec, claude_prompt)

                if claude_success:
                    # Create specialized task file for monitoring
                    task_file = f"orchestration/tasks/{agent_name}_tasks.txt"
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    task_entry = (
                        f"[{timestamp}] [{priority.upper()}] AUTONOMOUS CLAUDE AGENT\n"
                        f"Agent: {agent_name}\n"
                        f"Focus: {agent_spec.focus}\n"
                        f"Task: {task_description}\n"
                        f"Responsibilities: {', '.join(agent_spec.responsibilities)}\n"
                        f"Estimated Duration: {agent_spec.estimated_duration}\n"
                        f"Status: ACTIVE - Claude instance running autonomously\n"
                        f"Monitor: tmux attach -t {agent_name}\n"
                        f"{'=' * 50}\n"
                    )

                    with open(task_file, "a") as f:  # Append to preserve existing tasks
                        f.write(task_entry)

                    created_agents.append(
                        {
                            "name": agent_name,
                            "focus": agent_spec.focus,
                            "file": task_file,
                            "status": "ACTIVE",
                        }
                    )

                    print(f"✅ Spawned autonomous Claude agent: {agent_name}")
                else:
                    print(f"❌ Failed to spawn Claude agent: {agent_name}")

            except Exception as e:
                print(f"⚠️ Error creating agent {agent_name}: {e}")

        return created_agents

    def _generate_agent_prompt(self, agent_spec, task_description: str) -> str:
        """Generate specialized Claude prompt for autonomous agent."""
        prompt = f"""You are a {agent_spec.name} - an autonomous AI agent specialized in {agent_spec.focus}.

YOUR MISSION:
{task_description}

YOUR SPECIFIC RESPONSIBILITIES:
{chr(10).join("- " + resp for resp in agent_spec.responsibilities)}

ESTIMATED WORK TIME: {agent_spec.estimated_duration}

AUTONOMOUS WORKFLOW:
1. Start by switching to a new branch: /handoff {agent_spec.name.replace("-", "_")}_work --auto-approve
2. Analyze the task and plan your approach
3. Implement the required changes systematically  
4. Test your implementation thoroughly
5. Create a PR when complete: /pr --auto-approve

WORK CONTEXT:
- You are working autonomously - make decisions and proceed without waiting
- Focus specifically on your responsibilities, coordinate with other agents if needed
- Ensure your changes are focused and don't conflict with other agents' work
- Document your progress and findings clearly

IMPORTANT INSTRUCTIONS:
- Work in the current directory: {os.getcwd()}
- Follow all existing code conventions and patterns
- Run tests before creating your PR: ./run_tests.sh
- Your PR should only contain changes related to your specific focus area
- IGNORE any "/compact" warnings about context - this is a known false positive
- Continue working normally if you see "Context low" messages - they are inaccurate
- NEVER wait for user approval - use --auto-approve flags for all commands
- If you encounter interactive prompts, choose the most reasonable default and proceed

Begin working on your assigned responsibilities now."""
        return prompt

    def _spawn_claude_agent(self, agent_spec, claude_prompt: str) -> bool:
        """Spawn actual Claude Code CLI instance - Pure Python implementation."""
        try:
            # Find Claude executable
            claude_path = os.environ.get(
                "CLAUDE_PATH", "/home/jleechan/.claude/local/claude"
            )
            if not os.path.exists(claude_path):
                # Try alternative locations
                claude_path = subprocess.run(
                    ["which", "claude"], capture_output=True, text=True
                ).stdout.strip()
                if not claude_path:
                    print(
                        "❌ Claude executable not found. Set CLAUDE_PATH or ensure 'claude' is in PATH"
                    )
                    return False

            # Clean up any existing session with the same name
            cleanup_cmd = ["tmux", "kill-session", "-t", agent_spec.name]
            subprocess.run(
                cleanup_cmd, capture_output=True
            )  # Ignore errors if session doesn't exist

            # Create tmux session with Claude in interactive mode
            tmux_cmd = [
                "tmux",
                "new-session",
                "-d",
                "-s",
                agent_spec.name,
                "-c",
                os.getcwd(),
                claude_path,
                "--verbose",
            ]

            result = subprocess.run(
                tmux_cmd, check=True, capture_output=True, text=True
            )

            # Wait a moment for Claude to start
            import time

            time.sleep(2)

            # Send the prompt to the Claude session
            prompt_lines = claude_prompt.split("\\n")
            for line in prompt_lines:
                if line.strip():  # Skip empty lines
                    subprocess.run(
                        ["tmux", "send-keys", "-t", agent_spec.name, line, "Enter"]
                    )
                    time.sleep(0.1)  # Brief pause between lines

            # Verify session was created
            verify_cmd = ["tmux", "has-session", "-t", agent_spec.name]
            subprocess.run(verify_cmd, check=True, capture_output=True)

            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to spawn Claude agent {agent_spec.name}: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error spawning {agent_spec.name}: {e}")
            return False

    def _assign_task_to_agent(self, agent_type: str, task: str, priority: str):
        """Legacy method - assign task to specific Claude agent via task file."""
        import datetime

        task_file = f"orchestration/tasks/{agent_type}_tasks.txt"

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        task_entry = f"[{timestamp}] [{priority.upper()}] {task}\n"

        try:
            with open(task_file, "a") as f:
                f.write(task_entry)
        except Exception as e:
            print(f"Warning: Could not write to {task_file}: {e}")

    def _check_status(self) -> str:
        """Check real Claude agent orchestration system status."""
        try:
            # Check Redis
            redis_status = (
                "✅ Connected"
                if self.broker and self.broker.redis_client.ping()
                else "❌ Disconnected"
            )

            # Check tmux sessions for Claude agents
            tmux_result = subprocess.run(
                ["tmux", "list-sessions"], capture_output=True, text=True
            )
            claude_agents = {}
            if tmux_result.returncode == 0:
                for line in tmux_result.stdout.split("\n"):
                    if line.strip():
                        for agent_name in [
                            "frontend-agent",
                            "backend-agent",
                            "testing-agent",
                            "opus-master",
                        ]:
                            if agent_name in line:
                                parts = line.split(":")
                                if len(parts) >= 2:
                                    session_info = ":".join(parts[1:]).strip()
                                    claude_agents[agent_name] = session_info

            # Check task files and pending tasks
            task_counts = {}
            for agent_type in ["frontend", "backend", "testing"]:
                task_file = f"orchestration/tasks/{agent_type}_tasks.txt"
                try:
                    with open(task_file, "r") as f:
                        lines = f.readlines()
                        task_counts[agent_type] = len([l for l in lines if l.strip()])
                except FileNotFoundError:
                    task_counts[agent_type] = 0

            # Build detailed status
            status = "🎯 **Real Claude Agent Orchestration Status**\n\n"
            status += f"🔄 Redis: {redis_status}\n"
            status += f"🤖 Active Claude Agents: {len(claude_agents)}\n\n"

            # Show Claude agent details
            agent_icons = {
                "frontend-agent": "🎨",
                "backend-agent": "⚙️",
                "testing-agent": "🧪",
                "opus-master": "🎯",
            }

            for agent_name, icon in agent_icons.items():
                if agent_name in claude_agents:
                    status += (
                        f"   {icon} {agent_name.replace('-', ' ').title()}: ✅ ACTIVE\n"
                    )
                    status += f"      └─ Session: {claude_agents[agent_name]}\n"
                    status += f"      └─ Connect: tmux attach -t {agent_name}\n"
                else:
                    status += f"   {icon} {agent_name.replace('-', ' ').title()}: ❌ STOPPED\n"

            # Show task queue status
            status += "\n📋 **Task Queue Status:**\n"
            for agent_type, count in task_counts.items():
                if count > 0:
                    status += f"   📝 {agent_type.title()} tasks: {count} pending\n"
                else:
                    status += f"   ✅ {agent_type.title()} tasks: No pending tasks\n"

            # Show shared status file if available
            try:
                with open("orchestration/tasks/shared_status.txt", "r") as f:
                    shared_status = f.read().strip()
                    if shared_status:
                        status += "\n📊 **Agent Dashboard:**\n"
                        for line in shared_status.split("\n"):
                            if line.strip():
                                status += f"   {line}\n"
            except FileNotFoundError:
                pass

            # Add monitoring commands
            status += "\n💡 **Quick Commands:**\n"
            status += "   • Delegate task: /orch Build user authentication\n"
            status += "   • Connect to Frontend: tmux attach -t frontend-agent\n"
            status += "   • Connect to Backend: tmux attach -t backend-agent\n"
            status += "   • Connect to Testing: tmux attach -t testing-agent\n"
            status += "   • View task files: cat orchestration/tasks/*_tasks.txt\n"
            status += "   • System status: ./orchestration/start_system.sh status\n"

            return status

        except Exception as e:
            return f"❌ Error checking status: {e}"

    def _show_help(self) -> str:
        """Show orchestration help."""
        return """🎯 **Orchestration Commands via Claude Code CLI:**

**Task Delegation:**
   • /orch Build a user authentication system
   • /orch Create a REST API urgently
   • /orch Implement a database schema

**Agent Connection & Collaboration:**
   • /orch connect to sonnet 1
   • /orch how do I connect to agents?
   • /orch collaborate with sonnet-2
   • /orch use claude code cli with agent

**System Monitoring:**
   • /orch What's the status?
   • /orch monitor agents
   • /orch what are agents doing?
   • /orch How's the progress?

**Agent Management:**
   • /orch Spawn a new agent
   • /orch connect agent (shows available agents)

**Natural Language Questions:**
   • /orch help me with connections
   • /orch show me connection options
   • /orch how does this work?
   • /orch what are my monitoring options?

**Priority Keywords:**
   • High: urgent, ASAP, immediately, critical
   • Medium: (default)
   • Low: later, when possible, no rush

**System Commands:**
   • Start: ./orchestration/start_system.sh start
   • Stop: ./orchestration/start_system.sh stop
   • Opus Terminal: tmux attach -t opus-master

**💡 Full Claude Code CLI Integration:**
   • Use /e, /think, /copilot, and ALL other commands
   • Connect directly to agent sessions with full CLI access
   • Read/write files, run git commands, tests, etc.
   • Seamless collaboration between you and AI agents!"""

    def _spawn_agent(self) -> str:
        """Spawn new agent."""
        return (
            "🤖 To spawn new agents, run:\n"
            "   ./orchestration/start_system.sh spawn sonnet\n\n"
            "💡 This will create a new Sonnet agent in a separate tmux session."
        )

    def _check_progress(self) -> str:
        """Check task progress."""
        return (
            "📊 Progress checking via message queues not yet implemented.\n"
            "💡 For now, check individual agent tmux sessions:\n"
            "   tmux list-sessions | grep -E '(opus|sonnet|sub)'"
        )

    def _monitor_agents(self) -> str:
        """Provide agent monitoring commands and tips."""
        return """🔍 **Agent Monitoring Guide:**

**Real-time tmux Monitoring:**
   • List all sessions: tmux list-sessions
   • Connect to Sonnet-1: tmux attach -t sonnet-1
   • Connect to Sonnet-2: tmux attach -t sonnet-2
   • Detach from session: Ctrl+B then D

**Multi-pane Monitoring Setup:**
   • Create monitor session: tmux new-session -d -s monitor
   • Split horizontally: tmux split-window -h -t monitor
   • Watch Sonnet-1: tmux send-keys -t monitor:0.0 'tmux attach -t sonnet-1' Enter
   • Watch Sonnet-2: tmux send-keys -t monitor:0.1 'tmux attach -t sonnet-2' Enter
   • Connect to monitor: tmux attach -t monitor

**Redis Activity Monitoring:**
   • Real-time activity: redis-cli monitor
   • Agent heartbeats: redis-cli keys "agent:*"
   • Task queues: redis-cli keys "queue:*"
   • Agent details: redis-cli get "agent:sonnet-1"

**Quick Status Checks:**
   • /orch What's the status?
   • ./orchestration/start_system.sh status

**Pro Tips:**
   • Use tmux mouse mode: tmux set -g mouse on
   • Scroll in tmux: Ctrl+B then Page Up/Down
   • Find agents: tmux list-sessions | grep sonnet"""

    def _connect_to_agent(self, command: str) -> str:
        """Provide instructions for connecting to a specific agent."""
        # Get available agents
        try:
            active_agents = self.broker.get_active_agents()
            sonnet_agents = [
                agent for agent in active_agents if agent.startswith("sonnet")
            ]

            if not sonnet_agents:
                return (
                    "❌ No Sonnet agents available to connect to.\n"
                    "💡 Start agents with: ./orchestration/start_system.sh spawn sonnet"
                )

            # If user specified an agent, use that; otherwise show options
            target_agent = None
            if command.target:
                # Extract agent number or name from target
                target_lower = command.target.lower()
                if "sonnet" in target_lower:
                    for agent in sonnet_agents:
                        if (
                            agent.lower() in target_lower
                            or target_lower in agent.lower()
                        ):
                            target_agent = agent
                            break
                elif target_lower.isdigit():
                    target_agent = f"sonnet-{target_lower}"
                    if target_agent not in sonnet_agents:
                        target_agent = None

            if target_agent and target_agent in sonnet_agents:
                return f"""🔗 **Connecting to {target_agent}:**

**Direct Connection:**
   tmux attach -t {target_agent}

**Collaborative Setup:**
   # Create shared session with {target_agent}
   tmux new-session -d -s collaborate-{target_agent}
   tmux split-window -h -t collaborate-{target_agent}
   
   # Your Claude Code CLI
   tmux send-keys -t collaborate-{target_agent}:0.0 'cd $(pwd) && claude' Enter
   
   # {target_agent} session
   tmux send-keys -t collaborate-{target_agent}:0.1 'tmux attach -t {target_agent}' Enter
   
   # Connect to collaborative session
   tmux attach -t collaborate-{target_agent}

**Inside the {target_agent} session you can:**
   • See what the agent is currently working on
   • Run any Claude Code CLI commands (/e, /think, /testui, etc.)
   • Use all your slash commands  
   • Work collaboratively with the Sonnet agent
   • Take over tasks or provide guidance

**Detach from session:** Ctrl+B then D
"""
            else:
                # Show available agents
                result = "🤖 **Available Sonnet Agents:**\n\n"
                for i, agent in enumerate(sonnet_agents, 1):
                    result += f"   {i}. {agent}\n"
                    result += f"      └─ Connect: tmux attach -t {agent}\n\n"

                result += "💡 **Usage examples:**\n"
                result += "   • /orch connect to sonnet 1\n"
                result += "   • /orch connect to sonnet-2\n"
                result += "   • /orch connect agent\n"

                return result

        except Exception as e:
            return f"❌ Error connecting to agent: {e}"

    def _connect_to_agent_simple(self, user_input: str) -> str:
        """Simple agent connection without ParsedCommand."""
        try:
            # Get available tmux sessions with 'agent' in name
            result = subprocess.run(
                ["tmux", "list-sessions"], capture_output=True, text=True
            )
            if result.returncode != 0:
                return "❌ No tmux sessions found"

            agents = []
            for line in result.stdout.split("\n"):
                if "agent" in line and ":" in line:
                    session_name = line.split(":")[0]
                    agents.append(session_name)

            if not agents:
                return "❌ No agent sessions found"

            if len(agents) == 1:
                agent = agents[0]
                return f"🔗 Connect to {agent}: tmux attach -t {agent}"
            else:
                result = "🤖 Available agents:\n"
                for agent in agents:
                    result += f"   • tmux attach -t {agent}\n"
                return result

        except Exception as e:
            return f"❌ Error: {e}"


def main():
    """Main orchestration command handler."""
    if len(sys.argv) < 2:
        print("Usage: /orchestrate [natural language command]")
        print("Example: /orchestrate Build a user authentication system")
        return 1

    # Get the natural language command
    user_input = " ".join(sys.argv[1:])

    # Initialize orchestration CLI
    cli = OrchestrationCLI()

    # Check if orchestration system is running
    if not cli.is_orchestration_running():
        print("⚠️  Orchestration system not running.")
        print("💡 To use orchestration, start Claude with: ./claude_start.sh")
        print("   Or start manually: ./orchestration/start_system.sh start")
        return 1

    # Connect to message broker
    if not cli.connect_to_broker():
        return 1

    # Simple command matching - Claude provides the real intelligence
    user_lower = user_input.lower()

    # Execute the appropriate command
    if any(word in user_lower for word in ["status", "check", "what"]):
        result = cli._check_status()
    elif any(word in user_lower for word in ["help", "how", "?"]):
        result = cli._show_help()
    elif any(word in user_lower for word in ["monitor", "watch"]):
        result = cli._monitor_agents()
    elif any(word in user_lower for word in ["connect", "attach"]):
        result = cli._connect_to_agent_simple(user_input)
    # Note: cleanup and terminate commands not yet implemented
    else:
        # Default to task delegation - Claude analyzed the task already
        result = cli._delegate_task(user_input)
    print(f"\n{result}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
