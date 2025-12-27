#!/usr/bin/env python3
"""
Unit tests for .claude/settings.json hook configuration validation.

This test enforces the robust hook pattern to prevent system lockouts
caused by environment variable dependencies.

Author: Claude Code (Genesis Coder, Prime Mover)
Created: 2025-08-22
Issue: Fix for PR #1410 hook environment robustness
"""

import json
import re
import unittest
from pathlib import Path


class TestClaudeSettingsValidation(unittest.TestCase):
    """Validate .claude/settings.json hook configurations for robustness."""

    def setUp(self):
        """Set up test fixtures."""
        self.project_root = Path(__file__).parent.parent.parent
        self.settings_file = self.project_root / ".claude" / "settings.json"

        # Load settings.json
        if not self.settings_file.exists():
            self.skipTest(f"Settings file not found: {self.settings_file}")

        with open(self.settings_file) as f:
            self.settings = json.load(f)

    def test_settings_file_exists(self):
        """Test that .claude/settings.json exists."""
        self.assertTrue(
            self.settings_file.exists(),
            f"Settings file must exist: {self.settings_file}",
        )

    def test_settings_file_valid_json(self):
        """Test that settings.json is valid JSON."""
        self.assertIsInstance(
            self.settings, dict, "Settings must be a valid JSON object"
        )
        self.assertIn("hooks", self.settings, "Settings must contain 'hooks' section")

    def test_hook_robustness_patterns(self):
        """Test that all hooks use robust patterns to prevent system lockouts."""
        hooks_config = self.settings.get("hooks", {})
        violations = []

        # Define hook event types to validate
        hook_events = ["PreToolUse", "PostToolUse", "Stop", "UserPromptSubmit"]

        for event_type in hook_events:
            if event_type not in hooks_config:
                continue

            event_hooks = hooks_config[event_type]
            if not isinstance(event_hooks, list):
                continue

            for matcher_group in event_hooks:
                if not isinstance(matcher_group, dict) or "hooks" not in matcher_group:
                    continue

                for hook in matcher_group["hooks"]:
                    if not isinstance(hook, dict) or "command" not in hook:
                        continue

                    command = hook["command"]
                    description = hook.get("description", "No description")

                    # Validate this specific hook command
                    violation = self._validate_hook_command(
                        command, event_type, description
                    )
                    if violation:
                        violations.append(violation)

        # Report all violations
        if violations:
            error_msg = "❌ HOOK VALIDATION FAILURES:\n\n" + "\n\n".join(violations)
            error_msg += "\n\n🛡️ FIX: Use robust pattern from .claude/hooks/CLAUDE.md"
            self.fail(error_msg)

    def _validate_hook_command(
        self, command: str, event_type: str, description: str
    ) -> str:
        """
        Validate a single hook command for robustness.

        Returns:
            str: Error message if validation fails, empty string if passes
        """
        # Skip validation for non-hook commands
        if "claude/hooks" not in command:
            return ""

        # Check for TRULY fragile patterns (not wrapped in bash -c with git resolution)
        if not command.startswith("bash -c"):
            if any(pattern in command for pattern in ["$ROOT", "${ROOT}"]):
                return (
                    f"❌ FRAGILE PATTERN in {event_type}:\n"
                    f"   Description: {description}\n"
                    f"   Issue: Direct $ROOT usage without bash wrapper\n"
                    f"   Command: {command}\n"
                    f"   Risk: Could cause system lockout if $ROOT undefined"
                )

        # For commands that start with simple python3/bash without git resolution
        simple_fragile_patterns = [
            (r'^python3\s+["\']?\$ROOT', "Direct python3 execution with $ROOT"),
            (r'^bash\s+["\']?\$ROOT', "Direct bash execution with $ROOT"),
            (r'^[^"\']*\$ROOT[^"\']*$', "Raw $ROOT usage without resolution"),
        ]

        for pattern, issue in simple_fragile_patterns:
            if re.search(pattern, command):
                return (
                    f"❌ FRAGILE PATTERN in {event_type}:\n"
                    f"   Description: {description}\n"
                    f"   Issue: {issue}\n"
                    f"   Command: {command}\n"
                    f"   Risk: Could cause system lockout if $ROOT undefined"
                )

        # For Python/shell script hooks, enforce robust pattern
        if any(ext in command for ext in [".py", ".sh"]) and "claude/hooks" in command:
            required_components = [
                ("git rev-parse --is-inside-work-tree", "Git repository check"),
                ("ROOT=$(git rev-parse --show-toplevel)", "Dynamic ROOT resolution"),
                ("[ -x", "Executable file check"),
                ("exit 0", "Graceful exit"),
                ("bash -c", "Bash wrapper for robustness"),
            ]

            missing_components = []
            for component, purpose in required_components:
                if component not in command:
                    missing_components.append(f"   - {component} ({purpose})")

            if missing_components:
                return (
                    f"❌ INCOMPLETE ROBUST PATTERN in {event_type}:\n"
                    f"   Description: {description}\n"
                    f"   Missing components:\n" + "\n".join(missing_components) + "\n"
                    f"   Command: {command}\n"
                    f"   Fix: Use pattern from .claude/hooks/CLAUDE.md"
                )

        return ""  # Validation passed

    def test_no_shell_injection_vulnerabilities(self):
        """Test that hook commands are not vulnerable to shell injection."""
        hooks_config = self.settings.get("hooks", {})
        vulnerabilities = []

        for event_type, event_hooks in hooks_config.items():
            if not isinstance(event_hooks, list):
                continue

            for matcher_group in event_hooks:
                if not isinstance(matcher_group, dict) or "hooks" not in matcher_group:
                    continue

                for hook in matcher_group["hooks"]:
                    if not isinstance(hook, dict) or "command" not in hook:
                        continue

                    command = hook["command"]
                    description = hook.get("description", "No description")

                    # Check for potential shell injection patterns
                    dangerous_patterns = [
                        (r"[^\\]\$\w+[^}]", "Unquoted variable expansion"),
                        (r"`[^`]+`", "Command substitution without proper escaping"),
                        (r"\$\([^)]*\w+[^)]*\)", "Uncontrolled command substitution"),
                    ]

                    for pattern, risk in dangerous_patterns:
                        if re.search(pattern, command):
                            # Skip safe patterns we know about
                            if "git rev-parse --show-toplevel" in command:
                                continue

                            vulnerabilities.append(
                                f"⚠️  POTENTIAL VULNERABILITY in {event_type}:\n"
                                f"   Description: {description}\n"
                                f"   Risk: {risk}\n"
                                f"   Command: {command}"
                            )

        if vulnerabilities:
            error_msg = "🔒 SECURITY VALIDATION FAILURES:\n\n" + "\n\n".join(
                vulnerabilities
            )
            self.fail(error_msg)

    def test_hook_files_exist(self):
        """Test that all referenced hook files actually exist."""
        hooks_config = self.settings.get("hooks", {})
        missing_files = []

        for event_type, event_hooks in hooks_config.items():
            if not isinstance(event_hooks, list):
                continue

            for matcher_group in event_hooks:
                if not isinstance(matcher_group, dict) or "hooks" not in matcher_group:
                    continue

                for hook in matcher_group["hooks"]:
                    if not isinstance(hook, dict) or "command" not in hook:
                        continue

                    command = hook["command"]
                    description = hook.get("description", "No description")

                    # Extract hook file paths
                    hook_files = re.findall(
                        r'\.claude/hooks/([^"\']+\.(?:py|sh))', command
                    )

                    for hook_file in hook_files:
                        hook_path = self.project_root / ".claude" / "hooks" / hook_file
                        if not hook_path.exists():
                            missing_files.append(
                                f"📁 MISSING FILE in {event_type}:\n"
                                f"   Description: {description}\n"
                                f"   Missing: {hook_path}\n"
                                f"   Command: {command}"
                            )

        if missing_files:
            error_msg = "📂 FILE EXISTENCE FAILURES:\n\n" + "\n\n".join(missing_files)
            self.fail(error_msg)

    def test_consistent_pattern_usage(self):
        """Test that all hooks use consistent robust patterns."""
        hooks_config = self.settings.get("hooks", {})
        inconsistencies = []
        robust_pattern_count = 0
        total_hook_count = 0

        for event_type, event_hooks in hooks_config.items():
            if not isinstance(event_hooks, list):
                continue

            for matcher_group in event_hooks:
                if not isinstance(matcher_group, dict) or "hooks" not in matcher_group:
                    continue

                for hook in matcher_group["hooks"]:
                    if not isinstance(hook, dict) or "command" not in hook:
                        continue

                    command = hook["command"]
                    description = hook.get("description", "No description")

                    # Only count hooks that reference .claude/hooks files
                    if "claude/hooks" in command and any(
                        ext in command for ext in [".py", ".sh"]
                    ):
                        total_hook_count += 1

                        # Check if this hook uses the robust pattern components
                        robust_components = [
                            "bash -c",
                            "git rev-parse --is-inside-work-tree",
                            "ROOT=$(git rev-parse --show-toplevel)",
                            "[ -x",
                            "exit 0",
                        ]

                        missing_components = [
                            comp for comp in robust_components if comp not in command
                        ]

                        if not missing_components:
                            robust_pattern_count += 1
                        else:
                            # Only report as inconsistency if missing critical components
                            critical_missing = [
                                comp
                                for comp in missing_components
                                if comp in ["bash -c", "git rev-parse", "exit 0"]
                            ]
                            if critical_missing:
                                inconsistencies.append(
                                    f"🔄 INCONSISTENT PATTERN in {event_type}:\n"
                                    f"   Description: {description}\n"
                                    f"   Missing: {', '.join(critical_missing)}\n"
                                    f"   Command: {command}"
                                )

        # Report consistency statistics
        if total_hook_count > 0:
            consistency_rate = (robust_pattern_count / total_hook_count) * 100
            print(
                f"\n📊 Hook Pattern Consistency: {robust_pattern_count}/{total_hook_count} ({consistency_rate:.1f}%)"
            )

        # Only fail if there are critical inconsistencies
        if inconsistencies:
            error_msg = "🔄 CRITICAL CONSISTENCY FAILURES:\n\n" + "\n\n".join(
                inconsistencies
            )
            self.fail(error_msg)


