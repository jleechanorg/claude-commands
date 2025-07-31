#!/usr/bin/env python3
"""
Memory Integration System for Cognitive Enhancement Framework
============================================================

This module provides the core integration layer that bridges learned patterns
with active conversation responses, enabling conscious memory consultation
and automatic learning integration.

Key Features:
- Response wrapper with memory consultation
- Automatic correction detection and learning
- Template-based memory integration
- Conversation flow management
"""

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from typing import Any

from enhanced_learn import EnhancedLearner, LearningPattern
from query_patterns import (
    MemoryConsciousResponseGenerator,
    PatternQueryEngine,
    QueryResult,
)


@dataclass
class ResponseContext:
    """Context for a response generation."""

    user_message: str
    conversation_history: list[str]
    previous_response: str
    query_intent: str
    domain: str
    complexity: str  # "simple", "moderate", "complex"


@dataclass
class MemoryConsultationResult:
    """Result of memory consultation."""

    should_consult: bool
    patterns_found: int
    high_priority_patterns: list[LearningPattern]
    recommendations: list[str]
    memory_guidance: str | None
    query_result: QueryResult | None


class MemoryIntegratedResponse:
    """Response wrapper that integrates memory consultation."""

    def __init__(self, learner: EnhancedLearner | None = None):
        self.learner = learner or EnhancedLearner()
        self.query_engine = PatternQueryEngine(self.learner)
        self.response_generator = MemoryConsciousResponseGenerator(self.learner)

        # Response templates
        self.templates = {
            "with_memory": self._load_template("response_with_memory.md"),
            "correction_detected": self._load_template("correction_response.md"),
            "learning_integration": self._load_template("learning_integration.md"),
        }

    def _load_template(self, template_name: str) -> str:
        """Load response template."""
        template_path = f"roadmap/cognitive_enhancement/templates/{template_name}"
        try:
            with open(template_path) as f:
                return f.read()
        except FileNotFoundError:
            # Return default template if file doesn't exist
            return self._get_default_template(template_name)

    def _get_default_template(self, template_name: str) -> str:
        """Get default template content."""
        templates = {
            "response_with_memory.md": """
## Memory Consultation

{memory_guidance}

## Response

{main_response}

## Learning Integration

{learning_notes}
""",
            "correction_response.md": """
## Correction Acknowledged

I notice you're correcting my previous response. Let me learn from this:

**Previous Understanding:** {previous_claim}
**Corrected Information:** {corrected_info}
**My Learning:** {learning_summary}

## Updated Response

{corrected_response}
""",
            "learning_integration.md": """
## Learning from This Conversation

**New Pattern Learned:** {pattern_content}
**Confidence Level:** {confidence}
**Application:** {application_notes}

This has been integrated into my knowledge base for future reference.
""",
        }
        return templates.get(template_name, "Template not found: {template_name}")

    def analyze_context(
        self,
        user_message: str,
        previous_response: str = "",
        conversation_history: list[str] = None,
    ) -> ResponseContext:
        """Analyze the context of a user message."""
        conversation_history = conversation_history or []

        # Determine query intent
        intent_patterns = {
            "question": r"\?|what|how|why|when|where|who",
            "correction": r"actually|no|wrong|incorrect|fix|correct",
            "request": r"please|can you|could you|would you",
            "clarification": r"clarify|explain|elaborate|meaning",
        }

        intent = "statement"
        for intent_type, pattern in intent_patterns.items():
            if re.search(pattern, user_message.lower()):
                intent = intent_type
                break

        # Determine domain
        domain_indicators = {
            "technical": [
                "code",
                "api",
                "function",
                "algorithm",
                "database",
                "programming",
            ],
            "process": ["workflow", "procedure", "steps", "process", "method"],
            "creative": ["story", "creative", "design", "art", "narrative"],
            "analytical": ["analysis", "data", "statistics", "research", "evaluate"],
        }

        domain = "general"
        for domain_type, indicators in domain_indicators.items():
            if any(indicator in user_message.lower() for indicator in indicators):
                domain = domain_type
                break

        # Determine complexity
        complexity = "simple"
        if len(user_message.split()) > 20:
            complexity = "moderate"
        if len(user_message.split()) > 50 or any(
            word in user_message.lower()
            for word in ["complex", "detailed", "comprehensive"]
        ):
            complexity = "complex"

        return ResponseContext(
            user_message=user_message,
            conversation_history=conversation_history,
            previous_response=previous_response,
            query_intent=intent,
            domain=domain,
            complexity=complexity,
        )

    def consult_memory(self, context: ResponseContext) -> MemoryConsultationResult:
        """Consult memory for relevant patterns."""

        # Determine if consultation is needed
        should_consult = (
            context.complexity in ["moderate", "complex"]
            or context.query_intent in ["correction", "question"]
            or len(context.user_message.split()) > 10
        )

        if not should_consult:
            return MemoryConsultationResult(
                should_consult=False,
                patterns_found=0,
                high_priority_patterns=[],
                recommendations=[],
                memory_guidance=None,
                query_result=None,
            )

        # Query patterns
        query_result = self.query_engine.query_patterns(context.user_message)

        # Identify high priority patterns
        high_priority = [
            match.pattern
            for match in query_result.matches
            if match.relevance_score > 1.5 or match.pattern.confidence >= 0.8
        ]

        # Generate memory guidance
        memory_guidance = None
        if query_result.matches:
            memory_guidance = self.query_engine.format_query_results(query_result)

        return MemoryConsultationResult(
            should_consult=True,
            patterns_found=len(query_result.matches),
            high_priority_patterns=high_priority,
            recommendations=query_result.recommendations,
            memory_guidance=memory_guidance,
            query_result=query_result,
        )

    def detect_and_learn_corrections(
        self, context: ResponseContext
    ) -> list[LearningPattern]:
        """Detect corrections and create learning patterns."""
        corrections = self.learner.detect_corrections(
            context.user_message, context.previous_response
        )
        learned_patterns = []

        for correction in corrections:
            pattern = self.learner.learn_from_correction(
                correction, context.user_message
            )
            learned_patterns.append(pattern)

        return learned_patterns

    def generate_memory_enhanced_response(
        self,
        context: ResponseContext,
        main_response: str,
        consultation_result: MemoryConsultationResult,
    ) -> str:
        """Generate response enhanced with memory consultation."""

        if (
            not consultation_result.should_consult
            or not consultation_result.memory_guidance
        ):
            return main_response

        # Use template to structure response
        template = self.templates["with_memory"]

        # Generate learning notes
        learning_notes = ""
        if consultation_result.high_priority_patterns:
            learning_notes = "Applied learned patterns:\n"
            for pattern in consultation_result.high_priority_patterns[:3]:
                learning_notes += f"• {pattern.content[:100]}...\n"

        return template.format(
            memory_guidance=consultation_result.memory_guidance,
            main_response=main_response,
            learning_notes=learning_notes or "No specific patterns applied.",
        )


    def generate_correction_response(
        self, context: ResponseContext, learned_patterns: list[LearningPattern]
    ) -> str:
        """Generate response acknowledging corrections."""

        if not learned_patterns:
            return ""

        # Use the most significant correction
        main_pattern = max(learned_patterns, key=lambda p: p.confidence)

        template = self.templates["correction_detected"]

        return template.format(
            previous_claim="[Previous response content]",
            corrected_info=main_pattern.content,
            learning_summary=f"I now understand: {main_pattern.content}",
            corrected_response="I'll apply this correction in my updated understanding.",
        )



