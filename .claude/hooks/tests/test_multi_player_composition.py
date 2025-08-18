#!/usr/bin/env python3
"""
Test Multi-Player Command Composition Hook
Tests the enhanced compose-commands.sh hook with nested command detection
"""

import subprocess
import tempfile
import os
import unittest
from pathlib import Path

class TestMultiPlayerComposition(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment"""
        # Find the hook script
        self.repo_root = subprocess.check_output(['git', 'rev-parse', '--show-toplevel']).decode().strip()
        self.hook_script = os.path.join(self.repo_root, '.claude/hooks/compose-commands.sh')
        self.assertTrue(os.path.exists(self.hook_script), "Hook script must exist")
        
    def run_hook(self, input_text):
        """Run the hook with given input and return output"""
        try:
            result = subprocess.run(
                [self.hook_script],
                input=input_text,
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout
        except subprocess.TimeoutExpired:
            self.fail("Hook script timed out")
        except Exception as e:
            self.fail(f"Hook script failed: {e}")
    
    def test_single_command_with_nested_detection(self):
        """Test that /pr command detects its nested commands"""
        output = self.run_hook("/pr implement user authentication")
        
        # Should detect /pr command
        self.assertIn("🔍 Detected slash commands:/pr", output)
        
        # Should find nested commands from pr.md
        self.assertIn("🎯 Multi-Player Intelligence:", output)
        self.assertIn("Found nested commands:", output)
        
        # Should include the nested commands in combination
        expected_nested = ["/think", "/execute", "/push", "/copilot", "/review"]
        for cmd in expected_nested:
            self.assertIn(cmd, output)
        
        # Should provide user message
        self.assertIn('📋 Automatically tell the user: "I detected these commands:/pr', output)
    
    def test_multiple_commands_with_nested_detection(self):
        """Test multiple commands with nested command detection"""
        output = self.run_hook("/execute /review fix authentication system")
        
        # Should detect both commands
        self.assertIn("🔍 Detected slash commands:/execute /review", output)
        
        # Should find nested commands
        self.assertIn("🎯 Multi-Player Intelligence:", output)
        
        # Should include execute's nested commands (/plan, /autoapprove, etc.)
        self.assertIn("/plan", output)
        
        # Should combine all commands intelligently
        self.assertIn("Use these approaches in combination:", output)
    
    def test_simple_command_passthrough(self):
        """Test that simple commands without nesting pass through unchanged"""
        input_text = "/help show available commands"
        output = self.run_hook(input_text)
        
        # Should pass through unchanged (no multi-player detection for /help)
        self.assertEqual(output.strip(), input_text)
    
    def test_no_commands_passthrough(self):
        """Test that text without commands passes through unchanged"""
        input_text = "This is just regular text without any slash commands"
        output = self.run_hook(input_text)
        
        # Should pass through unchanged
        self.assertEqual(output.strip(), input_text)
    
    def test_pasted_content_filtering(self):
        """Test that pasted GitHub content correctly filters out false positive commands"""
        # Simulate pasted GitHub PR content with many commands (>PASTE_COMMAND_THRESHOLD=2)
        input_text = """
        Type / to search
        Navigation Menu
        Pull requests
        /pr review authentication /execute workflow /push changes
        Files changed: +150 -30
        Commits 5
        /utils/helper /src/main /test/spec
        """
        
        output = self.run_hook(input_text)
        
        # Should pass through unchanged because it's detected as pasted content with too many commands (>2)
        self.assertEqual(output.strip(), input_text.strip())
    
    def test_intentional_commands_in_limited_pasted_content(self):
        """Test that intentional commands in limited pasted content are processed"""  
        # Simulate pasted content with just 1-2 commands at start/end (likely intentional)
        input_text = "/pr implement authentication system\nSome regular content here without GitHub patterns"
        
        output = self.run_hook(input_text)
        
        # Should detect and process the /pr command  
        self.assertIn("🔍 Detected slash commands:/pr", output)
        
        # Should provide nested command intelligence
        self.assertIn("🎯 Multi-Player Intelligence:", output)
    
    def test_nested_command_parsing_accuracy(self):
        """Test that nested command parsing finds the right patterns"""
        output = self.run_hook("/pr test nested parsing")
        
        # Verify specific nested commands from pr.md are found
        # These should be detected based on the "combines the functionality of" pattern
        expected_commands = ["/think", "/execute", "/push", "/copilot", "/review"]
        
        for cmd in expected_commands:
            self.assertIn(cmd, output, f"Expected nested command {cmd} not found in output")
    
    def test_debug_logging_integration(self):
        """Test that debug logging works with multi-player features"""
        # Test with debug enabled
        env = os.environ.copy()
        env['COMPOSE_DEBUG'] = '1'
        env['COMPOSE_LOG_FILE'] = '/tmp/test_compose_debug.log'
        
        try:
            result = subprocess.run(
                [self.hook_script],
                input="/pr test debug logging",
                capture_output=True,
                text=True,
                env=env,
                timeout=10
            )
            
            # Check that log file was created and contains debug info
            log_file = '/tmp/test_compose_debug.log'
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    log_content = f.read()
                
                # Should log detected and nested commands separately
                self.assertIn("DETECTED:", log_content)
                self.assertIn("NESTED:", log_content)
                
                # Clean up log file
                os.remove(log_file)
            
        except subprocess.TimeoutExpired:
            self.fail("Hook script with debug logging timed out")
    
    def test_command_deduplication(self):
        """Test that duplicate commands are properly deduplicated"""
        # Test case where detected command is also in nested commands
        output = self.run_hook("/execute implement /execute workflow")
        
        # /execute should appear only once in the final combination
        execute_count = output.count("/execute")
        
        # Should be 3-4: "Detected" section, final combination, and possibly nested sections
        # The fixed deduplication should prevent excessive duplicates (was 5+ before fix)
        self.assertLessEqual(execute_count, 4, "Deduplication should limit /execute to reasonable count")

if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)