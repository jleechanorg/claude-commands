#!/usr/bin/env python3

from enhanced_learn import LearningPattern

"""
Pattern Query System for Cognitive Enhancement Framework
========================================================

This module provides sophisticated pattern querying capabilities for the
cognitive enhancement framework, allowing AI assistants to consult learned
patterns before generating responses.

Key Features:
- Multi-dimensional pattern search
- Context-aware relevance scoring
- Pattern recommendation engine
- Response guidance generation
"""

import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from enhanced_learn import EnhancedLearner, LearningPattern


@dataclass
class PatternMatch:
    """Represents a pattern match with relevance score."""

    pattern: LearningPattern
    relevance_score: float
    match_reasons: list[str]
    suggested_action: str


@dataclass
class QueryResult:
    """Complete result of a pattern query."""

    matches: list[PatternMatch]
    total_searched: int
    query_analysis: dict[str, Any]
    recommendations: list[str]


class PatternQueryEngine:
    """Advanced pattern querying system with context awareness."""

    def __init__(self, learner: EnhancedLearner | None = None):
        self.learner = learner or EnhancedLearner()

        # Query analysis patterns
        self.intent_patterns = {
            "seeking_correction": [
                r"how.*(?:should|correct)",
                r"what.*(?:right way|proper)",
                r"(?:fix|correct).*(?:this|that)",
                r"mistake.*(?:in|with)",
            ],
            "seeking_preference": [
                r"prefer.*(?:to|that)",
                r"like.*(?:better|more)",
                r"style.*(?:guide|preference)",
                r"format.*(?:should|prefer)",
            ],
            "seeking_process": [
                r"(?:how to|steps to)",
                r"process.*(?:for|of)",
                r"workflow.*(?:for|when)",
                r"procedure.*(?:to|for)",
            ],
            "seeking_technical": [
                r"(?:api|code|function|method)",
                r"technical.*(?:detail|spec)",
                r"implementation.*(?:of|for)",
                r"algorithm.*(?:for|to)",
            ],
        }

    def analyze_query_intent(self, query: str) -> dict[str, float]:
        """Analyze the intent of a query to improve pattern matching."""
        query_lower = query.lower()
        intent_scores = {}

        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, query_lower)
                score += len(matches)

            # Normalize score
            intent_scores[intent] = min(score / len(patterns), 1.0)

        return intent_scores

    def extract_query_keywords(self, query: str) -> set[str]:
        """Extract meaningful keywords from query."""
        # Remove common words
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "up",
            "about",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "between",
            "among",
            "throughout",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "can",
            "shall",
            "must",
            "ought",
        }

        # Extract words (alphanumeric + underscore)
        words = re.findall(r"\b\w+\b", query.lower())

        # Filter stop words and short words
        keywords = {word for word in words if len(word) > 2 and word not in stop_words}

        return keywords

    def calculate_pattern_relevance(
        self,
        pattern: LearningPattern,
        query: str,
        intent_scores: dict[str, float],
        keywords: set[str],
    ) -> tuple[float, list[str]]:
        """Calculate relevance score for a pattern against a query."""
        score = 0
        reasons = []

        # Content matching
        content_lower = pattern.content.lower()
        query_lower = query.lower()

        # Exact phrase matching (highest weight)
        if query_lower in content_lower:
            score += 3.0
            reasons.append("exact_phrase_match")

        # Keyword matching
        keyword_matches = 0
        for keyword in keywords:
            if keyword in content_lower:
                keyword_matches += 1

        if keyword_matches > 0:
            keyword_score = min(keyword_matches / len(keywords), 1.0) * 2.0
            score += keyword_score
            reasons.append(f"keyword_matches_{keyword_matches}")

        # Context matching
        context_lower = pattern.context.lower()
        if any(keyword in context_lower for keyword in keywords):
            score += 1.0
            reasons.append("context_match")

        # Tag matching
        tag_matches = 0
        for tag in pattern.tags:
            tag_lower = tag.lower()
            if tag_lower in query_lower or any(
                keyword in tag_lower for keyword in keywords
            ):
                tag_matches += 1

        if tag_matches > 0:
            score += tag_matches * 0.5
            reasons.append(f"tag_matches_{tag_matches}")

        # Intent alignment
        pattern_type_lower = pattern.pattern_type.lower()
        for intent, intent_score in intent_scores.items():
            if intent_score > 0.3:  # Significant intent
                if intent.replace("seeking_", "") in pattern_type_lower or any(
                    tag.lower() == intent.replace("seeking_", "")
                    for tag in pattern.tags
                ):
                    score += intent_score * 1.5
                    reasons.append(f"intent_alignment_{intent}")

        # Confidence weighting
        score *= pattern.confidence

        # Recency bonus (patterns learned recently are more relevant)
        try:
            pattern_date = datetime.fromisoformat(pattern.timestamp)
            days_old = (datetime.now() - pattern_date).days
            if days_old < 7:
                score *= 1.2
                reasons.append("recent_learning")
            elif days_old < 30:
                score *= 1.1
                reasons.append("moderately_recent")
        except:
            pass

        return score, reasons

    def query_patterns(
        self, query: str, limit: int = 10, min_relevance: float = 0.1
    ) -> QueryResult:
        """Query patterns with advanced relevance scoring."""

        # Analyze query
        intent_scores = self.analyze_query_intent(query)
        keywords = self.extract_query_keywords(query)

        # Score all patterns
        pattern_matches = []
        for pattern in self.learner.patterns:
            relevance_score, reasons = self.calculate_pattern_relevance(
                pattern, query, intent_scores, keywords
            )

            if relevance_score >= min_relevance:
                # Determine suggested action
                suggested_action = self._determine_suggested_action(
                    pattern, intent_scores
                )

                match = PatternMatch(
                    pattern=pattern,
                    relevance_score=relevance_score,
                    match_reasons=reasons,
                    suggested_action=suggested_action,
                )
                pattern_matches.append(match)

        # Sort by relevance
        pattern_matches.sort(key=lambda x: x.relevance_score, reverse=True)

        # Generate recommendations
        recommendations = self._generate_recommendations(pattern_matches[:limit], query)

        return QueryResult(
            matches=pattern_matches[:limit],
            total_searched=len(self.learner.patterns),
            query_analysis={
                "intent_scores": intent_scores,
                "keywords": list(keywords),
                "top_intent": max(intent_scores, key=intent_scores.get)
                if intent_scores
                else None,
            },
            recommendations=recommendations,
        )

    def _determine_suggested_action(
        self, pattern: LearningPattern, intent_scores: dict[str, float]
    ) -> str:
        """Determine the suggested action based on pattern and intent."""
        if pattern.pattern_type == "correction":
            return "avoid_previous_mistake"
        if pattern.pattern_type == "preference":
            return "follow_user_preference"
        if pattern.pattern_type == "workflow":
            return "follow_established_process"
        if pattern.pattern_type == "technical":
            return "apply_technical_knowledge"
        # Use intent to suggest action
        top_intent = (
            max(intent_scores, key=intent_scores.get) if intent_scores else None
        )
        if top_intent == "seeking_correction":
            return "provide_corrected_information"
        if top_intent == "seeking_preference":
            return "acknowledge_preference"
        if top_intent == "seeking_process":
            return "outline_process_steps"
        if top_intent == "seeking_technical":
            return "provide_technical_details"
        return "apply_learned_knowledge"

    def _generate_recommendations(
        self, matches: list[PatternMatch], query: str
    ) -> list[str]:
        """Generate actionable recommendations based on pattern matches."""
        recommendations = []

        if not matches:
            recommendations.append(
                "No relevant patterns found. Proceed with standard response."
            )
            return recommendations

        # Group by pattern type
        by_type = defaultdict(list)
        for match in matches:
            by_type[match.pattern.pattern_type].append(match)

        # Generate type-specific recommendations
        if "correction" in by_type:
            corrections = by_type["correction"]
            high_confidence_corrections = [
                c for c in corrections if c.pattern.confidence >= 0.8
            ]
            if high_confidence_corrections:
                recommendations.append(
                    f"CRITICAL: Apply {len(high_confidence_corrections)} high-confidence corrections from past user feedback"
                )

        if "preference" in by_type:
            preferences = by_type["preference"]
            recommendations.append(
                f"Consider {len(preferences)} user preferences when formatting response"
            )

        if "workflow" in by_type:
            workflows = by_type["workflow"]
            recommendations.append(
                f"Follow {len(workflows)} established workflow patterns"
            )

        if "technical" in by_type:
            technical = by_type["technical"]
            recommendations.append(
                f"Apply {len(technical)} technical insights from previous learning"
            )

        # Overall recommendation
        top_match = matches[0]
        if top_match.relevance_score > 2.0:
            recommendations.insert(
                0,
                f"HIGH RELEVANCE: {top_match.suggested_action} - {top_match.pattern.content[:100]}...",
            )

        return recommendations

    def get_pattern_summary(self, match: PatternMatch) -> str:
        """Get a concise summary of a pattern match for display."""
        pattern = match.pattern
        summary = f"[{pattern.pattern_type.upper()}] {pattern.content[:80]}"
        if len(pattern.content) > 80:
            summary += "..."

        summary += f" (Confidence: {pattern.confidence:.1f}, Relevance: {match.relevance_score:.1f})"
        return summary

    def format_query_results(self, result: QueryResult) -> str:
        """Format query results for display in responses."""
        if not result.matches:
            return "No relevant patterns found in memory."

        output = []
        output.append(
            f"Memory Query Results ({len(result.matches)} matches from {result.total_searched} patterns):"
        )

        for i, match in enumerate(result.matches[:5], 1):
            output.append(f"{i}. {self.get_pattern_summary(match)}")

        if result.recommendations:
            output.append("\nRecommendations:")
            for rec in result.recommendations:
                output.append(f"• {rec}")

        return "\n".join(output)


