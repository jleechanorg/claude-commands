#!/usr/bin/env python3
"""
Prompt File Lifecycle Tests

Tests the complete lifecycle of task prompt files to ensure:
1. Files are created with correct content for each task
2. Files are cleaned up appropriately based on age and context
3. No cross-contamination between different orchestration runs
4. Memory usage doesn't grow unbounded from accumulated files

This addresses the specific lifecycle management gap that caused the stale task bug.
"""

import glob
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


class TestPromptFileLifecycle(unittest.TestCase):
    """Tests for complete prompt file lifecycle management."""

    def setUp(self):
        """Set up test environment."""
        self.test_temp_dir = tempfile.mkdtemp(prefix="prompt_lifecycle_test_")
        self.orchestration = UnifiedOrchestration()
        self.task_dispatcher = TaskDispatcher()

    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.test_temp_dir):
            shutil.rmtree(self.test_temp_dir)

    def test_prompt_file_creation_contains_correct_task(self):
        """Test that prompt files are created with the correct task content."""
        agent_name = "task-agent-test123"
        task_description = "Fix authentication bug in login system"

        with patch('tempfile.mkdtemp', return_value=self.test_temp_dir), \
             patch('subprocess.run') as mock_subprocess, \
             patch('os.makedirs'), \
             patch.object(TaskDispatcher, '_get_active_tmux_agents', return_value=set()):

            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = ""

            # Create agent spec
            agent_spec = {
                'name': agent_name,
                'focus': task_description,
                'prompt': f'Task: {task_description}\nExecute this task',
                'capabilities': ['development'],
                'type': 'development'
            }

            # Mock file writing to capture content
            written_content = {}
            original_open = open

            def mock_open(filename, mode='r', *args, **kwargs):
                if mode == 'w' and 'agent_prompt' in filename:
                    # Create a mock file object that captures content
                    class MockFile:
                        def __init__(self, path):
                            self.path = path
                            self.content = ""

                        def write(self, data):
                            self.content += data

                        def __enter__(self):
                            return self

                        def __exit__(self, *args):
                            written_content[self.path] = self.content

                    return MockFile(filename)
                else:
                    return original_open(filename, mode, *args, **kwargs)

            with patch('builtins.open', side_effect=mock_open):
                # Create the agent (should write prompt file)
                self.task_dispatcher.create_dynamic_agent(agent_spec)

                # Verify prompt file was created with correct content
                prompt_files = [k for k in written_content.keys() if 'agent_prompt' in k]
                self.assertEqual(len(prompt_files), 1)

                prompt_content = written_content[prompt_files[0]]
                self.assertIn(task_description, prompt_content)
                self.assertIn("authentication bug", prompt_content)

    def test_prompt_file_cleanup_age_threshold(self):
        """Test that cleanup respects the 5-minute age threshold exactly."""
        current_time = time.time()

        # Create files at different ages around the 5-minute (300 second) threshold
        test_files = [
            (f"{self.test_temp_dir}/agent_prompt_just_under.txt", current_time - 299),  # 4:59 - keep
            (f"{self.test_temp_dir}/agent_prompt_exactly_5min.txt", current_time - 300),  # 5:00 - remove
            (f"{self.test_temp_dir}/agent_prompt_just_over.txt", current_time - 301),  # 5:01 - remove
            (f"{self.test_temp_dir}/agent_prompt_way_old.txt", current_time - 3600),  # 1 hour - remove
        ]

        for file_path, mtime in test_files:
            with open(file_path, 'w') as f:
                f.write("test content")

        files_to_keep = [test_files[0][0]]  # Only just_under should be kept
        files_to_remove = [f[0] for f in test_files[1:]]  # All others should be removed

        def mock_getmtime(path):
            for file_path, mtime in test_files:
                if file_path == path:
                    return mtime
            return current_time

        with patch('glob.glob', return_value=[f[0] for f in test_files]), \
             patch('os.path.getmtime', side_effect=mock_getmtime), \
             patch('os.remove') as mock_remove:

            # Trigger cleanup
            orchestration = UnifiedOrchestration()

            # Verify only files >= 5 minutes old were removed
            expected_removes = [call(f) for f in files_to_remove]
            mock_remove.assert_has_calls(expected_removes, any_order=True)

            # Verify file under 5 minutes was not removed
            for kept_file in files_to_keep:
                self.assertNotIn(call(kept_file), mock_remove.call_args_list)

    def test_prompt_file_cleanup_handles_concurrent_access(self):
        """Test that cleanup handles files being removed by other processes."""
        test_files = [
            f"{self.test_temp_dir}/agent_prompt_concurrent1.txt",
            f"{self.test_temp_dir}/agent_prompt_concurrent2.txt",
            f"{self.test_temp_dir}/agent_prompt_concurrent3.txt",
        ]

        for file_path in test_files:
            with open(file_path, 'w') as f:
                f.write("test content")

        def mock_remove(path):
            if "concurrent2" in path:
                # Simulate file being removed by another process
                raise OSError("File not found (removed by another process)")
            # Other files remove successfully

        with patch('glob.glob', return_value=test_files), \
             patch('os.path.getmtime', return_value=time.time() - 400), \
             patch('os.remove', side_effect=mock_remove):

            # Should not raise exception even if some files can't be removed
            try:
                orchestration = UnifiedOrchestration()
                # If we get here, the exception was handled gracefully
                success = True
            except OSError:
                success = False

            self.assertTrue(success, "Cleanup should handle concurrent file removal gracefully")

    def test_prompt_file_content_isolation(self):
        """Test that different agent tasks have completely isolated prompt content."""
        tasks = [
            ("Fix database connection pooling", "database", "pooling"),
            ("Update API documentation", "api", "documentation"),
            ("Refactor authentication middleware", "authentication", "middleware"),
        ]

        written_prompts = {}
        original_open = open

        def capture_prompt_writes(filename, mode='r', *args, **kwargs):
            if mode == 'w' and 'agent_prompt' in filename:
                class MockFile:
                    def __init__(self, path):
                        self.path = path
                        self.content = ""

                    def write(self, data):
                        self.content += data

                    def __enter__(self):
                        return self

                    def __exit__(self, *args):
                        written_prompts[self.path] = self.content

                return MockFile(filename)
            else:
                return original_open(filename, mode, *args, **kwargs)

        with patch('subprocess.run') as mock_subprocess, \
             patch('os.makedirs'), \
             patch('os.path.exists', return_value=False), \
             patch.object(TaskDispatcher, '_get_active_tmux_agents', return_value=set()), \
             patch('builtins.open', side_effect=capture_prompt_writes):

            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = ""

            for i, (task_desc, keyword1, keyword2) in enumerate(tasks):
                # Generate agent for this task
                agents = self.task_dispatcher.analyze_task_and_create_agents(task_desc)
                self.assertEqual(len(agents), 1)

                # Create the agent (should write prompt file)
                agent_name = f"task-agent-{i}"
                agent_spec = agents[0].copy()
                agent_spec['name'] = agent_name

                self.task_dispatcher.create_dynamic_agent(agent_spec)

        # Verify each prompt contains only its own task content
        self.assertEqual(len(written_prompts), len(tasks))

        prompt_contents = list(written_prompts.values())
        for i, (task_desc, keyword1, keyword2) in enumerate(tasks):
            prompt_content = prompt_contents[i]

            # Should contain its own task keywords
            self.assertIn(keyword1, prompt_content.lower())
            self.assertIn(keyword2, prompt_content.lower())

            # Should NOT contain other tasks' keywords
            for j, (other_task, other_kw1, other_kw2) in enumerate(tasks):
                if i != j:
                    # Check that other tasks' specific keywords are not present
                    if other_kw1 not in keyword1 and other_kw1 not in keyword2:
                        self.assertNotIn(other_kw1, prompt_content.lower(),
                                       f"Prompt {i} should not contain keyword '{other_kw1}' from task {j}")

    def test_memory_leak_prevention(self):
        """Test that prompt files don't accumulate indefinitely causing memory issues."""
        # Simulate many orchestration runs over time
        orchestration_runs = 50
        files_per_run = 3

        all_created_files = []

        for run in range(orchestration_runs):
            # Create files for this run
            run_files = []
            for agent in range(files_per_run):
                filename = f"{self.test_temp_dir}/agent_prompt_run{run}_agent{agent}.txt"
                with open(filename, 'w') as f:
                    f.write(f"Task for run {run}, agent {agent}")
                run_files.append(filename)
                all_created_files.append(filename)

            # Make earlier runs' files old enough to be cleaned up
            if run > 10:  # Keep some files recent
                for old_file in run_files:
                    old_time = time.time() - (400 + run * 10)  # Increasingly old
                    os.utime(old_file, (old_time, old_time))

        with patch('glob.glob', return_value=all_created_files), \
             patch('os.remove') as mock_remove:

            # Mock getmtime to return file ages based on filename
            def mock_getmtime(path):
                if 'run0' in path or 'run1' in path:
                    return time.time() - 3600  # 1 hour old
                elif any(f'run{i}' in path for i in range(2, 40)):
                    return time.time() - 600   # 10 minutes old
                else:
                    return time.time() - 120   # 2 minutes old (recent)

            with patch('os.path.getmtime', side_effect=mock_getmtime):
                # Trigger cleanup
                orchestration = UnifiedOrchestration()

                # Verify that old files were cleaned up (prevent memory leak)
                # Should clean up at least the very old files
                removed_count = mock_remove.call_count
                self.assertGreater(removed_count, 20,
                                 "Should remove old files to prevent memory leak")

                # Verify recent files were not all removed
                recent_files_removed = sum(1 for call in mock_remove.call_args_list
                                         if any(f'run{i}' in str(call) for i in range(45, 50)))
                self.assertLess(recent_files_removed, files_per_run * 5,
                               "Should not remove all recent files")

    def test_cross_user_isolation(self):
        """Test that different users/contexts don't interfere with each other's prompt files."""
        # This test ensures that in multi-user or multi-context environments,
        # prompt files don't leak between different orchestration contexts

        user_contexts = ["user1", "user2", "user3"]
        context_files = {}

        for user in user_contexts:
            user_files = []
            for i in range(3):
                filename = f"{self.test_temp_dir}/agent_prompt_{user}_task{i}.txt"
                with open(filename, 'w') as f:
                    f.write(f"Task for {user}: task {i}")
                user_files.append(filename)
            context_files[user] = user_files

        # Simulate cleanup for one specific user context
        target_user = "user2"
        target_files = context_files[target_user]

        # Make only target user's files old
        for filename in target_files:
            old_time = time.time() - 400
            os.utime(filename, (old_time, old_time))

        with patch('glob.glob', return_value=target_files), \
             patch('os.path.getmtime', return_value=time.time() - 400), \
             patch('os.remove') as mock_remove:

            # Trigger cleanup
            orchestration = UnifiedOrchestration()

            # Verify only target user's files were cleaned up
            removed_files = [call[0][0] for call in mock_remove.call_args_list]
            self.assertEqual(set(removed_files), set(target_files))

            # Verify other users' files were not affected
            for other_user in user_contexts:
                if other_user != target_user:
                    for other_file in context_files[other_user]:
                        self.assertNotIn(other_file, removed_files)


