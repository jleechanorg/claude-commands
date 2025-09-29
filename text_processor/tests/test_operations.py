"""
Unit tests for text_processor.operations module.
"""

import pytest
from text_processor.operations import (
    count_words,
    count_characters,
    count_lines,
    replace_text,
    convert_case,
    get_text_stats
)


class TestCountWords:
    """Test word counting functionality."""

    def test_count_words_simple(self):
        """Test basic word counting."""
        assert count_words("hello world") == 2
        assert count_words("one") == 1
        assert count_words("") == 0

    def test_count_words_multiple_spaces(self):
        """Test word counting with multiple spaces."""
        assert count_words("hello    world") == 2
        assert count_words("  hello  world  ") == 2
        assert count_words("   ") == 0

    def test_count_words_newlines_tabs(self):
        """Test word counting with newlines and tabs."""
        assert count_words("hello\nworld") == 2
        assert count_words("hello\tworld") == 2
        assert count_words("hello\n\nworld") == 2
        assert count_words("word1\n  word2\t\tword3") == 3

    def test_count_words_punctuation(self):
        """Test word counting with punctuation."""
        assert count_words("hello, world!") == 2
        assert count_words("don't count") == 2
        assert count_words("word1; word2: word3.") == 3

    def test_count_words_edge_cases(self):
        """Test edge cases for word counting."""
        assert count_words(None) == 0
        assert count_words("   \n\t   ") == 0
        assert count_words("a") == 1


class TestCountCharacters:
    """Test character counting functionality."""

    def test_count_characters_with_spaces(self):
        """Test character counting including spaces."""
        assert count_characters("hello", include_spaces=True) == 5
        assert count_characters("hello world", include_spaces=True) == 11
        assert count_characters("", include_spaces=True) == 0

    def test_count_characters_without_spaces(self):
        """Test character counting excluding spaces."""
        assert count_characters("hello", include_spaces=False) == 5
        assert count_characters("hello world", include_spaces=False) == 10
        assert count_characters("   ", include_spaces=False) == 0

    def test_count_characters_special_whitespace(self):
        """Test character counting with tabs and newlines."""
        text = "hello\tworld\n"
        assert count_characters(text, include_spaces=True) == 12
        assert count_characters(text, include_spaces=False) == 10

    def test_count_characters_edge_cases(self):
        """Test edge cases for character counting."""
        assert count_characters(None, include_spaces=True) == 0
        assert count_characters(None, include_spaces=False) == 0
        assert count_characters("", include_spaces=True) == 0
        assert count_characters("", include_spaces=False) == 0


class TestCountLines:
    """Test line counting functionality."""

    def test_count_lines_simple(self):
        """Test basic line counting."""
        assert count_lines("hello") == 1
        assert count_lines("hello\nworld") == 2
        assert count_lines("") == 0

    def test_count_lines_trailing_newline(self):
        """Test line counting with trailing newlines."""
        assert count_lines("hello\n") == 1
        assert count_lines("hello\nworld\n") == 2
        assert count_lines("hello\n\n") == 2

    def test_count_lines_empty_lines(self):
        """Test line counting with empty lines."""
        assert count_lines("hello\n\nworld") == 3
        assert count_lines("\n\n") == 2
        assert count_lines("\nhello\n") == 2

    def test_count_lines_edge_cases(self):
        """Test edge cases for line counting."""
        assert count_lines(None) == 0
        assert count_lines("\n") == 1


class TestReplaceText:
    """Test text replacement functionality."""

    def test_replace_text_basic(self):
        """Test basic text replacement."""
        assert replace_text("hello world", "world", "universe") == "hello universe"
        assert replace_text("hello", "hello", "hi") == "hi"
        assert replace_text("", "old", "new") == ""

    def test_replace_text_multiple_occurrences(self):
        """Test replacement with multiple occurrences."""
        assert replace_text("hello hello", "hello", "hi") == "hi hi"
        assert replace_text("ababab", "ab", "x") == "xxx"

    def test_replace_text_case_sensitive(self):
        """Test case-sensitive replacement."""
        result = replace_text("Hello hello", "hello", "hi", case_sensitive=True)
        assert result == "Hello hi"

    def test_replace_text_case_insensitive(self):
        """Test case-insensitive replacement."""
        result = replace_text("Hello hello", "hello", "hi", case_sensitive=False)
        assert result == "hi hi"

    def test_replace_text_no_match(self):
        """Test replacement when pattern not found."""
        assert replace_text("hello world", "xyz", "abc") == "hello world"

    def test_replace_text_edge_cases(self):
        """Test edge cases for text replacement."""
        assert replace_text("hello", "", "new") == "hello"
        assert replace_text(None, "old", "new") == None
        assert replace_text("hello", "hello", "") == ""


class TestConvertCase:
    """Test case conversion functionality."""

    def test_convert_case_upper(self):
        """Test uppercase conversion."""
        assert convert_case("hello world", "upper") == "HELLO WORLD"
        assert convert_case("Hello World", "UPPER") == "HELLO WORLD"

    def test_convert_case_lower(self):
        """Test lowercase conversion."""
        assert convert_case("HELLO WORLD", "lower") == "hello world"
        assert convert_case("Hello World", "LOWER") == "hello world"

    def test_convert_case_title(self):
        """Test title case conversion."""
        assert convert_case("hello world", "title") == "Hello World"
        assert convert_case("HELLO WORLD", "TITLE") == "Hello World"

    def test_convert_case_capitalize(self):
        """Test capitalize conversion."""
        assert convert_case("hello world", "capitalize") == "Hello world"
        assert convert_case("HELLO WORLD", "CAPITALIZE") == "Hello world"

    def test_convert_case_invalid_type(self):
        """Test invalid case type."""
        with pytest.raises(ValueError, match="Unsupported case type"):
            convert_case("hello", "invalid")

    def test_convert_case_edge_cases(self):
        """Test edge cases for case conversion."""
        assert convert_case("", "upper") == ""
        assert convert_case(None, "upper") == None
        assert convert_case("123", "upper") == "123"


class TestGetTextStats:
    """Test comprehensive text statistics functionality."""

    def test_get_text_stats_basic(self):
        """Test basic text statistics."""
        text = "Hello world.\nThis is a test."
        stats = get_text_stats(text)

        assert stats['words'] == 6
        assert stats['characters_with_spaces'] == 28
        assert stats['characters_without_spaces'] == 23
        assert stats['lines'] == 2
        assert stats['paragraphs'] == 1

    def test_get_text_stats_paragraphs(self):
        """Test paragraph counting in statistics."""
        text = "Paragraph 1\n\nParagraph 2\n\nParagraph 3"
        stats = get_text_stats(text)

        assert stats['paragraphs'] == 3

    def test_get_text_stats_empty(self):
        """Test statistics for empty text."""
        stats = get_text_stats("")

        assert stats['words'] == 0
        assert stats['characters_with_spaces'] == 0
        assert stats['characters_without_spaces'] == 0
        assert stats['lines'] == 0
        assert stats['paragraphs'] == 0

    def test_get_text_stats_single_word(self):
        """Test statistics for single word."""
        stats = get_text_stats("hello")

        assert stats['words'] == 1
        assert stats['characters_with_spaces'] == 5
        assert stats['characters_without_spaces'] == 5
        assert stats['lines'] == 1
        assert stats['paragraphs'] == 1
