#!/usr/bin/env python3
"""
Unit tests for Memory MCP Effectiveness Analyzer using TDD approach.

Based on PR requirements:
- Test UTF-8 encoding handling
- Test line count tracking for proper metrics calculation
- Test project logger usage instead of print statements
- Test robust _is_successful_result to handle non-string content
- Test consultation_frequency calculation
"""

import unittest
import sys
import os
import json
import tempfile
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'scripts'))

# Import the module under test
from analyze_memory_mcp_effectiveness import (
    MemoryMCPAnalyzer,
    MIN_LINE_THRESHOLD,
    EMPTY_RESULT_INDICATORS,
    SUCCESS_INDICATORS,
    CONSULTATION_PATTERNS
)


class TestMemoryMCPAnalyzer(unittest.TestCase):
    """Test suite for Memory MCP Effectiveness Analyzer using TDD methodology."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.analyzer = MemoryMCPAnalyzer(log_directory=self.temp_dir)

    def tearDown(self):
        """Clean up after each test method."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # RED Phase: Test UTF-8 Encoding Handling
    def test_parse_conversation_log_utf8_encoding(self):
        """Test that UTF-8 encoded files are properly read."""
        # Create a test file with UTF-8 content including special characters
        utf8_content = [
            '{"role": "user", "content": "Test with émojis 🚀 and spëcial chars"}',
            '{"role": "assistant", "content": "Memory search: found 5 entities with café patterns"}',
            '{"role": "user", "content": "Another line with 中文 characters"}'
        ] + ['{"role": "user", "content": "padding line"}'] * (MIN_LINE_THRESHOLD - 3)

        test_file = os.path.join(self.temp_dir, "utf8_test.jsonl")
        with open(test_file, 'w', encoding='utf-8') as f:
            for line in utf8_content:
                f.write(line + '\n')

        result = self.analyzer.parse_conversation_log(test_file)

        # Should successfully parse UTF-8 content
        self.assertFalse(result.get('skipped', False))
        self.assertEqual(result['line_count'], len(utf8_content))
        self.assertGreaterEqual(result['memory_consultations'], 1)  # Should find memory search pattern

    def test_parse_conversation_log_utf8_encoding_error_handling(self):
        """Test handling of UTF-8 encoding errors."""
        # Create a file with invalid UTF-8 bytes
        test_file = os.path.join(self.temp_dir, "invalid_utf8.jsonl")
        with open(test_file, 'wb') as f:
            f.write(b'\xff\xfe{"invalid": "utf8"}\n')  # Invalid UTF-8 byte sequence

        result = self.analyzer.parse_conversation_log(test_file)

        # Should handle encoding error gracefully
        self.assertTrue(result.get('skipped', False))
        self.assertEqual(result.get('reason'), 'encoding_error')
        self.assertIn('error', result)

    # RED Phase: Test Line Count Tracking
    def test_parse_conversation_log_line_count_tracking(self):
        """Test that line count is accurately tracked for metrics calculation."""
        # Create test file with known line count
        test_lines = [
            '{"role": "user", "content": "line 1"}',
            '{"role": "assistant", "content": "line 2"}',
            '', # Empty line should be counted
            '{"role": "user", "content": "line 4"}',
        ] + ['{"role": "user", "content": "padding"}'] * (MIN_LINE_THRESHOLD - 4)

        expected_line_count = len(test_lines)

        test_file = os.path.join(self.temp_dir, "line_count_test.jsonl")
        with open(test_file, 'w', encoding='utf-8') as f:
            for line in test_lines:
                f.write(line + '\n')

        result = self.analyzer.parse_conversation_log(test_file)

        # Line count should be exact
        self.assertEqual(result['line_count'], expected_line_count)

        # Consultation frequency should be calculated based on accurate line count
        expected_frequency = result['memory_consultations'] / expected_line_count
        self.assertEqual(result['consultation_frequency'], expected_frequency)

    def test_parse_conversation_log_skips_short_files(self):
        """Test that files shorter than MIN_LINE_THRESHOLD are skipped."""
        # Create file with fewer lines than threshold
        short_content = ['{"role": "user", "content": "short file"}'] * (MIN_LINE_THRESHOLD - 1)

        test_file = os.path.join(self.temp_dir, "short_file.jsonl")
        with open(test_file, 'w', encoding='utf-8') as f:
            for line in short_content:
                f.write(line + '\n')

        result = self.analyzer.parse_conversation_log(test_file)

        # Should be skipped due to length
        self.assertTrue(result.get('skipped', False))
        self.assertEqual(result.get('reason'), 'too_short')
        self.assertEqual(result['line_count'], len(short_content))

    # RED Phase: Test Project Logger Usage
    @patch('scripts.analyze_memory_mcp_effectiveness.logging_util')
    def test_analyzer_uses_project_logger(self, mock_logging_util):
        """Test that analyzer uses project logging_util instead of print statements."""
        mock_logger = MagicMock()
        mock_logging_util.getLogger.return_value = mock_logger

        # Initialize analyzer (should call getLogger)
        analyzer = MemoryMCPAnalyzer()

        # Should have called logging_util.getLogger
        mock_logging_util.getLogger.assert_called_with('analyze_memory_mcp_effectiveness')

    @patch('scripts.analyze_memory_mcp_effectiveness.logging_util')
    def test_parse_conversation_log_logs_appropriately(self, mock_logging_util):
        """Test that parse_conversation_log uses logger instead of print."""
        mock_logger = MagicMock()
        mock_logging_util.getLogger.return_value = mock_logger

        # Create valid test file
        test_content = ['{"role": "user", "content": "test"}'] * MIN_LINE_THRESHOLD
        test_file = os.path.join(self.temp_dir, "logging_test.jsonl")
        with open(test_file, 'w', encoding='utf-8') as f:
            for line in test_content:
                f.write(line + '\n')

        analyzer = MemoryMCPAnalyzer(self.temp_dir)
        result = analyzer.parse_conversation_log(test_file)

        # Should have used logger methods
        self.assertTrue(mock_logger.debug.called or mock_logger.info.called)

    # RED Phase: Test Robust _is_successful_result Method
    def test_is_successful_result_handles_non_string_content(self):
        """Test that _is_successful_result robustly handles non-string content."""
        # Test with None
        result = self.analyzer._is_successful_result(None)
        self.assertFalse(result)  # None converts to empty string, should be considered empty

        # Test with integer
        result = self.analyzer._is_successful_result(42)
        self.assertFalse(result)  # Number doesn't contain empty indicators

        # Test with list
        result = self.analyzer._is_successful_result(['found', 'entities'])
        self.assertTrue(result)  # List converted to string contains 'found', 'entities'

        # Test with dict
        result = self.analyzer._is_successful_result({'entities': []})
        self.assertFalse(result)  # Contains '[]' which is an empty indicator

    def test_is_successful_result_detects_empty_indicators(self):
        """Test that _is_successful_result correctly identifies empty result indicators."""
        # Test each empty indicator
        for indicator in EMPTY_RESULT_INDICATORS:
            content = f"Search completed but {indicator} were returned"
            result = self.analyzer._is_successful_result(content)
            self.assertFalse(result, f"Should detect empty indicator: {indicator}")

    def test_is_successful_result_detects_success_indicators(self):
        """Test that _is_successful_result correctly identifies success indicators."""
        for indicator in SUCCESS_INDICATORS:
            content = f"Search {indicator} multiple relevant patterns"
            result = self.analyzer._is_successful_result(content)
            self.assertTrue(result, f"Should detect success indicator: {indicator}")

    def test_is_successful_result_entity_count_parsing(self):
        """Test that _is_successful_result correctly parses entity counts."""
        # Test positive entity count
        content = "Search found 5 entities matching the pattern"
        result = self.analyzer._is_successful_result(content)
        self.assertTrue(result)  # 5 entities > 0, should be successful

        # Test zero entity count
        content = "Search found 0 entities matching the pattern"
        result = self.analyzer._is_successful_result(content)
        self.assertFalse(result)  # 0 entities should be unsuccessful

        # Test malformed count
        content = "Search found abc entities"  # Non-numeric
        result = self.analyzer._is_successful_result(content)
        self.assertTrue(result)  # Should default to success indicators check (contains 'found')

    def test_is_successful_result_json_structure_detection(self):
        """Test that _is_successful_result correctly identifies JSON structures."""
        # Test non-empty entities array
        content = '{"entities": [{"name": "test_entity"}], "relationships": []}'
        result = self.analyzer._is_successful_result(content)
        self.assertTrue(result)  # Has entities, should be successful

        # Test empty entities array
        content = '{"entities": [], "relationships": []}'
        result = self.analyzer._is_successful_result(content)
        self.assertFalse(result)  # Empty entities array should be unsuccessful

        # Test malformed JSON
        content = '{"entities": [broken json'
        result = self.analyzer._is_successful_result(content)
        self.assertFalse(result)  # Should fall back to success indicators

    @patch('scripts.analyze_memory_mcp_effectiveness.logging_util')
    def test_is_successful_result_error_handling(self, mock_logging_util):
        """Test that _is_successful_result handles errors gracefully."""
        mock_logger = MagicMock()
        mock_logging_util.getLogger.return_value = mock_logger

        analyzer = MemoryMCPAnalyzer()

        # Mock re.search to raise an exception
        with patch('re.search', side_effect=Exception("Test regex error")):
            result = analyzer._is_successful_result("test content")

            # Should default to False (not successful) and log warning
            self.assertFalse(result)
            mock_logger.warning.assert_called()

    # RED Phase: Test Consultation Frequency Calculation
    def test_has_memory_consultation_pattern_detection(self):
        """Test that _has_memory_consultation correctly identifies consultation patterns."""
        # Test each consultation pattern
        test_cases = [
            ("memory search for patterns", True),
            ("mcp memory integration", True),
            ("memory query optimization", True),
            ("search pattern analysis", True),
            ("unrelated content", False)
        ]

        for content, expected in test_cases:
            result = self.analyzer._has_memory_consultation(content)
            self.assertEqual(result, expected, f"Failed for content: {content}")

    def test_has_memory_consultation_case_insensitive(self):
        """Test that consultation detection is case-insensitive."""
        content = "MEMORY SEARCH FOR PATTERNS"
        result = self.analyzer._has_memory_consultation(content)
        self.assertTrue(result)

        content = "Memory Search for Patterns"
        result = self.analyzer._has_memory_consultation(content)
        self.assertTrue(result)

    def test_consultation_frequency_calculation_accuracy(self):
        """Test that consultation frequency is calculated accurately."""
        # Create test file with known consultation patterns
        test_content = [
            '{"role": "user", "content": "Please search memory for patterns"}',  # Consultation
            '{"role": "assistant", "content": "Found 3 entities"}',  # Not consultation
            '{"role": "user", "content": "Try mcp memory search"}',  # Consultation
            '{"role": "assistant", "content": "Regular response"}',  # Not consultation
        ] + ['{"role": "user", "content": "padding"}'] * (MIN_LINE_THRESHOLD - 4)

        test_file = os.path.join(self.temp_dir, "frequency_test.jsonl")
        with open(test_file, 'w', encoding='utf-8') as f:
            for line in test_content:
                f.write(line + '\n')

        result = self.analyzer.parse_conversation_log(test_file)

        # Should find exactly 2 consultations
        self.assertEqual(result['memory_consultations'], 2)

        # Frequency should be consultations / total lines
        expected_frequency = 2 / len(test_content)
        self.assertEqual(result['consultation_frequency'], expected_frequency)

    # RED Phase: Test Directory Analysis
    def test_analyze_directory_nonexistent_directory(self):
        """Test handling of nonexistent directory."""
        result = self.analyzer.analyze_directory("/nonexistent/directory")

        self.assertEqual(result['error'], 'directory_not_found')
        self.assertEqual(result['directory'], '/nonexistent/directory')

    def test_analyze_directory_no_log_files(self):
        """Test handling of directory with no log files."""
        # Create empty directory
        empty_dir = os.path.join(self.temp_dir, "empty")
        os.makedirs(empty_dir)

        result = self.analyzer.analyze_directory(empty_dir)

        self.assertEqual(result['error'], 'no_log_files')
        self.assertEqual(result['directory'], empty_dir)

    def test_analyze_directory_with_valid_logs(self):
        """Test analysis of directory containing valid log files."""
        # Create multiple test log files
        for i in range(3):
            test_content = [
                f'{{"role": "user", "content": "memory search test {i}"}}',  # Consultation
                f'{{"role": "assistant", "content": "found {i+1} entities"}}',  # Success
            ] + [f'{{"role": "user", "content": "padding {j}"}}' for j in range(MIN_LINE_THRESHOLD - 2)]

            test_file = os.path.join(self.temp_dir, f"conversation_{i}.jsonl")
            with open(test_file, 'w', encoding='utf-8') as f:
                for line in test_content:
                    f.write(line + '\n')

        result = self.analyzer.analyze_directory(self.temp_dir)

        # Should analyze all 3 files
        self.assertNotIn('error', result)
        self.assertEqual(result['analyzed_files'], 3)
        self.assertEqual(result['total_consultations'], 3)  # 1 per file
        self.assertGreater(result['overall_success_rate'], 0)

    # RED Phase: Test Report Generation
    def test_generate_report_json_format(self):
        """Test report generation in JSON format."""
        test_results = {
            'directory': '/test/dir',
            'total_files': 2,
            'analyzed_files': 2,
            'skipped_files': 0,
            'total_consultations': 5,
            'total_successful_searches': 3,
            'total_searches': 5,
            'overall_success_rate': 0.6,
            'average_consultations_per_file': 2.5,
            'file_results': []
        }

        report = self.analyzer.generate_report(test_results, 'json')

        # Should be valid JSON
        parsed = json.loads(report)
        self.assertEqual(parsed['total_consultations'], 5)
        self.assertEqual(parsed['overall_success_rate'], 0.6)

    def test_generate_report_text_format(self):
        """Test report generation in text format."""
        test_results = {
            'directory': '/test/dir',
            'total_files': 2,
            'analyzed_files': 2,
            'skipped_files': 0,
            'total_consultations': 5,
            'total_successful_searches': 3,
            'total_searches': 5,
            'overall_success_rate': 0.6,
            'average_consultations_per_file': 2.5,
            'file_results': []
        }

        report = self.analyzer.generate_report(test_results, 'text')

        # Should contain key information
        self.assertIn('Memory MCP Effectiveness Analysis Report', report)
        self.assertIn('Total Consultations: 5', report)
        self.assertIn('Overall Success Rate: 60%', report)

    def test_generate_report_markdown_format(self):
        """Test report generation in markdown format."""
        test_results = {
            'directory': '/test/dir',
            'total_files': 2,
            'analyzed_files': 2,
            'skipped_files': 0,
            'total_consultations': 5,
            'total_successful_searches': 3,
            'total_searches': 5,
            'overall_success_rate': 0.6,
            'average_consultations_per_file': 2.5,
            'file_results': [
                {
                    'file': '/test/high_performing.jsonl',
                    'memory_consultations': 3,
                    'success_rate': 0.8,
                    'line_count': 50
                }
            ]
        }

        report = self.analyzer.generate_report(test_results, 'markdown')

        # Should contain markdown formatting
        self.assertIn('# Memory MCP Effectiveness Analysis Report', report)
        self.assertIn('**Total Memory Consultations:** 5', report)
        self.assertIn('| File | Consultations | Success Rate |', report)  # Table header

    # GREEN Phase: Test Integration Scenarios
    def test_full_analysis_workflow(self):
        """Integration test: Complete analysis workflow from files to report."""
        # Create comprehensive test scenario
        test_scenarios = [
            {
                'filename': 'high_performance.jsonl',
                'consultations': 3,
                'successes': 3,  # 100% success rate
                'content': [
                    '{"role": "user", "content": "memory search for optimization patterns"}',
                    '{"role": "assistant", "content": "found 5 relevant entities with patterns"}',
                    '{"role": "user", "content": "search memory for debug techniques"}',
                    '{"role": "assistant", "content": "discovered 3 debugging entities"}',
                    '{"role": "user", "content": "mcp memory query for solutions"}',
                    '{"role": "assistant", "content": "located 7 solution entities"}'
                ]
            },
            {
                'filename': 'mixed_performance.jsonl',
                'consultations': 2,
                'successes': 1,  # 50% success rate
                'content': [
                    '{"role": "user", "content": "memory search for patterns"}',
                    '{"role": "assistant", "content": "no entities found matching criteria"}',  # Empty result
                    '{"role": "user", "content": "search memory again"}',
                    '{"role": "assistant", "content": "found 2 relevant patterns"}'  # Success
                ]
            }
        ]

        # Create test files
        for scenario in test_scenarios:
            # Pad to minimum threshold
            padded_content = scenario['content'] + [
                '{"role": "user", "content": "padding"}'
                for _ in range(MIN_LINE_THRESHOLD - len(scenario['content']))
            ]

            test_file = os.path.join(self.temp_dir, scenario['filename'])
            with open(test_file, 'w', encoding='utf-8') as f:
                for line in padded_content:
                    f.write(line + '\n')

        # Run full analysis
        analysis_results = self.analyzer.analyze_directory(self.temp_dir)

        # Verify analysis results
        self.assertNotIn('error', analysis_results)
        self.assertEqual(analysis_results['analyzed_files'], 2)
        self.assertEqual(analysis_results['total_consultations'], 5)  # 3 + 2
        self.assertEqual(analysis_results['total_successful_searches'], 4)  # 3 + 1

        # Calculate expected success rate
        expected_success_rate = 4 / 5  # 4 successes out of 5 consultations
        self.assertAlmostEqual(analysis_results['overall_success_rate'], expected_success_rate, places=2)

        # Generate report
        report = self.analyzer.generate_report(analysis_results, 'text')
        self.assertIn('Overall Success Rate: 80%', report)  # 80% = 4/5

    # GREEN Phase: Test Error Recovery
    @patch('scripts.analyze_memory_mcp_effectiveness.logging_util')
    def test_parse_conversation_log_malformed_json_recovery(self, mock_logging_util):
        """Test that malformed JSON lines are skipped gracefully."""
        mock_logger = MagicMock()
        mock_logging_util.getLogger.return_value = mock_logger

        test_content = [
            '{"role": "user", "content": "valid json"}',
            'invalid json line without braces',
            '{"role": "assistant", "content": "memory search found entities"}',
            '{"incomplete": json',
        ] + ['{"role": "user", "content": "padding"}'] * (MIN_LINE_THRESHOLD - 4)

        test_file = os.path.join(self.temp_dir, "malformed_json.jsonl")
        with open(test_file, 'w', encoding='utf-8') as f:
            for line in test_content:
                f.write(line + '\n')

        analyzer = MemoryMCPAnalyzer()
        result = analyzer.parse_conversation_log(test_file)

        # Should process valid lines and skip malformed ones
        self.assertFalse(result.get('skipped', False))
        self.assertEqual(result['total_entries'], 2)  # Only valid JSON lines
        self.assertEqual(result['memory_consultations'], 1)  # Should find the consultation

        # Should log warnings for malformed JSON
        self.assertTrue(mock_logger.warning.called)

    # REFACTOR Phase: Test Constants and Configuration
    def test_constants_are_used_correctly(self):
        """Test that defined constants are actually used in the code."""
        # Test MIN_LINE_THRESHOLD
        short_file_content = ['{"role": "user", "content": "test"}'] * (MIN_LINE_THRESHOLD - 1)
        test_file = os.path.join(self.temp_dir, "short.jsonl")
        with open(test_file, 'w') as f:
            for line in short_file_content:
                f.write(line + '\n')

        result = self.analyzer.parse_conversation_log(test_file)
        self.assertTrue(result.get('skipped'))
        self.assertEqual(result.get('reason'), 'too_short')

        # Test CONSULTATION_PATTERNS
        for pattern in CONSULTATION_PATTERNS:
            # Create content that should match this pattern
            if 'memory' in pattern and 'search' in pattern:
                test_content = "memory search test"
            elif 'mcp' in pattern:
                test_content = "mcp memory test"
            elif 'memory' in pattern and 'query' in pattern:
                test_content = "memory query test"
            else:
                test_content = "search pattern test"

            result = self.analyzer._has_memory_consultation(test_content)
            self.assertTrue(result, f"Pattern {pattern} should match content: {test_content}")


