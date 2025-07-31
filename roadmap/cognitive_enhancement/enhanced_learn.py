#!/usr/bin/env python3

from datetime import datetime, timedelta

"""
Enhanced Learning System for Cognitive Enhancement Framework
============================================================

This module provides advanced learning capabilities that automatically capture,
analyze, and integrate knowledge from conversations and corrections.

Key Features:
- Automatic correction detection from user messages
- Pattern extraction and categorization
- Learning integration with existing knowledge base
- Memory-enhanced response generation
"""

import json
import os
import re
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class LearningPattern:
    """Represents a learned pattern with metadata."""

    pattern_type: str  # "correction", "preference", "workflow", "technical"
    content: str
    context: str
    confidence: float
    timestamp: str
    source: str  # "user_correction", "self_discovery", "observation"
    examples: list[str]
    tags: list[str]


@dataclass
class CorrectionEvent:
    """Represents a detected correction from user."""

    original_claim: str
    corrected_info: str
    correction_type: str
    severity: str  # "critical", "important", "minor"
    domain: str  # "technical", "process", "preference"


class EnhancedLearner:
    """Advanced learning system with correction detection and pattern analysis."""

    def __init__(
        self,
        knowledge_base_path: str = "roadmap/cognitive_enhancement/knowledge_base.json",
    ):
        self.knowledge_base_path = knowledge_base_path
        self.patterns: list[LearningPattern] = []
        self.load_knowledge_base()

        # Correction detection patterns
        self.correction_indicators = [
            r"actually[,\s]",
            r"no[,\s].*(?:that's|this is|it's)",
            r"(?:incorrect|wrong|not quite)",
            r"let me (?:correct|clarify)",
            r"(?:should be|is actually|in fact)",
            r"you (?:missed|forgot|didn't)",
            r"but really",
            r"the right way is",
            r"(?:fix|change) that to",
        ]

    def load_knowledge_base(self) -> None:
        """Load existing knowledge base from disk."""
        if os.path.exists(self.knowledge_base_path):
            try:
                with open(self.knowledge_base_path) as f:
                    data = json.load(f)
                    self.patterns = [
                        LearningPattern(**pattern)
                        for pattern in data.get("patterns", [])
                    ]
            except Exception as e:
                print(f"Warning: Could not load knowledge base: {e}")
                self.patterns = []
        else:
            self.patterns = []

    def save_knowledge_base(self) -> None:
        """Save knowledge base to disk."""
        os.makedirs(os.path.dirname(self.knowledge_base_path), exist_ok=True)
        data = {
            "patterns": [asdict(pattern) for pattern in self.patterns],
            "last_updated": datetime.now().isoformat(),
        }
        with open(self.knowledge_base_path, "w") as f:
            json.dump(data, f, indent=2)

    def detect_corrections(
        self, user_message: str, previous_response: str = ""
    ) -> list[CorrectionEvent]:
        """Detect corrections in user messages."""
        corrections = []

        # Look for correction indicators
        for pattern in self.correction_indicators:
            matches = re.finditer(pattern, user_message.lower())
            for match in matches:
                # Extract context around correction
                start = max(0, match.start() - 50)
                end = min(len(user_message), match.end() + 100)
                context = user_message[start:end]

                correction = CorrectionEvent(
                    original_claim="[Previous response context]",
                    corrected_info=context,
                    correction_type="user_feedback",
                    severity=self._assess_correction_severity(context),
                    domain=self._classify_domain(context),
                )
                corrections.append(correction)

        return corrections

    def _assess_correction_severity(self, context: str) -> str:
        """Assess the severity of a correction."""
        critical_words = ["wrong", "incorrect", "never", "always", "critical", "error"]
        important_words = ["should", "better", "prefer", "recommend"]

        context_lower = context.lower()

        if any(word in context_lower for word in critical_words):
            return "critical"
        if any(word in context_lower for word in important_words):
            return "important"
        return "minor"

    def _classify_domain(self, context: str) -> str:
        """Classify the domain of a correction."""
        technical_indicators = [
            "code",
            "function",
            "method",
            "api",
            "database",
            "algorithm",
        ]
        process_indicators = ["workflow", "process", "step", "procedure", "protocol"]
        preference_indicators = ["prefer", "like", "want", "style", "format"]

        context_lower = context.lower()

        if any(word in context_lower for word in technical_indicators):
            return "technical"
        if any(word in context_lower for word in process_indicators):
            return "process"
        if any(word in context_lower for word in preference_indicators):
            return "preference"
        return "general"

    def learn_from_correction(
        self, correction: CorrectionEvent, context: str = ""
    ) -> LearningPattern:
        """Create a learning pattern from a correction."""
        pattern = LearningPattern(
            pattern_type="correction",
            content=f"Correction: {correction.corrected_info}",
            context=context,
            confidence=0.9 if correction.severity == "critical" else 0.7,
            timestamp=datetime.now().isoformat(),
            source="user_correction",
            examples=[correction.corrected_info],
            tags=[correction.domain, correction.severity, "user_feedback"],
        )

        self.add_pattern(pattern)
        return pattern

    def learn_from_observation(
        self, observation: str, context: str, pattern_type: str = "observation"
    ) -> LearningPattern:
        """Learn from self-observed patterns."""
        pattern = LearningPattern(
            pattern_type=pattern_type,
            content=observation,
            context=context,
            confidence=0.6,
            timestamp=datetime.now().isoformat(),
            source="self_discovery",
            examples=[observation],
            tags=["self_observed", pattern_type],
        )

        self.add_pattern(pattern)
        return pattern

    def add_pattern(self, pattern: LearningPattern) -> None:
        """Add a pattern to the knowledge base."""
        # Check for duplicates
        for existing in self.patterns:
            if (
                existing.content.lower() == pattern.content.lower()
                and existing.pattern_type == pattern.pattern_type
            ):
                # Update existing pattern instead of adding duplicate
                existing.confidence = max(existing.confidence, pattern.confidence)
                existing.examples.extend(pattern.examples)
                existing.tags = list(set(existing.tags + pattern.tags))
                self.save_knowledge_base()
                return

        self.patterns.append(pattern)
        self.save_knowledge_base()

    def query_relevant_patterns(
        self, query: str, limit: int = 5
    ) -> list[LearningPattern]:
        """Query patterns relevant to a specific topic or context."""
        query_lower = query.lower()
        scored_patterns = []

        for pattern in self.patterns:
            score = 0

            # Content relevance
            if query_lower in pattern.content.lower():
                score += 2

            # Context relevance
            if query_lower in pattern.context.lower():
                score += 1

            # Tag relevance
            for tag in pattern.tags:
                if tag.lower() in query_lower or query_lower in tag.lower():
                    score += 1

            # Pattern type relevance
            if pattern.pattern_type.lower() in query_lower:
                score += 1

            # Weight by confidence
            score *= pattern.confidence

            if score > 0:
                scored_patterns.append((score, pattern))

        # Sort by score and return top results
        scored_patterns.sort(key=lambda x: x[0], reverse=True)
        return [pattern for _, pattern in scored_patterns[:limit]]

    def get_patterns_by_type(self, pattern_type: str) -> list[LearningPattern]:
        """Get all patterns of a specific type."""
        return [p for p in self.patterns if p.pattern_type == pattern_type]

    def get_recent_patterns(self, days: int = 7) -> list[LearningPattern]:
        """Get patterns learned in the last N days."""


        cutoff = datetime.now() - timedelta(days=days)

        recent = []
        for pattern in self.patterns:
            try:
                pattern_time = datetime.fromisoformat(pattern.timestamp)
                if pattern_time > cutoff:
                    recent.append(pattern)
            except ValueError:
                continue

        return sorted(recent, key=lambda p: p.timestamp, reverse=True)

    def analyze_learning_trends(self) -> dict[str, Any]:
        """Analyze learning patterns and trends."""
        if not self.patterns:
            return {"total_patterns": 0, "message": "No patterns learned yet"}

        # Group by type
        type_counts = {}
        for pattern in self.patterns:
            type_counts[pattern.pattern_type] = (
                type_counts.get(pattern.pattern_type, 0) + 1
            )

        # Group by domain
        domain_counts = {}
        for pattern in self.patterns:
            for tag in pattern.tags:
                domain_counts[tag] = domain_counts.get(tag, 0) + 1

        # Confidence distribution
        high_confidence = len([p for p in self.patterns if p.confidence >= 0.8])
        medium_confidence = len([p for p in self.patterns if 0.5 <= p.confidence < 0.8])
        low_confidence = len([p for p in self.patterns if p.confidence < 0.5])

        return {
            "total_patterns": len(self.patterns),
            "type_distribution": type_counts,
            "domain_distribution": domain_counts,
            "confidence_distribution": {
                "high": high_confidence,
                "medium": medium_confidence,
                "low": low_confidence,
            },
            "recent_learning_rate": len(self.get_recent_patterns(7)),
        }


def main():
    """Example usage of the enhanced learning system."""
    learner = EnhancedLearner()

    # Example: Detect corrections
    user_message = "Actually, that's not quite right. The API should use POST not GET for that endpoint."
    corrections = learner.detect_corrections(user_message)

    for correction in corrections:
        print(f"Detected correction: {correction}")
        pattern = learner.learn_from_correction(correction, "API endpoint discussion")
        print(f"Created learning pattern: {pattern.content}")

    # Example: Query patterns
    relevant = learner.query_relevant_patterns("API endpoint")
    print(f"\nRelevant patterns for 'API endpoint': {len(relevant)} found")

    # Example: Learning trends
    trends = learner.analyze_learning_trends()
    print(f"\nLearning trends: {trends}")


if __name__ == "__main__":
    main()
