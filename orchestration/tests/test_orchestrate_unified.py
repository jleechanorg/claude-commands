"""Tests for the unified orchestration system."""

import os
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

# Add orchestration directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fixtures import mock_claude_fixture, mock_redis_fixture, mock_tmux_fixture
from orchestrate_unified import UnifiedOrchestration


class TestUnifiedOrchestration(unittest.TestCase):
    """Test the main orchestration system."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.test_dir)

        # Ensure result directories exist
        os.makedirs('/tmp/orchestration_results', exist_ok=True)
        os.makedirs('/tmp/orchestration_logs', exist_ok=True)

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.old_cwd)
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_basic_task_flow(self):
        """Test: User request → orchestrate_unified → task_dispatcher → agent creation"""

        with mock_tmux_fixture() as mock_tmux, \
             mock_claude_fixture() as mock_claude, \
             mock_redis_fixture() as mock_redis:

            # Given: A simple task request
            task = "Fix all failing tests"

            # When: orchestrate_unified.py is called
            orchestration = UnifiedOrchestration()
            orchestration.orchestrate(task)

            # Then: Verify the call chain

            # 1. Verify task dispatcher was called to create agents
            assert len(mock_tmux.sessions) > 0, "No tmux sessions created"

            # 2. Verify agent was created with correct name pattern
            session_names = list(mock_tmux.sessions.keys())
            agent_session = session_names[0]
            assert agent_session.startswith('task-agent-'), \
                f"Agent session name doesn't match pattern: {agent_session}"

            # 3. Verify tmux session was created
            assert 'new-session' in str(mock_tmux.call_history)

            # 4. Verify claude was called with correct model
            assert mock_claude.assert_called_with_model('sonnet')

            # 5. Verify prompt file was used
            assert mock_claude.assert_called_with_prompt_file()

    def test_redis_integration_success(self):
        """Test: Agent creation → Redis registration when available"""

        with mock_tmux_fixture() as mock_tmux, \
             mock_claude_fixture() as mock_claude, \
             mock_redis_fixture() as mock_redis:

            # Given: Redis is available
            task = "Create new feature"

            # When: Agent is created
            orchestration = UnifiedOrchestration()
            orchestration.orchestrate(task)

            # Then: Verify Redis registration

            # 1. Verify agent was registered in Redis
            agent_keys = [key for key in mock_redis.hashes.keys() if key.startswith('agent:')]
            self.assertGreater(len(agent_keys), 0, "No agents registered in Redis")

            # 2. Verify agent data structure
            agent_key = agent_keys[0]
            agent_data = mock_redis.hgetall(agent_key)
            self.assertIn('type', agent_data)
            self.assertIn('capabilities', agent_data)
            self.assertIn('status', agent_data)
            self.assertEqual(agent_data['status'], 'active')

    def test_redis_fallback_behavior(self):
        """Test: Redis unavailable → File-based coordination"""

        with mock_tmux_fixture() as mock_tmux, \
             mock_claude_fixture() as mock_claude, \
             mock_redis_fixture(should_fail=True) as mock_redis:

            # Given: Redis connection fails
            task = "Run tests and fix failures"

            # When: System starts
            orchestration = UnifiedOrchestration()
            orchestration.orchestrate(task)

            # Then: Verify fallback behavior

            # 1. Verify file-based coordination activated
            self.assertIsNone(orchestration.message_broker,
                            "Message broker should be None when Redis fails")

            # 2. Verify result files created
            self.assertTrue(os.path.exists('/tmp/orchestration_results'),
                          "Result directory not created")

            # 3. Verify agent still created despite Redis failure
            self.assertGreater(len(mock_tmux.sessions), 0,
                             "Agent should be created even when Redis fails")

    def test_dependency_checking(self):
        """Test: System checks required dependencies"""

        with mock_tmux_fixture(), mock_claude_fixture(), mock_redis_fixture():

            # Test with missing dependencies
            with patch('subprocess.run') as mock_run:
                mock_run.return_value = Mock(returncode=1)  # Simulate missing command

                orchestration = UnifiedOrchestration()

                # Should detect missing dependencies
                has_deps = orchestration._check_dependencies()
                self.assertFalse(has_deps, "Should detect missing dependencies")

    def test_agent_workspace_creation(self):
        """Test: Agent gets unique workspace and branch"""

        with mock_tmux_fixture() as mock_tmux, \
             mock_claude_fixture() as mock_claude, \
             mock_redis_fixture():

            # Setup git mock
            with patch('subprocess.run') as mock_git:
                mock_git.return_value = Mock(returncode=0)

                # Given: Task request
                task = "Update documentation"

                # When: Agent created
                orchestration = UnifiedOrchestration()
                orchestration.orchestrate(task)

                # Then: Verify git worktree was created
                git_calls = [call.args[0] for call in mock_git.call_args_list
                           if call.args and 'git' in call.args[0][0]]

                worktree_calls = [call for call in git_calls
                                if 'worktree' in call and 'add' in call]

                self.assertGreater(len(worktree_calls), 0,
                                 "Git worktree should be created")

                # Verify worktree created from main branch
                worktree_call = worktree_calls[0]
                self.assertIn('main', worktree_call,
                            "Worktree should be created from main branch")

    def test_multiple_agent_creation(self):
        """Test: System can handle multiple agents if needed"""

        with mock_tmux_fixture() as mock_tmux, \
             mock_claude_fixture() as mock_claude, \
             mock_redis_fixture():

            # Given: Complex task that might require multiple agents
            task = "Refactor entire codebase, update docs, and run full test suite"

            # When: Task analyzed
            orchestration = UnifiedOrchestration()
            orchestration.orchestrate(task)

            # Then: Verify at least one agent created
            # Note: Current implementation creates 1 agent, but architecture supports multiple
            self.assertGreaterEqual(len(mock_tmux.sessions), 1,
                                  "At least one agent should be created")

            # Verify each agent has unique name
            session_names = list(mock_tmux.sessions.keys())
            unique_names = set(session_names)
            self.assertEqual(len(session_names), len(unique_names),
                           "All agent names should be unique")

    def test_agent_prompt_includes_mandatory_steps(self):
        """Test: Agent prompt includes mandatory PR creation steps"""

        with mock_tmux_fixture(), mock_claude_fixture() as mock_claude, mock_redis_fixture():

            # Given: Task request
            task = "Fix security vulnerability"

            # When: Agent created
            orchestration = UnifiedOrchestration()
            orchestration.orchestrate(task)

            # Then: Verify prompt file contains mandatory steps
            claude_calls = mock_claude.call_history
            self.assertGreater(len(claude_calls), 0, "Claude should be called")

            # Find calls with prompt files
            prompt_file_calls = []
            for call in claude_calls:
                cmd = call['cmd']
                for arg in cmd:
                    if arg.startswith('@'):
                        prompt_file = arg[1:]
                        if os.path.exists(prompt_file):
                            with open(prompt_file) as f:
                                prompt_content = f.read()
                                prompt_file_calls.append(prompt_content)

            self.assertGreater(len(prompt_file_calls), 0, "Should have prompt file calls")

            # Verify mandatory steps in prompt
            prompt_content = prompt_file_calls[0]
            self.assertIn('gh pr create', prompt_content,
                        "Prompt should include PR creation command")
            self.assertIn('MANDATORY COMPLETION STEPS', prompt_content,
                        "Prompt should include mandatory steps section")
            self.assertIn('FAILURE TO CREATE PR = INCOMPLETE TASK', prompt_content,
                        "Prompt should include PR creation failure warning")


if __name__ == '__main__':
    unittest.main()
