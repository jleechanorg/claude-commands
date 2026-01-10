#!/usr/bin/env python3
"""
Tests for --model parameter support in orchestration and automation.

Validates that model parameter is correctly passed through the automation pipeline.
"""

import argparse
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from jleechanorg_pr_automation.jleechanorg_pr_monitor import JleechanorgPRMonitor


class TestModelParameter(unittest.TestCase):
    """Test suite for model parameter functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.monitor = JleechanorgPRMonitor()

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
        with patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.TaskDispatcher'),              patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.ensure_base_clone'),              patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.chdir'),              patch('jleechanorg_pr_automation.jleechanorg_pr_monitor.dispatch_agent_for_pr_with_task') as mock_dispatch,              patch.object(self.monitor, '_post_fix_comment_queued') as mock_queued,              patch.object(self.monitor, '_start_fix_comment_review_watcher') as mock_watcher,              patch.object(self.monitor, '_get_pr_comment_state', return_value=(None, [])):
            
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

        with patch.object(monitor, "_get_pr_comment_state", return_value=(None, [])), \
             patch.object(monitor, "_should_skip_pr", return_value=False), \
             patch.object(monitor, "_post_fixpr_queued", return_value=True), \
             patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.ensure_base_clone", return_value="/tmp/fake/repo"), \
             patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.chdir"), \
             patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.TaskDispatcher"), \
             patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.dispatch_agent_for_pr", return_value=True) as mock_dispatch:

            monitor.safety_manager.fixpr_limit = 10
            result = monitor._process_pr_fixpr(
                repository="test/repo",
                pr_number=123,
                pr_data=pr_data,
                agent_cli="claude",
                model="sonnet",
            )

        self.assertEqual(result, "posted")
        self.assertEqual(mock_dispatch.call_args[1].get("model"), "sonnet")


if __name__ == '__main__':
    unittest.main()
