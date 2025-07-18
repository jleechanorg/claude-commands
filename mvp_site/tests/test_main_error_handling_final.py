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

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import parse_set_command


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
            self.assertEqual(result["hp"], 100)
            self.assertEqual(result["str"], 18)
            self.assertEqual(result["valid_array"], [1, 2, 3])

            # Invalid JSON should be skipped
            self.assertNotIn("name", result)
            self.assertNotIn("broken", result)
            self.assertNotIn("array", result)

            # Should log warnings for invalid JSON
            self.assertEqual(mock_warning.call_count, 3)

    def test_empty_values_and_whitespace(self):
        """Test handling of empty values and whitespace"""
        command = """
        hp=50
        
        name="Hero"
        """

        result = parse_set_command(command)
        self.assertEqual(result, {"hp": 50, "name": "Hero"})

    def test_lines_without_equals(self):
        """Test lines that don't contain equals sign are ignored"""
        command = """hp=100
this line has no equals
str=15
another line without it
wis=12"""

        result = parse_set_command(command)
        self.assertEqual(result, {"hp": 100, "str": 15, "wis": 12})

    def test_special_characters_in_values(self):
        """Test values containing special characters"""
        command = '''name="Hero = 'Strong'"
formula="damage = str * 2"
description="Line 1\\nLine 2"'''

        result = parse_set_command(command)
        self.assertEqual(result["name"], "Hero = 'Strong'")
        self.assertEqual(result["formula"], "damage = str * 2")
        # JSON parsing converts \\n to actual newline
        self.assertEqual(result["description"], "Line 1\nLine 2")

    def test_numeric_boolean_null_values(self):
        """Test various value types"""
        command = """int=42
float=3.14
bool_true=true
bool_false=false
null_value=null"""

        result = parse_set_command(command)
        self.assertEqual(result["int"], 42)
        self.assertEqual(result["float"], 3.14)
        self.assertEqual(result["bool_true"], True)
        self.assertEqual(result["bool_false"], False)
        self.assertIsNone(result["null_value"])

    def test_arrays_and_objects(self):
        """Test complex JSON structures"""
        command = """items=["sword", "shield"]
stats={"str": 18, "dex": 14}
nested={"player": {"level": 5}}"""

        result = parse_set_command(command)
        self.assertEqual(result["items"], ["sword", "shield"])
        self.assertEqual(result["stats"], {"str": 18, "dex": 14})
        self.assertEqual(result["nested"], {"player": {"level": 5}})

    def test_edge_cases(self):
        """Test various edge cases"""
        command = """valid=100
=no_key
key_only=
multiple=equals=signs"""

        with patch("logging_util.warning") as mock_warning:
            result = parse_set_command(command)

            # Valid line
            self.assertEqual(result["valid"], 100)

            # Lines with empty key or value are skipped
            self.assertEqual(len(result), 1)  # Only 'valid' was parsed

            # All invalid lines should generate warnings
            self.assertTrue(mock_warning.call_count >= 2)

    def test_unicode_and_emoji(self):
        """Test unicode characters and emoji"""
        command = """name="Hero 🗡️"
title="龍 Slayer"
items=["⚔️", "🛡️"]"""

        result = parse_set_command(command)
        self.assertEqual(result["name"], "Hero 🗡️")
        self.assertEqual(result["title"], "龍 Slayer")
        self.assertEqual(result["items"], ["⚔️", "🛡️"])

    def test_very_long_values(self):
        """Test handling of very long values"""
        long_string = "x" * 1000
        command = f'''short=123
long="{long_string}"
after=456'''

        result = parse_set_command(command)
        self.assertEqual(result["short"], 123)
        self.assertEqual(result["long"], long_string)
        self.assertEqual(result["after"], 456)

    def test_escaped_characters(self):
        """Test escaped characters in JSON strings"""
        command = r'''quote="She said \"Hello\""
newline="First\nSecond"
tab="Col1\tCol2"
backslash="Path\\to\\file"'''

        result = parse_set_command(command)
        self.assertEqual(result["quote"], 'She said "Hello"')
        self.assertEqual(result["newline"], "First\nSecond")
        self.assertEqual(result["tab"], "Col1\tCol2")
        self.assertEqual(result["backslash"], "Path\\to\\file")


if __name__ == "__main__":
    unittest.main(verbosity=2)
