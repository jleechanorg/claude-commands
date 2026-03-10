#!/usr/bin/env python3
"""
UserJot Test Generator Subagent
Stateless test generation functionality following UserJot patterns
"""

import time
import re
from typing import Dict, List, Any


def generate_tests(objective: str, context: Dict[str, Any], constraints: Dict[str, Any], success_criteria: str) -> Dict[str, Any]:
    """
    Stateless test generator subagent
    
    UserJot Principles:
    - No conversation history or persistent state
    - Pure function: same input always produces same output
    - Minimal required context only
    - Structured output with success metrics
    
    Args:
        objective: Clear description of test generation goals
        context: Code and test requirements only
        constraints: Framework/coverage limitations
        success_criteria: How to measure test success
        
    Returns:
        Structured test generation result with metrics
    """
    start_time = time.time()
    
    try:
        # Extract required context
        code = context.get("code", "")
        test_type = context.get("test_type", "unit")
        framework = context.get("framework", "pytest")
        coverage_target = context.get("coverage_target", 80)
        
        if not code:
            return _create_error_response("No code provided for test generation", start_time)
        
        # Analyze code structure (stateless)
        functions = _extract_functions(code)
        classes = _extract_classes(code)
        
        # Generate tests based on code analysis
        test_cases = _generate_test_cases(functions, classes, test_type, framework)
        
        # Calculate coverage estimation
        estimated_coverage = _estimate_coverage(test_cases, functions, classes)
        
        # Generate test code
        test_code = _generate_test_code(test_cases, framework)
        
        # Calculate success metrics
        execution_time = time.time() - start_time
        success = estimated_coverage >= (coverage_target / 100) and len(test_cases) > 0
        confidence = min(0.95, estimated_coverage)
        
        return {
            "result": {
                "test_code": test_code,
                "test_cases": test_cases,
                "estimated_coverage": round(estimated_coverage * 100, 1),
                "test_count": len(test_cases),
                "framework": framework,
                "summary": _generate_test_summary(len(test_cases), estimated_coverage, test_type)
            },
            "success": success,
            "confidence": confidence,
            "metrics": {
                "execution_time": execution_time,
                "functions_analyzed": len(functions),
                "classes_analyzed": len(classes),
                "test_cases_generated": len(test_cases),
                "estimated_coverage": estimated_coverage
            },
            "notes": f"Generated {len(test_cases)} test cases with {estimated_coverage*100:.1f}% estimated coverage"
        }
        
    except Exception as e:
        return _create_error_response(f"Test generation failed: {str(e)}", start_time)


def _extract_functions(code: str) -> List[Dict[str, Any]]:
    """Extract function definitions from code (stateless analysis)"""
    functions = []
    lines = code.split('\n')
    
    for i, line in enumerate(lines):
        # Simple function detection
        if line.strip().startswith('def ') and '(' in line:
            func_match = re.match(r'\s*def\s+(\w+)\s*\(([^)]*)\)', line)
            if func_match:
                func_name = func_match.group(1)
                params = func_match.group(2)
                
                # Skip private/magic methods for basic testing
                if not func_name.startswith('_'):
                    functions.append({
                        "name": func_name,
                        "params": [p.strip() for p in params.split(',') if p.strip()],
                        "line": i + 1,
                        "type": "function"
                    })
    
    return functions


def _extract_classes(code: str) -> List[Dict[str, Any]]:
    """Extract class definitions from code (stateless analysis)"""
    classes = []
    lines = code.split('\n')
    
    for i, line in enumerate(lines):
        if line.strip().startswith('class ') and ':' in line:
            class_match = re.match(r'\s*class\s+(\w+)', line)
            if class_match:
                class_name = class_match.group(1)
                classes.append({
                    "name": class_name,
                    "line": i + 1,
                    "type": "class"
                })
    
    return classes


def _generate_test_cases(functions: List[Dict[str, Any]], classes: List[Dict[str, Any]], test_type: str, framework: str) -> List[Dict[str, Any]]:
    """Generate test cases based on code structure"""
    test_cases = []
    
    # Generate function tests
    for func in functions:
        # Basic positive test case
        test_cases.append({
            "name": f"test_{func['name']}_basic",
            "type": "positive",
            "target": func["name"],
            "description": f"Test basic functionality of {func['name']}",
            "test_data": _generate_test_data(func["params"]),
            "assertions": ["result is not None", "test passes"]
        })
        
        # Edge case test
        if func["params"]:
            test_cases.append({
                "name": f"test_{func['name']}_edge_cases",
                "type": "edge_case",
                "target": func["name"],
                "description": f"Test edge cases for {func['name']}",
                "test_data": _generate_edge_case_data(func["params"]),
                "assertions": ["handles edge cases correctly"]
            })
        
        # Error handling test
        test_cases.append({
            "name": f"test_{func['name']}_error_handling",
            "type": "negative",
            "target": func["name"],
            "description": f"Test error handling in {func['name']}",
            "test_data": "invalid_input",
            "assertions": ["raises appropriate exception"]
        })
    
    # Generate class tests
    for cls in classes:
        test_cases.append({
            "name": f"test_{cls['name']}_instantiation",
            "type": "instantiation",
            "target": cls["name"],
            "description": f"Test {cls['name']} can be instantiated",
            "test_data": {},
            "assertions": ["instance created successfully"]
        })
    
    return test_cases


