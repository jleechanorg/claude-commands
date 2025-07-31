"""
Hybrid debug content system for backward compatibility.

This module provides functions to handle both old campaigns with embedded debug tags
and new campaigns with structured debug_info fields.
"""

import re
from typing import Any

# Debug tag patterns - same as in gemini_response.py
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


def contains_debug_tags(text: str) -> bool:
    """
    Check if text contains any legacy debug tags.

    Args:
        text: Story text to check

    Returns:
        True if any debug tags are found
    """
    if not text:
        return False

    # Check for any debug tag patterns
    patterns = [
        DEBUG_START_PATTERN,
        DEBUG_STATE_PATTERN,
        DEBUG_ROLL_PATTERN,
        STATE_UPDATES_PATTERN,
    ]

    for pattern in patterns:
        if pattern.search(text):
            return True

    return False


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

    # Apply all debug stripping patterns
    processed = DEBUG_START_PATTERN.sub("", text)
    processed = DEBUG_STATE_PATTERN.sub("", processed)
    processed = DEBUG_ROLL_PATTERN.sub("", processed)
    processed = STATE_UPDATES_PATTERN.sub("", processed)
    processed = STATE_UPDATES_MALFORMED_PATTERN.sub("", processed)

    return processed


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
    processed = STATE_UPDATES_MALFORMED_PATTERN.sub("", processed)

    return processed


def process_story_entry_for_display(
    entry: dict[str, Any], debug_mode: bool
) -> dict[str, Any]:
    """
    Process a single story entry for display, handling debug content appropriately.

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

    # Check if this is an old campaign with embedded debug tags
    if contains_debug_tags(text):
        # Apply appropriate stripping based on debug mode
        if debug_mode:
            # In debug mode, only strip STATE_UPDATES blocks
            processed_text = strip_state_updates_only(text)
        else:
            # In non-debug mode, strip all debug content
            processed_text = strip_debug_content(text)

        # Create a new entry dict to avoid modifying the original
        processed_entry = entry.copy()
        processed_entry["text"] = processed_text
        return processed_entry

    # For new campaigns, text should already be clean
    # Debug info would be in separate field (not implemented yet)
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
