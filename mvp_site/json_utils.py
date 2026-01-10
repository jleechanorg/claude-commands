"""
Unified JSON parsing utilities for handling incomplete or malformed JSON responses.

This module provides both low-level utilities and high-level robust parsing for LLM outputs.
"""

import json
import re
from typing import Any, Optional

from mvp_site import constants, logging_util

# Constants for content logging thresholds
CONTENT_LENGTH_THRESHOLD = 1000  # Max characters to log for debug content

# Precompiled regex patterns for field extraction from malformed JSON
ENTITIES_MENTIONED_PATTERN = re.compile(
    r'"entities_mentioned"\s*:\s*\[(.*?)\]', re.DOTALL
)
ENTITY_STRING_PATTERN = re.compile(r'"([^"]+)"')
STATE_UPDATES_PATTERN = re.compile(r'"state_updates"\s*:\s*(\{.*?\})', re.DOTALL)
DEBUG_INFO_PATTERN = re.compile(r'"debug_info"\s*:\s*(\{.*?\})', re.DOTALL)
TEXT_CONTENT_PATTERN = re.compile(r':\s*"([^"]+)')
# Pattern to find start of planning_block (bracket-aware extraction handles the rest)
PLANNING_BLOCK_START_PATTERN = re.compile(r'"planning_block"\s*:\s*\{')


def extract_nested_object(text: str, field_name: str) -> Optional[str]:
    """Extract a nested JSON object using bracket-aware parsing.

    This handles nested braces correctly, unlike simple regex patterns that
    truncate on the first closing brace.

    Args:
        text: The JSON text to search
        field_name: The field name to extract (e.g., "planning_block")

    Returns:
        The extracted object as a string, or None if not found
    """
    # Find the start of the field
    pattern = re.compile(rf'"{field_name}"\s*:\s*\{{')
    match = pattern.search(text)
    if not match:
        return None

    # Start from the opening brace
    start_idx = match.end() - 1  # -1 to include the opening brace
    brace_count = 0
    in_string = False
    escape_next = False

    for i, char in enumerate(text[start_idx:], start=start_idx):
        if escape_next:
            escape_next = False
            continue

        if char == "\\":
            escape_next = True
            continue

        if char == '"' and not escape_next:
            in_string = not in_string
            continue

        if in_string:
            continue

        if char == "{":
            brace_count += 1
        elif char == "}":
            brace_count -= 1
            if brace_count == 0:
                # Found the matching closing brace
                return text[start_idx : i + 1]

    # If we get here, braces were unbalanced - return what we found
    return None


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


def try_parse_json(text: str) -> tuple[Optional[dict[str, Any]], bool]:
    """
    Try to parse JSON text, returning (result, success).
    """
    try:
        return json.loads(text), True
    except json.JSONDecodeError:
        return None, False


def extract_json_boundaries(text: str) -> Optional[str]:  # noqa: PLR0912
    """
    Extract JSON content between first { and its matching } or [ and its matching ].

    Returns:
        Extracted JSON string if valid boundaries found, original text if incomplete,
        or None if no JSON start marker ({ or [) is found
    """
    # Strip common LLM-generated prefixes like [Mode: STORY MODE] before JSON
    # Match pattern: [word: text] followed by whitespace and JSON start
    prefix_pattern = r'^\s*\[[A-Za-z]+:.*?\]\s*'
    text = re.sub(prefix_pattern, '', text)

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


def complete_truncated_json(text: str) -> str:  # noqa: PLR0912
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
            elif (
                completed[i] in "}]"
                and nesting_stack
                and nesting_stack[-1] == completed[i]
            ):
                nesting_stack.pop()

        i += 1

    # Close any remaining open brackets/braces in reverse order
    while nesting_stack:
        completed += nesting_stack.pop()

    return completed


MAX_QUOTE_TERMINATOR_LOOKAHEAD = 256


def _scan_non_whitespace(text: str, start: int, max_distance: int) -> Optional[int]:
    # Cap lookahead to avoid repeated scans across very long narrative strings.
    if start >= len(text):
        return len(text)

    limit = min(len(text), start + max_distance)
    index = start
    while index < limit and text[index].isspace():
        index += 1

    if index >= len(text):
        return len(text)
    if index >= limit:
        return None

    return index


def _is_quote_terminator(text: str, quote_pos: int) -> bool:  # noqa: PLR0911
    # Lookahead validation: only treat as closing quote if followed by JSON structure.
    if quote_pos + 1 >= len(text):
        return True

    lookahead = _scan_non_whitespace(
        text, quote_pos + 1, MAX_QUOTE_TERMINATOR_LOOKAHEAD
    )
    if lookahead is None:
        return False
    if lookahead >= len(text):
        return True
    if text[lookahead] in ["}", "]"]:
        return True
    if text[lookahead] == ",":
        next_token = _scan_non_whitespace(
            text, lookahead + 1, MAX_QUOTE_TERMINATOR_LOOKAHEAD
        )
        if next_token is None:
            return False
        if next_token >= len(text):
            return True
        if text[next_token] in ['"', "}", "]"]:
            return True

    return False


