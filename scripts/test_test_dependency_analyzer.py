#!/usr/bin/env python3
"""
Simple test for the Test Dependency Analyzer

Validates that the analyzer correctly maps files to tests and produces expected output.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from test_dependency_analyzer import DependencyAnalyzer


class TestDependencyAnalyzerTests(unittest.TestCase):
    """Test cases for the Test Dependency Analyzer."""

    def setUp(self):
        """Set up test environment."""
        self.analyzer = DependencyAnalyzer()

    def test_analyzer_initialization(self):
        """Test that analyzer initializes correctly."""
        self.assertIsNotNone(self.analyzer.config)
        self.assertIn("mappings", self.analyzer.config)
        self.assertIsNotNone(self.analyzer.project_root)

    def test_direct_file_mapping(self):
        """Test direct file mappings work correctly."""
        # Test main.py mapping
        tests = self.analyzer.find_matching_tests("main.py")
        self.assertIn("test_main_*.py", tests)
        self.assertIn("test_api_*.py", tests)

        # Test llm_service.py mapping
        tests = self.analyzer.find_matching_tests("llm_service.py")
        self.assertIn("test_gemini_*.py", tests)
        self.assertIn("test_json_*.py", tests)

    def test_pattern_mapping(self):
        """Test pattern-based mappings work correctly."""
        # Test frontend file mapping
        tests = self.analyzer.find_matching_tests("frontend_v2/components/Button.tsx")
        self.assertIn("test_v2_*.py", tests)

        # Test configuration file mapping
        tests = self.analyzer.find_matching_tests("config.yml")
        self.assertIn("test_integration_*.py", tests)

    def test_conservative_mappings(self):
        """Test conservative fallback mappings."""
        # Test unknown Python file in mvp_site
        tests = self.analyzer.find_matching_tests("mvp_site/unknown_service.py")
        self.assertTrue(any("test_main_" in test for test in tests))

        # Test unknown frontend file
        tests = self.analyzer.find_matching_tests("static/unknown.js")
        self.assertTrue(any("testing_ui" in test for test in tests))

    def test_pattern_expansion(self):
        """Test that glob patterns expand to actual test files."""
        # Test main pattern expansion
        expanded = self.analyzer.expand_test_patterns(["test_main_*.py"])
        self.assertTrue(len(expanded) > 0)
        self.assertTrue(all("test_main_" in test for test in expanded))

        # Test API pattern expansion
        expanded = self.analyzer.expand_test_patterns(["test_api_*.py"])
        self.assertTrue(len(expanded) > 0)
        self.assertTrue(all("test_api_" in test for test in expanded))

    def test_always_run_tests(self):
        """Test that always-run tests are included."""
        self.analyzer.add_always_run_tests()
        self.assertTrue(len(self.analyzer.selected_tests) > 0)

    def test_analyze_changes(self):
        """Test full change analysis workflow."""
        changed_files = ["main.py", "llm_service.py"]
        selected_tests = self.analyzer.analyze_changes(changed_files)

        # Should have selected some tests
        self.assertTrue(len(selected_tests) > 0)

        # Should include always-run tests
        self.assertTrue(any("test_integration_mock.py" in test for test in selected_tests))

        # Should include main and gemini related tests
        main_tests = [t for t in selected_tests if "test_main_" in t]
        gemini_tests = [t for t in selected_tests if "test_gemini_" in t]
        self.assertTrue(len(main_tests) > 0)
        self.assertTrue(len(gemini_tests) > 0)

    def test_write_selected_tests(self):
        """Test writing selected tests to output file."""
        # Analyze some changes
        changed_files = ["main.py"]
        self.analyzer.analyze_changes(changed_files)

        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp_file:
            tmp_path = tmp_file.name

        try:
            self.analyzer.write_selected_tests(tmp_path)

            # Verify file was created and has content
            self.assertTrue(os.path.exists(tmp_path))

            with open(tmp_path) as f:
                lines = f.readlines()

            self.assertTrue(len(lines) > 0)
            self.assertTrue(all(line.strip().endswith('.py') for line in lines))

        finally:
            # Clean up
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_safety_threshold(self):
        """Test safety threshold behavior."""
        # Create a large number of changed files to trigger safety threshold
        large_change_list = [f"file_{i}.py" for i in range(1000)]
        selected_tests = self.analyzer.analyze_changes(large_change_list)

        # Should fall back to all tests or a substantial number
        self.assertTrue(len(selected_tests) > 50)  # Should be many tests

    def test_git_changes_fallback(self):
        """Test git changes with fallback behavior."""
        # This might fail in CI, but should handle gracefully
        changed_files = self.analyzer.get_git_changes()

        # Should return a list (empty or with files)
        self.assertIsInstance(changed_files, list)

        # If we have changes, should be valid file paths
        if changed_files:
            self.assertTrue(all(isinstance(f, str) for f in changed_files))


def main():
    """Run the tests."""
    print("Running Test Dependency Analyzer validation tests...")
    print("=" * 60)

    # Run the tests
    unittest.main(verbosity=2, exit=False)

    print("\n" + "=" * 60)
    print("Test Dependency Analyzer validation completed.")

    # Also run a quick integration test
    print("\nRunning integration test...")
    analyzer = DependencyAnalyzer()

    # Test with sample changes
    test_changes = ["main.py", "llm_service.py", "frontend_v2/test.tsx"]
    selected_tests = analyzer.analyze_changes(test_changes)

    print(f"Sample analysis: {len(test_changes)} changed files -> {len(selected_tests)} selected tests")
    print("Sample selected tests:")
    for test in sorted(list(selected_tests))[:10]:  # Show first 10
        print(f"  {test}")
    if len(selected_tests) > 10:
        print(f"  ... and {len(selected_tests) - 10} more")

    print("\n✅ Integration test completed successfully!")


if __name__ == "__main__":
    main()
