#!/usr/bin/env python3
"""
Context-Aware Memory Query System for Week 2 Conscious Memory Integration
Analyzes conversation context and determines when memory consultation is needed
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class ContextAnalyzer:
    """Analyzes conversation context to determine memory consultation needs"""
    
    def __init__(self):
        self.memory_trigger_patterns = {
            'code_generation': [
                r'write.*?(function|class|script|code)',
                r'create.*?(method|component|module)',
                r'implement.*?(feature|functionality)',
                r'add.*?(function|class|method)',
                r'build.*?(component|system|tool)'
            ],
            'code_review': [
                r'review.*?(code|pr|pull request)',
                r'check.*?(implementation|logic)',
                r'analyze.*?(code|function)',
                r'feedback.*?(code|implementation)',
                r'comments.*?(code|review)'
            ],
            'debugging': [
                r'fix.*?(bug|error|issue)',
                r'debug.*?(problem|issue)',
                r'solve.*?(error|problem)',
                r'troubleshoot.*?',
                r'why.*?(not working|failing|broken)'
            ],
            'architecture_decisions': [
                r'design.*?(system|architecture)',
                r'choose.*?(approach|solution|pattern)',
                r'decide.*?(how to|architecture)',
                r'what.*?(pattern|approach|design)',
                r'best.*?(practice|way|approach)'
            ],
            'workflow_guidance': [
                r'how.*?(should|do|to)',
                r'process.*?(for|to)',
                r'workflow.*?(for|to)',
                r'steps.*?(to|for)',
                r'procedure.*?(for|to)'
            ],
            'quality_standards': [
                r'test.*?(coverage|quality|standards)',
                r'quality.*?(requirements|standards)',
                r'standards.*?(for|to)',
                r'documentation.*?(requirements|standards)',
                r'best.*?(practices|standards)'
            ]
        }
        
        self.urgency_indicators = {
            'urgent': ['urgent', 'asap', 'immediately', 'quick', 'fast', 'rush'],
            'normal': ['when you can', 'at some point', 'eventually'],
            'careful': ['careful', 'thorough', 'comprehensive', 'detailed', 'precise']
        }
        
        self.task_complexity_indicators = {
            'simple': ['simple', 'quick', 'small', 'minor', 'basic'],
            'medium': ['moderate', 'standard', 'typical', 'normal'],
            'complex': ['complex', 'comprehensive', 'detailed', 'major', 'large', 'full']
        }
    
    def analyze_context(self, user_message: str, conversation_history: Optional[List[str]] = None) -> Dict:
        """Analyze message context and determine memory consultation strategy"""
        message_lower = user_message.lower()
        
        context_analysis = {
            'trigger_categories': self._detect_trigger_categories(message_lower),
            'urgency_level': self._detect_urgency(message_lower),
            'complexity_level': self._detect_complexity(message_lower),
            'memory_consultation_needed': False,
            'consultation_priority': 'low',
            'relevant_contexts': [],
            'query_keywords': []
        }
        
        # Determine if memory consultation is needed
        if context_analysis['trigger_categories']:
            context_analysis['memory_consultation_needed'] = True
            context_analysis['consultation_priority'] = self._calculate_priority(context_analysis)
            context_analysis['relevant_contexts'] = context_analysis['trigger_categories']
            context_analysis['query_keywords'] = self._extract_query_keywords(message_lower, context_analysis['trigger_categories'])
        
        return context_analysis
    
    def _detect_trigger_categories(self, message: str) -> List[str]:
        """Detect which categories of memory patterns might be relevant"""
        triggered_categories = []
        
        for category, patterns in self.memory_trigger_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message, re.IGNORECASE):
                    triggered_categories.append(category)
                    break
        
        return list(set(triggered_categories))  # Remove duplicates
    
    def _detect_urgency(self, message: str) -> str:
        """Detect urgency level from message"""
        for urgency, indicators in self.urgency_indicators.items():
            if any(indicator in message for indicator in indicators):
                return urgency
        return 'normal'
    
    def _detect_complexity(self, message: str) -> str:
        """Detect task complexity from message"""
        for complexity, indicators in self.task_complexity_indicators.items():
            if any(indicator in message for indicator in indicators):
                return complexity
        return 'medium'
    
    def _calculate_priority(self, context: Dict) -> str:
        """Calculate memory consultation priority based on context"""
        priority_score = 0
        
        # Base score for triggered categories
        priority_score += len(context['trigger_categories']) * 10
        
        # Urgency modifiers
        if context['urgency_level'] == 'urgent':
            priority_score += 15
        elif context['urgency_level'] == 'careful':
            priority_score += 20
        
        # Complexity modifiers
        if context['complexity_level'] == 'complex':
            priority_score += 15
        elif context['complexity_level'] == 'simple':
            priority_score += 5
        
        # High-value categories get priority boost
        high_value_categories = ['code_generation', 'architecture_decisions', 'quality_standards']
        if any(cat in context['trigger_categories'] for cat in high_value_categories):
            priority_score += 20
        
        if priority_score >= 40:
            return 'high'
        elif priority_score >= 20:
            return 'medium'
        else:
            return 'low'
    
    def _extract_query_keywords(self, message: str, categories: List[str]) -> List[str]:
        """Extract keywords for memory queries based on detected categories"""
        keywords = []
        
        # Add category-specific keywords
        category_keywords = {
            'code_generation': ['coding', 'function', 'class', 'implementation'],
            'code_review': ['review', 'quality', 'standards'],
            'debugging': ['debugging', 'testing', 'error'],
            'architecture_decisions': ['architecture', 'design', 'pattern'],
            'workflow_guidance': ['workflow', 'process', 'procedure'],
            'quality_standards': ['quality', 'testing', 'standards']
        }
        
        for category in categories:
            keywords.extend(category_keywords.get(category, []))
        
        # Extract technical terms from message
        technical_terms = re.findall(r'\b(?:function|class|method|variable|import|test|code|script|file|module|component|system|api|database|server|client)\b', message, re.IGNORECASE)
        keywords.extend(technical_terms)
        
        return list(set(keywords))  # Remove duplicates

class MemoryQueryEngine:
    """Executes memory queries based on context analysis"""
    
    def __init__(self):
        self.local_memory_file = Path.home() / ".cache" / "claude-learning" / "learning_memory.json"
        self.context_analyzer = ContextAnalyzer()
    
    def query_relevant_patterns(self, user_message: str, conversation_history: Optional[List[str]] = None) -> Dict:
        """Query memory for patterns relevant to current context"""
        
        # Analyze context
        context = self.context_analyzer.analyze_context(user_message, conversation_history)
        
        result = {
            'context_analysis': context,
            'memory_insights': [],
            'patterns_found': [],
            'confidence_weighted_suggestions': [],
            'consultation_needed': context['memory_consultation_needed']
        }
        
        if not context['memory_consultation_needed']:
            return result
        
        # Query local memory first
        local_patterns = self._query_local_memory(context['query_keywords'])
        result['patterns_found'].extend(local_patterns)
        
        # Try Memory MCP if available
        try:
            mcp_patterns = self._query_memory_mcp(context['query_keywords'])
            result['patterns_found'].extend(mcp_patterns)
        except Exception:
            # Memory MCP not available, continue with local only
            pass
        
        # Generate insights and suggestions
        if result['patterns_found']:
            result['memory_insights'] = self._generate_insights(result['patterns_found'], context)
            result['confidence_weighted_suggestions'] = self._rank_suggestions(result['patterns_found'])
        
        return result
    
    def _query_local_memory(self, keywords: List[str]) -> List[Dict]:
        """Query local memory file for relevant patterns"""
        if not self.local_memory_file.exists():
            return []
        
        try:
            with open(self.local_memory_file, 'r') as f:
                memory = json.load(f)
        except:
            return []
        
        entities = memory.get("entities", {})
        corrections = [e for e in entities.values() if e.get("type") == "user_correction"]
        
        relevant_patterns = []
        
        for correction in corrections:
            # Check if any keywords match the correction context or content
            correction_contexts = [ctx.lower() for ctx in correction.get("context", [])]
            correction_text = str(correction.get("pattern", "")).lower()
            
            relevance_score = 0
            
            # Score based on keyword matches
            for keyword in keywords:
                if any(keyword.lower() in ctx for ctx in correction_contexts):
                    relevance_score += 2
                if keyword.lower() in correction_text:
                    relevance_score += 1
            
            if relevance_score > 0:
                pattern_entry = correction.copy()
                pattern_entry['relevance_score'] = relevance_score
                pattern_entry['source'] = 'local_memory'
                relevant_patterns.append(pattern_entry)
        
        # Sort by relevance and confidence
        relevant_patterns.sort(key=lambda x: (x['relevance_score'], x.get('confidence', 0)), reverse=True)
        
        return relevant_patterns[:5]  # Return top 5 most relevant
    
    def _query_memory_mcp(self, keywords: List[str]) -> List[Dict]:
        """Query Memory MCP for relevant patterns"""
        # This would integrate with actual Memory MCP
        # For now, return empty list as placeholder
        return []
    
    def _generate_insights(self, patterns: List[Dict], context: Dict) -> List[str]:
        """Generate insights from found patterns"""
        insights = []
        
        if not patterns:
            return ["💭 No relevant patterns found in memory."]
        
        insights.append(f"💭 Found {len(patterns)} relevant pattern(s) from previous learning:")
        
        for i, pattern in enumerate(patterns[:3], 1):  # Show top 3
            pattern_text = pattern.get("pattern", "Unknown pattern")
            if isinstance(pattern_text, list):
                pattern_text = " → ".join(pattern_text)
            
            confidence = pattern.get("confidence", 0)
            correction_type = pattern.get("correction_type", "unknown")
            
            insights.append(f"  {i}. [{correction_type}] {pattern_text} (confidence: {confidence:.1f})")
        
        if len(patterns) > 3:
            insights.append(f"  ... and {len(patterns) - 3} more pattern(s)")
        
        return insights
    
    def _rank_suggestions(self, patterns: List[Dict]) -> List[Dict]:
        """Rank suggestions by confidence and relevance"""
        suggestions = []
        
        for pattern in patterns:
            confidence = pattern.get("confidence", 0)
            relevance = pattern.get("relevance_score", 0)
            combined_score = (confidence * 0.7) + (relevance * 0.3)
            
            suggestion = {
                'pattern': pattern.get("pattern", ""),
                'type': pattern.get("correction_type", "unknown"),
                'confidence': confidence,
                'relevance': relevance,
                'combined_score': combined_score,
                'recommendation': self._generate_recommendation(pattern)
            }
            suggestions.append(suggestion)
        
        suggestions.sort(key=lambda x: x['combined_score'], reverse=True)
        return suggestions[:5]  # Top 5 suggestions
    
    def _generate_recommendation(self, pattern: Dict) -> str:
        """Generate actionable recommendation from pattern"""
        correction_type = pattern.get("correction_type", "unknown")
        pattern_text = pattern.get("pattern", "")
        
        if isinstance(pattern_text, list):
            pattern_text = " → ".join(pattern_text)
        
        recommendation_templates = {
            'dont_do_instead': f"Consider: {pattern_text}",
            'use_instead': f"Recommend: {pattern_text}",
            'preference': f"User prefers: {pattern_text}",
            'context_behavior': f"In this context: {pattern_text}",
            'always_rule': f"Remember to: {pattern_text}",
            'never_rule': f"Avoid: {pattern_text}"
        }
        
        return recommendation_templates.get(correction_type, f"Apply: {pattern_text}")

def test_context_aware_memory():
    """Test the context-aware memory system"""
    
    query_engine = MemoryQueryEngine()
    
    test_messages = [
        "Write a function to validate user input",
        "Review this code for potential issues",
        "Fix the bug in the authentication system",
        "What's the best approach for handling database migrations?",
        "How should I structure this test file?",
        "Add comprehensive test coverage for the API endpoints",
        "Quick fix for the broken navigation"
    ]
    
    print("🧠 Testing Context-Aware Memory System")
    print("=" * 60)
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n{i}. User Message: '{message}'")
        print("-" * 40)
        
        result = query_engine.query_relevant_patterns(message)
        
        context = result['context_analysis']
        print(f"Context Analysis:")
        print(f"  - Categories: {', '.join(context['trigger_categories']) if context['trigger_categories'] else 'None'}")
        print(f"  - Urgency: {context['urgency_level']}")
        print(f"  - Complexity: {context['complexity_level']}")
        print(f"  - Consultation needed: {context['memory_consultation_needed']}")
        print(f"  - Priority: {context['consultation_priority']}")
        
        if result['memory_insights']:
            print(f"\nMemory Insights:")
            for insight in result['memory_insights']:
                print(f"  {insight}")
        
        if result['confidence_weighted_suggestions']:
            print(f"\nTop Suggestions:")
            for suggestion in result['confidence_weighted_suggestions'][:2]:
                print(f"  - {suggestion['recommendation']} (score: {suggestion['combined_score']:.2f})")

if __name__ == "__main__":
    test_context_aware_memory()