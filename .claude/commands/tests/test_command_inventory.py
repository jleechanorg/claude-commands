#!/usr/bin/env python3
"""
Test that verifies the command system integrity after removing over-engineered composition system.
Focuses on basic command file inventory and structure validation.
"""

import os
import sys
import unittest
from pathlib import Path


class TestCommandInventory(unittest.TestCase):
    """Test basic command system integrity"""
    
    def setUp(self):
        """Set up test data"""
        # Find commands directory 
        test_file_dir = Path(__file__).parent.parent
        if test_file_dir.name == "commands":
            self.commands_dir = test_file_dir
        else:
            # If running from project root
            self.commands_dir = Path(__file__).parent.parent.parent.parent / ".claude" / "commands"
        
        # Scan actual command files
        self.actual_commands = self._scan_command_files()
        
    def _scan_command_files(self):
        """Scan .claude/commands/ directory for command definitions"""
        commands = set()
        
        # Look for .md files (command definitions)
        for md_file in self.commands_dir.glob("*.md"):
            if (not md_file.name.startswith("test-") and 
                not md_file.name.upper().startswith("SIMPLIFICATION") and
                not md_file.name.upper().startswith("README")):  # Skip documentation files
                command_name = f"/{md_file.stem}"
                commands.add(command_name)
            
        # Look for .py files that might be commands (exclude test files and utilities)
        for py_file in self.commands_dir.glob("*.py"):
            if (not py_file.name.startswith("test_") and 
                not py_file.name.startswith("copilot_")):
                command_name = f"/{py_file.stem}"
                commands.add(command_name)
        
        # Remove known utilities and non-commands
        non_commands = {
            "/lint_utils", "/save_mcp_queue", "/header_check", 
            "/fake_detector", "/request_optimizer", "/pr_utils",
            "/copilot_analyzer", "/copilot_implementer", "/copilot_reporter",
            "/copilot_safety", "/copilot_verifier", "/copilot_expansion_analysis"
        }
        commands -= non_commands
        
        return commands
    
    def test_essential_commands_present(self):
        """Test that essential commands are present"""
        
        # Essential commands that should always be present
        essential_commands = {
            "/test", "/execute", "/coverage", "/learn", "/pr", 
            "/push", "/integrate", "/newbranch", "/arch", "/review"
        }
        
        missing_essential = essential_commands - self.actual_commands
        if missing_essential:
            self.fail(
                f"Missing essential commands: {sorted(missing_essential)}\n"
                f"These core commands must be present in the system"
            )
    
    def test_reasonable_command_count(self):
        """Test that we have reasonable numbers of commands"""
        
        command_count = len(self.actual_commands)
        
        # Should have reasonable minimum counts
        self.assertGreaterEqual(command_count, 20,
            f"Expected at least 20 commands, got {command_count}")
        
        # Should not have excessive counts (sanity check)
        self.assertLessEqual(command_count, 150,
            f"Commands seem excessive: {command_count}. Review command inventory.")
    
    def test_no_over_engineered_composition_files(self):
        """Test that over-engineered composition files have been removed"""
        
        removed_files = [
            "composition_hook.py",
            "combinations.md", 
            "combo-help.md",
            "integration_example.py"
        ]
        
        for filename in removed_files:
            file_path = self.commands_dir / filename
            self.assertFalse(file_path.exists(), 
                f"Over-engineered file {filename} should have been removed")
    
    def test_command_files_readable(self):
        """Test that command files are properly formatted"""
        
        for md_file in self.commands_dir.glob("*.md"):
            if (not md_file.name.startswith("test-") and 
                not md_file.name.upper().startswith("SIMPLIFICATION") and
                not md_file.name.upper().startswith("README")):  # Skip documentation files
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Basic validation - should have content
                    self.assertGreater(len(content.strip()), 10,
                        f"Command file {md_file.name} appears to be empty or too short")
                    # Should have usage or description
                    content_lower = content.lower()
                    self.assertTrue(
                        'usage' in content_lower or 'description' in content_lower,
                        f"Command file {md_file.name} should have Usage or Description section"
                    )


def print_command_inventory():
    """Print current command inventory for debugging"""
    
    test_file_dir = Path(__file__).parent.parent
    if test_file_dir.name == "commands":
        commands_dir = test_file_dir
    else:
        commands_dir = Path(__file__).parent.parent.parent.parent / ".claude" / "commands"
    
    print("\n" + "="*60)
    print("COMMAND INVENTORY SUMMARY")
    print("="*60)
    
    md_files = sorted([f"/{f.stem}" for f in commands_dir.glob("*.md") 
                      if (not f.name.startswith("test-") and 
                          not f.name.upper().startswith("SIMPLIFICATION") and
                          not f.name.upper().startswith("README"))])
    py_files = sorted([f"/{f.stem}" for f in commands_dir.glob("*.py") 
                      if not f.name.startswith("test_") and not f.name.startswith("copilot_")])
    
    print(f"\nMARKDOWN COMMANDS ({len(md_files)}):")
    for cmd in md_files:
        print(f"  {cmd}")
    
    print(f"\nPYTHON COMMANDS ({len(py_files)}):")
    for cmd in py_files:
        print(f"  {cmd}")
    
    print(f"\nTOTAL COMMANDS: {len(md_files) + len(py_files)}")
    print("="*60)


if __name__ == "__main__":
    # Print inventory for debugging
    print_command_inventory()
    
    # Run tests
    unittest.main(verbosity=2)