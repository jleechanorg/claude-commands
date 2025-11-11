"""
Core text processing operations module.

This module provides the core functionality for text processing operations
including counting, replacement, and case conversion.
"""

import re
from typing import Any


def count_words(text: str | None) -> int:
    """
    Count the number of words in the given text.

    Args:
        text: Input text string

    Returns:
        Number of words in the text
    """
    if text is None or not text.strip():
        return 0

    # Split on whitespace and filter out empty strings
    words = [word for word in text.split() if word.strip()]
    return len(words)


def count_characters(text: str | None, include_spaces: bool = True) -> int:
    """
    Count the number of characters in the given text.

    Args:
        text: Input text string
        include_spaces: Whether to include spaces in the count

    Returns:
        Number of characters in the text
    """
    if text is None:
        return 0

    if include_spaces:
        return len(text)
    return len(text.replace(' ', '').replace('\t', '').replace('\n', '').replace('\r', ''))


def count_lines(text: str | None) -> int:
    """
    Count the number of lines in the given text.

    Args:
        text: Input text string

    Returns:
        Number of lines in the text
    """
    if text is None:
        return 0

    # Count newlines and add 1 if text doesn't end with newline
    lines = text.split('\n')
    # Remove empty line at end if text ends with newline
    if lines and lines[-1] == '':
        lines.pop()

    return len(lines) if lines else 0


def replace_text(text: str | None, old: str, new: str, case_sensitive: bool = True) -> str | None:
    """
    Replace occurrences of old text with new text.

    Args:
        text: Input text string
        old: Text to be replaced
        new: Replacement text
        case_sensitive: Whether replacement should be case sensitive

    Returns:
        Text with replacements made
    """
    if text is None or not old:
        return text

    if case_sensitive:
        return text.replace(old, new)
    # Use regex for case-insensitive replacement
    pattern = re.escape(old)
    return re.sub(pattern, lambda _: new, text, flags=re.IGNORECASE)


def convert_case(text: str | None, case_type: str) -> str | None:
    """
    Convert text case according to the specified type.

    Args:
        text: Input text string
        case_type: Type of case conversion ('upper', 'lower', 'title', 'capitalize')

    Returns:
        Text with case conversion applied

    Raises:
        ValueError: If case_type is not supported
    """
    if text is None:
        return text

    case_type = case_type.lower()

    if case_type == 'upper':
        return text.upper()
    if case_type == 'lower':
        return text.lower()
    if case_type == 'title':
        return text.title()
    if case_type == 'capitalize':
        return text.capitalize()
    raise ValueError(f"Unsupported case type: {case_type}. "
                    f"Supported types: upper, lower, title, capitalize")


def get_text_stats(text: str) -> dict[str, Any]:
    """
    Get comprehensive statistics about the text.

    Args:
        text: Input text string

    Returns:
        Dictionary containing various text statistics
    """
    stats = {
        'characters_with_spaces': count_characters(text, include_spaces=True),
        'characters_without_spaces': count_characters(text, include_spaces=False),
        'words': count_words(text),
        'lines': count_lines(text),
        'paragraphs': len([p for p in text.split('\n\n') if p.strip()]) if text else 0
    }

    return stats
