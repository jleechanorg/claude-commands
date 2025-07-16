#!/usr/bin/env python3
"""
Test suite for PR Comment Formatter to ensure proper functionality.
"""

import unittest
import json
import tempfile
import os
from pr_comment_formatter import (
    PRCommentFormatter, 
    PRCommentResponse, 
    CommentStatus, 
    UserComment, 
    CopilotComment, 
    TaskItem
)


class TestCommentStatus(unittest.TestCase):
    """Test CommentStatus enum functionality."""
    
    def test_from_string(self):
        """Test converting strings to CommentStatus."""
        self.assertEqual(CommentStatus.from_string("resolved"), CommentStatus.RESOLVED)
        self.assertEqual(CommentStatus.from_string("FIXED"), CommentStatus.FIXED)
        self.assertEqual(CommentStatus.from_string("unknown"), CommentStatus.PENDING)
    
    def test_status_values(self):
        """Test status values contain proper indicators."""
        self.assertTrue(CommentStatus.RESOLVED.value.startswith("✅"))
        self.assertTrue(CommentStatus.REJECTED.value.startswith("❌"))
        self.assertTrue(CommentStatus.ACKNOWLEDGED.value.startswith("🔄"))


class TestUserComment(unittest.TestCase):
    """Test UserComment functionality."""
    
    def test_format_line_ref(self):
        """Test line reference formatting."""
        comment = UserComment(line_number=123, text="test", response="response")
        self.assertEqual(comment.format_line_ref(), "Line 123")
        
        comment_no_line = UserComment(text="test", response="response")
        self.assertEqual(comment_no_line.format_line_ref(), "General")


class TestCopilotComment(unittest.TestCase):
    """Test CopilotComment functionality."""
    
    def test_is_positive_status(self):
        """Test positive status detection."""
        comment = CopilotComment(
            description="test",
            status=CommentStatus.RESOLVED,
            reason="test reason"
        )
        self.assertTrue(comment.is_positive_status())
        
        comment_negative = CopilotComment(
            description="test",
            status=CommentStatus.REJECTED,
            reason="test reason"
        )
        self.assertFalse(comment_negative.is_positive_status())


class TestTaskItem(unittest.TestCase):
    """Test TaskItem functionality."""
    
    def test_format_task(self):
        """Test task formatting."""
        task = TaskItem(
            description="Test task",
            details=["Detail 1", "Detail 2"],
            status=CommentStatus.RESOLVED
        )
        
        formatted = task.format_task()
        self.assertIn("✅ RESOLVED Test task", formatted)
        self.assertIn("- Detail 1", formatted)
        self.assertIn("- Detail 2", formatted)
        
        # Test task without details
        simple_task = TaskItem(description="Simple task")
        simple_formatted = simple_task.format_task()
        self.assertEqual(simple_formatted, "✅ RESOLVED Simple task")


class TestPRCommentResponse(unittest.TestCase):
    """Test PRCommentResponse functionality."""
    
    def setUp(self):
        """Set up test response."""
        self.response = PRCommentResponse(summary_title="Test Summary")
    
    def test_add_task(self):
        """Test adding tasks."""
        self.response.add_task("Test task", ["detail1", "detail2"], CommentStatus.FIXED)
        
        self.assertEqual(len(self.response.tasks), 1)
        self.assertEqual(self.response.tasks[0].description, "Test task")
        self.assertEqual(self.response.tasks[0].details, ["detail1", "detail2"])
        self.assertEqual(self.response.tasks[0].status, CommentStatus.FIXED)
    
    def test_add_user_comment(self):
        """Test adding user comments."""
        self.response.add_user_comment(123, "Test comment", "Test response", CommentStatus.ADDRESSED)
        
        self.assertEqual(len(self.response.user_comments), 1)
        self.assertEqual(self.response.user_comments[0].line_number, 123)
        self.assertEqual(self.response.user_comments[0].text, "Test comment")
        self.assertEqual(self.response.user_comments[0].response, "Test response")
        self.assertEqual(self.response.user_comments[0].status, CommentStatus.ADDRESSED)
    
    def test_add_copilot_comment(self):
        """Test adding Copilot comments."""
        self.response.add_copilot_comment("Test description", CommentStatus.VALIDATED, "Test reason")
        
        self.assertEqual(len(self.response.copilot_comments), 1)
        self.assertEqual(self.response.copilot_comments[0].description, "Test description")
        self.assertEqual(self.response.copilot_comments[0].status, CommentStatus.VALIDATED)
        self.assertEqual(self.response.copilot_comments[0].reason, "Test reason")
    
    def test_format_response(self):
        """Test complete response formatting."""
        self.response.add_task("Test task", ["detail1"])
        self.response.add_user_comment(123, "Test comment", "Test response")
        self.response.add_copilot_comment("Test copilot", CommentStatus.FIXED, "Test reason")
        self.response.final_status = "All done"
        
        formatted = self.response.format_response()
        
        # Check main components are present
        self.assertIn("Summary: Test Summary", formatted)
        self.assertIn("✅ RESOLVED Test task", formatted)
        self.assertIn("✅ User Comments Addressed", formatted)
        self.assertIn("Line 123", formatted)
        self.assertIn("Test comment", formatted)
        self.assertIn("✅ Copilot Comments Status", formatted)
        self.assertIn("Test copilot", formatted)
        self.assertIn("✅ Final Status", formatted)
        self.assertIn("All done", formatted)
        
        # Check table formatting
        self.assertIn("| Comment", formatted)
        self.assertIn("| Status", formatted)
        self.assertIn("| Reason", formatted)


