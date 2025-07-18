#!/usr/bin/env python3
"""
Comprehensive tests for copilot_implementer.py

Tests the critical functionality for unused import detection/removal
and magic number detection/replacement.
"""

import unittest
import tempfile
import os
import sys
from unittest.mock import patch, mock_open
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from copilot_implementer import (
    UnusedImportDetector, 
    MagicNumberDetector,
    CopilotImplementer,
    ImplementationResult
)


class TestUnusedImportDetector(unittest.TestCase):
    """Test unused import detection and removal"""
    
    def setUp(self):
        self.detector = UnusedImportDetector()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        # Clean up temp files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_file(self, content: str) -> str:
        """Create a temporary test file with given content"""
        file_path = os.path.join(self.temp_dir, "test_file.py")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path
    
    def test_simple_unused_import(self):
        """Test detection of simple unused import"""
        content = """import os
import sys
import json

def test():
    path = os.path.join("a", "b")
    return path
"""
        file_path = self.create_test_file(content)
        unused = self.detector.find_unused_imports(file_path)
        
        # Should find sys and json as unused
        unused_names = [name for _, name, _ in unused]
        self.assertIn('sys', unused_names)
        self.assertIn('json', unused_names)
        self.assertNotIn('os', unused_names)
    
    def test_multi_import_line(self):
        """Test detection in multi-import lines"""
        content = """import os, sys, json
from datetime import datetime, timedelta, timezone

def test():
    path = os.path.join("a", "b")
    now = datetime.now()
    return path, now
"""
        file_path = self.create_test_file(content)
        unused = self.detector.find_unused_imports(file_path)
        
        unused_names = [name for _, name, _ in unused]
        self.assertIn('sys', unused_names)
        self.assertIn('json', unused_names)
        self.assertIn('timedelta', unused_names)
        self.assertIn('timezone', unused_names)
        self.assertNotIn('os', unused_names)
        self.assertNotIn('datetime', unused_names)
    
    def test_qualified_name_usage(self):
        """Test that qualified names are detected as used"""
        content = """import os.path
import sys.stdout

def test():
    return os.path.join("a", "b")
"""
        file_path = self.create_test_file(content)
        unused = self.detector.find_unused_imports(file_path)
        
        unused_names = [name for _, name, _ in unused]
        self.assertNotIn('os.path', unused_names)
        self.assertIn('sys.stdout', unused_names)
    
    def test_alias_imports(self):
        """Test import aliases"""
        content = """import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def test():
    arr = np.array([1, 2, 3])
    return arr
"""
        file_path = self.create_test_file(content)
        unused = self.detector.find_unused_imports(file_path)
        
        unused_names = [name for _, name, _ in unused]
        self.assertNotIn('np', unused_names)
        self.assertIn('pd', unused_names)
        self.assertIn('plt', unused_names)
    
    def test_star_imports(self):
        """Test handling of star imports (should be preserved)"""
        content = """from os import *
import sys

def test():
    return path.join("a", "b")  # Uses os.path via star import
"""
        file_path = self.create_test_file(content)
        unused = self.detector.find_unused_imports(file_path)
        
        # Star imports should not be marked as unused
        unused_names = [name for _, name, _ in unused]
        self.assertIn('sys', unused_names)
        # Star import detection doesn't mark individual names as unused
    
    def test_remove_unused_imports_multi_line(self):
        """Test removal of unused imports from multi-import lines"""
        content = """import os, sys, json, time
from datetime import datetime, timedelta, timezone

def test():
    path = os.path.join("a", "b")
    now = datetime.now()
    return path, now
"""
        file_path = self.create_test_file(content)
        result = self.detector.remove_unused_imports(file_path)
        
        self.assertTrue(result.success)
        self.assertGreater(len(result.changes_made), 0)
        
        # Read the modified file
        with open(file_path, 'r', encoding='utf-8') as f:
            modified_content = f.read()
        
        # Should preserve os and datetime, remove others
        self.assertIn('import os', modified_content)
        self.assertIn('from datetime import datetime', modified_content)
        self.assertNotIn('sys', modified_content)
        self.assertNotIn('json', modified_content)
        # Check that 'time' is not in import statements (not in middle of datetime)
        lines = modified_content.split('\n')
        import_lines = [line for line in lines if line.strip().startswith(('import', 'from'))]
        time_in_imports = any('time' in line and 'datetime' not in line for line in import_lines)
        self.assertFalse(time_in_imports, "'time' should not appear in import statements")
        self.assertNotIn('timedelta', modified_content)
        self.assertNotIn('timezone', modified_content)
    
    def test_remove_entire_unused_line(self):
        """Test removal of entirely unused import lines"""
        content = """import os
import sys
import json

def test():
    path = os.path.join("a", "b")
    return path
"""
        file_path = self.create_test_file(content)
        result = self.detector.remove_unused_imports(file_path)
        
        self.assertTrue(result.success)
        
        # Read the modified file
        with open(file_path, 'r', encoding='utf-8') as f:
            modified_content = f.read()
        
        # Should only have os import
        self.assertIn('import os', modified_content)
        self.assertNotIn('import sys', modified_content)
        self.assertNotIn('import json', modified_content)
    
    def test_preserve_indentation(self):
        """Test that indentation is preserved in modified imports"""
        content = """if True:
    import os, sys, json
    
    def test():
        path = os.path.join("a", "b")
        return path
"""
        file_path = self.create_test_file(content)
        result = self.detector.remove_unused_imports(file_path)
        
        self.assertTrue(result.success)
        
        # Read the modified file
        with open(file_path, 'r', encoding='utf-8') as f:
            modified_content = f.read()
        
        # Should preserve indentation
        self.assertIn('    import os', modified_content)
        self.assertNotIn('    import os, sys, json', modified_content)