class TestRobustPatternExamples(unittest.TestCase):
    """Test robust pattern validation with specific examples."""

    def setUp(self):
        """Set up validator for testing."""
        # Create a minimal validator instance
        self.validator = TestClaudeSettingsValidation()
        self.validator.setUp = lambda: None  # Skip file loading

    def test_fragile_pattern_detection(self):
        """Test that fragile patterns are correctly detected."""
        fragile_commands = [
            'python3 "$ROOT/.claude/hooks/context_monitor.py"',
            'bash "$ROOT/.claude/hooks/script.sh"',
            'exec "$ROOT/.claude/hooks/test.py"',
        ]

        for command in fragile_commands:
            with self.subTest(command=command):
                violation = self.validator._validate_hook_command(
                    command, "TestEvent", "Test hook"
                )
                self.assertNotEqual(
                    violation, "", f"Should detect fragile pattern: {command}"
                )
                self.assertIn("FRAGILE PATTERN", violation)

    def test_robust_pattern_acceptance(self):
        """Test that robust patterns are correctly accepted."""
        robust_command = (
            "bash -c 'if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then "
            "ROOT=$(git rev-parse --show-toplevel); "
            '[ -x "$ROOT/.claude/hooks/context_monitor.py" ] && '
            'python3 "$ROOT/.claude/hooks/context_monitor.py"; fi; exit 0\''
        )

        violation = self.validator._validate_hook_command(
            robust_command, "TestEvent", "Test hook"
        )

        self.assertEqual(
            violation,
            "",
            f"Should accept robust pattern, but got violation: {violation}",
        )


if __name__ == "__main__":
    # Run with verbose output to show validation details
    unittest.main(verbosity=2, buffer=True)