class TestPRCommentFormatter(unittest.TestCase):
    """Test PRCommentFormatter functionality."""
    
    def test_create_response(self):
        """Test creating new response."""
        response = PRCommentFormatter.create_response("Test Title")
        self.assertEqual(response.summary_title, "Test Title")
        self.assertEqual(len(response.tasks), 0)
        self.assertEqual(len(response.user_comments), 0)
        self.assertEqual(len(response.copilot_comments), 0)
    
    def test_from_json_string(self):
        """Test creating response from JSON string."""
        json_data = {
            "summary_title": "JSON Test",
            "tasks": [
                {
                    "description": "JSON task",
                    "details": ["detail1", "detail2"],
                    "status": "fixed"
                }
            ],
            "user_comments": [
                {
                    "line_number": 456,
                    "text": "JSON comment",
                    "response": "JSON response",
                    "status": "addressed"
                }
            ],
            "copilot_comments": [
                {
                    "description": "JSON copilot",
                    "status": "validated",
                    "reason": "JSON reason"
                }
            ],
            "final_status": "JSON final"
        }
        
        response = PRCommentFormatter.from_json(json_data)
        
        self.assertEqual(response.summary_title, "JSON Test")
        self.assertEqual(len(response.tasks), 1)
        self.assertEqual(response.tasks[0].description, "JSON task")
        self.assertEqual(response.tasks[0].status, CommentStatus.FIXED)
        
        self.assertEqual(len(response.user_comments), 1)
        self.assertEqual(response.user_comments[0].line_number, 456)
        self.assertEqual(response.user_comments[0].status, CommentStatus.ADDRESSED)
        
        self.assertEqual(len(response.copilot_comments), 1)
        self.assertEqual(response.copilot_comments[0].status, CommentStatus.VALIDATED)
        
        self.assertEqual(response.final_status, "JSON final")
    
    def test_from_json_file(self):
        """Test creating response from JSON file."""
        json_data = {
            "summary_title": "File Test",
            "tasks": [],
            "user_comments": [],
            "copilot_comments": [],
            "final_status": "File final"
        }
        
        # Create temporary JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_data, f)
            temp_file = f.name
        
        try:
            with open(temp_file, 'r') as f:
                file_data = json.load(f)
            
            response = PRCommentFormatter.from_json(file_data)
            self.assertEqual(response.summary_title, "File Test")
            self.assertEqual(response.final_status, "File final")
        finally:
            os.unlink(temp_file)
    
    def test_generate_template(self):
        """Test template generation."""
        template = PRCommentFormatter.generate_template()
        
        # Check template contains expected elements
        self.assertIn("Summary: PR Updated & Comments Addressed", template)
        self.assertIn("✅ RESOLVED GitHub PR Description Updated", template)
        self.assertIn("✅ User Comments Addressed", template)
        self.assertIn("Line 486", template)
        self.assertIn("✅ Copilot Comments Status", template)
        self.assertIn("✅ Final Status", template)
        
        # Check table formatting
        self.assertIn("| Comment", template)
        self.assertIn("| Status", template)
        self.assertIn("| Reason", template)


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
            CommentStatus.FIXED
        )
        
        response.add_user_comment(
            789,
            "Integration user comment",
            "Integration user response",
            CommentStatus.RESOLVED
        )
        
        response.add_copilot_comment(
            "Integration copilot comment",
            CommentStatus.VALIDATED,
            "Integration copilot reason"
        )
        
        response.final_status = "Integration complete"
        
        # Format and verify
        formatted = response.format_response()
        
        # Verify all components are present and properly formatted
        self.assertIn("Summary: Integration Test", formatted)
        self.assertIn("✅ FIXED Integration task", formatted)
        self.assertIn("- Integration detail 1", formatted)
        self.assertIn("1. Line 789 - \"Integration user comment\"", formatted)
        self.assertIn("✅ RESOLVED Integration user response", formatted)
        self.assertIn("| Integration copilot ... | VALIDATED", formatted)
        self.assertIn("Integration complete", formatted)
        
        # Test round-trip through JSON
        json_data = {
            "summary_title": response.summary_title,
            "tasks": [
                {
                    "description": task.description,
                    "details": task.details,
                    "status": task.status.name.lower()
                }
                for task in response.tasks
            ],
            "user_comments": [
                {
                    "line_number": comment.line_number,
                    "text": comment.text,
                    "response": comment.response,
                    "status": comment.status.name.lower()
                }
                for comment in response.user_comments
            ],
            "copilot_comments": [
                {
                    "description": comment.description,
                    "status": comment.status.name.lower(),
                    "reason": comment.reason
                }
                for comment in response.copilot_comments
            ],
            "final_status": response.final_status
        }
        
        response_from_json = PRCommentFormatter.from_json(json_data)
        formatted_from_json = response_from_json.format_response()
        
        # Should be identical
        self.assertEqual(formatted, formatted_from_json)


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)