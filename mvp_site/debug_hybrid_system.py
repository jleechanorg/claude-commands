"""
Hybrid debug content system for backward compatibility.

This module provides functions to handle both old campaigns with embedded debug tags
and new campaigns with structured debug_info fields.
"""

import re
from typing import Any

from mvp_site import logging_util
from mvp_site.json_utils import unescape_json_string, extract_nested_object

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
# Matches blocks like:
#   ---
#   **Dice Rolls**: []
#   ---
#   **State Updates**:
#   - player_character_data.inventory...
#   ---
MARKDOWN_DEBUG_BLOCK_PATTERN = re.compile(
    r"---\s*\n\*\*(?:Dice Rolls|State Updates|Planning Block)\*\*:.*?(?=\n---|\Z)",
    re.DOTALL
)
# Inline debug_info JSON objects sometimes leak into narrative; we strip them
# using bracket-aware extraction in strip_debug_content (regex alone breaks on nesting).
MARKDOWN_DEBUG_INFO_PATTERN = re.compile(r'"debug_info"\s*:\s*\{')

# JSON cleanup patterns - same as in narrative_response_schema.py
NARRATIVE_PATTERN = re.compile(r'"narrative"\s*:\s*"([^"]*(?:\\.[^"]*)*)"')
JSON_STRUCTURE_PATTERN = re.compile(r"[{}\[\]]")
JSON_KEY_QUOTES_PATTERN = re.compile(r'"([^"]+)":')
JSON_COMMA_SEPARATOR_PATTERN = re.compile(r'",\s*"')
WHITESPACE_PATTERN = re.compile(
    r"[^\S\r\n]+"
)  # Normalize spaces while preserving line breaks


def contains_json_artifacts(text: str) -> bool:
    """
    Check if text contains JSON artifacts that need cleaning.

    Args:
        text: Text to check for JSON artifacts

    Returns:
        True if text appears to contain JSON that should be cleaned
    """
    if not text:
        return False

    # Check multiple indicators to avoid corrupting valid narrative text
    is_likely_json = (
        "{" in text
        and (text.strip().startswith("{") or text.strip().startswith('"'))
        and (text.strip().endswith("}") or text.strip().endswith('"'))
        and (
            text.count('"') >= 4 or "entities_mentioned" in text or "narrative" in text
        )  # Either quotes or JSON field names
    )

    # Also check for specific JSON field patterns that shouldn't appear in narrative
    has_json_fields = (
        '"narrative":' in text
        or '"god_mode_response":' in text
        or '"entities_mentioned":' in text
        or '"state_updates":' in text
        or '"description":' in text
    )

    # Check for JSON escape sequences that indicate this is escaped JSON content
    has_json_escapes = (
        "\\n" in text  # Literal \n characters
        and '\\"' in text  # Escaped quotes
        and (text.count("\\n") > 1 or text.count('\\"') > 1)  # Multiple escapes
    )

    return is_likely_json or has_json_fields or has_json_escapes


def convert_json_escape_sequences(text: str) -> str:
    """
    Convert JSON escape sequences to their actual characters.

    This function properly converts JSON escape sequences like \\n, \\t, \\" to
    their actual character equivalents, preserving content structure.

    Args:
        text: Text containing JSON escape sequences

    Returns:
        Text with escape sequences converted to actual characters
    """
    if not text:
        return text

    # Use json_utils.unescape_json_string for proper conversion
    return unescape_json_string(text)


def clean_json_artifacts(text: str) -> str:
    """
    Clean JSON artifacts from narrative text using the same logic as parse_structured_response.

    Args:
        text: Text that may contain JSON artifacts

    Returns:
        Cleaned text with JSON artifacts removed
    """
    if not text or not contains_json_artifacts(text):
        return text

    cleaned_text = text

    # First, check for god_mode_response pattern (prioritize over narrative)
    god_mode_match = re.search(
        r'"god_mode_response"\s*:\s*"([^"]*(?:\\.[^"]*)*)"', cleaned_text
    )
    if god_mode_match:
        cleaned_text = god_mode_match.group(1)
        # Properly unescape JSON string escapes
        cleaned_text = unescape_json_string(cleaned_text)
        logging_util.info(
            "Frontend: Extracted god_mode_response from JSON structure in display processing"
        )
        return cleaned_text

    # Then, try to extract just the narrative value if possible
    if '"narrative"' in cleaned_text:
        narrative_match = NARRATIVE_PATTERN.search(cleaned_text)
        if narrative_match:
            cleaned_text = narrative_match.group(1)
            # Properly unescape JSON string escapes
            cleaned_text = unescape_json_string(cleaned_text)
            logging_util.info(
                "Frontend: Extracted narrative from JSON structure in display processing"
            )
            return cleaned_text

    # Check for description pattern (for campaign descriptions)
    if '"description"' in cleaned_text:
        description_match = re.search(
            r'"description"\s*:\s*"([^"]*(?:\\.[^"]*)*)"', cleaned_text
        )
        if description_match:
            cleaned_text = description_match.group(1)
            # Properly unescape JSON string escapes
            cleaned_text = unescape_json_string(cleaned_text)
            logging_util.info(
                "Frontend: Extracted description from JSON structure in display processing"
            )
            return cleaned_text

    # Check if this is just escaped JSON content (like Dragon Knight description)
    if "\\n" in cleaned_text and '\\"' in cleaned_text and "{" not in cleaned_text:
        # This appears to be just escaped text content, not JSON structure
        cleaned_text = unescape_json_string(cleaned_text)
        logging_util.info("Frontend: Unescaped JSON escape sequences in text content")
        return cleaned_text

    # Fallback to aggressive cleanup only as last resort
    if contains_json_artifacts(cleaned_text):
        logging_util.warning(
            "Frontend: Applying aggressive JSON cleanup in display processing"
        )
        cleaned_text = JSON_STRUCTURE_PATTERN.sub(
            "", cleaned_text
        )  # Remove braces and brackets
        cleaned_text = JSON_KEY_QUOTES_PATTERN.sub(
            r"\1:", cleaned_text
        )  # Remove quotes from keys
        cleaned_text = JSON_COMMA_SEPARATOR_PATTERN.sub(
            ". ", cleaned_text
        )  # Replace JSON comma separators
        cleaned_text = unescape_json_string(
            cleaned_text
        )  # Properly unescape all JSON escape sequences
        cleaned_text = WHITESPACE_PATTERN.sub(
            " ", cleaned_text
        )  # Normalize spaces while preserving line breaks
        cleaned_text = cleaned_text.strip()

    return cleaned_text


