#!/usr/bin/env python3
"""
Fake/Demo/Simulation Detection Utility

Detects patterns that indicate fake, simulated, or demo implementations
instead of real working functionality.
"""

import ast
import os
import re
from dataclasses import dataclass
from typing import Any, List


@dataclass
class FakePattern:
    """Represents a detected fake implementation pattern"""

    type: str  # 'hardcoded', 'todo', 'placeholder', 'ignored_params', etc.
    severity: str  # 'critical', 'high', 'medium', 'low'
    location: str  # file:line or function name
    description: str
    evidence: str  # the actual code or text that triggered detection
    suggestion: str  # how to fix it


class FakeDetector:
    """Detects fake, demo, and simulated code patterns"""

    def __init__(self):
        self.patterns = []

    def analyze_file(self, filepath: str) -> List[FakePattern]:
        """Analyze a Python file for fake patterns"""
        if not os.path.exists(filepath):
            return []

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            patterns = []
            patterns.extend(self._check_text_patterns(content, filepath))
            patterns.extend(self._check_ast_patterns(content, filepath))

            return patterns

        except Exception as e:
            return [
                FakePattern(
                    type="analysis_error",
                    severity="low",
                    location=filepath,
                    description=f"Could not analyze file: {str(e)}",
                    evidence="",
                    suggestion="Check file syntax and permissions",
                )
            ]

    def analyze_code_string(
        self, code: str, context: str = "code"
    ) -> List[FakePattern]:
        """Analyze a code string for fake patterns"""
        patterns = []
        patterns.extend(self._check_text_patterns(code, context))
        patterns.extend(self._check_ast_patterns(code, context))
        return patterns

    def _check_text_patterns(self, content: str, location: str) -> List[FakePattern]:
        """Check for text-based fake patterns"""
        patterns = []
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()

            # TODO comments indicating unfinished work
            if re.search(
                r"#\s*TODO.*(?:implement|fix|replace|temporary|placeholder|fake|demo)",
                line_stripped,
                re.IGNORECASE,
            ):
                patterns.append(
                    FakePattern(
                        type="todo_unfinished",
                        severity="high",
                        location=f"{location}:{i}",
                        description="TODO comment indicates unfinished implementation",
                        evidence=line_stripped,
                        suggestion="Complete the implementation or remove the TODO",
                    )
                )

            # Placeholder text patterns
            placeholder_patterns = [
                r"placeholder.*(?:implementation|data|response)",
                r"(?:fake|mock|demo|simulated).*(?:data|response|result)",
                r"hardcoded.*(?:for now|temporarily)",
                r"return.*(?:fake|placeholder|demo)",
                r"would be (?:implemented|performed|called) here",
            ]

            for pattern in placeholder_patterns:
                if re.search(pattern, line_stripped, re.IGNORECASE):
                    patterns.append(
                        FakePattern(
                            type="placeholder_text",
                            severity="medium",
                            location=f"{location}:{i}",
                            description="Placeholder or demo text detected",
                            evidence=line_stripped,
                            suggestion="Replace with actual implementation",
                        )
                    )

            # Hardcoded percentage or status values
            if re.search(
                r"(?:ready|complete|success).*(?:percent|%)\s*[:\=]\s*\d+",
                line_stripped,
                re.IGNORECASE,
            ):
                patterns.append(
                    FakePattern(
                        type="hardcoded_percentage",
                        severity="high",
                        location=f"{location}:{i}",
                        description="Hardcoded percentage value detected",
                        evidence=line_stripped,
                        suggestion="Calculate percentage dynamically based on actual analysis",
                    )
                )

        return patterns

    def _check_ast_patterns(self, content: str, location: str) -> List[FakePattern]:
        """Check for AST-based fake patterns"""
        patterns = []

        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                # Functions that always return the same value
                if isinstance(node, ast.FunctionDef):
                    patterns.extend(self._check_function_patterns(node, location))

                # Hardcoded dictionaries with suspicious patterns
                if isinstance(node, ast.Dict):
                    patterns.extend(self._check_dict_patterns(node, location))

        except SyntaxError:
            # File might not be valid Python, skip AST analysis
            pass

        return patterns

    def _check_function_patterns(
        self, func_node: ast.FunctionDef, location: str
    ) -> List[FakePattern]:
        """Check function for fake patterns"""
        patterns = []

        # Check if function ignores its parameters
        param_names = [arg.arg for arg in func_node.args.args]

        if param_names:
            # Look for parameters that are never used in the function
            func_source = ast.unparse(func_node) if hasattr(ast, "unparse") else ""
            unused_params = []

            for param in param_names:
                if (
                    param not in func_source or func_source.count(param) <= 1
                ):  # Only appears in definition
                    unused_params.append(param)

            if len(unused_params) > len(param_names) * 0.5:  # More than half unused
                patterns.append(
                    FakePattern(
                        type="ignored_parameters",
                        severity="high",
                        location=f"{location}:{func_node.lineno}",
                        description=f"Function '{func_node.name}' ignores most of its parameters: {unused_params}",
                        evidence=f"def {func_node.name}({', '.join(param_names)})",
                        suggestion="Use the parameters in the implementation or remove unused ones",
                    )
                )

        # Check for functions that always return the same hardcoded value
        return_nodes = [n for n in ast.walk(func_node) if isinstance(n, ast.Return)]
        if len(return_nodes) == 1 and isinstance(
            return_nodes[0].value, (ast.Dict, ast.List, ast.Constant)
        ):
            patterns.append(
                FakePattern(
                    type="hardcoded_return",
                    severity="critical",
                    location=f"{location}:{func_node.lineno}",
                    description=f"Function '{func_node.name}' always returns the same hardcoded value",
                    evidence="Function has single hardcoded return statement",
                    suggestion="Make return value depend on function inputs and logic",
                )
            )

        return patterns

    def _check_dict_patterns(
        self, dict_node: ast.Dict, location: str
    ) -> List[FakePattern]:
        """Check dictionary for suspicious hardcoded patterns"""
        patterns = []

        # Look for dictionaries with keys suggesting fake data
        if hasattr(dict_node, "keys"):
            key_values = []
            for key in dict_node.keys:
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    key_values.append(key.value.lower())

            fake_indicators = [
                "production_ready_percent",
                "success_probability",
                "verdict",
                "summary",
            ]
            suspicious_keys = [
                k
                for k in key_values
                if any(indicator in k for indicator in fake_indicators)
            ]

            if suspicious_keys:
                patterns.append(
                    FakePattern(
                        type="suspicious_dict",
                        severity="medium",
                        location=f"{location}:{dict_node.lineno}",
                        description=f"Dictionary contains keys that suggest hardcoded analysis results: {suspicious_keys}",
                        evidence=f"Keys: {suspicious_keys}",
                        suggestion="Generate these values dynamically based on actual analysis",
                    )
                )

        return patterns

    def analyze_function_behavior(
        self, func, test_inputs: List[Any]
    ) -> List[FakePattern]:
        """Analyze if a function returns the same output for different inputs"""
        if not test_inputs or len(test_inputs) < 2:
            return []

        patterns = []
        results = []

        try:
            for test_input in test_inputs:
                if isinstance(test_input, (list, tuple)):
                    result = func(*test_input)
                else:
                    result = func(test_input)
                results.append(result)

            # Check if all results are identical
            if len(set(str(r) for r in results)) == 1:
                patterns.append(
                    FakePattern(
                        type="identical_outputs",
                        severity="critical",
                        location=func.__name__
                        if hasattr(func, "__name__")
                        else "unknown",
                        description="Function returns identical results for different inputs",
                        evidence=f"Same output for inputs: {test_inputs}",
                        suggestion="Make function output depend on input values",
                    )
                )

        except Exception:
            # Function might not be callable or might have errors
            pass

        return patterns

    def generate_report(self, patterns: List[FakePattern]) -> str:
        """Generate a human-readable report of fake patterns"""
        if not patterns:
            return "✅ No fake/demo patterns detected"

        report = ["🚨 FAKE/DEMO PATTERNS DETECTED", ""]

        by_severity = {}
        for pattern in patterns:
            if pattern.severity not in by_severity:
                by_severity[pattern.severity] = []
            by_severity[pattern.severity].append(pattern)

        for severity in ["critical", "high", "medium", "low"]:
            if severity in by_severity:
                report.append(
                    f"### {severity.upper()} ISSUES ({len(by_severity[severity])})"
                )
                for pattern in by_severity[severity]:
                    report.append(f"**{pattern.type}** - {pattern.location}")
                    report.append(f"  {pattern.description}")
                    if pattern.evidence:
                        report.append(f"  Evidence: `{pattern.evidence}`")
                    report.append(f"  Fix: {pattern.suggestion}")
                    report.append("")

        return "\n".join(report)


# Convenience functions
def detect_fake_patterns_in_file(filepath: str) -> List[FakePattern]:
    """Quick function to detect fake patterns in a file"""
    detector = FakeDetector()
    return detector.analyze_file(filepath)


def detect_fake_patterns_in_code(code: str, context: str = "code") -> List[FakePattern]:
    """Quick function to detect fake patterns in code string"""
    detector = FakeDetector()
    return detector.analyze_code_string(code, context)


def generate_fake_report(filepath: str) -> str:
    """Generate a fake detection report for a file"""
    detector = FakeDetector()
    patterns = detector.analyze_file(filepath)
    return detector.generate_report(patterns)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        print(generate_fake_report(filepath))
    else:
        print("Usage: python fake_detector.py <filepath>")
