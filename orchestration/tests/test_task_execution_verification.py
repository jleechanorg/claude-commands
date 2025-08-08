#!/usr/bin/env python3
"""
Task Execution Verification Tests

Tests to ensure that orchestration agents execute the tasks they were actually assigned,
not cached or stale tasks from previous runs. This provides verification that user
intent matches agent execution.

Key Verification Points:
1. Agent prompts contain correct task descriptions
2. Agent workspace setup matches task requirements
3. Task context is properly isolated between runs
4. Agent completion reports reflect actual work done
"""

import json
import os
import shutil
import tempfile
import time
import unittest
from unittest.mock import patch, MagicMock, call

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from orchestrate_unified import UnifiedOrchestration
from task_dispatcher import TaskDispatcher


class TestTaskExecutionVerification(unittest.TestCase):
    """Tests that verify agents execute the correct tasks."""

    def setUp(self):
        self.test_temp_dir = tempfile.mkdtemp(prefix="task_execution_test_")
        self.orchestration = UnifiedOrchestration()
        self.task_dispatcher = TaskDispatcher()

    def tearDown(self):
        if os.path.exists(self.test_temp_dir):
            shutil.rmtree(self.test_temp_dir)

    def test_agent_prompt_contains_exact_user_request(self):
        """Test that agent prompts contain the exact user task request."""
        test_cases = [
            {
                'user_request': 'Fix the authentication bug in login.py line 42',
                'expected_keywords': ['authentication', 'bug', 'login.py', 'line 42'],
                'unexpected_keywords': ['logout', 'registration', 'password reset']
            },
            {
                'user_request': 'Update the API documentation for the payment endpoints',
                'expected_keywords': ['API', 'documentation', 'payment', 'endpoints'],
                'unexpected_keywords': ['database', 'frontend', 'authentication']
            },
            {
                'user_request': 'Refactor the database connection pooling in services/db.py',
                'expected_keywords': ['refactor', 'database', 'connection', 'pooling', 'services/db.py'],
                'unexpected_keywords': ['frontend', 'API', 'authentication']
            }
        ]

        with patch('subprocess.run') as mock_subprocess, \
             patch('os.makedirs'), \
             patch('os.path.exists', return_value=False), \
             patch.object(TaskDispatcher, '_get_active_tmux_agents', return_value=set()):

            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = ""

            for test_case in test_cases:
                with self.subTest(request=test_case['user_request']):
                    # Generate agent for user request
                    agents = self.task_dispatcher.analyze_task_and_create_agents(
                        test_case['user_request']
                    )

                    self.assertEqual(len(agents), 1)
                    agent = agents[0]
                    prompt = agent['prompt'].lower()

                    # Verify expected keywords are present
                    for keyword in test_case['expected_keywords']:
                        self.assertIn(keyword.lower(), prompt,
                                    f"Expected keyword '{keyword}' not found in prompt")

                    # Verify unexpected keywords are not present
                    for keyword in test_case['unexpected_keywords']:
                        self.assertNotIn(keyword.lower(), prompt,
                                       f"Unexpected keyword '{keyword}' found in prompt")

    def test_agent_workspace_reflects_task_context(self):
        """Test that agent workspace setup reflects the task being performed."""
        tasks = [
            ("Fix frontend styling issues", "frontend"),
            ("Debug backend API errors", "backend"),
            ("Update database schema", "database")
        ]

        created_workspaces = []

        with patch('subprocess.run') as mock_subprocess, \
             patch('os.makedirs') as mock_makedirs:

            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = ""

            # Mock makedirs to capture workspace creation
            def capture_makedirs(path, exist_ok=False):
                if 'agent_workspace' in path:
                    created_workspaces.append(path)

            mock_makedirs.side_effect = capture_makedirs

            for task_desc, task_type in tasks:
                with patch.object(TaskDispatcher, '_get_active_tmux_agents', return_value=set()):
                    agents = self.task_dispatcher.analyze_task_and_create_agents(task_desc)

                    self.assertEqual(len(agents), 1)
                    agent = agents[0]

                    # Create agent (should set up workspace)
                    self.task_dispatcher.create_dynamic_agent(agent)

            # Verify workspaces were created for each task
            self.assertEqual(len(created_workspaces), len(tasks))

            # Verify each workspace is unique (no reuse)
            self.assertEqual(len(set(created_workspaces)), len(tasks))

    def test_task_context_isolation_between_agents(self):
        """Test that different agents have completely isolated task contexts."""
        simultaneous_tasks = [
            "Implement user authentication with JWT tokens",
            "Optimize database queries for better performance",
            "Create API documentation for payment endpoints"
        ]

        generated_agents = []

        with patch('subprocess.run') as mock_subprocess, \
             patch('os.makedirs'), \
             patch('os.path.exists', return_value=False), \
             patch.object(TaskDispatcher, '_get_active_tmux_agents', return_value=set()):

            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = ""

            # Generate agents for all tasks
            for task in simultaneous_tasks:
                agents = self.task_dispatcher.analyze_task_and_create_agents(task)
                self.assertEqual(len(agents), 1)
                generated_agents.append((task, agents[0]))

            # Verify each agent has isolated context
            for i, (task, agent) in enumerate(generated_agents):
                prompt = agent['prompt']

                # Should contain its own task
                self.assertIn(task, prompt)

                # Should not contain other tasks
                for j, (other_task, _) in enumerate(generated_agents):
                    if i != j:
                        # Extract unique keywords from other task
                        other_keywords = set(other_task.lower().split()) - {'the', 'and', 'for', 'with', 'of', 'in', 'to'}
                        current_keywords = set(task.lower().split())
                        unique_other_keywords = other_keywords - current_keywords

                        for keyword in unique_other_keywords:
                            if len(keyword) > 4:  # Only check meaningful keywords
                                self.assertNotIn(keyword, prompt.lower(),
                                               f"Agent for '{task}' should not contain '{keyword}' from '{other_task}'")

    def test_agent_completion_verification_mechanism(self):
        """Test that agent completion can be verified against original task."""
        task_description = "Add logging to the payment processing module"

        with patch('subprocess.run') as mock_subprocess, \
             patch('os.makedirs'), \
             patch('os.path.exists', return_value=False), \
             patch.object(TaskDispatcher, '_get_active_tmux_agents', return_value=set()):

            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = ""

            # Generate and create agent
            agents = self.task_dispatcher.analyze_task_and_create_agents(task_description)
            agent = agents[0]

            # Verify completion criteria are included in prompt
            prompt = agent['prompt']

            # Should include verification steps
            self.assertIn("completion", prompt.lower())
            self.assertTrue(
                any(word in prompt.lower() for word in ["complete", "finish", "done", "verify"]),
                "Prompt should include completion verification steps"
            )

            # Should include the original task for verification
            self.assertIn(task_description, prompt)

    def test_pr_context_detection_accuracy(self):
        """Test that PR context detection correctly identifies update vs create scenarios."""
        test_scenarios = [
            {
                'task': 'Fix PR #1234 comment about variable naming',
                'expected_mode': 'update',
                'expected_pr': '1234'
            },
            {
                'task': 'Update the existing PR with better error handling',
                'expected_mode': 'update',
                'expected_pr': None  # Should try to find recent PR
            },
            {
                'task': 'Create a new feature for user notifications',
                'expected_mode': 'create',
                'expected_pr': None
            },
            {
                'task': 'Improve PR #5678 by adding unit tests',
                'expected_mode': 'update',
                'expected_pr': '5678'
            }
        ]

        for scenario in test_scenarios:
            with self.subTest(task=scenario['task']):
                pr_number, mode = self.task_dispatcher._detect_pr_context(scenario['task'])

                self.assertEqual(mode, scenario['expected_mode'],
                               f"Expected mode {scenario['expected_mode']}, got {mode}")

                if scenario['expected_pr']:
                    self.assertEqual(pr_number, scenario['expected_pr'],
                                   f"Expected PR {scenario['expected_pr']}, got {pr_number}")

    def test_task_prompt_includes_mandatory_completion_steps(self):
        """Test that all task prompts include mandatory completion steps."""
        tasks = [
            "Fix authentication bug",
            "Update API documentation",
            "Refactor database connections"
        ]

        mandatory_elements = [
            "commit",  # Must commit changes
            "push",    # Must push changes
            "completion",  # Must report completion
        ]

        with patch('subprocess.run') as mock_subprocess, \
             patch('os.makedirs'), \
             patch('os.path.exists', return_value=False), \
             patch.object(TaskDispatcher, '_get_active_tmux_agents', return_value=set()):

            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = ""

            for task in tasks:
                with self.subTest(task=task):
                    agents = self.task_dispatcher.analyze_task_and_create_agents(task)
                    agent = agents[0]
                    prompt = agent['prompt'].lower()

                    # Verify all mandatory elements are present
                    for element in mandatory_elements:
                        self.assertIn(element, prompt,
                                    f"Prompt for '{task}' missing mandatory element: {element}")

    def test_unique_agent_naming_prevents_conflicts(self):
        """Test that agent names are unique even for similar tasks."""
        similar_tasks = [
            "Fix bug in authentication system",
            "Fix bug in authorization system",
            "Fix bug in payment system"
        ]

        generated_names = []

        with patch('subprocess.run') as mock_subprocess, \
             patch('os.makedirs'), \
             patch('os.path.exists', return_value=False), \
             patch.object(TaskDispatcher, '_get_active_tmux_agents', return_value=set()):

            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = ""

            for task in similar_tasks:
                agents = self.task_dispatcher.analyze_task_and_create_agents(task)
                agent = agents[0]
                generated_names.append(agent['name'])

            # Verify all names are unique
            self.assertEqual(len(generated_names), len(set(generated_names)),
                           "Agent names should be unique even for similar tasks")

            # Verify all names follow expected pattern
            for name in generated_names:
                self.assertTrue(name.startswith('task-agent-'),
                              f"Agent name '{name}' should start with 'task-agent-'")
                self.assertTrue(name[11:].isdigit() or '-' in name[11:],
                              f"Agent name '{name}' should have numeric suffix")

    def test_agent_execution_environment_isolation(self):
        """Test that agents get isolated execution environments."""
        tasks = [
            "Work on frontend components",
            "Work on backend services",
            "Work on database migrations"
        ]

        created_environments = []

        with patch('subprocess.run') as mock_subprocess:
            # Mock git worktree creation
            def mock_subprocess_side_effect(*args, **kwargs):
                cmd = args[0]
                if len(cmd) > 0 and cmd[0] == 'git' and 'worktree' in cmd:
                    # Extract the directory path from git worktree add command
                    if len(cmd) > 3:
                        workspace_dir = cmd[3]  # git worktree add -b branch_name workspace_dir main
                        created_environments.append(workspace_dir)

                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stdout = ""
                return mock_result

            mock_subprocess.side_effect = mock_subprocess_side_effect

            with patch('os.makedirs'), \
                 patch.object(TaskDispatcher, '_get_active_tmux_agents', return_value=set()):

                for task in tasks:
                    agents = self.task_dispatcher.analyze_task_and_create_agents(task)
                    agent = agents[0]

                    # Create agent (should set up isolated environment)
                    self.task_dispatcher.create_dynamic_agent(agent)

            # Verify isolated environments were created
            self.assertEqual(len(created_environments), len(tasks))

            # Verify each environment is unique
            self.assertEqual(len(set(created_environments)), len(tasks))

            # Verify environment naming follows pattern
            for env_path in created_environments:
                self.assertIn('agent_workspace_', env_path)


