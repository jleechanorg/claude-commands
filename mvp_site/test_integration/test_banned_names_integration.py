#!/usr/bin/env python3
"""
Unit tests for banned names integration in WorldArchitect.AI
"""

import os
import sys
import unittest
from unittest.mock import mock_open, patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from world_loader import load_banned_names, load_world_content_for_system_instruction


class TestBannedNamesIntegration(unittest.TestCase):
    """Test banned names loading and integration"""

    def setUp(self):
        """Set up test data"""
        self.sample_banned_names = """# Banned Names

These names are overused by LLMs and cannot be used in any world content.

## Banned Names List

### Primary Banned Names (Original)
- Alaric
- Blackwood
- Corvus
- Elara
- Valerius
"""

        self.sample_book_content = "Book content here"
        self.sample_world_content = "World content here"

    def test_load_banned_names_success(self):
        """Test successful loading of banned names"""
        with patch("builtins.open", mock_open(read_data=self.sample_banned_names)):
            with patch("os.path.join") as mock_join:
                mock_join.return_value = "mocked_path"

                result = load_banned_names()

                # The function strips the content, so compare stripped version
                self.assertEqual(result, self.sample_banned_names.strip())
                self.assertIn("Alaric", result)
                self.assertIn("Corvus", result)
                self.assertIn("Valerius", result)

    def test_load_banned_names_file_not_found(self):
        """Test behavior when banned names file is not found"""
        with patch("builtins.open", side_effect=FileNotFoundError):
            with patch("logging.warning") as mock_warning:
                result = load_banned_names()

                self.assertEqual(result, "")
                mock_warning.assert_called_once()
                self.assertIn(
                    "Banned names file not found", mock_warning.call_args[0][0]
                )

    def test_load_banned_names_general_error(self):
        """Test behavior when general error occurs loading banned names"""
        with patch("builtins.open", side_effect=Exception("Test error")):
            with patch("logging.error") as mock_error:
                result = load_banned_names()

                self.assertEqual(result, "")
                mock_error.assert_called_once()
                self.assertIn("Error loading banned names", mock_error.call_args[0][0])

    @patch("world_loader.load_banned_names")
    def test_world_content_includes_banned_names(self, mock_load_banned):
        """Test that world content includes banned names section"""
        mock_load_banned.return_value = self.sample_banned_names

        # Mock file reads for book and world content
        mock_files = {
            "book_path": self.sample_book_content,
            "world_path": self.sample_world_content,
        }

        def mock_open_file(path, *args, **kwargs):
            class MockFile:
                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    pass

                def read(self):
                    if "celestial_wars" in str(path):
                        return mock_files["book_path"]
                    if "world_assiah" in str(path):
                        return mock_files["world_path"]
                    return ""

                def strip(self):
                    return self.read().strip()

            return MockFile()

        with patch("builtins.open", side_effect=mock_open_file):
            with patch("os.path.join") as mock_join:
                mock_join.side_effect = lambda *args: "/".join(args)

                result = load_world_content_for_system_instruction()

                # Check structure
                self.assertIn("WORLD CONTENT FOR CAMPAIGN CONSISTENCY", result)
                self.assertIn("PRIMARY CANON - CELESTIAL WARS ALEXIEL BOOK", result)
                self.assertIn("SECONDARY CANON - WORLD OF ASSIAH DOCUMENTATION", result)
                self.assertIn("CRITICAL NAMING RESTRICTIONS", result)

                # Check banned names content
                self.assertIn("Banned Names", result)
                self.assertIn("must NEVER be used", result)

                # Check enforcement text
                self.assertIn("Enforcement", result)
                self.assertIn("New NPCs being introduced", result)
                self.assertIn("Player character suggestions", result)

                # Check world consistency rules
                self.assertIn(
                    "7. **Name Restrictions**: NEVER use any name from the banned names list",
                    result,
                )

    def test_banned_names_in_critical_section(self):
        """Test that banned names appear in the critical naming restrictions section"""
        with patch(
            "world_loader.load_banned_names", return_value=self.sample_banned_names
        ):
            with patch("builtins.open", mock_open(read_data="dummy content")):
                with patch("os.path.join") as mock_join:
                    mock_join.side_effect = lambda *args: "/".join(args)

                    result = load_world_content_for_system_instruction()

                    # Find the critical naming restrictions section
                    critical_start = result.find("CRITICAL NAMING RESTRICTIONS")
                    self.assertNotEqual(
                        critical_start,
                        -1,
                        "CRITICAL NAMING RESTRICTIONS section not found",
                    )

                    # Find where it ends (next --- marker)
                    critical_end = result.find("---", critical_start + 1)
                    critical_section = result[critical_start:critical_end]

                    # Check that banned names are in this section
                    self.assertIn("Alaric", critical_section)
                    self.assertIn("Corvus", critical_section)
                    self.assertIn("Elara", critical_section)
                    self.assertIn("Valerius", critical_section)

    def test_specific_banned_names_present(self):
        """Test that specific problematic names are included"""
        # Test only the names that are actually in our sample data
        names_to_test = ["Alaric", "Blackwood", "Corvus", "Elara", "Valerius"]

        with patch(
            "world_loader.load_banned_names", return_value=self.sample_banned_names
        ):
            with patch("builtins.open", mock_open(read_data="dummy content")):
                with patch("os.path.join") as mock_join:
                    mock_join.side_effect = lambda *args: "/".join(args)

                    result = load_world_content_for_system_instruction()

                    for name in names_to_test:
                        self.assertIn(
                            name,
                            result,
                            f"Banned name '{name}' not found in world content",
                        )

    def test_enforcement_instructions_complete(self):
        """Test that enforcement instructions are complete"""
        with patch(
            "world_loader.load_banned_names", return_value=self.sample_banned_names
        ):
            with patch("builtins.open", mock_open(read_data="dummy content")):
                with patch("os.path.join") as mock_join:
                    mock_join.side_effect = lambda *args: "/".join(args)

                    result = load_world_content_for_system_instruction()

                    # Check all enforcement categories
                    enforcement_items = [
                        "New NPCs being introduced",
                        "Player character suggestions",
                        "Location names",
                        "Organization names",
                        "Any other named entity",
                    ]

                    for item in enforcement_items:
                        self.assertIn(
                            item, result, f"Enforcement item '{item}' not found"
                        )

    def test_world_consistency_rules_updated(self):
        """Test that world consistency rules include name restrictions"""
        with patch(
            "world_loader.load_banned_names", return_value=self.sample_banned_names
        ):
            with patch("builtins.open", mock_open(read_data="dummy content")):
                with patch("os.path.join") as mock_join:
                    mock_join.side_effect = lambda *args: "/".join(args)

                    result = load_world_content_for_system_instruction()

                    # Check that rule #7 exists
                    self.assertIn(
                        "7. **Name Restrictions**: NEVER use any name from the banned names list",
                        result,
                    )


