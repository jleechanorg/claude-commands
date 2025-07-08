"""
Comprehensive test suite for json_utils.py
Tests JSON parsing utilities for handling incomplete or malformed JSON responses
"""
import unittest
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from json_utils import (
    count_unmatched_quotes,
    count_unmatched_braces,
    unescape_json_string,
    try_parse_json,
    extract_json_boundaries,
    complete_truncated_json,
    extract_field_value
)


class TestCountUnmatchedQuotes(unittest.TestCase):
    """Test count_unmatched_quotes function"""
    
    def test_no_quotes(self):
        """Test with text containing no quotes"""
        self.assertEqual(count_unmatched_quotes("hello world"), 0)
        self.assertEqual(count_unmatched_quotes(""), 0)
        self.assertEqual(count_unmatched_quotes("123 456"), 0)
    
    def test_matched_quotes(self):
        """Test with properly matched quotes"""
        self.assertEqual(count_unmatched_quotes('"hello"'), 2)
        self.assertEqual(count_unmatched_quotes('"hello" "world"'), 4)
        self.assertEqual(count_unmatched_quotes('{"key": "value"}'), 4)
    
    def test_unmatched_quotes(self):
        """Test with unmatched quotes"""
        self.assertEqual(count_unmatched_quotes('"hello'), 1)
        self.assertEqual(count_unmatched_quotes('"hello" "world'), 3)
        self.assertEqual(count_unmatched_quotes('{"key": "value'), 3)
    
    def test_escaped_quotes(self):
        """Test with escaped quotes"""
        self.assertEqual(count_unmatched_quotes(r'"hello \"world\""'), 2)
        self.assertEqual(count_unmatched_quotes(r'"say \"hi\""'), 2)
        self.assertEqual(count_unmatched_quotes(r'"\""'), 2)
    
    def test_escaped_backslashes(self):
        """Test with escaped backslashes before quotes"""
        self.assertEqual(count_unmatched_quotes(r'"hello\\"'), 2)
        self.assertEqual(count_unmatched_quotes(r'"path\\to\\file"'), 2)
        self.assertEqual(count_unmatched_quotes(r'"end with \\\\"'), 2)
    
    def test_mixed_escape_sequences(self):
        """Test with various escape sequences"""
        self.assertEqual(count_unmatched_quotes(r'"\n\t\r"'), 2)
        self.assertEqual(count_unmatched_quotes(r'"line1\nline2"'), 2)
        self.assertEqual(count_unmatched_quotes(r'"\\"\\"\\"'), 4)  # Fixed: escape_next algorithm counts 4
    
    def test_complex_json_strings(self):
        """Test with complex JSON-like strings"""
        json_str = '{"name": "John \\"Doe\\"", "path": "C:\\\\Users\\\\file.txt"}'
        self.assertEqual(count_unmatched_quotes(json_str), 8)
        
        incomplete_json = '{"name": "John \\"Doe\\"", "path": "C:\\\\Users'
        self.assertEqual(count_unmatched_quotes(incomplete_json), 7)  # Fixed: escape_next algorithm counts 7


