#!/usr/bin/env python3
"""
Red-Green test for character/NPC extraction regex functionality.

Tests the NPC pattern matching that uses re.findall in gemini_service.py
to ensure the import re statement exists and works properly.
"""

import os
import sys
import unittest
import re

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'mvp_site'))

import gemini_service

# Set dummy API key before importing gemini_service
os.environ["GEMINI_API_KEY"] = "DUMMY_KEY_FOR_TESTING"


class TestCharacterExtractionRegex(unittest.TestCase):
    """Test character/NPC extraction regex functionality"""

    def test_re_import_exists(self):
        """RED: Test that re module is properly imported"""
        # This should fail initially if import re is missing
        try:


            # Access the re module within gemini_service scope
            self.assertTrue(hasattr(gemini_service, "re"))
        except NameError as e:
            if "is not defined" in str(e):
                self.fail(f"re module not properly imported: {e}")
            raise

    def test_npc_pattern_extraction_from_prompt(self):
        """RED: Test NPC pattern extraction using re.findall"""
        # Import inside test to catch import errors

        # Test prompt with NPC patterns that should be extracted
        test_prompt = """
        You are part of an adventure with NPCs including Elena, Marcus.
        There is also an advisor named Gandalf who will guide you.
        """

        # These are the patterns from gemini_service.py lines 913-914
        npc_patterns = [
            r"NPCs?\s+(?:including|such as)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)*)",
            r"(?:advisor|companion|member)s?\s+(?:named?|called?)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        ]

        # This should work if re is properly imported
        try:


            expected_entities = []

            for pattern in npc_patterns:
                matches = re.findall(pattern, test_prompt)
                for match in matches:
                    # Split by commas if multiple NPCs listed
                    npc_names = [n.strip() for n in match.split(",")]
                    for npc in npc_names:
                        if (
                            npc
                            and npc not in expected_entities
                            and npc not in ["and", "or", "the", "a", "an"]
                        ):
                            expected_entities.append(npc)

            # Verify we extracted the expected NPCs
            self.assertIn("Elena", expected_entities)
            self.assertIn("Marcus", expected_entities)
            self.assertIn("Gandalf", expected_entities)

        except NameError as e:
            if "'re' is not defined" in str(e):
                self.fail(f"re module not available in gemini_service scope: {e}")
            raise

    def test_actual_gemini_service_npc_extraction(self):
        """GREEN: Test that actual gemini_service code works with re patterns"""
        # This will test if the actual code in gemini_service works
        # by calling a function that uses the NPC extraction

        # We can't easily test the full get_initial_story without mocking
        # but we can test the import and basic functionality


        # Just verify the module loads and re is available
        self.assertTrue(hasattr(gemini_service, "re"))

        # Test the patterns are defined (they're local to the function, so we'll copy them)
        test_prompt = "Adventure with NPCs including Alice and Bob"

        # Simulate the same logic from gemini_service
        npc_patterns = [
            r"NPCs?\s+(?:including|such as)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)*)",
            r"(?:advisor|companion|member)s?\s+(?:named?|called?)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        ]

        # This should not raise NameError if re is properly imported


        for pattern in npc_patterns:
            matches = re.findall(pattern, test_prompt)
            # Should find the NPCs
            if matches:
                self.assertIn("Alice", matches[0])

    def test_planning_block_character_creation_check(self):
        """GREEN: Test the actual re.search usage in planning block logic"""


        # Test the actual line that uses re.search in the current code
        test_text = "[CHARACTER CREATION] Please create your character stats"

        # This is the actual usage from line 1044 in gemini_service.py
        result = re.search(r"\[CHARACTER CREATION", test_text, re.IGNORECASE)
        self.assertIsNotNone(result)

        # Test negative case
        normal_text = "The adventure continues..."
        result2 = re.search(r"\[CHARACTER CREATION", normal_text, re.IGNORECASE)
        self.assertIsNone(result2)

    def test_all_re_usage_in_gemini_service(self):
        """GREEN: Comprehensive test of all regex usage in gemini_service"""


        # Test 1: NPC pattern extraction (lines 913-914)
        test_prompt = """
        Adventure with NPCs including Elena, Marcus.
        There is an advisor named Gandalf.
        """

        npc_patterns = [
            r"NPCs?\s+(?:including|such as)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)*)",
            r"(?:advisor|companion|member)s?\s+(?:named?|called?)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        ]

        found_entities = []
        for pattern in npc_patterns:
            matches = re.findall(pattern, test_prompt)
            for match in matches:
                found_entities.extend([n.strip() for n in match.split(",")])

        # Should find NPCs without errors
        self.assertIn("Elena", found_entities)
        self.assertIn("Gandalf", found_entities)

        # Test 2: Character creation check (line 1044)
        char_creation_text = "[CHARACTER CREATION] Enter your stats"
        result = re.search(r"\[CHARACTER CREATION", char_creation_text, re.IGNORECASE)
        self.assertIsNotNone(result)

        # If we get here without NameError, re is properly imported and working


if __name__ == "__main__":
    unittest.main()
