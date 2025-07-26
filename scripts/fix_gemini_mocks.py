#!/usr/bin/env python3
"""
Script to fix all gemini service mocks to return GeminiResponse objects instead of tuples.
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
        return f"""return_value=mock_gemini_response)

        # Create mock GeminiResponse object before the patch
        mock_gemini_response = MagicMock()
        mock_gemini_response.narrative_text = {ai_response_var}
        mock_gemini_response.debug_tags_present = {{'dm_notes': True, 'dice_rolls': True, 'state_changes': True}}
        mock_gemini_response.state_updates = {{}}

        with patch('gemini_service.continue_story', """

    # Replace the patterns
    new_content = re.sub(tuple_pattern, replace_tuple_mock, content)

    # Fix any issues with the replacement
    new_content = new_content.replace(
        "with patch('gemini_service.continue_story', return_value=mock_gemini_response)\n        \n        # Create mock GeminiResponse",
        "# Create mock GeminiResponse object\n        mock_gemini_response = MagicMock()\n        mock_gemini_response.narrative_text = ai_response\n        mock_gemini_response.debug_tags_present = {'dm_notes': True, 'dice_rolls': True, 'state_changes': True}\n        mock_gemini_response.state_updates = {}\n        \n        with patch('gemini_service.continue_story', return_value=mock_gemini_response",
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
