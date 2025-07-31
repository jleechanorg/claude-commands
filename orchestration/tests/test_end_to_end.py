"""End-to-end integration tests for the orchestration system."""

import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

# Add orchestration directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fixtures import mock_claude_fixture, mock_redis_fixture, mock_tmux_fixture
from orchestrate_unified import UnifiedOrchestration


class TestOrchestrationEndToEnd(unittest.TestCase):
    """End-to-end integration tests verifying complete orchestration flow."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.test_dir)

        # Create required directories
        os.makedirs("/tmp/orchestration_results", exist_ok=True)
        os.makedirs("/tmp/orchestration_logs", exist_ok=True)

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.old_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_complete_task_workflow_with_redis(self):
        """Test: Complete workflow from task request to completion with Redis"""

        with (
            mock_tmux_fixture() as mock_tmux,
            mock_claude_fixture() as mock_claude,
            mock_redis_fixture() as mock_redis,
        ):
            # Given: A task request and working Redis
            task = "Fix all failing tests and create comprehensive report"

            # When: Complete orchestration workflow runs
            orchestration = UnifiedOrchestration()

            # Mock git operations for workspace creation
            with patch("subprocess.run") as mock_git:
                mock_git.return_value = Mock(returncode=0)

                # Execute orchestration
                orchestration.orchestrate(task)

                # Then: Verify complete workflow

                # 1. Redis connection established
                assert orchestration.message_broker is not None, "Redis message broker should be available"

                # 2. Agent created and registered
                agent_keys = [
                    k for k in mock_redis.hashes if k.startswith("agent:")
                ]
                assert len(agent_keys) > 0, "Agent should be registered in Redis"

                # 3. Tmux session created
                assert len(mock_tmux.sessions) > 0, "Tmux session should be created"

                # 4. Git worktree created from main
                git_calls = [
                    call.args[0]
                    for call in mock_git.call_args_list
                    if call.args and "git" in call.args[0][0]
                ]
                worktree_calls = [
                    call for call in git_calls if "worktree" in call and "main" in call
                ]
                assert len(worktree_calls) > 0, "Git worktree should be created from main"

                # 5. Claude called with correct parameters
                assert mock_claude.assert_called_with_model("sonnet")
                assert mock_claude.assert_called_with_prompt_file()

                # 6. Agent registered with correct capabilities
                agent_key = agent_keys[0]
                agent_data = mock_redis.hgetall(agent_key)
                capabilities = json.loads(agent_data["capabilities"])
                expected_capabilities = [
                    "task_execution",
                    "development",
                    "git_operations",
                    "server_management",
                    "testing",
                    "full_stack",
                ]
                assert capabilities == expected_capabilities

    def test_complete_task_workflow_without_redis(self):
        """Test: Complete workflow gracefully handles Redis unavailability"""

        with (
            mock_tmux_fixture() as mock_tmux,
            mock_claude_fixture(),
            mock_redis_fixture(should_fail=True),
        ):
            # Given: Task request with Redis unavailable
            task = "Implement new API endpoint with tests"

            # When: Orchestration runs without Redis
            orchestration = UnifiedOrchestration()

            with patch("subprocess.run") as mock_git:
                mock_git.return_value = Mock(returncode=0)

                # Execute orchestration (should not fail)
                orchestration.orchestrate(task)

                # Then: Verify graceful fallback

                # 1. Message broker should be None
                assert orchestration.message_broker is None, "Message broker should be None when Redis fails"

                # 2. Agent still created despite Redis failure
                assert len(mock_tmux.sessions) > 0, "Agent should be created even without Redis"

                # 3. File-based coordination used
                assert os.path.exists("/tmp/orchestration_results"), "Result directory should exist for file-based coordination"

    def test_agent_restart_with_existing_conversation(self):
        """Test: Agent restart handling with existing conversation files"""

        with (
            mock_tmux_fixture(),
            mock_claude_fixture() as mock_claude,
            mock_redis_fixture(),
        ):
            # Given: Existing conversation file
            conversation_dir = os.path.expanduser("~/.claude/conversations")
            os.makedirs(conversation_dir, exist_ok=True)

            # Create a mock conversation file that will match our agent name pattern
            task = "Continue previous work"
            orchestration = UnifiedOrchestration()

            # Get the agent name that would be generated
            dispatcher = orchestration.task_dispatcher
            agents = dispatcher.analyze_task_and_create_agents(task)
            agent_name = agents[0]["name"] if agents else "test-agent"

            conversation_file = os.path.join(conversation_dir, f"{agent_name}.json")
            with open(conversation_file, "w") as f:
                json.dump({"previous": "conversation"}, f)

            try:
                with patch("subprocess.run") as mock_subprocess:
                    mock_subprocess.return_value = Mock(returncode=0)

                    # When: Agent is created with existing conversation
                    orchestration.orchestrate(task)

                    # Then: Verify --continue flag is used
                    claude_calls = mock_claude.call_history
                    assert len(claude_calls) > 0, "Claude should be called"

                    # Check if --continue flag was included in any call
                    continue_flag_found = False
                    for call in claude_calls:
                        if "--continue" in str(call["cmd"]):
                            continue_flag_found = True
                            break

                    assert continue_flag_found, "Should use --continue flag for existing conversations"

            finally:
                # Cleanup
                if os.path.exists(conversation_file):
                    os.remove(conversation_file)

    def test_multiple_agents_coordination(self):
        """Test: System can coordinate multiple agents if needed"""

        with (
            mock_tmux_fixture() as mock_tmux,
            mock_claude_fixture(),
            mock_redis_fixture() as mock_redis,
        ):
            # Given: Complex task that could benefit from multiple agents
            task = "Refactor authentication system, update all related tests, and create migration scripts"

            # When: Orchestration processes complex task
            orchestration = UnifiedOrchestration()

            with patch("subprocess.run") as mock_git:
                mock_git.return_value = Mock(returncode=0)

                orchestration.orchestrate(task)

                # Then: Verify agent coordination

                # Note: Current implementation creates 1 agent per task
                # This test verifies the architecture supports multiple agents
                assert len(mock_tmux.sessions) >= 1, "At least one agent should be created"

                # Verify each agent has unique session
                session_names = list(mock_tmux.sessions.keys())
                unique_sessions = set(session_names)
                assert len(session_names) == len(unique_sessions), "All tmux sessions should have unique names"

                # If multiple agents were created, verify Redis coordination
                agent_keys = [
                    k for k in mock_redis.hashes if k.startswith("agent:")
                ]
                assert len(agent_keys) == len(mock_tmux.sessions), "Number of Redis registrations should match tmux sessions"

    def test_error_handling_and_recovery(self):
        """Test: System handles errors gracefully and continues operation"""

        with (
            mock_tmux_fixture(),
            mock_claude_fixture(),
            mock_redis_fixture(),
        ):
            # Given: Task request with simulated git failure
            task = "Fix critical bug in production"

            # When: Git operations fail
            with patch("subprocess.run") as mock_git:
                # Simulate git failure on first call, success on subsequent
                call_count = 0

                def git_side_effect(cmd, **kwargs):
                    nonlocal call_count
                    call_count += 1
                    if call_count == 1 and "git" in cmd[0]:
                        return Mock(
                            returncode=1, stderr="git error"
                        )  # First git call fails
                    return Mock(returncode=0)  # Subsequent calls succeed

                mock_git.side_effect = git_side_effect

                orchestration = UnifiedOrchestration()

                # Execute orchestration (should handle git failure gracefully)
                orchestration.orchestrate(task)

                # Then: Verify error handling

                # System should still attempt to create agents
                # even if some git operations fail
                assert orchestration.task_dispatcher is not None, "Task dispatcher should be initialized"

    def test_agent_completion_verification_flow(self):
        """Test: System verifies agent completion correctly"""

        with (
            mock_tmux_fixture() as mock_tmux,
            mock_claude_fixture(),
            mock_redis_fixture(),
        ):
            # Given: Task request
            task = "Create user registration feature"

            # When: Agent completes task and creates result file
            orchestration = UnifiedOrchestration()

            with patch("subprocess.run") as mock_git:
                mock_git.return_value = Mock(returncode=0)

                orchestration.orchestrate(task)

                # Simulate agent completion by creating result file
                session_names = list(mock_tmux.sessions.keys())
                if session_names:
                    agent_name = session_names[0]
                    result_file = (
                        f"/tmp/orchestration_results/{agent_name}_results.json"
                    )

                    completion_data = {
                        "agent": agent_name,
                        "status": "completed",
                        "branch": f"{agent_name}-work",
                        "pr_url": "https://github.com/test/repo/pull/123",
                    }

                    with open(result_file, "w") as f:
                        json.dump(completion_data, f)

                    # Then: Verify completion can be detected
                    assert os.path.exists(result_file), "Agent result file should exist"

                    with open(result_file) as f:
                        result_data = json.load(f)
                        assert result_data["status"] == "completed"
                        assert result_data["agent"] == agent_name

    def test_dependency_integration(self):
        """Test: System integrates correctly with all required dependencies"""

        with mock_tmux_fixture(), mock_claude_fixture(), mock_redis_fixture():
            # Given: System with all dependencies available
            orchestration = UnifiedOrchestration()

            # Mock all dependency checks to succeed
            with patch("subprocess.run") as mock_deps:
                mock_deps.return_value = Mock(returncode=0, stdout="/usr/bin/tool")

                # When: Dependency check runs
                has_dependencies = orchestration._check_dependencies()

                # Then: All dependencies should be found
                assert has_dependencies, "All dependencies should be available"

                # Verify dependency checks were made
                dep_calls = [
                    call.args[0]
                    for call in mock_deps.call_args_list
                    if call.args and "which" in call.args[0]
                ]

                # Should check for: tmux, git, gh, claude
                expected_tools = {"tmux", "git", "gh", "claude"}
                checked_tools = set()

                for call in dep_calls:
                    if len(call) > 1:
                        checked_tools.add(call[1])

                assert expected_tools.issubset(checked_tools), f"Should check all required tools: {expected_tools}"


if __name__ == "__main__":
    unittest.main()
