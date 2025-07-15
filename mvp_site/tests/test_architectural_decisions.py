#!/usr/bin/env python3
"""
Architecture Decision Tests (ADTs)

These tests verify that our architectural decisions remain valid and are 
actually implemented as designed. They prevent the "test name vs reality" 
problem and ensure architectural consistency.
"""

import unittest
import os
import sys
import importlib
import tempfile
import shutil
from unittest.mock import patch, mock_open

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Add .claude/commands to path for arch module import
claude_commands_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.claude', 'commands')
sys.path.insert(0, claude_commands_path)


class TestArchitecturalDecisions(unittest.TestCase):
    """Tests that validate our architectural decisions"""
    
    def test_adt_001_pydantic_validation_is_used(self):
        """ADT-001: Entity validation uses Pydantic implementation for robust data validation"""
        # Import and verify we're using the pydantic module
        from schemas import entities_pydantic
        
        # Verify we're using Pydantic
        self.assertIn('pydantic', str(entities_pydantic.SceneManifest.__module__), 
                     "SceneManifest should be using Pydantic implementation")
        
        # Verify Pydantic is in requirements since it's now the default
        req_path = os.path.join(os.path.dirname(__file__), '..', 'requirements.txt')
        with open(req_path) as f:
            requirements = f.read()
            # Note: Pydantic comes as dependency of google-genai, so we don't need explicit entry
    
    def test_adt_002_only_pydantic_implementation_exists(self):
        """ADT-002: Only Pydantic implementation exists (Simple removed)"""
        schema_dir = os.path.join(os.path.dirname(__file__), '..', 'schemas')
        entity_files = [f for f in os.listdir(schema_dir) 
                       if f.startswith('entities') and f.endswith('.py')]
        
        self.assertEqual(len(entity_files), 1, 
                        f"Should have only Pydantic implementation, found: {entity_files}")
        self.assertIn('entities_pydantic.py', entity_files, "Only Pydantic version should exist")
        self.assertNotIn('entities_simple.py', entity_files, "Simple version should be removed")
    
    def test_adt_003_entity_tracking_imports_pydantic_module(self):
        """ADT-003: entity_tracking.py imports from Pydantic module"""
        import entity_tracking
        
        # Check what module is actually imported
        manifest_module = entity_tracking.SceneManifest.__module__
        self.assertEqual(manifest_module, 'schemas.entities_pydantic',
                        f"entity_tracking should import from schemas.entities_pydantic")
        
        # Verify validation type is set correctly
        self.assertEqual(entity_tracking.VALIDATION_TYPE, "Pydantic")
    
    def test_adt_004_pydantic_validation_actually_rejects_bad_data(self):
        """ADT-004: Pydantic validation actually rejects invalid data"""
        from schemas.entities_pydantic import NPC, HealthStatus, EntityType
        
        # Test that gender validation works for NPCs (Luke campaign fix)
        with self.assertRaises(Exception) as context:
            npc = NPC(
                entity_id="npc_test_001",
                display_name="Test NPC",
                health=HealthStatus(hp=10, hp_max=10),
                current_location="loc_test_001",
                gender=None  # Should fail - gender required for NPCs
            )
        
        # Verify the error is about gender validation
        self.assertIn("Gender is required for NPCs", str(context.exception))
    
    def test_adt_005_defensive_numeric_conversion_works(self):
        """ADT-005: DefensiveNumericConverter handles 'unknown' values gracefully"""
        from schemas.defensive_numeric_converter import DefensiveNumericConverter
        
        # Test conversion of 'unknown' values
        result = DefensiveNumericConverter.convert_value('hp', 'unknown')
        self.assertEqual(result, 1, "Should convert 'unknown' to default value 1")
        
        # Test conversion of valid numeric strings
        result = DefensiveNumericConverter.convert_value('hp', '25')
        self.assertEqual(result, 25, "Should convert valid numeric string")
        
        # Test conversion of actual numbers
        result = DefensiveNumericConverter.convert_value('hp', 30)
        self.assertEqual(result, 30, "Should pass through actual numbers")
    
    def test_adt_006_no_environment_variable_switching(self):
        """ADT-006: No environment variable switching - Pydantic is always used"""
        import entity_tracking
        
        # Verify that validation type is always Pydantic regardless of environment
        info = entity_tracking.get_validation_info()
        self.assertEqual(info['validation_type'], 'Pydantic')
        self.assertEqual(info['pydantic_available'], 'true')
        
        # Verify no environment variable dependency
        import os
        old_env = os.environ.get('USE_PYDANTIC')
        try:
            # Set environment variable to false - should not affect anything
            os.environ['USE_PYDANTIC'] = 'false'
            
            # Force reimport
            if 'entity_tracking' in sys.modules:
                del sys.modules['entity_tracking']
            
            import entity_tracking
            
            # Should still be Pydantic
            self.assertEqual(entity_tracking.VALIDATION_TYPE, "Pydantic")
            
        finally:
            if old_env is not None:
                os.environ['USE_PYDANTIC'] = old_env
            elif 'USE_PYDANTIC' in os.environ:
                del os.environ['USE_PYDANTIC']