class TestCountUnmatchedBraces(unittest.TestCase):
    """Test count_unmatched_braces function"""
    
    def test_no_braces(self):
        """Test with text containing no braces or brackets"""
        self.assertEqual(count_unmatched_braces("hello world"), (0, 0))
        self.assertEqual(count_unmatched_braces(""), (0, 0))
        self.assertEqual(count_unmatched_braces("key: value"), (0, 0))
    
    def test_matched_braces(self):
        """Test with properly matched braces"""
        self.assertEqual(count_unmatched_braces("{}"), (0, 0))
        self.assertEqual(count_unmatched_braces("{key: value}"), (0, 0))
        self.assertEqual(count_unmatched_braces("{{nested}}"), (0, 0))
    
    def test_matched_brackets(self):
        """Test with properly matched brackets"""
        self.assertEqual(count_unmatched_braces("[]"), (0, 0))
        self.assertEqual(count_unmatched_braces("[1, 2, 3]"), (0, 0))
        self.assertEqual(count_unmatched_braces("[[nested]]"), (0, 0))
    
    def test_unmatched_braces(self):
        """Test with unmatched braces"""
        self.assertEqual(count_unmatched_braces("{"), (1, 0))
        self.assertEqual(count_unmatched_braces("}"), (-1, 0))
        self.assertEqual(count_unmatched_braces("{{}"), (1, 0))
        self.assertEqual(count_unmatched_braces("{}}"), (-1, 0))
    
    def test_unmatched_brackets(self):
        """Test with unmatched brackets"""
        self.assertEqual(count_unmatched_braces("["), (0, 1))
        self.assertEqual(count_unmatched_braces("]"), (0, -1))
        self.assertEqual(count_unmatched_braces("[[]"), (0, 1))
        self.assertEqual(count_unmatched_braces("[]]"), (0, -1))
    
    def test_mixed_braces_brackets(self):
        """Test with mixed braces and brackets"""
        self.assertEqual(count_unmatched_braces("{[]}"), (0, 0))
        self.assertEqual(count_unmatched_braces("[{}]"), (0, 0))
        self.assertEqual(count_unmatched_braces("{[}]"), (0, 0))  # Mismatched but balanced
        self.assertEqual(count_unmatched_braces("{["), (1, 1))
        self.assertEqual(count_unmatched_braces("}]"), (-1, -1))
    
    def test_braces_in_strings(self):
        """Test that braces inside strings are ignored"""
        self.assertEqual(count_unmatched_braces('{"key": "{value}"}'), (0, 0))
        self.assertEqual(count_unmatched_braces('{"array": "[1,2,3]"}'), (0, 0))
        self.assertEqual(count_unmatched_braces('{"text": "}{][{"}'), (0, 0))
    
    def test_escaped_quotes_in_strings(self):
        """Test with escaped quotes in strings"""
        self.assertEqual(count_unmatched_braces(r'{"key": "val\"ue}"}'), (0, 0))
        self.assertEqual(count_unmatched_braces(r'{"key": "val\\"}'), (0, 0))  # Fixed: String ends at quote, braces match
        self.assertEqual(count_unmatched_braces(r'["item\"1]", "item2"]'), (0, 0))


class TestUnescapeJsonString(unittest.TestCase):
    """Test unescape_json_string function"""
    
    def test_no_escape_sequences(self):
        """Test with strings containing no escape sequences"""
        self.assertEqual(unescape_json_string("hello world"), "hello world")
        self.assertEqual(unescape_json_string(""), "")
        self.assertEqual(unescape_json_string("123"), "123")
    
    def test_newline_escapes(self):
        """Test unescaping newline characters"""
        self.assertEqual(unescape_json_string("line1\\nline2"), "line1\nline2")
        self.assertEqual(unescape_json_string("\\n\\n\\n"), "\n\n\n")
        self.assertEqual(unescape_json_string("start\\n"), "start\n")
    
    def test_tab_escapes(self):
        """Test unescaping tab characters"""
        self.assertEqual(unescape_json_string("col1\\tcol2"), "col1\tcol2")
        self.assertEqual(unescape_json_string("\\t\\t"), "\t\t")
        self.assertEqual(unescape_json_string("\\ttab"), "\ttab")
    
    def test_quote_escapes(self):
        """Test unescaping quote characters"""
        self.assertEqual(unescape_json_string('\\"hello\\"'), '"hello"')
        self.assertEqual(unescape_json_string('say \\"hi\\"'), 'say "hi"')
        self.assertEqual(unescape_json_string('\\"\\"\\"'), '"""')
    
    def test_backslash_escapes(self):
        """Test unescaping backslash characters"""
        self.assertEqual(unescape_json_string("path\\\\to\\\\file"), "path\\to\\file")
        self.assertEqual(unescape_json_string("\\\\\\\\"), "\\\\")
        self.assertEqual(unescape_json_string("end\\\\"), "end\\")
    
    def test_other_escapes(self):
        """Test unescaping other special characters"""
        self.assertEqual(unescape_json_string("slash\\/test"), "slash/test")
        self.assertEqual(unescape_json_string("back\\bspace"), "back\bspace")
        self.assertEqual(unescape_json_string("form\\ffeed"), "form\ffeed")
        self.assertEqual(unescape_json_string("return\\rcarriage"), "return\rcarriage")
    
    def test_multiple_escapes(self):
        """Test unescaping multiple different escape sequences"""
        self.assertEqual(
            unescape_json_string(r'line1\nline2\ttab\r\n\"quote\"'),
            'line1\nline2\ttab\r\n"quote"'
        )
        self.assertEqual(
            unescape_json_string(r'\\path\\to\\file.txt\n'),
            '\\path\\to\\file.txt\n'
        )
    
    def test_unicode_preserved(self):
        """Test that Unicode characters are preserved"""
        self.assertEqual(unescape_json_string("Hello 世界"), "Hello 世界")
        self.assertEqual(unescape_json_string("Emoji 😀"), "Emoji 😀")
        self.assertEqual(unescape_json_string("Math π"), "Math π")


