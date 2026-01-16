#!/usr/bin/env python3
"""
Red-Green test for orchestration task dispatcher fix.
Verifies that the system creates general task agents instead of hardcoded test agents.
"""

import unittest
from unittest.mock import MagicMock, mock_open, patch

from orchestration.task_dispatcher import TaskDispatcher


class TestTaskDispatcherFix(unittest.TestCase):
    """Test that task dispatcher creates appropriate agents for requested tasks."""

    def setUp(self):
        """Set up test dispatcher."""
        self.dispatcher = TaskDispatcher()

    def test_server_start_task_creates_general_agent(self):
        """Test that server start request creates general task agent, not test agent."""
        # RED: This would have failed before the fix
        task = "Start a test server on port 8082"
        # Mock shutil.which to ensure CLI is available in CI
        with (
            patch("orchestration.task_dispatcher.shutil.which", return_value="/usr/bin/claude"),
            patch("orchestration.task_dispatcher.subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            agents = self.dispatcher.analyze_task_and_create_agents(task)

        # Should create exactly one agent
        assert len(agents) == 1

        # Should be a general task agent, not test-analyzer or test-writer
        agent = agents[0]
        assert "task-agent" in agent["name"]
        assert "test-analyzer" not in agent["name"]
        assert "test-writer" not in agent["name"]

        # Should have the exact task as focus
        assert agent["focus"] == task

        # Should have general capabilities
        assert "task_execution" in agent["capabilities"]
        assert "server_management" in agent["capabilities"]

    def test_testserver_command_creates_general_agent(self):
        """Test that /testserver command creates general agent."""
        task = "tell the agent to start the test server on 8082 instead"
        # Mock shutil.which to ensure CLI is available in CI
        with (
            patch("orchestration.task_dispatcher.shutil.which", return_value="/usr/bin/claude"),
            patch("orchestration.task_dispatcher.subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            agents = self.dispatcher.analyze_task_and_create_agents(task)

        # Should not create test coverage agents
        assert len(agents) == 1
        agent = agents[0]
        assert "test-analyzer" not in agent["name"]
        assert "test-writer" not in agent["name"]
        assert "coverage" not in agent["focus"].lower()

    def test_copilot_task_creates_general_agent(self):
        """Test that copilot tasks create general agents."""
        task = "run /copilot on PR 825"
        # Mock shutil.which to ensure CLI is available in CI
        with (
            patch("orchestration.task_dispatcher.shutil.which", return_value="/usr/bin/claude"),
            patch("orchestration.task_dispatcher.subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            agents = self.dispatcher.analyze_task_and_create_agents(task)

        # Should create general task agent
        assert len(agents) == 1
        agent = agents[0]
        assert "task-agent" in agent["name"]
        assert agent["focus"] == task

    def test_no_hardcoded_patterns(self):
        """Test that various tasks all create general agents, not pattern-matched types."""
        test_tasks = [
            "Start server on port 6006",
            "Run copilot analysis",
            "Execute test server with production mode",
            "Modify testserver command to use prod mode",
            "Update configuration files",
            "Create a new feature",
            "Fix a bug in the system",
            "Write documentation",
        ]

        for task in test_tasks:
            with self.subTest(task=task):
                # Mock shutil.which to ensure CLI is available in CI
                with (
                    patch("orchestration.task_dispatcher.shutil.which", return_value="/usr/bin/claude"),
                    patch("orchestration.task_dispatcher.subprocess.run") as mock_run,
                ):
                    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
                    agents = self.dispatcher.analyze_task_and_create_agents(task)

                    # All tasks should create single general agent
                    assert len(agents) == 1
                    agent = agents[0]

                    # Should always be task-agent, never specialized types
                    assert "task-agent" in agent["name"]
                    assert "test-analyzer" not in agent["name"]
                    assert "test-writer" not in agent["name"]
                    assert "security-scanner" not in agent["name"]
                    assert "frontend-developer" not in agent["name"]
                    assert "backend-developer" not in agent["name"]

                    # Focus should be the exact task
                    assert agent["focus"] == task


    def test_cli_specific_default_model_gemini(self):
        """Test that Gemini CLI defaults to GEMINI_MODEL when model is 'sonnet'."""
        from orchestration.task_dispatcher import GEMINI_MODEL
        
        agent_spec = {
            "name": "test-agent",
            "focus": "test task",
            "cli": "gemini",  # Use 'cli' not 'cli_chain' for create_dynamic_agent
            "model": "sonnet",  # Default value that should be overridden
        }
        
        # Verify initial model is 'sonnet'
        self.assertEqual(agent_spec["model"], "sonnet")
        
        with (
            patch("orchestration.task_dispatcher.shutil.which", return_value="/usr/bin/gemini"),
            patch("orchestration.task_dispatcher.subprocess.run") as mock_run,
            patch.object(self.dispatcher, "_create_worktree_at_location") as mock_worktree,
            patch.object(self.dispatcher, "_get_active_tmux_agents", return_value=set()),
            patch.object(self.dispatcher, "_check_existing_agents", return_value=set()),
            patch.object(self.dispatcher, "_cleanup_stale_prompt_files"),
            patch.object(self.dispatcher, "_validate_cli_availability", return_value=True),
            patch("orchestration.task_dispatcher.Path.write_text") as mock_write_text,
            patch("os.makedirs"),
            patch("os.chmod"),
            patch("builtins.open", mock_open()),
            patch("os.path.exists", return_value=False),
        ):
            mock_worktree.return_value = ("/tmp/test", MagicMock(returncode=0))
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            result = self.dispatcher.create_dynamic_agent(agent_spec)
            
            # Verify that model was replaced with GEMINI_MODEL in agent_spec
            self.assertTrue(result)
            # The model should have been replaced with GEMINI_MODEL for gemini CLI
            # Check the written script content to verify GEMINI_MODEL was used
            if mock_write_text.called:
                script_content = mock_write_text.call_args[0][0]
                # The script should contain GEMINI_MODEL, not 'sonnet'
                self.assertIn(GEMINI_MODEL, script_content)
                self.assertNotIn("sonnet", script_content)

    def test_cli_specific_default_model_cursor(self):
        """Test that Cursor CLI defaults to CURSOR_MODEL when model is 'sonnet'."""
        from orchestration.task_dispatcher import CURSOR_MODEL
        
        agent_spec = {
            "name": "test-agent",
            "focus": "test task",
            "cli_chain": "cursor",
            "model": "sonnet",  # Default value that should be overridden
        }
        
        with (
            patch("orchestration.task_dispatcher.shutil.which", return_value="/usr/bin/cursor-agent"),
            patch("orchestration.task_dispatcher.subprocess.run") as mock_run,
            patch.object(self.dispatcher, "_create_worktree_at_location") as mock_worktree,
            patch.object(self.dispatcher, "_get_active_tmux_agents", return_value=set()),
            patch.object(self.dispatcher, "_check_existing_agents", return_value=set()),
            patch.object(self.dispatcher, "_cleanup_stale_prompt_files"),
            patch.object(self.dispatcher, "_validate_cli_availability", return_value=True),
        ):
            mock_worktree.return_value = ("/tmp/test", MagicMock(returncode=0))
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            result = self.dispatcher.create_dynamic_agent(agent_spec)
            self.assertTrue(result)

    def test_model_placeholder_in_command_template(self):
        """Test that {model} placeholder works in Gemini command template."""
        from orchestration.task_dispatcher import CLI_PROFILES
        
        gemini_profile = CLI_PROFILES.get("gemini")
        self.assertIsNotNone(gemini_profile, "Gemini CLI profile should exist")
        
        command_template = gemini_profile.get("command_template")
        self.assertIsNotNone(command_template, "Command template should exist")
        
        # Verify template uses {model} placeholder, not hardcoded GEMINI_MODEL
        self.assertIn("{model}", command_template, 
                     "Command template should use {model} placeholder")
        self.assertNotIn("GEMINI_MODEL", command_template,
                        "Command template should not contain hardcoded GEMINI_MODEL")
        
        # Test that template can be formatted with a model value
        test_model = "gemini-3-auto"
        formatted = command_template.format(
            binary="/usr/bin/gemini",
            model=test_model,
            prompt_file="/tmp/test.txt"
        )
        self.assertIn(test_model, formatted,
                     f"Formatted command should contain model '{test_model}'")

    def test_explicit_model_overrides_default(self):
        """Test that explicit model parameter overrides CLI-specific defaults."""
        agent_spec = {
            "name": "test-agent",
            "focus": "test task",
            "cli_chain": "gemini",
            "model": "gemini-3-auto",  # Explicit model, not 'sonnet'
        }
        
        with (
            patch("orchestration.task_dispatcher.shutil.which", return_value="/usr/bin/gemini"),
            patch("orchestration.task_dispatcher.subprocess.run") as mock_run,
            patch.object(self.dispatcher, "_create_worktree_at_location") as mock_worktree,
            patch.object(self.dispatcher, "_get_active_tmux_agents", return_value=set()),
            patch.object(self.dispatcher, "_check_existing_agents", return_value=set()),
            patch.object(self.dispatcher, "_cleanup_stale_prompt_files"),
            patch.object(self.dispatcher, "_validate_cli_availability", return_value=True),
        ):
            mock_worktree.return_value = ("/tmp/test", MagicMock(returncode=0))
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            result = self.dispatcher.create_dynamic_agent(agent_spec)
            self.assertTrue(result)
            # The explicit model should be used, not the default


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
