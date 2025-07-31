#!/usr/bin/env python3
"""
Test suite for PR Comment Formatter to ensure proper functionality.
"""

import json
import os
import tempfile
import unittest

from pr_comment_formatter import (
    CommentStatus,
    CopilotComment,
    PRCommentFormatter,
    PRCommentResponse,
    TaskItem,
    UserComment,
)


class TestCommentStatus(unittest.TestCase):
    """Test CommentStatus enum functionality."""

    def test_from_string(self):
        """Test converting strings to CommentStatus."""
        assert CommentStatus.from_string("resolved") == CommentStatus.RESOLVED
        assert CommentStatus.from_string("FIXED") == CommentStatus.FIXED
        assert CommentStatus.from_string("unknown") == CommentStatus.PENDING

    def test_status_values(self):
        """Test status values contain proper indicators."""
        assert CommentStatus.RESOLVED.value.startswith("✅")
        assert CommentStatus.REJECTED.value.startswith("❌")
        assert CommentStatus.ACKNOWLEDGED.value.startswith("🔄")


class TestUserComment(unittest.TestCase):
    """Test UserComment functionality."""

    def test_format_line_ref(self):
        """Test line reference formatting."""
        comment = UserComment(line_number=123, text="test", response="response")
        assert comment.format_line_ref() == "Line 123"

        comment_no_line = UserComment(text="test", response="response")
        assert comment_no_line.format_line_ref() == "General"


class TestCopilotComment(unittest.TestCase):
    """Test CopilotComment functionality."""

    def test_is_positive_status(self):
        """Test positive status detection."""
        comment = CopilotComment(
            description="test", status=CommentStatus.RESOLVED, reason="test reason"
        )
        assert comment.is_positive_status()

        comment_negative = CopilotComment(
            description="test", status=CommentStatus.REJECTED, reason="test reason"
        )
        assert not comment_negative.is_positive_status()


class TestTaskItem(unittest.TestCase):
    """Test TaskItem functionality."""

    def test_format_task(self):
        """Test task formatting."""
        task = TaskItem(
            description="Test task",
            details=["Detail 1", "Detail 2"],
            status=CommentStatus.RESOLVED,
        )

        formatted = task.format_task()
        assert "✅ RESOLVED Test task" in formatted
        assert "- Detail 1" in formatted
        assert "- Detail 2" in formatted

        # Test task without details
        simple_task = TaskItem(description="Simple task")
        simple_formatted = simple_task.format_task()
        assert simple_formatted == "✅ RESOLVED Simple task"


class TestPRCommentResponse(unittest.TestCase):
    """Test PRCommentResponse functionality."""

    def setUp(self):
        """Set up test response."""
        self.response = PRCommentResponse(summary_title="Test Summary")

    def test_add_task(self):
        """Test adding tasks."""
        self.response.add_task("Test task", ["detail1", "detail2"], CommentStatus.FIXED)

        assert len(self.response.tasks) == 1
        assert self.response.tasks[0].description == "Test task"
        assert self.response.tasks[0].details == ["detail1", "detail2"]
        assert self.response.tasks[0].status == CommentStatus.FIXED

    def test_add_user_comment(self):
        """Test adding user comments."""
        self.response.add_user_comment(
            123, "Test comment", "Test response", CommentStatus.ADDRESSED
        )

        assert len(self.response.user_comments) == 1
        assert self.response.user_comments[0].line_number == 123
        assert self.response.user_comments[0].text == "Test comment"
        assert self.response.user_comments[0].response == "Test response"
        assert self.response.user_comments[0].status == CommentStatus.ADDRESSED

    def test_add_copilot_comment(self):
        """Test adding Copilot comments."""
        self.response.add_copilot_comment(
            "Test description", CommentStatus.VALIDATED, "Test reason"
        )

        assert len(self.response.copilot_comments) == 1
        assert self.response.copilot_comments[0].description == "Test description"
        assert self.response.copilot_comments[0].status == CommentStatus.VALIDATED
        assert self.response.copilot_comments[0].reason == "Test reason"

    def test_format_response(self):
        """Test complete response formatting."""
        self.response.add_task("Test task", ["detail1"])
        self.response.add_user_comment(123, "Test comment", "Test response")
        self.response.add_copilot_comment(
            "Test copilot", CommentStatus.FIXED, "Test reason"
        )
        self.response.final_status = "All done"

        formatted = self.response.format_response()

        # Check main components are present
        assert "Summary: Test Summary" in formatted
        assert "✅ RESOLVED Test task" in formatted
        assert "✅ User Comments Addressed" in formatted
        assert "Line 123" in formatted
        assert "Test comment" in formatted
        assert "✅ Copilot Comments Status" in formatted
        assert "Test copilot" in formatted
        assert "✅ Final Status" in formatted
        assert "All done" in formatted

        # Check table formatting
        assert "| Comment" in formatted
        assert "| Status" in formatted
        assert "| Reason" in formatted


