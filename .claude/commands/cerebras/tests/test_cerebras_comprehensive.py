#!/usr/bin/env python3
"""
Comprehensive test suite for Cerebras conversation context system
Combines tests for both extract_conversation_context.py and cerebras_direct.sh
Uses TDD methodology to ensure complete logic coverage.
"""

import unittest
import tempfile
import json
import os
import sys
import subprocess
import stat
import hashlib
from pathlib import Path
from unittest.mock import patch, mock_open
import shutil

# Add parent directory to path to import the module under test
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from extract_conversation_context import (
    estimate_tokens,
    extract_conversation_context,
    _redact,
    _sanitize_path,
    DEFAULT_MAX_TOKENS
)


class TestTokenEstimation(unittest.TestCase):
    """Test token estimation functionality"""
    
    def test_estimate_tokens_basic(self):
        """Test basic token estimation (4 chars per token)"""
        self.assertEqual(estimate_tokens("test"), 1)  # 4 chars = 1 token
        self.assertEqual(estimate_tokens("test test"), 2)  # 9 chars = 2 tokens
        self.assertEqual(estimate_tokens("a" * 16), 4)  # 16 chars = 4 tokens
    
    def test_estimate_tokens_empty(self):
        """Test token estimation with empty string"""
        self.assertEqual(estimate_tokens(""), 0)
        self.assertEqual(estimate_tokens("   "), 0)  # 3 chars = 0 tokens
    
    def test_estimate_tokens_unicode(self):
        """Test token estimation with unicode characters"""
        # Python len() counts unicode characters as 1 each regardless of byte size
        result = estimate_tokens("🚀🚀🚀🚀")  # 4 chars / 4 = 1 token
        self.assertEqual(result, 1)


class TestSecretRedaction(unittest.TestCase):
    """Test secret redaction patterns"""
    
    def test_redact_api_keys(self):
        """Test redaction of common API key patterns"""
        text = "export API_KEY=sk-1234567890123456789012345"
        result = _redact(text)
        self.assertIn("[REDACTED]", result)
        self.assertNotIn("sk-1234567890123456789012345", result)
    
    def test_redact_jwt_tokens(self):
        """Test redaction of JWT-like tokens"""
        text = "token eyJhbGciOiJIUzI1NiIsInR5cCI.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFt.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        result = _redact(text)
        self.assertIn("[REDACTED]", result)
    
    def test_redact_generic_secrets(self):
        """Test redaction of generic secret patterns"""
        test_cases = [
            "api_key=secret123",
            "token: mytoken456", 
            "secret=verysecret789"
        ]
        for text in test_cases:
            result = _redact(text)
            self.assertIn("[REDACTED]", result)
    
    def test_redact_no_secrets(self):
        """Test that normal text remains unchanged"""
        text = "This is normal conversation text with no secrets"
        result = _redact(text)
        self.assertEqual(text, result)


class TestPathSanitizationBasic(unittest.TestCase):
    """Test path sanitization functionality"""
    
    def test_sanitize_path_basic(self):
        """Test basic hash-based path sanitization"""
        path = "/Users/test/project"
        result = _sanitize_path(path)
        # Should follow pattern: directoryname-hash
        self.assertIn("project-", result)
        parts = result.split('-')
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0], "project") 
        self.assertEqual(len(parts[1]), 12)  # 12-char hash
    
    def test_sanitize_path_complex(self):
        """Test hash-based path sanitization with complex paths"""
        path = "/Users/test_user/my.project/work_tree"
        result = _sanitize_path(path)
        # Should contain directory name and hash
        self.assertIn("work_tree-", result)
        # Hash should be 12 characters
        parts = result.split('-')
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0], "work_tree")
        self.assertEqual(len(parts[1]), 12)
        # Should be alphanumeric hash
        self.assertTrue(parts[1].isalnum())
    
    def test_sanitize_path_edge_cases(self):
        """Test edge cases in hash-based path sanitization"""
        # Empty path gets empty directory name but still gets hash
        empty_result = _sanitize_path("")
        self.assertIn("-", empty_result)
        # Single character paths
        single_result = _sanitize_path("/")
        self.assertIn("-", single_result)
        # Different paths should produce different results
        result1 = _sanitize_path("/path/to/dir1")
        result2 = _sanitize_path("/path/to/dir2")
        self.assertNotEqual(result1, result2)


