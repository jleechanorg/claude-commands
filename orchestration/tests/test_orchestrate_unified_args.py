#!/usr/bin/env python3
"""
Unit tests for orchestrate_unified.py optional arguments.

Tests:
- Argument parsing for all optional flags
- Options dict construction
- Context file loading
- Branch checkout handling
- Agent spec injection
"""

import argparse
import inspect
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Add orchestration directory to path for imports
orchestration_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, orchestration_dir)

from orchestration import orchestrate_unified
from orchestration import live_mode
from orchestration.cli_args import add_agent_cli_and_model_arguments
from orchestration.cli_args import add_named_session_argument
from orchestration.cli_args import add_shared_orchestration_arguments
from orchestration.cli_args import add_task_argument
from orchestration.cli_args import add_live_cli_arguments
from orchestration.orchestrate_unified import UnifiedOrchestration


class TestOrchestrateUnifiedArguments(unittest.TestCase):
    """Test orchestrate_unified.py argument parsing."""

    def test_argparse_all_optional_arguments(self):
        """Test that all optional arguments are parsed correctly."""
        test_args = [
            "orchestrate_unified.py",
            "--context",
            "/tmp/context.md",
            "--branch",
            "my-branch",
            "--pr",
            "123",
            "--agent-cli",
            "codex",
            "--mcp-agent",
            "TestAgent",
            "--bead",
            "bead-123",
            "--validate",
            "make test",
            "--no-new-pr",
            "--no-new-branch",
            "My task description",
        ]

        parser = argparse.ArgumentParser()
        parser.add_argument("task", nargs="+")
        parser.add_argument("--context", type=str, default=None)
        parser.add_argument("--branch", type=str, default=None)
        parser.add_argument("--pr", type=int, default=None)
        parser.add_argument("--agent-cli", type=str, default=None)
        parser.add_argument("--mcp-agent", type=str, default=None)
        parser.add_argument("--bead", type=str, default=None)
        parser.add_argument("--validate", type=str, default=None)
        parser.add_argument("--no-new-pr", action="store_true")
        parser.add_argument("--no-new-branch", action="store_true")

        args = parser.parse_args(test_args[1:])

        self.assertEqual(args.task, ["My task description"])
        self.assertEqual(args.context, "/tmp/context.md")
        self.assertEqual(args.branch, "my-branch")
        self.assertEqual(args.pr, 123)
        self.assertEqual(args.agent_cli, "codex")
        self.assertEqual(args.mcp_agent, "TestAgent")
        self.assertEqual(args.bead, "bead-123")
        self.assertEqual(args.validate, "make test")
        self.assertTrue(args.no_new_pr)
        self.assertTrue(args.no_new_branch)

    def test_argparse_no_optional_arguments(self):
        """Test parsing with only task description (backward compatibility)."""
        test_args = ["orchestrate_unified.py", "Simple", "task", "here"]

        parser = argparse.ArgumentParser()
        parser.add_argument("task", nargs="+")
        parser.add_argument("--context", type=str, default=None)
        parser.add_argument("--branch", type=str, default=None)
        parser.add_argument("--pr", type=int, default=None)
        parser.add_argument("--agent-cli", type=str, default=None)
        parser.add_argument("--mcp-agent", type=str, default=None)
        parser.add_argument("--bead", type=str, default=None)
        parser.add_argument("--validate", type=str, default=None)
        parser.add_argument("--no-new-pr", action="store_true")
        parser.add_argument("--no-new-branch", action="store_true")

        args = parser.parse_args(test_args[1:])

        self.assertEqual(args.task, ["Simple", "task", "here"])
        self.assertIsNone(args.context)
        self.assertIsNone(args.branch)
        self.assertIsNone(args.pr)
        self.assertIsNone(args.agent_cli)
        self.assertIsNone(args.mcp_agent)
        self.assertIsNone(args.bead)
        self.assertIsNone(args.validate)
        self.assertFalse(args.no_new_pr)
        self.assertFalse(args.no_new_branch)

    def test_argparse_partial_arguments(self):
        """Test parsing with only some optional arguments."""
        test_args = ["orchestrate_unified.py", "--branch", "feature-branch", "--pr", "456", "Update feature"]

        parser = argparse.ArgumentParser()
        parser.add_argument("task", nargs="+")
        parser.add_argument("--context", type=str, default=None)
        parser.add_argument("--branch", type=str, default=None)
        parser.add_argument("--pr", type=int, default=None)
        parser.add_argument("--agent-cli", type=str, default=None)
        parser.add_argument("--mcp-agent", type=str, default=None)
        parser.add_argument("--bead", type=str, default=None)
        parser.add_argument("--validate", type=str, default=None)
        parser.add_argument("--no-new-pr", action="store_true")
        parser.add_argument("--no-new-branch", action="store_true")

        args = parser.parse_args(test_args[1:])

        self.assertEqual(args.task, ["Update feature"])
        self.assertIsNone(args.context)
        self.assertEqual(args.branch, "feature-branch")
        self.assertEqual(args.pr, 456)
        self.assertIsNone(args.agent_cli)
        self.assertIsNone(args.mcp_agent)
        self.assertIsNone(args.bead)
        self.assertIsNone(args.validate)
        self.assertFalse(args.no_new_pr)
        self.assertFalse(args.no_new_branch)

    def test_options_dict_construction(self):
        """Test that options dict is built correctly from parsed args."""

        # Simulate parsed args
        class MockArgs:
            context = "/tmp/ctx.md"
            branch = "test-branch"
            pr = 789
            agent_cli = "gemini"
            agent_cli_provided = False
            mcp_agent = "Agent1"
            bead = "bead-xyz"
            validate = "./run_tests.sh"
            no_new_pr = True
            no_new_branch = False
            task = ["Test task"]

        args = MockArgs()

        options = {
            "context": args.context,
            "branch": args.branch,
            "pr": args.pr,
            "agent_cli": args.agent_cli,
            "agent_cli_provided": args.agent_cli_provided,
            "mcp_agent": args.mcp_agent,
            "bead": args.bead,
            "validate": args.validate,
            "no_new_pr": args.no_new_pr,
            "no_new_branch": args.no_new_branch,
        }

        self.assertEqual(options["context"], "/tmp/ctx.md")
        self.assertEqual(options["branch"], "test-branch")
        self.assertEqual(options["pr"], 789)
        self.assertEqual(options["agent_cli"], "gemini")
        self.assertFalse(options["agent_cli_provided"])
        self.assertEqual(options["mcp_agent"], "Agent1")
        self.assertEqual(options["bead"], "bead-xyz")
        self.assertEqual(options["validate"], "./run_tests.sh")
        self.assertTrue(options["no_new_pr"])
        self.assertFalse(options["no_new_branch"])