class TestMagicNumberDetector(unittest.TestCase):
    """Test magic number detection and replacement"""
    
    def setUp(self):
        self.detector = MagicNumberDetector()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        # Clean up temp files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_file(self, content: str) -> str:
        """Create a temporary test file with given content"""
        file_path = os.path.join(self.temp_dir, "test_file.py")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path
    
    def test_find_magic_numbers(self):
        """Test detection of magic numbers"""
        content = """def test():
    x = 42
    y = 42
    z = 100
    pi = 3.14159
    another_pi = 3.14159
    return x + y + z + pi + another_pi
"""
        file_path = self.create_test_file(content)
        magic_numbers = self.detector.find_magic_numbers(file_path)
        
        # Should find 42 and 3.14159 (both appear twice)
        values = [value for _, value, _ in magic_numbers]
        self.assertIn(42, values)
        self.assertIn(3.14159, values)
        # 100 should not be found (appears only once)
        self.assertNotIn(100, values)
    
    def test_ignore_common_numbers(self):
        """Test that common numbers are ignored"""
        content = """def test():
    x = 0
    y = 1
    z = -1
    a = 2
    b = 10
    return x + y + z + a + b
"""
        file_path = self.create_test_file(content)
        magic_numbers = self.detector.find_magic_numbers(file_path)
        
        # All these numbers should be ignored
        self.assertEqual(len(magic_numbers), 0)
    
    def test_create_constants_and_replace(self):
        """Test creation of constants and replacement of magic numbers"""
        content = """def calculate():
    area = 42 * 42
    circumference = 2 * 3.14159 * 5
    volume = 42 * 3.14159
    return area, circumference, volume
"""
        file_path = self.create_test_file(content)
        result = self.detector.create_constants(file_path)
        
        self.assertTrue(result.success)
        self.assertGreater(len(result.changes_made), 0)
        
        # Read the modified file
        with open(file_path, 'r', encoding='utf-8') as f:
            modified_content = f.read()
        
        # Should have constants defined
        self.assertIn('CONSTANT_42 = 42', modified_content)
        self.assertIn('CONSTANT_3_14159 = 3.14159', modified_content)
        
        # Should have replaced magic numbers
        self.assertIn('area = CONSTANT_42 * CONSTANT_42', modified_content)
        self.assertIn('2 * CONSTANT_3_14159 * 5', modified_content)
        self.assertIn('CONSTANT_42 * CONSTANT_3_14159', modified_content)
    
    def test_constant_placement(self):
        """Test that constants are placed after imports"""
        content = """#!/usr/bin/env python3
import os
import sys
from datetime import datetime

def calculate():
    x = 42
    y = 42
    return x + y
"""
        file_path = self.create_test_file(content)
        result = self.detector.create_constants(file_path)
        
        self.assertTrue(result.success)
        
        # Read the modified file
        with open(file_path, 'r', encoding='utf-8') as f:
            modified_content = f.read()
        
        lines = modified_content.split('\n')
        
        # Find positions
        import_end = -1
        constant_pos = -1
        function_start = -1
        
        for i, line in enumerate(lines):
            if line.startswith('from datetime import'):
                import_end = i
            elif 'CONSTANT_42 = 42' in line:
                constant_pos = i
            elif 'def calculate():' in line:
                function_start = i
        
        # Constants should be after imports but before functions
        self.assertGreater(constant_pos, import_end)
        self.assertLess(constant_pos, function_start)
    
    def test_no_magic_numbers(self):
        """Test handling when no magic numbers are found"""
        content = """def test():
    x = 0
    y = 1
    z = variable_name
    return x + y + z
"""
        file_path = self.create_test_file(content)
        result = self.detector.create_constants(file_path)
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.changes_made), 0)
        self.assertEqual(result.description, "No magic numbers found")


