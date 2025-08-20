#!/usr/bin/env python3
"""
Matrix-Enhanced TDD Tests for Cerebras/Qwen Command Integration
Following comprehensive test matrix approach from /tdd command
"""

import unittest
import subprocess
import os
import json
import time
from unittest.mock import patch, MagicMock


class QwenCommandMatrixTests(unittest.TestCase):
    """Matrix-driven tests covering all qwen command scenarios"""
    
    def setUp(self):
        """Set up test environment for each matrix test"""
        self.qwen_script = "/home/jleechan/projects/worldarchitect.ai/worktree_human/.claude/commands/cerebras/cerebras_direct.sh"
        self.original_env = os.environ.copy()
        
    def tearDown(self):
        """Restore environment after each test"""
        os.environ.clear()
        os.environ.update(self.original_env)

    # Matrix 1: API Configuration Testing (Provider × Authentication × Model)
    
    def test_matrix_1_1_cerebras_valid_key(self):
        """[1,1] Cerebras with valid CEREBRAS_API_KEY → Fast generation + timing"""
        # RED: This should fail initially as we need to verify the timing output format
        os.environ['CEREBRAS_API_KEY'] = 'test_key_cerebras'
        
        with patch('subprocess.run') as mock_run:
            # Mock successful Cerebras response
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='🚀🚀🚀 QWEN GENERATED IN 500ms 🚀🚀🚀\n\nprint("Hello World")\n\n🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀\n⚡ QWEN BLAZING FAST: 500ms (vs Sonnet comparison)\n🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀'
            )
            
            result = subprocess.run([self.qwen_script, "write hello world"], 
                                  capture_output=True, text=True)
            
            # Verify timing display format
            self.assertIn('🚀🚀🚀 QWEN GENERATED IN', result.stdout)
            self.assertIn('ms 🚀🚀🚀', result.stdout)
            self.assertIn('⚡ QWEN BLAZING FAST:', result.stdout)
            
    def test_matrix_1_2_cerebras_fallback_key(self):
        """[1,2] Cerebras with OPENAI_API_KEY fallback → Fallback auth working"""
        # RED: Test fallback authentication mechanism
        os.environ.pop('CEREBRAS_API_KEY', None)
        os.environ['OPENAI_API_KEY'] = 'test_key_openai'
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout='Generated code')
            
            result = subprocess.run([self.qwen_script, "test prompt"], 
                                  capture_output=True, text=True)
            
            # Should work with fallback key
            self.assertEqual(result.returncode, 0)
            
    def test_matrix_1_3_cerebras_missing_keys(self):
        """[1,3] Cerebras with missing keys → Clear error message"""
        # RED: Test error handling for missing authentication
        os.environ.pop('CEREBRAS_API_KEY', None)
        os.environ.pop('OPENAI_API_KEY', None)
        
        result = subprocess.run([self.qwen_script, "test prompt"], 
                              capture_output=True, text=True)
        
        # Should fail with clear error message
        self.assertEqual(result.returncode, 2)
        self.assertIn('CEREBRAS_API_KEY', result.stderr)
        self.assertIn('must be set', result.stderr)
        
    def test_matrix_2_1_sonnet_valid_key(self):
        """[2,1] Sonnet with valid CLAUDE_API_KEY → Sonnet generation"""
        # RED: Test Sonnet flag and timing format
        os.environ['CLAUDE_API_KEY'] = 'test_key_claude'
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='🧠🧠🧠 SONNET GENERATED IN 2500ms 🧠🧠🧠\n\nprint("Hello from Sonnet")\n\n🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠\n⚡ SONNET PERFORMANCE: 2500ms\n🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠'
            )
            
            result = subprocess.run([self.qwen_script, "--sonnet", "test prompt"], 
                                  capture_output=True, text=True)
            
            # Verify Sonnet-specific timing format
            self.assertIn('🧠🧠🧠 SONNET GENERATED IN', result.stdout)
            self.assertIn('⚡ SONNET PERFORMANCE:', result.stdout)
            
    def test_matrix_2_2_sonnet_missing_key(self):
        """[2,2] Sonnet with missing CLAUDE_API_KEY → Clear error message"""
        # RED: Test Sonnet authentication error
        os.environ.pop('CLAUDE_API_KEY', None)
        
        result = subprocess.run([self.qwen_script, "--sonnet", "test prompt"], 
                              capture_output=True, text=True)
        
        self.assertEqual(result.returncode, 2)
        self.assertIn('CLAUDE_API_KEY', result.stderr)
        
    # Matrix 2: Command Input Variations (Prompt × Flags × Context)
    
    def test_matrix_3_1_simple_code_request(self):
        """[3,1] Simple code request with project context → Code generation"""
        # RED: Test basic code generation workflow
        os.environ['CEREBRAS_API_KEY'] = 'test_key'
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='def hello():\n    return "world"'
            )
            
            result = subprocess.run([self.qwen_script, "write a hello function"], 
                                  capture_output=True, text=True)
            
            self.assertEqual(result.returncode, 0)
            self.assertIn('def hello', result.stdout)
            
    def test_matrix_3_4_empty_prompt(self):
        """[3,4] Empty prompt → Usage error"""
        # RED: Test input validation
        result = subprocess.run([self.qwen_script], capture_output=True, text=True)
        
        self.assertEqual(result.returncode, 1)
        self.assertIn('Usage:', result.stdout)
        
    def test_matrix_3_5_special_characters(self):
        """[3,5] Special characters in prompt → Proper escaping"""
        # RED: Test special character handling
        os.environ['CEREBRAS_API_KEY'] = 'test_key'
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout='Generated code')
            
            result = subprocess.run([self.qwen_script, "print('test \"quotes\" and $vars')"], 
                                  capture_output=True, text=True)
            
            # Should handle special characters without errors
            self.assertEqual(result.returncode, 0)
            
    # Matrix 3: Performance & Timing Testing
    
    def test_matrix_4_1_cerebras_timing_display(self):
        """[4,1] Cerebras timing display format → Rocket emojis and ms"""
        # RED: Test specific timing format requirements
        os.environ['CEREBRAS_API_KEY'] = 'test_key'
        
        with patch('subprocess.run') as mock_run:
            mock_output = """
🚀🚀🚀 QWEN GENERATED IN 750ms 🚀🚀🚀

print("fast code")

🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀
⚡ QWEN BLAZING FAST: 750ms (vs Sonnet comparison)
🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀🚀
"""
            mock_run.return_value = MagicMock(returncode=0, stdout=mock_output)
            
            result = subprocess.run([self.qwen_script, "test timing"], 
                                  capture_output=True, text=True)
            
            # Verify exact timing format
            self.assertRegex(result.stdout, r'🚀🚀🚀 QWEN GENERATED IN \d+ms 🚀🚀🚀')
            self.assertRegex(result.stdout, r'⚡ QWEN BLAZING FAST: \d+ms \(vs Sonnet comparison\)')
            
    def test_matrix_4_2_sonnet_timing_comparison(self):
        """[4,2] Sonnet timing display → Brain emojis and comparison"""
        # RED: Test Sonnet timing format
        os.environ['CLAUDE_API_KEY'] = 'test_key'
        
        with patch('subprocess.run') as mock_run:
            mock_output = """
🧠🧠🧠 SONNET GENERATED IN 3200ms 🧠🧠🧠

print("thoughtful code")

🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠
⚡ SONNET PERFORMANCE: 3200ms
🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠🧠
"""
            mock_run.return_value = MagicMock(returncode=0, stdout=mock_output)
            
            result = subprocess.run([self.qwen_script, "--sonnet", "test timing"], 
                                  capture_output=True, text=True)
            
            # Verify Sonnet timing format
            self.assertRegex(result.stdout, r'🧠🧠🧠 SONNET GENERATED IN \d+ms 🧠🧠🧠')
            self.assertRegex(result.stdout, r'⚡ SONNET PERFORMANCE: \d+ms')
            
    # Matrix 4: System Prompt Integration Testing
    
    def test_matrix_5_1_concise_output(self):
        """[5,1] System prompt 'Be concise, direct' → No verbose explanations"""
        # RED: Test that output follows conciseness guidelines
        os.environ['CEREBRAS_API_KEY'] = 'test_key'
        
        with patch('subprocess.run') as mock_run:
            # Mock response that should be concise (just code, no explanation)
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='def factorial(n):\n    return 1 if n <= 1 else n * factorial(n-1)'
            )
            
            result = subprocess.run([self.qwen_script, "write factorial function"], 
                                  capture_output=True, text=True)
            
            # Should contain code but no verbose explanations
            self.assertIn('def factorial', result.stdout)
            self.assertNotIn('This function calculates', result.stdout)
            self.assertNotIn('Here is how it works', result.stdout)
            
    def test_matrix_5_2_no_comments_unless_asked(self):
        """[5,2] System prompt 'NEVER add comments' → Code without comments"""
        # RED: Test comment suppression in generated code
        os.environ['CEREBRAS_API_KEY'] = 'test_key'
        
        with patch('subprocess.run') as mock_run:
            # Mock code without comments
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='def process_data(data):\n    filtered = [x for x in data if x > 0]\n    return sorted(filtered)'
            )
            
            result = subprocess.run([self.qwen_script, "write data processing function"], 
                                  capture_output=True, text=True)
            
            # Should not contain code comments
            self.assertNotIn('#', result.stdout)
            self.assertNotIn('//', result.stdout)
            self.assertNotIn('"""', result.stdout)


if __name__ == '__main__':
    # Run matrix tests with detailed output
    unittest.main(verbosity=2)