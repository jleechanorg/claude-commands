#!/usr/bin/env python3
"""
Phase 3: Error handling tests for main.py parse_set_command
Target: Improve coverage by testing error paths
"""

import os

# Add parent directory to path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from world_logic import parse_set_command


class TestParseSetCommandErrorHandling(unittest.TestCase):
    """Test error handling in parse_set_command function"""

    def test_json_decode_errors(self):
        """Test handling of invalid JSON values"""
        command = """hp=100
name={"invalid": json without quotes}
str=18
broken={incomplete
array=[1, 2, unterminated
valid_array=[1, 2, 3]"""

        with patch("logging_util.warning") as mock_warning:
            result = parse_set_command(command)

            # Valid values should be parsed
            assert result["hp"] == 100
            assert result["str"] == 18
            assert result["valid_array"] == [1, 2, 3]

            # Invalid JSON should be skipped
            assert "name" not in result
            assert "broken" not in result
            assert "array" not in result

            # Should log warnings for invalid JSON
            assert mock_warning.call_count == 3

    def test_empty_values_and_whitespace(self):
        """Test handling of empty values and whitespace"""
        command = """
        hp=50

        name="Hero"
        """

        result = parse_set_command(command)
        assert result == {"hp": 50, "name": "Hero"}

    def test_lines_without_equals(self):
        """Test lines that don't contain equals sign are ignored"""
        command = """hp=100
this line has no equals
str=15
another line without it
wis=12"""

        result = parse_set_command(command)
        assert result == {"hp": 100, "str": 15, "wis": 12}

    def test_special_characters_in_values(self):
        """Test values containing special characters"""
        command = '''name="Hero = 'Strong'"
formula="damage = str * 2"
description="Line 1\\nLine 2"'''

        result = parse_set_command(command)
        assert result["name"] == "Hero = 'Strong'"
        assert result["formula"] == "damage = str * 2"
        # JSON parsing converts \\n to actual newline
        assert result["description"] == "Line 1\nLine 2"

    def test_numeric_boolean_null_values(self):
        """Test various value types"""
        command = """int=42
float=3.14
bool_true=true
bool_false=false
null_value=null"""

        result = parse_set_command(command)
        assert result["int"] == 42
        assert result["float"] == 3.14
        assert result["bool_true"] == True
        assert result["bool_false"] == False
        assert result["null_value"] is None

    def test_arrays_and_objects(self):
        """Test complex JSON structures"""
        command = """items=["sword", "shield"]
stats={"str": 18, "dex": 14}
nested={"player": {"level": 5}}"""

        result = parse_set_command(command)
        assert result["items"] == ["sword", "shield"]
        assert result["stats"] == {"str": 18, "dex": 14}
        assert result["nested"] == {"player": {"level": 5}}

    def test_edge_cases(self):
        """Test various edge cases"""
        command = """valid=100
=no_key
key_only=
multiple=equals=signs"""

        with patch("logging_util.warning") as mock_warning:
            result = parse_set_command(command)

            # Valid line
            assert result["valid"] == 100

            # Lines with empty key or value are skipped
            assert len(result) == 1  # Only 'valid' was parsed

            # All invalid lines should generate warnings
            assert mock_warning.call_count >= 2

    def test_unicode_and_emoji(self):
        """Test unicode characters and emoji"""
        command = """name="Hero 🗡️"
title="龍 Slayer"
items=["⚔️", "🛡️"]"""

        result = parse_set_command(command)
        assert result["name"] == "Hero 🗡️"
        assert result["title"] == "龍 Slayer"
        assert result["items"] == ["⚔️", "🛡️"]

    def test_very_long_values(self):
        """Test handling of very long values"""
        long_string = "x" * 1000
        command = f"""short=123
long="{long_string}"
after=456"""

        result = parse_set_command(command)
        assert result["short"] == 123
        assert result["long"] == long_string
        assert result["after"] == 456

    def test_escaped_characters(self):
        """Test escaped characters in JSON strings"""
        command = r'''quote="She said \"Hello\""
newline="First\nSecond"
tab="Col1\tCol2"
backslash="Path\\to\\file"'''

        result = parse_set_command(command)
        assert result["quote"] == 'She said "Hello"'
        assert result["newline"] == "First\nSecond"
        assert result["tab"] == "Col1\tCol2"
        assert result["backslash"] == "Path\\to\\file"


if __name__ == "__main__":
    unittest.main(verbosity=2)
