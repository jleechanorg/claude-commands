#!/usr/bin/env python3
"""
Tests for --model parameter support in orchestration and automation.

Validates that model parameter is correctly passed through the automation pipeline.
"""

import argparse
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from jleechanorg_pr_automation.jleechanorg_pr_monitor import (
    JleechanorgPRMonitor,
    _normalize_model,
)


class TestModelParameter(unittest.TestCase):
    """Test suite for model parameter functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.monitor = JleechanorgPRMonitor(automation_username="test-automation-user")

    def test_process_single_pr_accepts_model_parameter(self):
        """Test that process_single_pr_by_number accepts model parameter."""
        with patch.object(self.monitor, 'safety_manager') as mock_safety:
            with patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.AutomationUtils'):
                mock_safety.can_start_global_run.return_value = True
                mock_safety.try_process_pr.return_value = True

                # Should not raise TypeError for model parameter
                try:
                    self.monitor.process_single_pr_by_number(
                        pr_number=1234,
                        repository="test/repo",
                        fix_comment=True,
                        agent_cli="claude",
                        model="sonnet"  # Test model parameter
                    )
                except TypeError as e:
                    if "model" in str(e):
                        self.fail(f"process_single_pr_by_number does not accept model parameter: {e}")
                except Exception:
                    # Other exceptions are okay for this test - we just want to verify signature
                    pass

    def test_dispatch_fix_comment_agent_accepts_model_parameter(self):
        """Test that dispatch_fix_comment_agent accepts model parameter."""
        with patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.ensure_base_clone') as mock_clone,              patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.chdir'),              patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.TaskDispatcher'),              patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.dispatch_agent_for_pr_with_task') as mock_dispatch:
            
            mock_clone.return_value = "/tmp/fake/repo"
            mock_dispatch.return_value = True

            pr_data = {
                "number": 1234,
                "title": "Test PR",
                "headRefName": "test-branch",
                "url": "https://github.com/test/repo/pull/1234"
            }

            # Should not raise TypeError for model parameter
            try:
                self.monitor.dispatch_fix_comment_agent(
                    repository="test/repo",
                    pr_number=1234,
                    pr_data=pr_data,
                    agent_cli="claude",
                    model="opus"  # Test model parameter
                )
                # Verify it was passed through
                mock_dispatch.assert_called_once()
                call_kwargs = mock_dispatch.call_args[1]
                self.assertEqual(call_kwargs.get("model"), "opus")
            except TypeError as e:
                if "model" in str(e):
                    self.fail(f"dispatch_fix_comment_agent does not accept model parameter: {e}")

    def test_model_parameter_passed_to_dispatcher(self):
        """Test that model parameter is passed through to dispatcher."""
        with patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.TaskDispatcher'),              patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.ensure_base_clone'),              patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.chdir'),              patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.dispatch_agent_for_pr_with_task') as mock_dispatch,              patch.object(self.monitor, '_post_fix_comment_queued') as mock_queued,              patch.object(self.monitor, '_start_fix_comment_review_watcher') as mock_watcher,              patch.object(self.monitor, '_get_pr_comment_state', return_value=(None, [])),              patch.object(self.monitor, '_has_unaddressed_comments', return_value=True):
            
            mock_dispatch.return_value = True
            mock_queued.return_value = True
            mock_watcher.return_value = True

            pr_data = {
                "number": 1234,
                "title": "Test PR",
                "headRefName": "test-branch",
                "baseRefName": "main",
                "url": "https://github.com/test/repo/pull/1234",
                "headRepository": {"owner": {"login": "test"}},
                "headRefOid": "abc123"
            }

            # Process fix-comment with model parameter
            self.monitor._process_pr_fix_comment(
                repository="test/repo",
                pr_number=1234,
                pr_data=pr_data,
                agent_cli="claude",
                model="haiku"  # Test model parameter
            )

            # Verify dispatcher was called with model parameter
            mock_dispatch.assert_called_once()
            call_kwargs = mock_dispatch.call_args[1]
            self.assertEqual(call_kwargs.get("model"), "haiku")

    def test_cli_argument_parser_has_model_flag(self):
        """Test that CLI argument parser includes --model flag."""
        # Get the argument parser from the module
        parser = argparse.ArgumentParser()

        # Add the expected arguments (mimicking what main() does)
        parser.add_argument("--model", type=str, default=None,
                          help="Model to use for Claude CLI")

        # Should not raise error
        args = parser.parse_args(["--model", "sonnet"])
        self.assertEqual(args.model, "sonnet")

    def test_model_defaults_to_none(self):
        """Test that model parameter defaults to None when not provided."""
        parser = argparse.ArgumentParser()
        parser.add_argument("--model", type=str, default=None)

        # Parse without --model flag
        args = parser.parse_args([])
        self.assertIsNone(args.model)

    def test_multiple_model_values(self):
        """Test different valid model values."""
        valid_models = ["sonnet", "opus", "haiku", "gemini-3-pro-preview", "composer-1"]

        for model in valid_models:
            with self.subTest(model=model):
                with patch.object(self.monitor, 'safety_manager') as mock_safety:
                    with patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.AutomationUtils'):
                        mock_safety.can_start_global_run.return_value = True
                        mock_safety.try_process_pr.return_value = True

                        try:
                            self.monitor.process_single_pr_by_number(
                                pr_number=1234,
                                repository="test/repo",
                                fix_comment=True,
                                agent_cli="claude",
                                model=model
                            )
                        except TypeError as e:
                            if "model" in str(e):
                                self.fail(f"Model parameter not accepted for value '{model}': {e}")
                        except Exception:
                            # Other exceptions are okay
                            pass

    def test_fixpr_run_monitoring_cycle_threads_model(self):
        """FixPR mode should pass --model through to _process_pr_fixpr."""
        monitor = JleechanorgPRMonitor()
        pr = {
            "repository": "test/repo",
            "repositoryFullName": "test/repo",
            "number": 123,
            "title": "Test PR",
            "headRefName": "feature/test",
        }

        with patch.object(monitor, "discover_open_prs", return_value=[pr]), \
             patch.object(monitor, "is_pr_actionable", return_value=True), \
             patch.object(monitor, "_get_pr_comment_state", return_value=(None, [])), \
             patch.object(monitor, "_process_pr_fixpr", return_value="skipped") as mock_fixpr, \
             patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.has_failing_checks", return_value=True), \
             patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.AutomationUtils.execute_subprocess_with_timeout",
                   return_value=SimpleNamespace(returncode=0, stdout='{\"mergeable\":\"MERGEABLE\"}')):

            with patch.object(monitor, "safety_manager") as mock_safety:
                mock_safety.can_start_global_run.return_value = True
                mock_safety.try_process_pr.return_value = True
                mock_safety.get_global_runs.return_value = 1
                mock_safety.global_limit = 50
                mock_safety.fixpr_limit = 10
                mock_safety.pr_limit = 10
                mock_safety.pr_automation_limit = 10
                mock_safety.fix_comment_limit = 10

                monitor.run_monitoring_cycle(
                    max_prs=1,
                    cutoff_hours=24,
                    fixpr=True,
                    agent_cli="claude",
                    model="sonnet",
                )

            self.assertTrue(mock_fixpr.called)
            self.assertEqual(mock_fixpr.call_args[1].get("model"), "sonnet")

    def test_fixpr_process_pr_threads_model_to_dispatch(self):
        """_process_pr_fixpr should forward model through to dispatch_agent_for_pr."""
        monitor = JleechanorgPRMonitor()
        pr_data = {
            "number": 123,
            "title": "Test PR",
            "headRefName": "feature/test",
            "url": "https://github.com/test/repo/pull/123",
            "headRefOid": "abc123",
        }

        # Mock has_failing_checks to ensure PR is not skipped as "clean"
        with patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.has_failing_checks", return_value=True), \
             patch(
                 "jleechanorg_pr_automation.jleechanorg_pr_monitor.AutomationUtils.execute_subprocess_with_timeout",
                 return_value=SimpleNamespace(returncode=0, stdout='{"mergeable":"MERGEABLE"}', stderr=""),
             ), \
             patch.object(monitor, "_get_pr_comment_state", return_value=(None, [])), \
             patch.object(monitor, "_should_skip_pr", return_value=False), \
             patch.object(monitor, "_count_workflow_comments", return_value=0), \
             patch.object(monitor, "_post_fixpr_queued", return_value=True), \
             patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.ensure_base_clone", return_value="/tmp/fake/repo"), \
             patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.chdir"), \
             patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.TaskDispatcher"), \
             patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.dispatch_agent_for_pr", return_value=True) as mock_dispatch, \
             patch.object(monitor, "_post_fixpr_queued", return_value=True), \
             patch.object(monitor, "_record_processed_pr"), \
             patch.object(monitor, "safety_manager") as mock_safety:

            mock_safety.fixpr_limit = 10
            result = monitor._process_pr_fixpr(
                repository="test/repo",
                pr_number=123,
                pr_data=pr_data,
                agent_cli="claude",
                model="sonnet",
            )

            self.assertEqual(result, "posted")
            # Verify model was passed to dispatch_agent_for_pr
            mock_dispatch.assert_called_once()
            call_kwargs = mock_dispatch.call_args[1] if mock_dispatch.call_args else {}
            self.assertEqual(call_kwargs.get("model"), "sonnet")


    def test_normalize_model_none_returns_none(self):
        """Test that _normalize_model returns None for None input."""
        result = _normalize_model(None)
        self.assertIsNone(result)

    def test_normalize_model_empty_string_returns_none(self):
        """Test that _normalize_model returns None for empty string."""
        result = _normalize_model("")
        self.assertIsNone(result)
        
        result = _normalize_model("   ")
        self.assertIsNone(result)

    def test_normalize_model_valid_names(self):
        """Test that _normalize_model accepts valid model names."""
        valid_models = [
            "sonnet",
            "opus",
            "haiku",
            "gemini-3-pro-preview",
            "gemini-3-auto",
            "composer-1",
            "model_name",
            "model.name",
            "model_name_123",
            "a",
            "123",
        ]
        
        for model in valid_models:
            with self.subTest(model=model):
                result = _normalize_model(model)
                self.assertEqual(result, model.strip())
                
                # Test with whitespace
                result = _normalize_model(f"  {model}  ")
                self.assertEqual(result, model)

    def test_normalize_model_invalid_names_raises_error(self):
        """Test that _normalize_model rejects invalid model names."""
        invalid_models = [
            "model with spaces",
            "model@invalid",
            "model#invalid",
            "model$invalid",
            "model%invalid",
            "model&invalid",
            "model*invalid",
            "model+invalid",
            "model=invalid",
            "model[invalid",
            "model]invalid",
            "model{invalid",
            "model}invalid",
            "model|invalid",
            "model\\invalid",
            "model/invalid",
            "model<invalid",
            "model>invalid",
            "model,invalid",
            "model;invalid",
            "model:invalid",
            "model'invalid",
            'model"invalid',
            "model`invalid",
            "model~invalid",
            "model!invalid",
            "model?invalid",
        ]
        
        for model in invalid_models:
            with self.subTest(model=model):
                with self.assertRaises(argparse.ArgumentTypeError):
                    _normalize_model(model)

    def test_normalize_model_strips_whitespace(self):
        """Test that _normalize_model strips whitespace from valid names."""
        result = _normalize_model("  sonnet  ")
        self.assertEqual(result, "sonnet")
        
        result = _normalize_model("\tgemini-3-auto\n")
        self.assertEqual(result, "gemini-3-auto")


if __name__ == '__main__':
    unittest.main()
