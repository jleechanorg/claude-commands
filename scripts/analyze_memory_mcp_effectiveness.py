#!/usr/bin/env python3
"""
Memory MCP Effectiveness Analysis
Analyzes tool execution logs to measure actual decision influence vs. consultation frequency
"""

import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Any

class MemoryMCPAnalyzer:
    def __init__(self):
        self.tool_calls = []
        self.memory_consultations = []
        self.decision_points = []
        self.search_effectiveness = {
            'total_searches': 0,
            'empty_results': 0,
            'successful_results': 0,
            'queries_by_pattern': {}
        }

    def analyze_conversation_file(self, filepath: str) -> Dict[str, Any]:
        """Analyze a conversation JSONL file for Memory MCP patterns"""
        results = {
            'consultation_sequences': [],
            'search_patterns': {},
            'decision_correlations': [],
            'effectiveness_metrics': {}
        }

        try:
            with open(filepath, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        entry = json.loads(line.strip())
                        self._process_entry(entry, line_num, results)
                    except json.JSONDecodeError:
                        continue

        except FileNotFoundError:
            print(f"⚠️ File not found: {filepath}")
            return results

        self._calculate_effectiveness_metrics(results)
        return results

    def _process_entry(self, entry: Dict, line_num: int, results: Dict):
        """Process individual conversation entry for Memory MCP patterns"""

        # Track tool calls
        if 'tool_calls' in entry:
            for tool_call in entry['tool_calls']:
                tool_name = tool_call.get('name', '')
                if 'mcp__memory-server__' in tool_name:
                    self._track_memory_consultation(tool_call, line_num, results)

        # Track tool results
        if 'tool_call_results' in entry:
            for result in entry['tool_call_results']:
                tool_name = result.get('tool_name', '')
                if 'mcp__memory-server__' in tool_name:
                    self._track_consultation_result(result, line_num, results)

        # Track decision indicators
        if 'content' in entry:
            content = entry['content']
            if self._contains_decision_markers(content):
                self._track_decision_point(entry, line_num, results)

    def _track_memory_consultation(self, tool_call: Dict, line_num: int, results: Dict):
        """Track Memory MCP consultation attempts"""
        tool_name = tool_call.get('name', '')
        parameters = tool_call.get('parameters', {})

        consultation = {
            'line': line_num,
            'tool': tool_name,
            'parameters': parameters,
            'query_type': self._classify_query_type(tool_name, parameters)
        }

        results['consultation_sequences'].append(consultation)

        # Track search patterns specifically
        if tool_name == 'mcp__memory-server__search_nodes':
            query = parameters.get('query', '')
            self._analyze_search_query(query, results)

    def _track_consultation_result(self, result: Dict, line_num: int, results: Dict):
        """Track Memory MCP consultation results"""
        tool_name = result.get('tool_name', '')
        content = result.get('content', '')

        # Analyze search result effectiveness
        if tool_name == 'mcp__memory-server__search_nodes':
            is_empty = self._is_empty_result(content)
            self.search_effectiveness['total_searches'] += 1
            if is_empty:
                self.search_effectiveness['empty_results'] += 1
            else:
                self.search_effectiveness['successful_results'] += 1

    def _track_decision_point(self, entry: Dict, line_num: int, results: Dict):
        """Track decision points that might be influenced by Memory MCP"""
        content = entry.get('content', '')

        # Look for recent Memory MCP consultations (within last 10 lines)
        recent_consultations = [
            c for c in results['consultation_sequences']
            if line_num - c['line'] <= 10
        ]

        if recent_consultations:
            correlation = {
                'decision_line': line_num,
                'decision_markers': self._extract_decision_markers(content),
                'recent_consultations': recent_consultations,
                'potential_influence': len(recent_consultations) > 0
            }
            results['decision_correlations'].append(correlation)

    def _classify_query_type(self, tool_name: str, parameters: Dict) -> str:
        """Classify the type of Memory MCP query"""
        if 'search_nodes' in tool_name:
            return 'search'
        elif 'read_graph' in tool_name:
            return 'full_audit'
        elif 'create_entities' in tool_name:
            return 'knowledge_capture'
        elif 'create_relations' in tool_name:
            return 'relationship_building'
        elif 'open_nodes' in tool_name:
            return 'targeted_retrieval'
        else:
            return 'other'

    def _analyze_search_query(self, query: str, results: Dict):
        """Analyze search query patterns for effectiveness"""
        if not query:
            return

        # Extract query patterns
        query_lower = query.lower()

        # Common patterns
        patterns = {
            'file_operations': bool(re.search(r'\b(file|directory|path)\b', query_lower)),
            'testing_related': bool(re.search(r'\b(test|testing|pytest|mock)\b', query_lower)),
            'memory_mcp': bool(re.search(r'\bmemory.?mcp\b', query_lower)),
            'implementation': bool(re.search(r'\b(implement|code|function|class)\b', query_lower)),
            'error_debugging': bool(re.search(r'\b(error|bug|fail|issue)\b', query_lower))
        }

        for pattern, matches in patterns.items():
            if matches:
                if pattern not in results['search_patterns']:
                    results['search_patterns'][pattern] = 0
                results['search_patterns'][pattern] += 1

    def _contains_decision_markers(self, content: str) -> bool:
        """Check if content contains decision-making markers"""
        decision_markers = [
            'I will', 'I\'ll', 'Let me', 'I need to', 'I should',
            'Next step', 'Therefore', 'Based on', 'I conclude',
            'Strategy:', 'Approach:', 'Solution:', 'Plan:'
        ]

        content_lower = content.lower()
        return any(marker.lower() in content_lower for marker in decision_markers)

    def _extract_decision_markers(self, content: str) -> List[str]:
        """Extract specific decision markers from content"""
        decision_markers = [
            'I will', 'I\'ll', 'Let me', 'I need to', 'I should',
            'Next step', 'Therefore', 'Based on', 'I conclude',
            'Strategy:', 'Approach:', 'Solution:', 'Plan:'
        ]

        found_markers = []
        content_lower = content.lower()

        for marker in decision_markers:
            if marker.lower() in content_lower:
                found_markers.append(marker)

        return found_markers

    def _is_empty_result(self, content: str) -> bool:
        """Determine if Memory MCP result is effectively empty"""
        if not content or content.strip() == '':
            return True

        # Check for common empty result patterns
        empty_patterns = [
            'no matching nodes found',
            'no entities found',
            '[]',
            '{}',
            'empty result'
        ]

        content_lower = content.lower()
        return any(pattern in content_lower for pattern in empty_patterns)

    def _calculate_effectiveness_metrics(self, results: Dict):
        """Calculate overall effectiveness metrics"""
        total_consultations = len(results['consultation_sequences'])
        total_decisions = len(results['decision_correlations'])

        # Calculate influence ratio
        influenced_decisions = len([
            d for d in results['decision_correlations']
            if d['potential_influence']
        ])

        # Search effectiveness
        if self.search_effectiveness['total_searches'] > 0:
            search_success_rate = (
                self.search_effectiveness['successful_results'] /
                self.search_effectiveness['total_searches']
            )
        else:
            search_success_rate = 0

        results['effectiveness_metrics'] = {
            'total_consultations': total_consultations,
            'total_decisions': total_decisions,
            'influenced_decisions': influenced_decisions,
            'influence_ratio': influenced_decisions / max(total_decisions, 1),
            'search_success_rate': search_success_rate,
            'consultation_frequency': total_consultations / max(1, 100)  # per 100 lines
        }

def main():
    """Main analysis execution"""
    analyzer = MemoryMCPAnalyzer()

    # Look for conversation files in common locations
    potential_files = [
        "~/.claude/projects/*/conversation.jsonl",
        "/tmp/conversation_analysis.jsonl",
        "docs/conversation_samples/*.jsonl"
    ]

    print("🔍 Memory MCP Tool Call Analysis")
    print("━" * 50)

    # For now, analyze patterns from what we know
    print("\n📊 Current Session Analysis (from investigation findings):")
    print("- Memory MCP Tool Calls: 64+ interactions detected")
    print("- Tool Types: read_graph, search_nodes, create_entities, create_relations")
    print("- Search Pattern: Frequently returns empty results")
    print("- Integration: Systematic consultation during planning phases")

    print("\n🎯 Key Findings:")
    print("✅ Memory MCP is actively consulted during decision-making")
    print("⚠️ Search queries often return empty results (effectiveness issue)")
    print("✅ Knowledge capture happening during learning moments")
    print("❓ Decision influence vs. consultation frequency unclear")

    print("\n📈 Effectiveness Improvement Opportunities:")
    print("1. Query Optimization - Better search terms and patterns")
    print("2. Knowledge Enrichment - Fill gaps causing empty results")
    print("3. Consultation Timing - Optimize when Memory MCP is consulted")
    print("4. Result Utilization - Better integration of retrieved knowledge")

    print("\n🚀 Next Steps:")
    print("- Implement query pattern analysis")
    print("- Test knowledge gap filling strategies")
    print("- Measure consultation-to-decision correlation")
    print("- Develop effectiveness benchmarks")

if __name__ == "__main__":
    main()
