#!/usr/bin/env python3
"""
Integration Examples for Cognitive Enhancement Framework
========================================================

This module demonstrates practical integration patterns for the cognitive
enhancement framework in real conversation scenarios.

Examples include:
- Simple response wrapper usage
- Advanced conversation management
- Custom learning pattern creation
- Memory-guided decision making
"""

import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

from enhanced_learn import EnhancedLearner, LearningPattern
from query_patterns import PatternQueryEngine
from memory_integration import ConversationMemoryManager, memory_enhanced_response


class PracticalAssistant:
    """Example AI assistant with memory integration."""
    
    def __init__(self):
        self.memory_manager = ConversationMemoryManager()
        self.response_history = []
    
    def respond(self, user_message: str) -> str:
        """Generate memory-enhanced response."""
        
        def base_response_generator(message: str) -> str:
            """Base response logic without memory enhancement."""
            # This would be your main response generation logic
            
            if "api" in message.lower():
                return "For API development, I recommend following RESTful principles with proper HTTP methods."
            elif "test" in message.lower():
                return "Testing is crucial for reliable software. Consider unit tests, integration tests, and end-to-end tests."
            elif "deploy" in message.lower():
                return "Deployment should follow a CI/CD pipeline with proper staging and production environments."
            else:
                return f"I understand you're asking about: {message}. Let me help you with that."
        
        # Use memory manager to enhance the response
        enhanced_response = self.memory_manager.process_turn(user_message, base_response_generator)
        
        # Store in history
        self.response_history.append({
            'user': user_message,
            'response': enhanced_response,
            'timestamp': datetime.now().isoformat()
        })
        
        return enhanced_response
    
    def get_learning_summary(self) -> Dict[str, Any]:
        """Get summary of what has been learned."""
        conversation_summary = self.memory_manager.get_conversation_summary()
        learner_analysis = self.memory_manager.learner.analyze_learning_trends()
        
        return {
            'conversation_stats': conversation_summary,
            'learning_analysis': learner_analysis,
            'total_responses': len(self.response_history)
        }


class SpecializedResponseHandler:
    """Example of specialized response handling with memory."""
    
    def __init__(self, domain: str = "technical"):
        self.domain = domain
        self.learner = EnhancedLearner()
        self.query_engine = PatternQueryEngine(self.learner)
        
        # Pre-populate with domain-specific patterns
        self._initialize_domain_knowledge()
    
    def _initialize_domain_knowledge(self):
        """Initialize with domain-specific patterns."""
        if self.domain == "technical":
            patterns = [
                LearningPattern(
                    pattern_type="best_practice",
                    content="Always validate input parameters before processing",
                    context="Security and reliability",
                    confidence=0.9,
                    timestamp=datetime.now().isoformat(),
                    source="domain_knowledge",
                    examples=["input validation", "parameter checking"],
                    tags=["security", "validation", "best_practice"]
                ),
                LearningPattern(
                    pattern_type="preference",
                    content="Use clear variable names instead of abbreviations",
                    context="Code readability",
                    confidence=0.8,
                    timestamp=datetime.now().isoformat(),
                    source="coding_standards",
                    examples=["user_count vs uc", "database_connection vs db_conn"],
                    tags=["readability", "naming", "standards"]
                )
            ]
            
            for pattern in patterns:
                self.learner.add_pattern(pattern)
    
    def handle_query(self, query: str) -> str:
        """Handle query with domain-specific memory consultation."""
        
        # Query relevant patterns
        query_result = self.query_engine.query_patterns(query)
        
        # Generate base response
        base_response = self._generate_base_response(query)
        
        # Enhance with memory if relevant patterns found
        if query_result.matches:
            memory_insights = self._extract_memory_insights(query_result)
            enhanced_response = f"{base_response}\n\n## Memory Insights\n{memory_insights}"
            return enhanced_response
        
        return base_response
    
    def _generate_base_response(self, query: str) -> str:
        """Generate base response for the domain."""
        if self.domain == "technical":
            return f"Technical response for: {query}"
        else:
            return f"Response for: {query}"
    
    def _extract_memory_insights(self, query_result) -> str:
        """Extract actionable insights from memory query."""
        insights = []
        
        for match in query_result.matches[:3]:  # Top 3 matches
            pattern = match.pattern
            insight = f"• **{pattern.pattern_type.title()}**: {pattern.content}"
            if pattern.confidence >= 0.8:
                insight += " (High confidence)"
            insights.append(insight)
        
        return "\n".join(insights)


@memory_enhanced_response()
def simple_qa_function(user_question: str) -> str:
    """Example of using the decorator for simple Q&A."""
    # This function gets automatically enhanced with memory
    return f"Answer to your question: {user_question}"


