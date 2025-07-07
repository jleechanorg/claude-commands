#!/usr/bin/env python3
"""
Test suite for token_utils.py

Tests token counting and logging utilities for accurate token estimation
and consistent logging across the application.
"""

import unittest
import logging
from unittest.mock import Mock, patch
import sys
import os

# Add the parent directory to sys.path so we can import from mvp_site
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from token_utils import estimate_tokens, log_with_tokens, format_token_count


class TestTokenUtils(unittest.TestCase):
    """Test suite for token utility functions."""
    
    def test_estimate_tokens_with_string(self):
        """Test token estimation with string input."""
        # Test empty string
        self.assertEqual(estimate_tokens(""), 0)
        
        # Test single character (should round down to 0)
        self.assertEqual(estimate_tokens("a"), 0)
        
        # Test 4 characters (should be 1 token)
        self.assertEqual(estimate_tokens("test"), 1)
        
        # Test 8 characters (should be 2 tokens)
        self.assertEqual(estimate_tokens("testing!"), 2)
        
        # Test longer text
        text = "This is a longer text for testing token estimation."
        expected_tokens = len(text) // 4  # 51 chars = 12 tokens
        self.assertEqual(estimate_tokens(text), expected_tokens)
    
    def test_estimate_tokens_with_list(self):
        """Test token estimation with list input."""
        # Test empty list
        self.assertEqual(estimate_tokens([]), 0)
        
        # Test list with empty strings
        self.assertEqual(estimate_tokens(["", ""]), 0)
        
        # Test list with strings
        text_list = ["hello", "world", "test"]
        total_chars = len("hello") + len("world") + len("test")  # 14 chars
        expected_tokens = total_chars // 4  # 3 tokens
        self.assertEqual(estimate_tokens(text_list), expected_tokens)
        
        # Test list with mixed content (should ignore non-strings)
        mixed_list = ["hello", 123, "world", None, "test"]
        expected_chars = len("hello") + len("world") + len("test")  # 14 chars
        expected_tokens = expected_chars // 4  # 3 tokens
        self.assertEqual(estimate_tokens(mixed_list), expected_tokens)
    
    def test_estimate_tokens_with_none(self):
        """Test token estimation with None input."""
        self.assertEqual(estimate_tokens(None), 0)
    
    def test_estimate_tokens_edge_cases(self):
        """Test edge cases for token estimation."""
        # Test very large text
        large_text = "a" * 10000
        expected_tokens = 10000 // 4  # 2500 tokens
        self.assertEqual(estimate_tokens(large_text), expected_tokens)
        
        # Test unicode characters
        unicode_text = "café ñoño 你好"
        expected_tokens = len(unicode_text) // 4
        self.assertEqual(estimate_tokens(unicode_text), expected_tokens)
        
        # Test text with newlines and special characters
        special_text = "line1\nline2\t\r\n!@#$%^&*()"
        expected_tokens = len(special_text) // 4
        self.assertEqual(estimate_tokens(special_text), expected_tokens)
    
    @patch('token_utils.logging_util.info')
    def test_log_with_tokens_default_logger(self, mock_log):
        """Test log_with_tokens with default logger."""
        message = "Test message"
        text = "test text content"  # 17 chars = 4 tokens
        
        log_with_tokens(message, text)
        
        expected_log = f"{message}: 17 characters (~4 tokens)"
        mock_log.assert_called_once_with(expected_log)
    
    def test_log_with_tokens_custom_logger(self):
        """Test log_with_tokens with custom logger."""
        mock_logger = Mock()
        message = "Custom log test"
        text = "custom text"  # 11 chars = 2 tokens
        
        log_with_tokens(message, text, logger=mock_logger)
        
        expected_log = f"{message}: 11 characters (~2 tokens)"
        mock_logger.info.assert_called_once_with(expected_log)
    
    @patch('token_utils.logging_util.info')
    def test_log_with_tokens_empty_text(self, mock_log):
        """Test log_with_tokens with empty text."""
        message = "Empty test"
        text = ""
        
        log_with_tokens(message, text)
        
        expected_log = f"{message}: 0 characters (~0 tokens)"
        mock_log.assert_called_once_with(expected_log)
    
    @patch('token_utils.logging_util.info')
    def test_log_with_tokens_none_text(self, mock_log):
        """Test log_with_tokens with None text."""
        message = "None test"
        text = None
        
        log_with_tokens(message, text)
        
        expected_log = f"{message}: 0 characters (~0 tokens)"
        mock_log.assert_called_once_with(expected_log)
    
    def test_format_token_count(self):
        """Test format_token_count function."""
        # Test zero characters
        result = format_token_count(0)
        self.assertEqual(result, "0 characters (~0 tokens)")
        
        # Test small count
        result = format_token_count(4)
        self.assertEqual(result, "4 characters (~1 token)")
        
        # Test larger count
        result = format_token_count(100)
        self.assertEqual(result, "100 characters (~25 tokens)")
        
        # Test odd number (should round down)
        result = format_token_count(17)
        self.assertEqual(result, "17 characters (~4 tokens)")
        
        # Test large count
        result = format_token_count(10000)
        self.assertEqual(result, "10000 characters (~2500 tokens)")
    
    def test_token_estimation_consistency(self):
        """Test that token estimation is consistent across functions."""
        test_texts = [
            "",
            "a",
            "test",
            "hello world",
            "This is a longer test string for consistency checking.",
            "Multi\nline\ntext\nwith\nspecial\ncharacters!@#$%"
        ]
        
        for text in test_texts:
            direct_estimate = estimate_tokens(text)
            char_count = len(text) if text else 0
            formatted_result = format_token_count(char_count)
            
            # Extract token count from formatted string
            formatted_tokens = int(formatted_result.split("~")[1].split(" ")[0])
            
            self.assertEqual(direct_estimate, formatted_tokens,
                           f"Inconsistent token count for text: '{text}'")
    
    def test_log_with_tokens_integration(self):
        """Integration test for log_with_tokens with various inputs."""
        mock_logger = Mock()
        
        test_cases = [
            ("Empty", "", "Empty: 0 characters (~0 tokens)"),
            ("Short", "hi", "Short: 2 characters (~0 tokens)"),
            ("Medium", "hello world", "Medium: 11 characters (~2 tokens)"),
            ("Long", "This is a much longer test message", "Long: 34 characters (~8 tokens)")
        ]
        
        for message, text, expected in test_cases:
            mock_logger.reset_mock()
            log_with_tokens(message, text, logger=mock_logger)
            mock_logger.info.assert_called_once_with(expected)


if __name__ == '__main__':
    unittest.main()