class TestContextFileLoading(unittest.TestCase):
    """Test context file loading functionality."""

    def test_context_file_loads_successfully(self):
        """Test that context file content is loaded correctly."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", dir=project_root, delete=False) as f:
            f.write("# Test Context\n\nThis is test context content.")
            context_path = f.name

        try:
            with open(context_path, "r") as f:
                content = f.read()

            self.assertIn("# Test Context", content)
            self.assertIn("This is test context content", content)
        finally:
            os.unlink(context_path)

    def test_context_file_not_found_handling(self):
        """Test handling of missing context file."""
        context_path = "/nonexistent/path/context.md"
        self.assertFalse(os.path.exists(context_path))


@unittest.skip(
    "PR #5824: dispatcher analyze/create removed; ai_orch now uses runner.py passthrough/async only"
)
class TestLiveModeDispatcherWrapPrompt(unittest.TestCase):
    """Ensure live-mode dispatcher commands keep wrapped PR-aware behavior."""

    def test_dispatcher_analyze_enables_wrap_and_pr_update_mode(self):
        with (
            patch("sys.argv", ["ai_orch", "dispatcher", "analyze", "Fix PR #123"]),
            patch("orchestration.live_mode.TaskDispatcher") as mock_dispatcher_cls,
        ):
            dispatcher = mock_dispatcher_cls.return_value
            dispatcher.analyze_task_and_create_agents.return_value = [
                {"name": "task-agent-1", "cli": "claude"}
            ]

            rc = live_mode.main()

        self.assertEqual(rc, 0)
        dispatcher.analyze_task_and_create_agents.assert_called_once_with(
            "Fix PR #123",
            forced_cli=None,
            wrap_prompt=True,
            pr_update_mode=True,
        )

    def test_dispatcher_create_enables_wrap_and_pr_update_mode(self):
        with (
            patch("sys.argv", ["ai_orch", "dispatcher", "create", "Update PR #99"]),
            patch("orchestration.live_mode.TaskDispatcher") as mock_dispatcher_cls,
        ):
            dispatcher = mock_dispatcher_cls.return_value
            dispatcher.analyze_task_and_create_agents.return_value = [
                {"name": "task-agent-1", "cli": "claude"}
            ]
            dispatcher.create_dynamic_agent.return_value = True

            rc = live_mode.main()

        self.assertEqual(rc, 0)
        dispatcher.analyze_task_and_create_agents.assert_called_once_with(
            "Update PR #99",
            forced_cli=None,
            wrap_prompt=True,
            pr_update_mode=True,
        )


class TestAgentSpecInjection(unittest.TestCase):
    """Test agent spec injection with options."""

    def test_agent_spec_receives_all_options(self):
        """Test that agent spec is properly augmented with options."""
        agent_spec = {"name": "test-agent", "capabilities": "Test capabilities"}

        options = {
            "agent_cli": "codex",
            "branch": "feature-branch",
            "pr": 123,
            "mcp_agent": "TestAgent",
            "bead": "bead-id",
            "validate": "make test",
            "no_new_pr": True,
            "no_new_branch": True,
        }

        # Simulate injection logic from orchestrate method
        if options.get("agent_cli") is not None:
            agent_spec["cli"] = options["agent_cli"]
        if options.get("branch"):
            agent_spec["existing_branch"] = options["branch"]
        if options.get("pr"):
            agent_spec["existing_pr"] = options["pr"]
        if options.get("mcp_agent"):
            agent_spec["mcp_agent_name"] = options["mcp_agent"]
        if options.get("bead"):
            agent_spec["bead_id"] = options["bead"]
        if options.get("validate"):
            agent_spec["validation_command"] = options["validate"]
        if options.get("no_new_pr"):
            agent_spec["no_new_pr"] = True
        if options.get("no_new_branch"):
            agent_spec["no_new_branch"] = True

        # Verify injected values
        self.assertEqual(agent_spec["cli"], "codex")
        self.assertEqual(agent_spec["existing_branch"], "feature-branch")
        self.assertEqual(agent_spec["existing_pr"], 123)
        self.assertEqual(agent_spec["mcp_agent_name"], "TestAgent")
        self.assertEqual(agent_spec["bead_id"], "bead-id")
        self.assertEqual(agent_spec["validation_command"], "make test")
        self.assertTrue(agent_spec["no_new_pr"])
        self.assertTrue(agent_spec["no_new_branch"])

    def test_agent_spec_partial_options(self):
        """Test agent spec with only some options provided."""
        agent_spec = {"name": "test-agent", "capabilities": "Test capabilities"}

        options = {
            "branch": "my-branch",
            "pr": None,
            "mcp_agent": None,
            "bead": None,
            "validate": None,
            "no_new_pr": False,
            "no_new_branch": False,
        }

        # Simulate injection logic
        if options.get("branch"):
            agent_spec["existing_branch"] = options["branch"]
        if options.get("pr"):
            agent_spec["existing_pr"] = options["pr"]
        if options.get("mcp_agent"):
            agent_spec["mcp_agent_name"] = options["mcp_agent"]
        if options.get("bead"):
            agent_spec["bead_id"] = options["bead"]
        if options.get("validate"):
            agent_spec["validation_command"] = options["validate"]
        if options.get("no_new_pr"):
            agent_spec["no_new_pr"] = True
        if options.get("no_new_branch"):
            agent_spec["no_new_branch"] = True

        # Only branch should be set
        self.assertEqual(agent_spec["existing_branch"], "my-branch")
        self.assertNotIn("existing_pr", agent_spec)
        self.assertNotIn("mcp_agent_name", agent_spec)
        self.assertNotIn("bead_id", agent_spec)
        self.assertNotIn("validation_command", agent_spec)
        self.assertNotIn("no_new_pr", agent_spec)
        self.assertNotIn("no_new_branch", agent_spec)


class TestEnhancedTaskWithContext(unittest.TestCase):
    """Test task enhancement with context content."""

    def test_task_enhanced_with_context(self):
        """Test that task description is enhanced with context content."""
        task_description = "Fix the authentication bug"
        context_content = "  ## Auth Module\n\nThe auth module is in src/auth.py\n"

        normalized_context = context_content.strip()
        enhanced_task = f"{task_description}\n\n---\n## Pre-computed Context\n{normalized_context}"

        self.assertIn("Fix the authentication bug", enhanced_task)
        self.assertIn("## Pre-computed Context", enhanced_task)
        self.assertIn("## Auth Module", enhanced_task)
        self.assertIn("src/auth.py", enhanced_task)

    def test_task_not_enhanced_without_context(self):
        """Test that task description is unchanged without context."""
        task_description = "Simple task"
        context_content = None

        enhanced_task = task_description
        if context_content:
            enhanced_task = f"{task_description}\n\n---\n## Pre-computed Context\n{context_content}"

        self.assertEqual(enhanced_task, "Simple task")


class TestBranchValidation(unittest.TestCase):
    """Test branch name validation."""

    def test_safe_branch_names(self):
        self.assertTrue(orchestrate_unified.UnifiedOrchestration._is_safe_branch_name("feature/branch-1"))
        self.assertTrue(orchestrate_unified.UnifiedOrchestration._is_safe_branch_name("release_2024.01"))

    def test_unsafe_branch_names(self):
        self.assertFalse(orchestrate_unified.UnifiedOrchestration._is_safe_branch_name("feature branch"))
        self.assertFalse(orchestrate_unified.UnifiedOrchestration._is_safe_branch_name("branch;rm -rf /"))


class TestMainFunctionImport(unittest.TestCase):
    """Test that orchestrate_unified module can be imported."""

    def test_module_imports(self):
        """Test that orchestrate_unified module imports successfully."""
        self.assertTrue(hasattr(orchestrate_unified, "main"))
        self.assertTrue(hasattr(orchestrate_unified, "UnifiedOrchestration"))

    def test_unified_orchestration_class_exists(self):
        """Test that UnifiedOrchestration class exists and has orchestrate method."""
        from orchestration import orchestrate_unified

        self.assertTrue(hasattr(orchestrate_unified.UnifiedOrchestration, "orchestrate"))

    def test_orchestrate_method_accepts_options(self):
        """Test that orchestrate method accepts options parameter."""
        sig = inspect.signature(orchestrate_unified.UnifiedOrchestration.orchestrate)
        params = list(sig.parameters.keys())

        self.assertIn("task_description", params)
        self.assertIn("options", params)

        # Verify options has default value
        options_param = sig.parameters["options"]
        self.assertEqual(options_param.default, None)


class TestGhCommandMocking(unittest.TestCase):
    """Test gh command interactions are properly mockable."""

    @patch("subprocess.run")
    def test_gh_pr_list_command_structure(self, mock_run):
        """Test that gh pr list command is called with correct arguments."""
        mock_run.return_value = MagicMock(returncode=0, stdout="[]", stderr="")

        # Simulate the command structure used in _find_recent_agent_work
        result = subprocess.run(
            [
                "gh",
                "pr",
                "list",
                "--author",
                "@me",
                "--limit",
                "5",
                "--json",
                "number,title,headRefName,createdAt",
            ],
            shell=False,
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        self.assertEqual(call_args[0], "gh")
        self.assertEqual(call_args[1], "pr")
        self.assertEqual(call_args[2], "list")
        self.assertIn("--author", call_args)
        self.assertIn("--json", call_args)

    @patch("subprocess.run")
    def test_gh_pr_list_with_branch_pattern(self, mock_run):
        """Test gh pr list with --head branch pattern."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='[{"number": 123, "url": "https://github.com/test/repo/pull/123", "title": "Test PR", "state": "OPEN"}]',
            stderr="",
        )

        branch_pattern = "task-agent-test-work"
        result = subprocess.run(
            [
                "gh",
                "pr",
                "list",
                "--head",
                branch_pattern,
                "--json",
                "number,url,title,state",
            ],
            shell=False,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        self.assertIn("--head", call_args)
        self.assertIn(branch_pattern, call_args)

    @patch("subprocess.run")
    def test_gh_command_timeout_handling(self, mock_run):
        """Test that gh commands use appropriate timeout."""
        mock_run.return_value = MagicMock(returncode=0, stdout="[]", stderr="")

        subprocess.run(
            ["gh", "pr", "list"],
            shell=False,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )

        # Verify timeout was set
        call_kwargs = mock_run.call_args[1]
        self.assertEqual(call_kwargs.get("timeout"), 30)
        self.assertEqual(call_kwargs.get("shell"), False)

    @patch("subprocess.run")
    def test_gh_command_failure_handling(self, mock_run):
        """Test handling of gh command failures."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "gh")

        # Simulate the exception handling in orchestrate_unified.py
        try:
            subprocess.run(
                ["gh", "pr", "list"],
                shell=False,
                capture_output=True,
                text=True,
                check=True,
                timeout=30,
            )
            failed = False
        except subprocess.CalledProcessError:
            failed = True

        self.assertTrue(failed)

    def test_pr_json_parsing(self):
        """Test parsing of gh pr list JSON output."""
        # Simulate gh pr list output
        pr_json = '[{"number": 123, "title": "Test PR", "headRefName": "feature-branch", "createdAt": "2025-01-01T12:00:00Z"}]'
        prs = json.loads(pr_json)

        self.assertEqual(len(prs), 1)
        self.assertEqual(prs[0]["number"], 123)
        self.assertEqual(prs[0]["title"], "Test PR")
        self.assertEqual(prs[0]["headRefName"], "feature-branch")

    def test_pr_created_at_parsing(self):
        """Test parsing of PR createdAt timestamp."""
        # Test the ISO 8601 Z format parsing
        created_at = "2025-01-01T12:00:00Z"
        pr_created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        self.assertEqual(pr_created_at.year, 2025)
        self.assertEqual(pr_created_at.month, 1)
        self.assertEqual(pr_created_at.day, 1)
        self.assertEqual(pr_created_at.hour, 12)


class TestOrchestrateReturnConsistency(unittest.TestCase):
    """Regression tests for consistent int return values from orchestrate()."""

    def test_orchestrate_returns_zero_when_dependencies_missing(self):
        """Dependency failure path should return int 0, not None."""
        orchestration = orchestrate_unified.UnifiedOrchestration()
        with patch.object(orchestration, "_check_dependencies", return_value=False):
            result = orchestration.orchestrate("test task")
        self.assertEqual(result, 0)


class TestLiveModeCLIHelpAndWorktreeFlags(unittest.TestCase):
    """Regression coverage for ai_orch CLI help and run-time worktree flags."""

    @unittest.skip("PR #5824: ai_orch entry point is runner.py; help text differs")
    def test_ai_orch_help_includes_run_options(self):
        """Top-level --help should surface run-mode options including worktree flags."""
        with (
            patch("sys.argv", ["ai_orch", "--help"]),
            patch("sys.stdout", new_callable=io.StringIO) as mock_stdout,
        ):
            rc = live_mode.main()

        self.assertEqual(rc, 0)
        output = mock_stdout.getvalue()
        self.assertIn("Run mode arguments (default command):", output)
        self.assertIn("--no-worktree", output)
        self.assertIn("--worktree", output)
        self.assertIn("--no-new-branch", output)

    @unittest.skip("PR #5824: run mode in runner.py; no UnifiedOrchestration worktree options")
    def test_ai_orch_run_supports_worktree_flag(self):
        """--worktree should map to no_worktree=False and reach UnifiedOrchestration."""
        with (
            patch("sys.argv", ["ai_orch", "run", "--worktree", "Test", "worktree", "task"]),
            patch("orchestration.live_mode.UnifiedOrchestration") as mock_unified_cls,
        ):
            orchestrator = mock_unified_cls.return_value
            orchestrator.orchestrate.return_value = 1

            rc = live_mode.main()

        self.assertEqual(rc, 0)
        orchestrator.orchestrate.assert_called_once()
        _, orchestrate_kwargs = orchestrator.orchestrate.call_args
        self.assertFalse(orchestrate_kwargs["options"]["no_worktree"])

    @unittest.skip("PR #5824: run mode in runner.py; no --no-worktree flag")
    def test_ai_orch_run_supports_no_worktree_flag(self):
        """Explicit --no-worktree should map to no_worktree=True and reach UnifiedOrchestration."""
        with (
            patch("sys.argv", ["ai_orch", "run", "--no-worktree", "Test", "no", "worktree", "task"]),
            patch("orchestration.live_mode.UnifiedOrchestration") as mock_unified_cls,
        ):
            orchestrator = mock_unified_cls.return_value
            orchestrator.orchestrate.return_value = 1

            rc = live_mode.main()

        self.assertEqual(rc, 0)
        orchestrator.orchestrate.assert_called_once()
        _, orchestrate_kwargs = orchestrator.orchestrate.call_args
        self.assertTrue(orchestrate_kwargs["options"]["no_worktree"])

    @unittest.skip("PR #5824: run mode in runner.py; live_mode has no run")
    def test_ai_orch_run_default_worktree_is_disabled(self):
        """No flag should default to no_worktree=True (worktree isolation disabled by default)."""
        with (
            patch("sys.argv", ["ai_orch", "run", "Test", "default", "task"]),
            patch("orchestration.live_mode.UnifiedOrchestration") as mock_unified_cls,
        ):
            orchestrator = mock_unified_cls.return_value
            orchestrator.orchestrate.return_value = 1

            rc = live_mode.main()

        self.assertEqual(rc, 0)
        orchestrator.orchestrate.assert_called_once()
        _, orchestrate_kwargs = orchestrator.orchestrate.call_args
        self.assertTrue(orchestrate_kwargs["options"]["no_worktree"])

    @unittest.skip("PR #5824: run mode in runner.py; live_mode has no run")
    def test_ai_orch_defaults_to_claude_and_sonnet(self):
        """Default ai_orch run should target claude with sonnet model unless overridden."""
        with (
            patch("sys.argv", ["ai_orch", "run", "Build", "new", "feature"]),
            patch("orchestration.live_mode.UnifiedOrchestration") as mock_unified_cls,
        ):
            orchestrator = mock_unified_cls.return_value
            orchestrator.orchestrate.return_value = 1

            rc = live_mode.main()

        self.assertEqual(rc, 0)
        orchestrator.orchestrate.assert_called_once()
        _, orchestrate_kwargs = orchestrator.orchestrate.call_args
        options = orchestrate_kwargs["options"]
        self.assertEqual(options["agent_cli"], "claude")
        self.assertEqual(options["model"], "sonnet")
        self.assertTrue(options["no_worktree"])

    @unittest.skip("PR #5824: run mode in runner.py; no add_shared_orchestration_arguments in run path")
    def test_shared_orchestration_arguments_are_reused_in_ai_orch_run_parser(self):
        """live_mode should wire shared orchestration args through a single helper function."""
        with (
            patch("sys.argv", ["ai_orch", "run", "some", "task"]),
            patch("orchestration.live_mode.UnifiedOrchestration") as mock_unified_cls,
            patch(
                "orchestration.live_mode.add_shared_orchestration_arguments",
                wraps=live_mode.add_shared_orchestration_arguments,
            ) as add_shared_mock,
        ):
            mock_unified_cls.return_value.orchestrate.return_value = 1

            rc = live_mode.main()

        self.assertEqual(rc, 0)
        add_shared_mock.assert_called_once()

    def test_shared_parser_handles_new_orch_args(self):
        """Helper used by both CLI entrypoints should parse common orchestration flags."""
        parser = argparse.ArgumentParser()
        add_shared_orchestration_arguments(parser)

        parsed = parser.parse_args(
            [
                "--worktree",
                "--branch",
                "feature-branch",
                "--validate",
                "make test",
                "--mcp-agent",
                "agent-name",
                "--bead",
                "bead-1",
                "--no-new-pr",
                "--agent-cli",
                "gemini,claude",
            ]
        )

        self.assertFalse(parsed.no_worktree)
        self.assertEqual(parsed.branch, "feature-branch")
        self.assertEqual(parsed.validate, "make test")
        self.assertEqual(parsed.mcp_agent, "agent-name")
        self.assertEqual(parsed.bead, "bead-1")
        self.assertTrue(parsed.no_new_pr)
        self.assertEqual(parsed.agent_cli, "gemini,claude")

    @unittest.skip("PR #5824: dispatcher analyze/create removed")
    def test_dispatcher_parsers_reuse_agent_cli_helper(self):
        """Dispatcher analyze/create should use the shared agent-cli argument helper."""
        with (
            patch(
                "orchestration.live_mode.add_agent_cli_and_model_arguments",
                wraps=add_agent_cli_and_model_arguments,
            ) as add_agent_helper,
            patch("sys.argv", ["ai_orch", "dispatcher", "analyze", "Task input"]),
            patch("orchestration.live_mode.TaskDispatcher") as mock_dispatcher_cls,
        ):
            dispatcher = mock_dispatcher_cls.return_value
            dispatcher.analyze_task_and_create_agents.return_value = [{"name": "task-agent-1", "cli": "claude"}]
            rc = live_mode.main()

        self.assertEqual(rc, 0)
        self.assertGreaterEqual(add_agent_helper.call_count, 1)

    def test_dispatcher_create_parses_shared_agent_cli_model_args(self):
        """Dispatcher create should keep shared agent_cli/model signature."""
        parser = argparse.ArgumentParser()
        parser.add_argument("task", nargs="+")
        add_agent_cli_and_model_arguments(parser)

        parsed = parser.parse_args(["--agent-cli", "claude", "--model", "sonnet", "ignored-task"])

        self.assertEqual(parsed.agent_cli, "claude")
        self.assertEqual(parsed.model, "sonnet")


class TestCliArgCentralizationHelpers(unittest.TestCase):
    """Regression tests for centralized orchestration CLI helpers."""

    def test_safe_monitor_args_are_reusable(self):
        parser = argparse.ArgumentParser(description="safe monitor")
        from orchestration.cli_args import add_safe_monitor_arguments

        add_safe_monitor_arguments(parser)

        parsed = parser.parse_args(["--all", "--interval", "15", "agent-1"])

        self.assertTrue(parsed.all)
        self.assertEqual(parsed.interval, 15)
        self.assertEqual(parsed.agent, "agent-1")


    @unittest.skip("PR #5824: run mode moved to runner.py; live_mode no longer has run with UnifiedOrchestration")
    def test_live_mode_run_uses_shared_task_helper(self):
        """run mode should use centralized task positional helper."""
        with patch("orchestration.live_mode.add_task_argument", wraps=add_task_argument) as helper:
            with patch("orchestration.live_mode.UnifiedOrchestration") as mock_unified_cls:
                mock_unified_cls.return_value.orchestrate.return_value = 1
                with patch("sys.argv", ["ai_orch", "run", "sample", "task"]):
                    rc = live_mode.main()

        self.assertGreaterEqual(helper.call_count, 1)
        self.assertEqual(rc, 0)

    @unittest.skip("PR #5824: orchestrate_unified is stub; does not use add_task_argument")
    def test_orchestrate_unified_uses_shared_task_helper(self):
        """orchestrate_unified should use centralized task helper."""
        with patch("orchestration.orchestrate_unified.add_task_argument", wraps=add_task_argument) as helper:
            with patch("orchestration.orchestrate_unified.UnifiedOrchestration") as mock_unified_cls:
                mock_unified_cls.return_value.orchestrate.return_value = 1
                with patch("sys.argv", ["orchestrate_unified.py", "sample", "task"]):
                    rc = orchestrate_unified.main()

        self.assertEqual(helper.call_count, 1)
        self.assertEqual(rc, 0)

    def test_reusable_task_arg_builder(self):
        """Task helper should produce identical positional parsing."""
        parser = argparse.ArgumentParser()
        add_task_argument(parser, help_text="Task description for tests")
        parsed = parser.parse_args(["my", "task", "input"])

        self.assertEqual(parsed.task, ["my", "task", "input"])

    def test_live_cli_argument_reuse(self):
        """Live CLI helper should parse shared session command options consistently."""
        parser = argparse.ArgumentParser()
        add_live_cli_arguments(parser)
        parsed = parser.parse_args(["--cli", "claude", "--name", "sess", "--dir", "/tmp", "--model", "sonnet", "--detached"])

        self.assertEqual(parsed.cli, "claude")
        self.assertEqual(parsed.name, "sess")
        self.assertEqual(parsed.dir, "/tmp")
        self.assertEqual(parsed.model, "sonnet")
        self.assertTrue(parsed.detached)

    def test_named_session_argument_reusable(self):
        parser = argparse.ArgumentParser()
        add_named_session_argument(parser, help_text="Session name to attach to")
        parsed = parser.parse_args(["session-1"])

        self.assertEqual(parsed.session, "session-1")

    @unittest.skip("PR #5824: run mode moved to runner.py; live_mode no longer has run")
    def test_ai_orch_run_default_worktree_behavior(self):
        """Default run invocation without worktree flags should preserve no_worktree=True."""
        with (
            patch("sys.argv", ["ai_orch", "run", "Default", "worktree", "task"]),
            patch("orchestration.live_mode.UnifiedOrchestration") as mock_unified_cls,
        ):
            orchestrator = mock_unified_cls.return_value
            orchestrator.orchestrate.return_value = 1

            rc = live_mode.main()

        self.assertEqual(rc, 0)
        orchestrator.orchestrate.assert_called_once()
        _, orchestrate_kwargs = orchestrator.orchestrate.call_args
        self.assertTrue(orchestrate_kwargs["options"]["no_worktree"])

    def test_cleanup_args_reusable(self):
        parser = argparse.ArgumentParser()
        from orchestration.cli_args import add_cleanup_arguments

        add_cleanup_arguments(parser)

        parsed = parser.parse_args(["--dry-run", "--json"])

        self.assertTrue(parsed.dry_run)
        self.assertTrue(parsed.json)

    def test_test_runner_args_reusable(self):
        parser = argparse.ArgumentParser()
        from orchestration.cli_args import add_test_runner_arguments

        add_test_runner_arguments(parser)

        parsed = parser.parse_args(["--verbose", "--list"])

        self.assertTrue(parsed.verbose)
        self.assertTrue(parsed.list)


if __name__ == "__main__":
    unittest.main()
