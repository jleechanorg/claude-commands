"""
Tests for Claude Service - Header Compliance Tracking

This module tests the Claude service header validation and compliance tracking functionality.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import constants

# Mock firebase_admin before importing services
mock_firestore = MagicMock()
mock_firestore.DELETE_FIELD = MagicMock(name="DELETE_FIELD")
mock_firestore.SERVER_TIMESTAMP = MagicMock(name="SERVER_TIMESTAMP")

sys.modules['firebase_admin.firestore'] = mock_firestore
sys.modules['firebase_admin'] = MagicMock()

# Mock firestore_service functions
sys.modules['firestore_service'] = MagicMock()

from claude_service import (
    validate_header_compliance,
    parse_header_components,
    process_claude_response,
    get_compliance_status,
    generate_compliance_alert,
    validate_multiple_responses
)


class TestHeaderValidation(unittest.TestCase):
    """Test header validation functionality."""
    
    def test_validate_header_compliance_valid_formats(self):
        """Test validation with valid header formats."""
        valid_headers = [
            "[Local: main | Remote: origin/main | PR: none]\nContent here",
            "[Local: feature-branch | Remote: origin/feature-branch | PR: #123 https://github.com/user/repo/pull/123]\nContent",
            "[Local: dev | Remote: upstream/dev | PR: #456 https://example.com/pr/456]\nMore content"
        ]
        
        for header in valid_headers:
            with self.subTest(header=header):
                self.assertTrue(validate_header_compliance(header))
    
    def test_validate_header_compliance_invalid_formats(self):
        """Test validation with invalid header formats."""
        invalid_headers = [
            "Content without header",
            "[Invalid format]\nContent",
            "[Local: main | Remote: origin/main]\nMissing PR field",
            "[Local: main | PR: none]\nMissing Remote field",
            "[Remote: origin/main | PR: none]\nMissing Local field",
            "",
            None
        ]
        
        for header in invalid_headers:
            with self.subTest(header=header):
                self.assertFalse(validate_header_compliance(header))
    
    def test_validate_header_compliance_edge_cases(self):
        """Test validation with edge cases."""
        edge_cases = [
            # Leading/trailing whitespace
            "   [Local: main | Remote: origin/main | PR: none]\nContent   ",
            # Multiple lines
            "[Local: main | Remote: origin/main | PR: none]\nLine 1\nLine 2",
            # Empty strings and None
            "",
            None,
            123,  # Non-string input
        ]
        
        expected_results = [True, True, False, False, False]
        
        for header, expected in zip(edge_cases, expected_results):
            with self.subTest(header=header):
                self.assertEqual(validate_header_compliance(header), expected)


class TestHeaderParsing(unittest.TestCase):
    """Test header component parsing functionality."""
    
    def test_parse_header_components_valid(self):
        """Test parsing valid headers."""
        header = "[Local: feature-branch | Remote: origin/main | PR: #123 https://github.com/user/repo/pull/123]\nContent"
        
        result = parse_header_components(header)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['local_branch'], 'feature-branch')
        self.assertEqual(result['remote_branch'], 'origin/main')
        self.assertEqual(result['pr_info'], '#123 https://github.com/user/repo/pull/123')
    
    def test_parse_header_components_invalid(self):
        """Test parsing invalid headers."""
        invalid_headers = [
            "Content without header",
            "[Invalid format]\nContent",
            "",
            None
        ]
        
        for header in invalid_headers:
            with self.subTest(header=header):
                result = parse_header_components(header)
                self.assertIsNone(result)
    
    def test_parse_header_components_edge_cases(self):
        """Test parsing edge cases."""
        # Header with spaces in branch names
        header = "[Local: feature/my-feature | Remote: origin/feature/my-feature | PR: none]\nContent"
        
        result = parse_header_components(header)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['local_branch'], 'feature/my-feature')
        self.assertEqual(result['remote_branch'], 'origin/feature/my-feature')
        self.assertEqual(result['pr_info'], 'none')


class TestClaudeResponseProcessing(unittest.TestCase):
    """Test Claude response processing functionality."""
    
    @patch('claude_service.track_header_compliance')
    @patch('claude_service.get_session_compliance_rate')
    def test_process_claude_response_valid_header(self, mock_get_rate, mock_track):
        """Test processing response with valid header."""
        mock_get_rate.return_value = 0.85
        
        session_id = 'test_session_123'
        response_text = '[Local: main | Remote: origin/main | PR: none]\nHello world'
        
        result = process_claude_response(session_id, response_text)
        
        # Verify result structure
        self.assertTrue(result['has_header'])
        self.assertEqual(result['compliance_rate'], 0.85)
        self.assertIsNotNone(result['header_components'])
        self.assertEqual(result['response_preview'], response_text[:100])
        
        # Verify backend calls
        mock_track.assert_called_once_with(session_id, response_text, True)
        mock_get_rate.assert_called_once_with(session_id)
    
    @patch('claude_service.track_header_compliance')
    @patch('claude_service.get_session_compliance_rate')
    def test_process_claude_response_invalid_header(self, mock_get_rate, mock_track):
        """Test processing response with invalid header."""
        mock_get_rate.return_value = 0.65
        
        session_id = 'test_session_123'
        response_text = 'Content without header'
        
        result = process_claude_response(session_id, response_text)
        
        # Verify result structure
        self.assertFalse(result['has_header'])
        self.assertEqual(result['compliance_rate'], 0.65)
        self.assertIsNone(result['header_components'])
        self.assertEqual(result['response_preview'], response_text[:100])
        
        # Verify backend calls
        mock_track.assert_called_once_with(session_id, response_text, False)
        mock_get_rate.assert_called_once_with(session_id)
    
    @patch('claude_service.track_header_compliance')
    @patch('claude_service.get_session_compliance_rate')
    def test_process_claude_response_error_handling(self, mock_get_rate, mock_track):
        """Test error handling in response processing."""
        mock_track.side_effect = Exception("Database error")
        mock_get_rate.return_value = 0.0
        
        session_id = 'test_session_123'
        response_text = 'Some content'
        
        result = process_claude_response(session_id, response_text)
        
        # Should return safe defaults on error
        self.assertFalse(result['has_header'])
        self.assertEqual(result['compliance_rate'], 0.0)
        self.assertIsNone(result['header_components'])


class TestComplianceStatus(unittest.TestCase):
    """Test compliance status functionality."""
    
    @patch('claude_service.get_session_compliance_rate')
    @patch('firestore_service.get_session_compliance_stats')
    def test_get_compliance_status_success(self, mock_get_stats, mock_get_rate):
        """Test successful compliance status retrieval."""
        mock_get_rate.return_value = 0.85
        mock_get_stats.return_value = {
            'total_responses': 10,
            'compliant_responses': 8
        }
        
        session_id = 'test_session_123'
        
        result = get_compliance_status(session_id)
        
        self.assertEqual(result['compliance_rate'], 0.85)
        self.assertTrue(result['is_compliant'])  # >= 0.8
        self.assertEqual(result['total_responses'], 10)
        self.assertEqual(result['compliant_responses'], 8)
    
    @patch('claude_service.get_session_compliance_rate')
    @patch('firestore_service.get_session_compliance_stats')
    def test_get_compliance_status_low_compliance(self, mock_get_stats, mock_get_rate):
        """Test compliance status with low compliance rate."""
        mock_get_rate.return_value = 0.65
        mock_get_stats.return_value = {
            'total_responses': 10,
            'compliant_responses': 6
        }
        
        session_id = 'test_session_123'
        
        result = get_compliance_status(session_id)
        
        self.assertEqual(result['compliance_rate'], 0.65)
        self.assertFalse(result['is_compliant'])  # < 0.8
    
    @patch('claude_service.get_session_compliance_rate')
    @patch('firestore_service.get_session_compliance_stats')
    def test_get_compliance_status_error_handling(self, mock_get_stats, mock_get_rate):
        """Test error handling in compliance status retrieval."""
        mock_get_rate.side_effect = Exception("Database error")
        mock_get_stats.side_effect = Exception("Database error")
        
        session_id = 'test_session_123'
        
        result = get_compliance_status(session_id)
        
        # Should return safe defaults on error
        self.assertEqual(result['compliance_rate'], 0.0)
        self.assertFalse(result['is_compliant'])
        self.assertEqual(result['total_responses'], 0)
        self.assertEqual(result['compliant_responses'], 0)


class TestComplianceAlert(unittest.TestCase):
    """Test compliance alert functionality."""
    
    def test_generate_compliance_alert_needed(self):
        """Test alert generation when compliance is low."""
        low_compliance = 0.65
        
        alert = generate_compliance_alert(low_compliance)
        
        self.assertIsNotNone(alert)
        self.assertIn('65%', alert)
        self.assertIn('80%', alert)
    
    def test_generate_compliance_alert_not_needed(self):
        """Test alert generation when compliance is adequate."""
        good_compliance = 0.85
        
        alert = generate_compliance_alert(good_compliance)
        
        self.assertIsNone(alert)
    
    def test_generate_compliance_alert_edge_cases(self):
        """Test alert generation with edge cases."""
        edge_cases = [
            (0.0, True),    # Very low compliance
            (0.799, True),  # Just below threshold
            (0.8, False),   # Exactly at threshold
            (0.801, False), # Just above threshold
            (1.0, False),   # Perfect compliance
        ]
        
        for compliance_rate, should_alert in edge_cases:
            with self.subTest(compliance_rate=compliance_rate):
                alert = generate_compliance_alert(compliance_rate)
                if should_alert:
                    self.assertIsNotNone(alert)
                else:
                    self.assertIsNone(alert)


class TestMultipleResponseValidation(unittest.TestCase):
    """Test validation of multiple responses."""
    
    def test_validate_multiple_responses_mixed(self):
        """Test validation of mixed valid/invalid responses."""
        responses = [
            "[Local: main | Remote: origin/main | PR: none]\nValid response",
            "Invalid response without header",
            "[Local: feature | Remote: origin/feature | PR: #123 url]\nAnother valid response"
        ]
        
        results = validate_multiple_responses(responses)
        
        self.assertEqual(len(results), 3)
        
        # Check first response (valid)
        self.assertEqual(results[0]['index'], 0)
        self.assertTrue(results[0]['has_header'])
        self.assertIsNotNone(results[0]['header_components'])
        
        # Check second response (invalid)
        self.assertEqual(results[1]['index'], 1)
        self.assertFalse(results[1]['has_header'])
        self.assertIsNone(results[1]['header_components'])
        
        # Check third response (valid)
        self.assertEqual(results[2]['index'], 2)
        self.assertTrue(results[2]['has_header'])
        self.assertIsNotNone(results[2]['header_components'])
    
    def test_validate_multiple_responses_empty(self):
        """Test validation with empty response list."""
        results = validate_multiple_responses([])
        
        self.assertEqual(len(results), 0)
    
    def test_validate_multiple_responses_edge_cases(self):
        """Test validation with edge cases."""
        responses = [
            None,
            "",
            123,  # Non-string
            "[Local: main | Remote: origin/main | PR: none]\nValid"
        ]
        
        results = validate_multiple_responses(responses)
        
        self.assertEqual(len(results), 4)
        
        # First three should be invalid
        for i in range(3):
            self.assertFalse(results[i]['has_header'])
            self.assertIsNone(results[i]['header_components'])
        
        # Last one should be valid
        self.assertTrue(results[3]['has_header'])
        self.assertIsNotNone(results[3]['header_components'])


if __name__ == '__main__':
    unittest.main()