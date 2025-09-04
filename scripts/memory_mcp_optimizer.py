#!/usr/bin/env python3
"""
Memory MCP Query Optimization Engine
Transforms compound search phrases into effective single-word queries to improve search success rates.

Based on investigation showing:
- Single-word queries (investigation, search) return 2-9 entities
- Compound phrases return 0 entities
- Goal: Improve success rate from ~30% to 70%+
"""

import logging
from typing import List, Dict, Any, Optional
import re
from collections import Counter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MemoryMCPOptimizer:
    """
    Query Optimization Engine for Memory MCP that transforms compound search phrases
    into effective single-word queries to improve search success rates.
    """

    def __init__(self):
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
            compound_query (str): The compound search query to transform

        Returns:
            List[str]: List of individual words/concepts from the query
        """
        try:
            # Normalize the query: lowercase, remove special characters
            normalized_query = re.sub(r'[^a-zA-Z0-9\s]', '', compound_query.lower())

            # Split into words and remove empty strings
            words = [word.strip() for word in normalized_query.split() if word.strip()]

            logger.info(f"Transformed compound query '{compound_query}' into words: {words}")
            return words
        except Exception as e:
            logger.error(f"Error transforming query '{compound_query}': {str(e)}")
            return []

    def expand_concepts(self, concepts: List[str]) -> List[str]:
        """
        Map concepts to domain-specific single words using semantic expansion.

        Args:
            concepts (List[str]): List of concepts to expand

        Returns:
            List[str]: Expanded list of domain-specific search terms
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

            logger.info(f"Expanded concepts {concepts} into terms: {unique_terms}")
            return unique_terms
        except Exception as e:
            logger.error(f"Error expanding concepts {concepts}: {str(e)}")
            return concepts

    def optimize_query(self, compound_query: str) -> List[str]:
        """
        Complete optimization pipeline: transform compound query into optimized single-word queries.

        Args:
            compound_query (str): Original compound search query

        Returns:
            List[str]: Optimized single-word queries for best results
        """
        try:
            # Step 1: Transform compound query into words
            words = self.transform_query(compound_query)

            # Step 2: Expand concepts semantically
            expanded_terms = self.expand_concepts(words)

            # Step 3: Select best terms (prioritize original concepts, limit expansion)
            # Keep original words first, then add semantic expansions up to reasonable limit
            optimized_terms = []

            # Add original words first
            for word in words:
                if word not in optimized_terms:
                    optimized_terms.append(word)

            # Add expanded terms strategically (avoid over-expansion)
            for term in expanded_terms:
                if term not in optimized_terms and len(optimized_terms) < 6:  # Limit to 6 terms max
                    optimized_terms.append(term)

            logger.info(f"Optimized '{compound_query}' into final terms: {optimized_terms}")
            return optimized_terms

        except Exception as e:
            logger.error(f"Error optimizing query '{compound_query}': {str(e)}")
            return [compound_query]  # Fallback to original

    def merge_results(self, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge results from multiple single-word searches.

        Args:
            search_results (List[Dict[str, Any]]): List of search result dictionaries

        Returns:
            Dict[str, Any]: Merged search results with deduplication
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

            logger.info(f"Merged {len(search_results)} search results into {len(merged_entities)} entities and {len(merged_relationships)} relationships")
            return merged_result
        except Exception as e:
            logger.error(f"Error merging search results: {str(e)}")
            return {'entities': [], 'relationships': []}

    def score_results(self, results: Dict[str, Any], original_query: str) -> Dict[str, Any]:
        """
        Score and rank results by relevance to original compound query.

        Args:
            results (Dict[str, Any]): Merged search results
            original_query (str): Original compound query for relevance scoring

        Returns:
            Dict[str, Any]: Results with relevance scores added
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

            logger.info(f"Scored {len(scored_entities)} entities for relevance to '{original_query}'")
            return scored_results

        except Exception as e:
            logger.error(f"Error scoring results for query '{original_query}': {str(e)}")
            return results

    def learn_patterns(self, original_query: str, optimized_terms: List[str], search_results: Dict[str, Any]) -> None:
        """
        Track successful query transformations for improvement.

        Args:
            original_query (str): The original compound query
            optimized_terms (List[str]): The terms used in optimized search
            search_results (Dict[str, Any]): Results from the search
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

                logger.info(f"Learned successful pattern: '{original_query}' -> {optimized_terms} (found {entity_count} entities)")
            else:
                logger.info(f"No entities found for query '{original_query}', pattern not recorded")
        except Exception as e:
            logger.error(f"Error learning patterns for query '{original_query}': {str(e)}")

def main():
    """Example usage and testing of the Memory MCP Optimizer"""
    optimizer = MemoryMCPOptimizer()

    # Test queries based on investigation findings
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

        # Simulate learning (in real usage, this would come from actual Memory MCP results)
        simulated_results = {'entities': [{'name': f'Result for {term}', 'relevance_score': 0.8}] for term in optimized[:2]}
        optimizer.learn_patterns(query, optimized, simulated_results)

    print(f"\n📈 Learned patterns: {len(optimizer.successful_patterns)}")
    print("🚀 Memory MCP Query Optimizer ready for integration!")

if __name__ == "__main__":
    main()
