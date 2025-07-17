#!/usr/bin/env python3
"""
/orchestrate - AI Agent Orchestration via Claude Code CLI

Provides natural language interface to the orchestration system while maintaining
full Claude Code CLI functionality and context.
"""

import sys
import os
import subprocess
import json
from typing import Dict, Any, Optional

# Add orchestration directory to path
orchestration_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'orchestration')
sys.path.insert(0, orchestration_path)

try:
    from natural_language_parser import NaturalLanguageParser, ParsedCommand
    from message_broker import MessageBroker
    from intelligent_agent_planner import IntelligentAgentPlanner, AgentPlan
except ImportError:
    print("❌ Orchestration system not found. Please ensure orchestration/ directory exists.")
    sys.exit(1)


class OrchestrationCLI:
    """Claude Code CLI integration for orchestration system."""
    
    def __init__(self):
        self.parser = NaturalLanguageParser()
        self.broker = None
        self.agent_planner = IntelligentAgentPlanner()
        
    def is_orchestration_running(self) -> bool:
        """Check if orchestration system is running."""
        try:
            # Check Redis connectivity
            result = subprocess.run(['redis-cli', 'ping'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode != 0 or 'PONG' not in result.stdout:
                return False
            
            # Check if tmux sessions exist (actual detection method)
            result = subprocess.run(['tmux', 'list-sessions'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                return False
                
            # Check for any agent sessions (dynamic discovery)
            sessions = result.stdout
            agent_patterns = ['-agent:', 'frontend-agent:', 'backend-agent:', 'testing-agent:', 'opus-master:']
            
            # Look for any agent session (new intelligent agents or legacy agents)
            has_agents = any(pattern in sessions for pattern in agent_patterns)
            
            return has_agents
            
        except Exception:
            return False
    
    def start_orchestration_system(self) -> bool:
        """Start the orchestration system."""
        try:
            print("🚀 Starting orchestration system...")
            script_path = os.path.join(orchestration_path, 'start_system.sh')
            result = subprocess.run([script_path, 'start'], 
                                  capture_output=True, text=True, timeout=30)
            
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
        """Connect to the message broker."""
        try:
            self.broker = MessageBroker()
            # Test connection
            self.broker.redis_client.ping()
            return True
        except Exception as e:
            print(f"❌ Failed to connect to message broker: {e}")
            return False
    
    def execute_orchestration_command(self, command: ParsedCommand) -> str:
        """Execute orchestration-specific command."""
        if command.action == 'delegate_task':
            return self._delegate_task(command)
        elif command.action == 'check_status':
            return self._check_status()
        elif command.action == 'show_help':
            return self._show_help()
        elif command.action == 'spawn_agent':
            return self._spawn_agent()
        elif command.action == 'check_progress':
            return self._check_progress()
        elif command.action == 'monitor_agents':
            return self._monitor_agents()
        elif command.action == 'connect_agent':
            return self._connect_to_agent(command)
        else:
            return f"🤔 I understand '{command.action}' but need to implement the handler."
    
    def _delegate_task(self, command: ParsedCommand) -> str:
        """Delegate task using intelligent LLM-driven agent planning."""
        if not command.target:
            return "❌ Please specify what you want me to build or create."
        
        try:
            task_description = command.target
            priority = command.parameters.get('priority', 'medium')
            
            # Use LLM to analyze task and plan optimal agents
            print("🧠 Analyzing task with intelligent agent planner...")
            agent_plan = self.agent_planner.analyze_task(task_description)
            
            # Display agent plan
            plan_summary = self.agent_planner.format_plan_summary(agent_plan)
            print(f"\n{plan_summary}")
            
            # Create specialized agents based on plan
            created_agents = self._create_specialized_agents(agent_plan, task_description, priority)
            
            if not created_agents:
                return ("❌ Failed to create specialized agents.\n"
                       "💡 Try: ./orchestration/start_system.sh start")
            
            # Format response with intelligent agent details
            agent_list = []
            connection_commands = []
            
            for agent in created_agents:
                agent_list.append(f"🤖 {agent['name']}")
                connection_commands.append(f"   tmux attach -t {agent['name']}")
            
            return (f"✅ Task delegated to specialized agents!\n"
                   f"📋 Task: {task_description}\n"
                   f"⚡ Priority: {priority}\n"
                   f"🧠 Analysis: {agent_plan.reasoning}\n"
                   f"👥 Specialized Agents ({agent_plan.agent_count}): {', '.join(agent_list)}\n"
                   f"⚡ Execution: {'Parallel' if agent_plan.parallel_execution else 'Sequential'}\n"
                   f"🔗 Connect to agents:\n" + '\n'.join(connection_commands) + "\n"
                   f"💡 Monitor progress: /orch What's the status?")
            
        except Exception as e:
            return f"❌ Error in intelligent task delegation: {e}"
    
    def _create_specialized_agents(self, agent_plan: AgentPlan, task_description: str, priority: str) -> list:
        """Create specialized Claude agents with actual autonomous execution - Pure Python."""
        import datetime
        created_agents = []
        
        for agent_spec in agent_plan.agents:
            agent_name = agent_spec.name
            
            try:
                # Generate specialized Claude prompt
                claude_prompt = self._generate_agent_prompt(agent_spec, task_description)
                
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
                        f"{'='*50}\n"
                    )
                    
                    with open(task_file, 'a') as f:  # Append to preserve existing tasks
                        f.write(task_entry)
                    
                    created_agents.append({
                        'name': agent_name,
                        'focus': agent_spec.focus,
                        'file': task_file,
                        'status': 'ACTIVE'
                    })
                    
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
{chr(10).join('- ' + resp for resp in agent_spec.responsibilities)}

ESTIMATED WORK TIME: {agent_spec.estimated_duration}

AUTONOMOUS WORKFLOW:
1. Start by switching to a new branch: /handoff {agent_spec.name.replace('-', '_')}_work --auto-approve
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
            claude_path = os.environ.get('CLAUDE_PATH', '/home/jleechan/.claude/local/claude')
            if not os.path.exists(claude_path):
                # Try alternative locations
                claude_path = subprocess.run(['which', 'claude'], capture_output=True, text=True).stdout.strip()
                if not claude_path:
                    print(f"❌ Claude executable not found. Set CLAUDE_PATH or ensure 'claude' is in PATH")
                    return False
            
            # Clean up any existing session with the same name
            cleanup_cmd = ['tmux', 'kill-session', '-t', agent_spec.name]
            subprocess.run(cleanup_cmd, capture_output=True)  # Ignore errors if session doesn't exist
            
            # Create tmux session with Claude in interactive mode
            tmux_cmd = [
                'tmux', 'new-session', '-d', '-s', agent_spec.name, 
                '-c', os.getcwd(),
                claude_path, '--verbose'
            ]
            
            result = subprocess.run(tmux_cmd, check=True, capture_output=True, text=True)
            
            # Wait a moment for Claude to start
            import time
            time.sleep(2)
            
            # Send the prompt to the Claude session
            prompt_lines = claude_prompt.split('\\n')
            for line in prompt_lines:
                if line.strip():  # Skip empty lines
                    subprocess.run(['tmux', 'send-keys', '-t', agent_spec.name, line, 'Enter'])
                    time.sleep(0.1)  # Brief pause between lines
            
            # Verify session was created
            verify_cmd = ['tmux', 'has-session', '-t', agent_spec.name]
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
            with open(task_file, 'a') as f:
                f.write(task_entry)
        except Exception as e:
            print(f"Warning: Could not write to {task_file}: {e}")
    
    def _check_status(self) -> str:
        """Check real Claude agent orchestration system status."""
        try:
            # Check Redis
            redis_status = "✅ Connected" if self.broker and self.broker.redis_client.ping() else "❌ Disconnected"
            
            # Check tmux sessions for Claude agents
            tmux_result = subprocess.run(['tmux', 'list-sessions'], 
                                       capture_output=True, text=True)
            claude_agents = {}
            if tmux_result.returncode == 0:
                for line in tmux_result.stdout.split('\n'):
                    if line.strip():
                        for agent_name in ['frontend-agent', 'backend-agent', 'testing-agent', 'opus-master']:
                            if agent_name in line:
                                parts = line.split(':')
                                if len(parts) >= 2:
                                    session_info = ':'.join(parts[1:]).strip()
                                    claude_agents[agent_name] = session_info
            
            # Check task files and pending tasks
            task_counts = {}
            for agent_type in ['frontend', 'backend', 'testing']:
                task_file = f"orchestration/tasks/{agent_type}_tasks.txt"
                try:
                    with open(task_file, 'r') as f:
                        lines = f.readlines()
                        task_counts[agent_type] = len([l for l in lines if l.strip()])
                except FileNotFoundError:
                    task_counts[agent_type] = 0
            
            # Build detailed status
            status = f"🎯 **Real Claude Agent Orchestration Status**\n\n"
            status += f"🔄 Redis: {redis_status}\n"
            status += f"🤖 Active Claude Agents: {len(claude_agents)}\n\n"
            
            # Show Claude agent details
            agent_icons = {
                'frontend-agent': '🎨',
                'backend-agent': '⚙️',
                'testing-agent': '🧪',
                'opus-master': '🎯'
            }
            
            for agent_name, icon in agent_icons.items():
                if agent_name in claude_agents:
                    status += f"   {icon} {agent_name.replace('-', ' ').title()}: ✅ ACTIVE\n"
                    status += f"      └─ Session: {claude_agents[agent_name]}\n"
                    status += f"      └─ Connect: tmux attach -t {agent_name}\n"
                else:
                    status += f"   {icon} {agent_name.replace('-', ' ').title()}: ❌ STOPPED\n"
            
            # Show task queue status
            status += f"\n📋 **Task Queue Status:**\n"
            for agent_type, count in task_counts.items():
                if count > 0:
                    status += f"   📝 {agent_type.title()} tasks: {count} pending\n"
                else:
                    status += f"   ✅ {agent_type.title()} tasks: No pending tasks\n"
            
            # Show shared status file if available
            try:
                with open("orchestration/tasks/shared_status.txt", 'r') as f:
                    shared_status = f.read().strip()
                    if shared_status:
                        status += f"\n📊 **Agent Dashboard:**\n"
                        for line in shared_status.split('\n'):
                            if line.strip():
                                status += f"   {line}\n"
            except FileNotFoundError:
                pass
            
            # Add monitoring commands
            status += f"\n💡 **Quick Commands:**\n"
            status += f"   • Delegate task: /orch Build user authentication\n"
            status += f"   • Connect to Frontend: tmux attach -t frontend-agent\n"
            status += f"   • Connect to Backend: tmux attach -t backend-agent\n"
            status += f"   • Connect to Testing: tmux attach -t testing-agent\n"
            status += f"   • View task files: cat orchestration/tasks/*_tasks.txt\n"
            status += f"   • System status: ./orchestration/start_system.sh status\n"
            
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
        return ("🤖 To spawn new agents, run:\n"
               "   ./orchestration/start_system.sh spawn sonnet\n\n"
               "💡 This will create a new Sonnet agent in a separate tmux session.")
    
    def _check_progress(self) -> str:
        """Check task progress."""
        return ("📊 Progress checking via message queues not yet implemented.\n"
               "💡 For now, check individual agent tmux sessions:\n"
               "   tmux list-sessions | grep -E '(opus|sonnet|sub)'")
    
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
    
    def _connect_to_agent(self, command: ParsedCommand) -> str:
        """Provide instructions for connecting to a specific agent."""
        # Get available agents
        try:
            active_agents = self.broker.get_active_agents()
            sonnet_agents = [agent for agent in active_agents if agent.startswith("sonnet")]
            
            if not sonnet_agents:
                return ("❌ No Sonnet agents available to connect to.\n"
                       "💡 Start agents with: ./orchestration/start_system.sh spawn sonnet")
            
            # If user specified an agent, use that; otherwise show options
            target_agent = None
            if command.target:
                # Extract agent number or name from target
                target_lower = command.target.lower()
                if 'sonnet' in target_lower:
                    for agent in sonnet_agents:
                        if agent.lower() in target_lower or target_lower in agent.lower():
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
                result = f"🤖 **Available Sonnet Agents:**\n\n"
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
    
    # Parse the natural language command
    command = cli.parser.parse_command(user_input)
    
    # Show confidence if low
    if command.confidence < 0.5:
        print(f"🤔 I'm not entirely sure what you mean (confidence: {command.confidence:.0%})")
        print("💡 I'll try my best to help...")
    
    # Execute the command
    result = cli.execute_orchestration_command(command)
    print(f"\n{result}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())