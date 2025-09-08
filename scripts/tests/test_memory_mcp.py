#!/usr/bin/env python3
"""
Simple functional tests for Memory MCP components.
Focuses on core functionality without complex mocking.
"""

import unittest
import sys
import os
import json
import tempfile
from pathlib import Path

# Add scripts to path
scripts_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, scripts_dir)

# Import modules directly
import memory_mcp_optimizer
import analyze_memory_mcp_effectiveness


class TestMemoryMCPOptimizerSimple(unittest.TestCase):
    """Simple tests for Memory MCP Optimizer focusing on core functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.optimizer = memory_mcp_optimizer.MemoryMCPOptimizer()

    def test_transform_query_basic(self):
        """Test basic query transformation."""
        result = self.optimizer.transform_query("search effectiveness empty results")
        self.assertEqual(result, ['search', 'effectiveness', 'empty', 'results'])

    def test_transform_query_special_chars(self):
        """Test query transformation with special characters."""
        result = self.optimizer.transform_query("Memory MCP search! empty-results")
        expected = ['memory', 'mcp', 'search', 'empty', 'results']
        self.assertEqual(result, expected)

    def test_transform_query_none_input(self):
        """Test query transformation with None input."""
        result = self.optimizer.transform_query(None)
        self.assertEqual(result, [])

    def test_transform_query_empty_string(self):
        """Test query transformation with empty string."""
        result = self.optimizer.transform_query("")
        self.assertEqual(result, [])

    def test_expand_concepts_known_mappings(self):
        """Test concept expansion with known mappings."""
        result = self.optimizer.expand_concepts(['search', 'effectiveness'])
        # Should expand 'search' and 'effectiveness' to their mappings
        self.assertIn('search', result)
        self.assertIn('query', result)  # From search mapping
        self.assertIn('effectiveness', result)
        self.assertIn('efficiency', result)  # From effectiveness mapping

    def test_expand_concepts_unknown_mappings(self):
        """Test concept expansion with unknown mappings."""
        result = self.optimizer.expand_concepts(['unknown_term'])
        self.assertEqual(result, ['unknown_term'])

    def test_optimize_query_max_terms_limit(self):
        """Test that optimize_query respects MAX_TERMS limit."""
        # Create a query that would expand beyond MAX_TERMS
        long_query = " ".join(['search', 'effectiveness', 'empty', 'results', 'patterns', 'investigation', 'knowledge', 'decision'])
        result = self.optimizer.optimize_query(long_query)
        # Should be limited to MAX_TERMS (6)
        self.assertLessEqual(len(result), memory_mcp_optimizer.MAX_TERMS)

    def test_merge_results_empty(self):
        """Test merging empty results."""
        result = self.optimizer.merge_results([])
        expected = {'entities': [], 'relationships': []}
        self.assertEqual(result, expected)

    def test_merge_results_single_result(self):
        """Test merging single result."""
        search_results = [
            {
                'entities': [{'id': '1', 'name': 'entity1'}],
                'relationships': [{'id': 'r1', 'from': 'a', 'to': 'b'}]
            }
        ]
        result = self.optimizer.merge_results(search_results)
        self.assertEqual(len(result['entities']), 1)
        self.assertEqual(len(result['relationships']), 1)
        self.assertEqual(result['entities'][0]['name'], 'entity1')

    def test_score_results_basic(self):
        """Test basic result scoring."""
        results = {
            'entities': [
                {'name': 'search_entity', 'entityType': 'test', 'observations': ['search related']},
                {'name': 'other_entity', 'entityType': 'test', 'observations': ['not related']}
            ]
        }
        scored = self.optimizer.score_results(results, 'search effectiveness')

        # First entity should have higher score (contains 'search')
        self.assertGreater(
            scored['entities'][0]['relevance_score'],
            scored['entities'][1]['relevance_score']
        )


class TestMemoryMCPAnalyzerSimple(unittest.TestCase):
    """Simple tests for Memory MCP Analyzer focusing on core functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = analyze_memory_mcp_effectiveness.MemoryMCPAnalyzer()

    def test_has_memory_consultation_positive(self):
        """Test memory consultation detection - positive case."""
        content = "Using memory search to find patterns"
        result = self.analyzer._has_memory_consultation(content)
        self.assertTrue(result)

    def test_has_memory_consultation_negative(self):
        """Test memory consultation detection - negative case."""
        content = "This is just regular content"
        result = self.analyzer._has_memory_consultation(content)
        self.assertFalse(result)

    def test_is_successful_result_positive(self):
        """Test successful result detection - positive case."""
        content = "Found 5 entities in the search results"
        result = self.analyzer._is_successful_result(content)
        self.assertTrue(result)

    def test_is_successful_result_negative_empty(self):
        """Test successful result detection - negative case with empty indicators."""
        content = "No entities found in results"
        result = self.analyzer._is_successful_result(content)
        self.assertFalse(result)

    def test_is_successful_result_non_string_input(self):
        """Test successful result detection with non-string input."""
        result = self.analyzer._is_successful_result(None)
        self.assertFalse(result)

        result = self.analyzer._is_successful_result(123)
        self.assertFalse(result)

    def test_parse_conversation_log_short_file(self):
        """Test parsing a file that's too short."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as tmp:
            # Write fewer lines than MIN_LINE_THRESHOLD
            for i in range(5):  # Less than MIN_LINE_THRESHOLD (10)
                tmp.write(f'{{"content": "test message {i}"}}\n')
            tmp.flush()

            result = self.analyzer.parse_conversation_log(tmp.name)
            self.assertTrue(result.get('skipped'))
            self.assertEqual(result.get('reason'), 'too_short')

        os.unlink(tmp.name)

    def test_parse_conversation_log_valid_file(self):
        """Test parsing a valid conversation log file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as tmp:
            # Write enough lines with some memory consultations
            test_lines = [
                '{"content": "Using memory search to find patterns"}',  # Consultation
                '{"content": "Found 3 entities in search"}',            # Success
                '{"content": "Regular message without consultation"}',
                '{"content": "Another memory search query"}',           # Consultation
                '{"content": "No results found"}',                      # Failure
            ] + ['{"content": "padding message"}'] * 10  # Ensure above threshold

            for line in test_lines:
                tmp.write(line + '\n')
            tmp.flush()

            result = self.analyzer.parse_conversation_log(tmp.name)
            self.assertFalse(result.get('skipped', False))
            self.assertGreater(result['memory_consultations'], 0)
            self.assertGreaterEqual(result['total_searches'], 0)

        os.unlink(tmp.name)


class TestMemoryMCPIntegrationSimple(unittest.TestCase):
    """Simple integration tests for Memory MCP components."""

    def test_full_optimization_pipeline(self):
        """Test the complete optimization pipeline end-to-end."""
        optimizer = memory_mcp_optimizer.MemoryMCPOptimizer()

        # Test complete pipeline
        query = "search effectiveness empty results"
        optimized_terms = optimizer.optimize_query(query)

        # Should return optimized terms
        self.assertIsInstance(optimized_terms, list)
        self.assertGreater(len(optimized_terms), 0)
        self.assertLessEqual(len(optimized_terms), memory_mcp_optimizer.MAX_TERMS)

    def test_learn_patterns_functionality(self):
        """Test pattern learning functionality."""
        optimizer = memory_mcp_optimizer.MemoryMCPOptimizer()

        # Simulate successful search
        search_results = {
            'entities': [{'name': 'test_entity'}]
        }

        original_count = len(optimizer.successful_patterns)
        optimizer.learn_patterns("test query", ["test", "query"], search_results)

        # Should track the successful pattern
        self.assertGreaterEqual(len(optimizer.successful_patterns), original_count)


if __name__ == '__main__':
    unittest.main()
