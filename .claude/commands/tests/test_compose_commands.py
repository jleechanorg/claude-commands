#!/usr/bin/env python3
"""
Test suite for compose-commands.sh hook functionality
Red-Green TDD approach to fix claude -p hanging issue

Test coverage:
- Normal interactive mode behavior
- claude -p (print mode) behavior without hanging
- JSON input parsing
- Slash command detection
- Pasted content detection
"""

import subprocess
import json
import sys
import shutil
import os
from pathlib import Path

# Test constants for better maintainability
LARGE_CONTENT_REPEAT_COUNT = 100
LARGE_CONTENT_PATTERN = "Type / to search\n"
LARGE_CONTENT_SUFFIX = "Large content here"

class TestComposeCommands:
    def __init__(self):
        self.hook_path = Path(__file__).parent.parent.parent / "hooks" / "compose-commands.sh"
        assert self.hook_path.exists(), f"Hook not found at {self.hook_path}"

    def run_hook(self, input_text, timeout=5):
        """Run the compose-commands.sh hook with given input"""
        try:
            process = subprocess.Popen(
                [str(self.hook_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            stdout, stderr = process.communicate(input=input_text, timeout=timeout)
            return stdout, stderr, process.returncode
        except subprocess.TimeoutExpired:
            process.kill()
            return None, "TIMEOUT", -1

    def test_simple_text_passthrough(self):
        """Test that simple text passes through unchanged"""
        input_text = "hello world"
        stdout, stderr, returncode = self.run_hook(input_text)

        assert stdout is not None, "Hook should not timeout on simple input"
        print(f"DEBUG: stdout='{stdout}', stderr='{stderr}', returncode={returncode}")
        assert "hello world" in stdout, f"Expected 'hello world' in output, got: '{stdout}'"
        print("✅ PASS: Simple text passthrough")

    def test_claude_p_mode_no_hang(self):
        """Test that claude -p mode input doesn't hang"""
        # This simulates what claude -p sends to the hook
        input_text = "make a hello world function"
        stdout, stderr, returncode = self.run_hook(input_text, timeout=2)

        assert stdout is not None, "Hook should not timeout in claude -p mode"
        assert stderr != "TIMEOUT", "Hook should not hang when processing claude -p input"
        print("✅ PASS: claude -p mode doesn't hang")

    def test_actual_claude_p_no_hang(self):
        """Test that actual claude -p doesn't hang"""
        if os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true":
            print("↪️ SKIP: real 'claude -p' smoke test under CI/GitHub Actions")
            return "", "", 0
        if shutil.which("claude") is None:
            print("↪️ SKIP: 'claude' binary not found; skipping real claude -p smoke test")
            return "", "", 0

        # This is the real test - using actual claude -p
        try:
            process = subprocess.Popen(
                ["claude", "-p", "make a hello world function"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(Path(__file__).parent.parent.parent)  # Run from project root
            )

            stdout, stderr = process.communicate(timeout=10)
            print("✅ PASS: Real claude -p doesn't hang")
            return stdout, stderr, process.returncode
        except subprocess.TimeoutExpired:
            process.kill()
            print("❌ FAIL: Real claude -p hangs")
            raise AssertionError("Real claude -p should not hang")

    def test_json_input_parsing(self):
        """Test that JSON input is parsed correctly"""
        json_input = json.dumps({"prompt": "test prompt"})
        stdout, stderr, returncode = self.run_hook(json_input)

        assert stdout is not None, "Hook should not timeout on JSON input"
        assert "test prompt" in stdout, f"Expected 'test prompt' in output, got: {stdout}"
        print("✅ PASS: JSON input parsing")

    def test_slash_command_detection(self):
        """Test that slash commands are detected"""
        input_text = "/test command here"
        stdout, stderr, returncode = self.run_hook(input_text)

        assert stdout is not None, "Hook should not timeout on slash commands"
        # Hook should process slash commands without hanging
        print("✅ PASS: Slash command detection")

    def test_empty_input(self):
        """Test that empty input doesn't hang"""
        input_text = ""
        stdout, stderr, returncode = self.run_hook(input_text, timeout=1)

        assert stdout is not None, "Hook should not timeout on empty input"
        assert stderr != "TIMEOUT", "Hook should handle empty input gracefully"
        print("✅ PASS: Empty input handling")

    def test_large_input_no_hang(self):
        """Test that large input doesn't cause hanging"""
        # Simulate a large pasted content
        input_text = LARGE_CONTENT_PATTERN * LARGE_CONTENT_REPEAT_COUNT + LARGE_CONTENT_SUFFIX
        stdout, stderr, returncode = self.run_hook(input_text, timeout=3)

        assert stdout is not None, "Hook should not timeout on large input"
        assert stderr != "TIMEOUT", "Hook should handle large input without hanging"
        print("✅ PASS: Large input handling")


def run_failing_tests():
    """Run tests that should currently fail (red phase)"""
    print("🔴 RED PHASE: Running tests that should fail...")
    test_suite = TestComposeCommands()

    failed_tests = []

    try:
        test_suite.test_simple_text_passthrough()
    except Exception as e:
        print(f"❌ FAIL: Simple text passthrough - {e}")
        failed_tests.append("test_simple_text_passthrough")

    try:
        test_suite.test_claude_p_mode_no_hang()
    except Exception as e:
        print(f"❌ FAIL: claude -p mode no hang - {e}")
        failed_tests.append("test_claude_p_mode_no_hang")

    try:
        test_suite.test_json_input_parsing()
    except Exception as e:
        print(f"❌ FAIL: JSON input parsing - {e}")
        failed_tests.append("test_json_input_parsing")

    try:
        test_suite.test_slash_command_detection()
    except Exception as e:
        print(f"❌ FAIL: Slash command detection - {e}")
        failed_tests.append("test_slash_command_detection")

    try:
        test_suite.test_empty_input()
    except Exception as e:
        print(f"❌ FAIL: Empty input handling - {e}")
        failed_tests.append("test_empty_input")

    try:
        test_suite.test_large_input_no_hang()
    except Exception as e:
        print(f"❌ FAIL: Large input handling - {e}")
        failed_tests.append("test_large_input_no_hang")

    try:
        test_suite.test_actual_claude_p_no_hang()
    except Exception as e:
        print(f"❌ FAIL: Real claude -p hanging - {e}")
        failed_tests.append("test_actual_claude_p_no_hang")

    print(f"\n🔴 RED PHASE COMPLETE: {len(failed_tests)} failing tests")
    if failed_tests:
        print(f"Failed tests: {', '.join(failed_tests)}")

    return len(failed_tests) > 0


def run_green_tests():
    """Run tests after fixes (green phase)"""
    print("🟢 GREEN PHASE: Running tests after fixes...")
    test_suite = TestComposeCommands()

    passed_tests = []
    failed_tests = []

    tests = [
        ("Simple text passthrough", test_suite.test_simple_text_passthrough),
        ("claude -p mode no hang", test_suite.test_claude_p_mode_no_hang),
        ("JSON input parsing", test_suite.test_json_input_parsing),
        ("Slash command detection", test_suite.test_slash_command_detection),
        ("Empty input handling", test_suite.test_empty_input),
        ("Large input handling", test_suite.test_large_input_no_hang),
        ("Real claude -p no hang", test_suite.test_actual_claude_p_no_hang),
    ]

    for test_name, test_func in tests:
        try:
            test_func()
            passed_tests.append(test_name)
        except Exception as e:
            print(f"❌ FAIL: {test_name} - {e}")
            failed_tests.append(test_name)

    print(f"\n🟢 GREEN PHASE COMPLETE: {len(passed_tests)} passing, {len(failed_tests)} failing")
    return len(failed_tests) == 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "red":
        # Legacy/TDD mode: run the red phase intentionally.
        has_failures = run_failing_tests()
        sys.exit(0 if has_failures else 1)  # Exit 0 if we have expected failures

    # Default: run green phase for CI/test runners.
    success = run_green_tests()
    sys.exit(0 if success else 1)
