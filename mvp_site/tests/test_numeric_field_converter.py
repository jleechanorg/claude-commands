#!/usr/bin/env python3
"""Test cases for refactored NumericFieldConverter"""

import os
import sys
import unittest

# Add the mvp_site directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from numeric_field_converter import NumericFieldConverter


class TestNumericFieldConverter(unittest.TestCase):
    """Test refactored NumericFieldConverter functionality"""

    def test_try_convert_to_int_success(self):
        """Test successful string to int conversion"""
        assert NumericFieldConverter.try_convert_to_int("123") == 123
        assert NumericFieldConverter.try_convert_to_int("0") == 0
        assert NumericFieldConverter.try_convert_to_int("-42") == -42

    def test_try_convert_to_int_failure(self):
        """Test failed conversion returns original value"""
        assert NumericFieldConverter.try_convert_to_int("abc") == "abc"
        assert NumericFieldConverter.try_convert_to_int("12.5") == "12.5"
        assert NumericFieldConverter.try_convert_to_int("") == ""
        assert NumericFieldConverter.try_convert_to_int("unknown") == "unknown"

    def test_try_convert_to_int_non_string(self):
        """Test non-string values are returned unchanged"""
        assert NumericFieldConverter.try_convert_to_int(123) == 123
        assert NumericFieldConverter.try_convert_to_int(None) == None
        assert NumericFieldConverter.try_convert_to_int([1, 2, 3]) == [1, 2, 3]
        assert NumericFieldConverter.try_convert_to_int({"a": 1}) == {"a": 1}

    def test_convert_dict_with_fields(self):
        """Test dictionary conversion with specified numeric fields"""
        numeric_fields = {"hp", "level", "strength"}
        test_dict = {
            "hp": "25",
            "level": "5",
            "strength": "18",
            "name": "Aragorn",
            "description": "A ranger",
        }

        result = NumericFieldConverter.convert_dict_with_fields(
            test_dict, numeric_fields
        )

        assert result["hp"] == 25
        assert result["level"] == 5
        assert result["strength"] == 18
        assert result["name"] == "Aragorn"  # Non-numeric field unchanged
        assert result["description"] == "A ranger"  # Non-numeric field unchanged

    def test_convert_dict_with_fields_nested(self):
        """Test nested dictionary conversion"""
        numeric_fields = {"hp", "damage"}
        test_dict = {
            "character": {"hp": "50", "name": "Legolas"},
            "weapon": {"damage": "8", "type": "bow"},
        }

        result = NumericFieldConverter.convert_dict_with_fields(
            test_dict, numeric_fields
        )

        assert result["character"]["hp"] == 50
        assert result["character"]["name"] == "Legolas"
        assert result["weapon"]["damage"] == 8
        assert result["weapon"]["type"] == "bow"

    def test_convert_dict_with_fields_list(self):
        """Test list processing in dictionary conversion"""
        numeric_fields = {"count", "level"}
        test_dict = {
            "items": [
                {"count": "5", "name": "potion"},
                {"count": "3", "name": "scroll"},
            ],
            "characters": [
                {"level": "3", "name": "Gimli"},
                {"level": "4", "name": "Boromir"},
            ],
        }

        result = NumericFieldConverter.convert_dict_with_fields(
            test_dict, numeric_fields
        )

        assert result["items"][0]["count"] == 5
        assert result["items"][1]["count"] == 3
        assert result["characters"][0]["level"] == 3
        assert result["characters"][1]["level"] == 4
        assert result["items"][0]["name"] == "potion"

    def test_convert_all_possible_ints(self):
        """Test converting all possible integer strings"""
        test_dict = {
            "numeric_string": "42",
            "text_string": "hello",
            "mixed": "abc123",
            "negative": "-15",
            "zero": "0",
            "already_int": 99,
            "float_string": "12.5",
        }

        result = NumericFieldConverter.convert_all_possible_ints(test_dict)

        assert result["numeric_string"] == 42
        assert result["text_string"] == "hello"  # Unchanged
        assert result["mixed"] == "abc123"  # Unchanged
        assert result["negative"] == -15
        assert result["zero"] == 0
        assert result["already_int"] == 99  # Unchanged
        assert result["float_string"] == "12.5"  # Unchanged

    def test_convert_all_possible_ints_nested(self):
        """Test convert_all_possible_ints with nested structures"""
        test_dict = {
            "level1": {
                "numeric": "123",
                "text": "abc",
                "level2": {"deep_numeric": "456"},
            },
            "list_field": ["789", "text", "0"],
        }

        result = NumericFieldConverter.convert_all_possible_ints(test_dict)

        assert result["level1"]["numeric"] == 123
        assert result["level1"]["text"] == "abc"
        assert result["level1"]["level2"]["deep_numeric"] == 456
        assert result["list_field"] == [789, "text", 0]

    def test_legacy_convert_value(self):
        """Test legacy convert_value method for backward compatibility"""
        # Should ignore the key and just try to convert the value
        assert NumericFieldConverter.convert_value("any_key", "123") == 123
        assert NumericFieldConverter.convert_value("any_key", "text") == "text"

    def test_legacy_convert_dict(self):
        """Test legacy convert_dict method for backward compatibility"""
        test_dict = {"hp": "25", "name": "Test", "unknown_field": "42"}

        result = NumericFieldConverter.convert_dict(test_dict)

        # Should convert all possible integers regardless of field name
        assert result["hp"] == 25
        assert result["name"] == "Test"
        assert result["unknown_field"] == 42

    def test_invalid_data_handling(self):
        """Test handling of invalid data types"""
        # Non-dict input to dict methods should return unchanged
        assert NumericFieldConverter.convert_dict_with_fields("not_a_dict", set()) == "not_a_dict"
        assert NumericFieldConverter.convert_all_possible_ints(None) == None
        assert NumericFieldConverter.convert_dict([1, 2, 3]) == [1, 2, 3]


if __name__ == "__main__":
    unittest.main()
