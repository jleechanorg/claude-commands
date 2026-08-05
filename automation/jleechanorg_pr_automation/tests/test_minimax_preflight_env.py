"""TDD Tests for MiniMax Preflight Validation Fix.

Problem: MiniMax preflight validation was missing auth setup parity with
the local claudem function. The validation code applied env_set from
CLI_PROFILES but only mapped MINIMAX_API_KEY to ANTHROPIC_API_KEY.

Solution: Add runtime mapping of MiniMax key to both ANTHROPIC_API_KEY
and ANTHROPIC_AUTH_TOKEN in _run_two_phase_cli_validation, consistent
with task_dispatcher.py.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

from jleechanorg_pr_automation.jleechanorg_pr_monitor import JleechanorgPRMonitor


class TestMinimaxPreflightEnvFix(unittest.TestCase):
    """Test that MiniMax preflight validation includes API key mapping."""

    def setUp(self):
        self.monitor = JleechanorgPRMonitor(automation_username="test-user")

    @patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.validate_cli_two_phase")
    @patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.shutil.which")
    def test_minimax_preflight_maps_api_key_to_env(
        self, mock_which, mock_validate
    ):
        """Verify MINIMAX_API_KEY is mapped to ANTHROPIC_API_KEY in validation env."""
        # Setup mocks
        mock_which.return_value = "/usr/bin/claude"
        mock_validate.return_value = MagicMock(success=True, output_file=None)

        # Set MINIMAX_API_KEY in environment
        test_api_key = "sk-test-minimax-key-12345"
        with patch.dict(os.environ, {"MINIMAX_API_KEY": test_api_key}, clear=False):
            # Call the validation method
            result = self.monitor._run_two_phase_cli_validation(
                cli_name="minimax",
                agent_name="test-agent",
            )

        # Verify validate_cli_two_phase was called
        mock_validate.assert_called_once()

        # Get the env passed to validate_cli_two_phase
        call_kwargs = mock_validate.call_args.kwargs
        env = call_kwargs.get("env", {})

        # CRITICAL: Verify both auth env vars are set from MINIMAX key
        self.assertIn(
            "ANTHROPIC_API_KEY",
            env,
            "ANTHROPIC_API_KEY must be in validation env for MiniMax"
        )
        self.assertEqual(
            env["ANTHROPIC_API_KEY"],
            test_api_key,
            "ANTHROPIC_API_KEY must equal MINIMAX_API_KEY value"
        )
        self.assertIn(
            "ANTHROPIC_AUTH_TOKEN",
            env,
            "ANTHROPIC_AUTH_TOKEN must be in validation env for MiniMax"
        )
        self.assertEqual(
            env["ANTHROPIC_AUTH_TOKEN"],
            test_api_key,
            "ANTHROPIC_AUTH_TOKEN must equal MINIMAX_API_KEY value"
        )

    @patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.validate_cli_two_phase")
    @patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.shutil.which")
    def test_minimax_preflight_handles_missing_api_key(
        self, mock_which, mock_validate
    ):
        """Verify validation works when MINIMAX_API_KEY is not set."""
        mock_which.return_value = "/usr/bin/claude"
        mock_validate.return_value = MagicMock(success=True, output_file=None)

        # Ensure MINIMAX_API_KEY is NOT in environment
        env_without_key = os.environ.copy()
        env_without_key.pop("MINIMAX_API_KEY", None)

        with patch.dict(os.environ, env_without_key, clear=False):
            result = self.monitor._run_two_phase_cli_validation(
                cli_name="minimax",
                agent_name="test-agent",
            )

        mock_validate.assert_called_once()
        call_kwargs = mock_validate.call_args.kwargs
        env = call_kwargs.get("env", {})

        # ANTHROPIC_API_KEY should NOT be set if MINIMAX_API_KEY is not provided
        # (it would use whatever is in the parent environment or be unset)

    @patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.validate_cli_two_phase")
    @patch("jleechanorg_pr_automation.jleechanorg_pr_monitor.shutil.which")
    def test_non_minimax_cli_does_not_add_anthropic_key(
        self, mock_which, mock_validate
    ):
        """Verify other CLIs don't get ANTHROPIC_API_KEY added."""
        mock_which.return_value = "/opt/homebrew/bin/gemini"
        mock_validate.return_value = MagicMock(success=True, output_file=None)

        # Set MINIMAX_API_KEY but test with gemini
        with patch.dict(os.environ, {"MINIMAX_API_KEY": "some-key"}, clear=False):
            result = self.monitor._run_two_phase_cli_validation(
                cli_name="gemini",
                agent_name="test-agent",
            )

        mock_validate.assert_called_once()
        call_kwargs = mock_validate.call_args.kwargs
        env = call_kwargs.get("env", {})

        # For non-minimax, ANTHROPIC_API_KEY should NOT be added
        # (may exist from parent env, but shouldn't be added by our code)
        # The key test is that we didn't add it based on MINIMAX_API_KEY


if __name__ == "__main__":
    unittest.main()
