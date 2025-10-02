"""Test suite for memory integration"""

import os
import sys
import unittest
from unittest.mock import patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mvp_site.memory_integration import MemoryIntegration, enhance_slash_command


class TestMemoryIntegration(unittest.TestCase):
    def setUp(self):
        self.memory = MemoryIntegration()

    def test_extract_query_terms(self):
        """Test query term extraction"""
        # Test entity extraction
        terms = self.memory.extract_query_terms("Fix the GitHub API integration")
        assert "github" in [t.lower() for t in terms]
        assert "api" in [t.lower() for t in terms]

        # Test PR extraction
        terms = self.memory.extract_query_terms("Review PR #609 changes")
        assert "PR #609" in terms

        # Test stop word removal
        terms = self.memory.extract_query_terms("the is at which on")
        assert len(terms) == 0

    def test_relevance_scoring(self):
        """Test relevance score calculation"""
        entity = {
            "name": "git_workflow",
            "entityType": "pattern",
            "observations": ["All changes through PRs", "Never push to main"],
        }

        # High relevance - name match
        score = self.memory.calculate_relevance_score(entity, "git workflow issues")
        assert score > 0.35  # Should get 0.4 for name match

        # Medium relevance - type match
        score = self.memory.calculate_relevance_score(entity, "coding patterns")
        assert score > 0.1

        # Low relevance - no match
        score = self.memory.calculate_relevance_score(entity, "unrelated topic")
        assert score < 0.3

    def test_search_with_caching(self):
        """Test search with cache behavior"""
        with patch("memory_mcp_real.search_nodes") as mock_search:
            mock_search.return_value = [{"name": "test_entity", "entityType": "test"}]

            # First search - cache miss
            results1 = self.memory.search_relevant_memory(["test"])
            assert mock_search.call_count == 1

            # Second search - cache hit
            results2 = self.memory.search_relevant_memory(["test"])
            assert mock_search.call_count == 1  # No additional call
            assert results1 == results2

    def test_context_enhancement(self):
        """Test context enhancement with memories"""
        memories = [
            {
                "name": "urgent_pattern",
                "entityType": "pattern",
                "observations": ["Use minimal changes", "Skip refactoring"],
            }
        ]

        enhanced = self.memory.enhance_context("Original context", memories)
        assert "Relevant Memory Context" in enhanced
        assert "urgent_pattern" in enhanced
        assert "Use minimal changes" in enhanced

    def test_slash_command_enhancement(self):
        """Test slash command enhancement"""
        # Should enhance memory commands
        context = enhance_slash_command("/learn", "test pattern")
        assert isinstance(context, str)

        # Should not enhance other commands
        context = enhance_slash_command("/push", "some args")
        assert context == ""

    def test_error_handling(self):
        """Test graceful error handling"""
        with patch("memory_mcp_real.search_nodes") as mock_search:
            mock_search.side_effect = Exception("MCP unavailable")

            # Should return empty list on error
            results = self.memory.search_relevant_memory(["test"])
            assert results == []

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


if __name__ == "__main__":
    unittest.main()
