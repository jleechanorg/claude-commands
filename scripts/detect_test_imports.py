#!/usr/bin/env python3
"""
Phase 3: Test file inline import detector and optimizer.
Focuses specifically on MVP test files with specialized test import patterns.
"""

import ast
import os
import sys
from pathlib import Path
from typing import List, Dict


class TestInlineDetector:
    def __init__(self):
        self.inline_imports = []
        
    def find_test_inline_imports(self) -> List[Dict]:
        """Find inline imports in MVP test files specifically."""
        test_files = []
        
        # Find all test files in mvp_site
        mvp_path = Path("mvp_site")
        if mvp_path.exists():
            for py_file in mvp_path.rglob("*.py"):
                if "test" in str(py_file).lower():
                    test_files.append(str(py_file))
        
        # Also check testing directories
        for test_dir in ["testing_ui", "tests"]:
            test_path = Path(test_dir)
            if test_path.exists():
                for py_file in test_path.rglob("*.py"):
                    test_files.append(str(py_file))
        
        all_imports = []
        for filepath in test_files:
            imports = self.visit_file(filepath)
            all_imports.extend(imports)
            
        return all_imports
    
    def visit_file(self, filepath: str) -> List[Dict]:
        """Detect inline imports in a Python file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=filepath)
            detector = TestInlineImportVisitor(filepath)
            detector.visit(tree)
            return detector.inline_imports
            
        except Exception as e:
            print(f"Error processing {filepath}: {e}")
            return []


class TestInlineImportVisitor(ast.NodeVisitor):
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.inline_imports = []
        self.in_function = False
        self.function_depth = 0
        
    def visit_FunctionDef(self, node):
        old_in_function = self.in_function
        old_depth = self.function_depth
        
        self.in_function = True
        self.function_depth += 1
        
        self.generic_visit(node)
        
        self.in_function = old_in_function
        self.function_depth = old_depth
        
    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)
        
    def visit_Import(self, node):
        if self.in_function:
            for alias in node.names:
                self.inline_imports.append({
                    'file': self.filepath,
                    'line': node.lineno,
                    'type': 'import',
                    'module': alias.name,
                    'depth': self.function_depth,
                    'priority': self._get_test_priority(alias.name)
                })
    
    def visit_ImportFrom(self, node):
        if self.in_function:
            module = node.module or ''
            for alias in node.names:
                self.inline_imports.append({
                    'file': self.filepath,
                    'line': node.lineno,
                    'type': 'from_import',
                    'module': f"{module}.{alias.name}" if module else alias.name,
                    'from_module': module,
                    'import_name': alias.name,
                    'depth': self.function_depth,
                    'priority': self._get_test_priority(module or alias.name)
                })
    
    def _get_test_priority(self, module_name: str) -> str:
        """Classify import priority for test files."""
        # Test-specific high priority modules
        test_stdlib = {
            'unittest', 'pytest', 'mock', 'tempfile', 'os', 'sys', 'json',
            'time', 'datetime', 're', 'pathlib', 'subprocess', 'io'
        }
        
        # General stdlib modules
        stdlib_modules = {
            'argparse', 'collections', 'itertools', 'functools',
            'logging', 'typing', 'socket', 'shutil', 'glob', 'random'
        }
        
        module_base = module_name.split('.')[0]
        
        if module_base in test_stdlib:
            return 'HIGH'
        elif module_base in stdlib_modules:
            return 'MEDIUM'
        elif module_name.startswith(('mvp_site', 'scripts', 'testing')):
            return 'MEDIUM'
        else:
            return 'LOW'


def fix_test_imports(imports: List[Dict]) -> int:
    """Fix HIGH priority test imports by moving to module level."""
    fixed_count = 0
    
    # Group imports by file
    by_file = {}
    for imp in imports:
        if imp['priority'] == 'HIGH':
            filepath = imp['file']
            if filepath not in by_file:
                by_file[filepath] = []
            by_file[filepath].append(imp)
    
    for filepath, file_imports in by_file.items():
        if fix_file_test_imports(filepath, file_imports):
            fixed_count += 1
    
    return fixed_count


def fix_file_test_imports(filepath: str, imports: List[Dict]) -> bool:
    """Fix inline imports in a test file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        lines = content.split('\n')
        
        # Collect unique imports to add
        imports_to_add = set()
        for imp in imports:
            if imp['type'] == 'import':
                imports_to_add.add(f"import {imp['module']}")
            else:
                imports_to_add.add(f"from {imp['from_module']} import {imp['import_name']}")
        
        # Find insertion point (after docstring and existing imports)
        insert_pos = find_test_import_position(lines)
        
        # Add missing imports
        new_imports = []
        for import_line in sorted(imports_to_add):
            if import_line not in content:
                new_imports.append(import_line)
        
        if new_imports:
            # Insert new imports
            for i, import_line in enumerate(new_imports):
                lines.insert(insert_pos + i, import_line)
            
            # Remove inline imports (simple approach)
            content = '\n'.join(lines)
            
            # Basic cleanup of obvious inline patterns
            for imp in imports:
                if imp['type'] == 'import':
                    import_pattern = f"    import {imp['module']}"
                    content = content.replace(f"\n{import_pattern}\n", "\n")
                else:
                    from_pattern = f"    from {imp['from_module']} import {imp['import_name']}"
                    content = content.replace(f"\n{from_pattern}\n", "\n")
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"Fixed {len(new_imports)} imports in {filepath}")
            return True
        
        return False
        
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
        return False


def find_test_import_position(lines: List[str]) -> int:
    """Find the best position to insert imports in a test file."""
    insert_pos = 0
    in_docstring = False
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Handle docstrings
        if stripped.startswith('"""') or stripped.startswith("'''"):
            if not in_docstring:
                in_docstring = True
            else:
                in_docstring = False
                insert_pos = i + 1
                continue
        
        if in_docstring:
            continue
        
        # Skip comments and empty lines
        if not stripped or stripped.startswith('#'):
            continue
        
        # Found import section
        if stripped.startswith('import ') or stripped.startswith('from '):
            insert_pos = i + 1
        elif stripped and insert_pos > 0:
            # Found first non-import line after imports
            break
        elif stripped and not stripped.startswith('import ') and not stripped.startswith('from '):
            # No existing imports, insert here
            insert_pos = i
            break
    
    return insert_pos


def main():
    """Main execution for Phase 3 test import optimization."""
    print("Phase 3: Detecting inline imports in test files...")
    
    detector = TestInlineDetector()
    imports = detector.find_test_inline_imports()
    
    if not imports:
        print("No inline imports found in test files.")
        return 0
    
    print(f"Found {len(imports)} inline imports in test files:")
    
    # Group by priority
    by_priority = {}
    for imp in imports:
        priority = imp['priority']
        if priority not in by_priority:
            by_priority[priority] = []
        by_priority[priority].append(imp)
    
    for priority in ['HIGH', 'MEDIUM', 'LOW']:
        if priority in by_priority:
            print(f"\n{priority} PRIORITY ({len(by_priority[priority])} imports):")
            for imp in by_priority[priority][:5]:  # Show first 5
                print(f"  {imp['file']}:{imp['line']} - {imp.get('module', 'unknown')}")
    
    # Fix HIGH priority imports
    high_priority = by_priority.get('HIGH', [])
    if high_priority:
        print(f"\nFixing {len(high_priority)} HIGH priority imports...")
        fixed_count = fix_test_imports(high_priority)
        print(f"Fixed imports in {fixed_count} test files.")
    
    return len(imports)


if __name__ == '__main__':
    sys.exit(main())