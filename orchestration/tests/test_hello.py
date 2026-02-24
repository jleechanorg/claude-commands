"""Tests for hello module."""

import pytest

from orchestration.hello import say_hello


class TestSayHello:
    """Test cases for say_hello function."""

    def test_say_hello_default(self):
        """Test hello with default name."""
        result = say_hello()
        assert result == "Hello, World!"

    def test_say_hello_with_name(self):
        """Test hello with custom name."""
        result = say_hello("Alice")
        assert result == "Hello, Alice!"

    def test_say_hello_returns_string(self):
        """Test that result is a string."""
        result = say_hello()
        assert isinstance(result, str)