class TestPRCommentFormatter(unittest.TestCase):
    """Test PRCommentFormatter functionality."""

    def test_create_response(self):
        """Test creating new response."""
        response = PRCommentFormatter.create_response("Test Title")
        assert response.summary_title == "Test Title"
        assert len(response.tasks) == 0
        assert len(response.user_comments) == 0
        assert len(response.copilot_comments) == 0

    def test_from_json_string(self):
        """Test creating response from JSON string."""
        json_data = {
            "summary_title": "JSON Test",
            "tasks": [
                {
                    "description": "JSON task",
                    "details": ["detail1", "detail2"],
                    "status": "fixed",
                }
            ],
            "user_comments": [
                {
                    "line_number": 456,
                    "text": "JSON comment",
                    "response": "JSON response",
                    "status": "addressed",
                }
            ],
            "copilot_comments": [
                {
                    "description": "JSON copilot",
                    "status": "validated",
                    "reason": "JSON reason",
                }
            ],
            "final_status": "JSON final",
        }

        response = PRCommentFormatter.from_json(json_data)

        assert response.summary_title == "JSON Test"
        assert len(response.tasks) == 1
        assert response.tasks[0].description == "JSON task"
        assert response.tasks[0].status == CommentStatus.FIXED

        assert len(response.user_comments) == 1
        assert response.user_comments[0].line_number == 456
        assert response.user_comments[0].status == CommentStatus.ADDRESSED

        assert len(response.copilot_comments) == 1
        assert response.copilot_comments[0].status == CommentStatus.VALIDATED

        assert response.final_status == "JSON final"

    def test_from_json_file(self):
        """Test creating response from JSON file."""
        json_data = {
            "summary_title": "File Test",
            "tasks": [],
            "user_comments": [],
            "copilot_comments": [],
            "final_status": "File final",
        }

        # Create temporary JSON file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(json_data, f)
            temp_file = f.name

        try:
            with open(temp_file) as f:
                file_data = json.load(f)

            response = PRCommentFormatter.from_json(file_data)
            assert response.summary_title == "File Test"
            assert response.final_status == "File final"
        finally:
            os.unlink(temp_file)

    def test_generate_template(self):
        """Test template generation."""
        template = PRCommentFormatter.generate_template()

        # Check template contains expected elements
        assert "Summary: PR Updated & Comments Addressed" in template
        assert "✅ RESOLVED GitHub PR Description Updated" in template
        assert "✅ User Comments Addressed" in template
        assert "Line 486" in template
        assert "✅ Copilot Comments Status" in template
        assert "✅ Final Status" in template

        # Check table formatting
        assert "| Comment" in template
        assert "| Status" in template
        assert "| Reason" in template


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete workflow."""

    def test_complete_workflow(self):
        """Test complete workflow from creation to formatting."""
        # Create response
        response = PRCommentFormatter.create_response("Integration Test")

        # Add various elements
        response.add_task(
            "Integration task",
            ["Integration detail 1", "Integration detail 2"],
            CommentStatus.FIXED,
        )

        response.add_user_comment(
            789,
            "Integration user comment",
            "Integration user response",
            CommentStatus.RESOLVED,
        )

        response.add_copilot_comment(
            "Integration copilot comment",
            CommentStatus.VALIDATED,
            "Integration copilot reason",
        )

        response.final_status = "Integration complete"

        # Format and verify
        formatted = response.format_response()

        # Verify all components are present and properly formatted
        assert "Summary: Integration Test" in formatted
        assert "✅ FIXED Integration task" in formatted
        assert "- Integration detail 1" in formatted
        assert '1. Line 789 - "Integration user comment"' in formatted
        assert "✅ RESOLVED Integration user response" in formatted
        assert "| Integration copilot ... | VALIDATED" in formatted
        assert "Integration complete" in formatted

        # Test round-trip through JSON
        json_data = {
            "summary_title": response.summary_title,
            "tasks": [
                {
                    "description": task.description,
                    "details": task.details,
                    "status": task.status.name.lower(),
                }
                for task in response.tasks
            ],
            "user_comments": [
                {
                    "line_number": comment.line_number,
                    "text": comment.text,
                    "response": comment.response,
                    "status": comment.status.name.lower(),
                }
                for comment in response.user_comments
            ],
            "copilot_comments": [
                {
                    "description": comment.description,
                    "status": comment.status.name.lower(),
                    "reason": comment.reason,
                }
                for comment in response.copilot_comments
            ],
            "final_status": response.final_status,
        }

        response_from_json = PRCommentFormatter.from_json(json_data)
        formatted_from_json = response_from_json.format_response()

        # Should be identical
        assert formatted == formatted_from_json


if __name__ == "__main__":
    # Run all tests
    unittest.main(verbosity=2)
