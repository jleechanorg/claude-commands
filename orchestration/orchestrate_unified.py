#!/usr/bin/env python3
"""
Unified Orchestration System - LLM-Driven with File-based Coordination
Pure file-based A2A protocol without Redis dependencies
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

import glob
import json
import subprocess
import time
from datetime import datetime, timedelta
from task_dispatcher import TaskDispatcher

# Constraint system removed - using simple safety boundaries only


class UnifiedOrchestration:
    """Unified orchestration using file-based A2A coordination with LLM-driven intelligence."""

    # Configuration constants
    INITIAL_DELAY = 5  # Initial delay before checking for PRs
    POLLING_INTERVAL = 2  # Interval between PR checks
    STALE_PROMPT_FILE_AGE_SECONDS = 300  # 5 minutes

    def __init__(self):
        self.task_dispatcher = TaskDispatcher()
        # Simple safety boundaries only - no complex constraint parsing needed
        print("📁 File-based A2A coordination initialized")

        # Clean up stale prompt files on orchestration startup to prevent task reuse
        self._cleanup_stale_orchestration_state()

    def _cleanup_stale_orchestration_state(self):
        """Clean up stale prompt files and tmux sessions to prevent task reuse."""
        try:
            # Clean up all stale agent prompt files
            stale_prompt_files = glob.glob("/tmp/agent_prompt_*.txt")
            cleaned_count = 0
            for prompt_file in stale_prompt_files:
                try:
                    # Check if file is older than 5 minutes to avoid cleaning active tasks
                    file_age = time.time() - os.path.getmtime(prompt_file)
                    if file_age > self.STALE_PROMPT_FILE_AGE_SECONDS:
                        os.remove(prompt_file)
                        cleaned_count += 1
                except OSError:
                    pass  # File might have been removed by another process

            if cleaned_count > 0:
                print(f"🧹 Cleaned up {cleaned_count} stale prompt files")

            # Clean up completed tmux agent sessions (keep running ones)
            self._cleanup_completed_tmux_sessions()

        except Exception as e:
            print(f"⚠️ Warning: Could not fully clean orchestration state: {e}")

    def _cleanup_completed_tmux_sessions(self):
        """Clean up tmux sessions for agents that have completed their work."""
        try:
            # Get all task-agent tmux sessions
            result = subprocess.run(
                ["tmux", "list-sessions", "-F", "#{session_name}"],
                shell=False,
                capture_output=True,
                text=True,
                check=False,
                timeout=30
            )
            if result.returncode != 0:
                return

            sessions = result.stdout.strip().split('\n')
            agent_sessions = [s for s in sessions if s.startswith('task-agent-')]

            cleaned_sessions = 0
            for session in agent_sessions:
                if self._is_session_completed(session):
                    try:
                        subprocess.run(
                            ["tmux", "kill-session", "-t", session],
                            shell=False,
                            check=False,
                            capture_output=True,
                            timeout=30
                        )
                        cleaned_sessions += 1
                    except (subprocess.SubprocessError, OSError):
                        pass

            if cleaned_sessions > 0:
                print(f"🧹 Cleaned up {cleaned_sessions} completed tmux sessions")

        except Exception as e:
            print(f"⚠️ Warning: Could not clean tmux sessions: {e}")

    def _is_session_completed(self, session_name: str) -> bool:
        """Check if a tmux session has completed its work."""
        try:
            result = subprocess.run(
                ["tmux", "capture-pane", "-t", session_name, "-p"],
                shell=False,
                capture_output=True,
                text=True,
                check=False,
                timeout=30
            )
            if result.returncode != 0:
                return True  # Session might be dead already

            output = result.stdout.strip()
            completion_indicators = [
                "Agent completed successfully",
                "Agent execution completed. Session remains active for monitoring",
                "Session will auto-close in 1 hour"
            ]

            # If completion indicators found, session is done
            for indicator in completion_indicators:
                if indicator in output:
                    return True

            return False
        except (subprocess.SubprocessError, OSError):
            return True  # If we can't check, assume it's safe to clean

    def _check_dependencies(self):
        """Check system dependencies and report status."""
        dependencies = {"tmux": "tmux", "git": "git", "gh": "gh", "claude": "claude"}

        missing = []
        for name, command in dependencies.items():
            try:
                result = subprocess.run(
                    ["which", command],
                    shell=False,
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode != 0:
                    missing.append(name)
            except:
                missing.append(name)

        if missing:
            print(f"⚠️  Missing dependencies: {', '.join(missing)}")
            if "claude" in missing:
                print(
                    "   Install Claude Code CLI: https://docs.anthropic.com/en/docs/claude-code"
                )
            if "gh" in missing:
                print("   Install GitHub CLI: https://cli.github.com/")
            return False
        return True

    def _should_continue_existing_work(self, task_description: str) -> bool:
        """Check if task should continue existing agent work."""
        continuation_keywords = [
            "continue from",
            "same agent",
            "keep working",
            "follow up",
            "also",
            "and then",
            "make it run",
            "ensure",
            "verify",
        ]
        task_lower = task_description.lower()
        return any(keyword in task_lower for keyword in continuation_keywords)

    def _find_recent_agent_work(self, task_description: str) -> dict:
        """Find recent agent work that matches the task context."""
        try:
            # Check recent PRs for agent work
            result = subprocess.run(
                [
                    "gh",
                    "pr",
                    "list",
                    "--author",
                    "@me",
                    "--limit",
                    "5",
                    "--json",
                    "number,title,headRefName,createdAt",
                ],
                shell=False,
                capture_output=True,
                text=True,
                check=True,
                timeout=30
            )
            prs = json.loads(result.stdout)

            # Look for recent agent PRs (created in last hour)
            datetime.now() - timedelta(hours=1)

            for pr in prs:
                if (
                    "task-agent-" in pr["title"]
                    and "settings" in task_description.lower()
                ) and (
                    "settings" in pr["title"].lower()
                    or "gear" in pr["title"].lower()
                ):
                    agent_name = pr["headRefName"].replace("-work", "")
                    return {
                        "name": agent_name,
                        "branch": pr["headRefName"],
                        "pr_number": pr["number"],
                    }
        except Exception as e:
            print(f"⚠️  Could not check recent agent work: {e}")
        return None

    def _continue_existing_agent_work(
        self, existing_agent: dict, task_description: str
    ):
        """Continue work on existing agent branch."""
        try:
            # Check out the existing branch
            subprocess.run(
                ["git", "checkout", existing_agent["branch"]],
                shell=False,
                timeout=30,
                check=True
            )
            print(f"✅ Switched to existing branch: {existing_agent['branch']}")

            # Create new agent session on existing branch
            agent_spec = {
                "name": f"{existing_agent['name']}-continue",
                "focus": task_description,
                "existing_branch": existing_agent["branch"],
                "existing_pr": existing_agent.get("pr_number"),
            }

            if self.task_dispatcher.create_dynamic_agent(agent_spec):
                print(f"✅ Created continuation agent: {agent_spec['name']}")
                print(
                    f"📂 Working directory: {os.getcwd()}/agent_workspace_{agent_spec['name']}"
                )
                print(
                    f"📋 Monitor logs: tail -f /tmp/orchestration_logs/{agent_spec['name']}.log"
                )
                print(f"⏳ Monitor with: tmux attach -t {agent_spec['name']}")
            else:
                print("❌ Failed to create continuation agent")

        except Exception as e:
            print(f"❌ Failed to continue existing work: {e}")
            print("🔄 Falling back to new agent creation")

    def orchestrate(self, task_description: str):
        """Main orchestration method with LLM-driven agent creation."""
        print("🤖 Unified LLM-Driven Orchestration with File-based A2A")
        print("=" * 60)

        # Pre-flight checks
        if not self._check_dependencies():
            print("\n❌ Cannot proceed without required dependencies")
            return

        print(f"📋 Task: {task_description}")

        # Check for continuation keywords and existing agent work
        if self._should_continue_existing_work(task_description):
            existing_agent = self._find_recent_agent_work(task_description)
            if existing_agent:
                print(
                    f"🔄 Continuing work from {existing_agent['name']} on branch {existing_agent['branch']}"
                )
                self._continue_existing_agent_work(existing_agent, task_description)
                return

        # LLM-driven task analysis and agent creation with constraints
        agents = self.task_dispatcher.analyze_task_and_create_agents(task_description)

        print(f"\n🚀 Creating {len(agents)} dynamic agents...")

        created_agents = []
        for agent_spec in agents:
            if self.task_dispatcher.create_dynamic_agent(agent_spec):
                created_agents.append(agent_spec)

                # Agent coordination handled via file-based A2A protocol

        if created_agents:
            print(f"\n⏳ {len(created_agents)} agents working... Monitor with:")
            for agent in created_agents:
                print(f"   tmux attach -t {agent['name']}")

            print("\n📂 Agent working directories:")
            for agent in created_agents:
                # Create workspaces in dedicated orchestration directory to avoid polluting project root
                orchestration_dir = os.path.join(os.getcwd(), "orchestration", "agent_workspaces")
                os.makedirs(orchestration_dir, exist_ok=True)
                workspace_path = os.path.join(orchestration_dir, f"agent_workspace_{agent['name']}")
                print(f"   {workspace_path}")

            print("\n📋 Monitor agent logs:")
            for agent in created_agents:
                print(f"   tail -f /tmp/orchestration_logs/{agent['name']}.log")

            print(f"\n🏠 You remain in: {os.getcwd()}")
            print("\n📁 File-based A2A coordination - check orchestration/results/")

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
        time.sleep(self.INITIAL_DELAY)

        while time.time() - start_time < max_wait and len(prs_found) < len(agents):
            for agent in agents:
                if agent["name"] in [pr["agent"] for pr in prs_found]:
                    continue  # Already found PR for this agent

                # Check agent workspace for PR
                workspace_path = os.path.join("orchestration", "agent_workspaces", f"agent_workspace_{agent['name']}")
                if os.path.exists(workspace_path):
                    # Try multiple possible branch patterns
                    branch_patterns = [
                        f"{agent['name']}-work",
                        agent["name"],
                        f"task-{agent['name']}",
                        f"agent-{agent['name']}",
                    ]

                    for branch_pattern in branch_patterns:
                        try:
                            # Try to get PR info from the agent's branch
                            result = subprocess.run(
                                [
                                    "gh",
                                    "pr",
                                    "list",
                                    "--head",
                                    branch_pattern,
                                    "--json",
                                    "number,url,title,state",
                                ],
                                shell=False,
                                check=False,
                                cwd=workspace_path,
                                capture_output=True,
                                text=True,
                                timeout=30
                            )

                            if result.returncode == 0 and result.stdout.strip():
                                pr_data = json.loads(result.stdout)
                                if pr_data:
                                    pr_info = pr_data[0]
                                    prs_found.append(
                                        {
                                            "agent": agent["name"],
                                            "number": pr_info["number"],
                                            "url": pr_info["url"],
                                            "title": pr_info["title"],
                                            "state": pr_info["state"],
                                        }
                                    )
                                    break  # Found PR with this pattern, stop trying others
                        except subprocess.CalledProcessError as e:
                            print(
                                f"⚠️ Subprocess error while checking PRs for agent '{agent['name']}' with branch '{branch_pattern}': {e}"
                            )
                        except json.JSONDecodeError as e:
                            print(
                                f"⚠️ JSON decode error while parsing PR data for agent '{agent['name']}' with branch '{branch_pattern}': {e}"
                            )
                        except Exception as e:
                            print(
                                f"⚠️ Unexpected error while checking PRs for agent '{agent['name']}' with branch '{branch_pattern}': {e}"
                            )

            if len(prs_found) < len(agents):
                time.sleep(self.POLLING_INTERVAL)  # Wait before checking again

        # Display results
        if prs_found:
            print("\n✅ **PR(s) Created:**")
            for pr in prs_found:
                print(f"\n🔗 **Agent**: {pr['agent']}")
                print(f"   **PR #{pr['number']}**: {pr['title']}")
                print(f"   **URL**: {pr['url']}")
                print(f"   **Status**: {pr['state']}")
        else:
            print("\n⏳ No PRs detected yet. Agents may still be working.")
            print("   Check agent progress with: tmux attach -t [agent-name]")
            print("   Or wait and check manually: gh pr list --author @me")


def main():
    """Main entry point for unified orchestration."""
    if len(sys.argv) < 2 or sys.argv[1] in ["--help", "-h", "help"]:
        print("Usage: python3 orchestrate_unified.py [task description]")
        print(
            "Example: python3 orchestrate_unified.py 'Find security vulnerabilities and create coverage report'"
        )
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
