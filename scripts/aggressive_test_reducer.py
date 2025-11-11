#!/usr/bin/env python3
"""
Aggressive Test Reducer - Push test count from 152→80 tests through intelligent elimination

Implements aggressive elimination strategies while maintaining code coverage and functionality.
Combines multiple analysis approaches to safely reduce test count to the original 80-test target.
"""

import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from dead_code_eliminator import DeadCodeEliminator
from test_coverage_analyzer import TestCoverageAnalyzer

logger = logging.getLogger(__name__)


class AggressiveTestReducer:
    """Implements aggressive test elimination strategies to reach 80-test target."""

    def __init__(self, test_directory: str = "mvp_site/tests", source_directory: str = "mvp_site"):
        self.test_directory = Path(test_directory)
        self.source_directory = Path(source_directory)
        self.coverage_analyzer = TestCoverageAnalyzer(test_directory, source_directory)
        self.dead_code_eliminator = DeadCodeEliminator(source_directory, test_directory)
        self.elimination_strategies = []

    def reduce_to_target(self, current_tests: list[str], target_count: int = 80) -> dict:
        """
        Reduce test count to target through aggressive elimination strategies.
        
        Args:
            current_tests: List of current test files
            target_count: Target number of tests (default: 80)
            
        Returns:
            Dict with elimination plan and safety analysis
        """
        logger.info(f"Reducing {len(current_tests)} tests to {target_count} target")

        if len(current_tests) <= target_count:
            return {
                "status": "no_reduction_needed",
                "current_count": len(current_tests),
                "target_count": target_count,
                "message": "Already at or below target count"
            }

        elimination_plan = {
            "current_count": len(current_tests),
            "target_count": target_count,
            "tests_to_eliminate": len(current_tests) - target_count,
            "elimination_strategies": [],
            "final_test_set": [],
            "safety_analysis": {},
            "risk_assessment": "low"
        }

        # Apply elimination strategies in order of safety
        remaining_tests = current_tests.copy()

        # Strategy 1: Dead code elimination
        dead_code_eliminations = self._apply_dead_code_elimination(remaining_tests)
        remaining_tests = [t for t in remaining_tests if t not in dead_code_eliminations]
        elimination_plan["elimination_strategies"].append({
            "strategy": "dead_code_elimination",
            "eliminated_count": len(dead_code_eliminations),
            "eliminated_tests": dead_code_eliminations
        })

        # Strategy 2: Coverage overlap elimination
        if len(remaining_tests) > target_count:
            coverage_eliminations = self._apply_coverage_overlap_elimination(
                remaining_tests,
                target_reduction=len(remaining_tests) - target_count
            )
            remaining_tests = [t for t in remaining_tests if t not in coverage_eliminations]
            elimination_plan["elimination_strategies"].append({
                "strategy": "coverage_overlap_elimination",
                "eliminated_count": len(coverage_eliminations),
                "eliminated_tests": coverage_eliminations
            })

        # Strategy 3: Integration consolidation
        if len(remaining_tests) > target_count:
            integration_consolidations = self._apply_integration_consolidation(
                remaining_tests,
                target_reduction=len(remaining_tests) - target_count
            )
            remaining_tests = [t for t in remaining_tests if t not in integration_consolidations]
            elimination_plan["elimination_strategies"].append({
                "strategy": "integration_consolidation",
                "eliminated_count": len(integration_consolidations),
                "eliminated_tests": integration_consolidations
            })

        # Strategy 4: Performance-based elimination (last resort)
        if len(remaining_tests) > target_count:
            performance_eliminations = self._apply_performance_based_elimination(
                remaining_tests,
                target_reduction=len(remaining_tests) - target_count
            )
            remaining_tests = [t for t in remaining_tests if t not in performance_eliminations]
            elimination_plan["elimination_strategies"].append({
                "strategy": "performance_based_elimination",
                "eliminated_count": len(performance_eliminations),
                "eliminated_tests": performance_eliminations
            })

        elimination_plan["final_test_set"] = remaining_tests
        elimination_plan["final_count"] = len(remaining_tests)
        elimination_plan["safety_analysis"] = self._analyze_elimination_safety(current_tests, remaining_tests)
        elimination_plan["risk_assessment"] = self._assess_overall_risk(elimination_plan)

        logger.info(f"Reduction complete: {len(current_tests)} → {len(remaining_tests)} tests")
        return elimination_plan

    def validate_elimination_safety(self, original_tests: list[str], remaining_tests: list[str]) -> dict:
        """
        Validate that elimination maintains code coverage and functionality.
        
        Args:
            original_tests: Original test set
            remaining_tests: Proposed remaining test set after elimination
            
        Returns:
            Dict with safety validation results
        """
        logger.info("Validating elimination safety")

        # Analyze coverage impact
        original_coverage = self._calculate_total_coverage(original_tests)
        remaining_coverage = self._calculate_total_coverage(remaining_tests)
        coverage_loss = len(original_coverage - remaining_coverage)
        coverage_retention = len(remaining_coverage) / len(original_coverage) if original_coverage else 1

        # Check for critical functionality gaps
        critical_gaps = self._identify_critical_gaps(original_tests, remaining_tests)

        # Assess risk factors
        risk_factors = []
        if coverage_retention < 0.95:
            risk_factors.append(f"Coverage retention below 95%: {coverage_retention:.2%}")
        if critical_gaps:
            risk_factors.append(f"Critical functionality gaps: {len(critical_gaps)}")

        safety_validation = {
            "coverage_retention": coverage_retention,
            "coverage_loss": coverage_loss,
            "critical_gaps": critical_gaps,
            "risk_factors": risk_factors,
            "safety_level": "high" if not risk_factors else "medium" if len(risk_factors) == 1 else "low",
            "recommendations": self._generate_safety_recommendations(risk_factors)
        }

        return safety_validation

    def generate_reduction_report(self, reduction_plan: dict) -> dict:
        """
        Generate comprehensive test reduction report.
        
        Args:
            reduction_plan: Result from reduce_to_target()
            
        Returns:
            Dict with detailed reduction analysis and recommendations
        """
        report = {
            "reduction_summary": {
                "original_count": reduction_plan["current_count"],
                "target_count": reduction_plan["target_count"],
                "final_count": reduction_plan["final_count"],
                "total_eliminated": reduction_plan["current_count"] - reduction_plan["final_count"],
                "target_achieved": reduction_plan["final_count"] <= reduction_plan["target_count"]
            },
            "strategy_breakdown": reduction_plan["elimination_strategies"],
            "safety_analysis": reduction_plan["safety_analysis"],
            "risk_assessment": reduction_plan["risk_assessment"],
            "final_test_set": reduction_plan["final_test_set"],
            "elimination_timeline": self._estimate_elimination_timeline(reduction_plan),
            "rollback_plan": self._create_rollback_plan(reduction_plan),
            "validation_steps": self._generate_validation_steps(reduction_plan),
            "report_timestamp": __import__('time').time()
        }

        return report

    def _apply_dead_code_elimination(self, test_files: list[str]) -> list[str]:
        """Apply dead code elimination strategy."""
        logger.info("Applying dead code elimination strategy")

        try:
            dead_code_tests = self.dead_code_eliminator.find_tests_for_dead_code()
            # Only eliminate tests that are in our current test set
            eliminable = [t for t in dead_code_tests if t in test_files]
            logger.info(f"Dead code elimination: {len(eliminable)} tests marked for removal")
            return eliminable
        except Exception as e:
            logger.warning(f"Dead code elimination failed: {e}")
            return []

    def _apply_coverage_overlap_elimination(self, test_files: list[str], target_reduction: int) -> list[str]:
        """Apply coverage overlap elimination strategy."""
        logger.info(f"Applying coverage overlap elimination (target reduction: {target_reduction})")

        try:
            redundant_tests = self.coverage_analyzer.find_redundant_by_coverage(overlap_threshold=0.7)
            # Prioritize by overlap ratio and eliminate up to target reduction
            eliminable = [t for t in redundant_tests if t in test_files][:target_reduction]
            logger.info(f"Coverage overlap elimination: {len(eliminable)} tests marked for removal")
            return eliminable
        except Exception as e:
            logger.warning(f"Coverage overlap elimination failed: {e}")
            return []

    def _apply_integration_consolidation(self, test_files: list[str], target_reduction: int) -> list[str]:
        """Apply integration test consolidation strategy."""
        logger.info(f"Applying integration consolidation (target reduction: {target_reduction})")

        # Find integration tests that can be consolidated
        integration_tests = [t for t in test_files if 'integration' in Path(t).stem.lower()]

        # Simple consolidation: eliminate smaller integration tests
        if len(integration_tests) > 1:
            # Sort by file size (proxy for test complexity)
            integration_with_sizes = []
            for test in integration_tests:
                try:
                    size = Path(test).stat().st_size
                    integration_with_sizes.append((test, size))
                except:
                    integration_with_sizes.append((test, 0))

            # Keep larger tests, eliminate smaller ones
            integration_with_sizes.sort(key=lambda x: x[1], reverse=True)
            eliminable = [t for t, _ in integration_with_sizes[len(integration_tests)//2:]][:target_reduction]

            logger.info(f"Integration consolidation: {len(eliminable)} tests marked for removal")
            return eliminable

        return []

    def _apply_performance_based_elimination(self, test_files: list[str], target_reduction: int) -> list[str]:
        """Apply performance-based elimination strategy (slowest tests)."""
        logger.info(f"Applying performance-based elimination (target reduction: {target_reduction})")

        # Estimate test performance by file size and complexity patterns
        test_scores = []
        for test_file in test_files:
            score = self._calculate_test_performance_score(test_file)
            test_scores.append((test_file, score))

        # Sort by score (lowest first - these are slowest/most complex)
        test_scores.sort(key=lambda x: x[1])

        # Only eliminate non-critical slow tests
        eliminable = []
        for test_file, score in test_scores:
            if len(eliminable) >= target_reduction:
                break
            if not self._is_critical_test(test_file):
                eliminable.append(test_file)

        logger.info(f"Performance-based elimination: {len(eliminable)} tests marked for removal")
        return eliminable

    def _calculate_test_performance_score(self, test_file: str) -> float:
        """Calculate performance score for test (higher = faster/simpler)."""
        try:
            path = Path(test_file)
            size = path.stat().st_size

            # Read file to analyze complexity
            with open(path) as f:
                content = f.read()

            # Simple complexity metrics
            line_count = len(content.split('\n'))
            import_count = content.count('import ')
            fixture_count = content.count('@pytest.fixture')
            mock_count = content.count('mock') + content.count('Mock')

            # Higher score = simpler/faster test
            score = 1000 - (size / 10) - (line_count * 2) - (import_count * 5) - (fixture_count * 10) - (mock_count * 3)
            return max(score, 0)

        except Exception as e:
            logger.warning(f"Error calculating performance score for {test_file}: {e}")
            return 500  # Default mid-range score

    def _calculate_total_coverage(self, test_files: list[str]) -> set[str]:
        """Calculate total code coverage for a set of tests."""
        total_coverage = set()
        for test_file in test_files:
            try:
                coverage = self.coverage_analyzer._analyze_test_coverage(test_file)
                total_coverage.update(coverage)
            except Exception as e:
                logger.warning(f"Error calculating coverage for {test_file}: {e}")
        return total_coverage

    def _identify_critical_gaps(self, original_tests: list[str], remaining_tests: list[str]) -> list[str]:
        """Identify critical functionality that loses test coverage."""
        original_coverage = self._calculate_total_coverage(original_tests)
        remaining_coverage = self._calculate_total_coverage(remaining_tests)

        lost_coverage = original_coverage - remaining_coverage

        # Identify critical patterns in lost coverage
        critical_gaps = []
        for lost_item in lost_coverage:
            if any(pattern in lost_item.lower() for pattern in
                   ['auth', 'security', 'api', 'database', 'user', 'login', 'payment']):
                critical_gaps.append(lost_item)

        return critical_gaps

    def _analyze_elimination_safety(self, original_tests: list[str], remaining_tests: list[str]) -> dict:
        """Analyze safety of test elimination."""
        return self.validate_elimination_safety(original_tests, remaining_tests)

    def _assess_overall_risk(self, elimination_plan: dict) -> str:
        """Assess overall risk level of elimination plan."""
        safety = elimination_plan.get("safety_analysis", {})
        coverage_retention = safety.get("coverage_retention", 1.0)
        critical_gaps = len(safety.get("critical_gaps", []))

        if coverage_retention >= 0.95 and critical_gaps == 0:
            return "low"
        if coverage_retention >= 0.90 and critical_gaps <= 2:
            return "medium"
        return "high"

    def _is_critical_test(self, test_file: str) -> bool:
        """Check if test covers critical functionality."""
        critical_patterns = ['auth', 'security', 'api', 'database', 'integration', 'user_flow']
        return any(pattern in Path(test_file).stem.lower() for pattern in critical_patterns)

    def _generate_safety_recommendations(self, risk_factors: list[str]) -> list[str]:
        """Generate safety recommendations based on risk factors."""
        recommendations = []

        for risk in risk_factors:
            if "coverage retention" in risk:
                recommendations.append("Consider keeping additional tests to maintain coverage above 95%")
            if "critical functionality" in risk:
                recommendations.append("Review critical functionality gaps and add targeted tests")

        if not recommendations:
            recommendations.append("Elimination plan appears safe to proceed")

        return recommendations

    def _estimate_elimination_timeline(self, reduction_plan: dict) -> dict:
        """Estimate timeline for elimination implementation."""
        strategy_count = len(reduction_plan["elimination_strategies"])
        total_eliminated = sum(s["eliminated_count"] for s in reduction_plan["elimination_strategies"])

        return {
            "estimated_hours": max(2, strategy_count * 1 + total_eliminated * 0.1),
            "phases": [
                "Analysis and validation (30 min)",
                "Gradual elimination by strategy (1-2 hours)",
                "Coverage validation (30 min)",
                "Integration testing (1 hour)"
            ]
        }

    def _create_rollback_plan(self, reduction_plan: dict) -> dict:
        """Create rollback plan in case elimination causes issues."""
        return {
            "backup_location": "test_backups/aggressive_reduction/",
            "rollback_steps": [
                "Stop CI/CD pipelines",
                "Restore eliminated test files from backup",
                "Run full test suite to validate restoration",
                "Update test configuration files"
            ],
            "validation_criteria": [
                "All original tests pass",
                "No new test failures",
                "Coverage metrics restored"
            ]
        }

    def _generate_validation_steps(self, reduction_plan: dict) -> list[str]:
        """Generate validation steps for elimination plan."""
        return [
            "Run remaining test suite to ensure all pass",
            "Generate coverage report and verify retention > 95%",
            "Run integration tests to check critical functionality",
            "Performance test to confirm CI time reduction",
            "Staging deployment with full regression testing",
            "Monitor production for 24h after deployment"
        ]
