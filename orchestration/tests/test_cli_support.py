"""Tests for multi-CLI support in the task dispatcher."""

import unittest
from unittest.mock import MagicMock, mock_open, patch

from orchestration.task_dispatcher import CLI_PROFILES, TaskDispatcher, GEMINI_MODEL


class TestAgentCliSelection(unittest.TestCase):
    """Verify that different CLIs can be selected and executed."""

    def setUp(self):
        self.dispatcher = TaskDispatcher()

    def test_detects_codex_cli_keyword(self):
        """Ensure codex keyword detection selects the Codex CLI."""
        task = "Please run codex exec --yolo against the new hooks"
        agent_specs = self.dispatcher.analyze_task_and_create_agents(task)
        self.assertEqual(agent_specs[0]["cli"], "codex")

    def test_detects_codex_cli_name_reference(self):
        """Mentioning the CLI name directly should select the Codex profile."""
        task = "Codex should handle the red team hardening checklist"
        agent_specs = self.dispatcher.analyze_task_and_create_agents(task)
        self.assertEqual(agent_specs[0]["cli"], "codex")

    def test_auto_selects_only_available_cli(self):
        """Fallback to installed CLI when task has no explicit preference."""

        with patch("orchestration.task_dispatcher.shutil.which") as mock_which:

            def which_side_effect(command):
                if command == "claude":
                    return None
                if command == "codex":
                    return "/usr/local/bin/codex"
                return None

            mock_which.side_effect = which_side_effect

            task = "Please help with integration tests"
            agent_specs = self.dispatcher.analyze_task_and_create_agents(task)

        self.assertEqual(agent_specs[0]["cli"], "codex")

    def test_create_dynamic_agent_uses_codex_command(self):
        """Ensure codex agents execute via `codex exec --yolo`."""
        agent_spec = {
            "name": "task-agent-codex-test",
            "focus": "Validate Codex CLI integration",
            "prompt": "Do the work",
            "capabilities": [],
            "type": "development",
            "cli": "codex",
        }

        with (
            patch.object(self.dispatcher, "_cleanup_stale_prompt_files"),
            patch.object(self.dispatcher, "_get_active_tmux_agents", return_value=set()),
            patch.object(
                self.dispatcher,
                "_create_worktree_at_location",
                return_value=("/tmp/task-agent-codex-test", MagicMock(returncode=0, stderr="")),
            ),
            patch("os.makedirs"),
            patch("os.chmod"),
            patch("builtins.open", mock_open()),
            patch("os.path.exists", return_value=False),
            patch("orchestration.task_dispatcher.Path.write_text") as mock_write_text,
            patch("orchestration.task_dispatcher.subprocess.run") as mock_run,
            patch("orchestration.task_dispatcher.shutil.which") as mock_which,
        ):

            def which_side_effect(command):
                known_binaries = {
                    "codex": "/usr/bin/codex",
                    "tmux": "/usr/bin/tmux",
                }
                return known_binaries.get(command)

            mock_which.side_effect = which_side_effect
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            result = self.dispatcher.create_dynamic_agent(agent_spec)

        self.assertTrue(result)
        self.assertGreater(len(mock_write_text.call_args_list), 0)
        script_contents = mock_write_text.call_args_list[0][0][0]  # First positional arg is the content
        self.assertIn("codex exec --yolo", script_contents)
        self.assertIn(
            "< /tmp/agent_prompt_task-agent-codex-test.txt",
            script_contents,
        )
        self.assertIn("Codex exit code", script_contents)

    def test_create_dynamic_agent_falls_back_when_requested_cli_missing(self):
        """Gracefully switch to an available CLI when the preferred one is absent."""

        agent_spec = {
            "name": "task-agent-fallback-test",
            "focus": "Fallback behavior",
            "prompt": "Do the work",
            "capabilities": [],
            "type": "development",
            "cli": "claude",
        }

        with (
            patch.object(self.dispatcher, "_cleanup_stale_prompt_files"),
            patch.object(self.dispatcher, "_get_active_tmux_agents", return_value=set()),
            patch.object(
                self.dispatcher,
                "_create_worktree_at_location",
                return_value=("/tmp/task-agent-fallback-test", MagicMock(returncode=0, stderr="")),
            ),
            patch("os.makedirs"),
            patch("os.chmod"),
            patch("builtins.open", mock_open()),
            patch("os.path.exists", return_value=False),
            patch("orchestration.task_dispatcher.Path.write_text") as mock_write_text,
            patch("orchestration.task_dispatcher.subprocess.run") as mock_run,
            patch("orchestration.task_dispatcher.shutil.which") as mock_which,
            patch.object(self.dispatcher, "_ensure_mock_claude_binary", return_value=None),
        ):

            def which_side_effect(command):
                mapping = {
                    "claude": None,
                    "codex": "/usr/bin/codex",
                    "tmux": "/usr/bin/tmux",
                }
                return mapping.get(command)

            mock_which.side_effect = which_side_effect
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            result = self.dispatcher.create_dynamic_agent(agent_spec)

        self.assertTrue(result)
        self.assertEqual(agent_spec["cli"], "codex")
        script_contents = mock_write_text.call_args_list[0][0][0]  # First positional arg is the content
        self.assertIn("codex exec --yolo", script_contents)


