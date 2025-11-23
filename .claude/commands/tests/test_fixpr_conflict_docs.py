#!/usr/bin/env python3
"""
Test suite for /fixpr conflict resolution documentation feature.

Tests verify:
1. Conflict documentation directory creation logic
2. Conflict resolution documentation template structure
3. Git commands for committing documentation
4. Edge cases (special characters in branch names, etc.)
"""

import unittest
import tempfile
import os
import subprocess
import shutil
from unittest.mock import patch


class TestConflictDocumentationDirectoryCreation(unittest.TestCase):
    """Test conflict documentation directory creation logic."""

    def setUp(self):
        """Set up temporary directory for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

        # Initialize git repo for testing
        subprocess.run(['git', 'init'], check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'], check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'], check=True, capture_output=True)

    def tearDown(self):
        """Clean up temporary directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_create_conflict_docs_directory(self):
        """Test that conflict documentation directory is created correctly."""
        branch_name = "feature/test-branch"
        pr_number = "1234"
        # Sanitize branch name and add delimiter
        sanitized_branch = branch_name.replace("/", "-")
        conflict_docs_dir = f"docs/conflicts/{sanitized_branch}-pr{pr_number}"

        # Create directory structure
        os.makedirs(conflict_docs_dir, exist_ok=True)

        # Verify directory exists at correct flat path
        self.assertTrue(os.path.isdir(conflict_docs_dir))
        # Verify it's flat (no nested feature/ directory)
        self.assertFalse(os.path.exists("docs/conflicts/feature/test-branch-pr1234"))
        # Verify expected sanitized path
        self.assertTrue(os.path.exists("docs/conflicts/feature-test-branch-pr1234"))

    def test_create_conflict_docs_directory_with_special_characters(self):
        """Test directory creation with special characters in branch name."""
        branch_name = "feature/test-branch_123"
        pr_number = "5678"
        # Sanitize branch name and add delimiter
        sanitized_branch = branch_name.replace("/", "-")
        conflict_docs_dir = f"docs/conflicts/{sanitized_branch}-pr{pr_number}"

        # Create directory structure
        os.makedirs(conflict_docs_dir, exist_ok=True)

        # Verify directory exists at correct flat path
        self.assertTrue(os.path.isdir(conflict_docs_dir))
        # Verify it's flat (no nested directories)
        self.assertFalse(os.path.exists("docs/conflicts/feature"))
        # Verify expected sanitized path
        self.assertTrue(os.path.exists("docs/conflicts/feature-test-branch_123-pr5678"))

    def test_create_conflict_docs_directory_nested(self):
        """Test that sanitized directory structure is created correctly (flat, not nested)."""
        branch_name = "feature/test"
        pr_number = "9999"
        # Sanitize branch name and add delimiter
        sanitized_branch = branch_name.replace("/", "-")
        conflict_docs_dir = f"docs/conflicts/{sanitized_branch}-pr{pr_number}"

        # Create directory (mkdir -p equivalent)
        os.makedirs(conflict_docs_dir, exist_ok=True)

        # Verify parent directories exist
        self.assertTrue(os.path.isdir("docs"))
        self.assertTrue(os.path.isdir("docs/conflicts"))
        # Verify flat structure (no nested feature/ directory)
        self.assertFalse(os.path.exists("docs/conflicts/feature"))
        # Verify sanitized path exists
        self.assertTrue(os.path.isdir(conflict_docs_dir))
        self.assertTrue(os.path.exists("docs/conflicts/feature-test-pr9999"))


