#!/usr/bin/env python3
"""
Tmux Session Lifecycle Tests

Tests for tmux session management in the orchestration system, ensuring:
1. Sessions are created properly for each agent
2. Sessions are cleaned up when agents complete
3. No resource leaks from accumulated dead sessions
4. Session state detection works correctly

This prevents resource accumulation that could impact system performance.
"""

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


class TestTmuxSessionLifecycle(unittest.TestCase):
    """Tests for complete tmux session lifecycle management."""

    def setUp(self):
        self.test_temp_dir = tempfile.mkdtemp(prefix="tmux_lifecycle_test_")
        self.orchestration = UnifiedOrchestration()
        self.task_dispatcher = TaskDispatcher()

    def tearDown(self):
        if os.path.exists(self.test_temp_dir):
            shutil.rmtree(self.test_temp_dir)

    def test_tmux_session_creation_for_agents(self):
        """Test that tmux sessions are created properly for each agent."""
        task_description = "Fix authentication bug in login system"

        tmux_commands_executed = []

        def mock_subprocess_side_effect(*args, **kwargs):
            cmd = args[0]
            if len(cmd) > 0 and cmd[0] == 'tmux':
                tmux_commands_executed.append(cmd)

            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            return mock_result

        with patch('subprocess.run', side_effect=mock_subprocess_side_effect), \
             patch('os.makedirs'), \
             patch('os.path.exists', return_value=False), \
             patch.object(TaskDispatcher, '_get_active_tmux_agents', return_value=set()):

            # Generate and create agent
            agents = self.task_dispatcher.analyze_task_and_create_agents(task_description)
            agent = agents[0]

            # Create agent (should create tmux session)
            success = self.task_dispatcher.create_dynamic_agent(agent)
            self.assertTrue(success)

            # Verify tmux new-session command was executed
            new_session_commands = [cmd for cmd in tmux_commands_executed
                                  if len(cmd) > 1 and cmd[1] == 'new-session']

            self.assertEqual(len(new_session_commands), 1)

            # Verify session command includes required parameters
            session_cmd = new_session_commands[0]
            self.assertIn('-d', session_cmd)  # Detached
            self.assertIn('-s', session_cmd)  # Session name

            # Find session name
            session_name_index = session_cmd.index('-s') + 1
            session_name = session_cmd[session_name_index]
            self.assertTrue(session_name.startswith('task-agent-'))

    def test_tmux_session_cleanup_on_startup(self):
        """Test that completed tmux sessions are cleaned up on orchestration startup."""
        # Mock tmux session data
        completed_sessions = [
            'task-agent-completed1',
            'task-agent-completed2'
        ]
        active_sessions = [
            'task-agent-active1',
            'task-agent-active2'
        ]
        other_sessions = [
            'user-session',
            'development-session'
        ]

        all_sessions = completed_sessions + active_sessions + other_sessions

        killed_sessions = []

        def mock_subprocess_side_effect(*args, **kwargs):
            cmd = args[0]

            if cmd[0] == 'tmux' and cmd[1] == 'list-sessions':
                # Return all sessions
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stdout = '\n'.join(all_sessions)
                return mock_result

            elif cmd[0] == 'tmux' and cmd[1] == 'capture-pane':
                # Return different output based on session type
                session_name = cmd[3]  # -t session_name
                mock_result = MagicMock()
                mock_result.returncode = 0

                if session_name in completed_sessions:
                    mock_result.stdout = "Agent completed successfully\nSession will auto-close in 1 hour"
                else:
                    mock_result.stdout = "Working on task..."

                return mock_result

            elif cmd[0] == 'tmux' and cmd[1] == 'kill-session':
                # Track which sessions were killed
                session_name = cmd[3]  # -t session_name
                killed_sessions.append(session_name)
                mock_result = MagicMock()
                mock_result.returncode = 0
                return mock_result

            # Default mock result
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            return mock_result

        with patch('subprocess.run', side_effect=mock_subprocess_side_effect):
            # Create orchestration instance (should trigger cleanup)
            orchestration = UnifiedOrchestration()

            # Verify only completed task-agent sessions were killed
            self.assertEqual(set(killed_sessions), set(completed_sessions))

            # Verify active and non-agent sessions were not killed
            for session in active_sessions + other_sessions:
                self.assertNotIn(session, killed_sessions)

    def test_session_completion_detection_accuracy(self):
        """Test that session completion detection accurately identifies completed sessions."""
        test_cases = [
            {
                'session_output': 'Agent completed successfully\nMonitor with: tmux attach',
                'expected_completed': True
            },
            {
                'session_output': 'Agent execution completed. Session remains active for monitoring',
                'expected_completed': True
            },
            {
                'session_output': 'Session will auto-close in 1 hour',
                'expected_completed': True
            },
            {
                'session_output': 'Working on task... Please wait',
                'expected_completed': False
            },
            {
                'session_output': 'ERROR: Task failed, investigating',
                'expected_completed': False
            },
            {
                'session_output': 'Analyzing code structure...',
                'expected_completed': False
            }
        ]

        for test_case in test_cases:
            with self.subTest(output=test_case['session_output'][:30]):
                with patch('subprocess.run') as mock_subprocess:
                    mock_subprocess.return_value.returncode = 0
                    mock_subprocess.return_value.stdout = test_case['session_output']

                    result = self.orchestration._is_session_completed('test-session')

                    self.assertEqual(result, test_case['expected_completed'],
                                   f"Expected {test_case['expected_completed']} for output: {test_case['session_output']}")

    def test_session_cleanup_handles_dead_sessions(self):
        """Test that cleanup handles sessions that are already dead."""
        dead_sessions = ['task-agent-dead1', 'task-agent-dead2']
        live_sessions = ['task-agent-live1']

        def mock_subprocess_side_effect(*args, **kwargs):
            cmd = args[0]

            if cmd[0] == 'tmux' and cmd[1] == 'list-sessions':
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stdout = '\n'.join(dead_sessions + live_sessions)
                return mock_result

            elif cmd[0] == 'tmux' and cmd[1] == 'capture-pane':
                session_name = cmd[3]
                mock_result = MagicMock()

                if session_name in dead_sessions:
                    # Dead session - command fails
                    mock_result.returncode = 1
                    mock_result.stderr = "session not found"
                else:
                    # Live session
                    mock_result.returncode = 0
                    mock_result.stdout = "Working on task..."

                return mock_result

            # Default success
            mock_result = MagicMock()
            mock_result.returncode = 0
            return mock_result

        with patch('subprocess.run', side_effect=mock_subprocess_side_effect):
            # Should not raise exception when encountering dead sessions
            try:
                orchestration = UnifiedOrchestration()
                success = True
            except Exception:
                success = False

            self.assertTrue(success, "Cleanup should handle dead sessions gracefully")

    def test_active_agent_counting_excludes_idle_sessions(self):
        """Test that active agent counting correctly excludes idle/completed sessions."""
        all_sessions = [
            'task-agent-working1',
            'task-agent-working2',
            'task-agent-idle1',
            'task-agent-idle2',
            'non-agent-session'
        ]

        working_sessions = ['task-agent-working1', 'task-agent-working2']
        idle_sessions = ['task-agent-idle1', 'task-agent-idle2']

        def mock_subprocess_side_effect(*args, **kwargs):
            cmd = args[0]

            if cmd[0] == 'tmux' and cmd[1] == 'list-sessions':
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stdout = '\n'.join(all_sessions)
                return mock_result

            elif cmd[0] == 'tmux' and cmd[1] == 'capture-pane':
                session_name = cmd[3]
                mock_result = MagicMock()
                mock_result.returncode = 0

                if session_name in working_sessions:
                    mock_result.stdout = "Executing task step 3 of 5..."
                elif session_name in idle_sessions:
                    mock_result.stdout = "Agent completed successfully"
                else:
                    mock_result.stdout = "Regular tmux session"

                return mock_result

            mock_result = MagicMock()
            mock_result.returncode = 0
            return mock_result

        with patch('subprocess.run', side_effect=mock_subprocess_side_effect), \
             patch('shutil.which', return_value='/usr/bin/tmux'):

            active_agents = self.task_dispatcher._get_active_tmux_agents()

            # Should only count working sessions, not idle ones
            self.assertEqual(len(active_agents), len(working_sessions))
            self.assertEqual(active_agents, set(working_sessions))

    def test_session_resource_leak_prevention(self):
        """Test that sessions don't accumulate indefinitely causing resource leaks."""
        # Simulate scenario with many old completed sessions
        old_completed_sessions = [f'task-agent-old{i}' for i in range(20)]
        recent_active_sessions = [f'task-agent-recent{i}' for i in range(3)]

        all_sessions = old_completed_sessions + recent_active_sessions
        killed_sessions = []

        def mock_subprocess_side_effect(*args, **kwargs):
            cmd = args[0]

            if cmd[0] == 'tmux' and cmd[1] == 'list-sessions':
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stdout = '\n'.join(all_sessions)
                return mock_result

            elif cmd[0] == 'tmux' and cmd[1] == 'capture-pane':
                session_name = cmd[3]
                mock_result = MagicMock()
                mock_result.returncode = 0

                if session_name in old_completed_sessions:
                    mock_result.stdout = "Agent completed successfully"
                else:
                    mock_result.stdout = "Working on current task..."

                return mock_result

            elif cmd[0] == 'tmux' and cmd[1] == 'kill-session':
                session_name = cmd[3]
                killed_sessions.append(session_name)
                mock_result = MagicMock()
                mock_result.returncode = 0
                return mock_result

            mock_result = MagicMock()
            mock_result.returncode = 0
            return mock_result

        with patch('subprocess.run', side_effect=mock_subprocess_side_effect):
            # Trigger cleanup
            orchestration = UnifiedOrchestration()

            # Verify old completed sessions were cleaned up
            self.assertEqual(len(killed_sessions), len(old_completed_sessions))
            self.assertEqual(set(killed_sessions), set(old_completed_sessions))

    def test_concurrent_session_access_safety(self):
        """Test that session operations are safe when multiple processes access tmux."""
        sessions_to_check = ['task-agent-concurrent1', 'task-agent-concurrent2']

        # Simulate race conditions where sessions might be killed by other processes
        def mock_subprocess_side_effect(*args, **kwargs):
            cmd = args[0]

            if cmd[0] == 'tmux' and cmd[1] == 'list-sessions':
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_result.stdout = '\n'.join(sessions_to_check)
                return mock_result

            elif cmd[0] == 'tmux' and cmd[1] == 'capture-pane':
                session_name = cmd[3]
                mock_result = MagicMock()

                if session_name == 'task-agent-concurrent1':
                    # Session exists and is completed
                    mock_result.returncode = 0
                    mock_result.stdout = "Agent completed successfully"
                else:
                    # Session was killed by another process
                    mock_result.returncode = 1
                    mock_result.stderr = "session not found"

                return mock_result

            elif cmd[0] == 'tmux' and cmd[1] == 'kill-session':
                mock_result = MagicMock()
                mock_result.returncode = 0
                return mock_result

            mock_result = MagicMock()
            mock_result.returncode = 0
            return mock_result

        with patch('subprocess.run', side_effect=mock_subprocess_side_effect):
            # Should handle race conditions gracefully
            try:
                orchestration = UnifiedOrchestration()
                success = True
            except Exception:
                success = False

            self.assertTrue(success, "Should handle concurrent session access safely")

    def test_session_naming_uniqueness(self):
        """Test that session names are unique even under high load."""
        tasks = [f"Task {i}" for i in range(10)]
        created_sessions = []

        def mock_subprocess_side_effect(*args, **kwargs):
            cmd = args[0]

            if cmd[0] == 'tmux' and cmd[1] == 'new-session':
                # Extract session name
                session_name_index = cmd.index('-s') + 1
                session_name = cmd[session_name_index]
                created_sessions.append(session_name)

                mock_result = MagicMock()
                mock_result.returncode = 0
                return mock_result

            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = ""
            return mock_result

        with patch('subprocess.run', side_effect=mock_subprocess_side_effect), \
             patch('os.makedirs'), \
             patch('os.path.exists', return_value=False), \
             patch.object(TaskDispatcher, '_get_active_tmux_agents', return_value=set()):

            # Create multiple agents rapidly
            for task in tasks:
                agents = self.task_dispatcher.analyze_task_and_create_agents(task)
                agent = agents[0]
                self.task_dispatcher.create_dynamic_agent(agent)

            # Verify all session names are unique
            self.assertEqual(len(created_sessions), len(set(created_sessions)),
                           "All session names should be unique")

            # Verify all names follow the expected pattern
            for session_name in created_sessions:
                self.assertTrue(session_name.startswith('task-agent-'),
                              f"Session name '{session_name}' should start with 'task-agent-'")

    def test_session_config_file_usage(self):
        """Test that tmux sessions use the correct configuration file."""
        with patch('subprocess.run') as mock_subprocess, \
             patch('os.path.exists') as mock_exists, \
             patch('os.makedirs'), \
             patch.object(TaskDispatcher, '_get_active_tmux_agents', return_value=set()):

            # Mock config file exists
            def mock_exists_side_effect(path):
                return 'tmux-agent.conf' in path

            mock_exists.side_effect = mock_exists_side_effect
            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = ""

            # Create agent
            agents = self.task_dispatcher.analyze_task_and_create_agents("Test task")
            agent = agents[0]
            self.task_dispatcher.create_dynamic_agent(agent)

            # Verify tmux was called with config file
            tmux_calls = [call for call in mock_subprocess.call_args_list
                         if len(call[0]) > 0 and len(call[0][0]) > 0 and call[0][0][0] == 'tmux']

            self.assertGreater(len(tmux_calls), 0)

            # Check if any tmux call included the -f flag for config file
            config_used = any('-f' in call[0][0] for call in tmux_calls)
            self.assertTrue(config_used, "Tmux should be called with config file when available")


if __name__ == '__main__':
    unittest.main(verbosity=2)