def extract_field_value(text: str, field_name: str) -> Optional[str]:
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
                elif char == '"' and _is_quote_terminator(text, pos):
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


class RobustJSONParser:
    """
    A robust parser that can handle various forms of incomplete JSON responses.
    Designed specifically for LLM outputs that might be truncated or malformed.
    """

    @staticmethod
    def _normalize_to_dict(result: Any, _original_text: str) -> Optional[dict[str, Any]]:
        """
        Normalize parser result to always return a dict or None.

        json.loads() can return any JSON type (dict, list, str, int, etc.),
        but this parser's contract is to always return dict | None.

        Args:
            result: The raw result from json.loads()
            original_text: The original text for fallback extraction

        Returns:
            A dict or None, never a list or primitive type
        """
        if result is None:
            return None

        if isinstance(result, dict):
            return result

        if isinstance(result, list):
            # If list contains a dict, extract first element
            if result and isinstance(result[0], dict):
                logging_util.debug(
                    "Normalized list to dict by extracting first element"
                )
                return result[0]
            # Otherwise, return None to trigger fallback strategies
            logging_util.debug(
                "List result cannot be normalized to dict, returning None"
            )
            return None

        # For primitives (str, int, bool, etc.), return None
        logging_util.debug(
            f"Primitive result type {type(result).__name__} cannot be normalized, returning None"
        )
        return None

    @staticmethod
    def parse(text: str) -> tuple[Optional[dict[str, Any]], bool]:  # noqa: PLR0911, PLR0912, PLR0915
        """
        Attempts to parse JSON text with multiple fallback strategies.

        Args:
            text: The potentially incomplete JSON string

        Returns:
            tuple: (parsed_dict or None, was_incomplete)
        """
        if not text or not text.strip():
            return None, False

        text = text.strip()

        # Strategy 1: Try standard JSON parsing first
        result, success = try_parse_json(text)
        if success:
            normalized = RobustJSONParser._normalize_to_dict(result, text)
            if normalized is not None:
                return normalized, False
            # If normalization failed (e.g., list result), continue to other strategies

        # Strategy 2: Find JSON boundaries and fix common issues
        try:
            fixed_json = RobustJSONParser._fix_json_boundaries(text)
            if fixed_json != text:
                result = json.loads(fixed_json)
                normalized = RobustJSONParser._normalize_to_dict(result, text)
                # If we got a non-dict but the text seems to contain object fields, continue
                if normalized is None and (
                    '"narrative"' in text or '"entities_mentioned"' in text
                ):
                    logging_util.debug(
                        "Got non-dict but text contains object fields, continuing..."
                    )
                elif normalized is not None:
                    logging_util.info("Successfully fixed JSON boundaries")
                    return normalized, True
        except json.JSONDecodeError:
            pass
        except (ValueError, KeyError, TypeError) as e:
            logging_util.debug(f"JSON boundary fix failed: {e}")

        # Strategy 3: Try to complete incomplete JSON
        try:
            completed_json = RobustJSONParser._complete_json(text)
            result = json.loads(completed_json)
            normalized = RobustJSONParser._normalize_to_dict(result, text)
            if normalized is not None:
                logging_util.info("Successfully completed incomplete JSON")
                return normalized, True
        except json.JSONDecodeError:
            pass
        except (ValueError, KeyError, TypeError) as e:
            logging_util.debug(f"JSON completion failed: {e}")

        # Strategy 4: Extract fields individually using regex
        try:
            # Log the malformed JSON content for debugging
            logging_util.warning(
                "MALFORMED_JSON_DETECTED: Attempting field extraction from malformed JSON"
            )
            logging_util.debug(f"MALFORMED_JSON_CONTENT: Length: {len(text)} chars")

            # Log sample of malformed content (safely truncated)
            if len(text) <= CONTENT_LENGTH_THRESHOLD:
                logging_util.debug(f"MALFORMED_JSON_CONTENT: {text}")
            else:
                half_threshold = CONTENT_LENGTH_THRESHOLD // 2
                start_content = text[:half_threshold]
                end_content = text[-half_threshold:]
                logging_util.debug(
                    f"MALFORMED_JSON_CONTENT: {start_content}...[{len(text) - CONTENT_LENGTH_THRESHOLD} chars omitted]...{end_content}"
                )

            extracted = RobustJSONParser._extract_fields(text)
            if extracted:
                logging_util.info("Successfully extracted fields from malformed JSON")
                logging_util.info(f"EXTRACTED_FIELDS: {list(extracted.keys())}")
                return extracted, True
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            logging_util.debug(f"Field extraction failed: {e}")

        # Strategy 5: Last resort - try to fix and parse again
        try:
            aggressively_fixed = RobustJSONParser._aggressive_fix(text)
            if aggressively_fixed and aggressively_fixed != "{}":
                result = json.loads(aggressively_fixed)
                normalized = RobustJSONParser._normalize_to_dict(result, text)
                if normalized is not None:
                    logging_util.info("Successfully parsed with aggressive fixes")
                    return normalized, True
        except json.JSONDecodeError:
            pass
        except (ValueError, KeyError, TypeError) as e:
            logging_util.debug(f"Aggressive fix failed: {e}")

        logging_util.error("All JSON parsing strategies failed")
        return None, True

    @staticmethod
    def _fix_json_boundaries(text: str) -> str:
        """Fix common JSON boundary issues"""
        extracted = extract_json_boundaries(text)
        return extracted if extracted else text

    @staticmethod
    def _complete_json(text: str) -> str:
        """Attempt to complete incomplete JSON"""
        return complete_truncated_json(text)

    @staticmethod
    def _extract_fields(text: str) -> Optional[dict[str, Any]]:
        """Extract individual fields using regex"""
        result = {}

        # Extract narrative field
        narrative = extract_field_value(text, "narrative")
        if narrative is not None:
            result["narrative"] = narrative

        # Extract entities_mentioned array
        entities_match = ENTITIES_MENTIONED_PATTERN.search(text)
        if entities_match:
            entities_str = entities_match.group(1)
            # Parse entity list
            entities = []
            for match in ENTITY_STRING_PATTERN.finditer(entities_str):
                entities.append(match.group(1))
            result["entities_mentioned"] = entities

        # Extract location_confirmed
        location = extract_field_value(text, "location_confirmed")
        if location is not None:
            result["location_confirmed"] = location

        # Extract god_mode_response field (critical for god mode commands)
        god_mode_response = extract_field_value(text, constants.FIELD_GOD_MODE_RESPONSE)
        if god_mode_response is not None:
            result[constants.FIELD_GOD_MODE_RESPONSE] = god_mode_response

        # Extract state_updates object (try to preserve state changes)
        state_updates_match = STATE_UPDATES_PATTERN.search(text)
        if state_updates_match:
            try:
                state_updates_str = state_updates_match.group(1)
                state_updates = json.loads(state_updates_str)
                result["state_updates"] = state_updates
            except json.JSONDecodeError:
                # If the object is malformed, just set empty dict
                result["state_updates"] = {}

        # Extract debug_info object (try to preserve debug information)
        debug_info_match = DEBUG_INFO_PATTERN.search(text)
        if debug_info_match:
            try:
                debug_info_str = debug_info_match.group(1)
                debug_info = json.loads(debug_info_str)
                result["debug_info"] = debug_info
            except json.JSONDecodeError:
                # If the object is malformed, just set empty dict
                result["debug_info"] = {}

        # Extract session_header field (bead 21f fix - Cerebras tool-loop missing headers)
        session_header = extract_field_value(text, constants.FIELD_SESSION_HEADER)
        if session_header is not None:
            result[constants.FIELD_SESSION_HEADER] = session_header

        # Extract planning_block object using bracket-aware parsing
        # (bead 21f fix - shallow regex truncated nested braces)
        planning_block_str = extract_nested_object(text, constants.FIELD_PLANNING_BLOCK)
        if planning_block_str:
            try:
                planning_block = json.loads(planning_block_str)
                result[constants.FIELD_PLANNING_BLOCK] = planning_block
            except json.JSONDecodeError:
                # If the object is malformed, just set empty dict
                result[constants.FIELD_PLANNING_BLOCK] = {}

        return result if result else None

    @staticmethod
    def _aggressive_fix(text: str) -> str:
        """Aggressively fix JSON by rebuilding it from extracted parts"""
        extracted = RobustJSONParser._extract_fields(text)
        if not extracted:
            # If we can't extract anything, try to at least get some text
            # Look for any substantial text content
            text_match = TEXT_CONTENT_PATTERN.search(text)
            if text_match:
                extracted = {"narrative": text_match.group(1)}
            else:
                return "{}"

        # Rebuild clean JSON
        return json.dumps(extracted)


def parse_llm_json_response(response_text: str) -> tuple[dict[str, Any], bool]:
    """
    Parse potentially incomplete JSON response from LLM.

    Args:
        response_text: Raw response from LLM that should be JSON

    Returns:
        tuple: (parsed_dict, was_incomplete)
    """
    parser = RobustJSONParser()
    result, was_incomplete = parser.parse(response_text)

    if result is None:
        # If no JSON could be parsed, treat the entire text as narrative
        logging_util.info("No JSON found in response, treating as plain text narrative")
        return {
            "narrative": response_text.strip(),
            "entities_mentioned": [],
            "location_confirmed": "Unknown",
        }, True

    # Ensure required fields exist
    if "narrative" not in result:
        result["narrative"] = ""
    if "entities_mentioned" not in result:
        result["entities_mentioned"] = []
    if "location_confirmed" not in result:
        result["location_confirmed"] = "Unknown"

    return result, was_incomplete
