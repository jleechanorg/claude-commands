"""Simple integration test for the orchestration system."""

import os
import tempfile
import unittest
from unittest.mock import Mock, patch
import sys

# Add orchestration directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from orchestrate_unified import UnifiedOrchestration
from fixtures import mock_tmux_fixture, mock_claude_fixture, mock_redis_fixture


class TestSimpleOrchestrationFlow(unittest.TestCase):
    """Test the simple, actual orchestration flow that exists."""

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

    def test_simple_task_creates_agent(self):
        """Test: Simple task creates one general agent"""

        with mock_tmux_fixture() as mock_tmux, \
             mock_claude_fixture() as mock_claude, \
             mock_redis_fixture() as mock_redis:

            # Given: A simple task
            task = "Fix the failing tests"

            # Mock git operations
            with patch('subprocess.run') as mock_git:
                mock_git.return_value = Mock(returncode=0)

                # When: Orchestration runs
                orchestration = UnifiedOrchestration()
                orchestration.orchestrate(task)

                # Then: Verify simple flow

                # 1. One tmux session created
                self.assertEqual(len(mock_tmux.sessions), 1, "Should create exactly one agent")

                # 2. Agent name follows pattern
                agent_name = list(mock_tmux.sessions.keys())[0]
                self.assertTrue(agent_name.startswith('task-agent-'),
                              f"Agent name should start with 'task-agent-': {agent_name}")

                # 3. Git worktree created
                git_calls = [call.args[0] for call in mock_git.call_args_list
                           if call.args and len(call.args[0]) > 0 and 'git' in call.args[0][0]]
                worktree_calls = [call for call in git_calls if 'worktree' in call]
                self.assertGreater(len(worktree_calls), 0, "Should create git worktree")

                # 4. Claude called with sonnet model
                self.assertTrue(mock_claude.assert_called_with_model('sonnet'))

    def test_redis_is_optional(self):
        """Test: System works whether Redis is available or not"""

        # Test with Redis available
        with mock_tmux_fixture() as mock_tmux, \
             mock_claude_fixture(), \
             mock_redis_fixture():

            with patch('subprocess.run') as mock_git:
                mock_git.return_value = Mock(returncode=0)

                orchestration = UnifiedOrchestration()
                orchestration.orchestrate("Test with Redis")

                # Should work fine
                self.assertEqual(len(mock_tmux.sessions), 1)
                self.assertIsNotNone(orchestration.message_broker)

        # Test with Redis unavailable
        with mock_tmux_fixture() as mock_tmux, \
             mock_claude_fixture(), \
             mock_redis_fixture(should_fail=True):

            with patch('subprocess.run') as mock_git:
                mock_git.return_value = Mock(returncode=0)

                orchestration = UnifiedOrchestration()
                orchestration.orchestrate("Test without Redis")

                # Should still work
                self.assertEqual(len(mock_tmux.sessions), 1)
                self.assertIsNone(orchestration.message_broker)

    def test_agent_gets_proper_workspace(self):
        """Test: Agent gets unique workspace directory"""

        with mock_tmux_fixture(), mock_claude_fixture(), mock_redis_fixture():

            with patch('subprocess.run') as mock_git:
                mock_git.return_value = Mock(returncode=0)

                # When: Agent created
                orchestration = UnifiedOrchestration()
                orchestration.orchestrate("Create feature")

                # Then: Git worktree should be called with proper parameters
                git_calls = [call.args[0] for call in mock_git.call_args_list
                           if call.args and len(call.args[0]) > 0 and 'git' in call.args[0][0]]

                worktree_calls = [call for call in git_calls
                                if 'worktree' in call and 'add' in call and 'main' in call]

                self.assertGreater(len(worktree_calls), 0,
                                 "Should create worktree from main branch")


if __name__ == '__main__':
    unittest.main()
