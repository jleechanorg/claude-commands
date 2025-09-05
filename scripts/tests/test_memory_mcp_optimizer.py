#!/usr/bin/env python3
"""
Unit tests for Memory MCP Optimizer using TDD approach.

Based on PR requirements:
- Test query transformation, concept expansion, result merging
- Test error handling and edge cases
- Verify optimization pipeline end-to-end
"""

import unittest
import sys
import os
import json
from unittest.mock import patch, MagicMock

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'scripts'))

# Import the module under test
from memory_mcp_optimizer import MemoryMCPOptimizer, MAX_TERMS, MIN_RELEVANCE_SCORE


class TestMemoryMCPOptimizer(unittest.TestCase):
    """Test suite for Memory MCP Optimizer using TDD methodology."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.optimizer = MemoryMCPOptimizer()

    def tearDown(self):
        """Clean up after each test method."""
        pass

    # RED Phase: Test Query Transformation
    def test_transform_query_basic_compound_phrase(self):
        """Test that compound phrases are split into constituent words."""
        query = "search effectiveness empty results"
        expected = ['search', 'effectiveness', 'empty', 'results']
        result = self.optimizer.transform_query(query)
        self.assertEqual(result, expected)

    def test_transform_query_with_special_characters(self):
        """Test query transformation with special characters and punctuation."""
        query = "Memory MCP search! empty-results & query patterns"
        expected = ['memory', 'mcp', 'search', 'empty', 'results', 'query', 'patterns']
        result = self.optimizer.transform_query(query)
        self.assertEqual(result, expected)

    def test_transform_query_empty_string(self):
        """Test transformation of empty query string."""
        result = self.optimizer.transform_query("")
        self.assertEqual(result, [])

    def test_transform_query_whitespace_only(self):
        """Test transformation of whitespace-only query."""
        result = self.optimizer.transform_query("   \t\n  ")
        self.assertEqual(result, [])

    def test_transform_query_single_word(self):
        """Test transformation of single word query."""
        result = self.optimizer.transform_query("investigation")
        self.assertEqual(result, ['investigation'])

    # RED Phase: Test Concept Expansion
    def test_expand_concepts_known_mappings(self):
        """Test expansion of concepts that have domain mappings."""
        concepts = ['search', 'effectiveness']
        result = self.optimizer.expand_concepts(concepts)

        # Should include original concepts plus their mappings
        self.assertIn('search', result)
        self.assertIn('query', result)  # From search mapping
        self.assertIn('effectiveness', result)
        self.assertIn('efficiency', result)  # From effectiveness mapping

    def test_expand_concepts_unknown_mappings(self):
        """Test expansion of concepts without domain mappings."""
        concepts = ['unknown_concept', 'another_unknown']
        result = self.optimizer.expand_concepts(concepts)

        # Should preserve unknown concepts as-is
        self.assertEqual(set(result), {'unknown_concept', 'another_unknown'})

    def test_expand_concepts_mixed_known_unknown(self):
        """Test expansion with mix of known and unknown concepts."""
        concepts = ['search', 'unknown_concept', 'memory']
        result = self.optimizer.expand_concepts(concepts)

        # Should expand known concepts and preserve unknown ones
        self.assertIn('search', result)
        self.assertIn('query', result)  # From search mapping
        self.assertIn('unknown_concept', result)  # Preserved as-is
        self.assertIn('memory', result)
        self.assertIn('storage', result)  # From memory mapping

    def test_expand_concepts_empty_list(self):
        """Test expansion of empty concept list."""
        result = self.optimizer.expand_concepts([])
        self.assertEqual(result, [])

    # RED Phase: Test Query Optimization Pipeline
    def test_optimize_query_respects_max_terms_limit(self):
        """Test that optimization respects MAX_TERMS constant."""
        # Create a query that would expand beyond MAX_TERMS
        long_query = "search effectiveness empty results query patterns investigation memory optimization"
        result = self.optimizer.optimize_query(long_query)

        # Should not exceed MAX_TERMS
        self.assertLessEqual(len(result), MAX_TERMS)

    def test_optimize_query_prioritizes_original_words(self):
        """Test that original words are prioritized in optimization."""
        query = "search effectiveness"
        result = self.optimizer.optimize_query(query)

        # Original words should appear first
        self.assertIn('search', result)
        self.assertIn('effectiveness', result)

    def test_optimize_query_end_to_end(self):
        """Test complete optimization pipeline from compound query to optimized terms."""
        query = "Memory MCP search empty results"
        result = self.optimizer.optimize_query(query)

        # Should return list of optimized terms
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)
        self.assertIn('memory', result)
        self.assertIn('mcp', result)
        self.assertIn('search', result)

    # RED Phase: Test Result Merging
    def test_merge_results_empty_list(self):
        """Test merging with empty results list."""
        result = self.optimizer.merge_results([])
        expected = {'entities': [], 'relationships': []}
        self.assertEqual(result, expected)

    def test_merge_results_single_result(self):
        """Test merging with single search result."""
        search_results = [{
            'entities': [{'id': 'entity1', 'name': 'test_entity'}],
            'relationships': [{'id': 'rel1', 'from': 'a', 'to': 'b'}]
        }]

        result = self.optimizer.merge_results(search_results)

        self.assertEqual(len(result['entities']), 1)
        self.assertEqual(len(result['relationships']), 1)
        self.assertEqual(result['entities'][0]['name'], 'test_entity')

    def test_merge_results_multiple_results_with_duplicates(self):
        """Test merging multiple results with duplicate entities."""
        search_results = [
            {
                'entities': [{'id': 'entity1', 'name': 'test_entity'}],
                'relationships': []
            },
            {
                'entities': [{'id': 'entity1', 'name': 'test_entity'}],  # Duplicate
                'relationships': [{'id': 'rel1', 'from': 'a', 'to': 'b'}]
            }
        ]

        result = self.optimizer.merge_results(search_results)

        # Should deduplicate entities
        self.assertEqual(len(result['entities']), 1)
        self.assertEqual(len(result['relationships']), 1)

    def test_merge_results_entities_without_id_use_name(self):
        """Test merging when entities don't have ID, use name for deduplication."""
        search_results = [
            {
                'entities': [{'name': 'entity_by_name'}],
                'relationships': []
            },
            {
                'entities': [{'name': 'entity_by_name'}],  # Same name, should dedupe
                'relationships': []
            }
        ]

        result = self.optimizer.merge_results(search_results)

        # Should deduplicate by name
        self.assertEqual(len(result['entities']), 1)

    # RED Phase: Test Result Scoring
    def test_score_results_empty_results(self):
        """Test scoring with empty results."""
        results = {'entities': [], 'relationships': []}
        query = "test query"

        scored = self.optimizer.score_results(results, query)

        self.assertEqual(scored['entities'], [])
        self.assertEqual(scored['relationships'], [])

    def test_score_results_calculates_relevance_scores(self):
        """Test that relevance scores are calculated based on query terms."""
        results = {
            'entities': [
                {
                    'name': 'search_entity',
                    'entityType': 'test',
                    'observations': ['This entity is about search functionality']
                },
                {
                    'name': 'unrelated_entity',
                    'entityType': 'other',
                    'observations': ['This has nothing to do with the query']
                }
            ],
            'relationships': []
        }
        query = "search effectiveness"

        scored = self.optimizer.score_results(results, query)

        # Should add relevance_score to entities
        self.assertIn('relevance_score', scored['entities'][0])
        self.assertIn('relevance_score', scored['entities'][1])

        # Entity with matching content should have higher score
        search_entity_score = scored['entities'][0]['relevance_score']
        unrelated_entity_score = scored['entities'][1]['relevance_score']
        self.assertGreaterEqual(search_entity_score, unrelated_entity_score)

    def test_score_results_sorts_by_relevance_descending(self):
        """Test that results are sorted by relevance score in descending order."""
        results = {
            'entities': [
                {
                    'name': 'low_relevance',
                    'entityType': 'test',
                    'observations': ['unrelated content']
                },
                {
                    'name': 'high_relevance',
                    'entityType': 'search',
                    'observations': ['search and effectiveness patterns']
                }
            ],
            'relationships': []
        }
        query = "search effectiveness"

        scored = self.optimizer.score_results(results, query)

        # Should be sorted with highest relevance first
        first_score = scored['entities'][0]['relevance_score']
        second_score = scored['entities'][1]['relevance_score']
        self.assertGreaterEqual(first_score, second_score)

        # High relevance entity should be first
        self.assertEqual(scored['entities'][0]['name'], 'high_relevance')

    # RED Phase: Test Pattern Learning
    def test_learn_patterns_successful_search(self):
        """Test learning patterns from successful search results."""
        query = "test query"
        terms = ['test', 'query']
        results = {'entities': [{'name': 'found_entity'}]}

        # Should not raise exception and should track pattern
        self.optimizer.learn_patterns(query, terms, results)

        pattern_key = 'test query'
        self.assertIn(pattern_key, self.optimizer.successful_patterns)
        self.assertEqual(self.optimizer.successful_patterns[pattern_key]['count'], 1)
        self.assertEqual(self.optimizer.successful_patterns[pattern_key]['entities_found'], 1)

    def test_learn_patterns_unsuccessful_search(self):
        """Test learning patterns from unsuccessful search (no entities found)."""
        query = "unsuccessful query"
        terms = ['unsuccessful', 'query']
        results = {'entities': []}  # No entities found

        # Should not add pattern for unsuccessful searches
        self.optimizer.learn_patterns(query, terms, results)

        pattern_key = 'unsuccessful query'
        self.assertNotIn(pattern_key, self.optimizer.successful_patterns)

    def test_learn_patterns_accumulates_counts(self):
        """Test that repeated successful patterns accumulate counts."""
        query = "repeated query"
        terms = ['repeated', 'query']
        results = {'entities': [{'name': 'entity1'}, {'name': 'entity2'}]}

        # Learn same pattern twice
        self.optimizer.learn_patterns(query, terms, results)
        self.optimizer.learn_patterns(query, terms, results)

        pattern_key = 'repeated query'
        self.assertEqual(self.optimizer.successful_patterns[pattern_key]['count'], 2)
        self.assertEqual(self.optimizer.successful_patterns[pattern_key]['entities_found'], 4)  # 2 entities × 2 calls

    # RED Phase: Test Error Handling
    @patch('memory_mcp_optimizer.logging_util')
    def test_transform_query_handles_exceptions(self, mock_logging):
        """Test that transform_query handles exceptions gracefully."""
        # Mock re.sub to raise an exception
        with patch('memory_mcp_optimizer.re.sub', side_effect=Exception("Test exception")):
            result = self.optimizer.transform_query("test query")

            # Should return empty list on error
            self.assertEqual(result, [])

            # Should log error
            mock_logging.error.assert_called()

    @patch('memory_mcp_optimizer.logging_util')
    def test_expand_concepts_handles_exceptions(self, mock_logging):
        """Test that expand_concepts handles exceptions gracefully."""
        # Mock dict operations to raise an exception
        with patch.object(self.optimizer, 'domain_mappings', side_effect=Exception("Test exception")):
            result = self.optimizer.expand_concepts(['test'])

            # Should return original concepts on error
            self.assertEqual(result, ['test'])

            # Should log error
            mock_logging.error.assert_called()

    @patch('memory_mcp_optimizer.logging_util')
    def test_merge_results_handles_exceptions(self, mock_logging):
        """Test that merge_results handles exceptions gracefully."""
        # Create malformed search results
        malformed_results = [{'entities': 'invalid_format'}]  # Should be list, not string

        # Should not crash and return empty structure
        result = self.optimizer.merge_results(malformed_results)

        self.assertEqual(result, {'entities': [], 'relationships': []})
        mock_logging.error.assert_called()

    @patch('memory_mcp_optimizer.logging_util')
    def test_score_results_handles_exceptions(self, mock_logging):
        """Test that score_results handles exceptions gracefully."""
        # Create results that will cause scoring errors
        results = {'entities': [{'name': None}], 'relationships': []}  # None name will cause issues

        # Should not crash and return original results
        result = self.optimizer.score_results(results, "test query")

        # Should return results even if scoring fails
        self.assertIn('entities', result)

    # GREEN Phase: Test Integration Scenarios
    def test_full_optimization_workflow(self):
        """Integration test: Complete optimization workflow from query to scored results."""
        # Simulate full workflow like /memory search command would use
        original_query = "Memory MCP search effectiveness patterns"

        # Step 1: Optimize query
        optimized_terms = self.optimizer.optimize_query(original_query)
        self.assertIsInstance(optimized_terms, list)
        self.assertGreater(len(optimized_terms), 0)

        # Step 2: Simulate multiple search results (like from Memory MCP)
        simulated_search_results = [
            {
                'entities': [
                    {'name': 'memory_pattern_1', 'entityType': 'pattern', 'observations': ['search effectiveness analysis']}
                ],
                'relationships': []
            },
            {
                'entities': [
                    {'name': 'mcp_integration', 'entityType': 'integration', 'observations': ['memory mcp optimization']}
                ],
                'relationships': [{'from': 'memory_pattern_1', 'to': 'mcp_integration', 'relationType': 'uses'}]
            }
        ]

        # Step 3: Merge results
        merged_results = self.optimizer.merge_results(simulated_search_results)
        self.assertEqual(len(merged_results['entities']), 2)
        self.assertEqual(len(merged_results['relationships']), 1)

        # Step 4: Score results
        scored_results = self.optimizer.score_results(merged_results, original_query)
        self.assertEqual(len(scored_results['entities']), 2)

        # All entities should have relevance scores
        for entity in scored_results['entities']:
            self.assertIn('relevance_score', entity)
            self.assertGreaterEqual(entity['relevance_score'], MIN_RELEVANCE_SCORE)

        # Step 5: Learn patterns
        self.optimizer.learn_patterns(original_query, optimized_terms, scored_results)

        # Should have learned the successful pattern
        pattern_keys = list(self.optimizer.successful_patterns.keys())
        self.assertGreater(len(pattern_keys), 0)

    # GREEN Phase: Test Constants Usage
    def test_constants_are_used_correctly(self):
        """Test that defined constants are actually used in the code."""
        # Test MAX_TERMS constant
        long_query = " ".join([f"term{i}" for i in range(MAX_TERMS + 5)])  # More terms than limit
        result = self.optimizer.optimize_query(long_query)
        self.assertLessEqual(len(result), MAX_TERMS)

        # Test MIN_RELEVANCE_SCORE constant (implicitly through scoring)
        results = {'entities': [{'name': 'test', 'entityType': 'test', 'observations': []}], 'relationships': []}
        scored = self.optimizer.score_results(results, "unrelated query")

        # Even unrelated queries should have scores >= MIN_RELEVANCE_SCORE
        self.assertGreaterEqual(scored['entities'][0]['relevance_score'], MIN_RELEVANCE_SCORE)

    # REFACTOR Phase: Test Edge Cases
    def test_optimize_query_with_none_input(self):
        """Test optimization with None input."""
        result = self.optimizer.optimize_query(None)
        # Should handle None gracefully and return empty list
        self.assertEqual(result, [])

    def test_domain_mappings_completeness(self):
        """Test that domain mappings are comprehensive for key terms."""
        # These terms should have mappings based on investigation findings
        key_terms = ['search', 'effectiveness', 'memory', 'results', 'patterns', 'investigation']

        for term in key_terms:
            self.assertIn(term, self.optimizer.domain_mappings,
                         f"Domain mapping missing for key term: {term}")
            self.assertIsInstance(self.optimizer.domain_mappings[term], list)
            self.assertGreater(len(self.optimizer.domain_mappings[term]), 0)

    def test_unique_terms_preservation(self):
        """Test that duplicate terms are properly handled in expansion."""
        concepts = ['search', 'search', 'effectiveness']  # Intentional duplicate
        result = self.optimizer.expand_concepts(concepts)

        # Should not have duplicates in final result
        self.assertEqual(len(result), len(set(result)))


