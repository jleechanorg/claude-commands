#!/usr/bin/env python3
"""
Comprehensive tests for copilot_safety.py

Tests safety checks, risk assessment, and validation.
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from copilot_safety import (
    SafetyChecker,
    SafetyResult
)


class TestSafetyChecker(unittest.TestCase):
    """Test the main SafetyChecker class"""
    
    def setUp(self):
        self.checker = SafetyChecker()
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


class TestFileSafetyChecks(unittest.TestCase):
    """Test file safety checking functionality"""
    
    def setUp(self):
        self.checker = SafetyChecker()
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
    
    def test_safe_file(self):
        """Test safety check for safe Python file"""
        content = """
import os
import sys

def hello_world():
    return "Hello, World!"
"""
        file_path = self.create_test_file(content)
        result = self.checker.check_file_safety(file_path)
        
        self.assertTrue(result.safe)
        self.assertEqual(result.risk_level, "low")
    
    def test_protected_file(self):
        """Test safety check for protected files"""
        content = "print('Hello')"
        file_path = self.create_test_file(content, "main.py")
        result = self.checker.check_file_safety(file_path)
        
        self.assertFalse(result.safe)  # Protected files are blocked
        self.assertEqual(result.risk_level, "high")
        self.assertIn("Protected file", result.issues[0])
        self.assertIn("auto_modification", result.blocked_operations)
    
    def test_non_python_file(self):
        """Test safety check for non-Python files"""
        content = "console.log('Hello');"
        file_path = self.create_test_file(content, "test.js")
        result = self.checker.check_file_safety(file_path)
        
        self.assertFalse(result.safe)  # Non-Python files are medium risk
        self.assertEqual(result.risk_level, "medium")
        self.assertIn("Non-Python file", result.issues[0])
    
    def test_file_not_found(self):
        """Test safety check for non-existent files"""
        result = self.checker.check_file_safety("/nonexistent/file.py")
        
        self.assertFalse(result.safe)
        self.assertEqual(result.risk_level, "medium")
        self.assertIn("File does not exist", result.issues[0])
        self.assertIn("all", result.blocked_operations)
    
    def test_dangerous_patterns(self):
        """Test detection of dangerous patterns in files"""
        content = """
import os
import subprocess

def dangerous_function():
    subprocess.call(['rm', '-rf', '/tmp/test'])
    os.system('echo "dangerous"')
    return "done"
"""
        file_path = self.create_test_file(content)
        result = self.checker.check_file_safety(file_path)
        
        self.assertEqual(result.risk_level, "high")
        # Should detect dangerous patterns
        dangerous_issues = [issue for issue in result.issues if "Dangerous pattern" in issue]
        self.assertGreater(len(dangerous_issues), 0)
    
    def test_risky_imports(self):
        """Test detection of risky imports"""
        content = """
import subprocess
import pickle
import tempfile

def test_function():
    return "test"
"""
        file_path = self.create_test_file(content)
        result = self.checker.check_file_safety(file_path)
        
        # Should detect risky imports
        risky_issues = [issue for issue in result.issues if "Risky import" in issue]
        self.assertGreater(len(risky_issues), 0)
        self.assertIn(result.risk_level, ["medium", "high"])


class TestChangeSafetyChecks(unittest.TestCase):
    """Test change safety checking functionality"""
    
    def setUp(self):
        self.checker = SafetyChecker()
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
    
    def test_safe_change(self):
        """Test safety check for safe changes"""
        old_content = """
import os
import sys

def hello():
    return "Hello"
"""
        new_content = """
import os

def hello():
    return "Hello, World!"
"""
        file_path = self.create_test_file(old_content)
        result = self.checker.check_change_safety(file_path, old_content, new_content)
        
        self.assertTrue(result.safe)
        self.assertEqual(result.risk_level, "low")
    
    def test_large_change(self):
        """Test safety check for large changes"""
        old_content = "def test(): pass"
        new_content = "\n".join([f"def function_{i}(): pass" for i in range(60)])
        
        file_path = self.create_test_file(old_content)
        result = self.checker.check_change_safety(file_path, old_content, new_content)
        
        self.assertEqual(result.risk_level, "medium")
        self.assertIn("Large change", result.issues[0])
    
    def test_adding_dangerous_patterns(self):
        """Test detection when dangerous patterns are added"""
        old_content = """
import os

def safe_function():
    return "safe"
"""
        new_content = """
import os
import subprocess

def dangerous_function():
    subprocess.call(['rm', '-rf', '/'])
    return "dangerous"
"""
        file_path = self.create_test_file(old_content)
        result = self.checker.check_change_safety(file_path, old_content, new_content)
        
        self.assertFalse(result.safe)
        self.assertEqual(result.risk_level, "critical")
        self.assertIn("add_dangerous_patterns", result.blocked_operations)
    
    def test_adding_risky_imports(self):
        """Test detection when risky imports are added"""
        old_content = """
import os

def test():
    return "test"
"""
        new_content = """
import os
import subprocess
import pickle

def test():
    return "test"
"""
        file_path = self.create_test_file(old_content)
        result = self.checker.check_change_safety(file_path, old_content, new_content)
        
        self.assertIn(result.risk_level, ["medium", "high", "critical"])
        risky_issues = [issue for issue in result.issues if "Added risky import" in issue]
        self.assertGreater(len(risky_issues), 0)
    
    def test_syntax_error_in_new_content(self):
        """Test detection of syntax errors in new content"""
        old_content = """
