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

        self.sample_book_content = "PRIMARY CANON - CELESTIAL WARS ALEXIEL BOOK content here"
        self.sample_world_content = "# World of Assiah - Compressed Campaign Guide\n\nWorld content here"

    def test_load_banned_names_success(self):
        """Test successful loading of banned names"""
        with patch("builtins.open", mock_open(read_data=self.sample_banned_names)):
            with patch("os.path.join") as mock_join:
                mock_join.return_value = "mocked_path"

                result = load_banned_names()

                # The function strips the content, so compare stripped version
                assert result == self.sample_banned_names.strip()
                assert "Alaric" in result
                assert "Corvus" in result
                assert "Valerius" in result

    def test_load_banned_names_file_not_found(self):
        """Test behavior when banned names file is not found"""
        with patch("builtins.open", side_effect=FileNotFoundError):
            with patch("logging_util.warning") as mock_warning:
                result = load_banned_names()

                assert result == ""
                mock_warning.assert_called_once()
                assert "Banned names file not found" in mock_warning.call_args[0][0]

    def test_load_banned_names_general_error(self):
        """Test behavior when general error occurs loading banned names"""
        with patch("builtins.open", side_effect=Exception("Test error")):
            with patch("logging_util.warning") as mock_error:
                result = load_banned_names()

                assert result == ""
                mock_error.assert_called_once()
                assert "Could not load banned names file" in mock_error.call_args[0][0]

    @patch("world_loader.load_banned_names")
    @patch("world_loader.read_file_cached", autospec=True)
    def test_world_content_includes_banned_names(self, mock_read_file_cached, mock_load_banned):
        """Test that world content includes banned names section"""
        mock_load_banned.return_value = self.sample_banned_names
        
        # Mock the cached file reader to return our test content
        def mock_read_file_side_effect(filepath, encoding="utf-8"):
            if "world_assiah" in str(filepath) or "assiah" in str(filepath):
                return self.sample_world_content
            return ""
        
        mock_read_file_cached.side_effect = mock_read_file_side_effect
        
        with patch("os.path.join") as mock_join:
            mock_join.side_effect = lambda *args: "/".join(args)

            result = load_world_content_for_system_instruction()

            # Check structure
            assert "WORLD CONTENT FOR CAMPAIGN CONSISTENCY" in result
            assert "# World of Assiah - Compressed Campaign Guide" in result
            assert "WORLD CANON - INTEGRATED CAMPAIGN GUIDE" in result
            assert "CRITICAL NAMING RESTRICTIONS" in result

            # Check banned names content
            assert "Banned Names" in result
            assert "must NEVER be used" in result

            # Check enforcement text
            assert "Enforcement" in result
            assert "New NPCs being introduced" in result
            assert "Player character suggestions" in result

            # Check world consistency rules
            assert (
                "6. **Name Restrictions**: NEVER use any name from the CRITICAL NAMING RESTRICTIONS section"
                in result
            )

    @patch("world_loader.load_banned_names") 
    @patch("world_loader.read_file_cached", autospec=True)
    def test_banned_names_in_critical_section(self, mock_read_file_cached, mock_load_banned):
        """Test that banned names appear in the critical naming restrictions section"""
        mock_load_banned.return_value = self.sample_banned_names
        mock_read_file_cached.return_value = self.sample_world_content
        
        with patch("os.path.join") as mock_join:
            mock_join.side_effect = lambda *args: "/".join(args)

            result = load_world_content_for_system_instruction()

            # Find the critical naming restrictions section
            critical_start = result.find("CRITICAL NAMING RESTRICTIONS")
            assert (
                critical_start != -1
            ), "CRITICAL NAMING RESTRICTIONS section not found"

            # Find where it ends (next --- marker)
            critical_end = result.find("---", critical_start + 1)
            critical_section = result[critical_start:critical_end]

            # Check that banned names are in this section
            assert "Alaric" in critical_section
            assert "Corvus" in critical_section
            assert "Elara" in critical_section
            assert "Valerius" in critical_section

    @patch("world_loader.load_banned_names")
    @patch("world_loader.read_file_cached", autospec=True)
    def test_specific_banned_names_present(self, mock_read_file_cached, mock_load_banned):
        """Test that specific problematic names are included"""
        # Test only the names that are actually in our sample data
        names_to_test = ["Alaric", "Blackwood", "Corvus", "Elara", "Valerius"]

        mock_load_banned.return_value = self.sample_banned_names
        mock_read_file_cached.return_value = self.sample_world_content
        
        with patch("os.path.join") as mock_join:
            mock_join.side_effect = lambda *args: "/".join(args)

            result = load_world_content_for_system_instruction()

            for name in names_to_test:
                assert (
                    name in result
                ), f"Banned name '{name}' not found in world content"

    @patch("world_loader.load_banned_names")
    @patch("world_loader.read_file_cached", autospec=True)
    def test_enforcement_instructions_complete(self, mock_read_file_cached, mock_load_banned):
        """Test that enforcement instructions are complete"""
        mock_load_banned.return_value = self.sample_banned_names
        mock_read_file_cached.return_value = self.sample_world_content
        
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
                assert item in result, f"Enforcement item '{item}' not found"

    @patch("world_loader.load_banned_names")
    @patch("world_loader.read_file_cached", autospec=True)
    def test_world_consistency_rules_updated(self, mock_read_file_cached, mock_load_banned):
        """Test that world consistency rules include name restrictions"""
        mock_load_banned.return_value = self.sample_banned_names
        mock_read_file_cached.return_value = self.sample_world_content
        
        with patch("os.path.join") as mock_join:
            mock_join.side_effect = lambda *args: "/".join(args)

            result = load_world_content_for_system_instruction()

            # Check that rule #7 exists
            assert (
                "6. **Name Restrictions**: NEVER use any name from the CRITICAL NAMING RESTRICTIONS section"
                in result
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
            assert len(content) > 500, "Banned names file seems too short"

            # Check for expected sections
            assert "# Banned Names" in content
            assert "Primary Banned Names" in content
            assert "Extended Banned Names" in content

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
                assert name in content, f"Expected banned name '{name}' not found"

            # Check there are at least 50 names (rough count of lines with "- ")
            name_lines = [
                line for line in content.split("\n") if line.strip().startswith("- ")
            ]
            assert len(name_lines) >= 50, "Expected at least 50 banned names"


if __name__ == "__main__":
    unittest.main()
