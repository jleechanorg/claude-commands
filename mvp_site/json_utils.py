"""
Shared JSON parsing utilities for handling incomplete or malformed JSON responses
"""

import json
import re
from typing import Any


def count_unmatched_quotes(text: str) -> int:
    """
    Count unmatched quotes in text, accounting for escape sequences.

    Returns:
        Number of unmatched quotes (odd number indicates we're in a string)
    """
    quote_count = 0
    escape_next = False

    for char in text:
        if escape_next:
            escape_next = False
            continue
        if char == "\\":
            escape_next = True
            continue
        if char == '"' and not escape_next:
            quote_count += 1

    return quote_count


def count_unmatched_braces(text: str) -> tuple[int, int]:
    """
    Count unmatched braces and brackets, accounting for strings.

    Returns:
        tuple: (unmatched_braces, unmatched_brackets)
    """
    brace_count = 0
    bracket_count = 0
    in_string = False
    escape_next = False

    for char in text:
        if escape_next:
            escape_next = False
            continue

        if char == "\\":
            escape_next = True
            continue

        if char == '"' and not escape_next:
            in_string = not in_string
            continue

        if not in_string:
            if char == "{":
                brace_count += 1
            elif char == "}":
                brace_count -= 1
            elif char == "[":
                bracket_count += 1
            elif char == "]":
                bracket_count -= 1

    return (brace_count, bracket_count)


def unescape_json_string(text: str) -> str:
    """
    Unescape common JSON escape sequences.
    """
    # Handle escape sequences properly by processing them character by character
    result = []
    i = 0
    while i < len(text):
        if text[i] == "\\" and i + 1 < len(text):
            next_char = text[i + 1]
            if next_char == "n":
                result.append("\n")
                i += 2
            elif next_char == "t":
                result.append("\t")
                i += 2
            elif next_char == "r":
                result.append("\r")
                i += 2
            elif next_char == "b":
                result.append("\b")
                i += 2
            elif next_char == "f":
                result.append("\f")
                i += 2
            elif next_char == '"':
                result.append('"')
                i += 2
            elif next_char == "/":
                result.append("/")
                i += 2
            elif next_char == "\\":
                result.append("\\")
                i += 2
            else:
                # Unknown escape sequence, keep as is
                result.append(text[i])
                i += 1
        else:
            result.append(text[i])
            i += 1

    return "".join(result)


def try_parse_json(text: str) -> tuple[dict[str, Any] | None, bool]:
    """
    Try to parse JSON text, returning (result, success).
    """
    try:
        return json.loads(text), True
    except json.JSONDecodeError:
        return None, False


def extract_json_boundaries(text: str) -> str | None:
    """
    Extract JSON content between first { and its matching } or [ and its matching ].

    Returns:
        Extracted JSON string if valid boundaries found, original text if incomplete,
        or None if no JSON start marker ({ or [) is found
    """
    start_match = re.search(r"[{\[]", text)
    if not start_match:
        return None

    text = text[start_match.start() :]

    if text.startswith("{"):
        brace_count = 0
        in_string = False
        i = 0

        while i < len(text):
            if in_string and text[i] == "\\" and i + 1 < len(text):
                # Skip escaped character in string
                i += 2
                continue

            if text[i] == '"':
                in_string = not in_string
            elif not in_string:
                if text[i] == "{":
                    brace_count += 1
                elif text[i] == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        return text[: i + 1]

            i += 1
    elif text.startswith("["):
        bracket_count = 0
        in_string = False
        i = 0

        while i < len(text):
            if in_string and text[i] == "\\" and i + 1 < len(text):
                # Skip escaped character in string
                i += 2
                continue

            if text[i] == '"':
                in_string = not in_string
            elif not in_string:
                if text[i] == "[":
                    bracket_count += 1
                elif text[i] == "]":
                    bracket_count -= 1
                    if bracket_count == 0:
                        return text[: i + 1]

            i += 1

    return text