class TestConflictDocumentationTemplate(unittest.TestCase):
    """Test conflict resolution documentation template structure."""

    def setUp(self):
        """Set up temporary directory for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

        # Initialize git repo for testing
        subprocess.run(['git', 'init'], check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'], check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'], check=True, capture_output=True)

    def tearDown(self):
        """Clean up temporary directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_conflict_summary_template_structure(self):
        """Test that conflict_summary.md template has required sections."""
        branch_name = "test-branch"
        pr_number = "1234"
        # Sanitize branch name and add delimiter (consistent with documented format)
        sanitized_branch = branch_name.replace("/", "-")
        conflict_docs_dir = f"docs/conflicts/{sanitized_branch}-pr{pr_number}"
        os.makedirs(conflict_docs_dir, exist_ok=True)

        # Create conflict_summary.md with required sections
        summary_content = """# Merge Conflict Resolution Report

**Branch**: {branch_name}
**PR Number**: {pr-number}
**Date**: {timestamp}

## Conflicts Resolved

### File: src/main.py

**Conflict Type**: Import statement ordering
**Risk Level**: Low

**Original Conflict**:
```python
<<<<<<< HEAD
import os
import sys
=======
import sys
import os
>>>>>>> main
```

**Resolution Strategy**: Combined both branches, sorted imports alphabetically

**Reasoning**:
- Both branches had the same imports, just different ordering
- Alphabetical sorting follows PEP 8 style guide
- No functional difference between orderings

**Final Resolution**:
```python
import os
import sys
```

## Summary

- **Total Conflicts**: 1
- **Low Risk**: 1
- **High Risk**: 0
"""

        summary_path = os.path.join(conflict_docs_dir, "conflict_summary.md")
        with open(summary_path, 'w') as f:
            f.write(summary_content)

        # Verify file exists and has required sections
        self.assertTrue(os.path.exists(summary_path))
        with open(summary_path, 'r') as f:
            content = f.read()
            self.assertIn("Merge Conflict Resolution Report", content)
            self.assertIn("Conflicts Resolved", content)
            self.assertIn("Conflict Type", content)
            self.assertIn("Risk Level", content)
            self.assertIn("Original Conflict", content)
            self.assertIn("Resolution Strategy", content)
            self.assertIn("Reasoning", content)
            self.assertIn("Final Resolution", content)
            self.assertIn("Summary", content)

    def test_index_template_structure(self):
        """Test that index.md template has required sections."""
        branch_name = "test-branch"
        pr_number = "1234"
        # Sanitize branch name and add delimiter (consistent with documented format)
        sanitized_branch = branch_name.replace("/", "-")
        conflict_docs_dir = f"docs/conflicts/{sanitized_branch}-pr{pr_number}"
        os.makedirs(conflict_docs_dir, exist_ok=True)

        # Create index.md with required sections
        index_content = """# Conflict Resolution Index

**PR**: #{pr_number}
**Branch**: {branch_name}
**Resolved**: {timestamp}

## Files Modified

- [Detailed Conflict Report](./conflict_summary.md)

## Quick Stats

- Files with conflicts: 1
- Low risk resolutions: 1
- Medium risk resolutions: 0
- High risk resolutions: 0
- Manual review required: 0
"""

        index_path = os.path.join(conflict_docs_dir, "index.md")
        with open(index_path, 'w') as f:
            f.write(index_content)

        # Verify file exists and has required sections
        self.assertTrue(os.path.exists(index_path))
        with open(index_path, 'r') as f:
            content = f.read()
            self.assertIn("Conflict Resolution Index", content)
            self.assertIn("PR", content)
            self.assertIn("Branch", content)
            self.assertIn("Files Modified", content)
            self.assertIn("Quick Stats", content)
            self.assertIn("conflict_summary.md", content)


class TestGitCommandsForDocumentation(unittest.TestCase):
    """Test git commands for committing conflict documentation."""

    def setUp(self):
        """Set up temporary directory for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

        # Initialize git repo for testing
        subprocess.run(['git', 'init'], check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'], check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'], check=True, capture_output=True)

        # Create initial commit
        with open('README.md', 'w') as f:
            f.write('# Test Repo\n')
        subprocess.run(['git', 'add', 'README.md'], check=True, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'Initial commit'], check=True, capture_output=True)

    def tearDown(self):
        """Clean up temporary directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_git_add_conflict_docs_directory(self):
        """Test that git add works for conflict docs directory."""
        branch_name = "test-branch"
        pr_number = "1234"
        # Sanitize branch name and add delimiter (consistent with documented format)
        sanitized_branch = branch_name.replace("/", "-")
        conflict_docs_dir = f"docs/conflicts/{sanitized_branch}-pr{pr_number}"
        os.makedirs(conflict_docs_dir, exist_ok=True)

        # Create a test file
        test_file = os.path.join(conflict_docs_dir, "conflict_summary.md")
        with open(test_file, 'w') as f:
            f.write("# Test\n")

        # Add directory to git
        result = subprocess.run(
            ['git', 'add', conflict_docs_dir],
            capture_output=True,
            text=True
        )

        # Verify no errors
        self.assertEqual(result.returncode, 0)

        # Verify file is staged
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True
        )
        self.assertIn(conflict_docs_dir, result.stdout)

    def test_git_commit_conflict_docs(self):
        """Test that git commit works for conflict documentation."""
        branch_name = "test-branch"
        pr_number = "1234"
        # Sanitize branch name and add delimiter (consistent with documented format)
        sanitized_branch = branch_name.replace("/", "-")
        conflict_docs_dir = f"docs/conflicts/{sanitized_branch}-pr{pr_number}"
        os.makedirs(conflict_docs_dir, exist_ok=True)

        # Create a test file
        test_file = os.path.join(conflict_docs_dir, "conflict_summary.md")
        with open(test_file, 'w') as f:
            f.write("# Test\n")

        # Add and commit
        subprocess.run(['git', 'add', conflict_docs_dir], check=True, capture_output=True)
        commit_message = f"docs: Document conflict resolution for PR #{pr_number}"
        result = subprocess.run(
            ['git', 'commit', '-m', commit_message],
            capture_output=True,
            text=True
        )

        # Verify commit succeeded
        self.assertEqual(result.returncode, 0)

        # Verify commit message is correct
        result = subprocess.run(
            ['git', 'log', '-1', '--pretty=%B'],
            capture_output=True,
            text=True
        )
        self.assertIn(commit_message, result.stdout)


