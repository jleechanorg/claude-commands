#!/usr/bin/env python3
"""
Intelligent Task Dispatcher for Multi-Agent Orchestration
Enhanced with LLM-driven task analysis and dynamic agent creation
"""

import json
import os
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

import glob


class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


# Production safety limits
MAX_CONCURRENT_AGENTS = 5


class TaskType(Enum):
    FRONTEND = "frontend"
    BACKEND = "backend"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    INFRASTRUCTURE = "infrastructure"
    BUGFIX = "bugfix"
    FEATURE = "feature"


@dataclass
class Task:
    """Represents a task to be assigned to an agent"""

    id: str
    description: str
    task_type: TaskType
    priority: TaskPriority
    estimated_duration: int  # minutes
    dependencies: list[str]
    assigned_agent: str | None = None
    status: str = "pending"  # pending, assigned, in_progress, completed, failed
    created_at: datetime = None
    assigned_at: datetime | None = None
    completed_at: datetime | None = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class TaskDispatcher:
    """Intelligently assigns tasks to the most suitable agents"""

    def __init__(self, orchestration_dir: str = None):
        self.orchestration_dir = orchestration_dir or os.path.dirname(__file__)
        self.tasks_dir = os.path.join(self.orchestration_dir, "tasks")
        self.tasks: dict[str, Task] = {}
        # Dynamic agent capabilities - agents register their own capabilities
        # This allows agents to determine what they can handle based on task content
        self.agent_capabilities = self._discover_agent_capabilities()

        # LLM-driven enhancements
        self.active_agents = set()  # Track active agent names for collision detection
        self.result_dir = "/tmp/orchestration_results"
        os.makedirs(self.result_dir, exist_ok=True)

        # Load existing tasks
        self._load_tasks()

    def _discover_agent_capabilities(self) -> dict:
        """Discover agent capabilities dynamically from registered agents"""
        # Default capabilities for any discovered agents
        # Agents can handle any task type - let them decide based on content
        default_capabilities = {
            "frontend-agent": {
                "types": list(TaskType),  # Can handle any task type
                "keywords": [],  # No keyword matching - agent decides
                "max_concurrent": 2,
                "current_load": 0,
            },
            "backend-agent": {
                "types": list(TaskType),  # Can handle any task type
                "keywords": [],  # No keyword matching - agent decides
                "max_concurrent": 3,
                "current_load": 0,
            },
            "testing-agent": {
                "types": list(TaskType),  # Can handle any task type
                "keywords": [],  # No keyword matching - agent decides
                "max_concurrent": 2,
                "current_load": 0,
            },
        }

        # In production, this would query Redis for registered agents
        # and their self-reported capabilities
        return default_capabilities

    def _load_tasks(self):
        """Load tasks from task files"""
        task_files = {
            "frontend_tasks.txt": "frontend-agent",
            "backend_tasks.txt": "backend-agent",
            "testing_tasks.txt": "testing-agent",
        }

        for filename, agent in task_files.items():
            filepath = os.path.join(self.tasks_dir, filename)
            if os.path.exists(filepath):
                with open(filepath) as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if line:
                            task_id = f"{agent}-{line_num}"
                            task = self._parse_task_description(task_id, line, agent)
                            self.tasks[task_id] = task

    def _parse_task_description(
        self, task_id: str, description: str, suggested_agent: str = None
    ) -> Task:
        """Parse task description and infer properties"""
        # Determine task type from description
        task_type = self._infer_task_type(description)

        # Determine priority from keywords
        priority = self._infer_priority(description)

        # Estimate duration
        duration = self._estimate_duration(description)

        # Find dependencies
        dependencies = self._find_dependencies(description)

        return Task(
            id=task_id,
            description=description,
            task_type=task_type,
            priority=priority,
            estimated_duration=duration,
            dependencies=dependencies,
            assigned_agent=suggested_agent,
        )

    def _infer_task_type(self, description: str) -> TaskType:
        """Infer task type from description"""
        desc_lower = description.lower()

        # Check for specific keywords
        if any(
            keyword in desc_lower
            for keyword in ["ui", "react", "css", "html", "component", "form", "style"]
        ):
            return TaskType.FRONTEND
        if any(
            keyword in desc_lower
            for keyword in ["api", "database", "server", "backend", "auth", "endpoint"]
        ):
            return TaskType.BACKEND
        if any(
            keyword in desc_lower
            for keyword in ["test", "testing", "validate", "verify", "quality"]
        ):
            return TaskType.TESTING
        if any(keyword in desc_lower for keyword in ["bug", "fix", "error", "issue"]):
            return TaskType.BUGFIX
        if any(
            keyword in desc_lower
            for keyword in ["doc", "documentation", "readme", "guide"]
        ):
            return TaskType.DOCUMENTATION
        if any(
            keyword in desc_lower
            for keyword in ["deploy", "ci", "infrastructure", "setup"]
        ):
            return TaskType.INFRASTRUCTURE
        return TaskType.FEATURE

    def _infer_priority(self, description: str) -> TaskPriority:
        """Infer priority from description"""
        desc_lower = description.lower()

        if any(
            keyword in desc_lower
            for keyword in ["critical", "urgent", "emergency", "production"]
        ):
            return TaskPriority.CRITICAL
        if any(keyword in desc_lower for keyword in ["important", "high", "priority"]):
            return TaskPriority.HIGH
        if any(keyword in desc_lower for keyword in ["low", "minor", "nice to have"]):
            return TaskPriority.LOW
        return TaskPriority.MEDIUM

    def _estimate_duration(self, description: str) -> int:
        """Estimate task duration in minutes"""
        # Simple heuristic based on description length and complexity keywords
        base_duration = 30  # 30 minutes default

        # Adjust based on description length
        word_count = len(description.split())
        if word_count > 20:
            base_duration += 30
        elif word_count > 10:
            base_duration += 15

        # Adjust based on complexity keywords
        desc_lower = description.lower()
        if any(
            keyword in desc_lower
            for keyword in ["complex", "refactor", "redesign", "architecture"]
        ):
            base_duration *= 2
        elif any(keyword in desc_lower for keyword in ["simple", "quick", "minor"]):
            base_duration = max(15, base_duration // 2)

        return base_duration

    def _find_dependencies(self, description: str) -> list[str]:
        """Find task dependencies from description"""
        dependencies = []

        # Look for explicit dependency mentions
        if "depends on" in description.lower():
            # Extract dependency information
            pass

        # Look for task references
        if "after" in description.lower():
            # Extract sequence dependencies
            pass

        return dependencies

    def get_best_agent_for_task(self, task: Task) -> str | None:
        """Find the best agent for a given task using dynamic assignment"""
        candidates = []

        for agent_name, capabilities in self.agent_capabilities.items():
            score = 0

            # All agents can handle any task type now - let them decide
            # Base score for availability
            score += 50

            # No keyword matching - agents understand task content naturally
            # Instead, use load balancing as primary factor

            # Check agent availability (load)
            if capabilities["current_load"] < capabilities["max_concurrent"]:
                score += 50 - (capabilities["current_load"] * 10)
            else:
                score -= 50  # Heavy penalty for overloaded agents

            # Priority bonus for high-priority tasks
            if task.priority == TaskPriority.CRITICAL:
                score += 30
            elif task.priority == TaskPriority.HIGH:
                score += 15

            # Round-robin factor to distribute work evenly
            # Prefer agents with lower current load
            load_ratio = capabilities["current_load"] / capabilities["max_concurrent"]
            score -= int(load_ratio * 20)

            candidates.append((agent_name, score))

        # Sort by score and return best candidate
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0] if candidates and candidates[0][1] > 0 else None

    def assign_task(self, task: Task, agent: str = None) -> bool:
        """Assign a task to an agent"""
        if agent is None:
            agent = self.get_best_agent_for_task(task)

        if agent is None:
            print(f"❌ No suitable agent found for task: {task.description}")
            return False

        # Check agent availability
        if (
            self.agent_capabilities[agent]["current_load"]
            >= self.agent_capabilities[agent]["max_concurrent"]
        ):
            print(f"⚠️  Agent {agent} is at capacity, queueing task")
            return False

        # Assign task
        task.assigned_agent = agent
        task.assigned_at = datetime.now()
        task.status = "assigned"

        # Update agent load
        self.agent_capabilities[agent]["current_load"] += 1

        # Write task to agent's file
        self._write_task_to_agent_file(task, agent)

        print(f"✅ Task assigned to {agent}: {task.description}")
        return True

    def _write_task_to_agent_file(self, task: Task, agent: str):
        """Write task to agent's task file"""
        task_files = {
            "frontend-agent": "frontend_tasks.txt",
            "backend-agent": "backend_tasks.txt",
            "testing-agent": "testing_tasks.txt",
        }

        filename = task_files.get(agent)
        if filename:
            filepath = os.path.join(self.tasks_dir, filename)
            with open(filepath, "a") as f:
                f.write(f"{task.description}\n")

    def add_task_from_description(self, description: str) -> str:
        """Add a new task from description"""
        task_id = f"task-{int(time.time())}"
        task = self._parse_task_description(task_id, description)
        self.tasks[task_id] = task

        # Try to assign immediately
        if self.assign_task(task):
            return task_id
        print(f"⏳ Task queued: {description}")
        return task_id

    def process_pending_tasks(self):
        """Process all pending tasks and try to assign them"""
        pending_tasks = [
            task for task in self.tasks.values() if task.status == "pending"
        ]

        # Sort by priority and creation time
        pending_tasks.sort(key=lambda t: (t.priority.value, t.created_at), reverse=True)

        for task in pending_tasks:
            self.assign_task(task)

    def get_agent_workload(self) -> dict[str, Any]:
        """Get current workload for all agents"""
        workload = {}

        for agent_name, capabilities in self.agent_capabilities.items():
            agent_tasks = [
                task
                for task in self.tasks.values()
                if task.assigned_agent == agent_name
                and task.status in ["assigned", "in_progress"]
            ]

            workload[agent_name] = {
                "current_load": capabilities["current_load"],
                "max_concurrent": capabilities["max_concurrent"],
                "utilization": capabilities["current_load"]
                / capabilities["max_concurrent"],
                "tasks": len(agent_tasks),
                "task_list": [task.description for task in agent_tasks],
            }

        return workload

    def generate_task_report(self) -> dict[str, Any]:
        """Generate comprehensive task report"""
        total_tasks = len(self.tasks)
        pending_tasks = sum(
            1 for task in self.tasks.values() if task.status == "pending"
        )
        assigned_tasks = sum(
            1 for task in self.tasks.values() if task.status == "assigned"
        )
        completed_tasks = sum(
            1 for task in self.tasks.values() if task.status == "completed"
        )

        return {
            "timestamp": datetime.now(),
            "total_tasks": total_tasks,
            "pending_tasks": pending_tasks,
            "assigned_tasks": assigned_tasks,
            "completed_tasks": completed_tasks,
            "completion_rate": completed_tasks / max(total_tasks, 1),
            "agent_workload": self.get_agent_workload(),
            "task_distribution": {
                task_type.value: sum(
                    1 for task in self.tasks.values() if task.task_type == task_type
                )
                for task_type in TaskType
            },
        }

    def save_task_report(self):
        """Save task report to file"""
        report = self.generate_task_report()

        report_file = os.path.join(self.tasks_dir, "task_report.json")
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        print(
            f"📊 Task report saved: {report['total_tasks']} tasks, "
            f"{report['completion_rate']:.1%} completion rate"
        )

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
        except:
            pass

        return existing

    def _generate_unique_name(self, base_name: str, role_suffix: str = "") -> str:
        """Generate unique agent name with collision detection."""
        timestamp = int(time.time()) % 10000

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

        # Generate unique timestamp for agent names
        timestamp = int(time.time()) % 10000

        # Always create a general development agent that can handle any task
        # The agent itself will understand what to do based on the task description
        return [{
            "name": f"task-agent-{timestamp}",
            "type": "development",
            "focus": task_description,
            "capabilities": ["task_execution", "development", "git_operations", "server_management", "testing", "full_stack"],
            "prompt": f"""Task: {task_description}

Execute the task exactly as requested. Key points:
- If asked to start a server, start it on the specified port
- If asked to modify files, make those exact modifications
- If asked to run commands, execute them
- If asked to test, run the appropriate tests
- Always follow the specific instructions given

Complete the task, then commit and create a PR."""
        }]

    def _extract_ui_focus(self, task_description: str) -> str:
        """Extract specific UI component or area from task description."""
        task_lower = task_description.lower()

        # Common UI components to look for
        ui_components = {
            'button': 'UI buttons and click handlers',
            'form': 'form elements and validation',
            'wizard': 'wizard interface and flow',
            'character creation': 'character creation interface',
            'summary': 'summary display components',
            'navigation': 'navigation elements',
            'modal': 'modal dialogs',
            'menu': 'menu components',
            'table': 'data tables',
            'card': 'card components',
            'layout': 'page layout',
            'header': 'header components',
            'footer': 'footer components',
            'sidebar': 'sidebar navigation'
        }

        # Check for specific components mentioned
        for component, description in ui_components.items():
            if component in task_lower:
                return description

        # Default to general UI
        return "UI and frontend JavaScript/CSS"


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
2. When done, run these commands IN ORDER:

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
   gh pr create --title "Agent {agent_name}: {agent_focus}" \
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

   # Create completion report
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

            # Create tmux session with enhanced monitoring and error handling
            # Use @filename syntax to read prompt from file
            # Add --dangerously-skip-permissions for orchestration agents to create files/PRs
            claude_cmd = f'{claude_path} -p @{prompt_file} --output-format stream-json --verbose --dangerously-skip-permissions'

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

            print(f"✅ Created {agent_name} - Focus: {agent_focus}")
            return True

        except Exception as e:
            print(f"❌ Failed to create {agent_name}: {e}")
            return False


def main():
    """Main entry point for task dispatcher"""
    dispatcher = TaskDispatcher()

    # Process any pending tasks
    dispatcher.process_pending_tasks()

    # Generate and save report
    dispatcher.save_task_report()

    # Show summary
    report = dispatcher.generate_task_report()
    print("\n📋 Task Summary:")
    print(f"   Total: {report['total_tasks']}")
    print(f"   Pending: {report['pending_tasks']}")
    print(f"   Assigned: {report['assigned_tasks']}")
    print(f"   Completed: {report['completed_tasks']}")
    print(f"   Completion Rate: {report['completion_rate']:.1%}")


if __name__ == "__main__":
    main()
