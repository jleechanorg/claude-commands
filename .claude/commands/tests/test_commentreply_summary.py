#!/usr/bin/env python3
"""
Unit tests for commentreply.py post_consolidated_summary function.
specifically testing the total_issues calculation fix.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import json
from pathlib import Path

# Add parent directory (commands) to path to import commentreply
# __file__ is .claude/commands/tests/test_commentreply_summary.py
# parent -> tests
# parent.parent -> commands
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
# Also add _copilot_modules since commentreply imports from it
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_copilot_modules"))

import commentreply

class TestCommentReplySummary(unittest.TestCase):
    """Test post_consolidated_summary logic"""

    @patch("commentreply.os.path.exists", return_value=True)
    @patch("commentreply.os.unlink")
    @patch("commentreply.run_command")
    @patch("commentreply.tempfile.NamedTemporaryFile")
    def test_total_issues_calculation_fix(
        self, mock_tempfile, mock_run_command, mock_unlink, mock_exists
    ):
        """Test that total_issues sums actual issues, not metadata"""
        
        # mock run_command to return success
        # The function expects json output from gh api
        mock_run_command.return_value = (True, json.dumps({"html_url": "http://url"}), "")

        # Mock tempfile to capture writes
        mock_file = MagicMock()
        mock_tempfile.return_value.__enter__.return_value = mock_file
        mock_file.name = "/tmp/mock_file"

        # Sample responses data
        responses_data = {
            "responses": [
                # Response 1: Single issue
                {
                   "comment_id": "1",
                   "category": "ROUTINE",
                   "response": "FIXED"
                   # Single issue format (treated as 1 issue)
                },
                # Response 2: Multi-issue (3 issues)
                {
                    "comment_id": "2",
                    "analysis": {
                        "total_issues": 100, # Metadata says 100 (should be ignored)
                        "actionable": 100
                    },
                    "issues": [
                        {"category": "CRITICAL", "response": "FIXED"},
                        {"category": "CRITICAL", "response": "FIXED"},
                        {"category": "CRITICAL", "response": "FIXED"}
                    ]
                }
            ]
        }

        # Expected calculation:
        # Response 1: 1 issue
        # Response 2: 3 issues (len(issues))
        # Total: 4 issues (NOT 101 or 100)

        # Run the function
        commentreply.post_consolidated_summary(
            owner="owner",
            repo="repo",
            pr_number="123",
            collected_replies=[],
            responses_data=responses_data,
            commit_hash="abc",
            total_targets=4,
            already_replied_count=0
        )

        # Verify temp file write
        # It writes json.dumps({"body": ...})
        # Join all write calls if multiple (likely one write or multiple chunks)
        # Assuming one write or we capture arguments
        
        # Check all write calls
        written_content = ""
        for call in mock_file.write.call_args_list:
            args = call[0]
            written_content += args[0]
            
        # Parse the JSON written to file
        try:
            data = json.loads(written_content)
            body = data.get("body", "")
        except json.JSONDecodeError:
            self.fail(f"Could not parse JSON written to temp file: {written_content}")

        # Verify Total Issues count in the body
        # Expected: "Total Issues**: 4"
        self.assertIn("Total Issues**: 4", body)
        self.assertNotIn("Total Issues**: 101", body)
        self.assertNotIn("Total Issues**: 100", body)
        
        # Verify Critical count (3 from response 2)
        # and Routine count (1 from response 1)
        self.assertIn("Critical**: 3", body)
        self.assertIn("Routine**: 1", body)

if __name__ == "__main__":
    unittest.main()
