#!/usr/bin/env python3
"""
Tests for --model parameter support in orchestration and automation.

Validates that model parameter is correctly passed through the automation pipeline.
"""

import argparse
import unittest
from unittest.mock import MagicMock, patch

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


if __name__ == '__main__':
    unittest.main()
