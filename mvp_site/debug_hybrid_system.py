"""
Hybrid debug content system for backward compatibility.

This module provides functions to handle both old campaigns with embedded debug tags
and new campaigns with structured debug_info fields.
"""

from __future__ import annotations

import json
import re
from typing import Any

from mvp_site import logging_util


def _extract_nested_object(text: str, field_name: str) -> str | None:
    """Extract a nested JSON object using bracket-aware parsing.

    This handles nested braces correctly, unlike simple regex patterns that truncate
    on the first closing brace.
    """
    pattern = re.compile(rf'"{re.escape(field_name)}"\s*:\s*\{{')
    match = pattern.search(text)
    if not match:
        return None

    start_idx = match.end() - 1  # include the opening brace
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

        if char == '"':
            in_string = not in_string
            continue

        if in_string:
            continue

        if char == "{":
            brace_count += 1
        elif char == "}":
            brace_count -= 1
            if brace_count == 0:
                return text[start_idx : i + 1]

    return None


def _unescape_json_string(text: str) -> str:
    """Unescape common JSON escape sequences, including unicode escapes."""
    if not text:
        return text

    # Prefer JSON string decoding when possible (handles \uXXXX and surrogate pairs).
    try:
        return json.loads(f'"{text}"')
    except Exception:
        pass

    result: list[str] = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch != "\\" or i + 1 >= len(text):
            result.append(ch)
            i += 1
            continue

        nxt = text[i + 1]
        if nxt == "n":
            result.append("\n")
            i += 2
        elif nxt == "t":
            result.append("\t")
            i += 2
        elif nxt == "r":
            result.append("\r")
            i += 2
        elif nxt == "b":
            result.append("\b")
            i += 2
        elif nxt == "f":
            result.append("\f")
            i += 2
        elif nxt in {'"', "/", "\\"}:
            result.append(nxt)
            i += 2
        elif nxt == "u" and i + 5 < len(text):
            hex_part = text[i + 2 : i + 6]
            try:
                codepoint = int(hex_part, 16)
                i += 6
                # Handle surrogate pairs when present.
                if 0xD800 <= codepoint <= 0xDBFF and i + 5 < len(text) and text[i : i + 2] == "\\u":
                    low_hex = text[i + 2 : i + 6]
                    low = int(low_hex, 16)
                    if 0xDC00 <= low <= 0xDFFF:
                        i += 6
                        combined = 0x10000 + ((codepoint - 0xD800) << 10) + (low - 0xDC00)
                        result.append(chr(combined))
                        continue
                result.append(chr(codepoint))
            except Exception:
                result.append("\\")
                i += 1
        else:
            # Unknown escape sequence, keep the backslash and advance.
            result.append("\\")
            i += 1

    return "".join(result)


# Debug tag patterns - same as in llm_response.py
DEBUG_START_PATTERN = re.compile(r"\[DEBUG_START\][\s\S]*?\[DEBUG_END\]")
DEBUG_STATE_PATTERN = re.compile(r"\[DEBUG_STATE_START\][\s\S]*?\[DEBUG_STATE_END\]")
DEBUG_ROLL_PATTERN = re.compile(r"\[DEBUG_ROLL_START\][\s\S]*?\[DEBUG_ROLL_END\]")
STATE_UPDATES_PATTERN = re.compile(
    r"\[STATE_UPDATES_PROPOSED\][\s\S]*?\[END_STATE_UPDATES_PROPOSED\]"
)
# Handle malformed STATE_UPDATES blocks
STATE_UPDATES_MALFORMED_PATTERN = re.compile(
    r"S?TATE_UPDATES_PROPOSED\][\s\S]*?\[END_STATE_UPDATES_PROPOSED\]"
)

# Markdown-formatted debug patterns (LLM sometimes outputs these in narrative)
MARKDOWN_DEBUG_BLOCK_PATTERN = re.compile(
    r"---\s*\n\*\*(?:Dice Rolls|State Updates|Planning Block)\*\*:.*?(?=\n---|\Z)",
    re.DOTALL,
)
# Inline debug_info JSON objects sometimes leak into narrative; we strip them
# using bracket-aware extraction in strip_debug_content (regex alone breaks on nesting).
MARKDOWN_DEBUG_INFO_PATTERN = re.compile(r'"debug_info"\s*:\s*\{')

