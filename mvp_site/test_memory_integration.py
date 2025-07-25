"""Test suite for memory integration"""

import unittest
from unittest.mock import Mock, patch

from memory_integration import MemoryIntegration, enhance_slash_command


class TestMemoryIntegration(unittest.TestCase):

    def setUp(self):
        self.memory = MemoryIntegration()

    def test_extract_query_terms(self):
        """Test query term extraction"""
        # Test entity extraction
        terms = self.memory.extract_query_terms("Fix the GitHub API integration")
        self.assertIn("github", [t.lower() for t in terms])
        self.assertIn("api", [t.lower() for t in terms])

        # Test PR extraction
        terms = self.memory.extract_query_terms("Review PR #609 changes")
        self.assertIn("PR #609", terms)

        # Test stop word removal
        terms = self.memory.extract_query_terms("the is at which on")
        self.assertEqual(len(terms), 0)

    def test_relevance_scoring(self):
        """Test relevance score calculation"""
        entity = {
            "name": "git_workflow",
            "entityType": "pattern",
            "observations": ["All changes through PRs", "Never push to main"]
        }

        # High relevance - name match
        score = self.memory.calculate_relevance_score(entity, "git workflow issues")
        self.assertGreater(score, 0.35)  # Should get 0.4 for name match

        # Medium relevance - type match
        score = self.memory.calculate_relevance_score(entity, "coding patterns")
        self.assertGreater(score, 0.1)

        # Low relevance - no match
        score = self.memory.calculate_relevance_score(entity, "unrelated topic")
        self.assertLess(score, 0.3)

    def test_search_with_caching(self):
        """Test search with cache behavior"""
        with patch('memory_mcp_real.search_nodes') as mock_search:
            mock_search.return_value = [{"name": "test_entity", "entityType": "test"}]

            # First search - cache miss
            results1 = self.memory.search_relevant_memory(["test"])
            self.assertEqual(mock_search.call_count, 1)

            # Second search - cache hit
            results2 = self.memory.search_relevant_memory(["test"])
            self.assertEqual(mock_search.call_count, 1)  # No additional call
            self.assertEqual(results1, results2)

    def test_context_enhancement(self):
        """Test context enhancement with memories"""
        memories = [{
            "name": "urgent_pattern",
            "entityType": "pattern",
            "observations": ["Use minimal changes", "Skip refactoring"]
        }]

        enhanced = self.memory.enhance_context("Original context", memories)
        self.assertIn("Relevant Memory Context", enhanced)
        self.assertIn("urgent_pattern", enhanced)
        self.assertIn("Use minimal changes", enhanced)

    def test_slash_command_enhancement(self):
        """Test slash command enhancement"""
        # Should enhance memory commands
        context = enhance_slash_command("/learn", "test pattern")
        self.assertIsInstance(context, str)

        # Should not enhance other commands
        context = enhance_slash_command("/push", "some args")
        self.assertEqual(context, "")

    def test_error_handling(self):
        """Test graceful error handling"""
        with patch('memory_mcp_real.search_nodes') as mock_search:
            mock_search.side_effect = Exception("MCP unavailable")

            # Should return empty list on error
            results = self.memory.search_relevant_memory(["test"])
            self.assertEqual(results, [])

    def test_metrics_tracking(self):
        """Test performance metrics"""
        metrics = self.memory.metrics

        # Record some queries
        metrics.record_query(True, 0.01)  # Cache hit
        metrics.record_query(False, 0.05)  # Cache miss
        metrics.record_query(True, 0.02)  # Cache hit

        # Check metrics
        self.assertAlmostEqual(metrics.cache_hit_rate, 0.667, places=2)
        self.assertAlmostEqual(metrics.avg_latency, 0.0267, places=3)


if __name__ == '__main__':
    unittest.main()
