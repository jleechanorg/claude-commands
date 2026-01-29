"""Tests for multi-CLI support in the task dispatcher."""

import logging
import shlex
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from orchestration.cli_validation import ValidationResult
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
            patch.object(self.dispatcher, "_print_tmp_subdirectories"),
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
            patch.object(self.dispatcher, "_validate_cli_availability", return_value=True) as mock_validate,
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
            patch.object(self.dispatcher, "_print_tmp_subdirectories"),
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
            patch.object(self.dispatcher, "_validate_cli_availability", return_value=True) as mock_validate,
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

    def test_create_dynamic_agent_fails_when_requested_cli_missing(self):
        """Agent creation should fail when the requested CLI is absent (no automatic fallback)."""

        agent_spec = {
            "name": "task-agent-fallback-test",
            "focus": "No fallback behavior",
            "prompt": "Do the work",
            "capabilities": [],
            "type": "development",
            "cli": "claude",
        }

        with (
            patch.object(self.dispatcher, "_cleanup_stale_prompt_files"),
            patch.object(self.dispatcher, "_get_active_tmux_agents", return_value=set()),
            patch.object(self.dispatcher, "_print_tmp_subdirectories"),
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
            patch.object(self.dispatcher, "_validate_cli_availability", return_value=False) as mock_validate,
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

        # Should fail because claude is missing and no fallback occurs
        self.assertFalse(result, "Agent creation should fail when requested CLI is missing")
        # CLI should remain unchanged (no fallback)
        self.assertEqual(agent_spec["cli"], "claude")


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
        """Verify Gemini CLI command template uses {model} placeholder for dynamic model selection."""
        gemini_profile = CLI_PROFILES["gemini"]
        command_template = gemini_profile["command_template"]

        # Template should use {model} placeholder, not hardcoded GEMINI_MODEL
        # The actual model (GEMINI_MODEL or user-specified) is set at runtime
        self.assertIn("{model}", command_template)
        self.assertNotIn("GEMINI_MODEL", command_template)
        
        # Verify template can be formatted with GEMINI_MODEL
        formatted = command_template.format(binary="/usr/bin/gemini", model=GEMINI_MODEL)
        self.assertIn(GEMINI_MODEL, formatted)

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
            patch.object(self.dispatcher, "_print_tmp_subdirectories"),
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
            patch.object(self.dispatcher, "_validate_cli_availability", return_value=True) as mock_validate,
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

    def test_gemini_cli_fails_when_requested_but_missing(self):
        """Agent creation should fail when Gemini is absent (no automatic fallback)."""
        agent_spec = {
            "name": "task-agent-gemini-fallback-test",
            "focus": "No fallback behavior",
            "prompt": "Do the work",
            "capabilities": [],
            "type": "development",
            "cli": "gemini",
        }

        with (
            patch.object(self.dispatcher, "_cleanup_stale_prompt_files"),
            patch.object(self.dispatcher, "_get_active_tmux_agents", return_value=set()),
            patch.object(self.dispatcher, "_print_tmp_subdirectories"),
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
            patch.object(self.dispatcher, "_validate_cli_availability", return_value=False) as mock_validate,
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

        # Should fail because gemini is missing and no fallback occurs
        self.assertFalse(result, "Agent creation should fail when requested CLI is missing")
        # CLI should remain unchanged (no fallback)
        self.assertEqual(agent_spec["cli"], "gemini")

    def test_explicit_agent_cli_flag_gemini(self):
        """Verify --agent-cli gemini flag works correctly."""
        task = "Fix the bug --agent-cli gemini"
        agent_specs = self.dispatcher.analyze_task_and_create_agents(task)
        self.assertEqual(agent_specs[0]["cli"], "gemini")

    def test_preflight_validation_fallback_to_codex_on_quota(self):
        """Pre-flight validation should fallback to Codex when Gemini quota exhausted."""
        agent_spec = {
            "name": "task-agent-preflight-test",
            "focus": "Test pre-flight validation fallback",
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
                return_value=("/tmp/task-agent-preflight-test", MagicMock(returncode=0, stderr="")),
            ),
            patch("os.makedirs"),
            patch("os.chmod"),
            patch("builtins.open", mock_open()),
            patch("os.path.exists", return_value=False),
            patch("orchestration.task_dispatcher.Path.write_text") as mock_write_text,
            patch("orchestration.task_dispatcher.subprocess.run") as mock_run,
            patch("orchestration.task_dispatcher.shutil.which") as mock_which,
            patch.object(self.dispatcher, "_validate_cli_availability") as mock_validate,
            patch.object(self.dispatcher, "_print_tmp_subdirectories") as mock_show_tmp,
        ):

            def which_side_effect(command):
                known_binaries = {
                    "gemini": "/usr/bin/gemini",
                    "codex": "/usr/bin/codex",
                    "tmux": "/usr/bin/tmux",
                }
                return known_binaries.get(command)

            mock_which.side_effect = which_side_effect

            # Mock validation: Gemini fails, Codex succeeds
            def validate_side_effect(cli_name, cli_path, agent_name, model=None):
                if cli_name == "gemini":
                    return False  # Quota exhausted
                elif cli_name == "codex":
                    return True  # Available
                return False

            mock_validate.side_effect = validate_side_effect
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            result = self.dispatcher.create_dynamic_agent(agent_spec)

        self.assertTrue(result)
        mock_show_tmp.assert_called()
        # Agent should have fallen back to Codex
        self.assertEqual(agent_spec["cli"], "codex")
        script_contents = mock_write_text.call_args_list[0][0][0]
        self.assertIn("codex exec --yolo", script_contents)


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
        # Command template uses {model} placeholder for dynamic model selection
        self.assertIn("{model}", gemini["command_template"])
        # Verify template can be formatted with GEMINI_MODEL (the default)
        formatted = gemini["command_template"].format(binary="/usr/bin/gemini", model=GEMINI_MODEL)
        self.assertIn(GEMINI_MODEL, formatted)
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
        # NOTE: model is now a required placeholder (dynamic model selection)
        test_values = {
            "binary": "/usr/bin/gemini",
            "model": GEMINI_MODEL,  # Required placeholder for dynamic model selection
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
        """Integration: Model is set dynamically via {model} placeholder, defaults to GEMINI_MODEL."""

        # Verify template uses {model} placeholder for dynamic model selection
        template = CLI_PROFILES["gemini"]["command_template"]
        self.assertIn("{model}", template)
        # Verify template can be formatted with GEMINI_MODEL (the default)
        formatted = template.format(binary="/usr/bin/gemini", model=GEMINI_MODEL)
        self.assertIn(GEMINI_MODEL, formatted)

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


def test_print_tmp_subdirectories_lists_dirs_only(caplog):
    dispatcher = TaskDispatcher()
    with tempfile.TemporaryDirectory() as temp_root:
        Path(temp_root, "orchestration_results").mkdir()
        Path(temp_root, "worldarchitectai").mkdir()
        Path(temp_root, "not_a_dir.txt").write_text("x", encoding="utf-8")

        with caplog.at_level(logging.INFO, logger="orchestration.task_dispatcher"):
            dispatcher._print_tmp_subdirectories(
                tmp_root=temp_root,
                max_entries=10,
                correlation_id="test-agent",
            )

    assert temp_root in caplog.text
    assert "orchestration_results" in caplog.text
    assert "worldarchitectai" in caplog.text
    assert "not_a_dir.txt" not in caplog.text
    records = [record for record in caplog.records if record.name == "orchestration.task_dispatcher"]
    assert records
    assert all(getattr(record, "correlation_id", None) == "test-agent" for record in records)


class TestCliValidation(unittest.TestCase):
    """Tests for pre-flight CLI validation (_validate_cli_availability)."""

    def setUp(self):
        self.dispatcher = TaskDispatcher()

    def test_gemini_validation_success_with_exit_code_0(self):
        """Gemini validation should succeed when exit code is 0 and output file is created."""
        with patch("orchestration.task_dispatcher.validate_cli_two_phase") as mock_validate:
            mock_validate.return_value = ValidationResult(
                success=True,
                phase="execution",
                message="gemini execution test passed",
                output_file=MagicMock(),
            )
            result = self.dispatcher._validate_cli_availability("gemini", "/usr/bin/gemini", "test-agent")
            self.assertTrue(result)
            mock_validate.assert_called_once()

    def test_gemini_validation_fails_with_quota_error(self):
        """Gemini validation should fail when quota/rate limit is detected."""
        quota_messages = [
            "exhausted your capacity",
            "exhausted your daily quota",
            "rate limit",
            "quota exceeded",
            "resource_exhausted",
        ]
        for quota_msg in quota_messages:
            with patch("orchestration.task_dispatcher.validate_cli_two_phase") as mock_validate:
                mock_validate.return_value = ValidationResult(
                    success=False,
                    phase="execution",
                    message=f"gemini quota/rate limit detected: {quota_msg}",
                )
                result = self.dispatcher._validate_cli_availability("gemini", "/usr/bin/gemini", "test-agent")
                self.assertFalse(result, f"Should fail for quota message: {quota_msg}")

    def test_gemini_validation_fails_with_non_zero_exit_code(self):
        """Gemini validation should fail when exit code is non-zero (unless quota error)."""
        with patch("orchestration.task_dispatcher.validate_cli_two_phase") as mock_validate:
            mock_validate.return_value = ValidationResult(
                success=False,
                phase="execution",
                message="gemini execution test failed (exit code 1)",
            )
            result = self.dispatcher._validate_cli_availability("gemini", "/usr/bin/gemini", "test-agent")
            self.assertFalse(result)

    def test_gemini_validation_timeout_returns_true(self):
        """Gemini validation timeout should return True (allows runtime fallback)."""
        with patch("orchestration.task_dispatcher.validate_cli_two_phase") as mock_validate:
            mock_validate.return_value = ValidationResult(
                success=True,
                phase="execution",
                message="gemini execution test timed out (will try anyway)",
            )
            result = self.dispatcher._validate_cli_availability("gemini", "/usr/bin/gemini", "test-agent")
            self.assertTrue(result)

    def test_gemini_validation_exception_returns_true(self):
        """Gemini validation exception should return True (allows runtime fallback)."""
        with patch("orchestration.task_dispatcher.validate_cli_two_phase") as mock_validate:
            mock_validate.return_value = ValidationResult(
                success=True,
                phase="execution",
                message="gemini execution test error: Network error (will try anyway)",
            )
            result = self.dispatcher._validate_cli_availability("gemini", "/usr/bin/gemini", "test-agent")
            self.assertTrue(result)

    def test_codex_validation_success_with_exit_code_0(self):
        """Codex validation should succeed when exit code is 0 and output file is created."""
        with patch("orchestration.task_dispatcher.validate_cli_two_phase") as mock_validate:
            mock_validate.return_value = ValidationResult(
                success=True,
                phase="execution",
                message="codex execution test passed",
                output_file=MagicMock(),
            )
            result = self.dispatcher._validate_cli_availability("codex", "/usr/bin/codex", "test-agent")
            self.assertTrue(result)

    def test_codex_validation_success_with_help_output(self):
        """Codex validation should succeed when help/version output is recognized."""
        with patch("orchestration.task_dispatcher.validate_cli_two_phase") as mock_validate:
            mock_validate.return_value = ValidationResult(
                success=True,
                phase="execution",
                message="codex execution test passed (help/version detected as fallback)",
            )
            result = self.dispatcher._validate_cli_availability("codex", "/usr/bin/codex", "test-agent")
            self.assertTrue(result)

    def test_codex_validation_success_with_version_output(self):
        """Codex validation should succeed when version output is recognized."""
        with patch("orchestration.task_dispatcher.validate_cli_two_phase") as mock_validate:
            mock_validate.return_value = ValidationResult(
                success=True,
                phase="execution",
                message="codex execution test passed (help/version detected as fallback)",
            )
            result = self.dispatcher._validate_cli_availability("codex", "/usr/bin/codex", "test-agent")
            self.assertTrue(result)

    def test_codex_validation_fails_with_unrecognized_error(self):
        """Codex validation should fail when exit code is non-zero and output is unrecognized."""
        with patch("orchestration.task_dispatcher.validate_cli_two_phase") as mock_validate:
            mock_validate.return_value = ValidationResult(
                success=False,
                phase="execution",
                message="codex execution test failed (exit code 1)",
            )
            result = self.dispatcher._validate_cli_availability("codex", "/usr/bin/codex", "test-agent")
            self.assertFalse(result)

    def test_codex_validation_timeout_returns_true(self):
        """Codex validation timeout should return True (allows runtime fallback)."""
        with patch("orchestration.task_dispatcher.validate_cli_two_phase") as mock_validate:
            mock_validate.return_value = ValidationResult(
                success=True,
                phase="execution",
                message="codex execution test timed out (will try anyway)",
            )
            result = self.dispatcher._validate_cli_availability("codex", "/usr/bin/codex", "test-agent")
            self.assertTrue(result)

    def test_codex_validation_exception_returns_true(self):
        """Codex validation exception should return True (allows runtime fallback)."""
        with patch("orchestration.task_dispatcher.validate_cli_two_phase") as mock_validate:
            mock_validate.return_value = ValidationResult(
                success=True,
                phase="execution",
                message="codex execution test error: Network error (will try anyway)",
            )
            result = self.dispatcher._validate_cli_availability("codex", "/usr/bin/codex", "test-agent")
            self.assertTrue(result)

    def test_claude_validation_success_with_executable(self):
        """Claude validation should succeed when binary is executable and can write output."""
        with (
            patch("orchestration.task_dispatcher.os.access") as mock_access,
            patch("orchestration.task_dispatcher.validate_cli_two_phase") as mock_validate,
        ):
            mock_access.return_value = True
            mock_validate.return_value = ValidationResult(
                success=True,
                phase="execution",
                message="claude execution test passed",
                output_file=MagicMock(),
            )
            result = self.dispatcher._validate_cli_availability("claude", "/usr/bin/claude", "test-agent")
            self.assertTrue(result)

    def test_claude_validation_fails_with_non_executable(self):
        """Claude validation should fail when binary is not executable."""
        with patch("orchestration.task_dispatcher.os.access") as mock_access:
            mock_access.return_value = False
            # Should return False before calling validate_cli_two_phase
            result = self.dispatcher._validate_cli_availability("claude", "/usr/bin/claude", "test-agent")
            self.assertFalse(result)

    def test_cursor_validation_success_with_executable(self):
        """Cursor validation should succeed when binary is executable and can write output."""
        with (
            patch("orchestration.task_dispatcher.os.access") as mock_access,
            patch("orchestration.task_dispatcher.validate_cli_two_phase") as mock_validate,
        ):
            mock_access.return_value = True
            mock_validate.return_value = ValidationResult(
                success=True,
                phase="execution",
                message="cursor execution test passed",
                output_file=MagicMock(),
            )
            result = self.dispatcher._validate_cli_availability("cursor", "/usr/bin/cursor-agent", "test-agent")
            self.assertTrue(result)

    def test_cursor_validation_fails_with_non_executable(self):
        """Cursor validation should fail when binary is not executable."""
        with patch("orchestration.task_dispatcher.os.access") as mock_access:
            mock_access.return_value = False
            # Should return False before calling validate_cli_two_phase
            result = self.dispatcher._validate_cli_availability("cursor", "/usr/bin/cursor-agent", "test-agent")
            self.assertFalse(result)

    def test_unknown_cli_type_returns_true(self):
        """Unknown CLI types should return True with warning (allows runtime fallback)."""
        with patch("builtins.print") as mock_print:
            result = self.dispatcher._validate_cli_availability("unknown-cli", "/usr/bin/unknown", "test-agent")
            self.assertTrue(result)
            # Verify warning was printed
            mock_print.assert_called()
            call_args = str(mock_print.call_args)
            self.assertIn("Unknown CLI type", call_args)
            self.assertIn("test-agent", call_args)

    def test_validation_includes_agent_name_in_logs(self):
        """Validation should include agent_name in all log messages."""
        with patch("builtins.print") as mock_print, patch(
            "orchestration.task_dispatcher.subprocess.run"
        ) as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Error")
            self.dispatcher._validate_cli_availability("gemini", "/usr/bin/gemini", "my-test-agent")
            # Check that agent_name appears in log messages
            calls = [str(call) for call in mock_print.call_args_list]
            agent_name_found = any("my-test-agent" in call for call in calls)
            self.assertTrue(agent_name_found, "agent_name should appear in log messages")

    def test_validation_exception_handling_includes_agent_name(self):
        """Exception handling should include agent_name in log messages."""
        with patch("builtins.print") as mock_print, patch(
            "orchestration.task_dispatcher.subprocess.run"
        ) as mock_run:
            mock_run.side_effect = Exception("Test error")
            result = self.dispatcher._validate_cli_availability("gemini", "/usr/bin/gemini", "error-test-agent")
            self.assertTrue(result)
            # Verify exception log includes agent name
            calls = [str(call) for call in mock_print.call_args_list]
            agent_name_found = any("error-test-agent" in call for call in calls)
            self.assertTrue(agent_name_found, "agent_name should appear in exception log")


class TestAgentCreationWithValidation(unittest.TestCase):
    """Integration tests that verify agent creation actually works with validation."""

    def setUp(self):
        self.dispatcher = TaskDispatcher()

    def test_agent_creation_with_gemini_validation_success(self):
        """Agent creation should succeed when Gemini validation passes."""
        agent_spec = {
            "name": "test-agent-gemini-validation",
            "focus": "Test Gemini validation in agent creation",
            "prompt": "Test prompt",
            "capabilities": [],
            "type": "development",
            "cli": "gemini",
        }

        with (
            patch.object(self.dispatcher, "_cleanup_stale_prompt_files"),
            patch.object(self.dispatcher, "_get_active_tmux_agents", return_value=set()),
            patch.object(self.dispatcher, "_print_tmp_subdirectories"),
            patch.object(
                self.dispatcher,
                "_create_worktree_at_location",
                return_value=("/tmp/test-agent-gemini-validation", MagicMock(returncode=0, stderr="")),
            ),
            patch("os.makedirs"),
            patch("os.chmod"),
            patch("builtins.open", mock_open()),
            patch("os.path.exists", return_value=False),
            patch("orchestration.task_dispatcher.Path.write_text") as mock_write_text,
            patch("orchestration.task_dispatcher.subprocess.run") as mock_run,
            patch("orchestration.task_dispatcher.shutil.which") as mock_which,
            patch("orchestration.task_dispatcher.validate_cli_two_phase") as mock_validate,
        ):
            def which_side_effect(command):
                known_binaries = {
                    "gemini": "/usr/bin/gemini",
                    "tmux": "/usr/bin/tmux",
                }
                return known_binaries.get(command)

            mock_which.side_effect = which_side_effect
            
            # Mock validation to succeed
            mock_validate.return_value = ValidationResult(
                success=True,
                phase="execution",
                message="gemini execution test passed",
                output_file=MagicMock(),
            )

            # Mock agent execution call
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            result = self.dispatcher.create_dynamic_agent(agent_spec)

        self.assertTrue(result, "Agent creation should succeed when validation passes")
        # Verify validation was called
        mock_validate.assert_called()

    def test_agent_creation_with_gemini_validation_failure_fails(self):
        """Agent creation should fail when Gemini validation fails (no automatic fallback)."""
        agent_spec = {
            "name": "test-agent-gemini-fallback",
            "focus": "Test failure when Gemini validation fails",
            "prompt": "Test prompt",
            "capabilities": [],
            "type": "development",
            "cli": "gemini",
        }

        with (
            patch.object(self.dispatcher, "_cleanup_stale_prompt_files"),
            patch.object(self.dispatcher, "_get_active_tmux_agents", return_value=set()),
            patch.object(self.dispatcher, "_print_tmp_subdirectories"),
            patch.object(
                self.dispatcher,
                "_create_worktree_at_location",
                return_value=("/tmp/test-agent-gemini-fallback", MagicMock(returncode=0, stderr="")),
            ),
            patch("os.makedirs"),
            patch("os.chmod"),
            patch("builtins.open", mock_open()),
            patch("os.path.exists", return_value=False),
            patch("orchestration.task_dispatcher.Path.write_text") as mock_write_text,
            patch("orchestration.task_dispatcher.subprocess.run") as mock_run,
            patch("orchestration.task_dispatcher.shutil.which") as mock_which,
            patch.object(self.dispatcher, "_validate_cli_availability") as mock_validate_method,
        ):
            def which_side_effect(command):
                known_binaries = {
                    "gemini": "/usr/bin/gemini",
                    "codex": "/usr/bin/codex",
                    "tmux": "/usr/bin/tmux",
                }
                return known_binaries.get(command)

            mock_which.side_effect = which_side_effect
            
            # Mock validation: Gemini fails (no fallback attempted)
            def validate_side_effect(cli_name, cli_path, agent_name, model=None):
                if cli_name == "gemini":
                    return False
                return False
            
            mock_validate_method.side_effect = validate_side_effect

            # Mock agent execution call
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            result = self.dispatcher.create_dynamic_agent(agent_spec)

        # Should fail because Gemini validation failed and no fallback occurs
        self.assertFalse(result, "Agent creation should fail when validation fails")
        # CLI should remain unchanged (no fallback)
        self.assertEqual(agent_spec["cli"], "gemini", "Should not fall back to Codex when Gemini fails")
        # Verify only Gemini validation was attempted (no fallback validation)
        validation_calls = mock_validate_method.call_args_list

        def _extract_cli_name(call):
            if call[0]:
                return call[0][0]
            return call[1].get("cli_name")

        gemini_calls = [c for c in validation_calls if _extract_cli_name(c) == "gemini"]
        codex_calls = [c for c in validation_calls if _extract_cli_name(c) == "codex"]
        self.assertGreater(len(gemini_calls), 0, "Gemini validation should be attempted")
        self.assertEqual(len(codex_calls), 0, "Codex fallback validation should NOT be attempted")

    def test_agent_creation_fails_when_all_validations_fail(self):
        """Agent creation should fail when all CLI validations fail."""
        agent_spec = {
            "name": "test-agent-all-fail",
            "focus": "Test failure when all validations fail",
            "prompt": "Test prompt",
            "capabilities": [],
            "type": "development",
            "cli": "gemini",
        }

        with (
            patch.object(self.dispatcher, "_cleanup_stale_prompt_files"),
            patch.object(self.dispatcher, "_get_active_tmux_agents", return_value=set()),
            patch.object(self.dispatcher, "_print_tmp_subdirectories"),
            patch("orchestration.task_dispatcher.shutil.which") as mock_which,
            patch("orchestration.task_dispatcher.validate_cli_two_phase") as mock_validate,
        ):
            def which_side_effect(command):
                known_binaries = {
                    "gemini": "/usr/bin/gemini",
                    "codex": "/usr/bin/codex",
                    "claude": "/usr/bin/claude",
                    "cursor": "/usr/bin/cursor-agent",
                    "tmux": "/usr/bin/tmux",
                }
                return known_binaries.get(command)

            mock_which.side_effect = which_side_effect
            
            # Mock all validations to fail
            mock_validate.return_value = ValidationResult(
                success=False,
                phase="execution",
                message="validation failed",
            )
            
            # Mock all validations to fail
            with patch("orchestration.task_dispatcher.subprocess.run") as mock_run:
                # All validations fail (quota/errors)
                mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="exhausted your daily quota")
                
                result = self.dispatcher.create_dynamic_agent(agent_spec)

        self.assertFalse(result, "Agent creation should fail when all validations fail")

    def test_agent_creation_logs_validation_steps(self):
        """Agent creation should log validation steps for debugging."""
        agent_spec = {
            "name": "test-agent-logging",
            "focus": "Test validation logging",
            "prompt": "Test prompt",
            "capabilities": [],
            "type": "development",
            "cli": "gemini",
        }

        with (
            patch.object(self.dispatcher, "_cleanup_stale_prompt_files"),
            patch.object(self.dispatcher, "_get_active_tmux_agents", return_value=set()),
            patch.object(self.dispatcher, "_print_tmp_subdirectories"),
            patch.object(
                self.dispatcher,
                "_create_worktree_at_location",
                return_value=("/tmp/test-agent-logging", MagicMock(returncode=0, stderr="")),
            ),
            patch("os.makedirs"),
            patch("os.chmod"),
            patch("builtins.open", mock_open()),
            patch("os.path.exists", return_value=False),
            patch("orchestration.task_dispatcher.Path.write_text"),
            patch("orchestration.task_dispatcher.subprocess.run") as mock_run,
            patch("orchestration.task_dispatcher.shutil.which") as mock_which,
            patch("builtins.print") as mock_print,
        ):
            def which_side_effect(command):
                known_binaries = {
                    "gemini": "/usr/bin/gemini",
                    "tmux": "/usr/bin/tmux",
                }
                return known_binaries.get(command)

            mock_which.side_effect = which_side_effect
            mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")

            self.dispatcher.create_dynamic_agent(agent_spec)

        # Verify validation logging occurred
        print_calls = [str(call) for call in mock_print.call_args_list]
        validation_logs = [call for call in print_calls if "validation" in call.lower() or "validating" in call.lower()]
        self.assertGreater(len(validation_logs), 0, "Validation steps should be logged")
        
        # Verify agent name appears in logs
        agent_name_logs = [call for call in print_calls if "test-agent-logging" in call]
        self.assertGreater(len(agent_name_logs), 0, "Agent name should appear in validation logs")


if __name__ == "__main__":
    unittest.main()
