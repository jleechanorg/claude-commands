#!/usr/bin/env python3
"""
Comprehensive tests for main copilot.py orchestrator

Tests GitHub API integration, comment processing, reply posting,
and the coordination between modular components.
"""

import unittest
import sys
import os
import json
from unittest.mock import patch, MagicMock, call
import subprocess

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock the modular imports before importing copilot
sys.modules['copilot_analyzer'] = MagicMock()
sys.modules['copilot_implementer'] = MagicMock() 
sys.modules['copilot_safety'] = MagicMock()
sys.modules['copilot_verifier'] = MagicMock()

import copilot
from copilot import GitHubCopilotProcessor


class TestGitHubCopilotProcessor(unittest.TestCase):
    """Test GitHubCopilotProcessor class functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.processor = GitHubCopilotProcessor(pr_number="123", monitor_mode=False)
        self.test_pr_data = {
            "number": 123,
            "title": "Test PR",
            "state": "open",
            "user": {"login": "testuser"},
            "html_url": "https://github.com/test/repo/pull/123"
        }
        
    @patch('subprocess.run')
    def test_get_repo_info_success(self, mock_run):
        """Test successful repository info extraction"""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="jleechanorg/worldarchitect.ai",
            stderr=""
        )
        
        result = self.processor._get_repo_info()
        
        # Should extract owner and repo from git remote
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

    def test_monitor_mode_initialization(self):
        """Test monitor mode vs normal mode initialization"""
        monitor_processor = GitHubCopilotProcessor(monitor_mode=True)
        normal_processor = GitHubCopilotProcessor(monitor_mode=False)
        
        self.assertTrue(monitor_processor.monitor_mode)
        self.assertFalse(normal_processor.monitor_mode)

    def test_pr_number_detection(self):
        """Test PR number detection from various sources"""
        # Test explicit PR number
        processor_with_pr = GitHubCopilotProcessor(pr_number="456")
        self.assertEqual(processor_with_pr.pr_number, "456")
        
        # Test auto-detection (would normally call get_pr_number method)
        processor_auto = GitHubCopilotProcessor(pr_number=None)
        self.assertIsNone(processor_auto.pr_number)


class TestCommentFiltering(unittest.TestCase):
    """Test comment extraction and filtering"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.processor = GitHubCopilotProcessor(pr_number="123", monitor_mode=False)
        self.sample_user_comments = [
            {
                "id": 1,
                "body": "This looks good to me!",
                "user": "reviewer1",
                "created_at": "2025-07-18T10:00:00Z",
                "type": "user"
            },
            {
                "id": 2, 
                "body": "🔄 **ACKNOWLEDGED**: Previous comment addressed",
                "user": "jleechan2015",
                "created_at": "2025-07-18T11:00:00Z",
                "type": "user"
            },
            {
                "id": 3,
                "body": "Please fix this issue",
                "user": "jleechan2015",
                "created_at": "2025-07-18T12:00:00Z",
                "type": "user"
            }
        ]
        
        self.sample_categorized_comments = {
            "user_comments": self.sample_user_comments,
            "copilot_suggestions": [],
            "coderabbit_suggestions": []
        }

    def test_filter_user_comments_basic(self):
        """Test basic filtering of user comments"""
        filtered = self.processor._filter_user_comments(self.sample_categorized_comments)
        
        # Should filter out automated acknowledgment but keep others
        self.assertEqual(len(filtered), 2)
        # Should have reviewer comment and real jleechan comment
        comment_ids = [c["id"] for c in filtered]
        self.assertIn(1, comment_ids)  # reviewer comment
        self.assertIn(3, comment_ids)  # real jleechan comment
        self.assertNotIn(2, comment_ids)  # filtered automated reply

    def test_filter_sophisticated_automated_replies(self):
        """Test filtering of sophisticated automated replies (bug fix test)"""
        sophisticated_replies = [
            {
                "id": 4,
                "body": "✅ **IMPLEMENTED**: Enhanced error handling added",
                "user": "jleechan2015",
                "created_at": "2025-07-18T13:00:00Z",
                "type": "user"
            },
            {
                "id": 5,
                "body": "CommentResponse(comment_id='123', response_type=<ResponseType.ACKNOWLEDGED>)",
                "user": "jleechan2015", 
                "created_at": "2025-07-18T14:00:00Z",
                "type": "user"
            }
        ]
        
        test_comments = self.sample_user_comments + sophisticated_replies
        categorized = {"user_comments": test_comments, "copilot_suggestions": [], "coderabbit_suggestions": []}
        
        filtered = self.processor._filter_user_comments(categorized)
        
        # Should filter out all automated replies including sophisticated ones
        comment_ids = [c["id"] for c in filtered]
        self.assertIn(1, comment_ids)  # reviewer comment
        self.assertIn(3, comment_ids)  # real jleechan comment
        self.assertNotIn(2, comment_ids)  # basic automated reply
        self.assertNotIn(4, comment_ids)  # sophisticated automated reply
        self.assertNotIn(5, comment_ids)  # object repr automated reply

    def test_coderabbit_comment_filtering(self):
        """Test filtering of CodeRabbit comments"""
        coderabbit_comments = [
            {
                "id": 10,
                "body": "Consider adding error handling here",
                "user": "coderabbit[bot]",
                "type": "coderabbit"
            },
            {
                "id": 11,
                "body": "Thank you for the update @jleechan2015",
                "user": "coderabbit[bot]", 
                "type": "coderabbit"
            }
        ]
        
        categorized = {
            "user_comments": [],
            "copilot_suggestions": [],
            "coderabbit_suggestions": coderabbit_comments
        }
        
        filtered = self.processor._filter_coderabbit_comments(categorized)
        
        # Should filter out thank you messages
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["id"], 10)  # Keep suggestion, filter thank you


