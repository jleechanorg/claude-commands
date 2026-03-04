#!/usr/bin/env python3
"""TDD tests for runner.py (ai_orch entry point)."""

import subprocess
import sys
import unittest
from unittest.mock import patch

# Add project root for imports
import os

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from orchestration.runner import main


class TestRunnerWorktreeGuard(unittest.TestCase):
    """Test --worktree requires --async (PR #5824 fix)."""

    def test_worktree_without_async_returns_exit_2(self):
        """--worktree without --async must fail with exit code 2."""
        with patch("sys.argv", ["ai_orch", "run", "--worktree", "some task"]):
            rc = main()
        self.assertEqual(rc, 2, "Should return 2 when --worktree used without --async")

    def test_worktree_without_async_prints_error(self):
        """--worktree without --async must print clear error message."""
        with patch("sys.argv", ["ai_orch", "run", "--worktree", "task"]):
            with patch("sys.stdout") as mock_stdout:
                main()
                output = "".join(c[0][0] for c in mock_stdout.write.call_args_list if c[0])
                self.assertIn("--worktree requires --async", output)


class TestRunnerHelp(unittest.TestCase):
    """Test runner help and version."""

    def test_version_flag_exits_zero(self):
        """--version triggers sys.exit(0) via argparse."""
        exit_codes = []

        def capture_exit(code=0):
            exit_codes.append(code)
            raise SystemExit(code)

        with patch("sys.argv", ["ai_orch", "--version"]):
            with patch("sys.exit", side_effect=capture_exit):
                with self.assertRaises(SystemExit):
                    main()
        self.assertEqual(exit_codes, [0])