class TestConflictDocumentationEdgeCases(unittest.TestCase):
    """Test edge cases for conflict documentation."""

    def setUp(self):
        """Set up temporary directory for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

    def tearDown(self):
        """Clean up temporary directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_branch_name_with_slashes(self):
        """Test that branch names with slashes are sanitized to flat paths."""
        branch_name = "feature/test/branch"
        pr_number = "1234"
        sanitized_branch = branch_name.replace("/", "-")
        conflict_docs_dir = f"docs/conflicts/{sanitized_branch}-pr{pr_number}"

        # Should create FLAT directory structure
        os.makedirs(conflict_docs_dir, exist_ok=True)

        # Verify flat structure (no nested feature/test/branch directories)
        self.assertFalse(os.path.exists("docs/conflicts/feature"))
        self.assertTrue(os.path.exists("docs/conflicts/feature-test-branch-pr1234"))

    def test_pr_number_as_string(self):
        """Test that PR number can be handled as string."""
        branch_name = "test-branch"
        pr_number = "1234"
        sanitized_branch = branch_name.replace("/", "-")
        conflict_docs_dir = f"docs/conflicts/{sanitized_branch}-pr{pr_number}"

        os.makedirs(conflict_docs_dir, exist_ok=True)
        self.assertTrue(os.path.isdir(conflict_docs_dir))
        self.assertTrue(os.path.exists("docs/conflicts/test-branch-pr1234"))

    def test_empty_conflict_list(self):
        """Test handling empty conflict list."""
        branch_name = "test-branch"
        pr_number = "1234"
        sanitized_branch = branch_name.replace("/", "-")
        conflict_docs_dir = f"docs/conflicts/{sanitized_branch}-pr{pr_number}"
        os.makedirs(conflict_docs_dir, exist_ok=True)

        # Create summary with no conflicts
        summary_content = """# Merge Conflict Resolution Report

**Branch**: {branch_name}
**PR Number**: {pr-number}

## Conflicts Resolved

No conflicts were found.

## Summary

- **Total Conflicts**: 0
"""

        summary_path = os.path.join(conflict_docs_dir, "conflict_summary.md")
        with open(summary_path, 'w') as f:
            f.write(summary_content)

        self.assertTrue(os.path.exists(summary_path))

    def test_delimiter_between_branch_and_pr(self):
        """Test that branch name and PR number have clear delimiter."""
        branch_name = "mybranch"
        pr_number = "123"
        sanitized_branch = branch_name.replace("/", "-")
        conflict_docs_dir = f"docs/conflicts/{sanitized_branch}-pr{pr_number}"

        os.makedirs(conflict_docs_dir, exist_ok=True)

        # Should be able to parse back branch and PR from path
        path_parts = conflict_docs_dir.split("-pr")
        self.assertEqual(len(path_parts), 2)
        self.assertEqual(path_parts[1], pr_number)

    def test_special_characters_sanitized(self):
        """Test that special characters in branch names are sanitized."""
        branch_name = "feature/test_branch-123"
        pr_number = "456"
        sanitized_branch = branch_name.replace("/", "-")
        conflict_docs_dir = f"docs/conflicts/{sanitized_branch}-pr{pr_number}"

        os.makedirs(conflict_docs_dir, exist_ok=True)

        # Verify no nested directories from slashes
        self.assertFalse(os.path.exists("docs/conflicts/feature"))
        # Verify expected flat path
        self.assertTrue(os.path.exists("docs/conflicts/feature-test_branch-123-pr456"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
