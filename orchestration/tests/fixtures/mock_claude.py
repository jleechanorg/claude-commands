"""Mock fixtures for Claude CLI operations in orchestration tests."""

import os
from contextlib import contextmanager
from unittest.mock import Mock, patch


class MockClaude:
    """Mock Claude CLI handler."""

    def __init__(self):
        self.call_history = []
        self.responses = {}
        self.default_response = Mock(returncode=0, stdout="Task completed successfully", stderr="")

    def set_response(self, task_pattern, response):
        """Set mock response for specific task patterns."""
        self.responses[task_pattern] = response

    def mock_subprocess_run(self, cmd, **kwargs):
        """Mock subprocess.run for claude commands."""
        self.call_history.append({"cmd": cmd, "kwargs": kwargs, "cwd": kwargs.get("cwd", os.getcwd())})

        if not cmd or "claude" not in str(cmd[0]):
            # Not a claude command, pass through
            return Mock(returncode=1, stdout="", stderr="command not found")

        # Check for which command to mock 'which claude'
        if len(cmd) == 2 and cmd[0] == "which" and cmd[1] == "claude":
            return Mock(returncode=0, stdout="/usr/local/bin/claude", stderr="")

        # Mock claude execution
        return self._handle_claude_execution(cmd, **kwargs)

    def _handle_claude_execution(self, cmd, **kwargs):
        """Handle claude CLI execution."""
        # Extract prompt file if using @prompt_file syntax
        prompt_content = ""
        for arg in cmd:
            if arg.startswith("@"):
                prompt_file = arg[1:]
                if os.path.exists(prompt_file):
                    with open(prompt_file) as f:
                        prompt_content = f.read()

        # Check for matching response patterns
        for pattern, response in self.responses.items():
            if pattern.lower() in prompt_content.lower():
                return response

        # Simulate successful task completion
        return self._simulate_successful_completion(cmd, **kwargs)

    def _simulate_successful_completion(self, cmd, **kwargs):
        """Simulate a successful Claude task completion."""
        cwd = kwargs.get("cwd", os.getcwd())

        # Simulate creating some files to show work was done
        if cwd and os.path.exists(cwd):
            # Create a simple test file to show agent worked
            test_file = os.path.join(cwd, "agent_work_completed.txt")
            with open(test_file, "w") as f:
                f.write("Agent completed task successfully\n")

        return Mock(
            returncode=0,
            stdout="Task completed. Changes committed and PR created.",
            stderr="",
        )

    def get_last_call(self):
        """Get the last claude command that was called."""
        return self.call_history[-1] if self.call_history else None

    def get_calls_for_agent(self, agent_name):
        """Get all calls made for a specific agent."""
        agent_calls = []
        for call in self.call_history:
            if agent_name in str(call["cmd"]) or agent_name in call["cwd"]:
                agent_calls.append(call)
        return agent_calls

    def assert_called_with_model(self, model_name="sonnet"):
        """Assert that claude was called with the specified model."""
        for call in self.call_history:
            cmd = call["cmd"]
            if "--model" in cmd:
                model_index = cmd.index("--model")
                if model_index + 1 < len(cmd) and cmd[model_index + 1] == model_name:
                    return True
        return False

    def assert_called_with_prompt_file(self):
        """Assert that claude was called with a prompt file."""
        for call in self.call_history:
            cmd = call["cmd"]
            for arg in cmd:
                if arg.startswith("@"):
                    return True
        return False


@contextmanager
def mock_claude_fixture():
    """Fixture that provides a mock Claude environment."""
    mock_claude = MockClaude()

    with patch("subprocess.run", side_effect=mock_claude.mock_subprocess_run):
        yield mock_claude


class MockClaudeAgent:
    """Mock agent that simulates Claude behavior in tests."""

    def __init__(self, agent_name, task_description):
        self.agent_name = agent_name
        self.task_description = task_description
        self.completed = False
        self.pr_created = False
        self.work_files = []

    def simulate_work(self, workspace_dir):
        """Simulate agent doing work in workspace."""
        # Create some files to show work was done
        work_file = os.path.join(workspace_dir, f"{self.agent_name}_work.txt")
        with open(work_file, "w") as f:
            f.write(f"Work completed for: {self.task_description}\n")
            f.write(f"Agent: {self.agent_name}\n")

        self.work_files.append(work_file)
        return work_file

    def simulate_pr_creation(self):
        """Simulate PR creation."""
        self.pr_created = True
        return {
            "number": 12345,
            "url": "https://github.com/test/repo/pull/12345",
            "title": f"Agent {self.agent_name}: {self.task_description}",
        }

    def complete_task(self):
        """Mark task as completed."""
        self.completed = True
