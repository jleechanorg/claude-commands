"""
Text Processor - A Python CLI utility for text processing operations.

This package provides a command-line interface for common text processing tasks:
- Word, character, and line counting
- Text replacement operations
- Case conversion (uppercase, lowercase, title case)

The package is structured with:
- text_processor.py: Main CLI interface
- operations.py: Core text processing logic
- tests/: Comprehensive test suite
"""

from .operations import (
    convert_case,
    count_characters,
    count_lines,
    count_words,
    replace_text,
)

__version__ = "1.0.0"
__author__ = "WorldArchitect.AI"

__all__ = [
    "count_words",
    "count_characters",
    "count_lines",
    "replace_text",
    "convert_case"
]
