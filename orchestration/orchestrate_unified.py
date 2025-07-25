#!/usr/bin/env python3
"""
Unified Orchestration System - LLM-Driven with Redis Coordination
Combines the best of both systems: Redis infrastructure + LLM intelligence
"""

import sys
import os
import time
import subprocess

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
        else:
            print("❌ No agents were created successfully")

def main():
    """Main entry point for unified orchestration."""
    if len(sys.argv) < 2:
        print("Usage: python3 orchestrate_unified.py [task description]")
        print("Example: python3 orchestrate_unified.py 'Find security vulnerabilities and create coverage report'")
        return 1

    task = " ".join(sys.argv[1:])
    orchestration = UnifiedOrchestration()
    orchestration.orchestrate(task)

    return 0

if __name__ == "__main__":
    sys.exit(main())