class TestMemoryMCPAnalyzerCLI(unittest.TestCase):
    """Test suite for Memory MCP Analyzer CLI functionality."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('sys.argv', ['analyze_memory_mcp_effectiveness.py', '--help'])
    def test_main_help_option(self):
        """Test that main function shows help when requested."""
        from analyze_memory_mcp_effectiveness import main

        # Should exit with help (SystemExit expected)
        with self.assertRaises(SystemExit):
            main()

    @patch('sys.argv', ['analyze_memory_mcp_effectiveness.py', '--verbose'])
    @patch('scripts.analyze_memory_mcp_effectiveness.MemoryMCPAnalyzer')
    @patch('scripts.analyze_memory_mcp_effectiveness.logging_util')
    def test_main_verbose_mode(self, mock_logging_util, mock_analyzer_class):
        """Test main function in verbose mode."""
        mock_logger = MagicMock()
        mock_logging_util.getLogger.return_value = mock_logger

        mock_analyzer = MagicMock()
        mock_analyzer_class.return_value = mock_analyzer
        mock_analyzer.analyze_directory.return_value = {
            'total_consultations': 5,
            'overall_success_rate': 0.7,
            'directory': '/test'
        }
        mock_analyzer.generate_report.return_value = "Test report"

        from analyze_memory_mcp_effectiveness import main

        try:
            main()
        except SystemExit as e:
            # Should exit successfully (code 0)
            self.assertEqual(e.code, 0)

        # Should have set debug level
        mock_logging_util.getLogger().setLevel.assert_called_with(mock_logging_util.DEBUG)


if __name__ == '__main__':
    # Configure test environment
    os.environ['TESTING'] = 'true'

    unittest.main(verbosity=2)
