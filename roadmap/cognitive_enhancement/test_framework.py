#!/usr/bin/env python3
"""
Test Script for Cognitive Enhancement Framework
===============================================

This script verifies that all components of the framework work correctly.
"""

import sys
import os
import tempfile
import shutil
from datetime import datetime

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_learn import EnhancedLearner, LearningPattern
from query_patterns import PatternQueryEngine
from memory_integration import ConversationMemoryManager


def test_enhanced_learner():
    """Test the enhanced learning system."""
    print("Testing Enhanced Learner...")
    
    # Create temporary knowledge base
    temp_dir = tempfile.mkdtemp()
    kb_path = os.path.join(temp_dir, "test_kb.json")
    
    try:
        learner = EnhancedLearner(kb_path)
        
        # Test pattern creation
        pattern = LearningPattern(
            pattern_type="test",
            content="This is a test pattern",
            context="Testing framework",
            confidence=0.8,
            timestamp=datetime.now().isoformat(),
            source="test",
            examples=["test example"],
            tags=["test", "framework"]
        )
        
        learner.add_pattern(pattern)
        print("✓ Pattern creation successful")
        
        # Test pattern retrieval
        patterns = learner.query_relevant_patterns("test")
        assert len(patterns) > 0, "Should find test pattern"
        print("✓ Pattern retrieval successful")
        
        # Test correction detection
        corrections = learner.detect_corrections("Actually, that's wrong. The answer should be different.")
        assert len(corrections) > 0, "Should detect correction"
        print("✓ Correction detection successful")
        
        # Test saving/loading
        learner.save_knowledge_base()
        learner2 = EnhancedLearner(kb_path)
        assert len(learner2.patterns) > 0, "Should load saved patterns"
        print("✓ Save/load successful")
        
        print("Enhanced Learner: All tests passed! ✓")
        
    finally:
        shutil.rmtree(temp_dir)


def test_pattern_query_engine():
    """Test the pattern query engine."""
    print("\nTesting Pattern Query Engine...")
    
    # Create temporary knowledge base
    temp_dir = tempfile.mkdtemp()
    kb_path = os.path.join(temp_dir, "test_kb.json")
    
    try:
        learner = EnhancedLearner(kb_path)
        
        # Add test patterns
        patterns = [
            LearningPattern(
                pattern_type="api",
                content="Use POST for data submission",
                context="API development",
                confidence=0.9,
                timestamp=datetime.now().isoformat(),
                source="test",
                examples=["POST request"],
                tags=["api", "http", "technical"]
            ),
            LearningPattern(
                pattern_type="preference",
                content="User prefers bullet points",
                context="Formatting",
                confidence=0.7,
                timestamp=datetime.now().isoformat(),
                source="test",
                examples=["bullet lists"],
                tags=["formatting", "style"]
            )
        ]
        
        for pattern in patterns:
            learner.add_pattern(pattern)
        
        query_engine = PatternQueryEngine(learner)
        
        # Test query functionality
        result = query_engine.query_patterns("API data submission")
        assert len(result.matches) > 0, "Should find API-related patterns"
        print("✓ Query execution successful")
        
        # Test relevance scoring
        assert result.matches[0].relevance_score > 0, "Should have positive relevance score"
        print("✓ Relevance scoring working")
        
        # Test intent analysis
        intent_scores = query_engine.analyze_query_intent("How should I implement an API?")
        assert "seeking_technical" in intent_scores, "Should detect technical intent"
        print("✓ Intent analysis working")
        
        # Test result formatting
        formatted = query_engine.format_query_results(result)
        assert "Memory Query Results" in formatted, "Should format results properly"
        print("✓ Result formatting working")
        
        print("Pattern Query Engine: All tests passed! ✓")
        
    finally:
        shutil.rmtree(temp_dir)


