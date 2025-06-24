#!/usr/bin/env python3
"""
Unit tests for the _clean_markdown_from_json function.
Tests individual markdown cleaning patterns to ensure robust JSON extraction.
"""
import unittest
import sys
import os

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from gemini_service import _clean_markdown_from_json, parse_llm_response_for_state_changes
import json

class TestMarkdownCleaning(unittest.TestCase):
    """Unit tests for markdown cleaning functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_json = """{
  "player_character_data": {
    "hp_current": 75
  }
}"""

    def test_clean_json_unchanged(self):
        """Test that clean JSON passes through unchanged."""
        result = _clean_markdown_from_json(self.sample_json)
        self.assertEqual(result, self.sample_json)

    def test_remove_code_blocks(self):
        """Test removal of markdown code blocks."""
        # Test ```json prefix
        input_text = f"```json\n{self.sample_json}\n```"
        result = _clean_markdown_from_json(input_text)
        self.assertEqual(result, self.sample_json)
        
        # Test plain ``` prefix
        input_text = f"```\n{self.sample_json}\n```"
        result = _clean_markdown_from_json(input_text)
        self.assertEqual(result, self.sample_json)

    def test_remove_bold_formatting(self):
        """Test removal of bold markdown (**text**)."""
        # Simple bold wrapping
        input_text = f"**\n{self.sample_json}\n**"
        result = _clean_markdown_from_json(input_text)
        self.assertEqual(result, self.sample_json)
        
        # Bold with whitespace
        input_text = f"**   \n{self.sample_json}   \n**"
        result = _clean_markdown_from_json(input_text)
        self.assertEqual(result, self.sample_json)

    def test_remove_italic_formatting(self):
        """Test removal of italic markdown (*text*)."""
        # Simple italic wrapping  
        input_text = f"*\n{self.sample_json}\n*"
        result = _clean_markdown_from_json(input_text)
        self.assertEqual(result, self.sample_json)

    def test_remove_html_tags(self):
        """Test removal of HTML tags."""
        input_text = f"<strong>\n{self.sample_json}\n</strong>"
        result = _clean_markdown_from_json(input_text)
        self.assertEqual(result, self.sample_json)
        
        # Multiple tags
        input_text = f"<div><strong>\n{self.sample_json}\n</strong></div>"
        result = _clean_markdown_from_json(input_text)
        self.assertEqual(result, self.sample_json)

    def test_mixed_formatting_patterns(self):
        """Test complex mixed formatting patterns."""
        # Bold around code block
        input_text = f"**```json\n{self.sample_json}\n```**"
        result = _clean_markdown_from_json(input_text)
        self.assertEqual(result, self.sample_json)

    def test_remove_commentary_lines(self):
        """Test removal of commentary and decoration lines."""
        # Commentary with asterisks
        input_text = f"*Here's the update:*\n\n```json\n{self.sample_json}\n```\n\n*End of update*"
        result = _clean_markdown_from_json(input_text)
        self.assertEqual(result, self.sample_json)
        
        # Lines with just asterisks
        input_text = f"*****\n{self.sample_json}\n*****"
        result = _clean_markdown_from_json(input_text)
        self.assertEqual(result, self.sample_json)
        
        # Update commentary without asterisks
        input_text = f"Here is the update\n{self.sample_json}\nEnd of update"
        result = _clean_markdown_from_json(input_text)
        self.assertEqual(result, self.sample_json)

    def test_preserve_json_content(self):
        """Test that JSON content with braces/brackets is preserved."""
        # JSON with arrays and nested objects
        complex_json = """{
  "data": {
    "items": [
      {"name": "sword", "damage": 10},
      {"name": "shield", "defense": 5}
    ]
  }
}"""
        
        input_text = f"*Update:*\n```json\n{complex_json}\n```\n*Done*"
        result = _clean_markdown_from_json(input_text)
        self.assertEqual(result, complex_json)

    def test_whitespace_handling(self):
        """Test proper whitespace handling."""
        # Extra whitespace around content
        input_text = f"   \n\n**   \n{self.sample_json}   \n**\n\n   "
        result = _clean_markdown_from_json(input_text)
        self.assertEqual(result, self.sample_json)

    def test_edge_cases(self):
        """Test edge cases and malformed input."""
        # Empty input
        result = _clean_markdown_from_json("")
        self.assertEqual(result, "")
        
        # Only whitespace
        result = _clean_markdown_from_json("   \n\n   ")
        self.assertEqual(result, "")
        
        # Only markdown decorations
        result = _clean_markdown_from_json("*****\n```\n```\n*****")
        self.assertEqual(result, "")

    def test_real_world_patterns(self):
        """Test real-world patterns from the JSON parsing test suite."""
        # Test case 3: Bold markdown wrapping
        input_text = f"**\n{self.sample_json}\n**"
        result = _clean_markdown_from_json(input_text)
        self.assertEqual(result, self.sample_json)
        
        # Test case 4: Mixed markdown formatting
        input_text = f"**```json\n{self.sample_json}\n```**"
        result = _clean_markdown_from_json(input_text)
        self.assertEqual(result, self.sample_json)
        
        # Test case 5: Extra whitespace and asterisks
        input_text = f"   **\n   {self.sample_json.replace('{', '   {').replace('}', '}   ')}\n   **"
        result = _clean_markdown_from_json(input_text)
        # Should still parse as valid JSON structure
        self.assertIn('"player_character_data"', result)
        self.assertIn('"hp_current": 75', result)
        
        # Test case 6: Nested markdown
        input_text = f"*Here's the update:*\n\n```json\n{self.sample_json}\n```\n\n*End of update*"
        result = _clean_markdown_from_json(input_text)
        self.assertEqual(result, self.sample_json)
        
        # Test case 7: HTML-style formatting
        input_text = f"<strong>\n{self.sample_json}\n</strong>"
        result = _clean_markdown_from_json(input_text)
        self.assertEqual(result, self.sample_json)

    def test_function_idempotency(self):
        """Test that running the function multiple times gives same result."""
        input_text = f"**```json\n{self.sample_json}\n```**"
        
        first_clean = _clean_markdown_from_json(input_text)
        second_clean = _clean_markdown_from_json(first_clean)
        third_clean = _clean_markdown_from_json(second_clean)
        
        self.assertEqual(first_clean, self.sample_json)
        self.assertEqual(second_clean, self.sample_json)
        self.assertEqual(third_clean, self.sample_json)

    def test_integration_with_parser(self):
        """Test integration with the main parse_llm_response_for_state_changes function."""
        # Test that markdown-wrapped JSON gets parsed correctly by the main function
        wrapped_response = f"""
