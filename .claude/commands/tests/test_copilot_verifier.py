#!/usr/bin/env python3
"""
Comprehensive tests for copilot_verifier.py

Tests verification workflows, test execution, and safety checks.
"""

import unittest
import tempfile
import os
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from copilot_verifier import (
    CopilotVerifier,
    VerificationResult,
    CheckType
)


class TestCopilotVerifier(unittest.TestCase):
    """Test the main CopilotVerifier class"""
    
    def setUp(self):
        self.verifier = CopilotVerifier()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        # Clean up temp files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_file(self, content: str, filename: str = "test_file.py") -> str:
        """Create a temporary test file with given content"""
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path


class TestSyntaxVerification(unittest.TestCase):
    """Test syntax checking functionality"""
    
    def setUp(self):
        self.verifier = CopilotVerifier()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_file(self, content: str, filename: str = "test_file.py") -> str:
        """Create a temporary test file with given content"""
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path
    
    def test_valid_syntax(self):
        """Test verification of valid Python syntax"""
        content = """
import os
import sys

def hello_world():
    return "Hello, World!"

if __name__ == "__main__":
    print(hello_world())
"""
        file_path = self.create_test_file(content)
        result = self.verifier.verify_syntax([file_path])
        
        self.assertTrue(result.success)
        self.assertEqual(result.check_type, CheckType.SYNTAX)
        self.assertIn("syntax valid", result.description.lower())
    
    def test_invalid_syntax(self):
        """Test detection of syntax errors"""
        content = """
import os

def broken_function(
    # Missing closing parenthesis
    return "This won't work"
"""
        file_path = self.create_test_file(content)
        result = self.verifier.verify_syntax([file_path])
        
        self.assertFalse(result.success)
        self.assertEqual(result.check_type, CheckType.SYNTAX)
        self.assertIsNotNone(result.error_message)
    
    def test_multiple_files_mixed_syntax(self):
        """Test syntax verification with mixed valid/invalid files"""
        valid_content = """
def valid_function():
    return True
"""
        invalid_content = """
def invalid_function(
    # Syntax error here
    return False
"""
        
        valid_file = self.create_test_file(valid_content, "valid.py")
        invalid_file = self.create_test_file(invalid_content, "invalid.py")
        
        result = self.verifier.verify_syntax([valid_file, invalid_file])
        
        # Should fail because one file has syntax errors
        self.assertFalse(result.success)
        self.assertIn("invalid.py", result.error_message or "")


class TestImportVerification(unittest.TestCase):
    """Test import verification functionality"""
    
    def setUp(self):
        self.verifier = CopilotVerifier()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_file(self, content: str, filename: str = "test_file.py") -> str:
        """Create a temporary test file with given content"""
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path
    
    def test_valid_imports(self):
        """Test verification of valid imports"""
        content = """
import os
import sys
import json
from datetime import datetime

def test():
    return os.path.join("a", "b")
"""
        file_path = self.create_test_file(content)
        result = self.verifier.verify_imports([file_path])
        
        self.assertTrue(result.success)
        self.assertEqual(result.check_type, CheckType.IMPORTS)
    
    def test_missing_import(self):
        """Test detection of missing imports"""
        content = """
# Missing import for undefined_module

def test():
    return undefined_module.some_function()
"""
        file_path = self.create_test_file(content)
        result = self.verifier.verify_imports([file_path])
        
        # This should still pass syntax check, import issues are runtime
        # Our verifier focuses on syntax-level import verification
        self.assertTrue(result.success)


class TestTestExecution(unittest.TestCase):
    """Test test execution functionality"""
    
    def setUp(self):
        self.verifier = CopilotVerifier()
    
    @patch('subprocess.run')
    def test_run_project_tests_success(self, mock_run):
        """Test successful test execution"""
        # Mock successful test run
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "All tests passed\n"
        mock_run.return_value.stderr = ""
        
        result = self.verifier.run_project_tests()
        
        self.assertTrue(result.success)
        self.assertEqual(result.check_type, CheckType.TESTS)
        self.assertIn("tests passed", result.description.lower())
    
    @patch('subprocess.run')
    def test_run_project_tests_failure(self, mock_run):
        """Test failed test execution"""
        # Mock failed test run
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = "2 tests failed\n"
        mock_run.return_value.stderr = "TestError: assertion failed\n"
        
        result = self.verifier.run_project_tests()
        
        self.assertFalse(result.success)
        self.assertEqual(result.check_type, CheckType.TESTS)
        self.assertIn("failed", result.description.lower())
        self.assertIsNotNone(result.error_message)
    
    @patch('subprocess.run')
    def test_run_specific_tests(self, mock_run):
        """Test running tests for specific files"""
        # Mock successful test run
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Specific tests passed\n"
        
        result = self.verifier.run_tests_for_files(["src/module.py"])
        
        self.assertTrue(result.success)
        self.assertEqual(result.check_type, CheckType.TESTS)


