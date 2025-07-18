#!/usr/bin/env python3
"""
Comprehensive tests for copilot_analyzer.py

Tests comment parsing, categorization, and GitHub API integration.
"""

import unittest
import sys
import os
import subprocess
from unittest.mock import patch, MagicMock
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from copilot_analyzer import (
    CopilotAnalyzer,
    Comment,
    CommentType,
    Implementability,
    Priority,
    AnalysisResult
)


class TestCommentCategorization(unittest.TestCase):
    """Test comment categorization logic"""
    
    def setUp(self):
        self.analyzer = CopilotAnalyzer()
    
    def test_auto_fixable_unused_imports(self):
        """Test categorization of unused import comments"""
        comment = Comment(
            id="1",
            body="Please remove unused imports from this file",
            user="reviewer",
            comment_type=CommentType.INLINE
        )
        
        categorized = self.analyzer.categorize_comment(comment)
        
        self.assertEqual(categorized.implementability, Implementability.AUTO_FIXABLE)
        self.assertEqual(categorized.priority, Priority.HIGH)
        self.assertIn("auto_fix_unused_imports", categorized.suggested_actions)
    
    def test_auto_fixable_magic_numbers(self):
        """Test categorization of magic number comments"""
        comment = Comment(
            id="2",
            body="These magic numbers should be extracted to constants",
            user="reviewer",
            comment_type=CommentType.INLINE
        )
        
        categorized = self.analyzer.categorize_comment(comment)
        
        self.assertEqual(categorized.implementability, Implementability.AUTO_FIXABLE)
        self.assertIn("auto_fix_magic_numbers", categorized.suggested_actions)
    
    def test_auto_fixable_formatting(self):
        """Test categorization of formatting comments"""
        comment = Comment(
            id="3",
            body="Please fix the code formatting and import ordering",
            user="reviewer",
            comment_type=CommentType.INLINE
        )
        
        categorized = self.analyzer.categorize_comment(comment)
        
        self.assertEqual(categorized.implementability, Implementability.AUTO_FIXABLE)
        self.assertIn("auto_fix_formatting", categorized.suggested_actions)
    
    def test_manual_logic_changes(self):
        """Test categorization of manual logic comments"""
        comment = Comment(
            id="4",
            body="This business logic needs to be refactored for better clarity",
            user="reviewer",
            comment_type=CommentType.INLINE
        )
        
        categorized = self.analyzer.categorize_comment(comment)
        
        self.assertEqual(categorized.implementability, Implementability.MANUAL)
        self.assertEqual(categorized.priority, Priority.HIGH)
    
    def test_not_applicable_subjective(self):
        """Test categorization of subjective preference comments"""
        comment = Comment(
            id="5",
            body="Consider using a different approach here, might be better",
            user="reviewer",
            comment_type=CommentType.INLINE
        )
        
        categorized = self.analyzer.categorize_comment(comment)
        
        self.assertEqual(categorized.implementability, Implementability.NOT_APPLICABLE)
        self.assertEqual(categorized.priority, Priority.LOW)
    
    def test_default_categorization(self):
        """Test default categorization for unclear comments"""
        comment = Comment(
            id="6",
            body="Some unclear feedback that doesn't match patterns",
            user="reviewer",
            comment_type=CommentType.INLINE
        )
        
        categorized = self.analyzer.categorize_comment(comment)
        
        self.assertEqual(categorized.implementability, Implementability.MANUAL)
        self.assertEqual(categorized.priority, Priority.MEDIUM)