# JSON cleanup patterns - same as in narrative_response_schema.py
NARRATIVE_PATTERN = re.compile(r'"narrative"\s*:\s*"([^"]*(?:\\.[^"]*)*)"')
JSON_STRUCTURE_PATTERN = re.compile(r"[{}\[\]]")
JSON_KEY_QUOTES_PATTERN = re.compile(r'"([^"]+)":')
JSON_COMMA_SEPARATOR_PATTERN = re.compile(r'",\s*"')
WHITESPACE_PATTERN = re.compile(r"[^\S\r\n]+")  # Normalize spaces while preserving line breaks


def contains_json_artifacts(text: str) -> bool:
    """
    Check if text contains JSON artifacts that need cleaning.
    """
    if not text:
        return False

    is_likely_json = (
        "{" in text
        and (text.strip().startswith("{") or text.strip().startswith('"'))
        and (text.strip().endswith("}") or text.strip().endswith('"'))
        and (text.count('"') >= 4 or "entities_mentioned" in text or "narrative" in text)
    )

    has_json_fields = (
        '"narrative":' in text
        or '"god_mode_response":' in text
        or '"entities_mentioned":' in text
        or '"state_updates":' in text
        or '"description":' in text
    )

    has_json_escapes = (
        "\\n" in text
        and '\\"' in text
        and (text.count("\\n") > 1 or text.count('\\"') > 1)
    )

    return is_likely_json or has_json_fields or has_json_escapes


def convert_json_escape_sequences(text: str) -> str:
    """
    Convert JSON escape sequences to their actual characters.
    """
    if not text:
        return text
    return _unescape_json_string(text)


def clean_json_artifacts(text: str) -> str:
    """
    Clean JSON artifacts from narrative text using the same logic as parse_structured_response.
    """
    if not text or not contains_json_artifacts(text):
        return text

    cleaned_text = text

    god_mode_match = re.search(
        r'"god_mode_response"\s*:\s*"([^"]*(?:\\.[^"]*)*)"', cleaned_text
    )
    if god_mode_match:
        cleaned_text = _unescape_json_string(god_mode_match.group(1))
        logging_util.info(
            "Frontend: Extracted god_mode_response from JSON structure in display processing"
        )
        return cleaned_text

    if '"narrative"' in cleaned_text:
        narrative_match = NARRATIVE_PATTERN.search(cleaned_text)
        if narrative_match:
            cleaned_text = _unescape_json_string(narrative_match.group(1))
            logging_util.info(
                "Frontend: Extracted narrative from JSON structure in display processing"
            )
            return cleaned_text

    if '"description"' in cleaned_text:
        description_match = re.search(
            r'"description"\s*:\s*"([^"]*(?:\\.[^"]*)*)"', cleaned_text
        )
        if description_match:
            cleaned_text = _unescape_json_string(description_match.group(1))
            logging_util.info(
                "Frontend: Extracted description from JSON structure in display processing"
            )
            return cleaned_text

    if "\\n" in cleaned_text and '\\"' in cleaned_text and "{" not in cleaned_text:
        cleaned_text = _unescape_json_string(cleaned_text)
        logging_util.info("Frontend: Unescaped JSON escape sequences in text content")
        return cleaned_text

    if contains_json_artifacts(cleaned_text):
        logging_util.warning(
            "Frontend: Applying aggressive JSON cleanup in display processing"
        )
        cleaned_text = JSON_STRUCTURE_PATTERN.sub("", cleaned_text)
        cleaned_text = JSON_KEY_QUOTES_PATTERN.sub(r"\1:", cleaned_text)
        cleaned_text = JSON_COMMA_SEPARATOR_PATTERN.sub(". ", cleaned_text)
        cleaned_text = _unescape_json_string(cleaned_text)
        cleaned_text = WHITESPACE_PATTERN.sub(" ", cleaned_text).strip()

    return cleaned_text