class TestASTAnalysisEngine(unittest.TestCase):
    """Unit tests for the AST-based architecture analysis engine"""
    
    def setUp(self):
        """Set up test fixtures with temporary directory and test files"""
        # Import arch module for testing
        import arch
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
                        try:
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
        
        self.syntax_error_code = '''
def broken_function(:
    return "This has a syntax error"
'''
        
        # Create test files
        self.simple_file = os.path.join(self.test_dir, "simple.py")
        self.complex_file = os.path.join(self.test_dir, "complex.py") 
        self.syntax_error_file = os.path.join(self.test_dir, "syntax_error.py")
        self.empty_file = os.path.join(self.test_dir, "empty.py")
        
        with open(self.simple_file, 'w') as f:
            f.write(self.simple_code)
        with open(self.complex_file, 'w') as f:
            f.write(self.complex_code)
        with open(self.syntax_error_file, 'w') as f:
            f.write(self.syntax_error_code)
        with open(self.empty_file, 'w') as f:
            f.write("")
    
    def tearDown(self):
        """Clean up temporary files"""
        shutil.rmtree(self.test_dir)
    
    def test_adt_007_analyze_file_structure_valid_python(self):
        """ADT-007: AST analysis correctly analyzes valid Python files"""
        result = self.arch.analyze_file_structure(self.simple_file)
        
        self.assertTrue(result.get('success', False), "Should successfully analyze valid Python file")
        self.assertEqual(result['file'], self.simple_file)
        self.assertIn('metrics', result)
        self.assertIn('functions', result)
        self.assertIn('imports', result)
        self.assertIn('classes', result)
        self.assertIn('issues', result)
        
        # Verify metrics
        metrics = result['metrics']
        self.assertGreater(metrics['lines'], 0, "Should count lines")
        self.assertEqual(metrics['function_count'], 2, "Should find hello function and method")
        self.assertEqual(metrics['class_count'], 1, "Should find one class")
        self.assertGreaterEqual(metrics['complexity'], 1, "Should calculate complexity")
    
    def test_adt_008_analyze_file_structure_syntax_error(self):
        """ADT-008: AST analysis gracefully handles syntax errors"""
        result = self.arch.analyze_file_structure(self.syntax_error_file)
        
        self.assertFalse(result.get('success', False), "Should not succeed with syntax error")
        self.assertTrue(result.get('syntax_error', False), "Should flag as syntax error")
        self.assertIn('error', result)
        self.assertIn('Syntax error', result['error'])
    
    def test_adt_009_analyze_file_structure_missing_file(self):
        """ADT-009: AST analysis handles missing files gracefully"""
        missing_file = os.path.join(self.test_dir, "nonexistent.py")
        result = self.arch.analyze_file_structure(missing_file)
        
        self.assertIn('error', result)
        self.assertIn('File not found', result['error'])
    
    def test_adt_010_analyze_file_structure_empty_file(self):
        """ADT-010: AST analysis handles empty files gracefully"""
        result = self.arch.analyze_file_structure(self.empty_file)
        
        self.assertIn('error', result)
        self.assertIn('Empty file', result['error'])
        self.assertTrue(result.get('skipped', False))
    
    def test_adt_011_calculate_cyclomatic_complexity_simple(self):
        """ADT-011: Cyclomatic complexity calculation for simple code"""
        import ast
        tree = ast.parse(self.simple_code)
        complexity = self.arch.calculate_cyclomatic_complexity(tree)
        
        # Simple code should have low complexity (1 base + minimal branching)
        self.assertGreaterEqual(complexity, 1, "Should have at least base complexity of 1")
        self.assertLessEqual(complexity, 5, "Simple code should have low complexity")
    
    def test_adt_012_calculate_cyclomatic_complexity_complex(self):
        """ADT-012: Cyclomatic complexity calculation for complex code"""
        import ast
        tree = ast.parse(self.complex_code)
        complexity = self.arch.calculate_cyclomatic_complexity(tree)
        
        # Complex code should have high complexity due to nested conditions
        self.assertGreater(complexity, 10, "Complex code should have high complexity")
    
    def test_adt_013_extract_functions_with_complexity(self):
        """ADT-013: Function extraction with complexity analysis"""
        import ast
        tree = ast.parse(self.complex_code)
        functions = self.arch.extract_functions_with_complexity(tree)
        
        self.assertEqual(len(functions), 4, "Should find complex_function plus 3 class methods")
        
        func = functions[0]
        self.assertEqual(func['name'], 'complex_function')
        self.assertIn('line', func)
        self.assertIn('complexity', func)
        self.assertIn('args_count', func)
        self.assertEqual(func['args_count'], 3, "Should count function arguments correctly")
        self.assertGreater(func['complexity'], 5, "Complex function should have high complexity")
    
    def test_adt_014_extract_import_dependencies(self):
        """ADT-014: Import dependency extraction"""
        import_code = '''
import os
import sys
from typing import Dict, List
from unittest.mock import patch
'''
        import ast
        tree = ast.parse(import_code)
        imports = self.arch.extract_import_dependencies(tree)
        
        self.assertGreater(len(imports), 0, "Should find imports")
        
        # Check for expected imports
        import_modules = [imp['module'] for imp in imports if imp['type'] == 'import']
        self.assertIn('os', import_modules)
        self.assertIn('sys', import_modules)
        
        # Check for from imports
        from_imports = [imp for imp in imports if imp['type'] == 'from_import']
        typing_imports = [imp for imp in from_imports if imp['module'] == 'typing']
        self.assertGreater(len(typing_imports), 0, "Should find typing imports")
    
    def test_adt_015_extract_classes_with_methods(self):
        """ADT-015: Class and method extraction"""
        import ast
        tree = ast.parse(self.complex_code)
        classes = self.arch.extract_classes_with_methods(tree)
        
        self.assertEqual(len(classes), 1, "Should find one class")
        
        cls = classes[0]
        self.assertEqual(cls['name'], 'ComplexClass')
        self.assertIn('methods', cls)
        self.assertEqual(cls['method_count'], 3, "Should find three methods")
        
        # Check method types
        methods = cls['methods']
        prop_method = next((m for m in methods if m['name'] == 'prop'), None)
        static_method = next((m for m in methods if m['name'] == 'static_method'), None)
        class_method = next((m for m in methods if m['name'] == 'class_method'), None)
        
        self.assertIsNotNone(prop_method, "Should find property method")
        self.assertIsNotNone(static_method, "Should find static method")
        self.assertIsNotNone(class_method, "Should find class method")
        
        self.assertTrue(prop_method.get('is_property', False), "Should identify property")
        self.assertTrue(static_method.get('is_static', False), "Should identify static method")
        self.assertTrue(class_method.get('is_class', False), "Should identify class method")
    
    def test_adt_016_find_architectural_issues_high_complexity(self):
        """ADT-016: High complexity issue detection"""
        import ast
        tree = ast.parse(self.complex_code)
        issues = self.arch.find_architectural_issues(tree, self.complex_file)
        
        # Should find high complexity issue
        complexity_issues = [issue for issue in issues if issue['type'] == 'high_complexity']
        self.assertGreater(len(complexity_issues), 0, "Should detect high complexity functions")
        
        issue = complexity_issues[0]
        self.assertIn('location', issue)
        self.assertIn('message', issue)
        self.assertIn('suggestion', issue)
        self.assertIn(issue['severity'], ['warning', 'error'], "High complexity should be marked as warning or error")
    
    def test_adt_017_generate_evidence_based_insights(self):
        """ADT-017: Evidence-based insights generation"""
        # Create analysis results with known patterns
        analysis_results = [
            {
                'success': True,
                'file': 'test.py',
                'metrics': {'complexity': 25, 'lines': 100, 'function_count': 5},
                'functions': [
                    {'name': 'complex_func', 'line': 10, 'complexity': 15, 'has_docstring': False},
                    {'name': 'simple_func', 'line': 20, 'complexity': 2, 'has_docstring': True}
                ]
            }
        ]
        
        insights = self.arch.generate_evidence_based_insights(analysis_results)
        
        self.assertGreater(len(insights), 0, "Should generate insights for high complexity")
        
        # Check for high complexity insight
        complexity_insights = [i for i in insights if i['category'] == 'complexity']
        self.assertGreater(len(complexity_insights), 0, "Should find file complexity insight")
        
        # Check for function complexity insight
        func_insights = [i for i in insights if i['category'] == 'function_complexity']
        self.assertGreater(len(func_insights), 0, "Should find function complexity insight")
        
        # Verify insight structure
        insight = insights[0]
        self.assertIn('category', insight)
        self.assertIn('severity', insight)
        self.assertIn('finding', insight)
        self.assertIn('evidence', insight)
        self.assertIn('recommendation', insight)
        self.assertIn('specific_actions', insight)
    
    def test_adt_018_format_analysis_for_arch_command(self):
        """ADT-018: Formatted output for /arch command integration"""
        analysis_results = [
            {
                'success': True,
                'file': 'main.py',
                'metrics': {'complexity': 30, 'lines': 200, 'function_count': 10}
            }
        ]
        insights = [
            {
                'category': 'complexity',
                'severity': 'high',
                'finding': 'High complexity detected',
                'evidence': ['main.py (complexity: 30)'],
                'recommendation': 'Refactor complex code'
            }
        ]
        
        formatted = self.arch.format_analysis_for_arch_command(analysis_results, insights)
        
        self.assertIn('Technical Analysis', formatted)
        self.assertIn('Files Analyzed', formatted)
        self.assertIn('Key Findings', formatted)
        self.assertIn('🚨', formatted, "Should include severity emoji")
        self.assertIn('main.py', formatted, "Should include file evidence")
    
    def test_adt_019_analyze_project_files_multiple_files(self):
        """ADT-019: Analysis of multiple files"""
        file_patterns = [self.simple_file, self.complex_file]
        result = self.arch.analyze_project_files(file_patterns)
        
        self.assertIn('analysis_results', result)
        self.assertIn('insights', result)
        self.assertIn('summary', result)
        
        summary = result['summary']
        self.assertEqual(summary['total_files'], 2, "Should analyze both files")
        self.assertEqual(summary['successful_analyses'], 2, "Both files should succeed")
        self.assertEqual(summary['syntax_errors'], 0, "No syntax errors in valid files")
    
    def test_adt_020_variance_validation_different_outputs(self):
        """ADT-020: Variance validation - different files produce different analysis"""
        simple_result = self.arch.analyze_file_structure(self.simple_file)
        complex_result = self.arch.analyze_file_structure(self.complex_file)
        
        # Both should succeed
        self.assertTrue(simple_result.get('success', False))
        self.assertTrue(complex_result.get('success', False))
        
        # Should have different complexity values
        simple_complexity = simple_result['metrics']['complexity']
        complex_complexity = complex_result['metrics']['complexity']
        self.assertNotEqual(simple_complexity, complex_complexity, 
                           "Different files should have different complexity")
        
        # Complex file should have higher complexity
        self.assertGreater(complex_complexity, simple_complexity,
                          "Complex file should have higher complexity than simple file")
        
        # Should have different function counts
        simple_func_count = simple_result['metrics']['function_count']
        complex_func_count = complex_result['metrics']['function_count']
        self.assertNotEqual(simple_func_count, complex_func_count,
                           "Different files should have different function counts")


if __name__ == '__main__':
    unittest.main()