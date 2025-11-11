#!/usr/bin/env python3
"""
Test suite for subprocess_utils module.

Tests focus on:
1. JWT regex bug fix - ensuring non-sensitive data isn't redacted
2. Secret redaction for actual sensitive data
3. Command execution safety
4. Tmux session name validation
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock
import subprocess

# Add the parent commands directory to path for subprocess_utils
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

import subprocess_utils


class TestSanitizeLogContent(unittest.TestCase):
    """Test the sanitize_log_content function with focus on JWT regex bug."""
    
    def test_jwt_regex_does_not_redact_version_numbers(self):
        """Version numbers should NOT be redacted."""
        test_cases = [
            "Installing package version 1.2.3",
            "Upgrading from v2.0.1 to v2.0.2",
            "numpy==1.21.0 installed successfully",
            "Python 3.11.5 is the current version"
        ]
        
        for content in test_cases:
            result = subprocess_utils.sanitize_log_content(content)
            self.assertEqual(content, result, 
                f"Version number incorrectly redacted: {content}")
    
    def test_jwt_regex_does_not_redact_domain_names(self):
        """Domain names should NOT be redacted."""
        test_cases = [
            "Connecting to api.github.com",
            "Fetching from example.com.au",
            "DNS lookup for mail.google.com failed",
            "Redirect to auth.stripe.com detected"
        ]
        
        for content in test_cases:
            result = subprocess_utils.sanitize_log_content(content)
            self.assertEqual(content, result,
                f"Domain name incorrectly redacted: {content}")
    
    def test_jwt_regex_does_not_redact_file_paths(self):
        """File paths and module references should NOT be redacted."""
        test_cases = [
            "Loading module path.to.file",
            "Import error in utils.helpers.validators",
            "File located at src.components.auth",
            "Using os.path.join for path construction",
            "numpy.array.shape is (3, 4, 5)"
        ]
        
        for content in test_cases:
            result = subprocess_utils.sanitize_log_content(content)
            self.assertEqual(content, result,
                f"File path incorrectly redacted: {content}")
    
    def test_actual_jwt_tokens_are_redacted(self):
        """Real JWT tokens SHOULD be redacted."""
        # Real JWT example (expired test token)
        jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        
        test_cases = [
            f"Authorization: Bearer {jwt_token}",
            f"Token: {jwt_token}",
            f"JWT={jwt_token} in environment",
        ]
        
        for content in test_cases:
            result = subprocess_utils.sanitize_log_content(content)
            self.assertIn("[REDACTED_CREDENTIAL]", result,
                f"JWT token not redacted: {content[:50]}...")
            self.assertNotIn(jwt_token, result,
                f"JWT token still visible in output")
    
    def test_api_keys_are_redacted(self):
        """API keys and secrets SHOULD be redacted."""
        test_cases = [
            "api_key=sk-1234567890abcdefghijklmnopqrstuvwxyz",
            "GITHUB_TOKEN=ghp_1234567890abcdefghijklmnopqrstuvwxyz123456",
            "Authorization: Bearer sk-proj-abcdefghijklmnopqrstuvwxyz123456789",
            "password=SuperSecretPassword123!@#$%^&*()",
            "github_pat_11ABCDEFG1234567890abcdefghijklmnopqrstuvwxyz"
        ]
        
        for content in test_cases:
            result = subprocess_utils.sanitize_log_content(content)
            self.assertIn("[REDACTED_CREDENTIAL]", result,
                f"Sensitive data not redacted: {content[:30]}...")
    
    def test_mixed_content_selective_redaction(self):
        """Only sensitive parts should be redacted in mixed content."""
        content = """
        Connecting to api.github.com using version 2.1.0
        Authentication token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
        Loading module utils.auth.validator
        """
        
        result = subprocess_utils.sanitize_log_content(content)
        
        # Non-sensitive data should remain
        self.assertIn("api.github.com", result)
        self.assertIn("version 2.1.0", result)
        self.assertIn("utils.auth.validator", result)
        
        # JWT should be redacted
        self.assertIn("[REDACTED_CREDENTIAL]", result)
        self.assertNotIn("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9", result)


class TestRunCmdSafe(unittest.TestCase):
    """Test the run_cmd_safe function."""
    
    @patch('subprocess_utils.subprocess.run')
    def test_command_execution_with_timeout(self, mock_run):
        """Test that commands execute with proper timeout."""
        mock_run.return_value = MagicMock(
            returncode=0, 
            stdout="Success", 
            stderr=""
        )
        
        result = subprocess_utils.run_cmd_safe(["echo", "test"], timeout=30)
        
        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args[1]
        self.assertEqual(call_kwargs['timeout'], 30)
        self.assertEqual(result.returncode, 0)
    
    def test_empty_command_raises_error(self):
        """Empty commands should raise ValueError."""
        with self.assertRaises(ValueError) as context:
            subprocess_utils.run_cmd_safe([])
        self.assertIn("Empty command", str(context.exception))
    
    @patch('subprocess_utils.subprocess.run')
    @patch('subprocess_utils.logger')
    def test_command_logging_redacts_secrets(self, mock_logger, mock_run):
        """Sensitive data in commands should be redacted in logs."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Success",
            stderr=""
        )
        
        # Command with sensitive data
        subprocess_utils.run_cmd_safe([
            "curl", "-H", "Authorization: Bearer secret123",
            "--token", "mysecrettoken",
            "https://api.example.com"
        ])
        
        # Check that the logged command had secrets redacted
        debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
        command_log = next((msg for msg in debug_calls if "Executing command" in msg), None)
        
        self.assertIsNotNone(command_log)
        self.assertNotIn("secret123", command_log)
        self.assertNotIn("mysecrettoken", command_log)
        self.assertIn("[REDACTED]", command_log)


class TestValidateTmuxSessionName(unittest.TestCase):
    """Test tmux session name validation."""
    
    def test_valid_session_names(self):
        """Valid session names should pass."""
        valid_names = [
            "my-session",
            "session_123",
            "test.session",
            "MySession",
            "a" * 64  # Max length
        ]
        
        for name in valid_names:
            self.assertTrue(
                subprocess_utils.validate_tmux_session_name(name),
                f"Valid name rejected: {name}"
            )
    
    def test_invalid_session_names(self):
        """Invalid session names should fail."""
        invalid_names = [
            "",  # Empty
            "-session",  # Leading hyphen
            "a" * 65,  # Too long
            "session:window",  # Contains colon (removed in fix)
            "session;name",  # Contains semicolon
            "session|name",  # Contains pipe
            "session&name",  # Contains ampersand
        ]
        
        for name in invalid_names:
            self.assertFalse(
                subprocess_utils.validate_tmux_session_name(name),
                f"Invalid name accepted: {name}"
            )


if __name__ == "__main__":
    # Run with verbose output to see all test results
    unittest.main(verbosity=2)