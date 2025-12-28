"""Tests for multi-CLI support in the task dispatcher."""

import shlex
import unittest
from unittest.mock import MagicMock, mock_open, patch

from orchestration.task_dispatcher import (
    CLI_PROFILES,
    CURSOR_MODEL,
    GEMINI_MODEL,
    TaskDispatcher,
)


class TestAgentCliSelection(unittest.TestCase):
    """Verify that different CLIs can be selected and executed."""

    def setUp(self):
        self.dispatcher = TaskDispatcher()

    def test_respects_forced_cli_codex(self):
        """Forced CLI selection should override detection/keywords."""
        task = "Please run codex exec --yolo against the new hooks"
        agent_specs = self.dispatcher.analyze_task_and_create_agents(task, forced_cli="codex")
        self.assertEqual(agent_specs[0]["cli"], "codex")

    def test_respects_forced_cli_codex_name_reference(self):
        """Forced CLI selection works regardless of task wording."""
        task = "Codex should handle the red team hardening checklist"
        agent_specs = self.dispatcher.analyze_task_and_create_agents(task, forced_cli="codex")
        self.assertEqual(agent_specs[0]["cli"], "codex")

    def test_keywords_select_cli_when_not_forced(self):
        """Keywords should select CLI when no explicit override is provided."""
        with patch("orchestration.task_dispatcher.shutil.which") as mock_which:
            mock_which.side_effect = (
                lambda command: "/usr/bin/codex"
                if command == "codex"
                else "/usr/bin/claude"
                if command == "claude"
                else None
            )

            task = "Please run codex exec against the hooks"
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

    def test_agent_cli_chain_parses_from_flag(self):
        """Comma-separated --agent-cli should produce a deterministic CLI chain."""
        task = "Please help with integration tests --agent-cli=gemini,codex"
        agent_specs = self.dispatcher.analyze_task_and_create_agents(task)
        self.assertEqual(agent_specs[0]["cli"], "gemini")
        self.assertEqual(agent_specs[0]["cli_chain"], ["gemini", "codex"])

    def test_invalid_forced_cli_raises_value_error(self):
        """Invalid forced_cli values should raise a clear error."""
        with self.assertRaises(ValueError):
            self.dispatcher.analyze_task_and_create_agents("Please help", forced_cli="invalid")

    def test_invalid_agent_cli_flag_raises_value_error(self):
        """Invalid --agent-cli values should raise (do not silently fall back)."""
        with self.assertRaises(ValueError):
            self.dispatcher.analyze_task_and_create_agents("Please help --agent-cli=invalid")

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

    def test_create_dynamic_agent_embeds_cli_chain(self):
        """When cli_chain is provided, the generated runner should include both attempts in order."""
        agent_spec = {
            "name": "task-agent-cli-chain-test",
            "focus": "Validate CLI chain",
            "prompt": "Do the work",
            "capabilities": [],
            "type": "development",
            "cli": "gemini",
            "cli_chain": ["gemini", "codex"],
        }

        with (
            patch.object(self.dispatcher, "_cleanup_stale_prompt_files"),
            patch.object(self.dispatcher, "_get_active_tmux_agents", return_value=set()),
            patch.object(
                self.dispatcher,
                "_create_worktree_at_location",
                return_value=("/tmp/task-agent-cli-chain-test", MagicMock(returncode=0, stderr="")),
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
                    "codex": "/usr/bin/codex",
                    "tmux": "/usr/bin/tmux",
                }
                return known_binaries.get(command)

            mock_which.side_effect = which_side_effect
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            result = self.dispatcher.create_dynamic_agent(agent_spec)

        self.assertTrue(result)
        script_contents = mock_write_text.call_args_list[0][0][0]  # First positional arg is the content
        self.assertIn("CLI chain: gemini,codex", script_contents)
        self.assertIn("Gemini exit code", script_contents)
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
            patch.object(self.dispatcher, "_ensure_mock_cli_binary", return_value=None),
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

    def test_respects_forced_cli_gemini_keyword(self):
        """Forced CLI selection should override detection/keywords."""
        task = "Please run gemini to analyze this code"
        agent_specs = self.dispatcher.analyze_task_and_create_agents(task, forced_cli="gemini")
        self.assertEqual(agent_specs[0]["cli"], "gemini")

    def test_respects_forced_cli_gemini_name_reference(self):
        """Forced selection works regardless of wording."""
        task = "Use Gemini CLI to review the authentication module"
        agent_specs = self.dispatcher.analyze_task_and_create_agents(task, forced_cli="gemini")
        self.assertEqual(agent_specs[0]["cli"], "gemini")

    def test_respects_forced_cli_gemini_google_reference(self):
        """Forced selection works even with generic Google reference."""
        task = "Use google ai to help with this task"
        agent_specs = self.dispatcher.analyze_task_and_create_agents(task, forced_cli="gemini")
        self.assertEqual(agent_specs[0]["cli"], "gemini")

    def test_gemini_keywords_select_cli_when_not_forced(self):
        """Gemini keywords should select CLI when not overridden."""
        with patch("orchestration.task_dispatcher.shutil.which") as mock_which:
            mock_which.side_effect = (
                lambda command: "/usr/bin/gemini"
                if command == "gemini"
                else "/usr/bin/claude"
                if command == "claude"
                else None
            )

            task = "Please run gemini to analyze this code"
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
            patch.object(self.dispatcher, "_ensure_mock_cli_binary", return_value=None),
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

    def test_gemini_forced_cli_overrides_keywords(self):
        """Forced CLI should return gemini regardless of keywords."""

        keywords = CLI_PROFILES["gemini"]["detection_keywords"]
        for keyword in keywords:
            task = f"Please {keyword} this code for me"
            agent_specs = self.dispatcher.analyze_task_and_create_agents(task, forced_cli="gemini")
            self.assertEqual(agent_specs[0]["cli"], "gemini")

    def test_gemini_command_template_format_string_valid(self):
        """Integration: Verify command template has valid format placeholders."""

        template = CLI_PROFILES["gemini"]["command_template"]

        # Test that template can be formatted with expected placeholders
        # NOTE: prompt_file is now passed via stdin_template, not command_template
        test_values = {
            "binary": "/usr/bin/gemini",
        }

        try:
            formatted = template.format(**test_values)
            self.assertIn("/usr/bin/gemini", formatted)
            self.assertIn(GEMINI_MODEL, formatted)
            # Prompt comes via stdin, not command line
            self.assertIn("--yolo", formatted)
        except KeyError as e:
            self.fail(f"Command template has unknown placeholder: {e}")

    def test_claude_cli_priority_over_gemini_when_explicit(self):
        """Integration: Explicit --agent-cli claude overrides default Gemini."""
        # Mock both CLIs as available
        with patch("orchestration.task_dispatcher.shutil.which") as mock_which:

            def which_side_effect(cmd):
                return f"/usr/bin/{cmd}" if cmd in ["claude", "gemini", "codex"] else None

            mock_which.side_effect = which_side_effect

            # Without explicit flag, now defaults to gemini
            task_without_flag = "Fix the authentication bug"
            specs_without = self.dispatcher.analyze_task_and_create_agents(task_without_flag)
            self.assertEqual(specs_without[0]["cli"], "gemini")

            # With explicit flag, should use claude
            task_with_flag = "Fix the authentication bug --agent-cli claude"
            specs_with = self.dispatcher.analyze_task_and_create_agents(task_with_flag)
            self.assertEqual(specs_with[0]["cli"], "claude")

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

    def test_gemini_stdin_template_uses_prompt_file(self):
        """Integration: Gemini receives prompt via stdin (not deprecated -p flag)."""

        gemini = CLI_PROFILES["gemini"]
        # Prompt must come via stdin since -p flag is deprecated and only appends to stdin
        self.assertEqual(gemini["stdin_template"], "{prompt_file}")
        self.assertFalse(gemini["quote_prompt"])

    def test_all_cli_profiles_have_consistent_structure(self):
        """Integration: All CLI profiles (claude, codex, gemini, cursor) have same structure."""

        expected_keys = set(CLI_PROFILES["claude"].keys())

        for cli_name, profile in CLI_PROFILES.items():
            profile_keys = set(profile.keys())
            self.assertEqual(
                profile_keys,
                expected_keys,
                f"CLI profile '{cli_name}' has inconsistent keys. "
                f"Missing: {expected_keys - profile_keys}, Extra: {profile_keys - expected_keys}",
            )

    def test_all_env_unset_values_are_valid_posix_identifiers(self):
        """Integration: All env_unset values must be valid POSIX environment variable names."""
        import re

        for cli_name, profile in CLI_PROFILES.items():
            env_unset = profile.get("env_unset", [])
            self.assertIsInstance(env_unset, list, f"{cli_name} env_unset should be a list")
            for var in env_unset:
                self.assertIsInstance(var, str, f"{cli_name} env_unset values should be strings")
                self.assertTrue(
                    re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", var),
                    f"{cli_name} env_unset contains invalid variable name: {var!r}",
                )

    def test_env_unset_expected_values(self):
        """Integration: Verify expected env_unset values for each CLI profile."""
        self.assertEqual(CLI_PROFILES["claude"]["env_unset"], ["ANTHROPIC_API_KEY"])
        self.assertEqual(CLI_PROFILES["codex"]["env_unset"], ["OPENAI_API_KEY"])
        self.assertEqual(CLI_PROFILES["gemini"]["env_unset"], ["GEMINI_API_KEY"])
        self.assertEqual(CLI_PROFILES["cursor"]["env_unset"], [])


class TestCursorCliIntegration(unittest.TestCase):
    """Tests for Cursor Agent CLI integration."""

    def setUp(self):
        self.dispatcher = TaskDispatcher()

    def test_cursor_profile_exists(self):
        """Cursor CLI profile should be registered in CLI_PROFILES."""
        self.assertIn("cursor", CLI_PROFILES)

    def test_cursor_profile_structure(self):
        """Cursor profile should have all required fields."""
        cursor = CLI_PROFILES["cursor"]
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
            self.assertIn(field, cursor, f"Missing field: {field}")

    def test_cursor_binary_name(self):
        """Cursor profile should use cursor-agent binary."""
        cursor = CLI_PROFILES["cursor"]
        self.assertEqual(cursor["binary"], "cursor-agent")

    def test_cursor_command_template(self):
        """Cursor command template should include -f flag, configured model and output format."""
        cursor = CLI_PROFILES["cursor"]
        template = cursor["command_template"]
        tokens = shlex.split(template)
        self.assertIn("-f", tokens, "Missing -f flag for non-interactive execution")
        self.assertIn(f"--model {CURSOR_MODEL}", template)
        self.assertIn("--output-format text", template)
        self.assertIn("-p @{prompt_file}", template)

    def test_cursor_detection_keywords(self):
        """Cursor should be detected by relevant keywords (not model names)."""
        cursor = CLI_PROFILES["cursor"]
        # Note: "grok" removed - model names should not trigger CLI selection
        # since the model is configurable via CURSOR_MODEL env var
        expected_keywords = ["cursor", "cursor-agent"]
        for keyword in expected_keywords:
            self.assertIn(keyword, cursor["detection_keywords"])
        # Ensure model name is NOT in detection keywords (decoupled concerns)
        self.assertNotIn("grok", cursor["detection_keywords"])

    def test_cursor_keyword_detection(self):
        """Task with cursor keywords should select cursor CLI."""
        with patch("orchestration.task_dispatcher.shutil.which") as mock_which:
            mock_which.side_effect = lambda cmd: f"/usr/bin/{cmd}" if cmd in ["claude", "cursor-agent"] else None

            task = "Use cursor to analyze the latest trends"
            agent_specs = self.dispatcher.analyze_task_and_create_agents(task)

        self.assertEqual(agent_specs[0]["cli"], "cursor")

    def test_cursor_forced_cli(self):
        """Forced CLI selection should work for cursor."""
        task = "Analyze the codebase for fresh insights"
        agent_specs = self.dispatcher.analyze_task_and_create_agents(task, forced_cli="cursor")
        self.assertEqual(agent_specs[0]["cli"], "cursor")

    def test_cursor_stdin_template(self):
        """Cursor uses /dev/null for stdin (prompt passed via -p flag)."""
        cursor = CLI_PROFILES["cursor"]
        self.assertEqual(cursor["stdin_template"], "/dev/null")
        self.assertFalse(cursor["quote_prompt"])

    def test_cursor_does_not_support_continue(self):
        """Cursor should not support conversation continuation."""
        cursor = CLI_PROFILES["cursor"]
        self.assertFalse(cursor["supports_continue"])
        self.assertIsNone(cursor["conversation_dir"])


if __name__ == "__main__":
    unittest.main()
