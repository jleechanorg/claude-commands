#!/usr/bin/env python3
"""
Pattern Extractor for Enhanced /learn Command

Analyzes user interactions to extract implicit patterns and preferences.
Updates PATTERNS.md and integrates with memory system.
"""

import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class PatternCategory(Enum):
    STYLE = "Code Style Patterns"
    REVIEW = "Review Focus Patterns"
    WORKFLOW = "Workflow Patterns"
    COMMUNICATION = "Communication Patterns"
    ERROR_RECOVERY = "Error Recovery Patterns"
    TOOL_USAGE = "Tool & Command Usage"
    ANTI_PATTERN = "Anti-Patterns"


class Confidence(Enum):
    HIGH = ("🟢", 0.9, "Seen 5+ times, consistently applied")
    MEDIUM = ("🟡", 0.7, "Seen 3-4 times, mostly consistent")
    LOW = ("🔴", 0.5, "Seen 1-2 times, needs validation")


@dataclass
class Pattern:
    """Represents a learned pattern from user interaction"""

    name: str
    category: PatternCategory
    description: str
    evidence: list[str]
    triggers: list[str]
    actions: list[str]
    context: str | None
    confidence: float
    occurrences: int
    last_seen: datetime
    auto_apply: bool = False


class PatternExtractor:
    """Extracts patterns from user interactions"""

    # Correction indicators
    CORRECTION_PHRASES = [
        r"no,?\s*actually",
        r"please\s+change",
        r"should\s+be",
        r"don't\s+use",
        r"always\s+use",
        r"prefer\s+",
        r"instead\s+of",
        r"not\s+like\s+that",
        r"wrong",
        r"fix\s+this",
        r"rename",
        r"refactor",
    ]

    # Context indicators
    RUSH_INDICATORS = [
        "ship it",
        "just make it work",
        "quick fix",
        "urgent",
        "asap",
        "rush",
        "fast",
        "now",
        "today",
    ]

    QUALITY_INDICATORS = [
        "take your time",
        "careful",
        "critical",
        "production",
        "thorough",
        "comprehensive",
        "polish",
        "perfect",
    ]

    def __init__(self):
        self.patterns: dict[str, Pattern] = {}

    def extract_patterns(self, interaction_text: str) -> list[Pattern]:
        """Extract patterns from a user interaction"""
        patterns = []

        # Check for corrections
        corrections = self._find_corrections(interaction_text)
        for correction in corrections:
            pattern = self._analyze_correction(correction)
            if pattern:
                patterns.append(pattern)

        # Check for context shifts
        context = self._detect_context(interaction_text)
        if context:
            patterns.append(context)

        # Check for preferences
        preferences = self._extract_preferences(interaction_text)
        patterns.extend(preferences)

        return patterns

    def _find_corrections(self, text: str) -> list[str]:
        """Find correction patterns in text"""
        corrections = []
        for phrase in self.CORRECTION_PHRASES:
            matches = re.finditer(phrase, text, re.IGNORECASE)
            for match in matches:
                # Extract surrounding context
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 100)
                corrections.append(text[start:end])
        return corrections

    def _analyze_correction(self, correction: str) -> Pattern | None:
        """Analyze a correction to extract pattern"""
        # Style corrections
        if any(term in correction.lower() for term in ["name", "rename", "variable"]):
            return self._create_style_pattern(correction)

        # Code structure corrections
        if any(
            term in correction.lower() for term in ["structure", "organize", "refactor"]
        ):
            return self._create_structure_pattern(correction)

        # Error handling corrections
        if any(term in correction.lower() for term in ["except", "error", "handle"]):
            return self._create_error_pattern(correction)

        return None

    def _detect_context(self, text: str) -> Pattern | None:
        """Detect context shifts in interaction"""
        text_lower = text.lower()

        # Rush mode detection
        if any(indicator in text_lower for indicator in self.RUSH_INDICATORS):
            return Pattern(
                name="Rush Mode Context",
                category=PatternCategory.WORKFLOW,
                description="User is in rush mode - prioritize speed over perfection",
                evidence=[text[:200]],
                triggers=self.RUSH_INDICATORS,
                actions=[
                    "Minimize refactoring",
                    "Focus on functionality",
                    "Document TODOs for later",
                    "Skip non-critical improvements",
                ],
                context="Time-sensitive situations",
                confidence=0.8,
                occurrences=1,
                last_seen=datetime.now(),
                auto_apply=True,
            )

        # Quality mode detection
        if any(indicator in text_lower for indicator in self.QUALITY_INDICATORS):
            return Pattern(
                name="Quality Mode Context",
                category=PatternCategory.WORKFLOW,
                description="User wants high quality - prioritize correctness and polish",
                evidence=[text[:200]],
                triggers=self.QUALITY_INDICATORS,
                actions=[
                    "Comprehensive testing",
                    "Full documentation",
                    "Performance optimization",
                    "Code review mindset",
                ],
                context="Critical or production code",
                confidence=0.8,
                occurrences=1,
                last_seen=datetime.now(),
                auto_apply=True,
            )

        return None

    def _extract_preferences(self, text: str) -> list[Pattern]:
        """Extract implicit preferences from accepted/modified code"""
        preferences = []

        # Python-specific preferences
        if "f-string" in text or "f'" in text or 'f"' in text:
            preferences.append(
                Pattern(
                    name="F-String Preference",
                    category=PatternCategory.STYLE,
                    description="Prefer f-strings over .format() or % formatting",
                    evidence=[text[:100]],
                    triggers=["string formatting", "interpolation"],
                    actions=["Use f-strings for string formatting"],
                    context="Python code",
                    confidence=0.7,
                    occurrences=1,
                    last_seen=datetime.now(),
                )
            )

        # Import preferences
        if "import" in text and "top" in text:
            preferences.append(
                Pattern(
                    name="Import Organization",
                    category=PatternCategory.STYLE,
                    description="All imports at top of file, properly organized",
                    evidence=[text[:100]],
                    triggers=["import statements"],
                    actions=["Place all imports at module top", "Sort imports"],
                    context="Python modules",
                    confidence=0.9,
                    occurrences=1,
                    last_seen=datetime.now(),
                )
            )

        return preferences

    def _create_style_pattern(self, correction: str) -> Pattern:
        """Create a style-related pattern"""
        return Pattern(
            name="Naming Convention",
            category=PatternCategory.STYLE,
            description="Descriptive names preferred over abbreviations",
            evidence=[correction],
            triggers=["variable naming", "function naming"],
            actions=["Use full descriptive names", "Avoid abbreviations"],
            context="All code",
            confidence=0.6,
            occurrences=1,
            last_seen=datetime.now(),
        )

    def _create_structure_pattern(self, correction: str) -> Pattern:
        """Create a code structure pattern"""
        return Pattern(
            name="Code Organization",
            category=PatternCategory.STYLE,
            description="Specific structure preferences",
            evidence=[correction],
            triggers=["code structure", "file organization"],
            actions=["Follow observed structure patterns"],
            context="Code organization",
            confidence=0.5,
            occurrences=1,
            last_seen=datetime.now(),
        )

    def _create_error_pattern(self, correction: str) -> Pattern:
        """Create an error handling pattern"""
        return Pattern(
            name="Error Handling Style",
            category=PatternCategory.STYLE,
            description="Specific exception handling required",
            evidence=[correction],
            triggers=["exception handling", "error catching"],
            actions=["Use specific exceptions", "Avoid bare except"],
            context="Error handling",
            confidence=0.8,
            occurrences=1,
            last_seen=datetime.now(),
        )

    def update_pattern_confidence(self, pattern_name: str, success: bool):
        """Update pattern confidence based on application success"""
        if pattern_name in self.patterns:
            pattern = self.patterns[pattern_name]
            if success:
                pattern.confidence = min(0.99, pattern.confidence + 0.1)
                pattern.occurrences += 1
            else:
                pattern.confidence = max(0.1, pattern.confidence - 0.2)
            pattern.last_seen = datetime.now()

    def merge_similar_patterns(self):
        """Merge patterns that are similar"""
        # Implementation for pattern deduplication

    def to_memory_entities(self, patterns: list[Pattern]) -> dict:
        """Convert patterns to memory system entities"""
        entities = []
        for pattern in patterns:
            entities.append(
                {
                    "name": pattern.name,
                    "entityType": "Pattern",
                    "observations": [
                        f"Category: {pattern.category.value}",
                        f"Description: {pattern.description}",
                        f"Confidence: {pattern.confidence}",
                        f"Auto-apply: {pattern.auto_apply}",
                        *[f"Evidence: {e}" for e in pattern.evidence],
                        *[f"Trigger: {t}" for t in pattern.triggers],
                        *[f"Action: {a}" for a in pattern.actions],
                    ],
                }
            )
        return {"entities": entities}


def main():
    """Example usage"""
    extractor = PatternExtractor()

    # Example interaction
    interaction = """
    No, actually please change 'usr' to 'user'. I prefer descriptive 
    variable names over abbreviations. Also, this needs to ship today
    so just make it work for now.
    """

    patterns = extractor.extract_patterns(interaction)

    print("Extracted Patterns:")
    for pattern in patterns:
        print(f"\n{pattern.name} ({pattern.category.value})")
        print(f"  Confidence: {pattern.confidence}")
        print(f"  Description: {pattern.description}")
        print(f"  Actions: {', '.join(pattern.actions)}")


if __name__ == "__main__":
    main()