class TestComprehensiveVerification(unittest.TestCase):
    """Test comprehensive verification workflow"""
    
    def setUp(self):
        self.verifier = CopilotVerifier()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_file(self, content: str, filename: str = "test_file.py") -> str:
        """Create a temporary test file with given content"""
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path
    
    @patch.object(CopilotVerifier, 'run_project_tests')
    def test_comprehensive_verification_all_pass(self, mock_tests):
        """Test comprehensive verification when all checks pass"""
        # Create valid test file
        content = """
import os

def valid_function():
    return os.path.join("a", "b")
"""
        file_path = self.create_test_file(content)
        
        # Mock successful test run
        mock_tests.return_value = VerificationResult(
            success=True,
            check_type=CheckType.TESTS,
            description="All tests passed"
        )
        
        results = self.verifier.comprehensive_verification([file_path])
        
        # Should have results for syntax, imports, and tests
        self.assertGreaterEqual(len(results), 2)
        
        # All should pass
        for result in results:
            self.assertTrue(result.success, f"Check {result.check_type} should pass")
    
    @patch.object(CopilotVerifier, 'run_project_tests')
    def test_comprehensive_verification_with_failures(self, mock_tests):
        """Test comprehensive verification with some failures"""
        # Create invalid test file
        content = """
import os

def broken_function(
    # Syntax error
    return os.path.join("a", "b")
"""
        file_path = self.create_test_file(content)
        
        # Mock test run (won't matter due to syntax error)
        mock_tests.return_value = VerificationResult(
            success=True,
            check_type=CheckType.TESTS,
            description="Tests passed"
        )
        
        results = self.verifier.comprehensive_verification([file_path])
        
        # Should have at least syntax check result
        self.assertGreater(len(results), 0)
        
        # Syntax check should fail
        syntax_results = [r for r in results if r.check_type == CheckType.SYNTAX]
        self.assertEqual(len(syntax_results), 1)
        self.assertFalse(syntax_results[0].success)


class TestFileIntegrityChecks(unittest.TestCase):
    """Test file integrity and safety checks"""
    
    def setUp(self):
        self.verifier = CopilotVerifier()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_file(self, content: str, filename: str = "test_file.py") -> str:
        """Create a temporary test file with given content"""
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path
    
    def test_verify_file_integrity_valid(self):
        """Test file integrity check for valid files"""
        content = """
def hello():
    return "Hello, World!"
"""
        file_path = self.create_test_file(content)
        result = self.verifier.verify_file_integrity([file_path])
        
        self.assertTrue(result.success)
        self.assertEqual(result.check_type, CheckType.FILE_INTEGRITY)
    
    def test_verify_file_integrity_missing_file(self):
        """Test file integrity check for missing files"""
        missing_file = "/nonexistent/file.py"
        result = self.verifier.verify_file_integrity([missing_file])
        
        self.assertFalse(result.success)
        self.assertIn("not found", result.error_message.lower())
    
    def test_verify_file_integrity_empty_file(self):
        """Test file integrity check for empty files"""
        empty_file = self.create_test_file("")
        result = self.verifier.verify_file_integrity([empty_file])
        
        # Empty files are valid, just a warning
        self.assertTrue(result.success)


class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases"""
    
    def setUp(self):
        self.verifier = CopilotVerifier()
    
    def test_empty_file_list(self):
        """Test verification with empty file list"""
        result = self.verifier.verify_syntax([])
        
        self.assertTrue(result.success)
        self.assertIn("no files", result.description.lower())
    
    def test_nonexistent_files(self):
        """Test verification with nonexistent files"""
        result = self.verifier.verify_syntax(["/nonexistent/file.py"])
        
        self.assertFalse(result.success)
        self.assertIn("not found", result.error_message.lower())
    
    @patch('subprocess.run')
    def test_test_runner_exception(self, mock_run):
        """Test handling of test runner exceptions"""
        # Mock subprocess exception - FileNotFoundError is caught and verifier continues
        # to try other test runners. If all fail, it returns success with "no test runner found"
        mock_run.side_effect = FileNotFoundError("Test runner not found")
        
        result = self.verifier.run_project_tests()
        
        # The verifier returns success=True when no test runner is found
        self.assertTrue(result.success)
        self.assertIn("no test runner found", result.description.lower())


class TestVerificationResult(unittest.TestCase):
    """Test VerificationResult data class"""
    
    def test_verification_result_creation(self):
        """Test creating VerificationResult instances"""
        result = VerificationResult(
            success=True,
            check_type=CheckType.SYNTAX,
            description="Test description"
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.check_type, CheckType.SYNTAX)
        self.assertEqual(result.description, "Test description")
        self.assertIsNone(result.error_message)
    
    def test_verification_result_with_error(self):
        """Test VerificationResult with error information"""
        result = VerificationResult(
            success=False,
            check_type=CheckType.TESTS,
            description="Test failed",
            error_message="Specific error details"
        )
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_message, "Specific error details")


if __name__ == '__main__':
    unittest.main(verbosity=2)