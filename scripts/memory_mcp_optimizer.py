#!/usr/bin/env python3
"""
Memory MCP Query Optimization Engine
Transforms compound search phrases into effective single-word queries to improve search success rates.

Based on investigation showing:
- Single-word queries (investigation, search) return 2-9 entities
- Compound phrases return 0 entities
- Goal: Improve success rate from ~30% to 70%+
"""

import argparse
import json
import os
import re
import sys
from typing import List, Dict, Any

# Add mvp_site to path for logging_util import
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mvp_site'))
import logging_util

# Use project logging utility
logger = logging_util.getLogger(__name__)

# Constants for magic numbers
MAX_TERMS = 6  # Maximum number of optimized terms to prevent over-expansion
MIN_RELEVANCE_SCORE = 0.0  # Minimum relevance score for results
DEFAULT_EXPANSION_LIMIT = 4  # Default limit for semantic expansion per concept

class MemoryMCPOptimizer:
    """
    Query Optimization Engine for Memory MCP that transforms compound search phrases
    into effective single-word queries to improve search success rates.
    """

    def __init__(self) -> None:
        # Domain concept mappings for semantic expansion
        self.domain_mappings = {
            'search': ['search', 'query', 'lookup', 'find'],
            'effectiveness': ['effectiveness', 'efficiency', 'success', 'performance'],
            'empty': ['empty', 'null', 'void', 'zero'],
            'results': ['results', 'outcomes', 'findings', 'responses'],
            'patterns': ['patterns', 'structures', 'templates', 'models'],
            'investigation': ['investigation', 'analysis', 'research', 'study'],
            'knowledge': ['knowledge', 'information', 'data', 'insights'],
            'decision': ['decision', 'choice', 'selection', 'determination'],
            'optimization': ['optimization', 'improvement', 'enhancement', 'refinement'],
            'memory': ['memory', 'storage', 'retention', 'recall'],
            'mcp': ['mcp', 'protocol', 'server', 'integration'],
            'tool': ['tool', 'function', 'utility', 'instrument'],
            'workflow': ['workflow', 'process', 'procedure', 'method'],
            'failure': ['failure', 'error', 'issue', 'problem'],
            'success': ['success', 'achievement', 'completion', 'victory']
        }

        # Track successful query transformations
        self.successful_patterns = {}

    def transform_query(self, compound_query: str) -> List[str]:
        """
        Split compound phrases into constituent concepts.

        Args:
            compound_query: The compound search query to transform

        Returns:
            List of individual words/concepts from the query
        """
        try:
            # Handle None input
            if compound_query is None:
                logging_util.error("Query cannot be None")
                return []

            # Normalize the query: lowercase, replace special characters with spaces
            normalized_query = re.sub(r'[^a-zA-Z0-9\s]', ' ', compound_query.lower())

            # Split into words and remove empty strings
            words = [word.strip() for word in normalized_query.split() if word.strip()]

            logging_util.info(f"Transformed compound query '{compound_query}' into words: {words}")
            return words
        except Exception as e:
            logging_util.error(f"Error transforming query '{compound_query}': {str(e)}")
            return []

    def expand_concepts(self, concepts: List[str]) -> List[str]:
        """
        Map concepts to domain-specific single words using semantic expansion.

        Args:
            concepts: List of concepts to expand

        Returns:
            Expanded list of domain-specific search terms
        """
        try:
            expanded_terms = []

            for concept in concepts:
                # If we have a mapping for this concept, use it
                if concept in self.domain_mappings:
                    expanded_terms.extend(self.domain_mappings[concept])
                else:
                    # Otherwise, just use the original concept
                    expanded_terms.append(concept)

            # Remove duplicates while preserving order
            unique_terms = list(dict.fromkeys(expanded_terms))

            logging_util.info(f"Expanded concepts {concepts} into terms: {unique_terms}")
            return unique_terms
        except Exception as e:
            logging_util.error(f"Error expanding concepts {concepts}: {str(e)}")
            return concepts

    def optimize_query(self, compound_query: str) -> List[str]:
        """
        Complete optimization pipeline: transform compound query into optimized single-word queries.

        Args:
            compound_query: Original compound search query

        Returns:
            Optimized single-word queries for best results
        """
        try:
            # Step 1: Transform compound query into words
            words = self.transform_query(compound_query)

            # Step 2: Expand concepts semantically
            expanded_terms = self.expand_concepts(words)

            # Step 3: Select best terms (prioritize original concepts, limit expansion)
            # Keep original words first, then add semantic expansions up to reasonable limit
            optimized_terms = []

            # Add original words first (up to MAX_TERMS limit)
            for word in words:
                if word not in optimized_terms and len(optimized_terms) < MAX_TERMS:
                    optimized_terms.append(word)

            # Add expanded terms strategically (avoid over-expansion)
            for term in expanded_terms:
                if term not in optimized_terms and len(optimized_terms) < MAX_TERMS:
                    optimized_terms.append(term)

            logging_util.info(f"Optimized '{compound_query}' into final terms: {optimized_terms}")
            return optimized_terms

        except Exception as e:
            logging_util.error(f"Error optimizing query '{compound_query}': {str(e)}")
            return [compound_query]  # Fallback to original

    def merge_results(self, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge results from multiple single-word searches.

        Args:
            search_results: List of search result dictionaries

        Returns:
            Merged search results with deduplication
        """
        try:
            merged_entities = []
            merged_relationships = []
            seen_entity_ids = set()
            seen_relationship_ids = set()

            # Iterate through all search results
            for result in search_results:
                # Merge entities
                if 'entities' in result:
                    for entity in result['entities']:
                        entity_id = entity.get('id') or entity.get('name')
                        if entity_id and entity_id not in seen_entity_ids:
                            merged_entities.append(entity)
                            seen_entity_ids.add(entity_id)

                # Merge relationships
                if 'relationships' in result:
                    for relationship in result['relationships']:
                        rel_id = relationship.get('id') or f"{relationship.get('from')}->{relationship.get('to')}"
                        if rel_id and rel_id not in seen_relationship_ids:
                            merged_relationships.append(relationship)
                            seen_relationship_ids.add(rel_id)

            merged_result = {
                'entities': merged_entities,
                'relationships': merged_relationships
            }

            logging_util.info(f"Merged {len(search_results)} search results into {len(merged_entities)} entities and {len(merged_relationships)} relationships")
            return merged_result
        except Exception as e:
            logging_util.error(f"Error merging search results: {str(e)}")
            return {'entities': [], 'relationships': []}

    def score_results(self, results: Dict[str, Any], original_query: str) -> Dict[str, Any]:
        """
        Score and rank results by relevance to original compound query.

        Args:
            results: Merged search results
            original_query: Original compound query for relevance scoring

        Returns:
            Results with relevance scores added
        """
        try:
            original_words = set(self.transform_query(original_query))
            scored_entities = []

            for entity in results.get('entities', []):
                # Calculate relevance score based on term matches
                entity_text = ' '.join([
                    str(entity.get('name', '')),
                    str(entity.get('entityType', '')),
                    ' '.join(entity.get('observations', []))
                ]).lower()

                # Count matches with original query terms
                matches = sum(1 for word in original_words if word in entity_text)
                relevance_score = matches / len(original_words) if original_words else 0

                # Add score to entity
                entity_with_score = entity.copy()
                entity_with_score['relevance_score'] = relevance_score
                scored_entities.append(entity_with_score)

            # Sort by relevance score (highest first)
            scored_entities.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)

            scored_results = results.copy()
            scored_results['entities'] = scored_entities

            logging_util.info(f"Scored {len(scored_entities)} entities for relevance to '{original_query}'")
            return scored_results

        except Exception as e:
            logging_util.error(f"Error scoring results for query '{original_query}': {str(e)}")
            return results

    def learn_patterns(self, original_query: str, optimized_terms: List[str], search_results: Dict[str, Any]) -> None:
        """
        Track successful query transformations for improvement.

        Args:
            original_query: The original compound query
            optimized_terms: The terms used in optimized search
            search_results: Results from the search
        """
        try:
            # Count how many entities were found
            entity_count = len(search_results.get('entities', []))

            # If we found entities, record this as a successful pattern
            if entity_count > 0:
                pattern_key = ' '.join(optimized_terms)
                if pattern_key not in self.successful_patterns:
                    self.successful_patterns[pattern_key] = {
                        'count': 0,
                        'entities_found': 0,
                        'original_queries': []
                    }

                self.successful_patterns[pattern_key]['count'] += 1
                self.successful_patterns[pattern_key]['entities_found'] += entity_count
                self.successful_patterns[pattern_key]['original_queries'].append(original_query)

                logging_util.info(f"Learned successful pattern: '{original_query}' -> {optimized_terms} (found {entity_count} entities)")
            else:
                logging_util.info(f"No entities found for query '{original_query}', pattern not recorded")
        except Exception as e:
            logging_util.error(f"Error learning patterns for query '{original_query}': {str(e)}")

def main() -> None:
    """Real CLI for Memory MCP Optimizer with argparse"""
    parser = argparse.ArgumentParser(
        description='Memory MCP Query Optimizer - Transform compound queries into optimized single-word searches'
    )
    parser.add_argument(
        'query',
        nargs='?',
        help='Query to optimize (if not provided, runs test mode)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run test mode with predefined queries'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging output'
    )

    args = parser.parse_args()

    if args.verbose:
        logging_util.getLogger().setLevel(logging_util.DEBUG)

    optimizer = MemoryMCPOptimizer()

    if args.test or not args.query:
        # Test mode with real optimization patterns
        test_queries = [
            "search effectiveness empty results query patterns",
            "Memory MCP search empty results",
            "Memory MCP tool call effectiveness",
            "workflow debugging pattern analysis",
            "investigation memory optimization"
        ]

        print("🔍 Memory MCP Query Optimizer Testing")
        print("=" * 50)

        for query in test_queries:
            print(f"\n📊 Testing query: '{query}'")
            optimized = optimizer.optimize_query(query)
            print(f"✅ Optimized terms: {optimized}")

            # For testing, create realistic results structure
            test_results = {
                'entities': [{
                    'name': f'entity_{i}',
                    'entityType': 'test_result',
                    'observations': [f'Test observation for {term}']
                } for i, term in enumerate(optimized[:2])]
            }
            optimizer.learn_patterns(query, optimized, test_results)

        print(f"\n📈 Learned patterns: {len(optimizer.successful_patterns)}")
        print("🚀 Memory MCP Query Optimizer ready for integration!")
    else:
        # Single query optimization mode
        print(f"🔍 Optimizing query: '{args.query}'")
        optimized_terms = optimizer.optimize_query(args.query)
        print(f"✅ Optimized terms: {optimized_terms}")

        # Output in JSON format for scripting integration
        result = {
            'original_query': args.query,
            'optimized_terms': optimized_terms,
            'term_count': len(optimized_terms)
        }
        print(f"📊 JSON Result: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    main()