class TestTryParseJson(unittest.TestCase):
    """Test try_parse_json function"""
    
    def test_valid_json(self):
        """Test parsing valid JSON"""
        result, success = try_parse_json('{"key": "value"}')
        self.assertTrue(success)
        self.assertEqual(result, {"key": "value"})
        
        result, success = try_parse_json('[]')
        self.assertTrue(success)
        self.assertEqual(result, [])
        
        result, success = try_parse_json('[1, 2, 3]')
        self.assertTrue(success)
        self.assertEqual(result, [1, 2, 3])
    
    def test_invalid_json(self):
        """Test parsing invalid JSON"""
        result, success = try_parse_json('{invalid}')
        self.assertFalse(success)
        self.assertIsNone(result)
        
        result, success = try_parse_json('{"key": value}')  # Unquoted value
        self.assertFalse(success)
        self.assertIsNone(result)
        
        result, success = try_parse_json('{')  # Incomplete
        self.assertFalse(success)
        self.assertIsNone(result)
    
    def test_empty_string(self):
        """Test parsing empty string"""
        result, success = try_parse_json('')
        self.assertFalse(success)
        self.assertIsNone(result)
    
    def test_null_values(self):
        """Test parsing JSON with null values"""
        result, success = try_parse_json('null')
        self.assertTrue(success)
        self.assertIsNone(result)
        
        result, success = try_parse_json('{"key": null}')
        self.assertTrue(success)
        self.assertEqual(result, {"key": None})
    
    def test_numeric_values(self):
        """Test parsing JSON with numeric values"""
        result, success = try_parse_json('42')
        self.assertTrue(success)
        self.assertEqual(result, 42)
        
        result, success = try_parse_json('3.14')
        self.assertTrue(success)
        self.assertEqual(result, 3.14)
        
        result, success = try_parse_json('{"num": -123.45}')
        self.assertTrue(success)
        self.assertEqual(result, {"num": -123.45})
    
    def test_boolean_values(self):
        """Test parsing JSON with boolean values"""
        result, success = try_parse_json('true')
        self.assertTrue(success)
        self.assertEqual(result, True)
        
        result, success = try_parse_json('false')
        self.assertTrue(success)
        self.assertEqual(result, False)
        
        result, success = try_parse_json('{"active": true, "deleted": false}')
        self.assertTrue(success)
        self.assertEqual(result, {"active": True, "deleted": False})


