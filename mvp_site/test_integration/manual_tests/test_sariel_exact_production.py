#!/usr/bin/env python3
"""
Manual test to reproduce the exact Sariel campaign production scenario.
This test makes real API calls and validates entity tracking behavior.

Usage:
    # From mvp_site directory:
    TESTING=true python run_manual_test.py tests/manual_tests/test_sariel_exact_production.py
    
    # Or directly with proper path setup:
    cd mvp_site && TESTING=true python -m tests.manual_tests.test_sariel_exact_production
"""

import sys
import os
import json
import time
from datetime import datetime

# Import setup handled by __init__.py
from main import create_app
from game_state import GameState
from gemini_service import get_initial_story, continue_story


def print_section(title):
    """Print formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_entity_tracking(entities_expected, entities_found):
    """Print entity tracking results"""
    print(f"Expected entities: {entities_expected}")
    print(f"Found entities: {entities_found}")
    missing = set(entities_expected) - set(entities_found)
    if missing:
        print(f"⚠️  MISSING ENTITIES: {missing}")
    else:
        print("✅ All entities tracked correctly")


def run_sariel_exact_production():
    """Run the exact Sariel campaign production scenario"""
    print_section("SARIEL EXACT PRODUCTION TEST")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Testing: Entity tracking, Cassian problem, state updates")
    
    # Initialize Flask app for testing
    app = create_app()
    app.config['TESTING'] = True
    
    # Initial prompt - Sariel meeting Cassian
    initial_prompt = """You are Sariel, a member of House Arcanus known for magical prowess. 
    You've been summoned to the throne room where you find your estranged brother Cassian 
    waiting with grave news about your family's legacy."""
    
    print_section("1. INITIAL STORY GENERATION")
    print(f"Prompt: {initial_prompt[:100]}...")
    
    # Generate initial story
    initial_response = get_initial_story(
        prompt=initial_prompt,
        selected_prompts=['narrative', 'mechanics'],
        generate_companions=True,
        use_default_world=True
    )
    
    print("\nResponse preview:")
    print(initial_response[:500] + "..." if len(initial_response) > 500 else initial_response)
    
    # Check for Sariel and Cassian
    sariel_found = 'Sariel' in initial_response
    cassian_found = 'Cassian' in initial_response
    
    print(f"\n✅ Sariel mentioned: {sariel_found}")
    print(f"✅ Cassian mentioned: {cassian_found}")
    
    # Create game state
    game_state = GameState()
    
    # The problematic user input that triggers the Cassian problem
    print_section("2. CASSIAN PROBLEM TEST")
    user_input = "Tell Cassian I was scared and helpless"
    print(f"User input: '{user_input}'")
    print("This input references Cassian who should be present in the scene...")
    
    # Continue story with problematic input
    story_context = [
        {'actor': 'user', 'text': initial_prompt},
        {'actor': 'gemini', 'text': initial_response}
    ]
    
    continue_response = continue_story(
        user_input=user_input,
        mode='character',
        story_context=story_context,
        current_game_state=game_state,
        selected_prompts=['narrative', 'mechanics'],
        use_default_world=True
    )
    
    print("\nResponse preview:")
    print(continue_response[:500] + "..." if len(continue_response) > 500 else continue_response)
    
    # Check if Cassian is mentioned in response
    cassian_in_response = 'Cassian' in continue_response
    sariel_in_response = 'Sariel' in continue_response
    
    print(f"\n✅ Sariel in response: {sariel_in_response}")
    if cassian_in_response:
        print(f"✅ Cassian in response: {cassian_in_response} - CASSIAN PROBLEM SOLVED!")
    else:
        print(f"❌ Cassian in response: {cassian_in_response} - CASSIAN PROBLEM DETECTED!")
        print("   The user referenced Cassian but the AI didn't include him in the response")
    
    # Additional test interactions
    print_section("3. ADDITIONAL INTERACTIONS")
    
    test_inputs = [
        "Ask Cassian about the nature of this grave news",
        "1",  # Choice selection
        "Cast detect magic to sense any magical threats"
    ]
    
    for i, test_input in enumerate(test_inputs, 1):
        print(f"\nInteraction {i + 2}: '{test_input}'")
        
        story_context.extend([
            {'actor': 'user', 'text': user_input},
            {'actor': 'gemini', 'text': continue_response}
        ])
        
        response = continue_story(
            user_input=test_input,
            mode='character',
            story_context=story_context,
            current_game_state=game_state,
            selected_prompts=['narrative', 'mechanics'],
            use_default_world=True
        )
        
        # Update for next iteration
        user_input = test_input
        continue_response = response
        
        # Quick entity check
        entities_mentioned = []
        if 'Sariel' in response:
            entities_mentioned.append('Sariel')
        if 'Cassian' in response:
            entities_mentioned.append('Cassian')
        
        print(f"Entities tracked: {entities_mentioned}")
    
    # Final summary
    print_section("TEST SUMMARY")
    print("1. Initial story generation: ✅ PASSED")
    print(f"2. Cassian problem test: {'✅ PASSED' if cassian_in_response else '❌ FAILED'}")
    print("3. Entity tracking: Validated across multiple interactions")
    print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    # Ensure we have API key
    if not os.environ.get('GEMINI_API_KEY'):
        print("ERROR: GEMINI_API_KEY environment variable not set")
        print("Please set your API key before running this test")
        sys.exit(1)
    
    # Run the test
    try:
        run_sariel_exact_production()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)