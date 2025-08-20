#!/usr/bin/env python3
"""
Integration Tests for Stale Task Queue Bug Prevention

These tests specifically target the bug where orchestration agents executed
stale tasks from previous runs instead of newly requested tasks.

Critical Bug Context:
- Found 289 stale prompt files in /tmp/agent_prompt_*.txt
- Agents reused old prompt files containing different tasks
- User requested "server modification", agents executed "PR comment responses"
- Root cause: Missing cleanup lifecycle for task prompt files

Test Goals:
1. Verify prompt files are cleaned up between orchestration runs
2. Ensure fresh task prompts are generated for each new request
3. Test multi-run scenarios to catch stale state reuse
4. Verify task execution matches user intent, not cached prompts
"""

import glob
import json
import os
import shutil
import tempfile
import time
import unittest
from unittest.mock import patch, MagicMock, call

# Import the modules we're testing
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from orchestrate_unified import UnifiedOrchestration
from task_dispatcher import TaskDispatcher


class TestStaleTaskPrevention(unittest.TestCase):
    """Integration tests to prevent the stale task queue bug from recurring."""

    def setUp(self):
        """Set up test environment with temp directories."""
        self.test_temp_dir = tempfile.mkdtemp(prefix="orchestration_test_")
        self.original_tmp_pattern = "/tmp/agent_prompt_*.txt"
        self.test_tmp_pattern = f"{self.test_temp_dir}/agent_prompt_*.txt"

        # Patch the file paths to use our test directory
        self.mock_glob_patcher = patch('glob.glob')
        self.mock_glob = self.mock_glob_patcher.start()

        # Create test orchestration instance
        self.orchestration = UnifiedOrchestration()
        self.task_dispatcher = TaskDispatcher()

    def tearDown(self):
        """Clean up test environment."""
        self.mock_glob_patcher.stop()
        if os.path.exists(self.test_temp_dir):
            shutil.rmtree(self.test_temp_dir)

    def _create_stale_prompt_files(self, count: int, task_content: str = "OLD_TASK") -> list:
        """Helper: Create fake stale prompt files for testing."""
        stale_files = []
        for i in range(count):
            filename = f"{self.test_temp_dir}/agent_prompt_task-agent-{i}.txt"
            with open(filename, 'w') as f:
                f.write(f"Task: {task_content} {i}\n")
                f.write("This is an old task from a previous run\n")
            # Make file older than 5 minutes (300 seconds)
            old_time = time.time() - 400
            os.utime(filename, (old_time, old_time))
            stale_files.append(filename)
        return stale_files

    def _create_recent_prompt_files(self, count: int, task_content: str = "ACTIVE_TASK") -> list:
        """Helper: Create recent prompt files that should NOT be cleaned up."""
        recent_files = []
        for i in range(count):
            filename = f"{self.test_temp_dir}/agent_prompt_active-agent-{i}.txt"
            with open(filename, 'w') as f:
                f.write(f"Task: {task_content} {i}\n")
                f.write("This is an active task from current run\n")
            recent_files.append(filename)
        return recent_files

    def test_stale_prompt_file_cleanup_on_startup(self):
        """Test that stale prompt files are cleaned up when orchestration starts."""
        # Create mix of stale and recent files
        stale_files = self._create_stale_prompt_files(5, "STALE_SERVER_MOD")
        recent_files = self._create_recent_prompt_files(2, "CURRENT_TASK")

        # Mock glob to return our test files
        all_files = stale_files + recent_files
        self.mock_glob.return_value = all_files

        # Mock os.path.getmtime to return appropriate ages
        original_getmtime = os.path.getmtime
        def mock_getmtime(path):
            if any(stale in path for stale in stale_files):
                return time.time() - 400  # Old files
            else:
                return time.time() - 60   # Recent files

        with patch('os.path.getmtime', side_effect=mock_getmtime), \
             patch('os.remove') as mock_remove:

            # Create new orchestration instance (triggers cleanup)
            orchestration = UnifiedOrchestration()

            # Verify only stale files were marked for removal
            expected_removes = [call(f) for f in stale_files]
            mock_remove.assert_has_calls(expected_removes, any_order=True)

            # Verify recent files were not removed
            for recent_file in recent_files:
                self.assertNotIn(call(recent_file), mock_remove.call_args_list)

    def test_multi_run_task_isolation(self):
        """Test that multiple orchestration runs don't reuse stale tasks."""
        with patch('subprocess.run') as mock_subprocess, \
             patch('os.makedirs'), \
             patch('os.path.exists', return_value=False), \
             patch.object(TaskDispatcher, '_get_active_tmux_agents', return_value=set()):

            # Mock subprocess responses for git operations
            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = ""

            # First run - task about server modification
            first_task = "Modify run_local_server.sh to avoid killing existing servers"
            agents_first = self.task_dispatcher.analyze_task_and_create_agents(first_task)

            self.assertEqual(len(agents_first), 1)
            first_agent = agents_first[0]
            self.assertIn("server", first_agent['prompt'].lower())
            self.assertIn("run_local_server.sh", first_agent['prompt'])

            # Simulate some time passing and files being created
            time.sleep(0.1)

            # Second run - completely different task about PR comments
            second_task = "Respond to PR #1118 comments about code formatting"
            agents_second = self.task_dispatcher.analyze_task_and_create_agents(second_task)

            self.assertEqual(len(agents_second), 1)
            second_agent = agents_second[0]
            self.assertIn("pr", second_agent['prompt'].lower())
            self.assertIn("1118", second_agent['prompt'])
            self.assertIn("comment", second_agent['prompt'].lower())

            # CRITICAL: Verify tasks are different and not reused
            self.assertNotEqual(first_agent['prompt'], second_agent['prompt'])
            self.assertNotIn("run_local_server.sh", second_agent['prompt'])
            self.assertNotIn("PR #1118", first_agent['prompt'])

    def test_agent_prompt_file_cleanup_before_creation(self):
        """Test that agent-specific prompt files are cleaned up before agent creation."""
        agent_name = "task-agent-test123"

        # Create existing prompt file for this agent
        existing_prompt_file = f"{self.test_temp_dir}/agent_prompt_{agent_name}.txt"
        with open(existing_prompt_file, 'w') as f:
            f.write("Task: Old cached task\nThis should be cleaned up")

        with patch('os.path.exists', return_value=True), \
             patch('os.remove') as mock_remove, \
             patch('subprocess.run') as mock_subprocess:

            mock_subprocess.return_value.returncode = 0

            # Create agent specification
            agent_spec = {
                'name': agent_name,
                'focus': 'New fresh task',
                'prompt': 'Task: New fresh task\nThis is the current task',
                'capabilities': ['development'],
                'type': 'development'
            }

            # Create agent (should trigger cleanup)
            self.task_dispatcher.create_dynamic_agent(agent_spec)

            # Verify the old prompt file was removed
            mock_remove.assert_called_with(existing_prompt_file)

    def test_task_prompt_freshness_verification(self):
        """Test that task prompts always reflect current user request, never cached."""
        task_variations = [
            "Fix failing unit tests in authentication module",
            "Update documentation for the API endpoints",
            "Refactor database connection pooling logic",
            "Add logging to the payment processing system"
        ]

        generated_prompts = []

        with patch('subprocess.run') as mock_subprocess, \
             patch('os.makedirs'), \
             patch('os.path.exists', return_value=False), \
             patch.object(TaskDispatcher, '_get_active_tmux_agents', return_value=set()):

            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = ""

            for task in task_variations:
                agents = self.task_dispatcher.analyze_task_and_create_agents(task)
                self.assertEqual(len(agents), 1)

                agent_prompt = agents[0]['prompt']
                generated_prompts.append(agent_prompt)

                # Verify prompt contains current task, not cached ones
                self.assertIn(task, agent_prompt)

                # Verify prompt doesn't contain other tasks
                for other_task in task_variations:
                    if other_task != task:
                        self.assertNotIn(other_task, agent_prompt)

        # Verify all prompts are unique (no reuse)
        self.assertEqual(len(set(generated_prompts)), len(task_variations))

    def test_prompt_file_age_based_cleanup(self):
        """Test that cleanup respects file age (5 minute threshold)."""
        # Create files with different ages
        very_old_file = f"{self.test_temp_dir}/agent_prompt_very_old.txt"
        old_file = f"{self.test_temp_dir}/agent_prompt_old.txt"
        recent_file = f"{self.test_temp_dir}/agent_prompt_recent.txt"

        with open(very_old_file, 'w') as f:
            f.write("Very old task")
        with open(old_file, 'w') as f:
            f.write("Old task")
        with open(recent_file, 'w') as f:
            f.write("Recent task")

        # Mock file ages
        def mock_getmtime(path):
            if "very_old" in path:
                return time.time() - 3600  # 1 hour old
            elif "old" in path:
                return time.time() - 400   # 6+ minutes old (should be cleaned)
            else:
                return time.time() - 120   # 2 minutes old (should be kept)

        self.mock_glob.return_value = [very_old_file, old_file, recent_file]

        with patch('os.path.getmtime', side_effect=mock_getmtime), \
             patch('os.remove') as mock_remove:

            # Trigger cleanup
            orchestration = UnifiedOrchestration()

            # Verify only old files (>5 minutes) were removed
            expected_removes = [call(very_old_file), call(old_file)]
            mock_remove.assert_has_calls(expected_removes, any_order=True)

            # Verify recent file was not removed
            self.assertNotIn(call(recent_file), mock_remove.call_args_list)

    def test_tmux_session_cleanup_integration(self):
        """Test that completed tmux sessions are cleaned up to prevent resource leaks."""
        completed_sessions = ['task-agent-completed1', 'task-agent-completed2']
        active_sessions = ['task-agent-active1']

        with patch('subprocess.run') as mock_subprocess:
            # Mock tmux list-sessions command
            list_sessions_output = '\n'.join(completed_sessions + active_sessions)

            # Mock tmux capture-pane for completion detection
            def mock_subprocess_side_effect(*args, **kwargs):
                cmd = args[0]
                if cmd[0] == 'tmux' and cmd[1] == 'list-sessions':
                    mock_result = MagicMock()
                    mock_result.returncode = 0
                    mock_result.stdout = list_sessions_output
                    return mock_result
                elif cmd[0] == 'tmux' and cmd[1] == 'capture-pane':
                    session_name = cmd[3]  # -t session_name
                    mock_result = MagicMock()
                    mock_result.returncode = 0
                    if 'completed' in session_name:
                        mock_result.stdout = "Agent completed successfully\nSession will auto-close in 1 hour"
                    else:
                        mock_result.stdout = "Agent is working on task..."
                    return mock_result
                elif cmd[0] == 'tmux' and cmd[1] == 'kill-session':
                    mock_result = MagicMock()
                    mock_result.returncode = 0
                    return mock_result
                else:
                    mock_result = MagicMock()
                    mock_result.returncode = 0
                    mock_result.stdout = ""
                    return mock_result

            mock_subprocess.side_effect = mock_subprocess_side_effect

            # Trigger cleanup
            orchestration = UnifiedOrchestration()

            # Verify completed sessions were killed
            kill_calls = [call for call in mock_subprocess.call_args_list
                         if len(call[0]) > 0 and len(call[0][0]) > 1 and
                         call[0][0][0] == 'tmux' and call[0][0][1] == 'kill-session']

            self.assertEqual(len(kill_calls), 2)  # Two completed sessions

    def test_large_scale_stale_file_scenario(self):
        """Test cleanup handles large numbers of stale files (like the 289 found in production)."""
        # Simulate the production scenario with 289 stale files
        stale_files = self._create_stale_prompt_files(289, "STALE_PRODUCTION_TASK")

        self.mock_glob.return_value = stale_files

        with patch('os.path.getmtime', return_value=time.time() - 400), \
             patch('os.remove') as mock_remove:

            # Create orchestration instance (triggers cleanup)
            orchestration = UnifiedOrchestration()

            # Verify all 289 stale files were marked for removal
            self.assertEqual(mock_remove.call_count, 289)

            # Verify each stale file was removed exactly once
            removed_files = [call[0][0] for call in mock_remove.call_args_list]
            self.assertEqual(set(removed_files), set(stale_files))

    def test_concurrent_orchestration_safety(self):
        """Test that multiple concurrent orchestration instances don't interfere."""
        # This test verifies that the cleanup is safe even if multiple
        # instances are starting up simultaneously

        stale_files = self._create_stale_prompt_files(10, "CONCURRENT_TEST")
        self.mock_glob.return_value = stale_files

        removal_counts = []

        def track_removals(*args):
            removal_counts.append(len(args))

        with patch('os.path.getmtime', return_value=time.time() - 400), \
             patch('os.remove', side_effect=track_removals):

            # Create multiple orchestration instances concurrently
            instances = [UnifiedOrchestration() for _ in range(3)]

            # Verify cleanup happened (at least one instance cleaned up)
            # Due to file system race conditions, we just verify cleanup occurred
            self.assertGreater(sum(removal_counts), 0)