class TestConversationContextExtraction(unittest.TestCase):
    """Test main conversation context extraction functionality"""
    
    def setUp(self):
        """Set up test environment with temporary directories"""
        self.temp_dir = tempfile.mkdtemp()
        self.projects_dir = Path(self.temp_dir) / ".claude" / "projects"
        self.projects_dir.mkdir(parents=True)
    
    def tearDown(self):
        """Clean up temporary directories"""
        shutil.rmtree(self.temp_dir)
    
    @patch('extract_conversation_context.Path.home')
    @patch('extract_conversation_context.os.getcwd')
    def test_extract_no_project_dir(self, mock_getcwd, mock_home):
        """Test behavior when project directory doesn't exist"""
        mock_home.return_value = Path(self.temp_dir)
        mock_getcwd.return_value = "/nonexistent/project"
        
        with patch('sys.stderr'):  # Suppress stderr output in tests
            result = extract_conversation_context()
        
        self.assertEqual(result, "")
    
    @patch('extract_conversation_context.Path.home')  
    @patch('extract_conversation_context.os.getcwd')
    def test_extract_no_jsonl_files(self, mock_getcwd, mock_home):
        """Test behavior when no JSONL files exist"""
        mock_home.return_value = Path(self.temp_dir)
        mock_getcwd.return_value = "/test/project"
        
        # Create project directory but no JSONL files
        project_dir = self.projects_dir / "test-project"
        project_dir.mkdir()
        
        with patch('sys.stderr'):  # Suppress stderr output in tests
            result = extract_conversation_context()
        
        self.assertEqual(result, "")
    
    @patch('extract_conversation_context.Path.home')
    @patch('extract_conversation_context.os.getcwd') 
    def test_extract_valid_conversation(self, mock_getcwd, mock_home):
        """Test extraction of valid conversation data"""
        mock_home.return_value = Path(self.temp_dir)
        mock_getcwd.return_value = "/test/project"
        
        # Create project directory and JSONL file
        project_dir = self.projects_dir / "test-project"
        project_dir.mkdir()
        
        jsonl_file = project_dir / "conversation.jsonl"
        conversation_data = [
            {
                "type": "user",
                "message": {"content": "Hello, can you help me?"},
                "timestamp": "2024-01-01T10:00:00Z"
            },
            {
                "type": "assistant", 
                "message": {"content": [{"type": "text", "text": "Sure, I'd be happy to help!"}]},
                "timestamp": "2024-01-01T10:00:01Z"
            }
        ]
        
        with open(jsonl_file, 'w') as f:
            for record in conversation_data:
                f.write(json.dumps(record) + '\n')
        
        result = extract_conversation_context()
        
        # Should contain extracted context
        self.assertIn("Recent Conversation Context", result)
        self.assertIn("Hello, can you help me?", result)
        self.assertIn("Sure, I'd be happy to help!", result)
        self.assertIn("User", result)
        self.assertIn("Assistant", result)
    
    def test_default_max_tokens_constant(self):
        """Test that DEFAULT_MAX_TOKENS constant is properly defined"""
        self.assertEqual(DEFAULT_MAX_TOKENS, 50000)
        self.assertIsInstance(DEFAULT_MAX_TOKENS, int)


