#!/usr/bin/env python3
"""
Dead Code Eliminator - Identifies tests for completely unused code paths

Analyzes source code to find dead/unused functions, classes, and modules, then identifies
tests that only cover this dead code. These tests can be safely eliminated as part of
aggressive test optimization strategy.
"""

import ast
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class DeadCodeEliminator:
    """Identifies and eliminates tests for dead/unused source code."""

    def __init__(self, source_directory: str = "mvp_site", test_directory: str = None):
        self.source_directory = Path(source_directory)
        self.test_directory = Path(test_directory) if test_directory else Path("mvp_site/tests")
        self.dead_code_map = {}
        self.usage_map = {}
        self.test_dependencies = {}

    def find_dead_code(self) -> set[str]:
        """
        Find dead/unused code in the source directory.
        
        Returns:
            Set of identifiers for dead code (functions, classes, variables)
        """
        logger.info("Analyzing source code for dead/unused elements")

        # Step 1: Build usage map of all code references
        self._build_usage_map()

        # Step 2: Find code that is never referenced
        dead_code = set()

        for source_file in self.source_directory.rglob("*.py"):
            if self._is_test_file(str(source_file)):
                continue

            try:
                with open(source_file, encoding='utf-8') as f:
                    content = f.read()

                tree = ast.parse(content)

                # Check functions
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        func_id = f"{source_file.stem}.{node.name}"
                        if not self._is_used(func_id):
                            dead_code.add(func_id)
                            logger.debug(f"Dead function: {func_id}")

                    elif isinstance(node, ast.ClassDef):
                        class_id = f"{source_file.stem}.{node.name}"
                        if not self._is_used(class_id):
                            dead_code.add(class_id)
                            logger.debug(f"Dead class: {class_id}")

                    elif isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                var_id = f"{source_file.stem}.{target.id}"
                                if not self._is_used(var_id):
                                    dead_code.add(var_id)
                                    logger.debug(f"Dead variable: {var_id}")

            except Exception as e:
                logger.warning(f"Error analyzing {source_file}: {e}")

        logger.info(f"Found {len(dead_code)} dead code elements")
        return dead_code

    def find_tests_for_dead_code(self, dead_code: set[str] = None) -> list[str]:
        """
        Find tests that only cover dead code and can be eliminated.
        
        Args:
            dead_code: Set of dead code identifiers. If None, will analyze automatically.
            
        Returns:
            List of test files that can be safely eliminated
        """
        if dead_code is None:
            dead_code = self.find_dead_code()

        logger.info(f"Finding tests that only cover {len(dead_code)} dead code elements")

        eliminable_tests = []

        for test_file in self.test_directory.rglob("test_*.py"):
            test_dependencies = self._analyze_test_dependencies(str(test_file))

            if not test_dependencies:
                continue

            # Check if test only covers dead code
            live_dependencies = test_dependencies - dead_code

            if not live_dependencies:
                # Test only covers dead code - can be eliminated
                eliminable_tests.append(str(test_file))
                logger.info(f"Test only covers dead code: {test_file.name}")
            elif len(live_dependencies) / len(test_dependencies) < 0.3:
                # Test mostly covers dead code - candidate for elimination
                eliminable_tests.append(str(test_file))
                logger.info(f"Test mostly covers dead code ({len(live_dependencies)}/{len(test_dependencies)} live): {test_file.name}")

        logger.info(f"Found {len(eliminable_tests)} tests covering dead code")
        return eliminable_tests

    def analyze_elimination_impact(self, test_files: list[str]) -> dict:
        """
        Analyze the impact of eliminating specific test files.
        
        Args:
            test_files: List of test files to analyze for elimination
            
        Returns:
            Dict with impact analysis including coverage loss and risk assessment
        """
        logger.info(f"Analyzing elimination impact for {len(test_files)} test files")

        impact_report = {
            "total_tests_analyzed": len(test_files),
            "safe_eliminations": [],
            "risky_eliminations": [],
            "coverage_impact": {},
            "risk_factors": {}
        }

        for test_file in test_files:
            test_deps = self._analyze_test_dependencies(test_file)
            risk_level = self._assess_elimination_risk(test_file, test_deps)

            if risk_level == "low":
                impact_report["safe_eliminations"].append(test_file)
            else:
                impact_report["risky_eliminations"].append(test_file)
                impact_report["risk_factors"][test_file] = risk_level

            # Calculate coverage impact
            live_deps = self._filter_live_dependencies(test_deps)
            impact_report["coverage_impact"][test_file] = {
                "total_dependencies": len(test_deps),
                "live_dependencies": len(live_deps),
                "dead_code_ratio": (len(test_deps) - len(live_deps)) / len(test_deps) if test_deps else 0
            }

        return impact_report

    def generate_elimination_report(self) -> dict:
        """
        Generate comprehensive dead code elimination report.
        
        Returns:
            Dict containing dead code analysis and elimination recommendations
        """
        dead_code = self.find_dead_code()
        eliminable_tests = self.find_tests_for_dead_code(dead_code)
        impact_analysis = self.analyze_elimination_impact(eliminable_tests)

        report = {
            "dead_code_summary": {
                "total_dead_elements": len(dead_code),
                "dead_code_types": self._categorize_dead_code(dead_code),
                "elimination_candidates": len(eliminable_tests)
            },
            "elimination_recommendations": {
                "safe_to_eliminate": impact_analysis["safe_eliminations"],
                "requires_review": impact_analysis["risky_eliminations"],
                "total_potential_savings": len(eliminable_tests)
            },
            "detailed_analysis": impact_analysis,
            "dead_code_details": list(dead_code)[:50],  # Limit output size
            "analysis_timestamp": __import__('time').time()
        }

        return report

    def _build_usage_map(self):
        """Build comprehensive usage map of all code references."""
        logger.debug("Building usage map for dead code detection")

        self.usage_map = {}

        for py_file in self.source_directory.rglob("*.py"):
            try:
                with open(py_file, encoding='utf-8') as f:
                    content = f.read()

                tree = ast.parse(content)

                for node in ast.walk(tree):
                    # Track function calls
                    if isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name):
                            self._mark_used(node.func.id, str(py_file))
                        elif isinstance(node.func, ast.Attribute):
                            self._mark_used(self._get_full_name(node.func), str(py_file))

                    # Track name references
                    elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                        self._mark_used(node.id, str(py_file))

                    # Track imports
                    elif isinstance(node, ast.Import):
                        for alias in node.names:
                            self._mark_used(alias.name, str(py_file))

                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            for alias in node.names:
                                self._mark_used(f"{node.module}.{alias.name}", str(py_file))

            except Exception as e:
                logger.warning(f"Error building usage map for {py_file}: {e}")

    def _mark_used(self, identifier: str, used_in_file: str):
        """Mark an identifier as used."""
        if identifier not in self.usage_map:
            self.usage_map[identifier] = set()
        self.usage_map[identifier].add(used_in_file)

    def _is_used(self, identifier: str) -> bool:
        """Check if an identifier is used anywhere in the codebase."""
        # Check exact match
        if identifier in self.usage_map:
            return True

        # Check partial matches (e.g., function name without module)
        simple_name = identifier.split('.')[-1]
        return simple_name in self.usage_map

    def _analyze_test_dependencies(self, test_file: str) -> set[str]:
        """Analyze what source code a test file depends on."""
        if test_file in self.test_dependencies:
            return self.test_dependencies[test_file]

        dependencies = set()

        try:
            with open(test_file, encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    dependencies.add(node.func.id)
                elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    dependencies.add(self._get_full_name(node.func))
                elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    dependencies.add(node.id)

        except Exception as e:
            logger.warning(f"Error analyzing test dependencies for {test_file}: {e}")

        self.test_dependencies[test_file] = dependencies
        return dependencies

    def _filter_live_dependencies(self, dependencies: set[str]) -> set[str]:
        """Filter dependencies to only include live (non-dead) code."""
        live_deps = set()
        for dep in dependencies:
            if self._is_used(dep):
                live_deps.add(dep)
        return live_deps

    def _assess_elimination_risk(self, test_file: str, dependencies: set[str]) -> str:
        """Assess the risk of eliminating a test file."""
        # High risk patterns
        if any(pattern in test_file.lower() for pattern in ['integration', 'auth', 'security', 'api']):
            return "high"

        # Medium risk - tests with many live dependencies
        live_deps = self._filter_live_dependencies(dependencies)
        if len(live_deps) > 5:
            return "medium"

        return "low"

    def _categorize_dead_code(self, dead_code: set[str]) -> dict[str, int]:
        """Categorize dead code by type."""
        categories = {"functions": 0, "classes": 0, "variables": 0, "other": 0}

        for code in dead_code:
            if "def " in code or "function" in code:
                categories["functions"] += 1
            elif "class" in code:
                categories["classes"] += 1
            elif "var" in code or "=" in code:
                categories["variables"] += 1
            else:
                categories["other"] += 1

        return categories

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

    def _is_test_file(self, file_path: str) -> bool:
        """Check if a file is a test file."""
        return "test" in Path(file_path).name.lower()
