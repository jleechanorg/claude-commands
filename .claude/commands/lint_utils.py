#!/usr/bin/env python3
"""
Linting utilities for Claude commands
Integrates Ruff, isort, mypy, and Bandit into command workflows
"""

import os
import subprocess
import sys
from typing import List, Tuple

# Constants
MAX_DIRECTORY_TRAVERSAL_LEVELS = 3
MAX_ERROR_LINES = 3


class LintResult:
    """Container for linting results"""

    def __init__(
        self, tool_name: str, success: bool, output: str = "", error: str = ""
    ):
        self.tool_name = tool_name
        self.success = success
        self.output = output
        self.error = error

    def __str__(self) -> str:
        status = "✅ PASS" if self.success else "❌ FAIL"
        return f"{self.tool_name}: {status}"


class LintRunner:
    """Runs comprehensive linting suite"""

    def __init__(self, target_dir: str = "mvp_site", auto_fix: bool = False):
        self.target_dir = target_dir
        self.auto_fix = auto_fix
        self.results: List[LintResult] = []

    def _find_venv_path(self) -> str:
        """Find virtual environment path by checking current and parent directories"""
        current_dir = os.getcwd()
        for _ in range(MAX_DIRECTORY_TRAVERSAL_LEVELS):
            venv_bin = os.path.join(current_dir, "venv", "bin")
            if os.path.exists(venv_bin):
                return venv_bin
            current_dir = os.path.dirname(current_dir)
        return ""

    def _ensure_venv(self) -> bool:
        """Ensure we're in virtual environment"""
        if os.environ.get("VIRTUAL_ENV"):
            return True

        # Try to find venv in current dir or parent dirs
        venv_bin = self._find_venv_path()
        if venv_bin:
            print("⚠️  Virtual environment found, tools should work...")
            return True

        # Check if tools are available anyway (maybe system-wide install)
        try:
            subprocess.run(["ruff", "--version"], capture_output=True, check=True)
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass

        print("❌ Virtual environment not found and tools not available.")
        return False

    def _run_command(self, command: List[str], tool_name: str) -> LintResult:
        """Run a command and return LintResult"""
        try:
            # Ensure we have the full venv path for commands
            if not os.environ.get("VIRTUAL_ENV"):
                # Use the common venv finder method
                venv_bin = self._find_venv_path()
                if venv_bin:
                    tool_path = os.path.join(venv_bin, command[0])
                    if os.path.exists(tool_path):
                        command[0] = tool_path

            result = subprocess.run(
                command, capture_output=True, text=True, cwd=os.getcwd()
            )

            success = result.returncode == 0
            output = result.stdout if result.stdout else result.stderr

            return LintResult(tool_name, success, output, result.stderr)

        except FileNotFoundError:
            return LintResult(tool_name, False, "", f"Tool '{command[0]}' not found")
        except Exception as e:
            return LintResult(tool_name, False, "", str(e))

    def run_ruff_lint(self) -> LintResult:
        """Run Ruff linting"""
        cmd = ["ruff", "check", self.target_dir]
        if self.auto_fix:
            cmd.append("--fix")

        return self._run_command(cmd, "Ruff Lint")

    def run_ruff_format(self) -> LintResult:
        """Run Ruff formatting"""
        cmd = ["ruff", "format", self.target_dir]
        if not self.auto_fix:
            cmd.append("--diff")

        return self._run_command(cmd, "Ruff Format")

    def run_isort(self) -> LintResult:
        """Run isort import sorting"""
        cmd = ["isort", self.target_dir]
        if not self.auto_fix:
            cmd.extend(["--check-only", "--diff"])

        return self._run_command(cmd, "isort")

    def run_mypy(self) -> LintResult:
        """Run mypy type checking"""
        cmd = ["mypy", self.target_dir]
        return self._run_command(cmd, "mypy")

    def run_bandit(self) -> LintResult:
        """Run Bandit security scanning"""
        cmd = ["bandit", "-r", self.target_dir, "-f", "txt"]
        return self._run_command(cmd, "Bandit")

    def run_all(self) -> Tuple[bool, List[LintResult]]:
        """Run all linting tools and return overall success status"""
        print(f"🔍 Running comprehensive linting on: {self.target_dir}")

        if not self._ensure_venv():
            return False, []

        # Run all tools
        self.results = [
            self.run_ruff_lint(),
            self.run_ruff_format(),
            self.run_isort(),
            self.run_mypy(),
            self.run_bandit(),
        ]

        # Determine overall success
        all_passed = all(result.success for result in self.results)

        return all_passed, self.results

    def print_summary(self) -> None:
        """Print a summary of all linting results"""
        if not self.results:
            print("❌ No linting results to display")
            return

        print("\n📊 Linting Summary:")
        print("=" * 50)

        passed = 0
        for result in self.results:
            status_emoji = "✅" if result.success else "❌"
            print(f"{status_emoji} {result.tool_name}")

            if result.success:
                passed += 1
            elif result.output or result.error:
                # Show first few lines of error for context
                error_text = result.error or result.output
                lines = error_text.split("\n")[:MAX_ERROR_LINES]
                for line in lines:
                    if line.strip():
                        print(f"    💡 {line.strip()}")

        print("=" * 50)
        print(f"📈 Results: {passed}/{len(self.results)} tools passed")

        if passed < len(self.results):
            print(f"💡 Run with auto-fix: ./run_lint.sh {self.target_dir} fix")


def run_lint_check(
    target_dir: str = "mvp_site", auto_fix: bool = False
) -> Tuple[bool, str]:
    """
    Convenience function for running linting from Claude commands
    Returns (success, summary_message)
    """
    runner = LintRunner(target_dir, auto_fix)
    success, results = runner.run_all()

    if success:
        return True, "🎉 All linting checks passed!"
    else:
        failed_tools = [r.tool_name for r in results if not r.success]
        return False, f"❌ Linting failed: {', '.join(failed_tools)}"


def should_run_linting() -> bool:
    """Check if linting should be run based on environment/flags"""
    # Skip linting if explicitly disabled
    if os.environ.get("SKIP_LINT", "").lower() in ["true", "1", "yes"]:
        return False

    # Skip in CI unless explicitly enabled
    if os.environ.get("CI") and not os.environ.get("ENABLE_LINT_IN_CI"):
        return False

    return True


if __name__ == "__main__":
    """Command line interface for testing"""
    target = sys.argv[1] if len(sys.argv) > 1 else "mvp_site"
    fix_mode = len(sys.argv) > 2 and sys.argv[2] == "fix"

    runner = LintRunner(target, fix_mode)
    success, results = runner.run_all()
    runner.print_summary()

    sys.exit(0 if success else 1)