class TestBannedNamesRealFile(unittest.TestCase):
    """Test with the actual banned_names.md file if it exists"""

    def setUp(self):
        """Check if we're in the right directory structure"""
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.mvp_site_dir = os.path.dirname(self.script_dir)
        self.world_dir = os.path.join(self.mvp_site_dir, "world")
        self.banned_names_path = os.path.join(self.world_dir, "banned_names.md")

    def test_real_banned_names_file_exists(self):
        """Test that the real banned names file exists and has content"""
        if os.path.exists(self.banned_names_path):
            with open(self.banned_names_path) as f:
                content = f.read()

            # Check file has substantial content
            self.assertGreater(len(content), 500, "Banned names file seems too short")

            # Check for expected sections
            self.assertIn("# Banned Names", content)
            self.assertIn("Primary Banned Names", content)
            self.assertIn("Extended Banned Names", content)

            # Check for some specific names
            key_names = [
                "Alaric",
                "Corvus",
                "Elara",
                "Valerius",
                "Aria",
                "Phoenix",
                "Raven",
            ]
            for name in key_names:
                self.assertIn(name, content, f"Expected banned name '{name}' not found")

            # Check there are at least 50 names (rough count of lines with "- ")
            name_lines = [
                line for line in content.split("\n") if line.strip().startswith("- ")
            ]
            self.assertGreaterEqual(
                len(name_lines), 50, "Expected at least 50 banned names"
            )


if __name__ == "__main__":
    unittest.main()