class TestCerebrasDirectScript(unittest.TestCase):
    """Test cerebras_direct.sh script functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.script_path = str((Path(__file__).resolve().parents[1] / "cerebras_direct.sh").resolve())
    
    def test_script_exists_and_executable(self):
        """Test that the script file exists and is executable"""
        self.assertTrue(os.path.exists(self.script_path), f"Script {self.script_path} does not exist")
        self.assertTrue(os.access(self.script_path, os.X_OK), f"Script {self.script_path} is not executable")
    
    def test_script_has_correct_shebang(self):
        """Test that script has correct shebang"""
        with open(self.script_path, 'r') as f:
            first_line = f.readline().strip()
        self.assertEqual(first_line, "#!/bin/bash", "Script should have #!/bin/bash shebang")
    
    def test_missing_arguments_shows_usage(self):
        """Test handling of missing arguments shows usage"""
        result = subprocess.run([self.script_path], capture_output=True, text=True)
        
        # Should show usage message
        output = (result.stdout or "") + (result.stderr or "")
        self.assertIn("Usage:", output)
        self.assertIn("cerebras_direct.sh", output)
        
        # Should exit with code 1 when no arguments provided
        self.assertEqual(result.returncode, 1)
    
    def test_context_file_parameter_recognized(self):
        """Test that --context-file parameter is recognized"""
        # Create a temporary context file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test context from previous conversation")
            temp_file = f.name
        
        try:
            # Test with context file - should succeed if API key available
            result = subprocess.run(
                [self.script_path, "--context-file", temp_file, "simple test"], 
                capture_output=True, text=True
            )
            
            # Should either succeed (if API key available) or fail gracefully
            self.assertNotEqual(result.returncode, 1)  # Should not be usage error
            
            # If it succeeded, output should contain Cerebras response
            if result.returncode == 0:
                self.assertIn("CEREBRAS GENERATED", result.stdout)
        finally:
            os.unlink(temp_file)
    
    def test_api_key_validation_when_missing(self):
        """Test that script validates API key presence when missing"""
        # Remove API keys from environment for this test
        env = os.environ.copy()
        env.pop('CEREBRAS_API_KEY', None)
        env.pop('OPENAI_API_KEY', None)
        
        result = subprocess.run([self.script_path, "test prompt"], capture_output=True, text=True, env=env)
        
        output = (result.stdout or "") + (result.stderr or "")
        self.assertIn("CEREBRAS_API_KEY", output)
        self.assertEqual(result.returncode, 2)  # Should exit with code 2 for API key error
    
    def test_input_validation_prevents_injection(self):
        """Test that script prevents command injection"""
        dangerous_inputs = [
            "test; rm -rf /",
            "test `rm -rf /`", 
            "test | rm -rf /",
            "test && rm -rf /"
        ]
        
        for dangerous_input in dangerous_inputs:
            result = subprocess.run([self.script_path, dangerous_input], capture_output=True, text=True)
            
            # Should either reject dangerous input or exit with validation error
            self.assertNotEqual(result.returncode, 0)
            output = (result.stdout or "") + (result.stderr or "")
            if "Invalid characters" not in output:
                # If not caught by validation, should fail due to API key (safer failure)
                self.assertIn("API_KEY", output)
    
    def test_script_syntax_is_valid(self):
        """Test that script has valid bash syntax"""
        result = subprocess.run(["bash", "-n", self.script_path], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, f"Script has syntax errors: {result.stderr}")
    
    def test_script_handles_empty_context_file(self):
        """Test that script handles empty context files gracefully"""
        # Create empty context file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            temp_file = f.name  # Empty file
        
        try:
            result = subprocess.run(
                [self.script_path, "--context-file", temp_file, "test prompt"], 
                capture_output=True, text=True
            )
            
            # Should handle empty file gracefully - either succeed or fail gracefully
            self.assertNotEqual(result.returncode, 1)  # Should not be usage error
        finally:
            os.unlink(temp_file)
    
    def test_script_handles_nonexistent_context_file(self):
        """Test that script handles nonexistent context files gracefully"""
        result = subprocess.run(
            [self.script_path, "--context-file", "/nonexistent/file.txt", "test prompt"], 
            capture_output=True, text=True
        )
        
        # Should handle missing file gracefully - either succeed or fail gracefully
        self.assertNotEqual(result.returncode, 1)  # Should not be usage error


class TestConversationContextExtractionBugFix(unittest.TestCase):
    """Test the conversation context extraction bug fix with proper TDD"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.projects_dir = Path(self.temp_dir) / ".claude" / "projects"
        self.projects_dir.mkdir(parents=True)
    
    def tearDown(self):
        """Clean up temporary directories"""
        shutil.rmtree(self.temp_dir)
    
    def _create_test_conversation_file(self, project_dir, content="test conversation"):
        """Helper to create a test conversation file"""
        conv_file = project_dir / "test.jsonl"
        # Create proper JSONL format
        jsonl_content = json.dumps({
            "type": "user", 
            "message": {"content": [{"type": "text", "text": content}]},
            "timestamp": "2024-01-01T12:00:00Z"
        })
        conv_file.write_text(jsonl_content)
        return conv_file
    
    def test_extract_conversation_context_with_hash_match(self):
        """Test that hash-based directory matching works"""
        # This should work (baseline test)
        current_path = "/Users/test/worktree_cereb"
        
        # Create hash-based directory (should match directly)
        sanitized = _sanitize_path(current_path)
        hash_project_dir = self.projects_dir / sanitized
        hash_project_dir.mkdir()
        self._create_test_conversation_file(hash_project_dir, "hash match test")
        
        with patch('extract_conversation_context.os.getcwd') as mock_getcwd, \
             patch('extract_conversation_context.Path.home') as mock_home:
            
            mock_getcwd.return_value = current_path
            mock_home.return_value = Path(self.temp_dir)
            
            result = extract_conversation_context()
            
            self.assertNotEqual(result, "", "Hash-based matching should work")
            self.assertIn("hash match test", result)
    
    def test_extract_conversation_context_fallback_pattern_bug(self):
        """Test the specific fallback pattern bug - THIS IS THE CORE BUG TEST"""
        # This test captures the exact bug: pattern '*worktree_cereb*' not matching 
        # '-Users-jleechan-projects-worldarchitect-ai-worktree-cereb'
        
        current_path = "/Users/jleechan/projects/worldarchitect.ai/worktree_cereb"
        claude_dir_name = "-Users-jleechan-projects-worldarchitect-ai-worktree-cereb"
        
        # Create Claude directory with the problematic name
        claude_project_dir = self.projects_dir / claude_dir_name
        claude_project_dir.mkdir()
        self._create_test_conversation_file(claude_project_dir, "fallback pattern test")
        
        with patch('extract_conversation_context.os.getcwd') as mock_getcwd, \
             patch('extract_conversation_context.Path.home') as mock_home:
            
            mock_getcwd.return_value = current_path
            mock_home.return_value = Path(self.temp_dir)
            
            result = extract_conversation_context()
            
            # This should NOT be empty - if it is, the bug exists
            self.assertNotEqual(result, "", "Fallback pattern should find conversation in Claude directory")
            self.assertIn("fallback pattern test", result)
    
    def test_cross_platform_fallback_patterns(self):
        """Test fallback patterns work across different platforms"""
        test_cases = [
            # macOS
            ("/Users/dev/projects/worktree_cereb", "-Users-dev-projects-worktree-cereb"),
            # Linux
            ("/home/dev/projects/worktree_cereb", "-home-dev-projects-worktree-cereb"),
            # WSL
            ("/mnt/c/dev/projects/worktree_cereb", "-mnt-c-dev-projects-worktree-cereb"),
        ]
        
        for current_path, claude_dir_name in test_cases:
            with self.subTest(current_path=current_path):
                # Clean up previous test directories
                for existing_dir in self.projects_dir.iterdir():
                    if existing_dir.is_dir():
                        shutil.rmtree(existing_dir)
                
                # Create Claude directory
                claude_project_dir = self.projects_dir / claude_dir_name
                claude_project_dir.mkdir()
                self._create_test_conversation_file(claude_project_dir, f"platform test {current_path}")
                
                with patch('extract_conversation_context.os.getcwd') as mock_getcwd, \
                     patch('extract_conversation_context.Path.home') as mock_home:
                    
                    mock_getcwd.return_value = current_path
                    mock_home.return_value = Path(self.temp_dir)
                    
                    result = extract_conversation_context()
                    
                    self.assertNotEqual(result, "", f"Should find conversation for path: {current_path}")
                    self.assertIn(f"platform test {current_path}", result)
    
    def test_underscore_to_hyphen_conversion(self):
        """Test that underscore to hyphen conversion works in fallback patterns"""
        # Test case where directory name has underscores but Claude dir has hyphens
        current_path = "/Users/dev/my_test_project"
        claude_dir_name = "-Users-dev-my-test-project"  # underscores become hyphens
        
        claude_project_dir = self.projects_dir / claude_dir_name
        claude_project_dir.mkdir()
        self._create_test_conversation_file(claude_project_dir, "underscore conversion test")
        
        with patch('extract_conversation_context.os.getcwd') as mock_getcwd, \
             patch('extract_conversation_context.Path.home') as mock_home:
            
            mock_getcwd.return_value = current_path
            mock_home.return_value = Path(self.temp_dir)
            
            result = extract_conversation_context()
            
            self.assertNotEqual(result, "", "Should handle underscore to hyphen conversion")
            self.assertIn("underscore conversion test", result)
    
    def test_no_conversation_files_found(self):
        """Test behavior when directory exists but no conversation files"""
        current_path = "/Users/dev/empty_project"
        claude_dir_name = "-Users-dev-empty-project"
        
        # Create directory but NO conversation files
        claude_project_dir = self.projects_dir / claude_dir_name
        claude_project_dir.mkdir()
        
        with patch('extract_conversation_context.os.getcwd') as mock_getcwd, \
             patch('extract_conversation_context.Path.home') as mock_home:
            
            mock_getcwd.return_value = current_path
            mock_home.return_value = Path(self.temp_dir)
            
            result = extract_conversation_context()
            
            self.assertEqual(result, "", "Should return empty string when no conversation files found")