class MemoryConsciousResponseGenerator:
    """Response generator that consults memory patterns before responding."""

    def __init__(self, learner: EnhancedLearner | None = None):
        self.learner = learner or EnhancedLearner()
        self.query_engine = PatternQueryEngine(self.learner)

    def should_consult_memory(self, query: str) -> bool:
        """Determine if memory consultation is needed for this query."""
        # Always consult for complex queries
        if len(query.split()) > 10:
            return True

        # Consult for correction indicators
        correction_indicators = ["fix", "correct", "wrong", "mistake", "error"]
        if any(indicator in query.lower() for indicator in correction_indicators):
            return True

        # Consult for technical queries
        technical_indicators = ["how to", "api", "code", "implementation", "algorithm"]
        if any(indicator in query.lower() for indicator in technical_indicators):
            return True

        # Consult for preference queries
        preference_indicators = ["prefer", "like", "style", "format", "way"]
        if any(indicator in query.lower() for indicator in preference_indicators):
            return True

        return False

    def consult_memory(self, query: str) -> QueryResult | None:
        """Consult memory patterns for relevant information."""
        if not self.should_consult_memory(query):
            return None

        return self.query_engine.query_patterns(query)

    def generate_memory_guidance(
        self, query: str
    ) -> tuple[str | None, QueryResult | None]:
        """Generate memory guidance for a query."""
        result = self.consult_memory(query)

        if not result or not result.matches:
            return None, None

        guidance = self.query_engine.format_query_results(result)
        return guidance, result


def main():
    """Example usage of the pattern query system."""
    # Initialize system
    learner = EnhancedLearner()
    query_engine = PatternQueryEngine(learner)

    # Add some example patterns for testing


    example_patterns = [
        LearningPattern(
            pattern_type="correction",
            content="Use POST method for API data submission, not GET",
            context="API endpoint discussion",
            confidence=0.9,
            timestamp=datetime.now().isoformat(),
            source="user_correction",
            examples=["POST for data submission"],
            tags=["api", "http", "technical", "critical"],
        ),
        LearningPattern(
            pattern_type="preference",
            content="User prefers bullet points over numbered lists for summaries",
            context="Response formatting discussion",
            confidence=0.8,
            timestamp=datetime.now().isoformat(),
            source="user_feedback",
            examples=["bullet point summaries"],
            tags=["formatting", "preference", "ui"],
        ),
    ]

    # Add patterns to learner
    for pattern in example_patterns:
        learner.add_pattern(pattern)

    # Test queries
    test_queries = [
        "How should I implement API endpoints?",
        "What's the best way to format a summary?",
        "Can you help me with data submission?",
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")
        result = query_engine.query_patterns(query)
        formatted = query_engine.format_query_results(result)
        print(formatted)


if __name__ == "__main__":
    main()
