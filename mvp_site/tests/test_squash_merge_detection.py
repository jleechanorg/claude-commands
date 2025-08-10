#!/usr/bin/env python3
"""
Unit tests for squash-merge detection functionality in integrate.sh
Tests the critical bug fixes for false positive detection.
"""

import os
import re
import subprocess
import sys
import unittest

class TestSquashMergeDetection(unittest.TestCase):
    """Test squash-merge detection functionality and bug fixes."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        self.integrate_script = os.path.join(self.project_root, "integrate.sh")
        
        # Ensure integrate.sh exists
        self.assertTrue(
            os.path.exists(self.integrate_script),
            f"integrate.sh not found at {self.integrate_script}"
        )
    
    def test_integrate_script_syntax(self):
        """Test that integrate.sh has valid bash syntax."""
        result = subprocess.run(
            ["bash", "-n", self.integrate_script],
            capture_output=True,
            text=True
        )
        self.assertEqual(
            result.returncode, 0,
            f"integrate.sh has syntax errors: {result.stderr}"
        )
    
    def test_detect_function_exists(self):
        """Test that detect_squash_merged_commits function exists."""
        with open(self.integrate_script, 'r') as f:
            content = f.read()
        
        self.assertIn(
            "detect_squash_merged_commits()",
            content,
            "detect_squash_merged_commits function not found"
        )
    
    def test_regex_bug_fix(self):
        """Test that the sed regex requires at least one digit (POSIX-compatible [0-9][0-9]*)."""
        with open(self.integrate_script, 'r') as f:
            content = f.read()
        
        # Should use POSIX-compatible [0-9][0-9]* (digit followed by zero or more digits)
        self.assertIn(
            "sed 's/ (#[0-9][0-9]*)$//'",
            content,
            "Regex should use POSIX-compatible [0-9][0-9]* pattern"
        )
        
        # Should not use the incorrect single [0-9]* which would match zero digits
        # Note: Our implementation uses [0-9][0-9]* which requires at least one digit
    
    def test_empty_string_check(self):
        """Test that empty string check is present to prevent false positives."""
        with open(self.integrate_script, 'r') as f:
            content = f.read()
        
        # Should have empty string check
        self.assertIn(
            'if [ -z "$base_subject" ]',
            content,
            "Empty string check missing - could cause false positives"
        )
        
        # Should skip processing when empty (continue within the guard)
        guard_re = re.compile(
            r'if\s+\[\s+-z\s+"\$base_subject"\s+\];\s*then.*?\bcontinue\b.*?fi',
            re.DOTALL,
        )
        self.assertRegex(
            content, guard_re,
            "Missing 'continue' within the empty base_subject guard"
        )    
    def test_fixed_strings_flag(self):
        """Test that --fixed-strings flag is used with git log --grep."""
        with open(self.integrate_script, 'r') as f:
            content = f.read()
        
        # Should use --fixed-strings to prevent regex interpretation
        grep_pattern = r'git log.*--fixed-strings.*--grep'
        self.assertTrue(
            re.search(grep_pattern, content, re.DOTALL),
            "--fixed-strings flag missing from git log command"
        )
    
    def test_sed_regex_behavior(self):
        """Test the actual sed regex behavior with various inputs."""
        test_cases = [
            # (input, expected_output, description)
            ("Fix bug (#123)", "Fix bug", "Should strip valid PR number"),
            ("Update docs (#)", "Update docs (#)", "Should NOT strip empty parens"),
            ("Fix issue ( #789)", "Fix issue ( #789)", "Should NOT strip with space before #"),
            ("Something (#abc)", "Something (#abc)", "Should NOT strip non-numeric"),
            (" (#456)", "", "Should result in empty string"),
            ("Normal commit", "Normal commit", "Should leave normal commits unchanged"),
            ("Multiple (#123) and (#456)", "Multiple (#123) and", "Should only strip last occurrence"),
        ]
        
        for input_text, expected, description in test_cases:
            with self.subTest(input=input_text, expected=expected):
                # Test the POSIX-compatible sed regex directly
                result = subprocess.run(
                    ["sed", "s/ (#[0-9][0-9]*)$//"],
                    input=input_text,
                    text=True,
                    capture_output=True
                )
                
                self.assertEqual(result.returncode, 0, f"sed command failed: {result.stderr}")
                
                # Only strip newlines, preserve other whitespace when expected has it
                if expected.endswith(' ') or expected.endswith('\t'):
                    actual_output = result.stdout.rstrip('\n')
                else:
                    actual_output = result.stdout.strip()
                
                self.assertEqual(
                    actual_output, expected,
                    f"{description}: '{input_text}' → '{actual_output}' (expected '{expected}')"
                )
    
    def test_critical_false_positive_cases(self):
        """Test specific cases that would cause false positives."""
        
        # Case 1: Empty subject after stripping would match all commits
        empty_result = subprocess.run(
            ["sed", "s/ (#[0-9][0-9]*)$//"],
            input=" (#123)",
            text=True,
            capture_output=True
        )
        self.assertEqual(empty_result.stdout.strip(), "", 
                        "This case should result in empty string")
        
        # Case 2: Pattern without digits should not be stripped
        no_digits_result = subprocess.run(
            ["sed", "s/ (#[0-9][0-9]*)$//"],
            input="Update docs (#)",
            text=True,
            capture_output=True
        )
        self.assertEqual(no_digits_result.stdout.strip(), "Update docs (#)",
                        "Pattern without digits should not be stripped")
    
    def test_function_integration_points(self):
        """Test that the function is called at the right place in integrate.sh."""
        with open(self.integrate_script, 'r') as f:
            content = f.read()
        
        # Should be called when checking commits not in origin/main
        self.assertIn(
            "if detect_squash_merged_commits $commit_count; then",
            content,
            "Function should be called with commit count parameter"
        )
    
    def test_error_handling_and_safety(self):
        """Test that the function has proper error handling."""
        with open(self.integrate_script, 'r') as f:
            content = f.read()
        
        # Should handle git command failures gracefully
        self.assertIn(
            "2>/dev/null",
            content,
            "Should suppress git error output"
        )
        
        # Should check if commit_subject is not empty before processing
        self.assertIn(
            'if [ -n "$commit_subject" ]',
            content,
            "Should check that commit_subject is not empty"
        )


class TestSquashMergeRegexEdgeCases(unittest.TestCase):
    """Additional edge case tests for the regex patterns."""
    
    def test_regex_anchoring(self):
        """Test that regex is properly anchored to end of string."""
        test_cases = [
            ("Fix (#123) bug", "Fix (#123) bug"),  # Should not match in middle
            ("Fix bug (#123)", "Fix bug"),         # Should match at end
            ("Fix (#123) and (#456)", "Fix (#123) and"),  # Should only match last
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(input=input_text):
                result = subprocess.run(
                    ["sed", "s/ (#[0-9][0-9]*)$//"],
                    input=input_text,
                    text=True,
                    capture_output=True
                )
                
                actual = result.stdout.strip()
                self.assertEqual(actual, expected,
                    f"'{input_text}' → '{actual}' (expected '{expected}')")
    
    def test_whitespace_handling(self):
        """Test proper whitespace handling in regex."""
        test_cases = [
            ("Fix  (#123)", "Fix "),         # Double space - should preserve one space
            ("Fix\t(#123)", "Fix\t(#123)"), # Tab doesn't match (regex requires space)
            ("Fix(#123)", "Fix(#123)"),     # No space - should not match
        ]
        
        for input_text, expected in test_cases:
            with self.subTest(input=input_text):
                result = subprocess.run(
                    ["sed", "s/ (#[0-9][0-9]*)$//"],
                    input=input_text,
                    text=True,
                    capture_output=True
                )
                
                # Preserve trailing whitespace for accurate comparison
                if expected.endswith(' ') or expected.endswith('\t'):
                    actual = result.stdout.rstrip('\n')
                else:
                    actual = result.stdout.strip()
                    
                self.assertEqual(actual, expected,
                    f"'{repr(input_text)}' → '{repr(actual)}' (expected '{repr(expected)}')")


if __name__ == '__main__':
    unittest.main(verbosity=2)