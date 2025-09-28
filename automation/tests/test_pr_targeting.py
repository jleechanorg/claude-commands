#!/usr/bin/env python3
"""
Test PR targeting functionality for jleechanorg_pr_monitor - Codex Strategy Tests Only
"""

import unittest
import sys
from pathlib import Path

# Add automation directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import after path setup
from jleechanorg_pr_monitor import JleechanorgPRMonitor


class TestPRTargeting(unittest.TestCase):
    """Test PR targeting functionality - Codex Strategy Only"""

    def test_extract_commit_marker(self):
        """Commit markers can be parsed from Codex comments"""
        monitor = JleechanorgPRMonitor()
        marker = monitor._extract_commit_marker(
            f"{monitor.CODEX_COMMENT_TEXT}\n\n"
            f"{monitor.CODEX_COMMIT_MARKER_PREFIX}abc123{monitor.CODEX_COMMIT_MARKER_SUFFIX}"
        )
        self.assertEqual(marker, "abc123")


if __name__ == '__main__':
    unittest.main()
