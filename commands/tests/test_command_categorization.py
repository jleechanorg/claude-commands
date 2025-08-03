#!/usr/bin/env python3
"""
Test that ensures all commands defined in .claude/commands/ are properly
categorized as protocol or natural language modifiers in composition_hook.py
"""

import sys
import unittest
from pathlib import Path

# Add the commands directory to the path so we can import composition_hook
commands_dir = Path(__file__).parent.parent
sys.path.insert(0, str(commands_dir))

try:
    from composition_hook import get_available_commands
except ImportError:
    # If running from project root, try different path
    sys.path.insert(
        0, str(Path(__file__).parent.parent.parent.parent / ".claude" / "commands")
    )
    from composition_hook import get_available_commands


class TestCommandCategorization(unittest.TestCase):
    """Test that all defined commands are properly categorized"""

    def setUp(self):
        """Set up test data"""
        # Try to find the correct commands directory
        test_file_dir = Path(__file__).parent.parent
        if (test_file_dir / "composition_hook.py").exists():
            self.commands_dir = test_file_dir
        else:
            # If running from project root
            self.commands_dir = (
                Path(__file__).parent.parent.parent.parent / ".claude" / "commands"
            )

        self.composition_commands = get_available_commands()

        # Get all categorized commands
        self.protocol_commands = set(self.composition_commands["protocol_commands"])
        self.natural_modifiers = set(self.composition_commands["natural_modifiers"])
        self.all_categorized = self.protocol_commands | self.natural_modifiers

        # Scan actual command files
        self.actual_commands = self._scan_command_files()

    def _scan_command_files(self):
        """Scan .claude/commands/ directory for actual command definitions"""
        commands = set()

        # Look for .md files (command definitions)
        for md_file in self.commands_dir.glob("*.md"):
            command_name = f"/{md_file.stem}"
            commands.add(command_name)

        # Look for .py files that might be commands (exclude test files and utilities)
        for py_file in self.commands_dir.glob("*.py"):
            if (
                not py_file.name.startswith("test_")
                and py_file.name != "composition_hook.py"
                and py_file.name != "integration_example.py"
                and not py_file.name.startswith("copilot_")
            ):
                command_name = f"/{py_file.stem}"
                commands.add(command_name)

        # Remove known utilities and non-commands
        non_commands = {
            "/lint_utils",
            "/save_mcp_queue",
            "/header_check",
            "/fake_detector",
            "/request_optimizer",
            "/pr_utils",
            "/copilot_analyzer",
            "/copilot_implementer",
            "/copilot_reporter",
            "/copilot_safety",
            "/copilot_verifier",
            "/copilot_expansion_analysis",
        }
        commands -= non_commands

        return commands

    def test_all_actual_commands_are_categorized(self):
        """Test that every actual command file has a categorization"""
        uncategorized = self.actual_commands - self.all_categorized

        if uncategorized:
            self.fail(
                f"Found {len(uncategorized)} uncategorized commands: {sorted(uncategorized)}\n"
                f"Please add them to either protocol_commands or natural_modifiers in composition_hook.py"
            )

    def test_no_stale_categorizations(self):
        """Test that categorized commands have corresponding files"""
        missing_files = self.all_categorized - self.actual_commands

        # Allow some exceptions for aliases and virtual natural language modifiers
        allowed_missing = {
            # Command aliases
            "/e",  # Alias for /execute
            "/r",  # Alias for /roadmap
            "/nb",  # Alias for /newbranch
            "/rg",  # Alias for /tdd
            "/con",  # Alias for /context
            "/orch",  # Alias for /orchestrate
            "/thinku",  # Alias for /think ultra
            "/commentr",  # Alias for /commentreply
            # Virtual natural language modifiers (don't need files - interpreted by Claude)
            "/clean",
            "/complete",
            "/deploy",
            "/minimal",
            "/paranoid",
            "/performance",
            "/thorough",
            "/verbose",
        }

        actual_missing = missing_files - allowed_missing

        if actual_missing:
            self.fail(
                f"Found {len(actual_missing)} categorized commands without files: {sorted(actual_missing)}\n"
                f"Please remove them from composition_hook.py or create the missing command files"
            )

    def test_no_duplicate_categorizations(self):
        """Test that no command is in both protocol and natural categories"""
        duplicates = self.protocol_commands & self.natural_modifiers

        if duplicates:
            self.fail(
                f"Found {len(duplicates)} commands in both categories: {sorted(duplicates)}\n"
                f"Each command must be either protocol OR natural, not both"
            )

    def test_categorization_makes_sense(self):
        """Test that categorizations follow expected patterns"""

        # Protocol commands should be actions (verbs)
        action_words = {
            "test",
            "deploy",
            "execute",
            "push",
            "integrate",
            "learn",
            "review",
            "replicate",
            "coverage",
            "arch",
            "optimize",
            "handoff",
            "orchestrate",
            "copilot",
        }

        # Natural modifiers should be adjectives/adverbs
        modifier_words = {
            "debug",
            "paranoid",
            "minimal",
            "complete",
            "think",
            "verbose",
            "thorough",
            "clean",
            "performance",
        }

        # Check that most protocol commands contain action words
        protocol_with_actions = 0
        for cmd in self.protocol_commands:
            cmd_word = cmd.lstrip("/").lower()
            if any(action in cmd_word for action in action_words):
                protocol_with_actions += 1

        # Should have reasonable coverage of action words in protocol commands
        action_coverage = protocol_with_actions / len(self.protocol_commands)
        self.assertGreater(
            action_coverage,
            0.3,
            f"Only {action_coverage:.1%} of protocol commands contain action words. "
            f"Review categorization - protocol commands should be actions.",
        )

        # Check that natural modifiers contain modifier words
        natural_with_modifiers = 0
        for cmd in self.natural_modifiers:
            cmd_word = cmd.lstrip("/").lower()
            if any(modifier in cmd_word for modifier in modifier_words):
                natural_with_modifiers += 1

        # Should have reasonable coverage of modifier words in natural commands
        modifier_coverage = natural_with_modifiers / len(self.natural_modifiers)
        self.assertGreater(
            modifier_coverage,
            0.4,
            f"Only {modifier_coverage:.1%} of natural commands contain modifier words. "
            f"Review categorization - natural commands should be modifiers.",
        )

    def test_essential_commands_present(self):
        """Test that essential commands are properly categorized"""

        # Essential protocol commands that should always be present
        essential_protocol = {"/test", "/execute", "/coverage", "/learn", "/pr"}

        missing_essential = essential_protocol - self.protocol_commands
        if missing_essential:
            self.fail(
                f"Missing essential protocol commands: {sorted(missing_essential)}\n"
                f"These core commands must be categorized as protocol_commands"
            )

        # Essential natural modifiers that should always be present
        essential_natural = {"/debug", "/paranoid", "/minimal", "/think"}

        missing_natural = essential_natural - self.natural_modifiers
        if missing_natural:
            self.fail(
                f"Missing essential natural modifiers: {sorted(missing_natural)}\n"
                f"These core modifiers must be categorized as natural_modifiers"
            )

    def test_categorization_counts_reasonable(self):
        """Test that we have reasonable numbers of each category"""

        protocol_count = len(self.protocol_commands)
        natural_count = len(self.natural_modifiers)

        # Should have more protocol commands than natural modifiers
        self.assertGreater(
            protocol_count,
            natural_count,
            f"Expected more protocol commands ({protocol_count}) than natural modifiers ({natural_count})",
        )

        # Should have reasonable minimum counts
        self.assertGreaterEqual(
            protocol_count,
            20,
            f"Expected at least 20 protocol commands, got {protocol_count}",
        )
        self.assertGreaterEqual(
            natural_count,
            5,
            f"Expected at least 5 natural modifiers, got {natural_count}",
        )

        # Should not have excessive counts (sanity check)
        self.assertLessEqual(
            protocol_count,
            100,
            f"Protocol commands seem excessive: {protocol_count}. Review categorization.",
        )
        self.assertLessEqual(
            natural_count,
            50,
            f"Natural modifiers seem excessive: {natural_count}. Review categorization.",
        )


def print_command_summary():
    """Print a summary of current command categorization for debugging"""
    commands = get_available_commands()

    print("\n" + "=" * 60)
    print("COMMAND CATEGORIZATION SUMMARY")
    print("=" * 60)

    print(f"\nPROTOCOL COMMANDS ({len(commands['protocol_commands'])}):")
    for cmd in sorted(commands["protocol_commands"]):
        print(f"  {cmd}")

    print(f"\nNATURAL MODIFIERS ({len(commands['natural_modifiers'])}):")
    for cmd in sorted(commands["natural_modifiers"]):
        print(f"  {cmd}")

    print(
        f"\nTOTAL COMMANDS: {len(commands['protocol_commands']) + len(commands['natural_modifiers'])}"
    )
    print("=" * 60)


if __name__ == "__main__":
    # Print summary for debugging
    print_command_summary()

    # Run tests
    unittest.main(verbosity=2)
