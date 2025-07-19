#!/usr/bin/env python3
"""
Enhanced Execute Command Wrapper with Pattern Query Integration
===============================================================

This module provides an enhanced /execute command wrapper that automatically
queries learned patterns before execution to improve decision quality and
avoid repeated mistakes.

Integration Features:
- Automatic pattern querying before task execution
- Memory-informed execution planning
- Pattern-guided decision making
- Learning integration feedback loop
"""

import os
import sys
from dataclasses import dataclass

# Import the cognitive enhancement framework
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from enhanced_learn import EnhancedLearner
from query_patterns import (
    MemoryConsciousResponseGenerator,
    PatternQueryEngine,
    QueryResult,
)


@dataclass
class ExecutionContext:
    """Context information for command execution."""

    command: str
    task_description: str
    complexity: str  # "Low", "Medium", "High"
    pattern_guidance: str | None
    memory_insights: QueryResult | None
    recommended_approach: str
    checkpoint_frequency: str


class EnhancedExecuteWrapper:
    """Enhanced execute command wrapper with pattern query integration."""

    def __init__(self):
        self.learner = EnhancedLearner()
        self.query_engine = PatternQueryEngine(self.learner)
        self.memory_generator = MemoryConsciousResponseGenerator(self.learner)

    def analyze_task_complexity(self, task: str) -> str:
        """Analyze task complexity based on keywords and structure."""
        task_lower = task.lower()

        # High complexity indicators
        high_complexity = [
            "architecture",
            "refactor",
            "migration",
            "integration",
            "system",
            "multiple",
            "complex",
            "across",
            "entire",
            "comprehensive",
        ]

        # Medium complexity indicators
        medium_complexity = [
            "implement",
            "create",
            "build",
            "modify",
            "update",
            "enhance",
            "api",
            "database",
            "test",
            "feature",
        ]

        # Low complexity indicators
        low_complexity = ["fix", "debug", "small", "quick", "simple", "single", "minor"]

        # Count matches
        high_score = sum(1 for keyword in high_complexity if keyword in task_lower)
        medium_score = sum(1 for keyword in medium_complexity if keyword in task_lower)
        low_score = sum(1 for keyword in low_complexity if keyword in task_lower)

        # Determine complexity
        if high_score >= 2 or len(task.split()) > 15:
            return "High"
        if medium_score >= 2 or len(task.split()) > 8:
            return "Medium"
        if low_score >= 1 or len(task.split()) <= 5:
            return "Low"
        return "Medium"  # Default

    def query_execution_patterns(self, task: str) -> QueryResult | None:
        """Query patterns relevant to task execution."""
        # Enhance query with execution context
        execution_query = f"execute task: {task} implementation approach workflow"

        result = self.query_engine.query_patterns(execution_query, limit=5)

        # Also check for specific task-related patterns
        task_specific_query = f"{task} similar previous experience"
        task_result = self.query_engine.query_patterns(task_specific_query, limit=3)

        # Combine results
        if result.matches or task_result.matches:
            # Merge recommendations
            combined_recommendations = []
            if result.recommendations:
                combined_recommendations.extend(result.recommendations)
            if task_result.recommendations:
                combined_recommendations.extend(task_result.recommendations)

            # Return the more comprehensive result
            if len(result.matches) >= len(task_result.matches):
                result.recommendations = combined_recommendations
                return result
            task_result.recommendations = combined_recommendations
            return task_result

        return None

    def generate_execution_approach(self, context: ExecutionContext) -> str:
        """Generate execution approach based on complexity and patterns."""
        approach_parts = []

        # Base approach by complexity
        if context.complexity == "High":
            approach_parts.append(
                "🚨 HIGH COMPLEXITY: Use subagent coordination with parallel execution"
            )
            approach_parts.append("• Create worktrees for isolated development")
            approach_parts.append("• Define clear subagent responsibilities")
            approach_parts.append("• Establish synchronization points")
        elif context.complexity == "Medium":
            approach_parts.append("⚠️ MEDIUM COMPLEXITY: Consider subagent assistance")
            approach_parts.append("• Evaluate if parallel work would benefit")
            approach_parts.append("• Use direct execution with careful checkpoints")
        else:
            approach_parts.append("✅ LOW COMPLEXITY: Direct execution appropriate")
            approach_parts.append("• Single-threaded implementation")
            approach_parts.append("• Standard checkpoint frequency")

        # Pattern-informed modifications
        if context.memory_insights and context.memory_insights.matches:
            approach_parts.append("\n🧠 PATTERN INSIGHTS:")

            # Look for execution preferences in patterns
            for match in context.memory_insights.matches[:3]:
                pattern = match.pattern
                if (
                    "execution" in pattern.content.lower()
                    or "approach" in pattern.content.lower()
                ):
                    approach_parts.append(f"• {pattern.content[:80]}...")

                # Check for workflow patterns
                if match.pattern.pattern_type == "workflow":
                    approach_parts.append(
                        f"• Follow established workflow: {pattern.content[:60]}..."
                    )

                # Check for corrections
                if match.pattern.pattern_type == "correction":
                    approach_parts.append(
                        f"• ⚠️ Avoid previous mistake: {pattern.content[:60]}..."
                    )

        return "\n".join(approach_parts)

    def determine_checkpoint_frequency(
        self, complexity: str, patterns: QueryResult | None
    ) -> str:
        """Determine appropriate checkpoint frequency."""
        base_frequency = {
            "High": "Every 3 minutes OR 2-3 files",
            "Medium": "Every 5 minutes OR 3-5 files",
            "Low": "Every 7 minutes OR 5-7 files",
        }

        # Check patterns for frequency preferences
        if patterns and patterns.matches:
            for match in patterns.matches:
                content_lower = match.pattern.content.lower()
                if "checkpoint" in content_lower or "frequency" in content_lower:
                    if "frequent" in content_lower or "often" in content_lower:
                        return "Every 3 minutes OR 2-3 files (pattern-recommended)"
                    if "less" in content_lower or "reduced" in content_lower:
                        return "Every 7 minutes OR 5-7 files (pattern-recommended)"

        return base_frequency[complexity]

    def generate_todowrite_checklist(
        self, context: ExecutionContext, command_type: str
    ) -> str:
        """Generate enhanced TodoWrite checklist with pattern insights."""

        checklist = f"""## EXECUTE PROTOCOL CHECKLIST - ENHANCED WITH MEMORY
- [ ] Context check: 85% remaining
- [ ] Task complexity assessment: {context.complexity}
- [ ] Pattern query completed: {"✅ YES" if context.memory_insights else "❌ NO"}
- [ ] Execution approach: {context.recommended_approach.split(":")[0].replace("🚨", "").replace("⚠️", "").replace("✅", "").strip()}
- [ ] Checkpoint frequency: {context.checkpoint_frequency}
- [ ] Scratchpad location: roadmap/scratchpad_[branch].md
- [ ] PR update strategy: Push at each checkpoint"""

        if command_type == "plan":
            checklist += """
- [ ] Subagent strategy needed? Yes/No (Why: ___)
- [ ] Git worktree strategy confirmed: Yes/No
- [ ] Parallel execution strategy: Yes/No (Why: ___)
- [ ] Worktree usage justified: Yes/No (Why: ___)
- [ ] Subagent coordination plan: ___
- [ ] 🚨 MANDATORY: Complete plan presented to user: YES/NO
- [ ] User approval received: YES/NO"""
        else:
            checklist += """
- [ ] Best judgment strategy determined: Based on complexity + patterns
- [ ] Ready to execute immediately: YES"""

        if context.memory_insights and context.memory_insights.matches:
            checklist += f"""

## MEMORY INSIGHTS APPLIED
- [ ] Pattern guidance reviewed: {len(context.memory_insights.matches)} relevant patterns found
- [ ] High-confidence corrections applied: {sum(1 for m in context.memory_insights.matches if m.pattern.pattern_type == "correction" and m.pattern.confidence >= 0.8)}
- [ ] User preferences considered: {sum(1 for m in context.memory_insights.matches if m.pattern.pattern_type == "preference")}
- [ ] Workflow patterns followed: {sum(1 for m in context.memory_insights.matches if m.pattern.pattern_type == "workflow")}"""

        return checklist

    def format_pattern_guidance(self, context: ExecutionContext) -> str:
        """Format pattern guidance for display."""
        if not context.memory_insights or not context.memory_insights.matches:
            return "No relevant patterns found in memory."

        output = []
        output.append("🧠 MEMORY CONSULTATION RESULTS:")
        output.append(
            f"Found {len(context.memory_insights.matches)} relevant patterns from {context.memory_insights.total_searched} total patterns"
        )

        # Group by type for better organization
        by_type = {}
        for match in context.memory_insights.matches:
            pattern_type = match.pattern.pattern_type
            if pattern_type not in by_type:
                by_type[pattern_type] = []
            by_type[pattern_type].append(match)

        # Display by type with appropriate emphasis
        for pattern_type, matches in by_type.items():
            if pattern_type == "correction":
                output.append(f"\n🚨 CRITICAL CORRECTIONS ({len(matches)}):")
                for match in matches:
                    confidence_marker = "⚠️" if match.pattern.confidence >= 0.8 else "ℹ️"
                    output.append(
                        f"  {confidence_marker} {match.pattern.content[:100]}..."
                    )

            elif pattern_type == "preference":
                output.append(f"\n🎯 USER PREFERENCES ({len(matches)}):")
                for match in matches:
                    output.append(f"  • {match.pattern.content[:100]}...")

            elif pattern_type == "workflow":
                output.append(f"\n📋 ESTABLISHED WORKFLOWS ({len(matches)}):")
                for match in matches:
                    output.append(f"  • {match.pattern.content[:100]}...")

            elif pattern_type == "technical":
                output.append(f"\n🔧 TECHNICAL INSIGHTS ({len(matches)}):")
                for match in matches:
                    output.append(f"  • {match.pattern.content[:100]}...")

        # Add recommendations
        if context.memory_insights.recommendations:
            output.append("\n💡 MEMORY RECOMMENDATIONS:")
            for rec in context.memory_insights.recommendations:
                output.append(f"  • {rec}")

        return "\n".join(output)

    def enhanced_execute(self, task: str, command_type: str = "execute") -> str:
        """Execute enhanced command with pattern query integration."""

        # Step 1: Query patterns for relevant information
        memory_insights = self.query_execution_patterns(task)

        # Step 2: Analyze task complexity
        complexity = self.analyze_task_complexity(task)

        # Step 3: Generate execution approach
        execution_context = ExecutionContext(
            command=command_type,
            task_description=task,
            complexity=complexity,
            pattern_guidance=None,
            memory_insights=memory_insights,
            recommended_approach="",
            checkpoint_frequency="",
        )

        # Step 4: Generate approach and frequency based on patterns
        execution_context.recommended_approach = self.generate_execution_approach(
            execution_context
        )
        execution_context.checkpoint_frequency = self.determine_checkpoint_frequency(
            complexity, memory_insights
        )

        # Step 5: Format pattern guidance
        pattern_guidance = self.format_pattern_guidance(execution_context)
        execution_context.pattern_guidance = pattern_guidance

        # Step 6: Generate TodoWrite checklist
        checklist = self.generate_todowrite_checklist(execution_context, command_type)

        # Step 7: Format complete response
        response_parts = []

        if command_type == "plan":
            response_parts.append(f"I'll plan the execution of: {task}")
            response_parts.append(
                "First, let me consult my memory for relevant patterns..."
            )
        else:
            response_parts.append(f"I'll execute: {task}")
            response_parts.append("Consulting memory patterns for guidance...")

        response_parts.append("\n" + pattern_guidance)
        response_parts.append(f"\n**Complexity Assessment**: {complexity}")
        response_parts.append(
            f"**Recommended Approach**: {execution_context.recommended_approach}"
        )
        response_parts.append(
            f"**Checkpoint Frequency**: {execution_context.checkpoint_frequency}"
        )

        response_parts.append(f"\n{checklist}")

        if command_type == "plan":
            response_parts.append(
                "\n⏸️ **PLAN PRESENTED** - Waiting for your approval to proceed..."
            )
        else:
            response_parts.append(
                "\n🚀 **READY TO EXECUTE** - Beginning implementation with pattern-informed approach..."
            )

        return "\n".join(response_parts)


def main():
    """Example usage of the enhanced execute wrapper."""
    wrapper = EnhancedExecuteWrapper()

    # Test examples
    test_tasks = [
        "Fix the JSON parsing bug in the API endpoint",
        "Implement comprehensive user authentication system with OAuth",
        "Add a simple logging statement to the main function",
    ]

    for task in test_tasks:
        print(f"\n{'=' * 60}")
        print(f"TASK: {task}")
        print("=" * 60)
        result = wrapper.enhanced_execute(task, "execute")
        print(result)


if __name__ == "__main__":
    main()
