#!/usr/bin/env python3
"""
Test suite for Command Output Trimmer Hook

Tests all compression rules and integration scenarios.
"""

import io
import os
import sys
import json
import shutil
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, call

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from command_output_trimmer import (
    Config,
    OptimizedCommandOutputTrimmer as CommandOutputTrimmer,
    CompressionStats,
    main,
)

class TestCommandOutputTrimmer(unittest.TestCase):
    """Test cases for CommandOutputTrimmer"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.settings_file = os.path.join(self.temp_dir, '.claude', 'settings.json')
        os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)

        # Create basic settings
        settings = {
            "output_trimmer": {
                "enabled": True
            }
        }
        with open(self.settings_file, 'w') as f:
            json.dump(settings, f)

        original_expanduser = os.path.expanduser

        def mock_expanduser(path):
            if path == '~/.claude/settings.json':
                return self.settings_file
            return original_expanduser(path)

        self.expanduser_patcher = patch('command_output_trimmer.os.path.expanduser', side_effect=mock_expanduser)
        self.expanduser_patcher.start()

        CommandOutputTrimmer._reset_singleton_for_testing()
        # Use the singleton OptimizedCommandOutputTrimmer
        self.trimmer = CommandOutputTrimmer()

    def tearDown(self):
        """Clean up test environment"""
        CommandOutputTrimmer._reset_singleton_for_testing()
        if hasattr(self, 'expanduser_patcher'):
            self.expanduser_patcher.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_detect_command_type_test(self):
        """Test detection of test command output"""
        test_output = """
        Running tests...
        test_example.py::test_function PASSED
        test_another.py::test_method FAILED
        """
        self.assertEqual(self.trimmer.detect_command_type(test_output), 'test')

    def test_detect_command_type_pushl(self):
        """Test detection of pushl command output"""
        pushl_output = """
        Creating PR #123
        https://github.com/user/repo/pull/123
        PR created successfully
        """
        self.assertEqual(self.trimmer.detect_command_type(pushl_output), 'pushl')

    def test_detect_command_type_copilot(self):
        """Test detection of copilot command output"""
        copilot_output = """
        Phase 1: Analysis
        Copilot autonomous mode activated
        Phase 2: Execution
        """
        self.assertEqual(self.trimmer.detect_command_type(copilot_output), 'copilot')

    def test_detect_command_type_coverage(self):
        """Test detection of coverage command output"""
        coverage_output = """
        Name                    Stmts   Miss  Cover
        mymodule.py               20      5    75%
        another.py                15      2    87%
        TOTAL                     35      7    80%
        Coverage HTML written to htmlcov/index.html
        """
        self.assertEqual(self.trimmer.detect_command_type(coverage_output), 'coverage')

    def test_detect_command_type_execute(self):
        """Test detection of execute command output"""
        execute_output = """
        ✅ Task completed
        🔄 In progress
        TODO: Next steps
        """
        self.assertEqual(self.trimmer.detect_command_type(execute_output), 'execute')

    def test_detect_command_type_generic(self):
        """Test generic fallback detection"""
        generic_output = """
        Some random command output
        with no specific patterns
        """
        self.assertEqual(self.trimmer.detect_command_type(generic_output), 'generic')

    def test_compress_test_output_preserve_errors(self):
        """Test that test compression preserves error messages"""
        test_lines = [
            "Running 10 tests...",
            "test_a.py::test_1 PASSED",
            "test_a.py::test_2 PASSED",
            "test_a.py::test_3 PASSED",
            "test_a.py::test_4 PASSED",
            "test_b.py::test_5 ERROR: Something went wrong",
            "Traceback (most recent call last):",
            "  File test_b.py, line 10",
            "AssertionError: Values don't match",
            "test_b.py::test_6 PASSED",
            "========== SUMMARY ==========",
            "5 passed, 1 failed"
        ]

        compressed = self.trimmer.compress_test_output(test_lines)

        # Should preserve errors and traceback
        error_lines = [line for line in compressed if 'ERROR' in line or 'Traceback' in line or 'AssertionError' in line]
        self.assertTrue(len(error_lines) >= 3, "Should preserve error, traceback, and assertion")

        # Should preserve summary
        summary_lines = [line for line in compressed if 'SUMMARY' in line or 'passed, 1 failed' in line]
        self.assertTrue(len(summary_lines) >= 1, "Should preserve summary")

    def test_compress_test_output_limit_passed_tests(self):
        """Test that test compression limits passed test output"""
        test_lines = [f"test_{i}.py::test_method PASSED" for i in range(10)]
        compressed = self.trimmer.compress_test_output(test_lines)

        # Debug: Print the compression result
        # print(f"Original: {len(test_lines)} lines")
        # print(f"Compressed: {len(compressed)} lines")
        # print(f"Compressed content: {compressed}")

        # Should limit passed tests and add compression indicator
        passed_lines = [line for line in compressed if 'PASSED' in line and 'compressed' not in line]
        compression_indicator = [line for line in compressed if 'compressed' in line]

        self.assertLessEqual(len(passed_lines), 3, f"Should limit passed test lines, got {len(passed_lines)}: {passed_lines}")
        if len(test_lines) > 3:
            self.assertTrue(len(compression_indicator) >= 1, "Should indicate compression")

    def test_compress_pushl_output_preserve_pr_links(self):
        """Test that pushl compression preserves PR links"""
        pushl_lines = [
            "Enumerating objects: 100, done.",
            "Counting objects: 100% (100/100), done.",
            "Delta compression using up to 8 threads",
            "Creating pull request...",
            "PR #123: https://github.com/user/repo/pull/123",
            "PR created successfully"
        ]

        compressed = self.trimmer.compress_pushl_output(pushl_lines)

        # Should preserve PR links
        pr_links = [line for line in compressed if 'github.com' in line]
        self.assertTrue(len(pr_links) >= 1, "Should preserve GitHub PR links")

        # Should compress git operations
        git_ops = [line for line in compressed if 'Enumerating' in line or 'Delta compression' in line]
        if len([line for line in pushl_lines if 'Enumerating' in line or 'Delta compression' in line]) > 2:
            compression_indicator = [line for line in compressed if 'compressed' in line]
            self.assertTrue(len(compression_indicator) >= 1, "Should compress verbose git operations")

    def test_compress_copilot_output_preserve_phases(self):
        """Test that copilot compression preserves phase information"""
        copilot_lines = [
            "=== Phase 1: Analysis ===",
            "Analyzing codebase...",
            "Duration: 1.2s",
            "Elapsed: 500ms",
            "=== Phase 2: Execution ===",
            "Executing changes...",
            "Duration: 2.1s",
            "✅ Phase 2 complete",
            "=== Phase 3: Validation ===",
            "Validating results..."
        ]

        compressed = self.trimmer.compress_copilot_output(copilot_lines)

        # Should preserve phase markers
        phase_lines = [line for line in compressed if 'Phase' in line and '===' in line]
        self.assertTrue(len(phase_lines) >= 2, "Should preserve phase markers")

        # Should preserve results
        result_lines = [line for line in compressed if '✅' in line]
        self.assertTrue(len(result_lines) >= 1, "Should preserve result indicators")

    def test_compress_coverage_output_preserve_percentages(self):
        """Test that coverage compression preserves percentage information"""
        coverage_lines = [
            "Name                    Stmts   Miss  Cover",
            "mymodule.py               20      5    75%",
            "another.py                15      2    87%",
            "third.py                  10      1    90%",
            "fourth.py                  8      0   100%",
            "fifth.py                  12      3    75%",
            "TOTAL                     65     11    83%"
        ]

        compressed = self.trimmer.compress_coverage_output(coverage_lines)

        # Should preserve total percentage
        total_lines = [line for line in compressed if 'TOTAL' in line]
        self.assertTrue(len(total_lines) >= 1, "Should preserve total coverage")

        # Should preserve percentage lines
        percentage_lines = [line for line in compressed if '%' in line]
        self.assertTrue(len(percentage_lines) >= 1, "Should preserve percentage information")

    def test_compress_execute_output_preserve_todo_states(self):
        """Test that execute compression preserves TODO states"""
        execute_lines = [
            "Starting execution...",
            "✅ Task 1 completed",
            "🔄 Task 2 in progress",
            "❌ Task 3 failed",
            "Explanation: This is a long explanation",
            "Details: More verbose details here",
            "Reasoning: Even more explanatory text",
            "More reasoning text...",
            "TODO: Next steps to take",
            "- [x] Completed item",
            "- [ ] Pending item"
        ]

        compressed = self.trimmer.compress_execute_output(execute_lines)

        # Should preserve TODO states
        todo_lines = [line for line in compressed if '✅' in line or '🔄' in line or '❌' in line]
        self.assertTrue(len(todo_lines) >= 3, "Should preserve TODO state indicators")

        # Should preserve checklist items
        checklist_lines = [line for line in compressed if '- [' in line]
        self.assertTrue(len(checklist_lines) >= 2, "Should preserve checklist items")

    def test_compress_generic_output_fallback(self):
        """Test generic compression fallback"""
        # Create long generic output (>FAST_TRIM_MAX_LINES to trigger trimming)
        generic_lines = [
            f"Line {i}: Some generic content"
            for i in range(Config.FAST_TRIM_MAX_LINES + 25)
        ]
        generic_lines[10] = "ERROR: Important error message"
        generic_lines[30] = "https://important-link.com"

        compressed = self.trimmer.compress_generic_output(generic_lines)

        # Should keep first and last lines
        self.assertTrue(compressed[0] == generic_lines[0], "Should preserve first line")
        self.assertTrue(compressed[-1] == generic_lines[-1], "Should preserve last line")

        # Should preserve important patterns
        important_lines = [line for line in compressed if 'ERROR:' in line or 'https://' in line]
        self.assertTrue(len(important_lines) >= 2, "Should preserve important patterns")

        # Should indicate intelligent summarization
        summary_indicator = [line for line in compressed if 'SUMMARY' in line or 'compressed' in line]
        self.assertTrue(len(summary_indicator) >= 1, "Should indicate compression or summarization")

    def test_compression_stats_calculation(self):
        """Test compression statistics calculation"""
        test_output = "Line 1\nLine 2\nLine 3\n" * 100  # Create substantial output
        compressed_output, stats = self.trimmer.compress_output(test_output)

        self.assertIsInstance(stats, CompressionStats)
        self.assertGreater(stats.original_lines, 0)
        self.assertGreaterEqual(stats.compressed_lines, 0)
        self.assertGreaterEqual(stats.bytes_saved, 0)
        self.assertGreaterEqual(stats.compression_ratio, 0.0)

    def test_natural_language_passthrough_detection(self):
        """Natural language requests should bypass trimming"""
        long_output = "Please show full output before trimming.\n" + "\n".join(
            f"Line {i}: Some detailed output" for i in range(150)
        )

        processed = self.trimmer.process_command_output(long_output)
        self.assertEqual(processed, long_output, "Natural language request should bypass trimming")

        # Verify that without the request the output would be trimmed
        CommandOutputTrimmer._reset_singleton_for_testing()
        trimmer_without_request = CommandOutputTrimmer()
        long_output_without_request = "\n".join(f"Line {i}: Some detailed output" for i in range(150))
        processed_without_request = trimmer_without_request.process_command_output(long_output_without_request)
        self.assertNotEqual(
            processed_without_request,
            long_output_without_request,
            "Without bypass request, output should be trimmed"
        )

    def test_settings_disabled(self):
        """Test that trimming can be disabled via settings"""
        # For the singleton pattern, we'll test the config loading directly
        # rather than trying to reload it at runtime
        settings = {
            "output_trimmer": {
                "enabled": False
            }
        }
        with open(self.settings_file, 'w') as f:
            json.dump(settings, f)

        # Reset singleton and create new trimmer that will load from the test settings
        CommandOutputTrimmer._reset_singleton_for_testing()
        trimmer = CommandOutputTrimmer()

        test_output = "Line 1\nLine 2\nLine 3\n" * 100
        processed_output = trimmer.process_command_output(test_output)

        # Should return original output unchanged when disabled
        self.assertEqual(processed_output, test_output)

    def test_main_function_with_args(self):
        """Test main function with command line arguments"""
        test_args = ["script_name", "test", "output", "content"]

        with patch('sys.argv', test_args):
            fake_buf = io.BytesIO(b"test input data")
            stdin_stub = types.SimpleNamespace(buffer=fake_buf)
            with patch('command_output_trimmer.sys.stdin', new=stdin_stub):
                with patch('sys.stdout.write') as mock_stdout:
                    result = main()

                    self.assertEqual(result, 0)
                    mock_stdout.assert_called()

    def test_error_handling(self):
        """Test error handling in compression"""
        # Test with malformed settings
        with open(self.settings_file, 'w') as f:
            f.write("invalid json")

        # Should not crash, should use defaults
        trimmer = CommandOutputTrimmer()
        test_output = "Test output"
        processed = trimmer.process_command_output(test_output)

        # Should return some output (either original or processed)
        self.assertIsInstance(processed, str)

    def test_main_enforces_byte_limit_with_unicode(self):
        """Ensure byte-based truncation works for multi-byte input"""

        unicorn_text = "🦄" * 32  # Multi-byte characters
        raw_bytes = unicorn_text.encode('utf-8')

        with patch('sys.argv', ['command_output_trimmer']):
            fake_buf = io.BytesIO(raw_bytes)
            stdin_stub = types.SimpleNamespace(buffer=fake_buf)
            with patch.object(Config, 'MAX_INPUT_SIZE', 16):
                with patch('command_output_trimmer.sys.stdin', new=stdin_stub):
                    with patch('sys.stderr.write') as mock_stderr:
                        with patch('sys.stdout.write') as mock_stdout:
                            result = main()

        self.assertEqual(result, 0)
        self.assertTrue(mock_stdout.called)
        warning_calls = [call for call in mock_stderr.call_args_list if 'Warning: Input exceeds' in ''.join(call.args)]
        self.assertTrue(warning_calls, "Expected byte-limit warning for unicode input")

class TestIntegration(unittest.TestCase):
    """Integration tests for the command output trimmer"""

    def setUp(self):
        """Set up test environment"""
        # Reset singleton to ensure clean state
        CommandOutputTrimmer._reset_singleton_for_testing()

    def test_real_command_patterns(self):
        """Test with realistic command output patterns"""

        # Realistic test output (large enough to trigger compression)
        pytest_output = """============================== test session starts ==============================
