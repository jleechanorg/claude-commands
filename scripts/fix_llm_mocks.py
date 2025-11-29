#!/usr/bin/env python3
"""
Script to fix all gemini service mocks to return LLMResponse objects instead of tuples.
"""

import os
import re


def fix_file_mocks(file_path):
    """Fix gemini service mocks in a single file."""
    print(f"Fixing {file_path}...")

    with open(file_path) as f:
        content = f.read()

    # Pattern to match: return_value=(something, None)
    tuple_pattern = r"return_value=\(([^,]+),\s*None\)"

    def replace_tuple_mock(match):
        ai_response_var = match.group(1)
        return f"""return_value=mock_llm_response)

        # Create mock LLMResponse object before the patch
        mock_llm_response = MagicMock()
        mock_llm_response.narrative_text = {ai_response_var}
        mock_llm_response.debug_tags_present = {{'dm_notes': True, 'dice_rolls': True, 'state_changes': True}}
        mock_llm_response.state_updates = {{}}

        with patch('llm_service.continue_story', """

    # Replace the patterns
    new_content = re.sub(tuple_pattern, replace_tuple_mock, content)

    # Fix any issues with the replacement
    new_content = new_content.replace(
        "with patch('llm_service.continue_story', return_value=mock_gemini_response)\n        \n        # Create mock LLMResponse",
        "# Create mock LLMResponse object\n        mock_llm_response = MagicMock()\n        mock_llm_response.narrative_text = ai_response\n        mock_llm_response.debug_tags_present = {'dm_notes': True, 'dice_rolls': True, 'state_changes': True}\n        mock_llm_response.state_updates = {}\n        \n        with patch('llm_service.continue_story', return_value=mock_llm_response",
    )

    # Write back
    with open(file_path, "w") as f:
        f.write(new_content)

    print(f"Fixed {file_path}")


# List of files that need fixing
files_to_fix = [
    "/home/jleechan/projects/worldarchitect.ai/mvp_site/tests/test_debug_mode.py",
    "/home/jleechan/projects/worldarchitect.ai/mvp_site/tests/test_debug_mode_e2e.py",
]

for file_path in files_to_fix:
    if os.path.exists(file_path):
        fix_file_mocks(file_path)
    else:
        print(f"File not found: {file_path}")

print("Done!")