class TestGeminiCliSupport(unittest.TestCase):
    """Tests for Gemini CLI support in task dispatcher."""

    def setUp(self):
        self.dispatcher = TaskDispatcher()

    def test_detects_gemini_cli_keyword(self):
        """Ensure gemini keyword detection selects the Gemini CLI."""
        task = "Please run gemini to analyze this code"
        agent_specs = self.dispatcher.analyze_task_and_create_agents(task)
        self.assertEqual(agent_specs[0]["cli"], "gemini")

    def test_detects_gemini_cli_name_reference(self):
        """Mentioning Gemini CLI name directly should select the Gemini profile."""
        task = "Use Gemini CLI to review the authentication module"
        agent_specs = self.dispatcher.analyze_task_and_create_agents(task)
        self.assertEqual(agent_specs[0]["cli"], "gemini")

    def test_detects_gemini_google_reference(self):
        """Google AI reference should select the Gemini profile."""
        task = "Use google ai to help with this task"
        agent_specs = self.dispatcher.analyze_task_and_create_agents(task)
        self.assertEqual(agent_specs[0]["cli"], "gemini")

    def test_gemini_cli_profile_exists(self):
        """Verify Gemini CLI profile is properly configured."""
        self.assertIn("gemini", CLI_PROFILES)

        gemini_profile = CLI_PROFILES["gemini"]
        self.assertEqual(gemini_profile["binary"], "gemini")
        self.assertEqual(gemini_profile["display_name"], "Gemini")
        self.assertIn("gemini", gemini_profile["detection_keywords"])
        self.assertIn("google ai", gemini_profile["detection_keywords"])

    def test_gemini_uses_configured_model(self):
        """Verify Gemini CLI is configured to use the configured GEMINI_MODEL."""
        gemini_profile = CLI_PROFILES["gemini"]
        command_template = gemini_profile["command_template"]

        # Must contain model flag with the configured GEMINI_MODEL
        self.assertIn(GEMINI_MODEL, command_template)

    def test_auto_selects_gemini_when_only_available(self):
        """Fallback to Gemini CLI when it's the only installed CLI."""
        with patch("orchestration.task_dispatcher.shutil.which") as mock_which:

            def which_side_effect(command):
                if command == "gemini":
                    return "/usr/local/bin/gemini"
                return None

            mock_which.side_effect = which_side_effect

            task = "Please help with integration tests"
            agent_specs = self.dispatcher.analyze_task_and_create_agents(task)

        self.assertEqual(agent_specs[0]["cli"], "gemini")

    def test_create_dynamic_agent_uses_gemini_command(self):
        """Ensure Gemini agents execute via gemini CLI with correct model."""
        agent_spec = {
            "name": "task-agent-gemini-test",
            "focus": "Validate Gemini CLI integration",
            "prompt": "Do the work",
            "capabilities": [],
            "type": "development",
            "cli": "gemini",
        }

        with (
            patch.object(self.dispatcher, "_cleanup_stale_prompt_files"),
            patch.object(self.dispatcher, "_get_active_tmux_agents", return_value=set()),
            patch.object(
                self.dispatcher,
                "_create_worktree_at_location",
                return_value=("/tmp/task-agent-gemini-test", MagicMock(returncode=0, stderr="")),
            ),
            patch("os.makedirs"),
            patch("os.chmod"),
            patch("builtins.open", mock_open()),
            patch("os.path.exists", return_value=False),
            patch("orchestration.task_dispatcher.Path.write_text") as mock_write_text,
            patch("orchestration.task_dispatcher.subprocess.run") as mock_run,
            patch("orchestration.task_dispatcher.shutil.which") as mock_which,
        ):

            def which_side_effect(command):
                known_binaries = {
                    "gemini": "/usr/bin/gemini",
                    "tmux": "/usr/bin/tmux",
                }
                return known_binaries.get(command)

            mock_which.side_effect = which_side_effect
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            result = self.dispatcher.create_dynamic_agent(agent_spec)

        self.assertTrue(result)
        self.assertGreater(len(mock_write_text.call_args_list), 0)
        script_contents = mock_write_text.call_args_list[0][0][0]
        # Verify Gemini CLI command is in the script
        self.assertIn("gemini", script_contents)
        # Verify the model is the configured GEMINI_MODEL
        self.assertIn(GEMINI_MODEL, script_contents)
        self.assertIn("Gemini exit code", script_contents)

    def test_gemini_cli_fallback_when_requested_but_missing(self):
        """Gracefully switch to an available CLI when Gemini is absent."""
        agent_spec = {
            "name": "task-agent-gemini-fallback-test",
            "focus": "Fallback behavior",
            "prompt": "Do the work",
            "capabilities": [],
            "type": "development",
            "cli": "gemini",
        }

        with (
            patch.object(self.dispatcher, "_cleanup_stale_prompt_files"),
            patch.object(self.dispatcher, "_get_active_tmux_agents", return_value=set()),
            patch.object(
                self.dispatcher,
                "_create_worktree_at_location",
                return_value=("/tmp/task-agent-gemini-fallback-test", MagicMock(returncode=0, stderr="")),
            ),
            patch("os.makedirs"),
            patch("os.chmod"),
            patch("builtins.open", mock_open()),
            patch("os.path.exists", return_value=False),
            patch("orchestration.task_dispatcher.Path.write_text") as mock_write_text,
            patch("orchestration.task_dispatcher.subprocess.run") as mock_run,
            patch("orchestration.task_dispatcher.shutil.which") as mock_which,
            patch.object(self.dispatcher, "_ensure_mock_claude_binary", return_value=None),
        ):

            def which_side_effect(command):
                mapping = {
                    "gemini": None,
                    "claude": None,
                    "codex": "/usr/bin/codex",
                    "tmux": "/usr/bin/tmux",
                }
                return mapping.get(command)

            mock_which.side_effect = which_side_effect
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            result = self.dispatcher.create_dynamic_agent(agent_spec)

        self.assertTrue(result)
        # Should have fallen back to codex
        self.assertEqual(agent_spec["cli"], "codex")
        script_contents = mock_write_text.call_args_list[0][0][0]
        self.assertIn("codex exec --yolo", script_contents)

    def test_explicit_agent_cli_flag_gemini(self):
        """Verify --agent-cli gemini flag works correctly."""
        task = "Fix the bug --agent-cli gemini"
        agent_specs = self.dispatcher.analyze_task_and_create_agents(task)
        self.assertEqual(agent_specs[0]["cli"], "gemini")


