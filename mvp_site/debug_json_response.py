"""
Debug utilities for handling incomplete JSON responses from Gemini API
"""

import re

import logging_util
from json_utils import complete_truncated_json, extract_field_value, try_parse_json


def fix_incomplete_json(response_text):
    """
    Attempts to fix incomplete JSON responses from Gemini.

    Args:
        response_text: The potentially incomplete JSON string

    Returns:
        tuple: (fixed_json_dict, was_incomplete)
    """
    if not response_text:
        return None, False

    # First, try to parse as-is
    result, success = try_parse_json(response_text)
    if success:
        return result, False

    # Try to complete truncated JSON
    response_text = response_text.strip()
    completed = complete_truncated_json(response_text)

    # Try to parse the completed JSON
    result, success = try_parse_json(completed)
    if success:
        logging_util.warning("Fixed incomplete JSON response")
        return result, True

    # As a last resort, try to extract just the narrative field
    logging_util.error("Failed to fix incomplete JSON")
    narrative = extract_field_value(response_text, "narrative")
    if narrative:
        return {"narrative": narrative, "_incomplete": True}, True

    return None, True


def validate_json_response(response_dict):
    """
    Validates that a JSON response has the expected structure.

    Args:
        response_dict: The parsed JSON dictionary

    Returns:
        tuple: (is_valid, missing_fields, truncated_fields)
    """
    if not isinstance(response_dict, dict):
        return False, ["not a dictionary"], []

    expected_fields = ["narrative"]  # Add other expected fields as needed
    missing_fields = []
    truncated_fields = []

    for field in expected_fields:
        if field not in response_dict:
            missing_fields.append(field)
        elif isinstance(response_dict[field], str):
            # Check if the field appears truncated
            value = response_dict[field]
            # Common signs of truncation
            if value and not value.rstrip().endswith((".", "!", "?", '"', "---")):
                # Check if it ends mid-sentence
                last_line = value.split("\n")[-1]
                if last_line and not re.match(r"^(---|\d+\.|\*)", last_line):
                    truncated_fields.append(field)

    is_valid = len(missing_fields) == 0
    return is_valid, missing_fields, truncated_fields


def extract_planning_block(narrative_text):
    """
    Extracts the planning block from a narrative, even if JSON was incomplete.

    Args:
        narrative_text: The narrative text that may contain a planning block

    Returns:
        str: The planning block text or None
    """
    # Look for the planning block pattern
    planning_match = re.search(
        r"--- PLANNING BLOCK ---\s*(.*?)$", narrative_text, re.DOTALL | re.IGNORECASE
    )

    if planning_match:
        return planning_match.group(1).strip()

    return None


# Example usage:
if __name__ == "__main__":
    # Test with your incomplete JSON
    incomplete_json = """{"narrative": "[SESSION_HEADER]\\nTimestamp: Year 1620, Kythorn, Day 10, 02:05 PM\\nLocation: The Eastern March, on the road to the Dragon's Tooth mountains.\\nStatus: Lvl 1 Fighter/Paladin | HP: 12/12 | Gold: 25gp\\nResources:\\n- Hero Points: 1/1\\n\\nSir Andrew ignored Gareth's probing question, his focus narrowing back to the mission. He folded the map with crisp, efficient movements and tucked it away. His duty was clear; the feelings of his companions were secondary variables. He turned to the other two members of his small company, his expression a mask of command.\\n\\n\\"Report,\\" he said, his voice flat and devoid of warmth. He looked first to Kiera Varrus, the scout, whose cynical eyes were already scanning the treacherous path ahead.\\n\\nKiera spat on the ground, pulling her leather hood tighter against the wind. \\"It's a goat track at best, Sir Knight. Not a proper road. The ground is loose shale, easy to turn an ankle or alert anything hiding in the rocks.\\" She squinted at the mountains."""

    fixed_json, was_incomplete = fix_incomplete_json(incomplete_json)
    logging_util.info(
        f"JSON fix result - incomplete: {was_incomplete}, success: {fixed_json is not None}"
    )

    if fixed_json:
        is_valid, missing, truncated = validate_json_response(fixed_json)
        logging_util.info(
            f"JSON validation - valid: {is_valid}, missing fields: {len(missing)}, truncated: {truncated}"
        )
