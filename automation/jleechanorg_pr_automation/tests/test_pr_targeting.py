#!/usr/bin/env python3
"""
Test PR targeting functionality for jleechanorg_pr_monitor - Codex Strategy Tests Only
"""

import unittest

from jleechanorg_pr_automation.jleechanorg_pr_monitor import JleechanorgPRMonitor


class TestPRTargeting(unittest.TestCase):
    """Test PR targeting functionality - Codex Strategy Only"""

    def test_extract_commit_marker(self):
        """Commit markers can be parsed from Codex comments"""
        monitor = JleechanorgPRMonitor()
        test_comment = f"@codex @coderabbitai @copilot @cursor [AI automation] Test comment\n\n{monitor.CODEX_COMMIT_MARKER_PREFIX}abc123{monitor.CODEX_COMMIT_MARKER_SUFFIX}"
        marker = monitor._extract_commit_marker(test_comment)
        self.assertEqual(marker, "abc123")


if __name__ == '__main__':
    unittest.main()