def contains_debug_tags(text: str) -> bool:
    """Check if text contains any legacy debug tags or markdown debug content."""
    if not text:
        return False

    patterns = [
        DEBUG_START_PATTERN,
        DEBUG_STATE_PATTERN,
        DEBUG_ROLL_PATTERN,
        STATE_UPDATES_PATTERN,
        MARKDOWN_DEBUG_BLOCK_PATTERN,
        MARKDOWN_DEBUG_INFO_PATTERN,
    ]
    return any(pattern.search(text) for pattern in patterns)


def strip_debug_content(text: str) -> str:
    """Strip all debug content from text (for non-debug mode)."""
    if not text:
        return text

    processed = DEBUG_START_PATTERN.sub("", text)
    processed = DEBUG_STATE_PATTERN.sub("", processed)
    processed = DEBUG_ROLL_PATTERN.sub("", processed)
    processed = STATE_UPDATES_PATTERN.sub("", processed)
    processed = STATE_UPDATES_MALFORMED_PATTERN.sub("", processed)
    processed = MARKDOWN_DEBUG_BLOCK_PATTERN.sub("", processed)

    for _ in range(50):
        match = MARKDOWN_DEBUG_INFO_PATTERN.search(processed)
        if not match:
            break

        debug_obj = _extract_nested_object(processed, "debug_info")
        if not debug_obj:
            processed = processed[: match.start()] + processed[match.end() :]
            continue

        obj_pos = processed.find(debug_obj, match.start())
        if obj_pos == -1:
            processed = processed[: match.start()] + processed[match.end() :]
            continue

        removal_start = match.start()
        removal_end = obj_pos + len(debug_obj)

        prefix = processed[:removal_start].rstrip()
        if prefix.endswith(","):
            search_start = max(0, len(prefix) - 50)
            local_comma_pos = prefix.rfind(",", search_start)
            if local_comma_pos != -1:
                removal_start = local_comma_pos

        suffix = processed[removal_end:]
        suffix_l = suffix.lstrip()
        if suffix_l.startswith(","):
            removal_end += (len(suffix) - len(suffix_l)) + 1

        processed = processed[:removal_start] + processed[removal_end:]

    processed = re.sub(r"(?:^|\n)---\s*(?:\n---\s*)*(?:\n|$)", "\n", processed)
    processed = re.sub(r"\n{3,}", "\n\n", processed)

    return processed.strip()


def strip_state_updates_only(text: str) -> str:
    """Strip only STATE_UPDATES blocks (for debug mode)."""
    if not text:
        return text
    processed = STATE_UPDATES_PATTERN.sub("", text)
    return STATE_UPDATES_MALFORMED_PATTERN.sub("", processed)


def process_story_entry_for_display(entry: dict[str, Any], debug_mode: bool) -> dict[str, Any]:
    """Process a single story entry for display, handling debug content and JSON artifacts appropriately."""
    if entry.get("actor") != "gemini":
        return entry

    text = entry.get("text", "")
    processed_text = text

    if contains_json_artifacts(text):
        processed_text = clean_json_artifacts(text)
        logging_util.info("Frontend: Cleaned JSON artifacts from story entry")

    if contains_debug_tags(processed_text):
        if debug_mode:
            processed_text = strip_state_updates_only(processed_text)
        else:
            processed_text = strip_debug_content(processed_text)

    if processed_text != text:
        processed_entry = entry.copy()
        processed_entry["text"] = processed_text
        return processed_entry

    return entry


def process_story_for_display(story_entries: list[dict[str, Any]], debug_mode: bool) -> list[dict[str, Any]]:
    """Process a full story (list of entries) for display."""
    return [process_story_entry_for_display(entry, debug_mode) for entry in story_entries]


def get_narrative_for_display(story_text: str, debug_mode: bool) -> str:
    """Get narrative text appropriate for display based on campaign type and debug mode."""
    if not contains_debug_tags(story_text):
        return story_text
    if debug_mode:
        return strip_state_updates_only(story_text)
    return strip_debug_content(story_text)