class TestExtractJsonBoundaries(unittest.TestCase):
    """Test extract_json_boundaries function"""
    
    def test_no_json_markers(self):
        """Test with text containing no JSON markers"""
        self.assertIsNone(extract_json_boundaries("hello world"))
        self.assertIsNone(extract_json_boundaries(""))
        self.assertIsNone(extract_json_boundaries("key: value"))
    
    def test_simple_json_object(self):
        """Test extracting simple JSON objects"""
        self.assertEqual(extract_json_boundaries('{"key": "value"}'), '{"key": "value"}')
        self.assertEqual(extract_json_boundaries('prefix {"key": "value"} suffix'), '{"key": "value"}')
        self.assertEqual(extract_json_boundaries('{}'), '{}')
    
    def test_simple_json_array(self):
        """Test extracting simple JSON arrays"""
        self.assertEqual(extract_json_boundaries('[1, 2, 3]'), '[1, 2, 3]')
        self.assertEqual(extract_json_boundaries('prefix [1, 2, 3] suffix'), '[1, 2, 3]')
        self.assertEqual(extract_json_boundaries('[]'), '[]')
    
    def test_nested_json_object(self):
        """Test extracting nested JSON objects"""
        nested = '{"outer": {"inner": "value"}}'
        self.assertEqual(extract_json_boundaries(nested), nested)
        
        complex_nested = '{"a": {"b": {"c": "d"}}}'
        self.assertEqual(extract_json_boundaries(complex_nested), complex_nested)
    
    def test_json_with_strings_containing_braces(self):
        """Test extracting JSON with strings containing braces"""
        json_str = '{"text": "This has { and } in it"}'
        self.assertEqual(extract_json_boundaries(json_str), json_str)
        
        json_str = '{"nested": "{\\"inner\\": true}"}'
        self.assertEqual(extract_json_boundaries(json_str), json_str)
    
    def test_incomplete_json(self):
        """Test with incomplete JSON"""
        # Should return the incomplete JSON as-is
        incomplete = '{"key": "value", "incomplete":'
        self.assertEqual(extract_json_boundaries(incomplete), incomplete)
        
        # Unclosed nested object
        incomplete = '{"outer": {"inner": "value"'
        self.assertEqual(extract_json_boundaries(incomplete), incomplete)
    
    def test_multiple_json_objects(self):
        """Test with multiple JSON objects (should extract first)"""
        multiple = '{"first": 1} {"second": 2}'
        self.assertEqual(extract_json_boundaries(multiple), '{"first": 1}')
        
        with_text = 'Text before {"obj": true} more text {"other": false}'
        self.assertEqual(extract_json_boundaries(with_text), '{"obj": true}')
    
    def test_escaped_quotes_in_strings(self):
        """Test JSON with escaped quotes in strings"""
        json_str = r'{"quote": "She said \"Hello\""}'
        self.assertEqual(extract_json_boundaries(json_str), json_str)
        
        json_str = r'{"path": "C:\\Users\\file.txt"}'
        self.assertEqual(extract_json_boundaries(json_str), json_str)


class TestCompleteTruncatedJson(unittest.TestCase):
    """Test complete_truncated_json function"""
    
    def test_empty_string(self):
        """Test with empty string"""
        self.assertEqual(complete_truncated_json(""), "{}")
        self.assertEqual(complete_truncated_json("   "), "{}")
    
    def test_already_complete_json(self):
        """Test with already complete JSON"""
        self.assertEqual(complete_truncated_json('{"key": "value"}'), '{"key": "value"}')
        self.assertEqual(complete_truncated_json('[1, 2, 3]'), '[1, 2, 3]')
        self.assertEqual(complete_truncated_json('{}'), '{}')
    
    def test_missing_closing_brace(self):
        """Test completing JSON missing closing braces"""
        self.assertEqual(complete_truncated_json('{"key": "value"'), '{"key": "value"}')
        self.assertEqual(complete_truncated_json('{"a": {"b": "c"'), '{"a": {"b": "c"}}')
        self.assertEqual(complete_truncated_json('{'), '{}')
    
    def test_missing_closing_bracket(self):
        """Test completing JSON missing closing brackets"""
        self.assertEqual(complete_truncated_json('[1, 2, 3'), '[1, 2, 3]')
        self.assertEqual(complete_truncated_json('[{"a": "b"}'), '[{"a": "b"}]')
        self.assertEqual(complete_truncated_json('['), '[]')
    
    def test_unclosed_string(self):
        """Test completing JSON with unclosed strings"""
        self.assertEqual(complete_truncated_json('{"key": "value'), '{"key": "value"}')
        self.assertEqual(complete_truncated_json('{"key": "val'), '{"key": "val"}')
        self.assertEqual(complete_truncated_json('{"a": "b", "c": "d'), '{"a": "b", "c": "d"}')
    
    def test_unclosed_string_with_closing_brace(self):
        """Test special case of unclosed string with closing brace"""
        self.assertEqual(complete_truncated_json('{"key": "value}'), '{"key": "value"}')
        self.assertEqual(complete_truncated_json('{"text": "has } in it}'), '{"text": "has } in it"}')
    
    def test_mixed_brackets_and_braces(self):
        """Test completing JSON with mixed brackets and braces"""
        self.assertEqual(complete_truncated_json('[{"a": "b"'), '[{"a": "b"}]')
        self.assertEqual(complete_truncated_json('{"arr": [1, 2'), '{"arr": [1, 2]}')
        self.assertEqual(complete_truncated_json('[{"a": [{"b": "c"'), '[{"a": [{"b": "c"}]}]')
    
    def test_non_json_text(self):
        """Test with non-JSON text"""
        self.assertEqual(complete_truncated_json("not json"), "not json")
        self.assertEqual(complete_truncated_json("key: value"), "key: value")