def test():
    return "test"
"""
        new_content = """
def test(
    # Syntax error - missing closing parenthesis
    return "test"
"""
        file_path = self.create_test_file(old_content)
        result = self.checker.check_change_safety(file_path, old_content, new_content)
        
        self.assertFalse(result.safe)
        self.assertEqual(result.risk_level, "high")
        self.assertIn("syntax_error", result.blocked_operations)


class TestOperationSafetyChecks(unittest.TestCase):
    """Test operation-specific safety checks"""
    
    def setUp(self):
        self.checker = SafetyChecker()
    
    def test_safe_operations(self):
        """Test safety checks for generally safe operations"""
        safe_operations = [
            ("remove_unused_imports", "regular_file.py"),
            ("create_constants", "utils.py"),
            ("format_code", "helper.py")
        ]
        
        for op_type, target in safe_operations:
            with self.subTest(operation=op_type, target=target):
                result = self.checker.check_operation_safety(op_type, target)
                self.assertIn(result.risk_level, ["low", "medium"])
    
    def test_protected_file_operations(self):
        """Test operations on protected files"""
        protected_operations = [
            ("remove_unused_imports", "main.py"),
            ("format_code", "config.py"),
            ("refactor", "app.py")
        ]
        
        for op_type, target in protected_operations:
            with self.subTest(operation=op_type, target=target):
                result = self.checker.check_operation_safety(op_type, target)
                self.assertIn(result.risk_level, ["medium", "high"])
    
    def test_risky_operations(self):
        """Test inherently risky operations"""
        result = self.checker.check_operation_safety("refactor", "some_file.py")
        self.assertEqual(result.risk_level, "medium")
        self.assertIn("refactoring", result.recommendations[0].lower())
    
    def test_unknown_operations(self):
        """Test unknown operation types"""
        result = self.checker.check_operation_safety("unknown_operation", "file.py")
        self.assertEqual(result.risk_level, "medium")
        self.assertIn("Unknown operation", result.issues[0])
    
    def test_external_directory_operations(self):
        """Test operations outside project directory"""
        result = self.checker.check_operation_safety("remove_unused_imports", "/etc/passwd")
        
        self.assertFalse(result.safe)
        self.assertEqual(result.risk_level, "critical")
        self.assertIn("external_directory", result.blocked_operations)


class TestBatchOperationValidation(unittest.TestCase):
    """Test batch operation validation"""
    
    def setUp(self):
        self.checker = SafetyChecker()
    
    def test_safe_batch(self):
        """Test validation of safe batch operations"""
        operations = [
            {"type": "remove_unused_imports", "target": "file1.py"},
            {"type": "create_constants", "target": "file2.py"},
            {"type": "format_code", "target": "file3.py"}
        ]
        
        result = self.checker.validate_batch_operations(operations)
        self.assertTrue(result.safe)
        self.assertIn(result.risk_level, ["low", "medium"])
    
    def test_large_batch(self):
        """Test validation of large batch operations"""
        operations = [
            {"type": "remove_unused_imports", "target": f"file{i}.py"}
            for i in range(15)
        ]
        
        result = self.checker.validate_batch_operations(operations)
        self.assertIn("Large batch", result.issues[0])
        self.assertIn(result.risk_level, ["medium", "high"])
    
    def test_conflicting_operations(self):
        """Test detection of conflicting operations on same files"""
        operations = [
            {"type": "remove_unused_imports", "target": "file.py"},
            {"type": "format_code", "target": "file.py"},
            {"type": "create_constants", "target": "file.py"}
        ]
        
        result = self.checker.validate_batch_operations(operations)
        self.assertIn("Multiple operations on same files", result.issues[0])
        self.assertIn(result.risk_level, ["medium", "high"])
    
    def test_mixed_risk_batch(self):
        """Test batch with mixed risk levels"""
        operations = [
            {"type": "remove_unused_imports", "target": "safe_file.py"},
            {"type": "refactor", "target": "main.py"},  # High risk
            {"type": "format_code", "target": "regular.py"}
        ]
        
        result = self.checker.validate_batch_operations(operations)
        # Should take the highest risk level from individual operations
        self.assertIn(result.risk_level, ["high"])


class TestSafetyResult(unittest.TestCase):
    """Test SafetyResult data class"""
    
    def test_safety_result_creation(self):
        """Test creating SafetyResult instances"""
        result = SafetyResult(
            safe=True,
            risk_level="low",
            issues=[],
            recommendations=["Test recommendation"]
        )
        
        self.assertTrue(result.safe)
        self.assertEqual(result.risk_level, "low")
        self.assertEqual(len(result.recommendations), 1)
        self.assertEqual(len(result.blocked_operations), 0)  # Should be empty list from __post_init__
    
    def test_safety_result_with_blocked_operations(self):
        """Test SafetyResult with blocked operations"""
        result = SafetyResult(
            safe=False,
            risk_level="critical",
            issues=["Critical issue"],
            recommendations=["Fix immediately"],
            blocked_operations=["dangerous_operation"]
        )
        
        self.assertFalse(result.safe)
        self.assertEqual(result.risk_level, "critical")
        self.assertIn("dangerous_operation", result.blocked_operations)


if __name__ == '__main__':
    unittest.main(verbosity=2)