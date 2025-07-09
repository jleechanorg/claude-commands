#!/usr/bin/env python3
"""
Quick verification of structured fields implementation status.
Checks both frontend and backend to identify what's implemented vs what's missing.
"""

import os
import re

def check_frontend():
    print("=== FRONTEND IMPLEMENTATION CHECK ===")
    
    app_js_path = "mvp_site/static/app.js"
    with open(app_js_path, 'r') as f:
        content = f.read()
    
    # Check for key functions
    print("\n1. Function signatures:")
    if "appendToStory = (actor, text, mode = null, debugMode = false, sequenceId = null, fullData = null)" in content:
        print("✓ appendToStory has fullData parameter")
    else:
        print("✗ appendToStory missing fullData parameter")
    
    if "generateStructuredFieldsHTML" in content:
        print("✓ generateStructuredFieldsHTML function exists")
    else:
        print("✗ generateStructuredFieldsHTML function missing")
    
    # Check field access patterns
    print("\n2. Field access patterns in generateStructuredFieldsHTML:")
    patterns = {
        "fullData.dice_rolls": "Looking for dice_rolls at TOP LEVEL",
        "fullData.debug_info.dice_rolls": "Looking for dice_rolls in DEBUG_INFO",
        "fullData.resources": "Looking for resources at TOP LEVEL", 
        "fullData.debug_info.resources": "Looking for resources in DEBUG_INFO"
    }
    
    for pattern, desc in patterns.items():
        if pattern in content:
            print(f"✓ {desc}")
        else:
            print(f"✗ {desc}")
    
    # Check where appendToStory is called with data
    print("\n3. API response handling:")
    if re.search(r"appendToStory\('gemini'.*?, data\)", content):
        print("✓ appendToStory is called with full data object")
    else:
        print("✗ appendToStory not receiving full data object")

def check_backend():
    print("\n\n=== BACKEND IMPLEMENTATION CHECK ===")
    
    main_py_path = "mvp_site/main.py"
    with open(main_py_path, 'r') as f:
        content = f.read()
    
    print("\n1. Structured response handling:")
    patterns = {
        "structured_response": "Uses structured_response object",
        "debug_info": "Builds debug_info dict",
        "dice_rolls": "Handles dice_rolls field",
        "resources": "Handles resources field"
    }
    
    for pattern, desc in patterns.items():
        if pattern in content:
            print(f"✓ {desc}")
        else:
            print(f"✗ {desc}")

def check_schema():
    print("\n\n=== SCHEMA CHECK ===")
    
    schema_path = "mvp_site/prompts/game_state_instruction.md"
    if os.path.exists(schema_path):
        print("✓ Schema file exists")
        with open(schema_path, 'r') as f:
            content = f.read()
            if "dice_rolls" in content and "debug_info" in content:
                print("✓ Schema defines dice_rolls within debug_info structure")
    else:
        print("✗ Schema file not found")

def main():
    print("Structured Fields Implementation Status Check")
    print("=" * 50)
    
    check_frontend()
    check_backend()
    check_schema()
    
    print("\n\n=== SUMMARY ===")
    print("The implementation appears to have a mismatch:")
    print("- Backend likely sends fields nested in debug_info (per schema)")
    print("- Frontend looks for fields at top level (incorrect)")
    print("- This needs to be fixed in generateStructuredFieldsHTML function")

if __name__ == "__main__":
    main()