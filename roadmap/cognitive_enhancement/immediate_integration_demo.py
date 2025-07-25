#!/usr/bin/env python3

from memory_integration import memory_enhanced_response

"""
Immediate Integration Demo for Cognitive Enhancement Framework
==============================================================

This script demonstrates how to immediately start using the cognitive enhancement
framework in your conversations. It shows practical, working examples that can
be used right away.

Run this script to see the framework in action!
"""

import os
import sys
from datetime import datetime

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_learn import EnhancedLearner, LearningPattern
from memory_integration import ConversationMemoryManager
from query_patterns import PatternQueryEngine


class DemoAssistant:
    """Demo assistant with full memory integration."""

    def __init__(self):
        self.memory_manager = ConversationMemoryManager()
        self.conversation_count = 0

        # Pre-populate with some example patterns
        self._initialize_demo_patterns()

    def _initialize_demo_patterns(self):
        """Initialize with demonstration patterns."""
        demo_patterns = [
            LearningPattern(
                pattern_type="correction",
                content="Use POST for data submission, not GET",
                context="API endpoint discussion",
                confidence=0.9,
                timestamp=datetime.now().isoformat(),
                source="user_correction",
                examples=["POST for creating data", "GET for reading data"],
                tags=["api", "http", "technical", "critical"],
            ),
            LearningPattern(
                pattern_type="preference",
                content="User prefers bullet points over numbered lists",
                context="Response formatting",
                confidence=0.8,
                timestamp=datetime.now().isoformat(),
                source="user_feedback",
                examples=["bullet point lists", "• item format"],
                tags=["formatting", "preference", "style"],
            ),
            LearningPattern(
                pattern_type="workflow",
                content="Always explain the reasoning before giving the solution",
                context="Problem-solving approach",
                confidence=0.7,
                timestamp=datetime.now().isoformat(),
                source="observation",
                examples=["explain then solve", "reasoning first"],
                tags=["methodology", "explanation", "structure"],
            ),
            LearningPattern(
                pattern_type="technical",
                content="Include error handling in all code examples",
                context="Code quality standards",
                confidence=0.8,
                timestamp=datetime.now().isoformat(),
                source="best_practice",
                examples=["try-catch blocks", "error validation"],
                tags=["coding", "error_handling", "quality"],
            ),
        ]

        for pattern in demo_patterns:
            self.memory_manager.learner.add_pattern(pattern)

    def respond_to(self, user_message: str) -> str:
        """Generate response with memory integration."""
        self.conversation_count += 1

        def base_response_generator(message: str) -> str:
            """Generate base response without memory enhancement."""
            message_lower = message.lower()

            # Simple response logic for demonstration
            if "api" in message_lower:
                return """For API development, I recommend:
1. Use appropriate HTTP methods (GET for reading, POST for creating)
2. Implement proper authentication
3. Add input validation
4. Include comprehensive error handling
5. Document your endpoints clearly"""

            if "code" in message_lower or "programming" in message_lower:
                return """For coding best practices:
1. Write clear, readable code
2. Include error handling
3. Add meaningful comments
4. Test your code thoroughly
5. Follow consistent naming conventions"""

            if "test" in message_lower:
                return """For effective testing:
1. Write unit tests for individual functions
2. Create integration tests for workflows
3. Include edge case testing
4. Automate your test suite
5. Aim for good coverage"""

            if "deploy" in message_lower:
                return """For reliable deployment:
1. Use a CI/CD pipeline
2. Test in staging environment
3. Implement rollback procedures
4. Monitor application health
5. Use infrastructure as code"""

            return f"I understand you're asking about: {message}. Let me provide helpful information based on what I know and have learned from our conversations."

        # Use memory manager to enhance the response
        enhanced_response = self.memory_manager.process_turn(
            user_message, base_response_generator
        )

        return enhanced_response

    def show_learning_stats(self) -> str:
        """Show current learning statistics."""
        conv_summary = self.memory_manager.get_conversation_summary()
        learning_trends = self.memory_manager.learner.analyze_learning_trends()

        stats = f"""
📊 Learning Statistics:
• Total conversations: {self.conversation_count}
• Memory consultations: {conv_summary["memory_consultations"]}
• Patterns in knowledge base: {learning_trends["total_patterns"]}
• High confidence patterns: {learning_trends["confidence_distribution"]["high"]}
• Recent learning rate: {learning_trends["recent_learning_rate"]} patterns/week
• Consultation rate: {conv_summary["consultation_rate"]:.1%}
"""
        return stats.strip()

    def query_memory_directly(self, query: str) -> str:
        """Query memory directly and show results."""
        result = self.memory_manager.memory_response.query_engine.query_patterns(query)

        if not result.matches:
            return f"No relevant patterns found for: {query}"

        output = [f"🧠 Memory Query Results for: '{query}'\n"]

        for i, match in enumerate(result.matches[:3], 1):
            pattern = match.pattern
            output.append(f"{i}. [{pattern.pattern_type.upper()}] {pattern.content}")
            output.append(
                f"   Relevance: {match.relevance_score:.2f} | Confidence: {pattern.confidence:.1f}"
            )
            output.append(f"   Tags: {', '.join(pattern.tags[:3])}")
            output.append("")

        if result.recommendations:
            output.append("💡 Recommendations:")
            for rec in result.recommendations[:2]:
                output.append(f"• {rec}")

        return "\n".join(output)