platform linux -- Python 3.11.9, pytest-7.4.4, pluggy-1.3.0
rootdir: /home/user/project
plugins: xdist-3.3.1, cov-4.0.0
collected 45 items

"""
        # Add many PASSED tests to trigger compression
        for i in range(20):
            for j in range(3):
                pytest_output += f"tests/test_file_{i}.py::test_method_{j} PASSED                          [{i*15+j*5:2d}%]\n"

        pytest_output += """
================================== FAILURES ==================================
__________________________ test_user_validation __________________________

def test_user_validation():
>       assert user.is_valid()
E       AssertionError: User validation failed

tests/test_models.py:25: AssertionError

================================== ERRORS ==================================
__________________________ test_helper_function __________________________

E   ImportError: No module named 'missing_dependency'

============================= short test summary info =============================
FAILED tests/test_models.py::test_user_validation - AssertionError: User validation failed
ERROR tests/test_utils.py::test_helper_function - ImportError: No module named 'missing_dependency'
========================= 43 passed, 1 failed, 1 error =========================
"""

        trimmer = CommandOutputTrimmer()
        compressed, stats = trimmer.compress_output(pytest_output)

        # Should preserve failures and errors
        self.assertIn('FAILURES', compressed)
        self.assertIn('ERRORS', compressed)
        self.assertIn('AssertionError', compressed)
        self.assertIn('ImportError', compressed)

        # Should preserve summary
        self.assertIn('43 passed, 1 failed, 1 error', compressed)

        # Should have reasonable compression
        self.assertGreater(stats.compression_ratio, 0.1)

if __name__ == '__main__':
    unittest.main()