class TestMemoryMCPOptimizerCLI(unittest.TestCase):
    """Test suite for Memory MCP Optimizer CLI functionality."""

    @patch('sys.argv', ['memory_mcp_optimizer.py', '--test'])
    @patch('memory_mcp_optimizer.MemoryMCPOptimizer')
    def test_main_test_mode(self, mock_optimizer_class):
        """Test main function in test mode."""
        mock_optimizer = MagicMock()
        mock_optimizer_class.return_value = mock_optimizer
        mock_optimizer.optimize_query.return_value = ['test', 'terms']
        mock_optimizer.successful_patterns = {'test pattern': {}}

        # Import and run main (should not raise exception)
        from memory_mcp_optimizer import main

        # Should complete without error
        try:
            main()
        except SystemExit:
            pass  # Normal exit is fine

    @patch('sys.argv', ['memory_mcp_optimizer.py', 'single query test'])
    @patch('memory_mcp_optimizer.MemoryMCPOptimizer')
    def test_main_single_query_mode(self, mock_optimizer_class):
        """Test main function with single query."""
        mock_optimizer = MagicMock()
        mock_optimizer_class.return_value = mock_optimizer
        mock_optimizer.optimize_query.return_value = ['single', 'query', 'test']

        # Import and run main (should not raise exception)
        from memory_mcp_optimizer import main

        try:
            main()
        except SystemExit:
            pass  # Normal exit is fine

        # Should have called optimize_query with the provided query
        mock_optimizer.optimize_query.assert_called_with('single query test')


if __name__ == '__main__':
    # Configure test environment
    os.environ['TESTING'] = 'true'

    unittest.main(verbosity=2)