Here's my response:

[STATE_UPDATES_PROPOSED]
**```json
{self.sample_json}
```**
[END_STATE_UPDATES_PROPOSED]

That's the update!
"""
        
        result = parse_llm_response_for_state_changes(wrapped_response)
        expected = {"player_character_data": {"hp_current": 75}}
        self.assertEqual(result, expected)

    def test_json_validity_after_cleaning(self):
        """Test that cleaned output is always valid JSON."""
        test_cases = [
            f"**\n{self.sample_json}\n**",
            f"```json\n{self.sample_json}\n```",
            f"*Update:*\n{self.sample_json}\n*Done*",
            f"<strong>{self.sample_json}</strong>",
            f"**```json\n{self.sample_json}\n```**"
        ]
        
        for i, test_case in enumerate(test_cases):
            with self.subTest(case=i):
                cleaned = _clean_markdown_from_json(test_case)
                # Should be valid JSON
                try:
                    parsed = json.loads(cleaned)
                    self.assertIsInstance(parsed, dict)
                    self.assertIn("player_character_data", parsed)
                except json.JSONDecodeError as e:
                    self.fail(f"Cleaned output is not valid JSON: {e}\nCleaned: {repr(cleaned)}")

if __name__ == '__main__':
    print("=== Testing Markdown Cleaning Function ===")
    unittest.main(verbosity=2)