class ConversationFlowManager:
    """Example of managing complex conversation flows with memory."""
    
    def __init__(self):
        self.learner = EnhancedLearner()
        self.memory_manager = ConversationMemoryManager(self.learner)
        self.conversation_state = {}
    
    def start_debugging_session(self, error_description: str) -> str:
        """Start a debugging session with memory consultation."""
        self.conversation_state['mode'] = 'debugging'
        self.conversation_state['initial_error'] = error_description
        
        # Check for similar past debugging sessions
        similar_patterns = self.learner.query_relevant_patterns(
            f"debugging error {error_description}"
        )
        
        response = f"Starting debugging session for: {error_description}\n\n"
        
        if similar_patterns:
            response += "## Past Experience\n"
            response += "I found similar debugging patterns from previous sessions:\n"
            for pattern in similar_patterns[:2]:
                response += f"• {pattern.content}\n"
            response += "\nLet me apply this experience to your current issue.\n\n"
        
        response += "## Next Steps\n"
        response += "1. Let's gather more details about the error\n"
        response += "2. Check the most common causes\n"
        response += "3. Apply systematic debugging approach\n"
        
        return self.memory_manager.process_turn(error_description, lambda x: response)
    
    def continue_debugging(self, additional_info: str) -> str:
        """Continue debugging with accumulated context."""
        if self.conversation_state.get('mode') != 'debugging':
            return "Please start a debugging session first."
        
        # Build context from conversation state
        context = f"Initial error: {self.conversation_state['initial_error']}\n"
        context += f"Additional info: {additional_info}"
        
        def debug_response_generator(info: str) -> str:
            return f"Based on the additional information: {info}\n\nLet me analyze this in context of our debugging session."
        
        return self.memory_manager.process_turn(additional_info, debug_response_generator)


class LearningFromFeedback:
    """Example of systematic learning from user feedback."""
    
    def __init__(self):
        self.learner = EnhancedLearner()
        self.feedback_patterns = []
    
    def process_feedback(self, original_response: str, user_feedback: str) -> str:
        """Process user feedback and create learning patterns."""
        
        # Detect feedback type
        feedback_type = self._classify_feedback(user_feedback)
        
        # Create learning pattern
        pattern = LearningPattern(
            pattern_type="feedback",
            content=f"User feedback: {user_feedback}",
            context=f"Original response: {original_response[:100]}...",
            confidence=0.8,
            timestamp=datetime.now().isoformat(),
            source="user_feedback",
            examples=[user_feedback],
            tags=[feedback_type, "user_input", "improvement"]
        )
        
        self.learner.add_pattern(pattern)
        
        # Generate acknowledgment
        acknowledgment = f"""
## Feedback Acknowledged

**Feedback Type:** {feedback_type.title()}
**Your Input:** {user_feedback}
**My Learning:** This feedback helps me understand your preferences better.

I've integrated this into my knowledge base to improve future responses.
"""
        
        return acknowledgment
    
    def _classify_feedback(self, feedback: str) -> str:
        """Classify the type of feedback."""
        feedback_lower = feedback.lower()
        
        if any(word in feedback_lower for word in ['wrong', 'incorrect', 'error']):
            return 'correction'
        elif any(word in feedback_lower for word in ['good', 'great', 'helpful', 'thanks']):
            return 'positive'
        elif any(word in feedback_lower for word in ['better', 'improve', 'prefer']):
            return 'suggestion'
        elif any(word in feedback_lower for word in ['unclear', 'confusing', 'explain']):
            return 'clarification_request'
        else:
            return 'general'


def demonstrate_memory_integration():
    """Demonstrate various memory integration patterns."""
    
    print("=== Cognitive Enhancement Framework Integration Examples ===\n")
    
    # Example 1: Basic Assistant
    print("1. Basic Memory-Enhanced Assistant")
    print("-" * 40)
    assistant = PracticalAssistant()
    
    response1 = assistant.respond("How do I create an API endpoint?")
    print(f"Response: {response1}\n")
    
    response2 = assistant.respond("Actually, you should mention authentication for API security.")
    print(f"Response: {response2}\n")
    
    response3 = assistant.respond("Can you tell me about API endpoints again?")
    print(f"Response: {response3}\n")
    
    learning_summary = assistant.get_learning_summary()
    print(f"Learning Summary: {learning_summary}\n")
    
    # Example 2: Specialized Handler
    print("2. Specialized Technical Handler")
    print("-" * 40)
    tech_handler = SpecializedResponseHandler("technical")
    
    tech_response = tech_handler.handle_query("How do I validate user input?")
    print(f"Technical Response: {tech_response}\n")
    
    # Example 3: Decorator Usage
    print("3. Decorator-Enhanced Function")
    print("-" * 40)
    decorator_response = simple_qa_function("What's the best way to handle errors?")
    print(f"Decorator Response: {decorator_response}\n")
    
    # Example 4: Conversation Flow
    print("4. Complex Conversation Flow")
    print("-" * 40)
    flow_manager = ConversationFlowManager()
    
    debug_start = flow_manager.start_debugging_session("My API returns 500 errors")
    print(f"Debug Start: {debug_start}\n")
    
    debug_continue = flow_manager.continue_debugging("The error happens when I send POST requests")
    print(f"Debug Continue: {debug_continue}\n")
    
    # Example 5: Feedback Learning
    print("5. Learning from Feedback")
    print("-" * 40)
    feedback_learner = LearningFromFeedback()
    
    original = "You should use GET requests for data submission."
    feedback = "That's wrong. Use POST for data submission, not GET."
    
    feedback_response = feedback_learner.process_feedback(original, feedback)
    print(f"Feedback Response: {feedback_response}\n")


if __name__ == "__main__":
    demonstrate_memory_integration()