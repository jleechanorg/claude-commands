#!/usr/bin/env python3
"""Test that character creation uses clean formatting without DM notes."""

import os
import sys
# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


import logging_util
from gemini_service import get_initial_story

def test_clean_character_creation_format():
    """Test that character creation responses don't include DM notes or debug blocks."""
    # Set up environment
    os.environ['TESTING'] = 'true'
    logging_util.basicConfig(level=logging_util.INFO)
    
    print("\n=== Testing Clean Character Creation Formatting ===\n")
    
    # Initial prompt with mechanics enabled
    user_prompt = "I want to be a warrior"
    selected_prompts = ['mechanics']
    
    print(f"User prompt: {user_prompt}")
    print(f"Selected prompts: {selected_prompts}\n")
    
    try:
        # Get initial response
        response = get_initial_story(user_prompt, selected_prompts=selected_prompts)
        
        print("AI Response:")
        print(response)
        print("\n" + "="*50 + "\n")
        
        # Check for clean formatting
        formatting_issues = []
        
        if "DM Notes:" in response or "DM MODE" in response:
            formatting_issues.append("Response contains DM notes")
            
        if "[DEBUG" in response:
            formatting_issues.append("Response contains debug blocks")
            
        if "🔧 STATE UPDATES" in response:
            formatting_issues.append("Response contains state update blocks")
            
        # Check for expected clean format elements
        has_options = ("1." in response and "2." in response and "3." in response)
        has_question = "?" in response
        
        if formatting_issues:
            print("❌ FORMATTING ISSUES FOUND:")
            for issue in formatting_issues:
                print(f"   - {issue}")
        else:
            print("✅ CLEAN FORMATTING: No DM notes or debug blocks found")
            
        if has_options and has_question:
            print("✅ PROPER STRUCTURE: Options and question presented clearly")
        else:
            print("⚠️  STRUCTURE: May be missing clear options or question")
            
        # Additional check for character creation format
        if "[CHARACTER CREATION" in response:
            print("✅ USING RECOMMENDED FORMAT: [CHARACTER CREATION] header found")
        else:
            print("ℹ️  FORMAT: Not using [CHARACTER CREATION] header format")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_clean_character_creation_format()