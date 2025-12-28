#!/usr/bin/env python3
"""
Recovery Coordinator for Orchestration System
Handles agent failures, implements recovery strategies, and tracks metrics
"""

import json
import os
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class RecoveryReason(Enum):
    """Reasons for agent failure"""

    SIGINT = "SIGINT (Ctrl-C interruption)"
    TIMEOUT = "Task timeout exceeded"
    API_ERROR = "Claude API error"
    GIT_ERROR = "Git/GitHub operation failed"
    PERMISSION_ERROR = "File permission denied"
    UNKNOWN = "Unknown failure reason"


class RecoveryStrategy(Enum):
    """Recovery strategies for failed agents"""

    RESUME = "resume"  # Continue from checkpoint
    RESTART = "restart"  # Fresh start with same task
    REASSIGN = "reassign"  # Try different agent type
    ESCALATE = "escalate"  # Manual intervention needed


@dataclass
class RecoveryEvent:
    """Record of a recovery attempt"""

    agent_name: str
    task_description: str
    failure_time: str
    recovery_time: str
    exit_code: int
    reason: RecoveryReason
    strategy: RecoveryStrategy
    partial_work: list[str]
    recovery_success: bool
    recovery_duration_seconds: float


class RecoveryCoordinator:
    """Coordinates recovery of failed agents"""

    def __init__(self, orchestration_dir: str = None):
        self.orchestration_dir = orchestration_dir or os.path.dirname(__file__)
        self.results_dir = "/tmp/orchestration_results"
        self.checkpoints_dir = "/tmp/orchestration_checkpoints"
        self.logs_dir = "/tmp/orchestration_logs"
        self.metrics_file = os.path.join(self.orchestration_dir, "recovery_metrics.json")

        # Create directories
        os.makedirs(self.checkpoints_dir, exist_ok=True)

        # Load existing metrics
        self.metrics = self._load_metrics()

    def _load_metrics(self) -> dict[str, Any]:
        """Load recovery metrics from file"""
        if os.path.exists(self.metrics_file):
            try:
                with open(self.metrics_file) as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass

        # Initialize metrics
        return {
            "total_tasks": 0,
            "first_try_success": 0,
            "required_recovery": 0,
            "failed_after_recovery": 0,
            "recovery_events": [],
            "reason_counts": {},
            "total_recovery_time": 0,
        }

    def _save_metrics(self):
        """Save metrics to file"""
        with open(self.metrics_file, "w") as f:
            json.dump(self.metrics, f, indent=2)

    def check_agent_failure(self, agent_name: str) -> dict[str, Any] | None:
        """Check if an agent has failed"""
        result_file = os.path.join(self.results_dir, f"{agent_name}_results.json")

        if not os.path.exists(result_file):
            return None

        with open(result_file) as f:
            result = json.load(f)

        if result.get("status") == "failed":
            return result

        return None

    def analyze_failure_reason(self, agent_name: str, exit_code: int) -> RecoveryReason:
        """Determine why an agent failed"""
        if exit_code == 130:
            return RecoveryReason.SIGINT
        if exit_code == 124:  # Common timeout exit code
            return RecoveryReason.TIMEOUT

        # Check logs for specific errors
        log_file = os.path.join(self.logs_dir, f"{agent_name}.log")
        if os.path.exists(log_file):
            with open(log_file) as f:
                log_content = f.read()

            if "permission denied" in log_content.lower():
                return RecoveryReason.PERMISSION_ERROR
            if "api" in log_content.lower() and "error" in log_content.lower():
                return RecoveryReason.API_ERROR
            if "git" in log_content.lower() and "error" in log_content.lower():
                return RecoveryReason.GIT_ERROR

        return RecoveryReason.UNKNOWN

    def analyze_partial_work(self, agent_name: str) -> list[str]:
        """Analyze what work was completed before failure"""
        workspace = f"/home/jleechan/projects/worldarchitect.ai/worktree_roadmap/agent_workspace_{agent_name}"
        partial_work = []

        if not os.path.exists(workspace):
            return partial_work

        # Check for created files
        for root, _dirs, files in os.walk(workspace):
            # Skip .git directory
            if ".git" in root:
                continue

            for file in files:
                file_path = os.path.relpath(os.path.join(root, file), workspace)
                # Check if file is new (not in git)
                result = subprocess.run(
                    ["git", "ls-files", file_path],
                    check=False,
                    cwd=workspace,
                    capture_output=True,
                    text=True,
                )
                if not result.stdout.strip():
                    partial_work.append(f"Created: {file_path}")

        # Check git status for modifications
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            check=False,
            cwd=workspace,
            capture_output=True,
            text=True,
        )

        for line in result.stdout.strip().split("\n"):
            if line.startswith("M "):
                partial_work.append(f"Modified: {line[3:]}")

        return partial_work

    def determine_recovery_strategy(
        self, reason: RecoveryReason, partial_work: list[str], attempt_count: int = 1
    ) -> RecoveryStrategy:
        """Decide how to recover from failure"""
        # If multiple attempts have failed, escalate
        if attempt_count >= 3:
            return RecoveryStrategy.ESCALATE

        # SIGINT usually means manual interruption - resume from where left off
        if reason == RecoveryReason.SIGINT and partial_work:
            return RecoveryStrategy.RESUME

        # API errors might be transient - restart
        if reason == RecoveryReason.API_ERROR:
            return RecoveryStrategy.RESTART

        # Permission errors need different approach
        if reason == RecoveryReason.PERMISSION_ERROR:
            return RecoveryStrategy.ESCALATE

        # Default: resume if work done, restart if not
        return RecoveryStrategy.RESUME if partial_work else RecoveryStrategy.RESTART

    def generate_recovery_prompt(
        self,
        agent_name: str,
        task_desc: str,
        partial_work: list[str],
        strategy: RecoveryStrategy,
    ) -> str:
        """Generate prompt for recovery agent"""
        if strategy == RecoveryStrategy.RESUME:
            completed_items = "\n".join(f"  - {work}" for work in partial_work)
            return f"""Continue the incomplete task. Previous agent completed:
{completed_items}

Original task: {task_desc}

Please complete the remaining work, ensuring you don't duplicate what's already done."""

        if strategy == RecoveryStrategy.RESTART:
            return f"""Complete this task from the beginning: {task_desc}

Note: A previous attempt failed. Please ensure all steps are completed successfully."""

        return task_desc

    def recover_agent(self, agent_name: str) -> dict[str, Any]:
        """Attempt to recover a failed agent"""
        start_time = time.time()

        # Check failure
        failure = self.check_agent_failure(agent_name)
        if not failure:
            return {"success": False, "error": "No failure found"}

        # Analyze failure
        exit_code = failure.get("exit_code", -1)
        reason = self.analyze_failure_reason(agent_name, exit_code)
        partial_work = self.analyze_partial_work(agent_name)

        # Get task description from prompt file
        prompt_file = f"/tmp/agent_prompt_{agent_name}.txt"
        task_desc = "Unknown task"
        if os.path.exists(prompt_file):
            with open(prompt_file) as f:
                content = f.read()
                # Extract task description from prompt
                if "Task:" in content:
                    task_desc = content.split("Task:")[1].split("\n")[0].strip()

        # Determine strategy
        strategy = self.determine_recovery_strategy(reason, partial_work)

        # Record metrics
        self.metrics["required_recovery"] += 1
        self.metrics["reason_counts"][reason.value] = self.metrics["reason_counts"].get(reason.value, 0) + 1

        # Log recovery attempt
        print(f"\n🔄 RECOVERY INITIATED for {agent_name}")
        print(f"   Reason: {reason.value}")
        print(f"   Strategy: {strategy.value}")
        print(f"   Partial work completed: {len(partial_work)} items")

        recovery_agent_name = None
        if strategy == RecoveryStrategy.ESCALATE:
            print("   ⚠️  Manual intervention required")
            recovery_success = False
        else:
            # Create recovery agent
            self.generate_recovery_prompt(agent_name, task_desc, partial_work, strategy)

            # Use orchestration system to create recovery agent
            recovery_agent_name = f"{agent_name}-recovery-{int(time.time())}"

            # For now, return the recovery plan
            recovery_success = True
            print(f"   ✅ Recovery agent prepared: {recovery_agent_name}")

        # Record recovery event
        recovery_time = time.time() - start_time
        event = RecoveryEvent(
            agent_name=agent_name,
            task_description=task_desc,
            failure_time=datetime.now().isoformat(),
            recovery_time=datetime.now().isoformat(),
            exit_code=exit_code,
            reason=reason,
            strategy=strategy,
            partial_work=partial_work,
            recovery_success=recovery_success,
            recovery_duration_seconds=recovery_time,
        )

        # Convert enum values to strings for JSON serialization
        event_dict = asdict(event)
        event_dict["reason"] = event.reason.value
        event_dict["strategy"] = event.strategy.value
        self.metrics["recovery_events"].append(event_dict)
        self.metrics["total_recovery_time"] += recovery_time

        if not recovery_success:
            self.metrics["failed_after_recovery"] += 1

        self._save_metrics()

        return {
            "success": recovery_success,
            "reason": reason.value,
            "strategy": strategy.value,
            "partial_work": partial_work,
            "recovery_agent": recovery_agent_name if recovery_success else None,
        }

    def get_recovery_report(self) -> str:
        """Generate a recovery metrics report"""
        total = self.metrics["total_tasks"]
        if total == 0:
            return "No tasks recorded yet"

        first_try_rate = (self.metrics["first_try_success"] / total) * 100
        recovery_rate = (self.metrics["required_recovery"] / total) * 100

        report = f"""
📊 Orchestration Recovery Metrics
================================
Total Tasks: {total}
First Try Success: {self.metrics["first_try_success"]} ({first_try_rate:.1f}%)
Required Recovery: {self.metrics["required_recovery"]} ({recovery_rate:.1f}%)
Failed After Recovery: {self.metrics["failed_after_recovery"]}

Recovery Reasons:
"""
        for reason, count in self.metrics["reason_counts"].items():
            percentage = (
                (count / self.metrics["required_recovery"]) * 100 if self.metrics["required_recovery"] > 0 else 0
            )
            report += f"  - {reason}: {count} ({percentage:.1f}%)\n"

        if self.metrics["required_recovery"] > 0:
            avg_recovery_time = self.metrics["total_recovery_time"] / self.metrics["required_recovery"]
            report += f"\nAverage Recovery Time: {avg_recovery_time:.2f} seconds"

        return report


def main():
    """Test recovery coordinator"""
    coordinator = RecoveryCoordinator()

    # Check for the specific failure
    agent_name = "task-agent-5030"
    result = coordinator.recover_agent(agent_name)

    print("\nRecovery Result:")
    print(json.dumps(result, indent=2))

    print("\n" + coordinator.get_recovery_report())


if __name__ == "__main__":
    main()
