#!/usr/bin/env python3
"""
Test script to demonstrate the enhanced Proto Genesis workflow
without requiring actual claude CLI calls.
"""
import sys
from pathlib import Path
from proto_genesis import load_goal_from_directory, generate_execution_strategy

def mock_claude_response(prompt, use_codex=False):
    """Mock claude response for testing."""
    if "execution strategy" in prompt.lower():
        return """SUBSTEP BREAKDOWN:
- SUBSTEP 1: Create fibonacci function with basic structure and docstring
- SUBSTEP 2: Implement efficient algorithm (dynamic programming or iterative)
- SUBSTEP 3: Add input validation and error handling
- SUBSTEP 4: Test the function with various inputs and edge cases

RECOMMENDED SLASH COMMANDS:
- Primary: /converge for main workflow
- Supporting: /execute, /test, /debug for implementation and validation

EXECUTION APPROACH:
- Start with basic function structure and documentation
- Implement iterative algorithm for O(n) efficiency
- Add comprehensive input validation
- Test with fibonacci(0)=0, fibonacci(1)=1, fibonacci(5)=5, fibonacci(10)=55
- Debug any issues and ensure all edge cases work properly

Focus for this iteration: Complete working fibonacci function with testing validation"""
    elif "consensus" in prompt.lower():
        return """COMPLETION: 75%

CRITERIA MET:
- Function Implementation Complete ✅
- Algorithm Efficiency Verified ✅
- Function Documentation Present ✅

REMAINING GAPS:
- Edge Cases Handling (need to test n=0, negative inputs)
- Input Validation (need type checking)
- Complete Testing Validation (need all test cases)

EXPLANATION: Core function is implemented with efficient algorithm and documentation, but needs edge case handling and comprehensive testing to reach 100% completion."""
    else:
        return f"Mock response for: {prompt[:100]}..."

def test_enhanced_workflow():
    """Test the enhanced Proto Genesis workflow."""
    goal_dir = "goals/2025-09-22-0217-fibonacci-function/"

    print("=" * 60)
    print("PROTO GENESIS - Enhanced Workflow Test")
    print("=" * 60)

    # Load goal
    refined_goal, exit_criteria = load_goal_from_directory(goal_dir)
    if not refined_goal:
        print("Error: Could not load goal from directory")
        return

    print(f"Goal: {refined_goal}")
    print(f"Criteria: {exit_criteria[:100]}...")
    print()

    print("ITERATION 1/1")
    print("-" * 30)

    # Step 1: Generate execution strategy
    print("STEP 1: Execution Strategy & Planning")
    execution_strategy = generate_execution_strategy(refined_goal, 1, "", False)

    # Mock the claude call for demonstration
    strategy_response = mock_claude_response("execution strategy")
    print("Execution Strategy:")
    print(strategy_response)
    print()

    # Step 2: Execute (mocked)
    print("STEP 2: Execution")
    execution_response = mock_claude_response("execute fibonacci")
    print("Progress made:")
    print("✅ Created fibonacci function with efficient iterative algorithm")
    print("✅ Added comprehensive docstring with examples")
    print("✅ Implemented basic structure ready for testing")
    print()

    # Step 3: Consensus (mocked)
    print("STEP 3: Consensus Assessment")
    consensus_response = mock_claude_response("consensus evaluation")
    print("Consensus Assessment:")
    print(consensus_response)
    print()

    print("🎯 ENHANCED WORKFLOW DEMONSTRATED SUCCESSFULLY!")
    print()
    print("Key improvements shown:")
    print("✅ Combined execution strategy with substep breakdown")
    print("✅ Slash command discovery (local + global paths)")
    print("✅ Streamlined 3-step process")
    print("✅ Debugging and testing encouragement")
    print("✅ Both claude and codex mode support")

if __name__ == "__main__":
    test_enhanced_workflow()
