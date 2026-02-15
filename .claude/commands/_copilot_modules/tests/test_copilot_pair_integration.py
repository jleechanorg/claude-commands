#!/usr/bin/env python3
"""
Tests for /copilot and /pair integration.

Following TDD (RED phase): Write tests FIRST before implementation.
These tests will FAIL until the integration is implemented.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from pair_integration import (
    should_trigger_pair,
    generate_pair_task_spec,
    collect_pair_results,
    enhance_response_with_pair_data,
    load_copilot_config
)


class TestCopilotPairTriggerLogic(unittest.TestCase):
    """Test when /pair should be triggered based on comment category."""

    def test_triggers_pair_for_critical_comments_when_enabled(self):
        """Test /pair launches for CRITICAL comments when COPILOT_USE_PAIR=true."""
        # Arrange
        comment = {
            "id": "123",
            "category": "CRITICAL",
            "body": "Fix this security vulnerability immediately"
        }
        env = {"COPILOT_USE_PAIR": "true"}

        # Act
        should_trigger = should_trigger_pair(comment, env)

        # Assert
        self.assertTrue(should_trigger, "CRITICAL comments should trigger /pair when enabled")

    def test_triggers_pair_for_blocking_comments_when_enabled(self):
        """Test /pair launches for BLOCKING comments when COPILOT_USE_PAIR=true and min_severity is BLOCKING."""
        # Arrange
        comment = {
            "id": "124",
            "category": "BLOCKING",
            "body": "This blocks merge - must fix"
        }
        env = {"COPILOT_USE_PAIR": "true", "COPILOT_PAIR_MIN_SEVERITY": "BLOCKING"}

        # Act
        should_trigger = should_trigger_pair(comment, env)

        # Assert
        self.assertTrue(should_trigger, "BLOCKING comments should trigger /pair when min_severity is BLOCKING")

    def test_blocking_triggers_with_default_min_severity(self):
        """Test BLOCKING triggers even when min severity remains default CRITICAL."""
        # Arrange
        comment = {
            "id": "124b",
            "category": "BLOCKING",
            "body": "This blocks merge - must fix"
        }
        env = {"COPILOT_USE_PAIR": "true"}  # min severity defaults to CRITICAL

        # Act
        should_trigger = should_trigger_pair(comment, env)

        # Assert
        self.assertTrue(
            should_trigger,
            "BLOCKING should still trigger with default config when /pair is enabled",
        )

    def test_no_trigger_for_important_by_default(self):
        """Test /pair does NOT trigger for IMPORTANT by default."""
        # Arrange
        comment = {
            "id": "125",
            "category": "IMPORTANT",
            "body": "Please consider refactoring this"
        }
        env = {"COPILOT_USE_PAIR": "true"}

        # Act
        should_trigger = should_trigger_pair(comment, env)

        # Assert
        self.assertFalse(should_trigger, "IMPORTANT should not trigger /pair by default")

    def test_triggers_important_when_flag_set(self):
        """Test /pair triggers for IMPORTANT when COPILOT_PAIR_IMPORTANT=true."""
        # Arrange
        comment = {
            "id": "126",
            "category": "IMPORTANT",
            "body": "Please refactor this"
        }
        env = {
            "COPILOT_USE_PAIR": "true",
            "COPILOT_PAIR_IMPORTANT": "true"
        }

        # Act
        should_trigger = should_trigger_pair(comment, env)

        # Assert
        self.assertTrue(should_trigger, "IMPORTANT should trigger when flag enabled")

    def test_no_trigger_when_pair_disabled(self):
        """Test /pair never triggers when COPILOT_USE_PAIR=false."""
        # Arrange
        comment = {
            "id": "127",
            "category": "CRITICAL",
            "body": "Critical security issue"
        }
        env = {"COPILOT_USE_PAIR": "false"}

        # Act
        should_trigger = should_trigger_pair(comment, env)

        # Assert
        self.assertFalse(should_trigger, "No /pair when disabled, even for CRITICAL")

    def test_no_trigger_for_routine_comments(self):
        """Test /pair never triggers for ROUTINE comments."""
        # Arrange
        comment = {
            "id": "128",
            "category": "ROUTINE",
            "body": "Nice work!"
        }
        env = {"COPILOT_USE_PAIR": "true"}

        # Act
        should_trigger = should_trigger_pair(comment, env)

        # Assert
        self.assertFalse(should_trigger, "ROUTINE comments should never trigger /pair")


class TestPairTaskSpecGeneration(unittest.TestCase):
    """Test generation of task spec passed to /pair agents."""

    def test_generates_task_spec_with_all_context(self):
        """Test task spec includes all necessary context for /pair."""
        # Arrange
        comment = {
            "id": "123",
            "category": "CRITICAL",
            "body": "Fix null pointer in auth.py line 45",
            "path": "src/auth.py",
            "line": 45,
            "html_url": "https://github.com/repo/pr/1#comment-123"
        }
        pr_context = {
            "number": "5360",
            "branch": "feature/auth-fix",
            "base": "main",
            "url": "https://github.com/repo/pr/5360"
        }

        # Act
        task_spec = generate_pair_task_spec(comment, pr_context)

        # Assert
        self.assertIn("Fix PR #5360 Comment #123", task_spec)
        self.assertIn("CRITICAL", task_spec)
        self.assertIn("src/auth.py:45", task_spec)
        self.assertIn("Fix null pointer", task_spec)
        self.assertIn("feature/auth-fix", task_spec)
        self.assertIn("Acceptance Criteria", task_spec)

    def test_task_spec_includes_verification_steps(self):
        """Test task spec includes test commands for verification."""
        # Arrange
        comment = {"id": "124", "category": "BLOCKING", "body": "Fix the bug"}
        pr_context = {"number": "100", "branch": "fix-branch", "base": "main"}

        # Act
        task_spec = generate_pair_task_spec(comment, pr_context)

        # Assert
        self.assertIn("Verification", task_spec)
        self.assertIn("Run", task_spec, "Should include test command")


class TestPairResultCollection(unittest.TestCase):
    """Test collecting results from /pair session."""

    def test_collects_commit_sha_from_pair_session(self):
        """Test extracts commit SHA after /pair completion."""
        # Arrange - simulate pair session created commit
        with tempfile.TemporaryDirectory() as temp_dir:
            session_dir = Path(temp_dir) / "pair_session_123"
            session_dir.mkdir()

            # Simulate pair session output
            (session_dir / "pair_status.txt").write_text("VERIFICATION_COMPLETE")
            (session_dir / "pair_commit.txt").write_text("abc123de")

            # Act
            results = collect_pair_results(session_dir)

            # Assert
            self.assertEqual(results["commit"], "abc123de")
            self.assertEqual(results["status"], "VERIFICATION_COMPLETE")

    def test_collects_modified_files_list(self):
        """Test extracts list of files modified by /pair."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            session_dir = Path(temp_dir) / "pair_session_124"
            session_dir.mkdir()

            files_modified = ["src/auth.py", "tests/test_auth.py"]
            (session_dir / "pair_files.txt").write_text("\n".join(files_modified))
            (session_dir / "pair_status.txt").write_text("VERIFICATION_COMPLETE")

            # Act
            results = collect_pair_results(session_dir)

            # Assert
            self.assertEqual(results["files_modified"], files_modified)

    def test_collects_test_results(self):
        """Test extracts test pass/fail counts from /pair."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            session_dir = Path(temp_dir) / "pair_session_125"
            session_dir.mkdir()

            test_output = "12 passed, 0 failed\ntest_auth.py::test_fix PASSED"
            (session_dir / "pair_test_output.txt").write_text(test_output)
            (session_dir / "pair_status.txt").write_text("VERIFICATION_COMPLETE")

            # Act
            results = collect_pair_results(session_dir)

            # Assert
            self.assertEqual(results["test_results"]["passed"], 12)
            self.assertEqual(results["test_results"]["failed"], 0)


class TestResponsesJsonEnhancement(unittest.TestCase):
    """Test enhancement of responses.json with pair metadata."""

    def test_adds_pair_metadata_to_response(self):
        """Test pair metadata fields added to responses.json."""
        # Arrange
        base_response = {
            "comment_id": "123",
            "category": "CRITICAL",
            "response": "FIXED",
            "action_taken": "Fixed null pointer"
        }
        pair_results = {
            "session_id": "copilot-pair-5360-123-1234567890",
            "commit": "abc123de",
            "files_modified": ["src/auth.py", "tests/test_auth.py"],
            "tests_added": ["tests/test_auth.py"],
            "duration_seconds": 180,
            "status": "VERIFICATION_COMPLETE",
            "test_results": {"passed": 12, "failed": 0}
        }

        # Act
        enhanced = enhance_response_with_pair_data(base_response, pair_results)

        # Assert
        self.assertEqual(enhanced["commit"], "abc123de")
        self.assertIn("pair_metadata", enhanced)
        self.assertEqual(enhanced["pair_metadata"]["session_id"], "copilot-pair-5360-123-1234567890")
        self.assertEqual(enhanced["pair_metadata"]["duration_seconds"], 180)
        self.assertEqual(enhanced["pair_metadata"]["status"], "VERIFICATION_COMPLETE")

    def test_enhanced_response_includes_verification_status(self):
        """Test verification field shows test pass status."""
        # Arrange
        base_response = {"comment_id": "124", "category": "BLOCKING"}
        pair_results = {
            "session_id": "pair-124",
            "status": "VERIFICATION_COMPLETE",
            "test_results": {"passed": 8, "failed": 0}
        }

        # Act
        enhanced = enhance_response_with_pair_data(base_response, pair_results)

        # Assert
        self.assertIn("verification", enhanced)
        self.assertIn("Tests pass", enhanced["verification"])
        self.assertIn("8 passed", enhanced["verification"])


class TestConfigurationFlags(unittest.TestCase):
    """Test configuration environment variables."""

    def test_copilot_use_pair_defaults_to_false(self):
        """Test COPILOT_USE_PAIR defaults to false for safety."""
        # Act
        config = load_copilot_config({})

        # Assert
        self.assertFalse(config["use_pair"])

    def test_pair_min_severity_defaults_to_critical(self):
        """Test minimum severity for /pair defaults to CRITICAL."""
        # Act
        config = load_copilot_config({"COPILOT_USE_PAIR": "true"})

        # Assert
        self.assertEqual(config["pair_min_severity"], "CRITICAL")

    def test_pair_coder_and_verifier_defaults(self):
        """Test default agent CLIs for /pair."""
        # Act
        config = load_copilot_config({"COPILOT_USE_PAIR": "true"})

        # Assert
        self.assertEqual(config["pair_coder"], "claude")
        self.assertEqual(config["pair_verifier"], "codex")

    def test_pair_timeout_defaults_to_600_seconds(self):
        """Test /pair timeout defaults to 10 minutes."""
        # Act
        config = load_copilot_config({"COPILOT_USE_PAIR": "true"})

        # Assert
        self.assertEqual(config["pair_timeout"], 600)


if __name__ == "__main__":
    unittest.main()
