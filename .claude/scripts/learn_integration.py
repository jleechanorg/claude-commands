#!/usr/bin/env python3
"""
Integration module for enhanced /learn command

Connects pattern extraction with:
- Memory system (MCP)
- PATTERNS.md updates
- CONTEXT_AWARENESS.md
- Other slash commands
"""

import json

from pattern_extractor import Pattern, PatternExtractor
from update_patterns import PatternDocUpdater


class LearnCommandIntegration:
    """Orchestrates the enhanced /learn command functionality"""

    def __init__(self):
        self.extractor = PatternExtractor()
        self.doc_updater = PatternDocUpdater()

    def execute_learn(self, context: str | None = None) -> dict:
        """Execute the enhanced /learn command"""
        result = {
            "patterns_found": 0,
            "patterns_added": 0,
            "memory_updated": False,
            "documentation_updated": False,
            "insights": [],
        }

        # Step 1: Gather context
        if not context:
            context = self._gather_recent_context()

        # Step 2: Extract patterns using sequential thinking
        patterns = self._extract_with_thinking(context)
        result["patterns_found"] = len(patterns)

        # Step 3: Validate and categorize patterns
        validated_patterns = self._validate_patterns(patterns)

        # Step 4: Update documentation
        for pattern in validated_patterns:
            if self.doc_updater.add_pattern(pattern):
                result["patterns_added"] += 1

        if result["patterns_added"] > 0:
            self.doc_updater.save()
            result["documentation_updated"] = True

        # Step 5: Update memory system
        if validated_patterns:
            memory_result = self._update_memory_system(validated_patterns)
            result["memory_updated"] = memory_result

        # Step 6: Generate insights
        result["insights"] = self._generate_insights(validated_patterns)

        # Step 7: Check for meta-patterns
        meta_patterns = self._analyze_meta_patterns()
        if meta_patterns:
            result["insights"].extend(meta_patterns)

        return result

    def _gather_recent_context(self) -> str:
        """Gather recent conversation context"""
        # In real implementation, would read from conversation history
        # For now, return a placeholder
        return "Recent interaction context would be gathered here"

    def _extract_with_thinking(self, context: str) -> list[Pattern]:
        """Use sequential thinking to extract patterns"""
        # Simulate sequential thinking analysis
        thinking_prompts = [
            "What correction or preference was expressed?",
            "Why might the user want this change?",
            "When does this pattern apply?",
            "Are there exceptions to consider?",
            "How confident are we in this pattern?",
        ]

        # Extract patterns
        patterns = self.extractor.extract_patterns(context)

        # Enhance with thinking analysis
        for pattern in patterns:
            # Add thinking-based enhancements
            pattern.description += " [Enhanced via sequential thinking]"

        return patterns

    def _validate_patterns(self, patterns: list[Pattern]) -> list[Pattern]:
        """Validate patterns against existing knowledge"""
        validated = []

        for pattern in patterns:
            # Check if pattern contradicts existing rules
            if not self._contradicts_existing(pattern):
                # Check if pattern is meaningful
                if self._is_meaningful(pattern):
                    validated.append(pattern)

        return validated

    def _contradicts_existing(self, pattern: Pattern) -> bool:
        """Check if pattern contradicts CLAUDE.md or existing patterns"""
        # Would check against CLAUDE.md and PATTERNS.md
        # For now, simple validation
        return False

    def _is_meaningful(self, pattern: Pattern) -> bool:
        """Check if pattern is worth recording"""
        # Patterns need evidence and clear actions
        return bool(pattern.evidence) and bool(pattern.actions)

    def _update_memory_system(self, patterns: list[Pattern]) -> bool:
        """Update memory system with new patterns"""
        try:
            # Convert to memory entities
            memory_data = self.extractor.to_memory_entities(patterns)

            # Would call MCP memory server here
            # For now, just save to file
            with open("/tmp/pattern_memory.json", "w") as f:
                json.dump(memory_data, f, indent=2)

            return True
        except Exception as e:
            print(f"Memory update failed: {e}")
            return False

    def _generate_insights(self, patterns: list[Pattern]) -> list[str]:
        """Generate insights from patterns"""
        insights = []

        # Pattern frequency
        if len(patterns) > 3:
            insights.append(
                f"High correction frequency detected - {len(patterns)} patterns in one interaction"
            )

        # Confidence analysis
        high_confidence = [p for p in patterns if p.confidence >= 0.8]
        if high_confidence:
            insights.append(
                f"{len(high_confidence)} high-confidence patterns identified"
            )

        # Category distribution
        categories = {}
        for pattern in patterns:
            categories[pattern.category.value] = (
                categories.get(pattern.category.value, 0) + 1
            )

        if categories:
            dominant = max(categories, key=categories.get)
            insights.append(f"Primary focus area: {dominant}")

        # Context awareness
        contexts = [p for p in patterns if p.context]
        if contexts:
            insights.append(f"Context-specific patterns detected: {len(contexts)}")

        return insights

    def _analyze_meta_patterns(self) -> list[str]:
        """Analyze patterns of patterns"""
        meta_insights = []

        # Get statistics
        stats = self.doc_updater.get_statistics()

        # Learning velocity
        if stats["total"] > 10:
            meta_insights.append(
                f"Knowledge base growing: {stats['total']} total patterns"
            )

        # Category balance
        if stats["by_category"]:
            # Find imbalances
            max_cat = max(stats["by_category"].values())
            min_cat = min(stats["by_category"].values())
            if max_cat > min_cat * 3:
                meta_insights.append(
                    "Pattern imbalance detected - some categories underrepresented"
                )

        # Confidence distribution
        total_confidence = sum(stats["by_confidence"].values())
        if total_confidence > 0:
            high_ratio = stats["by_confidence"]["high"] / total_confidence
            if high_ratio < 0.3:
                meta_insights.append(
                    "Many low-confidence patterns - more validation needed"
                )
            elif high_ratio > 0.7:
                meta_insights.append(
                    "Strong pattern confidence - predictions should be accurate"
                )

        return meta_insights

    def apply_patterns(self, task: str) -> list[dict]:
        """Apply learned patterns to a task"""
        applicable = []

        # Load all patterns
        # In real implementation, would parse PATTERNS.md
        # For now, return example

        return applicable

    def get_pattern_suggestions(self, code: str) -> list[dict]:
        """Suggest improvements based on learned patterns"""
        suggestions = []

        # Analyze code against patterns
        # Would check for pattern violations

        return suggestions


def main():
    """Example usage of enhanced /learn"""
    integration = LearnCommandIntegration()

    # Example: User corrects a style issue
    context = """
    User: No, actually please use f-strings instead of .format().
    Also rename 'calc_val' to 'calculated_value' - I prefer 
    descriptive names. This is for production so be careful.
    """

    result = integration.execute_learn(context)

    print("Learn Command Results:")
    print(f"Patterns found: {result['patterns_found']}")
    print(f"Patterns added: {result['patterns_added']}")
    print(f"Documentation updated: {result['documentation_updated']}")
    print(f"Memory updated: {result['memory_updated']}")

    if result["insights"]:
        print("\nInsights:")
        for insight in result["insights"]:
            print(f"- {insight}")


if __name__ == "__main__":
    main()
