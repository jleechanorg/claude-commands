#!/usr/bin/env python3
"""
Test PR detection patterns in the orchestration system.
Tests that various phrasings correctly trigger UPDATE vs CREATE mode.
"""

import sys
import os

# Add orchestration directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from task_dispatcher import TaskDispatcher


def test_pr_detection_patterns():
    """Test various PR detection patterns."""
    dispatcher = TaskDispatcher()
    
    # Test cases: (task_description, expected_mode, description)
    test_cases = [
        # UPDATE mode patterns - explicit PR number
        ("fix PR #123", "update", "Explicit PR number with fix"),
        ("adjust pull request #456", "update", "Explicit PR with adjust"),
        ("update PR #789", "update", "Explicit PR with update"),
        ("PR #100 needs better error handling", "update", "PR number at start"),
        ("add logging to PR #200", "update", "Add something to PR"),
        
        # UPDATE mode patterns - contextual references
        ("adjust the PR", "update", "Contextual PR with adjust"),
        ("fix that pull request", "update", "Contextual PR with fix"),
        ("the PR needs more tests", "update", "The PR needs pattern"),
        ("continue with the PR", "update", "Continue with PR"),
        ("update the existing PR", "update", "Existing PR reference"),
        
        # CREATE mode patterns - no PR mentioned
        ("implement user authentication", "create", "Feature without PR"),
        ("fix the login bug", "create", "Bug fix without PR"),
        ("create new feature for exports", "create", "New feature task"),
        ("add dark mode support", "create", "Enhancement without PR"),
        
        # CREATE mode patterns - explicit new PR
        ("create new PR for refactoring", "create", "Explicit new PR"),
        ("start fresh pull request for API", "create", "Fresh PR request"),
    ]
    
    print("Testing PR Detection Patterns")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for task, expected_mode, description in test_cases:
        pr_number, detected_mode = dispatcher._detect_pr_context(task)
        
        if detected_mode == expected_mode:
            print(f"✅ PASS: {description}")
            print(f"   Task: '{task}'")
            print(f"   Mode: {detected_mode} {'(PR #' + pr_number + ')' if pr_number else ''}")
            passed += 1
        else:
            print(f"❌ FAIL: {description}")
            print(f"   Task: '{task}'")
            print(f"   Expected: {expected_mode}, Got: {detected_mode}")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print(f"Success rate: {(passed/(passed+failed)*100):.1f}%")
    
    return failed == 0


def test_agent_prompt_generation():
    """Test that agent prompts are correctly generated for each mode."""
    dispatcher = TaskDispatcher()
    
    print("\n\nTesting Agent Prompt Generation")
    print("=" * 60)
    
    # Test UPDATE mode with PR number
    print("\n1. UPDATE mode with PR number:")
    agents = dispatcher.analyze_task_and_create_agents("fix the typo in PR #950")
    agent = agents[0]
    pr_context = agent.get('pr_context', None)
    if pr_context:
        print(f"Mode detected: {pr_context.get('mode', 'none')}")
        print(f"PR number: {pr_context.get('pr_number', 'none')}")
    else:
        print(f"PR context: None (indicates CREATE mode)")
    print(f"Prompt includes UPDATE instructions: {'UPDATE MODE' in agent['prompt']}")
    print(f"Prompt includes checkout command: {'gh pr checkout' in agent['prompt']}")
    
    # Test CREATE mode
    print("\n2. CREATE mode:")
    agents = dispatcher.analyze_task_and_create_agents("implement new caching system")
    agent = agents[0]
    pr_context = agent.get('pr_context', None)
    print(f"PR context: {pr_context or 'None (CREATE mode)'}")
    print(f"Prompt includes CREATE instructions: {'NEW PR MODE' in agent['prompt']}")
    print(f"Prompt includes new branch instruction: {'new branch from main' in agent['prompt']}")
    
    # Test UPDATE mode without PR number
    print("\n3. UPDATE mode without PR number (ambiguous):")
    agents = dispatcher.analyze_task_and_create_agents("fix the issues in the PR")
    agent = agents[0]
    pr_context = agent.get('pr_context', None)
    if pr_context:
        print(f"Mode detected: {pr_context.get('mode', 'none')}")
        print(f"PR number: {pr_context.get('pr_number', 'none')}")
    else:
        print(f"PR context: None")
    print(f"Prompt includes clarification request: {'Which PR should I update?' in agent['prompt']}")


if __name__ == "__main__":
    success = test_pr_detection_patterns()
    test_agent_prompt_generation()
    
    sys.exit(0 if success else 1)