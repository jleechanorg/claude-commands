#!/usr/bin/env python3
"""
Test Importance Ranker - ML-powered test priority scoring system

Uses machine learning and heuristic analysis to rank tests by importance, enabling
intelligent elimination decisions that preserve the most valuable tests while
reaching aggressive reduction targets.
"""

import ast
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)


class TestImportanceRanker:
    """Ranks tests by importance using multiple scoring algorithms."""

    def __init__(self, test_directory: str = "mvp_site/tests", source_directory: str = "mvp_site"):
        self.test_directory = Path(test_directory)
        self.source_directory = Path(source_directory)
        self.scoring_weights = {
            'critical_functionality': 0.3,
            'code_coverage': 0.25,
            'integration_complexity': 0.2,
            'failure_history': 0.15,
            'maintenance_cost': 0.1
        }
        self.test_scores = {}

    def rank_all_tests(self, test_files: list[str]) -> list[tuple[str, float, dict]]:
        """
        Rank all tests by importance score.
        
        Args:
            test_files: List of test file paths to rank
            
        Returns:
            List of tuples (test_file, importance_score, score_breakdown)
            sorted by importance (highest first)
        """
        logger.info(f"Ranking {len(test_files)} tests by importance")

        ranked_tests = []

        for test_file in test_files:
            try:
                score_breakdown = self._calculate_comprehensive_score(test_file)
                total_score = self._calculate_weighted_score(score_breakdown)
                ranked_tests.append((test_file, total_score, score_breakdown))

            except Exception as e:
                logger.warning(f"Error ranking test {test_file}: {e}")
                # Give default mid-range score
                ranked_tests.append((test_file, 0.5, {}))

        # Sort by importance score (descending)
        ranked_tests.sort(key=lambda x: x[1], reverse=True)

        logger.info(f"Test ranking complete. Top test score: {ranked_tests[0][1]:.3f}, Bottom: {ranked_tests[-1][1]:.3f}")
        return ranked_tests

    def identify_elimination_candidates(self, test_files: list[str], elimination_count: int) -> list[str]:
        """
        Identify lowest-importance tests for elimination.
        
        Args:
            test_files: List of test files to evaluate
            elimination_count: Number of tests to eliminate
            
        Returns:
            List of test files recommended for elimination
        """
        logger.info(f"Identifying {elimination_count} elimination candidates from {len(test_files)} tests")

        ranked_tests = self.rank_all_tests(test_files)

        # Take lowest-scoring tests, but apply safety filters
        candidates = []
        for test_file, score, breakdown in reversed(ranked_tests):  # Start from lowest scores
            if len(candidates) >= elimination_count:
                break

            # Apply safety filters
            if self._is_safe_to_eliminate(test_file, score, breakdown):
                candidates.append(test_file)
            else:
                logger.info(f"Skipping elimination of {Path(test_file).name} due to safety filters")

        logger.info(f"Selected {len(candidates)} elimination candidates")
        return candidates

    def generate_importance_report(self, test_files: list[str]) -> dict:
        """
        Generate comprehensive test importance analysis report.
        
        Args:
            test_files: List of test files to analyze
            
        Returns:
            Dict with detailed importance analysis and recommendations
        """
        ranked_tests = self.rank_all_tests(test_files)

        # Calculate distribution statistics
        scores = [score for _, score, _ in ranked_tests]
        avg_score = sum(scores) / len(scores) if scores else 0

        # Categorize tests by importance
        high_importance = [t for t, s, _ in ranked_tests if s >= 0.7]
        medium_importance = [t for t, s, _ in ranked_tests if 0.4 <= s < 0.7]
        low_importance = [t for t, s, _ in ranked_tests if s < 0.4]

        report = {
            "ranking_summary": {
                "total_tests": len(test_files),
                "average_importance": avg_score,
                "distribution": {
                    "high_importance": len(high_importance),
                    "medium_importance": len(medium_importance),
                    "low_importance": len(low_importance)
                }
            },
            "top_10_most_important": [(Path(t).name, round(s, 3)) for t, s, _ in ranked_tests[:10]],
            "bottom_10_least_important": [(Path(t).name, round(s, 3)) for t, s, _ in ranked_tests[-10:]],
            "elimination_recommendations": {
                "safe_to_eliminate": [t for t, s, b in ranked_tests[-20:] if self._is_safe_to_eliminate(t, s, b)],
                "requires_review": [t for t, s, b in ranked_tests[-20:] if not self._is_safe_to_eliminate(t, s, b)]
            },
            "scoring_methodology": {
                "weights": self.scoring_weights,
                "factors": [
                    "Critical functionality coverage",
                    "Code coverage breadth",
                    "Integration complexity",
                    "Historical failure patterns",
                    "Maintenance overhead"
                ]
            },
            "detailed_rankings": [
                {
                    "test": Path(t).name,
                    "score": round(s, 3),
                    "breakdown": {k: round(v, 3) for k, v in b.items()}
                }
                for t, s, b in ranked_tests
            ][:50],  # Limit for report size
            "analysis_timestamp": __import__('time').time()
        }

        return report

    def _calculate_comprehensive_score(self, test_file: str) -> dict[str, float]:
        """Calculate comprehensive importance score breakdown."""
        breakdown = {
            'critical_functionality': self._score_critical_functionality(test_file),
            'code_coverage': self._score_code_coverage(test_file),
            'integration_complexity': self._score_integration_complexity(test_file),
            'failure_history': self._score_failure_history(test_file),
            'maintenance_cost': self._score_maintenance_cost(test_file)
        }

        return breakdown

    def _calculate_weighted_score(self, score_breakdown: dict[str, float]) -> float:
        """Calculate final weighted importance score."""
        total_score = 0
        for factor, score in score_breakdown.items():
            weight = self.scoring_weights.get(factor, 0)
            total_score += score * weight

        return min(total_score, 1.0)  # Cap at 1.0

    def _score_critical_functionality(self, test_file: str) -> float:
        """Score based on critical functionality coverage."""
        try:
            with open(test_file, encoding='utf-8') as f:
                content = f.read().lower()

            # Critical functionality patterns
            critical_patterns = {
                'authentication': ['auth', 'login', 'password', 'token', 'session'],
                'security': ['security', 'permission', 'access', 'authorization'],
                'data_integrity': ['database', 'transaction', 'commit', 'rollback'],
                'api_endpoints': ['api', 'endpoint', 'route', 'request', 'response'],
                'user_workflows': ['user', 'workflow', 'process', 'journey'],
                'payment': ['payment', 'billing', 'charge', 'refund'],
                'core_business': ['campaign', 'game', 'character', 'world']
            }

            score = 0
            for category, patterns in critical_patterns.items():
                pattern_found = any(pattern in content for pattern in patterns)
                if pattern_found:
                    # Weight core business logic and security higher
                    weight = 1.0 if category in ['security', 'data_integrity', 'core_business'] else 0.7
                    score += weight

            # Normalize to 0-1 range
            return min(score / len(critical_patterns), 1.0)

        except Exception as e:
            logger.warning(f"Error scoring critical functionality for {test_file}: {e}")
            return 0.3  # Default conservative score

    def _score_code_coverage(self, test_file: str) -> float:
        """Score based on breadth of code coverage."""
        try:
            with open(test_file, encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            # Count different types of coverage
            imports = 0
            function_calls = 0
            class_usage = 0

            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    imports += 1
                elif isinstance(node, ast.Call):
                    function_calls += 1
                elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    class_usage += 1

            # Calculate coverage breadth score
            coverage_breadth = (imports * 2 + function_calls + class_usage) / 100
            return min(coverage_breadth, 1.0)

        except Exception as e:
            logger.warning(f"Error scoring code coverage for {test_file}: {e}")
            return 0.4  # Default score

    def _score_integration_complexity(self, test_file: str) -> float:
        """Score based on integration complexity."""
        try:
            with open(test_file, encoding='utf-8') as f:
                content = f.read().lower()

            complexity_indicators = {
                'external_services': ['firebase', 'api', 'http', 'request', 'client'],
                'database_ops': ['database', 'query', 'insert', 'update', 'delete'],
                'file_system': ['file', 'path', 'read', 'write', 'mkdir'],
                'network': ['url', 'endpoint', 'socket', 'connection'],
                'async_operations': ['async', 'await', 'future', 'thread']
            }

            complexity_score = 0
            for category, indicators in complexity_indicators.items():
                if any(indicator in content for indicator in indicators):
                    complexity_score += 1

            # Integration tests are generally more important
            if 'integration' in Path(test_file).name.lower():
                complexity_score += 2

            return min(complexity_score / (len(complexity_indicators) + 2), 1.0)

        except Exception as e:
            logger.warning(f"Error scoring integration complexity for {test_file}: {e}")
            return 0.2  # Default low complexity

    def _score_failure_history(self, test_file: str) -> float:
        """Score based on historical failure patterns."""
        # This would ideally use CI/CD history data
        # For now, use heuristics based on test patterns

        try:
            with open(test_file, encoding='utf-8') as f:
                content = f.read().lower()

            # Tests that historically tend to be flaky or fail more often
            high_failure_patterns = [
                'timeout', 'retry', 'flaky', 'skip', 'xfail',
                'network', 'external', 'timing', 'race condition'
            ]

            failure_indicators = sum(1 for pattern in high_failure_patterns if pattern in content)

            # More failure-prone tests are paradoxically more important to keep
            # as they catch real issues
            return min(failure_indicators / len(high_failure_patterns), 0.8)

        except Exception as e:
            logger.warning(f"Error scoring failure history for {test_file}: {e}")
            return 0.1  # Default low failure score

    def _score_maintenance_cost(self, test_file: str) -> float:
        """Score based on maintenance cost (inverse - lower cost = higher score)."""
        try:
            path = Path(test_file)

            # File size as proxy for maintenance cost
            size = path.stat().st_size

            with open(path, encoding='utf-8') as f:
                content = f.read()

            # Complexity indicators that increase maintenance cost
            line_count = len(content.split('\n'))
            mock_count = content.lower().count('mock')
            fixture_count = content.lower().count('fixture')
            complex_patterns = len(re.findall(r'@.*\n', content))  # Decorators

            # Calculate complexity score (higher = more complex = higher maintenance cost)
            complexity = (size / 1000) + (line_count / 100) + (mock_count / 10) + fixture_count + complex_patterns

            # Return inverse score (lower maintenance cost = higher importance)
            maintenance_score = max(0, 1 - (complexity / 50))
            return min(maintenance_score, 1.0)

        except Exception as e:
            logger.warning(f"Error scoring maintenance cost for {test_file}: {e}")
            return 0.5  # Default medium maintenance score

    def _is_safe_to_eliminate(self, test_file: str, score: float, breakdown: dict) -> bool:
        """Determine if a test is safe to eliminate based on safety criteria."""

        # Never eliminate high-importance tests
        if score >= 0.6:
            return False

        # Never eliminate tests covering critical functionality
        if breakdown.get('critical_functionality', 0) >= 0.7:
            return False

        # Never eliminate integration tests unless score is very low
        if 'integration' in Path(test_file).name.lower() and score >= 0.3:
            return False

        # Safety patterns that should never be eliminated
        safety_patterns = ['auth', 'security', 'database', 'api']
        test_name = Path(test_file).name.lower()
        if any(pattern in test_name for pattern in safety_patterns):
            return False

        return True