class TestExtractFieldValue(unittest.TestCase):
    """Test extract_field_value function"""
    
    def test_extract_simple_string_field(self):
        """Test extracting simple string fields"""
        json_str = '{"name": "John", "age": "30"}'
        self.assertEqual(extract_field_value(json_str, "name"), "John")
        self.assertEqual(extract_field_value(json_str, "age"), "30")
    
    def test_extract_nonexistent_field(self):
        """Test extracting nonexistent fields"""
        json_str = '{"name": "John"}'
        self.assertIsNone(extract_field_value(json_str, "age"))
        self.assertIsNone(extract_field_value(json_str, "address"))
    
    def test_extract_from_empty_string(self):
        """Test extracting from empty string"""
        self.assertIsNone(extract_field_value("", "field"))
        self.assertIsNone(extract_field_value("   ", "field"))
    
    def test_extract_field_with_escaped_quotes(self):
        """Test extracting fields containing escaped quotes"""
        json_str = r'{"quote": "She said \"Hello\""}'
        self.assertEqual(extract_field_value(json_str, "quote"), 'She said "Hello"')
        
        json_str = r'{"path": "C:\\Users\\file.txt"}'
        self.assertEqual(extract_field_value(json_str, "path"), "C:\\Users\\file.txt")
    
    def test_extract_field_with_newlines(self):
        """Test extracting fields containing newlines"""
        json_str = r'{"text": "Line 1\nLine 2\nLine 3"}'
        self.assertEqual(extract_field_value(json_str, "text"), "Line 1\nLine 2\nLine 3")
    
    def test_extract_narrative_field(self):
        """Test extracting narrative field (special handling)"""
        # Complete narrative
        json_str = '{"narrative": "Once upon a time..."}'
        self.assertEqual(extract_field_value(json_str, "narrative"), "Once upon a time...")
        
        # Narrative with quotes
        json_str = r'{"narrative": "She said \"Hello\" to him."}'
        self.assertEqual(extract_field_value(json_str, "narrative"), 'She said "Hello" to him.')
        
        # Incomplete narrative (truncated)
        json_str = '{"narrative": "This is a very long story that'
        self.assertEqual(extract_field_value(json_str, "narrative"), "This is a very long story that")
    
    def test_extract_from_malformed_json(self):
        """Test extracting from malformed JSON"""
        # Missing quotes around field name
        malformed = '{name: "John"}'
        self.assertIsNone(extract_field_value(malformed, "name"))
        
        # Missing closing quote
        malformed = '{"name": "John'
        self.assertEqual(extract_field_value(malformed, "name"), "John")
        
        # Extra commas
        malformed = '{"name": "John",, "age": "30"}'
        self.assertEqual(extract_field_value(malformed, "name"), "John")
    
    def test_extract_nested_field(self):
        """Test that nested fields are not extracted (only top-level)"""
        json_str = '{"user": {"name": "John"}, "name": "Company"}'
        # Should get top-level name, not nested one
        self.assertEqual(extract_field_value(json_str, "name"), "Company")
    
    def test_extract_field_with_special_characters(self):
        """Test extracting fields with special characters"""
        json_str = r'{"special": "Tab:\t Newline:\n Quote:\" Backslash:\\"}'
        expected = 'Tab:\t Newline:\n Quote:" Backslash:\\'
        self.assertEqual(extract_field_value(json_str, "special"), expected)
    
    def test_extract_empty_string_value(self):
        """Test extracting empty string values"""
        json_str = '{"empty": "", "name": "John"}'
        self.assertEqual(extract_field_value(json_str, "empty"), "")
    
    def test_extract_with_trailing_backslash(self):
        """Test extracting incomplete string with trailing backslash"""
        # This can happen with truncated JSON
        json_str = '{"text": "incomplete\\'
        self.assertEqual(extract_field_value(json_str, "text"), "incomplete")
        
        json_str = '{"narrative": "story ends with\\\\'
        self.assertEqual(extract_field_value(json_str, "narrative"), "story ends with\\\\")


if __name__ == '__main__':
    unittest.main()