class TestPathSanitizationAdvanced(unittest.TestCase):
    """Test path sanitization function works correctly"""
    
    def test_sanitize_path_format(self):
        """Test that _sanitize_path produces correct format"""
        test_paths = [
            "/Users/test/worktree_cereb",
            "/home/user/worktree_cereb", 
            "/mnt/c/dev/worktree_cereb",
        ]
        
        for path in test_paths:
            with self.subTest(path=path):
                result = _sanitize_path(path)
                
                # Should be format: dirname-hash
                parts = result.split('-')
                self.assertEqual(len(parts), 2, f"Should have format 'dirname-hash': {result}")
                self.assertEqual(parts[0], "worktree_cereb", f"Directory name preserved: {result}")
                self.assertEqual(len(parts[1]), 12, f"Hash should be 12 chars: {result}")
                self.assertTrue(parts[1].isalnum(), f"Hash should be alphanumeric: {result}")
    
    def test_sanitize_path_uniqueness(self):
        """Test that different paths generate different hashes"""
        path1 = "/Users/test/worktree_cereb"
        path2 = "/home/user/worktree_cereb"
        
        result1 = _sanitize_path(path1)
        result2 = _sanitize_path(path2)
        
        self.assertNotEqual(result1, result2, "Different paths should generate different sanitized names")