class TestReplyPosting(unittest.TestCase):
    """Test reply posting with enhanced fallback mechanism"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.processor = GitHubCopilotProcessor(pr_number="123", monitor_mode=False)
        self.test_comment = {
            "id": 1,
            "body": "Consider adding error handling here",
            "user": "reviewer1",
            "type": "inline"
        }

    def test_format_reply_content_basic(self):
        """Test basic reply content formatting"""
        reply = self.processor.format_reply_content(self.test_comment, "EVALUATE", "Needs review")
        
        # Should return a formatted reply string
        self.assertIsInstance(reply, str)
        self.assertGreater(len(reply), 0)

    def test_format_reply_content_with_modular_architecture(self):
        """Test reply formatting with modular architecture"""
        # Mock modular architecture availability
        with patch('copilot.MODULAR_ARCHITECTURE_AVAILABLE', True):
            # Mock the analyzer and reporter
            mock_analyzer = MagicMock()
            mock_reporter = MagicMock()
            
            self.processor.analyzer = mock_analyzer
            self.processor.reporter = mock_reporter
            
            # Mock the categorize_comment to return a mock analyzed comment
            mock_analyzed_comment = MagicMock()
            mock_analyzed_comment.implementability.value = "manual"  # Will trigger acknowledged response
            mock_analyzer.categorize_comment.return_value = mock_analyzed_comment
            
            # Mock response object with response_text
            mock_response = MagicMock()
            mock_response.response_text = "✅ **ACKNOWLEDGED**: This is a sophisticated response"
            mock_reporter.generate_acknowledged_response.return_value = mock_response
            
            reply = self.processor.format_reply_content(self.test_comment, "", "")
            
            self.assertEqual(reply, "✅ **ACKNOWLEDGED**: This is a sophisticated response")

    def test_enhanced_fallback_mechanism(self):
        """Test the enhanced fallback mechanism that prevents object repr bug"""
        # Mock modular architecture with problematic response object
        with patch('copilot.MODULAR_ARCHITECTURE_AVAILABLE', True):
            mock_analyzer = MagicMock()
            mock_reporter = MagicMock()
            
            self.processor.analyzer = mock_analyzer
            self.processor.reporter = mock_reporter
            
            # Mock the categorize_comment to return a mock analyzed comment
            mock_analyzed_comment = MagicMock()
            mock_analyzed_comment.implementability.value = "manual"
            mock_analyzer.categorize_comment.return_value = mock_analyzed_comment
            
            # Mock response object WITHOUT response_text or content (the bug scenario)
            mock_response = MagicMock()
            # Remove the attributes to simulate the problematic case
            del mock_response.response_text
            del mock_response.content
            del mock_response.message 
            del mock_response.text
            del mock_response.body
            mock_reporter.generate_acknowledged_response.return_value = mock_response
            
            # Capture print statements for logging verification
            with patch('builtins.print') as mock_print:
                reply = self.processor.format_reply_content(self.test_comment, "", "")
                
                # Should use ultimate fallback instead of str(response)
                self.assertEqual(reply, "🔄 **ACKNOWLEDGED**: Comment acknowledged (automated response generation failed)")
                self.assertNotIn("CommentResponse(", reply)  # Ensure no object repr
                self.assertNotIn("MagicMock", reply)  # Ensure no mock object repr
                
                # Should log warning about missing attributes
                print_calls = [call.args[0] for call in mock_print.call_args_list]
                warning_logged = any("Warning: Response object missing expected attributes" in str(call) for call in print_calls)
                self.assertTrue(warning_logged)

    def test_basic_reply_fallback(self):
        """Test fallback to basic reply when modular architecture fails"""
        # Mock modular architecture failure
        with patch('copilot.MODULAR_ARCHITECTURE_AVAILABLE', False):
            reply = self.processor.format_reply_content(self.test_comment, "EVALUATE", "Needs review")
            
            # Should use basic reply generation
            self.assertIsInstance(reply, str)
            self.assertGreater(len(reply), 0)
            # Basic replies should contain some decision or acknowledgment
            self.assertTrue(any(keyword in reply.upper() for keyword in ["GOOD", "SUGGESTION", "ACKNOWLEDGED", "EVALUATE"]))


class TestMonitorMode(unittest.TestCase):
    """Test monitor mode functionality"""
    
    def test_monitor_mode_detection(self):
        """Test monitor mode vs normal mode behavior"""
        monitor_processor = GitHubCopilotProcessor(monitor_mode=True)
        normal_processor = GitHubCopilotProcessor(monitor_mode=False)
        
        self.assertTrue(monitor_processor.monitor_mode)
        self.assertFalse(normal_processor.monitor_mode)

    def test_monitor_mode_affects_reply_content(self):
        """Test that monitor mode generates appropriate responses"""
        # Force basic mode to avoid modular architecture interference
        with patch('copilot.MODULAR_ARCHITECTURE_AVAILABLE', False):
            monitor_processor = GitHubCopilotProcessor(monitor_mode=True)
            
            test_comment = {
                "id": 1,
                "body": "Consider adding error handling",
                "user": "reviewer1",
                "type": "inline"
            }
            
            # In monitor mode, should generate a response using basic reply system
            reply = monitor_processor.format_reply_content(test_comment, "", "")
            
            self.assertIsInstance(reply, str)
            self.assertGreater(len(reply), 0)
            
            # Monitor mode should generate meaningful content without mock objects
            self.assertNotIn("MagicMock", reply)
            self.assertNotIn("<Mock", reply)
            
            # Should contain some kind of acknowledgment or evaluation
            reply_upper = reply.upper()
            self.assertTrue(any(keyword in reply_upper for keyword in [
                "GOOD", "SUGGESTION", "ACKNOWLEDGED", "EVALUATE", "CONSIDER", "AUTOMATED", "THIS"
            ]))


class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases"""
    
    def test_processor_with_invalid_pr_number(self):
        """Test processor initialization with invalid PR number"""
        processor = GitHubCopilotProcessor(pr_number="invalid")
        
        # Should handle gracefully without crashing
        self.assertEqual(processor.pr_number, "invalid")

    def test_empty_comment_processing(self):
        """Test handling of empty comment lists"""
        processor = GitHubCopilotProcessor(pr_number="123", monitor_mode=False)
        
        # Test with empty categorized comments
        empty_categorized = {
            "user_comments": [],
            "copilot_suggestions": [],
            "coderabbit_suggestions": []
        }
        
        filtered_user = processor._filter_user_comments(empty_categorized)
        filtered_coderabbit = processor._filter_coderabbit_comments(empty_categorized)
        
        self.assertEqual(len(filtered_user), 0)
        self.assertEqual(len(filtered_coderabbit), 0)

    def test_malformed_comment_handling(self):
        """Test handling of malformed comment data"""
        processor = GitHubCopilotProcessor(pr_number="123", monitor_mode=False)
        
        malformed_comment = {
            "id": 1,
            # Missing body, user, etc.
        }
        
        # Should handle gracefully without crashing
        reply = processor.format_reply_content(malformed_comment, "", "")
        
        self.assertIsInstance(reply, str)
        self.assertGreater(len(reply), 0)