def complete_truncated_json(text: str) -> str:
    """
    Attempt to complete truncated JSON by adding missing quotes and braces.
    """
    if not text.strip():
        return "{}"

    # Ensure it starts with { or [
    if not text.strip().startswith(("{", "[")):
        return text

    completed = text

    # Check for unclosed strings
    quote_count = count_unmatched_quotes(text)
    if quote_count % 2 == 1:
        # Odd number of quotes means we're in a string
        if completed.rstrip().endswith("}"):
            # Insert quote before the closing brace
            completed = completed[:-1] + '"}'
        else:
            completed += '"'

    # Track the nesting order to close properly
    nesting_stack = []
    in_string = False
    i = 0

    while i < len(completed):
        if completed[i] == '"':
            # Check if this quote is escaped
            if i > 0 and completed[i - 1] == "\\":
                # Count preceding backslashes
                num_backslashes = 0
                j = i - 1
                while j >= 0 and completed[j] == "\\":
                    num_backslashes += 1
                    j -= 1

                # If even number of backslashes, the quote is NOT escaped
                if num_backslashes % 2 == 0:
                    in_string = not in_string
            else:
                in_string = not in_string
        elif not in_string:
            if completed[i] == "{":
                nesting_stack.append("}")
            elif completed[i] == "[":
                nesting_stack.append("]")
            elif completed[i] in "}]" and nesting_stack:
                if nesting_stack[-1] == completed[i]:
                    nesting_stack.pop()

        i += 1

    # Close any remaining open brackets/braces in reverse order
    while nesting_stack:
        completed += nesting_stack.pop()

    return completed


def extract_field_value(text: str, field_name: str) -> str | None:
    """
    Extract a specific field value from potentially malformed JSON.

    Args:
        text: The JSON-like text
        field_name: The field to extract

    Returns:
        The extracted value or None
    """
    # Special handling for narrative field - it often contains quotes and can be very long
    if field_name == "narrative":
        # For narrative, we need to handle incomplete JSON where the string might be cut off
        # First try: Look for narrative field and find its proper end
        narrative_start = re.search(rf'"{field_name}"\s*:\s*"', text, re.DOTALL)
        if narrative_start:
            start_pos = narrative_start.end()

            # Find the end of the narrative value by tracking escape sequences
            pos = start_pos
            escaped = False
            while pos < len(text):
                char = text[pos]

                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    # Found the closing quote
                    value = text[start_pos:pos]
                    return unescape_json_string(value)

                pos += 1

            # If we reach here, the JSON is incomplete - return everything from start
            value = text[start_pos:]

            # For incomplete JSON (no closing quote found), we generally don't unescape
            # because we can't be sure the escape sequences are complete
            # However, if there are no trailing backslashes, it's safe to unescape
            has_trailing_backslash = value and value[-1] == "\\"

            if has_trailing_backslash:
                # Don't unescape - preserve raw content for incomplete JSON
                return value
            # No trailing backslash - safe to unescape
            return unescape_json_string(value)

    # For other fields, find the rightmost occurrence to avoid nested fields
    # Use negative lookahead to ensure we're not inside another object
    pattern = rf'"{field_name}"\s*:\s*"((?:[^"\\]|\\.)*)"(?![^{{}}]*\}}[^{{}}]*"{field_name}")'

    # Find all matches and use the last one (rightmost)
    matches = list(re.finditer(pattern, text, re.DOTALL))
    if matches:
        value = matches[-1].group(1)
        # Handle trailing backslash in incomplete strings
        if value.endswith("\\") and len(value) % 2 == 1:
            value = value[:-1]
        return unescape_json_string(value)

    # Fallback for incomplete strings
    incomplete_pattern = rf'"{field_name}"\s*:\s*"([^"]*?)(?=\s*[,}}]|$)'
    match = re.search(incomplete_pattern, text, re.DOTALL)
    if match:
        value = match.group(1)
        # Remove trailing backslash if it's incomplete
        if value.endswith("\\"):
            value = value.rstrip("\\")
        return unescape_json_string(value)

    return None