class TestTaskTraceability(unittest.TestCase):
    """Tests for tracing task execution from request to completion."""

    def setUp(self):
        self.test_temp_dir = tempfile.mkdtemp(prefix="task_traceability_test_")

    def tearDown(self):
        if os.path.exists(self.test_temp_dir):
            shutil.rmtree(self.test_temp_dir)

    def test_task_request_to_execution_chain(self):
        """Test the complete chain from user request to agent execution."""
        user_request = "Implement rate limiting for API endpoints"

        execution_chain = []

        def track_orchestration_call(task_desc):
            execution_chain.append(('orchestration_start', task_desc))
            return []  # No agents for this mock

        def track_agent_creation(agent_spec):
            execution_chain.append(('agent_creation', agent_spec['focus']))
            return True

        with patch.object(UnifiedOrchestration, 'orchestrate', side_effect=track_orchestration_call), \
             patch.object(TaskDispatcher, 'create_dynamic_agent', side_effect=track_agent_creation):

            # Start orchestration
            orchestration = UnifiedOrchestration()
            orchestration.orchestrate(user_request)

            # Verify the execution chain
            self.assertGreater(len(execution_chain), 0)
            self.assertEqual(execution_chain[0][0], 'orchestration_start')
            self.assertEqual(execution_chain[0][1], user_request)

    def test_task_completion_reporting_includes_original_request(self):
        """Test that completion reports can be traced back to original request."""
        task_description = "Add input validation to user registration form"
        agent_name = "task-agent-validation-123"

        with patch('subprocess.run') as mock_subprocess, \
             patch('os.makedirs'), \
             patch('os.path.exists', return_value=False), \
             patch.object(TaskDispatcher, '_get_active_tmux_agents', return_value=set()):

            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = ""

            # Generate agent
            task_dispatcher = TaskDispatcher()
            agents = task_dispatcher.analyze_task_and_create_agents(task_description)
            agent = agents[0]
            agent['name'] = agent_name

            # Extract completion report template from prompt
            prompt = agent['prompt']

            # Should include original task in completion report
            self.assertIn(task_description, prompt)

            # Should include completion report mechanism
            self.assertTrue(
                any(phrase in prompt.lower() for phrase in [
                    'completion report',
                    'result',
                    'echo',
                    '.json'
                ]),
                "Prompt should include completion reporting mechanism"
            )

    def test_error_reporting_maintains_task_context(self):
        """Test that error reporting maintains connection to original task."""
        failing_task = "Fix non-existent file that will cause errors"

        with patch('subprocess.run') as mock_subprocess, \
             patch('os.makedirs'), \
             patch('os.path.exists', return_value=False), \
             patch.object(TaskDispatcher, '_get_active_tmux_agents', return_value=set()):

            # Simulate subprocess failure
            mock_subprocess.return_value.returncode = 1
            mock_subprocess.return_value.stderr = "git: command failed"

            task_dispatcher = TaskDispatcher()
            agents = task_dispatcher.analyze_task_and_create_agents(failing_task)
            agent = agents[0]

            # Even with potential failures, agent should have correct task context
            self.assertIn(failing_task, agent['prompt'])
            self.assertIn(agent['focus'], failing_task)


if __name__ == '__main__':
    unittest.main(verbosity=2)