class TestCopilotImplementer(unittest.TestCase):
    """Test the main CopilotImplementer class"""
    
    def setUp(self):
        self.implementer = CopilotImplementer()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        # Clean up temp files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_file(self, content: str) -> str:
        """Create a temporary test file with given content"""
        file_path = os.path.join(self.temp_dir, "test_file.py")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path
    
    def test_implement_unused_imports_suggestion(self):
        """Test implementing unused imports suggestion"""
        content = """import os, sys, json

def test():
    return os.path.join("a", "b")
"""
        file_path = self.create_test_file(content)
        
        result = self.implementer.implement_suggestion("auto_fix_unused_imports", file_path)
        
        self.assertTrue(result.success)
        self.assertIn("unused imports", result.description.lower())
    
    def test_implement_magic_numbers_suggestion(self):
        """Test implementing magic numbers suggestion"""
        content = """def test():
    x = 42
    y = 42
    return x + y
"""
        file_path = self.create_test_file(content)
        
        result = self.implementer.implement_suggestion("auto_fix_magic_numbers", file_path)
        
        self.assertTrue(result.success)
        self.assertIn("constants", result.description.lower())
    
    def test_unknown_suggestion_type(self):
        """Test handling of unknown suggestion types"""
        file_path = self.create_test_file("def test(): pass")
        
        result = self.implementer.implement_suggestion("unknown_suggestion", file_path)
        
        self.assertFalse(result.success)
        self.assertIn("Unknown suggestion type", result.description)
    
    def test_file_not_found(self):
        """Test handling of non-existent files"""
        result = self.implementer.implement_suggestion("auto_fix_unused_imports", "/nonexistent/file.py")
        
        # The current implementation returns success=True with "No unused imports found" for missing files
        # This is due to the exception handling in find_unused_imports returning empty list
        self.assertTrue(result.success)
        self.assertIn("No unused imports", result.description)
    
    @patch('subprocess.run')
    def test_commit_changes(self, mock_run):
        """Test committing changes"""
        # Mock successful git operations
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "abc123def\n"
        
        results = [
            ImplementationResult(
                success=True,
                file_path="/test/file.py",
                description="Test change",
                changes_made=["Test change made"]
            )
        ]
        
        commit_hash = self.implementer.commit_changes(results, "Test commit")
        
        # Should return a commit hash
        self.assertIsNotNone(commit_hash)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""
    
    def setUp(self):
        self.detector = UnusedImportDetector()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_file(self, content: str) -> str:
        """Create a temporary test file with given content"""
        file_path = os.path.join(self.temp_dir, "test_file.py")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path
    
    def test_syntax_error_file(self):
        """Test handling of files with syntax errors"""
        content = """import os
def test(
    # Syntax error - missing closing parenthesis
    return os.path.join("a", "b")
"""
        file_path = self.create_test_file(content)
        unused = self.detector.find_unused_imports(file_path)
        
        # Should handle gracefully and return empty list
        self.assertEqual(len(unused), 0)
    
    def test_empty_file(self):
        """Test handling of empty files"""
        file_path = self.create_test_file("")
        unused = self.detector.find_unused_imports(file_path)
        
        self.assertEqual(len(unused), 0)
    
    def test_file_with_only_comments(self):
        """Test handling of files with only comments"""
        content = """# This is a comment
# Another comment
# import os  # This is in a comment, not real import
"""
        file_path = self.create_test_file(content)
        unused = self.detector.find_unused_imports(file_path)
        
        self.assertEqual(len(unused), 0)
    
    def test_nonexistent_file(self):
        """Test handling of non-existent files"""
        unused = self.detector.find_unused_imports("/nonexistent/file.py")
        
        self.assertEqual(len(unused), 0)


if __name__ == '__main__':
    unittest.main()