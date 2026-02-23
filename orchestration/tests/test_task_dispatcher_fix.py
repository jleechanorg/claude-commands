#!/usr/bin/env python3
"""
Red-Green test for orchestration task dispatcher fix.
Verifies that the system creates general task agents instead of hardcoded test agents.
"""

import unittest
from unittest.mock import ANY, MagicMock, mock_open, patch

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

    def test_detects_invalid_base_ref_error(self):
        """Invalid git base-ref errors should be recognized for interactive recovery."""
        self.assertTrue(self.dispatcher._is_invalid_base_ref_error("fatal: not a valid object name: 'main'"))
        self.assertTrue(self.dispatcher._is_invalid_base_ref_error("fatal: invalid reference: main"))
        self.assertFalse(self.dispatcher._is_invalid_base_ref_error("fatal: branch already exists"))

    def test_retries_worktree_with_user_base_branch_after_main_failure(self):
        """When main is missing, dispatcher should prompt for base branch and retry once."""
        agent_spec = {
            "name": "test-agent",
            "focus": "write 2+2 in a file",
            "cli": "claude",
            "model": "sonnet",
        }

        first_failure = MagicMock(returncode=128, stderr="fatal: not a valid object name: 'main'\n")
        second_success = MagicMock(returncode=0, stderr="")

        with (
            patch("orchestration.task_dispatcher.shutil.which", return_value="/usr/bin/claude"),
            patch("orchestration.task_dispatcher.subprocess.run") as mock_run,
            patch.object(self.dispatcher, "_create_worktree_at_location") as mock_worktree,
            patch.object(self.dispatcher, "_prompt_for_base_branch", return_value="develop") as mock_prompt,
            patch.object(self.dispatcher, "_get_active_tmux_agents", return_value=set()),
            patch.object(self.dispatcher, "_check_existing_agents", return_value=set()),
            patch.object(self.dispatcher, "_cleanup_stale_prompt_files"),
            patch.object(self.dispatcher, "_validate_cli_availability", return_value=True),
            patch("orchestration.task_dispatcher.Path.write_text"),
            patch("os.makedirs"),
            patch("os.chmod"),
            patch("builtins.open", mock_open()),
            patch("os.path.exists", return_value=False),
        ):
            mock_worktree.side_effect = [
                ("/tmp/test-agent", first_failure),
                ("/tmp/test-agent", second_success),
            ]
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            result = self.dispatcher.create_dynamic_agent(agent_spec)

        self.assertTrue(result)
        mock_prompt.assert_called_once_with("main")
        self.assertEqual(mock_worktree.call_count, 2)
        self.assertEqual(mock_worktree.call_args_list[0].kwargs.get("base_ref"), "main")
        self.assertEqual(mock_worktree.call_args_list[1].kwargs.get("base_ref"), "develop")
        self.assertEqual(self.dispatcher._interactive_base_ref, "develop")

    def test_does_not_cache_interactive_base_ref_when_retry_still_fails(self):
        """Interactive base ref should only be cached after a successful retry."""
        agent_spec = {
            "name": "test-agent",
            "focus": "write 2+2 in a file",
            "cli": "claude",
            "model": "sonnet",
        }

        first_failure = MagicMock(returncode=128, stderr="fatal: not a valid object name: 'main'\n")
        second_failure = MagicMock(returncode=128, stderr="fatal: not a valid object name: 'develop'\n")

        with (
            patch("orchestration.task_dispatcher.shutil.which", return_value="/usr/bin/claude"),
            patch("orchestration.task_dispatcher.subprocess.run") as mock_run,
            patch.object(self.dispatcher, "_create_worktree_at_location") as mock_worktree,
            patch.object(self.dispatcher, "_prompt_for_base_branch", return_value="develop"),
            patch.object(self.dispatcher, "_get_active_tmux_agents", return_value=set()),
            patch.object(self.dispatcher, "_check_existing_agents", return_value=set()),
            patch.object(self.dispatcher, "_cleanup_stale_prompt_files"),
            patch.object(self.dispatcher, "_validate_cli_availability", return_value=True),
            patch("orchestration.task_dispatcher.Path.write_text"),
            patch("os.makedirs"),
            patch("os.chmod"),
            patch("builtins.open", mock_open()),
            patch("os.path.exists", return_value=False),
        ):
            mock_worktree.side_effect = [
                ("/tmp/test-agent", first_failure),
                ("/tmp/test-agent", second_failure),
            ]
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            result = self.dispatcher.create_dynamic_agent(agent_spec)

        self.assertFalse(result)
        self.assertIsNone(self.dispatcher._interactive_base_ref)

    def test_create_worktree_retries_in_tmp_directory_after_default_failure(self):
        """Worktree creation should retry once in /tmp fallback directory when default location fails."""
        failure_result = MagicMock(returncode=128, stderr="fatal: Permission denied")
        success_result = MagicMock(returncode=0, stderr="")

        with (
            patch.object(self.dispatcher, "_calculate_agent_directory", return_value="/Users/test/orch/retry-agent"),
            patch.object(self.dispatcher, "_ensure_directory_exists"),
            patch.object(
                self.dispatcher,
                "_create_tmp_worktree_directory",
                return_value="/tmp/orchestration_worktrees/orch_repo/retry-agent-abc123",
            ),
            patch.object(self.dispatcher, "_branch_exists", return_value=False),
            patch("orchestration.task_dispatcher.subprocess.run") as mock_run,
        ):
            mock_run.side_effect = [failure_result, success_result]
            agent_dir, result = self.dispatcher._create_worktree_at_location(
                {"name": "retry-agent"},
                "retry-agent-work",
                base_ref="develop",
                create_new_branch=True,
            )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(agent_dir, "/tmp/orchestration_worktrees/orch_repo/retry-agent-abc123")
        self.assertEqual(mock_run.call_count, 2)
        first_cmd = mock_run.call_args_list[0][0][0]
        second_cmd = mock_run.call_args_list[1][0][0]
        self.assertEqual(first_cmd[:3], ["git", "worktree", "add"])
        self.assertIn("/Users/test/orch/retry-agent", first_cmd)
        self.assertEqual(second_cmd[:3], ["git", "worktree", "add"])
        self.assertIn("/tmp/orchestration_worktrees/orch_repo/retry-agent-abc123", second_cmd)

    def test_build_worktree_command_skips_b_flag_when_branch_already_exists(self):
        """When create_new_branch=True but branch already exists (from partial failure), omit -b."""
        with patch.object(self.dispatcher, "_branch_exists", return_value=True):
            cmd = self.dispatcher._build_worktree_add_command(
                agent_dir="/tmp/test-agent",
                branch_name="fix/my-branch",
                base_ref="main",
                create_new_branch=True,
            )

        # Should NOT use -b since branch already exists
        self.assertNotIn("-b", cmd)
        self.assertEqual(cmd, ["git", "worktree", "add", "/tmp/test-agent", "fix/my-branch"])

    def test_build_worktree_command_resets_existing_branch_when_base_ref_mismatch(self):
        """When existing branch matches create_new_branch but stale base, force-reset it with -B."""
        with (
            patch.object(self.dispatcher, "_branch_exists", return_value=True),
            patch.object(self.dispatcher, "_branch_matches_base_ref", return_value=False),
        ):
            cmd = self.dispatcher._build_worktree_add_command(
                agent_dir="/tmp/test-agent",
                branch_name="fix/my-branch",
                base_ref="main",
                create_new_branch=True,
            )

        self.assertEqual(
            cmd,
            ["git", "worktree", "add", "-B", "fix/my-branch", "/tmp/test-agent", "main"],
        )

    def test_build_worktree_command_uses_b_flag_for_new_branch(self):
        """When create_new_branch=True and branch does not exist, use -b."""
        with patch.object(self.dispatcher, "_branch_exists", return_value=False):
            cmd = self.dispatcher._build_worktree_add_command(
                agent_dir="/tmp/test-agent",
                branch_name="fix/new-branch",
                base_ref="main",
                create_new_branch=True,
            )

        self.assertEqual(cmd, ["git", "worktree", "add", "-b", "fix/new-branch", "/tmp/test-agent", "main"])

    def test_create_worktree_skips_tmp_retry_for_non_path_errors(self):
        """Non-path git failures should not trigger /tmp retry."""
        failure_result = MagicMock(returncode=128, stderr="fatal: not a valid object name: 'main'")

        with (
            patch.object(self.dispatcher, "_calculate_agent_directory", return_value="/Users/test/orch/retry-agent"),
            patch.object(self.dispatcher, "_ensure_directory_exists"),
            patch.object(self.dispatcher, "_create_tmp_worktree_directory") as mock_tmp_dir,
            patch.object(self.dispatcher, "_branch_exists", return_value=False),
            patch("orchestration.task_dispatcher.subprocess.run") as mock_run,
        ):
            mock_run.return_value = failure_result
            _, result = self.dispatcher._create_worktree_at_location(
                {"name": "retry-agent"},
                "retry-agent-work",
                base_ref="main",
                create_new_branch=True,
            )

        self.assertEqual(result.returncode, 128)
        self.assertEqual(mock_run.call_count, 1)
        mock_tmp_dir.assert_not_called()

    def test_create_worktree_with_existing_local_branch_uses_local_checkout(self):
        """Existing local branches should be added directly without creating a new branch."""
        branch_name = "feature/local-branch"

        with (
            patch.object(self.dispatcher, "_calculate_agent_directory", return_value="/Users/test/orch/local-agent"),
            patch.object(self.dispatcher, "_ensure_directory_exists"),
            patch.object(self.dispatcher, "_branch_exists", return_value=True),
            patch("orchestration.task_dispatcher.subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            agent_dir, result = self.dispatcher._create_worktree_at_location(
                {"name": "local-agent"},
                branch_name,
                create_new_branch=False,
            )

        self.assertEqual(agent_dir, "/Users/test/orch/local-agent")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(mock_run.call_args[0][0], [
            "git",
            "worktree",
            "add",
            "/Users/test/orch/local-agent",
            branch_name,
        ])

    def test_create_worktree_with_existing_remote_branch_creates_local_tracking_branch(self):
        """Remote-only existing branches should be checked out as local tracking branches."""
        branch_name = "feature/remote-branch"

        with (
            patch.object(self.dispatcher, "_calculate_agent_directory", return_value="/Users/test/orch/remote-agent"),
            patch.object(self.dispatcher, "_ensure_directory_exists"),
            patch.object(self.dispatcher, "_branch_exists", return_value=False),
            patch.object(self.dispatcher, "_remote_branch_exists", return_value=True),
            patch("orchestration.task_dispatcher.subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            agent_dir, result = self.dispatcher._create_worktree_at_location(
                {"name": "remote-agent"},
                branch_name,
                create_new_branch=False,
            )

        self.assertEqual(agent_dir, "/Users/test/orch/remote-agent")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(mock_run.call_args[0][0], [
            "git",
            "worktree",
            "add",
            "-b",
            branch_name,
            "/Users/test/orch/remote-agent",
            f"origin/{branch_name}",
        ])

    def test_create_worktree_retries_in_tmp_directory_with_remote_existing_branch(self):
        """Retry path should preserve remote-branch tracking when default location fails."""
        branch_name = "feature/remote-branch"

        with (
            patch.object(self.dispatcher, "_calculate_agent_directory", return_value="/Users/test/orch/remote-agent"),
            patch.object(self.dispatcher, "_ensure_directory_exists"),
            patch.object(
                self.dispatcher,
                "_create_tmp_worktree_directory",
                return_value="/tmp/orchestration_worktrees/orch_repo/remote-agent-abc123",
            ),
            patch.object(self.dispatcher, "_branch_exists", return_value=False),
            patch.object(self.dispatcher, "_remote_branch_exists", return_value=True),
            patch("orchestration.task_dispatcher.subprocess.run") as mock_run,
        ):
            mock_run.side_effect = [
                MagicMock(returncode=128, stderr="fatal: Permission denied"),
                MagicMock(returncode=0, stdout="", stderr=""),
            ]
            agent_dir, result = self.dispatcher._create_worktree_at_location(
                {"name": "remote-agent"},
                branch_name,
                create_new_branch=False,
            )

        self.assertEqual(agent_dir, "/tmp/orchestration_worktrees/orch_repo/remote-agent-abc123")
        self.assertEqual(result.returncode, 0)
        first_cmd = mock_run.call_args_list[0][0][0]
        second_cmd = mock_run.call_args_list[1][0][0]
        self.assertEqual(first_cmd, [
            "git",
            "worktree",
            "add",
            "-b",
            branch_name,
            "/Users/test/orch/remote-agent",
            f"origin/{branch_name}",
        ])
        self.assertEqual(second_cmd, [
            "git",
            "worktree",
            "add",
            "-b",
            branch_name,
            "/tmp/orchestration_worktrees/orch_repo/remote-agent-abc123",
            f"origin/{branch_name}",
        ])

    def test_create_worktree_cleans_tmp_dir_when_retry_fails(self):
        """Temporary fallback directory should be cleaned up when retry also fails."""
        first_failure = MagicMock(returncode=128, stderr="fatal: Permission denied")
        retry_failure = MagicMock(returncode=128, stderr="fatal: Permission denied")
        tmp_dir = "/tmp/orchestration_worktrees/orch_repo/retry-agent-abc123"

        with (
            patch.object(self.dispatcher, "_calculate_agent_directory", return_value="/Users/test/orch/retry-agent"),
            patch.object(self.dispatcher, "_ensure_directory_exists"),
            patch.object(self.dispatcher, "_create_tmp_worktree_directory", return_value=tmp_dir),
            patch.object(self.dispatcher, "_branch_exists", return_value=False),
            patch("orchestration.task_dispatcher.subprocess.run") as mock_run,
            patch.object(self.dispatcher, "_safe_rmtree") as mock_cleanup,
        ):
            mock_run.side_effect = [first_failure, retry_failure]
            _, result = self.dispatcher._create_worktree_at_location(
                {"name": "retry-agent"},
                "retry-agent-work",
                base_ref="main",
                create_new_branch=True,
            )

        self.assertEqual(result.returncode, 128)
        mock_cleanup.assert_called_once_with(tmp_dir)

    def test_no_worktree_mode_honors_existing_branch_checkout(self):
        """No-worktree mode should checkout requested existing branch before execution."""
        agent_spec = {
            "name": "test-agent",
            "focus": "task",
            "cli": "claude",
            "model": "sonnet",
            "no_worktree": True,
            "existing_branch": "develop",
        }

        with (
            patch("orchestration.task_dispatcher.shutil.which", return_value="/usr/bin/claude"),
            patch("orchestration.task_dispatcher.subprocess.run") as mock_run,
            patch.object(self.dispatcher, "_get_active_tmux_agents", return_value=set()),
            patch.object(self.dispatcher, "_check_existing_agents", return_value=set()),
            patch.object(self.dispatcher, "_cleanup_stale_prompt_files"),
            patch.object(self.dispatcher, "_validate_cli_availability", return_value=True),
            patch.object(self.dispatcher, "_checkout_branch", return_value=True) as mock_checkout,
            patch("orchestration.task_dispatcher.Path.write_text"),
            patch("os.makedirs"),
            patch("os.chmod"),
            patch("builtins.open", mock_open()),
            patch("os.path.exists", return_value=False),
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            result = self.dispatcher.create_dynamic_agent(agent_spec)

        self.assertTrue(result)
        mock_checkout.assert_called_once_with("develop", ANY)

    def test_create_dynamic_agent_uses_unique_run_artifacts(self):
        """Each run should get unique log/result/prompt files while preserving legacy pointers."""
        agent_spec1 = {
            "name": "test-agent",
            "focus": "task one",
            "cli": "claude",
            "model": "sonnet",
            "no_worktree": True,
        }
        agent_spec2 = {
            "name": "test-agent",
            "focus": "task two",
            "cli": "claude",
            "model": "sonnet",
            "no_worktree": True,
        }

        with (
            patch("orchestration.task_dispatcher.shutil.which", return_value="/usr/bin/claude"),
            patch("orchestration.task_dispatcher.subprocess.run") as mock_run,
            patch.object(self.dispatcher, "_get_active_tmux_agents", return_value=set()),
            patch.object(self.dispatcher, "_check_existing_agents", return_value=set()),
            patch.object(self.dispatcher, "_cleanup_stale_prompt_files"),
            patch.object(self.dispatcher, "_validate_cli_availability", return_value=True),
            patch.object(self.dispatcher, "_generate_run_artifact_suffix", side_effect=["run1", "run2"]),
            patch.object(self.dispatcher, "_set_latest_artifact_pointer") as mock_pointer,
            patch("orchestration.task_dispatcher.Path.write_text"),
            patch("os.makedirs"),
            patch("os.chmod"),
            patch("builtins.open", mock_open()),
            patch("os.path.exists", return_value=False),
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            self.assertTrue(self.dispatcher.create_dynamic_agent(agent_spec1))
            self.assertTrue(self.dispatcher.create_dynamic_agent(agent_spec2))

        self.assertIn("_run1.log", agent_spec1["log_file"])
        self.assertIn("_run2.log", agent_spec2["log_file"])
        self.assertIn("_run1.json", agent_spec1["result_file"])
        self.assertIn("_run2.json", agent_spec2["result_file"])
        self.assertIn("_run1.txt", agent_spec1["prompt_file"])
        self.assertIn("_run2.txt", agent_spec2["prompt_file"])
        self.assertEqual(agent_spec1["legacy_log_file"], agent_spec2["legacy_log_file"])
        self.assertEqual(agent_spec1["legacy_result_file"], agent_spec2["legacy_result_file"])
        self.assertGreaterEqual(mock_pointer.call_count, 4)

    def test_get_active_tmux_agents_uses_dispatcher_socket(self):
        """Active-agent discovery should query tmux on the dispatcher socket."""
        with (
            patch("orchestration.task_dispatcher.shutil.which", return_value="/usr/bin/tmux"),
            patch.object(self.dispatcher, "_tmux_base_command", return_value=["tmux", "-L", "sockA"]),
            patch.object(self.dispatcher, "_is_agent_actively_working", return_value=True),
            patch("orchestration.task_dispatcher.subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="task-agent-a\n", stderr="")
            active = self.dispatcher._get_active_tmux_agents()

        self.assertEqual(active, {"task-agent-a"})
        self.assertEqual(
            mock_run.call_args_list[0][0][0],
            ["tmux", "-L", "sockA", "list-sessions", "-F", "#{session_name}"],
        )

    def test_is_agent_actively_working_uses_dispatcher_socket(self):
        """Pane capture should use the same dispatcher tmux socket."""
        with (
            patch.object(self.dispatcher, "_tmux_base_command", return_value=["tmux", "-L", "sockA"]),
            patch("orchestration.task_dispatcher.subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="still working", stderr="")
            self.assertTrue(self.dispatcher._is_agent_actively_working("task-agent-a"))

        self.assertEqual(
            mock_run.call_args_list[0][0][0],
            ["tmux", "-L", "sockA", "capture-pane", "-t", "task-agent-a", "-p"],
        )

    def test_check_existing_agents_uses_dispatcher_socket(self):
        """Collision checks should list tmux sessions on the dispatcher socket."""
        with (
            patch("orchestration.task_dispatcher.shutil.which", return_value="/usr/bin/tmux"),
            patch.object(self.dispatcher, "_tmux_base_command", return_value=["tmux", "-L", "sockA"]),
            patch("orchestration.task_dispatcher.subprocess.run") as mock_run,
            patch("orchestration.task_dispatcher.glob.glob", return_value=[]),
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="task-agent-a\n", stderr="")
            existing = self.dispatcher._check_existing_agents()

        self.assertIn("task-agent-a", existing)
        self.assertEqual(
            mock_run.call_args_list[0][0][0],
            ["tmux", "-L", "sockA", "list-sessions", "-F", "#{session_name}"],
        )

    def test_no_worktree_fallback_checks_out_existing_branch(self):
        """Fallback from failed worktree should still checkout the requested existing branch."""
        agent_spec = {
            "name": "test-agent",
            "focus": "task",
            "cli": "claude",
            "model": "sonnet",
            "existing_branch": "develop",
        }
        worktree_failure = MagicMock(returncode=128, stderr="fatal: Permission denied")

        with (
            patch("orchestration.task_dispatcher.shutil.which", return_value="/usr/bin/claude"),
            patch("orchestration.task_dispatcher.subprocess.run") as mock_run,
            patch.object(self.dispatcher, "_create_worktree_at_location", return_value=("/tmp/test-agent", worktree_failure)),
            patch.object(self.dispatcher, "_prompt_to_continue_without_worktree", return_value=True),
            patch.object(self.dispatcher, "_get_active_tmux_agents", return_value=set()),
            patch.object(self.dispatcher, "_check_existing_agents", return_value=set()),
            patch.object(self.dispatcher, "_cleanup_stale_prompt_files"),
            patch.object(self.dispatcher, "_validate_cli_availability", return_value=True),
            patch.object(self.dispatcher, "_checkout_branch", return_value=True) as mock_checkout,
            patch("orchestration.task_dispatcher.Path.write_text"),
            patch("os.makedirs"),
            patch("os.chmod"),
            patch("builtins.open", mock_open()),
            patch("os.path.exists", return_value=False),
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            result = self.dispatcher.create_dynamic_agent(agent_spec)

        self.assertTrue(result)
        mock_checkout.assert_called_once_with("develop", ANY)

    def test_branch_exists_logs_exception_details(self):
        """Branch-existence helper should log failures instead of silently swallowing them."""
        with (
            patch("orchestration.task_dispatcher.subprocess.run", side_effect=RuntimeError("boom")),
            patch("orchestration.task_dispatcher.logger.warning") as mock_warning,
        ):
            self.assertFalse(TaskDispatcher._branch_exists("feature/test"))

        mock_warning.assert_called_once()

    def test_claude_launcher_script_does_not_unset_anthropic_auth_token(self):
        """Generated launcher script should preserve ANTHROPIC_AUTH_TOKEN for Claude auth."""
        agent_spec = {
            "name": "test-agent",
            "focus": "test auth token preservation",
            "cli": "claude",
            "model": "sonnet",
        }

        with (
            patch("orchestration.task_dispatcher.shutil.which", return_value="/usr/bin/claude"),
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

        self.assertTrue(result)
        self.assertTrue(mock_write_text.called)
        script_content = mock_write_text.call_args[0][0]
        self.assertNotIn("unset ANTHROPIC_AUTH_TOKEN", script_content)


class TestWrapPromptParameter(unittest.TestCase):
    """TDD RED tests: verify wrap_prompt parameter controls prompt wrapping behavior."""

    def setUp(self):
        """Set up test dispatcher."""
        self.dispatcher = TaskDispatcher()

    def test_wrap_prompt_false_returns_raw_task_description(self):
        """RED: wrap_prompt=False should return raw task_description as prompt."""
        task = "Run integration tests on the auth module"
        agents = self.dispatcher.analyze_task_and_create_agents(task, wrap_prompt=False)

        self.assertEqual(len(agents), 1)
        agent = agents[0]
        self.assertEqual(agent["prompt"], task,
                         f"FAIL: prompt should be raw task but got: {agent['prompt'][:100]}")

    def test_wrap_prompt_false_no_pr_mode_in_prompt(self):
        """RED: wrap_prompt=False should have no PR MODE instructions."""
        task = "Fix bug in login handler"
        agents = self.dispatcher.analyze_task_and_create_agents(task, wrap_prompt=False)

        agent = agents[0]
        self.assertNotIn("PR UPDATE MODE", agent["prompt"],
                         "FAIL: PR UPDATE MODE found in prompt when wrap_prompt=False")
        self.assertNotIn("NEW PR MODE", agent["prompt"],
                         "FAIL: NEW PR MODE found in prompt when wrap_prompt=False")
        self.assertNotIn("EXECUTION GUIDELINES", agent["prompt"],
                         "FAIL: EXECUTION GUIDELINES found in prompt when wrap_prompt=False")

    def test_wrap_prompt_false_no_pr_context_injected(self):
        """RED: wrap_prompt=False should not inject pr_context even for PR-mentioning tasks."""
        task = "Fix the tests on PR #42"
        agents = self.dispatcher.analyze_task_and_create_agents(task, wrap_prompt=False)

        agent = agents[0]
        self.assertNotIn("pr_context", agent,
                         "FAIL: pr_context injected when wrap_prompt=False")

    def test_wrap_prompt_true_enables_wrapping(self):
        """GREEN baseline: wrap_prompt=True enables prompt wrapping."""
        task = "Add a new feature to the dashboard"
        agents = self.dispatcher.analyze_task_and_create_agents(task, wrap_prompt=True)

        agent = agents[0]
        self.assertIn("NEW PR MODE", agent["prompt"],
                       "FAIL: wrap_prompt=True should include NEW PR MODE")

    def test_wrap_prompt_default_is_false(self):
        """Default wrap_prompt=False passes task directly without LLM analysis."""
        task = "Add a new feature to the dashboard"
        agents = self.dispatcher.analyze_task_and_create_agents(task)

        agent = agents[0]
        # Default is now False (direct prompt mode)
        self.assertEqual(agent["prompt"], task,
                        "FAIL: Default should pass task directly")

    def test_wrap_prompt_false_preserves_other_agent_spec_fields(self):
        """RED: wrap_prompt=False should still set name, type, focus, capabilities, cli."""
        task = "Deploy the staging server"
        agents = self.dispatcher.analyze_task_and_create_agents(task, wrap_prompt=False)

        agent = agents[0]
        self.assertIn("task-agent", agent["name"])
        self.assertEqual(agent["type"], "development")
        self.assertEqual(agent["focus"], task)
        self.assertIsInstance(agent["capabilities"], list)
        self.assertIn("cli", agent)

    def test_wrap_prompt_false_with_pr_task_still_detects_cli(self):
        """RED: wrap_prompt=False should still detect the correct CLI."""
        task = "Use codex to fix the bug"
        agents = self.dispatcher.analyze_task_and_create_agents(task, wrap_prompt=False)

        agent = agents[0]
        self.assertEqual(agent["prompt"], task)
        self.assertEqual(agent["cli"], "codex",
                         f"FAIL: CLI should be 'codex' but got '{agent.get('cli')}'")


class TestGhPrViewLogging(unittest.TestCase):
    """Tests for structured logging when gh pr view subprocess fails."""

    def setUp(self):
        """Set up test dispatcher."""
        self.dispatcher = TaskDispatcher()

    def test_gh_pr_view_exception_logs_debug(self):
        """Exception during gh pr view should emit logger.debug with gh_pr_view_failed."""
        task = "Fix tests on PR #123"
        with (
            patch("orchestration.task_dispatcher.shutil.which", return_value="/usr/bin/claude"),
            patch("orchestration.task_dispatcher.subprocess.run") as mock_run,
            patch("orchestration.task_dispatcher.logger") as mock_logger,
        ):
            # First call is _detect_pr_context → _find_recent_pr which calls subprocess
            # The gh pr view call is the one that should raise
            def run_side_effect(cmd, **kwargs):
                if "pr" in cmd and "view" in cmd:
                    raise OSError("gh not found")
                return MagicMock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            agents = self.dispatcher.analyze_task_and_create_agents(task, pr_update_mode=True, wrap_prompt=True)

        # Verify logger.debug was called with gh_pr_view_failed event
        debug_calls = [
            call for call in mock_logger.debug.call_args_list
            if call[0][0] == "gh_pr_view_failed"
        ]
        self.assertEqual(len(debug_calls), 1, "Expected exactly one gh_pr_view_failed log")
        self.assertTrue(
            debug_calls[0][1].get("exc_info"),
            "gh_pr_view_failed should be logged with exc_info=True",
        )
        extra = debug_calls[0][1].get("extra", {})
        self.assertEqual(extra["pr_number"], "123")

    def test_gh_pr_view_nonzero_exit_logs_debug(self):
        """Non-zero exit from gh pr view should emit logger.debug with gh_pr_view_nonzero_exit."""
        task = "Fix tests on PR #456"
        with (
            patch("orchestration.task_dispatcher.shutil.which", return_value="/usr/bin/claude"),
            patch("orchestration.task_dispatcher.subprocess.run") as mock_run,
            patch("orchestration.task_dispatcher.logger") as mock_logger,
        ):
            def run_side_effect(cmd, **kwargs):
                if "pr" in cmd and "view" in cmd:
                    return MagicMock(returncode=1, stdout="", stderr="not found")
                return MagicMock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            agents = self.dispatcher.analyze_task_and_create_agents(task, pr_update_mode=True, wrap_prompt=True)

        # Verify logger.debug was called with gh_pr_view_nonzero_exit event
        debug_calls = [
            call for call in mock_logger.debug.call_args_list
            if call[0][0] == "gh_pr_view_nonzero_exit"
        ]
        self.assertEqual(len(debug_calls), 1, "Expected exactly one gh_pr_view_nonzero_exit log")
        extra = debug_calls[0][1].get("extra", {})
        self.assertEqual(extra["pr_number"], "456")
        self.assertEqual(extra["returncode"], 1)
        self.assertEqual(extra["stderr"], "not found")


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