class TestGitHubAPIIntegration(unittest.TestCase):
    """Test GitHub API integration with mocking"""
    
    def setUp(self):
        self.analyzer = CopilotAnalyzer()
    
    @patch('subprocess.run')
    def test_extract_inline_comments(self, mock_run):
        """Test extraction of inline review comments"""
        # Mock GitHub API response
        mock_response = [
            {
                'id': 123,
                'body': 'Remove unused imports',
                'user': {'login': 'github-actions', 'type': 'Bot'},
                'path': 'src/main.py',
                'line': 5,
                'position': 10
            },
            {
                'id': 124,
                'body': 'Fix magic numbers',
                'user': {'login': 'coderabbit', 'type': 'Bot'},
                'path': 'src/utils.py',
                'line': 15,
                'position': 20
            }
        ]
        
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = json.dumps(mock_response)
        
        comments = self.analyzer._extract_inline_comments("123")
        
        self.assertEqual(len(comments), 2)
        self.assertEqual(comments[0].id, "123")
        self.assertEqual(comments[0].body, "Remove unused imports")
        self.assertEqual(comments[0].user, "github-actions")
        self.assertEqual(comments[0].comment_type, CommentType.INLINE)
        self.assertEqual(comments[0].file_path, "src/main.py")
        self.assertEqual(comments[0].line_number, 5)
    
    @patch('subprocess.run')
    def test_extract_general_comments(self, mock_run):
        """Test extraction of general PR comments"""
        # Mock GitHub API response
        mock_response = {
            'comments': [
                {
                    'id': 456,
                    'body': 'Overall good work, but consider fixing the formatting',
                    'author': {'login': 'jleechan2015'},
                    'createdAt': '2025-01-01T10:00:00Z',
                    'url': 'https://github.com/test/test/issues/1#issuecomment-456'
                }
            ]
        }
        
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = json.dumps(mock_response)
        
        comments = self.analyzer._extract_general_comments("123")
        
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0].id, "456")
        self.assertEqual(comments[0].user, "jleechan2015")
        self.assertEqual(comments[0].comment_type, CommentType.GENERAL)
    
    @patch('subprocess.run')
    def test_extract_ci_failures(self, mock_run):
        """Test extraction of CI failure information"""
        # Mock GitHub API response for CI status
        mock_response = {
            'statusCheckRollup': [
                {
                    'name': 'test-suite',
                    'conclusion': 'FAILURE',
                    'detailsUrl': 'https://github.com/test/actions/runs/123',
                    'context': 'Test suite failed'
                },
                {
                    'name': 'lint-check',
                    'conclusion': 'SUCCESS',
                    'detailsUrl': 'https://github.com/test/actions/runs/124',
                    'context': 'Linting passed'
                }
            ]
        }
        
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = json.dumps(mock_response)
        
        failures = self.analyzer.extract_ci_failures("123")
        
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]['name'], 'test-suite')
        self.assertEqual(failures[0]['conclusion'], 'FAILURE')
    
    @patch('subprocess.run')
    def test_api_error_handling(self, mock_run):
        """Test handling of GitHub API errors"""
        # Mock API failure
        mock_run.side_effect = subprocess.CalledProcessError(1, 'gh')
        
        comments = self.analyzer._extract_inline_comments("123")
        
        # Should return empty list on error
        self.assertEqual(len(comments), 0)
    
    @patch('subprocess.run')
    def test_invalid_json_handling(self, mock_run):
        """Test handling of invalid JSON responses"""
        # Mock invalid JSON response
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "invalid json {"
        
        comments = self.analyzer._extract_inline_comments("123")
        
        # Should return empty list on JSON parse error
        self.assertEqual(len(comments), 0)


class TestAnalysisWorkflow(unittest.TestCase):
    """Test the complete analysis workflow"""
    
    def setUp(self):
        self.analyzer = CopilotAnalyzer()
    
    @patch.object(CopilotAnalyzer, '_detect_pr_number')
    @patch.object(CopilotAnalyzer, 'extract_pr_comments')
    @patch.object(CopilotAnalyzer, 'extract_ci_failures')
    def test_analyze_pr_with_mixed_comments(self, mock_ci, mock_comments, mock_detect):
        """Test complete PR analysis with mixed comment types"""
        # Mock PR number detection
        mock_detect.return_value = "123"
        
        # Mock comments
        mock_comments.return_value = [
            Comment(
                id="1",
                body="Remove unused imports from main.py",
                user="github-actions",
                comment_type=CommentType.INLINE,
                file_path="main.py",
                line_number=5
            ),
            Comment(
                id="2",
                body="This business logic is complex and needs refactoring",
                user="reviewer",
                comment_type=CommentType.INLINE,
                file_path="business.py",
                line_number=100
            ),
            Comment(
                id="3",
                body="Consider using a different color scheme here",
                user="designer",
                comment_type=CommentType.GENERAL
            )
        ]
        
        # Mock CI failures
        mock_ci.return_value = [
            {
                'name': 'test-failure',
                'conclusion': 'FAILURE',
                'detailsUrl': 'https://test.com'
            }
        ]
        
        result = self.analyzer.analyze_pr()
        
        # Verify analysis results
        self.assertEqual(result.total_count, 3)
        self.assertEqual(result.auto_fixable_count, 1)  # Unused imports
        self.assertEqual(result.manual_count, 1)  # Business logic refactor
        self.assertEqual(result.not_applicable_count, 1)  # Color scheme
        self.assertEqual(len(result.ci_failures), 1)
    
    @patch.object(CopilotAnalyzer, '_detect_pr_number')
    @patch.object(CopilotAnalyzer, 'extract_pr_comments')
    def test_analyze_pr_no_comments(self, mock_comments, mock_detect):
        """Test analysis when no comments are found"""
        mock_detect.return_value = "123"
        mock_comments.return_value = []
        
        result = self.analyzer.analyze_pr()
        
        self.assertEqual(result.total_count, 0)
        self.assertEqual(result.auto_fixable_count, 0)
        self.assertEqual(result.manual_count, 0)
        self.assertEqual(result.not_applicable_count, 0)
    
    def test_analyze_pr_no_number(self):
        """Test analysis when no PR number can be detected"""
        with patch.object(self.analyzer, '_detect_pr_number', return_value=None):
            with self.assertRaises(ValueError):
                self.analyzer.analyze_pr()