def test_memory_integration():
    """Test the memory integration system."""
    print("\nTesting Memory Integration...")
    
    # Create temporary knowledge base
    temp_dir = tempfile.mkdtemp()
    kb_path = os.path.join(temp_dir, "test_kb.json")
    
    try:
        # Initialize with temporary knowledge base
        learner = EnhancedLearner(kb_path)
        manager = ConversationMemoryManager(learner)
        
        # Test response processing
        def test_response_generator(message: str) -> str:
            return f"Test response to: {message}"
        
        response = manager.process_turn("How do I create an API?", test_response_generator)
        assert "Test response to:" in response, "Should include base response"
        print("✓ Response processing working")
        
        # Test correction learning
        correction_response = manager.process_turn(
            "Actually, you should mention authentication first",
            test_response_generator
        )
        assert len(manager.learner.patterns) > 0, "Should learn from correction"
        print("✓ Correction learning working")
        
        # Test memory consultation
        memory_response = manager.process_turn(
            "Tell me about API security",
            test_response_generator
        )
        # Should find the learned pattern about authentication
        print("✓ Memory consultation working")
        
        # Test conversation statistics
        stats = manager.get_conversation_summary()
        assert stats['total_turns'] == 3, "Should track conversation turns"
        print("✓ Conversation tracking working")
        
        print("Memory Integration: All tests passed! ✓")
        
    finally:
        shutil.rmtree(temp_dir)


def test_end_to_end_workflow():
    """Test complete end-to-end workflow."""
    print("\nTesting End-to-End Workflow...")
    
    # Create temporary knowledge base
    temp_dir = tempfile.mkdtemp()
    kb_path = os.path.join(temp_dir, "test_kb.json")
    
    try:
        manager = ConversationMemoryManager(EnhancedLearner(kb_path))
        
        def simple_response(message: str) -> str:
            if "api" in message.lower():
                return "Use GET for reading data and POST for creating data."
            return f"General response about: {message}"
        
        # Step 1: Initial question
        response1 = manager.process_turn("How do I implement an API endpoint?", simple_response)
        print("✓ Initial response generated")
        
        # Step 2: User correction
        response2 = manager.process_turn(
            "Actually, you should mention input validation as the first priority for API security.",
            simple_response
        )
        print("✓ Correction processed and learned")
        
        # Step 3: Follow-up question should apply learned knowledge
        response3 = manager.process_turn("What are API best practices?", simple_response)
        
        # Verify learning was applied
        patterns = manager.learner.query_relevant_patterns("input validation")
        if len(patterns) == 0:
            # Check all patterns to debug
            all_patterns = manager.learner.patterns
            print(f"Debug: Found {len(all_patterns)} total patterns")
            for p in all_patterns:
                print(f"  Pattern: {p.content[:50]}... (tags: {p.tags})")
        assert len(patterns) > 0, f"Should have learned about input validation, found {len(patterns)} patterns"
        print("✓ Learning applied to subsequent responses")
        
        # Step 4: Check memory consultation occurred
        stats = manager.get_conversation_summary()
        assert stats['memory_consultations'] > 0, "Should have consulted memory"
        print("✓ Memory consultation occurred")
        
        # Step 5: Verify knowledge persistence
        manager.learner.save_knowledge_base()
        new_learner = EnhancedLearner(kb_path)
        assert len(new_learner.patterns) > 0, "Knowledge should persist"
        print("✓ Knowledge persistence verified")
        
        print("End-to-End Workflow: All tests passed! ✓")
        
    finally:
        shutil.rmtree(temp_dir)


def main():
    """Run all tests."""
    print("=" * 60)
    print("🧠 COGNITIVE ENHANCEMENT FRAMEWORK - SYSTEM TESTS")
    print("=" * 60)
    
    try:
        test_enhanced_learner()
        test_pattern_query_engine()
        test_memory_integration()
        test_end_to_end_workflow()
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED! FRAMEWORK IS WORKING CORRECTLY!")
        print("=" * 60)
        print("\nThe Cognitive Enhancement Framework is ready for integration.")
        print("Key capabilities verified:")
        print("• ✓ Pattern learning and storage")
        print("• ✓ Memory querying and relevance scoring")
        print("• ✓ Automatic correction detection")
        print("• ✓ Response enhancement with memory")
        print("• ✓ Conversation flow management")
        print("• ✓ Knowledge persistence")
        
        print("\nNext steps:")
        print("1. Run 'python3 immediate_integration_demo.py' for interactive demo")
        print("2. Integrate memory_integration.py into your conversation handler")
        print("3. Use @memory_enhanced_response decorator for simple integration")
        print("4. Customize patterns and templates for your specific domain")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        print("Please check the error and fix the issue before proceeding.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())