class TestIntegrationPoints(unittest.TestCase):
    """Test integration between orchestrator and modular components"""
    
    def test_modular_architecture_integration(self):
        """Test integration with modular architecture when available"""
        processor = GitHubCopilotProcessor(pr_number="123", monitor_mode=False)
        
        # Test that processor can handle both modular and basic modes
        test_comment = {
            "id": 1,
            "body": "Test comment",
            "user": "reviewer1"
        }
        
        # Should not crash regardless of modular architecture availability
        reply = processor.format_reply_content(test_comment, "", "")
        
        self.assertIsInstance(reply, str)
        self.assertGreater(len(reply), 0)

    def test_processor_initialization_components(self):
        """Test processor initializes with proper components"""
        processor = GitHubCopilotProcessor(pr_number="123", monitor_mode=False)
        
        # Check essential attributes exist
        self.assertTrue(hasattr(processor, 'pr_number'))
        self.assertTrue(hasattr(processor, 'monitor_mode'))
        self.assertTrue(hasattr(processor, 'fixes_applied'))
        self.assertTrue(hasattr(processor, 'warnings_found'))


class TestPerformanceOptimizations(unittest.TestCase):
    """Test performance optimizations and bug fixes"""
    
    def test_comment_filtering_reduces_load(self):
        """Test that comment filtering reduces processing load"""
        processor = GitHubCopilotProcessor(pr_number="123", monitor_mode=False)
        
        # Create many user comments with automated replies mixed in
        large_user_comment_list = []
        for i in range(20):
            # Add real comments
            large_user_comment_list.append({
                "id": i,
                "body": f"Real comment {i}",
                "user": f"reviewer{i}",
                "type": "user"
            })
            
            # Add automated replies that should be filtered
            large_user_comment_list.append({
                "id": 100+i,
                "body": f"🔄 **ACKNOWLEDGED**: Auto reply {i}",
                "user": "jleechan2015",
                "type": "user"
            })
        
        categorized = {
            "user_comments": large_user_comment_list,
            "copilot_suggestions": [],
            "coderabbit_suggestions": []
        }
        
        filtered = processor._filter_user_comments(categorized)
        
        # Should filter out automated replies, keeping only real comments
        self.assertEqual(len(filtered), 20)  # Only real comments
        self.assertLess(len(filtered), len(large_user_comment_list))  # Reduced load

    def test_sophisticated_reply_filtering(self):
        """Test filtering of sophisticated automated replies (prevents infinite loops)"""
        processor = GitHubCopilotProcessor(pr_number="123", monitor_mode=False)
        
        sophisticated_automated_replies = [
            {
                "id": 1,
                "body": "✅ **IMPLEMENTED**: Enhanced error handling added to improve robustness",
                "user": "jleechan2015",
                "type": "user"
            },
            {
                "id": 2,
                "body": "CommentResponse(comment_id='123', response_type=<ResponseType.ACKNOWLEDGED>, response_text='Fixed')",
                "user": "jleechan2015",
                "type": "user"
            },
            {
                "id": 3,
                "body": "This is a real comment from me",
                "user": "jleechan2015",
                "type": "user"
            }
        ]
        
        categorized = {
            "user_comments": sophisticated_automated_replies,
            "copilot_suggestions": [],
            "coderabbit_suggestions": []
        }
        
        filtered = processor._filter_user_comments(categorized)
        
        # Should filter out sophisticated automated replies but keep real comment
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["id"], 3)  # Only the real comment


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)