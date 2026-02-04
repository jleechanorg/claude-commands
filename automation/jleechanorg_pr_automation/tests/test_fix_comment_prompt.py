#!/usr/bin/env python3
"""Tests for fix_comment prompt formatting."""

import unittest
from unittest.mock import MagicMock, patch
from automation.jleechanorg_pr_automation.jleechanorg_pr_monitor import JleechanorgPRMonitor

class TestFixCommentPrompt(unittest.TestCase):
    def test_fix_comment_prompt_forbids_gh_cli(self):
        monitor = JleechanorgPRMonitor(no_act=True)
        
        pr_data = {
            "headRefName": "feature/test-branch",
            "title": "Test PR"
        }
        
        # Call the method
        prompt = monitor._build_fix_comment_prompt_body(
            repository="owner/repo",
            pr_number=123,
            pr_data=pr_data,
            head_sha="abc1234",
            agent_cli="claude"
        )
        
        # Assertion: The prompt should NOT recommend gh pr comment
        # This test is expected to FAIL initially until we fix the monitor
        # Assertion: The prompt should NOT recommend gh pr comment as a Reply Method
        self.assertNotIn("- Issue/PR comments: `gh pr comment", prompt, "Prompt should NOT recommend using 'gh pr comment' as a method")
        self.assertNotIn("- Inline review comments: `gh api", prompt, "Prompt should NOT recommend using 'gh api' as a method")
        
        # Assertion: The prompt SHOULD recommend Python methods
        self.assertIn("post_pr_comment_python", prompt, "Prompt should recommend post_pr_comment_python")
        self.assertIn("requests.get", prompt, "Prompt should recommend requests.get for fetching feedback")

if __name__ == "__main__":
    unittest.main()