class TestCommentFiltering(unittest.TestCase):
    """Test filtering of comments by user and type"""
    
    def setUp(self):
        self.analyzer = CopilotAnalyzer()
    
    @patch('subprocess.run')
    def test_bot_comment_filtering(self, mock_run):
        """Test that bot comments are properly filtered"""
        # Mock response with various user types
        mock_response = [
            {
                'id': 1,
                'body': 'Bot comment',
                'user': {'login': 'github-actions', 'type': 'Bot'},
                'path': 'test.py',
                'line': 1
            },
            {
                'id': 2,
                'body': 'User comment',
                'user': {'login': 'regular-user', 'type': 'User'},
                'path': 'test.py',
                'line': 2
            },
            {
                'id': 3,
                'body': 'CodeRabbit comment',
                'user': {'login': 'coderabbitai', 'type': 'Bot'},
                'path': 'test.py',
                'line': 3
            },
            {
                'id': 4,
                'body': 'Author comment',
                'user': {'login': 'jleechan2015', 'type': 'User'},
                'path': 'test.py',
                'line': 4
            }
        ]
        
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = json.dumps(mock_response)
        
        comments = self.analyzer._extract_inline_comments("123")
        
        # Should only include bot comments and jleechan2015 comments
        self.assertEqual(len(comments), 3)
        user_logins = [c.user for c in comments]
        self.assertIn('github-actions', user_logins)
        self.assertIn('coderabbitai', user_logins)
        self.assertIn('jleechan2015', user_logins)
        self.assertNotIn('regular-user', user_logins)


class TestPatternMatching(unittest.TestCase):
    """Test regex pattern matching for comment categorization"""
    
    def setUp(self):
        self.analyzer = CopilotAnalyzer()
    
    def test_case_insensitive_matching(self):
        """Test that pattern matching is case insensitive"""
        comment = Comment(
            id="1",
            body="REMOVE UNUSED IMPORTS",
            user="reviewer",
            comment_type=CommentType.INLINE
        )
        
        categorized = self.analyzer.categorize_comment(comment)
        
        self.assertEqual(categorized.implementability, Implementability.AUTO_FIXABLE)
        self.assertIn("auto_fix_unused_imports", categorized.suggested_actions)
    
    def test_partial_phrase_matching(self):
        """Test matching within larger text"""
        comment = Comment(
            id="1",
            body="The function looks good overall, but please remove unused import statements for cleaner code.",
            user="reviewer",
            comment_type=CommentType.INLINE
        )
        
        categorized = self.analyzer.categorize_comment(comment)
        
        self.assertEqual(categorized.implementability, Implementability.AUTO_FIXABLE)
        self.assertIn("auto_fix_unused_imports", categorized.suggested_actions)
    
    def test_multiple_pattern_matches(self):
        """Test handling when multiple patterns match"""
        comment = Comment(
            id="1",
            body="Please remove unused imports and fix the formatting",
            user="reviewer",
            comment_type=CommentType.INLINE
        )
        
        categorized = self.analyzer.categorize_comment(comment)
        
        # Should still be auto-fixable (first match wins)
        self.assertEqual(categorized.implementability, Implementability.AUTO_FIXABLE)
        # Should include the first matching action
        self.assertTrue(len(categorized.suggested_actions) > 0)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)