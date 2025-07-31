#!/usr/bin/env python
"""Demonstration of Memory MCP Integration

This script shows how memory integration enhances LLM responses.
"""

import sys

sys.path.insert(0, 'mvp_site')

from memory_integration import enhance_slash_command, memory_integration


def demo_query_extraction():
    """Show query term extraction"""
    print("=== Query Term Extraction Demo ===")

    test_inputs = [
        "How do I fix GitHub API errors?",
        "Review PR #609 for compliance issues",
        "Debug the ImportError in auth module",
        "What's the proper git workflow?"
    ]

    for user_input in test_inputs:
        terms = memory_integration.extract_query_terms(user_input)
        print(f"\nInput: {user_input}")
        print(f"Extracted terms: {terms}")

def demo_memory_search():
    """Show memory search in action"""
    print("\n\n=== Memory Search Demo ===")

    # Search for git-related memories
    print("\nSearching for 'git' memories...")
    memories = memory_integration.search_relevant_memory(['git'])

    for memory in memories:
        print(f"\nFound: {memory.get('name')} ({memory.get('entityType')})")
        for obs in memory.get('observations', [])[:2]:
            print(f"  - {obs}")

def demo_slash_command_enhancement():
    """Show slash command enhancement"""
    print("\n\n=== Slash Command Enhancement Demo ===")

    commands = [
        ("/learn", "test execution patterns"),
        ("/debug", "urgent context issue"),
        ("/think", "git workflow optimization"),
        ("/push", "feature branch")  # This shouldn't get enhanced
    ]

    for cmd, args in commands:
        print(f"\nCommand: {cmd} {args}")
        context = enhance_slash_command(cmd, args)
        if context:
            print("Enhanced with memory context:")
            print(context[:200] + "..." if len(context) > 200 else context)
        else:
            print("No memory enhancement (command not in enhanced list)")

def demo_relevance_scoring():
    """Show relevance scoring"""
    print("\n\n=== Relevance Scoring Demo ===")

    # Mock entity for scoring
    entity = {
        "name": "urgent_context_pattern",
        "entityType": "pattern",
        "observations": [
            "When jleechan2015 mentions 'urgent' or 'context', they want minimal changes",
            "Skip comprehensive refactoring when context is low"
        ]
    }

    queries = [
        "urgent fix needed",
        "context is getting low",
        "random unrelated query",
        "pattern analysis"
    ]

    for query in queries:
        score = memory_integration.calculate_relevance_score(entity, query)
        print(f"\nQuery: '{query}'")
        print(f"Relevance score: {score:.2f}")

def demo_performance_metrics():
    """Show performance tracking"""
    print("\n\n=== Performance Metrics Demo ===")

    # Do some searches to generate metrics
    for _ in range(3):
        memory_integration.search_relevant_memory(['test'])

    metrics = memory_integration.metrics
    print(f"Cache hit rate: {metrics.cache_hit_rate:.1%}")
    print(f"Average latency: {metrics.avg_latency:.3f}s")
    print(f"Total queries: {metrics.cache_hits + metrics.cache_misses}")

if __name__ == "__main__":
    print("Memory MCP Integration Demonstration")
    print("=" * 40)

    demo_query_extraction()
    demo_memory_search()
    demo_slash_command_enhancement()
    demo_relevance_scoring()
    demo_performance_metrics()

    print("\n\n=== Integration Complete ===")
    print("The memory system is ready to enhance LLM responses!")
    print("\nTo enable in production:")
    print("1. Replace mcp_memory_stub.py with real MCP calls")
    print("2. Add memory enhancement to slash command processing")
    print("3. Enable pre-response memory checks")
    print("4. Monitor performance metrics")
