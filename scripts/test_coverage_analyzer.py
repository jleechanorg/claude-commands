#!/usr/bin/env python3
"""
Test Coverage Analyzer - AST-based coverage overlap detection for aggressive test elimination

Analyzes test files to identify coverage overlap and find redundant tests that can be safely eliminated
while maintaining code coverage. Part of the aggressive test optimization strategy to reach 80-test target.
"""

import ast
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class TestCoverageAnalyzer:
    """Analyzes test coverage overlap to identify redundant tests for aggressive elimination."""

    def __init__(self, test_directory: str, source_directory: str = "mvp_site"):
        self.test_directory = Path(test_directory)
        self.source_directory = Path(source_directory)
        self.test_coverage_map = {}
        self.source_coverage_map = {}

    def analyze_coverage_overlap(self, test_files: list[str]) -> dict[str, list[str]]:
        """
        Analyze coverage overlap between test files.
        
        Args:
            test_files: List of test file paths to analyze
            
        Returns:
            Dict mapping test files to lists of other tests with overlapping coverage
        """
        logger.info(f"Analyzing coverage overlap for {len(test_files)} test files")

        # Build coverage maps for each test file
        for test_file in test_files:
            try:
                self.test_coverage_map[test_file] = self._analyze_test_coverage(test_file)
            except Exception as e:
                logger.warning(f"Failed to analyze coverage for {test_file}: {e}")
                self.test_coverage_map[test_file] = set()

        # Find overlapping coverage between tests
        overlap_map = {}
        for test_file in test_files:
            overlaps = []
            test_coverage = self.test_coverage_map.get(test_file, set())

            for other_test in test_files:
                if test_file != other_test:
                    other_coverage = self.test_coverage_map.get(other_test, set())
                    if test_coverage and other_coverage:
                        overlap_ratio = len(test_coverage & other_coverage) / len(test_coverage | other_coverage)
                        if overlap_ratio > 0.3:  # Significant overlap threshold
                            overlaps.append(other_test)

            overlap_map[test_file] = overlaps

        logger.info(f"Coverage overlap analysis complete: {len([k for k, v in overlap_map.items() if v])} tests have overlaps")
        return overlap_map

    def find_redundant_by_coverage(self, overlap_threshold: float = 0.8) -> list[str]:
        """
        Find tests that are redundant based on coverage overlap.
        
        Args:
            overlap_threshold: Minimum overlap ratio to consider redundant (0.0-1.0)
            
        Returns:
            List of test files that can be safely eliminated
        """
        logger.info(f"Finding redundant tests with overlap threshold {overlap_threshold}")

        redundant_tests = []
        processed_tests = set()

        for test_file, test_coverage in self.test_coverage_map.items():
            if test_file in processed_tests or not test_coverage:
                continue

            # Find tests with high coverage overlap
            for other_test, other_coverage in self.test_coverage_map.items():
                if (other_test != test_file and other_test not in processed_tests and
                    other_coverage and test_coverage):

                    # Calculate coverage overlap
                    intersection = test_coverage & other_coverage
                    union = test_coverage | other_coverage
                    overlap_ratio = len(intersection) / len(union) if union else 0

                    if overlap_ratio >= overlap_threshold:
                        # Prefer to keep the test with more coverage
                        if len(test_coverage) >= len(other_coverage):
                            redundant_tests.append(other_test)
                            processed_tests.add(other_test)
                        else:
                            redundant_tests.append(test_file)
                            processed_tests.add(test_file)
                            break

        # Filter out critical tests that should never be eliminated
        filtered_redundant = []
        for test in redundant_tests:
            if not self._is_critical_test(test):
                filtered_redundant.append(test)
            else:
                logger.info(f"Preserving critical test: {test}")

        logger.info(f"Found {len(filtered_redundant)} redundant tests for elimination")
        return filtered_redundant

    def generate_coverage_report(self) -> dict:
        """
        Generate comprehensive coverage analysis report.
        
        Returns:
            Dict containing coverage statistics and analysis results
        """
        total_tests = len(self.test_coverage_map)
        tests_with_coverage = len([t for t, c in self.test_coverage_map.items() if c])

        # Calculate coverage distribution
        coverage_sizes = [len(coverage) for coverage in self.test_coverage_map.values() if coverage]
        avg_coverage = sum(coverage_sizes) / len(coverage_sizes) if coverage_sizes else 0

        # Find high-overlap test pairs
        high_overlap_pairs = []
        test_files = list(self.test_coverage_map.keys())
        for i, test1 in enumerate(test_files):
            for test2 in test_files[i+1:]:
                coverage1 = self.test_coverage_map.get(test1, set())
                coverage2 = self.test_coverage_map.get(test2, set())
                if coverage1 and coverage2:
                    overlap = len(coverage1 & coverage2) / len(coverage1 | coverage2)
                    if overlap > 0.5:
                        high_overlap_pairs.append((test1, test2, overlap))

        report = {
            "total_tests_analyzed": total_tests,
            "tests_with_coverage": tests_with_coverage,
            "average_coverage_size": avg_coverage,
            "high_overlap_pairs": len(high_overlap_pairs),
            "overlap_details": high_overlap_pairs[:10],  # Top 10 overlaps
            "redundancy_candidates": self.find_redundant_by_coverage(),
            "analysis_timestamp": __import__('time').time()
        }

        return report

    def _analyze_test_coverage(self, test_file: str) -> set[str]:
        """
        Analyze what source code a test file covers using AST parsing.
        
        Args:
            test_file: Path to test file to analyze
            
        Returns:
            Set of source code identifiers (functions, classes, methods) covered by the test
        """
        coverage = set()

        try:
            test_path = Path(test_file)
            if not test_path.exists():
                return coverage

            with open(test_path, encoding='utf-8') as f:
                content = f.read()

            # Parse AST to find imports and function calls
            tree = ast.parse(content)

            for node in ast.walk(tree):
                # Track imports from source modules
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if self._is_source_module(alias.name):
                            coverage.add(f"import:{alias.name}")

                elif isinstance(node, ast.ImportFrom):
                    if node.module and self._is_source_module(node.module):
                        for alias in node.names:
                            coverage.add(f"from:{node.module}.{alias.name}")

                # Track function calls to source code
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        coverage.add(f"call:{node.func.id}")
                    elif isinstance(node.func, ast.Attribute):
                        coverage.add(f"call:{self._get_full_name(node.func)}")

                # Track class instantiations
                elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    coverage.add(f"reference:{node.id}")

        except Exception as e:
            logger.warning(f"Error analyzing test coverage for {test_file}: {e}")

        return coverage

    def _is_source_module(self, module_name: str) -> bool:
        """Check if a module name refers to source code (not external libraries)."""
        if not module_name:
            return False

        # Consider modules starting with project-specific prefixes as source
        source_prefixes = ['mvp_site', 'app', 'models', 'routes', 'services', 'utils']
        return any(module_name.startswith(prefix) for prefix in source_prefixes)

    def _get_full_name(self, node: ast.Attribute) -> str:
        """Get full dotted name from an attribute node."""
        names = []
        current = node

        while isinstance(current, ast.Attribute):
            names.append(current.attr)
            current = current.value

        if isinstance(current, ast.Name):
            names.append(current.id)

        return '.'.join(reversed(names))

    def _is_critical_test(self, test_file: str) -> bool:
        """
        Determine if a test is critical and should not be eliminated.
        
        Args:
            test_file: Path to test file
            
        Returns:
            True if test is critical and should be preserved
        """
        # Critical test patterns that should never be eliminated
        critical_patterns = [
            'test_auth',
            'test_security',
            'test_database',
            'test_api_',
            'test_integration',
            'test_end_to_end',
            'test_user_flow'
        ]

        test_name = Path(test_file).stem.lower()
        return any(pattern in test_name for pattern in critical_patterns)