class TestPromptFileIntegration(unittest.TestCase):
    """Integration tests for prompt file lifecycle in realistic scenarios."""

    def setUp(self):
        self.test_temp_dir = tempfile.mkdtemp(prefix="prompt_integration_test_")

    def tearDown(self):
        if os.path.exists(self.test_temp_dir):
            shutil.rmtree(self.test_temp_dir)

    def test_realistic_production_scenario(self):
        """Test the exact scenario that caused the production bug."""
        # Scenario: User requests server modification, but system executes PR comment task

        # Step 1: Previous orchestration run left stale files
        stale_files = []
        for i in range(5):
            filename = f"{self.test_temp_dir}/agent_prompt_stale_agent_{i}.txt"
            with open(filename, 'w') as f:
                f.write(f"""Task: Respond to PR #1118 comments about code formatting

This is a stale task from a previous orchestration run.
The user originally asked about PR comment responses.
""")
            # Make files old (simulate previous run from hours ago)
            old_time = time.time() - 7200  # 2 hours old
            os.utime(filename, (old_time, old_time))
            stale_files.append(filename)

        # Step 2: User makes new request
        new_task = "Modify run_local_server.sh to avoid killing already running servers"

        with patch('glob.glob', return_value=stale_files), \
             patch('os.path.getmtime', return_value=time.time() - 7200), \
             patch('os.remove') as mock_remove, \
             patch('subprocess.run') as mock_subprocess, \
             patch('os.makedirs'), \
             patch('os.path.exists', return_value=False), \
             patch.object(TaskDispatcher, '_get_active_tmux_agents', return_value=set()):

            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = ""

            # Step 3: New orchestration should clean up stale files
            orchestration = UnifiedOrchestration()
            task_dispatcher = TaskDispatcher()

            # Verify stale files were cleaned up
            expected_removes = [call(f) for f in stale_files]
            mock_remove.assert_has_calls(expected_removes, any_order=True)

            # Step 4: Generate agents for new task
            agents = task_dispatcher.analyze_task_and_create_agents(new_task)
            self.assertEqual(len(agents), 1)

            agent = agents[0]

            # Step 5: Verify new task content, not stale content
            self.assertIn("run_local_server.sh", agent['prompt'])
            self.assertIn("server", agent['prompt'].lower())
            self.assertNotIn("PR #1118", agent['prompt'])
            self.assertNotIn("comment", agent['prompt'].lower())
            self.assertNotIn("formatting", agent['prompt'].lower())

    def test_rapid_successive_orchestration_calls(self):
        """Test rapid successive orchestration calls don't interfere."""
        tasks = [
            "Fix unit tests in auth module",
            "Update API documentation",
            "Refactor database connections"
        ]

        generated_agents = []

        with patch('subprocess.run') as mock_subprocess, \
             patch('os.makedirs'), \
             patch('os.path.exists', return_value=False), \
             patch.object(TaskDispatcher, '_get_active_tmux_agents', return_value=set()), \
             patch('glob.glob', return_value=[]):  # No stale files

            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = ""

            task_dispatcher = TaskDispatcher()

            # Make rapid successive calls
            for task in tasks:
                agents = task_dispatcher.analyze_task_and_create_agents(task)
                self.assertEqual(len(agents), 1)
                generated_agents.append(agents[0])
                time.sleep(0.01)  # Minimal delay

            # Verify each agent has correct task content
            for i, agent in enumerate(generated_agents):
                expected_task = tasks[i]
                self.assertIn(expected_task, agent['prompt'])

                # Verify no cross-contamination
                for j, other_task in enumerate(tasks):
                    if i != j:
                        # Check that other tasks don't leak into this agent's prompt
                        other_keywords = other_task.split()
                        current_keywords = expected_task.split()

                        for keyword in other_keywords:
                            if keyword not in current_keywords and len(keyword) > 3:
                                self.assertNotIn(keyword, agent['prompt'])


if __name__ == '__main__':
    # Run tests with detailed output
    unittest.main(verbosity=2)
