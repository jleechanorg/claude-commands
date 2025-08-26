#!/usr/bin/env python3
"""
Elimination Safety Checker - Validates test elimination decisions for safety

Comprehensive safety validation system that ensures test elimination decisions
maintain critical functionality coverage and don't introduce risks to the
codebase integrity. Critical component for aggressive test reduction.
"""

import logging
from typing import Dict, List, Set
from pathlib import Path


logger = logging.getLogger(__name__)


class EliminationSafetyChecker:
    def __init__(self, test_suite, coverage_data, dependency_graph):
        self.test_suite = test_suite
        self.coverage_data = coverage_data
        self.dependency_graph = dependency_graph
        self.safety_report = {}
    
    def validate_elimination_safety(self, tests_to_eliminate):
        """Validate if eliminating specified tests is safe"""
        risks = self.identify_critical_risks(tests_to_eliminate)
        coverage_impact = self.check_coverage_retention(tests_to_eliminate)
        
        is_safe = len(risks['critical']) == 0 and coverage_impact['retention_ratio'] >= 0.8
        
        self.safety_report = {
            'is_safe': is_safe,
            'risks': risks,
            'coverage_impact': coverage_impact
        }
        
        return is_safe
    
    def check_coverage_retention(self, tests_to_eliminate):
        """Check how much code coverage is retained after elimination"""
        total_lines = set()
        remaining_lines = set()
        
        for test in self.test_suite:
            total_lines.update(self.coverage_data.get(test, set()))
        
        for test in self.test_suite:
            if test not in tests_to_eliminate:
                remaining_lines.update(self.coverage_data.get(test, set()))
        
        retention_ratio = len(remaining_lines) / len(total_lines) if total_lines else 1.0
        
        return {
            'original_coverage': len(total_lines),
            'remaining_coverage': len(remaining_lines),
            'retention_ratio': retention_ratio
        }
    
    def identify_critical_risks(self, tests_to_eliminate):
        """Identify critical risks associated with test elimination"""
        critical_risks = []
        high_risks = []
        
        for test in tests_to_eliminate:
            dependencies = self.dependency_graph.get(test, set())
            
            # Check for tests that others depend on
            if dependencies:
                for dep in dependencies:
                    if dep in self.test_suite and dep not in tests_to_eliminate:
                        critical_risks.append(f"Test {test} is depended on by {dep}")
            
            # Check for integration tests
            if 'integration' in test.lower() or 'e2e' in test.lower():
                critical_risks.append(f"Test {test} is an integration/E2E test")
        
        return {
            'critical': critical_risks,
            'high': high_risks
        }
    
    def generate_safety_report(self):
        """Generate detailed safety report"""
        return self.safety_report

    def perform_comprehensive_safety_analysis(self, tests_to_eliminate: List[str]) -> Dict:
        """Perform comprehensive safety analysis for test elimination."""
        logger.info(f"Performing comprehensive safety analysis for {len(tests_to_eliminate)} tests")
        
        analysis = {
            'timestamp': __import__('time').time(),
            'tests_analyzed': len(tests_to_eliminate),
            'safety_checks': {},
            'risk_assessment': 'low',
            'recommendations': [],
            'critical_issues': []
        }
        
        # Safety Check 1: Coverage retention
        coverage_check = self.check_coverage_retention(tests_to_eliminate)
        analysis['safety_checks']['coverage_retention'] = coverage_check
        
        if coverage_check['retention_ratio'] < 0.95:
            analysis['critical_issues'].append(f"Coverage retention below 95%: {coverage_check['retention_ratio']:.2%}")
            analysis['risk_assessment'] = 'high'
        
        # Safety Check 2: Critical functionality
        critical_risks = self.identify_critical_risks(tests_to_eliminate)
        analysis['safety_checks']['critical_risks'] = critical_risks
        
        if critical_risks['critical']:
            analysis['critical_issues'].extend(critical_risks['critical'])
            analysis['risk_assessment'] = 'high'
        
        # Safety Check 3: Test dependencies
        dependency_issues = self._check_test_dependencies(tests_to_eliminate)
        analysis['safety_checks']['dependency_issues'] = dependency_issues
        
        if dependency_issues:
            analysis['critical_issues'].extend(dependency_issues)
            analysis['risk_assessment'] = 'medium' if analysis['risk_assessment'] == 'low' else 'high'
        
        # Generate recommendations
        analysis['recommendations'] = self._generate_safety_recommendations(analysis)
        
        return analysis

    def _check_test_dependencies(self, tests_to_eliminate: List[str]) -> List[str]:
        """Check for test dependency issues."""
        issues = []
        
        for test in tests_to_eliminate:
            # Check if other tests depend on this test's setup/fixtures
            test_name = Path(test).stem
            
            # Look for dependency patterns
            for other_test in self.test_suite:
                if other_test not in tests_to_eliminate and other_test != test:
                    try:
                        with open(other_test, 'r') as f:
                            content = f.read()
                        
                        # Check for imports or references to eliminated test
                        if test_name in content or f"from {test_name}" in content:
                            issues.append(f"Test {other_test} may depend on eliminated test {test}")
                    except Exception as e:
                        logger.warning(f"Error checking dependencies for {other_test}: {e}")
        
        return issues

    def _generate_safety_recommendations(self, analysis: Dict) -> List[str]:
        """Generate safety recommendations based on analysis."""
        recommendations = []
        
        if analysis['risk_assessment'] == 'high':
            recommendations.append("CRITICAL: Do not proceed with elimination - high risk detected")
            recommendations.append("Review and address all critical issues before elimination")
        elif analysis['risk_assessment'] == 'medium':
            recommendations.append("CAUTION: Proceed with careful monitoring")
            recommendations.append("Consider gradual elimination with validation at each step")
        else:
            recommendations.append("SAFE: Elimination can proceed with normal monitoring")
        
        # Specific recommendations based on issues
        coverage = analysis['safety_checks'].get('coverage_retention', {})
        if coverage.get('retention_ratio', 1) < 0.95:
            recommendations.append("Add targeted tests to maintain coverage above 95%")
        
        critical_risks = analysis['safety_checks'].get('critical_risks', {})
        if critical_risks.get('critical'):
            recommendations.append("Review integration/E2E test elimination - consider keeping critical tests")
        
        return recommendations