class TestConversationContextChronologicalOrdering(unittest.TestCase):
    """Test chronological ordering and timestamp functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.projects_dir = Path(self.temp_dir) / '.claude' / 'projects'
        self.projects_dir.mkdir(parents=True)
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
    
    def test_chronological_order_and_timestamps(self):
        """Test that messages are in chronological order (oldest first) with timestamps"""
        current_path = "/Users/test/chronology_test"
        hash_project_dir = self.projects_dir / f"chronology_test-{hashlib.sha256(current_path.encode()).hexdigest()[:12]}"
        hash_project_dir.mkdir()
        
        # Create JSONL with multiple messages with explicit timestamps
        conv_file = hash_project_dir / "test.jsonl"
        
        # Create messages with different timestamps - NOTE: reversed input order to test sorting
        messages = [
            {"type": "user", "message": {"content": "Third message (newest)"}, "timestamp": "2024-01-01T12:30:00Z"},
            {"type": "assistant", "message": {"content": "Second response"}, "timestamp": "2024-01-01T12:20:00Z"},
            {"type": "user", "message": {"content": "First message (oldest)"}, "timestamp": "2024-01-01T12:10:00Z"},
        ]
        
        # Write messages in reverse chronological order to test sorting
        jsonl_content = '\n'.join([json.dumps(msg) for msg in messages])
        conv_file.write_text(jsonl_content)
        
        with patch('extract_conversation_context.os.getcwd') as mock_getcwd, \
             patch('extract_conversation_context.Path.home') as mock_home:
            
            mock_getcwd.return_value = current_path
            mock_home.return_value = Path(self.temp_dir)
            
            result = extract_conversation_context()
            
            # Test that result is not empty
            self.assertNotEqual(result, "", "Should extract conversation with timestamps")
            
            # Test chronological order: First message should appear before Third message
            first_pos = result.find("First message (oldest)")
            third_pos = result.find("Third message (newest)")
            self.assertNotEqual(first_pos, -1, "Should contain first message")
            self.assertNotEqual(third_pos, -1, "Should contain third message") 
            self.assertLess(first_pos, third_pos, "First message should appear BEFORE third message in output")
            
            # Test timestamps are included in output
            self.assertIn("12:10:00Z", result, "Should include oldest timestamp")
            self.assertIn("12:30:00Z", result, "Should include newest timestamp")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)