class TestTaskDispatcherCleanup(unittest.TestCase):
    """Specific tests for TaskDispatcher cleanup functionality."""

    def setUp(self):
        self.test_temp_dir = tempfile.mkdtemp(prefix="task_dispatcher_test_")
        self.task_dispatcher = TaskDispatcher()

    def tearDown(self):
        if os.path.exists(self.test_temp_dir):
            shutil.rmtree(self.test_temp_dir)

    def test_cleanup_stale_prompt_files_exact_match(self):
        """Test that cleanup only removes exact agent name matches, not similar names."""
        agent_name = "task-agent-123"

        # Create files with similar but different names
        exact_file = f"{self.test_temp_dir}/agent_prompt_{agent_name}.txt"
        similar_file = f"{self.test_temp_dir}/agent_prompt_{agent_name}456.txt"  # Similar but different
        different_file = f"{self.test_temp_dir}/agent_prompt_other-agent-789.txt"

        for file_path in [exact_file, similar_file, different_file]:
            with open(file_path, 'w') as f:
                f.write("test content")

        with patch('os.path.exists', return_value=True), \
             patch('os.remove') as mock_remove:

            # Trigger cleanup for specific agent
            self.task_dispatcher._cleanup_stale_prompt_files(agent_name)

            # Verify only exact match was removed
            mock_remove.assert_called_once_with(exact_file)

    def test_cleanup_handles_missing_files_gracefully(self):
        """Test that cleanup handles cases where files don't exist or are already removed."""
        agent_name = "task-agent-missing"

        with patch('os.path.exists', return_value=False), \
             patch('os.remove') as mock_remove:

            # Should not raise exception when file doesn't exist
            self.task_dispatcher._cleanup_stale_prompt_files(agent_name)

            # Should not attempt to remove non-existent file
            mock_remove.assert_not_called()


if __name__ == '__main__':
    # Create a test suite focusing on stale task prevention
    suite = unittest.TestSuite()

    # Add all tests from both classes
    suite.addTest(unittest.makeSuite(TestStaleTaskPrevention))
    suite.addTest(unittest.makeSuite(TestTaskDispatcherCleanup))

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)