def contains_debug_tags(text: str) -> bool:
    """
    Check if text contains any legacy debug tags or markdown debug content.

    Args:
        text: Story text to check

    Returns:
        True if any debug tags are found
    """
    if not text:
        return False

    # Check for any debug tag patterns (including markdown format)
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
    """
    Strip all debug content from text (for non-debug mode).

    Args:
        text: Text with potential debug tags

    Returns:
        Text with all debug content removed
    """
    if not text:
        return text

    # Apply all debug stripping patterns (legacy tags)
    processed = DEBUG_START_PATTERN.sub("", text)
    processed = DEBUG_STATE_PATTERN.sub("", processed)
    processed = DEBUG_ROLL_PATTERN.sub("", processed)
    processed = STATE_UPDATES_PATTERN.sub("", processed)
    processed = STATE_UPDATES_MALFORMED_PATTERN.sub("", processed)

    # Strip markdown-formatted debug blocks
    processed = MARKDOWN_DEBUG_BLOCK_PATTERN.sub("", processed)

    # Remove any embedded "debug_info": {...} objects with bracket-aware parsing
    while True:
        match = MARKDOWN_DEBUG_INFO_PATTERN.search(processed)
        if not match:
            break
        debug_obj = extract_nested_object(processed, "debug_info")
        if not debug_obj:
            # Fallback: if extraction fails, remove the marker to avoid infinite loop
            processed = processed[: match.start()] + processed[match.end() :]
            break
        processed = processed.replace(f'"debug_info": {debug_obj}', "")

    # Clean up leftover --- separators (may be left orphaned after stripping)
    processed = re.sub(r"(?:^|\n)---\s*(?:\n---\s*)*(?:\n|$)", "\n", processed)

    # Clean up excessive newlines left after stripping
    processed = re.sub(r"\n{3,}", "\n\n", processed)

    return processed.strip()


def strip_state_updates_only(text: str) -> str:
    """
    Strip only STATE_UPDATES blocks (for debug mode).

    Args:
        text: Text with potential state update blocks

    Returns:
        Text with STATE_UPDATES blocks removed but other debug content preserved
    """
    if not text:
        return text

    # Remove only STATE_UPDATES_PROPOSED blocks
    processed = STATE_UPDATES_PATTERN.sub("", text)
    return STATE_UPDATES_MALFORMED_PATTERN.sub("", processed)


def process_story_entry_for_display(
    entry: dict[str, Any], debug_mode: bool
) -> dict[str, Any]:
    """
    Process a single story entry for display, handling debug content and JSON artifacts appropriately.

    Args:
        entry: Story entry from database
        debug_mode: Whether debug mode is enabled

    Returns:
        Processed story entry safe for display
    """
    # Only process AI responses
    if entry.get("actor") != "gemini":
        return entry

    # Get the text content
    text = entry.get("text", "")
    processed_text = text

    # First, clean any JSON artifacts that shouldn't appear in narrative text
    if contains_json_artifacts(text):
        processed_text = clean_json_artifacts(text)
        logging_util.info("Frontend: Cleaned JSON artifacts from story entry")

    # Then, check if this is an old campaign with embedded debug tags
    if contains_debug_tags(processed_text):
        # Apply appropriate stripping based on debug mode
        if debug_mode:
            # In debug mode, only strip STATE_UPDATES blocks
            processed_text = strip_state_updates_only(processed_text)
        else:
            # In non-debug mode, strip all debug content
            processed_text = strip_debug_content(processed_text)

    # Create a new entry dict if any processing was done
    if processed_text != text:
        processed_entry = entry.copy()
        processed_entry["text"] = processed_text
        return processed_entry

    # For new campaigns with no artifacts, text should already be clean
    return entry


def process_story_for_display(
    story_entries: list[dict[str, Any]], debug_mode: bool
) -> list[dict[str, Any]]:
    """
    Process a full story (list of entries) for display.

    Args:
        story_entries: List of story entries from database
        debug_mode: Whether debug mode is enabled

    Returns:
        Processed story entries safe for display
    """
    return [
        process_story_entry_for_display(entry, debug_mode) for entry in story_entries
    ]


def get_narrative_for_display(story_text: str, debug_mode: bool) -> str:
    """
    Get narrative text appropriate for display based on campaign type and debug mode.

    This is the main function for processing individual narrative texts.

    Args:
        story_text: Raw story text from database
        debug_mode: Whether debug mode is enabled

    Returns:
        Processed narrative text
    """
    # Check if this is an old campaign with embedded debug tags
    if not contains_debug_tags(story_text):
        # New campaign - text is already clean
        return story_text

    # Old campaign - apply appropriate stripping
    if debug_mode:
        return strip_state_updates_only(story_text)
    return strip_debug_content(story_text)