class ConversationMemoryManager:
    """Manages memory integration across conversation turns."""

    def __init__(self, learner: EnhancedLearner | None = None):
        self.learner = learner or EnhancedLearner()
        self.memory_response = MemoryIntegratedResponse(self.learner)
        self.conversation_log = []

    def process_turn(
        self, user_message: str, generate_response_fn: Callable[[str], str]
    ) -> str:
        """Process a conversation turn with memory integration."""

        # Get previous response for context
        previous_response = ""
        if self.conversation_log:
            previous_response = self.conversation_log[-1].get("response", "")

        # Analyze context
        context = self.memory_response.analyze_context(
            user_message,
            previous_response,
            [turn["user"] for turn in self.conversation_log],
        )

        # Consult memory
        consultation_result = self.memory_response.consult_memory(context)

        # Detect corrections and learn
        learned_patterns = self.memory_response.detect_and_learn_corrections(context)

        # Generate main response
        main_response = generate_response_fn(user_message)

        # Handle corrections
        correction_response = ""
        if learned_patterns:
            correction_response = self.memory_response.generate_correction_response(
                context, learned_patterns
            )

        # Enhance with memory
        final_response = main_response
        if consultation_result.should_consult:
            final_response = self.memory_response.generate_memory_enhanced_response(
                context, main_response, consultation_result
            )

        # Prepend correction acknowledgment if needed
        if correction_response:
            final_response = correction_response + "\n\n" + final_response

        # Log conversation turn
        self.conversation_log.append(
            {
                "user": user_message,
                "response": final_response,
                "context": context,
                "consultation": consultation_result,
                "learned_patterns": len(learned_patterns),
                "timestamp": datetime.now().isoformat(),
            }
        )

        return final_response

    def get_conversation_summary(self) -> dict[str, Any]:
        """Get summary of conversation with learning statistics."""
        total_turns = len(self.conversation_log)
        memory_consultations = sum(
            1 for turn in self.conversation_log if turn["consultation"].should_consult
        )
        total_learned = sum(turn["learned_patterns"] for turn in self.conversation_log)

        return {
            "total_turns": total_turns,
            "memory_consultations": memory_consultations,
            "patterns_learned": total_learned,
            "consultation_rate": memory_consultations / total_turns
            if total_turns > 0
            else 0,
            "learning_rate": total_learned / total_turns if total_turns > 0 else 0,
        }


def memory_enhanced_response(learner: EnhancedLearner | None = None):
    """Decorator for memory-enhanced response functions."""

    def decorator(response_func):
        @wraps(response_func)
        def wrapper(user_message: str, *args, **kwargs):
            manager = ConversationMemoryManager(learner)
            return manager.process_turn(
                user_message, lambda msg: response_func(msg, *args, **kwargs)
            )

        return wrapper

    return decorator


def main():
    """Example usage of memory integration system."""

    # Initialize manager
    manager = ConversationMemoryManager()

    # Example response function
    def simple_response(message: str) -> str:
        return f"Standard response to: {message}"

    # Test conversation
    test_messages = [
        "How do I implement an API endpoint?",
        "Actually, that's wrong. You should use POST not GET for data submission.",
        "Can you show me the correct way again?",
    ]

    for message in test_messages:
        print(f"\nUser: {message}")
        response = manager.process_turn(message, simple_response)
        print(f"Assistant: {response}")

    # Show conversation summary
    summary = manager.get_conversation_summary()
    print(f"\nConversation Summary: {summary}")


if __name__ == "__main__":
    main()
