#!/usr/bin/env python3
"""
Test file to demonstrate and validate JSON parsing issues with markdown formatting.
"""

import json
import re
import sys
import os

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gemini_service import parse_llm_response_for_state_changes

def test_markdown_json_parsing():
    """Test various markdown-wrapped JSON scenarios that might be causing issues."""
    
    print("Testing JSON parsing with various markdown formatting...")
    
    # Test cases that might be problematic
    test_cases = [
        {
            "name": "Standard format (should work)",
            "content": """
[STATE_UPDATES_PROPOSED]
{
  "player_character_data": {
    "hp_current": 75
  }
}
[END_STATE_UPDATES_PROPOSED]
"""
        },
        {
            "name": "Markdown code block (should work)",
            "content": """
[STATE_UPDATES_PROPOSED]
```json
{
  "player_character_data": {
    "hp_current": 75
  }
}
```
[END_STATE_UPDATES_PROPOSED]
"""
        },
        {
            "name": "Bold markdown wrapping (likely broken)",
            "content": """
[STATE_UPDATES_PROPOSED]
**
{
  "player_character_data": {
    "hp_current": 75
  }
}
**
[END_STATE_UPDATES_PROPOSED]
"""
        },
        {
            "name": "Mixed markdown formatting (likely broken)",
            "content": """
[STATE_UPDATES_PROPOSED]
**```json
{
  "player_character_data": {
    "hp_current": 75
  }
}
```**
[END_STATE_UPDATES_PROPOSED]
"""
        },
        {
            "name": "Extra whitespace and asterisks (likely broken)",
            "content": """
[STATE_UPDATES_PROPOSED]
   **
   {
     "player_character_data": {
       "hp_current": 75
     }
   }
   **
[END_STATE_UPDATES_PROPOSED]
"""
        },
        {
            "name": "Nested markdown (likely broken)",
            "content": """
[STATE_UPDATES_PROPOSED]
*Here's the update:*

```json
{
  "player_character_data": {
    "hp_current": 75
  }
}
```

*End of update*
[END_STATE_UPDATES_PROPOSED]
"""
        },
        {
            "name": "HTML-style formatting (likely broken)",
            "content": """
[STATE_UPDATES_PROPOSED]
<strong>
{
  "player_character_data": {
    "hp_current": 75
  }
}
</strong>
[END_STATE_UPDATES_PROPOSED]
"""
        }
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test {i}: {test_case['name']} ---")
        
        try:
            result = parse_llm_response_for_state_changes(test_case['content'])
            
            # Check if we got the expected result
            if result and isinstance(result, dict) and 'player_character_data' in result:
                expected_hp = result.get('player_character_data', {}).get('hp_current')
                if expected_hp == 75:
                    print(f"✅ SUCCESS: Parsed correctly, got hp_current = {expected_hp}")
                    success_count += 1
                else:
                    print(f"❌ PARTIAL: Parsed as dict but hp_current = {expected_hp} (expected 75)")
            else:
                print(f"❌ FAILED: Got {type(result)} with content: {result}")
                
        except Exception as e:
            print(f"❌ ERROR: Exception during parsing: {e}")
    
    print(f"\n=== SUMMARY ===")
    print(f"Passed: {success_count}/{total_count} tests")
    print(f"Success rate: {(success_count/total_count)*100:.1f}%")
    
    if success_count < total_count:
        print(f"❌ {total_count - success_count} tests failed - JSON parsing needs improvement")
        return False
    else:
        print("✅ All tests passed!")
        return True

if __name__ == "__main__":
    test_markdown_json_parsing() 