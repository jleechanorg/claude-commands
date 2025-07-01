"""
Comprehensive unit tests for debug mode parser.
"""
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from debug_mode_parser import DebugModeParser


class TestDebugModeParser(unittest.TestCase):
    """Test the debug mode command parser."""
    
    def test_enable_commands_basic(self):
        """Test basic enable commands."""
        test_cases = [
            "enable debug mode",
            "debug mode on",
            "debug on",
            "turn on debug mode",
            "turn debug mode on",
            "activate debug mode",
            "debug mode enable",
            "set debug mode on",
            "start debug mode",
        ]
        
        for cmd in test_cases:
            with self.subTest(cmd=cmd):
                result, should_update = DebugModeParser.parse_debug_command(cmd, 'god')
                self.assertEqual(result, 'enable', f"Failed to parse: {cmd}")
                self.assertTrue(should_update)
    
    def test_enable_commands_with_punctuation(self):
        """Test enable commands with punctuation."""
        test_cases = [
            "enable debug mode.",
            "enable debug mode!",
            "debug mode: on",
            "debug: enable",
        ]
        
        for cmd in test_cases:
            with self.subTest(cmd=cmd):
                result, _ = DebugModeParser.parse_debug_command(cmd, 'god')
                self.assertEqual(result, 'enable', f"Failed to parse: {cmd}")
    
    def test_enable_commands_variations(self):
        """Test enable command variations."""
        test_cases = [
            "debugmode on",
            "debug-mode on",
            "enable debugging",
            "enable debug",
            "debugging on",
        ]
        
        for cmd in test_cases:
            with self.subTest(cmd=cmd):
                result, _ = DebugModeParser.parse_debug_command(cmd, 'god')
                self.assertEqual(result, 'enable', f"Failed to parse: {cmd}")
    
    def test_enable_commands_conversational(self):
        """Test conversational enable commands."""
        test_cases = [
            "i want to enable debug mode",
            "please enable debug mode",
            "can you enable debug mode",
            "can you enable debug mode?",
            "let's turn on debug mode",
            "lets turn on debug mode",
            "show me debug mode",
            "show debug info",
        ]
        
        for cmd in test_cases:
            with self.subTest(cmd=cmd):
                result, _ = DebugModeParser.parse_debug_command(cmd, 'god')
                self.assertEqual(result, 'enable', f"Failed to parse: {cmd}")
    
    def test_disable_commands_basic(self):
        """Test basic disable commands."""
        test_cases = [
            "disable debug mode",
            "debug mode off",
            "debug off",
            "turn off debug mode",
            "turn debug mode off",
            "deactivate debug mode",
            "debug mode disable",
            "set debug mode off",
            "stop debug mode",
            "exit debug mode",
            "quit debug mode",
        ]
        
        for cmd in test_cases:
            with self.subTest(cmd=cmd):
                result, should_update = DebugModeParser.parse_debug_command(cmd, 'god')
                self.assertEqual(result, 'disable', f"Failed to parse: {cmd}")
                self.assertTrue(should_update)
    
    def test_disable_commands_variations(self):
        """Test disable command variations."""
        test_cases = [
            "debugmode off",
            "debug-mode off",
            "disable debugging",
            "disable debug",
            "debugging off",
            "hide debug mode",
            "hide debug info",
            "no more debug mode",
        ]
        
        for cmd in test_cases:
            with self.subTest(cmd=cmd):
                result, _ = DebugModeParser.parse_debug_command(cmd, 'god')
                self.assertEqual(result, 'disable', f"Failed to parse: {cmd}")
    
    def test_case_insensitive(self):
        """Test that parsing is case insensitive."""
        test_cases = [
            ("ENABLE DEBUG MODE", 'enable'),
            ("Debug Mode ON", 'enable'),
            ("DeBuG oN", 'enable'),
            ("DISABLE debug MODE", 'disable'),
            ("Debug OFF", 'disable'),
        ]
        
        for cmd, expected in test_cases:
            with self.subTest(cmd=cmd):
                result, _ = DebugModeParser.parse_debug_command(cmd, 'god')
                self.assertEqual(result, expected, f"Failed case insensitive: {cmd}")
    
    def test_extra_whitespace(self):
        """Test handling of extra whitespace."""
        test_cases = [
            ("  enable   debug   mode  ", 'enable'),
            ("\tenable\tdebug\tmode\t", 'enable'),
            ("enable  debug  mode", 'enable'),
            ("   disable   debug   mode   ", 'disable'),
        ]
        
        for cmd, expected in test_cases:
            with self.subTest(cmd=cmd):
                result, _ = DebugModeParser.parse_debug_command(cmd, 'god')
                self.assertEqual(result, expected, f"Failed whitespace handling: {cmd}")
    
    def test_negative_patterns(self):
        """Test that negative patterns don't trigger debug mode."""
        test_cases = [
            "debug the issue",
            "debugging my code",
            "while in debug mode",
            "show debug information about the character",
            "debug this problem",
            "debug the error",
            "i need to debug something",
            "help me debug this",
        ]
        
        for cmd in test_cases:
            with self.subTest(cmd=cmd):
                result, _ = DebugModeParser.parse_debug_command(cmd, 'god')
                self.assertIsNone(result, f"False positive for: {cmd}")
    
    def test_non_debug_commands(self):
        """Test that regular commands don't trigger debug mode."""
        test_cases = [
            "attack the goblin",
            "cast fireball",
            "I walk into the tavern",
            "what do I see?",
            "check my inventory",
            "talk to the merchant",
            "debug",  # Just the word alone
            "mode",
            "on",
            "off",
        ]
        
        for cmd in test_cases:
            with self.subTest(cmd=cmd):
                result, _ = DebugModeParser.parse_debug_command(cmd, 'god')
                self.assertIsNone(result, f"False positive for: {cmd}")
    
    def test_only_works_in_god_mode(self):
        """Test that debug commands only work in god mode."""
        test_cases = [
            "enable debug mode",
            "debug on",
            "disable debug mode",
            "debug off",
        ]
        
        for cmd in test_cases:
            with self.subTest(cmd=cmd):
                # Should work in god mode
                result_god, _ = DebugModeParser.parse_debug_command(cmd, 'god')
                self.assertIsNotNone(result_god, f"Should work in god mode: {cmd}")
                
                # Should NOT work in character mode
                result_char, _ = DebugModeParser.parse_debug_command(cmd, 'character')
                self.assertIsNone(result_char, f"Should not work in character mode: {cmd}")
    
    def test_is_debug_toggle_command(self):
        """Test the quick check method."""
        # Should return True for debug commands
        self.assertTrue(DebugModeParser.is_debug_toggle_command("enable debug mode", 'god'))
        self.assertTrue(DebugModeParser.is_debug_toggle_command("debug off", 'god'))
        
        # Should return False for non-debug commands
        self.assertFalse(DebugModeParser.is_debug_toggle_command("attack goblin", 'god'))
        self.assertFalse(DebugModeParser.is_debug_toggle_command("debug the issue", 'god'))
        
        # Should return False in character mode
        self.assertFalse(DebugModeParser.is_debug_toggle_command("enable debug mode", 'character'))
    
    def test_get_state_update_message(self):
        """Test state update message generation."""
        # Enable messages
        msg = DebugModeParser.get_state_update_message('enable', True)
        self.assertIn("enabled", msg)
        self.assertIn("will now see", msg)
        
        # Disable messages
        msg = DebugModeParser.get_state_update_message('disable', False)
        self.assertIn("disabled", msg)
        self.assertIn("now hidden", msg)
        
        # Already enabled
        msg = DebugModeParser.get_state_update_message('enable', False)
        self.assertIn("already enabled", msg)
        
        # Already disabled
        msg = DebugModeParser.get_state_update_message('disable', True)
        self.assertIn("already disabled", msg)
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        test_cases = [
            # Empty or minimal input
            ("", None),
            (" ", None),
            ("\n", None),
            
            # Partial matches that shouldn't work
            ("enable", None),
            ("debug", None),
            ("mode", None),
            ("enable debug", 'enable'),  # This should work per variations test
            ("debug mode", None),
            
            # Close but not quite
            ("enable debug mod", None),
            ("debug mode o", None),
            ("turn debug on", None),  # Missing "mode"
            
            # Extra text that invalidates
            ("enable debug mode please", 'enable'),  # This should work
            ("please enable debug mode thanks", None),  # Extra at end
            ("hey enable debug mode", None),  # Extra at start
        ]
        
        for cmd, expected in test_cases:
            with self.subTest(cmd=cmd):
                result, _ = DebugModeParser.parse_debug_command(cmd, 'god')
                self.assertEqual(result, expected, f"Edge case failed: '{cmd}'")
    
    def test_similar_but_different_commands(self):
        """Test commands that are similar but shouldn't trigger."""
        test_cases = [
            "enable debug logging",
            "debug mode status",
            "is debug mode on?",
            "check debug mode",
            "debug mode info",
            "what is debug mode",
            "explain debug mode",
        ]
        
        for cmd in test_cases:
            with self.subTest(cmd=cmd):
                result, _ = DebugModeParser.parse_debug_command(cmd, 'god')
                self.assertIsNone(result, f"Similar command false positive: {cmd}")


if __name__ == '__main__':
    unittest.main()