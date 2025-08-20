#!/usr/bin/env python3
"""
Integration Test for Orchestration System
Tests the full workflow: Agent creation → Task execution → PR creation → Cleanup

This is NOT part of the regular CI test suite - it's a manual integration test
that creates real agents and PRs for testing the orchestration system.
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from typing import Optional

# Add orchestrate module to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from orchestrate import OrchestrationCLI
except ImportError as e:
    print(f"❌ Failed to import orchestrate module: {e}")
    sys.exit(1)


class OrchestrationIntegrationTest:
    """
    Integration test for the orchestration system.

    This test will:
    1. Create an agent using the orchestration system
    2. Give it a simple task (create a test file and PR)
    3. Monitor the agent's progress
    4. Verify the PR was created
    5. Clean up by closing the PR
    """

    def __init__(self):
        self.cli = OrchestrationCLI()
        self.test_id = int(time.time()) % 10000
        self.agent_name = None
        self.pr_number = None
        self.test_start_time = datetime.now()

    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp and level"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def run_command(self, cmd: list, description: str) -> tuple[bool, str]:
        """Run a command and return success status and output"""
        self.log(f"Running: {description}")
        self.log(f"Command: {' '.join(cmd)}")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            success = result.returncode == 0
            output = result.stdout + result.stderr

            if success:
                self.log(f"✅ {description} - SUCCESS", "SUCCESS")
            else:
                self.log(
                    f"❌ {description} - FAILED (exit code: {result.returncode})",
                    "ERROR",
                )

            if output.strip():
                self.log(f"Output: {output.strip()}")

            return success, output

        except subprocess.TimeoutExpired:
            self.log(f"⏰ {description} - TIMEOUT", "ERROR")
            return False, "Command timed out"
        except Exception as e:
            self.log(f"💥 {description} - EXCEPTION: {e}", "ERROR")
            return False, str(e)

    def wait_for_agent_startup(self, agent_name: str, max_wait: int = 30) -> bool:
        """Wait for agent to start up and be ready"""
        self.log(f"Waiting for agent {agent_name} to start up (max {max_wait}s)")

        for i in range(max_wait):
            # Check if tmux session exists
            success, _ = self.run_command(
                ["tmux", "has-session", "-t", agent_name],
                f"Check if {agent_name} session exists",
            )

            if success:
                self.log(f"✅ Agent {agent_name} session is active")
                # Give it a bit more time to initialize Claude
                time.sleep(5)
                return True

            time.sleep(1)

        self.log(f"❌ Agent {agent_name} failed to start within {max_wait}s", "ERROR")
        return False

    def monitor_agent_progress(self, agent_name: str, max_monitor: int = 300) -> bool:
        """Monitor agent progress by checking tmux output"""
        self.log(f"Monitoring agent {agent_name} progress (max {max_monitor}s)")

        start_time = time.time()
        last_output = ""

        while time.time() - start_time < max_monitor:
            # Capture tmux pane content
            success, output = self.run_command(
                ["tmux", "capture-pane", "-t", agent_name, "-p"],
                f"Capture {agent_name} output",
            )

            if success and output != last_output:
                self.log(f"Agent {agent_name} output changed:")
                # Show last 10 lines of output
                lines = output.strip().split("\n")
                for line in lines[-10:]:
                    if line.strip():
                        self.log(f"  {line}")
                last_output = output

                # Check for completion indicators
                if any(
                    indicator in output.lower()
                    for indicator in [
                        "pr #",
                        "pull request",
                        "successfully created",
                        "merge",
                    ]
                ):
                    self.log("🎉 Agent appears to have completed task!", "SUCCESS")
                    return True

                # Check for error indicators
                if any(
                    error in output.lower()
                    for error in ["error:", "failed:", "cannot", "permission denied"]
                ):
                    self.log("⚠️ Agent encountered an error", "WARN")

            time.sleep(10)  # Check every 10 seconds

        self.log(f"⏰ Monitoring timeout after {max_monitor}s", "WARN")
        return False

    def find_created_pr(self) -> Optional[int]:
        """Find the PR number created by the agent"""
        self.log("Searching for PR created by agent")

        # List recent PRs
        success, output = self.run_command(
            [
                "gh",
                "pr",
                "list",
                "--limit",
                "5",
                "--json",
                "number,title,author,createdAt",
            ],
            "List recent PRs",
        )

        if not success:
            return None

        try:
            prs = json.loads(output)
            for pr in prs:
                # Look for PR created recently (within last 10 minutes)
                created_time = datetime.fromisoformat(
                    pr["createdAt"].replace("Z", "+00:00")
                )
                time_diff = (
                    datetime.now(created_time.tzinfo) - created_time
                ).total_seconds()

                if time_diff < 600:  # 10 minutes
                    self.log(f"Found recent PR: #{pr['number']} - {pr['title']}")
                    return pr["number"]

        except (json.JSONDecodeError, KeyError) as e:
            self.log(f"Error parsing PR list: {e}", "ERROR")

        return None

    def create_test_agent(self) -> bool:
        """Create an agent with a specific test task"""
        self.log("=" * 60)
        self.log("STEP 1: Creating test agent")
        self.log("=" * 60)

        # Create a unique task for this test
        task = f"""Create a simple test file and PR for integration test {self.test_id}.

SPECIFIC TASK:
1. Create a file called test_integration_{self.test_id}.txt in the current directory
2. The file should contain: "Integration test {self.test_id} completed at {datetime.now()}"
3. Add this file to git and commit it
4. Create a PR with title "Integration Test {self.test_id}"