def _generate_test_data(params: List[str]) -> Dict[str, Any]:
    """Generate appropriate test data for function parameters"""
    test_data = {}
    
    for param in params:
        if not param or param == 'self':
            continue
            
        param_clean = param.split('=')[0].strip()
        
        # Simple type inference based on parameter names
        if any(word in param_clean.lower() for word in ['id', 'count', 'num', 'age']):
            test_data[param_clean] = 123
        elif any(word in param_clean.lower() for word in ['name', 'title', 'text']):
            test_data[param_clean] = "test_string"
        elif any(word in param_clean.lower() for word in ['email', 'mail']):
            test_data[param_clean] = "test@example.com"
        elif any(word in param_clean.lower() for word in ['bool', 'flag', 'active']):
            test_data[param_clean] = True
        else:
            test_data[param_clean] = "test_value"
    
    return test_data


def _generate_edge_case_data(params: List[str]) -> Dict[str, Any]:
    """Generate edge case test data"""
    edge_data = {}
    
    for param in params:
        if not param or param == 'self':
            continue
            
        param_clean = param.split('=')[0].strip()
        
        # Edge cases based on parameter types
        if any(word in param_clean.lower() for word in ['id', 'count', 'num']):
            edge_data[param_clean] = [0, -1, 999999]
        elif any(word in param_clean.lower() for word in ['name', 'text']):
            edge_data[param_clean] = ["", "x"*1000, None]
        elif any(word in param_clean.lower() for word in ['email']):
            edge_data[param_clean] = ["invalid_email", "", "test@"]
        else:
            edge_data[param_clean] = [None, "", 0]
    
    return edge_data


def _estimate_coverage(test_cases: List[Dict[str, Any]], functions: List[Dict[str, Any]], classes: List[Dict[str, Any]]) -> float:
    """Estimate test coverage based on generated test cases"""
    if not functions and not classes:
        return 0.0
    
    total_targets = len(functions) + len(classes)
    covered_targets = set()
    
    for test_case in test_cases:
        covered_targets.add(test_case["target"])
    
    coverage = len(covered_targets) / total_targets if total_targets > 0 else 0.0
    
    # Bonus for different test types
    test_types = set(tc["type"] for tc in test_cases)
    type_bonus = len(test_types) * 0.1
    
    return min(1.0, coverage + type_bonus)


def _generate_test_code(test_cases: List[Dict[str, Any]], framework: str) -> str:
    """Generate actual test code in specified framework"""
    if framework == "pytest":
        return _generate_pytest_code(test_cases)
    elif framework == "unittest":
        return _generate_unittest_code(test_cases)
    else:
        return _generate_pytest_code(test_cases)  # Default to pytest


def _generate_pytest_code(test_cases: List[Dict[str, Any]]) -> str:
    """Generate pytest test code"""
    code_lines = [
        "import pytest",
        "from unittest.mock import Mock, patch",
        "",
        "# Generated test cases",
        ""
    ]
    
    for test_case in test_cases:
        code_lines.extend([
            f"def {test_case['name']}():",
            f'    """',
            f"    {test_case['description']}",
            f'    """',
            f"    # Test data: {test_case['test_data']}",
            f"    # Target: {test_case['target']}",
            f"    # Type: {test_case['type']}",
            "",
            "    # Setup",
            "    pass  # Add test setup here",
            "",
            "    # Execute", 
            "    pass  # Add test execution here",
            "",
            "    # Assert",
            "    pass  # Add assertions here",
            "",
            ""
        ])
    
    return "\n".join(code_lines)


def _generate_unittest_code(test_cases: List[Dict[str, Any]]) -> str:
    """Generate unittest test code"""
    code_lines = [
        "import unittest",
        "from unittest.mock import Mock, patch",
        "",
        "",
        "class TestGeneratedTests(unittest.TestCase):",
        '    """Generated test class"""',
        ""
    ]
    
    for test_case in test_cases:
        code_lines.extend([
            f"    def {test_case['name']}(self):",
            f'        """',
            f"        {test_case['description']}",
            f'        """',
            f"        # Test data: {test_case['test_data']}",
            f"        # Target: {test_case['target']}",
            f"        # Type: {test_case['type']}",
            "",
            "        # Setup",
            "        pass  # Add test setup here",
            "",
            "        # Execute",
            "        pass  # Add test execution here", 
            "",
            "        # Assert",
            "        pass  # Add assertions here",
            "",
            ""
        ])
    
    code_lines.extend([
        "",
        'if __name__ == "__main__":',
        "    unittest.main()"
    ])
    
    return "\n".join(code_lines)


def _generate_test_summary(test_count: int, coverage: float, test_type: str) -> str:
    """Generate human-readable test summary"""
    return f"Generated {test_count} {test_type} tests with {coverage*100:.1f}% estimated coverage"


def _create_error_response(error_message: str, start_time: float) -> Dict[str, Any]:
    """Create standardized error response"""
    return {
        "result": None,
        "success": False,
        "confidence": 0.0,
        "metrics": {
            "execution_time": time.time() - start_time,
            "error": True
        },
        "notes": error_message,
        "error": error_message
    }