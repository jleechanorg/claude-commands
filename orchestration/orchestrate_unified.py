#!/usr/bin/env python3
"""
Unified Orchestration System - LLM-Driven with Redis Coordination
Combines the best of both systems: Redis infrastructure + LLM intelligence
"""

import sys
import os
import time
import subprocess
import json

# Add orchestration directory to path
sys.path.insert(0, os.path.dirname(__file__))

from task_dispatcher import TaskDispatcher
from message_broker import MessageBroker

class UnifiedOrchestration:
    """Unified orchestration combining Redis coordination with LLM-driven intelligence."""
    
    def __init__(self):
        self.task_dispatcher = TaskDispatcher()
        self.message_broker = None
        self._init_redis_broker()
    
    def _init_redis_broker(self):
        """Initialize Redis message broker if available."""
        try:
            self.message_broker = MessageBroker()
            print("🔄 Redis: Connected")
        except Exception as e:
            print(f"📡 Redis: Unavailable ({e}) - Using file-based coordination")
            self.message_broker = None
    
    def _check_dependencies(self):
        """Check system dependencies and report status."""
        dependencies = {
            'tmux': 'tmux',
            'git': 'git',
            'gh': 'gh',
            'claude': 'claude'
        }
        
        missing = []
        for name, command in dependencies.items():
            try:
                result = subprocess.run(
                    ['which', command], 
                    capture_output=True, 
                    text=True
                )
                if result.returncode != 0:
                    missing.append(name)
            except:
                missing.append(name)
        
        if missing:
            print(f"⚠️  Missing dependencies: {', '.join(missing)}")
            if 'claude' in missing:
                print("   Install Claude Code CLI: https://docs.anthropic.com/en/docs/claude-code")
            if 'gh' in missing:
                print("   Install GitHub CLI: https://cli.github.com/")
            return False
        return True
    
    def orchestrate(self, task_description: str):
        """Main orchestration method with LLM-driven agent creation."""
        print("🤖 Unified LLM-Driven Orchestration with Redis Coordination")
        print("=" * 60)
        
        # Pre-flight checks
        if not self._check_dependencies():
            print("\n❌ Cannot proceed without required dependencies")
            return
            
        print(f"📋 Task: {task_description}")
        
        # LLM-driven task analysis and agent creation
        agents = self.task_dispatcher.analyze_task_and_create_agents(task_description)
        
        print(f"\n🚀 Creating {len(agents)} dynamic agents...")
        
        created_agents = []
        for agent_spec in agents:
            if self.task_dispatcher.create_dynamic_agent(agent_spec):
                created_agents.append(agent_spec)
                
                # Register with Redis if available
                if self.message_broker:
                    try:
                        self.message_broker.register_agent(
                            agent_spec["name"],
                            agent_spec["type"], 
                            agent_spec["capabilities"]
                        )
                    except Exception as e:
                        print(f"⚠️ Redis registration failed for {agent_spec['name']}: {e}")
        
        if created_agents:
            print(f"\n⏳ {len(created_agents)} agents working... Monitor with:")
            for agent in created_agents:
                print(f"   tmux attach -t {agent['name']}")
            
            print(f"\n📂 To explore agent workspaces (optional):")
            for agent in created_agents:
                workspace_path = os.path.join(os.getcwd(), f"agent_workspace_{agent['name']}")
                print(f"   cd {workspace_path}")
            
            print(f"\n🏠 You remain in: {os.getcwd()}")
                
            if self.message_broker:
                print(f"\n🔄 Redis coordination active - agents can communicate")
            else:
                print(f"\n📁 File-based coordination - check orchestration/results/")
            
            # Wait briefly and check for PR creation
            self._check_and_display_prs(created_agents)
        else:
            print("❌ No agents were created successfully")
    
    def _check_and_display_prs(self, agents, max_wait=30):
        """Check for PRs created by agents and display them."""
        print(f"\n🔍 Checking for PR creation (waiting up to {max_wait}s)...")
        
        prs_found = []
        start_time = time.time()
        
        # Give agents some time to create PRs
        time.sleep(5)
        
        while time.time() - start_time < max_wait and len(prs_found) < len(agents):
            for agent in agents:
                if agent['name'] in [pr['agent'] for pr in prs_found]:
                    continue  # Already found PR for this agent
                
                # Check agent workspace for PR
                workspace_path = f"agent_workspace_{agent['name']}"
                if os.path.exists(workspace_path):
                    try:
                        # Try to get PR info from the agent's branch
                        result = subprocess.run(
                            ['gh', 'pr', 'list', '--head', f"{agent['name']}-work", '--json', 'number,url,title,state'],
                            cwd=workspace_path,
                            capture_output=True,
                            text=True
                        )
                        
                        if result.returncode == 0 and result.stdout.strip():
                            pr_data = json.loads(result.stdout)
                            if pr_data:
                                pr_info = pr_data[0]
                                prs_found.append({
                                    'agent': agent['name'],
                                    'number': pr_info['number'],
                                    'url': pr_info['url'],
                                    'title': pr_info['title'],
                                    'state': pr_info['state']
                                })
                    except Exception as e:
                        # Silently continue if PR check fails
                        pass
            
            if len(prs_found) < len(agents):
                time.sleep(2)  # Wait before checking again
        
        # Display results
        if prs_found:
            print(f"\n✅ **PR(s) Created:**")
            for pr in prs_found:
                print(f"\n🔗 **Agent**: {pr['agent']}")
                print(f"   **PR #{pr['number']}**: {pr['title']}")
                print(f"   **URL**: {pr['url']}")
                print(f"   **Status**: {pr['state']}")
        else:
            print(f"\n⏳ No PRs detected yet. Agents may still be working.")
            print(f"   Check agent progress with: tmux attach -t [agent-name]")
            print(f"   Or wait and check manually: gh pr list --author @me")

def main():
    """Main entry point for unified orchestration."""
    if len(sys.argv) < 2 or sys.argv[1] in ['--help', '-h', 'help']:
        print("Usage: python3 orchestrate_unified.py [task description]")
        print("Example: python3 orchestrate_unified.py 'Find security vulnerabilities and create coverage report'")
        print("\nThe orchestration system will:")
        print("1. Create specialized agents for your task")
        print("2. Monitor their progress")
        print("3. Display any PRs created at the end")
        return 1 if len(sys.argv) < 2 else 0
    
    task = " ".join(sys.argv[1:])
    orchestration = UnifiedOrchestration()
    orchestration.orchestrate(task)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())