def run_interactive_demo():
    """Run an interactive demonstration."""
    print("=" * 60)
    print("🧠 COGNITIVE ENHANCEMENT FRAMEWORK - INTERACTIVE DEMO")
    print("=" * 60)
    print()
    print("This demo shows how the framework learns from conversations.")
    print("Try asking about APIs, coding, testing, or deployment.")
    print("Provide corrections to see the learning in action!")
    print()
    print("Commands:")
    print("• 'stats' - Show learning statistics")
    print("• 'query: <text>' - Query memory directly")
    print("• 'quit' - Exit demo")
    print()

    assistant = DemoAssistant()

    while True:
        try:
            user_input = input("You: ").strip()

            if user_input.lower() in ["quit", "exit", "q"]:
                break
            if user_input.lower() == "stats":
                print(assistant.show_learning_stats())
                continue
            if user_input.lower().startswith("query:"):
                query = user_input[6:].strip()
                result = assistant.query_memory_directly(query)
                print(result)
                continue
            if not user_input:
                continue

            print("\nAssistant:", end=" ")
            response = assistant.respond_to(user_input)
            print(response)
            print()

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
            continue

    print("\n" + "=" * 60)
    print("📊 FINAL LEARNING STATISTICS")
    print("=" * 60)
    print(assistant.show_learning_stats())
    print("\nThank you for trying the Cognitive Enhancement Framework!")


def run_scripted_demo():
    """Run a scripted demonstration showing key features."""
    print("=" * 60)
    print("🧠 COGNITIVE ENHANCEMENT FRAMEWORK - SCRIPTED DEMO")
    print("=" * 60)

    assistant = DemoAssistant()

    # Demo conversations showing different features
    demo_conversations = [
        {
            "title": "1. Basic API Question",
            "user": "How do I create an API endpoint for user registration?",
            "show_memory": True,
        },
        {
            "title": "2. User Correction (Learning Event)",
            "user": "Actually, that's not quite right. You should always mention input validation first when discussing API security.",
            "show_memory": False,
        },
        {
            "title": "3. Follow-up Question (Memory Applied)",
            "user": "Can you tell me about API best practices again?",
            "show_memory": True,
        },
        {
            "title": "4. Different Domain Question",
            "user": "What are the best practices for writing unit tests?",
            "show_memory": True,
        },
        {
            "title": "5. Style Preference Feedback",
            "user": "I prefer when you use bullet points instead of numbered lists for summaries.",
            "show_memory": False,
        },
        {
            "title": "6. Test Memory Application",
            "user": "Can you summarize the key points about testing?",
            "show_memory": True,
        },
    ]

    for demo in demo_conversations:
        print(f"\n{demo['title']}")
        print("-" * len(demo["title"]))
        print(f"User: {demo['user']}")

        if demo["show_memory"]:
            # Show memory query first
            memory_result = assistant.query_memory_directly(demo["user"])
            if "No relevant patterns found" not in memory_result:
                print(f"\n🧠 Memory Check:\n{memory_result}")

        print(f"\nAssistant: {assistant.respond_to(demo['user'])}")

        input("\nPress Enter to continue...")

    print(f"\n{assistant.show_learning_stats()}")


def demonstrate_direct_integration():
    """Show how to integrate the framework directly into existing code."""
    print("=" * 60)
    print("🔧 DIRECT INTEGRATION EXAMPLES")
    print("=" * 60)

    print("\n1. Simple Function Enhancement:")
    print("-" * 40)

    # Example 1: Enhance existing function


    @memory_enhanced_response()
    def my_chat_function(user_input: str) -> str:
        return f"Basic response to: {user_input}"

    result = my_chat_function("Tell me about API security")
    print(f"Enhanced Response:\n{result}")

    print("\n2. Custom Response Handler:")
    print("-" * 40)

    # Example 2: Custom handler with memory
    learner = EnhancedLearner()
    query_engine = PatternQueryEngine(learner)

    def custom_handler(question: str) -> str:
        # Query memory first
        memory_result = query_engine.query_patterns(question)

        # Generate base response
        base_response = f"Standard answer for: {question}"

        # Enhance if memory found
        if memory_result.matches:
            memory_insights = "\n".join(
                [
                    f"• {match.pattern.content[:80]}..."
                    for match in memory_result.matches[:2]
                ]
            )
            return f"{base_response}\n\n🧠 Memory Insights:\n{memory_insights}"

        return base_response

    result = custom_handler("How should I handle API errors?")
    print(f"Custom Handler Response:\n{result}")

    print("\n3. Learning from Feedback:")
    print("-" * 40)

    # Example 3: Manual learning
    correction_message = (
        "You should mention rate limiting when discussing API security."
    )
    corrections = learner.detect_corrections(correction_message)

    if corrections:
        for correction in corrections:
            pattern = learner.learn_from_correction(
                correction, "API security discussion"
            )
            print(f"Learned Pattern: {pattern.content}")
            print(f"Confidence: {pattern.confidence}")
            print(f"Tags: {', '.join(pattern.tags)}")


if __name__ == "__main__":
    print("Choose demo mode:")
    print("1. Interactive Demo (recommended)")
    print("2. Scripted Demo")
    print("3. Direct Integration Examples")
    print("4. All Demos")

    choice = input("\nEnter choice (1-4): ").strip()

    if choice == "1":
        run_interactive_demo()
    elif choice == "2":
        run_scripted_demo()
    elif choice == "3":
        demonstrate_direct_integration()
    elif choice == "4":
        run_scripted_demo()
        print("\n" + "=" * 60)
        demonstrate_direct_integration()
        print("\n" + "=" * 60)
        print("Starting interactive demo...")
        run_interactive_demo()
    else:
        print("Invalid choice. Running interactive demo...")
        run_interactive_demo()