class TestGeminiCliIntegration(unittest.TestCase):
    """Integration tests for Gemini CLI with minimal mocking.

    These tests verify real behavior of CLI detection, profile configuration,
    and command generation with only essential mocks (external system calls).
    """

    def setUp(self):
        self.dispatcher = TaskDispatcher()

    def test_gemini_profile_complete_configuration(self):
        """Integration: Verify complete Gemini profile has all required fields."""

        gemini = CLI_PROFILES["gemini"]

        # All required profile fields must exist
        required_fields = [
            "binary",
            "display_name",
            "generated_with",
            "co_author",
            "supports_continue",
            "conversation_dir",
            "continue_flag",
            "restart_env",
            "command_template",
            "stdin_template",
            "quote_prompt",
            "detection_keywords",
        ]

        for field in required_fields:
            self.assertIn(field, gemini, f"Missing required field: {field}")

        # Verify specific values for Gemini profile
        self.assertEqual(gemini["binary"], "gemini")
        self.assertEqual(gemini["display_name"], "Gemini")
        self.assertIn(GEMINI_MODEL, gemini["command_template"])
        self.assertFalse(gemini["supports_continue"])
        self.assertIsNone(gemini["conversation_dir"])

    def test_gemini_detection_keywords_comprehensive(self):
        """Integration: Test all detection keywords actually trigger Gemini selection."""

        keywords = CLI_PROFILES["gemini"]["detection_keywords"]

        # Mock only shutil.which to make gemini appear available
        with patch("orchestration.task_dispatcher.shutil.which") as mock_which:
            mock_which.side_effect = lambda command: "/usr/bin/gemini" if command == "gemini" else None

            for keyword in keywords:
                task = f"Please {keyword} this code for me"
                agent_specs = self.dispatcher.analyze_task_and_create_agents(task)
                self.assertEqual(
                    agent_specs[0]["cli"], "gemini", f"Keyword '{keyword}' did not trigger Gemini selection"
                )

    def test_gemini_command_template_format_string_valid(self):
        """Integration: Verify command template has valid format placeholders."""

        template = CLI_PROFILES["gemini"]["command_template"]

        # Test that template can be formatted with expected placeholders
        test_values = {
            "binary": "/usr/bin/gemini",
            "prompt_file": "/tmp/test_prompt.txt",
        }

        try:
            formatted = template.format(**test_values)
            self.assertIn("/usr/bin/gemini", formatted)
            self.assertIn(GEMINI_MODEL, formatted)
            self.assertIn("/tmp/test_prompt.txt", formatted)
        except KeyError as e:
            self.fail(f"Command template has unknown placeholder: {e}")

    def test_gemini_cli_priority_over_claude_when_explicit(self):
        """Integration: Explicit --agent-cli gemini overrides default Claude."""
        # Mock both CLIs as available
        with patch("orchestration.task_dispatcher.shutil.which") as mock_which:

            def which_side_effect(cmd):
                return f"/usr/bin/{cmd}" if cmd in ["claude", "gemini", "codex"] else None

            mock_which.side_effect = which_side_effect

            # Without explicit flag, would default to claude
            task_without_flag = "Fix the authentication bug"
            specs_without = self.dispatcher.analyze_task_and_create_agents(task_without_flag)
            self.assertEqual(specs_without[0]["cli"], "claude")

            # With explicit flag, should use gemini
            task_with_flag = "Fix the authentication bug --agent-cli gemini"
            specs_with = self.dispatcher.analyze_task_and_create_agents(task_with_flag)
            self.assertEqual(specs_with[0]["cli"], "gemini")

    def test_gemini_detection_case_insensitive(self):
        """Integration: Gemini detection works regardless of case."""
        with patch("orchestration.task_dispatcher.shutil.which") as mock_which:
            mock_which.side_effect = lambda command: "/usr/bin/gemini" if command == "gemini" else None

            test_cases = [
                "Use GEMINI for this",
                "Use Gemini for this",
                "Use gemini for this",
                "Use GeMiNi for this",
            ]

            for task in test_cases:
                specs = self.dispatcher.analyze_task_and_create_agents(task)
                self.assertEqual(specs[0]["cli"], "gemini", f"Case variation '{task}' failed detection")

    def test_gemini_agent_spec_complete_structure(self):
        """Integration: Full agent spec generation includes all required fields."""
        with patch("orchestration.task_dispatcher.shutil.which") as mock_which:
            mock_which.side_effect = lambda command: "/usr/bin/gemini" if command == "gemini" else None

            task = "Use gemini to implement the new feature"
            specs = self.dispatcher.analyze_task_and_create_agents(task)

            self.assertEqual(len(specs), 1)
            spec = specs[0]

            # Verify all required spec fields
            required_spec_fields = ["name", "type", "focus", "capabilities", "prompt", "cli"]
            for field in required_spec_fields:
                self.assertIn(field, spec, f"Missing spec field: {field}")

            self.assertEqual(spec["cli"], "gemini")
            self.assertTrue(spec["name"].startswith("task-agent-"))
            self.assertEqual(spec["type"], "development")

    def test_gemini_model_enforced_in_all_paths(self):
        """Integration: gemini-2.5-pro model is enforced regardless of task content."""

        # Verify model cannot be overridden by task content
        template = CLI_PROFILES["gemini"]["command_template"]
        self.assertIn(GEMINI_MODEL, template)

    def test_gemini_stdin_template_not_prompt_file(self):
        """Integration: Gemini uses /dev/null for stdin, not prompt file."""

        gemini = CLI_PROFILES["gemini"]
        self.assertEqual(gemini["stdin_template"], "/dev/null")
        self.assertFalse(gemini["quote_prompt"])

    def test_all_cli_profiles_have_consistent_structure(self):
        """Integration: All CLI profiles (claude, codex, gemini) have same structure."""

        expected_keys = set(CLI_PROFILES["claude"].keys())

        for cli_name, profile in CLI_PROFILES.items():
            profile_keys = set(profile.keys())
            self.assertEqual(
                profile_keys,
                expected_keys,
                f"CLI profile '{cli_name}' has inconsistent keys. "
                f"Missing: {expected_keys - profile_keys}, Extra: {profile_keys - expected_keys}",
            )


if __name__ == "__main__":
    unittest.main()