IMPORTANT: This is a test - work quickly and efficiently."""

        # Use orchestrate.py to create the agent
        self.log(f"Creating agent with task: {task[:100]}...")

        # Run orchestrate.py with the task
        success, output = self.run_command(
            ["python3", ".claude/commands/orchestrate.py", task],
            "Create agent via orchestrate.py",
        )

        if not success:
            self.log("Failed to create agent", "ERROR")
            return False

        # Extract agent name from output
        lines = output.split("\n")
        for line in lines:
            if "Agent:" in line and "task-agent-" in line:
                # Extract agent name
                parts = line.split()
                for part in parts:
                    if "task-agent-" in part:
                        self.agent_name = part
                        break

        if not self.agent_name:
            self.log("Could not extract agent name from output", "ERROR")
            return False

        self.log(f"✅ Agent created: {self.agent_name}")
        return True

    def wait_and_monitor_agent(self) -> bool:
        """Wait for agent to start and monitor its progress"""
        self.log("=" * 60)
        self.log("STEP 2: Monitoring agent execution")
        self.log("=" * 60)

        # Wait for agent to start
        if not self.wait_for_agent_startup(self.agent_name):
            return False

        # Monitor agent progress
        return self.monitor_agent_progress(self.agent_name)

    def verify_pr_creation(self) -> bool:
        """Verify that the agent created a PR"""
        self.log("=" * 60)
        self.log("STEP 3: Verifying PR creation")
        self.log("=" * 60)

        # Look for the PR
        pr_number = self.find_created_pr()

        if pr_number:
            self.pr_number = pr_number
            self.log(f"✅ Found PR created by agent: #{pr_number}")

            # Get PR details
            success, output = self.run_command(
                ["gh", "pr", "view", str(pr_number), "--json", "title,author,state"],
                f"Get details for PR #{pr_number}",
            )

            if success:
                try:
                    pr_data = json.loads(output)
                    self.log(f"PR Title: {pr_data['title']}")
                    self.log(f"PR Author: {pr_data['author']['login']}")
                    self.log(f"PR State: {pr_data['state']}")
                except json.JSONDecodeError:
                    self.log("Could not parse PR details", "WARN")

            return True
        else:
            self.log("❌ No PR found - agent may not have completed task", "ERROR")
            return False

    def cleanup_agent_and_pr(self) -> bool:
        """Clean up the test agent and close the PR"""
        self.log("=" * 60)
        self.log("STEP 4: Cleanup")
        self.log("=" * 60)

        cleanup_success = True

        # Kill the agent tmux session
        if self.agent_name:
            success, _ = self.run_command(
                ["tmux", "kill-session", "-t", self.agent_name],
                f"Kill agent {self.agent_name}",
            )
            if success:
                self.log(f"✅ Agent {self.agent_name} cleaned up")
            else:
                self.log(f"⚠️ Could not kill agent {self.agent_name}", "WARN")
                cleanup_success = False

        # Close the PR
        if self.pr_number:
            success, _ = self.run_command(
                [
                    "gh",
                    "pr",
                    "close",
                    str(self.pr_number),
                    "--comment",
                    f"Closing integration test PR #{self.pr_number} - test completed",
                ],
                f"Close PR #{self.pr_number}",
            )
            if success:
                self.log(f"✅ PR #{self.pr_number} closed")
            else:
                self.log(f"⚠️ Could not close PR #{self.pr_number}", "WARN")
                cleanup_success = False

        return cleanup_success

    def run_full_test(self) -> bool:
        """Run the complete integration test"""
        self.log("🚀 Starting Orchestration Integration Test")
        self.log(f"Test ID: {self.test_id}")
        self.log(f"Start time: {self.test_start_time}")
        self.log("")

        try:
            # Step 1: Create agent
            if not self.create_test_agent():
                self.log("❌ FAILED: Could not create test agent", "ERROR")
                return False

            # Step 2: Monitor agent
            if not self.wait_and_monitor_agent():
                self.log("❌ FAILED: Agent monitoring failed", "ERROR")
                self.cleanup_agent_and_pr()
                return False

            # Step 3: Verify PR
            if not self.verify_pr_creation():
                self.log("❌ FAILED: PR verification failed", "ERROR")
                self.cleanup_agent_and_pr()
                return False

            # Step 4: Cleanup
            if not self.cleanup_agent_and_pr():
                self.log("⚠️ WARNING: Cleanup had issues", "WARN")

            # Calculate test duration
            end_time = datetime.now()
            duration = (end_time - self.test_start_time).total_seconds()

            self.log("")
            self.log("=" * 60)
            self.log("🎉 INTEGRATION TEST COMPLETED SUCCESSFULLY!")
            self.log(f"Duration: {duration:.1f} seconds")
            self.log(f"Agent: {self.agent_name}")
            self.log(f"PR: #{self.pr_number}")
            self.log("=" * 60)

            return True

        except KeyboardInterrupt:
            self.log("🛑 Test interrupted by user", "WARN")
            self.cleanup_agent_and_pr()
            return False
        except Exception as e:
            self.log(f"💥 Test failed with exception: {e}", "ERROR")
            self.cleanup_agent_and_pr()
            return False


def main():
    """Main entry point for integration test"""
    print("🧪 Orchestration Integration Test")
    print("=" * 60)
    print("This test will:")
    print("1. Create a real agent using the orchestration system")
    print("2. Give it a task to create a test file and PR")
    print("3. Monitor the agent's progress")
    print("4. Verify the PR was created")
    print("5. Clean up by closing the PR")
    print("")
    print("⚠️  WARNING: This test creates real agents and PRs!")
    print("=" * 60)
    print("")

    # Run the test
    test = OrchestrationIntegrationTest()
    success = test.run_full_test()

    # Exit with appropriate code
    if success:
        print("\n✅ Integration test PASSED")
        sys.exit(0)
    else:
        print("\n❌ Integration test FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
