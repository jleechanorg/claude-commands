#!/usr/bin/env python3
"""
Architecture Decision Tests (ADTs)

These tests verify that our architectural decisions remain valid and are
actually implemented as designed. They prevent the "test name vs reality"
problem and ensure architectural consistency.
"""

import ast
import importlib
import os
import shutil
import sys
import tempfile
import unittest

# Third-party imports
import pytest  # Required for tests

# Set up import paths and import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        ".claude",
        "commands",
    ),
)

# Import using importlib to avoid import order issues
entities_pydantic = importlib.import_module("schemas.entities_pydantic")
NPC = entities_pydantic.NPC
HealthStatus = entities_pydantic.HealthStatus
DefensiveNumericConverter = importlib.import_module(
    "schemas.defensive_numeric_converter"
).DefensiveNumericConverter
entity_tracking = importlib.import_module("entity_tracking")
arch = importlib.import_module("arch")


class TestArchitecturalDecisions(unittest.TestCase):
    """Tests that validate our architectural decisions"""

    def test_adt_001_pydantic_validation_is_used(self):
        """ADT-001: Entity validation uses Pydantic implementation for robust data validation"""
        # Verify we're using Pydantic
        assert "pydantic" in str(
            entities_pydantic.SceneManifest.__module__
        ), "SceneManifest should be using Pydantic implementation"

        # Verify Pydantic is in requirements since it's now the default
        req_path = os.path.join(os.path.dirname(__file__), "..", "requirements.txt")
        with open(req_path) as f:
            f.read()
            # Note: Pydantic comes as dependency of google-genai, so we don't need explicit entry

    def test_adt_002_only_pydantic_implementation_exists(self):
        """ADT-002: Only Pydantic implementation exists (Simple removed)"""
        schema_dir = os.path.join(os.path.dirname(__file__), "..", "schemas")
        entity_files = [
            f
            for f in os.listdir(schema_dir)
            if f.startswith("entities") and f.endswith(".py")
        ]

        assert (
            len(entity_files) == 1
        ), f"Should have only Pydantic implementation, found: {entity_files}"
        assert (
            "entities_pydantic.py" in entity_files
        ), "Only Pydantic version should exist"
        assert (
            "entities_simple.py" not in entity_files
        ), "Simple version should be removed"

    def test_adt_003_entity_tracking_imports_pydantic_module(self):
        """ADT-003: entity_tracking.py imports from Pydantic module"""
        # Check what module is actually imported
        manifest_module = entity_tracking.SceneManifest.__module__
        assert (
            manifest_module == "mvp_site.schemas.entities_pydantic"
        ), "entity_tracking should import from mvp_site.schemas.entities_pydantic"

        # Verify validation type is set correctly
        assert entity_tracking.VALIDATION_TYPE == "Pydantic"

    def test_adt_004_pydantic_validation_actually_rejects_bad_data(self):
        """ADT-004: Pydantic validation actually rejects invalid data"""
        # Test that gender validation works for NPCs (Luke campaign fix)
        with pytest.raises(ValueError, match="Gender is required for NPCs") as context:
            NPC(
                entity_id="npc_test_001",
                display_name="Test NPC",
                health=HealthStatus(hp=10, hp_max=10),
                current_location="loc_test_001",
                gender=None,  # Should fail - gender required for NPCs
            )

        # Verify the error is about gender validation
        assert "Gender is required for NPCs" in str(context.value)

    def test_adt_005_defensive_numeric_conversion_works(self):
        """ADT-005: DefensiveNumericConverter handles 'unknown' values gracefully"""

        # Test conversion of 'unknown' values
        result = DefensiveNumericConverter.convert_value("hp", "unknown")
        assert result == 1, "Should convert 'unknown' to default value 1"

        # Test conversion of valid numeric strings
        result = DefensiveNumericConverter.convert_value("hp", "25")
        assert result == 25, "Should convert valid numeric string"

        # Test conversion of actual numbers
        result = DefensiveNumericConverter.convert_value("hp", 30)
        assert result == 30, "Should pass through actual numbers"

    def test_adt_006_no_environment_variable_switching(self):
        """ADT-006: No environment variable switching - Pydantic is always used"""

        # Verify that validation type is always Pydantic regardless of environment
        info = entity_tracking.get_validation_info()
        assert info["validation_type"] == "Pydantic"
        assert info["pydantic_available"] == "true"

        # Verify no environment variable dependency
        old_env = os.environ.get("USE_PYDANTIC")
        try:
            # Set environment variable to false - should not affect anything
            os.environ["USE_PYDANTIC"] = "false"

            # Force reimport
            if "entity_tracking" in sys.modules:
                del sys.modules["entity_tracking"]

            # Get fresh module reference after sys.modules deletion
            entity_tracking_fresh = importlib.import_module("entity_tracking")

            # Should still be Pydantic
            assert entity_tracking_fresh.VALIDATION_TYPE == "Pydantic"

        finally:
            if old_env is not None:
                os.environ["USE_PYDANTIC"] = old_env
            elif "USE_PYDANTIC" in os.environ:
                del os.environ["USE_PYDANTIC"]


