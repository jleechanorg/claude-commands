"""Tests for the task dispatcher system."""

import os
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

# Add orchestration directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fixtures import mock_claude_fixture, mock_tmux_fixture
from task_dispatcher import TaskDispatcher


class TestTaskDispatcher(unittest.TestCase):
    """Test the task dispatcher functionality."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.test_dir)

        # Create orchestration directory structure
        self.orchestration_dir = os.path.join(self.test_dir, 'orchestration')
        os.makedirs(self.orchestration_dir, exist_ok=True)
        os.makedirs('/tmp/orchestration_results', exist_ok=True)
        os.makedirs('/tmp/orchestration_logs', exist_ok=True)

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.old_cwd)
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_task_analysis_and_agent_creation(self):
        """Test: Task analysis creates appropriate agent specification"""

        # Given: Task dispatcher
        dispatcher = TaskDispatcher(self.orchestration_dir)

        # When: Task is analyzed
        task_description = "Fix all failing unit tests"
        agents = dispatcher.analyze_task_and_create_agents(task_description)

        # Then: Verify agent specification
        self.assertEqual(len(agents), 1, "Should create exactly one agent")

        agent_spec = agents[0]
        self.assertIn('name', agent_spec)
        self.assertIn('type', agent_spec)
        self.assertIn('focus', agent_spec)
        self.assertIn('capabilities', agent_spec)
        self.assertIn('prompt', agent_spec)

        # Verify agent name pattern
        self.assertTrue(agent_spec['name'].startswith('task-agent-'),
                       f"Agent name should start with 'task-agent-': {agent_spec['name']}")

        # Verify task description is included
        self.assertEqual(agent_spec['focus'], task_description)
        self.assertIn(task_description, agent_spec['prompt'])

    def test_dynamic_agent_creation_flow(self):
        """Test: create_dynamic_agent follows complete flow"""

        with mock_tmux_fixture() as mock_tmux, mock_claude_fixture() as mock_claude:

            # Given: Task dispatcher and agent specification
            dispatcher = TaskDispatcher(self.orchestration_dir)
            agent_spec = {
                'name': 'test-agent-1234',
                'type': 'development',
                'focus': 'Test task',
                'capabilities': ['testing', 'git'],
                'prompt': 'Complete the test task'
            }

            # Mock git operations
            with patch('subprocess.run') as mock_git:
                mock_git.return_value = Mock(returncode=0)

                # When: Agent is created
                success = dispatcher.create_dynamic_agent(agent_spec)

                # Then: Verify creation success
                self.assertTrue(success, "Agent creation should succeed")

                # Verify tmux session was created
                self.assertIn('test-agent-1234', mock_tmux.sessions)

                # Verify git worktree was created
                git_calls = [call.args[0] for call in mock_git.call_args_list
                           if call.args and len(call.args[0]) > 0 and 'git' in call.args[0][0]]

                worktree_calls = [call for call in git_calls
                                if len(call) > 1 and 'worktree' in call]
                self.assertGreater(len(worktree_calls), 0, "Git worktree should be created")

    def test_agent_workspace_isolation(self):
        """Test: Each agent gets isolated workspace"""

        with mock_tmux_fixture(), mock_claude_fixture():

            # Given: Multiple agent specifications
            dispatcher = TaskDispatcher(self.orchestration_dir)
            agent_specs = [
                {
                    'name': 'agent-1',
                    'type': 'development',
                    'focus': 'Task 1',
                    'capabilities': ['testing'],
                    'prompt': 'Do task 1'
                },
                {
                    'name': 'agent-2',
                    'type': 'development',
                    'focus': 'Task 2',
                    'capabilities': ['coding'],
                    'prompt': 'Do task 2'
                }
            ]

            with patch('subprocess.run') as mock_subprocess:
                mock_subprocess.return_value = Mock(returncode=0)

                # When: Both agents are created
                success1 = dispatcher.create_dynamic_agent(agent_specs[0])
                success2 = dispatcher.create_dynamic_agent(agent_specs[1])

                # Then: Both should succeed
                self.assertTrue(success1 and success2, "Both agents should be created")

                # Verify unique workspaces
                expected_workspace1 = os.path.join(self.test_dir, 'agent_workspace_agent-1')
                expected_workspace2 = os.path.join(self.test_dir, 'agent_workspace_agent-2')

                # Check that git worktree calls were made for both workspaces
                git_calls = [call.args[0] for call in mock_subprocess.call_args_list
                           if call.args and len(call.args[0]) > 0 and 'git' in call.args[0][0]]

                workspace_paths = []
                for call in git_calls:
                    if 'worktree' in call and 'add' in call:
                        # Extract workspace path from git worktree add command
                        if len(call) > 4:  # git worktree add -b branch_name workspace_path main
                            workspace_paths.append(call[4])

                self.assertEqual(len(set(workspace_paths)), 2,
                               "Should create unique workspaces for each agent")

    def test_agent_name_collision_avoidance(self):
        """Test: Agent names are unique even with rapid creation"""

        with mock_tmux_fixture(), mock_claude_fixture():

            dispatcher = TaskDispatcher(self.orchestration_dir)

            # Given: Multiple rapid agent creation requests
            base_name = "task-agent"
            created_names = []

            with patch('subprocess.run') as mock_subprocess:
                mock_subprocess.return_value = Mock(returncode=0)

                # When: Multiple agents created rapidly
                for i in range(3):
                    agents = dispatcher.analyze_task_and_create_agents(f"Task {i}")
                    if agents:
                        created_names.append(agents[0]['name'])
                        dispatcher.create_dynamic_agent(agents[0])

                # Then: All names should be unique
                unique_names = set(created_names)
                self.assertEqual(len(created_names), len(unique_names),
                               f"All agent names should be unique: {created_names}")

    # Removed task type and priority inference tests - these features were over-engineered
    # and added unnecessary complexity. The current approach simplifies task handling by
    # creating general task agents without categorizing tasks by type or priority. This
    # ensures a more flexible and streamlined system.

    def test_agent_limit_enforcement(self):
        """Test: System respects maximum concurrent agent limit"""

        with mock_tmux_fixture(), mock_claude_fixture():

            dispatcher = TaskDispatcher(self.orchestration_dir)

            # Mock the MAX_CONCURRENT_AGENTS limit to a small number for testing
            with patch('task_dispatcher.MAX_CONCURRENT_AGENTS', 2):

                with patch('subprocess.run') as mock_subprocess:
                    mock_subprocess.return_value = Mock(returncode=0)

                    # Given: Multiple agent creation attempts beyond limit
                    agent_specs = []
                    for i in range(4):  # Try to create 4 agents (limit is 2)
                        spec = {
                            'name': f'test-agent-{i}',
                            'type': 'development',
                            'focus': f'Task {i}',
                            'capabilities': ['testing'],
                            'prompt': f'Do task {i}'
                        }
                        agent_specs.append((spec, dispatcher.create_dynamic_agent(spec)))

                    # Then: Only first 2 should succeed
                    successful_creations = sum(1 for spec, success in agent_specs if success)
                    self.assertEqual(successful_creations, 2,
                                   "Should respect maximum agent limit")

    def test_basic_prompt_structure(self):
        """Test: Generated prompts have basic structure"""

        dispatcher = TaskDispatcher(self.orchestration_dir)

        # Given: Task description
        task = "Implement user authentication"

        # When: Agent specification is created
        agents = dispatcher.analyze_task_and_create_agents(task)

        # Then: Basic prompt structure should be present
        self.assertEqual(len(agents), 1)
        prompt = agents[0]['prompt']

        # Verify basic elements (detailed mandatory steps are added in create_dynamic_agent)
        basic_elements = [
            'Task: Implement user authentication',
            'Execute the task exactly as requested',
            'Complete the task, then commit and create a PR'
        ]

        for element in basic_elements:
            self.assertIn(element, prompt,
                        f"Prompt should contain '{element}'")

    def test_fresh_branch_from_main(self):
        """Test: Agents always create fresh branches from main"""

        with mock_tmux_fixture(), mock_claude_fixture():

            dispatcher = TaskDispatcher(self.orchestration_dir)
            agent_spec = {
                'name': 'test-agent-main',
                'type': 'development',
                'focus': 'Test main branch',
                'capabilities': ['git'],
                'prompt': 'Test task'
            }

            with patch('subprocess.run') as mock_git:
                mock_git.return_value = Mock(returncode=0)

                # When: Agent is created
                dispatcher.create_dynamic_agent(agent_spec)

                # Then: Verify git worktree uses main as source
                git_calls = [call.args[0] for call in mock_git.call_args_list
                           if call.args and 'git' in call.args[0][0]]

                worktree_calls = [call for call in git_calls
                                if 'worktree' in call and 'add' in call]

                self.assertGreater(len(worktree_calls), 0, "Should create git worktree")

                # Check that 'main' is specified as the source
                worktree_call = worktree_calls[0]
                self.assertIn('main', worktree_call,
                            "Worktree should be created from main branch")

    def test_pr_detection_patterns(self):
        """Test various PR detection patterns."""
        dispatcher = TaskDispatcher(self.orchestration_dir)

        # Test cases: (task_description, expected_mode, description)
        test_cases = [
            # UPDATE mode patterns - explicit PR number
            ("fix PR #123", "update", "Explicit PR number with fix"),
            ("adjust pull request #456", "update", "Explicit PR with adjust"),
            ("update PR #789", "update", "Explicit PR with update"),
            ("PR #100 needs better error handling", "update", "PR number at start"),
            ("add logging to PR #200", "update", "Add something to PR"),

            # UPDATE mode patterns - contextual references
            ("adjust the PR", "update", "Contextual PR with adjust"),
            ("fix that pull request", "update", "Contextual PR with fix"),
            ("the PR needs more tests", "update", "The PR needs pattern"),
            ("continue with the PR", "update", "Continue with PR"),
            ("update the existing PR", "update", "Existing PR reference"),

            # CREATE mode patterns - no PR mentioned
            ("implement user authentication", "create", "Feature without PR"),
            ("fix the login bug", "create", "Bug fix without PR"),
            ("create new feature for exports", "create", "New feature task"),
            ("add dark mode support", "create", "Enhancement without PR"),

            # CREATE mode patterns - explicit new PR
            ("create new PR for refactoring", "create", "Explicit new PR"),
            ("start fresh pull request for API", "create", "Fresh PR request"),
        ]

        for task, expected_mode, description in test_cases:
            with self.subTest(description=description):
                pr_number, detected_mode = dispatcher._detect_pr_context(task)
                self.assertEqual(detected_mode, expected_mode,
                               f"{description}: Expected {expected_mode}, got {detected_mode}")

    def test_agent_prompt_generation_for_pr_modes(self):
        """Test that agent prompts are correctly generated for each PR mode."""
        dispatcher = TaskDispatcher(self.orchestration_dir)

        # Test UPDATE mode with PR number
        agents = dispatcher.analyze_task_and_create_agents("fix the typo in PR #950")
        agent = agents[0]
        pr_context = agent.get('pr_context', None)

        self.assertIsNotNone(pr_context, "PR context should be set for UPDATE mode")
        self.assertEqual(pr_context.get('mode'), 'update')
        self.assertEqual(pr_context.get('pr_number'), '950')
        self.assertIn('UPDATE MODE', agent['prompt'])
        self.assertIn('gh pr checkout', agent['prompt'])

        # Test CREATE mode
        agents = dispatcher.analyze_task_and_create_agents("implement new caching system")
        agent = agents[0]
        pr_context = agent.get('pr_context', None)

        self.assertIsNone(pr_context, "PR context should be None for CREATE mode")
        self.assertIn('NEW PR MODE', agent['prompt'])
        self.assertIn('new branch from main', agent['prompt'])

        # Test UPDATE mode without PR number (ambiguous)
        # Mock _find_recent_pr to return None for this test
        with patch.object(dispatcher, '_find_recent_pr', return_value=None):
            agents = dispatcher.analyze_task_and_create_agents("fix the issues in the PR")
            agent = agents[0]
            pr_context = agent.get('pr_context', None)

            self.assertIsNotNone(pr_context, "PR context should be set for ambiguous UPDATE")
            self.assertEqual(pr_context.get('mode'), 'update')
            self.assertIsNone(pr_context.get('pr_number'))
            self.assertIn('Which PR should I update?', agent['prompt'])


if __name__ == '__main__':
    unittest.main()
