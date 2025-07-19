#!/usr/bin/env python3
"""
Script to add GeminiResponse mock objects to debug mode tests.
"""


def add_mock_to_line(lines, line_num, mock_response_var):
    """Add mock GeminiResponse creation before the specified line."""
    mock_creation = [
        "        # Create mock GeminiResponse",
        "        mock_gemini_response = MagicMock()",
        f"        mock_gemini_response.narrative_text = {mock_response_var}",
        "        mock_gemini_response.debug_tags_present = {'dm_notes': True, 'dice_rolls': True, 'state_changes': False}",
        "        mock_gemini_response.state_updates = {}",
        "        ",
    ]

    # Insert the mock creation lines before the patch line
    for i, mock_line in enumerate(mock_creation):
        lines.insert(line_num + i, mock_line)

    return len(mock_creation)


# Read the file
file_path = (
    "/home/jleechan/projects/worldarchitect.ai/mvp_site/tests/test_debug_mode.py"
)
with open(file_path) as f:
    lines = f.readlines()

# Find lines that have "with patch('gemini_service.continue_story', return_value=mock_gemini_response):"
# and add mock creation before them
offset = 0
for i, line in enumerate(lines):
    actual_line_num = i + offset
    if (
        "with patch('gemini_service.continue_story', return_value=mock_gemini_response):"
        in line
    ):
        # Find the mock_response variable in the preceding lines
        mock_response_var = "mock_response"  # Default
        for j in range(actual_line_num - 1, max(0, actual_line_num - 20), -1):
            if "mock_response = " in lines[j]:
                break

        # Check if mock creation already exists
        has_mock_creation = False
        for j in range(max(0, actual_line_num - 6), actual_line_num):
            if "mock_gemini_response = MagicMock()" in lines[j]:
                has_mock_creation = True
                break

        if not has_mock_creation:
            added_lines = add_mock_to_line(lines, actual_line_num, mock_response_var)
            offset += added_lines

# Write back
with open(file_path, "w") as f:
    f.writelines(lines)

print(f"Updated {file_path}")
