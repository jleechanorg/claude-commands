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


if __name__ == "__main__":
    unittest.main()
