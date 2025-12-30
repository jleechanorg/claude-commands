#!/usr/bin/env python3
"""
Packaging integration tests to catch package structure issues.

These tests verify that the package can be imported as it would be
when installed via pip, not just when run from the source directory.

This would have caught the missing __init__.py bug in openai_automation/
"""

import subprocess
import sys
import os
import pytest
import jleechanorg_pr_automation
from jleechanorg_pr_automation.openai_automation import codex_github_mentions


class TestPackagingIntegration:
    """Test that package structure works for pip installations."""

    def test_openai_automation_module_import(self):
        """
        Test that openai_automation can be imported as a proper submodule.

        This catches missing __init__.py files that would break pip installs.
        Uses the same import path that --codex-update uses.
        """
        # This is what happens when user runs: python3 -m jleechanorg_pr_automation.openai_automation.codex_github_mentions
        # It requires proper package structure with __init__.py files

        # Import moved to top level to comply with standards
        assert codex_github_mentions is not None, "Module import returned None"

    def test_openai_automation_module_execution(self):
        """
        Test that openai_automation module can be executed with -m flag.

        This is the actual command used by --codex-update in jleechanorg_pr_monitor.py
        """
        # This simulates what happens in jleechanorg_pr_monitor.py:1340
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "jleechanorg_pr_automation.openai_automation.codex_github_mentions",
                "--help"
            ],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode == 0, (
            f"Module execution failed with return code {result.returncode}\n"
            f"STDOUT: {result.stdout}\n"
            f"STDERR: {result.stderr}\n"
            f"This usually means __init__.py is missing in openai_automation/"
        )

        # Verify help output contains expected content
        assert "--limit" in result.stdout or "--help" in result.stdout, (
            f"Help output doesn't contain expected flags. Got: {result.stdout}"
        )

    def test_openai_automation_has_init_file(self):
        """
        Directly verify that __init__.py exists in openai_automation.

        This is a sanity check to catch the issue at the file system level.
        """
        # Imports moved to top level

        # Get the package directory
        package_dir = os.path.dirname(jleechanorg_pr_automation.__file__)
        openai_automation_dir = os.path.join(package_dir, "openai_automation")
        init_file = os.path.join(openai_automation_dir, "__init__.py")

        assert os.path.exists(openai_automation_dir), (
            f"openai_automation directory not found at {openai_automation_dir}"
        )

        assert os.path.isfile(init_file), (
            f"Missing __init__.py in openai_automation directory!\n"
            f"Expected file at: {init_file}\n"
            f"Without this file, the directory cannot be imported as a Python module.\n"
            f"This breaks: python3 -m jleechanorg_pr_automation.openai_automation.codex_github_mentions"
        )


class TestPackageStructure:
    """Verify overall package structure is correct."""

    def test_all_package_dirs_have_init(self):
        """
        Verify all package directories have __init__.py files.

        This prevents future packaging bugs.
        """
        # Imports moved to top level

        package_root = os.path.dirname(jleechanorg_pr_automation.__file__)

        # Find all directories that contain Python files
        package_dirs = set()
        for root, dirs, files in os.walk(package_root):
            # Skip test directories and __pycache__
            if "__pycache__" in root or ".pytest_cache" in root:
                continue

            # If directory contains .py files, it should have __init__.py
            has_python_files = any(f.endswith(".py") for f in files)
            if has_python_files and root != package_root:
                package_dirs.add(root)

        missing_init = []
        for pkg_dir in package_dirs:
            init_file = os.path.join(pkg_dir, "__init__.py")
            if not os.path.isfile(init_file):
                rel_path = os.path.relpath(pkg_dir, package_root)
                missing_init.append(rel_path)

        assert not missing_init, (
            f"Found package directories without __init__.py:\n" +
            "\n".join(f"  - {d}" for d in missing_init) +
            "\n\nAll directories containing Python files must have __init__.py to be importable as modules."
        )