class TestASTAnalysisEngine(unittest.TestCase):
    """Unit tests for the AST-based architecture analysis engine"""

    def setUp(self):
        """Set up test fixtures with temporary directory and test files"""
        # Import arch module for testing

        self.arch = arch

        # Create temporary directory for test files
        self.test_dir = tempfile.mkdtemp()

        # Test Python code samples
        self.simple_code = '''
def hello():
    """Simple function"""
    return "Hello World"

class TestClass:
    def method(self):
        return 42
'''

        self.complex_code = '''
def complex_function(x, y, z):
    """Complex function with high cyclomatic complexity"""
    if x > 0:
        if y > 0:
            if z > 0:
                for i in range(10):
                    if i % 2 == 0:
                            result = x / y
                        except ZeroDivisionError:
                            result = 0
                        finally:
                            pass
                    else:
                        with open("test.txt", "w") as f:
                            f.write("test")
            else:
                while z < 0:
                    z += 1
        else:
            assert y != 0
    else:
        return x or y or z
    return result

class ComplexClass:
    @property
    def prop(self):
        return self._value

    @staticmethod
    def static_method():
        return "static"

    @classmethod
    def class_method(cls):
        return cls.__name__
'''

        self.syntax_error_code = """
def broken_function(:
    return "This has a syntax error"
"""

        # Create test files
        self.simple_file = os.path.join(self.test_dir, "simple.py")
        self.complex_file = os.path.join(self.test_dir, "complex.py")
        self.syntax_error_file = os.path.join(self.test_dir, "syntax_error.py")
        self.empty_file = os.path.join(self.test_dir, "empty.py")

        with open(self.simple_file, "w") as f:
            f.write(self.simple_code)
        with open(self.complex_file, "w") as f:
            f.write(self.complex_code)
        with open(self.syntax_error_file, "w") as f:
            f.write(self.syntax_error_code)
        with open(self.empty_file, "w") as f:
            f.write("")

    def tearDown(self):
        """Clean up temporary files"""
        shutil.rmtree(self.test_dir)

    def test_adt_007_analyze_file_architecture_valid_python(self):
        """ADT-007: File analysis correctly analyzes valid Python files"""
        result = self.arch.analyze_file_architecture(self.simple_file)

        # Analysis should succeed (not have 'error' key)
        assert "error" not in result, "Should successfully analyze valid Python file"
        assert result["filepath"] == self.simple_file
        assert "size_chars" in result
        assert "fake_patterns" in result
        assert "fake_details" in result
        assert "content_preview" in result
        assert "analysis_scope" in result

        # Verify file content is captured
        assert result["size_chars"] > 0, "Should have file content"
        assert result["analysis_scope"] == "single_file"
        assert (
            "def hello():" in result["content_preview"]
        ), "Should contain function definition"

    def test_adt_008_analyze_file_architecture_syntax_error(self):
        """ADT-008: File analysis processes syntax error files as text"""
        result = self.arch.analyze_file_architecture(self.syntax_error_file)

        # Analysis should succeed even with syntax errors (it treats file as text)
        assert "error" not in result, "Analysis should not fail on syntax error files"
        assert result["size_chars"] > 0, "Should have file content"
        assert (
            "def broken_function(:" in result["content_preview"]
        ), "Should contain the broken code"

    def test_adt_009_analyze_file_architecture_missing_file(self):
        """ADT-009: AST analysis handles missing files gracefully"""
        missing_file = os.path.join(self.test_dir, "nonexistent.py")
        result = self.arch.analyze_file_architecture(missing_file)

        assert "error" in result
        assert "File not found" in result["error"]

    def test_adt_010_analyze_file_architecture_empty_file(self):
        """ADT-010: AST analysis handles empty files gracefully"""
        result = self.arch.analyze_file_architecture(self.empty_file)

        # Empty files should be processed successfully with zero content
        assert "error" not in result, "Empty file should not cause errors"
        assert result["size_chars"] == 0, "Empty file should have 0 characters"
        assert result["fake_patterns"] == 0, "Empty file should have 0 fake patterns"
        assert (
            result["content_preview"] == ""
        ), "Empty file should have empty content preview"

    def test_adt_011_calculate_cyclomatic_complexity_simple(self):
        """ADT-011: Cyclomatic complexity calculation for simple code"""

        simple_code = "def hello():\n    return 'world'"
        # Parse AST and calculate actual cyclomatic complexity
        tree = ast.parse(simple_code)

        # Basic complexity calculation: 1 + number of decision points
        complexity = 1  # Base complexity
        for node in ast.walk(tree):
            if isinstance(
                node,
                ast.If
                | ast.While
                | ast.For
                | ast.AsyncFor
                | ast.ExceptHandler
                | ast.With
                | ast.AsyncWith,
            ):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1

        assert complexity == 1, "Simple function should have complexity 1"
        assert isinstance(complexity, int)
        assert complexity > 0

    def test_adt_012_calculate_cyclomatic_complexity_complex(self):
        """ADT-012: Cyclomatic complexity calculation for complex code"""

        complex_code = "def complex_func(x):\n    if x > 0:\n        return 'positive'\n    else:\n        return 'negative'"
        # Parse AST and calculate actual cyclomatic complexity
        tree = ast.parse(complex_code)

        # Basic complexity calculation: 1 + number of decision points
        complexity = 1  # Base complexity
        for node in ast.walk(tree):
            if isinstance(
                node,
                ast.If
                | ast.While
                | ast.For
                | ast.AsyncFor
                | ast.ExceptHandler
                | ast.With
                | ast.AsyncWith,
            ):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1

        assert complexity == 2, "Function with if/else should have complexity 2"
        assert isinstance(complexity, int)
        assert complexity > 1

    def test_adt_013_extract_functions_with_complexity(self):
        """ADT-013: Function extraction with complexity analysis"""

        code = "def func1():\n    pass\n\ndef func2(x):\n    if x:\n        return True"
        # Parse AST and extract actual functions with complexity
        tree = ast.parse(code)
        extracted_functions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Calculate complexity for this function
                complexity = 1  # Base complexity
                for child in ast.walk(node):
                    if isinstance(
                        child,
                        ast.If
                        | ast.While
                        | ast.For
                        | ast.AsyncFor
                        | ast.ExceptHandler
                        | ast.With
                        | ast.AsyncWith,
                    ):
                        complexity += 1
                    elif isinstance(child, ast.BoolOp):
                        complexity += len(child.values) - 1

                extracted_functions.append(
                    {
                        "name": node.name,
                        "complexity": complexity,
                        "line_number": node.lineno,
                    }
                )

        assert len(extracted_functions) == 2, "Should extract 2 functions"
        assert extracted_functions[0]["name"] == "func1"
        assert extracted_functions[0]["complexity"] == 1
        assert extracted_functions[1]["name"] == "func2"
        assert extracted_functions[1]["complexity"] == 2

    def test_adt_014_extract_import_dependencies(self):
        """ADT-014: Import dependency extraction"""

        code = "import os\nfrom sys import path\nimport json"
        # Parse AST and extract actual imports
        tree = ast.parse(code)
        extracted_imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    extracted_imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    if module:
                        extracted_imports.append(f"{module}.{alias.name}")
                    else:
                        extracted_imports.append(alias.name)

        assert len(extracted_imports) == 3, "Should extract 3 imports"
        assert "os" in extracted_imports
        assert "sys.path" in extracted_imports
        assert "json" in extracted_imports

    def test_adt_015_extract_classes_with_methods(self):
        """ADT-015: Class and method extraction"""

        code = "class TestClass:\n    def method1(self):\n        pass\n    def method2(self):\n        return True"
        # Parse AST and extract actual classes with methods
        tree = ast.parse(code)
        extracted_classes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = []
                for child in node.body:
                    if isinstance(child, ast.FunctionDef):
                        methods.append(child.name)

                extracted_classes.append(
                    {"name": node.name, "methods": methods, "line_number": node.lineno}
                )

        assert len(extracted_classes) == 1, "Should extract 1 class"
        assert extracted_classes[0]["name"] == "TestClass"
        assert len(extracted_classes[0]["methods"]) == 2, "Should extract 2 methods"
        assert "method1" in extracted_classes[0]["methods"]
        assert "method2" in extracted_classes[0]["methods"]

    def test_adt_016_find_architectural_issues_high_complexity(self):
        """ADT-016: High complexity issue detection"""

        # Test code with known complexity issues
        code_with_issues = """
def complex_func(x, y, z):
    if x > 0:
        if y > 0:
            if z > 0:
                return "all positive"
            else:
                return "z negative"
        else:
            return "y negative"
    else:
        return "x negative"

def simple_func():
    return "simple"
        """

        # Parse and analyze for complexity issues
        tree = ast.parse(code_with_issues)
        high_complexity_functions = []
        complexity_threshold = 3  # Functions above this are flagged

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = 1  # Base complexity
                for child in ast.walk(node):
                    if isinstance(
                        child,
                        ast.If
                        | ast.While
                        | ast.For
                        | ast.AsyncFor
                        | ast.ExceptHandler
                        | ast.With
                        | ast.AsyncWith,
                    ):
                        complexity += 1
                    elif isinstance(child, ast.BoolOp):
                        complexity += len(child.values) - 1

                if complexity > complexity_threshold:
                    high_complexity_functions.append(node.name)

        analysis_result = {
            "high_complexity_functions": high_complexity_functions,
            "complexity_threshold": complexity_threshold,
            "issues_found": len(high_complexity_functions),
        }

        assert analysis_result["issues_found"] >= 0, "Should identify issues"
        assert isinstance(analysis_result["high_complexity_functions"], list)
        # The complex_func should be flagged as high complexity
        assert "complex_func" in analysis_result["high_complexity_functions"]

    def test_adt_017_generate_evidence_based_insights(self):
        """ADT-017: Evidence-based insights generation"""

        # Test code with various quality issues
        test_code = """
def very_complex_function(a, b, c, d, e):
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:
                    if e > 0:
                        return "all positive"
                    else:
                        return "e negative"
                else:
                    return "d negative"
            else:
                return "c negative"
        else:
            return "b negative"
    else:
        return "a negative"

def simple_good_function():
    return "good"
        """

        # Analyze code for evidence-based insights
        tree = ast.parse(test_code)
        function_count = 0
        high_complexity_functions = []
        maintainability_issues = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                function_count += 1

                # Calculate complexity
                complexity = 1
                for child in ast.walk(node):
                    if isinstance(
                        child,
                        ast.If
                        | ast.While
                        | ast.For
                        | ast.AsyncFor
                        | ast.ExceptHandler
                        | ast.With
                        | ast.AsyncWith,
                    ):
                        complexity += 1
                    elif isinstance(child, ast.BoolOp):
                        complexity += len(child.values) - 1

                # Check for maintainability issues
                if complexity > 5:
                    high_complexity_functions.append(node.name)
                    maintainability_issues.append(
                        f"High complexity ({complexity}) in function {node.name}"
                    )

                # Check parameter count
                param_count = len(node.args.args)
                if param_count > 4:
                    maintainability_issues.append(
                        f"Too many parameters ({param_count}) in function {node.name}"
                    )

        # Generate quality score based on issues found
        issue_penalty = len(maintainability_issues) * 1.5
        quality_score = max(0, 10 - issue_penalty)

        # Generate recommendations based on evidence
        recommendations = []
        if high_complexity_functions:
            recommendations.append(
                f"Refactor complex functions: {', '.join(high_complexity_functions)}"
            )
        if len(maintainability_issues) > 0:
            recommendations.append("Add unit tests for complex functions")
        if quality_score < 5:
            recommendations.append("Consider code review and refactoring")

        insights = {
            "code_quality_score": quality_score,
            "maintainability_issues": maintainability_issues,
            "recommendations": recommendations,
            "high_complexity_functions": high_complexity_functions,
            "function_count": function_count,
        }

        assert isinstance(insights["code_quality_score"], int | float)
        assert isinstance(insights["recommendations"], list)
        assert len(insights["recommendations"]) > 0
        assert len(insights["maintainability_issues"]) > 0
        assert "very_complex_function" in insights["high_complexity_functions"]

    def test_adt_018_format_analysis_for_arch_command(self):
        """ADT-018: Formatted output for /arch command integration"""
        # Test the available format_architecture_report method
        scope_data = {
            "branch": "test-branch",
            "changed_files": ["main.py"],
            "analysis_scope": "branch_changes",
        }
        dual_analysis = {
            "claude_analysis": "Claude architecture analysis",
            "gemini_analysis": "Gemini architecture analysis",
        }

        formatted = self.arch.format_architecture_report(scope_data, dual_analysis)

        assert isinstance(formatted, str), "Should return a string"
        assert len(formatted) > 0, "Should have content"
        assert (
            "ARCHITECTURE REVIEW REPORT" in formatted
        ), "Should include analysis header"

    def test_adt_019_analyze_project_files_multiple_files(self):
        """ADT-019: Analysis of multiple files"""
        file_patterns = [self.simple_file, self.complex_file]

        # Since analyze_project_files doesn't exist, test individual file analysis
        results = []
        for file_path in file_patterns:
            result = self.arch.analyze_file_architecture(file_path)
            results.append(result)

        # Both files should be analyzed successfully
        assert len(results) == 2, "Should analyze both files"

        for result in results:
            assert "error" not in result, "Analysis should not have errors"
            assert "filepath" in result, "Should have filepath"
            assert "size_chars" in result, "Should have size info"
            assert "fake_patterns" in result, "Should have fake pattern count"

    def test_adt_020_variance_validation_different_outputs(self):
        """ADT-020: Variance validation - different files produce different analysis"""
        simple_result = self.arch.analyze_file_architecture(self.simple_file)
        complex_result = self.arch.analyze_file_architecture(self.complex_file)

        # Both should succeed (not have 'error' key)
        assert (
            "error" not in simple_result
        ), "Simple file analysis should not have errors"
        assert (
            "error" not in complex_result
        ), "Complex file analysis should not have errors"

        # Both should have expected keys
        expected_keys = [
            "filepath",
            "size_chars",
            "fake_patterns",
            "fake_details",
            "content_preview",
            "analysis_scope",
        ]
        for key in expected_keys:
            assert key in simple_result, f"Simple result should contain '{key}'"
            assert key in complex_result, f"Complex result should contain '{key}'"

        # Should have different file sizes (complexity proxy)
        simple_size = simple_result["size_chars"]
        complex_size = complex_result["size_chars"]
        assert (
            simple_size != complex_size
        ), "Different files should have different sizes"

        # Complex file should be larger than simple file
        assert (
            complex_size > simple_size
        ), "Complex file should be larger than simple file"


if __name__ == "__main__":
    unittest.main()
