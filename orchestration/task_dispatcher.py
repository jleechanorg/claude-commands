#!/usr/bin/env python3
"""
Intelligent Task Dispatcher for Multi-Agent Orchestration
Analyzes tasks and assigns them to the most suitable agents
"""

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class TaskPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


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
        self.agent_capabilities = {
            "frontend-agent": {
                "types": [TaskType.FRONTEND, TaskType.DOCUMENTATION],
                "keywords": [
                    "ui",
                    "react",
                    "css",
                    "html",
                    "component",
                    "style",
                    "interface",
                    "form",
                ],
                "max_concurrent": 2,
                "current_load": 0,
            },
            "backend-agent": {
                "types": [TaskType.BACKEND, TaskType.INFRASTRUCTURE],
                "keywords": [
                    "api",
                    "database",
                    "server",
                    "flask",
                    "firestore",
                    "auth",
                    "endpoint",
                ],
                "max_concurrent": 3,
                "current_load": 0,
            },
            "testing-agent": {
                "types": [TaskType.TESTING, TaskType.BUGFIX],
                "keywords": [
                    "test",
                    "bug",
                    "fix",
                    "validate",
                    "verify",
                    "quality",
                    "coverage",
                ],
                "max_concurrent": 2,
                "current_load": 0,
            },
        }

        # Load existing tasks
        self._load_tasks()

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
        """Find the best agent for a given task"""
        candidates = []

        for agent_name, capabilities in self.agent_capabilities.items():
            score = 0

            # Check if agent can handle this task type
            if task.task_type in capabilities["types"]:
                score += 50

            # Check keyword matches
            desc_lower = task.description.lower()
            keyword_matches = sum(
                1 for keyword in capabilities["keywords"] if keyword in desc_lower
            )
            score += keyword_matches * 10

            # Check agent availability (load)
            if capabilities["current_load"] < capabilities["max_concurrent"]:
                score += 20
            else:
                score -= 50  # Heavy penalty for overloaded agents

            # Priority bonus for high-priority tasks
            if task.priority == TaskPriority.CRITICAL:
                score += 30
            elif task.priority == TaskPriority.HIGH:
                score += 15

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
